"""Rewrite the deck slides for the one-DOF seat as the main design (v5.2). Numbers come from
model/calc_v13/seat_1dof/page.json; uploaded image URLs from presentation/animations/blobs.json.
Usage: python3 update_slides_v52.py <deck_root>   (deck_root holds project/slides/*.html as read from the Slides artifact)
Only the slides listed in SLIDES are (re)written; slide ids and the deck order stay the same.
"""
import json, os, re, sys, statistics as st
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
BB = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/bed_baseline.json"))); SLU = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/slider.json")))["users"]
K72 = [k for k, v in BB["users"].items() if v["0.58"]["handle"] is not None and SLU[k].get("E_release")]
med = lambda xs: st.median(xs)
CMP = dict(low=med([BB["users"][k]["0.42"]["L_bar"] for k in K72]), high_L=med([BB["users"][k]["0.58"]["L_bar"] for k in K72]),
           high_best=med([BB["users"][k]["0.58"]["handle"] for k in K72]), seat=med([SLU[k]["E_release"] for k in K72]))
BS = BB["summary"]; N72 = len(K72); NOFF = 81 - N72
_sv = lambda bed, k: med([1 - SLU[u]["E_release"] / BB["users"][u][bed][k] for u in K72])   # per-user saving, same 72 users
SAVE_LOW = _sv("0.42", "L_bar"); SAVE_HL = _sv("0.58", "L_bar"); SAVE_HB = _sv("0.58", "handle"); NWORSE = BS["bed0.58_handle"]["n_worse"]
PHIREL = st.median([v["phi_release"] for v in SLU.values()])
pct = lambda v: f"{100 * v:.0f}%"
N_SCEN = len(json.load(open(os.path.join(ROOT, "model/calc_v13/controller_seat.json")))["scenarios"])
pc = lambda v: f"{100 * v:.0f}"
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
  f'<p style="font-size:40px;line-height:1.45;color:#D6D2C8">帮老人夜里从床沿站起来：平时和床一样低；起身时座板跟着大腿前移、上升、前倾，一路托着人；速度跟着人，松手就停</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:#AEB6C0">[组员姓名] · 汇报结构草稿 · 标“待补”的部分还在做</p>\n</div>\n'
  + img("seat_step3", "示意图：老人双手握住身前横杆，座板跟着大腿前移、上升、前倾", 640, 540, extra=";border:none") +
  '\n<aside>大家好，我们是第 16 组。我们的题目是“床边起身台”：帮腿力下降的老人夜里从床沿站起来。一句话概括我们的思路：平时它和床一样低；起身时座板跟着人的大腿往前、往上走并稍微前倾，一路托着人；速度跟着人走，松手就停。</aside>\n</section>\n')

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
  f'<li>机构全装在床头一侧的封闭箱里，床尾一侧敞开</li>\n<li><b>为什么不用四连杆：</b>只放床头一侧的四连杆箱子小一半，但偏载靠两个相距 8 cm 的铰点扛，铰点受力约为滑块的 8 倍（附录）</li>\n</ul>\n</div>\n</div>',
  f"接下来讲机构。我们最初的方案是座板竖直升起，但我们用二维模型模拟了 81 位不同身高、胖瘦、起身习惯和脚位的用户，发现一个问题：起身时髋会往前走，竖直升的座板跟不上，髋往前走得早的人会从座面往前滑，万一坐回去还会坐空，81 人里只有 {VS['n_ok']} 人两项都合格。所以座板要跟着大腿走：往前约 {100 * M['travel']['dx']:.0f} 厘米、往上约 {100 * M['travel']['dz']:.0f} 厘米，最多前倾 {M['phi_run_max']:.0f} 度。实现它只用一个电机：座板下一个铰点装在滑块上，沿一根斜导轨走；另一个铰点用连杆拉到底座上，管前倾角。这样走出的轨迹和我们要的曲线最多差 {M['centre_err_mm']:.0f} 毫米，81 人全部合格。整套机构装在床头一侧的封闭箱里，床尾一侧留给回床时转腿。为什么不用四连杆？我们也试了只放床头一侧的四连杆，箱子能小一半，但座板挂在一侧的偏载只能靠两个相距 8 厘米的铰点扛，铰点受力大约是导轨滑块的 8 倍，推杆力也大一倍多，所以还是用导轨。",
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
  f'\n<div style="display:grid;grid-template-columns:1080px 1fr;gap:48px;align-items:center">\n' + img("seat_force", "左：丝杠推力随座面高度；右：座板前倾随座面高度，不超过 16 度", 1080, 410, bg="#FFFFFF") +
  f'\n<div style="display:flex;flex-direction:column;gap:22px">\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>丝杠：</b>起身时 ≤ {M["F_lift100_N"]} N（100 kg），猛坐静载 ≤ {M["F_hold100_N"]} N；行程 {M["stroke"] * 1000:.0f} mm</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>双导轨、每轨两个滑块：</b>偏载悬臂 {FO["moment_Nm"]} N·m，每个滑块约 {FO["per_carriage_lateral_N"] / 1000:.1f} kN</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>应急下降：</b>先用电池按住“降”；控制器也坏了，拉立柱侧带护盖的拨杆：先断电机电源再松制动，限速约 {E["limiter_speed_mps"] * 100:.0f} cm/s，松手即停</p>\n</div>\n</div>\n'
  + todo("按厂家样本选定滚珠丝杠、直线导轨和制动器型号；核对 3 cm/s 时的电机转速和扭矩") + "\n"
  + foot("载荷：起身按座板推 0.5 倍体重 + 座板 10 kg；静载按 100 kg × 1.5 倍体重，载荷可在座面任意位置（虚功法）"),
  f"这是驱动的第一版选型。座板由一根滚珠丝杠推着滑块走。左图是丝杠推力：起身时最多约 {M['F_lift100_N']} 牛，100 公斤的人猛坐下来时约 {M['F_hold100_N']} 牛。右图是座板前倾，全程不超过 16 度。滚珠丝杠效率高，但不能自锁，所以加一个失电常闭制动器：平时和断电时都抱住。断电时先用电池，按住“降”慢慢降；如果控制器也坏了，拉立柱侧面带护盖的拨杆，第一段行程先切断电机电源，再松开制动器，人的重量把座板慢慢压下去，速度限在每秒 3 厘米左右，全程大约 11 秒，一松手就停。机构在床头一侧，座板是悬臂，偏载时导轨要扛 {FO['moment_Nm']} 牛米的力矩，所以用两根导轨、每根两个滑块。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:36px")

tip_rows = [(k, v) for k, v in T.items() if isinstance(v, dict) and v.get("margin_rear_cm") is not None]
S["stability"] = sec("stability", PAPER,
  head("3 · 稳定性", "人在台上不会翻；人在地上扶一下会翻，所以和床固定") +
  f'\n<div style="display:grid;grid-template-columns:1fr 690px;gap:40px;align-items:start">\n<table style="font-size:24px;color:{BODY}">\n<tr><th style="width:55%;text-align:left">工况</th><th style="width:45%;text-align:left">结果</th></tr>\n' +
  "\n".join(f'<tr><td>{k}</td><td>离后 / 前 / 侧边缘还有 {v["margin_rear_cm"]:.0f} / {v["margin_front_cm"]:.0f} / {v["margin_side_cm"]:.0f} cm</td></tr>' for k, v in tip_rows) +
  f'\n<tr><td><b>人站在地上</b>，在横杆高度拉或推台架（台架只有自重 {T["base"]["device_kg"]:.0f} kg）</td><td><b style="color:#A2431F">{min(fl.values())} N 就翻</b>（约 {round(min(fl.values()) / 9.81)} kg 力）</td></tr>\n'
  f'<tr><td>和床固定后，固定件需要的拉力（扶手设计载荷 1112 N × 1.5）</td><td>{anchor} N</td></tr>\n</table>\n'
  + img("seat_top", "俯视示意：床、台架底座、床头一侧的机构箱、座板、L 形扶手、站起后走向床尾的路线和回床路线", 690, 495) + '\n</div>\n'
  + todo("用 CAD 的真实质量和质心复核；固定件锁在床架或床腿上（床垫下的压板拉不住 2.3 kN，不用）") + "\n"
  + foot(f"底座 x 3–78 cm、y {cm(T['base']['y'][0])} … +{cm(T['base']['y'][1])} cm；机构箱在床头一侧，台架质心偏床头一侧 {cm(T['base']['device_com'][1])} cm"),
  f"人坐上去、挪动位置时，台架会不会翻？分两种情况。第一种，人在台架上，坐在座板上或站在踏板上，这时手拉扶手是人和台架之间的内力，翻不了；表里几种最不利的情况，合力离底座边缘都还有余量。第二种是真正的危险：人不在台上，比如夜里走回床边时扶了一下横杆，这时台架只有自己大约 {T['base']['device_kg']:.0f} 公斤压着，{min(fl.values())} 牛、也就是十几公斤的力就能把它拉翻。所以台架必须和床固定，固定件按扶手的设计载荷 1112 牛、安全系数 1.5 来设计，大约需要 {anchor} 牛的拉力，所以要锁在床架或床腿上。右边是俯视图：台架沿床长占 65 厘米，机构箱在床头一侧，人站起来后转向床尾一侧走下底座，助行器放在那里。横杆露在外面的那一头做成圆头软包、带夜光，夜里不容易撞上。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:36px")

S["risk"] = sec("risk", PAPER,
  head("4 · 安全", "最重要的六个风险和对策") +
  f'\n<div style="display:grid;grid-template-columns:1fr 600px;gap:40px;align-items:start">\n<table style="font-size:24px;color:{BODY}">\n<tr><th style="width:28%">风险</th><th style="width:72%">对策</th></tr>\n'
  f'<tr><td><b>夹手、夹腿</b></td><td>机构全封闭，支架从毛刷竖槽伸出；座板侧缘到箱壁 {cm(L["Y"]["wall_in"] - L["Y"]["seat"])} cm；座板后缘软包，下降遇阻（电机电流升高）即停</td></tr>\n'
  f'<tr><td><b>从座板滑落</b></td><td>全程前倾不超过 16°（最大 {M["phi_run_max"]:.1f}°）；高摩擦面料；压力中心偏出安全区就不抬</td></tr>\n'
  f'<tr><td><b>抬升中头晕、往回坐</b></td><td>速度降到 0、停住接人；只有按住“降”才降；久坐不动只提醒、呼叫家属</td></tr>\n'
  f'<tr><td><b>传感器失效</b></td><td>空载查零点；抬升中三处力之和与体重差 >15% 就锁住；开关用双通道触点</td></tr>\n'
  f'<tr><td><b>断电、卡住</b></td><td>失电制动抱住；电池按住“降”；控制器坏了拉带护盖的拨杆（先断电机），限速 3 cm/s</td></tr>\n'
  f'<tr><td><b>扶一下就把台架拉翻</b></td><td>台架和床固定（人不在台上时 {tipmin} N 就会翻）；横杆末端圆头软包、夜光</td></tr>\n</table>\n'
  f'<div style="display:flex;flex-direction:column;gap:14px">{img("seat_step5", "示意：站稳后座板停在放手时的位置，坐回也接得住", 600, 500)}<p style="font-size:24px;line-height:1.5;color:#66707C">放手后座板停在原处：头晕坐回时接得住</p></div>\n</div>\n'
  + foot("[待补] 完整风险表（严重度、发生可能性、检测方式）放附录；适用标准：IEC 60601-1-11、ISO 13482、EN 12182"),
  f"这一页是我们认为最重要的六个风险。夹手夹腿：机构全部封闭在床头一侧的箱子里，只留一条带毛刷的竖槽让座板支架伸出来，座板侧边到箱壁有 {cm(L['Y']['wall_in'] - L['Y']['seat'])} 厘米，手指夹不住。从座板上滑下来：全程前倾不超过 16 度，面料用高摩擦的，压力中心偏出安全区就不抬。抬升中头晕往回坐：速度降到零，座板停在原处接住人；只有按住“降”才会往下，久坐不动只提醒、呼叫家属。传感器失效：空着时查零点，抬升中三处力之和和体重对不上就锁住。断电或卡住：制动器抱住，先用电池按住“降”；控制器也坏了，拉带护盖的拨杆，先断电机，再慢慢降。最后，人不在台上时扶一下横杆就可能把台架拉翻，所以台架和床固定。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:40px")

S["verify"] = sec("verify", LIGHT,
  head("5 · 验证", "设计要求 → 怎么验证 → 结果") +
  f'\n<table style="font-size:24px;color:{BODY}">\n<tr><th style="width:30%">设计要求</th><th style="width:24%">怎么验证</th><th style="width:32%">目前结果</th><th style="width:14%">状态</th></tr>\n'
  f'<tr><td>1a 床不用垫高，起身省力达到抬高床的水平</td><td>2D 起身模型，同一扶手、同一批用户</td><td>比低床省 {pct(SAVE_LOW)}；和抬高床相当（中位 {CMP["seat"]:.2f} vs {CMP["high_best"]:.2f}）</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>1b 座板跟着人走：不往前滑、坐回接得住</td><td>81 人 × 机构实际轨迹</td><td>{nok}/81 合格（竖直升降 {VS["n_ok"]}/81）；按坐垫压下后的位置 {CT.get("n_ok", "—")}/81；腿一软全程接得住 81/81</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>2 推力不超过约半个体重</td><td>速度规则 + 场景仿真</td><td>坐板版 {N_SCEN} 个场景都没有超过上限</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>3 手握 + 力分布确认后才抬；松手即停</td><td>状态机仿真</td><td>松手后立即停住</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>4 机构放得下、推得动、撑得住</td><td>尺寸、干涉、选型、FEA</td><td>机构箱离床 {L["bed_floor_cm"]["机构箱（导轨、滑块、电机、连杆）"]} cm；[待补] FEA</td><td><b style="color:{ACC}">进行中</b></td></tr>\n'
  f'<tr><td>5 人坐上、挪动、坐回时不翻</td><td>合重心和倾翻计算</td><td>人在台上余量足；人在地上要和床固定；[待补] 真实质量复核</td><td><b style="color:{ACC}">进行中</b></td></tr>\n'
  f'<tr><td>6 有人坐着才降；离座后停住接人</td><td>状态机仿真</td><td>坐回、断电场景都落到安全状态</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n</table>\n'
  + foot("本项目只做概念、设计和仿真，不做实物和人体实验；“初步完成”指已有第一版计算或仿真结果"),
  f"这张表把设计要求和验证方法一一对上。第一条要求我们写成两项：一是床不用垫高，起身省力达到抬高床的水平，结果是比低床省约 {pct(SAVE_LOW)}、和抬高床相当；二是座板要跟着人走：我们用机构实际走出的轨迹重跑了 81 位用户，{nok} 人都不往前滑、坐回接得住，竖直升降只有 {VS['n_ok']} 人；把坐垫压下去以后的座板位置也算了一遍，{CT.get('n_ok', '—')} 人合格。推力上限、松手即停和有人坐着才降，用状态机的场景仿真验证；机构的强度和台架稳定性的真实质量复核还在进行中。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:36px")

S["conclusion"] = (f'<section id="conclusion" data-transition="fade" style="background:#18202A;color:#F2EFE8;{SANS};padding:128px;display:flex;flex-direction:column;gap:48px">\n'
  f'<div style="display:flex;flex-direction:column;gap:16px">\n<p style="font-size:26px;color:#E3A24A;letter-spacing:2px">5 · 结论</p>\n'
  f'<h2 style="{SERIF};font-size:64px;font-weight:700;line-height:1.2;color:#F2EFE8">平时和床一样低，起身时跟着大腿托一程，随时可停</h2>\n</div>\n'
  f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:32px">\n'
  f'<div style="background:#232E3B;border-radius:20px;padding:40px;display:flex;flex-direction:column;gap:16px"><h3 style="font-size:34px;font-weight:700;color:#E3A24A">省力、接得住</h3><p style="font-size:30px;line-height:1.5;color:#E4E0D6">床不用垫高，省力达到抬高床；起身全程腿一软都接得住（81/81，床只在刚起身时接得住）</p></div>\n'
  f'<div style="background:#232E3B;border-radius:20px;padding:40px;display:flex;flex-direction:column;gap:16px"><h3 style="font-size:34px;font-weight:700;color:#E3A24A">做得出来</h3><p style="font-size:30px;line-height:1.5;color:#E4E0D6">一个电机：斜导轨 + 倾角连杆；机构封闭在床头一侧，床尾敞开；台架和床固定</p></div>\n'
  f'<div style="background:#232E3B;border-radius:20px;padding:40px;display:flex;flex-direction:column;gap:16px"><h3 style="font-size:34px;font-weight:700;color:#E3A24A">安全</h3><p style="font-size:30px;line-height:1.5;color:#E4E0D6">松手即停、有人坐着才降、速度跟着人走；断电时制动抱住，拉拨杆可慢慢降</p></div>\n</div>\n'
  f'<aside>总结一下。起身台平时和床一样低，起身时座板跟着大腿托一程。按同一个模型，它比从低床起身省约 {pct(SAVE_LOW)}；和把床垫高到 0.58 米相比只多省 {pct(SAVE_HB)} 到 {pct(SAVE_HL)}，好处主要是平时坐得低、脚踩得实，而且座板跟着大腿走，我们模拟的 81 位用户都不会往前滑，坐回去也接得住。机构上，一个电机带动斜导轨和倾角连杆，整套机构封闭在床头一侧，床尾一侧敞开，台架和床固定。控制上，松手即停、有人坐着才降、速度跟着人走；断电时制动器抱住，拉一下拨杆就能慢慢降下来。</aside>\n</section>\n')

def _bar(label, v, col, bold=False, note=""):
    w = round(600 * v / 0.45)
    return (f'<p style="font-size:28px;color:{INK if bold else BODY}">{"<b>" + label + "</b>" if bold else label}</p>'
            f'<div style="display:flex;align-items:center;gap:16px"><div style="height:40px;width:{w}px;background:{col};border-radius:0 6px 6px 0"></div>'
            f'<p style="font-size:28px;font-weight:700">{v:.2f}</p><p style="font-size:22px;color:#66707C">{note}</p></div>')
S["whynot"] = sec("whynot", PAPER,
  head("2 · 方案比较", f"比低床省约 {pct(SAVE_LOW)}；比抬高床只多省 {pc(SAVE_HB)}–{pct(SAVE_HL)}，好处在别处", 56) +
  f'\n<div style="display:grid;grid-template-columns:1060px 1fr;gap:56px;align-items:start">\n<div style="display:flex;flex-direction:column;gap:18px">\n'
  f'<p style="font-size:26px;color:#66707C">起身最吃力那一刻的 effort，中位数（越低越轻松；同一模型、同一批 {N72} 位用户）</p>\n'
  f'<div style="display:grid;grid-template-columns:360px 1fr;gap:18px 20px;align-items:center">\n'
  + _bar("低床 0.42 m + L 扶手", CMP["low"], "#C3C9D1") + "\n"
  + _bar("抬高床 0.58 m + L 扶手", CMP["high_L"], "#9AA3AD") + "\n"
  + _bar("抬高床 0.58 m + 最佳扶手", CMP["high_best"], "#7D8792") + "\n"
  + _bar("起身台：坐板放手那一刻", CMP["seat"], "#B4620A", bold=True) +
  f'\n</div>\n<p style="font-size:24px;line-height:1.5;color:{BODY}">另有 {NOFF} 位用户（1.50 m、臀部厚）坐在 0.58 m 的床上脚踩不实，没法比；起身台平时 0.42 m，81 人都踩得实</p>\n</div>\n'
  f'<div style="display:flex;flex-direction:column;gap:26px">\n'
  f'<p style="font-size:30px;line-height:1.45"><b>比低床：</b>每个人都省，中位数省 {pct(SAVE_LOW)}</p>\n'
  f'<p style="font-size:30px;line-height:1.45"><b>比抬高床：</b>只省 {pc(SAVE_HB)}–{pct(SAVE_HL)}；{N72} 人里 {NWORSE} 人反而略费力</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>原因：</b>多数人在座板前倾最大（约 {PHIREL:.0f}°）时就离开坐垫，那时髋只比坐在 0.58 m 床上高约 4 cm；导轨上段没用来托人</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{ACC}"><b>所以它的价值是：</b>平时坐得低、脚踩得实；起身全程有托、不往前滑、坐回接得住（第 8 页）</p>\n</div>\n</div>\n'
  + foot("effort = 最吃力的关节用掉自身最大力量的比例（2D 准静态模型，手上最多出半个体重）。抬高床按最有利的坐姿（臀部离床沿 0–10 cm）和 35 个扶手位置里最好的算。旧版此页的 13–20% 来自竖直升到 0.66 m 的旧模型，已作废"),
  f"接下来比较几种起身方式。我们用同一个二维、准静态的起身模型、同一副 L 形扶手和同一批用户，算最吃力那一刻最吃力的关节用掉了自身最大力量的几成，叫 effort，越低越轻松。从 0.42 米的低床起身，中位数是 {CMP['low']:.2f}；把床垫高到 0.58 米，降到 {CMP['high_L']:.2f}，扶手放到最有利的位置是 {CMP['high_best']:.2f}；起身台在座板放手那一刻是 {CMP['seat']:.2f}。所以和低床比，起身台每个人都省，中位数省 {pct(SAVE_LOW)}；但和抬高床比只多省 {pct(SAVE_HB)} 到 {pct(SAVE_HL)}，有 {NWORSE} 个人反而略费力。原因是多数人在座板前倾最大、大约 {PHIREL:.0f} 度时就离开了坐垫，那时髋部只比坐在 0.58 米的床上高约 4 厘米。我们之前的版本写比抬高床省 13 到 20%，那是竖直升降旧模型的数字，这次按同一口径重算后不成立，我们改掉了。起身台相对抬高床的好处主要在别处：平时和床一样低，脚踩得实，0.58 米的床有 {NOFF} 位个子矮的用户脚踩不实；起身全程有托，不往前滑，坐回去也接得住。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:40px")

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
 "users": [("<li>床不改造；台架和床固定；起身时座板跟着大腿升到约 0.69 m，人不往前滑</li>", "<li>床保持低位、脚踩得实；起身省力达到抬高床的水平；座板跟着大腿走，人不往前滑</li>"),
           ("设计工况 60 kg、1.60 m。", "起身模型以 60 kg、1.60 m 为基准；结构按 100 kg × 1.5 校核。")],
 "agenda": [("升降机构、运动演示、推杆选型、稳定性", "坐板机构、运动演示、驱动选型、稳定性")],
 "prior": [("不同：推力可设上限，扶手一起升，能升到 0.66 m", "不同：推力可设上限，座板跟着大腿走，能升到 0.69 m"),
           ("不同：用在床边、不用机器人", "不同：用在床边、单自由度机构")],
 "statemachine": [('<h3 style="font-size:34px;font-weight:700;color:#9A5408">离座后停住</h3><p style="font-size:28px;line-height:1.5;color:#3F4A57">人站起来后座板停在原高度、保持水平，坐回去也接得住</p>',
                   '<h3 style="font-size:34px;font-weight:700;color:#9A5408">离座后停住</h3><p style="font-size:28px;line-height:1.5;color:#3F4A57">座板停在放手时的位置接人；人走开、踏板空了几秒后才降回齐平</p>'),
                  ("第三，人站起来以后，座板停在原高度、保持水平，万一坐回去也接得住。", "第三，人站起来以后，座板停在放手时的位置，万一坐回去也接得住；等人走开、踏板也空了几秒，座板才降回和床齐平，这样人回来时像坐普通椅子一样坐上去。")],
 "limits": [("<li>仿真里的用户模型是简化的，只用来检验控制逻辑</li>", "<li>人体按二维刚体轮廓、坐垫按独立弹簧床算；分区坐垫和面料摩擦要样件实测</li>"),
            ("<li>往前挪 25–30 cm 对老人是否可行，还没验证</li>", "<li>挪上座板约 10–20 cm、回床往后挪：防滑面料会让挪动更难，要实测</li>"),
            ("<li>评估占地和夜里走动时的绊倒风险</li>", "<li>评估占地和夜里走动时的绊倒风险；控制仿真按坐板重跑</li>")],
 "appendix": [("<tr><td>现有技术和专利表</td><td>角色 1</td><td><b style=\"color:#2F7A55\">有材料</b></td></tr>",
               "<tr><td>现有技术和专利表</td><td>角色 1</td><td><b style=\"color:#2F7A55\">有材料</b></td></tr>\n<tr><td>单自由度坐板设计（81 人、机构、坐垫、干涉、两轮审计）</td><td>角色 2、3</td><td><b style=\"color:#2F7A55\">有材料</b></td></tr>")],
 "questions": [("机构做到“选型 + 尺寸估算 + CAD 运动动画”够不够？双升降柱为主、剪叉作对比可以吗？", "座板改成跟着大腿走的单自由度曲线（斜导轨 + 倾角连杆），竖直升降作对比，这个方向可以吗？做到选型 + 尺寸估算 + CAD 运动动画够不够？"),
               ("第二，机构做到选型、尺寸估算和 CAD 运动动画够不够；", "第二，座板改成跟着大腿走的曲线、竖直升降作对比，这个方向行不行，机构做到选型、尺寸估算和 CAD 运动动画够不够；")],
}

REPL["statemachine"] += [("才带人慢慢降；座板上没人时不动</p>", "才带人慢慢降；空座板只在“空载复位”时自己降回齐平</p>"),
                         ("第二，只有确认有人坐着才下降，座板上没人时不动；", "第二，带人下降必须确认有人坐着，并且按住“降”或坐着很久没有操作；空座板只在人走开以后自己降回齐平；")]

# ---------------------------------------------------------------- v5.3: fixes after the Gemini audit of the deck (audit/v2)
RZ = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/release_z.json")))
zr = sorted(v["seat_z"] for v in RZ.values()); ZMED, ZMAX = st.median(zr), max(zr)
NW_L = BS["bed0.58_L_bar"]["n_worse"]
S["whynot"] = sec("whynot", PAPER,
  head("2 · 方案比较", f"床不用垫高，也能达到抬高床的省力效果；比低床省约 {pct(SAVE_LOW)}", 56) +
  f'\n<div style="display:grid;grid-template-columns:1060px 1fr;gap:56px;align-items:start">\n<div style="display:flex;flex-direction:column;gap:18px">\n'
  f'<p style="font-size:26px;color:#66707C">起身最吃力那一刻的 effort，中位数（越低越轻松；同一模型、同一批 {N72} 位用户）</p>\n'
  f'<div style="display:grid;grid-template-columns:360px 1fr;gap:18px 20px;align-items:center">\n'
  + _bar("低床 0.42 m + L 扶手", CMP["low"], "#C3C9D1") + "\n"
  + _bar("抬高床 0.58 m + L 扶手", CMP["high_L"], "#9AA3AD") + "\n"
  + _bar("抬高床 0.58 m + 最佳扶手", CMP["high_best"], "#7D8792") + "\n"
  + _bar("起身台：坐板放手那一刻", CMP["seat"], "#B4620A", bold=True) +
  f'\n</div>\n<p style="font-size:24px;line-height:1.5;color:{BODY}">另有 {NOFF} 位用户（1.50 m、臀部厚）坐在 0.58 m 的床上脚踩不实，没法比；起身台平时 0.42 m，81 人都踩得实</p>\n</div>\n'
  f'<div style="display:flex;flex-direction:column;gap:24px">\n'
  f'<p style="font-size:30px;line-height:1.45"><b>比低床：</b>每个人都省，中位数省 {pct(SAVE_LOW)}</p>\n'
  f'<p style="font-size:30px;line-height:1.45"><b>和抬高床：</b>相当，中位数再省 {pc(SAVE_HB)}–{pct(SAVE_HL)}；{NWORSE} 人略差（多是髋晚前移、脚靠后，差 ≤ 0.03）</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{BODY}"><b>为什么只是相当：</b>放手时座板高度中位 {ZMED:.2f} m、最高 {ZMAX:.2f} m，和 0.58 m 的床差不多高</p>\n'
  f'<p style="font-size:28px;line-height:1.5;color:{ACC}"><b>抬高床做不到的：</b>平时坐得低、脚踩得实；起身全程有托、不往前滑、坐回接得住（第 8 页）</p>\n</div>\n</div>\n'
  + foot("effort = 最吃力的关节用掉自身最大力量的比例（2D 准静态模型，手上最多出半个体重）。抬高床按最有利的坐姿（臀部离床沿 0–10 cm）和 35 个扶手位置里最好的算"),
  f"接下来比较几种起身方式。我们用同一个二维、准静态的起身模型、同一副 L 形扶手和同一批用户，算最吃力那一刻最吃力的关节用掉了自身最大力量的几成，叫 effort，越低越轻松。从 0.42 米的低床起身，中位数是 {CMP['low']:.2f}；把床垫高到 0.58 米，是 {CMP['high_L']:.2f}，扶手放到最有利的位置是 {CMP['high_best']:.2f}；起身台在座板放手那一刻是 {CMP['seat']:.2f}。所以起身台比低床每个人都省，中位数省 {pct(SAVE_LOW)}；和抬高床相当，中位数再省 {pc(SAVE_HB)} 到 {pct(SAVE_HL)}。有 {NWORSE} 个人略差，多是髋部晚前移、脚放得靠后的人，差得很少，而且这是和每人最有利的扶手位置比；和同一副扶手比只有 {NW_L} 人略差。为什么只是相当？因为人离开座板时，座板高度中位数是 {ZMED:.2f} 米，最高 {ZMAX:.2f} 米，和 0.58 米的床差不多。所以起身台的价值在于：不用把床垫高、平时脚踩得实，同时达到抬高床的省力效果；而且起身全程有座板托着，不往前滑，坐回去也接得住，这是抬高床做不到的。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:40px")

S["statemachine"] = sec("statemachine", PAPER,
  head("4 · 控制", "状态机：出了意外先停住；只有人按住才会往下动") +
  "\n" + img("seat_statemachine", "状态机：待机、已坐上、抬升、停住、站立保持、下降、空座板停住、锁定，以及它们之间的切换条件", 1664, 520, bg="#FFFFFF") +
  f'\n<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:28px">\n'
  f'<div style="background:{LIGHT};border-radius:20px;padding:28px;display:flex;flex-direction:column;gap:10px"><h3 style="font-size:32px;font-weight:700;color:{ACC}">松手即停</h3><p style="font-size:26px;line-height:1.5;color:{BODY}">松手或任何故障，立即停住并制动，座板停在当前位置</p></div>\n'
  f'<div style="background:{LIGHT};border-radius:20px;padding:28px;display:flex;flex-direction:column;gap:10px"><h3 style="font-size:32px;font-weight:700;color:{ACC}">按住“降”才降</h3><p style="font-size:26px;line-height:1.5;color:{BODY}">松开就停；坐着很久不动只提醒、呼叫家属，座板不自己动</p></div>\n'
  f'<div style="background:{LIGHT};border-radius:20px;padding:28px;display:flex;flex-direction:column;gap:10px"><h3 style="font-size:32px;font-weight:700;color:{ACC}">离座后停住</h3><p style="font-size:26px;line-height:1.5;color:{BODY}">座板停在放手处接人；回床时按住“降”，空座板停在 0.50 m，坐上后再降到床面</p></div>\n</div>',
  "控制部分我们用一个状态机。核心是三条规则。第一，松手或者出任何故障，立即停住并制动。第二，座板往下动必须有人按住“降”，松开就停；如果有人坐在升起的座板上很久不动，系统只提醒并呼叫家属，不会自己把人降下去，因为一个晕过去或很虚弱的人，在动着的座板上更容易滑落。第三，人站起来以后，座板停在放手的位置，万一坐回去也接得住；空座板也只在按住“降”时才动。回床时按住“降”，空座板先停在 0.50 米这个回床高度，人坐上去比坐到床面高度省约两成力，坐稳后再按住“降”，带着人降到床面，往后挪回床上。自检有两层：空着的时候检查各个测力单元的零点；抬升中，座板、踏板和横杆三处的力加起来应该约等于体重，差超过 15% 并持续半秒才锁定，锁定后只能按住“降”慢慢下。",
  layout="display:flex;flex-direction:column;gap:30px")

S["sensing"] = sec("sensing", LIGHT,
  head("4 · 传感与交互", "手握发指令，力分布确认人准备好了") +
  f'\n<div style="display:grid;grid-template-columns:640px 1fr;gap:56px;align-items:center">\n' + img("seat_sensors", "侧视示意：1 座板测力，2 横杆测力，3 握把开关，4 踏板测力", 640, 540) +
  f'\n<div style="display:flex;flex-direction:column;gap:20px">\n'
  f'<p style="font-size:30px;line-height:1.5"><b>1 座板下测力：</b><span style="color:{BODY}">坐上了没有、坐正了没有（压力中心）；推了多少力（速度规则，按座板倾角折算）</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>2 横杆测力：</b><span style="color:{BODY}">手在不在上面；人是不是挂在横杆上</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>3 握把式“起”开关：</b><span style="color:{BODY}">握紧才升、松手就停</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>4 踏板测力：</b><span style="color:{BODY}">脚踩实了没有；体重是不是真的转到了脚上</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>自检：</b><span style="color:{BODY}">空着时查零点；抬升中三处力之和 ≈ 体重</span></p>\n'
  f'<p style="font-size:30px;line-height:1.5"><b>反馈：</b><span style="color:{BODY}">握把上的状态灯和踏板夜灯</span></p>\n</div>\n</div>\n'
  + foot("不用底座称重：台架和床固定后，一部分力经固定件传给床，底座测不准。先例：东京大学 Kogami 等的辅助椅用座下压力中心判断“想起身”"),
  "交互上，我们用手握来发指令：开关做在人正前方横杆的握把上，握紧才升、松手就停。座板下的测力单元测坐上了没有、坐正了没有，也测座板推了多少力，用来控制速度；座板会前倾，测力单元测的是垂直于座面的力，控制器用丝杠编码器知道当时的倾角，把它折算成竖直方向。横杆测力看手在不在、人是不是整个挂在横杆上；踏板测力看脚踩实了没有，也用来确认体重真的转到了脚上。自检分两层：空着的时候查零点；抬升中，三处的力加起来应该约等于体重。我们不用底座称重，因为台架和床固定以后，有一部分力经固定件传到床上，底座测不准。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:40px")

S["speed"] = (f'<section id="speed" data-transition="fade" style="background:{LIGHT};color:{INK};{SANS};padding:128px;display:grid;grid-template-columns:1fr 760px;gap:56px;align-items:center">\n'
  f'<div style="display:flex;flex-direction:column;gap:26px">\n<p style="font-size:26px;color:{ACC};letter-spacing:2px">4 · 速度随人自适应</p>\n'
  f'<h2 style="{SERIF};font-size:54px;font-weight:700;line-height:1.25">人卸掉多少体重，座板就升多快</h2>\n'
  f'<p style="font-size:32px;line-height:1.4;background:{PAPER};border:1px solid {LINE};border-radius:16px;padding:24px">v = k ×（推力上限 − 座板的力），限在 0 到最快速度之间</p>\n'
  f'<ul style="font-size:26px;line-height:1.5;color:{BODY}">\n'
  f'<li>人往回坐，座板力超过上限，速度变成 0，不会倒退</li>\n'
  f'<li>座板力下降，还要看到踏板力上升才提速；人挂在横杆上就限速</li>\n'
  f'<li>个人设置：推力上限 0.5–0.6 × 体重，最快 1.5–3 cm/s，由家人或护理人员设定</li>\n</ul>\n'
  + todo("右图是竖直升降版本的仿真（升到 0.66 m）；按坐板的轨迹和倾角、新的下降规则重跑") + '\n</div>\n'
  f'<img src="/_blob/ad1f8a915d4e93b6cc6e40353ef198a9" alt="竖直升降版本的 8 个场景仿真：座板高度、座板受力和控制状态" style="width:760px;height:760px;object-fit:contain;background:#FFFFFF;border-radius:16px;border:1px solid {LINE}">\n'
  "<aside>抬升速度怎么定？我们用一条规则：速度等于 k 乘以“推力上限减去座板测到的力”，并且限在零到最快速度之间。人自己卸掉的体重越多，座板上的力越小，座板就升得越快；如果人往回坐，力超过上限，速度变成零，不会倒退。为了防止误判，座板力下降时还要看到踏板力相应上升才提速，说明体重真的转到了脚上；如果人把体重挂在横杆上，就限速。个人设置包括推力上限和最快速度。右边的仿真还是竖直升降版本的，我们会按坐板的轨迹和新的下降规则重跑。</aside>\n</section>\n")

# ---------------------------------------------------------------- v5.4: fall catch (seat_1dof_fall_catch.py) and the seat controller (controller_seat.py)
FC = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/fall_catch.json")))["summary"]
CS = json.load(open(os.path.join(ROOT, "model/calc_v13/controller_seat.json"))); CSS = {x["key"]: x for x in CS["scenarios"]}
def _bar2(label, v, col, note, bold=False):
    w = round(500 * v)
    return (f'<p style="font-size:26px;color:{INK if bold else BODY}">{"<b>" + label + "</b>" if bold else label}</p>'
            f'<div style="display:flex;align-items:center;gap:14px"><div style="height:34px;width:{max(w, 4)}px;background:{col};border-radius:0 6px 6px 0"></div>'
            f'<p style="font-size:26px;font-weight:700">{100 * v:.0f}%</p><p style="font-size:21px;color:#66707C">{note}</p></div>')
S["whynot"] = sec("whynot", PAPER,
  head("2 · 方案比较", "床不用垫高，省力达到抬高床；腿一软时，全程都接得住", 56) +
  f'\n<div style="display:grid;grid-template-columns:1040px 1fr;gap:48px;align-items:start">\n<div style="display:flex;flex-direction:column;gap:14px">\n'
  f'<p style="font-size:24px;color:#66707C">① 起身最吃力那一刻的 effort，中位数（越低越轻松；同一批 {N72} 人）</p>\n'
  f'<div style="display:grid;grid-template-columns:340px 1fr;gap:10px 20px;align-items:center">\n'
  + _bar("低床 0.42 m + L 扶手", CMP["low"], "#C3C9D1") + "\n" + _bar("抬高床 0.58 m + 最佳扶手", CMP["high_best"], "#7D8792") + "\n"
  + _bar("起身台：坐板放手那一刻", CMP["seat"], "#B4620A", bold=True) +
  f'\n</div>\n<p style="font-size:24px;color:#66707C;margin-top:14px">② 腿一软往回坐时，臀部还落在座面上的起身阶段，中位数（81 人）</p>\n'
  f'<div style="display:grid;grid-template-columns:340px 1fr;gap:10px 20px;align-items:center">\n'
  + _bar2("低床 0.42 m", FC["bed042"]["caught_share_med"], "#C3C9D1", f'全程接得住 {FC["bed042"]["n_always_caught"]}/81') + "\n"
  + _bar2("抬高床 0.58 m", FC["bed058"]["caught_share_med"], "#7D8792", f'{FC["bed058"]["n_always_caught"]}/81') + "\n"
  + _bar2("竖直升降座板", FC["vertical"]["caught_share_med"], "#9AA3AD", f'{FC["vertical"]["n_always_caught"]}/81') + "\n"
  + _bar2("起身台：曲线坐板", FC["seat"]["caught_share_med"], "#B4620A", f'{FC["seat"]["n_always_caught"]}/81', bold=True) +
  f'\n</div>\n</div>\n<div style="display:flex;flex-direction:column;gap:22px">\n'
  f'<p style="font-size:28px;line-height:1.45"><b>省力：</b>比低床省 {pct(SAVE_LOW)}；和抬高床相当（再省 {pc(SAVE_HB)}–{pct(SAVE_HL)}）</p>\n'
  f'<p style="font-size:28px;line-height:1.45"><b>接得住：</b>站起来后臀部在床沿外约 25 cm，床接不住；坐板停在身后，臀部落点还在座面前缘以内 {FC["seat"]["catch_at_standing_cm_med"]:.1f} cm</p>\n'
  f'<p style="font-size:26px;line-height:1.5;color:{BODY}">扶手抓得住，但撑不住整个人（模型里两手合计最多 1/4 体重）</p>\n'
  f'<p style="font-size:26px;line-height:1.5;color:{ACC}">往后直挺挺倒时床也接得住；坐板 {100 * FC["seat"]["backward_on_seat_med"]:.0f}% 落在座板上、其余越过座板后缘落到床上，都不落地 → 后缘软包</p>\n</div>\n</div>\n'
  + foot("effort：2D 准静态模型，两手合计最多出 1/4 体重。②：起身中任一时刻髋部直着往下落，臀部落点（髋后 4 cm）在座面前缘以内算接住；床按坐在床沿（髋在床沿上方）算"),
  f"接下来比较几种起身方式，看两件事。第一是省力：同一个模型、同一副扶手，起身台比从低床起身省 {pct(SAVE_LOW)}，和把床垫高到 0.58 米相当。第二是更重要的：起身中间腿一软往回坐，会不会坐空。我们按同一个定义算：任一时刻髋部直着往下落，臀部落点还在座面上就算接住。床只在刚起身的前 15% 左右接得住，因为人一站起来，臀部就到了床沿外大约 25 厘米；竖直升降的座板跟不上大腿，中位数只有 62%；曲线坐板一直跟着人，人离开以后就停在身后，81 个人在整个起身过程中都接得住。扶手能抓，但两只手撑不住整个人。也要说清楚：如果人是直挺挺往后倒，床也接得住；这时坐板有一部分情况会越过座板后缘落到床上，不会落地，但会碰到后缘，所以座板后缘要做软包。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:32px")

S["speed"] = (f'<section id="speed" data-transition="fade" style="background:{LIGHT};color:{INK};{SANS};padding:128px;display:grid;grid-template-columns:1fr 760px;gap:56px;align-items:center">\n'
  f'<div style="display:flex;flex-direction:column;gap:24px">\n<p style="font-size:26px;color:{ACC};letter-spacing:2px">4 · 速度随人自适应</p>\n'
  f'<h2 style="{SERIF};font-size:54px;font-weight:700;line-height:1.25">人卸掉多少体重，座板就升多快</h2>\n'
  f'<p style="font-size:30px;line-height:1.4;background:{PAPER};border:1px solid {LINE};border-radius:16px;padding:22px">v = k ×（推力上限 − 座板的力），限在 0 到最快速度之间</p>\n'
  f'<ul style="font-size:26px;line-height:1.5;color:{BODY}">\n'
  f'<li>人往回坐，座板力超过上限，速度变成 0，不会倒退</li>\n'
  f'<li>座板力按倾角折算成竖直方向；人挂在横杆上就限速</li>\n'
  f'<li>个人设置：推力上限 0.5–0.6 × 体重，最快 1.5–3 cm/s</li>\n'
  f'<li>按坐板轨迹仿真 {len(CS["scenarios"])} 个场景，都落到安全状态（全部见附录）；典型用户 {CSS["typical"]["seat_off_time_s"]:.0f} s 内在 {CSS["typical"]["seat_off_height"]:.2f} m 离座</li>\n</ul>\n</div>\n'
  + img("ctrl_seat_main", "坐板控制仿真三个场景：典型用户、抬升中晕倒松手（停住接人、17 秒后提醒呼叫、不自己降）、抬升中断电（按住“降”用电池慢降）", 740, 810, bg="#FFFFFF") + "\n"
  f"<aside>抬升速度怎么定？我们用一条规则：速度等于 k 乘以“推力上限减去座板测到的力”，并且限在零到最快速度之间。人自己卸掉的体重越多，座板升得越快；人往回坐，速度变成零，不会倒退。座板会前倾，控制器按丝杠编码器知道的倾角，把座板的力折算成竖直方向；如果人把体重挂在横杆上，就限速。右边是按坐板实际轨迹重跑的仿真，一共 {len(CS['scenarios'])} 个场景，这里放三个：典型用户大约 {CSS['typical']['seat_off_time_s']:.0f} 秒在 {CSS['typical']['seat_off_height']:.2f} 米离座，座板停在那里；抬升中晕倒松手，座板停住接人，17 秒后提醒并呼叫家属，不会自己往下降；断电时制动抱住，按住“降”用电池慢慢降。其余场景放在附录。</aside>\n</section>\n")

# ---------------------------------------------------------------- v5.5: mechanism slide with the 3-D view (make_mech_views.py)
S["mechanism"] = sec("mechanism", PAPER,
  head("3 · 机构", "座板沿一条曲线前移、上升、前倾：斜导轨 + 倾角连杆，一个电机", 54) +
  f'\n<div style="display:grid;grid-template-columns:960px 1fr;gap:44px;align-items:start">\n'
  + img("mech_3d_slide", "三维示意（座板与床齐平）：床头一侧半透明的机构箱里有两根导轨、滑块板和 4 个滑块、滚珠丝杠、上端的电机和制动器、倾角连杆；座板由悬臂托架伸出；L 形扶手；床尾一侧敞开", 960, 635, bg="#FFFFFF") +
  f'\n<div style="display:flex;flex-direction:column;gap:20px">\n'
  + img("seat_vs_vertical", "同一位髋早前移的用户：竖直升降时往前滑、坐回落空；曲线座板跟着大腿走", 660, 260) +
  f'\n<ul style="font-size:24px;line-height:1.45;color:{BODY}">\n'
  f'<li><b>运动：</b>3 个转动副 + 1 个移动副。铰点 1 在滑块上沿导轨走直线，连杆拉住铰点 2，两点定下位置和前倾</li>\n'
  f'<li><b>传动：</b>电机 → 皮带 → 滚珠丝杠 → 滑块板；第二根导轨和 4 个滑块只扛单侧偏载</li>\n'
  f'<li><b>为什么不竖直升：</b>竖直 {VS["n_ok"]}/81 不前滑、接得住，曲线 {nok}/81</li>\n'
  f'<li>前移 {100 * M["travel"]["dx"]:.1f} cm、上升 {100 * M["travel"]["dz"]:.1f} cm，前倾 ≤ {M["phi_run_max"]:.0f}°</li>\n</ul>\n</div>\n</div>\n'
  + foot("三维图由二维模型的坐标画出（座板与床齐平），截面尺寸为估计值，不是 CAD"),
  f"接下来讲机构。左边是去掉人以后的三维示意，座板现在和床齐平。所有机构都装在床头一侧这个箱子里，床尾一侧是空的。运动上，它是一个三个转动副加一个移动副的四杆机构：座板下面有两个铰点，铰点 1 装在滑块板上，沿斜导轨走直线；铰点 2 用一根倾角连杆拉到底座上。这两个铰点一定，座板的位置和前倾角就都定了。驱动只有一个电机，经过皮带带动滚珠丝杠，推着滑块板走。这里有两根导轨、四个滑块，第一根导轨就是那个移动副；第二根导轨不增加约束，只是用来扛座板挂在一侧带来的扭矩。为什么不竖直升？右上角是同一个人：竖直升的座板跟不上大腿，人会往前滑，81 人里只有 {VS['n_ok']} 人合格；曲线座板 {nok} 人都合格。座板前移约 {100 * M['travel']['dx']:.0f} 厘米、上升约 {100 * M['travel']['dz']:.0f} 厘米，前倾最多 {M['phi_run_max']:.0f} 度。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:30px")

REPL.pop("statemachine", None)   # v5.3 rewrites the whole slide
REPL["limits"].append(("<li>人体按二维刚体轮廓、坐垫按独立弹簧床算；分区坐垫和面料摩擦要样件实测</li>", "<li>人体按二维刚体轮廓、坐垫按独立弹簧床算；分区坐垫和面料摩擦要样件实测</li>\n<li>横杆固定：回来要从床尾一侧侧身走进约 0.46 m 深的空间，助行器进不去。备选：可掀起的翻转横杆（要加锁扣和“已锁住”检测，可能忘了放下）</li>"))
REPL["limits"].append(("<li>评估占地和夜里走动时的绊倒风险；控制仿真按坐板重跑</li>", "<li>评估占地和夜里走动时的绊倒风险；摔倒方式（腿软、往后倒）要用实测动作核对</li>"))

# ---------------------------------------------------------------- v5.6: rise paths now reach standing (solve_s fix) + deck audit round 3
FC = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/fall_catch.json")))["summary"]
BT = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/bed_thigh.json")))["thigh_slope_deg"]
FS, F58, F42, FV = FC["seat"], FC["bed058"], FC["bed042"], FC["vertical"]
NW_ALL = BS["bed0.58_handle"]["n_worse"]; HB, SE = CMP["high_best"], CMP["seat"]
_th = lambda r, c: f'<td style="padding:8px 12px;border-bottom:1px solid {LINE}{";font-weight:700;color:" + INK if c else ""}">{r}</td>'
def _tr(cells, bold_last=True):
    return "<tr>" + "".join(_th(c, bold_last and i == len(cells) - 1) for i, c in enumerate(cells)) + "</tr>"
MODES = ('<table style="font-size:21px;color:#3F4A57;border-collapse:collapse;width:100%">'
  + '<tr>' + "".join(f'<th style="text-align:left;padding:8px 12px;border-bottom:2px solid {LINE};font-size:20px;color:#66707C">{h}</th>' for h in ("腿一软时", "低床 0.42 m", "抬高床 0.58 m", "竖直升降", "曲线坐板")) + '</tr>'
  + _tr(["① 髋直着往下落", pct(F42["caught_share_med"]), pct(F58["caught_share_med"]), pct(FV["caught_share_med"]), f'{pct(FS["caught_share_med"])}（每人 ≥ {pct(FS["caught_share_min"])}）'])
  + _tr(["② 膝软、髋往后下落", pct(F42["knee_on_med"]), pct(F58["knee_on_med"]), "—", f'{pct(FS["knee_on_med"])}，其余落到后缘'])
  + _tr(["③ 直挺挺往后倒", "接得住", "接得住", "—", f'{pct(FS["backward_on_seat_med"])}，其余越过后缘'])
  + '</table>')
S["whynot"] = sec("whynot", PAPER,
  head("2 · 方案比较", "床不用垫高，省力达到抬高床；腿一软时，起身大半程臀部都落在座板上", 52) +
  f'\n<div style="display:grid;grid-template-columns:1080px 1fr;gap:48px;align-items:start">\n<div style="display:flex;flex-direction:column;gap:14px">\n'
  f'<p style="font-size:24px;color:#66707C">① 起身最吃力那一刻的 effort，中位数（越低越轻松；81 人）</p>\n'
  f'<div style="display:grid;grid-template-columns:400px 1fr;gap:10px 20px;align-items:center">\n'
  + _bar("低床 0.42 m + L 扶手", CMP["low"], "#C3C9D1") + "\n" + _bar("抬高床 0.58 m + 扶手放最优处", HB, "#7D8792") + "\n"
  + _bar("起身台：坐板放手那一刻", SE, "#B4620A", bold=True) +
  f'\n</div>\n<p style="font-size:24px;color:#66707C;margin-top:12px">② 臀部还落在支撑面上的起身阶段，中位数（81 人，三种摔法）</p>\n' + MODES +
  f'\n</div>\n<div style="display:flex;flex-direction:column;gap:20px">\n'
  f'<p style="font-size:27px;line-height:1.45"><b>省力：</b>比低床省 {pct(SAVE_LOW)}；比抬高床再省约 {pc(SAVE_HB)}%，{NW_ALL}/81 人略费力</p>\n'
  f'<p style="font-size:27px;line-height:1.45"><b>床：</b>人一站起来，臀部在床沿外约 25 cm，① ② 大半程接不住</p>\n'
  f'<p style="font-size:27px;line-height:1.45"><b>坐板：</b>只在快站直时，{81 - FS["n_always_caught"]}/81 人直着落会落在前缘外 {-FS["miss_worst_cm_med"]:.0f}–{-FS["miss_worst_cm_min"]:.0f} cm</p>\n'
  f'<p style="font-size:25px;line-height:1.5;color:{ACC}">往后摔会碰座板后缘 → 后缘软包</p>\n'
  f'<p style="font-size:25px;line-height:1.5;color:{BODY}">扶手抓得住，撑不住整个人（两手最多 1/4 体重）</p>\n</div>\n</div>\n'
  + foot("effort：2D 准静态，81 人。②：起身中任一时刻腿一软，臀部落点（髋后 4 cm）还在座面上算接住；床按坐在床沿算。三种摔法是边界情况，真实摔倒在它们之间"),
  f"接下来比较几种起身方式，看两件事。第一是省力：同一个模型、同样 81 位用户，起身台比从低床起身省约 {pct(SAVE_LOW)}；和把床垫高到 0.58 米、扶手放在对它最有利的位置相比，再省约 {pc(SAVE_HB)}%，但有 {NW_ALL} 个人略费力，所以只能说相当或略好。第二件事更重要：起身中间腿一软，会不会坐空。我们算了三种摔法。髋直着往下落时，床只在刚起身的前 {pct(F58['caught_share_med'])} 左右接得住，因为人一站起来，臀部就到了床沿外大约 25 厘米；坐板一直跟着人，离开后停在身后，起身的绝大部分都接得住，只在快站直时，约三分之一的人会落在座板前缘外几厘米。膝盖软、髋往后下落时，坐板从不让人落到前面，床要到快站直时才接得住。直挺挺往后倒时，床都接得住，坐板这时会被碰到后缘，所以后缘要软包。三种摔法是边界情况，真实的摔倒在它们之间。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:28px")

S["verify"] = sec("verify", LIGHT,
  head("5 · 验证", "设计要求 → 怎么验证 → 结果") +
  f'\n<table style="font-size:22px;color:#3F4A57">\n<tr><th style="width:29%">设计要求</th><th style="width:22%">怎么验证</th><th style="width:36%">目前结果</th><th style="width:13%">状态</th></tr>\n'
  f'<tr><td>1a 床不用垫高，起身省力达到抬高床的水平</td><td>2D 起身模型，同一批 81 人</td><td>比低床省 {pct(SAVE_LOW)}；比抬高床再省约 {pc(SAVE_HB)}%（中位 {SE:.2f} vs {HB:.2f}），{NW_ALL}/81 人略费力</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>1b 座板跟着人走：不往前滑、坐回接得住</td><td>81 人 × 机构实际轨迹</td><td>{nok}/81 合格（竖直升降 {VS["n_ok"]}/81）；按坐垫压下后 {CT.get("n_ok", "—")}/81；腿一软直着落，起身中位 {pct(FS["caught_share_med"])} 接得住（床 {pct(F58["caught_share_med"])}）</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>2 推力不超过约半个体重</td><td>速度规则 + 场景仿真</td><td>坐板版 {N_SCEN} 个场景都没有超过上限</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>3 手握 + 力分布确认后才抬；松手即停</td><td>状态机仿真</td><td>松手后立即停住</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>4 抬升速度跟着人走，并能按人设定</td><td>坐板控制仿真</td><td>速度随座板力变；推力上限、最快速度按人设；典型用户 {CSS["typical"]["seat_off_time_s"]:.0f} s 离座</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>5 人坐上、挪动、坐回时不翻</td><td>合重心和倾翻计算</td><td>人在台上余量足；人在地上要和床固定；[待补] 真实质量复核</td><td><b style="color:#9A5408">进行中</b></td></tr>\n'
  f'<tr><td>6 只有按住“降”才往下动；离座后停住接人</td><td>状态机仿真</td><td>坐回、晕倒、断电、回床场景都落到安全状态</td><td><b style="color:#2F7A55">初步完成</b></td></tr>\n'
  f'<tr><td>＋ 机构放得下、推得动、撑得住</td><td>尺寸、干涉、选型、FEA</td><td>机构箱离床 2.1 cm；[待补] FEA（应力和悬臂变形）</td><td><b style="color:#9A5408">进行中</b></td></tr>\n</table>\n'
  + foot("本项目只做概念、设计和仿真，不做实物和人体实验；“初步完成”指已有第一版计算或仿真结果"),
  f"这张表把第 4 页的六条设计要求和验证方法一一对上。第一条我们写成两项：一是床不用垫高，起身省力达到抬高床的水平，结果是比低床省约 {pct(SAVE_LOW)}，比抬高床再省一点；二是座板跟着人走：用机构实际轨迹重跑 81 位用户，{nok} 人不往前滑、坐回接得住，竖直升降只有 {VS['n_ok']} 人；腿一软时，起身的绝大部分都有座板接住。推力上限、松手即停、速度跟着人走、只有按住才往下降，用状态机的场景仿真验证。最后一行不是用户要求，是机构本身要做到的：放得下、推得动、撑得住，强度和悬臂变形的 FEA 还在做。",
  pad="128px 128px 160px", layout="display:flex;flex-direction:column;gap:32px")

S["conclusion"] = S["conclusion"].replace(
  "床不用垫高，省力达到抬高床；起身全程腿一软都接得住（81/81，床只在刚起身时接得住）",
  f"床不用垫高，省力达到抬高床；腿一软时，起身大半程都有座板接住（床只在刚起身时接得住）").replace(
  "松手即停、有人坐着才降、速度跟着人走；断电时制动抱住，拉拨杆可慢慢降", "松手即停、只有按住“降”才往下动、速度跟着人走；断电时制动抱住，电池或拨杆慢慢降")
_ca = re.search(r"<aside>.*?</aside>", S["conclusion"], re.S).group(0)
S["conclusion"] = S["conclusion"].replace(_ca, f"<aside>总结一下。起身台平时和床一样低，起身时座板跟着大腿托一程。按同一个模型，它比从低床起身省约 {pct(SAVE_LOW)}，和把床垫高到 0.58 米相当或略好；更重要的是，起身中间腿一软，起身的绝大部分都有座板在臀部下面接住，而床只在刚起身时接得住。机构上，一个电机带动斜导轨和倾角连杆，整套机构封闭在床头一侧，床尾一侧敞开，台架和床固定。控制上，松手即停，只有按住“降”才往下动，速度跟着人走；断电时制动器抱住，用电池或拨杆慢慢降下来。</aside>")

S["concept"] = S["concept"].replace("<b>1</b> 坐在床沿，挪上和床齐平的座板", "<b>1</b> 坐到床沿：往前倾就够得着横杆").replace(
  "<b>2</b> 双手握住身前横杆，想坐多久都行", "<b>2</b> 握住横杆，挪上和床齐平的座板；想坐多久都行").replace(
  "用的时候一共五步：坐在床沿，往前挪一点，坐上一块和床齐平的座板；双手握住身前横杆上的握把，想坐多久都可以；",
  "用的时候一共五步：先坐到床沿，往前倾一点就能握住身前的横杆；拉着横杆往前挪，坐上一块和床齐平的座板，想坐多久都可以；")
assert "往前倾就够得着横杆" in S["concept"] and "拉着横杆往前挪" in S["concept"]

_mo = f"座板前移约 {100 * M['travel']['dx']:.0f} 厘米、上升约 {100 * M['travel']['dz']:.0f} 厘米"
assert _mo in S["mechanism"]; S["mechanism"] = S["mechanism"].replace(_mo, f"座板前移约 {100 * M['travel']['dx']:.1f} 厘米、上升约 {100 * M['travel']['dz']:.1f} 厘米")

for a, b in (("先断电机电源再松制动，限速约 3 cm/s，松手即停", "先断电机电源再松制动，丝杠轴上的离心限速器把速度限在约 3 cm/s，松手即停"),
             ("人的重量把座板慢慢压下去，速度限在每秒 3 厘米左右", "人的重量把座板慢慢压下去，丝杠轴上的离心限速器把速度限在每秒 3 厘米左右")):
    assert a in S["sizing"], a; S["sizing"] = S["sizing"].replace(a, b)
for a, b in (("下降遇阻（电机电流升高）即停", "下降遇阻（电机电流或座板测力突变）即停"), ("（先断电机），限速 3 cm/s", "（先断电机），离心限速 3 cm/s")):
    assert a in S["risk"], a; S["risk"] = S["risk"].replace(a, b)
_sf = f"底座 x 3–78 cm、y {cm(T['base']['y'][0])} … +{cm(T['base']['y'][1])} cm"
assert _sf in S["stability"]; S["stability"] = S["stability"].replace(_sf, f"底座 x 3–78 cm（离床方向）、y {cm(T['base']['y'][0])} … +{cm(T['base']['y'][1])} cm（沿床长 65 cm）")
for a, b in (("空着时查零点；抬升中三处力之和 ≈ 体重</span>", "空着时查零点；抬升中三处力之和 ≈ 体重（体重在个人设置里输入）</span>"),
             ("握把上的状态灯和踏板夜灯</span>", "握把上的状态灯、踏板夜灯；握了不动时，用语音说明原因（如“请往前坐一点”）</span>")):
    assert a in S["sensing"], a; S["sensing"] = S["sensing"].replace(a, b)
_sm = "座板停在放手处接人；回床时按住“降”，空座板停在 0.50 m，坐上后再降到床面"
assert _sm in S["statemachine"]; S["statemachine"] = S["statemachine"].replace(_sm, "座板停在放手处接人；回床时按住“降”，空座板停在 0.50 m，坐上后再降到床面；推不动或到顶也停住")

REPL.setdefault("users", []).append(("<li>只有确认有人坐着才下降；离座后座板停住接人</li>", "<li>只有人按住“降”才往下动，不自动下降；离座后座板停住接人</li>"))
REPL.setdefault("limits", []).append(("往前挪二三十厘米对老人是否可行，也还没有验证。", "挪上座板约十到二十厘米、回床时往后挪，对老人是否可行，也还没有验证；座板后缘在往后摔时会被碰到，软包要做好。"))
REPL.setdefault("appendix", []).append(("<tr><td>8 个仿真场景的逐个说明</td>", f"<tr><td>{N_SCEN} 个控制仿真场景的逐个说明</td>"))

# ---------------------------------------------------------------- v5.6c: open audit round 4 (3-D joint statics, controller interlocks, lever position)
C3 = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/cantilever3d.json"))); kN = lambda k: f'{C3[k]["value"] / 1000:.1f}'
def _rep(sid, pairs):
    for a, b in pairs:
        assert a in S[sid], (sid, a[:40]); S[sid] = S[sid].replace(a, b)
_rep("sizing", [
  (f"猛坐静载 ≤ {M['F_hold100_N']} N", f"猛坐静载 ≤ {kN('nut_axial_N')} kN（含沿座面的力）"),
  (f"<b>双导轨、每轨两个滑块：</b>偏载悬臂 {FO['moment_Nm']} N·m，每个滑块约 {FO['per_carriage_lateral_N'] / 1000:.1f} kN",
   f"<b>偏载约 {C3['c1_moment_Nm']['value']} N·m：</b>先经铰点 1，铰点 1 要用能承受力矩的轴承（交叉滚子轴承，或相距约 14 cm 的双轴承）；双导轨每个滑块 ≤ {kN('carriage_resultant_N')} kN；连杆两端球铰只受拉压"),
  ("拉立柱侧带护盖的拨杆", "拉横杆拐角下带翻盖的拨杆"),
  ("如果控制器也坏了，拉立柱侧面带护盖的拨杆，", "如果控制器也坏了，拉横杆和立柱拐角下面带翻盖的拨杆，坐着就够得到，"),
  (f"100 公斤的人猛坐下来时约 {M['F_hold100_N']} 牛", f"100 公斤的人猛坐下来、再算上沿座面的力，约 {kN('nut_axial_N')} 千牛"),
  (f"偏载时导轨要扛 {FO['moment_Nm']} 牛米的力矩，所以用两根导轨、每根两个滑块。",
   f"偏载时有约 {C3['c1_moment_Nm']['value']} 牛米的力矩，它先经过铰点 1 才到滑块板，所以铰点 1 要用能承受力矩的轴承，再由两根导轨、四个滑块扛住；连杆两端用球铰，只受拉压。")])
_rep("sizing", [("载荷可在座面任意位置（虚功法）", f"载荷可在座面任意位置（虚功法）；图里只算沿座面法向，算上沿座面的力约 {kN('nut_axial_N')} kN")])
_rep("risk", [
  ("空载查零点；抬升中三处力之和与体重差 >15% 就锁住；开关用双通道触点", "空载查零点；抬升中三处力之和与体重差 15–35% 减速并语音提示，>35% 才锁住；开关用双通道触点"),
  ("控制器坏了拉带护盖的拨杆（先断电机）", "控制器坏了拉横杆拐角下带翻盖的拨杆（先断电机）"),
  ("抬升中三处力之和和体重对不上就锁住。", "抬升中三处力之和和体重对不上，差得不多就减速提醒，差得多才锁住。"),
  ("控制器也坏了，拉带护盖的拨杆，先断电机，再慢慢降。", "控制器也坏了，拉横杆拐角下面带翻盖的拨杆，坐着就够得到，先断电机，再慢慢降。")])
_rep("speed", [
  ("<li>座板力按倾角折算成竖直方向；人挂在横杆上就限速</li>", "<li>座板卸掉的力要在踏板上出现才提速；人挂在横杆上就限速</li>"),
  ("座板会前倾，控制器按丝杠编码器知道的倾角，把座板的力折算成竖直方向；", "座板卸掉的力必须同时出现在踏板上才提速，所以人往后靠回床垫时，座板不会升；座板会前倾，控制器按丝杠编码器知道的倾角，把座板的力折算成竖直方向；")])
_rep("statemachine", [("差超过 15% 并持续半秒才锁定，", "差 15% 到 35% 只减速并语音提醒，超过 35% 并持续半秒才锁定，")])
_rep("mechanism", [("<li><b>传动：</b>电机 → 皮带 → 滚珠丝杠 → 滑块板；第二根导轨和 4 个滑块只扛单侧偏载</li>",
                    "<li><b>传动：</b>电机 → 皮带 → 滚珠丝杠 → 滑块板；单侧偏载经铰点 1 的轴承传进滑块板，由第二根导轨和 4 个滑块扛住</li>")])

# the motion slide was re-laid-out by hand in the deck editor (10/27): keep the deck's version, do not regenerate it
S.pop("motion", None)

if __name__ == "__main__":
    for sid, html in S.items():
        if html: open(os.path.join(OUT, f"{sid}.html"), "w").write(html)
    for sid, pairs in REPL.items():
        p = os.path.join(OUT, f"{sid}.html"); h = open(p).read()
        for a, b in pairs:
            if b in h: continue                         # already applied (deck root is edited in place)
            if a not in h: print("  skip (superseded):", sid, a[:30]); continue
            assert h.count(a) == 1, (sid, a[:40]); h = h.replace(a, b)
        if sid == "appendix":                      # an earlier non-idempotent run repeated a row: drop repeated lines
            seen = set(); h = "\n".join(l for l in h.split("\n") if not (l.startswith("<tr><td>") and (l in seen or seen.add(l))))
        open(p, "w").write(h)
    print("written", [k for k, v in S.items() if v] + list(REPL))
