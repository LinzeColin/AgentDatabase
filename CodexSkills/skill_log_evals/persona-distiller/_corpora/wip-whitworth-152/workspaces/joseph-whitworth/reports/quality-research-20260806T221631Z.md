# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller/_corpora/wip-whitworth-152/workspaces/joseph-whitworth`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-06T22:16:31Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 9,
    "claims": 0
  },
  "sources_total": 9,
  "sources_train": 9,
  "sources_usable_train": 7,
  "sources_holdout": 0,
  "primary_sources": 7,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 7,
    "conversations": 0,
    "expression": 0,
    "external": 0,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 6,
    "已证实归属": 4
  },
  "corpus_integrity": {
    "已扫": 9,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/src-86fb98d51ecf/gb-1855-903-whitworth_djvu.txt　过短：125 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "P1 声称本人所著": 6,
    "未挂 attribution": 0
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 6,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 6,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 7,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 5 条（7 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 9,
    "含同形字的源": 0
  },
  "content_review": {
    "byline_in_carrier": "核过 0 条，指错 0 条",
    "fraktur_mojibake": "✓ 没有花体乱码",
    "staged_not_ingested": "✓ 台账与工作区一致（或本人物没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档引文**未核成**（不是通过）：语料读不到，或一条引文都没扫到",
    "first_person_density": {
      "实质第一人称句": 428,
      "密度/万字": 3.2,
      "正文字符": 1337124,
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
    "状态": "本人物没有定制判据——**不适用**（不是通过）",
    "★": "「名+姓」够不够，取决于这个人物有没有同名近亲。**每个人物都要单测一次。**"
  },
  "lane_quotes": {
    "逐道": {
      "01-writings.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "04-external.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "05-decisions.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "06-timeline.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      }
    },
    "合计": "0 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.9965,
      "第三人称": 0.0,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0035,
      "已标的份数": 7,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 9,
    "train 源总数": 9,
    "本人所著字节": 1460772,
    "train 总字节": 1460772,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 1233670,
    "第一人称（动词式）/万字": 6.75,
    "**立场句/万字**": 0.21,
    "其中不含第一人称的": 18,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 6,
    "**疑似著录卡**": {},
    "读不到正文的": [],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "状态": "**未核验**（不是通过）——没有可用的 --cache，取不到语料原文"
  },
  "semantic_residue": {
    "状态": "未启用（0 条订正全是非 content 域，取不到规则）——**不是通过**",
    "★": "全库回查：唯一有内容的订正是 Bessemer #132 的 2 条，scope 都是 `evaluation`。**这判据找的输入从来没出现过。**"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "拒答溢出条数": 0
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller/_corpora/wip-whitworth-152/workspaces/joseph-whitworth/evidence/source-ledger.jsonl",
    "一手份数": 7,
    "台账总份数": 7,
    "一手占比": 1.0,
    "有材料的道数": 1,
    "quick 要的一手份数": 4,
    "够得着吗": "够不着：份数 7 < 8——**材料本身就不够**；六条道只占 1 < 3——**空着的道抓再多别的也补不上**"
  },
  "rights_basis": {
    "源条数": 9,
    "声称公有领域": 9,
    "不声称（不判）": 0,
    "有据可查": 0,
    "有结论无依据": 9,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": []
}
```

## Errors

- `source.minimum`: usable train sources 7 < profile minimum 8
- `source.lane-coverage`: source metadata covers 1 lanes < profile minimum 3: ['writings']
- `research.authorship-unproven`: src-d70bdcbfcc85 miscellaneouspa00whitgoog_djvu.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-f801c53b936e wikisource_miscellaneous_papers_1858.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.attribution-basis`: historical 人物未声明 attribution_basis —— **必须写明靠什么证明这是他写的**。前印刷时代人物：A-byline 等五种署名证据结构上不存在，须另找权威（如作者自著目录）；印刷时代人物：扉页与印工可用，但**须写明哪些版次／托名件不算**
- `research.source-unclaimed`: `src-dcb590c32cf4` miscellaneouspa03whitgoog_djvu.txt —— 声称 `Joseph Whitworth` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-d70bdcbfcc85` miscellaneouspa00whitgoog_djvu.txt —— 声称 `Joseph Whitworth` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-f801c53b936e` wikisource_miscellaneous_papers_1858.txt —— 声称 `Joseph Whitworth` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-548b27e71548` miscellaneouspa01whitgoog_djvu.txt —— 声称 `Joseph Whitworth` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-7a88f8465ab7` miscellaneouspa02whitgoog_djvu.txt —— 声称 `Joseph Whitworth` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-28dfa1d4651c` jstor-41334745_djvu.txt —— 声称 `Joseph Whitworth` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []

## Warnings

- None
