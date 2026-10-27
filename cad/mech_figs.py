"""Static figures for cad/mechanism.html: side view and top view with part balloons, section along the c1 axis with balloons,
and four FEA diagrams (supports, loads, welds). World mm, z up; part codes are the BOM codes of build_sheet.py."""
import math, html
import numpy as np
import build_sheet as BS

PT, D, YS = BS.PT, BS.D, BS.YS
KP0, KP1 = D["key_poses"]["齐平（起点）"], D["key_poses"]["顶（终点）"]
E = np.array(D["rail_dirs"]["e"]); NF = np.array(D["rail_dirs"]["nf_rail1_to_rail2"])
mmv = lambda p: np.array(p, float) * 1000
B = mmv(D["link"]["ground_pivot_B"]); R1 = [mmv(p) for p in (D["rail1"]["lo"], D["rail1"]["hi"])]; R2 = [mmv(p) for p in (D["rail2"]["lo"], D["rail2"]["hi"])]
SC = [mmv(p) for p in (D["screw"]["axis_lo"], D["screw"]["axis_hi"])]; HOUSE = [mmv(p) for p in PT["housing"]["outline_xz"]]; MOTOR = [mmv(p) for p in D["housing"]["motor_xz"]]
H = 1000 * D["seat"]["half_len"]; LIP = 1000 * D["seat"]["lip"]
SEAT = {"foamr": [(-H, 0), (-20, 0), (-20, -50), (-H, -50)], "foamf": [(-20, 0), (H, 0), (H, -80), (-20, -80)], "board": [(-H + LIP, -50), (-20, -50), (-20, -80), (H, -80), (H, -92), (-H + LIP, -92)],
        "arm": [(-40, -100), (75, -100), (75, -110), (-40, -110)], "beam": [(-25, -100), (25, -100), (25, -130), (-25, -130)]}

def Wt(Q, phi, p):
    a = math.radians(phi); return np.array([Q[0] + math.cos(a) * p[0] + math.sin(a) * p[1], Q[1] - math.sin(a) * p[0] + math.cos(a) * p[1]])

class Fig:
    """viewBox in mm; horizontal u, vertical v (v up)."""
    def __init__(self, u0, u1, v0, v1, label, cls="fig"):
        self.u0, self.v1 = u0, v1; self.o = [f'<svg class="{cls}" viewBox="0 0 {u1 - u0:.0f} {v1 - v0:.0f}" role="img" aria-label="{html.escape(label)}">']
    X = lambda s, u: u - s.u0
    Y = lambda s, v: s.v1 - v
    def pts(s, P): return " ".join(f"{s.X(p[0]):.1f},{s.Y(p[1]):.1f}" for p in P)
    def poly(s, P, cls, extra=""): s.o.append(f'<polygon class="{cls}" points="{s.pts(P)}" {extra}/>')
    def line(s, a, b, cls, extra=""): s.o.append(f'<line class="{cls}" x1="{s.X(a[0]):.1f}" y1="{s.Y(a[1]):.1f}" x2="{s.X(b[0]):.1f}" y2="{s.Y(b[1]):.1f}" {extra}/>')
    def rect(s, u0, u1, v0, v1, cls, extra=""): s.o.append(f'<rect class="{cls}" x="{s.X(u0):.1f}" y="{s.Y(v1):.1f}" width="{u1 - u0:.1f}" height="{v1 - v0:.1f}" {extra}/>')
    def circ(s, c, r, cls, extra=""): s.o.append(f'<circle class="{cls}" cx="{s.X(c[0]):.1f}" cy="{s.Y(c[1]):.1f}" r="{r}" {extra}/>')
    def text(s, p, t, cls="lab", anchor="start", dx=0, dy=0): s.o.append(f'<text class="{cls}" x="{s.X(p[0]) + dx:.1f}" y="{s.Y(p[1]) + dy:.1f}" text-anchor="{anchor}">{html.escape(t)}</text>')
    def balloon(s, code, anchor, pos, r=17):
        a, p = np.array(anchor, float), np.array(pos, float); d = a - p; n = np.hypot(*d) or 1; q = p + d / n * r
        s.o.append(f'<g class="bal" data-code="{code}"><line class="ldr" x1="{s.X(q[0]):.1f}" y1="{s.Y(q[1]):.1f}" x2="{s.X(a[0]):.1f}" y2="{s.Y(a[1]):.1f}"/>'
                   f'<circle class="ldot" cx="{s.X(a[0]):.1f}" cy="{s.Y(a[1]):.1f}" r="3.5"/><circle class="bc" cx="{s.X(p[0]):.1f}" cy="{s.Y(p[1]):.1f}" r="{r}"/>'
                   f'<text class="bt" x="{s.X(p[0]):.1f}" y="{s.Y(p[1]) + 5:.1f}" text-anchor="middle">{code}</text></g>')
    def hatch_fix(s, a, b, side=-1, cls="fixh"):
        """fixed support along segment a-b, hatch on the 'side' normal."""
        a, b = np.array(a, float), np.array(b, float); d = (b - a) / np.hypot(*(b - a)); n = np.array([-d[1], d[0]]) * side
        s.line(a, b, "fixl"); L = np.hypot(*(b - a)); k = 0
        while k <= L:
            p = a + d * k; s.line(p, p + 12 * n - 8 * d, cls); k += 10
    def arrow(s, a, b, cls="farr"): s.line(a, b, cls, 'marker-end="url(#fa)"')
    def end(s): s.o.append("</svg>"); return "".join(s.o)

DEFS = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
        '<marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" class="fah"/></marker>'
        '<pattern id="hat" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="9" class="hatl"/></pattern></defs></svg>')

def side_view():
    f = Fig(-170, 840, -30, 1000, "侧视总装图：按比例，座板在齐平位，带零件编号")
    f.rect(-170, 0, 0, 420, "bed"); f.text((-160, 210), "床", "lab muted")
    f.rect(-170, 840, -14, 0, "", 'fill="url(#hat)"'); f.line((-170, 0), (840, 0), "floor")
    f.poly(HOUSE, "house"); f.rect(30, 780, 0, 35, "base"); f.rect(200, 620, 35, 47, "base")
    for r in (R1, R2): f.line(r[0], r[1], "rail")
    f.line(SC[0], SC[1], "screw"); f.poly(MOTOR, "motor")
    f.line((700, 35), (700, 950), "post"); f.circ((700, 950), 19, "barc")
    for kp, ghost in ((KP1, True), (KP0, False)):
        Q, phi, P1, P2 = mmv(kp["Q"]), kp["phi"], mmv(kp["P1"]), mmv(kp["P2"]); g = " ghost" if ghost else ""
        corner = [P1 + 190 * E - 25 * NF, P1 + 190 * E + 175 * NF, P1 - 40 * E + 175 * NF] + [P1 - 42 * (math.cos(a) * E + math.sin(a) * NF) for a in np.linspace(0, math.pi / 2, 7)]
        f.poly(corner, "plate" + g)
        if not ghost:
            for o in (0, 150):
                for s_ in (0, 150):
                    c = P1 + s_ * E + o * NF; f.poly([c - 30.7 * E - 17 * NF, c + 30.7 * E - 17 * NF, c + 30.7 * E + 17 * NF, c - 30.7 * E + 17 * NF], "carr")
            nc = P1 + 75 * E + 75 * NF; f.poly([nc - 22 * E - 14 * NF, nc + 22 * E - 14 * NF, nc + 22 * E + 14 * NF, nc - 22 * E + 14 * NF], "nut")
        f.line(B, P2, "linkp" + g); f.line(P1, P2, "armc2" + g)
        for k in ("beam", "arm", "board", "foamf", "foamr"): f.poly([Wt(Q, phi, p) for p in SEAT[k]], k + g)
        f.circ(P1, 37.5, "cartc" + g); f.circ(P2, 14.5, "rodp" + g)
    f.circ(B, 14.5, "rodp"); f.rect(B[0] - 30, B[0] + 30, B[1] - 34, B[1] - 20, "base")
    Q0, P1, P2 = mmv(KP0["Q"]), mmv(KP0["P1"]), mmv(KP0["P2"])
    f.text(mmv(KP1["Q"]) + np.array([-40, 40]), "顶位（虚影）", "lab muted", "end")
    bl = [("S1", Wt(Q0, KP0["phi"], (-55, -20)), (-110, 650)), ("S2", Wt(Q0, KP0["phi"], (50, -30)), (-50, 650)), ("S4", Wt(Q0, KP0["phi"], (70, -86)), (-110, 590)),
          ("S7", Wt(Q0, KP0["phi"], (-10, -118)), (-110, 530)), ("J3", P1 + np.array([-30, 15]), (-110, 470)), ("J4", (P1 + P2) / 2, (-110, 300)), ("L2", P2, (-110, 240)),
          ("L1", B + 0.55 * (P2 - B), (300, 80)), ("L3", B + np.array([0, -25]), (420, 80)),
          ("C1", P1 + 100 * E + 60 * NF, (610, 600)), ("C2", P1 + 150 * E + 150 * NF, (610, 660)), ("D1", R2[0] + 0.85 * (R2[1] - R2[0]), (610, 760)),
          ("D2", SC[0] + 0.62 * (SC[1] - SC[0]), (610, 540)), ("D4", np.mean(MOTOR, 0), (610, 860)), ("H1", (505, 300), (610, 420)),
          ("B2", (580, 41), (610, 140)), ("B1", (740, 18), (790, 120)), ("B4", (700, 650), (790, 650)), ("B5", (700, 950), (790, 900))]
    for c, a, p in bl: f.balloon(c, a, p)
    return f.end()

def top_view():
    f = Fig(-170, 880, -330, 470, "俯视图：座板在齐平位，看横向（y）布置，带零件编号")
    Yv = lambda y: y
    f.rect(-170, 0, -330, 470, "bed"); f.text((-160, 0), "床", "lab muted"); f.text((-160, -300), "床尾方向 ↓", "lab muted"); f.text((-160, 440), "床头方向 ↑", "lab muted")
    f.rect(30, 780, -270, 380, "baseo"); f.rect(90, 720, -210, 320, "paper")
    f.rect(200, 620, -220, 220, "footp")
    f.rect(15, 517, 250, 358, "house")
    f.rect(min(R1[0][0], R2[0][0]), max(R1[1][0], R2[1][0]), 321, 336, "railt")
    Q0x = 1000 * KP0["Q"][0]; P1x = 1000 * KP0["P1"][0]
    f.rect(Q0x - H, Q0x + H, -220, 220, "foamf"); f.rect(Q0x - H, Q0x - 20, -220, 220, "foamr")
    f.rect(Q0x - 25, Q0x + 25, -205, 212, "beamd"); f.rect(Q0x - 30, Q0x + 30, 212, 226, "beam")
    f.rect(P1x - 37.5, P1x + 37.5, 229, 308, "cartc"); f.rect(1000 * KP0["P1"][0] - 40, 1000 * KP0["P1"][0] + 190 * E[0], 288, 308, "plate")
    f.line((1000 * KP0["P2"][0], 275), (B[0], 275), "linkp")
    f.rect(670, 730, 270, 330, "base"); f.rect(681, 719, -50, 300, "barc")
    f.line((Q0x, -300), (Q0x, 470), "axisl"); f.text((Q0x + 6, -300), "座面中心（齐平位）", "lab muted")
    f.text((300, -300), "敞开一侧：人的腿从这边放下", "lab"); f.text((540, 400), "机构箱（床头一侧）", "lab")
    bl = [("S2", (Q0x + 40, -150), (-60, -240)), ("S7", (Q0x, -60), (-60, -170)), ("S8", (Q0x - 30, 219), (-60, 150)), ("J3", (P1x, 268), (-60, 250)),
          ("C1", (P1x + 80, 298), (230, 430)), ("D1", (300, 328), (330, 430)), ("L1", (300, 275), (430, 430)), ("H1", (480, 345), (530, 430)),
          ("B2", (420, -100), (660, -300)), ("B1", (760, -100), (810, -200)), ("B4", (700, 300), (810, 260)), ("B5", (700, 60), (810, 60))]
    for c, a, p in bl: f.balloon(c, a, p)
    for yy in (-220, 0, 220, 358):
        f.line((790, yy), (800, yy), "grid"); f.text((803, yy), f"y {yy}", "tick", dy=4)
    return f.end()

def section_view(with_ids=True):
    """along the c1 axis; y horizontal (to scale), the other direction schematic. data-part for the load-path stepper."""
    c = 69.7; f = Fig(-260, 400, -232, 175, "沿铰点 1 轴线的剖面：座板、横梁、节点板、铰点 1 轴、两个圆锥滚子轴承、内壁竖槽、铰点 2 摆臂、滑块板、滑块、导轨、侧板")
    f.o[0] = f.o[0].replace('<svg class="fig"', '<svg class="fig" id="sec"')
    def R(y0, y1, v0, v1, cls, part): f.rect(y0, y1, v0, v1, cls, f'data-part="{part}"')
    R(-220, 220, c - 50, c, "foamr", "seat"); R(-220, 220, c - 80, c - 50, "foamf", "seat"); R(-220, 220, c - 92, c - 80, "board", "seat")
    for yy in (-180, 180): R(yy - 12, yy + 12, c - 100, c - 92, "scell", "cells")
    R(-205, 204, c - 130, c - 100, "beam", "beam"); R(-200, -160, c - 110, c - 100, "beam", "cells"); R(160, 200, c - 110, c - 100, "beam", "cells")
    R(204, 216, -62, 40, "beam", "knuckle"); R(216, 226, -37.5, 37.5, "shaft", "shaft"); R(226, 302, -15, 15, "shaft", "shaft"); R(249, 271, -25, 25, "shaft", "shaft")
    R(229, 308, 27.5, 37.5, "cartc", "cart"); R(229, 247, -37.5, -27.5, "cartc", "cart"); R(273, 308, -37.5, -27.5, "cartc", "cart")
    for (y0, y1), part in (((229, 246), "brgB"), ((274, 291), "brgA")):
        for v0, v1 in ((15, 27.5), (-27.5, -15)):
            R(y0, y1, v0, v1, "sbrg", part); f.line((y0, v1), (y1, v0), "sbrgx", f'data-part="{part}"')
    R(292, 299, -22.5, -15, "nut", "shaft"); R(292, 299, 15, 22.5, "nut", "shaft")
    R(250, 253, 43.5, 160, "swall", "wall"); R(250, 253, -200, -43.5, "swall", "wall")
    for vv in (43.5, -43.5): f.line((246, vv), (257, vv), "brush")
    R(258, 270, -122, -12, "beam", "arm"); f.o.append(f'<circle class="rodp" data-part="arm" cx="{f.X(275):.1f}" cy="{f.Y(-117):.1f}" r="14.5"/>')
    f.line((275, -132), (275, -200), "linkp", 'data-part="arm"')
    R(288, 308, -42, 160, "plate", "plate")
    for vv in (0.0, 105.0): R(308, 324, vv - 30.7, vv + 30.7, "carr", "carr")
    R(324, 336, -200, 160, "railt", "rail"); R(336, 351, -200, 160, "sback", "back"); R(356, 358, -200, 160, "swall", "back")
    f.line((195, 0), (340, 0), "axisl"); f.text((193, 0), "铰点 1 轴线", "lab", "end", dy=4)
    f.arrow((-100, c + 70), (-100, c + 4)); f.text((-100, c + 78), "偏 10 cm 的体重", "lab", "middle")
    bl = [("S1", (-150, c - 25), (-245, 150)), ("S2", (-60, c - 65), (-200, 150)), ("S4", (-130, c - 86), (-245, -40)), ("S5", (-190, c - 96), (-245, -90)),
          ("S7", (-60, c - 115), (-150, -150)), ("S6", (180, c - 105), (130, -150)), ("S8", (210, -50), (200, -190)),
          ("J1", (290, 0), (300, 150)), ("J2", (283, 22), (200, 150)), ("J3", (296, 33), (250, 150)), ("H2", (251, 100), (150, 120)),
          ("J4", (264, -80), (215, -150)), ("L2", (275, -117), (320, -190)), ("C1", (298, 120), (350, 150)), ("C2", (316, 105), (380, 110)),
          ("D1", (330, -150), (382, -120)), ("H1", (343, -60), (382, -60))]
    for code, a, p in bl: f.balloon(code, a, p, 15)
    for yy in (-220, 0, 220, 250, 288, 336):
        f.line((yy, -222), (yy, -214), "grid"); f.text((yy, -232), str(yy), "tick", "middle", dy=-2)
    return f.end()

# ---------------------------------------------------------------- FEA diagrams
def fea_c1():
    f = Fig(120, 400, -125, 140, "有限元重点 1：铰点 1 组件和滑块座焊件", "fig fs")
    R = f.rect
    R(204, 216, -62, 40, "beam dim"); R(216, 226, -37.5, 37.5, "shaft"); R(226, 302, -15, 15, "shaft"); R(249, 271, -25, 25, "shaft")
    R(229, 308, 27.5, 37.5, "cartc hot"); R(229, 247, -37.5, -27.5, "cartc hot"); R(273, 308, -37.5, -27.5, "cartc hot")
    for y0, y1 in ((229, 246), (274, 291)):
        for v0, v1 in ((15, 27.5), (-27.5, -15)): R(y0, y1, v0, v1, "sbrg"); f.line((y0, v1), (y1, v0), "sbrgx")
    R(288, 308, -42, 110, "plate hot"); R(250, 253, 43.5, 115, "swall"); R(250, 253, -110, -43.5, "swall")
    for vv in (0.0, 80.0): R(308, 324, vv - 30.7, vv + 30.7, "carr")
    for vv in (0.0, 80.0): f.hatch_fix((324, vv - 30), (324, vv + 30), side=-1)
    for p in ((280, 37.5), (280, -37.5)): f.poly([(p[0], p[1]), (p[0] + 8, p[1] + 8), (p[0] + 8, p[1] - 8)], "weld")
    f.arrow((205, 60), (205, 10)); f.text((200, 66), "−F₁", "lab", "end")
    f.o.append(f'<path class="marc" d="M {f.X(180):.1f} {f.Y(-20):.1f} A 26 26 0 1 1 {f.X(180):.1f} {f.Y(22):.1f}" marker-end="url(#fa)"/>'); f.text((160, -40), "−M₁", "lab", "middle")
    f.text((260, -60), "窗口（80°）", "lab", "middle"); f.text((330, 118), "滑块面固定", "lab", "middle")
    f.text((250, 122), "▲ = 焊缝", "lab", "middle")
    return f.end()

def fea_beam():
    f = Fig(-250, 360, -150, 112, "有限元重点 2：座板横梁和节点板")
    f.rect(-220, 220, 12, 24, "board dim"); f.rect(-205, 212, -18, 12, "beam hot"); f.rect(212, 226, -60, 40, "beam hot"); f.rect(226, 245, -20, 20, "shaft")
    f.hatch_fix((245, -40), (245, 40), side=-1)
    f.arrow((-100, 80), (-100, 26)); f.text((-100, 84), "1471 N（+ 沿座面、侧向 0.3 倍）", "lab", "middle")
    f.o.append(f'<path class="defl" d="M {f.X(212):.1f} {f.Y(-3):.1f} Q {f.X(0):.1f} {f.Y(-8):.1f} {f.X(-205):.1f} {f.Y(-40):.1f}"/>'); f.text((-205, -52), "外缘下沉 ≈ 1.7 mm（放大画）", "lab")
    for p in ((205, 12), (205, -18)): f.poly([(p[0], p[1]), (p[0] - 8, p[1] + 8), (p[0] - 8, p[1] - 8)], "weld")
    f.text((210, -75), "焊缝：横梁 ↔ 节点板（最大弯矩处）", "lab", "end"); f.text((248, -50), "轴端法兰面固定", "lab")
    f.line((-150, -18), (-150, 12), "dimln"); f.text((-145, -6), "高 30（被小腿间隙卡住）", "lab")
    f.text((-220, -120), "y = −220（座板外缘）", "tick"); f.text((212, -120), "y = 212", "tick", "middle")
    return f.end()

def fea_house():
    f = Fig(-30, 600, -50, 860, "有限元重点 3：机构箱盒体（带竖槽）")
    f.poly(HOUSE, "house hot"); f.hatch_fix((15, 40), (517, 40), side=-1)
    P1a, P1b = mmv(KP0["P1"]), mmv(KP1["P1"]); d = (P1b - P1a) / np.hypot(*(P1b - P1a)); n = np.array([-d[1], d[0]])
    ang0 = math.atan2(n[1], n[0]); st = [P1b + 43.5 * np.array([math.cos(ang0 - a), math.sin(ang0 - a)]) for a in np.linspace(0, math.pi, 13)]
    st += [P1a + 43.5 * np.array([math.cos(ang0 + math.pi - a), math.sin(ang0 + math.pi - a)]) for a in np.linspace(0, math.pi, 13)]; f.poly(st, "slot")
    f.text(P1b + np.array([-60, 70]), "内壁竖槽（宽 87）", "lab", "end")
    cp = PT["cases"]["housing_Mx_Nm"]["carriage_points_mm"]
    for p in cp: f.circ((p[0], p[2]), 9, "oop"); f.circ((p[0], p[2]), 3, "oopd")
    f.text((cp[1][0] - 10, cp[1][2] + 40), "⊙ 滑块力（主要垂直纸面）", "lab", "middle")
    f.text((30, 10), "底边和底座螺栓连接：固定", "lab")
    return f.end()

def fea_rail():
    f = Fig(-160, 620, -40, 1080, "有限元重点 4：扶手立柱和底座（正视，看 y-z 平面）", "fig fl")
    f.rect(-120, 400, 0, 35, "base hot"); f.hatch_fix((-120, 0), (400, 0), side=-1)
    f.rect(270, 330, 35, 950, "base hot"); f.rect(-50, 300, 931, 969, "barc")
    for p in ((270, 35), (330, 35)): f.poly([(p[0], p[1]), (p[0] - 8 if p[0] < 300 else p[0] + 8, p[1] + 8), (p[0], p[1] + 16)], "weld")
    f.arrow((-50, 1050), (-50, 975)); f.text((-40, 1040), "1668 N 向下", "lab")
    f.arrow((-140, 950), (-60, 950)); f.text((-140, 920), "侧推", "lab")
    f.circ((-30, 950), 11, "oop"); f.circ((-30, 950), 3.5, "oopd"); f.text((-10, 890), "向人拉（垂直纸面）", "lab")
    f.text((340, 120), "根部弯矩 1.53 kN·m", "lab"); f.text((340, 80), "焊缝 + 底座管局部", "lab")
    return f.end()
