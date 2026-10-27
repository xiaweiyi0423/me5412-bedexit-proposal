"""Build cad/cad_sheet.html (the dimension sheet for the CAD model, role 3) from model/calc_v13/seat_1dof/cad_sheet.json and
cad/travel_table.csv. Regenerate the inputs with model/calc_v13/seat_1dof_cad_sheet.py after any model change, then run this."""
import csv, json, math, os, html
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/cad_sheet.json")))
C3 = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/cantilever3d.json")))
PT = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/parts.json"))); ST = PT["statics"]; YS = PT["y_stack"]; kN = lambda k: f'{ST[k]["value"] / 1000:.1f}'
TT = list(csv.reader(open(os.path.join(HERE, "travel_table.csv")))); KP = list(csv.reader(open(os.path.join(HERE, "key_poses.csv"))))
mm = lambda v: (lambda t: t[:-2] if t.endswith(".0") else t)(f"{1000 * v:.1f}").replace("-", "−"); P = lambda p: f"({mm(p[0])}, {mm(p[1])})"
J = D["joints"]; brake = 2 * ST["nut_axial_N"]["value"] * D["screw"]["lead_mm"] / 1000 / (2 * math.pi)

def W(Q, phi, p):                       # seat frame -> world (x, z); phi forward tilt in degrees
    a = math.radians(phi); return (Q[0] + math.cos(a) * p[0] + math.sin(a) * p[1], Q[1] - math.sin(a) * p[0] + math.cos(a) * p[1])

# ---------------------------------------------------------------- side view (x-z), to scale, mm
S = 0.62                                # px per mm
X0, X1, Z0, Z1 = -320, 820, -30, 1010
sx = lambda x: (1000 * x - X0) * S; sz = lambda z: (Z1 - 1000 * z) * S
Wd, Hd = (X1 - X0) * S, (Z1 - Z0) * S
def poly(pts, cls): return f'<polygon class="{cls}" points="' + " ".join(f"{sx(x):.1f},{sz(z):.1f}" for x, z in pts) + '"/>'
def line(a, b, cls): return f'<line class="{cls}" x1="{sx(a[0]):.1f}" y1="{sz(a[1]):.1f}" x2="{sx(b[0]):.1f}" y2="{sz(b[1]):.1f}"/>'
def dot(p, cls="pin", r=4): return f'<circle class="{cls}" cx="{sx(p[0]):.1f}" cy="{sz(p[1]):.1f}" r="{r}"/>'
def lab(p, t, dx=8, dy=-6, cls="lab", anchor="start"): return f'<text class="{cls}" x="{sx(p[0]) + dx:.1f}" y="{sz(p[1]) + dy:.1f}" text-anchor="{anchor}">{html.escape(t)}</text>'
h = D["seat"]["half_len"]; lip = D["seat"]["lip"]
def seat(Q, phi, cls):
    rear = [W(Q, phi, p) for p in ((-h, 0), (-0.02, 0), (-0.02, -0.05), (-h, -0.05))]
    front = [W(Q, phi, p) for p in ((-0.02, 0), (h, 0), (h, -0.08), (-0.02, -0.08))]
    spacer = [W(Q, phi, p) for p in ((-h + lip, -0.05), (-0.02, -0.05), (-0.02, -0.08), (-h + lip, -0.08))]
    board = [W(Q, phi, p) for p in ((-h + lip, -0.08), (h, -0.08), (h, -0.092), (-h + lip, -0.092))]
    bm = PT["beam"]; beam = [W(Q, phi, p) for p in ((bm["xs"][0], bm["zs"][0]), (bm["xs"][1], bm["zs"][0]), (bm["xs"][1], bm["zs"][1]), (bm["xs"][0], bm["zs"][1]))]
    arm = [W(Q, phi, p) for p in ((-0.04, -0.100), (0.075, -0.100), (0.075, -0.110), (-0.04, -0.110))]
    return (poly(rear, cls + " foamr") + poly(front, cls + " foamf") + poly(spacer, cls + " board") + poly(board, cls + " board") + poly(arm, cls + " board") +
            poly(beam, cls + " beam"))
F0, F1 = D["key_poses"]["齐平（起点）"], D["key_poses"]["顶（终点）"]; B = D["link"]["ground_pivot_B"]
svg = [f'<svg viewBox="0 0 {Wd:.0f} {Hd:.0f}" role="img" aria-label="侧视图（x-z 平面），按比例：床、底座、机构箱、两根导轨、丝杠、电机、连杆、座板在齐平位和顶位、横杆和踏板">']
for g in range(-300, 801, 100):                                           # grid every 100 mm
    svg.append(f'<line class="grid" x1="{(g - X0) * S:.1f}" y1="0" x2="{(g - X0) * S:.1f}" y2="{Hd:.1f}"/>')
    svg.append(f'<text class="tick" x="{(g - X0) * S + 3:.1f}" y="{Hd - 4:.1f}">{g}</text>')
for g in range(0, 1001, 100):
    svg.append(f'<line class="grid" x1="0" y1="{(Z1 - g) * S:.1f}" x2="{Wd:.1f}" y2="{(Z1 - g) * S:.1f}"/>')
    svg.append(f'<text class="tick" x="3" y="{(Z1 - g) * S - 3:.1f}">{g}</text>')
svg.append(poly([(-0.32, 0), (0, 0), (0, 0.36), (-0.32, 0.36)], "bed")); svg.append(poly([(-0.32, 0.36), (0, 0.36), (0, D["bed"]["top_z"]), (-0.32, D["bed"]["top_z"])], "mat"))
svg.append(lab((-0.31, 0.43), "床垫面 z 420", 0, -4)); svg.append(lab((-0.31, 0.18), "床（x < 0）", 0, 0, "lab muted"))
svg.append(line((-0.32, 0), (0.82, 0), "floor"))
b = D["base"]; svg.append(poly([(b["x"][0], 0), (b["x"][1], 0), (b["x"][1], b["tube_h"]), (b["x"][0], b["tube_h"])], "base"))
fp = D["footplate"]; svg.append(poly([(fp["x"][0], fp["z"][0]), (fp["x"][1], fp["z"][0]), (fp["x"][1], fp["z"][1]), (fp["x"][0], fp["z"][1])], "plate"))
svg.append(poly(PT["housing"]["outline_xz"], "housing")); svg.append(poly(D["housing"]["motor_xz"], "motor"))
r1, r2, sc = D["rail1"], D["rail2"], D["screw"]
svg.append(line(r1["lo"], r1["hi"], "rail")); svg.append(line(r2["lo"], r2["hi"], "rail")); svg.append(line(sc["axis_lo"], sc["axis_hi"], "screw"))
svg.append(seat(F1["Q"], F1["phi"], "ghost")); svg.append(line(B, F1["P2"], "link ghostl"))
svg.append(seat(F0["Q"], F0["phi"], "now")); svg.append(line(B, F0["P2"], "link"))
for p, cl in ((F0["P1"], "cart"), (F1["P1"], "cart ghostp")): svg.append(f'<circle class="{cl}" cx="{sx(p[0]):.1f}" cy="{sz(p[1]):.1f}" r="{37.5 * S:.1f}"/>')
for p in (F0["P1"], F0["P2"]): svg.append(dot(p))
for p in (F1["P1"], F1["P2"]): svg.append(dot(p, "pin ghostp"))
svg.append(dot(B, "pivot", 5))
hr = D["handrail"]; svg.append(line((hr["post"]["x"], b["tube_h"]), (hr["post"]["x"], hr["post"]["top_z"]), "post")); svg.append(dot((hr["post"]["x"], hr["post"]["top_z"]), "bar", 7))
SC40 = (sc["axis_lo"][0] + 0.45 * (sc["axis_hi"][0] - sc["axis_lo"][0]), sc["axis_lo"][1] + 0.45 * (sc["axis_hi"][1] - sc["axis_lo"][1]))
L = [(F0["Q"], "Q 座面中心（齐平）", 10, 18), (F1["Q"], "Q（顶位）", -12, -14), (F0["P1"], "铰点 1", -10, 4), (F0["P2"], "铰点 2", -10, 4), (B, "连杆地面铰点 B", 10, 4),
     (r1["hi"], "导轨 1", -10, -4), (r2["hi"], "导轨 2", 8, 12), (SC40, "丝杠轴线", 10, 4), (D["housing"]["motor_xz"][1], "电机 + 制动器", 8, -6),
     ((hr["post"]["x"], hr["post"]["top_z"]), "横杆（垂直纸面） z 950", -12, -12), ((0.42, 0.047), "踏板", 0, -8), ((0.517, 0.40), "机构箱（侧视外廓，v5.7）", 6, 0), ((F0["P1"][0] + 0.04, F0["P1"][1] + 0.03), "铰点 1 轴承座 Ø75", 4, -2),
     ((PT["clearances"]["housing_bed_point"][0], PT["clearances"]["housing_bed_point"][1]), f'离床最近 {PT["clearances"]["housing_bed_cm"] * 10:.0f}', -6, 16)]
for p, t, dx, dy in L: svg.append(lab(p, t, dx, dy, "lab", "end" if dx < 0 else "start"))
svg.append("</svg>")

def table(head, rows, cls=""):
    return (f'<div class="tw"><table class="{cls}"><thead><tr>' + "".join(f"<th>{x}</th>" for x in head) + "</tr></thead><tbody>" +
            "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table></div>")
rng = lambda t: f"{mm(t[0])} … {mm(t[1])}"
Y = {"座板（宽 440）": "−220 … +220", "横梁": rng(PT["beam"]["y"]), "节点板（横梁端头）": rng(YS["knuckle"]), "铰点 1 轴承 B（座板侧）": rng(YS["brgB"]),
     "机构箱内壁 2 mm（竖槽所在）": rng(YS["wall_in"]), "铰点 2 摆臂 12 mm": "258 … 270", "连杆平面（杆端中心）": mm(YS["link"]),
     "滑块板 20 mm": rng(YS["plate"]), "铰点 1 轴承 A（在滑块板孔里）": rng(YS["brgA"]), "滑块受力面 / 丝杠轴线": mm(YS["carriage"]),
     "导轨底面 = 侧板内表面": mm(YS["back"][0]), "侧板 15 mm（导轨安装板）": rng(YS["back"]), "机构箱外壁": rng(YS["wall_out"]), "底座": f'{mm(b["y"][0])} … {mm(b["y"][1])}', "横杆": f'{mm(hr["bar"]["y"][0])} … {mm(hr["bar"]["y"][1])}', "扶手立柱": f'{mm(hr["post"]["y"])}'}
fixed = [["导轨 1 HGR15（铰点 1 的滑块在上面走）", f'下端 {P(r1["lo"])}，上端 {P(r1["hi"])}', f'长 {mm(r1["length"])}，与竖直成 {r1["angle_from_vertical_deg"]}°'],
         ["导轨 2 HGR15（只扛偏载）", f'下端 {P(r2["lo"])}，上端 {P(r2["hi"])}', f'与导轨 1 平行，在导轨平面内相距 {mm(r2["offset"])}，偏向前下方'],
         ["丝杠轴线", f'{P(sc["axis_lo"])} → {P(sc["axis_hi"])}', f'Ø16 导程 {sc["lead_mm"]:.0f}，行程 {mm(sc["stroke"])}；上端 BK12 固定，下端 BF12 浮动'],
         ["连杆地面铰点 B", P(B), f'连杆长 {mm(D["link"]["length"])}'],
         ["机构箱侧视外廓（v5.7：按零件实际外形 + 5 间隙 + 3 壁）", " ".join(P(p) for p in PT["housing"]["outline_xz"]), f'y {mm(YS["wall_in"][0])} … {mm(YS["wall_out"][1])}；侧视面积 {PT["housing"]["area_cm2"]} cm²，顶 z {mm(PT["housing"]["top_z"])}'],
         ["电机 + 制动器", " ".join(P(p) for p in D["housing"]["motor_xz"]), "制动器和限速器在丝杠上端；电机在丝杠旁、偏导轨 2 一侧，同步带 1:3"],
         ["底座框（管高 35）", f'x {mm(b["x"][0])} … {mm(b["x"][1])}', f'y {mm(b["y"][0])} … {mm(b["y"][1])}'],
         ["踏板", f'x {mm(fp["x"][0])} … {mm(fp["x"][1])}，z {mm(fp["z"][0])} … {mm(fp["z"][1])}', f'y {mm(fp["y"][0])} … {mm(fp["y"][1])}'],
         ["L 形扶手", f'立柱 x {mm(hr["post"]["x"])}，顶 z {mm(hr["post"]["top_z"])}', "横杆从立柱伸到人正前方，末端圆头软包、夜光"]]
seatrows = [["座板长（沿座面）", f'{mm(2 * h)}，从 Q 往后 {mm(h)}、往前 {mm(h)}', f'后端 {mm(lip)} 是软唇边（搭在床垫上），刚性部分从 x<sub>s</sub> = −{mm(h - lip)} 开始'],
            ["坐垫", f'后区 x<sub>s</sub> −{mm(h)} … {mm(D["seat"]["split_x_s"])}：厚 50；前区 {mm(D["seat"]["split_x_s"])} … +{mm(h)}：厚 80', "后 10 kPa/cm、前 3 kPa/cm（分区坐垫）"],
            ["底板", "12 mm 桦木多层板一整块，z<sub>s</sub> −80 … −92，x<sub>s</sub> −40 … +85", "后区下面加 30 mm 垫条（x<sub>s</sub> −40 … −20），把后区 50 mm 泡棉托到和前区齐平"],
            ["铰点 1（座板坐标）", f'({mm(D["seat"]["pins_seat_frame"]["c1"][0])}, {mm(D["seat"]["pins_seat_frame"]["c1"][1])})', "相对 Q，座板坐标系"],
            ["铰点 2（座板坐标）", f'({mm(D["seat"]["pins_seat_frame"]["c2"][0])}, {mm(D["seat"]["pins_seat_frame"]["c2"][1])})', f'两铰点相距 {mm(D["seat"]["pins_seat_frame"]["spacing"])}'],
            ["<s>座板下悬臂托架（假设截面）</s>", f'x<sub>s</sub> {mm(D["seat_arm"]["seat_frame_x"][0])} … {mm(D["seat_arm"]["seat_frame_x"][1])}，z<sub>s</sub> {mm(D["seat_arm"]["seat_frame_z"][0])} … {mm(D["seat_arm"]["seat_frame_z"][1])}', f'y {mm(D["seat_arm"]["y"][0])} … {mm(D["seat_arm"]["y"][1])}，从座板下穿过竖槽进箱'],
            ["横梁（v5.7）", f'x<sub>s</sub> {mm(PT["beam"]["xs"][0])} … {mm(PT["beam"]["xs"][1])}，z<sub>s</sub> {mm(PT["beam"]["zs"][0])} … {mm(PT["beam"]["zs"][1])}', f'y {rng(PT["beam"]["y"])}；S355 矩形管 50 × 30 × 4，端头焊节点板'],
            ["称重支臂 ×2、称重单元 ×4", "支臂 x<sub>s</sub> −40 … +75，z<sub>s</sub> −100 … −110；单元在 (−30, ±190)、(+60, ±190)", "支臂 S355 扁钢 40 × 10，焊在横梁两端、顶面和横梁齐平；单元夹在支臂和底板之间（高 ≤ 8）"],
            ["滑块板（v5.7）", "沿导轨：铰点 1 往下 40 到往上 190；垂直导轨：铰点 1 往后 25 到往前 175；靠铰点 1 的角倒成 R42（绕铰点 1）", f'y {rng(YS["plate"])}；S355 20 mm，和铰点 1 轴承座筒焊成一体后精加工'],
            ["滑块 HGH15CA ×4", "每根导轨 2 个，相距 150（沿导轨）", "滑块中心：铰点 1 处、铰点 1 往上 150；导轨 2 上对应位置"]]
C1 = PT["c1"]; LK = PT["link"]; CR = PT["carriage"]; DR = PT["drive"]; CL = PT["clearances"]; HB = PT["housing_box"]; HRL = PT["handrail"]; MS = PT["masses"]
jrows = [["铰点 1（座板 ↔ 滑块板，绕 y 转）", f'力矩 {ST["c1_moment_Nm"]["value"]:.0f} N·m + 力 {kN("c1_force_N")} kN',
          f'<b>必须能承受力矩。</b>v5.7 定为一对圆锥滚子轴承 32006 X，背对背，沿 y 相距 {C1["spacing_mm"]:.0f}：轴承 B 在座板侧缘外（y {rng(YS["brgB"])}），轴承 A 在滑块板孔里（y {rng(YS["brgA"])}）。'
          f'两个轴承装在一根 Ø75 的钢管（轴承座筒）里，筒焊在滑块板上，穿过内壁竖槽。每个轴承最大 {kN("brgA_radial_N")} kN，静安全系数 {C1["sf"]}。为什么不用交叉滚子轴承：见第 11 项'],
        ["铰点 2、B（连杆两端）", f'拉 {PT["link_forces_N"]["tension"] / 1000:.1f} / 压 {PT["link_forces_N"]["compression"] / 1000:.1f} kN', "杆端关节轴承 M10（SKF SIKAC 10 M 或同级，头部外径 ≤ 30），连杆只受拉压、不受侧向力"],
        ["丝杠螺母", f'轴向 {kN("nut_axial_N")} kN', f"浮动接头，只传轴向；失电制动器 ≥ {brake:.1f} N·m（2 倍保持力），选 8 N·m 级"],
        ["每个滑块 HGH15CA", f'垂直侧板 {kN("carriage_radial_y_N")} kN，导轨平面内 {kN("carriage_lateral_inplane_N")} kN', f'等效静载 {CR["P0_kN"]} kN × 1.3（4 个滑块受力不均）= {CR["P0_x13_kN"]} kN；额定静载 16.97 kN，安全系数 {CR["sf"]}'],
        ["应急拉索拨杆", "—", D["lever"]], ["和床的固定件", f'{PT["tipping"]["固定件拉力（ADA 609 扶手设计载荷 1112 N，安全系数 1.5）"]["anchor_N"]} N', "锁在床架或床腿上（ADA 扶手载荷 1112 N × 1.5）；形式待定"]]
clr = [["机构箱离床（静止件）", f'{CL["housing_bed_cm"] * 10:.0f}', f'最近处是铰点 2 在齐平位时的杆端（x {mm(CL["housing_bed_point"][0] + 0.015)}，z {mm(CL["housing_bed_point"][1])}）。箱子不动，不夹人；要 ≥ 15 就换 M8 杆端（头部外径 ≤ 24）'],
       ["座板、横梁、支臂、铰点 1 轴承座离床（全行程）", f'{CL["seat_parts_bed_cm"] * 10:.0f}', "活动件；规则 ≥ 15"], ["座板侧缘到机构箱内壁", "30", "手指夹不住"],
       ["座板底面到底座（最低处）", f'{CL["seat_parts_floor_cm"] * 10:.0f}', ""],
       ["座板、横梁、支臂离小腿和脚（81 人，到站直）", f'{CL["legs_min_cm"] * 10:.0f}', "最紧的是 1.75 m、脚靠后的人站直时；v5.7 的横梁截面不改变它"]]

# ---------------------------------------------------------------- v5.7: parts, materials, checks
ok = lambda c: '<span class="ok">通过</span>' if c else '<span class="bad">不通过</span>'
bom = [
 ["坐垫", "S1", "后区泡棉", "高硬度再生（重组）海绵 100–150 kg/m³，或闭孔 EVA 叠层", "x<sub>s</sub> −85 … −20，厚 50，宽 440（含 45 软唇边，唇边下无底板）", "1", "目标：压缩 40% 时约 20 kPa"],
 ["", "S2", "前区泡棉", "高回弹（HR）海绵 45–55 kg/m³，高硬度级", "x<sub>s</sub> −20 … +85，厚 80，宽 440", "1", "目标：压缩 40% 时约 10 kPa"],
 ["", "S3", "面料", "防水、可擦洗的 PU 涂层弹力布，表面高摩擦", "包住 S1、S2，底面钉在 S4 上", "1", "防滑和清洁"],
 ["座板", "S4", "底板", "12 mm 桦木多层板", "x<sub>s</sub> −40 … +85，宽 440，z<sub>s</sub> −80 … −92", "1", "+ 后区垫条 30 × 20 × 440"],
 ["", "S5", "称重单元", "薄型，抗拔（螺栓固定的平行梁式，或加防掀限位）", f'高 ≤ 8；量程 ≥ 110 kg/只；位置 (−30, ±190)、(+60, ±190)', "4", f'每只受力 {PT["cells"]["min_N"]} … +{PT["cells"]["max_N"]} N'],
 ["", "S6", "称重支臂", "S355 扁钢 40 × 10", "x<sub>s</sub> −40 … +75，y ±190，顶面和横梁齐平", "2", "焊在横梁上"],
 ["", "S7", "横梁", "S355 矩形管 50 × 30 × 4", f'x<sub>s</sub> ±25，z<sub>s</sub> −100 … −130，y {rng(PT["beam"]["y"])}', "1", f'应力 {PT["beam"]["vm_MPa"]:.0f} / 允许 237 MPa'],
 ["", "S8", "节点板", "S355 14 mm", f'y {rng(YS["knuckle"])}，焊在横梁端头；6 × M10-10.9 接 S9 的法兰（PCD 55）', "1", ""],
 ["铰点 1", "J1", "铰点 1 轴", "42CrMo4 调质", "轴承段 Ø30（k5），端头法兰 Ø75 × 12；长约 100（y 212 … 310）；尾端 KM6 锁紧螺母", "1", f'应力 {C1["shaft"]["vm_MPa"]} / 允许 {C1["shaft"]["allow_MPa"]} MPa'],
 ["", "J2", "圆锥滚子轴承", "SKF 32006 X/Q 或同级（30 × 55 × 17）", f'背对背，中心距 {C1["spacing_mm"]:.0f}；KM6 螺母预紧', "2", f'静安全系数 {C1["sf"]}'],
 ["", "J3", "轴承座筒", "S355 无缝钢管 Ø75，轴承孔 Ø55 H7", f'y {mm(YS["brgB"][0])} … {mm(YS["plate"][1])}；中段 y 256 … 284 开 60° 窗口让 J4 穿出；焊在 C1 上后两孔一起精加工', "1", "穿过内壁竖槽"],
 ["", "J4", "铰点 2 摆臂", "S355 12 mm", "铰点 1 → 铰点 2 中心距 117，臂宽 30，铰点 2 端外形 R15；毂长 24，用 Ø30 胀紧套（或花键）接 J1", "1", "传扭矩约 180 N·m，不用单键"],
 ["连杆", "L1", "连杆管", "S355 钢管 Ø20 × 2", f'铰点中心距 {mm(D["link"]["length"])}；两端焊螺纹接头（一端左旋，可调长）', "1", f'压杆安全系数 {LK["buckling_sf"]}'],
 ["", "L2", "杆端关节轴承", "SKF SIKAC 10 M 或同级（M10，头部外径 ≤ 30）", "c2 一端装在 J4 上，B 一端装在 L3 上", "2", f'静安全系数 {LK["rod_end_sf"]}'],
 ["", "L3", "B 支座", "S355 8 mm 双耳座 + M10 销", f'中心 {P(D["link"]["ground_pivot_B"])}，焊在机构箱底框', "1", ""],
 ["滑块座", "C1", "滑块板", "S355 20 mm", f'见第 04 项外形，y {rng(YS["plate"])}', "1", f'应力 {PT["plate"]["S355 钢板 20"]["stress_MPa"]} / 允许 237 MPa（粗估）'],
 ["", "C2", "滑块", "HIWIN HGH15CA（Z0 轻预压）或同级", "34 × 61.4，高 28（含导轨）", "4", f'静安全系数 {CR["sf"]}'],
 ["", "C3", "螺母座 + 浮动接头", "S355 + 标准浮动接头", "螺母法兰在 C1 背面、两导轨之间；侧板对应处开 8 深让位槽", "1", "只传轴向"],
 ["驱动", "D1", "导轨", "HIWIN HGR15 或同级", f'长 {mm(D["rail1"]["length"])}，两根，在导轨平面内相距 150', "2", ""],
 ["", "D2", "滚珠丝杠", "Ø16 导程 10（HIWIN R16-10K3-FSCDIN 或同级）", "螺纹长约 400、总长约 500；上端 BK12 固定，下端 BF12 浮动", "1", f'静安全系数 {DR["static_sf"]}'],
 ["", "D3", "同步带", "HTD-5M 宽 15，带轮 15T / 45T", "电机 → 丝杠 1:3", "1", ""],
 ["", "D4", "电机", "24 V 无刷直流，57 机座，带编码器", "额定 ≥ 0.6 N·m、≥ 600 r/min（约 100 W 级）", "1", f'需要 {DR["motor_torque_Nm"]} N·m @ {DR["motor_rpm"]} r/min'],
 ["", "D5", "失电制动器", "弹簧加压电磁制动器，24 V，额定 8 N·m（例：mayr ROBA-stop-M 8 号）", "装在丝杠上端，带手动释放（接应急拉索）", "1", f'需要 ≥ {brake:.1f} N·m'],
 ["", "D6", "离心限速器", "按 180 r/min（座板 3 cm/s）动作", "装在丝杠上", "1", ""],
 ["", "D7", "位置和限位", "丝杠端多圈绝对编码器 + 上下限位开关", "", "1 套", "控制器用它算倾角"],
 ["机构箱", "H1", "侧板（导轨安装板）", "6061-T6 15 mm", f'y {rng(YS["back"])}，外形同机构箱外廓；导轨安装面精铣', "1", ""],
 ["", "H2", "内壁", "钢板 2 mm", f'y {rng(YS["wall_in"])}；沿铰点 1 轨迹开竖槽，宽 87（= 75 + 2 × 6），两侧毛刷', "1", "和 H1、H3 连成盒子"],
 ["", "H3", "周边围板", "钢板 2 mm 折弯，焊或铆", "连接 H1 和 H2", "1", f'盒子扛横滚力矩 {ST["housing_Mx_Nm"]["value"]:.0f} N·m'],
 ["", "H4", "外罩", "1.5 mm 铝板或 ABS（不受力）", f'y {rng(YS["wall_out"])}', "1", ""],
 ["底座等", "B1", "底座框", "S355 矩形管 60 × 30 × 3（平放，高 30）+ 5 mm 调平脚", "x 30 … 780，y −270 … 380，顶面 35", "1", ""],
 ["", "B2", "踏板", "6061-T6 10 mm + 2 mm 防滑胶垫", "x 200 … 620，y ±220，z 35 … 47", "1", f'下沉 {PT["footplate"]["10 mm"]["defl_mm"]} mm'],
 ["", "B3", "踏板称重单元", "100 kg/只，装在底座框内侧托板上（不加高踏板）", "踏板四角", "4", ""],
 ["", "B4", "扶手立柱", "S355 方管 60 × 60 × 4，喷塑", "x 700，y 300，z 35 … 950；根部 10 mm 底板 + 4 块筋，和底座框焊成一体", "1", f'根部弯矩 {HRL["post"]["方管 60×60×4"]["base_moment_Nm"]} N·m'],
 ["", "B5", "横杆", "S355 圆管 Ø38 × 4，喷塑（或 Ø42.4 × 3.2）", "z 950，y −50 … 300；末端圆头软包、夜光；握把开关段", "1", f'应力 {HRL["bar"]["圆管 Ø38×4（S355 喷塑）"]["stress_MPa"]} / 允许 237 MPa'],
 ["", "B6", "和床固定件", "待定（床腿夹或底板伸到床腿下）", "", "2", f'拉力 {PT["tipping"]["固定件拉力（ADA 609 扶手设计载荷 1112 N，安全系数 1.5）"]["anchor_N"]} N'],
 ["", "B7", "控制器 + 电池", "24 V 锂电池（能降完全程）", "机构箱底部", "1", ""]]
link_c = PT["link_forces_N"]; arm_M = max(link_c.values()) * 0.117; arm_s = arm_M / (0.012 * 0.03 ** 2 / 6) / 1e6
chk = [
 ["横梁 S7", "弯 + 扭，Mises", f'{PT["beam"]["vm_MPa"]:.0f} MPa', "237 MPa", ok(PT["beam"]["vm_MPa"] < 237)],
 ["铰点 1 轴 J1（Ø30，42CrMo4）", f'轴承 B 处弯矩 {ST["shaft_M_at_B_Nm"]["value"]:.0f} N·m + 扭矩 {ST["shaft_torsion_Nm"]["value"]:.0f} N·m', f'{C1["shaft"]["vm_MPa"]} MPa', f'{C1["shaft"]["allow_MPa"]} MPa', ok(C1["shaft"]["ok"])],
 ["铰点 1 轴承 J2（32006 X）", f'径向 B {kN("brgB_radial_N")} / A {kN("brgA_radial_N")} kN，轴向 {kN("brg_axial_N")} kN → 当量静载', f'{C1["P0_kN"]} kN', "额定静载 44 kN", ok(C1["sf"] >= 2) + f'（{C1["sf"]}）'],
 ["对照：交叉滚子轴承 RU66（外径 95）", "当量静载 = 径向 + 2 × 力矩 / 66", f'{C1["why_not_crossed_roller"]["RU66"]["P0_kN"]} kN', "额定静载 22.3 kN", ok(False) + "（约 1.06）"],
 ["对照：交叉滚子轴承 RU85（外径 120）", "强度够，但离床", f'{C1["why_not_crossed_roller"]["RU85"]["bed_gap_cm"] * 10:.0f} mm', "≥ 15 mm", ok(False)],
 ["铰点 2 摆臂 J4（12 × 30）", "连杆力 × 117 臂长", f'{arm_s:.0f} MPa', "237 MPa", ok(arm_s < 237)],
 ["连杆 L1（Ø20 × 2）", f'拉 {link_c["tension"] / 1000:.1f} / 压 {link_c["compression"] / 1000:.1f} kN', f'压杆临界 {LK["euler_kN"]} kN', f'安全系数 {LK["buckling_sf"]}', ok(LK["buckling_sf"] > 3)],
 ["杆端 L2（M10）", "连杆力", f'{max(link_c.values()) / 1000:.2f} kN', "额定静载 12.2 kN", ok(LK["rod_end_sf"] > 3) + f'（{LK["rod_end_sf"]}）'],
 ["滑块 C2（HGH15CA）", "垂直侧板 + 导轨平面内，× 1.3 不均", f'{CR["P0_x13_kN"]} kN', "额定静载 16.97 kN", ok(CR["sf"] >= 2) + f'（{CR["sf"]}）'],
 ["滑块板 C1（S355 20）", "最远滑块的力从轴承座筒传过去（窄条悬臂，偏保守）", f'{PT["plate"]["S355 钢板 20"]["stress_MPa"]} MPa', "237 MPa", ok(PT["plate"]["S355 钢板 20"]["stress_MPa"] < 237) + "；15 mm 时 337，不够"],
 ["丝杠 D2", f'轴向 {kN("nut_axial_N")} kN（上端固定，人坐着时丝杠受拉）', f'寿命约 {DR["life_cycles"]} 次起坐', "额定静载 19.3 kN", ok(DR["static_sf"] > 3) + f'（{DR["static_sf"]}）'],
 ["电机 D4", f'起身最大推力 {DR["lift_force_N"]} N，丝杠效率 0.9、带 0.95、1:3', f'{DR["motor_torque_Nm"]} N·m @ {DR["motor_rpm"]} r/min（输出 {DR["motor_power_W"]} W）', "额定 ≥ 0.6 N·m", ok(True)],
 ["应急下降（1:3 带，电机拖着转）", "最轻 45 kg 的人能不能压下去", f'推力 {PT["emergency_belt3"]["light_user_drive_N"]} N / 阻力 {PT["emergency_belt3"]["resist_N"]} N', "余量 > 1.3", ok(PT["emergency_belt3"]["margin"] > 1.3) + f'（{PT["emergency_belt3"]["margin"]}；1:1 时 2.6）'],
 ["机构箱盒体 H1–H3（底部截面）", f'横滚力矩 {ST["housing_Mx_Nm"]["value"]:.0f} N·m', f'翼缘应力 {HB["flange_stress_MPa"]} MPa', "—", ok(True) + "（竖槽以上交给 FEA）"],
 ["扶手立柱 B4（60 × 60 × 4）", f'横杆末端 {HRL["load_N"]} N，向人拉', f'{HRL["post"]["方管 60×60×4"]["vm_MPa"]} MPa，末端位移 {HRL["post"]["方管 60×60×4"]["tip_pull_mm"]} mm', "237 MPa", ok(True) + f'（50 × 50 × 4：位移 {HRL["post"]["方管 50×50×4"]["tip_pull_mm"]} mm）'],
 ["横杆 B5（Ø38 × 4）", f'末端 {HRL["load_N"]} N 向下', f'{HRL["bar"]["圆管 Ø38×4（S355 喷塑）"]["stress_MPa"]} MPa', "237 MPa", ok(True) + f'（304 不锈钢 Ø38 × 2：{HRL["bar"]["圆管 Ø38×2（304 不锈钢）"]["stress_MPa"]} / 137，不够）'],
 ["踏板 B2（10 mm 铝）", "150 kg 站在中间，四角支撑", f'{PT["footplate"]["10 mm"]["defl_mm"]} mm，{PT["footplate"]["10 mm"]["stress_MPa"]} MPa', "160 MPa", ok(True) + f'（8 mm：{PT["footplate"]["8 mm"]["defl_mm"]} mm）']]
dfl = [[n, f"{v:.2f}"] for n, v in PT["deflection"]["rows"]] + [["<b>合计</b>", f'<b>{PT["deflection"]["total_mm"]:.2f}</b>'], ["目标", f'≤ {PT["deflection"]["limit_mm"]:.0f}']]
tp = PT["tipping"]; mrows = [[n, f"{m:.1f}", f"({mm(c[0])}, {mm(c[1])}, {mm(c[2])})"] for n, m, c in MS["device"]] + [["<b>整机</b>", f'<b>{MS["device_kg"]:.1f}</b>', f'<b>({mm(MS["device_com"][0])}, {mm(MS["device_com"][1])}, {mm(MS["device_com"][2])})</b>']]
tiprows = [[k, f'{v["margin_rear_cm"]} / {v["margin_front_cm"]} / {v["margin_side_cm"]}'] for k, v in tp.items() if isinstance(v, dict) and "margin_rear_cm" in v]
cush = [[k, f'{v["k_kPa_per_cm"]} kPa/cm', f'{v["thick_mm"]}', f'约 {v["cv40_kPa"]:.0f} kPa'] for k, v in PT["cushion"].items()]
cat = [["32006 X/Q（SKF）", "30 × 55 × 17，C 35.8 kN，C0 44 kN", "经销商表（ameco、RS）", "SKF 样本"],
       ["HGH15CA / HGR15（HIWIN）", "C 11.38 kN，C0 16.97 kN；34 × 61.4，H 28", "C 与 HIWIN 官网系列下限一致；C0 取旧版 HIWIN 表，本次没能打开原厂样本", "HIWIN HG 样本"],
       ["R16-10K3-FSCDIN（HIWIN）", "Ca 9.1 kN，C0a 19.3 kN", "Damen CNC 列出的 2024 HIWIN 样本值", "HIWIN 丝杠样本"],
       ["SIKAC 10 M（SKF）", "C 10 kN，C0 12.2 kN，头部外径 29", "RS、Acorn、Motion 经销商表", "SKF 样本"],
       ["ROBA-stop-M 8 号（mayr）", "额定 8 N·m", "mayr 选型器", "24 V 线圈和外径向厂家确认"],
       ["THK RU66 / RU85（对照）", "RU66：外径 95，节圆 66，C0 22.3 kN；RU85：外径 120，C0 29.5 kN", "经销商表（GMT、goldsupplier）", "只用来说明为什么不用"]]
chg = ["铰点 1：从“交叉滚子轴承，或相距约 14 cm 的双轴承”改为一对圆锥滚子轴承（相距 61），装在穿过竖槽的 Ø75 轴承座筒里。原因：铰点 1 在齐平位离床侧面只有 69 mm，强度够的交叉滚子轴承外径 120，会伸到离床 9 mm；外径 95 的强度不够。",
       f'载荷：加上侧向 ± 0.3 倍（人在座板上横向蹭）；活动件质量按零件算（座板侧 {MS["seat_kg"]} kg、滑块座 {MS["plate_kg"]} kg，原来按 10 kg）。铰点 1 力矩 {ST["c1_moment_Nm"]["value"]:.0f} N·m（原 611），螺母 {kN("nut_axial_N")} kN（原 2.0）。',
       f'机构箱外廓：按零件实际外形（导轨宽、滑块板、轴承座筒、杆端、制动器、电机）+ 5 间隙 + 3 壁重算。面积 {PT["housing"]["old_area_cm2"]} → {PT["housing"]["area_cm2"]} cm²，顶仍约 0.80 m；离床 21 → {CL["housing_bed_cm"] * 10:.0f} mm（原来没算杆端的尺寸）。',
       f'整机质量估算约 {MS["device_kg"]:.0f} kg（稳定性检查原来假设 45 kg），重心 ({mm(MS["device_com"][0])}, {mm(MS["device_com"][1])})；翻倒余量都变大，人不在台上时横推 {tp["结论"]["min_tip_force_N"]} N 才翻，仍要和床固定。',
       "电机：同步带从约 1:1 改为 1:3，电机只需 0.46 N·m；代价是应急下降时电机被拖着转得更快，余量 2.6 → 1.6。",
       "座板：一整块底板 + 后区垫条；悬臂托架改为横梁 50 × 30 × 4 + 两条称重支臂；铰点 2 摆臂移到座板侧缘外（y 258 … 270），不再在座板下面。"]
todo = ["机构箱离床 12 mm（静止件，不夹人）：小于 15 mm 的规则。团队定：接受，或铰点 2 改用 M8 杆端（头部外径 ≤ 24，离床到约 15 mm）。",
        "称重单元型号：薄（≤ 8 mm）、能被向上拔、量程 ≥ 110 kg 的现货不多；找不到就把横梁降 5 mm 重查离腿间隙。",
        "两区泡棉：剪 10 × 10 cm 样块，压 2 cm（后区）和 3.2 cm（前区）称力，对上第 14 项的目标再定牌号。",
        "标准件额定值按厂家样本核一遍（第 15 项）。",
        "螺母法兰在两导轨之间，侧板要开让位槽；制动器外径确认后核机构箱顶部。"]
# ---------------------------------------------------------------- v5.7: mechanism diagrams (side-view kinematic sketch + section along the c1 axis)
def kin_svg():
    """side view, to scale: bodies 1 frame, 2 carriage, 3 seat, 4 link; joints P, R1, S2, S3."""
    k = 0.78; XA, XB, ZA, ZB = -140, 760, -20, 900
    X = lambda x: (1000 * x - XA) * k; Z = lambda z: (ZB - 1000 * z) * k; Wd2, Hd2 = (XB - XA) * k, (ZB - ZA) * k
    o = [f'<svg viewBox="0 0 {Wd2:.0f} {Hd2:.0f}" role="img" aria-label="机构运动简图：机架、滑块座、座板、连杆四个构件，一个移动副、一个转动副、两个球铰，自由度 1">',
         '<defs><pattern id="hat" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" class="hatl"/></pattern>'
         '<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrh"/></marker></defs>']
    P_ = lambda pts: " ".join(f"{X(x):.1f},{Z(z):.1f}" for x, z in pts)
    o.append(f'<polygon class="bed" points="{P_([(-0.14, 0), (0, 0), (0, 0.42), (-0.14, 0.42)])}"/>')
    o.append(f'<text class="lab muted" x="{X(-0.13):.1f}" y="{Z(0.22):.1f}">床</text>')
    o.append(f'<rect x="{X(-0.14):.1f}" y="{Z(0):.1f}" width="{X(0.76) - X(-0.14):.1f}" height="10" fill="url(#hat)"/><line class="floor" x1="{X(-0.14):.1f}" y1="{Z(0):.1f}" x2="{X(0.76):.1f}" y2="{Z(0):.1f}"/>')
    r1 = D["rail1"]; lo, hi = np.array(r1["lo"]), np.array(r1["hi"]); ee = (hi - lo) / np.linalg.norm(hi - lo); nn = np.array([ee[1], -ee[0]])
    # rail = part of the frame: line + hatch strip on the frame side (forward-down, toward rail 2)
    strip = [lo, hi, hi + 0.012 * nn, lo + 0.012 * nn]
    o.append(f'<polygon points="{P_(strip)}" fill="url(#hat)"/><line class="kin1" x1="{X(lo[0]):.1f}" y1="{Z(lo[1]):.1f}" x2="{X(hi[0]):.1f}" y2="{Z(hi[1]):.1f}"/>')
    # screw + motor/brake at the top
    s0, s1 = np.array(D["screw"]["axis_lo"]), np.array(D["screw"]["axis_hi"])
    o.append(f'<line class="kscrew" x1="{X(s0[0]):.1f}" y1="{Z(s0[1]):.1f}" x2="{X(s1[0]):.1f}" y2="{Z(s1[1]):.1f}"/>')
    mc = s1 + 0.035 * ee
    o.append(f'<circle class="kmot" cx="{X(mc[0]):.1f}" cy="{Z(mc[1]):.1f}" r="13"/><text class="klab c" x="{X(mc[0]):.1f}" y="{Z(mc[1]) + 4:.1f}" text-anchor="middle">M</text>')
    o.append(f'<text class="lab" x="{X(mc[0]) + 18:.1f}" y="{Z(mc[1]) - 6:.1f}">电机 + 失电制动 + 限速</text>')
    # Q path
    qs = [(float(r[1]) / 1000, float(r[2]) / 1000) for r in TT[1:]]
    o.append(f'<polyline class="qpath" points="{P_(qs)}"/>')
    def pose(F, ghost):
        g = " ghost" if ghost else ""
        Q, phi, P1, P2 = F["Q"], F["phi"], np.array(F["P1"]), np.array(F["P2"])
        a = W(Q, phi, (-h, 0)); b = W(Q, phi, (h, 0))
        tri = [a, b, tuple(P1), tuple(P2)]
        o.append(f'<polygon class="kseat{g}" points="{P_([a, b, tuple(P1)])}"/><polygon class="kseat{g}" points="{P_([tuple(P1), tuple(P2), a])}"/>')
        o.append(f'<line class="kplate{g}" x1="{X(a[0]):.1f}" y1="{Z(a[1]):.1f}" x2="{X(b[0]):.1f}" y2="{Z(b[1]):.1f}"/>')
        c = P1 + 0.075 * ee; bx = [c - 0.11 * ee - 0.016 * nn, c + 0.11 * ee - 0.016 * nn, c + 0.11 * ee + 0.004 * nn, c - 0.11 * ee + 0.004 * nn]
        o.append(f'<polygon class="kslider{g}" points="{P_(bx)}"/>')
        o.append(f'<line class="klink{g}" x1="{X(Bp_[0]):.1f}" y1="{Z(Bp_[1]):.1f}" x2="{X(P2[0]):.1f}" y2="{Z(P2[1]):.1f}"/>')
        for p in (P1, P2): o.append(f'<circle class="kjoint{g}" cx="{X(p[0]):.1f}" cy="{Z(p[1]):.1f}" r="6"/>')
        return P1, P2, c, a, b
    Bp_ = np.array(D["link"]["ground_pivot_B"])
    pose(F1, True); P1, P2, c, a, b = pose(F0, False)
    o.append(f'<polygon points="{P_([tuple(Bp_), tuple(Bp_ + np.array([-0.022, -0.03])), tuple(Bp_ + np.array([0.022, -0.03]))])}" class="kground"/>')
    o.append(f'<rect x="{X(Bp_[0] - 0.03):.1f}" y="{Z(Bp_[1] - 0.03):.1f}" width="{0.06 * 1000 * k:.1f}" height="8" fill="url(#hat)"/>')
    o.append(f'<circle class="kjoint" cx="{X(Bp_[0]):.1f}" cy="{Z(Bp_[1]):.1f}" r="6"/>')
    # load arrow (body weight) at the seat
    Qn = F0["Q"]; o.append(f'<line class="kload" x1="{X(Qn[0] + 0.02):.1f}" y1="{Z(Qn[1] + 0.13):.1f}" x2="{X(Qn[0] + 0.02):.1f}" y2="{Z(Qn[1] + 0.01):.1f}" marker-end="url(#arr)"/>')
    L = [((Qn[0] + 0.03, Qn[1] + 0.12), "体重", 4, 0, "start"),
         (tuple(P1), "R1 铰点 1（转动副，承受力矩）", -12, 0, "end"), (tuple(P2), "S2 铰点 2（球铰）", -12, 6, "end"), (tuple(Bp_), "S3 B（球铰，接机架）", 12, 4, "start"),
         (tuple(c + 0.12 * ee), "② 滑块座（滑块板 + 轴承座筒）", 12, 0, "start"), (tuple(hi), "P 移动副（两根导轨）", 10, -4, "start"),
         ((b[0], b[1]), "③ 座板", 8, -10, "start"), (tuple(0.5 * (Bp_ + P2)), "④ 连杆", 10, 0, "start"),
         ((F1["Q"][0], F1["Q"][1]), "顶位（半透明）", 10, -16, "start"), ((qs[len(qs) // 2][0], qs[len(qs) // 2][1]), "座面中心 Q 的轨迹", 10, 4, "start"),
         ((0.52, 0.06), "① 机架：机构箱 + 底座 + 导轨，和床固定", 0, -6, "start"), (tuple(s0 + 0.12 * (s1 - s0)), "丝杠（驱动 ②）", 10, 8, "start")]
    for p, t, dx, dy, an in L: o.append(f'<text class="lab" x="{X(p[0]) + dx:.1f}" y="{Z(p[1]) + dy:.1f}" text-anchor="{an}">{html.escape(t)}</text>')
    o.append("</svg>"); return "".join(o)

def sec_svg():
    """section along the c1 axis: y to scale (mm), the other direction schematic. Shows the layers and the load path."""
    k = 1.55; YA, YB = -250, 380; VA, VB = -190, 140
    Xy = lambda y: (y - YA) * k + 10; Vv = lambda v: (VB - v) * k + 10; Wd3, Hd3 = (YB - YA) * k + 20, (VB - VA) * k + 20
    o = [f'<svg viewBox="0 0 {Wd3:.0f} {Hd3:.0f}" role="img" aria-label="沿铰点 1 轴线的剖面示意：座板、横梁、节点板、铰点 1 轴、两个圆锥滚子轴承、内壁竖槽、铰点 2 摆臂、滑块板、滑块、导轨、侧板">',
         '<defs><pattern id="hat2" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" class="hatl"/></pattern>'
         '<marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrh"/></marker></defs>']
    rect = lambda y0, y1, v0, v1, cls, extra="": o.append(f'<rect class="{cls}" x="{Xy(y0):.1f}" y="{Vv(v1):.1f}" width="{(y1 - y0) * k:.1f}" height="{(v1 - v0) * k:.1f}" {extra}/>')
    c1v = 69.7                                                   # seat top is 69.7 above the c1 axis (seat frame)
    rect(-220, 220, c1v - 50, c1v, "sfoamr"); rect(-220, 220, c1v - 80, c1v - 50, "sfoamf")
    rect(-220, 220, c1v - 92, c1v - 80, "sboard")
    rect(-205, 212, c1v - 130, c1v - 100, "ssteel")             # cross-beam
    rect(-190, -180, c1v - 110, c1v - 100, "ssteel"); rect(180, 190, c1v - 110, c1v - 100, "ssteel")   # arms (end view)
    for yy in (-190, 190): rect(yy - 12, yy + 12, c1v - 100, c1v - 92, "scell")
    rect(212, 226, -60, 40, "ssteel")                           # knuckle
    rect(212, 224, -37.5, 37.5, "sshaft")                      # shaft flange
    rect(224, 312, -15, 15, "sshaft")                          # shaft
    rect(229, 308, 27.5, 37.5, "scart"); rect(229, 256, -37.5, -27.5, "scart"); rect(284, 308, -37.5, -27.5, "scart")   # cartridge (window at the bottom)
    for y0, y1 in ((229, 246), (290, 307)):                     # tapered roller bearings, both halves
        for s_ in (1, -1):
            v0, v1 = (15, 27.5) if s_ > 0 else (-27.5, -15)
            rect(y0, y1, v0, v1, "sbrg")
            o.append(f'<line class="sbrgx" x1="{Xy(y0):.1f}" y1="{Vv(v1 if s_ > 0 else v0):.1f}" x2="{Xy(y1):.1f}" y2="{Vv(v0 if s_ > 0 else v1):.1f}"/>')
    rect(312, 318, -12, 12, "snut")                             # lock nut
    rect(250, 253, 43.5, 135, "swall"); rect(250, 253, -185, -43.5, "swall")       # inner wall with slot
    for vv in (43.5, -43.5): o.append(f'<line class="brush" x1="{Xy(247):.1f}" y1="{Vv(vv):.1f}" x2="{Xy(256):.1f}" y2="{Vv(vv):.1f}"/>')
    rect(258, 270, -125, -10, "ssteel")                         # c2 arm (through the window)
    o.append(f'<circle class="srod" cx="{Xy(275):.1f}" cy="{Vv(-117):.1f}" r="{14.5 * k:.1f}"/><circle class="kjoint" cx="{Xy(275):.1f}" cy="{Vv(-117):.1f}" r="4"/>')
    o.append(f'<line class="klink" x1="{Xy(275):.1f}" y1="{Vv(-117):.1f}" x2="{Xy(275):.1f}" y2="{Vv(-185):.1f}"/>')
    rect(288, 308, -42, 135, "splate")                          # carriage plate
    for vv in (0.0, 110.0): rect(308, 336, vv - 30.7, vv + 30.7, "scarr")
    rect(321, 336, -185, 135, "srail")
    rect(336, 351, -185, 135, "sback"); rect(356, 358, -185, 135, "swall")
    o.append(f'<line class="axis" x1="{Xy(200):.1f}" y1="{Vv(0):.1f}" x2="{Xy(330):.1f}" y2="{Vv(0):.1f}"/>')
    # load and path
    o.append(f'<line class="kload" x1="{Xy(-100):.1f}" y1="{Vv(c1v + 60):.1f}" x2="{Xy(-100):.1f}" y2="{Vv(c1v + 2):.1f}" marker-end="url(#arr2)"/>')
    tag = lambda y, v, n: o.append(f'<circle class="tagc" cx="{Xy(y):.1f}" cy="{Vv(v):.1f}" r="9"/><text class="tagt" x="{Xy(y):.1f}" y="{Vv(v) + 4:.1f}" text-anchor="middle">{n}</text>')
    for y, v, n in ((-100, c1v + 70, "F"), (0, c1v - 115, "1"), (219, 55, "2"), (237.5, 48, "3"), (298.5, 48, "4"), (322, 50, "5"), (343.5, 150 - 10, "6"), (264, -140, "7")): tag(y, v, n)
    labs = [(-218, c1v + 8, "坐垫（后区硬、前区软）", "start"), (-218, c1v - 88, "底板 12", "start"), (-120, c1v - 140, "横梁 50×30×4", "start"), (-190, c1v - 92 + 18, "称重单元", "middle"),
            (226, -70, "节点板", "start"), (229, -50, "轴承 B", "end"), (290, 62, "轴承 A", "middle"), (251.5, 140, "内壁 + 竖槽（毛刷）", "middle"),
            (240, -160, "铰点 2 摆臂 → 杆端 → 连杆（往下到 B）", "end"), (298, 145, "滑块板 20", "middle"), (360, 120, "滑块 / 导轨 / 侧板", "end"),
            (200, 6, "铰点 1 轴线", "end"), (-100, c1v + 85, "偏 10 cm 的体重", "middle")]
    for y, v, t, an in labs: o.append(f'<text class="lab" x="{Xy(y):.1f}" y="{Vv(v):.1f}" text-anchor="{an}">{html.escape(t)}</text>')
    for yy, t in ((-220, "−220"), (0, "0"), (220, "220"), (250, "250"), (288, "288"), (336, "336"), (358, "358")):
        o.append(f'<line class="grid" x1="{Xy(yy):.1f}" y1="{Hd3 - 22:.1f}" x2="{Xy(yy):.1f}" y2="{Hd3 - 14:.1f}"/><text class="tick" x="{Xy(yy):.1f}" y="{Hd3 - 3:.1f}" text-anchor="middle">{t}</text>')
    o.append("</svg>"); return "".join(o)
KIN = kin_svg(); SEC = sec_svg()
path = ["F 偏 10 cm 的体重压在坐垫上，经称重单元到横梁。", "1 横梁把力和力矩（约 510 N·m）带到座板侧缘。", "2 节点板 + 轴端法兰把它交给铰点 1 轴。",
        f'3、4 两个圆锥滚子轴承相距 {C1["spacing_mm"]:.0f}，把力矩变成一对相反的径向力（最大 {kN("brgA_radial_N")} kN）。座板绕这根轴转，这是转动副 R1。',
        "5 轴承座筒焊在滑块板上，滑块板把力分给 4 个滑块（两轨 × 两个，相距 150 × 150）。", "6 导轨装在侧板上，侧板和内壁、周边围板连成盒子，传到底座和床。",
        "7 铰点 2 摆臂从轴承座筒的窗口伸出，经连杆把座板的倾角“拉住”：它只管绕 y 的转动，所以连杆只受拉压。"]

csvtxt = "\n".join(",".join(r) for r in TT)
kp = table(KP[0][:1] + ["丝杠行程", "Q x", "Q z", "前倾 °", "铰点 1 x", "铰点 1 z", "铰点 2 x", "铰点 2 z", "连杆角 °"], KP[1:], "num")
tt = table(["丝杠行程", "Q x", "Q z", "前倾 °", "铰点 1 x", "铰点 1 z", "铰点 2 x", "铰点 2 z", "连杆角 °"], TT[1:], "num")

page = f'''<title>起身台 CAD 尺寸表</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: a drawing sheet — title block, one to-scale side view, then coordinate tables grouped by part */
:root {{
  --paper:#F5F6F3; --sheet:#FFFFFF; --ink:#1A2430; --ink2:#46515E; --muted:#6E7782; --rule:#D5D9DD;
  --blue:#1E5AA8; --blue2:#9DB8DE; --red:#B3261E; --foam:#E9B872; --foam2:#F4D9AE; --steel:#5B6B7C; --steel2:#B8C1CB; --bed:#DCE1E7; --green:#2E7D4F;
  --display:"Noto Serif SC", "Songti SC", serif; --body:"Noto Sans SC", "PingFang SC", system-ui, sans-serif; --mono:"IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper:#12171D; --sheet:#1A2129; --ink:#E6EAEE; --ink2:#B9C2CC; --muted:#8B95A0; --rule:#2E3741;
  --blue:#7FAEEA; --blue2:#3D5F8C; --red:#F08A80; --foam:#B98A45; --foam2:#7A6440; --steel:#9AA9B8; --steel2:#56636F; --bed:#2A323B; --green:#7CC79A; color-scheme:dark }} }}
:root[data-theme="dark"] {{
  --paper:#12171D; --sheet:#1A2129; --ink:#E6EAEE; --ink2:#B9C2CC; --muted:#8B95A0; --rule:#2E3741;
  --blue:#7FAEEA; --blue2:#3D5F8C; --red:#F08A80; --foam:#B98A45; --foam2:#7A6440; --steel:#9AA9B8; --steel2:#56636F; --bed:#2A323B; --green:#7CC79A; color-scheme:dark }}
body {{ background:var(--paper); color:var(--ink); font-family:var(--body); font-size:15px; line-height:1.6 }}
.wrap {{ max-width:1180px; margin:0 auto; padding-block:28px 56px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); display:flex; flex-direction:column; gap:22px }}
.titleblock {{ background:var(--sheet); border:1.5px solid var(--ink); display:grid; grid-template-columns:1fr auto; }}
.titleblock .name {{ padding:18px 22px; border-right:1.5px solid var(--ink); min-width:0 }}
.titleblock h1 {{ font-family:var(--display); font-size:30px; margin:0; text-wrap:balance }}
.titleblock .sub {{ color:var(--ink2); margin:6px 0 0 }}
.meta {{ display:grid; grid-template-columns:auto auto; font-size:13px }}
.meta div {{ padding:6px 14px; border-bottom:1px solid var(--rule) }}
.meta div:nth-child(odd) {{ color:var(--muted); letter-spacing:.06em }}
.meta div:nth-child(even) {{ font-family:var(--mono) }}
@media (max-width:700px) {{ .titleblock {{ grid-template-columns:1fr }} .titleblock .name {{ border-right:none; border-bottom:1.5px solid var(--ink) }} }}
section {{ background:var(--sheet); border:1px solid var(--rule); padding:18px 20px; display:flex; flex-direction:column; gap:12px; min-width:0 }}
h2 {{ font-family:var(--display); font-size:20px; margin:0; display:flex; gap:10px; align-items:baseline }}
h2 .no {{ font-family:var(--mono); font-size:13px; color:var(--blue); letter-spacing:.08em }}
p {{ margin:0; max-width:72ch }}
.key {{ border-left:3px solid var(--red); padding:10px 14px; background:color-mix(in srgb, var(--red) 7%, var(--sheet)) }}
.key ol {{ margin:4px 0 0; padding-left:1.3em; display:grid; gap:4px }}
.tw {{ overflow-x:auto }}
table {{ border-collapse:collapse; width:100%; font-size:14px }}
th {{ text-align:left; font-weight:500; color:var(--muted); font-size:12.5px; letter-spacing:.04em; border-bottom:1.5px solid var(--ink); padding:6px 10px; white-space:nowrap }}
td {{ border-bottom:1px solid var(--rule); padding:7px 10px; vertical-align:top }}
td:nth-child(2) {{ font-family:var(--mono); font-size:13px }}
table.num td {{ font-family:var(--mono); font-size:13px; font-variant-numeric:tabular-nums; white-space:nowrap }}
table.num td:first-child {{ font-family:var(--body) }}
.fig {{ overflow-x:auto; border:1px solid var(--rule); background:var(--sheet) }}
svg {{ display:block; width:100%; min-width:640px; height:auto }}
svg .grid {{ stroke:var(--rule); stroke-width:.6 }} svg .tick {{ fill:var(--muted); font:10px var(--mono) }}
svg .floor {{ stroke:var(--ink); stroke-width:1.4 }} svg .bed {{ fill:var(--bed) }} svg .mat {{ fill:var(--steel2); opacity:.45 }}
svg .base, svg .plate {{ fill:var(--steel) }} svg .housing {{ fill:var(--blue2); fill-opacity:.18; stroke:var(--blue); stroke-width:1.2; stroke-dasharray:5 3 }}
svg .motor {{ fill:var(--ink2) }} svg .rail {{ stroke:var(--ink); stroke-width:4 }} svg .screw {{ stroke:var(--red); stroke-width:1.6; stroke-dasharray:8 3 2 3 }}
svg .link {{ stroke:var(--steel); stroke-width:6; stroke-linecap:round }} svg .ghostl {{ opacity:.35 }}
svg .foamr {{ fill:var(--foam) }} svg .foamf {{ fill:var(--foam2) }} svg .board {{ fill:var(--steel) }} svg .ghost {{ opacity:.35 }}
svg .pin {{ fill:var(--sheet); stroke:var(--red); stroke-width:2 }} svg .ghostp {{ opacity:.45 }} svg .pivot {{ fill:var(--red) }}
svg .post {{ stroke:var(--steel); stroke-width:6 }} svg .bar {{ fill:var(--ink) }}
svg .beam {{ fill:var(--ink2) }} svg .cart {{ fill:none; stroke:var(--red); stroke-width:1.4; stroke-dasharray:3 2 }}
.ok {{ color:var(--green); font-weight:500 }} .bad {{ color:var(--red); font-weight:500 }}
table.bom td:nth-child(2) {{ font-family:var(--mono); font-size:13px; color:var(--blue) }} table.bom td:first-child {{ color:var(--muted); font-size:13px; white-space:nowrap }}
table.bom td:nth-child(4), table.bom td:nth-child(5) {{ font-family:var(--body); font-size:13.5px }}
svg .hatl {{ stroke:var(--muted); stroke-width:1 }} svg .arrh {{ fill:var(--red) }}
svg .kin1 {{ stroke:var(--ink); stroke-width:3 }} svg .kscrew {{ stroke:var(--red); stroke-width:1.6; stroke-dasharray:8 3 2 3 }}
svg .kmot {{ fill:var(--sheet); stroke:var(--ink); stroke-width:1.6 }} svg .klab {{ fill:var(--ink); font:600 13px var(--body) }}
svg .qpath {{ fill:none; stroke:var(--blue); stroke-width:1.4; stroke-dasharray:4 3 }}
svg .kseat {{ fill:var(--foam2); fill-opacity:.55; stroke:var(--ink); stroke-width:1.6; stroke-linejoin:round }} svg .kplate {{ stroke:var(--ink); stroke-width:5; stroke-linecap:round }}
svg .kslider {{ fill:var(--blue2); stroke:var(--blue); stroke-width:1.6 }} svg .klink {{ stroke:var(--steel); stroke-width:4; stroke-linecap:round }}
svg .kjoint {{ fill:var(--sheet); stroke:var(--red); stroke-width:2 }} svg .kground {{ fill:none; stroke:var(--ink); stroke-width:1.4 }}
svg .ghost.kseat, svg .ghost.kplate, svg .ghost.kslider, svg .ghost.klink, svg .ghost.kjoint {{ opacity:.3 }}
svg .kload {{ stroke:var(--red); stroke-width:2.4 }}
svg .sfoamr {{ fill:var(--foam) }} svg .sfoamf {{ fill:var(--foam2) }} svg .sboard {{ fill:#C9A36B }} svg .ssteel {{ fill:var(--steel) }} svg .scell {{ fill:var(--blue) }}
svg .sshaft {{ fill:var(--ink2) }} svg .scart {{ fill:var(--red); fill-opacity:.55 }} svg .sbrg {{ fill:var(--sheet); stroke:var(--ink); stroke-width:1 }} svg .sbrgx {{ stroke:var(--ink); stroke-width:1 }}
svg .snut {{ fill:var(--ink) }} svg .swall {{ fill:var(--muted) }} svg .brush {{ stroke:var(--ink); stroke-width:2; stroke-dasharray:1 2 }}
svg .srod {{ fill:var(--sheet); stroke:var(--steel); stroke-width:2 }} svg .splate {{ fill:var(--blue2) }} svg .scarr {{ fill:var(--blue); fill-opacity:.7 }}
svg .srail {{ fill:var(--ink); fill-opacity:.7 }} svg .sback {{ fill:var(--steel2) }} svg .axis {{ stroke:var(--red); stroke-width:1; stroke-dasharray:10 3 2 3 }}
svg .tagc {{ fill:var(--red) }} svg .tagt {{ fill:#fff; font:600 11px var(--mono) }}
.fig.kin svg {{ max-width:760px; margin:0 auto }}
ol {{ margin:0; padding-left:1.3em; display:grid; gap:4px; max-width:80ch }}
svg .lab {{ fill:var(--ink); font:12px var(--body) }} svg .muted {{ fill:var(--muted) }}
.cap {{ color:var(--muted); font-size:13px }}
.planes {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:6px 18px; font-size:14px }}
.planes div {{ display:flex; justify-content:space-between; gap:12px; border-bottom:1px dotted var(--rule); padding:3px 0 }}
.planes span:last-child {{ font-family:var(--mono); white-space:nowrap }}
details summary {{ cursor:pointer; color:var(--blue); font-weight:500 }}
button {{ font:inherit; font-size:13px; color:var(--blue); background:transparent; border:1px solid var(--blue); padding:4px 12px; cursor:pointer }}
button:focus-visible, summary:focus-visible {{ outline:2px solid var(--blue); outline-offset:2px }}
textarea {{ width:100%; height:120px; font:12px var(--mono); color:var(--ink); background:var(--paper); border:1px solid var(--rule) }}
.row {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap }}
</style>
<div class="wrap">
<header class="titleblock">
  <div class="name"><h1>起身台 CAD 尺寸表</h1><p class="sub">单自由度坐板（斜导轨 + 倾角连杆）：给角色 3 建 SolidWorks 装配体用。坐标由模型算出；v5.7 起零件截面、材料和标准件也定了（第 10–15 项），都按手算校核过，板件和机构箱再交给 FEA 复核。</p></div>
  <div class="meta"><div>版本</div><div>v5.7 · 2026-10-27</div><div>单位</div><div>mm，角度 °</div><div>来源</div><div>calc_v13 · cad_sheet.py、parts.py</div><div>交给</div><div>角色 3（CAD）</div></div>
</header>

<section>
  <h2><span class="no">00</span>先读这三条</h2>
  <div class="key"><ol>
    <li><b>坐标系：</b>原点在地面、床的长边正下方，y = 0 是座板中面。x 向床外（床在 x &lt; 0），y 沿床长、指向床头一侧（机构箱在 +y），z 向上。座板坐标系：原点 Q 是座面（坐垫上表面）中点，x<sub>s</sub> 沿座面向前，z<sub>s</sub> 垂直座面；座板前倾 φ 时，世界坐标 = Q + R(φ)·(x<sub>s</sub>, z<sub>s</sub>)。</li>
    <li><b>不能改的：</b>两根导轨的位置和角度、铰点 1 和 2 在座板上的位置、连杆地面铰点 B 和连杆长度。它们一起决定座板的轨迹；改了任何一个，81 人的检查要重算。</li>
    <li><b>铰点 1 是关键件：</b>要承受约 {ST["c1_moment_Nm"]["value"]:.0f} N·m 的力矩（座板单侧悬臂的偏载都经过它）。v5.7 定为一对圆锥滚子轴承装在穿过竖槽的轴承座筒里（第 05、10 项）；交叉滚子轴承离床太近或强度不够（第 11 项）。机构简图见第 17 项。</li></ol></div>
</section>

<section>
  <h2><span class="no">01</span>侧视图（x–z，按比例，网格 100 mm）</h2>
  <div class="fig">{"".join(svg)}</div>
  <p class="cap">实色是座板在齐平位（丝杠行程 0），半透明是顶位（行程 {mm(sc["stroke"])}）。两根导轨都装在 y = {mm(r1["y"])} 的同一块侧板上，侧视里平行；红色点划线是丝杠轴线；红点是连杆地面铰点 B，白心红圈是铰点 1、2。</p>
</section>

<section>
  <h2><span class="no">02</span>横向位置（y）</h2>
  <div class="planes">{"".join(f"<div><span>{k}</span><span>{v}</span></div>" for k, v in Y.items())}</div>
</section>

<section>
  <h2><span class="no">03</span>固定件（世界坐标 x, z）</h2>
  {table(["零件", "坐标", "说明"], fixed)}
</section>

<section>
  <h2><span class="no">04</span>运动件（座板坐标，相对 Q）</h2>
  {table(["零件", "尺寸 / 坐标", "说明"], seatrows)}
</section>

<section>
  <h2><span class="no">05</span>关节和受力（100 kg × 1.5 + 活动件实际质量，偏向敞开一侧 10 cm，含竖直、沿座面 ± 0.3 和侧向 ± 0.3 的力，全行程最不利）</h2>
  {table(["关节", "要传的力", "做法"], jrows)}
</section>

<section>
  <h2><span class="no">06</span>关键位置</h2>
  {kp}
  <details><summary>全行程表（丝杠每 10 mm 一行，{len(TT) - 1} 行）</summary>{tt}</details>
  <div class="row"><button type="button" id="copy-csv">复制全行程 CSV</button><span class="cap" id="copy-msg"></span></div>
  <textarea id="csv" readonly hidden>{html.escape(csvtxt)}</textarea>
  <p class="cap">建运动算例时：给丝杠螺母一个线性位移 0 → {mm(sc["stroke"])}，座板的位置和前倾应和这张表一致（误差 &lt; 1 mm、0.1°）；这是检查装配约束有没有建对的最快办法。</p>
</section>

<section>
  <h2><span class="no">07</span>要保持的间隙</h2>
  {table(["位置", "最小间隙 mm", "说明"], clr)}
</section>

<section>
  <h2><span class="no">08</span>交给 FEA（角色 4）</h2>
  {table(["工况", "说明"], [[c, ""] for c in D["fea"]["cases"]] + [["侧向 ± 0.3 倍设计载荷", "v5.7 新增"],
     ["滑块板 + 轴承座筒焊件", "手算用窄条悬臂，偏保守：20 mm 时 190 MPa、外缘 1.3 mm"], ["机构箱盒体", "竖槽以上内壁被切开，手算只算了底部截面"],
     ["变形目标", f'100 kg × 1.5 时座板外缘下沉 ≤ {D["fea"]["deflection_target_mm"]} mm；手算合计 {PT["deflection"]["total_mm"]:.1f} mm（第 12 项）']])}
</section>

<section>
  <h2><span class="no">09</span>需要 CAD 决定的</h2>
  <div class="key"><ol>
    <li><s>铰点 1 的做法</s>：v5.7 已定（圆锥滚子轴承对 + 轴承座筒）。</li>
    <li><s>各件截面</s>：v5.7 已定（第 10 项），CAD 按这个建，FEA 复核。</li>
    <li>应急拨杆的位置：横杆与立柱拐角下方、带翻盖，坐着够不够得到。</li>
    <li>和床的固定件：床腿夹，还是底板伸到床腿下面。</li>
    <li>CAD 出来以后，把真实质量和质心给角色 4 复核稳定性（手算估约 {MS["device_kg"]:.0f} kg，第 13 项）。</li>
    <li>其余待定见第 16 项。</li></ol></div>
</section>

<section>
  <h2><span class="no">10</span>零件和材料（v5.7）</h2>
  <p class="cap">编号给 CAD 建零件用。尺寸 mm；x<sub>s</sub>、z<sub>s</sub> 是座板坐标（相对 Q），y 是世界坐标。“依据”列是校核结果，细节在第 11 项。</p>
  {table(["组", "编号", "零件", "材料 / 型号", "尺寸和位置", "数量", "依据"], bom, "bom")}
</section>

<section>
  <h2><span class="no">11</span>强度和选型校核（设计载荷：100 kg × 1.5，偏 10 cm，含沿座面和侧向 ± 0.3）</h2>
  <p class="cap">规则：Mises 应力 ≤ 屈服 / 1.5（载荷里已经乘了 1.5，合计对屈服 2.25 倍）；轴承和滑块静安全系数 ≥ 2。都是手算（梁公式），板件和机构箱以 FEA 为准。</p>
  {table(["零件", "工况", "计算值", "允许 / 额定", "结果"], chk)}
</section>

<section>
  <h2><span class="no">12</span>变形预算：座板外缘下沉（设计载荷）</h2>
  <p class="cap">外缘指 y = −220、座板前沿。轴承和滑块刚度是假设值（预紧的 32006 X 每个 400 N/µm，HGH15CA 200 N/µm），要按样本刚度核。</p>
  {table(["来源", "mm"], dfl, "num")}
</section>

<section>
  <h2><span class="no">13</span>质量和重心（估算）</h2>
  <p class="cap">按第 10 项的材料和尺寸估，CAD 出来后用真实值替换。稳定性检查原来假设台架 45 kg、重心 (250, 150)；用这里的值重算如下。</p>
  {table(["部件", "kg", "重心 (x, y, z)"], mrows, "num")}
  {table(["工况", "翻倒余量 cm（后 / 前 / 侧）"], tiprows + [["人站在地上推拉横杆（只有台架自重）", f'横推 {tp["结论"]["min_tip_force_N"]} N 就翻，必须和床固定']])}
</section>

<section>
  <h2><span class="no">14</span>坐垫和称重单元的目标值</h2>
  <p class="cap">坐垫模型是“独立弹簧床”：压强 = 刚度 × 压下量。换成泡棉的常用指标（压缩 40% 时的压强）是近似，真实泡棉不是线性的，要用样块实测。</p>
  {table(["区", "模型刚度", "厚 mm", "压缩 40% 时"], cush)}
  <p>称重单元：{PT["cells"]["spec"]}。</p>
</section>

<section>
  <h2><span class="no">15</span>标准件额定值的来源（订货前按厂家样本核）</h2>
  {table(["型号", "用到的值", "来源", "要核的地方"], cat)}
</section>

<section>
  <h2><span class="no">16</span>v5.7 改了什么，还有什么没定</h2>
  <div class="key"><ol>{"".join(f"<li>{c}</li>" for c in chg)}</ol></div>
  <p><b>还没定：</b></p>
  <ol>{"".join(f"<li>{c}</li>" for c in todo)}</ol>
</section>

<section>
  <h2><span class="no">17</span>机构简图：v5.7 的想法</h2>
  <p class="key">会动的版本（可旋转 3D、机构动画、带编号三视图、有限元重点、接 Claude 的问答）：<a href="https://claude.ai/artifact/LxyAiPy2EsFtxV18R1ReSC">起身台机构与选型</a>。</p>
  <p><b>左（侧视，按比例）：</b>4 个构件。① 机架，即机构箱 + 底座 + 导轨。② 滑块座。③ 座板。④ 连杆。导轨是移动副 P，铰点 1 是转动副 R1，铰点 2 和 B 是球铰。按平面机构数：n = 4，低副 4 个，自由度 = 3 × (4 − 1) − 2 × 4 = 1，由丝杠驱动 ②。
  ② 沿导轨走决定座板升多高；④ 拉住 ③ 绕 R1 转多少，决定前倾多少。</p>
  <div class="fig kin">{KIN}</div>
  <p><b>右（沿铰点 1 轴线的剖面，y 方向按比例，另一方向示意）：</b>座板只在床头一侧有支撑，人坐偏时的力矩一路传下去。圆圈里的编号是传力顺序：</p>
  <div class="fig">{SEC}</div>
  <ol>{"".join(f"<li>{t}</li>" for t in path)}</ol>
  <p class="cap">关键改动在 3–5：两个轴承拉开 61 mm，装在一根穿过竖槽的 Ø75 钢管里。这样在径向只占 Ø75，离床够远；交叉滚子轴承要 Ø120 才扛得住，会伸到离床 9 mm。</p>
</section>
</div>
<script>
document.getElementById("copy-csv").addEventListener("click", async () => {{
  const t = document.getElementById("csv"), m = document.getElementById("copy-msg");
  try {{ await navigator.clipboard.writeText(t.value); m.textContent = "已复制，可以粘贴到 Excel 或 SolidWorks 设计表"; }}
  catch (e) {{ t.hidden = false; t.select(); m.textContent = "浏览器不让直接复制：已选中下面的文字，按 Ctrl+C"; }}
}});
</script>
'''
open(os.path.join(HERE, "cad_sheet.html"), "w").write(page); print(len(page), "bytes")
