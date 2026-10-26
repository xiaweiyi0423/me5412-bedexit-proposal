"""Run the six-angle audit of the slides and talk guide with Gemini 4 (gemini-4-argon).

Usage: python3 run_audit.py <bundle_dir> [angle ...]
<bundle_dir> is made by build_bundle.py + render_slides.js (slides.md, img/full_*.png, img/thumb_*.png).
The API key is injected by the session proxy, so no key is needed here.
"""
import base64, io, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

MODEL = 'gemini-4-argon'
URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'
HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = sys.argv[1]
# slides whose pictures are uploaded images: the full-size render only has a placeholder, so send the thumbnail too
PHOTO_SLIDES = {'cover', 'concept', 'mechanism', 'motion', 'risk', 'sensing', 'team'}

COMMON = """你在审计一个大学课程小组项目的汇报材料：21 页中文 slides（每页文字和讲稿备注）和一份讲稿指南（每页要点、预备问答、待补清单）。附件是每页截图；部分配图在截图里是灰色占位块，这些页另附了真实缩略图。

请从下面给你的角度出发，自由地找出这份材料真正的问题和薄弱处——会让汇报失分、被问住、或误导听众的地方。不必面面俱到，也不必凑数；你认为最重要的东西优先讲。
每个问题请说清：在哪里（页码或讲稿），原文证据，为什么是问题（讲因果，区分确定的事实和推测），以及怎么改。按重要性排序，并标出严重度（高/中/低）。最后用几句话给出总体判断和最值得先做的一件事。用中文回答，少用术语堆砌。
"""

ANGLES = {
 'A_argument': "你的角度：核心论证是否站得住。你是懂坐→站生物力学和简化建模的审稿人。整套方案的存在理由是“起身时座高决定省力，起身台升到 0.66 m 比抬高床再省 13–20%”。看看从问题、证据、模型到结论这条推理链哪里牢靠、哪里说过了头、哪里有被忽略的反例或代价。",
 'B_safety': "你的角度：安全与故障逻辑。你是医疗设备 / 个人护理机器人的安全评审员；老师强调用户界面和操作安全很关键。看看控制规则、状态机、传感、稳定性和风险分析在异常和意外情况下是否站得住，有没有漏掉的严重风险。",
 'C_real_use': "你的角度：真实使用场景。你是给居家老人做转移评估的作业治疗师，见过很多老人夜里起床的真实情况。看看这个设备从夜里醒来到站稳迈步、再到回床的整个过程，对目标用户是否现实，哪些环节没被想到。",
 'D_grading': "你的角度：评分人。你是这门课的老师，手边有自己 10/26 给小组的邮件要点和 11/3 的交付要求（见课程背景）。看看这份材料对你的要求回应得怎么样，离一份好的终稿还差什么，哪些缺口会直接扣分，你最想问小组什么。",
 'E_delivery': "你的角度：现场听众和版面。你是第一次听这个汇报的工科研究生同学，也懂一点 slides 设计。看看每页能不能很快看懂、讲稿好不好讲、前后是否连贯、时长是否现实、版面和字号在投影上是否可读。",
 'F_qa': "你的角度：答辩时最刁钻、最懂行的提问者。找出最可能把小组问住的问题（优先找讲稿指南里没准备的），并评估讲稿指南里已经准备的回答站不站得住，给出更好的回答或需要补的材料。",
}

def img_part(path, size=None):
    im = Image.open(path).convert('RGB')
    if size: im = im.resize(size)
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=85)
    return {'inline_data': {'mime_type': 'image/jpeg', 'data': base64.b64encode(buf.getvalue()).decode()}}

def build_parts():
    ctx = open(os.path.join(HERE, 'context.md')).read()
    slides = open(os.path.join(BUNDLE, 'slides.md')).read()
    parts = [{'text': ctx + '\n\n# 21 页 slides、讲稿和讲稿指南\n' + slides + '\n\n# 附件：每页截图\n'}]
    imgdir = os.path.join(BUNDLE, 'img')
    for f in sorted(os.listdir(imgdir)):
        if not f.startswith('full_'): continue
        n, sid = f[5:7], f[8:-4]
        parts.append({'text': f'第 {int(n)} 页（{sid}）渲染截图：'}); parts.append(img_part(os.path.join(imgdir, f), (1600, 900)))
        if sid in PHOTO_SLIDES:
            parts.append({'text': f'第 {int(n)} 页（{sid}）真实缩略图（含实际配图）：'}); parts.append(img_part(os.path.join(imgdir, f'thumb_{n}_{sid}.png')))
    return parts

def call(angle, parts):
    # streamed (SSE) so a long generation keeps the connection alive through the proxy
    body = {'system_instruction': {'parts': [{'text': COMMON + '\n' + ANGLES[angle]}]},
            'contents': [{'role': 'user', 'parts': parts + [{'text': '请从你的角度审计这份材料。'}]}],
            'generationConfig': {'maxOutputTokens': 32768}}
    data = json.dumps(body).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(URL.replace(':generateContent', ':streamGenerateContent') + '?alt=sse',
                                         data=data, headers={'Content-Type': 'application/json'})
            text, fin, usage = [], None, {}
            with urllib.request.urlopen(req, timeout=1800) as resp:
                for line in resp:
                    line = line.decode().strip()
                    if not line.startswith('data:'): continue
                    r = json.loads(line[5:])
                    for c in r.get('candidates', []):
                        text += [p.get('text', '') for p in c.get('content', {}).get('parts', []) if not p.get('thought')]
                        fin = c.get('finishReason') or fin
                    usage = r.get('usageMetadata', usage)
            if fin == 'STOP' and text:
                return angle, fin, usage, ''.join(text)
            print(angle, 'attempt', attempt, 'incomplete:', fin, flush=True)
        except Exception as e:
            err = e.read().decode()[:500] if hasattr(e, 'read') else str(e)
            print(angle, 'attempt', attempt, 'failed:', err, flush=True)
        time.sleep(min(120, 10 * 2 ** attempt))
    return angle, 'ERROR', {}, ''

if __name__ == '__main__':
    angles = sys.argv[2:] or list(ANGLES)
    parts = build_parts()
    with ThreadPoolExecutor(min(3, len(angles))) as ex:
        for angle, fin, usage, text in ex.map(lambda a: call(a, parts), angles):
            print(angle, fin, usage.get('promptTokenCount'), usage.get('candidatesTokenCount'), flush=True)
            with open(os.path.join(HERE, f'gemini_{angle}.md'), 'w') as f:
                f.write(f'<!-- model: {MODEL}; finishReason: {fin}; usage: {json.dumps(usage)} -->\n\n{text}\n')
