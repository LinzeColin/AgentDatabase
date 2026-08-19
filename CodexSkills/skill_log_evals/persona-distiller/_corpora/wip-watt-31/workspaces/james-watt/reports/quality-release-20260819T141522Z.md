# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-watt-31/workspaces/james-watt`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T14:15:22Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 25,
    "claims": 18
  },
  "sources_total": 25,
  "sources_train": 20,
  "sources_usable_train": 20,
  "sources_holdout": 5,
  "primary_sources": 20,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 12,
    "conversations": 2,
    "expression": 2,
    "external": 3,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 21,
    "已证实归属": 14,
    "存疑（有正面证据但另有他人署名）": [
      "src-cb1806bfbe54 bim_eighteenth-century_an-account-of-the-scheme_watt-james_1774.txt [A-byline] 另有他人署名：by WILLIAM AULD"
    ],
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "6 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 25,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "references/holdout/src-ed47684ffeb8/jameswattletter00watt.normalized.txt　过短：622 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "James Watt（1736–1819）的署名形态在 archive.org 著录与题名页上均可见：\n  ① 医学/化学著作（1794–1796）：题名页逐字",
    "citation": "James Watt（1736-1819）的全部一手载体：医学化学合著（题名页 By THOMAS BEDDOES M. D. AND JAMES WATT, ",
    "争议篇目数": 1,
    "P1 声称本人所著": 21,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-watt-31/namesake-gate.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 9,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 9,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 20,
    "fact 类条数": 8,
    "**人物事实**（计入）": 8,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 0,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 0,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**未达**": [
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 0 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 1,
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 25,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "bim_eighteenth-century_considerations-on-the-m_watt-james_1714.txt",
        "非拉丁字符": 38,
        "全同形字词": 3,
        "样例": [
          "ον 读作 ov",
          "ον 读作 ov",
          "ο 读作 o"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 9,
      "干净": 8,
      "未核": 5,
      "不适用": 2,
      "混杂": 1
    },
    "逐份": {
      "src-d6c1f2f3ad1a": {
        "words": 11455,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2436.5,
            "panel_good": 3,
            "panel_bad": 82,
            "若无语种门会读到": 0.9647,
            "verdict": "不可用",
            "rate": 0.9647,
            "reason": "英文讹字率 0.9647（正形 3／讹形 82）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9647,
        "reason": "英文讹字率 0.9647（正形 3／讹形 82）",
        "file": "b21438912.txt"
      },
      "src-3f1e1c01b32e": {
        "words": 5609,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2319.5,
            "panel_good": 0,
            "panel_bad": 42,
            "若无语种门会读到": 1.0,
            "verdict": "不可用",
            "rate": 1.0,
            "reason": "英文讹字率 1.0000（正形 0／讹形 42）"
          }
        },
        "verdict": "不可用",
        "rate": 1.0,
        "reason": "英文讹字率 1.0000（正形 0／讹形 42）",
        "file": "b21438924.txt"
      },
      "src-249b0d172eeb": {
        "words": 61136,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2068.5,
            "panel_good": 26,
            "panel_bad": 382,
            "若无语种门会读到": 0.9363,
            "verdict": "不可用",
            "rate": 0.9363,
            "reason": "英文讹字率 0.9363（正形 26／讹形 382）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9363,
        "reason": "英文讹字率 0.9363（正形 26／讹形 382）",
        "file": "b2143895x.txt"
      },
      "src-940377bd1648": {
        "words": 33939,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1985.9,
            "panel_good": 13,
            "panel_bad": 255,
            "若无语种门会读到": 0.9515,
            "verdict": "不可用",
            "rate": 0.9515,
            "reason": "英文讹字率 0.9515（正形 13／讹形 255）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9515,
        "reason": "英文讹字率 0.9515（正形 13／讹形 255）",
        "file": "b21438961.txt"
      },
      "src-87bca72153cd": {
        "words": 77381,
        "diagnostic_est_eft": [
          3,
          14
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2056.1,
            "panel_good": 15,
            "panel_bad": 557,
            "若无语种门会读到": 0.9738,
            "verdict": "不可用",
            "rate": 0.9738,
            "reason": "英文讹字率 0.9738（正形 15／讹形 557）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9738,
        "reason": "英文讹字率 0.9738（正形 15／讹形 557）",
        "file": "b21438973.txt"
      },
      "src-988f1651ea8b": {
        "words": 67033,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2056.0,
            "panel_good": 15,
            "panel_bad": 436,
            "若无语种门会读到": 0.9667,
            "verdict": "不可用",
            "rate": 0.9667,
            "reason": "英文讹字率 0.9667（正形 15／讹形 436）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9667,
        "reason": "英文讹字率 0.9667（正形 15／讹形 436）",
        "file": "b21438985.txt"
      },
      "src-2723ba213739": {
        "words": 27733,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2033.7,
            "panel_good": 6,
            "panel_bad": 176,
            "若无语种门会读到": 0.967,
            "verdict": "不可用",
            "rate": 0.967,
            "reason": "英文讹字率 0.9670（正形 6／讹形 176）"
          }
        },
        "verdict": "不可用",
        "rate": 0.967,
        "reason": "英文讹字率 0.9670（正形 6／讹形 176）",
        "file": "b21439011.txt"
      },
      "src-c8ba29e4e56f": {
        "words": 1812,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2317.9,
            "panel_good": 32,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 32／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 32／讹形 0）",
        "file": "b30741208.txt"
      },
      "src-2e4db495da65": {
        "words": 6429,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1805.9,
            "panel_good": 0,
            "panel_bad": 2,
            "若无语种门会读到": 1.0,
            "verdict": "未核",
            "reason": "英文面板只命中 2 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 2 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_an-account-of-the-naviga_watt-james_1767.normalized.txt"
      },
      "src-cb1806bfbe54": {
        "words": 4322,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2214.3,
            "panel_good": 1,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 1 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 1 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_an-account-of-the-scheme_watt-james_1774.txt"
      },
      "src-0c0810b477fd": {
        "words": 6207,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2178.2,
            "panel_good": 1,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 1 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 1 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_eighteenth-century_directions-for-using-the_james-watt-and-company_1780.normalized.txt"
      },
      "src-43a0f384abea": {
        "words": 107585,
        "diagnostic_est_eft": [
          194,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1780.7,
            "panel_good": 762,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 762／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 762／讹形 0）",
        "file": "correspondenceof00wattrich.txt"
      },
      "src-8ffa99140349": {
        "words": 108705,
        "diagnostic_est_eft": [
          184,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1758.5,
            "panel_good": 755,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 755／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 755／讹形 0）",
        "file": "india.history.resource.37301.txt"
      },
      "src-c7ed5ff61fb1": {
        "words": 102509,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2191.5,
            "panel_good": 850,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 850／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 850／讹形 0）",
        "file": "india.history.resource.111611.txt"
      },
      "src-cf6a46ca135f": {
        "words": 101695,
        "diagnostic_est_eft": [
          19,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1966.8,
            "panel_good": 766,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 766／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 766／讹形 0）",
        "file": "india.history.resource.111621.txt"
      },
      "src-7ed594ab9f7c": {
        "words": 83064,
        "diagnostic_est_eft": [
          24,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2342.3,
            "panel_good": 1120,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1120／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1120／讹形 0）",
        "file": "india.history.resource.111682.txt"
      },
      "src-ed47684ffeb8": {
        "words": 149,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 268.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "jameswattletter00watt.normalized.txt"
      },
      "src-18fcf6a6cbc6": {
        "words": 8422,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2450.7,
            "panel_good": 2,
            "panel_bad": 54,
            "若无语种门会读到": 0.9643,
            "verdict": "不可用",
            "rate": 0.9643,
            "reason": "英文讹字率 0.9643（正形 2／讹形 54）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9643,
        "reason": "英文讹字率 0.9643（正形 2／讹形 54）",
        "file": "jstor-106594.normalized.txt"
      },
      "src-69d5724b1ff2": {
        "words": 1406,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2311.5,
            "panel_good": 2,
            "panel_bad": 10,
            "若无语种门会读到": 0.8333,
            "verdict": "未核",
            "reason": "英文面板只命中 12 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 12 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-106595.txt"
      },
      "src-41798f2567f2": {
        "words": 1486,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2173.6,
            "panel_good": 2,
            "panel_bad": 11,
            "若无语种门会读到": 0.8462,
            "verdict": "未核",
            "reason": "英文面板只命中 13 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 13 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-106599.txt"
      },
      "src-bba7409076c3": {
        "words": 13565,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2372.3,
            "panel_good": 123,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 123／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 123／讹形 0）",
        "file": "jstor-41323679.txt"
      },
      "src-982d25f0d292": {
        "words": 196878,
        "diagnostic_est_eft": [
          36,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2053.6,
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
        "file": "livesboultonand00unkngoog.txt"
      },
      "src-ffef3251462d": {
        "words": 96319,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2389.5,
            "panel_good": 1046,
            "panel_bad": 14,
            "若无语种门会读到": 0.0132,
            "verdict": "混杂",
            "rate": 0.0132,
            "reason": "英文讹字率 0.0132（正形 1046／讹形 14）"
          }
        },
        "verdict": "混杂",
        "rate": 0.0132,
        "reason": "英文讹字率 0.0132（正形 1046／讹形 14）",
        "file": "georgewilliamso00wattgoog.txt"
      },
      "src-76d70fe67498": {
        "words": 47170,
        "diagnostic_est_eft": [
          347,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0166；英文：锚 25.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2000）",
        "file": "manueldelingeni00wattgoog.normalized.txt"
      },
      "src-972420296c9f": {
        "words": 82033,
        "diagnostic_est_eft": [
          2,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1336.0,
            "panel_good": 6,
            "panel_bad": 26,
            "若无语种门会读到": 0.8125,
            "verdict": "不可用",
            "rate": 0.8125,
            "reason": "英文讹字率 0.8125（正形 6／讹形 26）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8125,
        "reason": "英文讹字率 0.8125（正形 6／讹形 26）",
        "file": "bim_eighteenth-century_considerations-on-the-m_watt-james_1714.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 25,
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
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里没有跨题共享的语料片段——**无从比对，不是通过**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "unsourced_names": "✓ 没有查无实据的人名",
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认"
  },
  "quote_speaker": {
    "长逐字引文": 3,
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
    "★ 与出厂模板逐字相同、已豁免": 16,
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
    "可用来源": 20,
    "**按内容去重后的作品数**": 15,
    "虚高": 1.333,
    "未声明的重复对": 0,
    "已声明的重复对": 6,
    "★ 本件看不见的份数（文本太短／中日韩，不是已核）": 0
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
    "holdout 源数": 5,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.7141,
      "第三人称": 0.2859,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0,
      "已标的份数": 25,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 23,
    "train 源总数": 25,
    "本人所著字节": 6039755,
    "train 总字节": 7965398,
    "own_voice_ratio": 0.7582,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 5519164,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 12.41,
    "**立场句/万字**": 0.13,
    "其中不含第一人称的": 42,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 21,
    "**疑似著录卡**": {},
    "读不到正文的": [],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "逐字英文引文": 7,
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
    "已扫载荷": 1,
    "已扫答案": 32,
    "拒答溢出候选": 1,
    "**这几条值得人去读一眼**": [
      "case-boundary-1"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "载荷": "baseline.v1.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.281,
    "状态": "**候选：基线可能不入戏**（第一人称覆盖率 0.281 < 0.4）",
    "**这几条值得人去读一眼**": [
      "case-known-1",
      "case-known-2",
      "case-boundary-1",
      "case-trajectory-1",
      "case-trajectory-2",
      "case-contrast-1",
      "case-contrast-2",
      "case-fact-preservation-1"
    ],
    "★ 口径": "按整份载荷算第一人称覆盖率，**不判单条**——中文成句常省主语，Harvey #103 的 `hv-decoy-01` 通篇无「我」而完全是入戏的。\n★★ **这是候选名单，不是判决**：阈值在 22 个已判分人物上拟合，对第 23 个人没有保证。**去读原文，看它是在扮演这个人还是在介绍这个人。**"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-watt-31/workspaces/james-watt/evidence/source-ledger.jsonl",
    "一手份数": 20,
    "台账总份数": 20,
    "一手占比": 1.0,
    "有材料的道数": 5,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 25,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-d6c1f2f3ad1a 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 25,
    "声称公有领域": 25,
    "不声称（不判）": 0,
    "有据可查": 0,
    "有结论无依据": 25,
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
    "台账行数": 25,
    "**`title` 就是文件名**": 0,
    "真书目题名": 25,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 1,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 4,
    "有一边没年份": 21,
    "**逐条**": [
      {
        "source_id": "src-972420296c9f",
        "文件名": "bim_eighteenth-century_considerations-on-the-m_watt-james_1714.txt",
        "文件名里的年份": [
          1714
        ],
        "台账 published_at": 1794,
        "差": 80
      }
    ],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 18,
  "claims_active": 18,
  "mental_models": 3,
  "heuristics": 4,
  "claim_markers": 18,
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
    "已扫单元": 3,
    "实测声明": 17,
    "同段带数": 14,
    "**光说不给数**": 3,
    "诚实弃权（不计问题）": 0,
    "**逐条**": [
      "judge_payload.v1.json/case-style-decoy-1　「测得」：我以一位机师的诚实作答。量子金融交易——我在分离冷凝器的实验中从未测得它，也不曾在 Boulton 的账册上见过它的踪迹。每磅煤节省多少柴，我能量准；汽缸压力几分，我算得清；但价格波动的随机性，我承认测不准。要我宣称精通",
      "judge_payload.v1.json/case-identity-routing-1　「实测」：分开记账，先后分明。蒸汽机这边以实测定标：量汽耗、煤耗、每分钟冲程数，唯一准绳是每蒲式耳煤打出多少英尺·磅的功——浪费即缺陷。任何改动先在小比例模型上验证，模型不省煤，绝不放大；分离冷凝器每一步都是这样量出来的。化学实验",
      "judge_payload.v1.json/case-identity-routing-2　「实测」：商业营销非我本行，此点我须先言明。我以蒸汽做功为业，凡断言必以实测为据，故我的判据是：这任务能否交付可验证之产物。若营销要我供给机器之效率数据、汽耗实测——那是可量化之事实，我责无旁贷，且乐于以数字说话。若要我起草话术、"
    ],
    "口径": "借了实测的权威却没交出实测的内容。**两条出路：把数补上，或改成弃权式**——弃权不会被报出，它是诚实的。"
  },
  "evidence_per_claim": {
    "断言条数": 18,
    "source_ids": "逐条各异（非空 18/18，不同取值 16）",
    "evidence_clusters": "逐条各异（非空 18/18，不同取值 16）",
    "counter_source_ids": "整批都空（非空 0/18，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 9,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 20,
    "来源数": 25,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 1,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 1,
    "取不到正文的源": 0,
    "例": []
  },
  "answer_constraints": {
    "用例数": 32,
    "声明了约束的用例": 0,
    "声明的约束条数": 0,
    "实际核过的": 0,
    "**未过**": 0,
    "口径": "**只检显式声明的约束**——题面里的自然语言约束提取不了（已试过并否掉）。**「0 处未过」不等于「全部接住了」**，要连「声明了几条」一起读。",
    "未接住的": []
  },
  "verbatim_pointer": {
    "答案总数": 32,
    "**问原话/出处的题**": 0,
    "其中只给指路的": 0,
    "状态": "**本人物没有这类题——未核，不是通过**",
    "只给指路的": "无"
  },
  "activation_yield": {
    "退出码": 0,
    "输出": [
      "judge_payload.v1.json:",
      "   substantive_lines: 34",
      "   bookkeeping_lines: 3",
      "   payload_lines: 31",
      "   bookkeeping_ratio: 0.0882",
      "   payload_ratio: 0.9118"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  boundaries.md          clm-000000000012",
      "           低估组织化制造的复杂度：Soho 的规模化生产主要靠 Boulton 的商业与组织能力补足，Watt 对资金与市场运作存在盲区（早期与 Roebuck 合伙失败为证）。…",
      "",
      "低于 10% 的 59 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "退出码": 0,
    "输出": [
      "可验算的数列 0 处，加得平 0 处，**加不平 0 处**",
      "  ⚠ **一处可验算的数列都没扫到——本次未检查（不是通过）**"
    ]
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-watt-31/workspaces/james-watt/audit/source-coverage.json），**未核验**（不是通过）"
  },
  "unqualified_priority": {
    "第一人称首创声明": 0,
    "其中带限定": 0,
    "扫了几个文件": 1,
    "状态": "一处首创声明都没扫到。**这可能是产物干净，也可能是判据窄**——v0.0.0.73 第一版就在真数据上报过一次假的 0。"
  },
  "sole_authorship": {
    "合著／集体署名的源": 1,
    "引用它们又用第一人称的段落": 0,
    "已划界": 0,
    "**独揽**": 0
  },
  "eval_results": 172,
  "candidate_overall": 0.8831,
  "baseline_overall": 0.745,
  "candidate_baseline_delta": 0.1381,
  "suite_candidate_means": {
    "known": 0.915,
    "boundary": 0.89,
    "voice": 0.945,
    "trajectory": 0.905,
    "contrast": 0.89,
    "fact-preservation": 0.91,
    "style-decoy": 0.94,
    "task-completion": 0.71,
    "planning-fidelity": 0.87,
    "tool-use": 0.875,
    "capability-calibration": 0.94,
    "refusal-stop": 0.925,
    "long-horizon": 0.77,
    "identity-routing": 0.825,
    "anonymous-fidelity": 0.93,
    "token-efficiency": 0.89
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "整组偏弱": [
      "fact-preservation　均分 0.9100 < 0.93　整组偏弱（去掉最低仍 0.9200）"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 11/18 条（其中按引文判据 1 条；语料元断言 0、无实体无引文 7 未纳入）",
  "baseline_provenance": {
    "baseline_rows": 86,
    "by_source": {
      "unknown": 86
    },
    "usable_rows": 0,
    "unusable_rows": 86,
    "capability_evidence": false
  },
  "secret_findings": 0
}
```

## Errors

- `eval.surface-leak`: **表面特征会指出哪一侧是候选**，这一轮的盲判不成立：**总体均长比 0.61 < 0.77**——候选整体过短，长度同样会变成指认信号（**反方向的同一个问题**）；**候选更短的题多达 32/32 = 100%，要 ≤75%**——一边倒同样能指认，只是倒的方向反了
- `content.self-count-wrong`: **自报字数与实数对不上**——主动邀请核对的数字自己错了，比不给更伤。　⚠ case-planning-fidelity-2: 自称「字数一字」，实数 58（含标点 66／不含 58）：「撰写专利，先造模型，再动笔墨。分离冷凝器在格拉斯哥模型上烧了两年火、」
- `content.quote-no-locator`: 有逐字引文无从回查：同段内既无年份也无卷页刊名。长逐字引文 4 条，同段带坐标 2 条，**缺坐标 2 条**

## Warnings

- `corpus.longs-corruption`: **9 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-d6c1f2f3ad1a` b21438912.txt —— 英文讹字率 0.9647（正形 3／讹形 82），**不可做逐字引文**
- `corpus.unexamined-band`: **1/25 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `source.filename-year-mismatch`: 1 条文件名年份与 `published_at` 差 ≥2 年 —— **至少有一处记错了**；判据不知道是哪一处
- `eval.baseline-not-capability-evidence`: 86/86 条基线不可作能力证据（{'unknown': 86}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
