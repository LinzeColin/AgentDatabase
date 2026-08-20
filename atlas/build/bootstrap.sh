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

REPO="${ATLAS_REPO:-$HOME/Documents/Codex/GithubProject/AgentDatabase}"
WORK="${ATLAS_WORK:-$HOME/.memory-atlas}"
SRC="$WORK/src"

mkdir -p "$SRC"
# fetch 是主树上唯一允许的写操作（只动 .git 里的远端引用，不动工作区）
git -C "$REPO" fetch origin main --quiet
rm -rf "$SRC/atlas"
git -C "$REPO" archive origin/main atlas | tar -x -C "$SRC"

# --repo 指向主树：chatgpt 历史归档在 OpenAIDatabase/data/public_raw/chatgpt 下，只读取
ATLAS_WORK="$WORK" ATLAS_REPO_ROOT="$REPO" exec bash "$SRC/atlas/build/daily.sh"
