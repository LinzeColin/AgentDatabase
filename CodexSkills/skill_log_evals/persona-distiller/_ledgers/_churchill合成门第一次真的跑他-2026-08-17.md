# Churchill #191：合成门第一次真的跑了他 —— **36 条硬错，18 条是 claim 自己的**（2026-08-17）

`_被拒检的工作区-2026-08-14.md` 记过：他是 7 个拒检工作区里**唯一要处置的**那个
（有 13 条 claim、32 道盲判题，而合成门一次都没跑过他）。
今天把那句「没跑过」从**已知未知**变成**测出来的数**。

## 先订正 08-14 那份台账的一个前提

它写：「这件**不能靠补一个 SKILL.md 糊过去** —— 那是产物的一部分，要按流程写。」

**这句话对 `SKILL.md` 不成立。** 实测：

* `templates/target/SKILL.md.tmpl` 共 67 行，**只有两个占位符**：`{{SLUG}}`、`{{TARGET_NAME}}`；
* 全库现存 **38 份** `SKILL.md`，把 slug 与人名替换回占位符后，
  **38 份全部逐字相同**。

★★ **这个数我报了三版，前两版的「差异」全是我自己的归一化造成的**：

| 版本 | 我报的 | 「不同」的是谁 | 真因 |
|---|---|---|---|
| 一 | 36/38 | coffin、shewhart | 正则 `([^.]+)\.` 被中名缩写 `Charles L. Coffin` 在第一个点截断 |
| 二 | 37/38 | henry-gantt | 我优先取 `target_name`（Henry **Laurence** Gantt），而他的 SKILL.md 用的是 `name`（Henry Gantt） |
| **三** | **38/38** | 无 | 两个名字字段**都试**、**长的先替** |

**三次都不是数据不同，是我的尺子不同。**
同族：正则要过语料的形态关（中名缩写）、一个概念两个字段名。
[[my-checkers-are-mis-cut-six-times-in-one-day]]｜[[eval-artifacts-have-five-schemas]]

⇒ 它是 `init_target.py` 在**第 2 步**机械渲染的脚手架，不是手写产物。
  ★ 但 08-14 那句话背后的**担心是对的**：不许靠补文件让门变绿。
  下面这次实测恰恰相反 —— 补上脚手架之后门报得**更多**，不是更少。

## 怎么测的（仓里一个字节都没动）

把他的工作区整棵 `cp -R` 到 scratchpad，在**副本**里按模板渲染 `SKILL.md`
（slug=`winston-churchill`，name=`Winston Churchill`，3721 字节），
然后对副本跑 `quality_check.py . --phase synthesis`。
跑完 `git status --porcelain -- _corpora` = **0 行**。

## 结果：rc=1，**36 条硬错 / 14 种**

| 错误码 | 条数 | 归类 |
|---|---:|---|
| `structure.missing` | 10 | 脚手架缺失的后果 |
| **`claim.insufficient-support`** | **6** | **他的 claim 本身** |
| **`claim.non-independent`** | **6** | **他的 claim 本身** |
| **`claim.insufficient-contexts`** | **4** | **他的 claim 本身** |
| `route.invalid` | 1 | 脚手架 |
| `runtime.versioning-enabled` | 1 | 脚手架 |
| `identity.catalog-invalid` | 1 | 脚手架 |
| `source.minimum` | 1 | 其他 |
| `source.lane-coverage` | 1 | 其他 |
| `research.ledger-file-missing` | 1 | 其他（语料不在本机） |
| `corpus.structurally-infeasible` | 1 | 其他 |
| `research.lane-completion` | 1 | 其他 |
| **`claim.model-minimum`** | **1** | **他的 claim 本身** |
| **`claim.heuristic-minimum`** | **1** | **他的 claim 本身** |

    脚手架类 13 条｜**claim 本身 18 条**｜其余 5 条

样例：`clm-09e4178d7931 needs at least two supporting sources`。

## 这证实了 08-14 的判断，而且给了数

当时写「他的 32 道题**不该进判分队列**：判据没跑过的产物拿去判分，
等于用人力替判据把关」。今天量出来：**他 13 条 claim 上有 18 条硬错**，
其中 6 条是「支持源不足两个」、6 条是「证据不独立」。
**这不是补个文件能解决的，是他的断言层没做完。**

## 我**没有**动他的工作区，理由

补齐全部 17 项脚手架在机械上做得到（`init_target.py` 到临时目录再拷过来），
但那会造出一个**半初始化**的工作区：`route-manifest.json`／`identity-catalog.json`
本该由他真实的身份分面派生，机械生成的是空壳，
门会从「结构缺失」变成「结构存在但内容是假的」—— **比现在更难发现**。

★ 而 `init_target.py --force` 这条路**会先 `shutil.rmtree(target)`**
（他有 `meta.json`，那道 `--force refused` 的防线放行）。他 35 个文件全部已进 git，
所以破坏可恢复，但恢复之后还要手工把 35 份合回新脚手架 —— 代价不小且无收益。

⇒ **维持现状**：他继续留在拒检状态、继续不进判分队列，
  `check_scoring_ready.py` 继续每次点他的名。
  真要推进他，起点是**补他的断言层**（18 条硬错里 12 条是支持源与独立性），
  不是补文件。
