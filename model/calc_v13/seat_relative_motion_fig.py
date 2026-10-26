"""Figures for seat_relative_motion.py: sagittal stage-by-stage sketch and the relative-motion curves for 27 users."""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import seat_trajectory as ST
from seat_relative_motion import *
from model import arm_ik_all, shoulder_ok

for f in ["/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(f): font_manager.fontManager.addfont(f); plt.rcParams["font.family"] = "WenQuanYi Zen Hei"
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
INK = "#1f2328"; MUTED = "#8a9099"; BODY = "#c9b8a6"; SEAT = "#3b6ea8"; GOOD = "#2e7d4f"; BAD = "#c0392b"; BED = "#e3ddd3"

FIT_REF = (1.60, 0.33, 0.6)      # the one-DOF curve is fitted to the user whose hip moves forward earliest
maps = {tuple(json.loads(k)): v for k, v in json.load(open(os.path.join(OUT, "maps.json"))).items()}

def designs():
    _, ref = rise(*FIT_REF)
    return [("V：竖直升降，座面水平（现方案）", dict(curve=curve_vertical(), seat=Seat(), amax=0.12, follow=False, kind="V")),
            ("1-DOF：沿固定曲线前移+上升+前倾≤30°\n（曲线按'最早前移'的人拟合，前缘加长托腿垫）",
             dict(curve=curve_fit(ref, 30), seat=Seat(), amax=0.18, follow=False, kind="FIT"))]

def run(user, d):
    ST.A_MAX = d["amax"]; sub, path = rise(*user)
    rows = track(sub, path, d["seat"], d["curve"], follow=d["follow"]); return sub, path, rows

def trunk_for(user, hz, s):
    m = maps[(user[0], user[1])]; hzs = np.array(m["hz"]); i = int(np.argmin(abs(hzs - hz))); j = int(np.argmin(abs(S_GRID - s)))
    t = m["trunk0"][i][j]; return 20.0 if t < 0 else float(t)

def draw_person(ax, sub, pz, user, hz):
    A, K, Hp = pz["A"], pz["K"], pz["Hp"]
    s = np.degrees(np.arctan2(K[0] - A[0], K[1] - A[1])); th = np.radians(trunk_for(user, hz, s))
    uT = np.array([np.sin(th), np.cos(th)]); S = Hp + sub.L_trunk * uT; head = S + 0.11 * uT
    foot = sub.foot_len; heel, toe = np.array([A[0] - 0.25 * foot, 0.0]), np.array([A[0] + 0.75 * foot, 0.0])
    ax.fill([heel[0], toe[0], A[0] + 0.02, A[0] - 0.03], [0.0, 0.0, A[1] + 0.02, A[1] + 0.02], color=BODY, lw=0)
    # back outline: buttock arc + back of thigh (the surface the seat touches), then a simple body band
    pts, kind, aa = body_points(pz)
    u = pz["u"]; n = np.array([-u[1], u[0]])          # front of thigh
    back = pts[aa <= 0.30]
    poly = np.vstack([back, K - 0.045 * n, K + 0.05 * n, Hp + 0.07 * n + 0.05 * uT])
    ax.fill(poly[:, 0], poly[:, 1], color=BODY, lw=0, zorder=2)
    ax.plot(back[:, 0], back[:, 1], color="#8c6f55", lw=0.8, zorder=3)
    ax.plot(*np.array([A, K]).T, color=BODY, lw=7, solid_capstyle="round", zorder=2)
    ax.plot(*np.array([Hp, S]).T, color=BODY, lw=13, solid_capstyle="round", zorder=2)
    ax.add_patch(plt.Circle(head, 0.085, color=BODY, zorder=2))
    P = bar_at(hz); Es = [E for E in arm_ik_all(S, P, sub.L_uarm, sub.L_farm) if shoulder_ok(S, E, uT)]
    if Es: ax.plot(*np.array([S, Es[0], P]).T, color="#a8927c", lw=3.5, solid_capstyle="round", zorder=4)
    ax.add_patch(plt.Circle(P, 0.018, color=INK, zorder=5))
    ax.plot(*np.array([A, K, Hp]).T, "o", ms=2.2, color="#6b5a49", zorder=5)

def draw_seat(ax, seat, Q, phi, kind, curve):
    xs = np.linspace(-seat.h, seat.h, 60); top = np.stack([xs, seat.top(xs)], 1)
    bot = np.array([[seat.h - 0.01, -seat.t], [-seat.h, -seat.t]])
    loc = np.vstack([top, bot]); Rm = rot(phi); W = Q + loc @ Rm.T
    ax.fill(W[:, 0], W[:, 1], color=SEAT, alpha=0.9, lw=0, zorder=6)
    if kind == "V":
        ax.plot([Q[0], Q[0]], [Q[1] - seat.t, 0.0], color=SEAT, lw=3, alpha=0.35, zorder=1)
    else:
        ax.plot(curve[1][:, 0], curve[1][:, 1], ls=(0, (2, 2)), color=SEAT, lw=0.9, alpha=0.7, zorder=1)

def stage_panel(ax, sub, path, rows, user, idx, d, label):
    r = rows[idx]; pz = path[idx]; hz = pz["Hp"][1]
    ax.fill([-0.40, 0.0, 0.0, -0.40], [0.0, 0.0, Z0, Z0], color=BED, lw=0, zorder=0)
    ax.text(-0.2, 0.36, "床", color=MUTED, ha="center", fontsize=8)
    ax.plot([-0.40, 0.90], [0, 0], color=INK, lw=0.8)
    draw_seat(ax, d["seat"], np.array(r["Q"]), r["phi"], d["kind"], d["curve"])
    draw_person(ax, sub, pz, user, hz)
    C = np.array(r["P"]); ok = r["ok"]
    ax.add_patch(plt.Circle(C, 0.013, color=GOOD if ok else BAD, zorder=8))
    # catch margin: seat front edge vs where the buttock lands if the user sits back now
    land = pz["Hp"][0] - SIT_BEHIND; fe = r["front_x"]; yb = 0.26
    col = GOOD if r["catch"] >= 0 else BAD
    ax.annotate("", xy=(fe, yb), xytext=(land, yb), arrowprops=dict(arrowstyle="<->", color=col, lw=1.2, shrinkA=0, shrinkB=0), zorder=9)
    ax.plot([land, land], [yb - 0.03, pz["Hp"][1] - R_B], color=col, lw=0.6, ls=":", zorder=9)
    ax.plot([fe, fe], [yb - 0.03, r["seat_top"] - 0.02], color=col, lw=0.6, ls=":", zorder=9)
    ax.text((fe + land) / 2, yb - 0.09, f"坐回余量 {100 * r['catch']:+.0f} cm", ha="center", color=col, fontsize=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85), zorder=10)
    ax.text(-0.37, 1.40, label, fontsize=8.5, color=INK, va="top", fontweight="bold")
    ax.text(-0.37, 1.33, f"髋高 {hz:.2f} m   座面前倾 {r['phi']:.0f}°\n"
                         f"累计前滑 {100 * r['slip']:+.1f} cm\n接触长度 {100 * r['contact_len']:.0f} cm",
            fontsize=7.5, color=INK, va="top", linespacing=1.4)
    ax.set_xlim(-0.40, 0.88); ax.set_ylim(-0.02, 1.42); ax.set_aspect("equal"); ax.axis("off")

def fig_stages(user=(1.60, 0.29, 1.0), name="stages_typical"):
    D = designs(); fig, axes = plt.subplots(len(D), 5, figsize=(15, 3.9 * len(D) + 0.6))
    for row, (title, d) in enumerate(D):
        sub, path, rows = run(user, d)
        good = [i for i, r in enumerate(rows) if r.get("contact") and r.get("ok")]
        rel = good[-1]; picks = [0, int(rel * 0.33), int(rel * 0.66), rel]
        labels = ["① 坐姿（座面与床齐平）", "② 起身 1/3", "③ 起身 2/3", "④ 放手前最后支撑"]
        for c, (i, lab) in enumerate(zip(picks, labels)): stage_panel(axes[row, c], sub, path, rows, user, i, d, lab)
        ax = axes[row, 4]; hz = [r["hz"] for r in rows if r.get("contact") and r.get("ok")]
        sl = [100 * r["slip"] for r in rows if r.get("contact") and r.get("ok")]; ca = [100 * r["catch"] for r in rows if r.get("contact") and r.get("ok")]
        ax.axhline(0, color=MUTED, lw=0.6); ax.plot(hz, sl, color=BAD, lw=2, label="累计前滑（+ 人往前滑出座面；- 座板跑到人下面）")
        ax.plot(hz, ca, color=GOOD, lw=2, label="坐回余量（- = 坐回会落到前缘外）")
        ax.set_xlabel("髋高 (m)"); ax.set_ylabel("cm"); ax.set_ylim(-12, 12); ax.legend(fontsize=7, loc="lower left", frameon=False)
        ax.set_title("相对运动随起身变化", fontsize=8.5)
        fig.text(0.01, 1 - (row + 0.08) / len(D) * 0.93, title, fontsize=10.5, fontweight="bold", color=SEAT, va="top")
    fig.suptitle(f"矢状面：人与坐板的相对运动（身高 {user[0]:.2f} m，脚踝在床沿前 {user[1]:.2f} m，髋随起身匀速前移）", fontsize=11.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.965), h_pad=2.6)
    p = os.path.join(OUT, f"{name}.png"); fig.savefig(p, dpi=150); plt.close(fig); return p

def fig_users(name="users_27"):
    _, ref = rise(*FIT_REF)
    D = [("V 竖直升降（现方案）", dict(curve=curve_vertical(), seat=Seat(), amax=0.12, follow=False)),
         ("1-DOF 固定曲线 + 托腿垫", dict(curve=curve_fit(ref, 30), seat=Seat(), amax=0.18, follow=False)),
         ("实时跟随（3 自由度 + 传感，上限）", dict(curve=None, seat=Seat(), amax=0.12, follow=True))]
    STY = {0.6: "#c0392b", 1.0: "#3b6ea8", 2.5: "#7a7f87"}
    fig, axes = plt.subplots(3, 3, figsize=(13, 9), sharex=True)
    for c, (title, d) in enumerate(D):
        for user in PERSONS:
            dd = dict(d)
            if d["follow"]:
                _, own = rise(*user); dd["curve"] = curve_fit(own, 30)
            sub, path, rows = run(user, dd); g = [r for r in rows if r.get("contact") and r.get("ok")]
            f = [r["f"] for r in g]; col = STY[user[2]]
            axes[0, c].plot(f, [100 * r["slip"] for r in g], color=col, lw=0.9, alpha=0.75)
            axes[1, c].plot(f, [100 * r["catch"] for r in g], color=col, lw=0.9, alpha=0.75)
            axes[2, c].plot(f, [100 * r["contact_len"] for r in g], color=col, lw=0.9, alpha=0.75)
            for k in range(3): axes[k, c].plot(f[-1], [100 * g[-1]["slip"], 100 * g[-1]["catch"], 100 * g[-1]["contact_len"]][k], "o", ms=2.5, color=col)
        axes[0, c].set_title(title, fontsize=10, color=INK)
        for k in range(2): axes[k, c].axhline(0, color=INK, lw=0.6)
    axes[0, 0].set_ylabel("累计前滑 (cm)\n+ 人往前滑出座面 / - 座板跑到人下面"); axes[1, 0].set_ylabel("坐回余量 (cm)\n- = 坐回落到前缘外")
    axes[2, 0].set_ylabel("接触长度 (cm)\n座垫压缩 1.5 cm 内")
    for c in range(3): axes[2, c].set_xlabel("起身进度（0 = 坐，1 = 站直）；圆点 = 座板最后一次有效支撑")
    for k in range(3):
        for c in range(3): axes[k, c].set_ylim([(-14, 12), (-5, 12), (0, 14)][k])
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color=v, lw=2) for v in STY.values()], ["髋早前移（先前倾再起）", "髋匀速前移", "髋晚前移（先直上再前移）"],
               loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.995))
    fig.suptitle("27 位用户（身高 1.50/1.60/1.75 m × 脚位 0.25/0.29/0.33 m × 3 种起身习惯）", y=0.955, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    p = os.path.join(OUT, f"{name}.png"); fig.savefig(p, dpi=150); plt.close(fig); return p

if __name__ == "__main__":
    print(fig_stages()); print(fig_stages((1.60, 0.29, 0.6), "stages_leanfirst")); print(fig_users())
