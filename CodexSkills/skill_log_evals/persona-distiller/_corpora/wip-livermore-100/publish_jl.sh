#!/bin/bash
# Livermore #100 收口：发布门 → 打包 → 入库 → 重建视图 → 校验
# 用法：bash publish_jl.sh
set -euo pipefail
SP="$(cd "$(dirname "$0")" && pwd)"
# ★★ 2026-08-12：这里原本写死
#   SK=/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/...
#   **那个 worktree 已经不存在**，脚本直接跑必失败。改成从本文件位置往上推。
SK="$(cd "$SP/../../../../registry/codex/persona-distiller" && pwd)"
G="$SK/../persona-distiller-group"
T="$SP/jesse-livermore"

echo "=== 1/6 发布门（strict）==="
python3 "$SK/scripts/quality_check.py" "$T" --phase release --strict --write-report

echo "=== 2/6 入库前 products 基线 ==="
BEFORE=$(python3 -c "import json;print(len(json.load(open('$G/team-index.json',encoding='utf-8'))['products']))")
echo "products = $BEFORE"

echo "=== 3/6 打包 ==="
python3 "$SK/scripts/package_target.py" "$T" --output "$SP/dist/" --registry-root "$G"

echo "=== 4/6 入库 ==="
ZIP=$(ls -t "$SP"/dist/*.zip | head -1)
python3 "$SK/scripts/register_persona.py" "$ZIP" --registry-root "$G"

echo "=== 5/6 重建视图 ==="
python3 "$G/scripts/rebuild_team_views.py" --registry-root "$G"

echo "=== 6/6 校验 + 只增不减 ==="
python3 "$G/scripts/validate_group.py" --registry-root "$G"
python3 "$G/scripts/check_group_version_binding.py" --registry-root "$G"
AFTER=$(python3 -c "import json;print(len(json.load(open('$G/team-index.json',encoding='utf-8'))['products']))")
echo "products $BEFORE → $AFTER"
[ "$AFTER" -gt "$BEFORE" ] || { echo "✗✗ products 未增加，停"; exit 1; }
