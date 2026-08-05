# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-adams-131/workspaces/comfort-avery-adams`
- Phase: `synthesis`
- Profile: `quick`
- Generated: `2026-08-05T01:56:32Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 72,
    "claims": 10
  },
  "sources_total": 72,
  "sources_train": 69,
  "sources_usable_train": 69,
  "sources_holdout": 3,
  "primary_sources": 69,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 6,
    "conversations": 60,
    "expression": 2,
    "external": 0,
    "decisions": 0,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 71,
    "已证实归属": 71
  },
  "corpus_integrity": {
    "已扫": 72,
    "不是语料": 0,
    "可疑": 3,
    "可疑（只报不拦）": [
      "raw/src-933ff2bdf389/0036-conv-1916-vxxxv.txt　过短：1909 字节 < 2000——**确认这是不是一份完整的件**",
      "raw/src-48dc97b884d6/0043-conv-1917-vxxxvi.txt　过短：1861 字节 < 2000——**确认这是不是一份完整的件**",
      "raw/src-017cca837707/0049-conv-1917-vxxxvi.txt　过短：1854 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "**印本署名逐份实读，只读正文、不读抓源方写的表头。** 71/71 份一手全部取到 A-* 证据。证据形态五种，都是这类会刊的固定体例：\n① 讨论环节的发言标",
    "citation": "Transactions A.I.E.E. 卷 XXIII(1904)／XXVI(1907)／XXVII(1908)／XXVIII(1909)／XXIX(191",
    "争议篇目数": 5,
    "P1 声称本人所著": 71,
    "未挂 attribution": 0
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 71,
    "靠 A-* 署名证据认定": 71,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 69,
    "fact 类条数": 1,
    "**人物事实**（计入）": 1,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 14,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 1,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 1,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-cf49362d3d44 **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可核 `fact` 断言 1 条 < 要求 14 条（69 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因",
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 1 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 72,
    "含同形字的源": 0
  },
  "content_review": {
    "unexamined_band": {
      "n": 27,
      "of": 69,
      "files": [
        "0049-conv-1917-vxxxvi.txt",
        "0035-conv-1915-vxxxiv.txt",
        "0020-conv-1913-vxxxii.txt",
        "0001-conv-1907-vxxvi.txt",
        "0055-conv-1919-vxxxviii.txt",
        "0025-conv-1913-vxxxii.txt",
        "0033-conv-1915-vxxxiv.txt",
        "0026-conv-1913-vxxxii.txt"
      ]
    },
    "byline_in_carrier": "核过 0 条，指错 0 条",
    "fraktur_mojibake": "✓ 没有花体乱码",
    "staged_not_ingested": "✓ 台账与工作区一致（或本人物没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 5 条，切分后核验片段 5 个，未命中 1 个，长 s 还原后才命中 0 个｜⚠ 研究/06-timeline.md: 「COMMITTEE ON CODE OF PRINCIPLES OF PROFESSIONAL CONDUCT, C. A. Adams, Chairman」",
    "first_person_density": {
      "实质第一人称句": 78,
      "密度/万字": 1.76,
      "正文字符": 442402,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "own_voice": {
    "本人所著的 train 源数": 72,
    "train 源总数": 72,
    "本人所著字节": 624376,
    "train 总字节": 624376,
    "own_voice_ratio": 1.0,
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "拒答溢出条数": 0
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-adams-131/workspaces/comfort-avery-adams/evidence/source-ledger.jsonl",
    "一手份数": 69,
    "台账总份数": 69,
    "一手占比": 1.0,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "rights_basis": {
    "源条数": 72,
    "声称公有领域": 0,
    "不声称（不判）": 72,
    "有据可查": 0,
    "有结论无依据": 0,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": [
    "writings",
    "conversations",
    "expression",
    "timeline"
  ],
  "claims_total": 10,
  "claims_active": 10,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 5,
  "eval_cases": 0,
  "eval_suite_counts": {},
  "case_self_sufficiency": {
    "状态": "**没有用例可扫**——这不是通过"
  },
  "measurement_claims": {
    "已扫单元": 1,
    "实测声明": 0,
    "同段带数": 0,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0,
    "状态": "**一处实测声明都没扫到——本次什么也没检查，不构成通过。**合成阶段常态如此（断言层通常不写「我量过」），**但发布阶段若仍是 0，要去看是不是扫错了单元。**"
  },
  "evidence_per_claim": {
    "断言条数": 10,
    "source_ids": "逐条各异（非空 10/10，不同取值 8）",
    "evidence_clusters": "逐条各异（非空 10/10，不同取值 10）",
    "counter_source_ids": "整批都空（非空 0/10，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 7,
    "**全部来源塌缩成一部作品的**": 7,
    "作品组数": 11,
    "来源数": 72,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——两两 8 词片重叠 ≥30%（以较短一侧为分母）即判同一作品",
    "塌缩的断言": [
      "clm-4a82ee0802d6",
      "clm-cf49362d3d44",
      "clm-2d707170f214",
      "clm-43e881de3f26",
      "clm-996925d128e7",
      "clm-a16ba827261b",
      "clm-8d2fa4a5df2b"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-adams-131/workspaces/comfort-avery-adams/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     5.9%  persona.md             clm-4a82ee0802d6",
      "           **他会明说自己的感受是混合的，而不是把立场压成一边。** 评议 Steinmetz 论文时开口就是「I must confess to mixed feelings whic…",
      "",
      "低于 10% 的 9 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-adams-131/workspaces/comfort-avery-adams/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-adams-131/workspaces/comfort-avery-adams/audit/source-coverage.json），**未核验**（不是通过）"
  },
  "unqualified_priority": {
    "第一人称首创声明": 0,
    "其中带限定": 0,
    "扫了几个文件": 1,
    "状态": "一处首创声明都没扫到。**这可能是产物干净，也可能是判据窄**——v0.0.0.73 第一版就在真数据上报过一次假的 0。"
  },
  "sole_authorship": {
    "合著／集体署名的源": 2,
    "引用它们又用第一人称的段落": 0,
    "已划界": 0,
    "**独揽**": 0
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0
  }
}
```

## Errors

- `eval.suite-minimum`: known cases 0 < 1
- `eval.suite-minimum`: boundary cases 0 < 1
- `eval.suite-minimum`: voice cases 0 < 1
- `eval.suite-minimum`: trajectory cases 0 < 1
- `eval.suite-minimum`: contrast cases 0 < 1
- `eval.suite-minimum`: fact-preservation cases 0 < 1
- `eval.suite-minimum`: style-decoy cases 0 < 1
- `eval.suite-minimum`: task-completion cases 0 < 1
- `eval.suite-minimum`: planning-fidelity cases 0 < 1
- `eval.suite-minimum`: tool-use cases 0 < 1
- `eval.suite-minimum`: capability-calibration cases 0 < 1
- `eval.suite-minimum`: refusal-stop cases 0 < 1
- `eval.suite-minimum`: long-horizon cases 0 < 1
- `eval.suite-minimum`: identity-routing cases 0 < 1
- `eval.suite-minimum`: anonymous-fidelity cases 0 < 1
- `eval.suite-minimum`: token-efficiency cases 0 < 1

## Warnings

- `corpus.unexamined-band`: **27/69 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `claim.orphan`: active Claim clm-2d707170f214 is not rendered in any core artifact
- `claim.orphan`: active Claim clm-43e881de3f26 is not rendered in any core artifact
- `claim.orphan`: active Claim clm-996925d128e7 is not rendered in any core artifact
- `claim.orphan`: active Claim clm-a16ba827261b is not rendered in any core artifact
- `claim.orphan`: active Claim clm-8d2fa4a5df2b is not rendered in any core artifact
