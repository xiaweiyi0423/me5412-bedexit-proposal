"""Merge the team's own PPTX pages into the image-based English deck (BedExitSeat_EN.pptx).

The base deck keeps our pages (cover, film, agenda, problem, existing solutions, product comparison, team,
conclusion, appendix). Pages that a teammate redesigned are dropped from the base and their own slides are copied
in at the same place, XML as is (shapes, morph transitions, timing, videos, charts, pictures), with every related
part copied and every relationship id remapped. Speaker notes are copied as text; a copied slide without notes
gets ours from presentation/slides_en/<id>.html (<aside>).

usage: merge_team_pptx.py BASE.pptx OUT.pptx --p2 6-8.pptx --p3 p9-12.pptx --p4 control.pptx --p5 summary.pptx
"""
import argparse, copy, re
from pathlib import Path
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from lxml import etree

REPO = Path(__file__).resolve().parents[2]
RNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# final order: ("base", slide id in the base deck) or (source key, 1-based slide number in that file)
ORDER = [("base", "cover"), ("base", "film"), ("base", "agenda"), ("base", "problem"), ("base", "prior"),
         ("p2", 1), ("p2", 2), ("p2", 3),
         *[("p3", i) for i in range(1, 11)],
         ("p4", 1), ("p4", 2), ("p4", 3),
         ("base", "compare"), ("p5", 2), ("p5", 3), ("base", "team"), ("base", "conclusion"),
         ("base", "appendix"), ("base", "concept"), ("base", "cantilever"), ("base", "speed"), ("base", "fall_exit"),
         ("base", "nextsteps"), ("base", "parts"), ("base", "drawings"), ("base", "sizing"), ("base", "verify")]
# notes for copied slides that have none: our slide whose content they carry
NOTES_FROM = {("p2", 1): "whynot", ("p5", 2): "advantages", ("p5", 3): "limits"}
# small wording fixes on copied slides: (source, slide) -> [(old run text, new run text)]
PATCH = {("p5", 2): [("Share of the move where the seat still holds you",
                      "Hips dropping straight down still land on the seat (falling backward: 73%)")]}


def our_notes(sid):
    h = (REPO / "presentation/slides_en" / f"{sid}.html").read_text()
    m = re.search(r"<aside>(.*?)</aside>", h, re.S)
    return m.group(1).strip() if m else ""


class Copier:
    def __init__(self, dest):
        self.dest, self.pkg, self.done = dest, dest.part.package, {}

    def new_partname(self, src_name):
        stem = re.sub(r"\d+(\.\w+)$", r"%d\1", str(src_name))
        if "%d" not in stem:
            stem = re.sub(r"(\.\w+)$", r"%d\1", stem)
        return self.pkg.next_partname(stem)

    def copy_rels(self, src_part, dst_part):
        """Copy every relationship of src_part onto dst_part; return {old rId: new rId}."""
        m = {}
        for rid, rel in list(src_part.rels.items()):
            if rel.reltype in (RT.SLIDE_LAYOUT, RT.NOTES_SLIDE):
                continue
            if rel.is_external:
                m[rid] = dst_part.relate_to(rel.target_ref, rel.reltype, is_external=True)
                continue
            tgt = rel.target_part
            key = (id(src_part.package), str(tgt.partname))
            fresh = key not in self.done
            if fresh:
                self.done[key] = Part(PackURI(self.new_partname(tgt.partname)), tgt.content_type, self.pkg, tgt.blob)
            newp = self.done[key]
            m[rid] = dst_part.relate_to(newp, rel.reltype)
            if fresh and len(tgt.rels):                       # e.g. a chart and its embedded workbook
                sub = self.copy_rels(tgt, newp)
                if tgt.content_type.endswith("xml"):
                    x = etree.fromstring(tgt.blob)
                    remap(x, sub)
                    newp._blob = etree.tostring(x, xml_declaration=True, encoding="UTF-8", standalone=True)
        return m

    def add_slide(self, src_slide):
        blank = self.dest.slide_layouts[6]
        s = self.dest.slides.add_slide(blank)
        el = copy.deepcopy(src_slide._element)
        remap(el, self.copy_rels(src_slide.part, s.part))
        s.part._element = el
        return s


def remap(el, m):
    for e in el.iter():
        for a, v in list(e.attrib.items()):
            if a.startswith("{%s}" % RNS) and v in m:
                e.set(a, m[v])


def notes_text(slide):
    if slide.has_notes_slide and slide.notes_slide.notes_text_frame is not None:
        return slide.notes_slide.notes_text_frame.text.strip()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"), ap.add_argument("out")
    for k in ("p2", "p3", "p4", "p5"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    dest = Presentation(a.base)
    meta = __import__("json").load(open(REPO / "presentation/deck.json"))["order"]
    base_ids = {sid: dest.slides._sldIdLst[i] for i, sid in enumerate(meta)}   # base deck = deck.json order
    srcs = {k: Presentation(getattr(a, k)) for k in ("p2", "p3", "p4", "p5")}
    cp = Copier(dest)
    new_ids = {}
    for key in ORDER:
        if key[0] == "base":
            continue
        src = srcs[key[0]].slides[key[1] - 1]
        for old, new in PATCH.get(key, []):
            hit = [r for sh in src.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs for r in p.runs if r.text.strip() == old]
            assert hit, (key, old)
            hit[0].text = new
        s = cp.add_slide(src)
        n = notes_text(src) or (our_notes(NOTES_FROM[key]) if key in NOTES_FROM else "")
        if n:
            s.notes_slide.notes_text_frame.text = n
        new_ids[key] = dest.slides._sldIdLst[-1]
    lst = dest.slides._sldIdLst
    keep = [base_ids[k[1]] if k[0] == "base" else new_ids[k] for k in ORDER]
    for sid_el in list(lst):                      # drop the base pages the team replaced
        if sid_el not in keep:
            dest.part.drop_rel(sid_el.rId)
            lst.remove(sid_el)
    for e in keep:                                # final order
        lst.remove(e); lst.append(e)
    dest.save(a.out)
    print("wrote", a.out, len(dest.slides), "slides")


if __name__ == "__main__":
    main()
