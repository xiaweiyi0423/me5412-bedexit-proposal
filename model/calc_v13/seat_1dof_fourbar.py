"""Four-bar seat with a curved (convex) seat top: can seat shape absorb the four-bar's error?

Idea. If the seat top is a circular arc of radius R, turning the seat about the arc centre does not change the surface: the
arc simply touches the thigh at the point whose tangent matches the thigh. So the linkage only has to carry the arc centre
along the right path; tilt errors are absorbed (within the arc's angular span) and only shift the seat edges by R x error.
That turns a hard motion-generation problem (position + angle) into an easier path-generation problem.

Steps
  1 design curve as in seat_1dof_design.py (fitted to the user who moves the hip forward earliest, smoothed)
  2 for each seat radius R (flat, 0.40, 0.25, 0.18 m): synthesise a four-bar whose ground pivots sit in the space under
    the seat (x 0..0.28, z 0.04..0.38) and whose moving pivots are on the seat bracket; the mechanism starts exactly at the
    flush, level seat; cost = arc-centre path error + the part of the tilt error the arc cannot absorb
  3 run all 81 users on (a) the exact curve with that seat shape and (b) the curve the four-bar really makes
Output: seat_1dof/fourbar.json
"""
import json, os, sys, time, itertools
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import Seat, rot, Z0
from seat_relative_motion import rise, curve_fit
from seat_1dof_design import USERS, ukey, track_user, resample_curve, fb_simulate, PHI_MAX, PAD_AMAX
from model import G

OUT = os.path.join(HERE, "seat_1dof")
RS = [1e3, 0.40, 0.25, 0.18]
HALF = (ST.SEAT_X1 - ST.SEAT_X0) / 2
BOXA = dict(x=(0.0, 0.28), z=(0.04, 0.38))

def design_curve():
    _, ref = rise(1.50, 0.33, 0.6, r_b=0.09); q_, Q_, p_ = curve_fit(ref, PHI_MAX); Qm, pm = Q_[15:], p_[15:]
    ds = np.hypot(*np.diff(Qm, axis=0).T) + 0.1 * np.radians(np.abs(np.diff(pm))); t = np.concatenate([[0], np.cumsum(ds)]); t /= t[-1]
    w = np.ones(len(t)); w[0] = 50.0
    fx, fz, fp = (np.polyfit(t, v, 3, w=w) for v in (Qm[:, 0], Qm[:, 1], pm))
    tt = np.linspace(0, 1, 300); Q = np.c_[np.polyval(fx, tt), np.polyval(fz, tt)]; phi = np.clip(np.polyval(fp, tt), 0, None)
    return with_prefix(Q, phi)

def with_prefix(Q, phi):
    pre = np.array([Q[0] - np.array([0, d]) for d in np.arange(0.03, 0, -0.002)])
    return (np.arange(len(pre) + len(Q)) * 1.0, np.vstack([pre, Q]), np.concatenate([np.zeros(len(pre)), phi]))

CV = design_curve(); QT, PT = resample_curve(CV, 40)

def centre(Q, phi, R):
    return Q if R >= 1e2 else Q + np.array([rot(p) @ np.array([0.0, -R]) for p in np.atleast_1d(phi)]).reshape(Q.shape)

def sim_partial(A, L1, B, L2, c1, c2, a0, a1, n, P2_ref):
    """like fb_simulate but returns the valid part up to where the linkage cannot close."""
    Lc = np.hypot(*(c2 - c1)); loc_ang = np.arctan2(*(c2 - c1)[::-1]); out = []; prev = P2_ref
    for a in np.linspace(a0, a1, n):
        P1 = A + L1 * np.array([np.cos(a), np.sin(a)]); dv = B - P1; d = np.hypot(*dv)
        if d > L2 + Lc or d < abs(L2 - Lc) or d < 1e-9: break
        x = (Lc ** 2 - L2 ** 2 + d ** 2) / (2 * d); h = np.sqrt(max(Lc ** 2 - x ** 2, 0)); e = dv / d; nrm = np.array([-e[1], e[0]])
        c_a, c_b = P1 + x * e + h * nrm, P1 + x * e - h * nrm
        P2 = c_a if np.hypot(*(c_a - prev)) <= np.hypot(*(c_b - prev)) else c_b
        if np.hypot(*(P2 - prev)) > 0.05: break           # branch jump = dead point
        prev = P2; phi = np.degrees(loc_ang - np.arctan2(dv[1] * 0 + (P2 - P1)[1], (P2 - P1)[0]))
        out.append((P1 - rot(phi) @ c1, phi, P1, P2, a))
    return out

def sim_mech(v, n=140, partial=False):
    v = np.asarray(v, float); A, B, c1, c2 = v[0:2], v[2:4], v[4:6], v[6:8]
    P10, P20 = QT[0] + c1, QT[0] + c2; L1 = np.hypot(*(P10 - A)); L2 = np.hypot(*(P20 - B))
    if L1 < 0.05 or L2 < 0.05 or np.hypot(*(c1 - c2)) < 0.05: return None
    a0 = np.arctan2(*(P10 - A)[::-1]); best = None
    for sgn in (1, -1):
        s = sim_partial(A, L1, B, L2, c1, c2, a0, a0 + sgn * np.radians(170), n, P20)
        if len(s) < 3: continue
        z = np.array([p[0][1] for p in s])
        if z[2] < z[0] - 1e-4: continue
        top = np.argmax(z >= QT[-1][1]) if (z >= QT[-1][1]).any() else None
        if top is not None: return s[:top + 1]
        # keep only the rising part
        k = int(np.argmax(z)); cand = s[:k + 1]
        if best is None or cand[-1][0][1] > best[-1][0][1]: best = cand
    return best if partial else None

def cost(v, R):
    s = sim_mech(v, n=70, partial=True)
    if s is None: return 10.0
    short = max(0.0, QT[-1][1] - s[-1][0][1])
    if short > 0: return 1.0 + 5 * short
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    Cs = centre(Qs, ph, R); Ct = centre(QT, PT, R)
    d = np.hypot(*(Cs[None, :, :] - Ct[:, None, :]).transpose(2, 0, 1)); j = d.argmin(1)
    e_pos = d[np.arange(len(QT)), j].max()
    dphi = np.radians(ph[j] - PT)
    if R >= 1e2: e_ang = 0.10 * np.abs(dphi).max()
    else: e_ang = np.maximum(R * np.abs(dphi) - 0.02, 0).max() + 0.02 * np.abs(dphi).max()
    pen = 0.0
    A, B = v[0:2], v[2:4]
    for p in s:   # transmission angle and links clear of the bed block (x < 0, z < 0.42)
        P1, P2 = p[2], p[3]; d1 = P2 - P1; d2 = P2 - B
        ca = abs(d1 @ d2) / (np.hypot(*d1) * np.hypot(*d2) + 1e-12); pen += max(0, ca - np.cos(np.radians(35))) / len(s)
        for X, Y in ((A, P1), (B, P2)):
            for t in (0.25, 0.5, 0.75, 1.0):
                P = X + t * (Y - X)
                if P[0] < 0 and P[1] < Z0: pen += 0.01
    if np.max(np.diff([p[4] for p in s])) * 0 != 0: pen += 1
    return e_pos + e_ang + pen

BOUNDS = [BOXA["x"], BOXA["z"], BOXA["x"], BOXA["z"], (-0.08, 0.10), (-0.25, -0.03), (-0.08, 0.10), (-0.25, -0.03)]
def synth_job(args):
    R, seed = args
    r = differential_evolution(cost, BOUNDS, args=(R,), seed=seed, popsize=15, maxiter=220, tol=1e-7, polish=False)
    return R, seed, float(r.fun), r.x.tolist()

def describe(v, R):
    s = sim_mech(v, n=400); Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    Cs = centre(Qs, ph, R); Ct = centre(QT, PT, R)
    d = np.hypot(*(Cs[None, :, :] - Ct[:, None, :]).transpose(2, 0, 1)); j = d.argmin(1)
    A, B, c1, c2 = (np.array(v[i:i + 2]) for i in (0, 2, 4, 6))
    mus = []
    for p in s:
        d1 = p[3] - p[2]; d2 = p[3] - B; mus.append(float(np.degrees(np.arccos(np.clip(d1 @ d2 / (np.hypot(*d1) * np.hypot(*d2)), -1, 1)))))
    # bounding box of everything that moves or is fixed below the seat, relative to the seat footprint
    pts = np.array([A, B] + [p[2] for p in s] + [p[3] for p in s])
    # motor torque at A: lifting 0.5 BW of 60 kg + 10 kg, holding 1.5 BW of 100 kg + 10 kg, load normal to the seat at its centre
    def torque(Fs):
        out = []
        for i in range(1, len(s) - 1):
            n_ = rot(s[i][1]) @ np.array([0.0, 1.0]); F = -Fs * n_ + np.array([0, -10 * G])
            dQ = (s[i + 1][0] - s[i - 1][0]) / (s[i + 1][4] - s[i - 1][4]); out.append(float(-(F @ dQ)))
        return out
    tl, th = torque(0.5 * 60 * G), torque(1.5 * 100 * G)
    return dict(A=A.round(4).tolist(), B=B.round(4).tolist(), c1=c1.round(4).tolist(), c2=c2.round(4).tolist(),
                L1=round(float(np.hypot(*(QT[0] + c1 - A))), 4), L2=round(float(np.hypot(*(QT[0] + c2 - B))), 4), coupler=round(float(np.hypot(*(c1 - c2))), 4),
                centre_err_mm=round(1000 * float(d[np.arange(len(QT)), j].max()), 1), tilt_err_deg=round(float(np.abs(ph[j] - PT).max()), 1),
                edge_shift_mm=round(1000 * float((min(R, 0.5) if R < 1e2 else HALF) * np.radians(np.abs(ph[j] - PT)).max()), 1),
                transmission_deg=[round(min(mus), 1), round(max(mus), 1)], input_sweep_deg=round(float(np.degrees(s[-1][4] - s[0][4])), 1),
                space_x=[round(float(pts[:, 0].min()), 3), round(float(pts[:, 0].max()), 3)], space_z=[round(float(pts[:, 1].min()), 3), round(float(pts[:, 1].max()), 3)],
                torque_lift60_Nm=[round(min(tl), 1), round(max(tl), 1)], torque_hold100_Nm=[round(min(th), 1), round(max(th), 1)],
                frames=[dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in s[::10]]), s

if __name__ == "__main__":
    t0 = time.time()
    jobs = [(R, seed) for R in RS for seed in range(3)]
    with Pool() as pool: SY = pool.map(synth_job, jobs)
    best = {}
    for R, seed, f, x in SY:
        if R not in best or f < best[R][0]: best[R] = (f, x)
    print("synth", round(time.time() - t0), "s", {R: round(b[0], 4) for R, b in best.items()})
    out = dict(note=__doc__, radii=RS, mech={}, users={})
    evals = []; sims = {}
    for R in RS:
        info, s = describe(best[R][1], R); out["mech"][str(R)] = info; sims[R] = s
        print(R, {k: v for k, v in info.items() if k != "frames"})
        seat_kw = dict(R=R, r_e=0.03)
        cv_fb = with_prefix(np.array([p[0] for p in s]), np.array([p[1] for p in s]))
        evals += [(("exact", R), (u, CV, PAD_AMAX, seat_kw)) for u in USERS]
        evals += [(("fourbar", R), (u, cv_fb, PAD_AMAX, seat_kw)) for u in USERS]
    with Pool() as pool: RES = pool.map(track_user, [e[1] for e in evals])
    for (tag, _), (k, summ, _) in zip(evals, RES):
        out["users"].setdefault(f"{tag[0]} R{tag[1]}", {})[k] = summ
    ok = lambda v: bool(v.get("release_hz") and v["fwd_slip_max_cm"] <= 2 and v["min_catch_cm"] >= 0)
    table = {}
    for name, d in out["users"].items():
        vals = list(d.values()); E = [v["E0_release"] for v in vals if v.get("E0_release") is not None]
        table[name] = dict(n_ok=sum(ok(v) for v in vals), fwd_max=max(v["fwd_slip_max_cm"] for v in vals),
                           catch_min=min(v["min_catch_cm"] for v in vals if v.get("min_catch_cm") is not None),
                           E_med=round(float(np.median(E)), 3), E_max=max(E), a_max=max(v["a_max_cm"] for v in vals),
                           contact_len_med=round(float(np.median([v["contact_len_release_cm"] for v in vals if v.get("contact_len_release_cm") is not None])), 1))
        print(f"{name:18s}", table[name])
    out["table"] = table
    json.dump(out, open(os.path.join(OUT, "fourbar.json"), "w"), separators=(",", ":"))
    print("done", round(time.time() - t0), "s")
