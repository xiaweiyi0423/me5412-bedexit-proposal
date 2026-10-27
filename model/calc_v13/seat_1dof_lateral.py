"""Fall prevention step 1: sideways (frontal-plane) falls during the rise on the seat. A kill test, not a full analysis.

Question: during the rise, how much sideways disturbance does it take to fall toward the OPEN side (-y, nothing there) and
toward the HEAD side (+y, housing wall 3 cm from the seat edge, handrail post)? Which phase is weakest? Do two cheap fixes help?
  M1  extend the bar from y -0.05 to -0.25, so both hands can grip symmetrically about the body's midline;
  M2  a flip-down side guard on the seat's open side (y -0.24, 0.20 above the cushion, over the seat's rear 2/3).
Compared with sitting on a bed (0.42 / 0.58 m) for the seated phase. Also: how far the hip drops in a fall to the open side.

Method (quasi-static, frontal plane; a simplification - no stepping, no muscle response, no arm pull):
  * 81 users, slider curve, track rows as seat_1dof_handrail.user_eval. A frame is "seated" while i < len(good).
    Every 2nd frame: trunk angle and seat share from seat_trajectory.effort with the bar trunk filter (as bar_effort).
  * Sagittal COM (x, z) from the effort model's segments: head-trunk at Hp + r_headtrunk*uT; both arms at
    S + 0.45 (bar - S) (hands on the bar); thighs at Hp + 0.433 (K - Hp); shank+foot at the shank middle. y_COM = 0.
  * Base of support (BoS) in the floor plane = convex hull of: both feet, the buttock contact (while seated and the seat
    carries > 5 % BW) and, in the variants with hands, both hand points on the bar.
  * Lateral margin d = distance from the COM's ground projection to the hull edge along y at x = x_COM (open side: -y).
    Pendulum height l = z_COM - support height (seat contact height while seated, footplate top 0.047 after);
    v_crit = d * sqrt(g / l): the sideways COM speed that carries the extrapolated COM (Hof's XcoM) past the BoS edge.
    Larger v_crit = harder to push over. For a feel: a light nudge or a small stumble gives roughly 0.1-0.3 m/s.
Output: seat_1dof/lateral.json, seat_1dof/lateral.png
"""
import json, os, sys
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, ".."))
import seat_trajectory as ST
import seat_1dof_handrail as HR
import seat_1dof_fall_catch as FC
from seat_relative_motion import track
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
from seat_trajectory import rot
from model import G

OUT = os.path.join(HERE, "seat_1dof")
BAR = HR.bar_now(); BARP = np.array([BAR["x"], BAR["z"]])
HANDS = {"none": None, "current": (-0.04, 0.16), "M1": (-0.10, 0.10)}
FOOT_Y, FOOT_W = 0.06, 0.055; HIP_BR = 0.191
GUARD = dict(y=-0.24, h=0.20)
F_LAT, F_PULL = 0.10, 0.20        # hand forces as fractions of BW: sideways grip friction along the bar, pull on the bar (assumed)
WALL_Y, SEAT_EDGE = 0.25, 0.22
P = json.load(open(os.path.join(OUT, "parts.json"))); HOUSE = np.array(P["housing"]["outline_xz"])
NOTE = ("ASSUMPTIONS: feet centred at y = +-0.06 H, foot width 0.055 H, x from A - 0.25 L_foot to A + 0.75 L_foot; buttock contact "
        "x Hp +- 0.08, y +-(0.5 * 0.191 H - 0.02) while seated and the seat carries > 5 % BW; hands at x = bar x (0.70): current bar "
        "(y -0.05..0.30) -> hands at y -0.04 / +0.16 (20 cm apart, as far toward the open side as the bar allows), M1 (bar to -0.25) "
        "-> -0.10 / +0.10; arms' COM at 45 % of the shoulder-to-bar line; y_COM = 0 (symmetric posture). Margin and v_crit are "
        "quasi-static (extrapolated-COM criterion); hand points in the BoS assume the hands can take load (upper bound), "
        "'none' is the lower bound. Hands as forces (variants *_force): a sideways grip force 0.10 BW at bar height and a pull 0.20 BW "
        "applied at the hands' mean y let the COM go past the feet edge by e = (0.10 (z_bar - z_support) + 0.20 * lever) BW / BW; the "
        "lever is from the tipping edge (outer edge of the foot on the falling side) to the hands' mean y. These hand forces are guesses "
        "(elderly grip about 150-200 N per hand; reaction time not modelled).")

def hull(pts):
    pts = sorted(set(map(tuple, np.round(pts, 5))))
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in pts[::-1]:
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return np.array(lo[:-1] + up[:-1])

def y_span(H, x):
    """y range of convex polygon H (x, y) at abscissa x; None if x outside."""
    ys = []
    for i in range(len(H)):
        a, b = H[i], H[(i + 1) % len(H)]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]:
            t = (x - a[0]) / (b[0] - a[0]); ys.append(a[1] + t * (b[1] - a[1]))
        elif a[0] == x: ys.append(a[1])
    return (min(ys), max(ys)) if ys else None

def feet_pts(sub, A):
    L = sub.foot_len; w = FOOT_W * sub.H; c = FOOT_Y * sub.H; x0, x1 = A[0] - 0.25 * L, A[0] + 0.75 * L; out = []
    for s in (-1, 1):
        for x in (x0, x1):
            for dy in (-w / 2, w / 2): out.append((x, s * c + dy))
    return out

def seat_pts(sub, Hp):
    hw = 0.5 * HIP_BR * sub.H - 0.02; return [(Hp[0] + dx, s * hw) for dx in (-0.08, 0.08) for s in (-1, 1)]

def com(sub, pz, th, arms="bar"):
    Hp, K, A = pz["Hp"], pz["K"], pz["A"]; uT = np.array([np.sin(np.radians(th)), np.cos(np.radians(th))]); S = Hp + sub.L_trunk * uT
    arm_c = S + 0.45 * (BARP - S) if arms == "bar" else S + np.array([0.0, -0.30])
    segs = [(Hp + sub.r_headtrunk * uT, sub.m_headtrunk), (arm_c, 2 * (sub.m_uarm + sub.m_farm)), (Hp + 0.433 * (K - Hp), 2 * sub.m_thigh),
            (A + 0.5 * (K - A), 2 * sub.m_shank_foot)]
    m = sum(w for _, w in segs); c = sum(p * w for p, w in segs) / m; return c, S

def effort_full(sub, pz, contact):
    tr = HR.ok_trunks(sub, pz, BARP)
    if not tr: return None
    old = ST.TRUNKS; ST.TRUNKS = tr
    try: return ST.effort(sub, pz, BARP, contact) if contact is not None else ST.effort(sub, pz, BARP)
    finally: ST.TRUNKS = old

def housing_top(x):
    zs = []
    for i in range(len(HOUSE)):
        a, b = HOUSE[i], HOUSE[(i + 1) % len(HOUSE)]
        if (a[0] - x) * (b[0] - x) <= 0 and a[0] != b[0]: zs.append(a[1] + (x - a[0]) / (b[0] - a[0]) * (b[1] - a[1]))
    return max(zs) if zs else None

def margins(sub, pz, c, seated, f_seat, z_sup, hands):
    pts = feet_pts(sub, pz["A"])
    if seated and f_seat > 0.05: pts += seat_pts(sub, pz["Hp"])
    if hands: pts += [(BARP[0], hands[0]), (BARP[0], hands[1])]
    Hh = hull(np.array(pts)); sp = y_span(Hh, c[0])
    if sp is None: return None
    l = max(c[1] - z_sup, 0.05); w0 = np.sqrt(G / l)
    return dict(d_open=-sp[0], d_head=sp[1], v_open=-sp[0] * w0, v_head=sp[1] * w0, l=l)

def user_job(u):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u); cv = HR.slider_cv()
    rows = track(sub, path, ST.Seat(r_e=0.03), cv); good = [r for r in rows if r.get("contact") and r.get("ok")]; ng = len(good)
    frames = []
    for i in range(0, len(path), 2):
        pz = path[i]; seated = i < ng
        if seated:
            r = rows[i]; k = min(int(r["k"]), len(cv[1]) - 1); n_ = rot(cv[2][k]) @ np.array([0, 1.0])
            res = effort_full(sub, pz, (np.array(r["P"]), n_, r["pelvis"])); z_sup = float(r["P"][1])
        else:
            res = effort_full(sub, pz, None); z_sup = 0.047
        if res is None: continue
        E, th, fs = res; c, S = com(sub, pz, th)
        fr = dict(i=i, f=round(float(pz["f"]), 3), seated=seated, th=th, f_seat=round(fs, 3), com=np.round(c, 3).tolist(), hip_z=round(float(pz["Hp"][1]), 3),
                  shoulder=np.round(S, 3).tolist())
        for hv, hands in HANDS.items():
            m = margins(sub, pz, c, seated, fs, z_sup, hands)
            if m: fr[hv] = {k: round(float(v), 3) for k, v in m.items()}
        if "none" in fr:                                    # hands as FORCES (they do not widen the BoS: they sit inside the feet laterally)
            ye = FOOT_Y * sub.H + FOOT_W * sub.H / 2; w0 = np.sqrt(G / fr["none"]["l"])
            for hv in ("current", "M1"):
                yc = float(np.mean(HANDS[hv])); arm = BARP[1] - z_sup
                e_open = F_LAT * arm + F_PULL * max(yc + ye, 0.0); e_head = F_LAT * arm + F_PULL * max(ye - yc, 0.0)
                fr[hv + "_force"] = dict(v_open=round((fr["none"]["d_open"] + e_open) * w0, 3), v_head=round((fr["none"]["d_head"] + e_head) * w0, 3),
                                         e_open=round(e_open, 3), e_head=round(e_head, 3))
        if seated:                                          # M2: guard stops the pelvis at y -0.24; toppling over its top edge
            lg = c[1] - (z_sup + GUARD["h"]); fr["M2_v_open"] = None if lg <= 0.02 else round(abs(GUARD["y"]) * np.sqrt(G / lg), 3)
            fr["M2_cant_topple"] = bool(lg <= 0.02)
        ht = housing_top(S[0]); fr["head_wall"] = dict(housing_top=None if ht is None else round(ht, 3), shoulder_below_top=bool(ht is not None and S[1] <= ht),
                                                      hip_in_housing_x=bool(HOUSE[:, 0].min() <= pz["Hp"][0] <= HOUSE[:, 0].max()))
        frames.append(fr)
    # end-of-rise standing, hands off (feet only)
    pz = path[-1]; res = effort_full(sub, pz, None)
    stand = None
    if res:
        c, S = com(sub, pz, res[1], arms="side"); m = margins(sub, pz, c, False, 0.0, 0.047, None); stand = {k: round(float(v), 3) for k, v in m.items()} if m else None
    # bed baselines (seated on the bed edge, trunk 15 deg, arms at the side; buttocks + feet, no handrail)
    beds = {}
    for bed in (0.42, 0.58):
        bp = FC.bed_path(u[0], u[3], u[2], 0.0, bed + u[1])
        if not bp: beds[str(bed)] = None; continue
        q = bp[0]; c, S = com(sub, q, 15.0, arms="side"); m = margins(sub, q, c, True, 1.0, bed, None)
        beds[str(bed)] = None if m is None else dict({k: round(float(v), 3) for k, v in m.items()}, hip_drop=round(float(q["Hp"][1]) - 0.10, 3))
    return ukey(u), dict(frames=frames, n_seated=ng, stand_feet_only=stand, bed=beds)

def summarize(R):
    pct = lambda a, q: round(float(np.percentile(a, q)), 3) if len(a) else None
    S = dict(n_users=len(R))
    for hv in list(HANDS) + ["current_force", "M1_force"]:
        for side in ("open", "head"):
            for ph, sel in (("seated", True), ("after_release", False)):
                mins, fs, hz = [], [], []
                for k, r in R.items():
                    fr = [x for x in r["frames"] if x["seated"] == sel and hv in x]
                    if not fr: continue
                    j = min(fr, key=lambda x: x[hv]["v_" + side]); mins.append(j[hv]["v_" + side]); fs.append(j["f"]); hz.append(j["hip_z"])
                S[f"{hv}_{side}_{ph}"] = dict(v_crit_min_med=pct(mins, 50), v_crit_min_p10=pct(mins, 10), v_crit_min_min=pct(mins, 0), f_at_min_med=pct(fs, 50),
                                               hip_z_at_min_med=pct(hz, 50), n=len(mins))
    # margins at the start (seated on our seat, flush) vs the bed
    st0, b42, b58, sf = [], [], [], []
    for r in R.values():
        fr = [x for x in r["frames"] if x["seated"] and "none" in x]
        if fr: st0.append(fr[0]["none"]["v_open"])
        if r["bed"].get("0.42"): b42.append(r["bed"]["0.42"]["v_open"])
        if r["bed"].get("0.58"): b58.append(r["bed"]["0.58"]["v_open"])
        if r["stand_feet_only"]: sf.append(r["stand_feet_only"]["v_open"])
    S["start_seated_vs_bed"] = dict(seat_flush_no_hands_v_med=pct(st0, 50), bed042_v_med=pct(b42, 50), bed058_v_med=pct(b58, 50), n_bed058=len(b58),
                                    standing_feet_only_v_med=pct(sf, 50), standing_feet_only_v_p10=pct(sf, 10))
    # M2 (seated only)
    m2, cant = [], 0; ntot = 0
    for r in R.values():
        fr = [x for x in r["frames"] if x["seated"]]
        for x in fr:
            ntot += 1; cant += x.get("M2_cant_topple", False)
        v = [x["M2_v_open"] for x in fr if x.get("M2_v_open") is not None]
        if v: m2.append(min(v))
    S["M2_guard_seated"] = dict(frames_cannot_topple_share=round(cant / max(ntot, 1), 3), v_crit_min_med_where_topple_possible=pct(m2, 50), n_users_with_topple_possible=len(m2))
    # hip drop to the open side
    drop_max, drop_rel = [], []
    for r in R.values():
        fr = [x for x in r["frames"] if x["seated"]]
        if fr: drop_max.append(max(x["hip_z"] for x in fr) - 0.10)
        fa = [x for x in r["frames"] if "current" in x]
        if fa: j = min(fa, key=lambda x: x["current"]["v_open"]); drop_rel.append(j["hip_z"] - 0.10)
    bd42 = [r["bed"]["0.42"]["hip_drop"] for r in R.values() if r["bed"].get("0.42")]; bd58 = [r["bed"]["0.58"]["hip_drop"] for r in R.values() if r["bed"].get("0.58")]
    v = lambda h: round(float(np.sqrt(2 * G * h)), 2)
    S["hip_drop_open_side"] = dict(seated_max_med=pct(drop_max, 50), seated_max_max=pct(drop_max, 100), at_weakest_current_med=pct(drop_rel, 50),
                                   bed042_med=pct(bd42, 50), bed058_med=pct(bd58, 50),
                                   impact_speed_mps=dict(seated_max_med=v(pct(drop_max, 50)), bed042=v(pct(bd42, 50)), bed058=v(pct(bd58, 50)) if bd58 else None))
    # head side: does the housing stop a fall to +y?
    sh_ok, hip_ok, n = 0, 0, 0
    for r in R.values():
        for x in r["frames"]:
            n += 1; sh_ok += x["head_wall"]["shoulder_below_top"]; hip_ok += x["head_wall"]["hip_in_housing_x"]
    S["head_side_housing"] = dict(frames=n, shoulder_below_housing_top_share=round(sh_ok / max(n, 1), 3), hip_x_within_housing_share=round(hip_ok / max(n, 1), 3),
                                  wall_gap_m=round(WALL_Y - SEAT_EDGE, 3))
    return S

def bar_check():
    F = 1.5 * 1112.0; L = 0.55; E = 210e9; out = {}
    for nm, D, t in (("Ø38×4", 0.038, 0.004), ("Ø42.4×3.2", 0.0424, 0.0032), ("Ø42.4×4", 0.0424, 0.004), ("Ø48.3×3.2", 0.0483, 0.0032)):
        d = D - 2 * t; I = np.pi * (D ** 4 - d ** 4) / 64; Z = I / (D / 2); s = F * L / Z; tip = F * L ** 3 / (3 * E * I)
        out[nm] = dict(stress_MPa=round(s / 1e6), allow_MPa=237, ok=bool(s / 1e6 <= 237), bar_tip_mm=round(1000 * tip, 1))
    bt = 0.06; ti = 0.004; Am = (bt - ti) ** 2; Ip = (bt ** 4 - (bt - 2 * ti) ** 4) / 12; Zp = Ip / (bt / 2)
    sig = F * (0.95 - 0.035) / Zp; tau = F * L / (2 * Am * ti); out["post_60x60x4"] = dict(vm_MPa=round(float(np.sqrt(sig ** 2 + 3 * tau ** 2)) / 1e6), tau_MPa=round(tau / 1e6, 1))
    return dict(load_N=round(F), cantilever_m=L, sections=out)

def figure(R, path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False
    fbins = np.linspace(0, 1, 21); fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    V = [("none", "不算手", "#6B7480"), ("current_force", "现横杆，双手出力", "#B3261E"), ("M1_force", "横杆加长到 −0.25，双手出力", "#1E5AA8")]
    for hv, lb, col in V:
        for side, ls in (("open", "-"), ("head", "--")):
            if hv == "none" and side == "head": continue
            med = []
            for a, b in zip(fbins[:-1], fbins[1:]):
                v = [x[hv]["v_" + side] for r in R.values() for x in r["frames"] if hv in x and a <= x["f"] < b]
                med.append(np.median(v) if v else np.nan)
            axs[0].plot((fbins[:-1] + fbins[1:]) / 2, med, ls, color=col, lw=2 if side == "open" else 1.2, label=f"{lb}，{'敞开侧' if side == 'open' else '床头侧'}")
    med = []
    for a, b in zip(fbins[:-1], fbins[1:]):
        v = [x["M2_v_open"] for r in R.values() for x in r["frames"] if x["seated"] and x.get("M2_v_open") is not None and a <= x["f"] < b]
        med.append(min(np.median(v), 3.0) if v else np.nan)
    axs[0].plot((fbins[:-1] + fbins[1:]) / 2, med, ":", color="#2E7D4F", lw=2, label="敞开侧加挡板（只在坐着时有效）")
    axs[0].set_xlabel("起身进度 f（0 坐着 → 1 站直）"); axs[0].set_ylabel("把人推倒所需的侧向速度 v_crit（m/s），中位"); axs[0].axhline(0.2, color="#999", lw=0.8, ls=":")
    axs[0].text(0.01, 0.21, "约 0.2 m/s：轻推 / 小踉跄", fontsize=8, color="#666"); axs[0].legend(fontsize=7); axs[0].set_ylim(0, None); axs[0].grid(alpha=0.25)
    hz = []
    for a, b in zip(fbins[:-1], fbins[1:]):
        v = [x["hip_z"] - 0.10 for r in R.values() for x in r["frames"] if a <= x["f"] < b]; hz.append(np.median(v) if v else np.nan)
    axs[1].plot((fbins[:-1] + fbins[1:]) / 2, hz, color="#1A2430", lw=2, label="座板（往敞开侧倒时髋部下落高度）")
    for bed, c_ in ((0.42, "#2E7D4F"), (0.58, "#9A5408")):
        v = [r["bed"][str(bed)]["hip_drop"] for r in R.values() if r["bed"].get(str(bed))]
        if v: axs[1].axhline(np.median(v), color=c_, ls="--", label=f"坐在 {bed:.2f} m 床边")
    axs[1].set_xlabel("起身进度 f"); axs[1].set_ylabel("髋部下落高度（m），中位"); axs[1].legend(fontsize=8); axs[1].grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(path, dpi=150)

if __name__ == "__main__":
    with Pool() as p: R = dict(p.map(user_job, USERS))
    S = summarize(R)
    out = dict(note=__doc__, assumptions=NOTE, bar=BAR, hands=HANDS, guard=GUARD, summary=S, bar_extension_check=bar_check(),
               users={k: dict(n_seated=v["n_seated"], stand_feet_only=v["stand_feet_only"], bed=v["bed"],
                              weakest_open_current=min((x for x in v["frames"] if "current" in x), key=lambda x: x["current"]["v_open"], default=None))
                      for k, v in R.items()})
    json.dump(out, open(os.path.join(OUT, "lateral.json"), "w"), ensure_ascii=False, indent=1, default=float)
    figure(R, os.path.join(OUT, "lateral.png"))
    print(json.dumps(S, ensure_ascii=False, indent=1)); print(json.dumps(out["bar_extension_check"], ensure_ascii=False))
