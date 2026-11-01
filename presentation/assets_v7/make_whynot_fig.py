"""whynot slide: four ways to rise, the same instant of the rise, where a straight-down hip drop lands.

One typical user (REF = H1.60 r0.09 p1.0 xa0.29, the user of seat_rise.gif), all four panels at the same rise fraction
F_PICK (f = hip-height fraction from seated to standing, the f of fall_catch.json), each option on its own rise path:
  lowbed    0.42 m bed, sitting on the mattress edge (hip x = 0)  -> seat_1dof_fall_catch.bed_path(..., hip0=0, bed+r_b)
  highbed   0.58 m bed, same                                       -> idem
  vertical  vertical-lift seat (curve_vertical(top=0.69))         -> path_of(u) + track(..., FC.CVV), stays put after release
  ours      inclined-rail seat (slider curve)                      -> path_of(u) + track(..., FC.CV); same pose as page.json anim
Body pose: model pose() (ankle, knee, hip), trunk angle from seat_1dof_design.trunk_for (as in page.json anim).
Landing point (fall_catch definition): the buttock lands BEHIND = 4 cm behind the hip joint; catch = support front edge -
(hip x - 0.04). Dashed line = that point dropped straight down. Green = lands on the support; red = the horizontal gap
from the support's front edge to the dashed line (|catch| in cm, same number as fall_catch.json users[REF][option]).
Drawing style and helpers from presentation/animations/make_seat_gif.py (imported; its __main__ is not run).
Only text in the images is "<n> cm" (numbers + units), so there is no separate English variant.
Usage: python3 presentation/assets_v7/make_whynot_fig.py      -> presentation/assets_v7/whynot_{lowbed,highbed,vertical,ours}.png
"""
import os, sys, math, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CALC = os.path.join(ROOT, "model", "calc_v13")
sys.path[:0] = [CALC, os.path.join(ROOT, "model"), os.path.join(ROOT, "presentation", "animations")]
_cwd = os.getcwd(); os.chdir(CALC)
import make_seat_gif as G                                   # style, palette, person(), mechanism(), housing(), handrail()
import seat_1dof_fall_catch as FC                           # bed_path, CV (curved seat), CVV (vertical lift), BEHIND
import seat_trajectory as ST
from seat_trajectory import Seat
from seat_relative_motion import track
from seat_1dof_design import path_of, trunk_for, shank_deg, PAD_AMAX
os.chdir(_cwd)
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle

U = (1.60, 0.09, 1.0, 0.29); REF = G.REF; RB = U[1]; F_PICK = 0.70
A = G.D["anim"][REF]                                        # segment lengths + foot length of the REF user
X0, X1, Z0, Z1 = -0.62, 1.10, -0.035, 1.43                  # world window (m); 330 x 280 px on the slide, exported 2x
PX_W, PX_H = 660, 560
WHITE = "#FFFFFF"

def pick(path, f=F_PICK):
    i = int(np.argmin([abs(p["f"] - f) for p in path])); return i, path[i]

def frame(pz):
    """pose dict in the shape make_seat_gif.person() expects (trunk from the same map as the page.json anim)."""
    tr = trunk_for(U, float(pz["Hp"][1]), shank_deg(pz))
    return dict(Hp=[float(v) for v in pz["Hp"]], K=[float(v) for v in pz["K"]], A=[float(v) for v in pz["A"]], tr=tr, f=float(pz["f"]))

def seat_rows(cv):
    ST.A_MAX = PAD_AMAX; sub, path = path_of(U); rows = track(sub, path, Seat(r_e=0.03), cv)
    good = [r for r in rows if r.get("contact") and r.get("ok")]; i, pz = pick(path)
    r = good[i] if i < len(good) else good[-1]; return pz, r, i < len(good)

def data():
    out = {}
    for key, h in (("lowbed", 0.42), ("highbed", 0.58)):
        path = FC.bed_path(U[0], U[3], U[2], 0.0, h + RB); _, pz = pick(path)
        out[key] = dict(fr=frame(pz), edge=0.0, top=h, bed=h)
    for key, cv in (("vertical", FC.CVV), ("ours", FC.CV)):
        pz, r, contact = seat_rows(cv)
        out[key] = dict(fr=frame(pz), edge=float(r["front_x"]), top=float(r["seat_top"]), Q=[float(v) for v in r["Q"]], phi=float(r["phi"]),
                        contact=contact, bed=0.42)
    for d in out.values():
        d["xb"] = d["fr"]["Hp"][0] - FC.BEHIND; d["catch"] = d["edge"] - d["xb"]
    return out

def base(ax, bed_h):
    ax.set_xlim(X0, X1); ax.set_ylim(Z0, Z1); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((X0, Z0), X1 - X0, Z1 - Z0, color=WHITE, zorder=0))
    ax.plot([X0, X1], [0, 0], color=G.MUTED, lw=1.5, zorder=1)
    ax.add_patch(Rectangle((X0, 0), -X0, bed_h - 0.06, color=G.BED, zorder=1)); ax.add_patch(Rectangle((X0, bed_h - 0.06), -X0, 0.06, color=G.MAT, zorder=1))

def seat_top_z(d, x):
    """height of the support's top surface at x (seat: along the tilted board)."""
    if "Q" not in d: return d["top"]
    Q, phi = np.array(d["Q"]), d["phi"]; a = math.radians(phi)
    return float(Q[1] - math.tan(a) * (x - Q[0]))          # rotv(phi, (s, 0)) = (cos s, -sin s): front goes down? see check below

def draw(key, d, path):
    fig = plt.figure(figsize=(PX_W / 200, PX_H / 200), dpi=200); ax = fig.add_axes([0, 0, 1, 1])
    base(ax, d["bed"]); G.handrail(ax)
    fr = d["fr"]; Hp = np.array(fr["Hp"]); xb = d["xb"]
    if key == "vertical":
        Q = np.array(d["Q"]); x0, x1 = Q[0] - G.HALF, Q[0] + G.HALF; z = d["top"]
        ax.add_patch(Rectangle((Q[0] - 0.035, 0.0), 0.07, z - 0.05, color=G.STEEL2, zorder=3))
        ax.add_patch(Rectangle((Q[0] - 0.12, 0.0), 0.24, 0.035, color=G.DEV, zorder=3))
        ax.add_patch(Polygon([(x0, z), (x1, z), (x1, z - 0.05), (x0, z - 0.05)], closed=True, color=G.FOAM_R, zorder=5))
        land_z = 0.035 if xb < Q[0] + 0.12 else 0.0
    elif key == "ours":
        ax.add_patch(Rectangle((0.03, 0), 0.75, 0.04, color=G.DEV, zorder=2)); G.housing(ax); G.mechanism(ax, d["Q"], d["phi"])
        land_z = None
    else:
        land_z = 0.0
    G.person(ax, A, fr, bar=True, rb=RB)
    caught = d["catch"] >= 0
    if key == "ours":                                       # landing point on the tilted board top (board frame y = 0)
        Q = np.array(d["Q"]); e = G.rotv(d["phi"], (1.0, 0.0)); s = (xb - Q[0]) / e[0]; land = Q + s * e
        p0, p1 = G.W(Q, d["phi"], (-G.HALF, 0)), G.W(Q, d["phi"], (G.HALF, 0))
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=G.GOOD, lw=6, solid_capstyle="round", zorder=11)
        lz = float(land[1])
    else:
        lz = land_z
    ax.plot([xb, xb], [Hp[1], lz], color=G.INK if caught else G.RED, lw=2.2, ls=(0, (4, 3)), zorder=12)
    ax.add_patch(Circle((xb, Hp[1]), 0.016, color=G.INK, zorder=13))
    if caught:
        ax.add_patch(Circle((xb, lz), 0.024, color=G.GOOD, zorder=13))
    else:                                                   # miss: red cross on the floor, red gap at the support's top
        c = 0.028; ax.plot([xb - c, xb + c], [lz + c, lz - c], color=G.RED, lw=3, zorder=13); ax.plot([xb - c, xb + c], [lz - c, lz + c], color=G.RED, lw=3, zorder=13)
        ez = d["top"]; ex = d["edge"]
        ax.add_patch(Rectangle((ex, ez - 0.012), xb - ex, 0.024, color=G.RED, alpha=0.22, lw=0, zorder=12))
        ax.annotate("", xy=(ex, ez), xytext=(xb, ez), arrowprops=dict(arrowstyle="<|-|>", color=G.RED, lw=2.0, mutation_scale=11, shrinkA=0, shrinkB=0), zorder=13)
        ax.plot([ex, ex], [ez - 0.05, ez + 0.05], color=G.RED, lw=2.0, zorder=13)
        lab = f"{abs(100 * d['catch']):.0f} cm"
        tx = max((ex + xb) / 2, X0 + 0.20); ty = ez - 0.10
        ax.text(tx, ty, lab, ha="center", va="top", fontsize=17, fontweight="bold", color=G.RED, zorder=14,
                bbox=dict(boxstyle="round,pad=0.15", facecolor=WHITE, edgecolor="none", alpha=0.9))
    fig.savefig(path, facecolor=WHITE); plt.close(fig)

if __name__ == "__main__":
    DD = data()
    for k, d in DD.items():
        print(f"{k:9s} f={d['fr']['f']:.3f} hip=({d['fr']['Hp'][0]:.3f},{d['fr']['Hp'][1]:.3f}) tr={d['fr']['tr']:.0f} edge={d['edge']:.3f} "
              f"top={d['top']:.3f} landing x={d['xb']:.3f} catch={100 * d['catch']:+.1f} cm" + (f" Q={d['Q']} phi={d['phi']:.1f} contact={d['contact']}" if 'Q' in d else ""))
        draw(k, d, os.path.join(HERE, f"whynot_{k}.png"))
    json.dump({k: dict(f=d["fr"]["f"], hip=d["fr"]["Hp"], trunk_deg=d["fr"]["tr"], support_edge_x=d["edge"], support_top=d["top"], landing_x=d["xb"],
                       catch_cm=round(100 * d["catch"], 1)) for k, d in DD.items()}, open(os.path.join(HERE, "whynot_fig.json"), "w"), indent=1)
