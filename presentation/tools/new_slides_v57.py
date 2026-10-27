import os
OUT = os.path.join(os.path.dirname(__file__), "..", "slides")
B = lambda i: "/_blob/" + i
FONT = "font-family:'Noto Sans SC', Arial, sans-serif"
SERIF = "font-family:'Noto Serif SC', Georgia, serif"
INK, BODY, MUTED, ACC, OR = "#18202A", "#3F4A57", "#66707C", "#9A5408", "#B4620A"
CARD = "background:#FFFFFF;border-radius:20px;border:1px solid #E2DED5"

def head(sid, bg, eyebrow, title, size=52, pad="128px 128px 160px", gap=30):
    return (f'<section id="{sid}" data-transition="fade" style="background:{bg};color:{INK};{FONT};padding:{pad};display:flex;flex-direction:column;gap:{gap}px">\n'
            f'<div style="display:flex;flex-direction:column;gap:16px">\n<p style="font-size:26px;color:{ACC};letter-spacing:2px">{eyebrow}</p>\n'
            f'<h2 style="{SERIF};font-size:{size}px;font-weight:700;line-height:1.2">{title}</h2>\n</div>\n')

def foot(t):
    return f'<p style="position:absolute;left:128px;bottom:64px;width:1664px;font-size:24px;color:{MUTED}">{t}</p>\n'

def bars(rows, scale, label_w, unit=""):
    """rows: (label, value, color, bold, note)"""
    h = f'<div style="display:grid;grid-template-columns:{label_w}px 1fr;gap:12px 20px;align-items:center">\n'
    for lab, v, col, bold, note in rows:
        lw = f"color:{INK};font-weight:700" if bold else f"color:{BODY}"
        h += (f'<p style="font-size:24px;line-height:1.3;{lw}">{lab}</p>'
              f'<div style="display:flex;align-items:center;gap:14px"><div style="height:34px;width:{round(v*scale)}px;background:{col};border-radius:0 6px 6px 0"></div>'
              f'<p style="font-size:26px;font-weight:700">{v:.2f}{unit}</p><p style="font-size:22px;color:{MUTED}">{note}</p></div>\n')
    return h + '</div>\n'

def write(sid, html):
    open(os.path.join(OUT, sid + ".html"), "w").write(html)

# ---------- cantilever ----------
li = lambda b, t: f'<li><b>{b}</b>{t}</li>'
write("cantilever", head("cantilever", "#F7F5F0", "3 · 单侧悬臂怎么扛住",
    "座板只挂在床头一侧：偏载的力矩先由铰点 1 的一对轴承接住，再经滑块板交给两根导轨") +
f'''<div style="display:grid;grid-template-columns:920px 1fr;gap:48px;align-items:start">
<img src="{B("16f223eb4ef6384984b93ad2efeb6168")}" alt="剖面图：座板和横梁伸向敞开一侧，右端经节点板、轴、一对圆锥滚子轴承进入焊在滑块板上的轴承座；滑块板背后是导轨滑块和机构箱侧板" style="width:920px;height:578px;object-fit:contain;{CARD}">
<div style="display:flex;flex-direction:column;gap:22px">
<p style="font-size:24px;color:{MUTED}">最坏工况：100 kg × 1.5 倍体重，坐在敞开一侧边上（偏 10 cm），再加 0.3 倍侧推</p>
<ul style="font-size:26px;line-height:1.45;color:{BODY};display:flex;flex-direction:column;gap:12px">
{li("铰点 1 力矩 586 N·m：", "两只 32006 X 圆锥滚子轴承相距 45 mm，把力矩变成一推一拉；当量静载 13.6 kN，静安全系数 3.2")}
{li("轴 Ø30（42CrMo4 调质）：", "208 MPa，许用 433")}
{li("横梁 50×30×4（S355）：", "113 MPa，许用 237")}
{li("4 个 HGH15CA 滑块：", "最重的一个 5.2 kN，静安全系数 2.5")}
{li("座板外缘总下沉约 4.0 mm：", "目标 ≤ 5 mm")}
</ul>
</div>
</div>
''' + foot("全部是手算（静力平衡 + 梁公式），还不是有限元；轴承、滑块额定值取自经销商资料，要用厂家样本核对。编号见附录工程图") +
'''<aside>评审最容易问的一个问题是：座板只挂在一侧，会不会弯、会不会歪？这一页回答它。左边是从床尾方向看过去的剖面。人坐在座板敞开一侧的边上，体重离支撑点很远，在铰点 1 产生约 586 牛米的力矩。我们在铰点 1 放了一对背对背的圆锥滚子轴承，相距 45 毫米，装在一个直径 75 毫米的轴承座里，轴承座焊在滑块板上。力矩在这对轴承上变成一推一拉，最重的一只当量静载约 13.6 千牛，静安全系数 3.2。之前考虑过交叉滚子轴承，但能扛住这个力矩的型号外径 120 毫米，离床垫只剩 0.9 厘米，所以换成了圆锥滚子轴承对。后面的轴、横梁、滑块都按同一组最坏工况算过，有余量；座板外缘总下沉约 4 毫米。这些都是手算，下一步由建模和有限元的同学用 CAD 模型核对。</aside>
</section>
''')

# ---------- fall_side ----------
G1, G2 = "#C3C9D1", "#7D8792"
rows = [
    ("坐在 0.42 m 床沿（对照）", 0.91, G1, False, ""),
    ("起身台：坐着，刚开始", 0.85, OR, False, ""),
    ("起身台：坐着最弱处（髋高 0.73 m）", 0.80, OR, True, ""),
    ("放开座板、只靠双脚站", 0.47, G2, True, "床和起身台一样"),
    ("坐着 + 双手握横杆", 1.27, OR, False, ""),
    ("坐着 + 敞开侧挡板（备选）", 2.40, "#2F7A55", False, ""),
]
drops = [
    ("坐在 0.42 m 床沿", 0.41, G1, False, "落地约 2.8 m/s"),
    ("坐在 0.58 m 床沿", 0.57, G2, False, "约 3.3 m/s"),
    ("起身台上（最高时）", 0.63, OR, True, "约 3.5 m/s"),
]
write("fall_side", head("fall_side", "#FCFBF8", "4 · 防跌倒 ① 侧向摔倒",
    "侧向最弱的时刻是放开座板以后，和从床上站起来一样；起身台多出的风险是从敞开侧摔下时落差更大", size=48, gap=26) +
f'''<div style="display:grid;grid-template-columns:960px 1fr;gap:56px;align-items:start">
<div style="display:flex;flex-direction:column;gap:14px">
<p style="font-size:24px;color:{MUTED}">① 身体被侧向推到多快才会倒（m/s，81 人中位数，越长越稳）</p>
{bars(rows, 180, 440)}
<p style="font-size:22px;color:{MUTED}">粗略参照：轻推一下、小绊一下约 0.1–0.3 m/s</p>
</div>
<div style="display:flex;flex-direction:column;gap:14px">
<p style="font-size:24px;color:{MUTED}">② 往敞开侧摔下去，髋部落差（m，中位数）</p>
{bars(drops, 260, 250)}
<ul style="font-size:24px;line-height:1.45;color:{BODY};display:flex;flex-direction:column;gap:10px;margin-top:8px">
<li><b>床头一侧：</b>机构箱挡住（箱壁离座板 3 cm）</li>
<li><b>横杆往敞开侧加长：</b>不值得，敞开侧反而略差（1.27 → 1.20），还要换更粗的管</li>
<li><b>待定：</b>敞开侧翻下式挡板，或座板测力发现重心侧偏就停（后者没仿真）</li>
</ul>
</div>
</div>
''' + foot("准静态、正面看的模型：不含迈步和肌肉反应。临界速度 = 重心到支撑边的距离 × √(g / 重心高度)。数值用于方案之间比较，不是绝对预测") +
'''<aside>老师可能会问：有没有考虑老人在起身台上往侧面摔？我们做了一个简单的检验。左图的长度是“身体被侧向推到多快才会倒”，越长越稳。坐在起身台上和坐在低床沿差不多，最弱的时候约 0.8 米每秒。真正最弱的时刻是放开座板、只靠两只脚站着，约 0.47 米每秒，这一点从床上站起来也一样，不是起身台带来的。双手握住横杆，坐着时能提到约 1.27。起身台多出来的风险在右图：坐在台上最高处从敞开一侧摔下去，髋部落差约 0.63 米，比低床多 22 厘米，和垫高到 0.58 米的床差不多。床头一侧有机构箱挡着。我们试过把横杆往敞开侧加长，没有用，反而略差。两个备选对策还没定：一是敞开侧加一块可翻下的挡板，模型里能把坐着时的余量提到约 2.4；二是靠座板下的测力单元，发现重心往侧面偏就停，这个还没仿真。这个模型是准静态的，不含迈步，只能用来比较方案。</aside>
</section>
''')

# ---------- fall_exit ----------
def stat(big, small, col=INK):
    return f'<div style="background:#FFFFFF;border:1px solid #E2DED5;border-radius:16px;padding:22px 26px;display:flex;flex-direction:column;gap:6px"><p style="font-size:44px;font-weight:700;color:{col}">{big}</p><p style="font-size:22px;line-height:1.4;color:{BODY}">{small}</p></div>'
write("fall_exit", head("fall_exit", "#F7F5F0", "4 · 防跌倒 ② 离开台子时摔倒",
    "用完离开踏板时摔倒：现有的踏板和横杆测力，原理上能认出来；但只在合成数据上验证过", size=48, gap=26) +
f'''<div style="display:grid;grid-template-columns:860px 1fr;gap:56px;align-items:start">
<div style="display:flex;flex-direction:column;gap:18px">
<p style="font-size:24px;color:{MUTED}">正常迈下去 vs 摔下去，踏板上看到的区别（中位数）</p>
<table style="font-size:24px;color:{BODY};border-collapse:collapse;width:100%">
<tr><th style="text-align:left;padding:10px 12px;border-bottom:2px solid #E2DED5;font-size:22px;color:{MUTED}">信号</th><th style="text-align:left;padding:10px 12px;border-bottom:2px solid #E2DED5;font-size:22px;color:{MUTED}">正常离开</th><th style="text-align:left;padding:10px 12px;border-bottom:2px solid #E2DED5;font-size:22px;color:{MUTED}">摔倒</th></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #E2DED5">脚下的力卸掉用时</td><td style="padding:10px 12px;border-bottom:1px solid #E2DED5">0.54 s</td><td style="padding:10px 12px;border-bottom:1px solid #E2DED5;font-weight:700;color:{INK}">0.37 s（更快）</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #E2DED5">压力中心离脚中心多远（0 中心，1 脚边）</td><td style="padding:10px 12px;border-bottom:1px solid #E2DED5">0.24</td><td style="padding:10px 12px;border-bottom:1px solid #E2DED5;font-weight:700;color:{INK}">0.70（压在脚边）</td></tr>
<tr><td style="padding:10px 12px;border-bottom:1px solid #E2DED5">膝盖、髋砸到踏板的冲击</td><td style="padding:10px 12px;border-bottom:1px solid #E2DED5">无</td><td style="padding:10px 12px;border-bottom:1px solid #E2DED5;font-weight:700;color:{INK}">腿软时 1.5–3 倍体重</td></tr>
</table>
<p style="font-size:24px;line-height:1.5;color:{BODY}">单看任何一个信号都分不清（区分度最好的也只有 0.79；0.5 等于瞎猜，1.0 完全分开）；几个合起来才行</p>
<p style="font-size:24px;line-height:1.5;color:{ACC}"><b>认出来以后只能报警</b>（开灯、语音、呼叫家属），挡不住这一次摔倒</p>
</div>
<div style="display:flex;flex-direction:column;gap:16px">
<p style="font-size:24px;color:{MUTED}">每 100 次正常离开误报 5 次时，摔倒检出率</p>
{stat("98%", "基本情况（逻辑回归，7 个特征）")}
{stat("80%", "最坏情况：压力中心噪声加倍 + 正常人也快步、踩脚边 + 慢慢倒", OR)}
{stat("75%", "三条阈值规则（误报 3.9 次 / 100），不用训练")}
<p style="font-size:22px;line-height:1.45;color:{MUTED}">双脚都离开踏板后再摔：这些传感器看不到，要靠雷达或可穿戴，不在本项目范围</p>
</div>
</div>
''' + foot("合成数据：正常离开和摔倒各约 500 次，摔倒过程用倒立摆模型生成，所以结果偏乐观。下一步：志愿者在软垫上做摔倒动作 + 老人正常离开，检出 ≥ 80%、误报 ≤ 5 次/100 才继续") +
'''<aside>第二个防跌倒问题：用完起身台、离开踏板的时候摔倒，我们能不能知道？我们没有加新的传感器，只用设计里已有的踏板四个测力单元和横杆测力。正常迈下去，脚下的力是慢慢转移走的，压力中心停在支撑脚的中间；摔倒时，力卸得更快，压力中心先跑到脚的边上，腿软的话膝盖还会砸到踏板。单看任何一个信号都分不清，几个合起来，在我们生成的数据上，每一百次正常离开误报五次时能认出约 98% 的摔倒；把条件设得很不利，也有约 80%。要强调两点。第一，这些数据是我们自己用模型生成的，结果偏乐观，必须用真人数据验证：志愿者在软垫上做摔倒动作，再录老人的正常离开，检出率到 80%、误报不超过每百次五次才继续。第二，认出来以后只能报警、开灯、呼叫家属，挡不住这一次摔倒。人已经走下踏板以后再摔，这些传感器看不到，不在我们的范围。</aside>
</section>
''')

# ---------- nextsteps (FEA) ----------
def fcard(src, alt, cap, sub):
    return (f'<div style="{CARD};padding:16px;display:grid;grid-template-columns:380px 1fr;gap:20px;align-items:center">'
            f'<img src="{src}" alt="{alt}" style="width:380px;height:270px;object-fit:contain">'
            f'<div style="display:flex;flex-direction:column;gap:10px"><p style="font-size:28px;font-weight:700;color:{INK}">{cap}</p><p style="font-size:23px;line-height:1.45;color:{BODY}">{sub}</p></div></div>')
write("nextsteps", head("nextsteps", "#FCFBF8", "5 · 下一步",
    "建模和有限元：先算这四个部位（手算找出的薄弱处，还不是有限元结果）", size=48, gap=28) +
'<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">\n' +
fcard(B("8fca01ced7de315e720e4cedc6354b3c"), "滑块板和轴承座焊接件受力示意：铰点 1 的力和力矩、焊缝位置、80° 窗口", "① 滑块板 + 轴承座焊接件",
      "力矩 586 N·m 从轴承座进滑块板；看轴承座根部焊缝和 80° 窗口两侧") + "\n" +
fcard(B("52a3609e185b1006682b78f3d55bc7e6"), "横梁受力示意：外缘 1471 N 向下，根部焊在节点板上", "② 座板横梁 + 节点板焊缝",
      "手算 113 MPa（许用 237）；看根部焊缝和外缘下沉（手算 1.6 mm）") + "\n" +
fcard(B("b1435ad16eb52cdd58c7120ba4cb1026"), "机构箱侧板示意：滑块固定点、竖槽、底边固定", "③ 机构箱侧板（开竖槽处）",
      "滑块力传到侧板；竖槽削弱了截面，看槽端应力和箱体扭转") + "\n" +
fcard(B("d4f5478be8499f19095922d7d069f369"), "扶手立柱示意：横杆端 1668 N 向下，根部弯矩 1.53 kN·m", "④ 扶手立柱 + 底座",
      "横杆端 1668 N，根部弯矩 1.53 kN·m；看立柱根部焊缝和底座变形") + "\n</div>\n" +
foot("每个部位的载荷向量、边界条件和判据都写在机构网页的“有限元重点”一节，CAD 零件和 STEP 文件也在那里下载") +
'''<aside>下一步交给建模和有限元的同学。我们手算找出四个最该先算的部位，注意这些还不是有限元结果。第一，滑块板和轴承座的焊接件：座板的力矩从这里进滑块板，要看轴承座根部的焊缝和中间那个 80 度窗口两侧。第二，座板横梁和节点板之间的焊缝，手算 113 兆帕，看焊缝和外缘下沉。第三，机构箱侧板：中间开了让支架伸出来的竖槽，要看槽两端的应力和整个箱子的扭转。第四，扶手立柱和底座：人整个挂在横杆上时根部弯矩约 1.5 千牛米。每个部位的载荷、边界条件、判据都已经写在机构网页上，零件模型和 STEP 文件也能直接下载。</aside>
</section>
''')

# ---------- drawings (appendix) ----------
def thumb(src, alt, cap):
    return (f'<div style="display:flex;flex-direction:column;gap:8px"><img src="{src}" alt="{alt}" style="width:360px;height:255px;object-fit:contain;{CARD}">'
            f'<p style="font-size:22px;color:{BODY}">{cap}</p></div>')
write("drawings", head("drawings", "#F7F5F0", "附录 · 工程图", "CAD 模型（40 个零件）的总装图和关键零件图", size=52, pad="128px", gap=32) +
f'''<div style="display:grid;grid-template-columns:900px 1fr;gap:40px;align-items:start">
<div style="display:flex;flex-direction:column;gap:8px"><img src="{B("5d4177b1e4f65c71d8567777f1872c28")}" alt="总装图：主视、俯视、左视和轴测图，座板与床齐平，右侧明细表" style="width:900px;height:636px;object-fit:contain;{CARD}"><p style="font-size:22px;color:{BODY}">总装图（座板与床齐平）</p></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
{thumb(B("ae7045eb7ad5fb03b9533b91bad4b6b1"), "零件图 C1 滑块板", "C1 滑块板（S355，20 mm）")}
{thumb(B("9ea13000597290ed1f658e3c9f6e6a6c"), "零件图 J3 轴承座", "J3 轴承座（Ø75，80° 窗口）")}
{thumb(B("dc0e16a2bd566b78bb281eaa48a30a53"), "零件图 S7 横梁", "S7 横梁（50×30×4）")}
{thumb(B("b642adee077d4fbd21f5c65fdff1f462"), "零件图 J1 铰点 1 轴", "J1 铰点 1 轴（Ø30）")}
</div>
</div>
<aside>附录：这是 CAD 模型的总装图和四张关键零件图。完整的 23 张零件图、STEP 文件和三维模型都在机构网页上，可以直接下载。</aside>
</section>
''')

# ---------- parts (appendix) ----------
write("parts", head("parts", "#FCFBF8", "附录 · 零件编号", "零件一览：侧视和俯视（编号和工程图一一对应）", size=52, pad="128px", gap=32) +
f'''<div style="display:grid;grid-template-columns:1fr 1fr;gap:40px">
<img src="{B("38a73515d77cdc78c51a713b6b0aa24f")}" alt="侧视图，零件编号气泡" style="width:812px;height:660px;object-fit:contain;{CARD}">
<img src="{B("50cef8e46983e79d3826540b9a4ea3cc")}" alt="俯视图，零件编号气泡" style="width:812px;height:660px;object-fit:contain;{CARD}">
</div>
<aside>附录：零件编号。S 开头是座板上的零件，J 是铰点，C 是滑块板，L 是倾角连杆，D 是驱动，H 是机构箱，B 是底座。被问到某个零件时用这一页定位。</aside>
</section>
''')
print("ok")
