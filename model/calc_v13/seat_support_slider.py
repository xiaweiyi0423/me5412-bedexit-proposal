"""v5.4 user model for the controller simulation of the inclined-rail seat (replaces seat_support.py, which was built for
the vertical lift with a bar that rose with the seat).

For the reference user (1.60 m, buttock 9 cm, even hip shift, ankle 29 cm) the rise is tracked on the real seat curve
(slider.json, same contact rules as seat_1dof_slider.py eval). At every contact instant the seat pose (height, tilt) and
the body pose are known. For seat-force limits cap = 0 .. 1.2 BW (force along the seat normal), the effort LP with the
fixed L bar (seat_1dof_handrail.bar_effort) gives the least effort; inverted, it gives the least seat force a user whose
strongest effort is c can reach at that seat position: min_seat(h, c). After the last supported instant (contact past
the pad end) the seat no longer reaches the buttock; seat-off then needs E_free at that pose.
Output: seat_1dof/seat_support_slider.json  {h, phi, E_free, caps, E[cap] per row, release}
"""
import json, os
import numpy as np
from multiprocessing import Pool
import seat_trajectory as ST
from seat_trajectory import Seat, rot
from seat_relative_motion import track
import seat_1dof_handrail as HR
from seat_1dof_design import path_of, PAD_AMAX
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "seat_1dof", "seat_support_slider.json")
REF = (1.60, 0.09, 1.0, 0.29); CAPS = [round(x, 3) for x in np.arange(0.0, 1.2001, 0.025)]
CV = HR.slider_cv()

def rows_of(u):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u)
    rows = track(sub, path, Seat(r_e=0.03), CV); good = [r for r in rows if r.get("contact") and r.get("ok")]
    return sub, path, good

def row_job(args):
    i = args; sub, path, good = rows_of(REF); r = good[i]; p_ = path[i]
    k = min(int(r["k"]), len(CV[1]) - 1); n_ = rot(CV[2][k]) @ np.array([0, 1.0]); con = (np.array(r["P"]), n_, r["pelvis"])
    E = []
    for c in CAPS:
        e = HR.bar_effort(sub, p_, con, cap=c) if c > 0 else HR.bar_effort(sub, p_)
        E.append(None if e is None else round(e, 4))
    return i, dict(h=round(float(CV[1][k][1]), 4), phi=round(float(CV[2][k]), 2), hip_z=round(float(p_["Hp"][1]), 4), E=E)

if __name__ == "__main__":
    sub, path, good = rows_of(REF); idx = list(range(0, len(good), 2)) + ([len(good) - 1] if (len(good) - 1) % 2 else [])
    with Pool() as p: R = dict(p.map(row_job, idx))
    rows = [R[i] for i in sorted(R)]
    rel = rows[-1]
    json.dump(dict(note=__doc__, user="H1.60 r0.09 p1.0 xa0.29", caps=CAPS, rows=rows, release=dict(h=rel["h"], E_free=rel["E"][0]),
                   top=round(float(CV[1][-1][1]), 3), curve=dict(h=[round(float(q[1]), 4) for q in CV[1][::5]], phi=[round(float(x), 2) for x in CV[2][::5]])),
              open(OUT, "w"), separators=(",", ":"))
    print(len(rows), "rows; seat h", rows[0]["h"], "->", rel["h"], "; E_free at release", rel["E"][0], "; E with cap 0.5 at start", rows[0]["E"][20])
    for r in rows[::3]: print(r["h"], r["phi"], [r["E"][j] for j in (0, 4, 8, 12, 16, 20)])
