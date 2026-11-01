"""Rebuild data.js (window.DATA) for pulse.js: the reference user's rise, the mechanism travel table and the CAD meshes.

The original packer (prep.py of the 3D-scene tools) was never committed; this rebuilds the fields pulse.js reads:
  pose {L, foot, frames[{Hp, K, A, tr, sink, seat{Q, phi}}]}  <- model/calc_v13/seat_1dof/page.json, anim[REF] (seat, sink from cush.z1)
  mech {Q0}                                                   <- page.json mech.frames[0].Q (seat flush with the mattress)
  bar  {x, z}                                                 <- page.json consts.handrail
  kin  [[stroke, Qx, Qz, tilt, pin1x, pin1z, pin2x, pin2z, link], ...] (mm, deg) <- cad/travel_table.csv
  mesh                                                        <- cad/out/mesh.json
Usage: python3 prep_data.py   (writes data.js next to this file)
"""
import csv, json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))
REF = "H1.60 r0.09 p1.0 xa0.29"
P = json.load(open(f"{ROOT}/model/calc_v13/seat_1dof/page.json"))
A = P["anim"][REF]
r4 = lambda v: [round(float(x), 4) for x in v]
frames = []
for f in A["frames"]:
    o = dict(Hp=r4(f["Hp"]), K=r4(f["K"]), A=r4(f["A"]), tr=round(float(f["tr"]), 2))
    cu = (f.get("cush") or {}).get("z1")
    o["sink"] = round(cu["sink_mm"] / 1000, 4) if cu and not cu.get("lost") else 0.0
    # seat = the loaded seat pose under the zoned cushion (cush.z1), as in make_seat_gif.py: it starts ~3 cm above the flush pose Q0
    # and is left at 12.9 deg forward tilt when the person leaves it (the film's "前倾 13°" readout)
    if f.get("seat") and cu and not cu.get("lost"): o["seat"] = dict(Q=r4(cu["Q"]), phi=round(float(cu["phi"]), 2))
    frames.append(o)
rows = list(csv.reader(open(f"{ROOT}/cad/travel_table.csv")))
kin = [[float(x) for x in r] for r in rows[1:] if r]
D = dict(pose=dict(L=A["L"], foot=A["foot"], frames=frames), mech=dict(Q0=r4(P["mech"]["frames"][0]["Q"])),
         bar=P["consts"]["handrail"], kin=kin, mesh=json.load(open(f"{ROOT}/cad/out/mesh.json")))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js"), "w").write("window.DATA=" + json.dumps(D, separators=(",", ":")) + ";")
print(len(frames), "pose frames,", sum(1 for f in frames if "seat" in f), "with seat; sink0", frames[0]["sink"], "; kin rows", len(kin), "; parts", len(D["mesh"]["parts"]))
