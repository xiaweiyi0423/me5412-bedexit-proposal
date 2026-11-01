"""Safety-anatomy figure for the risk slide (side view, drawn from the model like the other seat figures).
  risk_anatomy.png  device mid-lift (frame of max tilt), ghosted user, numbered markers ① ② ⑤ ⑥ at the parts they concern.
The callout text lives on the slide (presentation/slides/risk.html), keyed by the same numbers.
Reuses the drawing code of presentation/animations/make_seat_gif.py (import does not regenerate its figures).
Usage: python3 make_risk_fig.py
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "presentation", "animations"))
import make_seat_gif as G   # noqa: E402  (palette, layout data D/M/L/BAR, scene/housing/handrail/mechanism/person)

INK, STEEL, STEEL2, ACC, RED, GOOD, BG = G.INK, G.STEEL, G.STEEL2, G.ACC, G.RED, G.GOOD, G.BG
M, L, BAR = G.M, G.L, G.BAR
MARK = "#B4620A"          # marker fill (deck accent)


def marker(ax, n, xy, targets):
    """numbered disc at xy with thin leader lines ending in a dot at each target."""
    for t in targets:
        ax.plot([xy[0], t[0]], [xy[1], t[1]], color=MARK, lw=3.0, zorder=20, solid_capstyle="round")
        ax.add_patch(Circle(t, 0.013, facecolor=MARK, edgecolor="#FFFFFF", lw=1.2, zorder=21))
    ax.add_patch(Circle(xy, 0.056, facecolor=MARK, edgecolor="#FFFFFF", lw=2.5, zorder=22))
    ax.text(xy[0], xy[1] - 0.002, str(n), ha="center", va="center", fontsize=38, fontweight="bold", color="#FFFFFF", zorder=23, fontfamily="DejaVu Sans")


def render(path, user=G.REF, k=15):
    A = G.D["anim"][user]; fr = A["frames"][k]; Q, phi = fr["seat"]["Q"], fr["seat"]["phi"]
    x0, x1, z0, z1 = -0.38, 1.06, -0.03, 1.21
    fig = plt.figure(figsize=(8.2, 8.2 * (z1 - z0) / (x1 - x0)), dpi=145); ax = fig.add_axes([0, 0, 1, 1])
    G.scene(ax, x0, x1, z1); ax.set_ylim(z0, z1)
    for t in list(ax.texts): t.remove()                      # drop the "床" label: all text is on the slide
    G.housing(ax, 0.30); G.handrail(ax)
    # motor + power-off brake at the top of the housing (layout polygon from the model)
    ax.add_patch(Polygon(L["motor"], closed=True, facecolor=STEEL, edgecolor=INK, lw=1.2, alpha=.85, zorder=6))
    # base-to-bed fixing: clamp plate from the base end onto the bed frame
    ax.add_patch(Rectangle((-0.07, 0.0), 0.11, 0.045, facecolor=STEEL, edgecolor=INK, lw=1.2, zorder=6))
    ax.add_patch(Rectangle((-0.07, 0.045), 0.03, 0.10, facecolor=STEEL, edgecolor=INK, lw=1.2, zorder=6))
    # bar end: soft round head with glow strip (halo)
    ax.add_patch(Circle((BAR["x"], BAR["z"]), 0.040, facecolor="#E8F2C8", edgecolor="#9DBF5A", lw=2, alpha=.9, zorder=6))
    # emergency lever with flip cover, under the bar corner
    lx, lz = BAR["x"] - 0.035, BAR["z"] - 0.075
    ax.add_patch(Rectangle((lx - 0.012, lz - 0.012), 0.05, 0.03, facecolor=RED, edgecolor=INK, lw=1, zorder=7))
    ax.plot([lx, lx - 0.045], [lz, lz - 0.035], color=INK, lw=3.2, solid_capstyle="round", zorder=7)
    # user: pale, opaque, drawn behind the translucent housing (view from the head side), so the parts stay readable
    n_p, n_l = len(ax.patches), len(ax.lines); body, limb = G.BODY, G.LIMB
    G.BODY, G.LIMB = "#EDE4D9", "#DCCDBD"
    G.person(ax, A, fr, rb=A.get("rb", 0.09)); G.BODY, G.LIMB = body, limb
    for art in ax.patches[n_p:] + ax.lines[n_l:]: art.set_zorder(1.8)
    P1, P2 = G.mechanism(ax, Q, phi)
    # tilt arc on the seat (shows the forward tilt)
    rear = G.W(Q, phi, (-G.HALF, 0.0)); front = G.W(Q, phi, (G.HALF, 0.0))
    ax.plot([rear[0], rear[0] + 0.26], [rear[1], rear[1]], color=INK, lw=1.2, ls=(0, (4, 3)), zorder=11)
    a = np.radians(np.linspace(-phi, 0, 20)); ax.plot(rear[0] + 0.24 * np.cos(a), rear[1] + 0.24 * np.sin(a), color=INK, lw=2.4, zorder=11)
    mot = np.mean(L["motor"], axis=0)
    marker(ax, 1, (-0.27, 0.58), [tuple(rear + np.array([0.0, -0.02])), tuple(P1)])          # soft rear edge; bracket through the brush slot (seat side edge 3 cm from the housing wall)
    marker(ax, 2, (-0.22, 0.90), [tuple(G.W(Q, phi, (0.05, -0.03)))])                                # cushion
    marker(ax, 5, (0.96, 0.60), [tuple(mot), (lx - 0.045, lz - 0.035)])                           # motor + brake; lever under the bar corner
    marker(ax, 6, (0.96, 1.12), [(BAR["x"] + 0.03, BAR["z"] + 0.03)])                            # bar end
    marker(ax, 6, (-0.27, 0.10), [(-0.055, 0.10)])                                                # base fixed to the bed
    fig.savefig(path, facecolor=BG); plt.close(fig)


if __name__ == "__main__":
    render(os.path.join(HERE, "risk_anatomy.png")); print("done")
