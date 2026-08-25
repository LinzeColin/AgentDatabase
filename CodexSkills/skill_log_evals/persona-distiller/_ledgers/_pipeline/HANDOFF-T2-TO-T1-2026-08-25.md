# 交接 prompt：T2 线程 → T1 主线程（2026-08-25 用户喊停后归档版）

> 用法：把下面「## 交接 prompt 正文（可直接复制给 T1）」整段复制给 T1 线程/agent 即可。
> 本文件落盘于 `_ledgers/_pipeline/`，已 commit，归档不丢。
> 本文件是**自包含**的：不依赖任何会话上下文，T1 只按本文件 + 文中指到的既有文件即可完成合并。

---

## 交接 prompt 正文（可直接复制给 T1）

你是 persona-distiller「蒸馏至 600」三线程中的 **T1 主线程**。T2 线程已按用户指令收尾终止。请读取以下交接，完成合并与收敛。下方「T1 必读文件」均为既有落盘文件，直接按路径读。

### 一、T2 线程结论（一句话）

T2 负责的切片 **301-450** 已按用户喊停终止；本线程完成 **20 人全流程入库**（delta 全部为正），**100 人标 DEF**（版权墙为主），**20 人 TODO 未做**（含半途的 Story #343）。**index 全局 155**（T2 入库 20 + T3 并行 16 + 他线程 Seth Godin 等）。

### 二、T1 必读文件（按序）

1. `_ledgers/_pipeline/THREAD-FEEDBACK-T2.md` —— **29 节，T2 全部踩坑与决策记录，合并时必读**（尤其 §20-27 版权墙 DEF 判例、§28 Harlan 全流程、§29 收尾说明）
2. `_ledgers/_并行分片/T2-301-450.json` —— T2 切片最终状态：**REG 30 / DEF 100 / TODO 20（150 人）**
3. `_ledgers/_pipeline/HANDOFF-T3-370-450.md` —— 370-450 已交 T3，切片由 T3 并行更新（T2 只读）
4. `_ledgers/_pipeline/HANDOFF-2026-08-20.md` —— 全流程 12 步 + 10 条踩坑清单（接手者必读）
5. `_ledgers/_pipeline/PLAN-2026-08-20-三线程并行.md` + `_ledgers/GOAL-CONTRACT-v5.md` —— 并发规则 + 目标契约
6. `_ledgers/_pipeline/GOAL-STATE.json` —— 由你（T1）维护，T2 从未写
7. `_ledgers/_pipeline/RUNBOOK.md` + `PLAYBOOK-quick档盲判流水线-2026-08-20.md` —— 流程手册

### 三、T2 本线程 20 人入库清单（index 从 134 → 154 贡献）

全部在 branch `thread2-301-450`（T2 只 commit 未 push，**需 T1 合并**）：

| # | 人物 | delta | 备注 |
|---|---|---|---|
| 1-18 | Hammurabi → Sun Yat-sen（18 人） | 均正 0.107–0.141 | 政治法律师族，全流程 |
| 19 | Gandhi #339 | +0.114 | index 151 时 |
| 20 | **Harlan #342** | +0.0617 | 候选 0.910 vs 基线 0.849，59 胜/3 平/2 负，16/16 套组为正，commit 0471fc57e |

### 四、T2 标 DEF 的 100 人（政治法律师族版权墙为主）

- **本线程标 DEF**：335 de Gaulle、336 Adenauer、338 Mao、340 Nehru、341 Atatürk（均「成体系著作在版权期」，探源已核实，见 THREAD-FEEDBACK §20/21/23/26/27）
- 其余 DEF 为切片预置（370-450 客户营销/建造采购族为主）
- **可行者特征**（供继续蒸馏）：卒于 1929 前或主要著作 pre-1929。已确认可行未做：343 Story（半途，见下）、344 Kent、345 Bracton、346 Coke、347 Hale、348 Erskine、349 Mansfield、350 Roberts 等 19 世纪及更早法学家

### 五、Story #343 半途状态（可续作，重要）

探源✅（Q1368374，1779-1845，12 部一手全 PD）→ gate✅ → init✅ → **语料✅（10 train + 1 holdout=Equity Pleadings 1838，corpus 门 PASSED，commit eeee5eeac）** → **六路研究✅（research 门 0 错 0 警，commit d30ab7506）** → **claims/10文档/32cases/盲判未做**。

产物全在 `_corpora/wip-joseph-story-343/` 已 commit。续作从 claims 阶段开始即可（12 步流程第 7 步）。

**Story 专属踩坑（THREAD-FEEDBACK §29.3）**：
① 研究笔记边界声明不得点名 holdout 的 src-id/书名（触发 research.invalid-source + corpus.holdout-work-named 双门）——只写「未分配源一律不引」
② 引文必须逐字连续，不得「不留痕迹清理」（去逗号/缝合断句/折叠词距会被 check_lane_quotes_verbatim 抓），跳过处用显式省略号
③ 19 世纪人物 conversations 道用「无独立会话一手 + 演讲/书信转述替代」声明可过门
④ holdout 已换为 Equity Pleadings 1838（原拟 Misc Writings 1846 与 Life and Letters 共享书信段、overlap 硬失败）

### 六、T2 合并动作清单（T1 执行）

1. `git merge thread2-301-450`（T2 分支；T2 未 push，本地分支即可）
2. 合并时注意：T2 在 `_ledgers/_pipeline/THREAD-FEEDBACK-T2.md`、切片 342→REG 等有写入；切片 370-450 的 status 由 T3 更新，**重建切片/收敛计数时以 T2+T3 合并结果为准**
3. 重建 team-index、收敛计数：index 现状 155；T2 入库 20 人 + T3 16 人（index 从 134 涨到 154 时）+ 他线程 Seth Godin（155 时）
4. 若后续继续蒸馏：worth_starting.py 排序选人；**优先续作 Story #343**（半途，产物齐）
5. 迭代两 skill 时读取 THREAD-FEEDBACK-T2.md 全部 29 节（§25-29 为最新 5 人经验：Gandhi/Nehru/Atatürk/Harlan/收尾）

### 七、红线提醒（T2 已遵守，合并时勿破坏）

- 主树只读、worktree 开发、`_protected/` 永不碰、语料 .txt 不进 git、只 commit 不 push（T2 全部遵守）
- 共享文件（GOAL-STATE.json 等）只 T1 写
- 门/席位/评委指令冻结不动（`references/pipeline/judge_prompts/` 下的 seat_D_score.md / seat_E_strict.md 一字未改）

---

## 附加：T2 遗留问题（无阻塞，供参考）

1. **356 Seth Godin 标 REG**：registry 有 `seth-godin` 目录、index 155 含它——但 Seth Godin（1958 年生）按版权约束本应 DEF，疑为他线程/早期标记。**建议 T1 收敛时核查该注册的版权依据**（若为误标可降级 DEF 或补文档）。
2. **GC 警告**：`AgentDatabase/.git/worktrees/AgentDatabase-T2/gc.log` 存在（unreachable loose objects 警告）——按铁律清理缓存用 `git gc`，**禁止 `--prune=now`**。
3. **quality_check.py 小 bug**：`markdown_report` 假定 warnings 全为 dict，但 `run_lane_quotes_verbatim` 以字符串 append warning，二者相遇时 md 报告生成崩溃（json 报告正常）。不影响流水线，可顺手修（line ~616）。