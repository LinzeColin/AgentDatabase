# Elihu Thomson 人物 Skill

> ⚠⚠ **这个人物没有入库（三轮用尽，记拒发）。**
> **看任何 delta 之前先读 [`DELTA-READ-ME-FIRST.md`](DELTA-READ-ME-FIRST.md)**——
> 这里有两个数：`+0.4084`（有 rubric）与 `−0.0859`（无 rubric），**只有后者能用**。

- 构建器：Persona Distiller `v0.0.0.5`
- 目录/Skill 名：`elihu-thomson`
- 构建主身份：材料建工师
- 主身份规范值：`technical-engineer`
- 主场景：未指定；每次任务自动推断
- 来源类型：`historical`
- 研究档位：`quick`
- 内部模型快照：`0.1.0-draft`
- 人物产物版本：打包并成功登记时按该人物独立分配 `0.0.0.1` 至 `0.0.0.999`
- 创建时间：2026-08-04T21:21:42Z

安装后直接调用本人物 Skill 并给出任务。身份分面和场景由 Skill 内部自动路由，用户不需要选择身份、编号或权重。例如：

```text
用他的方式审查这个技术方案
设计一套研究与教学计划
```

每次运行不分配版本号，也不强制修改聊天标签或输出文件名。产物版本只标识一次成功发布的人物 Skill 包。

安装：

```bash
python3 install.py
```

默认安装到 `~/.codex/skills/elihu-thomson`。研究工作区包含原始/受限材料；发布 ZIP 默认只带运行所需模型、审计摘要和安全更新模板。
