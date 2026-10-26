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
# extend the curve to the 0.66 m top along its last direction, tilt easing to 5 deg (the run beyond the design curve)
def line_fit(P):
    m = P.mean(0); U, S, Vt = np.linalg.svd(P - m); d = Vt[0]; n = np.array([-d[1], d[0]]); return m, d, (P - m) @ n

def simulate(v, n=300):
    """slider-crank: c1 on the fitted line, c2 on the fitted circle; drive c1 along the line; returns poses (Q, phi, P1, P2, s)."""
    c1, c2 = np.array(v[:2]), np.array(v[2:4])
    P1 = world(Qd, Pd, c1); P2 = world(Qd, Pd, c2); m, d, r1 = line_fit(P1); Bc, R, r2 = circle_fit(P2)
    s0 = (P1[0] - m) @ d; s1 = (P1[-1] - m) @ d; Lc = np.hypot(*(c2 - c1)); loc = np.arctan2(*(c2 - c1)[::-1]); out = []; prev = P2[0]
    ext = 0.06 * np.sign(s1 - s0)
    for s in np.linspace(s0, s1 + ext, n):
        X = m + s * d; dv = Bc - X; dd = np.hypot(*dv)
        if dd > R + Lc or dd < abs(R - Lc): break
        a = (Lc ** 2 - R ** 2 + dd ** 2) / (2 * dd); h = np.sqrt(max(Lc ** 2 - a ** 2, 0)); e = dv / dd; nn = np.array([-e[1], e[0]])
        ca, cb = X + a * e + h * nn, X + a * e - h * nn; Y = ca if np.hypot(*(ca - prev)) <= np.hypot(*(cb - prev)) else cb; prev = Y
        phi = np.degrees(loc - np.arctan2(*(Y - X)[::-1])); Q = X - rot(phi) @ c1
        out.append((Q, phi, X, Y, s))
        if Q[1] >= V5.TOP: break
    return out, dict(m=m, d=d, B=Bc, R=R, res1=float(np.abs(r1).max()), res2=float(np.abs(r2).max()))

def cost(v):
    c1, c2 = np.array(v[:2]), np.array(v[2:4])
    if np.hypot(*(c1 - c2)) < V5.MIN_COUPLER: return 1 + (V5.MIN_COUPLER - np.hypot(*(c1 - c2)))
    s, g = simulate(v, 120)
    if len(s) < 10: return 2.0
    if s[-1][0][1] < V5.TOP - 1e-3: return 1 + (V5.TOP - s[-1][0][1])
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    dist = np.hypot(*(Qs[None, :, :] - Qd[:, None, :]).transpose(2, 0, 1)); j = dist.argmin(1)
    e = dist[np.arange(len(Qd)), j].max() + 0.1 * np.abs(np.radians(ph[j] - Pd)).max()
    pen = 0.05 * max(0, ph.max() - V5.PHI_RUN_MAX) + 0.05 * max(0, -ph.min() - 2)
    # rail must reach down to the base (lower end above floor, in front of the bed); ground pivot B on the base region
    lo = min(s[0][2], s[-1][2], key=lambda p: p[1]); pen += max(0, -lo[0] + 0.02) + max(0, 0.03 - g["B"][0]) + max(0, g["B"][1] - 0.40) + max(0, 0.04 - g["B"][1])
    # rigid parts vs bed: plate, bracket, link B-c2, rail segment
    for f in s[::10]:
        plate, br = LY.seat_polys(f[0], f[1], c1, c2)
        for pts, r in ((LY.poly_pts(plate, 0.01), 0), (LY.poly_pts(br, 0.01), 0), (LY.seg_pts(g["B"], f[3]), 0.02)):
            d_ = float(LY.bed_d(pts).min()) - r
            if d_ < V5.CLR_BED: pen += 5 * (V5.CLR_BED - d_)
    return e + pen

def synth(seed):
    r = differential_evolution(cost, [(-0.085, 0.085), (-0.26, -0.03), (-0.085, 0.085), (-0.26, -0.03)], seed=seed, popsize=25, maxiter=300, tol=1e-9, polish=False)
    return float(r.fun), r.x.tolist()

if __name__ == "__main__":
    t0 = time.time()
    with Pool() as p: SY = p.map(synth, range(4))
    f, v = min(SY); s, g = simulate(v, 700)
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    dist = np.hypot(*(Qs[None, :, :] - Qd[:, None, :]).transpose(2, 0, 1)); j = dist.argmin(1)
    rail = [s[0][2].tolist(), s[-1][2].tolist()]
    info = dict(c1=np.round(v[:2], 4).tolist(), c2=np.round(v[2:4], 4).tolist(), rail=np.round(rail, 4).tolist(), rail_angle_deg=round(float(np.degrees(np.arctan2(g["d"][0], g["d"][1]))) % 180, 1),
                stroke=round(float(abs(s[-1][4] - s[0][4])), 3), B=np.round(g["B"], 4).tolist(), link=round(float(g["R"]), 4), centre_err_mm=round(1000 * float(dist[np.arange(len(Qd)), j].max()), 1),
                tilt_err_deg=round(float(np.abs(ph[j] - Pd).max()), 1), phi_run_max=round(float(ph.max()), 1), phi_end=round(float(ph[-1]), 1), cost=round(f, 4))
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
            n_ = rot(s[i][1]) @ np.array([0, 1.0]); Fv = -1.5 * 100 * G * n_
            Cn = s[i + 1][0] + rot(s[i + 1][1]) @ np.array([xo, 0]); Cp = s[i - 1][0] + rot(s[i - 1][1]) @ np.array([xo, 0])
            F.append(abs(-(Fv @ (Cn - Cp)) / (s[i + 1][4] - s[i - 1][4])))
    info["screw_force_hold100_N"] = round(max(F)); info["frames"] = [dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in s[::14]]
    json.dump(dict(note=__doc__, x=v, mech=info, summary=summ, users=R), open(os.path.join(OUT, "slider.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("summary", summ, "screw force", info["screw_force_hold100_N"]); print("done", round(time.time() - t0), "s")
