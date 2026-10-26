"""v13: how hard is it to make the seat rise? The audit's missing link.

The v12 speed rule  v = k (F_cap - F_seat)  only moves the seat once the user has brought the seat load below the
force cap (default 0.5 BW). compare_v11 only evaluated seat-off (seat load = 0). Here the sit-to-stand LP of model.py
gets one extra variable: a vertical seat force Fs, 0 <= Fs <= cap * BW, acting under the buttocks.

Two questions, both at every seat height h on the lift path (bar fixed at hip + 0.55 m, seat + 0.40 m, as built):
  1. start effort(h, cap): the least effort that keeps the seat load at or below the cap (the seat may carry up to cap).
     The lift can only start, and keep going, if the user can produce this.
  2. min seat load(h, c): for a user whose strongest effort is c, the least seat load they can reach. Seat-off is
     possible at the first height where this reaches 0. This replaces the ad-hoc user model of calc_v12/controller_sim.

Same simplifications as model.py: 2-D, quasi-static, hip and knee (plus shoulder and elbow when holding the bar).
"""
import json, os, sys
import numpy as np
from scipy.optimize import linprog
from multiprocessing import Pool
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from model import Subject, STSConfig, sts_geometry, moment_about, arm_ik_all, shoulder_ok, cap_rows, cross, G

BAR = (0.55, 0.40)            # bar relative to hip (x) and seat (z), as in compare_v11 "B66_x55_z40"
SEAT_BEHIND_HIP = 0.04        # centre of seat pressure behind the hip joint (seat front edge at the hip, 14 cm deep)
MIN_FEET = 0.30               # feet must carry at least this x BW (the controller's 'feet on plate' threshold)
SHANKS = list(range(-10, 31, 5)); TRUNKS = tuple(range(0, 81, 5))
ARMS = {"P1 cap25": (1.0, 0.25), "P2 arm x0.5": (0.5, 0.30)}
HS = [round(0.42 + 0.02 * i, 2) for i in range(13)]          # 0.42 .. 0.66
CAPS = [0.3, 0.4, 0.5, 0.6]
EFFORTS = [0.20, 0.22, 0.23, 0.24, 0.25, 0.27, 0.29, 0.31, 0.35, 0.39]

def subject(arm_factor):
    s = Subject()
    for k in ("sh_flex", "sh_ext", "el_flex", "el_ext"): setattr(s, k, getattr(Subject(), k) * arm_factor)
    return s

def lp_rows(sub, cfg, g, P, u, S, E, x_s):
    """Inequality rows over x = [Fx, Fz, Fs, t]: joint moments within t x strength, feet COP, friction, hand cap."""
    K, Hp = g["K"], g["Hp"]
    C_ua = S + 0.436 * (E - S); C_fa = E + 0.5 * (P - E)
    upper = [(Hp + sub.r_headtrunk * u, sub.m_headtrunk), (C_ua, 2 * sub.m_uarm), (C_fa, 2 * sub.m_farm)]
    thighs = [(Hp + 0.433 * (K - Hp), 2 * sub.m_thigh)]
    Mh = moment_about(Hp, P, upper)
    Mk_t = moment_about(K, P, upper + thighs)
    # seat force (vertical, at x_s) on the pelvis: muscle moment term = -(x_s - J_x) * Fs
    hip = (np.array([Mh.a[0], Mh.a[1], -(x_s - Hp[0])]), Mh.b, 2 * sub.hip_ext, 2 * sub.hip_flex)
    knee = (-np.array([Mk_t.a[0], Mk_t.a[1], -(x_s - K[0])]), -Mk_t.b, 2 * sub.knee_ext, 2 * sub.knee_flex)
    Me = moment_about(E, P, [(C_fa, 2 * sub.m_farm)])
    Ms = moment_about(S, P, [(C_fa, 2 * sub.m_farm), (C_ua, 2 * sub.m_uarm)])
    sh = (np.array([Ms.a[0], Ms.a[1], 0.0]), Ms.b, 2 * sub.sh_flex, 2 * sub.sh_ext)
    el = (np.array([Me.a[0], Me.a[1], 0.0]), Me.b, 2 * sub.el_flex, 2 * sub.el_ext)
    A, b = [], []
    for a, bb, pos, neg in (hip, knee, sh, el):
        A.append([*a, -pos]); b.append(-bb)
        A.append([*(-a), -neg]); b.append(bb)
    shank = [(g["A"] + 0.5 * (K - g["A"]), 2 * sub.m_shank_foot)]
    allm = upper + thighs + shank
    W = sum(m for _, m in allm) * G
    Mw = sum(cross(p, np.array([0.0, -m * G])) for p, m in allm)
    h0 = g["heel"] + cfg.cop_margin_heel; t0 = g["toe"] - cfg.cop_margin_toe
    Px, Pz = P
    A.append([-Pz, Px - h0, x_s - h0, 0]); b.append(-Mw - h0 * W)        # feet COP >= heel
    A.append([Pz, -Px + t0, -x_s + t0, 0]); b.append(Mw + t0 * W)        # feet COP <= toe
    A.append([0, 1, 1, 0]); b.append(W - MIN_FEET * sub.M * G)            # feet keep load
    A.append([1, cfg.mu, cfg.mu, 0]); b.append(cfg.mu * W)                 # floor friction
    A.append([-1, cfg.mu, cfg.mu, 0]); b.append(cfg.mu * W)
    cA, cb = cap_rows(cfg.hand_cap * sub.M * G)
    A += [[r[0], r[1], 0, 0] for r in cA]; b += cb
    return A, b

def solve(sub, h, hand_cap, heel_min, seat_cap, eff_cap=None, x_off=SEAT_BEHIND_HIP):
    """eff_cap None: minimise effort with Fs <= seat_cap*BW. Else: minimise Fs with effort <= eff_cap."""
    BW = sub.M * G; best = None
    for st in SHANKS:
        cfg = STSConfig(bed_h=h, shank_tilt_deg=st, trunk_grid=TRUNKS, hand_cap=hand_cap)
        try: g = sts_geometry(sub, cfg)
        except ValueError: continue
        if g["heel"] - g["Hp"][0] < heel_min: continue
        Hp = g["Hp"]; P = np.array([Hp[0] + BAR[0], h + BAR[1]]); x_s = Hp[0] - x_off
        for th in cfg.trunk_grid:
            u = np.array([np.sin(np.radians(th)), np.cos(np.radians(th))]); S = Hp + sub.L_trunk * u
            for E in [E for E in arm_ik_all(S, P, sub.L_uarm, sub.L_farm) if shoulder_ok(S, E, u)]:
                A, b = lp_rows(sub, cfg, g, P, u, S, E, x_s)
                if eff_cap is None:
                    c = [0, 0, 0, 1]; bounds = [(-2000, 2000)] * 2 + [(0, seat_cap * BW), (0, None)]
                else:
                    c = [0, 0, 1, 0]; bounds = [(-2000, 2000)] * 2 + [(0, None), (0, eff_cap)]
                r = linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs")
                if not r.success: continue
                val = r.x[3] if eff_cap is None else r.x[2] / BW
                if best is None or val < best[0]:
                    best = (val, dict(shank=st, trunk=th, Fs_BW=round(r.x[2] / BW, 3), hand_BW=round(float(np.hypot(r.x[0], r.x[1])) / BW, 3),
                                      effort=round(float(r.x[3]), 3)))
    return best

def job(a):
    kind, arm, h, heel, x = a
    f, hc = ARMS[arm]; sub = subject(f)
    if kind == "start": return a, {str(c): solve(sub, h, hc, heel, c, x_off=SEAT_BEHIND_HIP)[1] for c in CAPS + [0.0]}
    return a, {str(e): (lambda r: None if r is None else r[1])(solve(sub, h, hc, heel, 1.0, eff_cap=e)) for e in EFFORTS}

if __name__ == "__main__":
    jobs = [("start", arm, h, heel, None) for arm in ARMS for h in HS for heel in (0.08, 0.10)]
    jobs += [("minseat", arm, h, 0.08, None) for arm in ARMS for h in HS]
    with Pool() as p: R = p.map(job, jobs)
    out = {"note": __doc__.strip().split("\n")[0], "bar": BAR, "seat_behind_hip": SEAT_BEHIND_HIP, "min_feet_BW": MIN_FEET,
           "start": {}, "min_seat": {}}
    for (kind, arm, h, heel, _), res in R:
        if kind == "start": out["start"].setdefault(arm, {}).setdefault(f"heel{int(heel*100):02d}", {})[f"{h:.2f}"] = res
        else: out["min_seat"].setdefault(arm, {})[f"{h:.2f}"] = res
    # sensitivity of the start effort at flush to where the seat pushes
    sens = {}
    for x in (0.02, 0.07):
        f, hc = ARMS["P1 cap25"]; sens[f"seat_behind_hip_{x}"] = {str(c): solve(subject(f), 0.42, hc, 0.08, c, x_off=x)[1] for c in CAPS}
    out["sensitivity_flush_P1"] = sens
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seat_support.json"), "w"), indent=1)
    for arm in ARMS:
        print(arm, "start effort (heel 0.08) by height, cap 0.5 / 0.0:")
        print("  ", [(h, out["start"][arm]["heel08"][f"{h:.2f}"]["0.5"]["effort"], out["start"][arm]["heel08"][f"{h:.2f}"]["0.0"]["effort"]) for h in HS])
        print("  min seat load for effort 0.23 / 0.25 / 0.29:", [(h, *(None if out['min_seat'][arm][f'{h:.2f}'][e] is None else out['min_seat'][arm][f'{h:.2f}'][e]['Fs_BW'] for e in ('0.23','0.25','0.29'))) for h in HS])
    print(json.dumps(sens))
