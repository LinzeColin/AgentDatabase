Linze 打开一个网址，看懂自己这段时间的时间去了哪。

<!-- ↑ 第一行是北极星。**只有 Owner 能改**，agent 永远不改、不重写、不「优化表述」。 -->

# Memory Atlas

网址：https://memoryatlas.linzezhang.com　（Cloudflare Access 保护，只有 Owner 能进）

**杀期：2026-09-20。** 到期 Owner 一次都没主动想打开就杀掉，不复活、不重构。

## 结构

```
atlas/build/extract.py   本机 7 个来源 → 一行一会话（增量，未改动的文件直接复用）
atlas/build/metrics.py   token/缓存、经济指数、耦合网络三个派生块
atlas/build/build.py     会话 → atlas.json + 每天一个明细文件
atlas/build/deploy.sh    发到 VPS3，翻软链接，自检，给回滚命令
atlas/build/daily.sh     每日流水线；bootstrap.sh 是 cron 唯一入口
atlas/web/
  core/app.js     启动 / 主题切换 / 路由
  core/select.js  纯数据选择器（**不产出任何标记、不含任何样式**）
  core/fx.js      背景光场：星域=粒子辉光，控制台=网格扫描线，手记=无
  core/g3d.js     手写 3D：投影、轨道相机、力导布局（CSP 装不了 three.js）
  vendor/gsap.min.js   GSAP 3.15，本地 vendor —— CSP 是 script-src 'self'，用不了 CDN
  themes/<主题>/  shell.css + shell.js + kit.js + views/×11
```

## 三套主题：换的是排版、结构、交互，不是配色

三套各有自己的 `shell.css`、组件词汇（`kit.js`）和 11 个视图实现，
**互相不共享一行样式或标记**。共享的只有 `core/select.js` 里的纯数据选择器。

| | 控制台 | 星域 | 手记 |
|---|---|---|---|
| 字面 | 等宽 | 无衬线 | 衬线 |
| 导航 | 左命令轨 + 数字键 | 浮岛胶囊 | running head 小型大写 |
| 组件 | 行与规则线，没有卡片 | Bento 玻璃卡 + 轨道条 | 段落、旁注、图注 |
| 表格 | 主表面就是表格 | 收进抽屉，主表面是形状 | 当作「图」并配图注 |
| 图表 | ASCII 火花线 | 环形 / 流图 / 辉光 | 细墨线线稿 |
| 动效 | 0.14s power2，硬 | 0.70s back.out，弹 | 0.48s power1，几乎没有 |
| 背景 | 网格 + 扫描线 | 粒子 + 辉光 + 视差 | 无 |
| 交互 | 键盘优先（1-9 / d / t） | 悬停展开、拖拽轨道 | 点击翻页 |

每套都有深浅两色，共 6 种组合，选择记在 localStorage。

## 每天怎么跑

无人值守，本机 cron 每天 03:10 跑一条命令：

```bash
bash ~/.memory-atlas/run.sh
```

`run.sh` 是 `atlas/build/bootstrap.sh` 的一份拷贝，装一次就不再动。它每次先
`git fetch` 再 `git archive origin/main atlas` 把代码从**远端 ref** 取出来，
然后执行 `daily.sh`。

**为什么要绕这一层**：主树归「谁在开发谁占着」—— 实测它可以领先 `origin/main`
63 个提交并带着未跟踪目录（铁律 2 被别的线程破坏）。定时任务不能依赖它的状态，
更不许去清理它（那是别人还没推的活）。所以对主树只做 `fetch`，一个字节都不写。

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
