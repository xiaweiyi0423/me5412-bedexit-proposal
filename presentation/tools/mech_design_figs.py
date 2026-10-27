"""Figures for the mechanism-design slides (deck v5.7): where the seat must go, five candidate mechanisms, how the
inclined rail + tilt link was sized. All geometry comes from model/calc_v13/seat_1dof/{page,v5,fourbar_oneside}.json.
Output: presentation/assets_v57/{md_target,md_candidates,md_synthesis}.png
"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CALC = os.path.join(ROOT, "model/calc_v13"); sys.path.insert(0, CALC)
import seat_1dof_layout as LY  # seat plate + bracket polygons (same as the checks)
from seat_trajectory import rot
OUT = os.path.join(ROOT, "presentation/assets_v57")
J = lambda f: json.load(open(os.path.join(CALC, "seat_1dof", f)))
P = J("page.json"); V5 = J("v5.json"); OS = J("fourbar_oneside.json")
M = P["mech"]; Z0 = P["consts"]["Z0"]

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False
INK, BODY, MUTED, OR, G1, G2, BLUE, GREEN, RED, BED = "#18202A", "#3F4A57", "#66707C", "#B4620A", "#C3C9D1", "#7D8792", "#2F5A95", "#2F7A55", "#A2431F", "#E3E6EA"


def bed(ax, x0=-0.12, cm=False, label_z=None):
    k = 100 if cm else 1
    ax.add_patch(Rectangle((x0 * k, 0), -x0 * k, Z0 * k, fc=BED, ec="none", zorder=0))
    ax.text(x0 * k / 2, label_z if label_z is not None else Z0 * k * 0.5, "床", ha="center", va="center", color=MUTED, fontsize=11)


# ---------------------------------------------------------------- A: target path
def fig_target():
    fig, ax = plt.subplots(figsize=(9.6, 6.6), dpi=220); FS = 17
    for k, e in P["envelope"].items():
        Q = np.array(e["Q"]) * 100; ax.plot(Q[:, 0], Q[:, 1], color=G1, lw=0.8, zorder=1)
    Qd = np.array(P["design_curve"]["poses"]["Q"]) * 100
    Qm = np.array([f["Q"] for f in M["frames"]]) * 100
    ax.plot(Qd[:, 0], Qd[:, 1], color=OR, lw=4.5, zorder=3, solid_capstyle="round")
    ax.plot(Qm[:, 0], Qm[:, 1], color=INK, lw=1.8, ls=(0, (4, 3)), zorder=4)
    x0 = Qd[0, 0]; ax.plot([x0, x0], [Z0 * 100, 69], color=RED, lw=2.4, ls=(0, (6, 3)), zorder=2)
    bed(ax, -0.10, cm=True, label_z=40)
    ax.text(x0 - 1.0, 63, "竖直升降\n11/81 合格", color=RED, fontsize=FS, ha="right", va="center")
    ax.annotate("灰线：81 人各自\n理想的座板路径", xy=(19.5, 57), xytext=(26, 45), fontsize=FS, color=BODY, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))
    ax.annotate("橙线：设计曲线", xy=(Qd[-15, 0], Qd[-15, 1]), xytext=(10, 71.2), fontsize=FS, color=OR, arrowprops=dict(arrowstyle="-", color=OR, lw=0.9))
    ax.annotate("黑虚线：机构实际走的\n（最多差 8 mm）", xy=(Qm[-4, 0], Qm[-4, 1]), xytext=(26, 60), fontsize=FS, color=INK, arrowprops=dict(arrowstyle="-", color=INK, lw=0.9))
    ax.plot([x0], [Z0 * 100], "o", color=INK, ms=6, zorder=5); ax.text(x0 + 0.8, Z0 * 100 - 2.0, "起点：和床面齐平", fontsize=FS - 2, color=BODY)
    ax.set_xlim(-10, 44); ax.set_ylim(38, 73); ax.set_aspect("equal")
    ax.set_xlabel("座板中心在床沿前（cm）", fontsize=FS - 1, color=BODY); ax.set_ylabel("座面高度（cm）", fontsize=FS - 1, color=BODY)
    for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=FS - 3); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "md_target.png"), facecolor="white"); plt.close(fig)


# ---------------------------------------------------------------- four-bar forward kinematics (for the one-side layout)
def fourbar_frames(m, top, n=400):
    A, B, c1, c2 = (np.array(m[k]) for k in ("A", "B", "c1", "c2")); L1, L2 = m["L1"], m["L2"]; cp = np.hypot(*(c2 - c1))
    Q0 = np.array(P["design_curve"]["poses"]["Q"][0]); P1 = Q0 + rot(0) @ c1; P2 = Q0 + rot(0) @ c2
    th0 = np.arctan2(*(P1 - A)[::-1]); out = []; prev = P2
    for sgn in (1, -1):  # pick the direction that lifts the seat
        out = []; prev = P2
        for th in th0 + sgn * np.linspace(0, np.radians(160), n):
            X = A + L1 * np.array([np.cos(th), np.sin(th)]); d = B - X; dd = np.hypot(*d)
            if dd > L2 + cp or dd < abs(L2 - cp): break
            a = (cp ** 2 - L2 ** 2 + dd ** 2) / (2 * dd); h = np.sqrt(max(cp ** 2 - a ** 2, 0)); e = d / dd; nn = np.array([-e[1], e[0]])
            ca, cb = X + a * e + h * nn, X + a * e - h * nn; Y = ca if np.hypot(*(ca - prev)) <= np.hypot(*(cb - prev)) else cb; prev = Y
            loc = np.arctan2(*(c2 - c1)[::-1]); phi = np.degrees(loc - np.arctan2(*(Y - X)[::-1])); Q = X - rot(phi) @ c1
            out.append(dict(Q=Q.tolist(), phi=float(phi), P1=X.tolist(), P2=Y.tolist()))
            if Q[1] >= top: break
        if len(out) > 5 and out[-1]["Q"][1] > out[0]["Q"][1] + 0.05: return out
    return out


def plate(ax, f, c1, c2, alpha=1.0, z=3):
    pl, br = LY.seat_polys(np.array(f["Q"]), f["phi"], np.array(c1), np.array(c2))
    ax.add_patch(Polygon(br, closed=True, fc="#9AA3AE", ec="none", alpha=0.55 * alpha, zorder=z))
    ax.add_patch(Polygon(pl, closed=True, fc=OR, ec="none", alpha=alpha, zorder=z + 1))


def pivot(ax, p, ground=False, z=6):
    if ground: ax.plot(*p, marker="^", ms=8, color=INK, zorder=z)
    else: ax.plot(*p, "o", ms=5.5, mfc="white", mec=INK, mew=1.3, zorder=z)


# ---------------------------------------------------------------- B: five candidates (side view, start pose solid, top pose ghost)
def fig_candidates():
    mid, sides = V5["layouts"]["mid"]["mech"], V5["layouts"]["sides"]["mech"]
    osd = OS["mech"]; os_frames = fourbar_frames(osd, 0.69)
    panels = [("竖直升降", "vert", None), ("四连杆 · 座板正下方中间", "fb", (mid, mid["frames"])),
              ("四连杆 · 两腿外侧各一套", "fb", (sides, sides["frames"])), ("四连杆 · 只在床头一侧", "fb", (osd, os_frames)),
              ("斜导轨 + 倾角连杆（采用）", "slider", (M, M["frames"]))]
    fig, axs = plt.subplots(1, 5, figsize=(17, 4.4), dpi=200)
    for ax, (title, kind, data) in zip(axs, panels):
        bed(ax, -0.12); ax.plot([-0.12, 0.58], [0, 0], color=G2, lw=1.2, zorder=0)
        if kind == "vert":
            c1 = [0.0, -0.1]; c2 = [0.0, -0.05]
            for f, al in ((dict(Q=[0.055, Z0], phi=0.0), 1.0), (dict(Q=[0.055, 0.69], phi=0.0), 0.35)):
                pl, _ = LY.seat_polys(np.array(f["Q"]), 0.0, np.array(c1), np.array(c2))
                ax.add_patch(Polygon(pl, closed=True, fc=OR, ec="none", alpha=al, zorder=4))
            ax.add_patch(Rectangle((0.035, 0.0), 0.04, Z0 - 0.045, fc=G2, ec="none", zorder=2))
            ax.add_patch(Rectangle((0.035, Z0 - 0.045), 0.04, 0.69 - Z0, fc=G2, ec="none", alpha=0.3, zorder=2))
            ax.annotate("", xy=(0.15, 0.69), xytext=(0.15, Z0 + 0.02), arrowprops=dict(arrowstyle="->", color=RED, lw=1.6))
        elif kind == "fb":
            m, fr = data; A, B = m["A"], m["B"]; f0, f1 = fr[0], fr[-1]
            Qs = np.array([f["Q"] for f in fr]); ax.plot(Qs[:, 0], Qs[:, 1], color=OR, lw=1.4, ls=(0, (3, 2)), zorder=2)
            for f, al in ((f1, 0.3), (f0, 1.0)):
                plate(ax, f, m["c1"], m["c2"], al)
                for g, p in ((A, f["P1"]), (B, f["P2"])): ax.plot([g[0], p[0]], [g[1], p[1]], color=INK, lw=2.4, alpha=al, zorder=5)
                for p in (f["P1"], f["P2"]): pivot(ax, p) if al == 1.0 else None
            for g in (A, B): pivot(ax, g, ground=True)
        else:
            m, fr = data; f0, f1 = fr[0], fr[-1]; lo, hi = np.array(M["rail_lo"]), np.array(M["rail_hi"])
            ax.plot([lo[0], hi[0]], [lo[1], hi[1]], color=BLUE, lw=5, alpha=0.75, solid_capstyle="round", zorder=2)
            Qs = np.array([f["Q"] for f in fr]); ax.plot(Qs[:, 0], Qs[:, 1], color=OR, lw=1.4, ls=(0, (3, 2)), zorder=2)
            for f, al in ((f1, 0.3), (f0, 1.0)):
                plate(ax, f, M["c1"], M["c2"], al)
                ax.plot([M["B"][0], f["P2"][0]], [M["B"][1], f["P2"][1]], color=INK, lw=2.4, alpha=al, zorder=5)
                ax.add_patch(Rectangle((f["P1"][0] - 0.02, f["P1"][1] - 0.02), 0.04, 0.04, fc=BLUE, ec=INK, lw=0.8, alpha=al, zorder=5))
                if al == 1.0: pivot(ax, f["P1"]); pivot(ax, f["P2"])
            pivot(ax, M["B"], ground=True)
        ax.set_xlim(-0.12, 0.58); ax.set_ylim(-0.02, 0.90); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(title, fontsize=19, color=INK if "采用" not in title else OR, fontweight="bold" if "采用" in title else "normal", pad=4)
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.02, top=0.90, wspace=0.05); fig.savefig(os.path.join(OUT, "md_candidates.png"), facecolor="white"); plt.close(fig)
    # sanity: the one-side four-bar re-simulated here should match its stored path error roughly
    Qd = np.array(P["design_curve"]["poses"]["Q"]); Qo = np.array([f["Q"] for f in os_frames])
    err = max(np.hypot(*(Qo - q).T).min() for q in Qd[Qd[:, 1] <= Qo[:, 1].max()])
    print(f"one-side four-bar: {len(os_frames)} frames, top {Qo[-1, 1]:.3f} m, max dev from design curve {err * 1000:.0f} mm (stored {osd['centre_err_mm']})")


# ---------------------------------------------------------------- C: synthesis (c1 traces a line -> rail, c2 traces an arc -> link)
def fig_synthesis():
    fr = M["frames"]; P1 = np.array([f["P1"] for f in fr]); P2 = np.array([f["P2"] for f in fr]); Q = np.array([f["Q"] for f in fr])
    B = np.array(M["B"]); lo, hi = np.array(M["rail_lo"]), np.array(M["rail_hi"])
    fig, ax = plt.subplots(figsize=(7.6, 6.6), dpi=220); bed(ax, -0.12)
    ax.plot([-0.12, 0.6], [0, 0], color=G2, lw=1.2, zorder=0)
    ax.plot([lo[0], hi[0]], [lo[1], hi[1]], color=BLUE, lw=9, alpha=0.25, solid_capstyle="round", zorder=1)
    ax.plot(P1[:, 0], P1[:, 1], color=BLUE, lw=2.6, zorder=3)
    ang = np.arctan2(*(P2 - B).T[::-1]); a0, a1 = ang.min() - 0.08, ang.max() + 0.08; t = np.linspace(a0, a1, 60)
    ax.plot(B[0] + M["link"] * np.cos(t), B[1] + M["link"] * np.sin(t), color=GREEN, lw=1.0, ls=(0, (3, 2)), zorder=2)
    ax.plot(P2[:, 0], P2[:, 1], color=GREEN, lw=2.6, zorder=3)
    ax.plot(Q[:, 0], Q[:, 1], color=OR, lw=2.0, ls=(0, (4, 2)), zorder=3)
    idx = [0, len(fr) // 2, len(fr) - 1]
    for k, i in enumerate(idx):
        al = 1.0 if k == 0 else 0.45 if k == 1 else 0.3; f = fr[i]
        plate(ax, f, M["c1"], M["c2"], al, z=4)
        ax.plot([B[0], f["P2"][0]], [B[1], f["P2"][1]], color=INK, lw=2.2, alpha=al, zorder=6)
        ax.add_patch(Rectangle((f["P1"][0] - 0.022, f["P1"][1] - 0.022), 0.044, 0.044, angle=0, fc=BLUE, ec=INK, lw=0.8, alpha=al, zorder=6))
        pivot(ax, f["P1"], z=7); pivot(ax, f["P2"], z=7)
    pivot(ax, B, ground=True, z=7)
    mid = lambda a: a[len(a) // 2]
    FS = 17
    ax.annotate("铰点 1：轨迹是直线\n→ 装滑块，走导轨", xy=mid(P1), xytext=(-0.115, 0.84), fontsize=FS, color=BLUE, arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.9))
    ax.annotate("铰点 2：轨迹是圆弧\n→ 连杆拉到 B", xy=mid(P2), xytext=(0.07, 0.02), fontsize=FS, color=GREEN, arrowprops=dict(arrowstyle="-", color=GREEN, lw=0.9))
    ax.text(B[0] + 0.012, B[1] + 0.025, "B", fontsize=FS, color=INK)
    ax.annotate("座板中心\n贴住设计曲线", xy=(Q[-8, 0], Q[-8, 1]), xytext=(0.36, 0.70), fontsize=FS, color=OR, arrowprops=dict(arrowstyle="-", color=OR, lw=0.9))
    ax.set_xlim(-0.12, 0.66); ax.set_ylim(-0.02, 0.92); ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "md_synthesis.png"), facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    fig_target(); fig_candidates(); fig_synthesis(); print("figures written to", OUT)
