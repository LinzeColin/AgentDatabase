# External accounts

## Scope and assigned sources

**本道分到 11 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-a2eb00fe307e` | 1867 | S1 | Essai sur les oeuvres et la doctrine de Machiavel |
| `src-28b88a9e7e14` | 1878 | S1 | Niccolò Machiavelli and his times |
| `src-402c44d1a4a1` | 1878 | S1 | Niccolò Machiavelli and his times |
| `src-4bf15fe30dbb` | 1878 | S1 | Niccolo Machiavelli and his Times, Vol. I |
| `src-6f8aba6067ce` | 1878 | S1 | Niccolò Machiavelli and His Times |
| `src-385f5ba4714f` | 1883 | S1 | Niccolò Machiavelli and His Times |
| `src-adc11f95eade` | 1883 | S1 | Niccolò Machiavelli and His Times |
| `src-bd9990100dd4` | 1891 | S1 | The life and times of Niccolo Machiavelli v 1 |
| `src-bf853d07951e` | 1891 | S1 | The life and times of Niccolo Machiavelli v 2 |
| `src-71d023632e39` | 1892 | S1 | The life and times of Niccolò Machiavelli |
| `src-c337cd6aef37` | 1916 | S1 | Three prose writers of the Italian renaissance |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` **且抽取成功**的行。


★ **另有 1 份取回来是坏的，不计入上面的份数**（`extraction_status: failed`；保留在台账里是为了别再抓一次）：
- `src-213511a1f84a` Life And Times Of Niccolo Machiavelli —— 两把独立的尺子都判它不可用：① **天城文字符 1,114,949 / 全文 2,674,715 = 41.68%** —— OCR 把拉丁字母误识成天城文，采样原样如 `क्न 2777 4
## Source-linked observations

**★ 说话人不是他**：本道 12 份全是二手（`tier=S1`），
下面这条的说话人是传记作者 **Villari**（《Niccolò Machiavelli and his Times》1878）。

### O-1 · 后世传记为他的师承**改错**，靠的是生卒年相减

> `The origin of this mistake is, because after Marsigli’s death, Vangelista da Pisa and Girolamo da Napoli taught at St Spirito, and Manetti studied under them.`
> —— `src-4bf15fe30dbb` @218785

★ 前文 Villari 摆出两个日期：Luigi Marsigli 生约 1330、卒 1394-08-21；
Manetti 生 1396——`belongs to a later generation`，**两人不可能是师生**。
然后才解释误传怎么来的：Marsigli 死后，另两人在同一处任教，Manetti 从的是他们。
⇒ **关于他的记载里，最先被订正的是年代，不是评价。**
这也说明本项目引用二手时的口径：`external` 那一道回答「别人怎么看他」，
**说话人必须写明**。
## Candidate Claims

Pending.

## Contradictions and alternative explanations

Pending.

## Unknowns and source gaps

Pending.

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
