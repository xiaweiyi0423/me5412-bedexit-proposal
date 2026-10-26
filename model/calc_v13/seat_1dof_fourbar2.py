"""Four-bar v3: tuck the linkage under the seat footprint, and drive it with a pivoted linear actuator.

Variants (flat seat, same design curve, run to 0.66 m):
  prev      the v2 four-bar (ground pivots up to 25 cm ahead of the bed edge, bracket 25 cm deep)
  tuck12    ground pivots under the seat footprint (x 0..14 cm), bracket at most 12 cm below the seat top
  tuck20    same ground region, bracket up to 20 cm deep
  fwd6      bracket may reach 6 cm ahead of the cushion front (seat frame longer, cushion unchanged), 12 cm deep
For each: synthesis (arc-free path generation, seat-centre path + tilt error), 81-user check, clearance of the bracket to
the body and of the links to the calves, then a pivoted electric actuator (base pivot D, rod end on rocker A or B):
stroke, retracted length (>= stroke + 12 cm), push force lifting (60 kg, 0.5 BW + 10 kg) and holding (100 kg, 1.5 BW + 10 kg),
and the recommended cushion (6 kPa/cm, 5 cm) support check.
Output: seat_1dof/fourbar2.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_trajectory as ST
from seat_trajectory import rot, Z0, body_points
import seat_1dof_fourbar as F
from seat_1dof_fourbar import QT, PT, sim_partial, with_prefix
from seat_1dof_design import USERS, ukey, path_of, track_user, PAD_AMAX
from model import G

OUT = os.path.join(HERE, "seat_1dof"); TOP = 0.66; HALF = (ST.SEAT_X1 - ST.SEAT_X0) / 2
VARIANTS = {
    "tuck12": dict(g=((0.0, 0.14), (0.05, 0.32)), c=((-0.085, 0.085), (-0.12, -0.03))),
    "tuck20": dict(g=((0.0, 0.14), (0.05, 0.32)), c=((-0.085, 0.085), (-0.20, -0.03))),
    "fwd6":   dict(g=((0.0, 0.20), (0.05, 0.32)), c=((-0.085, 0.145), (-0.12, -0.03))),
    "swept15": dict(g=((0.0, 0.30), (0.05, 0.32)), c=((-0.085, 0.085), (-0.15, -0.03))),
    "swept20": dict(g=((0.0, 0.30), (0.05, 0.32)), c=((-0.085, 0.085), (-0.20, -0.03))),
}
ONLY = [v for v in os.environ.get("VARS", "").split(",") if v]

def run(v, top=TOP, n=600):
    v = np.asarray(v, float); A, B, c1, c2 = v[0:2], v[2:4], v[4:6], v[6:8]
    P10, P20 = QT[0] + c1, QT[0] + c2; L1 = np.hypot(*(P10 - A)); L2 = np.hypot(*(P20 - B))
    if L1 < 0.04 or L2 < 0.04 or np.hypot(*(c1 - c2)) < 0.04: return None
    a0 = np.arctan2(*(P10 - A)[::-1]); best = None
    for sgn in (1, -1):
        s = sim_partial(A, L1, B, L2, c1, c2, a0, a0 + sgn * np.radians(175), n, P20)
        if len(s) < 3: continue
        z = np.array([p[0][1] for p in s])
        if z[2] < z[0] - 1e-4: continue
        if (z >= top).any(): return s[:int(np.argmax(z >= top)) + 1]
        k = int(np.argmax(z)); cand = s[:k + 1]
        if best is None or cand[-1][0][1] > best[-1][0][1]: best = cand
    return best

def cost(v):
    s = run(v, n=80)
    if s is None: return 10.0
    short = max(0.0, TOP - s[-1][0][1])
    if short > 0: return 1.0 + 5 * short
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    d = np.hypot(*(Qs[None, :, :] - QT[:, None, :]).transpose(2, 0, 1)); j = d.argmin(1)
    e_pos = d[np.arange(len(QT)), j].max(); e_ang = 0.10 * np.abs(np.radians(ph[j] - PT)).max()
    B = np.asarray(v[2:4]); pen = 0.0
    for p in s:
        d1 = p[3] - p[2]; d2 = p[3] - B
        ca = abs(d1 @ d2) / (np.hypot(*d1) * np.hypot(*d2) + 1e-12); pen += 5 * max(0, ca - np.cos(np.radians(40))) / len(s)
    pen += 0.05 * max(0.0, -ph.min() - 2.0)          # the seat must not tip backwards
    return e_pos + e_ang + pen

def synth(args):
    name, seed = args; V = VARIANTS[name]
    bounds = [V["g"][0], V["g"][1], V["g"][0], V["g"][1], V["c"][0], V["c"][1], V["c"][0], V["c"][1]]
    r = differential_evolution(cost, bounds, seed=seed, popsize=16, maxiter=260, tol=1e-7, polish=False)
    return name, float(r.fun), r.x.tolist()

def seg_d(P, X, Y):
    d = Y - X; t = np.clip(((P - X) @ d) / (d @ d), 0, 1); return float(np.hypot(*(P - (X + t * d))))

def clearances(args):
    """per user: min distance of links to the calf (5 cm behind the shank line), of the bracket pivots to the body outline,
    and of an actuator line D-E to the calf; at the seat position the user actually has."""
    u, sim, cv, rows, npre, act = args; sub, p = path_of(u); A, B = sim[0][5], sim[0][6]
    calf = 9.0; body = 9.0; actc = 9.0
    for r, pz in zip(rows, p):
        if not r.get("contact"): break
        i = min(max(int(r["k"]) - npre, 0), len(sim) - 1); P1, P2 = sim[i][2], sim[i][3]
        for X, Y in ((A, P1), (B, P2)):
            for t in np.linspace(0, 1, 10): calf = min(calf, seg_d(X + t * (Y - X), pz["A"], pz["K"]) - 0.05)
        pts, kind, aa = body_points(pz)
        for P in (P1, P2): body = min(body, float(np.hypot(*(pts - P).T).min()))
        if act is not None:
            Dp = np.array(act["D"]); E = act_E(sim[i], act)
            for t in np.linspace(0, 1, 10): actc = min(actc, seg_d(Dp + t * (E - Dp), pz["A"], pz["K"]) - 0.05)
    return ukey(u), calf, body, actc

def act_E(frame, act):
    """rod end on rocker `on` (A-P1 or B-P2): fraction t along the rocker plus offset o perpendicular to it."""
    G0, P = (frame[5], frame[2]) if act["on"] == "A" else (frame[6], frame[3])
    d = P - G0; L = np.hypot(*d); e = d / L; nrm = np.array([-e[1], e[0]])
    return G0 + act["t"] * d + act["o"] * nrm

def actuator_search(sim):
    """pivoted linear actuator: base pivot D (in the base, behind the calves), rod end on a rocker."""
    best = None
    HOLD = 1.5 * 100 * G; LIFT = 0.5 * 60 * G
    def forces(act, Fs):
        Ls = np.array([np.hypot(*(act_E(f, act) - np.array(act["D"]))) for f in sim]); out = []
        for i in range(1, len(sim) - 1):
            n_ = rot(sim[i][1]) @ np.array([0.0, 1.0]); Fx = -Fs * n_ + np.array([0, -10 * G])
            dW = -(Fx @ (sim[i + 1][0] - sim[i - 1][0])); dL = Ls[i + 1] - Ls[i - 1]
            out.append(dW / dL if abs(dL) > 1e-7 else np.inf)
        return Ls, np.array(out)
    for on in ("A", "B"):
        for t in (0.4, 0.6, 0.8, 1.0, 1.2):
            for o in (-0.06, -0.03, 0.0, 0.03, 0.06):
                for Dx in np.arange(0.0, 0.201, 0.025):
                    for Dz in (0.04, 0.08, 0.12):
                        act = dict(on=on, t=t, o=o, D=[float(Dx), float(Dz)])
                        Ls, Fh = forces(act, HOLD)
                        stroke = Ls.max() - Ls.min()
                        if stroke > 0.25 or Ls.min() < stroke + 0.12: continue
                        if not np.all(np.isfinite(Fh)) or np.sign(np.diff(Ls)).min() != np.sign(np.diff(Ls)).max(): continue   # monotonic, no dead point
                        E_all = np.array([act_E(f, act) for f in sim])
                        if (E_all[:, 1] < 0.03).any() or ((E_all[:, 0] < 0) & (E_all[:, 1] < Z0)).any(): continue
                        peak = np.abs(Fh).max()
                        if best is None or peak < best[0]:
                            _, Fl = forces(act, LIFT)
                            best = (peak, act, float(stroke), float(Ls.min()), float(Ls.max()), Fh, Fl)
    if best is None: return None
    peak, act, stroke, lmin, lmax, Fh, Fl = best
    return dict(act, stroke=round(stroke, 3), L=[round(lmin, 3), round(lmax, 3)], F_hold100_N=[round(float(np.abs(Fh).min())), round(float(np.abs(Fh).max()))],
                F_lift60_N=[round(float(np.abs(Fl).min())), round(float(np.abs(Fl).max()))],
                push=bool(np.median(Fh) > 0), force_curve=dict(z=[round(float(f[0][1]), 3) for f in sim[1:-1:10]],
                                                              hold100=[round(float(abs(x))) for x in Fh[::10]], lift60=[round(float(abs(x))) for x in Fl[::10]]))

def describe(v):
    s = run(v, n=700); A, B = np.asarray(v[0:2]), np.asarray(v[2:4]); c1, c2 = np.asarray(v[4:6]), np.asarray(v[6:8])
    sim = [(p[0], p[1], p[2], p[3], p[4], A, B) for p in s]
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    d = np.hypot(*(Qs[None, :, :] - QT[:, None, :]).transpose(2, 0, 1)); j = d.argmin(1)
    mus = []
    for p in s:
        d1 = p[3] - p[2]; d2 = p[3] - B; mus.append(float(np.degrees(np.arccos(np.clip(d1 @ d2 / (np.hypot(*d1) * np.hypot(*d2)), -1, 1)))))
    pts = np.array([A, B] + [p[2] for p in s] + [p[3] for p in s])
    # how far the moving pivots stick out of the seat footprint (seat frame x) and below the seat top
    info = dict(A=A.round(4).tolist(), B=B.round(4).tolist(), c1=c1.round(4).tolist(), c2=c2.round(4).tolist(),
                L1=round(float(np.hypot(*(QT[0] + c1 - A))), 4), L2=round(float(np.hypot(*(QT[0] + c2 - B))), 4), coupler=round(float(np.hypot(*(c1 - c2))), 4),
                centre_err_mm=round(1000 * float(d[np.arange(len(QT)), j].max()), 1), tilt_err_deg=round(float(np.abs(ph[j] - PT).max()), 1),
                transmission_deg=[round(min(mus), 1), round(max(mus), 1)], input_sweep_deg=round(float(np.degrees(s[-1][4] - s[0][4])), 1),
                space_x=[round(float(pts[:, 0].min()), 3), round(float(pts[:, 0].max()), 3)], space_z=[round(float(pts[:, 1].min()), 3), round(float(pts[:, 1].max()), 3)],
                bracket_depth_mm=round(-1000 * float(min(c1[1], c2[1])), 0), phi_max=round(float(ph.max()), 1), phi_end=round(float(ph[-1]), 1))
    return info, sim

if __name__ == "__main__":
    t0 = time.time()
    names = ONLY or list(VARIANTS)
    jobs = [(n, s) for n in names for s in range(3)]
    with Pool() as pool: SY = pool.map(synth, jobs)
    best = {}
    for n, f, x in SY:
        if n not in best or f < best[n][0]: best[n] = (f, x)
    if not ONLY:
        prev = json.load(open(os.path.join(OUT, "fourbar.json")))["mech"]["1000.0"]
        best["prev"] = (None, prev["A"] + prev["B"] + prev["c1"] + prev["c2"])
    print("synth", round(time.time() - t0), "s", {k: (None if b[0] is None else round(b[0], 4)) for k, b in best.items()})
    out = dict(note=__doc__, variants={})
    import seat_cushion as SC
    sims = {}; cvs = {}
    for name, (_, x) in best.items():
        info, sim = describe(x); sims[name] = sim
        cvs[name] = with_prefix(np.array([p[0] for p in sim]), np.array([p[1] for p in sim]))
        info["act"] = actuator_search(sim)
        out["variants"][name] = dict(mech=info, x=x)
        print(name, {k: v for k, v in info.items() if k != "act"}, "\n   act", None if info["act"] is None else {k: v for k, v in info["act"].items() if k != "force_curve"})
    # users (rigid) and cushion checks; register the curves for the cushion module before the pool forks
    for name in best: SC.CVS[name] = cvs[name]
    ev = [(name, u) for name in best for u in USERS]
    with Pool() as pool: R = pool.map(track_user, [(u, cvs[n], PAD_AMAX, dict(r_e=0.03)) for n, u in ev])
    rows_by = {}
    for (n, u), (k, s, rows) in zip(ev, R):
        out["variants"][n].setdefault("users", {})[k] = s; rows_by[(n, k)] = rows
    cush = {n: ("中硬 " + n, 6.0, 6.0, 0.05, 0.0, n) for n in best}
    cj = [(u, st, cush[n]) for n in best for u in USERS for st in SC.STAGES]
    with Pool() as pool: CR = pool.map(SC.solve_stage, cj)
    for (u, st, c), r in zip(cj, CR):
        out["variants"][c[5]].setdefault("cushion_rows", []).append(None if r is None else dict(stage=st, sink=r["sink_mm"], p=r["p_peak_kPa"], tau=r["tau_s"]))
    cl = [(u, sims[n], cvs[n], rows_by[(n, ukey(u))], len(cvs[n][0]) - len(sims[n]), out["variants"][n]["mech"]["act"]) for n in best for u in USERS]
    with Pool() as pool: CL = pool.map(clearances, cl)
    for i, n in enumerate([n for n in best for u in USERS]):
        k, calf, body, actc = CL[i]; v = out["variants"][n].setdefault("clear", dict(calf=9.0, body=9.0, act=9.0))
        v["calf"] = min(v["calf"], calf); v["body"] = min(v["body"], body); v["act"] = min(v["act"], actc)
    ok = lambda v: bool(v.get("release_hz") and v["fwd_slip_max_cm"] <= 2 and v["min_catch_cm"] >= 0)
    for n, V in out["variants"].items():
        us = V["users"]; E = [v["E0_release"] for v in us.values()]
        rows = V["cushion_rows"]; lost = {str(s): sum(1 for (u, s2), r in zip([(u, s2) for u in USERS for s2 in SC.STAGES], rows) if s2 == s and r is None) for s in SC.STAGES}
        V["summary"] = dict(n_ok=sum(ok(v) for v in us.values()), fwd_max=max(v["fwd_slip_max_cm"] for v in us.values()),
                            catch_min=min(v["min_catch_cm"] for v in us.values()), E_med=round(float(np.median(E)), 3), E_max=max(E),
                            cushion_lost=lost, clear_calf_cm=round(100 * V["clear"]["calf"], 1), clear_body_cm=round(100 * V["clear"]["body"], 1),
                            clear_act_calf_cm=round(100 * V["clear"]["act"], 1))
        V["mech"]["frames"] = [dict(Q=np.round(p[0], 4).tolist(), phi=round(float(p[1]), 2), P1=np.round(p[2], 4).tolist(), P2=np.round(p[3], 4).tolist()) for p in sims[n][::14]]
        del V["cushion_rows"]
        print(f"{n:8s}", V["summary"])
    path = os.path.join(OUT, "fourbar2.json")
    if ONLY and os.path.exists(path):
        old = json.load(open(path)); old["variants"].update(out["variants"]); out = old
    json.dump(out, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s")
