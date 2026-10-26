"""Stick-figure demo animations for the rise-station slides (side view, schematic).
Geometry and poses follow the proposal page animation; joints are re-solved with 2-link IK so limb lengths stay fixed."""
import math, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Polygon, Rectangle, Circle, FancyBboxPatch
from PIL import Image

for f in font_manager.findSystemFonts():
    if "NotoSansCJK" in f and "Regular" in f: font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Noto Sans CJK SC", "DejaVu Sans"]

INK = "#18202A"; MUTED = "#8C96A1"; BED = "#D7DBE1"; MAT = "#E9ECF0"; DEV = "#C3C9D1"
SEAT = "#E09A3A"; ACT = "#7B4BB0"; SENS_ON = "#E3A92E"; SENS_OFF = "#D5D9DE"; BG = "#FBFAF6"; ACC = "#B4620A"
LEN = dict(T=0.461, TH=0.392, SH=0.394, U=0.298, F=0.32)

def ik(a, b, l1, l2, hint):
    a = np.array(a, float); b = np.array(b, float); d = b - a; L = np.linalg.norm(d)
    L = min(max(L, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3); u = d / (np.linalg.norm(d) + 1e-9); b = a + u * L
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L); h = math.sqrt(max(0, l1 * l1 - x * x)); n = np.array([-u[1], u[0]])
    p1 = a + u * x + n * h; p2 = a + u * x - n * h
    return (p1 if np.linalg.norm(p1 - hint) <= np.linalg.norm(p2 - hint) else p2), b

def solve(q):
    q = {k: np.array(v, float) for k, v in q.items()}
    t = q["S"] - q["H"]; q["S"] = q["H"] + t / np.linalg.norm(t) * LEN["T"]
    q["K"], q["A"] = ik(q["H"], q["A"], LEN["TH"], LEN["SH"], q["K"])
    q["E"], q["W"] = ik(q["S"], q["W"], LEN["U"], LEN["F"], q["E"])
    return q

P = {
 "edge":  dict(S=[-0.12,0.97],H=[-0.15,0.51],K=[0.24,0.46],A=[0.24,0.062],T=[0.41,0.02],E=[-0.05,0.72],W=[0.10,0.64]),
 "scoot": dict(S=[0.18,0.97],H=[0.13,0.51],K=[0.52,0.46],A=[0.52,0.062],T=[0.69,0.02],E=[0.22,0.70],W=[0.36,0.64]),
 "ready": dict(S=[0.28,0.94],H=[0.13,0.51],K=[0.46,0.40],A=[0.29,0.062],T=[0.46,0.02],E=[0.48,0.76],W=[0.69,0.82]),
 "rise":  dict(S=[0.37,1.149],H=[0.14,0.75],K=[0.42,0.44],A=[0.29,0.062],T=[0.46,0.02],E=[0.52,0.98],W=[0.69,1.06]),
 "stand": dict(S=[0.31,1.309],H=[0.29,0.848],K=[0.31,0.456],A=[0.29,0.062],T=[0.46,0.02],E=[0.50,1.10],W=[0.69,1.06]),
}
def seated(L, lean=0.0):
    """seated upright on the seat at lift L, hands on the bar"""
    return dict(S=[0.14+lean,0.97+L],H=[0.11,0.51+L],K=[0.46,0.44+0.6*L],A=[0.29,0.062],T=[0.46,0.02],E=[0.22,0.70+L],W=[0.40,0.58+L])

def lerp(a, b, t):
    return {k: [a[k][0] + (b[k][0] - a[k][0]) * t, a[k][1] + (b[k][1] - a[k][1]) * t] for k in a}

def ease(t): return 2*t*t if t < .5 else 1 - (-2*t+2)**2/2

def draw(ax, L, q, sens, state, caption, step, readout=True):
    ax.clear(); ax.set_xlim(-0.95, 1.66); ax.set_ylim(-0.05, 1.42); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((-0.95, -0.05), 2.61, 1.47, color=BG, zorder=0))
    ax.plot([-0.95, 1.66], [0, 0], color=MUTED, lw=1.5, zorder=1)
    ax.add_patch(Rectangle((-0.95, 0), 0.95, 0.27, color=BED, zorder=1)); ax.add_patch(Rectangle((-0.95, 0.27), 0.95, 0.15, color=MAT, zorder=1))
    ax.text(-0.45, 0.12, "床（不改造）", ha="center", va="center", color="#6B7480", fontsize=12)
    ax.add_patch(Rectangle((-0.26, 0.265), 0.27, 0.012, color=ACT, zorder=2))           # hook plate under mattress
    ax.add_patch(Polygon([[0,0],[0.80,0],[0.77,0.013],[0,0.013]], color=DEV, zorder=2))
    h0 = 0.42 + L
    ax.add_patch(Rectangle((0.0, 0.013), 0.14, 0.287, color=DEV, zorder=2))              # outer column housing
    if h0 - 0.05 > 0.30: ax.add_patch(Rectangle((0.035, 0.30), 0.07, h0 - 0.05 - 0.30, color="#AEB6C0", zorder=2))
    ax.add_patch(Polygon([[-0.03,h0],[0.14,h0],[0.14,h0-0.045],[-0.03,h0-0.045]], color=SEAT, zorder=3))
    BX, zs, zb = 0.69, 0.64 + L, 0.82 + L
    ax.plot([BX, BX], [0.02, 0.55], color=INK, lw=7, alpha=.3, zorder=2)
    ax.plot([BX, BX], [0.5, zb], color=INK, lw=3.5, alpha=.6, zorder=2)
    ax.plot([0, BX], [zs, zs], color=INK, lw=3.5, alpha=.45, zorder=2, solid_capstyle="round")
    ax.add_patch(Circle((BX, zb), 0.022, color=INK, zorder=4))
    q = solve(q)
    hc = q["S"] + (q["S"] - q["H"]) / np.linalg.norm(q["S"] - q["H"]) * 0.12
    for pts, w in (([q["S"], q["H"], q["K"], q["A"], q["T"]], 5), ([q["S"], q["E"], q["W"]], 3.5)):
        a = np.array(pts); ax.plot(a[:,0], a[:,1], color=INK, lw=w, solid_capstyle="round", solid_joinstyle="round", zorder=5)
    ax.add_patch(Circle(hc, 0.055, facecolor=BG, edgecolor=INK, lw=3, zorder=6))
    for key, (x, z) in dict(seat=(0.07, h0 - 0.022), bar=(BX, zb + 0.04), feet=(0.40, 0.006)).items():
        ax.add_patch(Circle((x, z), 0.018, facecolor=SENS_ON if key in sens else SENS_OFF, edgecolor=INK, lw=1, zorder=7))
    # state badge + readout
    ax.add_patch(FancyBboxPatch((1.08, 1.27), 0.52, 0.11, boxstyle="round,pad=0.01,rounding_size=0.03", color="#FFFFFF", ec="#D9DDE2", zorder=8))
    ax.text(1.105, 1.325, "状态", color="#6B7480", fontsize=12, va="center", zorder=9)
    ax.text(1.22, 1.325, state, color=ACC, fontsize=15, fontweight="bold", va="center", zorder=9)
    if readout: ax.text(1.105, 1.205, f"座面 {h0:.2f} m", color=INK, fontsize=13, zorder=9)
    ax.text(-0.92, 1.35, step, color=ACC, fontsize=16, fontweight="bold", va="top", zorder=9)
    ax.text(-0.92, 1.26, caption, color=INK, fontsize=15, va="top", zorder=9, linespacing=1.5)
    ax.text(1.105, 1.12, "● 黄点 = 正在受力的传感器", color="#6B7480", fontsize=11, va="top", zorder=9)

def render(frames, path, fps=12):
    fig = plt.figure(figsize=(9.6, 5.4), dpi=100, facecolor=BG); ax = fig.add_axes([0, 0, 1, 1])
    imgs = []
    for fr in frames:
        draw(ax, **fr); fig.canvas.draw()
        imgs.append(Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba()).convert("RGB"))
    plt.close(fig)
    pal = imgs[len(imgs)//2].quantize(colors=96, method=Image.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000/fps), loop=0, optimize=True, disposal=1)
    imgs[-1].save(path.replace(".gif", "_last.png")); imgs[0].save(path.replace(".gif", "_first.png"))

def seg(a, b, n, La, Lb, **kw):
    out = []
    for i in range(n):
        t = ease(i / max(1, n - 1))
        out.append(dict(L=La + (Lb - La) * t, q=lerp(a, b, t), **kw))
    return out

def hold(q, L, n, **kw): return [dict(L=L, q=q, **kw) for _ in range(n)]

# ---------- 1. one complete use ----------
F = []
F += hold(P["edge"], 0, 14, sens={"feet"}, state="待机", step="1 / 5", caption="坐在床沿，脚踩台架的踏板")
F += seg(P["edge"], P["scoot"], 18, 0, 0, sens={"feet"}, state="待机", step="2 / 5", caption="往前挪 25–30 cm，\n坐上和床齐平的短座板")
F += hold(P["scoot"], 0, 6, sens={"seat","feet"}, state="已坐上", step="2 / 5", caption="往前挪 25–30 cm，\n坐上和床齐平的短座板")
F += seg(P["scoot"], P["ready"], 14, 0, 0, sens={"seat","feet"}, state="已坐上", step="3 / 5", caption="握住横杆上的握把，\n想坐多久都行")
F += hold(P["ready"], 0, 10, sens={"seat","bar","feet"}, state="静坐", step="3 / 5", caption="握住横杆上的握把，\n想坐多久都行")
F += seg(P["ready"], P["rise"], 34, 0, 0.24, sens={"seat","bar","feet"}, state="抬升", step="4 / 5", caption="握紧“起”开关：\n座板竖直升起，\n人自己也在发力。\n人卸掉的体重越多，\n座板升得越快")
F += seg(P["rise"], P["stand"], 14, 0.24, 0.24, sens={"bar","feet"}, state="站立保持", step="5 / 5", caption="离座：座板停在\n原高度、保持水平")
F += hold(P["stand"], 0.24, 22, sens={"bar","feet"}, state="站立保持", step="5 / 5", caption="站稳后换手到助行器；\n万一坐回去，\n座板接得住")
render(F, "/tmp/claude-0/-home-claude/913dcd2f-c277-5e33-8b00-aa6df00d832b/scratchpad/anim/use_sequence.gif")

# ---------- 2. safety: sit back mid-lift ----------
mid = lerp(P["ready"], P["rise"], 0.45)
G = []
G += hold(P["ready"], 0, 8, sens={"seat","bar","feet"}, state="静坐", step="场景", caption="抬升中头晕、往回坐")
G += seg(P["ready"], mid, 18, 0, 0.11, sens={"seat","bar","feet"}, state="抬升", step="场景", caption="抬升中头晕、往回坐")
G += seg(mid, seated(0.11), 10, 0.11, 0.11, sens={"seat","feet"}, state="停住", step="1", caption="座板受力超过上限，\n速度自然变成 0；\n手离开握把，\n立即停住并制动")
G += hold(seated(0.11), 0.11, 18, sens={"seat","feet"}, state="停住", step="1", caption="座板停在当前高度、\n保持水平，接住人")
G += seg(seated(0.11), seated(0.0), 24, 0.11, 0.0, sens={"seat","feet"}, state="下降", step="2", caption="确认有人坐着\n（按住“降”或静坐\n一段时间），才以\n约 2 cm/s 带人降回床面")
G += hold(seated(0.0), 0.0, 16, sens={"seat","feet"}, state="已坐上", step="3", caption="回到床面高度，\n可以往后挪回床上")
render(G, "/tmp/claude-0/-home-claude/913dcd2f-c277-5e33-8b00-aa6df00d832b/scratchpad/anim/safety_sitback.gif")
print(len(F), len(G))
