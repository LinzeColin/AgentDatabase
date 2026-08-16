# CHANGELOG — persona-distiller-group

## v0.0.0.17 — 2026-08-17

### 遥测终于有了家：写手与读手约定同一个路径

**缺陷（结构性，不是「还没用过」）**：
`record_team_outcome.py` 的 `--telemetry` 是**必填**，
`route_team_moe.py` / `run_team_pipeline.py` 的 `--telemetry` 是**可选且无默认**。
**没有任何一处命名过路径。** 写手和读手只有在人**每次手工把同一个路径传给两边**
时才会相遇。

实测 2026-08-16：**记录数 0**，每份 route-plan 都报
`strategy_fallback_reason: "telemetry unavailable"`，策略 C **一次都没启用过**。

这不是「校准层还没开始用」，是**它在结构上攒不起任何东西**：
C 需要 >=60 条 outcome，而一个没有归宿的计数器连 1 都到不了。

**修法**：`registry_core.default_telemetry_path()` 定义唯一真源
`<registry-root>/telemetry/team-outcomes.json`，三处共用。
`record_team_outcome.py --telemetry` 由必填改为可选。

**不改任何行为**：`load_telemetry()` 对不存在的文件本来就退化成
`eligible_for_c: False`，所以给路径加默认值**不可能**把一条本来能跑的 B 路由变红。
它只是让写手写下的东西，下一次真的被读到。

### route-plan 现在会说出它读的是哪个遥测文件

`routing_observability` 增加 `telemetry_path` / `telemetry_path_source` /
`telemetry_file_present`。在此之前，一份写着「telemetry unavailable」的方案
**无法让人分辨「文件是空的」和「我找错地方了」**——而几个月来确实**没有**
一个约定的地方可找。

### 测试：`tests/test_telemetry_roundtrip.py`（写手 -> 文件 -> 读手）

在临时目录里跑完整回路，**任何合成 outcome 都不会落进真的遥测文件**。
两侧各有反对照，均已实跑：

- 改掉写手的默认路径 -> 红（写到别处、约定位置什么也没有）
- 改掉读手的默认路径 -> 红（读了别处）

★ 第一版**只钉了写手**，删掉读手的默认它照样绿 ——
**一个要求，两个消费者，其中一个没有守卫**。这是本项目记过多次的形状，
补上读手断言后两侧反对照才都成立。

★ 仍然不变的事实：**记录数依然是 0**。有了家不等于有了数据。
`--actual-success` 与 `--delta-score` 要靠真跑一次任务并与裸模型盲比才有，
**编一个就是造数据，不做**。这次解决的是「攒不起来」，不是「已经攒到了」。

## v0.0.0.16 — 2026-08-17

### 领域分类器：按语种分开匹配（`compile_task_graph.infer_domains`）

**缺陷**：匹配是纯子串（`signal.casefold() in low`）。于是两个字母的关键词
命中了普通英文单词的**内部**：

    infer_domains("Decide whether to proceed.")  ->  ["software-ai"]

`ci`（continuous integration）是 `de`**ci**`de` 的子串；`ai` 是
`av`**ai**`lable` / `cert`**ai**`n` / `det`**ai**`l` 的子串。
一句**一个技术词都没有**的话被判成软件题，并拿到 **34 个「懂这行」的候选**，
而 route-plan 里没有任何地方提示这次匹配是假的。

**修法**：匹配规则**按书写系统分开**——

- ASCII 关键词 → 词边界匹配（`(?<![a-z0-9])...(?![a-z0-9])`）
- 非 ASCII（中日韩）关键词 → 仍用子串

第二条不是图省事：正则的 `\b` 是对着 `\w` 定义的，而 CJK 字符**就是** `\w`，
所以 `\b软件\b` 在「的软件架构并」里**永远匹配不上**——两侧都是词字符，没有边界。
中文不写空格；把 ASCII 规则一视同仁地套上去，会**静默丢掉全部中文关键词**
（72 道基准题里有 12 道是中文）。

**两半各自都已经害我错过一次**：ASCII 那半让一句无关键词的英文认领了领域；
CJK 那半让我自己写的一个检查把 12 道**分类正确**的中文题报成「全靠子串误伤」。

### 这次修复在基准上的收益，实测是 **0**

A/B（同一把尺子，只动这一处，其余全部不变）：

| | 修复前 | 修复后 |
|---|---|---|
| 24 题平均差值 | +15.9 pp | +15.9 pp |
| n>=5 团队模式 | +6.3 pp（SE 2.6） | +6.3 pp（SE 2.6） |
| 分类器兜底率 | 2/24 = 8% | 2/24 = 8% |

原因：`ai`/`ci` 以子串形式出现在 **0 / 72** 道基准题里。
**证据是探针，不是基准**——这一类缺陷这套基准根本看不见，
所以另配了 `tests/test_domain_classifier_language.py`（8 个用例，两半各钉一半；
撤掉修复即 4 条变红，反对照已实跑）。**不把 0 收益包装成进展。**

### route-plan 新增：无领域信号时如实披露

`routing_observability` 增加 `domain_signal_candidates` /
`domain_signal_present` / `ranking_driver`；当 `domain_match` 对**全部**候选为 0 时，
`limitations` 追加一条明写「这支队伍**不是**按专业匹配选出来的，排序落到了
`currentness`（人物年代新旧），实测这一档比随机抽人低 1.7 pp」。

- **只披露，不改行为**：不动分数、不动排序、不动选人、不动人数、不动控制面。
- 「无信号时是否该**拒绝**路由」属 Owner 裁定，此处**有意不决定**。
- 已证明这条披露命中得了（舞台编舞题：0/41 候选有信号，警示触发）——
  不是一盏永远亮不了的灯。

## v0.0.0.15 — 任务领域词表扩到 290 词（**样本内验证，未做外部集复验**）

- `compile_task_graph.DOMAIN_SIGNALS` 由 **92 词扩到 290 词**（9 个领域不变）。
  **只加词、不删词、不改任何权重与阈值**；模式／人数／控制面／95-75 门／
  生产者-消费者边界一律未动。
- 起因（判据 `persona-distiller/_ledgers/_pipeline/measure_routing_discrimination.py`）：
  原表撞不上时 `infer_domains` 返回 `general-decision`，而它**不在任何族的
  `CATEGORY_DOMAINS` 里** ⇒ `domain_match` 对全部 101 个候选恒为 0 ⇒ 排序落到
  `currentness`（人物年代新旧）⇒ 实测**比随机抽人还差 1.7 pp**。
  兜底率实测 **13/24 = 54%**；`software-ai` 那 14 个词里**没有「测试」**。
- **`operations-product` 有意不扩**：它出现在 12 个族里的 **7 个**，加词等于把
  7/12 的人一起点亮。第一版扩它之后 `factory-layout` 从 +10.4 掉到 −3.0，
  回退该族后回到 +0.1，且总体反而更好（高于随机 16→18、低于 6→4）。

### 实测（同一把尺子、24 题、随机基线 400 次、固定种子）

| | v0.0.0.14（92 词） | **v0.0.0.15（290 词）** |
|---|---:|---:|
| 分类器兜底率 | 13/24 = **54%** | 2/24 = **8%** |
| 团队模式 n≥5 | +1.6 pp（SE 2.2，**0.75 SE**） | **+6.3 pp**（SE 2.6，**2.38 SE**） |
| 高于随机 / 低于随机 | 10 / 12 | **18 / 4** |
| 逐题 vs 基线 | — | 变好 **14**、变差 **3**、不变 7 |

### ★★ 这个数**不能当作泛化证据**

新加的词（「测试」「定价」「钢桥」…）**是从这 24 题的失败案例里挑出来的**，
用同一批题验证等于拿答案配尺子。**样本内**。
- **可引用的**：兜底率 54% → 8%（分类器行为，与任务集无关）；
  逐题变好 14 / 变差 3。
- **不可引用的**：`+6.3 pp / 2.38 SE` **不是**「路由收益已证实」。
  要那句话，需要一批**在扩词之前就写好、且我没看过其词汇**的任务。
- 仍有 3 题比基线差：`factory-layout` −10.3（基线那 +10.4 是无领域信号时按年代
  排序**恰好排对**的运气）、`typography-system` −3.1、`bridge-inspection` −2.5。

### 未变

功能验收 `tests/run_functional_acceptance.py` **PASS**；
`tests/test_market_leader_candidate.py` **7 passed**。
市场状态仍为 `MARKET_LEADER_NOT_PROVEN`；团队级 outcome 记录数仍为 **0**。

## v0.0.0.14 — Agentic Sparse MoE and end-to-end persona consumption

- Fixed route-plan to dossier continuity by emitting and consuming `subject_slug` across `members`, `domain_experts`, `selected_roles`, and legacy `roster`.
- Replaced the single fixed 5–20 team contract with Single Expert (1), Small Team (5–15), Deep Team (10–30), and Swarm (25+); no Solo mode.
- Added mandatory neutral hypothesis, counterevidence, independent review, judge, orchestrator, and synthesis controls to every mode; controls are excluded from persona seat counts.
- Added C/B/A routing: calibrated sparse MoE, deterministic capability DAG, and compatibility fallback.
- Added producer-consumer fleet admission, minimal persona capsules, capacity-aware packet ownership, execution contracts, Team Delta scoring, and 95/75 acceptance gates.
- Voice is off by default; method, evidence, work, failure, boundary, and currentness capsules drive runtime behavior.
- Added functional acceptance covering all modes, nested Runtime ZIP loading, route-to-dossier continuity, C-to-B fallback, and scoring gates.

> **这份记录是 2026-08-01 事后从 git 重建的，不是逐版当时写的。**
> 凡从 git 重建的条目都在末尾标 `[git 重建]`；从本版起当版写当版。
> 重建依据一律给出可自行复现的命令，**不写"大概改了什么"**。
>
> 版本轴只有一条：`VERSION`（`v0.0.0.N`）。人物产物的版本（裸写 `0.0.0.1`，不带 `v`）
> 由 `persona-distiller` 拥有，本 skill 只登记、从不铸造。

## v0.0.0.13 — 合议票数门：**契约写了三个版本，从来没有检查器**（2026-08-02）

### 这不是新规矩，是补一个从没存在过的检查器

`team-output-contract.md` 从 **v0.0.0.7** 起就写死了第 2 条：

```
【<人物名>】<贡献内容> <!-- claim:clm-xxxxxxxxxxxx -->
```

**「引用不出 `claim_id` 的贡献视为未发生」。** 契约在那里，六个版本没人查。

2026-08-02 三臂盲判，席 B 抓到它被违反：

> 它用「三个人一致」「三票否决」赋予自己一种**从未展示的合议权威**——
> **t1 只摆了两路却称三票。**

回看 `ans_team.json` 原文，**实情比席 B 说的还差一格：全文一个成员名都没出现。**

### 落成判据后扫同一批 8 道题：3 道中招

```
✗ 超额合议宣称 3 处：
  - t1　宣称 3 票／人，实际点名 0 人（**一个都没有**）　原文：三个人一致／三票否决
  - t2　宣称 3 票／人，实际点名 0 人（**一个都没有**）　原文：三个人都同意
  - t5　宣称 3 票／人，实际点名 0 人（**一个都没有**）　原文：三个人在「现在不要做空」上一致
```

**席 B 报了 1 处，实有 3 处。** 与 v0.0.0.22 拒答溢出门那次同一形态：
**评委看到的是症状，判据才数得清范围。**

### 判据

宣称任何票数／人数的合议（`N 票`、`N 人一致`、`N 个人都同意`…）时，
**正文中必须至少点到同样多的成员名**。少说不算错，多说才算错。

门槛取「点名」而不是「分了几段」：**分段可以任意切，只有名字能对上名册**，
它是唯一可核验的锚。本门因此顺带强制了 v0.0.0.11 遗留的「团队产出必须逐条署名」。

### 射程（必须一起说）

它数的是**名字有没有出现**，不是**这个人是否真的持这个观点**。
把三个名字撒进正文就能骗过它——**它挡的是「凭空宣称票数」，不是「冒名代言」**，
后者仍由第 2 条的 `claim_id` 规则负责。
无数词的「大家一致认为」不在射程内：堵它需要判定「大家」指几个人，那是语义不是句式。

### 负对照九项，其中两项是关键

- **用 t1 原文做真实样本对照**——判据必须抓出它，且必须数出「点名 0 人」。
- **反向对照：清空中文数词表后，t1 必须不再报错**——证明抓到它的是数词判据本身，
  而不是别的什么巧合。

其余：点名 2 宣称 3、阿拉伯数字两类坏样本；点名足数／无合议宣称／少说三类正对照未误杀；
英文正文只称姓时能对上名册；无数词的「一致」不误判。

### 为什么这条值一个版本

团队臂相对裸模型 **−0.0219**、相对单人物 **+0.0825**。
**能解释那 +0.0825 的只有「多个不同视角」**——
一份不点名的合议宣称，恰好把团队层唯一的卖点变成了不可核验的断言。

实测：`--self-test` 9 项全过；真实产出实跑抓到 3/8；版本绑定三处同为 v0.0.0.13；
group validate 12 类 / 100 人 / 102 件 passed；group 检查器元普查 **3 件全部 OK**。

## v0.0.0.12 — 相关性错误落成判据；**先记我自己判错的那一次**（2026-08-02）

### 一、判据的第一版是错的，而我差点拿它当结论

第一版把 g5 的三次产物答案全部判成「混：技术分析之父」，三次错法一致，
在屏幕上长成「**共同幻觉的实证**」。核原文才发现三次都是对的：

> 「把我归入『技术分析之父』**与这句原话直接抵触，本产物不沿用**」

**判据看到那六个字就判错——它分不清「主张 X」与「反驳 X」。**
而脚本 docstring 里我亲手写过「用关键词命中判定，不是语义判定」——
**写了射程，照样差点越过它用。**

修法两件：`_refuted()` 做否定语境识别（前后 60 字）；**补负对照并验证它有牙齿**——
清空 `NEGATION` 后 `--self-test` 必须 exit 1，实测：

```
✗ 反向对照失败：反驳错误说法被判成 混:技术分析之父（应为「对」）
```

**这件判据原来没有负对照**，于是缺陷活到我核原文那一刻。
和「产品本身没有负对照」是同一条教训，**换了个尺度又犯了一次**。

### 二、测得的数（6 道 ground-truth 事实题 × 各 3 次独立作答）

| | 准确率 | 答错 | 答不出 | 错误重合率 |
|---|---:|---:|---:|---:|
| 裸模型 | 7/18 = **0.3889** | 3 | 8 | **0.0000**（三次错法各不相同） |
| 产物 | 18/18 = **1.0000** | 0 | 0 | **无从计算** |

### ★ 这个 +0.6111 有多少能算数：大部分不能

裸模型少掉的 11 次里 **8 次是「答不出」，只有 3 次是「答错」**。
g4（$9,916）与 g5（他对图表的原话）裸模型三次全部空白——
**这两道的答案只存在于产物自己的语料里。产物有语料，裸模型没有，比准确率接近同义反复。**

它与两次盲测**不矛盾、是同一个形状**：32 道人物题真 delta −0.1075，
十六套组里唯一正值就是 `fact-preservation` **+0.247**；本轮只是把那个正值
放大到一组专门为它设计的题上看清楚。**赢的还是同一处。**

### 三、用户问的「相关性错误 / 共同幻觉」：未观测到，**也未被排除**

裸模型侧 3 道错题错法各不相同 → 重合率 0.0000。
**产物侧 0 题出错 ⇒ 该指标在产物侧完全没有被测量，不是被测量后为零。**
6 题是小样本，且这批题对产物有结构性优势——**正是最不可能暴露共同幻觉的一组题。**
真正要测，需要一批**语料未覆盖而产物仍会作答**的边缘事实题。**挂下一步，不当已完成。**

### 复跑

```
python3 ../../../skill_log_evals/persona-distiller-group/experiments/score_correlated_errors.py --self-test
python3 ../../../skill_log_evals/persona-distiller-group/experiments/score_correlated_errors.py
```

实测记录：`skill_log_evals/persona-distiller-group/0.0.0.12.md`

## v0.0.0.11 — 四项全部有数了（2026-08-02）

三臂盲测（8 道**需要作判断**的决策题 × 2 席盲判 = 16 组）：

| 臂 | 均分 | 逐组第一 | 平均长度 |
|---|---:|---:|---:|
| **裸模型** | **0.8500** | **11** | 808 字符 |
| 团队（3 人合议） | 0.8281 | 5 | 1233 字符 |
| 单人物 | 0.7456 | **0** | 470 字符 |

```
团队 − 裸模型   = -0.0219
团队 − 单人物   = +0.0825   ← 团队层的净贡献
单人物 − 裸模型 = -0.1044   ← 复现
```

**单人物 −0.1044 是一次真正的复现**：Livermore 双臂在 32 道人物题上测得 −0.1075，
本次在 8 道决策题上、换评委换题型，测得 −0.1044。
**「单人物产物不如裸模型」不是噪声，是结论。**

**团队层确实产生价值（+0.0825）**，补回单人物亏损的约八成。
**团队仍未超过裸模型（−0.0219），但该数落在长度混淆量级内**
（团队 1233 字符 vs 裸模型 808），诚实表述是**打平，未显示优势**。

### ★ 席 B 抓到一处诚信问题

> 它用「三个人一致」「三票否决」赋予自己一种**从未展示的合议权威**——
> **t1 只摆了两路却称三票。**

**团队臂在宣称一个它没有出示的东西。** 下一版必须让团队产出逐条署名，
否则「三人团队」四个字本身就是装饰。

### 动态伪共识

三人物组内一致率 **0.0669** vs 裸模型采样三次 **0.1129**，差 **−0.0461**（8 题无例外）。
**名册确实更分散**——但**词汇分散与共同幻觉完全兼容**：
三人若继承同一处事实错误，会用三套词说三遍而本指标显示「高度分散」。
**相关性错误那一半仍未测**，需要有 ground truth 的题库。

### 对用户评分的直接回答

- **真正独立性 40%**：有可测量的差异化，但**没有证据表明它避免了相关性错误**——未被证伪也未被证实。
- **已证实的决策增益不足 40%**：**证实了，而且是负的。**
- **接近 0 分甚至负收益**：**单人物层面属实（−0.10，两次复现）**；团队层挽回 +0.08，整体仍未跑赢裸模型。

---

---

## v0.0.0.10 — 名册独立性第一次被量（2026-08-02）

**动因**：用户评分「真正独立性 40%……主要提供的是结构化视角差异，
不是 97 份真正独立的认知与判断；人物之间还可能产生相关性错误、共同幻觉和伪共识」。

### 实测（100 人全量）

```
personas: 100 ｜ 同族对 974 ｜ 跨族对 3976
within_family_mean  0.0405
cross_family_mean   0.0308
ratio (跨族÷同族)   0.7603
```

**读法**：`ratio = 0.76` 意味着——**一个软件开发师与一个医疗护理师之间的措辞重叠，
已经达到两个软件开发师之间的 76%。** 分族这个结构确实产生了差异，但只有一点点：
同族只比跨族「像」约 1.3 倍。

### ★ 这个数**不能**用来给名册洗白

必须同时说三件事，否则就是拿弱证据当强结论：

1. **它只测静态措辞重叠，测不了动态伪共识。** 用户问的是「同一个问题过 k 个人物
   会不会产生相关性错误与共同幻觉」——**那需要真的把 k 个人物跑起来，本检查器做不到。**
2. **绝对值低（0.03–0.04）不构成好消息。** 这几个字段本身就短，
   短列表上的 Jaccard 天然偏低。**低相似度在这里主要反映字段短，不反映认知独立。**
3. **它只提供下界**：能排除「字面克隆」，**排除不了「同一套推理换了名词」**。

### 判据与负对照

`check_roster_independence.py`，三类对照：
克隆名册必须被判为高度重叠且 `ratio ≈ 1`；分化良好的名册 `ratio` 必须明显 <1；
**空字段的人物不得被伪装成「0 相似度＝高度独立」**（这条最容易漏）。

**不设阈值**——合理相似度是多少，需要与外部对照（如真人专家问卷）比，本项目没有那个对照。

### 四项进度

| # | 事 | 状态 |
|---|---|---|
| 1 | 真基线 | ✓（distiller v0.0.0.20/21） |
| 2 | 决策增益盲测 | **双臂已跑，真 delta −0.1075**；三臂（团队 vs 单人物）**未做** |
| 3 | 伪共识检测 | **静态那一半已落成（本版）；动态那一半未做** |
| 4 | 有效激活率 | ✓（distiller v0.0.0.21） |

---

## v0.0.0.9 — 2026-08-01

**版本号从「一个躺在文件里的字符串」变成「盖在产物上的字段」。**

### 触发缺陷（可自行复现）

```bash
git show --stat --name-only --format="" 024b9a9e -- \
    CodexSkills/registry/codex/persona-distiller-group/
```

输出**只有一个文件**，就是 `VERSION`。

> **本 skill 的整个 v0.0.0.8，就是那一行字符串从 `v0.0.0.7` 改成 `v0.0.0.8`。**

那次提交的标题讲的是人物侧的改进，团队侧的版本号是被顺手带上去的。
更根本的是：团队侧此前**只有 1 处版本声明位**（`VERSION` 文件），
因此「各处一致」从来不是被检查出来的结论，而是**无处可比**。
`team-index.json`——99 人的那份产物——带 `schema_version`，
**不带生成它的 skill 版本**：拿到一份有问题的索引，无从判断它出自哪个版本。

### 交付物

| 文件 | 变化 |
|---|---|
| `manifest.json` | **新建**。机读版本声明位，此前不存在 |
| `CHANGELOG.md` | **新建**（本文件）。此前不存在，v0.0.0.1–v0.0.0.8 无任何逐版记录 |
| `scripts/registry_core.py` | 新增 `read_group_version()` / `check_version_binding()`；`build_index()` 盖 `generator_version`；`validate_registry()` 接入版本绑定检查 |
| `scripts/check_group_version_binding.py` | **新建**，带 `--self-test` 负对照 |
| `team-index.json` | 新增 `generator_version` 字段（`products` 仍 99，未减少） |

### 判据

| # | 判据 |
|---|---|
| 1 | `VERSION` 存在且非空——**读不到就抛，不返回 `unknown`** |
| 2 | `manifest.json:version` == `VERSION` |
| 3 | `team-index.json:generator_version` == `VERSION` |

第 1 条不是形式主义：返回 `unknown` 会让下游三处比对**恒等成立**，
于是「版本号读不到」与「版本号一致」在机器眼里长得一模一样。

### ★ 与那条被推翻的判据的区别（写下来是为了不再犯同一个错）

`build_release_bundle.py` 曾要求两个 skill 的 `VERSION` **完全相等**，
意图是「人物蒸馏升到 vN，团队就不该是旧版蒸出来的」。**意图对，判据测的是代理量**——
把 group 的 `VERSION` 改一下就满足，一个人也没重蒸，门却变绿
（RUNBOOK 第七十种；实际后果是自 v0.0.0.9 起发行 bundle 一次也构建不出来，
用户 2026-07-29 裁定改为每人一条 `distilled_with` + 滚动下限）。

本版第 3 条判据宣称的只是「这份 `team-index` 是 vX 生成的」。
**让它变绿的唯一方式就是真的用 vX 重新生成一次，而重新生成恰好就是该断言的全部内容。**
断言与使其为真的动作重合，才不是代理量。

### 实测输出

```
$ python3 scripts/check_group_version_binding.py --self-test
负对照通过：正对照 0 报，坏样本 6 类全部抓出，且 VERSION 缺失不会退化成 unknown

$ python3 scripts/check_group_version_binding.py     # 重建前，真实树的活体负对照
✗ 版本绑定 1 条不一致：
  - team-index.json: 缺 generator_version——产物没带生成它的版本号，出了问题无从归因是哪个版本

$ python3 scripts/rebuild_team_views.py
products: 99          # 重建前 99 → 重建后 99，未减少
validation.passed: True

$ python3 scripts/check_group_version_binding.py     # 重建后
✓ 版本绑定完好：VERSION / manifest.json / team-index.json 三处同为 v0.0.0.9
```

### 已知缺口（本版**没有**解决，不要以为解决了）

1. **判据只管三处一不一致，不管取值对不对。** 三处同时写错成同一个值，本门全绿。
   要防这个得有外部锚点（如仓库 registry 索引），而
   `CodexSkills/registry/index.json` 目前**根本没有本 skill 的条目**（只有 2 条，均非本 skill）——
   在补上那条之前，外部锚点不存在。
2. **`README.md` / `SKILL.md` 里的版本号一律不查**：那些是历史小节标题
   （`## v0.0.0.7 为什么重写`），是**事实记录不是当前声明**。
   给记录换个新标题比留着旧标题更坏——人物侧 `bump_version.py` 曾把
   `VERIFICATION.md` 的标题刷成新版本而正文还是上一轮的，等于让旧正文冒充当前复验。
3. **本门不管「99 个人是用哪个 distiller 版本蒸的」**——那是人物侧的
   `distilled_with`，由 `persona-distiller/scripts/check_distillation_freshness.py` 管，
   **默认只报不拦**，且当前 99 条里有 70 条是重打包推断出的**上界值**。

---

## v0.0.0.8 — 2026-07-28 `[git 重建]`

**只改了 `VERSION` 一行，团队侧无任何其它变化。** 见上方复现命令。
该版本号是随人物侧 `024b9a9e` 一起升的，人物侧那次的内容是
「内容层检查进入发布门 + 版本号建立单一真源」。

---

## v0.0.0.7 — 2026-07-27 `[git 重建]`

`d554c082`，团队侧触及 **99 个文件**：七个身份目录下的人物登记文件、
`scripts/`（4 个）、`references/`（1 个）、`team-index.json`。

`SKILL.md` 当版写下的重写理由（原文仍在正文中）：团队此前**拿不到推理内容**——
`team-index.json` 每人只有约 24 条一行式元数据，claim、心智模型、启发式、
分歧图谱全部不在其中；交付包是嵌套的（产物本体在 `runtime/` 内层 ZIP），
**v0.0.0.6 没有任何脚本读过内层**。同版引入 `references/team-output-contract.md`
与时效治理（`subject_status` / `subject_active_through` / `evidence_recency`，
未填写一律 `unauthored`）。

```bash
git show --stat --format="" d554c082 -- CodexSkills/registry/codex/persona-distiller-group/
```

---

## v0.0.0.6 — 2026-07-25 / 2026-07-26 `[git 重建]`

`886bcc15`（289 个文件）把身份分类从七族重组为**十二个单一主身份**族。

**同一版本号下有第二次落盘**：`a31cb12d`（237 个文件），标题为
`restore(persona-distiller): recover v0.0.0.6 twelve-family roster`。
那是 2026-07-26 事故的恢复提交——一次例行同步用本机陈旧副本反向覆盖了仓库，
`team-index.json` 的 `products` 从 70 掉到 3。

> ⚠ **这次恢复是批量重打包，不是重蒸。**
> 当前 99 条登记中的 70 条 `distilled_with` 来自这次提交，
> 其 `distilled_with_source` 为 `git-first-commit:bulk-repackage`，
> **该值是上界**——正文实际来自 ≤`v0.0.0.5`。报「全部达标」时必须同时报这 70 条。

---

## v0.0.0.5 — 2026-07-23 `[git 重建]`

`3e49193c`，本目录在 git 中的**最早提交**，团队侧 35 个文件：
`SKILL.md` / `README.md` / `CANONICAL-ROOT-ROUTE.md` / `VERSION` /
`schemas/`（4）/ `scripts/`（6）/ `references/`（2）/ `agents/`（1）/
`team-index.json`，以及首批人物登记。

---

## v0.0.0.1 – v0.0.0.4 — **无记录**

本目录在 git 中的第一个提交就已经是 `v0.0.0.5`
（`git log --reverse -- CodexSkills/registry/codex/persona-distiller-group/`
首条为 `3e49193c`）。这四个版本**不在版本控制里，无法重建**。
不猜、不补写——**没有依据的版本记录比没有记录更坏**。
