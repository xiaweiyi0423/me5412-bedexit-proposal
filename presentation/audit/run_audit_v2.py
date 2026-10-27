"""v2 audit of the deck and talk guide after the seat became the main design (v5.3).
Usage: python3 run_audit_v2.py <bundle_dir> [angle ...]   bundle from build_bundle_v2.py + render_slides.js
Reuses run_audit.call/COMMON; context from context_v2.md; output in audit/v2/."""
import os, sys
from concurrent.futures import ThreadPoolExecutor
import json
import run_audit as RA
HERE = os.path.dirname(os.path.abspath(__file__)); OUTD = os.path.join(HERE, 'v2'); os.makedirs(OUTD, exist_ok=True)
RA.ANGLES['A_argument'] = ("你的角度：核心论证是否站得住。你是懂坐→站生物力学和简化建模的审稿人。方案现在的存在理由是："
    "座板跟着大腿走（曲线），竖直升降会让人往前滑、坐回落空；同口径下比低床省约 32%，但比抬高床只省 5–10%，价值主要在平时坐得低、全程有托。"
    "看看从问题、证据、模型到结论这条推理链哪里牢靠、哪里说过了头、哪里有被忽略的反例或代价，特别是省力不多这一点会不会动摇整个方案。")
RA.ANGLES['D_grading'] += " 注意：方案在 10/27 后从竖直升降改成了曲线坐板，看看改动后整套材料是否前后一致。"

def build_parts():
    ctx = open(os.path.join(HERE, 'context_v2.md')).read(); slides = open(os.path.join(RA.BUNDLE, 'slides.md')).read()
    parts = [{'text': ctx + '\n\n# 21 页 slides、讲稿和讲稿指南\n' + slides + '\n\n# 附件：每页截图（配图已渲染在内）\n'}]
    imgdir = os.path.join(RA.BUNDLE, 'img')
    for f in sorted(os.listdir(imgdir)):
        if not f.startswith('full_'): continue
        n, sid = f[5:7], f[8:-4]
        parts.append({'text': f'第 {int(n)} 页（{sid}）截图：'}); parts.append(RA.img_part(os.path.join(imgdir, f), (1600, 900)))
    return parts

if __name__ == '__main__':
    RA.COMMON = RA.COMMON.replace('部分配图在截图里是灰色占位块，这些页另附了真实缩略图。', '截图里已包含实际配图。')
    angles = sys.argv[2:] or list(RA.ANGLES); parts = build_parts()
    with ThreadPoolExecutor(min(3, len(angles))) as ex:
        for angle, fin, usage, text in ex.map(lambda a: RA.call(a, parts), angles):
            print(angle, fin, usage.get('promptTokenCount'), usage.get('candidatesTokenCount'), flush=True)
            with open(os.path.join(OUTD, f'gemini_{angle}.md'), 'w') as f:
                f.write(f'<!-- model: {RA.MODEL}; finishReason: {fin}; usage: {json.dumps(usage)} -->\n\n{text}\n')
