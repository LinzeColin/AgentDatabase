# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roberts-austen-135/workspaces/william-chandler-roberts-austen`
- Phase: `research`
- Profile: `standard`
- Generated: `2026-08-05T23:03:43Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 26,
    "claims": 0
  },
  "sources_total": 26,
  "sources_train": 26,
  "sources_usable_train": 26,
  "sources_holdout": 0,
  "primary_sources": 25,
  "primary_ratio": 0.9615,
  "lane_source_counts": {
    "writings": 13,
    "conversations": 3,
    "expression": 7,
    "external": 1,
    "decisions": 1,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 24,
    "已证实归属": 2
  },
  "corpus_integrity": {
    "已扫": 26,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/src-5891eaf328db/letter00robe.txt　过短：1244 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "P1 声称本人所著": 24,
    "未挂 attribution": 0
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 16,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 16,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 26,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 6,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 6 条（26 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 26,
    "含同形字的源": 0
  },
  "content_review": {
    "unexamined_band": {
      "n": 1,
      "of": 26,
      "files": [
        "letter00robe.txt"
      ]
    },
    "byline_in_carrier": "核过 0 条，指错 0 条",
    "fraktur_mojibake": "✓ 没有花体乱码",
    "staged_not_ingested": "✓ 台账与工作区一致（或本人物没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档引文**未核成**（不是通过）：语料读不到，或一条引文都没扫到",
    "first_person_density": {
      "实质第一人称句": 488,
      "密度/万字": 1.82,
      "正文字符": 2687760,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "material_split": {
    "返回码": 0,
    "**holdout 泄漏处**": 0
  },
  "threshold_doc_drift": {
    "返回码": 0,
    "**不一致处**": 0
  },
  "verdict_attribution": {
    "**归属错**": 0
  },
  "rubric_health": {
    "状态": "没有 cases/答案，**未核验**（不是通过）"
  },
  "namesake_criteria": {
    "**unknown 条数**": 0,
    "逐条": [
      "william-chandler-roberts-austen：目标本人 26　他人 0　**unknown 0**"
    ]
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.6644,
      "第三人称": 0.0021,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.3335,
      "已标的份数": 13,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 25,
    "train 源总数": 26,
    "本人所著字节": 2866821,
    "train 总字节": 2872737,
    "own_voice_ratio": 0.9979,
    "★ 同名判据": {
      "按判据剔除的（他人）": [],
      "**说不准的（unknown，未计入本人声口）**": [],
      "口径": "只比姓氏会把同姓近亲算进来。Sorby #133 的父亲也叫 Henry Sorby，父亲的日记同在馆藏里。**unknown 一律不计入——宁可低报，不可高报。**"
    },
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "拒答溢出条数": 0
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roberts-austen-135/workspaces/william-chandler-roberts-austen/evidence/source-ledger.jsonl",
    "一手份数": 25,
    "台账总份数": 26,
    "一手占比": 0.9615,
    "有材料的道数": 6,
    "standard 要的一手份数": 12,
    "够得着吗": "吃全部材料就够得着"
  },
  "rights_basis": {
    "源条数": 26,
    "声称公有领域": 26,
    "不声称（不判）": 0,
    "有据可查": 9,
    "有结论无依据": 17,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": []
}
```

## Errors

- `research.authorship-unproven`: src-a16660d41422 philtrans00412410.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-3a7b624f0324 philtrans07401700.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-11156663a5e4 philtrans05512448.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-4ae0892cbde8 philtrans09730582.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-60539abbb73b philtrans05894557.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-fff1b6898cd1 philtrans00706421.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-baf16940309f philtrans04290113.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-2ebdf104a176 philtrans01205368.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-accdb5e0821f philtrans09607756.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-42286afc9366 philtrans08066202.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-4b50569ba761 paper-doi-10_1038_015153a0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-567238c2ad76 paper-doi-10_1038_020587b0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-6f608ad2e089 paper-doi-10_1038_021272a0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-b63e790a63d6 paper-doi-10_1038_041420a0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-ff6f30e8b7e9 paper-doi-10_1038_043388a0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-851b1f460f29 paper-doi-10_1038_044245a0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-4df10147b875 paper-doi-10_1038_052367a0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-4b34c9929162 paper-doi-10_1038_054055c0.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-d563a762c431 cantorlectureso00robegoog.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-06496f1d3bc2 canadasmetalsal00robegoog.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-8268c67b4de9 intrometallurgy00roberich.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-5891eaf328db letter00robe.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.attribution-basis`: historical 人物未声明 attribution_basis —— **必须写明靠什么证明这是他写的**。前印刷时代人物：A-byline 等五种署名证据结构上不存在，须另找权威（如作者自著目录）；印刷时代人物：扉页与印工可用，但**须写明哪些版次／托名件不算**
- `research.source-unclaimed`: `src-a16660d41422` philtrans00412410.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-827f6033da2f` philtrans00429265.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-3a7b624f0324` philtrans07401700.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-11156663a5e4` philtrans05512448.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-4ae0892cbde8` philtrans09730582.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-baf16940309f` philtrans04290113.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-2ebdf104a176` philtrans01205368.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-b63e790a63d6` paper-doi-10_1038_041420a0.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-ff6f30e8b7e9` paper-doi-10_1038_043388a0.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-851b1f460f29` paper-doi-10_1038_044245a0.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-4df10147b875` paper-doi-10_1038_052367a0.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-4b34c9929162` paper-doi-10_1038_054055c0.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-366fbd20fc5a` paper-doi-10_1038_060173c0.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-06496f1d3bc2` canadasmetalsal00robegoog.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-8268c67b4de9` intrometallurgy00roberich.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-5891eaf328db` letter00robe.txt —— 声称 `William Chandler Roberts-Austen` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 6: []

## Warnings

- `corpus.unexamined-band`: **1/26 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
