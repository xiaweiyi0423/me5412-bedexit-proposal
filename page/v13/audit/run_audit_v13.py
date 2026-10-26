"""Audit the v13 proposal page (rise_station_v13.html) and its model/controller code with Gemini 4 (gemini-4-argon).

Usage: python3 run_audit_v13.py <img_dir> [angle ...]
<img_dir> holds section and step screenshots of the rendered page (made with Playwright). The API key is injected by the
session proxy. Results go to gemini_<angle>.md next to this script.
"""
import base64, io, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

MODEL = "gemini-4-argon"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:streamGenerateContent?alt=sse"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
IMG = sys.argv[1]

COMMON = """你在审计一个大学课程小组项目（ME5412 Robotics for Healthcare）的设计方案：床边起身台，第 13 版。材料包括：课程背景和老师的要求、方案网页的源码（文字都在 HTML 和脚本的数据数组里）、起身模型和控制器仿真的 Python 代码及结果摘要，以及网页各部分和“一晚上的往返”11 个步骤的截图。

请从下面给你的角度出发，自由地找出这个方案和这份网页真正的问题和薄弱处：推理不成立、数字或代码有错、设计有漏洞、会被老师问住、会误导读者的地方。不必面面俱到，也不必凑数；你认为最重要的优先讲。
每个问题请说清：在哪里（网页的哪一节、哪一步，或代码的哪个函数），原文或代码证据，为什么是问题（讲因果，区分确定的事实和推测），以及怎么改。按重要性排序，并标出严重度（高/中/低）。最后用几句话给出总体判断和最值得先做的一件事。用中文回答，少用术语堆砌。
"""
ANGLES = {
 "A_argument": "你的角度：核心论证与模型。你是懂坐→站生物力学和简化建模的审稿人。重点看起身模型的扩展（座板托力）是否建得对、结论（起步不是瓶颈、推力上限 0.4–0.6、按能力定义目标人群、离座高度因人而异）是否站得住，有没有过度引申。请读 seat_support.py 的代码。",
 "B_safety": "你的角度：控制与安全逻辑。你是医疗设备 / 个人护理机器人的安全评审员。重点看状态机和控制规则在异常和意外情况下是否闭合，新的“空座保持、回床时坐上高处座板再降”是否引入新风险，仿真是否真的检验了它声称检验的东西。请读 controller_v13.py 的代码。",
 "C_real_use": "你的角度：真实使用场景。你是给居家老人做转移评估的作业治疗师。看“起床、离开、回床”整个夜间往返对目标用户是否现实，哪些环节没想到或想得太乐观。",
 "D_grading": "你的角度：评分人。你是这门课的老师，手边有自己 10/26 给小组的邮件要点和 11/3 的交付要求。看这个方案对你的要求回应得怎么样，离一份好的终稿还差什么，哪些缺口会直接扣分，你最想问小组什么。",
 "E_reader": "你的角度：读者。你是第一次看这个方案网页的工科研究生（也可能是组员）。看网页能不能让人很快弄懂这个装置是什么、怎么用、为什么这样设计；哪里讲得不清、前后不一致、图和文字对不上、术语没解释。",
 "F_qa": "你的角度：答辩时最刁钻、最懂行的提问者。找出最可能把小组问住的问题，尤其是这一版新加的内容（起步计算、能力区间、回床、空座保持、控制规则修改）带来的新问题，并给出更好的回答或需要补的材料。",
}

def img_part(path, maxw=1280):
    im = Image.open(path).convert("RGB")
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}

def build_parts():
    ctx = open(os.path.join(ROOT, "presentation/audit/context.md")).read()
    page = open(os.path.join(ROOT, "page/v13/template.html")).read()
    ss = json.load(open(os.path.join(ROOT, "model/calc_v13/seat_support.json")))
    cs = json.load(open(os.path.join(ROOT, "model/calc_v13/controller_v13.json")))
    summ = dict(seat_support_start_effort_heel08={arm: {h: {c: v["effort"] for c, v in d.items()} for h, d in ss["start"][arm]["heel08"].items()} for arm in ss["start"]},
                min_seat_load_by_height_and_effort={arm: {h: {e: (None if r is None else r["Fs_BW"]) for e, r in d.items()} for h, d in ss["min_seat"][arm].items()} for arm in ss["min_seat"]},
                controller_params=cs["params"], controller_results=[{k: v for k, v in r.items() if k != "series"} for r in cs["scenarios"]])
    text = (ctx + "\n\n# 方案网页源码（page/v13/template.html；数据在构建时注入，摘要见下）\n```html\n" + page + "\n```\n"
            + "\n# 起身模型扩展 model/calc_v13/seat_support.py\n```python\n" + open(os.path.join(ROOT, "model/calc_v13/seat_support.py")).read() + "\n```\n"
            + "\n# 原起身模型中被调用的部分 model/model.py（节选）\n```python\n" + open(os.path.join(ROOT, "model/model.py")).read()[:16000] + "\n```\n"
            + "\n# 控制器和仿真 model/calc_v13/controller_v13.py\n```python\n" + open(os.path.join(ROOT, "model/calc_v13/controller_v13.py")).read() + "\n```\n"
            + "\n# 计算结果摘要（JSON）\n```json\n" + json.dumps(summ, ensure_ascii=False) + "\n```\n\n# 网页截图\n")
    parts = [{"text": text}]
    for f in sorted(os.listdir(IMG)):
        parts.append({"text": f"截图 {f}："}); parts.append(img_part(os.path.join(IMG, f)))
    return parts

def call(angle, parts):
    body = {"system_instruction": {"parts": [{"text": COMMON + "\n" + ANGLES[angle]}]},
            "contents": [{"role": "user", "parts": parts + [{"text": "请从你的角度审计这个方案和网页。"}]}],
            "generationConfig": {"maxOutputTokens": 32768}}
    data = json.dumps(body).encode()
    for attempt in range(6):
        try:
            text, fin, usage = [], None, {}
            with urllib.request.urlopen(urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"}), timeout=1800) as resp:
                for line in resp:
                    line = line.decode().strip()
                    if not line.startswith("data:"): continue
                    r = json.loads(line[5:])
                    for c in r.get("candidates", []):
                        text += [p.get("text", "") for p in c.get("content", {}).get("parts", []) if not p.get("thought")]
                        fin = c.get("finishReason") or fin
                    usage = r.get("usageMetadata", usage)
            if fin == "STOP" and text: return angle, fin, usage, "".join(text)
            print(angle, "attempt", attempt, "incomplete:", fin, flush=True)
        except Exception as e:
            print(angle, "attempt", attempt, "failed:", e.read().decode()[:300] if hasattr(e, "read") else e, flush=True)
        time.sleep(min(120, 10 * 2 ** attempt))
    return angle, "ERROR", {}, ""

if __name__ == "__main__":
    angles = sys.argv[2:] or list(ANGLES); parts = build_parts()
    print("payload MB", round(len(json.dumps(parts)) / 1e6, 2), flush=True)
    with ThreadPoolExecutor(min(3, len(angles))) as ex:
        for angle, fin, usage, text in ex.map(lambda a: call(a, parts), angles):
            print(angle, fin, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), flush=True)
            open(os.path.join(HERE, f"gemini_{angle}.md"), "w").write(f"<!-- model: {MODEL}; finishReason: {fin}; usage: {json.dumps(usage)} -->\n\n{text}\n")
