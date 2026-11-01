"""English versions of the cad/mech_figs.py figures used on the appendix slides.

  fig_section_en.png (cantilever)   fig_fea_{c1,beam,house,rail}_en.png (nextsteps)   fig_side_en.png / fig_top_en.png (parts)
  The fea_* PNGs are slide versions (1440 x 1024, few large labels) -- see SLIDE below.

Usage: python3 presentation/assets_en/make_cad_figs_en.py        (writes into presentation/assets_en/)

Safety: importing cad/mech_figs.py imports cad/build_sheet.py, which rewrites the tracked cad/cad_sheet.html. So this
script never imports them here. It copies the two modules and their inputs (travel_table.csv, key_poses.csv and three
JSON files from model/calc_v13/seat_1dof/) into a temp directory with the same layout, runs the figure functions there in
a subprocess (python -B, so no __pycache__ either), and reads back the SVG strings. Nothing in the repo is written
except the PNGs below.

The SVG <text> labels and aria-labels are translated through ZH2EN (terms per presentation/slides_en/STYLE.md), the page
CSS (light theme) is taken from cad/mech_page_tpl.py with Inter as the body font, and each figure is rasterised with
headless Chromium (node + playwright) at the pixel size of its Chinese PNG in presentation/assets_v57/ (SVG drawn at
width W - 96 px with a 48 px white margin, which is how those PNGs were framed).
"""
import json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# figure function -> (output name, pixel size of the Chinese PNG in assets_v57)
FIGS = {"section_view": ("fig_section", (3096, 1946)), "fea_c1": ("fig_fea_c1", (2000, 1894)), "fea_beam": ("fig_fea_beam", (2496, 1128)),
        "fea_house": ("fig_fea_house", (1896, 2696)), "fea_rail": ("fig_fea_rail", (1496, 2108)),
        "side_view": ("fig_side", (2896, 2952)), "top_view": ("fig_top", (2896, 2230))}

# Chinese label -> English label, or (English label, {attribute overrides / dx, dy nudges})
ZH2EN = {
    # section_view
    "铰点 1 轴线": "Pivot 1 axis",
    "偏 10 cm 的体重": ("Weight, 10 cm off-centre", dict(dx=18)),          # clear of balloon S2
    # fea_c1
    "窗口（80°）": "Window (80°)",
    "滑块面固定": "Carriage faces fixed",
    "▲ = 焊缝": "▲ = weld",
    # fea_beam
    "1471 N（+ 沿座面、侧向 0.3 倍）": "1471 N (+ 0.3× along seat and sideways)",
    "外缘下沉 ≈ 1.7 mm（放大画）": "Outer edge drops ≈ 1.7 mm (exaggerated)",
    "焊缝：横梁 ↔ 节点板（最大弯矩处）": "Weld: beam ↔ knuckle plate (max. moment)",
    "轴端法兰面固定": (["Shaft flange", "face fixed"], dict(dx=4, dy=4, lh=18)),       # right edge
    "高 30（被小腿间隙卡住）": ("Height 30 (calf clearance)", dict(dy=-2)),  # clear of the deflection line
    "y = −220（座板外缘）": "y = −220 (seat outer edge)",
    # fea_house
    "内壁竖槽（宽 87）": "Inner-wall slot (87 wide)",
    "⊙ 滑块力（主要垂直纸面）": "⊙ Carriage forces (mostly out of plane)",
    "底边和底座螺栓连接：固定": "Bottom edge bolted to base: fixed",
    # fea_rail
    "1668 N 向下": "1668 N down",
    "侧推": (["Side", "push"], dict(lh=32)),                           # clear of the grab bar
    "向人拉（垂直纸面）": (["Pull toward user", "(out of plane)"], dict(lh=32)),  # clear of the post
    "根部弯矩 1.53 kN·m": (["Root moment", "1.53 kN·m"], dict(dy=-80, lh=35)),  # right edge
    "焊缝 + 底座管局部": (["Weld + local", "base tube"], dict(dy=-40, lh=35)),
    # side_view / top_view
    "床": "Bed",
    "顶位（虚影）": "Top position (ghost)",
    "床尾方向 ↓": "Foot of bed ↓",
    "床头方向 ↑": "Head of bed ↑",
    "座面中心（齐平位）": "Seat centre (flush position)",
    "敞开一侧：人的腿从这边放下": "Open side: legs come down here",
    "机构箱（床头一侧）": "Mechanism housing (head end)",
    # aria-labels
    "沿铰点 1 轴线的剖面：座板、横梁、节点板、铰点 1 轴、两个圆锥滚子轴承、内壁竖槽、铰点 2 摆臂、滑块板、滑块、导轨、侧板":
        "Section along the pivot 1 axis: seat, beam, knuckle plate, pivot 1 shaft, two tapered roller bearings, inner-wall slot, "
        "pivot 2 arm, carriage plate, carriages, linear guides, side plate",
    "有限元重点 1：铰点 1 组件和滑块座焊件": "FEA focus 1: pivot 1 assembly and carriage-plate weldment",
    "有限元重点 2：座板横梁和节点板": "FEA focus 2: seat beam and knuckle plate",
    "有限元重点 3：机构箱盒体（带竖槽）": "FEA focus 3: mechanism housing box (with slot)",
    "有限元重点 4：扶手立柱和底座（正视，看 y-z 平面）": "FEA focus 4: grab-bar post and base (front view, y-z plane)",
    "侧视总装图：按比例，座板在齐平位，带零件编号": "Side view of the assembly: to scale, seat at flush position, with part codes",
    "俯视图：座板在齐平位，看横向（y）布置，带零件编号": "Top view: seat at flush position, lateral (y) layout, with part codes",
}
CJK = re.compile(r"[　-〿㐀-鿿＀-￯]")


def svgs_from_sandbox():
    """Run mech_figs in a temp copy so build_sheet's write of cad_sheet.html lands in the temp dir."""
    T = tempfile.mkdtemp(prefix="mechfigs_")
    try:
        os.makedirs(os.path.join(T, "cad")); os.makedirs(os.path.join(T, "model/calc_v13/seat_1dof"))
        for f in ("build_sheet.py", "mech_figs.py", "travel_table.csv", "key_poses.csv"):
            shutil.copy(os.path.join(ROOT, "cad", f), os.path.join(T, "cad", f))
        for f in ("cad_sheet.json", "cantilever3d.json", "parts.json"):
            shutil.copy(os.path.join(ROOT, "model/calc_v13/seat_1dof", f), os.path.join(T, "model/calc_v13/seat_1dof", f))
        code = ("import json, mech_figs as M\n"
                f"out = {{k: getattr(M, k)() for k in {list(FIGS)!r}}}; out['DEFS'] = M.DEFS\n"
                "json.dump(out, open('../svgs.json', 'w'), ensure_ascii=False)")
        subprocess.run([sys.executable, "-B", "-c", code], cwd=os.path.join(T, "cad"), check=True, stdout=subprocess.DEVNULL)
        return json.load(open(os.path.join(T, "svgs.json")))
    finally:
        shutil.rmtree(T, ignore_errors=True)


def page_css():
    """Light-theme variables + all `svg ...` rules of cad/mech_page_tpl.py (f-string braces undoubled), Latin fonts."""
    src = open(os.path.join(ROOT, "cad/mech_page_tpl.py"), encoding="utf-8").read()
    root = re.search(r"\n:root \{\{(.*?)\}\}", src, re.S).group(1)
    rules = [l for l in src.splitlines() if l.startswith("svg ") or l.startswith("svg.")]
    css = ":root {" + root + "}\n" + "\n".join(rules)
    css = css.replace("{{", "{").replace("}}", "}")
    css = re.sub(r"--body:[^;]*;", '--body:"Inter", "DejaVu Sans", Arial, sans-serif;', css)
    css = re.sub(r"--mono:[^;]*;", '--mono:"IBM Plex Mono", "JetBrains Mono", "DejaVu Sans Mono", monospace;', css)
    return css


def translate(svg):
    """Replace <text> content and aria-labels via ZH2EN. A tuple value (text or [lines], opts) may nudge the label
    (opts dx, dy in viewBox units) or break it into lines (tspans, line step lh)."""
    unesc = lambda s: s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def lookup(s):
        en = ZH2EN.get(s)
        if en is None:
            if CJK.search(s): raise SystemExit(f"no translation for {s!r}")
            return s, {}
        return en if isinstance(en, tuple) else (en, {})
    def text(m):
        attrs, body = m.group(1), unesc(m.group(2)); en, o = lookup(body)
        x = float(re.search(r' x="([-\d.]+)"', attrs).group(1)) + o.get("dx", 0)
        y = float(re.search(r' y="([-\d.]+)"', attrs).group(1)) + o.get("dy", 0)
        attrs = re.sub(r' x="[-\d.]+"', f' x="{x:.1f}"', attrs); attrs = re.sub(r' y="[-\d.]+"', f' y="{y:.1f}"', attrs)
        if isinstance(en, list):
            inner = "".join(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else o["lh"]}">{esc(t)}</tspan>' for i, t in enumerate(en))
        else:
            inner = esc(en)
        return f"<text{attrs}>{inner}</text>"
    svg = re.sub(r"<text([^>]*)>([^<]*)</text>", text, svg)
    svg = re.sub(r'aria-label="([^"]*)"', lambda m: 'aria-label="' + esc(lookup(unesc(m.group(1)))[0]) + '"', svg)
    assert not CJK.search(svg), "CJK left in SVG"
    return svg


RENDER_JS = r"""
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const b = await chromium.launch();
  for (const j of jobs) {
    const p = await b.newPage({ viewport: { width: j.w, height: j.h }, deviceScaleFactor: 1 });
    await p.goto('file://' + j.html); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    try { await p.screenshot({ path: j.png }); }
    catch (e) { await p.waitForTimeout(1000); await p.screenshot({ path: j.png, clip: { x: 0, y: 0, width: j.w, height: j.h } }); }
    await p.close(); console.log('wrote', j.png);
  }
  await b.close();
})();
"""


# --- slide versions of the four FEA sketches (appendix slide "nextsteps", shown in a 360 x 256 px box) -------------
# The full-page figures carry many small labels; on the slide they shrank to ~6 px. For the slide the four fea_* PNGs
# are re-drawn at 1440 x 1024 (4x the box, same aspect): the geometry of the mech_figs SVG is kept (its <text> labels
# removed, cropped by a custom viewBox) and only a few large labels (80 px here = 20 px on the slide) are overlaid.
SW, SH, FS = 1440, 1024, 80          # canvas, label font size (px at 1440 wide; /4 on the slide)

# name -> (crop viewBox in the figure's own SVG units [x, y, w, h], placement [x, y, w, h] on the canvas, overlay fn)
def _slide_labels():
    def T(x, y, t, anchor="start", cls="sl"):
        lines = t if isinstance(t, list) else [t]
        sp = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else round(FS * 1.08)}">{l}</tspan>' for i, l in enumerate(lines))
        return f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{sp}</text>'
    L = lambda x1, y1, x2, y2: f'<line class="sldr" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
    return T, L

def slide_overlay(name, M):
    """M(X, Y) maps the figure's own SVG units to canvas px. Returns overlay SVG (labels, leaders)."""
    T, L = _slide_labels(); o = []
    if name == "fig_fea_c1":            # own units: X = u - 120, Y = 140 - v
        o.append(T(M(85, 0)[0] - 30, 130, "F₁", "end", "sl slr"))
        o.append(T(20, M(0, 190)[1] + 40, ["M₁", "586 N·m"], "start", "sl slr"))
        o.append(T(M(230, 0)[0], M(0, 75)[1], "Fixed"))
        w = M(166, 177); o.append(T(1100, 870, "▲ weld", "start", "sl sla")); o.append(L(1090, 845, w[0] + 10, w[1]))
        o.append(T(M(131.5, 0)[0] + 24, 1000, "80° window"))
    elif name == "fig_fea_beam":        # own units: X = u + 250, Y = 112 - v
        o.append(T(M(150, 0)[0] + 30, 170, "1471 N", "start", "sl slr"))
        o.append(T(1430, 110, "Fixed", "end"))
        o.append(T(20, 760, "Outer edge sag ≈ 1.6 mm", "start", "sl slr"))
        w = M(455, 130); o.append(T(1420, 950, "▲ weld (max. moment)", "end", "sl sla")); o.append(L(1300, 885, w[0], w[1] + 12))
    elif name == "fig_fea_house":       # own units: X = u + 30, Y = 860 - v
        o.append(T(700, 110, ["⊙ Carriage forces", "out of plane", "(≤ 3.8 kN each)"], "start", "sl slr"))
        a = M(230, 560); o.append(T(700, 560, "Slot (87 wide)")); o.append(L(690, 535, a[0], a[1]))
        o.append(T(700, 900, ["Bottom edge", "fixed"]))
    elif name == "fig_fea_rail":        # own units: X = u + 160, Y = 1080 - v
        o.append(T(M(110, 0)[0] - 30, 110, "1668 N", "end", "sl slr"))
        o.append(T(1420, 470, ["Root moment", "1.53 kN·m"], "end", "sl slr"))
        w = M(500, 1035); o.append(T(1420, 800, ["▲ weld +", "base tube"], "end", "sl sla")); o.append(L(1130, 760, w[0] + 8, w[1] - 10))
    return "".join(o)

SLIDE = {  # crop [x, y, w, h] in figure units ; placement [x, y, w, h] on canvas ; extra CSS (strokes for small-scale figures)
    "fig_fea_c1": ((0, 25, 300, 225), (0, 0, SW, SH), ""),
    "fig_fea_beam": ((20, 50, 590, 150), (0, 160, SW, 470), " svg .farr { stroke-width:5 } svg .defl { stroke-width:5 }"),
    "fig_fea_house": ((20, 0, 580, 920), (10, 10, 660, 1004), " svg .house { stroke-width:5 } svg .slot { stroke-width:4 } svg .oop { stroke-width:6 } svg .fixl { stroke-width:6 } svg .fixh { stroke-width:3 }"),
    "fig_fea_rail": ((0, 0, 780, 1120), (240, 10, 700, 1004), " svg .farr { stroke-width:8 } svg .fixl { stroke-width:6 } svg .fixh { stroke-width:3 } svg .oop { stroke-width:6 }"),
}

SLIDE_CSS = (".sl { font:500 %dpx 'Inter', 'DejaVu Sans', Arial, sans-serif; fill:#1A2430; paint-order:stroke; stroke:#fff;"
             " stroke-width:14px; stroke-linejoin:round } .slr { fill:#B3261E; font-weight:700 } .sla { fill:#9A5408; font-weight:700 }"
             " .sldr { stroke:#1A2430; stroke-width:4 }" % FS)


def slide_svg(name, svg):
    (cx, cy, cw, ch), (px, py, pw, ph), _ = SLIDE[name]
    s = min(pw / cw, ph / ch); ox = px + (pw - cw * s) / 2; oy = py + (ph - ch * s) / 2
    M = lambda X, Y: (round(ox + (X - cx) * s), round(oy + (Y - cy) * s))
    inner = re.sub(r"<text[^>]*>.*?</text>", "", svg, flags=re.S)
    if s < 2:   # small-scale figures: enlarge the out-of-plane markers
        inner = re.sub(r'(class="oop"[^>]*?) r="[\d.]+"', r'\1 r="22"', inner)
        inner = re.sub(r'(class="oopd"[^>]*?) r="[\d.]+"', r'\1 r="8"', inner)
    inner = re.sub(r'<svg class="[^"]*" viewBox="[^"]*"', f'<svg x="{px}" y="{py}" width="{pw}" height="{ph}" viewBox="{cx} {cy} {cw} {ch}"', inner, count=1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SW} {SH}" width="{SW}" height="{SH}" style="display:block">'
            f'<rect width="{SW}" height="{SH}" fill="#fff"/>{inner}{slide_overlay(name, M)}</svg>')


def main():
    S = svgs_from_sandbox(); css = page_css(); tmp = tempfile.mkdtemp(prefix="mechfigs_html_"); jobs = []
    fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap">'
    try:
        for fn, (name, (W, H)) in FIGS.items():
            svg = translate(S[fn])
            if name in SLIDE:      # slide version: large labels, 1440 x 1024
                html = (f'<!doctype html><meta charset="utf-8">{fonts}<style>{css}\n{SLIDE_CSS}{SLIDE[name][2]}\n'
                        f'html, body {{ margin:0; background:#fff }}</style>{S["DEFS"]}{slide_svg(name, svg)}')
                hp = os.path.join(tmp, name + ".html"); open(hp, "w", encoding="utf-8").write(html)
                jobs.append(dict(html=hp, png=os.path.join(HERE, name + "_en.png"), w=SW, h=SH)); continue
            html = (f'<!doctype html><meta charset="utf-8">{fonts}<style>{css}\n'
                    f'html, body {{ margin:0; background:#fff }} body {{ padding:48px; width:{W - 96}px; height:{H - 96}px }}\n'
                    f'svg.fig {{ display:block; width:{W - 96}px; height:{H - 96}px; min-width:0 }}</style>'
                    f'{S["DEFS"]}{svg}')
            hp = os.path.join(tmp, name + ".html"); open(hp, "w", encoding="utf-8").write(html)
            jobs.append(dict(html=hp, png=os.path.join(HERE, name + "_en.png"), w=W, h=H))
        jp = os.path.join(tmp, "jobs.json"); json.dump(jobs, open(jp, "w"))
        js = os.path.join(tmp, "render.js"); open(js, "w").write(RENDER_JS)
        subprocess.run(["node", js, jp], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
