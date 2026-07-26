# AgentDatabase

Agent 数据仓。三个活动范围：
- **`OpenAIDatabase/`** —— Codex / OpenAI 会话与记忆运行时（记忆图谱、个性化、行为智能）。
- **`MemoryAtlas/`** —— 记忆图谱发布件。
- **`CodexSkills/`** —— 本机 Codex Skill 的仓库镜像与治理登记（人物蒸馏等）。

以及从旧 Mac 迁出的历史归档（作为 Release 资产，不占本地存储）。

## 📦 数据落地政策（长期有效 · 自运行分仓治理）

**本仓存代码/治理/技能登记与已发布制品；开发中新产生的长期/业务/运行时数据不入本仓**，
一律写私有仓 `LinzeColin/Private-Database`：Agent 会话/记忆数据 → `Private-AgentDatabase/`。
用各仓内 `private_db_client.py` 免 clone 读写（`ingest/get/list/verify`）；Private-Database 禁止 `git clone`；派生/临时物走 `.gitignore`。
> ⛔ 唯一待闭环：`OpenAIDatabase/data/` 仍是活运行记忆、尚未迁走，详见 [`OpenAIDatabase/MIGRATION_MANDATE.md`](OpenAIDatabase/MIGRATION_MANDATE.md)（SDK cutover 完成前不得删）。

## Contents

Large archives are stored as **release assets** (not in git), because GitHub
rejects any file over 100 MB inside a repository. See the release
[`old-mac-20260630`](../../releases/tag/old-mac-20260630).

| Asset | Size | Contents |
|---|---|---|
| `codex-token-history-migration-pack-20260630.tar.gz` | 1.08 GiB | Token-usage history migration pack from the old Mac: 408 session rollouts (2026-06-02 → 2026-06-30), sqlite log databases, `~/.codex` home state |
| `old-mac-session-history-20260630.tar.gz` | 800 MiB | Old-Mac Codex session history export |
| `current-mac-session-history-20260630.tar.gz` | 36.5 MiB | Current-Mac Codex session history export, as of 2026-06-30 |
| `codex-numeric-token-usage-export-20260630.tar.gz` | 147 KiB | Numeric token-usage export (CSV/JSON) |

The 408 session rollouts in the migration pack exist **only** here — they were never
imported into `~/.codex/sessions` on this machine.

## Restore

    gh release download old-mac-20260630 --repo LinzeColin/AgentDatabase
    shasum -a 256 -c checksums.txt
    tar -xzf codex-token-history-migration-pack-20260630.tar.gz

## Integrity

`checksums.txt` holds the sha256 of every asset, computed before upload.

## CodexSkills

本机 Codex Skill 的仓库镜像与治理登记。索引：[`CodexSkills/README.md`](CodexSkills/README.md)（人读）、[`CodexSkills/index.json`](CodexSkills/index.json)（机器读，供 Agent 按需检索单个 skill，不要整仓 clone）。

“人物蒸馏 Skill”构建器位于
[`CodexSkills/registry/codex/persona-distiller/`](CodexSkills/registry/codex/persona-distiller/)，
唯一 canonical 登记与专家团队 Skill 位于平级的
[`CodexSkills/registry/codex/persona-distiller-group/`](CodexSkills/registry/codex/persona-distiller-group/)。
它生成的每个人物产物必须且只能登记到对应的一个身份目录；每个人物只进入一个
单一主身份目录，不再使用“多重身份”目录。十二个目录固定为 `材料建工师/`、
`软件开发师/`、`艺术设计师/`、`创业经营师/`、`投资资本师/`、`思想教育师/`、
`政治法律师/`、`客户营销师/`、`建造采购师/`、`财务合规师/`、`医疗护理师/`、
`农林牧渔师/`；每个版本只保存一个全量完整交付 ZIP，机器索引为
[`team-index.json`](CodexSkills/registry/codex/persona-distiller-group/team-index.json)，
最高优先级团队路由为
[`CANONICAL-ROOT-ROUTE.md`](CodexSkills/registry/codex/persona-distiller-group/CANONICAL-ROOT-ROUTE.md)。
身份目录只用于唯一登记；安装后用户直接调用对应人物 Skill，内部自动路由身份与场景，
不要求用户选择身份。每个 canonical 人物的成功蒸馏产物独立使用
`0.0.0.1` 至 `0.0.0.999` 连续版本；单次运行没有版本编号。
