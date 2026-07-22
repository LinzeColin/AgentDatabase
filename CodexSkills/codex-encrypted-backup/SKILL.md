---
name: codex-encrypted-backup
description: 在不创建本地自动脚本或 launchd 的前提下，将本机 Codex 的 memories、全部 sessions（含 archived）及受管 attachments 加密备份到 LinzeColin/AgentDatabase 的 GitHub Release。用于创建、执行、核验、保留或恢复验证这一备份通道。
---

# Codex 加密备份

## 目标与固定边界

这是一个**独立恢复、公开仓库仅存密文**的 Codex 备份通道。每次成功运行生成一份可单独恢复的累计快照；它不是依赖前一日备份的链式增量。

仅允许备份以下逻辑来源：

1. Codex memories；
2. 全部 Codex sessions，包含 archived；
3. Codex 受管 attachments。

绝不纳入：logs、配置、Skills、插件/模型缓存、Git 工作区、浏览器资料、Keychain、GitHub token、age 私钥、API/SSH 私钥、cookie、密码、恢复码或任何其他凭证。

禁止创建或安装本地自动脚本、launchd job、cron job、持久数据库或额外仓库。临时文件只能是本次运行产生的密文分片、最小 manifest、锁文件；不得落地明文压缩包。

## 唯一远端与统一密钥

每次运行先从 `LinzeColin/AgentDatabase` 的 `main` 读取：

- `OpenAIDatabase/config/storage/public_encrypted_backup_policy.json`
- `OpenAIDatabase/config/storage/raw_material_policy.json`

只有两份策略均存在、状态允许且仍含 owner 的 public-ciphertext-only 授权时才继续。固定校验条件如下：

- Release 仓库：`LinzeColin/AgentDatabase`（public）；
- 传输方式：GitHub Release asset only，绝不 Git tracked；
- `key_id`：`agentdatabase-public-backup-v1`；
- age recipient：`age1r0dxp7w0x0mx2tnleup5jad7ju7lrsyuewm2h9y4hss6le8f0pdslc0w50`；
- recipient SHA-256 fingerprint：`e92633e20b74672ff9e6d8a27db657e7fb770a4e47c12d107bcd9ab213e03be9`；
- 私钥只可经 macOS Keychain 或 owner secret manager 使用；不得输出、导出、复制或写成 identity file。

策略、recipient、fingerprint、仓库、授权范围任一漂移，或 age/私钥访问不可用时：`ACTION: STOP`，不上传、不发布、不删数据。

## 每次运行的 fail-closed 流程

### 0. 预检

依次确认：

- 没有同一通道正在运行（使用本次临时锁）；
- GitHub 当前身份对目标仓库具有创建 Release 与上传资产的权限；
- `age` 可用，且只能使用上述统一 recipient；
- 三类来源都已被当前 Codex runtime 明确定位、可读且完整。`sessions` 必须覆盖 archived；attachments 若没有独立根，必须由 runtime 明确证明它们已包含在 session 存储中；不能靠扫描整个 `.codex` 猜测；
- 可用磁盘空间足以容纳至多三份临时密文分片；
- 网络可用。

任一项失败即停止。本地原始资料、现有 Release、手工 Release、密钥及配置一律不改动。

### 1. 取数与快照稳定性

只读取上述三类逻辑来源。建立本次只在内存/临时阶段使用的完整性视图，避免在归档时来源发生变化；若来源在归档期变化，终止本轮或重新开始一次，绝不发布部分快照。

不得读取、展示或上传会话正文、附件名、绝对路径、目录清单或内容摘要。用户报告也不得泄露这些信息。

### 2. 流式加密与三附件上限

将快照压缩后立即用 age 加密，明文压缩流只能在管道中短暂存在，不能保存为文件。压缩格式为 gzip；密文后缀为 `.age`。

密文按策略的单分片上限切分；每个自动 Release **最多 3 个密文附件**。附件采用不包含来源信息的 opaque 名称，例如只含自动通道、备份 ID 和序号。

如果加密结果超过三份，必须停止并清除本次临时密文，不创建/不发布不完整 Release。不得为了通过上限排除旧 sessions、attachments 或 memories。

### 3. 草稿 Release 与最小 manifest

先创建草稿 Release，自动 tag 必须以前缀 `codex-auto-backup-` 开头。Release body 中写入最小 manifest；不得作为额外附件占用三附件额度。

最小 manifest 只能含：

- `backup_id`、`created_at`、`schema_version`；
- `key_id`、recipient fingerprint；
- 每个密文分片的序号、总数、SHA-256、大小；
- 固定逻辑来源集合 `codex_memories`、`codex_sessions`、`codex_attachments`。

不得含文件名、来源路径、会话内容、明文成员、密钥或解密步骤。

### 4. 远端校验与发布

将密文上传到草稿 Release 后，从 GitHub 远端重新读取每个资产的大小与 SHA-256 digest，并逐项和本地临时密文比对。

仅在全部一致时发布；否则保持不发布并清理本次草稿/临时密文，绝不影响已成功的 Release。无法取得或验证远端 SHA-256 也视为失败。

### 5. 保留策略

发布成功后，只枚举同时满足以下条件的自动 Release：

- tag 以 `codex-auto-backup-` 开头；
- manifest 标识本通道与 `agentdatabase-public-backup-v1`；
- 资产均为本通道的 `.age` 密文。

按创建时间仅保留最近 3 份，旧的自动 Release 与其自动 tag 一并删除。没有这个前缀/标识的人工首份或历史 Release 永远不碰。

### 6. 清理与恢复验证

成功的远端验证和发布完成后，只删除本次临时密文、临时 manifest 与锁文件。绝不删除本机 memories、sessions、attachments、密钥、GitHub 成功备份或 Codex 审计记录。

每月第一次成功的自动备份后，额外执行一次短暂恢复验证：下载刚发布的密文，使用 Keychain/secret-manager 私钥流式解密并检查归档完整性，然后立刻丢弃输出。不得持久保存明文；若验证失败，保留成功 Release 但报告 `恢复验证失败`，不得删除任何资料。

## 自动任务输出

首行必须是以下之一：`ACTION: ACT`、`ACTION: STOP`、`ACTION: ESCALATE`。

正常成功仅报告：成功状态、密文总大小、远端 SHA-256 校验结果、当前自动保留数、是否为非准点运行、是否执行月度恢复验证。失败时只报告阶段和安全原因；不输出密钥、会话内容、附件名、文件名或敏感路径。

## 不采用链式增量的原因

“只保留 3 份自动 Release”与“所有历史都可独立恢复”不能安全地与链式增量同时成立：删除基础快照会使后续增量不可恢复。因此本通道用每次合并成最新累计全量快照的方式实现无遗漏恢复；本机源从不自动删除。
