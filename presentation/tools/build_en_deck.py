"""Assemble the English deck from presentation/slides_en/ (which still carries the Chinese deck's /_blob/ ids).

Step 1  python3 build_en_deck.py plan
        For every /_blob/<id> (img src and data-video) in slides_en, find the local Chinese file and its English
        variant (<stem>_en.* in assets_en/ or next to the original). Writes .work/en_build/plan.json and prints the
        files with no English variant (fine for pictures without text).
Step 2  (lead) upload plan["upload"] to the English deck; save {local path: new blob url} as .work/en_build/uploaded.json
Step 3  python3 build_en_deck.py build
        Writes .work/en_build/project/deck.json and project/slides/<id>.html with the new blob urls.
"""
import json, os, re, sys, glob
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); P = R + "/presentation"
OUT = R + "/.work/en_build"
ALT = {"cad_3d_shell": "assets_v57/3d_a_shell.png", "cad_3d_open": "assets_v57/3d_b_open.png", "cad_poses": "assets_v57/3d_poses_strip.png",
       "cad_joint": "assets_v57/3d_d_joint.png", "fig_section": "assets_v57/fig_section.png", "fig_side": "assets_v57/fig_side.png",
       "fig_top": "assets_v57/fig_top.png", "md_target": "assets_v57/md_target.png", "md_candidates": "assets_v57/md_candidates.png",
       "md_synthesis": "assets_v57/md_synthesis.png", "dw_assembly": "assets_v57/dw_assembly_flush.png", "dw_C1": "assets_v57/dw_C1.png",
       "dw_J3": "assets_v57/dw_J3.png", "dw_S7": "assets_v57/dw_S7.png", "dw_J1": "assets_v57/dw_J1.png", "fea_c1": "assets_v57/fig_fea_c1.png",
       "fea_beam": "assets_v57/fig_fea_beam.png", "fea_house": "assets_v57/fig_fea_house.png", "fea_rail": "assets_v57/fig_fea_rail.png",
       "still_film": "assets_v6/still_film.jpg", "still_motion": "assets_v6/still_motion.jpg", "still_sensing": "assets_v6/still_sensing.jpg",
       "video_film": "video/pulse/bedexit_pulse.mp4", "video_clip_motion": "assets_v6/clip_motion.mp4", "video_clip_sensing": "assets_v6/clip_sensing.mp4"}


def zh_local(name):
    if name in ALT: return P + "/" + ALT[name]
    if name.startswith("v7_"): return P + "/assets_v7/" + name[3:] + ".png"
    for f in (P + "/assets_v6/icons/" + name + ".svg", P + "/animations/" + name + ".png", P + "/animations/" + name + ".gif"):
        if os.path.exists(f): return f


OVR = P + "/slides_en/en_overrides.json"  # {default English file: slide-specific replacement}, repo-relative


def en_variant(zh):
    d, base = os.path.split(zh); stem, ext = os.path.splitext(base)
    for f in [f"{P}/assets_en/{stem}_en{e}" for e in (ext, ".png", ".jpg", ".gif", ".mp4")] + [f"{d}/{stem}_en{ext}"]:
        if os.path.exists(f): return f


def order():
    o = json.load(open(P + "/deck.json"))["order"]
    return [s for s in o if os.path.exists(f"{P}/slides_en/{s}.html")], [s for s in o if not os.path.exists(f"{P}/slides_en/{s}.html")]


def plan():
    bj = json.load(open(P + "/animations/blobs.json")); by_id = {u.split("/")[-1]: n for n, u in bj.items()}
    ids, missing_slides = order(); m, no_en, unknown = {}, [], []
    for sid in ids:
        h = open(f"{P}/slides_en/{sid}.html").read()
        for bid in re.findall(r'(?:src|data-video)="/_blob/([0-9a-f]{32})"', h):
            if bid in m: continue
            n = by_id.get(bid); zh = zh_local(n) if n else None
            if not zh or not os.path.exists(zh): unknown.append((sid, bid, n)); continue
            en = en_variant(zh); rel = os.path.relpath(en or zh, R)
            ov = json.load(open(OVR)) if os.path.exists(OVR) else {}
            m[bid] = ov.get(rel, rel)
            if not en: no_en.append((sid, n, os.path.relpath(zh, R)))
    os.makedirs(OUT, exist_ok=True)
    json.dump({"map": m, "upload": sorted(set(m.values()))}, open(OUT + "/plan.json", "w"), indent=1)
    print("slides:", len(ids), "missing EN slides:", missing_slides)
    print("blobs:", len(m), "files to upload:", len(set(m.values())))
    print("no English variant (check these have no text):"); [print("  ", *x) for x in no_en]
    if unknown: print("UNKNOWN blob ids:"); [print("  ", *x) for x in unknown]


def build():
    pl = json.load(open(OUT + "/plan.json")); up = json.load(open(OUT + "/uploaded.json"))
    ids, _ = order(); os.makedirs(OUT + "/project/slides", exist_ok=True)
    for sid in ids:
        h = open(f"{P}/slides_en/{sid}.html").read()
        h = re.sub(r'/_blob/([0-9a-f]{32})', lambda mm: up[pl["map"][mm.group(1)]], h)
        open(f"{OUT}/project/slides/{sid}.html", "w").write(h)
    zh = json.load(open(P + "/deck.json"))
    deck = {"v": 4, "createdOnFiles": {"v": 1, "at": "2026-11-01T06:00:00Z"}, "lists": "css", "title": "Bed-Exit Seat", "order": ids,
            "sections": {"s0": {"description": "Cover, 46 s film and agenda", "start": "cover"},
                         "s1": {"description": "The problem and who it is for", "start": "problem"},
                         "s2": {"description": "Existing solutions and how ways of rising compare", "start": "prior"},
                         "s3": {"description": "Mechanism design, motion and stability", "start": "mech_path"},
                         "s4": {"description": "Sensing, control and safety", "start": "sensing"},
                         "s5": {"description": "Results, limits, conclusion and team", "start": "verify"},
                         "s6": {"description": "Appendix for Q&A", "start": "appendix"}},
            "faces": {"inter": {"family": "Inter", "href": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"},
                      "source-serif-4": {"family": "Source Serif 4", "href": "https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&display=swap"}},
            "designSystems": []}
    json.dump(deck, open(OUT + "/project/deck.json", "w"), ensure_ascii=False)
    print("built", len(ids), "slides into", OUT + "/project")


if __name__ == "__main__":
    {"plan": plan, "build": build}[sys.argv[1]]()
