#!/usr/bin/env bash
# deploy.sh —— 把 web/ 发到 VPS3 的 memory-atlas 容器。
#
# 线上结构（沿用既有的，不新发明）：
#   /srv/linze/apps/memory-atlas/releases/<UTC时间戳>-<内容哈希>/dist
#   current / previous 两个软链接 —— 回滚就是把 current 指回 previous
#
# 注意：容器把 current/dist 做成 bind mount，Docker 在**启动时**解析路径，
# 所以光翻软链接容器是看不见的，必须 recreate。上一次线上停在 8/9 就是这么卡住的。
set -euo pipefail

HOST="${ATLAS_HOST:-linze-vps3}"
APP=/srv/linze/apps/memory-atlas
COMPOSE=/srv/linze/apps/agentdatabase/current/ops/memory-atlas/docker-compose.yml
SRC="$(cd "${1:-$(dirname "$0")/../web}" && pwd)"   # 默认仓内 web/，也可传发布目录

[ -f "$SRC/index.html" ] || { echo "没有 web/index.html，先跑 build.py"; exit 1; }
[ -f "$SRC/atlas/atlas.json" ] || { echo "没有 atlas/atlas.json，先跑 build.py"; exit 1; }

HASH=$(find "$SRC" -type f -exec shasum -a 256 {} \; | sort | shasum -a 256 | cut -c1-12)
TS=$(date -u +%Y%m%dT%H%M%SZ)
REL="$APP/releases/$TS-$HASH"

# 探测清单在本地按发布目录现算，再作为字面量带进远端 —— 不手写主题名。
# 手写过一次：nebula 改名成 glass，探测清单漏改，自检把「文件没发上去」
# 读成了「一切正常」（nginx 的 try_files 把它兜底成首页并返回 200）。
PROBE="/ /core/app.js /core/select.js /vendor/gsap.min.js /vendor/three.module.min.js /atlas/atlas.json"
for th in $(ls "$SRC/themes" 2>/dev/null); do
  PROBE="$PROBE /themes/$th/shell.css /themes/$th/views/overview.js"
done

echo "→ 发布 $TS-$HASH"
ssh "$HOST" "mkdir -p '$REL/dist'"
rsync -az --delete -e ssh "$SRC/" "$HOST:$REL/dist/"

ssh "$HOST" bash -s <<REMOTE
set -euo pipefail
cd "$APP"
[ -L current ] && ln -sfn "\$(readlink current)" previous
ln -sfn "$REL" current
ln -sfn "$REL" candidate
docker compose -f "$COMPOSE" up -d --force-recreate memory-atlas-web >/dev/null 2>&1

# 容器不映射端口到主机（Traefik 走 docker 网络），所以要按容器 IP 探。
# 之前照着 127.0.0.1:8088 探，永远返回 000 —— 探测机制自己坏了却报"没起来"，
# 那是最坏的一种假信号：真实状态是"不确定"，不是"断了"。
IP=""
for i in \$(seq 1 20); do
  IP=\$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' memory-atlas-web 2>/dev/null | awk '{print \$1}')
  [ -n "\$IP" ] && curl -fsS -o /dev/null "http://\$IP:8088/healthz" 2>/dev/null && break
  IP=""
  sleep 0.5
done
[ -n "\$IP" ] || { echo "超时：20 次探测都没拿到健康的容器"; exit 1; }

echo "--- 源站自检（容器直连）---"
# 探测清单不再手写主题名 —— 改名一次就会漏一个，实测 nebula→glass 改完就漏了。
# 从发布目录里现算：每个主题的 shell.css 都要真的能取到。
for p in $PROBE; do
  code=\$(curl -s -o /dev/null -w '%{http_code}' "http://\$IP:8088\$p")
  size=\$(curl -s -o /dev/null -w '%{size_download}' "http://\$IP:8088\$p")
  ctype=\$(curl -s -o /dev/null -w '%{content_type}' "http://\$IP:8088\$p")
  # nginx 的 try_files 会把不存在的路径回落成 index.html：HTTP 200、内容却是首页。
  # 只看状态码会把「文件根本没发上去」读成「一切正常」——必须同时核对类型。
  flag=""
  case "\$p" in
    *.js)   [ "\${ctype#*javascript}" = "\$ctype" ] && flag="  ← 不是 JS，疑似回落到首页" ;;
    *.css)  [ "\${ctype#*css}" = "\$ctype" ] && flag="  ← 不是 CSS，疑似回落到首页" ;;
    *.json) [ "\${ctype#*json}" = "\$ctype" ] && flag="  ← 不是 JSON，疑似回落到首页" ;;
  esac
  printf '  %-32s HTTP %s  %s bytes  %s%s\n' "\$p" "\$code" "\$size" "\$ctype" "\$flag"
  [ -n "\$flag" ] && bad=1
done
[ "\${bad:-0}" = 1 ] && { echo "✗ 有资源没真正发上去（被 SPA 兜底掩盖）"; exit 1; }
echo "--- 边缘自检（经 Traefik，按真实 Host 路由）---"
# 容器刚 recreate，Traefik 要几秒才认到新后端，期间是 503。最多试 15 次，不写死等。
edge=000
for i in \$(seq 1 15); do
  edge=\$(curl -sk -o /dev/null -w '%{http_code}' -H 'Host: memoryatlas.linzezhang.com' https://127.0.0.1/)
  [ "\$edge" = 200 ] && break
  sleep 1
done
echo "  Traefik -> HTTP \$edge"
[ "\$edge" = 200 ] || { echo "✗ 边缘没通"; exit 1; }
echo "  release  = \$(readlink current)"
echo "  previous = \$(readlink previous)"
REMOTE

echo
echo "回滚（一条命令）："
echo "  ssh $HOST 'cd $APP && ln -sfn \$(readlink previous) current && docker compose -f $COMPOSE up -d --force-recreate memory-atlas-web'"
