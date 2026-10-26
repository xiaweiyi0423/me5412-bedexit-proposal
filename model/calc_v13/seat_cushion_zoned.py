"""Zoned seat cushion (rear firm, front soft): can it move the seat's push from the thigh to the pelvis?

Same cushion model as seat_cushion.py (bed of independent springs, p = k * squeeze, width 0.24 m, bottoming at 0.8 t) on the
v5 slider curve (CUSH_MECH=slider), the seat pushing 0.5 BW. 81 users x 4 rise stages (15 / 35 / 55 / 70 %).
A cushion here has a rear zone (seat-frame x < split) and a front zone with their own stiffness and thickness; the front
zone's top can also be lowered by `drop` (a pre-shaped step, 1 cm ramp) - a shape change, not a stiffness change.

Per case: pelvis share = part of the seat force on the body outline with a <= 4 cm (a = distance along the back of the body
from the buttock-thigh junction, + towards the knee); centre of pressure a; where the peak pressure is; peak pressure; sink;
'lost' = the seat reaches the end of travel before the cushion carries 0.5 BW; sitting squeeze (60 kg, 0.75 BW, level seat).
Pass 2 (selected cushions): effort with the force split into its pelvis part (helps hip and knee) and thigh part (knee only),
hand on the fixed pole (x 0.69, z 0.85 / 0.95 / 1.05, best).
Output: seat_1dof/cushion_zoned.json
"""
import json, os, sys, time
os.environ["CUSH_MECH"] = "slider"
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
import seat_cushion as SC
from seat_trajectory import rot, effort
from seat_1dof_design import USERS, ukey, path_of
from model import G

OUT = os.path.join(HERE, "seat_1dof"); W = SC.W; SEAT = SC.SEAT; STAGES = SC.STAGES
# the seat's own curve: the slider run to the end of its rail (rail_ext in slider.json; RAIL_EXT overrides)
import seat_1dof_slider as SL
from seat_1dof_fourbar import with_prefix
_sim, _ = SL.simulate(json.load(open(os.path.join(OUT, "slider.json")))["x"], 900)
CV = with_prefix(np.array([p[0] for p in _sim]), np.array([p[1] for p in _sim])); TOP = round(float(_sim[-1][0][1]), 3)
PA = float(os.environ.get("PELVIS_A", ST.PELVIS_A))

def C_(name, kr, kf, tr=0.05, tf=0.05, split=0.0, drop=0.0):
    return dict(name=name, kr=kr, kf=kf, tr=tr, tf=tf, split=split, drop=drop)

def top_z(x, c):
    """uncompressed cushion top in the seat frame: the seat profile, the front zone lowered by `drop` over a 1 cm ramp."""
    return SEAT.top(x) - c["drop"] * np.clip((x - c["split"]) / 0.01, 0, 1)

def load(u, P, A, ds, c):
    Q, phi = SC.pose_at(u, CV); Rm = rot(phi); loc = (P - Q) @ Rm; x, z = loc[:, 0], loc[:, 1]
    inside = (x >= -SEAT.h) & (x <= SEAT.h); sq = np.clip(np.where(inside, top_z(x, c) - z, 0.0), 0, None)
    front = x >= c["split"]; k = np.where(front, c["kf"], c["kr"]) * 1e5; t = np.where(front, c["tf"], c["tr"])
    bott = sq > 0.8 * t
    p = k * np.minimum(sq, 0.8 * t) + np.where(bott, 50 * k * (sq - 0.8 * t), 0)
    m = sq > 0; xm = x[m]; d = (SEAT.top(xm + 1e-4) - SEAT.top(xm - 1e-4)) / 2e-4
    nl = np.stack([-d, np.ones_like(d)], 1) / np.hypot(d, 1)[:, None]; nrm = nl @ Rm.T
    f = (p[m] * ds[m] * W)[:, None] * nrm
    F = f.sum(0) if len(f) else np.zeros(2)
    return dict(F=F, Fm=float(np.hypot(*F)), p=p, sq=sq, bott=bool(bott[m].any()), f=f, idx=np.where(m)[0], x=x)

def solve(sub, pz, c, k0=0.0):
    P, A, ds = SC.dense_outline(pz); target = 0.5 * sub.M * G; n = len(CV[0]) - 1
    u = max(k0, 0.0); prev = u; L = load(u, P, A, ds, c)
    while L["Fm"] < target:
        prev = u; u += 4.0
        if u >= n: return None, (P, A, ds)
        L = load(u, P, A, ds, c)
    lo, hi = prev, u
    for _ in range(25):
        mid = (lo + hi) / 2
        if load(mid, P, A, ds, c)["Fm"] >= target: hi = mid
        else: lo = mid
    return (hi, load(hi, P, A, ds, c)), (P, A, ds)

def metrics(res, P, A, ds, c):
    u, L = res; idx = L["idx"]; fm = np.hypot(*L["f"].T); a = A[idx]; pel = a <= PA
    w = L["p"][idx] * ds[idx]; ipk = int(np.argmax(L["p"][idx]))
    xs = L["x"][idx]
    return dict(pel_share=round(float(fm[pel].sum() / fm.sum()), 3), cop_a_cm=round(100 * float((a * w).sum() / w.sum()), 1),
                peak_a_cm=round(100 * float(a[ipk]), 1), p_peak_kPa=round(float(L["p"][idx].max()) / 1000, 1),
                sink_mm=round(1000 * float(L["sq"].max()), 1), contact_cm=round(100 * float(ds[idx].sum()), 1), bottom=L["bott"],
                junction_seat_x_cm=round(100 * float(np.interp(0.0, A, L["x"])), 1), pelvis_end_seat_x_cm=round(100 * float(np.interp(PA, A, L["x"])), 1), u=round(float(u), 2))

def contact_parts(res, P, A, ds, BW=None):
    """the seat force per unit of its magnitude, as (point, force, on pelvis) groups: pelvis part and thigh part, each at its centre."""
    u, L = res; idx = L["idx"]; f = L["f"]; Fm = L["Fm"]; pel = A[idx] <= PA; parts = []
    for msk, isp in ((pel, True), (~pel, False)):
        if not msk.any(): continue
        fs = f[msk]; Fp = fs.sum(0); mag = np.hypot(*fs.T)
        Cp = (P[idx][msk] * mag[:, None]).sum(0) / mag.sum()
        parts.append((Cp, Fp / Fm, isp))
    return dict(parts=parts, cap=0.5 if BW is None else min(0.5, Fm / BW))

def pole_effort(sub, pz, contact):
    best = None; cap = contact.get("cap", 0.5) if isinstance(contact, dict) else 0.5
    for zb in (0.85, 0.95, 1.05):
        r = effort(sub, pz, np.array([0.69, zb]), contact, cap=cap)
        if r and (best is None or r[0] < best): best = r[0]
    return best

def stage_pose(user, stage):
    sub, path = path_of(user); pz = min(path, key=lambda q: abs(q["f"] - stage)); return sub, pz

def job_geom(args):
    user, stage, c = args; sub, pz = stage_pose(user, stage); res, (P, A, ds) = solve(sub, pz, c)
    if res is None: return None
    return metrics(res, P, A, ds, c)

def job_effort(args):
    """effort with the cushion force split into pelvis / thigh parts. If the seat runs out of travel before reaching 0.5 BW
    ('lost'), the seat stops at the end of travel and pushes with whatever force the cushion gives there: effort_all uses that."""
    user, stage, c = args; sub, pz = stage_pose(user, stage); res, (P, A, ds) = solve(sub, pz, c)
    free = pole_effort(sub, pz, None)
    if res is None:
        n = len(CV[0]) - 1; L = load(float(n), P, A, ds, c); frac = L["Fm"] / (sub.M * G)
        e = pole_effort(sub, pz, contact_parts((float(n), L), P, A, ds, sub.M * G)) if L["Fm"] > 1.0 else free
        global_cap = round(frac, 3)
        return dict(lost=True, effort_all=e if e is not None else free, effort_free=free, end_force_BW=global_cap)
    m = metrics(res, P, A, ds, c); m["effort"] = pole_effort(sub, pz, contact_parts(res, P, A, ds)); m["effort_free"] = free
    m["effort_all"] = m["effort"]; m["lost"] = False
    return m

def sitdown(c):
    sub, path = path_of((1.60, 0.09, 1.0, 0.29)); pz = path[0]; P, A, ds = SC.dense_outline(pz); target = 0.75 * 60 * G
    for dz in np.arange(-0.03, 0.12, 0.0005):
        Q = CV[1][15] + np.array([0, dz]); loc = P - Q; x, z = loc[:, 0], loc[:, 1]; inside = (x >= -SEAT.h) & (x <= SEAT.h)
        sq = np.clip(np.where(inside, top_z(x, c) - z, 0), 0, None); front = x >= c["split"]
        k = np.where(front, c["kf"], c["kr"]) * 1e5; t = np.where(front, c["tf"], c["tr"])
        F = float((k * np.minimum(sq, 0.8 * t) * ds * W).sum())
        if F >= target or (sq > 0.8 * t).any():
            p = k * np.minimum(sq, 0.8 * t)
            return dict(sink_mm=round(1000 * float(sq.max()), 1), bottom=bool((sq > 0.8 * t).any()), p_peak_kPa=round(float(p.max()) / 1000, 1))
    return None

def summarize(rows):
    rs = [r for r in rows if r]; out = dict(n=len(rows), lost=len(rows) - len(rs))
    for k in ("effort_all", "effort_free"):            # over every case, the lost ones included
        xs = [r[k] for r in rows if r and r.get(k) is not None]
        if xs: out[k] = dict(med=round(float(np.median(xs)), 3), p10=round(float(np.percentile(xs, 10)), 3), p90=round(float(np.percentile(xs, 90)), 3), max=round(float(max(xs)), 3))
    rs = [r for r in rs if not r.get("lost")]; out["lost"] = len(rows) - len(rs)
    for k in ("pel_share", "cop_a_cm", "peak_a_cm", "p_peak_kPa", "sink_mm", "contact_cm", "effort"):
        xs = [r[k] for r in rs if r.get(k) is not None]
        if xs: out[k] = dict(med=round(float(np.median(xs)), 3), p10=round(float(np.percentile(xs, 10)), 3), p90=round(float(np.percentile(xs, 90)), 3), max=round(float(max(xs)), 3))
    out["bottom_share"] = round(sum(r["bottom"] for r in rs) / max(len(rs), 1), 2)
    out["peak_on_pelvis_share"] = round(sum(r["peak_a_cm"] <= 100 * PA for r in rs) / max(len(rs), 1), 2)
    for k in ("junction_seat_x_cm", "pelvis_end_seat_x_cm"):
        js = [r[k] for r in rs if r.get(k) is not None]
        if js: out[k] = dict(med=float(np.median(js)), p10=float(np.percentile(js, 10)), p90=float(np.percentile(js, 90)))
    return out

if __name__ == "__main__":
    t0 = time.time(); mode = sys.argv[1] if len(sys.argv) > 1 else "grid"
    path_out = os.path.join(OUT, os.environ.get("ZONED_OUT", "cushion_zoned.json"))
    prev = json.load(open(path_out)) if os.path.exists(path_out) else {}
    if mode == "grid":
        cush = [C_("均匀 6/6，5 cm（现推荐）", 6, 6)]
        for split in (-0.04, -0.02, 0.0, 0.02):
            for kr, kf in ((10, 3), (15, 2), (20, 1.5), (30, 1)):
                cush.append(C_(f"后 {kr} / 前 {kf}，分界 {round(100 * split)} cm", kr, kf, 0.05, 0.08, split))
        for split in (-0.02, 0.0, 0.02):
            for drop in (0.01, 0.02, 0.03):
                cush.append(C_(f"后 15 / 前 2，分界 {round(100 * split)} cm，前区顶面低 {round(100 * drop)} cm", 15, 2, 0.05, 0.08, split, drop))
        jobs = [(u, s, c) for c in cush for u in USERS for s in STAGES]
        with Pool() as pool: R = pool.map(job_geom, jobs, chunksize=8)
        out = dict(note=__doc__, grid={})
        for i, c in enumerate(cush):
            rows = R[i * len(USERS) * len(STAGES):(i + 1) * len(USERS) * len(STAGES)]
            by = {str(s): summarize([r for (u, s_, _), r in zip(jobs[i * len(USERS) * len(STAGES):(i + 1) * len(USERS) * len(STAGES)], rows) if s_ == s]) for s in STAGES}
            out["grid"][c["name"]] = dict(c=c, all=summarize(rows), by_stage=by, sitdown=sitdown(c))
            a = out["grid"][c["name"]]["all"]
            print(f'{c["name"]:34s} lost {a["lost"]:3d} pel {a["pel_share"]["med"]:.2f} peak@pel {a["peak_on_pelvis_share"]:.2f} cop {a["cop_a_cm"]["med"]:5.1f} '
                  f'peak_a {a["peak_a_cm"]["med"]:5.1f} p {a["p_peak_kPa"]["med"]:5.1f}/{a["p_peak_kPa"]["max"]:5.1f} sink {a["sink_mm"]["med"]:5.1f} bott {a["bottom_share"]:.2f} sit {out["grid"][c["name"]]["sitdown"]}', flush=True)
        out["effort"] = prev.get("effort", {})
    else:                                  # effort pass on named cushions: python3 seat_cushion_zoned.py effort "<name>" ...
        out = prev; names = sys.argv[2:]
        for nm in names:
            c = out["grid"][nm]["c"]; jobs = [(u, s, c) for u in USERS for s in STAGES]
            with Pool() as pool: R = pool.map(job_effort, jobs, chunksize=4)
            out.setdefault("effort", {})[nm] = dict(all=summarize(R), by_stage={str(s): summarize([r for (u, s_, _), r in zip(jobs, R) if s_ == s]) for s in STAGES},
                                                    rows=[dict(user=ukey(u), stage=s, **(r or {})) for (u, s, _), r in zip(jobs, R)])
            e = out["effort"][nm]["all"]; print(nm, "effort", e.get("effort"), "free", e.get("effort_free"), "pel", e.get("pel_share"), flush=True)
    json.dump(out, open(path_out, "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s")
