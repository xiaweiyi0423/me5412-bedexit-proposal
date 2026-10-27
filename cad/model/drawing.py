"""Reference drawing sheets (A3 landscape SVG, first-angle projection) for the bed-exit seat parts.

project(shape, view)          -> dict(vis=[polyline...], hid=[polyline...]) in the view's 2-D coords (mm)
draw_part(part, path)         -> one sheet per part: front / top / left / iso, overall dimensions, key-dimension table, title block
draw_assembly(parts, pose, p) -> the whole assembly in WORLD at a pose, visible lines only, scale 1:10, parts list

Views (eye positions, first-angle layout): front = eye at -y, top = eye at +z (placed below front), left = eye at -x
(placed right of front), iso = eye at (+x, -y, +z). Sheets are plain black-on-white SVG (shown as <img>, no CSS variables).
"""
import html, math
import cadquery as cq
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_EDGE
from OCP.TopoDS import TopoDS
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepLib import BRepLib
import cadlib

VIEWS = {"front": ((0, -1, 0), (1, 0, 0)), "top": ((0, 0, 1), (1, 0, 0)), "left": ((-1, 0, 0), (0, -1, 0)),
         "iso": ((1, -1, 1), (1, 1, 0))}
FONT = '"Noto Sans SC","PingFang SC","Microsoft YaHei","Hiragino Sans GB",sans-serif'
SCALES = [(2, 1), (1, 1), (1, 2), (1, 2.5), (1, 5), (1, 10), (1, 20), (1, 50)]
SHEET_W, SHEET_H = 420.0, 297.0
COL_X = 284.0                      # right column (table + title block) starts here
AREA = (12.0, 12.0, COL_X - 6.0, SHEET_H - 12.0)   # x0, y0, x1, y1 for the views

# ---------------------------------------------------------------- geometry helpers
def to_topods(shape):
    """cq.Workplane / cq.Shape / list -> TopoDS_Shape (compound when several)."""
    if isinstance(shape, cq.Workplane):
        vals = [v for v in shape.vals() if isinstance(v, cq.Shape)]
        return vals[0].wrapped if len(vals) == 1 else cq.Compound.makeCompound(vals).wrapped
    if isinstance(shape, cq.Shape): return shape.wrapped
    if isinstance(shape, (list, tuple)): return cq.Compound.makeCompound(list(shape)).wrapped
    return shape

def bbox(shape):
    """tight axis-aligned box (xmin, ymin, zmin, xmax, ymax, zmax)."""
    b = Bnd_Box(); BRepBndLib.AddOptimal_s(to_topods(shape), b, False, False); return b.Get()

def _edges_to_polylines(comp, defl):
    out = []
    if comp is None or comp.IsNull(): return out
    BRepLib.BuildCurves3d_s(comp)
    ex = TopExp_Explorer(comp, TopAbs_EDGE)
    while ex.More():
        e = TopoDS.Edge_s(ex.Current())
        try:
            c = BRepAdaptor_Curve(e); u0, u1 = c.FirstParameter(), c.LastParameter()
            if c.GetType() == GeomAbs_Line:
                pts = [c.Value(u0), c.Value(u1)]
            else:
                d = GCPnts_QuasiUniformDeflection(c, defl, u0, u1)
                if d.IsDone() and d.NbPoints() >= 2: pts = [d.Value(i) for i in range(1, d.NbPoints() + 1)]
                else: pts = [c.Value(u0 + (u1 - u0) * k / 24) for k in range(25)]
            out.append([(p.X(), p.Y()) for p in pts])
        except Exception:
            pass
        ex.Next()
    return out

def project(shape, view, hidden=True, defl=0.05):
    """HLR projection. shape: Workplane / Shape / TopoDS. Returns dict(vis, hid) of polylines [(u, v), ...]."""
    d, xd = VIEWS[view]
    algo = HLRBRep_Algo(); algo.Add(to_topods(shape))
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(*d), gp_Dir(*xd)))); algo.Update(); algo.Hide()
    h = HLRBRep_HLRToShape(algo)
    vis = []
    for c in (h.VCompound(), h.OutLineVCompound(), h.Rg1LineVCompound()): vis += _edges_to_polylines(c, defl)
    hid = []
    if hidden:
        for c in (h.HCompound(), h.OutLineHCompound()): hid += _edges_to_polylines(c, defl)
    return dict(vis=vis, hid=hid)

def _pbox(pr):
    us = [p[0] for pl in pr["vis"] + pr["hid"] for p in pl]; vs = [p[1] for pl in pr["vis"] + pr["hid"] for p in pl]
    if not us: return (0, 0, 1, 1)
    return (min(us), min(vs), max(us), max(vs))

# ---------------------------------------------------------------- svg helpers
def fnum(v):
    v = abs(v); return f"{v:.1f}".rstrip("0").rstrip(".") if v < 10 else f"{v:.0f}"
def esc(t): return html.escape(str(t))
def wrap(text, width_mm, fs):
    """greedy wrap by estimated glyph width (CJK ~ 1.0 em, ASCII ~ 0.56 em)."""
    lines, cur, w = [], "", 0.0
    for ch in str(text):
        cw = fs * (1.0 if ord(ch) > 0x2E80 else 0.56)
        if w + cw > width_mm and cur:
            lines.append(cur); cur, w = "", 0.0
            if ch == " ": continue
        cur += ch; w += cw
    if cur: lines.append(cur)
    return lines or [""]

class Sheet:
    def __init__(self):
        self.o = []
    def add(self, s): self.o.append(s)
    def line(self, x1, y1, x2, y2, w=0.25, color="#000", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{w}"{da}/>')
    def rect(self, x, y, w, h, sw=0.35, fill="none"):
        self.add(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="#000" stroke-width="{sw}"/>')
    def text(self, x, y, t, fs=3.0, anchor="start", weight=None, rot=None, color="#000"):
        tr = f' transform="rotate({rot} {x:.2f} {y:.2f})"' if rot else ""
        fw = f' font-weight="{weight}"' if weight else ""
        self.add(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{fs}" text-anchor="{anchor}" fill="{color}"{fw}{tr}>{esc(t)}</text>')
    def polylines(self, pls, tf, w, color="#000", dash=None):
        if not pls: return
        d = []
        for pl in pls:
            pts = [tf(u, v) for u, v in pl]
            d.append("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts))
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{" ".join(d)}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"{da}/>')
    def arrow(self, x, y, dx, dy, L=2.6, W=0.9):
        n = math.hypot(dx, dy) or 1; dx, dy = dx / n, dy / n; px, py = -dy, dx
        self.add(f'<path d="M{x:.2f},{y:.2f} L{x - L * dx + W * px:.2f},{y - L * dy + W * py:.2f} L{x - L * dx - W * px:.2f},{y - L * dy - W * py:.2f} Z" fill="#000"/>')
    def dim_h(self, xa, xb, y_obj, y_dim, value):
        """horizontal dimension between xa..xb, extension lines from y_obj to y_dim."""
        s = 1 if y_dim > y_obj else -1
        for x in (xa, xb): self.line(x, y_obj + s * 1.0, x, y_dim + s * 1.5, 0.18)
        self.line(xa, y_dim, xb, y_dim, 0.18)
        if abs(xb - xa) > 7: self.arrow(xa, y_dim, -1, 0); self.arrow(xb, y_dim, 1, 0)
        else: self.arrow(xa, y_dim, 1, 0); self.arrow(xb, y_dim, -1, 0)
        self.text((xa + xb) / 2, y_dim - 1.0, fnum(value), 3.2, "middle")
    def dim_v(self, ya, yb, x_obj, x_dim, value):
        s = 1 if x_dim > x_obj else -1
        for y in (ya, yb): self.line(x_obj + s * 1.0, y, x_dim + s * 1.5, y, 0.18)
        self.line(x_dim, ya, x_dim, yb, 0.18)
        if abs(yb - ya) > 7: self.arrow(x_dim, ya, 0, -1); self.arrow(x_dim, yb, 0, 1)
        else: self.arrow(x_dim, ya, 0, 1); self.arrow(x_dim, yb, 0, -1)
        xm = x_dim - 1.0; ym = (ya + yb) / 2; self.text(xm, ym, fnum(value), 3.2, "middle", rot=-90)
    def svg(self, title):
        body = "\n".join(self.o)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SHEET_W:.0f} {SHEET_H:.0f}" width="{SHEET_W:.0f}mm" height="{SHEET_H:.0f}mm" '
                f'font-family=\'{FONT}\'><title>{esc(title)}</title><rect width="{SHEET_W:.0f}" height="{SHEET_H:.0f}" fill="#fff"/>\n{body}\n</svg>')

def frame(sh):
    sh.rect(5, 5, SHEET_W - 10, SHEET_H - 10, 0.7)

def first_angle_symbol(sh, x, y):
    """first-angle symbol: truncated cone side view (narrow end left), circles on the right (facing the wide end)."""
    sh.add(f'<path d="M{x:.2f},{y + 1.6:.2f} L{x + 7:.2f},{y:.2f} L{x + 7:.2f},{y + 6:.2f} L{x:.2f},{y + 4.4:.2f} Z" fill="none" stroke="#000" stroke-width="0.25"/>')
    sh.line(x - 1, y + 3, x + 8, y + 3, 0.13, dash="2,0.6,0.4,0.6")
    cx, cy = x + 12.5, y + 3
    sh.add(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3" fill="none" stroke="#000" stroke-width="0.25"/><circle cx="{cx:.2f}" cy="{cy:.2f}" r="1.4" fill="none" stroke="#000" stroke-width="0.25"/>')
    sh.line(cx - 4, cy, cx + 4, cy, 0.13, dash="2,0.6,0.4,0.6"); sh.line(cx, cy - 4, cx, cy + 4, 0.13, dash="2,0.6,0.4,0.6")

def title_block(sh, rows, note, y_top=None):
    """rows: [(label, value)]; drawn bottom-right inside the frame, width = right column. Returns its top y."""
    x0, x1 = COL_X, SHEET_W - 5; w = x1 - x0; lab_w = 20.0; fs = 3.0
    lines = []
    for lab, val in rows:
        vl = wrap(val, w - lab_w - 3, fs) if lab != "投影" else [""]
        lines.append((lab, vl, max(6.0, 1.6 + 4.0 * len(vl))))
    nl = wrap(note, w - 4, 2.4); h_note = 2.5 + 3.3 * len(nl)
    H = sum(h for _, _, h in lines) + h_note
    y = SHEET_H - 5 - H; top = y
    sh.rect(x0, y, w, H, 0.5)
    for lab, vl, h in lines:
        sh.line(x0, y + h, x1, y + h, 0.18); sh.line(x0 + lab_w, y, x0 + lab_w, y + h, 0.18)
        sh.text(x0 + 2, y + h / 2 + 1.1, lab, fs, color="#333")
        if lab == "投影":
            first_angle_symbol(sh, x0 + lab_w + 3, y + h / 2 - 3); sh.text(x0 + lab_w + 22, y + h / 2 + 1.1, "第一角投影", fs)
        else:
            for k, t in enumerate(vl): sh.text(x0 + lab_w + 2, y + 4.4 + 4.0 * k, t, fs, weight="bold" if lab in ("零件名称", "编号") else None)
        y += h
    for k, t in enumerate(nl): sh.text(x0 + 2, y + 3.4 + 3.3 * k, t, 2.4, color="#333")
    return top

def table(sh, x0, y0, w, header, rows, fs=2.8, col_frac=0.5, title=None):
    """two-column table, returns bottom y."""
    y = y0
    if title: sh.text(x0, y + 3.5, title, 3.4, weight="bold"); y += 5.5
    c1 = w * col_frac
    sh.line(x0, y, x0 + w, y, 0.35)
    if header:
        sh.text(x0 + 1.5, y + 3.6, header[0], fs, color="#444"); sh.text(x0 + c1 + 1.5, y + 3.6, header[1], fs, color="#444"); y += 5.2; sh.line(x0, y, x0 + w, y, 0.25)
    for a, b in rows:
        la = wrap(a, c1 - 3, fs); lb = wrap(b, w - c1 - 3, fs); n = max(len(la), len(lb)); h = 1.8 + 3.5 * n
        for k, t in enumerate(la): sh.text(x0 + 1.5, y + 3.7 + 3.5 * k, t, fs)
        for k, t in enumerate(lb): sh.text(x0 + c1 + 1.5, y + 3.7 + 3.5 * k, t, fs)
        y += h; sh.line(x0, y, x0 + w, y, 0.13)
    return y

# ---------------------------------------------------------------- layout
def _layout(boxes, scale, dim=True):
    """boxes: dict view -> (u0, v0, u1, v1) in mm. Returns origins dict view -> (ox, oy) (sheet coords of the box's top-left) or None."""
    gap = 17.0 if dim else 10.0; dl = 14.0 if dim else 4.0
    f, t, l = boxes["front"], boxes["top"], boxes["left"]
    Wf, Hf = (f[2] - f[0]) * scale, (f[3] - f[1]) * scale
    Wl = (l[2] - l[0]) * scale; Ht = (t[3] - t[1]) * scale
    ox_f = AREA[0] + dl; oy_f = AREA[1] + dl
    ox_l = ox_f + Wf + gap; oy_t = oy_f + Hf + gap
    if ox_l + Wl > AREA[2] or oy_t + Ht > AREA[3]: return None
    if max(Wf, Wl) < 1 or max(Hf, Ht) < 1: return None
    return dict(front=(ox_f, oy_f), top=(ox_f, oy_t), left=(ox_l, oy_f), iso_cell=(ox_l, oy_t, AREA[2], AREA[3]))

def _tf(box, ox, oy, s):
    u0, v0, u1, v1 = box
    return lambda u, v: (ox + (u - u0) * s, oy + (v1 - v) * s)

def _sc_label(sc): a, b = sc; return f"{a:g}:{b:g}"

def draw_views(sh, prs, scale_choice=None, hidden=True, dims=None, iso_grow=1.0):
    """prs: dict view -> projection. Picks the largest standard scale that fits; draws views (+ iso in the free cell).
    dims: dict(width, height, depth) values for the overall dimensions (None: no dims). Returns the scale label."""
    boxes = {k: _pbox(v) for k, v in prs.items()}
    chosen = None
    for sc in ([scale_choice] if scale_choice else SCALES):
        s = sc[0] / sc[1]; lay = _layout(boxes, s, dim=dims is not None)
        if lay: chosen = (sc, s, lay); break
    if not chosen:
        sc = (1, 100); s = 0.01; lay = _layout(boxes, s, dim=dims is not None) or dict(front=(20, 20), top=(20, 150), left=(150, 20), iso_cell=(150, 150, 270, 280)); chosen = (sc, s, lay)
    sc, s, lay = chosen
    wv, wh = 0.5, 0.25
    labels = {"front": "主视图", "top": "俯视图", "left": "左视图"}
    for k in ("front", "top", "left"):
        ox, oy = lay[k]; tf = _tf(boxes[k], ox, oy, s)
        if hidden: sh.polylines(prs[k]["hid"], tf, wh, "#777", "1.6,0.9")
        sh.polylines(prs[k]["vis"], tf, wv)
        u0, v0, u1, v1 = boxes[k]
        sh.text(ox, oy + (v1 - v0) * s + 5.5 if k != "top" else oy + (v1 - v0) * s + 5.5, labels[k], 2.8, color="#555")
    if dims:
        f = boxes["front"]; ox, oy = lay["front"]; W = (f[2] - f[0]) * s; Hh = (f[3] - f[1]) * s
        sh.dim_h(ox, ox + W, oy, oy - 8, dims["width"]); sh.dim_v(oy, oy + Hh, ox, ox - 8, dims["height"])
        t = boxes["top"]; ox, oy = lay["top"]; Ht = (t[3] - t[1]) * s
        sh.dim_v(oy, oy + Ht, ox, ox - 8, dims["depth"])
    if "iso" in prs:
        cx0, cy0, cx1, cy1 = lay["iso_cell"]; ib = boxes["iso"]; iw, ih = ib[2] - ib[0], ib[3] - ib[1]
        cw, ch = cx1 - cx0 - 6, cy1 - cy0 - 10
        if cw > 25 and ch > 25 and iw > 0 and ih > 0:
            si = min(s * iso_grow, cw / iw, ch / ih); ox = cx0 + 3 + (cw - iw * si) / 2; oy = cy0 + 3 + (ch - ih * si) / 2
            sh.polylines(prs["iso"]["vis"], _tf(ib, ox, oy, si), 0.35)
            sh.text(cx0 + 3, cy1 - 1.5, "轴测图" + ("（比例同主视图）" if abs(si - s) < 1e-9 else "（不按比例）"), 2.6, color="#555")
    return _sc_label(sc)

# ---------------------------------------------------------------- public
NOTE = "参考图：尺寸来自计算模型；公差、焊缝、表面处理由角色 3 定"
PROJECT = "ME5412 床边起身台 v5.7"

def draw_part(part, path):
    shp = part.shape
    prs = {k: project(shp, k, hidden=(k != "iso")) for k in ("front", "top", "left", "iso")}
    x0, y0, z0, x1, y1, z1 = bbox(shp)
    sh = Sheet(); frame(sh)
    sc = draw_views(sh, prs, dims=dict(width=x1 - x0, height=z1 - z0, depth=y1 - y0))
    rows = [("零件名称", part.name), ("编号", part.code), ("材料", part.material), ("数量", str(part.qty)), ("比例", sc), ("单位", "mm"), ("投影", ""), ("项目", PROJECT)]
    top = title_block(sh, rows, NOTE + ("。外购件：外形按样本估，订货以厂家图纸为准" if part.buy else ""))
    params = [(a, str(b)) for a, b in (part.params or [])]
    params = [("外形（x × y × z）", f"{fnum(x1 - x0)} × {fnum(y1 - y0)} × {fnum(z1 - z0)}")] + params
    yb = table(sh, COL_X, 12, SHEET_W - 5 - COL_X, ("尺寸", "数值"), params, fs=2.7, col_frac=0.5, title="关键尺寸")
    if part.note:
        for k, t in enumerate(wrap(part.note, SHEET_W - 5 - COL_X - 2, 2.6)):
            if yb + 6 + 3.4 * k < top - 3: sh.text(COL_X + 1, yb + 6 + 3.4 * k, t, 2.6, color="#333")
    open(path, "w", encoding="utf-8").write(sh.svg(f"{part.code} {part.name}"))
    return sc

def world_shapes(parts, pose_name, skip_ref=True):
    """[(code, idx, cq.Shape in world)] for every instance at a pose."""
    p = cadlib.POSES[pose_name]; out = []
    for part in parts:
        if skip_ref and part.group == "ref": continue
        g = cadlib.group_loc(part.group, p)
        base = [v for v in part.shape.vals() if isinstance(v, cq.Shape)]
        base = base[0] if len(base) == 1 else cq.Compound.makeCompound(base)
        for i, il in enumerate(part.instances): out.append((part.code, i, base.moved(g * il)))
    return out

def draw_assembly(parts, pose_name, path):
    ws = world_shapes(parts, pose_name)
    comp = cq.Compound.makeCompound([s for _, _, s in ws])
    prs = {k: project(comp, k, hidden=False, defl=0.2) for k in ("front", "top", "left", "iso")}
    sh = Sheet(); frame(sh)
    x0, y0, z0, x1, y1, z1 = bbox(comp)
    sc = draw_views(sh, prs, scale_choice=(1, 10), hidden=False, dims=dict(width=x1 - x0, height=z1 - z0, depth=y1 - y0), iso_grow=4.0)
    pose = cadlib.POSES[pose_name]
    rows = [("零件名称", f"总装（{ {'flush': '齐平位', 'mid': '中间位', 'top': '顶位'}.get(pose_name, pose_name)}，丝杠行程 {pose['stroke']:.0f}）"), ("编号", "ASM"),
            ("材料", "见零件表"), ("数量", "1"), ("比例", sc), ("单位", "mm"), ("投影", ""), ("项目", PROJECT)]
    top = title_block(sh, rows, NOTE + "。坐标：x 离床、y 指向床头、z 向上，原点在床长边正下方地面")
    seen = {}
    for part in parts:
        if part.group == "ref": continue
        if part.code not in seen: seen[part.code] = [part.name, 0]
        seen[part.code][1] += part.qty
    items = [(c, f"{n} ×{q}") for c, (n, q) in seen.items()]
    avail = top - 3 - 18; per = 3.9; fs = 2.4
    n_fit = max(1, int(avail // per))
    cols = [items[i:i + n_fit] for i in range(0, len(items), n_fit)]
    w_all = SHEET_W - 5 - COL_X; cw = w_all / max(1, len(cols))
    sh.text(COL_X, 15.5, "零件表", 3.4, weight="bold")
    for ci, col in enumerate(cols[:3]):
        x = COL_X + ci * cw; y = 18
        sh.line(x, y, x + cw - 1, y, 0.3)
        for c, t in col:
            sh.text(x + 1, y + 3.0, c, fs, weight="bold")
            for k, tt in enumerate(wrap(t, cw - 11, fs)[:1]): sh.text(x + 9.5, y + 3.0, tt, fs)
            y += per; sh.line(x, y, x + cw - 1, y, 0.1)
    open(path, "w", encoding="utf-8").write(sh.svg(f"总装 {pose_name}"))
    return sc
