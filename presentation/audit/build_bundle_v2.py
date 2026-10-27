"""Bundle for the v2 audit (seat as main design): slide text and speaker notes from presentation/slides, talk-guide
metadata (key point, Q&A, to-dos, minutes, status) parsed from the published guide presentation/tools/talk_guide.html.
Usage: python3 build_bundle_v2.py <bundle_dir>   (then render_slides.js <bundle_dir> for img/full_*.png)
"""
import html, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); P = ROOT + '/presentation'
OUT = sys.argv[1]; os.makedirs(OUT + '/img', exist_ok=True)
deck = json.load(open(P + '/deck.json')); order = deck['order']
g = open(P + '/tools/talk_guide.html').read()
D = json.loads(re.search(r'const D=(\{.*?\});', g, re.S).group(1))
meta = {s['id']: s for s in D['slides']}
strip = lambda s: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()

def guide(sid):
    a = re.search(rf'<article class="srow" id="s-{sid}".*?</article>', g, re.S).group(0)
    key = re.search(r'<p class="keyl"><b>[^<]*</b>(.*?)</p>', a, re.S); st = re.search(r'<span class="pill [^"]*">(.*?)</span>', a)
    qa = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', a, re.S); todo = re.findall(r'<li><b>待补：</b>(.*?)</li>', a, re.S)
    return dict(key=strip(key.group(1)) if key else '', st=strip(st.group(1)) if st else '', qa=[(strip(q), strip(x)) for q, x in qa], todo=[strip(t) for t in todo])

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
    h = open(f'{P}/slides/{sid}.html').read(); aside = re.search(r'<aside>(.*?)</aside>', h, re.S); m = meta.get(sid, {}); d = guide(sid)
    if sid in secstart: parts.append(f'\n## 【章节】{secstart[sid]}\n')
    s = [f'### 第 {i} 页 · {m.get("t", sid)}  (id={sid}; 计划时长 {m.get("m", "?")} 分钟; 讲稿指南状态={d["st"]})',
         '**slide 上的文字：**', text_of(h), '**讲稿（slide 备注）：**', html.unescape(aside.group(1).strip()) if aside else '(无)',
         f'**讲稿指南·这一页要让听众记住：** {d["key"]}']
    if d['qa']: s.append('**讲稿指南·可能被问到：**\n' + '\n'.join(f'- 问：{q}\n  答：{a}' for q, a in d['qa']))
    if d['todo']: s.append('**讲稿指南·待补：**\n' + '\n'.join(f'- {t}' for t in d['todo']))
    parts.append('\n'.join(s))
open(OUT + '/slides.md', 'w').write('\n\n'.join(parts))
print(len('\n\n'.join(parts)), 'chars;', len(order), 'slides')
