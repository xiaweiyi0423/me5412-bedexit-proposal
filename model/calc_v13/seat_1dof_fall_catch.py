"""v5.4: does the seat protect against falling back better than a bed? Same catch definition for every option.

Question (user, 2026-10-27): besides effort, is fall protection the real advantage? The cushion is under the buttocks;
a handrail cannot be sat on.
Definition (as seat_relative_motion.track): if the user sits back at some instant of the rise, the buttock lands about
4 cm behind the hip joint. catch = front edge of the support - (hip x - 0.04): >= 0 lands on the support, < 0 lands on
or past its edge (a fall). drop = how far the hip falls before the buttock reaches the support's top.
Options, all 81 users, the whole rise from sitting to standing (hip-height fraction f = 0..1):
  seat      inclined-rail seat (slider.json curve): it follows until the user leaves it, then stays where it is
  vertical  vertical lift with the same rule (follows straight up, then stays)
  bed058    raised bed 0.58 m, user sitting with the hip right over the mattress edge (hip x = 0) or 5 cm further in
  bed042    low bed 0.42 m, same
Second fall mode (backward_*): the user tips backward stiffly about the ankle (hip moves back as it drops).
Third fall mode (knee_*, v5.6, deck audit round 3): the knees give way with the shins held where they are, so the hip swings
back and down about the knee. Straight down needs the shins to tip forward as the knees bend; real falls are between the three.
v5.6: the rise paths now reach standing (seat_relative_motion.solve_s fix); before, every path stopped at about two thirds of
the rise, so the seat was only checked up to there.
Output: seat_1dof/fall_catch.json
"""
import json, os
import numpy as np
from multiprocessing import Pool
import seat_trajectory as ST
from seat_trajectory import Seat
from seat_relative_motion import track, rise, curve_vertical
import seat_1dof_handrail as HR
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
from seat_1dof_fourbar import with_prefix
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "seat_1dof", "fall_catch.json")
BEHIND = 0.04; CV = HR.slider_cv(); CVV = curve_vertical(top=0.69)

def seat_like(u, cv):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rb = u[1]
    rows = track(sub, path, Seat(r_e=0.03), cv); good = [r for r in rows if r.get("contact") and r.get("ok")]
    out = []
    for i, pz in enumerate(path):
        r = good[i] if i < len(good) else good[-1]                      # after release the seat stays at the last support
        catch = r["front_x"] - (pz["Hp"][0] - BEHIND); drop = max(0.0, pz["Hp"][1] - rb - r["seat_top"]) if i >= len(good) else 0.0
        out.append((float(pz["f"]), float(catch), float(drop)))
    return out

def bed_path(H, xa, p, hip0, hz0):
    """like seat_relative_motion.rise, but where the planned hip x cannot be reached (feet would not hold it), the hip is
    put at the nearest reachable x instead of skipping that instant, so the path covers the whole rise."""
    from model import Subject
    from seat_trajectory import pose
    sub = Subject(H=H); hz1 = sub.ankle_h + sub.L_shank + sub.L_thigh - 0.012; out = []
    for hz in np.arange(hz0, hz1 + 1e-9, 0.004):
        f = (hz - hz0) / (hz1 - hz0); hx = hip0 + (xa - hip0) * f ** p
        P = [q for q in (pose(sub, xa, hz, s) for s in np.arange(-15.0, 45.01, 0.25)) if q is not None]
        if not P: continue
        q = min(P, key=lambda q: abs(q["Hp"][0] - hx)); q["f"] = f; out.append(q)
    return out

def bed_like(u, bed, hip0):
    H, rb, p, xa = u; path = bed_path(H, xa, p, hip0, bed + rb)
    if len(path) < 5 or abs(path[0]["Hp"][0] - hip0) > 0.01: return None    # cannot sit there with the feet on the floor
    return [(float(pz["f"]), float(0.0 - (pz["Hp"][0] - BEHIND)), float(max(0.0, pz["Hp"][1] - rb - bed))) for pz in path]

def backward(u, kind):
    """second fall mode: the user tips backward stiffly about the ankle until the hip reaches the support height.
    caught = the buttock lands on the seat (between its rear and front edge) or on the bed (x < 0)."""
    H, rb, p, xa = u
    if kind == "seat":
        ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rows = track(sub, path, Seat(r_e=0.03), CV); good = [r for r in rows if r.get("contact") and r.get("ok")]
    else:
        bed = 0.58 if kind == "bed058" else 0.42; path = bed_path(H, xa, p, 0.0, bed + rb)
        if len(path) < 5 or abs(path[0]["Hp"][0]) > 0.01: return None
    out = []
    for i, pz in enumerate(path):
        A = pz["A"]; Hp = pz["Hp"]; R = float(np.hypot(*(Hp - A)))
        if kind == "seat":
            r = good[i] if i < len(good) else good[-1]; zt = r["seat_top"] + rb; rear = r["front_x"] - 0.17
        else: zt = bed + rb; rear = -9.0
        dz = zt - A[1]
        if dz >= R or Hp[1] <= zt + 1e-6: out.append(1.0); continue
        x_land = A[0] - np.sqrt(R * R - dz * dz); xb = x_land - BEHIND
        if kind != "seat": out.append(1.0 if xb <= 0.0 else 0.0); continue
        if rear <= xb <= r["front_x"]: out.append(1.0); continue          # on the seat
        dz2 = 0.42 + rb - A[1]                                              # passed behind the seat: keeps tipping down to bed level
        xb2 = A[0] - np.sqrt(max(R * R - dz2 * dz2, 0.0)) - BEHIND
        out.append(0.5 if xb2 <= 0.0 else 0.0)                              # 0.5 = lands on the bed behind, past the seat's rear edge
    return float(np.mean([o == 1.0 for o in out])) if kind != "seat" else dict(on_seat=float(np.mean([o == 1.0 for o in out])),
                                                                                on_bed_behind=float(np.mean([o == 0.5 for o in out])),
                                                                                floor=float(np.mean([o == 0.0 for o in out])))

def knee(u, kind):
    """third mode: the hip swings back and down about the knee (shin fixed) until it reaches the support height.
    seat: 1 = buttock on the seat, 0.5 = behind its rear edge (on the padded edge or the bed: the 3-7 cm gap between seat and
    bed is narrower than the buttock), 0 = in front of the seat's front edge (a miss). bed: 1 = on the bed, 0 = in front of its edge."""
    H, rb, p, xa = u
    if kind == "seat":
        ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rows = track(sub, path, Seat(r_e=0.03), CV); good = [r for r in rows if r.get("contact") and r.get("ok")]
    else:
        from model import Subject
        sub = Subject(H=H); bed = 0.58 if kind == "bed058" else 0.42; path = bed_path(H, xa, p, 0.0, bed + rb)
        if len(path) < 5 or abs(path[0]["Hp"][0]) > 0.01: return None
    Lt = sub.L_thigh; out = []
    for i, pz in enumerate(path):
        K = pz["K"]; Hp = pz["Hp"]
        if kind == "seat":
            r = good[i] if i < len(good) else good[-1]; zt = r["seat_top"] + rb; front = r["front_x"]; rear = front - 0.17
        else: zt = bed + rb
        if Hp[1] <= zt + 1e-6: out.append(1.0); continue
        dz = zt - K[1]; xb = K[0] - np.sqrt(max(Lt * Lt - dz * dz, 0.0)) - BEHIND
        if kind != "seat": out.append(1.0 if xb <= 0.0 else 0.0); continue
        out.append(1.0 if rear <= xb <= front else (0.0 if xb > front else 0.5))
    o = np.array(out)
    return dict(on=float(np.mean(o == 1.0)), behind=float(np.mean(o == 0.5)), miss=float(np.mean(o == 0.0)), all_on=bool(np.all(o == 1.0)),
                no_miss=bool(np.all(o > 0.0)), end=float(o[-1]))

def job(u):
    return ukey(u), dict(seat=seat_like(u, CV), vertical=seat_like(u, CVV), bed058=bed_like(u, 0.58, 0.0), bed058_in=bed_like(u, 0.58, -0.05),
                         bed042=bed_like(u, 0.42, 0.0), bed042_in=bed_like(u, 0.42, -0.05))

def summ(series):
    S = [s for s in series if s]
    caught = [np.mean([c >= 0 for _, c, _ in s]) for s in S]
    first_miss = [next((f for f, c, _ in s if c < 0), None) for s in S]; fm = [x for x in first_miss if x is not None]
    worst = [min(c for _, c, _ in s) for s in S]; end = [s[-1][1] for s in S]
    drop_caught = [max([d for _, c, d in s if c >= 0] or [0.0]) for s in S]
    return dict(n=len(S), caught_share_med=round(float(np.median(caught)), 2), caught_share_min=round(float(min(caught)), 2),
                n_always_caught=sum(1 for x in first_miss if x is None), first_miss_f_med=round(float(np.median(fm)), 2) if fm else None,
                catch_worst_cm_med=round(100 * float(np.median(worst)), 1), catch_at_standing_cm_med=round(100 * float(np.median(end)), 1),
                drop_when_caught_cm_max=round(100 * float(max(drop_caught)), 1),
                first_miss_f_min=round(float(min(fm)), 2) if fm else None,
                miss_worst_cm_med=round(100 * float(np.median([w for w, x in zip(worst, first_miss) if x is not None])), 1) if fm else None,
                miss_worst_cm_min=round(100 * float(min(w for w, x in zip(worst, first_miss) if x is not None)), 1) if fm else None)

def bjob(u): return ukey(u), {k: backward(u, k) for k in ("seat", "bed058", "bed042")}
def kjob(u): return ukey(u), {k: knee(u, k) for k in ("seat", "bed058", "bed042")}

if __name__ == "__main__":
    with Pool() as p: R = dict(p.map(job, USERS)); RB = dict(p.map(bjob, USERS)); RK = dict(p.map(kjob, USERS))
    S = {k: summ([R[u][k] for u in R]) for k in ("seat", "vertical", "bed058", "bed058_in", "bed042", "bed042_in")}
    for k in ("bed058", "bed042"):
        v = [RB[u][k] for u in RB if RB[u][k] is not None]; S[k]["backward_caught_share_med"] = round(float(np.median(v)), 2); S[k]["backward_n_always"] = sum(1 for x in v if x >= 0.999)
    for q in ("on_seat", "on_bed_behind", "floor"):
        v = [RB[u]["seat"][q] for u in RB]; S["seat"][f"backward_{q}_med"] = round(float(np.median(v)), 2); S["seat"][f"backward_{q}_max"] = round(float(max(v)), 2)
    for k in ("seat", "bed058", "bed042"):
        v = [RK[u][k] for u in RK if RK[u][k] is not None]
        S[k].update(knee_on_med=round(float(np.median([x["on"] for x in v])), 2), knee_n_all_on=sum(x["all_on"] for x in v),
                    knee_n_no_miss=sum(x["no_miss"] for x in v), knee_miss_med=round(float(np.median([x["miss"] for x in v])), 2),
                    knee_end_on=sum(x["end"] == 1.0 for x in v), knee_end_behind=sum(x["end"] == 0.5 for x in v), knee_end_miss=sum(x["end"] == 0.0 for x in v))
    for k, v in S.items(): print(k, v)
    json.dump(dict(note=__doc__, summary=S, users={u: {k: (None if s is None else [[round(a, 3) for a in x] for x in s[::3]]) for k, s in d.items()} for u, d in R.items()}),
              open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
