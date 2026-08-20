Linze 打开一个网址，看懂自己这段时间的时间去了哪。

<!-- ↑ 第一行是北极星。**只有 Owner 能改**，agent 永远不改、不重写、不「优化表述」。 -->

# Memory Atlas

网址：https://memoryatlas.linzezhang.com　（Cloudflare Access 保护，只有 Owner 能进）

**杀期：2026-09-20。** 到期 Owner 一次都没主动想打开就杀掉，不复活、不重构。

## 三个文件就是全部

```
atlas/build/extract.py   本机 7 个来源 → 一行一会话（增量，未改动的文件直接复用）
atlas/build/build.py     会话 → atlas.json + 每天一个明细文件
atlas/build/deploy.sh    发到 VPS3 的 memory-atlas 容器，翻软链接，自检，给回滚命令
atlas/web/               页面本体。没有构建步骤，没有依赖，没有 CDN。
```

## 每天怎么跑

无人值守，一条命令，本机 cron 每天 03:10 自动跑：

```bash
bash atlas/build/daily.sh
```

它依次做：抽取 → 聚合 → 发布 → 自检。产物写在 `~/.memory-atlas/`，**绝不写进仓**
（仓是 PUBLIC，产物含对话原文）。

- 首跑 ~50 秒；之后每天 ~15 秒（未改动的文件直接复用缓存）
- 运行期**不调用任何模型**，纯标准库，零 token，零 agent
- 缓存键带解析器指纹：改了解析逻辑，缓存自动失效，不会静默产出陈旧数据
- 上一轮没跑完就跳过本轮，**不等待、不重试**；锁超过 3 小时视为残留自动清掉

### 为什么这一段跑在本机而不是 VPS

源数据（`~/.claude`、`~/.codex`、`~/.kimi-code` …）只存在于这台机器上。
但**服务端不依赖本机**：笔记本关着，站点照常提供上一次的数据，
页面顶部自己标出「数据截至」，超过 48 小时会显示**断了**并在正文上方挂告警 ——
流水线停了看得见，不会静默陈旧。

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
