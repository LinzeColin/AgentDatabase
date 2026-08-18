# Pursuing Goal 契约 v5（2026-08-19 定稿 · DeepSeek）

> 本文件是 goal 的唯一执行细则。goal objective（≤50 字）只写计分规则；一切细节以本文件为准。
> 承接《_移交v4-pursuing-goal-2026-08-19.md》；峰谷定义已联网核实纠正（v4 旧窗口过时）。

## 0. 计分与汇报（每轮强制）

- 唯一计分产出：包内人数 +1（team-card.json 成功登记）。其余活动（判据/复核/台账/skill 迭代）只是手段。
- 每次汇报必须带两个数：① 包内人数（现算，不许引用）：
  `git -c core.quotePath=false ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l`
  ② 本轮新增人数。格式：两个数 + 进度（当前/600）+ 已完成 + 未完成 + 下一步。
- 连续 3 次行动没让包内人数 +1 → 停止一切判据/复核/缺陷调查，只许做「让下一位出货」的事；
  想开新审计，先说清它挡住了哪一位的哪一步。

## 1. 峰谷时段（2026-08-19 联网核实：官方 2026-08-16 16:00 UTC 起分时价）

| 时段 | 悉尼时间 | 时长 | 策略 |
|---|---|---|---|
| **峰时（贵）** | 11:00–14:00、16:00–20:00 | 7h | 只做轻维护（计划/台账/复盘/编排），允许 block，重活推迟到谷时 |
| **谷时（便宜）** | 其余 17h（20:00–11:00、14:00–16:00） | 17h | **全力推进**批量活；无人值守自动恢复 |

官方价格（元/百万 tokens；峰=谷×2）：Pro 输出 谷 ¥13.5/峰 ¥27.0、缓存命中输入 谷 ¥0.15/峰 ¥0.30、未命中输入 谷 ¥4.5/峰 ¥9.0；
Flash 输出 谷 ¥4.5/峰 ¥9.0、命中 谷 ¥0.05/峰 ¥0.10、未命中 谷 ¥1.5/峰 ¥3.0。
本机实测（usage_stats）：4.5 亿输入 token 仅 ¥76.59，**缓存命中率 98.4%**，93.6% 消费落在谷时。

无人值守规则：每轮第一步 `TZ=Australia/Sydney date +%H%M` 判时段 + 读 `~/.dsh/cron-flags/` 旗标；
第二步读 `_ledgers/_pipeline/GOAL-STATE.json`；每轮结束写 GOAL-STATE（当前人物+阶段+下一步）。
goal 自动续轮 = 无需人点击；App 退出需重开（cron 09:00 每日同步会留下断点日志）。

## 2. 工作顺序（优先级从高到低）

**P0 · 解锁在途人物**（产物已全做完，只差阶段 4/5；名单用 next_person.py「已做但未出货」现算）：
- 候选侧独立子代理：只给该人物 skill 产物载荷 + 冻结题面（不给语料/rubric）；
- 对照侧裸模型独立子代理：只给同一份冻结题面；
- 独立评委盲判：不知哪侧是候选，按人物冻结的评委指令；两侧与评委互不见对方语料；
- 判分过 → 发布门 → register_persona.py 登记 → 包内人数 +1 → 划掉在途记录。
- **双侧答题必须同一模型**（同 flash 或同 pro），禁止混模型制造假 delta。

**P1 · 补齐 600 人队列**（恢复「补齐 384 人进队列」，暂停前提已于 08-17 失效）：
- 12 族 × 50 = 600（允许族间弹性，总量 ≥600）；每族对照 _蒸馏名单_v1草稿.md，
  尾部用 agent-reach 轻量检索补全到 50；不编造名字；新名字过 namesake gate；
  按 worth_starting.py 卒年/可得性排序；结果写回 build_queue.py（OUT 指向仓内 _ledgers/_蒸馏队列.json）并重建队列，
  保证 next_person.py 有 NEXT；人名一律照队列串写。

**P2 · 正常蒸馏循环**（队列有 NEXT 后）：RUNBOOK 12 步 + _每次开工必读.md 铁律；
混合分工（抓源外包/泳道·claim·文档·用例主循环/评委独立）；单人 ≤40 万 token；评委 2 席
（一席判分 + 一席不知前情异质核查，核查席不出分）；载荷冻结附指纹；复判轮 ≤1；
台账写仓内 _ledgers/；raw 留工作区不进交付包；抓源清单存进仓。

**P3 · 两个 skill 的迭代**：
- persona-distiller：每 3–5 人迭代；改后 build_manifest.py + check_contract_drift.py + 全量自检；改 main() 补冒烟；
- 专家团队 skill：每 3–5 组迭代；目标 = 路由效率/token 性价比/实质性推进，用包内判据实测
  （check_mode_ladder_reachable、check_team_size_ladder_has_no_hole、check_execution_contract_fits_a_context、
  check_admission_signal_depends_on_the_task、check_divergence_pairs_survive_extraction 等）；
  重点：776KB 合同瘦身（Task #136）、C 层预测量（Task #137）、模式判对率 25%、分歧检出 0/72、
  裸模型对照/寒（不知前情）评委/对立反抗复审是否真在执行；
- 迭代必须有实测证据，无净增益回滚；不为迭代而迭代；迭代不超限 skill；
- 必要时（结构性缺陷/连续两轮无净增益）调 teleiosis 白箱迭代（一次 27 轮，先写清候选与预期收益）。

## 3. 模型路由（配置强制，不是「尽量」）

- 主循环（本会话，Pro）：同名消歧裁定、归属/权利裁定、rubric 编写、deep 档候选侧答案、判分与
  「已确认干净」结论、发布门、skill 迭代决策。
- subagent（profile 已配默认 `deepseek-v4-flash`，需冷启动生效）：抓源批次、判据复查/缺陷狩猎、
  台账起草（Pro 复核）、OCR 分诊、语料整理、批量文档。
- subagent-pro（profile 已新增，需冷启动生效）：需要独立会话但需要 Pro 判断的委派（盲判评委等）。
- workflow 工具 agent() 支持 per-agent provider/model 覆盖：并行批量件显式派 flash。
- 缓存纪律：长 goal 反复重读同一批 skill/合同文件命中 $0.022/M（实测命中率 98.4%）；
  skill 迭代打断缓存 → 迭代集中到谷时批量做。

## 4. 每日同步 / 日志 / token / 复盘（防丢失、防漂移）

- **cron 每日 09:00（谷时）daily-sync.sh**（已装）：git fetch + ff-only/安全合并 + 白名单 commit +
  fail-closed push（validate_group passed 才推）+ _ledgers → ~/Downloads/蒸馏 同步 + 开工快照日志；
  日志 `~/.dsh/cron-logs/daily-sync.log`。
- **实时进度**：`_ledgers/_pipeline/GOAL-STATE.json`（每轮更新：当前人物/阶段/下一步/时段）。
- **运行日志**：`_ledgers/_pipeline/GOAL-LOG.md`（每轮追加一行：时间/人物/动作/两个数/token 实测）。
- **单位任务 token**：每人物完成时用 usage_stats 实测记录（评委+主循环），写入 GOAL-LOG 与额度台账；
  单人超 40 万须写原因。
- **每日复盘**：每个谷时开始的第一轮，写 `_ledgers/_daily-review-YYYY-MM-DD.md`：
  昨日新增/卡点/教训/明日计划；由 daily-sync 推上 GitHub。

## 5. 硬约束（防漂移，吸取 v4 教训）

1) 现算人数必须用 git ls-files 命令，不许引用、不许手数；
2) 手搓统计前先 ls scripts/ 找权威判据；打架时假定错的是手搓那把；
3) 人名进台账前 grep _蒸馏队列.json，用队列串；别名放「★ 别名」；
4) 改 skill 目录任何文件 → build_manifest.py + check_contract_drift.py；改工具 main() → 冒烟；
5) 零编造；只取公有领域（出版年 ≤1930）；不碰付费墙/访问控制/验证码；绝不 git add -A；
   不删 _protected/；不把 private 资产推上 PUBLIC 仓；
6) 已冻结判据与门一律不动（2026-08-12 授权裁定）；存量产物只记档（P2）；新人物流程可改（P3）；
7) 停下来只有两种情况：不可逆后果；必须 Owner 裁定（说清哪件、为何只能人定）。

## 6. 完成定义

- 达到 600 人，或用户喊停；每 5 人/每 5 组写结算（含 usage_stats 实测 token）。
- 本文件由 goal 每轮开头重读（不靠记忆）。
