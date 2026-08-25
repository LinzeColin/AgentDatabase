# Video Prompt Compiler v0.0.0.2

**自然语言 → 电影级、工业级、模型兼容的视频 Prompt 编译器。**

它不是摄影形容词库，而是一个小型编译系统：先把自然语言拆成事实、约束、动作、相机、时间、声音、物理和连续性，再按目标视频模型渲染。

## 核心架构

```text
Natural language
→ Constraint Ledger
→ Production Route
→ VideoPromptIR
→ Precision Candidate / Expressive Candidate
→ Hard Gates + 15-dimensional scoring
→ Model Renderer
→ Structural Validation
→ Generate–Observe–Diagnose–Delta loop
```

## 主要路线

T2V、I2V、Reference-to-Video、Video Edit、Extend、真实素材剪辑/EDL、剧本转分镜、2D Motion Graphics、AIGC 3D Concept、真实 CAD/Blender handoff、参考视频反向拆解、失败 Prompt 最小修复。

## 当前模型适配器

MiniMax H3、Hailuo 2.3、Seedance 2.0、Kling VIDEO 3.0、Veo 3.1、Runway Gen-4.5、Wan2.2、LTX-2，以及 MiniMax Design 项目级桥接。过时或无法从官方来源确认的版本标签不会被自动当作事实。

## 安装

```bash
python3 scripts/install.py --target codex
python3 scripts/install.py --target claude
python3 scripts/install.py --target both
```

## 边界

默认不调用收费媒体模型；不把 AIGC 冒充真实证据；不编造工业事实；不把本地结构分当作真实视频质量分；不覆盖现有 `prompt-compiler`。

完整使用说明见 `README_FIRST.md`、`QUICKSTART.md` 与 `SKILL.md`。
