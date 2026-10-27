"""Rewrite the deck slides for the one-DOF seat as the main design (v5.2). Numbers come from
model/calc_v13/seat_1dof/page.json; uploaded image URLs from presentation/animations/blobs.json.
Usage: python3 update_slides_v52.py <deck_root>   (deck_root holds project/slides/*.html as read from the Slides artifact)
Only the slides listed in SLIDES are (re)written; slide ids and the deck order stay the same.
"""
import json, os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, ".."))
P = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/page.json")))
BL = json.load(open(os.path.join(HERE, "animations/blobs.json")))
OUT = os.path.join(sys.argv[1], "project/slides")
M = P["mech"]; L = P["layout"]; E = L["emergency"]; T = L["tipping"]; BAR = P["consts"]["handrail"]; F = P["check"]["design"]; VS = P["check"]["vertical_summary"]
Z = P["zoned"]; Z1 = Z["ids"]["z1"]; U0 = Z["ids"]["u"]; CT = P["check"]["cushion"].get(Z1, {}).get("summary", {})
FO = L["forces"]["载荷偏向敞开一侧 10 cm"]; nok = sum(1 for v in F.values() if v.get("release_hz") and v["fwd_slip_max_cm"] <= 2 and v["min_catch_cm"] >= 0)
Erel = st.median([v["E0_release"] for v in F.values() if v.get("E0_release") is not None])
anchor = T["固定件拉力（ADA 609 扶手设计载荷 1112 N，安全系数 1.5）"]["anchor_N"]; tipmin = T["结论"]["min_tip_force_N"]
fl = T["人站在地上推拉横杆（只有台架自重）"]
cm = lambda v: f"{100 * v:.0f}"
INK, BODY, ACC, LIGHT, PAPER, LINE = "#18202A", "#3F4A57", "#9A5408", "#F7F5F0", "#FCFBF8", "#E2DED5"
SANS = "font-family:'Noto Sans SC', Arial, sans-serif"; SERIF = "font-family:'Noto Serif SC', Georgia, serif"

def head(sec, title, size=60):
    return (f'<div style="display:flex;flex-direction:column;gap:16px">\n<p style="font-size:26px;color:{ACC};letter-spacing:2px">{sec}</p>\n'
            f'<h2 style="{SERIF};font-size:{size}px;font-weight:700;line-height:1.2">{title}</h2>\n</div>')

def img(name, alt, w, h, bg="#FBFAF6", fit="contain", extra=""):
    return f'<img src="{BL[name]}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:{fit};background:{bg};border-radius:20px;border:1px solid {LINE}{extra}">'

def todo(text):
    return (f'<div style="border:2px dashed #C98A3E;border-radius:16px;padding:20px 28px;background:#FBF3E8"><p style="font-size:26px;line-height:1.5;color:{BODY}">'
            f'<b style="color:{ACC}">待补：</b>{text}</p></div>')

def foot(text):
    return f'<p style="position:absolute;left:128px;bottom:64px;width:1664px;font-size:24px;color:#66707C">{text}</p>'

def sec(sid, bg, body, aside, pad="128px", layout="display:flex;flex-direction:column;gap:40px"):
    return (f'<section id="{sid}" data-transition="fade" style="background:{bg};color:{INK};{SANS};padding:{pad};{layout}">\n{body}\n<aside>{aside}</aside>\n</section>\n')

S = {}
S["cover"] = (f'<section id="cover" data-transition="fade" style="background:#18202A;color:#F2EFE8;{SANS};padding:128px;display:grid;grid-template-columns:1fr 640px;gap:64px;align-items:center">\n'
  f'<div style="display:flex;flex-direction:column;gap:40px">\n<p style="font-size:28px;color:#E3A24A;letter-spacing:2px">ME5412 Robotics for Healthcare · Group 16</p>\n'
  f'<h1 style="{SERIF};font-size:120px;font-weight:700;line-height:1.1;color:#F2EFE8">床边起身台</h1>\n'
  f'<p style="font-size:40px;line-height:1.45;color:#D6D2C8">帮老人夜里从床沿站起来：平时和床一样低；起身时座板跟着大腿前移、上升、前倾，把人托到床达不到的高度；速度跟着人，松手就停</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:#AEB6C0">[组员姓名] · 汇报结构草稿 · 标“待补”的部分还在做</p>\n</div>\n'
  + img("seat_step3", "示意图：老人双手握住身前横杆，座板跟着大腿前移、上升、前倾", 640, 540, extra=";border:none") +
  '\n<aside>大家好，我们是第 16 组。我们的题目是“床边起身台”：帮腿力下降的老人夜里从床沿站起来。一句话概括我们的思路：平时它和床一样低；起身时座板跟着人的大腿往前、往上走并稍微前倾，把人托到床达不到的高度；速度跟着人走，松手就停。</aside>\n</section>\n')

S["users"] = None  # small text edit, done by replace below
S["concept"] = sec("concept", LIGHT,
  head("2 · 方案", "床边起身台：一次完整的使用") + '\n<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:20px">\n' +
  "\n".join(f'<div style="display:flex;flex-direction:column;gap:16px">{img(f"seat_step{i}", a, 316, 266)}<p style="font-size:28px;line-height:1.45"><b>{i}</b> {t}</p></div>'
            for i, (a, t) in enumerate([("坐在床沿，挪上和床齐平的座板", "坐在床沿，挪上和床齐平的座板"), ("双手握住身前的横杆", "双手握住身前横杆，想坐多久都行"),
                                         ("握紧开关，座板跟着大腿走", "握紧“起”开关：座板跟着大腿前移、上升、前倾"), ("坐垫托住臀部和大腿近端", "人自己也发力，坐垫托住臀部和大腿近端"),
                                         ("站稳，座板停住", "站稳；座板停在放手时的位置，坐回也接得住")], 1)) +
  f'\n</div>\n<p style="font-size:30px;line-height:1.5;color:{BODY}">床不改造。台架靠在床的长边、和床固定；机构全部装在床头一侧的封闭箱里，床尾一侧敞开，回床时腿能转过去。L 形扶手固定在底座上，横杆在人正前方。</p>\n'
  + foot("示意图由二维模型画出（1.60 m、60 kg），不是 CAD；红色条是坐垫与身体的接触区"),
  "我们的方案叫床边起身台。它放在床的长边，床本身不改，台架和床固定。用的时候一共五步：坐在床沿，往前挪一点，坐上一块和床齐平的座板；双手握住身前横杆上的握把，想坐多久都可以；准备好了握紧“起”开关，座板不是竖直往上顶，而是跟着大腿一起往前、往上走，并且稍微前倾；人自己也在发力，坐垫托住臀部和大腿靠近臀部的那一段；站稳以后，座板停在放手时的位置，万一头晕坐回去，也接得住。机构全部装在床头一侧的一个封闭箱里，床尾一侧是空的，回床时腿可以转过去。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:44px")

S["mechanism"] = sec("mechanism", PAPER,
  head("3 · 机构", f"座板沿一条曲线前移、上升、前倾：单侧斜导轨 + 倾角连杆", 56) +
  f'\n<div style="display:grid;grid-template-columns:600px 1fr;gap:48px">\n' + img("seat_mech", "侧视示意：座板在三个高度，双导轨、滑块、倾角连杆、分区坐垫、L 形扶手", 600, 620) +
  f'\n<div style="display:flex;flex-direction:column;gap:24px">\n' + img("seat_vs_vertical", "同一位髋早前移的用户：竖直升降时往前滑、坐回落空；曲线座板跟着大腿走", 1016, 400) +
  f'\n<ul style="font-size:28px;line-height:1.5;color:{BODY}">\n'
  f'<li><b>为什么不竖直升：</b>髋早前移的人会往前滑出座面、坐回落空。81 人里，竖直升降 {VS["n_ok"]} 人合格，曲线座板 {nok} 人</li>\n'
  f'<li><b>一个电机：</b>滑块沿斜导轨走，连杆管前倾；座板前移 {100 * M["travel"]["dx"]:.1f} cm、上升 {100 * M["travel"]["dz"]:.1f} cm，前倾 ≤ {M["phi_run_max"]:.0f}°，轨迹误差 {M["centre_err_mm"]:.0f} mm</li>\n'
  f'<li>机构全装在床头一侧的封闭箱里，床尾一侧敞开</li>\n</ul>\n</div>\n</div>',
  f"接下来讲机构。我们最初的方案是座板竖直升起，但我们用二维模型模拟了 81 位不同身高、胖瘦、起身习惯和脚位的用户，发现一个问题：起身时髋会往前走，竖直升的座板跟不上，髋往前走得早的人会从座面往前滑，万一坐回去还会坐空，81 人里只有 {VS['n_ok']} 人两项都合格。所以座板要跟着大腿走：往前约 {100 * M['travel']['dx']:.0f} 厘米、往上约 {100 * M['travel']['dz']:.0f} 厘米，最多前倾 {M['phi_run_max']:.0f} 度。实现它只用一个电机：座板下一个铰点装在滑块上，沿一根斜导轨走；另一个铰点用连杆拉到底座上，管前倾角。这样走出的轨迹和我们要的曲线最多差 {M['centre_err_mm']:.0f} 毫米，81 人全部合格。整套机构装在床头一侧的封闭箱里，床尾一侧留给回床时转腿。",
  layout="display:flex;flex-direction:column;gap:36px")

S["motion"] = (f'<section id="motion" data-transition="fade" style="background:{LIGHT};color:{INK};{SANS};padding:128px;display:grid;grid-template-columns:1120px 1fr;gap:56px;align-items:center">\n'
  + img("seat_rise", "示意动画：一位 1.60 m 的用户握住横杆起身，座板沿曲线跟着大腿走，坐垫接触区随之变化，放手后座板停住", 1120, 630) +
  f'\n<div style="display:flex;flex-direction:column;gap:28px">\n<p style="font-size:26px;color:{ACC};letter-spacing:2px">3 · 运动演示</p>\n'
  f'<h2 style="{SERIF};font-size:52px;font-weight:700;line-height:1.25">关键动作和状态</h2>\n'
  f'<p style="font-size:28px;line-height:1.55;color:{BODY}">右上角是控制器状态。红色条是坐垫和臀部、大腿的接触区，颜色越深压强越高。放手后座板停在原处。</p>\n'
  f'<div style="border:2px dashed #C98A3E;border-radius:16px;padding:24px;background:#FBF3E8;display:flex;flex-direction:column;gap:10px"><p style="font-size:26px;color:{ACC}"><b>待补</b></p><p style="font-size:26px;line-height:1.5;color:{BODY}">SolidWorks 运动算例动画：滑块沿双导轨上升、连杆控制前倾、座板跟着大腿走</p></div>\n</div>\n'
  '<aside>这段示意动画由我们的二维模型直接画出：一位 1.60 米的用户双手握住身前横杆起身，座板沿着机构的曲线跟着大腿走。红色条是坐垫和身体的接触区，颜色越深压强越高；可以看到前半程推在臀部和大腿根部，后半程推在大腿上。放手以后，座板停在原来的位置。右上角是控制器的状态。正式版会换成 SolidWorks 的运动动画。</aside>\n</section>\n')

S["sizing"] = sec("sizing", LIGHT,
  head("3 · 驱动选型", "滚珠丝杠 + 失电制动；双导轨扛住单侧悬臂") +
  f'\n<div style="display:grid;grid-template-columns:1080px 1fr;gap:48px;align-items:center">\n' + img("seat_force", "左：丝杠推力随座面高度；右：座板前倾随座面高度，不超过 15 度", 1080, 410, bg="#FFFFFF") +
  f'\n<div style="display:flex;flex-direction:column;gap:22px">\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>丝杠：</b>起身时 ≤ {M["F_lift100_N"]} N（100 kg），猛坐静载 ≤ {M["F_hold100_N"]} N；行程 {M["stroke"] * 1000:.0f} mm</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>双导轨、每轨两个滑块：</b>偏载悬臂 {FO["moment_Nm"]} N·m，每个滑块约 {FO["per_carriage_lateral_N"] / 1000:.1f} kN</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>应急下降：</b>拉握把旁的拨杆，制动松开，离心限速约 {E["limiter_speed_mps"] * 100:.0f} cm/s，松手即停</p>\n</div>\n</div>\n'
  + todo("按厂家样本选定滚珠丝杠、直线导轨和制动器型号；核对 3 cm/s 时的电机转速和扭矩") + "\n"
  + foot("载荷：起身按座板推 0.5 倍体重 + 座板 10 kg；静载按 100 kg × 1.5 倍体重，载荷可在座面任意位置（虚功法）"),
  f"这是驱动的第一版选型。座板由一根滚珠丝杠推着滑块走。左图是丝杠推力：起身时最多约 {M['F_lift100_N']} 牛，100 公斤的人猛坐下来时约 {M['F_hold100_N']} 牛。右图是座板前倾，全程不超过 15 度。滚珠丝杠效率高，但不能自锁，所以加一个失电常闭制动器：平时和断电时都抱住。应急时拉握把旁边的拨杆，制动器松开，人的重量把座板慢慢压下去，离心限速器把速度限在每秒 10 厘米左右，一松手就停。机构在床头一侧，座板是悬臂，偏载时导轨要扛 {FO['moment_Nm']} 牛米的力矩，所以用两根导轨、每根两个滑块。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:36px")

tip_rows = [(k, v) for k, v in T.items() if isinstance(v, dict) and v.get("margin_rear_cm") is not None]
S["stability"] = sec("stability", PAPER,
  head("3 · 稳定性", "人在台上不会翻；人在地上扶一下会翻，所以和床固定") +
  f'\n<table style="font-size:26px;color:{BODY}">\n<tr><th style="width:52%">工况</th><th style="width:48%">结果</th></tr>\n' +
  "\n".join(f'<tr><td>{k}</td><td>离后 / 前 / 侧边缘还有 {v["margin_rear_cm"]:.0f} / {v["margin_front_cm"]:.0f} / {v["margin_side_cm"]:.0f} cm</td></tr>' for k, v in tip_rows) +
  f'\n<tr><td><b>人站在地上</b>，在横杆高度拉或推台架（台架只有自重 {T["base"]["device_kg"]:.0f} kg）</td><td><b style="color:#A2431F">{min(fl.values())} N 就翻</b>（约 {round(min(fl.values()) / 9.81)} kg 力）</td></tr>\n'
  f'<tr><td>和床固定后，固定件需要的拉力（扶手设计载荷 1112 N × 1.5）</td><td>{anchor} N</td></tr>\n</table>\n'
  + todo("用 CAD 的真实质量和质心复核；固定件的具体形式（床腿夹或床垫下压板）") + "\n"
  + foot(f"底座 x 3–78 cm、y {cm(T['base']['y'][0])} … +{cm(T['base']['y'][1])} cm；机构箱在床头一侧，台架质心偏床头一侧 {cm(T['base']['device_com'][1])} cm"),
  f"人坐上去、挪动位置时，台架会不会翻？分两种情况。第一种，人在台架上，坐在座板上或站在踏板上，这时手拉扶手是人和台架之间的内力，翻不了；表里几种最不利的情况，合力离底座边缘都还有余量。第二种是真正的危险：人不在台上，比如夜里走回床边时扶了一下横杆，这时台架只有自己大约 {T['base']['device_kg']:.0f} 公斤压着，{min(fl.values())} 牛、也就是十几公斤的力就能把它拉翻。所以台架必须和床固定，固定件按扶手的设计载荷 1112 牛、安全系数 1.5 来设计，大约需要 {anchor} 牛的拉力。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:36px")

S["risk"] = sec("risk", PAPER,
  head("4 · 安全", "最重要的六个风险和对策") +
  f'\n<div style="display:grid;grid-template-columns:1fr 600px;gap:40px;align-items:start">\n<table style="font-size:24px;color:{BODY}">\n<tr><th style="width:28%">风险</th><th style="width:72%">对策</th></tr>\n'
  f'<tr><td><b>夹手、夹腿</b></td><td>机构全封闭在床头一侧的箱里，座板支架从毛刷竖槽伸出；座板侧缘到箱壁 {cm(L["Y"]["wall_in"] - L["Y"]["seat"])} cm（大于 25 mm）</td></tr>\n'
  f'<tr><td><b>从座板滑落</b></td><td>放手时座板前倾不超过 {M["phi_run_max"]:.0f}°；高摩擦面料；压力中心偏出安全区就不抬</td></tr>\n'
  f'<tr><td><b>抬升中头晕、往回坐</b></td><td>速度自然降到 0、立即停住；座板停在原处接住人；有人坐着才慢慢降</td></tr>\n'
  f'<tr><td><b>传感器失效</b></td><td>底座四角测力，和体重对不上就锁住；开关用双通道触点</td></tr>\n'
  f'<tr><td><b>断电、卡住</b></td><td>失电制动抱住；拉握把旁的拨杆，离心限速慢慢降，松手即停；电池降</td></tr>\n'
  f'<tr><td><b>扶一下就把台架拉翻</b></td><td>台架和床固定（人不在台上时 {tipmin} N 就会翻）</td></tr>\n</table>\n'
  f'<div style="display:flex;flex-direction:column;gap:14px">{img("seat_step5", "示意：站稳后座板停在放手时的位置，坐回也接得住", 600, 500)}<p style="font-size:24px;line-height:1.5;color:#66707C">放手后座板停在原处：头晕坐回时接得住</p></div>\n</div>\n'
  + foot("[待补] 完整风险表（严重度、发生可能性、检测方式）放附录；适用标准：IEC 60601-1-11、ISO 13482、EN 12182"),
  f"这一页是我们认为最重要的六个风险。夹手夹腿：机构全部封闭在床头一侧的箱子里，只留一条带毛刷的竖槽让座板支架伸出来，座板侧边到箱壁有 {cm(L['Y']['wall_in'] - L['Y']['seat'])} 厘米，手指夹不住。从座板上滑下来：放手时座板前倾不超过 {M['phi_run_max']:.0f} 度，面料用高摩擦的，压力中心偏出安全区就不抬。抬升中头晕往回坐：速度自然降到零，座板停在原处接住人。传感器失效：底座四个角测总重量，和体重对不上就锁住。断电或卡住：制动器抱住，拉握把旁边的拨杆就能慢慢降下来。最后，人不在台上时扶一下横杆就可能把台架拉翻，所以台架和床固定。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:40px")

S["verify"] = sec("verify", LIGHT,
  head("5 · 验证", "设计要求 → 怎么验证 → 结果") +
  f'\n<table style="font-size:24px;color:{BODY}">\n<tr><th style="width:30%">设计要求</th><th style="width:24%">怎么验证</th><th style="width:32%">目前结果</th><th style="width:14%">状态</th></tr>\n'
  f'<tr><td>1 只在起身时升高，比现有办法省力</td><td>2D 起身模型</td><td>升到 0.66 m 比抬高床省 13–20%</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>1′ 座板跟着人走：不往前滑、坐回接得住</td><td>81 人 × 机构实际轨迹</td><td>{nok}/81 合格（竖直升降 {VS["n_ok"]}/81）；按坐垫压下后的位置 {CT.get("n_ok", "—")}/81</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>2 推力不超过约半个体重</td><td>速度规则 + 场景仿真</td><td>8 个场景都没有超过上限</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>3 手握 + 力分布确认后才抬；松手即停</td><td>状态机仿真</td><td>松手后立即停住</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>4 机构放得下、推得动、撑得住</td><td>尺寸、干涉、选型、FEA</td><td>机构箱离床 {L["bed_floor_cm"]["机构箱（导轨、滑块、电机、连杆）"]} cm；[待补] FEA</td><td><b style="color:{ACC}">进行中</b></td></tr>\n'
  f'<tr><td>5 人坐上、挪动、坐回时不翻</td><td>合重心和倾翻计算</td><td>人在台上余量足；人在地上要和床固定；[待补] 真实质量复核</td><td><b style="color:{ACC}">进行中</b></td></tr>\n'
  f'<tr><td>6 有人坐着才降；离座后停住接人</td><td>状态机仿真</td><td>坐回、断电场景都落到安全状态</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n</table>\n'
  + foot("本项目只做概念、设计和仿真，不做实物和人体实验；“初步完成”指已有第一版计算或仿真结果"),
  f"这张表把设计要求和验证方法一一对上。新增的一行是座板要跟着人走：我们用机构实际走出的轨迹重跑了 81 位用户，{nok} 人都不往前滑、坐回接得住，竖直升降只有 {VS['n_ok']} 人；把坐垫压下去以后的座板位置也算了一遍，{CT.get('n_ok', '—')} 人合格。推力上限、松手即停和有人坐着才降，用状态机的场景仿真验证；机构的强度和台架稳定性的真实质量复核还在进行中。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:36px")

S["conclusion"] = (f'<section id="conclusion" data-transition="fade" style="background:#18202A;color:#F2EFE8;{SANS};padding:128px;display:flex;flex-direction:column;gap:48px">\n'
  f'<div style="display:flex;flex-direction:column;gap:16px">\n<p style="font-size:26px;color:#E3A24A;letter-spacing:2px">5 · 结论</p>\n'
  f'<h2 style="{SERIF};font-size:64px;font-weight:700;line-height:1.2;color:#F2EFE8">平时和床一样低，起身时跟着人升得比床高，随时可停</h2>\n</div>\n'
  f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:32px">\n'
  f'<div style="background:#232E3B;border-radius:20px;padding:40px;display:flex;flex-direction:column;gap:16px"><h3 style="font-size:34px;font-weight:700;color:#E3A24A">省力、不滑</h3><p style="font-size:30px;line-height:1.5;color:#E4E0D6">升到床达不到的高度，比抬高床再省 13–20%；座板跟着大腿走，81 人都不往前滑、坐回接得住</p></div>\n'
  f'<div style="background:#232E3B;border-radius:20px;padding:40px;display:flex;flex-direction:column;gap:16px"><h3 style="font-size:34px;font-weight:700;color:#E3A24A">做得出来</h3><p style="font-size:30px;line-height:1.5;color:#E4E0D6">一个电机：斜导轨 + 倾角连杆；机构封闭在床头一侧，床尾敞开；台架和床固定</p></div>\n'
  f'<div style="background:#232E3B;border-radius:20px;padding:40px;display:flex;flex-direction:column;gap:16px"><h3 style="font-size:34px;font-weight:700;color:#E3A24A">安全</h3><p style="font-size:30px;line-height:1.5;color:#E4E0D6">松手即停、有人坐着才降、速度跟着人走；断电时制动抱住，拉拨杆可慢慢降</p></div>\n</div>\n'
  f'<aside>总结一下。起身台平时和床一样低，起身时把座面升到床达不到的高度，比抬高床再省 13 到 20%；而且座板跟着大腿走，我们模拟的 81 位用户都不会往前滑，坐回去也接得住。机构上，一个电机带动斜导轨和倾角连杆，整套机构封闭在床头一侧，床尾一侧敞开，台架和床固定。控制上，松手即停、有人坐着才降、速度跟着人走；断电时制动器抱住，拉一下拨杆就能慢慢降下来。</aside>\n</section>\n')

S["sensing"] = sec("sensing", LIGHT,
  head("4 · 传感与交互", "手握发指令，力分布确认人准备好了") +
  f'\n<div style="display:grid;grid-template-columns:640px 1fr;gap:56px;align-items:center">\n' + img("seat_sensors", "侧视示意：1 座板测力，2 横杆测力，3 握把开关，4 踏板测力，5 底座四角测力", 640, 540) +
  f'\n<div style="display:flex;flex-direction:column;gap:20px">\n'
  f'<p style="font-size:30px;line-height:1.5"><b>1 座板下测力：</b><span style="color:{BODY}">坐上了没有、坐正了没有（压力中心）；推了多少力（速度规则）</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>2 横杆测力：</b><span style="color:{BODY}">手在不在上面</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>3 握把式“起”开关：</b><span style="color:{BODY}">握紧才升、松手就停；在人正前方的横杆上</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>4 踏板测力：</b><span style="color:{BODY}">脚踩实了没有</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>5 底座四角测力：</b><span style="color:{BODY}">总重减去台架自重应约等于体重，对不上就锁住</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>反馈：</b><span style="color:{BODY}">握把上的状态灯和踏板夜灯</span></p>\n</div>\n</div>\n'
  + foot("先例：东京大学 Kogami 等的辅助椅用座下压力中心前移判断“想起身”"),
  "交互上，我们用手握来发指令：开关做在人正前方横杆的握把上，握紧才升、松手就停。座板下的测力单元测坐上了没有、坐正了没有，也测座板推了多少力，用来控制速度。踏板下的测力单元看脚踩实了没有。座板会前倾，座板下的单向测力单元测不准竖直方向的体重，所以体重自检放到底座四个角：对地的总力减去台架自重，应该约等于体重，对不上就锁住。反馈方面，握把上有状态灯，踏板有夜灯。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:40px")

REPL = {   # small edits on slides kept as they are
 "users": [("<li>床不改造；台架和床固定；只在起身时升到约 0.66 m</li>", "<li>床不改造；台架和床固定；起身时座板跟着大腿升到约 0.69 m，人不往前滑</li>")],
 "agenda": [("升降机构、运动演示、推杆选型、稳定性", "坐板机构、运动演示、驱动选型、稳定性")],
 "prior": [("不同：推力可设上限，扶手一起升，能升到 0.66 m", "不同：推力可设上限，座板跟着大腿走，能升到 0.69 m")],
 "statemachine": [('<h3 style="font-size:34px;font-weight:700;color:#9A5408">离座后停住</h3><p style="font-size:28px;line-height:1.5;color:#3F4A57">人站起来后座板停在原高度、保持水平，坐回去也接得住</p>',
                   '<h3 style="font-size:34px;font-weight:700;color:#9A5408">离座后停住</h3><p style="font-size:28px;line-height:1.5;color:#3F4A57">座板停在放手时的位置接人；人走开、踏板空了几秒后才降回齐平</p>'),
                  ("第三，人站起来以后，座板停在原高度、保持水平，万一坐回去也接得住。", "第三，人站起来以后，座板停在放手时的位置，万一坐回去也接得住；等人走开、踏板也空了几秒，座板才降回和床齐平，这样人回来时像坐普通椅子一样坐上去。")],
 "limits": [("<li>仿真里的用户模型是简化的，只用来检验控制逻辑</li>", "<li>人体按二维刚体轮廓、坐垫按独立弹簧床算；分区坐垫和面料摩擦要样件实测</li>")],
 "appendix": [("<tr><td>现有技术和专利表</td><td>角色 1</td><td><b style=\"color:#2F7A55\">有材料</b></td></tr>",
               "<tr><td>现有技术和专利表</td><td>角色 1</td><td><b style=\"color:#2F7A55\">有材料</b></td></tr>\n<tr><td>单自由度坐板设计（81 人、机构、坐垫、干涉、两轮审计）</td><td>角色 2、3</td><td><b style=\"color:#2F7A55\">有材料</b></td></tr>")],
 "questions": [("机构做到“选型 + 尺寸估算 + CAD 运动动画”够不够？双升降柱为主、剪叉作对比可以吗？", "座板改成跟着大腿走的单自由度曲线（斜导轨 + 倾角连杆），竖直升降作对比，这个方向可以吗？做到选型 + 尺寸估算 + CAD 运动动画够不够？"),
               ("第二，机构做到选型、尺寸估算和 CAD 运动动画够不够；", "第二，座板改成跟着大腿走的曲线、竖直升降作对比，这个方向行不行，机构做到选型、尺寸估算和 CAD 运动动画够不够；")],
 "whynot": [('<p style="font-size:28px;line-height:1.5;color:#3F4A57">只升到 0.60 m 就和抬高床差不多：省力来自固定床达不到的那段高度</p>',
             f'<p style="font-size:28px;line-height:1.5;color:#3F4A57">只升到 0.60 m 就和抬高床差不多。座板还要跟着大腿走，否则人会往前滑（第 8 页）</p>')],
}

if __name__ == "__main__":
    for sid, html in S.items():
        if html: open(os.path.join(OUT, f"{sid}.html"), "w").write(html)
    for sid, pairs in REPL.items():
        p = os.path.join(OUT, f"{sid}.html"); h = open(p).read()
        for a, b in pairs:
            assert h.count(a) == 1, (sid, a[:40]); h = h.replace(a, b)
        open(p, "w").write(h)
    print("written", [k for k, v in S.items() if v] + list(REPL))
