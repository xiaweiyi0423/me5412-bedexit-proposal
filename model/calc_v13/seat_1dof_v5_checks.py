"""v5 checks for the one-side inclined rail + tilt link seat (seat_1dof/slider.json).

Layout across the width (y, seat centre line y = 0; + = head-of-bed side):
  head side  (+y) rail and its side column at y = +0.26..+0.30, tilt link at y = +0.31, link pivot B on the side base rail;
             handrail pole at x 0.69 on this side
  foot side  (-y) open: only the floor rail (4 cm high) - this is where the legs swing back onto the bed
  full width seat plate + seat frame (bracket) under the seat, cantilevered from the carriage
Checks
  1 sagittal interference over the travel: rail (with carriage), column, link, seat plate, bracket vs bed and floor;
    full-width parts (plate, bracket) vs every user's calves and feet at the matching moment
  2 pinch gaps (closing gaps under 25 mm = finger risk): link vs seat/bracket, link vs rail column, seat underside vs base
  3 forces: lead screw, link, carriage normal force and the out-of-plane moment from the cantilever (100 kg, 1.5 BW)
  4 tipping with the mechanism mass on one side
  5 emergency lowering after a quick release: does the seat sink under load everywhere, tilt on the way, damper size
  6 leg swing to the open side
Output: seat_1dof/v5_checks.json
"""
import json, os, sys
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_1dof_v5 as V5
import seat_1dof_slider as SL
import seat_1dof_layout as LY
import seat_trajectory as ST
from seat_trajectory import rot, Seat
from seat_relative_motion import track
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
from model import G

OUT = V5.OUT
S = json.load(open(os.path.join(OUT, "slider.json"))); v = S["x"]; M = S["mech"]
sim, g = SL.simulate(v, 700); c1, c2 = np.array(v[:2]), np.array(v[2:4]); Bp = np.array(M["B"])
d = g["d"] * np.sign((sim[-1][2] - sim[0][2]) @ g["d"])
RAIL = (sim[0][2] - 0.06 * d, sim[-1][2] + 0.06 * d)
COLUMN = [(np.array([RAIL[0][0], 0.04]), RAIL[0]), (np.array([RAIL[1][0] + 0.05, 0.04]), RAIL[1])]     # two posts under the rail ends
cv = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim])); npre = len(cv[0]) - len(sim)

def frame_parts(f):
    plate, br = LY.seat_polys(f[0], f[1], c1, c2)
    return plate, br, (Bp, f[3])

def check_bed():
    worst = {}
    def upd(k, val):
        worst[k] = min(worst.get(k, 9.0), val)
    upd("导轨（含滑块余量）", float(LY.bed_d(LY.seg_pts(*RAIL, 40)).min()) - 0.02)
    for i, (X, Y_) in enumerate(COLUMN): upd("导轨立柱", float(LY.bed_d(LY.seg_pts(X, Y_, 20)).min()) - 0.025)
    for f in sim[::5]:
        plate, br, link = frame_parts(f)
        upd("座板（刚性部分）", float(LY.bed_d(LY.poly_pts(plate, 0.005)).min())); upd("座板支架", float(LY.bed_d(LY.poly_pts(br, 0.005)).min()))
        upd("倾角连杆", float(LY.bed_d(LY.seg_pts(*link, 20)).min()) - 0.02)
        upd("全部零件—地面", min(float(LY.poly_pts(br, 0.005)[:, 1].min()), float(min(link[0][1], link[1][1])) - 0.02))
    return {k: round(100 * v_, 1) for k, v_ in worst.items()}

def legs_job(u):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rows = track(sub, path, Seat(r_e=0.03), cv); dmin = 9.0; zi = None
    for i, pz in enumerate(path):
        r = rows[i] if i < len(rows) else None
        if r and r.get("contact") and r.get("ok"): zi = min(max(int(r["k"]) - npre, 0), len(sim) - 1)
        if zi is None: continue
        plate, br, _ = frame_parts(sim[zi]); caps = LY.body_caps(pz, sub); pts = LY.poly_pts(br, 0.005)
        for cn in ("calf", "foot"): dmin = min(dmin, float(LY.cap_d(pts, *caps[cn]).min()))
    return ukey(u), round(100 * dmin, 1)

def pinch():
    g_ = {}
    def upd(k, val):
        g_[k] = min(g_.get(k, 9.0), val)
    for f in sim[::4]:
        plate, br, link = frame_parts(f); plp = LY.poly_pts(plate, 0.005); brp = LY.poly_pts(br, 0.005)
        # the link and the bracket are on the head side; same plane only near the bracket side plate
        lk = LY.seg_pts(*link, 30)
        upd("连杆—座板底面", float(np.min(np.hypot(*(lk[:, None, :] - plp[None, :, :]).transpose(2, 0, 1)))) - 0.02)
        upd("连杆—导轨立柱", min(float(LY.cap_d(lk, X, Y_, 0.025).min()) for X, Y_ in COLUMN) - 0.02)
        upd("座板底面—底座", float(plp[:, 1].min()) - 0.04)
        upd("支架—导轨立柱", min(float(LY.cap_d(brp, X, Y_, 0.025).min()) for X, Y_ in COLUMN))
    return {k: round(100 * v_, 1) for k, v_ in g_.items()}

def tipping(dev_kg=40.0, dev_com=(0.25, 0.08)):
    """base: x 0.03..0.78 (front extended past the pole); y from -0.27 (open, foot side) to +0.33 (head side: the side beam
    carries the link pivot B at |y| 0.31). Device mass centre (x, y) shifted to the head side."""
    out = {}; X0, X1, Yo, Yh = 0.03, 0.78, 0.27, 0.33
    cases = {"100 kg 猛坐座板后缘（1.5 倍体重）": [(1.5 * 100 * G, 0.01, 0.0)], "100 kg 整个挂在扶手立杆上": [(100 * G, 0.69, 0.25)],
             "45 kg 猛坐后缘": [(1.5 * 45 * G, 0.01, 0.0)]}
    for k, loads in cases.items():
        F = sum(a for a, _, _ in loads) + dev_kg * G
        cx = (sum(a * x for a, x, _ in loads) + dev_kg * G * dev_com[0]) / F; cy = (sum(a * y for a, _, y in loads) + dev_kg * G * dev_com[1]) / F
        out[k] = dict(cop_x=round(cx, 3), cop_y=round(cy, 3), margin_rear_cm=round(100 * (cx - X0), 1), margin_front_cm=round(100 * (X1 - cx), 1),
                      margin_side_cm=round(100 * min(Yh - cy, Yo + cy), 1))
    for m in (60, 100):
        W = (m + dev_kg) * G; yc = dev_kg * dev_com[1] / (m + dev_kg)     # person on the seat centre line, device on the head side
        out[f"侧推翻倒力（{m} kg 在台上，扶手 1.06 m）"] = dict(to_open_side_N=round(W * (Yo + yc) / 1.06), to_head_side_N=round(W * (Yh - yc) / 1.06))
    out["base"] = dict(x=[X0, X1], y=[-Yo, Yh], device_kg=dev_kg, device_com=list(dev_com))
    return out

def emergency():
    """quick release: the carriage is free; the generalized force along the rail from a seat load decides the motion."""
    gen = []
    for i in range(1, len(sim) - 1, 5):
        n_ = rot(sim[i][1]) @ np.array([0, 1.0])
        for xo in V5.XOFF:
            Cn = sim[i + 1][0] + rot(sim[i + 1][1]) @ np.array([xo, 0]); Cp = sim[i - 1][0] + rot(sim[i - 1][1]) @ np.array([xo, 0])
            ds = sim[i + 1][4] - sim[i - 1][4]; Fv = -n_                      # unit load, normal to the seat
            gen.append(((Fv @ (Cn - Cp)) / ds, float(sim[i][0][1])))       # force along the rail per N of seat load (+ = drives up)
    up = [q for q, _ in gen]; sinks = all(q * np.sign(sim[-1][4] - sim[0][4]) < 0 for q in up)
    k_max, k_min = max(abs(q) for q in up), min(abs(q) for q in up)
    # damper: rail speed <= 0.10 m/s for 100 kg at 1.5 BW; then a 45 kg user at 0.8 BW sinks at least at:
    c = 1.5 * 100 * G * k_max / 0.10; v_min = 0.8 * 45 * G * k_min / c
    return dict(seat_sinks_under_load=bool(sinks), rail_force_per_N_seat_load=[round(k_min, 2), round(k_max, 2)], damper_Ns_per_m=round(c),
                slowest_sink_mps=round(v_min, 3), tilt_max_on_the_way=round(float(max(p[1] for p in sim)), 1),
                stroke_m=M["stroke"], time_full_sink_s=[round(M["stroke"] / 0.10, 1), round(M["stroke"] / max(v_min, 1e-3), 1)])

def leg_swing(Hs=(1.50, 1.60, 1.75)):
    """open (foot) side: what the lower legs must clear when swinging back onto the bed - the floor rail and footplate edge."""
    return dict(open_side_obstacles_height_m=0.04, note="床尾一侧只有贴地纵轨（高 4 cm）和脚踏板边缘；导轨、立柱、连杆、扶手立杆都在床头一侧")

if __name__ == "__main__":
    out = dict(note=__doc__, mech=M)
    out["bed_floor_cm"] = check_bed()
    with Pool() as p: LG = dict(p.map(legs_job, USERS))
    out["bracket_vs_legs_cm"] = dict(min=min(LG.values()), worst_user=min(LG, key=LG.get))
    out["pinch_cm"] = pinch(); out["tipping"] = tipping(); out["emergency"] = emergency(); out["leg_swing"] = leg_swing()
    out["rail"] = dict(lo=np.round(RAIL[0], 4).tolist(), hi=np.round(RAIL[1], 4).tolist(), columns=[[np.round(a, 3).tolist(), np.round(b, 3).tolist()] for a, b in COLUMN])
    json.dump(out, open(os.path.join(OUT, "v5_checks.json"), "w"), ensure_ascii=False, indent=1)
    for k in ("bed_floor_cm", "bracket_vs_legs_cm", "pinch_cm", "tipping", "emergency"): print(k, out[k])
