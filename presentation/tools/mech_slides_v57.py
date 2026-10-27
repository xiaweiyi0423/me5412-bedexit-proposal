"""Mechanism-design slides (deck v5.7b): ① where the seat must go, ② five candidate mechanisms, ③ the rail + tilt link and
how it was sized (rewrites mechanism.html). Numbers from model/calc_v13/seat_1dof/{page,fourbar_oneside,parts}.json.
Usage: python3 mech_slides_v57.py <slides_dir>
"""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
J = lambda f: json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof", f)))
P = J("page.json"); OS = J("fourbar_oneside.json"); PJ = J("parts.json")
M = P["mech"]; PL = P["placements"]; VS = P["check"]["vertical_summary"]; OSS = OS["summary"]
OUT = sys.argv[1]
FONT = "font-family:'Noto Sans SC', Arial, sans-serif"; SERIF = "font-family:'Noto Serif SC', Georgia, serif"
INK, BODY, MUTED, ACC, OR = "#18202A", "#3F4A57", "#66707C", "#9A5408", "#B4620A"
CARD = "background:#FFFFFF;border-radius:20px;border:1px solid #E2DED5"
B = lambda i: "/_blob/" + i

def head(sid, bg, eyebrow, title, size=48, gap=28):
    return (f'<section id="{sid}" data-transition="fade" style="background:{bg};color:{INK};{FONT};padding:128px 128px 160px;display:flex;flex-direction:column;gap:{gap}px">\n'
            f'<div style="display:flex;flex-direction:column;gap:14px">\n<p style="font-size:26px;color:{ACC};letter-spacing:2px">{eyebrow}</p>\n'
            f'<h2 style="{SERIF};font-size:{size}px;font-weight:700;line-height:1.2">{title}</h2>\n</div>\n')
foot = lambda t: f'<p style="position:absolute;left:128px;bottom:64px;width:1664px;font-size:24px;color:{MUTED}">{t}</p>\n'
li = lambda b, t: f'<li><b>{b}</b>{t}</li>'
def write(sid, h): open(os.path.join(OUT, sid + ".html"), "w").write(h)

nok = M["summary"]["n_ok"]; dx, dz = M["travel"]["dx"] * 100, M["travel"]["dz"] * 100

# ① path
write("mech_path", head("mech_path", "#FCFBF8", "3 · 机构设计 ① 座板该怎么走", "先定路径：从 81 个人的起身动作里，定出座板要走的一条曲线") +
f'''<div style="display:grid;grid-template-columns:900px 1fr;gap:48px;align-items:start">
<img src="{B("ab9462e6dc02a78eb42c7940f6c756ac")}" alt="侧视图：81 条灰线是每个人理想的座板中心路径，从床沿起点往前上方散开；橙色是选定的设计曲线，靠在最前沿；黑色虚线是斜导轨机构实际走的，几乎重合；红色竖直虚线是竖直升降" style="width:900px;height:619px;object-fit:contain;{CARD}">
<ul style="font-size:25px;line-height:1.5;color:{BODY};display:flex;flex-direction:column;gap:16px">
{li("为什么不能竖直：", f"起身时髋部先往前、再往上。竖直的座板跟不上大腿，人往前滑出座面，坐回时会坐空（{VS['n_ok']}/81 合格）")}
{li("每个人的理想路径：", "座板一直托在臀腿交界，跟着大腿走；前倾 ≤ 15°，再陡往回坐会顺坡滑")}
{li("一个电机只能走一条路：", f"从髋最早前移的 18 人里挑，选中的这条跟得上走得最靠前的人；走得靠后的人，座板只是托在大腿更靠前处。检查 {nok}/81 合格")}
{li("其他约束：", "起点和床面齐平；刚性件离床 ≥ 1.5 cm；床尾一侧敞开，回床时腿能转过去")}
</ul>
</div>
''' + foot("81 人 = 3 种身高 × 3 种臀厚 × 3 种起身习惯 × 3 种脚位；二维准静态。合格 = 前滑 ≤ 2 cm 且往回坐接得住。设计曲线到 0.61 m，之上沿导轨延长到 0.69 m（补坐垫压缩）") +
f'''<aside>机构设计我们分三步讲。第一步，先不管用什么机构，先定座板应该怎么走。我们用 81 位模拟用户，三种身高、三种胖瘦、三种起身习惯、三种脚的位置，算出每个人起身时髋部和大腿怎么动。图上每条灰线是一个人理想的座板路径：座板一直托在臀部和大腿交界的地方，跟着大腿走，前倾不超过 15 度，因为再陡，人往回坐时会顺着坡滑下来。可以看到，所有人的路径都是先往前、再往上，这就是为什么不能竖直升：竖直的座板，就是红色这条虚线，跟不上大腿，人会往前滑出座面，81 人里只有 {VS['n_ok']} 人合格。但我们只有一个电机，座板只能走一条路。我们在髋部最早往前走的那些人里挑了一条，就是橙色这条：它跟得上走得最靠前的人；对走得靠后的人，座板只是托在大腿更靠前的位置，不会让人往前滑。用 81 个人逐个检查，{nok} 人合格。另外几个约束是：起点和床面齐平，刚性零件离床至少 1.5 厘米，床尾一侧要敞开，回床时腿能转过去。</aside>
</section>
''')

# ② candidates
mid, sides = PL["v5-mid"], PL["v5-sides"]; fb_bear = OS["cantilever"]["载荷偏向敞开一侧 10 cm"]["bearing_ground_N_b80"] / 1000
td = lambda t, b=False: f'<p style="font-size:22px;line-height:1.35;text-align:center;color:{INK if b else BODY};{"font-weight:700;" if b else ""}">{t}</p>'
lab = lambda t: f'<p style="font-size:21px;line-height:1.35;color:{MUTED}">{t}</p>'
rows = [("81 人合格", [str(VS["n_ok"]), f'{mid["n_ok"]}*', f'{sides["n_ok"]}*', str(OSS["n_ok"]), str(nok)]),
        ("偏离设计曲线", ["不追曲线", f'{mid["centre_err_mm"]:.0f} mm', f'{sides["centre_err_mm"]:.0f} mm', f'{OS["mech"]["centre_err_mm"]:.0f} mm', f'{M["centre_err_mm"]:.0f} mm']),
        ("驱动静载", ["—", f'{mid["force_kN"]} kN', f'{sides["force_kN"]} kN', f'{OS["act"]["F_hold100_N"] / 1000:.1f} kN', f'{M["F_hold100_N"] / 1000:.1f} kN']),
        ("问题", ["跟不上大腿，往前滑", "连杆和小腿在同一平面，会碰", "两侧都挡住，回床腿转不过去；要两个同步推杆",
                 f"偏载只靠相距 8 cm 的铰点扛，地面轴承约 {fb_bear:.0f} kN；站直时连杆碰小腿", f"代价：机构箱高（箱顶 {PJ['housing']['top_z']:.2f} m）"])]
cells = ""
for name, vals in rows:
    cells += f'<div style="border-top:1px solid #E2DED5;padding-top:8px">{lab(name)}</div>' + "".join(
        f'<div style="border-top:1px solid #E2DED5;padding-top:8px;{"background:#FBF3E8;" if i == 4 else ""}padding-left:10px;padding-right:10px">{td(v, i == 4)}</div>' for i, v in enumerate(vals))
write("mech_select", head("mech_select", "#F7F5F0", "3 · 机构设计 ② 选机构", "同一组约束、同样 81 个人，比了五种机构") +
f'''<div style="display:grid;grid-template-columns:170px repeat(5, 1fr);column-gap:0;row-gap:8px">
<div></div><img src="{B("216146ef62fbb2f90f01720a9ea2bdc8")}" alt="五种机构侧视简图：竖直升降、座板正下方的四连杆、两腿外侧的四连杆、只在床头一侧的四连杆、斜导轨加倾角连杆；实色为起点，浅色为最高处，虚线为座板中心轨迹" style="grid-column:2 / span 5;width:1494px;height:387px;object-fit:contain;background:#FFFFFF;border-radius:16px">
{cells}
</div>
''' + foot("静载按 100 kg × 1.5 倍体重。* 这两种在起身路径修正（算全程）之前已因别的原因淘汰，没有重算。偏离 = 座板中心离设计曲线的最大距离") +
f'''<aside>第二步，选机构。路径定了以后，我们在同一组约束下、用同样 81 个人比了五种机构。竖直升降不追这条曲线，跟不上大腿，只有 {VS['n_ok']} 人合格。四连杆我们试了三种放法：放在座板正下方中间，连杆和小腿在同一个平面里，会碰腿，轨迹也差得多；两腿外侧各放一套，轨迹不错，但两边都被挡住，回床时腿转不过去，还要两个同步的推杆；只放在床头一侧，箱子能小一半，但座板的偏载只能靠座板上两个相距 8 厘米的铰点来扛，地面铰点的轴承要承受约 {fb_bear:.0f} 千牛，站直时连杆还会碰到小腿。最后是我们采用的斜导轨加倾角连杆：轨迹只差 {M['centre_err_mm']:.0f} 毫米，驱动力最小，床尾一侧敞开。它的代价是机构箱比较高，因为导轨本身要装下整个行程。</aside>
</section>
''')

# ③ result (rewrites mechanism.html)
write("mechanism", head("mechanism", "#FCFBF8", "3 · 机构设计 ③ 斜导轨 + 倾角连杆", "座板上找两个点：一个走直线、一个走圆弧") +
f'''<div style="display:grid;grid-template-columns:720px 1fr;gap:48px;align-items:start">
<img src="{B("e59fbf3e2ff1bdb7e7f40169a8c941cb")}" alt="侧视图：座板在起点、中间、最高三个位置；铰点 1 的轨迹是一条直线，沿斜导轨；铰点 2 的轨迹是绕底座 B 的圆弧，由连杆约束；座板中心贴住设计曲线" style="width:720px;height:625px;object-fit:contain;{CARD}">
<div style="display:flex;flex-direction:column;gap:22px">
<ul style="font-size:24px;line-height:1.5;color:{BODY};display:flex;flex-direction:column;gap:12px">
{li("思路：", "让座板沿设计曲线走，看座板上每个点走出的轨迹。轨迹接近直线的点装在滑块上走导轨，接近圆弧的点用连杆拉到圆心 B")}
{li("尺寸怎么定：", "只搜座板上两个铰点的位置（4 个数），导轨和 B 由拟合得出；约束：前倾 ≤ 16°、到顶 0.69 m 时前倾 0–8°、两铰点相距 ≥ 80 mm、离床 ≥ 1.5 cm")}
{li("结果：", f"导轨与竖直 {M['rail_angle_deg']:.0f}°、丝杠行程 {M['stroke'] * 1000:.0f} mm、连杆 {M['link'] * 1000:.0f} mm；座板中心最多差 {M['centre_err_mm']:.0f} mm、{M['tilt_err_deg']}°；前移 {dx:.1f} cm、上升 {dz:.1f} cm")}
{li("一个自由度：", "3 个转动副 + 1 个移动副；电机 → 皮带 → 滚珠丝杠 → 滑块")}
</ul>
<img src="{B("cce29011ddde24c7ec79959b8e6e2495")}" alt="CAD 模型：床头一侧半透明的机构箱，内有双导轨、丝杠和连杆，座板在行程中间" style="width:520px;height:325px;object-fit:contain;{CARD}">
</div>
</div>
''' + foot("右下是 CAD 模型（40 个零件，座板在行程中间）；搜索用差分进化，代价 = 座板中心和前倾偏离设计曲线的最大值") +
f'''<aside>第三步，定尺寸。思路很简单：让座板沿着设计曲线走一遍，看座板上每一个点会走出什么轨迹。有的点走出来接近一条直线，就把它装在滑块上，让它沿直导轨走，这就是铰点 1，蓝色这条；有的点走出来接近一段圆弧，就用一根连杆把它拉到圆心，这就是铰点 2，绿色这条，圆心就是底座上的 B 点。所以我们只需要搜索座板上两个铰点的位置，一共 4 个数；导轨的位置和角度、B 点和连杆长度都由拟合直接得出。约束是：前倾全程不超过 16 度，到顶 0.69 米时前倾在 0 到 8 度之间，两个铰点相距至少 8 厘米，所有刚性零件离床至少 1.5 厘米。结果是导轨和竖直方向成 {M['rail_angle_deg']:.0f} 度，丝杠行程 {M['stroke'] * 1000:.0f} 毫米，连杆 {M['link'] * 1000:.0f} 毫米，座板中心和设计曲线最多差 {M['centre_err_mm']:.0f} 毫米。整个机构是三个转动副加一个移动副，一个自由度，一个电机经皮带带动滚珠丝杠推滑块。右下角是按这些尺寸建的 CAD 模型。</aside>
</section>
''')
print("written mech_path, mech_select, mechanism")
