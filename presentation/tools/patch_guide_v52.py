"""Patch the published talk guide (起身台汇报讲稿) for the v5.2 seat as the main design.
Usage: python3 patch_guide_v52.py <guide_in.html> <deck_root> <thumb_dir> <guide_out.html>
  guide_in   the saved published guide (the page is static HTML: one <article> per slide + a JSON blob for the builder)
  deck_root  the deck files after update_slides_v52.py (speaker notes = the slides' <aside>)
  thumb_dir  full_NN_<id>.png renders from render_slides.js (thumbnails are re-encoded as 560 px WebP)
For the slides in UPD: new title/minutes/status/key point/Q&A/to-do, new script (the slide's aside), new thumbnail.
Then the to-do table, the to-do count, the builder labels and the JSON blob are rebuilt from the articles.
"""
import base64, html, io, json, os, re, sys, statistics as st
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
P = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/page.json")))
M = P["mech"]; L = P["layout"]; E = L["emergency"]; T = L["tipping"]; B = P["consts"]["handrail"]; VS = P["check"]["vertical_summary"]
Z = P["zoned"]; Z1 = Z["ids"]["z1"]; U0 = Z["ids"]["u"]; Z2 = Z["ids"]["z2"]; CT = P["check"]["cushion"].get(Z1, {}).get("summary", {})
F = P["check"]["design"]; nok = sum(1 for v in F.values() if v.get("release_hz") and v["fwd_slip_max_cm"] <= 2 and v["min_catch_cm"] >= 0)
Erel = st.median([v["E0_release"] for v in F.values() if v.get("E0_release") is not None]); FO = L["forces"]["载荷偏向敞开一侧 10 cm"]
fl = T["人站在地上推拉横杆（只有台架自重）"]; anchor = T["固定件拉力（ADA 609 扶手设计载荷 1112 N，安全系数 1.5）"]["anchor_N"]
cm = lambda v: f"{100 * v:.0f}"
V53 = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/fourbar_oneside.json"))); BB = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/bed_baseline.json")))
SLU = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/slider.json")))["users"]
K72 = [k for k, v in BB["users"].items() if v["0.58"]["handle"] is not None and SLU[k].get("E_release")]
_sv = lambda bed, k: st.median([1 - SLU[u]["E_release"] / BB["users"][u][bed][k] for u in K72])
S_LOW, S_HL, S_HB = (round(100 * _sv(*a)) for a in (("0.42", "L_bar"), ("0.58", "L_bar"), ("0.58", "handle"))); NW = BB["summary"]["bed0.58_handle"]["n_worse"]
FBC = V53["cantilever"]["载荷偏向敞开一侧 10 cm"]

# st: ok / part / gap; todo: (what, who, when)
UPD = {
 "cover": dict(key="一句话说清做什么：平时和床一样低；起身时座板跟着大腿前移、上升、前倾；速度跟着人，松手就停。", ask=[], todo=[("填组员姓名", "全员", "11/3")], st="part"),
 "users": dict(key="用户已经和老师确认；六条要求在最后的验证表里逐条检查，第 1 条加了“座板跟着大腿走、人不往前滑”。",
   ask=[("偏瘫的人能用吗？", "开关一只手就能用，力分布的阈值按个人基线设，所以不排除；前提是能坐稳。")], todo=[], st="ok"),
 "concept": dict(key="坐上 → 握住身前横杆 → 座板跟着大腿走 → 站稳，座板一直接得住人；机构都在床头一侧，床尾敞开。",
   ask=[("往前挪 25–30 cm，老人做得到吗？", "这是目前最大的不确定。我们用姿态几何检查能不能放下，是否可行列入局限和后续实测。"),
        ("为什么扶手不跟着座板升？", f"跟着升需要再加一套机构；固定的 L 形扶手最简单。横杆在人正前方 x {cm(B['x'])} cm、高 {B['z']:.2f} m，81 位模拟用户坐着都够得着，从坐到站不用换手。")], todo=[], st="ok"),
 "whynot": dict(key=f"同一模型、同一扶手重算：比低床省约 {S_LOW}%，比抬高床只省 {S_HB}–{S_HL}%；好处主要是平时坐得低、脚踩得实，起身全程有托、不往前滑。旧版的 13–20% 来自旧模型，已作废。",
   ask=[(f"比抬高床只省 {S_HB}–{S_HL}%，还值得做一台电动设备吗？", f"省力上优势不大，要说实话。它的价值在别处：0.58 m 的床有 {81 - len(K72)} 位矮个用户脚踩不实，而起身台平时 0.42 m；起身过程有座板托着、不往前滑、头晕坐回接得住；还有松手即停等安全控制。是否值得，要看目标用户里这些问题有多常见，这一点我们没有数据。"),
        ("为什么只多省一点？", "多数人在座板前倾最大（约 15°）时就离开了坐垫，那时髋部只比坐在 0.58 m 床上高约 4 cm，导轨上段基本没用来托人。要再省力，座板得在上段继续托住大腿，这和 15° 防滑上限冲突，是下一步要权衡的。"),
        ("模型可信吗？", "只用来比较方向和量级：二维准静态，只看最吃力的那一刻，没有动态过程和实测，已写进局限页。")], todo=[], st="part"),
 "mechanism": dict(key=f"座板不是竖直升，而是跟着大腿走：竖直升降 81 人里只有 {VS['n_ok']} 人不前滑、坐回接得住，曲线座板 {nok}/81。一个电机：斜导轨 + 倾角连杆。",
   ask=[("为什么不用两根升降柱竖直升？", f"髋往前走得早的人，竖直座板跟不上，会往前滑出座面，坐回时还会坐空；81 位模拟用户里竖直升降只有 {VS['n_ok']} 人两项都合格。"),
        ("一个自由度怎么同时管位置和前倾？", f"座板上两个铰点：一个装在沿斜导轨走的滑块上，一个用连杆拉到底座。两点一定，位置和前倾就都定了；轨迹和要的曲线最多差 {M['centre_err_mm']:.0f} mm。"),
        ("为什么不用四连杆？", f"试过三种。放座板正下方会碰小腿，只有 55/81 人合格；两侧各一套会挡住回床转腿。只放床头一侧的四连杆箱子能小一半（箱顶 {V53['box']['z_top']:.2f} m），但偏载只能靠座板上两个相距 8 cm 的铰点扛，地面铰点轴承要承受约 {FBC['bearing_ground_N_b80'] / 1000:.0f} kN，是导轨方案每个滑块的 {round(FBC['bearing_ground_N_b80'] / FO['per_carriage_lateral_N'])} 倍；推杆力也大一倍多；按补全的起身路径，{81 - V53['summary']['n_ok']} 人前滑或坐回余量不合格，站直时连杆离小腿 {V53['summary']['leg_clear_min_cm']:.0f} cm（会碰到）。它放手时更省力一点（{V53['summary']['E_rel_med']:.2f}，导轨 {Erel:.2f}），因为托得更久，但抵不过前面几条。所以保留导轨。"),
        ("双导轨是不是太占地方？", "不是主要原因：两根导轨装在同一块侧板上，箱子厚度不变，侧视面积只多 7%。箱子大是因为导轨本身要装下行程，有约 0.58 m 长。滑块间距可从 150 mm 减到 100 mm，箱顶能降 4 cm。"),
        ("单侧机构，座板是悬臂，扛得住吗？", f"偏载时悬臂力矩约 {FO['moment_Nm']} N·m。用两根导轨（相距 150 mm）、每根两个滑块（相距 150 mm），把力矩变成滑块之间的拉压，每个滑块约 {FO['per_carriage_lateral_N'] / 1000:.1f} kN，15 或 20 号导轨能承受。")],
   todo=[("CAD：机构箱、双导轨和滑块板、座板悬臂支架", "角色 3", "11/3 必须")], st="part"),
 "motion": dict(key="看一遍关键动作：座板跟着大腿走，坐垫接触区随之变化，放手后座板停住。",
   ask=[("动画是按真实尺寸做的吗？", "由二维模型直接画出：人体按 1.60 m 的比例，机构按计算出的铰点和导轨；它不是 CAD，正式版换成 SolidWorks 的运动动画。")],
   todo=[("SolidWorks 运动算例动画：滑块沿双导轨上升、连杆控制前倾、座板跟着大腿走（老师邮件里明确要求）", "角色 3", "11/3 必须")], st="gap"),
 "sizing": dict(key=f"滚珠丝杠起身时 ≤ {M['F_lift100_N']} N、猛坐静载 ≤ {M['F_hold100_N']} N；失电制动抱住，拉拨杆可慢慢降；双导轨扛住悬臂。",
   ask=[("滚珠丝杠不自锁，断电怎么办？", "失电常闭制动器：断电时抱住。应急时拉握把旁边的拨杆松开制动，人的重量把座板压下去，离心限速器把速度限在约 10 cm/s，一松手就停，不用复位。"),
        ("最轻的人坐着能降下来吗？", f"算过：最轻的用户沿导轨的下沉推力约 {E['light_user_drive_N']} N，丝杠、导轨和毛刷的阻力约 {E['resist_N']} N，是 {E['margin']} 倍。")],
   todo=[("按厂家样本选定滚珠丝杠、直线导轨和制动器型号；核对 3 cm/s 时的电机转速和扭矩", "角色 4", "11/3")], st="part"),
 "stability": dict(key=f"人在台上翻不了；人在地上扶一下横杆，{min(fl.values())} N 就会拉翻，所以台架必须和床固定。",
   ask=[("重重坐下的冲击呢？", "座板按 1.5 倍体重算，冲击可以取 2–3 倍，之后用 FEA 校核。"),
        ("固定件要多大力？", f"按扶手设计载荷 1112 N（ADA 609）、安全系数 1.5，固定件约需 {anchor} N 的拉力，用床腿夹或床垫下压板。")],
   todo=[("用 CAD 的真实质量和质心复核", "角色 4（等角色 3 的 CAD）", "11/3"), ("和床固定的固定件具体形式", "角色 3、4", "11/3")], st="part"),
 "sensing": dict(key="握紧才升、松手即停；座板下测力管速度，底座四角测力做体重自检。",
   ask=[("为什么体重自检不用座板下的测力单元？", "座板会前倾，座板下的单向测力单元只测垂直于座面的力，算不准竖直方向的体重；底座四角测的是对地总力，减去台架自重就是体重，和座板倾角、手怎么用力都无关。"),
        ("为什么不做成全自动（检测到想起身就抬）？", "按住式更安全、意图明确；压力中心前移作为第二个确认条件，这是借鉴东京大学那把辅助椅。")], todo=[], st="ok"),
 "statemachine": dict(key="出了意外先停住：松手即停、有人坐着才降、离座后停住接人；人走开后才降回齐平。",
   ask=[("人回来时座板在高处怎么坐？", "人离开、踏板也空了几秒后，座板自动降回和床齐平（空载复位），回来时像坐普通椅子一样坐上去。"),
        ("断电怎么办？", "失电制动器抱住，座板停住；拉握把旁的拨杆可以慢慢降，也可以用电池降。")], todo=[], st="ok"),
 "risk": dict(key="六个最重要的风险都有对策：机构全封闭、前倾 ≤ 15°、松手即停、底座测力自检、制动 + 拨杆慢降、和床固定。",
   ask=[("为什么只列六条？", "主 slides 只放最重要的六条；完整风险表（严重度、可能性、检测方式）放附录。"),
        ("座板前倾 15°，坐回时会不会滑下来？", "静力学上摩擦系数大于 tan 15° ≈ 0.27 就不滑；考虑坐回冲击和滑的睡衣，面料按 μ ≥ 0.5 的高摩擦纹理面料选，样件实测。")],
   todo=[("附录：完整风险表（严重度、发生可能性、检测方式、对策）", "角色 4、5", "11/3")], st="part"),
 "verify": dict(key=f"新增一行：座板跟着人走，{nok}/81 不前滑、坐回接得住（竖直 {VS['n_ok']}/81）；机构强度和稳定性复核还在做。",
   ask=[("没有实物，怎么证明设计可行？", "这门课要求的是概念、设计和仿真；我们用模型、手算、FEA 和场景仿真逐条验证，实测列入后续工作。"),
        ("81 个用户是怎么来的？", "三种身高 × 三种胖瘦 × 三种起身习惯 × 三种脚位，组合成 81 人；起身习惯是模型里的代表情况，需要真实动作数据核对。")],
   todo=[("FEA：座板支架、滑块板和固定件在 1.5 倍体重下的应力和变形", "角色 4", "11/3 必须"), ("稳定性用真实质量复核后更新这一行", "角色 4", "11/3")], st="part"),
 "limits": dict(key="二维准静态模型、没有实物；坐垫和面料要样件实测。", ask=[], todo=[], st="ok"),
 "conclusion": dict(key="平时和床一样低，起身时跟着人升得比床高，随时可停。", ask=[], todo=[], st="ok"),
 "appendix": dict(key="附录不讲，被问到时翻出来；新增坐板设计网页。", ask=[], todo=[], st="ok"),
}
# ---------------------------------------------------------------- v5.3: after the Gemini audit of the deck (audit/v2)
RZ = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/release_z.json"))); _z = sorted(v["seat_z"] for v in RZ.values())
ZMED, ZMAX = st.median(_z), max(_z); NW_L = BB["summary"]["bed0.58_L_bar"]["n_worse"]
UPD["whynot"] = dict(key=f"床不用垫高，也能达到抬高床的省力效果（比低床省约 {S_LOW}%，和抬高床相当）；抬高床做不到的是平时脚踩得实、起身全程有托、不往前滑。",
   ask=[("和抬高床只差一点，为什么还要做一台电动设备？", f"它解决的是抬高床的两难：床高了，坐着脚踩不实（0.58 m 的床有 {81 - len(K72)} 位矮个用户踩不实），床低了起身费力。起身台平时 0.42 m，起身时达到抬高床的省力效果；另外起身全程有座板托着，不往前滑，头晕坐回接得住。值不值得，要看目标用户里这些问题有多常见，我们没有这方面的数据。"),
        ("人在约 0.56 m 就离开座板，为什么导轨做到 0.69 m？", f"离座高度因人而异：中位 {ZMED:.2f} m，个子高的到 {ZMAX:.2f} m；没有人用到 0.69 m，顶上约 3 cm 是余量，可以再缩短。离座以后座板就停在那里接人，不会继续往上走。"),
        (f"为什么有 {NW} 个人反而略费力？", f"多是髋部晚往前走、脚放得靠后的人，差得很少（≤ 0.03）；而且这是和每人最有利的扶手位置比，和同一副扶手比只有 {NW_L} 人略差。"),
        ("你们之前说比抬高床省 13–20%？", "那是竖直升到 0.66 米的旧模型（手上最多出 25% 体重、扶手跟着座板升）。换成现在的坐板、固定扶手和同一口径以后不成立，我们改掉了。"),
        ("模型可信吗？", "只用来比较方向和量级：二维准静态，只看最吃力的那一刻，没有动态过程和实测，已写进局限页。")], todo=[], st="ok")
UPD["concept"] = dict(key="坐上 → 握住身前横杆 → 座板跟着大腿走 → 站稳，座板一直接得住人；机构都在床头一侧，床尾敞开（俯视图在第 11 页）。",
   ask=[("要往前挪多远？为什么不能直接坐在座板上？", "座板就紧贴床沿：从床沿内 3 cm 到床沿外 14 cm，和床齐平，后缘软边搭在床垫上。人从床沿往前挪到臀部在座板上，大约 10–20 cm，取决于原来坐得多靠里。是否容易做到要实测，已写进局限。"),
        ("床垫边缘一坐就陷下去，座板会不会比床垫高一截？", "会有这个问题。机构在齐平位以下留了 3 cm 行程，起始高度可以按床垫边缘压陷量设得比床垫面低 0–3 cm。"),
        ("防滑面料会不会让人挪不上去？", "会，这是一对矛盾：挪上去希望滑，起身和坐回希望不滑。目前先用高摩擦面料，挪动难度要样件实测，列入局限。"),
        ("为什么扶手不跟着座板升？", f"跟着升需要再加一套机构；固定的 L 形扶手最简单。横杆在人正前方 x {cm(B['x'])} cm、高 {B['z']:.2f} m，81 位模拟用户坐着都够得着，从坐到站不用换手。")], todo=[], st="ok")
UPD["sizing"] = dict(key=f"滚珠丝杠起身时 ≤ {M['F_lift100_N']} N、猛坐静载 ≤ {M['F_hold100_N']} N；失电制动抱住；双导轨扛住悬臂；应急先用电池，再用带护盖的拨杆。",
   ask=[("滚珠丝杠不自锁，断电怎么办？", f"失电常闭制动器：断电时抱住。先用电池按住“降”慢慢降；控制器也坏了，拉立柱侧面带护盖的拨杆：第一段行程断开电机电源，再松开制动，人的重量把座板压下去，限速约 {E['limiter_speed_mps'] * 100:.0f} cm/s（全程约 {E['time_full_sink_s']:.0f} s），一松手就停。"),
        ("最轻的人坐着能降下来吗？", f"最轻的用户沿导轨的下沉推力约 {E['light_user_drive_N']} N；阻力约 {E['resist_N']} N（丝杠、导轨、毛刷，加电机被反拖的阻力约 {E.get('motor_drag_N', 0)} N，按 0.05 N·m 估，要按电机样本核对），是 {E['margin']} 倍。电机用皮带直连、不加减速器，才拖得动。"),
        ("偏载会不会把丝杠别弯、卡死？", "丝杠装在两根导轨之间，螺母用浮动接头连到滑块板，只传轴向推力；偏载力矩全部由导轨和滑块扛。选型时还要核对滑块的许用力矩。")],
   todo=[("按厂家样本选定滚珠丝杠、直线导轨、制动器和电机型号；核对 3 cm/s 时的电机转速和扭矩、电机反拖阻力", "角色 4", "11/3")], st="part")
UPD["stability"] = dict(key=f"人在台上翻不了；人在地上扶一下横杆，{min(fl.values())} N 就会拉翻，所以台架必须锁在床架或床腿上。俯视图说明怎么走下去、怎么回床。",
   ask=[("重重坐下的冲击呢？", "座板按 1.5 倍体重算，冲击可以取 2–3 倍，之后用 FEA 校核。"),
        ("固定件要多大力？", f"按扶手设计载荷 1112 N（ADA 609）、安全系数 1.5，固定件约需 {anchor} N 的拉力，要锁在床架或床腿上；床垫下的压板拉不住，不用。"),
        ("站起来以后怎么走出去？", "身后是座板、床头一侧是机构箱、身前是横杆，所以转向床尾一侧走下底座；助行器放在那一侧，底座边缘做斜坡。"),
        ("回床怎么回？", "按住“降”把空座板降到和床齐平，坐上去，往后挪回床面，腿向床尾一侧转上床。往后挪对老人可能更难，要实测。")],
   todo=[("用 CAD 的真实质量和质心复核", "角色 4（等角色 3 的 CAD）", "11/3"), ("固定件的具体形式（床腿夹或绕床架的对拉带）", "角色 3、4", "11/3")], st="part")
UPD["sensing"] = dict(key="握紧才升、松手即停；座板测力管速度（按倾角折算）；踏板和横杆确认体重真的转到了脚上；不用底座称重。",
   ask=[("座板前倾时，座板下的测力单元还准吗？", "它测的是垂直于座面的力。丝杠编码器知道当时的倾角（最大 15.7°），控制器把它折算成竖直方向；倾角带来的误差只有几个百分点，自检容差是 15%。"),
        ("为什么不用底座称体重？", "台架和床固定以后，有一部分力经固定件传到床上，底座测不准；人刚坐上时腿还压着床垫，也对不上。所以自检改成：空着时查零点，抬升中座板、踏板、横杆三处力之和约等于体重。"),
        ("为什么不做成全自动（检测到想起身就抬）？", "按住式更安全、意图明确；压力中心前移作为第二个确认条件，这是借鉴东京大学那把辅助椅。")], todo=[], st="ok")
UPD["statemachine"] = dict(key="出了意外先停住：松手即停；只有人按住“降”才往下动（空座板也一样）；久坐不动只提醒、呼叫家属。",
   ask=[("老人在半空晕过去了怎么办？", "座板停住、制动抱住，接住人；系统提醒并呼叫家属，但不会自己把人降下去，因为一个瘫软的人在动着的座板上更容易滑落。"),
        ("人回来时座板在高处怎么坐？", "按住横杆上的“降”，把空座板降到和床齐平，再坐上去往后挪回床面。空座板只在按住时动，避免它自己动时夹到床边的被子或手。"),
        ("往回坐的一瞬间，座板力变小，会不会被当成离座？", "离座要座板力低于 5% 体重并持续 0.3 秒；速度规则用的是低通滤波后的力，坐回的冲击只会让速度变成零。"),
        ("断电怎么办？", "失电制动器抱住，座板停住；用电池按住“降”慢慢降；控制器也坏了，用带护盖的拨杆。")], todo=[("按坐板（0.69 m、带前倾）和新的下降规则重跑控制仿真", "角色 5", "11/3")], st="part")
UPD["speed"] = dict(key="人卸掉多少体重，座板就升多快；座板力下降要伴随踏板力上升才提速，人挂在横杆上就限速。",
   ask=[("人整个挂在横杆上，座板力也会变小，会不会被当成站起来了？", "所以加了一条：座板力下降时，踏板力要相应上升才提速；横杆被往下压得很重时限速。"),
        ("速度公式会不会算出负数？", "限在零到最快速度之间：力超过上限时速度为零，不会倒退。"),
        ("右边的仿真是新方案的吗？", "不是，那是竖直升降版本（升到 0.66 m）。规则是一样的，我们会按坐板的轨迹和倾角重跑。")],
   todo=[("按坐板轨迹和倾角重跑仿真，重画成大字号；只在主页放 2–3 个场景，其余放附录", "角色 5", "11/3")], st="part")
UPD["risk"] = dict(key="六个风险都有对策：机构全封闭、座板后缘软包、前倾 ≤ 16°、松手即停、只有按住才降、自检、电池和拨杆应急、和床固定。",
   ask=[("为什么只列六条？", "主 slides 只放最重要的六条；完整风险表（严重度、可能性、检测方式）放附录。"),
        ("座板前倾 16°，坐回时会不会滑下来？", "全程最大前倾 15.7°。静力学上摩擦系数大于 tan 16° ≈ 0.29 就不滑；考虑坐回冲击和滑的睡衣，面料按 μ ≥ 0.5 选；身前有横杆、脚在踏板上，人也不会直接滑到地上。睡衣和皮肤之间的相对滑动要样件实测。"),
        ("座板降回时，后缘会不会夹到床边的东西？", "座板后缘软包；空座板只在按住“降”时动；下降中电机电流升高（遇阻）就停。")],
   todo=[("附录：完整风险表（严重度、发生可能性、检测方式、对策）", "角色 4、5", "11/3")], st="part")
UPD["verify"] = dict(key=f"第 1 条拆成两项：床不用垫高、省力达到抬高床的水平（比低床省 {S_LOW}%）；座板跟着人走，{nok}/81 不前滑、坐回接得住（竖直 {VS['n_ok']}/81）。",
   ask=UPD["verify"]["ask"], todo=UPD["verify"]["todo"], st="part")
UPD["users"] = dict(key="用户已经和老师确认；第 1 条要求改成：床保持低位、省力达到抬高床的水平、座板跟着大腿走。起身模型按 60 kg、1.60 m，结构按 100 kg × 1.5。",
   ask=[("偏瘫的人能用吗？", "开关一只手就能用，阈值按个人设定；轻度偏瘫可以，但机构箱和立柱在床头一侧，要按健侧手和床的方向选左右镜像的安装。前提是能坐稳。")], todo=[], st="ok")
UPD["limits"] = dict(key="二维准静态模型、没有实物；挪上座板和回床时往后挪要实测；控制仿真还是竖直升降版本。", ask=[], todo=[], st="ok")
UPD["conclusion"] = dict(key="平时和床一样低，起身时跟着大腿托一程，随时可停。", ask=[], todo=[], st="ok")

# ---------------------------------------------------------------- v5.4: fall catch and the seat controller simulation
FCS = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/fall_catch.json")))["summary"]
CSJ = json.load(open(os.path.join(ROOT, "model/calc_v13/controller_seat.json"))); CSK = {x["key"]: x for x in CSJ["scenarios"]}
UPD["whynot"] = dict(key=f"两件事：省力达到抬高床（床不用垫高）；更重要的是腿一软往回坐时接得住——坐板起身全程都接得住（81/81），床只在刚起身的前 {100 * FCS['bed058']['caught_share_med']:.0f}% 接得住。",
   ask=[("扶手不也能防摔吗？", "扶手能抓住、能稳住方向，但撑不住整个人：模型里两手合计最多出 1/4 体重。腿一软时需要有东西在臀部下面，扶手坐不上去。"),
        ("“接得住”是怎么算的？", f"起身过程中任一时刻，假设腿一软、髋部直着往下落，看臀部落点（髋后 4 cm）还在不在座面前缘以内。床：人一站起来，臀部就在床沿外约 {-FCS['bed058']['catch_at_standing_cm_med']:.0f} cm；坐板：离座后停在身后，落点还在前缘以内 {FCS['seat']['catch_at_standing_cm_med']:.1f} cm。"),
        ("如果是往后直挺挺倒呢？", f"那是另一种摔法：髋部一边往下一边往后。床都接得住（人倒回床上）；坐板约 {100 * FCS['seat']['backward_on_seat_med']:.0f}% 落在座板上，其余越过座板后缘落到床上，没有落地，但会碰到后缘，所以后缘做软包。哪种摔法更常见，我们没有数据：晕、腿软更像第一种，往后失去平衡更像第二种。"),
        ("和抬高床只差一点，为什么还要做一台电动设备？", f"省力上和抬高床相当，价值在别处：床不用垫高、脚踩得实（0.58 m 的床有 {81 - len(K72)} 位矮个用户踩不实）；起身全程有托，腿一软时接得住，这是抬高床和扶手都做不到的。"),
        ("人在约 0.56 m 就离开座板，为什么导轨做到 0.69 m？", f"离座高度因人而异：中位 {ZMED:.2f} m，个子高的到 {ZMAX:.2f} m；顶上约 3 cm 是余量，可以再缩短。离座以后座板就停在那里接人。"),
        ("你们之前说比抬高床省 13–20%？", "那是竖直升到 0.66 米的旧模型。换成现在的坐板、固定扶手和同一口径以后不成立，我们改掉了。")], todo=[], st="ok")
UPD["speed"] = dict(key=f"人卸掉多少体重，座板就升多快；按坐板轨迹仿真 {len(CSJ['scenarios'])} 个场景，都落到安全状态。",
   ask=[("人整个挂在横杆上，座板力也会变小，会不会被当成站起来了？", "横杆受压超过 0.3 倍体重就只按 30% 速度升。仿真里这个人借横杆离开了座板，座板就停在原处接人。"),
        ("速度公式会不会算出负数？", "限在零到最快速度之间：力超过上限时速度为零，不会倒退。"),
        ("仿真用的是什么用户？", f"1.60 m 的参考用户，沿坐板的实际轨迹和倾角、固定 L 形扶手，算出他在每个座板位置最多能把座板上的力压到多低。最多发力 0.28 的用户约 {CSK['typical']['seat_off_time_s']:.0f} s 在 {CSK['typical']['seat_off_height']:.2f} m 离座；0.24 的用户站不起来，座板到顶后停住，按住“降”回床面。"),
        ("仿真里改了什么？", "用坐板的轨迹和倾角；去掉了“坐着不动就自动降”和两根立柱同步检查；“还坐着”的门槛从 0.15 降到 0.10 倍体重，因为坐板上的人起身中途可以把座板力降到 0.15，原来的门槛会让他坐偏后不能继续升。")],
   todo=[("把全部 14 个场景的图（controller_seat_all.png）放进附录", "角色 5", "11/3")], st="part")
UPD["statemachine"] = dict(UPD["statemachine"], todo=[], st="ok")
UPD["limits"] = dict(key="二维准静态模型、没有实物；挪上座板和回床往后挪要实测；摔倒方式（腿软、往后倒）要用实测动作核对。", ask=[], todo=[], st="ok")
UPD["conclusion"] = dict(key="床不用垫高，省力达到抬高床；起身全程腿一软都接得住；一个电机，机构封闭在床头一侧；只有按住才往下动。", ask=[], todo=[], st="ok")
UPD["verify"] = dict(UPD["verify"], key=f"第 1 条拆成两项：省力达到抬高床（比低床省 {S_LOW}%）；座板跟着人走，{nok}/81 不前滑、腿一软全程接得住（竖直 {VS['n_ok']}/81）。")

# ---------------------------------------------------------------- v5.5: mechanism slide with the 3-D view
UPD["mechanism"] = dict(UPD["mechanism"], key=f"三维图：机构全在床头一侧的箱子里。3 个转动副 + 1 个移动副：铰点 1 沿导轨走直线，连杆拉住铰点 2，两点定下位置和前倾；电机经皮带带动滚珠丝杠。竖直升降 {VS['n_ok']}/81，曲线 {nok}/81。",
   ask=[("导轨是不是只是为了稳？", "第一根导轨不是：它就是那个移动副，规定铰点 1 只能走直线，丝杠推的也是它；去掉它座板就多一个自由度、定不住。第二根导轨和多出来的滑块才是只为稳：它们不增加约束，只把座板挂在一侧的扭矩变成一对力。"),
        ("皮带是干什么的？", "只是把电机折到丝杠旁边，省长度，传动比约 1:1。把转动变成直线运动的是滚珠丝杠。")] + UPD["mechanism"]["ask"])

# ---------------------------------------------------------------- v5.5b: return height 0.50 m, padded bar end, swing-up bar as an alternative
_RET = ("回床怎么回？", "按住横杆上的“降”，空座板先停在回床高度（默认 0.50 m）；坐上去，比坐到床面高度省约两成力（参考用户 0.32 对 0.40）；坐稳后再按住“降”，带着人降到床面，往后挪回床上，腿向床尾一侧转上床。空座板只在按住时动。")
_BAR = ("横杆在身前，回来、出去会不会挡路？", "会有一点。出去时往床尾一侧走，横杆正好和行走方向平行，是一根扶手；挡的是往正前方直走。回来要从床尾一侧侧身走进座板和横杆之间约 0.46 m 深的空间，助行器进不去，最后一两步扶着横杆走。横杆末端做成圆头软包、带夜光。备选是可掀起的翻转横杆，写在局限页。")
UPD["statemachine"] = dict(UPD["statemachine"], ask=[a for a in UPD["statemachine"]["ask"] if not a[0].startswith("人回来时")] + [_RET])
UPD["stability"] = dict(UPD["stability"], ask=[a for a in UPD["stability"]["ask"] if a[0] != "回床怎么回？"] + [_RET, _BAR])
UPD["limits"] = dict(UPD["limits"], key="二维准静态模型、没有实物；挪上座板要实测；横杆固定，回来要侧身走进约 0.46 m 深的空间（备选：可掀起的横杆）；摔倒方式要用实测动作核对。")

# ---------------------------------------------------------------- v5.6: rise paths reach standing (solve_s fix) + deck audit round 3
FCS = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/fall_catch.json")))["summary"]; FS, F58, F42 = FCS["seat"], FCS["bed058"], FCS["bed042"]
BTJ = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/bed_thigh.json"))); TH = BTJ["thigh_slope_deg"]; RCH = BTJ["reach_from_bed"]
SSJ = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/seat_support_slider.json"))); E0 = SSJ["rows"][0]["E"][SSJ["caps"].index(0.5)]
CSJ = json.load(open(os.path.join(ROOT, "model/calc_v13/controller_seat.json"))); CSK = {x["key"]: x for x in CSJ["scenarios"]}
NWA = BB["summary"]["bed0.58_handle"]["n_worse"]; NWL = BB["summary"]["bed0.58_L_bar"]["n_worse"]
p_ = lambda v: f"{100 * v:.0f}%"
_FIX = ("你们之前说腿一软全程接得住 81/81？", f"那是我们自己查出来的错误：起身路径的求解在大约三分之二处就停了，离座后站直的那一段没算。补全以后，直着往下落时坐板接得住起身的中位 {p_(FS['caught_share_med'])}（每人至少 {p_(FS['caught_share_min'])}），{FS['n_always_caught']}/81 全程；床仍只有前 {p_(F58['caught_share_med'])} 左右。合格人数 81 → {nok}，竖直升降 19 → {VS['n_ok']}。机构没变，只是检查算全了。")
UPD["whynot"] = dict(key=f"省力：比低床省 {S_LOW}%，比抬高床再省约 {S_HB}%（{NWA}/81 略费力），只能说相当或略好。防跌：三种摔法里，坐板几乎不让臀部落到支撑面前面；床在 ①② 里大半程接不住。代价：往后摔会碰座板后缘，要软包。",
   ask=[("“接得住”是怎么算的？", f"起身中任一时刻假设腿一软，看臀部落点（髋后 4 cm）还在不在座面上。算了三种边界摔法：① 髋直着往下落；② 膝盖软、小腿不动，髋绕膝往后下落；③ 整个人绕脚踝直挺挺往后倒。真实的摔倒在它们之间。"),
        ("膝盖一软人是往后坐的，床不就接住了吗？", f"这就是 ②。床要到快站直时才接得住：低床站直时 {F42['knee_end_on']}/81，抬高床 {F58['knee_end_on']}/81；起身中途（大腿还比较平的时候）髋绕膝往后转不了多远，臀部还在床沿外。整个起身过程里，床接得住的阶段中位只有 {p_(F42['knee_on_med'])}（低床）、{p_(F58['knee_on_med'])}（抬高床）。坐板在 ② 里 81 人都不会落到前面：{p_(FS['knee_on_med'])} 的阶段落在座板上，其余落到座板后缘或床上。"),
        ("落在座板前缘附近，座板还前倾 15°，会不会滑下去？", "站直时直着落，落点就在前缘附近（中位在前缘以内约 1 cm），这是坐板最弱的时候，我们不说它一定接得住。静力上摩擦系数大于 tan 16° ≈ 0.29 就不滑，面料按 μ ≥ 0.5 选；人手还握着身前的横杆。真实的冲击和睡衣打滑要样件实测，写在局限页。"),
        ("往后倒会不会砸在座板后缘上？", f"会碰到：③ 里中位 {p_(FS['backward_on_bed_behind_med'])} 的阶段臀部越过座板后缘落到床上，② 快站直时也是。座板和床之间的缝只有 3–7 cm，比臀部窄，人不会掉进去，但会碰到后缘，所以后缘必须软包。"),
        ("扶手不也能防摔吗？", "扶手能抓住、稳住方向，但撑不住整个人：模型里两手合计最多出 1/4 体重。腿一软时需要有东西在臀部下面。"),
        ("和抬高床只差一点，为什么还要做一台电动设备？", f"省力上相当或略好，价值在别处：0.58 m 的床对矮个子偏高，1.50 m 的人坐在床沿、脚踩地，大腿要往下倾约 {TH['1.50_0.58']['med']:.0f}°，近乎半站着（0.42 m 时约 {TH['1.50_0.42']['med']:.0f}°）；起身台平时 0.42 m。另外起身大半程有座板在臀部下面，这是抬高床和扶手做不到的。"),
        (f"为什么有 {NWA} 个人反而略费力？", f"差得很少；而且这是和抬高床“扶手放在对它最有利的位置”比，和同一副 L 形扶手比只有 {NWL} 人略差。"),
        ("人在约 0.57 m 就离开座板，为什么导轨做到 0.69 m？", f"离座高度因人而异：中位 {ZMED:.2f} m，最高 {ZMAX:.2f} m；顶上约 1 cm 是余量。离座以后座板就停在那里接人。"),
        _FIX], todo=[], st="ok")
UPD["concept"] = dict(UPD["concept"], key="坐到床沿、握住横杆 → 拉着横杆挪上和床齐平的座板 → 握紧开关，座板跟着大腿走 → 站稳，座板停住；机构都在床头一侧，床尾敞开。",
   ask=[("往前挪的时候手扶哪里？", f"先握横杆再挪。坐在床沿（髋在床沿上方或往里 5 cm），81 位模拟用户往前倾不超过 30° 都够得着横杆；往里 10 cm 时只有 {RCH['-0.10']}/81。所以第一步是先坐到床沿，抓住横杆，再拉着它往前挪。")]
       + [a for a in UPD["concept"]["ask"] if not a[0].startswith("为什么扶手不跟着")])
UPD["sizing"] = dict(UPD["sizing"], ask=[
        ("滚珠丝杠不自锁，断电怎么办？", f"失电常闭制动器：断电时抱住。先用电池按住“降”慢慢降；控制器也坏了，拉立柱侧面带护盖的拨杆：第一段行程断开电机电源，再松开制动，人的重量把座板压下去。"),
        ("电机都断电了，靠什么把速度限在 3 cm/s？", f"丝杠轴上装一个离心限速器：转得比设定快时，里面的摩擦块被甩出去压住外壳，产生和转速相关的阻力，把座板限在约 {E['limiter_speed_mps'] * 100:.0f} cm/s（丝杠约 {E['screw_rpm_at_limit']} rpm，全程约 {E['time_full_sink_s']:.0f} s）。前面算的 {E['resist_N']} N 阻力只是为了确认最轻的人能让座板开始往下走，限速靠的是限速器。"),
        ("最轻的人坐着能降下来吗？", f"最轻的用户沿导轨的下沉推力约 {E['light_user_drive_N']} N：45 kg、座板上承担 0.75 倍体重、最不利位置的推力系数 0.56，再加座板自重的分量。阻力约 {E['resist_N']} N（丝杠、导轨、毛刷，加电机被反拖约 {E.get('motor_drag_N', 0)} N，要按电机样本核对），是 {E['margin']} 倍。"),
        ("老人自己够得着立柱侧的拨杆吗？", "拨杆主要给家属或护理人员用；老人自己用的是电池按住“降”。控制器也坏了时，坐在半空停住等人来，比自己探身去拉更安全，这和“晕倒时停住、呼叫家属”是同一个思路。"),
        ("偏载会不会把丝杠别弯、卡死？", "丝杠装在两根导轨之间，螺母用浮动接头连到滑块板，只传轴向推力；偏载力矩全部由导轨和滑块扛。选型时还要核对滑块的许用力矩。")])
UPD["sensing"] = dict(UPD["sensing"], ask=[
        ("“三处力之和 ≈ 体重”，体重从哪来？", "在个人设置里输入（推力上限本来就按体重设）；装机时也可以让人站在踏板上、手离开横杆称一次。不用底座称，因为和床固定以后底座测不准。"),
        ("座板只测法向力，前倾时折算得准吗？", f"不完全准：座板和臀部之间还有沿座面的摩擦力，法向力 × cos φ 会漏掉它的竖直分量。最坏按摩擦力刚好让座板合力竖直算，误差是座板力的 1 − cos²φ，15.7° 时约 7%；而座板前倾大的时候人已经卸掉大半体重，折到总体重上只有 2–3%。所以自检容差设 15%、持续 0.5 s 才锁。"),
        ("握着开关不动，老人怎么知道为什么？", "握把上的灯，加一句语音说明原因（比如“请往前坐一点”“脚踩到踏板上”）。夜里低头看不清灯，语音更直接。")]
       + [a for a in UPD["sensing"]["ask"] if a[0].startswith("为什么不做成全自动")])
UPD["statemachine"] = dict(UPD["statemachine"], ask=[a for a in UPD["statemachine"]["ask"] if a[0] != "回床怎么回？"] + [
        ("一直握着“起”，但推不动或到顶了呢？", "座板推力到上限还不动 2 s，或到顶 4 s 仍未离座，就转到“停住”：制动抱住，人可以按住“降”回去。仿真里发力不够的用户就是这样回到床面的。"),
        ("回床时空座板停在 0.50 m，想直接降到床面呢？", "松开再按住“降”，空座板就继续降到床面。比如想直接坐床沿、或者白天整理床铺时用。"),
        ("“降”键坏了怎么办？", "开关用双通道触点，一路坏了能检测出来并报警；按键都失效时，久坐不动 17 s 会自动呼叫家属，家属用立柱侧的拨杆把人慢慢放下来。"),
        _RET])
UPD["speed"] = dict(UPD["speed"], ask=[a for a in UPD["speed"]["ask"] if not a[0].startswith("仿真用的是什么用户")] + [
        ("刚坐着时座板力大于上限，速度不就是 0 吗？", f"是的，这是有意的：坐着时座板承担大半体重，人要先前倾、脚往下踩，把座板力降到上限（0.5 倍体重）以下，座板才开始动。参考用户做到这一步的 effort 约 {E0:.2f}，比放手时（{SSJ['release']['E_free']:.2f}）还低，所以不是难点；也保证了“人不发力，机器不会把人整个抬起来”。"),
        ("仿真用的是什么用户？", f"1.60 m 的参考用户，沿坐板的实际轨迹和倾角、固定 L 形扶手。最多发力 0.28 的用户约 {CSK['typical']['seat_off_time_s']:.0f} s 在 {CSK['typical']['seat_off_height']:.2f} m 离座；0.24 的用户站不起来，座板到顶后停住，按住“降”回床面。")],
   todo=[(f"把全部 {len(CSJ['scenarios'])} 个场景的图（controller_seat_all.png）放进附录", "角色 5", "11/3")])
UPD["stability"] = dict(UPD["stability"], ask=UPD["stability"]["ask"] + [
        ("固定件 2.3 kN 是不是太大？床会不会被拉着走？", "2.3 kN 是按扶手的结构设计载荷（ADA 1112 N × 1.5）定的强度，真人夜里扶一下大多在几百牛以内。固定后要防的是台架翻，不是整体滑：台架加床约 100 kg，地面摩擦按 0.3 算约 300 N 才滑，底座和床脚加防滑垫。另一个做法是把底座伸一块板压在床腿下面，用床的重量压住，不用夹紧床架；具体形式留给 CAD。")])
UPD["risk"] = dict(UPD["risk"], ask=[a for a in UPD["risk"]["ask"] if not a[0].startswith("座板降回时")] + [
        ("座板往下降时夹到手或被子怎么办？", "座板后缘软包；空座板只在按住“降”时动；下降中电机电流升高、或座板测力突然变化（空座板本该几乎为零），就停。带人往下降时，座板下面是机构箱和底座，脚在踏板上，前面没有能被压到的空间。")])
UPD["mechanism"] = dict(UPD["mechanism"], todo=UPD["mechanism"]["todo"] + [("FEA：除了应力，算悬臂座板在 150 kg 偏载下外端的下沉（目标 < 3 mm）", "角色 4", "11/3")])
UPD["verify"] = dict(UPD["verify"], key=f"第 4 页的六条逐条对上，外加“机构放得下”一行。1a：比低床省 {S_LOW}%，比抬高床再省约 {S_HB}%；1b：{nok}/81 不前滑、坐回接得住（竖直 {VS['n_ok']}/81），腿一软起身大半程有座板接住。")
UPD["limits"] = dict(UPD["limits"], key="二维准静态、没有实物；挪上座板和回床往后挪要实测；横杆固定，回来要侧身走进约 0.46 m 的空间；站直时直着摔和往后摔是坐板的弱处（前缘、后缘）。")
UPD["conclusion"] = dict(UPD["conclusion"], key="床不用垫高，省力达到抬高床；腿一软时起身大半程有座板接住；一个电机，机构封闭在床头一侧；只有按住才往下动。")
UPD["users"] = dict(UPD["users"], key="六条设计要求在验证页逐条检查；第 6 条是“只有按住‘降’才往下动”（不是“有人坐着才降”，因为回床时空座板也要降）。")

PILL = dict(ok=("p-ok", "内容齐"), part=("p-part", "部分待补"), gap=("p-gap", "待补"))

def aside(root, sid):
    h = open(os.path.join(root, "project/slides", f"{sid}.html")).read()
    return re.search(r"<aside>(.*?)</aside>", h, re.S).group(1).strip()

def thumb(path):
    im = Image.open(path).convert("RGB"); im = im.resize((560, 315), Image.LANCZOS); b = io.BytesIO(); im.save(b, "WEBP", quality=72)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()

if __name__ == "__main__":
    gin, root, tdir, gout = sys.argv[1:5]; h = open(gin).read()
    thumbs = {re.sub(r"^full_\d+_|\.png$", "", f): os.path.join(tdir, f) for f in os.listdir(tdir) if f.startswith("full_")}
    for sid, u in UPD.items():
        i = h.index(f'<article class="srow" id="s-{sid}"'); j = h.index("</article>", i) + len("</article>"); a = h[i:j]
        a = re.sub(r'<img src="data:image/webp;base64,[^"]+"', f'<img src="{thumb(thumbs[sid])}"', a)
        cls, lab = PILL[u["st"]]; a = re.sub(r'<span class="pill p-[a-z]+">[^<]*</span>', f'<span class="pill {cls}">{lab}</span>', a, count=1)
        a = re.sub(r'(<p class="keyl"><b>这一页要让听众记住：</b>).*?(</p>)', lambda m: m.group(1) + html.escape(u["key"], quote=False) + m.group(2), a, flags=re.S)
        a = re.sub(r'(<p class="say">).*?(</p>)', lambda m: m.group(1) + aside(root, sid) + m.group(2), a, flags=re.S)
        a = re.sub(r'\n  <ul class="todo">.*?</ul>', "", a, flags=re.S)
        a = re.sub(r'\n  <div><p class="lbl">可能被问到</p>.*?</dl></div>', "", a, flags=re.S)
        extra = ""
        if u["todo"]: extra += '\n  <ul class="todo">' + "".join(f'<li><b>待补：</b>{w} <span style="color:var(--muted)">· {who} · {when}</span></li>' for w, who, when in u["todo"]) + "</ul>"
        if u["ask"]: extra += '\n  <div><p class="lbl">可能被问到</p><dl class="qa">' + "".join(f"<dt>{q}</dt><dd>{ans}</dd>" for q, ans in u["ask"]) + "</dl></div>"
        a = a.replace("\n </div>\n</article>", extra + "\n </div>\n</article>")
        a = re.sub(r'data-todo="\d"', f'data-todo="{1 if u["todo"] else 0}"', a, count=1)
        h = h[:i] + a + h[j:]
    # rebuild the to-do table and the count from every article
    rows, n_must = [], 0; todo_ids = set()
    for m in re.finditer(r'<article class="srow" id="s-([a-z]+)".*?</article>', h, re.S):
        sid = m.group(1); a = m.group(0); no = re.search(r'<span class="no">第 (\d+) 页</span><h3>([^<]*)</h3>', a)
        for w, who, when in re.findall(r'<li><b>待补：</b>(.*?) <span style="color:var\(--muted\)">· (.*?) · (.*?)</span></li>', a):
            todo_ids.add(sid); must = "必须" in when; n_must += must
            rows.append(f'<tr><td><a href="#s-{sid}">{no.group(1)} {no.group(2)}</a></td><td>{w}</td><td style="white-space:nowrap">{who}</td><td><span class=\'pill {"p-gap" if must else "p-part"}\'>{when}</span></td></tr>')
    i = h.index('<div class="box scroll"><table><thead><tr><th style="width:20%">在哪一页</th>'); i = h.index("<tbody>", i) + len("<tbody>"); j = h.index("</tbody>", i)
    h = h[:i] + "".join(rows) + h[j:]
    h = re.sub(r'<p class="lab">待补</p><p class="big">\d+ 项</p><p class="d">.*?</p>',
               f'<p class="lab">待补</p><p class="big">{len(rows)} 项</p><p class="d">其中 {n_must} 项 11/3 必须有：CAD（机构箱、双导轨、悬臂支架）、CAD 运动动画、FEA。其余大多是复核和附录。</p>', h, flags=re.S)
    # JSON blob for the builder
    i = h.index("const D={"); j = h.index(";\n", i); D = json.loads(h[i + len("const D="):j])
    for s in D["slides"]: s["todo"] = s["id"] in todo_ids
    h = h[:i] + "const D=" + json.dumps(D, ensure_ascii=False) + h[j:]
    # builder labels: pills follow the to-do flag
    for s in D["slides"]:
        h = re.sub(rf'(<input type="checkbox" id="c-{s["id"]}" data-id="{s["id"]}"><span><b>{s["n"]}</b> {re.escape(s["t"])})( <span class=\'pill p-part\'>待补</span>)?(</span>)',
                   lambda m: m.group(1) + (" <span class='pill p-part'>待补</span>" if s["todo"] else "") + m.group(3), h)
    h = h.replace('<p class="lead">配合 21 页 slides 使用：', '<p class="lead"><b>10/27 更新：</b>座板改为跟着大腿走的单自由度曲线（单侧斜导轨 + 倾角连杆）作为主方案，竖直升降作对比；扶手改为固定的 L 形扶手；机构、选型、稳定性、风险、验证几页随之更新。<br>配合 21 页 slides 使用：', 1)
    h = h.replace("计算数字来自 GitHub 仓库 model/calc_v12；缩略图按 10/26 晚的 slides 渲染；动画是示意，不是 CAD。",
                  "计算数字来自 GitHub 仓库 model/calc_v12（起身模型、控制仿真）和 model/calc_v13（单自由度坐板）；缩略图按 10/27 的 slides 渲染；动画由二维模型画出，是示意，不是 CAD。")
    open(gout, "w").write(h); print("written", gout, len(h), "bytes;", len(rows), "to-dos")
