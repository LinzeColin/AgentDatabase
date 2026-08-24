# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-24T03:54:50Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 17,
    "claims": 0
  },
  "sources_total": 17,
  "sources_train": 17,
  "sources_usable_train": 17,
  "sources_holdout": 0,
  "primary_sources": 17,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 11,
    "conversations": 2,
    "expression": 4,
    "external": 0,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 17,
    "已证实归属": 8,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "9 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 17,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Jean-Baptiste Say（1767-1832）著作归属依据：① archive.org 目录 creator 字段（Say, Jean Baptist",
    "citation": "archive.org 目录检索 creator:\"Say, Jean Baptiste\" / creator:\"Say, Jean-Baptiste\"（num",
    "争议篇目数": 0,
    "P1 声称本人所著": 0,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "skip",
    "说明": "**找不到同名候选名单——不适用，不是通过**",
    "候选数": 0,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": []
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
    "usable_train": 17,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 5 条（17 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 17,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 5,
      "不适用": 12
    },
    "逐份": {
      "src-f7154d6be8dd": {
        "words": 27041,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2292.8,
            "panel_good": 305,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 305／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 305／讹形 0）",
        "file": "catechismofpolit00sayj.txt"
      },
      "src-d9920ebbab87": {
        "words": 34468,
        "diagnostic_est_eft": [
          427,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0117；英文：锚 4.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.5000）",
        "file": "b29287571.txt"
      },
      "src-003d387aca63": {
        "words": 131322,
        "diagnostic_est_eft": [
          1598,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0227；英文：锚 3.1<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.3529）",
        "file": "bub_gb_N7JDAAAAcAAJ.txt"
      },
      "src-8249fec8789a": {
        "words": 678478,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0038；英文：锚 2.2<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.0681）",
        "file": "bub_gb_nGt2dzHrtIMC.txt"
      },
      "src-1695e00c1f47": {
        "words": 63102,
        "diagnostic_est_eft": [
          1013,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0029；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.1429）",
        "file": "catchismedco00sayj.txt"
      },
      "src-cb25bd63b578": {
        "words": 643917,
        "diagnostic_est_eft": [
          8052,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0006；英文：锚 2.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1333）",
        "file": "courscompletdc00sayjuoft.txt"
      },
      "src-68e157418b30": {
        "words": 130399,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 411.2,
            "panel_good": 2810,
            "panel_bad": 11,
            "若无语种门会读到": 0.0039,
            "verdict": "干净",
            "rate": 0.0039,
            "reason": "德语讹字率 0.0039（正形 2810／讹形 11）"
          }
        },
        "德语附加": {
          "h→b率": 0.0179,
          "h→b样本": 2295,
          "变音符每千词": 61.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0039,
        "reason": "德语讹字率 0.0039（正形 2810／讹形 11）",
        "file": "darstellungdern00morsgoog.txt"
      },
      "src-b1935dc2cb56": {
        "words": 94188,
        "diagnostic_est_eft": [
          998,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0290；英文：锚 3.8<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.1667）",
        "file": "india.history.resource.35409.txt"
      },
      "src-0d7cfabc38d1": {
        "words": 56287,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2325.4,
            "panel_good": 602,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 602／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 602／讹形 0）",
        "file": "letterstomrmalth00sayjrich.txt"
      },
      "src-7309a76950f4": {
        "words": 26871,
        "diagnostic_est_eft": [
          248,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.0133；英文：锚 4.1<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.0000）",
        "file": "micro_IA40244320_0069.txt"
      },
      "src-4f99e70027da": {
        "words": 371204,
        "diagnostic_est_eft": [
          3899,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0079；英文：锚 5.7<500.0，若强行读 0.1176；德语：锚 0.1<15.0，若强行读 0.4118）",
        "file": "oeuvresdiverses00saygoog.txt"
      },
      "src-cfbc1f979683": {
        "words": 27940,
        "diagnostic_est_eft": [
          287,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 3.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2000）",
        "file": "olbieouessaisurl00sayj.txt"
      },
      "src-b68240fb3bd9": {
        "words": 27766,
        "diagnostic_est_eft": [
          499,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0058；英文：锚 1.8<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.1111）",
        "file": "petitvolumeconte00sayj.txt"
      },
      "src-9ac3add24ba1": {
        "words": 316291,
        "diagnostic_est_eft": [
          3984,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0089；英文：锚 4.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2308）",
        "file": "traitedeconomie00saygoog.txt"
      },
      "src-342c06541c14": {
        "words": 103128,
        "diagnostic_est_eft": [
          140,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0053；英文：锚 14.4<500.0，若强行读 0.0000；德语：锚 6.8<15.0，若强行读 0.0889）",
        "file": "tratadodeeconom01sayjguat.txt"
      },
      "src-a9248c41ada4": {
        "words": 258508,
        "diagnostic_est_eft": [
          15,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2449.1,
            "panel_good": 2049,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2049／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2049／讹形 0）",
        "file": "treatiseonpoliti00sayj.txt"
      },
      "src-47686e48abd4": {
        "words": 135493,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2414.4,
            "panel_good": 1008,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1008／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1008／讹形 0）",
        "file": "treatiseonpoliti01sayjuoft.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 17,
    "与台账不一致的道": [
      "02-conversations.md",
      "03-expression.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "核过 17 条，指错 0 条，**没核 18 条（不是通过）**",
    "fraktur_mojibake": "1 份",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档里**一条引文都没扫到**——没有可核的对象（不是通过）",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 81484812,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 0,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 0,
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
    "可用来源": 17,
    "**按内容去重后的作品数**": 15,
    "虚高": 1.133,
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
    "holdout 源数": 0,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 17,
    "train 源总数": 17,
    "本人所著字节": 20365440,
    "train 总字节": 20365440,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 3232109,
    "**判据说未核验的**": 13,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-d9920ebbab87",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.102）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-003d387aca63",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.090）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8249fec8789a",
        "原因": "语种判为 **?**（en=0.000 de=0.001 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-1695e00c1f47",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.108）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-cb25bd63b578",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.106）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-68e157418b30",
        "原因": "语种判为 **de**（en=0.004 de=0.111 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b1935dc2cb56",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.097）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-7309a76950f4",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.093）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 5.1,
    "**立场句/万字**": 0.12,
    "其中不含第一人称的": 35,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 17,
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
    "已扫答案": 0,
    "拒答溢出候选": 0
  },
  "baseline_in_persona": {
    "状态": "**没找到对照臂载荷——未核验，不是通过**（判分前应已有 `evals/baseline.v1.json`）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say/evidence/source-ledger.jsonl",
    "一手份数": 17,
    "台账总份数": 17,
    "一手占比": 1.0,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 17,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-f7154d6be8dd 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 17,
    "声称公有领域": 0,
    "不声称（不判）": 17,
    "有据可查": 0,
    "有结论无依据": 0,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": [],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 17,
    "**`title` 就是文件名**": 0,
    "真书目题名": 17,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 17,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 2,
    "**硬失败**": 1,
    "其中·真重合": 0,
    "其中·无法判定": 1,
    "**逐条**": [
      "✗ 账本里没有 holdout —— 无法判定"
    ],
    "未核口径": "定位不到 holdout 的正文 ⇒ **这道门没能跑起来**，既不是「有重合」也不是「没重合」。语料正文不进 git，在没有语料缓存的机器上这是预期结果——给 `--cache <语料目录>` 才核得成。"
  }
}
```

## Errors

- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []
- `corpus.holdout-unverifiable`: holdout 与 train 的重合**未能核验**（1 条定位不到正文）——**未核不等于通过，也不等于有重合**；给 `--cache <语料目录>` 重跑。逐条见 metrics.holdout_overlap

## Warnings

- `corpus.fraktur-mojibake`: **1 份德文语料是花体 OCR 乱码**——der→ber、und→unb、ist→ift，整篇没有一个词能拿去检索或引用。份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。
