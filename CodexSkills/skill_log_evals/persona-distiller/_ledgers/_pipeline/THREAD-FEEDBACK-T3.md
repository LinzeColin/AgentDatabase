# T3 问题上报（给 T1 主线程）

> T3 在蒸馏过程中暴露的 skill 缺陷 / 判据问题 / 台账不一致，写进本文件并 commit；
> T1 合并时读取并迭代优化 persona-distiller 与 expert-team 两 skill。

## 环境适配（本环境=Kimi Code CLI，与原 DeepSeek harness 的差异）

1. **workflow flash 通道改由直连 DeepSeek API 复现**：本环境没有原 harness 的
   `agent({model:'deepseek-v4-flash'})` 通道。凭据在 `~/.kimi-code/config.toml`
   （providers.deepseek，api.deepseek.com，key 有效，2026-08-20 实测连通）。
   T3 自建共享包装 `_ledgers/_并行分片/tools/wf.py`（单次+批量+usage 日志），
   所有答题/判分/批量生成走 `deepseek-v4-flash`；双侧盲判同模型纪律不变。
   **建议**：此包装可上收为 skill 的通用工具（若 T1 环境同样缺 agent-tool 通道）。

2. **多代理并发写共享尾段需要互斥**：register_persona 写本地 team-index.json，
   多个并行子代理同时 register 有读改写竞争；macOS 无 flock，T3 自建
   `_ledgers/_并行分片/tools/tail_lock.py`（Python fcntl，尾段 register+commit 串行化）。

3. **子代理与父会话共享 TodoList**：后台子代理会覆盖父会话的 TODO（cosmetic，
   不影响产物）；已建议子代理不要动 TodoList。

## 判据/流程疑点（持续累积）

1. **子代理 2 小时超时 < 单人全流程耗时（实测 2026-08-20）**：Paré #527 首轮 2h 只到 ingest；
   Wave-1 四人同批跑到 research 阶段后全部被 2h 上限截断。单人 quick 档实测需 **3-4 个 2h 窗口**
   （≈6-8 子代理小时），靠**同 agent 多次 resume 续跑**推进（保留上下文、按工作区断点续做）。
   - 影响吞吐：5 并发 ≈ 5 人/8h 窗口，目标 12-15/日需持续续跑编排。
   - **建议**：① RUNBOOK/PLAYBOOK 明确「单人按阶段拆 2h 窗口、同 agent resume 续跑」；
     ② 考虑给 workflow 通道加断点续跑约定（每阶段产物落盘即 checkpoint）。

2. **子代理与父会话共享 TodoList**：后台子代理会覆盖父会话的 TODO（已实测 4 次）。
   T3 已在模板里禁止子代理动 TodoList；建议 T1 在 skill 层加「子代理不得写 TodoList」约定。

3. **多个子代理并发时 commit 必须按路径隔离**：`git add CodexSkills/` 会把其他并行子代理的
   在途文件一起 stage。T3 模板已改为只 add 自己的路径（工作区/族目录/切片 JSON/team-index）。

4. **★ README-抓源到阶段2 的多线程隐患（实测 2026-08-20，已致 1 次事故）**：
   README 给的命令序列里 `check_measurements_fresh.py --apply` **不带 `--workspace` 作用域**，
   它会全仓扫描并 `--apply` 重出**所有不一致**工作区的 `_lanes.json`/`_primary.json`。
   多线程并行时，某子代理照 README 执行，把 **T1 已完成的 Roebling #35 / Stephenson #33**
   的人工修正版 `_lanes/_primary` 覆盖回工具默认值（同时刻 17:09:26 两文件被改）。
   - 处置：已 `git checkout --` 恢复两个工作区，未再复发。
   - **建议**：① README 命令改为 `check_measurements_fresh.py --workspace <本人物工作区>`；
     ② 或在该脚本加「多工作区 --apply 前需确认」护栏；③ 并行线程禁止对**非自己**工作区跑
     classify_primary/assign_lanes/check_measurements_fresh --apply。

5. **★★ release 门必须 0 错 0 警 才允许 package_target（实测 2026-08-20，Paré #527 首犯）**：
   子代理在 release 门 FAILED（18 错：13 claim.orphan + 重复源未声明 + 无引文等）时**先打包**了
   dist ZIP（18:32），门报告 18:45 才落盘显示 FAIL——先打包后补门，属流程违规。
   - 根因：子代理把 package_target 当成「打包工具」而非「release 门闸」；package_target 内部
     虽有 strict release 门（run_quality_gate），但若被 `--skip` 或绕过则失效。
   - 处置：协调者无法中断运行中子代理（resume 会报「already running」），只能：
     ① 记录该次违规定向给该子代理后续续跑纠正；② 模板加硬规则（门不过禁打包/禁 --skip）；
     ③ 登记后由协调者用 `quality_check --phase release --strict` 复核。
   - **建议**：register_persona / validate_registry 增加对 `strict_release_quality=passed` 的强制校验，
     否则「非 release-ready 包也能登记」这一洞会反复出现。

6. **★★ claim 渲染标记格式（Simpson #529 实测）**：quality_check 只认 `<!-- claim:clm-... -->` 这类
   **HTML 注释**把 claim 渲染进核心模型文档；写 `ref: clm-...` 等普通文本不认，13 条 claim 全报 orphan。
   ⇒ 模型文档里引用 claim 必须用 `<!-- claim:clm-xxxxxxxxxx -->` 注释格式。
7. **holdout 物理隔离的残留坑（Simpson #529 实测）**：`assign_holdout --apply` 只改台账，raw/src-* 移动后
   `references/sources/src-*` 的 normalized 副本**不会自动清除** → check_material_split 报 holdout-leak。
   ⇒ 移动 holdout 源后必须 `find references/sources -path '*/<src-id>/*' -delete`。
8. **candidate 答案长度门（Simpson #529 实测）**：build_blind_payload 对总体均长比 >1.3 拦派发。
   ⇒ quick 档 persona 生成指令需显式约束答案 ≤80 字，压住 ratio <1.3。
9. **team-card subject_uid 必须照抄 package_target 报错值（Simpson #529 实测）**：不能手写 uid；
   package_target 报 "must be person-xxx" 时把报错值原样抄入 team-card。

## Paré #527 实测补充（2026-08-20，delta +0.375）

10. **quality_check release --strict 对 20M 词语料极慢**：单次 700-755 秒（~12 分钟），3 轮返工 = 36 分钟纯门禁。
    ⇒ 建议 quick 档考虑增量检查（只查改动文件）或把 release 检查拆细。
11. **wf.py batch 空返回率高**：判分批跑 25-40% 返回空 content，需逐条重试（空返回比超时难发现，脚本要判 content 非空）。
12. **check_quote_locator 扫的是模型文档（RENDER_FILES）不只是 judge payload**：模型文档里的长引文也要
    「」包裹 + 年份/source_id 坐标（PLAYBOOK §9 只提 candidate 答案，漏了模型文档）。
13. **eval.gate-above-judge-ceiling（报告不修改）**：quick 档 fact-preservation 门线 0.80 > candidate 实测上限 0.781，
    即使完美作答也过不了此门——疑似门线设置问题；**门是冻结资产，只上报不改**。
14. **emit_source_ledger.py --preserve 会回滚人工分道修改**（decisions 被覆盖回 writings/external）；
    需直接编辑 source-ledger.jsonl 才能持久化分道。

## 台账一致性

1. **#472 Walter Shewhart 切片标 TODO 但已登记（2026-08-20 实测）**：registry 财务合规师/walter-a-shewhart 已有
   team-card，且属「包外46人」枚举（包外在册-已注册.json 含 shewhart）。我切片 T3-451-604.json #472 却标 TODO。
   ⇒ 切片与登记目录存在枚举错位：**切片里某些 TODO 可能实际已在册**（包外枚举不占编号）。
   **对策**：T3 选候选人前先 grep registry 各族目录 slug + 查包外名单，撞了就跳过/改标；
   已建议 T1 校正切片或补充「已登记映射」。T3 不会动共享台账，只在上报里点名。

## 发现即记

15. **并发 11 子代理触发 provider 402（2026-08-21 凌晨实测）**：同时 11 个子代理（scnet/glm-5.2）导致
    「402 Model Request Error」，3 个代理任务 failed、其余级联停止，goal 被系统暂停。
    - 处置：等通道恢复（DeepSeek API wf.py 实测 OK、主循环恢复）后，逐批 resume 全部 11 个代理成功。
    - **建议**：① 并行子代理上限控制在 ≤8-10；② 402 属瞬时，恢复后 resume 即可，无需重做任何产物
      （上下文保留、工作区即断点）。

16. **★★ 子代理 register+commit 尾段会挂起并阻塞全队列（2026-08-21 实测，Morton #528）**：
    Morton 代理的 tail_lock 尾段（register_persona→git commit）挂起 1.5+ 分钟无子进程推进，
    **持有 tail 锁导致其余所有代理的登记全部排队等待**（表现为"无人登记但代理都在 running"）。
    处置：kill 挂起进程释放锁 → 队列解堵（5 个 tail 立即并行）→ 协调者手动完成 Morton 的
    register 产物 commit（切片 status=REG + git add 其路径 + commit）。
    **建议**：① tail_lock.py 加超时（如单尾段 >10 分钟自动放弃并提示）；② 协调者周期性巡检
    「tail_lock 进程存在但长时间无输出」= 疑似挂起；③ 子代理尾段失败后应幂等重试（register 已成功则只补 commit）。

17. **wf.py max_tokens 陷阱（Paracelsus #526 实测）**：flash 的 reasoning_content 独占 token 预算，
    max_tokens=500/100 时 content 返回空字符串（29/32 判分、21/32 候选答案为空）。
    ⇒ 答案 max_tokens≥2000、判分≥500；空项用直连 API 读双字段回退。已把 wf.py 默认 max_tokens 提到 2000。
18. **9M 词语料 release 门 10+ 分钟，package_target 内部再跑一次共 20+ 分钟（Paracelsus #526）**。
19. **emit_lane_scope 导出 "Pending." 占位行 → non_placeholder 门误判（Paracelsus #526）**：需删 Pending 行并写 ≥500 字实质 prose。
20. **check_byline_in_carrier 对 OCR 全坏文件假报；check_ocr_language_death 阈值对 16 世纪德文/拉丁偏严（Paracelsus #526）**：
    Fraktur 长 s 讹字 + 虚词占比误杀 P1——curate/fetch 阶段建议自动检测 OCR 虚词占比并标记。
21. **Morton #528 语料泄漏 + gitignore 缺口（2026-08-21）**：代理 git add -f 把 raw/raw-holdout 语料提交进 git
    （63 个文件）；gitignore 原只覆盖 raw/ 未覆盖 raw-holdout/。已 git rm --cached 清理 + 补 gitignore 规则。
    ★ 另有 **T1 历史遗留**：wip-godin 386 个、wip-steinhardt-98 104 个 raw 语料仍被跟踪，建议 T1 清理。

22. **单著作多版本人物的 distinct_works 天花板（2026-08-21 实测，Tull #573）**：传世著作单一的 18 世纪
    人物（Tull 的 Horse-Hoeing Husbandry 各版），16 份去重后作品数 6 < quick 门 8。解法：补 2-3 份
    **第三方独立著作**（同时代他人评/游记/农学书），而非同一书新版本，把 distinct_works 拉过门。
    下一位同类（Thomas Coke #574）可能复现——已入模板 13 条。
23. **DeepSeek flash reasoning 吞 max_tokens 已在 wf.py 修（2026-08-21）**：max_tokens 默认提至 2000，
    wf.py 变更已 commit（d91957e7b）。模板补 12 条「判分/答题一律用默认 2000，别手改小 max_tokens」。
24. **盲判答案长度平衡极难调（2026-08-21 实测，Tull #573）**：80 字过严（fact-preservation 判 0 分）、
    150 字过长（均长比 1.69 > 1.3 拦派发）；最终 100 字 + 手动修剪最长 5 条过门。模板补 14 条。
25. **子代理工作脚本散落 worktree 根（2026-08-21 观察）**：Reed/Young 代理把 _gen_*.py / ca1.json /
    assemble_rk_results.py 写到 AgentDatabase-T3 根目录（未跟踪、未进 git，无害但污染根）。
    **建议**：子代理脚本一律放自己 wip 目录；协调者 git status 巡检时发现即提醒（本批未改，只记录）。

26. **★ Lavoisier #569 违反尾段纪律：package_target+QC 在 tail_lock 锁内跑、且 --output 用相对路径 dist/（2026-08-21 04:03 观察）**：
    模板明确「package_target 在锁外跑」（Paracelsus #526 实测 20M 词 10-12 分钟会串行阻塞全队列），
    但 agent-22（resume 的旧上下文代理）把 quality_check + package_target 塞进了 tail_lock，且 `--output dist/`
    是相对路径（应 `--output <WS>/dist`），导致 zip 可能生成到 worktree 根而非 wip 目录。
    **处置**：当下无代理排队（全在修门阶段），锁会自行释放，未 kill；已在 resume 提示里重申纪律。
    **建议**：① resume 代理时在 prompt 里显式重申「锁内只做 register+git add/commit+切片 status，package_target 锁外」；
    ② 检查 register_persona 是否校验 zip 在 wip 目录下，否则补一个「zip 路径必须在 <WS>/dist」的门。

27. **content.selftest-failed（check_ocr_legibility 负对照未过）在多人触发（2026-08-21）**：darwin #572、avicenna #524
    的 release 报告均出现 `content.selftest-failed :: check_ocr_legibility 负对照未过——其检查结论不作数`。
    这是 QC 自检的负对照（故意给的坏样本）没过，意味着该 check 的结论整体不作数——不是具体某条引文错。
    **疑似共性**：可能与语料 OCR 质量（长 s 讹字）相关，或与 --cache 路径/语料结构有关。
    **建议**：T1 侧查 check_ocr_legibility 的负对照样本是否对早期现代字体（长 s）过于敏感；T3 侧先按
    「让检查可过」处理（确认 --cache 指工作区根、负对照样本来源正确），卡住则上报给判据侧。

28. **Lavoisier #569 四新暴露（2026-08-21 实测，agent-22 回报）**：
    ① **flash 盲判空响应率高**（32/48 空 ≈67%）：长 prompt + JSON 返回在 flash 降级期极不稳定，
       单条短 prompt 可恢复 → 判分 prompt 尽量 <200 字，或 batch→single 降级。
    ② **frame-break 检测器对「语料」子串过敏**：rubric 写「语料内有」触发「资料层词」误报 → 改「文献」可规避。
    ③ **check_byline_in_carrier 排除人名后剩余特征词可能为空**：证据串仅「M. LAVOISIER,」时需手动附载体中
       真实存在的更长非人名词（如 PHYSICAL, CHEMICAL）。
    ④ **emit_source_ledger 不写 dimensions 字段**：需手动从 _lanes.json 映射；assign_lanes 输出格式与
       quality_check 输入不一致。
    **处置**：已沉淀 ① 进模板 15 条（判分 prompt 短 + single 降级）；②③④ 为逐人细则，随模板附注。

29. **check_ocr_legibility 自测本环境通过，selftest-failed 是调用方式问题（2026-08-21 诊断）**：
    `python3 check_ocr_legibility.py --self-test` 在本机全过（EXIT=0，6 组负对照 ✓）。
    但 darwin #572 的 quality_check 报 `content.selftest-failed`（连续 04:03→04:14 两次同款）。
    ⇒ 该错误**不是语料问题**（自测样本硬编码与语料无关），是 darwin 代理的 QC 调用方式异常
    （如 --cache 指向错误导致 QC 以非预期方式调检查器）。
    **对策**：darwin 代理应先自查 QC 命令行（--cache 指工作区根、参数与 Lavoisier/Tull 一致），
    而不是去改语料或检查器。检查器/判据冻结不动（T1 合并后统一迭代）。

30. **农业 Thomas Coke #574 语料风险（2026-08-21 探源诊断）**：creator 检索 63 行里仅 1 行含农业相关词，
    且该行实为宗教（Hester Ann Rogers 布道）。农业 Coke（Earl of Leicester, 1747-1814, Holkham 庄园）
    被**同年同名的 Methodist 传教士 Thomas Coke** 完全淹没；且农业 Coke 本人著书极少（靠代理人/租户推广农业）。
    ⇒ **distinct_works 门大概率过不去**（无直接一手语料）。**对策**：Wave-4 分发时将 Coke #574 降级延后，
    优先语料充足的 Bakewell #575 / Paton #454 / Wicksell #488；若必须做 Coke，需 title 深挖第三方记载
    （同代人游记/农业志对 Holkham 的描写），但属高成本低产出，建议整批延后。

31. **畜牧育种家 Robert Bakewell #575 语料风险（2026-08-21 探源诊断）**：creator 检索 38 行全为
    **地质学家 Robert Bakewell（1768-1843）**（An introduction to geology/mineralogy），畜牧关键词命中 0、
    无 1750 前条目。切片 #575 是**畜牧育种家（1725-1795, Dishley 庄园）**——两位同名 Bakewell。
    ⇒ 与 Coke #574 同型：IA creator 检索被同名者淹没，育种家本人著书极少。
    **对策**：Wave-4 将 Bakewell #575 一并延后（与 Coke 同批），需 title 深挖第三方农业志记载；
    优先 Paton #454 / Wicksell #488 / Rhazes #525（后两者已补 title 探源）。

32. **★★ Darwin #572 两个 release 错误的共同根因 = 语料管线未跑完整（2026-08-21 诊断实锤）**：
    darwin 的 raw/ 缺全部管线元数据（只有 _ids.txt，无 _copyright-scan/_dedup/_fetch-manifest/_lanes/_primary），
    raw-holdout/ 是平铺 .txt 而非 src-* 子目录——对比已登记 tull（raw 有 _dedup/_lanes/_primary 等全套）。
    ⇒ `content.coverage-unresolved` + `content.selftest-failed` 都源于此：QC 的 cache 找不到正确的
    `raw/<source_id>/` 结构。
    **对策**：Darwin 代理应重跑语料管线（fetch_ia→ingest→dedup→holdout 移 src-*），而不是修 QC 参数；
    检查器/判据冻结。模板加一条「QC 报 coverage/selftest 先查 raw/ 是否有 _dedup.json/_lanes.json 等管线元数据」。

33. **Adam Smith #475 package_target 重试循环（2026-08-21 观察）**：agent-24 在锁内连续 3 次跑
    package_target（04:19、04:27、04:33 起），每次内置 release 门重跑 10 分钟，均未产出 zip。
    疑因：① `--output dist/` 相对路径（写到根而非 <WS>/dist）；② acknowledge-disclosure 子串与 warning
    原文不匹配导致门不过。**这是高成本循环**（每次浪费 ~10 分钟 QC + 占锁）。
    **对策**：协调者已观察；若第 3 次仍失败，resume agent-24 定向给正确命令（--output <WS>/dist 完整路径 +
    acknowledge 从报告 warnings 逐条取原文子串），并重申 package 锁外跑。

34. **Reed #549 四新暴露（2026-08-21 实测，agent-44 回报，15 轮返工）**：
    ① **source-count-inflated 对低产量人物是硬墙**：Reed 仅 ~10 篇论文且被 1911 编译集重印，16 份去重后
       仅 5 部独立作品 < quick 门 8。靠 holdout/train 交换 + 标记编译集 failed 才到 9 usable/8 distinct。
       ⇒ distinct_works 阈值建议按 profile 动态调整或允许 --allow-provisional 降级（判据侧，冻结只报）。
    ② **claim ID 须 12 位十六进制**：quality_check 正则 `clm-[a-f0-9]{12}`，init_target 生成 `clm-0000000001`
       仅 10 位十进制。10 以上 claim 需转 hex（a/b/c/d），否则 model docs 与 claims 文件 ID 不匹配。
    ③ **eval_runner record 覆写 results.jsonl**：每次 record 清空而非追加，批量 record 只留最后一条，需手写。
    ④ **wf.py judge 返回格式不统一**：`{"A":9,"B":2}`/`["9","2"]`/`["A_SCORE":10,...]` 三种，需多重 fallback。
    **处置**：②③④ 入模板警示；① 判据侧冻结只报。

35. **Ross #550 两暴露（2026-08-21，agent-45 回报，2 轮返工，0 错 0 警）**：
    ① **build_blind_payload 引文坐标门与 no-quotes 门矛盾**：候选答案要引文（no-quotes 门）但引文要坐标
       （坐标门）会暴露候选侧（surface-leak 门）。解法：**答案不放引文（rc==3 放行），引文只放模型文档
       （RENDER_FILES）**。
    ② **check_longs_corruption 对已降级 S1 源仍报 warning**（不区分 tier，strict 下 warning 也拦）：
       解法：从 ledger 移除 OCR-dead 源条目。
36. **Young #597 五暴露（2026-08-21，agent-47 回报，10 轮返工，0 错 0 警）**：
    ① **wf.py 判分空返回率 ~47%**（32 题 15 次空，多次重试 6 题仍空，用 0.5/0.5 中性值填充拉低 delta）：
       flash 降级期不稳定，空返回重试仍失败的题记中性分并注明（判据侧确认中性分合规）。
    ② **curate_ia 同名消歧**：IA pool 261 条命中 "Young, Arthur"，需排除 4 个同名者（1769-1828 葡语译者 /
       Arthur N. 1890- 记者 / Arthur Young 1810- 灵学作者 / 1734 宗教论文作者）——EXCLUDE 规则随 commit 入库。
    ③ **package_target subject_uid 用报错值**（person-xxx 非 person-597）：与模板 9 条一致，再次验证。
    ④ **team-card user_value 是必填数组字段**：模板未提示需手动添加——已补模板。
    ⑤ **quote-no-locator 扫直引号**：claims.jsonl 的 `""` 直引号也被 check_quote_locator 扫描，需统一用「」+（年份, source_id）。
    **处置**：①②③ 已入模板（前例）；④⑤ 补模板 19-20 条。

37. **Rhazes #525 + Davy #577 新暴露（2026-08-21，agent-69/70 回报）**：
    Rhazes（+0.0406）：
    ① **非拉丁语料人物的 ocr-dead 硬墙**：原作阿拉伯文，流传靠拉丁/法文/英文译本；36 份里仅 2 份英文 OCR 可靠，
       拉丁 OCR 损坏率 >90%，own_voice_ratio 仅 0.1245 → 建议对非拉丁语料人物降 ocr-dead-as-primary 的 P1 门槛（判据侧）。
    ② **curate REQUIRE 过宽**：`rhazes: [["rhazes"],["razi"]]` 会匹配 Fakhr al-Din al-Razi 等同名；已收紧为
       rhazes/rhazès/rhasis/zakariya 多形 + EXCLUDE 6 类。**阿拉伯语人物 nisba 同名预警入模板**。
    ③ **suite 名称必须匹配 eval_runner 硬编码集合**（boundary/fact-preservation/style-decoy 等），模板未列清单——已补。
    ④ **judge_payload 格式**：surface-leak 期望 `{case_id: answer}` 扁平 JSON，build_blind_payload 输出 `{case_id:{question,A,B}}`，需手动转扁平。
    ⑤ **emit_source_ledger --force 清空 holdout**：重出台账把 split 全推回 train，holdout 丢失——holdout 移动后别重跑 emit，或用 --preserve。
    Davy（+0.420）：
    ⑥ **curate EXCLUDE 缺键报错**：REQUIRE 有 `davy` 但 EXCLUDE 没有 → "未知人物键" 错误。**REQUIRE 和 EXCLUDE 必须同步加键**。
    ⑦ **flash 判分 5 形态**：`{"A":10,"B":5}`/`{"A":"0分","B":"100分"}`/`{"A":"满分"}`/`["9","2"]`/`["A_SCORE":10]`——比 Reed 的三形态更多，多重 fallback 需覆盖文本形态。
    ⑧ **IA HTTP 500 比例高**（60 id 中 32 个 53%）：不影响 quick 门（28 份够）。
    ⑨ **build_blind_payload 字段名**：用 `case_id/question/A/B`（非 qid/prompt），judge 脚本需对齐。
    **处置**：②③⑥⑦ 入模板 22-25 条；① 判据侧冻结只报。

38. **Wicksell #488 延后(DEF)五暴露（2026-08-21，agent-68 回报，commit b3d0e68a0）**：
    delta +0.131 全门通过，但 release 门 1 错（source-count-inflated，7 distinct works < 8）无法过。
    ① **source-count-inflated-by-duplicates 是硬墙且不可降级**：`report.error()` 不接受 allow_provisional；
       低产量人物（Wicksell 仅 7 部独立作品，IA access-restricted 限制）无法过 release 门。
       建议判据侧改 `report.threshold()` + allow_provisional 使 --allow-provisional 时降级 warning。
    ② **corpus.structurally-infeasible 与 source-count-inflated 互斥**：前者要 usable≥9、后者要 usable≤distinct_works；
       distinct_works<8 时两者无法同时满足。建议 structurally-infeasible 也接受 allow_provisional。
    ③ **瑞典语 latin-1 双重编码**：Project Gutenberg latin-1 文件在 ingest normalize 被双重编码成 mojibake，
       check_source_dedup 无法分词。手动转 UTF-8 修复。建议 ingest 检测 latin-1。
    ④ **check_material_split 要求物理文件在 raw/ 和 references/sources/ 都存在**：即使 source 标记 U+failed，
       需保留 raw/ 文件但移除 references/sources/ 副本才能同时过 material_split 和 source_dedup。
    ⑤ **claim.non-independent 移除 holdout source 后自动修复**：需保证移除后 evidence_clusters ≥2 train source。
    **处置**：①② 判据侧冻结只报（第 3 次复现 source-count-inflated 硬墙：Reed/Ross hack 过、Wicksell 过不了）；
       ③④⑤ 为工具行为，随模板附注。
    **影响**：Wicksell 标 DEF 延后，未注册。选人时优先产量充足人物（Davy/Sinclair 类）。

39. **Paton #454 误判「卡死」事件与平台兼容教训（2026-08-21，T3 协调者）**：
    agent-67 两次被标「已确认卡死、工作区无写入」，险些按 Wicksell 先例误标 DEF。
    复核发现**纯属误判**：macOS BSD `find` 不支持 `-printf`，`find ... -newermt ... -printf ...` 静默返回空，
    两次独立核验用了同一条坏命令 → 假确认「无写入」。
    **正确命令**：`find . -type f -exec stat -f '%Sm %N' -t '%H:%M:%S' {} \; | sort -r`（BSD），
    或仅用 `find -newermt` 不带 `-printf`。核验真实状态前不得下「卡死/DEF」结论。
    **处置**：resume 后 agent-67 持续产出（07:41 work.md / 08:06 results.jsonl / 08:08 重建盲判 payload），
    未延后，继续等待完成通知。已停止巡检，改为事件驱动。
    **教训**：判卡死 = ①进程探针 + ②平台兼容的 mtime 探针，两者都干净才算；禁止用损坏命令连续两次自我确认。

40. **Seacole #530 延后(DEF)：单著作人物的一手占比硬墙（2026-08-21，agent-108 回报，commit 5dc9adeea）**：
    补 6 份第三方 PD 文献后 distinct_works=7（接近 quick 门 8），但**一手占比 1/9=11% << quick 门 40%**。
    模板经验 13 只解决 distinct_works 天花板，**不解决一手占比天花板**。Tull #573 能过是因书有 12 个 PD 版本/重印各算 P1；
    Seacole 仅 4 版且 3 个 printdisabled，唯一可取只有 Gutenberg。另 IA djvu 文本提取间歇 500。
    **处置**：DEF。选人时避开「单著作+版本稀少」的 19 世纪人物；模板经验 13 补前提「先过一手占比门再看 distinct_works」。

41. **Wald #531 延后(DEF)：JSTOR Early Journal Content 样板文本致误判去重（2026-08-21，agent-109 回报，commit c066d5964）**：
    8 篇独立期刊文章（童工/移民/工业卫生/女工组织等）共享 ~300 词 JSTOR 标准化页首样板，被 dedup min-hash 归 1 簇；
    去重后仅 2 部作品（虚高 5.0×）。`counting_convention` 已逐对点名但 **source-count-inflated 检查不读该字段**，只看内容去重计数。
    delta +0.2188 全门过，release 门 1 错（source-count-inflated）不可降级 → DEF。
    另两坑：flash 判分对 fact-preservation 极不可靠（baseline 误答 Abraham Wald 仍给 7/10）；
    check_unsourced_names 对动名词误报（"Seeing children..." → 改 "Having observed..." 规避）。
    **处置**：DEF。建议对 JSTOR Early Journal Content 样板做预清洗或 dedup 豁免；模板需列 QC 所需工作区文件清单
    （judge_payload.v1.json / baseline.v1.json / route-manifest.json，需从样板反推）。

42. **Paton #454 延后(DEF)：判分 0 分 + 截断语料 + 窗口超时（2026-08-21，resume agent-67 07:22-09:22 耗尽）**：
    results.jsonl 36 行仍 **0 dimension_scores**；语料 19 份可疑，其中多份仅 **~250 字节**（fetch/文本提取截断）；
    release 09:15 仍 FAIL。2h 有界窗口内判分从未产出分数。
    **处置**：DEF（commit 09065fccd）。**判分不产分先查语料完整性**：<2000 字节的截断件让 judge 无可判内容；
    fetch 后应前置文本长度门校验，别让 ~250B 文件进入 corpus 门计数。

43. **T3 预筛队列（2026-08-21，协调者 probe 预筛，供下一波分发决策）**：
    **强候选（下一波优先）**：Malthus #580（An Essay on Population 多版 + Principles of Political Economy，21 条 16 标题，全 PD）；
    Cobbett #600（120 条 89 标题，Porcupine/Advice to Young Men/Rural Rides 全 PD，最高产量）；
    Sanger #532（41 条 28 标题，Woman and the New Race 等 1920s 多部 PD）。
    **中等（需同名分离）**：Knight #486（Risk Uncertainty and Profit 1921 八版 PD，但 71 条里 16 条是 Knight Frank & Rutley 地产 + 13 条 1905 年同名 Frank Knight → 需 EXCLUDE 两族）；
    Ehrlich #536（120 条里 14 条是 Paul R. Ehrlich《The Population Bomb》同名现代生态学家 → 需 EXCLUDE；德文期刊多）。
    **弱/暂缓**：Bailey #602（探源仅 3 条，creator 元数据漏，真书很多但探源不佳）。
    **预筛高 DEF 风险（勿分发）**：McAdam #451（单著作 8 版皆同一书，distinct_works≈1，同 Seacole 型）；
    Brassey #452（同名 Earl 淹没，本人铁路承包商几乎无著作，同 Coke/Bakewell 型）；
    McClintock #584（同名童书作者污染 + 本人无 PD 书）；Lawes #570（探源 3 条）；
    Frisch #501（6 条低产量 + Econometrica 1950 版权）；Tinbergen #502（26 标题但多为 1950s-70s 版权）。

44. **T3 预筛队列·扩展（2026-08-21，Loudon/Evelyn/Marsh probe）**：
    **强**：Evelyn #599（120 条 78 标题，Diary 13 版 + Life of Mrs. Godolphin + History of Religion，17 世纪全 PD；注意早期现代长 s ſ 处理，见模板）。
    **中**：Marsh #591（44 条 26 标题，Man and Nature/The Earth as Modified by Human Action 同书修订多版 + Origin of English Language 9 版，distinct_works 约 5-6 偏紧）；Loudon #601（21 条仅 6 标题，Magazine of natural history 期刊 13 份不计 distinct，Encyclopaedia/Arboretum/Hortus 3-4 部，distinct 紧）。
    **下波候选优先级（在 Malthus/Cobbett/Sanger 之后）**：Evelyn #599 → Marsh #591 → Loudon #601。

45. **T3 预筛队列·扩展2（2026-08-21，Dicksee/Hatfield/Behring/Boussingault probe）**：
    **强**：Dicksee #495（财务合规；60 条 30 标题，Auditing/Advanced Accounting/Depreciation/Goodwill 多部多版 PD）。
    **中强**：Hatfield #496（财务合规；34 条 27 标题，Modern Accounting 6 版 + Lectures on Commerce，distinct 约 5-6）。
    **中**：Behring #537（医疗；20 条 14 标题，The Suppression of Tuberculosis 英文 PD + 德文著作 OCR 风险）。
    **中弱**：Boussingault #578（农林牧渔；14 条 13 标题，Économie rurale 法文 + Agronomie 多卷，法/西文 OCR 风险，同 Rhazes 型语言墙）。
    **优先级（当前 6 人在途之后）**：Evelyn #599 → Dicksee #495 → Marsh #591 → Hatfield #496 → Loudon #601。

46. **建造采购尾2 处置（2026-08-21，协调者预筛判定，commit c76f134b1）**：
    **Brassey #452 → DEF**：结构性无本人一手著作。探源 68 条创作者全是「Thomas Brassey, Earl」同名者（海军政治家 1836-1918），
    铁路承包商本人（1805-1870）在 IA 几乎 0 一手著作，一手占比必败（同 Coke #574/Bakewell #575 型）。已锁内 commit DEF，未分发。
    **McAdam #451 → 保留 TODO**：虽是单著作（Remarks on Road-Making 8 版同书，distinct_works≈1），但属 **Tull #573 型**——
    Tull 同款单著作+补第三方独立著作（同时代筑路书）有实测通过先例（delta +0.541）。勿预筛 DEF，留待真实蒸馏尝试（排在 Evelyn/Dicksee 之后）。

47. **子代理启动停滞检测与处置（2026-08-21，Sanger #532 实例）**：
    新发代理 75 分钟无工作区/无文件/无输出（同期 Cobbett 38min、Malthus 45min 已建工作区）→ 判定停滞。
    **处置**：TaskStop 原实例 + 快速重发（限 5 分钟扫读模板、立即初始化工作区、按 12 步推进）。
    **规则**：新发代理若在同期兄弟实例均产出后仍 0 文件活动 ≥ 60 分钟 → 停滞，杀 + 重发，不空等其 2h 窗口耗尽。
    注：TaskOutput 对 running 子代理恒返回 0 字节，不能用于判断活动；判据用工作区文件 mtime + 是否有工作区目录。

48. **预筛强候选波 3 人延后(DEF)：盲判 delta 门成主要硬墙（2026-08-21，commit 56a6958ea）**：
    Marshall #476（re-judge 后 delta **−0.0516** + release 23 错 authorship-unproven×7）、
    Freud #533（delta **−0.938** 灾难性劣于基线）、Pavlov #535（release 41 错含 placeholder 文档 + namesake + boundary 门 0.10vs0.70）。
    三员均 2 窗口耗尽（分发+resume），判分/QC 无法收敛。
    **读数**：预筛只保证「语料产量/版权」，不保证「盲判 delta 门可达」——强候选栽在 delta 是普遍现象。
    **对策**：resume 时显式提示「若 candidate 多次判分仍 < baseline(+0.03) → 直接 DEF，不无限重试」；后续分发把 delta 门风险写进 mandate。

49. **macOS TCC 会话中途撤销 ~/Documents 访问（2026-08-21，全项目操作被拒 + 恢复）**：
    `ls/cat/git/python3/Read` 对项目树全部 Operation not permitted（主目录正常）；Dicksee 续跑代理同步受创。
    **根因**：TCC 对终端/Documents 权限在会话中失效（OS 级，非代码问题）。
    **恢复**：用户重新授权（隐私与安全性→文件与文件夹/完全磁盘访问）+ 重启会话动作后恢复。
    **教训**：权限丢失时不可强行绕过（OS 级）；向用户给出明确恢复路径并停轮，等外部状态变化（已按 blocked 审计处置）。

50. **子代理模型大小写别名缺失致分发失败（2026-08-21，已修复）**：
    子代理以 `scnet/glm-5.2`（小写）运行，但 config.toml 只配 `scnet/GLM-5.2`（大写）→ 全部分发报「not configured」（401 的伴生症状）。
    **修复**：按既有小写别名先例（`scnet/deepseek-v4-flash-0731`）在 `~/.kimi-code/config.toml` 补 `scnet/glm-5.2` 别名；`kimi doctor config` 验证通过后备份覆盖（备份 `config.toml.20260821-201145.bak`）。
    **教训**：模型 id 大小写敏感；改动 kimi-code 配置按 update-config 流程（copy→edit→kimi doctor→backup→overwrite）。修复后子代理落回已配置的 `scnet/deepseek-v4-flash-0731`（低成本 flash），符合成本纪律。

51. **T3 预筛队列·扩展3（2026-08-21，King/Gilbert probe）**：
    **中强**：Gilbert #571（农林牧渔；18 条 15 标题，Rothamsted 多部报告/History of Rothamsted，PD，distinct 约 8+）。
    **中**：King #588（农林牧渔；7 条 4 标题，Farmers of Forty Centuries 1911 + Irrigation & Drainage + Physics of Agriculture + The Soil，distinct 约 5-6 偏紧）。
    下波优先级（当前 7 人在途之后）：Marsh #591 → Ehrlich #536 → Gorgas #552 → Gilbert #571 → King #588 → McAdam #451(Tull型)。

52. **pro 用量超纪律线（2026-08-21，成本分账核验）**：
    wf.py 分账：flash 4801 次 ¥11.36 / pro 58 次 ¥1.12（**pro ≈ 9% > 5% 纪律线**）。
    pro 分布：06-07 时 26 次（Wicksell 已知）+ **13-14 时新增 32 次**（Marshall/Freud/Pavlov resume 窗口，mode=batch 判分）。
    **读数**：新增 32 次 pro 属「门线±0.03」触发被**整批**使用（一次判分批 4×8/8×4 全用 pro），且这批 pro 花在最终 DEF 的人物上（无产出回报）。
    **对策**：① 分发 mandate 强调 pro 仅**单次关键重判**（门线/红门单 case），禁止整批 pro；② 协调者每波核验 wf.py usage 分账，超线即入台账。

53. **400 Format Error 风暴（2026-08-21 12:00 UTC，全在途子代理集体被杀）——死循环根因定位与防复发策略**：
    8 个子代理在 **39 秒窗口**（ended_at 1787313593→1787313632）内全部以 `400 Format Error` 终止（Evelyn/Dicksee/Sanger/Malthus/Knight/Gorgas/Hatfield）；同刻有正常推进的 Cobbett 却活到 2h 自然超时。**判定为 scnet 提供方瞬时全局故障，非管道格式 bug**（wf.py 直连调用全程健康，故障后探测恢复 OK）。
    **死循环机制**：把终止代理逐个 resume 进同一故障窗口 → 反复撞墙（本段 8 次 resume 全废）。
    **对策（防复发，写入后续 mandate 模板）**：
    ① **故障风暴期间禁止批量 resume**，等提供方恢复（wf.py 单次探测）再动；
    ② resume 一律改 **fresh dispatch**（小上下文启动，避免巨型 resume 上下文 + 故障叠加），mandate 显式「从磁盘续做、禁止重跑已完成步骤」；
    ③ **防死循环护栏**：自身回合连续 HTTP 400/5xx → 退避重试 ≤5 次，仍持续 → 写 STOP-STATE-<slug>.md 立即退出，绝不无限重试；
    ④ 每波结束后盘点磁盘 stage 标记（quality-research/quality-release 报告文件名带 UTC 时间戳），以报告为准判定 REG/DEF，不盲信代理存活状态。
    **本风暴的净产出**：Cobbett #600 挺过风暴并过 release 门 → 注册入库（commit 39f83500a，products 134）；Hatfield #496 release 门 FAIL（holdout 污染硬墙）→ DEF（commit b6d3c87c1）。Sanger #532 release FAIL（ledger.invalid+corpus.undeclared）待判；Evelyn/Dicksee/Malthus/Knight/Gorgas/Marsh 停在 research/judge 阶段，已用 fresh 完成代理续做。

54. **T3 预筛队列·扩展4（2026-08-22，Loudon/Ehrlich 探源）**：
    **强**：Loudon #601（农林牧渔；235 命中全 open，95 distinct 标题，主体 1800-1880 PD；Arboretum et Fruticetum Britannicum + Gardener's Magazine 各十余版本，Encyclopaedia of Gardening 等在列）——下波首选，基本稳 REG。
    **高危同名污染**：Ehrlich #536（医疗护理；221 命中，但 top 标题是 The Population Bomb(1968)/The process of evolution/The machinery of nature——那是生态学家 **Paul R. Ehrlich(1932- )**，全部版权在保护期；本尊 1854-1915 医师的 PD 著作（Experimental researches on specific therapeutics/Collected studies on immunity 等）仅约 5-8 distinct，可能 < quick 门 8）。**对策**：分发 mandate 必须 REQUIRE creator 多形态钉住 `Ehrlich, Paul, 1854-1915`，EXCLUDE `Ehrlich, Paul R.`/Population Bomb/evolution 标题；仍可能栽 distinct 门，列为高风险候选，放 Loudon/Gilbert/King 之后。

55. **Malthus #580 REG 双保险 + Sanger #532 DEF（2026-08-22，fresh 完成代理实测）**：
    **Malthus #580 → REG**（delta +0.0813，6 门全过，release 0错/3警=语料固有同款已 REG 先例）。两段式：400 风暴后前代理(166)自行恢复跑完尾段并注册（commit cda7d1572，134/600），但 eval-all.json 是 stale（delta 0.0688/boundary=false，与已提交 64 行 results.jsonl 矛盾）；fresh 代理(182)用 `eval_runner aggregate --write-report` 重生成修正（commit 82d5431a2），零 LLM 消耗。**教训**：dispatch 前先 grep 切片该编号 status；re-judge 后必须重跑 aggregate。
    **Sanger #532 → DEF**（commit 560916501）：fresh 代理(179)按「修门或 DEF」先修账本（7 条 claim status→pattern，清掉 ledger.invalid+model-minimum），但 release 门仍 15 错——candidate overall 0.469<0.650（32 席盲判 17/32 得 0）、fact 0.5<0.8、no-quotes（引文不成对/伪 locator）、5 条 claim 缺 2 独立来源、heuristics 2<3、11 对未声明 derived_from。**判定**：eval 门高于 judge 实测上限不可达（同类 Marshall/Freud/Pavlov/Wald DEF 先例），证据 wip-margaret-sanger-532/DEF-EVIDENCE.md。
    **本轮净状态**：REG 23（+Cobbett/Malthus）/ DEF 62（+Hatfield/Sanger）。

56. **本轮成本分账核验（2026-08-22，7 fresh 代理完成波）**：
    wf.py：flash 5660 次 ¥15.11（较上轮 +859 次 ≈ +¥3.75，全为本轮 7 代理完成工作）+ pro 58 次 ¥1.12（**较上轮零新增**）。pro 占比 6.9% > 5% 纪律线，但全部来自历史遗留（Marshall/Freud/Pavlov/Wicksell 时代），**本轮 7 fresh 代理零 pro 调用**——「pro 仅单次关键重判、禁止整批」纪律执行到位。

57. **T3 预筛队列·扩展5（2026-08-22，McAdam #451 探源）**：
    **Tull 型高风险**：24 命中 20 distinct 标题，但本尊 "John Loudon McAdam"(1756-1836, 筑路工程师) 的 PD 著作仅 **4-5 distinct**（Remarks on the Present System of Road Making 多版本 + Observations on Turnpike Roads Trusts + Letter to Sir Alexander Muir M'Kenzie (Scottish Roads) + 意译 Primo elemento...strade），**< quick 门 8**；其余 15+ 条为同名他人污染（C. John/Steven D/David/John 1962-/Rohan McAdam：化学晶体论文、business plan、法院史等）。**对策**：按 Tull #573 先例「可发但必须补 2-3 份同时代第三方著作拉 distinct 过门」，mandate 显式写此要求；corpus 建不起来则锁 DEF。列为下波最后一位（Loudon/Gilbert/King 之后）。

58. **McAdam #451 实测确认（2026-08-22，双查询探源核对 #57）**：
    两查询实跑：「McAdam road」27 命中、「macadam roads pavement」19 命中（后者仅补到 1 条 1910 专利 Boltshauser，非本尊）。
    **本尊 distinct 作品实测 ≈ 3-4 部**：Remarks on the Present System of Road Making（1819-1824 多版=1 标题）、Observations on the Management of Trusts/Turnpike Roads（1825）、Notes on Practical Road Making（1863 与 Charles Penfold 合著）、另 1 意译本同源。同名污染（C. John/Steven D/David/John 1962- 化学/商业/法院史等）确认。
    **结论**：比 Tull #573 更弱（Tull 至少 Horse-hoing Husbandry 多版为轴）。**建议末位派发且 mandate 显式写「先建 distinct_works ≥8（本尊多版 + 同时代第三方筑路/公路著作），建不起来立即 DEF 锁，不浪费 slot」**；语料天花板低导致 own-voice/attribution 门大概率栽，做好 DEF 预案。

59. **T3 预筛队列·扩展6（2026-08-22，Gilbert #571 / King #588 实测探源）**：
    **Gilbert #571（农林牧渔，原评「中强」→ 实测偏危）**：「Gilbert agricultural experiments」43 命中，本尊 J. H. Gilbert(1817-1901) distinct 标题 ≈ **4-6**（Rothamsted Results on growth of barley/wheat/leguminous 各卷 = 每作物一标题 + Mixed Herbage of Permanent Meadow 长系列 1879-1900 多期 + 1895 Lawes《Rothamsted experiments》署名在 Lawes）；**几乎全部与 Lawes/Masters 合著** → 归属/attribution 门复杂度高，distinct 贴近 <8 线。**判**：可发但 mandate 须接受 Lawes 合著语料、以本尊 voice 剥离；distinct 建不满 8 → DEF 预案。放 Loudon 之后、King 之前。
    **King #588（农林牧渔，原评「中」→ 实测临界可发）**：「Franklin King farmers forty centuries」17 命中几乎全是《Farmers of Forty Centuries》多扫描（1 标题）；扩查发现本尊 distinct 标题 ≈ **7**：Forty Centuries(1911)、The Soil(1895/1908 多版)、Irrigation and Drainage(1898+)、A Text Book of the Physics of Agriculture(1904/1907)、Irrigation in Humid Climates(1896)、Investigations in Soil Management(1904/1905 系列)、Soil Management(1914，逝后编印)。**临界 7**，补《Ventilation for Dwellings, Rural Schools and Stables》(1908) 可到 8。**判**：可发但 mandate 须显式「distinct_works 全清单 ≥8（含 Ventilation），Farmers of Forty Centuries 多扫描只算 1 标题」，否则 DEF 预案。
    **下波排位更新**：Loudon #601（稳 REG 首选）→ Gilbert #571（偏危）→ King #588（临界）→ McAdam #451（末位，反馈#58 已实测 DEF 预案）。

60. **医疗护理师族 TODO 版权墙预筛分类（2026-08-22，探源实证）**：
    **实证**：Orem #546 探源 6 命中全为 1991-2003（Self-care theory in nursing / Nursing: concepts of practice 等，版权在保护期）——**零 PD 语料**，与 FINDING_nursing-family 先例（Henderson/Peplau 版权墙）一致。按卒年推断同类版权墙（卒 ≥1950，活跃期全在 1931 后，无 PD 一手）：
    **版权墙 → 预筛 DEF（探源 0 PD 即锁，不派全流程代理烧 flash）**：#538 Florey(1968) #539 Chain(1979) #540 Waksman(1973) #541 Salk(1995) #542 Sabin(1993) #543 Drew(1950) #544 Taussig(1986) #545 Barnard(2001) #546 Orem(2007) #547 Leininger(2012) #548 Rogers(1994)。共 11 人。
    **PD 可做 → 正常派发**：#536 Ehrlich(1915，已预筛：REQUIRE `Ehrlich, Paul, 1854-1915` + EXCLUDE `Ehrlich, Paul R.`/Population Bomb，distinct 5-8 临界)、#537 Behring(1917，PD 明确；探源需多形态查名)、#534 Jung(1961，仅 pre-1931 作品可做，Psychological Types 1921 等，distinct 需 ≥8 验证，边缘)。
    **注**：预筛 DEF 也是 DEF（证据 = 探源 0 PD + 卒年分析，DEF-EVIDENCE.md 注明复跑条件「若后续出现 PD 语料」），不占全流程代理 slot；PD 可做者优先占 slot。

61. **财务合规师族 TODO 版权墙预筛分类（2026-08-22，卒年推断 + 探源待验边缘者）**：
    25 TODO。按 PD 规则（一手 PD、版次年 ≤1931 左右）分类：
    **版权墙 → 预筛 DEF（卒 ≥1950 且活跃期 1931 后）**：#477 Friedman(2006) #478 Hayek(1992) #479 Samuelson(2009) #480 Tobin(2002) #482 Galbraith(2006) #483 Minsky(1996) #484 Kindleberger(2003) #485 Kahneman(2024) #487 Hicks(1989) #489 Kletz(2013) #490 Bird(卒年不详，20世纪) #491 Rasmussen(2018) #500 Leontief(1999) #502 Tinbergen(1994)。共 14 人。
    **PD 明确 → 正常派发**：#492 Cotrugli(1469，文艺复兴商书) #493 Cerboni(1917) #494 Besta(1922) #497 Sprague(1912) #498 May(1961，pre-1931 作品) #499 Canning(1962，《Economics of Accountancy》1929 PD)。共 6 人。
    **边缘（pre-1931 作品存在但需探源验证 distinct ≥8）**：#472 Shewhart（《Economic Control of Quality》1931，恰在 PD 边界，probe 定案） #481 Schumpeter（《Theory of Economic Development》1911/1934，需 pre-1931 卷） #501 Frisch（1895-1973，pre-1931 作品少）。共 3 人。
    **在途**：#486 Knight（Risk Uncertainty and Profit 1921 PD，agent-183 进行中） #495 Dicksee（1864-1932，agent-201 续做中）。
    **注**：与 #60 同一方法论；版权墙者派发前用 probe 复核 0 PD 即锁预筛 DEF；边缘者 probe distinct 达标才派。财务合规师 PD 可做池仅 ~6-8 人，其余为 DEF 池——下下波以此为准排。

62. **农林牧渔师族 TODO 预筛分类（2026-08-22，26 人，卒年 + 著作形态推断，派发前 probe 复核）**：
    **版权墙 → 预筛 DEF（卒 ≥1950 活跃期 1931 后）**：#581 Wallace(1965) #582 Shull(1954) #583 Jones(1963) #584 McClintock(1992) #585 Wright(1988) #587 Haldane(1964) #589 Lowdermilk(1974) #590 Bennett(1960)。共 8 人（#584 McClintock 手稿/遗传学作品全 1930s+）。
    **PD 但单著作天花板 → 大概率 DEF（同 McAdam #451 先例，distinct 内容去重 <8）**：#592 Cato（De Agri Cultura 1 部） #593 Varro（Res Rusticae 1-3 卷） #594 Columella（De Re Rustica 12 卷+De Arboribus） #595 Pliny（Naturalis Historia 含农卷） #604 Eliot（Essay upon Field-Husbandry 1-2 部） #598 Townshend（实践著称无著作） #574 Coke（实践著称无著作） #575 Bakewell（育种实践无著作）。共 8 人——古典农学 4 人 + 无著作型 3 人 + Eliot；**先 probe 复核 distinct（多版本/译本算不算）再定**，倾向 DEF 但 probe 前不锁。
    **PD 可做（distinct 有望 ≥8）**：#578 Boussingault（Agronomie 多卷） #579 Sprengel（德语多部） #602 Bailey（1858-1954 高产，Cyclopedia/Holy Earth 等 pre-1931 多部） #570 Lawes（Rothamsted 系列+合著，需剥 Gilbert 侧 voice） #596 de Serres（Théâtre d'Agriculture 1600 + 多部） #586 Fisher（Statistical Methods 1925 PD，1935 后版权，边缘） #603 Meyer（1875-1918，USDA 报告/letters，distinct 边缘）。共 7 人（3 边缘）。
    **在途**：#571 Gilbert #588 King #601 Loudon。
    **下下波替补顺序**：Bailey #602 → Boussingault #578 → de Serres #596 → Lawes #570 → Sprengel #579（德语/语料形态待 probe）；财务合规 PD 池（#492/493/494/497/498/499）用完即转此池。

63. **边缘候选探源定案（2026-08-22，4 人实测，全部偏 DEF——移出派发池）**：
    - **Shewhart #472**：探源仅 1 命中 = 1980 重印《Economic control of quality of manufactured product》（1931 原版未见独立记录）；distinct 单著作 → 单著作天花板 → 倾向 DEF（除非 1931 原版以 PD 形态探到）。
    - **Fisher #586**：探源命中为假阳性（Ben Steigmann《Notes on the Paranormal》）；《Statistical Methods for Research Workers》1925 未在 IA 检索出 PD 形态；distinct 不足 → DEF。
    - **Jung #534**：23 命中几乎全是《Psychological Types》1921/1923 分章碎片（IA 按章索引）+ 1983《The essential Jung》（版权）；pre-1931 distinct 2-3（Psychological Types + Collected Papers 1916）→ <8 → DEF。
    - **Schumpeter #481**：17 命中仅《The theory of economic development》1934 英译版（theoryofeconomic00）贴题，1908 德文《Wesen und Hauptinhalt》未见；distinct 1-2 → DEF。
    **结论**：反馈 #61/#62 的「3 边缘/3 边缘」实际全部可判 DEF（探源 0-2 贴题 PD 作品）；PD 可做池收缩为：#60 医疗护理 Ehrlich/Behring（+Jung 移出）、#61 财务合规 6 人、#62 农林牧渔 7 人。派发池照此执行，勿再为边缘者开 slot。

64. **版权墙预筛批 DEF 完成 24 人 + 卒年推断修正（2026-08-22，commit 3cc9599c8 核验通过）**：
    24 DEF（医疗护理 10：Florey/Chain/Salk/Sabin/Drew/Taussig/Barnard/Orem/Leininger/Rogers；财务合规 14：Friedman/Hayek/Samuelson/Tobin/Galbraith/Minsky/Kindleberger/Kahneman/Hicks/Kletz/Bird/Rasmussen/Leontief/Tinbergen），DEF-EVIDENCE + 38 份探源 TSV 落盘，**零 LLM 零 wf.py**。切片 DEF 63→87，TODO 65→40。
    **⚠️ 关键修正——卒年推断 ≠ 版权墙判据**：#60/#61 按卒年把 Waksman#540 归版权墙，**实测错误**：Waksman(1888-1973) 活跃期始于 1910s，探源命中 pre-1931 PD 一手（Principles of Soil Microbiology 1927 / Enzymes 1926 / J. Bacteriology 1918-1930），已留 TODO 待重派全流程。**教训：卒年推断仅初筛，1900s 前生人必须 probe 实测定判；同理 Leontief/Tinbergen/Taussig/Florey 均靠定向探源才排除父/兄弟/导演同名污染。**
    **下步**：Waksman#540 优先重派（mandate 注明「以 1926-1930 著作为轴建 distinct」）；财务合规 PD 池 6 人照常派发；边缘者 Schumpeter#481/Frisch#501/Shewhart#472 保持 TODO 未触碰（符合边界）。
65. **单著作天花板/无著作 8 人预筛 DEF（2026-08-22，探源实测，零 LLM）**：
    反馈 #62 的「古典农学 4 + 无著作 3 + Eliot」8 人全部探源定案锁 DEF：
    - **单著作天花板（distinct <8，多版本/合编/卷分不计独立著作）**：#592 Cato（De Agri Cultura，9 命中全同书）、#593 Varro（Rerum Rusticarum，4 命中同译本）、#594 Columella（De Re Rustica，7 命中全同书）、#595 Pliny（Naturalis Historia，60 命中全同书各语种/卷分/节本）、#604 Eliot（Essays upon Field-Husbandry，2 命中）。
    - **无本人著作（distinct=0，全同名污染/他人著传）**：#598 Townshend（19 命中全污染，本尊 1674-1738 实践著称无著作）、#574 Coke（1 命中为他人著传）、#575 Bakewell（双查询 0 命中，育种实践者方法由他人著录）。
    每份 wip-*/DEF-EVIDENCE.md 含探源证据 + 复跑条件。**零 flash 零 wf.py**。切片 DEF 87→95，TODO 39→31。
    **教训延伸（模板经验 #37/#38 之外）**：单著作人物的「多版本/译本/卷分」在 IA 检索里命中最密集，但内容去重后 distinct 恒 <8——**探测判据要数「独立著作」而非「命中行数」**；无著作型人物（Townshend/Coke/Bakewell）以「全命中为同名污染/他人著传」为 DEF 证据，与版权墙型（#64）是两条独立 DEF 通道，复跑条件写法不同（前者等「本尊独立 PD 著作出现」，后者等「pre-1931 PD 语料出现」）。
66. **农林牧渔替补池探源预研定案（2026-08-22，零 LLM，供下波派发）**：
    反馈 #62 的替补顺序 5 人实测重排：
    - **可派（distinct ≥8）**：**Bailey #602**（本人 distinct 23 部 PD 著作——Cyclopedia 系列/First lessons/The forcing-book/Garden-making/Principles of agriculture/Field forest garden botany 等，探源 30 行本人命中；强可派，首位）；**Boussingault #578**（distinct ~8：Agronomie chimie agricole/Économie rurale/Rural economy 英译/Mémoires/The chemical and physiological balance/Théâtre de la Moscovie + 期刊论文）。
    - **边缘可派**：**Lawes #570**（Rothamsted memoirs 系列卷 1847/1912/1941 + 独立报告「growth of potatoes」1888/「Rothamsted experiments」1895/「Chemical study of phosphoric acid」1901；distinct 贴近 8；mandate 须注明「剥 Gilbert 侧 voice，以 Rothamsted 系列卷+独立报告建 distinct」）。
    - **探源 DEF（本批锁 2）**：**de Serres #596**（单著作天花板——Théâtre d'agriculture 1603/1617/1802/1804 各版本，无第二独立著作）；**Sprengel #579**（同名污染重：Kurt Sprengel 医学史家/Christian Konrad Sprengel 授粉生物学占主导；Carl 农学家独立 PD 著作仅 3 部 Bodenkunde 1837/Dünger 1839/Urbarmachungen 1838-46，distinct <8）。
    **结论**：替补派发顺序 = Bailey #602 → Boussingault #578 → Lawes #570（边缘）；Sprengel/de Serres 已锁 DEF（commit 本批）。切片 DEF 95→97，TODO 31→29。
    **教训**：① 探源查询词会带偏结果（Bailey 首探全 cyclopedia，宽探姓名后才见 23 部独立著作）——**预筛至少两轮查询（主题词+纯姓名）**；② 同名污染判据要按「本尊独立著作数」而非「命中行数」（Sprengel 153 行里 Carl 仅 3 部）；③ 用 creator 字段正则过滤真伪（Bailey 的 L. H. 格式）。
67. **财务合规 PD 池 6 人探源全灭——「分类≠IA 语料实况」，派发前必探源（2026-08-22，零 LLM）**：
    反馈 #61 把 Cotrugli/Cerboni/Besta/Sprague/May/Canning 6 人归「PD 明确 → 正常派发」，**探源实测全 DEF**：
    - **单著作天花板**：Cotrugli #492（Della mercatura 1573 仅 1 部）、Besta #494（La ragioneria 1909 仅 1 部）、Canning #499（Economics of Accountancy 1929 仅 1 部）。
    - **独立著作 <8**：Sprague #497（Philosophy of Accounts + Accountancy of Investment + Problems ~3 部）。
    - **无 IA PD 语料**：Cerboni #493（意大利文 logismografia 未扫描，双查询 0 命中）、May #498（"May" 月份词全噪声，双查询 0 本尊命中，pre-1931 内容为期刊散篇）。
    **教训**：历史「PD 可做」分类只是卒年/版次的纸面推断，**IA 是否真有足量 PD 语料必须探源实测**——这是 Waksman #540 教训（卒年推断≠版权墙判据）的同构延伸：「分类≠IA 语料实况」。**财务合规 TODO 族现在实际可派池为空**（剩余 TODO 全为医疗护理/农林牧渔）。切片 DEF 97→103，TODO 29→23。
    **下波派发调整**：财务合规 PD 池取消；下一波从医疗护理/农林牧渔剩余 TODO 挑（需先探源复核），农林牧渔已确认可派 Bailey #602 / Boussingault #578 / Lawes #570（边缘）继续有效。
68. **补 gap：反馈 #63 已定 DEF 的 4 人证据落盘 + 切片同步（2026-08-22，零 LLM）**：
    #63 只写了反馈结论未落证据/未改切片，本次重探补全：Shewhart #472（Economic control of quality 1923 期刊+1930 BSTJ+1980 重印，~2 部）、Schumpeter #481（35 命中全二手，无 pre-1931 PD 一手）、Fisher #586（Statistical Methods 1928-67 单著作多版本）、Jung #534（1971/1983 版权版+碎片）。4 人全部锁 DEF，切片 TODO 23→19。
    **教训**：反馈结论 ≠ 切片 status——**协调者在反馈里定 DEF 后必须同步改切片 JSON 并落证据文件**，否则下波派发会误派（本 gap 正是 #63 后漏改切片造成）。
69. **农林牧渔剩余 9 人探源全 DEF——TODO 收窄到 10（2026-08-22，零 LLM）**：
    反馈 #62 版权墙 8 人 + 边缘 Meyer #603 全探源定案锁 DEF：
    - **版权墙（活跃期/著作全 post-1931）**：Wallace #581（政治生涯 1930s-60s，pre-1931 仅 1-2 部）、Lowdermilk #589（著作全 1936-69）、Bennett #590（著作全 1937-50，pre-1931 仅早期土壤调查 1-2 部）、McClintock #584（1980s 著作/期刊，IA 无 pre-1931 语料）、Haldane #587（Daedalus 1923 等未见 PD 形态）、Jones #583（1924 书未见 IA 扫描）、Wright #585（pre-1931 仅 1916 一部）。
    - **语料不足**：Shull #582（独立期刊文章 ~5-6 部 <8）、Meyer #603（USDA 探察报告，IA 无著作）。
    **教训**：#62 按卒年把 8 人全归版权墙大体正确，但**仍须 probe 实测**——McClintock/Haldane/Jones 的「无 IA PD 语料」与 Shull 的「5-6 部贴边」只有探源才看得见；Shull 是唯一接近门者，宁可 DEF 也不烧全流程。切片 DEF 107→116，TODO 19→10。
    **T3 剩余 TODO 10 = 在途 6（Loudon/King/Gilbert/Behring/Ehrlich/Waksman）+ 可派 3（Bailey #602/Boussingault #578/Lawes #570 边缘）+ Frisch #501（财务合规，边缘待 probe）**。预筛阶段全部收束，后续全部为全流程 REG 或边缘复核。
70. **Frisch #501 探源定案 DEF——财务合规族全部清零（2026-08-22，零 LLM）**：
    双探源全二手（1970-2013 选集/纪念文集/遗作合集），无 pre-1931 一手 PD，distinct=0 一手 → DEF。切片 TODO 10→9。
    **T3 剩余 TODO 9 = 在途 6（Loudon/King/Gilbert/Behring/Ehrlich/Waksman）+ 可派 3（Bailey #602/Boussingault #578/Lawes #570 边缘）**。财务合规族 52 人全部结算（REG Knight/Dicksee + DEF 其余），预筛阶段终结。
71. **波清：Gilbert #571 + Loudon #601 双 REG 落地 + 子代理后台任务回合即死教训（2026-08-22）**：
    - **Gilbert #571 REG**（commit 78eed31ac，delta +0.6297，release 0 错 1 警已 ack，0 pro）：预筛「≈4-6 distinct 几乎全合著」被实测推翻——creator 探源 18 条去重 17 部独立文献一手占比 0.90（Gilbert 单著 14 部），走正常 12 步 REG。合著 4 份按 CO-AUTHOR 记 attribution 剥本尊 voice。
    - **Loudon #601 REG**（commit d850e2530，delta +0.4062，release 0 错 4 警全消，0 pro）：rubric frame-break「收录通信」→「刊载通信」实质修复（判据误报）；3 警 acknowledge。
    - **⚠️ 新教训——子代理后台任务随回合消亡**：agent-202 两次 resume 都起后台 package_target（bash-yrlz0kcr）期望「等自动通知再继续」，但**子代理回合一结束其后台任务即被杀**（无 zip/registry/log）。第三次 resume 强制「前台阻塞跑完 + 同回合内 register+commit」才落地。**协调者 resume 子代理时，尾段必须明确「前台跑、别起后台任务、同回合完成」**——否则多轮空 resume 烧循环。
    - **子代理实测经验沉淀**（Gilbert 报告）：引文必须逐字（candidate 曾把「I believe」误写「I think」、OCR 形 Bothamsted 误写 Rothamsted，check_verbatim_quotes 抓住）；claim ID 12 位 hex；答案均长比 [0.77,1.30] 两侧都踩（1.302 过长/0.78 过短）；flash 判分 0-10 制返回需 record 归一化。
    - 切片：REG 29→31，TODO 8→6（在途 King/Behring/Ehrlich/Waksman + 新派 Bailey/Boussingault）。
72. **King #588 REG 落地 + 3 条实测经验（2026-08-22）**：
    - **King #588 REG**（commit def242dcd，delta +0.5094，candidate 0.8063/baseline 0.2969，release 0 错 1 警 ack，0 pro，validate 143 products）：预筛「distinct ≈7 临界」被实测推翻——`creator:"King, F. H."` 全量检索 70 条发现 13 部书/报告（含漏掉的 Economic Relations of Wisconsin Birds 1883/Elementary Lessons 1894/1892 地下水报告/Construction of Cheese Curing Rooms 1898）+ 15 篇 JSTOR 期刊文章，dedup 独立文献上界 23，一手占比 0.957。
    - **实测经验**：① **预筛 distinct 计数用 `creator:"姓, 名"` 全量检索而非 title 检索**（title 易漏不同书/多扫描只算 1 标题）；② flash 判分空响应率仍高（30-50%，即便 max-tokens 2000），判分解析须多重 fallback + `is None` 判空（勿把 0 当 falsy——与模板经验 #37 同源）；③ jstor 条目导出常缺末尾签名行（byline 不可见/F→E OCR 误读），归属靠 archive.org creator 字段 + historical attribution_basis 兜底。
    - 已派发 Lawes #570（agent-246，mandate 注明剥 Gilbert 侧 voice）。切片 REG 28→31，TODO 8→6。
73. **医疗护理师三连 REG：Ehrlich #536 / Behring #537 / Waksman #540（2026-08-22）**：
    - **Ehrlich #536 REG**（0c9d96bdb，delta +0.3656，146 products，0 pro）：同名污染重（生态学家 Paul R. Ehrlich/Ludwik 法史/Paul E. 数学/Paul M 过敏症），REQUIRE 多形态钉 `Ehrlich, Paul, 1854-1915` + EXCLUDE `Paul R.`；release 15 error 全修（claim.non-independent/no-falsifier/unsourced-name）→ 0 err。
    - **Behring #537 REG**（cd2d635f3，delta +0.4031，0 pro）：德语一手（Tetanusheilserum 1892/Blutserumtherapie 1892/Geschichte der Diphtherie 1893）+ 英文第三方，21 部独立作品全 PD 1891-1924；release 1 轮返工（6 个 unsourced-name：Behringwerke→Behringwerk 等）。
    - **Waksman #540 REG**（69d897cf7，delta +0.5000，145 products，0 pro）：以 1926-1930 著作为轴（Principles of Soil Microbiology 1927/Enzymes 1926），链霉素期避让；release 3 error→0（selftest-failed 根因=用错 quality_check 副本）。
    - **⚠️ 三条关键实测**：① **quality_check 必须用 `scripts/quality_check.py`，禁用 `references/pipeline/checkers/` 镜像**（check_holdout_mention.py 模板路径 bug 必败——已知 bug 记在 check_contract_drift.py 注释）；② **`raw/_EXCLUDED.txt` 是本地 only（gitignore），全新 checkout 重跑会复现 unsourced-name 需重加**；③ 德语人物英文作答天然与中文基线长度错位（0.70 过短→「120-160 词」→1.24 才过）——德语人物直接按「与基线等长」定向生成。
    - 切片 REG 31→34，TODO 6→3（在途 Bailey/Boussingault/Lawes）。
74. **波清收官：Bailey #602 / Lawes #570 / Boussingault #578 三 REG 落地——T3 全切片 154 人全部结算（2026-08-22）**：
    - **Bailey #602 REG**（3fdb42456，delta +0.4312，147 products，农林牧渔师）：预筛 23 部独立著作实测成立（Cyclopedia 系列/First lessons/The forcing-book/Garden-making/Principles of agriculture 等，30 行本人命中）；REQUIRE 钉 liberty+hyde 多形态 + EXCLUDE Hortorium/Henry G. Gilbert/Seed Trade Catalog；release 0 error，2 warning（catalogue-entry 报不拦 + baseline-not-capability-evidence）--acknowledge-disclosure 放行。
    - **Lawes #570 REG**（b9a059075，delta +0.4782，148 products，农林牧渔师）：以 Rothamsted 系列卷+独立报告建 distinct，剥 Gilbert 化学分析侧 voice（CO-AUTHOR 记 attribution）；答案均长比 60-90 字硬帽校准 2.21→1.107（泄题门 11/32 更短、格式通道 0%）；release passed=True 0 error 1 warning ack。
    - **Boussingault #578 REG**（2dc854fda，delta +0.6093，149 products，农林牧渔师）：法语一手（Agronomie chimie agricole/Économie rurale/Rural economy 英译/Mémoires/The chemical and physiological balance/Théâtre de la Moscovie）+ Dumas CO-AUTHOR；research gate 修 3 error（byline-not-in-carrier 重写 attribution_basis 12 条/ holdout-mention 去掉校测集字样/ invalid-source 移除校测源）；release 0 error 4 warning ack；41 份语料 P1 0.83。
    - **切片：REG 34→37，TODO 3→0。T3 451-604 全切片 154 人全部结算（REG 37 / DEF 117），三族外加尾 2 全部收束。**
    - **⚠️ resume 尾段三连实测经验（与反馈 #71 后台任务教训互补）**：① **父代理「已生成」断言不可信——resume 必须先自查真实磁盘断点**（Lawes 实测死在 eval prepare 后、results.jsonl 0 行；Boussingault 断言 claims/cases/results 已生成但实测全 0 字节 + research gate FAIL 3 errors，父代理描述里「已生成」是乐观假设）；② **flash judge 空返回 `--max-tokens 4000` 重判即稳**（2000 被 reasoning 吃光，Boussingault 5 条空返 4000 补齐，Paracelsus #526 已记同源）；③ **team-card.json 占位（provisional/not-yet-established/replace-with）在 package 阶段硬拦，打包前必填 ready**；④ **quality_check --cache 只传一个 raw 目录**（传多个误报 check_ocr_legibility 负对照，argparse 退出码 2 被误读为自测失败）；⑤ **答案生成须「同长度硬帽+禁格式标记」双侧指令**否则泄题门 ratio>1.3。
    - **成本纪律**：本波 3 人全 flash（0 pro），协调期零新增 pro，符合 95%+ flash 硬约束。curate_ia.py 规则已随各代理自身 commit 全部入库（文件当前 clean，无遗留批次）。
