"""Pack the mechanism-design data (81 ideal paths, design curve, hinge traces, five candidates) into design.js."""
import json, os, sys
import numpy as np
ROOT = "/home/user/me5412-bedexit-proposal"; CALC = f"{ROOT}/model/calc_v13"; sys.path.insert(0, CALC); sys.path.insert(0, f"{ROOT}/presentation/tools")
import seat_1dof_layout as LY
from mech_design_figs import fourbar_frames
J = lambda f: json.load(open(os.path.join(CALC, "seat_1dof", f)))
P = J("page.json"); V5 = J("v5.json"); OS = J("fourbar_oneside.json"); M = P["mech"]
r = lambda a: np.round(np.asarray(a, float), 4).tolist()
def local(c1, c2):   # plate + bracket polygons in seat-local coordinates
    pl, br = LY.seat_polys(np.zeros(2), 0.0, np.array(c1), np.array(c2)); return dict(plate=r(pl), br=r(br))
def fr(frames): return [dict(Q=r(f["Q"]), phi=round(f["phi"], 2), P1=r(f["P1"]), P2=r(f["P2"])) for f in frames]
mid, sides, osd = V5["layouts"]["mid"]["mech"], V5["layouts"]["sides"]["mech"], OS["mech"]
D = dict(Z0=P["consts"]["Z0"],
         env=[r(e["Q"]) for e in P["envelope"].values()],
         design=dict(Q=r(P["design_curve"]["poses"]["Q"]), phi=r(P["design_curve"]["poses"]["phi"])),
         mech=dict(c1=M["c1"], c2=M["c2"], B=M["B"], link=M["link"], rail_lo=M["rail_lo"], rail_hi=M["rail_hi"], frames=fr(M["frames"]), **local(M["c1"], M["c2"])),
         cands=[dict(key=k, A=m["A"], B=m["B"], c1=m["c1"], c2=m["c2"], frames=fr(f), **local(m["c1"], m["c2"]))
                for k, m, f in (("mid", mid, mid["frames"]), ("sides", sides, sides["frames"]), ("oneside", osd, fourbar_frames(osd, 0.69)))])
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "design.js"), "w").write("window.DS=" + json.dumps(D) + ";")
print(len(D["env"]), "paths;", [len(c["frames"]) for c in D["cands"]], "cand frames;", len(D["mech"]["frames"]), "mech frames")

# ---- how a line is drawn: a few users' rise postures paired with their thigh-carried seat poses (export as design_demo.js)
import seat_1dof_design as SD
DEMO = [(1.60, 0.09, 1.0, 0.29), (1.50, 0.07, 0.6, 0.25), (1.75, 0.11, 2.5, 0.33), (1.50, 0.11, 2.5, 0.29), (1.75, 0.07, 0.6, 0.33)]
demo = []
for u in DEMO:
    sub, p = SD.path_of(u); q, Q, phi = SD.curve_fit(p, 30.0); n = len(Q) - 15
    idx = np.linspace(0, len(p) - 1, 48).round().astype(int)
    demo.append(dict(key=SD.ukey(u), H=u[0], fr=[dict(Hp=r(p[i]["Hp"]), K=r(p[i]["K"]), A=r(p[i]["A"]), f=round(float(p[i]["f"]), 3),
                     Q=r(Q[15 + min(i, n - 1)]), phi=round(float(phi[15 + min(i, n - 1)]), 2), on=bool(i < n)) for i in idx]))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "design_demo.js"), "w").write(
    "window.DEMO=" + json.dumps(dict(users=demo, chosen=P["design_curve"]["chosen"], keys=list(P["envelope"].keys()))) + ";")
print("demo users", [d["key"] for d in demo], "chosen", P["design_curve"]["chosen"])
