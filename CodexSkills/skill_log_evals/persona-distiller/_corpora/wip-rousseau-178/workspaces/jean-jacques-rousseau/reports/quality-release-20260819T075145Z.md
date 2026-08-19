# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-rousseau-178/workspaces/jean-jacques-rousseau`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T07:51:45Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 103,
    "claims": 34
  },
  "sources_total": 103,
  "sources_train": 91,
  "sources_usable_train": 91,
  "sources_holdout": 12,
  "primary_sources": 79,
  "primary_ratio": 0.8681,
  "lane_source_counts": {
    "writings": 61,
    "conversations": 12,
    "expression": 0,
    "external": 12,
    "decisions": 0,
    "timeline": 6
  },
  "authorship": {
    "P1 声称为本人所著": 91,
    "已证实归属": 41,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "50 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 103,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/avisauxgensdelet00rous.txt　过短：1755 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干编本的题名页逐字（`src-1ef4f4ebbc04`）：`OEUVRES COMPLÈTES DE J. J. ROUSSEAU AVEC DES NOT",
    "citation": "archive.org item（`src-1ef4f4ebbc04` 的 locator 见 source-ledger）",
    "争议篇目数": 0,
    "P1 声称本人所著": 86,
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
    "usable_train": 91,
    "fact 类条数": 20,
    "**人物事实**（计入）": 20,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 19,
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
    "已查语料件": 103,
    "含同形字的源": 6,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "bim_eighteenth-century_anecdotes-of-the-last-tw_corancez-olivier-de_1798.txt",
        "非拉丁字符": 4,
        "全同形字词": 0,
        "样例": [
          "νο⁰ẽ 读作 vo⁰ẽ"
        ]
      },
      {
        "源": "bim_eighteenth-century_botanique-english-le_rousseau-jean-jacques_1796.txt",
        "非拉丁字符": 3,
        "全同形字词": 0,
        "样例": [
          "ποmm 读作 πomm",
          "hο 读作 ho"
        ]
      },
      {
        "源": "bim_eighteenth-century_considrations-sur-le-go_rousseau-jean-jacques_1782.txt",
        "非拉丁字符": 2,
        "全同形字词": 1,
        "样例": [
          "ο 读作 o",
          "ECONBοE 读作 ECONBoE"
        ]
      },
      {
        "源": "bim_eighteenth-century_eloisa-or-a-series-of-_rousseau-jean-jacques_1764_1.txt",
        "非拉丁字符": 3,
        "全同形字词": 2,
        "样例": [
          "ο 读作 o",
          "ο 读作 o",
          "egDν 读作 egDv"
        ]
      },
      {
        "源": "bim_eighteenth-century_emilius-and-sophia-or-_rousseau-jean-jacques_1783.txt",
        "非拉丁字符": 1,
        "全同形字词": 0,
        "样例": [
          "νj 读作 vj"
        ]
      },
      {
        "源": "bub_gb_zN1MAAAAcAAJ.txt",
        "非拉丁字符": 2,
        "全同形字词": 2,
        "样例": [
          "ο 读作 o",
          "ν 读作 v"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 22,
      "不适用": 60,
      "混杂": 3,
      "未核": 5,
      "干净": 13
    },
    "逐份": {
      "src-fc4911a43495": {
        "words": 76521,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 516.5,
            "panel_good": 365,
            "panel_bad": 653,
            "若无语种门会读到": 0.6415,
            "verdict": "不可用",
            "rate": 0.6415,
            "reason": "德语讹字率 0.6415（正形 365／讹形 653）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1509,
          "变音符每千词": 45.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6415,
        "reason": "德语讹字率 0.6415（正形 365／讹形 653）",
        "file": "10066336bsb.txt"
      },
      "src-0614303d6af4": {
        "words": 61942,
        "diagnostic_est_eft": [
          0,
          602
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.9049；英文：锚 4.2<500.0，若强行读 0.5000；德语：锚 0.3<15.0，若强行读 0.8750）",
        "file": "10097325bsb.txt"
      },
      "src-8a0ad52c5d77": {
        "words": 16611,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 568.3,
            "panel_good": 31,
            "panel_bad": 74,
            "若无语种门会读到": 0.7048,
            "verdict": "不可用",
            "rate": 0.7048,
            "reason": "德语讹字率 0.7048（正形 31／讹形 74）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 325,
          "变音符每千词": 53.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7048,
        "reason": "德语讹字率 0.7048（正形 31／讹形 74）",
        "file": "10599347bsb.txt"
      },
      "src-bf7ad6ba0680": {
        "words": 51697,
        "diagnostic_est_eft": [
          532,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0600；英文：锚 1.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1538）",
        "file": "10713049bsb.txt"
      },
      "src-d173b2dabfe0": {
        "words": 112398,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 622.9,
            "panel_good": 109,
            "panel_bad": 817,
            "若无语种门会读到": 0.8823,
            "verdict": "不可用",
            "rate": 0.8823,
            "reason": "德语讹字率 0.8823（正形 109／讹形 817）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2597,
          "变音符每千词": 49.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8823,
        "reason": "德语讹字率 0.8823（正形 109／讹形 817）",
        "file": "10762426bsb.txt"
      },
      "src-f1d1ffcf7f5e": {
        "words": 111836,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 618.9,
            "panel_good": 228,
            "panel_bad": 882,
            "若无语种门会读到": 0.7946,
            "verdict": "不可用",
            "rate": 0.7946,
            "reason": "德语讹字率 0.7946（正形 228／讹形 882）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2474,
          "变音符每千词": 49.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7946,
        "reason": "德语讹字率 0.7946（正形 228／讹形 882）",
        "file": "10762427bsb.txt"
      },
      "src-3c91b85250af": {
        "words": 77506,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 590.8,
            "panel_good": 417,
            "panel_bad": 652,
            "若无语种门会读到": 0.6099,
            "verdict": "不可用",
            "rate": 0.6099,
            "reason": "德语讹字率 0.6099（正形 417／讹形 652）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1537,
          "变音符每千词": 37.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6099,
        "reason": "德语讹字率 0.6099（正形 417／讹形 652）",
        "file": "10764054bsb.txt"
      },
      "src-f7c1a948f032": {
        "words": 64405,
        "diagnostic_est_eft": [
          0,
          830
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.9188；英文：锚 4.3<500.0，若强行读 1.0000；德语：锚 0.5<15.0，若强行读 0.6957）",
        "file": "11258220bsb.txt"
      },
      "src-eaae19ebf3cb": {
        "words": 43874,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 511.7,
            "panel_good": 513,
            "panel_bad": 250,
            "若无语种门会读到": 0.3277,
            "verdict": "不可用",
            "rate": 0.3277,
            "reason": "德语讹字率 0.3277（正形 513／讹形 250）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 787,
          "变音符每千词": 78.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.3277,
        "reason": "德语讹字率 0.3277（正形 513／讹形 250）",
        "file": "11718256bsb.txt"
      },
      "src-0795b4f9421e": {
        "words": 61657,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 577.1,
            "panel_good": 530,
            "panel_bad": 497,
            "若无语种门会读到": 0.4839,
            "verdict": "不可用",
            "rate": 0.4839,
            "reason": "德语讹字率 0.4839（正形 530／讹形 497）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1187,
          "变音符每千词": 28.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.4839,
        "reason": "德语讹字率 0.4839（正形 530／讹形 497）",
        "file": "11918930bsb.txt"
      },
      "src-b3e4f1f48bf6": {
        "words": 74665,
        "diagnostic_est_eft": [
          1,
          530
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.9571；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.6364）",
        "file": "11919281bsb.txt"
      },
      "src-f18ee29f286d": {
        "words": 47484,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 521.6,
            "panel_good": 1195,
            "panel_bad": 289,
            "若无语种门会读到": 0.1947,
            "verdict": "混杂",
            "rate": 0.1947,
            "reason": "德语讹字率 0.1947（正形 1195／讹形 289）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1156,
          "变音符每千词": 44.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.1947,
        "reason": "德语讹字率 0.1947（正形 1195／讹形 289）",
        "file": "11919322bsb.txt"
      },
      "src-2389afc68417": {
        "words": 47748,
        "diagnostic_est_eft": [
          0,
          382
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.3<15.0，若强行读 0.6589；英文：锚 1.9<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "1766jjacquesrous00rous.txt"
      },
      "src-bba68d3e7ffe": {
        "words": 170358,
        "diagnostic_est_eft": [
          0,
          509
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8025；英文：锚 3.3<500.0，若强行读 1.0000；德语：锚 0.1<15.0，若强行读 0.8889）",
        "file": "1782collectionco10rous.txt"
      },
      "src-1ae86fb504c8": {
        "words": 126983,
        "diagnostic_est_eft": [
          0,
          538
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8396；英文：锚 1.7<500.0，若强行读 1.0000；德语：锚 0.1<15.0，若强行读 0.9167）",
        "file": "1782collectionco17rous.txt"
      },
      "src-a275ac2e547e": {
        "words": 72273,
        "diagnostic_est_eft": [
          0,
          772
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8128；英文：锚 3.3<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.8824）",
        "file": "1791emileoudel02rous.txt"
      },
      "src-ec684cbf06d5": {
        "words": 68775,
        "diagnostic_est_eft": [
          0,
          706
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.7957；英文：锚 2.3<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.4667）",
        "file": "1791emileoudel03rous.txt"
      },
      "src-1ef4f4ebbc04": {
        "words": 731373,
        "diagnostic_est_eft": [
          8699,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0070；英文：锚 1.4<500.0，若强行读 0.0278；德语：锚 0.0<15.0，若强行读 0.3125）",
        "file": "1846oeuvrescom02rousuoft.txt"
      },
      "src-247577f8640a": {
        "words": 75598,
        "diagnostic_est_eft": [
          750,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 1.9<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.6000）",
        "file": "1911lettresind00rous.txt"
      },
      "src-732d39d2e7a7": {
        "words": 80241,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2018.4,
            "panel_good": 26,
            "panel_bad": 1011,
            "若无语种门会读到": 0.9749,
            "verdict": "不可用",
            "rate": 0.9749,
            "reason": "英文讹字率 0.9749（正形 26／讹形 1011）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9749,
        "reason": "英文讹字率 0.9749（正形 26／讹形 1011）",
        "file": "31383026610652.txt"
      },
      "src-b6f6c2257a8b": {
        "words": 92101,
        "diagnostic_est_eft": [
          1209,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0087；英文：锚 2.6<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1429）",
        "file": "A029103.txt"
      },
      "src-f25d5e53af8f": {
        "words": 122311,
        "diagnostic_est_eft": [
          0,
          212
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 1.0000；英文：锚 2.9<500.0，若强行读 1.0000；德语：锚 0.2<15.0，若强行读 0.8333）",
        "file": "BIUSante_07891x01.txt"
      },
      "src-dfd6a6c5f7bb": {
        "words": 60105,
        "diagnostic_est_eft": [
          1,
          573
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.0<15.0，若强行读 0.9874；英文：锚 3.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.8333）",
        "file": "a1758jjrousseauci00rous.txt"
      },
      "src-e7ebbb5f86d6": {
        "words": 61572,
        "diagnostic_est_eft": [
          1,
          519
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.8<15.0，若强行读 0.9630；英文：锚 2.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.8000）",
        "file": "aa1758jjrousseau00rous.txt"
      },
      "src-6d01d4bdbb5a": {
        "words": 89252,
        "diagnostic_est_eft": [
          1,
          968
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.7402；英文：锚 4.7<500.0，若强行读 1.0000；德语：锚 0.3<15.0，若强行读 0.9375）",
        "file": "amileoudeldu01rous.txt"
      },
      "src-fa889e6e1723": {
        "words": 71505,
        "diagnostic_est_eft": [
          0,
          400
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8860；英文：锚 3.9<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "amileoudeldu02rous.txt"
      },
      "src-4e50f690225f": {
        "words": 67896,
        "diagnostic_est_eft": [
          0,
          363
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8613；英文：锚 2.9<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.5333）",
        "file": "amileoudeldu03rous.txt"
      },
      "src-c41d2f17f11d": {
        "words": 83339,
        "diagnostic_est_eft": [
          0,
          1065
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.7355；英文：锚 3.1<500.0，若强行读 1.0000；德语：锚 0.1<15.0，若强行读 0.4324）",
        "file": "amileoudeldu04rous.txt"
      },
      "src-7509b6003dbf": {
        "words": 272,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "avisauxgensdelet00rous.txt"
      },
      "src-b5baa4a0416c": {
        "words": 1815,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 462.8,
            "panel_good": 47,
            "panel_bad": 1,
            "若无语种门会读到": 0.0208,
            "verdict": "混杂",
            "rate": 0.0208,
            "reason": "德语讹字率 0.0208（正形 47／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 32,
          "变音符每千词": 75.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.0208,
        "reason": "德语讹字率 0.0208（正形 47／讹形 1）",
        "file": "bekenntnisseunv00hardgoog.txt"
      },
      "src-48b2f5f69ffb": {
        "words": 8822,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1667.4,
            "panel_good": 0,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 0 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 0 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_a-dialogue-between-a-man_rousseau-jean-jacques_1761.txt"
      },
      "src-0088d5b7596e": {
        "words": 58655,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2153.4,
            "panel_good": 11,
            "panel_bad": 5,
            "若无语种门会读到": 0.3125,
            "verdict": "未核",
            "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_an-inquiry-into-the-natu_rousseau-jean-jacques_1791_0.txt"
      },
      "src-fdc170192feb": {
        "words": 21348,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1831.6,
            "panel_good": 0,
            "panel_bad": 14,
            "若无语种门会读到": 1.0,
            "verdict": "未核",
            "reason": "英文面板只命中 14 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 14 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_anecdotes-of-the-last-tw_corancez-olivier-de_1798.txt"
      },
      "src-2eabce7d2b1c": {
        "words": 133590,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1813.2,
            "panel_good": 19,
            "panel_bad": 10,
            "若无语种门会读到": 0.3448,
            "verdict": "未核",
            "reason": "英文面板只命中 29 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 29 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_botanique-english-le_rousseau-jean-jacques_1787.txt"
      },
      "src-82e837894e91": {
        "words": 139252,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1732.3,
            "panel_good": 19,
            "panel_bad": 12,
            "若无语种门会读到": 0.3871,
            "verdict": "不可用",
            "rate": 0.3871,
            "reason": "英文讹字率 0.3871（正形 19／讹形 12）"
          }
        },
        "verdict": "不可用",
        "rate": 0.3871,
        "reason": "英文讹字率 0.3871（正形 19／讹形 12）",
        "file": "bim_eighteenth-century_botanique-english-le_rousseau-jean-jacques_1796.txt"
      },
      "src-d7edf5a0f615": {
        "words": 56293,
        "diagnostic_est_eft": [
          0,
          7
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.9250；英文：锚 3.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "bim_eighteenth-century_considrations-sur-le-go_rousseau-jean-jacques_1782.txt"
      },
      "src-e0f9ae7515b8": {
        "words": 57623,
        "diagnostic_est_eft": [
          0,
          12
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.8889；英文：锚 5.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.8889）",
        "file": "bim_eighteenth-century_discours-sur-lorigine-e_rousseau-jean-jacques_1782.txt"
      },
      "src-1b21ee175a98": {
        "words": 53250,
        "diagnostic_est_eft": [
          454,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.0335；英文：锚 3.6<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.2222）",
        "file": "bim_eighteenth-century_discours-sur-lorigine-e_rousseau-jean-jacques_1782_0.txt"
      },
      "src-7e2874439aa2": {
        "words": 98955,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1688.8,
            "panel_good": 30,
            "panel_bad": 6,
            "若无语种门会读到": 0.1667,
            "verdict": "混杂",
            "rate": 0.1667,
            "reason": "英文讹字率 0.1667（正形 30／讹形 6）"
          }
        },
        "verdict": "混杂",
        "rate": 0.1667,
        "reason": "英文讹字率 0.1667（正形 30／讹形 6）",
        "file": "bim_eighteenth-century_eloisa-_rousseau-jean-jacques_1784_1.txt"
      },
      "src-775e16de995f": {
        "words": 90358,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1796.9,
            "panel_good": 18,
            "panel_bad": 12,
            "若无语种门会读到": 0.4,
            "verdict": "不可用",
            "rate": 0.4,
            "reason": "英文讹字率 0.4000（正形 18／讹形 12）"
          }
        },
        "verdict": "不可用",
        "rate": 0.4,
        "reason": "英文讹字率 0.4000（正形 18／讹形 12）",
        "file": "bim_eighteenth-century_eloisa-_rousseau-jean-jacques_1784_2.txt"
      },
      "src-c7701238aaa1": {
        "words": 88027,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1696.5,
            "panel_good": 29,
            "panel_bad": 17,
            "若无语种门会读到": 0.3696,
            "verdict": "不可用",
            "rate": 0.3696,
            "reason": "英文讹字率 0.3696（正形 29／讹形 17）"
          }
        },
        "verdict": "不可用",
        "rate": 0.3696,
        "reason": "英文讹字率 0.3696（正形 29／讹形 17）",
        "file": "bim_eighteenth-century_eloisa-or-a-series-of-_rousseau-jean-jacques_1761_1.txt"
      },
      "src-537dae580388": {
        "words": 101671,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1827.5,
            "panel_good": 25,
            "panel_bad": 35,
            "若无语种门会读到": 0.5833,
            "verdict": "不可用",
            "rate": 0.5833,
            "reason": "英文讹字率 0.5833（正形 25／讹形 35）"
          }
        },
        "verdict": "不可用",
        "rate": 0.5833,
        "reason": "英文讹字率 0.5833（正形 25／讹形 35）",
        "file": "bim_eighteenth-century_eloisa-or-a-series-of-_rousseau-jean-jacques_1761_3_0.txt"
      },
      "src-710448a5e437": {
        "words": 98093,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1586.7,
            "panel_good": 28,
            "panel_bad": 21,
            "若无语种门会读到": 0.4286,
            "verdict": "不可用",
            "rate": 0.4286,
            "reason": "英文讹字率 0.4286（正形 28／讹形 21）"
          }
        },
        "verdict": "不可用",
        "rate": 0.4286,
        "reason": "英文讹字率 0.4286（正形 28／讹形 21）",
        "file": "bim_eighteenth-century_eloisa-or-a-series-of-_rousseau-jean-jacques_1764_1.txt"
      },
      "src-7d63fdd11b45": {
        "words": 101381,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1664.9,
            "panel_good": 34,
            "panel_bad": 11,
            "若无语种门会读到": 0.2444,
            "verdict": "不可用",
            "rate": 0.2444,
            "reason": "英文讹字率 0.2444（正形 34／讹形 11）"
          }
        },
        "verdict": "不可用",
        "rate": 0.2444,
        "reason": "英文讹字率 0.2444（正形 34／讹形 11）",
        "file": "bim_eighteenth-century_eloisa-or-a-series-of-o_rousseau-jean-jacques_1769_1.txt"
      },
      "src-b0e34147dada": {
        "words": 71492,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1844.4,
            "panel_good": 21,
            "panel_bad": 10,
            "若无语种门会读到": 0.3226,
            "verdict": "不可用",
            "rate": 0.3226,
            "reason": "英文讹字率 0.3226（正形 21／讹形 10）"
          }
        },
        "verdict": "不可用",
        "rate": 0.3226,
        "reason": "英文讹字率 0.3226（正形 21／讹形 10）",
        "file": "bim_eighteenth-century_emile-english-emilius_rousseau-jean-jacques_1767_3.txt"
      },
      "src-ae3c9439ae9a": {
        "words": 6507,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1254.0,
            "panel_good": 4,
            "panel_bad": 1,
            "若无语种门会读到": 0.2,
            "verdict": "未核",
            "reason": "英文面板只命中 5 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 5 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_emilius-and-sophia-or-_rousseau-jean-jacques_1783.txt"
      },
      "src-ab29eb947ed6": {
        "words": 247345,
        "diagnostic_est_eft": [
          3004,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.5<15.0，若强行读 0.0023；英文：锚 1.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2500）",
        "file": "bub_gb_3DbL7IDH2jIC.txt"
      },
      "src-1b826ee092ec": {
        "words": 39459,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 599.6,
            "panel_good": 1327,
            "panel_bad": 1,
            "若无语种门会读到": 0.0008,
            "verdict": "干净",
            "rate": 0.0008,
            "reason": "德语讹字率 0.0008（正形 1327／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0017,
          "h→b样本": 1158,
          "变音符每千词": 102.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0008,
        "reason": "德语讹字率 0.0008（正形 1327／讹形 1）",
        "file": "bub_gb_OXcpAAAAYAAJ.txt"
      },
      "src-11fff2c32840": {
        "words": 180386,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 627.3,
            "panel_good": 225,
            "panel_bad": 2976,
            "若无语种门会读到": 0.9297,
            "verdict": "不可用",
            "rate": 0.9297,
            "reason": "德语讹字率 0.9297（正形 225／讹形 2976）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3980,
          "变音符每千词": 58.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9297,
        "reason": "德语讹字率 0.9297（正形 225／讹形 2976）",
        "file": "bub_gb_yN1MAAAAcAAJ.txt"
      },
      "src-40e6aba1da09": {
        "words": 112765,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 638.6,
            "panel_good": 115,
            "panel_bad": 620,
            "若无语种门会读到": 0.8435,
            "verdict": "不可用",
            "rate": 0.8435,
            "reason": "德语讹字率 0.8435（正形 115／讹形 620）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2653,
          "变音符每千词": 39.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8435,
        "reason": "德语讹字率 0.8435（正形 115／讹形 620）",
        "file": "bub_gb_zN1MAAAAcAAJ.txt"
      },
      "src-670dc0b2b31f": {
        "words": 435081,
        "diagnostic_est_eft": [
          4532,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0060；英文：锚 3.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.4750）",
        "file": "ceuvrescomplete00troigoog.txt"
      },
      "src-a1dccf5726b4": {
        "words": 110157,
        "diagnostic_est_eft": [
          14,
          978
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.9<15.0，若强行读 0.7076；英文：锚 6.9<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.7000）",
        "file": "chepfl-lipr-AXA226.txt"
      },
      "src-aea9d887150e": {
        "words": 94213,
        "diagnostic_est_eft": [
          8,
          541
        ],
        "逐语域": {
          "拉丁": {
            "语域": "拉丁",
            "anchors_per_10k": 18.6,
            "panel_good": 26,
            "panel_bad": 421,
            "若无语种门会读到": 0.9418,
            "verdict": "不可用",
            "rate": 0.9418,
            "reason": "拉丁讹字率 0.9418（正形 26／讹形 421）"
          }
        },
        "ae_连字": {
          "ae_per_1000": 0.74,
          "quae": 14,
          "que": 969,
          "quae_ratio": 0.014,
          "判读": "**打散**",
          "理由": "ae 0.74/千字母（门 3.5）、quae 占比 0.014（门 0.80）"
        },
        "verdict": "不可用",
        "rate": 0.9418,
        "reason": "拉丁讹字率 0.9418（正形 26／讹形 421）　★ **但 ae 连字被打散**（ae 0.74/千字母（门 3.5）、quae 占比 0.014（门 0.80））：`quae`→`que`、`haec`→`hee`，**逐字引用会印出作者没写的形**",
        "file": "collectioncompl31rousgoog.txt"
      },
      "src-d22a3140d87c": {
        "words": 226822,
        "diagnostic_est_eft": [
          9,
          2172
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.9349；英文：锚 10.6<500.0，若强行读 0.1818；德语：锚 0.2<15.0，若强行读 0.9679）",
        "file": "collectioncompl41rousgoog.txt"
      },
      "src-8a180096a208": {
        "words": 93971,
        "diagnostic_est_eft": [
          0,
          549
        ],
        "逐语域": {
          "拉丁": {
            "语域": "拉丁",
            "anchors_per_10k": 17.5,
            "panel_good": 20,
            "panel_bad": 435,
            "若无语种门会读到": 0.956,
            "verdict": "不可用",
            "rate": 0.956,
            "reason": "拉丁讹字率 0.9560（正形 20／讹形 435）"
          }
        },
        "ae_连字": {
          "ae_per_1000": 1.27,
          "quae": 18,
          "que": 924,
          "quae_ratio": 0.019,
          "判读": "**打散**",
          "理由": "ae 1.27/千字母（门 3.5）、quae 占比 0.019（门 0.80）"
        },
        "verdict": "不可用",
        "rate": 0.956,
        "reason": "拉丁讹字率 0.9560（正形 20／讹形 435）　★ **但 ae 连字被打散**（ae 1.27/千字母（门 3.5）、quae 占比 0.019（门 0.80））：`quae`→`que`、`haec`→`hee`，**逐字引用会印出作者没写的形**",
        "file": "collectioncompl76rousgoog.txt"
      },
      "src-5d929d93a258": {
        "words": 87500,
        "diagnostic_est_eft": [
          2,
          632
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.8939；英文：锚 14.2<500.0，若强行读 0.3077；德语：锚 0.0<15.0，若强行读 0.9697）",
        "file": "collectioncompl78rousgoog.txt"
      },
      "src-6e07c3cd72a1": {
        "words": 20173,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1854.5,
            "panel_good": 171,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 171／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 171／讹形 0）",
        "file": "confessionsofjjr03904gut.txt"
      },
      "src-e7fc736e3e1b": {
        "words": 23708,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1965.2,
            "panel_good": 210,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 210／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 210／讹形 0）",
        "file": "confessionsofjjr03905gut.txt"
      },
      "src-62325ce7f5d5": {
        "words": 22902,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1927.3,
            "panel_good": 209,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 209／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 209／讹形 0）",
        "file": "confessionsofjjr03906gut.txt"
      },
      "src-321aadbefc89": {
        "words": 32992,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2246.9,
            "panel_good": 275,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 275／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 275／讹形 0）",
        "file": "confessionsofjjr03912gut.txt"
      },
      "src-568a90d14e6e": {
        "words": 279560,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2086.4,
            "panel_good": 2278,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2278／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2278／讹形 0）",
        "file": "confessionsofjjr03913gut.txt"
      },
      "src-9cb87f8a87da": {
        "words": 262091,
        "diagnostic_est_eft": [
          3143,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.8<15.0，若强行读 0.0045；英文：锚 1.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2500）",
        "file": "contratsocialou00rous.txt"
      },
      "src-6871d2e450ca": {
        "words": 124814,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2287.9,
            "panel_good": 1578,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1578／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1578／讹形 0）",
        "file": "cu31924014398154.txt"
      },
      "src-896ae63d7e1e": {
        "words": 67481,
        "diagnostic_est_eft": [
          568,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0035；英文：锚 432.3<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.3000）",
        "file": "cu31924027383284.txt"
      },
      "src-63c27e7d3e0f": {
        "words": 80898,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2119.6,
            "panel_good": 635,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 635／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 635／讹形 0）",
        "file": "cu31924027386915.txt"
      },
      "src-aaf22cfd258f": {
        "words": 51951,
        "diagnostic_est_eft": [
          1,
          323
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8256；英文：锚 6.5<500.0，若强行读 1.0000；德语：锚 0.2<15.0，若强行读 0.5238）",
        "file": "ddiscourssurlori00rous.txt"
      },
      "src-dd55dfcd5953": {
        "words": 98293,
        "diagnostic_est_eft": [
          6,
          1111
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.9003；英文：锚 6.5<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.8421）",
        "file": "dictionnairedemu02rous.txt"
      },
      "src-78d329fb5da1": {
        "words": 52556,
        "diagnostic_est_eft": [
          0,
          255
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.7978；英文：锚 6.7<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "discourssurlor00rous.txt"
      },
      "src-7de63f6c8842": {
        "words": 52822,
        "diagnostic_est_eft": [
          2,
          357
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.7901；英文：锚 7.0<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.6364）",
        "file": "discourssurlori00rous.txt"
      },
      "src-429979edb42e": {
        "words": 54704,
        "diagnostic_est_eft": [
          12,
          245
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.9100；英文：锚 26.7<500.0，若强行读 0.1818；德语：锚 0.0<15.0，若强行读 0.8824）",
        "file": "discourssurlori01rousgoog.txt"
      },
      "src-2173747b3a01": {
        "words": 52350,
        "diagnostic_est_eft": [
          5,
          260
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.9936；英文：锚 8.6<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.8750）",
        "file": "discourssurlorig00rous_0.txt"
      },
      "src-fa22bf802099": {
        "words": 51595,
        "diagnostic_est_eft": [
          20,
          633
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.9467；英文：锚 22.5<500.0，若强行读 0.1538；德语：锚 0.0<15.0，若强行读 0.7500）",
        "file": "ducontractsocia00rousgoog.txt"
      },
      "src-813765779d1f": {
        "words": 91899,
        "diagnostic_est_eft": [
          2,
          809
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.6845；英文：锚 4.1<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.7500）",
        "file": "ducontratsocialo02rous.txt"
      },
      "src-38cc190dcb5d": {
        "words": 81070,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1799.2,
            "panel_good": 39,
            "panel_bad": 608,
            "若无语种门会读到": 0.9397,
            "verdict": "不可用",
            "rate": 0.9397,
            "reason": "英文讹字率 0.9397（正形 39／讹形 608）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9397,
        "reason": "英文讹字率 0.9397（正形 39／讹形 608）",
        "file": "eloisaoraseries01rousgoog.txt"
      },
      "src-6cdd7d7004d8": {
        "words": 100533,
        "diagnostic_est_eft": [
          19,
          1040
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.5041；英文：锚 2.8<500.0，若强行读 1.0000；德语：锚 0.2<15.0，若强行读 0.7600）",
        "file": "espritmaximesetp00rous.txt"
      },
      "src-959e8b14de18": {
        "words": 13417,
        "diagnostic_est_eft": [
          0,
          94
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.6226；英文：锚 5.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "extraitduprojet00sain.txt"
      },
      "src-212bd671b070": {
        "words": 12723,
        "diagnostic_est_eft": [
          0,
          37
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.9836；英文：锚 7.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "extraitduprojetd00sain.txt"
      },
      "src-7bca5a65617d": {
        "words": 167077,
        "diagnostic_est_eft": [
          26,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2273.9,
            "panel_good": 2284,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2284／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2284／讹形 0）",
        "file": "frenchenglishphi34desc.txt"
      },
      "src-b34d6a25206b": {
        "words": 37139,
        "diagnostic_est_eft": [
          286,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0076；英文：锚 1.9<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.0000）",
        "file": "honneurspublicsr00pari.txt"
      },
      "src-a71c47686b3e": {
        "words": 19458,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2049.5,
            "panel_good": 0,
            "panel_bad": 197,
            "若无语种门会读到": 1.0,
            "verdict": "不可用",
            "rate": 1.0,
            "reason": "英文讹字率 1.0000（正形 0／讹形 197）"
          }
        },
        "verdict": "不可用",
        "rate": 1.0,
        "reason": "英文讹字率 1.0000（正形 0／讹形 197）",
        "file": "india.history.resource.111524.txt"
      },
      "src-1dd271d2186f": {
        "words": 74291,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2348.2,
            "panel_good": 631,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 631／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 631／讹形 0）",
        "file": "india.history.resource.94272.txt"
      },
      "src-9ab8e7a7e0e0": {
        "words": 158809,
        "diagnostic_est_eft": [
          1814,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 38.3<500.0，若强行读 0.0000；德语：锚 0.8<15.0，若强行读 0.0609）",
        "file": "jeanjacquesrous00text.txt"
      },
      "src-8f93e51a9549": {
        "words": 75583,
        "diagnostic_est_eft": [
          1,
          673
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.8<15.0，若强行读 0.9231；英文：锚 2.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "jjrousseaucitoy00rous.txt"
      },
      "src-ebf3a9b90c5f": {
        "words": 370680,
        "diagnostic_est_eft": [
          5043,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.0051；英文：锚 1.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2097）",
        "file": "mileoudelducatio00rous.txt"
      },
      "src-1f30bc1c5390": {
        "words": 4712,
        "diagnostic_est_eft": [
          0,
          31
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 1.0000；英文：锚 4.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "ninonlenclosmrsu00lenc.txt"
      },
      "src-e21555d11891": {
        "words": 10713,
        "diagnostic_est_eft": [
          0,
          95
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.9<15.0，若强行读 0.9138；英文：锚 5.6<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.8333）",
        "file": "observationsdeje00rous.txt"
      },
      "src-e03eef32a4bf": {
        "words": 102706,
        "diagnostic_est_eft": [
          1337,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0056；英文：锚 1.6<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2857）",
        "file": "oeuvrescomplt05rous.txt"
      },
      "src-7138b8135cc0": {
        "words": 126701,
        "diagnostic_est_eft": [
          1471,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.0096；英文：锚 2.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2381）",
        "file": "oeuvresdejjrous08rous.txt"
      },
      "src-6a19a301ae96": {
        "words": 107629,
        "diagnostic_est_eft": [
          1283,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.4<15.0，若强行读 0.0038；英文：锚 3.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0857）",
        "file": "oeuvresdejjrous09rous.txt"
      },
      "src-2fbcf83a4817": {
        "words": 132692,
        "diagnostic_est_eft": [
          1677,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0112；英文：锚 3.3<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.2308）",
        "file": "oeuvresdejjrous10rous.txt"
      },
      "src-295c799edb98": {
        "words": 92725,
        "diagnostic_est_eft": [
          2,
          823
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.5264；英文：锚 3.5<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.7000）",
        "file": "oeuvresdejjrouss01rous.txt"
      },
      "src-11f37d429b7a": {
        "words": 90668,
        "diagnostic_est_eft": [
          1,
          872
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.6384；英文：锚 3.2<500.0，若强行读 1.0000；德语：锚 0.0<15.0，若强行读 0.9231）",
        "file": "oeuvresdejjrouss12rous.txt"
      },
      "src-ad7e88b8ec10": {
        "words": 87875,
        "diagnostic_est_eft": [
          1,
          852
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.8068；英文：锚 3.5<500.0，若强行读 1.0000；德语：锚 0.1<15.0，若强行读 0.9444）",
        "file": "oeuvresdejjrouss15rous.txt"
      },
      "src-7274d87d1f72": {
        "words": 90241,
        "diagnostic_est_eft": [
          1,
          270
        ],
        "逐语域": {
          "拉丁": {
            "语域": "拉丁",
            "anchors_per_10k": 19.7,
            "panel_good": 91,
            "panel_bad": 380,
            "若无语种门会读到": 0.8068,
            "verdict": "不可用",
            "rate": 0.8068,
            "reason": "拉丁讹字率 0.8068（正形 91／讹形 380）"
          }
        },
        "ae_连字": {
          "ae_per_1000": 1.0,
          "quae": 16,
          "que": 970,
          "quae_ratio": 0.016,
          "判读": "**打散**",
          "理由": "ae 1.00/千字母（门 3.5）、quae 占比 0.016（门 0.80）"
        },
        "verdict": "不可用",
        "rate": 0.8068,
        "reason": "拉丁讹字率 0.8068（正形 91／讹形 380）　★ **但 ae 连字被打散**（ae 1.00/千字母（门 3.5）、quae 占比 0.016（门 0.80））：`quae`→`que`、`haec`→`hee`，**逐字引用会印出作者没写的形**",
        "file": "oeuvresdejjrouss22rous.txt"
      },
      "src-1ae5867e8c44": {
        "words": 16578,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1520.1,
            "panel_good": 101,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 101／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 101／讹形 0）",
        "file": "romanticelements00fole.txt"
      },
      "src-7c62154cfa36": {
        "words": 78291,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2126.0,
            "panel_good": 622,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 622／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 622／讹形 0）",
        "file": "rousseauandnatu00hudsgoog.txt"
      },
      "src-0f7f9723eb9e": {
        "words": 77750,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2155.8,
            "panel_good": 624,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 624／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 624／讹形 0）",
        "file": "rousseaunaturali0000unse_c8a6.txt"
      },
      "src-fd437884f0e0": {
        "words": 32175,
        "diagnostic_est_eft": [
          336,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.0000；英文：锚 27.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2500）",
        "file": "tudesurjjrousse00giragoog.txt"
      },
      "src-e671a5bcdd69": {
        "words": 42840,
        "diagnostic_est_eft": [
          399,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0097；英文：锚 1.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.5000）",
        "file": "tudesurltatm00bouguoft.txt"
      },
      "src-5a6c67b00ba5": {
        "words": 152231,
        "diagnostic_est_eft": [
          2040,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.2<15.0，若强行读 0.0040；英文：锚 1.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0857）",
        "file": "uvrescompltesd02rous.txt"
      },
      "src-1fcd4d865dbe": {
        "words": 384463,
        "diagnostic_est_eft": [
          4697,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.8<15.0，若强行读 0.0025；英文：锚 4.2<500.0，若强行读 0.0588；德语：锚 0.0<15.0，若强行读 0.2969）",
        "file": "uvrescompltesde04rousgoog.txt"
      },
      "src-da98705d1df6": {
        "words": 358188,
        "diagnostic_est_eft": [
          2884,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.0097；英文：锚 5.3<500.0，若强行读 0.0769；德语：锚 0.0<15.0，若强行读 0.1410）",
        "file": "uvrescompltesde07rousgoog.txt"
      },
      "src-ae284b9d4433": {
        "words": 51024,
        "diagnostic_est_eft": [
          26,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.0000；英文：锚 115.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "yhteiskuntasopim53593gut.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 103,
    "与台账不一致的道": [],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "corpus_cache": "未给 --cache，**自动使用 `raw`**（与本文件另外三处一致）",
    "quote_integrity_scope": "evals/judge_payload.v1.json 不在——**答案层未核验（不是通过）**；候选答案没落进工作区时，任何门都看不见它",
    "quote_integrity": "有引文未在语料中找到——**未命中不等于伪造**，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里",
    "shared_anchor": "evals/judge_payload.v1.json 不在——**同源引用未比对（不是通过）**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak": "evals/baseline.v1.json 不在——**表面特征泄题未核（不是通过）**；基线只存在于人物工作目录里，没落进工作区，**门看不见它**",
    "unsourced_names": "缺 --cache 或 judge_payload，**承重人名未核（不是通过）**",
    "self_counts": "evals/judge_payload.v1.json 不在——**自报字数未核（不是通过）**",
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 34,
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
    "可用来源": 91,
    "**按内容去重后的作品数**": 69,
    "虚高": 1.319,
    "未声明的重复对": 0,
    "已声明的重复对": 12,
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
        "引文数": 6,
        "核过": 6,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 2,
        "核过": 2,
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
        "引文数": 2,
        "核过": 2,
        "**对不上**": []
      }
    },
    "合计": "10 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 12,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 94,
    "train 源总数": 103,
    "本人所著字节": 58392542,
    "train 总字节": 61787782,
    "own_voice_ratio": 0.945,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 9587629,
    "**判据说未核验的**": 70,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-fc4911a43495",
        "原因": "语种判为 **de**（en=0.001 de=0.082 fr=0.004）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-0614303d6af4",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.057）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8a0ad52c5d77",
        "原因": "语种判为 **de**（en=0.000 de=0.111 fr=0.007）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-bf7ad6ba0680",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.057）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-d173b2dabfe0",
        "原因": "语种判为 **de**（en=0.000 de=0.125 fr=0.005）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-f1d1ffcf7f5e",
        "原因": "语种判为 **de**（en=0.000 de=0.122 fr=0.005）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-3c91b85250af",
        "原因": "语种判为 **de**（en=0.000 de=0.122 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-f7c1a948f032",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.062）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 36.85,
    "**立场句/万字**": 0.28,
    "其中不含第一人称的": 146,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 91,
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
    "第一人称覆盖率": 0.656,
    "状态": "无候选（第一人称覆盖率 0.656）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-rousseau-178/workspaces/jean-jacques-rousseau/evidence/source-ledger.jsonl",
    "一手份数": 79,
    "台账总份数": 91,
    "一手占比": 0.8681,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 103,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-fc4911a43495 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 103,
    "声称公有领域": 0,
    "不声称（不判）": 103,
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
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 103,
    "**`title` 就是文件名**": 0,
    "真书目题名": 103,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 25,
    "有一边没年份": 78,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 34,
  "claims_active": 34,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 34,
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
    "实测声明": 0,
    "同段带数": 0,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0,
    "状态": "**一处实测声明都没扫到——本次什么也没检查，不构成通过。**合成阶段常态如此（断言层通常不写「我量过」），**但发布阶段若仍是 0，要去看是不是扫错了单元。**"
  },
  "evidence_per_claim": {
    "断言条数": 34,
    "source_ids": "逐条各异（非空 34/34，不同取值 19）",
    "evidence_clusters": "逐条各异（非空 34/34，不同取值 29）",
    "counter_source_ids": "整批都空（非空 0/34，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 1,
    "作品组数（连通分量，仅供参考）": 78,
    "来源数": 103,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 31,
    "挂错作品": 7,
    "版本差（作品对、逐字文本取自另一版）": 1,
    "不唯一（同句见于多份源，挂错也照样绿）": 5,
    "取不到正文的源": 0,
    "例": [
      "clm-e50ec62138f4：挂 ['bim_eighteenth-century_discours-sur-lorigine-e_rousseau-jean-jacques_1782.txt', 'oeuvresdejjrouss15rous.txt'] → 实 ['1846oeuvrescom02rousuoft.txt', 'mileoudelducatio00rous.txt', 'uvrescompltesde04rousgoog.txt']",
      "clm-e50ec62138f4：挂 ['bim_eighteenth-century_discours-sur-lorigine-e_rousseau-jean-jacques_1782.txt', 'oeuvresdejjrouss15rous.txt'] → 实 ['bub_gb_3DbL7IDH2jIC.txt', 'contratsocialou00rous.txt', 'cu31924027383284.txt', 'ddiscourssurlori00rous.txt', 'discourssurlori01rousgoog.txt', 'discourssurlorig00rous_0.txt', 'uvrescompltesde04rousgoog.txt']",
      "clm-e50ec62138f4：挂 ['bim_eighteenth-century_discours-sur-lorigine-e_rousseau-jean-jacques_1782.txt', 'oeuvresdejjrouss15rous.txt'] → 实 ['bub_gb_3DbL7IDH2jIC.txt', 'contratsocialou00rous.txt', 'ddiscourssurlori00rous.txt', 'discourssurlor00rous.txt', 'discourssurlorig00rous_0.txt']",
      "clm-2915b76381f7：挂 ['1782collectionco10rous.txt', 'discourssurlori00rous.txt'] → 实 ['discourssurlorig00rous_0.txt']",
      "clm-2cbde79560b4：挂 ['discourssurlor00rous.txt', 'discourssurlori00rous.txt'] → 实 ['bub_gb_3DbL7IDH2jIC.txt', 'discourssurlori01rousgoog.txt', 'discourssurlorig00rous_0.txt', 'espritmaximesetp00rous.txt', 'uvrescompltesde04rousgoog.txt']",
      "clm-ff3c8af70708：挂 ['bim_eighteenth-century_discours-sur-lorigine-e_rousseau-jean-jacques_1782.txt', 'oeuvresdejjrouss15rous.txt'] → 实 ['1846oeuvrescom02rousuoft.txt', 'mileoudelducatio00rous.txt', 'uvrescompltesde04rousgoog.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-rousseau-178/workspaces/jean-jacques-rousseau/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-e2d31c14b445",
      "           **他的自证模型：先给方法的独特性，再把自己当样本。** 《忏悔录》里方法（`une entreprise qui n'eut jamais d'exemple`）在前，样本（…",
      "",
      "低于 10% 的 45 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-rousseau-178/workspaces/jean-jacques-rousseau/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-rousseau-178/workspaces/jean-jacques-rousseau/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.7912,
  "baseline_overall": 0.5094,
  "candidate_baseline_delta": 0.2819,
  "suite_candidate_means": {
    "known": 0.94,
    "boundary": 0.935,
    "voice": 0.825,
    "trajectory": 0.525,
    "contrast": 0.6,
    "fact-preservation": 0.9,
    "style-decoy": 0.675,
    "task-completion": 0.6,
    "planning-fidelity": 0.825,
    "tool-use": 0.91,
    "capability-calibration": 0.6,
    "refusal-stop": 0.8,
    "long-horizon": 0.7,
    "identity-routing": 0.925,
    "anonymous-fidelity": 0.95,
    "token-efficiency": 0.95
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "**被单独一道题拖住**": [
      "fact-preservation　均分 0.9000 < 0.93　**被 jjr-fact-preservation-01（0.850）一道拖住——去掉它 0.9500 ≥ 0.93**"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 24/34 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 10 未纳入）",
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

- None

## Warnings

- `corpus.longs-corruption`: **22 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-fc4911a43495` 10066336bsb.txt —— 德语讹字率 0.6415（正形 365／讹形 653），**不可做逐字引文**
- `corpus.unexamined-band`: **1/103 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
