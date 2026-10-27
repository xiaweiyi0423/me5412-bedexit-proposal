"""v5.6: re-evaluate the 81 users on the one-side four-bar of fourbar_oneside.json (geometry and actuator kept) after the
solve_s fix, so the four-bar and the rail are compared on the same full-rise paths. Updates summary + users in place."""
import json, os
import numpy as np
from multiprocessing import Pool
import seat_1dof_v5 as V5, seat_1dof_fourbar2 as FB2
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seat_1dof", "fourbar_oneside.json")
if __name__ == "__main__":
    J = json.load(open(OUT)); v = np.array(J["x"]); act = J["act"]; s = FB2.run(v, n=700)
    cv = with_prefix(np.array([p[0] for p in s]), np.array([p[1] for p in s]))
    with Pool() as p: R = dict(p.map(V5.user_job, [(u, cv, "sides", v, act) for u in USERS]))
    vals = [q for q in R.values() if q]; ok = lambda q: bool(q and q["fwd_slip_cm"] <= 2 and q["catch_min_cm"] >= 0)
    E = [q["E_release"] for q in vals if q.get("E_release") is not None]
    summ = dict(n_ok=sum(ok(q) for q in R.values()), fwd_max=max(q["fwd_slip_cm"] for q in vals), catch_min=min(q["catch_min_cm"] for q in vals),
                phi_release_max=max(q["phi_release"] for q in vals), E_rel_med=round(float(np.median(E)), 3), E_rel_max=round(float(max(E)), 3),
                E_sup_max=max(q["E_supported_max"] for q in vals), leg_clear_min_cm=min(q.get("leg_clear_cm", 9) for q in vals))
    print("old", J["summary"]); print("new", summ)
    J["summary"] = summ; J["users"] = R; J["note_v56"] = "users re-evaluated on full-rise paths (solve_s fix); mechanism unchanged"
    json.dump(J, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
