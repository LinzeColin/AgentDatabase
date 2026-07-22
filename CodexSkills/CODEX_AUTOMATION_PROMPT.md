# Codex 自动化提示词：每周备份全部 Skill 到 GitHub

在 Codex 里新建一个 automation，把下面「———」之间的**全部内容**作为提示词粘进去。

**调度：** 每周日 03:00（Australia/Sydney）
**Cron：** `0 3 * * 0`

———

调用 `skill-github-sync` 这个 skill，把本机全部 Skill 全量备份到 GitHub。

这是无人值守的每周定时任务。请严格按 skill 里写的步骤执行，不要自己发挥。

## 要做什么

把本机四个来源的 skill 全量镜像到 `LinzeColin/AgentDatabase` 的 `CodexSkills/`：

- `~/.codex/skills/` → `codex/`（自建、下载、从 GitHub 装的）
- `~/.codex/skills/.system/` → `codex-system/`（OpenAI 官方，Apache-2.0）
- `~/.claude/skills/` → `claude/`（Anthropic 侧）
- `~/.agents/skills/` → `agents/`（跨工具通用目录）

目标是**仓库永远等于本机现状**：本机新增的要上去，改过的要更新，**删掉的也要从仓库删掉**。不是只增不减的堆积。

## 怎么做

在 `~/Documents/Codex/GithubProject/AgentDatabase` 上开一个隔离工作树（主树保持只读干净），在里面跑：

```bash
python3 CodexSkills/sync_skills.py
```

脚本自己会依次完成：盘点四个来源 → 镜像并传播删除 → 凭据硬门 → 重建 `index.json` 与 `README.md` → 有变化才提交 → 推送。跑完回收工作树与临时分支，主树 `git pull --ff-only`，然后 `git gc`（**不要加 `--prune=now`**）。

完整命令见 `skill-github-sync` 的 SKILL.md，照抄即可。

## 三条不能破的规矩

1. **凭据门不可绕过。** 目标仓是**公开**的。脚本一旦扫到密钥、令牌或私钥就会中止且不推送。这时**不要**加 `--force`、不要改脚本、不要删检查。正确做法是把凭据从那个 skill 里清掉（改用环境变量或外部配置），下次再同步；然后**在报告里明确告诉我是哪个文件命中了什么**。

2. **不改 skill 内容。** 这是备份任务，只做镜像。不要编辑、重命名、重排或「顺手优化」任何 skill。

3. **不要谎报成功。** 以 `git push` 的实际结果为准。没推上去就说没推上去，连同原因一起报。

## 报告格式

跑完给我一份简短报告：

```
本周 Skill 备份 · <日期>

变化：新增 N 个 / 修改 N 个 / 删除 N 个
  + codex/<名字>
  ~ agents/<名字>
  - claude/<名字>
（无变化就写「本机与仓库一致，无变化」）

当前规模：X 份实例 / Y 个不同名字
凭据扫描：0 命中  ← 命中的话这里要列全，并说明已中止
提交：<短 SHA>  或  未产生提交
索引：https://github.com/LinzeColin/AgentDatabase/blob/main/CodexSkills/README.md
仓库卫生：分支 / 未决合并请求 / 待办事项 各是多少
```

如果因为文件超过 95MB 被跳过，逐个列出来，不要默默吞掉。

———

## 建完之后

**先手动跑一次**，确认三件事：

1. 能正常推送（首次会有较多新增，属正常）；
2. 凭据扫描是 0 命中；
3. 收尾后仓库只剩 `main` 一条分支、0 未决合并请求、0 待办事项。

确认无误后，它每周日凌晨自动跑，你不用管。

## 平时怎么用

日常正常增删改 skill 就行，**不用手动同步** —— 周日会自动兜住。

想立刻同步（比如刚写完一个重要 skill）就直接说：

```
用 skill-github-sync 同步一下
```

想先看看会改什么而不真的推：

```bash
python3 ~/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/sync_skills.py --dry-run
```

## 一个提醒

因为是每周跑，如果周中删了一个 skill 又后悔，在同步发生前本机恢复即可；同步之后仓库那份也会被删掉，但 **Git 历史仍然留着**，可以用 `git log --diff-filter=D -- CodexSkills/<来源>/<名字>` 找回。
