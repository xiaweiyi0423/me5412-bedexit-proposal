"""Stability baseline for the bedside rise station (design v12).

Two different questions, kept apart on purpose:
 1. User completely on the station (seated on the seat plate and/or standing on the footplate):
    hand forces on the rail are internal. The station can only tip if the COMBINED centre of gravity
    of user + station leaves the base footprint. -> margins per posture, sagittal and lateral.
 2. User only partly on the station (sitting on the bed, or already off the footplate) and pulling
    on the rail: an external force. -> unanchored capacity, and the hold-down force an anchor to the
    bed must supply for a safety factor of 1.5.

Coordinates: x forward from the bed edge (station rear edge x = 0), y sideways (base centred, half-width
0.33 m, side rail on the -y side), z up. Footprint x in [0, 0.80], y in [-0.33, 0.33].
Run: python stability.py  ->  stability.json, stability_top.png
"""
import json, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

g = 9.81
M_USER, M_ST = 60.0, 35.0
X_ST = 0.25                     # station COM x (from the earlier design estimate)
BX0, BX1, BY = 0.0, 0.80, 0.33  # footprint
SEAT_W = 0.44

# 2D poses (x, z) from the proposal page animation (60 kg, 1.60 m figure): S shoulder, H hip, K knee, A ankle
POSE = {
 "Seated on seat (flush)": dict(S=[0.18, 0.97], H=[0.13, 0.51], K=[0.52, 0.46], A=[0.52, 0.062], on_station=1.0),
 "Ready, holding bar":     dict(S=[0.28, 0.94], H=[0.13, 0.51], K=[0.46, 0.40], A=[0.29, 0.062], on_station=1.0),
 "Seat-off at 0.66 m":     dict(S=[0.37, 1.149], H=[0.14, 0.75], K=[0.42, 0.44], A=[0.29, 0.062], on_station=1.0),
 "Standing":               dict(S=[0.31, 1.309], H=[0.29, 0.848], K=[0.31, 0.456], A=[0.29, 0.062], on_station=1.0),
 "Sits back, upright (0.66)": dict(S=[0.05, 1.21], H=[0.07, 0.75], K=[0.42, 0.62], A=[0.40, 0.062], on_station=1.0),
 "Sits back, leaning back 20°": dict(S=[-0.09, 1.18], H=[0.05, 0.75], K=[0.42, 0.62], A=[0.40, 0.062], on_station=1.0),
}
# segment mass fractions and COM positions (Winter-type values): head-arms-trunk, both thighs, both shanks+feet
SEG = [("HAT", 0.678, "H", "S", 0.626), ("thighs", 0.200, "H", "K", 0.433), ("shanks+feet", 0.122, "K", "A", 0.50)]

def user_com_x(q):
    return sum(m * (q[a][0] + (q[b][0] - q[a][0]) * f) for _, m, a, b, f in SEG)

def combined(xu, yu=0.0):
    xc = (M_USER * xu + M_ST * X_ST) / (M_USER + M_ST)
    yc = (M_USER * yu) / (M_USER + M_ST)
    return xc, yc

rows = []
for name, q in POSE.items():
    xu = user_com_x(q); xc, _ = combined(xu)
    rows.append(dict(posture=name, user_com_x=round(xu, 3), combined_x=round(xc, 3),
                     margin_rear=round(xc - BX0, 3), margin_front=round(BX1 - xc, 3)))

# lateral: user's COM shifted sideways while fully on the station
lat = []
for label, yu in [("centred", 0.0), ("hip at seat edge", SEAT_W / 2 - 0.05), ("leaning out of the seat", 0.30),
                  ("extreme slump", 0.45)]:
    _, yc = combined(0.25, yu)
    lat.append(dict(case=label, user_com_y=yu, combined_y=round(yc, 3), margin=round(BY - abs(yc), 3)))
y_tip = BY * (M_USER + M_ST) / M_USER     # user COM offset that would tip the station sideways

# ---- partly on the station, pulling on the rail (external force) ----
W = M_ST * g
cases = [  # (name, force N, height m, lever of station weight about the tipping edge m, anchor lever m)
 ("Forward pull on front bar (raised, 1.06 m)", 177, 1.06, BX1 - X_ST, BX1),
 ("Sideways pull on side rail, low (0.64 m)",   177, 0.64, BY, 2 * BY),
 ("Sideways pull on side rail, high (0.88 m)",  177, 0.88, BY, 2 * BY),
 ("Pull towards the bed on side rail (0.64 m)", 177, 0.64, X_ST, BX1),
 ("Grab-bar level load, sideways high (0.88 m)", 1112, 0.88, BY, 2 * BY),
]
SF = 1.5
ext = []
for name, F, h, lever, anchor_lever in cases:
    cap = W * lever / h
    need = max(0.0, (SF * F * h - W * lever) / anchor_lever)
    ext.append(dict(case=name, force_N=F, height_m=h, unanchored_capacity_N=round(cap), sf_unanchored=round(cap / F, 2),
                    anchor_holddown_for_SF1p5_N=round(need)))
note_bed = "Pulling towards the bed: the bed itself is right behind the station, so with the station anchored this case is not critical."

out = dict(assumptions=dict(user_kg=M_USER, station_kg=M_ST, station_com_x=X_ST, footprint=[BX0, BX1, -BY, BY],
                            segment_model="Winter-type fractions; poses from proposal animation"),
           fully_on_station_sagittal=rows, fully_on_station_lateral=lat, user_offset_to_tip_sideways_m=round(y_tip, 3),
           partly_on_station_pull=ext, note=note_bed)
json.dump(out, open("stability.json", "w"), indent=1)

# ---- figure: top view ----
fig, ax = plt.subplots(1, 2, figsize=(12, 5.6), gridspec_kw=dict(width_ratios=[1.1, 1]))
a = ax[0]
a.add_patch(Rectangle((BX0, -BY), BX1 - BX0, 2 * BY, fc="#eceff3", ec="#555", lw=1.2, label="Base footprint"))
a.add_patch(Rectangle((-0.6, -0.5), 0.6, 1.0, fc="#dfe3ea", ec="none")); a.text(-0.3, 0.42, "Bed", ha="center", color="#555")
a.add_patch(Rectangle((0, -SEAT_W / 2), 0.14, SEAT_W, fc="#f0b45c", ec="#b86b0b", label="Seat plate"))
a.plot([0, 0.69, 0.69], [-0.28, -0.28, 0.12], color="#18202a", lw=3, label="L-shaped rail")
cols = plt.cm.viridis(np.linspace(0, 0.9, len(rows)))
for r, c in zip(rows, cols):
    a.plot(r["combined_x"], 0, "o", color=c, ms=8, label=f'{r["posture"]}: {r["margin_rear"]:.2f} m to rear edge')
for l in lat[1:3]:
    a.plot(0.25 * M_USER / (M_USER + M_ST) + X_ST * M_ST / (M_USER + M_ST), l["combined_y"], "s", color="#b0532c", ms=7)
a.annotate("user leaning sideways\n(combined COG)", (0.25, lat[2]["combined_y"]), (0.42, 0.24), fontsize=8,
           arrowprops=dict(arrowstyle="->", color="#b0532c"))
a.set_xlim(-0.6, 0.9); a.set_ylim(-0.5, 0.5); a.set_aspect("equal"); a.set_xlabel("x (m), forward from bed edge"); a.set_ylabel("y (m)")
a.set_title("User fully on the station: combined COG stays inside the base"); a.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)
b = ax[1]
labels = [e["case"].replace(" (", "\n(") for e in ext]
y = np.arange(len(ext))
b.barh(y - 0.2, [e["unanchored_capacity_N"] for e in ext], 0.4, color="#9aa3ad", label="Unanchored capacity")
b.barh(y + 0.2, [e["force_N"] * SF for e in ext], 0.4, color="#7b4bb0", label="Required (1.5 × design force)")
for i, e in enumerate(ext):
    b.text(max(e["unanchored_capacity_N"], e["force_N"] * SF) + 20, i, f'anchor {e["anchor_holddown_for_SF1p5_N"]} N', va="center", fontsize=7.5)
b.set_yticks(y); b.set_yticklabels(labels, fontsize=7); b.invert_yaxis(); b.set_xlabel("Horizontal force (N)")
b.set_title("User partly off the station, pulling on the rail"); b.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False); b.set_xlim(0, 2600)
plt.tight_layout(); plt.savefig("stability_top.png", dpi=160)

for r in rows: print(r)
for l in lat: print(l)
print("user offset to tip sideways", round(y_tip, 3))
for e in ext: print(e)
