"""v5.6 (open audit round 4): 3-D statics of the one-side seat, joint by joint. Replaces the shortcut in
seat_1dof_v5_checks.forces(), which assumed the seat's roll moment reaches the carriage plate and only added the two
moment shares, without the in-plane loads and without asking which joint carries the moment.

Bodies and joints (world frame: x out from the bed, y along the bed (+ head side), z up):
  seat + bracket (rigid)  -- c1: revolute about y at pin 1 (on the carriage plate); a shaft with two bearings a distance s1
                             apart along y carries Fx, Fy, Fz and the moments Mx, Mz (not My)
                          -- link B-c2 with rod ends at both ends: axial force only, in the plane y = Y_link
  carriage plate (rigid)  -- 4 carriages (2 rails x 2), each reacting a force normal to the rail in the rail plane (in-plane,
                             "lateral") and normal to the side plate (y, "radial"); no axial force
                          -- ball-screw nut through a floating joint: axial force only (along the rail)
Load: 100 kg x 1.5 + 10 kg seat, at points along the seat (V5.XOFF) and at y = 0 or 10 cm toward the open side; every 10th
pose along the travel. Directions (round 4b): along the seat normal (as the planar analysis), straight down (a person
dropping onto the tilted seat), and normal +/- 0.3 x the normal force along the seat (friction while shuffling).
The plate is statically indeterminate (9 unknowns, 6 equations): carriage forces = least-norm solution (= equal carriage
stiffness on a rigid plate). The variant "c1 is a plain pin" puts the roll moment into the link instead (link out-of-plane).
Output: seat_1dof/cantilever3d.json
"""
import json, os
import numpy as np
import seat_1dof_slider as SL
import seat_1dof_v5 as V5
import seat_1dof_v5_checks as VC
from seat_trajectory import rot
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "seat_1dof", "cantilever3d.json")
G = 9.81; Y = VC.Y; GAP, SPAN = VC.RAIL_GAP, VC.CARR_SPAN
Y_PLATE = Y["rail"] - 0.0225          # plate mid-plane (plate drawn at y_rail - 0.03 .. - 0.015)
Y_SCREW = Y["rail"] - 0.029

def v3(p, y): return np.array([p[0], y, p[1]])           # (x, z) + y -> 3-D

def solve_seat(Pload, Fload, P1, yc1, P2, B):
    """unknowns: F1 (3), M1x, M1z, T (link axial). Moments about the c1 centre."""
    C1 = v3(P1, yc1); uL = v3(P2 - B, 0.0); uL /= np.linalg.norm(uL); L2 = v3(P2, Y["link"])
    A = np.zeros((6, 6)); b = np.zeros(6)
    A[0:3, 0:3] = np.eye(3); A[0:3, 5] = uL; b[0:3] = -Fload                                   # sum F = 0
    A[3:6, 3] = [1, 0, 0]; A[3:6, 4] = [0, 0, 1]; A[3:6, 5] = np.cross(L2 - C1, uL); b[3:6] = -np.cross(Pload - C1, Fload)
    x = np.linalg.solve(A, b); return x[0:3], np.array([x[3], 0.0, x[4]]), x[5]

def solve_plate(F1, M1, P1, yc1, e, nf):
    """loads from the seat on the plate: -F1 at C1, -M1. Unknowns: 4 carriages x (nf, y) + nut (e)."""
    C1 = v3(P1, yc1); E3, N3, Yh = v3(e, 0), v3(nf, 0), np.array([0, 1.0, 0])
    pts = [v3(P1 + s * e + o * nf, Y["rail"]) for o in (0.0, GAP) for s in (0.0, SPAN)]
    nut = v3(P1 + 0.5 * GAP * nf + 0.5 * SPAN * e, Y_SCREW)
    cols, ref = [], C1
    for p in pts:
        for d in (N3, Yh): cols.append(np.r_[d, np.cross(p - ref, d)])
    cols.append(np.r_[E3, np.cross(nut - ref, E3)]); A = np.array(cols).T
    b = -np.r_[-F1, -M1]
    x = np.linalg.pinv(A) @ b; res = float(np.abs(A @ x - b).max())
    car = x[:8].reshape(4, 2); return car, x[8], res

def bearings(F1, M1, s1):
    """two radial bearings on the c1 shaft, s1 apart along y: radial forces (in the xz plane)."""
    # r = (0, d, 0): r x f = (d fz, 0, -d fx); d = -s1/2, +s1/2
    fz_d = M1[0] / s1; fx_d = -M1[2] / s1           # (fz2 - fz1)/2 * s1 = Mx ... per bearing deviation
    b1 = np.array([F1[0] / 2 - fx_d, F1[2] / 2 - fz_d]); b2 = np.array([F1[0] / 2 + fx_d, F1[2] / 2 + fz_d])
    return max(np.hypot(*b1), np.hypot(*b2))

if __name__ == "__main__":
    J = json.load(open(os.path.join(HERE, "seat_1dof", "slider.json"))); sim, g = SL.simulate(J["x"], 700)
    e = np.array(g["d"]) / np.hypot(*g["d"]); nf = np.array([e[1], -e[0]]); B = np.array(g["B"])
    if (VC.rails()[1][0] - VC.rails()[0][0]) @ nf < 0: nf = -nf               # nf points from rail 1 to rail 2
    yc1 = 0.5 * (Y["wall_in"] - 0.01 + Y_PLATE)                                # c1 shaft centre between slot and plate
    worst = {}
    def upd(k, v, info):
        if v > worst.get(k, (0, None))[0]: worst[k] = (v, info)
    for i in range(0, len(sim), 10):
        Q, phi, P1, P2, s = sim[i]; n_ = rot(phi) @ np.array([0, 1.0])
        for xo in V5.XOFF:
            for yl in (0.0, -0.10):
                Pl = v3(Q + rot(phi) @ np.array([xo, 0]), yl); t_ = rot(phi) @ np.array([1.0, 0])
                for kind, f2 in (("normal", -1.5 * 100 * G * n_), ("vertical", np.array([0, -1.5 * 100 * G])),
                                 ("normal+fwd", -1.5 * 100 * G * (n_ - 0.3 * t_)), ("normal+back", -1.5 * 100 * G * (n_ + 0.3 * t_))):
                  Fl = v3(f2, 0.0) + np.array([0, 0, -10 * G])
                  F1, M1, T = solve_seat(Pl, Fl, P1, yc1, P2, B); car, nut, res = solve_plate(F1, M1, P1, yc1, e, nf)
                  info = dict(z=round(float(Q[1]), 3), xo=xo, y=yl, load=kind)
                  upd("link_axial_N", abs(T), info); upd("nut_axial_N", abs(nut), info); upd("c1_moment_Nm", float(np.hypot(M1[0], M1[2])), info)
                  upd("c1_force_N", float(np.linalg.norm(F1)), info)
                  upd("carriage_radial_y_N", float(np.abs(car[:, 1]).max()), info); upd("carriage_lateral_inplane_N", float(np.abs(car[:, 0]).max()), info)
                  upd("carriage_resultant_N", float(np.hypot(car[:, 0], car[:, 1]).max()), info)
                  for s1 in (0.06, 0.08, 0.10, 0.14): upd(f"c1_bearing_radial_N_s{int(s1 * 1000)}", bearings(F1, M1, s1), info)
                  # variant: c1 a plain pin (no Mx, Mz): a side force at c2 must supply the moment; |M| / (xz distance c1-c2) is the
                  # least side force that could (lower bound; round 4b fixed the old |Mx| / dz, which blew up when dz -> 0)
                  d = v3(P2, Y["link"]) - v3(P1, yc1); Fy_link = float(np.hypot(M1[0], M1[2])) / float(np.hypot(d[0], d[2]))
                  upd("variant_plain_pin_link_side_force_N", Fy_link, info)
    out = {k: dict(value=round(v), at=i) for k, (v, i) in worst.items()}
    out["assumptions"] = dict(c1_shaft_centre_y=round(yc1, 3), plate_y=Y_PLATE, screw_y=Y_SCREW, link_y=Y["link"], rail_y=Y["rail"],
                              carriage_centres="P1, P1 + 0.15 e on rail 1; same + 0.15 nf on rail 2", bearing_spacing_m=[0.06, 0.08, 0.10, 0.14])
    out["old_forces_v5_checks"] = VC.forces()
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    for k, v in out.items(): print(k, v)
