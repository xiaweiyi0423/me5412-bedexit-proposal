"""v5.3: seat height when each of the 81 users leaves the seat (inclined rail, rigid contact, pad limit as in slider.json).
Answers the deck audit question "is the upper part of the rail used?". Output: seat_1dof/release_z.json"""
import json, os
import numpy as np
from multiprocessing import Pool
import seat_1dof_handrail as HR, seat_trajectory as ST
from seat_trajectory import Seat
from seat_relative_motion import track
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
CV = HR.slider_cv()
def job(u):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u)
    rows = track(sub, path, Seat(r_e=0.03), CV); good = [r for r in rows if r.get("contact") and r.get("ok")]
    k = min(int(good[-1]["k"]), len(CV[1]) - 1)
    return ukey(u), dict(seat_z=round(float(CV[1][k][1]), 3), phi=round(float(CV[2][k]), 1))
if __name__ == "__main__":
    with Pool() as p: R = dict(p.map(job, USERS))
    z = np.array([v["seat_z"] for v in R.values()])
    print("seat z at release: min %.3f p10 %.3f med %.3f p90 %.3f max %.3f; top %.2f" % (z.min(), *np.percentile(z, [10, 50, 90]), z.max(), max(q[0][1] for q in [CV[1:2]]) if False else CV[1][-1][1]))
    json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seat_1dof", "release_z.json"), "w"), separators=(",", ":"))
