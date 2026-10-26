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
CUSH_REC = next(c for c in SC.CUSH if c[0] == "中硬 + 行程到 0.66 m")

def cushion_patch(sub, pz, k0):
    """recommended cushion, seat pushing 0.5 BW: slide the seat along the curve (SC.CVS[top] = the slider curve) from the
    rigid touch index k0 until the cushion force reaches the target; return the contact strip on the body."""
    P, A, ds = SC.dense_outline(pz); target = 0.5 * sub.M * G; CV = SC.CVS[CUSH_REC[5]]; n = len(CV[0]) - 1
    u = max(k0 - 3.0, 0.0); prev = u; L = SC.load(u, P, A, ds, CUSH_REC)
    while L["Fm"] < target:
        prev = u; u += 0.5
        if u >= n: return dict(lost=True)
        L = SC.load(u, P, A, ds, CUSH_REC)
    lo, hi = prev, u
    for _ in range(25):
        mid = (lo + hi) / 2
        if SC.load(mid, P, A, ds, CUSH_REC)["Fm"] >= target: hi = mid
        else: lo = mid
    L = SC.load(hi, P, A, ds, CUSH_REC); idx = L["idx"]
    if len(idx) == 0: return dict(lost=True)
    Q, phi = SC.pose_at(hi, CV); pts = P[idx]; step = max(1, len(pts) // 12)
    strip = np.vstack([pts[::step], pts[-1:]])
    p = L["p"][idx] / 1000; pk = p[::step].tolist() + [float(p[-1])]
    return dict(lost=False, Q=np.round(Q, 4).tolist(), phi=round(float(phi), 1), strip=np.round(strip, 4).tolist(), p=np.round(pk, 1).tolist(),
                len_cm=round(100 * float(ds[idx].sum()), 1), a=[round(100 * float(A[idx].min()), 1), round(100 * float(A[idx].max()), 1)],
                p_max=round(float(p.max()), 1), sink_mm=round(1000 * float(L["sq"].max()), 1), bottom=L["bott"])

def anim_job(args):
    u, cv = args; ST.A_MAX = PAD_AMAX; sub, p = path_of(u); rows = track(sub, p, Seat(r_e=0.03), cv); fr = []
    for i in range(0, len(p), 3):
        pz = p[i]; r = rows[i] if i < len(rows) else None
        d = dict(f=round(pz["f"], 3), A=np.round(pz["A"], 3).tolist(), K=np.round(pz["K"], 3).tolist(), Hp=np.round(pz["Hp"], 3).tolist(),
                 tr=trunk_for(u, pz["Hp"][1], shank_deg(pz)))
        if r and r.get("contact") and r.get("ok"):
            k = min(int(r["k"]), len(cv[1]) - 1)
            d.update(seat=dict(Q=np.round(cv[1][k], 4).tolist(), phi=round(float(cv[2][k]), 1)), C=np.round(r["P"], 3).tolist(),
                     a=round(r["a"], 3), slip=round(r["slip"], 3), catch=round(r["catch"], 3), cush=cushion_patch(sub, pz, int(r["k"])))
        fr.append(d)
    return ukey(u), dict(L=[round(sub.L_shank, 3), round(sub.L_thigh, 3), round(sub.L_trunk, 3), round(sub.L_uarm, 3), round(sub.L_farm, 3)],
                         foot=round(sub.foot_len, 3), frames=fr)

def env_job(u):
    H, rb, p, xa = u; _, path = rise(H, xa, p, r_b=rb); q, Q, phi = curve_fit(path, V5.PHI_CAP)
    return ukey(u), dict(Q=np.round(Q[15:], 4).tolist(), phi=np.round(phi[15:], 2).tolist())

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
    sim, g = SL.simulate(SLJ["x"], 700); c1, c2 = np.array(SLJ["x"][:2]), np.array(SLJ["x"][2:4]); M = SLJ["mech"]
    cv = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim]))
    zs = [round(float(p[0][1]), 3) for p in sim]
    mech = dict(M, kind="slider", name="v5-slider", top=TOP, rail_lo=CK["rail"]["lo"], rail_hi=CK["rail"]["hi"], columns=CK["rail"]["columns"],
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
    SC.CVS[CUSH_REC[5]] = cv                  # the cushion solve runs on the same curve (and index) as the animation
    with Pool() as pool: AN = dict(pool.map(anim_job, [(u, cv) for u in USERS]))
    cs = [f["seat"] and f.get("cush") for a_ in AN.values() for f in a_["frames"] if "seat" in f]
    ok = [c for c in cs if c and not c["lost"]]
    print("cushion frames", len(cs), "lost", sum(1 for c in cs if c and c["lost"]), "len med", np.median([c["len_cm"] for c in ok]), "p med", np.median([c["p_max"] for c in ok]))
    with Pool() as pool: ENV = dict(pool.map(env_job, USERS))
    frames = []
    for fr in sim[::35] + [sim[-1]]:
        plate, br = LY.seat_polys(fr[0], fr[1], c1, c2)
        frames.append(dict(Q=np.round(fr[0], 4).tolist(), phi=round(float(fr[1]), 2), P1=np.round(fr[2], 4).tolist(), P2=np.round(fr[3], 4).tolist(),
                           plate=np.round(plate, 4).tolist(), bracket=np.round(br, 4).tolist()))
    b = CK["bed_floor_cm"]
    clear_rows = [["导轨（含滑块余量）", "床", "床头侧平面", b["导轨（含滑块余量）"], "全行程"], ["导轨立柱", "床", "床头侧平面", b["导轨立柱"], "固定件"],
                  ["座板、支架", "床", "全宽", min(b["座板（刚性部分）"], b["座板支架"]), "坐着时（座板后缘软唇边 4.5 cm 搭在床垫上）"],
                  ["倾角连杆", "床", "床头侧平面", b["倾角连杆"], "全行程"], ["全部零件", "地面", "全部", b["全部零件—地面"], "全行程"],
                  ["座板支架（全宽）", "小腿、脚", "全宽", CK["bracket_vs_legs_cm"]["min"], "81 人，按各自时刻"]]
    placements = {}
    for n, Vv in V5J["layouts"].items():
        m_ = Vv["mech"]; placements["v5-" + n] = dict(n_ok=Vv["summary"]["n_ok"], fwd_max=Vv["summary"]["fwd_max"], catch_min=Vv["summary"]["catch_min"],
                                                      centre_err_mm=m_["centre_err_mm"], phi_max=m_["phi_run_max"], bracket_mm=m_["bracket_depth_mm"],
                                                      force_kN=None if not m_["act"] else round(m_["act"]["F_hold100_N"] / 1000, 1), leg=Vv["summary"]["leg_clear_min"] if n == "mid" else None)
    placements["v5-slider"] = dict(n_ok=SLJ["summary"]["n_ok"], fwd_max=SLJ["summary"]["fwd_max"], catch_min=SLJ["summary"]["catch_min"], centre_err_mm=M["centre_err_mm"],
                                   phi_max=M["phi_run_max"], bracket_mm=mech["bracket_depth_mm"], force_kN=round(mech["F_hold100_N"] / 1000, 1), leg=None)
    page = dict(users=D["users"], assist=D["assist"], envelope=ENV, design_curve=dict(D["design_curve"], poses=V5J["design_curve"], phi_max=V5.PHI_CAP),
                consts=dict(D["consts"], top=TOP, phi_max=V5.PHI_CAP, pole=dict(x=0.69, z=[0.75, 1.10])), mech=mech, anim=AN,
                check=dict(design=users, vertical=D["check"]["vertical"]), shapes=dict(table=FB["table"]),
                cushion=dict(cushions=CU["cushions"], summary=CU["summary"], sitdown=CU["sitdown"]), placements=placements,
                layout=dict(frames=frames, clear_rows=clear_rows, pinch=CK["pinch_cm"], tipping=CK["tipping"], emergency=CK["emergency"], kind="slider", legs_worst=CK["bracket_vs_legs_cm"], bed_floor_cm=CK["bed_floor_cm"],
                            Y=dict(seat=0.22, rail=0.28, link=0.31, base=0.27), sizes=dict(PLATE_T=0.045, LIP=V5.LIP)))
    json.dump(page, open(os.path.join(OUT, "page.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s", {k: mech[k] for k in ("F_lift60_N", "F_lift100_N", "F_hold100_N")})
