# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-jefferson-175/workspaces/thomas-jefferson`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T04:35:26Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 73,
    "claims": 25
  },
  "sources_total": 73,
  "sources_train": 66,
  "sources_usable_train": 65,
  "sources_holdout": 7,
  "primary_sources": 58,
  "primary_ratio": 0.8923,
  "lane_source_counts": {
    "writings": 25,
    "conversations": 24,
    "expression": 8,
    "external": 3,
    "decisions": 1,
    "timeline": 4
  },
  "authorship": {
    "P1 声称为本人所著": 66,
    "已证实归属": 57,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "9 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 73,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/version-final-de-la-declaracion-de-la-independencia.txt　过短：3 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干编本的题名页逐字（`src-2080428c7f4f`）：`The Works of Thomas Jefferson Collected and Edit",
    "citation": "archive.org item `cu31924092892011`（题名页原文见 authority）",
    "争议篇目数": 0,
    "P1 声称本人所著": 66,
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
    "usable_train": 66,
    "fact 类条数": 14,
    "**人物事实**（计入）": 14,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 14,
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
    "已查语料件": 73,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "bim_eighteenth-century_notes-on-the-state-of-vi_jefferson-thomas_1787.txt",
        "非拉丁字符": 33,
        "全同形字词": 6,
        "样例": [
          "ο 读作 o",
          "ν 读作 v",
          "ον 读作 ov"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "干净": 62,
      "不可用": 3,
      "未核": 6,
      "不适用": 2
    },
    "逐份": {
      "src-cb8911bf2cd9": {
        "words": 220913,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2272.4,
            "panel_good": 2037,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2037／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2037／讹形 0）",
        "file": "10064095bsb.txt"
      },
      "src-a473ad91bd99": {
        "words": 220855,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2268.2,
            "panel_good": 2043,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2043／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2043／讹形 0）",
        "file": "10069010bsb.txt"
      },
      "src-62fdaa348a52": {
        "words": 9795,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2405.3,
            "panel_good": 92,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 92／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 92／讹形 0）",
        "file": "americanpolitica00jeff.txt"
      },
      "src-5d9f1ea8579d": {
        "words": 12545,
        "diagnostic_est_eft": [
          2,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2082.9,
            "panel_good": 121,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 121／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 121／讹形 0）",
        "file": "anessaytowardsf00jeffgoog.txt"
      },
      "src-3f4febe479e3": {
        "words": 88116,
        "diagnostic_est_eft": [
          0,
          5
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1987.0,
            "panel_good": 22,
            "panel_bad": 422,
            "若无语种门会读到": 0.9505,
            "verdict": "不可用",
            "rate": 0.9505,
            "reason": "英文讹字率 0.9505（正形 22／讹形 422）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9505,
        "reason": "英文讹字率 0.9505（正形 22／讹形 422）",
        "file": "annualregistervi00jeff.txt"
      },
      "src-29b9a8e05249": {
        "words": 92748,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1937.3,
            "panel_good": 7,
            "panel_bad": 13,
            "若无语种门会读到": 0.65,
            "verdict": "未核",
            "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_notes-on-the-state-of-vi_jefferson-thomas_1787.txt"
      },
      "src-96915834ac95": {
        "words": 35238,
        "diagnostic_est_eft": [
          0,
          141
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 1.0000；英文：锚 6.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "bub_gb_LlJBAAAAcAAJ.txt"
      },
      "src-7fde54f52a7b": {
        "words": 220921,
        "diagnostic_est_eft": [
          25,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2371.4,
            "panel_good": 2133,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2133／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2133／讹形 0）",
        "file": "cu31924026091581.txt"
      },
      "src-c850b7f2e0c7": {
        "words": 187584,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2196.9,
            "panel_good": 1544,
            "panel_bad": 1,
            "若无语种门会读到": 0.0006,
            "verdict": "干净",
            "rate": 0.0006,
            "reason": "英文讹字率 0.0006（正形 1544／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0006,
        "reason": "英文讹字率 0.0006（正形 1544／讹形 1）",
        "file": "cu31924027055718.txt"
      },
      "src-f5f2b814ba2f": {
        "words": 72918,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2267.5,
            "panel_good": 502,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 502／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 502／讹形 0）",
        "file": "cu31924028751760.txt"
      },
      "src-50bd2c33f11f": {
        "words": 219378,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2322.1,
            "panel_good": 2138,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2138／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2138／讹形 0）",
        "file": "cu31924071238426.txt"
      },
      "src-7cff9fa1ad54": {
        "words": 229461,
        "diagnostic_est_eft": [
          25,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2315.5,
            "panel_good": 2172,
            "panel_bad": 1,
            "若无语种门会读到": 0.0005,
            "verdict": "干净",
            "rate": 0.0005,
            "reason": "英文讹字率 0.0005（正形 2172／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0005,
        "reason": "英文讹字率 0.0005（正形 2172／讹形 1）",
        "file": "cu31924071238442.txt"
      },
      "src-55088e3da972": {
        "words": 231175,
        "diagnostic_est_eft": [
          73,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2397.9,
            "panel_good": 2661,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2661／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2661／讹形 0）",
        "file": "cu31924071238467.txt"
      },
      "src-611f39dd8ca3": {
        "words": 212272,
        "diagnostic_est_eft": [
          4,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1553.7,
            "panel_good": 180,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 180／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 180／讹形 0）",
        "file": "cu31924092528631.txt"
      },
      "src-2080428c7f4f": {
        "words": 145564,
        "diagnostic_est_eft": [
          27,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2198.2,
            "panel_good": 1595,
            "panel_bad": 2,
            "若无语种门会读到": 0.0013,
            "verdict": "干净",
            "rate": 0.0013,
            "reason": "英文讹字率 0.0013（正形 1595／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.0013,
        "reason": "英文讹字率 0.0013（正形 1595／讹形 2）",
        "file": "cu31924092892011.txt"
      },
      "src-b98a3e20228d": {
        "words": 140828,
        "diagnostic_est_eft": [
          46,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2070.4,
            "panel_good": 1404,
            "panel_bad": 1,
            "若无语种门会读到": 0.0007,
            "verdict": "干净",
            "rate": 0.0007,
            "reason": "英文讹字率 0.0007（正形 1404／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0007,
        "reason": "英文讹字率 0.0007（正形 1404／讹形 1）",
        "file": "cu31924092892037.txt"
      },
      "src-5ebe1ee2ca41": {
        "words": 18183,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1458.0,
            "panel_good": 93,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 93／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 93／讹形 0）",
        "file": "gpl_1600362.txt"
      },
      "src-27db67073ecf": {
        "words": 37588,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2311.1,
            "panel_good": 321,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 321／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 321／讹形 0）",
        "file": "jeffersonsgerman01jeff.txt"
      },
      "src-f20b182b53fb": {
        "words": 117523,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2377.0,
            "panel_good": 1109,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1109／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1109／讹形 0）",
        "file": "jeffersonthomas09lipsrich.txt"
      },
      "src-0604da4c825a": {
        "words": 134705,
        "diagnostic_est_eft": [
          65,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2226.4,
            "panel_good": 1207,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1207／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1207／讹形 0）",
        "file": "jeffersonthomas18lipsrich.txt"
      },
      "src-190760238a50": {
        "words": 3738,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2528.1,
            "panel_good": 2,
            "panel_bad": 19,
            "若无语种门会读到": 0.9048,
            "verdict": "未核",
            "reason": "英文面板只命中 21 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 21 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-1005111.txt"
      },
      "src-8a928a2bb062": {
        "words": 1198,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1736.2,
            "panel_good": 5,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 5 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 5 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-1921491.txt"
      },
      "src-60f178fb97d0": {
        "words": 96740,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2339.8,
            "panel_good": 998,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 998／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 998／讹形 0）",
        "file": "lettersaddresses00jeffiala.txt"
      },
      "src-70083a3cc2d9": {
        "words": 96707,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2340.1,
            "panel_good": 998,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 998／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 998／讹形 0）",
        "file": "lettersandaddres00jeffiala.txt"
      },
      "src-f02cbbe877ed": {
        "words": 96752,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2337.7,
            "panel_good": 998,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 998／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 998／讹形 0）",
        "file": "lettersandaddres00jeffuoft.txt"
      },
      "src-8bd16b706229": {
        "words": 28527,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2208.8,
            "panel_good": 726,
            "panel_bad": 1,
            "若无语种门会读到": 0.0014,
            "verdict": "干净",
            "rate": 0.0014,
            "reason": "英文讹字率 0.0014（正形 726／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0014,
        "reason": "英文讹字率 0.0014（正形 726／讹形 1）",
        "file": "lifemoralsjesusnaz00jeff.txt"
      },
      "src-252ce7838048": {
        "verdict": "未核",
        "reason": "空文本",
        "words": 0,
        "file": "lifemoralsof00jeff.txt"
      },
      "src-ac2df69c6c36": {
        "words": 52995,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2265.9,
            "panel_good": 1155,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1155／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1155／讹形 0）",
        "file": "manualofparliame00jeff.txt"
      },
      "src-1e85535aa4a1": {
        "words": 61413,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2327.8,
            "panel_good": 621,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 621／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 621／讹形 0）",
        "file": "masterthoughtsof00jeffiala.txt"
      },
      "src-fa22311720b8": {
        "words": 61982,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2319.4,
            "panel_good": 630,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 630／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 630／讹形 0）",
        "file": "masterthoughtst00jeffgoog.txt"
      },
      "src-9d4d45bfc2d0": {
        "words": 203989,
        "diagnostic_est_eft": [
          13,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2337.6,
            "panel_good": 2226,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2226／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2226／讹形 0）",
        "file": "memoircorrespond16781gut.txt"
      },
      "src-54c743809b0e": {
        "words": 212542,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2243.1,
            "panel_good": 2205,
            "panel_bad": 2,
            "若无语种门会读到": 0.0009,
            "verdict": "干净",
            "rate": 0.0009,
            "reason": "英文讹字率 0.0009（正形 2205／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.0009,
        "reason": "英文讹字率 0.0009（正形 2205／讹形 2）",
        "file": "memoirscorrespo00jeffgoog.txt"
      },
      "src-8c764b949630": {
        "words": 221632,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2255.4,
            "panel_good": 2018,
            "panel_bad": 1,
            "若无语种门会读到": 0.0005,
            "verdict": "干净",
            "rate": 0.0005,
            "reason": "英文讹字率 0.0005（正形 2018／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0005,
        "reason": "英文讹字率 0.0005（正形 2018／讹形 1）",
        "file": "memoirscorrespo01jeffgoog.txt"
      },
      "src-1eeb8d395518": {
        "words": 92999,
        "diagnostic_est_eft": [
          18,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2199.4,
            "panel_good": 1124,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1124／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1124／讹形 0）",
        "file": "notesonstateofvir00jeff.txt"
      },
      "src-b107fc414c7e": {
        "words": 92679,
        "diagnostic_est_eft": [
          8,
          7
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2230.4,
            "panel_good": 131,
            "panel_bad": 890,
            "若无语种门会读到": 0.8717,
            "verdict": "不可用",
            "rate": 0.8717,
            "reason": "英文讹字率 0.8717（正形 131／讹形 890）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8717,
        "reason": "英文讹字率 0.8717（正形 131／讹形 890）",
        "file": "notesonstateofvirg00jeff.txt"
      },
      "src-5b0ad2ebec28": {
        "words": 3391,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2385.7,
            "panel_good": 17,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 17 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 17 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "orationoncentenn00dall.txt"
      },
      "src-4f30582e77e0": {
        "words": 7646,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2300.5,
            "panel_good": 4,
            "panel_bad": 108,
            "若无语种门会读到": 0.9643,
            "verdict": "不可用",
            "rate": 0.9643,
            "reason": "英文讹字率 0.9643（正形 4／讹形 108）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9643,
        "reason": "英文讹字率 0.9643（正形 4／讹形 108）",
        "file": "summaryviewofrig00jeff_1.txt"
      },
      "src-843f7cba4fcc": {
        "words": 76379,
        "diagnostic_est_eft": [
          627,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0000；英文：锚 16.4<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.0500）",
        "file": "tudesconomiques00fovigoog.txt"
      },
      "src-6a3cf5192354": {
        "verdict": "未核",
        "reason": "空文本",
        "words": 0,
        "file": "version-final-de-la-declaracion-de-la-independencia.txt"
      },
      "src-b1b92284a86d": {
        "words": 73735,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2273.3,
            "panel_good": 510,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 510／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 510／讹形 0）",
        "file": "virginiadynasty00johnrich.txt"
      },
      "src-d114fe5c8b31": {
        "words": 135467,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2537.0,
            "panel_good": 1290,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1290／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1290／讹形 0）",
        "file": "virginiakentucky00jeff.txt"
      },
      "src-b25132260b5c": {
        "words": 142995,
        "diagnostic_est_eft": [
          23,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2254.9,
            "panel_good": 2825,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2825／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2825／讹形 0）",
        "file": "workofjeffer02jeffuoft.txt"
      },
      "src-979a7acc8e1b": {
        "words": 144406,
        "diagnostic_est_eft": [
          27,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2211.3,
            "panel_good": 1597,
            "panel_bad": 1,
            "若无语种门会读到": 0.0006,
            "verdict": "干净",
            "rate": 0.0006,
            "reason": "英文讹字率 0.0006（正形 1597／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0006,
        "reason": "英文讹字率 0.0006（正形 1597／讹形 1）",
        "file": "workofjeffer03jeffuoft.txt"
      },
      "src-06b2c10518b9": {
        "words": 143160,
        "diagnostic_est_eft": [
          23,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2370.0,
            "panel_good": 1458,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1458／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1458／讹形 0）",
        "file": "workofjeffer07jeffuoft.txt"
      },
      "src-40ab8a8e148b": {
        "words": 224545,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2310.3,
            "panel_good": 2128,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2128／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2128／讹形 0）",
        "file": "worksofjefferson02jeffuoft.txt"
      },
      "src-73c6d3d92bae": {
        "words": 229237,
        "diagnostic_est_eft": [
          25,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2317.0,
            "panel_good": 2176,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2176／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2176／讹形 0）",
        "file": "worksofjefferson06jeffuoft.txt"
      },
      "src-d7d3d12050b1": {
        "words": 243094,
        "diagnostic_est_eft": [
          31,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2356.7,
            "panel_good": 2384,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2384／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2384／讹形 0）",
        "file": "worksofjefferson07jeffuoft.txt"
      },
      "src-9a25c3c38607": {
        "words": 212494,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2279.4,
            "panel_good": 2283,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2283／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2283／讹形 0）",
        "file": "worksofjefferson09jeffuoft.txt"
      },
      "src-354b5e5d9486": {
        "words": 142616,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2169.7,
            "panel_good": 1377,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1377／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1377／讹形 0）",
        "file": "worksthomasjeff01fordgoog.txt"
      },
      "src-a34664b045f8": {
        "words": 229399,
        "diagnostic_est_eft": [
          24,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2311.3,
            "panel_good": 2169,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2169／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2169／讹形 0）",
        "file": "writingsbeinghis06jeffuoft.txt"
      },
      "src-f4676862e84f": {
        "words": 243587,
        "diagnostic_est_eft": [
          32,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2349.5,
            "panel_good": 2373,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2373／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2373／讹形 1）",
        "file": "writingsbeinghis07jeffuoft.txt"
      },
      "src-6e2ef4ff69a7": {
        "words": 124220,
        "diagnostic_est_eft": [
          10,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2498.1,
            "panel_good": 1385,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1385／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1385／讹形 0）",
        "file": "writingslibrary03jeff.txt"
      },
      "src-9c60ff696b84": {
        "words": 116700,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2380.5,
            "panel_good": 1107,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1107／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1107／讹形 0）",
        "file": "writingslibrarye00jeffuoft.txt"
      },
      "src-106864c12dfa": {
        "words": 147207,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2272.0,
            "panel_good": 2123,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2123／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2123／讹形 0）",
        "file": "writingslibrarye01jeffuoft.txt"
      },
      "src-ecdd50a73149": {
        "words": 133630,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2258.8,
            "panel_good": 1651,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1651／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1651／讹形 0）",
        "file": "writingslibrarye02jeffuoft.txt"
      },
      "src-aa3f09f9fa08": {
        "words": 126354,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2284.1,
            "panel_good": 1254,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1254／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1254／讹形 0）",
        "file": "writingslibrarye05jeffuoft.txt"
      },
      "src-353f9fbf1714": {
        "words": 133713,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2353.2,
            "panel_good": 1250,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1250／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1250／讹形 0）",
        "file": "writingslibrarye07jeffuoft.txt"
      },
      "src-929058738592": {
        "words": 119013,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2302.2,
            "panel_good": 1158,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1158／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1158／讹形 0）",
        "file": "writingslibrarye10jeffuoft.txt"
      },
      "src-146f63540200": {
        "words": 129327,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2321.9,
            "panel_good": 1192,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1192／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1192／讹形 0）",
        "file": "writingslibrarye13jeffuoft.txt"
      },
      "src-a82ff4312435": {
        "words": 124029,
        "diagnostic_est_eft": [
          16,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2405.8,
            "panel_good": 1251,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1251／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1251／讹形 0）",
        "file": "writingslibrarye16jeffuoft.txt"
      },
      "src-0e84ede7e592": {
        "words": 148006,
        "diagnostic_est_eft": [
          46,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2084.7,
            "panel_good": 1525,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1525／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1525／讹形 0）",
        "file": "writingsoft04jeffiala.txt"
      },
      "src-ad414af365c6": {
        "words": 229411,
        "diagnostic_est_eft": [
          25,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2318.7,
            "panel_good": 2177,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2177／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2177／讹形 0）",
        "file": "writingsoft06jeffiala.txt"
      },
      "src-f21716ca9d2e": {
        "words": 212435,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2282.9,
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
        "file": "writingsoft09jeffiala.txt"
      },
      "src-7e5b59c7c6af": {
        "words": 166765,
        "diagnostic_est_eft": [
          14,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2236.0,
            "panel_good": 3014,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 3014／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 3014／讹形 0）",
        "file": "writingsofthom02jeff.txt"
      },
      "src-f3ee30d59c57": {
        "words": 212909,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2271.4,
            "panel_good": 2270,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2270／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2270／讹形 0）",
        "file": "writingsofthoma09jeff.txt"
      },
      "src-965dc5776bbf": {
        "words": 123024,
        "diagnostic_est_eft": [
          15,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2402.5,
            "panel_good": 1250,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1250／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1250／讹形 0）",
        "file": "writingsofthomas0000vari_j3j9.txt"
      },
      "src-4bbb0a6ea54a": {
        "words": 219063,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2325.5,
            "panel_good": 2135,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2135／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2135／讹形 0）",
        "file": "writingsofthomas04jeffiala.txt"
      },
      "src-575e212950a7": {
        "words": 262483,
        "diagnostic_est_eft": [
          17,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2326.2,
            "panel_good": 2449,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2449／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2449／讹形 0）",
        "file": "writingsthomas13jeffrich.txt"
      },
      "src-50b6bb84870e": {
        "words": 260432,
        "diagnostic_est_eft": [
          71,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2274.0,
            "panel_good": 2807,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2807／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2807／讹形 0）",
        "file": "writingsthomas17jeffrich.txt"
      },
      "src-f6e9b6e2f70b": {
        "words": 231838,
        "diagnostic_est_eft": [
          17,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2253.1,
            "panel_good": 2392,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2392／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2392／讹形 0）",
        "file": "writingsthomasj00editgoog.txt"
      },
      "src-886efa10d584": {
        "words": 219736,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2314.4,
            "panel_good": 2123,
            "panel_bad": 1,
            "若无语种门会读到": 0.0005,
            "verdict": "干净",
            "rate": 0.0005,
            "reason": "英文讹字率 0.0005（正形 2123／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0005,
        "reason": "英文讹字率 0.0005（正形 2123／讹形 1）",
        "file": "writingsthomasj00washgoog.txt"
      },
      "src-01f67df2c755": {
        "words": 64964,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1765.7,
            "panel_good": 915,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 915／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 915／讹形 0）",
        "file": "youthofjefferson00cookiala.txt"
      },
      "src-5e680ca34b56": {
        "words": 66466,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1779.7,
            "panel_good": 936,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 936／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 936／讹形 0）",
        "file": "youthofjefferson00cookrich.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 73,
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
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "schema_drift": "✗ dedup-verdicts.jsonl: 解析失败 Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 31,
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
    "可用来源": 65,
    "**按内容去重后的作品数**": 27,
    "虚高": 2.407,
    "未声明的重复对": 0,
    "已声明的重复对": 43,
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
        "核过": 4,
        "**对不上**": [
          "extraction_status: failed"
        ]
      },
      "02-conversations.md": {
        "引文数": 3,
        "核过": 3,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 3,
        "核过": 3,
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
    "合计": "11 条引文，对不上 1 条",
    "读不到正文的来源": [],
    "holdout 源数": 7,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 68,
    "train 源总数": 73,
    "本人所著字节": 65309488,
    "train 总字节": 67215208,
    "own_voice_ratio": 0.9716,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 62616859,
    "**判据说未核验的**": 3,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-252ce7838048",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-843f7cba4fcc",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.080）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-6a3cf5192354",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 17.49,
    "**立场句/万字**": 0.12,
    "其中不含第一人称的": 478,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 66,
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
    "第一人称覆盖率": 0.438,
    "状态": "无候选（第一人称覆盖率 0.438）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-jefferson-175/workspaces/thomas-jefferson/evidence/source-ledger.jsonl",
    "一手份数": 58,
    "台账总份数": 65,
    "一手占比": 0.8923,
    "有材料的道数": 6,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 72,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-cb8911bf2cd9 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 73,
    "声称公有领域": 0,
    "不声称（不判）": 73,
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
    "台账行数": 73,
    "**`title` 就是文件名**": 0,
    "真书目题名": 73,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 1,
    "有一边没年份": 72,
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
    "实测声明": 0,
    "同段带数": 0,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0,
    "状态": "**一处实测声明都没扫到——本次什么也没检查，不构成通过。**合成阶段常态如此（断言层通常不写「我量过」），**但发布阶段若仍是 0，要去看是不是扫错了单元。**"
  },
  "evidence_per_claim": {
    "断言条数": 25,
    "source_ids": "逐条各异（非空 25/25，不同取值 21）",
    "evidence_clusters": "逐条各异（非空 25/25，不同取值 24）",
    "counter_source_ids": "整批都空（非空 0/25，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 3,
    "作品组数（连通分量，仅供参考）": 35,
    "来源数": 73,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 34,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 31,
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-jefferson-175/workspaces/thomas-jefferson/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  facts.md               clm-03a799ad3834",
      "           **独立宣言的自明真理段——两个编本逐字不同。** `We hold these truths to be self-evident, that all men are cre…",
      "",
      "低于 10% 的 39 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-jefferson-175/workspaces/thomas-jefferson/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-jefferson-175/workspaces/thomas-jefferson/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.9153,
  "baseline_overall": 0.6188,
  "candidate_baseline_delta": 0.2966,
  "suite_candidate_means": {
    "known": 0.925,
    "boundary": 0.915,
    "voice": 0.88,
    "trajectory": 0.9,
    "contrast": 0.95,
    "fact-preservation": 0.95,
    "style-decoy": 0.9,
    "task-completion": 0.95,
    "planning-fidelity": 0.93,
    "tool-use": 0.935,
    "capability-calibration": 0.95,
    "refusal-stop": 0.95,
    "long-horizon": 0.925,
    "identity-routing": 0.725,
    "anonymous-fidelity": 0.935,
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
  "claim_coverage_checked": "实际检查 19/25 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 6 未纳入）",
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

- `corpus.longs-corruption`: **3 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-3f4febe479e3` annualregistervi00jeff.txt —— 英文讹字率 0.9505（正形 22／讹形 422），**不可做逐字引文**
- `corpus.unexamined-band`: **1/73 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- research.lane_quotes：1 条逐字引文回原文对不上——**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
