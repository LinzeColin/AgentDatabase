# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-frobel-181/workspaces/friedrich-frobel`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T09:14:29Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 51,
    "claims": 23
  },
  "sources_total": 51,
  "sources_train": 47,
  "sources_usable_train": 47,
  "sources_holdout": 4,
  "primary_sources": 46,
  "primary_ratio": 0.9787,
  "lane_source_counts": {
    "writings": 30,
    "conversations": 4,
    "expression": 5,
    "external": 1,
    "decisions": 0,
    "timeline": 7
  },
  "authorship": {
    "P1 声称为本人所著": 0,
    "已证实归属": 0
  },
  "corpus_integrity": {
    "已扫": 51,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干德文编本的题名页（`src-78c284144dcf`，**Fraktur 排印，OCR 严重讹变**）。逐字原样：`?erau«gcgeben i?on ",
    "citation": "archive.org item（`src-78c284144dcf` 的 locator 见 source-ledger）",
    "争议篇目数": 0,
    "P1 声称本人所著": 50,
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
    "usable_train": 47,
    "fact 类条数": 11,
    "**人物事实**（计入）": 11,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 10,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 3,
    "**可复用做法**（计入）": 3,
    "复述式（不计入）": 0,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实"
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 51,
    "含同形字的源": 2,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "10762804bsb.txt",
        "非拉丁字符": 7,
        "全同形字词": 1,
        "样例": [
          "ν 读作 v",
          "n⁰ν 读作 n⁰v",
          "HH¹Ʒο 读作 HH¹Ʒo"
        ]
      },
      {
        "源": "FroebelEducazioneUomo.txt",
        "非拉丁字符": 4,
        "全同形字词": 2,
        "样例": [
          "а 读作 a",
          "а 读作 a"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 4,
      "不适用": 3,
      "干净": 44
    },
    "逐份": {
      "src-18b6090f5f15": {
        "words": 206933,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 801.8,
            "panel_good": 282,
            "panel_bad": 614,
            "若无语种门会读到": 0.6853,
            "verdict": "不可用",
            "rate": 0.6853,
            "reason": "德语讹字率 0.6853（正形 282／讹形 614）"
          }
        },
        "德语附加": {
          "h→b率": 0.0002,
          "h→b样本": 4109,
          "变音符每千词": 84.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6853,
        "reason": "德语讹字率 0.6853（正形 282／讹形 614）",
        "file": "10762804bsb.txt"
      },
      "src-ea158b847c59": {
        "words": 88293,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0032；英文：锚 0.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "FroebelEducazioneUomo.txt"
      },
      "src-6efe0d112ef5": {
        "words": 65094,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2259.7,
            "panel_good": 563,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 563／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 563／讹形 0）",
        "file": "aidstofamilygove00meyeuoft.txt"
      },
      "src-d4b9a6e4246f": {
        "words": 68589,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2025.3,
            "panel_good": 556,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 556／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 556／讹形 0）",
        "file": "autobiography00fruoft.txt"
      },
      "src-d57796f8101f": {
        "words": 64065,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2018.1,
            "panel_good": 517,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 517／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 517／讹形 0）",
        "file": "autobiographyoff00fr.txt"
      },
      "src-acbb866a32d5": {
        "words": 67935,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2049.6,
            "panel_good": 557,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 557／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 557／讹形 0）",
        "file": "autobiographyoff00frbe.txt"
      },
      "src-ccca8dba7834": {
        "words": 64250,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2018.2,
            "panel_good": 518,
            "panel_bad": 1,
            "若无语种门会读到": 0.0019,
            "verdict": "干净",
            "rate": 0.0019,
            "reason": "英文讹字率 0.0019（正形 518／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0019,
        "reason": "英文讹字率 0.0019（正形 518／讹形 1）",
        "file": "autobiographyoff00frob.txt"
      },
      "src-9e1a03fec2e7": {
        "words": 68127,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2048.1,
            "panel_good": 555,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 555／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 555／讹形 0）",
        "file": "autobiographyoff00froeiala.txt"
      },
      "src-9a599af46426": {
        "words": 68061,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2044.3,
            "panel_good": 556,
            "panel_bad": 2,
            "若无语种门会读到": 0.0036,
            "verdict": "干净",
            "rate": 0.0036,
            "reason": "英文讹字率 0.0036（正形 556／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.0036,
        "reason": "英文讹字率 0.0036（正形 556／讹形 2）",
        "file": "autobiographyoff00fruoft.txt"
      },
      "src-17bb2d882beb": {
        "words": 58631,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2070.1,
            "panel_good": 490,
            "panel_bad": 1,
            "若无语种门会读到": 0.002,
            "verdict": "干净",
            "rate": 0.002,
            "reason": "英文讹字率 0.0020（正形 490／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.002,
        "reason": "英文讹字率 0.0020（正形 490／讹形 1）",
        "file": "autobiooffriedri00froeiala.txt"
      },
      "src-0e9685ee5c80": {
        "words": 189724,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 846.5,
            "panel_good": 281,
            "panel_bad": 4424,
            "若无语种门会读到": 0.9403,
            "verdict": "不可用",
            "rate": 0.9403,
            "reason": "德语讹字率 0.9403（正形 281／讹形 4424）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3892,
          "变音符每千词": 94.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9403,
        "reason": "德语讹字率 0.9403（正形 281／讹形 4424）",
        "file": "bub_gb_SMoJAQAAIAAJ.txt"
      },
      "src-6846b7525666": {
        "words": 204954,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 772.0,
            "panel_good": 415,
            "panel_bad": 3641,
            "若无语种门会读到": 0.8977,
            "verdict": "不可用",
            "rate": 0.8977,
            "reason": "德语讹字率 0.8977（正形 415／讹形 3641）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4406,
          "变音符每千词": 96.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8977,
        "reason": "德语讹字率 0.8977（正形 415／讹形 3641）",
        "file": "bub_gb_kmc0AQAAMAAJ.txt"
      },
      "src-78c284144dcf": {
        "words": 209853,
        "diagnostic_est_eft": [
          0,
          24
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 64.8,
            "panel_good": 201,
            "panel_bad": 3152,
            "若无语种门会读到": 0.9401,
            "verdict": "不可用",
            "rate": 0.9401,
            "reason": "德语讹字率 0.9401（正形 201／讹形 3152）"
          }
        },
        "德语附加": {
          "h→b率": 0.0518,
          "h→b样本": 772,
          "变音符每千词": 126.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9401,
        "reason": "德语讹字率 0.9401（正形 201／讹形 3152）",
        "file": "bub_gb_xhwBAAAAYAAJ.txt"
      },
      "src-c5b1c845ca63": {
        "words": 107789,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2327.2,
            "panel_good": 965,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 965／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 965／讹形 0）",
        "file": "educationofman00f.txt"
      },
      "src-5a7b788a774a": {
        "words": 107568,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2340.6,
            "panel_good": 967,
            "panel_bad": 1,
            "若无语种门会读到": 0.001,
            "verdict": "干净",
            "rate": 0.001,
            "reason": "英文讹字率 0.0010（正形 967／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.001,
        "reason": "英文讹字率 0.0010（正形 967／讹形 1）",
        "file": "educationofman00fr.txt"
      },
      "src-3bab9a30dc87": {
        "words": 103766,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2335.4,
            "panel_good": 935,
            "panel_bad": 1,
            "若无语种门会读到": 0.0011,
            "verdict": "干净",
            "rate": 0.0011,
            "reason": "英文讹字率 0.0011（正形 935／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0011,
        "reason": "英文讹字率 0.0011（正形 935／讹形 1）",
        "file": "educationofman00fr2.txt"
      },
      "src-020c6b623301": {
        "words": 105603,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2347.8,
            "panel_good": 940,
            "panel_bad": 1,
            "若无语种门会读到": 0.0011,
            "verdict": "干净",
            "rate": 0.0011,
            "reason": "英文讹字率 0.0011（正形 940／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0011,
        "reason": "英文讹字率 0.0011（正形 940／讹形 1）",
        "file": "educationofman00frbe.txt"
      },
      "src-e6dc985703e6": {
        "words": 109676,
        "diagnostic_est_eft": [
          3,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2505.5,
            "panel_good": 1252,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1252／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1252／讹形 0）",
        "file": "educationofman00froe.txt"
      },
      "src-36349185b8d9": {
        "words": 103410,
        "diagnostic_est_eft": [
          4,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2344.4,
            "panel_good": 952,
            "panel_bad": 1,
            "若无语种门会读到": 0.001,
            "verdict": "干净",
            "rate": 0.001,
            "reason": "英文讹字率 0.0010（正形 952／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.001,
        "reason": "英文讹字率 0.0010（正形 952／讹形 1）",
        "file": "educationofman00frrich.txt"
      },
      "src-dd6af8da94b3": {
        "words": 104800,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2364.8,
            "panel_good": 962,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 962／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 962／讹形 0）",
        "file": "educationofman00fruoft.txt"
      },
      "src-0ee0bb0ac3f7": {
        "words": 92638,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2484.7,
            "panel_good": 1133,
            "panel_bad": 3,
            "若无语种门会读到": 0.0026,
            "verdict": "干净",
            "rate": 0.0026,
            "reason": "英文讹字率 0.0026（正形 1133／讹形 3）"
          }
        },
        "verdict": "干净",
        "rate": 0.0026,
        "reason": "英文讹字率 0.0026（正形 1133／讹形 3）",
        "file": "friedrichfroebe00frgoog.txt"
      },
      "src-393062b3c22a": {
        "words": 117362,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2332.1,
            "panel_good": 1430,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1430／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1430／讹形 0）",
        "file": "friedrichfroebe01jarvgoog.txt"
      },
      "src-2ca0e80439a5": {
        "words": 90108,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2506.3,
            "panel_good": 1128,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1128／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1128／讹形 0）",
        "file": "friedrichfroebe02jarvgoog.txt"
      },
      "src-b74213b6501a": {
        "words": 113566,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2334.8,
            "panel_good": 1418,
            "panel_bad": 1,
            "若无语种门会读到": 0.0007,
            "verdict": "干净",
            "rate": 0.0007,
            "reason": "英文讹字率 0.0007（正形 1418／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0007,
        "reason": "英文讹字率 0.0007（正形 1418／讹形 1）",
        "file": "friedrichfroebe03jarvgoog.txt"
      },
      "src-f32e3228c157": {
        "words": 93850,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2478.0,
            "panel_good": 1128,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1128／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1128／讹形 0）",
        "file": "friedrichfroebel00fr.txt"
      },
      "src-a7db55db365f": {
        "words": 93257,
        "diagnostic_est_eft": [
          5,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2488.4,
            "panel_good": 1133,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1133／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1133／讹形 0）",
        "file": "friedrichfroebel00froe.txt"
      },
      "src-206610b15226": {
        "words": 89658,
        "diagnostic_est_eft": [
          5,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2512.9,
            "panel_good": 1121,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1121／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1121／讹形 0）",
        "file": "friedrichfroebel00frrich.txt"
      },
      "src-265b964e5142": {
        "words": 92764,
        "diagnostic_est_eft": [
          5,
          3
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2492.7,
            "panel_good": 1126,
            "panel_bad": 1,
            "若无语种门会读到": 0.0009,
            "verdict": "干净",
            "rate": 0.0009,
            "reason": "英文讹字率 0.0009（正形 1126／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0009,
        "reason": "英文讹字率 0.0009（正形 1126／讹形 1）",
        "file": "friedrichfroebel01fr.txt"
      },
      "src-82d4f0e78a25": {
        "words": 93032,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2504.5,
            "panel_good": 1136,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1136／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1136／讹形 0）",
        "file": "friedrichfroebel02fr.txt"
      },
      "src-4f056938f63e": {
        "words": 116619,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2340.0,
            "panel_good": 1423,
            "panel_bad": 1,
            "若无语种门会读到": 0.0007,
            "verdict": "干净",
            "rate": 0.0007,
            "reason": "英文讹字率 0.0007（正形 1423／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0007,
        "reason": "英文讹字率 0.0007（正形 1423／讹形 1）",
        "file": "friedrichfroebel03fr.txt"
      },
      "src-83b59276db92": {
        "words": 51895,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2309.1,
            "panel_good": 441,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 441／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 441／讹形 0）",
        "file": "froebelletters00friala.txt"
      },
      "src-b9e8ee0a133a": {
        "words": 76830,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2293.5,
            "panel_good": 818,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 818／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 818／讹形 0）",
        "file": "froebelschiefwri00frrich.txt"
      },
      "src-42ae0c161d4f": {
        "words": 77188,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2293.8,
            "panel_good": 818,
            "panel_bad": 7,
            "若无语种门会读到": 0.0085,
            "verdict": "干净",
            "rate": 0.0085,
            "reason": "英文讹字率 0.0085（正形 818／讹形 7）"
          }
        },
        "verdict": "干净",
        "rate": 0.0085,
        "reason": "英文讹字率 0.0085（正形 818／讹形 7）",
        "file": "froebelschiefwri00fruoft.txt"
      },
      "src-b094fd4fe0b7": {
        "words": 129926,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2215.7,
            "panel_good": 1332,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1332／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1332／讹形 0）",
        "file": "froebelsletterso00fr.txt"
      },
      "src-10e3aa4dc12d": {
        "words": 126525,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2231.6,
            "panel_good": 1326,
            "panel_bad": 1,
            "若无语种门会读到": 0.0008,
            "verdict": "干净",
            "rate": 0.0008,
            "reason": "英文讹字率 0.0008（正形 1326／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0008,
        "reason": "英文讹字率 0.0008（正形 1326／讹形 1）",
        "file": "froebelsletterso00froe.txt"
      },
      "src-cc7abad9b0a2": {
        "words": 104204,
        "diagnostic_est_eft": [
          189,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0120；英文：锚 6.5<500.0，若强行读 0.0000；德语：锚 3.2<15.0，若强行读 0.0000）",
        "file": "laeducacindelh00fr.txt"
      },
      "src-e2268900dcc4": {
        "words": 92321,
        "diagnostic_est_eft": [
          177,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0119；英文：锚 5.8<500.0，若强行读 0.0000；德语：锚 2.9<15.0，若强行读 0.0000）",
        "file": "laeducacindelh01fr.txt"
      },
      "src-38ba9f2011f4": {
        "words": 126244,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2244.4,
            "panel_good": 1330,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1330／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1330／讹形 0）",
        "file": "lettersonkinderg00friala.txt"
      },
      "src-feed4b6efc60": {
        "words": 48086,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2033.4,
            "panel_good": 401,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 401／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 401／讹形 0）",
        "file": "motherplaynurser00froe.txt"
      },
      "src-d044478e84a8": {
        "words": 77319,
        "diagnostic_est_eft": [
          2,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1655.7,
            "panel_good": 441,
            "panel_bad": 1,
            "若无语种门会读到": 0.0023,
            "verdict": "干净",
            "rate": 0.0023,
            "reason": "英文讹字率 0.0023（正形 441／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0023,
        "reason": "英文讹字率 0.0023（正形 441／讹形 1）",
        "file": "motherssongsgame00fruoft.txt"
      },
      "src-fb6c24863e56": {
        "words": 64969,
        "diagnostic_est_eft": [
          4,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2039.9,
            "panel_good": 588,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 588／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 588／讹形 0）",
        "file": "mottoesandcomme00unkngoog.txt"
      },
      "src-8691d5260829": {
        "words": 68549,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2069.2,
            "panel_good": 595,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 595／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 595／讹形 0）",
        "file": "mottoescommentar00fr.txt"
      },
      "src-5f4c85ec8d34": {
        "words": 64691,
        "diagnostic_est_eft": [
          5,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2040.3,
            "panel_good": 577,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 577／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 577／讹形 0）",
        "file": "mottoescommentar00frrich.txt"
      },
      "src-5d88b1d62ecc": {
        "words": 113133,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2341.8,
            "panel_good": 1403,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1403／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1403／讹形 0）",
        "file": "richfroebelfried00frrich.txt"
      },
      "src-7c304edace73": {
        "words": 23010,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1409.0,
            "panel_good": 104,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 104／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 104／讹形 0）",
        "file": "songsandmusicfr00compgoog.txt"
      },
      "src-8de5e1862b85": {
        "words": 24665,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1260.5,
            "panel_good": 89,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 89／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 89／讹形 0）",
        "file": "songsmusicoffrie00fr.txt"
      },
      "src-241b755ba6c2": {
        "words": 26420,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1105.2,
            "panel_good": 89,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 89／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 89／讹形 0）",
        "file": "songsmusicoffrie00fruoft.txt"
      },
      "src-ec642a55bf99": {
        "words": 24383,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1266.0,
            "panel_good": 84,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 84／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 84／讹形 0）",
        "file": "songsmusicoffrie01fr.txt"
      },
      "src-464c59771f2d": {
        "words": 41240,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1939.1,
            "panel_good": 275,
            "panel_bad": 2,
            "若无语种门会读到": 0.0072,
            "verdict": "干净",
            "rate": 0.0072,
            "reason": "英文讹字率 0.0072（正形 275／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.0072,
        "reason": "英文讹字率 0.0072（正形 275／讹形 2）",
        "file": "studentsfroebel01herfgoog.txt"
      },
      "src-3b1d8669e740": {
        "words": 40056,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1973.0,
            "panel_good": 263,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 263／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 263／讹形 0）",
        "file": "studentsfroebela00froeiala.txt"
      },
      "src-f9b18fc33e99": {
        "words": 48661,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2078.9,
            "panel_good": 340,
            "panel_bad": 2,
            "若无语种门会读到": 0.0058,
            "verdict": "干净",
            "rate": 0.0058,
            "reason": "英文讹字率 0.0058（正形 340／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.0058,
        "reason": "英文讹字率 0.0058（正形 340／讹形 2）",
        "file": "studentsfroebela00fruoft.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 51,
    "与台账不一致的道": [],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "corpus_cache": "未给 --cache，**自动使用 `raw`**（与本文件另外三处一致）",
    "quote_integrity_scope": "evals/judge_payload.v1.json 不在——**答案层未核验（不是通过）**；候选答案没落进工作区时，任何门都看不见它",
    "shared_anchor": "evals/judge_payload.v1.json 不在——**同源引用未比对（不是通过）**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak": "evals/baseline.v1.json 不在——**表面特征泄题未核（不是通过）**；基线只存在于人物工作目录里，没落进工作区，**门看不见它**",
    "unsourced_names": "缺 --cache 或 judge_payload，**承重人名未核（不是通过）**",
    "self_counts": "evals/judge_payload.v1.json 不在——**自报字数未核（不是通过）**",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 13,
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
    "可用来源": 47,
    "**按内容去重后的作品数**": 17,
    "虚高": 2.765,
    "未声明的重复对": 0,
    "已声明的重复对": 77,
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
    "判据条数": 32,
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
        "引文数": 4,
        "核过": 4,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 1,
        "核过": 1,
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
        "引文数": 3,
        "核过": 3,
        "**对不上**": []
      }
    },
    "合计": "8 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 4,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 0,
    "train 源总数": 51,
    "本人所著字节": 0,
    "train 总字节": 30608298,
    "own_voice_ratio": 0.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 23094883,
    "**判据说未核验的**": 7,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-18b6090f5f15",
        "原因": "语种判为 **de**（en=0.000 de=0.157 fr=0.012）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-ea158b847c59",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-0e9685ee5c80",
        "原因": "语种判为 **de**（en=0.000 de=0.137 fr=0.012）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-6846b7525666",
        "原因": "语种判为 **de**（en=0.000 de=0.125 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-78c284144dcf",
        "原因": "语种判为 **?**（en=0.000 de=0.007 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-cc7abad9b0a2",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.002）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-e2268900dcc4",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.002）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 14.04,
    "**立场句/万字**": 0.12,
    "其中不含第一人称的": 182,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 50,
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
    "载荷": "baseline_bare.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.625,
    "状态": "无候选（第一人称覆盖率 0.625）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-frobel-181/workspaces/friedrich-frobel/evidence/source-ledger.jsonl",
    "一手份数": 46,
    "台账总份数": 47,
    "一手占比": 0.9787,
    "有材料的道数": 5,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 51,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-18b6090f5f15 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 51,
    "声称公有领域": 0,
    "不声称（不判）": 51,
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
    "台账行数": 51,
    "**`title` 就是文件名**": 0,
    "真书目题名": 51,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 51,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 23,
  "claims_active": 23,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 23,
  "eval_cases": 32,
  "eval_suite_counts": {
    "known": 2,
    "boundary": 2,
    "voice": 2,
    "trajectory": 2,
    "contrast": 2,
    "fact-preservation": 2,
    "style-decoy": 2,
    "task-completion": 2,
    "planning-fidelity": 2,
    "tool-use": 2,
    "capability-calibration": 2,
    "refusal-stop": 2,
    "long-horizon": 2,
    "identity-routing": 2,
    "anonymous-fidelity": 2,
    "token-efficiency": 2
  },
  "case_self_sufficiency": {
    "用例数": 32,
    "断链的题": 0
  },
  "measurement_claims": {
    "已扫单元": 1,
    "实测声明": 1,
    "同段带数": 1,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0
  },
  "evidence_per_claim": {
    "断言条数": 23,
    "source_ids": "逐条各异（非空 23/23，不同取值 16）",
    "evidence_clusters": "逐条各异（非空 23/23，不同取值 20）",
    "counter_source_ids": "整批都空（非空 0/23，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 3,
    "作品组数（连通分量，仅供参考）": 21,
    "来源数": 51,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 16,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 2,
    "不唯一（同句见于多份源，挂错也照样绿）": 12,
    "取不到正文的源": 0,
    "例": [
      "clm-fe586b2a7b69：挂 ['educationofman00f.txt'] → 实 ['educationofman00frrich.txt', 'educationofman00fruoft.txt', 'froebelschiefwri00frrich.txt']",
      "clm-c6728fec5def：挂 ['froebelsletterso00froe.txt'] → 实 ['autobiographyoff00frbe.txt', 'autobiographyoff00froeiala.txt', 'autobiographyoff00fruoft.txt', 'froebelsletterso00fr.txt', 'lettersonkinderg00friala.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-frobel-181/workspaces/friedrich-frobel/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-9d8aa40d243f",
      "           **他的活动模型：成人是活动的一部分，不是外面的人。** 记录里教师被**安排到队列的位置上**；而母亲游戏里母亲是执球的那一方。⇒ 他的场景里没有旁观席。…",
      "",
      "低于 10% 的 32 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-frobel-181/workspaces/friedrich-frobel/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-frobel-181/workspaces/friedrich-frobel/audit/source-coverage.json），**未核验**（不是通过）"
  },
  "unqualified_priority": {
    "第一人称首创声明": 0,
    "其中带限定": 0,
    "扫了几个文件": 1,
    "状态": "一处首创声明都没扫到。**这可能是产物干净，也可能是判据窄**——v0.0.0.73 第一版就在真数据上报过一次假的 0。"
  },
  "sole_authorship": {
    "合著／集体署名的源": 0,
    "状态": "**账本里一条合著／集体署名的源都没有——本次什么也没查，不构成通过。**十一个人物里只有三个的账本记了这一层，**多半是抓源阶段没记，不是真的没有合著。**"
  },
  "eval_results": 64,
  "candidate_overall": 0.85,
  "baseline_overall": 0.4744,
  "candidate_baseline_delta": 0.3756,
  "suite_candidate_means": {
    "known": 0.6,
    "boundary": 0.925,
    "voice": 0.95,
    "trajectory": 0.6,
    "contrast": 0.575,
    "fact-preservation": 0.95,
    "style-decoy": 0.925,
    "task-completion": 0.9,
    "planning-fidelity": 0.975,
    "tool-use": 0.9,
    "capability-calibration": 0.675,
    "refusal-stop": 0.925,
    "long-horizon": 0.95,
    "identity-routing": 0.95,
    "anonymous-fidelity": 0.875,
    "token-efficiency": 0.925
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 18/23 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 5 未纳入）",
  "baseline_provenance": {
    "baseline_rows": 32,
    "by_source": {
      "unknown": 32
    },
    "usable_rows": 0,
    "unusable_rows": 32,
    "capability_evidence": false
  },
  "secret_findings": 0
}
```

## Errors

- `model.placeholder`: strategy.md is not substantive enough for release
- `corpus.ocr-dead-as-primary`: **有被 OCR 整份毁掉的文件被记作 P1**——你正打算从一份读不出字的文件里取逐字引文；换干净扫本或降级

## Warnings

- `corpus.longs-corruption`: **4 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-18b6090f5f15` 10762804bsb.txt —— 德语讹字率 0.6853（正形 282／讹形 614），**不可做逐字引文**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
