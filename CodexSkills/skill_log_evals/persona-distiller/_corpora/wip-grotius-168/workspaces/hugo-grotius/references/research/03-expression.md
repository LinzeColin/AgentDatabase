# Expression DNA and micro-behavior

## Scope and assigned sources

**本道分到 2 份（train split）**：

| source_id | 出版年 | tier | 题名 |
|---|---|---|---|
| `src-fd2c87dfecb9` | 1637 | P1 | Hugonis Grotii Poemata（拉丁诗全集：Sacra／Patria／Nuptialia、哀歌、杂咏、铭辞等） |
| `src-50d9d5f3ff5e` | 1839 | P1 | The Adamus Exul of Grotius, or The Prototype of Paradise Lost |

★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；只投影 `split == train` 的行。

## Source-linked observations

### 一、★★★ Poemata 卷末 **4.2% 是别人写给他的**——量声口前必须切掉

`src-fd2c87dfecb9`（Poemata 1637）题名页自己就写着这一段的存在（@611 附近）：
`cum amicorum elogijs`（附友人题赠）。

边界可定位：全卷 10 处 `EIVSDEM` **全部落在 @735866–@766769**，
即文件的最后 4.3%。起点处（@735866）读作：

> `EIVSDEM ad HVGONEM GROTI^VM.`

（`GROTI^VM`＝`GROTIVM`；意为「由同一位作者，**致** Hugo Grotius」。）

| | 值 |
|---|---|
| 全卷 | 768,513 字符 |
| 附录区 | **@735866 – 768513 = 32,647 字符（4.2%）** |
| 该区特征 | 逐首都是他人作品，题名形如「某某 **ad/in** HVGONEM GROTIVM」 |

**这一段里的第一人称是别人的。** 早先逐处读过的 6 处 `HVGONIS GROTII` 里，
只有 1 处（@112657 `HVGONIS GROTII MYRTILVS…`）是他的作品标题，
另 4 处分别是父亲 Jan 贺他出生、Apollonius Scottus 悼其幼子、婚礼贺诗、他人评其剧
（逐处坐标见工作区根目录 `00-归属证据实测.md`）。

★ **对本道的直接后果**：任何「第一人称密度／声口」的计算，
**必须在 @735866 处截断**，否则把别人的「我」算成了他的。

### 二、这一道**没有任何可逐字引的本人原文**

本道两份：

| source_id | 是什么 | 逐字可引性 |
|---|---|---|
| `src-fd2c87dfecb9` | Poemata 1637，**他的拉丁诗全集** | 长 s 讹字率 **0.9193 → 不可用** |
| `src-50d9d5f3ff5e` | Adamus Exul，**Barham 1839 英译** | 英文面板 0.0000 → 干净，**但不是他的原文** |

→ **「他的诗怎么写」这件事，本项目只能通过 19 世纪的英译转述**，
拿不到一句他自己的拉丁诗行。写产物时不得把 Barham 的英文当成他的措辞。

### ★ 本节没做什么

- **没有读诗**。上面两条一条是位置分布 + 一处标题回读，一条是判据实测表。
- 附录区起点 @735866 是**按 `EIVSDEM` 的分布定的**，
  **没有逐首核对**该区之前是否也混入了他人作品——只核到「该区之后全是」。
- Barham 英译的忠实度**完全没查**。

## Candidate Claims

### C-07（**射程约束**，不是人物特征）量他的「声口」前必须先切掉两块

- **依据**：观察 一（Poemata 卷末 @735866 起 4.2% 是**别人写给他的**，
  标志 `EIVSDEM ad HVGONEM GROTI^VM.`）＋ 观察 二（另一份是 Barham 1839
  **英译**，不是他的拉丁）。
- **可检验**：任何第一人称／声口密度计算，若未在 @735866 截断，
  或把 Barham 的英文当成他的措辞，**结果作废**。

### C-08（形态，弱）他的诗作被同时代人当作**可以回赠的对象**

- **依据**：卷末附录里有父亲 Jan 贺其诞生、Apollonius Scottus 悼其幼子、
  婚礼贺诗、他人评其剧（逐处坐标见 `00-归属证据实测.md`）。
- **★ 弱在哪**：这是**编者（弟弟）选编的结果**，反映的是编者认为该收什么，
  **不必然反映他本人的交往**。→ **不进产物。**

## Contradictions and alternative explanations

### X-05 分界只靠一个标记词，**该点之前有没有混入没核过**

`EIVSDEM` 是我用来定界的唯一标志。若附录之外还有不带该标记的他人作品，
现在的分界就偏了——本道只核到「@735866 之后全是」，
**没核该点之前有没有混入**。

## Unknowns and source gaps

- **没有读诗**。两条观察一条是位置分布 + 一处标题回读，一条是判据实测表。
- Barham 英译的**忠实度完全没查**。
- 附录区起点是按 `EIVSDEM` 分布定的，**没有逐首核对**。

## Proposed Holdout cases

IDs only; research Agents must not inspect Holdout bodies.

## Handoff to adjudication

Pending.
