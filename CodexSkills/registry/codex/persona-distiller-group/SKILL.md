---
name: persona-distiller-group
description: The single user-facing entry point for evidence-grounded persona expertise. It routes one natural-language task to Single Expert, Small Team, Deep Team, or Swarm; loads each selected Persona Distiller product's real runtime payload; executes mandatory hypothesis, adversarial, independent review, adjudication, and synthesis controls; and returns one coherent artifact plus a Team Delta Card. The caller never chooses identities, weights, routing strategy, or team size.
---

# 人物蒸馏专家团队

## 产品边界

用户只调用本 Skill。`persona-distiller` 是上游人物质量工厂，不是普通用户入口：它负责研究、证据、人物模型、边界和交付 ZIP；本 Skill 负责人物资产准入、任务编译、稀疏路由、真实载入、协作执行、裁决、用户体验和净 Delta。

目标门是测量合同，不是设计时自我声明：整体 Delta、使用体感、MoE、路由、功能和质量目标均为 `>=95`；任何维度、任务切片、模板、框架或模型结果必须 `>=75`。没有 L4 生产盲测和独立 Verifier 时，只能写 `MARKET_LEADER_NOT_PROVEN`。

## 已测量的边界（2026-08-17 现算，不是设计声明）

上一节说「没有 L4 盲测就只能写 `MARKET_LEADER_NOT_PROVEN`」。
下面是**已经测出来的那部分** —— 每一条都能用仓里的判据重跑。
写在这里，是因为**读这份文档的人正是要据此决定用不用、怎么用**。

| 问题 | 实测 | 怎么重跑 |
|---|---|---|
| 路由比随机抽人好多少 | **2026-08-18 现算 @v0.0.0.32**：n≥5 团队模式 **+6.8 pp**（20 题，SE 2.6，离零 **2.62 SE**）；n=1 单专家 **+63.6 pp**（4 题，SE 21.6，离零 2.94 SE —— 命中率只能 0% 或 100%，**别把它当同一把尺**）。★ 旧值 +6.3／+64.0 是 08-17 词表修正前的读数，**这两个数会随词表漂**。★★ 增益的主要证据正是那张人工词表（见下一行）——**两行要一起读**。 | `measure_routing_discrimination.py`（**包外**） |
| 排序主要由什么驱动 | **`domain_match`**，而它由一张**人工关键词表**算出 —— 与路由合同「人工关键词不得成为冠军路由的主要证据」正面冲突。★ **份额随样本大幅漂，必须连样本一起读**（2026-08-18 现算）：`measure_routing_discrimination` **66.5%**｜单题（微服务重构 deep_team/14）**64.6%**｜名册标签 12 条**中位 46.6%**（最小 0.0%）。**更稳的口径是名次**：`domain_match` **当第一驱动的任务** —— 名册标签 12 条 **8/12 = 67%**，而 **72 道 oracle 全量（12 个题面）是 66/72 = 92%**、去变体 **11/12 = 92%**（★ **默认样本低估了问题**；★★ 我先前写的「前 12 条 12/12 = 100%」**只覆盖 3 个题面** —— oracle 文件按题面聚集排列，取前 N 条会重复计数，已订正）。★★ **因果**：合同想要的冠军证据是 C 层结果遥测，而遥测至今 **0 条**（C 要 ≥60 条）——关键词之所以主导，是因为 **C 从来没有打开过**，不是有人选它当冠军。 | `measure_routing_discrimination.py`（**包外**）／`scripts/check_keyword_table_is_not_the_main_driver.py`（**包内，带 rc 与回归地板**） |
| **「专家拒接不在其能力范围内的任务」拦得住谁** | **拦不住大部分人** —— 准入判的是 `max(task_similarity, packet_similarity, capabilities, scenarios, domain_match) < 门`，**任一项过线即可**，而其中 `packet_similarity` **与任务无关**：它比的是候选人卡片与 `work_packets` 的 `objective`，而那些 objective 是**固定套话**（「把用户目标编译为交付物、约束、成功条件和停止条件。」…）——五道内容毫不相干的题（微服务重构／40 公顷农场轮作／医院灭菌安全论证／供应商合同谈判／一串无意义词）编出的 14 条 objective **sha256 完全相同** ⇒ **102/102 人的读数跨题一个都不动**。规模（24 条名册标签、策略 B、门 0.17，2026-08-18 现算 @v0.0.0.36）：过准入的人里**其余四项全部低于门、唯一靠这条任务无关通道过线**的 —— 均值 **62.8%**，最坏一题 **97.6%（41/42 人）**。即这些人**没有任何与本题有关的证据**，却被判为「能接」。★★ **换成用户的单位再量一遍**（12 个独立题面、`auto` 档）：**最终坐进队伍**的 173 人里，**35 人（20.2%）**是唯一靠这条通道过的准入。而且分布不是平均的 —— **9 支 `small_team` 各占 36–45%**（10–12 人的队里有 4–5 人），**3 支 `deep_team`（24–28 人）与 1 支长题 `small_team` 都是 0%**。⇒ **题写得越短，队里靠任务无关通道进来的人越多** —— 而题短正是用户给的信息最少、最需要路由替他判断的时候。★ 顺带核过一处**产品是诚实的**：`routing_observability.selected_with_zero_task_relevance` 的`TASK_RELEVANCE_COMPONENTS` **正确地把 `packet_similarity` 排除在外**（四项＝`task_similarity`/`scenario_match`/`capability_match`/`user_value_match`）——**我先猜它把任务无关项算成了相关，读了源码发现猜错了**。它报 `[]` 与上面的 35 人不矛盾：它数的是「被选中的人里**四项全 0**」，口径不同。★ 射程：占比依赖样本，换成真实用户提问会不会变 —— **没量过**。★★ 顺带查出产品自身一处不一致：接受路径 `return` 时 `round(v, 4)`、拒绝路径原样返回 ⇒ 同一个读数两种精度（不影响判定，只坑读数的人 —— 我自己就被坑了一次）。 | `scripts/check_admission_signal_depends_on_the_task.py`（**包内，带回归地板＋正对照**） |
| 多少任务根本没有领域信号 | **在 72 道 oracle 上现算是 0%**（regression-24 0/24、development-48 0/48，两种口径都是 0：①分类器只认出兜底档 ②所有合格候选的 `domain_match` 全 0）。旧值 2/24=8%（更早 54%）是词表 92→290 词过程中的读数。★★ **但换一份样本就完全不同**：60 条**名册场景标签**上，只认出兜底档的占 **33/67 = 49.3%**。无域信号时排序落到 `currentness`，实测**低于随机抽人 1.7 pp**；route-plan 与执行合同会明写 `NO DOMAIN SIGNAL` | 同上 |
| 模式判对没有 | 任务包自带 72 道 oracle：**模式命中 25%**（12/48、6/24，**2026-08-18 现算 @v0.0.0.31**）；`single_expert` 与 `swarm` **一次都没被选中**；人数 `persona_target` **命中 0%**（中位偏差 +6 人）。★ 旧值 33%（16/48、8/24）**是 `设计`/`design` 还在过火时的读数** —— 见下方「一个正确的修复让这个数掉了 8 个点」 | `check_benchmark_mode_accuracy.py` |
| 强制控制面在不在 | **72 条全齐、0 次缺失** ✓ 这一条是真在执行的 | 同上 |
| **我能拿到几个人** | **1 人，或者 ≥9 人 —— 中间没有档。** 只靠推断（不给 `--size`/`--mode`），`persona_expert_target` 取得到的值：纯长度扫 1–240 词 ⇒ **{1, 9, 10, 11, 21, 22}**；72 道 oracle ⇒ **{10, 11, 12, 24, 25, 28}**。**2–8 这一整段，两种样本上一次都没出现过**，而合同声明 `small_team` 是 **(5, 15)**。**成因可从公式推**：`single_expert` 恰好 1；`small_team` 是 `min(15, max(5, round(5 + 6c + 3r + |domains|)))`，进门要 `c ≥ 0.38` ⇒ 门一过、各分量落地板（c 0.3838、r 0.08、domains 1）就已经是 `8.54 → **9**`。★★ **出口自相矛盾**：`--size 5..8` 只在**推断出的模式已经是 small_team** 时被接受；任务短到 `single_expert` 时 `--size 6` 被拒（「valid: 1–1」）⇒ **想要 6 个人，你得先把任务写到足以拿 9 个人**；何况 `--size` 是运行时旗标，**不是用户在自然语言里能表达的东西**。 | `scripts/check_team_size_ladder_has_no_hole.py`（**包内**，7 项自测含公式复算＋出口正反例） |
| **档位由什么决定** | **主要由题面长度**。负对照：`zzq0 zzq1 …` 这类**毫无内容**的串（撞不上任何词表、域落兜底档、无连词无交付物词）——**100 个无意义词 ⇒ complexity 0.784 ⇒ deep_team，派 21 人**；180 个 ⇒ 22 人。而真有内容的短请求「修复登录接口的空指针崩溃并补回归测试。」⇒ **0.296 ⇒ single_expert（1 人）**。成因：`complexity` 里**光字数一项上限 `min(词数,120)/170 = 0.706`**，deep_team 门 0.76、减 base 只需 0.62。★★ 而真任务上**唯一在起作用的触发就是 `complexity`**（72/72；risk 0/72、domains≥5 0/72、parallel 0/72）⇒ **整条阶梯实际由「题面有多长」驱动**。**长度不是复杂度。** | `scripts/check_mode_ladder_reachable.py`（**包内**，每次实跑都印这张负对照表） |
| **多样性把「对口的人」换掉多少** | **换手率中位 36%**（8 条名册标签、deep_team、size=14；范围 29–43%）；★ **换成 72 道 oracle 全量（12 个题面）⇒ 中位 57%（43–79%）—— 默认样本低估了问题**；★★ 我先前写的「前 8 条 中位 61%（57–64%）」**只覆盖 2 个题面**，**那个窄区间看着像稳定，其实是 2 题面 × 4 变体**，已订正。即**按对口度排前列的人约三分之一被多样性换掉**。临界点是从源码推的：同族第 2 人要胜过一个**新族**候选，`base_score` 需领先 **(0.08+0.025)/0.76 = 0.1382**（第 3 人 0.1711｜第 5 人 0.2368｜封顶 0.2632）。实测一道软件评审题：**14 人里只有 3 个软件开发师，第 5 位是农场主** —— Chip Huyen base **0.3549**（全场第 2 高）被压到 marginal **0.1872**、排第 10；Joel Salatin base 0.2299 因是唯一的农林牧渔师，marginal **反涨**到 0.2470、排第 5。 | `scripts/check_diversity_does_not_outweigh_fit.py`（**包内，带回归地板与非退化守卫**） |
| **谁来干哪个包，由什么决定** | **主要由一个不含任何任务信息的量**。`assign_packets` 的 `score = compatibility + 0.28*base_score − 0.08*载荷 − (0.25 若超载)`，而 `compatibility = overlap_score(packet["objective"], 候选人卡片)` —— `objective` 是**模板文案**：12 个独立题面（auto 档）出现过的**不同 objective 只有 28 条**，5 条固定阶段包 ＋ 23 条「独立处理第 N 个分片」（N 只是编号），**没有一条带任务内容**。★ 唯一一次「objective 里出现题面片段」是反向巧合：某题面自己写了「证据缺口」，而模板里本来就有这四个字。**消融**：12 支多人队伍、包合计 173 个，把 `compatibility` 置 0 ⇒ **154/173 = 89.0% 的包换了主人**。★★ **射程**：对照臂（只剩 `0.28*base − 载荷`）**本身是退化的**，所以这个数**不能读成「89% 的分派是错的」** —— 它只支持「决定谁拿哪个包的，主要是一个与任务无关的量」。 | `measure_packet_assignment_ablation.py`（**包外**，5 项自测含反例） |
| **宿主要装进上下文的那份合同有多大** | **`deep_team` 的执行合同 776 KB，dossier 1796 KB**（2026-08-18 整条链现跑 `route_team_moe → build_team_dossier → build_execution_contract`，读的是**盘上字节**）：`single_expert` 1 人 ⇒ route-plan 30／dossier 83／contract **38 KB**；`small_team` 9 人 ⇒ 111／531／**233 KB**；`deep_team` 28 人 ⇒ 273／1796／**776 KB**；**`swarm` 30 人 ⇒ 318／1786／789 KB**（★ swarm 那道题是**我造的**—— 把 `PARALLEL` 词表塞满再填到 905 字；自然任务里 swarm 一次都没被选中，**这一行只证明链条跑得通与体量，不证明用户会遇到 swarm**）。合同里 `execution_units` 占 **88.1%／98.0%／99.4%**（每位专家一段）⇒ **随人数近似线性长**，最大那份**每位专家约 27.7 KB**。★ token 数**不是量出来的**：字节是实测，除数是选的 —— 776 KB ÷ (4.0／2.5／1.5 字节每 token) ⇒ **199／318／530 K token**，即区间 **199–530 K**。**别只报一个数。**★★ 与档位阶梯并排读：**32 个无意义词就能拿到 deep_team**（见上面两行）⇒ **一个稍长的请求就能产出宿主可能装不下的合同**。★★★ 判据**不判「太大了」**（多大算大取决于宿主，不是这个包能定的），只判「**每位专家占的字节不许比基线更胖**」。★★★★ **那 776 KB 里没有免费的午餐**（同日复量）：`execution_units` 的 **97.2% 是 `capsules`**，而 33 段里有 **29 种不同内容** —— 唯一的重复是 **5 段空的控制面角色（0 KB）**。即 **28 个人 × 每人 22.6 KB 实打实的材料**（`method_capsule` 37.9%／`evidence_capsule` 22.5%／`failure_capsule` 18.8%／`work_capsule` 9.5%／`boundary_capsule` 8.6%／`voice_capsule` 1.7%／`currentness_capsule` 0.9%）。⇒ **要瘦身就得少给每个人材料，那是质量取舍，不是免费的清理** —— 见 Task #136。 | `scripts/check_execution_contract_fits_a_context.py`（**包内**，8 项自测，整条链现跑约 9 秒） |
| 团队级结果遥测有多少条 | **0 条**。C 层要 ≥60 条 ⇒ **C 从未启用过，全部实跑都是 B** | `report_expert_team_state.py` |
| **C 层（自优化）攒够 60 条就能开吗** | **不能 —— 它被绑在「产品表现得差」这个条件上。**C 层要 `ECE ≤ 0.12`，而写手存进遥测的 `predicted_success` 是**队伍 `marginal_score` 均值**（`record_team_outcome:95`）—— 一个**排序分，不是概率**。实测取值（★ 两份样本都报）：72 道 oracle 的 12 个题面 **0.1559–0.2552** ⇒ 窗口 **0.04–0.38**；名册标签 12 条 **0.2155–0.5160** ⇒ 窗口 **0.10–0.64**。**取对产品最有利的那份（上沿 0.64）**：真实成功率 70%／80%／90% ⇒ ECE **0.1840／0.2840／0.3840**⇒ 三档**全部启用不了**。★★ **整条回路实跑过**（临时遥测文件，默认路径一字节未碰）：60 条 + `actual` 匹配排序分 ⇒ ECE **0.0000** ⇒ 实跑 strategy = **C**；60 条 + `actual` 0.85 ⇒ ECE **0.6091** ⇒ 实跑 strategy = **B**。⇒ **机制是通的，坏的是预测量选错了对象** —— 不是「没实现」。见 Task #137。 | `scripts/check_c_layer_is_reachable_for_a_working_product.py`（**包内**，7 项自测含正/反对照） |
| 分歧检测能不能命中 | **命中不了，而且不是碰巧** —— 2026-08-18 用**权威抽取器**（`build_team_dossier.extract_divergences`，逐个开 102 份交付包读 `divergence-map.md`）现算：全库可互相点名的配对 **24 / 5151 = 0.47%**，**24 个全部同族**（investor-capital-allocator 17、software-developer 7，**跨族 0 个**）。★★ **72 道 oracle 全量实测：路由选出的队伍含可检出对的 0/72**；而**同样大小**的随机队伍（200 次重抽）中位 **22/72 = 30.6%**，200 次里 **0 次** ≤0（经验 p<0.005）⇒ **不是碰巧没凑到，是系统性地把它们分开**：多样性配重要求同族第 2 人 `base_score` 领先 **0.1382**，而唯一检得出分歧的配对恰好全是同族 —— **多样性与分歧检出结构性冲突**。★ 旧记录写的「24 个任务里 0 个」用的是另一份 24 条样本，且当时**没跑通权威抽取器**；本次是第一次真的跑通（第一版我 `rt.get("team")` 拿错键，队伍全空、`0/72` 作废，是「队伍规模中位 0 人」这行打印抓出来的）。`divergences: []` 意为「**没有检出**」，**不是**「专家一致」 | `scripts/check_divergence_pairs_survive_extraction.py`（**包内**，守配对数不掉＋退化/切碎双反例）／72 题那两个数的复算：见 CHANGELOG v0.0.0.37 |
| 名册覆盖 | 12 个身份族中 **医疗护理师恒为 0 人**；命中该族的任务注定 0 | `audit_persona_fleet_for_team.py` |
| 名册里的人物本身测过没有 | **102 个在册产物中只有 2 个**（2%）有干净的盲测 delta 读数（Carver +0.3791、Shewhart +0.1822）；另 3 个只有污染读数（看过 rubric 才写基线，不算证据）；**97 个什么读数都没有**。三方向交叉核一致：102 份 registration.json 与 102 份 team-card.json 含 delta 字样的都是 **0** 份 | `check_registered_products_have_delta_evidence.py` |
| 团队 vs 裸模型的盲测增益 | **没有这个数。** 需要真跑任务并与裸模型盲比、且要互相独立的评委会话 —— 未做，**不编** | —— |

> ### ★★★ 先说清楚：**这一列里有四个脚本不在你装的这个包里**（2026-08-18 实测）
>
> 以「装了这个 skill 的人」的视角把上表点名的脚本逐个查过去：
>
> | 脚本 | 在哪 |
> |---|---|
> | `audit_persona_fleet_for_team.py`／`record_team_outcome.py`／`run_tests.py`／`run_functional_acceptance.py` | **本包 `scripts/`、`tests/`** ✓ |
> | `measure_routing_discrimination.py` | ✗ **不随包分发** —— `skill_log_evals/persona-distiller/_ledgers/_pipeline/`（开发台账树） |
> | `check_benchmark_mode_accuracy.py` | ✗ 同上 |
> | `check_registered_products_have_delta_evidence.py` | ✗ 同上 |
> | `report_expert_team_state.py` | ✗ 同上 |
>
> 也就是说：**上表八行里，有四行的「怎么重跑」在你机器上不存在**，
> 照着敲会得到 `can't open file`。那四件都在本项目的 git 仓里，
> 但它们属于**开发侧台账**，不进 skill 包。
> （另有 `build_release_bundle.py`／`bump_version.py`／`self_check.py` 出现在 CHANGELOG 里，
> 它们随**上游** `persona-distiller` 分发，也不在本包。）
>
> **这条披露本身有判据守着**：`scripts/check_cited_scripts_ship_with_the_package.py`
> 扫本包所有随包 `.md`，任何**新**出现的包外脚本若没进它的明码表就判红
> （闭集合，不靠措辞匹配；零命中判 rc=4 未核而不是通过）。

> ### ★★★ 一个**正确的修复**让这个数掉了 8 个点（2026-08-18 消融确认）
>
> 上表「模式判对」旧值 **33%**（16/48、8/24），现算 **25%**（12/48、6/24）。
> 逐条查翻号的题，**6 条全是同一句题面的变体**：
>
> > 「**设计**跨服务、数据、权限、恢复和运维的软件架构并生成迁移任务包。」
> > 域：`software-ai, creative-design, research-education` → `software-ai, research-education`
> > ⇒ domains 3 → 2 ⇒ 掉出 deep_team，落到 small_team（oracle 期望 deep_team）
>
> 掉的那个 `creative-design` **只因为句子里有「设计」两个字** —— 一道软件架构题，不是设计题。
> 2026-08-17 把 `设计`/`design` 降为弱信号（有实测误发为据、有负对照护住真·设计题），
> 正是**修掉了这个误报**。
>
> **消融确认（只关 `WEAK_SIGNALS` 一个开关，其余一律不动，且复原后回到原值）：**
>
> | 题集 | 现行 | 关掉弱信号 |
> |---|---|---|
> | development-48 | **12/48 = 25%** | **16/48 = 33%** |
> | regression-24 | **6/24 = 25%** | **8/24 = 33%** |
>
> **两个题集都精确回到旧值。**
>
> ⇒ **旧的 33% 里有 8 个百分点是那个缺陷挣来的。**
> 修好它之后路由并没有变差 —— 它原本也没做对这 6 条，只是**从「因为一个假域而蒙对」
> 变成了「诚实地做错」**。
> ★ 这也是为什么本项目对基准分数**不做优化**：谁去优化它，第一步就会把这个正确的修复退回去。

> ### ★★★ 上表每一个数都**只对它那份样本成立** —— 两份样本在三项上互相矛盾
>
> 本 skill 的数出自两份不同的任务集，**它们给出的图几乎相反**（2026-08-18 现算 @v0.0.0.31）：
>
> | | **72 道 oracle**（`benchmarks/*.jsonl`，任务口吻，TaskPack 原样） | **60 条名册标签**（产物自带 `application_scenarios`，名词短语） |
> |---|---|---|
> | 选中 `single_expert` | **0 次** —— 逐档召回 0/12、0/6，且**直接量档位分布也是 0/72** | **53 / 60 = 88%** |
> | 选中 `deep_team` | **18 / 72 = 25%**（靠 `complexity ≥ 0.76`） | **0 次** ← ★ 「结构性不可达」**只对标签成立** |
> | 选中 `small_team` | **54 / 72 = 75%** | 7 / 60 |
> | 选中 `swarm` | **0 次** | **0 次** ← ★ **两份样本都坐实**：`parallelizability` 最大 **0.665 < 门 0.72**，与那条**照着 swarm 门写的**验收题面读数**完全相同** |
> | 无域信号 | **0%** | **49.3%** 只认出兜底档 |
> | 平均长度 | 任务口吻的整句 | **33 字**，多为名词短语 |
>
> **同一个产品、同一天、同一版本。** 差的是问它的方式。
>
> ⇒ 读这张表时，**任何一个百分数都要连「哪份样本」一起读**。
> 特别是「88% 只坐 1 个人」这句：**它说的是名册标签，而真任务上单人档一次也没被选中**；
> 
> 在任务口吻的 72 条上，`single_expert` **一次都没被选中**——方向完全相反。
> ★ 两份都不是「真实用户提问」：一份是产物自己写的标签，一份是任务包作者写的 oracle。
> **真实提问的分布没有量过。**

**怎么用这张表**

1. 任务落在没有领域信号的那 8% 时，**别把队伍当成「按专业挑出来的」** ——
   执行合同的 `selection_caveats` 会明写这一点。
2. `documented_divergences` 为空时，**不要写成「专家们意见一致」** ——
   执行合同的 `user_output_contract.phrasing_rules` 有明确措辞要求。
3. 需要 1 个人或 25+ 人的任务，**显式传 `--mode` / `--size`** ——
   auto 在基准的 72 道题上从没选中过这两种模式。
4. 想要「比裸模型强多少」的数，先跑真实任务并记录 outcome
   （`record_team_outcome.py` 默认写 `<registry-root>/telemetry/team-outcomes.json`，
   路由默认从同一处读）。**攒够 60 条 C 层才会启用。**

## 四种模式

| 模式 | 人物专家席位 | 适用 |
|---|---:|---|
| `single_expert` | 1 | 单一专业、边界明确、一个人物方法足够 |
| `small_team` | 5–15 | 多能力、可部分并行、协调成本可控 |
| `deep_team` | 10–30 | 高风险、跨域、强冲突、多阶段交付 |
| `swarm` | 25+ | 至少 25 个真实、低耦合、可合并工作分片 |

没有 Solo 模式。低复杂度任务进入 `single_expert`。

人物席位只统计 `persona-solver`。以下中立控制面在四种模式中始终执行，但不计入人物人数：

1. `team-orchestrator`
2. `hypothesis-framer`
3. `counterevidence-adversary`
4. `independent-reviewer`
5. `decision-judge`
6. `synthesis-lead`

## 运行主线

```text
用户一次输入
→ Task Compiler / work-packet DAG
→ C/B/A 路由
→ 人物资产准入
→ route plan（含 subject_slug）
→ 内层 Runtime ZIP / dossier / capsules
→ 人物独立工作产物
→ 对抗反证
→ 独立复审
→ 裁判裁决
→ 单一最终交付
→ Team Delta Card
→ outcome telemetry
```

### C / B / A

- **C：Calibrated Agentic Sparse MoE**。只有真实结果遥测满足样本、校准和切片覆盖门才启用。
- **B：Deterministic Capability DAG**。默认稳定执行面；按能力、方法、工具、边界和工作包路由。
- **A：Compatibility Router**。仅在 B 无法形成有效图时兜底，保持旧资产和接口可迁移。

回退只发生在路由策略层：`C → B → A`。不回退到 Solo；若没有任何真实人物可用，状态是 `insufficient_roster`，不得伪造专家。

## 六步调用

```bash
# 1. 构建人物资产准入账本
python3 scripts/audit_persona_fleet_for_team.py \
  --registry-root . \
  --require-artifacts \
  --output expert-fleet-admission.json

# 2. 一条命令准备完整团队运行目录
python3 scripts/run_team_pipeline.py \
  --task "<用户任务>" \
  --mode auto \
  --strategy auto \
  --registry-root . \
  --refresh-admission \
  --require-artifacts \
  --workdir ./team-runs/current
```

运行目录必须产生：

- `route-plan.json`
- `team-dossier.json`
- `execution-contract.json`
- `run-receipt.json`

宿主 Agent 按 execution contract 执行后，写回结果并执行。

> **注意：下面两个 `--result` 要的是两份不同的文档。**
> `result-input.json` 是**判分输入**（`absolute` / `candidate` / `baseline` / `paired`）；
> `team-result.json` 是**运行叙述**（`work_completed` / `member_contributions` /
> `decision_changing_disagreements` / `audit_trace` / `next_action` /
> `remaining_unknowns`）。参数同名而内容不同，别把同一份传给两边 ——
> 传错时 `score_team_delta` 会 **`status: blocked` 并 rc=2**（不会给你一个 0 分冒充读数）。


```bash
python3 scripts/score_team_delta.py --result result-input.json --output delta-score.json
python3 scripts/build_team_delta_card.py --route-plan route-plan.json --result team-result.json --delta-score delta-score.json --output team-delta-card.json
python3 scripts/record_team_outcome.py --route-plan route-plan.json --delta-score delta-score.json --task-slice <slice> --actual-success <0..1> --telemetry outcome-telemetry.json
# ★ `<slice>` **不是自由文本**：`task_slice_coverage` 的分母是一个 12 个词的固定表
#   （creative / currentness / deep-architecture / deep-high-risk / ood-boundary /
#    recovery / single-diagnosis / single-explanation / small-product /
#    small-research / swarm-batch / swarm-search）。
#   写表外的名字**照收不报错**，但对 coverage 贡献恒为 0，而 **C 层启用看的就是 coverage**。
#   表外的名字会记进遥测的 `unrecognised_task_slices`；`--help` 里也印着整张表。
```

★★★ **团队给出答案之后、记录结果之前，跑这一件**（2026-08-18 补：
它此前**没有任何流程调用方**，只有自测被自动收编）：

```bash
python3 scripts/check_team_attribution.py team-answer.json --members-file route-plan.json
```

**合议票数门**：团队宣称的票数不得超过它实际点名的人数。
它必须在**运行时**跑 —— 团队答案不是仓里的产物，仓里永远没有它可吃的输入。

不得把“已生成合同”说成“任务已完成”。只有真实结果可以更新 C 层校准。

## 自检

    python3 scripts/run_tests.py            # 默认就是门：有红即 rc=1
    python3 scripts/run_tests.py --report   # 只报告

★ `run_tests.py` 只跑 `tests/`，**不碰 `scripts/` 下的判据**。发布前另跑这三件：

    python3 scripts/check_group_version_binding.py     # 版本三处绑定（硬门）
    python3 scripts/check_roster_independence.py       # 名册独立性（只报不判）
    python3 scripts/check_mode_ladder_reachable.py     # 四档模式够不够得到（披露）

  这三件已接进 `tests/run_functional_acceptance.py`；单独列在此处，
  是因为**「被自测收编」不等于「有人拿真数据跑过」**。

跑 `tests/` 下**全部** `test_*.py` **＋** `run_*.py`
（`run_functional_acceptance.py` 不叫 `test_*`，只按一种命名会漏掉它）。
**件数以 `run_tests.py` 印出的「扫描面」为准，本文不写死数字** ——
原来这里写着「全部 9 件」，而它当天就被同一场会话里新增的测试证伪成 11 件。
（[[claims-my-own-next-delivery-falsifies]]：会再产一份的东西，写判别式不写计数。）
文件正文里记着一张**变异实测表**：把核心函数逐个打坏，看几件测试会喊。

## 硬门

1. 路由结果必须给每个人物输出 `subject_slug`。
2. dossier 必须真实打开登记产物的内层 Runtime ZIP。
3. 没有真实 payload、claim 和 boundary，不得开始人物推理。
4. 每条人物特有贡献必须引用该人物自己的 `claim_id`。
5. 当前事实来自独立的有日期事实通道，不从历史人物权威推断。
6. Voice 胶囊默认关闭；优先 Method、Evidence、Work、Failure、Boundary。
7. 分歧按前提、证据、预测、失败条件和适用范围裁决；不按多数票折中。
8. 生成者不得复审自己；裁判不得修改候选证据。
9. Swarm 只用于真实独立分片，不得用 25 份重复意见凑人数。
10. 任一硬维度低于 75，候选退回优化，不得发布冠军结论。

## 必读参考

- `references/persona-producer-consumer-contract.md`
- `references/moe-routing-contract.md`
- `references/team-size-control-plane.md`
- `references/team-output-contract.md`
- `references/user-experience-contract.md`
- `references/team-delta-scorecard.md`
- `references/market-leader-acceptance.md`
