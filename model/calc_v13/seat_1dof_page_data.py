"""Assemble the data for page/seat_1dof.html (second version: four-bar hidden under the seat + cushion stiffness).

Inputs: seat_1dof/design.json (users, assist, envelope, design curve, two-track guide, vertical baseline),
        seat_1dof/fourbar.json (four-bar per seat shape), seat_1dof/cushion.json (cushion study).
Recomputes for the recommended mechanism (flat-seat four-bar run to 0.66 m): the 81-user check, stooped-trunk effort, the
per-user animation, motor torque and transmission angle along the travel.
Output: seat_1dof/page.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot
from seat_1dof_design import USERS, ukey, path_of, track_user, stoop_job, trunk_for, shank_deg, PAD_AMAX
from seat_1dof_fourbar import with_prefix
from seat_cushion import SIMS, V
from model import G, Subject

OUT = os.path.join(HERE, "seat_1dof")
TOP = 0.66
MECH = os.environ.get("MECH", "swept15")      # which four-bar from fourbar2.json goes on the page

if __name__ == "__main__":
    t0 = time.time()
    D = json.load(open(os.path.join(OUT, "design.json"))); FB = json.load(open(os.path.join(OUT, "fourbar.json"))); CU = json.load(open(os.path.join(OUT, "cushion.json")))
    F2 = json.load(open(os.path.join(OUT, "fourbar2.json")))
    import seat_1dof_fourbar2 as FB2
    x = np.array(F2["variants"][MECH]["x"]); sim = [p[:5] for p in FB2.run(x, n=700)]
    cv = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim])); npre = len(cv[0]) - len(sim)
    A, B, c1, c2 = x[:2], x[2:4], x[4:6], x[6:8]
    seat_kw = dict(r_e=0.03)
    with Pool() as pool: R = pool.map(track_user, [(u, cv, PAD_AMAX, seat_kw) for u in USERS])
    real = {k: s for k, s, _ in R}; rows_real = {k: rows for k, _, rows in R}
    with Pool() as pool: SK = pool.map(stoop_job, [(u, real[ukey(u)].get("release_hz"), real[ukey(u)].get("release_shank")) for u in USERS])
    for u, e in zip(USERS, SK): real[ukey(u)]["E0_release_stooped"] = e
    # torque at the input pivot A, transmission angle, along the travel
    def torque(Fs):
        out = []
        for i in range(1, len(sim) - 1):
            n_ = rot(sim[i][1]) @ np.array([0.0, 1.0]); F = -Fs * n_ + np.array([0, -10 * G])
            dQ = (sim[i + 1][0] - sim[i - 1][0]) / (sim[i + 1][4] - sim[i - 1][4]); out.append(float(-(F @ dQ)))
        return out
    tl, th = torque(0.5 * 60 * G), torque(1.5 * 100 * G)
    mus = []
    for p in sim:
        d1 = p[3] - p[2]; d2 = p[3] - B; mus.append(float(np.degrees(np.arccos(np.clip(d1 @ d2 / (np.hypot(*d1) * np.hypot(*d2)), -1, 1)))))
    pts = np.array([A, B] + [p[2] for p in sim] + [p[3] for p in sim])
    zs = [round(float(p[0][1]), 3) for p in sim]
    mech = dict(kind="fourbar", A=A.round(4).tolist(), B=B.round(4).tolist(), c1=c1.round(4).tolist(), c2=c2.round(4).tolist(),
                L1=round(float(np.hypot(*(sim[0][2] - A))), 4), L2=round(float(np.hypot(*(sim[0][3] - B))), 4), coupler=round(float(np.hypot(*(c1 - c2))), 4),
                input_sweep_deg=round(float(np.degrees(sim[-1][4] - sim[0][4])), 1), transmission_deg=[round(min(mus), 1), round(max(mus), 1)],
                torque_lift60_Nm=[round(min(tl), 1), round(max(tl), 1)], torque_hold100_Nm=[round(min(th), 1), round(max(th), 1)],
                space_x=[round(float(pts[:, 0].min()), 3), round(float(pts[:, 0].max()), 3)], space_z=[round(float(pts[:, 1].min()), 3), round(float(pts[:, 1].max()), 3)],
                top=TOP, phi_end=round(float(sim[-1][1]), 1), phi_max=round(float(max(p[1] for p in sim)), 1),
                travel=dict(dx=round(float(sim[-1][0][0] - sim[0][0][0]), 3), dz=round(float(sim[-1][0][1] - sim[0][0][1]), 3)),
                frames=[dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in sim[::12]],
                torque_curve=dict(z=zs[1:-1][::10], lift60=[round(t, 1) for t in tl[::10]], hold100=[round(t, 1) for t in th[::10]]),
                transmission_curve=dict(z=zs[::10], mu=[round(m, 1) for m in mus[::10]]))
    # clearance between the links and the calves (5 cm behind the shank line), at the matching seat position
    def seg_d(P, X, Y):
        d = Y - X; t = np.clip(((P - X) @ d) / (d @ d), 0, 1); return float(np.hypot(*(P - (X + t * d))))
    worst = []
    for u in USERS:
        sub, p = path_of(u); rows = rows_real[ukey(u)]; dmin = 9.0
        for r, pz in zip(rows, p):
            if not r.get("contact"): break
            i = min(max(int(r["k"]) - npre, 0), len(sim) - 1); P1, P2 = sim[i][2], sim[i][3]
            for X, Y in ((A, P1), (B, P2)):
                for t in np.linspace(0, 1, 12):
                    dmin = min(dmin, seg_d(X + t * (Y - X), pz["A"], pz["K"]) - 0.05)
        worst.append(dict(user=ukey(u), clearance_cm=round(100 * dmin, 1)))
    mech["calf_clearance_min_cm"] = min(w["clearance_cm"] for w in worst)
    mech["name"] = MECH; mech["act"] = F2["variants"][MECH]["mech"]["act"]; mech["bracket_depth_mm"] = F2["variants"][MECH]["mech"]["bracket_depth_mm"]
    mech["summary"] = F2["variants"][MECH]["summary"]
    placements = {}
    for n, Vv in F2["variants"].items():
        m_ = Vv["mech"]; placements[n] = dict(A=m_["A"], B=m_["B"], space_x=m_["space_x"], space_z=m_["space_z"], bracket_depth_mm=m_["bracket_depth_mm"],
                                              centre_err_mm=m_["centre_err_mm"], tilt_err_deg=m_["tilt_err_deg"], transmission_deg=m_["transmission_deg"],
                                              act=None if m_["act"] is None else {k: m_["act"][k] for k in ("stroke", "L", "F_hold100_N", "F_lift60_N", "D", "on")},
                                              **{k: Vv["summary"][k] for k in ("n_ok", "fwd_max", "catch_min", "E_med", "clear_calf_cm", "clear_act_calf_cm", "cushion_lost")})
    # animation
    anim = {}
    for u in USERS:
        sub, p = path_of(u); rows = rows_real[ukey(u)]; fr = []
        for i in range(0, len(p), 3):
            pz = p[i]; r = rows[i] if i < len(rows) else None
            d = dict(f=round(pz["f"], 3), A=np.round(pz["A"], 3).tolist(), K=np.round(pz["K"], 3).tolist(), Hp=np.round(pz["Hp"], 3).tolist(),
                     tr=trunk_for(u, pz["Hp"][1], shank_deg(pz)))
            if r and r.get("contact") and r.get("ok"):
                k = min(int(r["k"]), len(cv[1]) - 1)
                d.update(seat=dict(Q=np.round(cv[1][k], 4).tolist(), phi=round(float(cv[2][k]), 1)), C=np.round(r["P"], 3).tolist(),
                         a=round(r["a"], 3), slip=round(r["slip"], 3), catch=round(r["catch"], 3))
            fr.append(d)
        anim[ukey(u)] = dict(L=[round(sub.L_shank, 3), round(sub.L_thigh, 3), round(sub.L_trunk, 3), round(sub.L_uarm, 3), round(sub.L_farm, 3)],
                             foot=round(sub.foot_len, 3), frames=fr)
    page = dict(users=D["users"], assist=D["assist"], envelope=D["envelope"], design_curve=D["design_curve"], consts=D["consts"],
                mech=mech, anim=anim, check=dict(design=real, vertical=D["check"]["vertical"], twotrack=D["check"]["design"]),
                twotrack={k: D["mech"][k] for k in ("c1", "c2", "stroke", "act_len", "F_act_lift60_N", "F_act_hold100_N", "R_min")},
                shapes=dict(table=FB["table"], mech={R: {k: v for k, v in m.items() if k != "frames"} for R, m in FB["mech"].items()}),
                cushion=dict(cushions=CU["cushions"], summary=CU["summary"], sitdown=CU["sitdown"]), placements=placements)
    page["consts"]["top"] = TOP
    json.dump(page, open(os.path.join(OUT, "page.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    ok = lambda v: bool(v.get("release_hz") and v["fwd_slip_max_cm"] <= 2 and v["min_catch_cm"] >= 0)
    E = [v["E0_release"] for v in real.values()]
    print("check", sum(ok(v) for v in real.values()), "fwd", max(v["fwd_slip_max_cm"] for v in real.values()), "catch", min(v["min_catch_cm"] for v in real.values()),
          "E", round(float(np.median(E)), 3), max(E), "stooped", round(float(np.median([v["E0_release_stooped"] for v in real.values()])), 3))
    print({k: v for k, v in mech.items() if k not in ("frames", "torque_curve", "transmission_curve")}); print("done", round(time.time() - t0), "s")
