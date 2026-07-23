---
name: skill-github-sync
description: 把本机全部 Skill（Codex 用户、Codex 系统/OpenAI 官方、Claude/Anthropic、Agents 通用目录）全量镜像备份到 GitHub 公开仓 LinzeColin/AgentDatabase 的 CodexSkills/registry/，重建人读与机器读索引，提交并推送。当用户要求备份 skill、同步 skill 到 GitHub、更新 skill 索引，或由每周定时自动化触发时使用。推送前有凭据硬门，扫到密钥即中止。
---

# Skill 同步到 GitHub

把本机所有 skill 全量镜像到 `LinzeColin/AgentDatabase` 的
`CodexSkills/registry/`，让任何 LLM 都能通过公网按需检索和加载。

**同步方向永远是「本机 → 仓库」。** 本机增删改什么，仓库就跟着变成什么，包括删除。

## 覆盖的来源

| 目录 | 本机路径 | 内容 |
|---|---|---|
| `registry/codex/` | `~/.codex/skills/` | 自建、下载、从 GitHub 装的 |
| `registry/codex-system/` | `~/.codex/skills/.system/` | OpenAI 官方随 Codex 分发（Apache-2.0，LICENSE 原样保留） |
| `registry/claude/` | `~/.claude/skills/` | Anthropic 侧 |
| `registry/agents/` | `~/.agents/skills/` | 跨工具通用目录 |

多个来源存在重名（例如 `dws` 三处都有，`agent-reach` 两处内容还不同），所以按来源分目录，**不拍平**。

## 执行步骤

```bash
REPO=~/Documents/Codex/GithubProject/AgentDatabase
WT=~/Documents/Codex/GithubProject/_scratch/agentdb-skill-sync-auto

# 0. 清理上次可能残留的工作树（幂等）
git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true
git -C "$REPO" worktree prune
git -C "$REPO" branch -D chore/skill-sync-auto 2>/dev/null || true

# 1. 取最新，开隔离工作树（主树保持只读且干净）
git -C "$REPO" fetch origin --quiet
git -C "$REPO" worktree add "$WT" -b chore/skill-sync-auto origin/main
git -C "$WT" sparse-checkout add CodexSkills

# 2. 同步（盘点 → 镜像 → 凭据门 → 重建索引 → 提交 → 推送）
python3 "$WT/CodexSkills/sync_skills.py"
RC=$?

# 3. 收尾：主树跟进，工作树与分支回收
git -C "$REPO" worktree remove --force "$WT" 2>/dev/null || true
git -C "$REPO" worktree prune
git -C "$REPO" branch -D chore/skill-sync-auto 2>/dev/null || true
git -C "$REPO" pull --ff-only origin main --quiet
git -C "$REPO" gc --quiet
exit $RC
```

`sync_skills.py` 会依次做：盘点四个来源 → 镜像并传播删除 → **凭据硬门** → 重建 `index.json` 与 `README.md` → 有变化才提交 → 推送。

## 硬规则

1. **凭据门不可绕过。** 目标仓是**公开**的。脚本扫到 OpenAI/Anthropic 密钥、GitHub 令牌、AWS 密钥、Slack 令牌、私钥、JWT、Google 密钥中任何一种，就**中止且不推送**，并列出命中文件。此时的正确处理是**从那个 skill 里删掉凭据**（改用环境变量或外部配置），再重跑；**绝不加 `--force` 或改脚本绕过**。
2. **不改 skill 内容。** 本流程只做镜像，不编辑、不重命名、不「顺手优化」任何 skill。
3. **删除要传播。** 本机删掉的 skill，镜像里也要删掉 —— 目标是「仓库永远等于本机现状」，不是「只增不减的堆积」。
4. **主树只读。** 一律在 `_scratch/` 下的工作树里操作，结束后回收工作树与临时分支，别把仓库留在脏状态。
5. **无变化不提交。** 本机与仓库一致时不产生空提交。
6. **收尾必须干净。** 结束时仓库只剩 `main` 一条分支、0 未决合并请求、0 待办事项、本地无遗留工作树。

## 报告什么

跑完向用户汇报：

- 本次新增 / 修改 / 删除了哪些 skill（按 `来源/名字` 列出）
- 当前总数：多少份实例、多少个不同名字
- 凭据扫描结果（命中就是**必须处理的阻塞**，不是提示）
- 提交号与索引地址
- 若因超过 95MB 跳过了文件，逐个列出 —— 不要默默吞掉

**不要声称推送成功而不核实。** 以 `git push` 的实际返回为准。

## 手动用法

```bash
python3 <仓库>/CodexSkills/sync_skills.py --dry-run   # 只看差异，不写不推
python3 <仓库>/CodexSkills/sync_skills.py --no-push   # 提交但不推
python3 <仓库>/CodexSkills/sync_skills.py             # 完整同步
```
