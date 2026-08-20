---
name: character-skin-pipeline
description: 用游戏官方立绘批量产出应用皮肤背板（原神/崩铁/绝区零/鸣潮等），并装进 DSH、Kimi Code 这类 Electron 应用。Use when 要做角色壁纸/背板批量生成、给桌面应用换皮肤、按花名册全量出图、或排查"皮肤装了但不显示"。覆盖：花名册采集、锚图选取、任务包与 prompt 约束、Batch API 出图、验收闸门、人工缺陷复核、宿主接入。
metadata:
  category: pipeline
---

# 角色皮肤生产线

一条从「游戏花名册」到「桌面应用换上皮肤」的完整链路。2026-08 在 HarnessUI 项目上
跑通了 612 张（原神 78 人 / 崩铁 54 人 / 绝区零 45 人），成本 $47，一次通过率 92.8%。

下面每一条都是踩过才知道的。**按顺序做，别跳步。**

---

## 0. 先算清楚成本，再动手

用户会问「多少钱」。**按成品数算，不是按提交数算。**
有质检闭环的产线里这两个数差一个量级——HarnessUI 上是 3:1（后来降到 1.08:1）。
报工期/报预算前先量出重试倍率，否则会乐观十几倍。

单价实测（gpt-image-2 @ 3840×2160，2026-08）：
- 实时接口 **$0.114/张**；Batch **减半 $0.057**
- 同一模型经 MiniMax Hub 转售：**8.34 元/张**，贵 10 倍以上

---

## 1. 花名册：用 wiki 的分类，别手敲

```
https://<game>.fandom.com/api.php?action=query&list=categorymembers
  &cmtitle=Category:Female Characters   (鸣潮是 Female Resonators)
```

中文名走 `prop=langlinks&lllang=zh`，**拿到的多半是繁体**，用 OpenCC `t2s` 转简体。
英文站没有 `zh` 链接的（绝区零全军覆没），改从中文站 `<wiki>.fandom.com/zh/api.php`
反查它自己的 `en` 链接再取反。两条都走，覆盖率能从 60% 升到 87%。

**花名册里的 `wiki_page` 可能是 `/Lore` 子页**——子页上没有立绘，取基础页。

## 2. 锚图：竖构图优先于大面积

角色还原度**完全**来自锚图，不来自 prompt。选取规则按优先级：

1. **provenance 优于分辨率**：先按文件名筛出立绘类
   （`Full Sprite` / `Splash Art` / `Portrait` / `Card`），再在其中比大小。
   直接按像素面积挑，会挑到抽卡横幅——164 个角色里错了 51 个。
2. **竖构图优于面积**：`(1 if h>=w else 0, w*h)` 排序。横幅像素再多，人物也是裁过的。
3. **必须加 `?format=original`**：Fandom 的 CDN 默认返回有损 WebP 转码，
   同一个 750×1800 文件 313KB vs 1.66MB。

## 3. Prompt：约束要能被机器复核

- **负面词写进正文**。`gpt-image-2` **没有** negative prompt 参数，
  任务包里那个 `negative_prompt` 字段发不出去，等于没写。
- **冲突要显式裁决**。「严格照参考图」和「必须穿丝袜」会打架，模型只能随机取中。
  写清优先级：身份（脸/发色/瞳色/配饰/配色）照锚图，服装造型照规则，**冲突时规则优先**。
- **用户点名否决过的，一定要有一条对应的排除项**。Q 版就是这么漏进去的——
  用户看到成品才发现，而 594 条 prompt 里一个字都没有。

## 4. 出图：Batch + 落盘即判 + 带着失败条款重出

- 走 `/v1/images/edits`，**JSON 模式下参数叫 `images`，是对象数组**
  `[{"image_url": "data:image/jpeg;base64,…"}]`。不是 multipart 的 `image`，
  不是字符串数组，也不是 Responses 风格的 `{"type":"input_image"}`。三种我都试错过。
- 尺寸上限 **长边 3840**。
- Batch 结果文件是 GB 级 JSONL，**必须分块流式落盘**。
  一次性 `read()` 会在 ssl 层抛 `OverflowError`，把守护进程直接打死。
- 重试必须**把上一次的失败条款拼进 prompt**，否则只是再掷一次骰子。

## 5. 验收：机器判数字，人判审美

机器闸门（比例/宽度/亮度/主体溢出）能查的到此为止。
**「有三只手」这类只能人判**——用视觉模型做判官试了三轮全失败：
宽松版漏掉已知坏图；严格版 100 张报 83 张；改问「显眼度」又漏掉。
问「能不能找出毛病」答案永远是能；问对之后它复现不了用户的阈值。

机器该做的是**把人工判定变便宜**：把人物从画幅里裁出来放大
（人物只占左 35%，整图缩略里手指级缺陷根本看不见）、排成密网格、
点一下标记、导出清单喂给定点重出。判官分数**只用来排序**。

## 6. 装进宿主

**先查这个宿主怎么给插件送素材**，别假设。
- **Kimi Code**：注册 `kimiskin://` 自定义协议直接读盘，自足。
- **DSH**：每个插件**只服务 `client.js` 一个文件**，其余路径全 404，
  渲染进程还拒绝 `file://`。只能由插件的宿主半边（Node）自己起一个 http 服务。
  **把服务放进插件里**，别做成外部进程——用户一关它，皮肤就悄悄没了背景。

DSH 装插件要**同时登记三处**：profile 的 `node_modules` 软链、`dependencies` 的
`link:`、以及 `dsh.profile.bundles` 加载清单（最容易漏的一条）。
判断有没有挂上：读 `window.__DSH_BOOT__.entries`，别靠界面猜。

## 7. 皮肤不显示 / 发灰：一步判据

把页面里所有元素的 `background-color` 和 `background-image` 临时清空、只留根容器的背板。
**立绘立刻显示 = 背板一直是好的，问题百分之百在遮挡。**

遮挡层的类名多半是编译哈希（每次构建都变），**不能按类名修**。
做法：清空全部后代底色，再只给承载文字的控件加回半透明底。
清空后文字会压在亮画面上读不了——用**按列的渐变遮罩**解决
（这类构图是「左人物、右留白」，侧栏区和正文区各压一层，人物那段不遮）。

其余两个常见但非主因的：`backdrop-filter: blur()` 糊的是元素背后的一切；
`background-attachment: fixed` 让 Chromium 按 1x 光栅化再放大。

## 8. 别用鼠标去诊断用户正在用的应用

多显示器 + 多 Spaces 下 `left_click(x,y)` 落点不可靠，而代价是污染用户的数据——
我把 328 字符诊断代码打进了用户正在写的消息并发送了。

**让被诊断的代码自己回报**：给本地服务加一个 POST 端点，插件把状态 POST 过去落成日志。
能用 Bash / HTTP / 文件读写查到的，一律不要用鼠标。

---

## 现成的工具

`AgentDatabase` 仓 `HarnessUI/tools/`：

| | |
|---|---|
| `collect_hires.py` / `probe_res.py` | 锚图探测与无损下载 |
| `build_taskpack.py` | 任务包与 prompt 生成 |
| `batch_run.py` / `batch_watch.sh` | Batch 出图、落盘即判、断点续跑 |
| `runner.py` | 验收闸门（`gate()` 返回带修正提示的失败条款） |
| `build_qa_crops.py` / `build_qa_page.py` | 人物特写 + 人工复核墙 |
| `regen.py` | 吃复核清单定点重出，旧图留 `rejected-N` |
| `fetch_zh_names.py` | 简体中文名采集 |
| `asset_server.py` | 素材服务（带 CORS 与状态写回） |
