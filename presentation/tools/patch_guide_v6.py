"""Patch the published talk guide (起身台汇报讲稿) for deck v6, the 15-minute version:
46 s film after the cover; problem + users merged; sensing + speed merged; cantilever folded into mechanism;
concept, cantilever, speed, fall_exit, nextsteps moved to the appendix; shorter speaker notes everywhere.
Usage: python3 patch_guide_v6.py <guide_in.html> <deck_root> <thumb_dir> <guide_out.html>
  guide_in   the saved published guide (one <article> per slide + a JSON blob `const D=`)
  deck_root  folder holding project/deck.json and project/slides/*.html (speaker notes = each slide's <aside>)
  thumb_dir  <id>.png renders at 1920x1080; slides without a png keep their old thumbnail
"""
import base64, html, io, json, os, re, sys
from PIL import Image

gin, root, tdir, gout = sys.argv[1:5]
h = open(gin).read()
order = json.load(open(os.path.join(root, "project/deck.json")))["order"]
MAIN = order[:order.index("appendix")]
APPX = [s for s in order[order.index("appendix"):] if s != "questions"]
GROUPS = [("开场", ["cover", "film", "agenda"]), ("1 问题与用户", ["problem"]), ("2 方案", ["prior", "whynot"]),
          ("3 机构与结构", ["mech_path", "mech_select", "mechanism", "motion", "stability"]),
          ("4 控制与安全", ["sensing", "statemachine", "risk", "fall_side"]),
          ("5 验证与总结", ["verify", "limits", "conclusion", "team"]),
          ("附录 · 本次沟通", APPX + ["questions"])]
SEC = {sid: g for g, ids in GROUPS for sid in ids}
assert sorted(SEC) == sorted(order), set(order) ^ set(SEC)
PILL = dict(ok=("p-ok", "内容齐"), part=("p-part", "部分待补"), gap=("p-gap", "待补"))
esc = lambda s: html.escape(s, quote=False)
NO_THUMB = {"team", "nextsteps"}          # their renders lack images we have no local copy of; keep the old thumbnails

# ------------------------------------------------------------------ titles, key points, Q&A, to-dos that change
CHG = {
 "agenda": dict(key="五部分，主讲约 14 分钟（含 46 秒短片）；细节都在附录。"),
 "problem": dict(h3="问题与用户", key="三个数说明矛盾：一半人从 38 cm 的床站不起来；床高上限约 0.58 m；22% 有体位性低血压。用户是能走、但从普通床起身困难的老人；六条设计要求最后逐条验证。"),
 "prior": dict(key="现有方案各有所长：借鉴“按住才动、断电用电池降”和受力互锁；不同在于放在床边、床不换，座板跟着大腿走。"),
 "whynot": dict(h3="和其他起身方式比较", key="省力只和抬高床相当（再省约 10%，22/81 人略费力）；真正的差别在腿一软时：人起到一半臀部已在床沿外约 25 cm，座板一路跟在下面（直着落：床 15%，座板全程）。往后倒时床更好 → 后缘软包。"),
 "mechanism": dict(h3="机构设计③：斜导轨 + 倾角连杆，单侧悬臂", key="在座板上找两个点：轨迹近直线的走导轨，近圆弧的用连杆拉到 B；只搜 4 个数，最多差 8 mm。单侧偏载约 586 N·m 由一对圆锥滚子轴承接住，再交给双导轨（安全系数 3.2 / 2.5）。",
   ans_text=[("见下一页：", "见本页右下（完整校核在附录“单侧悬臂”页）：")], ask_from="cantilever"),
 "motion": dict(key="短片里的四步，CAD 零件按真实运动学驱动；前倾最大约 16°、离座时约 13°；右下二维模型：前半程托臀部、后半程托大腿，人不往前滑。",
   ask_add=[("左边的动画是 CAD 吗？", "是。机构用 CAD 模型的零件网格，按斜导轨机构的运动学（丝杠行程 → 滑块、连杆、座板位姿）逐帧驱动；人物是扁平小人，姿态来自二维起身模型；前倾读数直接取自同一张行程表。")],
   todo_set=[("CAD 运动动画：本页左图已是 CAD 零件按真实运动学驱动的动画；和老师确认是否还要 SolidWorks 运动算例", "角色 3", "11/3")]),
 "sensing": dict(h3="传感与速度", key="握把是指令：握紧才升、松手就停。测力管两件事：升多快（人用力越多升越快，往回坐速度变 0；卸掉的力要在踏板上出现才提速）和自检（三处力之和 ≈ 体重）。", ask_from="speed"),
 "statemachine": dict(key="三条规则：松手或故障立即停住制动；只有按住“降”才往下动；离座后座板停住接人。“锁定”是传感器自检，不是处理腿软。",
   ask_add=[("松手停和“锁定”有什么区别？", "松手停是人的指令，立刻生效。锁定是传感器自检：抬升中三处力之和和体重差 15–35% 只减速提醒，超过 35% 并持续半秒才锁定（半秒用来排除读数的瞬时跳动），之后只能按住“降”慢慢下。人腿软往回坐不靠锁定，靠速度规则：座板的力一超过上限，速度就是 0，座板停在原处接住人。")]),
 "fall_side": dict(),
 "risk": dict(),
 "concept": dict(h3="附录：一次完整的使用"),
 "cantilever": dict(h3="附录：单侧悬臂怎么扛住"),
 "speed": dict(h3="附录：速度随人自适应"),
 "fall_exit": dict(h3="附录：离开踏板时摔倒"),
 "nextsteps": dict(h3="附录：建模和有限元"),
}
NEW = {"film": dict(t="46 秒短片", st="ok", key="先用 46 秒把问题、产品、用法和安全过一遍，后面每页只讲细节。",
   ask=[("短片里的画面是真实的吗？", "全部由代码生成，没有用 AI 生成画面：装置是 CAD 零件，按机构的真实运动学驱动；人物是扁平小人，姿态来自二维起身模型；画面里的三个数（81 种身体、轨迹误差 ≤ 8 mm、前倾角）都和模型一致。"),
        ("为什么开场放短片？", "15 分钟里先用不到 1 分钟让大家看到问题和产品，后面就不用再口头讲背景，每页直接讲依据。")],
   todo=[("在汇报用的电脑上试播：点一下能否带声音播放；备一份离线 mp4（presentation/video/pulse/bedexit_pulse.mp4）", "全员", "11/3")])}


def aside(sid):
    h_ = open(os.path.join(root, "project/slides", f"{sid}.html")).read()
    return re.search(r"<aside>(.*?)</aside>", h_, re.S).group(1).strip()


def minutes(sid):
    if sid in APPX or sid == "questions": return 0
    if sid == "film": return 0.9
    n = len(re.sub(r"\s", "", aside(sid)))
    return round(n / 230 + (0.1 if sid in ("cover", "agenda", "team") else 0.2), 1)


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


def span(sid):
    i = h.index(f'<article class="srow" id="s-{sid}"'); return i, h.index("</article>", i) + len("</article>")


def new_article(sid, u):
    cls, lab = PILL[u["st"]]
    a = (f'<article class="srow" id="s-{sid}" data-id="{sid}" data-todo="0">\n'
         f' <div class="side"><img src="{thumb(os.path.join(tdir, sid + ".png"))}" alt="第 0 页：{esc(u["t"])}" loading="lazy"><span class="sec">{SEC[sid]}</span></div>\n'
         f' <div class="txt">\n  <div class="meta"><span class="no">第 0 页</span><h3>{esc(u["t"])}</h3><span class="pill {cls}">{lab}</span>'
         f'<span class="merged" hidden>和上一页合并讲</span><span class="time"></span></div>\n'
         f'  <p class="keyl"><b>这一页要让听众记住：</b>{esc(u["key"])}</p>\n'
         f'  <div><p class="lbl">讲稿</p><p class="say">{aside(sid)}</p></div>\n </div>\n</article>')
    return set_body(a, u["ask"], u["todo"])


# 0) Q&A carried over from pages that were merged in (read before anything moves)
carried = {sid: get_ask(h[slice(*span(u["ask_from"]))]) for sid, u in CHG.items() if u.get("ask_from")}
# 1) drop articles whose slide is gone (users merged into problem)
for sid in re.findall(r'<article class="srow" id="s-([a-z_0-9]+)"', h):
    if sid not in order:
        i, j = span(sid); h = h[:i] + h[j:].lstrip("\n")
# 2) every existing slide: new script; thumbnail, title, key, Q&A, to-dos where they changed
for sid in order:
    if sid in NEW: continue
    i, j = span(sid); a = h[i:j]; u = CHG.get(sid, {})
    png = os.path.join(tdir, sid + ".png")
    if os.path.exists(png) and sid not in NO_THUMB:
        a = re.sub(r'<img src="data:image/webp;base64,[^"]+"', f'<img src="{thumb(png)}"', a)
    a = re.sub(r'(<p class="say">).*?(</p>)', lambda m: m.group(1) + aside(sid) + m.group(2), a, flags=re.S)
    if u.get("key"):
        a = re.sub(r'(<p class="keyl"><b>这一页要让听众记住：</b>).*?(</p>)', lambda m: m.group(1) + esc(u["key"]) + m.group(2), a, flags=re.S)
    if u.get("h3"):
        a = re.sub(r"<h3>[^<]*</h3>", f"<h3>{u['h3']}</h3>", a, count=1)
    ask, todo = get_ask(a), get_todo(a)
    for x, y in u.get("ans_text", []): ask = [(q, d.replace(x, y)) for q, d in ask]
    have = {q for q, _ in ask}
    ask += [qa for qa in carried.get(sid, []) if qa[0] not in have] + u.get("ask_add", [])
    if "todo_set" in u: todo = u["todo_set"]
    h = h[:i] + set_body(a, ask, todo) + h[j:]
# 3) new slides, then everything in deck order
for sid in [s for s in order if s in NEW]:
    if f'id="s-{sid}"' in h: i, j = span(sid); h = h[:i] + h[j:].lstrip("\n")
    _, j = span(order[order.index(sid) - 1]); h = h[:j] + new_article(sid, NEW[sid]) + h[j:]
arts = {sid: h[slice(*span(sid))] for sid in order}; first = min(span(s)[0] for s in order)
for sid in order:
    i, j = span(sid); h = h[:i] + h[j:].lstrip("\n")
h = h[:first] + "".join(arts[s] for s in order) + h[first:]
for n, sid in enumerate(order, 1):
    i, j = span(sid); a = h[i:j]
    a = re.sub(r'<span class="no">第 \d+ 页</span>', f'<span class="no">第 {n} 页</span>', a, count=1)
    t = re.search(r"<h3>([^<]*)</h3>", a).group(1)
    a = re.sub(r'alt="第 \d+ 页：[^"]*"', f'alt="第 {n} 页：{t}"', a, count=1)
    a = re.sub(r'<span class="sec">[^<]*</span>', f'<span class="sec">{SEC[sid]}</span>', a, count=1)
    h = h[:i] + a + h[j:]
# 4) JSON blob
i = h.index("const D="); j = h.index(";\n", i); D = json.loads(h[i + len("const D="):j])
slides = []
for n, sid in enumerate(order, 1):
    a = h[slice(*span(sid))]
    slides.append(dict(id=sid, n=n, t=html.unescape(re.search(r"<h3>([^<]*)</h3>", a).group(1)), m=minutes(sid), todo=bool(get_todo(a))))
D["slides"] = slides; D["formal"] = MAIN[:]
D["short"] = ["cover", "film", "problem", "whynot", "mech_select", "mechanism", "motion", "sensing", "statemachine", "verify", "conclusion"]
h = h[:i] + "const D=" + json.dumps(D, ensure_ascii=False) + h[j:]
# 5) builder check-boxes
SL = {s["id"]: s for s in slides}
def opt(sid):
    s = SL[sid]; pill = " <span class='pill p-part'>待补</span>" if s["todo"] else ""
    tt = "附录" if sid in APPX else "讨论" if sid == "questions" else f"{s['m']:.1f}"
    return f'<label class="opt"><input type="checkbox" id="c-{sid}" data-id="{sid}"><span><b>{s["n"]}</b> {esc(s["t"])}{pill}</span><span class="t">{tt}</span></label>'
blk = "".join(f'<p class="grp-h">{g}</p><div class="opts">' + "".join(opt(s) for s in ids) + "</div>" for g, ids in GROUPS)
i = h.index("<h3>页面</h3>") + len("<h3>页面</h3>"); j = h.index('\n  <h3 style="margin-top:14px">合并讲</h3>', i)
h = h[:i] + blk + h[j:]
# 6) script: appendix pages untimed; fresh stored selections
ap = json.dumps(APPX); apq = json.dumps(APPX + ["questions"])
h = re.sub(r'if\(!\[[^\]]*\]\.includes\(id\)\) pages\+\+;', f"if(!{apq}.includes(id)) pages++;", h)
h = re.sub(r'id==="questions"\?"讨论 5–10 分钟":\[[^\]]*\]\.includes\(id\)\?"不计时长"', f'id==="questions"?"讨论 5–10 分钟":{ap}.includes(id)?"不计时长"', h)
h = re.sub(r'const KEY="riser-talk-guide-v\d+";', 'const KEY="riser-talk-guide-v4";', h)
# 7) to-do table, summary boxes, header
rows, n_must = [], 0
for n, sid in enumerate(order, 1):
    a = h[slice(*span(sid))]
    for w, who, when in get_todo(a):
        must = "必须" in when; n_must += must
        rows.append(f'<tr><td><a href="#s-{sid}">{n} {esc(SL[sid]["t"])}</a></td><td>{w}</td><td style="white-space:nowrap">{who}</td><td><span class=\'pill {"p-gap" if must else "p-part"}\'>{when}</span></td></tr>')
i = h.index('<div class="box scroll"><table><thead><tr><th style="width:20%">在哪一页</th>'); i = h.index("<tbody>", i) + len("<tbody>"); j = h.index("</tbody>", i)
h = h[:i] + "".join(rows) + h[j:]
main = [SL[s] for s in MAIN]; tot = sum(s["m"] for s in main); short_tot = sum(SL[s]["m"] for s in D["short"])
h = re.sub(r'<p class="lab">正式汇报完整讲一遍</p><p class="big">约 \d+ 分钟</p><p class="d">.*?</p>',
           f'<p class="lab">正式汇报完整讲一遍</p><p class="big">约 {round(tot)} 分钟</p><p class="d">{len(main)} 页主 slides（含 46 秒短片）合计约 {tot:.1f} 分钟，按每分钟 230 字加指图时间估；附录不计时长。</p>', h, flags=re.S)
h = re.sub(r'<p class="lab">时间紧时</p><p class="big">约 \d+ 分钟</p><p class="d">.*?</p>',
           f'<p class="lab">时间紧时</p><p class="big">约 {round(short_tot)} 分钟</p><p class="d">只讲 {len(D["short"])} 页：封面 → 短片 → 问题 → 方案比较 → 选机构 → 机构 → 运动 → 传感 → 状态机 → 验证 → 结论。</p>', h, flags=re.S)
h = re.sub(r'<p class="lab">待补</p><p class="big">\d+ 项</p><p class="d">.*?</p>',
           f'<p class="lab">待补</p><p class="big">{len(rows)} 项</p><p class="d">其中 {n_must} 项 11/3 必须有：有限元。CAD 运动动画已有（运动演示页），待老师确认是否够。</p>', h, flags=re.S)
h = re.sub(r'<p class="lead"><b>10/27 晚更新（v5\.7）：</b>.*?</p>',
           f'<p class="lead"><b>10/28 更新（v6，15 分钟版）：</b>封面后放 46 秒短片；“问题”和“用户”合成一页，“传感”和“速度”合成一页，“单侧悬臂”并入机构第三步；“一次完整的使用”“单侧悬臂”“速度规则与仿真”“离开踏板时摔倒”“建模和有限元”移到附录；“现有方案”和“方案比较”配了侧视简图，“方案比较”改成以“腿一软时接不接得住”为主线；运动演示和传感页放了短片里的循环片段；讲稿整体压缩约三分之一。<br>配合 {len(order)} 页 slides 使用：{len(MAIN)} 页主讲、{len(APPX)} 页附录，加 1 页只在沟通时用的问题页。</p>', h, flags=re.S)
h = re.sub(r'<button type="button" data-preset="consult">沟通：全部 \d+ 页</button>', f'<button type="button" data-preset="consult">沟通：全部 {len(order)} 页</button>', h)
h = h.replace("缩略图按 10/27 晚的 slides 渲染", "缩略图按 10/28 的 slides 渲染")
open(gout, "w").write(h)
print("written", gout, len(h), "bytes;", len(rows), "to-dos;", f"main {len(main)} pages {tot:.1f} min; short {short_tot:.1f} min")
