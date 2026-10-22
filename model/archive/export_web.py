"""Export per-cell detail for the interactive explorer (web page)."""
import json, numpy as np
from model import Subject, STSConfig, sts_effort, sts_geometry, sts_collides
sub, sc = Subject(), STSConfig()
g = sts_geometry(sub, sc)
r3 = lambda v: round(float(v), 3)
def pack(d):
    if d is None: return None
    ju = d["joint_use"]
    return [r3(d["effort"]), int(d["trunk_deg"]), r3(d["elbow"][0]), r3(d["elbow"][1]),
            round(float(d["Fx"])), round(float(d["Fz"])),
            r3(ju["hip"]), r3(ju["knee"]), r3(ju["shoulder"]), r3(ju["elbow"])]
xs = np.round(np.arange(-0.40, 0.801, 0.025), 3); zs = np.round(np.arange(0.40, 1.301, 0.025), 3)
front = []
for z in zs:
    row = []
    for x in xs:
        P = np.array([x, z])
        row.append(None if sts_collides(sub, sc, P) else pack(sts_effort(sub, sc, P, 2, 0.0, True)))
    front.append(row)
hs = np.round(np.arange(0.55, 1.201, 0.025), 3)
side = [pack(sts_effort(sub, sc, np.array([g["edge_x"] + 0.03, h]), 1, 0.22, True)) for h in hs]
none = sts_effort(sub, sc, None, return_detail=True)
out = dict(
    xs=xs.tolist(), zs=zs.tolist(), front=front, side_h=hs.tolist(), side=side,
    none=dict(effort=r3(none["effort"]), trunk=none["trunk_deg"], ju=[r3(none["joint_use"][k]) for k in ["hip","knee"]]),
    geom=dict(A=[r3(v) for v in g["A"]], K=[r3(v) for v in g["K"]], H=[r3(v) for v in g["Hp"]],
              edge=r3(g["edge_x"]), heel=r3(g["heel"]), toe=r3(g["toe"]), bed=sc.bed_h,
              Ltr=r3(sub.L_trunk), Lua=r3(sub.L_uarm), Lfa=r3(sub.L_farm)),
    BW=round(sub.M * 9.81))
s = json.dumps(out, separators=(",", ":"))
open("web_data.json", "w").write(s); print(len(s), "bytes")
