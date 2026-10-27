"""v5.6: how a user sits on the bed edge with the feet on the floor: thigh slope (down toward the knee) on a 0.42 m and a
0.58 m bed, hip right over the edge, from the same rise geometry as the fall-catch bed paths. Also: can the user reach the
L bar while still sitting on the bed (hip over the edge, or 5 / 10 cm further in; trunk lean <= 30 deg, seat_1dof_handrail.reach_seated)? Replaces the v5.3 statement
"9 short users cannot sit on a 0.58 m bed", which came from the rise paths being cut short (solve_s bug). Output: seat_1dof/bed_thigh.json"""
import json, os
import numpy as np
import seat_1dof_fall_catch as FC
from seat_1dof_design import USERS
HERE = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":
    R = {}
    for H in (1.50, 1.60, 1.75):
        for bed in (0.42, 0.58):
            th = [FC.bed_path(h, xa, p, 0.0, bed + rb)[0]["theta"] for (h, rb, p, xa) in USERS if h == H]
            R[f"{H:.2f}_{bed:.2f}"] = dict(med=round(float(np.median(th)), 1), min=round(float(min(th)), 1), max=round(float(max(th)), 1))
    import seat_1dof_handrail as HR
    from seat_relative_motion import solve_s
    from seat_trajectory import pose, Z0
    from model import Subject
    bar = HR.bar_now(); reach = {}
    for hx in (0.0, -0.05, -0.10):
        n = 0
        for (H, rb, p, xa) in USERS:
            sub = Subject(H=H); s = solve_s(sub, xa, Z0 + rb, hx)
            n += bool(s is not None and HR.reach_seated(sub, pose(sub, xa, Z0 + rb, s), bar))
        reach[f"{hx:.2f}"] = n
    print("reach from the bed", reach)
    json.dump(dict(note=__doc__, thigh_slope_deg=R, reach_from_bed=reach, bar=bar), open(os.path.join(HERE, "seat_1dof", "bed_thigh.json"), "w"), ensure_ascii=False, indent=1)
    print(R)
