"""Page data for the v5 seat (tilt <= 15 deg, fixed handrail pole, chosen linkage layout) -> seat_1dof/page.json

Inputs: seat_1dof/v5.json (both layouts), design.json (users, assist), fourbar.json (seat-shape study), fourbar2.json and
layout.json (earlier placements, for the comparison table), cushion.json (cushion study, rerun on the v5 linkage).
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot, Seat
import seat_1dof_v5 as V5                     # sets the v5 design curve inside the four-bar module
import seat_1dof_fourbar2 as FB2
import seat_1dof_layout as LY
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, trunk_for, shank_deg, PAD_AMAX
from seat_relative_motion import rise, curve_fit, track
from model import G

OUT = os.path.join(HERE, "seat_1dof"); TOP = 0.66

def choose(v5):
    m = v5["layouts"].get("mid")
    if m and m["summary"]["n_ok"] == 81 and m["summary"]["leg_clear_min"] >= 2 and m["mech"]["transmission_deg"][0] >= 35: return "mid"
    return "sides"

def anim_job(args):
    u, cv = args; ST.A_MAX = PAD_AMAX; sub, p = path_of(u); rows = track(sub, p, Seat(r_e=0.03), cv); fr = []
    for i in range(0, len(p), 3):
        pz = p[i]; r = rows[i] if i < len(rows) else None
        d = dict(f=round(pz["f"], 3), A=np.round(pz["A"], 3).tolist(), K=np.round(pz["K"], 3).tolist(), Hp=np.round(pz["Hp"], 3).tolist(),
                 tr=trunk_for(u, pz["Hp"][1], shank_deg(pz)))
        if r and r.get("contact") and r.get("ok"):
            k = min(int(r["k"]), len(cv[1]) - 1)
            d.update(seat=dict(Q=np.round(cv[1][k], 4).tolist(), phi=round(float(cv[2][k]), 1)), C=np.round(r["P"], 3).tolist(),
                     a=round(r["a"], 3), slip=round(r["slip"], 3), catch=round(r["catch"], 3))
        fr.append(d)
    return ukey(u), dict(L=[round(sub.L_shank, 3), round(sub.L_thigh, 3), round(sub.L_trunk, 3), round(sub.L_uarm, 3), round(sub.L_farm, 3)],
                         foot=round(sub.foot_len, 3), frames=fr)

def env_job(u):
    H, rb, p, xa = u; _, path = rise(H, xa, p, r_b=rb); q, Q, phi = curve_fit(path, V5.PHI_CAP)
    return ukey(u), dict(Q=np.round(Q[15:], 4).tolist(), phi=np.round(phi[15:], 2).tolist())

if __name__ == "__main__":
    t0 = time.time()
    v5 = json.load(open(os.path.join(OUT, "v5.json"))); lay = choose(v5); L5 = v5["layouts"][lay]
    D = json.load(open(os.path.join(OUT, "design.json"))); FB = json.load(open(os.path.join(OUT, "fourbar.json")))
    CU = json.load(open(os.path.join(OUT, "cushion.json"))); F2 = json.load(open(os.path.join(OUT, "fourbar2.json"))); LYJ = json.load(open(os.path.join(OUT, "layout.json")))
    x = np.array(L5["x"]); A, B, c1, c2 = x[:2], x[2:4], x[4:6], x[6:8]; act = L5["mech"]["act"]
    sim = [p[:5] for p in FB2.run(x, n=700)]; cv = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim]))
    mus = []
    for p in sim:
        d1 = p[3] - p[2]; d2 = p[3] - B; mus.append(float(np.degrees(np.arccos(np.clip(d1 @ d2 / (np.hypot(*d1) * np.hypot(*d2)), -1, 1)))))
    zs = [round(float(p[0][1]), 3) for p in sim]
    mech = dict(L5["mech"], kind="fourbar", name="v5-" + lay, layout=lay, top=TOP,
                travel=dict(dx=round(float(sim[-1][0][0] - sim[0][0][0]), 3), dz=round(float(sim[-1][0][1] - sim[0][0][1]), 3)),
                frames=[dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in sim[::12]],
                transmission_curve=dict(z=zs[::10], mu=[round(m, 1) for m in mus[::10]]), summary=L5["summary"])
    mech["bracket_depth_mm"] = round(-1000 * min(c1[1], c2[1]))
    # users (map v5 field names to the page's)
    users = {}
    for k, q in L5["users"].items():
        if q is None: users[k] = dict(release_hz=None, fwd_slip_max_cm=99, min_catch_cm=-99); continue
        users[k] = dict(release_hz=q["release_hz"], fwd_slip_max_cm=q["fwd_slip_cm"], min_catch_cm=q["catch_min_cm"], E0_release=q["E_release"],
                        E0_release_stooped=q["E_release_stooped"], phi_release=q["phi_release"], shear_path_cm=q["shear_path_cm"], E_supported_max=q["E_supported_max"],
                        leg_clear_cm=q.get("leg_clear_cm"))
    with Pool() as pool: AN = dict(pool.map(anim_job, [(u, cv) for u in USERS]))
    with Pool() as pool: ENV = dict(pool.map(env_job, USERS))
    # layout frames for the interference drawing
    frames = []
    for fr in sim[::35] + [sim[-1]]:
        plate, br = LY.seat_polys(fr[0], fr[1], c1, c2); (Dd, H, rh), (H2, Ee, rr), _ = LY.act_parts(fr, act, A, B)
        frames.append(dict(Q=np.round(fr[0], 4).tolist(), phi=round(float(fr[1]), 2), P1=np.round(fr[2], 4).tolist(), P2=np.round(fr[3], 4).tolist(),
                           plate=np.round(plate, 4).tolist(), bracket=np.round(br, 4).tolist(), D=np.round(Dd, 4).tolist(), H=np.round(H, 4).tolist(), E=np.round(Ee, 4).tolist()))
    actbed = 1.0
    for fr in sim[::5]:
        (Dd, H, rh), (H2, Ee, rr), _ = LY.act_parts(fr, act, A, B)
        actbed = min(actbed, float(LY.bed_d(LY.seg_pts(Dd, H)).min()) - rh, float(LY.bed_d(LY.seg_pts(H2, Ee)).min()) - rr)
    s5 = L5["summary"]
    clear_rows = [["座板、支架、摇杆、立柱", "床、地面", "全部", L5["mech"]["bed_clear_cm"], "坐着时座板刚性部分与床垫侧面"],
                  ["推杆", "床、地面", "推杆所在平面", round(100 * actbed, 1), "全行程"],
                  ["推杆" + ("、连杆、支架" if lay == "mid" else ""), "小腿、脚", "中间" if lay == "mid" else "两侧（腿外侧）", s5["leg_clear_min"], "81 人，按各自时刻"]]
    pinch = L5["mech"]["pinch_cm"]
    Y = dict(seat=0.22, rockA=0.255, rockB=0.285, rail=0.27, act=0.0) if lay == "sides" else dict(seat=0.22, rockA=0.0, rockB=0.0, rail=0.27, act=0.06)
    # placements table: earlier variants + the two v5 layouts
    placements = {}
    for n, Vv in F2["variants"].items():
        m_ = Vv["mech"]; placements[n] = dict(space_x=m_["space_x"], space_z=m_["space_z"], centre_err_mm=m_["centre_err_mm"], tilt_err_deg=m_["tilt_err_deg"],
                                              transmission_deg=m_["transmission_deg"], n_ok=Vv["summary"]["n_ok"], clear_calf_cm=Vv["summary"].get("clear_calf_cm"), phi_max=m_.get("phi_max"))
    placements["layout"] = dict(space_x=LYJ["mech"]["space_x"], space_z=LYJ["mech"]["space_z"], centre_err_mm=LYJ["mech"]["centre_err_mm"], tilt_err_deg=LYJ["mech"]["tilt_err_deg"],
                                transmission_deg=LYJ["mech"]["transmission_deg"], n_ok=LYJ["summary"]["n_ok"], clear_calf_cm=None, phi_max=LYJ["mech"]["phi_max"])
    for n, Vv in v5["layouts"].items():
        m_ = Vv["mech"]; placements["v5-" + n] = dict(space_x=m_["space_x"], space_z=m_["space_z"], centre_err_mm=m_["centre_err_mm"], tilt_err_deg=m_["tilt_err_deg"],
                                                      transmission_deg=m_["transmission_deg"], n_ok=Vv["summary"]["n_ok"], clear_calf_cm=Vv["summary"]["leg_clear_min"] if n == "mid" else None,
                                                      phi_max=m_["phi_run_max"], coupler=m_["coupler"], act=m_["act"] and {k: m_["act"][k] for k in ("stroke", "L", "F_hold100_N", "F_lift60_N", "F_lift100_N")},
                                                      summary=Vv["summary"], pins=m_["pins_hold100_N"], bed=m_["bed_clear_cm"])
    page = dict(users=D["users"], assist=D["assist"], envelope=ENV, design_curve=dict(D["design_curve"], poses=v5["design_curve"], phi_max=V5.PHI_CAP),
                consts=dict(D["consts"], top=TOP, phi_max=V5.PHI_CAP, pole=dict(x=0.69, z=[0.75, 1.10])), mech=mech, anim=AN,
                check=dict(design=users, vertical=D["check"]["vertical"]), shapes=dict(table=FB["table"]), cushion=dict(cushions=CU["cushions"], summary=CU["summary"], sitdown=CU["sitdown"]),
                placements=placements, layout=dict(frames=frames, clear_rows=clear_rows, pinch=pinch, Y=Y, kind=lay, sizes=dict(R_ROCK=0.02, R_POST=0.025, R_HOUS=0.03, R_ROD=0.012, PLATE_T=0.045, LIP=V5.LIP)),
                v5=dict(chosen=lay, layouts={n: dict(summary=Vv["summary"], mech={k: Vv["mech"][k] for k in Vv["mech"] if k not in ("frames",)}) for n, Vv in v5["layouts"].items()}))
    json.dump(page, open(os.path.join(OUT, "page.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("layout", lay, s5); print("done", round(time.time() - t0), "s")
