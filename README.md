# ME5412 Robotics for Healthcare：夜间床边起身辅助（小组 proposal）

问题：居家、还能独立生活但腿部力量下降的老人，夜里从床沿坐→站→站稳→第一步这一段容易出事。

两个候选方案：

- **方案甲 · 动态扶手**：装在床上，平时当床栏；坐到床沿后轻推，扶手转到工作角度并在承重时锁死。
- **方案乙 · 床边起身台（推荐）**：床不改造。老人坐在床沿、脚踩台架踏板，往前挪到与床齐平的短座板上；按横杆上的“起”键后，座板升到 0.66 m 并前倾 15°，L 形扶手随座板升高。
  - 推力上限约为体重的一半，人要自己承担一部分体重。
  - 抬升中出现异常，先回水平再缓降；离座后座板保持水平，万一坐回去能接住人。

核心模型结论（2D 准静态坐→站线性规划，effort = 最吃力关节用掉的力量比例）：

| 情形 | 结果 |
|---|---|
| 起身台升到 0.66 m vs 抬高床（0.58 m）+ 扶手 | 低 17–20%（四种手臂假设） |
| 起身台升到 0.66 m vs 低床（0.42 m）撑床垫 | 低 30–40% |
| 起身台只升到 0.60 m vs 抬高床 | 差不多（−5% 到 +4%） |

所以起身台存在的理由是：只在起身那一刻，升到固定床设不到的高度。

## 目录

```
page/
  bedexit_proposal.html   最终网页（单文件，直接用浏览器打开）
  build_v11.py            生成网页：读 v10_body.html + 模型数据 → bedexit_proposal.html、v11_body.html
  build_v10.py            上一版构建脚本（build_v11 会读取其中的 CSS 片段；它本身依赖 archive/v9_body.html）
  v10_body.html           build_v11 的输入
  v2_template.html, v3_extra.css   页面头部和样式
  archive/                更早的构建脚本、中间版本和截图脚本
model/
  model.py                坐→站准静态模型（scipy HiGHS 线性规划）
  compare_v11.py          低床 / 抬高床 / 方案甲 / 方案乙，四种手臂假设，按图纸几何 → compare_v11.json
  seat_height_v11.py      座高 0.40–0.70 m 扫描（横杆按设计位置）+ 敏感性 → seat_height_v11.json
  export_explorer_v10.py  方案甲扶手位置热力图数据 → explorer_v10.json
  tipping_v11.py          台架倾翻：设计载荷 177 N → tipping_v11.json
  compare_v10.py, seat_height_v10.py, tipping_v10.py   上一版（扶手位置自由优化）
  archive/                更早的脚本和结果（含已弃用的“手上最多 10% 体重”假设）
docs/
  prior-art-bed-exit-assist.md   现有技术和文献检索
plan/
  plan.html               组内分工页（单文件，直接用浏览器打开）：每个角色要说明什么、建议做法、资料、示意图
  figs.py                 生成分工页里的示意图（侧视图、受力图、执行器、倾翻）→ figs.json；图已嵌入 plan.html
```

## 复现

```bash
pip install numpy scipy
cd model
python compare_v11.py         # 约 2 分钟，多进程
python seat_height_v11.py
python export_explorer_v10.py
python tipping_v11.py
cd ../page
python build_v11.py           # 生成 bedexit_proposal.html
```

## 模型的主要假设与局限

- 2D 侧视、准静态，只分析离座那一瞬间；受试者模型为 60 kg、1.60 m，关节力量是假设值。
- “手臂弱”用四种方式表示：手力上限 25% 体重（以 Schultz/Alexander 1992 的实测为锚）、肩肘力量 ×0.5、×0.35、正常手臂。
- 床垫按刚性计算，对两种床的基线有利。
- 座面前倾的效果没有建模：离座瞬间座面已不受力。
- 往前挪 25–30 cm 是否可行、“起”键还是自动触发、目标人群界定，仍待组内确认（见网页第四部分）。本项目只做概念、设计和仿真，不做实物和实验。
- 待处理：扶手升到高位（约 0.88 m）时，35 kg 台架侧向只能承受约 129 N，低于设计值 177 N；可选对策为加宽底座（半宽约 0.45 m）、加配重、与床腿固定，或人离开踏板后再降回。

截至 2026-10-23。
