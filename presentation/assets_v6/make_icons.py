"""Side-view pictograms for the deck (no <text>; labels go on the slide as real text).
Writes icons/<name>.svg and a preview sheet preview.html. Units: px in a 320x220 box, floor at y=200, 1 m = 110 px."""
import os
OUT = os.path.join(os.path.dirname(__file__), "icons"); os.makedirs(OUT, exist_ok=True)
INK, BODY, LINE, FILL, ACC, ACCL, GREY = "#18202A", "#3F4A57", "#7D8792", "#E9E5DC", "#B4620A", "#F3E3CF", "#C3C9D1"
W, H, FY, S = 320, 220, 200, 110.0
X0 = 120                                     # bed edge (px)
P = lambda x, z: (X0 + x * S, FY - z * S)    # metres (x forward from the bed edge, z up) -> px

def svg(body, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" aria-label="{label}">{body}</svg>'
def rect(x, y, w, h, fill=FILL, stroke=BODY, sw=2.5, rx=3, op=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"{d}/>'
def line(pts, col=BODY, sw=3, dash=None, op=1, cap="round"):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="{cap}" stroke-linejoin="round" opacity="{op}"{d}/>'
def poly(pts, fill=FILL, stroke=BODY, sw=2.5, op=1):
    return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" opacity="{op}"/>'
def circ(x, y, r, fill=INK, stroke="none", sw=0, op=1):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'
def arrow(a, b, col=ACC, sw=3.5):
    import math
    an = math.atan2(b[1] - a[1], b[0] - a[0]); h = 10
    p1 = (b[0] - h * math.cos(an - 0.45), b[1] - h * math.sin(an - 0.45)); p2 = (b[0] - h * math.cos(an + 0.45), b[1] - h * math.sin(an + 0.45))
    return line([a, b], col, sw) + poly([b, p1, p2], col, col, 1)
floor = line([(6, FY), (W - 6, FY)], LINE, 2.5)

def person(H_, K_, A_, S_, hand=None, col=INK):
    """Stick figure from metre coords; head along the trunk past the shoulder."""
    import math
    h, k, a, s = P(*H_), P(*K_), P(*A_), P(*S_)
    ut = ((S_[0] - H_[0]), (S_[1] - H_[1])); n = math.hypot(*ut); ut = (ut[0] / n, ut[1] / n)
    hd = P(S_[0] + 0.14 * ut[0], S_[1] + 0.14 * ut[1])
    toe = (a[0] + 20, a[1] + 4)
    out = line([a, k, h, s], col, 6.5) + line([a, toe], col, 6.5) + circ(*hd, 11, col)
    if hand:
        hp = P(*hand); el = ((s[0] + hp[0]) / 2 + 2, (s[1] + hp[1]) / 2 + 8); out += line([s, el, hp], col, 5)
    return out

# one mid-rise pose for the four support options (hip in front of the bed edge)
MID = dict(H_=(0.27, 0.56), K_=(0.64, 0.47), A_=(0.56, 0.06), S_=(0.58, 0.97))
def bed(top, risers=False):
    y = FY - top * S; legs = ""
    if risers:
        legs = rect(16, FY - 16, 22, 16, ACCL, ACC, 2.5, 2) + rect(X0 - 30, FY - 16, 22, 16, ACCL, ACC, 2.5, 2)
        frame = rect(10, y, X0 - 10, (FY - 16) - y, FILL, BODY)
    else:
        frame = rect(10, y, X0 - 10, FY - y, FILL, BODY)
    return frame + rect(10, y - 2, X0 - 10, 12, "#FFFFFF", BODY, 2) + legs
def rail_L(col=BODY):
    px, top = P(1.05, 0.0), P(1.05, 0.88)
    return line([px, top, P(0.78, 0.88)], col, 6)
HAND = (0.80, 0.88)

ICONS = {}
# ---- whynot: four ways to rise, same moment (hip just off the support)
ICONS["opt_lowbed"] = ("低床 0.42 m 加 L 形扶手，人起到一半时臀部已离开床沿", floor + bed(0.42) + rail_L() + person(**MID, hand=HAND))
ICONS["opt_highbed"] = ("床脚垫高到 0.58 m 加扶手，人起到一半时臀部已离开床沿", floor + bed(0.58, True) + rail_L() + person(**MID, hand=HAND))
vz = 0.53; vs = P(-0.10, vz)
ICONS["opt_vertical"] = ("竖直升降座板：座板只往上走，人起到一半时臀部已经到了座板前面",
    floor + bed(0.42) + rail_L() + rect(vs[0], vs[1], 0.26 * S, 10, ACCL, ACC, 2.5, 2) + rect(vs[0] + 0.10 * S, vs[1] + 10, 0.06 * S, FY - vs[1] - 10, GREY, BODY, 2, 1) +
    arrow((vs[0] - 0.06 * S, FY - 0.30 * S), (vs[0] - 0.06 * S, vs[1] - 6)) + person(**MID, hand=HAND))
# ours: inclined housing behind, seat under the hip, tilted ~13 deg
import math
ph = math.radians(13); c = P(0.24, 0.50); L1, L2 = 0.15 * S, 0.14 * S
seat = [(c[0] - L1 * math.cos(ph), c[1] - L1 * math.sin(ph)), (c[0] + L2 * math.cos(ph), c[1] + L2 * math.sin(ph))]
seat_poly = [seat[0], seat[1], (seat[1][0] - 3, seat[1][1] + 11), (seat[0][0] - 3, seat[0][1] + 11)]
house = [P(0.02, 0.0), P(0.50, 0.0), P(0.50, 0.80), P(0.34, 0.80)]
ICONS["opt_ours"] = ("起身台：斜导轨座板跟着大腿前移、上升、前倾，人起到一半时座板还在臀部下面",
    floor + bed(0.42) + poly(house, "#F6EFE4", "#C9B79F", 2) + line([P(0.06, 0.10), P(0.40, 0.72)], ACC, 4, "8 6", 0.9) + rail_L() + poly(seat_poly, ACC, ACC, 2) +
    arrow(P(-0.02, 0.30), P(0.10, 0.42), ACC, 3) + person(**MID, hand=HAND))

# ---- prior: existing products (furniture only, the moving part in accent)
def chair(seat_z=0.45, x=70, w=110, back=True, col=BODY, fill=FILL, op=1):
    y = FY - seat_z * S; out = rect(x, y, w, 14, fill, col, 2.5, 3, op)
    out += line([(x + 8, y + 14), (x + 8, FY)], col, 4, op=op) + line([(x + w - 8, y + 14), (x + w - 8, FY)], col, 4, op=op)
    if back: out += rect(x - 4, y - 0.45 * S, 14, 0.45 * S, fill, col, 2.5, 3, op)
    return out
# lift chair: seat and back tilt forward and rise on a base
def lchair(col, fill, dash=None):
    y = FY - 0.46 * S
    return rect(70, y, 120, 16, fill, col, 2.5, 4, 1, dash) + rect(62, y - 0.46 * S, 18, 0.46 * S + 8, fill, col, 2.5, 4, 1, dash)
base = rect(58, FY - 18, 150, 18, GREY, BODY, 2, 3)
rest = lchair(LINE, "none", "6 5")
lift = '<g transform="translate(18 -30) rotate(16 190 150)">' + lchair(ACC, ACCL) + '</g>'
mech = line([(96, FY - 18), (150, 116)], BODY, 4) + line([(160, FY - 18), (112, 128)], BODY, 4)
ICONS["prior_liftchair"] = ("升降椅：整张椅子往前上方抬起并前倾，虚线为平时位置", floor + base + rest + mech + lift + arrow((214, 112), (236, 80)))
ICONS["prior_highbed"] = ("床脚垫高的床加床边扶手", floor + bed(0.58, True).replace(f'width="{X0 - 10:.1f}"', 'width="190.0"') + line([P(1.10, 0.0), P(1.10, 0.95), P(0.95, 0.95)], BODY, 6))
# UpEasy-style cushion: hinged at the front edge, back raised by a gas spring
cy = FY - 0.45 * S; hx = 196
cush = poly([(80, cy - 52), (hx, cy - 4), (hx, cy), (80, cy)], ACCL, ACC, 2.5)
spring = line([(100, cy - 2), (108, cy - 36), (116, cy - 6), (124, cy - 30), (132, cy - 4)], ACC, 2.5)
ICONS["prior_cushion"] = ("气弹簧座垫：放在椅子上，前缘铰接，后部被气弹簧顶起", floor + chair(0.45, 70, 130) + cush + spring + circ(hx, cy - 2, 5, ACC) + arrow((88, cy - 20), (96, cy - 64)))
# research chair / patent: seat rises on a column, armrest and seat force sensing
sz = 0.62; sy = FY - sz * S
rc = rect(84, FY - 0.45 * S, 120, 14, "none", LINE, 2, 3).replace('/>', ' stroke-dasharray="6 5"/>') + rect(84, sy, 120, 14, ACCL, ACC, 2.5, 3) + rect(134, sy + 14, 20, FY - sy - 14, GREY, BODY, 2, 2) + \
     line([(80, sy - 50), (80, FY)], BODY, 4) + line([(80, sy - 30), (190, sy - 30)], BODY, 5) + \
     "".join(circ(x, sy + 7, 5, "#2F7A55") for x in (104, 144, 184)) + circ(150, sy - 30, 6, "#2F7A55") + arrow((222, FY - 0.40 * S), (222, sy - 4))
ICONS["prior_research"] = ("研究原型和专利：座面竖直抬起，座下和扶手测力判断人想起身（绿点为测力处）", floor + rc)

for k, (lab, body) in ICONS.items():
    open(os.path.join(OUT, k + ".svg"), "w").write(svg(body, lab))
open(os.path.join(os.path.dirname(__file__), "preview.html"), "w").write(
    '<html><body style="background:#FCFBF8;display:flex;flex-wrap:wrap;gap:20px;padding:20px">' +
    "".join(f'<div style="border:1px solid #ddd;background:#fff">{svg(b, l)}</div>' for k, (l, b) in ICONS.items()) + "</body></html>")
print({k: len(svg(b, l)) for k, (l, b) in ICONS.items()})
