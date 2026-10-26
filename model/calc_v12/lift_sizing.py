"""Lift mechanism and actuator sizing baseline for the bedside rise station (design v12).

Question this answers: which single-actuator mechanism fits under the seat, and how large are the
actuator force, stroke and speed over the 0.42 -> 0.66 m lift?

All numbers are first estimates for the team to check and replace (role 3: geometry, role 4: loads).
Run: python lift_sizing.py  ->  lift_sizing.json, lift_sizing.png
"""
import json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

g = 9.81
# ---------------- space envelope (m) ----------------
SEAT_TOP0 = 0.42          # seat surface when flush with mattress
SEAT_PLATE = 0.045        # seat plate thickness
CARRIER = 0.03            # seat carrier / top frame under the plate
BASE = 0.013 + 0.03       # footplate level + bottom frame
STROKE = 0.24             # seat lift 0.42 -> 0.66
H_AVAIL = SEAT_TOP0 - SEAT_PLATE - CARRIER - BASE   # collapsed height available for the mechanism
SEAT_DEPTH, SEAT_WIDTH = 0.14, 0.44

# ---------------- loads at the seat (N) ----------------
def loads(bw_kg, moving_kg=10.0, cap=0.5, cap_max=0.6):
    BW = bw_kg * g; Wm = moving_kg * g
    return dict(BW=BW,
                lift_default=cap * BW + Wm,      # pushing up to the force cap, plus moving parts
                lift_max=cap_max * BW + Wm,      # highest personal cap setting
                hold=1.5 * BW + Wm)              # static holding (sitting down on the seat), 1.5 x BW
L60, L100 = loads(60), loads(100)

# ---------------- option A: single-stage scissor across the seat width, horizontal actuator ----------------
def scissor_horizontal(L=0.40, arm_t=0.03):
    """Pin-to-pin arm length L. Height of the scissor H = L sin(theta).
    Virtual work: W dH = F dx with x = L cos(theta)  ->  F = W / tan(theta)."""
    h0 = H_AVAIL - arm_t                    # usable collapsed scissor height
    th0 = math.asin(min(h0, L * 0.25) / L)  # start low enough to leave room; use 0.25L if space allows
    H0 = L * math.sin(th0); H1 = H0 + STROKE
    if H1 > L * 0.98: return None
    th1 = math.asin(H1 / L)
    th = np.linspace(th0, th1, 200)
    ratio = 1 / np.tan(th)                   # F_act / W_seat
    stroke_act = L * (math.cos(th0) - math.cos(th1))
    return dict(name="Scissor, horizontal actuator", L=L, theta0_deg=math.degrees(th0), theta1_deg=math.degrees(th1),
                collapsed_height=H0 + arm_t, act_stroke=stroke_act,
                ratio_start=float(ratio[0]), ratio_end=float(ratio[-1]),
                h=list(SEAT_TOP0 + L * np.sin(th) - H0), ratio=list(ratio),
                speed_ratio_start=float(1/np.tan(th0)), speed_ratio_end=float(1/np.tan(th1)))

# ---------------- option B: same scissor, inclined actuator from the base to the far arm ----------------
def scissor_inclined(L=0.40, arm_t=0.03, c_body=0.12):
    """Actuator from a base point P=(px,0) to a point at fraction f along the arm that starts at the sliding
    bottom pivot. Searches px, f inside the seat width for the lowest peak force whose retracted length
    can hold the needed actuator stroke (retracted length >= stroke + c_body)."""
    h0 = min(H_AVAIL - arm_t, L * 0.25)
    th0 = math.asin(h0 / L); th1 = math.asin((h0 + STROKE) / L)
    th = np.linspace(th0, th1, 200)
    best = None
    for px in np.linspace(-0.02, SEAT_WIDTH - 0.02, 47):
        for f in np.linspace(0.3, 1.0, 36):
            # arm 2: from bottom slider (L cos th, 0) to top fixed pivot (0, H)
            ax = L * np.cos(th) * (1 - f); az = L * np.sin(th) * f
            s = np.hypot(ax - px, az)
            ds = np.gradient(s, th); dH = L * np.cos(th)
            if np.any(np.abs(ds) < 1e-6) or np.any(np.sign(ds) != np.sign(ds[0])): continue
            r = np.abs(dH / ds)                               # F_act / W_seat
            act_stroke = abs(s[-1] - s[0]); s_ret = min(s[0], s[-1])
            if s_ret < act_stroke + c_body: continue          # actuator body would not fit
            if np.max(ax) > SEAT_WIDTH or px > SEAT_WIDTH: continue
            pk = float(np.max(r))
            if best is None or pk < best["ratio_peak"]:
                best = dict(name="Scissor, inclined actuator", L=L, px=float(px), f=float(f),
                            theta0_deg=math.degrees(th0), theta1_deg=math.degrees(th1),
                            ratio_peak=pk, ratio_start=float(r[0]), ratio_end=float(r[-1]),
                            act_stroke=float(act_stroke), act_retracted=float(s_ret),
                            h=list(SEAT_TOP0 + L*np.sin(th) - L*np.sin(th0)), ratio=list(r))
    return best

# ---------------- option C: inline actuator / lifting column, ratio 1 ----------------
def inline(c_body_range=(0.10, 0.20)):
    need = [STROKE + c for c in c_body_range]
    return dict(name="Inline actuator or column (ratio 1)", ratio=1.0, act_stroke=STROKE,
                retracted_needed=need, fits_under_seat=bool(min(need) <= H_AVAIL),
                note="Needs a retracted length of about stroke + body length; does not fit under the seat, "
                     "so it would sit beside the seat (e.g. inside the side-rail post) and carry the seat as a "
                     "cantilever.")

def cantilever_moment(offset=0.25, load=None):
    load = load or L60["hold"]
    return load * offset

A = scissor_horizontal(); B = scissor_inclined()
C = inline()
out = dict(
    envelope=dict(collapsed_height_available=H_AVAIL, stroke=STROKE, seat_depth=SEAT_DEPTH, seat_width=SEAT_WIDTH),
    loads_60kg=L60, loads_100kg=L100,
    options={})
for o in (A, B):
    if o is None: continue
    k = o["name"]; r0 = o["ratio_start"]; rpk = max(o["ratio"])
    o2 = {kk: v for kk, v in o.items() if kk not in ("h", "ratio")}
    o2.update(F_lift_60kg_peak=rpk * L60["lift_max"], F_hold_60kg_flush=r0 * L60["hold"],
              F_hold_100kg_flush=r0 * L100["hold"])
    out["options"][k] = o2
C2 = dict(C); C2.update(F_lift_60kg=L60["lift_max"], F_hold_60kg=L60["hold"], F_hold_100kg=L100["hold"],
                        cantilever_moment_60kg_Nm=cantilever_moment(), cantilever_moment_100kg_Nm=cantilever_moment(load=L100["hold"]))
out["options"][C["name"]] = C2
out["design_notes"] = [
 "Space under the seat (collapsed) is about 0.30 m; an inline actuator needs about stroke + 0.10-0.20 m = 0.34-0.44 m, so it does not fit under the seat.",
 "A scissor fits (collapsed about 0.13 m) but multiplies the actuator force by about 2.7-3.9 near the flush position.",
 "Let the seat rest on a mechanical end stop when flush, so the actuator only ever pushes up to the force cap at the start of a lift.",
 "With the admittance rule the actuator never pushes more than F_cap x ratio; holding loads at height are 0.6-1.3 x the seat load."]
json.dump(out, open("lift_sizing.json", "w"), indent=1)

# ---------------- figure ----------------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for o, col in ((A, "#7b4bb0"), (B, "#b0532c")):
    if o is None: continue
    h = np.array(o["h"]); r = np.array(o["ratio"])
    ax[0].plot(h, r * L60["lift_max"] / 1000, color=col, lw=2, label=o["name"] + " — lifting")
    ax[0].plot(h, r * L60["hold"] / 1000, color=col, lw=1.5, ls="--", label=o["name"] + " — holding")
ax[0].axhline(L60["lift_max"] / 1000, color="#1d8a63", lw=2, label="Inline / column — lifting")
ax[0].axhline(L60["hold"] / 1000, color="#1d8a63", lw=1.5, ls="--", label="Inline / column — holding")
ax[0].set_xlabel("Seat height (m)"); ax[0].set_ylabel("Actuator force (kN), 60 kg user")
ax[0].set_title("Actuator force over the lift")
ax[0].text(0.43, 0.08, "Dashed = holding 1.5 x BW. At flush the seat should rest on an end stop,\nso the actuator never holds a seated user at the bottom.", transform=ax[0].transAxes, fontsize=7.5, va="bottom", color="#444"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=7.5)
names = [o["name"] for o in (A, B, C) if o]
ax[1].barh(["Available under seat"], [H_AVAIL], color="#999")
for i, o in enumerate((A, B)):
    if o: ax[1].barh([o["name"] + "\n(collapsed)"], [A["collapsed_height"]], color=["#7b4bb0", "#b0532c"][i])
ax[1].barh(["Inline actuator\n(retracted, min)"], [C["retracted_needed"][0]], color="#1d8a63")
ax[1].axvline(H_AVAIL, color="k", ls=":")
ax[1].set_xlabel("Height (m)"); ax[1].set_title("Does it fit under the seat?")
plt.tight_layout(); plt.savefig("lift_sizing.png", dpi=160)

def pr(o):
    print(o["name"]); [print("  ", k, (round(v, 3) if isinstance(v, float) else v)) for k, v in o.items()]
print("H_AVAIL", round(H_AVAIL, 3)); print("loads60", {k: round(v) for k, v in L60.items()}); print("loads100", {k: round(v) for k, v in L100.items()})
for o in out["options"].values(): pr(o)
