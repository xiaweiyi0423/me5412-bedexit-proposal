#!/usr/bin/env python3
"""Put the videos back into a PPTX exported from the online deck.

The export keeps only the poster stills of the three <img data-video> slides.
Each still is found again by comparing every picture in the deck with the
reference stills, replaced by a movie at the same place (still = poster), and
given playback timing:
  film    : starts on click, with sound, plays once
  motion / sensing : start with the slide, loop, muted

usage: pptx_embed_videos.py IN.pptx OUT.pptx [--film F] [--motion F] [--sensing F]
"""
import argparse, copy, io, struct, sys
from pathlib import Path

from lxml import etree
from PIL import Image, ImageChops, ImageStat
from pptx import Presentation
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.shapes.picture import Picture

REPO = Path(__file__).resolve().parents[2]
A6 = REPO / "presentation/assets_v6"
# name -> (default video, reference still, fallback slide no., autoplay+loop+mute)
TARGETS = {
    "film": (REPO / "presentation/video/pulse/bedexit_pulse.mp4", A6 / "still_film.jpg", 2, False),
    "motion": (A6 / "clip_motion.mp4", A6 / "still_motion.jpg", 10, True),
    "sensing": (A6 / "clip_sensing.mp4", A6 / "still_sensing.jpg", 12, True),
}
NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def xp(el, path):  # works on python-pptx oxml and plain lxml elements alike
    return etree.XPath(path, namespaces=NS)(el)


# mean abs diff (0-255) of 64x36 thumbnails: the same frame re-encoded/resized scores ~1,
# the closest *other* picture in the deck (motion vs sensing still) ~12
MAX_DIFF = 4.0


def thumb(blob):
    return Image.open(io.BytesIO(blob)).convert("RGB").resize((64, 36), Image.BILINEAR)


def diff(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3


def mp4_duration_ms(data):
    """Duration from the mvhd box (PowerPoint writes it as the play command's dur)."""
    i = data.find(b"mvhd")
    if i < 0:
        return None
    if data[i + 4] == 1:  # version 1: 64-bit times
        scale, dur = struct.unpack(">IQ", data[i + 24:i + 36])
    else:
        scale, dur = struct.unpack(">II", data[i + 16:i + 24])
    return round(dur * 1000 / scale)


def find_targets(prs):
    pics = [(n, s, sh) for n, s in enumerate(prs.slides, 1) for sh in s.shapes if isinstance(sh, Picture)]
    thumbs = {id(sh): thumb(sh.image.blob) for _, _, sh in pics}
    found, used = {}, set()
    for name, (_, still, slide_no, _) in TARGETS.items():
        ref_bytes = still.read_bytes()
        ref = thumb(ref_bytes)
        scored = sorted((diff(thumbs[id(sh)], ref), n, s, sh) for n, s, sh in pics if id(sh) not in used)
        if scored and scored[0][0] <= MAX_DIFF:
            d, n, s, sh = scored[0]
            how = f"perceptual diff {d:.2f}"
        else:  # fallback: largest picture on the expected slide
            if slide_no > len(prs.slides):
                sys.exit(f"{name}: no matching picture and slide {slide_no} does not exist")
            s = prs.slides[slide_no - 1]
            cands = [sh for sh in s.shapes  # GIFs are the deck's animations, never a video poster
                     if isinstance(sh, Picture) and sh.image.ext != "gif" and id(sh) not in used]
            if not cands:
                sys.exit(f"{name}: no matching picture and no picture on slide {slide_no}")
            n, sh = slide_no, max(cands, key=lambda p: p.width * p.height)
            how = f"FALLBACK largest picture on slide {n} (best diff {scored[0][0]:.1f})" if scored else "FALLBACK"
        same = sh.image.blob == ref_bytes
        print(f"  {name:8s} -> slide {n:2d} '{sh.name}' {sh.image.size[0]}x{sh.image.size[1]} "
              f"[{how}; bytes {'identical' if same else 'differ'} to {still.name}]")
        used.add(id(sh))
        found[name] = (s, sh)
    return found


def timing_root(sld):
    """tmRoot childTnLst and its mainSeq childTnLst (created if missing; existing timing kept)."""
    root = sld.get_or_add_childTnLst()  # python-pptx: keeps an existing standard p:timing
    seqs = xp(root, "./p:seq/p:cTn[@nodeType='mainSeq']")
    if seqs:
        main = seqs[0].find(qn("p:childTnLst"))
    else:
        seq = parse_xml(
            f'<p:seq {nsdecls("p")} concurrent="1" nextAc="seek"><p:cTn id="0" dur="indefinite" nodeType="mainSeq">'
            '<p:childTnLst/></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond>'
            '</p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond>'
            "</p:nextCondLst></p:seq>")
        root.insert(0, seq)  # PowerPoint puts the main sequence first
        main = seq[0].find(qn("p:childTnLst"))
    return root, main


def number_new_nodes(sld):
    """New p:cTn nodes are created with id=0; give them fresh ids (existing ids are left alone,
    since p:tn/@val elsewhere in the timing tree may refer to them)."""
    ctns = xp(sld, "./p:timing//p:cTn")
    next_id = max(int(c.get("id")) for c in ctns) + 1
    for c in ctns:
        if c.get("id") == "0":
            c.set("id", str(next_id))
            next_id += 1
    main_id = xp(sld, "./p:timing//p:cTn[@nodeType='mainSeq']/@id")[0]
    for tn in xp(sld, "./p:timing//p:tn[@val='MAINSEQ']"):
        tn.set("val", main_id)


def add_playback(sld, spid, auto, dur_ms):
    root, main = timing_root(sld)
    dur = str(dur_ms) if dur_ms else "indefinite"
    # media node python-pptx just added: loop = repeatCount on its cTn, mute on cMediaNode
    node = xp(root, f"./p:video/p:cMediaNode[p:tgtEl/p:spTgt/@spid='{spid}']")[0]
    if auto:
        node.set("mute", "1")
        node.find(qn("p:cTn")).set("repeatCount", "indefinite")
    # mediacall effect "Play" (presetID 1) = cmd playFrom(0.0) on the movie shape
    effect = (
        f'<p:par {nsdecls("p")}><p:cTn id="0" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" '
        f'nodeType="{"afterEffect" if auto else "clickEffect"}"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
        f'<p:childTnLst><p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="0" dur="{dur}" fill="hold"/>'
        f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd></p:childTnLst></p:cTn></p:par>')
    # clicking the movie itself toggles pause (PowerPoint adds this interactive trigger too)
    root.append(parse_xml(
        f'<p:seq {nsdecls("p")} concurrent="1" nextAc="seek"><p:cTn id="0" restart="whenNotActive" fill="hold" '
        f'evtFilter="cancelBubble" nodeType="interactiveSeq"><p:stCondLst><p:cond evt="onClick" delay="0"><p:tgtEl>'
        f'<p:spTgt spid="{spid}"/></p:tgtEl></p:cond></p:stCondLst><p:endSync evt="end" delay="0"><p:rtn val="all"/>'
        '</p:endSync><p:childTnLst><p:par><p:cTn id="0" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
        '<p:childTnLst><p:par><p:cTn id="0" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
        '<p:par><p:cTn id="0" presetID="2" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="clickEffect">'
        '<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:cmd type="call" cmd="togglePause"><p:cBhvr>'
        f'<p:cTn id="0" dur="1" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd>'
        '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par></p:childTnLst>'
        '</p:cTn><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        '</p:seq>'))
    groups = main.findall(qn("p:par"))
    first_cond = xp(groups[0], "./p:cTn/p:stCondLst/p:cond[@evt='onBegin']") if groups else []
    if auto and first_cond:  # slide already has an auto-start group: join it ("with previous")
        inner = xp(groups[0], "./p:cTn/p:childTnLst/p:par")[0].find(qn("p:cTn")).find(qn("p:childTnLst"))
        e = parse_xml(effect)
        e[0].set("nodeType", "withEffect")
        inner.append(e)
        return
    # click group: delay=indefinite waits for a click; adding onBegin of the mainSeq (tn val = its
    # cTn id) makes the first group fire as soon as the slide starts ("after previous" in PowerPoint)
    begin = '<p:cond evt="onBegin" delay="0"><p:tn val="MAINSEQ"/></p:cond>' if auto else ""
    group = parse_xml(
        f'<p:par {nsdecls("p")}><p:cTn id="0" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>{begin}'
        '</p:stCondLst><p:childTnLst><p:par><p:cTn id="0" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
        f'<p:childTnLst/></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    xp(group, ".//p:childTnLst")[-1].append(parse_xml(effect))
    if auto:
        main.insert(0, group)
    else:
        main.append(group)


def replace_with_movie(slide, pic, video, auto):
    data = video.read_bytes()
    mov = slide.shapes.add_movie(io.BytesIO(data), pic.left, pic.top, pic.width, pic.height,
                                 poster_frame_image=io.BytesIO(pic.image.blob), mime_type="video/mp4")
    old, new = pic._element, mov._element
    new.nvPicPr.cNvPr.set("name", f"Video {video.stem}")
    if old.nvPicPr.cNvPr.get("descr"):
        new.nvPicPr.cNvPr.set("descr", old.nvPicPr.cNvPr.get("descr"))
    # keep the picture's crop (applies to poster and video) and its rounded-corner geometry
    src = old.blipFill.find(qn("a:srcRect"))
    if src is not None:
        new.blipFill.find(qn("a:blip")).addnext(copy.deepcopy(src))
    geom = old.spPr.find(qn("a:prstGeom"))
    if geom is not None:
        new.spPr.replace(new.spPr.find(qn("a:prstGeom")), copy.deepcopy(geom))
    old.addprevious(new)  # same z-order slot as the picture (add_movie appended it on top)
    old.getparent().remove(old)
    add_playback(slide._element, mov.shape_id, auto, mp4_duration_ms(data))
    number_new_nodes(slide._element)
    return mov


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp"), ap.add_argument("out")
    for name, (video, *_) in TARGETS.items():
        ap.add_argument(f"--{name}", type=Path, default=video, help=f"video file (default {video.relative_to(REPO)})")
    args = ap.parse_args()
    prs = Presentation(args.inp)
    print(f"matching stills in {args.inp}:")
    for name, (slide, pic) in find_targets(prs).items():
        video, auto = getattr(args, name), TARGETS[name][3]
        mov = replace_with_movie(slide, pic, video, auto)
        print(f"  {name:8s}    embedded {video.name} ({video.stat().st_size / 1e6:.1f} MB) as shape id {mov.shape_id}, "
              + ("autoplay, loop, muted" if auto else "on click, sound, once"))
    prs.save(args.out)
    print(f"wrote {args.out} ({Path(args.out).stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
