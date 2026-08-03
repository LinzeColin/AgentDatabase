# 抓源指令 —— #117 Clara Barton（医疗护理师）

日期：2026-08-04　　`next_person.py` 配重选出（医疗护理师名册 0 人）

---

你负责 **Clara Barton（Clarissa Harlowe Barton，1821-12-25 – 1912-04-12，
美国护士、美国红十字会创建者）** 的**语料抓取**。

**这一次是真抓源，不是可得性探测**——她 1912 年卒，其著作与文书在公有领域。

## 工作目录

`CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-barton-117/`
语料放 `raw/<短名>/<短名>.txt`，台账写 `raw/_ids.txt`。

## ★★ 先读这一条：目标不是 45 份源，是 **30 份一手**

`min_sources 45` 只是分母下限。它与 `min_primary_ratio 0.65` 联立之后，
**真正的约束是一个绝对数**：

    要的一手份数 = ceil(min_sources × min_primary_ratio) = ceil(45 × 0.65) = **30**

**前两个人就死在这里**，而且**份数都不是问题**：

| | 总份数 | 一手 | 占比 | 结果 |
|---|---:|---:|---:|---|
| #115 Slavyanov | **53**（≥45 ✅） | **8** | 0.1509 | 够不着 |
| #116 Watson | 8 | 8 | 1.0000 | 够不着（道只有 2） |

**所以：宁可少抓十份二手，也要多抓一份她亲笔的。**

## ★★ 第二条硬约束：`conversations` 道不许是 0

六条道：`writings` / `expression` / `conversations` / `decisions` / `timeline` / `external`
**`min_lanes` 在 standard 与 deep 都是 6——任何一条为 0 就必死。**

**前两个人都栽在 `conversations`**：Slavyanov 一封信都没有，
Watson 七件访谈全部 `is_oa=false`。

**Barton 这一条应当是够得着的**——美国国会图书馆藏有 Clara Barton Papers
（日记与大量通信），另有 1862–1912 的公开书信与证词。
**但「应当」不是结论：先去确认，确认不了就如实报「找过，没有」，
并写清是「没找到」还是「找到了取不到」——这两种成因处置完全不同。**

## 铁律（违反其一，整批作废）

1. **零编造。** URL 必须是你**真的取到过内容**的。取不到就写进 `raw/_fetch.log`。
   **绝不允许凭印象填写篇名、年份、卷期页码。**
2. **只取公有领域。付费墙一律不碰，不绕过任何访问控制。**
   403 / access-restricted / Cloudflare 挑战一律**如实记「未绕过」并跳过**。
   （archive.org 的 `access-restricted-item: true` / `inlibrary` 属 lending-only，**不许碰**。）
3. **★ 「开放获取」不等于「公有领域」。** CC-BY-NC-SA 不是 PD，publisher-open 不是 PD，
   **本项目不按 NC 条款做例外。**
4. **★★ 版权依据只能取自出版方页面、Crossref 原始记录或版权局记录——
   绝不许照抄聚合器（Unpaywall／OpenAlex／CORE／BASE）的 `license` 字段。**
   **这是实测过的误判**：Unpaywall 对 `10.1111/j.1365-2702.2005.01256.x`
   返回 `license = "public-domain"`，而同一 DOI 的 Crossref 写的是 Wiley 标准条款，
   **且作者在世**。照抄那一格 = 把受保护作品当公有领域入库。
   **本人物 1912 年卒，依据写「卒年 1912，已过终身+70」即可，但要写。**
5. **报数前先跑一遍命令，不凭记忆**——份数、分档、道分布都要用 `ls`/`wc`/`awk` 实数。

## 台账格式 `raw/_ids.txt`（**照抄，不要自创**）

首行注释：
`# ── #117 Clara Barton (1821-12-25 – 1912-04-12, American nurse, founder of the American Red Cross; wrote in ENGLISH) corpus ledger ──`

随后每份一行，**制表符分隔，恰好 9 列**：

```
短名<TAB>URL<TAB>篇名<TAB>年份<TAB>出处定位<TAB>语种<TAB>分档<TAB>标记<TAB>说明
```

- 第 1 列短名**与 `raw/<短名>/<短名>.txt` 的目录名一字不差**
- 第 4 列年份只能来自文档本身／档案卡片／同卷可读的日期行，**并在第 9 列说明来源**
- 第 5 列出处定位：行号区间／页码／卷期。**读不出页码就不写页码**
- **第 7 列分档不许空**：
  - `P1` = **她亲笔／署名**：著作、日记、书信、演讲稿、证词、红十字会报告中她署名的部分
  - `P2` = 同一材料的**降质版本**（重复扫描、更差的 OCR、译本）
  - `S1` = **同时代**第三方（1860–1915）
  - `S2` = **后世**研究／传记
  - `U` = 无法定档（**入库后不计入 usable**）
- **第 8 列归属标记恰好一个**：`HIS-OWN`（她本人）／`CO-AUTHORED`／`THIRD-PARTY`／
  `ATTRIBUTION-UNCLEAR`；可另加 `POSTHUMOUS` / `TRANSLATION` / `DUPLICATE-SCAN` /
  `OCR-POOR` / `FULL-PAGE-SCAN`
- **第 9 列说明必须以 `lane=<六条道之一>. ` 开头**，其后写你看过文档后的判断依据；
  **并写明版权依据**（例：`RIGHTS=卒年 1912，终身+70 已过；出版方扉页 1899`）

## ★ 抓完之后、入库之前，自己先跑这一条

```bash
python3 CodexSkills/registry/codex/persona-distiller/scripts/check_corpus_ceiling.py \
  --ledger CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-barton-117/raw/_ids.txt \
  --profile deep
```

退出码：`0` 够得着 ／ `1` 够不着或只有缩分母才够 ／ `3` **判不了（说明台账格式没按上面写）**。

**看到 3 就回去修台账格式，不要交。**

## ★ 不许用「少取一点」把占比做上去

比值可以靠**砍分母**变好看。**这是缩分母，不是达标，本项目不接受。**
**如实报你真取到的全部**，占比由判据去算。

## 同名者风险

抓之前先确认有没有同名者会污染检索（例如同姓的 Barton、或她本人常被与
Florence Nightingale／Dorothea Dix 混记的段落）。
**凡是讲别人的材料，第 8 列标 `THIRD-PARTY`，正文里不许当作她的话。**

## 另外产出

- `raw/_fetch.log`：每次抓取尝试的结果，**成功与失败都记**
- `raw/_EXCLUDED.txt`：探到但**故意不入库**的，写明原因
- `raw/_BOUNDARIES.json`：仅针对整卷扫图，给出她那一段的起止行号 + 据以判断的原文行

## 返回值

简短中文报告：
① **总份数**与**一手份数**（分开报，只报总份数没有信息量）、分档分布、**六条道各几份**；
② `conversations` 道到底有没有——有就说来源，没有就说清是「没找到」还是「找到了取不到」；
③ 版权依据（**引原文**）；
④ 探过取不到的重要材料及原因（403 要写明**未绕过**）；
⑤ `check_corpus_ceiling.py` 的**原样输出**。

**「够不着」是有价值的结论，不是失败。**
**不许为交差把 S1 提成 P1、把 publisher-open 当公有领域。**
