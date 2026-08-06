# Decisions, trade-offs and reversals

## Scope and assigned sources

Train-split、`dimensions` 含 `decisions` 的 **3 份**：

| source_id | 年 | 分档 | 载体 |
|---|---|---|---|
| `src-42286afc9366` | 1902 | P1 | Phil. Trans. 金银合金（**整版扫本，本道不引它**，见下） |
| `src-dfa437e17e2d` | **1895** | P1 | IMechE **合金研究委员会第三报告** |
| `src-5bf1098b8d50` | **1897** | P1 | IMechE **合金研究委员会第四报告** |

★★ **本道上一轮写的是「读完确认为空」。** 那是对的——当时只有 1902 那一份。
后两份是**按 06-timeline 挖出的年份补抓回来的**，本道因此从空变为有。

## Source-linked observations

### ★★★ ① 一段完整的取舍：**放弃 → 造仪器 → 重启 → 发表**

> `and certain experiments made by myself fourteen years ago had to be abandoned at
> the time for want of some means of measuring and recording the temperatures
> employed. The provision of the recording pyrometer, which was the direct outcome
> of the work of this Committee, enabled the investigation to be resumed ; and the
> results have recently been communicated to the Royal Society, and formed the
> subject of the Bakerian Lecture`
> —— `src-5bf1098b8d50`（1897 第四报告）

**四件事写在同一句里**：
1. **放弃**——约 1883 年的实验，**理由写明：没有测温与记录的手段**；
2. **补足**——记录式高温计，且注明它是**本委员会工作的直接产物**；
3. **重启**——工具到位后把研究接回来；
4. **交代去向**——结果已报皇家学会，并成为 Bakerian Lecture 的题目。

★ **放弃的理由不是「做不出来」，是「量不了」。** 这与 01-writings 观察 ①
（方法细节另发一份报告）是同一种处置：**先解决怎么量，再谈结论。**

### ② 方法选择写明「试过之后才定」

> `After some preliminary experiments, it was decided that the only satisfactory way
> of testing this would be by means of the electric welding apparatus of the
> Thomson-Houston Co., in which alternating c…`
> —— `src-dfa437e17e2d`（1895 第三报告）

**不是直接宣布用什么，而是先说做过预备实验，再说据此定下唯一可行的办法。**

### ③ Graham 第三次出现，这次是**作为论据**

> `but, as Graham showed, the rate of diffusion is greatly increased by a small rise
> in temperature`
> —— `src-5bf1098b8d50`（1897）

1876 为其文集作评（03-expression）／1896「把 Graham 的工作推进一步」（02-conversations）／
**1897 直接引 Graham 的结论当推理前提**。**三个年份、三份来源、三种用法。**

## Candidate Claims

- **取舍以「能不能量」为准**：因缺测温手段而放弃，因仪器到位而重启。依据：观察 ①。
- **方法选择先做预备实验**：定下办法之前先试。依据：观察 ②。
- **师承贯穿三十年且用法在变**：从作评 → 声称推进 → 引为前提。依据：观察 ③ + 另两道。

## Contradictions and alternative explanations

- 观察 ① 与 ② 各只有一处出处，但**分属两份不同年份的报告**（1895／1897），
  不是同一份里的自我呼应。
- ★ 观察 ① 的「fourteen years ago」= 约 1883，而 DNB 记他 1882 年起任
  Chemist and Assayer（04-external）。**两处独立来源在时间上对得上**，
  但**没有任何一处说这两件事有关**——不要读成因果。
- **委员会报告是集体文献**：`it was decided` 的主语是委员会还是他本人，**本道分不出**。
  观察 ① 用的是 `made by myself`，那一处是他自己；观察 ② 的 `it was decided` **不是**。

## Unknowns and source gaps

- 1902 那份（`src-42286afc9366`）是整版扫本，**本道不引**：
  里头那段方括号补记讲的是氯代／溴代萘重氮盐的有机化学，用第三人称 `The author is of
  opinion`——**属同版另一篇摘要，不是他的**。（上一轮差点把它算成他的写作习惯。）
- 第一、第二、第五报告（1891／1893／1899）标在 `writings` 道上，**本道未读**；
  若那三份里也有取舍记载，本道结论会更硬。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

（本轮未提名。）

## Handoff to adjudication

**本道从「已探明为零」变为「有三条观察」**，转折点是补抓回来的两份委员会报告。

带下去两条限制：
1. **集体文献的主语问题**——`it was decided` 分不出是委员会还是他；
   只有 `made by myself` 那一处能确定是他本人。
2. 五份报告里**只读了两份**（1895／1897），另三份未读。
