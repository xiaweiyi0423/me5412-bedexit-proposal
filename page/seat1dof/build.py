"""Build the one-DOF seat page: inject model/calc_v13/seat_1dof/design.json into template.html -> ../seat_1dof.html"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/page.json")))

# step 3 note: medians for the 1.60 m / average-build users (all habits and foot positions)
a = D["assist"]; pts = a["points"]
def med(f, i):
    xs = [r["effort"][i] for r in a["rows"] if r["f"] == f and "H1.60 r0.09" in r["user"] and r["effort"][i] is not None]
    return float(np.median(xs))
def free(f):
    return float(np.median([r["free"] for r in a["rows"] if r["f"] == f and "H1.60 r0.09" in r["user"] and r["free"]]))
best = {f: min(range(len(pts)), key=lambda i: med(f, i)) for f in (0.1, 0.3, 0.5, 0.65)}
f = 0.3
D["assistNote"] = (
    f"<b>结论：助力点放在臀部和大腿交界处（坐骨正下方到大腿近端 4 cm）。</b>"
    f"起身 30% 时，推在这里费力 {med(f, 2):.3f}；推在臀部后下方 {med(f, 0):.3f}，推在大腿 10 cm 处 {med(f, 3):.3f}；"
    f"不推（坐板不帮忙）是 {free(f):.3f}。四个阶段里，最好的位置都是 “{pts[best[0.3]]}” 或相邻一点。但“4 cm 处最好”部分来自模型里 4 cm 的硬分界（那一点仍算推在骨盆上、力臂又最大），可靠的结论只是“越靠近坐骨越好，进入大腿中段后变差”。"
    f"<br>这条结论依赖一个模型假设：离臀腿交界 4 cm 以内的力算作作用在骨盆上（髋、膝都省力），更远的算作作用在大腿上（只帮膝）。"
    f"这条分界是按解剖位置估的，不是测出来的。设计曲线让坐板保持坐着时与大腿的相对位置，所以接触点大多停在交界处约 5 cm，正好在这条分界附近。")

# 5.3: one-side four-bar kill test and the same-footing bed comparison
C = os.path.join(ROOT, "model/calc_v13/seat_1dof")
FBO = json.load(open(os.path.join(C, "fourbar_oneside.json"))); BB = json.load(open(os.path.join(C, "bed_baseline.json")))
SLU = json.load(open(os.path.join(C, "slider.json")))["users"]
K72 = [k for k, v in BB["users"].items() if v["0.58"]["handle"] is not None and SLU[k].get("E_release")]
md = lambda xs: round(float(np.median(xs)), 3)
sv = lambda bed, k: md([1 - SLU[u]["E_release"] / BB["users"][u][bed][k] for u in K72])
fails = [k for k, q in FBO["users"].items() if not q or q["fwd_slip_cm"] > 2 or q["catch_min_cm"] < 0]
D["v53"] = dict(fb=dict(mech=FBO["mech"], act={k: FBO["act"][k] for k in ("stroke", "F_hold100_N", "F_lift100_N", "F_lift60_N")}, box=FBO["box"],
                        cant=FBO["cantilever"], summary=FBO["summary"], fails=[[k, FBO["users"][k]["fwd_slip_cm"]] for k in fails]),
                # rail housing variants: seat_1dof_v5_checks.housing() with RAIL_GAP / CARR_SPAN changed in memory (2026-10-27)
                box_variants=[["现方案：双导轨相距 150 mm，滑块相距 150 mm", 2749, 0.80], ["单导轨", 2554, 0.82], ["双导轨，滑块相距 100 mm", 2589, 0.76]],
                bed=dict(n=len(K72), noff=81 - len(K72), low=md([BB["users"][k]["0.42"]["L_bar"] for k in K72]), high_L=md([BB["users"][k]["0.58"]["L_bar"] for k in K72]),
                         high_best=md([BB["users"][k]["0.58"]["handle"] for k in K72]), seat=md([SLU[k]["E_release"] for k in K72]),
                         save_low=sv("0.42", "L_bar"), save_hl=sv("0.58", "L_bar"), save_hb=sv("0.58", "handle"), worse=BB["summary"]["bed0.58_handle"]["n_worse"],
                         phi_rel=md([v["phi_release"] for v in SLU.values()])),
                release=(lambda z: dict(med=round(float(np.median(z)), 3), p90=round(float(np.percentile(z, 90)), 3), max=round(float(max(z)), 3)))(
                    [v["seat_z"] for v in json.load(open(os.path.join(C, "release_z.json"))).values()]))

tpl = open(os.path.join(HERE, "template.html")).read()
out = tpl.replace("/*__DATA__*/{}", json.dumps(D, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(ROOT, "page/seat_1dof.html"), "w").write(out)
print(len(out), "bytes")
