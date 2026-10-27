# ---------------------------------------------------------------- 3D model data (world mm, z up)
P1a, P1b = np.array(frames[0][4:6]), np.array(frames[-1][4:6]); dsl = (P1b - P1a) / np.hypot(*(P1b - P1a)); nsl = np.array([-dsl[1], dsl[0]])
SLOT = [(P1a + 43.5 * nsl - 40 * dsl).tolist(), (P1b + 43.5 * nsl + 40 * dsl).tolist(), (P1b - 43.5 * nsl + 40 * dsl).tolist(), (P1a - 43.5 * nsl - 40 * dsl).tolist()]
c1s = [1000 * v for v in D["seat"]["pins_seat_frame"]["c1"]]; c2s = [1000 * v for v in D["seat"]["pins_seat_frame"]["c2"]]
NAMES = {}
for row in BS.bom: NAMES[row[1]] = [row[2], row[3]]
DATA.update(slot=SLOT, c1s=c1s, c2s=c2s, names=NAMES)

# ---------------------------------------------------------------- FEA focus (role 4) and modelling guide (role 3)
CS = PT["cases"]; NF3 = np.array([D["rail_dirs"]["nf_rail1_to_rail2"][0], 0.0, D["rail_dirs"]["nf_rail1_to_rail2"][1]])
vec = lambda v, u="N": "(" + ", ".join(f"{x:+.0f}" for x in v) + f") {u}"
neg = lambda v: [-x for x in v]
def corner_pt(case):
    Q, phi = case["pose"]["Q_mm"], case["pose"]["phi"]; p = MF.Wt(Q, phi, (85, 0)); return f"({p[0]:.0f}, −220, {p[1]:.0f})"
def c1_rows(case, name):
    return [[name, f'行程 {case["pose"]["stroke_mm"]:.0f} mm，Q = ({case["pose"]["Q_mm"][0]:.0f}, {case["pose"]["Q_mm"][1]:.0f})，前倾 {case["pose"]["phi"]:.1f}°',
             f'作用点：铰点 1 轴线中点 {vec(case["c1_centre_mm"], "mm")}', f'力 {vec(neg(case["F1_N"]))}', f'力矩 {vec(neg(case["M1_Nm"]), "N·m")}']]
car_rows = []
cH = CS["housing_Mx_Nm"]
for i, (fv, p) in enumerate(zip(cH["carriages_nf_y_N"], cH["carriage_points_mm"])):
    F = -(fv[0] * NF3 + fv[1] * np.array([0, 1.0, 0])); car_rows.append([f"滑块 {['1 下', '1 上', '2 下', '2 上'][i]}", vec(p, "mm"), vec(F)])
cB = CS["beam_vm_MPa"]
FEA = [
 dict(n=1, t="铰点 1 组件 + 滑块座焊件", codes="J1 J2 J3 C1", fig=MF.fea_c1(), lvl="最先做",
      why=[f'整个座板只在床头一侧有支撑，人坐偏时的力矩（约 {ST["c1_moment_Nm"]["value"]:.0f} N·m）和力（约 {kN("c1_force_N")} kN）全部经过这里，是整台机器最集中的传力点。',
           "轴承座筒穿过内壁竖槽，中段开了 60° 窗口给摆臂穿出，又和滑块板焊在一起：窗口角和焊缝根部有应力集中，手算算不出来。",
           f'手算只把滑块板当窄条悬臂：应力 {PT["plate"]["S355 钢板 20"]["stress_MPa"]} MPa（允许 237），座板外缘下沉 {PT["plate"]["S355 钢板 20"]["corner_mm"]} mm，是变形预算里第二大的一项，误差可能不小。',
           "两个轴承孔焊后要同轴；受力后两孔相对转得太多，圆锥滚子轴承会偏载。"],
      model="滑块板 + 轴承座筒做成一个实体（焊缝用 3–4 mm 圆角近似）；两个轴承不建滚子，用“轴承接头”或在两个孔面上加分布径向力；J1 轴可以不进 FEA（梁公式已够）。网格：窗口角、焊缝根部加密到 1–2 mm，二阶四面体。",
      loads=c1_rows(CS["brg_P0_N"], "工况 1-a：偏 10 cm + 沿座面往前 0.3（轴承力最大）") + c1_rows(CS["c1_moment_Nm"], "工况 1-b：偏 10 cm + 侧向 0.3（力矩最大）"),
      bc="4 个滑块安装面固定（更准：每个滑块用 200 N/µm 的弹簧）；螺母座处只约束沿导轨方向。",
      out=["Mises 最大值和位置（焊缝根部、窗口角）≤ 237 MPa（S355，屈服 / 1.5）", "铰点 1 轴线在载荷下的转角 × 0.49 m = 对座板外缘下沉的贡献，目标 ≤ 1.5 mm",
           "两个轴承孔轴线的相对转角 ≤ 1 mrad（约 3.4′）", f'支反力自查：4 个滑块合力应接近 {CR["P0_kN"]} kN 量级（不乘 1.3）'], codes_hl=["J1", "J2", "J3", "C1"]),
 dict(n=2, t="座板横梁 + 节点板（含焊缝）", codes="S7 S8 S6", fig=MF.fea_beam(), lvl="第二",
      why=["横梁高度被小腿间隙卡死在 30 mm，不能靠加高解决；它是变形预算里最大的一项（手算外缘下沉 1.7 mm）。",
           f'横梁和节点板的角焊缝正好在最大弯矩处（约 {ST["beam_M_vert_Nm"]["value"]:.0f} N·m），而且每次起坐都加载一次：每天十几次、十年约 5 万次，要看疲劳。',
           "节点板同时受弯（来自横梁）和扭（座板前后偏载），手算是分开算的。"],
      model="横梁 + 称重支臂 + 节点板 + J1 轴端法兰建成一个实体或壳 + 实体混合；底板和坐垫不建，把载荷经 4 个称重单元垫块传进来（刚性连接）。",
      loads=[[f'工况 2：偏 10 cm、前沿附近（全行程里横梁应力最大）', f'行程 {cB["pose"]["stroke_mm"]:.0f} mm，前倾 {cB["pose"]["phi"]:.1f}°', f'作用点 {vec(cB["load_point_mm"], "mm")}', f'力 {vec(cB["load_N"])}', "另做：同一点加侧向 ± 441 N"]],
      bc="J1 轴端法兰和节点板的接触面固定（或把 J1 轴也建上，在两个轴承位置用轴承约束）。",
      out=[f'焊缝热点应力：设计载荷下 ≤ 237 MPa；名义载荷（100 kg、不乘 1.5）下应力幅 ≤ 100 MPa（按焊缝 FAT 71、10 万次估，留余量）', f'座板外缘（y −220、前沿）下沉 ≤ 2 mm', "横梁局部屈曲（壁厚 4 mm 一般没问题，顺手看一眼）"],
      codes_hl=["S7", "S8", "S6"]),
 dict(n=3, t="机构箱盒体（带竖槽）", codes="H1 H2 H3", fig=MF.fea_house(), lvl="第三",
      why=["两根导轨装在侧板 H1 上，座板的偏载最后都变成滑块对侧板“往外拔、往里压”的力，侧板像一面悬臂墙。",
           f'手算把箱子当成闭口盒子：内壁 H2、侧板 H1、围板 H3 一起受力，外缘只沉 {PT["housing_box"]["corner_mm"]} mm。但如果盒子不起作用、只靠 15 mm 铝侧板自己扛，同样的力会让外缘沉 20 mm 以上。',
           "内壁上沿铰点 1 轨迹开了一条 87 mm 宽的斜槽，竖槽以上的部分盒子是开口的，抗弯和抗扭都会掉多少，手算不知道。这一项决定 H2、H3 要多厚、竖槽两端要不要加强。"],
      model="H1、H2、H3 用壳单元（中面，厚度 15 / 2 / 2 mm），竖槽按实际开出来；底边和底座框螺栓连接。导轨不建，滑块力直接加在导轨安装面对应位置（每个滑块 61 × 34 的面上）。",
      loads=[["工况 3：偏 10 cm + 侧向 0.3，到顶位（横滚力矩最大）", "4 个滑块对侧板的力见右表", f'丝杠上端支撑：沿导轨 {cH["nut_N"]:.0f} N', f'连杆 B 点：{cH["link_N"]:.0f} N（沿连杆）', ""]],
      bc="底边（z = 40）和底座框连接处固定。",
      out=["导轨安装区在载荷下的转角 × 0.56 m = 对座板外缘下沉的贡献，目标 ≤ 0.5 mm", "竖槽两端、内壁和围板连接处 Mises ≤ 237 MPa（钢）/ 160 MPa（铝）", f'底部支反力矩自查：约 {ST["housing_Mx_Nm"]["value"]:.0f} N·m 绕 x 轴'],
      car=car_rows, codes_hl=["H1", "H2", "H3"]),
 dict(n=4, t="扶手立柱根部 + 底座框", codes="B4 B5 B1", fig=MF.fea_rail(), lvl="第四",
      why=[f'立柱根部弯矩约 {HRL["post"]["方管 60×60×4"]["base_moment_Nm"]} N·m，是全机最大的弯矩；底座管只有 30 mm 高，立柱焊在它上面，根部焊缝和底座管局部变形手算都只能粗估。',
           f'人起身时整个人的重心靠在横杆上，横杆“晃”会让人害怕：手算立柱 + 横杆末端位移 {HRL["post"]["方管 60×60×4"]["tip_pull_mm"]} mm，要 FEA 确认加上底座变形后还在 10 mm 以内。'],
      model="立柱、横杆用梁或实体；底座框用壳或实体；根部底板和筋按图建。",
      loads=[["工况 4：ADA 扶手载荷 1112 N × 1.5 = 1668 N，加在横杆末端 (700, −50, 950)", "三个方向分开算：竖直向下、向人拉（−x）、侧推（± y）", "", "", ""]],
      bc="底座和床的两个固定点固定；底座底面和地面只压不拉（或简化成固定，偏危险少）。",
      out=["根部焊缝 Mises ≤ 237 MPa", "横杆末端位移 ≤ 10 mm", "固定点拉力，和手算 2.2 kN 对比"], codes_hl=["B4", "B5", "B1"])]
NOFEA = [("铰点 1 轴 J1、摆臂 J4、连杆 L1", "梁公式已有足够余量（轴 208 / 433 MPa，连杆压杆安全系数 29）；摆臂和轴的连接用胀紧套，按厂家扭矩表选。"),
         ("导轨、滑块、轴承、丝杠、杆端", "标准件，按厂家额定静载和安全系数选（第 3 节表）；FEA 里不建细节，只当刚体或弹簧。"),
         ("坐垫、底板", "坐垫是软的，用样块压缩试验定；底板是多层板，只起铺垫作用。"),
         ("踏板 B2", "10 mm 铝板，手算下沉 1.9 mm、应力 44 MPa，余量大。")]
def fea_card(F):
    loads = "".join(f'<tr>{"".join(f"<td>{c}</td>" for c in r)}</tr>' for r in F["loads"])
    car = ""
    if F.get("car"): car = '<div class="tw"><table class="num"><thead><tr><th>滑块</th><th>位置 (x, y, z)</th><th>对侧板的力 (Fx, Fy, Fz)</th></tr></thead><tbody>' + "".join(f'<tr>{"".join(f"<td>{c}</td>" for c in r)}</tr>' for r in F["car"]) + "</tbody></table></div>"
    return f'''<article class="fea" id="fea-{F["n"]}" data-hl="{' '.join(F["codes_hl"])}">
  <header><span class="rank">{F["n"]}</span><div><h3>{html.escape(F["t"])}</h3><p class="codes">零件 {F["codes"]} · {F["lvl"]}</p></div><button type="button" class="btn ghost show3d" data-hl="{' '.join(F["codes_hl"])}">在 3D 里看</button></header>
  <div class="feagrid"><div class="feafig">{F["fig"]}</div>
  <div class="featext"><h4>为什么是这里</h4><ul>{"".join(f"<li>{w}</li>" for w in F["why"])}</ul>
  <h4>怎么建</h4><p>{F["model"]}</p><h4>约束</h4><p>{F["bc"]}</p></div></div>
  <h4>载荷（已含 1.5 倍；坐标见第 1 节，单位 mm、N）</h4>
  <div class="tw"><table class="loads"><tbody>{loads}</tbody></table></div>{car}
  <h4>要输出的结果和合格线</h4><ul class="outs">{"".join(f"<li>{o}</li>" for o in F["out"])}</ul>
</article>'''
GUIDE = [
 ("1 先画骨架草图", f'在 x–z 平面画一张布局草图：两根导轨线、丝杠轴线、B 点、床的外形。数值全部抄 CAD 尺寸表第 03 项。导轨和竖直成 {D["rail1"]["angle_from_vertical_deg"]}°，两根相距 150。'),
 ("2 分四个子装配", "① 机架：H1 侧板、H2 内壁、H3 围板、B1 底座、B4/B5 扶手、D1 导轨、D2 丝杠和支撑、L3 B 支座。② 滑块座：C1 滑块板 + J3 轴承座筒（一个焊件）、C2 滑块 ×4、螺母座。③ 座板：S4 底板、S6 支臂、S7 横梁、S8 节点板、J1 轴、J4 摆臂、坐垫外形。④ 连杆：L1 + 两个 L2 杆端。"),
 ("3 配合（关键）", "②–①：滑块底面贴导轨面，侧面对齐，只剩沿导轨移动。③–②：J1 轴和 J3 孔同轴，加一个 y 向距离；只剩绕 y 转动。④：一端杆端孔和 J4 的铰点 2 销同轴，另一端和 L3 的 B 销同轴。机构应只剩 1 个自由度。"),
 ("4 用运动算例验证", f'在 ② 上加线性马达，沿导轨走 0 → {mm(D["screw"]["stroke"])} mm。导出座面中心 Q 的位置和座板倾角，和 CAD 尺寸表第 06 项的行程表对比：误差应 < 1 mm、0.1°。对不上，通常是铰点位置或连杆长抄错了。'),
 ("5 干涉和间隙", "在 6 个关键位置做干涉检查；量座板、横梁、轴承座筒离床 ≥ 15 mm，座板侧缘到内壁 30 mm。机构箱离床手算 12 mm，在铰点 2 杆端那里，CAD 里看能不能做到 15。"),
 ("6 交给 FEA 前的简化", "坐垫、面料、螺栓、倒角都去掉；轴承、滑块、杆端用简化外形；焊件合并成一个实体。保留焊缝根部和窗口角的真实几何。")]
GLOBAL = [("材料", "S355：E 210 GPa，ν 0.3，屈服 355 MPa；6061-T6：E 69 GPa，屈服 240 MPa；42CrMo4 调质：屈服 ≥ 650 MPa。"),
          ("载荷已含 1.5", "下面所有载荷都已经是“100 kg × 1.5”的设计载荷；不要再乘。疲劳校核用名义载荷（除以 1.5）。"),
          ("合格线", "设计载荷下 Mises ≤ 屈服 / 1.5（S355 为 237 MPa，6061-T6 为 160 MPa）；座板外缘总下沉 ≤ 5 mm（手算合计 " + f'{PT["deflection"]["total_mm"]:.1f} mm）。'),
          ("最不利位置", "多数零件在顶位（行程约 326 mm）最危险，因为座板升高后偏载的力臂最长；横梁在起点附近最危险。"),
          ("先自查支反力", "跑完先看约束反力和下面给的手算值是否接近（差 20% 以内）；差得多通常是约束建错了，不是结构问题。")]

import re as _re
strip = lambda t: _re.sub(r"<[^>]+>", "", str(t)).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
ctx = []
ctx.append("【项目】床边起身台（ME5412 小组）。人坐在床边，座板从和床垫齐平（座面高 416 mm）沿斜线升到 690 mm，先前倾（最大约 16°）再回平，把人托到接近站立。单自由度：滑块座沿两根斜导轨（与竖直 34.1°）走，丝杠驱动，连杆管座板倾角。机构全在床头一侧的机构箱里，座板是单侧悬臂，床尾一侧敞开。")
ctx.append("【坐标】原点在地面、床长边正下方；x 向床外（床在 x<0），y 沿床长指向床头（机构箱在 +y），z 向上；y=0 是座板中面；单位 mm、N。座板坐标 x_s, z_s 相对座面中心 Q，座板绕 y 前倾 φ。")
ctx.append(f'【关键尺寸】丝杠行程 {mm(D["screw"]["stroke"])}；导轨长 {mm(D["rail1"]["length"])}，两轨在导轨平面内相距 150，每轨两个滑块相距 150；连杆长 {mm(D["link"]["length"])}，B 点 {[round(1000*v) for v in D["link"]["ground_pivot_B"]]}；铰点 1 在座板坐标 {[round(v,1) for v in c1s]}，铰点 2 {[round(v,1) for v in c2s]}；y 向分层：' + "，".join(f"{k} {v}" for k, v in YS.items()))
ctx.append("【零件表】" + "；".join(f"{strip(r[1])} {strip(r[2])}：{strip(r[3])}，{strip(r[4])}，数量 {strip(r[5])}，{strip(r[6])}" for r in BS.bom))
ctx.append("【手算校核（设计载荷 100 kg×1.5，偏 10 cm，含沿座面和侧向 ±0.3 倍）】" + "；".join(" | ".join(strip(c) for c in r) for r in BS.chk))
ctx.append("【变形预算 座板外缘下沉 mm】" + "；".join(f"{strip(a)} {b}" for a, b in BS.dfl))
ctx.append("【选型】" + "；".join(f'{c["t"]}：选 {c["pick"]}。{c["why"]} 数据：' + "，".join(f"{a}={b}" for a, b in c["nums"]) + "。没选：" + "，".join(f"{a[0]}（{a[1]}）" for a in c["alt"]) for c in CARDS))
for F_ in FEA:
    ctx.append(f'【有限元重点 {F_["n"]}：{F_["t"]}（{F_["codes"]}，{F_["lvl"]}）】原因：' + " ".join(strip(w) for w in F_["why"]) + f' 建法：{F_["model"]} 约束：{F_["bc"]} 载荷：' + "；".join(" ".join(strip(c) for c in r if c) for r in F_["loads"]) +
               ("；滑块对侧板的力：" + "；".join(" ".join(r) for r in F_["car"]) if F_.get("car") else "") + " 输出和合格线：" + "；".join(strip(o) for o in F_["out"]))
ctx.append("【不用做有限元】" + "；".join(f"{a}：{b}" for a, b in NOFEA))
ctx.append("【全局规则】" + "；".join(f"{a}：{b}" for a, b in GLOBAL))
ctx.append("【建模指南】" + "；".join(f"{a}：{b}" for a, b in GUIDE))
ctx.append("【传力路径】" + "；".join(f"{t}：{d}" for _, t, d in STEPS))
ctx.append("【标准件来源】" + "；".join(" | ".join(strip(c) for c in r) for r in BS.cat))
ctx.append("【还没定】" + "；".join(strip(t) for t in BS.todo))
ctx.append(f'【质量】整机估约 {MS["device_kg"]:.0f} kg，活动件 {MS["moving_kg"]} kg；稳定性按此重算后翻倒余量变大，但人不在台上时横推 {PT["tipping"]["结论"]["min_tip_force_N"]} N 会翻，台架必须和床固定。')
DATA["ctx"] = "\n".join(ctx)
QS = ["铰点 1 为什么不用一个交叉滚子轴承？", "有限元里两个圆锥滚子轴承怎么简化？", "横梁的载荷在 SolidWorks Simulation 里怎么加？", "机构箱的竖槽会不会让箱子变太软？", "装配时怎么检查机构建对了？", "哪些数还没核实、需要查样本？"]

page = f'''<title>起身台机构与选型</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* layout: drawing-sheet look shared with the CAD sheet. Order follows how a mechanical classmate reads it: 3D first, then motion, views with balloons, the load path, modelling, FEA, choices, tables */
:root {{
  --paper:#F3F5F2; --sheet:#FFFFFF; --ink:#1A2430; --ink2:#46515E; --muted:#6B7480; --rule:#D5D9DD;
  --blue:#1E5AA8; --blue2:#A9C1E4; --red:#B3261E; --green:#2E7D4F; --amber:#9A5408; --foam:#E9B872; --foam2:#F4D9AE; --wood:#C9A36B;
  --steel:#5B6B7C; --steel2:#B8C1CB; --bed:#DCE1E7; --hl:#E0A800;
  --display:"Noto Serif SC", "Songti SC", serif; --body:"Noto Sans SC", "PingFang SC", system-ui, sans-serif; --mono:"IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper:#12171D; --sheet:#1A2129; --ink:#E6EAEE; --ink2:#B9C2CC; --muted:#8B95A0; --rule:#2E3741;
  --blue:#7FAEEA; --blue2:#3D5F8C; --red:#F08A80; --green:#7CC79A; --amber:#E0A458; --foam:#B98A45; --foam2:#7A6440; --wood:#8E7350;
  --steel:#9AA9B8; --steel2:#56636F; --bed:#2A323B; --hl:#E8C547; color-scheme:dark }} }}
:root[data-theme="dark"] {{
  --paper:#12171D; --sheet:#1A2129; --ink:#E6EAEE; --ink2:#B9C2CC; --muted:#8B95A0; --rule:#2E3741;
  --blue:#7FAEEA; --blue2:#3D5F8C; --red:#F08A80; --green:#7CC79A; --amber:#E0A458; --foam:#B98A45; --foam2:#7A6440; --wood:#8E7350;
  --steel:#9AA9B8; --steel2:#56636F; --bed:#2A323B; --hl:#E8C547; color-scheme:dark }}
body {{ background:var(--paper); color:var(--ink); font-family:var(--body); font-size:15px; line-height:1.6 }}
.wrap {{ max-width:1200px; margin:0 auto; padding-block:26px 56px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); display:flex; flex-direction:column; gap:22px }}
.tb {{ background:var(--sheet); border:1.5px solid var(--ink); display:grid; grid-template-columns:1fr auto }}
.tb .name {{ padding:18px 22px; border-right:1.5px solid var(--ink); min-width:0; display:flex; flex-direction:column; gap:8px }}
h1 {{ font-family:var(--display); font-size:30px; margin:0; text-wrap:balance }}
.tb p {{ color:var(--ink2); margin:0; max-width:72ch }}
.meta {{ display:grid; grid-template-columns:auto auto; font-size:13px; align-content:start }}
.meta div {{ padding:6px 14px; border-bottom:1px solid var(--rule) }} .meta div:nth-child(odd) {{ color:var(--muted) }} .meta div:nth-child(even) {{ font-family:var(--mono) }}
@media (max-width:720px) {{ .tb {{ grid-template-columns:1fr }} .tb .name {{ border-right:none; border-bottom:1.5px solid var(--ink) }} }}
nav.toc {{ display:flex; flex-wrap:wrap; gap:4px 16px; font-size:13.5px }} nav.toc a {{ color:var(--blue); text-decoration:none }} nav.toc a:hover {{ text-decoration:underline }}
section {{ background:var(--sheet); border:1px solid var(--rule); padding:18px 20px; display:flex; flex-direction:column; gap:12px; min-width:0; scroll-margin-top:12px }}
h2 {{ font-family:var(--display); font-size:21px; margin:0; text-wrap:balance; display:flex; gap:10px; align-items:baseline }}
h2 .no {{ font-family:var(--mono); font-size:13px; color:var(--blue) }}
h3 {{ margin:0; font-size:17px }} h4 {{ margin:0; font-size:14.5px }}
p {{ margin:0; max-width:74ch }} .cap {{ color:var(--muted); font-size:13px }}
ul, ol {{ margin:0; padding-left:1.3em; display:grid; gap:4px; max-width:84ch }}
.key {{ border-left:3px solid var(--red); padding:10px 14px; background:color-mix(in srgb, var(--red) 6%, var(--sheet)) }}
.btn {{ font:inherit; font-size:13px; color:var(--sheet); background:var(--ink); border:1px solid var(--ink); padding:5px 14px; cursor:pointer }}
.btn.ghost {{ color:var(--blue); background:transparent; border-color:var(--blue) }}
button:focus-visible, input:focus-visible, a:focus-visible {{ outline:2px solid var(--blue); outline-offset:2px }}
.ctl {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap }}
input[type=range] {{ width:100%; accent-color:var(--red) }}
.seg {{ display:inline-flex; border:1px solid var(--blue) }}
.seg button {{ font:inherit; font-size:13px; padding:5px 14px; border:0; background:transparent; color:var(--blue); cursor:pointer }}
.seg button[aria-pressed="true"] {{ background:var(--blue); color:var(--sheet) }}
/* 3D */
.three {{ display:grid; grid-template-columns:minmax(0, 1fr) 300px; gap:18px }}
@media (max-width:900px) {{ .three {{ grid-template-columns:1fr }} }}
#v3 {{ position:relative; border:1px solid var(--rule); aspect-ratio:4 / 3; max-width:100%; background:var(--sheet); touch-action:none }}
#v3 canvas {{ display:block; width:100% !important; height:100% !important }}
#v3 .hint {{ position:absolute; left:10px; bottom:8px; font-size:12px; color:var(--muted); pointer-events:none }}
#v3 .fail {{ position:absolute; inset:0; display:grid; place-items:center; color:var(--muted); padding:20px; text-align:center }}
.info {{ border:1.5px solid var(--ink); padding:10px 12px; min-height:84px }} .info .code {{ font-family:var(--mono); color:var(--blue); font-size:13px }} .info b {{ font-size:16px }}
.legend {{ display:flex; flex-wrap:wrap; gap:5px }}
.lg {{ font:inherit; font-family:var(--mono); font-size:12px; padding:2px 7px; border:1px solid var(--rule); background:transparent; color:var(--ink2); cursor:pointer }}
.lg.on {{ border-color:var(--hl); background:color-mix(in srgb, var(--hl) 22%, var(--sheet)); color:var(--ink) }}
/* 2D animation */
.stage {{ display:grid; grid-template-columns:minmax(0, 1fr) 300px; gap:18px; align-items:start }}
@media (max-width:900px) {{ .stage {{ grid-template-columns:1fr }} }}
.view {{ border:1px solid var(--rule); min-width:0 }} #mech {{ display:block; width:100%; height:auto }}
.panel {{ display:flex; flex-direction:column; gap:14px; min-width:0 }}
.read {{ display:grid; grid-template-columns:1fr 1fr; border-top:1.5px solid var(--ink) }}
.read div {{ padding:7px 2px; border-bottom:1px solid var(--rule); display:flex; flex-direction:column }}
.read span {{ font-size:12px; color:var(--muted) }} .read b {{ font-family:var(--mono); font-size:19px; font-weight:500; font-variant-numeric:tabular-nums }}
.spark {{ display:block; width:100%; height:auto }}
.dof {{ font-size:13.5px; color:var(--ink2); border-left:3px solid var(--blue); padding:6px 10px; background:color-mix(in srgb, var(--blue) 6%, var(--sheet)) }} .dof code {{ font-family:var(--mono) }}
/* figures */
.views {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(420px, 1fr)); gap:16px }}
@media (max-width:480px) {{ .views {{ grid-template-columns:1fr }} }}
.views figure {{ margin:0; display:flex; flex-direction:column; gap:6px; min-width:0 }}
.figbox {{ border:1px solid var(--rule); overflow-x:auto }}
svg.fig {{ display:block; width:100%; height:auto; min-width:360px }}
#sec {{ min-width:560px }}
figcaption {{ font-size:13px; color:var(--muted) }}
svg text {{ font-family:var(--body) }}
svg .lab {{ fill:var(--ink); font-size:15px }} svg.fs .lab {{ font-size:9.5px }} svg.fl .lab {{ font-size:30px }} svg .muted {{ fill:var(--muted) }} svg .tick {{ fill:var(--muted); font:12px var(--mono) }} svg .grid {{ stroke:var(--rule); stroke-width:1 }}
svg .bed {{ fill:var(--bed) }} svg .floor {{ stroke:var(--ink); stroke-width:2 }} svg .hatl {{ stroke:var(--muted); stroke-width:1.2 }}
svg .house {{ fill:var(--blue2); fill-opacity:.18; stroke:var(--blue); stroke-width:1.6; stroke-dasharray:7 4 }}
svg .rail {{ stroke:var(--ink); stroke-width:9; opacity:.85 }} svg .railt {{ fill:var(--ink); fill-opacity:.6 }} svg .screw {{ stroke:var(--red); stroke-width:2.2; stroke-dasharray:10 4 3 4 }}
svg .motor {{ fill:var(--ink2) }} svg .base {{ fill:var(--steel) }} svg .baseo {{ fill:var(--steel); fill-opacity:.55 }} svg .paper {{ fill:var(--sheet) }} svg .footp {{ fill:var(--steel2) }}
svg .post {{ stroke:var(--steel); stroke-width:12 }} svg .barc {{ fill:var(--ink) }}
svg .plate {{ fill:var(--blue2); stroke:var(--blue); stroke-width:1.5 }} svg .carr {{ fill:var(--blue); opacity:.75 }} svg .cartc {{ fill:var(--red); fill-opacity:.3; stroke:var(--red); stroke-width:2 }}
svg .nut, svg .shaft {{ fill:var(--ink2) }} svg .foamr {{ fill:var(--foam) }} svg .foamf {{ fill:var(--foam2) }} svg .board {{ fill:var(--wood) }} svg .arm, svg .beam {{ fill:var(--steel) }}
svg .beamd {{ fill:var(--steel); fill-opacity:.35; stroke:var(--steel); stroke-dasharray:5 3 }}
svg .armc2 {{ stroke:var(--steel); stroke-width:22; stroke-linecap:round; opacity:.85 }} svg .linkp {{ stroke:var(--ink2); stroke-width:16; stroke-linecap:round }}
svg .rodp {{ fill:var(--sheet); stroke:var(--ink2); stroke-width:3 }} svg .ghost {{ opacity:.22 }}
svg .axisl {{ stroke:var(--red); stroke-width:1.2; stroke-dasharray:10 3 2 3 }}
svg .scell {{ fill:var(--blue) }} svg .sbrg {{ fill:var(--sheet); stroke:var(--ink); stroke-width:1 }} svg .sbrgx {{ stroke:var(--ink); stroke-width:1 }}
svg .swall {{ fill:var(--muted) }} svg .sback {{ fill:var(--steel2) }} svg .brush {{ stroke:var(--ink); stroke-width:2.2; stroke-dasharray:1 2 }}
svg .bal .ldr {{ stroke:var(--ink); stroke-width:1 }} svg .bal .ldot {{ fill:var(--ink) }} svg .bal .bc {{ fill:var(--sheet); stroke:var(--ink); stroke-width:1.6 }}
svg .bal .bt {{ fill:var(--ink); font:600 13px var(--mono) }} svg .bal {{ cursor:pointer }}
svg .bal.on .bc {{ fill:var(--hl); stroke:var(--ink) }}
svg .fixl {{ stroke:var(--ink); stroke-width:2.5 }} svg .fixh {{ stroke:var(--ink); stroke-width:1.2 }}
svg .farr {{ stroke:var(--red); stroke-width:3 }} svg .fah {{ fill:var(--red) }} svg .marc {{ fill:none; stroke:var(--red); stroke-width:2.5 }}
svg .weld {{ fill:var(--amber) }} svg .hot {{ stroke:var(--hl); stroke-width:3 }} svg .dim {{ opacity:.45 }} svg .defl {{ fill:none; stroke:var(--red); stroke-width:2; stroke-dasharray:6 4 }}
svg .dimln {{ stroke:var(--ink); stroke-width:1.2 }} svg .slot {{ fill:var(--sheet); stroke:var(--ink); stroke-width:1.5; stroke-dasharray:4 3 }}
svg .oop {{ fill:var(--sheet); stroke:var(--red); stroke-width:2.5 }} svg .oopd {{ fill:var(--red) }}
svg .kseat {{ fill:var(--foam2); fill-opacity:.6; stroke:var(--ink); stroke-width:2.4; stroke-linejoin:round }} svg .kplate {{ stroke:var(--ink); stroke-width:9; stroke-linecap:round }}
svg .kslider {{ fill:var(--blue2); stroke:var(--blue); stroke-width:2.4 }} svg .klink {{ stroke:var(--steel); stroke-width:6; stroke-linecap:round }} svg .kline {{ stroke:var(--ink); stroke-width:4 }}
svg .kj {{ fill:var(--sheet); stroke:var(--red); stroke-width:3 }} svg .kg {{ fill:none; stroke:var(--ink); stroke-width:2 }}
svg .trace {{ fill:none; stroke:var(--blue); stroke-width:2; stroke-dasharray:6 5 }} svg .qdot {{ fill:var(--blue) }} svg .kload {{ stroke:var(--red); stroke-width:3.5 }} svg .arrh {{ fill:var(--red) }}
svg .kl {{ fill:var(--ink); font-size:18px; font-weight:500 }} svg .kl2 {{ fill:var(--red); font-size:16px; font-family:var(--mono) }} svg .kcode {{ fill:var(--blue); font:600 15px var(--mono) }}
svg .sline {{ fill:none; stroke-width:2 }} svg .s1 {{ stroke:var(--blue) }} svg .s2 {{ stroke:var(--amber) }} svg .cur {{ stroke:var(--red); stroke-width:1.2 }} svg .sdot {{ fill:var(--red) }}
#sec [data-part] {{ transition:opacity .25s }} #sec.focus [data-part] {{ opacity:.15 }} #sec.focus [data-part].hl {{ opacity:1; stroke:var(--hl); stroke-width:3 }}
.secwrap {{ display:grid; grid-template-columns:minmax(0, 1.5fr) minmax(0, 1fr); gap:18px; align-items:start }}
@media (max-width:900px) {{ .secwrap {{ grid-template-columns:1fr }} }}
.steps {{ list-style:none; padding:0; display:flex; flex-direction:column; gap:6px }}
.step {{ font:inherit; font-size:14px; text-align:left; width:100%; display:grid; grid-template-columns:28px 1fr; gap:10px; padding:8px 10px; background:transparent; color:var(--ink); border:1px solid var(--rule); cursor:pointer }}
.step b {{ font-weight:500 }} .step[aria-pressed="true"] {{ border-color:var(--ink); background:color-mix(in srgb, var(--hl) 16%, var(--sheet)) }}
.sn {{ font-family:var(--mono); width:24px; height:24px; border-radius:50%; background:var(--red); color:var(--sheet); display:grid; place-items:center; font-size:12px }}
/* guide + FEA */
.guide {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px }}
.guide div {{ border-top:2px solid var(--ink); padding-top:8px; display:flex; flex-direction:column; gap:4px; min-width:0 }} .guide div p {{ font-size:14px; color:var(--ink2) }}
.glob {{ display:grid; grid-template-columns:150px 1fr; border-top:1.5px solid var(--ink) }}
.glob div {{ padding:7px 8px; border-bottom:1px solid var(--rule); font-size:14px }} .glob div:nth-child(odd) {{ font-weight:500 }}
@media (max-width:560px) {{ .glob {{ grid-template-columns:1fr }} .glob div:nth-child(odd) {{ border-bottom:none; padding-bottom:0 }} }}
.fea {{ border:1px solid var(--rule); padding:14px 16px; display:flex; flex-direction:column; gap:10px }}
.fea:first-of-type {{ border:1.5px solid var(--red) }}
.fea header {{ display:flex; gap:12px; align-items:center }} .fea header > div {{ flex:1; min-width:0 }}
.rank {{ font-family:var(--mono); font-size:20px; width:38px; height:38px; display:grid; place-items:center; background:var(--red); color:var(--sheet); flex:none }}
.codes {{ font-family:var(--mono); font-size:12.5px; color:var(--muted) }}
.feagrid {{ display:grid; grid-template-columns:minmax(0, 1fr) minmax(0, 1.2fr); gap:16px; align-items:start }}
@media (max-width:860px) {{ .feagrid {{ grid-template-columns:1fr }} }}
.feafig {{ border:1px solid var(--rule); overflow-x:auto }} .feafig svg.fig {{ max-height:460px; min-width:0 }} .featext {{ display:flex; flex-direction:column; gap:6px; min-width:0 }} .featext p, .featext li {{ font-size:14px; color:var(--ink2) }}
table.loads td {{ font-size:13px }} table.loads td:first-child {{ font-weight:500; min-width:180px }} table.loads td:nth-child(n+3) {{ font-family:var(--mono); white-space:nowrap }}
.outs li {{ font-size:14px }}
.nofea {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:10px }} .nofea div {{ border:1px dashed var(--rule); padding:8px 10px; font-size:13.5px; color:var(--ink2) }}
/* cards + tables */
.cards {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(330px, 1fr)); gap:14px }}
@media (max-width:420px) {{ .cards {{ grid-template-columns:1fr }} }}
.card {{ border:1px solid var(--rule); padding:14px 16px; display:flex; flex-direction:column; gap:8px; min-width:0 }} .card.key {{ border:1.5px solid var(--red) }}
.card header {{ display:flex; justify-content:space-between; align-items:center }} .ct {{ font-size:12px; letter-spacing:.08em; color:var(--muted) }}
.pill {{ font-size:11px; color:var(--sheet); background:var(--red); padding:1px 8px }}
.card h3 {{ font-size:16px; line-height:1.4 }} .card p {{ font-size:14px; color:var(--ink2) }}
.nums {{ display:grid; grid-template-columns:repeat(3, 1fr); border-top:1.5px solid var(--ink); border-bottom:1px solid var(--rule) }}
.nums div {{ padding:6px 4px; display:flex; flex-direction:column; min-width:0 }} .nums span {{ font-size:11.5px; color:var(--muted) }} .nums b {{ font-family:var(--mono); font-weight:500; font-size:14px }}
.altt {{ font-size:12px !important; color:var(--muted) !important }}
.alts {{ padding:0; list-style:none; font-size:13.5px; color:var(--ink2) }} .alts li {{ padding-left:18px; position:relative }} .alts li::before {{ position:absolute; left:0; font-family:var(--mono) }}
.alts li.no::before {{ content:"✕"; color:var(--red) }} .alts li.maybe::before {{ content:"△"; color:var(--amber) }}
.chips {{ display:flex; flex-wrap:wrap; gap:6px }}
.chip {{ font:inherit; font-size:13px; padding:3px 12px; border:1px solid var(--rule); background:transparent; color:var(--ink2); cursor:pointer }} .chip.on {{ border-color:var(--ink); color:var(--ink); background:color-mix(in srgb, var(--blue) 10%, var(--sheet)) }}
.tw {{ overflow-x:auto }} table {{ border-collapse:collapse; width:100%; font-size:14px }}
th {{ text-align:left; font-weight:500; color:var(--muted); font-size:12.5px; border-bottom:1.5px solid var(--ink); padding:6px 10px; white-space:nowrap }}
td {{ border-bottom:1px solid var(--rule); padding:7px 10px; vertical-align:top }}
#bom td:first-child {{ color:var(--muted); font-size:13px; white-space:nowrap }} #bom td:nth-child(2) {{ font-family:var(--mono); color:var(--blue); font-size:13px }}
#bom tr.on td {{ background:color-mix(in srgb, var(--hl) 18%, var(--sheet)) }}
table.num td {{ font-family:var(--mono); font-size:13px; font-variant-numeric:tabular-nums }} table.num td:first-child {{ font-family:var(--body) }}
.ok {{ color:var(--green); font-weight:500 }} .bad {{ color:var(--red); font-weight:500 }}
.tip {{ position:fixed; z-index:20; max-width:300px; background:var(--sheet); border:1.5px solid var(--ink); padding:8px 10px; font-size:13px; box-shadow:0 4px 14px rgba(0,0,0,.18) }}
.tip .code {{ font-family:var(--mono); color:var(--blue) }} .tip .m {{ color:var(--ink2) }}
.qa-fab {{ position:fixed; z-index:30; right:calc(16px + env(safe-area-inset-right, 0px)); bottom:calc(16px + env(safe-area-inset-bottom, 0px)); font:inherit; font-size:14px; font-weight:500;
  display:flex; align-items:center; gap:8px; padding:10px 16px; background:var(--ink); color:var(--sheet); border:0; cursor:pointer; box-shadow:0 6px 18px rgba(0,0,0,.22) }}
.qa-fab .dot {{ width:8px; height:8px; border-radius:50%; background:var(--hl) }}
.qa-win {{ position:fixed; z-index:31; right:calc(16px + env(safe-area-inset-right, 0px)); bottom:calc(16px + env(safe-area-inset-bottom, 0px));
  width:min(400px, calc(100vw - 32px)); height:min(560px, calc(100vh - 32px - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px)));
  display:flex; flex-direction:column; background:var(--sheet); border:1.5px solid var(--ink); box-shadow:0 10px 30px rgba(0,0,0,.25) }}
.qa-win[hidden] {{ display:none !important }}
.qa-win header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:8px; padding:10px 12px; border-bottom:1px solid var(--rule) }}
.qa-win header b {{ font-family:var(--display); font-size:16px }}
.qa-x {{ font:inherit; font-size:16px; width:32px; height:32px; border:1px solid var(--rule); background:transparent; color:var(--ink); cursor:pointer; flex:none }}
.qa-body {{ flex:1; min-height:0; overflow-y:auto; padding:10px 12px; display:flex; flex-direction:column; gap:10px }}
.qs-row {{ display:flex; flex-wrap:wrap; gap:6px }}
.qs {{ font:inherit; font-size:12.5px; text-align:left; padding:4px 10px; border:1px solid var(--blue); background:transparent; color:var(--blue); cursor:pointer }} .qs:disabled, .btn:disabled {{ opacity:.45; cursor:default }}
.qa-log {{ display:flex; flex-direction:column; gap:8px }} .qa-log:empty {{ display:none }}
.msg {{ max-width:100%; padding:8px 11px; font-size:14px; line-height:1.6 }} .msg p {{ margin:0 0 6px }} .msg ul {{ margin:0 0 6px }}
.msg.you {{ align-self:flex-end; max-width:88%; background:color-mix(in srgb, var(--blue) 12%, var(--sheet)); border:1px solid var(--blue2) }}
.msg.ai {{ align-self:stretch; border:1px solid var(--rule); border-left:3px solid var(--ink) }}
.msg code {{ font-family:var(--mono); font-size:12.5px }}
.pc {{ font:600 12px var(--mono); color:var(--blue); background:transparent; border:1px solid var(--blue2); padding:0 4px; cursor:pointer }}
.qa-in {{ display:flex; flex-direction:column; gap:6px; padding:10px 12px; border-top:1px solid var(--rule) }}
.sr {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0) }}
textarea {{ font:inherit; font-size:14px; width:100%; box-sizing:border-box; padding:7px 9px; border:1px solid var(--rule); background:var(--paper); color:var(--ink); resize:none }}
textarea:focus-visible {{ outline:2px solid var(--blue); outline-offset:1px }}
.two {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:18px }} .two > div {{ min-width:0; display:flex; flex-direction:column; gap:8px }}
</style>
{MF.DEFS}
<div class="wrap">
<header class="tb">
  <div class="name"><h1>起身台机构与选型</h1>
  <p>人坐在床边，座板从和床垫齐平的位置沿一条斜线升起、先前倾再回平，把人托到接近站立。整套机构都放在床头一侧的一个箱子里，座板像一块从箱子伸出来的悬臂，床尾一侧完全敞开，让腿能放下来。</p>
  <p>这一页写给建模（角色 3）和有限元（角色 4）的同学：先用 3D 和三视图看懂零件，再看每个零件为什么这样选，最后是要重点分析的 4 个地方。</p>
  <nav class="toc" aria-label="目录"><a href="#s1">1 看懂结构</a><a href="#s2">2 怎么动</a><a href="#s3">3 三视图和编号</a><a href="#s4">4 偏载怎么传</a><a href="#s5">5 建模指南</a><a href="#s6">6 有限元重点</a><a href="#s7">7 选型</a><a href="#s8">8 零件和材料</a><a href="#s9">9 校核</a></nav></div>
  <div class="meta"><div>版本</div><div>v5.7</div><div>行程</div><div>{mm(D["screw"]["stroke"])} mm</div><div>设计载荷</div><div>100 kg × 1.5</div><div>单位</div><div>mm、N、°</div><div>配套</div><div>CAD 尺寸表</div></div>
</header>

<section id="s1">
  <h2><span class="no">1</span>先看懂结构（可以转、可以点）</h2>
  <div class="three">
    <div id="v3"><span class="hint">拖动旋转 · 滚轮缩放 · 点零件看名字</span></div>
    <div class="panel">
      <div class="info" id="info" aria-live="polite"><span class="code">点一个零件</span><br><b>或点下面的编号</b><br><span class="cap">编号和第 8 节零件表一致</span></div>
      <div class="ctl"><button type="button" class="btn" id="p3">播放</button><button type="button" class="btn ghost" id="shell">隐藏机构箱外壳</button><button type="button" class="btn ghost" id="reset3">复位视角</button></div>
      <input type="range" id="r3d" min="0" max="{mm(D["screw"]["stroke"])}" step="1" value="0" aria-label="3D 丝杠行程">
      <div class="legend" id="legend"></div>
    </div>
  </div>
  <div class="key"><ol>
    <li><b>四个运动件：</b>滑块座（C1 板 + J3 轴承座筒 + 4 个 C2 滑块）沿两根 D1 导轨斜着走；座板（坐垫 + 横梁 S7 + 节点板 S8 + 轴 J1）通过铰点 1 挂在滑块座上，可以绕 y 轴转；连杆 L1 一头连座板上的摆臂 J4，另一头连机构箱底部的 B 点，管座板的倾角。</li>
    <li><b>驱动：</b>一根丝杠 D2 推滑块座；电机 D4 经同步带 1:3 驱动丝杠；失电制动器 D5 和离心限速器 D6 都装在丝杠上端。</li>
    <li><b>单侧悬臂：</b>座板 440 宽，只在 y = +212 这一端被托住。人坐偏时的力矩全部经过铰点 1，所以铰点 1 用两个相距 61 mm 的圆锥滚子轴承（第 4、6 节）。</li></ol></div>
</section>

<section id="s2">
  <h2><span class="no">2</span>机构怎么动（侧视，按比例）</h2>
  <div class="stage">
    <div class="view"><svg id="mech" role="img" aria-label="起身台侧视机构简图动画"></svg></div>
    <div class="panel">
      <div class="seg" role="group" aria-label="显示方式"><button type="button" id="m-kin" aria-pressed="true">机构简图</button><button type="button" id="m-part" aria-pressed="false">零件外形</button></div>
      <div class="ctl"><button type="button" class="btn" id="play">播放</button><span class="cap">拖动看任一位置</span></div>
      <input type="range" id="s" min="0" max="{mm(D["screw"]["stroke"])}" step="1" value="0" aria-label="丝杠行程">
      <div class="read"><div><span>丝杠行程</span><b id="r-s">0 mm</b></div><div><span>座面高度</span><b id="r-z">—</b></div><div><span>座面前移</span><b id="r-x">—</b></div><div><span>座板前倾</span><b id="r-p">—</b></div></div>
      <svg class="spark" id="spark" viewBox="0 0 300 150" role="img" aria-label="座面高度和前倾随丝杠行程的变化"></svg>
      <p class="dof">4 个构件：① 机架 ② 滑块座 ③ 座板 ④ 连杆。导轨 P、铰点 1（R1）、铰点 2（S2）、B（S3）共 4 个低副。<br><code>F = 3 × (4 − 1) − 2 × 4 = 1</code>：只有丝杠一个输入，座板的高度和倾角一起被确定。</p>
    </div>
  </div>
  <p class="cap">丝杠推 ② 沿导轨（与竖直 34°）上行，座板随之升高、前移；④ 另一端固定在 B，把座板拉成先前倾、到顶回平（最大约 16°）。虚线是座面中心 Q 的轨迹。床在左边，床垫面 420。</p>
</section>

<section id="s3">
  <h2><span class="no">3</span>三视图和零件编号</h2>
  <p class="cap">圆圈里是零件编号，和第 8 节零件表、第 1 节 3D 一致；点圆圈会在零件表里标出那一行。侧视按比例（实色齐平位，虚影顶位）；俯视看横向布置：座板在 y −220 … +220，机构箱在 y 250 … 358。</p>
  <div class="views">
    <figure><div class="figbox">{MF.side_view()}</div><figcaption>侧视（x–z），从床尾一侧（−y）往床头看</figcaption></figure>
    <figure><div class="figbox">{MF.top_view()}</div><figcaption>俯视（x–y）：上方是床头方向，左边是床</figcaption></figure>
  </div>
</section>

<section id="s4">
  <h2><span class="no">4</span>铰点 1：人坐偏时，力怎么传到地上</h2>
  <div class="secwrap">
    <div class="figbox">{MF.section_view()}</div>
    <div style="display:flex;flex-direction:column;gap:10px;min-width:0">
      <div class="ctl"><button type="button" class="btn" id="path-play">逐步播放</button><button type="button" class="btn ghost" id="path-all">全部显示</button></div>
      <ol class="steps">{steps}</ol>
    </div>
  </div>
  <p class="cap">剖面沿铰点 1 轴线：横向（y）按比例，竖直方向示意。两个轴承拉开 {C1["spacing_mm"]:.0f} mm、装在 Ø75 的座筒里，径向只占 Ø75，离床够远。强度够的交叉滚子轴承要 Ø120，会伸到离床 9 mm。</p>
</section>

<section id="s5">
  <h2><span class="no">5</span>建模指南（角色 3）</h2>
  <div class="guide">{"".join(f"<div><h4>{html.escape(t)}</h4><p>{html.escape(d)}</p></div>" for t, d in GUIDE)}</div>
  <p class="cap">坐标系：原点在地面、床长边正下方；x 向床外，y 沿床长指向床头（机构箱在 +y），z 向上；y = 0 是座板中面。所有坐标和全行程表在 CAD 尺寸表里。</p>
</section>

<section id="s6">
  <h2><span class="no">6</span>有限元重点（角色 4，和角色 3 一起做）</h2>
  <p>手算已经把每个零件过了一遍（第 9 节），大多数余量足够。下面 4 处是手算靠不住、或者余量最紧的地方，按优先级排；第 1 处最先做，它的结果会影响滑块板和轴承座筒的尺寸。</p>
  <div class="glob">{"".join(f"<div>{html.escape(a)}</div><div>{html.escape(b)}</div>" for a, b in GLOBAL)}</div>
  {"".join(fea_card(F) for F in FEA)}
  <h4>不用做有限元的</h4>
  <div class="nofea">{"".join(f"<div><b>{html.escape(a)}</b><br>{html.escape(b)}</div>" for a, b in NOFEA)}</div>
</section>

<section id="s7">
  <h2><span class="no">7</span>选型：选了什么，为什么，没选的</h2>
  <div class="cards">{"".join(card(c) for c in CARDS)}</div>
  <p class="cap">✕ 不满足要求；△ 可行但不如所选。额定值来自经销商表和厂家选型器，订货前按厂家样本核对（第 9 节最后一张表）。</p>
</section>

<section id="s8">
  <h2><span class="no">8</span>零件和材料</h2>
  <div class="chips" role="group" aria-label="按部件筛选">{chips}</div>
  <div class="tw"><table id="bom"><thead><tr><th>部件</th><th>编号</th><th>零件</th><th>材料 / 型号</th><th>尺寸和位置（mm）</th><th>数量</th><th>依据</th></tr></thead><tbody>{"".join(bom_rows)}</tbody></table></div>
</section>

<section id="s9">
  <h2><span class="no">9</span>手算校核</h2>
  <p class="cap">设计载荷：100 kg × 1.5，可偏 10 cm，含沿座面和侧向 ± 0.3 倍的力，全行程最不利位置。规则：应力 ≤ 屈服 / 1.5；轴承、滑块静安全系数 ≥ 2。</p>
  {table(["零件", "工况", "计算值", "允许 / 额定", "结果"], BS.chk)}
  <div class="two">
    <div><h4>座板外缘下沉预算（mm）</h4>{table(["来源", "mm"], BS.dfl, "num")}</div>
    <div><h4>质量和重心（估算）</h4>{table(["部件", "kg", "重心 (x, y, z)"], BS.mrows, "num")}<p class="cap">稳定性原来按 45 kg 算；按约 {MS["device_kg"]:.0f} kg 重算后翻倒余量都变大，但人不在台上时横推 {PT["tipping"]["结论"]["min_tip_force_N"]} N 仍会翻，台架要和床固定。</p></div>
  </div>
  <h4>标准件额定值的来源</h4>
  {table(["型号", "用到的值", "来源", "要核的地方"], BS.cat)}
</section>
</div>
<button type="button" id="qa-fab" class="qa-fab" aria-expanded="false" aria-controls="qa-win"><span class="dot"></span>问 Claude</button>
<aside id="qa-win" class="qa-win" hidden aria-label="问 Claude">
  <header><div><b>问 Claude</b><br><span class="cap">读的是这一页的全部资料；回答里的零件编号可以点</span></div><button type="button" id="qa-min" class="qa-x" aria-label="收起问答窗">—</button></header>
  <div class="qa-body">
    <div class="qs-row" id="qa-sugg">{"".join(f'<button type="button" class="qs">{html.escape(q)}</button>' for q in QS)}</div>
    <div id="qa-log" class="qa-log" aria-live="polite"></div>
  </div>
  <div class="qa-in"><label for="qa-in" class="sr">你的问题</label><textarea id="qa-in" rows="2" placeholder="例如：滑块板为什么要 20 mm？"></textarea>
    <div class="ctl"><button type="button" class="btn" id="qa-ask">提问</button><button type="button" class="btn ghost" id="qa-stop" hidden>停止</button><span class="cap" id="qa-note"></span></div></div>
</aside>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const D = {json.dumps(DATA, ensure_ascii=False)};
{open(os.path.join(HERE, "mech_page.js"), encoding="utf-8").read()}
</script>
'''
open(os.path.join(HERE, "mechanism.html"), "w").write(page); print(len(page), "bytes")
