"""Mechanism views without the human body (v5.4): side section, front and top views, 3-D isometric, motion GIF.

Geometry from model/calc_v13/seat_1dof/page.json (slider mechanism, v5_checks layout). Schematic, not CAD: parts are
drawn at their computed positions with assumed section sizes. Coordinates: x out from the bed edge, y along the bed
(+ = head side), z up; bed top 0.42 m.
Outputs (this folder): mech_side.png, mech_views.png (front + top), mech_3d.png, mech_motion.gif
"""
import math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
import make_seat_gif as G

HERE = os.path.dirname(os.path.abspath(__file__))
M, L, BAR, D = G.M, G.L, G.BAR, G.D
Y = L["Y"]; GAP = L["rail_gap"]; SPAN = L["carriage_span"]; HALF = G.HALF
INK, STEEL, STEEL2, BG, ACC = G.INK, G.STEEL, G.STEEL2, G.BG, G.ACC
R1 = (np.array(M["rail_lo"]), np.array(M["rail_hi"])); R2 = (np.array(L["rail2"][0]), np.array(L["rail2"][1]))
E_ = (R1[1] - R1[0]) / np.hypot(*(R1[1] - R1[0])); NF = (R2[0] - R1[0]) / GAP          # rail direction (up), in-plane normal to rail 2
B = np.array(M["B"]); C1, C2 = np.array(M["c1"]), np.array(M["c2"]); FR = M["frames"]
W = G.W
def pins(f): return W(f["Q"], f["phi"], C1), W(f["Q"], f["phi"], C2)
def seat_parts(f):
    Q, ph = f["Q"], f["phi"]; w = lambda pts: np.array([W(Q, ph, p) for p in pts])
    rear = w([(-HALF, 0), (-0.02, 0), (-0.02, -0.05), (-HALF, -0.05)]); front = w([(-0.02, 0), (HALF, 0), (HALF, -0.08), (-0.02, -0.08)])
    under = [W(Q, ph, (-HALF + 0.045, -0.062)), W(Q, ph, (-0.02, -0.062)), W(Q, ph, (-0.02, -0.092)), W(Q, ph, (HALF - 0.03, -0.092))]
    P1, P2 = pins(f); br = np.array(under + [P1, P2]); c = br.mean(0); br = br[np.argsort(np.arctan2(br[:, 1] - c[1], br[:, 0] - c[0]))]
    return rear, front, br, P1, P2
def carriages(P1):
    out = []
    for off in (0.0, GAP):
        for s_ in (0.0, SPAN):
            c = P1 + s_ * E_ + off * NF; out.append(np.array([c - 0.03 * E_ - 0.012 * NF, c + 0.03 * E_ - 0.012 * NF, c + 0.03 * E_ + 0.012 * NF, c - 0.03 * E_ + 0.012 * NF]))
    return out
def plate(P1):
    a, b = -0.04, SPAN + 0.04
    return np.array([P1 + a * E_ - 0.02 * NF, P1 + b * E_ - 0.02 * NF, P1 + b * E_ + (GAP + 0.02) * NF, P1 + a * E_ + (GAP + 0.02) * NF])
SCREW = (R1[0] + 0.5 * GAP * NF + 0.03 * E_, R1[1] + 0.5 * GAP * NF - 0.06 * E_)
F0, FM, F1 = FR[0], FR[len(FR) // 2], FR[-1]

# ---------------------------------------------------------------- side section
def side(ax, f, ghosts=(), labels=True, z1=1.08):
    ax.clear(); x0, x1 = -0.42, 1.0; ax.set_xlim(x0, x1); ax.set_ylim(-0.03, z1); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((x0, -0.03), x1 - x0, z1 + 0.03, color=BG, zorder=0)); ax.plot([x0, x1], [0, 0], color=G.MUTED, lw=1.5)
    ax.add_patch(Rectangle((x0, 0), -x0, 0.36, color=G.BED, zorder=1)); ax.add_patch(Rectangle((x0, 0.36), -x0, 0.06, color=G.MAT, zorder=1))
    ax.text(x0 / 2, 0.18, "床", ha="center", va="center", fontsize=15, color="#6B7480")
    ax.add_patch(Rectangle((0.03, 0), 0.75, 0.035, color=G.DEV, zorder=2))                                   # base beam
    ax.add_patch(Rectangle((0.20, 0.035), 0.42, 0.012, color="#9AA3AD", zorder=2))                           # footplate
    ax.add_patch(Rectangle((-0.06, 0.05), 0.09, 0.07, facecolor="#D6DAE0", edgecolor=STEEL, lw=1.2, zorder=2))  # bed-leg clamp (schematic)
    ax.add_patch(Polygon(L["housing"], closed=True, facecolor=STEEL2, edgecolor=STEEL, lw=1.4, ls="--", alpha=0.18, zorder=2))
    for a, b in (R1, R2): ax.plot([a[0], b[0]], [a[1], b[1]], color=STEEL, lw=5, solid_capstyle="butt", zorder=3)
    ax.plot([SCREW[0][0], SCREW[1][0]], [SCREW[0][1], SCREW[1][1]], color="#7A5A2E", lw=2.2, ls=(0, (6, 2)), zorder=3)
    ax.add_patch(Polygon(L["motor"], closed=True, facecolor="#3F4A57", edgecolor=INK, lw=1, zorder=4))
    ax.plot([BAR["x"], BAR["x"]], [0.035, BAR["z"]], color=STEEL, lw=6, alpha=.6, zorder=2, solid_capstyle="round")
    ax.add_patch(Circle((BAR["x"], BAR["z"]), 0.022, color=INK, zorder=7))
    for g in ghosts:                                                                                          # other positions, faint
        rear, front, br, P1, P2 = seat_parts(g)
        for poly, col in ((br, STEEL2), (rear, G.FOAM_R), (front, G.FOAM_F)): ax.add_patch(Polygon(poly, closed=True, color=col, alpha=0.30, zorder=3))
        ax.plot([B[0], P2[0]], [B[1], P2[1]], color=STEEL, lw=4, alpha=0.3, zorder=3)
    Qs = np.array([fr["Q"] for fr in FR]); ax.plot(Qs[:, 0], Qs[:, 1], color=ACC, lw=1.5, ls=":", zorder=6)
    rear, front, br, P1, P2 = seat_parts(f)
    ax.add_patch(Polygon(plate(P1), closed=True, facecolor="#C9CED6", edgecolor=STEEL, lw=1, alpha=0.55, zorder=4))
    for c in carriages(P1): ax.add_patch(Polygon(c, closed=True, facecolor=INK, edgecolor=INK, zorder=5))
    ax.add_patch(Polygon(br, closed=True, color=STEEL2, alpha=.9, zorder=5))
    ax.add_patch(Polygon(rear, closed=True, color=G.FOAM_R, zorder=6)); ax.add_patch(Polygon(front, closed=True, color=G.FOAM_F, zorder=6))
    ax.plot([B[0], P2[0]], [B[1], P2[1]], color=STEEL, lw=6, zorder=5, solid_capstyle="round")
    for p in (P1, P2, B): ax.add_patch(Circle(p, 0.011, facecolor="#FFFFFF", edgecolor=INK, lw=1.6, zorder=7))
    nut = P1 + 0.5 * GAP * NF + 0.075 * E_; ax.add_patch(Circle(nut, 0.016, facecolor="#7A5A2E", edgecolor=INK, lw=1, zorder=6))
    if not labels: return P1, P2
    items = [((W(f["Q"], f["phi"], (-0.05, -0.02))), "分区坐垫：后硬前软"), (W(f["Q"], f["phi"], (0.03, -0.085)), "座板支架（从机构箱的毛刷竖槽伸出）"),
             (P1, "铰点 1：装在滑块板上"), (P2, "铰点 2"), ((B + P2) / 2, "倾角连杆"), (B, "连杆底座铰点"),
             (R1[0] + 0.75 * (R1[1] - R1[0]), "导轨 1"), (R2[0] + 0.25 * (R2[1] - R2[0]), "导轨 2（同一侧板上，相距 150 mm）"),
             (carriages(P1)[1].mean(0), "4 个滑块 + 滑块板"), (nut, "丝杠螺母（浮动接头）"), (SCREW[0] + 0.55 * (SCREW[1] - SCREW[0]), "滚珠丝杠"),
             (np.array(L["motor"]).mean(0), "电机 + 失电制动器（皮带传动）"), (np.array([BAR["x"], 0.55]), "L 形扶手立柱"),
             (np.array([0.40, 0.045]), "踏板（下有测力单元）"), (np.array([0.0, 0.085]), "固定件：锁在床腿"), (np.array([0.6, 0.02]), "底座")]
    off = [(-0.10, 0.10), (-0.13, -0.07), (-0.10, 0.02), (-0.09, -0.06), (0.03, -0.07), (0.06, -0.05), (-0.07, 0.04), (0.07, 0.0),
           (0.02, -0.15), (0.10, 0.07), (0.06, 0.03), (0.08, 0.05), (0.06, 0.0), (0.0, -0.035), (-0.08, 0.03), (0.08, 0.035)]
    for i, ((xy, txt), (dx, dz)) in enumerate(zip(items, off), 1):
        tx, tz = xy[0] + dx, xy[1] + dz
        ax.plot([xy[0], tx], [xy[1], tz], color=INK, lw=0.9, zorder=8)
        ax.add_patch(Circle((tx, tz), 0.021, facecolor="#E3A92E", edgecolor=INK, lw=1, zorder=9)); ax.text(tx, tz, str(i), ha="center", va="center", fontsize=10, fontweight="bold", zorder=10)
    return items

def render_side(path):
    fig = plt.figure(figsize=(12.8, 9.6), dpi=130); ax = fig.add_axes([0.0, 0.0, 0.70, 1.0])
    items = side(ax, F0, ghosts=(FM, F1))
    tx = fig.add_axes([0.70, 0.0, 0.30, 1.0]); tx.axis("off"); tx.set_xlim(0, 1); tx.set_ylim(0, 1)
    tx.text(0.02, 0.97, "侧视剖面（床头一侧机构箱剖开）", fontsize=15, fontweight="bold", color=INK, va="top")
    tx.text(0.02, 0.925, "实色 = 和床齐平；浅色 = 行程中段和最高位\n橙色点线 = 座板中心的轨迹", fontsize=11.5, color="#5B6B7C", va="top", linespacing=1.4)
    for i, (_, t) in enumerate(items, 1): tx.text(0.02, 0.84 - 0.042 * i, f"{i:>2}  {t}", fontsize=12.5, color=INK, va="top")
    tv = M["travel"]
    tx.text(0.02, 0.105, f"导轨与竖直成 {M['rail_angle_deg']:.0f}°，丝杠行程 {M['stroke'] * 1000:.0f} mm\n座板中心前移 {tv['dx'] * 100:.1f} cm、上升 {tv['dz'] * 100:.1f} cm\n前倾先增后减，最大 {M['phi_run_max']:.1f}°，到顶 {M['phi_end']:.0f}°",
            fontsize=12, color=ACC, va="top", linespacing=1.5)
    tx.text(0.02, 0.01, "二维模型画出的示意，不是 CAD", fontsize=10.5, color="#8C96A1")
    fig.savefig(path, facecolor=BG); plt.close(fig)

# ---------------------------------------------------------------- front and top views
def render_views(path):
    fig, (af, at) = plt.subplots(1, 2, figsize=(14.5, 6.6), dpi=130, gridspec_kw=dict(width_ratios=[1.05, 1]))
    for ax in (af, at): ax.set_aspect("equal"); ax.axis("off")
    # front view: looking at the device from the room (from +x toward the bed); y horizontal (head side right), z up
    ax = af; ax.set_xlim(-0.75, 0.75); ax.set_ylim(-0.05, 1.12); ax.add_patch(Rectangle((-0.75, -0.05), 1.5, 1.17, color=BG, zorder=0))
    ax.add_patch(Rectangle((-0.75, 0.0), 1.5, 0.42, color=G.MAT, alpha=0.6, zorder=1)); ax.text(-0.70, 0.38, "床（在后面）", fontsize=11, color="#6B7480", va="top")
    ax.plot([-0.75, 0.75], [0, 0], color=G.MUTED, lw=1.5)
    for y0 in (Y["base_open"], Y["base_head"] - 0.04): ax.add_patch(Rectangle((y0, 0), 0.04, 0.035, color=STEEL, zorder=3))
    ax.add_patch(Rectangle((Y["base_open"], 0.0), Y["base_head"] - Y["base_open"], 0.012, color=G.DEV, zorder=2))
    ax.add_patch(Rectangle((-0.22, 0.035), 0.44, 0.012, color="#9AA3AD", zorder=3))
    zH = max(p[1] for p in L["housing"]); ax.add_patch(Rectangle((Y["wall_in"], 0.04), Y["wall_out"] - Y["wall_in"], zH - 0.04, facecolor=STEEL2, edgecolor=STEEL, lw=1.4, alpha=0.5, zorder=3))
    ax.plot([Y["rail"], Y["rail"]], [R1[0][1], R1[1][1]], color=INK, lw=4, zorder=4)
    ax.plot([Y["wall_in"], Y["wall_in"]], [0.30, 0.70], color="#E3A92E", lw=3, ls=(0, (2, 2)), zorder=5)
    for f, a in ((F1, 0.35), (F0, 1.0)):
        z = f["Q"][1]; ax.add_patch(Rectangle((-Y["seat"], z - 0.09), 2 * Y["seat"], 0.09, facecolor=G.FOAM_F, edgecolor=ACC, lw=1.2, alpha=a, zorder=6))
        ax.add_patch(Rectangle((-0.18, z - 0.13), Y["wall_in"] + 0.06 + 0.18, 0.04, facecolor=STEEL2, edgecolor=STEEL, lw=1, alpha=a, zorder=5))
    ax.plot([0.30, 0.30], [0.035, BAR["z"]], color=STEEL, lw=7, zorder=4); ax.plot([0.30, -0.05], [BAR["z"], BAR["z"]], color=INK, lw=8, solid_capstyle="round", zorder=4)
    lab = [((0.0, 0.40), "座板（齐平）", (-0.70, 0.62)), ((0.0, 0.67), "最高位（浅色）", (-0.70, 0.80)), ((-0.05, F0["Q"][1] - 0.11), "悬臂托架", (-0.70, 0.18)),
           ((Y["wall_in"], 0.55), "毛刷竖槽", (0.42, 0.50)), ((Y["rail"], 0.55), "导轨所在侧板", (0.42, 0.62)), (((Y["wall_in"] + Y["wall_out"]) / 2, zH - 0.02), "机构箱 11 cm 厚", (0.42, 0.88)),
           ((0.12, BAR["z"]), "横杆（握把开关）", (-0.70, 1.03)), ((0.30, 0.70), "立柱", (0.42, 0.74)), ((0.0, 0.04), "踏板", (-0.70, 0.08))]
    for xy, t, (tx, tz) in lab: ax.annotate(t, xy=xy, xytext=(tx, tz), fontsize=11.5, color=INK, arrowprops=dict(arrowstyle="-", color=G.MUTED, lw=0.9), zorder=9)
    ax.text(0.0, 1.10, "前视（从房间看向床）", fontsize=14, fontweight="bold", ha="center", va="top")
    ax.text(-0.70, -0.04, "← 床尾一侧敞开", fontsize=11.5, color=INK); ax.text(0.72, -0.04, "床头 →", fontsize=11.5, color=INK, ha="right")
    # top view
    ax = at; ax.set_xlim(-0.55, 0.62); ax.set_ylim(0.92, -0.30); ax.add_patch(Rectangle((-0.55, -0.30), 1.17, 1.22, color=BG, zorder=0))
    R = lambda y0, y1, x0, x1, **k: ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, **k))
    R(-0.55, 0.62, -0.30, 0.0, color=G.MAT, zorder=1); ax.text(-0.52, -0.22, "床", fontsize=12, color="#6B7480")
    R(Y["base_open"], Y["base_head"], 0.03, 0.78, facecolor="none", edgecolor=STEEL, lw=1.4, ls="--", zorder=2)
    R(-0.22, 0.22, 0.20, 0.62, color="#C3C9D1", alpha=0.6, zorder=2)
    Hx = [p[0] for p in L["housing"]]; R(Y["wall_in"], Y["wall_out"], min(Hx), max(Hx), facecolor=STEEL2, edgecolor=STEEL, lw=1.4, zorder=3)
    ax.plot([Y["rail"], Y["rail"]], [R1[0][0], R1[1][0]], color=INK, lw=3, zorder=4); ax.plot([Y["rail"], Y["rail"]], [R2[0][0], R2[1][0]], color=INK, lw=3, zorder=4)
    sx = D["consts"]["seat_x"]; dx = M["travel"]["dx"]
    R(-Y["seat"], Y["seat"], sx[0], sx[1], facecolor=G.FOAM_R, edgecolor=ACC, lw=1.4, zorder=5)
    R(-Y["seat"], Y["seat"], sx[0] + dx, sx[1] + dx, facecolor="none", edgecolor=ACC, lw=1.4, ls=":", zorder=5)
    ax.plot([0.30, -0.05], [BAR["x"], BAR["x"]], color=INK, lw=7, solid_capstyle="round", zorder=6); ax.add_patch(Circle((0.30, BAR["x"]), 0.03, color=INK, zorder=7))
    lab = [((0.0, 0.05), "座板（齐平）", (-0.52, 0.10)), ((0.0, 0.25), "最高位（前移 18.5 cm）", (-0.52, 0.30)), ((Y["wall_out"], 0.30), "机构箱", (0.42, 0.10)),
           ((Y["rail"], 0.25), "两根导轨（俯视重叠）", (0.42, 0.42)), ((0.0, 0.50), "踏板", (-0.52, 0.52)), ((0.10, BAR["x"]), "横杆", (-0.52, 0.72)),
           ((Y["base_open"], 0.70), "底座（虚线）", (-0.52, 0.86))]
    for xy, t, (tx, tz) in lab: ax.annotate(t, xy=xy, xytext=(tx, tz), fontsize=11.5, color=INK, arrowprops=dict(arrowstyle="-", color=G.MUTED, lw=0.9), zorder=9)
    ax.text(0.04, -0.27, "俯视", fontsize=14, fontweight="bold", ha="center", va="top")
    fig.tight_layout(); fig.savefig(path, facecolor=BG); plt.close(fig)

# ---------------------------------------------------------------- 3-D isometric
def prism(P, y0, y1):
    """extrude a sagittal polygon P (x, z) between y0 and y1 -> list of 3-D faces."""
    P = np.asarray(P); a = [(x, y0, z) for x, z in P]; b = [(x, y1, z) for x, z in P]; F = [a, b]
    for i in range(len(P)): j = (i + 1) % len(P); F.append([a[i], a[j], b[j], b[i]])
    return F
def box(x0, x1, y0, y1, z0, z1): return prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)
def thick(a, b, w):
    a, b = np.asarray(a), np.asarray(b); d = (b - a) / np.hypot(*(b - a)); n = np.array([-d[1], d[0]]) * w / 2
    return [a + n, b + n, b - n, a - n]
def add(ax, faces, fc, ec=None, alpha=1.0, lw=0.4):
    ax.add_collection3d(Poly3DCollection(faces, facecolors=fc, edgecolors=ec or fc, linewidths=lw, alpha=alpha))

def scene3d(ax, f, title):
    ax.set_axis_off()
    add(ax, box(-0.32, 0.0, -0.55, 0.55, 0.0, 0.42), "#E9ECF0", "#C9CED6", 0.45)                      # bed
    add(ax, box(0.03, 0.78, Y["base_open"], Y["base_open"] + 0.04, 0, 0.035), STEEL); add(ax, box(0.03, 0.78, Y["base_head"] - 0.04, Y["base_head"], 0, 0.035), STEEL)
    add(ax, box(0.03, 0.07, Y["base_open"], Y["base_head"], 0, 0.035), STEEL); add(ax, box(0.74, 0.78, Y["base_open"], Y["base_head"], 0, 0.035), STEEL)
    add(ax, box(0.20, 0.62, -0.22, 0.22, 0.035, 0.047), "#9AA3AD")                                         # footplate
    add(ax, prism(L["housing"], Y["wall_in"], Y["wall_out"]), "#AEB6C0", "#5B6B7C", 0.13, 0.6)          # housing, see-through
    for a, b in (R1, R2): add(ax, prism(thick(a, b, 0.02), Y["rail"] - 0.012, Y["rail"] + 0.012), "#3F4A57")
    add(ax, prism(thick(*SCREW, 0.012), Y["rail"] - 0.035, Y["rail"] - 0.023), "#7A5A2E")
    add(ax, prism(L["motor"], Y["rail"] - 0.05, Y["rail"] + 0.03), "#2B333D")
    rear, front, br, P1, P2 = seat_parts(f)
    add(ax, prism(plate(P1), Y["rail"] - 0.03, Y["rail"] - 0.015), "#C9CED6", "#5B6B7C")
    for c in carriages(P1): add(ax, prism(c, Y["rail"] - 0.016, Y["rail"] + 0.016), "#18202A")
    add(ax, prism(thick(B, P2, 0.03), Y["link"] - 0.012, Y["link"] + 0.012), "#5B6B7C")
    add(ax, prism(br, Y["wall_in"] - 0.02, Y["rail"] - 0.03), "#AEB6C0", "#5B6B7C")                    # bracket through the slot
    Q, ph = f["Q"], f["phi"]
    beam = [W(Q, ph, (-HALF + 0.05, -0.092)), W(Q, ph, (HALF - 0.03, -0.092)), W(Q, ph, (HALF - 0.03, -0.062)), W(Q, ph, (-HALF + 0.05, -0.062))]
    add(ax, prism(beam, -Y["seat"] + 0.03, Y["wall_in"]), "#AEB6C0", "#5B6B7C")                          # cantilever arm under the seat
    add(ax, prism(rear, -Y["seat"], Y["seat"]), G.FOAM_R, "#B4620A", 1.0, 0.3); add(ax, prism(front, -Y["seat"], Y["seat"]), G.FOAM_F, "#B4620A", 1.0, 0.3)
    add(ax, box(BAR["x"] - 0.02, BAR["x"] + 0.02, 0.28, 0.32, 0.035, BAR["z"]), "#5B6B7C")              # post
    add(ax, box(BAR["x"] - 0.02, BAR["x"] + 0.02, -0.05, 0.32, BAR["z"] - 0.02, BAR["z"] + 0.02), "#18202A")
    ax.set_xlim(-0.32, 0.82); ax.set_ylim(-0.55, 0.59); ax.set_zlim(0, 1.0); ax.set_box_aspect((1.14, 1.14, 1.0), zoom=1.25)
    ax.view_init(elev=20, azim=-58); ax.set_title(title, fontsize=15, y=0.97)

def render_3d(path):
    fig = plt.figure(figsize=(15, 7.4), dpi=130)
    for i, (f, t) in enumerate(((F0, "和床齐平（坐上去时）"), (F1, f"升到最高（约 {M['top']:.2f} m，前倾回到约 {M['phi_end']:.0f}°）")), 1):
        ax = fig.add_subplot(1, 2, i, projection="3d", computed_zorder=False); scene3d(ax, f, t)
    fig.text(0.5, 0.04, "床头一侧的机构箱画成半透明：里面是两根导轨、4 个滑块和滑块板、滚珠丝杠、上端的电机和制动器、倾角连杆；座板由悬臂托架从箱子内侧板的竖槽伸出。床尾一侧（左前方）敞开。示意，不是 CAD。",
             ha="center", fontsize=11.5, color=INK, wrap=True)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0.07, wspace=0); fig.savefig(path, facecolor=BG); plt.close(fig)

def render_3d_slide(path):
    """one labelled 3-D view at the flush position, for the mechanism slide."""
    fig = plt.figure(figsize=(11.2, 7.4), dpi=130); ax = fig.add_axes([-0.04, -0.04, 1.08, 1.08], projection="3d", computed_zorder=False)
    scene3d(ax, F0, ""); ax.set_box_aspect((1.14, 1.14, 1.0), zoom=1.12)
    rear, front, br, P1, P2 = seat_parts(F0); Q = F0["Q"]
    mid = lambda a, b, t=0.5: a + t * (b - a)
    lab = [((*mid(R1[0], R1[1], 0.85)[:1], Y["rail"], mid(R1[0], R1[1], 0.85)[1]), "两根导轨（同一侧板）", (-0.10, 0.45, 0.98)),
           ((*plate(P1).mean(0)[:1], Y["rail"] - 0.03, plate(P1).mean(0)[1]), "滑块板 + 4 个滑块", (0.55, 0.62, 0.42)),
           ((*mid(*SCREW, 0.55)[:1], Y["rail"] - 0.03, mid(*SCREW, 0.55)[1]), "滚珠丝杠", (0.82, 0.62, 0.66)),
           ((*np.array(L["motor"]).mean(0)[:1], Y["rail"], np.array(L["motor"]).mean(0)[1]), "电机 + 制动器（皮带）", (0.62, 0.62, 0.80)),
           ((*mid(B, P2)[:1], Y["link"], mid(B, P2)[1]), "倾角连杆", (0.80, 0.50, 0.22)),
           ((Q[0], 0.15, Q[1] - 0.08), "悬臂托架（从竖槽伸出）", (0.20, -0.10, 0.18)),
           ((Q[0] - 0.03, -0.10, Q[1] + 0.01), "分区坐垫", (-0.20, -0.40, 0.62)),
           ((BAR["x"], 0.08, BAR["z"]), "L 形扶手横杆（握把开关）", (0.60, 0.10, 1.14)),
           ((0.40, -0.10, 0.05), "踏板", (0.62, -0.45, 0.12)),
           ((0.10, -0.27, 0.03), "床尾一侧敞开", (0.05, -0.60, 0.02))]
    for (x, y, z), t, (tx, ty, tz) in lab:
        ax.plot([x, tx], [y, ty], [z, tz], color="#8C96A1", lw=0.9, zorder=30)
        ax.text(tx, ty, tz, t, fontsize=13, color=INK, zorder=31, bbox=dict(boxstyle="round,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.85))
    fig.savefig(path, facecolor="#FFFFFF"); plt.close(fig)

def render_gif(path, fps=12):
    fig = plt.figure(figsize=(7.2, 6.4), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); imgs = []
    seq = list(range(len(FR))) + [len(FR) - 1] * 8 + list(range(len(FR) - 1, -1, -1)) + [0] * 8
    for k in seq:
        f = FR[k]; side(ax, f, labels=False, z1=1.02)
        ax.text(-0.40, 0.98, f"座面 {f['Q'][1]:.2f} m · 前倾 {f['phi']:.1f}°", fontsize=14, color=INK, va="top")
        fig.canvas.draw(); imgs.append(Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB"))
    q = [im.quantize(colors=96, method=Image.Quantize.MEDIANCUT) for im in imgs]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True, disposal=1); plt.close(fig)

if __name__ == "__main__":
    render_side(os.path.join(HERE, "mech_side.png")); render_views(os.path.join(HERE, "mech_views.png"))
    render_3d(os.path.join(HERE, "mech_3d.png")); render_3d_slide(os.path.join(HERE, "mech_3d_slide.png")); render_gif(os.path.join(HERE, "mech_motion.gif")); print("done")
