import json, re
import os
P = os.path.dirname(os.path.abspath(__file__)) + "/"
M = P + "../model/"
b = open(P + "v10_body.html").read()

def rep(s, a, c):
    assert s.count(a) == 1, ("COUNT %d: " % s.count(a)) + a[:100]
    return s.replace(a, c)
def cut(s, start, end, repl):
    assert s.count(start) == 1, "START " + start[:80]
    i = s.index(start); j = s.index(end, i)
    return s[:i] + repl + s[j:]

C = json.load(open(M + "compare_v11.json"))
HS = json.load(open(M + "seat_height_v11.json"))
TIP = json.load(open(M + "tipping_v11.json"))
PX = [("手力上限 25%", "按老人实测", "P1 cap25"), ("肩肘力量 ×0.5", "手力上限 30%", "P2 arm x0.5"),
      ("肩肘力量 ×0.35", "手力上限 30%", "P3 arm x0.35"), ("手臂正常", "手力上限 30%", "strong cap30")]
def raised(k): return min(C[k]["bed058_mattress"]["effort"], C[k]["bed058_handle"]["effort"])
G = []
for lab, sub, k in PX:
    G.append([lab, sub, {"low": C[k]["bed042_mattress"]["effort"], "rb": raised(k), "A": C[k]["A042_drawn"]["effort"],
                         "B": C[k]["B66_x55_z40"]["effort"], "B60": C[k]["B60_x55_z40"]["effort"]}])
pct = lambda a, b: (a / b - 1) * 100
vsR = [pct(g[2]["B"], g[2]["rb"]) for g in G]; vsL = [pct(g[2]["B"], g[2]["low"]) for g in G]; vsA = [pct(g[2]["B"], g[2]["A"]) for g in G]
b60R = [pct(g[2]["B60"], g[2]["rb"]) for g in G]
rng = lambda v: f"{-max(v):.0f}–{-min(v):.0f}%"
rngS = lambda v: f"{min(v):+.0f}% 到 {max(v):+.0f}%".replace("-", "−")
N = C["none"]; n42, n58, n66 = N["none42"]["effort"], N["none57"]["effort"], N["none66"]["effort"]
A_rng = f'{min(g[2]["A"] for g in G):.2f}–{max(g[2]["A"] for g in G):.2f}'
B_rng = f'{min(g[2]["B"] for g in G):.2f}–{max(g[2]["B"] for g in G):.2f}'
print("B vs raised", vsR, "vs low", vsL, "vs A", vsA, "B60 vs raised", b60R)
S = HS["sens"]; effs = [S[k]["eff"] for k in S if "eff" in S[k]]
P1 = G[0][2]; P2 = G[1][2]

# ---------------- hero / part 3 intro ----------------
b = rep(b, '往前挪到与床齐平的座板上；座板升高并前倾，把骨盆送高；L 形扶手跟着一起升，站直后仍在手边。',
        '往前挪到与床齐平的短座板上；按下横杆上的“起”键后，座板升高到 0.66 m 并前倾，把骨盆送到固定床设不到的高度；L 形扶手跟着一起升，站直后仍在手边。')

# ---------------- dilemma ----------------
b = cut(b, '<section id="dilemma">', '<section id="existing">', f'''<section id="dilemma">
  <div class="sec-head">
    <div class="eyebrow">关键矛盾</div>
    <h2>床高本身就是一个两难</h2>
    <p class="lead">证据链第 5 环推出：起身的起点越高越省力。但床一直都在那个高度，坐着、上床、睡觉也得用它。</p>
  </div>
  <div class="grid3">
    <div class="card ev"><span class="pill fact">指南</span><div class="num">坐着：脚要踩实</div><p>NCOA 建议床面离地约 20–23 英寸（0.51–0.58 m），并给出经验法则：坐在床沿时双脚平踩、膝约 90°；床太高，脚踩不实。</p><p class="lim">指南，不是试验证据。按“脚平踩、膝约 90°”换算，1.50–1.60 m 的老人约是 0.40–0.45 m，低于 NCOA 的通用范围（我们的推算）。<span class="c" data-c="ncoa"></span></p></div>
    <div class="card ev"><span class="pill fact">文献</span><div class="num">站起：越高越省力</div><p>12 名 56–90 岁老人：38 cm 对 58 cm，离床时髋部力矩约 1.8 倍，一半人从 38 cm 站不起来；上床（坐下）时 58 cm 也更省力。有跌倒史的老人在低床上起身行走慢得多（6.3 s 对 3.7 s）。</p><p class="lim">医院病床、样本小。没有找到研究显示床“太高”带来危害。<span class="c" data-c="merryweather"></span><span class="c" data-c="christman"></span></p></div>
    <div class="card ev"><span class="pill infer">推断</span><div class="num">固定床只能停在折中高度</div><p>床可以用床脚垫抬到约 0.55–0.58 m。这是最便宜的对手，模型里它已经拿到大部分好处。但为了坐着脚踩实、上床方便，固定床不能再高；起身台只在起身那一刻升到 0.66 m，这是固定床做不到的。</p><p class="lim">“床再高就不行”只有指南和人体尺寸推算支持，没有实测。</p></div>
  </div>
</section>

''')

# ---------------- evidence chain / sources ----------------
b = rep(b, '{t:"model",n:"−22%",c:"座面从 0.42 m 抬到 0.60 m，不用手时 effort（最吃力关节用掉的力量比例）从 0.59 降到 0.46。",l:"不同建模设定下为 −14% 到 −30%；脚完全收不回时，0.42 m 不用手站不起来，0.60 m 可以。",s:""}',
        f'{{t:"model",n:"−36%",c:"座面从 0.42 m 抬到 0.66 m，不用手时 effort（最吃力关节用掉的力量比例）从 {n42:.2f} 降到 {n66:.2f}；比抬到 0.58 m 的床还低 {-pct(n66,n58):.0f}%。",l:"不同建模设定下为 −{-max(effs)*100:.0f}% 到 −{-min(effs)*100:.0f}%（0.42 → 0.66 m）。",s:""}}')
b = rep(b, 'c:"8 名老人（平均 86 岁）坐在约 0.46 m 高的椅子上，自己选择的身前把手高度为 0.71–0.84 m，即高出座面约 0.25–0.38 m。"',
        'c:"9 名老人（平均 86 岁）参加，其中 8 人完成坐→站测试：坐在约 0.46 m 高的椅子上，自己选择的身前把手高度为 0.71–0.84 m，即高出座面约 0.25–0.38 m。"')
b = rep(b, ' saedon:["Saedon et al., The Prevalence of Orthostatic Hypotension', ' saedon:["Saedon et al. 2020, The Prevalence of Orthostatic Hypotension')
b = re.sub(r'\n aba:\[[^\n]*\],', '', b)
b = rep(b, ' us6360382:["US6360382 (Karding), Powered toilet seat lift","https://patents.google.com/patent/US6360382"],',
        ' us6360382:["US6360382 (Karding), Powered toilet seat lift","https://patents.google.com/patent/US6360382"],\n'
        ' us5619762:["US5619762 (Mein, 1997), Lift for assisting persons from a seated position","https://patents.google.com/patent/US5619762"],\n'
        ' us8556347:["US8556347 (Fu Burg, 2013), Sit/stand assist seat beside a toilet","https://patents.google.com/patent/US8556347"],\n'
        ' ebar:["MIT News 2025, Eldercare robot helps people sit and stand, and catches them if they fall (E-BAR)","https://news.mit.edu/2025/eldercare-robot-helps-people-sit-stand-catches-them-fall-0513"],')

# ---------------- coverage / prior art ----------------
b = rep(b, '在坐→站、站稳、交接这几列，现有产品要么支撑位置不理想，要么需要老人自己按按钮、扳把手，要么只提醒、不支撑。',
        '在坐→站这一列，现有家用产品要么只给扶手（帮多少取决于手臂），要么能抬人但需要按按钮、站起后手边没有支撑，要么只提醒、不支撑。')
b = rep(b, "COV.forEach((r,k)=>{h+=`<tr${k===COV.length-2?' class=\"ours\"':''}>", "COV.forEach((r,k)=>{h+=`<tr${k>=COV.length-2?' class=\"ours\"':''}>")
b = rep(b, '"气弹簧座垫，开始起身时自动顶起，可抬约 70% 体重"', '"气弹簧座垫，开始起身时自动顶起；厂商称提供“70% lift”"')
b = rep(b, '扶手受力且座面卸载后，座面升高；有实施例检测到动作就自动开始；实施例 17 把机器人换成测力手杖或肘托', '扶手受力且座面卸载后，座面升高；实施例 7 座面前倾并前移；实施例 9 检测到动作就自动开始；实施例 17 把机器人换成测力手杖或肘托')
b = rep(b, '["SuperBar、Rehastage 把手",',
        '["家具旁抬升座（1997）","专利","放在椅子或沙发旁，人挪到座上，螺杆把座面升到站立高度；立柱带扶手","手持开关","思路最接近乙（挪上去、抬起来、扶手在旁），但靠开关、没有互锁，不在床边","us5619762"],\n'
        ' ["马桶旁抬升前倾座","专利","放在马桶旁，座面升高并快速前倾，带扶手","开关","用在如厕，靠开关","us8556347"],\n'
        ' ["MIT E-BAR（2025）","研究机器人","可移动的扶杆机器人，帮人坐下、站起，摔倒时弹出气囊","机器人控制","整台移动机器人，成本和体积都大","ebar"],\n ["SuperBar、Rehastage 把手",')

# ---------------- matrix ----------------
b = rep(b, '方案乙：起身台的侧扶手紧贴床沿、比床面高约 0.22 m，拉着它坐起。', '方案乙：起身台的侧扶手紧贴床沿、比床面高约 0.22 m，拉着它坐起（注意它和床垫之间的缝，见风险表）。')
b = rep(b, '再往前挪约 25 cm 坐上座板（座板与床齐平）。', '再往前挪约 25–30 cm 坐上座板（座板与床齐平）。')
b = rep(b, '方案乙：坐正、双手握住横杆、双脚踩实踏板并持续约 2 秒，才允许抬升；这也给血压留出调整时间。', '方案乙：可以一直坐着，座板不会自己抬；准备好了，握住横杆按“起”键才开始。')
b = rep(b, '方案乙（核心）：座板升高约 18 cm 并前倾约 15°，把骨盆送高；座板很短，脚可以收到它前缘下方。', '方案乙（核心）：座板升高约 24 cm（到 0.66 m）并前倾约 15°，把骨盆送高；座板前缘在髋关节正下方，不顶大腿；脚往回收到座板前缘前方约 8 cm。')
b = rep(b, '两个方案站直后扶手都在手边。乙：人站在踏板上，手上的力是人和台架之间的内力，台架不会被拉翻。', '两个方案站直后扶手都在手边。乙：离座后座板回到水平、保持高度，万一坐回去有平座面接住；人站在踏板上，手上的力是人和台架之间的内力。')
b = rep(b, '不在范围：展示时说明边界。回床可以按相反顺序使用起身台，留作后续工作。', '不在范围：展示时说明边界。乙的回床路径：座板齐平时坐上去，往后挪回床面；细节留作后续工作。')
b = rep(b, '模型中不用手时，最吃力的关节用掉约 55–58% 的力量', '模型中不用手时，最吃力的关节用掉约 59% 的力量')
b = rep(b, '"6-1":["挪动时手脚可能卡进缝隙。","fact"]', '"6-1":["挪动时手脚可能卡进缝隙。","infer"]')

# ---------------- decisions ----------------
b = rep(b, '["B","座面抬升 + 手扶平衡","装置，经过骨盆传入","手主要扶稳；不用手时也能降约 22%","互锁：坐正、握住、踩实才抬；出现异常就缓慢降平"]],',
        f'["B","座面抬升 + 手扶平衡","装置，经过骨盆传入","要能自己承担一部分体重；手主要扶稳","按“起”键 + 握住 + 踩实才抬；推力有上限；出事就回水平再降"]],')
b = rep(b, '<b>方案乙</b>把助力改走骨盆：在我们试过的四种手臂假设下，effort 都比撑硬床垫低 12–30%；其中不依赖手臂的那部分（座高本身）约 −22%。',
        f'<b>方案乙</b>把助力改走骨盆：升到 0.66 m 时，四种手臂假设下 effort 都比抬到 0.58 m 的床低 {rng([-v for v in vsR]) if False else ""}{-max(vsR):.0f}–{-min(vsR):.0f}%，不用手时低 {-pct(n66,n58):.0f}%。')
b = rep(b, '   ["","床上放座垫（UpEasy 类）",', '   ["","抬高床（床脚垫到 0.55–0.58 m）+ 扶手","不涉及","不用","需另加扶手","最便宜；但只能停在折中高度，坐着时矮个子脚踩不实"],\n   ["","床上放座垫（UpEasy 类）",')
b = rep(b, '"坐在床沿往前挪约 25 cm，脚一直踩在踏板上","L 形扶手随座板升","挪动时坐空、离开踏板后被拉翻、占地"]],',
        '"坐在床沿往前挪约 25–30 cm，脚一直踩在踏板上","L 形扶手随座板升","挪动时坐空、窄座板侧向不稳、占地"]],')

# ---------------- stepper ----------------
POSE_JS = '''const POSE={
 lie:fillPose({S:[-0.80,0.54],H:[-0.42,0.52],K:[-0.22,0.60],A:[-0.04,0.50],T:[-0.01,0.58],E:[-0.62,0.50],W:[-0.47,0.50]}),
 BsitIn:fillPose({S:[-0.36,0.97],H:[-0.38,0.51],K:[0.01,0.50],A:[0.40,0.48],T:[0.44,0.55],E:[-0.17,0.74],W:[0.06,0.64]}),
 Bedge:fillPose({S:[-0.12,0.97],H:[-0.15,0.51],K:[0.24,0.46],A:[0.24,0.062],T:[0.41,0.02],E:[-0.05,0.72],W:[0.10,0.64]}),
 Bscoot:fillPose({S:[0.18,0.97],H:[0.13,0.51],K:[0.52,0.46],A:[0.52,0.062],T:[0.69,0.02],E:[0.22,0.70],W:[0.36,0.64]}),
 Bready:fillPose({S:[0.28,0.94],H:[0.13,0.51],K:[0.46,0.40],A:[0.29,0.062],T:[0.46,0.02],E:[0.48,0.76],W:[0.69,0.82]}),
 Brise:fillPose({S:[0.37,1.149],H:[0.14,0.75],K:[0.42,0.44],A:[0.29,0.062],T:[0.46,0.02],E:[0.52,0.98],W:[0.69,1.06]}),
 Bstand:{S:[0.31,1.309],H:[0.29,0.848],K:[0.31,0.456],A:[0.29,0.062],T:[0.46,0.02],E:[0.50,1.10],W:[0.69,1.06],E2:[0.52,1.08],W2:[0.77,0.86]},
 AsitIn:fillPose({S:[-0.36,0.97],H:[-0.38,0.51],K:[0.01,0.50],A:[0.02,0.11],T:[0.14,0.06],E:[-0.17,0.94],W:[0.03,0.80]}),
 Asit:fillPose({S:[-0.12,0.97],H:[-0.15,0.51],K:[0.24,0.46],A:[0.16,0.062],T:[0.33,0.02],E:[-0.06,0.84],W:[0.03,0.80]}),
 Aswing:fillPose({S:[-0.04,0.96],H:[-0.15,0.51],K:[0.24,0.46],A:[0.16,0.062],T:[0.33,0.02],E:[0.12,0.84],W:[0.39,0.80]}),
 Aready:fillPose({S:[0.06,0.92],H:[-0.15,0.51],K:[0.24,0.46],A:[0.14,0.062],T:[0.31,0.02],E:[0.22,0.78],W:[0.39,0.80]}),
 Arise:fillPose({S:[0.24,0.95],H:[-0.04,0.60],K:[0.26,0.47],A:[0.14,0.062],T:[0.31,0.02],E:[0.10,0.76],W:[0.39,0.80]}),
 Astand:{S:[0.15,1.309],H:[0.13,0.848],K:[0.15,0.456],A:[0.13,0.062],T:[0.30,0.02],E:[0.30,1.04],W:[0.39,0.80],E2:[0.40,1.06],W2:[0.60,0.84]}
};
'''
STB = f'''const STATES_B=[
 {{k:"睡眠",R:[0,0],pose:"lie",light:0,sens:[],user:"侧躺在床上。",dev:"床不改造（约 0.42 m）。起身台放在床前：短座板与床面齐平、紧贴床沿；人站的薄踏板铺在地上；L 形扶手在一侧。",check:"不动作。",fail:"夜里走动时，脚先碰到踏板的斜边和底座；扶手不伸出底座范围。"}},
 {{k:"翻身坐起",R:[0,0],pose:"BsitIn",light:1,sens:[],user:"侧身，拉着侧扶手靠床的一端翻身坐起，腿越过座板放下。",dev:"不动。侧扶手紧贴床沿、比床面高约 0.22 m，相当于一小段床栏。",check:"不动作。",fail:"拉扶手的力主要朝向床；侧向按 177 N 设计（台架约 35 kg、底座半宽 0.33 m）。扶手和床垫之间的缝按床栏夹困要求设计。"}},
 {{k:"坐到床沿，脚踩踏板",R:[0,0],pose:"Bedge",light:1,sens:["feet"],user:"坐到床沿，双脚落在台架的踏板上，手扶侧扶手。",dev:"不动。座板只有约 14 cm 深，小腿可以从它前面放下。",check:"踏板测到双脚承重。",fail:"踏板厚度 ≤ 13 mm、四边斜坡，夜灯照亮踏板。"}},
 {{k:"往前挪，坐上座板",R:[0,0],pose:"Bscoot",light:1,sens:["seat","feet"],user:"像挪到椅子前沿那样，一点一点往前挪约 25–30 cm，坐到座板上，脚跟着往前挪。",dev:"不动。座板后缘有唇边压在床垫上。坐在床沿时床垫边会下陷几厘米，所以挪上座板时可能有一个小台阶（待测）。",check:"座板承重达到坐姿体重的大部分，判定为“已坐上”。",fail:"往后的力由床顶住；带脚轮的床要先锁住。挪动对目标人群是否可行，要在 10/27 前用组员模拟测一次（RQ4）。"}},
 {{k:"握住横杆，坐一会儿",R:[0,0],pose:"Bready",light:1,sens:["seat","bar","feet"],user:"把脚往回收，双手握住前横杆，想坐多久都可以。准备好了，按横杆上的“起”键。",dev:"等待。座板不会自己抬。",check:"按下“起”键时，还要同时满足：座板承重、左右差不超限、双手在横杆上、双脚踏板承重。",fail:"任何一个条件不满足，按键无效，指示灯提示哪一项没满足。"}},
 {{k:"抬升：升高并前倾",R:[0.24,15],pose:"Brise",light:1,sens:["seat","bar","feet"],user:"身体前倾、自己也发力站起，座板同时把骨盆往上送。",dev:"座板以约 3 cm/s 升高 24 cm（到 0.66 m）、前倾约 15°，全程约 8 s。L 形扶手跟着升，横杆始终比座面高约 0.40 m、在髋前约 0.55 m。推力上限约为体重的一半：人自己必须承担一部分体重，座板才升得动，不会把人整个推起来。",check:"抬升中，松开按键或双手离开横杆、座板负载回升（往回坐）、左右失衡、脚离开踏板，任一出现就停止，先回到水平，再以约 2 cm/s 降回床面高度。",fail:"断电时机构自锁，可手动缓降。夹手、夹腿靠间隙设计和边缘触感开关防护，不依赖推力上限。"}},
 {{k:"站稳 · 交接",R:[0.24,0],pose:"Bstand",light:1,sens:["bar","feet"],user:"站直，扶着横杆站稳几秒，再换手到停在横杆开口一侧的助行器。",dev:"离座后，座板回到水平、保持在 0.66 m：万一头晕坐回去，有一个平的座面接住。横杆不再移动。人站在踏板上，手上的力是人和台架之间的内力。",check:"这时双手离开横杆（换手到助行器）不触发任何动作。踏板和座板都没有负载一段时间后，座板才降回与床齐平。",fail:"人离开踏板后再拉横杆：台架约 35 kg、踏板长 0.80 m 时可承受约 {TIP['capacity_forward_N(35kg)']} N 水平拉力（设计载荷 177 N）。"}}
];
'''
b = cut(b, 'const POSE={', 'const STATES_A=[', POSE_JS + 'POSE.lie=fillPose(POSE.lie);\n' + STB)
b = re.sub(r'fail:"模型：effort [0-9.]+–[0-9.]+（四种手臂假设），和撑硬床垫相当或略差；床垫软时才明显更好。这一下帮得不多。"',
           f'fail:"模型（按动画里的扶手位置）：effort {A_rng}（四种手臂假设），和撑低床床垫差不多或更差。这一下帮得不多。"', b)
assert A_rng in b

DRAWB = '''function drawB(P,i){base(P);const ink=css("--ink"),muted=css("--muted"),edge=css("--edgec"),surf=css("--surface"),line=css("--line"),amber=css("--amber"),bedc=css("--bedc");
  el("text",{x:SX(-0.95),y:SZ(0.12),fill:muted,"font-size":13},"床（不改造，床面 0.42 m）");
  const L=P.R[0],tn=Math.tan(P.R[1]*Math.PI/180),h0=0.42+L,zr=h0+0.14*tn,zs=0.64+L,zb=0.82+L,t=0.045,BX=0.69;
  el("line",{x1:SX(BX),y1:SZ(0.02),x2:SX(BX),y2:SZ(0.55),stroke:ink,"stroke-width":8,opacity:.3});
  el("line",{x1:SX(BX),y1:SZ(0.5),x2:SX(BX),y2:SZ(zb),stroke:ink,"stroke-width":4,opacity:.55});
  el("line",{x1:SX(0.0),y1:SZ(zs),x2:SX(BX),y2:SZ(zs),stroke:ink,"stroke-width":4,"stroke-linecap":"round",opacity:.45});
  el("polygon",{points:pts([[0,0],[0.80,0],[0.77,0.013],[0,0.013]]),fill:bedc});
  el("rect",{x:SX(0.0),y:SZ(0.30),width:SX(0.14)-SX(0),height:SZ(0.013)-SZ(0.30),fill:bedc,rx:3});
  el("rect",{x:SX(0.04),y:SZ(h0-0.05),width:SX(0.10)-SX(0.04),height:Math.max(0,SZ(0.30)-SZ(h0-0.05)),fill:bedc});
  el("polygon",{points:pts([[-0.03,zr],[0,zr],[0.13,h0+0.01*tn],[0.14,h0-0.012],[0.14,h0-t],[0,zr-t],[-0.03,zr-0.012]]),fill:edge});
  el("text",{x:SX(0.005),y:SZ(0.17),fill:muted,"font-size":11},"起身台");
  el("text",{x:SX(0.50),y:SZ(0.05),fill:muted,"font-size":11.5},"踏板");
  walker(0.70);figure(P);
  el("circle",{cx:SX(BX),cy:SZ(zb),r:7,fill:ink});
  el("text",{x:16,y:26,fill:ink,"font-size":12.5},"L 形扶手：侧边段 + 前横杆，随座板一起升；横杆上有“起”键");
  el("text",{x:16,y:46,fill:muted,"font-size":11.5,"font-family":css("--font-mono")},"座面 "+h0.toFixed(2)+" m · 前倾 "+P.R[1].toFixed(0)+"° · 床面 0.42 m");
  if(i>=0)sensors(STATES_B[i].sens,{seat:[0.07,(zr+h0)/2+0.012],bar:[BX,zb+0.035],feet:[0.42,0.03]});
  const TX=u=>510+u*125,TY=v=>94+v*125;
  el("rect",{x:452,y:6,width:182,height:170,rx:8,fill:surf,stroke:line,"stroke-width":1});
  el("text",{x:596,y:24,fill:muted,"font-size":11.5},"俯视");
  el("rect",{x:TX(-0.38),y:TY(-0.6),width:TX(0)-TX(-0.38),height:TY(0.3)-TY(-0.6),fill:css("--matc"),rx:4});
  el("text",{x:TX(-0.34),y:TY(-0.45),fill:muted,"font-size":10.5},"床");
  el("rect",{x:TX(0),y:TY(-0.33),width:TX(0.80)-TX(0),height:TY(0.33)-TY(-0.33),fill:bedc,rx:3});
  el("rect",{x:TX(0),y:TY(-0.22),width:TX(0.14)-TX(0),height:TY(0.22)-TY(-0.22),fill:edge,rx:2});
  el("polyline",{points:[[0,-0.28],[BX,-0.28],[BX,0.12]].map(p=>TX(p[0])+","+TY(p[1])).join(" "),fill:"none",stroke:ink,"stroke-width":4,"stroke-linecap":"round","stroke-linejoin":"round"});
  el("path",{d:`M${TX(0.58)} ${TY(0.52)} L${TX(0.58)} ${TY(0.36)} L${TX(0.78)} ${TY(0.36)} L${TX(0.78)} ${TY(0.52)}`,fill:"none",stroke:muted,"stroke-width":2});
  el("text",{x:TX(0.55),y:TY(0.62),fill:muted,"font-size":10},"助行器");
  if(P.pose.S[1]<0.75){el("line",{x1:TX(-0.2),y1:TY(-0.5),x2:TX(-0.2),y2:TY(0.22),stroke:ink,"stroke-width":7,"stroke-linecap":"round"});el("circle",{cx:TX(-0.2),cy:TY(-0.54),r:7,fill:surf,stroke:ink,"stroke-width":2.5})}
  else{const hu=P.pose.H[0];el("line",{x1:TX(hu),y1:TY(0),x2:TX(Math.max(hu+0.2,P.pose.K[0]+0.05)),y2:TY(0),stroke:ink,"stroke-width":7,"stroke-linecap":"round"});el("circle",{cx:TX(hu-0.02),cy:TY(0),r:8,fill:surf,stroke:ink,"stroke-width":2.5})}
  el("path",{d:`M${TX(-0.15)} ${TY(0.19)} L${TX(0.11)} ${TY(0.19)}`,stroke:amber,"stroke-width":2,"stroke-dasharray":"4 3",fill:"none"});
  el("path",{d:`M${TX(0.11)} ${TY(0.19)} l-7 -4 l0 8 z`,fill:amber});
  el("text",{x:TX(-0.37),y:TY(0.42),fill:muted,"font-size":10},"往前挪 25–30 cm");
}
'''
b = cut(b, 'function drawB(P,i){', 'function drawA(P,i){', DRAWB)

# ---------------- compare ----------------
b = cut(b, '<section id="compare">', '<section id="explorerA">', f'''<section id="compare">
  <div class="sec-head"><div class="eyebrow">方案对比</div><h2>和低床、抬高床相比，两个方案各省多少力</h2>
    <p class="lead">对比对象有两个：现状（0.42 m 低床，双手撑床垫），以及最便宜的对手（用床脚垫把床抬到 0.58 m，再装床边扶手）。我们不知道哪种“手臂弱”的表示最接近真实老人，所以四种都算。两个方案的扶手都按动画里的实际位置计算；抬高床的扶手取它最省力的位置（对它有利）。</p></div>
  <div class="two">
    <div class="card chart"><div class="legend" id="cmpLegend"></div><svg id="cmpchart" viewBox="0 0 640 340" role="img" aria-label="四种手臂假设下，低床、抬高床、方案甲、方案乙的 effort 柱状图"></svg></div>
    <div class="card readout">
      <h3>怎么读这张图</h3>
      <p style="font-size:14px">effort 是最吃力的关节用掉了自己最大力量的几成，越低越轻松。床垫都按刚性计算，对两种床的基线有利。</p>
      <p style="font-size:14px"><b>方案乙（升到 0.66 m）</b>在四组里都最低：比抬高到 0.58 m 的床低 {-max(vsR):.0f}–{-min(vsR):.0f}%，比低床撑床垫低 {-max(vsL):.0f}–{-min(vsL):.0f}%，比方案甲低 {-max(vsA):.0f}–{-min(vsA):.0f}%。</p>
      <p style="font-size:14px"><b>如果乙只升到 0.60 m</b>，就和抬高床差不多（{rngS(b60R)}）。所以抬升目标必须超过固定床能设的高度，这是起身台存在的理由。</p>
      <p style="font-size:14px"><b>方案甲</b>（扶手在动画里的工作位置）和撑低床床垫差不多或更差：向前抓扶手主要靠肩发力，撑在髋旁的床垫用的是伸直的手臂。</p>
    </div>
  </div>
  <div class="scroll-x"><table class="t" id="cmpT"></table></div>
</section>

''')
CMPD = {"refs": [[n42, "0.42 m"], [n58, "0.58 m"], [n66, "0.66 m"]], "groups": G}
CMPJS = '''const CMP=''' + json.dumps(CMPD, ensure_ascii=False) + ''';
(function(){const svgc=$("#cmpchart"),W=640,H=340,m={l:52,r:96,t:22,b:62};
  const bars=[["低床 0.42 m 撑床垫","low","--muted"],["抬高床 0.58 m + 扶手","rb","--s2"],["方案甲：动态扶手","A","--s1"],["方案乙：起身台 0.66 m","B","--amber"]];
  $("#cmpLegend").innerHTML=bars.map(b=>`<span><i style="background:var(${b[2]});height:10px;width:10px"></i>${b[0]}</span>`).join("");
  const ymax=0.65,py=v=>m.t+(ymax-v)/ymax*(H-m.t-m.b);const ng=CMP.groups.length,gw=(W-m.l-m.r)/ng,bw=24,gap=4;
  function draw(){svgc.innerHTML="";const g=(t,a,c)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(c!=null)e.textContent=c;svgc.appendChild(e);return e};
    const muted=css("--muted"),ink2=css("--ink2"),ln=css("--line"),ink=css("--ink");
    for(let v=0;v<=0.61;v+=0.2){g("line",{x1:m.l,x2:W-m.r,y1:py(v),y2:py(v),stroke:ln});g("text",{x:m.l-8,y:py(v)+4,"text-anchor":"end","font-size":12,fill:muted,"font-family":css("--font-mono")},v.toFixed(1))}
    g("text",{x:W-m.r+10,y:m.t-6,"font-size":11.5,fill:ink2},"不用手");
    CMP.refs.forEach(([v,lab])=>{g("line",{x1:m.l,x2:W-m.r+6,y1:py(v),y2:py(v),stroke:muted,"stroke-dasharray":"5 4"});
      g("text",{x:W-m.r+10,y:py(v)+4,"font-size":11,fill:ink2,"font-family":css("--font-mono")},lab+" "+v.toFixed(2))});
    CMP.groups.forEach(([lab,sub,d],gi)=>{const x0=m.l+gi*gw+(gw-(4*bw+3*gap))/2;
      bars.forEach(([bl,bk,c],bi)=>{const v=d[bk],x=x0+bi*(bw+gap);
        g("rect",{x:x,y:py(v),width:bw,height:py(0)-py(v),fill:css(c),rx:3});
        g("text",{x:x+bw/2,y:py(v)-5,"text-anchor":"middle","font-size":10.5,fill:ink,"font-family":css("--font-mono")},v.toFixed(2))});
      g("text",{x:m.l+gi*gw+gw/2,y:H-m.b+20,"text-anchor":"middle","font-size":12.5,fill:ink},lab);
      g("text",{x:m.l+gi*gw+gw/2,y:H-m.b+37,"text-anchor":"middle","font-size":11.5,fill:muted},sub)});
    g("text",{x:14,y:m.t+6,"font-size":12.5,fill:ink2,transform:`rotate(-90 14 ${m.t+6})`,"text-anchor":"end"},"effort（越低越省力）");}
  draw();window.__cmpDraw=draw;
  const rows=[
   ["核心思路","扶手装在床上，平时当床栏；坐到床沿后轻推一下，扶手带着手转到工作角度（约 0.8 m 高），一用力就锁死","床前起身台：坐在床沿、脚踩踏板，往前挪上与床齐平的短座板；按“起”键后座板升到 0.66 m 并前倾；L 形扶手随座板升"],
   ["解决什么","支撑一直在手边：找得到，站直后也够得着","同左，并且把骨盆送到固定床设不到的高度"],
   ["站起那一下（模型 effort）","ARNG（四种手臂假设）；和撑低床床垫差不多或更差","BRNG；比抬高到 0.58 m 的床低 VSR"],
   ["对用户的要求","帮多少，取决于手臂力量","要能自己承担一部分体重（推力上限约为体重一半）；不用手时比 0.58 m 的床低 N58%"],
   ["要不要挪动","不用","要：坐在床沿往前挪约 25–30 cm，脚一直踩在踏板上（改进方向 A 可以免掉）"],
   ["运动部件与传感","1 个：扶手摆动；只需扶手测力","1 个驱动（四连杆：升高 + 前倾），扶手随升；座板、横杆、踏板测力 + “起”键"],
   ["床的依赖","要固定在床架上","不依赖；台架靠住床，人站在踏板上压住台架"],
   ["占地","小","约 0.66 × 0.80 m（含踏板）"],
   ["主要风险","转动时扫到膝或头、夹手、展开后挡路","往前挪时坐空、窄座板侧向不稳、扶手旁的夹困缝、离开踏板后被拉翻"],
   ["最接近的现有产品","SuperBar（身前固定横把手）、Smart-Rail（手动摆出）、Rehastage（被动跟随）","家具旁抬升座（US5619762）、电动如厕抬升座、升降躺椅、抬高床 + 扶手"],
   ["差别靠什么","“轻推即转、承重即锁”的交互，依赖“老人夜里做不好手动解锁和扳动”的假设，目前没有证据","用在床边、不换床；升到固定床设不到的高度；受力互锁 + 推力上限 + 出事回水平再降"],
   ["12 天工作量","小：一个摆动机构 + 简单传感","大：四连杆 + 状态机仿真 + 倾翻计算"],
   ["结论","实现简单，但站起那一下帮得不多","<b>推荐</b>：四种手臂假设下都最省力；但比抬高床只多省 VSR，需要讲清楚这部分值不值得一台机器"]];
  $("#cmpT").innerHTML=`<thead><tr><th>维度</th><th>方案甲 · 动态扶手</th><th>方案乙 · 床边起身台</th></tr></thead><tbody>`+rows.map((r,i)=>`<tr${i===rows.length-1?' class="pick"':''}><th>${r[0]}</th><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")+`</tbody>`;
})();
'''.replace("ARNG", A_rng).replace("BRNG", B_rng).replace("VSR", f"{-max(vsR):.0f}–{-min(vsR):.0f}%").replace("N58%", f"{-pct(n66,n58):.0f}%")
b = cut(b, 'const CMP=', '/* scheme A explorer */', CMPJS + '\n')

# ---------------- explorer ----------------
b = rep(b, '同样手数时，身前扶手和床沿扶手差别不大；最好的扶手位置也只和撑硬床垫差不多，手臂弱时还略差，因为向前抓扶手主要靠肩发力，而撑在髋旁的床垫用的是伸直的手臂。',
        '同样手数时，身前扶手和床沿扶手差别不大。扶手高度限制在老人自选的范围内（高出座面 0.25–0.45 m，图中两条虚线之间）时，最好的位置也只和撑硬床垫差不多。把扶手放到肩高附近（1.2 m 以上），模型会算出更省力，但那是向上拉的姿势，模型没有考虑握力和肩部安全。')
b = rep(b, 'ctx.font="11px "+css("--font-mono");for(let z=0.5;z<1.3;z+=0.25)ctx.fillText(z.toFixed(2)+" m",4,Y(z)+4);',
        'ctx.font="11px "+css("--font-mono");for(let z=0.5;z<1.3;z+=0.25)ctx.fillText(z.toFixed(2)+" m",4,Y(z)+4);\n  ctx.save();ctx.setLineDash([5,4]);[0.67,0.87].forEach(z=>line([[0,z],[Wd.x1,z]],muted,1.2));ctx.restore();ctx.fillStyle=muted;ctx.font="11px "+css("--font-body");ctx.fillText("老人自选扶手高度范围",X(0.45),Y(0.87)-5);')

# ---------------- height ----------------
b = rep(b, '<h2>台面抬多高，站起来能省多少力</h2>', '<h2>座板抬多高，站起来能省多少力</h2>')
b = rep(b, '三条线：不用手；双手扶身前横杆，按两种手臂假设（手上最多 25% 体重 / 肩肘力量打五折）。横杆在每个座高都放在最省力的位置（高出座面 0.25–0.45 m）。脚可以往回收，但不能收进升降机构下面（脚跟至少在髋前 8 cm）。基线是 0.42 m 的低床。',
        '三条线：不用手；双手扶身前横杆，按两种手臂假设（手上最多 25% 体重 / 肩肘力量打五折）。横杆按设计位置计算：髋前 0.55 m、高出座面 0.40 m。脚可以往回收，但不能收进升降机构下面（脚跟至少在髋前 8 cm）。灰带是固定床能设的上限（约 0.58 m），黄带是抬升目标（0.66 m）。')
b = rep(b, '<input type="range" id="hs" min="0" max="13" step="1" value="10">', '<input type="range" id="hs" min="0" max="15" step="1" value="13">')
b = cut(b, '<div class="grid3">\n    <div class="card ev"><span class="pill model">本组模型</span><div class="num">−22%</div>', '<details class="fold">\n    <summary><span class="st">模型的简化与局限</span>',
        f'''<div class="grid3">
    <div class="card ev"><span class="pill model">本组模型</span><div class="num">−{-pct(n66,n58):.0f}%</div><p>不用手时，座面 0.66 m 比抬到 0.58 m 的床再省 {-pct(n66,n58):.0f}%（effort {n58:.2f} → {n66:.2f}）；比 0.42 m 的低床省 {-pct(n66,n42):.0f}%。这部分不依赖手臂力量。</p><p class="lim">0.42 → 0.66 m 的降幅，换不同设定（坐姿参数、体型、脚能否收进座下）为 −{-max(effs)*100:.0f}% 到 −{-min(effs)*100:.0f}%。</p></div>
    <div class="card ev"><span class="pill model">本组模型</span><div class="num">{P1["rb"]:.2f} → {P1["B"]:.2f}</div><p>手上最多 25% 体重时：抬高到 0.58 m 的床（配最好的扶手）{P1["rb"]:.2f}，起身台 0.66 m {P1["B"]:.2f}（{pct(P1["B"],P1["rb"]):.0f}%）。肩肘力量打五折时 {P2["rb"]:.2f} → {P2["B"]:.2f}（{pct(P2["B"],P2["rb"]):.0f}%）。</p><p class="lim">25% 是个代理值：起身困难的老年女性（11 人）推扶手时，双手合力峰值约 159 N，对 60–65 kg 的人约为体重的 25%（体重原文未报告）；推扶手和拉横杆不完全一样。<span class="c" data-c="alexander"></span></p></div>
    <div class="card ev"><span class="pill fact">老人实测</span><div class="num">48.2 → 27.5 N·m</div><p>12 名 56–90 岁老人，床高从 38 cm 换到 58 cm，离床时髋部力矩明显下降；一半人无法在没有明显协助的情况下从 38 cm 的床上站起。方向与模型一致。</p><p class="lim">力矩为静态建模估算，完成离床分析的只有 6 人。<span class="c" data-c="merryweather"></span></p></div>
  </div>
  ''')
b = cut(b, '<li>模型偏好把脚往回收。床边：', '</ul></div>\n  </details>\n</section>', f'''<li>模型偏好把脚往回收。床边：脚跟最多伸进床沿下 5 cm；起身台：脚跟至少在髋前 8 cm（升降机构在座板下方）。在高座面时这个限制起作用，小腿前倾最多约 15°。</li>
      <li>座板前缘必须在髋关节正下方或更靠后：0.66 m 时大腿下倾约 50°，前缘每往前 2 cm，就多顶进大腿约 2 cm（按大腿半厚 6 cm 估算）。所以座板只有约 14 cm 深、前缘圆角，人坐在它的前沿上。</li>
      <li>座面在模型里是水平的。离座那一刻座面已经不受力，所以前倾只通过改变髋的位置起作用；要评估前倾，需要做离座前（座面仍受力）阶段的模型（RQ1）。</li>
      <li>和文献只能说“方向一致”：Yoshioka 2014 的 1.7 倍是单个关节（髋或膝）的峰值力矩比；模型给出的是膝 + 髋之和的比值，0.42 对 0.66 m 为 {min(S[k]["ratio"] for k in S if "ratio" in S[k]):.2f}–{max(S[k]["ratio"] for k in S if "ratio" in S[k]):.2f} 倍，口径不同。<span class="c" data-c="yosh2014"></span></li>
      <li>“手臂弱”有两种表示（手力上限、肩肘力量打折），结果不同，所以对比图四种都给出。</li>
      <li>关节力量是假设值；降幅对膝、髋力量的比例不敏感（比例改 ±30%，不用手时的降幅变化约 3 个百分点），effort 的绝对值敏感。</li>
    ''')
b = rep(b, 'hmin=0.40,hmax=0.66,ymin=0.15,ymax=0.65;', 'hmin=0.40,hmax=0.70,ymin=0.15,ymax=0.65;')
b = rep(b, 'for(let h=0.40;h<=0.661;h+=0.04)', 'for(let h=0.40;h<=0.701;h+=0.04)')
b = rep(b, 'g("rect",{x:px(0.59),y:m.t,width:px(0.61)-px(0.59),height:Hh-m.t-m.b,fill:css("--scope")});g("text",{x:px(0.60),y:m.t+12,"text-anchor":"middle","font-size":11.5,fill:css("--amber-ink")},"抬升目标");',
        'g("rect",{x:px(0.57),y:m.t,width:px(0.59)-px(0.57),height:Hh-m.t-m.b,fill:ln,opacity:.6});g("text",{x:px(0.58),y:m.t+12,"text-anchor":"middle","font-size":11.5,fill:muted},"固定床上限");g("rect",{x:px(0.65),y:m.t,width:px(0.67)-px(0.65),height:Hh-m.t-m.b,fill:css("--scope")});g("text",{x:px(0.66),y:m.t+28,"text-anchor":"middle","font-size":11.5,fill:css("--amber-ink")},"抬升目标");')
b = rep(b, 'const SER=[["none","--s1","不用手"],["bar25","--s2","扶横杆 · 上限 25%"],["barweak","--s3","扶横杆 · 肩肘 ×0.5"]];', 'const SER=[["none","--s1","不用手"],["bar25","--s2","扶横杆 · 上限 25%"],["barweak","--s3","扶横杆 · 肩肘 ×0.5"]];')
b = rep(b, 'hs.value=10;', 'hs.value=13;')

b = rep(b, 'const L=HD[k][HD[k].length-1];g("text",{x:W-m.r-2,y:py(L.effort)+(si===2?-10:si===1?16:-10),"text-anchor":"end"', 'const L=HD[k][2];g("text",{x:px(0.445),y:py(L.effort)+(si===2?-8:si===1?18:-8),"text-anchor":"start"')
# ---------------- delta ----------------
b = cut(b, '<div class="grid2">', '<section id="risk">', f'''<div class="grid2">
    <div class="card ev"><span class="pill amber">问 · 两个方案</span><div class="num" style="font-size:18px">为什么不直接把床调高？</div><p>这是最便宜、也最强的对手：用床脚垫把床抬到 0.55–0.58 m，再装一根床边扶手。模型里，它在离座那一刻已经拿到大部分好处：起身台如果只升到 0.60 m，和它差不多（{rngS(b60R)}）。所以起身台必须升到固定床设不到的高度：0.66 m 时，比 0.58 m 的床再省 {-max(vsR):.0f}–{-min(vsR):.0f}%（四种手臂假设），不用手时省 {-pct(n66,n58):.0f}%。能接受 0.58 m 的床、而且这样就站得起来的人，不需要起身台。<span class="c" data-c="ncoa"></span></p></div>
    <div class="card ev"><span class="pill amber">问 · 方案甲</span><div class="num" style="font-size:18px">为什么不用 SuperBar 或可摆出的床栏？</div><p>SuperBar 固定在身前，躺着时不在手边，而且一直挡在床前；可摆出的床栏要老人自己去扳。动态扶手不用找锁扣：轻推就转、一用力就锁，转动由电机辅助。但这个差别依赖一个还没有证据的假设：老人夜里做不好手动解锁和扳动。<span class="c" data-c="superbar"></span></p></div>
    <div class="card ev"><span class="pill amber">问 · 方案乙</span><div class="num" style="font-size:18px">为什么不在床沿放一个 120 美元的气弹簧座垫？</div><p>UpEasy 的抬升力按体重预设、没有扶手，厂商说明它为带扶手的椅子设计；放在床上是否稳定是我们的推断。起身台的推力上限按用户设定，只在按下“起”键且握住、踩实时启动，扶手随座板升，而且能升到 0.66 m。<span class="c" data-c="upeasy"></span></p></div>
    <div class="card ev"><span class="pill amber">问 · 方案乙</span><div class="num" style="font-size:18px">和升降躺椅、抬升座有什么不同？</div><p>安大略省审查记录的 3 起升降躺椅死亡，都是痴呆老人用遥控器把自己升起后，在无人目击时摔倒；起身台同样有这个风险，所以认知障碍列为不适用。家具旁抬升座（1997 年专利）和电动如厕抬升座和我们最像：抬骨盆、扶手在旁，但都靠开关。起身台的差别在于用在床边、受力互锁、推力上限，以及出事后“回水平再降”的逻辑。<span class="c" data-c="liftchair"></span><span class="c" data-c="us5619762"></span><span class="c" data-c="us6360382"></span></p></div>
  </div>
  <div class="card delta"><h3>方案乙能诚实宣称的差别（一个组合，而不是某一项“首创”）</h3><ol>
    <li><strong>不换床，只在起身那一刻升到固定床设不到的高度</strong>：平时床照旧，坐着、上床都不受影响；起身时座面到 0.66 m。这是它比“抬高床 + 扶手”多出来的部分。</li>
    <li><strong>受力互锁 + 推力上限 + 定义好的安全状态</strong>：按“起”键并且握住、踩实才动；推力上限约为体重一半，不会把人整个推起来；抬升中出事就回水平再降，离座后座板保持水平接住人。注意：Panasonic 的椅子专利已有“扶手受力 + 座面卸载才升高”、座面前倾前移、测力手杖等实施例，展示时要注明。<span class="c" data-c="us10022284"></span></li>
    <li><strong>站起后支撑不中断</strong>：L 形扶手和座板一起升。如厕抬升座和家具旁抬升座也做到了这一点，所以这一条只算组合的一部分。</li>
  </ol></div>
</section>

''')

# ---------------- risk ----------------
b = cut(b, '<section id="risk">', '<section id="improve">', f'''<section id="risk">
  <div class="sec-head"><div class="eyebrow">安全</div><h2>两个方案可能怎么出事，我们怎么防</h2>
    <p class="lead">会动、会对人施力的装置，在夜里、无人看护时使用，安全论证必须排在功能前面。“可能性”是初步估计。下面先给方案乙的控制状态，再列失效模式。</p></div>
  <div class="card" style="max-width:900px;display:grid;gap:8px"><h3>方案乙的控制状态</h3>
    <div class="flow"><span>待机</span><i>→</i><span>已坐上</span><i>→</i><span>静坐<small>想坐多久都行，不会自己抬</small></span><i>→</i><span>按“起”键<small>+ 座板承重、双手横杆、双脚踏板、左右均衡</small></span><i>→</i><span>抬升<small>3 cm/s，推力 ≤ 约 0.5 × 体重</small></span><i>→</i><span>离座<small>座板回水平、保持高度</small></span><i>→</i><span>复位<small>座板、踏板都无负载一段时间</small></span></div>
    <p style="font-size:14px"><b>抬升中出事</b>（松开按键或双手离开横杆、往回坐、左右失衡、脚离开踏板）→ 停止，先回水平，再以约 2 cm/s 降回床面；人是坐着的，手随横杆慢慢下来。<b>离座以后</b>：坐回去，座板已经是平的，接住人、不动；双手离开横杆去扶助行器，不触发任何动作。<b>断电</b>：自锁，可手动缓降。</p>
    <p style="font-size:14px">推力上限约为体重的一半：人自己必须承担一部分体重，座板才升得动。卸不了载的人不会被硬推起来，他们本来就不在目标人群里，这也避开了升降躺椅“把人整个推起来”的风险。夹手、夹腿另外靠间隙设计和边缘触感开关防护。</p>
  </div>
  <div class="scroll-x"><table class="t" id="fmea"></table></div>
  <p style="font-size:13.5px;color:var(--ink2);max-width:900px">可能相关的标准（待确认）：辅助产品通用要求 EN 12182；家用电气医疗设备 IEC 60601-1-11；个人护理机器人 ISO 13482。乙的侧扶手紧贴床沿、被用来拉着坐起，可能落入成人便携床栏的强制标准（美国 16 CFR 1270 / ASTM F3186-17）范围，需要核对。<span class="c" data-c="cpsc"></span></p>
</section>

''')
FM = f'''const FM=[
 ["B","误抬：还没准备好就开始抬升","被向前推、失去平衡","高","低","必须按“起”键，并且座板承重、双手横杆、双脚踏板、左右均衡同时满足"],
 ["B","抬升中松手、头晕发软或往回坐","从斜面上滑落","高","中","停止，先回水平再降；侧扶手和横杆在一侧和前方挡"],
 ["B","离座后头晕，坐回去","坐到斜面上滑落","高","中","离座后座板立即回水平、保持高度，接住人"],
 ["B","用户卸不了载","座板升不动","中","中","推力上限约 0.5 × 体重：升不动就停，属于设计行为；这类用户不在目标人群"],
 ["B","没坐正，或从座板开口一侧侧倒","侧滑、侧倒","高","中","左右受力差超限就不响应“起”键；开口一侧加随座板升的低挡边；座板只有约 14 cm 深，侧向稳定性待测"],
 ["B","座板前倾让人向前滑","滑落","高","中","前倾 ≤ 15°、防滑面、双脚踏板承重才动"],
 ["B","往前挪时坐空，从床和座板之间滑下","跌倒","高","中","座板后缘唇边压在床垫上；侧扶手全程可扶；测量床垫边下陷量（RQ4）"],
 ["B","侧扶手和床垫之间、座板升起后下方的缝","头颈或肢体卡住（夹困）","高","低","按床栏夹困要求控制缝宽；座板下方用伸缩裙板封住"],
 ["B","台架被拉翻","人和台架一起倒","高","中（未固定前）","设计载荷统一 177 N（体重 30%）：台架约 35 kg、踏板长 0.80 m、底座半宽 0.33 m，两个方向都满足；带脚轮的床要先锁住；倾翻计算见 RQ2"],
 ["B","升降机构的夹点","夹手、夹腿","中","中","软罩、间隙校核、边缘触感开关；机构在座板下方、脚的后面"],
 ["B","他人（伴侣、孩子、宠物）触发或被夹","意外动作","中","低","需要按键 + 四类受力条件同时满足"],
 ["B","踏板边缘、台架占用通道","绊倒","中","中","踏板 ≤ 13 mm 厚、四边斜坡、夜灯照亮；扶手不伸出底座范围"],
 ["B","找不到或按错“起”键","不抬升，或误以为坏了","低","中","按键在横杆正中、带背光；条件不满足时指示灯提示是哪一项"],
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
b = cut(b, 'const WEAK=[', '$("#weak").innerHTML=', f'''const WEAK=[
 ["W1","仍要往前挪约 25–30 cm，目标人群能否做到未知；床垫边下陷会让座板唇边变成小台阶"],
 ["W2","占地：约 0.66 × 0.80 m（含踏板），放在床前会占用下床通道"],
 ["W3","动作序列长：坐到床沿、挪、握住、按键、抬升约 8 s，加起来估计 20–30 秒（待测），和尿急冲突"],
 ["W4","机构：升高 + 前倾 + 扶手随升，夹点和故障点多"],
 ["W5","座板窄（约 14 cm 深）且前倾，开口一侧有侧倒、向前滑的风险"],
 ["W6","比抬高床只多省 {-max(vsR):.0f}–{-min(vsR):.0f}%：要说明这部分值得一台机器，以及谁不能用抬高床"]
];
''')
b = rep(b, '{k:"C 门控被动助力",', '{k:"C 门控被动助力（不采用）",')
b = rep(b, '下面三个改进方向各自补掉一部分缺点，也带来新的问题，可以单独采用，也可以组合（例如 A + B）。W5 靠前倾角上限和防滑座板处理（RQ1、RQ5），W6 靠“为什么不用现成的”这一节的讲法处理。',
        '定型：乙采用单驱动四连杆（方向 B）；托板式（方向 A）只作为挪动测试失败时的备选；门控被动助力（方向 C）和“推力上限 + 按键启动”的控制思路冲突，不采用。W5 靠低挡边、前倾角上限和防滑座板处理（RQ1、RQ5），W6 靠“为什么不直接把床调高”的讲法和目标人群的界定处理。')

# ---------------- RQ / gantt / todo ----------------
RQ = '''const RQ=[
 {id:"RQ1",t:"座板几何：抬多高、前缘放哪、前倾多少？",why:"决定“比抬高床多省多少”这个核心数字，以及座板会不会顶大腿。",how:"按身高 1.50–1.70 m 把抬升目标换算成腿长的比例（0.66 m 对应模型里的 1.60 m 老人）；检查座板前缘与大腿的间隙（前缘在髋关节正下方或更靠后，圆角）；12 天内前倾只做敏感性估计，完整的离座前阶段模型留作后续。模型里座面越高越省力，但超过约 0.66 m（腿长的约 78%）时人已接近站立，窄座板上坐回去的余地和侧向稳定都变差，所以不再往上加（判断，待测）。",kill:"如果前缘放在髋下方时座板太窄、人坐不稳，就加两侧挡边，或改用托板式（方向 A）。",out:"抬升目标随身高的换算表、座板截面尺寸",d:"10/23–10/24"},
 {id:"RQ2",t:"机构与稳定：一个驱动够不够？会不会翻？",why:"决定能不能做出来、占多大地方，是 CAD 和 FEA 的主体。",how:"单驱动四连杆，让座板同时升高 24 cm 和前倾 15°，扶手装在同一滑架上。执行器选型：推力约 0.5 × 体重 + 平台自重（约 400–500 N）、行程 24 cm、约 8 s。做 SolidWorks CAD；FEA 载荷：1.5 倍体重压在座板 + 横杆水平力 177 N。倾翻按 177 N 在前后、左右两个方向校核（台架约 35 kg、踏板长 0.80 m、底座半宽 0.33 m）。",kill:"如果 35 kg、0.66 × 0.80 m 做不到 177 N 不翻，又不能绑床腿，就改用方向 A（底座伸进床底）。",out:"连杆运动学、执行器选型、CAD、FEA、倾翻计算",d:"10/25–10/31"},
 {id:"RQ3",t:"控制：状态机在出事时都能落到安全状态吗？",why:"这是“闭环”的部分，也是 Q&A 一定会追问的安全论证。",how:"把状态机写成代码，用脚本化的传感器数据做仿真：正常起身、抬升中坐回、抬升中晕倒、单手松开、宠物压座板、断电、离座后坐回；检查每种情况的最终状态和座板轨迹。阈值由坐姿静力学和组员自测（体重秤 + 手机）初定；自测前先确认是否需要 NUS IRB 豁免，并说明健康学生不能代表 86 岁老人。",kill:"如果某个场景找不到既不误抬、又不漏抬的阈值，就再加一个确认条件（例如踏板压力中心前移）。",out:"状态机图、7 个场景的仿真时间线、阈值表",d:"10/24–10/31"},
 {id:"RQ4",t:"往前挪 25–30 cm 可行吗？怎么回床？",why:"挪动是起身台新增的一步，也是最可能被追问的一步。",how:"10/27 前做：组员负重或穿护膝模拟，从 0.42 m 床沿往前挪到座板上，记录挪了几次、手用了多少力；量坐在床沿时床垫边下陷多少。画出回床路径：座板齐平时坐上去，往后挪回床面。侧扶手 = 座面 +0.22 m；横杆 = 座面 +0.40 m、髋前 0.55 m（Bolli 2023：老人自选高出座面 0.25–0.38 m，我们取偏高的一端，因为模型在更高处更省力）。",kill:"如果连模拟用户都挪得很吃力，就改用方向 A（托板式，不用挪）。",out:"挪动测试记录、下陷量、回床路径图",d:"10/23–10/26"},
 {id:"RQ5",t:"安全论证够不够？",why:"会动、会施力的装置，Q&A 一定会被追问安全。",how:"按本页表格完善两个方案的失效模式分析，补上检测方式；核对侧扶手是否落入成人便携床栏标准（16 CFR 1270 / ASTM F3186-17）；确认其他适用标准（EN 12182、IEC 60601-1-11、ISO 13482）；明确不适用人群。",kill:"如果某个高严重度的失效找不到可行对策，就收缩功能（例如取消前倾）。",out:"失效模式分析表、标准清单、适用人群说明",d:"10/27–10/31"}
];
'''
b = cut(b, 'const RQ=[', '$("#rqs").innerHTML=', RQ)
b = rep(b, 'const lanes=[["RQ1 抬多高",10,23,10,26,""],["RQ2 机构 CAD/FEA",10,24,10,31,""],["RQ3 互锁与控制",10,26,10,31,""],["RQ4 挪动与扶手",10,23,10,28,""],["RQ5 安全",10,27,10,31,""],["整合 slides、彩排",10,30,11,2,"int"]];',
        'const lanes=[["RQ1 座板几何",10,23,10,24,""],["RQ2 机构 CAD/FEA",10,25,10,31,""],["RQ3 状态机仿真",10,24,10,31,""],["RQ4 挪动测试",10,23,10,26,""],["RQ5 安全",10,27,10,31,""],["整合 slides、彩排",10,30,11,2,"int"]];')
b = cut(b, 'const TODO=[', 'let saved=', f'''const TODO=[
 ["10/24 前定型：方案乙（单驱动四连杆）为主方案，方案甲作为对照","托板式（方向 A）只在挪动测试失败时启用。"],
 ["抬升目标：座面 0.66 m（从 0.42 m 升 24 cm）","必须高于固定床能设的上限（约 0.58 m）才有意义；按身高换算（RQ1）。"],
 ["目标人群表述","床抬到 0.58 m 仍站不起来、或不愿换床的人；能自己承担一部分体重、能用助行器走。不适用：认知障碍、需要移位机的人；偏瘫（单手）是否纳入？"],
 ["“起”键还是自动触发","按键更安全、意图明确，但又回到“需要老人操作”；可以讨论是否用踏板压力中心前移代替。"],
 ["扶手：单侧 L 形 + 开口侧低挡边","单侧留出开口给助行器交接；挡边防侧倒。"],
 ["床的适配范围","床高 0.40–0.50 m；床前约 0.8 m 空间；带脚轮的床要先锁住；单人床还是双人床。"],
 ["组员自测前确认伦理要求","是否需要 NUS IRB 豁免。"],
 ["每个 RQ 的负责人",""],
 ["10/27 consultation 带去什么","建议：问题全景、证据链、床高两难、两个方案演示、和低床/抬高床的对比、“为什么不直接调高床”、控制状态和失效模式表、挪动测试的初步结果。"]
];
''')


# ---------------- v11.1: fall-from-bed argument (inference, evidence gap) ----------------
b = rep(b, ' ebar:["MIT News 2025,', ' cochrane:["Anderson, Boshier, Hanna 2012, Interventions designed to prevent healthcare bed-related injuries in patients, Cochrane Database Syst Rev (CD008931)","https://www.cochrane.org/evidence/CD008931_interventions-designed-prevent-healthcare-bed-related-injuries-patients"],\n ebar:["MIT News 2025,')
b = rep(b, '<span class="pill fact">指南</span><div class="num">坐着：脚要踩实</div><p>NCOA 建议床面离地约 20–23 英寸（0.51–0.58 m），并给出经验法则：坐在床沿时双脚平踩、膝约 90°；床太高，脚踩不实。</p>',
        '<div style="display:flex;gap:6px;flex-wrap:wrap"><span class="pill fact">指南</span><span class="pill infer">推断</span></div><div class="num">坐着、睡着：要低</div><p>NCOA 建议床面离地约 20–23 英寸（0.51–0.58 m），并给出经验法则：坐在床沿时双脚平踩、膝约 90°；床太高，脚踩不实。另外，床越高，万一睡着时滚下床，落差越大：床面从 0.42 m 到 0.58 m，落差多约 38%。</p>')
b = rep(b, '低于 NCOA 的通用范围（我们的推算）。<span class="c" data-c="ncoa"></span></p>',
        '低于 NCOA 的通用范围（我们的推算）。低床能否减少受伤没有被证实：Cochrane 2012 只收录一项医院试验（18 个病房，22,036 名患者），因跌倒受伤的比率无显著差别（RR 1.35，95% CI 0.68–2.68），而且用上低床的患者不到一半；滚下床主要见于认知受损的人。<span class="c" data-c="ncoa"></span><span class="c" data-c="cochrane"></span></p>')
b = rep(b, '但为了坐着脚踩实、上床方便，固定床不能再高；', '但为了坐着脚踩实、万一滚下床落差小，固定床不能再高；')
b = rep(b, '能接受 0.58 m 的床、而且这样就站得起来的人，不需要起身台。<span class="c" data-c="ncoa"></span></p>',
        '能接受 0.58 m 的床、而且这样就站得起来的人，不需要起身台。次要理由（推断）：抬高床整夜停在 0.58 m，万一滚下床，落差多约 38%；起身台让床整夜保持低位，只在人醒着、握住横杆、踩着踏板的几秒内升高。低床减少受伤的效果目前没有被证实，所以这一条不当主论点。<span class="c" data-c="ncoa"></span><span class="c" data-c="cochrane"></span></p>')
b = rep(b, '"最便宜；但只能停在折中高度，坐着时矮个子脚踩不实"', '"最便宜；但只能停在折中高度，坐着时矮个子脚踩不实；整夜都在高位，滚下床落差更大（推断）"')
b = rep(b, '<li><strong>不换床，只在起身那一刻升到固定床设不到的高度</strong>：平时床照旧，坐着、上床都不受影响；起身时座面到 0.66 m。',
        '<li><strong>不换床，只在起身那一刻升到固定床设不到的高度</strong>：平时床照旧，坐着、上床、睡觉都在低位；起身时座面到 0.66 m。')


# ---------------- v11.2: plan-page alignment (no experiments; tipping correction) ----------------
b = rep(b, '"高","中（未固定前）","设计载荷统一 177 N（体重 30%）：台架约 35 kg、踏板长 0.80 m、底座半宽 0.33 m，两个方向都满足；带脚轮的床要先锁住；倾翻计算见 RQ2"',
        '"高","中","设计载荷统一 177 N（体重 30%）。台架约 35 kg、踏板长 0.80 m、底座半宽 0.33 m 时：前后方向满足；扶手在低位时侧向满足；扶手升到高位（约 0.88 m）时侧向只有约 129 N，不够。对策待定：底座半宽加到约 0.45 m、加配重、和床腿固定，或人离开踏板后再降回；带脚轮的床要先锁住"')
b = rep(b, '阈值由坐姿静力学和组员自测（体重秤 + 手机）初定；自测前先确认是否需要 NUS IRB 豁免，并说明健康学生不能代表 86 岁老人。',
        '阈值先用坐姿静力学估算的假设值，在局限里说明需要实测校准。不能写代码时，先做纸面场景表：传感器事件 → 状态变化 → 最终状态。')
b = rep(b, 'how:"10/27 前做：组员负重或穿护膝模拟，从 0.42 m 床沿往前挪到座板上，记录挪了几次、手用了多少力；量坐在床沿时床垫边下陷多少。画出回床路径：',
        'how:"不做实测：用 2D 人体姿态检查说明往前挪的距离和每一步的几何（坐床沿、挪上座板、升起、站立）；挪动对老人是否可行、床垫边下陷多少，列入局限与后续验证。画出回床路径：')
b = rep(b, 'kill:"如果连模拟用户都挪得很吃力，就改用方向 A（托板式，不用挪）。",out:"挪动测试记录、下陷量、回床路径图"',
        'kill:"如果几何上就放不下（脚收不回、大腿碰座板），就改用方向 A（托板式，不用挪）。",out:"姿态检查图、回床路径图"')
for d in ["10/23–10/24","10/25–10/31","10/24–10/31","10/23–10/26","10/27–10/31"]:
    b = rep(b, 'd:"' + d + '"', 'd:"时间见分工页"')
b = rep(b, '到 11 月 3 日要回答的五个问题。每个问题都写明它决定什么，以及一个能尽早推翻它的检验（kill test）。点开看具体做法。',
        '到 11 月 3 日要回答的五个问题。每个问题都写明它决定什么，以及一个能尽早推翻它的检验（kill test）。项目只做概念、设计和仿真，不做实物和实验；分工和时间安排以分工页为准。')
b = rep(b, '<div class="scroll-x"><div class="gantt" id="gantt"></div></div>', '')
i = b.index('(function(){const days=[],start=new Date(2026,9,22);'); j = b.index('const TODO=[', i)
b = b[:i] + b[j:]
i = b.index('const TODO=['); j = b.index('let saved=', i)
b = b[:i] + """const TODO=[
 ["已定：方案乙（床边起身台，单驱动四连杆）为主方案，方案甲作为对照","托板式（方向 A）只在几何检查放不下时启用。"],
 ["已定：slides 用英文；只做概念、设计和仿真","挪动可行性、阈值校准等实测内容列入局限与后续验证。"],
 ["抬升目标：座面 0.66 m（从 0.42 m 升 24 cm）","必须高于固定床能设的上限（约 0.58 m）才有意义；按身高换算。"],
 ["扶手高位时的侧向倾翻","35 kg、半宽 0.33 m 时不够；在加宽底座、加配重、和床腿固定、人离开后再降回之间选一个。"],
 ["目标人群表述","床抬到 0.58 m 仍站不起来、或不愿换床的人；能自己承担一部分体重、能用助行器走。不适用：认知障碍、需要移位机的人；偏瘫（单手）是否纳入？"],
 ["“起”键还是自动触发","按键更安全、意图明确，但又回到“需要老人操作”；可以讨论是否用踏板压力中心前移代替。"],
 ["床的适配范围","床高 0.40–0.50 m；床前约 0.8 m 空间；带脚轮的床要先锁住；单人床还是双人床。"]
];
""" + b[j:]

open(P + "v11_body.html", "w").write(b)

# ---------------- assemble ----------------
v2 = open(P + "v2_template.html").read()
head = v2[:v2.index('</style>')].replace('<title>床沿抬升起身模块</title>', '<title>夜间起身：从床沿到站稳</title>')
build10 = open(P + "build_v10.py").read()
extra_css = build10[build10.index("extra = open(P + \"v3_extra.css\").read() + '''") + len("extra = open(P + \"v3_extra.css\").read() + '''"):]
extra_css = extra_css[:extra_css.index("'''")]
page = head + open(P + "v3_extra.css").read() + extra_css + '\n</style>\n' + b
hd = {k: HS[k] for k in ["none", "bar25", "barweak"]}
page = page.replace('__HDATA__', json.dumps(hd, separators=(',', ':')))
page = page.replace('__XDATA__', open(M + 'explorer_v10.json').read())
open(P + "bedexit_proposal.html", "w").write(page)
print("ok", len(page))
