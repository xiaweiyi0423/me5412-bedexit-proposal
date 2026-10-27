"""v3 audit of the deck and talk guide after v5.4-5.5 (fall catch, seat controller, 3D mechanism, return height).
Usage: python3 run_audit_v3.py <bundle_dir> [angle ...]   bundle from build_bundle_v2.py + render_slides.js
Reuses run_audit.call/COMMON; context from context_v3.md; output in audit/v3/."""
import os, sys
from concurrent.futures import ThreadPoolExecutor
import json
import run_audit as RA
HERE = os.path.dirname(os.path.abspath(__file__)); OUTD = os.path.join(HERE, 'v3'); os.makedirs(OUTD, exist_ok=True)
RA.ANGLES['A_argument'] = ("你的角度：核心论证是否站得住。你是懂坐→站生物力学和简化建模的审稿人。方案现在的存在理由是："
    "省力和抬高床相当（比低床省 32%，比抬高床只省 5–10%），主要价值是起身中腿一软往回坐时，曲线坐板全程接得住（81/81），床只在起身前约 15% 接得住。"
    "看看从问题、证据、模型到结论这条推理链哪里牢靠、哪里说过了头、哪里有被忽略的反例或代价，特别是“接得住”的定义和摔法假设是否撑得起这个主张。")
RA.ANGLES['D_grading'] += " 注意：方案在 10/27 后从竖直升降改成了曲线坐板，看看改动后整套材料是否前后一致，以及上一轮审计后的修改是否都落实到了 slides 和讲稿。"

def build_parts():
    ctx = open(os.path.join(HERE, 'context_v3.md')).read(); slides = open(os.path.join(RA.BUNDLE, 'slides.md')).read()
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
