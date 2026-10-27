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

# st: ok / part / gap; todo: (what, who, when)
UPD = {
 "cover": dict(key="一句话说清做什么：平时和床一样低；起身时座板跟着大腿前移、上升、前倾；速度跟着人，松手就停。", ask=[], todo=[("填组员姓名", "全员", "11/3")], st="part"),
 "users": dict(key="用户已经和老师确认；六条要求在最后的验证表里逐条检查，第 1 条加了“座板跟着大腿走、人不往前滑”。",
   ask=[("偏瘫的人能用吗？", "开关一只手就能用，力分布的阈值按个人基线设，所以不排除；前提是能坐稳。")], todo=[], st="ok"),
 "concept": dict(key="坐上 → 握住身前横杆 → 座板跟着大腿走 → 站稳，座板一直接得住人；机构都在床头一侧，床尾敞开。",
   ask=[("往前挪 25–30 cm，老人做得到吗？", "这是目前最大的不确定。我们用姿态几何检查能不能放下，是否可行列入局限和后续实测。"),
        ("为什么扶手不跟着座板升？", f"跟着升需要再加一套机构；固定的 L 形扶手最简单。横杆在人正前方 x {cm(B['x'])} cm、高 {B['z']:.2f} m，81 位模拟用户坐着都够得着，从坐到站不用换手。")], todo=[], st="ok"),
 "whynot": dict(key="决定省力的是起身时的座高；床只有一个高度，起身台把“坐着的高度”和“起身的高度”分开，比抬高床再省 13–20%。座板还要跟着大腿走，否则人会往前滑。",
   ask=[("省 13–20% 值得做一台电动设备吗？", "除了省力，床可以整夜保持低位，站起后扶手一直在手边，还有安全控制；对最弱的那部分人，这点差别可能决定能不能站起来（这是推断，没有验证）。"),
        ("为什么不直接把床垫高？", "可以垫，而且这是效果最好的现有做法（0.29）。但床高同时决定坐着时脚能不能踩实，居家建议不超过约 0.58 m；起身台平时和床齐平，只在起身时升高，所以能再省 13–20%。"),
        ("模型可信吗？", "只用来比较方向和量级：准静态、只看离座瞬间，没有动态过程和实测，已写进局限页。")], todo=[], st="ok"),
 "mechanism": dict(key=f"座板不是竖直升，而是跟着大腿走：竖直升降 81 人里只有 {VS['n_ok']} 人不前滑、坐回接得住，曲线座板 {nok}/81。一个电机：斜导轨 + 倾角连杆。",
   ask=[("为什么不用两根升降柱竖直升？", f"髋往前走得早的人，竖直座板跟不上，会往前滑出座面，坐回时还会坐空；81 位模拟用户里竖直升降只有 {VS['n_ok']} 人两项都合格。"),
        ("一个自由度怎么同时管位置和前倾？", f"座板上两个铰点：一个装在沿斜导轨走的滑块上，一个用连杆拉到底座。两点一定，位置和前倾就都定了；轨迹和要的曲线最多差 {M['centre_err_mm']:.0f} mm。"),
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
