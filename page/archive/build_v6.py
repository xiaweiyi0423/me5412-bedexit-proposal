import json
P = "/home/claude/proposal/"
b = open(P + "v5_body.html").read()

def cut(s, start, end, repl):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + repl + s[j:]
def rep(s, a, c):
    assert a in s, a[:90]
    return s.replace(a, c)

cmp = json.load(open("/home/claude/bedexit_model/compare_AB.json"))

# ---------- HTML ----------
b = rep(b, '<a href="#p3">三 · 当前方案</a>', '<a href="#p3">三 · 两个方案</a><a href="#compare">方案对比</a>')
b = rep(b, '<p class="oneline">当前方案：床前的起身台。床保持低位不动；起身时，台面先接住腿、再接住人，最后后高前低地把骨盆送上去，扶手始终在手边。</p>',
        '<p class="oneline">两个候选方案：组里最初想到的「动态扶手」，以及在它基础上发展出来的「床边起身台」。我们推荐后者：它不只让手里有东西扶，还直接减轻腿的负担。</p>')
b = rep(b, '<span class="k">第三部分 · 待确认</span><span class="v">当前方案</span><span class="d">床边起身台：演示、模型、差别、风险、已知缺点。</span>',
        '<span class="k">第三部分 · 待确认</span><span class="v">两个候选方案</span><span class="d">动态扶手 vs 床边起身台：演示、对比、模型、风险、缺点。</span>')
b = cut(b, '<div class="part" id="p3">', '<section id="concept">',
 '''<div class="part" id="p3"><span class="pk">第三部分</span><h2>两个候选方案：动态扶手 vs 床边起身台</h2><p><b>方案甲 · 动态扶手</b>是组里最初的想法：扶手装在床上，平时当床栏；老人坐到床沿后，扶手自动转到他身前。<b>方案乙 · 床边起身台</b>是在比较“力从哪来”之后发展出来的：床不改，床前放一个与床同高的台架，台面接住人并把骨盆抬高，扶手固定在台架上。下面先看两个方案怎么用，再并排比较。</p><span class="badge">推荐方案乙，待组内确认</span></div>

''')
b = rep(b, '<h2>一次夜间起身，起身台在每一步做什么</h2>', '<h2>一次夜间起身，两个方案各自怎么做</h2>')
b = rep(b, '<p class="lead">点步骤，或者按“播放”。这是从床侧面看的示意图（老人面朝右），尺寸是初定目标值。</p>',
        '<p class="lead">先选方案，再点步骤或按“播放”。这是从床侧面看的示意图（老人面朝右），尺寸是初定目标值。</p>\n  <div class="seg" id="scheme" role="group" aria-label="选择方案" style="grid-template-columns:1fr 1fr;max-width:460px"><button data-s="A" aria-pressed="false">方案甲 · 动态扶手</button><button data-s="B" aria-pressed="true">方案乙 · 床边起身台</button></div>')
b = rep(b, '<span class="muted" style="font-size:12.5px">橙色 = 可动台面；黄点 = 传感器</span>',
        '<span class="muted" style="font-size:12.5px" id="sceneKey">橙色 = 可动台面；黄点 = 传感器</span>')

compare_html = '''<section id="compare">
  <div class="sec-head"><div class="eyebrow">方案对比</div><h2>动态扶手和起身台，差在哪里</h2>
    <p class="lead">两个方案都让“手边一直有支撑”，区别在站起那一下：动态扶手只能提供反作用力，帮多少取决于老人手臂的力量；起身台把骨盆抬高，直接减轻腿的负担。</p></div>
  <div class="two">
    <div class="card chart"><div class="legend" id="cmpLegend"></div><svg id="cmpchart" viewBox="0 0 640 330" role="img" aria-label="两个方案与现状的 effort 对比柱状图"></svg></div>
    <div class="card readout">
      <h3>怎么读这张图</h3>
      <p style="font-size:14px">effort 是最吃力的关节用掉了自己最大力量的几成，越低越轻松。“现状”是老人在 0.42 m 的低床上双手撑床垫。</p>
      <p style="font-size:14px"><b>手臂弱的人</b>：动态扶手和撑床垫一样（都是 __WA__），起身台降到 __WB__（−__WP__%）。</p>
      <p style="font-size:14px"><b>手臂有力的人</b>：三者接近（__SM__ / __SA__ / __SB__）。动态扶手在离座这一刻并不比撑床垫更省力，它的价值在站直以后，那时床垫已经够不着了。</p>
      <p style="font-size:13px;color:var(--ink2)">模型把床垫当成刚性的，所以“撑床垫”被算得偏好；作为参考，不用手时为 __NONE__。</p>
    </div>
  </div>
  <div class="scroll-x"><table class="t" id="cmpT"></table></div>
</section>

'''
b = rep(b, '<section id="height">', compare_html + '<section id="height">')
b = rep(b, '<div class="sec-head"><div class="eyebrow">模型</div><h2>台面抬多高，站起来能省多少力</h2>',
        '<div class="sec-head"><div class="eyebrow">方案乙 · 模型</div><h2>台面抬多高，站起来能省多少力</h2>')
b = rep(b, '<div class="sec-head"><div class="eyebrow">差别</div><h2>为什么不直接用现成的东西</h2>',
        '<div class="sec-head"><div class="eyebrow">差别</div><h2>为什么不直接用现成的东西</h2>')
b = rep(b, '<div class="grid3" style="grid-template-columns:repeat(2,minmax(0,1fr))">\n    <div class="card ev"><span class="pill amber">问</span><div class="num" style="font-size:18px">为什么不在床沿放一个 120 美元的气弹簧座垫？</div>',
        '<div class="grid3">\n    <div class="card ev"><span class="pill amber">问 · 方案甲</span><div class="num" style="font-size:18px">为什么不用 SuperBar 或可摆出的床栏？</div><p>SuperBar 固定在身前，躺着时不在手边，而且一直挡在床前；可摆出的床栏要老人自己去扳。动态扶手在没人握时自动换位。但这个差别依赖一个还没有证据的假设：老人夜里不会自己去扳。<span class="c" data-c="superbar"></span></p></div>\n    <div class="card ev"><span class="pill amber">问 · 方案乙</span><div class="num" style="font-size:18px">为什么不在床沿放一个 120 美元的气弹簧座垫？</div>')
b = rep(b, '<div class="card ev"><span class="pill amber">问</span><div class="num" style="font-size:18px">为什么不用电动升降躺椅？</div>',
        '<div class="card ev"><span class="pill amber">问 · 方案乙</span><div class="num" style="font-size:18px">为什么不用电动升降躺椅？</div>')
b = rep(b, '<h3>能诚实宣称的差别（一个组合，而不是某一项“首创”）</h3>', '<h3>方案乙能诚实宣称的差别（一个组合，而不是某一项“首创”）</h3>')
b = rep(b, '<div class="sec-head"><div class="eyebrow">安全</div><h2>它可能怎么出事，我们怎么防</h2>',
        '<div class="sec-head"><div class="eyebrow">方案乙 · 安全</div><h2>它可能怎么出事，我们怎么防</h2>')
b = rep(b, '<div class="sec-head"><div class="eyebrow">已知缺点与改进方向</div><h2>这个方案还有哪些毛病，怎么补</h2>',
        '<div class="sec-head"><div class="eyebrow">方案乙 · 已知缺点与改进方向</div><h2>起身台还有哪些毛病，怎么补</h2>')

# ---------- JS ----------
b = rep(b, ' ["本组方案（目标）","床边起身台：斜台接腿 → 平台 → 后高前低抬升；扶手固定在台架上","","-SSSSSP-"]',
        ' ["本组方案甲（目标）","动态扶手：收起即床栏，坐到床沿后自动转到身前；不抬升","","SSSSPSP-"],\n ["本组方案乙（目标）","床边起身台：斜台接腿 → 平台 → 后高前低抬升；扶手固定在台架上","","-SSSSSP-"]')
b = rep(b, 'COV.forEach((r,k)=>{h+=`<tr${k===COV.length-1?\' class="ours"\':\'\'}>',
        'COV.forEach((r,k)=>{h+=`<tr${k===COV.length-2?\' class="ours"\':\'\'}>')
b = rep(b, '   ["会动的把手（KIT 类）","装置，经过手传入","握力要承受最高约 60% 体重","会动的东西拉着人，风险高"],',
        '   ["自动换位的扶手（方案甲）","老人自己","手臂和握力要够","不用操作；扶手只在没人握时移动"],\n   ["会动的把手（KIT 类）","装置，经过手传入","握力要承受最高约 60% 体重","握着时移动、拉着人走，风险高"],')
b = rep(b, '"<b>座面抬升 + 手扶平衡（当前方案）</b>"', '"<b>座面抬升 + 手扶平衡（方案乙）</b>"')
b = rep(b, '],pick:2,\n  why:"<b>理由：</b>模型显示', '],pick:3,\n  why:"<b>理由：</b>模型显示')
b = rep(b, '"<b>床边起身台（当前方案）</b>"', '"<b>床边起身台（方案乙）</b>"')

# stepper: add scheme A
b = rep(b, 'const STATES=[', 'const STATES_B=[')
b = rep(b, 'function drawScene(i){const s=STATES[i];', 'function drawSceneB(i){const s=STATES_B[i];')
stA = r'''const STATES_A=[
 {k:"睡眠",grip:"stow",fig:"lie",sens:[],user:"侧躺在床上。",dev:"扶手收在床沿，当一根普通床栏用。",check:"不动作。",fail:"—"},
 {k:"坐到床沿",grip:"front",fig:"sit",sens:["edge"],user:"坐起、挪到床沿，可以扶着收起的扶手。",dev:"扶手在没人握时自动转到身前约 0.8 m 高。",check:"床沿受力上升、床中部受力下降并持续约 3 秒（床垫下的压力传感）。",fail:"误判时扶手展开，最坏情况是多了一根扶手；移动时可能碰到人，所以低速、限力。"},
 {k:"握住，停一下",grip:"front",fig:"ready",sens:["edge","grip"],user:"双手握住扶手，脚踩实，坐着停一会儿。",dev:"扶手受力时锁死。",check:"扶手受力。",fail:"锁止失效：采用机械自锁（如棘轮）。"},
 {k:"坐→站",grip:"front",fig:"rise",sens:["grip"],user:"身体前倾，自己发力站起来，手拉着扶手。",dev:"扶手锁死，只提供反作用力，不抬人。",check:"—",fail:"模型：手臂弱时 effort 0.49，和撑床垫一样；手臂有力时 0.37。这一下帮得不多。"},
 {k:"站稳 · 交接",grip:"front",fig:"stand",sens:["grip"],user:"站直，扶手仍在身前；换手到助行器，迈出第一步。",dev:"人离开一段时间后，扶手收回床沿。",check:"扶手和床沿都没有负载，并持续一段时间。",fail:"展开的扶手可能挡路；超时收回。"}
];
function drawSceneA(i){const s=STATES_A[i];svg.innerHTML="";const ink=css("--ink"),muted=css("--muted"),amber=css("--amber"),surf=css("--surface");
  const pts=a=>a.map(p=>SX(p[0])+","+SZ(p[1])).join(" ");
  el("line",{x1:0,y1:SZ(0),x2:640,y2:SZ(0),stroke:muted,"stroke-width":1.5});
  el("rect",{x:SX(-1),y:SZ(0.27),width:SX(0)-SX(-1),height:SZ(0)-SZ(0.27),fill:css("--bedc"),rx:4});
  el("rect",{x:SX(-1),y:SZ(0.42),width:SX(0)-SX(-1),height:SZ(0.27)-SZ(0.42),fill:css("--matc"),rx:6});
  el("text",{x:SX(-0.95),y:SZ(0.12),fill:muted,"font-size":13},"床（床沿 0.42 m）");
  el("line",{x1:SX(0.03),y1:SZ(0.27),x2:SX(0.03),y2:SZ(0.62),stroke:ink,"stroke-width":5,"stroke-linecap":"round"});
  const grip=s.grip==="stow"?[0.03,0.78]:[0.42,0.80];
  el("line",{x1:SX(0.03),y1:SZ(0.62),x2:SX(grip[0]),y2:SZ(grip[1]),stroke:ink,"stroke-width":5,"stroke-linecap":"round"});
  el("circle",{cx:SX(grip[0]),cy:SZ(grip[1]),r:8,fill:amber,stroke:surf,"stroke-width":3});
  el("text",{x:SX(grip[0])+12,y:SZ(grip[1])-12,fill:ink,"font-size":13},s.grip==="stow"?"扶手（收起 = 床栏）":"扶手（自动转到身前）");
  const wx=0.85;el("path",{d:`M${SX(wx)} ${SZ(0)} L${SX(wx+0.05)} ${SZ(0.82)} L${SX(wx+0.2)} ${SZ(0.82)} L${SX(wx+0.23)} ${SZ(0)}`,stroke:muted,"stroke-width":3,fill:"none"});
  el("text",{x:SX(wx-0.02),y:SZ(0.9),fill:muted,"font-size":12},"助行器");
  const L=(p,w)=>el("polyline",{points:pts(p),stroke:ink,"stroke-width":w||6,fill:"none","stroke-linecap":"round","stroke-linejoin":"round"});
  const head=p=>el("circle",{cx:SX(p[0]),cy:SZ(p[1]),r:16,fill:surf,stroke:ink,"stroke-width":4});
  const f=s.fig;
  if(f==="lie"){el("ellipse",{cx:SX(-0.55),cy:SZ(0.52),rx:56,ry:23,fill:surf,stroke:ink,"stroke-width":4});head([-0.88,0.52])}
  if(f==="sit"){const S=[-0.1,0.97];L([S,[-0.15,0.51],[0.25,0.47],[0.16,0.06],[0.3,0.02]]);head([-0.08,1.07]);L([S,[-0.04,0.74],[0.02,0.6]],4)}
  if(f==="ready"){const S=[0.06,0.92];L([S,[-0.15,0.51],[0.25,0.47],[0.14,0.06],[0.28,0.02]]);head([0.12,1.02]);L([S,[0.26,0.74],grip],4)}
  if(f==="rise"){const S=[0.24,0.95];L([S,[-0.04,0.60],[0.26,0.47],[0.14,0.06],[0.28,0.02]]);head([0.31,1.04]);L([S,[0.36,0.84],grip],4)}
  if(f==="stand"){const S=[0.14,1.32];L([S,[0.12,0.86],[0.14,0.46],[0.13,0.06],[0.27,0.02]]);head([0.15,1.45]);L([S,[0.32,1.06],grip],4);L([S,[0.50,1.10],[0.91,0.82]],3)}
  const sp={edge:[-0.15,0.43],grip:grip};
  s.sens.forEach(k=>{const p=sp[k];el("circle",{cx:SX(p[0]),cy:SZ(p[1]),r:5.5,fill:amber,stroke:ink,"stroke-width":1.5})});
}
let scheme="B";
const ST=()=>scheme==="A"?STATES_A:STATES_B;
function drawScene(i){if(scheme==="A")drawSceneA(i);else drawSceneB(i)}
'''
b = rep(b, 'let cur=0,timer=null;\nfunction setState(i){cur=i;drawScene(i);const s=STATES[i];',
        stA + 'let cur=0,timer=null;\nfunction setState(i){cur=i;drawScene(i);const s=ST()[i];')
b = rep(b, '<div class="muted" style="font-size:12.5px">第 ${i+1} 步 / 共 ${STATES.length} 步</div><h3>${s.k}</h3><dl class="kv"><dt>老人</dt><dd>${s.user}</dd><dt>起身台</dt>',
        '<div class="muted" style="font-size:12.5px">${scheme==="A"?"方案甲":"方案乙"} · 第 ${i+1} 步 / 共 ${ST().length} 步</div><h3>${s.k}</h3><dl class="kv"><dt>老人</dt><dd>${s.user}</dd><dt>${scheme==="A"?"扶手":"起身台"}</dt>')
b = rep(b, '$("#tabs").innerHTML=STATES.map((s,i)=>`<button aria-pressed="false"><span class="num">${i+1}</span>${s.k}</button>`).join("");',
        'function buildTabs(){$("#tabs").innerHTML=ST().map((s,i)=>`<button aria-pressed="false"><span class="num">${i+1}</span>${s.k}</button>`).join("")}\nbuildTabs();')
b = rep(b, '$("#play").onclick=()=>{if(timer){stop();return}$("#play").textContent="❚❚ 暂停";setState(0);timer=setInterval(()=>{if(cur>=STATES.length-1){stop();return}setState(cur+1)},2200)};\nsetState(4);',
        '$("#play").onclick=()=>{if(timer){stop();return}$("#play").textContent="❚❚ 暂停";setState(0);timer=setInterval(()=>{if(cur>=ST().length-1){stop();return}setState(cur+1)},2200)};\nsetState(4);\n$("#scheme").addEventListener("click",e=>{const btn=e.target.closest("button");if(!btn)return;stop();scheme=btn.dataset.s;document.querySelectorAll("#scheme button").forEach(x=>x.setAttribute("aria-pressed",String(x===btn)));$("#sceneKey").textContent=scheme==="A"?"扶手在没人握时转动；黄点 = 传感器":"橙色 = 可动台面；黄点 = 传感器";buildTabs();setState(scheme==="A"?3:4)});')

# comparison chart + table
cmp_js = r'''/* scheme comparison */
const CMP=__CMP__;
(function(){const svgc=$("#cmpchart"),W=640,H=330,m={l:52,r:16,t:20,b:56};
  const groups=[["手臂弱（手上约 10% 体重）","weak"],["手臂有力（手上约 30% 体重）","strong"]];
  const bars=[["现状：撑床垫","mattress_042","--muted"],["方案甲：动态扶手","handleA_042","--s1"],["方案乙：起身台","stationB_060","--amber"]];
  $("#cmpLegend").innerHTML=bars.map(b=>`<span><i style="background:var(${b[2]});height:10px;width:10px"></i>${b[0]}</span>`).join("");
  const ymax=0.7,py=v=>m.t+(ymax-v)/ymax*(H-m.t-m.b);const gw=(W-m.l-m.r)/2,bw=56,gap=14;
  function draw(){svgc.innerHTML="";const g=(t,a,c)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(c!=null)e.textContent=c;svgc.appendChild(e);return e};
    const muted=css("--muted"),ink2=css("--ink2"),ln=css("--line");
    for(let v=0;v<=0.61;v+=0.2){g("line",{x1:m.l,x2:W-m.r,y1:py(v),y2:py(v),stroke:ln});g("text",{x:m.l-8,y:py(v)+4,"text-anchor":"end","font-size":12,fill:muted,"font-family":css("--font-mono")},v.toFixed(1))}
    g("line",{x1:m.l,x2:W-m.r,y1:py(CMP.none_042),y2:py(CMP.none_042),stroke:muted,"stroke-dasharray":"5 4"});
    g("text",{x:W-m.r,y:py(CMP.none_042)-6,"text-anchor":"end","font-size":12,fill:ink2},"不用手 "+CMP.none_042.toFixed(2));
    groups.forEach(([lab,k],gi)=>{const x0=m.l+gi*gw+(gw-(3*bw+2*gap))/2;
      bars.forEach(([bl,bk,c],bi)=>{const v=CMP[k][bk],x=x0+bi*(bw+gap);
        g("rect",{x:x,y:py(v),width:bw,height:py(0)-py(v),fill:css(c),rx:4});
        g("text",{x:x+bw/2,y:py(v)-6,"text-anchor":"middle","font-size":13,fill:css("--ink"),"font-family":css("--font-mono")},v.toFixed(2))});
      g("text",{x:m.l+gi*gw+gw/2,y:H-m.b+22,"text-anchor":"middle","font-size":13,fill:ink2},lab)});
    g("text",{x:14,y:m.t+6,"font-size":12.5,fill:ink2,transform:`rotate(-90 14 ${m.t+6})`,"text-anchor":"end"},"effort（越低越省力）");}
  draw();window.__cmpDraw=draw;
  const rows=[
   ["核心思路","扶手装在床上，平时当床栏；坐到床沿后，没人握时自动转到身前约 0.8 m","床前独立台架，台面接住人并把骨盆抬高；扶手固定在台架上"],
   ["解决什么","支撑一直在手边：找得到，站直后也够得着","同左，并且直接减轻腿的负担"],
   ["站起那一下（模型 effort）",`手臂弱 ${CMP.weak.handleA_042.toFixed(2)}，与撑床垫相同；手臂有力 ${CMP.strong.handleA_042.toFixed(2)}`,`手臂弱 ${CMP.weak.stationB_060.toFixed(2)}；手臂有力 ${CMP.strong.stationB_060.toFixed(2)}`],
   ["对手臂的要求","帮多少，上限取决于手臂力量","手主要扶稳；手臂越弱，收益越大"],
   ["要不要挪动","不用","要：从床挪到台面（改进方向 A 可以免掉）"],
   ["运动部件","1 个：扶手摆动","2 段台面（或 1 套连杆）"],
   ["床的依赖","要固定在床架上","不依赖，独立台架"],
   ["占地","小","约 0.6 × 0.7 m"],
   ["主要风险","扶手移动时碰到人、误展开、夹手","抬升时机、向前滑、接缝、被拉翻"],
   ["最接近的现有产品","SuperBar（身前固定横把手）、Smart-Rail（手动摆出）、Rehastage（被动跟随）","UpEasy 座垫、电动升降躺椅、France Bed"],
   ["差别靠什么","“自动换位”，依赖“老人夜里不会自己扳”的假设，目前没有证据","组合差别：不改床 + 站起后支撑不中断 + 传感驱动抬升"],
   ["12 天工作量","小：一个摆动机构 + 简单传感","大：台面机构 + 互锁 + 倾覆计算"],
   ["结论","实现简单，但站起那一下帮得不多","<b>推荐</b>：效果更强；需要用改进方向 B、C 把复杂度控制住"]];
  $("#cmpT").innerHTML=`<thead><tr><th>维度</th><th>方案甲 · 动态扶手</th><th>方案乙 · 床边起身台</th></tr></thead><tbody>`+rows.map((r,i)=>`<tr${i===rows.length-1?' class="pick"':''}><th>${r[0]}</th><td>${r[1]}</td><td>${r[2]}</td></tr>`).join("")+`</tbody>`;
})();

'''
b = rep(b, '/* height chart */', cmp_js.replace('__CMP__', json.dumps(cmp)) + '/* height chart */')
b = rep(b, 'const redraw=()=>{drawScene(cur);hdraw(+hs.value)};', 'const redraw=()=>{drawScene(cur);hdraw(+hs.value);window.__cmpDraw&&window.__cmpDraw()};')

# readout text numbers
W_, S_ = cmp["weak"], cmp["strong"]
b = b.replace("__WA__", f'{W_["handleA_042"]:.2f}').replace("__WB__", f'{W_["stationB_060"]:.2f}')
b = b.replace("__WP__", f'{round((1 - W_["stationB_060"] / W_["handleA_042"]) * 100)}')
b = b.replace("__SM__", f'{S_["mattress_042"]:.2f}').replace("__SA__", f'{S_["handleA_042"]:.2f}').replace("__SB__", f'{S_["stationB_060"]:.2f}')
b = b.replace("__NONE__", f'{cmp["none_042"]:.2f}')

# todo first item
b = rep(b, ' ["是否采用床边起身台","也可以在展示里并列三个改进方向（托板式、单驱动连杆、门控被动助力），选一个作为最终设计。"],',
        ' ["选方案甲（动态扶手）还是方案乙（床边起身台）","推荐乙；甲实现简单，但站起那一下帮得不多。乙还可以结合改进方向 A、B、C。"],')

open(P + "v6_body.html", "w").write(b)
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
'''
page = head + extra + '\n</style>\n' + b
hd = json.load(open('/home/claude/bedexit_model/seat_height_v2.json'))
hd = {k: hd[k] for k in ["none", "mattress", "handle10", "handle30"]}
page = page.replace('__HDATA__', json.dumps(hd, separators=(',', ':')))
open(P + "bedexit_proposal.html", "w").write(page)
print("ok", len(page))
