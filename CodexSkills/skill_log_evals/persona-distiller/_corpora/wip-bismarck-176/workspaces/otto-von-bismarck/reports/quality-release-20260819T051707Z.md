# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-bismarck-176/workspaces/otto-von-bismarck`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T05:17:07Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 70,
    "claims": 25
  },
  "sources_total": 70,
  "sources_train": 60,
  "sources_usable_train": 60,
  "sources_holdout": 10,
  "primary_sources": 53,
  "primary_ratio": 0.8833,
  "lane_source_counts": {
    "writings": 15,
    "conversations": 16,
    "expression": 12,
    "external": 7,
    "decisions": 1,
    "timeline": 9
  },
  "authorship": {
    "P1 声称为本人所著": 63,
    "已证实归属": 16,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "47 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 70,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干编本题名页逐字（`src-ee3963b8a368`，Fraktur）：`Gedanken und Erinnerungen Von Otto Fürſt ",
    "citation": "archive.org item（各 source_id 的 locator 与 sha256 记于 source-ledger.jsonl）",
    "争议篇目数": 0,
    "P1 声称本人所著": 63,
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
    "usable_train": 60,
    "fact 类条数": 13,
    "**人物事实**（计入）": 13,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 12,
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
    "已查语料件": 70,
    "含同形字的源": 2,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "30081009593108.txt",
        "非拉丁字符": 2,
        "全同形字词": 0,
        "样例": [
          "SSνν 读作 SSvv"
        ]
      },
      {
        "源": "bismarcksbriefes00bism.txt",
        "非拉丁字符": 1,
        "全同形字词": 0,
        "样例": [
          "αf 读作 αf"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 50,
      "混杂": 3,
      "未核": 1,
      "干净": 14,
      "不适用": 2
    },
    "逐份": {
      "src-0c3daab5fdcf": {
        "words": 120932,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 563.6,
            "panel_good": 148,
            "panel_bad": 158,
            "若无语种门会读到": 0.5163,
            "verdict": "不可用",
            "rate": 0.5163,
            "reason": "德语讹字率 0.5163（正形 148／讹形 158）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2270,
          "变音符每千词": 110.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5163,
        "reason": "德语讹字率 0.5163（正形 148／讹形 158）",
        "file": "00078127bsb.txt"
      },
      "src-8fee88c1082b": {
        "words": 55145,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 575.8,
            "panel_good": 212,
            "panel_bad": 117,
            "若无语种门会读到": 0.3556,
            "verdict": "不可用",
            "rate": 0.3556,
            "reason": "德语讹字率 0.3556（正形 212／讹形 117）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1032,
          "变音符每千词": 104.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.3556,
        "reason": "德语讹字率 0.3556（正形 212／讹形 117）",
        "file": "10558638bsb.txt"
      },
      "src-8422ffb869a3": {
        "words": 109011,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 580.7,
            "panel_good": 420,
            "panel_bad": 121,
            "若无语种门会读到": 0.2237,
            "verdict": "不可用",
            "rate": 0.2237,
            "reason": "德语讹字率 0.2237（正形 420／讹形 121）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2522,
          "变音符每千词": 103.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.2237,
        "reason": "德语讹字率 0.2237（正形 420／讹形 121）",
        "file": "10558639bsb.txt"
      },
      "src-cfe297da4fc6": {
        "words": 21906,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 507.6,
            "panel_good": 90,
            "panel_bad": 195,
            "若无语种门会读到": 0.6842,
            "verdict": "不可用",
            "rate": 0.6842,
            "reason": "德语讹字率 0.6842（正形 90／讹形 195）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 377,
          "变音符每千词": 104.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6842,
        "reason": "德语讹字率 0.6842（正形 90／讹形 195）",
        "file": "10629304bsb.txt"
      },
      "src-32e1e087788f": {
        "words": 27760,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 585.0,
            "panel_good": 69,
            "panel_bad": 52,
            "若无语种门会读到": 0.4298,
            "verdict": "不可用",
            "rate": 0.4298,
            "reason": "德语讹字率 0.4298（正形 69／讹形 52）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 625,
          "变音符每千词": 103.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.4298,
        "reason": "德语讹字率 0.4298（正形 69／讹形 52）",
        "file": "11166432bsb.txt"
      },
      "src-1384279b1926": {
        "words": 142235,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 526.2,
            "panel_good": 649,
            "panel_bad": 234,
            "若无语种门会读到": 0.265,
            "verdict": "不可用",
            "rate": 0.265,
            "reason": "德语讹字率 0.2650（正形 649／讹形 234）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2784,
          "变音符每千词": 104.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.265,
        "reason": "德语讹字率 0.2650（正形 649／讹形 234）",
        "file": "11281959bsb.txt"
      },
      "src-fb8618283f87": {
        "words": 109228,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 581.2,
            "panel_good": 418,
            "panel_bad": 91,
            "若无语种门会读到": 0.1788,
            "verdict": "混杂",
            "rate": 0.1788,
            "reason": "德语讹字率 0.1788（正形 418／讹形 91）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2531,
          "变音符每千词": 103.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.1788,
        "reason": "德语讹字率 0.1788（正形 418／讹形 91）",
        "file": "11281960bsb.txt"
      },
      "src-5e838b6da534": {
        "words": 39139,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 520.7,
            "panel_good": 175,
            "panel_bad": 34,
            "若无语种门会读到": 0.1627,
            "verdict": "混杂",
            "rate": 0.1627,
            "reason": "德语讹字率 0.1627（正形 175／讹形 34）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 792,
          "变音符每千词": 100.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.1627,
        "reason": "德语讹字率 0.1627（正形 175／讹形 34）",
        "file": "11281961bsb.txt"
      },
      "src-4070865edf64": {
        "words": 50516,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 689.9,
            "panel_good": 42,
            "panel_bad": 152,
            "若无语种门会读到": 0.7835,
            "verdict": "不可用",
            "rate": 0.7835,
            "reason": "德语讹字率 0.7835（正形 42／讹形 152）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1103,
          "变音符每千词": 91.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7835,
        "reason": "德语讹字率 0.7835（正形 42／讹形 152）",
        "file": "11332890bsb.txt"
      },
      "src-60292ea8f3f0": {
        "words": 220140,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 545.2,
            "panel_good": 1056,
            "panel_bad": 317,
            "若无语种门会读到": 0.2309,
            "verdict": "不可用",
            "rate": 0.2309,
            "reason": "德语讹字率 0.2309（正形 1056／讹形 317）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4586,
          "变音符每千词": 102.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.2309,
        "reason": "德语讹字率 0.2309（正形 1056／讹形 317）",
        "file": "11358069bsb.txt"
      },
      "src-6dd34d18a1cc": {
        "words": 230983,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 593.6,
            "panel_good": 681,
            "panel_bad": 303,
            "若无语种门会读到": 0.3079,
            "verdict": "不可用",
            "rate": 0.3079,
            "reason": "德语讹字率 0.3079（正形 681／讹形 303）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 5349,
          "变音符每千词": 101.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.3079,
        "reason": "德语讹字率 0.3079（正形 681／讹形 303）",
        "file": "11358070bsb.txt"
      },
      "src-f7531b21c0d5": {
        "words": 330854,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 597.5,
            "panel_good": 703,
            "panel_bad": 362,
            "若无语种门会读到": 0.3399,
            "verdict": "不可用",
            "rate": 0.3399,
            "reason": "德语讹字率 0.3399（正形 703／讹形 362）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 7510,
          "变音符每千词": 98.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.3399,
        "reason": "德语讹字率 0.3399（正形 703／讹形 362）",
        "file": "11358071bsb.txt"
      },
      "src-6bb7f031f746": {
        "words": 167287,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 585.2,
            "panel_good": 745,
            "panel_bad": 309,
            "若无语种门会读到": 0.2932,
            "verdict": "不可用",
            "rate": 0.2932,
            "reason": "德语讹字率 0.2932（正形 745／讹形 309）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3636,
          "变音符每千词": 96.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.2932,
        "reason": "德语讹字率 0.2932（正形 745／讹形 309）",
        "file": "11358072bsb.txt"
      },
      "src-e69889a403d9": {
        "words": 290241,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 555.6,
            "panel_good": 1063,
            "panel_bad": 598,
            "若无语种门会读到": 0.36,
            "verdict": "不可用",
            "rate": 0.36,
            "reason": "德语讹字率 0.3600（正形 1063／讹形 598）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 5840,
          "变音符每千词": 109.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.36,
        "reason": "德语讹字率 0.3600（正形 1063／讹形 598）",
        "file": "30081009592969.txt"
      },
      "src-6ab5bd55e5aa": {
        "words": 356335,
        "diagnostic_est_eft": [
          11,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 519.6,
            "panel_good": 456,
            "panel_bad": 490,
            "若无语种门会读到": 0.518,
            "verdict": "不可用",
            "rate": 0.518,
            "reason": "德语讹字率 0.5180（正形 456／讹形 490）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 6770,
          "变音符每千词": 119.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.518,
        "reason": "德语讹字率 0.5180（正形 456／讹形 490）",
        "file": "30081009592985.txt"
      },
      "src-0e926803e259": {
        "words": 356545,
        "diagnostic_est_eft": [
          17,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 506.7,
            "panel_good": 451,
            "panel_bad": 517,
            "若无语种门会读到": 0.5341,
            "verdict": "不可用",
            "rate": 0.5341,
            "reason": "德语讹字率 0.5341（正形 451／讹形 517）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 6658,
          "变音符每千词": 120.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5341,
        "reason": "德语讹字率 0.5341（正形 451／讹形 517）",
        "file": "30081009592993.txt"
      },
      "src-5344423f6864": {
        "words": 243533,
        "diagnostic_est_eft": [
          117,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 483.5,
            "panel_good": 189,
            "panel_bad": 218,
            "若无语种门会读到": 0.5356,
            "verdict": "不可用",
            "rate": 0.5356,
            "reason": "德语讹字率 0.5356（正形 189／讹形 218）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4063,
          "变音符每千词": 100.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5356,
        "reason": "德语讹字率 0.5356（正形 189／讹形 218）",
        "file": "30081009593009.txt"
      },
      "src-8d82f38dec92": {
        "words": 378137,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 596.8,
            "panel_good": 1391,
            "panel_bad": 573,
            "若无语种门会读到": 0.2918,
            "verdict": "不可用",
            "rate": 0.2918,
            "reason": "德语讹字率 0.2918（正形 1391／讹形 573）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 8700,
          "变音符每千词": 104.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.2918,
        "reason": "德语讹字率 0.2918（正形 1391／讹形 573）",
        "file": "30081009593033.txt"
      },
      "src-c936342d8eb3": {
        "words": 289188,
        "diagnostic_est_eft": [
          23,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 495.5,
            "panel_good": 363,
            "panel_bad": 287,
            "若无语种门会读到": 0.4415,
            "verdict": "不可用",
            "rate": 0.4415,
            "reason": "德语讹字率 0.4415（正形 363／讹形 287）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 5498,
          "变音符每千词": 114.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.4415,
        "reason": "德语讹字率 0.4415（正形 363／讹形 287）",
        "file": "30081009593066.txt"
      },
      "src-59d9e01628d7": {
        "words": 257314,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 550.1,
            "panel_good": 168,
            "panel_bad": 351,
            "若无语种门会读到": 0.6763,
            "verdict": "不可用",
            "rate": 0.6763,
            "reason": "德语讹字率 0.6763（正形 168／讹形 351）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4877,
          "变音符每千词": 115.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6763,
        "reason": "德语讹字率 0.6763（正形 168／讹形 351）",
        "file": "30081009593074.txt"
      },
      "src-12e08ee46874": {
        "words": 382413,
        "diagnostic_est_eft": [
          5,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 605.1,
            "panel_good": 1610,
            "panel_bad": 886,
            "若无语种门会读到": 0.355,
            "verdict": "不可用",
            "rate": 0.355,
            "reason": "德语讹字率 0.3550（正形 1610／讹形 886）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 8901,
          "变音符每千词": 99.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.355,
        "reason": "德语讹字率 0.3550（正形 1610／讹形 886）",
        "file": "30081009593090.txt"
      },
      "src-d3f5941749db": {
        "words": 398671,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 640.4,
            "panel_good": 1857,
            "panel_bad": 1243,
            "若无语种门会读到": 0.401,
            "verdict": "不可用",
            "rate": 0.401,
            "reason": "德语讹字率 0.4010（正形 1857／讹形 1243）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 9838,
          "变音符每千词": 101.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.401,
        "reason": "德语讹字率 0.4010（正形 1857／讹形 1243）",
        "file": "30081009593108.txt"
      },
      "src-cb0086273a23": {
        "words": 6749,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 385.2,
            "panel_good": 51,
            "panel_bad": 35,
            "若无语种门会读到": 0.407,
            "verdict": "不可用",
            "rate": 0.407,
            "reason": "德语讹字率 0.4070（正形 51／讹形 35）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 62,
          "变音符每千词": 90.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.407,
        "reason": "德语讹字率 0.4070（正形 51／讹形 35）",
        "file": "anhangzudengeda01bismgoog.txt"
      },
      "src-fd24cdf65a3c": {
        "words": 126319,
        "diagnostic_est_eft": [
          0,
          97
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 60.2,
            "panel_good": 109,
            "panel_bad": 633,
            "若无语种门会读到": 0.8531,
            "verdict": "不可用",
            "rate": 0.8531,
            "reason": "德语讹字率 0.8531（正形 109／讹形 633）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 0,
          "变音符每千词": 82.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8531,
        "reason": "德语讹字率 0.8531（正形 109／讹形 633）",
        "file": "anhangzudengeda01schlgoog.txt"
      },
      "src-49458fc25471": {
        "words": 161467,
        "diagnostic_est_eft": [
          26,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 498.7,
            "panel_good": 637,
            "panel_bad": 828,
            "若无语种门会读到": 0.5652,
            "verdict": "不可用",
            "rate": 0.5652,
            "reason": "德语讹字率 0.5652（正形 637／讹形 828）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2794,
          "变音符每千词": 107.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5652,
        "reason": "德语讹字率 0.5652（正形 637／讹形 828）",
        "file": "anhangzudengedan02bism.txt"
      },
      "src-e4631d12e4d3": {
        "words": 221401,
        "diagnostic_est_eft": [
          5,
          30
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 66.4,
            "panel_good": 324,
            "panel_bad": 1792,
            "若无语种门会读到": 0.8469,
            "verdict": "不可用",
            "rate": 0.8469,
            "reason": "德语讹字率 0.8469（正形 324／讹形 1792）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 10,
          "变音符每千词": 109.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8469,
        "reason": "德语讹字率 0.8469（正形 324／讹形 1792）",
        "file": "bismarckbrief00bism.txt"
      },
      "src-a3a876342810": {
        "words": 221247,
        "diagnostic_est_eft": [
          5,
          41
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 66.2,
            "panel_good": 312,
            "panel_bad": 1789,
            "若无语种门会读到": 0.8515,
            "verdict": "不可用",
            "rate": 0.8515,
            "reason": "德语讹字率 0.8515（正形 312／讹形 1789）"
          }
        },
        "德语附加": {
          "h→b率": 0.9231,
          "h→b样本": 13,
          "变音符每千词": 109.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8515,
        "reason": "德语讹字率 0.8515（正形 312／讹形 1789）",
        "file": "bismarckbriefe00bism.txt"
      },
      "src-2b8fce1e18a9": {
        "words": 219658,
        "diagnostic_est_eft": [
          5,
          34
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 77.0,
            "panel_good": 159,
            "panel_bad": 1604,
            "若无语种门会读到": 0.9098,
            "verdict": "不可用",
            "rate": 0.9098,
            "reason": "德语讹字率 0.9098（正形 159／讹形 1604）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 0,
          "变音符每千词": 113.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9098,
        "reason": "德语讹字率 0.9098（正形 159／讹形 1604）",
        "file": "bismarckbriefe00kohlgoog.txt"
      },
      "src-050c42f40fa7": {
        "words": 54000,
        "diagnostic_est_eft": [
          1,
          4
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 90.4,
            "panel_good": 52,
            "panel_bad": 404,
            "若无语种门会读到": 0.886,
            "verdict": "不可用",
            "rate": 0.886,
            "reason": "德语讹字率 0.8860（正形 52／讹形 404）"
          }
        },
        "德语附加": {
          "h→b率": 0.125,
          "h→b样本": 16,
          "变音符每千词": 84.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.886,
        "reason": "德语讹字率 0.8860（正形 52／讹形 404）",
        "file": "bismarckbriefeo00bismgoog.txt"
      },
      "src-c730cce1d709": {
        "words": 3983,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1857.9,
            "panel_good": 18,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 18 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 18 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bismarckforsilve00bism.txt"
      },
      "src-5341320bb76e": {
        "words": 130340,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2266.5,
            "panel_good": 959,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 959／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 959／讹形 0）",
        "file": "bismarckmanands00vongoog.txt"
      },
      "src-bc26d93528d9": {
        "words": 115280,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2248.9,
            "panel_good": 707,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 707／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 707／讹形 0）",
        "file": "bismarckmanstat03butlgoog.txt"
      },
      "src-b906aa637e84": {
        "words": 127911,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2302.8,
            "panel_good": 952,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 952／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 952／讹形 0）",
        "file": "bismarckmanstate01bism.txt"
      },
      "src-5060f8551a32": {
        "words": 24786,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1870.8,
            "panel_good": 203,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 203／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 203／讹形 0）",
        "file": "bismarckmanstate01bismiala.txt"
      },
      "src-9f19a63ddd34": {
        "words": 127302,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2303.6,
            "panel_good": 950,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 950／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 950／讹形 0）",
        "file": "bismarckmanstate01bismuoft.txt"
      },
      "src-05d3fcaba186": {
        "words": 113704,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2348.7,
            "panel_good": 716,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 716／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 716／讹形 0）",
        "file": "bismarckmanstate02bismuoft.txt"
      },
      "src-e08ec7c1c903": {
        "words": 228674,
        "diagnostic_est_eft": [
          2,
          15
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 43.2,
            "panel_good": 389,
            "panel_bad": 1807,
            "若无语种门会读到": 0.8229,
            "verdict": "不可用",
            "rate": 0.8229,
            "reason": "德语讹字率 0.8229（正形 389／讹形 1807）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 0,
          "变音符每千词": 118.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8229,
        "reason": "德语讹字率 0.8229（正形 389／讹形 1807）",
        "file": "bismarckreden18400bismuoft.txt"
      },
      "src-591ee96df2aa": {
        "words": 31594,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 679.2,
            "panel_good": 24,
            "panel_bad": 92,
            "若无语种门会读到": 0.7931,
            "verdict": "不可用",
            "rate": 0.7931,
            "reason": "德语讹字率 0.7931（正形 24／讹形 92）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 759,
          "变音符每千词": 94.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7931,
        "reason": "德语讹字率 0.7931（正形 24／讹形 92）",
        "file": "bismarcksbriefes00bism.txt"
      },
      "src-7211dc69ad69": {
        "words": 25334,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1868.2,
            "panel_good": 215,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 215／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 215／讹形 0）",
        "file": "bismarcksletter00bismgoog.txt"
      },
      "src-077bc686aed9": {
        "words": 182212,
        "diagnostic_est_eft": [
          0,
          29
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 62.2,
            "panel_good": 56,
            "panel_bad": 834,
            "若无语种门会读到": 0.9371,
            "verdict": "不可用",
            "rate": 0.9371,
            "reason": "德语讹字率 0.9371（正形 56／讹形 834）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 12,
          "变音符每千词": 106.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9371,
        "reason": "德语讹字率 0.9371（正形 56／讹形 834）",
        "file": "bismarcksstaats00rogoog.txt"
      },
      "src-ffbdfc0cab93": {
        "words": 104476,
        "diagnostic_est_eft": [
          8,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2077.9,
            "panel_good": 1170,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1170／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1170／讹形 0）",
        "file": "bismarckstableta01bism_0.txt"
      },
      "src-2ce0977abf57": {
        "words": 37311,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 591.8,
            "panel_good": 66,
            "panel_bad": 77,
            "若无语种门会读到": 0.5385,
            "verdict": "不可用",
            "rate": 0.5385,
            "reason": "德语讹字率 0.5385（正形 66／讹形 77）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 778,
          "变音符每千词": 33.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5385,
        "reason": "德语讹字率 0.5385（正形 66／讹形 77）",
        "file": "bismarckundste00bism.txt"
      },
      "src-cde195c6fb0f": {
        "words": 47336,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 623.4,
            "panel_good": 36,
            "panel_bad": 148,
            "若无语种门会读到": 0.8043,
            "verdict": "不可用",
            "rate": 0.8043,
            "reason": "德语讹字率 0.8043（正形 36／讹形 148）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1050,
          "变音符每千词": 90.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8043,
        "reason": "德语讹字率 0.8043（正形 36／讹形 148）",
        "file": "briefeottosvonbi00bismuoft.txt"
      },
      "src-c77aa5d3c4a5": {
        "words": 281328,
        "diagnostic_est_eft": [
          16,
          44
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 73.9,
            "panel_good": 321,
            "panel_bad": 2648,
            "若无语种门会读到": 0.8919,
            "verdict": "不可用",
            "rate": 0.8919,
            "reason": "德语讹字率 0.8919（正形 321／讹形 2648）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1,
          "变音符每千词": 86.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8919,
        "reason": "德语讹字率 0.8919（正形 321／讹形 2648）",
        "file": "briefeseinebarau00bismuoft.txt"
      },
      "src-83f0e820c3b2": {
        "words": 146233,
        "diagnostic_est_eft": [
          8,
          11
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 114.2,
            "panel_good": 428,
            "panel_bad": 1027,
            "若无语种门会读到": 0.7058,
            "verdict": "不可用",
            "rate": 0.7058,
            "reason": "德语讹字率 0.7058（正形 428／讹形 1027）"
          }
        },
        "德语附加": {
          "h→b率": 0.0121,
          "h→b样本": 912,
          "变音符每千词": 123.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7058,
        "reason": "德语讹字率 0.7058（正形 428／讹形 1027）",
        "file": "bub_gb_-a0PAAAAQAAJ.txt"
      },
      "src-eabd5cdf8dff": {
        "words": 86867,
        "diagnostic_est_eft": [
          5,
          24
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 58.2,
            "panel_good": 59,
            "panel_bad": 385,
            "若无语种门会读到": 0.8671,
            "verdict": "不可用",
            "rate": 0.8671,
            "reason": "德语讹字率 0.8671（正形 59／讹形 385）"
          }
        },
        "德语附加": {
          "h→b率": 0.8438,
          "h→b样本": 32,
          "变音符每千词": 104.1,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8671,
        "reason": "德语讹字率 0.8671（正形 59／讹形 385）　★ **长 s 之外还坏了**：**h→b 讹变 84.4%**（`nicht`→`nicbt` 这一族，样本 32）——逐字引用会印出作者没写的形",
        "file": "bub_gb_BbIPAAAAQAAJ.txt"
      },
      "src-4addccb839e7": {
        "words": 288275,
        "diagnostic_est_eft": [
          21,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 481.3,
            "panel_good": 945,
            "panel_bad": 2068,
            "若无语种门会读到": 0.6864,
            "verdict": "不可用",
            "rate": 0.6864,
            "reason": "德语讹字率 0.6864（正形 945／讹形 2068）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4006,
          "变音符每千词": 98.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6864,
        "reason": "德语讹字率 0.6864（正形 945／讹形 2068）",
        "file": "bub_gb_BkIPAAAAYAAJ.txt"
      },
      "src-87688f01cbef": {
        "words": 108946,
        "diagnostic_est_eft": [
          775,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0042；英文：锚 1.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.4000）",
        "file": "bub_gb_CWAPAAAAYAAJ.txt"
      },
      "src-4e9f21cba8c8": {
        "words": 99597,
        "diagnostic_est_eft": [
          20,
          15
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 62.8,
            "panel_good": 34,
            "panel_bad": 319,
            "若无语种门会读到": 0.9037,
            "verdict": "不可用",
            "rate": 0.9037,
            "reason": "德语讹字率 0.9037（正形 34／讹形 319）"
          }
        },
        "德语附加": {
          "h→b率": 0.2,
          "h→b样本": 20,
          "变音符每千词": 101.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9037,
        "reason": "德语讹字率 0.9037（正形 34／讹形 319）",
        "file": "bub_gb_KsNVAAAAYAAJ.txt"
      },
      "src-b943cca7e9dd": {
        "words": 216489,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 507.4,
            "panel_good": 437,
            "panel_bad": 1052,
            "若无语种门会读到": 0.7065,
            "verdict": "不可用",
            "rate": 0.7065,
            "reason": "德语讹字率 0.7065（正形 437／讹形 1052）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2650,
          "变音符每千词": 107.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7065,
        "reason": "德语讹字率 0.7065（正形 437／讹形 1052）",
        "file": "bub_gb_NjNDAQAAMAAJ.txt"
      },
      "src-df2392e49517": {
        "words": 14609,
        "diagnostic_est_eft": [
          0,
          12
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 89.0,
            "panel_good": 11,
            "panel_bad": 111,
            "若无语种门会读到": 0.9098,
            "verdict": "不可用",
            "rate": 0.9098,
            "reason": "德语讹字率 0.9098（正形 11／讹形 111）"
          }
        },
        "德语附加": {
          "h→b率": 0.3333,
          "h→b样本": 39,
          "变音符每千词": 108.7,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9098,
        "reason": "德语讹字率 0.9098（正形 11／讹形 111）　★ **长 s 之外还坏了**：**h→b 讹变 33.3%**（`nicht`→`nicbt` 这一族，样本 39）——逐字引用会印出作者没写的形",
        "file": "bub_gb_akpzLZLxvP4C.txt"
      },
      "src-a7465c6d3b41": {
        "words": 19857,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1775.2,
            "panel_good": 113,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 113／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 113／讹形 0）",
        "file": "cihm_77460.txt"
      },
      "src-6e4619dd930d": {
        "words": 200551,
        "diagnostic_est_eft": [
          1043,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 1.2<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0588）",
        "file": "correspondancedi01bism.txt"
      },
      "src-80c5c087a2c5": {
        "words": 69179,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2158.7,
            "panel_good": 516,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 516／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 516／讹形 0）",
        "file": "correspondenceof00bismuoft.txt"
      },
      "src-8d914155d0cc": {
        "words": 69165,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2159.5,
            "panel_good": 515,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 515／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 515／讹形 0）",
        "file": "correspondenceof02bismuoft.txt"
      },
      "src-9bc38d196726": {
        "words": 179006,
        "diagnostic_est_eft": [
          6,
          18
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 49.4,
            "panel_good": 195,
            "panel_bad": 1176,
            "若无语种门会读到": 0.8578,
            "verdict": "不可用",
            "rate": 0.8578,
            "reason": "德语讹字率 0.8578（正形 195／讹形 1176）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 2,
          "变音符每千词": 151.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8578,
        "reason": "德语讹字率 0.8578（正形 195／讹形 1176）",
        "file": "diepolitischenre01bismuoft.txt"
      },
      "src-5da4f77d2f65": {
        "words": 196700,
        "diagnostic_est_eft": [
          1,
          11
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 41.9,
            "panel_good": 512,
            "panel_bad": 1204,
            "若无语种门会读到": 0.7016,
            "verdict": "不可用",
            "rate": 0.7016,
            "reason": "德语讹字率 0.7016（正形 512／讹形 1204）"
          }
        },
        "德语附加": {
          "h→b率": 0.4,
          "h→b样本": 5,
          "变音符每千词": 152.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7016,
        "reason": "德语讹字率 0.7016（正形 512／讹形 1204）",
        "file": "diepolitischenre02bismuoft.txt"
      },
      "src-14f6f7a4c80d": {
        "words": 317321,
        "diagnostic_est_eft": [
          0,
          12
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 65.2,
            "panel_good": 394,
            "panel_bad": 2509,
            "若无语种门会读到": 0.8643,
            "verdict": "不可用",
            "rate": 0.8643,
            "reason": "德语讹字率 0.8643（正形 394／讹形 2509）"
          }
        },
        "德语附加": {
          "h→b率": 0.0769,
          "h→b样本": 13,
          "变音符每千词": 123.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8643,
        "reason": "德语讹字率 0.8643（正形 394／讹形 2509）",
        "file": "dieredendesgraf00bismgoog.txt"
      },
      "src-ee3963b8a368": {
        "words": 71210,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 548.7,
            "panel_good": 74,
            "panel_bad": 12,
            "若无语种门会读到": 0.1395,
            "verdict": "混杂",
            "rate": 0.1395,
            "reason": "德语讹字率 0.1395（正形 74／讹形 12）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1197,
          "变音符每千词": 108.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.1395,
        "reason": "德语讹字率 0.1395（正形 74／讹形 12）",
        "file": "erinnerungundged00bism.txt"
      },
      "src-e8a9b012e601": {
        "words": 467622,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 526.4,
            "panel_good": 1516,
            "panel_bad": 5138,
            "若无语种门会读到": 0.7722,
            "verdict": "不可用",
            "rate": 0.7722,
            "reason": "德语讹字率 0.7722（正形 1516／讹形 5138）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 7553,
          "变音符每千词": 121.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7722,
        "reason": "德语讹字率 0.7722（正形 1516／讹形 5138）",
        "file": "frstbismarcksei01bismgoog.txt"
      },
      "src-e331f81691cb": {
        "words": 188088,
        "diagnostic_est_eft": [
          5,
          20
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 45.8,
            "panel_good": 225,
            "panel_bad": 1174,
            "若无语种门会读到": 0.8392,
            "verdict": "不可用",
            "rate": 0.8392,
            "reason": "德语讹字率 0.8392（正形 225／讹形 1174）"
          }
        },
        "德语附加": {
          "h→b率": 0.8667,
          "h→b样本": 15,
          "变音符每千词": 126.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8392,
        "reason": "德语讹字率 0.8392（正形 225／讹形 1174）",
        "file": "furstbismarckna02penz.txt"
      },
      "src-27fdb7e0f9f3": {
        "words": 164990,
        "diagnostic_est_eft": [
          0,
          8
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 55.6,
            "panel_good": 224,
            "panel_bad": 1113,
            "若无语种门会读到": 0.8325,
            "verdict": "不可用",
            "rate": 0.8325,
            "reason": "德语讹字率 0.8325（正形 224／讹形 1113）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3,
          "变音符每千词": 140.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8325,
        "reason": "德语讹字率 0.8325（正形 224／讹形 1113）",
        "file": "furstbismarckna03penz.txt"
      },
      "src-a8c4deedb478": {
        "words": 268034,
        "diagnostic_est_eft": [
          25,
          33
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 50.1,
            "panel_good": 636,
            "panel_bad": 1448,
            "若无语种门会读到": 0.6948,
            "verdict": "不可用",
            "rate": 0.6948,
            "reason": "德语讹字率 0.6948（正形 636／讹形 1448）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 0,
          "变音符每千词": 156.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6948,
        "reason": "德语讹字率 0.6948（正形 636／讹形 1448）",
        "file": "gedankenunderin00bism.txt"
      },
      "src-1c671fb369e4": {
        "words": 142399,
        "diagnostic_est_eft": [
          6,
          11
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 66.5,
            "panel_good": 297,
            "panel_bad": 881,
            "若无语种门会读到": 0.7479,
            "verdict": "不可用",
            "rate": 0.7479,
            "reason": "德语讹字率 0.7479（正形 297／讹形 881）"
          }
        },
        "德语附加": {
          "h→b率": 0.8125,
          "h→b样本": 16,
          "变音符每千词": 164.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7479,
        "reason": "德语讹字率 0.7479（正形 297／讹形 881）",
        "file": "gedankenunderinn01bism.txt"
      },
      "src-815755288ba6": {
        "words": 75502,
        "diagnostic_est_eft": [
          5,
          8
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 39.9,
            "panel_good": 91,
            "panel_bad": 320,
            "若无语种门会读到": 0.7786,
            "verdict": "不可用",
            "rate": 0.7786,
            "reason": "德语讹字率 0.7786（正形 91／讹形 320）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 1,
          "变音符每千词": 126.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7786,
        "reason": "德语讹字率 0.7786（正形 91／讹形 320）",
        "file": "gedankenunderinn03bism.txt"
      },
      "src-dc009c955d33": {
        "words": 50908,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2005.2,
            "panel_good": 361,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 361／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 361／讹形 0）",
        "file": "india.history.resource.85205.txt"
      },
      "src-4942f87597b2": {
        "words": 135835,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1943.8,
            "panel_good": 968,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 968／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 968／讹形 0）",
        "file": "lovelettersofbis00bismiala.txt"
      },
      "src-2f8b247e4d11": {
        "words": 318457,
        "diagnostic_est_eft": [
          5,
          20
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 67.1,
            "panel_good": 83,
            "panel_bad": 1367,
            "若无语种门会读到": 0.9428,
            "verdict": "不可用",
            "rate": 0.9428,
            "reason": "德语讹字率 0.9428（正形 83／讹形 1367）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 1,
          "变音符每千词": 104.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9428,
        "reason": "德语讹字率 0.9428（正形 83／讹形 1367）",
        "file": "preussenimbunde00poscgoog.txt"
      },
      "src-7110272546f6": {
        "words": 107892,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2122.9,
            "panel_good": 584,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 584／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 584／讹形 0）",
        "file": "professionalrec00liargoog.txt"
      },
      "src-d83b6a79022d": {
        "words": 26283,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 63.2,
            "panel_good": 8,
            "panel_bad": 243,
            "若无语种门会读到": 0.9681,
            "verdict": "不可用",
            "rate": 0.9681,
            "reason": "德语讹字率 0.9681（正形 8／讹形 243）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 5,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.9681,
        "reason": "德语讹字率 0.9681（正形 8／讹形 243）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "vierredenzurus00bismiala.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 70,
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
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 35,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 9,
    "★★ 射程": "只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语"
  },
  "holdout_mention": {
    "字面提及": 1,
    "**其中点名了是哪一份的**": 1,
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
    "可用来源": 60,
    "**按内容去重后的作品数**": 47,
    "虚高": 1.277,
    "未声明的重复对": 0,
    "已声明的重复对": 16,
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
        "引文数": 5,
        "核过": 5,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 1,
        "核过": 1,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 2,
        "核过": 2,
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
    "合计": "8 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 10,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 70,
    "train 源总数": 70,
    "本人所著字节": 70675241,
    "train 总字节": 70675241,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 7814693,
    "**判据说未核验的**": 48,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-0c3daab5fdcf",
        "原因": "语种判为 **de**（en=0.000 de=0.121 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8fee88c1082b",
        "原因": "语种判为 **de**（en=0.000 de=0.134 fr=0.012）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8422ffb869a3",
        "原因": "语种判为 **de**（en=0.000 de=0.133 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-cfe297da4fc6",
        "原因": "语种判为 **de**（en=0.001 de=0.112 fr=0.011）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-32e1e087788f",
        "原因": "语种判为 **de**（en=0.000 de=0.130 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-1384279b1926",
        "原因": "语种判为 **de**（en=0.000 de=0.130 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-fb8618283f87",
        "原因": "语种判为 **de**（en=0.000 de=0.133 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-5e838b6da534",
        "原因": "语种判为 **de**（en=0.000 de=0.126 fr=0.013）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 23.42,
    "**立场句/万字**": 0.16,
    "其中不含第一人称的": 81,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 63,
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
    "第一人称覆盖率": 0.531,
    "状态": "无候选（第一人称覆盖率 0.531）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-bismarck-176/workspaces/otto-von-bismarck/evidence/source-ledger.jsonl",
    "一手份数": 53,
    "台账总份数": 60,
    "一手占比": 0.8833,
    "有材料的道数": 6,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 70,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-0c3daab5fdcf 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 70,
    "声称公有领域": 0,
    "不声称（不判）": 70,
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
    "expression"
  ],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 70,
    "**`title` 就是文件名**": 0,
    "真书目题名": 70,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 70,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 25,
  "claims_active": 25,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 25,
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
    "断言条数": 25,
    "source_ids": "逐条各异（非空 25/25，不同取值 13）",
    "evidence_clusters": "逐条各异（非空 25/25，不同取值 25）",
    "counter_source_ids": "整批都空（非空 0/25，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 56,
    "来源数": 70,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 28,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 8,
    "取不到正文的源": 0,
    "例": []
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-bismarck-176/workspaces/otto-von-bismarck/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-a34d7e639e28",
      "           **他的判断模型：先看信息从哪条渠道来，再看内容。** `Der heimischen Politik bin ich ganz entrückt, da ich außer …",
      "",
      "低于 10% 的 36 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-bismarck-176/workspaces/otto-von-bismarck/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-bismarck-176/workspaces/otto-von-bismarck/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8262,
  "baseline_overall": 0.5062,
  "candidate_baseline_delta": 0.32,
  "suite_candidate_means": {
    "known": 0.725,
    "boundary": 0.525,
    "voice": 0.935,
    "trajectory": 0.875,
    "contrast": 0.575,
    "fact-preservation": 0.925,
    "style-decoy": 0.885,
    "task-completion": 0.95,
    "planning-fidelity": 0.95,
    "tool-use": 0.95,
    "capability-calibration": 0.625,
    "refusal-stop": 0.925,
    "long-horizon": 0.875,
    "identity-routing": 0.925,
    "anonymous-fidelity": 0.625,
    "token-efficiency": 0.95
  },
  "suite_single_drag": {
    "未过阈值的套组": 2,
    "**被单独一道题拖住**": [
      "boundary　均分 0.5250 < 0.70　**被 ovb-boundary-01（0.150）一道拖住——去掉它 0.9000 ≥ 0.70**",
      "fact-preservation　均分 0.9250 < 0.93　**被 ovb-fact-preservation-01（0.900）一道拖住——去掉它 0.9500 ≥ 0.93**"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 23/25 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 2 未纳入）",
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

- `corpus.holdout-work-named-in-artifacts`: **建模者读得到的文件里有 1 处直接说出了 holdout 是哪一份**（书名／卷次页码／文件名／源 id）——这比「提到有个 holdout」严重得多，**它把那道题考什么也告诉了**。　[('facts.md', 44)]
- `corpus.holdout-mentioned-in-artifacts`: **建模者读得到的文件里有 1 处提到 holdout**——知道「存在一份取不到的材料、它关于某某」已足够定位那道题。　[('facts.md', 'holdout')]
- `eval.boundary-threshold`: boundary score 0.525 < 0.700
- `corpus.ocr-dead-as-primary`: **有被 OCR 整份毁掉的文件被记作 P1**——你正打算从一份读不出字的文件里取逐字引文；换干净扫本或降级

## Warnings

- `corpus.longs-corruption`: **50 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-0c3daab5fdcf` 00078127bsb.txt —— 德语讹字率 0.5163（正形 148／讹形 158），**不可做逐字引文**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
