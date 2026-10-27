"""v5.4 controller simulation for the inclined-rail seat (replaces controller_v13.py, which simulated the vertical lift).

Plant: one DOF. The seat moves along the slider curve; state = seat height h (0.412 .. 0.69 m), tilt phi(h) from the
curve. Speeds are vertical seat speeds (cm/s), as before.
User: the reference user (1.60 m) of seat_support_slider.json. While trying to rise, a user whose strongest effort is c
brings the seat force (along the seat normal) down towards min_seat(h, c) over rise_T seconds; seat-off when it reaches 0.
Rules (v5.3, after the deck audit; differences from controller_v13 marked *):
  * speed v = clip(k (F_cap - F_seat_vert), 0, v_max), F_seat_vert = filtered normal force x cos(phi(h)) (encoder gives h)
  * interlock: if the bar carries more than 0.30 BW downward (user hanging on it), speed is limited to 0.3 v_max
  * sensor check: seat (x cos phi) + footplate + bar (signed) = BW within 15 %, only while lifting / lowering someone
    above flush, for 0.5 s -> LOCKED (only held DOWN, slow). No base-corner weighing. (Idle tare check not simulated.)
  * no automatic lowering of a seated user: seated or stopped with no input -> alert after 17 s (chime + call), no motion
  * lowering a seated user only while DOWN is held; the empty seat moves only while UP / DOWN is held (EMPTY_MOVE)
  * no column-sync check (one screw)
  * return to bed (v5.5): the empty seat, held DOWN, pauses at the personal return height (default 0.50 m: sitting onto it
    costs about 20 % less effort than onto 0.42 m); seated, the user holds DOWN again to ride to flush
  * 'still sitting' threshold 0.10 BW (was 0.15): on the seat a user mid-rise can be down to 0.15 BW and must still be able to resume
  power loss: brake holds; held DOWN lowers on the battery at half speed.
Output: controller_seat.json, controller_seat_all.png (all scenarios), controller_seat_main.png (three for the slide).
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
for f in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",):
    if os.path.exists(f): font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__)); g = 9.81; DT = 0.02
SS = json.load(open(os.path.join(HERE, "seat_1dof", "seat_support_slider.json")))
CAPS = np.array(SS["caps"]); ROWS = SS["rows"]; H0 = ROWS[0]["h"]; H1 = SS["top"]; HREL = SS["release"]["h"]; EFREE_REL = SS["release"]["E_free"]
HC, PC = np.array(SS["curve"]["h"]), np.array(SS["curve"]["phi"])
def phi_of(h): return float(np.interp(h, HC, PC))

def _min_cap(E, c):
    """least seat force (x BW, along the normal) with effort <= c for one row: E[j] = least effort with seat force <= CAPS[j]."""
    e = np.array([np.inf if x is None else x for x in E]); e = np.minimum.accumulate(e)      # more allowed force never costs more
    if e[0] <= c: return 0.0
    if e[-1] > c: return float(CAPS[-1])
    j = int(np.argmax(e <= c)); a, b = e[j - 1], e[j]
    return float(CAPS[j - 1] + (CAPS[j] - CAPS[j - 1]) * (a - c) / (a - b))
HS = np.array([r["h"] for r in ROWS])
def min_seat(h, c):
    if h >= HREL - 1e-4:                       # past the last supported pose: the seat no longer reaches the buttock
        return 0.0 if EFREE_REL <= c else _min_cap(ROWS[-1]["E"], c)
    v = [_min_cap(r["E"], c) for r in ROWS]
    return float(np.interp(h, HS, v))

class Params:
    def __init__(self, bw_kg=60.0, cap=0.5, vmax=0.03, ret_h=0.50):
        self.BW = bw_kg * g; self.F_cap = cap * self.BW; self.vmax = vmax; self.k = vmax / (0.35 * self.BW)
        self.a_max = 0.05; self.v_down = 0.02; self.v_empty = 0.015
        self.seated_thr = 0.40 * self.BW; self.occ_stay = 0.10 * self.BW; self.seatoff_thr = 0.05 * self.BW; self.feet_thr = 0.30 * self.BW
        self.grip_thr = 20.0; self.sum_tol = 0.15; self.sum_persist = 0.5; self.stall_t = 2.0; self.alert_t = 17.0
        self.empty_t = 5.0; self.stand_persist = 0.3; self.ret_h = ret_h; self.tau_f = 0.08; self.hang = 0.30 * self.BW

class Controller:
    def __init__(self, P, h=H0, state="IDLE"):
        self.P = P; self.state = state; self.h = h; self.v = 0.0; self.t_in = 0.0
        self.t_stall = self.t_seatoff = self.t_empty = self.t_idle = self.t_top = self.t_sum = self.t_stand = 0.0
        self.prev_grip = False; self.prev_down = False; self.alert = False; self.events = []; self.fs_f = None; self.paused = False; self.limited = False
    def go(self, s, msg=""):
        if s != self.state: self.state, self.t_in = s, 0.0; self.events.append((s, msg))
    def step(self, z, t):
        P = self.P; self.t_in += DT; v_cmd = 0.0; self.alert = False; self.limited = False
        cphi = np.cos(np.radians(phi_of(self.h))); fs_v = z["F_seat"] * cphi
        self.fs_f = fs_v if self.fs_f is None else self.fs_f + (fs_v - self.fs_f) * DT / P.tau_f
        stay = self.state in ("SEATED", "LOWERING", "STOPPED")
        occupied = z["F_seat"] > (P.occ_stay if stay else P.seated_thr)
        total = fs_v + z["F_feet"] + z["F_bar"]
        check = ((self.state == "LIFTING") or (self.state == "LOWERING" and occupied)) and self.h > H0 + 0.03
        self.t_sum = self.t_sum + DT if (check and abs(total - P.BW) / P.BW > P.sum_tol) else 0.0
        grip_edge = z["grip"] and not self.prev_grip; self.prev_grip = z["grip"]
        down_edge = z["down"] and not self.prev_down; self.prev_down = z["down"]
        bar_mag = abs(z["F_bar"]); ready = z["grip"] and bar_mag > P.grip_thr and z["F_feet"] > P.feet_thr and z["cop_ok"]
        if not z["power"] and self.state not in ("STOPPED", "LOCKED"): self.go("STOPPED", "断电：制动抱住；按住“降”用电池慢降")
        if self.t_sum > P.sum_persist and self.state != "LOCKED": self.go("LOCKED", "自检不过：锁定，只能按住“降”慢降")
        s = self.state
        if s == "IDLE":
            if occupied: self.go("SEATED")
        elif s == "SEATED":
            if z["F_seat"] < P.seatoff_thr and z["F_feet"] < P.feet_thr: self.go("IDLE" if self.h <= H0 + 1e-3 else "EMPTY_HOLD")
            elif ready and self.t_in > 0.5 and self.h < H1 - 1e-3: self.go("LIFTING")
            elif z["down"] and self.h > H0 + 1e-3 and z["cop_ok"]: self.go("LOWERING", "按住“降”：带人慢慢降")
            elif self.h > H0 + 1e-3:
                self.t_idle = self.t_idle + DT if not (z["grip"] or z["down"]) else 0.0
                self.alert = self.t_idle > P.alert_t
        elif s == "LIFTING":
            if not z["grip"] or bar_mag < P.grip_thr or not z["cop_ok"] or z["F_feet"] < P.feet_thr:
                self.go("STOPPED", "松手或条件不满足：停住并制动")
            else:
                v_cmd = float(np.clip(P.k * (P.F_cap - self.fs_f), 0, P.vmax))
                if z["F_bar"] > P.hang: v_cmd = min(v_cmd, 0.3 * P.vmax); self.limited = True
                if self.h >= H1 - 1e-4: v_cmd = 0.0
                self.t_stall = self.t_stall + DT if (v_cmd == 0.0 and self.h < H1 - 1e-4 and occupied) else 0.0
                self.t_seatoff = self.t_seatoff + DT if z["F_seat"] < P.seatoff_thr else 0.0
                self.t_top = self.t_top + DT if self.h >= H1 - 1e-4 else 0.0
                if self.t_seatoff > P.stand_persist: self.go("STANDING_HOLD", "离座：座板停在放手处")
                elif self.t_stall > P.stall_t: self.go("STOPPED", "到推力上限仍不动：停住")
                elif self.t_top > 2 * P.stall_t: self.go("STOPPED", "到顶仍未离座：停住")
        elif s == "STOPPED":
            self.t_stand = self.t_stand + DT if (z["F_seat"] < P.seatoff_thr and z["F_feet"] > P.feet_thr) else 0.0
            if not z["power"]:
                if z["down"]: v_cmd = -P.v_down * 0.5
            elif self.t_stand > P.stand_persist: self.go("STANDING_HOLD")
            elif occupied and grip_edge and ready and self.h < H1 - 1e-3: self.go("LIFTING")
            elif occupied and z["down"] and z["cop_ok"]: self.go("LOWERING", "有人坐着，按住“降”：带人慢慢降")
            elif occupied and not (z["grip"] or z["down"]): self.t_idle += DT; self.alert = self.t_idle > P.alert_t
            elif not occupied and z["F_feet"] < 0.05 * P.BW and self.t_in > P.empty_t: self.go("EMPTY_HOLD")
            if z["grip"] or z["down"]: self.t_idle = 0.0
        elif s == "STANDING_HOLD":
            if z["F_seat"] > P.seated_thr and self.t_in > 0.5: self.go("SEATED", "坐回：座板停住接人")
            self.t_empty = self.t_empty + DT if (z["F_seat"] < P.seatoff_thr and z["F_feet"] < 0.05 * P.BW) else 0.0
            if self.t_empty > P.empty_t: self.go("EMPTY_HOLD", "人已离开：座板停在原处")
        elif s == "EMPTY_HOLD":
            if occupied: self.go("SEATED", "有人坐上座板")
            elif (z.get("up") or down_edge) and z["F_seat"] < P.seatoff_thr: self.paused = False; self.go("EMPTY_MOVE")
        elif s == "EMPTY_MOVE":
            if z["F_seat"] > P.seatoff_thr: self.go("EMPTY_HOLD", "空座板移动时受力：停住")
            elif z.get("up"): v_cmd = P.v_empty if self.h < H1 - 1e-3 else 0.0
            elif z["down"]:
                stop_at = P.ret_h if (P.ret_h > H0 + 1e-3 and not self.paused and self.h > P.ret_h - 2e-3) else H0
                if self.h > stop_at + 1e-4: v_cmd = -P.v_empty
                else:
                    if stop_at > H0 + 1e-3: self.paused = True
                    self.go("EMPTY_HOLD", "到回床高度" if stop_at > H0 + 1e-3 else "到床面")
            else: self.go("EMPTY_HOLD")
        elif s == "LOWERING":
            if not occupied: self.go("STOPPED", "下降中座板卸载：停住")
            elif not z["cop_ok"]: self.go("STOPPED", "下降中压力中心偏出：停住")
            elif not z["down"]: self.go("STOPPED", "松开“降”：停住")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("SEATED", "到床面"); v_cmd = 0.0
        elif s == "LOCKED":
            if z["down"] and z["power"]: v_cmd = -P.v_down * 0.5
        dv = np.clip(v_cmd - self.v, -P.a_max * DT, P.a_max * DT)
        self.v = v_cmd if v_cmd == 0.0 else self.v + dv
        self.h = float(np.clip(self.h + self.v * DT, H0, H1))

def sc(key, name, c=0.28, T=40.0, rise_T=3.0, h0=H0, state0="IDLE", ret_h=0.50, **ev):
    return dict(key=key, name=name, c=c, T=T, rise_T=rise_T, h0=h0, state0=state0, ret_h=ret_h, ev=ev)
def hold(*spans): return lambda t: any(a <= t < b for a, b in spans)

SCEN = [
 sc("typical", "典型用户（最多发力 0.28）", c=0.28),
 sc("weakest", "刚好站得起来的用户（0.27）", c=0.27),
 sc("strong", "力气较大的用户（0.32）", c=0.32),
 sc("tooweak", "站不起来的用户（0.24）：停住，按住“降”回床面", c=0.24, T=60.0, sitback=36.0, down=hold((40.0, 60.0))),
 sc("sitback", "抬升中往回坐：停住接人", sitback=8.0, T=30.0),
 sc("faint", "抬升中晕倒、松手：停住接人，17 s 后提醒呼叫，不自己降", release=8.0, sitback=8.0, T=40.0),
 sc("mattress", "坐上时大腿还压在床垫上（0.2 倍体重）", mattress=0.2),
 sc("stepoff", "站起后一只脚先踩到地上，再离开", stepoff=True, T=30.0),
 sc("pullup", "起身时双手往上拉横杆（0.2 倍体重）", pull=0.2),
 sc("hang", "把体重压在横杆上（0.4 倍体重）：只按 30% 速度升；借横杆离座后座板停住接人", hang=0.4, T=40.0),
 sc("cop", "抬升中坐偏 1 s，重新握紧后继续", cop_off=(6.5, 7.5), regrip=(8.0, 8.5)),
 sc("return", "回床（默认回床高度 0.50 m）：按住“降”，空座板停在 0.50 m；坐上后再按住“降”降到床面", h0=0.57, state0="EMPTY_HOLD", ret="mid", T=36.0),
 sc("return_flush", "回床高度设成床面：按住“降”让空座板降到床面，再坐下挪回床上", h0=0.57, state0="EMPTY_HOLD", ret="flush", ret_h=H0, T=36.0),
 sc("stuck", "踏板传感器卡在高读数：锁定，按住“降”慢降", feet_stuck=6.0, down=hold((12.0, 40.0))),
 sc("power", "抬升中断电：按住“降”用电池慢降", power_off=7.0, down=hold((12.0, 45.0)), T=45.0),
]

def run(s):
    P = Params(vmax=0.03, ret_h=s["ret_h"]); C = Controller(P, h=s["h0"], state=s["state0"]); ev = s["ev"]; BW = P.BW; s0 = 0.79
    log = {k: [] for k in ("t", "h", "seat", "feet", "bar", "state", "alert", "limited")}; t_so = None; F_seat = 0.0
    for i in range(int(s["T"] / DT)):
        t = i * DT; cop_ok = True
        cphi = np.cos(np.radians(phi_of(C.h)))
        mat = ev.get("mattress", 0.0) if C.h < H0 + 0.02 else 0.0
        if ev.get("ret"):
            mid = ev["ret"] == "mid"; sit_t = 11.5 if mid else 16.0
            if t < 1.0: F_seat, F_feet, F_bar = 0.0, 0.0, 0.0; down = False
            elif t < sit_t: F_seat, F_bar = 0.0, 0.1 * BW; F_feet = BW - F_bar; down = 2.0 <= t < sit_t - 0.5
            elif t < sit_t + 1.0: F_bar = 0.05 * BW; F_seat = (t - sit_t) * 0.6 * BW; F_feet = BW - F_seat * cphi - F_bar; down = False
            else:
                F_bar = 0.05 * BW; down = mid and ((13.0 <= t < 14.5) or (15.5 <= t < 22.0))      # hold, let go once, hold again
                share = min(1.0, max(0.0, (t - (24.0 if mid else 22.0)) / 4.0)) if C.h <= H0 + 1e-3 else 0.0
                F_seat = 0.6 * BW * (1 - share); F_bar *= (1 - share); F_feet = max(0.0, BW - F_seat * cphi - F_bar - share * BW * 0.9)
            z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, grip=False, down=down, cop_ok=True, power=True)
        else:
            on = t >= 1.0; trying = t >= 3.0 and not (ev.get("sitback") and t >= ev["sitback"])
            e = min(1.0, max(0.0, (t - 3.0) / s["rise_T"])) if trying else 0.0
            target = min_seat(C.h, s["c"])
            if ev.get("hang") and trying: target = max(0.0, target - ev["hang"])       # weight goes to the bar, not the feet
            if on:
                frac = s0 - mat - e * (s0 - mat - target)
                if C.state == "STANDING_HOLD" and trying: frac = 0.0
                F_seat = max(0.0, frac) * BW
            else: F_seat = 0.0
            hands = t >= 3.0 and not (ev.get("release") and t >= ev["release"])
            if hands: F_bar = -ev["pull"] * BW if ev.get("pull") else (ev["hang"] * BW * e if ev.get("hang") else 60.0)
            else: F_bar = 0.0
            F_feet = (BW - F_seat * cphi - F_bar - mat * BW) if on else 0.0
            if ev.get("stepoff") and t_so is not None:
                if t > t_so + 3.0: F_bar = 0.0; F_feet = 0.5 * BW
                if t > t_so + 4.5: F_feet = 0.0
            if ev.get("feet_stuck") and t >= ev["feet_stuck"]: F_feet = 1.3 * BW
            if ev.get("cop_off") and ev["cop_off"][0] <= t < ev["cop_off"][1]: cop_ok = False
            grip = hands and not (ev.get("regrip") and ev["regrip"][0] <= t < ev["regrip"][1])
            dfun = ev.get("down")
            z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, grip=grip, cop_ok=cop_ok, down=bool(dfun and dfun(t)),
                     power=not (ev.get("power_off") and t >= ev["power_off"]))
        C.step(z, t)
        if C.state == "STANDING_HOLD" and t_so is None: t_so = t
        for k, v in (("t", t), ("h", C.h), ("seat", z["F_seat"] / BW), ("feet", z["F_feet"] / BW), ("bar", z["F_bar"] / BW), ("state", C.state),
                     ("alert", C.alert), ("limited", C.limited)):
            log[k].append(v)
    res = dict(key=s["key"], name=s["name"], c=s["c"], final_state=C.state, final_height=round(C.h, 3), max_height=round(max(log["h"]), 3),
               seat_off_height=None if t_so is None else round(log["h"][int(t_so / DT)], 3), seat_off_time_s=None if t_so is None else round(t_so - 3.0, 1),
               alert_from_s=next((round(log["t"][i], 1) for i, a in enumerate(log["alert"]) if a), None), speed_limited=any(log["limited"]), events=C.events)
    return log, res

STATES = ["IDLE", "SEATED", "LIFTING", "STOPPED", "STANDING_HOLD", "LOWERING", "EMPTY_HOLD", "EMPTY_MOVE", "LOCKED"]
CN = dict(IDLE="待机", SEATED="已坐上", LIFTING="抬升", STOPPED="停住", STANDING_HOLD="站立保持", LOWERING="下降", EMPTY_HOLD="空座板停住", EMPTY_MOVE="空座板移动", LOCKED="锁定")
COL = dict(IDLE="#c3c9d1", SEATED="#3f6fc4", LIFTING="#1f9e6e", STOPPED="#c8780c", STANDING_HOLD="#7a56c2", LOWERING="#b39400",
           EMPTY_HOLD="#6b7a8f", EMPTY_MOVE="#9aa6b8", LOCKED="#c0392b")

def panel(ax, s, lg, big=False):
    t = np.array(lg["t"]); fs = 21 if big else 11
    ax.plot(t, lg["h"], color="#18202a", lw=2.6 if big else 2)
    ax2 = ax.twinx(); ax2.plot(t, lg["seat"], color="#c8602a", lw=2 if big else 1.4); ax2.set_ylim(0, 1.05); ax2.axhline(0.5, ls=":", color="#c8602a", lw=1)
    ax2.tick_params(labelsize=fs - 2, colors="#c8602a")
    st = lg["state"]; j0 = 0
    for j in range(1, len(st) + 1):
        if j == len(st) or st[j] != st[j0]: ax.axvspan(t[j0], t[j - 1], ymin=0, ymax=0.07, color=COL[st[j0]], lw=0); j0 = j
    al = [x for x, a in zip(t, lg["alert"]) if a]
    if al: ax.axvspan(al[0], al[-1], ymin=0.93, ymax=1.0, color="#c0392b", alpha=0.35, lw=0); ax.text(al[0] + 0.3, 0.685, "提醒、呼叫家属", fontsize=fs - 2, color="#c0392b", va="top")
    ax.set_title(s["name"], fontsize=fs, loc="left"); ax.set_ylim(0.38, 0.71); ax.tick_params(labelsize=fs - 2); ax.grid(alpha=0.25)
    if big: ax.set_ylabel("座高 (m)", fontsize=fs - 2); ax2.set_ylabel("座板受力（×体重）", fontsize=fs - 3, color="#c8602a")

def legend(fig, fs, y):
    from matplotlib.patches import Patch
    hs = [Patch(color=COL[k], label=CN[k]) for k in STATES if k != "EMPTY_MOVE"]
    fig.legend(handles=hs, loc="lower center", ncol=4, fontsize=fs, frameon=False, bbox_to_anchor=(0.5, y))

if __name__ == "__main__":
    out = dict(note=__doc__.strip().split("\n")[0], user=SS["user"], release_h=HREL, E_free_release=EFREE_REL, top=H1,
               params=dict(cap_BW=0.5, vmax_cm_s=3.0, k="vmax / (0.35 BW)", hang_limit_BW=0.30, sum_tol=0.15, sum_persist_s=0.5, alert_s=17,
                           v_down=0.02, v_empty=0.015, occupied_enter_BW=0.40, occupied_stay_BW=0.10), scenarios=[])
    logs = {}
    for s in SCEN:
        lg, r = run(s); logs[s["key"]] = (s, lg)
        r["series"] = {k: ([round(float(x), 3) for x in lg[k][::10]] if k not in ("state",) else lg[k][::10]) for k in ("t", "h", "seat", "feet", "bar", "state")}
        out["scenarios"].append(r)
        print(f"{s['key']:9s} final={r['final_state']:13s} h={r['final_height']:.3f} max={r['max_height']:.3f} seat-off h={r['seat_off_height']} t={r['seat_off_time_s']} alert={r['alert_from_s']} limited={r['speed_limited']}")
    json.dump(out, open(os.path.join(HERE, "controller_seat.json"), "w"), ensure_ascii=False)
    fig, axs = plt.subplots(5, 3, figsize=(16, 18))
    for ax, s in zip(axs.flat, SCEN): panel(ax, *logs[s["key"]])
    for ax in axs.flat[len(SCEN):]: ax.axis("off")
    fig.suptitle("坐板控制仿真（1.60 m 用户）：座板高度（黑，m）、座板受力（橙，× 体重；虚线 = 推力上限 0.5）、控制状态（底部色带）", fontsize=14)
    legend(fig, 12, 0.0); fig.tight_layout(rect=(0, 0.05, 1, 0.98)); fig.savefig(os.path.join(HERE, "controller_seat_all.png"), dpi=110); plt.close(fig)
    fig, axs = plt.subplots(3, 1, figsize=(10.5, 11.5))
    for ax, k in zip(axs, ("typical", "faint", "power")): panel(ax, *logs[k], big=True)
    axs[-1].set_xlabel("时间 (s)", fontsize=19); legend(fig, 18, 0.0); fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(os.path.join(HERE, "controller_seat_main.png"), dpi=120); plt.close(fig)
