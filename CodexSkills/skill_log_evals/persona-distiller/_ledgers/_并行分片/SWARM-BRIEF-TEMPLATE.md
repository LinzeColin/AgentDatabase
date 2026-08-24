# T3 Swarm 子代理委托模板（每 {{item}} = 一个 coder 子代理跑完整 12 步）

> 用法：AgentSwarm(subagent_type=coder, items=[候选串], prompt_template=本模板)。
> 候选串格式：`<编号>|<slug>|<姓名>|<族>|<身份号>|<消歧备注>`
> 例：`527|ambroise-pare|Ambroise Paré|医疗护理师|11|16世纪法国外科之父；1649英文The Workes在IA`
>
> 本模板基于 Paré #527 首跑实测定稿（第一人入库前先验证其可用性再批量分发）。

## 使命
为 {{item}} 的**人物**完整跑通 persona-distiller 12 步蒸馏流水线并 register + commit。
这是 T3 切片（451-604）内的普通一人，流程与样板一致。

## ⚠️ 并发纪律（本会话多子代理并行，务必遵守）
- **不要动 TodoList**（与父会话共享，你一动就覆盖父会话的编排清单；你的进度写在工作区文件即可）。
- **绝不运行任何全仓扫描类命令**（会覆盖其他并行子代理/T1 已完成的共享工作区）：
  - `check_measurements_fresh.py` 必须带 `--workspace <你自己的工作区>`，**禁止全局 `--apply`**；
  - `classify_primary.py`/`assign_lanes.py`/`emit_source_ledger.py` 的 `--raw`/`--workspace`
    只能指向你自己的人物工作区，**禁止指向或循环遍历其他 wip-*/ 目录**。
- **commit 只 add 你自己的路径**（绝不 `git add CodexSkills/` 整目录，那会把其他并行子代理的在途文件一起 stage）：
  ```
  git add CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-<slug>-<n>/
  git add CodexSkills/registry/codex/persona-distiller-group/<族>/<slug>/
  git add "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_并行分片/T3-451-604.json"
  git add CodexSkills/registry/codex/persona-distiller-group/team-index.json   # register 产物（如有 diff）
  ```
  全部 add 与 commit 必须在 `tail_lock.py` 锁内执行（见「尾段」节）。
- **register + commit 尾段用锁串行化**；不要在锁外做任何 git add/commit。
- 你的 curate_ia 消歧规则若已在仓内预置（avicenna/paracelsus/morton/simpson 已由协调者预置），
  直接跑 `curate_ia.py --person <key>` 验证即可；若发现池里仍有漏网同名，按 tail_lock 锁内补规则并随你 commit。

## 工作目录与环境
- 工作目录：/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T3（git worktree，分支 thread3-451-604）
- 禁止：切分支、git merge/pull/push/rebase/reset。只允许最后 git add + commit（只限 CodexSkills 子目录内）。
- 蒸馏 skill 脚本：CodexSkills/registry/codex/persona-distiller/scripts/
- 流水线辅助脚本：CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/
- 样板（照抄其结构）：CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-smeaton-36/john-smeaton/
- workflow 通道包装（所有 DeepSeek flash 调用走它）：_ledgers/_并行分片/tools/wf.py
- 尾段互斥锁（register+commit 串行化）：_ledgers/_并行分片/tools/tail_lock.py
- 切片 JSON（只更新其中本人物编号的 status）：_ledgers/_并行分片/T3-451-604.json
- 你的人物探源 tsv 已预抓在：_corpora/_probe-T3/<key>.tsv（若缺可自跑 probe_ia.py）

## 必读（动手前按序读）
1. _ledgers/_pipeline/PLAYBOOK-quick档盲判流水线-2026-08-20.md（quick 档手册，最优先）
2. _ledgers/_pipeline/README-抓源到阶段2.md
3. _ledgers/_pipeline/HANDOFF-2026-08-20.md（12步+9坑）
4. registry/codex/persona-distiller/SKILL.md
5. 精读样板 wip-smeaton-36/john-smeaton/（meta.json historical 归属路、source-ledger、research/、evals/、team-card）
6. 尾部命令不熟时 grep RUNBOOK.md

## workflow 通道（wf.py）
- 单次：python3 <wf.py路径> call --model flash --prompt '...'；批量：... batch --model flash --in x.jsonl --out y.jsonl
- 双侧盲判必须同模型（默认 flash）；pro 仅四触发（门线±0.03/两席分歧>0.1/首轮未过/发布门红）
- 答题 4批×8、判分 8批×4；判分 prompt 只返回 {"A":分,"B":分}；结果立即落盘工作区

## 12 步（严格顺序）
探源(namesake-gate)→fetch_ia→ingest(tier/dimension 6 值)→dedup(derived_from+counting_convention)
→holdout(assign_holdout --apply+移 raw/src-* 到 raw-holdout/、references/sources/src-* 到 references/holdout/)
→6 路研究文档→claims→10 模型文档(非占位)→32 cases(16套件×2)→eval_runner prepare
→双测答案(flash 4批×8)→build_blind_payload(--balanced-positions)→盲判(flash 8批×4)
→record→aggregate→quality_check release --strict(0错0警)→package_target(--acknowledge-disclosure '<warning原文子串>')
→register_persona→切片JSON status→commit。

## 本人物要点（{{item}}）
- 姓名/族/身份号/工作区/注册目录/消歧备注见候选串。
- 工作区：_corpora/wip-<slug>-<编号>/<slug>/；注册目录：persona-distiller-group/<族>/<slug>/。
- 身份：12 族之一（1材料建工 2软件开发 3艺术设计 4创业经营 5投资资本 6思想教育 7政治法律 8客户营销 9建造采购 10财务合规 11医疗护理 12农林牧渔）。
- 归属路：subject_origin="historical" + attribution_basis 四字段 + covered_sources 逐份点名（原文件名 ｜ 署名照录：<载体中真实存在的原文>）。
- PD：版次年 ≤1930，scan_copyright.py 逐条读命中；access-restricted 跳过。
- 早期现代字体长 s（ſ→f）；署名照录先 grep 载体用实际形态。
- team-card subject_uid 用 init_target 分配的内部 uid（person-xxx），不是 wikidata QID。
- profile：quick 档（32 题双测）；check_corpus_ceiling --ledger 决定实际档位。

## curate_ia 规则（消歧）
- curate_ia.py 需要给 key <slug去横线> 加 EXCLUDE/REQUIRE 规则（照 PLAYBOOK §1 与既有条目格式）。
- **改 curate_ia.py 必须套尾段锁**（防并发覆盖）：
  `python3 _ledgers/_并行分片/tools/tail_lock.py -- bash -c '...你的 Edit/写规则动作...'`
  实际做法：先 Read curate_ia.py 确认最新内容，在锁内用 Edit 追加你的规则；若 old_string 失效重读再试。
- 这属于惯例（逐人加规则），不是改判据/门。

## 硬约束（不可违反）
- 零编造：事实必须语料可查；「」引文逐字一致；答案人名语料可查（contrast 题不引用语料外人物）。
- 语料原文不进 git（gitignore+门兜底）；只 commit 派生文档/台账/evals 产物。
- 只 commit 你的产物：_corpora/wip-<slug>-<n>/（非语料）、persona-distiller-group/<族>/<slug>/、切片 JSON 的本编号 status、register 生成的 team-index.json 变更。
- 只读共享台账：GOAL-STATE.json、GOAL-LOG.md、_蒸馏队列.json、_延后名单.json 一律不改。
- 不碰 _protected/；门/席位/评委指令/判据脚本冻结不动。
- 有不确定→停下汇报，不要猜。

## 尾段（发布→登记→提交）
> ★★ **release 门 0 错 0 警 是 package_target 的前置条件**：先跑
> `quality_check.py <WS> --phase release --strict --write-report`，确认 passed=True 且 0 错 0 警，
> **才允许** package_target。**禁止**用 package_target 的 `--skip` 出非 release-ready 包，
> **禁止**先打包后补门（Paré #527 曾因先打包、门 FAILED(18错) 被协调者拦截）。
> 若 release 门报错，先修（claim.orphan→用 `<!-- claim:clm-xxx -->` 渲染进模型文档；no-quotes-to-verify→注入逐字引文；
> unsourced-name→删语料外人名；quote-no-locator→补年份/出处；undeclared-duplicate-sources→补 derived_from），
> 再重跑直到 0 错 0 警。
> ★ **package_target 在锁外跑**（它是工作区本地操作，内置 release 门在 20M 词大语料上要 10-12 分钟；
>   放锁内会把整个登记队列串行挡住——Paracelsus #526 实测）。只有 **register_persona + git add/commit + 切片 status** 进锁。
> ★★ **QC 报 coverage-unresolved / selftest-failed 时先查语料管线，别修 QC 参数**（Darwin #572 实测）：
>   raw/ 必须含 `_dedup.json`/`_lanes.json`/`_primary.json`/`_copyright-scan.json` 等管线元数据，
>   raw-holdout/ 必须是 `src-*` 子目录结构（对比已登记 wip-jethro-tull-573/jethro-tull）。若只有裸 .txt，
>   是 ingest→dedup→holdout 没跑完整——重跑语料管线，而不是调 QC 的 --cache/参数。
> ★★ **resume 的代理必读本节再动手**（Lavoisier #569、Adam Smith #475 两个 resume 代理都因带旧上下文把
>   package_target/QC 塞进锁内、且用 `--output dist/` 相对路径违反纪律；旧上下文不认新模板）。
>   `--output` 必须写完整路径 `<WS>/dist`，不是相对 `dist/`——相对路径会把 zip 打到 worktree 根，register 后
>   git 里就没有该人的交付 ZIP（team-index 说 N 人、实际 N-1 个 zip 的坏状态）。
```
python3 CodexSkills/registry/codex/persona-distiller/scripts/package_target.py <WS> --output <WS>/dist --acknowledge-disclosure "<warning子串>"   # 锁外，慢
python3 _ledgers/_并行分片/tools/tail_lock.py -- bash -c 'cd /Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T3 && \
  python3 CodexSkills/registry/codex/persona-distiller/scripts/register_persona.py <WS>/dist/<zip> && \
  git add CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-<slug>-<n>/ && \
  git add CodexSkills/registry/codex/persona-distiller-group/<族>/<slug>/ && \
  git add CodexSkills/registry/codex/persona-distiller-group/team-index.json && \
  git add "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_并行分片/T3-451-604.json" && \
  git commit -m "T3 #<n> <slug> 入库(<总数>/600): delta +X.XXX"'
```
- 若你在锁内补了 curate_ia 规则，另加 `git add CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/curate_ia.py`。
- 每次 commit 后立即更新切片 JSON 的 status 为 REG（同样建议在锁内做，避免并发写同一 JSON）。
- 总数 = git ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l 自己 worktree 的数 + 主树基线 117。
- package_target 需要 --acknowledge-disclosure 传 warning 原文子串（多个 warning 传多个 flag）。

6. **claim 渲染用 HTML 注释**：核心模型文档里引用 claim 必须写 `<!-- claim:clm-xxxxxxxxxx -->`
   （普通 `ref: clm-` 不认，会报 claim.orphan）。
7. **holdout 移动后清残留**：raw/src-* 移入 raw-holdout/ 后，还要
   `find references/sources -path '*/<src-id>/*' -delete` 清掉 normalized 副本，否则报 holdout-leak。
8. **candidate 答案 ≤80 字**：build_blind_payload 对均长比 >1.3 拦派发；persona 生成指令显式约束字数。
9. **team-card subject_uid 照抄 package_target 报错值**（person-xxx），不要手写。
10. **模型文档里的长引文也要坐标**：check_quote_locator 扫 RENDER_FILES（模型文档）不只扫 judge payload——
    模型文档每条长引文需「」包裹 + 年份/source_id。
11. **wf.py 判分要判空**：batch 25-40% 返回空 content，脚本必须逐条检查 content 非空并重试空返回。
12. **wf.py 调用默认 max_tokens≥2000**：DeepSeek flash 的 reasoning_tokens 会先吃满预算，max_tokens 100-200 时 content 全部空返回（Tull #573 实测）。判分/答题批量一律用默认 2000，脚本不手改小 max_tokens。
13. **单著作多版本人物 distinct_works 天花板**：传世著作单一的 18 世纪人物（Tull #573 实测），16 份去重后作品数可能 < quick 门 8。解法：补 2-3 份**第三方独立著作**（同时代他人写的该书评/游记/农学书）而非再加同一书新版本，把 distinct_works 拉过门。
14. **盲判答案长度平衡**：candidate 答案 80 字过严（fact-preservation 判 0 分）、150 字过长（均长比 >1.3 拦派发）。Tull 实测 100 字 + 手动修剪最长 5 条才过门。答案生成指令写「≤100 字」，build 前自查均长比，超则修剪而不是改判据。
15. **flash 盲判空响应率高，判分 prompt 要短**（Lavoisier #569 实测 32/48 空 ≈67%）：长 prompt + JSON 返回在 flash 降级期极不稳定，单条短 prompt 可恢复。判分 prompt 尽量 <200 字；空响应先按「缩短 prompt + 单条重试」处理，不要盲目整批重跑。另注意 **frame-break 检测器对「语料」子串过敏**——rubric 里写「语料内有」会误报「资料层词」，改「文献」可规避。
16. **claim ID 必须是 12 位十六进制**（Reed #549 实测）：quality_check 正则 `clm-[a-f0-9]{12}`，init_target 生成的 `clm-0000000001`（10 位十进制）不认。10 以上 claim 要转 hex（a/b/c/d）。模型文档里的 `<!-- claim:clm-xxx -->` 与 evidence/claims.jsonl 的 ID 必须一致且 12 位 hex。
17. **wf.py judge 返回格式不统一，需多重 fallback**（Reed #549 实测）：可能返回 `{"A":9,"B":2}`、`["9","2"]`、`["A_SCORE":10,...]` 三种形态。判分解析脚本写三重 fallback；只认一种会漏判。另 eval_runner record 覆写 results.jsonl（清空而非追加）——批量 record 需手动写或逐条追加。
18. **低产量人物 source-count-inflated 是硬墙**（Reed #549 实测）：出版量少且被编译集重印的人物，去重后 distinct_works 可能 < 门 8。解法：holdout/train 交换 + 把「同书重印的编译集」标记 failed 而非计入 distinct；判据侧阈值冻结只报（T1 侧评估 profile 动态阈值）。
19. **team-card user_value 是必填数组字段**（Young #597 实测）：package_target/register 会因缺 user_value 报错或 validate_group 失败。模板样板里若有就照抄结构，没有就补一个 `"user_value": [{"维度": "...", "价值": "..."}]` 数组。
20. **check_quote_locator 连直引号也扫**（Young #597 实测）：claims.jsonl / 模型文档里的 `""` 直引号也会被扫描并报 quote-no-locator。所有引文统一用「」（fullwidth）+（年份, source_id），不要用 ASCII 直引号。
21. **答案里的引文 vs 表面泄露平衡**（Ross #550 实测）：build_blind_payload 的坐标门与 no-quotes 门矛盾——候选答案若带引文需坐标、坐标会暴露候选侧（surface-leak）。解法：**答案不放引文（rc==3 放行），引文只放模型文档（RENDER_FILES）**。
22. **curate_ia 的 REQUIRE 和 EXCLUDE 必须同步加键**（Davy #577 实测）：REQUIRE 有 `davy` 但 EXCLUDE 没有会报「未知人物键」。两表都加。另阿拉伯/波斯人物 **nisba 同名预警**（Rhazes #525 实测）：`razi` 作为 nisba 极常见，REQUIRE 用多形态（rhazes/rhazès/rhasis/zakariya）而非单一 nisba。
23. **suite 名称必须匹配 eval_runner 硬编码集合**（Rhazes #525 实测）：boundary/fact-preservation/style-decoy/refusal 等有效名，coverage/plan-fidelity 等自定义名全被拒。建 cases 前先查 eval_runner.py 的有效 suite 名清单。
24. **judge_payload 需扁平 JSON 给 surface-leak 读**（Rhazes #525 实测）：quality_check 期望 `{case_id: answer_text}`，build_blind_payload 输出 `{case_id:{question,A,B}}`——需手动转扁平。字段名用 `case_id/question/A/B`（非 qid/prompt）。
25. **wf.py 判分返回形态高达 5 种**（Davy #577 实测）：除 Reed 的 3 种外还有 `{"A":"满分","B":"满分"}` 文本形态。fallback 解析需覆盖：纯数字 JSON 对象 / 文本分 JSON / 数组 / A_SCORE 键 / 直接文本。判分脚本写全 fallback，解析失败记中性分并注明（不要静默）。
26. **results.jsonl 的 `dimension_scores` 为空是常态，不是判分失败**（Paton/Marshall/Pavlov 三连实测）：judge 以 `overall_score` 入行，`dimension_scores` 在 aggregate 阶段才由套件分合成。判分完成的判据是 results.jsonl 有 64 行 + eval-run/quality 报告可跑，**不是**看 dimension_scores。真要查状态看 release 报告的错误清单。
27. **分发前先探源预筛**（2026-08-21 T3 协调者策略）：单著作+版本稀少的 19 世纪人物（Seacole #530/McAdam #451 型：一手占比 1/9 < 40%）与 JSTOR Early Journal Content 期刊样板人物（Wald #531 型：8 篇独立文章共享页首样板被 min-hash 归 1 簇）基本必 DEF。分发前用 probe_ia 查：版本数/独立著作 ≥8、一手占比充足、版次年 ≤1930；不达标不发或直接预筛 DEF，避免整窗烧在必 DEF 人物上。
28. **2h 窗口对完整 12 步偏紧，超时≠失败**（历史 TaskList 实证）：早期 16 人全部经过「续跑→修门→尾步」多轮 resume 才完成，超时是常态。协调者 resume 时给**阶段明确 mandate**（如「判分完成，跑 record→aggregate→release→package→register」），比让代理重头跑更省、更可靠。
29. **pro 仅单次关键重判，禁止整批 pro**（2026-08-21 成本分账实证，反馈 #52）：Marshall/Freud/Pavlov resume 窗口内 32 次 batch 判分全用 pro（门线±0.03 触发被整批套用），pro 成本推到 9% > 5% 纪律线，且这批 pro 花在最终 DEF 的人物上（零产出）。**门线/红门触发只允许单 case 关键重判用 pro**，常规判分批一律 flash。
30. **resume 代理首次写入耗时 19-35 分钟**（2026-08-21 实测：Dicksee 19min/Sanger 23min/Cobbett 30min/Malthus 31min，与上下文规模成正比）：大上下文 resume 的「静默期」是正常上下文恢复，不是停滞。**停滞判定对 resume 代理放宽到 40+ 分钟**（新发代理维持 60 分钟）；判定用工作区 mtime + 是否建目录，不用 TaskOutput（running 恒 0 字节）。
31. **防死循环：故障风暴禁批量 resume，改 fresh dispatch + 防死循环护栏**（2026-08-21 400 Format Error 风暴实证，反馈 #53）：8 个在途子代理在 39 秒窗口集体以 `400 Format Error` 终止 = scnet 提供方瞬时全局故障（非管道 bug；wf.py 直连全程健康）。把终止代理逐个 resume 进同一故障窗口会反复撞墙（8 次 resume 全废）。对策：① 故障期间禁批量 resume，等 wf.py 单次探测恢复再动；② 一律 fresh dispatch（小上下文启动，mandate 显式「从磁盘续做、禁止重跑已完成步骤」）；③ **防死循环护栏**：代理自身回合连续 HTTP 400/5xx → 退避重试 ≤5 次/数分钟，仍持续 → 写 `STOP-STATE-<slug>.md` 记录停点并立即退出，绝不无限重试；④ 以磁盘 stage 报告判定（reports/quality-research-*.json / quality-release-*.json 文件名带 UTC 时间戳，errors 空即过门），不盲信代理存活状态。
32. **dispatch 前先查 person 是否已 REG/DEF + 任何 re-judge 后必须重跑 aggregate**（Malthus #580 实测，2026-08-22）：① 400 风暴后部分前代理会**自行恢复跑完尾段**——Malthus 的 dispatch 快照停在盲判中断时，但接手时发现前代理已判分(64行)→release→register→commit 全部完成，派 fresh 代理纯属多余（零 LLM 消耗收尾，verify 通过即确认 REG，勿重注册）。**dispatch 前先 grep 切片 JSON 该编号 status**，已 REG/DEF 就直接核验收口，不再派。② **boundary/门线 re-judge 后未重生成 eval-all.json 会留 stale 记录自相矛盾**（delta 0.0688/boundary=false 与已提交 results.jsonl 不符）——任何重判后必须重跑 `eval_runner.py aggregate --write-report`，把模板经验固化进尾段。
33. **release 门 FAILED 必须先读全 errors，再判定「记账可修」还是「需重建」**（Sanger #532 实测，2026-08-22）：发布报告可能同时含记账类（ledger.invalid/claim.status 非法/corpus.undeclared）与实质类（eval.overall-threshold、eval.fact、content.no-quotes、claim.insufficient-support、claim.heuristic-minimum、derived_from 未声明）错误。**只看 ledger 类就动手修会漏判**。判定程序：① 读全 errors；② 修唯一客观可修的记账问题（如 claim status 填类别名而合法值只有 fact/pattern/hypothesis/unknown/superseded）；③ 重跑 release 门看剩余错误；④ 若剩余是 eval 门高于 judge 实测上限（如 32 席上限 0.469 vs 门 0.650）、答案引文不成对/伪 locator、缺独立来源等需重建语料/答案的根本失败 → 锁 DEF（证据 + 复跑路径），不无限修。
34. **release check_quote_integrity 只扫 claims+answers，不扫研究文档**（Gorgas #552 实测，2026-08-22）：研究文档里逐字引文再多也不算数，`content.no-quotes-to-verify` 照样报。解法：把**逐字可查的「」引文 +（年份, source_id）坐标直接嵌进 claim 文本**（含 fact/value claim），别指望研究文档替 claim 兜底。
35. **candidate 过短同样被表面泄露门反向拦 + known 套件必带 holdout_source_ids + CHECKPOINT 按 mtime+产物清单固化**（Evelyn #599 实测，2026-08-22）：① 模板经验 14 只写了「过短判 0 分 / 过长拦派发」，实测 candidate 均长 60 字（ratio 0.57 < 0.77）也会被 build_blind_payload 拦——**过短同样算表面泄露信号**，指令写「≤100 字」但须自查均长比两侧。② smeaton 样板的 known case 有 `holdout_source_ids` 字段，但新人物 case 生成脚本常漏带 → release 门报 known-holdout；**known 套件必须带 holdout_source_ids（对应 4 份 holdout）**。③ 协调者阶段判定用「上次写入文件 mtime + 产物清单」（dist zip/team-card/registration 存在与否），比阶段名可靠（简报常滞后磁盘）。
36. **release「0错0警」实际执行口径 = 0 error + warning 逐条 acknowledge + verify_persona 须从 REPO 根跑 + flash 判分空响应 14/32 是常态**（Marsh #591 实测，2026-08-22）：① 已登记 tull 的 release 报告也是 0 错 2 警（FAIL 状态但靠 `--acknowledge-disclosure` 放行）——模板字面「0 警」与实际口径（0 error + 每警具名承认）有出入，协调者判 REG 以此口径为准，勿因「有警」误判 FAIL。② `verify_persona.py` 用相对路径（`os.path.join(reg,...)`）存在 cwd bug——**必须从 REPO 根（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T3）跑**才正确，从其他目录跑会误报「缺 team-card.json」。③ flash 判分空响应/截断率高达 14/32（44%），与 Lavoisier #569 一致——极简英文 prompt + 单条重试是标准配方，个别持续 8+ 次空返回才允许 pro 单条兜底（本次 q-06 已如此，属纪律内）。

## 回报（结束给紧凑结论）
1. delta（candidate vs baseline）与 aggregate 各门
2. release 门 0错0警？返工轮数
3. wf.py usage 分账
4. commit hash
5. 暴露的问题/判据疑点（供 THREAD-FEEDBACK-T3.md）
6. 下一位人选建议
37. **判分解析 `d.get("A") or ...` 吞 0 bug（Frank Knight #486 实测，2026-08-22）**：判分脚本解析 JSON 时用 `d.get("A") or d.get("A_SCORE") or d.get("A_score")` 链式兜底——**0.0 当 falsy 直接吞掉**，a/b 变 None → 落进 regex 分支，而 regex 分支一律 `/10`（假定 0-10 标度）。0-1 标度下凡一方得 0 分，另一方正常分（如 0.9）被压成 0.09，19 题被压坏。**修复：显式 `is None` 判断逐键兜底**，且判分完成后打印分数分布自检（全部落在 [0,1]、无整批 0.1 倍缩放痕迹再进 assemble）。教训通用化：**判分解析任何 falsy 值（0/""）都要用 `is None` 判断，别用 `or` 链**；解析结果写盘前打印 min/max/分布核对。
38. **并行写入必须互斥：dispatch 前先查切片 status + ps 查进程存活（Dicksee #495 实测）**：协调者同一批同时 resume 多个代理（Dicksee 与 Knight 同窗），代理写磁盘阶段产物无锁，偶发同文件竞争。对策：① dispatch/resume 前先 `git status` + 查切片 JSON 该编号 status（已 REG/DEF 就直接核验收口，不派）；② 对共享脚本（curate_ia.py）的改动由协调者统一 stage/commit，代理只在自己的 wip 目录写，不碰共享脚本；③ 多代理同窗时，协调者只在 tail_lock 内做 git 提交，避免与代理写盘竞争。
39. **子代理后台任务随回合消亡——尾段必须前台跑完**（Loudon #601 实测，2026-08-22）：子代理在回合内 `run_in_background` 起的 bash/package 任务，在其回合结束时即被杀，产物零落盘；「等自动通知再继续」在子代理语境不存在。协调者 resume 时尾段 mandate 必须写死：「**前台阻塞跑完每一步、同回合内完成 register+commit、禁止起后台任务**」，否则多轮空 resume 烧循环。
