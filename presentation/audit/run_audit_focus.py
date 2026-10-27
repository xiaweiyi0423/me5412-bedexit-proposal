"""Focused follow-up (round 4b): independent check of the new 3-D joint statics (seat_1dof_cantilever3d.py) and the controller
interlock change (controller_seat.py). Usage: python3 run_audit_focus.py   -> audit/v4/gemini_focus.md"""
import json, os, sys
sys.argv = [sys.argv[0], "/dev/null"]
import run_audit as RA
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
C = os.path.join(ROOT, "model/calc_v13")
txt = lambda f: open(os.path.join(C, f)).read()
prompt = f"""下面是一个单自由度起身座板的机构静力计算（新写的）和控制器代码。请做一次独立、严格的核查，不需要客气。

背景：座板悬臂伸在床边，机构全部在床头一侧（y 正方向）。座板 + 支架是一个刚体，通过铰点 1（绕 y 轴的转动副，装在滑块板上）和一根倾角连杆（两端球铰）连到机架。
滑块板装在同一块侧板（y = 0.32 m）上的两根平行斜导轨上，导轨与竖直成 34°，两导轨在导轨平面内相距 150 mm，每根导轨两个滑块，相距 150 mm。
丝杠螺母经浮动接头只传沿导轨的力。载荷 100 kg × 1.5 沿座面法向，加座板 10 kg，作用点可在座板上任意处，横向偏向敞开一侧 10 cm。

请检查：
1. seat_1dof_cantilever3d.py 的方程是否正确：未知量、力矩参考点、叉乘符号、法向 nf 的方向、滑块和螺母的位置、最小范数解是否等于“滑块等刚度、滑块板刚性”的弹性解、bearings() 里双轴承径向力的推导；
2. 结果是否可信（下面附了输出），有没有漏掉的载荷或会改变结论的假设；
3. 结论“铰点 1 必须做成相距 ≥ 8 cm 的双轴承短轴、连杆两端球铰只受拉压”在机械设计上是否合理，有没有更好的做法；
4. controller_seat.py 里新加的“卸掉的力要到脚上才提速”（shed = min(F_cap − F_seat, F_feet − (BW − F_cap) + 0.15 BW)）和分级自检（15–35% 限速并提示、> 35% 锁定）在逻辑和安全上有没有漏洞。

每个问题请写清证据、因果、严重度和改法；确认无误的部分也请明说。用中文。

# 输出（cantilever3d.json）
{txt("seat_1dof/cantilever3d.json")}

# seat_1dof_cantilever3d.py
```python
{txt("seat_1dof_cantilever3d.py")}
```

# seat_1dof_v5_checks.py（几何常量、rails()、旧 forces()）
```python
{txt("seat_1dof_v5_checks.py")}
```

# seat_1dof_slider.py（simulate：机构运动；平面受力）
```python
{txt("seat_1dof_slider.py")}
```

# controller_seat.py
```python
{txt("controller_seat.py")}
```
"""
RA.COMMON = "你是机械设计和医疗设备控制的资深审稿人。"; RA.ANGLES["focus"] = ""
angle, fin, usage, text = RA.call("focus", [{"text": prompt}])
print(fin, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"))
open(os.path.join(HERE, "v4", "gemini_focus.md"), "w").write(f"<!-- model: {RA.MODEL}; finishReason: {fin}; usage: {json.dumps(usage)} -->\n\n{text}\n")
