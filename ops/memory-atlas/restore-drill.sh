#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "用法: $0 <Private-Database manifest path> <空的隔离恢复目录>" >&2
  exit 64
fi

MANIFEST_PATH=$1
DESTINATION=$2
ENV_FILE=${MEMORY_ATLAS_ENV_FILE:-/srv/linze/secrets/memory-atlas.env}
PYTHON=${MEMORY_ATLAS_PYTHON:-/srv/linze/venvs/memory-atlas/bin/python}
AGENT_CURRENT=${MEMORY_ATLAS_AGENT_CURRENT:-/srv/linze/apps/agentdatabase/current}

[[ -r "$ENV_FILE" ]] || { echo "缺少受保护环境文件: $ENV_FILE" >&2; exit 78; }
[[ -x "$PYTHON" ]] || { echo "缺少 Memory Atlas Python: $PYTHON" >&2; exit 78; }
[[ -d "$DESTINATION" ]] || { echo "隔离恢复目录不存在: $DESTINATION" >&2; exit 66; }
[[ -z "$(find "$DESTINATION" -mindepth 1 -maxdepth 1 -print -quit)" ]] || {
  echo "隔离恢复目录必须为空: $DESTINATION" >&2
  exit 73
}

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
export PYTHONPATH="$AGENT_CURRENT"
exec "$PYTHON" -B -m OpenAIDatabase.scripts.memory_atlas_private restore-drill \
  --manifest-path "$MANIFEST_PATH" \
  --destination "$DESTINATION"
