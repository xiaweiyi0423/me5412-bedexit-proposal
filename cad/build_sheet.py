"""Build cad/cad_sheet.html (the dimension sheet for the CAD model, role 3) from model/calc_v13/seat_1dof/cad_sheet.json and
cad/travel_table.csv. Regenerate the inputs with model/calc_v13/seat_1dof_cad_sheet.py after any model change, then run this."""
import csv, json, math, os, html
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/cad_sheet.json")))
C3 = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/cantilever3d.json")))
TT = list(csv.reader(open(os.path.join(HERE, "travel_table.csv")))); KP = list(csv.reader(open(os.path.join(HERE, "key_poses.csv"))))
mm = lambda v: (lambda t: t[:-2] if t.endswith(".0") else t)(f"{1000 * v:.1f}").replace("-", "−"); P = lambda p: f"({mm(p[0])}, {mm(p[1])})"
J = D["joints"]; brake = 2 * C3["nut_axial_N"]["value"] * D["screw"]["lead_mm"] / 1000 / (2 * math.pi)

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
    board = [W(Q, phi, p) for p in ((-h + lip, -0.05), (-0.02, -0.05), (-0.02, -0.08), (h, -0.08), (h, -0.092), (-0.02, -0.092), (-0.02, -0.062), (-h + lip, -0.062))]
    return poly(rear, cls + " foamr") + poly(front, cls + " foamf") + poly(board, cls + " board")
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
svg.append(poly(D["housing"]["outline_xz"], "housing")); svg.append(poly(D["housing"]["motor_xz"], "motor"))
r1, r2, sc = D["rail1"], D["rail2"], D["screw"]
svg.append(line(r1["lo"], r1["hi"], "rail")); svg.append(line(r2["lo"], r2["hi"], "rail")); svg.append(line(sc["axis_lo"], sc["axis_hi"], "screw"))
svg.append(seat(F1["Q"], F1["phi"], "ghost")); svg.append(line(B, F1["P2"], "link ghostl"))
svg.append(seat(F0["Q"], F0["phi"], "now")); svg.append(line(B, F0["P2"], "link"))
for p in (F0["P1"], F0["P2"]): svg.append(dot(p))
for p in (F1["P1"], F1["P2"]): svg.append(dot(p, "pin ghostp"))
svg.append(dot(B, "pivot", 5))
hr = D["handrail"]; svg.append(line((hr["post"]["x"], b["tube_h"]), (hr["post"]["x"], hr["post"]["top_z"]), "post")); svg.append(dot((hr["post"]["x"], hr["post"]["top_z"]), "bar", 7))
SC40 = (sc["axis_lo"][0] + 0.45 * (sc["axis_hi"][0] - sc["axis_lo"][0]), sc["axis_lo"][1] + 0.45 * (sc["axis_hi"][1] - sc["axis_lo"][1]))
L = [(F0["Q"], "Q 座面中心（齐平）", 10, 18), (F1["Q"], "Q（顶位）", -12, -14), (F0["P1"], "铰点 1", -10, 4), (F0["P2"], "铰点 2", -10, 4), (B, "连杆地面铰点 B", 10, 4),
     (r1["hi"], "导轨 1", -10, -4), (r2["hi"], "导轨 2", 8, 12), (SC40, "丝杠轴线", 10, 4), (D["housing"]["motor_xz"][1], "电机 + 制动器", 8, -6),
     ((hr["post"]["x"], hr["post"]["top_z"]), "横杆（垂直纸面） z 950", -12, -12), ((0.42, 0.047), "踏板", 0, -8), ((0.5049, 0.40), "机构箱（侧视外廓）", 6, 0)]
for p, t, dx, dy in L: svg.append(lab(p, t, dx, dy, "lab", "end" if dx < 0 else "start"))
svg.append("</svg>")

def table(head, rows, cls=""):
    return (f'<div class="tw"><table class="{cls}"><thead><tr>' + "".join(f"<th>{x}</th>" for x in head) + "</tr></thead><tbody>" +
            "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table></div>")
Y = {"座板（宽 440）": "−220 … +220", "机构箱内壁（竖槽所在）": "250", "连杆平面": f'{mm(D["link"]["y"])}', "滑块板（假设厚 15）": "290 … 305", "丝杠轴线": f'{mm(sc["y"])}',
     "导轨安装面（两根导轨都在这里）": f'{mm(r1["y"])}', "机构箱外壁": "360", "底座": f'{mm(b["y"][0])} … {mm(b["y"][1])}', "横杆": f'{mm(hr["bar"]["y"][0])} … {mm(hr["bar"]["y"][1])}', "扶手立柱": f'{mm(hr["post"]["y"])}'}
fixed = [["导轨 1（铰点 1 的滑块在上面走）", f'下端 {P(r1["lo"])}，上端 {P(r1["hi"])}', f'长 {mm(r1["length"])}，与竖直成 {r1["angle_from_vertical_deg"]}°'],
         ["导轨 2（只扛偏载）", f'下端 {P(r2["lo"])}，上端 {P(r2["hi"])}', f'与导轨 1 平行，在导轨平面内相距 {mm(r2["offset"])}，偏向前下方'],
         ["丝杠轴线", f'{P(sc["axis_lo"])} → {P(sc["axis_hi"])}', f'行程 {mm(sc["stroke"])}，导程 {sc["lead_mm"]:.0f}'],
         ["连杆地面铰点 B", P(B), f'连杆长 {mm(D["link"]["length"])}'],
         ["机构箱侧视外廓（含 20 壁）", " ".join(P(p) for p in D["housing"]["outline_xz"]), f'y {mm(D["housing"]["y"][0])} … {mm(D["housing"]["y"][1])}'],
         ["电机 + 制动器外廓", " ".join(P(p) for p in D["housing"]["motor_xz"]), "同步带接丝杠，约 1:1"],
         ["底座框（管高 35）", f'x {mm(b["x"][0])} … {mm(b["x"][1])}', f'y {mm(b["y"][0])} … {mm(b["y"][1])}'],
         ["踏板", f'x {mm(fp["x"][0])} … {mm(fp["x"][1])}，z {mm(fp["z"][0])} … {mm(fp["z"][1])}', f'y {mm(fp["y"][0])} … {mm(fp["y"][1])}'],
         ["L 形扶手", f'立柱 x {mm(hr["post"]["x"])}，顶 z {mm(hr["post"]["top_z"])}', "横杆从立柱伸到人正前方，末端圆头软包、夜光"]]
seatrows = [["座板长（沿座面）", f'{mm(2 * h)}，从 Q 往后 {mm(h)}、往前 {mm(h)}', f'后端 {mm(lip)} 是软唇边（搭在床垫上），刚性部分从 x<sub>s</sub> = −{mm(h - lip)} 开始'],
            ["坐垫", f'后区 x<sub>s</sub> −{mm(h)} … {mm(D["seat"]["split_x_s"])}：厚 50；前区 {mm(D["seat"]["split_x_s"])} … +{mm(h)}：厚 80', "后 10 kPa/cm、前 3 kPa/cm（分区坐垫）"],
            ["坐垫 + 底板总厚", f'后 {mm(D["seat"]["foam_board_t"]["rear"])}，前 {mm(D["seat"]["foam_board_t"]["front"])}', "底板厚 12（假设）"],
            ["铰点 1（座板坐标）", f'({mm(D["seat"]["pins_seat_frame"]["c1"][0])}, {mm(D["seat"]["pins_seat_frame"]["c1"][1])})', "相对 Q，座板坐标系"],
            ["铰点 2（座板坐标）", f'({mm(D["seat"]["pins_seat_frame"]["c2"][0])}, {mm(D["seat"]["pins_seat_frame"]["c2"][1])})', f'两铰点相距 {mm(D["seat"]["pins_seat_frame"]["spacing"])}'],
            ["座板下悬臂托架（假设截面）", f'x<sub>s</sub> {mm(D["seat_arm"]["seat_frame_x"][0])} … {mm(D["seat_arm"]["seat_frame_x"][1])}，z<sub>s</sub> {mm(D["seat_arm"]["seat_frame_z"][0])} … {mm(D["seat_arm"]["seat_frame_z"][1])}', f'y {mm(D["seat_arm"]["y"][0])} … {mm(D["seat_arm"]["y"][1])}，从座板下穿过竖槽进箱'],
            ["滑块板（假设）", f'沿导轨：铰点 1 往下 40 到往上 {mm(D["carriage_plate"]["along_rail_from_pin1"][1])}；垂直导轨：导轨 1 外 20 到导轨 2 外 20', "y 290 … 305"],
            ["滑块", "每根导轨 2 个，相距 150（沿导轨）", "滑块中心：铰点 1 处、铰点 1 往上 150；导轨 2 上对应位置"]]
jrows = [["铰点 1（座板 ↔ 滑块板，绕 y 转）", f'力矩 {J["c1"]["must_carry"]["moment_Nm"]} N·m + 力 {J["c1"]["must_carry"]["force_N"] / 1000:.1f} kN', "<b>必须能承受力矩。</b>A：薄型交叉滚子轴承贴在滑块板侧面（厚约 20、外径 120–150）；B：短轴穿过竖槽，两个轴承相距约 140（每个约 " + f'{J["c1"]["bearing_radial_N"]["s140"] / 1000:.1f} kN）。只在箱内 60–80 间距：每个 {J["c1"]["bearing_radial_N"]["s80"] / 1000:.1f}–{J["c1"]["bearing_radial_N"]["s60"] / 1000:.1f} kN，而且和丝杠、连杆挤'],
        ["铰点 2、B（连杆两端）", f'连杆轴向 {J["c2"]["link_axial_N"] / 1000:.1f} kN', "杆端关节轴承（球铰），连杆只受拉压、不受侧向力"],
        ["丝杠螺母", f'轴向 {J["nut"]["axial_N"] / 1000:.1f} kN', f"浮动接头，只传轴向；失电制动器 ≥ {brake:.1f} N·m（2 倍保持力）"],
        ["每个滑块", f'垂直侧板 {J["carriages"]["radial_N"] / 1000:.1f} kN，导轨平面内 {J["carriages"]["lateral_N"] / 1000:.1f} kN，合力 {J["carriages"]["resultant_N"] / 1000:.1f} kN', "15 号滑块额定静载约 17–23 kN；离铰点 1 最近的那个选型时乘 1.3–1.5"],
        ["应急拉索拨杆", "—", D["lever"]], ["和床的固定件", f'{D["loads"]["anchor_N"]} N', "锁在床架或床腿上（ADA 扶手载荷 1112 N × 1.5）；形式待定"]]
clr = [["机构箱、座板、支架离床（全行程）", "21", "床沿到箱壁"], ["座板侧缘到机构箱内壁", "30", "手指夹不住"], ["座板底面到底座（最低处）", "283", ""],
       ["座板、支架离小腿和脚（81 人，到站直）", f'{D["clearances"]["legs_cm"]["min"] * 10:.0f}', "最紧的是 1.75 m、脚靠后的人站直时"], ["全部活动零件离地", "234", ""]]
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
  --blue:#1E5AA8; --blue2:#9DB8DE; --red:#B3261E; --foam:#E9B872; --foam2:#F4D9AE; --steel:#5B6B7C; --steel2:#B8C1CB; --bed:#DCE1E7;
  --display:"Noto Serif SC", "Songti SC", serif; --body:"Noto Sans SC", "PingFang SC", system-ui, sans-serif; --mono:"IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper:#12171D; --sheet:#1A2129; --ink:#E6EAEE; --ink2:#B9C2CC; --muted:#8B95A0; --rule:#2E3741;
  --blue:#7FAEEA; --blue2:#3D5F8C; --red:#F08A80; --foam:#B98A45; --foam2:#7A6440; --steel:#9AA9B8; --steel2:#56636F; --bed:#2A323B; color-scheme:dark }} }}
:root[data-theme="dark"] {{
  --paper:#12171D; --sheet:#1A2129; --ink:#E6EAEE; --ink2:#B9C2CC; --muted:#8B95A0; --rule:#2E3741;
  --blue:#7FAEEA; --blue2:#3D5F8C; --red:#F08A80; --foam:#B98A45; --foam2:#7A6440; --steel:#9AA9B8; --steel2:#56636F; --bed:#2A323B; color-scheme:dark }}
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
  <div class="name"><h1>起身台 CAD 尺寸表</h1><p class="sub">单自由度坐板（斜导轨 + 倾角连杆）：给角色 3 建 SolidWorks 装配体用。所有坐标由模型算出，标“假设”的是模型没用到、需要 CAD 定的截面尺寸。</p></div>
  <div class="meta"><div>版本</div><div>v5.6 · 2026-10-27</div><div>单位</div><div>mm，角度 °</div><div>来源</div><div>calc_v13 · cad_sheet.py</div><div>交给</div><div>角色 3（CAD）</div></div>
</header>

<section>
  <h2><span class="no">00</span>先读这三条</h2>
  <div class="key"><ol>
    <li><b>坐标系：</b>原点在地面、床的长边正下方，y = 0 是座板中面。x 向床外（床在 x &lt; 0），y 沿床长、指向床头一侧（机构箱在 +y），z 向上。座板坐标系：原点 Q 是座面（坐垫上表面）中点，x<sub>s</sub> 沿座面向前，z<sub>s</sub> 垂直座面；座板前倾 φ 时，世界坐标 = Q + R(φ)·(x<sub>s</sub>, z<sub>s</sub>)。</li>
    <li><b>不能改的：</b>两根导轨的位置和角度、铰点 1 和 2 在座板上的位置、连杆地面铰点 B 和连杆长度。它们一起决定座板的轨迹；改了任何一个，81 人的检查要重算。</li>
    <li><b>新发现的关键件：</b>铰点 1 要能承受约 {J["c1"]["must_carry"]["moment_Nm"]} N·m 的力矩（座板单侧悬臂的偏载都经过它），不能用普通销轴。两种做法见第 05 项，请在 CAD 里选一种。</li></ol></div>
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
  <h2><span class="no">05</span>关节和受力（100 kg × 1.5 + 座板 10 kg，偏向敞开一侧 10 cm，含竖直和沿座面的力，全行程最不利）</h2>
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
  {table(["工况", "说明"], [[c, ""] for c in D["fea"]["cases"]] + [["变形目标", f'100 kg 满载时座板外缘下沉 ≤ {D["fea"]["deflection_target_mm"]} mm（悬臂约 540，根部转 1.5° 外缘就沉约 14）']])}
</section>

<section>
  <h2><span class="no">09</span>需要 CAD 决定的</h2>
  <div class="key"><ol>
    <li>铰点 1 的做法：交叉滚子轴承，还是穿过竖槽的双轴承（第 05 项）。</li>
    <li>各件截面：滑块板厚、悬臂托架、连杆管径、机构箱侧板厚（侧板要扛滑块传来的拉拔力）。</li>
    <li>应急拨杆的位置：横杆与立柱拐角下方、带翻盖，坐着够不够得到。</li>
    <li>和床的固定件：床腿夹，还是底板伸到床腿下面。</li>
    <li>CAD 出来以后，把真实质量和质心给角色 4 复核稳定性。</li></ol></div>
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
