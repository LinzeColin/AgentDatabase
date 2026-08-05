# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-coffin-130/workspaces/charles-l-coffin`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-05T00:27:37Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 18,
    "claims": 0
  },
  "sources_total": 18,
  "sources_train": 18,
  "sources_usable_train": 18,
  "sources_holdout": 0,
  "primary_sources": 15,
  "primary_ratio": 0.8333,
  "lane_source_counts": {
    "writings": 14,
    "conversations": 0,
    "expression": 0,
    "external": 3,
    "decisions": 0,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 14,
    "已证实归属": 13,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "1 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 18,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "**一手印本署名逐份实读，且只读正文、不读抓源方写的表头**。★ 头一遍我把抓源方自己写的 `INVENTOR:` 表头当成了文件的署名——**那是我的表头不是",
    "citation": "US Letters Patent 395,878(1888)／409,015(1889)／425,164(1890)／427,971(1890)／428,45",
    "争议篇目数": 2,
    "P1 声称本人所著": 14,
    "未挂 attribution": 0
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 14,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 14,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 18,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 5 条（18 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 18,
    "含同形字的源": 0
  },
  "content_review": {
    "unexamined_band": {
      "n": 1,
      "of": 18,
      "files": [
        "us395878-full-text.txt"
      ]
    },
    "byline_in_carrier": "核过 0 条，指错 0 条",
    "fraktur_mojibake": "✓ 没有花体乱码",
    "staged_not_ingested": "✓ 台账与工作区一致（或本人物没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档引文**未核成**（不是通过）：语料读不到，或一条引文都没扫到"
  },
  "own_voice": {
    "本人所著的 train 源数": 15,
    "train 源总数": 18,
    "本人所著字节": 177735,
    "train 总字节": 205831,
    "own_voice_ratio": 0.8635,
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "拒答溢出条数": 0
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-coffin-130/workspaces/charles-l-coffin/evidence/source-ledger.jsonl",
    "一手份数": 15,
    "台账总份数": 18,
    "一手占比": 0.8333,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "rights_basis": {
    "源条数": 18,
    "声称公有领域": 0,
    "不声称（不判）": 18,
    "有据可查": 0,
    "有结论无依据": 0,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": []
}
```

## Errors

- `research.source-unclaimed`: `src-52e85961f055` us428459-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-6157ba6c3857` us395878-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-f22b1b1fdc93` us425164-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-d683a8313aa7` us427971-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-018d9d707255` us409015-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-9919a602058c` us477101-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-b3c7d91167ad` us483427-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-51e690f6a614` us495393-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-9605f57b1d98` us495394-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-7a3ec62e6f8b` us442016-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-aa4a06cdd287` us646619-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-583443e78127` us845760-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-6b23440988de` us1216947-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-adcd1c8f0a50` us1265613-full-text.txt —— 声称 `Charles L. Coffin` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []

## Warnings

- `corpus.unexamined-band`: **1/18 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
