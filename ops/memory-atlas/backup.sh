#!/usr/bin/env bash
set -euo pipefail
ENV_FILE=${MEMORY_ATLAS_ENV_FILE:-/srv/linze/secrets/memory-atlas.env}
AGENT_CURRENT=${MEMORY_ATLAS_AGENT_CURRENT:-/srv/linze/apps/agentdatabase/current}
PYTHON=${MEMORY_ATLAS_PYTHON:-/srv/linze/venvs/memory-atlas/bin/python}
[[ -r "$ENV_FILE" ]] || { echo "缺少受保护环境文件: $ENV_FILE" >&2; exit 78; }
[[ -d "$AGENT_CURRENT/OpenAIDatabase" ]] || { echo "AgentDatabase current 不可用: $AGENT_CURRENT" >&2; exit 66; }
[[ -x "$PYTHON" ]] || { echo "Memory Atlas Python 不可用: $PYTHON" >&2; exit 78; }
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
export PYTHONPATH="$AGENT_CURRENT"
export MEMORY_ATLAS_PRIVATE_DB_CLIENT=${MEMORY_ATLAS_PRIVATE_DB_CLIENT:-$AGENT_CURRENT/OpenAIDatabase/scripts/private_db_client.py}
export MEMORY_ATLAS_SOURCE_REGISTRY=${MEMORY_ATLAS_SOURCE_REGISTRY:-$AGENT_CURRENT/ops/memory-atlas/source-registry.json}
"$PYTHON" -B -m OpenAIDatabase.scripts.memory_atlas_private preflight >/dev/null
"$PYTHON" -B -m OpenAIDatabase.scripts.memory_atlas_private reconcile
"$PYTHON" -B -m OpenAIDatabase.scripts.memory_atlas_private backup-facts
