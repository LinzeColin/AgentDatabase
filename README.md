# AgentDatabase

Archived Codex agent history, migrated off this Mac to keep local storage 
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

“人物蒸馏 Skill”登记在
[`CodexSkills/registry/codex/persona-distiller/`](CodexSkills/registry/codex/persona-distiller/)。
它生成的每个人物产物必须且只能登记到对应的一个身份目录；多重身份只进入
`多重身份/`，不得在不同身份下重复登记。完整发布 ZIP、canonical 登记与生成索引保存在
[`产物登记/`](CodexSkills/registry/codex/persona-distiller/产物登记/)。
