---
name: prompt-compiler
description: 将原始 Prompt、代码、Agent 架构、配置或其他文本工件编译为可追溯、可回滚、可独立验收的冠军候选。GEPA、AutoResearch、Meta-Harness、Promptfoo 同时作为同层竞品和可路由下层执行器；Prompt Compiler 只有在全部必选竞品实际运行、全部冻结维度逐项排名第一、总体第一、独立最终测试、回归、红队、Promptfoo 与外部证据均通过时才允许发布。适用于提示词优化、Agent Skill 优化、竞品同场评测、版本记忆和防退化发布门禁。
license: MIT
compatibility: Python 3.10–3.14；正式运行需要任务模型、不同身份的独立终审模型、官方 GEPA 0.1.4、官方 Promptfoo 0.121.20（Node.js 22.22.0 以上，推荐 Node.js 24），以及可验证的 AutoResearch/MetaHarness 官方或受控 Git 工作区与真实外部命令。
metadata:
  version: v0.0.0.4
  language: zh-CN
  display_name_zh: 提示词编译器｜全维冠军版
  champion_contract: strict-first-on-every-frozen-dimension
---

# 提示词编译器｜全维冠军版

## 用户只需要这样用

安装后在 Codex、Claude Code 或兼容 Agent 中输入：

```text
$prompt-compiler
优化下面的原始工件。原文不可覆盖；GEPA、AutoResearch、Meta-Harness、Promptfoo 既要作为同层竞品参加同场竞技，也要作为可路由下层执行器。只有 Prompt Compiler 在全部冻结维度和总体上均排名第一，且独立终审、回归、红队和发布门全部通过，才允许输出获胜版本。

【原始工件】
在这里粘贴
```

Agent 负责建项目、保存历史、生成或导入案例、封印数据、运行候选搜索、独立评测、出中文报告和回滚。用户只需决定真实授权、成本上限、业务真值和最终发布责任。

## Pursuing Goal

在不改变原始目标、硬约束、权限、数据边界和输出合同的前提下，把全部已登记竞品同时作为同层对手与下层能力源，通过总预算守恒的自适应路由、逐维差距修复、单变更实验、严格独立复测和失败关闭发布门，使 Prompt Compiler 只在“每个冻结维度第一、总体第一、无硬失败、证据完整”时发布。

## 五路径冻结合同

1. `GEPA`、`Promptfoo optimize`、`AutoResearch loop`、`MetaHarness harness search` 是四条互相独立的原生优化路径，也是同层必选竞品。
2. `prompt_compiler omni` 是第五条路径，但不是第五个本地模拟优化器；它只做两阶段总编排：Stage 1 收集四条原生路径，Stage 2 进行逐维差距合成。
3. GEPA 只允许官方 `gepa.optimize_anything`；Promptfoo 只允许官方 CLI；AutoResearch 和 MetaHarness 只允许在隔离工作区中执行真实外部命令。
4. AutoResearch、MetaHarness、Omni 不得使用本地同名模拟；GEPA、Promptfoo 不得使用兼容回退。任何缺项都必须 `BLOCKED`。
5. Promptfoo 的获胜提示词只能从官方输出的精确 `Best prompt` 区段提取；候选建议模型与被优化目标模型分别记录为不同逻辑角色。
6. 四条原生路径全部通过且各自产生候选后，Omni 才能进入第二阶段；不允许用删除竞品、改名、补造候选或复用种子冒充路径通过。

## 不可协商冠军合同

1. **双重身份**：GEPA、AutoResearch、Meta-Harness、Promptfoo 必须同时保留 `same_layer_competitor` 和 `routable_executor` 两个角色。吸收能力不取消同层竞争；参加竞争也不妨碍能力路由。
2. **逐维第一**：内置 15 个维度和项目评分器自动发现的附加维度全部冻结。任一必选竞品在任一维度可分离领先，状态为 `CHAMPION_REJECTED`。
3. **并列规则**：低于 100% 的并列不算第一；只有有界指标双方都达到 100% 时，才允许记为不可超越的共同第一。
4. **证据不完整即阻塞**：竞品缺跑、维度缺值、预算不一致、最终测试不同、身份不独立、置信区间重叠或证据哈希不一致，均为 `CHAMPION_NOT_PROVEN`，不得发布。
5. **总体与最弱项同时优先**：候选选择顺序为硬安全、所有维度最低值、最弱任务切片、总体效果、稳定性、长度；平均分不能掩盖灾难性短板。
6. **总预算守恒**：所有同层竞品与 Prompt Compiler 自身共享一个冻结总预算。禁止把同一预算复制给每个引擎后再宣称等预算。
7. **先探测再路由**：每个必选执行器获得最低探测预算，剩余预算依据当前维度差距、任务剖面和能力先验分配；Prompt Compiler 的合成轮次也计入总预算。
8. **单变更、实测、保留或回滚**：每轮只允许一个可归因变化；独立验证后只有稳健排序键改善才保留，否则立即回滚到父候选。
9. **原文不可变**：每次输入逐字保存、永不覆盖；版本、链接、阈值、路径、硬约束和禁止项进入受保护字面量合同。
10. **最终测试密封**：训练、验证、最终测试、回归和红队分离。最终候选名单与哈希冻结后才允许打开最终测试。
11. **独立终审**：任务模型与最终评委必须是不同稳定身份。仅改角色名称、不改模型或执行身份，不算独立。
12. **外部自报分无效**：竞品只能提交候选。其自报分数、最佳结果或“通过”结论不能替代统一预言机和独立终审。
13. **真实门禁**：Promptfoo 双版对照、旧案例回归、固定红队、Promptfoo 官方红队、真实外部验收和 CI 独立重读均通过后才允许正式发布。
14. **动态维度同权**：项目自定义评分器或语义评委输出的规范化维度会在最终测试前自动冻结；不能通过不报告弱项规避冠军门。
15. **结论有证据边界**：`CHAMPION_PASS` 只覆盖报告中封印的数据、模型身份、版本、统一预言机、总预算、重复次数和竞品注册表。它不是脱离条件的永久口号。

## 内置冠军维度

| 维度 | 含义 | 主要证据 |
|---|---|---|
| overall | 总体效果 | 最终测试逐行得分 |
| worst_case | 最差案例 | 每案例重复结果的最差值 |
| weakest_slice | 最弱任务切片 | 逐任务均值中的最低值 |
| stability | 稳定性 | 重复结果偏离均值的程度 |
| correctness | 正确性 | 语义评委或业务评分器 |
| coverage | 覆盖完整性 | 断言、要求覆盖和评分维度 |
| executability | 可执行性 | 真实执行结果和评分器 |
| security | 安全性 | 泄漏、越权和语义安全判定 |
| efficiency | 工件效率 | 长度与冗余惩罚 |
| oracle | 业务预言机一致性 | 确定性、结构化和业务真值 |
| hard_safety | 硬安全 | 硬失败必须为零 |
| regression | 回归保持 | 旧案例独立复测 |
| redteam | 红队韧性 | 固定红队与官方红队 |
| cost_efficiency | 成本效率代理 | 优先真实 Token；否则明确标记字符代理 |
| latency_efficiency | 延迟效率代理 | 同环境实际耗时 |

附加维度名称必须满足 `[A-Za-z][A-Za-z0-9_.-]{0,63}`，每行返回 0–1 且越高越好。缺失即阻塞。

## 执行顺序

### 1. 初始化并保存原始工件

```bash
python3 -B scripts/prompt_compiler.py init \
  --project <工作目录> \
  --source-file <原始文件> \
  --objective-text "不改变目标和硬约束，提升全部冻结维度并在同场竞技中逐项第一。"
```

新输入只追加：

```bash
python3 -B scripts/prompt_compiler.py ingest --project <工作目录> --source-file <新输入文件>
```

### 2. 检查环境

```bash
python3 -B scripts/prompt_compiler.py self-test
python3 -B scripts/prompt_compiler.py doctor --probe
```

缺隔离运行环境时：

```bash
python3 -B scripts/prompt_compiler.py bootstrap
```

### 3. 准备并封印数据

优先导入授权、脱敏的真实案例。材料不足可生成临时案例打通链路，但不能据此形成正式业务冠军结论。

```bash
python3 -B scripts/prompt_compiler.py generate-cases --project <工作目录> --count 16
python3 -B scripts/prompt_compiler.py validate --project <工作目录>
python3 -B scripts/prompt_compiler.py seal --project <工作目录>
```

### 4. 绑定原生路径并运行双角色同场竞技

AutoResearch 与 MetaHarness 必须先配置官方或可验证工作区、真实命令和候选制品路径。可通过 `config.json` 的 `optimization.native_engines` 配置，也可使用环境变量：

```text
PROMPT_COMPILER_AUTORESEARCH_WORKSPACE
PROMPT_COMPILER_AUTORESEARCH_COMMAND
PROMPT_COMPILER_AUTORESEARCH_CANDIDATE_PATH
PROMPT_COMPILER_META_HARNESS_WORKSPACE
PROMPT_COMPILER_META_HARNESS_COMMAND
PROMPT_COMPILER_META_HARNESS_CANDIDATE_PATH
PROMPT_COMPILER_PROMPTFOO_SUGGESTIONS_IDENTITY
```

然后运行：

```bash
python3 -B scripts/prompt_compiler.py optimize \
  --project <工作目录> \
  --preset quick \
  --engines gepa,autoresearch,meta_harness,promptfoo,prompt_compiler
```

运行时会自动补齐竞品注册表中 `required=true` 的竞品。任一原生路径未配置、执行失败、没有候选或修改了合同外文件，Omni 都会失败关闭。

### 5. 独立发布裁决

```bash
python3 -B scripts/prompt_compiler.py external-acceptance \
  --output <工作目录>/reports/external_acceptance.json
python3 -B scripts/prompt_compiler.py ci-gate --project <工作目录>
```

CI 不信任报告里的单一布尔值，而会重新读取冠军证据文件、复算哈希、逐竞品逐维检查状态，并独立读取 Promptfoo 与外部验收证据。

## 四个机器状态

- `CHAMPION_PASS`：全部必选竞品、全部冻结维度均满足严格第一或 100% 上限共同第一，允许进入后续发布门。
- `CHAMPION_NOT_PROVEN`：存在缺跑、缺值、低于满分并列、统计未分离或证据不完整；保持原版。
- `CHAMPION_REJECTED`：至少一个竞品在至少一个冻结维度形成可分离优势；继续针对差距优化。
- `PASS`：冠军门之外，独立终审、回归、红队、Promptfoo、外部证据和发布合同全部通过。

## 历史、版本与文脉中枢

每次原始输入和获胜候选都会生成 ChatGPT、Codex、Claude、Gemini 四个目标版本，记录父子关系、时间、SHA-256 和回滚点。稳定交接文件：

```text
<项目>/.ramify/KERNEL.md
<项目>/.ramify/DECISIONS.md
<项目>/.ramify/HANDOFF.md
<项目>/.ramify/MANIFEST.json
```

完整正文和不可变历史位于：

```text
<项目>/.prompt-compiler/history.sqlite3
<项目>/.prompt-compiler/history/<记录编号>/content.md
```

## 失败处理

- 任一必选原生路径未产生候选：阻塞 Omni 和冠军声明，不以本地模拟、复制种子或删除竞品解决。
- 任一冻结维度缺证据：阻塞，不自动降低维度权重。
- 竞品在某维度领先：保留原版和差距证据，把后续预算定向到该维度及其能力最强执行器。
- 低于满分并列：继续优化或增加区分度更高的案例，不能宣布第一。
- 旧案例退化、红队失败或硬安全失败：立即退回，不以更高平均分抵消。
- 缺独立终审或真实外部证据：可继续研究候选，但禁止正式发布。
- 达到成本上限：停止新增调用，保留全部失败路径、证据和回滚点。

## 适用边界

本 Skill 负责文本工件和 Agent Skill 的优化、对比、版本治理与证据门禁。代码、Agent 架构和配置的正式冠军结果必须接入目标项目真实编译、测试、业务预言机和运行环境；通用文字评分不能代替领域验收。核心四路径没有本地兼容执行器；未验证的原生路径必须阻塞，不能冒充官方成功。
