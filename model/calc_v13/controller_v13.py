"""v13 controller for the rise station, with the changes from the 10/26 audit, and the same scenarios run under v12 rules.

Changes from calc_v12/controller_sim.py
  1. Sensor-sum check (seat + footplate + bar = body weight) only while lifting, or lowering someone, above flush (> 3 cm),
     where the user cannot be touching the mattress, and only if the mismatch lasts 0.5 s.
     v12 checked in every state: thighs on the mattress at flush, or one foot already on the floor, locked the station.
  2. No empty reset. After the user leaves, the seat stays where it is (EMPTY_HOLD), so it is waiting at standing height
     when they come back to bed. With nobody on it, the seat moves only while UP or DOWN is held (EMPTY_MOVE, 1.5 cm/s),
     and stops if anything loads it.
  3. Return to bed: sit on the raised seat, press DOWN, ride down to flush, slide back onto the mattress.
  4. Seated at height with no input: chime after 17 s, lower at 20 s (v12: 10 s, silent). Holding the grip resets the timer.
  5. Personal settings narrowed: force cap 0.4-0.6 BW (default 0.5), top speed 1.5-3 cm/s (the TL8 column cannot do 4).
  6. "The user has left the seat" now means seat load < 5 % BW and feet off the plate. v12 used "seat load < 40 % BW",
     so a user unloading the seat with part of their weight on the mattress was taken as gone and could never start.
  7. Column sync check: if the two columns differ by more than 5 mm, brake and lock (only slow DOWN while held).
User model: instead of v12's assumed capacity curve, the user can bring the seat load down to the least value the
2-D model allows at that height for their strongest effort c (seat_support.json, "P1 cap25"). Seat-off when that reaches 0.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
g = 9.81; DT = 0.02; H0, H1 = 0.42, 0.66
SS = json.load(open(os.path.join(HERE, "seat_support.json")))
TAB = SS["min_seat"]["P1 cap25"]
HGRID = np.array(sorted(float(h) for h in TAB))

def min_seat(h, c):
    """least seat load (x BW) a user with strongest effort c can reach at seat height h (linear in h and c)."""
    cs = sorted(float(e) for e in TAB["0.42"])
    def at_c(cc):
        return np.interp(h, HGRID, [TAB[f"{x:.2f}"][str(cc) if str(cc) in TAB[f"{x:.2f}"] else f"{cc}"]["Fs_BW"] for x in HGRID])
    c = min(max(c, cs[0]), cs[-1]); i = max(0, np.searchsorted(cs, c) - 1); i = min(i, len(cs) - 2)
    a, b = cs[i], cs[i + 1]; w = (c - a) / (b - a)
    return float(max(0.0, (1 - w) * at_c(a) + w * at_c(b)))

class Params:
    def __init__(self, rules="v13", bw_kg=60.0, cap=0.5, vmax=0.03):
        self.rules = rules; self.BW = bw_kg * g; self.F_cap = cap * self.BW; self.vmax = vmax
        self.k = vmax / (0.35 * self.BW)        # full speed when the seat load is 0.35 BW below the cap
        self.a_max = 0.05; self.v_down = 0.02; self.v_empty = 0.015
        self.seated_thr = 0.40 * self.BW; self.seatoff_thr = 0.05 * self.BW; self.feet_thr = 0.30 * self.BW
        self.grip_thr = 20.0; self.sum_tol = 0.15; self.sum_persist = 0.5 if rules == "v13" else 0.0
        self.stall_t = 2.0; self.idle_lower_t = 20.0 if rules == "v13" else 10.0; self.chime_t = 17.0
        self.empty_t = 5.0; self.sync_tol = 0.005

class Controller:
    def __init__(self, P, h=H0, state="IDLE"):
        self.P = P; self.state = state; self.h = h; self.v = 0.0; self.t_in = 0.0
        self.t_stall = self.t_seatoff = self.t_empty = self.t_idle = self.t_top = self.t_sum = 0.0
        self.msg = ""; self.prev_grip = False; self.chime = False; self.events = []
    def go(self, s, msg=""):
        if s != self.state:
            self.state, self.t_in, self.msg = s, 0.0, msg; self.events.append((s, msg))
    def step(self, z, t):
        P = self.P; self.t_in += DT; v_cmd = 0.0; self.chime = False
        occupied = z["F_seat"] > P.seated_thr
        total = z["F_seat"] + z["F_feet"] + max(0.0, z["F_bar"])
        if P.rules == "v12":
            check = occupied or z["F_feet"] > P.feet_thr
        else:
            check = ((self.state == "LIFTING") or (self.state == "LOWERING" and occupied)) and self.h > H0 + 0.03
        bad = check and abs(total - P.BW) / P.BW > P.sum_tol
        self.t_sum = self.t_sum + DT if bad else 0.0
        grip_edge = z["grip"] and not self.prev_grip; self.prev_grip = z["grip"]
        ready = z["grip"] and z["F_bar"] > P.grip_thr and z["F_feet"] > P.feet_thr and z["cop_ok"]
        if not z["power"] and self.state not in ("STOPPED", "LOCKED"): self.go("STOPPED", "断电：自锁停住；按住“降”用电池慢降")
        if self.t_sum > P.sum_persist and self.state != "LOCKED": self.go("LOCKED", "传感器自检不通过：锁定，只能按住“降”慢降")
        if z.get("sync_err", 0.0) > P.sync_tol and self.state != "LOCKED": self.go("LOCKED", "两根立柱不同步：制动并锁定")
        s = self.state
        if s == "IDLE":
            if occupied: self.go("SEATED")
            elif P.rules == "v12" and self.h > H0 + 1e-3: self.go("RESET_EMPTY")
        elif s == "SEATED":
            left = (z["F_seat"] < P.seatoff_thr) if P.rules == "v13" else (not occupied)
            if left and z["F_feet"] < P.feet_thr: self.go("IDLE" if self.h <= H0 + 1e-3 else "EMPTY_HOLD")
            elif ready and self.t_in > 0.5 and self.h < H1 - 1e-3: self.go("LIFTING")
            elif z["down"] and self.h > H0 + 1e-3: self.go("LOWERING", "按“降”：带人慢慢降")
            elif self.h > H0 + 1e-3:
                self.t_idle = self.t_idle + DT if not (z["grip"] or z["down"]) else 0.0
                self.chime = P.rules == "v13" and self.t_idle > P.chime_t
                if self.t_idle > P.idle_lower_t: self.go("LOWERING", "坐着没有操作：提示音后带人慢慢降")
        elif s == "LIFTING":
            if not z["grip"] or z["F_bar"] < P.grip_thr or not z["cop_ok"] or z["F_feet"] < P.feet_thr:
                self.go("STOPPED", "松手或条件不满足：停住并制动")
            else:
                v_cmd = float(np.clip(P.k * (P.F_cap - z["F_seat"]), 0, P.vmax))
                if self.h >= H1 - 1e-4: v_cmd = 0.0
                self.t_stall = self.t_stall + DT if (v_cmd == 0.0 and self.h < H1 - 1e-4 and occupied) else 0.0
                self.t_seatoff = self.t_seatoff + DT if z["F_seat"] < P.seatoff_thr else 0.0
                self.t_top = self.t_top + DT if self.h >= H1 - 1e-4 else 0.0
                if self.t_seatoff > 0.3: self.go("STANDING_HOLD", "离座：座板停在原高度、保持水平")
                elif self.t_stall > P.stall_t: self.go("STOPPED", "到推力上限仍不动：停住，可按“降”")
                elif self.t_top > 2 * P.stall_t: self.go("STOPPED", "到顶仍未离座：停住，可按“降”")
        elif s == "STOPPED":
            if not z["power"]:
                if z["down"]: v_cmd = -P.v_down * 0.5
            elif z["F_seat"] < P.seatoff_thr and z["F_feet"] > P.feet_thr: self.go("STANDING_HOLD")
            elif occupied and grip_edge and ready and self.h < H1 - 1e-3: self.go("LIFTING")
            elif occupied and (z["down"] or self.t_in > P.idle_lower_t): self.go("LOWERING", "有人坐着：带人慢慢降")
            elif P.rules == "v13" and occupied and self.t_in > P.chime_t: self.chime = True
            elif not occupied and z["F_feet"] < 0.05 * P.BW and self.t_in > P.empty_t:
                self.go("EMPTY_HOLD" if P.rules == "v13" else "RESET_EMPTY")
        elif s == "STANDING_HOLD":
            if occupied and self.t_in > 0.5: self.go("SEATED", "坐回：座板水平、停住接人")
            self.t_empty = self.t_empty + DT if (z["F_seat"] < P.seatoff_thr and z["F_feet"] < 0.05 * P.BW) else 0.0
            if self.t_empty > P.empty_t: self.go("EMPTY_HOLD" if P.rules == "v13" else "RESET_EMPTY", "人已离开")
        elif s == "EMPTY_HOLD":                       # v13 only: seat waits where it is
            if occupied: self.go("SEATED", "有人坐上座板")
            elif (z.get("up") or z["down"]) and z["F_seat"] < P.seatoff_thr: self.go("EMPTY_MOVE")
        elif s == "EMPTY_MOVE":                       # v13 only: hold-to-run with nobody on the seat
            if z["F_seat"] > P.seatoff_thr: self.go("EMPTY_HOLD", "空载移动时座板受力：停住")
            elif z.get("up"): v_cmd = P.v_empty if self.h < H1 - 1e-3 else 0.0
            elif z["down"]: v_cmd = -P.v_empty if self.h > H0 + 1e-4 else 0.0
            else: self.go("EMPTY_HOLD")
        elif s == "LOWERING":
            if not occupied: self.go("STOPPED", "下降中座板卸载：停住")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("SEATED", "到床面"); v_cmd = 0.0
        elif s == "RESET_EMPTY":                      # v12 only
            if occupied or z["F_feet"] > 0.05 * P.BW: self.go("STOPPED", "复位途中有人：停住")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("IDLE"); v_cmd = 0.0
        elif s == "LOCKED":
            if z["down"] and z["power"]: v_cmd = -P.v_down * 0.5
        dv = np.clip(v_cmd - self.v, -P.a_max * DT, P.a_max * DT)
        self.v = v_cmd if v_cmd == 0.0 else self.v + dv
        self.h = float(np.clip(self.h + self.v * DT, H0, H1))

# ---------------------------------------------------------------- scenarios
def sc(key, name, c=0.25, T=40.0, rise_T=3.0, h0=H0, state0="IDLE", **ev):
    return dict(key=key, name=name, c=c, T=T, rise_T=rise_T, h0=h0, state0=state0, ev=ev)

SCEN = [
 sc("typical", "典型目标用户（最多用到 effort 0.25）", c=0.25),
 sc("weakest", "最弱的目标用户（0.23）", c=0.23),
 sc("strong", "抬高床就够的人（0.31）", c=0.31),
 sc("tooweak", "站不起来的人（0.20），按“降”回床面", c=0.20, T=50.0, sitback=24.0, down_from=26.0),
 sc("sitback", "抬升中往回坐", sitback=9.0),
 sc("faint", "抬升中晕倒、松手", release=9.0, sitback=9.0, T=45.0),
 sc("mattress", "坐上时大腿还压在床垫上（0.2 倍体重）", mattress=0.2),
 sc("stepoff", "站起后一只脚先踩到地上，再离开", stepoff=True, T=30.0),
 sc("return", "回床：坐上停在高处的座板，按“降”，再挪回床上", h0=0.64, state0="EMPTY_HOLD", ret=True, T=36.0),
 sc("stuck", "踏板传感器卡在高读数", feet_stuck=8.0),
 sc("power", "抬升中断电，按“降”用电池慢降", power_off=9.0, down_from=15.0),
 sc("sync", "两根立柱不同步", sync_fault=8.5, down_from=14.0),
]

def run(s, rules="v13"):
    P = Params(rules=rules, vmax=0.03)
    C = Controller(P, h=s["h0"], state=s["state0"] if rules == "v13" or s["state0"] == "IDLE" else "RESET_EMPTY")
    ev = s["ev"]; BW = P.BW; s0 = 0.79
    log = {k: [] for k in ("t", "h", "seat", "feet", "bar", "state")}
    t_so = None; F_seat = 0.0
    for i in range(int(s["T"] / DT)):
        t = i * DT
        mat = ev.get("mattress", 0.0) if C.h < H0 + 0.02 else 0.0
        if ev.get("ret"):                                   # return-to-bed script
            if t < 1.0: F_seat, F_feet, F_bar = 0.0, 0.0, 0.0
            elif t < 3.0: F_seat, F_bar = 0.0, 60.0; F_feet = BW - F_bar          # on the footplate, hands on the bar
            elif t < 4.0: F_bar = 60.0; F_seat = (t - 3.0) * 0.6 * BW; F_feet = BW - F_seat - F_bar
            else:
                F_bar = 60.0 if t < 22.0 else 0.0
                share = min(1.0, max(0.0, (t - 22.0) / 4.0)) if C.h <= H0 + 1e-3 else 0.0   # slides back onto the bed
                F_seat = 0.6 * BW * (1 - share); F_feet = max(0.0, BW - F_seat - F_bar - share * BW * 0.9)
            z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, grip=False, down=4.5 <= t < 5.0, cop_ok=True, power=True)
        else:
            on = t >= 1.0
            trying = t >= 3.0 and not (ev.get("sitback") and t >= ev["sitback"])
            e = min(1.0, max(0.0, (t - 3.0) / s["rise_T"])) if trying else 0.0
            target = min_seat(C.h, s["c"])
            if on:
                frac = s0 - mat - e * (s0 - mat - target)
                if C.state == "STANDING_HOLD" and trying: frac = 0.0
                F_seat = max(0.0, frac) * BW
            else: F_seat = 0.0
            F_bar = 60.0 if (t >= 3.0 and not (ev.get("release") and t >= ev["release"])) else 0.0
            if ev.get("sitback") and t >= ev["sitback"]: F_bar = 0.0 if ev.get("release") else F_bar
            F_feet = (BW - F_seat - F_bar - mat * BW) if on else 0.0
            if ev.get("stepoff") and t_so is not None:
                if t > t_so + 3.0: F_bar = 0.0; F_feet = 0.5 * BW
                if t > t_so + 4.5: F_feet = 0.0
            if ev.get("feet_stuck") and t >= ev["feet_stuck"]: F_feet = 0.9 * BW
            grip = F_bar > 0
            z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, grip=grip, cop_ok=True,
                     down=bool(ev.get("down_from") and t >= ev["down_from"]),
                     power=not (ev.get("power_off") and t >= ev["power_off"]),
                     sync_err=0.008 if (ev.get("sync_fault") and t >= ev["sync_fault"]) else 0.0)
        C.step(z, t)
        if C.state == "STANDING_HOLD" and t_so is None: t_so = t
        for k, v in (("t", t), ("h", C.h), ("seat", z["F_seat"] / BW), ("feet", z["F_feet"] / BW), ("bar", z["F_bar"] / BW), ("state", C.state)):
            log[k].append(v)
    res = dict(key=s["key"], name=s["name"], rules=rules, final_state=C.state, final_height=round(C.h, 3),
               max_height=round(max(log["h"]), 3), seat_off_height=None if t_so is None else round(log["h"][int(t_so / DT)], 3),
               seat_off_time_s=None if t_so is None else round(t_so - 3.0, 1), events=C.events)
    return log, res

STATES = ["IDLE", "SEATED", "LIFTING", "STOPPED", "STANDING_HOLD", "LOWERING", "EMPTY_HOLD", "EMPTY_MOVE", "RESET_EMPTY", "LOCKED"]
COL = dict(IDLE="#c3c9d1", SEATED="#3f6fc4", LIFTING="#1f9e6e", STOPPED="#c8780c", STANDING_HOLD="#7a56c2",
           LOWERING="#b39400", EMPTY_HOLD="#6b7a8f", EMPTY_MOVE="#9aa6b8", RESET_EMPTY="#6b7a8f", LOCKED="#c0392b")

if __name__ == "__main__":
    out = dict(note=__doc__.strip().split("\n")[0], params=dict(cap_BW=0.5, cap_range=[0.4, 0.6], vmax_cm_s=3.0, vmax_range=[1.5, 3.0],
               k="vmax / (0.35 BW)", a_max=0.05, v_down=0.02, v_empty=0.015, sum_tol=0.15, sum_persist_s=0.5, idle_lower_s=20, chime_s=17,
               sync_tol_m=0.005, empty_hold_after_s=5), scenarios=[])
    figs = []
    for s in SCEN:
        for rules in ("v13", "v12"):
            if rules == "v12" and s["key"] not in ("mattress", "stepoff", "typical"): continue
            lg, r = run(s, rules)
            step = 10                                   # 0.2 s for the page
            r["series"] = {k: ([round(x, 3) for x in lg[k][::step]] if k != "state" else lg[k][::step]) for k in lg}
            out["scenarios"].append(r)
            if rules == "v13": figs.append((s, lg))
            print(f"{rules} {s['key']:9s} final={r['final_state']:13s} h={r['final_height']:.3f} seat-off h={r['seat_off_height']} t={r['seat_off_time_s']}")
    json.dump(out, open(os.path.join(HERE, "controller_v13.json"), "w"), ensure_ascii=False)
    fig, axs = plt.subplots(4, 3, figsize=(15, 13), sharey=True)
    for ax, (s, lg) in zip(axs.flat, figs):
        t = np.array(lg["t"]); ax.plot(t, lg["h"], color="#18202a", lw=2)
        ax2 = ax.twinx(); ax2.plot(t, lg["seat"], color="#c8602a", lw=1.4); ax2.set_ylim(0, 1.05); ax2.axhline(0.5, ls=":", color="#c8602a", lw=1)
        st = lg["state"]; j0 = 0
        for j in range(1, len(st) + 1):
            if j == len(st) or st[j] != st[j0]:
                ax.axvspan(t[j0], t[j - 1], ymin=0, ymax=0.06, color=COL[st[j0]], lw=0); j0 = j
        ax.set_title(s["key"] + "  c=" + str(s["c"]), fontsize=12); ax.set_ylim(0.38, 0.70); ax.tick_params(labelsize=11)
    fig.suptitle("v13 controller: seat height (black, m), seat load (orange, x BW; dotted = cap 0.5), state (bottom band)", fontsize=14)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "controller_v13.png"), dpi=110)
