# 多维百分比比较矩阵

> `Goal Fit` 是针对“自然语言→电影级/工业级/多模型可安装 Skill”的机制覆盖估计，不是原生模型盲测。证据置信度、许可证状态、真实生成和独立验收分开显示。

## 结果总览

| 项目 | Goal Fit | Evidence confidence | License | Native-model evidence | 角色/结论 |
|---|---:|---:|---|---|---|
| Video Prompt Compiler v0.0.0.2 | 96.4% | 76% | MIT; package-owned implementation | NOT_RUN | recommended integrated base |
| DirectorSKILL | 85.7% | 65% | MIT | UNKNOWN | director and shot-planning donor |
| 0xadvait/ai-video-skill | 83.7% | 62% | MIT | SELF_REPORTED_WORKFLOW | QC and end-to-end workflow donor |
| Square-Zero-Labs/video-prompting-skill | 80.5% | 68% | Apache-2.0 | NOT_DISCLOSED | model adapter and H3 schema donor |
| PenShot / story-shot-agent | 77.1% | 68% | MIT | NOT_DISCLOSED | screenplay-to-shot donor |
| Cinematic Video Prompt Engineer Skill | 74.8% | 55% | MIT | NOT_DISCLOSED | micro-performance donor |
| Alisa0808/vibe-creating-skill | 70.6% | 62% | MIT; NOTICE/attribution applies to the ported methodology | NOT_DISCLOSED | judgment-first natural-language donor |
| FFMPEGA natural-language editing | 54.4% | 60% | GPL-3.0 code; optional model weights include non-commercial terms | OPEN_SOURCE_WORKFLOW | deterministic edit-plan donor |
| PhyT2V / PhyPrompt | 52.6% | 92% | Research code/paper; verify each repository before direct code reuse | PAPER_EXPERIMENTS | physics-ledger and refinement donor |
| RAPO / RAPO++ | 49.9% | 94% | Research paper/code; verify repository terms before direct code reuse | PAPER_EXPERIMENTS | dual-branch optimizer donor |
| VideoFeedback2 / VideoScore2 | 40.2% | 95% | Dataset/model terms require component-level review | DATASET_AND_MODEL_EVALUATION | evaluation-dimension donor |
| HF video-prompt-enhancer | 36.5% | 52% | Apache-2.0 model card | MODEL_CARD_ONLY | optional local enhancer; not core |
| VidProM dataset | 19.1% | 90% | Mixed dataset provenance; includes non-commercial components | LARGE_DATASET | research corpus only |

## 评分维度与权重

- `natural_language_compilation`: 12%
- `production_method_routing`: 10%
- `cinematic_directing`: 10%
- `model_adapter_depth`: 12%
- `continuity_reference_control`: 8%
- `industrial_physics`: 10%
- `editing_storyboard_breadth`: 8%
- `qc_delta_repair`: 10%
- `current_model_freshness`: 8%
- `installability_runtime_burden`: 7%
- `license_reuse_clarity`: 5%

## 默认整合结论

不原样采用单一项目。以 Video Prompt Compiler v0.0.0.2 为集成底座，吸收：Vibe Creating 的判断优先、Square-Zero 的模型适配器、ai-video-skill 的 QC、RAPO 的双候选择优、PhyT2V 的物理复核、VideoFeedback2 的评估维度、PenShot 的剧本分镜和 FFMPEGA 的确定性编辑路由。

当前包的高 Goal Fit 只表示设计覆盖；真实视频模型与外部 Verifier 仍为 `NOT_RUN`。许可证列只说明公开仓库/模型卡的已见状态；本包没有直接拷贝第三方代码或权重。完整逐维数据见 `comparison_matrix.csv` / `comparison_matrix.json`。
