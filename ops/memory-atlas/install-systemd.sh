#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) -eq 0 ]] || { echo '必须以 root 执行 systemd 安装'; exit 77; }
REPO_ROOT=${1:?用法: install-systemd.sh REPO_ROOT}
[[ -f "$REPO_ROOT/OpenAIDatabase/scripts/memory_atlas_private/requirements-memory-atlas-private.txt" ]] || { echo '缺少锁定依赖文件'; exit 66; }
SOURCE_DIR="$REPO_ROOT/ops/memory-atlas/systemd"
install -d -m 0750 -o ubuntu -g ubuntu /srv/linze/state/memory-atlas /srv/linze/work/memory-atlas /srv/linze/apps/memory-atlas/shared/data /srv/linze/venvs
install -d -m 0700 -o ubuntu -g ubuntu /srv/linze/state/memory-atlas/gh-config
python3 -m venv /srv/linze/venvs/memory-atlas
/srv/linze/venvs/memory-atlas/bin/python -m pip install --disable-pip-version-check --requirement "$REPO_ROOT/OpenAIDatabase/scripts/memory_atlas_private/requirements-memory-atlas-private.txt"
for unit in memory-atlas-api.service memory-atlas-api-proxy.service memory-atlas-api-proxy.socket memory-atlas-reconcile.service memory-atlas-reconcile.timer memory-atlas-selfheal.service memory-atlas-selfheal.timer memory-atlas-action-worker.service memory-atlas-action-worker.timer; do
  install -m 0644 "$SOURCE_DIR/$unit" "/etc/systemd/system/$unit"
done
install -m 0755 "$REPO_ROOT/ops/memory-atlas/memory-atlas-selfheal" /usr/local/bin/memory-atlas-selfheal
systemctl daemon-reload
systemctl enable memory-atlas-api.service memory-atlas-api-proxy.socket memory-atlas-reconcile.timer memory-atlas-selfheal.timer memory-atlas-action-worker.timer
printf '%s
' 'SYSTEMD_INSTALL_READY'
