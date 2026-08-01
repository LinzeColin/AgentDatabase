# Steinhardt #98 —— holdout 重合的逐条裁定（2026-08-01）

`check_holdout_overlap.py` 报 **硬失败 0 / 待人工核 1**。规则要求逐条核完再往下走，
判据是「同场活动的不同报道可接受，**转载不可**」。以下是裁定与依据。

## 三份 holdout 的实测

| holdout | 最高覆盖 | 对手 | 裁定 |
|---|---:|---|---|
| `ms_2019_cnbc_accused_nyt_report_statement.txt` | **19.5%** | `ms_2021_cnbc_surrenders_stolen_antiquities.txt`（train） | **转载，部分污染** |
| `ms_2011_cnbc_buffett_snow_job_quotes.txt` | 4.9% | 同上 | 可用 |
| `ms_xxxx_globes_globes_interview.txt` | 0.00% | — | 可用 |

## 19.5% 那条：不是站点模板

我把 96 条重合 8-gram **全部列出来**核对，而不是抽样看开头——
第一眼的印象（「两篇都是 CNBC，重合的应该是导航栏」）**是错的**。

**属于站点模板的只有约 12 条**：
`skip navigation markets business investing tech politics video watchlist investing club pro livestream menu key points`、
`choose cnbc as your preferred source on google and never miss a moment from the most trusted name in business news`。

**其余 80 余条是实质内容**，逐字相同：

- `steinhardt s sense of humor can be insensitive and he has apologized for the unintended bad feelings his remarks have caused`
- `the steinhardt foundation for jewish life called the times report intentionally defamatory`
- `made sexual requests when the women sought support from the philanthropist`
- `steinhardt appeared in two sexual harassment lawsuits but was not named as a defendant in either case`
- `a statement from the billionaire who denies ever trying to touch anyone inappropriately`

**2021 年那篇文物报道里整段复用了 2019 年那篇性骚扰报道的正文。**
这是 CNBC 复用自家旧稿，属于**转载**，不是「同场活动的不同报道」。

## 处置

**不把这份 holdout 从 holdout 里拿出来，也不重新抽样。**
重抽会踩 RUNBOOK 第二十八种——holdout 在被读过之后才指派，于是它验证不了任何东西。
我已经读过这一段了，现在换一份等于自己制造那个缺陷。

**改为限定它的用途**：

- ⛔ **不得从 2019 年指控相关内容出 known 题**——那段内容在 train 里逐字存在，
  出成题目测不出任何东西。
- ✅ known 题全部从另两份干净 holdout 出
  （`ms_2011_cnbc_buffett_snow_job_quotes.txt` 4.9%、`ms_xxxx_globes_globes_interview.txt` 0.00%）。
- 该 holdout 的其余部分（若有 train 中不存在的内容）本轮**一律不用**——
  逐段划分干净区与污染区的成本高于它能提供的价值。

## 顺带记下的一条检查器局限（不是本轮阻塞）

`check_holdout_overlap.py` 的样板过滤阈值是「出现在 **>5 份** train 源中的 shingle」。
CNBC 在 train 里只有 2–3 篇，**它的站点模板因此过不了这个阈值，被算进了覆盖率**。
本轮那 19.5% 里约 12 条是模板，实质重合应低于该数——
**但结论方向不变**（实质重合仍然存在且是转载），所以本轮不改判据。

若将来某人物的 train 里某站点只有 1–2 篇而模板很长，这个阈值会把纯模板重合
放大成「待人工核」，制造假警报。**改法是按「同域名」而非「>5 份」过滤模板**，
记为下一版候选，本轮不动——现在改会让本轮的裁定失去可复现的基线。

---

# 附：`check_claim_coverage` 剩余两条的裁定（2026-08-01）

修完真缺陷后仍报 2 条。**逐条核完，两条都是误报**，理由如下。
（该工具自己的输出就写着「未检查，不等于通过」；同理，**报出来也不等于有问题**。
Maeda 一轮它的姊妹工具 `check_absence_claims` 报的 13 条里有 2 条是假的，错误率 15%。）

## `clm-ba1b0338463b` 缺 `1994` —— 误报

「1994」在该断言里**只出现在一句禁令中**：

> 产物不得把这个空缺填成「他认为 1994 年债券是最糟的决定」。

这是一句**关于不许写什么的元陈述**，不是一个需要来源支撑的断言。
工具按「关键实体是否出现在被引来源里」判定，认不出这个句法角色。

## `clm-b7ec12fd9ed6` 缺 `1550` —— 误报

`1550` 是**我自己算出来的数**，语料里当然没有，**它不该有**。
断言的内容正是「第三方那条算式算错了」，而 1550 是重算的结果。

**已实测复核**：`1.3 ** 28 = 1550.3`，10 万 × 1550.3 ≈ 1.55 亿。
第三方给的 4800 万对应年化 24.7%，即他自陈的净 25%——作者把毛收益率安到了净倍数上。

**派生值与引用值是两类东西。** 要求派生值出现在来源里，等于要求「不许算」。

## 结论

真缺陷 2 条（父亲名、生日月日）**已修**；误报 2 条**不修**。
`check_claim_coverage.py` 退出码仍为 1——**本轮不为了让它变绿而改判据**，
按必读的规矩：达不到门就选诚实退路并写台账，绝不为凑数放宽判据。

**下一版候选**：给该检查器加两条豁免——
① 实体只出现在「不得 / 不许 / 记为失败」句式内的，不计入；
② 断言自称是重算结果的（正文含「算下来 / 按 X 复利 / 我算了一遍」），派生值不计入。
本轮不动，动了这一轮的裁定就失去可复现的基线。
