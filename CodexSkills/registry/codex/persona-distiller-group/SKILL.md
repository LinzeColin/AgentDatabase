---
name: persona-distiller-group
description: Assemble a working expert team from uniquely registered Persona Distiller products, load each member's actual reasoning payload (mental models, heuristics, hard boundaries, documented divergences), and produce a decision artifact whose every substantive line is traceable to a cited claim_id. Use when a task benefits from several complementary person-model specialists plus isolated review, adjudication, and counterevidence roles; also use to inspect, verify, rebuild, or govern the canonical persona delivery registry. Infer identity and scenario internally; never ask the caller to choose an identity.
---

# 人物蒸馏专家团队

本 Skill 是人物蒸馏产物的 canonical registry 与团队路由器。

## v0.0.0.7 为什么重写

使用者反馈「路由、产出、影响结论帮助都不显著」。查证后，根因不在提示词，在架构：

| 缺陷 | 证据 | 后果 |
|---|---|---|
| **团队拿不到推理内容** | `team-index.json` 每人只有约 24 条一行式元数据；**29 条 claim、心智模型、启发式、分歧图谱全部不在其中**。交付包是嵌套的（产物本体在 `runtime/` 内层 ZIP），**v0.0.0.6 没有任何脚本读过内层** | 团队是一份**演员表**，不是一组被载入的视角。人名进来了，实质没进来——这就是「影响结论不显著」的直接原因 |
| **分歧图谱从未被激活** | 每份产物都写有 `divergence-map.md`，组队时从未读取 | 库里最高价值的资产（人物之间的真实分歧）完全闲置 |
| **路由是字符串计数** | `occurrences()` 数子串命中次数，无语义、无能力对齐 | 选人近乎按关键词碰运气 |
| **时效信号反向工作** | `freshness_score()` 读 `research_cutoff`，86/91 都是「做研究的日期」；例外的 5 条是**卒年被误填**，导致真正该标已故的人反而拿低分 | 无法回答「这个团队能不能谈当前实践」 |

**v0.0.0.7 的修法是补上缺失的执行环节，不是加更长的提示词。**

## 先读

团队任务先读 [`CANONICAL-ROOT-ROUTE.md`](CANONICAL-ROOT-ROUTE.md)，再读机器索引 [`team-index.json`](team-index.json)。

登记、校验或迁移任务另读：

- [`references/delivery-package-standard.md`](references/delivery-package-standard.md)
- [`references/team-routing-policy.md`](references/team-routing-policy.md)
- [`references/team-output-contract.md`](references/team-output-contract.md) — **v0.0.0.7 新增，团队产出的硬性契约**

## 团队调用（六步，第 3 步是本次新增的硬门）

1. **从任务内部推断主身份与主场景**；不向用户展示身份菜单，也不要求编号或权重。

2. **从 `team-index.json` 选人**，只用 `readiness=ready` 且能力、场景、边界匹配者。选 5–20 人，默认 7–10 人。

   ```bash
   python3 scripts/route_team.py --task "<当前任务>"
   ```

3. **【硬门】载入 dossier —— 没有 dossier 不得开始推理。**

   ```bash
   python3 scripts/build_team_dossier.py --route-plan route-plan.json --output dossier.json
   ```

   该脚本打开每位成员交付包的**内层 runtime ZIP**，取出其：
   **心智模型 / 启发式 / 价值 / 工作方法 / 盲点 / 表面矛盾**（均带 `claim_id` 与证伪条件）、
   **硬边界与拒答模板**、**已标注的「不得写成」**、以及 **`claim_index`**（供引用核对）。
   同时跨成员比对各自的 `divergence-map.md`，抽出**组内真实分歧**。

   **dossier 里 `usage_contract` 的四条是硬约束：**
   - **每位人物专家的每一条实质贡献，必须引用其自身 `claim_index` 里的 `claim_id`；引用不出来的贡献视为未发生。**
   - **若 `divergences` 非空，最终产出必须显式呈现该分歧，不得抹平取中。**
   - **`hard_boundaries` 与 `refusal_template` 在生成前生效，不是事后过滤。**
   - **`known_distortions` 里标注的「不得写成」违反即为交付失败。**

4. **必须隔离三个控制角色**：至少 1 个独立复审、1 个最终裁判、1 个反证分析。
   同一人物、上下文或输出不得同时担任正向解决者与其复审／裁判。
   控制角色使用中立功能协议，**不伪装成登记人物**。

5. **正向团队各自形成方案 → 反证 → 复审 → 裁判**；裁判只看密封的候选结果与证据摘要。

6. **按 [`references/team-output-contract.md`](references/team-output-contract.md) 产出交付物。**
   **产出中不含任何 `claim_id` 引用的，判定为「团队未实际参与」，须重跑。**

登记人数或相关度不足时，明确返回 `insufficient_roster`，用中立功能角色补足流程，
**不得虚构人物专家或捏造「独立模型」**。

## 时效治理（v0.0.0.7 新增）

`subject_status` 与 `subject_active_through` 是**蒸馏时由作者显式填写**的字段，
**不得由脚本从自由文本推导**——该推导已被验证会给出错误答案
（用 `time_scope` 判定会把 1996 年去世的人标成在世；用卒年正则会抓错年份）。

- 未填写者一律标 `unauthored`，**不猜测**。
- `scripts/backfill_subject_status.py` 只**提议**候选值供作者核对，**不写入**。
- **组队时必须检查 `roster_composition`**：若全组无在世成员，而任务涉及当前实践、
  在用工具或近三年变化，**必须显式声明该组合的时效局限，或补充在世实践者**。

## 唯一登记

每个 canonical 人物只能存在于以下一个目录：

1. `材料建工师/` 2. `软件开发师/` 3. `艺术设计师/` 4. `创业经营师/`
5. `投资资本师/` 6. `思想教育师/` 7. `政治法律师/` 8. `客户营销师/`
9. `建造采购师/` 10. `财务合规师/` 11. `医疗护理师/` 12. `农林牧渔师/`

每个人物只归属其单一主身份对应的目录。重新分类必须移动唯一 canonical 记录，不能复制。

人物发布号属于人物蒸馏产物，按 canonical 人物独立使用 `0.0.0.1` 至 `0.0.0.999`，
只在成功登记时占号。人物 Skill 的运行不编号。

## 完整交付硬门

登记前必须通过 `scripts/verify_delivery.py` 与 `scripts/validate_group.py`，
且 `release --strict` 0 错 0 警。三对齐（team-index 产物数 == 磁盘 ZIP == git 跟踪 ZIP，
多版本产物按版本数计入）必须成立。

## 安全与真实性

- 产物是**基于证据的模型，不是本人**，非授权、不代表其当前观点。
- 在世人物尤其如此：**模型不会跟着本人改变主意**。
- 不复述、不评价针对任何人物的未经证实指控。
- 控制角色不得伪装成登记人物；不得虚构人物专家。
