"""Next-version concept figure in the deck's figure style (same bed, housing, mechanism and mannequin as the other
figures; drawing functions from presentation/animations/make_seat_gif.py). Three panels:
  ① move + lock, seat start height fits the bed   ② floating seat (±5° sprung)   ③ flip-up bar + walker clip
Orange = parts that change in the next version. Numbers match the "four limits, four fixes" cards.
Usage: python3 presentation/assets_v7/make_concept_fig.py  ->  concept_next_zh.png, concept_next_en.png
Concept only: nothing here is modelled; the geometry of the new parts is schematic.
"""
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "presentation", "animations"))
import make_seat_gif as G
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon, FancyArrowPatch, Arc
plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]

TXT = {"zh": {"bed": "床", "lock": "锁止\n支脚落地", "h": "座高可调\n（床或沙发）", "float": "座板浮动 ±5°", "flip": "横杆上翻", "clip": "助行器卡扣",
              "p1": "① 移动 + 锁止 + 座高可调", "p2": "② 座板浮动，贴合臀部", "p3": "③ 横杆翻开，接上助行器"},
       "en": {"bed": "Bed", "lock": "Lock:\nfeet down", "h": "Start height\nfits bed / sofa", "float": "Floating ±5°", "flip": "Bar flips up", "clip": "Walker clip",
              "p1": "① Move, lock, set height", "p2": "② Seat floats to fit the hips", "p3": "③ Flip the bar, take the walker"}}
Z0, Z1 = -0.06, 1.86
FS = 1.0   # font scale (set per output)


def panel(fig, rect, x0, x1, lang, title):
    if FS > 1.2: title = title[:1]          # big-font version: number only (the slide key explains)
    ax = fig.add_axes(rect); G.scene(ax, x0, x1, Z1, Z0)
    ax.texts[-1].set_text(TXT[lang]["bed"]); ax.texts[-1].set_fontsize(15 * FS)
    ax.text(x0 + 0.04, Z1 - 0.07, title, ha="left", va="top", fontsize=19 * FS, fontweight="bold", color=G.INK)
    return ax


def casters(ax, locked=True):
    for x in (0.09, 0.72):                                   # casters lifted ~1 cm when locked
        ax.add_patch(Circle((x, 0.032 if locked else 0.022), 0.022, facecolor=G.INK, edgecolor=G.BG, lw=1, zorder=6))
    for x in (0.05, 0.76):                                   # lock feet (orange = new)
        ax.add_patch(Rectangle((x - 0.022, -0.005), 0.044, 0.02, facecolor=G.ACC, edgecolor=G.INK, lw=0.8, zorder=6))


def padlock(ax, x, z, s=0.05):
    ax.add_patch(Rectangle((x - s * 0.55, z), s * 1.1, s * 0.85, facecolor=G.GOOD, zorder=7))
    ax.add_patch(Arc((x, z + s * 0.85), s * 0.8, s * 0.9, theta1=0, theta2=180, color=G.GOOD, lw=3, zorder=7))


def walker(ax, x, clip_z=0.62):
    for xx in (x, x + 0.30):
        ax.plot([xx, xx], [0.0, 0.86], color=G.INK, lw=4, solid_capstyle="round", zorder=5)
        ax.add_patch(Rectangle((xx - 0.02, -0.01), 0.04, 0.02, color=G.INK, zorder=5))
    ax.plot([x, x + 0.30], [0.86, 0.86], color=G.INK, lw=4, zorder=5); ax.plot([x, x + 0.30], [0.45, 0.45], color=G.INK, lw=3, zorder=5)
    ax.add_patch(Rectangle((G.BAR["x"] + 0.01, clip_z - 0.03), x - G.BAR["x"] - 0.01, 0.06, facecolor=G.ACC, edgecolor=G.INK, lw=0.8, zorder=6))


def label(ax, x, z, s, ha="left", fs=15, col=None):
    ax.text(x, z, s, ha=ha, va="center", fontsize=fs * FS, color=col or G.ACC, fontweight="bold", zorder=20, linespacing=1.15)


def main(lang, fs=1.0, suffix=""):
    global FS; FS = fs
    A = G.D["anim"][G.REF]; fr = A["frames"]; idx = [i for i, f in enumerate(fr) if f.get("seat")]
    T = TXT[lang]; rb = A.get("rb", 0.09)
    xs = [(-0.40, 1.30), (-0.25, 1.15), (-0.25, 1.75)]           # panel x ranges (m), same scale
    widths = [b - a for a, b in xs]; H = Z1 - Z0; gap = 0.04; Wt = sum(widths) + gap * 2
    fig = plt.figure(figsize=(Wt / H * 6.0, 6.0), dpi=200)
    rects, cx = [], 0.0
    for w in widths: rects.append([cx / Wt, 0, w / Wt, 1]); cx += w + gap
    # ① empty frame at rest: casters + lock feet, start-height arrow, sofa ghost
    ax = panel(fig, rects[0], *xs[0], lang, T["p1"])
    Q0, p0 = G.M["frames"][0]["Q"], G.M["frames"][0]["phi"]
    G.housing(ax); G.handrail(ax); G.mechanism(ax, Q0, p0); casters(ax)
    padlock(ax, 0.88, 0.05)
    if FS > 1.2: label(ax, 0.88, 0.22, T["lock"].split("\n")[0].rstrip(":："), ha="center", fs=14)
    else: label(ax, 0.95, 0.12, T["lock"], fs=14)
    sx = G.W(Q0, p0, (G.HALF, 0.0))[0] + 0.05
    ax.add_patch(FancyArrowPatch((sx, Q0[1] - 0.10), (sx, Q0[1] + 0.12), arrowstyle="<|-|>", mutation_scale=18, color=G.ACC, lw=2.5, zorder=12))
    label(ax, -0.36, 0.66, T["h"], fs=14)
    ax.plot([-0.05, sx - 0.02], [0.66, Q0[1] + 0.02], color=G.ACC, lw=1.2, zorder=11)
    # ② mid-rise, floating seat marker
    ax = panel(fig, rects[1], *xs[1], lang, T["p2"])
    k = (idx[0] + idx[-1]) // 2; f = fr[k]; cu = f.get("cush", {}).get("z1")
    Q, phi = (cu["Q"], cu["phi"]) if cu and not cu.get("lost") else (f["seat"]["Q"], f["seat"]["phi"])
    G.housing(ax); G.handrail(ax); G.mechanism(ax, Q, phi); G.person(ax, A, f, rb=rb)
    if cu and not cu.get("lost"): G.strip(ax, cu)
    c = G.W(Q, phi, (0.0, -0.02))
    ax.add_patch(Arc(c, 0.36, 0.36, theta1=150 + phi, theta2=210 + phi, color=G.ACC, lw=3.5, zorder=13))
    for t in (150 + phi, 210 + phi):
        r = math.radians(t); ax.add_patch(Circle((c[0] + 0.18 * math.cos(r), c[1] + 0.18 * math.sin(r)), 0.014, color=G.ACC, zorder=13))
    label(ax, -0.20, 1.10, T["float"], fs=15)
    m = (c[0] + 0.18 * math.cos(math.radians(180 + phi)), c[1] + 0.18 * math.sin(math.radians(180 + phi)))
    ax.plot([-0.02, m[0]], [1.06, m[1]], color=G.ACC, lw=1.2, zorder=11)
    # ③ standing, bar flipped up, walker clipped at the post
    ax = panel(fig, rects[2], *xs[2], lang, T["p3"])
    last = G.M["frames"][-1]; fe = fr[idx[-1] + 1] if idx[-1] + 1 < len(fr) else fr[idx[-1]]
    G.housing(ax); G.mechanism(ax, fr[idx[-1]]["seat"]["Q"], fr[idx[-1]]["seat"]["phi"])
    bx, bz = G.BAR["x"], G.BAR["z"]
    ax.plot([bx, bx], [0.04, bz], color=G.STEEL, lw=5, alpha=.45, zorder=2, solid_capstyle="round")
    ax.add_patch(Circle((bx, bz), 0.022, facecolor="none", edgecolor=G.MUTED, lw=1.5, ls="--", zorder=7))      # old bar position
    ax.plot([bx, bx], [bz, bz + 0.34], color=G.ACC, lw=7, solid_capstyle="round", zorder=7)                      # bar flipped up
    ax.add_patch(FancyArrowPatch((bx + 0.16, bz + 0.02), (bx + 0.06, bz + 0.32), connectionstyle="arc3,rad=0.45", arrowstyle="-|>",
                                 mutation_scale=16, color=G.ACC, lw=2, ls="--", zorder=12))
    label(ax, bx + 0.16, bz + 0.20, T["flip"], fs=15)
    G.person(ax, A, fe, bar=False, rb=rb)
    walker(ax, bx + 0.22); label(ax, bx + 0.56, 0.62, T["clip"].replace("器", "器\n", 1) if lang == "zh" else T["clip"].replace(" ", "\n", 1), fs=15)
    out = os.path.join(HERE, f"concept_next_{lang}{suffix}.png"); fig.savefig(out, facecolor=G.BG); plt.close(fig); print(out)


if __name__ == "__main__":
    for lg in ("zh", "en"):
        G.set_lang(lg) if hasattr(G, "set_lang") else None
        main(lg)
        main(lg, 1.7, "_big")      # for a small strip on a slide (teammate's page)
