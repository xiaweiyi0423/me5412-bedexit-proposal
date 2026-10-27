"""Round 2: audit the v5 / v5.1 one-DOF seat (one-side inclined rail + tilt link, tilt cap 15 deg, fixed handrail pole, zoned
cushion) with Gemini 4 (gemini-4-argon).

Usage: python3 run_audit_v5.py <img_dir> [angle ...]     (screenshots from: node shots_v5.js <img_dir>)
The API key is injected by the session proxy. Results go to v5/gemini_<angle>.md.
"""
import base64, io, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

MODEL = "gemini-4-argon"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:streamGenerateContent?alt=sse"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
IMG = sys.argv[1]
M = os.path.join(ROOT, "model", "calc_v13")

COMMON = """你在审计一个大学课程小组项目（ME5412 Robotics for Healthcare，床边起身台）里的一个子设计：单自由度坐板，第五版（含 5.1）。坐板在老人起身时跟着身体往前、往上走并前倾（上限 15°）。机构是单侧斜导轨 + 倾角连杆：座板支架上一个铰点装在丝杠驱动的滑块上，沿直的斜导轨走；另一个铰点用连杆拉到底座铰点 B。全部机构在床头一侧，床尾一侧敞开，方便回床转腿。扶手是固定在底座上的竖直立杆。丝杠螺母带手动快速释放，配恒流阻尼器做应急下降。5.1 又研究了后硬前软的分区坐垫，想把推力从大腿移到骨盆，并为此把导轨加长了 3 cm。
第四版做过一轮审计（报告附在材料里），第五版就是针对那轮审计改的。
材料包括：课程背景和老师的要求、设计总结、上一轮审计报告、方案网页源码、全部计算代码、结果摘要（JSON），以及网页各节、机构动画（三种坐垫）、接触区放大图和三视图的截图。

请从下面给你的角度出发，自由地找出这个设计和这份网页真正的问题和薄弱处：推理不成立、模型假设撑不起结论、数字或代码有错、机构或结构有隐患、有安全漏洞、会被老师问住、会误导读者。上一轮已经指出并处理过的问题，只有在处理得不对或不彻底时再提。不必面面俱到，也不必凑数；你认为最重要的优先讲。
每个问题请说清：在哪里（网页的哪一节，或哪个文件的哪个函数），原文或代码证据，为什么是问题（讲因果，区分确定的事实和推测），以及怎么改或怎么验证。按重要性排序，标出严重度（高/中/低）。最后用几句话给出总体判断和最值得先做的一件事。用中文回答，少用术语堆砌。
"""
ANGLES = {
 "A_model": "你的角度：建模与推理。你是懂坐→站生物力学和简化建模的审稿人。重点看：分区坐垫一节的推理——“前半程能移到骨盆、后半程因为大腿倾角远大于座板倾角而移不过去”，“省力不是靠骨盆分界、推断来自压力中心后移”；费力模型新加的分布载荷（骨盆段帮髋和膝、大腿段只帮膝）；托不住时按导轨末端的力计算；15° 前倾上限下的坐回防滑（tan φ）；放手时机和固定立杆的费力；以及这些结论有没有过度引申。",
 "B_mech": "你的角度：机构与结构。你是机械设计审稿人。重点看：斜导轨 + 倾角连杆的综合方法和误差、导轨加长 3 cm 后末段座板后仰、丝杠推力（虚功法、偏心载荷）、连杆和滑块受力、单侧悬臂扭矩约 370 N·m 对导轨/滑块/支架的要求、立柱和底座、床头一侧侧梁外移到 +33 cm 后的抗倾翻、手动快速释放 + 恒流阻尼的可实现性、分区坐垫在座板骨架上的做法（前区下沉 3 cm）、可制造性和成本。",
 "C_safety": "你的角度：安全与人因。你是医疗设备安全评审员，同时有作业治疗师的经验。重点看：剩下的两处剪切夹点、坐在前倾 15° 或末段后仰 −3° 的座板上往回坐、分区坐垫坐着时坐骨下 23–49 kPa 的峰值压强和皮肤剪切、单侧悬臂座板受偏载时的侧倾、固定立杆的位置和抓握、横推约 276 N 就翻的侧向稳定、应急下降（谁来拉释放、下沉多快、人在什么姿势）、回床转腿的通道。",
 "D_code": "你的角度：代码与数字核查。你是仔细的代码审查者。请重点读 seat_cushion_zoned.py、seat_trajectory.effort 新增的分布载荷分支、seat_1dof_slider.py（eval 模式和 rail_ext）、seat_1dof_v5_checks.py（倾翻、夹点、应急）、seat_1dof_page_data_v5.py（接触区逐帧求解），找符号或单位错误、力的方向、二分搜索与单调性假设、托不住时的处理、统计口径（中位数、托不住是否计入）、干涉和夹点检查的采样漏检；并核对网页显示的数字与 JSON、总结文档是否一致。",
 "E_teacher": "你的角度：老师兼答辩时最刁钻的提问者。对照老师的要求（CAD 和运动动画、讲清机构和状态机、稳定性、UI 和操作安全），看第五版回应得怎么样、网页能不能让人很快看懂（特别是新加的分区坐垫一节和接触区图）；列出最可能把小组问住的问题，并给出更好的回答或需要补的材料。",
}

def img_part(path, maxw=1280):
    im = Image.open(path).convert("RGB")
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)))
    if im.height > 4000: im = im.resize((int(im.width * 4000 / im.height), 4000))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}

def summary():
    P = json.load(open(os.path.join(M, "seat_1dof", "page.json")))
    mech = {k: v for k, v in P["mech"].items() if k not in ("frames",)}
    users = P["check"]["design"]
    vert = {k: {kk: v.get(kk) for kk in ("release_hz", "fwd_slip_max_cm", "min_catch_cm", "E0_release")} for k, v in P["check"]["vertical"].items()}
    lay = {k: v for k, v in P["layout"].items() if k != "frames"}
    # contact-patch statistics per cushion over the animation frames
    cs = {}
    for kc in ("u", "z1", "z2"):
        fr = [f["cush"][kc] for a in P["anim"].values() for f in a["frames"] if f.get("seat") and f.get("cush")]
        ok = [c for c in fr if not c["lost"]]
        cs[kc] = dict(frames=len(fr), lost=len(fr) - len(ok), len_cm_med=sorted(c["len_cm"] for c in ok)[len(ok) // 2], p_max_med=sorted(c["p_max"] for c in ok)[len(ok) // 2],
                      pel_med=sorted(c["pel"] for c in ok)[len(ok) // 2])
    return dict(mechanism=mech, users_design=users, users_vertical_lift=vert, placements=P["placements"], layout=lay, cushion_uniform_study=P["cushion"],
                zoned=P["zoned"], contact_patch_anim=cs, design_curve=dict(chosen=P["design_curve"]["chosen"], phi_max=P["design_curve"]["phi_max"]), consts=P["consts"],
                assist_points=P["assist"]["points"])

def build_parts():
    rd = lambda p: open(os.path.join(ROOT, p)).read()
    text = rd("presentation/audit/context.md")
    text += "\n\n# 设计总结 model/calc_v13/seat_1dof_summary.md（第五版和 5.1 在最后）\n" + rd("model/calc_v13/seat_1dof_summary.md")
    text += "\n\n# 上一轮（第四版）审计报告 page/seat1dof/audit/audit_report.md\n" + rd("page/seat1dof/audit/audit_report.md")
    text += "\n\n# 方案网页源码 page/seat1dof/template.html（数据在构建时注入，摘要见文末 JSON）\n```html\n" + rd("page/seat1dof/template.html") + "\n```\n"
    for f in ("seat_trajectory.py", "seat_relative_motion.py", "seat_1dof_design.py", "seat_1dof_v5.py", "seat_1dof_slider.py", "seat_1dof_v5_checks.py",
              "seat_1dof_layout.py", "seat_cushion.py", "seat_cushion_zoned.py", "seat_1dof_page_data_v5.py"):
        text += f"\n# model/calc_v13/{f}\n```python\n" + rd("model/calc_v13/" + f) + "\n```\n"
    text += "\n# 被调用的原起身模型 model/model.py（节选）\n```python\n" + rd("model/model.py")[:14000] + "\n```\n"
    text += "\n# 结果摘要（JSON）\n```json\n" + json.dumps(summary(), ensure_ascii=False) + "\n```\n\n# 网页截图\n"
    parts = [{"text": text}]
    for f in sorted(os.listdir(IMG)):
        parts.append({"text": f"截图 {f}："}); parts.append(img_part(os.path.join(IMG, f)))
    return parts

def call(angle, parts):
    body = {"system_instruction": {"parts": [{"text": COMMON + "\n" + ANGLES[angle]}]},
            "contents": [{"role": "user", "parts": parts + [{"text": "请从你的角度审计这个设计和网页。"}]}],
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
    with ThreadPoolExecutor(3) as ex:
        for angle, fin, usage, text in ex.map(lambda a: call(a, parts), angles):
            open(os.path.join(HERE, "v5", f"gemini_{angle}.md"), "w").write(f"<!-- model {MODEL}, finish {fin}, usage {json.dumps(usage)} -->\n\n" + text)
            print(angle, fin, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), flush=True)
