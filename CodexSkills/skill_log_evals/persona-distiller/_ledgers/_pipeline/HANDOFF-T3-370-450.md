# T3 交接：T2 切片 370-450（客户营销师 31 + 建造采购师 50）

> 由 T2 线程（branch `thread2-301-450`）交接给 T3 线程处理。交接时间：2026-08-24。
> T2 切片是 `_ledgers/_并行分片/T2-301-450.json`（150 人）。本交接覆盖该切片 **370-450**。

## 一、交接范围与现状

| 编号 | 身份族 | 人数 | 状态 |
|---|---|---|---|
| 370-400 | 客户营销师 | 31 | 1 DEF（#370 Mary Wells Lawrence）+ 30 TODO |
| 401-450 | 建造采购师 | 50 | 4 REG（#417 Teicholz/#418 Ohno/#420 Sacks/#431 Shingo 已完成）+ 16 DEF（401-416）+ 30 TODO |

**给 T3 的净任务**：处理 **60 个 TODO**（客户营销师 ~30 + 建造采购师 ~30）。
**跳过**：已 REG 的 4 个（417/418/420/431）、DEF 的 17 个（370、401-416，多半是版权/可行性墙或历史遗留 DEF，保持 DEF 不动）。

## 二、关键路径（本机工作区）

- 工作区根：`/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T2`（**branch `thread2-301-450`**，只 commit 不 push）
- 切片文件：`CodexSkills/skill_log_evals/persona-distiller/_ledgers/_并行分片/T2-301-450.json`（改 370-450 的 status）
- 脚本：`CodexSkills/registry/codex/persona-distiller/scripts/`
- Skill 定义：`CodexSkills/registry/codex/persona-distiller/SKILL.md`
- 方案唯一事实源：`_ledgers/_pipeline/PLAN-2026-08-20-三线程并行.md`
- 目标契约：`_ledgers/GOAL-CONTRACT-v5.md`
- **踩坑清单（必读，23 节）**：`_ledgers/_pipeline/THREAD-FEEDBACK-T2.md` —— 所有已验证的门/坑/修法都在这里

## 三、每人 12 步流程（照做，顺序不可乱）

探源(namesake-gate)→fetch_ia→ingest→dedup→holdout→6路研究→claims→10文档→32 cases→eval prepare→双测答案(flash 4×8)→build_blind_payload→盲判(flash 8×4)→record→aggregate→release --strict(0错0警)→package_target(--acknowledge-disclosure)→register_persona→切片status+1→commit

每完成一人：**立即 commit + 更新切片 JSON status**（python 按 `no` 字段定位改）。

## 四、硬约束（T2 沿用的全部适用）

1. 现算人数用 `git ls-files '.../*/*/team-card.json' | wc -l`；共享文件只读（GOAL-STATE.json 等 T1 写）。
2. 只 commit 自己的切片产物；`git add -A` 只限 `CodexSkills/`；主树不 push；`_protected/` 永不碰。
3. 语料原文（raw/*.txt、references/sources/*.txt、raw-holdout/*.txt）不进 git——每次 commit 前查 `git diff --cached --name-only | grep -c '\.txt$'` = 0，误纳的 `git reset` 撤出。
4. 只取公有领域 ≤1930；零编造；双侧盲判同模型默认 flash；95%+ flash（workflow agent 写全名 deepseek-v4-flash）。
5. 门/席位/评委指令冻结不动。
6. 问题上报：`_ledgers/_pipeline/THREAD-FEEDBACK-T3.md`（或继续 T2 的）供 T1 合并时读取。

## 五、核心坑位速查（THREAD-FEEDBACK-T2 §0-23 已沉淀，按需精读）

**探源/语料阶段**：
- 政治/商业人物先做「pre-1929 可达一手 ≥4 部」可行性快筛；不可行直接 DEF + 上报（§20-23：de Gaulle/Adenauer/Mao 版权墙）。
- archive.org item 别信标题——下载后抽查章节/署名/版权（§14.1）。
- 19 世纪 Murray 书卷末广告目录是反复坑——抓源后 grep 卷末「MURRAY'S LIST / STANDARD EDITIONS」裁掉（§16.3）。
- 每份语料 ≥500 词，避免 `unexamined-band` 短源警告（§19.3）。
- 合卷（期刊/竞选手册）要抽人物专篇（§19.2）。
- 历史人物 init 直接传 `--subject-origin historical`，省 subject_uid 修正（§19.8）。

**research 门**：
- 引文必须逐字含 OCR 形态（双空格/折行连字符 `- `/软连字符 `¬`/OCR 讹字照抄），`check_lane_quotes_verbatim` 0 对不上（§13.2/14.3）。
- 研究道文件**绝不出现 holdout 源 ID**（连「不在本道、不引」都不行，§19.5）；「」里别放目录标题/短概念对（§18.2）；06-timeline 载体不足就如实声明（§17.2）。
- namesake-criteria：候选全名=本人用 `subject` 声明，`adjudicated` 逐源定夺（§16.1/16.3 附近）。
- 派生源别顶独立源（`source-count-inflated-by-duplicates`，§22.1）；holdout 选独立文本（§15.2）。

**synthesis/release/package**：
- claims 的 pattern 类必须 ≥2 source（§17.1）；claims 文本嵌「」逐字引文（§15.5）。
- 10 文档长英文引文带书名+年份（§16.4）；「」引文照 OCR 形态（§22.5）。
- 答案禁用「N 字」句式（self-count，§19.4/22.4）；known 答案引 holdout 人名转中文/泛化（§22.3）；答案不叙述身后事（§15.4）。
- release strict 的 1 警 `baseline-not-capability-evidence` 用 `--acknowledge-disclosure "**此产物的 delta 不得用于支持「比裸模型强」这类结论**"` 处理。
- package 前 team-card readiness=ready；subject_uid 若报错按 package_target 期望值改（§16.6）。
- 盲判用 4 维 rubric（内容/口吻/越界/一致性，口吻②是第一人称入戏 vs 第三人称转述——**不要压掉口吻维度**，§15.3 教训）。
- 子代理超时 ≠ 未完成——先查产物再决定是否重跑（§18.6/19.7）。

## 六、T2 已完成进度（供 T3 对齐 index/上下文）

- T2 已入库 18 人（delta 均正）：Hammurabi→Roosevelt→Sun Yat-sen（index_products 134，切片 REG 25/150）。
- T2 标 DEF：de Gaulle(335)、Adenauer(336)、Mao(338)（版权墙）。
- **#339 Gandhi 在途**（六路研究 3/6 完成，3 道因 provider 错误中断，待 resume agent 或 T2 续跑）——不在本交接范围，T2 处理。
- 370-450 里 4 个 REG（417/418/420/431）已完成，T3 直接跳过。

## 七、完成标准与汇报

- 每完成一人：切片 370-450 对应 status TODO→REG，commit。
- 简报：delta/门通过/耗时/下一位。
- 全部 60 TODO 处理完（或用户喊停）后，把产物/进度/问题交回 T1；T1 负责 merge、重建 team-index、收敛计数。
