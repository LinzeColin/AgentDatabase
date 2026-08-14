# Michelangelo #185 返工：19 条硬错的形状，以及**为什么不能直接开搜**

**2026-08-14**｜合成门现跑 `passed=False`，**硬错 19 条**（与 START-HERE 记的 19 一致）：

    claim.insufficient-support     8   八条断言各只有一处支撑
    claim.non-independent          8   同八条：证据簇不足两个
    claim.model-minimum            1   mental models **1 < 2**
    claim.heuristic-minimum        1   heuristics **0 < 3**
    claim.insufficient-contexts    1   clm-504ac43c44d3 语境不足两个

现有断言 22 条：`fact 13｜work-method 5｜mental-model 1｜blind-spot 1｜boundary 1｜value 1`。

## 缺第二处的八条，各挂在哪一份

| 断言 | 类 | 唯一源 |
|---|---|---|
| `clm-57132310d198`（估工期与花费：两个数对不上就把差额说出来） | work-method | `src-34bb6d56038a` |
| `clm-584dece9bffe`（不内行的事先说不内行，再请第三方估价对照） | work-method | `src-34bb6d56038a` |
| `clm-a928f1063ac7`（远程付款：回执上没付款人姓名就不算付讫） | work-method | `src-34bb6d56038a` |
| `clm-2a3b37136bc9`（钱的小数说到底） | mental-model | `src-34bb6d56038a` |
| `clm-f7a2ee35980a`（下施工指令：先给尺寸再给判据，回去看基座） | work-method | `src-43c819c03a55` |
| `clm-f7f67f29f5af`（同一场地多工种：下一工种进场时场地是否真空着） | work-method | `src-8539ad71569a` |
| `clm-504ac43c44d3`（直接说对方一直误解他） | blind-spot | `src-8539ad71569a` |
| `clm-7cee3cb6b511`（对家人要品行不要成就） | value | `src-8999a5688bea` |

**五条 work-method 里四条来自同一批书信。** 这就是要先量的东西。

## 语料面（现算，不是抄台账自述）

    台账 56 行｜train 47 / holdout 9｜正文读得到 **56 / 56**
    train 词数 **3,516,622**｜tier: P1 37 / S1 16 / U 3

按题名归并成 **44 部作品**，其中题名含 letter/lettere/briefe 的 **6 部、954,457 词**。
乍看「第二处独立作品有 5 部可取」。**这个读法是错的。**

## ★★ 六部书信作品，两两包含率量下来塌成一部

用 6-gram 包含率（`|A∩B| / min(|A|,|B|)`，**不用 Jaccard** ——
Jaccard 看不见「小的整个在大的里面」[[jaccard-cannot-see-a-short-text-inside-a-big-one]]）：

| A | B | 包含率 | 判 |
|---|---|---:|---|
| `buonarroti_le_lettere…` | `Le lettere di Michelangelo Buonarroti` | **0.6866** | 同一部 |
| `La lettere di Michelangelo Buonarroti` | `Le lettere di Michelangelo Buonarroti` | **0.6541** | 同一部 |
| `buonarroti_le_lettere…` | `La lettere di Michelangelo Buonarroti` | **0.5846** | 同一部 |
| 意文任一 | `Die Briefe des Michelagniolo Buonarroti`（德） | **0.0000** | **判不了** |
| 意文任一 | `Michelangelo Gedichte und Briefe`（德） | 0.0002 | **判不了** |
| 意文任一 | `A record of his life as told in his own letters`（英） | 0.0006 | **判不了** |

**三部意文版是同一批书信。** 另三部与意文重叠恒为 0 ——
**而这正是译本的读数**，不是「内容独立」的读数。
[[cross-language-holdout-leak-is-invisible]]（拉丁原本与英译本 n-gram 重叠 0，重叠门安静放行）

⇒ **n-gram 这把尺子在跨语言时判不了独立性。** 6 部很可能塌成 1 部，
但**现在还不能下这个结论** —— 要换一把尺子。

## 本轮唯一试过的一次搜索，四个候选全是误报

`find_second_evidence.py --claim clm-a928f1063ac7 --pattern "quietanz|ricevut|a chi.{0,20}pag|…"`
（工具自测先过：正对照命中、反例判 3 —— 那条纪律有效）

    搜索面：train 有正文 47 份 → **29 部独立作品**（工具自己的口径），已排除已引源与 holdout
    候选 42 处，落 4 部

四条逐条打开读完，**全是误报**：命中的 `ricevuto/ricevuta` 在那四部诗集与序跋里
都是「收到（一封信 / 一首诗 / 一份稿）」，**没有一处是付款回执**。
工具自己在输出里写着「松正则的命中大多是误报，每条都要打开读」——这次它是对的。

## 下一轮**必须先做**的那一件（不做就是在假搜索面上搜）

**换尺子判六部书信的独立性：按书信身份比，不按 n-gram 比。**
每封信有收信人＋日期，抽出 `(收信人, 年月)` 的集合再比 —— 译本的这个集合与原本**相同**，
而真正独立的辑本会有原本没有的信。可取面因此变成：

    独立可取面 = 德/英三部里 **意文三部没有的那些信**

量出来是 0 → **Michelangelo 属于延后类⑦「方法证据全部汇到一部作品」**（同 Pacioli #161），
19 条里至少 16 条结构性修不了，该记延后而不是继续搜。
量出来 > 0 → 那批信就是第二处证据的可取面，逐条读。

★ **不许跳过这一步直接搜。** 跳过就会像本轮那样，
在一个「29 部独立作品」的**虚假搜索面**上搜 —— 那个 29 是按 id 数的，
而其中至少 3 部（可能 6 部）根本是同一批书信。
[[two-source-ids-is-not-two-evidences]]｜[[bibliographic-proxy-instead-of-the-measurement]]

## 复现

```bash
Q=CodexSkills/registry/codex/persona-distiller/scripts/quality_check.py
W=CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-michelangelo-185/workspaces/michelangelo-buonarroti
python3 "$Q" "$W" --phase synthesis      # rc=1，errors 19 条
# ★ 是位置参数 target，**不是 --workspace**（我第一次就写错了）
```

---

# 续：**换的那把尺子也坏了** —— 「87 个意文没有的日期」几乎全是我造出来的

同日稍晚。按上面写的「抽 (年, 月) 集合比」做了，正对照先过
（1507 年 2 月那封信：意文 `8 di febbraio 1507`、德文 `1507 i. Februar`，**两边都抽到**）。

    三部意文合并后 490 个 (年,月)
    Die Briefe（德）           自有 297｜意文没有的 **70**
    Gedichte und Briefe（德）  自有  31｜意文没有的 **3**
    A record of his life（英）  自有 235｜意文没有的 **14**
    ⇒ 合计 **87**

**这个 87 不能用。** 里面有 `1475-02`、`1479-03`、`1481-01` ——
他 **1475 年 3 月才出生**，四岁六岁不会写信。按纪律抽 8 处打开读上下文：

| 部 | (年,月) | 实际是什么 |
|---|---|---|
| Die Briefe | 1475-02 | 书末 **ZEITTAFEL（年表）** ＋ 编者序 `Berlin, 14. Februar 1907. Karl Frey` |
| Die Briefe | 1496-03 | 同上，年表相邻行 |
| Die Briefe | 1508-10 | 同上（`1507. 21. September` / `12./14. Oktober` 那一列） |
| Die Briefe | 1512-02 | 同上 |
| A record | 1479-03 | 编者注：`Giovan Simone Buonarroti was born on March 11th, 1479` |
| A record | 1492-04 | 编者注：`Lorenzo died on April 8th, 1492` |
| A record | 1529-06 | **窗口跨行错配**：`January 6th, 1529` 与隔壁信头 `June 26th, 1531` 撞在一起 |
| A record | 1537-11 | 一张**收据**：`…the amount due for the two months, October and November`，年份来自隔壁 `1537` |

**8 处里 0 处是「意文没有的信」。** 真因：我的 ±90 字符窗口
在**年表**这种「一列年、一列月」的版面上，会把任意年配上任意月。
[[a-signal-that-both-overfires-and-underfires]]｜[[regex-must-clear-the-corpus-language]]

⇒ **这一轮没有证明德/英两部含有意文没有的信，也没有证伪。两把尺子都不成立。**

## ★★ 但抽样顺带露出一件真的

英文那部题名是 `A record of his life as told in his own **letters and papers**`。
1537-11 那处读出来是**一张收据原文**：

> Michelangelo has received from Messer Francesco Durante of Piacenza the sum of
> ninety-one and a third crowns in gold, being the amount due for the two months,
> October and November.

**这是 ricordi（账记/收据），不是书信** —— 意文那三部是 `lettere`，按题名根本不收这类。
而 `clm-a928f1063ac7` 要证的正是「远程付款：回执上没付款人姓名就不算付讫」。

⇒ **下一轮的可取面不是「意文没有的信」，是「英文那部里的 papers 部分」。**
判它是不是独立证据，要问的是：**这些 ricordi 在意文三部里有没有**，
而不是比日期集合。

## 下一轮的做法（比上一版收窄）

1. 在 `A record…`（`src-8539ad71569a`）里定位 **papers/ricordi 段**
   （标志：第三人称 `Michelangelo has received` / `Ricordo` 式记账句，不是书信的第二人称）。
2. 逐段拿原文去意文三部里搜（**用意文对应词，不是英译词** ——
   跨语言 n-gram 恒 0，这条已经栽过一次）。搜不到 ⇒ 它是独立材料。
3. 只有到这一步才谈得上给 `clm-a928f1063ac7` 补第二处证据。

★ 本轮**两把尺子都坏了**，一把（n-gram）跨语言恒 0，一把（年月对）在年表上乱配。
**两次都是「先量再搜」这条纪律拦住了假发现** —— 如果直接开搜，
我会在一个 29 部的虚假搜索面上、拿一堆年表日期当「新信」报上去。

---

# 续二：**证据有两处，但装不进去** —— 问题不在语料，在证据模型

按上一节写的做法走完了。结论比预想的清楚，而且**不是「找不到」**。

## 第一步：英文那段是意文那封的译文（证伪了自己上一节的猜测）

`A record of his life…`（`src-8539ad71569a`）里那段

> It is already fifteen days since I sent certain moneys to Lodovico in Florence
> with certain instructions, and I have never had a reply… **Tell Lodovico, therefore,
> to let me know if he has received them, and if he has done as I asked**

拿意文对应词回搜，**四部意文书信集全部命中同一封**：

> LIII. A Buonarroto… Bologna, 24 di febbraio (1507).
> `Io mandai cierti danari costà a Lodovico con cierta comessione già quindici dì sono
> e mai non ò avuto risposta. Somi molto maravigliato: però di' a Lodovico, che m'avisi
> se gli à ricevuti, e se à fatto quello gli comessi: m'avisi a ogni modo`

⇒ **英文那部是译本，不是独立材料。** 上一节「papers 部分可能是可取面」这个猜测，
在这一条上**被自己的实测证伪**。（`Michelangelo has received` 全书只 1 处、`Ricordo` 9 处，
papers 的量本来也撑不起来。）

## 第二步：★★ 但真的搜出了第二处 —— 另一封信，隔 48 年

同一次搜索命中了**另一封完全不同的信**：

> CCLXXVII. A Lionardo di Buonarroto Simoni in Firenze. **A dì dieci di maggio 1555.**
> `Io ti scrissi circa un mese fa che tu dessi dua scudi d'oro alla madre di Masino da Macìa…
> **Non ò mai avuto risposta. Àrei caro m'avisassi se avesti la lettera e se gli à' dati o sì o no.**`

与 1507 那封对照：

| | 1507-02-24 | 1555-05-10 |
|---|---|---|
| 收信人 | 弟弟 Buonarroto | 侄子 Lionardo |
| 事由 | 寄钱给父亲 Lodovico ＋ 一项交代 | 让侄子代付 2 金斯库多给一个工人的母亲 |
| 动作 | 没回音 → 要求确认**收到没有**＋**照办没有** | 没回音 → 要求确认**收到信没有**＋**给了没有，是或否** |

**隔 48 年、不同收信人、不同笔钱、同一套动作。** 这是两次独立的行为，不是一处证据数两遍。

## 第三步：装不进去 —— 两封信在同一部作品里

含 1555 那封的四个 source_id，两两 6-gram 包含率：

    src-34bb6d56038a ⇄ src-6094206729a1   0.6866
    src-34bb6d56038a ⇄ src-8999a5688bea   0.5930
    src-34bb6d56038a ⇄ src-14161091ddb3   0.5394
    src-6094206729a1 ⇄ src-8999a5688bea   0.5234
    src-14161091ddb3 ⇄ src-8999a5688bea   0.5593
    src-6094206729a1 ⇄ src-14161091ddb3   0.4663

**四个全是同一部书信集的不同扫描件**（其中两个题名一模一样）。

而判据是**纯结构**的（`quality_check.py` 372–381 行，现读）：

    insufficient-support  ← len(set(claim['source_ids'])) < 2
    insufficient-contexts ← len(set(claim['contexts'])) < 2
    non-independent       ← len(set(claim['evidence_clusters'])) < 2

它数的是**去重后的字符串个数**，不验这些 id 是不是同一部书。
⇒ 只要把两个 id 填进去，门就绿了 —— **而那正是 ㊸ 判过的「两处证据其实一部作品」。不做。**

## ⇒ Michelangelo 的形状，与 Brandeis **不是同一件事**

| | Brandeis #172 | Michelangelo #185 |
|---|---|---|
| 搜过之后 | **确实没有第二处**（6 轮，逐条读完全是别的题材） | **有第二处**，且是独立行为（隔 48 年） |
| 卡在哪 | 语料里没有 | **证据模型装不下**：一封信不是一个 source |

**根因：证据的单位是「卷」，而书信的自然单位是「封」。**
一部书信集 = 一个 source_id = 一个簇，于是「1507 那封」和「1555 那封」
在模型里塌成同一处。这是**用书目代理独立性**的老毛病。
[[bibliographic-proxy-instead-of-the-measurement]]｜[[two-source-ids-is-not-two-evidences]]

## 我的处置（自裁，不上交）

**不重切语料。** 把书信集按「封」重新入库会改变每个人物的
源计数 / 一手占比 / 道数 / 各档阈值 —— 全库有书信的人物都要重算，
而 ㊵ 已裁「已判分即冻结」。**为一个人改全库的证据模型，代价远大于收益。**

⇒ **Michelangelo 记延后类⑦「方法证据全部汇到一部作品」**（同 Pacioli #161），
但**理由与 Pacioli 不同，必须写清楚**：Pacioli 是证据真的只有一部书；
Michelangelo 是**证据有多处而模型只有一个格子**。

★ 这条差别不写清楚，下一个人会以为「Michelangelo 的语料不够」而重新去抓源 ——
**语料是够的，3,516,622 词、56 份全读得到。不够的是格子。**

## 还没做完的（下一轮从这里起）

本轮只把 `clm-a928f1063ac7` 一条查到底。**另 7 条还没逐条走这个流程**，
其中 4 条（`clm-57132310d198`／`584dece9bffe`／`2a3b37136bc9` 同挂 `src-34bb6d56038a`，
`clm-7cee3cb6b511` 挂 `src-8999a5688bea`）**大概率是同一形状**，
但 **「大概率」不是实测**，不许照抄结论。另 3 条挂在诗集与英译本上，形状可能不同。
