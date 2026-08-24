---
name: video-prompt-compiler
description: 将口语化、模糊或碎片化的视频想法编译为目标视频模型可执行的电影级、工业级、品牌级、微表演级、剪辑或 2D/3D 生产提示词。先判断真实素材剪辑、T2V、I2V、Reference、V2V/Edit、Extend、剧本转分镜、2D、AIGC 3D 还是真实 CAD/Blender，再建立事实约束账本与 VideoPromptIR，生成“精确版/表现版”两个候选，通过硬门槛和多维百分比评分择优，最后按 MiniMax H3、Hailuo 2.3、Seedance 2.0、Kling VIDEO 3.0、Veo 3.1、Runway Gen-4.5、Wan2.2、LTX-2 等适配器渲染。适用于“我只会自然语言”“优化这条视频 Prompt”“做工业级/电影级描述”“反推参考视频”“按素材剪片”“生成失败怎么修”等任务。默认只编译，不调用收费媒体模型。
license: MIT
metadata:
  version: v0.0.0.2
  language: zh-CN
  display_name_zh: 视频提示词编译器｜自然语言→电影级·工业级·多模型 Prompt
  default_output: selected_copy_prompt_or_director_pack
---

# Video Prompt Compiler

## 结论性合同

用户继续用自然语言表达，不需要学习摄影、模型参数或剪辑术语。本 Skill 负责完成：

```text
自然语言
→ 约束账本
→ 生产方法路由
→ VideoPromptIR
→ 精确候选 + 表现候选
→ 硬门槛
→ 多维评分择优
→ 目标模型渲染
→ 结构验证
→ 失败后的最小 Delta 修复
```

本 Skill 不是“形容词扩写器”。`高级、电影感、工业感、震撼、真实` 必须转成可观察的主体、动作、空间、摄像机、光线、材质、时间、声音、结束状态和不变量。

默认停止在 Prompt 编译阶段。没有用户明确批准，不调用图片、视频、语音、音乐或付费 API。

## 运行边界

必须保持：用户指定的品牌名、产品名、素材编号、台词、旁白、时长、比例、事实、参数和禁止项。

不得编造：客户、项目、检测结论、材料参数、精度、硬度、寿命、节省金额、产能、安全结论或视频模型当前 UI 能力。

真实素材存在时，优先让真实素材承担证据；AIGC 只补缺口、解释不可见过程或做明确标注的概念镜头。

AIGC 3D 不能冒充可测量 CAD、装配校核、有限元、温度场、流场或工程仿真。

## 0. 最小交互策略

内部先完成路由和缺口判断，不把模型选择负担甩给用户。

只有缺失信息会让生产方法完全改变时，才问一个关键问题；其余信息以显式 `ASSUMPTION` 或 `UNKNOWN` 推进。常见默认：

- 未给模型：先生成通用 IR，再给 1 个默认模型和 1 个备选模型；
- 未给时长：按最短可表达版本设计；
- 未给比例：作为界面参数留空，不写进 Prompt 正文；
- 有图片：默认 I2V，而不是重新描述并发明主体；
- 有真实视频：默认剪辑或编辑，而不是 T2V 重拍；
- 完整成片超过 15 秒：默认拆时间线和逐镜 Prompt；
- 工业内容：事实与物理优先于品牌包装；
- 人物内容：触发—反应—余韵优先于情绪形容词。

## 1. 建立约束账本

扩写前分为四层：

- `LOCKED_FACT`：用户、文件、图片、视频或已批准版本已经确定；
- `CREATIVE_SPACE`：可合理补充、不会改变事实的观察性细节；
- `UNKNOWN`：重要但没有证据或无法从当前平台确认；
- `FORBIDDEN`：用户禁止、权利边界、事实边界或高风险改变。

任何候选 Prompt 先通过约束保持门；丢失硬约束的候选直接淘汰，不参与加权平均。

## 2. 判断生产方法

| 条件 | 路线 | 核心输出 |
|---|---|---|
| 无素材，从零创造 | `text_to_video` | 单镜或分段生成 Prompt |
| 有稳定首帧/产品图/人物图 | `image_to_video` | 保持项、运动、相机、环境响应、结束状态 |
| 有多张图/视频/音频作为角色、动作、镜头或声音参考 | `reference_to_video` | 参考角色表、保留程度、目标时间线 |
| 有视频，只改局部 | `video_edit` | preserve / change only / time-location / forbidden |
| 从已有结尾继续 | `video_extend` | 最后确认状态、连续性、新事件、新结束状态 |
| 有真实素材，目标是成片 | `footage_edit` | EDL/时间线、素材入出点、字幕、旁白、现场声 |
| 有剧本或长故事 | `screenplay_to_shots` | 场景目标、角色 Bible、Shot List、逐镜 Prompt |
| 已有 Prompt，只需优化 | `prompt_optimize` | 精确版、表现版、评分、择优版 |
| 流程、图标、数据、文字 | `2d_motion_graphics` | 信息层级、布局、动画顺序、可编辑文字层 |
| 宣传 CG、概念剖面 | `aigc_3d_concept` | 几何外观、材质、镜头、概念边界 |
| 真实尺寸、装配、仿真 | `true_3d_handoff` | CAD/Blender/仿真任务说明，不生成伪结果 |
| 有参考视频，想提炼 Prompt 结构 | `reference_reverse` | 可迁移语法、镜头与动作机制，不逐字复刻 |

详细字段见 `references/method-schemas.md`。

## 3. 建立 VideoPromptIR

VideoPromptIR 是厂商无关的中间表示。必须先完成 IR，再渲染模型 Prompt；不得把一段“万能长 Prompt”直接复制给所有模型。

最低字段：

```text
constraint_ledger
production_method / input_mode / source_duration / target_duration / aspect
subject_anchor / environment
observable_action_beats
camera: shot_size / angle / one primary movement / viewer_effect
lighting_material_palette
audio: dialogue / foreground_sfx / ambience / score_policy
timeline / end_state
continuity_invariants
reference_roles / retention_policy
industrial physics ledger（适用时）
evidence boundary / unknowns
```

结构与示例见 `references/compiler-ir.md`。

## 4. 两个候选，不是十个随机变体

默认生成两个候选：

### Precision Candidate

最小充分、字面、约束优先。删除重复形容词，优先可执行性、物理和稳定结束状态。

### Expressive Candidate

在不改变事实的前提下，增加对观众体验真正有贡献的构图、节奏、光线、材料、声音和表演细节。不得增加第二个核心动作、冲突运镜或未经证实的故事事实。

两个候选都先过硬门槛，再按 `references/scoring-contract.md` 的维度打分。高分候选被选中；若两者优势互补，只允许合并不冲突字段，不做第三次无边界重写。

## 5. 单镜头通用语法

思考顺序：

```text
主体锚点
→ 一个主动作或状态变化
→ 摄像机位置与一个主要运动
→ 环境与空间关系
→ 光线、材质、色彩
→ 时间节拍
→ 环境/材料/人体反馈
→ 声音与台词
→ 稳定结束状态
→ 必须保持的不变量
```

动作预算：

| 有效时长 | 默认上限 |
|---|---|
| 3–5 秒 | 1 个主体动作 + 1 个相机行为 + 1 个环境响应 |
| 6–10 秒 | 1–2 个连续动作或 2 个节拍 |
| 11–15 秒 | 2–3 个节拍；必要时多镜头，但需连续性重锚 |
| 16–30 秒 | 分段或分镜，不用一个过载段落承担全部事件 |
| 30 秒以上 | 项目时间线 + 独立逐镜 Prompt + 后期组装 |

每个动作必须落在可见的结束状态，例如“她转身”改为“她缓慢转到侧面对着门，双脚停稳，视线仍留在对方身上”。

## 6. 工业级编译

工业 Prompt 先建立物理账本：

```text
实体与部件
几何和约束
接触/间隙/固定距离
能量或驱动力来源
轨迹、速度与方向
材料响应
环境响应
状态转移
最终不变量
证据边界
```

局部复核：每个工具—工件关系是否合理；全局复核：旋转、夹持、光线、声音、状态是否跨时间一致。

“真实工业感”不能靠更多火花。火花、熔池、切屑、粉尘、液体、热变色只在工艺和材料允许时出现，并与作用区域、方向和时间同步。

详见 `references/industrial-physics-ledger.md` 与 `references/industrial-language.md`。

## 7. 微表演编译

人物镜头按：

```text
触发事件
→ 呼吸/吞咽/肌肉紧张
→ 视线与眨眼
→ 眉眼、嘴角、下颌等细微变化
→ 肩颈、手指、胸口、重心和道具动作
→ 台词的触发词、停顿、速度与音量
→ 反应延迟
→ 相机与景别
→ 余韵和最后一口呼吸
```

不要用“悲伤、震惊、崩溃”替代可见行为。极近景不能安排夸张全身动作；关键台词后留出反应和余韵，不立即切走。

## 8. 参考素材与人物连续性

每个素材只能承担明确角色：

```text
Image 1：人物脸、发型和服装
Image 2：产品几何与表面
Video 1：表演或物体运动
Video 2：相机路径和剪辑节奏
Audio 1：声音音色或对白
```

“参考这个视频”不够；必须说明复制、部分保留、属性迁移还是弱参考。

多镜头人物默认采用：角色/产品 Reference Sheet → 场景锚帧 → 同一锁定参考喂给每个镜头 → 每镜只改变场景动作。Reddit 的锁定节点经验只作为低置信度社区线索，不能替代模型盲测。

详见 `references/character-consistency-workflow.md`。

## 9. 模型适配

先选择输入模式，再选择模型。只加载目标模型的适配文件。

当前已核验适配器（研究截止 2026-08-17）：

- MiniMax H3：`references/models/minimax-h3.md`
- MiniMax Hailuo 2.3：`references/models/hailuo-2.3.md`
- Seedance 2.0：`references/models/seedance-2.0.md`
- Kling VIDEO 3.0：`references/models/kling-video-3.0.md`
- Veo 3.1：`references/models/veo-3.1.md`
- Runway Gen-4.5：`references/models/runway-gen-4.5.md`
- Wan2.2：`references/models/wan2.2.md`
- LTX-2：`references/models/ltx-2.md`
- MiniMax Design 工作台：`references/models/minimax-design.md`

Sora 2 标记为 `RETIRED_NON_DEFAULT`（网页/应用已于 2026-04-26 停止，API 计划于 2026-09-24 停止）；无法在官方来源核实的 `Wan 2.6/2.7`、`Seedance 2.5` 等标签保留为 `VERIFY_AT_RUNTIME`。两类都不得作为默认事实，见 `references/models/retired-and-unknown.md`。

通用规则：

- 时长、比例、分辨率、变体数通常放在界面参数，不重复塞进正文；
- I2V 让图片负责外观，Prompt 重点写运动和变化；
- Reference 模式写素材关系和保留程度；
- Edit 模式写 preserve/change-only/时空范围；
- 厂商要求结构化 Schema 时严格按适配器输出；
- 模型名不等于能力，未知标签不通过字符串猜测。

## 10. 多维百分比评分

默认维度：

1. Intent Fidelity
2. Constraint Preservation
3. Method Fit
4. Visual Executability
5. Shot & Camera
6. Temporal Action Logic
7. Continuity & Identity
8. Model/Input Fit
9. Prompt Density
10. Audio/Dialogue
11. Industrial Physics（适用时）
12. Micro-performance（适用时）
13. Reference-role Clarity（适用时）
14. End State
15. Evidence Boundary & Repairability

评分先看硬门槛。丢硬约束、路由结构缺失、相机矛盾、虚假工程结论、参考角色不明等直接阻断。

必须同时输出证据标签：

```text
Structural specification score: XX%
Native-model generation evidence: NOT_RUN / PARTIAL / RUN
Human visual review: NOT_RUN / PARTIAL / RUN
External Verifier: NOT_RUN / PASS / FAIL / BLOCKED
```

结构分只衡量 Prompt 规格覆盖，不能宣称视频效果、审美或模型胜率。详见 `references/scoring-contract.md`。

## 11. 输出模式

### `copy`

```text
【制作判断】路线、输入模式、默认模型
【锁定与假设】仅列必要项
【可复制 Prompt】选中的模型渲染版
【界面参数】时长、比例、分辨率、变体数
【结构评分】多维百分比 + 证据状态
```

### `director`

1. 方法占比与 Creative Brief；
2. 约束账本；
3. 时间线 / Shot List / EDL；
4. 素材角色与连续性 Bible；
5. 每个缺失镜头的 IR 与模型 Prompt；
6. 2D/3D/声音/字幕方案；
7. 费用未知项、生成停止门和发布风险；
8. 结构评分和模型测试计划。

### `reverse`

输出全局风格指纹、镜头段落、动作、表演、相机、光线、声音、结束状态、可迁移语法和原创示例；不声称还原原始 Prompt，不逐字抄录长台词或屏幕文字。

### `repair`

```text
症状
高概率根因
必须保留
只修改一个变量
Delta Prompt
若仍失败的下一层回退
```

## 12. 生成后闭环

有生成结果时才进入：

```text
生成结果
→ 视觉/文本对齐/物理常识/连续性/声音评估
→ 定位最小根因
→ 只改变一个高杠杆变量
→ 再生成
→ 记录可迁移经验
```

不可见或未运行的结果标 `NOT_RUN`。不通过阅读 Prompt 自行宣布模型输出通过。

详见 `references/optimization-loop.md`。

## 13. 工具调用

路由：

```bash
python3 scripts/route_request.py --text '自然语言需求' --duration 8 --model 'Seedance 2.0' --format markdown
```

建立 IR：

```bash
python3 scripts/compile_request.py --text '自然语言需求' --duration 8 --model 'Seedance 2.0' --format json
```

结构验证：

```bash
python3 scripts/validate_output.py --file prompt.md --route image_to_video --preset industrial --duration 8 --model 'Runway Gen-4.5'
```

多维评分：

```bash
python3 scripts/score_prompt.py --file prompt.md --source-idea '原始需求' --route image_to_video --preset industrial --model 'Runway Gen-4.5'
```

参考视频抽帧：

```bash
python3 scripts/inspect_video.py /path/to/reference.mp4 --detail standard --output /tmp/reference-analysis
```

抽帧工具不做 OCR。Agent 用视觉能力分析联系表和关键帧。

## 14. 与现有系统的关系

本 Skill 独立安装为 `video-prompt-compiler`，不得覆盖现有 `prompt-compiler`。

推荐链路：

```text
自然语言
→ video-prompt-compiler 建立领域 IR 和候选
→ 可选 prompt-compiler 做通用措辞评测
→ 人工批准
→ 目标视频模型
→ 结果评估与最小 Delta 修复
```

`.ramify/` 保存本轮治理交接，但当前只是 `PROPOSED_NOT_COMMITTED`。正式外部 PASS 只能由独立 Verifier 产生。
