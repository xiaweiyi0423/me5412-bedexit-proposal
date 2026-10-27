"""v5.6: re-evaluate the 81 users at the chosen L bar (x 0.70, z 0.95) after the solve_s fix (rise paths now reach standing).
The bar position is a design decision and stays fixed; the other grid entries in handrail.json were computed before the fix
and are kept only as the record of how the bar was chosen. Updates handrail.json users + the chosen bar's grid summary."""
import json, os
from multiprocessing import Pool
import seat_1dof_handrail as HR
from seat_1dof_design import USERS
if __name__ == "__main__":
    J = json.load(open(HR.PATH)); b = J["bar"]; cv = HR.slider_cv()
    with Pool() as pool: R = dict(pool.map(HR.user_eval, [(u, cv, b) for u in USERS]))
    s = HR.summarize(R); key = f'{b["x"]:.2f},{b["z"]:.2f}'
    print("old", J["grid"][key]["summary"]); print("new", s)
    J["grid"][key]["summary"] = s; J["users"] = R
    J["note_v56"] = "users and the chosen bar's summary re-evaluated after the solve_s fix; other grid entries are pre-fix"
    json.dump(J, open(HR.PATH, "w"), ensure_ascii=False, separators=(",", ":"))
