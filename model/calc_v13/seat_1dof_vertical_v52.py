"""v5.2 fair baseline (round-2 audit A6 / E2): the vertical lift (level seat, rises straight up to 0.66 m, no thigh pad: the
contact may reach 12 cm down the thigh) re-run with the SAME fixed L-handrail and the same fixed-grip effort rule as the
curved seat, so that the comparison changes only the seat motion.
Output: seat_1dof/vertical_v52.json (same fields as slider.json users)
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_1dof_v5 as V5
from seat_relative_motion import curve_vertical
from seat_1dof_design import USERS

def job(u):
    V5.PAD_AMAX = 0.12                                   # vertical lift: plain seat, no thigh pad
    return V5.user_job((u, curve_vertical(), "sides", None, None))

if __name__ == "__main__":
    t0 = time.time()
    with Pool() as p: R = dict(p.map(job, USERS))
    vals = [q for q in R.values() if q]; ok = lambda q: bool(q and q["fwd_slip_cm"] <= 2 and q["catch_min_cm"] >= 0)
    E = [q["E_release"] for q in vals if q.get("E_release") is not None]
    summ = dict(n_ok=sum(ok(q) for q in R.values()), fwd_max=max(q["fwd_slip_cm"] for q in vals), catch_min=min(q["catch_min_cm"] for q in vals),
                E_rel_med=round(float(np.median(E)), 3), E_rel_max=round(float(max(E)), 3), n_release_effort=len(E))
    json.dump(dict(note=__doc__, summary=summ, users=R), open(os.path.join(V5.OUT, "vertical_v52.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print(summ, round(time.time() - t0), "s")
