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
font_manager.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc") if os.path.exists("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc") else None
plt.rcParams["font.family"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/page.json")))
for _u in D["users"]:
    if _u["key"] in D["anim"]: D["anim"][_u["key"]]["rb"] = _u["r_b"]
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

def outline(fr, rb):
    Hp, K = np.array(fr["Hp"]), np.array(fr["K"]); th = math.atan2(-(K[1] - Hp[1]), K[0] - Hp[0]); uu = np.array([math.cos(th), -math.sin(th)])
    pts = [Hp + rb * np.array([math.sin(math.radians(g)), -math.cos(math.radians(g))]) for g in np.arange(-95, -math.degrees(th) + 1e-9, 5)]
    T0 = Hp + rb * np.array([-math.sin(th), -math.cos(th)]); Lk = np.hypot(*(K - T0)); pts.append(T0 + uu * Lk * 0.92)
    nf = np.array([math.sin(th), math.cos(th)]); return np.array(pts), nf

def person(ax, A, fr, bar=True, alpha=1.0, rb=0.09):
    Ls, Lt, Ltr, Lua, Lfa = A["L"]; Hp, K, An = np.array(fr["Hp"]), np.array(fr["K"]), np.array(fr["A"])
    tr = math.radians(fr["tr"]); ut = np.array([math.sin(tr), math.cos(tr)]); S = Hp + Ltr * ut; foot = A["foot"]
    ax.add_patch(Polygon([[An[0] - 0.25 * foot, 0.042], [An[0] + 0.75 * foot, 0.042], [An[0] + 0.03, An[1] + 0.02], [An[0] - 0.03, An[1] + 0.025]], color=LIMB, alpha=alpha, zorder=8))
    pts, nf = outline(fr, rb)
    body = np.vstack([pts, [K + nf * 0.05, Hp + nf * 0.07 + ut * 0.05]])
    ax.add_patch(Polygon(body, closed=True, color=BODY, alpha=alpha, zorder=8)); ax.plot(pts[:, 0], pts[:, 1], color="#A88F75", lw=1.2, alpha=alpha, zorder=8)
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
    ax.add_patch(FancyBboxPatch((0.30, 1.36), 0.36, 0.12, boxstyle="round,pad=0.01,rounding_size=0.03", color="#FFFFFF", ec="#D9DDE2", zorder=11))
    ax.text(0.32, 1.42, "状态", color="#6B7480", fontsize=12, va="center", zorder=12)
    ax.text(0.42, 1.42, state, color=ACC, fontsize=15, fontweight="bold", va="center", zorder=12)
    for i, t in enumerate(lines): ax.text(0.30, 1.30 - 0.065 * i, t, color=INK, fontsize=12, zorder=12)
    if step: ax.text(-0.43, 1.50, step, color=ACC, fontsize=16, fontweight="bold", va="top", zorder=12)
    if cap: ax.text(-0.43, 1.41, cap, color=INK, fontsize=14, va="top", zorder=12, linespacing=1.5)

def frame_state(fr, released):
    if released: return "站立保持"
    if fr.get("seat") is None: return "已坐上"
    return "抬升"

def sunk(A, fr, dz):
    """v5.6b: the person sitting with the board flush: the foam carries the weight, so the hip is lower than the rigid-seat
    path by the foam compression dz; ankle fixed, knee re-solved (forward branch)."""
    if dz <= 0: return fr
    Ls, Lt = A["L"][0], A["L"][1]; An = np.array(fr["A"]); Hp = np.array(fr["Hp"]) - np.array([0.0, dz]); d = Hp - An; Lr = np.hypot(*d)
    if Lr >= Ls + Lt - 1e-4: return fr
    a = math.atan2(d[1], d[0]); b = math.acos(max(-1, min(1, (Ls * Ls + Lr * Lr - Lt * Lt) / (2 * Ls * Lr))))
    K = max((An + Ls * np.array([math.cos(a + sg * b), math.sin(a + sg * b)]) for sg in (-1, 1)), key=lambda k: k[0])
    return dict(fr, Hp=Hp.tolist(), K=K.tolist())

def draw_frame(ax, A, fr, last_seat, cush="z1", step=None, cap=None, hands=True, state=None, flush=False):
    scene(ax); housing(ax); handrail(ax)
    released = fr.get("seat") is None and last_seat is not None
    cu = fr.get("cush", {}).get(cush) if (fr.get("seat") and not flush) else None
    if flush:                         # v5.6: sitting before the lift: board flush with the bed, the person sunk into the foam
        Q, phi = M["frames"][0]["Q"], M["frames"][0]["phi"]; mechanism(ax, Q, phi)
        c0 = fr.get("cush", {}).get(cush) or {}; dz = (c0.get("sink_mm") or 0) / 1000 if isinstance(flush, bool) else flush
        person(ax, A, sunk(A, fr, dz), bar=hands, rb=A.get("rb", 0.09))
        badge(ax, state or "已坐上", [f"座板 {Q[1]:.2f} m（坐垫面与床面齐平）· 前倾 {phi:.0f}°", f"人坐进坐垫约 {100 * dz:.0f} cm"], step, cap); return dict(Q=Q, phi=phi)
    if cu and not cu.get("lost"): Q, phi = cu["Q"], cu["phi"]
    elif fr.get("seat"): Q, phi = fr["seat"]["Q"], fr["seat"]["phi"]
    elif last_seat: Q, phi = last_seat["Q"], last_seat["phi"]
    else: Q, phi = M["frames"][0]["Q"], M["frames"][0]["phi"]
    mechanism(ax, Q, phi); person(ax, A, fr, bar=hands, rb=A.get("rb", 0.09))
    if cu and not cu.get("lost"): strip(ax, cu)
    lines = [f"座面 {Q[1]:.2f} m · 前倾 {phi:.0f}°"]
    if cu and not cu.get("lost"): lines.append(f"坐垫接触 {cu['len_cm']:.0f} cm · 峰值 {cu['p_max']:.0f} kPa")
    elif released: lines.append("座板停在放手高度")
    badge(ax, state or ("站立保持" if released else ("抬升" if fr.get("seat") else "已坐上")), lines, step, cap)
    return dict(Q=Q, phi=phi)

def render_gif(path, user=REF, fps=10):
    A = D["anim"][user]; fig = plt.figure(figsize=(8.0, 8.0), dpi=110); ax = fig.add_axes([0, 0, 1, 1]); imgs = []; last = None
    frames = [A["frames"][0]] * 13 + A["frames"] + [A["frames"][-1]] * 12
    states = ["已坐上"] * 8 + ["抬升"] * 5 + [None] * len(A["frames"]) + ["站立保持"] * 12
    f0 = A["frames"][0]; c0 = f0["cush"]["z1"]; dz0 = c0["sink_mm"] / 1000; Qf, pf = np.array(M["frames"][0]["Q"]), M["frames"][0]["phi"]
    for n_, (fr, stt) in enumerate(zip(frames, states)):
        if 8 <= n_ < 13:                  # v5.6b: start of the lift: board and person rise together until the foam carries 0.5 BW
            w = (n_ - 7) / 6; Q = (1 - w) * Qf + w * np.array(c0["Q"]); ph = (1 - w) * pf + w * c0["phi"]
            scene(ax); housing(ax); handrail(ax); mechanism(ax, Q, ph); person(ax, A, sunk(A, f0, (1 - w) * dz0), rb=A.get("rb", 0.09))
            badge(ax, "抬升", [f"座板 {Q[1]:.2f} m · 前倾 {ph:.0f}°", "座板和人一起先升约 3 cm"])
            fig.canvas.draw(); imgs.append(Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB")); continue
        s = draw_frame(ax, A, fr, last, state=stt, flush=(n_ < 8))
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
        draw_frame(ax, A, fr[k], last, hands=(n != 1), state=["已坐上", "已坐上", "抬升", "抬升", "站立保持"][n - 1], flush=(n <= 2))
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
    ax.text(-0.22, 1.0, f"座板中心前移 {100 * M['travel']['dx']:.1f} cm、上升 {100 * M['travel']['dz']:.1f} cm，前倾 ≤ {M['phi_run_max']:.1f}°", fontsize=13.5, color=ACC, fontweight="bold")
    fig.savefig(path, facecolor=BG); plt.close(fig)

def render_vs(path):
    """early-hip user at the same moment: vertical lift (seat rises until it touches the body, max 0.66 m) vs the curved seat."""
    V = D["check"]["vertical"]; Fd = D["check"]["design"]; UU = {u["key"]: u for u in D["users"]}
    early = [k for k in Fd if " p0.6 " in k]; k = max(early, key=lambda kk: (V[kk].get("fwd_slip_max_cm") or 0))
    A = D["anim"][k]; rb = UU[k]["r_b"]; fr = A["frames"]; idx = [i for i, f in enumerate(fr) if f.get("seat")]; i = idx[len(idx) // 2] if idx else 0
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.1), dpi=110); fig.patch.set_facecolor(BG)    # v5.6: slide box is 660 x 260
    fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0, wspace=0.02)
    for ax, kind in zip(axs, ("vertical", "curve")):
        scene(ax, -0.35, 0.95, 1.45); f = fr[i]
        if kind == "vertical":
            pts, _ = outline(f, rb); x0, x1 = 0.0605 - HALF, 0.0605 + HALF; under = pts[(pts[:, 0] >= x0) & (pts[:, 0] <= x1)]
            zz = min(float(under[:, 1].min()) if len(under) else 0.66, 0.66)
            ax.add_patch(Polygon([(x0, zz), (x1, zz), (x1, zz - 0.05), (x0, zz - 0.05)], closed=True, color=SEAT, zorder=5))
            ax.plot([0.06, 0.06], [0.04, zz - 0.05], color=STEEL2, lw=14, zorder=3)
            ttl = f"竖直升降：往前滑 {V[k]['fwd_slip_max_cm']:.0f} cm"; col = RED
            note = "座板只能竖直上来，髋已经走到座板前面：\n只托住臀部后缘，人往前滑，坐回时会坐空"
        else:
            Q, phi = f["seat"]["Q"], f["seat"]["phi"]; mechanism(ax, Q, phi, show_inside=False)
            ttl = f"曲线坐板：往前滑 {Fd[k]['fwd_slip_max_cm']:.0f} cm"; col = GOOD
            note = "座板跟着大腿往前、往上、前倾：\n一直托在臀部和大腿根部下面"
        person(ax, A, f, bar=False, rb=rb)
        ax.set_ylim(0.15, 1.45); ax.text(-0.33, 1.40, ttl, fontsize=24, color=col, fontweight="bold", va="top")
        ax.text(-0.33, 1.25, "跟不上大腿，只托住臀部后缘" if kind == "vertical" else "一直托在臀部和大腿根部下面", fontsize=17, color=INK, va="top", zorder=12)
    fig.savefig(path, facecolor=BG); plt.close(fig)

def render_force(path):
    fc = M["force_curve"]; tc = M["tilt_curve"]
    fig, axs = plt.subplots(1, 2, figsize=(11.6, 4.4), dpi=120); fig.patch.set_facecolor("#FFFFFF")
    ax = axs[0]
    for k, lab, col in (("hold100", "静载：100 kg 猛坐 1.5 倍体重", RED), ("lift100", "起身：100 kg，座板推 0.5 倍体重", STEEL), ("lift60", "起身：60 kg", ACC)):
        ax.plot(fc["z"], fc[k], color=col, lw=2.4, label=lab)
    ax.set_xlabel("座面高度 (m)", fontsize=13); ax.set_ylabel("丝杠推力 (N)", fontsize=13); ax.set_ylim(0, None); ax.grid(alpha=.3); ax.legend(fontsize=11, frameon=False)
    ax.tick_params(labelsize=12)
    ax = axs[1]; ax.axhspan(0, 16, color="#E3F1EA"); ax.plot(tc["z"], tc["phi"], color=ACC, lw=2.6)
    ax.set_xlabel("座面高度 (m)", fontsize=13); ax.set_ylabel("座板前倾 (°)", fontsize=13); ax.set_ylim(-2, 20); ax.grid(alpha=.3); ax.tick_params(labelsize=12)
    ax.text(tc["z"][0], 17.0, "绿带 = 机构综合时的上限 16°", fontsize=11, color=GOOD)
    fig.tight_layout(); fig.savefig(path, facecolor="#FFFFFF"); plt.close(fig)

def render_sensors(path, user=REF):
    A = D["anim"][user]; fr = A["frames"][0]
    fig = plt.figure(figsize=(6.4, 5.4), dpi=120); ax = fig.add_axes([0, 0, 1, 1]); scene(ax, -0.30, 1.0, 1.25); housing(ax); handrail(ax)
    mechanism(ax, M["frames"][0]["Q"], M["frames"][0]["phi"]); person(ax, A, fr)
    Q = M["frames"][0]["Q"]; pts = [(1, (Q[0], Q[1] - 0.09), "座板下测力（法向力）"), (2, (BAR["x"], BAR["z"] + 0.05), "横杆测力"), (3, (BAR["x"] - 0.06, BAR["z"] - 0.06), "握把开关"),
                                    (4, (0.42, 0.06), "踏板测力")]
    for n, (x, z), lab in pts:
        ax.add_patch(Circle((x, z), 0.026, facecolor="#E3A92E", edgecolor=INK, lw=1.2, zorder=13)); ax.text(x, z, str(n), ha="center", va="center", fontsize=11, fontweight="bold", zorder=14)
    for i, (n, _, lab) in enumerate(pts): ax.text(-0.28, 1.20 - 0.075 * i, f"{n}  {lab}", fontsize=12.5, color=INK, va="top", zorder=14)
    fig.savefig(path, facecolor=BG); plt.close(fig)

def _box(ax, xy, w, h, txt, fc, fs=17, ec=INK):
    ax.add_patch(FancyBboxPatch((xy[0] - w / 2, xy[1] - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", facecolor=fc, edgecolor=ec, lw=1.6, zorder=3))
    ax.text(xy[0], xy[1], txt, ha="center", va="center", fontsize=fs, fontweight="bold", color=INK, zorder=4)

def _arrow(ax, a, b, lab="", rad=0.0, lxy=None, fs=12.5, col=STEEL, ls="-"):
    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch(a, b, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>", mutation_scale=18, lw=1.8, color=col, linestyle=ls, zorder=2, shrinkA=4, shrinkB=4))
    if lab:
        x, y = lxy if lxy else ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        ax.text(x, y, lab, ha="center", va="center", fontsize=fs, color=INK, zorder=5, linespacing=1.25,
                bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="none", alpha=0.92))

def render_statemachine(path):
    """state machine of the seat (v5.3 rules), Chinese, large type for a slide."""
    fig = plt.figure(figsize=(16.6, 5.2), dpi=120); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-0.6, 16.0); ax.set_ylim(-0.35, 4.6); ax.axis("off")
    ax.add_patch(Rectangle((-0.6, -0.35), 16.6, 4.95, color="#FFFFFF", zorder=0))
    W_, H_ = 1.9, 0.78
    P = {"待机": (0.5, 3.4), "已坐上": (3.6, 3.4), "抬升": (7.4, 3.4), "站立保持": (11.2, 3.4), "空座板停住": (14.5, 3.4),
         "下降": (3.6, 0.7), "停住": (7.4, 0.7), "锁定": (14.5, 0.7)}
    FC = {"抬升": "#DFF3EA", "停住": "#FDF3E2", "锁定": "#F9E0DD", "站立保持": "#ECE6F8", "下降": "#FBF5D9"}
    for k, xy in P.items(): _box(ax, xy, W_ if k != "空座板停住" else 2.3, H_, k, FC.get(k, "#F4F6F8"))
    e = lambda k, dx=0, dy=0: (P[k][0] + dx, P[k][1] + dy)
    _arrow(ax, e("待机", 0.95), e("已坐上", -0.95), "坐上座板", lxy=(2.05, 3.75))
    _arrow(ax, e("已坐上", 0.95), e("抬升", -0.95), "握紧开关 + 手在杆上\n+ 脚踩实 + 坐正", lxy=(5.5, 3.95))
    _arrow(ax, e("抬升", 0.95), e("站立保持", -0.95), "离座 0.3 s", lxy=(9.3, 3.75))
    _arrow(ax, e("站立保持", 1.0), e("空座板停住", -1.15), "人走开", lxy=(12.85, 3.75))
    _arrow(ax, e("抬升", -0.35, -0.39), e("停住", -0.35, 0.39), "松手 / 故障 / 断电\n/ 推不动或到顶", lxy=(6.2, 2.05))
    _arrow(ax, e("停住", 0.35, 0.39), e("抬升", 0.35, -0.39), "再握紧", lxy=(8.2, 2.05))
    _arrow(ax, e("停住", -0.95), e("下降", 0.95), "按住“降”", rad=0.0, lxy=(5.5, 0.98))
    _arrow(ax, e("下降", 0.95, -0.2), e("停住", -0.95, -0.2), "松开“降”", lxy=(5.5, 0.22))
    _arrow(ax, e("已坐上", -0.3, -0.39), e("下降", -0.3, 0.39), "按住“降”\n（座板高于齐平）", lxy=(2.5, 2.05))
    _arrow(ax, e("下降", 0.3, 0.39), e("已坐上", 0.3, -0.39), "到齐平", lxy=(4.4, 2.05))
    _arrow(ax, e("站立保持", -0.5, -0.39), e("停住", 0.95, 0.1), "坐回：座板不动，接住人", rad=-0.15, lxy=(10.6, 1.75))
    ax.plot([14.5, 14.5, 3.6], [3.8, 4.38, 4.38], color=MUTED, lw=1.8, zorder=2)
    _arrow(ax, (3.6, 4.38), e("已坐上", 0.0, 0.40), "", col=MUTED)
    ax.text(9.0, 4.38, "回床：按住“降”，空座板停在回床高度（默认 0.50 m），坐上去；再按住“降”降到床面（空着时松开再按住，也降到床面）", ha="center", va="center", fontsize=12.5, color=INK, zorder=5,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="#FFFFFF", edgecolor="none"))
    ax.text(14.5, 2.15, "任意状态", ha="center", va="center", fontsize=13, color=MUTED)
    _arrow(ax, (14.5, 1.95), e("锁定", 0, 0.42), "", col=RED, ls="--")
    ax.text(14.25, 1.45, "自检不过（空载零点 / 抬升中\n力之和与体重差 >15%，0.5 s）\n→ 只能按住“降”慢降", ha="right", va="center", fontsize=12, color=INK, linespacing=1.3)
    ax.text(7.4, -0.12, "停住时坐着很久不动：提醒并呼叫家属，座板不会自己动", ha="center", va="center", fontsize=13, color=ACC, fontweight="bold")
    fig.savefig(path, facecolor="#FFFFFF"); plt.close(fig)

def render_top(path):
    """top view: bed, base, mechanism housing, seat (flush and at the top), L-handrail, how the user walks off and back."""
    Y = L["Y"]; Hx = [p[0] for p in L["housing"]]
    fig = plt.figure(figsize=(7.8, 5.6), dpi=140); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-1.15, 0.95); ax.set_ylim(1.02, -0.48); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((-1.15, -0.48), 2.1, 1.5, color=BG, zorder=0))
    # plot axes: horizontal = along the bed (y, head side to the right), vertical = out from the bed edge (x, down)
    R = lambda y0, y1, x0, x1, **k: ax.add_patch(Rectangle((y0, x0), y1 - y0, x1 - x0, **k))
    R(-1.40, 0.80, -0.98, 0.0, facecolor=MAT, edgecolor=MUTED, lw=1.2, zorder=1); ax.text(-1.10, -0.40, "床（示意：只画了床长 2.0 m 中的一段）", fontsize=12, color="#6B7480")
    R(0.52, 0.76, -0.80, -0.10, facecolor="#FFFFFF", edgecolor=MUTED, lw=1, zorder=2); ax.text(0.64, -0.25, "枕头", fontsize=12, color="#6B7480", ha="center", rotation=90)
    ax.text(0.86, -0.25, "床头", fontsize=13, color=INK, ha="center", rotation=90); ax.text(-1.12, 0.12, "← 床尾", fontsize=13, color=INK, ha="left")
    R(Y["base_open"], Y["base_head"], 0.03, 0.78, facecolor="none", edgecolor=STEEL, lw=1.4, ls="--", zorder=3)
    ax.text(Y["base_open"] - 0.02, 0.12, "底座边缘\n做斜坡", fontsize=12, color=INK, ha="right", va="center")
    R(Y["wall_in"], Y["wall_out"], min(Hx), max(Hx), facecolor=STEEL2, edgecolor=STEEL, lw=1.4, zorder=4)
    ax.annotate("机构箱\n（顶高 0.80 m）", xy=(Y["wall_out"], 0.30), xytext=(0.48, 0.55), fontsize=12, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED))
    sx = D["consts"]["seat_x"]; dx = M["travel"]["dx"]
    R(-Y["seat"], Y["seat"], sx[0], sx[1], facecolor=FOAM_R, edgecolor=ACC, lw=1.4, zorder=5, alpha=0.9)
    R(-Y["seat"], Y["seat"], sx[0] + dx, sx[1] + dx, facecolor="none", edgecolor=ACC, lw=1.4, ls=":", zorder=5)
    ax.text(0.0, (sx[0] + sx[1]) / 2, "座板（与床齐平）", fontsize=12.5, color=INK, ha="center", va="center", zorder=6)
    ax.text(-0.02, sx[1] + dx - 0.035, f"升到顶时前移 {100 * dx:.0f} cm", fontsize=11.5, color=ACC, ha="center", va="center", zorder=6)
    ax.plot([0.30, -0.05], [BAR["x"], BAR["x"]], color=INK, lw=7, solid_capstyle="round", zorder=6); ax.add_patch(Circle((0.30, BAR["x"]), 0.035, color=INK, zorder=7))
    ax.add_patch(Circle((-0.05, BAR["x"]), 0.03, facecolor="#E3A92E", edgecolor=INK, lw=1.2, zorder=8))
    ax.annotate("末端圆头软包 + 夜光", xy=(-0.07, BAR["x"]), xytext=(-0.42, BAR["x"] + 0.16), fontsize=11.5, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED), zorder=8)
    ax.text(0.12, BAR["x"] - 0.05, "L 形扶手横杆（握把开关在这里）", fontsize=12, color=INK, ha="center", va="bottom", zorder=7)
    ax.add_patch(Circle((0.0, 0.42), 0.05, facecolor=BODY, edgecolor=LIMB, zorder=6)); ax.text(0.07, 0.42, "人站起时的位置", fontsize=11.5, color=INK, va="center", zorder=6)
    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch((-0.06, 0.45), (-0.60, 0.62), connectionstyle="arc3,rad=-0.25", arrowstyle="-|>", mutation_scale=20, lw=2.4, color=GOOD, zorder=8))
    R(-0.88, -0.62, 0.50, 0.86, facecolor="none", edgecolor=GOOD, lw=1.6, zorder=8); ax.text(-0.75, 0.68, "助行器", fontsize=12.5, color=GOOD, ha="center", va="center")
    ax.text(-0.72, 0.36, "站稳后转向床尾一侧\n走下底座、扶助行器", fontsize=12, color=GOOD, ha="center", va="center", zorder=8)
    ax.add_patch(FancyArrowPatch((-0.30, -0.06), (-0.62, -0.30), connectionstyle="arc3,rad=0.25", arrowstyle="-|>", mutation_scale=18, lw=2.0, color=ACC, ls="--", zorder=8))
    ax.text(-0.52, -0.17, "回床：按住“降”，座板停在 0.50 m → 坐上 →\n按住“降”降到床面 → 往后挪、腿向床尾转上床", fontsize=11.5, color=ACC, ha="center", va="center", zorder=8)
    ax.annotate("", xy=(Y["base_open"], 0.95), xytext=(Y["base_head"], 0.95), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2))
    ax.text((Y["base_open"] + Y["base_head"]) / 2 - 0.05, 0.93, f"台架沿床长占 {100 * (Y['base_head'] - Y['base_open']):.0f} cm", fontsize=12, color=INK, ha="center", va="bottom")
    fig.savefig(path, facecolor=BG); plt.close(fig)

if __name__ == "__main__":
    render_force(os.path.join(HERE, "seat_force.png")); render_sensors(os.path.join(HERE, "seat_sensors.png"))
    render_statemachine(os.path.join(HERE, "seat_statemachine.png")); render_top(os.path.join(HERE, "seat_top.png"))
    render_gif(os.path.join(HERE, "seat_rise.gif")); render_steps(os.path.join(HERE, "seat_step")); render_mech(os.path.join(HERE, "seat_mech.png")); render_vs(os.path.join(HERE, "seat_vs_vertical.png"))
    print("done")
