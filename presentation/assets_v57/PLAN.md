# v57 slide plan: bringing the web-page visuals into the deck

Scope: assets and plan only. Deck sources (`presentation/update_slides_v52.py`, `presentation/slides/*`, tools) are untouched. Nothing is published or committed.

## 0. How to wire these in (for the integrator)

1. Upload each PNG to the Slides artifact as an asset: Artifact publish with `url` + `asset: true`. Batches of ≤25 via `file_paths` work.
2. Add each returned `/_blob/<id>` to `presentation/animations/blobs.json` under the keys below, then reference it with `img(key, alt, w, h)`.
3. Slide frame is 1920×1080 with padding 128/128/160. That leaves a content box of about **1664×792**. All PNGs are 2× or larger, so shrink them to fit; never upscale.

| blobs.json key | file | px | note |
|---|---|---|---|
| cad_3d_shell | 3d_a_shell.png | 1600×1000 | mid stroke, shell semi-transparent, bed ghosted |
| cad_3d_open | 3d_b_open.png | 1600×1000 | same view, shell hidden, mechanism exposed |
| cad_pose_flush | 3d_c1_flush.png | 1000×1000 | pose 1/3, flush with mattress |
| cad_pose_mid | 3d_c2_mid.png | 1000×1000 | pose 2/3 |
| cad_pose_top | 3d_c3_top.png | 1000×1000 | pose 3/3, top of stroke |
| cad_joint | 3d_d_joint.png | 1600×1000 | close-up of cantilever joint (cushion/board hidden, J3 and C1 ghosted) |
| fig_side | fig_side.png | 2896×2952 | side view with part callouts |
| fig_top | fig_top.png | 2896×2230 | top view with part callouts |
| fig_section | fig_section.png | 3096×1946 | section through cantilever bearing pair |
| fea_c1 | fig_fea_c1.png | 2096×1990 | FEA focus: C1 carriage plate ⚠ see caveats |
| fea_beam | fig_fea_beam.png | 2496×1128 | FEA focus: cantilever beam |
| fea_house | fig_fea_house.png | 1896×2696 | FEA focus: bearing housing |
| fea_rail | fig_fea_rail.png | 1496×2108 | FEA focus: rail / carriage |
| cmp_effort | cmp_effort.png | 1460×476 | release-effort medians, 4 options |
| cmp_fall_down | cmp_fall_down.png | 1560×476 | "leg gives way": share caught during the rise |
| cmp_fall_knee | cmp_fall_knee.png | 1300×382 | knee buckling: share not sliding forward |
| seat_hip_paths | seatpage_hip_paths.png | 920×838 | 81 users' hip paths vs vertical-seat zone |
| seat_envelope | seatpage_envelope.png | 1166×942 | ⚠ old 0.66 m top; see caveats |
| dw_assembly | dw_assembly_flush.png | 2520×1782 | assembly drawing |
| dw_C1 / dw_J3 / dw_S7 / dw_J1 | dw_*.png | 2520×1782 | part drawings |

Numbers in the charts come from `model/calc_v13/seat_1dof/bed_baseline.json`, `slider.json` and `fall_catch.json`. Those are the same numbers the deck already quotes, including the per-user median saving of 33% vs the low bed.

## 1. Slide-by-slide proposal (deck order; ★ = new slide)

### cover: swap the visual
- Asset: `cad_3d_shell` in place of the sketch `seat_step3`.
- Why: the first thing reviewers see is the real product. The semi-transparent shell still hints at the mechanism inside.
- No text change.

### whynot: replace the MODES table with charts
- Assets: `cmp_effort` on top; `cmp_fall_down` and `cmp_fall_knee` stacked below, or side by side at about 780 px each.
- Headline (keep): **床不用垫高，省力达到抬高床＋好扶手的水平**
- Bullets:
  - 释放力中位数：起身台 0.26，低床＋横杆 0.40；每人比低床省 33%（中位）
  - 腿一软往下坐：起身台全程接住 52/81 人，抬高床只有 15%
  - 膝盖打软：起身台 81/81 不往前漏
- Speaker-note gist: the table had the same numbers but nobody reads a table at 2 m. The bars say "lowest effort and catches the fall" in one glance. The orange bar is ours. Say "median over 81 simulated users", not "every user".

### mechanism: real CAD instead of the sketch
- Assets: `cad_3d_open` (large, left) plus a 3-pose strip `cad_pose_flush`, `cad_pose_mid`, `cad_pose_top` (right column or bottom row, about 300 px each).
- Optional: `seat_hip_paths` as a small inset with the caption "为什么是曲线：81 人的髋部轨迹不在竖直座板区".
- Headline: **一个电机、一条曲线：座板跟着髋部走**
- Bullets:
  - 平时与床面齐平，不挡上下床
  - 抬升时沿弧线前移＋升高，贴合起身时髋部的真实路径
  - 单自由度：位置一个数就决定姿态，控制和安全检查都简单
- Speaker-note gist: walk the three poses left to right. Point at the curve, not the parts. The vertical-lift comparison image currently on this slide can move to backup.

### ★ new, after mechanism: "单侧悬臂怎么扛住"
- Assets: `fig_section` (left, about 60%) plus `cad_joint` (right).
- Headline: **单侧悬臂：两只轴承扛住全身重量**
- Bullets:
  - 两只轴承相距 45 mm，把弯矩变成一对推拉力；安全系数 3.2
  - Ø75 轴承座离床沿保持 ≥ 1.5 cm，不刮床垫
  - 只在一侧有结构，另一侧完全敞开，方便转身坐下
- Speaker-note gist: this is the obvious reviewer question ("one side only, will it bend?"), so answer it before they ask. Quote only the safety factor. Details sit in the FEA slide.

### ★ new, or appendix: "零件和编号"
- Assets: `fig_side` plus `fig_top` side by side. Both are tall, so give each about 800 px wide.
- Headline: **零件一览：侧视 / 俯视**
- Bullets: none, or a single line "编号与工程图（附录）一一对应".
- Speaker-note gist: orientation only. Skip it if time is short. I recommend the **appendix** to keep the main deck tight.

### ★ new, after risk: placeholder 1, lateral fall (`fall_lateral`)
- Source: `model/calc_v13/seat_1dof/lateral.json` (+ `lateral.png`). **Fill the numbers once the lateral kill test is final.**
- Assets: `lateral.png`, or a deck-style bar re-render of it.
- Headline (draft): **往侧面倒：开放侧和床头侧各有多少余量**
- Bullet slots:
  - 开放侧侧向余量：〈lateral.json → open-side margin〉
  - 床头侧：〈head-side margin〉；横杆加长方案可补到〈value〉
  - 结论一句：哪一侧是短板，以及打算用什么补
- Speaker-note gist: be explicit about what was simulated and what was not. If the margin is thin, say so and show the fix rather than hiding it.

### ★ new, after fall_lateral: placeholder 2, leaving without the platform (`fall_exit`)
- Source: `model/calc_v13/seat_1dof/exit_detect.json` (+ `exit_detect.png`). **Fill the numbers later.**
- Assets: `exit_detect.png`, or a re-render in deck style.
- Headline (draft): **人自己下床不用台子：能不能及时发现**
- Bullet slots:
  - 离床特征检测：检出率〈value〉，误报率〈value〉
  - 报警提前量〈value〉 s（相对于离开床面）
  - 局限：只靠床上传感器，离开后的跌倒不在本系统覆盖范围
- Speaker-note gist: this covers the case where the device is not used at all. Keep the claim at "detects the exit signature", not "prevents the fall".

### ★ new, after limits: "下一步：建模 + 有限元重点"
- Assets: 2×2 grid of `fea_c1`, `fea_beam`, `fea_house`, `fea_rail`, each about 800×380 box with a one-line caption.
- Headline: **下一步：四个最该先算的受力点**
- Captions (one line each):
  - C1 托板：窗口开口处应力集中
  - 悬臂梁：根部弯矩最大
  - 轴承座：两轴承间的推拉载荷
  - 导轨／滑块：偏载下的倾覆力矩
- Speaker-note gist: these are hand-calc hot spots, not FEA results yet. Say "we will verify", not "we verified".

### ★ appendix: "参考工程图"
- Assets: `dw_assembly`, then `dw_C1`, `dw_J3`, `dw_S7`, `dw_J1`. Use one per slide, or assembly alone plus a 2×2 of the four parts.
- Headline: **附录：工程图**
- No bullets. Backup for Q&A only.

### Unchanged
agenda, problem, users, prior, concept, motion, sizing, stability, sensing, statemachine, speed, risk, verify, conclusion, team, questions.

Net change: 3 visuals swapped (cover, whynot, mechanism) and 4 main-deck slides added (cantilever, 2 fall placeholders, next-step FEA). Parts and drawings go to the appendix.

## 2. Caveats to fix before use

1. **fea_c1** still labels the window "窗口（60°）", but the design is now 80°, and the weld triangles sit at the old y positions. The source is `cad/mech_figs.py → fea_c1`. Fix it there and re-render, or crop out the label.
2. **seat_envelope** shows the legacy 0.66 m top and 15° tilt annotations. Do not use it until `page/seat_1dof.html` is updated. `seat_hip_paths` is fine.
3. **cad_joint**: the J4 arm is partly hidden behind the beam. Readable, but not a clean hero shot; keep it secondary to `fig_section`.
4. Placeholder slides must not ship with 〈…〉 slots. Either fill them or drop them.
