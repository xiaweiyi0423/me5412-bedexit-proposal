<!-- model gemini-4-argon, finish STOP, usage {"promptTokenCount": 130439, "candidatesTokenCount": 6025, "totalTokenCount": 136464, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 112997}, {"modality": "IMAGE", "tokenCount": 17442}], "candidatesTokensDetails": [{"modality": "TEXT", "tokenCount": 6025}]} -->

以下从**代码与数字核查**角度，对单自由度坐板的计算脚本、结果 JSON、设计总结文档及网页源码进行逐一审计。问题按严重度（高→中→低）排序。

---

### 1. 【严重度：高】推杆推力与电机扭矩的虚功计算漏掉了外力矩项（座板旋转功）

- **位置**：
  - `seat_1dof_layout.py` 的 `actuator_candidates()` 内 `forces(act, Fs)` 函数
  - `seat_1dof_fourbar2.py` 的 `actuator_search()` 内 `forces(act, Fs)` 函数
  - `seat_1dof_fourbar.py` 与 `seat_1dof_page_data.py` 的 `torque(Fs)` 函数
- **代码证据**：
  ```python
  # seat_1dof_layout.py
  n_ = rot(s[i][1]) @ np.array([0.0, 1.0]); Fx = -Fs * n_ + np.array([0, -10 * G])
  dW = -(Fx @ (s[i + 1][0] - s[i - 1][0])); dL = Ls[i + 1] - Ls[i - 1]
  out.append(dW / dL if abs(dL) > 1e-7 else np.inf)
  ```
- **为什么是问题（确定的数学与力学事实）**：
  1. **漏掉旋转虚功 $M \cdot \Delta \phi$**：代码用虚功原理计算推杆推力 $F_{\text{act}} = -\frac{\mathbf{F} \cdot \Delta \mathbf{Q}}{\Delta L}$，这隐含假设外力始终精确作用在坐板局部坐标原点 $\mathbf{Q}$（座面中心）。但你的模型自己算出：随着老人起身或对“髋晚前移”的用户，接触点（以及坐垫压力中心）会移向坐板前缘（托腿垫，$x_{\text{loc}}$ 最大达 $+8.5\text{ cm}$）。当 $1.5 \times 100\text{ kg}$ 静载或 $0.5\text{ BW}$ 推力偏离中心距离 $e$ 时，会产生关于 $\mathbf{Q}$ 的俯仰力矩 $M = -F_s \cdot e$。正确的虚功方程应为：
     $$F_{\text{act}} \Delta L + \mathbf{F} \cdot \Delta \mathbf{Q} + M \cdot \Delta \phi = 0$$
     在坐板前倾增大阶段（$\Delta \phi > 0$）且载荷靠前时，这一项与平动项异号或同号，会显著改变推杆推力和连杆内力；而在行程后段（$\phi$ 从 $26.7^\circ$ 回落到 $4.7^\circ$，$\Delta \phi < 0$），力矩项直接叠加在推杆载荷上。
  2. **忽略摩擦与连杆偏载**：推杆在中间平面（$y=0$），通过一根细横管（半径 $2\text{ cm}$）驱动两侧距离 $57\text{ cm}$（$y = \pm 28.5\text{ cm}$）的摇杆 B。代码中只算了理想平面机构的虚功，完全没计入横管的扭转变形和两侧销轴的别劲摩擦。
- **怎么改 / 怎么验证**：
  在 `forces()` 和 `torque()` 中，把接触点偏心矩 $M = -F_s \cdot x_{\text{loc}}$ 乘以角度差分 `-np.radians(s[i+1][1] - s[i-1][1])` 加入 `dW`；取最不利偏心位置（如 $x_{\text{loc}} = +0.06\text{ m}$ 和 $-0.04\text{ m}$）包络复算推杆峰值力。

---

### 2. 【严重度：高】网页、JSON 与总结文档中“推杆上端安装位置”自相矛盾（相差 158 mm）

- **位置**：
  - 网页源码 `page/seat1dof/template.html` 第 405 行（`drawMechStatic` 的 `dimTable`）
  - 总结文档 `seat_1dof_summary.md` 第三版 vs 第四版
  - 结果数据 `layout.json` / 文末 JSON 摘要中的 `mechanism.act`
- **原文与代码证据**：
  - **JSON 真实计算值**：`"act": {"on": "B", "t": 0.6, "o": -0.03, "D": [0.05, 0.05]}`，摇杆 B 长度 `"L2": 0.2443`。根据 `act_E()` 代码 `G0 + act["t"] * d + act["o"] * nrm`，推杆上端铰点 E 位于摇杆 B **从底座铰点 B 算起 60% 处**（距 B 约 $147\text{ mm}$，**在摇杆末端内侧约 $98\text{ mm}$**），且向顺时针法向偏置 $30\text{ mm}$。
  - **网页源码硬编码错误**：`template.html` 里写死了 `["推杆上端","摇杆 B 末端外侧 60 mm"]`（截图 `05_mech.png` 右侧表格清晰显示此句）。这是第三版 `swept15` 方案（当时 $t=1.2, o=0.06$）残留的文字，第四版改成 `layout` 后忘了更新模板文字列。
- **为什么是问题**：
  网页左侧的 SVG 机构图（按 JSON 中 $t=0.6$ 绘制，横管在摇杆 B 中段）与右侧紧挨着的“尺寸（交给 CAD）”表格（写着“摇杆 B 末端外侧 60 mm”）直接打架。如果负责 CAD 的队友照着表格文字去建模，推杆长度、行程和干涉检查全部作废；老师看图和表一眼就能发现图文不符。
- **怎么改**：
  把 `template.html` 中的硬编码字符串改为根据 `act.t` 和 `act.o` 动态生成：如 `距铰点 B 沿杆 ${(act.t*100).toFixed(0)}%（${(m.L2*act.t*1000).toFixed(0)} mm），法向偏置 ${(act.o*1000).toFixed(0)} mm`。

---

### 3. 【严重度：高】对比基线“不公平”：新坐板放宽了托腿允许范围（18 cm），竖直升降却锁死在 12 cm

- **位置**：
  - `seat_1dof_design.py` 第 207 行（Step 6 验证对比）
  - 网页首屏 KPI（截图 `00_header.png`）与步骤 8 表格（截图 `08_check.png`）
- **代码证据**：
  ```python
  # seat_1dof_design.py
  jobs = [(u, cv, PAD_AMAX, {}) for u in USERS] + [(u, curve_vertical(), 0.12, {}) for u in USERS]
  ```
  且在 `seat_1dof_page_data.py` 中：
  - 新方案重跑时用了 `PAD_AMAX = 0.18`（允许接触点在大腿后侧 $18\text{ cm}$ 内）且 `seat_kw = dict(r_e=0.03)`（前缘圆角 $3\text{ cm}$）；
  - 而网页用来对比的 `vertical` 数据直接继承自 `design.json`，用的是 `amax = 0.12`（只允许 $12\text{ cm}$）且默认 `r_e = 0.02`（前缘圆角 $2\text{ cm}$）。
- **为什么是问题**：
  在 `track()` 函数中，一旦接触点 `a > A_MAX`，循环立即 `if not ok: break` 判定为坐板脱开（放手）。给新坐板设 $18\text{ cm}$、给竖直升降设 $12\text{ cm}$，人为导致竖直升降在更低的髋高（`release_hz`）就被强制判定“脱开”，从而拉高了竖直升降的“放手费力”（0.273 vs 0.251）。如果老师问：“如果给竖直升降的坐板前缘也加上同样的 18 cm 软托腿垫和 3 cm 圆角，差距还有这么大吗？”，你们会被问住。
- **怎么改 / 怎么验证**：
  在 `seat_1dof_page_data.py` 中，用完全相同的 `PAD_AMAX = 0.18` 和 `seat_kw = dict(r_e=0.03)` 重跑 `curve_vertical()`，或者在网页表格注释中明确说明竖直方案未加长托腿垫。

---

### 4. 【严重度：中】累计前滑（Slip）的定义与达标判定存在数学漏洞：允许“先大幅后滑、再前滑”相互抵消

- **位置**：
  - `seat_relative_motion.py` 的 `track()` 函数（第 118–120 行）
  - `seat_1dof_design.py` 的 `track_user()` 函数（第 60 行）
- **代码证据**：
  ```python
  # seat_relative_motion.py
  if prev is not None:
      pb = carry(pz, prev["bf"]); loc_now = (pb - Qk) @ Rm
      slip += float(loc_now[0] - prev["seat_x"])
  row["slip"] = slip
  ```
  ```python
  # seat_1dof_design.py
  s["fwd_slip_max_cm"] = round(100 * max([r["slip"] for r in good] + [0.0]), 1)
  ```
- **为什么是问题**：
  1. **`fwd_slip_max_cm` 取的是累计值 `slip` 从 0 开始的最大值，而不是正向滑移增量之和，也不是区间最大正向滑移**。看截图 `05_mech.png` 左下角的读数：在起身 35% 时，选中用户的“累计前滑”是 **`-4.7 cm`**（即坐板相对人往前跑了 $4.7\text{ cm}$，皮肤和裤子已经承受了 $4.7\text{ cm}$ 的摩擦滑移）。如果在后半程人再相对于坐板往前滑 $+6.0\text{ cm}$，累计 `slip` 最终只变成 $+1.3\text{ cm}$，代码算出的 `fwd_slip_max_cm` 是 $1.3\text{ cm} \le 2.0\text{ cm}$，直接判为“合格”！但实际上人在坐板上先往后蹭了 $4.7\text{ cm}$、再往前滑了 $6.0\text{ cm}$。
  2. **曲面弧长被投影成了局部 $x$ 坐标差**：`loc_now[0] - prev["seat_x"]` 只算了坐板局部坐标系下的 $x$ 投影差。当接触点在圆角前缘（`r_e = 3 cm`）附近移动时，表面切向是倾斜的，用 $\Delta x$ 代替弧长 $\Delta s$ 会低估实际滑移。
- **怎么改 / 怎么验证**：
  - 区分“相对于起点的最大正向位置偏移”和“从最低谷起算的最大前滑反弹量” `max_{i <= j} (slip[j] - slip[i])`，并在表格中同时报告最大负向滑移（坐板往前蹭大腿的距离，目前在很多用户上达到 $-5 \sim -8\text{ cm}$），诚实说明为什么这需要衣物与坐垫间具备适当的滑动或软垫剪切变形。

---

### 5. 【严重度：中】干涉检查存在三处硬编码与采样漏检，且床沿间隙违反了自己的设定约束

- **位置**：`seat_1dof_layout.py`
- **代码与数字证据**：
  1. **床沿间隙仅 $0.5\text{ cm}$，违反代码注释的 $1\text{ cm}$ 约束**：
     文件头注释写明：`"Here every rigid part must stay out of the bed block (x < 0, z < 0.42 m) by at least 1 cm over the whole travel"`，且 `CLR = 0.01`。但在 `cost(v)` 中，这只是一个软惩罚 `base + 5 * max(0.0, CLR - w)`。最终选出的机构 `rigid_vs_bed_floor_cm` 只有 **`0.5 cm`**（出现在起始位置座板刚性底板与床垫侧面之间）。老人坐下时床垫侧面会受压鼓出，且台架有弹性变形，$5\text{ mm}$ 的刚性间隙极易发生刮擦卡死。
  2. **脚部胶囊体高度硬编码为常数 `0.035 m`，未随身高缩放**：
     在 `body_caps(pz, sub)` 中：
     ```python
     heel = np.array([A[0] - 0.25 * sub.foot_len, 0.035])
     toe = np.array([A[0] + 0.75 * sub.foot_len, 0.035])
     ```
     加上脚踏板厚度（网页画了 $1.3\text{ cm}$ 或纵轨 $4\text{ cm}$）和踝关节高度 `sub.ankle_h = 0.039 * H`（$1.75\text{ m}$ 用户踝高 $6.8\text{ cm}$），脚背靠近踝关节处的实际高度在 $8 \sim 10\text{ cm}$，而代码把整只脚建成了中心在 $z=3.5\text{ cm}$、半径 $3.5\text{ cm}$（即顶面永远只有 $7.0\text{ cm}$ 高）的水平圆柱，低估了高个子用户脚背/脚后跟的高度。
  3. **优化筛选时的稀疏下采样**：
     - `cost(v)` 中调 `mech_bed_clear(v, s[::3])`（只查 1/3 的帧）；
     - `actuator_candidates()` 中 `for f in s[::8]:`（每 8 帧才查一次推杆与床的干涉），最后输出 `actbed` 时改成 `s[::5]`；
     - `seg_pts(X, Y_, n=12)` 把长达 $30 \sim 47\text{ cm}$ 的推杆/摇杆只离散成 12 个点（间距约 $3 \sim 4\text{ cm}$）去算对床角 $(0, 0.42)$ 的距离 `bed_d(pts)`。点对块的距离检测在折角处如果只采样线段上的离散点，两点之间跨越床角 $(0, 0.42)$ 时会产生数毫米的漏检（弦高误差）。
- **怎么改**：
  - 将线段对矩形床块 $(-\infty, 0] \times [0, 0.42]$ 的距离改为解析的**线段-线段最短距离**，消除 `seg_pts` 离散采样误差。
  - 将座板刚性部分起点 `LIP = 0.035` 稍微加大到 `0.045`（即软唇边留 $4.5\text{ cm}$），即可直接把床沿刚性间隙从 $0.5\text{ cm}$ 扩大到 $1.5\text{ cm}$。

---

### 6. 【严重度：中】坐垫独立弹簧床模型存在三处物理失真（积分方向、触底刚度突变、坐下时不计触底硬化）

- **位置**：`seat_cushion.py`
- **代码证据**：
  1. **`sitdown()` 函数算坐下下陷时，漏掉了触底硬化项（Bottoming stiffness）**：
     对比 `load()`（第 62 行）和 `sitdown()`（第 99 行）：
     ```python
     # load() 中包含 50 倍触底刚度：
     p = k * np.minimum(sq, 0.8 * t) + np.where(bott, 50 * k * (sq - 0.8 * t), 0)
     # sitdown() 中却直接截断了最大力，完全没有加触底后的支撑力：
     F = float((k * np.minimum(sq, 0.8 * t) * ds * W).sum())
     if F >= target or (sq > 0.8 * t).any(): return dict(..., F_BW=round(F / (60 * G), 2))
     ```
     正因如此，在 `sitdown` 一接触到 `0.8 * t` 时循环立刻退出，导致 JSON 和摘要里出现 `"中软": {"sink_mm": 48.5, "bottom": true, "F_BW": 0.53}`、`"软": {"F_BW": 0.4}` 这种反常数字（目标明明是承受 $0.75\text{ BW}$ 的静坐重量，代码在力只达到 $0.40\text{ BW}$ 时就停止下移了）。
  2. **面元长度 `ds` 取的是人体轮廓弧长，而非坐板法向投影长度**：
     `f = (p[sq > 0] * ds[sq > 0] * W)[:, None] * nrm`。Winkler 弹簧床定义在坐板表面上，压强 $p$ 乘以坐板表面微元 $\text{d}x_{\text{seat}}$ 才等于法向力。当大腿与坐板存在夹角 $\alpha$ 时，$\text{d}s_{\text{body}} = \text{d}x_{\text{seat}} / \cos\alpha$，直接乘人体弧长 `ds` 会虚增有效接触面积和支撑力。
  3. **时间常数 $\tau$ 在压到底（bottoming）附近被算得虚假地小**：
     `kq = (L2["Fm"] - L["Fm"]) / max(dq, 1e-6)`。一旦某一个采样点压缩量刚超过 $0.8t$，刚度瞬间乘以 50 倍，`kq` 暴增，算出的时间常数 $\tau = 1/(k_v k_q)$ 瞬间变小，掩盖了软坐垫在触底前响应极慢的问题。

---

### 7. 【严重度：中】“力跟随（走到接触为止）”在刚体模型与坐垫模型之间脱节，导致高个子起身初期座板“悬空追赶”

- **位置**：`seat_relative_motion.py` 的 `rise()` 与 `track()`；`seat_cushion.py` 的 `solve_stage()`
- **代码证据**：
  - 在 `rise()` 中，用户的起始髋高是按自己的臀厚算的：`hz0 = Z0 + r_b`。
  - 对于偏胖用户（`r_b = 0.11 m`），坐姿髋高 `hz0 = 0.53 m`。当他按 `p = 0.6`（髋早前移）起身时，髋部立刻前移，而坐板在起始段必须先沿着为 `H1.50, r_b = 0.09` 拟合的曲线走。
  - 在刚体模型 `track()` 中，不管坐板要走多远，只要在其 $0.66\text{ m}$ 的总行程内能碰到人体轮廓（`touch()` 遍历整个 `curve` 找到第一个 `gap <= 0` 的点），就认为此刻坐板**瞬时**到达了该位置并给出 $0.5\text{ BW}$ 推力。
- **为什么是问题**：
  实际上电动推杆有最大速度限制（README 写明：`速度 = k × (推力上限 − 座板测到的力)，封顶为个人最快速度`）。如果某个阶段人体接触点在曲线上的对应参数 $q$ 变化率 $\frac{\text{d}q}{\text{d}t}$ 超过了推杆最大速度，坐板根本追不上人，会直接脱开（力降为 0）。代码完全是几何求交（准静态无限速度追赶），没有校核整个起身过程中所需坐板速度 $\frac{\Delta q}{\Delta f}$ 是否出现突变或超速。
- **怎么改 / 怎么验证**：
  检查 `rows_real` 中相邻起身步长（$\Delta f$）对应的机构索引差分 `np.diff([r["k"] for r in rows])`。如果某一步 $\Delta k$ 很大，说明坐板需要瞬间大幅前移才能贴住大腿，需在局限性中说明或限制起身初期的曲线斜率。

---

### 8. 【严重度：低】多处数字、文件引用与构建产物不一致（老师或读者核对时会困惑）

1. **网页页脚的数据来源写错了脚本和 JSON 文件名**：
   - **位置**：`template.html` 第 259 行（截图 `09_limits.png` 底部下方）
   - **证据**：写着 `数据来源：model/calc_v13/seat_1dof_design.py → seat_1dof/design.json`。但实际上 `design.json` 是第一版“双曲线导轨槽”的数据；当前网页注入的是第四版四连杆数据，由 `seat_1dof_layout.py` 和 `seat_1dof_page_data.py` 生成到 `seat_1dof/page.json`。
2. **`seat_1dof_summary.md` 与 `cushion.json` / 网页表格的数字对不上**：
   - **位置**：`seat_1dof_summary.md` 第二版“坐垫刚度”段落 vs 截图 `07_cushion.png`
   - **证据**：总结文档写“起身到 55% / 70% 时托不住的人数从 8 / 25 增加到 35 / 52；推荐中硬坐垫……起身时下陷 2.8 cm，峰值压强 17 kPa……托不住的只剩 1 / 9 人”（这是基于第二版四连杆 `fourbar.json` 算出的 `cushion.json` 数据）；而在同一篇总结文档的第四版末尾又写“配中硬坐垫时，起身到 55% / 70% 托不住的分别是 0 / 3 人”（这是 `layout.json` 的数据）。但**网页第 7 步的坐垫表格（截图 `07_cushion.png`）展示的仍然是第二版机构的 `1 / 9 人`**，而网页第 5 步对比表里 `layout` 行数据又是 `0 / 3 人`。同一个网页里对同一个推荐坐垫+机构组合，第 5 步和第 7 步的“托不住人数”不一致。
3. **README 与子设计网页的核心设计主张完全相反**：
   - **位置**：项目 `README.md` 的“第 12 版设计改动（2026-10-26）” vs 整个 `seat_1dof.html`
   - **证据**：README 明确写着：*“取消座板前倾，改为竖直升降。一个推杆驱动的四连杆只有一个自由度，倾角由高度决定，做不到‘离座后停在高处、座板水平’”*。而本子设计网页的核心结论却是推翻竖直升降、改用前倾 $26.7^\circ$ 的单自由度四连杆。去见老师 consultation 前，必须统一团队口径（到底主方案是用竖直升降，还是把单自由度前倾四连杆作为最新 v13 方案并解释如何解决坐回顺坡下滑问题）。
4. **死代码与冗余计算**：
   - `seat_1dof_fourbar.py` 第 47 行：`np.arctan2(dv[1] * 0 + (P2 - P1)[1], (P2 - P1)[0])` 中 `dv[1] * 0` 属于无意义的残留代码；
   - 同文件第 77 行：`if np.max(np.diff([p[4] for p in s])) * 0 != 0: pen += 1`，由于乘以 0，条件恒为 False（除非出现 `NaN`），注释意图未实现。

---

### 总体判断与最值得先做的一件事

- **总体判断**：这套计算脚本工程量扎实，从人体姿态、接触点力学（LP）、四连杆轨迹综合、坐垫弹簧床到矢状面干涉检查形成了一条完整的闭环，可视化网页也做得非常清晰。但代码存在**三处实质性的物理/数学漏洞**（虚功算推力漏掉偏心矩项、对比竖直升降时使用了不同的托腿垫长度阈值 `0.18 vs 0.12`、前滑指标允许正负滑移抵消），以及**两处明显的图文数据打架**（网页把推杆上端位置写错成“摇杆 B 末端外侧 60 mm”、第 7 步坐垫表还在用旧版四连杆数据）。
- **最值得先做的一件事**：**立刻修正网页 `template.html` 中“推杆上端：摇杆 B 末端外侧 60 mm”的硬编码错误，并在 `seat_1dof_layout.py` 的推杆力计算 `forces()` 中补上接触点偏心带来的旋转虚功项 $M\Delta\phi$**。这两处直接关系到交给队友做 CAD 和结构校核的尺寸与载荷是否正确，改起来不到 10 行代码，却能避免汇报时出现低级穿帮。