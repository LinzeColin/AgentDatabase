# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/navier`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-21T21:30:43Z`
- Result: **PASS**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 9,
    "claims": 0
  },
  "sources_total": 9,
  "sources_train": 8,
  "sources_usable_train": 8,
  "sources_holdout": 1,
  "primary_sources": 8,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 5,
    "conversations": 2,
    "expression": 0,
    "external": 0,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 9,
    "已证实归属": 0,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "9 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 9,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Claude-Louis Navier 著作归属依据：① 法国科学院（Académie royale des Sciences）1824 年选其为院士；② Éc",
    "citation": "archive.org 目录 creator 字段 + 各书题名页/署名行；出版记录见各源 locator。",
    "争议篇目数": 0,
    "P1 声称本人所著": 9,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/navier/namesake-candidates.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 0,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 8,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 5 条（8 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 9,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "不适用": 8,
      "干净": 1
    },
    "逐份": {
      "src-4b7ed8ad4371": {
        "words": 124209,
        "diagnostic_est_eft": [
          1285,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0028；英文：锚 8.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.3846）",
        "file": "bub_gb_PNg3AAAAMAAJ.txt"
      },
      "src-e8d0c52b9b5c": {
        "words": 122507,
        "diagnostic_est_eft": [
          1240,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0270；英文：锚 11.8<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.4194）",
        "file": "rsumdesleonsdem00navigoog.txt"
      },
      "src-2ac1e1efe482": {
        "words": 151832,
        "diagnostic_est_eft": [
          1585,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0104；英文：锚 1.9<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.4000）",
        "file": "bub_gb_9G84AAAAMAAJ.txt"
      },
      "src-cbd6d1274c49": {
        "words": 117908,
        "diagnostic_est_eft": [
          1222,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0097；英文：锚 3.8<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.5000）",
        "file": "rapportmonsieurb00navi.txt"
      },
      "src-2cf5fe26f051": {
        "words": 92190,
        "diagnostic_est_eft": [
          820,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0531；英文：锚 14.5<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.2727）",
        "file": "considrationssu00margoog.txt"
      },
      "src-83dbfc1ebade": {
        "words": 4535,
        "diagnostic_est_eft": [
          41,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 6.6<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "notesurlemouveme00navi.txt"
      },
      "src-11c8beafdc2c": {
        "words": 22359,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2666.5,
            "panel_good": 223,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 223／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 223／讹形 0）",
        "file": "onmeansofcompari00navirich.txt"
      },
      "src-b430f904cdde": {
        "words": 8247,
        "diagnostic_est_eft": [
          97,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 106.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "examendelatonti00navigoog.txt"
      },
      "src-2561a7dd3e35": {
        "words": 30044,
        "diagnostic_est_eft": [
          198,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "bub_gb_RzQyKRVPdusC.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 9,
    "与台账不一致的道": [
      "02-conversations.md",
      "05-decisions.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "核过 9 条，指错 0 条",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 9 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 60 条，切分后核验片段 61 个，未命中 22 个，长 s 还原后才命中 0 个｜⚠ 研究/01-writings.md: 「La plupart des constructeurs déterminent les dimensions des parties des édifices ou des machines d'a」｜⚠ 研究/01-writings.md: 「Parmi ces conditions, l'une des plus essentielles est l'économie; la solidité et la durée ne sont pa」｜⚠ 研究/01-writings.md: 「Ainsi la résistance à la flexion est proportionnelle à la largeur et au cube de la hauteur du solide」｜⚠ 研究/01-writings.md: 「la valeur du travail des chevaux formant toujours à elle seule la partie principale du prix du trans」｜⚠ 研究/01-writings.md: 「Cette recherche est une application du calcul des probabilités , qu'il m'a paru convenable de faire 」｜⚠ 研究/01-writings.md: 「Complètement étranger, par ma situation particulière et par la nature de mes occupations, à toute sp」",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 7808931,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 61,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 24,
    "★★ 射程": "只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语"
  },
  "holdout_mention": {
    "字面提及": 0,
    "**其中点名了是哪一份的**": 0,
    "★ 只是泛泛提及（不说哪一份）": 0,
    "与 holdout 正文重叠": 0,
    "★ 与出厂模板逐字相同、已豁免": 12,
    "★★ 射程": "抓不到「不提 holdout 也不抄它、却把题目描述出来」的写法——那一类只能靠人读或答题方主动上报"
  },
  "source_numbering_gap": {
    "编号缺口": 0,
    "其中确认型": 0,
    "其中疑似（组内首字母不是 a）": 0,
    "★ 缺口上正好是 holdout 的": 0,
    "★★ 射程": "只看文件名；**尾部被整份拿走的缺口抓不到**；补齐编号也堵不住「份数本身是信息」那一层",
    "★ 文件名不带顺序前缀": "本件对这个工作区**看不见任何东西**（不是通过）",
    "★ holdout 文件名不带前缀": "**判不出缺口是不是它留下的**"
  },
  "source_dedup": {
    "可用来源": 8,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.0,
    "未声明的重复对": 0,
    "已声明的重复对": 0,
    "★ 本件看不见的份数（文本太短／中日韩，不是已核）": 0
  },
  "material_split": {
    "返回码": 2,
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
    "状态": "**答案尚未产出——本轮只验了 rubric**（不是全部核验）",
    "判据条数": 0,
    "**判据要求出戏的**": {},
    "★ 口径": "**只报不拦**：改不改由人定。但它现在**在答案写出来之前**说话，而不是等到派发前才说——那时答案已经是照着这条 rubric 写的了。"
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
    "holdout 源数": 1,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 9,
    "train 源总数": 9,
    "本人所著字节": 4185745,
    "train 总字节": 4185745,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 152574,
    "**判据说未核验的**": 8,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-4b7ed8ad4371",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.094）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-e8d0c52b9b5c",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.094）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-2ac1e1efe482",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.092）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-cbd6d1274c49",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.107）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-2cf5fe26f051",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.094）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-83dbfc1ebade",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.094）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b430f904cdde",
        "原因": "语种判为 **fr**（en=0.009 de=0.000 fr=0.072）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-2561a7dd3e35",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.101）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 15.01,
    "**立场句/万字**": 0.07,
    "其中不含第一人称的": 1,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 9,
    "**疑似著录卡**": {},
    "读不到正文的": [],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "逐字英文引文": 0,
    "**未命中**": 0,
    "跨版口命中（引文为真）": 0,
    "未命中样例": [],
    "跨版口样例": []
  },
  "semantic_residue": {
    "状态": "未启用（0 条订正全是非 content 域，取不到规则）——**不是通过**",
    "★": "全库回查：唯一有内容的订正是 Bessemer #132 的 2 条，scope 都是 `evaluation`。**这判据找的输入从来没出现过。**"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "已扫答案": 0,
    "拒答溢出候选": 0
  },
  "baseline_in_persona": {
    "状态": "**没找到对照臂载荷——未核验，不是通过**（判分前应已有 `evals/baseline.v1.json`）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/navier/evidence/source-ledger.jsonl",
    "一手份数": 8,
    "台账总份数": 8,
    "一手占比": 1.0,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 9,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-4b7ed8ad4371 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 9,
    "声称公有领域": 0,
    "不声称（不判）": 9,
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
    "decisions"
  ],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 9,
    "**`title` 就是文件名**": 0,
    "真书目题名": 9,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 9,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  }
}
```

## Errors

- None

## Warnings

- None
