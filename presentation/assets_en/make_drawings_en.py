"""English versions of the engineering drawings on the 'drawings' appendix slide.

  dw_assembly_flush_en.png, dw_C1_en.png, dw_J3_en.png, dw_S7_en.png, dw_J1_en.png   (2520 x 1782, as in assets_v57)

Usage: python3 presentation/assets_en/make_drawings_en.py      (writes into presentation/assets_en/)

Reads the existing SVGs in cad/out/drawings/ (read-only; cad/model/build_cad.py is NOT re-run, it would rewrite cad/out/),
translates every <text> and <title> through ZH2EN (terms per presentation/slides_en/STYLE.md), switches the sheet font to
Inter, and rasterises each sheet with headless Chromium (node + playwright). Parts-list rows "<name> ×N" are translated
by name. A list value is drawn as several lines (tspans). Fails if any CJK character is left.
"""
import json, os, re, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "cad", "out", "drawings")
SHEETS = {"assembly_flush": "dw_assembly_flush", "C1": "dw_C1", "J3": "dw_J3", "S7": "dw_S7", "J1": "dw_J1"}
W, H = 2520, 1782
CJK = re.compile(r"[　-〿㐀-鿿＀-￯]")
REF = "Reference drawing: dimensions from the calc model; tolerances, welds, finish set by Role 3"

PARTS = {  # parts-list names (assembly)
    "后区泡棉": "Rear foam", "前区泡棉": "Front foam", "底板": "Seat board", "后区垫条": "Rear spacer strip",
    "称重单元": "Load cell", "称重支臂": "Load-cell arm", "横梁": "Cross beam", "节点板": "Knuckle plate",
    "铰点 1 轴": "Pivot 1 shaft", "锁紧螺母 KM6": "Lock nut KM6", "铰点 2 摆臂": "Pivot 2 arm", "滑块板": "Carriage plate",
    "轴承座筒": "Bearing housing tube", "圆锥滚子轴承": "Tapered roller bearing", "滑块": "Carriage", "螺母座": "Nut bracket",
    "丝杠螺母": "Ball-screw nut", "连杆管": "Link tube", "杆端关节轴承": "Rod-end bearing", "B 支座": "Pivot B bracket",
    "导轨": "Linear guide", "滚珠丝杠": "Ball screw", "丝杠固定支撑": "Screw fixed support", "同步带轮": "Timing pulley",
    "电机": "Motor", "失电制动器": "Power-off brake", "离心限速器": "Centrifugal speed limiter",
    "侧板（导轨安装板）": "Side plate (guide mount)", "内壁": "Inner wall", "周边围板": "Surround panel", "外罩": "Outer cover",
    "驱动罩": "Drive cover", "底座框": "Base frame", "调平脚": "Levelling foot", "踏板": "Footplate", "防滑胶垫": "Anti-slip mat",
    "扶手立柱": "Grab-bar post", "横杆": "Grab bar", "控制器 + 电池": "Controller + battery",
}

ZH2EN = {
    # titles
    "总装 flush": "Assembly, flush position", "C1 滑块板": "C1 carriage plate", "J3 轴承座筒": "J3 bearing housing tube",
    "S7 横梁": "S7 cross beam", "J1 铰点 1 轴": "J1 pivot 1 shaft",
    # views
    "主视图": "Front view", "俯视图": "Top view", "左视图": "Left view",
    "轴测图（不按比例）": "Isometric (not to scale)", "轴测图（比例同主视图）": "Isometric (same scale as front view)",
    # title block
    "零件名称": "Part name", "编号": "Code", "材料": "Material", "数量": "Qty", "比例": "Scale", "单位": "Unit",
    "投影": "Projection", "第一角投影": "First-angle projection", "项目": "Project", "ME5412 床边起身台 v5.7": "ME5412 Bed-Exit Seat v5.7",
    "见零件表": "See parts list", "总装（齐平位，丝杠行程 0）": "Assembly (flush position, screw stroke 0)",
    "参考图：尺寸来自计算模型；公差、焊缝、表面处理由角色 3 定。坐标：x 离床、y 指向床头、z 向上，原点在床长": REF + ".",
    "边正下方地面": "Axes: x away from bed, y toward bed head, z up; origin on the floor below the bed's long edge.",
    "参考图：尺寸来自计算模型；公差、焊缝、表面处理由角色 3 定": REF,
    # tables
    "零件表": "Parts list", "关键尺寸": "Key dimensions", "尺寸": "Feature", "数值": "Value",
    # C1
    "滑块板": "Carriage plate", "S355 钢板 20 mm": "S355 steel plate 20 mm",
    "外形（x × y × z）": "Envelope (x × y × z)", "厚": "Thickness", "20 mm（y 288 … 308）": "20 mm (y 288 … 308)",
    "外形": "Outline", "沿导轨 −40 … 190，垂直导轨 −25 … 175（以铰": "Along guide −40 … 190, across guide −25 … 175",
    "点 1 为原点）": "(origin at pivot 1)",
    "铰点 1 角": "Pivot 1 corner", "R42（绕铰点 1）": "R42 (about pivot 1)",
    "轴承 A 孔": "Bearing A bore", "Ø55 H7（和 J3 焊后同镗）": "Ø55 H7 (bored with J3 after welding)",
    "滑块安装孔": "Carriage mounting holes", "4 × 4 × Ø4.5，26 × 26，块心 (0,0) (150,0) ": "4 × 4 × Ø4.5, 26 × 26, centres (0,0) (150,0) ",
    "螺母座孔": "Nut bracket holes", "4 × Ø6.6，40 × 40，心 (75, 75)": "4 × Ø6.6, 40 × 40, centre (75, 75)",
    "螺母法兰让位槽": "Nut-flange clearance slot", "背面 11 深": "Back face, 11 deep",
    "和 J3 焊成一个焊件，两个轴承孔焊后一起精加工；背面在螺母法兰处开 11 深让位槽。":
        ["One weldment with J3; both bearing bores finish-machined together after welding;",
         "11-deep clearance slot in the back face at the nut flange."],
    # J3
    "轴承座筒": "Bearing housing tube", "S355 无缝钢管 Ø75 / 内孔 Ø55": "S355 seamless tube Ø75 / bore Ø55",
    "外径 / 内孔": "OD / bore", "长": "Length", "y 229 … 288（再插进 C1 的孔到 308）": "y 229 … 288 (into the C1 bore to 308)",
    "窗口": "Window", "80°，y 247 … 273，中心在 -169.7°（滑块座坐": "80°, y 247 … 273, centred at −169.7°",
    "标，从 +X 转向 +Z）": "(carriage frame, from +X toward +Z)",
    "摆臂转角范围": "Arm swing range", "焊缝": "Weld", "和 C1 外圈角焊，焊后同镗两孔": "Fillet weld to C1; bores bored together",
    "穿过内壁竖槽；窗口让铰点 2 摆臂 J4 穿出。": "Passes through the inner-wall slot; the window lets the pivot 2 arm J4 out.",
    # S7
    "横梁": "Cross beam", "S355 矩形管 50 × 30 × 4": "S355 rectangular tube 50 × 30 × 4",
    "截面": "Section", "50（x_s）× 30（z_s）× 4": "50 (x_s) × 30 (z_s) × 4",
    "长（y）": "Length (y)", "409 mm（−205 … 204）": "409 mm (−205 … 204)",
    "端头": "Root end", "y = 204 处和 S8 节点板角焊（四周）": "Fillet weld all round to S8 at y = 204",
    "自由端": "Free end", "y = −205 焊端板封口（可选）": "End plate welded at y = −205 (optional)",
    "座板的单侧悬臂主梁；高 30 被小腿间隙卡住": "Main beam of the one-sided cantilever seat; height 30 set by calf clearance",
    # J1
    "铰点 1 轴": "Pivot 1 shaft", "42CrMo4 调质": "42CrMo4, quenched and tempered",
    "法兰": "Flange", "Ø75 × 10（y 216 … 226），6 × Ø11 PCD 55": "Ø75 × 10 (y 216 … 226), 6 × Ø11 PCD 55",
    "轴径": "Shaft diameter", "Ø30 k5（轴承位）": "Ø30 k5 (bearing seats)", "轴长": "Shaft length", "76 mm（y 226 … 302）": "76 mm (y 226 … 302)",
    "螺纹": "Thread", "M30 × 1.5（y 290 … 302），装 KM6": "M30 × 1.5 (y 290 … 302), KM6 nut",
    "轴承位": "Bearing seats", "y 229 … 246、274 … 291（间距 45）": "y 229 … 246, 274 … 291 (spacing 45)",
    "摆臂位": "Arm seat", "y 249 … 271，Ø30 胀紧套": "y 249 … 271, Ø30 locking bush",
    "座板绕它转（转动副 R1）；法兰用 6 颗 M10-10.9 接 S8": "The seat turns about it (revolute joint R1); flange bolts to S8 with 6 × M10-10.9",
}


def tr(s):
    if s in ZH2EN: return ZH2EN[s]
    m = re.fullmatch(r"(.*?) (×\d+)", s)
    if m and m.group(1) in PARTS: return f"{PARTS[m.group(1)]} {m.group(2)}"
    if CJK.search(s): raise SystemExit(f"no translation for {s!r}")
    return s


def translate(svg):
    unesc = lambda s: s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def text(m):
        attrs, en = m.group(1), tr(unesc(m.group(2)))
        if isinstance(en, list):
            x = re.search(r' x="([-\d.]+)"', attrs).group(1); fs = float(re.search(r'font-size="([\d.]+)"', attrs).group(1))
            return f"<text{attrs}>" + "".join(f'<tspan x="{x}" dy="{0 if i == 0 else round(1.35 * fs, 2)}">{esc(t)}</tspan>' for i, t in enumerate(en)) + "</text>"
        return f"<text{attrs}>{esc(en)}</text>"
    svg = re.sub(r"<text([^>]*)>([^<]*)</text>", text, svg)
    svg = re.sub(r"<title>([^<]*)</title>", lambda m: f"<title>{esc(tr(unesc(m.group(1))))}</title>", svg)
    svg = re.sub(r"font-family='[^']*'", "font-family='\"Inter\",\"DejaVu Sans\",Arial,sans-serif'", svg, count=1)
    svg = re.sub(r'width="420mm" height="297mm"', f'width="{W}" height="{H}"', svg, count=1)
    if CJK.search(svg): raise SystemExit("CJK left: " + ", ".join(sorted(set(CJK.findall(svg)))))
    return svg


RENDER_JS = r"""
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')); const b = await chromium.launch();
  for (const j of jobs) {
    const p = await b.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
    await p.goto('file://' + j.html); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(200);
    await p.screenshot({ path: j.png }); await p.close(); console.log('wrote', j.png);
  }
  await b.close();
})();
"""


def main():
    tmp = tempfile.mkdtemp(prefix="drawings_en_"); jobs = []
    try:
        for src, name in SHEETS.items():
            svg = translate(open(os.path.join(SRC, src + ".svg"), encoding="utf-8").read())
            hp = os.path.join(tmp, name + ".html")
            open(hp, "w", encoding="utf-8").write(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}} svg{{display:block}}</style>{svg}')
            jobs.append(dict(html=hp, png=os.path.join(HERE, name + "_en.png"), w=W, h=H))
        jp = os.path.join(tmp, "jobs.json"); json.dump(jobs, open(jp, "w"))
        js = os.path.join(tmp, "render.js"); open(js, "w").write(RENDER_JS)
        subprocess.run(["node", js, jp], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
