"""Open external audit (round 4, v5.6): no assigned angle. Gemini sees the deck + talk guide (bundle from build_bundle_v2.py +
render_slides.js), the seat design page as text, the design summary, and the model code that produces the numbers.
Usage: python3 run_audit_open.py <bundle_dir> <page_text.txt> [run ...]   (runs default: open_1 open_2 open_3; independent samples)
Output: audit/v4/gemini_<run>.md"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor
import run_audit as RA
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..")); OUTD = os.path.join(HERE, "v4"); os.makedirs(OUTD, exist_ok=True)
CODE = ["model/model.py"] + [f"model/calc_v13/{f}" for f in ("seat_trajectory.py", "seat_relative_motion.py", "seat_1dof_design.py", "seat_1dof_handrail.py",
        "seat_1dof_slider.py", "seat_1dof_v5.py", "seat_1dof_v5_checks.py", "seat_1dof_fall_catch.py", "seat_1dof_bed_baseline.py", "seat_support_slider.py",
        "controller_seat.py", "seat_cushion_zoned.py")]
OPEN = """你是一位外部审阅者，懂机器人、机构设计、生物力学建模和医疗护理设备，第一次看到这个大学课程小组项目的全部材料：
汇报 slides 和讲稿、讲稿指南、设计网页的文字、设计总结文档，以及产生所有数字的 Python 模型代码。

没有人给你指定角度。请你自己判断，这个项目现在最重要的问题是什么，可以是任何方面，例如：
- 结论是否真的被证据支持；
- 模型或代码里有没有错误、或站不住的假设；
- 设计本身有没有隐患；
- 材料之间是否矛盾；
- 汇报能否让人看懂；
- 离一份好的终稿还差什么。
不必面面俱到、不必凑数；宁可少而准。

每个问题请写清：
1. 在哪里（slide 页码、网页节、文档节或代码文件和函数）；
2. 原文或代码证据；
3. 为什么是问题，讲清因果，区分已确认的事实和你的推测；
4. 怎么改，或者怎样用一个便宜的检查来确认。

按重要性排序，标出严重度（高 / 中 / 低）。如果你认为某个问题需要更仔细的审计才能定论，请明确说出来，并说明要查什么。
最后用几句话给出总体判断。用中文回答，少用术语堆砌。"""

def build_parts(page_txt):
    ctx = open(os.path.join(HERE, "context_v4.md")).read(); slides = open(os.path.join(RA.BUNDLE, "slides.md")).read()
    summ = open(os.path.join(ROOT, "model/calc_v13/seat_1dof_summary.md")).read(); page = open(page_txt).read()
    code = "\n\n".join(f"### 文件 {f}\n```python\n{open(os.path.join(ROOT, f)).read()}\n```" for f in CODE)
    parts = [{"text": ctx + "\n\n# 一、21 页 slides、讲稿和讲稿指南\n" + slides + "\n\n# 二、设计网页（文字）\n" + page + "\n\n# 三、设计总结文档\n" + summ +
              "\n\n# 四、模型代码\n" + code + "\n\n# 五、每页 slide 截图\n"}]
    imgdir = os.path.join(RA.BUNDLE, "img")
    for f in sorted(os.listdir(imgdir)):
        if f.startswith("full_"): parts.append({"text": f"第 {int(f[5:7])} 页（{f[8:-4]}）截图："}); parts.append(RA.img_part(os.path.join(imgdir, f), (1600, 900)))
    return parts

if __name__ == "__main__":
    page_txt = sys.argv[2]; runs = sys.argv[3:] or ["open_1", "open_2", "open_3"]
    RA.COMMON = OPEN
    for r in runs: RA.ANGLES[r] = "（开放审计：自己决定看什么。）"
    parts = build_parts(page_txt)
    with ThreadPoolExecutor(len(runs)) as ex:
        for angle, fin, usage, text in ex.map(lambda a: RA.call(a, parts), runs):
            print(angle, fin, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), flush=True)
            open(os.path.join(OUTD, f"gemini_{angle}.md"), "w").write(f"<!-- model: {RA.MODEL}; finishReason: {fin}; usage: {json.dumps(usage)} -->\n\n{text}\n")
