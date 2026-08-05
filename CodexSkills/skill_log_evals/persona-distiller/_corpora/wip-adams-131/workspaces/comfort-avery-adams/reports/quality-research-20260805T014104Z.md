# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-adams-131/workspaces/comfort-avery-adams`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-05T01:41:04Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 72,
    "claims": 0
  },
  "sources_total": 72,
  "sources_train": 72,
  "sources_usable_train": 72,
  "sources_holdout": 0,
  "primary_sources": 72,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 6,
    "conversations": 63,
    "expression": 2,
    "external": 0,
    "decisions": 0,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 71,
    "已证实归属": 65
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
    "P1 声称本人所著": 71,
    "未挂 attribution": 0
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 71,
    "靠 A-* 署名证据认定": 65,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 6,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 72,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 15,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 15 条（72 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
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
      "of": 72,
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
    "research_quote": "研究文档引文**未核成**（不是通过）：语料读不到，或一条引文都没扫到",
    "first_person_density": {
      "实质第一人称句": 81,
      "密度/万字": 1.68,
      "正文字符": 481305,
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
    "一手份数": 72,
    "台账总份数": 72,
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
  "research_lanes_complete": []
}
```

## Errors

- `research.authorship-unproven`: src-16dfd1adf2b5 0001-conv-1907-vxxvi.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-933ff2bdf389 0036-conv-1916-vxxxv.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-73dd58f902fe 0042-conv-1916-vxxxv.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-88db6ad14325 0051-conv-1918-vxxxvii.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-7f0517874d99 0062-conv-1921-vxl.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-360436b143b3 0063-conv-1904-repulsion-motor-jr.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.attribution-basis`: historical 人物未声明 attribution_basis —— **必须写明靠什么证明这是他写的**。前印刷时代人物：A-byline 等五种署名证据结构上不存在，须另找权威（如作者自著目录）；印刷时代人物：扉页与印工可用，但**须写明哪些版次／托名件不算**
- `research.source-unclaimed`: `src-16dfd1adf2b5` 0001-conv-1907-vxxvi.txt —— 声称 `Comfort Avery Adams` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-933ff2bdf389` 0036-conv-1916-vxxxv.txt —— 声称 `Comfort Avery Adams` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-73dd58f902fe` 0042-conv-1916-vxxxv.txt —— 声称 `Comfort Avery Adams` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-88db6ad14325` 0051-conv-1918-vxxxvii.txt —— 声称 `Comfort Avery Adams` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-7f0517874d99` 0062-conv-1921-vxl.txt —— 声称 `Comfort Avery Adams` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-360436b143b3` 0063-conv-1904-repulsion-motor-jr.txt —— 声称 `Comfort Avery Adams` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []

## Warnings

- `corpus.unexamined-band`: **27/72 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
