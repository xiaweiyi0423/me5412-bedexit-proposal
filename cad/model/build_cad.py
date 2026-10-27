"""Build every CAD output under cad/out/ from the part modules (parts_seat, parts_carriage, parts_fixed; each build() -> list[Part]).

  python3 build_cad.py                 all outputs
  python3 build_cad.py --dummy         three dummy parts (pipeline test)
  options: --only S7,C1   --no-draw   --no-step   --no-mesh   --no-interf   --poses flush,mid,top

Outputs: out/step/<code>.step, out/step/assembly_{flush,top}.step, out/drawings/<code>.svg (made parts), out/drawings/assembly_flush.svg,
out/mesh.json, out/manifest.json, out/interference.json (pairs whose solids overlap by > 5 mm3 in world, at each pose).
"""
import argparse, importlib, json, os, sys, time, traceback
import cadquery as cq
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cadlib, drawing, export

MODULES = ("parts_seat", "parts_carriage", "parts_fixed")

def dummy_parts():
    P = cadlib.Part
    tube = cadlib.rect_tube_y(-25, 25, -130, -100, -205, 204, 4)
    plate = cadlib.holes_y(cadlib.box(-40, 190, 288, 308, -175, 25), [(0, 0)] + [(a + du, b + dv) for a, b in ((0, 0), (150, 0), (0, -150), (150, -150)) for du in (-13, 13) for dv in (-13, 13)], 2.25)
    plate = plate.cut(cadlib.cyl_y(0, 0, 280, 320, 27.5))
    disc = cadlib.tube_y(0, 0, 229, 246, 27.5, 15)
    return [P("S7", "横梁（测试）", "S355 矩形管 50 × 30 × 4", "seat", tube, color=cadlib.COLORS["steel"], params=[("壁厚", "4"), ("长", "409")], note="测试件"),
            P("C1", "滑块板（测试）", "S355 20 mm", "carriage", plate, color=cadlib.COLORS["blue_light"], params=[("轴承孔", "Ø55 H7"), ("滑块孔", "4 × M4，26 × 26")]),
            P("J2", "圆锥滚子轴承（测试）", "SKF 32006 X/Q", "carriage", disc, instances=[cadlib.IDENT, cadlib.loc(0, 61, 0)], buy=True, drawing=False, color=cadlib.COLORS["buy"])]

def collect(use_dummy):
    if use_dummy: return dummy_parts(), []
    parts, missing = [], []
    for mod in MODULES:
        if not os.path.exists(os.path.join(HERE, mod + ".py")): missing.append(mod); continue
        try:
            m = importlib.import_module(mod); got = m.build(); parts += got; print(f"{mod}: {len(got)} parts ({', '.join(p.code for p in got)})")
        except Exception:
            print(f"!! {mod} failed:"); traceback.print_exc(); missing.append(mod)
    return parts, missing

def interference(parts, pose_name, thresh=5.0):
    ws = drawing.world_shapes(parts, pose_name)
    boxes = [s.BoundingBox() for _, _, s in ws]; hits = []
    for i in range(len(ws)):
        for j in range(i + 1, len(ws)):
            if ws[i][0] == ws[j][0]: continue
            a, b = boxes[i], boxes[j]
            if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin: continue
            try: v = ws[i][2].intersect(ws[j][2]).Volume()
            except Exception as e: v = -1.0
            if v > thresh or v < 0: hits.append(dict(a=f"{ws[i][0]}#{ws[i][1] + 1}", b=f"{ws[j][0]}#{ws[j][1] + 1}", vol_mm3=round(v, 1)))
    return sorted(hits, key=lambda h: -h["vol_mm3"])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dummy", action="store_true"); ap.add_argument("--only", default="")
    for f in ("draw", "step", "mesh", "interf"): ap.add_argument(f"--no-{f}", action="store_true")
    ap.add_argument("--poses", default="flush,mid,top"); ap.add_argument("--out", default=cadlib.OUT)
    a = ap.parse_args(); T0 = time.time()
    out = a.out; os.makedirs(os.path.join(out, "step"), exist_ok=True); os.makedirs(os.path.join(out, "drawings"), exist_ok=True)
    parts, missing = collect(a.dummy)
    if missing: print("missing / failed modules:", missing)
    codes = [p.code for p in parts]; dup = {c for c in codes if codes.count(c) > 1}
    if dup: print("!! duplicate codes:", dup)
    print("check:", cadlib.check(parts)); print(f"collect + check {time.time() - T0:.1f}s")
    sel = [p for p in parts if not a.only or p.code in a.only.split(",")]
    drawn = set()
    if not a.no_step:
        t = time.time()
        for p in sel: export.export_part_step(p, os.path.join(out, "step", f"{p.code}.step"))
        if not a.only:
            for pn in ("flush", "top"): export.export_assembly_step(parts, pn, os.path.join(out, "step", f"assembly_{pn}.step"))
        print(f"STEP {time.time() - t:.1f}s")
    if not a.no_draw:
        t = time.time()
        for p in sel:
            if p.drawing and not p.buy:
                t1 = time.time(); sc = drawing.draw_part(p, os.path.join(out, "drawings", f"{p.code}.svg")); drawn.add(p.code)
                print(f"  drawing {p.code} {sc} {time.time() - t1:.1f}s")
        if not a.only: drawing.draw_assembly(parts, "flush", os.path.join(out, "drawings", "assembly_flush.svg"))
        print(f"drawings {time.time() - t:.1f}s")
    else:
        drawn = {p.code for p in parts if p.drawing and not p.buy and os.path.exists(os.path.join(out, "drawings", f"{p.code}.svg"))}
    if not a.no_mesh and not a.only:
        t = time.time(); info = export.export_mesh(parts, os.path.join(out, "mesh.json")); print(f"mesh {info} {time.time() - t:.1f}s")
    if not a.only:
        export.write_manifest(parts, os.path.join(out, "manifest.json"), drawn=drawn | {p.code for p in parts if p.drawing and not p.buy and os.path.exists(os.path.join(out, "drawings", f"{p.code}.svg"))})
    if not a.no_interf and not a.only:
        t = time.time(); rep = {}
        for pn in a.poses.split(","): rep[pn] = interference(parts, pn); print(f"  interference {pn}: {len(rep[pn])} pairs")
        json.dump(rep, open(os.path.join(out, "interference.json"), "w"), ensure_ascii=False, indent=1); print(f"interference {time.time() - t:.1f}s")
    print(f"total {time.time() - T0:.1f}s")

if __name__ == "__main__":
    main()
