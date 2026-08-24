# Notice and attribution

本项目为独立实现。研究阶段参考了多个公开项目的架构思想，但没有把任何第三方 Skill 的完整正文直接拼接为本项目。

可复用机制的主要来源包括：

- `wuwangzhang1216/DirectorSKILL`：导演、预演、关键帧、连续性、剪辑和失败修复框架；MIT。
- `CyberJ0605/cinematic-video-prompt-engineer-skill`：剧情诊断、微表演、声音、连续短片和结尾余韵；MIT。
- `Square-Zero-Labs/video-prompting-skill`：按模型与输入模式路由、H3/Seedance/Veo/Wan 适配层；Apache-2.0。
- `Alisa0808/vibe-creating-skill`：自然语言适配判断、信息密度检查、硬约束保留；MIT。
- `heloraai/Seedance2.0-Prompt-Optimizer-skill`：Seedance 场景模板与合规路由；MIT。
- `gracech0322-cmd/promptlab-image-video-to-prompt`：本地视频抽帧和参考视频反向提示词思路；MIT。
- `Square-Zero-Labs/video-prompting-skill`、`0xadvait/ai-video-skill`、`vericontext/vibeframe`：模型适配、生成后 QC/经验回流和生成前成本门控思路。
- Hugging Face 的 AutoT2VPrompt / VidProM：短输入扩写为视频 Prompt 的可行性证据；其非商业许可材料未被打包进本项目。

模型名称、商标和平台名称归各自权利人所有。本包不代表这些厂商，不承诺任何模型的具体 UI、价格或可用性长期不变。

导演风格模块只应学习高层方法，不得复制具体电影镜头、角色、台词或受版权保护的表达。本项目默认不用在世或已故导演姓名作为最终生成 Prompt 的必要组成，而优先转译为可观察的摄影、光线、表演和剪辑规则。
