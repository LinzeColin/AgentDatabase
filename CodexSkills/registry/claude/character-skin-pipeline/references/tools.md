# 工具清单（HarnessUI 实际文件，非示意）

仓：`Private-AgentDatabase/HarnessUI/`。全部脚本在 `tools/`，无三方依赖（标准库 + Pillow）。

## 花名册与素材采集

| 脚本 | 干什么 |
|---|---|
| `fetch_zh_names.py` | 给每个角色补简体中文名（langlinks + 中文站 categorymembers + OpenCC t2s） |
| `collect_refs.py` | 把官方立绘收进 SMB 素材库 |
| `collect_splash.py` | 把锚图从卡面升级到全身 splash art |
| `collect_hires.py` | 用 `?format=original` 无损重取原生分辨率（绕开 Fandom 的有损 WebP） |
| `collect_outfits.py` | 收全部换装/皮肤变体 |
| `collect_gallery.py` | 收角色画廊里剩下的官方美术分类 |
| `probe_loras.py` | 按花名册在 HuggingFace 探角色 LoRA 覆盖率（走本地方案时用） |
| `clean_art.py` | 抹掉右下角伪造的画师签名水印 |

> 花名册本身（`research/roster-*.json`）是用 Fandom `categorymembers` API 直接拉的，
> 见 `02-roster.md` 里的命令；没有单独脚本。

## 任务包与生成

| 脚本 | 干什么 |
|---|---|
| `build_taskpack.py` | 组装任务包（逐条 prompt + 锚图 + 期望尺寸） |
| `build_pilot.py` | 试跑包：**挑五个最能把批次跑崩的任务**，先花几毛钱验证管线 |
| `batch_run.py` | OpenAI Batch 全量驱动：提交/轮询/分块取回/落盘 |
| `batch_watch.sh` | 一直推进 batch 直到每个 unit 落定 |
| `runner.py` | 守夜人：把状态落盘，让 30 分钟的会话不至于白跑 |
| `overnight.py` | 无人值守整夜跑：生成→评分→重试→续跑 |
| `generate.py` | 花名册进、可安装的 DSH 皮肤包出（端到端） |
| `regen.py` | 定点重出：拿人工挑出的缺陷清单逐张重做 |
| `comfy_run.py` | 把试跑包丢本地 ComfyUI，做 A/B 对照（结论：画质不可用） |

## 验收

| 脚本 | 干什么 |
|---|---|
| `screen_defects.py` | 全量筛解剖缺陷——机器闸门查不了的那类（分数**只用于排序**） |
| `build_qa_crops.py` | 裁人物特写供人工扫查 |
| `build_qa_page.py` | 特写墙：一屏几十张，扫过去点掉有缺陷的 |
| `build_review.py` | 验收页——机器唯一做不了的那件事 |
| `ledger.py` | 批次感知的素材台账 |

## 归档与运行时

| 脚本 | 干什么 |
|---|---|
| `archive.py` | 归档到 NAS，**放在它所依据的素材旁边** |
| `build_catalog.py` | 生成运行时读的 `catalog.json` |
| `make_derivatives.py` | 生成运行时切换用的显示尺寸 WebP |
| `import_one.py` | 把一张外部图片收进素材库（菜单栏「添加素材」调它） |
| `build_skin.py` | DSH 皮肤工厂：四张图进，一个可安装皮肤包出 |
| `asset_server.py` | 通过 loopback http 把皮肤库喂给 DSH |
| `watch_mmx.py` | 读 MiniMax Design 网关日志判活（读两个最新日志，避午夜轮转） |
| `nightwatch.sh` | MiniMax Design GUI 跑批的守夜脚本 |

## 宿主侧源码

| 位置 | 干什么 |
|---|---|
| `dsh-plugin/lib/index.js` | 宿主半边（Node）：起素材服务，DSH 起它就起、退它就退 |
| `dsh-plugin/lib/client.js` | 浏览器半边：注入背景、清遮挡、可读性渐变、右下角面板 |
| `kimi-shell/main.js` | Kimi 外壳：`kimiskin://` 协议、串行 applySkin、`fs.watch` 共享状态 |
| `kimi-shell/harness-gallery.html` | Kimi 的画廊窗口 |
| `menubar-app/` | `LSUIElement` 菜单栏控制器（`main.js` / `gallery.html` / `state.js`） |

## 运行时目录 `~/.harness-ui/`

```
master/      母版 PNG（4.8GB，NAS 有备份）
display/     显示尺寸派生图
thumb/       缩略图
anchors/     锚图
catalog.json names_zh.json state.json
asset_server.py  import_one.py
qa/          crops/ + index.html（人工复核页）
review.html  diag.log
menubar/     控制器运行时数据
```

## 交付与调研产物

| 文件 | 是什么 |
|---|---|
| `delivery/manifest-v1.7.0.json` | 全量成品清单 |
| `delivery/acceptance-v1.7.0.json` | 逐张验收记录（status/attempts/metrics/fails） |
| `delivery/实测笔记.md` | 实测数据（成本、通过率、耗时） |
| `research/roster-{genshin,hsr,zzz,wuwa}.json` | 四游戏花名册 |
| `research/names_zh.json` | 中文名映射 |
| `research/generation-stack.md` | 渠道选型对比（为什么是 OpenAI Batch） |
| `research/material-sources.md` | 素材源调研 |
| `research/lora-coverage.md` | LoRA 覆盖率（本地方案的可行性判断） |
| `research/douyin-analysis.md` / `douyin-characters.json` | 抖音三博主蒸馏与角色清单 |
