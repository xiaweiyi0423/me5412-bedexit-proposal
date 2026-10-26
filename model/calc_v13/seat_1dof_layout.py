"""Seat four-bar v4: supports (pivot posts), bed clearance and a full 2-D interference check; data for the 3-D layout views.

Problem found in v3: at the start the rear bracket pivot sat at x = -2.7 cm, z = 27 cm, inside the bed. Here every rigid part
must stay out of the bed block (x < 0, z < 0.42 m; mattress top = seat top at the start) by at least 1 cm over the whole
travel. Only the soft cushion lip (3.5 cm at the rear of the seat) may lie over the mattress.

Parts and where they sit across the width (y = 0 is the seat centre line):
  full width  seat plate (4.5 cm), seat bracket (frame under the seat down to the two moving pivots), cross tube at the
              actuator rod end, base rear cross-member        -> checked against bed, floor and every user's legs
  sides       rockers A-P1 and B-P2, pivot posts at A and B (side plates at |y| = 0.26 / 0.28 m, outside the legs)
              -> checked against bed and floor here; against the body in the front view (legs stay within |y| <= hip/2)
  mid-plane   electric actuator (housing r 3 cm, rod r 1.2 cm) from the base pivot D to the rod end E on a rocker
              -> checked against bed, floor and every user's calves and feet
Body as capsules: thigh (hip-knee, radius = buttock radius), calf (knee-ankle, 5 cm), foot (heel-toe at 3.5 cm, 3.5 cm).
Output: seat_1dof/layout.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot, Z0
import seat_1dof_fourbar2 as FB2
from seat_1dof_fourbar import QT, PT, with_prefix
from seat_1dof_design import USERS, ukey, path_of, track_user, stoop_job, PAD_AMAX
from model import G

OUT = os.path.join(HERE, "seat_1dof"); TOP = 0.66
HALF = (ST.SEAT_X1 - ST.SEAT_X0) / 2; PLATE_T = 0.045; LIP = 0.035
CLR = 0.01; R_ROCK = 0.015; R_POST = 0.02; R_HOUS = 0.03; R_ROD = 0.012; R_TUBE = 0.02; R_CALF = 0.05; R_FOOT = 0.035
Y = dict(seat=0.22, rockA=0.255, rockB=0.285, rail=0.27, act=0.0)      # lateral planes (m)

def bed_d(P):
    """signed distance from points (n,2) to the bed block x < 0, 0 <= z < 0.42 (negative inside)."""
    P = np.atleast_2d(P); x, z = P[:, 0], P[:, 1]
    out = np.hypot(np.maximum(x, 0), np.maximum(z - Z0, 0))
    inside = (x < 0) & (z < Z0)
    return np.where(inside, -np.minimum(-x, Z0 - z), out)

def seg_pts(X, Y_, n=12): return np.array([X + t * (Y_ - X) for t in np.linspace(0, 1, n)])
def poly_pts(Pl, step=0.005):
    out = []
    for i in range(len(Pl)):
        a, b = Pl[i], Pl[(i + 1) % len(Pl)]; n = max(2, int(np.hypot(*(b - a)) / step)); out += [a + t * (b - a) for t in np.linspace(0, 1, n, endpoint=False)]
    return np.array(out)

def seat_polys(Q, phi, c1, c2):
    Rm = rot(phi); W = lambda L: np.array([Q + Rm @ np.array(p) for p in L])
    plate = W([(-HALF + LIP, 0), (HALF, 0), (HALF, -PLATE_T), (-HALF + LIP, -PLATE_T)])
    br = [(-HALF + LIP, -PLATE_T), (HALF - 0.03, -PLATE_T), tuple(c2), tuple(c1)]
    pts = np.array(br); c = pts.mean(0); order = np.argsort(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    return plate, W([br[i] for i in order])

def mech_bed_clear(v, s):
    """min clearance of rigid parts (plate, bracket, rockers, posts) to the bed and the floor over the frames s."""
    A, B, c1, c2 = v[0:2], v[2:4], v[4:6], v[6:8]; worst = 1.0; where = None
    posts = [(np.array([A[0], 0.04]), A, R_POST), (np.array([B[0], 0.04]), B, R_POST)]
    for f in s:
        Q, phi, P1, P2 = f[0], f[1], f[2], f[3]; plate, br = seat_polys(Q, phi, c1, c2)
        for name, pts, r in (("plate", poly_pts(plate, 0.01), 0.0), ("bracket", poly_pts(br, 0.01), 0.0),
                             ("rocker A", seg_pts(A, P1), R_ROCK), ("rocker B", seg_pts(B, P2), R_ROCK)):
            d = float(bed_d(pts).min()) - r; dz = float(pts[:, 1].min()) - r
            if min(d, dz) < worst: worst, where = min(d, dz), (name, "bed" if d < dz else "floor", round(float(Q[1]), 3))
    for X, Y_, r in posts:
        d = float(bed_d(seg_pts(X, Y_)).min()) - r
        if d < worst: worst, where = d, ("post", "bed", None)
    return worst, where

def cost(v):
    base = FB2.cost(v)
    if base >= 1.0: return base
    s = FB2.run(v, n=80)
    if s is None or len(s) < 4: return base + 1.0
    w, _ = mech_bed_clear(v, s[::3])
    return base + 5 * max(0.0, CLR - w)

BOUNDS = [(0.03, 0.30), (0.05, 0.32), (0.03, 0.30), (0.05, 0.32), (-0.085, 0.085), (-0.15, -0.03), (-0.085, 0.085), (-0.15, -0.03)]
def synth(seed):
    r = differential_evolution(cost, BOUNDS, seed=seed, popsize=16, maxiter=280, tol=1e-7, polish=False)
    return float(r.fun), r.x.tolist()

# ---------------------------------------------------------------- actuator
def act_E(f, act, A, B):
    G0, P = (A, f[2]) if act["on"] == "A" else (B, f[3])
    d = P - G0; L = np.hypot(*d); e = d / L; nrm = np.array([-e[1], e[0]]); return G0 + act["t"] * d + act["o"] * nrm

def act_parts(f, act, A, B):
    """housing (from D, length = retracted length - 2 cm) and rod (to E)."""
    D = np.array(act["D"]); E = act_E(f, act, A, B); u = (E - D) / np.hypot(*(E - D))
    H = D + u * (act["Lmin"] - 0.02)
    return (D, H, R_HOUS), (H, E, R_ROD), E

def actuator_candidates(v, s):
    A, B = np.asarray(v[0:2]), np.asarray(v[2:4]); HOLD = 1.5 * 100 * G; LIFT = 0.5 * 60 * G; cands = []
    def forces(act, Fs):
        Ls = np.array([np.hypot(*(act_E(f, act, A, B) - np.array(act["D"]))) for f in s]); out = []
        for i in range(1, len(s) - 1):
            n_ = rot(s[i][1]) @ np.array([0.0, 1.0]); Fx = -Fs * n_ + np.array([0, -10 * G])
            dW = -(Fx @ (s[i + 1][0] - s[i - 1][0])); dL = Ls[i + 1] - Ls[i - 1]
            out.append(dW / dL if abs(dL) > 1e-7 else np.inf)
        return Ls, np.array(out)
    for on in ("A", "B"):
        for t in (0.4, 0.6, 0.8, 1.0):
            for o in (-0.06, -0.03, 0.0, 0.03, 0.06):
                for Dx in np.arange(0.05, 0.226, 0.025):
                    for Dz in (0.05, 0.08):
                        act = dict(on=on, t=t, o=o, D=[float(Dx), float(Dz)])
                        Ls, Fh = forces(act, HOLD); stroke = Ls.max() - Ls.min()
                        if stroke > 0.25 or Ls.min() < stroke + 0.12: continue
                        dl = np.diff(Ls)
                        if not np.all(np.isfinite(Fh)) or (dl.min() < 0 < dl.max()): continue
                        act["Lmin"] = float(Ls.min())
                        ok = True
                        for f in s[::8]:
                            (D, H, rh), (H2, E, rr), _ = act_parts(f, act, A, B)
                            if bed_d(seg_pts(D, H)).min() - rh < CLR or bed_d(seg_pts(H2, E)).min() - rr < CLR: ok = False; break
                            if min(D[1], E[1]) < rh: ok = False; break
                            if np.hypot(*(E - f[0])) < 0.0: ok = False; break
                        if not ok: continue
                        _, Fl = forces(act, LIFT)
                        cands.append(dict(act, stroke=float(stroke), L=[float(Ls.min()), float(Ls.max())], peak=float(np.abs(Fh).max()),
                                          F_hold100_N=[round(float(np.abs(Fh).min())), round(float(np.abs(Fh).max()))],
                                          F_lift60_N=[round(float(np.abs(Fl).min())), round(float(np.abs(Fl).max()))],
                                          force_curve=dict(z=[round(float(f[0][1]), 3) for f in s[1:-1:10]], hold100=[round(float(abs(x))) for x in Fh[::10]],
                                                           lift60=[round(float(abs(x))) for x in Fl[::10]])))
    return sorted(cands, key=lambda c: c["peak"])

# ---------------------------------------------------------------- body capsules and the per-user check
def cap_d(P, X, Y_, r):
    d = Y_ - X; t = np.clip(((P - X) @ d) / (d @ d), 0, 1); return np.hypot(*(P - (X + t[:, None] * d)).T) - r

def body_caps(pz, sub):
    A, K, Hp = pz["A"], pz["K"], pz["Hp"]; heel = np.array([A[0] - 0.25 * sub.foot_len, 0.035]); toe = np.array([A[0] + 0.75 * sub.foot_len, 0.035])
    return dict(thigh=(Hp, K, pz.get("r_b", 0.09)), calf=(K, A, R_CALF), foot=(heel, toe, R_FOOT))

def user_check(args):
    u, v, act, cv, s, rows = args; sub, path = path_of(u); A, B, c1, c2 = (np.asarray(v[i:i + 2]) for i in (0, 2, 4, 6))
    npre = len(cv[0]) - len(s); res = {}
    def upd(k, d, hz):
        if k not in res or d < res[k][0]: res[k] = (float(d), round(float(hz), 3))
    for r, pz in zip(rows, path):
        if not r.get("contact"): break
        i = min(max(int(r["k"]) - npre, 0), len(s) - 1); f = s[i]
        caps = body_caps(pz, sub); _, br = seat_polys(f[0], f[1], c1, c2)
        brp = poly_pts(br, 0.01)
        for cn in ("calf", "foot"):
            upd("bracket-" + cn, cap_d(brp, *caps[cn]).min(), pz["Hp"][1])
        (D, H, rh), (H2, E, rr), Ept = act_parts(f, act, A, B)
        for cn in ("calf", "foot", "thigh"):
            upd("tube-" + cn, cap_d(np.atleast_2d(Ept), *caps[cn]).min() - R_TUBE, pz["Hp"][1])
        for cn in ("calf", "foot"):
            upd("actuator-" + cn, min(cap_d(seg_pts(D, H), *caps[cn]).min() - rh, cap_d(seg_pts(H2, E), *caps[cn]).min() - rr), pz["Hp"][1])
    return ukey(u), res

if __name__ == "__main__":
    t0 = time.time()
    with Pool() as pool: SY = pool.map(synth, range(4))
    f, x = min(SY); v = np.array(x)
    info, simt = FB2.describe(x); s = [p[:5] for p in FB2.run(x, n=700)]
    bed_w, bed_where = mech_bed_clear(v, s[::5])
    print("synth", round(time.time() - t0), "s cost", round(f, 4), {k: info[k] for k in ("A", "B", "c1", "c2", "L1", "L2", "centre_err_mm", "tilt_err_deg", "transmission_deg", "space_x", "space_z", "phi_max", "phi_end")},
          "bed/floor clearance", round(100 * bed_w, 1), "cm", bed_where)
    cv = with_prefix(np.array([p[0] for p in s]), np.array([p[1] for p in s]))
    with Pool() as pool: R = pool.map(track_user, [(u, cv, PAD_AMAX, dict(r_e=0.03)) for u in USERS])
    real = {k: sm for k, sm, _ in R}; rows = {k: rw for k, _, rw in R}
    cands = actuator_candidates(v, s); print("actuator candidates", len(cands))
    chosen = None; checks = None; best_min = -9.0
    for c in cands[:8]:
        with Pool() as pool: CK = pool.map(user_check, [(u, x, c, cv, s, rows[ukey(u)]) for u in USERS])
        worst = {}
        for k, res in CK:
            for part, (d, hz) in res.items():
                if part not in worst or d < worst[part][0]: worst[part] = (d, hz, k)
        mins = min(w[0] for p, w in worst.items() if p.startswith(("actuator", "tube")))
        print(" cand", c["on"], c["t"], c["o"], c["D"], "peak", round(c["peak"]), "min act/tube clearance", round(100 * mins, 1))
        if mins > best_min: chosen, checks, best_min = c, worst, mins
        if mins >= 0.02: break
    with Pool() as pool: SK = pool.map(stoop_job, [(u, real[ukey(u)].get("release_hz"), real[ukey(u)].get("release_shank")) for u in USERS])
    for u, e in zip(USERS, SK): real[ukey(u)]["E0_release_stooped"] = e
    import seat_cushion as SC
    SC.CVS["v4"] = cv
    cj = [(u, st, ("中硬 v4", 6.0, 6.0, 0.05, 0.0, "v4")) for u in USERS for st in SC.STAGES]
    with Pool() as pool: CR = pool.map(SC.solve_stage, cj)
    lost = {str(st): sum(1 for (u, st2, _), r in zip(cj, CR) if st2 == st and r is None) for st in SC.STAGES}
    # actuator / tube clearance against the bed and floor over the whole travel (no user)
    actbed = 1.0
    for fr in s[::5]:
        (D, H, rh), (H2, E, rr), _ = act_parts(fr, chosen, v[0:2], v[2:4])
        actbed = min(actbed, float(bed_d(seg_pts(D, H)).min()) - rh, float(bed_d(seg_pts(H2, E)).min()) - rr)
    ok = lambda q: bool(q.get("release_hz") and q["fwd_slip_max_cm"] <= 2 and q["min_catch_cm"] >= 0)
    E = [q["E0_release"] for q in real.values()]
    summ = dict(n_ok=sum(ok(q) for q in real.values()), fwd_max=max(q["fwd_slip_max_cm"] for q in real.values()), catch_min=min(q["min_catch_cm"] for q in real.values()),
                E_med=round(float(np.median(E)), 3), E_max=max(E), cushion_lost=lost)
    # frames for the sagittal interference drawing (every part's outline)
    A, B, c1, c2 = v[0:2], v[2:4], v[4:6], v[6:8]; frames = []
    for fr in s[::35] + [s[-1]]:
        plate, br = seat_polys(fr[0], fr[1], c1, c2); (D, H, rh), (H2, Ee, rr), _ = act_parts(fr, chosen, A, B)
        frames.append(dict(Q=np.round(fr[0], 4).tolist(), phi=round(float(fr[1]), 2), P1=np.round(fr[2], 4).tolist(), P2=np.round(fr[3], 4).tolist(),
                           plate=np.round(plate, 4).tolist(), bracket=np.round(br, 4).tolist(), D=np.round(D, 4).tolist(), H=np.round(H, 4).tolist(), E=np.round(Ee, 4).tolist()))
    out = dict(note=__doc__, x=x, mech=dict(info, act={k: val for k, val in chosen.items()}), users=real, summary=summ,
               clearance=dict(rigid_vs_bed_floor_cm=round(100 * bed_w, 1), rigid_vs_bed_where=bed_where, actuator_vs_bed_cm=round(100 * actbed, 1),
                              vs_users={p: dict(cm=round(100 * w[0], 1), hip_z=w[1], user=w[2]) for p, w in checks.items()}),
               frames=frames, Y=Y, sizes=dict(R_ROCK=R_ROCK, R_POST=R_POST, R_HOUS=R_HOUS, R_ROD=R_ROD, R_TUBE=R_TUBE, R_CALF=R_CALF, R_FOOT=R_FOOT, PLATE_T=PLATE_T, LIP=LIP))
    json.dump(out, open(os.path.join(OUT, "layout.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print("summary", summ); print("clearance", out["clearance"]); print("act", {k: val for k, val in chosen.items() if k != "force_curve"})
    print("done", round(time.time() - t0), "s")
