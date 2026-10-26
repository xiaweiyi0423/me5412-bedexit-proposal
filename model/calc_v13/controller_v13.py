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
  5. Personal settings narrowed: force cap 0.5-0.6 BW (default 0.5; 13.1, was 0.4-0.6 in 13.0), top speed 1.5-3 cm/s (the TL8 column cannot do 4).
  6. "The user has left the seat" now means seat load < 5 % BW and feet off the plate. v12 used "seat load < 40 % BW",
     so a user unloading the seat with part of their weight on the mattress was taken as gone and could never start.
  7. Column sync check: if the two columns differ by more than 5 mm, brake and lock (only slow DOWN while held).
Changes after the Gemini audit of v13 (13.1)
  8. The bar force is the signed vertical component (+ user pushes down, - user pulls up) and enters the sensor sum with
     its sign; "hand on the bar" uses the force magnitude. v12 clipped negative bar force to 0, so pulling up locked.
  9. "Someone is sitting" has hysteresis: enter above 0.40 BW, stay above 0.15 BW while seated, stopped or lowering.
 10. Lowering a seated user is hold-to-run: it continues only while DOWN is held (release = stop). Only the idle timeout
     lowers without a held button. Lowering starts only with the centre of pressure inside the safe zone and stops if it leaves.
 11. Return to bed: the user first holds DOWN to bring the empty seat down; it pauses at the personal return height
     (default bed level), then they sit. Sitting on a raised 14 cm seat with a drop behind it is no longer the default.
 12. Column sync fault locks with no motion at all (DOWN ignored); a sensor-sum fault still allows slow held DOWN.
     STOPPED -> STANDING_HOLD needs 0.3 s of seat-off. The speed rule uses a low-pass filtered seat force (about 2 Hz).
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
    def __init__(self, rules="v13", bw_kg=60.0, cap=0.5, vmax=0.03, ret_h=H0):
        self.rules = rules; self.BW = bw_kg * g; self.F_cap = cap * self.BW; self.vmax = vmax
        self.k = vmax / (0.35 * self.BW)        # full speed when the seat load is 0.35 BW below the cap
        self.a_max = 0.05; self.v_down = 0.02; self.v_empty = 0.015
        self.seated_thr = 0.40 * self.BW        # someone sits down (enter)
        self.occ_stay = 0.15 * self.BW if rules == "v13" else self.seated_thr   # still sitting (hysteresis)
        self.seatoff_thr = 0.05 * self.BW; self.feet_thr = 0.30 * self.BW
        self.grip_thr = 20.0; self.sum_tol = 0.15; self.sum_persist = 0.5 if rules == "v13" else 0.0
        self.stall_t = 2.0; self.idle_lower_t = 20.0 if rules == "v13" else 10.0; self.chime_t = 17.0
        self.empty_t = 5.0; self.sync_tol = 0.005; self.stand_persist = 0.3 if rules == "v13" else 0.0
        self.ret_h = ret_h                      # personal return-to-bed height: empty lowering pauses here
        self.tau_f = 0.08                       # low-pass filter on the seat force used by the speed rule (about 2 Hz)

class Controller:
    def __init__(self, P, h=H0, state="IDLE"):
        self.P = P; self.state = state; self.h = h; self.v = 0.0; self.t_in = 0.0
        self.t_stall = self.t_seatoff = self.t_empty = self.t_idle = self.t_top = self.t_sum = self.t_stand = 0.0
        self.msg = ""; self.prev_grip = False; self.prev_down = False; self.chime = False; self.events = []
        self.lock_reason = ""; self.lower_mode = ""; self.fs_f = None; self.paused = False
    def go(self, s, msg=""):
        if s != self.state:
            self.state, self.t_in, self.msg = s, 0.0, msg; self.events.append((s, msg))
    def step(self, z, t):
        P = self.P; self.t_in += DT; v_cmd = 0.0; self.chime = False; v13 = P.rules == "v13"
        self.fs_f = z["F_seat"] if self.fs_f is None else self.fs_f + (z["F_seat"] - self.fs_f) * DT / P.tau_f
        stay = self.state in ("SEATED", "LOWERING", "STOPPED")
        occupied = z["F_seat"] > (P.occ_stay if stay else P.seated_thr)
        # vertical forces: seat + footplate + bar (signed: + = user pushes down on the bar, - = pulls up)
        total = z["F_seat"] + z["F_feet"] + (z["F_bar"] if v13 else max(0.0, z["F_bar"]))
        if not v13:
            check = occupied or z["F_feet"] > P.feet_thr
        else:
            check = ((self.state == "LIFTING") or (self.state == "LOWERING" and occupied)) and self.h > H0 + 0.03
        bad = check and abs(total - P.BW) / P.BW > P.sum_tol
        self.t_sum = self.t_sum + DT if bad else 0.0
        grip_edge = z["grip"] and not self.prev_grip; self.prev_grip = z["grip"]
        down_edge = z["down"] and not self.prev_down; self.prev_down = z["down"]
        bar_mag = z.get("bar_mag", abs(z["F_bar"]))
        ready = z["grip"] and bar_mag > P.grip_thr and z["F_feet"] > P.feet_thr and z["cop_ok"]
        if not z["power"] and self.state not in ("STOPPED", "LOCKED"): self.go("STOPPED", "断电：自锁停住；按住“降”用电池慢降")
        if self.t_sum > P.sum_persist and self.state != "LOCKED":
            self.lock_reason = "sensor"; self.go("LOCKED", "传感器自检不通过：锁定，只能按住“降”慢降")
        if z.get("sync_err", 0.0) > P.sync_tol and not (self.state == "LOCKED" and self.lock_reason == "sync"):
            self.lock_reason = "sync" if v13 else "sensor"
            self.go("LOCKED", "两根立柱不同步：制动锁定，不再运动" if v13 else "两根立柱不同步：锁定")
        s = self.state
        if s == "IDLE":
            if occupied: self.go("SEATED")
            elif not v13 and self.h > H0 + 1e-3: self.go("RESET_EMPTY")
        elif s == "SEATED":
            left = (z["F_seat"] < P.seatoff_thr) if v13 else (not occupied)
            if left and z["F_feet"] < P.feet_thr: self.go("IDLE" if self.h <= H0 + 1e-3 else "EMPTY_HOLD")
            elif ready and self.t_in > 0.5 and self.h < H1 - 1e-3: self.go("LIFTING")
            elif z["down"] and self.h > H0 + 1e-3 and (z["cop_ok"] or not v13):
                self.lower_mode = "user"; self.go("LOWERING", "按住“降”：带人慢慢降")
            elif self.h > H0 + 1e-3:
                self.t_idle = self.t_idle + DT if not (z["grip"] or z["down"]) else 0.0
                self.chime = v13 and self.t_idle > P.chime_t
                if self.t_idle > P.idle_lower_t: self.lower_mode = "auto"; self.go("LOWERING", "坐着没有操作：提示音后带人慢慢降")
        elif s == "LIFTING":
            if not z["grip"] or bar_mag < P.grip_thr or not z["cop_ok"] or z["F_feet"] < P.feet_thr:
                self.go("STOPPED", "松手或条件不满足：停住并制动")
            else:
                fs = self.fs_f if v13 else z["F_seat"]
                v_cmd = float(np.clip(P.k * (P.F_cap - fs), 0, P.vmax))
                if self.h >= H1 - 1e-4: v_cmd = 0.0
                self.t_stall = self.t_stall + DT if (v_cmd == 0.0 and self.h < H1 - 1e-4 and occupied) else 0.0
                self.t_seatoff = self.t_seatoff + DT if z["F_seat"] < P.seatoff_thr else 0.0
                self.t_top = self.t_top + DT if self.h >= H1 - 1e-4 else 0.0
                if self.t_seatoff > 0.3: self.go("STANDING_HOLD", "离座：座板停在原高度、保持水平")
                elif self.t_stall > P.stall_t: self.go("STOPPED", "到推力上限仍不动：停住，可按住“降”")
                elif self.t_top > 2 * P.stall_t: self.go("STOPPED", "到顶仍未离座：停住，可按住“降”")
        elif s == "STOPPED":
            self.t_stand = self.t_stand + DT if (z["F_seat"] < P.seatoff_thr and z["F_feet"] > P.feet_thr) else 0.0
            if not z["power"]:
                if z["down"]: v_cmd = -P.v_down * 0.5
            elif self.t_stand > P.stand_persist: self.go("STANDING_HOLD")
            elif occupied and grip_edge and ready and self.h < H1 - 1e-3: self.go("LIFTING")
            elif occupied and z["down"] and (z["cop_ok"] or not v13): self.lower_mode = "user"; self.go("LOWERING", "有人坐着，按住“降”：带人慢慢降")
            elif occupied and self.t_in > P.idle_lower_t: self.lower_mode = "auto"; self.go("LOWERING", "有人坐着、无操作：提示音后带人慢慢降")
            elif v13 and occupied and self.t_in > P.chime_t: self.chime = True
            elif not occupied and z["F_feet"] < 0.05 * P.BW and self.t_in > P.empty_t:
                self.go("EMPTY_HOLD" if v13 else "RESET_EMPTY")
        elif s == "STANDING_HOLD":
            if z["F_seat"] > P.seated_thr and self.t_in > 0.5: self.go("SEATED", "坐回：座板水平、停住接人")
            self.t_empty = self.t_empty + DT if (z["F_seat"] < P.seatoff_thr and z["F_feet"] < 0.05 * P.BW) else 0.0
            if self.t_empty > P.empty_t: self.go("EMPTY_HOLD" if v13 else "RESET_EMPTY", "人已离开")
        elif s == "EMPTY_HOLD":                       # v13 only: seat waits where it is
            if occupied: self.go("SEATED", "有人坐上座板")
            elif (z.get("up") or down_edge) and z["F_seat"] < P.seatoff_thr: self.paused = False; self.go("EMPTY_MOVE")
        elif s == "EMPTY_MOVE":                       # v13 only: hold-to-run with nobody on the seat
            if z["F_seat"] > P.seatoff_thr: self.go("EMPTY_HOLD", "空载移动时座板受力：停住")
            elif z.get("up"): v_cmd = P.v_empty if self.h < H1 - 1e-3 else 0.0
            elif z["down"]:
                stop_at = P.ret_h if (P.ret_h > H0 + 1e-3 and not self.paused and self.h > P.ret_h - 2e-3) else H0
                if self.h > stop_at + 1e-4: v_cmd = -P.v_empty
                else:
                    if stop_at > H0 + 1e-3: self.paused = True
                    self.go("EMPTY_HOLD", "到回床高度，停住" if stop_at > H0 + 1e-3 else "到床面")
            else: self.go("EMPTY_HOLD")
        elif s == "LOWERING":
            if not occupied: self.go("STOPPED", "下降中座板卸载：停住")
            elif v13 and not z["cop_ok"]: self.go("STOPPED", "下降中压力中心偏出：停住")
            elif v13 and self.lower_mode == "user" and not z["down"]: self.go("STOPPED", "松开“降”：停住")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("SEATED", "到床面"); v_cmd = 0.0
        elif s == "RESET_EMPTY":                      # v12 only
            if occupied or z["F_feet"] > 0.05 * P.BW: self.go("STOPPED", "复位途中有人：停住")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("IDLE"); v_cmd = 0.0
        elif s == "LOCKED":
            if z["down"] and z["power"] and self.lock_reason != "sync": v_cmd = -P.v_down * 0.5
        dv = np.clip(v_cmd - self.v, -P.a_max * DT, P.a_max * DT)
        self.v = v_cmd if v_cmd == 0.0 else self.v + dv
        self.h = float(np.clip(self.h + self.v * DT, H0, H1))

# ---------------------------------------------------------------- scenarios
def sc(key, name, c=0.25, T=40.0, rise_T=3.0, h0=H0, state0="IDLE", ret_h=H0, **ev):
    return dict(key=key, name=name, c=c, T=T, rise_T=rise_T, h0=h0, state0=state0, ret_h=ret_h, ev=ev)

def hold(*spans):
    return lambda t: any(a <= t < b for a, b in spans)

SCEN = [
 sc("typical", "典型目标用户（最多用到 effort 0.25）", c=0.25),
 sc("weakest", "最弱的目标用户（0.23）", c=0.23),
 sc("strong", "抬高床就够的人（0.31）", c=0.31),
 sc("tooweak", "站不起来的人（0.20）：到顶停住，按住“降”回床面", c=0.20, T=60.0, sitback=38.0, down=hold((40.0, 60.0))),
 sc("sitback", "抬升中往回坐", sitback=9.0),
 sc("faint", "抬升中晕倒、松手", release=9.0, sitback=9.0, T=45.0),
 sc("mattress", "坐上时大腿还压在床垫上（0.2 倍体重）", mattress=0.2),
 sc("stepoff", "站起后一只脚先踩到地上，再离开", stepoff=True, T=30.0),
 sc("pullup", "起身时双手往上拉横杆（0.2 倍体重）", pull=0.2),
 sc("cop", "抬升中坐偏（压力中心偏出 1 s），重新握紧后继续", cop_off=(7.0, 8.0), regrip=(8.5, 9.0)),
 sc("return", "回床：按住“降”让空座板降到床面，再坐下挪回床上", h0=0.62, state0="EMPTY_HOLD", ret="flush", T=38.0),
 sc("return50", "回床（回床高度设为 0.50 m）：坐下后按住“降”", h0=0.62, state0="EMPTY_HOLD", ret="mid", ret_h=0.50, T=34.0),
 sc("stuck", "踏板传感器卡在高读数，按住“降”慢降", feet_stuck=8.0, down=hold((14.0, 40.0))),
 sc("power", "抬升中断电，按住“降”用电池慢降", power_off=9.0, down=hold((15.0, 45.0)), T=45.0),
 sc("sync", "两根立柱不同步：锁死，按“降”也不动", sync_fault=8.5, down=hold((14.0, 40.0))),
]

def run(s, rules="v13"):
    P = Params(rules=rules, vmax=0.03, ret_h=s["ret_h"])
    C = Controller(P, h=s["h0"], state=s["state0"] if rules == "v13" or s["state0"] == "IDLE" else "RESET_EMPTY")
    ev = s["ev"]; BW = P.BW; s0 = 0.79
    log = {k: [] for k in ("t", "h", "seat", "feet", "bar", "state")}
    t_so = None; F_seat = 0.0
    for i in range(int(s["T"] / DT)):
        t = i * DT; cop_ok = True; up = False; grip_override = None
        mat = ev.get("mattress", 0.0) if C.h < H0 + 0.02 else 0.0
        if ev.get("ret"):                                   # return-to-bed scripts
            mid = ev["ret"] == "mid"
            sit_t = 16.5 if not mid else 11.5
            if t < 1.0: F_seat, F_feet, F_bar = 0.0, 0.0, 0.0; down = False
            elif t < sit_t:                                  # standing on the plate, hands on the bar, holding DOWN for the empty seat
                F_seat, F_bar = 0.0, 0.1 * BW; F_feet = BW - F_bar; down = 2.0 <= t < sit_t - 0.5
            elif t < sit_t + 1.0:                            # sits down
                F_bar = 0.05 * BW; F_seat = (t - sit_t) * 0.6 * BW; F_feet = BW - F_seat - F_bar; down = False
            else:
                F_bar = 0.05 * BW
                if mid: down = (13.0 <= t < 14.5) or (15.5 <= t < 20.0)   # hold, let go once, hold again
                else: down = False
                start = 22.0 if not mid else 24.0
                share = min(1.0, max(0.0, (t - start) / 4.0)) if C.h <= H0 + 1e-3 else 0.0   # slides back onto the bed
                F_seat = 0.6 * BW * (1 - share); F_bar = F_bar * (1 - share)
                F_feet = max(0.0, BW - F_seat - F_bar - share * BW * 0.9)
            z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, grip=False, down=down, cop_ok=True, power=True)
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
            hands = t >= 3.0 and not (ev.get("release") and t >= ev["release"])
            F_bar = (-ev["pull"] * BW if ev.get("pull") else 60.0) if hands else 0.0
            if ev.get("sitback") and t >= ev["sitback"] and ev.get("release"): F_bar = 0.0
            F_feet = (BW - F_seat - F_bar - mat * BW) if on else 0.0
            if ev.get("stepoff") and t_so is not None:
                if t > t_so + 3.0: F_bar = 0.0; F_feet = 0.5 * BW
                if t > t_so + 4.5: F_feet = 0.0
            if ev.get("feet_stuck") and t >= ev["feet_stuck"]: F_feet = 0.9 * BW
            if ev.get("cop_off") and ev["cop_off"][0] <= t < ev["cop_off"][1]: cop_ok = False
            grip = hands and not (ev.get("regrip") and ev["regrip"][0] <= t < ev["regrip"][1])
            dfun = ev.get("down")
            z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, bar_mag=abs(F_bar), grip=grip, cop_ok=cop_ok,
                     down=bool(dfun and dfun(t)), power=not (ev.get("power_off") and t >= ev["power_off"]),
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
    out = dict(note=__doc__.strip().split("\n")[0], params=dict(cap_BW=0.5, cap_range=[0.5, 0.6], vmax_cm_s=3.0, vmax_range=[1.5, 3.0],
               k="vmax / (0.35 BW)", seat_force_filter_s=0.08, a_max=0.05, v_down=0.02, v_empty=0.015, sum_tol=0.15, sum_persist_s=0.5,
               occupied_enter_BW=0.40, occupied_stay_BW=0.15, idle_lower_s=20, chime_s=17, sync_tol_m=0.005, empty_hold_after_s=5,
               return_height_default_m=0.42), scenarios=[])
    figs = []
    for s in SCEN:
        for rules in ("v13", "v12"):
            if rules == "v12" and s["key"] not in ("mattress", "stepoff", "pullup", "typical"): continue
            lg, r = run(s, rules)
            step = 10                                   # 0.2 s for the page
            r["series"] = {k: ([round(x, 3) for x in lg[k][::step]] if k != "state" else lg[k][::step]) for k in lg}
            out["scenarios"].append(r)
            if rules == "v13": figs.append((s, lg))
            print(f"{rules} {s['key']:9s} final={r['final_state']:13s} h={r['final_height']:.3f} seat-off h={r['seat_off_height']} t={r['seat_off_time_s']}")
    json.dump(out, open(os.path.join(HERE, "controller_v13.json"), "w"), ensure_ascii=False)
    fig, axs = plt.subplots(5, 3, figsize=(15, 16), sharey=True)
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
