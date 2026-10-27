"""Alternative v5b: inclined guide (slider) + tilt link, one side only (the other side open, as in v13 13.1).

The seat bracket carries point c1 on a carriage that runs on a straight inclined rail, and point c2 on a link to a ground
pivot B (a slider-crank; one DOF, the carriage is driven by a lead screw in the rail). Synthesis: find c1, c2 in the seat
frame so that c1's path on the v5 design curve is a straight line and c2's path is a circle; constraints as in v5
(rigid parts 1.5 cm off the bed, tilt <= 16 deg over the run, c1-c2 >= 80 mm, rail lower end on the base).
Then the 81-user check with the fixed pole, forces and the line/circle residuals. Output: seat_1dof/slider.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_1dof_v5 as V5
import seat_1dof_layout as LY
from seat_trajectory import rot
from seat_1dof_design import circle_fit, world
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, resample_curve
from model import G
OUT = V5.OUT
Qd, Pd = resample_curve(V5.CVD, 80)
# v5.2: the seat itself must reach TOP (0.69 m: the zoned cushion needs ~3 cm more travel than the 0.66 m design curve) and
# end with a tilt of 0..8 deg (v5.1 only extended the old rail, which tipped the seat back to -3.4 deg). EXT is only the
# search range past the end of the design curve; the run stops at TOP.
TOP = 0.69; EXT = 0.15; PHI_END = (0.0, 8.0)
# extend the curve to the 0.66 m top along its last direction, tilt easing to 5 deg (the run beyond the design curve)
def line_fit(P):
    m = P.mean(0); U, S, Vt = np.linalg.svd(P - m); d = Vt[0]; n = np.array([-d[1], d[0]]); return m, d, (P - m) @ n

def simulate(v, n=300):
    """slider-crank: c1 on the fitted line, c2 on the fitted circle; drive c1 along the line; returns poses (Q, phi, P1, P2, s)."""
    c1, c2 = np.array(v[:2]), np.array(v[2:4])
    P1 = world(Qd, Pd, c1); P2 = world(Qd, Pd, c2); m, d, r1 = line_fit(P1); Bc, R, r2 = circle_fit(P2)
    s0 = (P1[0] - m) @ d; s1 = (P1[-1] - m) @ d; Lc = np.hypot(*(c2 - c1)); loc = np.arctan2(*(c2 - c1)[::-1]); out = []; prev = P2[0]
    ext = EXT * np.sign(s1 - s0); stop = TOP
    for s in np.linspace(s0, s1 + ext, n):
        X = m + s * d; dv = Bc - X; dd = np.hypot(*dv)
        if dd > R + Lc or dd < abs(R - Lc): break
        a = (Lc ** 2 - R ** 2 + dd ** 2) / (2 * dd); h = np.sqrt(max(Lc ** 2 - a ** 2, 0)); e = dv / dd; nn = np.array([-e[1], e[0]])
        ca, cb = X + a * e + h * nn, X + a * e - h * nn; Y = ca if np.hypot(*(ca - prev)) <= np.hypot(*(cb - prev)) else cb; prev = Y
        phi = np.degrees(loc - np.arctan2(*(Y - X)[::-1])); Q = X - rot(phi) @ c1
        out.append((Q, phi, X, Y, s))
        if Q[1] >= stop: break
    return out, dict(m=m, d=d, B=Bc, R=R, res1=float(np.abs(r1).max()), res2=float(np.abs(r2).max()))

def cost(v):
    c1, c2 = np.array(v[:2]), np.array(v[2:4])
    if np.hypot(*(c1 - c2)) < V5.MIN_COUPLER: return 1 + (V5.MIN_COUPLER - np.hypot(*(c1 - c2)))
    s, g = simulate(v, 120)
    if len(s) < 10: return 2.0
    if s[-1][0][1] < TOP - 1e-3: return 1 + (TOP - s[-1][0][1])
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    dist = np.hypot(*(Qs[None, :, :] - Qd[:, None, :]).transpose(2, 0, 1)); j = dist.argmin(1)
    e = dist[np.arange(len(Qd)), j].max() + 0.1 * np.abs(np.radians(ph[j] - Pd)).max()
    pen = 0.05 * max(0, ph.max() - V5.PHI_RUN_MAX) + 0.05 * max(0, -ph.min() - 2) + 0.05 * max(0, PHI_END[0] - ph[-1]) + 0.05 * max(0, ph[-1] - PHI_END[1])
    # rail must reach down to the base (lower end above floor, in front of the bed); ground pivot B on the base region
    lo = min(s[0][2], s[-1][2], key=lambda p: p[1]); pen += max(0, 0.03 - g["B"][0]) + max(0, g["B"][0] - 0.50) + max(0, g["B"][1] - 0.40) + max(0, 0.04 - g["B"][1])
    # rail incl. carriage margin (6 cm past both ends of the carriage travel) must stay off the bed
    d_ = g["d"]; lo_ = s[0][2] - 0.06 * d_ * np.sign((s[-1][2] - s[0][2]) @ d_); hi_ = s[-1][2] + 0.06 * d_ * np.sign((s[-1][2] - s[0][2]) @ d_)
    rb = float(LY.bed_d(LY.seg_pts(lo_, hi_, 30)).min()) - 0.02
    if rb < V5.CLR_BED: pen += 5 * (V5.CLR_BED - rb)
    # rigid parts vs bed: plate, bracket, link B-c2
    for f in s[::10]:
        plate, br = LY.seat_polys(f[0], f[1], c1, c2)
        for pts, r in ((LY.poly_pts(plate, 0.01), 0), (LY.poly_pts(br, 0.01), 0), (LY.seg_pts(g["B"], f[3]), 0.02)):
            d_ = float(LY.bed_d(pts).min()) - r
            if d_ < V5.CLR_BED: pen += 5 * (V5.CLR_BED - d_)
    return e + pen

def synth(seed):
    r = differential_evolution(cost, [(-0.085, 0.085), (-0.22, -0.03), (-0.085, 0.085), (-0.22, -0.03)], seed=seed, popsize=25, maxiter=300, tol=1e-9, polish=False)
    return float(r.fun), r.x.tolist()

if __name__ == "__main__":
    t0 = time.time()
    if len(sys.argv) > 1 and sys.argv[1] == "eval":       # keep the synthesised geometry, re-evaluate (e.g. with a longer rail)
        old = json.load(open(os.path.join(OUT, "slider.json"))); v = old["x"]; f = old["mech"]["cost"]
    else:
        with Pool() as p: SY = p.map(synth, range(4))
        f, v = min(SY)
    s, g = simulate(v, 700)
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    dist = np.hypot(*(Qs[None, :, :] - Qd[:, None, :]).transpose(2, 0, 1)); j = dist.argmin(1)
    rail = [s[0][2].tolist(), s[-1][2].tolist()]
    info = dict(c1=np.round(v[:2], 4).tolist(), c2=np.round(v[2:4], 4).tolist(), rail=np.round(rail, 4).tolist(), rail_angle_deg=round(float(np.degrees(np.arctan2(g["d"][0], g["d"][1]))) % 180, 1),
                stroke=round(float(abs(s[-1][4] - s[0][4])), 3), B=np.round(g["B"], 4).tolist(), link=round(float(g["R"]), 4), centre_err_mm=round(1000 * float(dist[np.arange(len(Qd)), j].max()), 1),
                tilt_err_deg=round(float(np.abs(ph[j] - Pd).max()), 1), phi_run_max=round(float(ph.max()), 1), phi_end=round(float(ph[-1]), 1), cost=round(f, 4), top=round(float(Qs[-1][1]), 3))
    print("slider", info, round(time.time() - t0), "s")
    cv = with_prefix(Qs, ph)
    with Pool() as p: R = dict(p.map(V5.user_job, [(u, cv, "sides", None, None) for u in USERS]))
    vals = [q for q in R.values() if q]; ok = lambda q: bool(q and q["fwd_slip_cm"] <= 2 and q["catch_min_cm"] >= 0)
    summ = dict(n_ok=sum(ok(q) for q in R.values()), fwd_max=max(q["fwd_slip_cm"] for q in vals), catch_min=min(q["catch_min_cm"] for q in vals),
                phi_release_max=max(q["phi_release"] for q in vals), E_rel_med=round(float(np.median([q["E_release"] for q in vals])), 3), E_rel_max=max(q["E_release"] for q in vals),
                E_sup_max=max(q["E_supported_max"] for q in vals))
    # forces: lead-screw (rail) force by virtual work, load anywhere on the seat, 1.5 BW of 100 kg; link force
    F = []
    for xo in V5.XOFF:
        for i in range(1, len(s) - 1, 5):
            n_ = rot(s[i][1]) @ np.array([0, 1.0]); Fv = -1.5 * 100 * G * n_ + np.array([0, -10 * G])     # + 10 kg seat and bracket
            Cn = s[i + 1][0] + rot(s[i + 1][1]) @ np.array([xo, 0]); Cp = s[i - 1][0] + rot(s[i - 1][1]) @ np.array([xo, 0])
            F.append(abs(-(Fv @ (Cn - Cp)) / (s[i + 1][4] - s[i - 1][4])))
    info["screw_force_hold100_N"] = round(max(F))
    # statics of the seat body: link B-c2 is a two-force member; carriage reacts force normal to the rail + moment (in-plane);
    # the screw takes the force along the rail. Out of plane: the seat load acts ~0.25 m from the rail plane -> torsion/roll moment.
    m2 = lambda r, w: r[0] * w[1] - r[1] * w[0]; worst = dict(screw=0, link=0, normal=0, moment=0)
    for xo in V5.XOFF:
        for i in range(0, len(s), 10):
            Q, phi, X, Y = s[i][0], s[i][1], s[i][2], s[i][3]; n_ = rot(phi) @ np.array([0, 1.0]); Fv = -1.5 * 100 * G * n_ + np.array([0, -10 * G])
            C = Q + rot(phi) @ np.array([xo, 0]); uL = (Y - g["B"]) / np.hypot(*(Y - g["B"])); d_ = g["d"]; nr = np.array([-d_[1], d_[0]])
            # unknowns: link force fl (along uL at Y), rail force: screw fs (along d at X), normal fn (along nr at X), moment Mc
            # take the carriage able to resist moment (profile guide): solve fs, fn, fl with Mc = moment balance remainder about X using fl
            # choose fl so the carriage moment is zero if possible (link takes the rotation): moment about X: (C-X)xFv + (Y-X)x(fl uL) = 0
            fl = -m2(C - X, Fv) / m2(Y - X, uL)
            rest = -(Fv + fl * uL); fs = rest @ d_; fn = rest @ nr
            worst = dict(screw=max(worst["screw"], abs(fs)), link=max(worst["link"], abs(fl)), normal=max(worst["normal"], abs(fn)), moment=worst["moment"])
    info["forces_hold100_N"] = {k: round(v) for k, v in worst.items() if k != "moment"}
    info["torsion_hold100_Nm"] = round(1.5 * 100 * G * 0.25); info["frames"] = [dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in s[::14]]
    json.dump(dict(note=__doc__, x=v, top=TOP, mech=info, summary=summ, users=R), open(os.path.join(OUT, "slider.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("summary", summ, "screw force", info["screw_force_hold100_N"]); print("done", round(time.time() - t0), "s")
