# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-andrea-palladio-147/andrea-palladio`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-24T00:19:39Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 41,
    "claims": 0
  },
  "sources_total": 41,
  "sources_train": 35,
  "sources_usable_train": 35,
  "sources_holdout": 6,
  "primary_sources": 32,
  "primary_ratio": 0.9143,
  "lane_source_counts": {
    "writings": 32,
    "conversations": 0,
    "expression": 0,
    "external": 2,
    "decisions": 0,
    "timeline": 2
  },
  "authorship": {
    "P1 声称为本人所著": 38,
    "已证实归属": 29,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "9 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 41,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Andrea Palladio（1508-1580）著作归属依据：① 其亲撰《I Quattro Libri dell'Architettura》（威尼斯 15",
    "citation": "archive.org 目录 creator 字段（Palladio, Andrea, 1508-1580 / Andrea Palladio / Andrea",
    "争议篇目数": 0,
    "P1 声称本人所著": 38,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-andrea-palladio-147/namesake-candidates.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 2,
    "靠 A-* 署名证据认定": 1,
    "靠 attribution_basis 逐份点名认定": 1,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 35,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 7,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 7 条（35 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 41,
    "含同形字的源": 3,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "bim_eighteenth-century_quattro-libri-dell-arc_palladio-andrea_1735.txt",
        "非拉丁字符": 28,
        "全同形字词": 0,
        "样例": [
          "ἈↄZr 读作 ἈↄZr",
          "Æ⁵α 读作 Æ⁵α",
          "ανihανν 读作 αvihαvv"
        ]
      },
      {
        "源": "bim_eighteenth-century_the-architecture-of-a-p_palladio-andrea_1721_2.txt",
        "非拉丁字符": 2,
        "全同形字词": 0,
        "样例": [
          "F⁵QNνVQ 读作 F⁵QNvVQ"
        ]
      },
      {
        "源": "bim_eighteenth-century_the-first-book-of-archit_palladio-andrea_1729.txt",
        "非拉丁字符": 9,
        "全同形字词": 1,
        "样例": [
          "ο 读作 o"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不适用": 23,
      "干净": 1,
      "不可用": 13,
      "未核": 4
    },
    "逐份": {
      "src-df8f1e0dfc8b": {
        "words": 31202,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.1382；英文：锚 14.4<500.0，若强行读 0.0000；德语：锚 0.6<15.0，若强行读 0.1860）",
        "file": "CHEPFL_LIPR_AXB223_4.txt"
      },
      "src-9f9be271978d": {
        "words": 6730,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 8.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "andreapalladio00gurl.txt"
      },
      "src-65b5a3cada5e": {
        "words": 39259,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2269.3,
            "panel_good": 376,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 376／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 376／讹形 0）",
        "file": "andreapalladioh00flet.txt"
      },
      "src-2458ace11749": {
        "words": 82508,
        "diagnostic_est_eft": [
          0,
          5
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2449.9,
            "panel_good": 15,
            "panel_bad": 908,
            "若无语种门会读到": 0.9837,
            "verdict": "不可用",
            "rate": 0.9837,
            "reason": "英文讹字率 0.9837（正形 15／讹形 908）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9837,
        "reason": "英文讹字率 0.9837（正形 15／讹形 908）",
        "file": "andreapalladiosa00pall.txt"
      },
      "src-6e344b2920a4": {
        "words": 23040,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2499.1,
            "panel_good": 0,
            "panel_bad": 293,
            "若无语种门会读到": 1.0,
            "verdict": "不可用",
            "rate": 1.0,
            "reason": "英文讹字率 1.0000（正形 0／讹形 293）"
          }
        },
        "verdict": "不可用",
        "rate": 1.0,
        "reason": "英文讹字率 1.0000（正形 0／讹形 293）",
        "file": "andreapalladiosf00pall.txt"
      },
      "src-f73d82dc0899": {
        "words": 229456,
        "diagnostic_est_eft": [
          3,
          700
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 900.0,
            "panel_good": 9,
            "panel_bad": 1003,
            "若无语种门会读到": 0.9911,
            "verdict": "不可用",
            "rate": 0.9911,
            "reason": "英文讹字率 0.9911（正形 9／讹形 1003）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9911,
        "reason": "英文讹字率 0.9911（正形 9／讹形 1003）",
        "file": "architecturePal00Pall.txt"
      },
      "src-f12e8de5838d": {
        "words": 40946,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2478.9,
            "panel_good": 6,
            "panel_bad": 371,
            "若无语种门会读到": 0.9841,
            "verdict": "不可用",
            "rate": 0.9841,
            "reason": "英文讹字率 0.9841（正形 6／讹形 371）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9841,
        "reason": "英文讹字率 0.9841（正形 6／讹形 371）",
        "file": "architectureofap0001pall.txt"
      },
      "src-d6d473ec76f6": {
        "words": 39162,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2421.7,
            "panel_good": 4,
            "panel_bad": 385,
            "若无语种门会读到": 0.9897,
            "verdict": "不可用",
            "rate": 0.9897,
            "reason": "英文讹字率 0.9897（正形 4／讹形 385）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9897,
        "reason": "英文讹字率 0.9897（正形 4／讹形 385）",
        "file": "architectureofapvol2pall.txt"
      },
      "src-ea04367ec274": {
        "words": 27674,
        "diagnostic_est_eft": [
          0,
          126
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.7<15.0，若强行读 0.9247；英文：锚 5.4<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.9545）",
        "file": "bertotti-le-terme-dei-romani-1785.txt"
      },
      "src-43994d593227": {
        "words": 28498,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2436.0,
            "panel_good": 1,
            "panel_bad": 15,
            "若无语种门会读到": 0.9375,
            "verdict": "未核",
            "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_early-english-books-1641-1700_the-first-book-of-archit_palladio-andrea_1668.txt"
      },
      "src-2ab7b096fb06": {
        "words": 124794,
        "diagnostic_est_eft": [
          8,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1636.1,
            "panel_good": 13,
            "panel_bad": 15,
            "若无语种门会读到": 0.5357,
            "verdict": "未核",
            "reason": "英文面板只命中 28 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 28 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_quattro-libri-dell-arc_palladio-andrea_1735.txt"
      },
      "src-b2d74fe2ffd3": {
        "words": 52466,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1931.3,
            "panel_good": 6,
            "panel_bad": 10,
            "若无语种门会读到": 0.625,
            "verdict": "未核",
            "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_the-architecture-of-a-p_palladio-andrea_1721_2.txt"
      },
      "src-fbcf8a5c1b35": {
        "words": 29066,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2315.1,
            "panel_good": 3,
            "panel_bad": 17,
            "若无语种门会读到": 0.85,
            "verdict": "未核",
            "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_the-first-book-of-archit_palladio-andrea_1729.txt"
      },
      "src-8c30a5dc3c19": {
        "words": 26334,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2581.8,
            "panel_good": 2,
            "panel_bad": 223,
            "若无语种门会读到": 0.9911,
            "verdict": "不可用",
            "rate": 0.9911,
            "reason": "英文讹字率 0.9911（正形 2／讹形 223）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9911,
        "reason": "英文讹字率 0.9911（正形 2／讹形 223）",
        "file": "bookofarchitectu00pall.txt"
      },
      "src-db6919652a18": {
        "words": 305947,
        "diagnostic_est_eft": [
          1,
          3
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8744；英文：锚 22.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.9097）",
        "file": "bub_gb_ahhUAAAAcAAJ.txt"
      },
      "src-a8064aa6be0c": {
        "words": 16459,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.6250；英文：锚 10.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "bub_gb_ktETgRIYzBUC.txt"
      },
      "src-117866e8800c": {
        "words": 17655,
        "diagnostic_est_eft": [
          0,
          129
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 1.0000；英文：锚 4.0<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "bub_gb_ujAa4--Tc7gC.txt"
      },
      "src-82bce713201a": {
        "words": 6275,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.4000；英文：锚 35.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "cinqueordinidiar00pall.txt"
      },
      "src-22850333186c": {
        "words": 64385,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 3.6<15.0，若强行读 0.0056；英文：锚 5.3<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.1852）",
        "file": "dellavitaedelle00scol.txt"
      },
      "src-f88f4081ca9f": {
        "words": 26482,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2167.9,
            "panel_good": 1,
            "panel_bad": 136,
            "若无语种门会读到": 0.9927,
            "verdict": "不可用",
            "rate": 0.9927,
            "reason": "英文讹字率 0.9927（正形 1／讹形 136）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9927,
        "reason": "英文讹字率 0.9927（正形 1／讹形 136）",
        "file": "firstbookofarchi0000pall.txt"
      },
      "src-6e2e616ffd1e": {
        "words": 26972,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2514.5,
            "panel_good": 2,
            "panel_bad": 242,
            "若无语种门会读到": 0.9918,
            "verdict": "不可用",
            "rate": 0.9918,
            "reason": "英文讹字率 0.9918（正形 2／讹形 242）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9918,
        "reason": "英文讹字率 0.9918（正形 2／讹形 242）",
        "file": "firstbookofarchi00pall.txt"
      },
      "src-b6cc7eeeb974": {
        "words": 62947,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.9226；英文：锚 13.5<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 1.0000）",
        "file": "gri_33125006448050.txt"
      },
      "src-47508680be5d": {
        "words": 90491,
        "diagnostic_est_eft": [
          0,
          43
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.9443；英文：锚 12.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.9350）",
        "file": "gri_33125008638575.txt"
      },
      "src-56047aa2b2bd": {
        "words": 63433,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2568.1,
            "panel_good": 19,
            "panel_bad": 742,
            "若无语种门会读到": 0.975,
            "verdict": "不可用",
            "rate": 0.975,
            "reason": "英文讹字率 0.9750（正形 19／讹形 742）"
          }
        },
        "verdict": "不可用",
        "rate": 0.975,
        "reason": "英文讹字率 0.9750（正形 19／讹形 742）",
        "file": "gri_33125008860922.txt"
      },
      "src-fd05b338bba2": {
        "words": 54447,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2514.9,
            "panel_good": 22,
            "panel_bad": 439,
            "若无语种门会读到": 0.9523,
            "verdict": "不可用",
            "rate": 0.9523,
            "reason": "英文讹字率 0.9523（正形 22／讹形 439）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9523,
        "reason": "英文讹字率 0.9523（正形 22／讹形 439）",
        "file": "gri_33125008860989.txt"
      },
      "src-fc16329323b9": {
        "words": 68513,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.2183；英文：锚 10.9<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.8750）",
        "file": "gri_33125010858245.txt"
      },
      "src-3bb592d48bff": {
        "words": 80327,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2506.9,
            "panel_good": 11,
            "panel_bad": 776,
            "若无语种门会读到": 0.986,
            "verdict": "不可用",
            "rate": 0.986,
            "reason": "英文讹字率 0.9860（正形 11／讹形 776）"
          }
        },
        "verdict": "不可用",
        "rate": 0.986,
        "reason": "英文讹字率 0.9860（正形 11／讹形 776）",
        "file": "gri_33125011115488.txt"
      },
      "src-8798c1b52adf": {
        "words": 75322,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2668.7,
            "panel_good": 21,
            "panel_bad": 1018,
            "若无语种门会读到": 0.9798,
            "verdict": "不可用",
            "rate": 0.9798,
            "reason": "英文讹字率 0.9798（正形 21／讹形 1018）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9798,
        "reason": "英文讹字率 0.9798（正形 21／讹形 1018）",
        "file": "gri_33125011569684.txt"
      },
      "src-0717a438e7a2": {
        "words": 5638,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 8.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.5000）",
        "file": "icinqueordinidel00pall.txt"
      },
      "src-d729c800ee5c": {
        "words": 246016,
        "diagnostic_est_eft": [
          3,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8427；英文：锚 23.4<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.9123）",
        "file": "icommentaridicgi00caes_0.txt"
      },
      "src-9d9c67f40eae": {
        "words": 43034,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.7244；英文：锚 9.5<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.8571）",
        "file": "india.history.resource.93250.txt"
      },
      "src-a27003a29732": {
        "words": 39958,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.7946；英文：锚 10.5<500.0，若强行读 0.0000；德语：锚 1.0<15.0，若强行读 0.7619）",
        "file": "india.history.resource.93773.txt"
      },
      "src-69268dc57247": {
        "words": 40637,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.8229；英文：锚 6.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.8462）",
        "file": "india.history.resource.93774.txt"
      },
      "src-3c9b16abf778": {
        "words": 61354,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.7<15.0，若强行读 0.9583；英文：锚 16.1<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.9231）",
        "file": "iquattrolibridel01pall.txt"
      },
      "src-15929926a78b": {
        "words": 66958,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.6676；英文：锚 9.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.8958）",
        "file": "iqvattrolibridel00pall_0.txt"
      },
      "src-eecef2cf93b7": {
        "words": 15156,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 19.1,
            "panel_good": 0,
            "panel_bad": 7,
            "若无语种门会读到": 1.0,
            "verdict": "未核",
            "reason": "德语面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 0,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": null,
        "reason": "德语面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "lantichitadiroma00pall.txt"
      },
      "src-24ecf25c7376": {
        "words": 30824,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 2.3<15.0，若强行读 0.0273；英文：锚 3.6<500.0，若强行读 0.0000；德语：锚 0.6<15.0，若强行读 0.0667）",
        "file": "le-fabbriche-e-i-disegni-di-andrea-palladio-t.-4-1843.txt"
      },
      "src-7200948e4551": {
        "words": 23629,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 5.1<15.0，若强行读 0.0000；英文：锚 1.7<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.2500）",
        "file": "lefabbricheeidis03bert.txt"
      },
      "src-cec1934c8ebb": {
        "words": 28661,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 2.1<15.0，若强行读 0.0000；英文：锚 0.7<500.0，若强行读 0.0000；德语：锚 0.7<15.0，若强行读 0.0000）",
        "file": "lefabbricheeidis04bert.txt"
      },
      "src-104fc055b0da": {
        "words": 66777,
        "diagnostic_est_eft": [
          2,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.6410；英文：锚 14.2<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.8913）",
        "file": "qvattrolibridel00pall.txt"
      },
      "src-559dc0a0a057": {
        "words": 17400,
        "diagnostic_est_eft": [
          0,
          118
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 1.0000；英文：锚 5.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "traittedescinqor00pall.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 41,
    "与台账不一致的道": [
      "02-conversations.md",
      "05-decisions.md",
      "03-expression.md",
      "04-external.md",
      "06-timeline.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "核过 36 条，指错 0 条",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 0 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `wip-andrea-palladio-147`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 21 条，切分后核验片段 24 个，未命中 7 个，长 s 还原后才命中 10 个｜⚠ 研究/01-writings.md: 「breue trattato de' cinque ordini」｜⚠ 研究/01-writings.md: 「L'ANTICHITÀ DI ROMA DI M. ANDREA PALLADIO. RACCOLTA BREVEMENTE dagli Auttori Antichi, & Moderni」｜⚠ 研究/01-writings.md: 「ho data al Pubblico l'intiera raccolta delle Fabbriche, e dei Disegni del celebre Architetto Andrea 」｜⚠ 研究/02-conversations.md: 「Di V. S. Illustrissima. Humiliss. & Deuotiss. Seruitore Andrea Palladio」｜⚠ 研究/03-expression.md: 「CINQVE ORDINI DELL'Architettura di Andrea Palladio illustrati e ridotti a metodo facile」｜⚠ 研究/05-decisions.md: 「l'intiera raccolta delle Fabbriche, e dei Disegni」",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 12880980,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 17,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 7,
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
    "可用来源": 35,
    "**按内容去重后的作品数**": 29,
    "虚高": 1.207,
    "未声明的重复对": 0,
    "已声明的重复对": 9,
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
    "holdout 源数": 6,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 40,
    "train 源总数": 41,
    "本人所著字节": 16191899,
    "train 总字节": 16469530,
    "own_voice_ratio": 0.9831,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 6545714,
    "**判据说未核验的**": 22,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-df8f1e0dfc8b",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-ea04367ec274",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.049）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-db6919652a18",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-a8064aa6be0c",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-117866e8800c",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.054）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-82bce713201a",
        "原因": "语种判为 **?**（en=0.001 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b6cc7eeeb974",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-47508680be5d",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.039）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 4.16,
    "**立场句/万字**": 0.05,
    "其中不含第一人称的": 26,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 38,
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-andrea-palladio-147/andrea-palladio/evidence/source-ledger.jsonl",
    "一手份数": 32,
    "台账总份数": 35,
    "一手占比": 0.9143,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 41,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-df8f1e0dfc8b 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 41,
    "声称公有领域": 0,
    "不声称（不判）": 41,
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
    "external",
    "decisions",
    "timeline"
  ],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 41,
    "**`title` 就是文件名**": 0,
    "真书目题名": 41,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 1,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 6,
    "有一边没年份": 35,
    "**逐条**": [
      {
        "source_id": "src-24ecf25c7376",
        "文件名": "le-fabbriche-e-i-disegni-di-andrea-palladio-t.-4-1843.txt",
        "文件名里的年份": [
          1843
        ],
        "台账 published_at": 1846,
        "差": 3
      }
    ],
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

- `corpus.longs-corruption`: **13 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-2458ace11749` andreapalladiosa00pall.txt —— 英文讹字率 0.9837（正形 15／讹形 908），**不可做逐字引文**
- `source.filename-year-mismatch`: 1 条文件名年份与 `published_at` 差 ≥2 年 —— **至少有一处记错了**；判据不知道是哪一处
