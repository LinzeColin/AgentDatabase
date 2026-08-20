#!/usr/bin/env bash
# bootstrap.sh —— cron 唯一直接调用的入口。装一份到 ~/.memory-atlas/run.sh 就不再动它。
#
# 为什么要这一层：主树 GithubProject/AgentDatabase 归「谁在开发谁占着」，
# 实测它可以领先 origin/main 63 个提交并带着未跟踪目录 —— 定时任务不能依赖它的状态，
# 更不许去清理它（那是别人没推的活）。所以这里用 `git archive origin/main atlas`
# 把代码从**远端 ref** 取出来，对主树只做 fetch，一个字节都不写。
#
# 装：cp atlas/build/bootstrap.sh ~/.memory-atlas/run.sh && chmod +x ~/.memory-atlas/run.sh
set -euo pipefail

# ── PATH：cron 是非交互 shell，不读 ~/.zshrc，拿到的是最小 PATH ──
#
# 实测（2026-08-20，本机）最小 PATH 下这两个**找不到**：
#   gh   → 真实位置 ~/.local/bin/gh
#   node → 真实位置 ~/.local/bin/node
#
# 后果不是「报错退出」，是**静默降级**，这才是真正危险的地方：
#   · node 缺 → extract.py 解 DSH 的 1937 场会话要走 helpers/dsh_reduce.js，直接哑掉
#   · gh  缺 → github.py 拿不到交付数据；push_brief.sh 与 sync_compound.sh
#              各自 `command -v gh || exit 0`，退出码 0 —— 日志里看着像成功
#
# 页面会照常渲染、照常显示「数据截至」，只是里面少了一大块 —— 没有任何一处会喊。
# 这正是 MEMORY 里「换机六类静默失效」那一条的形状。
# 同一台机器上 ~/.dsh/cron/daily-sync.sh 早就写了这一行，这里补上。
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO="${ATLAS_REPO:-$HOME/Documents/Codex/GithubProject/AgentDatabase}"
WORK="${ATLAS_WORK:-$HOME/.memory-atlas}"
SRC="$WORK/src"
LOG="$WORK/daily.log"

mkdir -p "$SRC" "$WORK"

# ── 起飞前检查：缺东西就**大声说**并中止，不许带着残缺跑完再报「完成」 ──
# 缺一半数据的一轮比不跑更坏：站点会用它覆盖上一轮的完整数据，
# 而顶部的「数据截至」还是新的 —— 看起来一切正常。
missing=()
for t in git tar python3 rsync ssh gh node; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
if [ ${#missing[@]} -gt 0 ]; then
  {
    echo "───── $(date -u +%FT%TZ) 起飞前检查未通过 ─────"
    echo "PATH 里找不到：${missing[*]}"
    echo "当前 PATH=$PATH"
    echo "本轮中止 —— 带着残缺跑完会用半份数据覆盖上一份完整数据，"
    echo "而页面顶部的「数据截至」照样是新的，等于静默丢数据。"
  } >>"$LOG"
  exit 1
fi

# fetch 是主树上唯一允许的写操作（只动 .git 里的远端引用，不动工作区）
git -C "$REPO" fetch origin main --quiet
rm -rf "$SRC/atlas"
git -C "$REPO" archive origin/main atlas | tar -x -C "$SRC"

# --repo 指向主树：chatgpt 历史归档在 OpenAIDatabase/data/public_raw/chatgpt 下，只读取
ATLAS_WORK="$WORK" ATLAS_REPO_ROOT="$REPO" exec bash "$SRC/atlas/build/daily.sh"
