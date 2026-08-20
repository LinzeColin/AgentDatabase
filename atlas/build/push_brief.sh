#!/usr/bin/env bash
# push_brief.sh —— 把 AGENT_BRIEF 推到私有仓，作为**权威副本**。
#
# 为什么必须是私有仓：里面有 Owner 的对话原话（实测含姓名、手机号、客户报价）。
# AgentDatabase 是 PUBLIC，一个字都不能进。
#
# 为什么要有权威副本：Owner 的要求是「让 agent 都知道这个信息」。
# 本机文件只有这台机器上的 agent 能看到；放进仓里，任何有仓权限的 agent
# 一条 gh 命令就能取到，不需要先认识这台机器。
set -euo pipefail

SRC="${1:?用法: push_brief.sh <brief 目录>}"
REPO="${BRIEF_REPO:-LinzeColin/Private-Database}"
# Owner 指定的沉淀地址是 dev-notes **分支**（tree/dev-notes/...），不是 main 上的同名目录。
# 两处都写等于两条事实链 —— 统一到这一条，main 上那份留一行指路。
BRANCH="${BRIEF_BRANCH:-dev-notes}"
DEST="${BRIEF_PATH:-Private-AgentDatabase/dev-notes}"

[ -f "$SRC/AGENT_BRIEF.md" ] || { echo "没有 AGENT_BRIEF.md"; exit 1; }
command -v gh >/dev/null || { echo "没有 gh"; exit 1; }

vis=$(gh repo view "$REPO" --json visibility -q .visibility 2>/dev/null || echo "")
# 硬门：目标仓必须是私有。判不出来也算不通过 ——
# 「查不到可见性」和「是私有」在这里绝不能当成同一件事。
[ "$vis" = "PRIVATE" ] || { echo "✗ 目标仓可见性为「${vis:-查不到}」，不是 PRIVATE，拒绝推送"; exit 1; }

put() {
  local file="$1" path="$2"
  local sha
  sha=$(gh api "repos/$REPO/contents/$path?ref=$BRANCH" --jq .sha 2>/dev/null || true)
  local args=(-X PUT "repos/$REPO/contents/$path"
              -f "message=chore(agent-brief): 每日沉淀 $(date -u +%F)"
              -f "branch=$BRANCH"
              -f "content=$(base64 < "$file" | tr -d '\n')")
  [ -n "$sha" ] && args+=(-f "sha=$sha")
  gh api "${args[@]}" --jq '.content.path' >/dev/null
}

put "$SRC/AGENT_BRIEF.md"   "$DEST/AGENT_BRIEF.md"
put "$SRC/agent_brief.json" "$DEST/agent_brief.json"
put "$SRC/README.md"        "$DEST/README.md"
echo "AGENT_BRIEF 已推送 → $REPO/$DEST/"
