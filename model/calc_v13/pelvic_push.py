"""Does a push on the pelvis from behind, or a forward-tilted seat, make standing up easier?

Same 2-D quasi-static sit-to-stand LP as seat_support.py, with two more inputs:
  Fp   horizontal push forward on the body from a pad behind it (0 <= Fp <= cap_p * BW), acting at height
       hip + dz. dz = -0.05 m is the buttocks / sacrum (below the hip joint), dz = +0.10 m is the lower back (above it).
       For a horizontal force only the height matters.
  tilt seat tilted forward by tilt deg: the seat reaction normal to the surface has a forward part Fs * tan(tilt)
       (no friction), acting at the seat surface 0.09 m below the hip.
Variables x = [Fx, Fz, Fs, Fp, t]: hand force on the body (x forward, z up), seat vertical force, pad force, effort.

Questions:
  A. seat-off (Fs = 0) at 0.58 / 0.62 / 0.66 m: effort with a pad at the buttocks vs at the lower back.
  B. after seat-off at 0.66 m: the rest of the way to standing (hip rising from 0.75 to 0.83 m) with the bar fixed
     where the seat stopped. Is "half squat to straight" the hard part? Does a buttock pad help there?
  C. stooped trunk (forward lean held at >= 30 deg, a crude stand-in for kyphosis): effort and how close the centre
     of pressure under the feet comes to the toes, with and without the pad pushing forward.
  D. tilted seat: start effort at 0.42 m (seat <= 0.5 BW) for tilt 0..15 deg. At seat-off Fs = 0, so in a
     quasi-static model tilt cannot change the seat-off effort at all.
"""
import json, os, sys
import numpy as np
from scipy.optimize import linprog
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from model import Subject, STSConfig, sts_geometry, moment_about, arm_ik_all, shoulder_ok, cap_rows, cross, G

SHANKS = list(range(-10, 31, 5)); TRUNKS = tuple(range(0, 81, 5))
ARMS = {"P1 cap25": (1.0, 0.25), "P2 arm x0.5": (0.5, 0.30)}
SEAT_BEHIND_HIP = 0.04; HIP_ABOVE_SEAT = 0.09; MIN_FEET = 0.30

def subject(f):
    s = Subject()
    for k in ("sh_flex", "sh_ext", "el_flex", "el_ext"): setattr(s, k, getattr(Subject(), k) * f)
    return s

def rows(sub, cfg, g, P, u, S, E, x_s, dz, tilt):
    K, Hp = g["K"], g["Hp"]; tn = np.tan(np.radians(tilt))
    C_ua = S + 0.436 * (E - S); C_fa = E + 0.5 * (P - E)
    upper = [(Hp + sub.r_headtrunk * u, sub.m_headtrunk), (C_ua, 2 * sub.m_uarm), (C_fa, 2 * sub.m_farm)]
    thighs = [(Hp + 0.433 * (K - Hp), 2 * sub.m_thigh)]
    Mh = moment_about(Hp, P, upper); Mk = moment_about(K, P, upper + thighs)
    zs = Hp[1] - HIP_ABOVE_SEAT; zp = Hp[1] + dz
    # muscle moment terms (-(r x F)) of the seat force (vertical Fs + forward Fs*tn) and the pad force (forward Fp)
    def terms(J):
        seat = -((x_s - J[0]) * 1.0 - (zs - J[1]) * tn)
        pad = (zp - J[1])
        return seat, pad
    hs, hp = terms(Hp); ks, kp = terms(K)
    lim = [(np.array([Mh.a[0], Mh.a[1], hs, hp]), Mh.b, 2 * sub.hip_ext, 2 * sub.hip_flex),
           (-np.array([Mk.a[0], Mk.a[1], ks, kp]), -Mk.b, 2 * sub.knee_ext, 2 * sub.knee_flex)]
    Me = moment_about(E, P, [(C_fa, 2 * sub.m_farm)]); Ms = moment_about(S, P, [(C_fa, 2 * sub.m_farm), (C_ua, 2 * sub.m_uarm)])
    lim += [(np.array([Ms.a[0], Ms.a[1], 0, 0]), Ms.b, 2 * sub.sh_flex, 2 * sub.sh_ext),
            (np.array([Me.a[0], Me.a[1], 0, 0]), Me.b, 2 * sub.el_flex, 2 * sub.el_ext)]
    A, b = [], []
    for a, bb, pos, neg in lim:
        A.append([*a, -pos]); b.append(-bb); A.append([*(-a), -neg]); b.append(bb)
    shank = [(g["A"] + 0.5 * (K - g["A"]), 2 * sub.m_shank_foot)]
    allm = upper + thighs + shank
    W = sum(m for _, m in allm) * G; Mw = sum(cross(p, np.array([0.0, -m * G])) for p, m in allm)
    h0 = g["heel"] + cfg.cop_margin_heel; t0 = g["toe"] - cfg.cop_margin_toe; Px, Pz = P
    # external moment about the floor origin of each force, per unit: hand (Fx,Fz) -> (-Pz, Px); seat -> (x_s - zs*tn); pad -> (-zp)
    ms_ = x_s - zs * tn; mp_ = -zp
    A.append([-Pz, Px - h0, ms_ - h0, mp_, 0]); b.append(-Mw - h0 * W)
    A.append([Pz, -Px + t0, -ms_ + t0, -mp_, 0]); b.append(Mw + t0 * W)
    A.append([0, 1, 1, 0, 0]); b.append(W - MIN_FEET * sub.M * G)
    mu = cfg.mu      # floor friction balances the hand, seat and pad horizontal forces
    A.append([1, mu, mu + tn, 1, 0]); b.append(mu * W)
    A.append([-1, mu, mu - tn, -1, 0]); b.append(mu * W)
    cA, cb = cap_rows(cfg.hand_cap * sub.M * G); A += [[r[0], r[1], 0, 0, 0] for r in cA]; b += cb
    return A, b, dict(W=W, Mw=Mw, toe=g["toe"], heel=g["heel"], Px=Px, Pz=Pz, ms=ms_, mp=mp_)

def solve(arm, h, seat_cap=0.0, pad_cap=0.0, dz=-0.05, tilt=0.0, trunk_min=0, bar_abs=None, hip_z=None):
    """h: seat height (hip = h + 0.09) unless hip_z is given (after seat-off: seat no longer touched, seat_cap must be 0)."""
    f, hc = ARMS[arm]; sub = subject(f); BW = sub.M * G; best = None
    bed_h = h if hip_z is None else hip_z - HIP_ABOVE_SEAT
    for st in SHANKS:
        cfg = STSConfig(bed_h=bed_h, shank_tilt_deg=st, trunk_grid=tuple(t for t in TRUNKS if t >= trunk_min), hand_cap=hc)
        try: g = sts_geometry(sub, cfg)
        except ValueError: continue
        if g["heel"] - g["Hp"][0] < 0.08: continue
        Hp = g["Hp"]; P = np.array(bar_abs) if bar_abs is not None else np.array([Hp[0] + 0.55, bed_h + 0.40])
        x_s = Hp[0] - SEAT_BEHIND_HIP
        for th in cfg.trunk_grid:
            u = np.array([np.sin(np.radians(th)), np.cos(np.radians(th))]); S = Hp + sub.L_trunk * u
            for E in [E for E in arm_ik_all(S, P, sub.L_uarm, sub.L_farm) if shoulder_ok(S, E, u)]:
                A, b, info = rows(sub, cfg, g, P, u, S, E, x_s, dz, tilt)
                r = linprog([0, 0, 0, 0, 1], A_ub=A, b_ub=b, bounds=[(-2000, 2000)] * 2 + [(0, seat_cap * BW), (0, pad_cap * BW), (0, None)], method="highs")
                if not r.success: continue
                if best is None or r.x[4] < best[0] - 1e-9:
                    Fx, Fz, Fs, Fp, t = r.x
                    feet = info["W"] - Fz - Fs
                    cop = -(info["Mw"] + info["Px"] * Fz - info["Pz"] * Fx + info["ms"] * Fs + info["mp"] * Fp) / feet
                    best = (t, dict(effort=round(float(t), 3), shank=st, trunk=th, Fs_BW=round(Fs / BW, 3), pad_BW=round(Fp / BW, 3),
                                    hand_x_BW=round(Fx / BW, 3), hand_z_BW=round(Fz / BW, 3),
                                    cop_to_toe_cm=round(100 * (info["toe"] - cop), 1), hip=[round(Hp[0], 3), round(Hp[1], 3)]))
    return None if best is None else best[1]

def job(a):
    kind, kw = a
    return a, solve(**kw)

if __name__ == "__main__":
    jobs = []
    for arm in ARMS:
        for h in (0.58, 0.62, 0.66):
            for pc in (0.0, 0.05, 0.10, 0.15):
                for dz in (-0.05, 0.10):
                    if pc == 0 and dz > 0: continue
                    jobs.append(("A", dict(arm=arm, h=h, pad_cap=pc, dz=dz)))
        # B: after seat-off at 0.66 m, bar fixed where it stopped (hip of the seat-off pose + 0.55, seat + 0.40)
        so = solve(arm, 0.66); bar = [so["hip"][0] + 0.55, 0.66 + 0.40]
        for hz in (0.75, 0.77, 0.79, 0.81, 0.83):
            for pc in (0.0, 0.10):
                jobs.append(("B", dict(arm=arm, h=0.66, hip_z=hz, pad_cap=pc, dz=-0.05, bar_abs=bar)))
        # C: stooped trunk (>= 30 deg) at seat-off 0.66 and halfway up, with and without a buttock pad
        for hz in (0.75, 0.79):
            for pc in (0.0, 0.10):
                jobs.append(("C", dict(arm=arm, h=0.66, hip_z=hz, pad_cap=pc, dz=-0.05, trunk_min=30, bar_abs=bar)))
        # D: tilted seat at the start (seat carries up to 0.5 BW)
        for tilt in (0, 5, 10, 15):
            for tmin in (0, 20):
                jobs.append(("D", dict(arm=arm, h=0.42, seat_cap=0.5, tilt=tilt, trunk_min=tmin)))
    with Pool() as p: R = p.map(job, jobs)
    out = {"note": __doc__.strip().split("\n")[0], "results": [dict(kind=k, **{kk: vv for kk, vv in kw.items() if kk != "bar_abs"}, res=r) for (k, kw), r in R]}
    json.dump(out, open(os.path.join(HERE, "pelvic_push.json"), "w"), indent=1, ensure_ascii=False)
    for (k, kw), r in R:
        args = {kk: vv for kk, vv in kw.items() if kk not in ("bar_abs",)}
        print(k, args, None if r is None else {kk: r[kk] for kk in ("effort", "trunk", "Fs_BW", "pad_BW", "hand_x_BW", "hand_z_BW", "cop_to_toe_cm")})
