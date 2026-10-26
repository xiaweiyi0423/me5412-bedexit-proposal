"""Build the one-DOF seat page: inject model/calc_v13/seat_1dof/design.json into template.html -> ../seat_1dof.html"""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", "..")
D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/design.json")))

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
    f"不推（坐板不帮忙）是 {free(f):.3f}。四个阶段里，最好的位置都是 “{pts[best[0.3]]}” 或相邻一点。"
    f"<br>这条结论依赖一个模型假设：离臀腿交界 4 cm 以内的力算作作用在骨盆上（髋、膝都省力），更远的算作作用在大腿上（只帮膝）。"
    f"这条分界是按解剖位置估的，不是测出来的。设计曲线让坐板保持坐着时与大腿的相对位置，所以接触点大多停在交界处约 5 cm，正好在这条分界附近。")

tpl = open(os.path.join(HERE, "template.html")).read()
out = tpl.replace("/*__DATA__*/{}", json.dumps(D, ensure_ascii=False, separators=(",", ":")))
open(os.path.join(ROOT, "page/seat_1dof.html"), "w").write(out)
print(len(out), "bytes")
