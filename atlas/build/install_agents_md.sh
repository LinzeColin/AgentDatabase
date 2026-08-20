#!/usr/bin/env bash
# install_agents_md.sh —— 把《开发经验沉淀契约》分发到每一个 agent 的指令文件。
#
# 为什么要一个分发器而不是手改五个文件：手改的后果是五份各自漂移，
# 半年后没人知道哪一份是对的。这里用一对哨兵注释把契约段圈起来，
# 每次分发**整段替换**，段外的内容一个字节都不动。
#
#   用法：bash atlas/build/install_agents_md.sh          # 分发（内容变了才写）
#         bash atlas/build/install_agents_md.sh --check  # 只检查漂移，不写
#
# 目标（缺哪个跳哪个，不报错，也绝不凭空造目录）：
#   ~/.claude/CLAUDE.md        Claude Code 全局记忆
#   ~/.codex/AGENTS.md         Codex 全局指令
#   ~/.dsh/AGENTS.md           DeepSeek Harness
#   ~/.kimi-code/AGENTS.md     Kimi Code
#   <工作区>/AGENTS.md         Kimi Code GUI 唯一可靠的通道
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"          # atlas/
SRC="$ROOT/AGENTS_CONTRACT.md"
WORKSPACE="${ATLAS_WORKSPACE:-$HOME/Documents/Codex/GithubProject}"
BEGIN='<!-- BEGIN memory-atlas:agent-contract v1 -->'
END='<!-- END memory-atlas:agent-contract v1 -->'
MODE="${1:-install}"

[ -f "$SRC" ] || { echo "✗ 找不到契约正文：$SRC"; exit 1; }
grep -q "$BEGIN" "$SRC" || { echo "✗ 契约正文缺起始哨兵，拒绝分发"; exit 1; }
grep -q "$END"   "$SRC" || { echo "✗ 契约正文缺结束哨兵，拒绝分发"; exit 1; }

TARGETS=(
  "$HOME/.claude/CLAUDE.md"
  "$HOME/.codex/AGENTS.md"
  "$HOME/.dsh/AGENTS.md"
  "$HOME/.kimi-code/AGENTS.md"
  "$WORKSPACE/AGENTS.md"
)

drift=0
for f in "${TARGETS[@]}"; do
  dir="$(dirname "$f")"
  [ -d "$dir" ] || { echo "－ 跳过 $f（$dir 不存在，这台机器没装它）"; continue; }

  if [ ! -f "$f" ]; then
    if [ "$MODE" = "--check" ]; then echo "✗ 缺文件 $f"; drift=1; continue; fi
    printf '# Agent 指令\n' > "$f"
  fi

  out="$(ATLAS_TGT="$f" ATLAS_SRC="$SRC" ATLAS_B="$BEGIN" ATLAS_E="$END" \
         ATLAS_MODE="$MODE" python3 "$ROOT/build/helpers/agents_block.py")"
  case "$out" in
    SAME)  [ "$MODE" = "--check" ] && echo "✓ $f" || echo "＝ 已最新 $f" ;;
    WROTE) echo "✓ 写入 $f" ;;
    DRIFT) echo "✗ 与契约不一致：$f"; drift=1 ;;
    *)     echo "✗ 未知返回「$out」：$f"; drift=1 ;;
  esac
done

if [ "$MODE" = "--check" ]; then
  if [ "$drift" = 0 ]; then echo "全部一致"; else
    echo "有文件与契约不一致 —— 跑一次不带 --check 的分发"; exit 1
  fi
fi
