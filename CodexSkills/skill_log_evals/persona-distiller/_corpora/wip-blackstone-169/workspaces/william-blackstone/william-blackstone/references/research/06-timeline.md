# Timeline, stages, and drift

## Scope and assigned sources

**本道分到 0 份（train split）**。

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**。

## Source-linked observations

★★ **本道的定位：印本年表，不是生平年表。**
台账没有给它投影任何 `split == train` 行，它用的是**全部 train 源的扉页年份**——
那是台账 `rights_basis` 字段里**逐字照录的印本年**，不是我从正文读的，也不是我推的。
「他哪一年做了什么」在多数条目上**推不出来**，下面逐条标明哪些能、哪些不能。

★ 这两句原本写在 Scope 节里，而那一节是 `emit_lane_scope.py` 机械重出的——
**放在那里会被下一次重出覆盖掉**（本轮实测就被覆盖了一次）。判断性的话要放在这里。

### 一、生卒（不来自本工作区语料，来自同名门）

`1723-07-10 – 1780-02-14`，**四库精确到日且互证**：Wikidata Q332449 ∧ LCCN n79120719 ∧
GND 118511483 ∧ VIAF 39385957，互证关系由 VIAF 的 sources 字段直接列出。
★ **这一条是子代理实调四库所得，我本人未重跑**，见 `meta.json` 的 `attribution_basis.citation`。

### 二、印本年表（**逐条标出处强弱**）

| 年 | 印本 | 年份出处 | 强弱 |
|---|---|---|---|
| 1747 | *The Pantheon: a Vision* | archive.org 条目 title/date 字段 | **弱**：只有编目一条，且该件归属为 `U` |
| 1758 | *A Discourse on the Study of the Law* | 编目题名**逐字转写**了题名页 `October XXV, M.DCC.LVIII` | **中**：单一来源，但转写的是题名页 |
| 1762 | *Law Tracts* 卷二 | 本文件内扉页照录 `M. DCC. LXIL` | 强（OCR 把 `II.` 读成 `L`） |
| 1762 | *Law Tracts* 卷一 | archive.org date ＋ **同套卷二扉页互证** | 中 |
| 1763 | *The Lawyer's Farewell to his Muse* 刊出 | **母卷**扉页照录 | 中：诗本身不署名、写作年另计 |
| 1766 | *An Analysis*，第五版 | 本文件内扉页照录 `MDCCLXVI.` ＋ 编目一致 | 强 |
| 1770 | *Letters to … Mr. Justice Blackstone*（他人所著） | 本文件内扉页照录 `M D C C L X X.` | 强 |
| 1773 | *Reply to Dr. Priestley's Remarks* | 本文件内分辑扉页照录 | 强 |
| 1773 | 费城合刊（他人编） | 编目 ＋ 分辑扉页照录互证 | 强 |
| 1781 | *Reports … Westminster-Hall* 两卷 | 本文件内扉页照录 `MDCCLXXXI` ＋ 编目 | 强 |
| 1898 | *Commentaries* 四卷（本工作区所用印本） | 扉页 ＋ 版权行**两处互证且都在文件内** | 强 |

### 三、从年表能读出的两件事

1. **1770 年那份他人来信的称谓是 `Mr. Justice Blackstone`** —— 与「他 1770 年起在庭上」相合，
   **这是本工作区内唯一一条由第三方文本佐证其职位年份的材料**。
2. **1781 年的两卷刊于他卒后一年**（卒 1780-02-14），扉页自陈收录 `From 1746 to 1779`——
   **编次跨越他出庭与在庭两个阶段，而出版发生在他身后**。


## Candidate Claims

- **clm-bs-time-01｜他的作品带年份的印本从 1758 连到 1781，跨度 23 年，
  且 1781 那部刊于身后。** 证据：上表各扉页照录 ＋ 四库卒年 1780-02-14。
- **clm-bs-time-02｜1770 年他已被同代人以「Mr. Justice」相称。**
  证据：`src-cef41ec3ad00` 扉页照录。
- **clm-bs-time-03｜同一篇 1758 年的讲词在 1766 与 1898 两个印本里被重新用作卷首。**
  证据：台账三处重叠记录（与 01 道 `clm-bs-arch-02`、03 道 `clm-bs-voice-03` 同源）。


## Contradictions and alternative explanations

- **印本年 ≠ 写作年。** 最清楚的一例：那首诗题名自陈 `Written in the Year 174…`，
  而刊出在 1763。**本道给出的是印本年表，任何「他那一年在想什么」的说法都超出它。**
- **1747 那一条不能用**：归属 `U`，年份只有编目一条。★ 不得据它说「他 24 岁时写过什么」。
- **1758 与 1762 卷一的年份都是单一来源**（一条编目题名／一条 date 字段 ＋ 同套互证）。
  它们比其余各条弱，**产物里若用到这两个年份，必须带上这句**。


## Unknowns and source gaps

- **本工作区没有任何逐日或逐月的一手记录**（书信、日记之类的编年材料本轮未取得，
  见 `_corpus/00-抓源记录.md` 的「没抓到」一节）。
  → **「他某年某月做了什么」这一层，本道答不了**，产物必须承认。
- 1762 两卷的年份读法依赖对 `M. DCC. LXIL` 的还原（OCR 讹形），**已照录未改**。
- 他任职的确切起讫（何时任 King's Counsel、何时转 King's Bench）**本工作区语料内没有**；
  规范档字段里有，但**那不是本工作区的一手材料**，本道不据以下断言。


## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

- 用例方向：`case-trajectory-*`——问他某个年份的具体事项时，他能不能区分「印本年我知道」与「那一年我在做什么我说不出」。

## Handoff to adjudication

- 三条候选断言均带证据；**年份逐条标了强弱，弱的两条已点名**。
- ★★ **传给判分侧的红线**：本人物**没有编年一手材料**。
  产物里凡出现「某年某月我如何」的叙述，**都是没有证据的**，必须删。
  能说的只有「哪一年出了哪个印本」，以及它与卒年的先后。

