# Candidate Profiles

## 推荐直接吸收机制

- Square-Zero video-prompting-skill：模型目录与 H3 Schema；
- Vibe Creating：判断优先和硬约束保护；
- ai-video-skill：QC 联系表、经验回流和 Subject→Action→Camera→Style→Constraints；
- DirectorSKILL：Blocking before framing、时间线、连续性；
- Cinematic Video Prompt Engineer：微表演和台词余韵；
- RAPO/RAPO++：双分支择优与结果闭环；
- PhyT2V/PhyPrompt：物理规则和迭代复核；
- VideoFeedback2/VideoScore2：多维评估；
- PenShot/story-shot-agent：剧本→分镜→逐镜；
- FFMPEGA：自然语言→确定性编辑计划。

## 仅作为可选实验

- HF video-prompt-enhancer：重型 Adapter，偏旧/特定模型语料；
- VidProM：大规模研究数据，但含非商业许可边界；
- Reddit 锁定参考节点：低置信度社区经验，需盲测。

## 明确拒绝

- 用 stars 或营销 benchmark 代替任务适配；
- 把所有视频模型统一成一个万能 Prompt；
- 默认并行运行所有模型；
- 依赖未核验的版本名；
- 把结构评分写成成片质量或“通过率”。

## 许可证快速结论

- Apache-2.0：Square-Zero video-prompting-skill；HF video-prompt-enhancer 模型卡；
- MIT：DirectorSKILL、0xadvait ai-video-skill、Vibe Creating、Cinematic Video Prompt Engineer、PenShot；
- GPL-3.0：ComfyUI-FFMPEGA；其部分可选模型权重另含非商业条款；
- VidProM 含非商业组件；研究数据、论文代码和模型权重在直接引入前仍须逐项读取其具体条款。

本包只吸收方法并自行实现，没有直接复制上述第三方代码、Skill 正文或模型权重。
