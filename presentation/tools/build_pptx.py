"""Image-based PPTX of the English deck: one full-slide render per slide, speaker notes, video posters as their own
pictures (then pptx_embed_videos.py turns those into movies). Usage: python3 build_pptx.py <render_dir> <out.pptx>"""
import json, sys
from pptx import Presentation
from pptx.util import Emu
rd, out = sys.argv[1:3]
meta = json.load(open(f"{rd}/meta.json")); R = __file__.rsplit("/presentation/", 1)[0]
prs = Presentation(); prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
px = 12192000 / 1920
for m in meta:
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.shapes.add_picture(f"{rd}/{m['id']}.png", 0, 0, prs.slide_width, prs.slide_height).name = f"slide {m['id']}"
    for v in m["videos"]:
        s.shapes.add_picture(f"{R}/{v['poster']}", Emu(int(v["x"] * px)), Emu(int(v["y"] * px)), Emu(int(v["w"] * px)), Emu(int(v["h"] * px))).name = "video poster"
    s.notes_slide.notes_text_frame.text = m["notes"]
prs.save(out); print("wrote", out, len(meta), "slides")
