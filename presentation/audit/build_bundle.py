"""Extract slide text, speaker notes, talk-guide metadata and images into a bundle for the audit."""
import json, re, html, base64, io, sys, os
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = sys.argv[1]
P = ROOT + '/presentation'
deck = json.load(open(P + '/deck.json'))
order = deck['order']
# talk guide metadata (D dict) from build_guide2.py
src = open(P + '/tools/build_guide2.py').read()
dsrc = src.split('\nD = {', 1)[1].split('\n}\n', 1)[0]
D = eval('{' + dsrc + '\n}')
short = eval(re.search(r'SHORT = (\[.*?\])', src).group(1))
# thumbnails from talk guide
g = open(P + '/tools/talk_guide.html').read()
thumbs = {}
for m in re.finditer(r'<article class="srow" id="s-(\w+)".*?<img src="data:image/(\w+);base64,([^"]+)"', g, re.S):
    thumbs[m.group(1)] = (m.group(2), m.group(3))
def text_of(sec):
    sec = re.sub(r'<aside>.*?</aside>', '', sec, flags=re.S)
    sec = re.sub(r'<img [^>]*alt="([^"]*)"[^>]*>', r'\n[图: \1]\n', sec)
    sec = re.sub(r'<(br|/p|/h1|/h2|/h3|/li|/div|/tr)[^>]*>', '\n', sec)
    sec = re.sub(r'<[^>]+>', ' ', sec)
    lines = [re.sub(r'[ \t]+', ' ', html.unescape(l)).strip() for l in sec.split('\n')]
    return '\n'.join(l for l in lines if l)
secstart = {v['start']: v['description'] for v in deck['sections'].values()}
parts = []
for i, sid in enumerate(order, 1):
    h = open(f'{P}/slides/{sid}.html').read()
    aside = re.search(r'<aside>(.*?)</aside>', h, re.S)
    d = D[sid]
    if sid in secstart:
        parts.append(f'\n## 【章节】{secstart[sid]}\n')
    s = [f'### 第 {i} 页 · {d["t"]}  (id={sid}; 计划时长 {d["m"]} 分钟; 状态={d["st"]}; 时间紧版本{"保留" if sid in short else "删去"})',
         '**slide 上的文字：**', text_of(h),
         '**讲稿（slide 备注）：**', html.unescape(aside.group(1).strip()) if aside else '(无)',
         f'**讲稿指南·这一页要让听众记住：** {d["key"]}']
    if d['ask']:
        s.append('**讲稿指南·可能被问到：**\n' + '\n'.join(f'- 问：{q}\n  答：{a}' for q, a in d['ask']))
    if d['todo']:
        s.append('**讲稿指南·待补：**\n' + '\n'.join(f'- {w}（{who}，{need}）' for w, who, need in d['todo']))
    parts.append('\n'.join(s))
    if sid in thumbs:
        fmt, b = thumbs[sid]
        im = Image.open(io.BytesIO(base64.b64decode(b))); im.seek(0)
        im.convert('RGB').save(f'{OUT}/img/thumb_{i:02d}_{sid}.png')
open(OUT + '/slides.md', 'w').write('\n\n'.join(parts))
print(len('\n\n'.join(parts)), 'chars;', len(thumbs), 'thumbs')
