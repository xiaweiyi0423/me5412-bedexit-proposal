"""Carriage group (slide weldment, bearings, carriages, nut), link group (link tube, rod ends) and the drive parts (rails, screw,
supports, pulleys, motor, brake, limiter, pivot-B bracket) of the bed-exit seat, v5.7. Contract: cadlib.py (frames, Y stack, DRIVE).

Frames used here
  carriage : origin pin 1, X = E (up the rails), Y = world y, Z = -NF. Rail coordinates (a along E, b along NF) -> (a, -b).
  link     : origin pivot B (world y 0), X from B toward pin 2.
  rails / screw / drive parts: built along their own X ("screw-local": origin SCREW_LO, X along E, Z = -NF), placed with
             cadlib.loc(x, 0, z, RAIL_ROT). In screw-local coordinates rail 1 is at Z = +75, rail 2 at Z = -75, and pin 1 at
             X = 20 + stroke, Z = +75.
"""
import math
import cadquery as cq
import cadlib as L
from cadlib import Part, Y, COLORS, loc, ab, prism_xz, cyl_y, tube_y, cyl_x, box, holes_y, DRIVE

YL = Y["link"]
BLOCKS = [(0.0, 0.0), (150.0, 0.0), (0.0, 150.0), (150.0, 150.0)]          # carriage-block centres, rail coords (a, b)
NUT_AB = (75.0, 75.0)                                                        # nut / nut bracket centre, rail coords
MOTOR_Z, MOTOR_Y = 150.0, 300.0                                              # motor axis in screw-local Z and world y (see report)


def arm_window():
    """centre and span (deg, carriage-local, from +X toward +Z) of the pin-2 arm over the whole travel."""
    e_deg = math.degrees(math.atan2(L.E[1], L.E[0])); angs = []
    n = 60
    for k in range(n + 1):
        p = L.pose(L.STROKE * k / n); dx, dz = p["P2"][0] - p["P1"][0], p["P2"][1] - p["P1"][1]
        angs.append(math.degrees(math.atan2(dz, dx)) - e_deg)
    return 0.5 * (min(angs) + max(angs)), min(angs), max(angs)


def plate_c1():
    """C1: 20 mm plate, y 288..308; corner next to pin 1 clipped by R42 about the origin; bearing-A bore; carriage and bracket holes."""
    y0, y1 = Y["plate"]
    pA = ab(-40.0, -math.sqrt(42 ** 2 - 40 ** 2)); pB = ab(-math.sqrt(42 ** 2 - 25 ** 2), -25.0)
    am = math.atan2(-12.806, -40.0) * 0.5 + math.atan2(-25.0, -33.749) * 0.5; pM = ab(42 * math.cos(am), 42 * math.sin(am))
    wp = (cq.Workplane("XZ", origin=(0, y0, 0)).moveTo(*ab(190, -25)).lineTo(*ab(190, 175)).lineTo(*ab(-40, 175)).lineTo(*pA)
          .threePointArc(pM, pB).close().extrude(-(y1 - y0)))
    wp = wp.cut(cyl_y(0, 0, y0 - 1, y1 + 1, 27.5))
    holes = [ab(a + da, b + db) for a, b in BLOCKS for da in (-13, 13) for db in (-13, 13)]
    wp = holes_y(wp, holes, 2.25)
    wp = holes_y(wp, [ab(NUT_AB[0] + da, NUT_AB[1] + db) for da in (-20, 20) for db in (-20, 20)], 3.3)
    return wp


def cartridge_j3():
    """J3: tube OD 75 / bore 55, y 229..288 on the pin-1 axis; window for y Y["window"] centred on the arm direction (80 deg: the 30-wide arm subtends +-31 deg at the bore, plus its +-7.8 deg swing)."""
    c, lo, hi = arm_window(); half = 40.0                     # arm 30 wide at r 27.5 (+-31 deg) + its +-7.8 deg swing
    wp = tube_y(0, 0, Y["brgB"][0], Y["plate"][0], 37.5, 27.5)
    pts = [(0.0, 0.0)] + [(50 * math.cos(math.radians(c - half + 2 * half * k / 12)), 50 * math.sin(math.radians(c - half + 2 * half * k / 12))) for k in range(13)]
    return wp.cut(prism_xz(pts, Y["window"][0], Y["window"][1])), (c, lo, hi)


def carriage_c2():
    """C2: HGH15CA envelope, one block at the origin: 61.4 along X, 34 along Z, body y 308..331.7, rail channel 15.5 x 15 underneath."""
    y0, y1 = Y["carriage"]
    return box(-30.7, 30.7, y0, y1, -17, 17).cut(box(-31, 31, y1 - 15.0, y1 + 1, -7.75, 7.75))


def nut_bracket_c3():
    """C3: top plate bolted to C1 (60 x 56 x 10, y 308..318) + an end wall (10 thick, perpendicular to the screw) the nut flange bolts to."""
    xc, zc = ab(*NUT_AB)
    top = box(xc - 30, xc + 30, Y["plate"][1], Y["plate"][1] + 10, zc - 28, zc - 13).union(box(xc - 30, xc + 30, Y["plate"][1], Y["plate"][1] + 10, zc + 13, zc + 28))   # split: the screw passes 14 mm under C1
    wall = box(xc - 32.5, xc - 22.5, Y["plate"][1], Y["screw"] + 24, zc - 28, zc + 28).cut(cyl_x(xc - 40, xc - 15, Y["screw"], zc, 15.0))
    return top.union(wall)


def nut_d2n():
    """D2n: ball nut, body dia 28 x 45 along X centred on the nut position, flange dia 48 x 10 at its lower end (bolted to C3's wall)."""
    xc, zc = ab(*NUT_AB)
    body = cyl_x(xc - 22.5, xc + 22.5, Y["screw"], zc, 14.0); fl = cyl_x(xc - 22.5, xc - 12.5, Y["screw"], zc, 24.0)
    return body.union(fl).cut(cyl_x(xc - 30, xc + 30, Y["screw"], zc, 8.1))


def c1_flange_pocket(c1):
    """the nut flange (dia 48, centred y 322) reaches y 298: pocket C1's underside (y 297..308) where the flange sits."""
    xc, zc = ab(*NUT_AB)
    return c1.cut(box(xc - 23.5, xc - 11.5, Y["plate"][1] - 11, Y["plate"][1] + 1, zc - 25.5, zc + 25.5))


def rail_d1():
    w = box(0, L.RAIL_LEN, Y["rail"][0], Y["rail"][1], -7.5, 7.5); x = 20.0
    while x < L.RAIL_LEN - 5:
        w = w.cut(cyl_y(x, 0, Y["rail"][0] - 1, Y["rail"][1] + 1, 2.25)).cut(cyl_y(x, 0, Y["rail"][0] - 1, Y["rail"][0] + 5.3, 3.75)); x += 60.0
    return w


def screw_d2():
    ys = Y["screw"]; x0, bk0, lim1 = DRIVE["screw_x0"], DRIVE["bk"][0], DRIVE["limiter"][1]
    return cyl_x(x0, bk0, ys, 0, 8.0).union(cyl_x(bk0, lim1, ys, 0, 6.0))


def support(x0, x1):
    ys = Y["screw"]; return box(x0, x1, ys - 21.5, ys + 21.5, -30, 30).cut(cyl_x(x0 - 1, x1 + 1, ys, 0, 6.5))


def pulleys_d3():
    ys = Y["screw"]; p0, p1 = DRIVE["pulley"]
    big = cyl_x(p0, p1, ys, 0, 36.0).cut(cyl_x(p0 - 1, p1 + 1, ys, 0, 6.0))
    small = cyl_x(p0, p1, MOTOR_Y, MOTOR_Z, 12.0).cut(cyl_x(p0 - 1, p1 + 1, MOTOR_Y, MOTOR_Z, 4.0))
    return big.union(small)


def motor_d4():
    p0 = DRIVE["pulley"][0]
    body = box(p0 - 100, p0, MOTOR_Y - 28.5, MOTOR_Y + 28.5, MOTOR_Z - 28.5, MOTOR_Z + 28.5)
    return body.union(cyl_x(p0, DRIVE["pulley"][1], MOTOR_Y, MOTOR_Z, 4.0))


def bracket_l3():
    bx, bz = L.B; lugs = None
    for yy in ((YL - 13, YL - 7), (YL + 7, YL + 13)):
        lug = (cq.Workplane("XZ", origin=(0, yy[0], 0)).moveTo(bx - 20, 50).lineTo(bx + 20, 50).lineTo(bx + 20, bz)
               .threePointArc((bx, bz + 20), (bx - 20, bz)).close().extrude(-(yy[1] - yy[0])))
        lugs = lug if lugs is None else lugs.union(lug)
    lugs = lugs.cut(cyl_y(bx, bz, YL - 20, YL + 20, 5.1))
    base = box(bx - 40, bx + 22, YL - 20, YL + 20, 42, 50)          # sits on the housing floor (z 40-42), inside the walls
    pin = cyl_y(bx, bz, YL - 15, YL + 15, 5.0)
    return lugs.union(base).union(pin)


def build():
    win_c, win_lo, win_hi = arm_window()
    c1 = c1_flange_pocket(plate_c1()); j3, _ = cartridge_j3()
    sl = lambda p: loc(p[0], 0, p[1], L.RAIL_ROT)
    parts = [
        Part("C1", "滑块板", "S355 钢板 20 mm", "carriage", c1, color=COLORS["blue_light"],
             params=[("厚", "20 mm（y 288 … 308）"), ("外形", "沿导轨 −40 … 190，垂直导轨 −25 … 175（以铰点 1 为原点）"), ("铰点 1 角", "R42（绕铰点 1）"),
                     ("轴承 A 孔", "Ø55 H7（和 J3 焊后同镗）"), ("滑块安装孔", "4 × 4 × Ø4.5，26 × 26，块心 (0,0) (150,0) (0,150) (150,150)"),
                     ("螺母座孔", "4 × Ø6.6，40 × 40，心 (75, 75)"), ("螺母法兰让位槽", "背面 11 深")],
             note="和 J3 焊成一个焊件，两个轴承孔焊后一起精加工；背面在螺母法兰处开 11 深让位槽。"),
        Part("J3", "轴承座筒", "S355 无缝钢管 Ø75 / 内孔 Ø55", "carriage", j3, color=COLORS["red"],
             params=[("外径 / 内孔", "Ø75 / Ø55 H7"), ("长", "y 229 … 288（再插进 C1 的孔到 308）"), ("窗口", f"80°，y {Y['window'][0]:.0f} … {Y['window'][1]:.0f}，中心在 {win_c:.1f}°（滑块座坐标，从 +X 转向 +Z）"),
                     ("摆臂转角范围", f"{win_lo:.1f}° … {win_hi:.1f}°"), ("焊缝", "和 C1 外圈角焊，焊后同镗两孔")],
             note="穿过内壁竖槽；窗口让铰点 2 摆臂 J4 穿出。"),
        Part("J2", "圆锥滚子轴承", "SKF 32006 X/Q 或同级（30 × 55 × 17）", "carriage", tube_y(0, 0, Y["brgB"][0], Y["brgB"][1], 27.5, 15.0),
             instances=[L.IDENT, loc(0, Y["brgA"][0] - Y["brgB"][0], 0)], color=COLORS["buy"], buy=True, drawing=False,
             params=[("内径 / 外径 / 宽", "30 / 55 / 17"), ("位置", "y 229 … 246（B）、274 … 291（A），背对背，间距 45")]),
        Part("C2", "滑块", "HIWIN HGH15CA（Z0 轻预压）或同级", "carriage", carriage_c2(),
             instances=[loc(*(lambda q: (q[0], 0, q[1]))(ab(a, b))) for a, b in BLOCKS], color=COLORS["blue"], buy=True, drawing=False,
             params=[("外形", "61.4 × 34，高 23.7（不含导轨）"), ("安装孔", "4 × M4，26 × 26")]),
        Part("C3", "螺母座", "S355", "carriage", nut_bracket_c3().cut(nut_d2n()), color=COLORS["steel"],
             params=[("顶板", "60 × 56 × 10，中间开 26 宽槽让丝杠通过，用 4 × M6 接 C1"), ("端板", "10 厚，螺母法兰贴在它上面"), ("螺母孔", "Ø30")],
             note="端板伸到 y 346，侧板 H1 在螺母行程上要开让位槽（宽约 60、深 12）。"),
        Part("D2n", "丝杠螺母", "HIWIN R16-10K3-FSCDIN 或同级", "carriage", nut_d2n(), color=COLORS["buy"], buy=True, drawing=False,
             params=[("本体", "Ø28 × 45"), ("法兰", "Ø48 × 10")]),
        Part("L1", "连杆管", "S355 钢管 Ø20 × 2", "link", cyl_x(43.0, L.LINK_LEN - 43.0, YL, 0, 10.0).cut(cyl_x(42.0, L.LINK_LEN - 42.0, YL, 0, 8.0)),
             color=COLORS["steel_dark"],
             params=[("管", "Ø20 × 2"), ("管长", f"{L.LINK_LEN - 86:.1f}"), ("铰点中心距", f"{L.LINK_LEN:.1f}（装配时用杆端螺纹调）"), ("两端", "焊 M10 螺纹接头，一端左旋")]),
        Part("L2", "杆端关节轴承", "SKF SIKAC 10 M 或同级", "link",
             tube_y(0, 0, YL - 6, YL + 6, 14.5, 5.0).union(cyl_x(12.0, 42.0, YL, 0, 7.0)),
             instances=[L.IDENT, loc(L.LINK_LEN, 0, 0, 180.0)], color=COLORS["buy"], buy=True, drawing=False,
             params=[("孔", "Ø10"), ("头部", "外径 29，厚 12"), ("螺纹", "M10 内螺纹")]),
        Part("L3", "B 支座", "S355 8 mm 双耳座 + Ø10 销", "fixed", bracket_l3(), color=COLORS["steel"],
             params=[("耳板", "2 × 6 厚，宽 40，R20 顶"), ("耳板间距", "14（杆端头厚 12）"), ("销孔", f"Ø10.2，中心 ({L.B[0]:.0f}, {YL:.0f}, {L.B[1]:.0f})"),
                     ("底板", "90 × 60 × 8，z 40 … 48")]),
        Part("D1", "导轨", "HIWIN HGR15 或同级", "fixed", rail_d1(), instances=[sl(L.RAIL1_LO), sl(L.RAIL2_LO)], color=COLORS["ink"], buy=True, drawing=False,
             params=[("截面", "15 × 15"), ("长", f"{L.RAIL_LEN:.0f}"), ("孔距", "60，首孔 20")]),
        Part("D2", "滚珠丝杠", "Ø16 导程 10（HIWIN R16-10 或同级）", "fixed", screw_d2(), instances=[sl(L.SCREW_LO)], color=COLORS["red"], buy=True, drawing=False,
             params=[("螺纹段", "Ø16，X 25 … 546（下端自由，不装浮动支撑）"), ("轴端", "Ø12"), ("总长", f"{DRIVE['limiter'][1] - DRIVE['screw_x0']:.0f}")]),
        Part("D2a", "丝杠固定支撑", "BK12 或同级", "fixed", support(*DRIVE["bk"]), instances=[sl(L.SCREW_LO)], color=COLORS["buy"], buy=True, drawing=False),
        Part("D3", "同步带轮", "HTD-5M 宽 15，45T / 15T", "fixed", pulleys_d3(), instances=[sl(L.SCREW_LO)], color=COLORS["buy"], buy=True, drawing=False,
             params=[("大轮", "Ø72 × 20（丝杠）"), ("小轮", "Ø24 × 20（电机）"), ("中心距", f"{math.hypot(MOTOR_Z, Y['screw'] - MOTOR_Y):.0f}")]),
        Part("D4", "电机", "24 V 无刷直流，57 机座（外形按 57 × 57 × 100 估）", "fixed", motor_d4(), instances=[sl(L.SCREW_LO)], color=COLORS["buy"], buy=True, drawing=False),
        Part("D5", "失电制动器", "8 N·m 级（外形按 Ø90 估，以样本为准）", "fixed",
             cyl_x(DRIVE["brake"][0], DRIVE["brake"][1], Y["screw"], 0, 45.0).cut(cyl_x(DRIVE["brake"][0] - 1, DRIVE["brake"][1] + 1, Y["screw"], 0, 6.0)),
             instances=[sl(L.SCREW_LO)], color=COLORS["buy"], buy=True, drawing=False),
        Part("D6", "离心限速器", "180 r/min（外形按 Ø60 估）", "fixed",
             cyl_x(DRIVE["limiter"][0], DRIVE["limiter"][1], Y["screw"], 0, 30.0).cut(cyl_x(DRIVE["limiter"][0] - 1, DRIVE["limiter"][1] + 1, Y["screw"], 0, 6.0)),
             instances=[sl(L.SCREW_LO)], color=COLORS["buy"], buy=True, drawing=False),
    ]
    return parts


# ---------------------------------------------------------------- self-checks
def _world(part, inst, gloc):
    return part.shape.val().moved(inst).moved(gloc)

def _clash(sa, sb):
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    c = BRepAlgoAPI_Common(sa.wrapped, sb.wrapped); g = GProp_GProps(); BRepGProp.VolumeProperties_s(c.Shape(), g); return g.Mass()

if __name__ == "__main__":
    ps = build(); by = {p.code: p for p in ps}
    print("check:", L.check(ps))
    for p in ps:
        bb = p.shape.val().BoundingBox(); print(f"{p.code:4s} qty {p.qty}  x {bb.xmin:7.1f} {bb.xmax:7.1f}  y {bb.ymin:6.1f} {bb.ymax:6.1f}  z {bb.zmin:7.1f} {bb.zmax:7.1f}")
    c, lo, hi = arm_window(); print(f"arm window centre {c:.1f} deg (range {lo:.1f} .. {hi:.1f})")
    for nm in ("flush", "top"):
        p = L.POSES[nm]; gc = L.group_loc("carriage", p)
        # C2 on D1: block centre vs rail line (perpendicular offset) and channel/rail y overlap
        for k, (a, b) in enumerate(BLOCKS):
            cx = p["P1"][0] + a * L.E[0] + b * L.NF[0]; cz = p["P1"][1] + a * L.E[1] + b * L.NF[1]
            lo_ = L.RAIL1_LO if b == 0 else L.RAIL2_LO; dx, dz = cx - lo_[0], cz - lo_[1]
            t = dx * L.E[0] + dz * L.E[1]; off = -dx * L.E[1] + dz * L.E[0]
            print(f"  {nm} block {k}: along rail {t:6.1f} (0..{L.RAIL_LEN:.0f}), off-line {off:+.2f} mm")
        # rod-end heads vs pins
        d = math.hypot(p["P2"][0] - L.B[0], p["P2"][1] - L.B[1]); print(f"  {nm}: |B-P2| {d:.2f} vs LINK_LEN {L.LINK_LEN:.2f} (diff {d - L.LINK_LEN:+.2f})")
        gl = L.group_loc("link", p); from OCP.gp import gp_Pnt
        q = gp_Pnt(L.LINK_LEN, 0, 0).Transformed(gl.wrapped.Transformation()); print(f"  {nm}: L2 head 2 at ({q.X():.1f}, {q.Z():.1f}) vs P2 {p['P2']}")
        # drive parts vs carriage parts
        fixed = {k: _world(by[k], by[k].instances[0], L.IDENT) for k in ("D2a", "D3", "D4", "D5", "D6", "D2", "D1")}
        for kc in ("C1", "C3", "D2n", "C2", "J3"):
            for inst in by[kc].instances:
                sc = _world(by[kc], inst, gc)
                for kf, sf in fixed.items():
                    v = _clash(sc, sf)
                    if v > 1: print(f"  CLASH {nm}: {kc} x {kf}: {v:.0f} mm3")
    # how far up the rails does C1 reach at the top, in screw-local X
    pt = L.POSES["top"]["P1"]; x_top = (pt[0] - L.SCREW_LO[0]) * L.E[0] + (pt[1] - L.SCREW_LO[1]) * L.E[1]
    print(f"pin 1 at top: screw-local X {x_top:.1f}; C1 reaches X {x_top + 190:.1f}, carriages to {x_top + 180.7:.1f}; nut to {x_top + 75 + 22.5:.1f}")
    import os
    if os.path.exists(os.path.join(os.path.dirname(__file__), "parts_seat.py")):
        try:
            import parts_seat as PS
            sp = {q.code: q for q in PS.build()}
            if "J4" in sp:
                for nm in ("flush", "mid", "top"):
                    p = L.POSES[nm]; s4 = _world(sp["J4"], sp["J4"].instances[0], L.group_loc("seat", p))
                    for kc in ("J3", "C1"):
                        v = _clash(_world(by[kc], by[kc].instances[0], L.group_loc("carriage", p)), s4); print(f"  J4 x {kc} at {nm}: {v:.0f} mm3")
        except Exception as ex: print("seat check skipped:", ex)
