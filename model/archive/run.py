"""Run all analyses, save results.json and figures."""
import json, sys, time
import numpy as np
from model import (Subject, STSConfig, SitUpConfig, sts_effort, situp_effort,
                   sts_geometry, sts_collides, rail_efforts, bar_points)
BAR1 = 0.20  # phase-1 map: short bar (m) along the bed axis, re-grip allowed

sub, sc, uc = Subject(), STSConfig(), SitUpConfig()
out = {}

# ---- sanity: geometry + no-handle baselines ---------------------------------
g = sts_geometry(sub, sc)
out["geometry"] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in g.items()}
out["sts_no_handle"] = sts_effort(sub, sc, None, return_detail=True)
out["situp_no_handle"] = situp_effort(sub, uc, None)
print("STS no handle:", out["sts_no_handle"])
print("Sit-up no handle:", out["situp_no_handle"])

# ---- Phase 2 map: two hands, handle in front (midline) ----------------------
xs2 = np.round(np.arange(-0.40, 0.81, 0.025), 3)
zs2 = np.round(np.arange(0.40, 1.31, 0.025), 3)
E2 = np.full((len(zs2), len(xs2)), np.nan)
t0 = time.time()
for i, z in enumerate(zs2):
    for j, x in enumerate(xs2):
        P = np.array([x, z])
        if sts_collides(sub, sc, P):
            continue
        e = sts_effort(sub, sc, P, n_arms=2, lateral=0.0)
        if e is not None:
            E2[i, j] = e
print(f"phase-2 map {time.time()-t0:.1f}s")
i, j = np.unravel_index(np.nanargmin(E2), E2.shape)
P2opt = np.array([xs2[j], zs2[i]])
out["sts_opt"] = dict(P=P2opt.tolist(),
                      x_from_bed_edge=float(P2opt[0] - g["edge_x"]),
                      **sts_effort(sub, sc, P2opt, 2, 0.0, return_detail=True))
print("phase-2 optimum", out["sts_opt"])

# ---- Phase 1 map: one hand, rail at bed edge (lateral 0.15 m) ---------------
xs1 = np.round(np.arange(-0.80, 0.41, 0.025), 3)
zs1 = np.round(np.arange(-0.05, 0.71, 0.025), 3)
E1 = np.full((len(zs1), len(xs1)), np.nan)
t0 = time.time()
for i, z in enumerate(zs1):
    for j, x in enumerate(xs1):
        e = situp_effort(sub, uc, bar_points((x, z), BAR1, 3), n_arms=1, lateral=0.15)
        if e is not None:
            E1[i, j] = e
print(f"phase-1 map {time.time()-t0:.1f}s")
i, j = np.unravel_index(np.nanargmin(E1), E1.shape)
P1opt = np.array([xs1[j], zs1[i]])
out["situp_opt"] = dict(P=P1opt.tolist(),
                        height_above_floor=float(P1opt[1] + sc.bed_h + uc.hip_above_mattress),
                        **situp_effort(sub, uc, bar_points(P1opt, BAR1, 3), 1, 0.15, return_detail=True))
print("phase-1 optimum", out["situp_opt"])

# ---- Fixed rail sweep -------------------------------------------------------
ss = np.round(np.arange(-0.70, 0.31, 0.05), 3)
hs = np.round(np.arange(0.60, 1.11, 0.025), 3)
R1 = np.full((len(hs), len(ss)), np.nan)
R2 = np.full((len(hs), len(ss)), np.nan)
t0 = time.time()
for i, h in enumerate(hs):
    for j, s in enumerate(ss):
        e1, e2 = rail_efforts(sub, sc, uc, s, h)
        R1[i, j] = np.nan if e1 is None else e1
        R2[i, j] = np.nan if e2 is None else e2
print(f"rail sweep {time.time()-t0:.1f}s")
worst = np.fmax(R1, R2)
worst[np.isnan(R1) | np.isnan(R2)] = np.nan
i, j = np.unravel_index(np.nanargmin(worst), worst.shape)
out["best_fixed_rail"] = dict(s=float(ss[j]), h=float(hs[i]),
                              effort_phase1=float(R1[i, j]),
                              effort_phase2=float(R2[i, j]))
# best rail for each phase alone
i1, j1 = np.unravel_index(np.nanargmin(R1), R1.shape)
i2, j2 = np.unravel_index(np.nanargmin(R2), R2.shape)
out["rail_best_for_phase1_only"] = dict(s=float(ss[j1]), h=float(hs[i1]),
                                        e1=float(R1[i1, j1]), e2=float(R2[i1, j1]))
out["rail_best_for_phase2_only"] = dict(s=float(ss[j2]), h=float(hs[i2]),
                                        e1=float(R1[i2, j2]), e2=float(R2[i2, j2]))
# phase-matched handle: phase 1 = best edge rail position for phase 1,
# phase 2 = best two-hand front position; also report 1-hand front for fairness
out["matched"] = dict(effort_phase1=float(R1[i1, j1]),
                      effort_phase2_two_hands=float(out["sts_opt"]["effort"]))
# one-hand front optimum
best1h = None
for x in np.arange(-0.1, 0.81, 0.025):
    for z in np.arange(0.5, 1.21, 0.025):
        P = np.array([x, z])
        e = sts_effort(sub, sc, P, n_arms=1, lateral=0.20)
        if e is not None and (best1h is None or e < best1h[0]):
            best1h = (e, P.tolist())
out["matched"]["effort_phase2_one_hand_front"] = float(best1h[0])
out["matched"]["one_hand_front_P"] = best1h[1]
print(json.dumps({k: out[k] for k in ["best_fixed_rail", "rail_best_for_phase1_only",
                                      "rail_best_for_phase2_only", "matched"]}, indent=1))

np.savez("maps.npz", xs2=xs2, zs2=zs2, E2=E2, xs1=xs1, zs1=zs1, E1=E1,
         ss=ss, hs=hs, R1=R1, R2=R2)
with open("results.json", "w") as f:
    json.dump(out, f, indent=1, default=float)
