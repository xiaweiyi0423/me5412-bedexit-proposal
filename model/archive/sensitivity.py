"""Does the conclusion survive changes to the assumptions?
Key quantities per scenario:
  none      : phase-2 effort without any handle
  side_best : best phase-2 effort with a fixed edge rail beside the hip (any height)
  front2    : best phase-2 effort with a two-hand handle in front
  p1_best   : best phase-1 (lie->sit) effort with an edge rail, and its height
  side_at_p1: phase-2 effort of the edge rail at the phase-1-best height
"""
import json, copy
import numpy as np
from model import (Subject, STSConfig, SitUpConfig, sts_effort, situp_effort,
                   sts_geometry, sts_collides, bar_points)


def key_numbers(sub, sc, uc):
    g = sts_geometry(sub, sc)
    none = sts_effort(sub, sc, None)
    side = {}
    for h in np.arange(0.60, 1.201, 0.025):
        e = sts_effort(sub, sc, np.array([g["edge_x"] + 0.03, h]), 1, 0.22)
        if e is not None:
            side[round(float(h), 3)] = e
    front = None
    for x in np.arange(0.0, 0.71, 0.05):
        for z in np.arange(0.6, 1.31, 0.05):
            P = np.array([x, z])
            if sts_collides(sub, sc, P):
                continue
            e = sts_effort(sub, sc, P, 2, 0.0)
            if e is not None and (front is None or e < front[0]):
                front = (e, [round(x, 3), round(z, 3)])
    p1 = None
    for s in np.arange(-0.45, 0.11, 0.05):
        for h in np.arange(0.70, 1.251, 0.05):
            z1 = h - sc.bed_h - uc.hip_above_mattress
            e = situp_effort(sub, uc, bar_points((s, z1), 0.40, 5), 1, 0.15)
            if e is not None and (p1 is None or e < p1[0]):
                p1 = (e, round(float(s), 3), round(float(h), 3))
    side_best_h = min(side, key=side.get)
    # nearest evaluated side height to the phase-1 best height
    side_at_p1 = None
    if p1 is not None:
        hh = min(side, key=lambda k: abs(k - p1[2]))
        side_at_p1 = side[hh]
    return dict(none=none, side_best=side[side_best_h], side_best_h=side_best_h,
                front2=front[0], front2_P=front[1],
                p1_best=None if p1 is None else p1[0],
                p1_best_h=None if p1 is None else p1[2],
                side_at_p1=side_at_p1)


scen = {}
base = (Subject(), STSConfig(), SitUpConfig())
scen["baseline"] = base


def variant(name, sub_kw=None, sc_kw=None, uc_kw=None):
    s, a, b = copy.deepcopy(base)
    for k, v in (sub_kw or {}).items(): setattr(s, k, v)
    for k, v in (sc_kw or {}).items(): setattr(a, k, v)
    for k, v in (uc_kw or {}).items(): setattr(b, k, v)
    scen[name] = (s, a, b)


variant("hand_cap_20pct", sc_kw=dict(hand_cap=0.20), uc_kw=dict(hand_cap=0.20))
variant("hand_cap_40pct", sc_kw=dict(hand_cap=0.40), uc_kw=dict(hand_cap=0.40))
b = base[0]
variant("weak_legs_x0.6", sub_kw=dict(knee_ext=b.knee_ext * 0.6, hip_ext=b.hip_ext * 0.6,
                                      hip_flex=b.hip_flex * 0.6))
variant("weak_arms_x0.7", sub_kw=dict(sh_flex=b.sh_flex * 0.7, sh_ext=b.sh_ext * 0.7,
                                      el_flex=b.el_flex * 0.7, el_ext=b.el_ext * 0.7))
variant("low_bed_0.42", sc_kw=dict(bed_h=0.42))
variant("high_bed_0.55", sc_kw=dict(bed_h=0.55))
variant("larger_person_75kg_1.70m", sub_kw=dict(M=75.0, H=1.70,
        **{k: getattr(b, k) * 75 / 60 for k in
           ["knee_ext", "knee_flex", "hip_ext", "hip_flex", "sh_flex", "sh_ext", "el_flex", "el_ext"]}))

res = {}
for name, (s, a, u) in scen.items():
    res[name] = key_numbers(s, a, u)
    r = res[name]
    f = lambda v: "infeasible" if v is None else f"{v:.3f}"
    print(f"{name:28s} none={f(r['none'])} side_best={f(r['side_best'])}@{r['side_best_h']} "
          f"front2={f(r['front2'])}@{r['front2_P']} p1={f(r['p1_best'])}@{r['p1_best_h']} "
          f"side@p1h={f(r['side_at_p1'])}", flush=True)
json.dump(res, open("sensitivity.json", "w"), indent=1, default=float)
