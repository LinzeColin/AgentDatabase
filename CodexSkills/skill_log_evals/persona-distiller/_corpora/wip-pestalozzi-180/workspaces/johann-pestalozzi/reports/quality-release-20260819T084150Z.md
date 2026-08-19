# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-pestalozzi-180/workspaces/johann-pestalozzi`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T08:41:50Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 70,
    "claims": 24
  },
  "sources_total": 70,
  "sources_train": 61,
  "sources_usable_train": 61,
  "sources_holdout": 9,
  "primary_sources": 60,
  "primary_ratio": 0.9836,
  "lane_source_counts": {
    "writings": 52,
    "conversations": 4,
    "expression": 1,
    "external": 1,
    "decisions": 1,
    "timeline": 2
  },
  "authorship": {
    "P1 声称为本人所著": 65,
    "已证实归属": 4,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "61 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 70,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干德文编本题名页逐字（`src-413dab629c0f`，1819，Fraktur）：`Peſtalozzi's ſaͤmmtliche Schriften",
    "citation": "archive.org item（各 source_id 的 locator 与 sha256 记于 source-ledger.jsonl）",
    "争议篇目数": 0,
    "P1 声称本人所著": 65,
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
    "usable_train": 61,
    "fact 类条数": 13,
    "**人物事实**（计入）": 13,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 13,
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
    "含同形字的源": 9,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "10082564bsb.txt",
        "非拉丁字符": 23,
        "全同形字词": 5,
        "样例": [
          "οο 读作 oo",
          "νοο 读作 voo",
          "ν 读作 v"
        ]
      },
      {
        "源": "10129403bsb.txt",
        "非拉丁字符": 6,
        "全同形字词": 0,
        "样例": [
          "ꝛñvꝛmfανα 读作 ꝛñvꝛmfαvα"
        ]
      },
      {
        "源": "10724505bsb.txt",
        "非拉丁字符": 4,
        "全同形字词": 0,
        "样例": [
          "πi 读作 πi"
        ]
      },
      {
        "源": "10724509bsb.txt",
        "非拉丁字符": 2,
        "全同形字词": 0,
        "样例": [
          "gungnαν 读作 gungnαv"
        ]
      },
      {
        "源": "bim_eighteenth-century_leonard-gertrude-a-po_pestalozzi-johann-heinr_1800.txt",
        "非拉丁字符": 1,
        "全同形字词": 0,
        "样例": [
          "οd 读作 od"
        ]
      },
      {
        "源": "bub_gb_H-I_AAAAcAAJ.txt",
        "非拉丁字符": 1,
        "全同形字词": 1,
        "样例": [
          "ν 读作 v"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 54,
      "不适用": 2,
      "干净": 11,
      "未核": 3
    },
    "逐份": {
      "src-e8dc4740199f": {
        "words": 66947,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 619.1,
            "panel_good": 85,
            "panel_bad": 277,
            "若无语种门会读到": 0.7652,
            "verdict": "不可用",
            "rate": 0.7652,
            "reason": "德语讹字率 0.7652（正形 85／讹形 277）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1169,
          "变音符每千词": 24.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7652,
        "reason": "德语讹字率 0.7652（正形 85／讹形 277）",
        "file": "10041514bsb.txt"
      },
      "src-06755f524adf": {
        "words": 367494,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 689.8,
            "panel_good": 560,
            "panel_bad": 1027,
            "若无语种门会读到": 0.6471,
            "verdict": "不可用",
            "rate": 0.6471,
            "reason": "德语讹字率 0.6471（正形 560／讹形 1027）"
          }
        },
        "德语附加": {
          "h→b率": 0.0002,
          "h→b样本": 6574,
          "变音符每千词": 86.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6471,
        "reason": "德语讹字率 0.6471（正形 560／讹形 1027）",
        "file": "10050004bsb.txt"
      },
      "src-978bbac09ab9": {
        "words": 54024,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 606.8,
            "panel_good": 118,
            "panel_bad": 153,
            "若无语种门会读到": 0.5646,
            "verdict": "不可用",
            "rate": 0.5646,
            "reason": "德语讹字率 0.5646（正形 118／讹形 153）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 912,
          "变音符每千词": 29.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5646,
        "reason": "德语讹字率 0.5646（正形 118／讹形 153）",
        "file": "10065771bsb.txt"
      },
      "src-46f93c4176cd": {
        "words": 24129,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 353.5,
            "panel_good": 9,
            "panel_bad": 328,
            "若无语种门会读到": 0.9733,
            "verdict": "不可用",
            "rate": 0.9733,
            "reason": "德语讹字率 0.9733（正形 9／讹形 328）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 164,
          "变音符每千词": 28.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9733,
        "reason": "德语讹字率 0.9733（正形 9／讹形 328）",
        "file": "10082563bsb.txt"
      },
      "src-b886d7402b7b": {
        "words": 33831,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 534.7,
            "panel_good": 26,
            "panel_bad": 365,
            "若无语种门会读到": 0.9335,
            "verdict": "不可用",
            "rate": 0.9335,
            "reason": "德语讹字率 0.9335（正形 26／讹形 365）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 227,
          "变音符每千词": 35.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9335,
        "reason": "德语讹字率 0.9335（正形 26／讹形 365）",
        "file": "10082564bsb.txt"
      },
      "src-5fb86375774b": {
        "words": 66046,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 680.7,
            "panel_good": 203,
            "panel_bad": 485,
            "若无语种门会读到": 0.7049,
            "verdict": "不可用",
            "rate": 0.7049,
            "reason": "德语讹字率 0.7049（正形 203／讹形 485）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1558,
          "变音符每千词": 37.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7049,
        "reason": "德语讹字率 0.7049（正形 203／讹形 485）",
        "file": "10116094bsb.txt"
      },
      "src-0ac0430b0bd5": {
        "words": 63327,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 681.7,
            "panel_good": 326,
            "panel_bad": 561,
            "若无语种门会读到": 0.6325,
            "verdict": "不可用",
            "rate": 0.6325,
            "reason": "德语讹字率 0.6325（正形 326／讹形 561）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1397,
          "变音符每千词": 32.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6325,
        "reason": "德语讹字率 0.6325（正形 326／讹形 561）",
        "file": "10116095bsb.txt"
      },
      "src-daf5ded51781": {
        "words": 64680,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 644.7,
            "panel_good": 247,
            "panel_bad": 384,
            "若无语种门会读到": 0.6086,
            "verdict": "不可用",
            "rate": 0.6086,
            "reason": "德语讹字率 0.6086（正形 247／讹形 384）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1272,
          "变音符每千词": 38.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6086,
        "reason": "德语讹字率 0.6086（正形 247／讹形 384）",
        "file": "10116096bsb.txt"
      },
      "src-9d4b3afa89e1": {
        "words": 39277,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 631.7,
            "panel_good": 46,
            "panel_bad": 212,
            "若无语种门会读到": 0.8217,
            "verdict": "不可用",
            "rate": 0.8217,
            "reason": "德语讹字率 0.8217（正形 46／讹形 212）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 691,
          "变音符每千词": 38.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8217,
        "reason": "德语讹字率 0.8217（正形 46／讹形 212）",
        "file": "10116099bsb.txt"
      },
      "src-e61586537107": {
        "words": 159001,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 787.2,
            "panel_good": 408,
            "panel_bad": 657,
            "若无语种门会读到": 0.6169,
            "verdict": "不可用",
            "rate": 0.6169,
            "reason": "德语讹字率 0.6169（正形 408／讹形 657）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3530,
          "变音符每千词": 71.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6169,
        "reason": "德语讹字率 0.6169（正形 408／讹形 657）",
        "file": "10128423bsb.txt"
      },
      "src-d13f3f022a13": {
        "words": 84407,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 794.1,
            "panel_good": 203,
            "panel_bad": 309,
            "若无语种门会读到": 0.6035,
            "verdict": "不可用",
            "rate": 0.6035,
            "reason": "德语讹字率 0.6035（正形 203／讹形 309）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1977,
          "变音符每千词": 40.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6035,
        "reason": "德语讹字率 0.6035（正形 203／讹形 309）",
        "file": "10129401bsb.txt"
      },
      "src-d501ab999db5": {
        "words": 90774,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 784.9,
            "panel_good": 302,
            "panel_bad": 829,
            "若无语种门会读到": 0.733,
            "verdict": "不可用",
            "rate": 0.733,
            "reason": "德语讹字率 0.7330（正形 302／讹形 829）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2120,
          "变音符每千词": 44.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.733,
        "reason": "德语讹字率 0.7330（正形 302／讹形 829）",
        "file": "10129403bsb.txt"
      },
      "src-844021790645": {
        "words": 63914,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 683.7,
            "panel_good": 328,
            "panel_bad": 531,
            "若无语种门会读到": 0.6182,
            "verdict": "不可用",
            "rate": 0.6182,
            "reason": "德语讹字率 0.6182（正形 328／讹形 531）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1419,
          "变音符每千词": 30.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6182,
        "reason": "德语讹字率 0.6182（正形 328／讹形 531）",
        "file": "10311310bsb.txt"
      },
      "src-7f0f6feca579": {
        "words": 64775,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 647.6,
            "panel_good": 247,
            "panel_bad": 359,
            "若无语种门会读到": 0.5924,
            "verdict": "不可用",
            "rate": 0.5924,
            "reason": "德语讹字率 0.5924（正形 247／讹形 359）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1269,
          "变音符每千词": 36.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5924,
        "reason": "德语讹字率 0.5924（正形 247／讹形 359）",
        "file": "10311311bsb.txt"
      },
      "src-2037435a6370": {
        "words": 45577,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 705.0,
            "panel_good": 44,
            "panel_bad": 164,
            "若无语种门会读到": 0.7885,
            "verdict": "不可用",
            "rate": 0.7885,
            "reason": "德语讹字率 0.7885（正形 44／讹形 164）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 967,
          "变音符每千词": 33.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7885,
        "reason": "德语讹字率 0.7885（正形 44／讹形 164）",
        "file": "10721192bsb.txt"
      },
      "src-413dab629c0f": {
        "words": 94983,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 669.3,
            "panel_good": 185,
            "panel_bad": 458,
            "若无语种门会读到": 0.7123,
            "verdict": "不可用",
            "rate": 0.7123,
            "reason": "德语讹字率 0.7123（正形 185／讹形 458）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1849,
          "变音符每千词": 37.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7123,
        "reason": "德语讹字率 0.7123（正形 185／讹形 458）",
        "file": "10724505bsb.txt"
      },
      "src-8d00638c094c": {
        "words": 119807,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 720.4,
            "panel_good": 416,
            "panel_bad": 939,
            "若无语种门会读到": 0.693,
            "verdict": "不可用",
            "rate": 0.693,
            "reason": "德语讹字率 0.6930（正形 416／讹形 939）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2597,
          "变音符每千词": 40.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.693,
        "reason": "德语讹字率 0.6930（正形 416／讹形 939）",
        "file": "10724506bsb.txt"
      },
      "src-c597746f519c": {
        "words": 110523,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 721.8,
            "panel_good": 342,
            "panel_bad": 791,
            "若无语种门会读到": 0.6981,
            "verdict": "不可用",
            "rate": 0.6981,
            "reason": "德语讹字率 0.6981（正形 342／讹形 791）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2361,
          "变音符每千词": 42.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6981,
        "reason": "德语讹字率 0.6981（正形 342／讹形 791）",
        "file": "10724507bsb.txt"
      },
      "src-d73dcc95971b": {
        "words": 81429,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 632.1,
            "panel_good": 107,
            "panel_bad": 347,
            "若无语种门会读到": 0.7643,
            "verdict": "不可用",
            "rate": 0.7643,
            "reason": "德语讹字率 0.7643（正形 107／讹形 347）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1568,
          "变音符每千词": 38.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7643,
        "reason": "德语讹字率 0.7643（正形 107／讹形 347）",
        "file": "10724508bsb.txt"
      },
      "src-e18b9d8fd986": {
        "words": 112207,
        "diagnostic_est_eft": [
          3,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 678.3,
            "panel_good": 166,
            "panel_bad": 521,
            "若无语种门会读到": 0.7584,
            "verdict": "不可用",
            "rate": 0.7584,
            "reason": "德语讹字率 0.7584（正形 166／讹形 521）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2230,
          "变音符每千词": 42.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7584,
        "reason": "德语讹字率 0.7584（正形 166／讹形 521）",
        "file": "10724509bsb.txt"
      },
      "src-eb1eed944428": {
        "words": 108645,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 641.9,
            "panel_good": 139,
            "panel_bad": 519,
            "若无语种门会读到": 0.7888,
            "verdict": "不可用",
            "rate": 0.7888,
            "reason": "德语讹字率 0.7888（正形 139／讹形 519）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1811,
          "变音符每千词": 40.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7888,
        "reason": "德语讹字率 0.7888（正形 139／讹形 519）",
        "file": "10724510bsb.txt"
      },
      "src-0e110ce02271": {
        "words": 69495,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0055；英文：锚 1.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "PestalozziMieIndagini.txt"
      },
      "src-aa40a14c2501": {
        "words": 78057,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1503.0,
            "panel_good": 6,
            "panel_bad": 40,
            "若无语种门会读到": 0.8696,
            "verdict": "不可用",
            "rate": 0.8696,
            "reason": "英文讹字率 0.8696（正形 6／讹形 40）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8696,
        "reason": "英文讹字率 0.8696（正形 6／讹形 40）",
        "file": "bim_eighteenth-century_leonard-gertrude-a-po_pestalozzi-johann-heinr_1800.txt"
      },
      "src-09d500dc9ecd": {
        "words": 378549,
        "diagnostic_est_eft": [
          2,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 719.0,
            "panel_good": 583,
            "panel_bad": 5849,
            "若无语种门会读到": 0.9094,
            "verdict": "不可用",
            "rate": 0.9094,
            "reason": "德语讹字率 0.9094（正形 583／讹形 5849）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 6088,
          "变音符每千词": 93.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9094,
        "reason": "德语讹字率 0.9094（正形 583／讹形 5849）",
        "file": "bub_gb_H-I_AAAAcAAJ.txt"
      },
      "src-92b9a40f1ae7": {
        "words": 73801,
        "diagnostic_est_eft": [
          0,
          9
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 285.0,
            "panel_good": 32,
            "panel_bad": 1005,
            "若无语种门会读到": 0.9691,
            "verdict": "不可用",
            "rate": 0.9691,
            "reason": "德语讹字率 0.9691（正形 32／讹形 1005）"
          }
        },
        "德语附加": {
          "h→b率": 0.0143,
          "h→b样本": 767,
          "变音符每千词": 99.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9691,
        "reason": "德语讹字率 0.9691（正形 32／讹形 1005）",
        "file": "bub_gb_tLQ7AAAAcAAJ.txt"
      },
      "src-54fb6856980e": {
        "words": 39490,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 686.2,
            "panel_good": 15,
            "panel_bad": 301,
            "若无语种门会读到": 0.9525,
            "verdict": "不可用",
            "rate": 0.9525,
            "reason": "德语讹字率 0.9525（正形 15／讹形 301）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 514,
          "变音符每千词": 37.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9525,
        "reason": "德语讹字率 0.9525（正形 15／讹形 301）",
        "file": "buchdermtter00pest.txt"
      },
      "src-1ce019d13e13": {
        "words": 150961,
        "diagnostic_est_eft": [
          174,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0098；英文：锚 11.4<500.0，若强行读 0.0000；德语：锚 1.6<15.0，若强行读 0.0988）",
        "file": "cmoeducajertrud00pestgoog.txt"
      },
      "src-1eb49c877fe6": {
        "words": 71519,
        "diagnostic_est_eft": [
          0,
          12
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 52.2,
            "panel_good": 64,
            "panel_bad": 779,
            "若无语种门会读到": 0.9241,
            "verdict": "不可用",
            "rate": 0.9241,
            "reason": "德语讹字率 0.9241（正形 64／讹形 779）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 4,
          "变音符每千词": 107.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9241,
        "reason": "德语讹字率 0.9241（正形 64／讹形 779）",
        "file": "diepdagogikjoh00pest.txt"
      },
      "src-2f5a30d16b04": {
        "words": 47570,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2406.8,
            "panel_good": 528,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 528／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 528／讹形 0）",
        "file": "gpl_1902807.txt"
      },
      "src-18a5a0caaae5": {
        "words": 91813,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2150.2,
            "panel_good": 914,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 914／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 914／讹形 0）",
        "file": "howgertrudeteach00pest.txt"
      },
      "src-469b0e10f10c": {
        "words": 105157,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2127.8,
            "panel_good": 1040,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1040／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1040／讹形 0）",
        "file": "howgertrudeteach00pest_0.txt"
      },
      "src-e9b7dcd6764b": {
        "words": 104860,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2132.0,
            "panel_good": 1040,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1040／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1040／讹形 0）",
        "file": "howgertrudeteach00pestiala.txt"
      },
      "src-81b5df873a0e": {
        "words": 105046,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2126.9,
            "panel_good": 1038,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1038／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1038／讹形 0）",
        "file": "howgertrudeteach00pestuoft.txt"
      },
      "src-7edf6595c82f": {
        "words": 57798,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1976.4,
            "panel_good": 538,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 538／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 538／讹形 0）",
        "file": "leonardgertrude00pestiala.txt"
      },
      "src-d30613613c98": {
        "words": 76616,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1691.4,
            "panel_good": 12,
            "panel_bad": 685,
            "若无语种门会读到": 0.9828,
            "verdict": "不可用",
            "rate": 0.9828,
            "reason": "英文讹字率 0.9828（正形 12／讹形 685）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9828,
        "reason": "英文讹字率 0.9828（正形 12／讹形 685）",
        "file": "leonardgertrudep00pest.txt"
      },
      "src-4b8f7b430a38": {
        "words": 41571,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2373.8,
            "panel_good": 460,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 460／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 460／讹形 0）",
        "file": "lettersonearlye03pestgoog.txt"
      },
      "src-bbcb93fad0d0": {
        "words": 41156,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2368.8,
            "panel_good": 445,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 445／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 445／讹形 0）",
        "file": "lettersonearlyed00pest.txt"
      },
      "src-17b03f664ea4": {
        "words": 49282,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2427.9,
            "panel_good": 542,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 542／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 542／讹形 0）",
        "file": "lettersonearlyed00pestiala.txt"
      },
      "src-ec56edc16d30": {
        "words": 177216,
        "diagnostic_est_eft": [
          3,
          2
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 715.2,
            "panel_good": 418,
            "panel_bad": 2851,
            "若无语种门会读到": 0.8721,
            "verdict": "不可用",
            "rate": 0.8721,
            "reason": "德语讹字率 0.8721（正形 418／讹形 2851）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3674,
          "变音符每千词": 56.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8721,
        "reason": "德语讹字率 0.8721（正形 418／讹形 2851）",
        "file": "lienhardundgert00pestgoog.txt"
      },
      "src-42cea47efc53": {
        "words": 216090,
        "diagnostic_est_eft": [
          2,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 705.6,
            "panel_good": 729,
            "panel_bad": 4572,
            "若无语种门会读到": 0.8625,
            "verdict": "不可用",
            "rate": 0.8625,
            "reason": "德语讹字率 0.8625（正形 729／讹形 4572）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4375,
          "变音符每千词": 57.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8625,
        "reason": "德语讹字率 0.8625（正形 729／讹形 4572）",
        "file": "lienhardundgert01pestgoog.txt"
      },
      "src-d2ac2fea5202": {
        "words": 179904,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 696.3,
            "panel_good": 418,
            "panel_bad": 2519,
            "若无语种门会读到": 0.8577,
            "verdict": "不可用",
            "rate": 0.8577,
            "reason": "德语讹字率 0.8577（正形 418／讹形 2519）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3602,
          "变音符每千词": 51.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8577,
        "reason": "德语讹字率 0.8577（正形 418／讹形 2519）",
        "file": "lienhardundgert02pestgoog.txt"
      },
      "src-9d516439f3cd": {
        "words": 102507,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 625.0,
            "panel_good": 230,
            "panel_bad": 1473,
            "若无语种门会读到": 0.8649,
            "verdict": "不可用",
            "rate": 0.8649,
            "reason": "德语讹字率 0.8649（正形 230／讹形 1473）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1602,
          "变音符每千词": 78.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8649,
        "reason": "德语讹字率 0.8649（正形 230／讹形 1473）",
        "file": "meinelebensschi01pestgoog.txt"
      },
      "src-bebd54a87647": {
        "words": 247875,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2180.9,
            "panel_good": 2743,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2743／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2743／讹形 0）",
        "file": "pestalozzipestal00barnrich.txt"
      },
      "src-927c60f97f75": {
        "words": 409999,
        "diagnostic_est_eft": [
          2,
          53
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 167.1,
            "panel_good": 845,
            "panel_bad": 3579,
            "若无语种门会读到": 0.809,
            "verdict": "不可用",
            "rate": 0.809,
            "reason": "德语讹字率 0.8090（正形 845／讹形 3579）"
          }
        },
        "德语附加": {
          "h→b率": 0.1785,
          "h→b样本": 409,
          "变音符每千词": 92.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.809,
        "reason": "德语讹字率 0.8090（正形 845／讹形 3579）",
        "file": "pestalozzisleben00pest.txt"
      },
      "src-7c075c939b58": {
        "words": 58915,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2017.7,
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
        "file": "pestalozzisleona00pestuoft.txt"
      },
      "src-8dc1b4837944": {
        "words": 168837,
        "diagnostic_est_eft": [
          1,
          24
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 97.4,
            "panel_good": 204,
            "panel_bad": 1841,
            "若无语种门会读到": 0.9002,
            "verdict": "不可用",
            "rate": 0.9002,
            "reason": "德语讹字率 0.9002（正形 204／讹形 1841）"
          }
        },
        "德语附加": {
          "h→b率": 0.6341,
          "h→b样本": 82,
          "变音符每千词": 97.3,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9002,
        "reason": "德语讹字率 0.9002（正形 204／讹形 1841）　★ **长 s 之外还坏了**：**h→b 讹变 63.4%**（`nicht`→`nicbt` 这一族，样本 82）——逐字引用会印出作者没写的形",
        "file": "pestalozzislienh00pest.txt"
      },
      "src-a492cba7836a": {
        "words": 342507,
        "diagnostic_est_eft": [
          0,
          51
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 111.3,
            "panel_good": 445,
            "panel_bad": 7470,
            "若无语种门会读到": 0.9438,
            "verdict": "不可用",
            "rate": 0.9438,
            "reason": "德语讹字率 0.9438（正形 445／讹形 7470）"
          }
        },
        "德语附加": {
          "h→b率": 0.0013,
          "h→b样本": 1582,
          "变音符每千词": 82.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9438,
        "reason": "德语讹字率 0.9438（正形 445／讹形 7470）",
        "file": "pestalozzissamtl04pest.txt"
      },
      "src-54ef5ba9b255": {
        "words": 4906,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 495.3,
            "panel_good": 25,
            "panel_bad": 36,
            "若无语种门会读到": 0.5902,
            "verdict": "不可用",
            "rate": 0.5902,
            "reason": "德语讹字率 0.5902（正形 25／讹形 36）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 47,
          "变音符每千词": 63.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5902,
        "reason": "德语讹字率 0.5902（正形 25／讹形 36）",
        "file": "pestalozzissmmt00seyfgoog.txt"
      },
      "src-3a50e0410ad7": {
        "words": 1235,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 704.5,
            "panel_good": 11,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 11 次 < 30 —— **样本量不够，不是「干净」**"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 291.5,
            "panel_good": 21,
            "panel_bad": 2,
            "若无语种门会读到": 0.087,
            "verdict": "未核",
            "reason": "德语面板只命中 23 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 12,
          "变音符每千词": 63.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 11 次 < 30 —— **样本量不够，不是「干净」**　（两语域都适用，取更差的一侧）",
        "file": "pestalozzissmmt01seyfgoog.txt"
      },
      "src-3e651b141b0c": {
        "words": 1210,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 661.2,
            "panel_good": 11,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 11 次 < 30 —— **样本量不够，不是「干净」**"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 281.0,
            "panel_good": 22,
            "panel_bad": 5,
            "若无语种门会读到": 0.1852,
            "verdict": "未核",
            "reason": "德语面板只命中 27 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 12,
          "变音符每千词": 65.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 11 次 < 30 —— **样本量不够，不是「干净」**　（两语域都适用，取更差的一侧）",
        "file": "pestalozzissmmt02seyfgoog.txt"
      },
      "src-c6e5607e0f7e": {
        "words": 1173,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 682.0,
            "panel_good": 10,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 10 次 < 30 —— **样本量不够，不是「干净」**"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 341.0,
            "panel_good": 21,
            "panel_bad": 1,
            "若无语种门会读到": 0.0455,
            "verdict": "未核",
            "reason": "德语面板只命中 22 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 12,
          "变音符每千词": 68.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 10 次 < 30 —— **样本量不够，不是「干净」**　（两语域都适用，取更差的一侧）",
        "file": "pestalozzissmmt03seyfgoog.txt"
      },
      "src-64f3ae1ac327": {
        "words": 7816,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 582.1,
            "panel_good": 43,
            "panel_bad": 143,
            "若无语种门会读到": 0.7688,
            "verdict": "不可用",
            "rate": 0.7688,
            "reason": "德语讹字率 0.7688（正形 43／讹形 143）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 102,
          "变音符每千词": 69.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7688,
        "reason": "德语讹字率 0.7688（正形 43／讹形 143）",
        "file": "pestalozzissmmt04seyfgoog.txt"
      },
      "src-b362bad8e0f4": {
        "words": 103697,
        "diagnostic_est_eft": [
          0,
          7
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 101.6,
            "panel_good": 81,
            "panel_bad": 1344,
            "若无语种门会读到": 0.9432,
            "verdict": "不可用",
            "rate": 0.9432,
            "reason": "德语讹字率 0.9432（正形 81／讹形 1344）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 9,
          "变音符每千词": 62.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9432,
        "reason": "德语讹字率 0.9432（正形 81／讹形 1344）",
        "file": "smmtlicheschr02pest.txt"
      },
      "src-4031b6090d47": {
        "words": 90819,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 681.9,
            "panel_good": 114,
            "panel_bad": 442,
            "若无语种门会读到": 0.795,
            "verdict": "不可用",
            "rate": 0.795,
            "reason": "德语讹字率 0.7950（正形 114／讹形 442）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1664,
          "变音符每千词": 29.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.795,
        "reason": "德语讹字率 0.7950（正形 114／讹形 442）",
        "file": "smmtlicheschr10pestuoft.txt"
      },
      "src-6b07fbead5b0": {
        "words": 94531,
        "diagnostic_est_eft": [
          0,
          9
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 106.6,
            "panel_good": 122,
            "panel_bad": 974,
            "若无语种门会读到": 0.8887,
            "verdict": "不可用",
            "rate": 0.8887,
            "reason": "德语讹字率 0.8887（正形 122／讹形 974）"
          }
        },
        "德语附加": {
          "h→b率": 0.0347,
          "h→b样本": 144,
          "变音符每千词": 71.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8887,
        "reason": "德语讹字率 0.8887（正形 122／讹形 974）",
        "file": "smmtlicheschri01pestuoft.txt"
      },
      "src-7507dd75903a": {
        "words": 119832,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 735.6,
            "panel_good": 424,
            "panel_bad": 829,
            "若无语种门会读到": 0.6616,
            "verdict": "不可用",
            "rate": 0.6616,
            "reason": "德语讹字率 0.6616（正形 424／讹形 829）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2702,
          "变音符每千词": 30.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6616,
        "reason": "德语讹字率 0.6616（正形 424／讹形 829）",
        "file": "smmtlicheschri03pestuoft.txt"
      },
      "src-d39f1f4010b5": {
        "words": 110632,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 731.9,
            "panel_good": 338,
            "panel_bad": 643,
            "若无语种门会读到": 0.6555,
            "verdict": "不可用",
            "rate": 0.6555,
            "reason": "德语讹字率 0.6555（正形 338／讹形 643）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2433,
          "变音符每千词": 28.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6555,
        "reason": "德语讹字率 0.6555（正形 338／讹形 643）",
        "file": "smmtlicheschri04pestuoft.txt"
      },
      "src-035d789f0099": {
        "words": 80981,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 642.1,
            "panel_good": 100,
            "panel_bad": 312,
            "若无语种门会读到": 0.7573,
            "verdict": "不可用",
            "rate": 0.7573,
            "reason": "德语讹字率 0.7573（正形 100／讹形 312）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1608,
          "变音符每千词": 29.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7573,
        "reason": "德语讹字率 0.7573（正形 100／讹形 312）",
        "file": "smmtlicheschri05pestuoft.txt"
      },
      "src-9a695e7d967e": {
        "words": 113388,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 685.3,
            "panel_good": 178,
            "panel_bad": 438,
            "若无语种门会读到": 0.711,
            "verdict": "不可用",
            "rate": 0.711,
            "reason": "德语讹字率 0.7110（正形 178／讹形 438）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2291,
          "变音符每千词": 30.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.711,
        "reason": "德语讹字率 0.7110（正形 178／讹形 438）",
        "file": "smmtlicheschri06pestuoft.txt"
      },
      "src-3b5d5f021934": {
        "words": 110965,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 668.4,
            "panel_good": 146,
            "panel_bad": 453,
            "若无语种门会读到": 0.7563,
            "verdict": "不可用",
            "rate": 0.7563,
            "reason": "德语讹字率 0.7563（正形 146／讹形 453）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1950,
          "变音符每千词": 25.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7563,
        "reason": "德语讹字率 0.7563（正形 146／讹形 453）",
        "file": "smmtlicheschri07pestuoft.txt"
      },
      "src-d2dd5976bf5e": {
        "words": 106942,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 684.9,
            "panel_good": 262,
            "panel_bad": 693,
            "若无语种门会读到": 0.7257,
            "verdict": "不可用",
            "rate": 0.7257,
            "reason": "德语讹字率 0.7257（正形 262／讹形 693）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2015,
          "变音符每千词": 31.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7257,
        "reason": "德语讹字率 0.7257（正形 262／讹形 693）",
        "file": "smmtlicheschri08pestuoft.txt"
      },
      "src-b71a31525629": {
        "words": 84683,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 689.7,
            "panel_good": 102,
            "panel_bad": 377,
            "若无语种门会读到": 0.7871,
            "verdict": "不可用",
            "rate": 0.7871,
            "reason": "德语讹字率 0.7871（正形 102／讹形 377）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1658,
          "变音符每千词": 30.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7871,
        "reason": "德语讹字率 0.7871（正形 102／讹形 377）",
        "file": "smmtlicheschri09pestuoft.txt"
      },
      "src-af16ecd35f79": {
        "words": 106582,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 684.8,
            "panel_good": 141,
            "panel_bad": 453,
            "若无语种门会读到": 0.7626,
            "verdict": "不可用",
            "rate": 0.7626,
            "reason": "德语讹字率 0.7626（正形 141／讹形 453）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1944,
          "变音符每千词": 30.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7626,
        "reason": "德语讹字率 0.7626（正形 141／讹形 453）",
        "file": "smmtlicheschri11pestuoft.txt"
      },
      "src-6d5cd0c1f383": {
        "words": 134008,
        "diagnostic_est_eft": [
          2,
          21
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 101.4,
            "panel_good": 99,
            "panel_bad": 1988,
            "若无语种门会读到": 0.9526,
            "verdict": "不可用",
            "rate": 0.9526,
            "reason": "德语讹字率 0.9526（正形 99／讹形 1988）"
          }
        },
        "德语附加": {
          "h→b率": 0.0921,
          "h→b样本": 152,
          "变音符每千词": 77.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9526,
        "reason": "德语讹字率 0.9526（正形 99／讹形 1988）",
        "file": "smmtlicheschri12pestuoft.txt"
      },
      "src-3d5a9b664cc4": {
        "words": 101375,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 659.2,
            "panel_good": 185,
            "panel_bad": 271,
            "若无语种门会读到": 0.5943,
            "verdict": "不可用",
            "rate": 0.5943,
            "reason": "德语讹字率 0.5943（正形 185／讹形 271）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1682,
          "变音符每千词": 26.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5943,
        "reason": "德语讹字率 0.5943（正形 185／讹形 271）",
        "file": "smmtlicheschri13pestuoft.txt"
      },
      "src-442afe91c8a1": {
        "words": 91845,
        "diagnostic_est_eft": [
          1,
          9
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 100.7,
            "panel_good": 135,
            "panel_bad": 1147,
            "若无语种门会读到": 0.8947,
            "verdict": "不可用",
            "rate": 0.8947,
            "reason": "德语讹字率 0.8947（正形 135／讹形 1147）"
          }
        },
        "德语附加": {
          "h→b率": 1.0,
          "h→b样本": 1,
          "变音符每千词": 81.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8947,
        "reason": "德语讹字率 0.8947（正形 135／讹形 1147）",
        "file": "smmtlicheschri14pestuoft.txt"
      },
      "src-dc0e417067bb": {
        "words": 102986,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 766.6,
            "panel_good": 183,
            "panel_bad": 524,
            "若无语种门会读到": 0.7412,
            "verdict": "不可用",
            "rate": 0.7412,
            "reason": "德语讹字率 0.7412（正形 183／讹形 524）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1663,
          "变音符每千词": 27.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7412,
        "reason": "德语讹字率 0.7412（正形 183／讹形 524）",
        "file": "smmtlicheschri15pestuoft.txt"
      },
      "src-6e7703b6f0f5": {
        "words": 370648,
        "diagnostic_est_eft": [
          5,
          24
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 52.3,
            "panel_good": 357,
            "panel_bad": 4896,
            "若无语种门会读到": 0.932,
            "verdict": "不可用",
            "rate": 0.932,
            "reason": "德语讹字率 0.9320（正形 357／讹形 4896）"
          }
        },
        "德语附加": {
          "h→b率": 0.9667,
          "h→b样本": 30,
          "变音符每千词": 96.7,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.932,
        "reason": "德语讹字率 0.9320（正形 357／讹形 4896）　★ **长 s 之外还坏了**：**h→b 讹变 96.7%**（`nicht`→`nicbt` 这一族，样本 30）——逐字引用会印出作者没写的形",
        "file": "smtlichewerke01pestuoft.txt"
      },
      "src-58ac21088a08": {
        "words": 206975,
        "diagnostic_est_eft": [
          14,
          42
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 100.0,
            "panel_good": 397,
            "panel_bad": 2723,
            "若无语种门会读到": 0.8728,
            "verdict": "不可用",
            "rate": 0.8728,
            "reason": "德语讹字率 0.8728（正形 397／讹形 2723）"
          }
        },
        "德语附加": {
          "h→b率": 0.0125,
          "h→b样本": 240,
          "变音符每千词": 89.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8728,
        "reason": "德语讹字率 0.8728（正形 397／讹形 2723）",
        "file": "smtlichewerke02pestuoft.txt"
      },
      "src-64aeef8c354a": {
        "words": 191417,
        "diagnostic_est_eft": [
          4,
          32
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 56.2,
            "panel_good": 181,
            "panel_bad": 1932,
            "若无语种门会读到": 0.9143,
            "verdict": "不可用",
            "rate": 0.9143,
            "reason": "德语讹字率 0.9143（正形 181／讹形 1932）"
          }
        },
        "德语附加": {
          "h→b率": 0.5652,
          "h→b样本": 23,
          "变音符每千词": 93.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9143,
        "reason": "德语讹字率 0.9143（正形 181／讹形 1932）",
        "file": "smtlichewerke03pestuoft.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 70,
    "与台账不一致的道": [
      "01-writings.md"
    ],
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
    "ocr_language_death": "⚠ **虚词占比低于下限的 4 份**（多半是 Fraktur／哥特体 OCR 认错字母）：",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 30,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 12,
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
    "可用来源": 61,
    "**按内容去重后的作品数**": 36,
    "虚高": 1.694,
    "未声明的重复对": 0,
    "已声明的重复对": 11,
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
        "引文数": 3,
        "核过": 3,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 2,
        "核过": 2,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 4,
        "核过": 4,
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
    "合计": "9 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 9,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 70,
    "train 源总数": 70,
    "本人所著字节": 47529707,
    "train 总字节": 47529707,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 5490153,
    "**判据说未核验的**": 53,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-e8dc4740199f",
        "原因": "语种判为 **de**（en=0.000 de=0.132 fr=0.011）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-06755f524adf",
        "原因": "语种判为 **de**（en=0.000 de=0.143 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-978bbac09ab9",
        "原因": "语种判为 **de**（en=0.001 de=0.106 fr=0.005）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-46f93c4176cd",
        "原因": "语种判为 **de**（en=0.000 de=0.146 fr=0.016）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b886d7402b7b",
        "原因": "语种判为 **de**（en=0.002 de=0.161 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-5fb86375774b",
        "原因": "语种判为 **de**（en=0.001 de=0.112 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-0ac0430b0bd5",
        "原因": "语种判为 **de**（en=0.001 de=0.124 fr=0.005）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-daf5ded51781",
        "原因": "语种判为 **de**（en=0.001 de=0.125 fr=0.007）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 19.77,
    "**立场句/万字**": 0.15,
    "其中不含第一人称的": 48,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 65,
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
    "第一人称覆盖率": 0.688,
    "状态": "无候选（第一人称覆盖率 0.688）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-pestalozzi-180/workspaces/johann-pestalozzi/evidence/source-ledger.jsonl",
    "一手份数": 60,
    "台账总份数": 61,
    "一手占比": 0.9836,
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
    "最优选法": "把 src-e8dc4740199f 扣作 holdout 即满足三项门",
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
    "两边都有年份": 1,
    "有一边没年份": 69,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 24,
  "claims_active": 24,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 24,
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
    "断言条数": 24,
    "source_ids": "逐条各异（非空 24/24，不同取值 17）",
    "evidence_clusters": "逐条各异（非空 24/24，不同取值 23）",
    "counter_source_ids": "整批都空（非空 0/24，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 1,
    "作品组数（连通分量，仅供参考）": 44,
    "来源数": 70,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 23,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 2,
    "不唯一（同句见于多份源，挂错也照样绿）": 11,
    "取不到正文的源": 0,
    "例": [
      "clm-8042d7313c7f：挂 ['10721192bsb.txt'] → 实 ['10050004bsb.txt', 'smmtlicheschri09pestuoft.txt']",
      "clm-3e5e6a45f7f6：挂 ['10721192bsb.txt', '10724505bsb.txt'] → 实 ['10050004bsb.txt', 'smmtlicheschri09pestuoft.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-pestalozzi-180/workspaces/johann-pestalozzi/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  capabilities.md        clm-abb445bb76f4",
      "           **把抽象的「引导」换成可观察的动作**：不写「真理引导我」，写它 `weder mein Gehen noch mein Stehen, weder mein liegen …",
      "",
      "低于 10% 的 36 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-pestalozzi-180/workspaces/johann-pestalozzi/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-pestalozzi-180/workspaces/johann-pestalozzi/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8247,
  "baseline_overall": 0.5919,
  "candidate_baseline_delta": 0.2328,
  "suite_candidate_means": {
    "known": 0.475,
    "boundary": 0.75,
    "voice": 0.95,
    "trajectory": 0.81,
    "contrast": 0.55,
    "fact-preservation": 0.95,
    "style-decoy": 0.925,
    "task-completion": 0.95,
    "planning-fidelity": 0.9,
    "tool-use": 0.95,
    "capability-calibration": 0.95,
    "refusal-stop": 0.9,
    "long-horizon": 0.9,
    "identity-routing": 0.91,
    "anonymous-fidelity": 0.55,
    "token-efficiency": 0.775
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 23/24 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 1 未纳入）",
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

- `corpus.longs-corruption`: **54 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-e8dc4740199f` 10041514bsb.txt —— 德语讹字率 0.7652（正形 85／讹形 277），**不可做逐字引文**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
