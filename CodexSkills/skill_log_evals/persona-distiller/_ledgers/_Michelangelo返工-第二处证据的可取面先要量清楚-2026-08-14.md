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
