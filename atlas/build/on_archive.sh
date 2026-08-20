#!/usr/bin/env bash
# on_archive.sh —— 归档行为触发时（上下文压缩 / 会话结束）刷新开发经验沉淀。
#
# 装：cp atlas/build/on_archive.sh ~/.memory-atlas/on-archive.sh && chmod +x
# 由 Claude Code 的 PreCompact/SessionEnd 与 Codex 的 SessionStart(compact) 调用。
#
# 三条硬性约束，都是被咬过才写下来的：
# 1. **必须快。** 钩子挡在 agent 前面。这里只做「复审已抽好的会话 + 上传」，
#    不重跑抽取（抽取要 60 秒，放钩子里等于每次压缩都卡一分钟）。
# 2. **必须去抖。** 一次长会话可能压缩很多次。30 分钟内跑过就跳过。
# 3. **必须有上限。** 绝不写没有终止条件的等待；整体超时直接放弃。
set -euo pipefail

WORK="${ATLAS_WORK:-$HOME/.memory-atlas}"
SRC="$WORK/src/atlas"
STAMP="$WORK/.on-archive.stamp"
LOG="$WORK/on-archive.log"
DEBOUNCE_MIN="${ATLAS_ARCHIVE_DEBOUNCE_MIN:-30}"

[ -d "$SRC/build" ] || exit 0            # 还没 bootstrap 过，静默退出
[ -d "$WORK/out" ] || exit 0             # 还没有抽取产物，没什么可复审的

# 去抖
if [ -f "$STAMP" ] && [ -z "$(find "$STAMP" -maxdepth 0 -mmin +"$DEBOUNCE_MIN" 2>/dev/null)" ]; then
  exit 0
fi
touch "$STAMP"

{
  echo "───── $(date -u +%FT%TZ) 归档触发 ─────"
  python3 "$SRC/build/sediment.py" --sessions "$WORK/out" --out "$WORK/brief" --web "$WORK/web"
  bash "$SRC/build/push_brief.sh" "$WORK/brief"
} >>"$LOG" 2>&1 || echo "$(date -u +%FT%TZ) 归档刷新失败" >>"$LOG"

tail -n 400 "$LOG" >"$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
