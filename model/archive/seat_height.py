"""Seat (bed-edge) height sweep. Trunk grid widened to 80 deg and shank tilt
free in {5..30} deg to avoid the posture artefacts the audit found."""
import json, copy, numpy as np
from model import Subject, STSConfig, sts_effort, sts_geometry
sub = Subject()
def run(h, mode):
    best = None
    for st in range(5, 31, 5):
        c = STSConfig(bed_h=h, shank_tilt_deg=st, trunk_grid=tuple(range(0, 81, 5)))
        try: g = sts_geometry(sub, c)
        except ValueError: continue
        if mode == "none":
            d = sts_effort(sub, c, None, return_detail=True)
        else:  # hands on mattress beside/behind hip (realistic baseline)
            P = np.array([g["Hp"][0] - 0.05, h + 0.02])
            d = sts_effort(sub, c, P, 2, 0.22, return_detail=True)
        if d and (best is None or d["effort"] < best["effort"]):
            # joint moments per leg in N m/kg
            ju = d["joint_use"]
            d["knee_Nmkg_leg"] = abs(ju["knee"]) * sub.knee_ext / sub.M if ju["knee"] >= 0 else None
            d["hip_Nmkg_leg"] = abs(ju["hip"]) * sub.hip_ext / sub.M if ju["hip"] >= 0 else None
            d["shank"] = st; best = d
    return best
out = {}
for mode in ["none", "mattress"]:
    rows = []
    for h in np.round(np.arange(0.40, 0.661, 0.02), 3):
        d = run(h, mode)
        rows.append(None if d is None else dict(h=float(h), effort=round(float(d["effort"]), 3),
            trunk=d["trunk_deg"], shank=d["shank"], knee=None if d["knee_Nmkg_leg"] is None else round(d["knee_Nmkg_leg"], 3),
            hip=None if d["hip_Nmkg_leg"] is None else round(d["hip_Nmkg_leg"], 3),
            hand=round(float(d["hand_load_pct_BW"]), 1)))
        print(mode, h, rows[-1])
    out[mode] = rows
json.dump(out, open("seat_height.json", "w"), indent=1)
