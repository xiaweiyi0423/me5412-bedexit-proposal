"""One-DOF seat: from the users' rising postures to a mechanism (design pipeline behind page/seat_1dof.html).

Steps (each writes its part of seat_1dof/design.json):
  1 users      81 users = height 1.50/1.60/1.75 m x buttock radius 0.07/0.09/0.11 m (slim / average / heavy; also the hip
               height above a flat seat) x rising habit p 0.6/1.0/2.5 (hip forward early / evenly / late) x ankle 0.25/0.29/0.33 m
               ahead of the bed edge. A stooped trunk (>= 30 deg forward) is a posture variant that changes the effort only.
  2 postures   each user's hip-knee-ankle path from sitting to standing (seat_relative_motion.rise)
  3 assist     where on the body the seat should push: effort with a 0.5 BW push at five places on the back outline
  4 seat pose  the seat pose each user would need (seat carried by the thigh, tilt <= 30 deg) -> envelope; the design curve
               is fitted to the user it serves worst-first (chosen by search); thigh-pad length from the farthest contact
  5 mechanism  a planar four-bar whose coupler is the seat bracket, synthesised to follow the design curve; motor torque,
               transmission angle, link forces, clearance to the legs and the bed
  6 check      the curve the four-bar actually makes, run for all 81 users: slip, sit-back margin, contact, release, effort
"""
import json, os, sys, itertools, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution, minimize
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import Seat, rot, body_points, pose, effort, bar_at, Z0, S_GRID
from seat_relative_motion import rise, curve_fit, curve_vertical, track, summarize, solve_s, E0_at
from model import Subject, G

OUT = os.path.join(HERE, "seat_1dof"); os.makedirs(OUT, exist_ok=True)
HS = [1.50, 1.60, 1.75]; RBS = [0.07, 0.09, 0.11]; PS = [0.6, 1.0, 2.5]; XAS = [0.25, 0.29, 0.33]
USERS = list(itertools.product(HS, RBS, PS, XAS))
PHI_MAX = 30.0; PAD_AMAX = 0.18; TYP = (1.60, 0.09, 1.0, 0.29)
MAPS = {tuple(json.loads(k)): v for k, v in json.load(open(os.path.join(HERE, "seat_trajectory", "maps.json"))).items()}

def ukey(u): return f"H{u[0]:.2f} r{u[1]:.2f} p{u[2]} xa{u[3]:.2f}"
def path_of(u):
    H, rb, p, xa = u; return rise(H, xa, p, r_b=rb)

def trunk_for(u, hz, s):
    m = MAPS[(u[0], u[3])]; hzs = np.array(m["hz"]); i = int(np.argmin(abs(hzs - hz))); j = int(np.argmin(abs(S_GRID - s)))
    t = m["trunk0"][i][j]; return 20.0 if t < 0 else float(t)

def shank_deg(pz): return float(np.degrees(np.arctan2(pz["K"][0] - pz["A"][0], pz["K"][1] - pz["A"][1])))

# ---------------------------------------------------------------- step 3: where to push
ASSIST = [("臀部后下方", "arc", -25.0), ("坐骨下方（臀-腿交界）", "a", 0.0), ("大腿近端 4 cm", "a", 0.04),
          ("大腿 10 cm", "a", 0.10), ("大腿 18 cm（托腿垫末端）", "a", 0.18)]
def assist_job(args):
    u, f = args; sub, path = path_of(u); pz = min(path, key=lambda q: abs(q["f"] - f)); rb = u[1]
    th = pz["theta"]; Hp = pz["Hp"]; uu = pz["u"]; out = []
    T0 = Hp + rb * np.array([np.sin(np.radians(-th)), -np.cos(np.radians(-th))])
    for name, kind, v in ASSIST:
        if kind == "arc":
            g = np.radians(-th + v); C = Hp + rb * np.array([np.sin(g), -np.cos(g)]); n = np.array([np.sin(g), -np.cos(g)]); pel = True
        else:
            C = T0 + v * uu; n = np.array([np.sin(np.radians(-th)), -np.cos(np.radians(-th))]); pel = v <= ST.PELVIS_A
        r = effort(sub, pz, bar_at(pz["Hp"][1]), (C, -n, pel))
        out.append(None if r is None else round(r[0], 3))
    r0 = effort(sub, pz, bar_at(pz["Hp"][1]))
    return u, f, out, None if r0 is None else round(r0[0], 3)

# ---------------------------------------------------------------- step 4: design curve choice
def track_user(args):
    u, cv, amax, seatkw = args; ST.A_MAX = amax; sub, path = path_of(u)
    rows = track(sub, path, Seat(**seatkw), cv); s = summarize(rows)
    good = [r for r in rows if r.get("contact") and r.get("ok")]
    s["fwd_slip_max_cm"] = round(100 * max([r["slip"] for r in good] + [0.0]), 1)
    s["a_max_cm"] = round(100 * max([r["a"] for r in good] + [0.0]), 1)
    if good:
        last = good[-1]; sh = solve_s(sub, u[3], last["hz"], last["hip_x"]) or 0.0
        s["E0_release"] = E0_at(MAPS, u[0], u[3], last["hz"], sh)
        s["release_shank"] = round(sh, 1); s["release_hip_x"] = round(last["hip_x"], 3)
    return ukey(u), s, rows

def resample_curve(cv, n):
    q, Q, phi = cv; main = slice(15, None)            # drop the 3 cm sink-in prefix
    Q, phi = Q[main], phi[main]
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]); t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])], 1), np.interp(t, s, phi)

# ---------------------------------------------------------------- step 5: four-bar synthesis
def circle_fit(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); c, *_ = np.linalg.lstsq(A, b, rcond=None)
    ctr = c[:2]; R = np.sqrt(c[2] + ctr @ ctr); return ctr, R, np.hypot(*(P - ctr).T) - R

def world(Q, phi, c): return Q + (rot(phi) @ c) if np.ndim(phi) == 0 else np.array([q + rot(p) @ c for q, p in zip(Q, phi)])

BOX = dict(x=(0.00, 0.30), z=(0.04, 0.40))      # fixed pivots: in front of the bed, behind the calves, above the footplate
def fb_cost(v, Qs, phis):
    c1, c2 = v[:2], v[2:]
    P1 = world(Qs, phis, c1); P2 = world(Qs, phis, c2)
    A, R1, e1 = circle_fit(P1); B, R2, e2 = circle_fit(P2)
    cost = np.abs(e1).max() + np.abs(e2).max()
    pen = 0.0
    for X in (A, B):
        pen += max(0, BOX["x"][0] - X[0]) + max(0, X[0] - BOX["x"][1]) + max(0, BOX["z"][0] - X[1]) + max(0, X[1] - BOX["z"][1])
    for R in (R1, R2): pen += max(0, 0.08 - R) + max(0, R - 0.60)
    pen += max(0, 0.08 - np.hypot(*(c1 - c2)))      # coupler points not too close
    # transmission angle (between coupler P1P2 and follower B-P2) stays in 40..140 deg
    for k in range(len(Qs)):
        d1 = P2[k] - P1[k]; d2 = P2[k] - B; ca = abs(d1 @ d2) / (np.hypot(*d1) * np.hypot(*d2))
        pen += max(0, ca - np.cos(np.radians(40)))
    return cost + 5 * pen

def fb_simulate(A, L1, B, L2, c1, c2, a0, a1, n=200, P2_ref=None):
    """drive the input link (A-P1) from angle a0 to a1; coupler = seat. Returns poses (Q, phi), P1, P2."""
    Lc = np.hypot(*(c2 - c1)); loc_ang = np.arctan2(*(c2 - c1)[::-1])
    out = []; prev = P2_ref
    for a in np.linspace(a0, a1, n):
        P1 = A + L1 * np.array([np.cos(a), np.sin(a)]); d = np.hypot(*(B - P1))
        if d > L2 + Lc or d < abs(L2 - Lc): return None
        x = (Lc ** 2 - L2 ** 2 + d ** 2) / (2 * d); h = np.sqrt(max(Lc ** 2 - x ** 2, 0)); e = (B - P1) / d; nrm = np.array([-e[1], e[0]])
        cands = [P1 + x * e + h * nrm, P1 + x * e - h * nrm]
        P2 = min(cands, key=lambda c: np.hypot(*(c - prev))) if prev is not None else cands[0]; prev = P2
        wang = np.arctan2(*(P2 - P1)[::-1]); phi = np.degrees(loc_ang - wang)
        Q = P1 - rot(phi) @ c1; out.append((Q, phi, P1, P2, a))
    return out

def seg_dist(P, A, B):
    d = B - A; t = np.clip(((P - A) @ d) / (d @ d), 0, 1); return np.hypot(*(P - (A + t * d)))

def stoop_job(args):
    u, hz, sh = args
    if hz is None: return None
    ST.TRUNKS = tuple(range(30, 81, 5)); sub = Subject(H=u[0]); pz = pose(sub, u[3], hz, sh)
    r = effort(sub, pz, bar_at(hz)); return None if r is None else round(r[0], 3)

# ---------------------------------------------------------------- main
if __name__ == "__main__":
    t0 = time.time(); D = {}
    # 1-2 users and their postures
    paths = {ukey(u): path_of(u) for u in USERS}
    D["users"] = [dict(key=ukey(u), H=u[0], r_b=u[1], p=u[2], x_a=u[3]) for u in USERS]
    print("paths", round(time.time() - t0), "s")
    # 3 assist location: typical-size users, all habits and ankles, four stages
    jobs = [(u, f) for u in USERS if u[1] == 0.09 and u[0] == 1.60 for f in (0.1, 0.3, 0.5, 0.65)]
    jobs += [(u, f) for u in USERS if u[1] in (0.07, 0.11) and u[3] == 0.29 and u[2] == 1.0 for f in (0.1, 0.3, 0.5, 0.65)]
    with Pool() as pool: A3 = pool.map(assist_job, jobs)
    D["assist"] = dict(points=[a[0] for a in ASSIST],
                       rows=[dict(user=ukey(u), f=f, effort=e, free=e0) for u, f, e, e0 in A3])
    print("assist", round(time.time() - t0), "s")
    # 4 seat pose envelope (each user's own thigh-carried seat), and the choice of the design curve
    env = {}
    for u in USERS:
        sub, p = paths[ukey(u)]; q, Q, phi = curve_fit(p, PHI_MAX)
        env[ukey(u)] = dict(Q=np.round(Q[15:], 4).tolist(), phi=np.round(phi[15:], 2).tolist())
    D["envelope"] = env
    cands = [u for u in USERS if u[2] == 0.6 and u[3] in (0.29, 0.33)]
    jobs = []; cvs = {}
    for c in cands:
        cvs[ukey(c)] = curve_fit(paths[ukey(c)][1], PHI_MAX)
        jobs += [(u, cvs[ukey(c)], PAD_AMAX, {}) for u in USERS]
    with Pool() as pool: R4 = pool.map(track_user, jobs)
    score = {}
    for i, c in enumerate(cands):
        res = [r[1] for r in R4[i * len(USERS):(i + 1) * len(USERS)]]
        fwd = max(r["fwd_slip_max_cm"] for r in res); catch = min(r["min_catch_cm"] for r in res if r.get("min_catch_cm") is not None)
        E = [r["E0_release"] for r in res if r.get("E0_release") is not None]
        score[ukey(c)] = dict(fwd_max=fwd, catch_min=catch, E_med=round(float(np.median(E)), 3), E_max=max(E),
                             n_lost=sum(r["release_hz"] is None for r in res), a_max=max(r["a_max_cm"] for r in res))
    ok = [k for k, s in score.items() if s["fwd_max"] <= 2.0 and s["catch_min"] >= 0]
    ref = min(ok or score, key=lambda k: (score[k]["E_max"], score[k]["E_med"]))
    D["design_curve"] = dict(candidates=score, chosen=ref, phi_max=PHI_MAX, pad_amax=PAD_AMAX)
    print("choice", ref, score[ref], round(time.time() - t0), "s")
    cv_raw = cvs[ref]
    # smooth the curve (cubic in a pose parameter): the tilt cap leaves a corner that a slot cannot follow
    q_, Q_, p_ = cv_raw; Qm, pm = Q_[15:], p_[15:]
    ds = np.hypot(*np.diff(Qm, axis=0).T) + 0.1 * np.radians(np.abs(np.diff(pm))); tpar = np.concatenate([[0], np.cumsum(ds)]); tpar /= tpar[-1]
    wts = np.ones(len(tpar)); wts[0] = 50.0
    fx, fz, fp = (np.polyfit(tpar, v, 3, w=wts) for v in (Qm[:, 0], Qm[:, 1], pm))
    tt = np.linspace(0, 1, 300); Qsm = np.c_[np.polyval(fx, tt), np.polyval(fz, tt)]; psm = np.clip(np.polyval(fp, tt), 0, None)
    pre = np.array([Qsm[0] - np.array([0, d]) for d in np.arange(0.03, 0, -0.002)])
    cv = (np.arange(len(pre) + len(Qsm)) * 1.0, np.vstack([pre, Qsm]), np.concatenate([np.zeros(len(pre)), psm]))
    D["design_curve"]["smoothing"] = dict(pos_err_mm=round(1000 * float(np.hypot(*(np.c_[np.polyval(fx, tpar), np.polyval(fz, tpar)] - Qm).T).max()), 1),
                                          tilt_err_deg=round(float(np.abs(np.polyval(fp, tpar) - pm).max()), 2))
    Qs, phis = resample_curve(cv, 24)
    D["design_curve"]["poses"] = dict(Q=np.round(Qs, 4).tolist(), phi=np.round(phis, 2).tolist())
    # 5a four-bar attempt (kept for the record): best of a short search, judged on pose error
    bounds = [(-0.20, 0.25), (-0.45, 0.05)] * 2; best = None
    for seed in range(3):
        r = differential_evolution(fb_cost, bounds, args=(Qs, phis), seed=seed, tol=1e-8, maxiter=800, popsize=25, polish=True)
        if best is None or r.fun < best.fun: best = r
    c1, c2 = best.x[:2], best.x[2:]; A_, L1, e1 = circle_fit(world(Qs, phis, c1)); B_, L2, e2 = circle_fit(world(Qs, phis, c2))
    D["fourbar_attempt"] = dict(circle_residual_mm=[round(1000 * float(np.abs(e1).max()), 1), round(1000 * float(np.abs(e2).max()), 1)],
                                A=A_.round(3).tolist(), B=B_.round(3).tolist(), L=[round(float(L1), 3), round(float(L2), 3)])
    print("fourbar attempt", D["fourbar_attempt"], round(time.time() - t0), "s")
    # 5b two-track guide: rollers c1, c2 on the seat bracket run in two fixed curved slots (side plates outside the seat
    #    width); one linear actuator from a base pivot Dp pushes roller pin c1. Exact for any rigid-body path.
    Qd, phid = resample_curve(cv, 160)
    def slot_path(c): return world(Qd, phid, np.asarray(c))
    def min_radius(T):
        d1 = np.gradient(T, axis=0); d2 = np.gradient(d1, axis=0)
        k = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.maximum(np.hypot(*d1.T) ** 3, 1e-12)
        return float(1 / max(k.max(), 1e-9))
    def normals(T):
        d = np.gradient(T, axis=0); d /= np.hypot(*d.T)[:, None]; return np.stack([-d[:, 1], d[:, 0]], 1), d
    def statics(c1, c2, Dp, F_seat, kg=10.0, step=1):
        T1, T2 = slot_path(c1), slot_path(c2); n1, t1 = normals(T1); n2, _ = normals(T2); out = []
        for i in range(0, len(Qd), step):
            Q, phi = Qd[i], phid[i]; n = rot(phi) @ np.array([0.0, 1.0]); F = -F_seat * n + np.array([0, -kg * G])
            m = lambda r, f: r[0] * f[1] - r[1] * f[0]
            den = m(T2[i] - T1[i], n2[i])
            if abs(den) < 1e-6: return None
            N2 = -m(Q - T1[i], F) / den; rest = -(F + N2 * n2[i])
            ua = (T1[i] - Dp) / np.hypot(*(T1[i] - Dp)); Mx = np.array([n1[i], ua]).T
            if abs(np.linalg.det(Mx)) < 1e-3: return None
            N1, Fa = np.linalg.solve(Mx, rest); out.append((float(N1), float(N2), float(Fa)))
        return np.array(out)
    grid = [(x, z) for x in np.arange(-0.08, 0.081, 0.02) for z in np.arange(-0.22, -0.049, 0.02)]
    tinfo = {}
    for c in grid:
        T = slot_path(c); tinfo[c] = dict(ok=bool(T[:, 0].min() >= 0.01 and T[:, 1].min() >= 0.08), R=min_radius(T))
    cands2 = []
    for c1 in grid:
        if not (tinfo[c1]["ok"] and tinfo[c1]["R"] >= 0.05): continue
        for c2 in grid:
            if c2 == c1 or not (tinfo[c2]["ok"] and tinfo[c2]["R"] >= 0.05): continue
            if np.hypot(c1[0] - c2[0], c1[1] - c2[1]) < 0.08: continue
            cands2.append((c1, c2))
    HOLD = 1.5 * 100 * G; LIFT = 0.5 * 60 * G
    def search(xmax):
        best2 = None
        for c1, c2 in cands2:
            T1 = slot_path(c1)
            for Dp in [np.array([x, z]) for x in np.arange(0.0, xmax + 1e-9, 0.025) for z in (0.04, 0.08, 0.12)]:
                L = np.hypot(*(T1 - Dp).T); stroke = L.max() - L.min()
                if stroke > 0.30 or L.min() < stroke + 0.11: continue
                st = statics(c1, c2, Dp, HOLD, step=5)
                if st is None: continue
                score = np.abs(st[:, 2]).max() + 0.5 * np.abs(st[:, :2]).max()
                if best2 is None or score < best2[0]: best2 = (score, c1, c2, Dp, stroke, L.min(), L.max())
        return best2
    print("two-track candidates", len(cands2))
    best2 = search(0.15) or search(0.30)
    _, c1, c2, Dp, stroke, Lmin, Lmax = best2; c1 = np.array(c1); c2 = np.array(c2)
    T1, T2 = slot_path(c1), slot_path(c2); sh = statics(c1, c2, Dp, HOLD); sl = statics(c1, c2, Dp, LIFT)
    tg = dict(c1=c1.round(3).tolist(), c2=c2.round(3).tolist(), D=Dp.round(3).tolist(), stroke=round(float(stroke), 3),
              act_len=[round(float(Lmin), 3), round(float(Lmax), 3)], R_min=[round(min_radius(T1), 3), round(min_radius(T2), 3)],
              track1=np.round(T1[::4], 4).tolist(), track2=np.round(T2[::4], 4).tolist(),
              F_act_lift60_N=[round(float(sl[:, 2].min())), round(float(sl[:, 2].max()))], F_act_hold100_N=[round(float(sh[:, 2].min())), round(float(sh[:, 2].max()))],
              N_slot_hold100_N=round(float(np.abs(sh[:, :2]).max())),
              force_curve=dict(z=np.round(Qd[::4, 1], 3).tolist(), lift60=np.round(sl[::4, 2]).tolist(), hold100=np.round(sh[::4, 2]).tolist(),
                               N1=np.round(sh[::4, 0]).tolist(), N2=np.round(sh[::4, 1]).tolist()),
              frames=[dict(Q=np.round(Qd[i], 4).tolist(), phi=round(float(phid[i]), 2)) for i in range(0, len(Qd), 4)],
              travel=dict(dx=round(float(Qd[-1, 0] - Qd[0, 0]), 3), dz=round(float(Qd[-1, 1] - Qd[0, 1]), 3), phi=round(float(phid[-1]), 1),
                          path_len=round(float(np.hypot(*np.diff(Qd, axis=0).T).sum()), 3)))
    D["mech"] = tg
    print("two-track", {k: v for k, v in tg.items() if k not in ("track1", "track2", "frames", "force_curve")}, round(time.time() - t0), "s")
    # 6 check with the design curve (exact for the two-track guide), all users; vertical lift for comparison
    jobs = [(u, cv, PAD_AMAX, {}) for u in USERS] + [(u, curve_vertical(), 0.12, {}) for u in USERS]
    with Pool() as pool: R6 = pool.map(track_user, jobs)
    real = {k: s for k, s, _ in R6[:len(USERS)]}; vert = {k: s for k, s, _ in R6[len(USERS):]}
    rows_real = {k: rows for k, _, rows in R6[:len(USERS)]}
    with Pool() as pool: SK = pool.map(stoop_job, [(u, real[ukey(u)].get("release_hz"), real[ukey(u)].get("release_shank")) for u in USERS])
    for u, e in zip(USERS, SK): real[ukey(u)]["E0_release_stooped"] = e
    D["check"] = dict(design=real, vertical=vert)
    # actuator clearance to the calves (actuator runs in the mid-plane under the seat; the plates are outside the legs)
    worst = []
    for u in USERS:
        sub, p = paths[ukey(u)]; rows = rows_real[ukey(u)]; dmin = 1e9; where = None
        for r, pz in zip(rows, p):
            if not r.get("contact"): break
            k = max(int(r["k"]) - 15, 0); Q = cv[1][min(int(r["k"]), len(cv[1]) - 1)]; phi = cv[2][min(int(r["k"]), len(cv[2]) - 1)]
            P1 = Q + rot(phi) @ c1
            for t in np.linspace(0, 1, 15):
                P = Dp + t * (P1 - Dp); d = seg_dist(P, pz["A"], pz["K"]) - 0.05
                if d < dmin: dmin, where = d, round(float(pz["Hp"][1]), 3)
        worst.append(dict(user=ukey(u), clearance_cm=round(100 * float(dmin), 1), at_hip=where))
    D["clearance"] = sorted(worst, key=lambda w: w["clearance_cm"])
    # per-user animation data (thinned)
    anim = {}
    for u in USERS:
        sub, p = paths[ukey(u)]; rows = rows_real[ukey(u)]; fr = []
        for i in range(0, len(p), 3):
            pz = p[i]; r = rows[i] if i < len(rows) else None
            d = dict(f=round(pz["f"], 3), A=np.round(pz["A"], 3).tolist(), K=np.round(pz["K"], 3).tolist(), Hp=np.round(pz["Hp"], 3).tolist(),
                     tr=trunk_for(u, pz["Hp"][1], shank_deg(pz)))
            if r and r.get("contact") and r.get("ok"):
                kk = min(int(r["k"]), len(cv[1]) - 1)
                d.update(seat=dict(Q=np.round(cv[1][kk], 4).tolist(), phi=round(float(cv[2][kk]), 1)), C=np.round(r["P"], 3).tolist(),
                         a=round(r["a"], 3), slip=round(r["slip"], 3), catch=round(r["catch"], 3))
            fr.append(d)
        anim[ukey(u)] = dict(L=[round(sub.L_shank, 3), round(sub.L_thigh, 3), round(sub.L_trunk, 3), round(sub.L_uarm, 3), round(sub.L_farm, 3)],
                             foot=round(sub.foot_len, 3), frames=fr)
    D["anim"] = anim
    D["consts"] = dict(Z0=Z0, seat_x=[ST.SEAT_X0, ST.SEAT_X1], top=0.66, bar_x=ST.BAR_X, phi_max=PHI_MAX, pad=PAD_AMAX, box=BOX)
    json.dump(D, open(os.path.join(OUT, "design.json"), "w"), separators=(",", ":"))
    def stat(dct, k, fn):
        xs = [v[k] for v in dct.values() if v.get(k) is not None]; return None if not xs else fn(xs)
    for name, dct in (("design", real), ("vertical", vert)):
        print(name, "fwd max", stat(dct, "fwd_slip_max_cm", max), "catch min", stat(dct, "min_catch_cm", min),
              "E med", stat(dct, "E0_release", np.median), "E max", stat(dct, "E0_release", max), "lost", sum(v["release_hz"] is None for v in dct.values()),
              "stooped med", stat(dct, "E0_release_stooped", np.median))
    print("clearance worst", D["clearance"][:3]); print("done", round(time.time() - t0), "s")
