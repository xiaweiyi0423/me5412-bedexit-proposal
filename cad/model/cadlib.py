"""Shared base for the CadQuery model of the bed-exit seat (v5.7). Every part module imports this.

Units mm, degrees. WORLD frame: x out from the bed (bed at x < 0), y along the bed toward its head (housing at +y), z up;
y = 0 is the seat's middle plane, floor z = 0.

Four GROUP frames (a part's `instances` place it in its group frame; the group frame is placed in the world per pose):
  "fixed"    : the world frame itself (housing, base, rails, screw, motor, handrail, B bracket).
  "seat"     : seat frame. Origin Q = middle of the cushion's top surface, x_s forward along the seat, z_s normal to it, y = world y.
               world = Location((Qx, 0, Qz), y-axis, phi)   (phi = forward tilt, deg; x' = cos x + sin z, z' = -sin x + cos z)
  "carriage" : rail-aligned frame at pin 1 (c1 axis). X_c = E (up along the rails), Y_c = world y, Z_c = -NF.
               A point a*E + b*NF + y*Y in world = (a, y, -b) in this frame.
               world = Location((P1x, 0, P1z), y-axis, RAIL_ROT)
  "link"     : origin at pivot B (world y 0), X_l along B -> pin 2, Y_l = world y. world = Location((Bx, 0, Bz), y-axis, -atan2(dz, dx))
Rails and the screw are "fixed" parts modelled along their own X (rail-aligned, like the carriage frame) and placed with
Location(start point, y-axis, RAIL_ROT).

A Part is ONE instance modelled in its own part-local frame (the frame its drawing uses); `instances` is the list of
cq.Location that put copies of it into its group frame. For most parts the part-local frame IS the group frame and
instances = [IDENT].

Helper conventions: prism_xz(points[(x, z)], y0, y1) extrudes a profile drawn in the x-z plane from y0 to y1 (y1 > y0).
cyl_y(cx, cz, y0, y1, r) is a cylinder along y. cyl_x(...) along x. box(...) axis-aligned. All return cq.Workplane.
"""
import csv, json, math, os
from dataclasses import dataclass, field
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "cad", "out")
_D = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/cad_sheet.json")))
_PT = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_1dof/parts.json")))
_TT = [[float(c) for c in r] for r in list(csv.reader(open(os.path.join(ROOT, "cad/travel_table.csv"))))[1:]]
m = lambda v: [1000.0 * float(a) for a in v]

# ---------------------------------------------------------------- geometry from the model (mm)
E = tuple(_D["rail_dirs"]["e"]); NF = tuple(_D["rail_dirs"]["nf_rail1_to_rail2"])          # (x, z) unit vectors
RAIL_ROT = -math.degrees(math.atan2(E[1], E[0]))                                              # about +y; maps +X to E
C1S = tuple(1000 * v for v in _D["seat"]["pins_seat_frame"]["c1"])                            # pin 1 in the seat frame (x_s, z_s)
C2S = tuple(1000 * v for v in _D["seat"]["pins_seat_frame"]["c2"])
HALF = 1000 * _D["seat"]["half_len"]; LIP = 1000 * _D["seat"]["lip"]; SEAT_W = 440.0
RAIL1_LO = tuple(m(_D["rail1"]["lo"])); RAIL2_LO = tuple(m(_D["rail2"]["lo"])); RAIL_LEN = 1000 * _D["rail1"]["length"]
RAIL_GAP = 150.0; CARR_SPAN = 150.0
SCREW_LO = tuple(m(_D["screw"]["axis_lo"])); SCREW_HI = tuple(m(_D["screw"]["axis_hi"]))
SCREW_LEN = math.hypot(SCREW_HI[0] - SCREW_LO[0], SCREW_HI[1] - SCREW_LO[1]); STROKE = 1000 * _D["screw"]["stroke"]
B = tuple(m(_D["link"]["ground_pivot_B"])); LINK_LEN = 1000 * _D["link"]["length"]
HOUSING = [tuple(m(p)) for p in _PT["housing"]["outline_xz"]]                                  # side-view outline (x, z), closed implicitly
MOTOR_XZ = [tuple(m(p)) for p in _D["housing"]["motor_xz"]]
POST = dict(x=1000 * _D["handrail"]["post"]["x"], y=300.0, top=1000 * _D["handrail"]["post"]["top_z"]); BAR_Y = (-50.0, 300.0)
BASE = dict(x=(30.0, 780.0), y=(-270.0, 380.0), top=35.0); FOOT = dict(x=(200.0, 620.0), y=(-220.0, 220.0), z=(35.0, 47.0))
BED_TOP = 420.0
# layer stack across y (mm) - v5.7, knuckle moved inboard so the J1 flange fits outboard of it
Y = dict(seat_edge=220.0, beam=(-205.0, 204.0), knuckle=(204.0, 216.0), flange=(216.0, 226.0), brgB=(229.0, 246.0), wall_in=(250.0, 252.0),
         arm_c2=(258.0, 270.0), hub=(258.0, 282.0), window=(256.0, 284.0), rod_c2=(270.0, 282.0), link=276.0, plate=(288.0, 308.0), brgA=(290.0, 307.0),
         locknut=(308.0, 315.0), shaft_end=318.0, carriage=(308.0, 331.7), rail=(321.0, 336.0), screw=322.0, back=(336.0, 351.0), wall_out=(356.0, 358.0))
# seat-frame z levels (mm): cushion top 0, board -80..-92, cells -92..-100, beam -100..-130, arms -100..-110
SZ = dict(foam_rear=-50.0, foam_front=-80.0, board=(-92.0, -80.0), cells=(-100.0, -92.0), beam=(-130.0, -100.0), arms=(-110.0, -100.0), split=-20.0)

def _interp(s):
    s = max(0.0, min(_TT[-1][0], s)); i = 0
    while i < len(_TT) - 2 and _TT[i + 1][0] < s: i += 1
    a, b = _TT[i], _TT[i + 1]; t = (s - a[0]) / ((b[0] - a[0]) or 1)
    return [a[k] + t * (b[k] - a[k]) for k in range(len(a))]

def pose(stroke_mm):
    """screw stroke -> dict(Q=(x, z), phi=deg, P1=(x, z), P2=(x, z)) in mm."""
    r = _interp(stroke_mm); return dict(stroke=r[0], Q=(r[1], r[2]), phi=r[3], P1=(r[4], r[5]), P2=(r[6], r[7]))
POSES = {"flush": pose(0.0), "mid": pose(STROKE / 2), "top": pose(STROKE)}

IDENT = cq.Location()
def loc(x=0.0, y=0.0, z=0.0, rot_y=0.0): return cq.Location(cq.Vector(x, y, z), cq.Vector(0, 1, 0), rot_y)
def ab(a, b):
    """rail coordinates -> carriage-frame (x, z): a along E, b along NF."""
    return (a, -b)

def group_loc(group, p):
    """group frame -> world for pose dict p."""
    if group == "fixed" or group == "ref": return IDENT
    if group == "seat": return loc(p["Q"][0], 0, p["Q"][1], p["phi"])
    if group == "carriage": return loc(p["P1"][0], 0, p["P1"][1], RAIL_ROT)
    if group == "link":
        dx, dz = p["P2"][0] - B[0], p["P2"][1] - B[1]; return loc(B[0], 0, B[1], -math.degrees(math.atan2(dz, dx)))
    raise ValueError(group)

# ---------------------------------------------------------------- primitives
def prism_xz(pts, y0, y1):
    """closed polygon in (x, z), extruded from y0 to y1 (y1 > y0)."""
    return cq.Workplane("XZ", origin=(0, y0, 0)).polyline(list(pts)).close().extrude(-(y1 - y0))
def cyl_y(cx, cz, y0, y1, r):
    return cq.Workplane("XZ", origin=(0, y0, 0)).center(cx, cz).circle(r).extrude(-(y1 - y0))
def tube_y(cx, cz, y0, y1, ro, ri):
    return cyl_y(cx, cz, y0, y1, ro).cut(cyl_y(cx, cz, y0 - 1, y1 + 1, ri))
def cyl_x(x0, x1, cy, cz, r):
    return cq.Workplane("YZ", origin=(x0, 0, 0)).center(cy, cz).circle(r).extrude(x1 - x0)
def cyl_z(cx, cy, z0, z1, r):
    return cq.Workplane("XY", origin=(0, 0, z0)).center(cx, cy).circle(r).extrude(z1 - z0)
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))
def rect_tube_y(x0, x1, z0, z1, y0, y1, t):
    """rectangular hollow section running along y."""
    return box(x0, x1, y0, y1, z0, z1).cut(box(x0 + t, x1 - t, y0 - 1, y1 + 1, z0 + t, z1 - t))
def rect_tube_x(x0, x1, y0, y1, z0, z1, t):
    return box(x0, x1, y0, y1, z0, z1).cut(box(x0 - 1, x1 + 1, y0 + t, y1 - t, z0 + t, z1 - t))
def rect_tube_z(x0, x1, y0, y1, z0, z1, t):
    return box(x0, x1, y0, y1, z0, z1).cut(box(x0 + t, x1 - t, y0 + t, y1 - t, z0 - 1, z1 + 1))
def holes_y(wp, centers, r, y0=-1e4, y1=1e4):
    for cx, cz in centers: wp = wp.cut(cyl_y(cx, cz, y0, y1, r))
    return wp
def pcd(cx, cz, radius, n, start_deg=0.0):
    return [(cx + radius * math.cos(math.radians(start_deg + 360 * k / n)), cz + radius * math.sin(math.radians(start_deg + 360 * k / n))) for k in range(n)]

# ---------------------------------------------------------------- the part record
@dataclass
class Part:
    code: str                 # BOM code, e.g. "S7"; a second piece of one BOM line gets a suffix: "S4b"
    name: str                 # Chinese name, as the BOM
    material: str             # material / model, as the BOM
    group: str                # "seat" | "carriage" | "link" | "fixed" | "ref" (reference only: bed)
    shape: cq.Workplane       # ONE instance, part-local frame (mm)
    instances: list = field(default_factory=lambda: [IDENT])   # part-local -> group frame
    color: str = "#8C96A0"
    buy: bool = False         # purchased part (envelope only, no drawing)
    drawing: bool = True      # make a drawing sheet
    params: list = field(default_factory=list)   # [(label, value-with-unit)] key dimensions for the drawing table
    note: str = ""            # one line for the drawing / page
    views: str = "auto"       # drawing hint, free text for the drawing module

    @property
    def qty(self): return len(self.instances)

COLORS = dict(steel="#6B7A8A", steel_dark="#4A5663", alu="#B9C3CD", foam_r="#E3B26A", foam_f="#F1D5A6", wood="#C9A36B", blue="#3D6FB6",
              blue_light="#A9C1E4", red="#B3261E", ink="#2A3440", rubber="#2B2B2B", bed="#D5DAE0", buy="#3B4652")

def check(parts):
    """quick sanity: every part has a valid non-empty solid; returns list of (code, volume)."""
    out = []
    for p in parts:
        v = p.shape.val(); assert v.isValid(), p.code; vol = sum(s.Volume() for s in p.shape.solids().vals()); assert vol > 0, p.code; out.append((p.code, round(vol)))
    return out

# ---------------------------------------------------------------- drive stack at the top end of the screw (shared by drive and housing)
# screw-local frame: origin SCREW_LO, X along E, Y = world y, Z = -NF (same rotation as the rails); screw axis at Y = Y["screw"].
# Nut travel along X: 95 +- 22.5 at the flush pose ... 426 +- 22.5 at the top.
# Stack beyond the nut (X, mm): BK12 fixed support 452-477, pulley 45T 480-500, brake (envelope dia 90) 505-545, limiter (dia 60) 548-578.
# BF12 floating support 5-25 at the low end. The stack's radius (46 incl. clearance) is larger than the 14 mm from the screw axis
# to the back plate face (y 336): the back plate H1 has a window there and a drive cover H5 bulges out to y 372.
DRIVE = dict(bf=(5.0, 25.0), bk=(452.0, 477.0), pulley=(480.0, 500.0), brake=(505.0, 545.0), limiter=(548.0, 578.0), r_env=46.0,
             window_x=(445.0, 585.0), cover_y=(351.0, 372.0))
def screw_to_world(x, z_local=0.0):
    """screw-local (X, Z) -> world (x, z); Z = -NF."""
    return (SCREW_LO[0] + x * E[0] - z_local * NF[0], SCREW_LO[1] + x * E[1] - z_local * NF[1])
