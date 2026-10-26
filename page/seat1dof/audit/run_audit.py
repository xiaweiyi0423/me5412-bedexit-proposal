"""Audit the one-DOF seat design (page/seat_1dof.html and the model/calc_v13 scripts behind it) with Gemini 4 (gemini-4-argon).

Usage: python3 run_audit.py <img_dir> [angle ...]     (screenshots from: node shots.js <img_dir>)
The API key is injected by the session proxy. Results go to gemini_<angle>.md next to this script.
"""
import base64, io, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

MODEL = "gemini-4-argon"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:streamGenerateContent?alt=sse"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
IMG = sys.argv[1]
M = os.path.join(ROOT, "model", "calc_v13")

COMMON = """你在审计一个大学课程小组项目（ME5412 Robotics for Healthcare，床边起身台）里的一个子设计：单自由度坐板。坐板在老人起身时跟着身体往前、往上走并前倾，由两侧四连杆加中间一根电动推杆驱动。材料包括：课程背景和老师的要求、设计总结、方案网页源码、全部计算代码、结果摘要（JSON），以及网页各节、机构动画和三视图的截图。

请从下面给你的角度出发，自由地找出这个设计和这份网页真正的问题和薄弱处：推理不成立、模型假设撑不起结论、数字或代码有错、机构或结构有隐患、有安全漏洞、会被老师问住、会误导读者。不必面面俱到，也不必凑数；你认为最重要的优先讲。
每个问题请说清：在哪里（网页的哪一节，或哪个文件的哪个函数），原文或代码证据，为什么是问题（讲因果，区分确定的事实和推测），以及怎么改或怎么验证。按重要性排序，标出严重度（高/中/低）。最后用几句话给出总体判断和最值得先做的一件事。用中文回答，少用术语堆砌。
"""
ANGLES = {
 "A_model": "你的角度：建模与推理。你是懂坐→站生物力学和简化建模的审稿人。重点看：刚性人体轮廓、骨盆与大腿受力分界 4 cm、3 种起身习惯和 81 人用户集是否有代表性、“放手那一刻”的定义、费力（关节力矩/力量）模型的用法；以及“单自由度够用”“前倾差 11° 无害”“凸圆弧座面不如平座面”“助力点放在臀腿交界”这些结论是否站得住、有没有过度引申。",
 "B_mech": "你的角度：机构与结构。你是机械设计审稿人。重点看：四连杆综合方法、传动角与死点、电动推杆的布置和受力计算（虚功法）、销轴/立板/横管的强度与刚度、自锁和断电、间隙磨损、可制造性；以及整台装置的抗倾翻（座板载人往前移 18 cm、人在扶手上用力时，底座是否够长够宽）。",
 "C_safety": "你的角度：安全与人因。你是医疗设备安全评审员，同时有作业治疗师的经验。重点看：连杆、立板、横管和座板之间的夹手夹腿点（横管离大腿只有 2.8 cm）、坐在前倾 25° 的座板上往回坐、坐垫压到底、皮肤剪切、座板唇边和床垫之间的卡夹、回床流程，以及腿的横向宽度假设是否合理。",
 "D_code": "你的角度：代码与数字核查。你是仔细的代码审查者。请逐个读计算脚本，找：符号或单位错误、前滑和坐回余量的定义或计算错误、力跟随（坐板走到接触为止）假设的问题、虚功推力计算、坐垫弹簧床模型、干涉检查的采样漏检、四连杆仿真的分支选择；并核对网页显示的数字与 JSON、总结文档是否一致。",
 "E_teacher": "你的角度：老师兼答辩时最刁钻的提问者。对照老师的要求（CAD 和运动动画、讲清机构和状态机、稳定性、UI 和操作安全），看这个子设计回应得怎么样、网页能不能让人很快看懂；列出最可能把小组问住的问题，并给出更好的回答或需要补的材料。",
}

def img_part(path, maxw=1280):
    im = Image.open(path).convert("RGB")
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)))
    if im.height > 4000: im = im.resize((int(im.width * 4000 / im.height), 4000))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(buf.getvalue()).decode()}}

def summary():
    P = json.load(open(os.path.join(M, "seat_1dof", "page.json")))
    mech = {k: v for k, v in P["mech"].items() if k not in ("frames", "torque_curve", "transmission_curve")}
    mech["act"] = {k: v for k, v in P["mech"]["act"].items()}
    users = {k: {kk: v.get(kk) for kk in ("release_hz", "fwd_slip_max_cm", "min_catch_cm", "contact_len_release_cm", "E0_release", "E0_release_stooped", "a_max_cm")}
             for k, v in P["check"]["design"].items()}
    vert = {k: {kk: v.get(kk) for kk in ("release_hz", "fwd_slip_max_cm", "min_catch_cm", "E0_release")} for k, v in P["check"]["vertical"].items()}
    return dict(mechanism=mech, users_design=users, users_vertical_lift=vert, placements=P["placements"], layout_clearance=P["layout"]["clearance"],
                layout_planes=P["layout"]["Y"], cushion=P["cushion"], seat_shapes=P["shapes"]["table"], design_curve=dict(chosen=P["design_curve"]["chosen"],
                candidates=P["design_curve"]["candidates"], smoothing=P["design_curve"].get("smoothing")), consts=P["consts"],
                assist_points=P["assist"]["points"], assist_rows=P["assist"]["rows"])

def build_parts():
    rd = lambda p: open(os.path.join(ROOT, p)).read()
    text = rd("presentation/audit/context.md")
    text += "\n\n# 设计总结 model/calc_v13/seat_1dof_summary.md\n" + rd("model/calc_v13/seat_1dof_summary.md")
    text += "\n\n# 上一轮（竖直升降 vs 曲线）总结 model/calc_v13/seat_trajectory_summary.md\n" + rd("model/calc_v13/seat_trajectory_summary.md")
    text += "\n\n# 方案网页源码 page/seat1dof/template.html（数据在构建时注入，摘要见文末 JSON）\n```html\n" + rd("page/seat1dof/template.html") + "\n```\n"
    for f in ("seat_trajectory.py", "seat_relative_motion.py", "seat_1dof_design.py", "seat_1dof_fourbar.py", "seat_1dof_fourbar2.py",
              "seat_1dof_layout.py", "seat_cushion.py", "seat_1dof_page_data.py"):
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
            open(os.path.join(HERE, f"gemini_{angle}.md"), "w").write(f"<!-- model {MODEL}, finish {fin}, usage {json.dumps(usage)} -->\n\n" + text)
            print(angle, fin, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), flush=True)
