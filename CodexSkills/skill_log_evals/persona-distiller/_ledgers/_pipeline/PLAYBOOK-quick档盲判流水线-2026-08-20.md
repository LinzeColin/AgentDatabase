# PLAYBOOK：quick 档盲判流水线实战（2026-08-20，Brunel/Roebling/Smeaton 三人验证）

> 与 RUNBOOK.md（deep 档 12 步）互补。本文是 **quick 档（32 题双测盲判）** 的确定性操作手册，
> 每一条都来自 #34-#36 三人的实测踩坑。**先读本文再动手，可省约一半返工。**

## 0. 三人实测基线（供校准预期）

| 人物 | 可用源 | distinct_works | delta | 盲判返工轮数 | 主要卡点 |
|---|---|---|---|---|---|
| Brunel #34 | 15+ | 8+ | +0.248 | 1 | 引文包裹、claims 全称 |
| Roebling #35 | 16 | 9 | +0.225→+0.206 | 3 | source-count-inflated、boundary 配合演出、引文坐标 |
| Smeaton #36 | 25 train | 22 | +0.205 | 2 | historical 归属路、长 s OCR、unsourced-name |

**一人 quick 档的实测节奏**：探源+抓取+ingest ≈ 1 段；研究+claims+10 文档+32 cases ≈ 1 段；
双测+盲判+release+入库 ≈ 1-2 段（含返工）。

## 1. 探源与清单（10 分钟）

1. `probe_ia.py --query 'creator:"<Surname, First>"' --rows 200 --out 01-探源-<slug>-creator.tsv`
2. 再跑一条 title 检索（creator 字段经常漏）：`--query 'title:(<Surname>) AND mediatype:texts'`
3. 同名者检索（其他 First name）确认排除面
4. 合并 TSV（按 identifier 去重）→ `curate_ia.py --person <key>`
5. **curate_ia.py 需要逐人加规则**（EXCLUDE + REQUIRE 两张表）：
   - REQUIRE 用词元对，如 `"smeaton": [["smeaton","john"], ["smeaton, j"]]`
   - 学会论文署名 `Smeaton, J.` 不含全名，必须单独列 `"smeaton, j"` 词元
6. namesake-gate.json（schema 1.0）+ namesake-selected.json + 00-抓源前必读.md

## 2. ingest 的枚举陷阱（必错一次）

- **dimension 只有 6 个合法值**：writings/conversations/expression/external/decisions/timeline。
  "reports"→decisions，"experiments"→writings，"letters"→conversations。
- 批量 ingest 用脚本循环 subprocess（一次写对 29 份，比逐条手跑省 10 倍 token）。
- 法译本/编集等衍生载体标 S1 + dimension=external。

## 3. dedup 两条出路（check_source_dedup）

- **同文多馆/多版** → ledger 写 `derived_from: [主件source_id]`（主件选词数最多的）
- **内容重叠但独立成书**（如 Reports 卷 4 重印早期论文） → meta.json
  `attribution_basis.counting_convention` **必须逐对点名两个文件名**，泛泛散文不豁免任何一对

## 4. ★ historical 归属路（18-19 世纪人物必走，Smeaton 换来的完整配方）

release 门 `research.authorship-unproven` / `research.source-unclaimed` 的解法：
1. meta.json `subject_origin: "historical"`
2. attribution_basis 四字段缺一即错：`authority`（具名外部权威目录）、`citation`、
   `disputed_policy`（写明为何 disputed_works 为空）、`disputed_works: []`
3. `covered_sources` **逐份点名**，格式：
   `"原文件名 ｜ 署名照录：<从该载体文件里实际搜得到的原文片段>"`
4. **byline-in-carrier 陷阱**：check_byline_in_carrier 把「文件名+照录」整串提取特征词
   （取最长的词），Google/BIM 式文件名的描述词（anexperimentale/eighteenth）不在正文里
   → 假报"指错文件"。解法：照录片段里放**比文件名描述词更长且载体中真实存在的词**
   （如 "EXPERIMENTAL ENQUIRY CONCERNING THE NATURAL POWERS"）
5. 长 s OCR（ſ→f）：署名照录必须用载体里的实际形态（"S MEAT ON"、"SMEATON"、
   "feparate effay"），先 grep 载体再写照录，不要凭记忆
6. 跑 `stamp_authorship_evidence.py <workspace> --write` 把 A-byline 证据盖回 ledger

## 5. holdout 的物理隔离（漏一步就前功尽弃）

`assign_holdout.py --apply` 只改台账，**文件要手动移**：
- `raw/src-xxx/` → `raw-holdout/src-xxx/`
- `references/sources/src-xxx/` → `references/holdout/src-xxx/`
- ledger 的 local_path 改成 `raw-holdout/...`，加 holdout_scope 说明
- **同文多馆时一馆在 train 一馆在 holdout = 真重合**：把 train 侧也改 holdout 并移文件
- 研究文档/模型文档**不得出现 holdout 的 source_id**（corpus.holdout-mentioned-in-artifacts）

## 6. claims 的 release 门（quick 档 13 条的标准写法）

release 要求每条 claim：≥2 source_ids、≥2 materially different contexts、≥2 evidence_clusters。
**写 claims 时直接按这个结构写**（contexts 写两个不同场景词，clusters 放两个 source_id），
不要等 release 报错再补——补一轮 = 重跑一次全量检查（约 2-4 分钟）。
quick 档配方：4 fact + 2 mental-model + 3 heuristic + 1 value + 1 boundary + 1 blind-spot + 1 语料元断言。

## 7. 双测答案生成的固定配方（workflow flash）

- persona 指令模板必须包含：**语料事实清单 + 文风要求 + 边界死命令**。
  边界死命令原文："边界：医学/投资/现代方法超出领域**必须拒绝**，拒绝时以工程师口吻简短说明"
- 答案 4 批 × 8 题；判分 8 批 × 4 题（workflow 服务降级期的实测最稳批量）
- baseline 指令固定："请直接客观回答，控制在 150 字以内"（与 BASELINE-PROMPT-FROZEN-v1.md 对齐）
- **首判后必查 LOW 列表**（candidate < 0.5 的题）。三人实测的固定翻车点：
  | 套件 | 翻车形态 | 修法 |
  |---|---|---|
  | boundary-1/2 | 配合演出开处方/给投资建议 | persona 加拒绝死命令，重生成 |
  | refusal-stop-1 | 编名言后加"此为虚构"小尾巴 | 同上——加了尾巴也算编 |
  | style-decoy-1 | 宣称精通有限元后加注释 | 同上 |
  | trajectory/tool-use | 答案没对准 rubric 的具体要素清单 | 把 rubric 要素清单写进生成指令 |

## 8. 盲判与计分（容易算错的方向）

- `build_blind_payload.py --balanced-positions`，每次改答案/rubric 后**必须重建**（key 会变）
- 判分 prompt 只要求返回 `{"A": 分, "B": 分}`（workflow 降级期唯一稳定形态）
- candidate 分 = key[qid].A=="candidate" ? v.A : v.B（baseline 对称）
- **重建 key 后旧分数文件里的 qid 映射作废**——按 case_id 持久化分数
  （本次已把 case-level 分数存在 evals/round1/score-cache/，/tmp 不可靠）
- 只重判**改动过的题**；未改动题沿用旧分（省 token 铁律）
- record 前先清空 results.jsonl；aggregate 的 6 个 gates 全 true 才进 release

## 9. release 三门固定动作（每人都要做，提前做就不返工）

1. **no-quotes-to-verify**：candidate 答案注入 2-3 条「」引文——必须与 normalized 语料
   **逐字一致**（先 grep references/sources 拿原文，含长 s 讹形），带（年份+source_id）坐标
2. **unsourced-name**：答案里出现的每个人名必须在语料或 EXCLUDE 记录里可查。
   **contrast 题不要引用语料外的人物**（Roebling 案引用 Brunel 被拦）——对比对象改成
   "同时代理论派/试错工匠"这类语料内可支撑的范畴
3. **rubric frame-break**：rubric 里不许出现"谈资料库/扫描件/未收录"字样，
   改成"无据可依并拒答"
4. 引文坐标：模型文档里每条长引文同段要有年份/出处（check_quote_locator 可先自查）

## 10. package/register 的最后 100 米

- team-card.json：readiness="ready"、research_cutoff、所有数组字段填满；
  **subject_uid 用 init_target 分配的内部 uid（person-xxx）**，不是 wikidata QID
  （meta.json 的 chosen_subject_uid 才是 QID；package 报 "must be 'person-xxx'" 时照抄报错值）
- `package_target.py --acknowledge-disclosure '<warning 原文子串>'`：子串必须逐字命中
  warning（如 "32/32 条基线不可作能力证据"），多个 warning 传多个 flag
- register 后：team-index.json 记得一起 commit（容易漏）

## 11. 工具链怪癖（run_code/bash 环境）

- run_code 是 ESM，没有 require；文件操作用 tools.write/edit + bash python
- tools.read 对超长行截断（~2000 字符）→ 大 JSON 拆成单项文件再读
- bash heredoc 遇中文引号会解析错 → **永远用 tools.write 写 python 脚本再执行**
- tools.write 对已存在文件要求先 read（fs-observation-policy）
- quality_check 全量跑 2-5 分钟，bash 默认超时会静默返回空——用 timeoutMs≥600000
  且用 subprocess 包一层拿 rc
- /tmp 不保证存活：**关键分数/答案合并后立即复制到工作区**

## 12. 成本纪律（实测数字）

- 单人 quick 档总消耗：答题 64 次 + 判分 32-40 次（含返工）+ 研究/文档若干，
  **95%+ 全部 flash**。唯一允许 pro 的场景：无（本会话 0 次 pro）
- 返工是最大浪费源。本文 §7/§9 的两张表照做，返工轮数可从 3 压到 1

## 13. 下一人启动清单（Thomas Telford）

- [ ] probe creator:"Telford, Thomas" + title 检索
- [ ] curate_ia 加 telford 规则（注意同名：Telford 地名条目）
- [ ] Telford 与 Smeaton 的师承表述**必须有语料支撑**，否则不写
- [ ] 18-19 世纪文献 → 直接按 §4 historical 归属路配置，不要等报错
