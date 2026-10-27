"""Fixed structure of the bed-exit seat (group "fixed", world frame, mm) plus the bed as a reference body (group "ref").
Housing H1-H5, base frame B1 (+ feet B1a), footplate B2/B2b, handrail post B4 and bar B5, controller box B7, bed.
Contract: cadlib.py (HOUSING outline, Y stack, DRIVE window, BASE, FOOT, POST, BAR_Y)."""
import math
import cadquery as cq
import cadlib as L
from cadlib import Part, prism_xz, cyl_y, box, rect_tube_x, rect_tube_y, loc, COLORS

def _window(margin=0.0):
    """drive-stack window in H1 (screw-local X x Z), world (x, z) polygon."""
    (x0, x1), r = L.DRIVE["window_x"], L.DRIVE["r_env"] + margin
    x0, x1 = x0 - margin, x1 + margin
    return [L.screw_to_world(x, z) for x, z in ((x0, -r), (x1, -r), (x1, r), (x0, r))]

def _outline(y0, y1): return prism_xz(L.HOUSING, y0, y1)

def _stadium(a, b, r, y0, y1):
    dx, dz = b[0] - a[0], b[1] - a[1]; n = math.hypot(dx, dz); nx, nz = -dz / n * r, dx / n * r
    band = prism_xz([(a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz), (b[0] - nx, b[1] - nz), (a[0] - nx, a[1] - nz)], y0, y1)
    return band.union(cyl_y(a[0], a[1], y0, y1, r)).union(cyl_y(b[0], b[1], y0, y1, r))

def build():
    parts = []
    yb0, yb1 = L.Y["back"]
    # H1 back plate: outline, drive window through, nut-flange relief 12 deep from the inner face
    h1 = _outline(yb0, yb1).cut(prism_xz(_window(), yb0 - 5, yb1 + 5))
    relief = [L.screw_to_world(x, z) for x, z in ((40, -32), (480, -32), (480, 32), (40, 32))]      # nut flange + C3 end wall path
    h1 = h1.cut(prism_xz(relief, yb0 - 1, yb0 + 12))
    parts.append(Part("H1", "侧板（导轨安装板）", "6061-T6 铝板 15 mm", "fixed", h1, color=COLORS["alu"],
                      params=[("板厚", "15 mm"), ("y", f"{yb0:.0f} … {yb1:.0f}"), ("外形", "机构箱侧视外廓（见总装图）"), ("驱动窗口", "沿丝杠 445 … 585 × 宽 92"),
                              ("螺母让位槽", "沿丝杠 60 … 470 × 宽 52 × 深 8"), ("导轨安装面", "y 336 面精铣；导轨孔按 HGR15 孔距 60 配钻")],
                      note="两根导轨装在这块板的内表面；驱动端的制动器比板面还宽，所以开窗口，外面加 H5 罩"))
    # H2 inner wall with the c1 slot
    yi0, yi1 = L.Y["wall_in"]; pa, pb = L.POSES["flush"]["P1"], L.POSES["top"]["P1"]
    h2 = _outline(yi0, yi1).cut(_stadium(pa, pb, 43.5, yi0 - 5, yi1 + 5))
    parts.append(Part("H2", "内壁", "钢板 2 mm", "fixed", h2, color="#9DB2CC",
                      params=[("板厚", "2 mm"), ("y", f"{yi0:.0f} … {yi1:.0f}"), ("竖槽宽", "87（= 轴承座筒 Ø75 + 2 × 6）"),
                              ("竖槽中心线", f"({pa[0]:.0f}, {pa[1]:.0f}) → ({pb[0]:.0f}, {pb[1]:.0f})"), ("竖槽两侧", "装毛刷条")],
                      note="竖槽沿铰点 1 的轨迹；毛刷让手指进不去"))
    # H3 perimeter band (2 mm), between the inner wall and the back plate
    h3o = cq.Workplane("XZ", origin=(0, yi1, 0)).polyline(L.HOUSING).close().extrude(-(yb0 - yi1))
    h3i = cq.Workplane("XZ", origin=(0, yi1 - 1, 0)).polyline(L.HOUSING).close().offset2D(-2.0, "intersection").extrude(-(yb0 - yi1 + 2))
    h3 = h3o.cut(h3i)
    parts.append(Part("H3", "周边围板", "钢板 2 mm 折弯，焊或铆", "fixed", h3, color="#8EA3BD",
                      params=[("板厚", "2 mm"), ("y", f"{yi1:.0f} … {yb0:.0f}（深 {yb0 - yi1:.0f}）"), ("走向", "沿机构箱侧视外廓一圈"),
                              ("作用", "把 H1、H2 连成闭口盒子")], note="盒子要扛横滚力矩约 888 N·m"))
    # H4 outer cover, window clears H5
    yo0, yo1 = L.Y["wall_out"][0], L.Y["wall_out"][0] + 1.5
    h4 = _outline(yo0, yo1).cut(prism_xz(_window(10.0), yo0 - 5, yo1 + 5))
    parts.append(Part("H4", "外罩", "1.5 mm 铝板或 ABS（不受力）", "fixed", h4, color="#C9D3DD",
                      params=[("板厚", "1.5 mm"), ("y", f"{yo0:.0f} … {yo1:.1f}"), ("窗口", "让出 H5 驱动罩")]))
    # H5 drive cover: open toward -y
    cy1 = L.DRIVE["cover_y"][1]
    h5 = prism_xz(_window(10.0), yb1, cy1).cut(prism_xz(_window(8.5), yb1 - 1, cy1 - 1.5))
    parts.append(Part("H5", "驱动罩", "钢板 1.5 mm", "fixed", h5, color="#7E93AD",
                      params=[("板厚", "1.5 mm"), ("y", f"{yb1:.0f} … {cy1:.0f}"), ("外形", "驱动窗口每边 + 10"), ("开口", "朝 −y，罩在 H1 窗口外")],
                      note="制动器和限速器外径大于丝杠到侧板的距离，这里机构箱局部加厚到 y 372"))
    # B1 base frame: 60 x 30 x 3 lying flat, z 5..35
    z0, z1, t = 5.0, 35.0, 3.0
    mx = lambda x0, x1, y0, y1: rect_tube_x(x0, x1, y0, y1, z0, z1, t)
    my = lambda x0, x1, y0, y1: rect_tube_y(x0, x1, z0, z1, y0, y1, t)
    members = [mx(30, 780, -270, -210), mx(30, 780, 320, 380), my(30, 90, -210, 320), my(720, 780, -210, 320),
               my(670, 730, -210, 320), mx(90, 670, 250, 310), my(190, 250, -210, 250), my(570, 630, -210, 250)]
    b1 = members[0]
    for mbr in members[1:]: b1 = b1.union(mbr)
    parts.append(Part("B1", "底座框", "S355 矩形管 60 × 30 × 3（平放，高 30）", "fixed", b1, color=COLORS["steel"],
                      params=[("管材", "60 × 30 × 3，平放"), ("外框", "x 30 … 780，y −270 … 380"), ("顶面", "z 35（下垫 5 mm 调平脚）"),
                              ("立柱下纵梁", "x 670 … 730"), ("机构箱下横梁", "y 250 … 310"), ("踏板下纵梁", "x 190 … 250、570 … 630")],
                      note="机构箱底（z 40）和底座顶（z 35）之间留 5 mm，用垫块或支脚连接"))
    feet = [(60, -240), (750, -240), (60, 350), (750, 350), (405, -240), (405, 350)]
    parts.append(Part("B1a", "调平脚", "Ø40 × 5 橡胶调平脚", "fixed", L.cyl_z(0, 0, 0, 5, 20), instances=[loc(x, y, 0) for x, y in feet],
                      color=COLORS["rubber"], buy=True, drawing=False, params=[("尺寸", "Ø40 × 5"), ("数量", "6")]))
    # B2 footplate + rubber mat
    (fx0, fx1), (fy0, fy1) = L.FOOT["x"], L.FOOT["y"]
    parts.append(Part("B2", "踏板", "6061-T6 铝板 10 mm", "fixed", box(fx0, fx1, fy0, fy1, 35, 45), color=COLORS["alu"],
                      params=[("尺寸", f"{fx1 - fx0:.0f} × {fy1 - fy0:.0f} × 10"), ("位置", f"x {fx0:.0f} … {fx1:.0f}，y ±{fy1:.0f}，z 35 … 45"),
                              ("支撑", "四角 4 只称重单元，装在底座框内侧托板上")]))
    parts.append(Part("B2b", "防滑胶垫", "2 mm 防滑橡胶", "fixed", box(fx0 + 10, fx1 - 10, fy0 + 10, fy1 - 10, 45, 47), color=COLORS["rubber"],
                      buy=True, drawing=False, params=[("尺寸", f"{fx1 - fx0 - 20:.0f} × {fy1 - fy0 - 20:.0f} × 2")]))
    # B4 post with base plate and gussets
    px, py, ptop = L.POST["x"], L.POST["y"], L.POST["top"]; ztop = ptop - 19
    post = L.rect_tube_z(px - 30, px + 30, py - 30, py + 30, 45, ztop, 4)
    plate = box(px - 100, px + 100, py - 75, py + 75, 35, 45)
    g = []
    for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if sx:   # gusset in the x-z plane, on the +-x face
            x0 = px + sx * 30; x1 = px + sx * 90
            g.append(prism_xz([(x0, 45), (x1, 45), (x0, 125)], py - 5, py + 5))
        else:    # gusset in the y-z plane, on the +-y face
            y0 = py + sy * 30; y1 = py + sy * 75                                                   # stays on the 150-wide base plate
            g.append(cq.Workplane("YZ", origin=(px - 5, 0, 0)).polyline([(y0, 45), (y1, 45), (y0, 125)]).close().extrude(10))
    b4 = post.union(plate)
    for gg in g: b4 = b4.union(gg)
    parts.append(Part("B4", "扶手立柱", "S355 方管 60 × 60 × 4，喷塑", "fixed", b4, color=COLORS["steel"],
                      params=[("方管", "60 × 60 × 4"), ("位置", f"x {px:.0f}，y {py:.0f}"), ("高度", f"z 45 … {ztop:.0f}"), ("底板", "200 × 150 × 10"),
                              ("筋板", "4 块，厚 10，高 80；x 向长 60、y 向长 45"), ("根部弯矩", "1.53 kN·m（ADA 1112 N × 1.5）")],
                      note="和底座框焊成一体；底板在 x 方向比底座外缘多出 20 mm，CAD 可缩到 160"))
    # B5 bar with a domed end
    by0, by1 = L.BAR_Y[0], py + 30
    bar = cyl_y(px, ptop, by0, by1, 19).cut(cyl_y(px, ptop, by0 + 4, by1 + 1, 15))
    cap = cq.Workplane("XY").sphere(19).translate((px, by0, ptop)).cut(box(px - 30, px + 30, by0, by0 + 40, ptop - 30, ptop + 30))
    b5 = bar.union(cap)
    parts.append(Part("B5", "横杆", "S355 圆管 Ø38 × 4，喷塑", "fixed", b5, color=COLORS["ink"],
                      params=[("圆管", "Ø38 × 4"), ("位置", f"x {px:.0f}，z {ptop:.0f}"), ("长度", f"y {by0:.0f} … {by1:.0f}（{by1 - by0:.0f}）"),
                              ("末端", "圆头，软包、夜光"), ("握把", "装握紧开关和测力")]))
    parts.append(Part("B7", "控制器 + 电池", "24 V 锂电池 + 控制器（外形估计）", "fixed", box(100, 250, 262, 330, 45, 120), color=COLORS["buy"],
                      buy=True, drawing=False, params=[("外形", "150 × 68 × 75")]))
    parts.append(Part("BED", "床（参考）", "床垫面 420", "ref", box(-900, 0, -700, 800, 0, L.BED_TOP), color=COLORS["bed"], buy=True, drawing=False,
                      params=[("床垫面", "z 420"), ("床沿", "x = 0")]))
    return parts

if __name__ == "__main__":
    ps = build(); print(L.check(ps))
    for p in ps:
        bb = p.shape.val().BoundingBox(); print(p.code, p.qty, [round(v, 1) for v in (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)])
