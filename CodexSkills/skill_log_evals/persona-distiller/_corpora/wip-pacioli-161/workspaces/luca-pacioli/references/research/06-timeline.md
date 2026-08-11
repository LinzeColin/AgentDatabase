# Timeline

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-0af54aee74c3` | 1908 | S2 | rouseball-1908-short-account-history-mathematics-pacioli.txt |
| `src-11b5ad20c3cc` | 1911 | S2 | catholic-encyclopedia-1911-lucas-pacioli.txt |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

★ 2026-08-12：下面几行原在本文件开头那个 Scope 节里。
  那一节由 emit_lane_scope.py 从台账**机械重出、不含阅读判断**，
  手写内容重出时会被静默抹掉——判断性的话搬到这里才留得住。
  ★★ 本条注释**刻意不用反引号**：反引号里的英文会被
     check_lane_quotes_verbatim 当成一条待核引文，而它当然核不到
     （第一版就是这么把三个工作区改红的）。

**2 份，均为 S2**：`catholic-encyclopedia-1911`、`rouseball-1908`。
（`geijsbeek-1914` 的导论里也有一份任教城市名单，本道一并核了，见 T2。）
★★★★ **本道最重要的一句写在最前面**：**这三份来源在两件基本事实上互相不一致**——
**卒年**与**任教城市名单**。**产物里不许悄悄取一个当确定值。**

## ★★★★ T1：卒年——**三个数，三个出处**

来源：src-11b5ad20c3cc src-0af54aee74c3

Catholic Encyclopedia 1911：

> born at Borgo San Sepolco, Tuscany, toward the middle of the fifteenth century; died probably
> soon after 1509. Little is

Rouse Ball 1908：

> he lectured on mathematics at Rome, Pisa, Venice, and Milan; and that at the last-named city he
> was the first occupant of a chair of mathematics founded by Sforza: he died at Florence about
> the year 1

（引到断点为止；该句原文作 `about the year 1510`。）

而本工作区 `meta.json` 现在写的是 **1517**（现代共识）。

★★★ **这不是抄错，是学界前后修正过。** 1908／1911 那两位作者看不到更晚的考证。
★★★★ **正确处置**：三个年份都留、各注出处，
**并把「卒年不确定、学界前后修正过」本身当成一条可引用的事实**。
★ **不许取居中数字，也不许只写 1517 而不提另外两个。**

## ★★★ T2：任教城市——**三份名单，没有两份相同**

来源：src-0af54aee74c3 src-11b5ad20c3cc src-bcece04a709a

| 出处 | 名单 |
|---|---|
| Rouse Ball 1908 | `Rome, Pisa, Venice, and Milan` |
| Catholic Encyclopedia 1911 | `professor of mathematics at Perugia, Rome, Naples, Pisa, and Venice` |
| Geijsbeek 1914 | `professor of mathematics at Perugia, Rome, Naples, Pesa and Venice`（`Pesa` 即 Pisa，**OCR 讹字照录**） |

★ **三份的交集只有 Rome 与 Venice。** Perugia／Naples 只见于后两份；Milan 只见于 Rouse Ball。
★★ Rouse Ball 对 Milan 那一条给了别人没给的细节：
`at the last-named city he was the first occupant of a chair of mathematics founded by Sforza`。
★★★ **产物里给城市名单时必须说是按哪一份给的。**

## ★★★ T3：名字有多种形式——**这一条直接关系到检索**

来源：src-0af54aee74c3 src-1cc77dd0a82f

Rouse Ball 1908：

> Lucas Pacioli, sometimes known as Lucas di Burgo, and sometimes, but more rarely, as Lucas
> Paciolus, was born at Burgo in Tuscany about the middle of the fifteenth century. We know little
> of his life

而瓦萨里用的是第四种：**`Fra Luca dal Borgo`**（见 `04-external.md`）。
Catholic Encyclopedia 的词条名是第五种：**`LUCAS PACIOLI (Paciuolo.)`**。

★★★★ **五种形式**：`Luca Pacioli` / `Lucas di Burgo` / `Lucas Paciolus` /
`Fra Luca dal Borgo` / `Paciuolo`。
**只按一种去检索，会漏掉大部分材料**——瓦萨里那两段指控就是按 `dal Borgo` 写的。
★ 与 Gantt #156 的 `Laurence`／`Lawrence` 是同一族的问题，**但这里是五种不是两种**。

## ★★ T4：与达·芬奇同在米兰

来源：src-11b5ad20c3cc

> with some co-operation on the part of Leonardo da Vinci. It

Catholic Encyclopedia 同段还写：他与达·芬奇一同在米兰、在「摩尔人卢多维科」的宫廷，
**直到法国人入侵**；晚年在佛罗伦萨与威尼斯。

★ **本条只有一处出处。** Rouse Ball 提到 Milan 与 Sforza，但**没有提达·芬奇**。
★★ 「Leonardo 为《De divina proportione》画插图」是通行说法，
**而本库这两份二手源都没有直说这一点**——**产物里不许把通行说法当本库证据。**

## ★ T5：三部作品的出版年

来源：src-11b5ad20c3cc src-0af54aee74c3

- 《Summa》：**威尼斯 1494**（两份来源一致）
- 《Divina Proportione》：**威尼斯 1509**（Catholic Encyclopedia）
- 他校订的欧几里得：**1509 威尼斯**（Catholic Encyclopedia：`His edition of Euclid was
  published in 1509 in Venice`）
- Rouse Ball 另提两部几何小册子：**1508 与 1509 印于威尼斯**

★ **这是本道最稳的一层**——两份来源在年份上不打架。
★★ 但那部欧几里得**已判「不入库」**（正文实质是欧几里得的），见 `meta.json` 的 `disputed_works`。

## Candidate Claims

**T-A（fact，可成条）**：**他的卒年在本库的三个来源里是三个不同的答案，
且学界前后修正过。**
- 证据 A：Catholic Encyclopedia 1911 `died probably soon after 1509`
- 证据 B：Rouse Ball 1908 `died at Florence about the year 1510`
- 证据 C：现代共识 1517（**本库无来源支撑，来自 Wikidata Q87620**）
- 语境：**百科词条 / 数学史专著**，两个语境 → 达标
- ★★ **本条的价值不在于给出卒年，在于说明这个数不确定。**

**T-B（fact，可成条）**：**他的名字在一手与二手材料里有至少五种形式。**
- 证据 A：Rouse Ball 三种（`Lucas Pacioli` / `Lucas di Burgo` / `Lucas Paciolus`）
- 证据 B：瓦萨里 `Fra Luca dal Borgo`
- 证据 C：Catholic Encyclopedia 词条名 `LUCAS PACIOLI (Paciuolo.)`
- 语境：数学史专著 / 传记 / 百科，三个语境 → 达标
- ★ **用处是检索与同名护栏**，不是关于他本人的断言。

**T-C（fact，★ 只有一处出处）**：**任教城市名单三份来源没有两份相同，交集只有 Rome 与 Venice。**
- ★ 三份都在库、可逐字核；**但「哪一份对」本库判不出来**。

## Contradictions and alternative explanations

- **卒年的三个值不是「谁错了」**：1908／1911 的作者看不到后来的档案考证。
  **产物里把它写成「学界修正过」比写成「有人写错了」准确。**
- **任教城市的差异可能是取景不同**：Rouse Ball 写的是「lectured on mathematics」，
  Catholic Encyclopedia 写的是「professor of mathematics」——
  ★ **讲学与任教席位不是一回事**，两份名单未必真的冲突。**本库判不出来。**
- **Geijsbeek 1914 那一份是英译者的导论**，与 Catholic Encyclopedia 高度相似
  （只差 `Pisa`／`Pesa` 一个 OCR 讹字）——★ **很可能不是独立第三处**，
  **计数时不该当两处证据。**

## Unknowns and source gaps

- **生年只有「十五世纪中叶」这种模糊说法**，两份来源都不给具体年份。
- **入修会的年份、任教的起讫年、在米兰的具体年份：全部没有。**
- **本道全部建在两份 20 世纪初的二手工具书上**——**没有任何同时代的传记材料。**
- ★ 与达·芬奇的合作**只有一处出处**，且**没有一处说 Leonardo 画了插图**。

## Proposed evaluation-set candidates

（本轮未提名。提名须在隔离样本划定之后、且不打开正文。）

## Handoff to adjudication

- Validate origin independence and evaluation-set separation before promotion.
- ★★★★ **本道给下游的第一条**：**卒年与任教城市都不是确定值。**
  给这两样时必须说明是按哪一份来源给的，**并说明另有不同说法**。
- ★★★ **名字五种形式**必须进 `facts.md` 与同名护栏说明——
  瓦萨里那两段指控是按 `dal Borgo` 写的，只搜 `Pacioli` 会整段漏掉。
- ★★ **Geijsbeek 1914 的城市名单很可能转抄自同一来源**，不许当独立第三处。
- ★ **「Leonardo 画了插图」是通行说法，本库两份来源都没直说**——不许写进产物。
