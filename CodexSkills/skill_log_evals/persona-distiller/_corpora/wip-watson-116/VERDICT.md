# #116 Jean Watson — **不按 deep 推进；standard 与 quick 也够不着。记延后（新增第五类：作者在世）**

**没有跑蒸馏。** 这一次派的是**可得性探测**，因为她 **1940 年生、在世**，
其著作全部在版权保护期内，而铁律是只取公有领域、付费墙一律不碰。

**没有假定她与 #113 Henderson / #114 Peplau 相同**——
版权、开放渠道、档案三层各自重查了一遍。**结论同向，成因是新的一类（见下）。**

## 结论：够不着，而且这次连 quick 都够不着

数字来自 `check_corpus_ceiling.py --ledger raw/_ids.txt`，**不是估的**：

```
手上：一手 8 份　总计 8 份　有材料的道 2 条
  quick    (8 / 3道 / 0.40 → 要 4 份一手)   够不着 —— 道 2 < 3
  standard (24 / 6道 / 0.50 → 要 12 份一手) 够不着 —— 份数 8<24、道 2<6、一手 8<12
  deep     (45 / 6道 / 0.65 → 要 30 份一手) 够不着 —— 份数 8<45、道 2<6、一手 8<30
```

| | 实测 | deep 门 |
|---|---:|---:|
| 真取到全文的源 | **8 份** | ≥45 |
| **其中一手（P1）** | **8 份** | **≥30** |
| 六条道覆盖 | **2 条**（writings 6 / expression 2） | 6 条 |
| **`conversations` 道** | **0** | ≥1（0 即 standard/deep 必死） |
| **确认公有领域的** | **0 件** | — |

八份合计 **25,006 词**。
`conversations` / `decisions` / `timeline` / `external` **全 0**。

**没有靠砍分母把占比做好看**：8/8 = 1.0 是因为**取到的确实全是她独著**，
不是因为丢掉了二手件。二手评述量极大（各国护理教科书章节、Pardede 2020 等），
**一件没取**——取了只会把分母做大、占比做低，那才是凑数的反面操作。

## ★ 版权状态：这一份和前两位**不是同一个问句**

Henderson / Peplau 要查的是「**有没有按时续展**」。
**Watson 没有这个问句可问。**

她最早的著作《Nursing: The Philosophy and Science of Caring》出版于 **1979 年**，
落在 **1976 年版权法**（1978-01-01 生效）之下 —— 17 U.S.C. §302(a)：
**保护期 = 作者终身 + 70 年，无须续展，也无从「漏续展」。**

### 硬证据一：她本人到 2023 年仍在逐篇持有版权

*Pensar Enfermagem* 期刊页面原文（`pensarenfermagem.esel.pt/.../view/296`）：

```
Copyright (c) 2023 Jean Watson
This work is licensed under a Creative Commons Attribution 4.0 International License.
```

**版权人写的是她本人的名字，而她在世。**
CC-BY 是**她授出的许可**，不是版权失效。**许可可以撤回，公有领域不能。**

其余各件的版权声明（全部照录自我实际取到的页面／PDF）：
`© Japan Academy of Nursing Science`（J-STAGE 2002/2004）、
`CC BY-NC 4.0`（SciELO TCE 2007）、
`© 2018 Universidad Católica Santo Toribio de Mogrovejo`（CIETNA）、
`CC BY-NC-ND 4.0`（OPI Napoli 2019）、
`© 2025 Watson Caring Science Institute.`（她本人机构官网）。
**七个国家、七种许可，没有一个是 PD。**

### 硬证据二（负结果，且必须按正确口径读）

**NYPL `cce-renewals` 全库 grep**：47 个 TSV 全下、**445,433 行**，
`jean watson` **0**、`watson, jean` **0**、两部主著书名 **0**；
`watson` 任意命中 446 行，其中**同行含 nursing/nurse/caring 的 = 0**。

**但 0 命中不是有利证据。** CCE 覆盖的是 1922–1963 年作品在 1950–1992 年的续展登记，
**她的产出期整段在这个区间之外**，查不到本来就是预期。**不许反推为公有领域。**

### 未取得的第二重证据（如实记）

**美国版权局 CPRS API**：`advance_search/` 先返 400 并吐出合法 `sort_field` 枚举，
补齐后仍 **500**；其余端点 404。**未取得登记记录，未绕过任何限制。**
（与 #114 遇到的是同一个故障。）

## ★★ 本次最有复用价值的一条：**聚合器把在版权期内的文章标成了 `public-domain`**

Unpaywall 对 `10.1111/j.1365-2702.2005.01256.x`
（Watson 独著，*J Clin Nurs* 2005 Guest Editorial）返回
`best_oa_location.license = "public-domain"`。

**这是错的。** 同一 DOI 的 Crossref 记录写的是
`http://onlinelibrary.wiley.com/termsAndConditions#vor` —— Wiley 标准条款。

**照抄这一格，就会把一篇在版权期内的 Wiley 社论当成 PD 入库。**
建议固化为一条常设判据：**版权判据只能取自出版方页面或 Crossref 原始记录，
不许取自 Unpaywall / OpenAlex 的 `license` 字段。**

## 缺口不是「某几条道空」，是整个人的可取材料在开放区之外

**决定性的一条**：她的 **9 部专著在 archive.org 的扫描全部 `access-restricted-item: true`**
（3 件还带 `inlibrary`）——**lending-only，一律未碰**。
而她的理论主干（10 Caritas Processes、transpersonal caring relationship、
carative factors 十项）**正是写在这些书里的**。

**全量核验，不是抽样**：OpenAlex 两个作者 ID 合并去重 **236 件**（独著 **110 件**），
∪ Crossref 筛出的 219 件 → **249 个唯一 DOI 逐条查 Unpaywall**：
`closed 218 / gold 12 / bronze 8 / green 8 / hybrid 3`。
31 个 OA 里 12 个是同名他人、6 个是她的合著（她排第 2–5 位）、
5 个 Wiley 独著实测 **Cloudflare 403 未绕过**，**真能取的就是那 8 个**。

**1976–2001 这 26 年的独著，一件 OA 都没有。**

## ★ `conversations` 道单独查过：**访谈有七件，七件全在墙后**

这一条是 #115 Slavyanov 的死因，所以本次单列核对：

| 年 | 篇名 / 出处 | 状态 |
|---|---|---|
| 2002 | Aesthetics, postmodern nursing… an Internet dialogue（*CTNM*） | closed |
| 2005 | Caring for our future: an interview with Jean Watson（Interview by Carla Mariano） | closed |
| 2007/2008 | The Power of Wholeness, Consciousness, and Caring: A Dialogue on Nursing Science（*IJHC* / *ANS*） | closed；DigitalGeorgetown handle **404** |
| 2009 | From Theory to Practice（Clarke, Watson, Brewer，*ANS*） | closed |
| 2010 | An interview with Jean Watson, HNY 2010（Interview by Lynne Nemeth） | closed |
| 2021 | **Nursing Is the Light in Institutional Darkness: A Dialogue With Dr. Jean Watson**（*NSQ*） | closed（Sage） |

**不是没找到，是找到了七件、七件都取不到。**

## 三件「索引说能取、实测取不到」的（如实记）

| 材料 | 索引说 | 实测 |
|---|---|---|
| RECIEN 2020 西英两版 COVID 领导力社论（她独著） | OpenAlex `green`、LA Referencia、`cc-by-nc-sa` | view/download 链接**全 404**（期刊改版） |
| Aquila (USM) 2021《Caring Science as Sacred Science》 | 机构库有条目 | `Document Type: Video`／`This document is currently not available here` ——**只有影像，无转录本** |
| 日赤広島 2000 開学特別記念講演 | CiNii 有条目 | JAIRO 停服 **HTTP 000**；CiNii crid **404** |

## 真取到的 8 份，如实标注

| 文件 | 词数 | 年 | 道 | 许可 |
|---|---:|---:|---|---|
| `jstage-holistic-2002` | 2,992 | 2002 | expression | © Japan Academy of Nursing Science |
| `jstage-caritas-communitas-2004` | 3,831 | 2004 | expression | © Japan Academy of Nursing Science |
| `tce-theory-human-caring-2007` | 4,427 | 2007 | writings | CC BY-NC 4.0 |
| `mundosaude-cuidar-essencia-2009` | 4,629 | 2009 | writings | 期刊持有（葡/英/西三语） |
| `tce-editorial-disciplina-2017` | 941 | 2017 | writings | SciELO CC |
| `cietna-ciencia-cuidado-2018` | 2,198 | 2018 | writings | © USAT；CC BY-NC-ND 2.5 PE |
| `opin-unitary-caring-2019` | 3,408 | 2019 | writings | CC BY-NC-ND 4.0 |
| `pensarenf-unitary-caritas-2023` | 2,580 | 2023 | writings | **Copyright (c) 2023 Jean Watson** + CC BY 4.0 |

**八份都不是公有领域**，全部是 gold/diamond OA 或学会持有。
**没有把 OA 冒充成 PD，没有把合著当独著，没有绕过任何访问控制。**

两件 Redalyc 镜像（TCE 2007 / 2017 的重复件）**真取到了但不计份数**——同源。

### 一处自我更正

写 `_DO_NOT_INGEST.md` 时我本想说那两篇讲演稿「带 `I want to`／`Let me` 的第一人称推进」。
**数了一遍，这句是编的**：两篇里 `I want to` 与 `Let me` **各 0 次**，
`we` 45／64 次。它们是**讲演之后整理成的论文，不是逐字转录**。
仍算 expression（讲台文体），**但不是 #114 那种 69 问 / 72 答的问答体。**

## 处置

- **不按 deep 推进；standard、quick 同样不推进。** 三档全部够不着。
- **入 `_延后名单`，成因记为新的一类——第五类：作者在世。**
  **不要并进第三类。** 第三类（#113/#114）是「产出期在版权内 + 被按时／自动续展」，
  **有确定到期日**（2034–2066）；
  本件是「终身 + 70」，**写不出到期日**——最早也要到 22 世纪。
- **一件不入库**，全部记进 `raw/_DO_NOT_INGEST.md`。

## 由此加固的排期规则

> **卒于 1930 年后 → 排期前先跑可得性探测**（#113/#114 已定）
> **★ 在世者 → 直接不排期，连探测都不必跑**（本件新增）

本次探测的价值**不在人物结论**（结论如预期），
而在两件可复用的判据素材：

1. **§「聚合器 license 字段不可信」** —— 一个已发生、可复现的误判，
   直接可以落成检查器。
2. **「访谈全在墙后」的七件清单** —— 说明 `conversations` 道为 0
   有时不是「没找」，而是「找到了、全取不到」，
   **报告里必须把这两种情况分开写**，否则下一个人会以为再抓一次就有。

**「够不着」是有价值的结论，不是失败。**
**这一次尤其是**——它把「够不着」的成因从「续展堵死」推进到了
「**根本没有到期日**」，那是一类以后不必再探的人。
