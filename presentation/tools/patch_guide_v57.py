"""Patch the published talk guide (起身台汇报讲稿) for deck v5.7: CAD model, cantilever page, fall prevention, FEA next steps.
Usage: python3 patch_guide_v57.py <guide_in.html> <deck_root> <thumb_dir> <guide_out.html>
  guide_in   the saved published guide (one <article> per slide + a JSON blob `const D=` for the builder)
  deck_root  folder holding project/deck.json and project/slides/*.html (speaker notes = each slide's <aside>)
  thumb_dir  <id>.png renders at 1920x1080 for every slide in CHG and NEW
What it does:
  * changed slides (CHG): new thumbnail and script; optional new key point, Q&A edits and to-dos
  * new slides (NEW): a new <article> inserted after its predecessor in the deck order
  * every article renumbered from deck.json; builder check-boxes, the JSON blob and the to-do table rebuilt
"""
import base64, html, io, json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PJ = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/parts.json")))
LT = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/lateral.json")))["summary"]
EX = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/exit_detect.json")))
st_ = PJ["statics"]; c1 = PJ["c1"]; car = PJ["carriage"]; tip = PJ["tipping"]
EXB = EX["results"]["base"]; EXW = EX["results"]["worst"]
r2 = lambda x: f"{round(x + 1e-9, 2):.2f}"

GROUPS = [("开场", ["cover", "agenda"]), ("1 问题与用户", ["problem", "users"]), ("2 方案", ["prior", "concept", "whynot"]),
          ("3 机构与结构", ["mech_path", "mech_select", "mechanism", "cantilever", "motion", "stability"]),
          ("4 控制与安全", ["sensing", "statemachine", "speed", "risk", "fall_side", "fall_exit"]),
          ("5 验证与总结", ["verify", "limits", "nextsteps", "conclusion", "team"]),
          ("附录 · 本次沟通", ["appendix", "parts", "drawings", "sizing", "questions"])]
SEC = {sid: g for g, ids in GROUPS for sid in ids}
APPX = {"appendix", "parts", "drawings", "sizing"}

FEA_TODO = ("FEA：四个部位的应力和变形（滑块板 + 轴承座焊接件、横梁焊缝、机构箱开槽侧板、扶手立柱；载荷、边界条件、判据在机构网页）", "角色 4", "11/3 必须")

# ------------------------------------------------------------------ new slides: title, minutes, status, key point, Q&A, to-dos
NEW = {
 "mech_path": dict(t="机构设计①：座板该怎么走", m=1.1, st="ok",
   key="先定路径再选机构：81 个人各自理想的座板路径都是先往前、再往上，竖直升降跟不上（11/81）；一个电机只能走一条路，选跟得上走得最靠前的人的那条，80/81 合格。",
   ask=[("为什么选“最靠前”的那条，不选平均的？", "座板走得比某人的理想位置靠前，只是托在他大腿更靠前处，人不会滑；走得靠后，臀部就从座板前缘滑出去。所以要跟得上走得最靠前的人。81 人逐个检查，80 人合格，差的那位前滑超了 4 mm。"),
        ("前倾为什么限 15°？", "人往回坐时，座板前倾越大越容易顺坡滑：不滑要求摩擦系数大于 tan 前倾，15° 时约 0.27。我们按高摩擦面料 μ ≥ 0.5 选，留了余量。"),
        ("81 个人是真实数据吗？", "不是。是 3 种身高 × 3 种臀厚 × 3 种起身习惯 × 3 种脚位组合出的模拟用户，起身动作由二维模型算出，要用真实起身动作数据核对。")], todo=[]),
 "mech_select": dict(t="机构设计②：比了五种机构", m=1.1, st="ok",
   key="同一组约束、同样 81 人比了五种机构：竖直跟不上；四连杆放中间碰腿、放两侧挡回床、只放一侧扛不住偏载；斜导轨 + 倾角连杆轨迹最准、驱动力最小，代价是箱子高。",
   ask=[("单侧四连杆箱子小一半，为什么不用？", "座板挂在一侧，偏载要靠座板上两个相距 8 cm 的铰点形成力偶，再靠连杆面外弯曲传到地面，地面铰点轴承要承受约 25 kN，是导轨方案每个滑块的约 8 倍；站直时连杆还会碰小腿，70/81 合格。如果以后箱顶高度成了硬约束，它是备选。"),
        ("带 * 的两种为什么没重算？", "它们在“起身路径只算到三分之二”的问题修正之前，就因为碰腿、挡回床被淘汰了；修正只会让合格人数变少，不会改变结论。"),
        ("箱顶 0.89 m 会不会挡住人？", "机构箱在床头一侧，人坐在座板上时它在身体侧面，不在面前；扶手横杆在人正前方。主要影响是占地和外观。")], todo=[]),
 "cantilever": dict(t="单侧悬臂怎么扛住", m=0.9, st="ok",
   key=f"座板只挂在一侧：偏载力矩 {st_['c1_moment_Nm']['value']} N·m 由铰点 1 的一对圆锥滚子轴承（相距 45 mm）接住，安全系数 {c1['sf']:.1f}；再经滑块板交给 4 个滑块（安全系数 {car['sf']:.1f}）。",
   ask=[("为什么不用交叉滚子轴承？", f"能扛住这个力矩的型号（RU85）外径 120 mm，装上后离床垫只剩 {c1['why_not_crossed_roller']['RU85']['bed_gap_cm']} cm；小一号的 RU66 当量静载 {c1['why_not_crossed_roller']['RU66']['P0_kN']} kN，已经接近额定 {c1['why_not_crossed_roller']['RU66']['C0_kN']} kN。一对 32006 X（外径 55）背对背、相距 45 mm，装在 Ø75 的轴承座里，当量静载 {c1['P0_kN']} kN，额定 {c1['C0_kN']:.0f} kN。"),
        ("座板外缘下沉 4 mm，人能感觉到吗？", f"约 4 mm 分布在座板外缘到铰点约 48 cm 的距离上，横向倾斜约 0.5°。其中横梁弯曲约 1.6 mm、轴承对约 0.7 mm（刚度是假设值，取决于预紧），其余来自轴、滑块和机构箱。轴承预紧要样件实测。"),
        ("这些数靠得住吗？", "是手算：三维静力平衡加梁公式，载荷取最坏组合（100 kg × 1.5、偏 10 cm、0.3 倍侧推）。焊缝和开孔附近的应力集中手算算不准，所以列为有限元的第一优先（“下一步”页）。轴承和滑块额定值来自经销商资料，要用厂家样本核对。")],
   todo=[]),
 "fall_side": dict(t="防跌倒①：侧向摔倒", m=1.1, st="part",
   key=f"侧向最弱的时刻是放开座板、只靠双脚（{LT['none_open_after_release']['v_crit_min_med']:.2f} m/s），从床上站起来也一样；起身台多出的风险是坐着从敞开侧摔下时落差 {LT['hip_drop_open_side']['seated_max_med']:.2f} m，和 0.58 m 的床差不多。",
   ask=[("“推到多快会倒”是什么意思？", f"把身体侧向推到这个速度，按“外推重心”判据（重心位置加上速度 × √(重心高度 / g)）就越过脚或坐垫的外缘。它是一个比较用的量：坐在低床沿约 {LT['start_seated_vs_bed']['bed042_v_med']:.2f}，坐在起身台上最弱约 {LT['none_open_seated']['v_crit_min_med']:.2f}。“轻推一下约 0.1–0.3 m/s”是粗略估计，没有实测。"),
        ("为什么横杆往敞开侧加长没用？", f"加长后两只手对称地握在身体两侧，往敞开侧倒时，手拉住的力臂反而变短（坐着 {r2(LT['current_force_open_seated']['v_crit_min_med'])} → {r2(LT['M1_force_open_seated']['v_crit_min_med'])}）；而且横杆悬臂更长，Ø38×4 的管会超应力，要换 Ø42.4×4。"),
        ("敞开侧加挡板会不会挡住回床？", "所以只能做成可翻下的：坐着时立起，回床时放下。缺点和翻转横杆一样，可能忘了立起来，要加“已立起”检测。另一个办法是靠座板下的四个测力单元，发现压力中心往敞开侧偏就停、不抬，不加零件，但还没仿真。"),
        ("坐着摔下来 0.63 m，有多危险？", f"比低床（{LT['hip_drop_open_side']['bed042_med']:.2f} m）高约 22 cm，和坐在 0.58 m 床沿摔下（{LT['hip_drop_open_side']['bed058_med']:.2f} m）差不多；站着侧摔的落差更大。所以起身台没有带来新类型的风险，但让坐着的阶段像坐在高床上。"),
        ("模型漏了什么？", "准静态、只看正面：没有迈步自救、没有肌肉反应，手按“抓得住”的上限算。它只能用来比较方案，不能预测真实摔倒的概率。")],
   todo=[("决定敞开侧对策：可翻下的挡板，或座板测力发现重心侧偏就停（后者要先仿真）", "角色 2、3、5", "11/3")]),
 "fall_exit": dict(t="防跌倒②：离开踏板时摔倒", m=1.1, st="part",
   key=f"不加传感器：踏板和横杆测力里有区分摔倒的信息，合成数据上每 100 次正常离开误报 5 次时检出约 {EXB['tpr_at_fa_per100']['5'] * 100:.0f}%（最坏 {EXW['tpr_at_fa_per100']['5'] * 100:.0f}%）；但数据是我们自己生成的，必须实测；认出来只能报警。",
   ask=[("检测到以后能做什么？", "只能报警：开灯、语音问一句、30 秒没回应就呼叫家属。挡不住这一次摔倒，但能缩短倒地后没人知道的时间。"),
        ("98% 可信吗？", "不可信到这个程度。摔倒过程是我们用倒立摆模型生成的，检测器又在同类数据上训练，结果偏乐观。它说明的是“现有传感器里有区分信息”，不是真实检出率。所以下一步是实测：志愿者在软垫上做摔倒动作、录老人的正常离开，检出 ≥ 80%、误报 ≤ 5 次 / 100 才继续。"),
        ("会不会老误报？", f"按每晚起来 {EX['false_alarm_cost']['exits_per_day']} 次估算，用简单的三条阈值规则（误报 {EXB['rule']['false_alarms_per100']} 次 / 100）大约每周 {EX['false_alarm_cost']['rule_false_prompts_per_week']} 次语音询问，按一下握把按钮就取消。"),
        ("哪种摔法最难认？", f"脚往侧面一滑（{EXB['detect_by_kind_at_5fa']['slip'] * 100:.0f}%）和踩一步想救回来又摔倒（{EXB['detect_by_kind_at_5fa']['rescue_step'] * 100:.0f}%），因为它们开头像正常迈步。"),
        ("人走下踏板后再摔呢？", "这些传感器看不到，要用床边毫米波雷达或可穿戴报警器，不在本项目范围。")],
   todo=[("实测验证离开踏板的摔倒检测：志愿者软垫摔倒动作 + 老人正常离开（≥ 80% 检出、≤ 5 次误报 / 100 才继续）", "角色 5", "11/3 之后")]),
 "nextsteps": dict(t="下一步：建模和有限元", m=0.6, st="part",
   key="交给建模和有限元的四个部位：滑块板 + 轴承座焊接件、横梁焊缝、机构箱开槽侧板、扶手立柱。都是手算找出的薄弱处，还不是有限元结果。",
   ask=[("为什么是这四个？", "按手算的应力比，以及手算算不准的程度排：焊缝和开孔附近有应力集中，梁公式算不出来；扶手立柱根部弯矩最大（约 1.5 kN·m）。"),
        ("边界条件怎么给？", "机构网页“有限元重点”一节里每个部位都写了：载荷向量（最坏工况）、固定面、要输出的量和判据；零件的 STEP 文件可以直接下载。")],
   todo=[FEA_TODO]),
 "parts": dict(t="附录：零件编号", m=0, st="ok", key="被问到某个零件时用这一页定位；编号和工程图一一对应。", ask=[], todo=[]),
 "drawings": dict(t="附录：工程图", m=0, st="ok", key="总装图和四张关键零件图；完整 23 张零件图和 STEP 在机构网页。", ask=[], todo=[]),
}

# ------------------------------------------------------------------ changed slides
_CANT_NEW = ("单侧机构，座板是悬臂，扛得住吗？", f"见下一页：偏载在铰点 1 处约 {st_['c1_moment_Nm']['value']} N·m，由一对相距 45 mm 的圆锥滚子轴承接住（安全系数 {c1['sf']:.1f}），再经滑块板交给 4 个滑块（最重的 {car['P0_kN']} kN，安全系数 {car['sf']:.1f}）。")
CHG = {
 "cover": dict(),
 "mechanism": dict(st="ok", key="机构设计第三步：在座板上找两个点，一个轨迹接近直线（装滑块走导轨），一个接近圆弧（用连杆拉到 B）；只搜 4 个数，导轨与竖直 34°、连杆 465 mm，最多差 8 mm。",
   h3="机构设计③：斜导轨 + 倾角连杆", ask_replace={"单侧机构，座板是悬臂，扛得住吗？": _CANT_NEW},
   ask_add=[("左边的三维图是 CAD 吗？", "是。用 CadQuery 按手算选定的尺寸建了 40 个零件，干涉检查只剩两处接触；STEP 文件、工程图都在机构网页上。")],
   todo_set=[]),
 "motion": dict(st="part", ask_replace={"动画是按真实尺寸做的吗？": ("动画是按真实尺寸做的吗？", "由二维模型直接画出：人体按 1.60 m 的比例，机构按计算出的铰点和导轨。右下角的三个位置是 CAD 模型截图，和动画用的是同一套尺寸。")},
   todo_set=[("CAD 运动动画（老师邮件里明确要求）：CAD 模型已有，按行程表的位置导出帧，或导入 SolidWorks 做运动算例", "角色 3", "11/3 必须")]),
 "sizing": dict(st="part", h3="附录：驱动选型", key=f"滚珠丝杠起身推力 ≤ 664 N，猛坐静载约 2.0 kN；失电制动抱住、离心限速应急下降；偏载 {st_['c1_moment_Nm']['value']} N·m 经铰点 1 轴承对到双导轨；型号已初选，待样本核对。",
   todo_set=[("用厂家样本核对已初选的型号：丝杠 R16-10、导轨 HGR15 + 滑块 HGH15CA、轴承 32006 X、8 N·m 制动器、电机约 26 W", "角色 4", "11/3")]),
 "stability": dict(key=f"人在台上不会翻；人不在台上时往床头方向推 {tip['结论']['min_tip_force_N']} N 就翻（台架按零件估约 85 kg），所以和床固定，固定件按 {tip['固定件拉力（ADA 609 扶手设计载荷 1112 N，安全系数 1.5）']['anchor_N']} N 设计。",
   text_replace=[("107 N", f"{tip['结论']['min_tip_force_N']} N"), ("107 牛", f"{tip['结论']['min_tip_force_N']} 牛")]),
 "risk": dict(text_replace=[("107 N", f"{tip['结论']['min_tip_force_N']} N")],
   ask_add=[("老人会不会从座板侧面摔下去？有跌倒检测吗？", "后两页专门讲：侧向摔倒做了一个比较模型；离开踏板时的摔倒，用现有的踏板和横杆测力检测，原理上可行但还要实测。")]),
 "limits": dict(),
 "appendix": dict(),
 "questions": dict(key="只问方向和程度，不问细节：差在哪、各块做多深、仿真验证够不够、汇报重点和时长。记下回答，当天发到群里。本次沟通用，正式汇报删去。", h3="想请老师给个方向"),
}

PILL = dict(ok=("p-ok", "内容齐"), part=("p-part", "部分待补"), gap=("p-gap", "待补"))
esc = lambda s: html.escape(s, quote=False)


def aside(root, sid):
    h = open(os.path.join(root, "project/slides", f"{sid}.html")).read()
    return re.search(r"<aside>(.*?)</aside>", h, re.S).group(1).strip()


def thumb(path):
    im = Image.open(path).convert("RGB").resize((560, 315), Image.LANCZOS); b = io.BytesIO(); im.save(b, "WEBP", quality=72)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode()


def todo_html(todo):
    return '\n  <ul class="todo">' + "".join(f'<li><b>待补：</b>{w} <span style="color:var(--muted)">· {who} · {when}</span></li>' for w, who, when in todo) + "</ul>" if todo else ""


def ask_html(ask):
    return '\n  <div><p class="lbl">可能被问到</p><dl class="qa">' + "".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in ask) + "</dl></div>" if ask else ""


def get_ask(a):
    m = re.search(r'<dl class="qa">(.*?)</dl>', a, re.S)
    return re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", m.group(1), re.S) if m else []


def get_todo(a):
    return re.findall(r'<li><b>待补：</b>(.*?) <span style="color:var\(--muted\)">· (.*?) · (.*?)</span></li>', a)


def set_body(a, ask, todo):
    a = re.sub(r'\n  <ul class="todo">.*?</ul>', "", a, flags=re.S)
    a = re.sub(r'\n  <div><p class="lbl">可能被问到</p>.*?</dl></div>', "", a, flags=re.S)
    a = a.replace("\n </div>\n</article>", todo_html(todo) + ask_html(ask) + "\n </div>\n</article>")
    return re.sub(r'data-todo="\d"', f'data-todo="{1 if todo else 0}"', a, count=1)


def new_article(sid, u, script, img):
    cls, lab = PILL[u["st"]]
    a = (f'<article class="srow" id="s-{sid}" data-id="{sid}" data-todo="0">\n'
         f' <div class="side"><img src="{img}" alt="第 0 页：{esc(u["t"])}" loading="lazy"><span class="sec">{SEC[sid]}</span></div>\n'
         f' <div class="txt">\n  <div class="meta"><span class="no">第 0 页</span><h3>{esc(u["t"])}</h3><span class="pill {cls}">{lab}</span>'
         f'<span class="merged" hidden>和上一页合并讲</span><span class="time"></span></div>\n'
         f'  <p class="keyl"><b>这一页要让听众记住：</b>{esc(u["key"])}</p>\n'
         f'  <div><p class="lbl">讲稿</p><p class="say">{script}</p></div>\n </div>\n</article>')
    return set_body(a, u["ask"], u["todo"])


if __name__ == "__main__":
    gin, root, tdir, gout = sys.argv[1:5]; h = open(gin).read()
    order = json.load(open(os.path.join(root, "project/deck.json")))["order"]
    art = lambda sid: (lambda i: (i, h.index("</article>", i) + len("</article>")))(h.index(f'<article class="srow" id="s-{sid}"'))
    # 1) changed slides
    for sid, u in CHG.items():
        i, j = art(sid); a = h[i:j]
        a = re.sub(r'<img src="data:image/webp;base64,[^"]+"', f'<img src="{thumb(os.path.join(tdir, sid + ".png"))}"', a)
        a = re.sub(r'(<p class="say">).*?(</p>)', lambda m: m.group(1) + aside(root, sid) + m.group(2), a, flags=re.S)
        if u.get("key"):
            a = re.sub(r'(<p class="keyl"><b>这一页要让听众记住：</b>).*?(</p>)', lambda m: m.group(1) + esc(u["key"]) + m.group(2), a, flags=re.S)
        if u.get("h3"):
            a = re.sub(r"<h3>[^<]*</h3>", f"<h3>{u['h3']}</h3>", a, count=1); a = re.sub(r'alt="第 (\d+) 页：[^"]*"', lambda m: f'alt="第 {m.group(1)} 页：{u["h3"]}"', a, count=1)
        if u.get("st"):
            cls, lab = PILL[u["st"]]; a = re.sub(r'<span class="pill p-[a-z]+">[^<]*</span>', f'<span class="pill {cls}">{lab}</span>', a, count=1)
        ask, todo = get_ask(a), get_todo(a)
        ask = [u.get("ask_replace", {}).get(q, (q, x)) for q, x in ask] + u.get("ask_add", [])
        if "todo_set" in u: todo = u["todo_set"]
        a = set_body(a, ask, todo)
        for x, y in u.get("text_replace", []): a = a.replace(x, y)
        h = h[:i] + a + h[j:]
    # 2) new slides, inserted after their predecessor in the deck order
    for sid in [s for s in order if s in NEW]:
        if f'id="s-{sid}"' in h: i, j = art(sid); h = h[:i] + h[j:].lstrip("\n")
        prev = order[order.index(sid) - 1]; _, j = art(prev)
        h = h[:j] + new_article(sid, NEW[sid], aside(root, sid), thumb(os.path.join(tdir, sid + ".png"))) + h[j:]
    # sizing's title follows the slide
    # 2b) put the articles in deck order
    arts = {sid: h[slice(*art(sid))] for sid in order}
    first = min(art(sid)[0] for sid in order)
    for sid in order:
        i, j = art(sid); h = h[:i] + h[j:].lstrip("\n")
    h = h[:first] + "".join(arts[sid] for sid in order) + h[first:]
    # 3) renumber every article from the deck order
    for n, sid in enumerate(order, 1):
        i, j = art(sid); a = h[i:j]
        a = re.sub(r'<span class="no">第 \d+ 页</span>', f'<span class="no">第 {n} 页</span>', a, count=1)
        a = re.sub(r'alt="第 \d+ 页：', f'alt="第 {n} 页：', a, count=1)
        a = re.sub(r'<span class="sec">[^<]*</span>', f'<span class="sec">{SEC[sid]}</span>', a, count=1)
        h = h[:i] + a + h[j:]
    # 4) JSON blob
    i = h.index("const D="); j = h.index(";\n", i); D = json.loads(h[i + len("const D="):j])
    old = {s["id"]: s for s in D["slides"]}; slides = []; todo_ids = set()
    for n, sid in enumerate(order, 1):
        a = h[slice(*art(sid))]; t = re.search(r"<h3>([^<]*)</h3>", a).group(1)
        m = 0 if sid in APPX else old[sid]["m"] if sid in old else NEW[sid]["m"]; td = bool(get_todo(a)); todo_ids |= {sid} if td else set()
        slides.append(dict(id=sid, n=n, t=html.unescape(t), m=m, todo=td))
    D["slides"] = slides
    D["formal"] = [s for s in order if s not in ("questions", "parts", "drawings", "sizing")]
    D["short"] = ["cover", "problem", "concept", "whynot", "mechanism", "stability", "speed", "risk", "fall_side", "verify", "conclusion"]
    h = h[:i] + "const D=" + json.dumps(D, ensure_ascii=False) + h[j:]
    # 5) builder check-boxes (regenerated from the groups)
    SL = {s["id"]: s for s in slides}
    def opt(sid):
        s = SL[sid]; pill = " <span class='pill p-part'>待补</span>" if s["todo"] else ""
        tt = "附录" if sid in APPX else "讨论" if sid == "questions" else f"{s['m']:.1f}"
        return f'<label class="opt"><input type="checkbox" id="c-{sid}" data-id="{sid}"><span><b>{s["n"]}</b> {esc(s["t"])}{pill}</span><span class="t">{tt}</span></label>'
    blk = "".join(f'<p class="grp-h">{g}</p><div class="opts">' + "".join(opt(s) for s in ids) + "</div>" for g, ids in GROUPS)
    i = h.index("<h3>页面</h3>") + len("<h3>页面</h3>"); j = h.index('\n  <h3 style="margin-top:14px">合并讲</h3>', i)
    h = h[:i] + blk + h[j:]
    # 6) script: appendix pages untimed; reset stored selections so the new pages show
    h = h.replace('if(id!=="appendix"&&id!=="questions") pages++;', 'if(!["appendix","parts","drawings","sizing","questions"].includes(id)) pages++;')
    h = h.replace('id==="appendix"?"不计时长"', '["appendix","parts","drawings","sizing"].includes(id)?"不计时长"')
    h = h.replace('const KEY="riser-talk-guide-v2";', 'const KEY="riser-talk-guide-v3";')
    # 7) to-do table, counts, header text
    rows, n_must = [], 0
    for n, sid in enumerate(order, 1):
        a = h[slice(*art(sid))]; t = SL[sid]["t"]
        for w, who, when in get_todo(a):
            must = "必须" in when; n_must += must
            rows.append(f'<tr><td><a href="#s-{sid}">{n} {esc(t)}</a></td><td>{w}</td><td style="white-space:nowrap">{who}</td><td><span class=\'pill {"p-gap" if must else "p-part"}\'>{when}</span></td></tr>')
    i = h.index('<div class="box scroll"><table><thead><tr><th style="width:20%">在哪一页</th>'); i = h.index("<tbody>", i) + len("<tbody>"); j = h.index("</tbody>", i)
    h = h[:i] + "".join(rows) + h[j:]
    h = re.sub(r'<p class="lab">待补</p><p class="big">\d+ 项</p><p class="d">.*?</p>',
               f'<p class="lab">待补</p><p class="big">{len(rows)} 项</p><p class="d">其中 {n_must} 项 11/3 必须有：CAD 运动动画、FEA（四个部位）。CAD 零件和工程图已有。</p>', h, flags=re.S)
    main = [s for s in slides if s["id"] not in APPX | {"questions"}]; tot = sum(s["m"] for s in main)
    h = re.sub(r'<p class="lab">正式汇报完整讲一遍</p><p class="big">约 \d+ 分钟</p><p class="d">.*?</p>',
               f'<p class="lab">正式汇报完整讲一遍</p><p class="big">约 {round(tot)} 分钟</p><p class="d">{len(main)} 页主 slides 合计约 {tot:.1f} 分钟（含指图讲解）；附录不计时长。超时就用下面的“时间紧”。</p>', h, flags=re.S)
    h = re.sub(r'<p class="lead"><b>10/27 更新：</b>.*?</p>',
               f'<p class="lead"><b>10/27 晚更新（v5.7）：</b>机构部分改成三页“机构设计”（座板该怎么走 → 比了五种机构 → 斜导轨 + 倾角连杆怎么定尺寸），驱动选型挪到附录；新增“单侧悬臂怎么扛住”、两页防跌倒（侧向摔倒、离开踏板时摔倒）、“下一步：建模和有限元”，附录加零件编号、工程图和驱动选型；稳定性按约 85 kg 的台架重算。<br>配合 {len(order)} 页 slides 使用：{len(main)} 页主 slides、4 页附录，加 1 页只在沟通时用的问题页。讲稿按课堂汇报的口吻写，和 slides 备注一致；还没做完的部分在页面上标了“待补”。</p>', h, count=1, flags=re.S)
    h = h.replace('<button type="button" data-preset="consult">明天沟通：全部 21 页</button>', f'<button type="button" data-preset="consult">沟通：全部 {len(order)} 页</button>')
    h = h.replace("缩略图按 10/27 的 slides 渲染；动画由二维模型画出，是示意，不是 CAD。", "缩略图按 10/27 晚的 slides 渲染；动画由二维模型画出，三维图和工程图来自 CAD 模型（cad/model）。")
    open(gout, "w").write(h); print("written", gout, len(h), "bytes;", len(rows), "to-dos;", f"main {len(main)} pages {tot:.1f} min")
