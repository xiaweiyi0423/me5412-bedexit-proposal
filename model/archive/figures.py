"""Slide-ready figures (PNG, 200 dpi, light background)."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from model import Subject, STSConfig, SitUpConfig, sts_geometry, sts_effort

plt.rcParams.update({
    "font.family": "Inter", "font.size": 10,
    "axes.edgecolor": "#b5b3ad", "axes.labelcolor": "#52514e",
    "xtick.color": "#52514e", "ytick.color": "#52514e",
    "axes.titleweight": "semibold", "axes.titlesize": 11.5,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
    "savefig.facecolor": "#fcfcfb",
})
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
BLUE, ORANGE = "#2a78d6", "#eb6834"
GRAY_BAR = "#b5b3ad"
UNREACH = "#e7e6e2"
ramp = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("blue_seq", ramp)
VMIN, VMAX = 0.30, 1.00

sub, sc, uc = Subject(), STSConfig(), SitUpConfig()
d = np.load("maps.npz")
res = json.load(open("results.json"))
sens = json.load(open("sensitivity.json"))
g = sts_geometry(sub, sc)
edge = g["edge_x"]


def body_line(ax, pts, **kw):
    pts = np.array(pts)
    ax.plot(pts[:, 0], pts[:, 1], color=INK, lw=2.2, solid_capstyle="round", zorder=5, **kw)


# ============================================================================
# Figure 1: where should the handle be, per phase
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.9), gridspec_kw=dict(wspace=0.18))

# ---- Panel A: lie -> sit ---------------------------------------------------
ax = axes[0]
mattress_top = sc.bed_h
z_off = sc.bed_h + uc.hip_above_mattress          # phase-1 z -> floor height
E1 = d["E1"]
ax.set_facecolor(UNREACH)
X1, Z1 = np.meshgrid(d["xs1"], d["zs1"] + z_off)
im = ax.pcolormesh(X1, Z1, np.clip(E1, VMIN, VMAX), cmap=CMAP, vmin=VMIN, vmax=VMAX,
                   shading="nearest", rasterized=True)
m1 = np.nanmin(E1)
ax.contour(X1, Z1, np.nan_to_num(E1, nan=9), levels=[m1 * 1.05], colors=INK, linewidths=1.2,
           linestyles="--")
# bed + lying figure
ax.add_patch(Rectangle((-0.85, 0.0), 1.30, mattress_top, fc="#d9d8d4", ec="none", zorder=4))
H = np.array([0.0, z_off]); S = H + np.array([-sub.L_trunk, 0])
K = H + np.array([sub.L_thigh, 0]); A_ = K + np.array([sub.L_shank, 0])
body_line(ax, [S, H, K, A_])
ax.add_patch(plt.Circle(S + np.array([-0.12, 0.0]), 0.075, fc="#fcfcfb", ec=INK, lw=2.2, zorder=5))
P1 = np.array(res["situp_opt"]["P"]) + np.array([0, z_off])
ax.plot(*P1, marker="o", ms=9, mfc=ORANGE, mec="#fcfcfb", mew=2, zorder=6)
ax.annotate("best grip zone\n(within 5% of min)", xy=P1, xytext=(P1[0] + 0.12, P1[1] + 0.12),
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
ax.text(-0.82, 0.22, "bed", color=INK2, fontsize=9, zorder=6)
ax.set_xlim(-0.85, 0.45); ax.set_ylim(0.0, 1.35); ax.set_aspect("equal")
ax.set_xlabel("position along the bed, relative to hip (m)  →  feet")
ax.set_ylabel("height above floor (m)")
ax.set_title("Phase 1 · lie → sit (one hand, rail at bed edge)", loc="left", color=INK)
ax.text(0.02, 0.98, "grey = handle cannot help\n(out of reach, or sit-up not possible)",
        transform=ax.transAxes, va="top", fontsize=8.5, color=INK2)

# ---- Panel B: sit -> stand -------------------------------------------------
ax = axes[1]
E2 = d["E2"]
ax.set_facecolor(UNREACH)
X2, Z2 = np.meshgrid(d["xs2"] - edge, d["zs2"])
ax.pcolormesh(X2, Z2, np.clip(E2, VMIN, VMAX), cmap=CMAP, vmin=VMIN, vmax=VMAX,
              shading="nearest", rasterized=True)
m2 = np.nanmin(E2)
ax.contour(X2, Z2, np.nan_to_num(E2, nan=9), levels=[m2 * 1.05], colors=INK, linewidths=1.2,
           linestyles="--")
# bed block (behind edge), floor, figure at seat-off with example front handle
ax.add_patch(Rectangle((-0.75, 0.0), 0.75, sc.bed_h, fc="#d9d8d4", ec="none", zorder=4))
ax.text(-0.72, 0.22, "bed", color=INK2, fontsize=9, zorder=6)
Pex = np.array([0.35, 0.95])           # a practical point inside the plateau
det = sts_effort(sub, sc, Pex, 2, 0.0, return_detail=True)
th = np.radians(det["trunk_deg"])
Hp, K, A_ = g["Hp"], g["K"], g["A"]
S = Hp + sub.L_trunk * np.array([np.sin(th), np.cos(th)])
E = np.array(det["elbow"])
sh = lambda p: p - np.array([edge, 0])
body_line(ax, [sh(S), sh(Hp), sh(K), sh(A_), sh(A_) + np.array([0.15, -0.05])])
if E is not None:
    body_line(ax, [sh(S), sh(E), sh(Pex)])
head = sh(S) + 0.12 * np.array([np.sin(th), np.cos(th)])
ax.add_patch(plt.Circle(head, 0.075, fc="#fcfcfb", ec=INK, lw=2.2, zorder=5))
ax.plot(*sh(Pex), marker="o", ms=9, mfc=ORANGE, mec="#fcfcfb", mew=2, zorder=6)
# fixed edge rail
ax.plot([0.03, 0.03], [0.6, 1.1], color=INK2, lw=3, alpha=0.9, zorder=6, solid_capstyle="butt")
ax.annotate("fixed edge rail\n(beside hip)", xy=(0.03, 1.1), xytext=(-0.55, 1.2), fontsize=9,
            color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
ax.annotate("handle in front\n(two hands)", xy=sh(Pex), xytext=(0.55, 0.62), fontsize=9,
            color=INK, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
ax.set_xlim(-0.75, 0.95); ax.set_ylim(0.0, 1.35); ax.set_aspect("equal")
ax.set_xlabel("distance in front of bed edge (m)")
ax.set_title("Phase 2 · sit → stand (handle in front, two hands)", loc="left", color=INK)

cb = fig.colorbar(im, ax=axes, shrink=0.78, pad=0.015, extend="max")
cb.set_label("effort = share of max strength used\nby the hardest-working joint", color=INK2)
cb.outline.set_visible(False)
fig.savefig("fig1_handle_maps.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================================
# Figure 2: the comparison that justifies a phase-matched handle
# ============================================================================
bf = res["best_fixed_rail"]; mt = res["matched"]
none2 = res["sts_no_handle"]["effort"]
rows = [  # (label, phase1, phase2, color)
    ("No handle", None, none2, GRAY_BAR),
    (f"Best single fixed edge rail\n(h = {bf['h']:.2f} m)", bf["effort_phase1"], bf["effort_phase2"], GRAY_BAR),
    ("Phase-matched handle\n(edge for lie→sit, front for sit→stand)", mt["effort_phase1"],
     mt["effort_phase2_two_hands"], BLUE),
]
fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.3), sharey=True, gridspec_kw=dict(wspace=0.08))
for k, (ax, title) in enumerate(zip(axes, ["Phase 1 · lie → sit", "Phase 2 · sit → stand"])):
    for i, (lab, e1, e2, col) in enumerate(rows):
        v = e1 if k == 0 else e2
        y = len(rows) - 1 - i
        if v is None:
            ax.text(0.01, y, "not possible — legs lift off the mattress", va="center",
                    fontsize=9.5, color=INK2)
            continue
        ax.barh(y, v, height=0.56, color=col, edgecolor="none")
        ax.text(v + 0.012, y, f"{v:.2f}", va="center", fontsize=10, color=INK)
    ax.set_xlim(0, 0.75)
    ax.set_title(title, loc="left", color=INK)
    ax.grid(axis="x", color="#ebeae6", lw=0.8); ax.set_axisbelow(True)
    for sp in ["top", "right", "left"]:
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("effort (lower is easier)")
axes[0].set_yticks(range(len(rows)))
axes[0].set_yticklabels([r[0] for r in rows][::-1])
red = 1 - mt["effort_phase2_two_hands"] / bf["effort_phase2"]
axes[1].text(0.74, 0.02, f"{red:.0%} less effort than the\nbest fixed rail",
             transform=axes[1].transData, ha="right", va="bottom", fontsize=9, color=BLUE,
             fontweight="semibold")
fig.savefig("fig2_comparison.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ============================================================================
# Figure 3: sensitivity — does "front beats edge rail" survive the assumptions?
# ============================================================================
names = {
    "baseline": "Baseline (60 kg, 1.60 m, bed 0.48 m)",
    "hand_cap_20pct": "Hand load cap 20% BW",
    "hand_cap_40pct": "Hand load cap 40% BW",
    "weak_legs_x0.6": "Legs 40% weaker",
    "weak_arms_x0.7": "Arms 30% weaker",
    "low_bed_0.42": "Low bed 0.42 m",
    "high_bed_0.55": "High bed 0.55 m",
    "larger_person_75kg_1.70m": "Larger person 75 kg, 1.70 m",
}
fig, ax = plt.subplots(figsize=(8.2, 4.2))
keys = list(names)
for i, k in enumerate(keys):
    y = len(keys) - 1 - i
    r = sens[k]
    ax.plot([r["front2"], r["side_best"]], [y, y], color="#d9d8d4", lw=2, zorder=1)
    ax.scatter(r["side_best"], y, s=70, color=GRAY_BAR, edgecolor="#fcfcfb", lw=1.5, zorder=3,
               label="best fixed edge rail (any height)" if i == 0 else None)
    ax.scatter(r["front2"], y, s=70, color=BLUE, edgecolor="#fcfcfb", lw=1.5, zorder=3,
               label="handle in front (two hands)" if i == 0 else None)
    ax.text(0.80, y, f"−{1 - r['front2'] / r['side_best']:.0%}", va="center", ha="right",
            fontsize=9.5, color=INK)
ax.set_yticks(range(len(keys))); ax.set_yticklabels([names[k] for k in keys][::-1])
ax.set_xlim(0.2, 0.82); ax.set_xlabel("sit → stand effort (lower is easier)")
ax.text(0.80, len(keys) - 0.35, "front vs rail", ha="right", fontsize=8.5, color=INK2)
for sp in ["top", "right", "left"]:
    ax.spines[sp].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color="#ebeae6", lw=0.8); ax.set_axisbelow(True)
ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False, fontsize=9)
fig.savefig("fig3_sensitivity.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("ok")
