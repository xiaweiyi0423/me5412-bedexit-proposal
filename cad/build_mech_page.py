"""Build cad/mechanism.html: animated mechanism diagram + c1 section with the load path + part choices, materials and checks.
Data: model/calc_v13/seat_1dof/parts.json, cad_sheet.json, cad/travel_table.csv (through build_sheet.py, which this imports;
importing it also rebuilds cad_sheet.html). Regenerate the inputs with seat_1dof_cad_sheet.py and seat_1dof_parts.py first."""
import json, os, html
import build_sheet as BS
import mech_figs as MF
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PT, D, ST, YS, C1, CR, DR, LK, HRL, MS = BS.PT, BS.D, BS.ST, BS.YS, BS.C1, BS.CR, BS.DR, BS.LK, BS.HRL, BS.MS
kN, mm, rng, table = BS.kN, BS.mm, BS.rng, BS.table
r = lambda v: [round(1000 * float(a), 1) for a in v]

# ---------------------------------------------------------------- animation data (mm, degrees)
frames = [[float(c) for c in row] for row in BS.TT[1:]]          # stroke, Qx, Qz, phi, P1x, P1z, P2x, P2z, link_deg
h = 1000 * D["seat"]["half_len"]; lip = 1000 * D["seat"]["lip"]; bm = PT["beam"]
seat_polys = {"foamr": [(-h, 0), (-20, 0), (-20, -50), (-h, -50)], "foamf": [(-20, 0), (h, 0), (h, -80), (-20, -80)],
              "spacer": [(-h + lip, -50), (-20, -50), (-20, -80), (-h + lip, -80)], "board": [(-h + lip, -80), (h, -80), (h, -92), (-h + lip, -92)],
              "arm": [(-40, -100), (75, -100), (75, -110), (-40, -110)],
              "beam": [(1000 * bm["xs"][0], 1000 * bm["zs"][0]), (1000 * bm["xs"][1], 1000 * bm["zs"][0]), (1000 * bm["xs"][1], 1000 * bm["zs"][1]), (1000 * bm["xs"][0], 1000 * bm["zs"][1])]}
DATA = dict(frames=frames, seat=seat_polys, half=h,
            rail1=[r(D["rail1"]["lo"]), r(D["rail1"]["hi"])], rail2=[r(D["rail2"]["lo"]), r(D["rail2"]["hi"])],
            screw=[r(D["screw"]["axis_lo"]), r(D["screw"]["axis_hi"])], B=r(D["link"]["ground_pivot_B"]),
            housing=[r(p) for p in PT["housing"]["outline_xz"]], motor=[r(p) for p in D["housing"]["motor_xz"]],
            e=D["rail_dirs"]["e"], nf=D["rail_dirs"]["nf_rail1_to_rail2"], plate=dict(e=[-40, 190], nf=[-25, 175], rc=42), cart=37.5, rod=14.5,
            post=dict(x=1000 * D["handrail"]["post"]["x"], top=1000 * D["handrail"]["post"]["top_z"]), base=dict(x=r(D["base"]["x"]), h=1000 * D["base"]["tube_h"]),
            foot=dict(x=r(D["footplate"]["x"]), z=r(D["footplate"]["z"])), bed=420)

STEPS = [("seat cells", "体重压在坐垫上", "人坐偏 10 cm（设计载荷 100 kg × 1.5）。力经底板和 4 个称重单元到横梁。"),
         ("beam", "横梁把它带到座板侧缘", f'横梁 50 × 30 × 4 是悬臂，根部弯矩约 {ST["beam_M_vert_Nm"]["value"]:.0f} N·m，应力 {PT["beam"]["vm_MPa"]:.0f} MPa（允许 237）。高只有 30，因为再深就碰到小腿。'),
         ("knuckle shaft", "节点板交给铰点 1 轴", f'轴端法兰用 6 颗 M10 接节点板。轴 Ø30（42CrMo4），在轴承 B 处弯矩 {ST["shaft_M_at_B_Nm"]["value"]:.0f} N·m。'),
         ("brgB brgA", "两个轴承把力矩拆成一对力", f'两个圆锥滚子轴承相距 {C1["spacing_mm"]:.0f} mm：力矩 ÷ 距离 = 一推一拉的径向力，最大 {kN("brgA_radial_N")} kN，额定静载 44 kN。座板只能绕这根轴转：转动副 R1。'),
         ("cart plate", "轴承座筒焊在滑块板上", "钢管 Ø75 穿过内壁竖槽，焊在 20 mm 滑块板上，两个轴承孔焊后一起加工，保证同轴。"),
         ("carr rail back", "4 个滑块、2 根导轨、侧板", f'滑块板把力分给 4 个滑块（150 × 150 方阵），每个最多 {CR["P0_x13_kN"]} kN（含不均 1.3 倍）。导轨装在侧板上，侧板和内壁、围板连成盒子，再到底座和床。'),
         ("arm", "另一路：摆臂和连杆管倾角", "铰点 2 摆臂从轴承座筒下方的窗口伸出，经杆端和连杆接到机构箱底部的 B。它只管座板绕轴转多少，所以连杆只受拉压。")]

CARDS = [
 dict(t="铰点 1 轴承", pick="圆锥滚子轴承 32006 X × 2", tag="关键", why=f'背对背装，相距 {C1["spacing_mm"]:.0f} mm，放在一根 Ø75 的轴承座筒里，座筒穿过内壁竖槽。',
      nums=[("当量静载", f'{C1["P0_kN"]} kN'), ("额定静载", "44 kN"), ("安全系数", f'{C1["sf"]}')],
      alt=[("交叉滚子 RU66（Ø95）", "强度不够：当量静载 21 kN ≈ 额定 22.3 kN", False), ("交叉滚子 RU85（Ø120）", "强度够，但伸到离床 9 mm（规则 ≥ 15）", False)]),
 dict(t="直线导轨", pick="HIWIN HGR15 × 2 + HGH15CA × 4", tag="", why="两根导轨装在同一块侧板上，间距 150；每根两个滑块，间距 150。偏载靠这个方阵拆成力偶。",
      nums=[("每块当量静载 × 1.3", f'{CR["P0_x13_kN"]} kN'), ("额定静载", "16.97 kN"), ("安全系数", f'{CR["sf"]}')],
      alt=[("20 号（HGH20CA）", "余量更大，但滑块长 77.5，导轨和机构箱都要加长约 2 cm；15 号已够", None)]),
 dict(t="丝杠", pick="滚珠丝杠 Ø16 导程 10", tag="", why="3 cm/s 时丝杠 180 r/min。上端固定（BK12），人坐着时丝杠受拉，不会压弯。能反向驱动，应急时靠人自重慢慢降。",
      nums=[("最大轴向", f'{kN("nut_axial_N")} kN'), ("额定静载", "19.3 kN"), ("寿命", f'约 {DR["life_cycles"]} 次')],
      alt=[("梯形丝杠（自锁）", "不能靠自重降，断电时人下不来", False)]),
 dict(t="电机和传动比", pick="24 V 无刷电机 57 机座 + 同步带 1:3", tag="", why=f'起身时最大推力 {DR["lift_force_N"]} N，换到电机上 {DR["motor_torque_Nm"]} N·m @ {DR["motor_rpm"]} r/min，输出约 {DR["motor_power_W"]} W；选额定 ≥ 0.6 N·m。',
      nums=[("电机扭矩", f'{DR["motor_torque_Nm"]} N·m'), ("应急下降余量", f'{PT["emergency_belt3"]["margin"]}'), ("1:1 时余量", "2.6")],
      alt=[("同步带 1:1", "电机要 1.3 N·m，体积大一倍；应急余量更大", None)]),
 dict(t="制动和限速", pick="失电制动器 8 N·m + 离心限速器，都装在丝杠上", tag="", why="制动器装在丝杠上，同步带不在承重路径里，带断了座板也不会掉。应急时拉索松开制动器，限速器把座板限在 3 cm/s。",
      nums=[("需要", f'≥ {BS.brake:.1f} N·m'), ("选", "8 N·m"), ("限速", "180 r/min")], alt=[("制动器装在电机轴上", "同步带进入承重路径，带断就失去制动", False)]),
 dict(t="连杆", pick="Ø20 × 2 钢管 + M10 杆端关节轴承 × 2", tag="", why="两端球铰，连杆只受拉压。一端左旋螺纹，装配时可调长度。",
      nums=[("拉 / 压", f'{PT["link_forces_N"]["tension"] / 1000:.1f} / {PT["link_forces_N"]["compression"] / 1000:.1f} kN'), ("压杆安全系数", f'{LK["buckling_sf"]}'), ("杆端安全系数", f'{LK["rod_end_sf"]}')],
      alt=[("M8 杆端", f'头部更小，机构箱离床可从 {PT["clearances"]["housing_bed_cm"] * 10:.0f} 增到约 15 mm；强度仍够（待核样本）', None)]),
 dict(t="座板骨架", pick="S355 矩形管 50 × 30 × 4 + 12 mm 桦木多层板", tag="", why="横梁高度被小腿间隙卡在 30 mm 以内，所以用钢不用铝。底板是多层板，坐垫面料可以直接钉上去。",
      nums=[("应力", f'{PT["beam"]["vm_MPa"]:.0f} / 237 MPa'), ("外缘下沉", f'{PT["beam"]["corner_mm"]} mm'), ("离腿", f'{PT["clearances"]["legs_min_cm"] * 10:.0f} mm')],
      alt=[("铝 6061 同截面", "刚度只有钢的 1/3，外缘下沉约 5 mm，单这一项就用完预算", False)]),
 dict(t="滑块板", pick="S355 钢板 20 mm（和轴承座筒焊成一体）", tag="", why="最远的滑块离铰点 1 约 15 cm，偏载要从轴承座筒穿过板传过去。",
      nums=[("应力（粗估）", f'{PT["plate"]["S355 钢板 20"]["stress_MPa"]} / 237 MPa'), ("外缘下沉", f'{PT["plate"]["S355 钢板 20"]["corner_mm"]} mm'), ("质量", f'{MS["plate_kg"]} kg（含座筒等）')],
      alt=[("S355 15 mm", f'应力 {PT["plate"]["S355 钢板 15"]["stress_MPa"]} MPa，超过允许值', False), ("6061 铝 25 mm", "能过，但钢座筒不能焊到铝板上", None)]),
 dict(t="扶手", pick="立柱方管 60 × 60 × 4 + 横杆 Ø38 × 4（S355 喷塑）", tag="", why=f'按 ADA 扶手载荷 1112 N × 1.5 = {HRL["load_N"]} N 加在横杆末端。',
      nums=[("立柱末端位移", f'{HRL["post"]["方管 60×60×4"]["tip_pull_mm"]} mm'), ("横杆应力", f'{HRL["bar"]["圆管 Ø38×4（S355 喷塑）"]["stress_MPa"]} / 237 MPa'), ("立柱根部弯矩", f'{HRL["post"]["方管 60×60×4"]["base_moment_Nm"]} N·m')],
      alt=[("立柱 50 × 50 × 4", f'强度够，但末端晃 {HRL["post"]["方管 50×50×4"]["tip_pull_mm"]} mm', None), ("304 不锈钢 Ø38 × 2 横杆", f'应力 {HRL["bar"]["圆管 Ø38×2（304 不锈钢）"]["stress_MPa"]} / 137 MPa，不够', False)]),
 dict(t="坐垫", pick="后区高硬度再生海绵 50 mm + 前区高回弹海绵 80 mm", tag="", why="后硬前软，让坐板的推力多落在骨盆、少压大腿。面料用防水可擦洗、表面高摩擦的 PU 涂层布。",
      nums=[("后区压 40%", f'约 {PT["cushion"]["后区（x_s < −20 mm，含 45 mm 软唇边）"]["cv40_kPa"]:.0f} kPa'), ("前区压 40%", f'约 {PT["cushion"]["前区"]["cv40_kPa"]:.0f} kPa'), ("依据", "坐垫模型 10 / 3 kPa/cm")],
      alt=[("普通家具海绵", "压 40% 时通常只有几 kPa，后区太软，推不到骨盆（推断，需样块实测）", None)])]

def card(c):
    alts = "".join(f'<li class="{"no" if a[2] is False else "maybe"}"><b>{html.escape(a[0])}</b>：{html.escape(a[1])}</li>' for a in c["alt"])
    nums = "".join(f'<div><span>{html.escape(k)}</span><b>{html.escape(v)}</b></div>' for k, v in c["nums"])
    return (f'<article class="card{" key" if c["tag"] else ""}"><header><span class="ct">{html.escape(c["t"])}</span>{"<span class=pill>" + c["tag"] + "</span>" if c["tag"] else ""}</header>'
            f'<h3>{html.escape(c["pick"])}</h3><p>{html.escape(c["why"])}</p><div class="nums">{nums}</div><p class="altt">没选的</p><ul class="alts">{alts}</ul></article>')

groups = []
for row in BS.bom:
    if row[0]: groups.append(row[0])
bom_rows = []; g = ""
for row in BS.bom:
    g = row[0] or g; bom_rows.append(f'<tr data-g="{g}">' + "".join(f"<td>{x}</td>" for x in [g] + row[1:]) + "</tr>")
chips = '<button type="button" class="chip on" data-g="*">全部</button>' + "".join(f'<button type="button" class="chip" data-g="{x}">{x}</button>' for x in groups)
steps = "".join(f'<li><button type="button" class="step" data-parts="{p}"><span class="sn">{i}</span><span><b>{html.escape(t)}</b><br>{html.escape(d)}</span></button></li>' for i, (p, t, d) in enumerate(STEPS, 1))

exec(open(os.path.join(HERE, 'mech_page_tpl.py'), encoding='utf-8').read())
