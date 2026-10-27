"""v5.2 handrail: an L-shaped rail fixed on the base (post on the head side + a horizontal bar in front of the user).

Why: the v5 vertical pole at x 0.69 m (head side) was out of reach while seated, could only be pulled with one hand from the
side, had no place for the hold-to-run switch, and the effort was computed as if the grip height could change during the rise
(round-2 audit A3, C1, E1).
Geometry: the bar runs across the user's front (y from the head-side post at +0.30 to about -0.05; the foot side stays open),
at height z_b and distance x_b from the bed edge. In the sagittal model the bar is one point (x_b, z_b): both hands hold it in
front of the body, which is what the 2-D two-arm effort model assumes, and the grip does not move during the rise.
Body clearance: the trunk (hip -> shoulder, 10 cm radius) and the head (8.5 cm radius, centre 12 cm past the shoulder) must
stay >= 5 cm off the bar; the effort solver may only use trunk angles that keep this clearance.
Reach: seated, sitting up (trunk 0..30 deg forward), every user must reach the bar (arm IK, shoulder range).
Search: x_b 0.40..0.70, z_b 0.80..1.05 (5 cm grid). Per user on the slider curve: release effort, release effort with a stooped
trunk (>= 30 deg), and the largest effort while the seat supports (rigid contact, every 4th frame).
Output: seat_1dof/handrail.json (grid + chosen bar); the bar is then used by seat_1dof_v5.pole_effort.
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot, Seat, effort, pose
from model import arm_ik_all, shoulder_ok, G

OUT = os.path.join(HERE, "seat_1dof"); PATH = os.path.join(OUT, "handrail.json")
R_TRUNK, R_HEAD, HEAD_OFF, CLEAR = 0.10, 0.085, 0.12, 0.05
ALL_TRUNKS = tuple(range(0, 81, 5))
DEFAULT_BAR = dict(x=0.55, z=0.90)

def bar_now():
    try: return json.load(open(PATH))["bar"]
    except (FileNotFoundError, KeyError): return DEFAULT_BAR

def _seg_d(P, A, B):
    d = B - A; t = np.clip((P - A) @ d / (d @ d), 0, 1); return float(np.hypot(*(P - (A + t * d))))

def trunk_clear(sub, Hp, th, bar):
    """clearance (m) between the bar point and the trunk / head for trunk angle th (deg from vertical, + forward)."""
    ut = np.array([np.sin(np.radians(th)), np.cos(np.radians(th))]); S = Hp + sub.L_trunk * ut; Hc = S + HEAD_OFF * ut
    return min(_seg_d(bar, Hp, S) - R_TRUNK, float(np.hypot(*(bar - Hc))) - R_HEAD)

def ok_trunks(sub, pz, bar, base=ALL_TRUNKS):
    return tuple(t for t in base if trunk_clear(sub, pz["Hp"], t, bar) >= CLEAR)

def bar_effort(sub, pz, contact=None, cap=0.5, bar=None, stooped=False):
    """effort with both hands on the fixed bar; trunk angles that would hit the bar are excluded."""
    b = np.array([(bar or bar_now())["x"], (bar or bar_now())["z"]])
    tr = ok_trunks(sub, pz, b, tuple(t for t in ALL_TRUNKS if t >= 30) if stooped else ALL_TRUNKS)
    if not tr: return None
    old = ST.TRUNKS; ST.TRUNKS = tr
    try:
        r = effort(sub, pz, b, contact, cap=cap) if contact is not None else effort(sub, pz, b)
    finally:
        ST.TRUNKS = old
    return None if r is None else r[0]

def reach_seated(sub, pz, bar, max_trunk=30):
    b = np.array([bar["x"], bar["z"]])
    for th in range(0, max_trunk + 1, 5):
        if trunk_clear(sub, pz["Hp"], th, b) < CLEAR: continue
        ut = np.array([np.sin(np.radians(th)), np.cos(np.radians(th))]); S = pz["Hp"] + sub.L_trunk * ut
        if any(shoulder_ok(S, E, ut) for E in arm_ik_all(S, b, sub.L_uarm, sub.L_farm)): return True
    return False

def user_eval(args):
    """one user on the seat curve cv, one bar: seated reach, release effort (normal / stooped), supported max."""
    from seat_relative_motion import track, solve_s
    from seat_1dof_design import ukey, path_of, PAD_AMAX
    u, cv, bar = args; ST.A_MAX = PAD_AMAX; sub, path = path_of(u)
    rows = track(sub, path, Seat(r_e=0.03), cv); good = [r for r in rows if r.get("contact") and r.get("ok")]
    out = dict(reach=reach_seated(sub, path[0], bar))
    if not good: return ukey(u), dict(out, E_release=None)
    last = good[-1]; sh = solve_s(sub, u[3], last["hz"], last["hip_x"]) or 0.0; pz = pose(sub, u[3], last["hz"], sh)
    out["E_release"] = bar_effort(sub, pz, bar=bar); out["E_release_stooped"] = bar_effort(sub, pz, bar=bar, stooped=True)
    E_sup = 0.0; nfail = 0
    for r, p_ in list(zip(rows, path))[:len(good)][::4]:
        k = min(int(r["k"]), len(cv[1]) - 1); n_ = rot(cv[2][k]) @ np.array([0, 1.0])
        e = bar_effort(sub, p_, (np.array(r["P"]), n_, r["pelvis"]), bar=bar)
        if e is None: nfail += 1
        else: E_sup = max(E_sup, e)
    out.update(E_supported_max=round(E_sup, 3), sup_infeasible=nfail)
    return ukey(u), out

def slider_cv():
    import seat_1dof_slider as SL
    from seat_1dof_fourbar import with_prefix
    sim, _ = SL.simulate(json.load(open(os.path.join(OUT, "slider.json")))["x"], 700)
    return with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim]))

def summarize(R):
    v = [q for q in R.values()]; E = [q["E_release"] for q in v if q.get("E_release") is not None]
    S = [q["E_supported_max"] for q in v if q.get("E_supported_max") is not None]
    return dict(n_reach=sum(q["reach"] for q in v), n_release_ok=len(E), E_rel_med=round(float(np.median(E)), 3) if E else None,
                E_rel_max=round(float(max(E)), 3) if E else None, E_sup_max=round(float(max(S)), 3) if S else None,
                sup_infeasible=sum(q.get("sup_infeasible", 0) for q in v))

if __name__ == "__main__":
    from seat_1dof_design import USERS
    t0 = time.time(); cv = slider_cv(); grid = {}
    cands = [dict(x=round(x, 2), z=round(z, 2)) for x in np.arange(0.40, 0.701, 0.05) for z in np.arange(0.80, 1.051, 0.05)]
    with Pool() as pool:
        for b in cands:
            R = dict(pool.map(user_eval, [(u, cv, b) for u in USERS])); s = summarize(R)
            grid[f'{b["x"]:.2f},{b["z"]:.2f}'] = dict(bar=b, summary=s, users=R)
            print(b, s, round(time.time() - t0), "s", flush=True)
    ok = [k for k, g in grid.items() if g["summary"]["n_reach"] == len(USERS) and g["summary"]["n_release_ok"] == len(USERS)]
    best = min(ok, key=lambda k: (grid[k]["summary"]["E_rel_med"], grid[k]["summary"]["E_sup_max"])) if ok else None
    json.dump(dict(note=__doc__, bar=grid[best]["bar"] if best else DEFAULT_BAR, chosen=best, feasible=ok,
                   grid={k: dict(bar=g["bar"], summary=g["summary"]) for k, g in grid.items()}, users=grid[best]["users"] if best else None),
              open(PATH, "w"), ensure_ascii=False, separators=(",", ":"))
    print("chosen", best, grid[best]["summary"] if best else None, "done", round(time.time() - t0), "s")
