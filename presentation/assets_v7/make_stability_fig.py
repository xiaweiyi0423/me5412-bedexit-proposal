"""Stability slide figure (top view): support polygon of the base, frame centre of mass, and for each tipping case the point
where the total ground reaction acts on the base (resultant / centre of pressure).

Data (nothing hard-coded except drawing positions):
  model/calc_v13/seat_1dof/parts.json   "tipping" (margins per case, floor-push thresholds, anchor force, base, device mass + CoM)
                                        "housing" (top_z, x extent)
  model/calc_v13/seat_1dof/handrail.json "bar" (bar x and height z)
  model/calc_v13/seat_1dof/page.json     layout Y (housing walls, seat half-width), seat x, seat travel
Resultant points: parts.json gives only edge distances. x = rear edge + margin_rear; y = head-side edge - margin_side (the side
margin is the head-side one in every case). The script re-derives the same points from the load positions used in
model/calc_v13/seat_1dof_v5_checks.py tipping() (seat rear edge (0.01, 0), bar (bar x, 0.10)) and stops if they differ by > 2 mm.
Floor push toward the head side at the threshold: the push is horizontal along +y at bar height, so the resultant keeps the
frame CoM's x and moves in y until it reaches the head-side edge (that is the definition of the threshold).
Usage: python3 presentation/assets_v7/make_stability_fig.py  ->  presentation/assets_v7/stability_top.png
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Polygon
from matplotlib.lines import Line2D

WQY = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(WQY): font_manager.fontManager.addfont(WQY)
plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA = os.path.join(ROOT, "model/calc_v13/seat_1dof")
P = json.load(open(os.path.join(DATA, "parts.json"))); T = P["tipping"]; HS = P["housing"]
BAR = json.load(open(os.path.join(DATA, "handrail.json")))["bar"]
PG = json.load(open(os.path.join(DATA, "page.json"))); Y = PG["layout"]["Y"]; SX = PG["consts"]["seat_x"]; DX = PG["mech"]["travel"]["dx"]

# palette from presentation/animations/make_seat_gif.py
INK = "#18202A"; MUTED = "#8C96A1"; BED = "#D7DBE1"; MAT = "#E9ECF0"; DEV = "#C3C9D1"; STEEL = "#5B6B7C"; STEEL2 = "#AEB6C0"
SEAT = "#E09A3A"; FOAM_R = "#E7B66F"; BG = "#FBFAF6"; ACC = "#B4620A"; RED = "#C2412D"; GOOD = "#2F7A55"; BODY = "#D9C8B4"

B = T["base"]; X0, X1 = B["x"]; YO, YH = B["y"]; COM = B["device_com"]; MDEV = B["device_kg"]; G = 9.81

# ---- resultant points of the on-platform cases, from the margins in parts.json --------------------------------------------
K_SIT100, K_HANG, K_SIT45 = "100 kg 猛坐座板后缘（1.5 倍体重）", "100 kg 整个挂在扶手横杆上（人在台上）", "45 kg 猛坐后缘"
LOADS = {K_SIT100: (1.5 * 100, 0.01, 0.0), K_HANG: (100.0, BAR["x"], 0.10), K_SIT45: (1.5 * 45, 0.01, 0.0)}   # as in v5_checks tipping()
pts = {}
for k, (m, xl, yl) in LOADS.items():
    t = T[k]; px = X0 + t["margin_rear_cm"] / 100; py = YH - t["margin_side_cm"] / 100
    fx = (m * xl + MDEV * COM[0]) / (m + MDEV); fy = (m * yl + MDEV * COM[1]) / (m + MDEV)    # cross-check with the load model
    assert abs(px - fx) < 0.002 and abs(py - fy) < 0.002, (k, px, py, fx, fy)
    assert abs((X1 - px) * 100 - t["margin_front_cm"]) < 0.2 and min(YH - py, py - YO) * 100 - t["margin_side_cm"] < 0.2
    assert min(px - X0, X1 - px, YH - py, py - YO) > 0, k                                       # inside the polygon
    pts[k] = (px, py)
FLOOR = T["人站在地上推拉横杆（只有台架自重）"]; F_HEAD = FLOOR["push_to_head_side_N"]
assert F_HEAD == T["结论"]["min_tip_force_N"]
assert abs(MDEV * G * (YH - COM[1]) / BAR["z"] - F_HEAD) < 1.0                                  # threshold: resultant on the head edge
TIP = (COM[0], YH)
ANCHOR = next(v["anchor_N"] for k, v in T.items() if k.startswith("固定件拉力（ADA"))


# ---- labels ---------------------------------------------------------------------------------------------------------------
mr = lambda k: f"{T[k]['margin_rear_cm']:.0f}"; ms_ = lambda k: f"{T[k]['margin_side_cm']:.0f}"
LAB = dict(
    zh=dict(bed="床", foot="← 床尾", head="床头", pillow="枕头", housing=f"机构箱\n顶高 {HS['top_z']:.2f} m", seat="座板", seat_top="座板升到顶",
            bar=f"扶手横杆  高 {BAR['z']:.2f} m", walk="站起后走向床尾", com=f"台架质心（约 {MDEV:.0f} kg）",
            sit100=f"100 kg 猛坐后缘\n离后边 {mr(K_SIT100)} cm", sit45=f"45 kg 猛坐后缘\n离后边 {mr(K_SIT45)} cm",
            hang=f"100 kg 挂在横杆上\n离床头侧边 {ms_(K_HANG)} cm", push=f"人站在地上，往床头推 {F_HEAD} N", tip="合力压到边上\n= 开始翻",
            anchor=f"固定到床\n{ANCHOR} N", lg=["合力作用点：人在台上", "合力作用点：翻倒临界", "台架质心（只有台架自重）", "底座 = 支撑多边形", "和床固定的点"]),
    en=dict(bed="bed", foot="← foot end", head="bed head side", pillow="pillow", housing=f"housing\ntop {HS['top_z']:.2f} m", seat="seat", seat_top="seat at top",
            bar=f"L-handrail bar, h {BAR['z']:.2f} m", walk="walks off toward\nfoot end", com=f"frame CoM (≈{MDEV:.0f} kg)",
            sit100=f"100 kg sits hard on rear\nedge (1.5×BW): {mr(K_SIT100)} cm to edge", sit45=f"45 kg sits hard on rear\nedge (1.5×BW): {mr(K_SIT45)} cm to edge",
            hang=f"100 kg hangs on bar\n(on platform): {ms_(K_HANG)} cm to\nhead-side edge", push=f"pushes bar from floor: tips at {F_HEAD} N",
            tip="resultant on the edge\n= starts to tip", anchor=f"fixed to bed\n{ANCHOR} N",
            lg=["ground reaction point, on platform", "ground reaction point, tipping", "frame CoM (frame weight only)",
                "base = support polygon", "anchor to bed"]))

def draw(lang, out):
    S = LAB[lang]; en = lang == "en"
    # horizontal = along the bed (y, head side to the right), vertical = away from the bed (x, down)
    YL, YR, XT, XB = -0.92, 1.16, -0.30, 0.98
    W_IN = 9.6; H_IN = W_IN * (XB - XT) / (YR - YL)
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=200); ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(YL, YR); ax.set_ylim(XB, XT); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((YL, XT), YR - YL, XB - XT, color=BG, zorder=0))
    R = lambda y0, y1, x0, x1, **k: ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, **k))
    FS = 17.0 if not en else 15.5
    # bed (only the part next to the frame) and pillow
    R(YL - 0.1, 0.80, XT - 0.1, 0.0, facecolor=MAT, edgecolor=MUTED, lw=1.2, zorder=1)
    R(0.56, 0.78, -0.27, -0.04, facecolor="#FFFFFF", edgecolor=MUTED, lw=1, zorder=2)
    ax.text(0.67, -0.155, S["pillow"], fontsize=FS - 2, color="#6B7480", ha="center", va="center", zorder=3, rotation=90 if en else 0)
    ax.text(-0.62, -0.13, S["bed"], fontsize=FS + 3, color="#6B7480", ha="center", va="center")
    ax.text(0.92, -0.12, S["head"] if en else "床\n头", fontsize=FS, color=INK, ha="center", va="center", linespacing=1.1, rotation=90 if en else 0)
    ax.text(YL + 0.02, -0.255, S["foot"], fontsize=FS, color=INK, ha="left", va="center")
    # support polygon = base outline
    R(YO, YH, X0, X1, facecolor="#EEF3EF", edgecolor=INK, lw=2.6, zorder=2)
    # housing (head side), seat (flush, and at the top), L handrail
    R(Y["wall_in"], Y["wall_out"], HS["x"][0], HS["x"][1], facecolor=STEEL2, edgecolor=STEEL, lw=1.4, zorder=3)
    ax.annotate(S["housing"], xy=(Y["wall_out"], 0.47), xytext=(0.47, 0.43), fontsize=FS - 1, color=INK, va="center", linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1), zorder=9)
    R(-Y["seat"], Y["seat"], SX[0], SX[1], facecolor=FOAM_R, edgecolor=ACC, lw=1.4, zorder=3, alpha=0.75)
    R(-Y["seat"], Y["seat"], SX[0] + DX, SX[1] + DX, facecolor="none", edgecolor=ACC, lw=1.3, ls=":", zorder=3)
    ax.text(-0.205, (SX[0] + SX[1]) / 2 - 0.01, S["seat"], fontsize=FS - 1, color=INK, ha="left", va="center", zorder=4)
    ax.text(-0.205, SX[1] + DX - 0.03, S["seat_top"], fontsize=FS - 3, color=ACC, ha="left", va="center", zorder=4)
    YB0, YB1 = -0.05, 0.30                                       # bar drawn as in make_seat_gif.render_top
    ax.plot([YB1, YB0], [BAR["x"], BAR["x"]], color=INK, lw=7, solid_capstyle="round", zorder=5)
    ax.add_patch(Circle((YB1, BAR["x"]), 0.03, color=INK, zorder=6))
    ax.text(0.10, BAR["x"] - 0.035, S["bar"], fontsize=FS - 2, color=INK, ha="center", va="bottom", zorder=9)
    # walking route (as on the old top view): off the open side toward the foot end
    ax.add_patch(FancyArrowPatch((YO - 0.02, 0.74), (-0.76, 0.66), connectionstyle="arc3,rad=-0.25", arrowstyle="-|>", mutation_scale=18,
                                 lw=1.8, color=MUTED, ls="--", zorder=4))
    ax.text((YO - 0.76) / 2 - (0.08 if en else 0.02), 0.87, S["walk"], fontsize=FS - 2, color="#6B7480", ha="center", va="center", zorder=4, linespacing=1.1)
    # frame CoM
    ax.plot(COM[1], COM[0], marker="o", ms=15, mfc="#FFFFFF", mec=INK, mew=2.2, zorder=7)
    ax.plot(COM[1], COM[0], marker="+", ms=15, mec=INK, mew=2.2, zorder=8)
    ax.annotate(S["com"], xy=(COM[1] - 0.01, COM[0] + 0.015), xytext=(0.05, 0.40), fontsize=FS - 1, color=INK, ha="center", va="top",
                arrowprops=dict(arrowstyle="-", color=INK, lw=1, shrinkB=8), zorder=9,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="#FFFFFF", edgecolor="none", alpha=0.85))
    # platform cases (green, inside)
    lab = {K_SIT100: (S["sit100"], 0.10), K_SIT45: (S["sit45"], 0.31), K_HANG: (S["hang"], 0.53)}
    for k, (px, py) in pts.items():
        ax.plot(py, px, marker="o", ms=15, mfc=GOOD, mec="#FFFFFF", mew=2, zorder=8)
        t, lx = lab[k]
        ax.annotate(t, xy=(py, px), xytext=(YO - 0.05, lx), fontsize=FS - 1, color=GOOD, ha="right", va="center", linespacing=1.2,
                    arrowprops=dict(arrowstyle="-", color=GOOD, lw=1.2, shrinkB=9), zorder=9)
    # floor push toward the head side: external force at the bar; the resultant moves from the CoM to the head-side edge
    ax.add_patch(FancyArrowPatch((0.0, 0.745), (0.26, 0.745), arrowstyle="-|>", mutation_scale=20, lw=3, color=RED, zorder=7))
    ax.text(-0.02, X1 + 0.03, S["push"], fontsize=FS - 1, color=RED, ha="center", va="top", zorder=9, fontweight="bold")
    ax.add_patch(FancyArrowPatch((COM[1] + 0.03, COM[0]), (TIP[1] - 0.03, TIP[0]), arrowstyle="-|>", mutation_scale=16, lw=1.8, color=RED,
                                 ls=(0, (3, 2)), zorder=7))
    ax.plot(TIP[1], TIP[0], marker="o", ms=17, mfc=RED, mec="#FFFFFF", mew=2, zorder=9)
    ax.annotate(S["tip"], xy=(TIP[1] + 0.02, TIP[0]), xytext=(0.47, 0.17), fontsize=FS - 1, color=RED, va="center", fontweight="bold",
                linespacing=1.15, arrowprops=dict(arrowstyle="-", color=RED, lw=1.2), zorder=9)
    # anchors to the bed (rear edge, both ends, as in v5_checks tipping())
    for yy in (YO, YH):
        ax.add_patch(Rectangle((yy - 0.025, X0 - 0.025), 0.05, 0.05, facecolor=ACC, edgecolor="#FFFFFF", lw=1.5, zorder=8))
    ax.text(YO - 0.04, X0 - 0.03, S["anchor"], fontsize=FS - 1, color=ACC, ha="right", va="bottom", zorder=9, linespacing=1.15, fontweight="bold")
    # legend
    H = [Line2D([], [], ls="", marker="o", ms=12, mfc=GOOD, mec="#FFFFFF"), Line2D([], [], ls="", marker="o", ms=12, mfc=RED, mec="#FFFFFF"),
         Line2D([], [], ls="", marker="o", ms=12, mfc="#FFFFFF", mec=INK, mew=2), Rectangle((0, 0), 1, 1, facecolor="#EEF3EF", edgecolor=INK, lw=2),
         Line2D([], [], ls="", marker="s", ms=10, mfc=ACC, mec="#FFFFFF")]
    lg = ax.legend(handles=H, labels=S["lg"], loc="lower right", bbox_to_anchor=(1.0, 0.0), fontsize=FS - 3.5, frameon=True, framealpha=0.95,
                   edgecolor="#E2DED5", handletextpad=0.5, borderpad=0.5, labelspacing=0.4)
    lg.set_zorder(10)
    fig.savefig(out, facecolor=BG); plt.close(fig)
    print(out, f"{W_IN * 200:.0f}x{H_IN * 200:.0f}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--lang", choices=["zh", "en", "both"], default="both"); a = ap.parse_args()
    for lg_ in (["zh", "en"] if a.lang == "both" else [a.lang]):
        draw(lg_, os.path.join(HERE, "stability_top.png" if lg_ == "zh" else "stability_top_en.png"))
    print({k[:8]: tuple(round(v, 3) for v in p) for k, p in pts.items()}, "tip", TIP, "anchor", ANCHOR)
