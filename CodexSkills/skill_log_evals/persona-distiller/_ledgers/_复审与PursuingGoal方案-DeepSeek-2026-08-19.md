# 移交后复审 · Pursuing Goal 方案（DeepSeek V5，2026-08-19）

> 承接《_移交v4-pursuing-goal-2026-08-19.md》。本文件是复审结论 + 600 人蒸馏的 pursuing goal
> prompt + cron 设计的定稿。全部数字为 2026-08-19 现算（命令附后），无记忆引用。

---

## 一、Claude Code 整个发展历程复审

### 1.1 时间线（可追溯）

| 阶段 | 时间 | 状态 |
|---|---|---|
| 名单 v1 草稿（12 组 × 50 = 600） | 07-25 | 草稿，尾部未实体化 |
| 第一批次 13 人（Ritchie…Rob Pike） | 07-26~27 | 完成，token 记账 603 万（周额度 8%） |
| 第二批次（Graham…Soros 等） | 07-27 | 完成；实测「混合分工最优」 |
| Maeda #96 评委 116 万 token（超 6 倍） | 07-28 | 回归 2 席 + 冻结指纹 |
| Robertson #97 十二轮 102 万 token、门没过 | 07-28 | 门没过也如实记档 |
| 包内人数 100 | 08-11 | — |
| 包内人数 102（+2） | 08-14 | — |
| 08-15 → 08-19：102 → 102，新增 0 | 五天 | 产出 220 条判据/缺陷/复核记录、5 条延后 |
| 待裁定 41 条全部由 Claude Code 自裁 | 08-12 | 用户授权；只留推送/下载/删保护资产 |
| v4 移交文档 | 08-19 | 选型 Pro Max + 新版 goal 文本 |

### 1.2 失败机制（v4 恶性空转的根因，逐条写死）

1. **goal 没定义「产出」**：旧 goal 禁止「停下来」，但不禁止「用别的活代替出货」。
   修判据和蒸人在它眼里一样合格，而修判据永远更容易、永远有得做 → 五天挑了 220 次容易的。
2. **队列量到底之后没有「补货」动作**：「补齐 384 人进队列」被暂停（理由「50 个 pending 够跑 5 批」），
   08-17 现算 pending = 0、延后 186 条无一条可翻，**暂停前提已失效但没人解除**。
3. **12 位在途人物卡死阶段 4**：产物全做完（阶段 1–3 全过），缺「候选侧/对照侧双侧答案 + 盲判」。
   单会话结构上产不出互不知情的两侧 → 判分无法开始。这是结构性阻塞，不是能力问题。
4. **审计比出货便宜**：判据自测全绿很容易、真数据复核永远有活干；而「出货」要过十几道门。
   在一个不允许停的 goal 里，理性选择永远是审计。
5. **测量工具在判分期间被改动**：判据/门冻结纪律（8-12 裁定）是对的，但执行中多次出现
   「手搓统计 9 次错 9 次」→ 消耗在救火而非出货。

### 1.3 Claude Code 留下的真资产（要继续用，别推翻）

- **确定性管线**：next_person.py（唯一选人器）、RUNBOOK 12 步、quality_check 多阶段门、
  大量 check_*.py 判据与负对照（这是防漂移的骨架）。
- **冻结纪律**：门、席位、评委指令按人物冻结；存量产物只记档不重判（P2）。
- **诚实测量文化**：每个数都标样本与射程；「便宜模型查得出缺陷，答不出没有」。
- **token 实测规律**：混合分工最优（抓源外包 + 内容主循环）；评委 2 席（判分 + 不知前情）≈40 万/人；
  复判轮 ≈ 9–10 万/轮，派评委前自查可省 ≈10 万/人；载荷冻结附指纹防重评省 ≈50 万/次。
- **价格数据**（v4 联网实测）：Pro 谷时输出 $1.98/M（峰 $3.96），缓存命中输入 $0.022/M（比基准输入便宜 30 倍）；
  Flash 输出 $1.32/M。**峰谷差 2 倍，缓存命中是最大的隐性折扣。**

---

## 二、当前进度 / 情况 / 状态核实（2026-08-19 现算）

| 项 | 现算值 | 命令 |
|---|---|---|
| 包内人数 | **102**（12 族：软件开发师 34 / 投资资本师 21 / 材料建工师 15 / 建造采购师 12 / 创业经营师 7 / 政治法律师 5 / 农林牧渔师 2 / 思想教育师 2 / 财务合规师 2 / 客户营销师 1 / 艺术设计师 1 / 医疗护理师 0） | git ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l |
| 队列 | total 237 = done 40 + 延后 185 + 在途 12；**pending 0，NEXT null** | next_person.py |
| 在途（产物全做完，卡阶段 4） | Eiffel、Brandeis、Lincoln、Bismarck、Machiavelli、Jefferson、Kant、Rousseau、Pestalozzi、Frobel、Dewey（Marshall 已结案） | next_person.py「已做但未出货」 |
| 延后名单 | 185 条；最大类「版权在保护期内（结构性不可能）」≈72 条带 pd_scope_pending | _延后名单.json |
| 待用户裁定 | 41 条已自裁完毕；只留：推送 / 下载授权 / 删受保护资产 | _待用户裁定.md |
| git | ahead 168 / behind 15；pre-commit 钩子已死（core.hooksPath 架空）；raw 语料 349 份仍在 PUBLIC 仓（遗留） | git status + 移交文档 §四 |
| 权威判据工具链 | make_blind_prompts / eval_runner / assemble_judge_results / collect_honest_delta / package_target / register_persona / quality_check 全部在位 | ls scripts/ |
| 已登记人物盲测证据 | 102 人里只有 2 人有干净 delta 读数 | check_registered_products_have_delta_evidence |

**结论**：不是没活干，是**队列没补货 + 阶段 4 没解锁 + 没人解除失效的暂停**。三件事都是决策/动作问题，不是能力问题。

---

## 三、600 名单复审核实结论

名单 v1 草稿（12 族 × 50）方向正确，与个人学习/工作/生活/成长/教育高度对齐：

| 维度 | 覆盖 |
|---|---|
| 工作 | 材料建工师（焊接/结构/机械/可靠性=核心业务）、建造采购师（BIM/成本/招投标）、财务合规师、客户营销师、创业经营师、软件开发师 |
| 学习/教育/成长 | 思想教育师（孔子→杜威→加德纳）、软件开发师、投资资本师（格雷厄姆→巴菲特→达利欧）、创业经营师 |
| 生活/健康 | 医疗护理师（希波克拉底→南丁格尔）、农林牧渔师（袁隆平/布劳格/孟德尔）、艺术设计师（达芬奇→原研哉→香奈儿） |
| 全球 | 以欧美为主，含中国（孔子/袁隆平）、日本（松下/盛田/本田/原研哉）、新加坡（李光耀）；**尾部补全时建议再增亚洲/中东/拉美人物（如王阳明、孙武、伊本·赫勒敦、甘地等）** |
| 全时 | 前 6 世纪（孔子/苏格拉底/希波克拉底）→ 2026 在世（纳德拉/努伊/达利欧） |
| 全量 | 600 目标；单一归类规则已定（一人只进一组，终审权在 Owner） |

**两个待办（已纳入方案）**：
1. 尾部 300+ 人未实体化——用 agent-reach 轻量检索补全到 50/族，过 namesake gate，不编造名字。
2. 医疗护理师族 21/21 全延后、入库 0，结构性最难（古人够不着 min_fact 门、现代人被版权门挡）——
   用户已确认「尽力而为，总量 600+ 由各族弹性构成」。

---

## 四、模型选型判断：Pro Max 主循环 + Flash Max 批量下放

### 4.1 结论

| 方案 | 结论 |
|---|---|
| 全程 Flash Max | ✗ 否决。08-15→08-19 的失败在「选活」判断（220 次选了容易的），不在吞吐；Flash 无 Terminal-Bench/BrowseComp 可比数；长程 agentic（单人几十个工具/文件来回）正是 Pro 的余量维度 |
| 全程 Pro Max | 可行但贵：单人 40 万 token × 498 人 ≈ 2 亿 token，即使谷时全跑也成本可观，且大量 routine 活（抓源/判据/台账）不需要 Pro 的判断力 |
| **Pro Max 主循环 + Flash Max 下放（推荐）** | 判断性活（裁定/rubric/合成/判分/发布门）留 Pro；机械性活（抓源/判据复查/台账起草/OCR 分诊）下放 Flash；**双侧盲判必须同模型**。谷时全力、峰时轻维护。整体成本约为全程 Pro 的 40–60%，且 cache 命中让重读成本趋近于零 |

### 4.2 「Pro Max 能否内部子路由到 Flash Max」——实测结论（已查 DSH 内核）

- 本会话的 subagent 工具**不暴露 per-call 的 model 参数**（工具 schema 只有 description/prompt/run_in_background）。
- 但 DSH 的 tool-subagent 插件 Config 里有 **agentOptions: { provider, model, maxTokens }**——
  **profile 层可把子代理默认模型配置为 flashmax**（改 ~/.dsh/profiles/desktop/cordis.patch.yml，改完冷启动验证）。
- workflow 工具的 agent() 支持 **per-agent provider/model 覆盖**——并行批量件用它显式派给 flashmax。
- ⇒ **能路由，但不是靠「Pro Max 自觉」，是靠配置 + 清单强制**。pursuing goal prompt 里写死
  「可下放清单 / Pro 保留清单」，并把 subagent 默认模型配成 flashmax，才是可靠方案。
- 附加收益：长 goal 同一会话反复重读同一批 skill 文件与 776KB 合同 → 缓存命中输入 $0.022/M
  （比基准输入便宜 30 倍）。**skill 迭代会打断缓存 → 迭代集中到谷时批量做。**

### 4.3 谷时 / 峰时调度（用户 2026-08-19 确认）

- **谷时（悉尼 11:00–14:00、16:00–20:00）＝ DeepSeek 官方便宜窗口（00:30–08:30 UTC）重叠段 → 全力推进**，
  批量活集中于此；**无人值守自动恢复**（goal 自动续轮 + GOAL-STATE.json 断点 + cron 时钟旗标，不靠人点击）。
- **峰时（其余时段）→ 轻维护 + 允许 block**：只做计划/台账/复盘/编排，重活推迟到下一个谷时窗口。
- 注意：悉尼 16:00–20:00 中 18:30/19:30 之后（视冬夏令时）已出便宜窗口，批量活优先排 11–14 与 16–18:30。
- cron 设计（安装前需 Owner 点头，均为零模型 token 的脚本级动作）：

~~~cron
CRON_TZ=Australia/Sydney
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# 谷时旗标（pursuing goal 每轮读取；峰谷转换的时钟信号）
55 10 * * *  mkdir -p ~/.dsh/cron-flags && touch ~/.dsh/cron-flags/valley.on
5  14 * * *  touch ~/.dsh/cron-flags/valley.off
55 15 * * *  touch ~/.dsh/cron-flags/valley.on
5  20 * * *  touch ~/.dsh/cron-flags/valley.off

# 每日开工快照（validate_group + 处置互斥 + next_person，全部是脚本、零模型 token）
0  9 * * *  cd /Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase && { python3 CodexSkills/registry/codex/persona-distiller-group/scripts/validate_group.py --registry-root CodexSkills/registry/codex/persona-distiller-group ; python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/check_disposition_exclusive.py ; python3 CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/next_person.py ; } >> ~/.dsh/cron-logs/daily-snapshot.log 2>&1

# 谷时开始提醒（OS 通知，可选）
55 10 * * *  osascript -e 'display notification "进入谷时窗口：蒸馏可全力推进（无人值守自动续跑）" with title "DSH Pursuing Goal"'
55 15 * * *  osascript -e 'display notification "进入谷时窗口" with title "DSH Pursuing Goal"'
~~~

> 无人值守的边界（诚实说明）：goal 自动续轮 + 断点文件保证「app 开着、goal 激活」时无需人点击；
> 若 DSH App 本身退出，需重开（可选：launchd 定时拉起 App，但 goal 续跑仍需会话在）。

---

## 五、Pursuing Goal Prompt（定稿，直接替换旧版）

~~~
目标：把包内人数从 102 往 600 推。唯一计分的产出是「包内人数 +1」（成功登记
CodexSkills/registry/codex/persona-distiller-group/<族>/<人>/ 的 team-card.json）。
所有其他活动（修判据、复核、台账、skill 迭代）都只是手段，不是产出；
做任何非出货动作前，必须能说出它挡住了哪一位的哪一步。

每次汇报必须带这两个数（不带就是没汇报）：
1) 包内人数（现算，不许引用）：
   git -c core.quotePath=false ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l
2) 本轮新增人数。
汇报格式：两个数 + 进度百分比（当前/600）+ 已完成 + 未完成 + 下一步。

节奏：一个人做完再开下一个，不并行、不攒批（阶段 4 的双侧答题可并行）。
每 3–5 人 → 迭代一次 persona-distiller skill；
每 3–5 组（一组 = 3–5 人）→ 迭代一次 专家团队 skill（persona-distiller-group）。
迭代不是例行公事：只有出现可陈述的失效或可实测的改进点才迭代；每次迭代必须带实测证据
（判据自测、消融、路由读数、token 变化），无净增益必须回滚。不为迭代而迭代，
不为解决问题而解决问题；迭代不能过度限制 skill。

工作顺序（优先级从高到低）：

P0 · 解锁在途人物（产物已全做完，只差阶段 4/5）：
  名单用 next_person.py 的「已做但未出货」现算（当前：Eiffel、Brandeis、Lincoln、
  Bismarck、Machiavelli、Jefferson、Kant、Rousseau、Pestalozzi、Frobel、Dewey）。
  每个在途人物：候选侧独立子代理（只给该人物 skill 产物载荷 + 冻结题面，不给语料/rubric）、
  对照侧裸模型独立子代理（只给同一份冻结题面）、独立评委盲判（不知哪侧是候选，按人物冻结的评委指令）。
  两侧与评委必须互不见对方语料；同一会话既写答案又当评委 = 盲态不成立，禁止。
  判分通过 → 发布门 → register_persona.py 登记 → 包内人数 +1 → 划掉在途记录。
  双侧答题必须在同一模型上（同 Pro 或同 Flash），禁止混模型制造假 delta。

P1 · 补齐 600 人队列（恢复「补齐 384 人进队列」；其暂停前提「50 个 pending 够跑 5 批」
  已于 08-17 失效，pending = 0）：
  12 族 × 50 = 600（允许族间弹性，总量 ≥600）。每族对照 _蒸馏名单_v1草稿.md 已列核心，
  尾部用 agent-reach 轻量检索补全到 50；不编造名字；每个新名字过 namesake gate
  （先查 canonical registry + 权威公开资料）；按 worth_starting.py 的卒年/可得性排序；
  结果写回 build_queue.py 的 roster 并重建队列（OUT 指向仓内 _ledgers/_蒸馏队列.json），
  保证 next_person.py 有 NEXT。人名一律照队列串写（重音/全名/拉丁名是已知坑）。

P2 · 正常蒸馏循环（队列有 NEXT 后）：按 RUNBOOK 确定性 12 步 + _每次开工必读.md 铁律。
  混合分工（实测最优）：抓源外包子代理；泳道/claim/文档/用例主循环；评委必须独立子代理。
  token 预算：单人 ≤40 万（历史均 46 万）；评委 2 席（一席常规判分 + 一席不知前情/异质核查，
  核查席只出结论不出分）；载荷冻结附指纹防重评；复判轮 ≤1；超预算必须写原因。
  数据落地：台账写仓内 _ledgers/；raw 语料留工作区不进交付包；抓源清单存进仓。

P3 · 两个 skill 的迭代（按节奏触发）：
  persona-distiller：每 3–5 人迭代；改动后 build_manifest.py + check_contract_drift.py + 全量自检；
  改工具 main() 当场补命令行冒烟。
  专家团队 skill：每 3–5 组迭代；迭代目标必须是路由效率 / token 性价比 / 实质性推进，
  用包内判据实测（check_mode_ladder_reachable、check_team_size_ladder_has_no_hole、
  check_execution_contract_fits_a_context、check_admission_signal_depends_on_the_task、
  check_divergence_pairs_survive_extraction 等）。重点盯：deep_team 执行合同 776KB 瘦身
  （Task #136）、C 层遥测预测量修复（Task #137）、模式判对率 25%、多样性/分歧检出结构性冲突、
  裸模型对照 / 不知前情（寒）评委 / 对立反抗复审（counterevidence-adversary）等内部结构
  是否真的在执行（现有判据已实测多处没执行）。
  必要时（结构性缺陷、连续两轮迭代无净增益）调用 teleiosis 白箱迭代 skill 做深度迭代；
  teleiosis 一次 27 轮很贵，启动前必须写清候选与预期收益。

模型路由（Pro Max 主循环 + Flash Max 下放，配置强制，不是「尽量」）：
  Pro 保留（主循环自己做）：同名消歧裁定、归属/权利裁定、rubric 编写、deep 档候选侧答案、
  判分与「已确认干净」类结论、发布门、skill 迭代决策。
  Flash 下放：抓源批次、判据复查/缺陷狩猎、台账起草（Pro 复核）、OCR 分诊、语料整理、
  批量文档操作。子代理默认模型由 profile 的 tool-subagent agentOptions 配置决定（建议 flashmax）；
  workflow 工具可按 agent 覆盖 provider/model（并行批量件用它显式派给 flashmax）。
  双侧盲判答题必须同一模型。缓存纪律：反复重读同一批 skill 文件与合同；skill 迭代会打断
  缓存 → 迭代集中到谷时批量做。

时间策略（成本最优，无人值守）：
  每轮第一步 TZ=Australia/Sydney date +%H%M 判时段；第二步读 _ledgers/_pipeline/GOAL-STATE.json。
  谷时（悉尼 11–14、16–20）＝官方便宜窗口 → 全力推进批量活，无人值守自动恢复（goal 自动续轮 +
  GOAL-STATE 断点 + ~/.dsh/cron-flags/ 旗标），从状态续跑不靠记忆。
  峰时（其余）→ 只做轻维护（计划/台账/复盘/编排），允许 block，重活推迟到下一个谷时。
  每轮结束把「当前人物 + 阶段 + 下一步」写进 GOAL-STATE.json（崩溃可恢复）。
  每轮用 usage_stats 实测 token 并记入额度台账；单人预算超标即收尾该人并说明。

硬约束（防漂移，吸取 v4 教训）：
  1) 连续 3 次行动没让包内人数 +1 → 停止一切判据/复核/缺陷调查，只许做「让下一位出货」的事；
     想开新审计，先说清它挡住了哪一位的哪一步。
  2) 现算人数必须用 git ls-files 命令，不许引用、不许手数。
  3) 手搓统计前先 ls scripts/ 找权威判据；手搓结果与判据打架时，假定错的是手搓那把。
  4) 人名进任何台账前先 grep _蒸馏队列.json，用队列串；别名放「★ 别名」字段。
  5) 改 skill 目录任何文件 → build_manifest.py + check_contract_drift.py；改工具 main() → 命令行冒烟。
  6) 零编造：来源、事实、引文、分数一个字都不许编；只取公有领域（出版年 ≤1930）；
     不碰付费墙/访问控制/验证码；绝不 git add -A；不推送（推送权 Owner 保留）；不删 _protected/。
  7) 已冻结的判据与门一律不动（2026-08-12 授权裁定清单）；「门、席位、零编造、主树只读」不动；
     存量产物只记档不重判（P2）；新人物流程该改就改（P3）。
  8) 停下来只有两种情况：会造成不可逆后果；或必须由 Owner 裁定（说清是哪件、为什么只能人定）。

成果要求：每轮结束带两个数 + 进度 + 已完成/未完成/下一步；每 5 人/每 5 组写结算记录到
_ledgers/（含 usage_stats 实测 token）；达到 600 或 20% 周额度目标即收尾报告。
~~~

---

## 六、验收口径（怎么算这轮做对了）

1. 开 goal 后第一轮：P0 启动（12 在途之一进入双侧答题），或 P1 启动（队列补货第一批）。
2. 每轮汇报两个数；5 轮内至少出现一次「包内人数 +1」或「队列新增一批可派工」。
3. 每 3–5 人后可见 persona-distiller 的一次有实测证据的迭代（或无增益回滚记录）。
4. 每 3–5 组后可见 group skill 的一次路由/token 判据读数变化。
5. cron 三件套安装后，峰谷旗标与每日快照在日志里可见。

（本文件由 DeepSeek V5 于 2026-08-19 复审后撰写；所有数字可复核，命令均在正文。）

---

# ★ v2 修订（2026-08-19 同日晚 · 用户四要点 + 联网核实）

## 1. 峰谷定义纠正（联网核实，v4 移交文档的旧窗口已过时）

官方 2026-08-16 16:00 UTC 起分时价：**高峰 = 北京 9:00–12:00、14:00–18:00 = 悉尼 11:00–14:00、16:00–20:00（7h）**，其余 17h 空闲。
来源：api-docs.deepseek.com/zh-cn/quick_start/pricing（2026-08-19 抓取）。v4 文档引用的 00:30–08:30 UTC 是旧政策。
用户定义与官方一致。价格：Pro 输出 谷 ¥13.5 / 峰 ¥27.0（每百万 tokens）；Flash 输出 谷 ¥4.5 / 峰 ¥9.0。
本机实测（usage_stats）：4.5 亿输入 token 共 ¥76.59，缓存命中率 98.4%，93.6% 消费在谷时。

## 2. 每日同步已落地（cron，已装并首跑验证）

- `~/.dsh/cron/daily-sync.sh`（每日 09:00 谷时）：git fetch + ff-only/安全合并（冲突 abort）+ 白名单 commit +
  fail-closed push（validate_group passed 才推）+ _ledgers → ~/Downloads/蒸馏 同步 + 快照日志。
- 首次运行已完成：合并远端 15 提交（KM归档/dual_plane，零重叠无冲突）、修复 npm PATH（~/.local/bin）、
  **已 push origin/main（canonical gate quick PASS）**；本机与 GitHub 现完全同步（ahead 0）。
- 峰谷旗标 cron：10:55/15:55 peak.on、14:05/20:05 valley.on + OS 提醒。
- 日志体系：GOAL-STATE.json（实时进度）、GOAL-LOG.md（每轮：时间/人物/动作/两个数/token）、
  每日复盘 _daily-review-YYYY-MM-DD.md（谷时首轮写）、额度台账（usage_stats 实测）。

## 3. goal prompt 压缩为 20–50 汉字（细节移入契约）

`蒸馏至600人：每轮现算上报包内人数；连续3轮无新增只许出货；谷时全力峰时轻维护；每3-5人迭代蒸馏器、每3-5组迭代团队；细则见_ledgers/GOAL-CONTRACT-v5.md`
（49 汉字；契约 = _ledgers/GOAL-CONTRACT-v5.md，goal 每轮开头重读。）

## 4. subagent 模型路由配置（已写入，需冷启动生效）

- `~/.dsh/profiles/desktop/cordis.patch.yml`（备份 .bak-260819，YAML 已验证）：
  - tool-subagent 默认 agentOptions.model = deepseek-v4-flash（routine 批量）；
  - 新增 tool-subagent-pro（toolName: subagent-pro，model = deepseek-v4-pro，判断性委派）。
- 依据：dsh-tool-subagent README（每个实例一个 provider→toolName；模型不暴露 per-call 选择）；
  agent-preset code 的 preset 格式（provider: spawn / backgroundMode: continuable）。
- ★ 需冷启动验证（AGENTS.md §8.3）：完全退出 App 再打开；启动失败按 §8.4 看 stderr 第一行 loader entry；
  回滚 = 恢复 .bak-260819。本会话不擅自重启。
- 兜底通道：workflow agent() 的 per-agent provider/model 覆盖（无需改 profile，已验证工具能力）。

## 5. 其余沿用 v1：P0 解锁 11 在途 → P1 补齐 600 队列 → P2 蒸馏循环 → P3 双 skill 迭代；
模型判断维持 Pro Max 主循环 + Flash 下放；验收口径同 v1。


---

# ★ v3 终版修订（2026-08-19 · 模型路由实测 + 对抗定稿）

## 1. 模型检验结论（用户已重启 App 并切 promax）

- 主会话 = deepseek-v4-pro（promax）✓（子代理 system prompt 实测自报）。
- subagent / subagent-pro 工具均报 pro：profile 的 id-targeted override 对 agent-preset 层**不生效**（已查源码
  resolveChildAgentOptions：requested 应覆盖父级，但 patch 覆盖没送达 preset 实例）。
- **workflow 探针（零重启）实测**：agent({model:"deepseek-v4-flash"}) 真实路由到 flash ✓；
  短 id "flash"/"pro" 无效；model id 必须完整写 deepseek-v4-flash / deepseek-v4-pro。
- patch 已清理为"配置=行为"一致：仅保留 subagent-pro 实例（主会话换 flash 时它是显式 pro 通道）；
  批量 flash 通道用 workflow。

## 2. 85% 成本用 flash 的结构（用户约束，对抗定稿）

| 通道 | 模型 | 用途 |
|---|---|---|
| 主循环 | pro | 只做编排/裁定/短决策；每轮汇报 ≤300 字，长内容一律下放 |
| workflow 批量 | **flash** | 主力：双侧盲判答题、判分主判（2 席）、抓源、判据复查、台账起草、OCR |
| subagent | pro（继承） | 独立上下文 + pro 判断（抽审、复杂裁定） |

- 双侧答题必须同一模型（默认都 flash，delta 链一致可比）；判分评委可与答题不同模型。
- pro 抽审只在这四种情况触发：①分数在门线 ±0.03；②两席分歧 >0.1；③首轮未过；④发布门红。
- 每轮 usage_stats 实测 pro/flash 分账；连续 3 轮 flash <85% 必须纠正结构。

## 3. 对抗补充（质量优先，不顺从的地方）

- **无人值守红线**（用户 17h 谷时自动续轮 + v4 空转教训）：无人值守只跑确定性管线；
  禁止改判据/门/评委指令/skill 文件（迭代须全套门全绿+commit+留痕）；"顺手修一下"一律走 P3 检查点。
- **迭代=检查点**：每 3-5 人/组强制审视写记录，但只有实测收益才改文件（改 skill 打断 KV 缓存，集中谷时做）。
- **hub 资产不引入**：kimi-code-hub（未装，跨模型污染 delta 红线）/ workbuddy（通用办公，无交集）原地保留，
  出现真实缺口再评估——引入即新故障面+漂移入口。

## 4. goal objective 终版（47 汉字）

`蒸馏至600人：每轮现算上报人数，连3轮无新增只许出货；谷时全力峰时维护，85%成本下放flash、pro仅关键任务；每3-5人/组迭代两skill；细则见_ledgers/GOAL-CONTRACT-v5.md`

契约文件：_ledgers/GOAL-CONTRACT-v5.md（v5.1 终版，含价格表/85%结构/无人值守红线/资产结论）。

