<!-- model: gemini-4-argon; finishReason: STOP; usage: {"promptTokenCount": 21942, "candidatesTokenCount": 8293, "totalTokenCount": 30235, "promptTokensDetails": [{"modality": "TEXT", "tokenCount": 21942}], "candidatesTokensDetails": [{"modality": "TEXT", "tokenCount": 8293}]} -->

作为机械设计和医疗设备控制的审稿人，我对提交的 `seat_1dof_cantilever3d.py`、`seat_1dof_v5_checks.py`、`seat_1dof_slider.py` 以及 `controller_seat.py` 进行了独立、严格的交叉核查。

以下是逐项审计报告。

---

### 一、 `seat_1dof_cantilever3d.py` 方程与推导核查

#### 1. 确认无误的部分（Verified Correct）
* **`v3(p, y)` 坐标映射**：将二维平面 `(x, z)` 映射为三维右手系 `(x, y, z)`（x 向床外，y 向床头，z 向上），叉乘遵循标准右手定则。
* **`solve_seat()` 静力平衡**：未知数共 6 个（`F1` 的 3 个分量、`M1x`、`M1z`、连杆轴向力 `T`）。因为铰点 1 是绕 y 轴的转动副，`M1y = 0`；连杆两端球铰且在同一平面 `y = Y["link"]` 内，故 `uL` 的 y 分量为 0，为二力杆。力平衡与绕 `C1` 的力矩平衡方程矩阵 `A` 和右端项 `b` 符号完全正确。
* **方向向量 `e` 和 `nf` 的修正**：在 `main` 中通过 `(VC.rails()[1][0] - VC.rails()[0][0]) @ nf < 0` 强制将 `nf` 修正为从导轨 1 指向导轨 2，弥补了未检查 `g["d"]` 极性的问题。且因为 `s1 - s0 > 0`，`e` 确实指向导轨上方，`pts` 和 `nut` 的坐标生成正确。
* **`solve_plate()` 作用力与反作用力**：座板受滑块板的力为 `F1, M1`，故滑块板受座板的力为 `-F1, -M1`。方程 $\sum \boldsymbol{F}_{\text{react}} + (-\boldsymbol{F}_1) = \boldsymbol{0} \implies \boldsymbol{A}\boldsymbol{x} = \boldsymbol{F}_1$，代码中 `b = -np.r_[-F1, -M1]` 即 `[F1, M1]`，符号正确。
* **`bearings()` 双轴承径向力推导**：设两轴承位于 $y = \pm s_1/2$，反力为 $\boldsymbol{F}_1/2 \pm (\Delta f_x, 0, \Delta f_z)$。其对中心的力矩为 $(0, -s_1/2, 0) \times (-\Delta f_x, 0, -\Delta f_z) + (0, s_1/2, 0) \times (\Delta f_x, 0, \Delta f_z) = (s_1 \Delta f_z, 0, -s_1 \Delta f_x) = (M_{1x}, 0, M_{1z})$，解得 $\Delta f_z = M_{1x}/s_1, \Delta f_x = -M_{1z}/s_1$。代码中的 `fz_d` 和 `fx_d` 符号及合成极值计算完全正确。

#### 2. 发现的问题（Issues Found）

##### **[问题 1.1] 最小二乘解（`pinv`）等价于“等刚度滑块”的前提条件在物理上不成立**
* **证据**：`solve_plate()` 第 44 行使用 `x = np.linalg.pinv(A) @ b` 求解 6 方程 9 未知数的超静定问题，并在文档字符串中声称 `least-norm solution (= equal carriage stiffness on a rigid plate)`。
* **因果推导**：
  设刚性滑块板的微小广义位移为 $\boldsymbol{\delta} = (\Delta \boldsymbol{r}_{C1}, \boldsymbol{\theta})^T$，则第 $i$ 个约束处的变形为 $\delta_i = \boldsymbol{a}_i^T \boldsymbol{\delta}$（其中 $\boldsymbol{a}_i$ 为矩阵 $\boldsymbol{A}$ 的第 $i$ 列）。若第 $i$ 个约束的线刚度为 $k_i$，则反力 $x_i = k_i \delta_i$，写成矩阵即 $\boldsymbol{x} = \boldsymbol{K} \boldsymbol{A}^T \boldsymbol{\delta}$。代入平衡方程 $\boldsymbol{A}\boldsymbol{x} = \boldsymbol{b}$ 得：
  $$\boldsymbol{x} = \boldsymbol{K}\boldsymbol{A}^T (\boldsymbol{A}\boldsymbol{K}\boldsymbol{A}^T)^{-1} \boldsymbol{b}$$
  只有当权重矩阵 $\boldsymbol{K} = k \boldsymbol{I}_9$ 时，上式才退化为 Moore-Penrose 伪逆 $\boldsymbol{A}^+ \boldsymbol{b} = \boldsymbol{A}^T(\boldsymbol{A}\boldsymbol{A}^T)^{-1}\boldsymbol{b}$。
  在实际机械中：
  1. 沿导轨方向 `E3` 仅有 `nut` 1 个未知数，与其他 8 个正交，不受刚度比影响；
  2. 但其余 8 个未知数中，4 个是滑块的法向力（`Yh`，即径向/上下开口方向），4 个是滑块的侧向力（`N3`）。线性滑块（尤其是四列圆弧沟槽或哥德式沟槽）的径向刚度 $k_y$ 与侧向刚度 $k_n$ 通常不等；
  3. 更严重的是，绕 $y$ 轴的面内转角 $\theta_y$ 既会引起 `N3` 方向的位移，但**完全不会**引起 `Yh` 方向的位移；而滑块板自身的平面外抗弯刚度（板厚仅 15 mm，见 `Y_PLATE` 注释 `0.03 .. 0.015`）远小于其面内拉压刚度！将滑块板假设为绝对刚体且令 $k_y = k_n$，会人为拉平各滑块载荷。
* **严重度**：**中（Medium）** — 虽然法向（$y$ 向）的 4 个力和侧向（`nf` 向）的 4 个力在几何上近似解耦（因为 4 个滑块共面于 $y = Y_{\text{rail}}$），使得 $k_y \neq k_n$ 对各自方向的分配影响有限，但**忽略滑块板面外弹性变形**会严重低估靠近 `C1` 的那个滑块（`o=0, s=0`）的 $y$ 向拔出力。
* **改法**：在汇报材料中必须明确注明“3093 N 为理想刚性滑块板假设下的理论下界”，并在选型时对最近端滑块乘以 $1.3 \sim 1.5$ 的弹性偏载系数（或将板厚增加/加焊背面筋条）。

##### **[问题 1.2] `variant_plain_pin_link_side_force_N`（普通销轴变体）计算存在物理与数学双重错误**
* **证据**：`seat_1dof_cantilever3d.py` 第 69 行：
  ```python
  d = v3(P2, Y["link"]) - v3(P1, yc1); Fy_link = abs(M1[0]) / max(abs(d[2]), 1e-6)
  ```
* **因果推导**：
  1. **数学漏项**：即便假设连杆端头 `P2` 提供侧向力 $F_{y,\text{link}}$ 来平衡力矩，位于 $\boldsymbol{d} = (\Delta x, \Delta y, \Delta z)$ 处的力 $(0, F_y, 0)$ 对 `C1` 产生的力矩是 $\boldsymbol{d} \times (0, F_y, 0) = (-\Delta z F_y, \, 0, \, \Delta x F_y)$。它只能提供一个固定比例 $(-\Delta z : \Delta x)$ 的 $(M_x, M_z)$ 组合，根本无法独立平衡任意的 $M_{1x}$ 和 $M_{1z}$（单靠一个 $F_y$ 甚至无法满足静力平衡，原体系会变成机构发生侧倾！）。
  2. **除零奇异性（Singular Artifact）**：随着座板升降，`P1` 和 `P2` 的高度差 $\Delta z = d[2]$ 可以趋近于 0。代码中仅用 `max(abs(d[2]), 1e-6)` 截断，如果某帧 $\Delta z$ 很小，算出的 `Fy_link` 会飙升到无穷大。输出中的 `5660 N (at z=0.558)` 只是因为恰好采样到了一个较小的 $\Delta z$，而非真实物理设计值。
* **严重度**：**低（Low）**（因为这只是一个用来反证“不能用普通单销”的对比项，不影响主方案，但论证方程在力学上是错的）。
* **改法**：若要计算用连杆抗倾覆的真实受力，必须将连杆改为绕 y 轴的圆柱副/叉耳，或者用 $\sqrt{M_{1x}^2 + M_{1z}^2} / \sqrt{\Delta x^2 + \Delta z^2}$ 估算最小所需侧向力，不能只除 `abs(d[2])`。

---

### 二、 计算结果可信度与遗漏载荷核查

#### 1. 现有输出结果的量级核查
* 垂向总载荷 $F_z \approx -(150 + 10) \times 9.81 = -1569.6\text{ N}$（当 $\phi \approx 0$ 时）。
* 当载荷在 $y_l = -0.10\text{ m}$ 时，到 `c1` 轴中心（$y_{c1} = 0.269\text{ m}$）的横向力臂为 $0.369\text{ m}$。
* 倾覆力矩 $M_{1x} \approx 1569.6 \times 0.369 = 579.2\text{ N}\cdot\text{m}$。当座板有倾角 $\phi$ 时，法向力产生 $F_x$ 分量，进一步产生 $M_{1z}$，合成力矩 `c1_moment_Nm = 589 Nm`，与手算完全吻合。
* 当轴承间距 $s_1 = 0.08\text{ m}$ 时，力偶引起的轴承径向力 $\Delta F = 589 / 0.08 = 7362.5\text{ N}$，叠加平面内主反力的一半（约 $1000\text{ N}$），得到 `c1_bearing_radial_N_s80 = 8402 N`，计算完全准确。

#### 2. 遗漏的关键载荷与假设漏洞（Missing Loads & Flawed Assumptions）

##### **[问题 2.1] 严重遗漏：座面切向力（摩擦力 + 臀部前滑/后推力）及座板中心下方偏移**
* **证据**：第 58 行 `Pl = v3(Q + rot(phi) @ np.array([xo, 0]), yl); Fl = v3(-1.5 * 100 * G * n_, 0.0) + np.array([0, 0, -10 * G])`。
* **因果推导**：
  1. `Fl` 假设人体载荷**100% 严格沿座面法向 `n_`**。但在控制器 `controller_seat.py` 的文档注释第 23 行中，作者自己写道：*“friction on a 16 deg seat alone can shift the vertical sum by up to ~17 % of the seat force”*。起身过程中，用户臀部与坐垫之间存在最大可达 $\mu N \approx 0.3 \times 1471 = 441\text{ N}$ 的切向摩擦力！
  2. 切向力不仅直接改变对 `C1` 和 `P2` 的平面力矩（显著增大连杆力 `T` 和丝杠力 `nut`），而且作用在坐垫上表面（距离 `c1` 有約 $10 \sim 20\text{ cm}$ 的高度差），会大幅放大峰值力。
* **严重度**：**高（High）** — 直接影响丝杠选型、制动器保持力矩（`brake_torque_Nm`）以及连杆屈曲校核。
* **改法**：在 `Fl` 中加入切向分量 $\pm \mu (1.5 \times 100 G) \boldsymbol{t}$（其中 $\boldsymbol{t} = \text{rot}(\phi)[1, 0]^T$，$\mu$ 取 $0.25 \sim 0.30$），取正负两个方向的最恶包络。

##### **[问题 2.2] 严重遗漏：单侧悬臂刚度不足导致的座板自由端下垂（Elastic Deflection）**
* **证据**：代码只做了静力强度分析，未做刚度/变形校核。
* **因果推导**：
  1. 在 $589\text{ N}\cdot\text{m}$ 的悬臂扭矩和 $80\text{ mm}$ 轴承跨距下，外侧轴承承受 $8402\text{ N}$ 载荷。普通深沟球轴承或调心轴承在 $8.4\text{ kN}$ 加上轴自身弯曲下，在 $80\text{ mm}$ 跨距上很容易产生 $0.3^\circ \sim 0.5^\circ$ 的角位移；
  2. 叠加滑块副（跨距 $150\text{ mm}$，受 $3093\text{ N}$ 拔出力）的接触变形、滑块板弯曲、以及**单侧壁板（housing wall，立在底座上）的侧向弯曲**；
  3. 悬臂总长从导轨面 $y = 0.32\text{ m}$ 到座板外缘 $y = -0.22\text{ m}$，长达 **$540\text{ mm}$**！只要根部累积产生 $1.5^\circ$ 的横滚角变形（Roll），座板敞开侧边缘就会向下塌陷 $540 \times \sin(1.5^\circ) \approx 14\text{ mm}$。老年用户坐上去会明显感到座板向外侧倾斜（产生向床外滑落的恐惧感），且极易导致座板侧缘与机构箱内壁（间隙见 `pinch()` 为 $30\text{ mm}$）发生摩擦或卡滞。
* **严重度**：**高（High）**。
* **改法**：必须增补从机架底座 $\to$ 侧壁板 $\to$ 导轨滑块 $\to$ 滑块板 $\to$ `c1` 轴 $\to$ 座板支架的串联柔度（Compliance）估算，确保在 $100\text{ kg}$ 静载下座板外端下垂量 $\le 5\text{ mm}$。

##### **[问题 2.3] 扶手载荷（Handrail Load）与座板载荷的耦合遗漏**
* **证据**：`tipping()` 中指出扶手立柱装在床头侧机构箱前方，横杆横跨用户前方；`controller_seat.py` 中允许用户在横杆上施加 $0.3 \sim 0.4\text{ BW}$ 的下压力或 $0.2\text{ BW}$ 的上拉力。
* **因果推导**：如果扶手安装在同一侧壁/底座结构上，人手推拉扶手的力也会传给机架侧板（影响侧板变形和地脚锚栓）；如果用户一边猛坐座板一边拉扶手，锚栓拉力会叠加。目前 `cantilever3d.py` 和 `tipping()` 将两者完全割裂计算。
* **严重度**：**中（Medium）**。

---

### 三、 机械设计合理性评估（“c1 双轴承 ≥ 8 cm 短轴 + 连杆球铰”方案）

**审稿结论：将连杆设为两端球铰（二力杆）是完全正确的；但让全部 589 N·m 的悬臂倾覆力矩先缩颈通过一根跨距仅 8 cm 的悬臂销轴（c1），再放大回 15 cm × 15 cm 的滑块阵列，在机械设计上是典型的“力流瓶颈（Force-Flow Bottleneck）”，非常不合理！**

#### 1. 为什么现有 `c1` 短轴方案不好？
1. **无谓的力放大（7.4 倍放大器）**：
   外部载荷仅 $1570\text{ N}$，导轨跨距有 $150\text{ mm}$（力臂比约 $2.4:1$，滑块力约 $3.1\text{ kN}$）。但因为中间串联了一个跨距仅 $80\text{ mm}$ 的 `c1` 短轴，力臂比暴增至 $369 / 80 = 4.6:1$，导致微小空间内的轴承径向力高达 **$8402\text{ N}$**！
2. **结构空间与装配悖论**：
   根据代码的 `assumptions`：
   * 机构箱内壁 `wall_in = 0.25 m`（含开槽）
   * `c1` 轴中心 `yc1 = 0.269 m`
   * 连杆平面 `link_y = 0.28 m`
   * 滑块板中心 `plate_y = 0.2975 m`
   * 丝杠中心 `screw_y = 0.291 m`
   * 导轨平面 `rail_y = 0.32 m`
   如果要放一根跨距 $s_1 = 80\text{ mm}$（甚至 $100\text{ mm}$）的轴，以 `yc1 = 0.269 m` 为中心，该轴将从 **$y = 0.229\text{ m}$（伸出内壁外侧 $21\text{ mm}$）一直贯穿到 $y = 0.309\text{ m}$（穿过连杆平面、穿过丝杠平面、穿过滑块板，直抵导轨表面前 $11\text{ mm}$）**！
   这不仅直接与丝杠（$y=0.291\text{ m}$）和连杆（$y=0.28\text{ m}$）发生**严重的物理空间干涉**，而且要在厚仅 $15\text{ mm}$ 的滑块板上挑出一个长 $80\text{ mm}$、能承受 $589\text{ N}\cdot\text{m}$ 根部弯矩的轴承座套筒，套筒外径至少需 $65 \sim 75\text{ mm}$（需用 30205/32006 级别圆锥滚子轴承），根本塞不进导轨与内壁之间 $70\text{ mm}$ 的狭小夹层！

#### 2. 更好的机械设计做法（改进方案）

* **改进方案 A：用“大直径薄壁交叉滚子轴承（Crossed Roller Bearing，如 RB/RU 系列或谐波减速器刚轮轴承）”替代 $8\text{ cm}$ 细长短轴（强烈推荐）**
  * **做法**：不在 $y$ 方向拉长轴距，而是采用一个轴向（$y$ 向）厚度仅 $15 \sim 25\text{ mm}$、节圆直径 $D = 120 \sim 150\text{ mm}$ 的**法兰式交叉滚子轴承**（或四点接触球转盘轴承），直接贴装在滑块板侧面（占用 $y = 0.255 \sim 0.275\text{ m}$，完全避开后方的丝杠 $0.291\text{ m}$ 和导轨）。
  * **优势**：
    1. 倾覆力矩直接由 $120 \sim 150\text{ mm}$ 的大滚道直径通过轴向推力偶承受，等效跨距比 $80\text{ mm}$ 短轴大，且**完全消除了悬臂轴与轴承座套筒的根部弯曲变形**；
    2. 轴向尺寸极薄（$\le 25\text{ mm}$），彻底解决与丝杠、滑块板的横向穿插干涉；
    3. 单个 RU120 级交叉滚子轴承的额定静倾覆力矩可达 $1500 \sim 2500\text{ N}\cdot\text{m}$ 以上，刚度是双深沟球短轴的 $5 \sim 8$ 倍。
* **改进方案 B：将导轨-滑块副做在座板支架与摇臂之间（或外移内壁轴承）**
  * 如果坚持用双轴承短轴，应把内侧轴承直接布置在座板下方（如 $y = 0.15\text{ m}$ 处，利用座板底面台阶空间），外侧轴承布置在滑块板上（$y = 0.28\text{ m}$），此时跨距天然达到 **$130 \sim 150\text{ mm}$**，轴承径向力立刻从 $8402\text{ N}$ 骤降至 **$4500\text{ N}$** 左右，且不侵占滑块板后方的丝杠空间。

---

### 四、 `controller_seat.py` 控制逻辑与安全漏洞核查

#### 1. 确认无误的部分（Verified Correct）
* **回床二段停靠逻辑（`EMPTY_HOLD` / `EMPTY_MOVE`）**：`down_edge` 配合 `self.paused` 标志位能够正确实现“从高处按住降 $\to$ 在 `ret_h` (0.50 m) 自动停住 $\to$ 松开再按住降 $\to$ 继续降到床面 `H0`”的逻辑。
* **倾角余弦修正**：`fs_v = z["F_seat"] * cphi` 正确使用了编码器高度查表得到的座板倾角余弦。

#### 2. 发现的控制与安全漏洞（Logic & Safety Flaws）

##### **[问题 4.1] `shed`（卸荷到脚提速）公式在“双手上拉扶手”或“人体轻于预设 60 kg”时存在严重功能失效（Deadlock）**
* **证据**：`controller_seat.py` 第 48 行 `Params.__init__` 硬编码 `bw_kg=60.0`，第 94 行：
  ```python
  shed = min(P.F_cap - self.fs_f, z["F_feet"] - (P.BW - P.F_cap) + P.feet_allow)
  ```
* **因果推导**：
  展开第二项：`z["F_feet"] - (P.BW - P.F_cap) + P.feet_allow`。当 `F_cap = 0.50 BW`、`feet_allow = 0.15 BW` 时，该项简化为：
  $$\text{shed}_2 = F_{\text{feet}} - 0.35\,\text{BW}$$
  这意味着：**只有当踏板力 $F_{\text{feet}} > 0.35\,\text{BW}$ 时，座板才开始有非零速度；要达到满速（$\text{shed} = 0.35\,\text{BW}$），踏板力必须达到 $F_{\text{feet}} \ge 0.70\,\text{BW}$！**
  这导致了三个严重后果：
  1. **未做坐姿自动称重（Auto-Tare / Weighing），轻体重用户永远无法升起座板（严重度：致命 Critical）**：
     代码中 `P.BW` 是固定参数（$60\text{ kg}$）。如果一个 $45\text{ kg}$ 的老年女性使用该设备（设计文档中明确包含 $45\text{ kg}$ 用户），她的总重只有 $0.75\,\text{BW}_{60}$。当她把座板力卸到 $0.5\,\text{BW}_{45} = 0.375\,\text{BW}_{60}$ 时，即使没有手部借力，她脚上的力也只有 $0.75 - 0.375 = 0.375\,\text{BW}_{60}$，$\text{shed}_2 = 0.025\,\text{BW}_{60}$，**座板几乎纹丝不动，随后触发 2 秒 `t_stall` 停机！** 相反，如果是 $100\text{ kg}$ 的用户，刚坐上去还没发力，$F_{\text{feet}}$ 就已经超过 $0.35\,\text{BW}_{60}$ 了，完全失去了防后靠保护！
  2. **双手上拉扶手（`pullup` 场景）时被错误降速**：
     在 `pullup` 场景中，用户向上拉横杆 $0.20\,\text{BW}$（即 $F_{\text{bar}} = -0.20\,\text{BW}$）。此时由竖直力平衡：$F_{\text{feet}} = \text{BW} - F_{\text{seat},v} - F_{\text{bar}} = 1.20\,\text{BW} - F_{\text{seat},v}$（注：在手拉横杆时 $F_{\text{bar}} < 0$，脚压力反而增大；但如果用户是**手向下撑床面或扶手立柱未装传感器处**，或 $F_{\text{bar}} > 0.15\,\text{BW}$ 向下压横杆时），只要向下撑横杆的力超过 `feet_allow` ($0.15\,\text{BW}$)，哪怕不到 `hang` 阈值 ($0.30\,\text{BW}$)，$\text{shed}_2$ 就会直接扣减速度，与 `hang` 限速逻辑发生隐式重叠。
  3. **一阶滤波相位不匹配**：
     第一项中的 `self.fs_f` 经过了 $\tau_f = 0.08\text{ s}$ 的低通滤波，但第二项中的 `z["F_feet"]` 却是**未滤波的原始踏板信号**！在真实硬件中，踏板冲击噪声会直接耦合进 `v_cmd`。
* **改法**：
  1. 必须在 `SEATED` 状态（当 `h <= H0 + 0.03` 且姿态稳定时，或者刚脱离床面 `h = H0 + 0.03` 瞬间）对 `total = fs_v + F_feet + F_bar` 进行采样锁定，作为当前用户的真实体重 `BW_est`；或直接将公式改为基于初始坐姿踏板力的增量形式；
  2. 若横杆有双向力传感器，正确的“防向后靠床垫”逻辑应当直接把经过滤波的横杆支撑力算入合法去向：
     `shed_received = (F_feet_f + max(0.0, F_bar_f)) - (BW_est - P.F_cap)`，这样既能精确拦截“把重量卸到无传感器的床垫上（`leanback`）”，又不需要拍脑袋凑一个 `0.15 BW` 的 `feet_allow`。

##### **[问题 4.2] 分级自检（Graded Sum Check）在物理上被座面摩擦力吃掉一半裕度，且 `LOWERING` 状态下忽略了 `warn`**
* **证据**：
  1. 文档注释：*“friction on a 16 deg seat alone can shift the vertical sum by up to ~17 % of the seat force”*；
  2. 第 73–79 行：`total = fs_v + z["F_feet"] + z["F_bar"]`，`sum_tol = 0.15`，`sum_lock = 0.35`。
* **因果推导**：
  1. **15% 阈值与 16° 倾角摩擦自相矛盾**：
     座板单轴力传感器测得的是法向力 $N$，无法测量沿座面的切向摩擦力 $f_t$。真实竖直方向座板合力为：
     $$F_{\text{seat},z} = N \cos\phi \pm f_t \sin\phi$$
     代码只用了 $N \cos\phi$（即 `fs_v`）。当 $\phi = 16^\circ$、摩擦系数 $\mu = 0.35$、用户在低位承重 $N = 0.8\,\text{BW}$ 时，漏算的切向力竖直分量为 $0.8 \times 0.35 \times \sin 16^\circ \approx 0.077\,\text{BW}$；若用户大腿后侧或小腿肚轻微擦碰座板前缘（法向朝前，切向朝上），偏差轻易突破 $0.15\,\text{BW}$。因此，在真实人体试验中，`15%` 的一级告警（限速 30% + 语音报错）会被**频繁误触发（False Positive）**。
  2. **`LOWERING` 状态下触发 `warn` 无任何降速动作**：
     第 75 行 `check` 在 `LOWERING and occupied` 时是生效的，也会置位 `self.warn = True`。但在第 122–128 行的 `elif s == "LOWERING":` 分支中，**根本没有检查 `self.warn`**（只在 `LIFTING` 第 96 行检查了 `self.warn`）！这意味着下降过程中即使传感器偏差在 $15\% \sim 35\%$ 之间持续超过 $0.5\text{ s}$，控制器既不减速也不做任何处理。
  3. **`LOCKED` 状态的进入清除盲区**：
     一旦进入 `LOCKED` 状态（第 84 行），状态机再也没有任何退出 `LOCKED` 的路径（即使降回到了床面 `H0` 且人已经离开，设备依然死锁在 `LOCKED`，必须断电重启代码）。
* **严重度**：**中（Medium）**。
* **改法**：
  1. 将一级阈值 `sum_tol` 从 `0.15` 放宽至 `0.20`，或将倾角摩擦包络 $N \cdot \mu_{\max} \sin\phi$ 作为动态容差带叠加到 `sum_tol` 上：`tol_dyn = P.sum_tol + 0.3 * (z["F_seat"] / P.BW) * np.sin(np.radians( abs(phi_of(self.h)) ))`；
  2. 在 `LOWERING` 分支中同样加入 `if self.warn: v_cmd = -P.v_down * 0.5; self.limited = True`；
  3. 在 `LOCKED` 分支中规定当降到底部 `self.h <= H0 + 1e-4` 且空载后，允许复位或进入维护待机状态。

##### **[问题 4.3] 加速度限制（`a_max`）在停机时被硬清零旁路（Jerk Spike）**
* **证据**：`controller_seat.py` 第 132 行：
  ```python
  dv = np.clip(v_cmd - self.v, -P.a_max * DT, P.a_max * DT)
  self.v = v_cmd if v_cmd == 0.0 else self.v + dv
  ```
* **因果推导**：当 `v_cmd == 0.0` 时（例如用户松手、坐偏 `cop_off`、或到达高度），代码直接令 `self.v = 0.0`，**完全绕过了 `a_max` 斜坡减速**，产生无穷大的理论减速度（阶跃急停）。在带着一侧悬臂的老年用户以 $3\text{ cm/s}$ 上升时，电机如果按阶跃零速指令直接抱死或满矩制动，会造成明显的机械冲击和身体前倾失稳。
* **严重度**：**低（Low）**（仿真与实机平滑问题）。
* **改法**：删去三元表达式，统一使用斜坡：`self.v = self.v + dv`（仅在掉电抱闸 `!z["power"]` 时硬置零）。

---

### 五、 总结清单（供修订对表）

| 序号 | 模块 | 问题简述 | 严重度 | 建议行动 |
| :--- | :--- | :--- | :--- | :--- |
| **1** | 机械设计 (`c1`) | $8\text{ cm}$ 双轴承短轴把载荷放大至 $8.4\text{ kN}$，且在 $y=0.229..0.309\text{ m}$ 区间与丝杠/连杆干涉 | **高** | 改用贴装在滑块板上的**大直径薄壁交叉滚子轴承（如 RU120）**，或将内轴承外移至座板下方使跨距 $\ge 14\text{ cm}$ |
| **2** | 静力计算 (`Fl`) | 漏掉座面切向摩擦力（$\pm \mu N$）和悬臂刚度变形校核 | **高** | 在 `Fl` 中加入 $\pm 0.3 N$ 切向力重算极值；增加座板敞开侧边缘的满载下垂量校核（目标 $\le 5\text{ mm}$） |
| **3** | 控制算法 (`shed`) | `P.BW` 硬编码 $60\text{ kg}$，导致 $45\text{ kg}$ 用户因 $F_{\text{feet}} < 0.35\,\text{BW}_{60}$ 无法升起座板 | **高** | 增加坐姿/离床瞬间的**自动称重（Auto-Tare）**获取当前用户真实 `BW`，并对 `F_feet` 施加同时间常数的低通滤波 |
| **4** | 静力计算 (`pinv`) | 最小范数解假设滑块板绝对刚性且径/侧向等刚度，低估近端滑块拔出力 | **中** | 选型时对 `carriage_radial_y_N` (3093 N) 乘以 $1.3 \sim 1.5$ 的弹性偏载系数 |
| **5** | 控制算法 (`warn`) | 16° 座板摩擦会吃掉一半 `15%` 容差；`LOWERING` 时忽略了 `warn` 降速 | **中** | 引入随 $\sin\phi$ 变化的动态容差带；在 `LOWERING` 中补齐 `self.warn` 降速逻辑 |
| **6** | 静力对比 (`variant`) | `abs(M1[0]) / abs(d[2])` 漏掉 $M_{1z}$ 且在 $\Delta z \to 0$ 时奇异发散 | **低** | 改为力矩模长除以平面距离 $\sqrt{\Delta x^2 + \Delta z^2}$ |
| **7** | 控制算法 (`self.v`) | `v_cmd == 0.0` 时绕过 `a_max` 直接硬置零产生急停冲击 | **低** | 正常停机也走 `-P.a_max * DT` 斜坡减速（仅断电时硬置零） |
