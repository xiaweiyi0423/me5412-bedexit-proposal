"""Seat trajectory study: can the seat keep supporting the user higher up, and is one degree of freedom enough?

Question (from the team): instead of a level seat that rises vertically, let the seat follow the natural rise (forward and
up) and tilt forward so it stays under the buttock / back of the thigh. Is that feasible with one DOF, how much better is a
second DOF, and how much do generous tolerances (deeper seat, rounded front bolster, longer travel) buy?

Method, in three layers.
1. Body. 2-D person (model.Subject, scaled with height H), feet fixed with the ankle at x_a. A posture on the way up is
   (hip height hz, shank tilt s); the hip x follows from the leg lengths. The back of the body is a circle of radius 0.09 m
   round the hip (buttock) joined to a line along the back of the thigh. Contact on the buttock or within 4 cm down the thigh
   pushes the pelvis (helps hip and knee); further down the thigh it helps the knee only; beyond A_MAX it is not accepted
   (pressure on the hamstrings), nor is contact on the back of the buttock (outward normal more than 60 deg from down).
2. Effort maps, per person, on the (hz, s) grid: E0 = least bottleneck effort with no seat (hands on the bar <= 25 % BW);
   Ea = the same with a seat pushing up on the pelvis, <= 0.5 BW (proxy for the supported phase). LP as model.py.
3. Seat mechanisms. The seat follows the body by force (it moves along its path until it touches), so a mechanism admits a
   posture if, along its path and within its travel, the first touch lands on an accepted part of the body.
   The rise is a route through the grid: supported nodes must be admitted by the mechanism, then the user lets go (release)
   and continues alone. The hardest moment of the best route (min over routes of the max effort along it) is the figure of
   merit; the user is allowed to choose the route (posture) - a habit check comes after.

Mechanisms (seat 17 cm deep, flush with the bed at 0.42 m at the start; travel limits as listed):
  V      vertical lift, seat level (current design), seat top <= 0.66 m
  L1     one DOF: straight guide inclined forward by beta, seat tilt coupled to travel (k deg per 10 cm, capped)
  ARC    one DOF: seat fixed to an arm that swings about a pivot in front of and below the seat (lift-chair style)
  L2     two DOF: inclined guide + independently driven tilt (any tilt 0..phi_max at each posture)
  XZ     two DOF: seat moves forward and up independently, stays level
  IDEAL  any seat pose (contact anywhere accepted), same top height: the upper bound for any mechanism
Same simplifications as the rest of the model: 2-D, quasi-static, frictionless seat contact, rigid body outline (a cushion
gives a little more contact area, so the accepted zone is a stand-in for comfort limits).
"""
import json, os, sys, heapq, itertools, time
import numpy as np
from scipy.optimize import linprog
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
from model import Subject, moment_about, arm_ik_all, shoulder_ok, cap_rows, cross, G

Z0 = 0.42; TOP = 0.66                  # seat top: flush with the bed at the start, highest position of the current lift
SEAT_X0, SEAT_X1 = -0.03, 0.14         # seat from 3 cm over the mattress to 14 cm in front of the bed edge
CAP = 0.5; MIN_FEET = 0.30; MU = 0.5; HAND_CAP = 0.25
BAR_X = 0.69                           # bar 0.55 m ahead of the seated hip, 0.40 m above the seat (rises with the seat)
R_B = 0.09                             # buttock radius = hip height above a flat seat
PELVIS_A = 0.04; A_MAX = 0.12; BACK_LIMIT = -60.0
TRUNKS = tuple(range(0, 81, 5))
S_GRID = np.arange(-5.0, 30.01, 2.5)   # shank tilt (deg, knee ahead of ankle) = ankle dorsiflexion
DZ = 0.02
PERSONS_H = [1.50, 1.60, 1.75]; PERSONS_XA = [0.25, 0.29, 0.33]; S_MAX = [20.0, 25.0, 30.0]
OUT = os.path.join(HERE, "seat_trajectory")

def hz_grid(sub):
    stand = sub.ankle_h + sub.L_shank + sub.L_thigh
    return np.round(np.arange(Z0 + R_B, stand - 0.012, DZ), 3)

def pose(sub, x_a, hz, s_deg):
    A = np.array([x_a, sub.ankle_h]); s = np.radians(s_deg)
    K = A + sub.L_shank * np.array([np.sin(s), np.cos(s)])
    dz = hz - K[1]
    if abs(dz) >= sub.L_thigh - 1e-6: return None
    Hp = np.array([K[0] - np.sqrt(sub.L_thigh ** 2 - dz ** 2), hz])
    u = (K - Hp) / sub.L_thigh
    theta = float(np.degrees(np.arctan2(-u[1], u[0])))
    return dict(A=A, K=K, Hp=Hp, u=u, theta=theta)

def bar_at(hz):
    return np.array([BAR_X, min(hz - R_B, TOP) + 0.40])

# ---------------------------------------------------------------- effort LP (vars Fx, Fz, Fc, t)
def effort(sub, pz, bar, contact=None, cap=CAP):
    K, Hp, A = pz["K"], pz["Hp"], pz["A"]; BW = sub.M * G; best = None
    P = np.asarray(bar, float); foot = sub.foot_len; heel, toe = A[0] - 0.25 * foot, A[0] + 0.75 * foot
    if contact is not None:
        C, f, pel = contact; fx, fz = f
        hc = -cross(C - Hp, f) if pel else 0.0; kc = -cross(C - K, f); mc = cross(C, f)
    else:
        hc = kc = mc = fx = fz = 0.0
    for th in TRUNKS:
        uT = np.array([np.sin(np.radians(th)), np.cos(np.radians(th))]); S = Hp + sub.L_trunk * uT
        for E in [E for E in arm_ik_all(S, P, sub.L_uarm, sub.L_farm) if shoulder_ok(S, E, uT)]:
            C_ua = S + 0.436 * (E - S); C_fa = E + 0.5 * (P - E)
            upper = [(Hp + sub.r_headtrunk * uT, sub.m_headtrunk), (C_ua, 2 * sub.m_uarm), (C_fa, 2 * sub.m_farm)]
            thighs = [(Hp + 0.433 * (K - Hp), 2 * sub.m_thigh)]
            Mh = moment_about(Hp, P, upper); Mk = moment_about(K, P, upper + thighs)
            Me = moment_about(E, P, [(C_fa, 2 * sub.m_farm)]); Ms = moment_about(S, P, [(C_fa, 2 * sub.m_farm), (C_ua, 2 * sub.m_uarm)])
            lim = [(np.array([Mh.a[0], Mh.a[1], hc]), Mh.b, 2 * sub.hip_ext, 2 * sub.hip_flex),
                   (-np.array([Mk.a[0], Mk.a[1], kc]), -Mk.b, 2 * sub.knee_ext, 2 * sub.knee_flex),
                   (np.array([Ms.a[0], Ms.a[1], 0]), Ms.b, 2 * sub.sh_flex, 2 * sub.sh_ext),
                   (np.array([Me.a[0], Me.a[1], 0]), Me.b, 2 * sub.el_flex, 2 * sub.el_ext)]
            Arow, b = [], []
            for a, bb, pos, neg in lim:
                Arow.append([*a, -pos]); b.append(-bb); Arow.append([*(-a), -neg]); b.append(bb)
            allm = upper + thighs + [(A + 0.5 * (K - A), 2 * sub.m_shank_foot)]
            W = sum(m for _, m in allm) * G; Mw = sum(cross(p, np.array([0.0, -m * G])) for p, m in allm)
            h0, t0 = heel + 0.02, toe - 0.04; Px, Pz = P
            Arow.append([-Pz, Px - h0, mc - h0 * fz, 0]); b.append(-Mw - h0 * W)
            Arow.append([Pz, -Px + t0, -mc + t0 * fz, 0]); b.append(Mw + t0 * W)
            Arow.append([0, 1, fz, 0]); b.append(W - MIN_FEET * BW)
            Arow.append([1, MU, fx + MU * fz, 0]); b.append(MU * W)
            Arow.append([-1, MU, -fx + MU * fz, 0]); b.append(MU * W)
            cA, cb = cap_rows(HAND_CAP * BW); Arow += [[r[0], r[1], 0, 0] for r in cA]; b += cb
            r = linprog([0, 0, 0, 1], A_ub=Arow, b_ub=b,
                        bounds=[(-2000, 2000)] * 2 + [(0, cap * BW if contact is not None else 0), (0, None)], method="highs")
            if r.success and (best is None or r.x[3] < best[0]):
                best = (float(r.x[3]), th, float(r.x[2] / BW))
    return best

def map_job(args):
    H, x_a = args; sub = Subject(H=H); hzs = hz_grid(sub)
    E0 = np.full((len(hzs), len(S_GRID)), np.inf); Ea = E0.copy(); T0 = np.full(E0.shape, -1.0)
    for i, hz in enumerate(hzs):
        for j, s in enumerate(S_GRID):
            pz = pose(sub, x_a, hz, s)
            if pz is None: continue
            r = effort(sub, pz, bar_at(hz))
            if r: E0[i, j], T0[i, j] = r[0], r[1]
            C = pz["Hp"] + np.array([-0.04, -R_B])
            r = effort(sub, pz, bar_at(hz), (C, np.array([0.0, 1.0]), True))
            if r: Ea[i, j] = r[0]
    return (H, x_a), dict(hz=hzs.tolist(), E0=E0.tolist(), Ea=Ea.tolist(), trunk0=T0.tolist())

# ---------------------------------------------------------------- body outline and seat profile
def body_points(pz):
    """sample points on the back outline: (points, kind) kind 0 = pelvis, 1 = thigh (accepted), 2 = not accepted;
    a = distance along the thigh line from the buttock tangent point (arc points: a <= 0)."""
    Hp, u, th = pz["Hp"], pz["u"], pz["theta"]
    g = np.radians(np.linspace(-90.0, -th, 40)) if th < 90 else np.radians(np.array([-90.0]))
    arc = Hp + R_B * np.stack([np.sin(g), -np.cos(g)], 1)
    a_arc = -R_B * (np.radians(-th) - g)
    kind_arc = np.where(np.degrees(g) < BACK_LIMIT, 2, 0)
    a = np.linspace(0.005, 0.30, 60); T0 = Hp + R_B * np.array([np.sin(np.radians(-th)), -np.cos(np.radians(-th))])
    line = T0 + a[:, None] * u
    kind_line = np.where(a <= PELVIS_A, 0, np.where(a <= A_MAX, 1, 2))
    return np.vstack([arc, line]), np.concatenate([kind_arc, kind_line]), np.concatenate([a_arc, a])

class Seat:
    """profile in the seat frame (origin = top centre, x forward): top arc radius R, rounded front edge r_e, rear r_r."""
    def __init__(self, depth=SEAT_X1 - SEAT_X0, R=1e3, r_e=0.02, r_r=0.01, thick=0.06):
        self.h = depth / 2; self.R, self.r_e, self.r_r, self.t = R, r_e, r_r, thick
        self.cf = np.array([self.h - r_e, self._arc(self.h - r_e) - r_e]); self.cr = np.array([-self.h + r_r, self._arc(-self.h + r_r) - r_r])
    def _arc(self, x): return np.sqrt(self.R ** 2 - x ** 2) - self.R
    def top(self, x):
        z = self._arc(np.clip(x, -self.h, self.h))
        f = x > self.cf[0]; z = np.where(f, self.cf[1] + np.sqrt(np.clip(self.r_e ** 2 - (x - self.cf[0]) ** 2, 0, None)), z)
        r = x < self.cr[0]; z = np.where(r, self.cr[1] + np.sqrt(np.clip(self.r_r ** 2 - (x - self.cr[0]) ** 2, 0, None)), z)
        return z
    def normal(self, x):
        e = 1e-4; d = (self.top(x + e) - self.top(x - e)) / (2 * e)
        n = np.array([-d, 1.0]); return n / np.hypot(*n)

def rot(phi):
    p = np.radians(phi); return np.array([[np.cos(p), np.sin(p)], [-np.sin(p), np.cos(p)]])  # local -> world, + = front down

def first_touch(seat, path, pts):
    """path: (q array, Q array (n,2), phi array). Returns (index, contact point index, local x) of the first pose that
    touches, or None if the seat never reaches the body within its travel."""
    qs, Qs, phis = path
    for k in range(len(qs)):
        Rm = rot(phis[k]); loc = (pts - Qs[k]) @ Rm             # world -> local (Rm orthonormal: inverse = transpose)
        x, z = loc[:, 0], loc[:, 1]
        inside = (x >= -seat.h) & (x <= seat.h)
        gap = np.where(inside, z - seat.top(x), np.inf)
        gap = np.where(gap < -seat.t, np.inf, gap)
        j = int(np.argmin(gap))
        if gap[j] <= 0: return k, j, x[j]
    return None

def contact_info(seat, path, pz):
    pts, kind, aa = body_points(pz)
    ft = first_touch(seat, path, pts)
    if ft is None: return None
    k, j, xl = ft; qs, Qs, phis = path
    n = rot(phis[k]) @ seat.normal(xl)
    return dict(ok=bool(kind[j] < 2), pelvis=bool(kind[j] == 0), a=float(aa[j]), P=pts[j].tolist(), f=n.tolist(),
                q=float(qs[k]), phi=float(phis[k]), seat_top=float(Qs[k][1]))

# ---------------------------------------------------------------- mechanisms -> list of paths (one path = one DOF)
Q0 = np.array([(SEAT_X0 + SEAT_X1) / 2, Z0])
QSTEP = 0.004

def path_line(beta, k=0.0, phi_max=0.0, top=TOP, q0=-0.03):
    b = np.radians(beta); qmax = (top - Z0) / np.cos(b)
    q = np.arange(q0, qmax + 1e-9, QSTEP); Q = Q0 + q[:, None] * np.array([np.sin(b), np.cos(b)])
    phi = np.clip(k * 10 * np.clip(q, 0, None), 0, phi_max)
    return q, Q, phi

def path_arc(px, pz_, top=TOP, amax=60.0):
    """seat rigidly on an arm about pivot O = Q0 + (px, pz_) (px > 0: in front); clockwise swing tilts the seat forward."""
    O = Q0 + np.array([px, pz_]); r0 = Q0 - O
    al = np.arange(-2.0, amax + 1e-9, 0.25); a = np.radians(al)
    Q = O + np.stack([r0[0] * np.cos(a) + r0[1] * np.sin(a), -r0[0] * np.sin(a) + r0[1] * np.cos(a)], 1)
    keep = Q[:, 1] <= top + 1e-9
    if not keep.any(): return None
    last = np.argmax(~keep) if (~keep).any() else len(al)
    return al[:last], Q[:last], np.clip(al[:last], 0, None)

MECHS = {}
def add(name, family, seat_kw, paths, note):
    MECHS[name] = dict(family=family, seat=seat_kw, paths=paths, note=note)

def build_mechs():
    add("V", "1-DOF", {}, [("line", (0.0,))], "current: vertical, level, top 0.66")
    add("V top0.72", "tolerance", {}, [("line", (0.0, 0, 0, 0.72))], "vertical, 6 cm more travel")
    add("V deep+6", "tolerance", dict(depth=0.23), [("line", (0.0,))], "vertical, seat 6 cm deeper (front edge 0.20)")
    add("V bolster", "tolerance", dict(r_e=0.06), [("line", (0.0,))], "vertical, front edge rounded r 6 cm")
    add("V deep+bolster+0.72", "tolerance", dict(depth=0.23, r_e=0.06), [("line", (0.0, 0, 0, 0.72))], "all three")
    for beta in (10, 20, 30, 40):
        for k in (0, 5, 10, 20):
            for pm in ((0,) if k == 0 else (15, 30, 45)):
                add(f"L1 b{beta} k{k} p{pm}", "1-DOF", {}, [("line", (beta, k, pm))], "inclined guide + coupled tilt")
                if beta in (20, 30) and k in (0, 10):
                    add(f"L1 b{beta} k{k} p{pm} bolster", "tolerance", dict(r_e=0.06), [("line", (beta, k, pm))], "with r 6 cm bolster")
    for px in (0.15, 0.30, 0.45):
        for pz_ in (-0.30, -0.15, 0.0):
            add(f"ARC x{int(px*100)} z{int(pz_*100)}", "1-DOF", {}, [("arc", (px, pz_))], "swing arm")
    for beta in (0, 20, 30):
        for pm in (20, 40):
            add(f"L2 b{beta} p{pm}", "2-DOF", {}, [("line", (beta, 1e3, phi)) for phi in range(0, pm + 1, 5)], "guide + driven tilt")
    add("XZ", "2-DOF", {}, [("line", (beta,)) for beta in range(0, 61, 5)], "forward + up, level")
    add("XZ+tilt", "3-DOF", {}, [("line", (beta, 1e3, phi)) for beta in range(0, 61, 5) for phi in range(0, 46, 5)], "forward + up + tilt")

def make_path(kind, p):
    if kind == "line":
        beta = p[0]; k = p[1] if len(p) > 1 else 0.0; pm = p[2] if len(p) > 2 else 0.0; top = p[3] if len(p) > 3 else TOP
        if k >= 1e3:   # fixed tilt pm during the whole travel (a driven tilt set before contact)
            q, Q, _ = path_line(beta, 0, 0, top); return q, Q, np.full(len(q), float(pm))
        return path_line(beta, k, pm, top)
    return path_arc(*p)

# ---------------------------------------------------------------- admissibility grid and best route
def admit_job(args):
    (H, x_a), mname = args; sub = Subject(H=H); m = MECHS[mname]; seat = Seat(**m["seat"]); hzs = hz_grid(sub)
    paths = [make_path(k, p) for k, p in m["paths"]]; paths = [p for p in paths if p is not None]
    adm = np.zeros((len(hzs), len(S_GRID)), bool); info = {}
    for i, hz in enumerate(hzs):
        for j, s in enumerate(S_GRID):
            pz = pose(sub, x_a, hz, s)
            if pz is None: continue
            best = None
            for path in paths:
                c = contact_info(seat, path, pz)
                if c and c["ok"] and (best is None or (c["pelvis"] and not best["pelvis"])):
                    best = c
                    if c["pelvis"]: break
            if best: adm[i, j] = True; info[(i, j)] = best
    return adm, info

def ideal_admit(sub, x_a, hzs, top=TOP):
    adm = np.zeros((len(hzs), len(S_GRID)), bool)
    for i, hz in enumerate(hzs):
        for j, s in enumerate(S_GRID):
            pz = pose(sub, x_a, hz, s)
            if pz is None: continue
            pts, kind, _ = body_points(pz)
            if pts[kind < 2][:, 1].min() <= top: adm[i, j] = True   # some accepted body point is low enough to reach
    return adm

def best_route(E0, Ea, adm, s_max, start_s_min=None):
    """bottleneck route: supported nodes (admitted, cost Ea) -> release -> free nodes (cost E0) -> top row.
    Moves: up one row with |ds| <= 2 grid steps (5 deg), or sideways one step. Returns (peak, route)."""
    n, m = E0.shape; okS = S_GRID <= s_max + 1e-9
    INF = np.inf; best = {}; heap = []; cnt = itertools.count()
    for j in range(m):
        if adm[0, j] and okS[j] and np.isfinite(Ea[0, j]):
            heapq.heappush(heap, (Ea[0, j], next(cnt), 0, j, 0, None))
    prev = {}
    while heap:
        c, _, i, j, ph, pr = heapq.heappop(heap)
        if (i, j, ph) in best: continue
        best[(i, j, ph)] = c; prev[(i, j, ph)] = pr
        if ph == 1 and i == n - 1:
            route = []; key = (i, j, ph)
            while key is not None: route.append(key); key = prev[key]
            return c, route[::-1]
        nxt = []
        if ph == 0: nxt.append((i, j, 1))
        for di, dj in [(0, -1), (0, 1)] + [(1, d) for d in range(-2, 3)]:
            ii, jj = i + di, j + dj
            if 0 <= ii < n and 0 <= jj < m and okS[jj]: nxt.append((ii, jj, ph))
        for ii, jj, pp in nxt:
            if (ii, jj, pp) in best: continue
            if pp == 0 and not adm[ii, jj]: continue
            cost = (Ea if pp == 0 else E0)[ii, jj]
            if not np.isfinite(cost): continue
            heapq.heappush(heap, (max(c, cost), next(cnt), ii, jj, pp, (i, j, ph)))
    return None, None

def route_summary(route, hzs, info=None):
    rel = next((k for k in route if k[2] == 1), None)
    sup = [k for k in route if k[2] == 0]
    out = dict(release_hz=float(hzs[rel[0]]), release_s=float(S_GRID[rel[1]]))
    if info and sup:
        last = info.get((sup[-1][0], sup[-1][1]))
        if last: out.update(last_contact=dict(a=round(last["a"], 3), pelvis=last["pelvis"], phi=round(last["phi"], 1), seat_top=round(last["seat_top"], 3)))
    return out

def assisted_check(args):
    """effort along the supported part of a route with the actual contact (point, direction, pelvis or thigh)."""
    (H, x_a), steps = args; sub = Subject(H=H); hzs = hz_grid(sub); worst = 0.0
    for (i, j, c) in steps:
        pz = pose(sub, x_a, hzs[i], S_GRID[j])
        r = effort(sub, pz, bar_at(hzs[i]), (np.array(c["P"]), np.array(c["f"]), c["pelvis"]))
        e = r[0] if r else np.inf; worst = max(worst, e)
    return worst

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); t0 = time.time()
    people = list(itertools.product(PERSONS_H, PERSONS_XA))
    mpath = os.path.join(OUT, "maps.json")
    if os.path.exists(mpath):
        maps = {tuple(json.loads(k)): v for k, v in json.load(open(mpath)).items()}
    else:
        with Pool() as pool: res = pool.map(map_job, people)
        maps = dict(res); json.dump({json.dumps(list(k)): v for k, v in maps.items()}, open(mpath, "w"))
    print("maps", round(time.time() - t0), "s")
    build_mechs()
    jobs = [(p, mn) for p in people for mn in MECHS]
    with Pool() as pool: adms = pool.map(admit_job, jobs)
    print("admit", round(time.time() - t0), "s")
    ADM = {job: a for job, a in zip(jobs, adms)}
    results = {}; checks = []
    for p in people:
        sub = Subject(H=p[0]); mp = maps[p]; hzs = np.array(mp["hz"]); E0 = np.array(mp["E0"]); Ea = np.array(mp["Ea"])
        for s_max in S_MAX:
            key = f"H{p[0]:.2f} xa{p[1]:.2f} s{int(s_max)}"
            row = {}
            low = np.zeros(E0.shape, bool); low[0, :] = True
            pk, rt = best_route(E0, Ea, low, s_max)
            row["bed only (seat at 0.42, no lift)"] = dict(peak=None if pk is None else round(pk, 3), **(route_summary(rt, hzs) if rt else {}))
            for name, top in (("IDEAL", TOP), ("IDEAL top0.72", 0.72)):
                adm = ideal_admit(sub, p[1], hzs, top); pk, rt = best_route(E0, Ea, adm, s_max)
                row[name] = dict(peak=None if pk is None else round(pk, 3), **(route_summary(rt, hzs) if rt else {}))
            for mn in MECHS:
                adm, info = ADM[(p, mn)]; pk, rt = best_route(E0, Ea, adm, s_max)
                d = dict(peak=None if pk is None else round(pk, 3), family=MECHS[mn]["family"])
                if rt:
                    d.update(route_summary(rt, hzs, info))
                    steps = [(i, j, info[(i, j)]) for (i, j, ph) in rt if ph == 0]
                    checks.append(((key, mn), (p, steps)))
                row[mn] = d
            results[key] = row
    with Pool() as pool: cw = pool.map(assisted_check, [c[1] for c in checks])
    for (key, mn), w in zip([c[0] for c in checks], cw):
        results[key][mn]["assisted_actual"] = round(w, 3) if np.isfinite(w) else None
    json.dump(dict(note=__doc__, persons=dict(H=PERSONS_H, x_a=PERSONS_XA, s_max=S_MAX), mechs={k: dict(family=v["family"], note=v["note"], seat=v["seat"], paths=v["paths"]) for k, v in MECHS.items()}, results=results),
              open(os.path.join(OUT, "results.json"), "w"), indent=1)
    print("done", round(time.time() - t0), "s")
