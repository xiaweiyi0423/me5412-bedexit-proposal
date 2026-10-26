"""Relative motion between the user and the seat during the rise (sagittal plane).

Why: as the user rises, the hip moves forward and the thigh steepens. A seat that only rises vertically and stays level
does not move with the body, so the body slides forward over it and the support shrinks to the front edge. This script
measures that, stage by stage, for several seat motions, and draws the sagittal-plane picture.

What counts as the unstable direction. Rising means bringing the body's weight forward over the feet; the fall that a
bed-exit aid must prevent is the fall backward / down onto or past the seat. Relative motion is bad when it
  (1) slides the body forward over the seat: friction on the body then points backward (against the rise) and the skin is
      sheared; measured as slip of the body over the seat surface (cm, + = body forward);
  (2) leaves less seat under the buttock: if the user sits back at that instant, where does the buttock land? Measured as
      the catch margin = seat front edge minus the sitting pressure centre (4 cm behind the hip joint); negative = lands
      on or past the front edge;
  (3) shrinks the contact to an edge: contact length = length of the body outline within 1.5 cm of the seat surface
      (a 1.5 cm cushion squeeze), a stand-in for contact area per unit width.
A forward-tilted seat has its own limit: if the user drops back onto it, the seat slope pushes them forward-down; with
cloth on cushion friction about 0.4-0.5 the slope should stay below about 20-25 deg at the moment of a sit-back.

Seat motions compared (all start flush and level with the bed at 0.42 m):
  V        vertical lift, seat level (current design), top 0.66 m
  FIT-typ  one DOF, path fitted once to a typical user: the seat moves as if fixed to that user's thigh (it keeps the
           seated thigh-seat relation), tilting with the thigh up to phi_max, then carries on moving with the hip at
           phi_max; the same curve is used for everyone
  FIT-adj  the same kind of one-DOF curve, re-fitted to each user's body size and foot position (a set-up adjustment, still
           one motor), but not to the day-to-day rising style
  FOLLOW   the seat follows each rise exactly (needs x, z and tilt in real time: three DOF + sensing); upper bound
For FIT and FOLLOW the seat is force-following along its curve, like the current lift: it advances until it touches.
"""
import json, os, sys, itertools
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from model import Subject
from seat_trajectory import (Z0, R_B, SEAT_X0, SEAT_X1, PELVIS_A, A_MAX, BACK_LIMIT, Seat, rot, body_points, pose, hz_grid,
                             S_GRID, BAR_X, bar_at)

OUT = os.path.join(HERE, "seat_trajectory")
Q0 = np.array([(SEAT_X0 + SEAT_X1) / 2, Z0])
SIT_BEHIND = 0.04; CUSHION = 0.015; DH = 0.004
TYP = (1.60, 0.29, 1.0)
PERSONS = list(itertools.product([1.50, 1.60, 1.75], [0.25, 0.29, 0.33], [0.6, 1.0, 2.5]))

# ---------------------------------------------------------------- the user's rise
def solve_s(sub, x_a, hz, hip_x):
    """shank tilt that puts the hip at hip_x for hip height hz (bisection; hip x increases with s)."""
    lo, hi = -15.0, 45.0
    def hx(s):
        p = pose(sub, x_a, hz, s); return None if p is None else p["Hp"][0]
    if hx(lo) is None or hx(hi) is None: return None
    if not (hx(lo) <= hip_x <= hx(hi)): return None
    for _ in range(40):
        m = (lo + hi) / 2
        if hx(m) < hip_x: lo = m
        else: hi = m
    return (lo + hi) / 2

def rise(H, x_a, p, hip0=0.10, r_b=R_B):
    """hip goes from (hip0, seated) to above the ankle at standing; x(f) = hip0 + (x_a - hip0) f^p, f = rise fraction.
    p < 1: hip forward early (lean-first); p = 1: proportional; p > 1: hip stays back, moves forward late."""
    sub = Subject(H=H); hz0 = Z0 + r_b; hz1 = sub.ankle_h + sub.L_shank + sub.L_thigh - 0.012
    out = []
    for hz in np.arange(hz0, hz1 + 1e-9, DH):
        f = (hz - hz0) / (hz1 - hz0); hx = hip0 + (x_a - hip0) * f ** p
        s = solve_s(sub, x_a, hz, hx)
        if s is None: continue
        pz = pose(sub, x_a, hz, s); pz["f"] = f; pz["r_b"] = r_b; out.append(pz)
    return sub, out

# ---------------------------------------------------------------- seat curves
def curve_vertical(top=0.66):
    q = np.arange(-0.03, top - Z0 + 1e-9, 0.002)
    return q, Q0 + q[:, None] * np.array([0.0, 1.0]), np.zeros(len(q))

def curve_fit(path, phi_max=30.0, top=0.66, stop_at_max=False):
    """seat pose = seated seat pose carried by the user's thigh: rotate by the thigh's extra slope (<= phi_max) about the
    hip and translate with the hip. Parameter = travel index along the user's rise."""
    p0 = path[0]; th0 = p0["theta"]; rel = Q0 - p0["Hp"]
    Q, phi = [], []
    for pz in path:
        a = min(pz["theta"] - th0, phi_max); a = max(a, 0.0)
        Rm = rot(a); Qk = pz["Hp"] + Rm @ rel
        if Qk[1] > top: break
        Q.append(Qk); phi.append(a)
        if stop_at_max and pz["theta"] - th0 >= phi_max: break
    Q = np.array(Q); phi = np.array(phi)
    # extend the start 3 cm below flush so a heavier sink-in still finds the seat
    pre = np.array([Q[0] - np.array([0, d]) for d in np.arange(0.03, 0, -0.002)])
    return np.arange(len(pre) + len(Q)) * 1.0, np.vstack([pre, Q]), np.concatenate([np.zeros(len(pre)), phi])

def touch(seat, curve, pts, k_hint=0):
    """first pose along the curve that touches (force-following seat). Returns index, point index, local x, gap array."""
    qs, Qs, phis = curve
    for k in range(len(qs)):
        loc = (pts - Qs[k]) @ rot(phis[k]); x, z = loc[:, 0], loc[:, 1]
        inside = (x >= -seat.h) & (x <= seat.h)
        gap = np.where(inside, z - seat.top(x), np.inf); gap = np.where(gap < -seat.t, np.inf, gap)
        j = int(np.argmin(gap))
        if gap[j] <= 0: return k, j, x, gap
    return None

def outline_len(pts, gap, tol=CUSHION):
    near = gap <= tol; L = 0.0
    for i in range(len(pts) - 1):
        if near[i] and near[i + 1]: L += float(np.hypot(*(pts[i + 1] - pts[i])))
    return L

def body_frame_point(pz, P, a):
    """a body point in material coordinates: buttock (a <= 0) moves with the hip (pelvis kept upright), thigh points
    move with the thigh."""
    d = P - pz["Hp"]
    if a <= 0: return ("pelvis", d)
    u = pz["u"]; n = np.array([u[1], -u[0]]); return ("thigh", np.array([d @ u, d @ n]))

def carry(pz, c):
    kind, v = c
    if kind == "pelvis": return pz["Hp"] + v
    u = pz["u"]; n = np.array([u[1], -u[0]]); return pz["Hp"] + v[0] * u + v[1] * n

# ---------------------------------------------------------------- one user x one seat motion
def track(sub, path, seat, curve, follow=False):
    rows = []; prev = None; slip = 0.0
    for i, pz in enumerate(path):
        pts, kind, aa = body_points(pz)
        cv = curve
        if follow:   # the curve is this user's own rise: this instant's seat pose, searched from 3 cm below it
            k = i + 15
            if k >= len(curve[0]): rows.append(dict(hz=float(pz["Hp"][1]), contact=False)); break
            off = np.arange(-0.03, 0.0101, 0.001)
            cv = (off, curve[1][k] + off[:, None] * np.array([0.0, 1.0]), np.full(len(off), curve[2][k]))
        t = touch(seat, cv, pts)
        if t is None: rows.append(dict(hz=float(pz["Hp"][1]), contact=False)); break
        k, j, xl, gap = t
        Qk, ph = cv[1][k], cv[2][k]; Rm = rot(ph)
        front = Qk + Rm @ np.array([seat.h, seat.top(np.array([seat.h - 1e-4]))[0]])
        ok = kind[j] < 2
        row = dict(hz=float(pz["Hp"][1]), f=float(pz["f"]), hip_x=float(pz["Hp"][0]), theta=float(pz["theta"]),
                   contact=True, ok=bool(ok), pelvis=bool(kind[j] == 0), a=float(aa[j]), seat_x=float(xl[j]), phi=float(ph),
                   seat_top=float(Qk[1]), front_x=float(front[0]), catch=float(front[0] - (pz["Hp"][0] - SIT_BEHIND)),
                   contact_len=outline_len(pts, gap), P=pts[j].tolist(), Q=Qk.tolist(), k=int(k))
        if prev is not None:   # slip: last contact's body point carried to now, against the last contact's seat point
            pb = carry(pz, prev["bf"]); loc_now = (pb - Qk) @ Rm
            slip += float(loc_now[0] - prev["seat_x"])
        row["slip"] = slip
        row["bf"] = body_frame_point(pz, pts[j], aa[j]); rows.append(row); prev = row
        if not ok: break
    for r in rows: r.pop("bf", None)
    return rows

def summarize(rows):
    good = [r for r in rows if r.get("contact") and r.get("ok")]
    if not good: return dict(release_hz=None)
    last = good[-1]
    return dict(release_hz=round(last["hz"], 3), release_f=round(last["f"], 2), slip_cm=round(100 * last["slip"], 1),
                min_catch_cm=round(100 * min(r["catch"] for r in good), 1), catch_at_release_cm=round(100 * last["catch"], 1),
                contact_len_release_cm=round(100 * last["contact_len"], 1),
                pelvis_share=round(sum(r["pelvis"] for r in good) / len(good), 2), phi_release=round(last["phi"], 1),
                why_end=("travel or reach" if rows[-1].get("contact") is False or rows[-1].get("ok", True)
                         else ("thigh too far down" if rows[-1]["a"] > 0 else "back of buttock")))

def E0_at(maps, H, x_a, hz, theta_s):
    m = maps.get((H, x_a))
    if m is None: return None
    hzs = np.array(m["hz"]); E = np.array(m["E0"])
    i = int(np.clip(np.searchsorted(hzs, hz) - 1, 0, len(hzs) - 2)); w = (hz - hzs[i]) / (hzs[i + 1] - hzs[i])
    j = int(np.argmin(abs(S_GRID - theta_s)))
    e = (1 - w) * E[i, j] + w * E[i + 1, j]
    return None if not np.isfinite(e) else round(float(e), 3)

def shank_of(sub, x_a, hz, hip_x): return solve_s(sub, x_a, hz, hip_x)

if __name__ == "__main__":
    maps = {}
    mp = os.path.join(OUT, "maps.json")
    if os.path.exists(mp): maps = {tuple(json.loads(k)): v for k, v in json.load(open(mp)).items()}
    _, typ_path = rise(*TYP)
    seats = {"standard": Seat(), "bolster": Seat(r_e=0.06), "deep+bolster": Seat(depth=0.23, r_e=0.06)}
    designs = {
        "V": ("V", dict()),
        "V top0.72": ("V72", dict()),
        "FIT-typ p20": ("FIT", dict(phi_max=20)),
        "FIT-typ p30": ("FIT", dict(phi_max=30)),
        "FIT-typ p45": ("FIT", dict(phi_max=45)),
        "FIT-typ p30 stop": ("FIT", dict(phi_max=30, stop_at_max=True)),
        "FIT-typ p30 top0.72": ("FIT", dict(phi_max=30, top=0.72)),
        "FIT-adj p30": ("ADJ", dict(phi_max=30)),
        "FOLLOW p30": ("FOL", dict(phi_max=30)),
    }
    res = {}; detail = {}
    for (H, x_a, p) in PERSONS:
        sub, path = rise(H, x_a, p)
        _, adj_path = rise(H, x_a, 1.0)
        for dn, (kind, kw) in designs.items():
            for sn, seat in seats.items():
                if sn != "standard" and not dn.startswith(("V", "FIT-typ p30")): continue
                if kind == "V": cv = curve_vertical(); fol = False
                elif kind == "V72": cv = curve_vertical(0.72); fol = False
                elif kind == "FIT": cv = curve_fit(typ_path, **kw); fol = False
                elif kind == "ADJ": cv = curve_fit(adj_path, **kw); fol = False
                else: cv = curve_fit(path, **kw); fol = True
                rows = track(sub, path, seat, cv, follow=fol)
                s = summarize(rows)
                if s["release_hz"]:
                    last = [r for r in rows if r.get("ok")][-1]
                    s["E0_release"] = E0_at(maps, H, x_a, last["hz"], shank_of(sub, x_a, last["hz"], last["hip_x"]) or 0)
                key = f"H{H:.2f} xa{x_a:.2f} p{p}"
                res.setdefault(f"{dn} | {sn}", {})[key] = s
                if (H, x_a) == (1.60, 0.29) or (p == 1.0 and x_a == 0.29):
                    detail[f"{dn} | {sn} | {key}"] = rows
    json.dump(dict(note=__doc__, results=res), open(os.path.join(OUT, "relative_motion.json"), "w"), indent=1)
    json.dump(detail, open(os.path.join(OUT, "relative_motion_detail.json"), "w"))
    # compact table: median and worst over the 27 users
    for d, by in res.items():
        vals = list(by.values())
        def col(k, fn):
            xs = [v[k] for v in vals if v.get(k) is not None]; return None if not xs else fn(xs)
        print(f"{d:32s} release hz med {col('release_hz', np.median)!s:6} min {col('release_hz', min)!s:6} | slip med {col('slip_cm', np.median)!s:5} max {col('slip_cm', max)!s:5}"
              f" | catch min {col('min_catch_cm', min)!s:6} | len rel med {col('contact_len_release_cm', np.median)!s:5} | E0 med {col('E0_release', np.median)!s:5} max {col('E0_release', max)!s:5}"
              f" | no-contact users {sum(v['release_hz'] is None for v in vals)}")
