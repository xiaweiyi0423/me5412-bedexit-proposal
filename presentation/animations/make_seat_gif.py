"""Seat-design figures for the slides (side view, drawn from the model, not CAD):
  seat_rise.gif        one user rising with the one-DOF seat (inclined rail + tilt link), zoned cushion contact, L-handrail
  seat_step{1..5}.png  five moments of one use (for the concept slide)
  seat_mech.png        the mechanism at three heights with labels (for the mechanism slide)
  seat_vs_vertical.png the same early-hip user on the vertical lift and on the curved seat at the same moment
Data: model/calc_v13/seat_1dof/page.json (built by seat_1dof_page_data_v5.py).
Usage: python3 make_seat_gif.py
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
from PIL import Image

for f in font_manager.findSystemFonts():
    if "NotoSansCJK" in f and "Regular" in f: font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Noto Sans CJK SC", "DejaVu Sans"]
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/page.json")))
INK = "#18202A"; MUTED = "#8C96A1"; BED = "#D7DBE1"; MAT = "#E9ECF0"; DEV = "#C3C9D1"; STEEL = "#5B6B7C"; STEEL2 = "#AEB6C0"
SEAT = "#E09A3A"; FOAM_R = "#E7B66F"; FOAM_F = "#F3D7A8"; BODY = "#D9C8B4"; LIMB = "#B79C80"; BG = "#FBFAF6"; ACC = "#B4620A"; RED = "#C2412D"; GOOD = "#2F7A55"
M = D["mech"]; L = D["layout"]; BAR = D["consts"]["handrail"]; HALF = (D["consts"]["seat_x"][1] - D["consts"]["seat_x"][0]) / 2
REF = "H1.60 r0.09 p1.0 xa0.29"

def rotv(phi, p):
    a = math.radians(phi); return np.array([math.cos(a) * p[0] + math.sin(a) * p[1], -math.sin(a) * p[0] + math.cos(a) * p[1]])

def W(Q, phi, p): return np.array(Q) + rotv(phi, p)

def ik(S, P, l1, l2):
    S, P = np.array(S), np.array(P); d = P - S; Lr = np.hypot(*d)
    if Lr > l1 + l2 - 1e-4: return None
    a = math.atan2(d[1], d[0]); b = math.acos(max(-1, min(1, (l1 * l1 + Lr * Lr - l2 * l2) / (2 * l1 * Lr))))
    return S + l1 * np.array([math.cos(a - b), math.sin(a - b)])

def scene(ax, x0=-0.45, x1=1.05, z1=1.55):
    ax.clear(); ax.set_xlim(x0, x1); ax.set_ylim(-0.04, z1); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((x0, -0.04), x1 - x0, z1 + 0.04, color=BG, zorder=0))
    ax.plot([x0, x1], [0, 0], color=MUTED, lw=1.5, zorder=1)
    ax.add_patch(Rectangle((x0, 0), -x0, 0.36, color=BED, zorder=1)); ax.add_patch(Rectangle((x0, 0.36), -x0, 0.06, color=MAT, zorder=1))
    ax.text(x0 / 2, 0.17, "床", ha="center", va="center", color="#6B7480", fontsize=13)
    ax.add_patch(Rectangle((0.03, 0), 0.75, 0.04, color=DEV, zorder=2))

def housing(ax, alpha=0.30):
    ax.add_patch(Polygon(L["housing"], closed=True, facecolor=STEEL2, edgecolor=STEEL, lw=1.2, alpha=alpha, zorder=2))

def handrail(ax):
    ax.plot([BAR["x"], BAR["x"]], [0.04, BAR["z"]], color=STEEL, lw=5, alpha=.45, zorder=2, solid_capstyle="round")
    ax.add_patch(Circle((BAR["x"], BAR["z"]), 0.022, color=INK, zorder=7))

def mechanism(ax, Q, phi, show_inside=True):
    c1, c2, B = M["c1"], M["c2"], M["B"]
    P1 = W(Q, phi, c1); P2 = W(Q, phi, c2)
    if show_inside:
        for a, b in ((M["rail_lo"], M["rail_hi"]), (L["rail2"][0], L["rail2"][1])):
            ax.plot([a[0], b[0]], [a[1], b[1]], color=STEEL, lw=3, alpha=.55, zorder=3)
        ax.plot([B[0], P2[0]], [B[1], P2[1]], color=STEEL, lw=5, zorder=4, solid_capstyle="round")
        ax.add_patch(Circle(B, 0.012, facecolor=BG, edgecolor=STEEL, lw=2, zorder=5))
        e = np.array(M["rail_hi"]) - np.array(M["rail_lo"]); e = e / np.hypot(*e)
        ax.plot([P1[0] - 0.03 * e[0], P1[0] + 0.18 * e[0]], [P1[1] - 0.03 * e[1], P1[1] + 0.18 * e[1]], color=INK, lw=7, alpha=.7, zorder=4, solid_capstyle="butt")
    under = [W(Q, phi, (-HALF + 0.045, -0.062)), W(Q, phi, (-0.02, -0.062)), W(Q, phi, (-0.02, -0.092)), W(Q, phi, (HALF - 0.03, -0.092))]
    br = np.array(under + [P1, P2]); c = br.mean(0); order = np.argsort(np.arctan2(br[:, 1] - c[1], br[:, 0] - c[0]))
    ax.add_patch(Polygon(br[order], closed=True, color=STEEL2, alpha=.8, zorder=4))
    rear = [W(Q, phi, p) for p in ((-HALF, 0), (-0.02, 0), (-0.02, -0.05), (-HALF, -0.05))]
    front = [W(Q, phi, p) for p in ((-0.02, 0), (HALF, 0), (HALF, -0.08), (-0.02, -0.08))]
    ax.add_patch(Polygon(rear, closed=True, color=FOAM_R, zorder=5)); ax.add_patch(Polygon(front, closed=True, color=FOAM_F, zorder=5))
    return P1, P2

def person(ax, A, fr, bar=True, alpha=1.0):
    Ls, Lt, Ltr, Lua, Lfa = A["L"]; Hp, K, An = np.array(fr["Hp"]), np.array(fr["K"]), np.array(fr["A"])
    tr = math.radians(fr["tr"]); ut = np.array([math.sin(tr), math.cos(tr)]); S = Hp + Ltr * ut; foot = A["foot"]
    ax.add_patch(Polygon([[An[0] - 0.25 * foot, 0.042], [An[0] + 0.75 * foot, 0.042], [An[0] + 0.03, An[1] + 0.02], [An[0] - 0.03, An[1] + 0.025]], color=LIMB, alpha=alpha, zorder=8))
    ax.plot([Hp[0], K[0]], [Hp[1], K[1]], color=BODY, lw=22, solid_capstyle="round", alpha=alpha, zorder=8)
    ax.plot([K[0], An[0]], [K[1], An[1]], color=LIMB, lw=11, solid_capstyle="round", alpha=alpha, zorder=8)
    ax.plot([Hp[0], S[0]], [Hp[1], S[1]], color=BODY, lw=26, solid_capstyle="round", alpha=alpha, zorder=8)
    ax.add_patch(Circle(S + 0.13 * ut, 0.085, color=BODY, alpha=alpha, zorder=8))
    if bar:
        P = np.array([BAR["x"], BAR["z"]]); E = ik(S, P, Lua, Lfa)
        if E is not None: ax.plot([S[0], E[0], P[0]], [S[1], E[1], P[1]], color=LIMB, lw=7, solid_capstyle="round", solid_joinstyle="round", alpha=alpha, zorder=9)
    return S

def strip(ax, cu):
    s = np.array(cu["strip"]); p = np.array(cu["p"])
    for i in range(len(s) - 1):
        w = min(1.0, (p[i] + p[i + 1]) / 40); col = (0.76, 0.25 + 0.55 * (1 - w), 0.18 + 0.55 * (1 - w))
        ax.plot(s[i:i + 2, 0], s[i:i + 2, 1], color=col, lw=6, solid_capstyle="round", zorder=10)

def badge(ax, state, lines, step=None, cap=None):
    ax.add_patch(FancyBboxPatch((0.56, 1.36), 0.47, 0.12, boxstyle="round,pad=0.01,rounding_size=0.03", color="#FFFFFF", ec="#D9DDE2", zorder=11))
    ax.text(0.58, 1.42, "状态", color="#6B7480", fontsize=12, va="center", zorder=12)
    ax.text(0.68, 1.42, state, color=ACC, fontsize=15, fontweight="bold", va="center", zorder=12)
    for i, t in enumerate(lines): ax.text(0.58, 1.30 - 0.065 * i, t, color=INK, fontsize=12.5, zorder=12)
    if step: ax.text(-0.43, 1.50, step, color=ACC, fontsize=16, fontweight="bold", va="top", zorder=12)
    if cap: ax.text(-0.43, 1.41, cap, color=INK, fontsize=14, va="top", zorder=12, linespacing=1.5)

def frame_state(fr, released):
    if released: return "站立保持"
    if fr.get("seat") is None: return "已坐上"
    return "抬升"

def draw_frame(ax, A, fr, last_seat, cush="z1", step=None, cap=None):
    scene(ax); housing(ax); handrail(ax)
    released = fr.get("seat") is None and last_seat is not None
    cu = fr.get("cush", {}).get(cush) if fr.get("seat") else None
    if cu and not cu.get("lost"): Q, phi = cu["Q"], cu["phi"]
    elif fr.get("seat"): Q, phi = fr["seat"]["Q"], fr["seat"]["phi"]
    elif last_seat: Q, phi = last_seat["Q"], last_seat["phi"]
    else: Q, phi = M["frames"][0]["Q"], M["frames"][0]["phi"]
    mechanism(ax, Q, phi); person(ax, A, fr)
    if cu and not cu.get("lost"): strip(ax, cu)
    lines = [f"座面 {Q[1]:.2f} m · 前倾 {phi:.0f}°"]
    if cu and not cu.get("lost"): lines.append(f"坐垫接触 {cu['len_cm']:.0f} cm · 峰值 {cu['p_max']:.0f} kPa")
    elif released: lines.append("座板停在放手高度")
    badge(ax, "站立保持" if released else ("抬升" if fr.get("seat") else "已坐上"), lines, step, cap)
    return dict(Q=Q, phi=phi)

def render_gif(path, user=REF, fps=10):
    A = D["anim"][user]; fig = plt.figure(figsize=(8.0, 8.0), dpi=110); ax = fig.add_axes([0, 0, 1, 1]); imgs = []; last = None
    frames = [A["frames"][0]] * 8 + A["frames"] + [A["frames"][-1]] * 12
    for fr in frames:
        s = draw_frame(ax, A, fr, last)
        if fr.get("seat"): last = fr["seat"]
        fig.canvas.draw(); imgs.append(Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB"))
    q = [im.quantize(colors=96, method=Image.Quantize.MEDIANCUT) for im in imgs]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True, disposal=1)
    imgs[-1].save(path.replace(".gif", "_last.png")); imgs[len(imgs) // 2].save(path.replace(".gif", "_mid.png")); plt.close(fig)

def render_steps(prefix, user=REF):
    A = D["anim"][user]; fr = A["frames"]; idx_seat = [i for i, f in enumerate(fr) if f.get("seat")]
    k0 = idx_seat[0] if idx_seat else 0; kr = idx_seat[-1] if idx_seat else len(fr) - 1; km = (k0 + kr) // 2
    picks = [(0, "坐在床沿，挪上和床齐平的座板"), (0, "双手握住身前横杆的握把"), (k0 + 2, "握紧开关：座板跟着大腿前移、上升、前倾"),
             (km, "坐垫托住臀部和大腿近端，人自己也发力"), (len(fr) - 1, "站稳；座板停在放手高度，坐回也接得住")]
    last = None
    for n, (k, cap) in enumerate(picks, 1):
        fig = plt.figure(figsize=(6.0, 6.0), dpi=120); ax = fig.add_axes([0, 0, 1, 1])
        for f in fr[:k + 1]:
            if f.get("seat"): last = f["seat"]
        draw_frame(ax, A, fr[k], last)
        fig.savefig(f"{prefix}{n}.png", facecolor=BG); plt.close(fig)

def render_mech(path):
    fig = plt.figure(figsize=(9.0, 8.0), dpi=120); ax = fig.add_axes([0, 0, 1, 1]); scene(ax, -0.25, 0.95, 1.05); housing(ax, 0.22); handrail(ax)
    fs = M["frames"]; picks = [fs[0], fs[len(fs) // 2], fs[-1]]
    for i, f in enumerate(picks):
        P1, P2 = mechanism(ax, f["Q"], f["phi"], show_inside=(i == len(picks) - 1))
        if i < len(picks) - 1:
            for poly in ax.patches[-3:]: poly.set_alpha(0.35)
    lo, hi, B = M["rail_lo"], M["rail_hi"], M["B"]
    ax.annotate("双导轨 + 滚珠丝杠\n（电机在上端，箱内）", xy=(hi[0], hi[1]), xytext=(0.38, 0.95), fontsize=13, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED), zorder=12)
    ax.annotate("倾角连杆", xy=((B[0] + P2[0]) / 2, (B[1] + P2[1]) / 2), xytext=(0.55, 0.20), fontsize=13, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED), zorder=12)
    ax.annotate("分区坐垫：后硬前软", xy=tuple(W(fs[-1]["Q"], fs[-1]["phi"], (0.0, 0.0))), xytext=(-0.22, 0.88), fontsize=13, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED), zorder=12)
    ax.annotate("L 形扶手横杆", xy=(BAR["x"], BAR["z"]), xytext=(0.62, 0.62), fontsize=13, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED), zorder=12)
    ax.text(-0.22, 1.0, f"座板中心前移 {100 * M['travel']['dx']:.0f} cm、上升 {100 * M['travel']['dz']:.0f} cm，前倾 ≤ {M['phi_run_max']:.0f}°", fontsize=13.5, color=ACC, fontweight="bold")
    fig.savefig(path, facecolor=BG); plt.close(fig)

def render_vs(path):
    """early-hip user at the same moment: vertical lift vs the curved seat (from the relative-motion study data on the page)."""
    V = D["check"]["vertical"]; Fd = D["check"]["design"]
    early = [k for k in Fd if " p0.6 " in k]; k = max(early, key=lambda kk: (V[kk].get("fwd_slip_max_cm") or 0))
    A = D["anim"][k]; fr = A["frames"]; idx = [i for i, f in enumerate(fr) if f.get("seat")]; i = idx[len(idx) * 2 // 3] if idx else 0
    fig, axs = plt.subplots(1, 2, figsize=(14, 7.2), dpi=110); fig.patch.set_facecolor(BG)
    for ax, kind in zip(axs, ("vertical", "curve")):
        scene(ax, -0.35, 0.95, 1.45); f = fr[i]; rb = D["users"][[u["key"] for u in D["users"]].index(k)]["r_b"]
        if kind == "vertical":
            zz = min(max(f["Hp"][1] - rb, 0.42), 0.66); Q, phi = [0.0605, zz], 0.0       # level seat right under the buttock
            ax.add_patch(Polygon([W(Q, 0, p) for p in ((-HALF, 0), (HALF, 0), (HALF, -0.05), (-HALF, -0.05))], closed=True, color=SEAT, zorder=5))
            ax.plot([0.06, 0.06], [0.04, zz - 0.05], color=STEEL2, lw=14, zorder=3)
            ttl = f"竖直升降：前滑 {V[k]['fwd_slip_max_cm']:+.1f} cm，坐回余量 {V[k]['min_catch_cm']:+.1f} cm"; col = RED
        else:
            Q, phi = f["seat"]["Q"], f["seat"]["phi"]; mechanism(ax, Q, phi, show_inside=False)
            ttl = f"曲线坐板：前滑 {Fd[k]['fwd_slip_max_cm']:+.1f} cm，坐回余量 {Fd[k]['min_catch_cm']:+.1f} cm"; col = GOOD
        person(ax, A, f, bar=False)
        ax.text(-0.33, 1.38, ttl, fontsize=14, color=col, fontweight="bold", va="top")
    fig.text(0.5, 0.03, f"同一位髋早前移的用户（{k}），起身同一时刻", ha="center", fontsize=12, color="#6B7480")
    fig.savefig(path, facecolor=BG); plt.close(fig)

def render_force(path):
    fc = M["force_curve"]; tc = M["tilt_curve"]
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.4), dpi=120); fig.patch.set_facecolor("#FFFFFF")
    ax = axs[0]
    for k, lab, col in (("hold100", "静载：100 kg 猛坐 1.5 倍体重", RED), ("lift100", "起身：100 kg，座板推 0.5 倍体重", STEEL), ("lift60", "起身：60 kg", ACC)):
        ax.plot(fc["z"], fc[k], color=col, lw=2.4, label=lab)
    ax.set_xlabel("座面高度 (m)", fontsize=13); ax.set_ylabel("丝杠推力 (N)", fontsize=13); ax.set_ylim(0, None); ax.grid(alpha=.3); ax.legend(fontsize=11, frameon=False)
    ax.tick_params(labelsize=12)
    ax = axs[1]; ax.axhspan(0, 15, color="#E3F1EA"); ax.plot(tc["z"], tc["phi"], color=ACC, lw=2.6)
    ax.set_xlabel("座面高度 (m)", fontsize=13); ax.set_ylabel("座板前倾 (°)", fontsize=13); ax.set_ylim(-2, 20); ax.grid(alpha=.3); ax.tick_params(labelsize=12)
    ax.text(tc["z"][0], 16.2, "绿带 = 不超过 15°", fontsize=11, color=GOOD)
    fig.tight_layout(); fig.savefig(path, facecolor="#FFFFFF"); plt.close(fig)

def render_sensors(path, user=REF):
    A = D["anim"][user]; fr = A["frames"][0]
    fig = plt.figure(figsize=(6.4, 5.4), dpi=120); ax = fig.add_axes([0, 0, 1, 1]); scene(ax, -0.30, 1.0, 1.25); housing(ax); handrail(ax)
    mechanism(ax, M["frames"][0]["Q"], M["frames"][0]["phi"]); person(ax, A, fr)
    Q = M["frames"][0]["Q"]; pts = [(1, (Q[0], Q[1] - 0.09), "座板下测力（法向力）"), (2, (BAR["x"], BAR["z"] + 0.05), "横杆测力"), (3, (BAR["x"] - 0.06, BAR["z"] - 0.06), "握把开关"),
                                    (4, (0.42, 0.06), "踏板测力"), (5, (0.06, 0.015), "底座四角测力（体重自检）")]
    for n, (x, z), lab in pts:
        ax.add_patch(Circle((x, z), 0.026, facecolor="#E3A92E", edgecolor=INK, lw=1.2, zorder=13)); ax.text(x, z, str(n), ha="center", va="center", fontsize=11, fontweight="bold", zorder=14)
    for i, (n, _, lab) in enumerate(pts): ax.text(-0.28, 1.20 - 0.075 * i, f"{n}  {lab}", fontsize=12.5, color=INK, va="top", zorder=14)
    fig.savefig(path, facecolor=BG); plt.close(fig)

if __name__ == "__main__":
    render_force(os.path.join(HERE, "seat_force.png")); render_sensors(os.path.join(HERE, "seat_sensors.png"))
    render_gif(os.path.join(HERE, "seat_rise.gif")); render_steps(os.path.join(HERE, "seat_step")); render_mech(os.path.join(HERE, "seat_mech.png")); render_vs(os.path.join(HERE, "seat_vs_vertical.png"))
    print("done")
