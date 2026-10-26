import json, html, re
SP = '/tmp/claude-0/-home-claude/913dcd2f-c277-5e33-8b00-aa6df00d832b/scratchpad'
T = json.load(open(SP + '/deckrender/thumbs2.json'))
DECK = json.load(open(SP + '/deck/project/deck.json'))
old = open(SP + '/guide/build_guide.py').read()
css = old.split('css = r"""', 1)[1].split('"""', 1)[0]
css += r"""
.st{display:inline-block;font-size:12px;border-radius:99px;padding:0 9px;line-height:1.8}
.todo{display:grid;gap:6px;margin:0;padding:0;list-style:none;font-size:14px}
.todo li{border:1px dashed var(--accent);background:var(--accent-bg);border-radius:8px;padding:6px 10px}
.todo li b{color:var(--accent)}
.grp-h{font-size:12.5px;color:var(--muted);letter-spacing:.06em;margin-top:10px}
.gif{position:relative}
.gif .tag{position:absolute;right:8px;bottom:8px;font-size:11.5px;background:var(--ink);color:var(--paper);border-radius:4px;padding:0 6px}
.sl.has{border-color:var(--accent);border-style:dashed}
.filter{display:flex;gap:8px;align-items:center;font-size:14px;color:var(--ink2)}
.filter input{accent-color:var(--accent);width:16px;height:16px}
td a{color:inherit}
"""

SEC = {"s0": "开场", "s1": "1 问题与用户", "s2": "2 方案", "s3": "3 机构与结构", "s4": "4 控制与安全", "s5": "5 验证与总结", "s6": "附录 · 本次沟通"}
order = DECK["order"]
starts = {v["start"]: k for k, v in DECK["sections"].items()}
secof, cur = {}, None
for sid in order:
    cur = starts.get(sid, cur); secof[sid] = cur

def aside(sid):
    h = open(f"{SP}/deck/project/slides/{sid}.html").read()
    return re.search(r"<aside>(.*?)</aside>", h, re.S).group(1).strip()

# m = minutes (script + pointing at figures); st = ok / part / gap; todo = (what, who, need)
D = {
 "cover": dict(t="封面", m=0.3, st="ok", key="一句话说清做什么：只在起身那一刻，把骨盆送到固定床设不到的高度。", ask=[], todo=[("填组员姓名", "全员", "11/3")]),
 "agenda": dict(t="汇报结构", m=0.3, st="ok", key="五部分，最后用“需求—验证”表收尾。", ask=[], todo=[]),
 "problem": dict(t="问题", m=1.0, st="part", key="固定高度的床很难两头兼顾：低了站不起来，高了脚踩不实。",
   ask=[("这些数据可靠吗？", "样本都不大（例如 12 人），我们只把它们当作方向性的证据；来源写在页面上，附录列出原文。")],
   todo=[("三个数字（一半、0.58 m、22%）打开原文再核对一次", "角色 1", "11/3")]),
 "users": dict(t="目标用户和设计要求", m=0.8, st="ok", key="用户已经和老师确认；六条要求在最后的验证表里逐条检查。",
   ask=[("偏瘫的人能用吗？", "开关一只手就能用，力分布的阈值按个人基线设，所以不排除；前提是能坐稳。")], todo=[]),
 "prior": dict(t="现有方案", m=1.0, st="part", key="借鉴压力中心判断和“按住才动”；不同在于用在床边不换床、推力有上限、速度跟着人走。",
   ask=[("和东京大学那把辅助椅有什么本质区别？", "那是一把椅子，要换家具；我们放在床边、床不改。控制上他们用压力中心触发抬升，我们另外加了推力上限和随人调速；那篇文章的作者自己也提到速度应该按人调整。")],
   todo=[("附录：完整的现有技术表和引用格式", "角色 1", "11/3")]),
 "concept": dict(t="一次完整的使用", m=1.0, st="ok", key="坐上 → 握住 → 升起 → 站稳，座板一直接得住人。",
   ask=[("往前挪 25–30 cm，老人做得到吗？", "这是目前最大的不确定。我们用姿态几何检查能不能放下，是否可行列入局限和后续实测。"),
        ("床垫边会不会下陷，形成台阶？", "座板后缘有唇边压在床垫上；下陷量要实测，列入局限。")], todo=[]),
 "whynot": dict(t="四种起身方式比较", m=1.3, st="ok", key="决定省力的是起身时的座高；床只有一个高度，起身台把“坐着的高度”和“起身的高度”分开，比抬高床再省 13–20%。",
   ask=[("省 13–20% 值得做一台电动设备吗？", "除了省力，床可以整夜保持低位，站起后扶手一直在手边，还有安全控制；对最弱的那部分人，这点差别可能决定能不能站起来（这是推断，没有验证）。"),
        ("为什么不直接把床垫高？", "可以垫，而且这是最有力的对手（0.29）。但床高同时决定坐着时脚能不能踩实，居家建议不超过约 0.58 m；起身台平时和床齐平，只在起身时升到 0.66 m，所以能再省 13–20%。"),
        ("模型可信吗？", "只用来比较方向和量级：准静态、只看离座瞬间，没有动态过程和实测，已写进局限页。")], todo=[]),
 "mechanism": dict(t="机构", m=1.0, st="ok", key="双升降柱放得下、推力不放大，作为主方案；剪叉作对比。",
   ask=[("两根柱怎么同步？", "可以用厂家控制器做同步（升降柱带霍尔信号输出），或者加机械约束，由机构组定。"),
        ("为什么不做前倾？", "一个自由度的机构，倾角由高度决定，做不到“停在高处的同时回到水平”。")], todo=[]),
 "motion": dict(t="运动演示", m=0.7, st="gap", key="看一遍关键动作，以及控制器状态如何跟着切换。",
   ask=[("动画是按真实尺寸做的吗？", "人体按 1.60 m 的比例、用两段腿的几何算出姿态，台架尺寸是初定值；它只说明动作顺序，正式版换成 SolidWorks 的运动动画。")],
   todo=[("SolidWorks 运动算例动画：两根升降柱伸出、座板竖直升起、扶手跟着升（老师邮件里明确要求）", "角色 3", "11/3 必须")]),
 "sizing": dict(t="推杆选型", m=0.8, st="part", key="每根柱只需推两百多牛，额定 2000 N，余量很大；剪叉起步就要一千多牛。",
   ask=[("速度够吗？", "TL8 满载约 9.6 mm/s、空载约 32.6 mm/s，每根实际负载约 300 N，3 cm/s 左右可行，要拿厂家的力-速度曲线确认。")],
   todo=[("按厂家力-速度曲线核对 3 cm/s 时的推力", "角色 4", "11/3"), ("两根柱的同步方式；选型表（型号、行程、推力、自锁）", "角色 3、4", "11/3"), ("计算图里的英文字太小，正式版重画成大字号", "角色 4", "11/3")]),
 "stability": dict(t="稳定性", m=1.3, st="part", key="人完全在台架上时拉扶手是内力，拉不翻；人部分离开时靠和床固定，安全系数提到 1.5。",
   ask=[("重重坐下的冲击呢？", "座板按 1.5 倍体重算，冲击可以取 2–3 倍，之后用 FEA 校核。"),
        ("要不要做斜坡倾翻测试？", "可以借移位机标准的做法，在 CAD 里校核前后 10°、侧向 5° 不倾覆。")],
   todo=[("用 CAD 的真实质量和质心复核", "角色 4（等角色 3 的 CAD）", "11/3"), ("重重坐回的冲击（2–3 倍体重）", "角色 4", "11/3"), ("和床固定的固定件具体形式", "角色 3、4", "11/3")]),
 "sensing": dict(t="传感与交互", m=0.9, st="ok", key="握紧才升、松手即停；压力中心判断坐正踩实；各力之和对不上就锁住。",
   ask=[("为什么不做成全自动（检测到想起身就抬）？", "按住式更安全、意图明确；压力中心前移作为第二个确认条件，这是借鉴东京大学那把辅助椅。"),
        ("有没有灯光或声音提示？", "握把上有状态灯（可以起 / 正在升 / 已停住），踏板有夜灯，已写在这页。")], todo=[]),
 "statemachine": dict(t="状态机", m=1.0, st="ok", key="三条规则：松手即停、有人坐着才降、离座后停住接人。",
   ask=[("停止距离多少？", "可以借移位机测试里的“停止距离小于 10 mm”作为验收指标。"),
        ("断电怎么办？", "推杆自锁，座板停住；用电池完成下降，或者带阻尼的手动缓降。")], todo=[]),
 "speed": dict(t="速度随人自适应", m=1.2, st="ok", key="推力上限和自适应速度是同一条规则：人卸掉多少体重，座板就升多快。",
   ask=[("k 怎么定？", "目前按“座板力比上限低 0.35 倍体重时达到最快速度”来设，可以按人调。"),
        ("仿真里的用户模型可信吗？", "这是简化模型，只用来检验控制逻辑会不会出错，不代表真实的起身生物力学。")],
   todo=[("计算图里的英文字太小，正式版重画成大字号", "角色 5", "11/3")]),
 "risk": dict(t="风险和对策", m=1.0, st="part", key="五个最重要的风险都有对策；往回坐的场景有动画演示。",
   ask=[("为什么只列五条？", "主 slides 只放最重要的五条；完整风险表（严重度、可能性、检测方式）放附录。"),
        ("参考了哪些标准？", "IEC 60601-1-11（家用医疗电气设备）、ISO 13482（个人护理机器人）、EN 12182（辅助产品通用要求），以及移位机标准 ISO 10535 的测试方法。")],
   todo=[("附录：完整风险表（严重度、发生可能性、检测方式、对策）", "角色 4、5", "11/3")]),
 "verify": dict(t="需求 → 验证 → 结果", m=1.0, st="part", key="六条要求里四条已有初步结果；机构强度和稳定性复核还在进行中。",
   ask=[("没有实物，怎么证明设计可行？", "这门课要求的是概念、设计和仿真；我们用模型、手算、FEA 和场景仿真逐条验证，实测列入后续工作。")],
   todo=[("FEA：座板、滑架和固定件在 1.5 倍体重下的应力和变形", "角色 4", "11/3 必须"), ("稳定性用真实质量复核后更新这一行", "角色 4", "11/3")]),
 "limits": dict(t="局限和后续工作", m=0.5, st="ok", key="主动说清模型和验证的边界。", ask=[], todo=[]),
 "conclusion": dict(t="结论", m=0.5, st="ok", key="三句话：省力、做得出来、安全。", ask=[], todo=[]),
 "team": dict(t="分工与贡献", m=0.3, st="part", key="五个角色对应装置的五个部分。", ask=[], todo=[("组员姓名和最终分工，明天组内讨论后填", "全员", "明天")]),
 "appendix": dict(t="附录目录", m=0.0, st="part", key="答问备用，不计入讲述时长。", ask=[], todo=[]),
 "questions": dict(t="想请老师确认的问题", m=0.0, st="ok", key="四个问题问清楚，记下回答，当天发到群里。本次沟通用，正式汇报删去。", ask=[], todo=[]),
}
SHORT = ["cover", "problem", "concept", "whynot", "mechanism", "stability", "speed", "risk", "verify", "conclusion"]
FORMAL = [s for s in order if s != "questions"]
ST = {"ok": ("p-ok", "内容齐"), "part": ("p-part", "部分待补"), "gap": ("p-gap", "主要内容待补")}

def e(s): return html.escape(s, quote=False)
S = []
for i, sid in enumerate(order, 1):
    d = dict(D[sid]); d.update(id=sid, n=i, sec=SEC[secof[sid]], say=aside(sid)); S.append(d)
tot_formal = sum(s["m"] for s in S if s["id"] in FORMAL)
tot_short = sum(s["m"] for s in S if s["id"] in SHORT)
todos = [(s, w, who, need) for s in S for (w, who, need) in s["todo"]]
must = [t for t in todos if "必须" in t[3]]

h = []
h.append('<title>起身台汇报讲稿</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n')
h.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">\n')
h.append(f'<style>{css}</style>\n<div class="wrap">')
h.append(f'''<header style="display:grid;gap:12px">
<p class="eyebrow">ME5412 GROUP 16 · 10/27 CONSULTATION</p>
<h1>起身台汇报讲稿</h1>
<p class="lead">配合 {len(order)} 页 slides 使用：{len(FORMAL) - 1} 页主 slides、1 页附录目录，加 1 页只在这次沟通时用的问题页。讲稿按课堂汇报的口吻写，和 slides 备注一致；还没做完的部分在页面上标了“待补”，照样放在结构里讲。</p>
</header>''')

h.append(f'''<section aria-labelledby="h-sum"><h2 id="h-sum">一眼看懂</h2>
<div class="sum">
 <div class="box"><p class="lab">正式汇报完整讲一遍</p><p class="big">约 {tot_formal:.0f} 分钟</p><p class="d">{len(FORMAL) - 1} 页主 slides 合计约 {tot_formal:.1f} 分钟（含指图讲解）；附录不计时长。</p></div>
 <div class="box"><p class="lab">时间紧时</p><p class="big">约 {tot_short:.0f} 分钟</p><p class="d">只讲 {len(SHORT)} 页，主线不断：问题 → 方案 → 为什么升高 → 机构和稳定 → 控制 → 安全 → 验证 → 结论。</p></div>
 <div class="box"><p class="lab">待补</p><p class="big">{len(todos)} 项</p><p class="d">其中 {len(must)} 项 11/3 必须有：CAD 运动动画、FEA。其余大多是复核和附录。</p></div>
</div>
</section>''')

rows = "".join(
    f'<tr><td><a href="#s-{s["id"]}">{s["n"]} {e(s["t"])}</a></td><td>{e(w)}</td><td style="white-space:nowrap">{e(who)}</td>'
    f'<td>{"<span class=\'pill p-gap\'>" + e(need) + "</span>" if "必须" in need else "<span class=\'pill p-part\'>" + e(need) + "</span>"}</td></tr>'
    for s, w, who, need in todos)
h.append(f'''<section aria-labelledby="h-todo"><h2 id="h-todo">待补清单（明天给老师看的重点）</h2>
<p class="lead">这些内容 slides 上已经留了位置、讲的时候说明“在做”。老师看完结构后，最值得问的是：这里面哪一项最重要，还有没有缺的。</p>
<div class="box scroll"><table><thead><tr><th style="width:20%">在哪一页</th><th>还缺什么</th><th style="width:16%">谁做</th><th style="width:12%">什么时候</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>''')

# ---- builder ----
groups = []
for k in DECK["sections"]:
    ids = [s for s in S if secof[s["id"]] == k]
    opts = "".join(f'<label class="opt"><input type="checkbox" id="c-{s["id"]}" data-id="{s["id"]}"><span><b>{s["n"]}</b> {e(s["t"])}{" <span class=\'pill p-part\'>待补</span>" if s["st"] != "ok" and s["todo"] else ""}</span><span class="t">{"讨论" if s["id"]=="questions" else "附录" if s["id"]=="appendix" else f"{s["m"]:.1f}"}</span></label>' for s in ids)
    groups.append(f'<p class="grp-h">{e(SEC[k])}</p><div class="opts">{opts}</div>')

slide_rows = []
for s in S:
    asks = "".join(f"<dt>{e(q)}</dt><dd>{e(a)}</dd>" for q, a in s["ask"])
    td = "".join(f'<li><b>待补：</b>{e(w)} <span style="color:var(--muted)">· {e(who)} · {e(need)}</span></li>' for w, who, need in s["todo"])
    gif = T.get(s["id"] + "_gif")
    img = (f'<div class="gif"><img src="{gif}" alt="第 {s["n"]} 页的示意动画"><span class="tag">动画</span></div>' if gif
           else f'<img src="{T[s["id"]]}" alt="第 {s["n"]} 页：{e(s["t"])}" loading="lazy">')
    cls, lab = ST[s["st"]]
    slide_rows.append(f'''<article class="srow" id="s-{s["id"]}" data-id="{s["id"]}" data-todo="{1 if s["todo"] else 0}">
 <div class="side">{img}<span class="sec">{e(s["sec"])}</span></div>
 <div class="txt">
  <div class="meta"><span class="no">第 {s["n"]} 页</span><h3>{e(s["t"])}</h3><span class="pill {cls}">{lab}</span><span class="merged" hidden>和上一页合并讲</span><span class="time"></span></div>
  <p class="keyl"><b>这一页要让听众记住：</b>{e(s["key"])}</p>
  <div><p class="lbl">讲稿</p><p class="say">{e(s["say"])}</p></div>
  {f'<ul class="todo">{td}</ul>' if td else ''}
  {f'<div><p class="lbl">可能被问到</p><dl class="qa">{asks}</dl></div>' if asks else ''}
 </div>
</article>''')

data = dict(slides=[dict(id=s["id"], n=s["n"], t=s["t"], m=s["m"], todo=bool(s["todo"])) for s in S],
            formal=FORMAL, short=SHORT)
h.append(f'''<section aria-labelledby="h-build"><h2 id="h-build">组装要讲的版本</h2>
<p class="lead">slides 里的模块都保留着；这里只是选这一次讲哪些。勾选页面，下面的时长、主线和逐页讲稿会跟着变。选择只保存在你自己的浏览器里。</p>
<div class="presets" role="group" aria-label="预设">
 <button type="button" data-preset="consult">明天沟通：全部 {len(order)} 页</button>
 <button type="button" data-preset="formal">11/3 正式汇报</button>
 <button type="button" data-preset="short">时间紧（约 {tot_short:.0f} 分钟）</button>
</div>
<div class="builder">
 <div class="box ctl">
  <h3>页面</h3>{"".join(groups)}
  <h3 style="margin-top:14px">合并讲</h3>
  <div class="opts">
   <label class="opt"><input type="checkbox" id="o-m1"><span>“推杆选型”并进“机构”一起讲（约省 0.5 分钟）</span></label>
   <label class="opt"><input type="checkbox" id="o-m2"><span>“状态机”并进“传感与交互”一起讲（约省 0.6 分钟）</span></label>
  </div>
 </div>
 <div class="live">
  <div class="box tot">
   <div class="totrow"><div><p class="lab">讲述时长</p><p class="big" id="tot">—</p></div><div><p class="lab">页数</p><p class="big" id="cnt">—</p></div>
   <div><label class="lab" for="target">目标时长（分钟）</label><input id="target" type="number" min="3" max="40" step="1" value="15"></div></div>
   <div class="meter" aria-hidden="true"><div id="bar"></div><div id="tick"></div></div>
   <p class="d" id="verdict"></p>
  </div>
  <div class="box"><p class="lab" style="margin-bottom:8px">逻辑主线（虚线框 = 有待补；点击跳到讲稿）</p><div class="flow" id="flow"></div></div>
 </div>
</div>
</section>
<section aria-labelledby="h-slides"><h2 id="h-slides">逐页讲稿</h2>
<div style="display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;align-items:center">
<p class="lead">按大约每分钟 230 字写，时长里加了指着图讲的时间。</p>
<label class="filter"><input type="checkbox" id="o-todo">只看有待补的页</label></div>
<div class="slides" id="rows">{"".join(slide_rows)}</div></section>
<script>
(function(){{"use strict";
const D={json.dumps(data, ensure_ascii=False)};
const KEY="riser-talk-guide-v2";
const $=s=>document.querySelector(s);
const SL=Object.fromEntries(D.slides.map(s=>[s.id,s]));
const ALL=D.slides.map(s=>s.id);
const PRESET={{consult:{{on:ALL.slice(),m1:false,m2:false,target:16}},formal:{{on:D.formal.slice(),m1:false,m2:false,target:15}},short:{{on:D.short.slice(),m1:true,m2:false,target:10}}}};
let st=null;
try{{st=JSON.parse(localStorage.getItem(KEY)||"null")}}catch(e){{st=null}}
if(!st||!Array.isArray(st.on)) st=JSON.parse(JSON.stringify(PRESET.consult));
const save=()=>{{try{{localStorage.setItem(KEY,JSON.stringify(st))}}catch(e){{}}}};
function mergedOf(id,list){{return (id==="sizing"&&st.m1&&list.includes("mechanism"))||(id==="statemachine"&&st.m2&&list.includes("sensing"))}}
function render(){{
 const list=ALL.filter(id=>st.on.includes(id));
 ALL.forEach(id=>$("#c-"+id).checked=st.on.includes(id));
 $("#o-m1").checked=!!st.m1; $("#o-m2").checked=!!st.m2; $("#o-todo").checked=!!st.onlyTodo;
 $("#target").value=st.target||15;
 let tot=0,pages=0; const flow=[];
 document.querySelectorAll("#rows .srow").forEach(r=>r.hidden=true);
 list.forEach(id=>{{
  const s=SL[id], mg=mergedOf(id,list);
  const t=mg?(id==="sizing"?0.3:0.4):s.m; tot+=t;
  if(id!=="appendix"&&id!=="questions") pages++;
  const el=document.querySelector(`#rows [data-id="${{id}}"]`);
  el.hidden=!!st.onlyTodo&&!s.todo;
  el.querySelector(".merged").hidden=!mg;
  el.querySelector(".time").textContent=id==="questions"?"讨论 5–10 分钟":id==="appendix"?"不计时长":`约 ${{t.toFixed(1)}} 分钟`;
  flow.push(`<a class="sl${{s.todo?" has":""}}${{mg?" mg":""}}" href="#s-${{id}}"><b>${{s.n}}</b>${{s.t}}${{mg?"（合并）":""}}</a>`);
 }});
 $("#flow").innerHTML=flow.join('<span class="arr" aria-hidden="true">→</span>');
 $("#tot").textContent=`${{tot.toFixed(1)}} 分钟`; $("#cnt").textContent=`${{pages}} 页`;
 const target=Math.max(1,st.target||15), span=Math.max(target*1.4,tot);
 $("#bar").style.width=Math.min(100,tot/span*100)+"%"; $("#tick").style.left=(target/span*100)+"%";
 $("#bar").className=tot>target+0.25?"over":"";
 const diff=tot-target;
 $("#verdict").textContent=diff>0.25?`比目标多约 ${{diff.toFixed(1)}} 分钟：可以打开“合并讲”，或参考“时间紧”去掉几页。`:diff<-1?`比目标少约 ${{(-diff).toFixed(1)}} 分钟：可以在关键页多讲一点。`:"和目标时长差不多。";
 save();
}}
ALL.forEach(id=>$("#c-"+id).addEventListener("change",e=>{{st.on=e.target.checked?[...new Set([...st.on,id])]:st.on.filter(x=>x!==id);render()}}));
[["o-m1","m1"],["o-m2","m2"],["o-todo","onlyTodo"]].forEach(([i,k])=>$("#"+i).addEventListener("change",e=>{{st[k]=e.target.checked;render()}}));
$("#target").addEventListener("input",()=>{{st.target=+$("#target").value||15;render()}});
document.querySelectorAll("[data-preset]").forEach(b=>b.addEventListener("click",()=>{{const ot=st.onlyTodo;st=JSON.parse(JSON.stringify(PRESET[b.dataset.preset]));st.onlyTodo=ot;render()}}));
render();
}})();
</script>''')
h.append('<footer>时长按讲稿字数加指图时间估算，实际以彩排计时为准。计算数字来自 GitHub 仓库 model/calc_v12；缩略图按 10/26 晚的 slides 渲染；动画是示意，不是 CAD。</footer></div>')
open(SP + '/guide/talk_guide.html', 'w').write("".join(h))
print('ok formal', round(tot_formal, 1), 'short', round(tot_short, 1), 'todos', len(todos), len("".join(h)) // 1024, 'KB')
