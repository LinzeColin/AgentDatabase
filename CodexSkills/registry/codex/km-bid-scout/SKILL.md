---
name: km-bid-scout
description: 路由和编排 KM 工业搜标的只读发现、官方取证、语义、资格商务、独立审计、简报、DWS 生命周期与影子演化。用于选择最小子 Skill 链并保持停止门；不自动报名、付款、签章、提交、发消息或发布规则。
---

# KM Bid Scout Router

## 目标

仅加载当前 mode 需要的子 Skill，按结构化交接顺序执行。本 Skill 负责预检、路由、停止和 run summary，不重复领域决策。

## Canonical KMIDS 定位

- GitHub 仓库：`https://github.com/LinzeColin/KMOS`；
- 本机只读主树：`/Users/linzezhang/Documents/Codex/GithubProject/KMOS`；
- 业务项目名：`KMIDS`；当前实际目录名：`KM_IDSystem/`；
- 本机项目目录：`/Users/linzezhang/Documents/Codex/GithubProject/KMOS/KM_IDSystem`。

主树只用于核验。任何实现必须先读 `/Users/linzezhang/Documents/Codex/GithubProject/README.md` 的六条铁律，在 `GithubProject/_scratch/` 建独立 worktree。开工、写入前和结束时都要记录 HEAD/status；并发 fast-forward 后不得沿用旧快照。仓库 README/AGENTS/HANDOFF 与 Owner 当前声明冲突时，保留冲突证据并停止写入，不把路径存在等同于迁移治理已闭合。

## INPUT_SUFFICIENCY_PREFLIGHT

每次运行、每个 mode、任何直接子 Skill 调用都必须先读 `references/input_preflight_and_output_locator.md`，检查输入是否足以支持本次结论和外部访问。最低公共输入为：

```yaml
run_id: stable unique id
goal: one bounded outcome
mode: FULL_DISCOVERY | INCREMENTAL_DISCOVERY | EVIDENCE_BACKFILL | DEADLINE_WATCH | AUDIT_ONLY | BRIEF_ONLY | DINGTALK_SYNC | OUTCOME_WATCH | EVOLVE_SHADOW
triggered_at_raw: original trigger value
source_scope: explicit source ids or []
budget: explicit query/page/byte/time limits
external_effects: deny
delivery: local_artifacts | return_to_chat
output_root: absolute local path
```

`external_effects` 不是 `deny` 时立即停止。缺少 required 输入时，先返回编号化缺口和最小补充格式，不开始领域动作。只有 Owner 对具体字段明确授权 `OMIT / BOUNDED_ASSUMPTION / PUBLIC_SAFE_PLACEHOLDER / DEFER_PHASE`，且记录 scope、impact 和有效期后，才可在允许范围降级继续；不得静默省略或把一次授权沿用到后续运行。企业权限、来源条款、P0/P1 官方证据、唯一法律主体、独立审计、secret/PII 边界和 Owner 发布签收不可豁免。

## 路由

1. 先读 `references/routing.md`，只选当前 mode 的链。
2. 每到一步才加载相应 `$km-bid-*` Skill；不预先加载全部 8 个。
3. 每步验证子 Skill 的 `assets/output.schema.json`；无效输出不交给下游。
4. 记录输入/输出 hash、Skill/version、coverage、耗时、成本和错误；禁止记 secret 和未脱敏私有内容。
5. 子 Skill 返回 `coverage_degraded`、`NEEDS_EVIDENCE`、`DISAGREEMENT_REVIEW` 或权限阻塞时，按路由表降级/停止，不跳过。

## 全局硬门

- P0/P1 必须官方源、关键证据、唯一法律载体和独立审计。
- UNKNOWN 不自动进 P0/X；公告逐 lot；候选不等于最终中标。
- 来源失败必须显示 coverage，不得输出“零机会”伪成功。
- 没有可审计 offset/source zone 不得计算剩余时间。
- DWS 未通过 admin/profile/enterprise/group/version/help/schema 门时，不调用真实私有数据。
- EVOLVE 只产 proposal/shadow diff，不改 ACTIVE、Skill、holdout 或 evaluator。

## 输出

生成一个符合 `assets/output.schema.json` 的 `ScoutRunResult`：输入预检、运行状态、实际路由、每步状态、覆盖、阻塞、产物索引、输出定位和唯一下一步。

## OUTPUT_LOCATOR

最终面向 Owner 的回复必须逐一列出本次创建、更新或复用文件的绝对路径、状态和用途；没有生成文件时明确写“本次未生成文件”，并给出本次 `output_root`。绝对本机路径只进入 Owner 本地回复/本地运行证据，不得泄漏到外部消息、公开简报或公共 Git 产物。

```bash
python3 scripts/validate_output.py result.json
```
