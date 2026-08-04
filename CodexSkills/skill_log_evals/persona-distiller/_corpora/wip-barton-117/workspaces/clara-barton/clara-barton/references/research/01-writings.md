# Writings and systematic works

**本路 44 份（P1 21／P2 22／S1 1）。P2 占一半——那是同一部书的多次扫描与多个印次，
不是四十四部著作。数份数会高估她的著述量四倍以上。**

## Scope and assigned sources

train 分割 44 份，**实际著作只有五部上下**，其余是重复扫描与后印。
按部归并（同名同书的多份合为一组）：

| 著作 | 份数 | P1 |
|---|---:|---|
| `The Red Cross: A History…`（1898） | 4 | src-b5bcb1ed5c47 |
| `The Red Cross in Peace and War`（1899，另有 1906／1910／1912 印次） | 7 | src-b721975d568d |
| `A Story of the Red Cross`（1904，另有 1915／1917／1918／1928 印次） | 8 | — |
| `The Story of My Childhood`（1907） | 3 | — |
| `Philanthropy at Johnstown`（1889） | 1 | src-abe3e0e313a5 |

**这一层归并必须做在断言之前**：`A Story of the Red Cross` 有 **8 份**扫描，
若按份计权，她一生等于写了同一件事八遍。

## ★★ Source-linked observations 一：署名与版权不在同一个人名下

`The Story of My Childhood`（1907）扉页与版权页逐字照录：

```
THE   STORY  OF   MY
CHILDHOOD
BY
CLARA   BARTON
NEW    YORK
THE    BAKER  &  TAYLOR    CO.
1907
…
Copyright,    1907,    by
The    Journal   Publishing    Co.,
```

**扉页署名是她，版权归 The Journal Publishing Co.**——该书先在刊物连载，
版权因此落在出版方。

对比 `The Red Cross in Peace and War`（src-b721975d568d）：

```
Copyright,   1898,  by   Clara    Barton
```

**这一部的版权在她自己名下。**

**两件事要分清**：**署名**证明的是「她写的」，**版权页**证明的是「谁持有权利」。
本项目只用前者做归属，用后者做权利依据；**二者不一致时不许互相顶替**。
（对 PD 判定无影响：她 1912 卒，两部都已过保护期。）

## Source-linked observations 二：她的著作是「事务报告」体，不是回忆录体

`Philanthropy at Johnstown`（1889）、`Report: America's Relief Expedition to Asia Minor`
（1896，见 05 决策路）与两部红十字史，形态一致：**先记事由、再记调度、最后记账目**。
这与 03 表达路里她把演讲称作 `render my account`（交账）是同一种自我定位。

**唯一的例外是 `The Story of My Childhood`（1907）**——
写童年，不是交账。**它是本人物风格判据里最该单独对待的一部。**

## Contradictions and alternative explanations

- **后印次可能有修订。** `The Red Cross in Peace and War` 有 1906／1910／1912 三个后印，
  1912 印次已在她卒年（1912-04-12）——**该印次是否经她过目无从查证**，
  台账已标 `POSTHUMOUS` 降 P2。**逐字引文只取 1899 初版那一份。**
- 「事务报告体」这个观察建立在**五部里的四部**上，样本小；
  若 03 路的讲稿也呈同型，才可升为断言。

## Unknowns and source gaps

- **未取到 LOC Letterbooks 52 卷**（图像已数字化、无转录；www.loc.gov 返 Cloudflare，
  **未绕过**）。它属 02 对话路，但其中的公务信函也会补强本路。
- **她的国会证词未单独取到。**
- 各后印次之间**未做逐字比对**，因此「后印有无修订」目前是未知而非否定。

## Proposed Holdout cases

不从本路提取 holdout。**本路 P2 密度最高，任何按篇名分组的 holdout 都极易与 train 重叠**
——第一次选 holdout 时就是栽在这里（`A Story of the Red Cross: Glimpses of Field Work`
与 `A Story of the Red Cross` 是同一本书的两种著录题名，覆盖 89.4%，硬失败 6 条）。
现 holdout 改为四册单副本日记，硬失败 0。

## Handoff to adjudication

1. **断言层必须按「部」计权，不按「份」计权。**
2. **逐字引文只取每部的 P1 初版**，后印与重复扫描（P2）不取。
3. `The Story of My Childhood` 与其余四部**分开处理**：前者是自传体，后者是报告体。
