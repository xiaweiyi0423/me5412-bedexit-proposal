"""v5.7: parts, sections and materials for the CAD model (role 3), with the checks that size them.

Why this file: the CAD sheet of v5.6 gave positions but left the sections "assumed". Sizing them showed one layout problem:
the c1 joint can't be a large crossed-roller bearing. Its centre runs only 69 mm from the bed's side face at the flush position,
so a ring of outside diameter 120 mm (THK RU85, the smallest one strong enough) comes within 0.9 cm of the bed. The bed
clearance rule is 1.5 cm. So c1 becomes a pair of tapered roller bearings, spaced along y in a short steel cartridge welded to
the carriage plate. The cartridge reaches out through the slot in the inner wall, and its outside diameter is 75 mm.

Load: the same design load as the joint statics (seat_1dof_cantilever3d.py): 100 kg x 1.5 at any point on the seat, 0 or 10 cm
toward the open side, in 4 directions (normal / vertical / normal +- 0.3 along the seat), every 10th pose. The moving masses
are now taken from the parts below. Before, the seat and bracket were a flat 10 kg.
Stress rule: von Mises <= yield / 1.5 under the design load. The design load already includes 1.5 x body weight, so the total
margin on yield is 2.25. Deflection budget: the seat's outer corner sinks <= 5 mm in total.
Beam formulas are hand estimates; FEA (role 4) checks the plate parts and the housing box.

Standard-part ratings are distributor figures, to be checked on the maker's catalogue before ordering:
  tapered roller 32006 X (SKF): 30 x 55 x 17 mm, C 35.8 kN, C0 44 kN, Y0 0.8 (distributor tables; Y0 from the e = 0.43 series)
  linear guide HIWIN HGH15CA on HGR15: C 11.38 kN (HIWIN's HG range starts at 11.38 kN), C0 16.97 kN (older HIWIN table,
     not re-checked here); block 34 x 61.4 mm, H 28 mm
  ball screw HIWIN R16-10K3-FSCDIN: Ca 9.1 kN, C0a 19.3 kN (Damen CNC listing of the 2024 HIWIN catalogue)
  rod end SKF SIKAC 10 M: C0 12.2 kN, C 10 kN (RS / Acorn listings)
  brake: spring-applied, 8 N m class (e.g. mayr ROBA-stop-M size 8, rated 8 N m)
Output: seat_1dof/parts.json
"""
import json, os, sys
import numpy as np
from multiprocessing import Pool
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_1dof_v5 as V5
import seat_1dof_v5_checks as VC
import seat_1dof_layout as LY
import seat_trajectory as ST
from seat_trajectory import rot, Seat
from seat_relative_motion import track
from seat_1dof_design import USERS, ukey, path_of, PAD_AMAX
from model import G

OUT = os.path.join(HERE, "seat_1dof", "parts.json")
MAT = {"S355": dict(E=210e9, G=81e9, fy=355e6, rho=7850, name="S355 结构钢"),
       "42CrMo4": dict(E=210e9, G=81e9, fy=650e6, rho=7850, name="42CrMo4 调质"),
       "6061": dict(E=69e9, G=26e9, fy=240e6, rho=2700, name="6061-T6 铝"),
       "304": dict(E=193e9, G=77e9, fy=205e6, rho=8000, name="304 不锈钢")}
SF = 1.5; DEFL_MM = 5.0
W_DES = 1.5 * 100 * G                              # design body load, N
sim, e, nf, Bp = VC.sim, VC.e, VC.nf, VC.Bp
if (VC.rails()[1][0] - VC.rails()[0][0]) @ nf < 0: nf = -nf

# ---------------------------------------------------------------- layer stack across the width (y, m), seat side -> head side
YS = dict(seat_edge=0.220, knuckle=(0.204, 0.216), flange=(0.216, 0.226), brgB=(0.229, 0.246), wall_in=(0.250, 0.253), arm_c2=(0.258, 0.268), link=0.275,
          plate=(0.288, 0.308), brgA=(0.290, 0.307), carriage=0.322, screw=0.322, back=(0.336, 0.351), wall_out=(0.356, 0.358))
yB, yA = np.mean(YS["brgB"]), np.mean(YS["brgA"]); S_BRG = yA - yB; Y_C1 = 0.5 * (yA + yB)

# ---------------------------------------------------------------- sections
def rect_tube(b, h, t):                           # b along the bending axis width, h depth (bending about the axis along b)
    I = (b * h ** 3 - (b - 2 * t) * (h - 2 * t) ** 3) / 12; Am = (b - t) * (h - t); J = 4 * Am ** 2 * t / (2 * (b - t) + 2 * (h - t))
    return dict(A=b * h - (b - 2 * t) * (h - 2 * t), I=I, Z=I / (h / 2), Am=Am, J=J, t=t)
def chs(D, t):
    d = D - 2 * t; I = np.pi * (D ** 4 - d ** 4) / 64; return dict(A=np.pi * (D ** 2 - d ** 2) / 4, I=I, Z=I / (D / 2), J=2 * I, Zp=2 * I / (D / 2))
BEAM = dict(b=0.050, h=0.030, t=0.004, xs=(-0.025, 0.025), zs=(-0.130, -0.100), y=(-0.205, YS["knuckle"][0]))   # seat cross-beam (seat frame)
BEAM_SEC_V = rect_tube(BEAM["b"], BEAM["h"], BEAM["t"]); BEAM_SEC_L = rect_tube(BEAM["h"], BEAM["b"], BEAM["t"])
ARMS = dict(xs=(-0.040, 0.075), zs=(-0.110, -0.100), y=(-0.19, 0.19), sec="扁钢 40 × 10")                           # load-cell arms
CELLS_XS, CELLS_Y = (-0.030, 0.060), 0.19
SHAFT_D = 0.030
CART = dict(D=0.075, d=0.055)                     # c1 cartridge tube outside / bore diameters
PLATE = dict(e=(-0.040, 0.190), nf=(-0.025, 0.175), t=0.020, mat="S355", r_c1=0.042)     # carriage plate, relative to pin 1, (e, nf)
LINK = dict(D=0.020, t=0.002, L=float(VC.M["link"]))

def v3(p, y): return np.array([p[0], y, p[1]])

def solve_seat(Pl, Fl, extra, P1, P2):
    """seat + knuckle + shaft (rigid) on: c1 pair (F1 at Y_C1, Mx, Mz), link B-c2 (axial T). Loads Fl at Pl plus extra=[(P, F)]."""
    C1 = v3(P1, Y_C1); uL = v3(P2 - Bp, 0.0); uL /= np.linalg.norm(uL); L2 = v3(P2, YS["link"])
    Ft = Fl + sum(f for _, f in extra); Mt = np.cross(Pl - C1, Fl) + sum(np.cross(p - C1, f) for p, f in extra)
    A = np.zeros((6, 6)); b = np.zeros(6)
    A[0:3, 0:3] = np.eye(3); A[0:3, 5] = uL; b[0:3] = -Ft
    A[3:6, 3] = [1, 0, 0]; A[3:6, 4] = [0, 0, 1]; A[3:6, 5] = np.cross(L2 - C1, uL); b[3:6] = -Mt
    x = np.linalg.solve(A, b); return x[0:3], np.array([x[3], 0.0, x[4]]), x[5]

def solve_plate(F1, M1, P1, Wp, Pp):
    """carriage plate + cartridge: seat side applies -F1 at C1 and -M1; own weight Wp at Pp. 4 carriages x (nf, y) + nut (e)."""
    C1 = v3(P1, Y_C1); E3, N3, Yh = v3(e, 0), v3(nf, 0), np.array([0, 1.0, 0])
    pts = [v3(P1 + s * e + o * nf, YS["carriage"]) for o in (0.0, VC.RAIL_GAP) for s in (0.0, VC.CARR_SPAN)]
    nut = v3(P1 + 0.5 * VC.RAIL_GAP * nf + 0.5 * VC.CARR_SPAN * e, YS["screw"])
    cols = []
    for p in pts:
        for d in (N3, Yh): cols.append(np.r_[d, np.cross(p - C1, d)])
    cols.append(np.r_[E3, np.cross(nut - C1, E3)]); A = np.array(cols).T
    Fext = -F1 + Wp; Mext = -M1 + np.cross(Pp - C1, Wp)
    x = np.linalg.pinv(A) @ (-np.r_[Fext, Mext]); return x[:8].reshape(4, 2), x[8], float(np.abs(A @ x + np.r_[Fext, Mext]).max())

PBOX = np.array([0.27, 0.30, 0.04])               # base section of the housing box (centre)
def bearing_pair(F1, M1):
    """radial forces on bearing B (seat side, y = yB) and A (plate side, y = yA) of the c1 shaft; F1 at the midpoint."""
    d = S_BRG / 2; fz_d = M1[0] / (2 * d); fx_d = -M1[2] / (2 * d)
    bB = np.hypot(F1[0] / 2 + fx_d, F1[2] / 2 + fz_d); bA = np.hypot(F1[0] / 2 - fx_d, F1[2] / 2 - fz_d)
    return bB, bA, abs(F1[1])

# ---------------------------------------------------------------- masses (kg) and centres (world at the flush pose; seat parts in seat frame)
def seat_parts():
    """seat assembly parts: (name, kg, (xs, y, zs) in the seat frame)."""
    h = 0.085; x0 = -h + V5.LIP; L = 0.44
    foam_r = 0.05 * (-0.02 - (-h)) * L * 60; foam_f = 0.08 * (h + 0.02) * L * 45                 # rebond ~60 kg/m3 equiv. (light), HR 45 kg/m3
    board = 0.012 * (h - x0) * L * 680                                                           # birch plywood 680 kg/m3
    spacer = 0.030 * (-0.02 - x0) * L * 680
    beam = BEAM_SEC_V["A"] * (BEAM["y"][1] - BEAM["y"][0]) * 7850
    arms = 2 * 0.040 * 0.010 * (ARMS["xs"][1] - ARMS["xs"][0]) * 7850
    knuckle = 0.014 * 0.10 * 0.08 * 7850; shaft = np.pi / 4 * SHAFT_D ** 2 * 0.10 * 7850 + np.pi / 4 * 0.07 ** 2 * 0.012 * 7850
    armc2 = 0.010 * 0.040 * 0.13 * 7850; cells = 4 * 0.06; cover = 0.4
    return [("坐垫（两区泡棉 + 面料）", foam_r + foam_f + cover, (0.0, 0.0, -0.04)), ("座板底板 12 mm + 后区垫条", board + spacer, (0.02, 0.0, -0.086)),
            ("横梁 50×30×4", beam, (0.0, np.mean(BEAM["y"]), -0.115)), ("称重支臂 ×2", arms, (0.012, 0.0, -0.105)), ("称重单元 ×4", cells, (0.012, 0.0, -0.096)),
            ("节点板 + 铰点 1 轴", knuckle + shaft, (0.008, 0.25, -0.07)), ("铰点 2 摆臂", armc2, (-0.008, YS["arm_c2"][0], -0.126))]

def plate_parts():
    """carriage weldment etc., in (e, nf) relative to pin 1 and y."""
    pa = (PLATE["e"][1] - PLATE["e"][0]) * (PLATE["nf"][1] - PLATE["nf"][0]) * PLATE["t"] * 7850
    cart = np.pi / 4 * (CART["D"] ** 2 - CART["d"] ** 2) * (yA - yB + 0.017) * 7850
    brg = 2 * 0.178; car = 4 * 0.18; nut = 0.35
    return [("滑块板 20 mm", pa, (0.075, 0.075, np.mean(YS["plate"]))), ("轴承座筒", cart, (0.0, 0.0, Y_C1)), ("圆锥滚子轴承 ×2", brg, (0.0, 0.0, Y_C1)),
            ("滑块 ×4", car, (0.075, 0.075, YS["carriage"])), ("丝杠螺母 + 浮动接头", nut, (0.075, 0.075, YS["screw"]))]

def worst_statics():
    sp = seat_parts(); m_seat = sum(m for _, m, _ in sp); cs = np.array([m * np.array(c) for _, m, c in sp]).sum(0) / m_seat
    pp = plate_parts(); m_plate = sum(m for _, m, _ in pp); cp = np.array([m * np.array(c) for _, m, c in pp]).sum(0) / m_plate
    W = {}; CASE = {}; cur = {}
    def upd(k, v, info):
        if v > W.get(k, (-1, None))[0]:
            W[k] = (v, info)
            if k in ("c1_moment_Nm", "brg_P0_N", "carriage_P0_N", "housing_Mx_Nm", "beam_vm_MPa"): CASE[k] = {kk: (np.round(vv, 1).tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in cur.items()}
    for i in range(0, len(sim), 10):
        Q, phi, P1, P2, s = sim[i]; R = rot(phi); n_ = R @ np.array([0, 1.0]); t_ = R @ np.array([1.0, 0])
        Pseat = v3(Q + R @ np.array([cs[0], cs[2]]), cs[1]); Wseat = np.array([0, 0, -m_seat * G])
        Pplate = v3(P1 + cp[0] * e + cp[1] * nf, cp[2]); Wplate = np.array([0, 0, -m_plate * G])
        for xo in V5.XOFF:
            for yl in (0.0, -0.10):
                Pl = v3(Q + R @ np.array([xo, 0]), yl)
                for kind, f2, fy in (("normal", -W_DES * n_, 0.0), ("vertical", np.array([0, -W_DES]), 0.0), ("normal+fwd", -W_DES * (n_ - 0.3 * t_), 0.0),
                                     ("normal+back", -W_DES * (n_ + 0.3 * t_), 0.0), ("normal+side_open", -W_DES * n_, -0.3 * W_DES), ("normal+side_head", -W_DES * n_, 0.3 * W_DES)):
                    Fl = v3(f2, 0.0) + np.array([0, fy, 0]); info = dict(z=round(float(Q[1]), 3), xo=xo, y=yl, load=kind)
                    F1, M1, T = solve_seat(Pl, Fl, [(Pseat, Wseat)], P1, P2); car, nut, res = solve_plate(F1, M1, P1, Wplate, Pplate)
                    cur.clear(); cur.update(pose=dict(stroke_mm=round(1000 * float(s - sim[0][4]), 1), Q_mm=np.round(1000 * Q, 1).tolist(), phi=round(float(phi), 2)),
                               load_point_mm=1000 * Pl, load_N=Fl, c1_centre_mm=1000 * v3(P1, Y_C1), F1_N=F1, M1_Nm=M1, link_N=round(float(T), 1),
                               carriages_nf_y_N=car, carriage_points_mm=[np.round(1000 * v3(P1 + s_ * e + o * nf, YS["carriage"]), 1).tolist() for o in (0.0, VC.RAIL_GAP) for s_ in (0.0, VC.CARR_SPAN)],
                               nut_N=round(float(nut), 1), seat_weight_N=round(float(m_seat * G), 1), plate_weight_N=round(float(m_plate * G), 1))
                    bB, bA, Fa = bearing_pair(F1, M1)
                    Mh = np.cross(Pl - PBOX, Fl) + np.cross(Pseat - PBOX, Wseat) + np.cross(Pplate - PBOX, Wplate)
                    upd("housing_Mx_Nm", abs(Mh[0]), info); upd("housing_Mz_Nm", abs(Mh[2]), info)
                    upd("link_tension_N", T, info); upd("link_compression_N", -T, info); upd("nut_axial_N", abs(nut), info)
                    upd("c1_moment_Nm", float(np.hypot(M1[0], M1[2])), info); upd("c1_force_N", float(np.linalg.norm(F1)), info)
                    P0B = max(bB, 0.5 * bB + 0.8 * (Fa + 0.5 * bA / 1.4)); P0A = max(bA, 0.5 * bA + 0.8 * (Fa + 0.5 * bB / 1.4))
                    upd("brgB_radial_N", bB, info); upd("brgA_radial_N", bA, info); upd("brg_axial_N", Fa, info); upd("brg_P0_N", max(P0A, P0B), info)
                    upd("carriage_radial_y_N", float(np.abs(car[:, 1]).max()), info); upd("carriage_lateral_inplane_N", float(np.abs(car[:, 0]).max()), info)
                    upd("carriage_P0_N", float((np.abs(car[:, 0]) + np.abs(car[:, 1])).max()), info)
                    # shaft bending at bearing B: seat loads outboard of B (the link acts between the bearings)
                    CB = v3(P1, yB); Mb = np.cross(Pl - CB, Fl) + np.cross(Pseat - CB, Wseat); upd("shaft_M_at_B_Nm", float(np.hypot(Mb[0], Mb[2])), info)
                    upd("shaft_torsion_Nm", abs(Mb[1]), info)
                    # cross-beam root (y = knuckle face), in seat axes; only the body load (seat parts' weight is small and spread)
                    Cr = v3(Q + R @ np.array([np.mean(BEAM["xs"]), np.mean(BEAM["zs"])]), BEAM["y"][1]); Mr = np.cross(Pl - Cr, Fl)
                    ex = v3(t_, 0); ez = v3(n_, 0)
                    upd("beam_M_vert_Nm", abs(Mr @ ex), info); upd("beam_M_lat_Nm", abs(Mr @ ez), info); upd("beam_T_Nm", abs(Mr[1]), info)
                    sv = abs(Mr @ ex) / BEAM_SEC_V["Z"] + abs(Mr @ ez) / BEAM_SEC_L["Z"]; tau = abs(Mr[1]) / (2 * BEAM_SEC_V["Am"] * BEAM["t"])
                    upd("beam_vm_MPa", float(np.sqrt(sv ** 2 + 3 * tau ** 2)) / 1e6, info)
                    # seat outer corner (y -0.22, front edge xs 0.085): bending + twist of the cross-beam, normal component only
                    Fn = abs(Fl @ ez); a = BEAM["y"][1] - yl; Lc = BEAM["y"][1] + 0.22; EI = MAT["S355"]["E"] * BEAM_SEC_V["I"]
                    dz = Fn * a ** 2 * (3 * Lc - a) / (6 * EI); twist = Fn * abs(xo - np.mean(BEAM["xs"])) * a / (MAT["S355"]["G"] * BEAM_SEC_V["J"])
                    upd("beam_corner_mm", 1000 * (dz + twist * (0.085 - np.mean(BEAM["xs"]))), info)
    out = {k: dict(value=round(float(v), 1 if "MPa" in k or "mm" in k else 0), at=i) for k, (v, i) in W.items()}
    out["cases"] = CASE
    return out, dict(seat_kg=round(m_seat, 2), seat_com_seat_frame=np.round(cs, 3).tolist(), plate_kg=round(m_plate, 2), seat_parts=sp, plate_parts=pp)

# ---------------------------------------------------------------- envelopes: the parts' real footprints in the side view
def beam_poly(): (x0, x1), (z0, z1) = BEAM["xs"], BEAM["zs"]; return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
def under_seat_poly():
    """board + arms + cross-beam, seat frame: replaces the old bracket hull (which ran down to pin 2 under the whole seat).
    Pin 2 and its arm sit beside the seat edge (y 0.258 - 0.268), out of the legs' way."""
    h = 0.085; pts = [(-h + V5.LIP, -0.080), (h, -0.080), (h, -0.092), (ARMS["xs"][1], -0.092), (ARMS["xs"][1], ARMS["zs"][0]), (BEAM["xs"][1], ARMS["zs"][0]),
                      (BEAM["xs"][1], BEAM["zs"][0]), (BEAM["xs"][0], BEAM["zs"][0]), (BEAM["xs"][0], ARMS["zs"][0]), (ARMS["xs"][0], ARMS["zs"][0]),
                      (ARMS["xs"][0], -0.092), (-h + V5.LIP, -0.092)]
    return [np.array(p) for p in pts]

def legs_job(u):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(u); rows = track(sub, path, Seat(r_e=0.03), VC.cv); dmin = 9.0; zi = None; poly = under_seat_poly()
    for i, pz in enumerate(path):
        r = rows[i] if i < len(rows) else None
        if r and r.get("contact") and r.get("ok"): zi = min(max(int(r["k"]) - VC.npre, 0), len(sim) - 1)
        if zi is None: continue
        Q, phi = sim[zi][0], sim[zi][1]; body, _ = VC.seat_body(Q, phi); W_ = np.array([Q + rot(phi) @ p for p in poly]); caps = LY.body_caps(pz, sub)
        for pg in (body, W_):
            pts = LY.poly_pts(pg, 0.005)
            for cn in ("calf", "foot"): dmin = min(dmin, float(LY.cap_d(pts, *caps[cn]).min()))
    return ukey(u), round(100 * dmin, 1)

R_C2 = 0.015                                       # pin-2 end: rod-end head <= 30 dia, arm end 30 wide
def disc(c, r, n=36): a = np.linspace(0, 2 * np.pi, n, endpoint=False); return [c + r * np.array([np.cos(t), np.sin(t)]) for t in a]
GAP_WALL = 0.008                                   # 5 mm running gap + 3 mm wall
def housing_parts(gap=0.005, wall=0.003, raw=False):
    """side-view outline from the parts: rails (+-10 mm), carriage plate over the travel, c1 cartridge, pin-2 arm and rod end, link sweep
    (+-15 mm), pivot B bracket, screw top stack (fixed support, pulley, brake, limiter) and motor; + gap + wall; floor 0.04."""
    (a1, b1), (a2, b2) = VC.rails(); pts = []
    for a, b in ((a1, b1), (a2, b2)):
        for q in (a, b): pts += [q + 0.010 * nf, q - 0.010 * nf]
    for f in sim[::5] + [sim[-1]]:
        P1, P2 = f[2], f[3]
        for de in PLATE["e"]:
            for dn in PLATE["nf"]:
                if de < 0 and dn < 0: continue                                                        # corner next to pin 1: rounded (r_c1)
                pts.append(P1 + de * e + dn * nf)
        pts += [P1 + PLATE["r_c1"] * (np.cos(a) * -e + np.sin(a) * -nf) for a in np.linspace(0, np.pi / 2, 7)]
        pts += disc(P1, CART["D"] / 2); pts += disc(P2, R_C2, 12)
        d = (P2 - Bp) / np.linalg.norm(P2 - Bp); nn = np.array([-d[1], d[0]]); pts += [P2 + 0.012 * nn, P2 - 0.012 * nn]
    pts += disc(Bp, 0.025, 12)
    top = b1 + 0.5 * VC.RAIL_GAP * nf - 0.06 * e                                                  # screw top end (as v5.6)
    for de, dn in ((0.0, -0.055), (0.0, 0.055), (0.07, -0.055), (0.07, 0.055)): pts.append(top + de * e + dn * nf)   # brake 8 N m (~108 dia) + limiter
    mot = top - 0.03 * e + 0.075 * nf                                                              # motor beside the screw toward rail 2, belt 1:3
    for de, dn in ((-0.10, -0.03), (0.02, -0.03), (-0.10, 0.03), (0.02, 0.03)): pts.append(mot + de * e + dn * nf)
    pts = np.array(pts)
    if raw: return pts
    pts = np.vstack([pts, [[p[0], 0.04] for p in pts]])
    Hh = VC.hull(pts); c = Hh.mean(0); g = gap + wall
    grow = np.array([p + g * (p - c) / np.hypot(*(p - c)) for p in Hh]); grow[:, 1] = np.maximum(grow[:, 1], 0.04)
    return grow

def housing_box(Mx, Mz):
    """housing as a box beam standing on the base: inner wall (steel 2 mm, y 0.250) and back plate (6061-T6 15 mm, y 0.336 - 0.351)
    as flanges, perimeter walls (steel 2 mm) as webs; length along x at the base 0.50 m. Roll moment Mx bends it about x;
    corner drop = rotation at the carriage height x lever to the seat's outer corner. Above z ~ 0.30 the slot cuts the inner wall:
    FEA must check that part. Mz twists the closed box."""
    L = 0.50; Es, Ea = 210e9, 69e9; yi, yb = 0.251, 0.3435; Ai, Ab = L * 0.002, L * 0.015
    yc = (Es * Ai * yi + Ea * Ab * yb) / (Es * Ai + Ea * Ab); EI = Es * Ai * (yi - yc) ** 2 + Ea * Ab * (yb - yc) ** 2 + Ea * L * 0.015 ** 3 / 12
    h = 0.46; th = Mx * h / EI; lever = yc + 0.22
    Am = L * (yb - yi); sum_s_t = L / 0.002 + L / (0.015 * Ea / Es) + 2 * (yb - yi) / 0.002; GJ = 81e9 * 4 * Am ** 2 / sum_s_t; tz = Mz * h / GJ
    return dict(EI_MNm2=round(EI / 1e6, 2), roll_rad=round(th, 5), corner_mm=round(1000 * th * lever, 2), twist_rad=round(tz, 5), twist_corner_mm=round(1000 * tz * 0.35, 2),
                flange_stress_MPa=round(Mx * max(abs(yi - yc), abs(yb - yc)) / EI * Es / 1e6))

def deflection_budget(W, plate_mm, box_mm):
    """seat outer corner (y -0.22, front edge) under the design load: sum of the parts. Bearing and carriage stiffness are assumed
    values (catalogue rigidity to be checked): preloaded 32006 X 400 N/um radial each; HGH15CA 200 N/um."""
    lever_c1 = Y_C1 + 0.22
    brg = (W["brgA_radial_N"]["value"] + W["brgB_radial_N"]["value"]) / 400e6 / S_BRG * lever_c1
    car = 2 * W["carriage_radial_y_N"]["value"] / 200e6 / VC.CARR_SPAN * (YS["carriage"] + 0.22)
    rows = [("座板横梁弯曲 + 扭转", W["beam_corner_mm"]["value"]), ("铰点 1 轴承对（假设径向刚度 400 N/µm）", round(1000 * brg, 2)),
            ("铰点 1 轴（Ø30，短）", 0.1), ("滑块板 S355 20（窄条估算，偏保守）", plate_mm), ("滑块和导轨（假设 200 N/µm）", round(1000 * car, 2)), ("机构箱盒体（底部，未计竖槽）", box_mm)]
    return dict(rows=rows, total_mm=round(sum(v for _, v in rows), 2), limit_mm=DEFL_MM)

def poly_area(P): x, z = P[:, 0], P[:, 1]; return 0.5 * abs(np.dot(x, np.roll(z, -1)) - np.dot(z, np.roll(x, -1)))

# ---------------------------------------------------------------- the rest of the parts (simple formulas)
def link_check(Tt, Tc):
    s = chs(LINK["D"], LINK["t"]); E = MAT["S355"]["E"]; Pcr = np.pi ** 2 * E * s["I"] / LINK["L"] ** 2
    return dict(section="Ø20 × 2 钢管 + 两端 M10 杆端关节轴承", stress_MPa=round(max(Tt, Tc) / s["A"] / 1e6, 1), euler_kN=round(Pcr / 1000, 1),
                buckling_sf=round(Pcr / max(Tc, 1), 1), rod_end_sf=round(12.2e3 / max(Tt, Tc), 1))

def shaft_check(Mb, T):
    d = SHAFT_D; s = 32 * Mb / (np.pi * d ** 3); t = 16 * T / (np.pi * d ** 3); vm = np.sqrt(s ** 2 + 3 * t ** 2)
    return dict(d_mm=1000 * d, mat="42CrMo4 调质（屈服 ≥ 650 MPa）", vm_MPa=round(vm / 1e6), allow_MPa=round(MAT["42CrMo4"]["fy"] / SF / 1e6), ok=bool(vm < MAT["42CrMo4"]["fy"] / SF))

def plate_check(car_P0):
    """carriage plate: the far carriage's force has to come through the plate from the cartridge. Narrow-strip cantilever (60 mm wide,
    from the cartridge edge to the far carriage, 0.15 - 0.04 m): conservative; FEA to confirm."""
    F = 1.3 * car_P0; L = VC.CARR_SPAN - CART["D"] / 2; b = 0.06; out = {}
    for nm, mat, t in (("S355 钢板 15", "S355", 0.015), ("S355 钢板 20", "S355", 0.020), ("6061-T6 铝板 25", "6061", 0.025)):
        I = b * t ** 3 / 12; M = F * L; s = M / (b * t ** 2 / 6); d = F * L ** 3 / (3 * MAT[mat]["E"] * I)
        theta = d / VC.CARR_SPAN; corner = theta * 0.50                                              # plate rotation x lever to the seat corner
        out[nm] = dict(stress_MPa=round(s / 1e6), allow_MPa=round(MAT[mat]["fy"] / SF / 1e6), corner_mm=round(1000 * corner, 2))
    return out

def screw_drive(nut_N, m_move):
    lead = 0.010; eta_s, eta_b, ratio = 0.90, 0.95, 3.0
    F_lift = 664 + (m_move - 10) * G * abs(e[1]) + 20                                            # lift 0.5 BW (sizing slide) + extra moving mass + seal
    T_screw = F_lift * lead / (2 * np.pi * eta_s); T_motor = T_screw / (ratio * eta_b); rpm_s = 0.03 / lead * 60
    dr = 0.0129; L = 0.45; I = np.pi * dr ** 4 / 64; A = np.pi * dr ** 2 / 4; E = 206e9
    Pcr = 2.0 * np.pi ** 2 * E * I / L ** 2                                                         # fixed - supported, if ever in compression
    w = 3.927 ** 2 / L ** 2 * np.sqrt(E * I / (7850 * A)); n_crit = w * 60 / (2 * np.pi)
    life_rev = (9.1e3 / (1.2 * 700)) ** 3 * 1e6; cycles = life_rev / (2 * VC.M["stroke"] / lead)
    return dict(screw="滚珠丝杠 Ø16 导程 10（HIWIN R16-10K3-FSCDIN 或同级），螺纹长约 400，总长约 500；上端固定支撑 BK12，下端浮动支撑 BF12",
                static_sf=round(19.3e3 / nut_N, 1), lift_force_N=round(F_lift), screw_torque_Nm=round(T_screw, 2), motor_torque_Nm=round(T_motor, 2),
                screw_rpm=round(rpm_s), motor_rpm=round(rpm_s * ratio), motor_power_W=round(T_motor * rpm_s * ratio * 2 * np.pi / 60),
                euler_kN=round(Pcr / 1000, 1), crit_rpm=round(n_crit), life_cycles=f"{cycles:.1e}",
                motor="24 V 无刷直流电机，57 机座，额定 ≥ 0.6 N·m（需 0.46，留 30%）、≥ 600 r/min（约 100 W 级），带编码器；同步带 HTD-5M 宽 15，15T/45T（1:3）",
                brake=f"失电常闭制动器装在丝杠上端，额定 8 N·m（需 ≥ {2 * nut_N * lead / (2 * np.pi):.1f}），带手动释放拉索；离心限速器也在丝杠上（180 r/min）",
                note="固定端在上：人坐在座板上时丝杠受拉，不会失稳；Euler 值只在万一受压时用")

def handrail_check():
    F = 1.5 * 1112.0; a = 0.35; H = 0.95 - 0.035; out = {}
    for pnm, mat, b, t in (("方管 50×50×4", "S355", 0.05, 0.004), ("方管 60×60×4", "S355", 0.06, 0.004)):
        s = rect_tube(b, b, t); E, Gm = MAT[mat]["E"], MAT[mat]["G"]
        M_base = F * H; T_post = F * a; sig = M_base / s["Z"]; tau = T_post / (2 * s["Am"] * t); vm = np.sqrt(sig ** 2 + 3 * tau ** 2)
        d_pull = F * H ** 3 / (3 * E * s["I"]) + (F * a * H / (Gm * s["J"])) * a
        out[pnm] = dict(base_moment_Nm=round(M_base), vm_MPa=round(vm / 1e6), allow_MPa=round(MAT[mat]["fy"] / SF / 1e6), tip_pull_mm=round(1000 * d_pull, 1))
    bar = {}
    for bnm, mat, D, t in (("圆管 Ø38×3（S355 喷塑）", "S355", 0.038, 0.003), ("圆管 Ø38×4（S355 喷塑）", "S355", 0.038, 0.004), ("圆管 Ø38×2（304 不锈钢）", "304", 0.038, 0.002), ("圆管 Ø42.4×3.2（S355 喷塑）", "S355", 0.0424, 0.0032)):
        s = chs(D, t); sig = F * a / s["Z"]; bar[bnm] = dict(stress_MPa=round(sig / 1e6), allow_MPa=round(MAT[mat]["fy"] / SF / 1e6), tip_mm=round(1000 * F * a ** 3 / (3 * MAT[mat]["E"] * s["I"]), 1))
    return dict(load_N=round(F), post=out, bar=bar)

def footplate_check():
    P = W_DES; L = 0.42; b = 0.42; out = {}
    for t in (0.008, 0.010):
        I = b * t ** 3 / 12; d = 2 * P * L ** 3 / (48 * MAT["6061"]["E"] * I); s = 2 * (P * L / 4) / (b * t ** 2 / 6)   # x2 for corner supports
        out[f"{int(t * 1000)} mm"] = dict(defl_mm=round(1000 * d, 1), stress_MPa=round(s / 1e6))
    return out

def cells_check():
    """4 cells under the seat board (rigid board, equal cells). Force range per cell for the design load anywhere on the board plus 0.3
    friction along the seat (acting 92 mm above the cell plane)."""
    xs = np.array([x for x in CELLS_XS for _ in (0, 1)]); ys = np.array([y for _ in CELLS_XS for y in (-CELLS_Y, CELLS_Y)])
    xm = xs.mean(); Sx = ((xs - xm) ** 2).sum(); Sy = (ys ** 2).sum(); lo, hi = 0.0, 0.0
    for xo in np.linspace(-0.04, 0.085, 11):
        for yo in np.linspace(-0.22, 0.22, 9):
            for ft in (-0.3, 0.0, 0.3):
                Mfric = ft * W_DES * 0.092; f = W_DES * (0.25 + (xs - xm) * (xo - xm) / Sx + ys * yo / Sy) + Mfric * (xs - xm) / Sx
                lo, hi = min(lo, f.min()), max(hi, f.max())
    return dict(positions_seat_frame=dict(x=list(CELLS_XS), y=[-CELLS_Y, CELLS_Y]), max_N=round(hi), min_N=round(lo),
                spec=f"4 只，高度 ≤ 8 mm；每只量程 ≥ {int(np.ceil(hi / G / 1.5 / 10) * 10)} kg（设计载荷 ≤ 150% 安全过载）；会被向上拔（最小 {lo:.0f} N），要用螺栓固定的平行梁式，或加防掀限位")

def cushion_spec():
    out = {}
    for nm, k, t in (("后区（x_s < −20 mm，含 45 mm 软唇边）", 10, 0.05), ("前区", 3, 0.08)):
        out[nm] = dict(k_kPa_per_cm=k, thick_mm=int(t * 1000), E_kPa=round(k * 100 * t), cv40_kPa=round(k * 0.4 * t * 100, 1))
    return out

if __name__ == "__main__":
    W, M = worst_statics()
    with Pool() as p: LG = dict(p.map(legs_job, USERS))
    Hs = housing_parts(); Hold = np.array(json.load(open(os.path.join(HERE, "seat_1dof", "v5_checks.json")))["rail"]["housing"])
    raw = housing_parts(raw=True); dr = LY.bed_d(raw); bed_h = float(dr.min()) - GAP_WALL; bed_pt = np.round(raw[dr.argmin()], 3).tolist(); bed_seat = 9.0; floor_seat = 9.0
    for f in sim:
        W_ = np.array([f[0] + rot(f[1]) @ p for p in under_seat_poly()]); pts = LY.poly_pts(W_, 0.003)
        bed_seat = min(bed_seat, float(LY.bed_d(pts).min())); floor_seat = min(floor_seat, float(pts[:, 1].min()))
        bed_seat = min(bed_seat, float(LY.bed_d(np.array(disc(f[2], CART["D"] / 2))).min()))
    # moving mass and the device mass / centre of mass (for the tipping check)
    m_move = M["seat_kg"] + M["plate_kg"] + 0.6
    ar = poly_area(Hs); wall_kg = (2 * ar * 0.002 + 0.11 * 2.2 * 0.002) * 7850; back_kg = ar * 0.015 * 2700
    dev = [("座板活动件", m_move, (0.15, 0.10, 0.45)), ("机构箱侧板 15 mm 铝", back_kg, (0.27, 0.344, 0.40)), ("机构箱内外壁和周边 2 mm 钢", wall_kg, (0.27, 0.30, 0.40)),
           ("导轨 2 根 + 丝杠 + 支撑", 2 * 0.58 * 1.38 + 1.4 + 1.0, (0.27, 0.33, 0.50)), ("电机 + 制动器 + 限速器 + 带", 1.4 + 1.2 + 0.5 + 0.3, (0.40, 0.31, 0.72)),
           ("连杆 + B 支座", 0.6, (0.40, 0.272, 0.25)), ("底座框 60×30×3", 4.0 * (2 * 0.75 + 3 * 0.65) * 1.0, (0.40, 0.055, 0.017)),
           ("踏板 10 mm 铝 + 胶垫 + 4 称重", 0.42 * 0.44 * 0.010 * 2700 + 0.6 + 0.4, (0.41, 0.0, 0.04)), ("扶手立柱 + 横杆", 0.915 * 6.93 + 0.35 * 2.59 + 0.5, (0.70, 0.22, 0.55)),
           ("控制器 + 电池", 2.5, (0.30, 0.31, 0.15))]
    m_dev = sum(m for _, m, _ in dev); com = np.array([m * np.array(c) for _, m, c in dev]).sum(0) / m_dev
    tip = VC.tipping(dev_kg=round(m_dev, 1), dev_com=(round(float(com[0]), 3), round(float(com[1]), 3)))
    em = VC.emergency(belt=3.0)
    PC = plate_check(W["carriage_P0_N"]["value"]); HB = housing_box(W["housing_Mx_Nm"]["value"], W["housing_Mz_Nm"]["value"])
    T = dict(tension=W["link_tension_N"]["value"], compression=W["link_compression_N"]["value"])
    out = dict(note=__doc__, y_stack=YS, bearing_spacing_m=round(S_BRG, 4), c1_centre_y=round(Y_C1, 4), materials={k: v["name"] for k, v in MAT.items()},
               statics={k: v for k, v in W.items() if k != "cases"}, cases=W["cases"], frame_dirs=dict(e=np.round(e, 4).tolist(), nf=np.round(nf, 4).tolist()), masses=dict(seat_kg=M["seat_kg"], plate_kg=M["plate_kg"], moving_kg=round(m_move, 1), seat_parts=[(n, round(m, 2)) for n, m, _ in M["seat_parts"]],
                                      plate_parts=[(n, round(m, 2)) for n, m, _ in M["plate_parts"]], device=[(n, round(m, 1), [round(float(v), 3) for v in c]) for n, m, c in dev],
                                      device_kg=round(m_dev, 1), device_com=np.round(com, 3).tolist()),
               beam=dict(section="矩形管 50 × 30 × 4（S355），宽 50 沿 x_s、高 30 沿 z_s", xs=BEAM["xs"], zs=BEAM["zs"], y=BEAM["y"], vm_MPa=W["beam_vm_MPa"]["value"],
                         allow_MPa=round(355 / SF), corner_mm=W["beam_corner_mm"]["value"]),
               c1=dict(bearings="圆锥滚子轴承 32006 X ×2（30×55×17，背对背，KM6 锁紧螺母预紧）", spacing_mm=round(1000 * S_BRG, 1), C0_kN=44.0,
                       P0_kN=round(W["brg_P0_N"]["value"] / 1000, 1), sf=round(44e3 / W["brg_P0_N"]["value"], 2),
                       cartridge=f"钢管 Ø{CART['D'] * 1000:.0f} / 内孔 Ø{CART['d'] * 1000:.0f}，焊在滑块板上后一起精加工两个轴承孔；中段开 60° 窗口让铰点 2 摆臂穿出",
                       shaft=shaft_check(W["shaft_M_at_B_Nm"]["value"], W["shaft_torsion_Nm"]["value"]),
                       why_not_crossed_roller=dict(RU66=dict(OD_mm=95, dp_mm=66, C0_kN=22.3, P0_kN=round((W["c1_force_N"]["value"] + 2 * W["c1_moment_Nm"]["value"] / 0.066) / 1000, 1)),
                                                   RU85=dict(OD_mm=120, dp_mm=85, C0_kN=29.5, bed_gap_cm=0.9))),
               link=link_check(T["tension"], T["compression"]), link_forces_N=T, carriage=dict(model="HIWIN HGH15CA ×4 on HGR15 ×2", C0_kN=16.97,
                    P0_kN=round(W["carriage_P0_N"]["value"] / 1000, 2), P0_x13_kN=round(1.3 * W["carriage_P0_N"]["value"] / 1000, 2), sf=round(16.97e3 / (1.3 * W["carriage_P0_N"]["value"]), 2)),
               plate=PC, housing_box=HB, deflection=deflection_budget(W, PC["S355 钢板 20"]["corner_mm"], HB["corner_mm"]), drive=screw_drive(W["nut_axial_N"]["value"], m_move), emergency_belt3=em,
               handrail=handrail_check(), footplate=footplate_check(), cells=cells_check(), cushion=cushion_spec(),
               clearances=dict(legs_min_cm=min(LG.values()), legs_worst=min(LG, key=LG.get), legs_old_cm=json.load(open(os.path.join(HERE, "seat_1dof", "v5_checks.json")))["bracket_vs_legs_cm"]["min"],
                               housing_bed_cm=round(100 * bed_h, 1), housing_bed_point=bed_pt, seat_parts_bed_cm=round(100 * bed_seat, 1), seat_parts_floor_cm=round(100 * floor_seat, 1)),
               housing=dict(outline_xz=np.round(Hs, 4).tolist(), area_cm2=round(1e4 * poly_area(Hs)), old_area_cm2=round(1e4 * poly_area(Hold)), top_z=round(float(Hs[:, 1].max()), 3),
                            old_top_z=round(float(Hold[:, 1].max()), 3), x=[round(float(Hs[:, 0].min()), 3), round(float(Hs[:, 0].max()), 3)]),
               tipping=tip)
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1, default=float)
    for k in ("statics", "masses", "beam", "c1", "link", "carriage", "plate", "housing_box", "deflection", "drive", "emergency_belt3", "handrail", "footplate", "cells", "cushion", "clearances", "housing", "tipping"):
        v = out[k]
        if k == "housing": v = {kk: vv for kk, vv in v.items() if kk != "outline_xz"}
        if k == "masses": v = {kk: vv for kk, vv in v.items() if kk not in ("seat_parts", "plate_parts")}
        print(k, json.dumps(v, ensure_ascii=False, default=float)[:900])
