# Steinhardt #98 —— 卡在语料上限，等一个范围决定

## 硬数字

| 项 | 值 | deep 门 |
|---|---|---|
| 干净 P1（有归属正面证据） | **28** | 需 **≥30** |
| 可用 train 源 | 45 | ≥45 ✅ |
| primary_ratio | **0.622** | ≥0.65 ❌ |

`min_sources 45` 与 `min_primary_ratio 0.65` 联立 ⟹ **P1 至少 30 份**。
**多灌次级源只会把比值压低**（分母涨、分子不动），所以这不是灌库能解决的。

## 28 份 P1 的构成

- **17 篇 CONTACT 署名随笔**（2000–2013，他基金会季刊，逐篇留有署名证据）
  含 2000 春季刊一整篇 `EV:`／`MS:` 问答
- **6 篇逐字稿/访谈**：Charlie Rose 2001、Charlie Rose 2006、
  Larry Connors 2001、Knowledge@Wharton 2009、Benzinga 2011（14 段应答）、
  The Media Line 2022（三方问答）
- **5 篇署名文章**：eJP「The 94 Percent」、eJP 日校演讲全文、
  Jewish Journal 悼 Adelson、SAPIR 2023、以及 2016 Senesh 演讲编者注版

投资侧一手件只有 6 篇——**这是本人物的真实结构性短板**，不只是数量问题。

## 为什么补不到 30（每条都实测过，不是推测）

| 矿脉 | 结果 |
|---|---|
| CONTACT 全 60 期 | 已按页切完，**只有 17 期有他的署名专栏**；其余期他的名字只在第 2 页刊头职衔栏 |
| YouTube 字幕（Robertson 那轮 13 篇 P2 的来源） | 字幕轨存在但取回 **0 字节**（签名令牌）。我独立复验了 4 个视频，抓源 A 的结论成立 |
| archive.org 三本书 | `No Bull` / `Market Wizards` / `Hedge Hunters` 全是借阅件，`_djvu.txt` 返回 401/403 |
| Wayback CDX 检索 | benzinga、barrons 两个站点均 0 条 |
| C-SPAN | 搜索结果整个走 JS，页面里那 25 处 Steinhardt 在导航脚本里 |
| eJP / SAPIR / Jewish Journal 作者页与站内搜索 | 搜到的基本是**写他的**，不是他写的；三篇候选逐一验署名，作者分别是 Karen Lehrman Bloch、Gidi Grinstein、Neville Teller |
| 网络检索（两轮） | 回来的条目全部已在库中 |
| NYT / WaPo / Barron's 存档 | 付费墙 |

## 我**没有**做的一件事，以及为什么

`ms_2008_contact_winter.txt` 是他与 Rabbi Daniel S. Brenner 的**合署**随笔。
把它算作 P1 就正好 29，再松一格就够 30。**我没有这么做**——
为了凑够门槛去改判据，正是本轮抓出来的那个病（RUNBOOK 第六十三种）。
它现在是 S1，abstract 里写明「其中任何一句都不能单独归给他」。

## 本轮已经落地的东西（与决定无关，已完成）

- **`check_authorship.py`**（新，硬门，已归位 `_pipeline/checkers/`）——
  语料要当「他的话」用必须有**正面归属证据**且证据随文落盘。
  三种：结构位置上的署名 / 编者注 / 对话轮次。回归 8 正例 + 6 反例全过。
- **`ms_contact2.py`**（新）—— 按页切 CONTACT，署名留在正文里。
- **RUNBOOK 第六十三～六十八种**（6 条）。
- **`build_manifest_ms.py`** —— 分层清单，一条一个理由，替掉了失效的自动判据。

**它拦下的最重要一件事**：抓源子代理把整期 CONTACT 按页切片后一律冠上
`ms_` 前缀，十份里九份不是他写的（Lynn Schusterman / Adam Bronfman /
Simon Greer / HUC-JIR 等）。其中一句
「我小时候父亲教我的第一课是：慈善是我们付给这世界的房租」
必然会被写成他与其父 Sol 的家世——**那是 Lynn Schusterman 的父亲**。
灌库命令带着 `--author "Michael Steinhardt"`，两步就洗白了。
