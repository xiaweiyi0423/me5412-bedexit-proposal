"""STEP / mesh / manifest export for the bed-exit seat CAD model.

export_part_step(part, path)                 one instance, part-local frame
export_assembly_step(parts, pose_name, path) every instance in WORLD at a pose (names "S7", "C2_3"; colours), bed included
export_mesh(parts, path)                     web mesh JSON: per part, instances merged, GROUP frame (instance loc applied, not group_loc)
write_manifest(parts, path)                  part list + file paths + poses for the page
"""
import array, base64, json, os
import cadquery as cq
import cadlib

def _one(shape):
    vals = [v for v in shape.vals() if isinstance(v, cq.Shape)]
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)

def _color(hexstr):
    h = hexstr.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)); return cq.Color(r, g, b, 1.0)

def export_part_step(part, path):
    cq.exporters.export(part.shape, path)

def export_assembly_step(parts, pose_name, path):
    p = cadlib.POSES[pose_name]; assy = cq.Assembly(name=f"bedexit_{pose_name}")
    for part in parts:
        g = cadlib.group_loc(part.group, p); base = _one(part.shape)
        for i, il in enumerate(part.instances):
            nm = part.code if part.qty == 1 else f"{part.code}_{i + 1}"
            assy.add(base, name=nm, loc=g * il, color=_color(part.color))
    assy.export(path, "STEP")

def _b64(typecode, seq):
    a = array.array(typecode, seq)
    if a.itemsize != 4: raise ValueError("need 4-byte items")
    return base64.b64encode(a.tobytes()).decode("ascii")

def tessellate(part, tol=0.4, ang=0.35):
    base = _one(part.shape); pos, idx = [], []
    for il in part.instances:
        v, t = base.moved(il).tessellate(tol, ang); o = len(pos) // 3
        for q in v: pos += [q.x, q.y, q.z]
        for a, b, c in t: idx += [a + o, b + o, c + o]
    return pos, idx

def export_mesh(parts, path, tol=0.4, ang=0.35):
    out = []; ntri = 0
    for part in parts:
        pos, idx = tessellate(part, tol, ang); ntri += len(idx) // 3
        out.append(dict(code=part.code, name=part.name, group=part.group, color=part.color, buy=part.buy, pos=_b64("f", pos), idx=_b64("I", idx)))
    data = dict(parts=out, frames=dict(rail_rot_deg=cadlib.RAIL_ROT, B=list(cadlib.B), link_y=0), units="mm")
    with open(path, "w") as f: json.dump(data, f, separators=(",", ":"))
    return dict(bytes=os.path.getsize(path), triangles=ntri)

def write_manifest(parts, path, drawn=None):
    """drawn: set of codes that got a drawing (default: parts with drawing=True and not buy)."""
    rows = []
    for part in parts:
        has_dr = (part.code in drawn) if drawn is not None else (part.drawing and not part.buy)
        rows.append(dict(code=part.code, name=part.name, material=part.material, group=part.group, qty=part.qty, buy=part.buy, color=part.color,
                         note=part.note, params=[[str(a), str(b)] for a, b in (part.params or [])], step=f"step/{part.code}.step",
                         drawing=f"drawings/{part.code}.svg" if has_dr else None))
    data = dict(version="v5.7", parts=rows,
                assembly=dict(step=dict(flush="step/assembly_flush.step", top="step/assembly_top.step"), drawing=dict(flush="drawings/assembly_flush.svg")),
                poses={k: dict(stroke=v["stroke"], Q=list(v["Q"]), phi=v["phi"], P1=list(v["P1"]), P2=list(v["P2"])) for k, v in cadlib.POSES.items()},
                frames=dict(rail_rot_deg=cadlib.RAIL_ROT, B=list(cadlib.B), E=list(cadlib.E), NF=list(cadlib.NF)))
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1)
