# English deck: glossary and style (shared by every agent)

The English deck is the FINAL presentation (15 min including the 46 s film, ME5412 Robotics for Healthcare, Group 16). Speakers are Chinese students presenting in English: notes must be easy to say aloud.

## Product and core terms (use exactly these)
| Chinese | English |
|---|---|
| 床边起身台 | Bed-Exit Seat (the product name; title case) |
| 座板 | seat (the moving seat board); 坐垫 cushion |
| 起身 / 起身动作 | rising; sit-to-stand (STS) — first use "sit-to-stand (STS)", then "rise"/"STS" |
| 坐回 | sit back down |
| 回床 | return to bed |
| 床沿 | bed edge |
| 低床 0.42 m / 抬高床 0.58 m | low bed (0.42 m) / raised bed (0.58 m) |
| 竖直升降 | vertical lift |
| 斜导轨 + 倾角连杆 | inclined guide + tilt link |
| 导轨 / 滑块 / 丝杠 | linear guide / carriage / ball screw |
| 双导轨 | twin linear guides |
| 铰点 1 / 铰点 2 | pivot 1 / pivot 2 |
| 一个自由度；3 个转动副 + 1 个移动副 | one degree of freedom (1-DOF); 3 revolute + 1 prismatic joint |
| 单侧悬臂 | one-sided cantilever |
| 机构箱 | mechanism housing |
| 扶手横杆 / L 形扶手 | grab bar / L-shaped grab bar |
| 握把开关（握紧才升、松手就停） | grip switch (hold to rise, release to stop) — "hold-to-run" |
| 按住"降" | hold "Down" |
| 踏板 | footplate |
| 测力 / 测力单元 | force sensing / load cell |
| 压力中心 | centre of pressure (CoP) |
| 自检 | self-check |
| 锁定 | lock-out |
| 失电制动 | power-off brake |
| 离心限速 | centrifugal speed limiter |
| 状态机 | state machine (states: Standby, Seated, Lifting, Stopped, Standing hold, Lowering, Empty seat held, Locked) |
| 体位性低血压 | orthostatic hypotension |
| 腿一软 | legs give way |
| 接住 / 接得住 | catch / caught (the hips land on a support) |
| 省力 / effort | effort (a model index: lower = easier) |
| 81 个模拟用户 | 81 simulated users |
| 设计曲线 | design path |
| 前倾 | forward tilt |
| 安全系数 | safety factor (SF) |
| 合力作用点 | ground-reaction point |
| 支撑多边形 | support polygon |
| 有限元 | FEA |
| 待补 | TODO (shown on slides as "[TODO]") |
| 角色 1–5 | Role 1–5 |
| 准静态二维模型 | 2D quasi-static model |
Units: keep SI with a space (0.42 m, 586 N·m, 5.2 kN, 15.7°, 3 cm/s). Keep every number exactly as in the Chinese slide.

## Style
- Slide title (h2) = the page's conclusion as a short sentence ("action title"), e.g. "Inclined guide + tilt link tracks the design path within 8 mm". Eyebrow (small line above) = section, e.g. "3 · MECHANISM DESIGN ③". Sentence case for titles.
- Body text: phrases, not paragraphs ("Hold to rise, release to stop"; "SF 3.2"). No filler words.
- English runs ~40% longer than Chinese: shorten rather than shrink fonts. Never below 24 px. Re-check every layout.
- Fonts: replace 'Noto Sans SC' with 'Inter' and 'Noto Serif SC' with 'Source Serif 4' in every style (body: `font-family:'Inter', Arial, sans-serif`; titles: `font-family:'Source Serif 4', Georgia, serif`). Keep colours and layout.
- Speaker notes (`<aside>`): spoken English, short sentences, plain words (B2 level), first person plural ("we"). Budget: about 130 spoken words per minute; keep each page's note to roughly the same speaking time as the Chinese one (Chinese chars ÷ 230 ≈ minutes → words ≈ minutes × 130). Keep every number. Do not add claims that are not in the Chinese.
- Honesty markers stay: "about", "estimated", "not yet tested", "[TODO]".
- Images: keep every `<img src="/_blob/...">` exactly as it is (the lead swaps in English figures later). Translate `alt` text to English.
