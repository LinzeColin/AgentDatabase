# Evidence Ledger — 2026-08-17

## 证据分级

- **A**：官方模型文档/发布、同行评审论文、官方研究代码；
- **B**：公开可检查的 Skill/仓库/数据集卡；
- **C**：作者自述、未独立复现的示例或模型卡；
- **D**：Reddit/论坛社区案例，只生成假设，不形成事实结论。

## 模型官方来源

| 来源 | 等级 | 提取机制 | 使用边界 |
|---|---|---|---|
| MiniMax H3 发布与 HF 指南 | A | 多模态上下文关系、Base/Full-reference Schema、音频与参考角色 | 发布方能力声明仍需实际账户和结果验证 |
| MiniMax Hailuo API 文档 | A | Hailuo 2.3 T2V/I2V、Fast I2V、参数与 2,000 字符 Prompt 限制 | 只约束官方 API，不推断第三方封装 |
| Seedance 2.0 官方发布 | A | 四模态输入、Reference/Edit/Extend、音画、多镜头、物理与运动控制 | “行业领先”等宣传性表述不进入本包评分 |
| Kling VIDEO 3.0 官方 Quickstart | A | 元素绑定、Multi-shot、音频/对白的适配方向 | 具体账户功能运行时核验 |
| Google Veo 3.1 模型页 | A | 电影级、4K、同步音频和复杂相机定位 | 产品/API参数可能变化，界面优先 |
| Runway Gen-4.5 官方指南 | A | T2V 描述视觉+运动；I2V 几乎只写运动；2–10秒当前规格 | 不把建议长度扩展为跨模型硬规则 |
| Wan2.2 官方仓库 | A/B | 当前官方开源版本与输入路线 | 不把 vendor 的 2.6/2.7 标签自动映射为官方版本 |
| LTX-2 官方仓库 | A/B | 逐时序单段落、字面准确、200词以内 | 本地运行不作为默认依赖 |
| OpenAI Sora discontinuation 说明 | A | 网页/应用 2026-04-26 停止；API 计划 2026-09-24 停止 | 标记非默认，不把剩余 API surface 推断为网页可用性 |

## Prompt 优化与评估研究

| 来源 | 等级 | 机制 | 本包整合 |
|---|---|---|---|
| RAPO, CVPR 2025 | A | 检索增强分支 + 指令重写分支，择优 Prompt | Precision / Expressive 双候选与硬门槛择优；不引入模型依赖 |
| RAPO++ | A/C | 生成结果驱动的样本级闭环优化 | 生成后 Observe–Diagnose–Delta 流程 |
| PhyT2V, CVPR 2025 | A | 物理规则导向的迭代、自反思/step-back | 工业物理账本与局部—全局复核；论文效果数字不当作本包结果 |
| PhyPrompt 2026 | A/C | RL 物理 Prompt 优化 | 作为未来模型测试路线，不作为运行依赖 |
| VideoFeedback2 / VideoScore2 | A/B | 27,168 视频；视觉质量、文本对齐、物理/常识三维人类反馈 | 评价维度与失败诊断框架 |
| VidProM | A/B | 1.67M prompts / 6.69M videos | 研究语料参考；含 CC BY-NC 组件，不复制进商业运行包 |
| HF video-prompt-enhancer | C | Qwen2.5-14B adapter 将简单 Prompt 扩写 | 可选实验，不作为核心；模型较重且 Sora 取向明显 |

## GitHub Skills / Projects

| 项目 | 等级 | 公开许可状态 | 可复用机制 | 未直接复用原因 |
|---|---|---|---|---|
| Square-Zero video-prompting-skill | B | Apache-2.0 | 模型适配器目录、H3 Schema、参数与正文分离、I2V 聚焦运动 | 本包自行实现，避免整体复制和版本耦合 |
| 0xadvait ai-video-skill | B/C | MIT | Subject→Action→Camera→Style→Constraints、联系表 QC、经验回流 | 端到端 API/服务依赖不符合默认只编译 |
| Vibe Creating Prompt | B/C | MIT；另有方法归属/NOTICE | S/E/I 判断优先、硬约束保留、不是所有任务都 vibe 化 | 工业与精确剪辑路线需独立保留 |
| DirectorSKILL | B/C | MIT | Blocking before framing、Shot List、连续性、失败修复 | 作为导演机制来源，不作为唯一底座 |
| Cinematic Video Prompt Engineer | C | MIT | 呼吸、视线、反应延迟、余韵 | 模型/工业/剪辑覆盖不足 |
| PenShot / story-shot-agent | B/C | MIT | 剧本→场景→分镜→逐镜 Prompt 与连续性 | 本包抽象工作流，不引入其 LangGraph/RAG 栈 |
| ComfyUI-FFMPEGA | B/C | GPL-3.0；部分可选权重为非商业条款 | 自然语言编辑→确定性 FFmpeg/时间线 | 只整合“能确定编辑就不重生成”的路由原则，不引入代码或权重 |

## Reddit

2026 年 7 月 r/AIAssisted 的一个帖子报告：同一固定参考节点与 pinned seed 跨镜复用，比每镜重新 Prompt 更能维持人物脸和服装；评论同时指出长镜头仍漂移、LoRA 在某些场景更强。等级 **D**。本包只把它转成“锁定参考工作流”的待验证假设，不写成模型普遍规律。

## 原始链接

- https://www.minimax.io/blog/minimax-h3
- https://platform.minimax.io/docs/release-notes/apis
- https://platform.minimax.io/docs/api-reference/video-generation-i2v
- https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0
- https://app.klingai.com/global/quickstart/kling-video-3-0
- https://ai.google.dev/gemini-api/docs/models/veo-3.1-generate-preview
- https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5
- https://github.com/Wan-Video/Wan2.2
- https://github.com/Lightricks/LTX-2
- https://help.openai.com/en/articles/20001152-what-to-know-about-the-sora-discontinuation
- https://mlanthology.org/cvpr/2025/gao2025cvpr-devil/
- https://github.com/pittisl/PhyT2V
- https://huggingface.co/datasets/TIGER-Lab/VideoFeedback2
- https://huggingface.co/datasets/WenhaoWang/VidProM
- https://huggingface.co/dariakryvosheieva/video-prompt-enhancer
- https://github.com/Square-Zero-Labs/video-prompting-skill
- https://github.com/0xadvait/ai-video-skill
- https://github.com/Alisa0808/vibe-creating-skill
- https://github.com/wuwangzhang1216/DirectorSKILL
- https://github.com/CyberJ0605/cinematic-video-prompt-engineer-skill
- https://github.com/neopen/story-shot-agent
- https://github.com/AEmotionStudio/ComfyUI-FFMPEGA
- https://www.reddit.com/r/AIAssisted/comments/1uo42d0/whats_actually_holding_a_character_consistent/
