"""Team slide figure: side view of the CURRENT design (inclined rail + tilt link, closed housing, L-handrail with grip
switch, footplate, sensors) with a user mid-rise, and five numbered markers for the five roles.
Reuses the drawing functions and data of presentation/animations/make_seat_gif.py (model/calc_v13/seat_1dof/page.json).
Usage: python3 presentation/assets_v7/make_team_fig.py [--lang zh|en|both] [--frame N]
  ->  presentation/assets_v7/team_roles.png (zh, label 床) and team_roles_en.png (en, label Bed), 1200 x 1012
Only text in the image: the bed label, the digits 1-5 and (en) two corner labels.
en numbers follow the five speakers: 1 whole system, 2 rising model, 3 mechanism + structure, 4 sensing + control, 5 products + next version.
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "presentation", "animations"))
import make_seat_gif as G                       # import only: its figures are generated under __main__
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]

USER = G.REF                                    # H1.60 m, r_b 0.09, early-hip p1.0 reference user (as in the GIF)
SENS = "#E3A92E"                                # sensor colour of the sensing slide

def main(path, k=None, lang="zh"):
    A = G.D["anim"][USER]; fr = A["frames"]; idx = [i for i, f in enumerate(fr) if f.get("seat")]
    k = (idx[0] + idx[-1]) // 2 if k is None else k          # mid-rise frame (same pick as seat_step4.png)
    f = fr[k]; cu = f.get("cush", {}).get("z1")
    Q, phi = (cu["Q"], cu["phi"]) if cu and not cu.get("lost") else (f["seat"]["Q"], f["seat"]["phi"])
    fig = plt.figure(figsize=(6.0, 5.06), dpi=200); ax = fig.add_axes([0, 0, 1, 1])
    x0, x1 = -0.50, 1.00; z1 = (x1 - x0) * 5.06 / 6.0 - 0.04
    G.scene(ax, x0, x1, z1); ax.texts[-1].set_fontsize(15); ax.texts[-1].set_text("床" if lang == "zh" else "Bed")
    # bed fixing: bracket from the base to the bed frame (bolted)
    ax.add_patch(Polygon([(-0.035, 0.04), (0.11, 0.04), (0.11, 0.065), (0.0, 0.065), (0.0, 0.20), (-0.035, 0.20)], closed=True, color=G.STEEL, zorder=3))
    for bz in (0.10, 0.165): ax.add_patch(Circle((-0.0175, bz), 0.008, color=G.BG, zorder=4))
    G.housing(ax); G.handrail(ax); G.mechanism(ax, Q, phi); G.person(ax, A, f, rb=A.get("rb", 0.09))
    BAR = G.BAR
    # sensors (as on the sensing slide): under the seat, in the bar, at the grip switch, under the footplate
    seat_s = G.W(Q, phi, (0.03, -0.105)); bar_s = (BAR["x"], BAR["z"] - 0.06); grip_s = (BAR["x"], BAR["z"]); foot_s = (0.40, 0.02)
    for (x, z) in (seat_s, bar_s, foot_s):
        ax.add_patch(Rectangle((x - 0.018, z - 0.012), 0.036, 0.024, facecolor=SENS, edgecolor=G.INK, lw=1.0, zorder=12))
    ax.add_patch(Circle(grip_s, 0.026, facecolor=SENS, edgecolor=G.INK, lw=1.2, zorder=12))
    R = 0.046
    def mark(n, x, z, r=R, fs=20):
        ax.add_patch(Circle((x, z), r, facecolor=G.ACC, edgecolor="white", lw=2.0, zorder=20))
        ax.text(x, z - 0.002, str(n), ha="center", va="center", color="white", fontsize=fs, fontweight="bold", fontfamily="DejaVu Sans", zorder=21)
    Hp, K = np.array(f["Hp"]), np.array(f["K"])
    if lang == "zh":                                                       # zh figure: original layout, unchanged
        mark(1, -0.11, 0.68)                                               # the use situation: person at the bed edge
    else:                                                                  # en: role 1 = whole system -> corner badge + label
        cx, cz = x0 + 0.075, z1 - 0.075
        mark(1, cx, cz)
        ax.text(cx + R + 0.025, cz - 0.002, "whole system", ha="left", va="center", color=G.INK, fontsize=13,
                fontfamily="DejaVu Sans", zorder=21)
    th = (Hp + K) / 2; mark(2, th[0] - 0.02, th[1] + 0.11)                 # hip / thigh: the rising model
    lk = np.array(G.M["B"]) * 0.45 + np.array(G.W(Q, phi, G.M["c2"])) * 0.55
    mark(3, lk[0] + 0.07, lk[1] - 0.05)                                    # rail + link + seat
    if lang == "zh":
        mark(4, 0.60, 0.29)                                                # base / housing / bed fixing / post
    else:                                                                  # en (by speaker): 3 = mechanism + structure
        mark(3, 0.60, 0.29)
        cx, cz = x0 + 0.075, z1 - 0.075 - 2.4 * R                          # 5 = products and next version
        mark(5, cx, cz)
        ax.text(cx + R + 0.025, cz - 0.002, "products, next version", ha="left", va="center", color=G.INK, fontsize=13,
                fontfamily="DejaVu Sans", zorder=21)
    if lang == "zh":
        mark(5, BAR["x"] + 0.11, BAR["z"] + 0.05)                          # grip switch + bar sensor
        mark(5, foot_s[0] + 0.16, 0.075, r=0.036, fs=15)                    # footplate sensor
        mark(5, 0.035, 0.475, r=0.036, fs=15)       # seat sensor
    else:                                                                  # en: each 5 sits right next to its sensor
        mark(4, grip_s[0] + 0.026 + R + 0.012, grip_s[1])                  # 4 = sensing and control: grip switch
        mark(4, foot_s[0] + 0.018 + 0.036 + 0.012, foot_s[1] + 0.012, r=0.036, fs=15)   # footplate sensor
        mark(4, seat_s[0] - 0.018 - 0.036 - 0.012, seat_s[1], r=0.036, fs=15)            # seat sensor
    fig.savefig(path, facecolor=G.BG); plt.close(fig)
    print(path, "frame", k, "seat Q", Q, "phi", round(phi, 1))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--lang", choices=["zh", "en", "both"], default="both"); ap.add_argument("--frame", type=int)
    a = ap.parse_args()
    for lg in (["zh", "en"] if a.lang == "both" else [a.lang]):
        main(os.path.join(HERE, "team_roles.png" if lg == "zh" else "team_roles_en.png"), a.frame, lg)
