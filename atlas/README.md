# Memory Atlas

**Linze 打开一个网址，看懂自己这段时间的时间去了哪。**

网址：https://memoryatlas.linzezhang.com　（Cloudflare Access 保护，只有 Owner 能进）

## 三个文件就是全部

```
atlas/build/extract.py   本机 7 个来源 → 一行一会话（增量，未改动的文件直接复用）
atlas/build/build.py     会话 → atlas.json + 每天一个明细文件
atlas/build/deploy.sh    发到 VPS3 的 memory-atlas 容器，翻软链接，自检，给回滚命令
atlas/web/               页面本体。没有构建步骤，没有依赖，没有 CDN。
```

## 每天怎么跑

```bash
python3 atlas/build/extract.py --out atlas/out --repo .
python3 atlas/build/build.py   --sessions atlas/out --out atlas/web
bash    atlas/build/deploy.sh
```

全量首跑约 45 秒；之后每天增量 **0.2 秒**（只解析当天新写的文件）。
运行期**不调用任何模型**，纯标准库，零 token。

## 回滚

```bash
ssh linze-vps3 'cd /srv/linze/apps/memory-atlas && ln -sfn $(readlink previous) current && \
  docker compose -f /srv/linze/apps/agentdatabase/current/ops/memory-atlas/docker-compose.yml \
  up -d --force-recreate memory-atlas-web'
```

## 几条踩过的坑，别再踩

- **线上不是 Pages。** `memoryatlas.linzezhang.com` → CF Tunnel → Traefik → `memory-atlas-web` 容器。
  往 Cloudflare Pages 部署到不了这个域名（Pages 那边的自定义域是 `deactivated`）。
- **容器 bind mount 在启动时解析路径。** 只翻 `current` 软链接容器看不见，必须 `--force-recreate`。
  线上停在 8/9 就是卡在这一步。
- **nginx 对 `/data/` 一律 404**（原设计：私有快照不当静态文件发）。数据放 `/atlas/`。
- **容器不映射端口到主机。** 健康探测要按容器 IP，照着 `127.0.0.1:8088` 探永远是 000。
- **CSP 是 `script-src 'self'`：** 没有内联脚本、没有 CDN。3D 是手写的，不是 three.js。
