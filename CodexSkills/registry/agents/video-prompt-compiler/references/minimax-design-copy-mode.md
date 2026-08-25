# MiniMax Design 复制模式

## 输出包

### 1. `MINIMAX_MASTER_PROMPT`

写给 MiniMax Design 主 Agent，包括：

- 项目目标；
- 目标受众与平台；
- 输入素材和角色；
- 真实素材、2D、AIGC、3D 的分工；
- 时间线；
- 每个生成节点的目标模型或能力；
- 生成前预算与停止门；
- 事实与权利边界；
- 最终交付。

### 2. `SHOT_PROMPTS`

每个生成镜头单独一块：

```text
V01 — 方法 — 推荐模型 — 可复制 Prompt — 界面参数 — 保持项
```

### 3. `EDIT_PROMPT`

用于已有素材时间线：素材编号、入点、出点、成片时间、裁切、字幕、声音。

### 4. `MODEL_USAGE_REQUEST`

要求 MiniMax Design 在生成前或生成后报告：

- 实际模型；
- 输入素材；
- 时长与分辨率；
- 变体数；
- 实际消耗；
- 是否采用。

无法读取的数据写 `UNKNOWN`。

## 自动 Router 边界

MiniMax Design 可以根据任务自动匹配模型，但本 Skill 不假定：

- 选择的所有模型都会运行；
- 第一条消息后模型池一定可以修改；
- credits 计算方式固定；
- Marketplace Skill 在所有地区可见。

因此总控 Prompt 应写：

```text
已启用模型只作为允许模型池。
每个节点只选择一个默认模型；只有明确标记 A/B 的节点才可使用两个模型。
任何媒体生成前先列出实际模型、输入、时长、变体和预计消耗，等待批准。
```

## 推荐输出语言

- MiniMax Design、Seedance、Kling：默认中文生成 Prompt；保留标准摄影术语。
- Veo/Runway：默认提供英文可复制 Prompt，并附一行中文意图；若 MiniMax Design 内部路由已验证中文表现良好，可只输出中文。
