"""Seat cushion stiffness: what it does to pressure, where the push acts, how far the seat must travel, and the force loop.

Cushion model: a bed of independent springs over the seat surface (pressure p = k * local squeeze, k in kPa per cm of
squeeze), foam thickness t; squeeze beyond 0.8 t counts as bottoming (the seat plate then pushes directly). Contact width
across the body 0.24 m (two buttocks / thighs). The seat follows the user by force: it moves along the four-bar's curve
until the cushion force equals the target (0.5 BW for a 60 kg user while lifting).

For each cushion and each user (81) at four stages of the rise:
  squeeze (sink), peak pressure, contact length, centre of pressure on the body (distance along the back of the thigh from the
  buttock-thigh junction; <= 4 cm counts as pushing the pelvis), extra seat travel compared with a rigid seat, the effort
  with the resultant force at the centre of pressure, and the force-loop time constant tau = 1 / (k_v * dF/dq) of the speed
  rule v = k_v (F_cap - F_seat) with k_v = 3 cm/s per 0.35 BW.
Sitting: 60 kg user resting on the level seat at bed height (about 0.75 BW on the seat, feet carry the rest) -> squeeze, does the cushion bottom out?
Output: seat_1dof/cushion.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import Seat, rot, body_points, effort, bar_at, Z0
from seat_1dof_design import USERS, ukey, path_of
from seat_1dof_fourbar import sim_mech, with_prefix
from model import G, Subject

OUT = os.path.join(HERE, "seat_1dof"); W = 0.24; STAGES = (0.15, 0.35, 0.55, 0.70)
FB = json.load(open(os.path.join(OUT, "fourbar.json")))["mech"]["1000.0"]
V = np.array(FB["A"] + FB["B"] + FB["c1"] + FB["c2"])

def fourbar_sim(top, n=900):
    """the flat-seat four-bar, run from the flush seat until the seat centre reaches `top` (it can go past the design top)."""
    import seat_1dof_fourbar as F
    A, B, c1, c2 = V[:2], V[2:4], V[4:6], V[6:8]; P10, P20 = F.QT[0] + c1, F.QT[0] + c2
    L1, L2 = np.hypot(*(P10 - A)), np.hypot(*(P20 - B)); a0 = np.arctan2(*(P10 - A)[::-1])
    s = F.sim_partial(A, L1, B, L2, c1, c2, a0, a0 - np.radians(125), n, P20)
    k = next(i for i, p in enumerate(s) if p[0][1] >= top); return s[:k + 1]

SIMS = {t: fourbar_sim(t) for t in (0.6285, 0.66)}
CVS = {t: with_prefix(np.array([p[0] for p in s]), np.array([p[1] for p in s])) for t, s in SIMS.items()}
CV = CVS[0.6285]
# cushions: (name, k front kPa/cm, k rear kPa/cm, thickness m, split x in seat frame: rear part is x < split)
CUSH = [("硬（几乎刚性）", 20.0, 20.0, 0.03, 0.0, 0.6285), ("中硬", 6.0, 6.0, 0.05, 0.0, 0.6285), ("中软", 3.0, 3.0, 0.06, 0.0, 0.6285),
        ("软", 1.5, 1.5, 0.08, 0.0, 0.6285), ("分区：后硬前软", 2.0, 6.0, 0.06, 0.0, 0.6285), ("分区：后软前硬", 6.0, 2.0, 0.06, 0.0, 0.6285),
        ("中硬 + 行程到 0.66 m", 6.0, 6.0, 0.05, 0.0, 0.66), ("分区（前 3）+ 行程到 0.66 m", 3.0, 6.0, 0.07, 0.0, 0.66)]
SEAT = Seat(r_e=0.03)

def dense_outline(pz):
    pts, kind, aa = body_points(pz)
    order = np.argsort(aa); pts, kind, aa = pts[order], kind[order], aa[order]
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]); t = np.arange(0, s[-1], 0.002)
    P = np.c_[np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])]; A = np.interp(t, s, aa)
    return P, A, np.gradient(t)

def pose_at(u, CV=None):
    CV = CV if CV is not None else CVS[0.6285]
    i = int(np.clip(np.floor(u), 0, len(CV[0]) - 2)); w = u - i
    return (1 - w) * CV[1][i] + w * CV[1][i + 1], (1 - w) * CV[2][i] + w * CV[2][i + 1]

def load(u, P, A, ds, c):
    name, kf, kr, t, split, top = c
    Q, phi = pose_at(u, CVS[top]); Rm = rot(phi); loc = (P - Q) @ Rm; x, z = loc[:, 0], loc[:, 1]
    inside = (x >= -SEAT.h) & (x <= SEAT.h); sq = np.where(inside, SEAT.top(x) - z, 0.0); sq = np.clip(sq, 0, None)
    k = np.where(x < split, kr, kf) * 1e5                        # kPa/cm -> N/m^3
    bott = sq > 0.8 * t
    p = k * np.minimum(sq, 0.8 * t) + np.where(bott, 50 * k * (sq - 0.8 * t), 0)   # bottoming: very stiff
    nrm = np.array([Rm @ SEAT.normal(xx) for xx in x[sq > 0]]) if (sq > 0).any() else np.zeros((0, 2))
    f = (p[sq > 0] * ds[sq > 0] * W)[:, None] * nrm; F = f.sum(0)
    return dict(F=F, Fm=float(np.hypot(*F)), p=p, sq=sq, bott=bool(bott.any()), f=f, idx=np.where(sq > 0)[0])

def solve_stage(args):
    user, stage, c = args; sub, path = path_of(user); pz = min(path, key=lambda q: abs(q["f"] - stage))
    P, A, ds = dense_outline(pz); target = 0.5 * sub.M * G; CV = CVS[c[5]]
    us = np.arange(0, len(CV[0]) - 1, 1.0); prev = None; u_touch = None
    for uu in us:
        L = load(uu, P, A, ds, c)
        if u_touch is None and L["Fm"] > 1.0: u_touch = uu
        if L["Fm"] >= target:
            lo, hi = (prev if prev is not None else uu), uu
            for _ in range(30):
                mid = (lo + hi) / 2
                if load(mid, P, A, ds, c)["Fm"] >= target: hi = mid
                else: lo = mid
            break
        prev = uu
    else:
        return None
    L = load(hi, P, A, ds, c); L2 = load(hi + 0.5, P, A, ds, c)
    Q1, _ = pose_at(hi, CV); Q0, _ = pose_at(u_touch, CV); Q2, _ = pose_at(hi + 0.5, CV)
    dq = np.hypot(*(Q2 - Q1)); kq = (L2["Fm"] - L["Fm"]) / max(dq, 1e-6)          # N per m of seat travel
    kv = 0.03 / (0.35 * sub.M * G); tau = 1 / (kv * kq) if kq > 0 else None
    w = L["p"][L["idx"]] * ds[L["idx"]]; a_cop = float((A[L["idx"]] * w).sum() / w.sum())
    cop = (P[L["idx"]] * w[:, None]).sum(0) / w.sum()
    fdir = L["F"] / L["Fm"]; pel = a_cop <= ST.PELVIS_A
    e = effort(sub, pz, bar_at(pz["Hp"][1]), (cop, fdir, pel), cap=0.5)
    clen = float(ds[L["idx"]].sum())
    return dict(user=ukey(user), stage=stage, sink_mm=round(1000 * float(L["sq"].max()), 1), p_peak_kPa=round(float(L["p"].max()) / 1000, 1),
                contact_cm=round(100 * clen, 1), cop_a_cm=round(100 * a_cop, 1), extra_travel_mm=round(1000 * float(np.hypot(*(Q1 - Q0))), 1),
                bottom=L["bott"], tau_s=None if tau is None else round(tau, 2), effort=None if e is None else round(e[0], 3))

def sitdown(c):
    """60 kg, 0.75 BW on the level seat at bed height (typical user): squeeze and bottoming."""
    sub, path = path_of((1.60, 0.09, 1.0, 0.29)); pz = path[0]; P, A, ds = dense_outline(pz); target = 0.75 * 60 * G
    for dz in np.arange(-0.03, 0.12, 0.0005):
        Q = CV[1][15] + np.array([0, dz]); name, kf, kr, t, split, top = c
        loc = P - Q; x, z = loc[:, 0], loc[:, 1]; inside = (x >= -SEAT.h) & (x <= SEAT.h)
        sq = np.clip(np.where(inside, SEAT.top(x) - z, 0), 0, None); k = np.where(x < split, kr, kf) * 1e5
        F = float((k * np.minimum(sq, 0.8 * t) * ds * W).sum())
        if F >= target or (sq > 0.8 * t).any(): return dict(sink_mm=round(1000 * float(sq.max()), 1), bottom=bool((sq > 0.8 * t).any()), F_BW=round(F / (60 * G), 2))
    return None

if __name__ == "__main__":
    t0 = time.time()
    jobs = [(u, s, c) for c in CUSH for u in USERS for s in STAGES]
    with Pool() as pool: R = pool.map(solve_stage, jobs)
    out = dict(note=__doc__, cushions=[dict(name=c[0], k_front=c[1], k_rear=c[2], t=c[3], top=c[5]) for c in CUSH], rows={}, summary={}, sitdown={})
    for (u, s, c), r in zip(jobs, R): out["rows"].setdefault(c[0], []).append(r)
    for c in CUSH:
        rs = [r for r in out["rows"][c[0]] if r]; nfail = len(out["rows"][c[0]]) - len(rs)
        def q(k, fn): xs = [r[k] for r in rs if r[k] is not None]; return round(float(fn(xs)), 3)
        stg = {str(st_): sum(1 for (uu, ss), r in zip([(u, s_) for u in USERS for s_ in STAGES], out["rows"][c[0]]) if ss == st_ and r is None) for st_ in STAGES}
        out["summary"][c[0]] = dict(lost_by_stage=stg, sink_med_mm=q("sink_mm", np.median), sink_max_mm=q("sink_mm", max), p_med_kPa=q("p_peak_kPa", np.median), p_max_kPa=q("p_peak_kPa", max),
                                    contact_med_cm=q("contact_cm", np.median), cop_pelvis_share=round(sum(r["cop_a_cm"] <= 100 * ST.PELVIS_A for r in rs) / len(rs), 2),
                                    cop_a_med_cm=q("cop_a_cm", np.median), extra_travel_med_mm=q("extra_travel_mm", np.median), extra_travel_max_mm=q("extra_travel_mm", max),
                                    bottom_share=round(sum(r["bottom"] for r in rs) / len(rs), 2), tau_med_s=q("tau_s", np.median), tau_max_s=q("tau_s", max),
                                    effort_med=q("effort", np.median), effort_max=q("effort", max), n_fail=nfail)
        out["sitdown"][c[0]] = sitdown(c)
        print(f"{c[0]:12s}", out["summary"][c[0]], out["sitdown"][c[0]])
    json.dump(out, open(os.path.join(OUT, "cushion.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s")
