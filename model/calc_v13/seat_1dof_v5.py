"""One-DOF seat v5: tilt capped at 15 deg, handrail fixed on the base, two linkage layouts compared.

Changes after the Gemini audit (page/seat1dof/audit/):
  - design curve with the seat tilt capped at 15 deg (a sit-back on a 15 deg slope is held by cloth-on-cushion friction, mu
    >= 0.27 needed); the four-bar must stay <= 16 deg over its whole run, including the part above the design curve
  - moving pivots on the seat bracket at least 80 mm apart (was 41 mm: pin forces up to 6 kN); rigid parts 1.5 cm clear of
    the bed (soft cushion lip 4.5 cm)
  - actuator force from virtual work with the load anywhere on the seat (the rotation term is included), envelope over load
    positions -6 .. +8.5 cm and the 1.5 BW / 100 kg static case; pin forces from the coupler statics
  - handrail fixed on the base: an L-shaped rail whose vertical part (x 0.69 m, z 0.75 .. 1.10 m) the user can grip at any
    height; release effort recomputed with it (the earlier pages assumed a rail rising with the seat)
Layouts
  mid    one four-bar in the mid-plane under the seat (both sides open: legs can swing back onto the bed), driven by two
         actuators side by side; every part must clear every user's calves and feet at the matching moment
  sides  a four-bar on each side outside the legs, each with its own actuator in its side plane (no cross tube); needs two
         synchronised actuators; both sides are closed
Output: seat_1dof/v5.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot, Z0, Seat, effort, pose, body_points
from seat_relative_motion import rise, curve_fit, track, solve_s, curve_vertical
import seat_1dof_fourbar2 as FB2
import seat_1dof_fourbar as F1
import seat_1dof_layout as LY
from seat_1dof_design import USERS, ukey, path_of, resample_curve, PAD_AMAX
from model import G, Subject

OUT = os.path.join(HERE, "seat_1dof"); TOP = 0.66; PHI_CAP = 15.0; PHI_RUN_MAX = 16.0
LIP = 0.045; CLR_BED = 0.015; MIN_COUPLER = 0.08; LEG_CLR = 0.02
POLE = dict(x=(0.62, 0.69, 0.76), z=tuple(np.round(np.arange(0.75, 1.101, 0.05), 2)))

# ---------------------------------------------------------------- design curve (tilt <= 15 deg)
def design_curve(cap=PHI_CAP):
    _, ref = rise(1.50, 0.33, 0.6, r_b=0.09); q_, Q_, p_ = curve_fit(ref, cap); Qm, pm = Q_[15:], p_[15:]
    ds = np.hypot(*np.diff(Qm, axis=0).T) + 0.1 * np.radians(np.abs(np.diff(pm))); t = np.concatenate([[0], np.cumsum(ds)]); t /= t[-1]
    w = np.ones(len(t)); w[0] = 50.0
    fx, fz, fp = (np.polyfit(t, v, 3, w=w) for v in (Qm[:, 0], Qm[:, 1], pm))
    tt = np.linspace(0, 1, 300); Q = np.c_[np.polyval(fx, tt), np.polyval(fz, tt)]; phi = np.clip(np.polyval(fp, tt), 0, cap)
    return F1.with_prefix(Q, phi)

def _frozen_curve():
    """v5.6: the design curve as synthesised (before the solve_s fix lengthened every rise); the mechanisms were fitted to it."""
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seat_1dof", "design_curve_v5.json")
    if not os.path.exists(f): return design_curve()
    d = json.load(open(f)); return np.array(d["q"]), np.array(d["Q"]), np.array(d["phi"])
CVD = _frozen_curve(); QT, PT = resample_curve(CVD, 40)
FB2.QT, FB2.PT = QT, PT          # the four-bar runner and its base cost now target the v5 curve
LY.LIP = LIP

# ---------------------------------------------------------------- legs at the matching moment (for the mid layout)
def leg_bins():
    """for seat-centre height bins (1 cm) along the design curve: every user's calf and foot capsules at the moments when their
    seat is in that bin, including standing up after the release (seat stays at the release height)."""
    bins = {}
    for u in USERS:
        ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rows = track(sub, path, Seat(r_e=0.03), CVD); zrel = None
        for i, pz in enumerate(path):
            r = rows[i] if i < len(rows) else None
            if r and r.get("contact") and r.get("ok"): k = min(int(r["k"]), len(CVD[1]) - 1); zs = CVD[1][k][1]; zrel = zs
            else: zs = zrel
            if zs is None: continue
            caps = LY.body_caps(pz, sub); b = int(round(100 * zs))
            bins.setdefault(b, []).append((caps["calf"], caps["foot"]))
    return bins

def legs_near(bins, zs):
    b = int(round(100 * zs)); out = []
    for bb in (b - 1, b, b + 1): out += bins.get(bb, [])
    return out

def leg_clouds(bins):
    """per bin: sample points on the calf and foot axes with their radii (vectorised clearance in the synthesis cost)."""
    cl = {}
    for b in bins:
        P, Rr = [], []
        legs = legs_near(bins, b / 100.0)
        step = max(1, len(legs) // 60)
        for calf, foot in legs[::step]:
            for X, Y_, r in (calf, foot):
                for t in np.linspace(0, 1, 8): P.append(X + t * (Y_ - X)); Rr.append(r)
        cl[b] = (np.array(P), np.array(Rr))
    return cl

# ---------------------------------------------------------------- cost
def parts_mid(f, c1, c2, A, B):
    plate, br = LY.seat_polys(f[0], f[1], c1, c2)
    return [("bracket", LY.poly_pts(br, 0.01), 0.0), ("rocker A", LY.seg_pts(A, f[2]), 0.02), ("rocker B", LY.seg_pts(B, f[3]), 0.02),
            ("post A", LY.seg_pts(np.array([A[0], 0.04]), A), 0.025), ("post B", LY.seg_pts(np.array([B[0], 0.04]), B), 0.025)]

def cost(v, layout, bins):
    v = np.asarray(v); base = FB2.cost(v)
    if base >= 1.0: return base
    s = FB2.run(v, n=80)
    if s is None or len(s) < 4: return base + 1.0
    A, B, c1, c2 = v[0:2], v[2:4], v[4:6], v[6:8]; pen = 0.0
    pen += 5 * max(0.0, MIN_COUPLER - np.hypot(*(c1 - c2)))
    pen += 0.05 * max(0.0, max(p[1] for p in s) - PHI_RUN_MAX)
    w, _ = LY.mech_bed_clear(v, s[::3]); pen += 5 * max(0.0, CLR_BED - w)
    if layout == "mid":
        for f in s[::4]:
            cl = CLOUDS.get(int(round(100 * f[0][1])))
            if cl is None or len(cl[0]) == 0: continue
            for name, pts, r in parts_mid(f, c1, c2, A, B):
                d = (np.hypot(*(pts[:, None, :] - cl[0][None, :, :]).transpose(2, 0, 1)) - cl[1][None, :]).min() - r
                if d < LEG_CLR: pen += (LEG_CLR - d) * 0.5
    return base + pen

BOUNDS = {"mid": [(0.03, 0.30), (0.05, 0.32), (0.03, 0.30), (0.05, 0.32), (-0.085, 0.085), (-0.26, -0.03), (-0.085, 0.085), (-0.26, -0.03)],
          "sides": [(0.03, 0.34), (0.05, 0.34), (0.03, 0.34), (0.05, 0.34), (-0.085, 0.085), (-0.26, -0.03), (-0.085, 0.085), (-0.26, -0.03)]}
BINS = None; CLOUDS = {}
def synth(args):
    layout, seed = args
    r = differential_evolution(cost, BOUNDS[layout], args=(layout, BINS), seed=seed, popsize=20, maxiter=400, tol=1e-8, polish=False)
    return layout, float(r.fun), r.x.tolist()

# ---------------------------------------------------------------- actuator: corrected virtual work, load anywhere on the seat
XOFF = (-0.06, -0.03, 0.0, 0.03, 0.06, 0.085)
def act_len(f, act, A, B): return float(np.hypot(*(LY.act_E(f, act, A, B) - np.array(act["D"]))))
def act_forces(s, act, A, B, Fs, kg=10.0):
    """push force (N, + = push) at each frame, worst over load positions XOFF; load normal to the seat at (xoff, 0) in the seat frame."""
    Ls = np.array([act_len(f, act, A, B) for f in s]); worst = np.zeros(len(s) - 2)
    for xo in XOFF:
        F = []
        for i in range(1, len(s) - 1):
            n_ = rot(s[i][1]) @ np.array([0, 1.0]); Fv = -Fs * n_ + np.array([0, -kg * G])
            Cn = s[i + 1][0] + rot(s[i + 1][1]) @ np.array([xo, 0]); Cp = s[i - 1][0] + rot(s[i - 1][1]) @ np.array([xo, 0])
            dL = Ls[i + 1] - Ls[i - 1]; F.append(-(Fv @ (Cn - Cp)) / dL if abs(dL) > 1e-7 else np.inf)
        F = np.array(F); worst = np.where(np.abs(F) > np.abs(worst), F, worst)
    return Ls, worst

def pin_forces(s, A, c1, c2, Fs):
    """coupler statics: rocker A as a two-force member, the rest through pin P2 (worst over load positions)."""
    m = lambda r, w: r[0] * w[1] - r[1] * w[0]; worst = [0.0, 0.0]
    for f in s[::5]:
        Q, phi, P1, P2 = f[0], f[1], f[2], f[3]; n_ = rot(phi) @ np.array([0, 1.0]); uA = (P1 - A) / np.hypot(*(P1 - A))
        for xo in XOFF:
            C = Q + rot(phi) @ np.array([xo, 0]); Fv = -Fs * n_
            fA = -m(C - P2, Fv) / m(P1 - P2, uA); R2 = -(Fv + fA * uA)
            worst = [max(worst[0], abs(fA)), max(worst[1], float(np.hypot(*R2)))]
    return worst

def actuator_search(v, s, layout, bins):
    A, B = np.asarray(v[0:2]), np.asarray(v[2:4]); HOLD = 1.5 * 100 * G; best = None
    Dxs = np.arange(0.04, 0.226, 0.02) if layout == "mid" else np.arange(0.04, 0.30, 0.02)
    for on in ("A", "B"):
        for t in (0.3, 0.45, 0.6, 0.8, 1.0):
            for o in (-0.06, -0.03, 0.0, 0.03, 0.06):
                for Dx in Dxs:
                    for Dz in (0.05, 0.08, 0.11):
                        act = dict(on=on, t=t, o=o, D=[float(Dx), float(Dz)])
                        Ls = np.array([act_len(f, act, A, B) for f in s[::10]]); stroke = Ls.max() - Ls.min()
                        if stroke > 0.25 or Ls.min() < stroke + 0.12: continue
                        dl = np.diff(Ls)
                        if dl.min() < 0 < dl.max(): continue
                        act["Lmin"] = float(Ls.min()); ok = True
                        for f in s[::10]:
                            (D, H, rh), (H2, E, rr), _ = LY.act_parts(f, act, A, B)
                            if min(LY.bed_d(LY.seg_pts(D, H)).min() - rh, LY.bed_d(LY.seg_pts(H2, E)).min() - rr) < CLR_BED or min(D[1], E[1]) < rh: ok = False; break
                            if layout == "mid":
                                for calf, foot in legs_near(bins, f[0][1])[::4]:
                                    d = min(LY.cap_d(LY.seg_pts(D, H), *calf).min() - rh, LY.cap_d(LY.seg_pts(H2, E), *calf).min() - rr,
                                            LY.cap_d(LY.seg_pts(D, H), *foot).min() - rh, LY.cap_d(LY.seg_pts(H2, E), *foot).min() - rr)
                                    if d < LEG_CLR: ok = False; break
                                if not ok: break
                        if not ok: continue
                        Ls2, Fh = act_forces(s[::3], act, A, B, HOLD)
                        if not np.all(np.isfinite(Fh)): continue
                        peak = float(np.abs(Fh).max())
                        if best is None or peak < best[0]: best = (peak, act)
    if best is None: return None
    peak, act = best
    Ls, Fh = act_forces(s, act, A, B, 1.5 * 100 * G); _, Fl = act_forces(s, act, A, B, 0.5 * 60 * G); _, Fl100 = act_forces(s, act, A, B, 0.5 * 100 * G)
    return dict(act, stroke=round(float(Ls.max() - Ls.min()), 3), L=[round(float(Ls.min()), 3), round(float(Ls.max()), 3)],
                F_hold100_N=round(float(np.abs(Fh).max())), F_lift60_N=round(float(np.abs(Fl).max())), F_lift100_N=round(float(np.abs(Fl100).max())),
                force_curve=dict(z=[round(float(f[0][1]), 3) for f in s[1:-1:12]], hold100=[round(float(abs(x))) for x in Fh[::12]], lift60=[round(float(abs(x))) for x in Fl[::12]]))

# ---------------------------------------------------------------- user checks with the fixed pole
def pole_effort(sub, pz, contact=None):
    """v5.2: both hands on the fixed L-handrail bar (seat_1dof_handrail.py): one grip for the whole rise, trunk angles that
    clear the bar. (v5 took the best of 3 x 8 grip points on a vertical pole at every instant: a regrip the user cannot do.)"""
    import seat_1dof_handrail as HR
    return HR.bar_effort(sub, pz, contact)

def user_job(args):
    u, cv, layout, v, act = args; ST.A_MAX = PAD_AMAX; sub, path = path_of(u)
    rows = track(sub, path, Seat(r_e=0.03), cv); good = [r for r in rows if r.get("contact") and r.get("ok")]
    if not good: return ukey(u), None
    last = good[-1]; sl = np.array([r["slip"] for r in good])
    sh = solve_s(sub, u[3], last["hz"], last["hip_x"]) or 0.0; pz = pose(sub, u[3], last["hz"], sh)
    import seat_1dof_handrail as HR
    E_rel = HR.bar_effort(sub, pz); E_st = HR.bar_effort(sub, pz, stooped=True)
    E_sup = 0.0
    for r, p_ in list(zip(rows, path))[:len(good)][::4]:
        k = min(int(r["k"]), len(cv[1]) - 1); n_ = rot(cv[2][k]) @ np.array([0, 1.0])
        e = HR.bar_effort(sub, p_, (np.array(r["P"]), n_, r["pelvis"]))
        E_sup = max(E_sup, e if e else 9)
    out = dict(release_hz=round(last["hz"], 3), phi_release=round(last["phi"], 1), fwd_slip_cm=round(100 * float(max(sl[j] - sl[:j + 1].min() for j in range(len(sl)))), 1),
               catch_min_cm=round(100 * min(r["catch"] for r in good), 1), shear_path_cm=round(100 * float(np.abs(np.diff(sl)).sum()), 1),
               E_release=None if E_rel is None else round(E_rel, 3), E_release_stooped=None if E_st is None else round(E_st, 3), E_supported_max=round(E_sup, 3))
    # clearances at the matching moment (mid layout: all parts vs legs; both: actuator vs legs)
    if v is not None:
        A, B, c1, c2 = (np.asarray(v[i:i + 2]) for i in (0, 2, 4, 6)); s = FB2.run(v, n=400); npre = len(cv[0]) - len(s); dmin = 9.0
        zrel_i = None
        for i, p_ in enumerate(path):
            r = rows[i] if i < len(rows) else None
            if r and r.get("contact") and r.get("ok"): zrel_i = min(max(int(r["k"]) - npre, 0), len(s) - 1)
            if zrel_i is None: continue
            f = s[zrel_i]; caps = LY.body_caps(p_, sub)
            parts = parts_mid(f, c1, c2, A, B) if layout == "mid" else []
            if act is not None:
                (D, H, rh), (H2, E, rr), _ = LY.act_parts(f, act, A, B); parts += [("act", LY.seg_pts(D, H), rh), ("rod", LY.seg_pts(H2, E), rr)]
            for name, pts, rad in parts:
                for cn in ("calf", "foot"): dmin = min(dmin, float(LY.cap_d(pts, *caps[cn]).min()) - rad)
        out["leg_clear_cm"] = round(100 * dmin, 1)
    return ukey(u), out

def pinch_gaps(v, s, act, layout):
    """closing gaps between moving and fixed parts (finger 25 mm rule): seat bracket/plate vs posts, rockers vs each other's posts,
    actuator rod end vs seat. Same-plane pairs only."""
    A, B, c1, c2 = (np.asarray(v[i:i + 2]) for i in (0, 2, 4, 6)); g = {}
    def upd(k, d):
        g[k] = min(g.get(k, 9.0), d)
    for f in s[::4]:
        plate, br = LY.seat_polys(f[0], f[1], c1, c2); brp = LY.poly_pts(br, 0.005); plp = LY.poly_pts(plate, 0.005)
        for nm, G0 in (("A", A), ("B", B)):
            upd(f"座板/支架—立柱{nm}", min(LY.cap_d(brp, np.array([G0[0], 0.04]), G0, 0.025).min(), LY.cap_d(plp, np.array([G0[0], 0.04]), G0, 0.025).min()))
        upd("摇杆A—立柱B", float(LY.cap_d(LY.seg_pts(A, f[2]), np.array([B[0], 0.04]), B, 0.025).min()) - 0.02)
        upd("摇杆B—立柱A", float(LY.cap_d(LY.seg_pts(B, f[3]), np.array([A[0], 0.04]), A, 0.025).min()) - 0.02)
        if act is not None:
            (D, H, rh), (H2, E, rr), _ = LY.act_parts(f, act, A, B)
            upd("推杆—座板底面", float(np.hypot(*(plp - E).T).min()) - 0.02)
            if act["on"] == "B": upd("推杆—摇杆A", float(LY.cap_d(LY.seg_pts(H2, E), A, f[2], 0.02).min()) - rr)
            else: upd("推杆—摇杆B", float(LY.cap_d(LY.seg_pts(H2, E), B, f[3], 0.02).min()) - rr)
    return {k: round(100 * d, 1) for k, d in g.items()}

if __name__ == "__main__":
    t0 = time.time()
    BINS = leg_bins(); CLOUDS = leg_clouds(BINS); print("leg bins", len(BINS), round(time.time() - t0), "s", flush=True)
    jobs = [(lay, sd) for lay in ("mid", "sides") for sd in range(4)]
    with Pool() as pool: SY = pool.map(synth, jobs)
    best = {}
    for lay, f, x in SY:
        if lay not in best or f < best[lay][0]: best[lay] = (f, x)
    print("synth", round(time.time() - t0), "s", {k: round(b[0], 4) for k, b in best.items()}, flush=True)
    out = dict(note=__doc__, phi_cap=PHI_CAP, design_curve=dict(Q=np.round(QT, 4).tolist(), phi=np.round(PT, 2).tolist()), layouts={})
    for lay, (f, x) in best.items():
        v = np.array(x); s = FB2.run(v, n=700); A, B, c1, c2 = v[0:2], v[2:4], v[4:6], v[6:8]
        info, _ = FB2.describe(x); info["phi_run_max"] = round(float(max(p[1] for p in s)), 1); info["coupler"] = round(float(np.hypot(*(c1 - c2))), 4)
        bedw, bedwhere = LY.mech_bed_clear(v, s[::5]); info["bed_clear_cm"] = round(100 * bedw, 1)
        act = actuator_search(v, s, lay, BINS); info["act"] = act
        info["pins_hold100_N"] = [round(p) for p in pin_forces(s, A, c1, c2, 1.5 * 100 * G)]
        info["pinch_cm"] = pinch_gaps(v, s, act, lay)
        cv = F1.with_prefix(np.array([p[0] for p in s]), np.array([p[1] for p in s]))
        with Pool() as pool: R = dict(pool.map(user_job, [(u, cv, lay, x, act) for u in USERS]))
        ok = lambda q: bool(q and q["fwd_slip_cm"] <= 2 and q["catch_min_cm"] >= 0)
        vals = [q for q in R.values() if q]
        summ = dict(n_ok=sum(ok(q) for q in R.values()), fwd_max=max(q["fwd_slip_cm"] for q in vals), catch_min=min(q["catch_min_cm"] for q in vals),
                    phi_release_max=max(q["phi_release"] for q in vals), E_rel_med=round(float(np.median([q["E_release"] for q in vals])), 3),
                    E_rel_max=max(q["E_release"] for q in vals), E_stooped_med=round(float(np.median([q["E_release_stooped"] for q in vals])), 3),
                    E_sup_max=max(q["E_supported_max"] for q in vals), shear_med=round(float(np.median([q["shear_path_cm"] for q in vals])), 1),
                    leg_clear_min=min(q.get("leg_clear_cm", 9) for q in vals))
        info["frames"] = [dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in s[::14]]
        out["layouts"][lay] = dict(x=x, mech=info, summary=summ, users=R)
        print(lay, {k: v_ for k, v_ in info.items() if k not in ("frames", "act")}, flush=True)
        print("  act", None if act is None else {k: v_ for k, v_ in act.items() if k != "force_curve"}, flush=True)
        print("  summary", summ, flush=True)
    json.dump(out, open(os.path.join(OUT, "v5.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s")
