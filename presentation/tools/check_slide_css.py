"""Flag inline-CSS the Slides runtime does not support (subset from the type's format.md).
Usage: python3 check_slide_css.py <slides_dir> [ids...]"""
import re, sys, os, glob
OK = set("""position left top right bottom width height min-width min-height max-width max-height display flex-direction flex-wrap gap
align-items justify-content justify-items align-self justify-self flex flex-grow flex-shrink flex-basis grid-template-columns grid-template-rows
grid-column grid-row aspect-ratio padding overflow font-family font-size font-weight font-style font line-height letter-spacing text-align
text-transform white-space text-decoration font-variant-numeric -webkit-text-stroke color background background-clip -webkit-text-fill-color
border border-top border-right border-bottom border-left border-radius box-shadow text-shadow opacity transform filter backdrop-filter
mix-blend-mode object-fit margin box-sizing grid-template""".split())
d = sys.argv[1]; ids = sys.argv[2:] or [os.path.basename(f)[:-5] for f in sorted(glob.glob(d + "/*.html"))]
bad = 0
for sid in ids:
    h = open(f"{d}/{sid}.html").read()
    for m in re.finditer(r'<(\w[\w-]*)[^>]*?style="([^"]*)"', h):
        tag, st = m.group(1), m.group(2)
        for decl in filter(None, (x.strip() for x in st.split(";"))):
            p, _, v = decl.partition(":"); p = p.strip().lower(); v = v.strip()
            msg = None
            if p not in OK: msg = "unsupported property"
            elif p in ("grid-column", "grid-row") and not re.fullmatch(r"span \d+", v): msg = "only 'span N'"
            elif re.search(r"\d(em|rem|vw|vh)\b", v) and p != "letter-spacing": msg = "unit"
            elif "var(" in v: msg = "var()"
            elif p == "justify-content" and "display:grid" in st.replace(" ", ""): msg = "justify-content on grid"
            elif p.startswith("margin") : continue
            if msg: bad += 1; print(f"{sid}: <{tag}> {decl}  -> {msg}")
print("issues:", bad)
