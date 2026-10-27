"""Page data for the v5 seat: one-side inclined rail + tilt link, tilt <= 15 deg, fixed handrail pole -> seat_1dof/page.json

Inputs: slider.json (mechanism + 81 users), v5_checks.json (interference, pinch, tipping, emergency), v5.json (the two
four-bar layouts, for the comparison), cushion.json (rerun on the slider), design.json (users, assist), fourbar.json
(seat-shape study), fourbar2.json + layout.json (earlier linkage placements).
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot, Seat
import seat_1dof_v5 as V5
import seat_1dof_slider as SL
import seat_1dof_layout as LY
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, trunk_for, shank_deg, PAD_AMAX
from seat_relative_motion import rise, curve_fit, track
from model import G

OUT = os.path.join(HERE, "seat_1dof"); TOP = 0.66

os.environ["CUSH_MECH"] = "slider"
import seat_cushion as SC
import seat_cushion_zoned as Z
# cushions shown in the animation (step 5 toggle): uniform (v5), zoned (v5.1 recommended), zoned + 2 cm front step
CUSHIONS = {"u": Z.C_("均匀 6/6，5 cm（现推荐）", 6, 6), "z1": Z.C_("后 10 / 前 3，分界 -2 cm", 10, 3, 0.05, 0.08, -0.02),
            "z2": Z.C_("后 15 / 前 2，分界 -2 cm，前区顶面低 2 cm", 15, 2, 0.05, 0.08, -0.02, 0.02)}

def cushion_patch(sub, pz, k0, c):
    """seat pushing 0.5 BW through cushion c: slide the seat along the curve (Z.CV = the animation curve) from the rigid
    touch index until the cushion force reaches the target; return the contact strip on the body."""
    res, (P, A, ds) = Z.solve(sub, pz, c, max(k0 - 4.0, 0.0))
    if res is None: return dict(lost=True)
    u, L = res; idx = L["idx"]
    if len(idx) == 0: return dict(lost=True)
    Q, phi = SC.pose_at(u, Z.CV); pts = P[idx]; step = max(1, len(pts) // 12); sel = list(range(0, len(pts), step)) + [len(pts) - 1]
    p = L["p"][idx] / 1000; fm = np.hypot(*L["f"].T); pel = A[idx] <= Z.PA
    return dict(lost=False, Q=np.round(Q, 4).tolist(), phi=round(float(phi), 1), strip=np.round(pts[sel], 3).tolist(), p=np.round(p[sel], 1).tolist(),
                len_cm=round(100 * float(ds[idx].sum()), 1), a=[round(100 * float(A[idx].min()), 1), round(100 * float(A[idx].max()), 1)],
                p_max=round(float(p.max()), 1), sink_mm=round(1000 * float(L["sq"].max()), 1), pel=round(float(fm[pel].sum() / fm.sum()), 2),
                a_split=round(100 * float(np.interp(c["split"], np.sort(L["x"]), A[np.argsort(L["x"])])), 1))

def anim_job(args):
    u, cv = args; ST.A_MAX = PAD_AMAX; sub, p = path_of(u); rows = track(sub, p, Seat(r_e=0.03), cv); fr = []
    for i in range(0, len(p), 3):
        pz = p[i]; r = rows[i] if i < len(rows) else None
        d = dict(f=round(pz["f"], 3), A=np.round(pz["A"], 3).tolist(), K=np.round(pz["K"], 3).tolist(), Hp=np.round(pz["Hp"], 3).tolist(),
                 tr=trunk_for(u, pz["Hp"][1], shank_deg(pz)))
        if r and r.get("contact") and r.get("ok"):
            k = min(int(r["k"]), len(cv[1]) - 1)
            d.update(seat=dict(Q=np.round(cv[1][k], 4).tolist(), phi=round(float(cv[2][k]), 1)), C=np.round(r["P"], 3).tolist(),
                     a=round(r["a"], 3), slip=round(r["slip"], 3), catch=round(r["catch"], 3), cush={k_: cushion_patch(sub, pz, int(r["k"]), c_) for k_, c_ in CUSHIONS.items()})
        fr.append(d)
    return ukey(u), dict(L=[round(sub.L_shank, 3), round(sub.L_thigh, 3), round(sub.L_trunk, 3), round(sub.L_uarm, 3), round(sub.L_farm, 3)],
                         foot=round(sub.foot_len, 3), frames=fr)

def env_job(u):
    H, rb, p, xa = u; _, path = rise(H, xa, p, r_b=rb); q, Q, phi = curve_fit(path, V5.PHI_CAP)
    return ukey(u), dict(Q=np.round(Q[15:], 4).tolist(), phi=np.round(phi[15:], 2).tolist())

def zoned_thigh():
    """thigh inclination vs seat tilt at the moment the uniform cushion carries 0.5 BW, per rise stage (medians over 81)."""
    c = CUSHIONS["u"]; out = {}
    for st in Z.STAGES:
        th, ph = [], []
        for u in USERS:
            sub, pz = Z.stage_pose(u, st); res, _ = Z.solve(sub, pz, c)
            if res is None: continue
            th.append(pz["theta"]); ph.append(float(np.interp(res[0], np.arange(len(Z.CV[2])), Z.CV[2])))
        out[str(st)] = dict(thigh=round(float(np.median(th)), 1), seat=round(float(np.median(ph)), 1))
    return out

def screw_curve(sim, Fs, kg=10.0):
    """lead-screw force along the rail (N, + = push up the rail), worst over load positions on the seat."""
    out = []
    for i in range(1, len(sim) - 1, 10):
        n_ = rot(sim[i][1]) @ np.array([0, 1.0]); Fv = -Fs * n_ + np.array([0, -kg * G]); w = 0.0
        for xo in V5.XOFF:
            Cn = sim[i + 1][0] + rot(sim[i + 1][1]) @ np.array([xo, 0]); Cp = sim[i - 1][0] + rot(sim[i - 1][1]) @ np.array([xo, 0])
            f = abs(-(Fv @ (Cn - Cp)) / (sim[i + 1][4] - sim[i - 1][4])); w = max(w, f)
        out.append(round(w))
    return out

if __name__ == "__main__":
    t0 = time.time()
    SLJ = json.load(open(os.path.join(OUT, "slider.json"))); CK = json.load(open(os.path.join(OUT, "v5_checks.json")))
    V5J = json.load(open(os.path.join(OUT, "v5.json"))); CU = json.load(open(os.path.join(OUT, "cushion.json")))
    D = json.load(open(os.path.join(OUT, "design.json"))); FB = json.load(open(os.path.join(OUT, "fourbar.json")))
    ZJ = json.load(open(os.path.join(OUT, "cushion_zoned.json"))); ZB = {(r["user"], r["stage"]): r["effort_all"] for r in ZJ["effort"]["均匀 6/6，5 cm（现推荐）"]["rows"]}
    ZT = zoned_thigh()
    import seat_1dof_handrail as HR
    import seat_1dof_v5_checks as VC
    HRJ = json.load(open(os.path.join(OUT, "handrail.json"))); VJ = json.load(open(os.path.join(OUT, "vertical_v52.json")))
    TRK = ZJ.get("track", {})
    sim, g = SL.simulate(SLJ["x"], 700); c1, c2 = np.array(SLJ["x"][:2]), np.array(SLJ["x"][2:4]); M = SLJ["mech"]
    cv = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim]))
    zs = [round(float(p[0][1]), 3) for p in sim]
    mech = dict(M, kind="slider", name="v5-slider", top=M.get("top", TOP), rail_lo=CK["rail"]["lo"], rail_hi=CK["rail"]["hi"], rail2=[CK["rail"]["lo2"], CK["rail"]["hi2"]],
                travel=dict(dx=round(float(sim[-1][0][0] - sim[0][0][0]), 3), dz=round(float(sim[-1][0][1] - sim[0][0][1]), 3)),
                bracket_depth_mm=round(-1000 * min(c1[1], c2[1])),
                frames=[dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in sim[::12]],
                force_curve=dict(z=zs[1:-1:10], hold100=screw_curve(sim, 1.5 * 100 * G), lift60=screw_curve(sim, 0.5 * 60 * G), lift100=screw_curve(sim, 0.5 * 100 * G)),
                tilt_curve=dict(z=zs[::10], phi=[round(float(p[1]), 1) for p in sim[::10]]), summary=SLJ["summary"])
    mech["F_lift60_N"] = max(mech["force_curve"]["lift60"]); mech["F_lift100_N"] = max(mech["force_curve"]["lift100"]); mech["F_hold100_N"] = max(mech["force_curve"]["hold100"])
    users = {}
    for k, q in SLJ["users"].items():
        if q is None: users[k] = dict(release_hz=None, fwd_slip_max_cm=99, min_catch_cm=-99); continue
        users[k] = dict(release_hz=q["release_hz"], fwd_slip_max_cm=q["fwd_slip_cm"], min_catch_cm=q["catch_min_cm"], E0_release=q["E_release"],
                        E0_release_stooped=q["E_release_stooped"], phi_release=q["phi_release"], shear_path_cm=q["shear_path_cm"], E_supported_max=q["E_supported_max"])
    Z.CV = cv                                  # the cushion solve runs on the same curve (and index) as the animation
    with Pool() as pool: AN = dict(pool.map(anim_job, [(u, cv) for u in USERS]))
    for k_ in CUSHIONS:
        cs = [f["cush"][k_] for a_ in AN.values() for f in a_["frames"] if "seat" in f]; ok = [c for c in cs if not c["lost"]]
        print("cushion", k_, "frames", len(cs), "lost", len(cs) - len(ok), "len med", np.median([c["len_cm"] for c in ok]), "p med", np.median([c["p_max"] for c in ok]), "pel med", np.median([c["pel"] for c in ok]))
    with Pool() as pool: ENV = dict(pool.map(env_job, USERS))
    frames = []
    for fr in sim[::35] + [sim[-1]]:
        plate, br = VC.seat_body(fr[0], fr[1])
        frames.append(dict(Q=np.round(fr[0], 4).tolist(), phi=round(float(fr[1]), 2), P1=np.round(fr[2], 4).tolist(), P2=np.round(fr[3], 4).tolist(),
                           plate=np.round(plate, 4).tolist(), bracket=np.round(br, 4).tolist()))
    b = CK["bed_floor_cm"]
    clear_rows = [["机构箱（双导轨、滑块、电机、连杆）", "床", "床头一侧", b["机构箱（导轨、滑块、电机、连杆）"], "固定件，含 2 cm 箱壁"],
                  ["座板（刚性部分）", "床", "全宽", b["座板（刚性部分）"], "坐着时（座板后缘软唇边 4.5 cm 搭在床垫上）"], ["座板支架", "床", "全宽", b["座板支架"], "全行程"],
                  ["全部活动零件", "地面", "全部", b["全部活动零件—地面"], "全行程"],
                  ["座板与支架（全宽，含前区下沉台阶）", "小腿、脚", "全宽", CK["bracket_vs_legs_cm"]["min"], "81 人，按各自时刻，逐帧"]]
    placements = {}
    for n, Vv in V5J["layouts"].items():
        m_ = Vv["mech"]; placements["v5-" + n] = dict(n_ok=Vv["summary"]["n_ok"], fwd_max=Vv["summary"]["fwd_max"], catch_min=Vv["summary"]["catch_min"],
                                                      centre_err_mm=m_["centre_err_mm"], phi_max=m_["phi_run_max"], bracket_mm=m_["bracket_depth_mm"],
                                                      force_kN=None if not m_["act"] else round(m_["act"]["F_hold100_N"] / 1000, 1), leg=Vv["summary"]["leg_clear_min"] if n == "mid" else None)
    placements["v5-slider"] = dict(n_ok=SLJ["summary"]["n_ok"], fwd_max=SLJ["summary"]["fwd_max"], catch_min=SLJ["summary"]["catch_min"], centre_err_mm=M["centre_err_mm"],
                                   phi_max=M["phi_run_max"], bracket_mm=mech["bracket_depth_mm"], force_kN=round(mech["F_hold100_N"] / 1000, 1), leg=None)
    page = dict(users=D["users"], assist=D["assist"], envelope=ENV, design_curve=dict(D["design_curve"], poses=V5J["design_curve"], phi_max=V5.PHI_CAP),
                consts=dict(D["consts"], top=M.get("top", TOP), phi_max=V5.PHI_CAP, handrail=HR.bar_now()), mech=mech, anim=AN,
                check=dict(design=users, vertical={k: (dict(release_hz=None, fwd_slip_max_cm=99, min_catch_cm=-99) if q is None else
                                                       dict(release_hz=q["release_hz"], fwd_slip_max_cm=q["fwd_slip_cm"], min_catch_cm=q["catch_min_cm"], E0_release=q["E_release"]))
                                                   for k, q in VJ["users"].items()}, vertical_summary=VJ["summary"],
                           cushion={nm: dict(summary=t["summary"], users=t["users"]) for nm, t in TRK.items()}),
                handrail=dict(bar=HRJ["bar"], chosen=HRJ["chosen"], grid=HRJ["grid"]), shapes=dict(table=FB["table"]),
                cushion=dict(cushions=CU["cushions"], summary=CU["summary"], sitdown=CU["sitdown"]), placements=placements,
                zoned=dict(grid={k_: dict(c=v_["c"], all={q: v_["all"].get(q) for q in ("lost", "pel_share", "cop_a_cm", "peak_a_cm", "p_peak_kPa", "sink_mm", "bottom_share", "peak_on_pelvis_share", "junction_seat_x_cm")},
                                          by_stage={s_: {q: b_.get(q) for q in ("lost", "pel_share", "junction_seat_x_cm")} for s_, b_ in v_["by_stage"].items()}, sitdown=v_["sitdown"]) for k_, v_ in ZJ["grid"].items()},
                           effort={k_: dict(all={q: v_["all"].get(q) for q in ("effort_all", "effort_free", "lost", "pel_share")}, by_stage={s_: {q: b_.get(q) for q in ("effort_all", "lost", "pel_share")} for s_, b_ in v_["by_stage"].items()},
                                            worse=sum(1 for r in v_["rows"] if r["effort_all"] > ZB[(r["user"], r["stage"])] + 0.005), max_worse=round(max(r["effort_all"] - ZB[(r["user"], r["stage"])] for r in v_["rows"]), 3))
                                   for k_, v_ in ZJ["effort"].items()},
                           thigh=ZT, ids={k_: c_["name"] for k_, c_ in CUSHIONS.items()}),
                layout=dict(frames=frames, clear_rows=clear_rows, pinch=CK["pinch_cm"], tipping=CK["tipping"], emergency=CK["emergency"], forces=CK["forces"], kind="slider",
                            legs_worst=CK["bracket_vs_legs_cm"], bed_floor_cm=CK["bed_floor_cm"], housing=CK["rail"]["housing"], motor=CK["rail"]["motor"],
                            rail2=[CK["rail"]["lo2"], CK["rail"]["hi2"]], Y=CK["Y"], seat_t=CK["seat_t"], rail_gap=CK["rail_gap"], carriage_span=CK["carriage_span"],
                            sizes=dict(LIP=V5.LIP)))
    json.dump(page, open(os.path.join(OUT, "page.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s", {k: mech[k] for k in ("F_lift60_N", "F_lift100_N", "F_hold100_N")})
