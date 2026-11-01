"""Clean load-path figure for the main 'mechanism' slide (v7).

Geometry: the c1-axis section of cad/mech_figs.py::section_view() (the same drawing behind assets_v57/fig_section.png),
regenerated here with the part-code balloons, tick labels and old load arrow switched off. On top: three numbered
load-path arrows (load -> bearing pair -> carriage plate -> twin rails). Numbers are read from
model/calc_v13/seat_1dof/parts.json, not typed in.

Usage: python3 presentation/assets_v7/make_loadpath_fig.py [--lang zh|en]
  zh -> presentation/assets_v7/fig_loadpath.png       en -> presentation/assets_v7/fig_loadpath_en.png
Rasterised with headless Chromium (node + playwright, as in presentation/tools/render_slide_local.js).
"""
import argparse, json, os, subprocess, sys, html, math

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK = os.path.join(ROOT, ".work", "mechanism")
sys.path.insert(0, os.path.join(ROOT, "cad"))
import mech_figs as MF  # noqa: E402

ACC, INK, MUTED = "#B4620A", "#18202A", "#66707C"
FONT = "'WenQuanYi Zen Hei', sans-serif"
DISPLAY_W = 896          # px on the 1920 slide
SCALE = 2                # export at 2x display

# ---------------------------------------------------------------- numbers (from the calc output)
P = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/parts.json")))
st, c1, car = P["statics"], P["c1"], P["carriage"]
case = P["cases"]["c1_moment_Nm"]
Fz, Fy = -case["load_N"][2], case["load_N"][1]
assert abs(Fz - 1.5 * 100 * 9.81) < 1, Fz                       # 100 kg x 1.5
assert abs(Fy / Fz + 0.3) < 0.01, Fy                             # 0.3 x side push toward the open side
assert abs(case["load_point_mm"][1] + 100) < 1                   # 10 cm toward the open side
M1 = st["c1_moment_Nm"]["value"]                                 # 586
SF_BRG = c1["sf"]                                                # 3.23
CAR_KN, SF_CAR = car["P0_kN"], car["sf"]                         # 5.18, 2.52
SPACING = c1["spacing_mm"]                                       # 45

TXT = {
    "zh": {
        "l1": [f"① 偏载：100 kg × 1.5，偏向敞开一侧 10 cm", "另加 0.3 倍侧推"],
        "l2": [f"② 一对圆锥滚子轴承", f"{M1:.0f} N·m，安全系数 {SF_BRG:.1f}"],
        "l3": ["③ 经滑块板到双导轨", f"最重滑块 {CAR_KN:.1f} kN", f"安全系数 {SF_CAR:.1f}"],
        "open": "← 敞开一侧", "out": "fig_loadpath.png",
    },
    "en": {
        "l1": ["① Offset load: 100 kg × 1.5, 10 cm toward open side", "(+0.3 lateral push)"],
        "l2": ["② Tapered roller bearing pair", f"{M1:.0f} N·m, SF {SF_BRG:.1f}"],
        "l3": ["③ Twin linear guides", "(via carriage plate)", f"max carriage {CAR_KN:.1f} kN", f"SF {SF_CAR:.1f}"],
        "open": "← open side", "out": "fig_loadpath_en.png",
    },
}

# ---------------------------------------------------------------- base section without codes
MF.Fig.balloon = lambda *a, **k: None
MF.Fig.text = lambda *a, **k: None                                 # axis label, old load label, tick numbers
MF.Fig.arrow = lambda *a, **k: None                                # old red load arrow
_line = MF.Fig.line
MF.Fig.line = lambda s, a, b, cls, extra="": None if cls == "grid" else _line(s, a, b, cls, extra)
sec = MF.section_view()
inner = sec[sec.index(">") + 1: sec.rindex("</svg>")]               # drop the outer <svg ...> of the original
U0, V1 = -260, 175                                                # original frame: X = u - U0, Y = V1 - v
X = lambda u: u - U0
Y = lambda v: V1 - v

CSS_VARS = {"paper": "#F3F5F2", "sheet": "#FFFFFF", "ink": "#1A2430", "ink2": "#46515E", "muted": "#6B7480", "rule": "#D5D9DD",
            "blue": "#1E5AA8", "blue2": "#A9C1E4", "red": "#B3261E", "foam": "#E9B872", "foam2": "#F4D9AE", "wood": "#C9A36B",
            "steel": "#5B6B7C", "steel2": "#B8C1CB"}
CSS = """
.plate{fill:var(--blue2);stroke:var(--blue);stroke-width:1.5}.carr{fill:var(--blue);opacity:.75}.cartc{fill:var(--red);fill-opacity:.3;stroke:var(--red);stroke-width:2}
.nut,.shaft{fill:var(--ink2)}.foamr{fill:var(--foam)}.foamf{fill:var(--foam2)}.board{fill:var(--wood)}.arm,.beam{fill:var(--steel)}
.linkp{stroke:var(--ink2);stroke-width:16;stroke-linecap:round}.rodp{fill:var(--sheet);stroke:var(--ink2);stroke-width:3}
.axisl{stroke:var(--red);stroke-width:1.2;stroke-dasharray:10 3 2 3}.scell{fill:var(--blue)}.sbrg{fill:var(--sheet);stroke:var(--ink);stroke-width:1}
.sbrgx{stroke:var(--ink);stroke-width:1}.swall{fill:var(--muted)}.sback{fill:var(--steel2)}.brush{stroke:var(--ink);stroke-width:2.2;stroke-dasharray:1 2}
.railt{fill:var(--ink);fill-opacity:.6}
"""


def arrow(pts, w=11, head=34, hw=30):
    """thick polyline arrow in the accent colour with a white halo; pts in (u, v)."""
    P_ = [(X(u), Y(v)) for u, v in pts]
    (x0, y0), (x1, y1) = P_[-2], P_[-1]
    L = math.hypot(x1 - x0, y1 - y0); dx, dy = (x1 - x0) / L, (y1 - y0) / L
    bx, by = x1 - dx * head, y1 - dy * head
    shaft = P_[:-1] + [(bx, by)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in shaft)
    tri = f"{x1:.1f},{y1:.1f} {bx - dy * hw / 2:.1f},{by + dx * hw / 2:.1f} {bx + dy * hw / 2:.1f},{by - dx * hw / 2:.1f}"
    return (f'<path d="{d}" fill="none" stroke="#fff" stroke-width="{w + 10}" stroke-linejoin="round"/>'
            f'<polygon points="{tri}" fill="#fff" stroke="#fff" stroke-width="10" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{ACC}" stroke-width="{w}" stroke-linejoin="round"/>'
            f'<polygon points="{tri}" fill="{ACC}"/>')


def badge(u, v, n, r=21):
    return (f'<circle cx="{X(u):.1f}" cy="{Y(v):.1f}" r="{r + 4}" fill="#fff"/><circle cx="{X(u):.1f}" cy="{Y(v):.1f}" r="{r}" fill="{ACC}"/>'
            f'<text x="{X(u):.1f}" y="{Y(v) + 9:.1f}" text-anchor="middle" font-size="27" font-weight="700" fill="#fff">{n}</text>')


def label(u, v, lines, size=30, gap=38, first_bold=True, anchor="start"):
    o = []
    for i, t in enumerate(lines):
        wt, col = ("700", ACC) if (i == 0 and first_bold) else ("700", INK)
        o.append(f'<text x="{X(u):.1f}" y="{Y(v - i * gap):.1f}" text-anchor="{anchor}" font-size="{size}" font-weight="{wt}" fill="{col}" '
                 f'stroke="#fff" stroke-width="7" paint-order="stroke" stroke-linejoin="round">{html.escape(t)}</text>')
    return "".join(o)


def build(lang):
    T = TXT[lang]
    # canvas in original (u, v) mm: u -255..760, v -160..222; parts above v=140 are clipped to free a label band
    u_lo, u_hi, v_lo, v_hi, v_clip = -270, 770, -158, 238, 140
    vb = f"{X(u_lo)} {Y(v_hi)} {u_hi - u_lo} {v_hi - v_lo}"
    c = 69.7  # seat top (same constant as section_view)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" style="width:100%;height:auto;display:block;font-family:{FONT}">',
         f'<rect x="{X(u_lo)}" y="{Y(v_hi)}" width="{u_hi - u_lo}" height="{v_hi - v_lo}" fill="#FFFFFF"/>',
         f'<clipPath id="cl"><rect x="{X(u_lo)}" y="{Y(v_clip)}" width="{u_hi - u_lo}" height="{v_clip - v_lo}"/></clipPath>',
         f'<g clip-path="url(#cl)">{inner}</g>']
    # highlight the parts on the path: bearing pair, carriage plate, rail
    hl = lambda u0, u1, v0, v1: f'<rect x="{X(u0)}" y="{Y(v1)}" width="{u1 - u0}" height="{v1 - v0}" fill="none" stroke="{ACC}" stroke-width="4" rx="4"/>'
    o += [hl(226, 294, -31, 31)]
    o.append(f'<text x="{X(-248)}" y="{Y(80)}" font-size="22" fill="{MUTED}">{html.escape(T["open"])}</text>')
    # ① load: down onto the seat, 10 cm toward the open side (u = -100)
    o.append(arrow([(-100, 132), (-100, c + 2)], w=13, head=38, hw=36))
    o.append(label(-250, 205, T["l1"]))
    # ② seat -> beam/knuckle/shaft -> bearing pair, along the c1 axis
    o.append(arrow([(-60, 0), (224, 0)]))
    o.append(badge(-60, 0, "②"))
    o.append(label(-250, -102, T["l2"]))
    # ③ bearing pair -> cartridge welded to the carriage plate -> carriages -> rails
    o.append(arrow([(296, 0), (348, 0)], head=30, hw=30))
    o.append(arrow([(298, 34), (298, 105), (348, 105)], head=30, hw=30))
    o.append(label(372, 72 if len(T["l3"]) == 3 else 92, T["l3"]))
    o.append("</svg>")
    return "".join(o), (u_hi - u_lo) / (v_hi - v_lo)


def render(svg, aspect, out_png, tag):
    os.makedirs(WORK, exist_ok=True)
    w = DISPLAY_W * SCALE; h = round(w / aspect)
    vars_ = ";".join(f"--{k}:{v}" for k, v in CSS_VARS.items())
    doc = (f"<!doctype html><meta charset=utf-8><style>*{{margin:0;padding:0}} :root{{{vars_}}} body{{width:{w}px;background:#fff}} {CSS}</style>{svg}")
    hp = os.path.join(WORK, f"loadpath_{tag}.html"); open(hp, "w").write(doc)
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"const p=await b.newPage({{viewport:{{width:{w},height:{h}}}}});await p.goto('file://{hp}');await p.waitForTimeout(300);"
          f"await p.screenshot({{path:'{out_png}',clip:{{x:0,y:0,width:{w},height:{h}}}}});await b.close();}})();")
    subprocess.run(["node", "-e", js], check=True)
    print("wrote", out_png, w, "x", h)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    a = ap.parse_args()
    svg, asp = build(a.lang)
    render(svg, asp, os.path.join(os.path.dirname(os.path.abspath(__file__)), TXT[a.lang]["out"]), a.lang)
