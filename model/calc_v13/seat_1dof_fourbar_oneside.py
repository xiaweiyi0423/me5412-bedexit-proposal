"""v5.3 kill test: a four-bar on the head side only (one side, cantilevered seat) vs the inclined rail + tilt link.

Why: v5 compared a mid-plane four-bar (55/81, blocked by the calves) and a four-bar on both sides (81/81, but both sides
closed so the legs cannot swing back onto the bed, two synchronised actuators). A four-bar on the head side only was never
tried. Its pivots sit below the seat (no 0.58 m inclined rail standing up to 0.80 m), so its housing might be smaller.
Its weak point is expected to be the cantilever: the off-centre seat load must go through revolute joints whose bearing
pairs can only be spread across the housing thickness, and through links bent out of their plane.

Same constraints as the rail design (seat_1dof_slider.py): reach 0.69 m, end tilt 0..8 deg, tilt <= 16 deg over the run,
seat-side pivots >= 80 mm apart, rigid parts >= 1.5 cm off the bed, transmission angle 40..140 deg (FB2.cost).
Out of plane (load 1.5 x 100 kg + 10 kg seat, on the centre line and 10 cm towards the open side, mechanism plane at
y = 0.305 m): the moment M = F * dy (vector along x). Its part perpendicular to the coupler line c1-c2 is taken by a
y-force couple at the two seat pins (Fy = M_perp / |c1c2|); its part along the coupler line is taken as bending moments at
the two pins (half each). Each rocker carries Fy and the pin moment to its ground pivot: bending + torsion in the link,
bearing-pair force = moment / bearing span (60 and 80 mm). Link stress for square steel tubes 40x40x3 and 60x60x4.
Output: seat_1dof/fourbar_oneside.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
from scipy.optimize import differential_evolution
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..'))
import seat_1dof_v5 as V5
import seat_1dof_fourbar2 as FB2
import seat_1dof_layout as LY
import seat_1dof_slider as SL
from seat_1dof_fourbar import with_prefix
from seat_1dof_design import USERS
from model import G

OUT = os.path.join(HERE, "seat_1dof", "fourbar_oneside.json")
TOP = SL.TOP; PHI_END = SL.PHI_END; Y_MECH = 0.305; WALL = 0.02
FB2.TOP = TOP; FB2.run.__defaults__ = (TOP, 600)          # run and its base cost now go to 0.69 m

def cost(v):
    c = V5.cost(v, "sides", None)
    if c >= 1.0: return c
    s = FB2.run(v, n=80)
    ph = np.array([p[1] for p in s])
    return c + 0.05 * max(0, PHI_END[0] - ph[-1]) + 0.05 * max(0, ph[-1] - PHI_END[1])

def synth(seed):
    r = differential_evolution(cost, V5.BOUNDS["sides"], seed=seed, popsize=20, maxiter=400, tol=1e-8, polish=False)
    return float(r.fun), r.x.tolist()

def hull_area(P): x, y = P[:, 0], P[:, 1]; return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def housing(v, s, act):
    """sagittal outline: hull of ground pivots, both rockers and the actuator over the run, floor at 0.04, + 2 cm wall."""
    from seat_1dof_v5_checks import hull
    A, B = np.asarray(v[0:2]), np.asarray(v[2:4]); pts = [A, B]
    for f in s[::8] + [s[-1]]:
        pts += [f[2], f[3]]
        if act:
            (D, H, _), (H2, E, _), _ = LY.act_parts(f, act, A, B); pts += [D, H, H2, E]
    pts = np.array(pts); pts = np.vstack([pts, [[p[0], 0.04] for p in pts]]); Hh = hull(pts); c = Hh.mean(0)
    grow = np.array([p + WALL * (p - c) / np.hypot(*(p - c)) for p in Hh]); grow[:, 1] = np.maximum(grow[:, 1], 0.04)
    return grow

def tube(a, t):
    I = (a ** 4 - (a - 2 * t) ** 4) / 12; W = I / (a / 2); Am = (a - t) ** 2
    return W, Am, t

def cantilever(v, s):
    A, B = np.asarray(v[0:2]), np.asarray(v[2:4]); F = 1.5 * 100 * G + 10 * G; out = {}
    for name, yl in (("载荷在座板中线", 0.0), ("载荷偏向敞开一侧 10 cm", -0.10)):
        M = F * (Y_MECH - yl); w = dict(moment_Nm=round(M), Fy_pin_N=0.0, M_pin_Nm=0.0, M_ground_Nm=0.0, bend_Nm=0.0, torsion_Nm=0.0)
        for f in s[::5]:
            P1, P2 = f[2], f[3]; d = P2 - P1; L = np.hypot(*d); dh = d / L
            M_par = M * abs(dh[0]); M_perp = M * abs(dh[1]); Fy = M_perp / L; Mp = M_par / 2
            for G_, P in ((A, P1), (B, P2)):
                r = P - G_; Lr = np.hypot(*r); ur = r / Lr
                # moment at the ground pivot (x-z plane vector): Fy at arm r -> |r| Fy perpendicular to r; plus the pin moment along d
                m_fy = Fy * Lr * np.array([ur[1], -ur[0]]); m_tot = m_fy + Mp * dh
                bend = abs(m_tot @ np.array([ur[1], -ur[0]])); tors = abs(m_tot @ ur)
                w["M_ground_Nm"] = max(w["M_ground_Nm"], float(np.hypot(*m_tot))); w["bend_Nm"] = max(w["bend_Nm"], float(bend)); w["torsion_Nm"] = max(w["torsion_Nm"], float(tors))
            w["Fy_pin_N"] = max(w["Fy_pin_N"], float(Fy)); w["M_pin_Nm"] = max(w["M_pin_Nm"], float(Mp))
        for b in (0.06, 0.08):
            w[f"bearing_ground_N_b{int(b * 1000)}"] = round(w["M_ground_Nm"] / b); w[f"bearing_pin_N_b{int(b * 1000)}"] = round(w["M_pin_Nm"] / b + w["Fy_pin_N"] / 2)
        for lab, (a, t) in (("40x40x3", (0.040, 0.003)), ("60x60x4", (0.060, 0.004))):
            W, Am, tt = tube(a, t); sig = w["bend_Nm"] / W; tau = w["torsion_Nm"] / (2 * Am * tt)
            w[f"stress_MPa_{lab}"] = round(float(np.sqrt(sig ** 2 + 3 * tau ** 2)) / 1e6)
        out[name] = {k: (round(x) if isinstance(x, float) else x) for k, x in w.items()}
    return out

if __name__ == "__main__":
    t0 = time.time()
    with Pool() as p: SY = p.map(synth, range(4))
    print("costs", sorted(round(c, 4) for c, _ in SY), round(time.time() - t0), "s", flush=True)
    f, v = min(SY); s = FB2.run(v, n=700)
    A, B, c1, c2 = (np.asarray(v[i:i + 2]) for i in (0, 2, 4, 6))
    Qs = np.array([p[0] for p in s]); ph = np.array([p[1] for p in s])
    d = np.hypot(*(Qs[None, :, :] - V5.QT[:, None, :]).transpose(2, 0, 1)); j = d.argmin(1)
    mech = dict(A=np.round(A, 4).tolist(), B=np.round(B, 4).tolist(), c1=np.round(c1, 4).tolist(), c2=np.round(c2, 4).tolist(),
                L1=round(float(np.hypot(*(s[0][2] - A))), 4), L2=round(float(np.hypot(*(s[0][3] - B))), 4), coupler=round(float(np.hypot(*(c1 - c2))), 4),
                centre_err_mm=round(1000 * float(d[np.arange(len(V5.QT)), j].max()), 1), tilt_err_deg=round(float(np.abs(ph[j] - V5.PT).max()), 1),
                top=round(float(Qs[-1][1]), 3), phi_run_max=round(float(ph.max()), 1), phi_end=round(float(ph[-1]), 1), cost=round(f, 4),
                bed_clear_cm=round(100 * float(LY.mech_bed_clear(v, s[::5])[0]), 1))
    print("mech", mech, flush=True)
    act = V5.actuator_search(v, s, "sides", None); print("act", None if act is None else {k: act[k] for k in ("stroke", "L", "F_hold100_N", "F_lift100_N", "F_lift60_N")}, flush=True)
    pins = V5.pin_forces(s, A, c1, c2, 1.5 * 100 * G); mech["pin_forces_N"] = [round(x) for x in pins]
    Hs = housing(v, s, act); box = dict(area_cm2=round(1e4 * hull_area(Hs)), x=[round(float(Hs[:, 0].min()), 3), round(float(Hs[:, 0].max()), 3)],
                                        z_top=round(float(Hs[:, 1].max()), 3), bed_clear_cm=round(100 * float(LY.bed_d(LY.poly_pts(Hs, 0.005)).min()), 1))
    print("box", box, flush=True)
    cant = cantilever(v, s); print("cantilever", json.dumps(cant, ensure_ascii=False), flush=True)
    cv = with_prefix(Qs, ph)
    with Pool() as p: R = dict(p.map(V5.user_job, [(u, cv, "sides", v, act) for u in USERS]))
    vals = [q for q in R.values() if q]; ok = lambda q: bool(q and q["fwd_slip_cm"] <= 2 and q["catch_min_cm"] >= 0)
    E = [q["E_release"] for q in vals if q.get("E_release") is not None]
    summ = dict(n_ok=sum(ok(q) for q in R.values()), fwd_max=max(q["fwd_slip_cm"] for q in vals), catch_min=min(q["catch_min_cm"] for q in vals),
                phi_release_max=max(q["phi_release"] for q in vals), E_rel_med=round(float(np.median(E)), 3), E_rel_max=round(float(max(E)), 3),
                E_sup_max=max(q["E_supported_max"] for q in vals), leg_clear_min_cm=min(q.get("leg_clear_cm", 9) for q in vals))
    print("users", summ, flush=True)
    json.dump(dict(note=__doc__, x=v, mech=mech, act=act, box=box, housing=np.round(Hs, 4).tolist(), cantilever=cant, summary=summ, users=R),
              open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    print("done", round(time.time() - t0), "s")
