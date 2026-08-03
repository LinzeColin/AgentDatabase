# 一手来源、版本与访问边界

核验日期：2026-08-02。

## 核心竞品

- GEPA 官方仓库：https://github.com/gepa-ai/gepa
- GEPA v0.1.4 发布页：https://github.com/gepa-ai/gepa/releases/tag/v0.1.4
- GEPA 文档：https://gepa-ai.github.io/gepa/
- AutoResearch 官方仓库：https://github.com/karpathy/autoresearch
- Meta-Harness 官方仓库：https://github.com/stanford-iris-lab/meta-harness
- Meta-Harness 论文：https://arxiv.org/abs/2603.28052
- Promptfoo 官方仓库：https://github.com/promptfoo/promptfoo
- Promptfoo v0.121.20 发布页：https://github.com/promptfoo/promptfoo/releases/tag/0.121.20
- Promptfoo 文档：https://www.promptfoo.dev/docs/
- Promptfoo npm：https://www.npmjs.com/package/promptfoo

版本事实：GEPA v0.1.4 于 2026-07-15 发布；Promptfoo v0.121.20 发布说明日期为 2026-07-30、GitHub 页面显示于 2026-07-31 发布。npm 搜索摘要曾短暂仍显示 0.121.19，因此本包以官方 GitHub 最新 Release 0.121.20 为冻结依据。

## 扩展竞品

- DSPy：https://github.com/stanfordnlp/dspy
- TextGrad：https://github.com/zou-group/textgrad
- OPRO：https://github.com/google-deepmind/opro
- PromptWizard：https://github.com/microsoft/PromptWizard
- PromptAgent：https://github.com/XinyuanWangCS/PromptAgent
- SAMMO：https://github.com/microsoft/sammo
- Opik：https://github.com/comet-ml/opik
- MLflow：https://github.com/mlflow/mlflow

## 治理 Skill

- Skill 清单：https://github.com/LinzeColin/AgentDatabase/tree/main/CodexSkills/registry/codex/
- Teleiosis：https://github.com/LinzeColin/AgentDatabase/tree/main/CodexSkills/registry/codex/teleiosis
- Persona Distiller Group：https://github.com/LinzeColin/AgentDatabase/tree/main/CodexSkills/registry/codex/persona-distiller-group
- Verifier：https://github.com/LinzeColin/AgentDatabase/tree/main/CodexSkills/registry/codex/verifier
- Context Kernel：https://github.com/LinzeColin/AgentDatabase/tree/main/CodexSkills/registry/codex/context-kernel
- i-have-adhd：https://github.com/ayghri/i-have-adhd
- Grilling：https://github.com/mattpocock/skills/tree/main/skills/productivity/grilling

## 访问边界

本轮核验了可访问的公开仓库与用户上传的 v0.0.0.2。未获得登录授权的 GitHub Private 仓库无法访问，包内不声称已读取。人物蒸馏缺少 dossier，故采用角色分离同模型复审，不冒充原生专家团队执行。AutoResearch 与 Meta-Harness 的默认执行器是公开机制兼容适配，不冒充其官方原生实验。
