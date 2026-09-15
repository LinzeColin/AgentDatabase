# persona-distiller 流水线实测经验

> 从 `AGENTS.md` 移出（2026-09-15）。做 persona-distiller 相关任务时读，其余任务不读。

## persona-distiller 流水线经验（2026-08-21 Telford#37 实测，供 T1/T2/T3 共用）

- **结论**：模型文档里引文坐标必须写成 `（src-XXX，YYYY 年）`，裸 `（src-XXX）` 不算坐标。
  **为什么**：check_quote_locator 的 LOCATOR 只认同段内的年份/页码/刊名/@偏移，不含 source_id；
  10 份产物一次性扫出 65 条缺坐标，release 被拦。**代价**：65 条 × 8 文件逐条返工（约 1 段）。
- **结论**：claims 层无排除机制——OCR 拼写变体（如 Pontcysyllte→Pontycysyllte）时，claim 文本必须
  用语料拼写；答案/产物可留标准拼写，但要在 `raw/_EXCLUDED.txt` 记录（二手依据，脱「无依据」）。
  **为什么**：check_claim_coverage 只看语料正文+台账，不读排除表；check_unsourced_names 读 raw/ 下
  `_` 前缀 .txt。**代价**：两个名字各一次拦门 + 一轮排查。
- **结论**：盲判载荷构建用 `--balanced-positions`（默认 sha256%2 可能偏，Telford 抽到 21/11）。
  **为什么**：位次与系统相关会灌进 delta（Holmes#170 实测位次效应 +0.015~+0.027）。重建只重排
  A/B 标签、不重生成答案，便宜。**代价**：重排后 judge 输入须重建（几行脚本）。
- **结论**：release 门扫 `evals/judge_payload.v1.json`（候选侧），不扫 A/B 盲判载荷——baseline 侧
  引文缺坐标不阻塞 release；基线 provenance warning 用 `package_target.py --acknowledge-disclosure
  '<warning 原文子串>'` 具名承认，不是 error，不打回。**为什么**：裸模型基线本来就是「非能力证据」，
  门拦的是冒充，不是发布。**代价**：0（按标准流程走）。
- **结论**：case-known 类题有意测 holdout 记忆，rubric 里会要求 holdout 细节（如 "Appendices 7-13"）；
  这类源标题词会穿过 holdout 泄漏门（非独有专名/数字）但被 unsourced-name 门抓——答案必须靠
  `_EXCLUDED.txt` 记录兜底，别去改答案。**为什么**：holdout 密封源正文不在 raw/，checker 查不到属预期。
  **代价**：Telford case-known-2 一次拦门。

## persona-distiller 预筛/收尾经验（2026-08-22 T3 会话实测，供三线程共用）

- **结论**：预筛 distinct 计数用 `creator:"姓, 名"` 全量检索，不用 title 检索。
  **为什么**：title 检索易漏不同书/多扫描只算 1 标题；King#588 预筛判「distinct≈7 临界」，
  creator 全量 70 条实得 13 部书/报告 + 15 篇期刊，上界 23、一手占比 0.957，正常走 REG。
  **代价**：0（多一次 creator 检索）。
- **结论**：「分类 ≠ IA 语料实况」——卒年/版次推断只是纸面，派发前必须 probe 实测。
  **为什么**：财务合规 PD 池 6 人（Cotrugli/Cerboni/Besta/Sprague/May/Canning）纸面全「PD 可做」，
  探源实测全 DEF（单著作天花板/独立著作<8/无 IA PD 语料）；Waksman#540 卒年推断归版权墙被实测推翻。
  **代价**：1 轮 6 人探源 TSV（零 LLM，便宜），换回不烧整窗全流程。
- **结论**：判分解析必须显式 `is None` 判空，禁止 `d.get("A") or ...`。
  **为什么**：`or` 把 0 分吞成 falsy 落到 fallback，统计全错。**代价**：一次全批分数失真 + 重判。
- **结论**：子代理（resume 尾段）后台任务随回合消亡——mandate 必须写明「前台阻塞跑完、
  同回合 register+commit、禁后台任务」。
  **为什么**：agent 两次 resume 都起后台 package_target 等自动通知，子代理一结束其后台任务即被杀。
  **代价**：多轮空 resume 烧循环（本会话一次）。
- **结论**：resume 代理不要信父代理「已生成」断言，先自查真实磁盘断点。
  **为什么**：Lawes 父代理断言 results 已生成实测 0 行（死 eval prepare 后）；Boussingault 断言
  claims/cases/results 已生成实测全 0 字节 + research gate FAIL 3 errors。**代价**：各补一段完整流水线。
- **结论**：flash judge 空返回用 `--max-tokens 4000` 重判即稳（2000 被 reasoning 吃光）；外语人物
  答案生成用「同长度硬帽 + 禁格式标记」双侧指令（泄题门 ratio>1.3 时）；`quality_check --cache`
  只传一个 raw 目录（传多个误报 ocr_legibility 负对照）；team-card.json 占位
  （provisional/not-yet-established/replace-with）在 package 阶段硬拦，打包前必填 ready。
  **为什么**：四者均为本会话 3 个 resume 代理实测踩坑；quality_check 须用 `scripts/quality_check.py`
  禁用 `references/pipeline/checkers/` 镜像（check_holdout_mention.py 模板路径 bug 必败）。
  **代价**：每项一次返工。
- **结论**：style-decoy 无数字题须禁中文量词全族（一/每/份/句/生/年/袋/匹），引文坐标用《书名》。
  **为什么**：Say#248/Franklin#236/Babson#234/Carnegie#176/Wanamaker#193 五人多轮被
  「一言以蔽之/每一分/一匹布/一生/身份」等判为违反无数字；check_self_reported_counts 把
  `[中文数字]{1,3}字` 当自报字数（「服务二字」「职业二字」都触发）。
  **代价**：每轮 1-2 题重生成+重建载荷+整份重判（约 15 分钟）。
- **结论**：trajectory 生平密集题必须把 rubric 锚点逐条（含 OCR 引文）写进 refine 提示，生成后逐锚点 grep。
  **为什么**：Say#248 traj-02 五轮才修完（漏 1813/1830/卒年/创办 vs 任编者）；Carnegie#176 traj-01/02
  首判编造年份数额被双席 critical。
  **代价**：每漏一锚点多一轮重判。
- **结论**：改答案/rubric 后重建盲判载荷，旧 judge 分数全作废，须清空整份重判（非只判改动题）。
  **为什么**：build_blind_payload 每次重新随机化 q 编号；Say#248 两轮、Babson#234 六轮均踩。
  **代价**：一轮 64 次 flash 判分（约 25 分钟），比"只重判改动题"贵但必须。
- **结论**：conversations 道手写信 OCR 常全灭（Edison#180：2 封 0-19 词乱码），探源须实测抓取核可用性。
  **为什么**：Edison 探源报 3 道（writings/conversations/expression），实测 conversations 4 条书信全乱码
  → 实际 2 道 <3 门槛，延后。
  **代价**：1 次抓取核验（便宜），避免整窗全流程后才发现缺道。
- **结论**：quick 档第 3 道可用 decisions 道补齐（JSTOR 政论文章归 decisions）。
  **为什么**：Babson#234 timeline 自传 1935 printdisabled 不可抓，用 JSTOR 1916/1912/1920 政论文章
  （A Business Man's View on Peace 等）补足 3 道。
  **代价**：0（JSTOR Early Journal Content 免费开放）。
- **结论**：三线程收敛回 main 用「复制 registry 新人物目录 + 同步切片台账」而非 git merge。
  **为什么**：T2/T3 分支基于旧分叉点，merge 会带入大量无关文件（cak-comfyui 等）与冲突；
  复制新人物（git ls-files 对比 main 独有 slug）干净可控。
  **代价**：54 人复制 + team-index 重建（脚本化，约 2 分钟）。
