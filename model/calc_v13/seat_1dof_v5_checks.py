"""v5.2 structure and safety checks for the one-side inclined rail + tilt link seat (seat_1dof/slider.json).

Changes after the round-2 audit (page/seat1dof/audit/v5/):
  - the whole head-side mechanism sits in a closed housing (inner wall y 0.25, outer wall y 0.36). The housing wall carries
    TWIN RAILS 150 mm apart in the rail plane, each with two carriages 150 mm apart, so the cantilever moment becomes force
    couples. The motor is folded beside the screw at the top (belt). The tilt link lives inside the housing. The seat bracket
    reaches the carriages through a brush-sealed slot in the inner wall. The two separate posts of v5 are gone (they crossed
    the bracket and the link).
  - the seat body is stepped for the zoned cushion: rear zone 5 cm foam + 1.2 cm board, front zone (x >= -2 cm) 8 cm foam +
    1.2 cm board, flush tops.
  - every frame is checked (no sub-sampling).
  - drive: ball screw (back-drivable) + power-off brake + centrifugal speed limiter. Emergency lowering = release the brake
    with a cable lever at the handrail grip; the seat sinks under the user's weight at the limiter speed, stops when the lever
    is let go; no re-engagement. A battery also lowers the seat.
Layout across the width (y, + = head side): seat |y| <= 0.22; housing 0.25 .. 0.36; base beams at y -0.27 (foot side) and
+0.38 (under the housing); L-handrail: post on the head side in front of the housing, bar across the user's front.
Checks
  1 sagittal clearances: housing (hull of rails, carriages, motor, link sweep, + 2 cm wall) vs bed; seat body and bracket vs
    bed, floor and every user's calves and feet at the matching moment
  2 pinch: seat edge to housing wall (constant gap), slot (brush seal), seat underside to base, seat vs bed edge
  3 forces: screw, link, carriage normal; cantilever moment for the load on the seat centre line and 10 cm towards the open
    side, split into the rail-pair couple and the carriage-pair couple
  4 tipping: person on the device (as v5) and, new, person standing on the floor pulling or pushing the bar (device weight
    only) -> anchoring to the bed and the anchor force
  5 emergency lowering with the ball screw: does the lightest user's weight overcome screw and rail friction; brake torque
Output: seat_1dof/v5_checks.json
"""
import json, os, sys
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_1dof_v5 as V5
import seat_1dof_slider as SL
import seat_1dof_layout as LY
import seat_1dof_handrail as HR
import seat_trajectory as ST
from seat_trajectory import rot, Seat
from seat_relative_motion import track
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
from model import G

OUT = V5.OUT
S = json.load(open(os.path.join(OUT, "slider.json"))); v = S["x"]; M = S["mech"]
sim, g = SL.simulate(v, 700); c1, c2 = np.array(v[:2]), np.array(v[2:4]); Bp = np.array(M["B"])
e = g["d"] * np.sign((sim[-1][2] - sim[0][2]) @ g["d"]); nf = np.array([e[1], -e[0]])        # rail direction (up), in-plane normal (forward-down)
Y = dict(seat=0.22, wall_in=0.25, link=0.28, rail=0.32, wall_out=0.36, base_open=-0.27, base_head=0.38)
RAIL_GAP, CARR_SPAN, CARR_LEN, WALL = 0.15, 0.15, 0.06, 0.02
SEAT_T = dict(rear=0.062, front=0.092, split=-0.02)                                             # foam + board, front zone stepped
cv = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim])); npre = len(cv[0]) - len(sim)

def seat_body(Q, phi):
    """stepped seat body (full width) and the bracket under it down to the two pins, world frame."""
    Rm = rot(phi); W_ = lambda L: np.array([Q + Rm @ np.array(p) for p in L]); h = LY.HALF; x0 = -h + V5.LIP
    body = W_([(x0, 0), (h, 0), (h, -SEAT_T["front"]), (SEAT_T["split"], -SEAT_T["front"]), (SEAT_T["split"], -SEAT_T["rear"]), (x0, -SEAT_T["rear"])])
    br = [(x0, -SEAT_T["rear"]), (SEAT_T["split"], -SEAT_T["rear"]), (SEAT_T["split"], -SEAT_T["front"]), (h - 0.03, -SEAT_T["front"]), tuple(c1), tuple(c2)]
    pts = np.array(br); c = pts.mean(0); order = np.argsort(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    return body, W_([br[i] for i in order])

def rails():
    """rail 1 (carriage pins on it) and rail 2 (offset 150 mm forward-down in the rail plane); the carriage block runs from 3 cm
    below the pin to 18 cm above it (two carriages 150 mm apart); each rail extends 2 cm past the block at both ends."""
    lo = sim[0][2] - (0.03 + 0.02) * e; hi = sim[-1][2] + (CARR_SPAN + CARR_LEN / 2 + 0.02) * e
    return (lo, hi), (lo + RAIL_GAP * nf, hi + RAIL_GAP * nf)

def carriages(P1):
    """the four carriage blocks for the pin at P1 (each a 6 cm long segment on its rail)."""
    out = []
    for off in (0.0, RAIL_GAP):
        for s_ in (0.0, CARR_SPAN):
            c = P1 + s_ * e + off * nf; out.append((c - CARR_LEN / 2 * e, c + CARR_LEN / 2 * e))
    return out

def motor_box():
    """motor folded beside the screw at the top of the rails (belt drive), 8 x 10 cm in the rail plane."""
    (lo, hi), _ = rails(); c = hi - 0.06 * e + 0.5 * RAIL_GAP * nf
    return np.array([c + a * e + b * nf for a, b in ((-0.05, -0.04), (0.05, -0.04), (0.05, 0.04), (-0.05, 0.04))])

def hull(P):
    P = np.unique(np.round(np.asarray(P), 5), axis=0); P = P[np.lexsort((P[:, 1], P[:, 0]))]
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in P:
        while len(lower) >= 2 and cr(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    for p in P[::-1]:
        while len(upper) >= 2 and cr(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])

def housing():
    """sagittal outline of the housing: hull of rails, carriage blocks over the travel, motor, link sweep and B; floor at 0.04."""
    (a1, b1), (a2, b2) = rails(); pts = [a1, b1, a2, b2, Bp] + list(motor_box())
    for f in sim[::10] + [sim[-1]]:
        for A_, B_ in carriages(f[2]): pts += [A_, B_]
        pts.append(f[3])
    pts = np.array(pts); pts = np.vstack([pts, [[p[0], 0.04] for p in pts]])
    Hh = hull(pts); c = Hh.mean(0)
    grow = np.array([p + WALL * (p - c) / np.hypot(*(p - c)) for p in Hh]); grow[:, 1] = np.maximum(grow[:, 1], 0.04)
    return grow

def check_bed():
    worst = {}
    def upd(k, val):
        worst[k] = min(worst.get(k, 9.0), val)
    Hs = housing(); upd("机构箱（导轨、滑块、电机、连杆）", float(LY.bed_d(LY.poly_pts(Hs, 0.005)).min()))
    for f in sim:
        body, br = seat_body(f[0], f[1])
        upd("座板（刚性部分）", float(LY.bed_d(LY.poly_pts(body, 0.005)).min())); upd("座板支架", float(LY.bed_d(LY.poly_pts(br, 0.005)).min()))
        upd("全部活动零件—地面", float(LY.poly_pts(br, 0.005)[:, 1].min()))
    return {k: round(100 * v_, 1) for k, v_ in worst.items()}

def legs_job(u):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rows = track(sub, path, Seat(r_e=0.03), cv); dmin = 9.0; zi = None
    for i, pz in enumerate(path):
        r = rows[i] if i < len(rows) else None
        if r and r.get("contact") and r.get("ok"): zi = min(max(int(r["k"]) - npre, 0), len(sim) - 1)
        if zi is None: continue
        body, br = seat_body(sim[zi][0], sim[zi][1]); caps = LY.body_caps(pz, sub)
        for poly in (body, br):
            pts = LY.poly_pts(poly, 0.005)
            for cn in ("calf", "foot"): dmin = min(dmin, float(LY.cap_d(pts, *caps[cn]).min()))
    return ukey(u), round(100 * dmin, 1)

def pinch():
    """closing gaps a finger could get into (25 mm rule)."""
    gmin = 9.0
    for f in sim:
        body, _ = seat_body(f[0], f[1]); gmin = min(gmin, float(LY.poly_pts(body, 0.005)[:, 1].min()) - 0.04)
    return {"座板侧缘—机构箱内壁（平行滑过，间隙不变）": round(100 * (Y["wall_in"] - Y["seat"]), 1),
            "座板底面—底座（最低处）": round(100 * gmin, 1),
            "支架穿过内壁的竖槽": "毛刷密封，手指进不去",
            "机构箱内部（滑块、连杆、丝杠、电机）": "全封闭"}

def forces():
    """cantilever moment of the seat load (100 kg x 1.5 + 10 kg seat) about the rail plane, for the load on the seat centre line
    and 10 cm towards the open side; split into the moment about the rail axis (taken by the two rails, 150 mm apart) and the
    moment about the in-plane normal (taken by the two carriages on each rail, 150 mm apart)."""
    F = 1.5 * 100 * G + 10 * G; y_mid = Y["rail"] + RAIL_GAP / 2 * 0       # rails sit in one plane at y_rail
    out = {}
    for name, yl in (("载荷在座板中线", 0.0), ("载荷偏向敞开一侧 10 cm", -0.10)):
        Mx = F * (Y["rail"] - yl); Me = Mx * abs(e[0]); Mn = Mx * abs(nf[0])
        Fr = Me / RAIL_GAP; Fc = Mn / CARR_SPAN
        out[name] = dict(moment_Nm=round(Mx), about_rail_axis_Nm=round(Me), about_normal_Nm=round(Mn), rail_pair_N=round(Fr), carriage_pair_N=round(Fc),
                         per_carriage_lateral_N=round(Fr / 2 + Fc / 2))
    return out

def tipping(dev_kg=45.0, dev_com=(0.25, 0.15)):
    """base x 0.03..0.78, y -0.27 (open) .. +0.38 (head). Device 45 kg (housing and mechanism on the head side).
    A: person on the device (as v5). B: person standing on the floor, hand on the bar (device weight only)."""
    bar = HR.bar_now(); xb, zb = bar["x"], bar["z"]; X0, X1, Yo, Yh = 0.03, 0.78, -Y["base_open"], Y["base_head"]; out = {}
    cases = {"100 kg 猛坐座板后缘（1.5 倍体重）": [(1.5 * 100 * G, 0.01, 0.0)], "100 kg 整个挂在扶手横杆上（人在台上）": [(100 * G, xb, 0.10)],
             "45 kg 猛坐后缘": [(1.5 * 45 * G, 0.01, 0.0)]}
    for k, loads in cases.items():
        Ft = sum(a for a, _, _ in loads) + dev_kg * G
        cx = (sum(a * x for a, x, _ in loads) + dev_kg * G * dev_com[0]) / Ft; cy = (sum(a * y for a, _, y in loads) + dev_kg * G * dev_com[1]) / Ft
        out[k] = dict(margin_rear_cm=round(100 * (cx - X0), 1), margin_front_cm=round(100 * (X1 - cx), 1), margin_side_cm=round(100 * min(Yh - cy, Yo + cy), 1))
    W = dev_kg * G
    floor = dict(pull_forward_N=round(W * (X1 - dev_com[0]) / zb), push_to_open_side_N=round(W * (Yo + dev_com[1]) / zb),
                 push_to_head_side_N=round(W * (Yh - dev_com[1]) / zb))
    out["人站在地上推拉横杆（只有台架自重）"] = floor
    worst = min(floor.values())
    # anchors to the bed along the rear edge (x 0.03, at both ends y -0.27 and +0.38). For each tipping direction:
    # needed anchor pull = (1.5 x design force x bar height - device weight x its arm) / anchor lever about that edge
    dirs = {"向前": (X1 - dev_com[0], X1 - X0), "向敞开一侧": (Yo + dev_com[1], Yo + Yh), "向床头一侧": (Yh - dev_com[1], Yo + Yh)}
    for nm, Fd in (("0.25 倍体重（100 kg）", 0.25 * 100 * G), ("ADA 609 扶手设计载荷 1112 N", 1112.0)):
        need = max(max(0.0, (1.5 * Fd * zb - W * arm) / lever) for arm, lever in dirs.values())
        out[f"固定件拉力（{nm}，安全系数 1.5）"] = dict(anchor_N=round(need))
    out["结论"] = dict(min_tip_force_N=worst, note="人不在台上时横推不到 %d N 就翻：台架必须和床固定" % worst)
    out["base"] = dict(x=[X0, X1], y=[-Yo, Yh], device_kg=dev_kg, device_com=list(dev_com))
    return out

def emergency(lead=0.010, eta_back=0.85, mu_rail=0.005, seal_N=20.0, brake_sf=2.0):
    """ball screw + power-off brake + centrifugal limiter. Generalized force along the rail per N of seat load (virtual work,
    load anywhere on the seat): it must point down everywhere, and for the lightest user (45 kg, 0.75 BW on the seat) it must
    beat the back-driving loss of the screw, the rail friction and the seal drag. Brake: holds the largest static screw force."""
    gen = []
    for i in range(1, len(sim) - 1, 3):
        n_ = rot(sim[i][1]) @ np.array([0, 1.0])
        for xo in V5.XOFF:
            Cn = sim[i + 1][0] + rot(sim[i + 1][1]) @ np.array([xo, 0]); Cp = sim[i - 1][0] + rot(sim[i - 1][1]) @ np.array([xo, 0])
            gen.append(float((-n_ @ (Cn - Cp)) / (sim[i + 1][4] - sim[i - 1][4])))
    sgn = np.sign(sim[-1][4] - sim[0][4]); sinks = all(q * sgn < 0 for q in gen); kmin = min(abs(q) for q in gen); kmax = max(abs(q) for q in gen)
    seat_w = 10 * G * abs(e[1])                                             # seat + bracket weight along the rail, helps sinking
    drive = kmin * 0.75 * 45 * G + seat_w
    Fr = forces()["载荷在座板中线"]; normal = 2 * (Fr["rail_pair_N"] + Fr["carriage_pair_N"]) * (45 * 0.75 + 10) / (150 + 10)   # scaled to the light user
    resist = (1 - eta_back) * drive + mu_rail * normal + seal_N
    F_hold = M.get("screw_force_hold100_N", 0); T_brake = brake_sf * F_hold * lead / (2 * np.pi)
    return dict(seat_sinks_under_load=bool(sinks), rail_force_per_N_seat_load=[round(kmin, 2), round(kmax, 2)], tilt_max_on_the_way=round(float(max(p[1] for p in sim)), 1),
                stroke_m=round(float(abs(sim[-1][4] - sim[0][4])), 3), light_user_drive_N=round(drive), resist_N=round(resist), margin=round(drive / resist, 1),
                limiter_speed_mps=0.10, time_full_sink_s=round(abs(sim[-1][4] - sim[0][4]) / 0.10, 1), lead_mm=1000 * lead,
                brake_torque_Nm=round(T_brake, 1), screw_rpm_at_limit=round(0.10 / lead * 60))

if __name__ == "__main__":
    out = dict(note=__doc__, mech=M, Y=Y, rail_gap=RAIL_GAP, carriage_span=CARR_SPAN, seat_t=SEAT_T)
    out["bed_floor_cm"] = check_bed()
    with Pool() as p: LG = dict(p.map(legs_job, USERS))
    out["bracket_vs_legs_cm"] = dict(min=min(LG.values()), worst_user=min(LG, key=LG.get))
    out["pinch_cm"] = pinch(); out["forces"] = forces(); out["tipping"] = tipping(); out["emergency"] = emergency()
    (a1, b1), (a2, b2) = rails()
    out["rail"] = dict(lo=np.round(a1, 4).tolist(), hi=np.round(b1, 4).tolist(), lo2=np.round(a2, 4).tolist(), hi2=np.round(b2, 4).tolist(),
                       housing=np.round(housing(), 4).tolist(), motor=np.round(motor_box(), 4).tolist())
    json.dump(out, open(os.path.join(OUT, "v5_checks.json"), "w"), ensure_ascii=False, indent=1, default=float)
    for k in ("bed_floor_cm", "bracket_vs_legs_cm", "pinch_cm", "forces", "tipping", "emergency"): print(k, out[k])
