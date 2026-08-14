# Machiavelli #177：一份源 **41.68% 是天城文乱码**，而所有门都放行

**2026-08-15**｜任务 #119 记着「第 1 批判完分后：修 Jefferson 空文件与 Machiavelli 天城文噪声」。
Jefferson 那半已做（另记）。这是另一半。

## 实况：只有一份，但那一份坏得很彻底

    src-213511a1f84a｜tier=S1｜split=train｜extraction_status=raw（原）
    title: Life And Times Of Niccolo Machiavelli
    天城文字符 **1,114,949 / 全文 2,674,715 = 41.68%**

采样原样（不改一个字符）：

    [1 ~~ ~~ ~+ क्न 2777 4 2 270 9 ५५ +^. © 41८4 ८.74 7.2 2.76. प । ॐ ध ` ~ =,
    एरचि के दाल 0 लाप्णद्या९ 10, (12051266 छ [ह ए ^, एणाः एज 270 1112६005

**这不是别的语种，是 OCR 把拉丁字母误识成天城文。**

## 用仓里已有的尺子复核，不另造

`_pipeline/fetch_kramerius.py::letter_run_ratio`（本会话早先为 Kramerius 通道写的，
自带正反自测，且明确不许把好的俄文/希腊文判成乱码）：

    letter_run_ratio = **0.2577**｜门槛 OCR_MIN_RATIO = **0.50**

**全工作区 79 份里只有这 1 份低于门槛。** 两把独立的尺子（天城文占比、字母连跑率）
指向同一份，互相印证。

## 它有多重、伤到谁

    占 train 词数 **523,460 / 10,312,850 = 5.1%**
    **被 0 条断言引用** —— 逐条查过 27 条断言，`src-213511a1f84a` 一次也没出现

⇒ **产物没有被污染**，影响面是语料统计。

## ★★ 为什么所有门都放行：与 Jefferson 那件**是同一个机制**

`quality_check.py:285` 的 usable 口径只看 `tier` 与 `extraction_status` 两个字段，
**从不打开文件**。这份 `tier=S1`（不是 U）、`extraction_status=raw`（不是 failed），
于是 41.68% 是乱码的文件被算作可用训练源。

★ 研究门**确实有一条相邻的告警**，但盖的不是这件：

> `corpus.longs-corruption`：**16 份语料的长 s 讹字率超过 20%** —— esse→esfe、such→fuch，
> 份数／分档／字数三样都是真的，所以既有的门都放行了

那是**替换型讹字**（一个字母被认成另一个字母），本件是**整段字符集误识**（拉丁 → 天城文）。
两者的信号不同，那条告警的正则抓不到这一份。
[[a-gates-scan-set-is-smaller-than-reality]]

## 处置：只写事实

`extraction_status: raw → failed`。抽取确实失败了（按仓自己的 `OCR_MIN_RATIO` 判），
这是陈述事实，不是调门；改完之后判据用它自己的规则把这份排除掉。

负对照：台账 **79 行 → 79 行**，**只有那 1 行变**，只动 `extraction_status`
与新增的 `★ OCR 失败-2026-08-15` 说明字段。

★ 写盘第一版失败过一次：说明文字里有 `41.68%`／`5.1%`／`20%`，
被 `%` 格式化当成占位符（`TypeError: * wants int`）。**好在负对照当场显示 0 行被改**，
没有半写。改用字符串拼接重做。[[prose-inside-templates-hits-metacharacters]]

## 改后的门读数（实测）

    改前：sources_train 69｜usable **69**｜primary 57｜ratio **0.8261**｜passed=True 硬错 0
    改后：sources_train 69｜usable **68**｜primary 57｜ratio **0.8382**｜passed=True 硬错 0

`primary_sources` 不变（这份是 S1，本来就不在分子里），**占比反而上升** ——
把一份坏 OCR 的次级源排除，一手比例只会更高。**没有一道门被移动。**

## ★ 一条自己写错又撤回的观察

我一度记下「改之前研究门几秒出结果，改成 `failed` 之后跑过 10 分钟未结束」，
并写进本文件当作「未查明的现象」。**那是错的，已删。** 真相两层：

1. 那两次「空输出」是我用了 `timeout 540 python3 …` —— **macOS 没有 `timeout`**，
   `rc=127 command not found`，**立刻空退出**。我把「命令不存在」读成了「跑不完」。
   [[pipe-to-tail-hides-the-exit-code]]｜[[empty-default-swallows-unknown]]
2. 直接跑（不套 `timeout`）实测 **rc=0、590 秒**。研究门在这个工作区本来就要约 10 分钟
   （他 train 有 **10,312,850** 词）—— **与我的改动无关**。

★ 教训：**报「变慢了」之前先确认那条命令真的跑过。** 一个 rc=127 的空输出，
和一个跑满十分钟的进程，在 stdout 上长得一模一样。
