import json, re
import os
P = os.path.dirname(os.path.abspath(__file__)) + "/"
M = P + "../model/"
b = open(P + "v9_body.html").read()

def rep(s, a, c, n=1):
    assert s.count(a) >= 1, "MISSING: " + a[:100]
    if n == 1:
        assert s.count(a) == 1, "NOT UNIQUE: " + a[:100]
    return s.replace(a, c)
def cut(s, start, end, repl):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + repl + s[j:]

C = json.load(open(M + "compare_v10.json"))
HS = json.load(open(M + "seat_height_v10.json"))
TIP = json.load(open(M + "tipping_v10.json"))
px = C["proxies"]
e = lambda k, d: px[k][d]["effort"]

# ======================= Part 3 intro =======================
b = rep(b, '<b>方案乙 · 床边起身台</b>是在比较“力从哪来”之后发展出来的：床不改，床前放一个与床同高的台架，台面接住人并把骨盆抬高，扶手固定在台架上。',
        '<b>方案乙 · 床边起身台</b>是在比较“力从哪来”之后发展出来的：床不改，床前放一个起身台。老人坐在床沿、脚踩台架的踏板，往前挪到与床齐平的座板上；座板升高并前倾，把骨盆送高；L 形扶手跟着一起升，站直后仍在手边。')

# ======================= dilemma =======================
b = cut(b, '<section id="dilemma">', '<section id="existing">', '''<section id="dilemma">
  <div class="sec-head">
    <div class="eyebrow">关键矛盾</div>
    <h2>床高本身就是一个两难</h2>
    <p class="lead">证据链第 5 环推出：起身的起点有多高，是一个可以设计的变量。但坐着和站起来，对床高的要求正好相反。</p>
  </div>
  <div class="grid3">
    <div class="card ev"><span class="pill fact">指南</span><div class="num">坐着：要低</div><p>坐在床沿时，双脚应平踩地面、膝约 90°；床太高，脚就踩不实。</p><p class="lim">NCOA 的居家防跌建议，属于指南，不是试验证据。按“脚平踩、膝约 90°”换算，1.55–1.60 m 的老人大约是 0.40–0.45 m（按人体尺寸推算）。<span class="c" data-c="ncoa"></span></p></div>
    <div class="card ev"><span class="pill fact">文献</span><div class="num">站起：要高</div><p>12 名 56–90 岁老人从 38 cm 的床上离床，髋部力矩为 58 cm 时的约 1.8 倍，一半人需要明显协助；有跌倒史的老人在低床上起身行走慢得多（6.3 s 对 3.7 s）。</p><p class="lim">医院病床、样本小。<span class="c" data-c="merryweather"></span><span class="c" data-c="christman"></span></p></div>
    <div class="card ev"><span class="pill amber">矛盾</span><div class="num">固定床高只能顾一头</div><p>升降护理床能两头都顾，但要换整张床。起身台只在起身的那一刻把骨盆抬高，平时床照旧。</p><p class="lim">前提是这户人家不打算换床；如果愿意换升降床，那是更简单的答案（见“为什么不直接把床调高”）。</p></div>
  </div>
</section>

''')

# ======================= evidence chain fixes =======================
b = rep(b, '{t:"fact",n:"多数在床边",c:"住院老人无人目击的跌倒，大多发生在床边，其次是卫生间。",l:"英格兰和威尔士的住院报告，原文没有给百分比。",s:"hignett"}',
        '{t:"fact",n:"最常见：床边",c:"住院跌倒报告中，最常见的地点是床边，其次是卫生间。",l:"来自英格兰和威尔士约 21.6 万份住院事故报告，不限于无人目击，也不是居家数据。",s:"hignett"}')
s0 = HS["sens"]
b = rep(b, '{t:"model",n:"−30%",c:"座面从 0.42 m 抬到 0.60 m，膝 + 髋所需力矩之和的降幅（不用手）。",l:"不同建模设定下为 −20% 到 −37%。",s:""}',
        '{t:"model",n:"−22%",c:"座面从 0.42 m 抬到 0.60 m，不用手时 effort（最吃力关节用掉的力量比例）从 0.59 降到 0.46。",l:"不同建模设定下为 −14% 到 −30%；脚完全收不回时，0.42 m 不用手站不起来，0.60 m 可以。",s:""}')
b = rep(b, '{t:"infer",n:"中途必断",c:"站直时肩高约 1.3 m、臂长约 0.62 m，够不到约 0.5 m 高的床垫。",l:"按人体尺寸推算，没有实测。",s:""}',
        '{t:"infer",n:"站直后够不着",c:"站直时肩高约 1.3 m、臂长约 0.62 m，不弯腰就够不到约 0.45 m 高的床垫。",l:"按人体尺寸推算；人可以边起身边松手，所以支撑是“逐渐失去”，没有实测。",s:""}')
b = rep(b, '{t:"fact",n:"0.71–0.84 m",c:"8 名老人自己选择的身前把手高度：站直后仍在手边。",l:"样本很小，只测了坐→站。",s:"bolli2023"}',
        '{t:"fact",n:"座面 +0.25–0.38 m",c:"8 名老人（平均 86 岁）坐在约 0.46 m 高的椅子上，自己选择的身前把手高度为 0.71–0.84 m，即高出座面约 0.25–0.38 m。",l:"样本很小，只测了坐→站；座面变高时要按“高出座面”换算。",s:"bolli2023"}')

# ======================= coverage / prior art =======================
b = rep(b, '["可摆出 / 旋转扶手","Smart-Rail、Arcorail：需手动扳动","smartrail","SSPPPPP-"]', '["可摆出 / 旋转扶手","Smart-Rail、Arcorail：需手动扳动","smartrail arcorail","SSPPPPP-"]')
b = rep(b, '["座垫式助起","UpEasy（气弹簧，无需按钮）、Mangar（充气）：主要用于椅子","upeasy","---PP---"]', '["座垫式助起","UpEasy（气弹簧，无需按钮）、Mangar（充气）：主要用于椅子","upeasy mangar","---PP---"]')
b = rep(b, '["本组方案乙（目标）","床边起身台：扶手近端兼作床栏；斜台接腿 → 平台 → 后高前低抬升","","PSSSSSP-"]',
        '["本组方案乙（目标）","床边起身台：侧扶手兼作一小段床栏；往前挪上座板；座板升高前倾，L 形扶手随升","","PSSSSSP-"]')
b = rep(b, '["Chair-egress 医院床","医院","床变成椅子、座面段前倾抬起，站立把手可自动升起","可按患者状态控制","医院设备，有护士在场","us8640285"],',
        '["Chair-egress 医院床（Hill-Rom）","医院","床变成椅子，座面段绕脚端转轴把后端抬起（egress boost）","按钮或触摸屏","医院设备；没有扶手，也不判断患者状态","us8640285"],\n ["椅式床 + 可收起的站立支撑","医院 / 专利","椅式床两侧的支撑可手动或自动升起，顶端是把手","专利只写“可由传感器电子控制”，没有具体规则","医院椅式床；没有座面抬升","us9265677"],\n ["电动如厕抬升座","产品 / 专利（如 US6360382）","座面升高并后高前低倾斜；扶手随座面升、保持水平","开关或脚踏，由用户或照护者操作","最接近的同类：同样“抬骨盆 + 扶手不离手”；差别在用在床边、要从床上挪过来、由受力互锁启动","us6360382"],')
b = rep(b, '["Panasonic 起身辅助系统","专利（椅子 + 机器人）","扶手受力且座面卸载后，座面升高；有实施例检测到动作就自动开始","扶手、座面测力","椅子 + 配套机器人；不在床边","us10022284"],',
        '["Panasonic 起身辅助系统","专利（椅子 + 机器人）","扶手受力且座面卸载后，座面升高；有实施例检测到动作就自动开始；实施例 17 把机器人换成测力手杖或肘托","扶手、座面测力","椅子，不在床边；“不用机器人”不构成差别","us10022284"],')
b = rep(b, '["SuperBar、Rehastage 把手","产品 / 专利","身前锁定的横把手；或随人起身向外摆的棘轮把手","无","只有扶手，没有座面助力","superbar"]',
        '["SuperBar、Rehastage 把手","产品 / 专利","身前锁定的横把手；或随人起身向外摆的棘轮把手","无","只有扶手，没有座面助力","superbar rehastage"]')
b = rep(b, 'const cite=k=>{const i=KEYS.indexOf(k);return i<0?"":`<a href="${SRC[k][1]}" target="_blank" rel="noopener">[${i+1}]</a>`};',
        'const cite=ks=>(ks||"").split(" ").filter(Boolean).map(k=>{const i=KEYS.indexOf(k);return i<0?"":`<a href="${SRC[k][1]}" target="_blank" rel="noopener">[${i+1}]</a>`}).join("");')
# sources: drop uncited, add new
for k in ["kinoshita", "yosh2007", "fda", "mhlw"]:
    b = re.sub(r'\n ' + k + r':\[[^\n]*\],?', '', b)
b = rep(b, ' aba:["US Access Board, ABA Chapter 3: Protruding Objects (§307.2)","https://www.access-board.gov/aba/guides/chapter-3-protruding-objects/"],',
        ' aba:["US Access Board, ABA Chapter 3: Protruding Objects (§307)","https://www.access-board.gov/aba/guides/chapter-3-protruding-objects/"],\n'
        ' ncoa:["National Council on Aging, Bedroom Safety Tips for Older Adults (2026)","https://www.ncoa.org/article/bedroom-safety-guide/"],\n'
        ' alexander:["Schultz, Alexander, Ashton-Miller 1992, Biomechanical analyses of rising from a chair, J Biomech 25(12)（手力数据引自 Alexander et al. 1991）","https://deepblue.lib.umich.edu/bitstream/2027.42/29713/1/0000047.pdf"],\n'
        ' us6360382:["US6360382 (Karding), Powered toilet seat lift","https://patents.google.com/patent/US6360382"],')

# ======================= matrix stage stances / notes =======================
b = rep(b, 'stance:"方案甲：收起的扶手就是床栏，拉着它翻身坐起。方案乙：起身台扶手靠床的一端紧贴床沿，同样可以拉着坐起。两个方案在这一段都不额外助力。"',
        'stance:"方案甲：收起的扶手就是床栏，拉着它翻身坐起。方案乙：起身台的侧扶手紧贴床沿、比床面高约 0.22 m，拉着它坐起。两个方案在这一段都不额外助力。"')
b = rep(b, 'stance:"方案甲：扶着收起的扶手挪到床沿。方案乙：拉着台架扶手挪到床沿，把腿放上斜台，台面升平后向前挪上台面。"',
        'stance:"方案甲：扶着收起的扶手挪到床沿。方案乙：扶着侧扶手坐到床沿，双脚落在台架踏板上，再往前挪约 25 cm 坐上座板（座板与床齐平）。"')
b = rep(b, 'stance:"扶手是起身台的固定部件，位置永远不变；台架下部是实体，脚先碰到它。"',
        'stance:"两个方案的支撑都在固定、可预测的位置：甲收在床边当床栏；乙是起身台的 L 形扶手。乙的踏板和底座让脚先碰到台架。"')
b = rep(b, 'stance:"坐在硬台面上、握住扶手、脚踩实，才允许抬升；这也给血压留出调整时间。"',
        'stance:"方案甲：握住锁定的扶手坐一会儿。方案乙：坐正、双手握住横杆、双脚踩实踏板并持续约 2 秒，才允许抬升；这也给血压留出调整时间。"')
b = rep(b, 'stance:"核心：台面后段抬高约 18 cm 成后高前低的梯形，把骨盆送高；前缘仍低，脚能平踩。"',
        'stance:"方案甲：扶手锁死，人自己站起。方案乙（核心）：座板升高约 18 cm 并前倾约 15°，把骨盆送高；座板很短，脚可以收到它前缘下方。"')
b = rep(b, 'stance:"扶手是台架的一部分，站直后仍在手边。"', 'stance:"两个方案站直后扶手都在手边。乙：人站在踏板上，手上的力是人和台架之间的内力，台架不会被拉翻。"')
b = rep(b, 'stance:"交接给老人自己的助行器；停靠位放在扶手末端旁边。"', 'stance:"交接给老人自己的助行器。乙：助行器停在前横杆开口的一侧。"')
b = rep(b, '"6-4":["会动的台面在人身上施力时，时机不对就会把人推出去，或者让人向前滑出。设计规则：互锁，只在条件满足时动，并限制前倾角。","infer"]',
        '"6-4":["会动的座面在人身上施力时，时机不对就会把人推出去，或者让人向前滑出。设计规则：互锁，只在条件满足时动；出现异常就缓慢降平，而不是停在高处；限制前倾角。","infer"]')

# ======================= decisions =======================
b = rep(b, '["B","座面抬升 + 手扶平衡","装置，经过骨盆传入","手主要负责平衡；手臂越弱，收益越大","设互锁：握住且踩实才动，松手即停"]],',
        '["B","座面抬升 + 手扶平衡","装置，经过骨盆传入","手主要扶稳；不用手时也能降约 22%","互锁：坐正、握住、踩实才抬；出现异常就缓慢降平"]],')
b = rep(b, 'why:"<b>方案甲</b>让老人自己出力，扶手只负责待在对的位置：简单、安全，但帮多少取决于手臂力量。<b>方案乙</b>把助力改走骨盆：模型显示，手只扶稳时 effort 从 0.49 降到 0.33；手臂有力的人收益较小（−14%），但硬台面比软床垫更稳。"},',
        f'why:"<b>方案甲</b>让老人自己出力，扶手只负责待在对的位置：简单、安全，但帮多少取决于手臂力量；模型里它和撑硬床垫差不多。<b>方案乙</b>把助力改走骨盆：在我们试过的四种手臂假设下，effort 都比撑硬床垫低 12–30%；其中不依赖手臂的那部分（座高本身）约 −22%。"}},')
b = rep(b, '["","床上放座垫（UpEasy 类）","软床垫上会晃","不用","没有","抬起后无支撑"],',
        '["","床上放座垫（UpEasy 类）","为带扶手的椅子设计，放在床上是否稳定未知","不用","没有","抬起后无支撑"],')
b = rep(b, '["B","床边起身台","不依赖：自带硬台面，高度可调","向前挪，台面与床齐平","扶手是台架的一部分","挪动时的接缝、台架移位、被拉翻、占地"]],',
        '["B","床边起身台","不依赖：自带硬座板","坐在床沿往前挪约 25 cm，脚一直踩在踏板上","L 形扶手随座板升","挪动时坐空、离开踏板后被拉翻、占地"]],')
b = rep(b, 'why:"<b>方案甲</b>不做抬升，所以没有床垫和挪动的问题，代价是不减轻腿的负担。<b>方案乙</b>用一个独立台架，同时解决“床垫做不出台阶”和“站起后没有支撑”，代价是多一次挪动、多占地方（见“已知缺点”）。"},',
        'why:"<b>方案甲</b>不做抬升，所以没有床垫和挪动的问题，代价是不减轻腿的负担。<b>方案乙</b>用一个独立台架，同时解决“床垫做不出台阶”和“站起后没有支撑”；人站在台架的踏板上，台架靠人的体重压住。代价是多一次往前挪、多占地方（见“已知缺点”）。"},')

# ======================= stepper: poses, states, drawing =======================
POSE_JS = '''const POSE={
 lie:fillPose({S:[-0.80,0.54],H:[-0.42,0.52],K:[-0.22,0.60],A:[-0.04,0.50],T:[-0.01,0.58],E:[-0.62,0.50],W:[-0.47,0.50]}),
 BsitIn:fillPose({S:[-0.36,0.97],H:[-0.38,0.51],K:[0.01,0.50],A:[0.40,0.48],T:[0.44,0.55],E:[-0.17,0.74],W:[0.06,0.64]}),
 Bedge:fillPose({S:[-0.12,0.97],H:[-0.15,0.51],K:[0.24,0.46],A:[0.24,0.062],T:[0.41,0.02],E:[-0.05,0.72],W:[0.10,0.64]}),
 Bscoot:fillPose({S:[0.17,0.97],H:[0.12,0.51],K:[0.51,0.46],A:[0.51,0.062],T:[0.68,0.02],E:[0.22,0.70],W:[0.36,0.64]}),
 Bready:fillPose({S:[0.28,0.94],H:[0.12,0.51],K:[0.45,0.40],A:[0.28,0.062],T:[0.45,0.02],E:[0.42,0.72],W:[0.62,0.77]}),
 Brise:fillPose({S:[0.384,1.068],H:[0.12,0.69],K:[0.42,0.43],A:[0.28,0.062],T:[0.45,0.02],E:[0.47,0.90],W:[0.62,0.95]}),
 Bstand:{S:[0.31,1.309],H:[0.28,0.848],K:[0.30,0.456],A:[0.28,0.062],T:[0.45,0.02],E:[0.48,1.08],W:[0.62,0.95],E2:[0.50,1.05],W2:[0.74,0.84]},
 AsitIn:fillPose({S:[-0.36,0.97],H:[-0.38,0.51],K:[0.01,0.50],A:[0.02,0.11],T:[0.14,0.06],E:[-0.17,0.94],W:[0.03,0.80]}),
 Asit:fillPose({S:[-0.12,0.97],H:[-0.15,0.51],K:[0.24,0.46],A:[0.16,0.062],T:[0.33,0.02],E:[-0.06,0.84],W:[0.03,0.80]}),
 Aswing:fillPose({S:[-0.04,0.96],H:[-0.15,0.51],K:[0.24,0.46],A:[0.16,0.062],T:[0.33,0.02],E:[0.12,0.84],W:[0.39,0.80]}),
 Aready:fillPose({S:[0.06,0.92],H:[-0.15,0.51],K:[0.24,0.46],A:[0.14,0.062],T:[0.31,0.02],E:[0.22,0.78],W:[0.39,0.80]}),
 Arise:fillPose({S:[0.24,0.95],H:[-0.04,0.60],K:[0.26,0.47],A:[0.14,0.062],T:[0.31,0.02],E:[0.10,0.76],W:[0.39,0.80]}),
 Astand:{S:[0.15,1.309],H:[0.13,0.848],K:[0.15,0.456],A:[0.13,0.062],T:[0.30,0.02],E:[0.30,1.04],W:[0.39,0.80],E2:[0.40,1.06],W2:[0.60,0.84]}
};
'''
STB = f'''const STATES_B=[
 {{k:"睡眠",R:[0,0],pose:"lie",light:0,sens:[],user:"侧躺在床上。",dev:"床不改造（约 0.42 m）。起身台放在床前：座板与床面齐平、紧贴床沿；人站的踏板铺在地上；L 形扶手在一侧。",check:"不动作。",fail:"夜里走动时，脚先碰到踏板的斜边和底座；扶手不伸出底座范围。"}},
 {{k:"翻身坐起",R:[0,0],pose:"BsitIn",light:1,sens:[],user:"侧身，拉着侧扶手靠床的一端翻身坐起，腿越过座板放下。",dev:"不动。侧扶手紧贴床沿、比床面高约 0.22 m，相当于一小段床栏。",check:"不动作。",fail:"拉扶手的力主要朝向床，由床顶住；侧向拉力靠台架自重（约 30 kg 时可承受约 {TIP['sit_up_lateral_pull_N']} N）和与床腿的绑带。"}},
 {{k:"坐到床沿，脚踩踏板",R:[0,0],pose:"Bedge",light:1,sens:["feet"],user:"坐到床沿，双脚落在台架的踏板上，手扶侧扶手。",dev:"不动。座板只有约 18 cm 深，小腿可以从它前面放下。",check:"踏板测到双脚承重（之后的互锁要用）。",fail:"踏板边缘做成斜坡、夜灯照亮踏板，防止绊脚。"}},
 {{k:"往前挪，坐上座板",R:[0,0],pose:"Bscoot",light:1,sens:["seat","feet"],user:"像挪到椅子前沿那样，一点一点往前挪约 25 cm，坐到座板上，脚跟着往前挪。",dev:"不动。座板后缘有唇边压在床垫上，和床垫齐平、没有缝。",check:"座板承重达到坐姿体重的大部分，判定为“已坐上”。",fail:"往后的力由床顶住，台架不会被推开。挪动距离约为平时挪到椅子前沿的 2 倍，目标人群能不能做到要先测（RQ4）。"}},
 {{k:"收脚、握住横杆、停一下",R:[0,0],pose:"Bready",light:1,sens:["seat","bar","feet"],user:"把脚往回收到座板前缘下方，双手握住前横杆，坐着停一会儿（也给血压调整的时间）。",dev:"等待，不抬升。",check:"进入“准备”需要同时满足：座板承重、左右差不超限（静坐时判断）、双手在横杆上、双脚踏板承重，并持续约 2 秒。阈值见 RQ3。",fail:"任何一个条件不满足，就不进入抬升。"}},
 {{k:"抬升：座板升高前倾",R:[0.18,15],pose:"Brise",light:1,sens:["seat","bar","feet"],user:"身体前倾，开始发力站起。",dev:"座板主动升高约 18 cm、前倾约 15°，座面到约 0.60 m。L 形扶手跟着一起升，横杆始终高出座面约 0.35 m。抬升按设定的速度和力上限走完行程：人卸载得早就提前离座；卸不了载，也照样被送高。",check:"抬升中，双手离开横杆，或座板负载异常（往回坐、偏向一侧），立即转为“缓慢降平”：先回到水平，再降回床面高度。",fail:"断电时机构自锁，可以手动缓降。前倾角上限 15°。"}},
 {{k:"站稳 · 交接",R:[0.18,15],pose:"Bstand",light:1,sens:["bar","feet"],user:"站直，扶着横杆站稳几秒，再换手到停在横杆开口一侧的助行器。",dev:"横杆仍在手边。人站在踏板上，手上的力是人和台架之间的内力，台架不会被拉翻。",check:"踏板和座板都没有负载、并持续一段时间后，座板才降回与床齐平。",fail:"人离开踏板后再拉横杆：台架自重约 30 kg 时可承受约 {TIP['off_plate_forward_pull_N']} N 水平拉力；另加床腿绑带。"}}
];
'''
b = cut(b, 'const POSE={', 'const STATES_A=[', POSE_JS + 'POSE.lie=fillPose(POSE.lie);\n' + STB)
b = rep(b, 'check:"—",fail:"模型：手臂弱时 effort 0.49，和撑床垫一样；手臂有力时 0.37。这一下帮得不多。"}',
        f'check:"—",fail:"模型：effort {min(e(k,"A_handle_042") for k in ["P1 cap25","P2 arm x0.5","P3 arm x0.35","strong cap30"]):.2f}–{max(e(k,"A_handle_042") for k in ["P1 cap25","P2 arm x0.5","P3 arm x0.35","strong cap30"]):.2f}（四种手臂假设），和撑硬床垫相当或略差；床垫软时才明显更好。这一下帮得不多。"}}')
b = rep(b, 'fail:"断电时离合脱开，可以用手推着转；承重时机械自锁。"}', 'fail:"转动时可能扫到膝或俯身的头：转动只在手推时发生、低速限扭矩、遇阻即停。断电时离合脱开，可以用手推着转；承重时机械自锁。"}')
b = rep(b, 'const paramsOf=s=>({pose:POSE[s.pose],R:s.R||[0.42,0.42],F:s.F||[0.42,0.42],light:s.light,ps:PSI[s.grip||"front"],hold:s.hold||0});',
        'const paramsOf=s=>({pose:POSE[s.pose],R:s.R||[0,0],light:s.light,ps:PSI[s.grip||"front"],hold:s.hold||0,ikw:s.pose==="lie"?0:1});')
b = rep(b, '  return {pose:p,R:lp2(a.R,b.R,t),F:lp2(a.F,b.F,t),light:lp(a.light,b.light,t),ps:lp(a.ps,b.ps,t),hold:lp(a.hold,b.hold,t)}}',
        '  return {pose:p,R:lp2(a.R,b.R,t),light:lp(a.light,b.light,t),ps:lp(a.ps,b.ps,t),hold:lp(a.hold,b.hold,t),ikw:lp(a.ikw,b.ikw,t)}}')

FIG = '''const LEN={T:0.461,TH:0.392,SH:0.394,U:0.298,F:0.32};
const nrm=v=>{const n=Math.hypot(v[0],v[1])||1;return [v[0]/n,v[1]/n]};
function ik(a,b,l1,l2,hint){let d=[b[0]-a[0],b[1]-a[1]],L=Math.hypot(d[0],d[1])||1e-6;const mx=l1+l2-0.002,mn=Math.abs(l1-l2)+0.002;
  if(L>mx||L<mn){const u=nrm(d),c=L>mx?mx:mn;b=[a[0]+u[0]*c,a[1]+u[1]*c];d=[b[0]-a[0],b[1]-a[1]];L=c}
  const x=(l1*l1-l2*l2+L*L)/(2*L),h=Math.sqrt(Math.max(0,l1*l1-x*x)),u=[d[0]/L,d[1]/L],n=[-u[1],u[0]];
  const p1=[a[0]+u[0]*x+n[0]*h,a[1]+u[1]*x+n[1]*h],p2=[a[0]+u[0]*x-n[0]*h,a[1]+u[1]*x-n[1]*h],dd=p=>Math.hypot(p[0]-hint[0],p[1]-hint[1]);
  return {j:dd(p1)<=dd(p2)?p1:p2,e:b}}
function solve(q,w){if(!(w>0.001))return q;const o=Object.assign({},q);
  const t=nrm([q.S[0]-q.H[0],q.S[1]-q.H[1]]);o.S=lp2(q.S,[q.H[0]+t[0]*LEN.T,q.H[1]+t[1]*LEN.T],w);
  const k=ik(q.H,q.A,LEN.TH,LEN.SH,q.K);o.K=lp2(q.K,k.j,w);o.A=lp2(q.A,k.e,w);o.T=[q.T[0]+o.A[0]-q.A[0],q.T[1]+o.A[1]-q.A[1]];
  const a1=ik(o.S,q.W,LEN.U,LEN.F,q.E);o.E=lp2(q.E,a1.j,w);o.W=lp2(q.W,a1.e,w);
  const a2=ik(o.S,q.W2,LEN.U,LEN.F,q.E2);o.E2=lp2(q.E2,a2.j,w);o.W2=lp2(q.W2,a2.e,w);return o}
function figure(P){const ink=css("--ink"),surf=css("--surface"),q=solve(P.pose,P.ikw==null?1:P.ikw);'''
b = rep(b, 'function figure(P){const ink=css("--ink"),surf=css("--surface"),q=P.pose;', FIG)

DRAWB = '''function drawB(P,i){base(P);const ink=css("--ink"),muted=css("--muted"),edge=css("--edgec"),surf=css("--surface"),line=css("--line"),amber=css("--amber"),bedc=css("--bedc");
  el("text",{x:SX(-0.95),y:SZ(0.12),fill:muted,"font-size":13},"床（不改造，床面 0.42 m）");
  const L=P.R[0],tn=Math.tan(P.R[1]*Math.PI/180),h0=0.42+L,zr=h0+0.12*tn,zf=h0-0.06*tn,zs=0.64+L,zb=0.77+L,t=0.045;
  el("line",{x1:SX(0.62),y1:SZ(0.03),x2:SX(0.62),y2:SZ(0.50),stroke:ink,"stroke-width":8,opacity:.3});
  el("line",{x1:SX(0.62),y1:SZ(0.45),x2:SX(0.62),y2:SZ(zb),stroke:ink,"stroke-width":4,opacity:.55});
  el("line",{x1:SX(0.0),y1:SZ(zs),x2:SX(0.62),y2:SZ(zs),stroke:ink,"stroke-width":4,"stroke-linecap":"round",opacity:.45});
  el("polygon",{points:pts([[0,0],[0.78,0],[0.74,0.025],[0,0.025]]),fill:bedc});
  el("rect",{x:SX(0.0),y:SZ(0.30),width:SX(0.16)-SX(0),height:SZ(0.025)-SZ(0.30),fill:bedc,rx:3});
  el("rect",{x:SX(0.05),y:SZ(h0-0.05),width:SX(0.11)-SX(0.05),height:Math.max(0,SZ(0.30)-SZ(h0-0.05)),fill:bedc});
  el("polygon",{points:pts([[-0.03,zr],[0,zr],[0.18,zf],[0.18,zf-t],[0,zr-t],[-0.03,zr-0.012]]),fill:edge});
  el("text",{x:SX(0.012),y:SZ(0.17),fill:muted,"font-size":11.5},"起身台");
  el("text",{x:SX(0.53),y:SZ(0.06),fill:muted,"font-size":11.5},"踏板");
  walker(0.67);figure(P);
  el("circle",{cx:SX(0.62),cy:SZ(zb),r:7,fill:ink});
  el("text",{x:16,y:26,fill:ink,"font-size":12.5},"L 形扶手：侧边段 + 前横杆，随座板一起升");
  el("text",{x:16,y:46,fill:muted,"font-size":11.5,"font-family":css("--font-mono")},"座面 "+h0.toFixed(2)+" m · 前倾 "+P.R[1].toFixed(0)+"° · 床面 0.42 m");
  if(i>=0)sensors(STATES_B[i].sens,{seat:[0.09,h0+0.012],bar:[0.62,zb+0.035],feet:[0.40,0.035]});
  const TX=u=>510+u*125,TY=v=>94+v*125;
  el("rect",{x:452,y:6,width:182,height:170,rx:8,fill:surf,stroke:line,"stroke-width":1});
  el("text",{x:596,y:24,fill:muted,"font-size":11.5},"俯视");
  el("rect",{x:TX(-0.38),y:TY(-0.6),width:TX(0)-TX(-0.38),height:TY(0.3)-TY(-0.6),fill:css("--matc"),rx:4});
  el("text",{x:TX(-0.34),y:TY(-0.45),fill:muted,"font-size":10.5},"床");
  el("rect",{x:TX(0),y:TY(-0.28),width:TX(0.78)-TX(0),height:TY(0.28)-TY(-0.28),fill:bedc,rx:3});
  el("rect",{x:TX(0),y:TY(-0.22),width:TX(0.18)-TX(0),height:TY(0.22)-TY(-0.22),fill:edge,rx:2});
  el("polyline",{points:[[0,-0.28],[0.62,-0.28],[0.62,0.12]].map(p=>TX(p[0])+","+TY(p[1])).join(" "),fill:"none",stroke:ink,"stroke-width":4,"stroke-linecap":"round","stroke-linejoin":"round"});
  el("path",{d:`M${TX(0.58)} ${TY(0.47)} L${TX(0.58)} ${TY(0.31)} L${TX(0.78)} ${TY(0.31)} L${TX(0.78)} ${TY(0.47)}`,fill:"none",stroke:muted,"stroke-width":2});
  el("text",{x:TX(0.47),y:TY(0.56),fill:muted,"font-size":10},"助行器");
  if(P.pose.S[1]<0.75){el("line",{x1:TX(-0.2),y1:TY(-0.5),x2:TX(-0.2),y2:TY(0.22),stroke:ink,"stroke-width":7,"stroke-linecap":"round"});el("circle",{cx:TX(-0.2),cy:TY(-0.54),r:7,fill:surf,stroke:ink,"stroke-width":2.5})}
  else{const hu=P.pose.H[0];el("line",{x1:TX(hu),y1:TY(0),x2:TX(Math.max(hu+0.2,P.pose.K[0]+0.05)),y2:TY(0),stroke:ink,"stroke-width":7,"stroke-linecap":"round"});el("circle",{cx:TX(hu-0.02),cy:TY(0),r:8,fill:surf,stroke:ink,"stroke-width":2.5})}
  el("path",{d:`M${TX(-0.15)} ${TY(0.19)} L${TX(0.10)} ${TY(0.19)}`,stroke:amber,"stroke-width":2,"stroke-dasharray":"4 3",fill:"none"});
  el("path",{d:`M${TX(0.10)} ${TY(0.19)} l-7 -4 l0 8 z`,fill:amber});
  el("text",{x:TX(-0.37),y:TY(0.42),fill:muted,"font-size":10},"往前挪约 25 cm");
}
'''
b = cut(b, 'function drawB(P,i){', 'function drawA(P,i){', DRAWB)
b = rep(b, '  walker(0.85);\n  const q=Object.assign({},P.pose,{W:lp2(P.pose.W,grip,P.hold)});', '  walker(0.55);\n  const q=Object.assign({},P.pose,{W:lp2(P.pose.W,grip,P.hold)});')
b = rep(b, '"轻推扶手才会转；黄点 = 传感器":"橙色 = 可动台面；黄点 = 传感器"', '"轻推扶手才会转；黄点 = 传感器":"橙色 = 可动座板；黄点 = 传感器"')
b = rep(b, '<span class="muted" style="font-size:12.5px" id="sceneKey">橙色 = 可动台面；黄点 = 传感器</span>', '<span class="muted" style="font-size:12.5px" id="sceneKey">橙色 = 可动座板；黄点 = 传感器</span>')
b = rep(b, 'aria-label="床、抬升段、把手、助行器和老人的侧视示意图"', 'aria-label="床、起身台、扶手、助行器和老人的侧视示意图，右上角为俯视图"')

b = rep(b, 'el("text",{x:SX(0.06),y:SZ(0.80)-16,fill:ink,"font-size":12.5},P.ps<-45?', 'el("text",{x:16,y:26,fill:ink,"font-size":12.5},P.ps<-45?')
b = rep(b, 'el("text",{x:SX(wx-0.02),y:SZ(0.9),fill:muted,"font-size":12},"助行器");', 'el("text",{x:SX(wx+0.25),y:SZ(0.03),fill:muted,"font-size":12},"助行器");')
# ======================= compare section =======================
b = cut(b, '<section id="compare">', '<section id="explorerA">', f'''<section id="compare">
  <div class="sec-head"><div class="eyebrow">方案对比</div><h2>动态扶手和起身台，差在哪里</h2>
    <p class="lead">两个方案都让“手边一直有支撑”，区别在站起那一下：动态扶手只能提供反作用力，帮多少取决于手臂力量；起身台把骨盆抬高，直接减轻腿的负担。我们不知道哪种“手臂弱”的表示最接近真实老人，所以四种都算。</p></div>
  <div class="two">
    <div class="card chart"><div class="legend" id="cmpLegend"></div><svg id="cmpchart" viewBox="0 0 640 340" role="img" aria-label="四种手臂假设下，撑床垫、方案甲、方案乙的 effort 柱状图"></svg></div>
    <div class="card readout">
      <h3>怎么读这张图</h3>
      <p style="font-size:14px">effort 是最吃力的关节用掉了自己最大力量的几成，越低越轻松。“撑床垫”是老人在 0.42 m 的低床上双手撑床垫；实心柱把床垫当成刚性的（对床垫有利），虚框是软床垫（手上最多 15% 体重）。每个方案的扶手都放在它自己最省力的位置。</p>
      <p style="font-size:14px"><b>方案乙</b>在四组里都最低：比撑硬床垫低 12–30%，比方案甲低 24–33%。</p>
      <p style="font-size:14px"><b>方案甲</b>和撑硬床垫差不多或略差：向前抓扶手主要靠肩发力，撑在髋旁的床垫用的是伸直的手臂。床垫软的时候，甲才明显更好。</p>
      <p style="font-size:14px"><b>不依赖手臂的部分</b>：不用手时，座高从 0.42 m 到 0.60 m，effort 从 0.59 降到 0.46（−22%）。</p>
      <p style="font-size:13px;color:var(--ink2)">旧版用“手上最多 10% 体重”代表手臂弱。在这个假设下，扶手放在哪里结果都一样，比较不出方案甲和床垫的差别，所以弃用。</p>
    </div>
  </div>
  <div class="scroll-x"><table class="t" id="cmpT"></table></div>
</section>

''')
CMPD = {"none042": C["none"]["0.42"]["effort"], "none060": C["none"]["0.6"]["effort"],
        "groups": [[lab, sub, {"mr": e(k, "mattress_rigid"), "ms": e(k, "mattress_soft"), "A": e(k, "A_handle_042"), "B": e(k, "B_bar_060")}]
                   for lab, sub, k in [["手力上限 25%", "按老人实测", "P1 cap25"], ["肩肘力量 ×0.5", "手力上限 30%", "P2 arm x0.5"],
                                       ["肩肘力量 ×0.35", "手力上限 30%", "P3 arm x0.35"], ["手臂正常", "手力上限 30%", "strong cap30"]]]}
rngA = [min(g[2]["A"] for g in CMPD["groups"]), max(g[2]["A"] for g in CMPD["groups"])]
rngB = [min(g[2]["B"] for g in CMPD["groups"]), max(g[2]["B"] for g in CMPD["groups"])]
CMPJS = '''const CMP=''' + json.dumps(CMPD, ensure_ascii=False) + ''';
(function(){const svgc=$("#cmpchart"),W=640,H=340,m={l:52,r:96,t:22,b:62};
  const bars=[["撑床垫（实心 = 硬，虚框 = 软）","mr","--muted"],["方案甲：动态扶手","A","--s1"],["方案乙：起身台","B","--amber"]];
  $("#cmpLegend").innerHTML=bars.map(b=>`<span><i style="background:var(${b[2]});height:10px;width:10px"></i>${b[0]}</span>`).join("");
  const ymax=0.65,py=v=>m.t+(ymax-v)/ymax*(H-m.t-m.b);const ng=CMP.groups.length,gw=(W-m.l-m.r)/ng,bw=32,gap=7;
  function draw(){svgc.innerHTML="";const g=(t,a,c)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(c!=null)e.textContent=c;svgc.appendChild(e);return e};
    const muted=css("--muted"),ink2=css("--ink2"),ln=css("--line"),ink=css("--ink");
    for(let v=0;v<=0.61;v+=0.2){g("line",{x1:m.l,x2:W-m.r,y1:py(v),y2:py(v),stroke:ln});g("text",{x:m.l-8,y:py(v)+4,"text-anchor":"end","font-size":12,fill:muted,"font-family":css("--font-mono")},v.toFixed(1))}
    [[CMP.none042,"0.42 m"],[CMP.none060,"0.60 m"]].forEach(([v,lab])=>{g("line",{x1:m.l,x2:W-m.r+6,y1:py(v),y2:py(v),stroke:muted,"stroke-dasharray":"5 4"});
      g("text",{x:W-m.r+10,y:py(v)-3,"font-size":11.5,fill:ink2},"不用手");g("text",{x:W-m.r+10,y:py(v)+12,"font-size":11,fill:ink2,"font-family":css("--font-mono")},lab+" "+v.toFixed(2))});
    CMP.groups.forEach(([lab,sub,d],gi)=>{const x0=m.l+gi*gw+(gw-(3*bw+2*gap))/2;
      bars.forEach(([bl,bk,c],bi)=>{const v=d[bk],x=x0+bi*(bw+gap);
        if(bk==="mr")g("rect",{x:x+1,y:py(d.ms),width:bw-2,height:py(v)-py(d.ms),fill:"none",stroke:muted,"stroke-dasharray":"3 3","stroke-width":1.5,rx:3});
        g("rect",{x:x,y:py(v),width:bw,height:py(0)-py(v),fill:css(c),rx:4});
        if(bk==="mr"){g("text",{x:x+bw/2,y:py(d.ms)-5,"text-anchor":"middle","font-size":11,fill:muted,"font-family":css("--font-mono")},d.ms.toFixed(2));
          g("text",{x:x+bw/2,y:py(v)+15,"text-anchor":"middle","font-size":11,fill:css("--surface"),"font-family":css("--font-mono")},v.toFixed(2))}
        else g("text",{x:x+bw/2,y:py(v)-5,"text-anchor":"middle","font-size":11.5,fill:ink,"font-family":css("--font-mono")},v.toFixed(2))});
      g("text",{x:m.l+gi*gw+gw/2,y:H-m.b+20,"text-anchor":"middle","font-size":12.5,fill:ink},lab);
      g("text",{x:m.l+gi*gw+gw/2,y:H-m.b+37,"text-anchor":"middle","font-size":11.5,fill:muted},sub)});
    g("text",{x:14,y:m.t+6,"font-size":12.5,fill:ink2,transform:`rotate(-90 14 ${m.t+6})`,"text-anchor":"end"},"effort（越低越省力）");}
  draw();window.__cmpDraw=draw;
  const rows=[
   ["核心思路","扶手装在床上，平时当床栏；坐到床沿后轻推一下，扶手带着手转到工作角度（约 0.8 m 高），一用力就锁死","床前起身台：坐在床沿、脚踩踏板，往前挪上与床齐平的短座板；座板升高并前倾，把骨盆送高；L 形扶手随座板升"],
   ["解决什么","支撑一直在手边：找得到，站直后也够得着","同左，并且直接减轻腿的负担"],
   ["站起那一下（模型 effort）","RNGA（四种手臂假设）；和撑硬床垫相当或略差","RNGB；比撑硬床垫低 12–30%，比方案甲低 24–33%"],
   ["对手臂的要求","帮多少，取决于手臂力量","不用手时也降约 22%（座高本身）；手再帮一部分"],
   ["要不要挪动","不用","要：坐在床沿往前挪约 25 cm，脚一直踩在踏板上（改进方向 A 可以免掉）"],
   ["运动部件与传感","1 个：扶手摆动；只需扶手测力","座板升高 + 前倾（目标一个驱动），扶手随升；座板、横杆、踏板测力"],
   ["床的依赖","要固定在床架上","不依赖；台架靠住床，人站在踏板上压住台架"],
   ["占地","小","约 0.56 × 0.78 m（含踏板）"],
   ["主要风险","转动时扫到膝或头、夹手、展开后挡路","抬升时机、中止后怎么降、往前挪时坐空、离开踏板后被拉翻"],
   ["最接近的现有产品","SuperBar（身前固定横把手）、Smart-Rail（手动摆出）、Rehastage（被动跟随）","电动如厕抬升座（抬骨盆 + 扶手随升）、升降躺椅、UpEasy、升降护理床"],
   ["差别靠什么","“轻推即转、承重即锁”的交互，依赖“老人夜里做不好手动解锁和扳动”的假设，目前没有证据","组合差别：不换床 + 站起后支撑不中断 + 受力互锁的主动抬升、异常即降平"],
   ["12 天工作量","小：一个摆动机构 + 简单传感","大：座板机构 + 互锁 + 倾翻计算"],
   ["结论","实现简单，但站起那一下帮得不多","<b>推荐</b>：模型在四种手臂假设下都最省力；代价是多一次往前挪、机构更复杂"]];
  $("#cmpT").innerHTML=`<thead><tr><th>维度</th><th>方案甲 · 动态扶手</th><th>方案乙 · 床边起身台</th></tr></thead><tbody>`+rows.map((r,i)=>`<tr${i===rows.length-1?' class="pick"':''}><th>${r[0]}</th><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")+`</tbody>`;
})();
'''.replace("RNGA", f"{rngA[0]:.2f}–{rngA[1]:.2f}").replace("RNGB", f"{rngB[0]:.2f}–{rngB[1]:.2f}")
b = cut(b, 'const CMP={', '/* scheme A explorer */', CMPJS + '\n')

# ======================= explorer A =======================
b = rep(b, '<button data-a="weak" aria-pressed="false">手臂弱<br><span style="font-size:11.5px;opacity:.75">手上 ≤ 10% 体重</span></button>',
        '<button data-a="weak" aria-pressed="false">手臂弱<br><span style="font-size:11.5px;opacity:.75">肩肘力量 ×0.5</span></button>')
b = rep(b, '<p style="font-size:14.5px"><b>这张图说明了方案甲的天花板：</b>同样手数时，身前扶手和床沿扶手差别不大；而且手臂越弱，扶手能帮的越少。手臂弱时，最好的扶手位置也只和撑床垫差不多。扶手的价值主要在“站直以后手边还有东西”，而不是“站起那一下更省力”。</p>',
        '<p style="font-size:14.5px"><b>这张图说明了方案甲的天花板：</b>同样手数时，身前扶手和床沿扶手差别不大；最好的扶手位置也只和撑硬床垫差不多，手臂弱时还略差，因为向前抓扶手主要靠肩发力，而撑在髋旁的床垫用的是伸直的手臂。扶手的价值主要在“站直以后手边还有东西”，而不是“站起那一下更省力”。</p>')
b = rep(b, '<li>“手上最多承担多少体重”是一个假设参数（10% / 30%），它决定了扶手能帮多少。</li>',
        '<li>“手臂弱”用肩、肘力量打五折表示，手上最多仍可承担 30% 体重。旧版用“手上最多 10% 体重”，那个假设下扶手放在哪里结果都一样，已弃用。</li>')

# ======================= height section =======================
b = rep(b, '<p class="lead">拖动滑块，或者把鼠标移到图上。三条线是三种起身方式：不用手；双手撑床垫（手上承担约 30% 体重）；手只扶住扶手保持平衡（手上只承担约 10% 体重，相当于手臂没力气的老人）。基线是 0.42 m 的低床。</p>',
        '<p class="lead">拖动滑块，或者把鼠标移到图上。三条线：不用手；双手扶身前横杆，按两种手臂假设（手上最多 25% 体重 / 肩肘力量打五折）。横杆在每个座高都放在最省力的位置（高出座面 0.25–0.45 m）。脚可以往回收，但不能收进升降机构下面（脚跟至少在髋前 8 cm）。基线是 0.42 m 的低床。</p>')
b = rep(b, '<div class="legend"><span><i style="background:var(--s1)"></i>不用手</span><span><i style="background:var(--s2)"></i>双手撑床垫</span><span><i style="background:var(--s3)"></i>手只扶稳</span>',
        '<div class="legend"><span><i style="background:var(--s1)"></i>不用手</span><span><i style="background:var(--s2)"></i>扶横杆 · 上限 25%</span><span><i style="background:var(--s3)"></i>扶横杆 · 肩肘 ×0.5</span>')
b = rep(b, '<div><div class="muted" style="font-size:12.5px">不用手时，膝 + 髋所需力矩之和，与 0.42 m 相比</div><div class="big" id="hcmp"></div></div>',
        '<div><div class="muted" style="font-size:12.5px">不用手时的 effort，与 0.42 m 相比</div><div class="big" id="hcmp"></div></div>')
b = rep(b, '<p style="font-size:13px;color:var(--ink2)">effort：最吃力的关节用掉了自己最大力量的几成。力矩为每条腿，单位 N·m/kg。</p>',
        '<p style="font-size:13px;color:var(--ink2)">effort：最吃力的关节用掉了自己最大力量的几成。</p>')
sv = HS["sens"]
effs = [sv[k]["eff"] for k in sv if "eff" in sv[k]]
b = cut(b, '<div class="grid3">\n    <div class="card ev"><span class="pill model">本组模型</span><div class="num">−30%</div>', '<details class="fold">\n    <summary><span class="st">模型的简化与局限</span>',
        f'''<div class="grid3">
    <div class="card ev"><span class="pill model">本组模型</span><div class="num">−22%</div><p>座面从 0.42 m 抬到 0.60 m，不用手时 effort 从 0.59 降到 0.46。这部分不依赖手臂力量。</p><p class="lim">换不同设定（坐姿参数、体型、脚能否收进座下）为 −{-max(effs)*100:.0f}% 到 −{-min(effs)*100:.0f}%。脚完全收不回时，0.42 m 不用手站不起来，0.60 m 可以。</p></div>
    <div class="card ev"><span class="pill model">本组模型</span><div class="num">{e("P1 cap25","mattress_rigid"):.2f} → {e("P1 cap25","B_bar_060"):.2f}</div><p>手上最多 25% 体重时：0.42 m 撑硬床垫 {e("P1 cap25","mattress_rigid"):.2f}，起身台扶横杆 {e("P1 cap25","B_bar_060"):.2f}（−30%）。肩肘力量打五折时 {e("P2 arm x0.5","mattress_rigid"):.2f} → {e("P2 arm x0.5","B_bar_060"):.2f}（−12%）。</p><p class="lim">25% 的依据：起身困难的老年女性（11 人）用扶手时，双手合力峰值约 159 N，对 60–65 kg 的人约为体重的 25%（体重原文未报告）。<span class="c" data-c="alexander"></span></p></div>
    <div class="card ev"><span class="pill fact">老人实测</span><div class="num">48.2 → 27.5 N·m</div><p>12 名 56–90 岁老人，床高从 38 cm 换到 58 cm，离床时髋部力矩明显下降；一半人无法在没有明显协助的情况下从 38 cm 的床上站起。方向与模型一致。</p><p class="lim">力矩为静态建模估算，完成离床分析的只有 6 人。<span class="c" data-c="merryweather"></span></p></div>
  </div>
  ''')
b = rep(b, '''      <li>小腿前倾角在 5°–30° 之间自由选取，多数情况取到 30° 的上限，说明模型偏好把脚往回收。所以起身台前缘下方要留踢脚凹位。</li>
      <li>座面在模型里是水平的。“后高前低”的梯形能让骨盆抬高、前缘仍低，但前倾的效果还没有建模（RQ1）。</li>
      <li>和文献只能说“量级一致、方向一致”：Yoshioka 2014 测的是 8 名年轻人（40 cm 对 60 cm 时力矩为 1.7 倍），换不同设定后，模型的这个比值在 1.1–1.8 倍之间。<span class="c" data-c="yosh2014"></span></li>''',
        f'''      <li>模型偏好把脚往回收。床边：脚跟最多伸进床沿下 5 cm；起身台：脚跟至少在髋前 8 cm（升降机构在髋下方，座板前缘下方是空的）。在 0.60 m 时这个限制起作用，小腿前倾最多约 15–20°。如果脚完全收不回（小腿前倾 ≤ 10°），起身台仍比撑硬床垫低 12–28%。</li>
      <li>座面在模型里是水平的。离座那一刻座面已经不受力，所以前倾只通过改变髋的位置起作用；要评估前倾，需要做离座前（座面仍受力）阶段的模型（RQ1）。</li>
      <li>和文献只能说“方向一致”：Yoshioka 2014 测的是 8 名年轻人，40 cm 对 60 cm 时力矩为 1.7 倍；模型不用手时 0.42 对 0.60 m 的膝 + 髋力矩之和为 {min(sv[k]["ratio"] for k in sv if "ratio" in sv[k]):.2f}–{max(sv[k]["ratio"] for k in sv if "ratio" in sv[k]):.2f} 倍。<span class="c" data-c="yosh2014"></span></li>
      <li>“手臂弱”有两种表示（手力上限、肩肘力量打折），结果不同，所以对比图四种都给出。</li>''')
HJS_OLD_START = 'const SER=[["none","--s1","不用手"],["mattress","--s2","双手撑床垫"],["handle10","--s3","手只扶稳"]];'
b = rep(b, HJS_OLD_START, 'const SER=[["none","--s1","不用手"],["bar25","--s2","扶横杆 · 上限 25%"],["barweak","--s3","扶横杆 · 肩肘 ×0.5"]];')
b = rep(b, '''function hread(idx){const n=HD.none[idx],mm=HD.mattress[idx],hh=HD.handle10[idx],n0=HD.none[BI];$("#hv").textContent=n.h.toFixed(2);
  const s=x=>x.knee+x.hip,pc=((s(n)/s(n0)-1)*100).toFixed(0);''',
        '''function hread(idx){const n=HD.none[idx],mm=HD.bar25[idx],hh=HD.barweak[idx],n0=HD.none[BI];$("#hv").textContent=n.h.toFixed(2);
  const pc=((n.effort/n0.effort-1)*100).toFixed(0);''')
b = rep(b, '''$("#hrows").innerHTML=`<span>不用手 · effort</span><span class="v">${n.effort.toFixed(2)}</span><span>不用手 · 膝 + 髋</span><span class="v">${s(n).toFixed(2)}</span><span>撑床垫 · effort</span><span class="v">${mm.effort.toFixed(2)}</span><span>手只扶稳 · effort</span><span class="v">${hh.effort.toFixed(2)}</span><span>不用手 · 躯干前倾</span><span class="v">${n.trunk}°</span>`;hdraw(idx)}''',
        '''$("#hrows").innerHTML=`<span>不用手 · effort</span><span class="v">${n.effort.toFixed(2)}</span><span>扶横杆 · 上限 25%</span><span class="v">${mm.effort.toFixed(2)}</span><span>扶横杆 · 肩肘 ×0.5</span><span class="v">${hh.effort.toFixed(2)}</span><span>不用手 · 躯干前倾</span><span class="v">${n.trunk}°</span><span>不用手 · 小腿前倾</span><span class="v">${n.shank}°</span>`;hdraw(idx)}''')
b = rep(b, 'tip.style.top=(py(HD.handle10[idx].effort)/Hh*r.height+40)+"px";', 'tip.style.top=(py(HD.barweak[idx].effort)/Hh*r.height+40)+"px";')
b = rep(b, 'tip.textContent=`${HD.none[idx].h.toFixed(2)} m · 不用手 ${HD.none[idx].effort.toFixed(2)} · 撑床垫 ${HD.mattress[idx].effort.toFixed(2)} · 只扶稳 ${HD.handle10[idx].effort.toFixed(2)}`});',
        'tip.textContent=`${HD.none[idx].h.toFixed(2)} m · 不用手 ${HD.none[idx].effort.toFixed(2)} · 上限 25% ${HD.bar25[idx].effort.toFixed(2)} · 肩肘 ×0.5 ${HD.barweak[idx].effort.toFixed(2)}`});')

# ======================= delta =======================
b = cut(b, '<div class="grid3">\n    <div class="card ev"><span class="pill amber">问 · 方案甲</span>', '<section id="risk">', f'''<div class="grid2">
    <div class="card ev"><span class="pill amber">问 · 两个方案</span><div class="num" style="font-size:18px">为什么不直接把床调高？</div><p>坐在床沿时，脚要能平踩、膝约 90°，对 1.55–1.60 m 的老人约是 0.40–0.45 m；站起来更省力的高度却在 0.55–0.60 m。固定的床高只能照顾一头。升降护理床可以两头都顾，但要换整张床（例如 EZ Lift 约 2,200 美元）。起身台只在起身的那一刻把骨盆抬高，平时床照旧。如果用户愿意换升降床，那是更简单的答案；我们针对的是不换床的家庭。<span class="c" data-c="ncoa"></span><span class="c" data-c="ezlift"></span></p></div>
    <div class="card ev"><span class="pill amber">问 · 方案甲</span><div class="num" style="font-size:18px">为什么不用 SuperBar 或可摆出的床栏？</div><p>SuperBar 固定在身前，躺着时不在手边，而且一直挡在床前；可摆出的床栏要老人自己去扳。动态扶手不用找锁扣：轻推就转、一用力就锁，转动由电机辅助。但这个差别依赖一个还没有证据的假设：老人夜里做不好手动解锁和扳动。<span class="c" data-c="superbar"></span></p></div>
    <div class="card ev"><span class="pill amber">问 · 方案乙</span><div class="num" style="font-size:18px">为什么不在床沿放一个 120 美元的气弹簧座垫？</div><p>厂商说明它为带扶手的椅子设计；放在床垫上是否稳定，是我们的推断。它的气弹簧在人开始起身时才释放，所以卸不了载的人得不到帮助，而且没有扶手。起身台是主动推，只在“坐正 + 握住横杆 + 踩实踏板”时启动，扶手随座板升。<span class="c" data-c="upeasy"></span></p></div>
    <div class="card ev"><span class="pill amber">问 · 方案乙</span><div class="num" style="font-size:18px">为什么不用电动升降躺椅或如厕抬升座？</div><p>安大略省的审查记录了 3 起死亡：都是痴呆老人，用遥控器把躺椅升到站立位置后，在无人目击时摔倒；报告把风险归于个人和环境因素，“站起后手边没有支撑”是我们的推断。电动如厕抬升座和我们最像（抬骨盆、扶手随座面升），但用在马桶上、靠开关启动。起身台用在床边，由受力互锁启动，异常时降平。<span class="c" data-c="liftchair"></span><span class="c" data-c="us6360382"></span></p></div>
  </div>
  <div class="card delta"><h3>方案乙能诚实宣称的差别（一个组合，而不是某一项“首创”）</h3><ol>
    <li><strong>不换床</strong>：床前独立台架，座板与床齐平；台架靠住床，人站在踏板上压住台架，不依赖床垫形状。</li>
    <li><strong>起身后支撑不中断</strong>：L 形扶手和座板一起升，针对升降躺椅“抬起后无支撑”的问题。电动如厕抬升座也做到了这一点，展示时要说明它是最接近的同类。<span class="c" data-c="us6360382"></span></li>
    <li><strong>受力驱动的主动抬升，异常即降平</strong>：现有的离床传感都用来报警；我们用座板、横杆、踏板的受力决定什么时候抬，并定义了中止后的安全状态。注意：Panasonic 的椅子专利已有“扶手受力 + 座面卸载才升高”的规则，其实施例还把机器人换成了测力手杖，展示时要注明。<span class="c" data-c="us10022284"></span></li>
    <li><strong>脚先碰到台架</strong>：扶手不伸出踏板和底座的范围，夜里走动时脚先碰到踏板斜边。这借用了无障碍规范的思路（ABA §307：墙挂突出物伸出不超过 10 cm，立柱式不超过 30 cm，因为手杖只探得到低处）；它是针对公共设施的规范，不约束住宅。<span class="c" data-c="aba"></span></li>
  </ol></div>
</section>

''')

b = rep(b, '老师最可能问的两个问题，我们这样回答：', '老师最可能问的几个问题，我们这样回答：')
# ======================= risk =======================
b = rep(b, '<div class="sec-head"><div class="eyebrow">方案乙 · 安全</div><h2>它可能怎么出事，我们怎么防</h2>\n    <p class="lead">会动、会对人施力的装置，在夜里、无人看护时使用，安全论证必须排在功能前面。下表按审计意见补全了这个设计特有的风险；“可能性”是初步估计。</p></div>',
        '<div class="sec-head"><div class="eyebrow">安全</div><h2>两个方案可能怎么出事，我们怎么防</h2>\n    <p class="lead">会动、会对人施力的装置，在夜里、无人看护时使用，安全论证必须排在功能前面。“可能性”是初步估计。下面先给方案乙的控制状态，再列失效模式。</p></div>\n  <div class="card" style="max-width:900px;display:grid;gap:8px"><h3>方案乙的控制状态</h3><div class="flow"><span>待机</span><i>→</i><span>已坐上</span><i>→</i><span>准备<small>坐正 + 双手横杆 + 双脚踏板，持续 2 s</small></span><i>→</i><span>抬升<small>限速、限力的主动推</small></span><i>→</i><span>到顶<small>人已离座</small></span><i>→</i><span>复位<small>座板、踏板都无负载一段时间</small></span></div><p style="font-size:14px">任何状态下出现异常（双手离开横杆、座板负载突变、偏向一侧、超时、断电）→ <b>缓慢降平</b>：先把前倾回到水平，再降回床面高度。抬升不跟着卸载走，所以卸不了载的人也能被送高；停在高处不算安全状态，因为头晕发软的人会从斜面上滑下来。</p></div>')
FM = f'''const FM=[
 ["B","还没准备好就开始抬升","被向前推、失去平衡","高","中","“准备”需座板承重 + 双手在横杆 + 双脚踏板承重，持续 2 秒；低速"],
 ["B","抬升中松手、头晕发软或往回坐","停在高处斜面上滑落","高","中","中止即缓慢降平（先回水平再下降），不停在高处；侧扶手和横杆在两侧和前方挡"],
 ["B","用户卸不了载","抬升不起作用","中","中","抬升是主动推（限速、限力），不跟随卸载"],
 ["B","没坐正（偏向一侧）","侧滑","高","中","静坐时左右受力差超限就不进入“准备”；侧扶手一侧挡住"],
 ["B","座板前倾让人向前滑","滑落","高","中","前倾 ≤ 15°、防滑面、双脚踏板承重才动"],
 ["B","往前挪时坐空，从床和座板之间滑下","跌倒","高","中","座板后缘唇边压在床垫上、与床垫齐平；侧扶手全程可扶；挪动可行性先测（RQ4）"],
 ["B","台架被拉翻","人和台架一起倒","高","中（待计算）","站在踏板上时手力是内力；离开踏板后，自重约 30 kg 可承受约 {TIP['off_plate_forward_pull_N']} N 水平拉力；加床腿绑带；倾翻计算（RQ2）"],
 ["B","升降机构的夹点","夹手、夹腿","中","中","软罩、间隙校核；机构在座板下方、脚的后面"],
 ["B","他人（伴侣、孩子、宠物）触发或被夹","意外动作","中","低","“准备”需三类条件同时满足"],
 ["B","踏板边缘、台架占用通道","绊倒","中","中","踏板斜边、夜灯照亮踏板；扶手不伸出底座范围"],
 ["AB","认知障碍用户","不理解装置，在错误时机使用","高","—","列为不适用人群，或需照护者在场"],
 ["B","只能用一只手（如偏瘫）","互锁条件永远不满足","中","—","单手模式待定（RQ3）"],
 ["AB","断电或电池故障","乙停在高位；甲转不动","中","低","乙：自锁 + 手动缓降；甲：离合脱开可手推"],
 ["A","扶手转动时扫到膝或俯身的头","碰撞、惊吓","中","中","只在手推时转、低速限扭矩、遇阻即停；转动范围在膝前方约 0.8 m 高"],
 ["A","转动中人突然用力","扶手在手下移动","高","低","受力超过阈值立即锁死；机械棘轮"],
 ["A","收起时当床栏用，与床垫之间有缝","夹困","高","低","按 ASTM F3186-17 的间隙要求设计"],
 ["A","展开后挡路","碰撞、绊倒","中","中","人离开后超时自动收回"]
];
$("#fmea").innerHTML=`<thead><tr><th style="width:68px">方案</th><th>可能的失效</th><th>后果</th><th>严重度</th><th>可能性（初估）</th><th>对策（待验证）</th></tr></thead><tbody>`+FM.map(r=>`<tr><td class="tg">${{tagHtml(r[0])}}</td><th>${{r[1]}}</th><td>${{r[2]}}</td><td><span class="pill ${{r[3]==="高"?"bad":"amber"}}">${{r[3]}}</span></td><td>${{r[4]}}</td><td>${{r[5]}}</td></tr>`).join("")+`</tbody>`;
'''
b = cut(b, 'const FM=[', 'const WEAK=[', FM)
b = cut(b, 'const WEAK=[', '$("#weak").innerHTML=', '''const WEAK=[
 ["W1","仍要往前挪约 25 cm：约为平时挪到椅子前沿的 2 倍，目标人群能否做到未知"],
 ["W2","占地：约 0.56 × 0.78 m（含踏板），放在床前会占用下床通道"],
 ["W3","动作序列长：坐到床沿、挪、收脚、停顿、抬升加起来估计 15–20 秒（待测），和尿急冲突"],
 ["W4","机构：座板升高 + 前倾 + 扶手随升，夹点和故障点多"],
 ["W5","座板前倾有向前滑出的风险"],
 ["W6","和电动如厕抬升座、升降躺椅、升降护理床的差别需要讲清楚"]
];
''')
b = rep(b, '{k:"A 托板式：不用挪",d:"一块硬质托板平时铺在床沿的床垫上（或者折起来当床栏），由床前的台架支撑，台架底座伸进床底。老人坐在床沿，就等于坐在托板上，抬升直接从床沿开始。",fix:"W1 不用挪动；W2 床前只剩扶手和窄底座；床压住底座，不容易被拉翻。"',
        '{k:"A 托板式：不用挪",d:"一块硬质托板平时铺在床沿的床垫上（或者折起来当床栏），由床前的台架支撑，台架底座伸进床底。老人坐在床沿，就等于坐在托板上，抬升直接从床沿开始。",fix:"W1 不用挪动；W2 床前只剩扶手和窄底座；床压住底座，更不容易翻。"')
b = rep(b, '{k:"B 单驱动连杆",d:"用一个电机加一套四连杆，让台面沿设计好的轨迹，从“平”连续运动到“后高前低”，代替两段台面各自驱动。",fix:"W3 动作更快、更连贯；W4 只有一个驱动和一条轨迹，夹点和故障点更少。"',
        '{k:"B 单驱动连杆",d:"用一个电机加一套四连杆，让座板沿设计好的轨迹同时升高和前倾；扶手装在同一个滑架上一起升。",fix:"W3 动作更连贯；W4 只有一个驱动和一条轨迹，夹点和故障点更少。"')
b = rep(b, 'nw:"助力大小按体重预设，不能随人调整；坐下时要靠体重把弹簧压回去，太轻的人可能压不动。"}',
        'nw:"气弹簧在人开始起身时才释放，卸不了载的人得不到帮助（这正是 UpEasy 的局限），和“主动推”的原则冲突；助力大小按体重预设；太轻的人可能压不回弹簧。"}')
b = rep(b, '下面三个改进方向各自补掉一部分缺点，也带来新的问题，可以单独采用，也可以组合（例如 A + C）。W5 靠前倾角上限和防滑台面处理（RQ1、RQ5），W6 靠“为什么不用现成的”这一节的讲法处理。',
        '下面三个改进方向各自补掉一部分缺点，也带来新的问题，可以单独采用，也可以组合（例如 A + B）。W5 靠前倾角上限和防滑座板处理（RQ1、RQ5），W6 靠“为什么不用现成的”这一节的讲法处理。')

# ======================= RQ / todo =======================
b = rep(b, 'how:"在模型里加入台面前倾和前缘高度；把 Merryweather 2015（老人，38 vs 58 cm）作为主要对照；给出 0.42 → 0.60 m 的降幅范围（目前 −20% 到 −37%）。"',
        f'how:"离座那一刻座面不受力，所以要加一个离座前（座面仍受力）阶段的模型，才能评估前倾；同时检查座板前缘和大腿的间隙。把 Merryweather 2015（老人，38 vs 58 cm）作为主要对照；给出 0.42 → 0.60 m 的降幅范围（目前 −{-max(effs)*100:.0f}% 到 −{-min(effs)*100:.0f}%）。"')
b = rep(b, 'how:"先比较“两段各自驱动”和“单驱动连杆”（改进方向 B），可选“门控气弹簧”（C）。比较项：动作时间、自由度、夹点、断电行为、成本。选一种做 SolidWorks CAD；做一个 FEA 载荷工况（1.5 倍体重压在台面后段 + 扶手前拉），再做一次倾覆计算。",kill:"如果台架在约 0.6 × 0.7 m 的占地内做不到稳定不翻，就考虑改进方向 A（底座伸进床底）。"',
        'how:"座板升高 + 前倾用单驱动四连杆（改进方向 B），扶手装在同一滑架上。比较项：动作时间、夹点、断电行为、成本。做 SolidWorks CAD；FEA 载荷工况：1.5 倍体重压在座板 + 横杆水平力约 180 N。倾翻按三种工况算：人站在踏板上、人离开踏板后拉横杆、坐在床沿侧拉侧扶手。",kill:"如果台架在约 0.56 × 0.78 m 内、离开踏板时承受不了约 150 N 的水平拉力，又不能绑床腿，就改用改进方向 A（底座伸进床底）。"')
b = rep(b, 'how:"写状态机（六个步骤）；用坐姿静力学和组员自测数据（体重秤 + 手机）定阈值；抬升位置跟随台面卸载（带死区）；定义中止后的下降规则；估算总耗时；讨论单手模式。"',
        'how:"细化状态机：待机 → 已坐上 → 准备 → 抬升（限速限力主动推）→ 到顶 → 复位，任何异常 → 缓慢降平。阈值用坐姿静力学和组员自测（体重秤 + 手机）初定，并说明健康学生不能代表 86 岁老人；估算总耗时；讨论单手模式。"')
b = rep(b, '{id:"RQ4",t:"从床挪到台面安全吗？扶手放哪？",why:"挪动是起身台新增的一步，也是最可能被追问的一步。",how:"设计床与台面之间的搭接和高度匹配；比较两侧扶手和身前扶手；扶手高度参考老人自选的 0.71–0.84 m；助行器交接的位置。",kill:"如果向前挪对目标人群太难（组员穿护膝模拟测试），就优先评估改进方向 A（托板式，不用挪）。"',
        '{id:"RQ4",t:"往前挪约 25 cm 可行吗？扶手放哪？",why:"挪动是起身台新增的一步，也是最可能被追问的一步。",how:"组员负重或穿护膝模拟，从 0.42 m 床沿往前挪到座板上，记录挪了几次、手用了多少力；座板唇边与床垫的搭接。侧扶手 = 座面 +0.22 m，横杆 = 座面 +0.35 m（Bolli 2023：老人自选高出座面 0.25–0.38 m）；助行器停在横杆开口一侧。",kill:"如果连模拟用户都挪得很吃力，就改用改进方向 A（托板式，不用挪）。"')
b = rep(b, 'how:"按本页表格完善失效模式分析，补上可能性和检测方式；确认适用标准（EN 12182、IEC 60601-1-11、ISO 13482）；明确不适用人群。"',
        'how:"按本页表格完善两个方案的失效模式分析，补上可能性和检测方式；确认适用标准（EN 12182、IEC 60601-1-11、ISO 13482）；明确不适用人群。"')
b = rep(b, '["台面动作序列：斜台 → 平台 → 后高前低","是否需要前倾？前倾角上限多少？（RQ1）"]', '["座板动作：齐平 → 升高约 18 cm 并前倾","前倾角上限多少？需要离座前阶段的模型（RQ1）"]')
b = rep(b, '["扶手放两侧还是身前","两侧像椅子扶手，身前像助行器；也决定站起后怎么交接。"]', '["扶手：单侧 L 形（侧边 + 前横杆）还是两侧","单侧留出开口给助行器交接；两侧更稳但要从前面出来。"]')
b = rep(b, '["目标人群表述","“所有人都能用，手臂弱的人收益最大”；不适用：认知障碍、需要移位机的人；偏瘫（单手）是否纳入？"]',
        '["目标人群表述","“不换床的家庭；座高带来的帮助不依赖手臂力量”；不适用：认知障碍、需要移位机的人；偏瘫（单手）是否纳入？"]')
b = rep(b, '["床的适配范围","床高范围、床下空隙（改进方向 A 需要）、单人床还是双人床、卧室空间。"]', '["床的适配范围","床高 0.40–0.50 m；床前约 0.8 m 空间；床下空隙（改进方向 A 需要）；单人床还是双人床。"],\n ["“不换床”这个前提","愿意换升降护理床的家庭不是我们的用户；展示时要正面说明。"]')
b = rep(b, '["10/27 consultation 带去什么","建议：问题全景、证据链、床高两难、起身台演示、座高曲线、“为什么不用现成的”、失效模式表、改进方向。"]',
        '["10/27 consultation 带去什么","建议：问题全景、证据链、床高两难、两个方案演示、四种手臂假设的对比、“为什么不直接调高床”、控制状态和失效模式表。"]')

open(P + "v10_body.html", "w").write(b)

# ======================= assemble =======================
v2 = open(P + "v2_template.html").read()
head = v2[:v2.index('</style>')].replace('<title>床沿抬升起身模块</title>', '<title>夜间起身：从床沿到站稳</title>')
extra = open(P + "v3_extra.css").read() + '''
:root{--s3:#1baf7a}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--s3:#199e70}}
:root[data-theme="dark"]{--s3:#199e70}
#alts .ev h3{font-size:16px}
#alts .ev p{font-size:14px}
#scheme{margin-top:4px}
#cmpLegend i{border-radius:3px}
.pill.tagA{color:var(--s1);margin-right:4px}
.pill.tagB{color:var(--amber-ink);margin-right:4px}
table.t td.tg{white-space:nowrap;width:68px}
table.t tr.pickA td,table.t tr.pickA th{background:color-mix(in srgb,var(--s1) 9%,var(--surface))}
table.t tr.pickA td.tg{box-shadow:inset 3px 0 0 var(--s1)}
table.t tr.pick td.tg{box-shadow:inset 3px 0 0 var(--amber)}
table.t tr.pick th{box-shadow:none}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media (max-width:760px){.grid2{grid-template-columns:1fr}}
.flow{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.flow span{border:1px solid var(--line);border-radius:8px;padding:4px 10px;font-size:13.5px;background:var(--surface);display:grid}
.flow small{font-size:11.5px;color:var(--muted)}
.flow i{font-style:normal;color:var(--muted)}
'''
page = head + extra + '\n</style>\n' + b
hd = {k: HS[k] for k in ["none", "bar25", "barweak"]}
page = page.replace('__HDATA__', json.dumps(hd, separators=(',', ':')))
page = page.replace('__XDATA__', open(M + 'explorer_v10.json').read())
open(P + "bedexit_proposal.html", "w").write(page)
print("ok", len(page))
