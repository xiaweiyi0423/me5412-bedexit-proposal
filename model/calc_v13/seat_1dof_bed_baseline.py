"""v5.2 baseline on the same footing as the seat: rising from a bed (low 0.42 m / raised 0.58 m) for the 81 users.

Why: the deck's "13-20 % less effort than a raised bed" came from the older vertical-lift model (seat 0.66 m, hand load
capped at 25 % BW, a bar that rose with the seat). The v5.2 seat uses another effort set-up (hand cap 0.5, the fixed L bar,
contact LP), so the comparison is redone here with the same effort function and the same users.
Seat-off on a bed: hip height = bed + r_b, hip x in {0.00, 0.05, 0.10} m past the bed edge (best of three: perching on the
edge is allowed), the user's own ankle x. Hands: (a) the same L bar at its fixed place, (b) the best bed handle on a grid
x 0.40-0.70, z bed+0.25..bed+0.45 (generous: no reach or install limits). Effort = HR.bar_effort, no seat contact.
The seat's number is its release effort (slider.json, same function, same bar): the moment the seat stops carrying the user.
Output: seat_1dof/bed_baseline.json."""
import json, os, sys
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
from model import Subject
from seat_trajectory import pose
from seat_relative_motion import solve_s
from seat_1dof_design import USERS, ukey
import seat_1dof_handrail as HR

OUT = os.path.join(HERE, "seat_1dof", "bed_baseline.json")
BEDS = [0.42, 0.58]; HIPX = [0.00, 0.05, 0.10]
HANDLES = [(round(x, 2), round(dz, 2)) for x in np.arange(0.40, 0.701, 0.05) for dz in np.arange(0.25, 0.451, 0.05)]

def job(u):
    H, rb, p, xa = u; sub = Subject(H=H); L = HR.bar_now(); out = {}
    for h in BEDS:
        hz = h + rb; poses = []
        for hx in HIPX:
            s = solve_s(sub, xa, hz, hx)
            if s is not None: poses.append(pose(sub, xa, hz, s))
        def best(bars):
            E = [HR.bar_effort(sub, pz, bar=b) for pz in poses for b in bars]; E = [e for e in E if e is not None]
            return round(min(E), 3) if E else None
        out[f"{h:.2f}"] = dict(L_bar=best([L]), handle=best([dict(x=x, z=h + dz) for x, dz in HANDLES]))
    return ukey(u), out

if __name__ == "__main__":
    S = json.load(open(os.path.join(HERE, "seat_1dof", "slider.json")))["users"]
    with Pool() as pool: R = dict(pool.map(job, USERS))
    summ = {}
    for h in BEDS:
        for k in ("L_bar", "handle"):
            pairs = [(S[u]["E_release"], R[u][f"{h:.2f}"][k]) for u in R if S[u].get("E_release") and R[u][f"{h:.2f}"][k]]
            b = np.array([q[1] for q in pairs]); s = np.array([q[0] for q in pairs]); red = 1 - s / b
            summ[f"bed{h:.2f}_{k}"] = dict(n=len(pairs), E_bed_med=round(float(np.median(b)), 3), E_bed_max=round(float(b.max()), 3),
                                           E_seat_med=round(float(np.median(s)), 3),
                                           saving_med=round(float(np.median(red)), 3), saving_p10=round(float(np.percentile(red, 10)), 3),
                                           saving_p90=round(float(np.percentile(red, 90)), 3), n_worse=int((red < 0).sum()))
            print(h, k, summ[f"bed{h:.2f}_{k}"], flush=True)
    json.dump(dict(note=__doc__, summary=summ, users=R), open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    print("done")
