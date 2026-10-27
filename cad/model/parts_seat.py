"""Seat group (group "seat", seat frame: x_s forward, y = world y, z_s normal; origin Q = cushion top centre). v5.7.
build() -> list[Part]. Purchased parts (S5 cells, J5 lock nut) are envelopes, no drawing."""
import math
import cadquery as cq
import cadlib as L
from cadlib import Part, COLORS, Y, SZ, C1S, C2S, loc, box, prism_xz, cyl_y, tube_y, holes_y, pcd

NOTCH = dict(x=(-36.0, 52.0), y=(200.0, 221.0), z=(-135.0, -26.0))     # head-side edge pocket for S8 + J1 flange
CELL_XY = [(-30.0, -180.0), (-30.0, 180.0), (60.0, -180.0), (60.0, 180.0)]   # y +-180 (BOM said +-190): clears S8 at y 204

def _notch(wp):
    return wp.cut(box(NOTCH["x"][0], NOTCH["x"][1], NOTCH["y"][0], NOTCH["y"][1], NOTCH["z"][0], NOTCH["z"][1]))

def _hull(points):
    P = sorted(set((round(x, 3), round(z, 3)) for x, z in points))
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def build():
    W2 = L.SEAT_W / 2; parts = []
    # cushion, board, spacer
    s1 = _notch(box(-85, SZ["split"], -W2, W2, SZ["foam_rear"], 0))
    parts.append(Part("S1", "后区泡棉", "高硬度再生（重组）海绵 100–150 kg/m³，或闭孔 EVA 叠层", "seat", s1, color=COLORS["foam_r"],
                      params=[("长（沿座面 x_s）", "65 mm（−85 … −20）"), ("宽（y）", "440 mm"), ("厚", "50 mm"), ("含软唇边", "x_s −85 … −40 下面无底板"),
                              ("目标硬度", "压 40% 时约 20 kPa"), ("头侧缺口", "x_s −36 … 52，y 200 … 221")], note="后区硬：把起身时的推力放到骨盆；外包 S3 面料"))
    s2 = _notch(box(SZ["split"], 85, -W2, W2, SZ["foam_front"], 0))
    parts.append(Part("S2", "前区泡棉", "高回弹（HR）海绵 45–55 kg/m³，高硬度级", "seat", s2, color=COLORS["foam_f"],
                      params=[("长（x_s）", "105 mm（−20 … 85）"), ("宽（y）", "440 mm"), ("厚", "80 mm"), ("目标硬度", "压 40% 时约 10 kPa"),
                              ("头侧缺口", "x_s −36 … 52，y 200 … 221，z_s −80 … −26")], note="前区软：少压大腿；顶面和后区齐平"))
    s4 = _notch(box(-40, 85, -W2, W2, SZ["board"][0], SZ["board"][1]))
    parts.append(Part("S4", "底板", "12 mm 桦木多层板", "seat", s4, color=COLORS["wood"],
                      params=[("长（x_s）", "125 mm（−40 … 85）"), ("宽（y）", "440 mm"), ("厚", "12 mm"), ("z_s", "−92 … −80"),
                              ("称重单元位置", "(−30, ±180)、(60, ±180)"), ("头侧缺口", "x_s −36 … 52，y 200 … 220")], note="一整块；面料钉在底面；压在 4 个称重单元上"))
    s4b = _notch(box(-40, SZ["split"], -W2, W2, SZ["board"][1], SZ["foam_rear"]))
    parts.append(Part("S4b", "后区垫条", "桦木多层板（垫条）", "seat", s4b, color=COLORS["wood"],
                      params=[("长（x_s）", "20 mm（−40 … −20）"), ("宽（y）", "440 mm"), ("高", "30 mm（z_s −80 … −50）")],
                      note="把 50 mm 厚的后区泡棉托到和前区齐平；粘在 S4 上"))
    # load cells (one envelope, 4 instances)
    cell = box(-15, 15, -15, 15, SZ["cells"][0], SZ["cells"][1])
    parts.append(Part("S5", "称重单元", "薄型，抗拔（螺栓固定的平行梁式，或加防掀限位）", "seat", cell, instances=[loc(x, y, 0) for x, y in CELL_XY],
                      color=COLORS["buy"], buy=True, drawing=False,
                      params=[("外形（估）", "30 × 30 × 8 mm"), ("量程", "≥ 110 kg/只"), ("受力范围", "−856 … +1592 N"), ("位置", "(−30, ±180)、(60, ±180)")],
                      note="外购件：外形按估计，选型后替换"))
    # load-cell arms: flat bar 40 x 10 across the beam; the beam's envelope is cut out (two pieces welded to the beam's sides)
    arm = box(-40, 75, -20, 20, SZ["arms"][0], SZ["arms"][1]).cut(box(-25, 25, -21, 21, SZ["beam"][0], SZ["beam"][1]))
    parts.append(Part("S6", "称重支臂", "S355 扁钢 40 × 10", "seat", arm, instances=[loc(0, -180, 0), loc(0, 180, 0)], color=COLORS["steel"],
                      params=[("截面", "40（y）× 10（z）"), ("长（x_s）", "115 mm（−40 … 75），中间让开横梁"), ("位置", "y = ±180（离 S8 留 4 mm 焊缝空间）"), ("z_s", "−110 … −100（顶面和横梁齐平）"),
                              ("连接", "两段焊在横梁前后侧面")], note="托称重单元；横梁处断开，两段角焊"))
    # cross-beam
    beam = L.rect_tube_y(-25, 25, SZ["beam"][0], SZ["beam"][1], Y["beam"][0], Y["beam"][1], 4)
    parts.append(Part("S7", "横梁", "S355 矩形管 50 × 30 × 4", "seat", beam, color=COLORS["steel"],
                      params=[("截面", "50（x_s）× 30（z_s）× 4"), ("长（y）", "409 mm（−205 … 204）"), ("x_s", "−25 … 25"), ("z_s", "−130 … −100"),
                              ("端头", "y = 204 处和 S8 节点板角焊（四周）"), ("自由端", "y = −205 焊端板封口（可选）")], note="座板的单侧悬臂主梁；高 30 被小腿间隙卡住"))
    # knuckle plate
    circ = [(C1S[0] + 40 * math.cos(t), C1S[1] + 40 * math.sin(t)) for t in [2 * math.pi * k / 48 for k in range(48)]]
    outline = _hull([(-30, -132), (30, -132), (30, -92), (-30, -92)] + circ)
    s8 = prism_xz(outline, Y["knuckle"][0], Y["knuckle"][1])
    s8 = holes_y(s8, pcd(C1S[0], C1S[1], 27.5, 6, 30), 4.25)
    s8 = holes_y(s8, [C1S], 15.5)
    parts.append(Part("S8", "节点板", "S355 12 mm", "seat", s8, color=COLORS["steel_dark"],
                      params=[("厚", "12 mm（y 204 … 216）"), ("外形", "横梁端 60 × 40 + 铰点 1 处 R40 的包络"), ("中心孔", "Ø31（铰点 1 轴线）"),
                              ("螺纹孔", "6 × M10（底孔 Ø8.5），PCD 55"), ("铰点 1 中心（座板坐标）", f"({C1S[0]:.1f}, {C1S[1]:.1f})")],
                      note="BOM 原写 14 mm；为给 J1 法兰让位改为 12 mm（y 204 … 216），横梁焊在 y = 204 面上"))
    # pin-1 shaft with flange
    fl = cyl_y(C1S[0], C1S[1], Y["flange"][0], Y["flange"][1], 37.5)
    fl = holes_y(fl, pcd(C1S[0], C1S[1], 27.5, 6, 30), 5.5)
    sh = cyl_y(C1S[0], C1S[1], Y["flange"][1], Y["shaft_end"], 15)
    try:
        sh = sh.faces(">Y").edges().chamfer(2)
    except Exception:
        pass
    j1 = fl.union(sh)
    parts.append(Part("J1", "铰点 1 轴", "42CrMo4 调质", "seat", j1, color=COLORS["steel_dark"],
                      params=[("法兰", "Ø75 × 10（y 216 … 226），6 × Ø11 PCD 55"), ("轴径", "Ø30 k5（轴承位）"), ("轴长", "76 mm（y 226 … 302）"),
                              ("螺纹", "M30 × 1.5（y 290 … 302），装 KM6"), ("轴承位", "y 229 … 246、274 … 291（间距 45）"), ("摆臂位", "y 249 … 271，Ø30 胀紧套")],
                      note="座板绕它转（转动副 R1）；法兰用 6 颗 M10-10.9 接 S8"))
    nut = tube_y(C1S[0], C1S[1], Y["locknut"][0], Y["locknut"][1], 22.5, 15)
    parts.append(Part("J5", "锁紧螺母 KM6", "KM6（M30 × 1.5）+ MB6 止动垫圈", "seat", nut, color=COLORS["buy"], buy=True, drawing=False,
                      params=[("规格", "KM6，M30 × 1.5"), ("外形", "Ø45 × 7"), ("位置", "y 308 … 315")], note="外购件：给两个圆锥滚子轴承加预紧"))
    # pin-2 arm
    dx, dz = C2S[0] - C1S[0], C2S[1] - C1S[1]; Ln = math.hypot(dx, dz); ux, uz = dx / Ln, dz / Ln; nx, nz = -uz * 15, ux * 15
    plate = prism_xz([(C1S[0] + nx, C1S[1] + nz), (C2S[0] + nx, C2S[1] + nz), (C2S[0] - nx, C2S[1] - nz), (C1S[0] - nx, C1S[1] - nz)], Y["arm_c2"][0], Y["arm_c2"][1])
    plate = plate.union(cyl_y(C2S[0], C2S[1], Y["arm_c2"][0], Y["arm_c2"][1], 15))
    hub = cyl_y(C1S[0], C1S[1], Y["hub"][0], Y["hub"][1], 25)
    j4 = hub.union(plate)
    j4 = holes_y(j4, [C1S], 15); j4 = holes_y(j4, [C2S], 5.1)
    parts.append(Part("J4", "铰点 2 摆臂", "S355 12 mm", "seat", j4, color=COLORS["steel"],
                      params=[("臂厚", "12 mm（y 258 … 270）"), ("臂宽", "30 mm，端部 R15"), ("孔距", f"{Ln:.1f} mm（铰点 1 → 铰点 2）"), ("毂", "Ø50 × 24（y 258 … 282），孔 Ø30"),
                              ("铰点 2 孔", "Ø10.2（M10 杆端销）"), ("铰点 2（座板坐标）", f"({C2S[0]:.1f}, {C2S[1]:.1f})")],
                      note="从轴承座筒的窗口伸出；用 Ø30 胀紧套接 J1（传约 180 N·m），不用单键"))
    return parts

if __name__ == "__main__":
    P = build(); print(L.check(P))
