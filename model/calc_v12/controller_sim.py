"""Controller starter for the bedside rise station (design v12): state machine + admittance speed law,
run over scripted scenarios. Plain Python + numpy/matplotlib; graphviz 'dot' (optional) draws the diagram.

Speed law (one rule for force cap and adaptive speed):
    v = clip(k * (F_cap - F_seat), 0, v_max)   with an acceleration limit
The user takes weight off the seat -> F_seat drops below F_cap -> seat rises; the more they unload,
the faster it rises. If they sit back, F_seat rises above F_cap and v becomes 0 by itself.

User model (deliberately simple, for scenario testing only, not biomechanics):
    seat load fraction  s(t) = max(0, s0 - e(t) * c(h))
    s0 = seated load on the seat (fraction of BW); e(t) in [0,1] = how hard the user is trying to rise;
    c(h) = how much load the user can take off at seat height h (rises with h: easier from higher).
Run: python controller_sim.py -> controller_sim.json, controller_timelines.png, state_machine.svg/.png
"""
import json, subprocess, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

g = 9.81
DT = 0.02
H0, H1 = 0.42, 0.66

class Params:
    def __init__(self, bw_kg=60.0, cap=0.5, vmax=0.03, k=None, a_max=0.05):
        self.BW = bw_kg * g
        self.F_cap = cap * self.BW
        self.vmax = vmax
        # k chosen so that unloading 0.35 BW below the cap gives full speed
        self.k = k if k is not None else vmax / (0.35 * self.BW)
        self.a_max = a_max
        self.v_down = 0.02
        self.seated_thr = 0.40 * self.BW      # someone is sitting
        self.seatoff_thr = 0.05 * self.BW     # seat-off
        self.feet_thr = 0.30 * self.BW
        self.grip_thr = 20.0
        self.sum_tol = 0.15                   # |sum of vertical forces - BW| / BW
        self.stall_t = 2.0                    # pushing at the cap without moving
        self.idle_lower_t = 10.0              # seated, no input -> lower with the user
        self.empty_reset_t = 5.0              # nobody on seat and footplate -> return flush

STATES = ["IDLE", "SEATED", "LIFTING", "STOPPED", "STANDING_HOLD", "LOWERING", "RESET_EMPTY", "LOCKED"]

class Controller:
    def __init__(self, P):
        self.P = P; self.state = "IDLE"; self.h = H0; self.v = 0.0
        self.t_in = 0.0; self.t_stall = 0.0; self.t_seatoff = 0.0; self.t_empty = 0.0; self.t_idle = 0.0
        self.msg = ""; self.prev_grip = False; self.t_top = 0.0

    def go(self, s, msg=""):
        if s != self.state: self.state, self.t_in, self.msg = s, 0.0, msg

    def step(self, z):
        """z: dict of sensor readings: F_seat, F_feet, F_bar, grip (bool), down (bool), cop_ok (bool), power (bool)"""
        P = self.P; self.t_in += DT
        occupied = z["F_seat"] > P.seated_thr
        total = z["F_seat"] + z["F_feet"] + max(0.0, z["F_bar"])
        sum_ok = (abs(total - P.BW) / P.BW < P.sum_tol) if (occupied or z["F_feet"] > P.feet_thr) else True
        v_cmd = 0.0
        grip_edge = z["grip"] and not self.prev_grip; self.prev_grip = z["grip"]
        ready = z["grip"] and z["F_bar"] > P.grip_thr and z["F_feet"] > P.feet_thr and z["cop_ok"]
        if not z["power"]:
            self.go("STOPPED", "power loss: brake holds; battery lowering on DOWN")
        if not sum_ok and self.state not in ("LOCKED",):
            self.go("LOCKED", "sensor check failed (sum != body weight)")
        s = self.state
        if s == "IDLE":
            if occupied: self.go("SEATED")
            elif self.h > H0 + 1e-3: self.go("RESET_EMPTY")
        elif s == "SEATED":
            if not occupied and z["F_feet"] < P.feet_thr: self.go("IDLE")
            elif ready and self.t_in > 0.5 and (self.h < H1 - 1e-3):
                self.go("LIFTING")
            elif z["down"] and self.h > H0 + 1e-3: self.go("LOWERING")
            elif self.h > H0 + 1e-3:
                self.t_idle = self.t_idle + DT if not (z["grip"] or z["down"]) else 0.0
                if self.t_idle > P.idle_lower_t: self.go("LOWERING", "seated with no input: lower with the user")
        elif s == "LIFTING":
            if not z["grip"] or z["F_bar"] < P.grip_thr or not z["cop_ok"] or z["F_feet"] < P.feet_thr:
                self.go("STOPPED", "released or condition lost: stop and brake")
            else:
                v_cmd = float(np.clip(P.k * (P.F_cap - z["F_seat"]), 0, P.vmax))
                if self.h >= H1 - 1e-4: v_cmd = 0.0
                self.t_stall = self.t_stall + DT if (v_cmd == 0.0 and self.h < H1 - 1e-4 and occupied) else 0.0
                self.t_seatoff = self.t_seatoff + DT if z["F_seat"] < P.seatoff_thr else 0.0
                self.t_top = self.t_top + DT if self.h >= H1 - 1e-4 else 0.0
                if self.t_seatoff > 0.3: self.go("STANDING_HOLD", "seat-off: hold height, seat level")
                elif self.t_stall > P.stall_t: self.go("STOPPED", "at force cap without moving: stop, offer DOWN")
                elif self.t_top > 2 * P.stall_t: self.go("STOPPED", "reached top without seat-off: stop, offer DOWN")
        elif s == "STOPPED":
            if not z["power"]:
                if z["down"]: v_cmd = -P.v_down * 0.5     # battery lowering, slow
            elif z["F_seat"] < P.seatoff_thr and z["F_feet"] > P.feet_thr: self.go("STANDING_HOLD")
            elif occupied and grip_edge and ready and self.h < H1 - 1e-3: self.go("LIFTING")   # needs a fresh grip
            elif occupied and (z["down"] or self.t_in > P.idle_lower_t): self.go("LOWERING", "occupied: lower with the user")
        elif s == "STANDING_HOLD":
            if occupied and self.t_in > 0.5: self.go("SEATED", "sat back down: seat is level and holds")
            self.t_empty = self.t_empty + DT if (z["F_seat"] < P.seatoff_thr and z["F_feet"] < 0.05 * P.BW) else 0.0
            if self.t_empty > P.empty_reset_t: self.go("RESET_EMPTY")
        elif s == "LOWERING":
            if not occupied: self.go("STOPPED", "seat unloaded while lowering: stop")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("SEATED"); v_cmd = 0.0
        elif s == "RESET_EMPTY":
            if occupied or z["F_feet"] > 0.05 * P.BW: self.go("STOPPED", "someone on the station during reset: stop")
            else:
                v_cmd = -P.v_down
                if self.h <= H0 + 1e-4: self.go("IDLE"); v_cmd = 0.0
        elif s == "LOCKED":
            if z["down"] and z["power"]: v_cmd = -P.v_down * 0.5          # user-commanded slow lowering only
        # acceleration limit and integration
        dv = np.clip(v_cmd - self.v, -P.a_max * DT, P.a_max * DT)
        self.v = v_cmd if v_cmd == 0.0 else self.v + dv
        self.h = float(np.clip(self.h + self.v * DT, H0, H1))
        return v_cmd

# ---------------- scenarios ----------------
def user_capacity(h, c0=0.45, c1=0.45):
    return c0 + c1 * (h - H0) / (H1 - H0)

def make_scenario(name, T=40.0, rise_T=3.0, s0=0.79, c0=0.45, c1=0.45, events=None, vmax=0.03):
    return dict(name=name, T=T, rise_T=rise_T, s0=s0, c0=c0, c1=c1, events=events or {}, vmax=vmax)

SCEN = [
 make_scenario("Normal user", rise_T=3.0, c0=0.40),
 make_scenario("Slow user, personal max 1.5 cm/s", rise_T=8.0, c0=0.40, vmax=0.015),
 make_scenario("Fast user, personal max 4 cm/s", rise_T=1.5, c0=0.40, vmax=0.04),
 make_scenario("Weak user (cannot stand even at 0.66 m)", c0=0.40, c1=0.25, events=dict(sitback=25.0)),
 make_scenario("Sits back mid-lift", c0=0.40, events=dict(sitback=9.0)),
 make_scenario("Faints: lets go mid-lift", c0=0.40, events=dict(release=9.0, sitback=9.0)),
 make_scenario("Footplate sensor stuck high", c0=0.40, events=dict(feet_stuck=8.0)),
 make_scenario("Power loss mid-lift", c0=0.40, events=dict(power_off=9.0, down_from=15.0)),
]

def run(sc, P=None):
    P = P or Params(vmax=sc["vmax"]); C = Controller(P)
    N = int(sc["T"] / DT); log = {k: [] for k in ("t", "h", "v", "F_seat", "state")}
    sat_t, grip_t = 1.0, 3.0       # sits on the seat at 1 s, grips and starts trying at 3 s
    seat_off_time = None
    for i in range(N):
        t = i * DT; ev = sc["events"]
        on_seat = t >= sat_t
        trying = t >= grip_t and not (ev.get("sitback") and t >= ev["sitback"])
        e = min(1.0, max(0.0, (t - grip_t) / sc["rise_T"])) if trying else 0.0
        if on_seat:
            s = max(0.0, sc["s0"] - e * user_capacity(C.h, sc["c0"], sc["c1"]))
            if C.state == "STANDING_HOLD" and trying: s = 0.0
        else:
            s = 0.0
        F_seat = s * P.BW
        F_bar = 60.0 if (t >= grip_t and not (ev.get("release") and t >= ev["release"])) else 0.0
        F_feet = (P.BW - F_seat - F_bar) if on_seat else 0.0
        if ev.get("feet_stuck") and t >= ev["feet_stuck"]: F_feet = 0.9 * P.BW
        grip = F_bar > 0
        z = dict(F_seat=F_seat, F_feet=F_feet, F_bar=F_bar, grip=grip, cop_ok=True,
                 down=bool(ev.get("down_from") and t >= ev["down_from"]),
                 power=not (ev.get("power_off") and t >= ev["power_off"]))
        C.step(z)
        if C.state == "STANDING_HOLD" and seat_off_time is None: seat_off_time = t
        for k, v in (("t", t), ("h", C.h), ("v", C.v), ("F_seat", F_seat / P.BW), ("state", C.state)): log[k].append(v)
    return log, dict(scenario=sc["name"], final_state=C.state, final_height=round(C.h, 3),
                     max_height=round(max(log["h"]), 3), max_speed_cm_s=round(float(100 * max(log["v"])), 2),
                     seat_off_time_s=None if seat_off_time is None else round(seat_off_time - 3.0, 2),
                     last_message=C.msg)

results = []; logs = []
for sc in SCEN:
    lg, r = run(sc); logs.append(lg); results.append(r)

# ---------------- figure: timelines ----------------
col = {s: c for s, c in zip(STATES, ["#9aa3ad", "#3d63b8", "#1d8a63", "#b86b0b", "#7b4bb0", "#a7781a", "#5a6b7a", "#c0392b"])}
fig, axes = plt.subplots(4, 2, figsize=(12, 11), sharex=True)
for ax, lg, r in zip(axes.flat, logs, results):
    t = np.array(lg["t"]); h = np.array(lg["h"]); fs = np.array(lg["F_seat"])
    ax.plot(t, h, color="#18202a", lw=2, label="Seat height (m)")
    ax2 = ax.twinx(); ax2.plot(t, fs, color="#b0532c", lw=1.2, label="Seat load / BW"); ax2.axhline(0.5, color="#b0532c", ls=":", lw=1)
    ax2.set_ylim(0, 1.0); ax2.set_ylabel("seat load / BW", color="#b0532c", fontsize=8)
    st = lg["state"]; start = 0
    for i in range(1, len(st) + 1):
        if i == len(st) or st[i] != st[start]:
            ax.axvspan(t[start], t[i - 1] + DT, ymin=0, ymax=0.08, color=col[st[start]], lw=0)
            start = i
    ax.set_ylim(0.38, 0.70); ax.set_title(r["scenario"], fontsize=10); ax.grid(alpha=.25)
    ax.set_ylabel("height (m)", fontsize=8)
for ax in axes[-1]: ax.set_xlabel("time (s)")
handles = [plt.Rectangle((0, 0), 1, 1, color=col[s]) for s in STATES]
fig.legend(handles, STATES, loc="lower center", ncol=8, fontsize=8, frameon=False)
fig.suptitle("Rise-station controller: seat height (black), seat load (orange, dotted = force cap 0.5 BW), state (colour bar)", fontsize=11)
plt.tight_layout(rect=(0, 0.03, 1, 0.97)); plt.savefig("controller_timelines.png", dpi=150)

# ---------------- state diagram ----------------
DOT = """digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#f4f6f8", fontname="Helvetica", fontsize=11]; edge [fontname="Helvetica", fontsize=9];
IDLE -> SEATED [label="seat load > 40% BW"];
SEATED -> LIFTING [label="grip switch + hand on bar\\n+ feet on plate + COP ok"];
LIFTING -> STANDING_HOLD [label="seat-off\\n(seat load < 5% BW, 0.3 s)"];
LIFTING -> STOPPED [label="release / condition lost /\\nat cap > 2 s / power loss"];
STOPPED -> LIFTING [label="grip again + conditions ok"];
STOPPED -> LOWERING [label="occupied and\\n(DOWN or 10 s no input)"];
STOPPED -> STANDING_HOLD [label="seat-off"];
SEATED -> LOWERING [label="DOWN (seat raised)\\nor 10 s no input"];
LOWERING -> SEATED [label="reached flush"];
LOWERING -> STOPPED [label="seat unloaded"];
STANDING_HOLD -> SEATED [label="sits back\\n(seat level, holds)"];
STANDING_HOLD -> RESET_EMPTY [label="seat + footplate empty 5 s"];
RESET_EMPTY -> IDLE [label="flush"];
RESET_EMPTY -> STOPPED [label="load detected"];
ANY [shape=plaintext, fillcolor=none, label="any state"];
ANY -> LOCKED [label="sensor sum != BW\\n(only slow DOWN allowed)", style=dashed];
LIFTING [fillcolor="#dff3ea"]; STOPPED [fillcolor="#fdf3e2"]; LOCKED [fillcolor="#f9e0dd"];
}"""
open("state_machine.dot", "w").write(DOT)
if shutil.which("dot"):
    for fmt in ("svg", "png"):
        subprocess.run(["dot", f"-T{fmt}", "state_machine.dot", "-o", f"state_machine.{fmt}"], check=True)

json.dump(dict(params=dict(F_cap_BW=0.5, vmax_m_s=0.03, k="vmax / (0.2 BW)", a_max=0.05, v_down=0.02),
               results=results), open("controller_sim.json", "w"), indent=1)
for r in results: print(r)
