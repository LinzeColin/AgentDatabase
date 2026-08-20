#!/usr/bin/env bash
# sync_compound.sh —— 成果复利事件的收发。两个方向，一条事实链。
#
#   pull   私有仓 dev-notes/compounding-events/  →  本机收件箱
#   push   本机派生的投影                        →  私有仓 memory-atlas/compounding/latest.json
#
# 用法：
#   bash atlas/build/sync_compound.sh pull
#   bash atlas/build/sync_compound.sh push <projection.json>
#
# 为什么原始事件在私有仓、投影也在私有仓：事件里带 Owner 的原话与项目细节，
# 公开的 AgentDatabase 一个字都不能进。推送前硬校验目标仓可见性，
# 不是 PRIVATE 就拒绝 —— 和 push_brief.sh 同一道门。
set -euo pipefail

REPO="${BRIEF_REPO:-LinzeColin/Private-Database}"
BRANCH="${BRIEF_BRANCH:-dev-notes}"
EVENTS_PATH="Private-AgentDatabase/dev-notes/compounding-events"
PROJ_PATH="Private-AgentDatabase/memory-atlas/compounding/latest.json"
WORK="${ATLAS_WORK:-$HOME/.memory-atlas}"
INBOX="$WORK/compounding/events"
MODE="${1:-pull}"

command -v gh >/dev/null || {
  echo "⚠ PATH 里没有 gh —— 复利事件 本轮**没有推送**（不是没变化，是根本没跑）。"
  echo "  当前 PATH=$PATH"
  echo "  cron 是非交互 shell，gh 在 ~/.local/bin，见 bootstrap.sh 的 PATH 那一段。"
  exit 0
}

# 目标仓必须是私有的。这道门和 push_brief.sh 一样，不共用代码是为了任一处被改坏时另一处还在。
vis=$(gh repo view "$REPO" --json visibility -q .visibility 2>/dev/null || echo "")
[ "$vis" = "PRIVATE" ] || { echo "✗ 目标仓可见性为「${vis:-查不到}」，不是 PRIVATE，拒绝同步"; exit 1; }

case "$MODE" in
pull)
  mkdir -p "$INBOX"
  # 目录不存在是正常状态（还没有人产过事件），不是错误。
  # 目录不存在时 gh 会把错误 JSON 写到 stdout 再非零退出 ——
  # 只判空会把 {"message":"Not Found"} 当成清单喂给解析器。所以按退出码判。
  if ! listing=$(gh api "repos/$REPO/contents/$EVENTS_PATH?ref=$BRANCH" 2>/dev/null); then
    echo "复利事件：远端还没有 $EVENTS_PATH（尚无事件），本轮跳过"
    exit 0
  fi
  n=0
  while IFS=$'\t' read -r name sha; do
    [ -n "$name" ] || continue
    case "$name" in *.json) ;; *) continue ;; esac
    # 已经有同 sha 的就不重下。sha 存成同名 .sha 小文件，比比对内容便宜。
    if [ -f "$INBOX/$name.sha" ] && [ "$(cat "$INBOX/$name.sha")" = "$sha" ]; then continue; fi
    gh api "repos/$REPO/contents/$EVENTS_PATH/$name?ref=$BRANCH" --jq .content \
      | base64 -d > "$INBOX/$name"
    printf '%s' "$sha" > "$INBOX/$name.sha"
    n=$((n + 1))
  done < <(printf '%s' "$listing" | python3 -c '
import json, sys
try:
    rows = json.load(sys.stdin)
except Exception:
    rows = []
if not isinstance(rows, list):      # 单文件或错误对象都不是清单
    rows = []
for row in rows:
    if isinstance(row, dict) and row.get("type") == "file":
        print(row["name"] + "\t" + row["sha"])
')
  echo "复利事件：收件箱新增/更新 $n 个，共 $(find "$INBOX" -name '*.json' 2>/dev/null | wc -l | tr -d ' ') 个"
  ;;
push)
  src="${2:?要推的投影文件路径}"
  [ -f "$src" ] || { echo "✗ 找不到投影文件 $src"; exit 1; }
  b64=$(base64 < "$src" | tr -d '\n')
  sha=$(gh api "repos/$REPO/contents/$PROJ_PATH?ref=$BRANCH" --jq .sha 2>/dev/null || true)
  args=(-X PUT "repos/$REPO/contents/$PROJ_PATH"
        -f "message=memory-atlas: 复利投影 $(date -u +%FT%TZ)"
        -f "content=$b64" -f "branch=$BRANCH")
  [ -n "$sha" ] && args+=(-f "sha=$sha")
  gh api "${args[@]}" >/dev/null
  echo "复利投影已推送 → $REPO@$BRANCH/$PROJ_PATH"
  ;;
*)
  echo "用法：sync_compound.sh pull | push <file>"; exit 64 ;;
esac
