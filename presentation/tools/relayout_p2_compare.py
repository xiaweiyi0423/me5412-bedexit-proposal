"""Re-lay out slide 1 of teammate 2's file (the comparison page) in the style of his slides 2-3: Georgia title,
Aptos body, 55 pt margin. Same content; fixes: legend lines overlapping, figures cropped at the head (uses the full
figures from presentation/assets_v7/whynot_*.png), highlight frame only on two sides, empty band above the table.
Slides 2-3 are left as they are.
usage: relayout_p2_compare.py IN.pptx OUT.pptx
"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

REPO = Path(__file__).resolve().parents[2]
INK, MUTED, ACC, ACC2, GOOD, BAD = "18232D", "545D68", "A75F15", "B16D19", "25784F", "C64C38"
BG, CARD, LINE, OURS = "F7F5F0", "FFFFFF", "E2DDD6", "FBF1E4"


def rgb(h): return RGBColor.from_string(h)


def box(s, x, y, w, h, fill=None, line=None, lw=0.75, shape=MSO_SHAPE.RECTANGLE, radius=None):
    b = s.shapes.add_shape(shape, Pt(x), Pt(y), Pt(w), Pt(h))
    if fill: b.fill.solid(); b.fill.fore_color.rgb = rgb(fill)
    else: b.fill.background()
    if line: b.line.color.rgb = rgb(line); b.line.width = Pt(lw)
    else: b.line.fill.background()
    if radius is not None: b.adjustments[0] = radius
    b.shadow.inherit = False
    return b


def text(s, x, y, w, h, runs, size=12, color=INK, bold=False, font="Aptos", align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=None):
    """runs: str, or list of paragraphs; a paragraph is a str or a list of (text, {size,color,bold}) pieces."""
    t = s.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h)); tf = t.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"): setattr(tf, side, 0)
    paras = [runs] if isinstance(runs, str) else runs
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing: p.space_after = Pt(spacing)
        for piece, kw in ([(para, {})] if isinstance(para, str) else para):
            r = p.add_run(); r.text = piece; f = r.font
            f.name = kw.get("font", font); f.size = Pt(kw.get("size", size)); f.bold = kw.get("bold", bold)
            f.color.rgb = rgb(kw.get("color", color))
    return t


def build(s):
    sp = s.shapes._spTree
    for sh in list(s.shapes): sp.remove(sh._element)
    box(s, 0, 0, 960, 540, fill=BG)
    text(s, 55, 40, 600, 16, "2 · COMPARISON", size=12.2, color=ACC)
    text(s, 55, 64, 850, 34, "Same effort as a raised bed, better support if legs give way", size=23, bold=True, font="Georgia")
    # grid: a label column + four option columns
    LX, LW, CX, CW, G = 55, 122, 187, 172, 8
    cols = [CX + i * (CW + G) for i in range(4)]
    top, img_h, lab_y, row1, row2, bottom = 116, 160, 282, 330, 376, 420
    box(s, cols[3] - 4, top - 6, CW + 8, bottom - top + 6, fill=OURS, line=ACC2, lw=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
    figs = ["whynot_lowbed", "whynot_highbed", "whynot_vertical", "whynot_ours"]
    names = [("Low bed", "0.42 m + L-bar"), ("Raised bed", "0.58 m + bar"), ("Vertical-lift seat", "lifts straight up"), ("Bed-Exit Seat", "curved path")]
    for i, (x, f, (n, sub)) in enumerate(zip(cols, figs, names)):
        box(s, x + 4, top, CW - 8, img_h, fill=CARD, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
        iw = CW - 16; ih = min(img_h - 8, iw * 600 / 660); iw = ih * 660 / 600     # fit inside the card
        s.shapes.add_picture(str(REPO / "presentation/assets_v7" / f"{f}.png"), Pt(x + (CW - iw) / 2), Pt(top + (img_h - ih) / 2), Pt(iw), Pt(ih))
        ours = i == 3
        text(s, x, lab_y, CW, 36, [[(n, {"bold": True, "size": 14, "color": ACC2 if ours else INK})], [(sub, {"size": 11, "color": ACC2 if ours else MUTED})]], align=PP_ALIGN.CENTER)
    # legend in the label column, beside the figures
    text(s, LX, top + 6, LW - 6, 130, [[("If the legs give way:", {"bold": True, "size": 12.5})],
                                       [("● ", {"color": GOOD, "size": 12.5}), ("hips land on a support", {"size": 11.5, "color": MUTED})],
                                       [("✕ ", {"color": BAD, "size": 12.5, "bold": True}), ("misses it; number = distance past the edge", {"size": 11.5, "color": MUTED})],
                                       [("(one moment, ~70% of the rise)", {"size": 10.5, "color": MUTED})]], spacing=5)
    # results table
    for y in (row1 - 4, row2 - 4, bottom):
        box(s, LX, y, cols[3] + CW - LX, 0.75, fill=LINE)
    text(s, LX, row1, LW, 40, [[("Effort ÷ body weight", {"size": 11.5})], [("lower = easier", {"size": 10, "color": MUTED})]], color=MUTED)
    text(s, LX, row2, LW, 40, [[("Legs give way:", {"size": 11.5})], [("share of rise caught", {"size": 10, "color": MUTED})]], color=MUTED)
    vals1 = [("0.40", INK), ("0.29", INK), ("—*", MUTED), ("0.26", INK)]
    vals2 = [("14%", INK), ("15%", INK), ("43%", INK), ("100%", GOOD)]
    for x, (v1, c1), (v2, c2), ours in zip(cols, vals1, vals2, (0, 0, 0, 1)):
        text(s, x, row1, CW, 36, v1, size=20, bold=True, color=c1, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x, row2, CW, 36, v2, size=20, bold=True, color=c2, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    # takeaway + source
    box(s, LX, 434, cols[3] + CW - LX, 42, fill="FCF9F5", line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.18)
    text(s, LX + 14, 434, cols[3] + CW - LX - 28, 42, [[("Takeaway: ", {"bold": True, "size": 14}),
                                                      ("about the same effort as a raised bed, but the seat stays under the hips for the whole rise.", {"size": 14})]],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, LX, 488, 850, 30, "2D quasi-static model, median of 81 simulated user configurations.  * Vertical lift not rated for effort: most users slide forward off the seat (next slide: 11/81 pass).",
         size=10.5, color=MUTED)


if __name__ == "__main__":
    p = Presentation(sys.argv[1]); build(p.slides[0]); p.save(sys.argv[2]); print("wrote", sys.argv[2])
