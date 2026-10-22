"""Fair A / B / mattress comparison (v10).

Changes vs compare_AB / seat_height_v2 (after audit 3):
 * weak arms represented two ways: (P1) hand-force cap anchored to measured
   older-adult hand forces (~25 % BW, Alexander 1991 via Schultz 1992), full arm
   strength; (P2/P3) arm-joint strength x0.5 / x0.35 with a 30 % cap.
   The old 10 % cap is reported only as "old assumption".
 * every handle design gets the SAME grid of grip positions (relative to the hip
   and absolute height) and keeps its best one -> the difference between A and B
   is the seat height, not where we happened to put the handle.
 * the foot position is limited by what is under the seat:
     bed:  heel may be at most 5 cm under the bed edge  (heel >= hip + 0.10)
     B:    rear plate mechanism under the pelvis, open below the front plate
           (heel >= hip + 0.08)
   plus a sensitivity case where the feet cannot be tucked at all (shank <= 10 deg).
 * mattress: rigid (upper bound) and soft (hand cap 15 % BW on the mattress).
"""
import json, numpy as np
from model import Subject, STSConfig, sts_effort, sts_geometry, sts_collides

SHANKS = list(range(-10, 31, 5))
XS = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]   # grip ahead of hip [m]
DZS = [0.25, 0.30, 0.35, 0.40, 0.45]   # grip above seat [m]; older adults chose 0.25-0.38 (Bolli 2023)


def subj(f=1.0):
    s = Subject()
    for k in ["sh_flex", "sh_ext", "el_flex", "el_ext"]:
        setattr(s, k, getattr(Subject(), k) * f)
    return s


def feasible(sub, h, st, heel_min_ahead):
    try:
        g = sts_geometry(sub, STSConfig(bed_h=h, shank_tilt_deg=st))
    except ValueError:
        return None
    if g["heel"] - g["Hp"][0] < heel_min_ahead:
        return None
    return g


def best(sub, h, mode, cap, heel_min, shank_max=30):
    out = None
    for st in SHANKS:
        if st > shank_max:
            continue
        g = feasible(sub, h, st, heel_min)
        if g is None:
            continue
        c = STSConfig(bed_h=h, shank_tilt_deg=st, trunk_grid=tuple(range(0, 81, 5)), hand_cap=cap)
        cands = []
        if mode == "none":
            cands = [(None, 2, 0.0, None)]
        elif mode == "mattress":
            cands = [(np.array([g["Hp"][0] - 0.05, h + 0.02]), 2, 0.22, "beside hip")]
        else:
            for dx in XS:
                for z in [h + d for d in DZS]:
                    P = np.array([g["Hp"][0] + dx, z])
                    if sts_collides(sub, c, P):
                        continue
                    cands.append((P, 2, 0.0, (dx, round(z - h, 2))))
        for P, n, lat, tag in cands:
            d = sts_effort(sub, c, P, n, lat, return_detail=True)
            if d and (out is None or d["effort"] < out["effort"]):
                out = dict(effort=round(float(d["effort"]), 3), shank=st, trunk=d["trunk_deg"],
                           hand=round(float(d["hand_load_pct_BW"]), 1), grip=tag,
                           heel_ahead_of_hip=round(float(g["heel"] - g["Hp"][0]), 3))
    return out


PROXIES = {
    "P1 cap25": dict(f=1.0, cap=0.25),
    "P2 arm x0.5": dict(f=0.5, cap=0.30),
    "P3 arm x0.35": dict(f=0.35, cap=0.30),
    "strong cap30": dict(f=1.0, cap=0.30),
    "old cap10": dict(f=1.0, cap=0.10),
}
BED_HEEL, B_HEEL = 0.10, 0.08

res = {"none": {}, "proxies": {}, "feet_blocked": {}}
s0 = subj()
for h in [0.42, 0.50, 0.55, 0.60]:
    res["none"][str(h)] = best(s0, h, "none", 0.3, B_HEEL if h > 0.42 else BED_HEEL)
for name, p in PROXIES.items():
    s = subj(p["f"])
    r = {
        "mattress_rigid": best(s, 0.42, "mattress", p["cap"], BED_HEEL),
        "mattress_soft": best(s, 0.42, "mattress", min(p["cap"], 0.15), BED_HEEL),
        "A_handle_042": best(s, 0.42, "handle", p["cap"], BED_HEEL),
        "B_bar_060": best(s, 0.60, "handle", p["cap"], B_HEEL),
    }
    res["proxies"][name] = r
    print(name, {k: (v["effort"], v["shank"], v["grip"], v["hand"]) for k, v in r.items()})
for name in ["P1 cap25", "P2 arm x0.5"]:
    p = PROXIES[name]; s = subj(p["f"])
    res["feet_blocked"][name] = {
        "none_042": best(s, 0.42, "none", 0.3, -1, 10),
        "none_060": best(s, 0.60, "none", 0.3, -1, 10),
        "mattress_rigid": best(s, 0.42, "mattress", p["cap"], -1, 10),
        "A_handle_042": best(s, 0.42, "handle", p["cap"], -1, 10),
        "B_bar_060": best(s, 0.60, "handle", p["cap"], -1, 10),
    }
    print("feet<=10", name, {k: (v["effort"] if v else None) for k, v in res["feet_blocked"][name].items()})
print("none", {k: (v["effort"], v["shank"]) for k, v in res["none"].items()})
json.dump(res, open("compare_v10.json", "w"), indent=1)
