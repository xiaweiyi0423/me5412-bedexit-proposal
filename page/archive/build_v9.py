import json
P = "/home/claude/proposal/"
b = open(P + "v6_body.html").read()

def cut(s, start, end, repl):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + repl + s[j:]
def rep(s, a, c):
    assert a in s, a[:90]
    return s.replace(a, c)

# ---------------- HTML: nav + decisions heading + explorer section ----------------
b = rep(b, '<a href="#compare">方案对比</a>', '<a href="#compare">方案对比</a><a href="#explorerA">甲 · 扶手模型</a>')
b = rep(b, '<div class="sec-head"><div class="eyebrow">设计逻辑</div><h2>四个关键选择</h2></div>',
        '<div class="sec-head"><div class="eyebrow">设计逻辑</div><h2>四个关键选择：两个方案各自怎么选</h2><p class="lead">表格最左边的标签表示这一行是哪个方案的选择：<span class="pill tagA">甲</span> 是动态扶手，<span class="pill tagB">乙</span> 是床边起身台。</p></div>')

explorer_html = '''<section id="explorerA">
  <div class="sec-head"><div class="eyebrow">方案甲 · 模型</div><h2>扶手放在哪里，站起来最省力</h2>
    <p class="lead">点击或拖动图中任意位置放置扶手，看老人怎么用力、哪个关节最吃力。颜色越深越费力。可以切换手臂强弱，也可以切换成床沿扶手（单手或双手）来比较。床高统一为 0.42 m。</p></div>
  <div class="explorer">
    <div class="stage">
      <canvas id="cv" aria-label="坐站侧视图：点击放置扶手"></canvas>
      <div class="cv-foot"><span class="ramp">省力 <i></i> 费力</span><label class="chk"><input type="checkbox" id="heat" checked> 热力图</label><span>侧视，单位 m；60 kg、1.60 m 老人模型</span></div>
    </div>
    <div class="ctrl">
      <div class="seg" id="armSeg" role="group" aria-label="手臂力量" style="grid-template-columns:1fr 1fr">
        <button data-a="strong" aria-pressed="true">手臂有力<br><span style="font-size:11.5px;opacity:.75">手上 ≤ 30% 体重</span></button>
        <button data-a="weak" aria-pressed="false">手臂弱<br><span style="font-size:11.5px;opacity:.75">手上 ≤ 10% 体重</span></button>
      </div>
      <div class="seg" role="group" aria-label="扶手类型">
        <button id="mFront" aria-pressed="true">身前<br><span style="font-size:11.5px;opacity:.75">双手</span></button>
        <button id="mSide2" aria-pressed="false">床沿扶手<br><span style="font-size:11.5px;opacity:.75">双手</span></button>
        <button id="mSide1" aria-pressed="false">床沿扶手<br><span style="font-size:11.5px;opacity:.75">单手</span></button>
      </div>
      <div id="sideCtl" hidden><label for="hSlider" class="note">扶手高度 <span class="mono" id="hVal"></span> m</label><input type="range" id="hSlider"></div>
      <div><h4>当前位置的 EFFORT</h4><div class="bigv" id="eff">–</div></div>
      <div class="bars" id="cmpBars"></div>
      <div><h4>各关节用掉的力量比例</h4><div class="bars" id="joints" style="margin-top:6px"></div></div>
      <p class="note" id="msg"></p>
    </div>
  </div>
  <div class="card" style="max-width:900px"><p style="font-size:14.5px"><b>这张图说明了方案甲的天花板：</b>同样手数时，身前扶手和床沿扶手差别不大；而且手臂越弱，扶手能帮的越少。手臂弱时，最好的扶手位置也只和撑床垫差不多。扶手的价值主要在“站直以后手边还有东西”，而不是“站起那一下更省力”。</p></div>
  <details class="fold"><summary><span class="st">这个模型的局限</span><span class="sd">展示时被追问要能说清</span></summary>
    <div class="body"><ul style="margin:0;padding-left:20px;color:var(--ink2);display:grid;gap:4px;font-size:14px">
      <li>2D 侧视、准静态，只分析离座那一瞬间；床沿扶手在人的侧面，只能投影到侧视图上粗略处理。</li>
      <li>“手上最多承担多少体重”是一个假设参数（10% / 30%），它决定了扶手能帮多少。</li>
      <li>床垫被当成刚性的，所以“撑床垫”被算得偏好。</li>
    </ul></div></details>
</section>

'''
b = rep(b, '<section id="height">', explorer_html + '<section id="height">')
b = rep(b, '<script type="application/json" id="hdata">__HDATA__</script>',
        '<script type="application/json" id="hdata">__HDATA__</script>\n<script type="application/json" id="xdata">__XDATA__</script>')

# ---------------- JS: decisions with both schemes ----------------
b = cut(b, 'const DEC=[', '$("#dec").innerHTML=', r'''const DEC=[
 {q:"选择 1：起身的力从哪来？",cols:["方案","力从哪来","对老人的要求","夜间独自使用"],rows:[
   ["","静止扶手（现有）","老人自己","手臂和握力要够","安全，但帮助的上限是老人手臂的力量"],
   ["A","自动换位的扶手","老人自己","手臂和握力要够","不用操作；扶手只在没人握时移动"],
   ["","会动的把手（KIT 类）","装置，经过手传入","握力要承受最高约 60% 体重","握着时移动、拉着人走，风险高"],
   ["B","座面抬升 + 手扶平衡","装置，经过骨盆传入","手主要负责平衡；手臂越弱，收益越大","设互锁：握住且踩实才动，松手即停"]],
  why:"<b>方案甲</b>让老人自己出力，扶手只负责待在对的位置：简单、安全，但帮多少取决于手臂力量。<b>方案乙</b>把助力改走骨盆：模型显示，手只扶稳时 effort 从 0.49 降到 0.33；手臂有力的人收益较小（−14%），但硬台面比软床垫更稳。"},
 {q:"选择 2：助力打在身体哪里？",cols:["接口","典型做法","适合本人群？","两个方案怎么用"],rows:[
   ["AB","手","扶手、把手","适合，作为借力或平衡","甲：唯一的接口，靠手借力；乙：辅助，负责平衡和“允许开始”"],
   ["B","骨盆 / 臀部","座面抬升、座面前倾","适合，作为主助力","乙：主助力。不需要握力，座高效应有老人实测支持"],
   ["","躯干 / 胸","胸垫、吊带","否","属于移位机，需要护工在场"],
   ["","膝","膝挡","否","通常配合护工使用"],
   ["","腿","外骨骼","否","夜里来不及穿戴"]],
  why:"<b>方案甲</b>只用手，手臂弱的人帮助有限。<b>方案乙</b>让手和骨盆分工：骨盆负责“推上去”，手负责“扶稳”和“授权”。"},
 {q:"选择 3：要不要抬升？抬升的部件放在哪里？",cols:["做法","床垫依赖","要不要挪动","站起后的支撑","主要风险"],rows:[
   ["A","不抬升，只让扶手换位","扶手固定在床架上，不改床垫","不用","扶手仍在身前","扶手移动时碰到人；站起那一下帮得不多"],
   ["","改造床沿（床垫下加模块）","普通床垫形成不了台阶，可能做不出来","不用","需另加扶手","床垫变形、夹缝"],
   ["","床上放座垫（UpEasy 类）","软床垫上会晃","不用","没有","抬起后无支撑"],
   ["","电动升降躺椅","不涉及","要从床走到椅子","没有","有死亡记录"],
   ["B","床边起身台","不依赖：自带硬台面，高度可调","向前挪，台面与床齐平","扶手是台架的一部分","挪动时的接缝、台架移位、被拉翻、占地"]],
  why:"<b>方案甲</b>不做抬升，所以没有床垫和挪动的问题，代价是不减轻腿的负担。<b>方案乙</b>用一个独立台架，同时解决“床垫做不出台阶”和“站起后没有支撑”，代价是多一次挪动、多占地方（见“已知缺点”）。"},
 {q:"选择 4：站起来以后怎么走？",cols:["做法","说明"],rows:[
   ["","扶手延伸成行走支撑","固定在床或台架上的装置跟不着人走，会把方案做成大杂烩"],
   ["AB","交接给老人自己的助行器","目标人群能用助行器走，难在站起来（坐→站比平地行走要求更高，待补文献）"],
   ["","连助行器也走不了的人","不在目标人群内：夜里不应独自下床"]],
  why:"两个方案都只负责到“站稳”为止，然后交接给老人自己的助行器。"}
];
const tagHtml=t=>(t.includes("A")?'<span class="pill tagA">甲</span>':'')+(t.includes("B")?'<span class="pill tagB">乙</span>':'');
''')
b = cut(b, '$("#dec").innerHTML=', '/* ================= PART 3', r'''$("#dec").innerHTML=DEC.map(d=>`<div class="card"><div class="q"><h3>${d.q}</h3></div>
 <div class="scroll-x"><table class="t"><thead><tr><th style="width:68px"></th>${d.cols.map(c=>`<th>${c}</th>`).join("")}</tr></thead><tbody>
 ${d.rows.map(r=>{const t=r[0],cls=t.includes("B")?"pick":t.includes("A")?"pickA":"";return `<tr class="${cls}"><td class="tg">${tagHtml(t)}</td>${r.slice(1).map((c,j)=>j===0?`<th>${c}</th>`:`<td>${c}</td>`).join("")}</tr>`}).join("")}</tbody></table></div><p class="why">${d.why}</p></div>`).join("");

''')

# ---------------- JS: tweened stepper ----------------
stepper = r'''/* ================= PART 3: stepper (tweened) ================= */
const svg=$("#scene");const SX=x=>300+x*290,SZ=z=>440-z*240;
const fillPose=p=>Object.assign({E2:p.E,W2:p.W},p);
const POSE={
 lie:fillPose({S:[-0.80,0.54],H:[-0.42,0.52],K:[-0.22,0.60],A:[-0.04,0.50],T:[-0.01,0.58],E:[-0.62,0.50],W:[-0.47,0.50]}),
 Blegs:fillPose({S:[-0.12,0.96],H:[-0.08,0.51],K:[0.30,0.50],A:[0.62,0.49],T:[0.66,0.56],E:[0.0,0.80],W:[0.14,0.72]}),
 Bsit:fillPose({S:[0.14,0.97],H:[0.17,0.51],K:[0.55,0.49],A:[0.68,0.06],T:[0.80,0.02],E:[0.18,0.80],W:[0.26,0.72]}),
 Bready:fillPose({S:[0.32,0.93],H:[0.17,0.51],K:[0.55,0.49],A:[0.66,0.06],T:[0.78,0.02],E:[0.48,0.80],W:[0.58,0.72]}),
 Brise:fillPose({S:[0.47,1.00],H:[0.21,0.66],K:[0.55,0.51],A:[0.66,0.06],T:[0.78,0.02],E:[0.60,0.84],W:[0.66,0.72]}),
 Bstand:{S:[0.80,1.32],H:[0.78,0.86],K:[0.80,0.46],A:[0.78,0.06],T:[0.90,0.02],E:[0.70,1.00],W:[0.68,0.72],E2:[0.92,1.06],W2:[0.98,0.82]},
 AsitIn:fillPose({S:[-0.36,0.95],H:[-0.38,0.51],K:[0.02,0.49],A:[0.03,0.10],T:[0.15,0.05],E:[-0.18,0.94],W:[0.03,0.80]}),
 Asit:fillPose({S:[-0.12,0.97],H:[-0.15,0.51],K:[0.25,0.47],A:[0.16,0.06],T:[0.30,0.02],E:[-0.08,0.86],W:[0.03,0.80]}),
 Aswing:fillPose({S:[-0.04,0.96],H:[-0.15,0.51],K:[0.25,0.47],A:[0.16,0.06],T:[0.30,0.02],E:[0.10,0.84],W:[0.39,0.80]}),
 BsitIn:fillPose({S:[-0.36,0.95],H:[-0.38,0.51],K:[0.02,0.49],A:[0.36,0.48],T:[0.40,0.55],E:[-0.15,0.80],W:[0.07,0.72]}),
 Await:fillPose({S:[-0.08,0.97],H:[-0.15,0.51],K:[0.25,0.47],A:[0.16,0.06],T:[0.30,0.02],E:[0.02,0.66],W:[0.16,0.52]}),
 Aready:fillPose({S:[0.06,0.92],H:[-0.15,0.51],K:[0.25,0.47],A:[0.14,0.06],T:[0.28,0.02],E:[0.22,0.78],W:[0.39,0.80]}),
 Arise:fillPose({S:[0.24,0.95],H:[-0.04,0.60],K:[0.26,0.47],A:[0.14,0.06],T:[0.28,0.02],E:[0.34,0.86],W:[0.39,0.80]}),
 Astand:{S:[0.14,1.32],H:[0.12,0.86],K:[0.14,0.46],A:[0.13,0.06],T:[0.27,0.02],E:[0.30,1.04],W:[0.39,0.80],E2:[0.50,1.10],W2:[0.91,0.82]}
};
POSE.lie=fillPose(POSE.lie);
const STATES_B=[
 {k:"睡眠",R:[0.42,0.42],F:[0.40,0.30],pose:"lie",light:0,sens:[],user:"侧躺在床上。",dev:"床保持低位（约 0.42 m），不做任何改造。起身台放在床前：台面后段与床面齐平，前段是一个低斜台，像脚凳。",check:"不动作。",fail:"起身台下部是实体，夜里走动时脚先碰到它，不会直接撞到扶手。"},
 {k:"翻身坐起",R:[0.42,0.42],F:[0.40,0.30],pose:"BsitIn",light:1,sens:[],user:"侧身，拉着起身台扶手靠床的一端翻身坐起。",dev:"起身台不动。扶手近端紧贴床沿、比床面高约 0.30 m，相当于一根床栏。",check:"不动作。",fail:"拉扶手时台架可能被拉动：台架与床架轻扣、底部防滑。"},
 {k:"挪到床沿，腿放上斜台",R:[0.42,0.42],F:[0.42,0.42],pose:"Blegs",light:1,sens:["F"],user:"扶着扶手挪到床沿，把小腿放到斜台上。",dev:"斜台慢慢升平，与床面形成一个连续平面。",check:"前段台面受力（腿的重量）持续约 2 秒才动；低速、限力。",fail:"误触发时只是前段升平，最坏情况是多了一个平台。"},
 {k:"往前挪，坐上台面",R:[0.42,0.42],F:[0.42,0.42],pose:"Bsit",light:1,sens:["R","F"],user:"扶着两侧扶手向前挪，坐到台面上，双脚落到台前的地面。",dev:"不动作。",check:"后段台面受力接近坐姿体重、左右受力均衡，才判定为“已坐上台面”。",fail:"床和台面之间可能有缝，台架可能被推开：加搭接板，台架与床架轻扣，并防滑锁定。"},
 {k:"握住，停一下",R:[0.42,0.42],F:[0.42,0.42],pose:"Bready",light:1,sens:["R","rail","feet"],user:"双手握住扶手，双脚踩实，坐着停一会儿（也给血压调整的时间）。",dev:"等待，不抬升。",check:"互锁：两侧扶手都受力、台面左右受力均衡、脚底承重达到阈值，并持续约 2 秒。阈值由坐姿静力学和组员自测确定（RQ3）。",fail:"任何一个条件不满足就不抬升。"},
 {k:"抬升成梯形",R:[0.64,0.56],F:[0.56,0.48],pose:"Brise",light:1,sens:["R","rail","feet"],user:"身体前倾，开始发力。",dev:"后段抬高约 18–22 cm、前段只抬约 6 cm，台面变成后高前低的梯形（前倾约 15°，待定），把骨盆送高，前缘仍低、脚能平踩。抬升位置跟着台面卸载的进度走（带死区），不是定时推。",check:"手一松，抬升立即停止并保持。中止后，只有双手重新握住才会缓慢下降。",fail:"断电时机构自锁；前倾角设上限，台面防滑，防止向前滑出。"},
 {k:"站稳 · 交接",R:[0.64,0.56],F:[0.56,0.48],pose:"Bstand",light:1,sens:["rail"],user:"站直，扶着扶手站稳几秒，再换手到助行器，迈出第一步。",dev:"扶手是台架的一部分，站直后仍在手边。人离开后，台面复位。",check:"台面和扶手都没有负载、并持续一段时间后才复位。",fail:"台架占用床前通道；扶手伸出底座不超过 10 cm，脚先碰到底座。"}
];
const STATES_A=[
 {k:"睡眠",grip:"stow",hold:0,pose:"lie",light:0,sens:[],user:"侧躺在床上。",dev:"扶手收着：摆臂沿着床边，当一根普通床栏用。",check:"不动作。",fail:"—"},
 {k:"翻身坐起",grip:"stow",hold:1,pose:"AsitIn",light:1,sens:["grip"],user:"侧身，拉着收起的扶手（也就是床栏）翻身坐起。",dev:"扶手收着，当床栏用；拉得再用力也不会转。",check:"收起状态下，向下或向内的大力只当作扶床栏，不触发转动。",fail:"—"},
 {k:"挪到床沿",grip:"stow",hold:1,pose:"Asit",light:1,sens:["grip"],user:"扶着扶手，把臀部挪到床沿，双脚落地。",dev:"不动。",check:"—",fail:"—"},
 {k:"轻推，扶手转到位",grip:"work",hold:1,pose:"Aswing",light:1,sens:["grip"],user:"手不松开，朝外轻轻一推。",dev:"扶手识别到轻推（水平方向、力小于约 20 N），低速转到工作角度（向内约 25°，由 RQ4 确定），把手一起带到位，然后锁定。",check:"只在轻推时转。转动中，手一用力（向下压或拉超过阈值）或遇到阻挡，立即停止并锁死；扭矩很小，老人一抵抗就停。",fail:"断电时离合脱开，可以用手推着转；承重时机械自锁。"},
 {k:"握住，停一下",grip:"work",hold:1,pose:"Aready",light:1,sens:["grip"],user:"双手握住扶手，脚踩实，坐着停一会儿。",dev:"已锁定。",check:"扶手受力。",fail:"锁止失效：采用机械自锁（如棘轮）。"},
 {k:"坐→站",grip:"work",hold:1,pose:"Arise",light:1,sens:["grip"],user:"身体前倾，自己发力站起来，手拉着扶手。",dev:"扶手锁死，只提供反作用力，不抬人。",check:"—",fail:"模型：手臂弱时 effort 0.49，和撑床垫一样；手臂有力时 0.37。这一下帮得不多。"},
 {k:"站稳 · 交接",grip:"work",hold:1,pose:"Astand",light:1,sens:["grip"],user:"站直，扶手仍在手边；换手到助行器，迈出第一步。",dev:"人离开一段时间后，扶手转回床边收起。",check:"扶手没有负载，并持续一段时间。",fail:"展开的扶手可能挡路；超时收回。"}
];
let scheme="B",cur=0,shown=null,raf=0,playing=false,playToken=0;
const ST=()=>scheme==="A"?STATES_A:STATES_B;
const PSI={stow:-90,work:25,front:25};
const paramsOf=s=>({pose:POSE[s.pose],R:s.R||[0.42,0.42],F:s.F||[0.42,0.42],light:s.light,ps:PSI[s.grip||"front"],hold:s.hold||0});
const lp=(a,b,t)=>a+(b-a)*t, lp2=(a,b,t)=>[lp(a[0],b[0],t),lp(a[1],b[1],t)];
function mix(a,b,t){const p={};for(const k in b.pose)p[k]=lp2(a.pose[k],b.pose[k],t);
  return {pose:p,R:lp2(a.R,b.R,t),F:lp2(a.F,b.F,t),light:lp(a.light,b.light,t),ps:lp(a.ps,b.ps,t),hold:lp(a.hold,b.hold,t)}}
const ease=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;
const reduceMotion=(()=>{try{return matchMedia("(prefers-reduced-motion: reduce)").matches}catch(e){return false}})();
function el(tag,attrs,text){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(text!=null)e.textContent=text;svg.appendChild(e);return e}
const pts=a=>a.map(p=>SX(p[0])+","+SZ(p[1])).join(" ");
function figure(P){const ink=css("--ink"),surf=css("--surface"),q=P.pose;
  const L=(p,w)=>el("polyline",{points:pts(p),stroke:ink,"stroke-width":w,fill:"none","stroke-linecap":"round","stroke-linejoin":"round"});
  L([q.S,q.H,q.K,q.A,q.T],6);
  const dx=q.S[0]-q.H[0],dz=q.S[1]-q.H[1],n=Math.hypot(dx,dz)||1,hc=[q.S[0]+dx/n*0.12,q.S[1]+dz/n*0.12];
  el("circle",{cx:SX(hc[0]),cy:SZ(hc[1]),r:16,fill:surf,stroke:ink,"stroke-width":4});
  L([q.S,q.E,q.W],4);
  if(Math.hypot(q.W2[0]-q.W[0],q.W2[1]-q.W[1])>0.02)L([q.S,q.E2,q.W2],3);}
function sensors(list,sp){const amber=css("--amber"),ink=css("--ink");list.forEach(k=>{const p=sp[k];if(p)el("circle",{cx:SX(p[0]),cy:SZ(p[1]),r:5.5,fill:amber,stroke:ink,"stroke-width":1.5})})}
function base(P){const muted=css("--muted");svg.innerHTML="";
  el("line",{x1:0,y1:SZ(0),x2:640,y2:SZ(0),stroke:muted,"stroke-width":1.5});
  if(P.light>0.01)el("ellipse",{cx:SX(0.75),cy:SZ(0)+2,rx:90,ry:9,fill:css("--amber"),opacity:(0.22*P.light).toFixed(3)});
  el("rect",{x:SX(-1),y:SZ(0.27),width:SX(0)-SX(-1),height:SZ(0)-SZ(0.27),fill:css("--bedc"),rx:4});
  el("rect",{x:SX(-1),y:SZ(0.42),width:SX(0)-SX(-1),height:SZ(0.27)-SZ(0.42),fill:css("--matc"),rx:6});}
function walker(wx){const muted=css("--muted");el("path",{d:`M${SX(wx)} ${SZ(0)} L${SX(wx+0.05)} ${SZ(0.82)} L${SX(wx+0.2)} ${SZ(0.82)} L${SX(wx+0.23)} ${SZ(0)}`,stroke:muted,"stroke-width":3,fill:"none"});
  el("text",{x:SX(wx-0.02),y:SZ(0.9),fill:muted,"font-size":12},"助行器");}
function drawB(P,i){base(P);const ink=css("--ink"),muted=css("--muted"),edge=css("--edgec");
  el("text",{x:SX(-0.95),y:SZ(0.12),fill:muted,"font-size":13},"床（不改造）");
  el("polygon",{points:pts([[0.03,0],[0.48,0],[0.48,0.12],[0.63,0.12],[0.63,0.28],[0.03,0.28]]),fill:css("--bedc")});
  el("text",{x:SX(0.08),y:SZ(0.12),fill:muted,"font-size":12.5},"起身台");
  el("text",{x:SX(0.49),y:SZ(0.03),fill:muted,"font-size":11},"踢脚凹位");
  const R=P.R,F=P.F,t=0.05;
  if(R[0]>0.43)el("path",{d:`M${SX(0.06)} ${SZ(0.28)} L${SX(0.30)} ${SZ(R[1]-t)} M${SX(0.30)} ${SZ(0.28)} L${SX(0.06)} ${SZ(R[0]-t)}`,stroke:ink,"stroke-width":2,opacity:.55,fill:"none"});
  el("line",{x1:SX(0.48),y1:SZ(0.28),x2:SX(0.48),y2:SZ((F[0]+F[1])/2-t),stroke:ink,"stroke-width":2,opacity:.55});
  el("polygon",{points:pts([[0.03,R[0]],[0.33,R[1]],[0.33,R[1]-t],[0.03,R[0]-t]]),fill:edge});
  el("polygon",{points:pts([[0.335,F[0]],[0.63,F[1]],[0.63,F[1]-t],[0.335,F[0]-t]]),fill:edge});
  [0.08,0.58].forEach(x=>el("line",{x1:SX(x),y1:SZ(0.28),x2:SX(x),y2:SZ(0.72),stroke:ink,"stroke-width":4,opacity:.8}));
  el("line",{x1:SX(0.05),y1:SZ(0.72),x2:SX(0.70),y2:SZ(0.72),stroke:ink,"stroke-width":6,"stroke-linecap":"round"});
  el("text",{x:SX(-0.98),y:SZ(1.55),fill:ink,"font-size":12.5},"两侧扶手：固定，伸出底座 ≤ 10 cm");
  el("text",{x:SX(-0.98),y:SZ(1.44),fill:muted,"font-size":11.5,"font-family":css("--font-mono")},"台面后缘 "+R[0].toFixed(2)+" m · 床面 0.42 m");
  walker(0.92);figure(P);
  if(i>=0)sensors(STATES_B[i].sens,{R:[0.18,(R[0]+R[1])/2+0.01],F:[0.48,(F[0]+F[1])/2+0.01],rail:[0.62,0.72],feet:[0.72,0.03]});}
function drawA(P,i){base(P);const ink=css("--ink"),muted=css("--muted"),amber=css("--amber"),surf=css("--surface"),line=css("--line");
  el("text",{x:SX(-0.95),y:SZ(0.12),fill:muted,"font-size":13},"床（床沿 0.42 m）");
  el("line",{x1:SX(0.03),y1:SZ(0.27),x2:SX(0.03),y2:SZ(0.80),stroke:ink,"stroke-width":5,"stroke-linecap":"round",opacity:.5});
  const ps=P.ps*Math.PI/180,AL=0.40,gx=0.03+AL*Math.cos(ps),grip=[gx,0.80];
  if(Math.cos(ps)>0.03)el("line",{x1:SX(0.03),y1:SZ(0.80),x2:SX(gx),y2:SZ(0.80),stroke:ink,"stroke-width":5,"stroke-linecap":"round"});
  el("circle",{cx:SX(grip[0]),cy:SZ(grip[1]),r:8,fill:amber,stroke:surf,"stroke-width":3});
  el("text",{x:SX(0.06),y:SZ(0.80)-16,fill:ink,"font-size":12.5},P.ps<-45?"扶手收起（沿床边，当床栏用）":"扶手在工作角度（向内约 25°）");
  walker(0.85);
  const q=Object.assign({},P.pose,{W:lp2(P.pose.W,grip,P.hold)});figure(Object.assign({},P,{pose:q}));
  if(i>=0)sensors(STATES_A[i].sens,{grip:grip});
  // top-view inset
  const TX=u=>522+u*140,TY=v=>146+v*140;
  el("rect",{x:462,y:8,width:172,height:196,rx:8,fill:surf,stroke:line,"stroke-width":1});
  el("text",{x:590,y:28,fill:muted,"font-size":12},"俯视");
  el("rect",{x:TX(-0.38),y:TY(-0.72),width:TX(0)-TX(-0.38),height:TY(0.25)-TY(-0.72),fill:css("--matc"),rx:4});
  el("text",{x:TX(-0.34),y:TY(-0.55),fill:muted,"font-size":10.5},"床");
  el("line",{x1:TX(0),y1:TY(-0.72),x2:TX(0),y2:TY(0.25),stroke:muted,"stroke-width":1,"stroke-dasharray":"3 3"});
  const lying=P.pose.S[1]<0.75;
  if(lying){el("line",{x1:TX(-0.2),y1:TY(-0.62),x2:TX(-0.2),y2:TY(0.18),stroke:ink,"stroke-width":7,"stroke-linecap":"round"});el("circle",{cx:TX(-0.2),cy:TY(-0.66),r:7,fill:surf,stroke:ink,"stroke-width":2.5})}
  else{const hu=Math.min(-0.04,P.pose.H[0]);el("line",{x1:TX(hu),y1:TY(0),x2:TX(Math.max(hu+0.2,P.pose.K[0]+0.05)),y2:TY(0),stroke:ink,"stroke-width":7,"stroke-linecap":"round"});el("circle",{cx:TX(hu-0.02),cy:TY(0),r:8,fill:surf,stroke:ink,"stroke-width":2.5})}
  const pv=[0.03,-0.24],a0=-90*Math.PI/180,a1=25*Math.PI/180,tp=a=>[pv[0]+AL*Math.cos(a),pv[1]+AL*Math.sin(a)],s0=tp(a0),s1=tp(a1),tip=tp(ps);
  el("path",{d:`M${TX(s0[0])} ${TY(s0[1])} A ${AL*140} ${AL*140} 0 0 1 ${TX(s1[0])} ${TY(s1[1])}`,fill:"none",stroke:amber,"stroke-width":1.5,"stroke-dasharray":"4 3",opacity:.8});
  el("line",{x1:TX(pv[0]),y1:TY(pv[1]),x2:TX(tip[0]),y2:TY(tip[1]),stroke:ink,"stroke-width":5,"stroke-linecap":"round"});
  el("circle",{cx:TX(pv[0]),cy:TY(pv[1]),r:5,fill:ink});
  el("circle",{cx:TX(tip[0]),cy:TY(tip[1]),r:5.5,fill:amber,stroke:surf,"stroke-width":2});
  el("text",{x:470,y:197,fill:muted,"font-size":11},"轻推后绕立柱转约 115°");
}
function render(P,i){(scheme==="A"?drawA:drawB)(P,i);shown=P}
function panel(i){const s=ST()[i];document.querySelectorAll("#tabs button").forEach((b,k)=>b.setAttribute("aria-pressed",String(k===i)));
  $("#spanel").innerHTML=`<div class="muted" style="font-size:12.5px">${scheme==="A"?"方案甲":"方案乙"} · 第 ${i+1} 步 / 共 ${ST().length} 步</div><h3>${s.k}</h3><dl class="kv"><dt>老人</dt><dd>${s.user}</dd><dt>${scheme==="A"?"扶手":"起身台"}</dt><dd>${s.dev}</dd><dt>判断依据</dt><dd>${s.check}</dd><dt>失效时</dt><dd>${s.fail}</dd></dl>`}
function tweenTo(i,dur){return new Promise(res=>{cancelAnimationFrame(raf);const to=paramsOf(ST()[i]),from=shown||to;
  if(reduceMotion||dur<=0||from===to){render(to,i);res();return}
  const t0=performance.now();const step=now=>{const t=Math.min(1,(now-t0)/dur);render(mix(from,to,ease(t)),t<1?-1:i);if(t<1)raf=requestAnimationFrame(step);else{render(to,i);res()}};raf=requestAnimationFrame(step)})}
function setState(i,dur){cur=i;panel(i);return tweenTo(i,dur==null?600:dur)}
function buildTabs(){$("#tabs").innerHTML=ST().map((s,i)=>`<button aria-pressed="false"><span class="num">${i+1}</span>${s.k}</button>`).join("")}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function stop(){playing=false;playToken++;$("#play").textContent="▶ 播放全过程"}
async function play(){const tok=++playToken;playing=true;$("#play").textContent="❚❚ 暂停";
  await setState(0,700);for(let i=1;i<ST().length;i++){await wait(1000);if(tok!==playToken)return;await setState(i,1700);if(tok!==playToken)return}
  await wait(800);if(tok===playToken)stop()}
buildTabs();
$("#tabs").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;stop();setState([...b.parentNode.children].indexOf(b))});
$("#play").onclick=()=>{if(playing)stop();else play()};
setState(5,0);
$("#scheme").addEventListener("click",e=>{const btn=e.target.closest("button");if(!btn)return;stop();scheme=btn.dataset.s;shown=null;
  document.querySelectorAll("#scheme button").forEach(x=>x.setAttribute("aria-pressed",String(x===btn)));
  $("#sceneKey").textContent=scheme==="A"?"扶手在没人握时转动；黄点 = 传感器":"橙色 = 可动台面；黄点 = 传感器";buildTabs();setState(scheme==="A"?3:5,0)});

'''
b = cut(b, '/* ================= PART 3: stepper ================= */', '/* scheme comparison */', stepper)
b = rep(b, 'const redraw=()=>{drawScene(cur);hdraw(+hs.value);window.__cmpDraw&&window.__cmpDraw()};',
        'const redraw=()=>{shown&&render(shown,cur);hdraw(+hs.value);window.__cmpDraw&&window.__cmpDraw();window.__expDraw&&window.__expDraw()};')

# ---------------- JS: explorer for scheme A ----------------
explorer_js = r'''/* scheme A explorer */
(function(){
const D=JSON.parse($("#xdata").textContent);
const RAMP=["#cde2fb","#9ec5f4","#6da7ec","#3987e5","#256abf","#184f95","#0d366b"];
const hx=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
function rc(v){const t=Math.max(0,Math.min(1,(v-0.3)/0.4))*(RAMP.length-1),i=Math.floor(t),f=t-i;if(i>=RAMP.length-1)return RAMP[RAMP.length-1];const a=hx(RAMP[i]),b=hx(RAMP[i+1]);return `rgb(${a.map((x,k)=>Math.round(x+(b[k]-x)*f)).join(",")})`}
const cv=$("#cv"),ctx=cv.getContext("2d"),Wd={x0:-0.75,x1:1.0,z0:0,z1:1.40};
let arm="strong",mode="front",ix=14,iz=8,ih=0,showHeat=true,scale=1;
const front=()=>D["front_"+arm],side=n=>D[`side${n}_${arm}`];
const bestOf=a=>a.reduce((m,d,k)=>d&&(m<0||d[0]<a[m][0])?k:m,-1);
function size(){const w=cv.clientWidth;if(!w)return;const h=Math.round(w*(Wd.z1-Wd.z0)/(Wd.x1-Wd.x0)),dpr=window.devicePixelRatio||1;cv.width=Math.round(w*dpr);cv.height=Math.round(h*dpr);cv.style.height=h+"px";ctx.setTransform(dpr,0,0,dpr,0,0);scale=w/(Wd.x1-Wd.x0);draw()}
const X=x=>(x-Wd.x0)*scale,Y=z=>(Wd.z1-z)*scale;
const curD=()=>mode==="front"?front()[iz][ix]:side(mode==="side2"?2:1)[ih];
const handleP=()=>mode==="front"?[D.xs[ix],D.zs[iz]]:[0.03,D.side_h[ih]];
function line(p,c,w){ctx.strokeStyle=c;ctx.lineWidth=w;ctx.lineCap="round";ctx.lineJoin="round";ctx.beginPath();p.forEach((q,k)=>k?ctx.lineTo(X(q[0]),Y(q[1])):ctx.moveTo(X(q[0]),Y(q[1])));ctx.stroke()}
function draw(){const w=cv.clientWidth,h=cv.clientHeight;if(!w)return;ctx.clearRect(0,0,w,h);ctx.fillStyle=css("--surface");ctx.fillRect(0,0,w,h);
  const ink=css("--ink"),muted=css("--muted"),amber=css("--amber");
  if(mode==="front"&&showHeat){const dx=0.05*scale;front().forEach((r,i)=>r.forEach((d,j)=>{if(!d)return;ctx.globalAlpha=.82;ctx.fillStyle=rc(d[0]);ctx.fillRect(X(D.xs[j])-dx/2,Y(D.zs[i])-dx/2,dx+.6,dx+.6)}));ctx.globalAlpha=1}
  ctx.fillStyle=css("--line");ctx.fillRect(X(-1),Y(0.42),X(0)-X(-1),Y(0)-Y(0.42));
  ctx.fillStyle=muted;ctx.font="12px "+css("--font-body");ctx.fillText("床 0.42 m",X(-0.6),Y(0.2));line([[Wd.x0,0],[Wd.x1,0]],muted,1.5);
  ctx.font="11px "+css("--font-mono");for(let z=0.5;z<1.3;z+=0.25)ctx.fillText(z.toFixed(2)+" m",4,Y(z)+4);
  if(mode!=="front"){ctx.globalAlpha=.5;line([[0.03,0.55],[0.03,1.2]],muted,6);ctx.globalAlpha=1;ctx.fillStyle=css("--ink2");ctx.font="12px "+css("--font-body");ctx.fillText("床沿扶手在身体侧面（投影）",X(0.06),Y(1.27))}
  const d=curD(),P=handleP(),st=d?d[10]:15,g=D.geo[String(st)],e=g.edge_x,rel=p=>[p[0]-e,p[1]];
  const H=rel(g.Hp),K=rel(g.K),A=rel(g.A),th=(d?d[1]:55)*Math.PI/180,S=[H[0]+D.L.tr*Math.sin(th),H[1]+D.L.tr*Math.cos(th)];
  line([[g.heel-e,0.005],[g.toe-e,0.005]],ink,4);line([S,H,K,A],ink,5);
  ctx.beginPath();ctx.fillStyle=css("--surface");ctx.strokeStyle=ink;ctx.lineWidth=4;ctx.arc(X(S[0]+0.12*Math.sin(th)),Y(S[1]+0.12*Math.cos(th)),0.075*scale,0,Math.PI*2);ctx.fill();ctx.stroke();
  if(d){line([S,[d[2],d[3]],P],ink,4);const k=0.0012,tip=[P[0]+d[4]*k,P[1]+d[5]*k];if(Math.hypot(d[4],d[5])>5){line([P,tip],amber,3);const ang=Math.atan2(-(tip[1]-P[1]),tip[0]-P[0]);ctx.fillStyle=amber;ctx.beginPath();ctx.moveTo(X(tip[0]),Y(tip[1]));ctx.lineTo(X(tip[0])-9*Math.cos(ang-.45),Y(tip[1])-9*Math.sin(ang-.45));ctx.lineTo(X(tip[0])-9*Math.cos(ang+.45),Y(tip[1])-9*Math.sin(ang+.45));ctx.closePath();ctx.fill()}}
  ctx.beginPath();ctx.arc(X(P[0]),Y(P[1]),8,0,Math.PI*2);ctx.fillStyle=amber;ctx.fill();ctx.lineWidth=3;ctx.strokeStyle=css("--surface");ctx.stroke()}
const bar=(l,v,c)=>`<div class="bar ${c||""}"><span>${l}</span><span class="track"><span class="fill" style="width:${Math.max(0,Math.min(1,v))*100}%"></span></span><span class="val">${v.toFixed(2)}</span></div>`;
function readout(){const d=curD(),r=D.ref,s2=side(2),s1=side(1);
  const refs=bar("不用手",r.none_042)+bar("双手撑床垫",r[arm].mattress_042)+bar("床沿扶手·双手",s2[bestOf(s2)][0])+bar("床沿扶手·单手",s1[bestOf(s1)][0]);
  if(!d){$("#eff").textContent="–";$("#cmpBars").innerHTML=refs;$("#joints").innerHTML="";$("#msg").innerHTML='<span class="warn">这个位置够不到，或会碰到腿和床。</span>';draw();return}
  $("#eff").textContent=d[0].toFixed(2);$("#cmpBars").innerHTML=refs+bar("当前位置",d[0],"cur");
  const two=mode!=="side1";$("#joints").innerHTML=bar("髋",Math.abs(d[6]))+bar("膝",Math.abs(d[7]))+bar(two?"肩（双手）":"肩（单手）",Math.abs(d[8]))+bar(two?"肘（双手）":"肘（单手）",Math.abs(d[9]));
  const F=Math.hypot(d[4],d[5]),worst=["髋","膝","肩","肘"][[d[6],d[7],d[8],d[9]].map(Math.abs).reduce((m,v,k,a)=>v>a[m]?k:m,0)];
  $("#msg").innerHTML=`手上的力 ${F.toFixed(0)} N（${(F/D.BW*100).toFixed(0)}% 体重），躯干前倾 ${d[1]}°；此时最吃力的是${worst}。橙色箭头是扶手作用在手上的力。`;draw()}
function pick(ev){if(mode!=="front")return;const r=cv.getBoundingClientRect(),x=Wd.x0+(ev.clientX-r.left)/scale,z=Wd.z1-(ev.clientY-r.top)/scale;
  ix=Math.max(0,Math.min(D.xs.length-1,Math.round((x-D.xs[0])/0.05)));iz=Math.max(0,Math.min(D.zs.length-1,Math.round((z-D.zs[0])/0.05)));readout()}
let drag=false;cv.addEventListener("pointerdown",e=>{drag=true;cv.setPointerCapture(e.pointerId);pick(e)});cv.addEventListener("pointermove",e=>{if(drag)pick(e)});cv.addEventListener("pointerup",()=>drag=false);
const hsl=$("#hSlider");hsl.min=0;hsl.max=D.side_h.length-1;hsl.step=1;const setH=()=>{$("#hVal").textContent=D.side_h[ih].toFixed(3)};
hsl.addEventListener("input",()=>{ih=+hsl.value;setH();readout()});
function setMode(m){mode=m;[["mFront","front"],["mSide2","side2"],["mSide1","side1"]].forEach(([id,k])=>$("#"+id).setAttribute("aria-pressed",String(k===m)));$("#sideCtl").hidden=m==="front";
  if(m!=="front"){ih=bestOf(side(m==="side2"?2:1));hsl.value=ih;setH()}readout()}
$("#mFront").onclick=()=>setMode("front");$("#mSide2").onclick=()=>setMode("side2");$("#mSide1").onclick=()=>setMode("side1");
$("#armSeg").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;arm=b.dataset.a;document.querySelectorAll("#armSeg button").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));setMode(mode)});
$("#heat").addEventListener("change",e=>{showHeat=e.target.checked;draw()});
window.addEventListener("resize",size);window.__expDraw=draw;size();readout();
})();

'''
b = rep(b, '/* height chart */', explorer_js + '/* height chart */')
for a_,c_ in [
 ('stance:"兼容：床本身不改，原有的床栏照常使用。"','stance:"方案甲：收起的扶手就是床栏，拉着它翻身坐起。方案乙：起身台扶手靠床的一端紧贴床沿，同样可以拉着坐起。两个方案在这一段都不额外助力。"'),
 ('stance:"坐到床沿后，把腿放上起身台的斜台；台面升平后向前挪上去，横向挪动变成向前挪。"','stance:"方案甲：扶着收起的扶手挪到床沿。方案乙：拉着台架扶手挪到床沿，把腿放上斜台，台面升平后向前挪上台面。"'),
 ('<p>现有床栏已经能应付这一段，方案只需要不妨碍它。</p>','<p>两个方案在这一段都提供扶点（见方案演示），但不额外助力。</p>'),
 ('["本组方案甲（目标）","动态扶手：收起即床栏，坐到床沿后自动转到身前；不抬升","","SSSSPSP-"]','["本组方案甲（目标）","动态扶手：收起即床栏；轻推后转到工作角度，一用力就锁；不抬升","","SSSSPSP-"]'),
 ('["本组方案乙（目标）","床边起身台：斜台接腿 → 平台 → 后高前低抬升；扶手固定在台架上","","-SSSSSP-"]','["本组方案乙（目标）","床边起身台：扶手近端兼作床栏；斜台接腿 → 平台 → 后高前低抬升","","PSSSSSP-"]'),
 ('扶手装在床上，平时当床栏；老人坐到床沿后，扶手自动转到他身前。','扶手装在床上，平时当床栏；老人坐到床沿后轻推一下，扶手带着手转到工作位置，一用力就锁死。'),
 ('["核心思路","扶手装在床上，平时当床栏；坐到床沿后，没人握时自动转到身前约 0.8 m"','["核心思路","扶手装在床上，平时当床栏；坐到床沿后轻推一下，扶手带着手转到工作角度（约 0.8 m 高），一用力就锁死"'),
 ('["运动部件","1 个：扶手摆动"','["运动部件与传感","1 个：扶手摆动；只需扶手测力"'),
 ('"2 段台面（或 1 套连杆）"]','"2 段台面（或 1 套连杆）；台面和扶手测力"]'),
 ('["主要风险","扶手移动时碰到人、误展开、夹手"','["主要风险","转动时手在扶手上（低速、限扭矩、一用力就锁）、夹手、展开后挡路"'),
 ('["差别靠什么","“自动换位”，依赖“老人夜里不会自己扳”的假设，目前没有证据"','["差别靠什么","“轻推即转、承重即锁”的交互，依赖“老人夜里做不好手动解锁和扳动”的假设，目前没有证据"'),
 ('["A","自动换位的扶手","老人自己","手臂和握力要够","不用操作；扶手只在没人握时移动"]','["A","轻推即转、承重即锁的扶手","老人自己","手臂和握力要够","不用找锁扣；一用力就锁死"]'),
 ('动态扶手在没人握时自动换位。但这个差别依赖一个还没有证据的假设：老人夜里不会自己去扳。','动态扶手不用找锁扣：轻推就转、一用力就锁，转动由电机辅助。但这个差别依赖一个还没有证据的假设：老人夜里做不好手动解锁和扳动。'),
 ('"扶手在没人握时转动；黄点 = 传感器"','"轻推扶手才会转；黄点 = 传感器"'),
]:
    assert a_ in b, a_[:60]
    b=b.replace(a_,c_)
open(P + "v9_body.html", "w").write(b)

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
'''
page = head + extra + '\n</style>\n' + b
hd = json.load(open('/home/claude/bedexit_model/seat_height_v2.json'))
hd = {k: hd[k] for k in ["none", "mattress", "handle10", "handle30"]}
page = page.replace('__HDATA__', json.dumps(hd, separators=(',', ':')))
page = page.replace('__XDATA__', open('/home/claude/bedexit_model/explorer_v7.json').read())
open(P + "bedexit_proposal.html", "w").write(page)
print("ok", len(page))
