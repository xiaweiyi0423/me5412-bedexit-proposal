"""
Bedside handle placement model — ME5412 group project
=====================================================

Question this model answers
---------------------------
Night-time bed exit has two load-bearing sub-tasks:
  Phase 1  lie -> sit   (raise the trunk from lying, legs still on the mattress)
  Phase 2  sit -> stand (seat-off from the bed edge)
Does one fixed bedside handle serve both, or do the two phases want the
handle in different places?  If they want different places, how much effort
does a fixed rail cost compared with a handle that is in the right place
for each phase?

Model in one paragraph
----------------------
2-D sagittal-plane, quasi-static (slow movement, inertia ignored).
Body = rigid segments with Winter (2009) mass / length fractions.
The hand(s) grip the handle; the handle can push/pull in any direction
(power grip on a round bar).  For a given handle position and trunk posture,
a linear program chooses the hand force F = (Fx, Fz) that minimises the
"bottleneck effort":

        effort = max over joints  |required joint moment| / joint strength

i.e. the fraction of maximum strength used by the joint that is working
hardest.  effort > 1  means some joint cannot produce the moment -> the
movement is not possible quasi-statically for this user.
Joint moments are linear in F, so this is an exact LP (scipy HiGHS).

Constraints
  Phase 2: centre of pressure under the feet stays inside the foot (with
           margin); floor friction mu = 0.5; feet carry at least 40 % BW.
  Phase 1: hip-flexor moment must not exceed the gravity moment of the legs
           (otherwise the legs lift off the mattress — the classic
           "can't do a sit-up without someone holding your feet").
  Both:    arm must reach the handle with an anatomically valid elbow
           (0-150 deg flexion) and shoulder (-60..170 deg).

Things this model deliberately does NOT capture (state these on the slide)
  * 3-D motion: real lie->sit is usually roll-to-side then push up; here it
    is a straight sit-up in the bed's long-axis plane.
  * Lateral handle offset is handled only by shortening the arm's in-plane
    reach; frontal-plane moments from a one-handed side grip are ignored.
  * Dynamics (momentum strategy), balance control, pain, cognition.
  * Strength values are assumed typical-order numbers for a frail older
    woman, not measured — conclusions should rest on RELATIVE differences
    and on the sensitivity check, not on absolute effort values.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import linprog

G = 9.81


# ----------------------------------------------------------------------------
# Subject (anthropometry from Winter, Biomechanics and Motor Control of Human
# Movement, 4th ed., Table 4.1 — fractions of body mass M and height H)
# ----------------------------------------------------------------------------
@dataclass
class Subject:
    M: float = 60.0          # kg
    H: float = 1.60          # m
    # strengths per limb [N m]  (ASSUMED, typical order for frail older women;
    # change these and re-run — see sensitivity())
    knee_ext: float = 75.0
    knee_flex: float = 40.0
    hip_ext: float = 80.0
    hip_flex: float = 50.0
    sh_flex: float = 28.0
    sh_ext: float = 35.0
    el_flex: float = 24.0
    el_ext: float = 18.0

    # --- derived geometry ---
    @property
    def L_shank(self): return 0.246 * self.H          # knee -> ankle
    @property
    def L_thigh(self): return 0.245 * self.H          # hip -> knee
    @property
    def L_trunk(self): return 0.288 * self.H          # hip -> shoulder
    @property
    def L_uarm(self): return 0.186 * self.H           # shoulder -> elbow
    @property
    def L_farm(self): return (0.146 + 0.054) * self.H # elbow -> grip centre
    @property
    def ankle_h(self): return 0.039 * self.H
    @property
    def foot_len(self): return 0.152 * self.H

    # --- masses (kg), both sides combined where bilateral ---
    @property
    def m_headtrunk(self): return (0.081 + 0.497) * self.M
    @property
    def r_headtrunk(self): return 0.180 * self.H       # COM distance from hip along trunk
    @property
    def m_uarm(self): return 0.028 * self.M            # one arm
    @property
    def m_farm(self): return (0.016 + 0.006) * self.M  # one forearm+hand
    @property
    def m_thigh(self): return 0.100 * self.M           # one thigh
    @property
    def m_shank_foot(self): return (0.0465 + 0.0145) * self.M


# ----------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------
def cross(r, f):
    """z-component of r x f in the (x,z) plane; CCW positive."""
    return r[0] * f[1] - r[1] * f[0]


def arm_ik(S, P, L1, L2):
    """Return elbow position for shoulder S reaching grip P, choosing the
    anatomically valid elbow (forearm flexes CCW relative to upper arm,
    0..150 deg).  Returns None if unreachable / no valid solution."""
    d = P - S
    D = np.hypot(*d)
    if D > L1 + L2 - 1e-6 or D < abs(L1 - L2) + 1e-6:
        return None
    a = np.arctan2(d[1], d[0])
    c = (L1**2 + D**2 - L2**2) / (2 * L1 * D)
    b = np.arccos(np.clip(c, -1, 1))
    sols = []
    for s in (+1, -1):
        ang = a + s * b
        E = S + L1 * np.array([np.cos(ang), np.sin(ang)])
        ua = E - S
        fa = P - E
        rel = np.degrees(np.arctan2(cross(ua, fa), ua @ fa))  # CCW from ua to fa
        if 0.0 <= rel <= 150.0:
            sols.append((E, rel))
    if not sols:
        return None
    return sols[0][0]


def arm_ik_all(S, P, L1, L2):
    """All anatomically valid elbow positions (0, 1 or 2)."""
    d = P - S
    D = np.hypot(*d)
    if D > L1 + L2 - 1e-6 or D < abs(L1 - L2) + 1e-6:
        return []
    a = np.arctan2(d[1], d[0])
    b = np.arccos(np.clip((L1**2 + D**2 - L2**2) / (2 * L1 * D), -1, 1))
    out = []
    for sgn in (+1, -1):
        ang = a + sgn * b
        E = S + L1 * np.array([np.cos(ang), np.sin(ang)])
        ua, fa = E - S, P - E
        rel = np.degrees(np.arctan2(cross(ua, fa), ua @ fa))
        if 0.0 <= rel <= 150.0:
            out.append(E)
    return out


def shoulder_ok(S, E, trunk_u):
    """Shoulder angle measured from 'arm hanging along -trunk' CCW
    (flexion positive). Allowed -60..170 deg."""
    hang = -trunk_u
    ua = E - S
    ang = np.degrees(np.arctan2(cross(hang, ua), hang @ ua))
    return -60.0 <= ang <= 170.0


# ----------------------------------------------------------------------------
# Linear program
# ----------------------------------------------------------------------------
@dataclass
class Moment:
    """A joint moment that is linear in F:  M = a . F + b"""
    a: np.ndarray
    b: float


def moment_about(J, P, masses, n_arm_F=1.0):
    """Moment (CCW) that the muscles at joint J must supply to the distal
    body, given: handle force F at P acting on the distal body, and point
    masses [(pos, kg), ...] on the distal body.  M_muscle = -(sum of external
    moments about J)."""
    r = P - J
    a = -np.array([-r[1], r[0]])          # -(r x F) is linear in F: -(rx*Fz - rz*Fx)
    b = -sum(cross(pos - J, np.array([0.0, -m * G])) for pos, m in masses)
    return Moment(a, b)


def cap_rows(cap_N, n=16):
    """|F| <= cap as a 16-gon (inscribed in the circle -> slightly conservative)."""
    A, b = [], []
    for k in range(n):
        a = 2 * np.pi * k / n
        A.append([np.cos(a), np.sin(a)]); b.append(cap_N * np.cos(np.pi / n))
    return A, b


def solve_lp(limits, extra_A=None, extra_b=None, F_bounds=(-2000, 2000)):
    """limits: list of (Moment, pos_limit, neg_limit) -> minimise t s.t.
    -neg*t <= M <= pos*t.   Variables x = [Fx, Fz, t]."""
    A, bvec = [], []
    for mom, pos, neg in limits:
        # a.F + b <= pos * t   ->  a.F - pos t <= -b
        A.append([mom.a[0], mom.a[1], -pos]); bvec.append(-mom.b)
        # -(a.F + b) <= neg * t -> -a.F - neg t <= b
        A.append([-mom.a[0], -mom.a[1], -neg]); bvec.append(mom.b)
    if extra_A is not None:
        for row, rhs in zip(extra_A, extra_b):
            A.append(list(row) + [0.0]); bvec.append(rhs)
    res = linprog(c=[0, 0, 1], A_ub=A, b_ub=bvec,
                  bounds=[F_bounds, F_bounds, (0, None)], method="highs")
    if not res.success:
        return None
    return res.x


# ----------------------------------------------------------------------------
# Phase 2: sit-to-stand at seat-off
# Frame: x forward (away from bed), z up, origin = floor below ankle.
# ----------------------------------------------------------------------------
@dataclass
class STSConfig:
    bed_h: float = 0.48          # top of mattress above floor [m]
    hip_above_seat: float = 0.09
    shank_tilt_deg: float = 15.0 # knee ahead of ankle (dorsiflexion at seat-off)
    edge_ahead_of_hip: float = 0.15  # bed edge is this far in front of hip
    trunk_grid: tuple = tuple(range(0, 61, 5))  # trunk tilt from vertical [deg]
    cop_margin_heel: float = 0.02
    cop_margin_toe: float = 0.04
    mu: float = 0.5
    min_foot_load: float = 0.40  # fraction of BW that must stay on the feet
    hand_cap: float = 0.30       # design envelope: total hand load <= this x BW


def sts_geometry(sub: Subject, cfg: STSConfig):
    A = np.array([0.0, sub.ankle_h])
    al = np.radians(cfg.shank_tilt_deg)
    K = A + sub.L_shank * np.array([np.sin(al), np.cos(al)])
    hip_z = cfg.bed_h + cfg.hip_above_seat
    dz = hip_z - K[1]
    if abs(dz) >= sub.L_thigh:
        raise ValueError("bed height inconsistent with leg length")
    dx = np.sqrt(sub.L_thigh**2 - dz**2)
    Hp = np.array([K[0] - dx, hip_z])
    heel = -0.25 * sub.foot_len
    toe = 0.75 * sub.foot_len
    edge_x = Hp[0] + cfg.edge_ahead_of_hip
    return dict(A=A, K=K, Hp=Hp, heel=heel, toe=toe, edge_x=edge_x)


def _sts_one(sub, cfg, g, P, u, S, E, n_arms):
    """LP for one trunk posture and one elbow solution. Returns (effort, x, limits) or None."""
    K, Hp = g["K"], g["Hp"]
    if P is not None:
        C_ua = S + 0.436 * (E - S)
        C_fa = E + 0.5 * (P - E)
        arm_masses = [(C_ua, n_arms * sub.m_uarm), (C_fa, n_arms * sub.m_farm)]
        free_arms, Fb, Pp = 2 - n_arms, (-2000, 2000), P
    else:
        arm_masses, free_arms, Fb, Pp = [], 2, (0.0, 0.0), Hp
    # free (non-gripping) arms: lumped at mid-trunk (crossed on chest)
    free_mass = [(Hp + 0.6 * sub.L_trunk * u, free_arms * (sub.m_uarm + sub.m_farm))]
    upper = [(Hp + sub.r_headtrunk * u, sub.m_headtrunk)] + arm_masses + free_mass
    thighs = [(Hp + 0.433 * (K - Hp), 2 * sub.m_thigh)]
    M_hip = moment_about(Hp, Pp, upper)                  # +ve = hip extension
    M_knee_thigh = moment_about(K, Pp, upper + thighs)
    M_knee = Moment(-M_knee_thigh.a, -M_knee_thigh.b)    # +ve = knee extension
    limits = [(M_hip, 2 * sub.hip_ext, 2 * sub.hip_flex),
              (M_knee, 2 * sub.knee_ext, 2 * sub.knee_flex)]
    if P is not None:
        M_el = moment_about(E, P, [(C_fa, n_arms * sub.m_farm)])
        M_sh = moment_about(S, P, [(C_fa, n_arms * sub.m_farm), (C_ua, n_arms * sub.m_uarm)])
        limits += [(M_sh, n_arms * sub.sh_flex, n_arms * sub.sh_ext),
                   (M_el, n_arms * sub.el_flex, n_arms * sub.el_ext)]
    # whole body: floor reaction balances weights + hand force F
    shank = [(g["A"] + 0.5 * (K - g["A"]), 2 * sub.m_shank_foot)]
    allm = upper + thighs + shank
    W = sum(m for _, m in allm) * G
    Mw = sum(cross(p, np.array([0.0, -m * G])) for p, m in allm)   # about floor origin
    # COP c = -(Mw + Px Fz - Pz Fx) / (W - Fz)
    h0 = g["heel"] + cfg.cop_margin_heel
    t0 = g["toe"] - cfg.cop_margin_toe
    Px, Pz = Pp
    A_, b_ = [], []
    A_.append([-Pz, Px - h0]); b_.append(-Mw - h0 * W)       # c >= heel (+margin)
    A_.append([Pz, -Px + t0]); b_.append(Mw + t0 * W)        # c <= toe (-margin)
    A_.append([0.0, 1.0]); b_.append(W - cfg.min_foot_load * sub.M * G)   # feet keep load
    A_.append([1.0, cfg.mu]); b_.append(cfg.mu * W)          # friction
    A_.append([-1.0, cfg.mu]); b_.append(cfg.mu * W)
    cA, cb = cap_rows(cfg.hand_cap * sub.M * G)
    A_ += cA; b_ += cb
    x = solve_lp(limits, A_, b_, F_bounds=Fb)
    if x is None:
        return None
    return x[2], x, limits


def sts_effort(sub: Subject, cfg: STSConfig, P, n_arms=2, lateral=0.0,
               return_detail=False):
    """Min bottleneck effort for seat-off with handle at P (x,z), minimised
    over trunk posture and over the (up to two) valid elbow positions.
    n_arms: hands on the handle.  lateral: lateral offset of the grip from
    the shoulder (crudely shrinks in-plane reach; keep it small)."""
    g = sts_geometry(sub, cfg)
    Hp = g["Hp"]
    R = sub.L_uarm + sub.L_farm
    if lateral >= R:
        return None
    k = np.sqrt(1 - (lateral / R) ** 2)
    L1, L2 = sub.L_uarm * k, sub.L_farm * k
    best = None
    for th in cfg.trunk_grid:
        t = np.radians(th)
        u = np.array([np.sin(t), np.cos(t)])
        S = Hp + sub.L_trunk * u
        if P is None:
            elbows = [None]
        else:
            elbows = [E for E in arm_ik_all(S, P, L1, L2) if shoulder_ok(S, E, u)]
        for E in elbows:
            r = _sts_one(sub, cfg, g, P, u, S, E, n_arms)
            if r is not None and (best is None or r[0] < best[0]):
                best = (r[0], r[1], r[2], th, E)
    if best is None:
        return None
    if not return_detail:
        return best[0]
    eff, x, limits, th, E = best
    F = np.array([x[0], x[1]])
    detail = dict(effort=eff, trunk_deg=th, Fx=x[0], Fz=x[1],
                  elbow=None if E is None else E.tolist(),
                  hand_load_pct_BW=100 * np.hypot(*F) / (sub.M * G), joint_use={})
    for nm, (mom, pos, neg) in zip(["hip", "knee", "shoulder", "elbow"], limits):
        val = mom.a @ F + mom.b
        detail["joint_use"][nm] = float(val / pos if val >= 0 else -val / neg)
    return detail


def sts_collides(sub, cfg, P, clearance=0.08):
    """Handle may not sit inside the thigh or shank (two-handed, midline)."""
    g = sts_geometry(sub, cfg)
    for a, b in ((g["Hp"], g["K"]), (g["K"], g["A"])):
        ab = b - a
        tt = np.clip((P - a) @ ab / (ab @ ab), 0, 1)
        if np.hypot(*(P - (a + tt * ab))) < clearance:
            return True
    # below the thigh line and behind the knee = under/inside the bed
    if P[0] < g["K"][0] and P[1] < g["Hp"][1] + 0.05 and P[0] > g["edge_x"] - 0.4:
        return True
    return False


# ----------------------------------------------------------------------------
# Phase 1: lie-to-sit (trunk raise, legs on mattress)
# Frame: x along the bed toward the feet, z up, origin = hip joint centre
# while lying. Mattress top at z = -hip_above_mattress.
# ----------------------------------------------------------------------------
@dataclass
class SitUpConfig:
    hip_above_mattress: float = 0.10
    phi_grid: tuple = tuple(range(0, 46, 5))   # trunk angle above horizontal [deg]
    leg_com_from_hip: float = 0.40             # fraction of leg length
    hand_cap: float = 0.30                     # total hand load <= this x BW


def _situp_one(sub, cfg, P, u, Hp, L1, L2, n_arms, M_leg_hold, E=None):
    """LP for one trunk angle and one grip point. Returns (effort, x, limits) or None."""
    S = Hp + sub.L_trunk * u
    mattress_z = -cfg.hip_above_mattress
    if P is not None:
        if E is None or not shoulder_ok(S, E, u) or E[1] < mattress_z:
            return None
        C_ua = S + 0.436 * (E - S)
        C_fa = E + 0.5 * (P - E)
        arm_masses = [(C_ua, n_arms * sub.m_uarm), (C_fa, n_arms * sub.m_farm)]
        free_arms, Fb, Pp = 2 - n_arms, (-2000, 2000), P
    else:
        arm_masses, free_arms, Fb, Pp = [], 2, (0.0, 0.0), Hp
    free_mass = [(Hp + 0.6 * sub.L_trunk * u, free_arms * (sub.m_uarm + sub.m_farm))]
    upper = [(Hp + sub.r_headtrunk * u, sub.m_headtrunk)] + arm_masses + free_mass
    M_hip = moment_about(Hp, Pp, upper)          # CCW +ve = extension; flexion negative
    limits = [(M_hip, 2 * sub.hip_ext, 2 * sub.hip_flex)]
    if P is not None:
        M_el = moment_about(E, P, [(C_fa, n_arms * sub.m_farm)])
        M_sh = moment_about(S, P, [(C_fa, n_arms * sub.m_farm),
                                   (C_ua, n_arms * sub.m_uarm)])
        limits += [(M_sh, n_arms * sub.sh_flex, n_arms * sub.sh_ext),
                   (M_el, n_arms * sub.el_flex, n_arms * sub.el_ext)]
    # legs must not lift: flexion moment (= -M_hip) <= M_leg_hold
    extra_A = [[-M_hip.a[0], -M_hip.a[1]]]
    extra_b = [M_hip.b + M_leg_hold]
    cA, cb = cap_rows(cfg.hand_cap * sub.M * G)
    extra_A += cA; extra_b += cb
    x = solve_lp(limits, extra_A, extra_b, F_bounds=Fb)
    if x is None:
        return None
    return x[2], x, limits


def situp_effort(sub: Subject, cfg: SitUpConfig, P, n_arms=1, lateral=0.15,
                 return_detail=False):
    """P: None (no handle), a single (x,z) point, or an (n,2) array of grip
    points along a bar — the user may re-grip at each trunk angle.
    Returns the worst (over trunk angles) of the best (over grip points)
    bottleneck effort; None if some trunk angle cannot be completed."""
    Hp = np.array([0.0, 0.0])
    R = sub.L_uarm + sub.L_farm
    if P is not None and lateral >= R:
        return None
    k = np.sqrt(1 - (lateral / R) ** 2) if P is not None else 1.0
    L1, L2 = sub.L_uarm * k, sub.L_farm * k
    leg_len = sub.L_thigh + sub.L_shank + sub.ankle_h
    m_legs = 2 * (sub.m_thigh + sub.m_shank_foot)
    M_leg_hold = m_legs * G * cfg.leg_com_from_hip * leg_len   # max flexor moment before legs lift
    pts = [None] if P is None else list(np.atleast_2d(P))
    worst, worst_detail = 0.0, None
    for ph in cfg.phi_grid:
        f = np.radians(ph)
        u = np.array([-np.cos(f), np.sin(f)])   # hip -> shoulder (toward head, up)
        best = None
        S = Hp + sub.L_trunk * u
        for Pi in pts:
            for E in ([None] if Pi is None else arm_ik_all(S, Pi, L1, L2)):
                r = _situp_one(sub, cfg, Pi, u, Hp, L1, L2, n_arms, M_leg_hold, E)
                if r is not None and (best is None or r[0] < best[0]):
                    best = (r[0], r[1], r[2], Pi)
        if best is None:
            return None if P is not None else float("inf")
        if best[0] > worst:
            eff, x, limits, Pi = best
            F = np.array([x[0], x[1]])
            worst = eff
            worst_detail = dict(effort=eff, phi_deg=ph, Fx=x[0], Fz=x[1],
                                grip=None if Pi is None else Pi.tolist(),
                                hand_load_pct_BW=100 * np.hypot(*F) / (sub.M * G),
                                joint_use={})
            for nm, (mom, pos, neg) in zip(["hip", "shoulder", "elbow"], limits):
                val = mom.a @ F + mom.b
                worst_detail["joint_use"][nm] = float(val / pos if val >= 0 else -val / neg)
    return worst_detail if return_detail else worst


def bar_points(center, length, n=5):
    """Grip points along a horizontal bar (along the bed's long axis)."""
    c = np.asarray(center, float)
    return np.array([[c[0] + d, c[1]] for d in np.linspace(-length / 2, length / 2, n)])


# ----------------------------------------------------------------------------
# Fixed bedside rail vs phase-matched handle
# A rail is mounted along the bed edge. Its grip is centred at lengthwise
# position s (relative to the user's hip; negative = toward the head),
# height h above the floor, grip length 0.40 m (user grabs the best point).
#   Phase 1: user lies with near shoulder ~0.15 m from the edge
#            -> in-plane point (x = s', z = h - bed_h - 0.10), lateral 0.15
#   Phase 2: user sits on the edge facing out; the rail is beside them
#            -> in-plane point (x = edge_x + 0.03, z = h),
#               lateral = max(0.20, |s'|), ONE hand
# ----------------------------------------------------------------------------
def rail_efforts(sub, sts_cfg, su_cfg, s, h, grip_len=0.40, n_pts=5,
                 lateral2=0.22):
    """Phase 1: user lies with hip at lengthwise 0, re-grips anywhere on the
    rail.  Phase 2: we GRANT that the user shuffles along the edge until the
    rail is right beside the hip (lateral offset lateral2), one hand."""
    z1 = h - sts_cfg.bed_h - su_cfg.hip_above_mattress
    e1 = situp_effort(sub, su_cfg, bar_points((s, z1), grip_len, n_pts),
                      n_arms=1, lateral=0.15)
    g = sts_geometry(sub, sts_cfg)
    e2 = sts_effort(sub, sts_cfg, np.array([g["edge_x"] + 0.03, h]),
                    n_arms=1, lateral=lateral2)
    return e1, e2
