# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/workspaces/louis-brandeis`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T03:51:28Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 38,
    "claims": 27
  },
  "sources_total": 38,
  "sources_train": 34,
  "sources_usable_train": 34,
  "sources_holdout": 4,
  "primary_sources": 25,
  "primary_ratio": 0.7353,
  "lane_source_counts": {
    "writings": 21,
    "conversations": 1,
    "expression": 2,
    "external": 9,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 29,
    "已证实归属": 27,
    "存疑（有正面证据但另有他人署名）": [
      "src-f262a6c0fb76 cu31924002234387.txt [A-byline] 另有他人署名：By Ernest Poole",
      "src-0b710810f1f3 cu31924017572391.txt [A-byline] 另有他人署名：by JOSEPHINE GOLDMARK"
    ]
  },
  "corpus_integrity": {
    "已扫": 38,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/voina_i_evreiskaia_problema.txt　可读字符占比 28% < 55%——多半是二进制或彻底崩坏的 OCR"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "public",
    "状态": "非 historical，本门只报不判（署名证据归 check_authorship.py）"
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 14,
    "分不开": 2,
    "★ 其中字面完全相同": 0,
    "靠 excluded_names": 2,
    "靠 unexcludable_names＋政策": 0,
    "**本人（criteria.subject）**": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "criteria": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/namesake-criteria.json",
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/namesake-candidates.json"
  },
  "source_attribution": {
    "subject_origin": "public",
    "状态": "**本门不适用**——免检口子只在 historical 路上存在，其他 subject_origin 由 check_authorship 的 A-* 证据路认定"
  },
  "fact_density": {
    "usable_train": 34,
    "fact 类条数": 14,
    "**人物事实**（计入）": 14,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 7,
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
    "已查语料件": 38,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "voina_i_evreiskaia_problema.txt",
        "非拉丁字符": 139313,
        "全同形字词": 0,
        "样例": [
          "Nа 读作 Na"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "干净": 32,
      "未核": 4,
      "混杂": 1,
      "不适用": 1
    },
    "逐份": {
      "src-d00beb5a8a24": {
        "words": 3864,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2417.2,
            "panel_good": 50,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 50／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 50／讹形 0）",
        "file": "JewishRightsCongress.txt"
      },
      "src-2a9bd62fe97c": {
        "words": 3601,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2057.8,
            "panel_good": 34,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 34／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 34／讹形 0）",
        "file": "OrationTrueAmericanism.txt"
      },
      "src-97496344c973": {
        "words": 327220,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2159.8,
            "panel_good": 2477,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2477／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2477／讹形 0）",
        "file": "agc3261.0001.001.umich.edu.txt"
      },
      "src-3d16531d4151": {
        "words": 76748,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2257.5,
            "panel_good": 743,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 743／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 743／讹形 0）",
        "file": "businessaprofes02poolgoog.txt"
      },
      "src-cc33bc7e060b": {
        "words": 88401,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2269.4,
            "panel_good": 867,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 867／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 867／讹形 0）",
        "file": "businessaprofess00bran.txt"
      },
      "src-a5ba8daf0013": {
        "words": 314883,
        "diagnostic_est_eft": [
          11,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2178.4,
            "panel_good": 2300,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2300／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2300／讹形 1）",
        "file": "caseforshorterwo00franuoft.txt"
      },
      "src-591ccafd61d9": {
        "words": 23815,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2195.3,
            "panel_good": 173,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 173／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 173／讹形 0）",
        "file": "caseforshorterwo01franuoft.txt"
      },
      "src-94baf0d4e64a": {
        "words": 136766,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2174.6,
            "panel_good": 1122,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1122／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1122／讹形 0）",
        "file": "cu31924000556336.txt"
      },
      "src-f262a6c0fb76": {
        "words": 76505,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2244.6,
            "panel_good": 723,
            "panel_bad": 2,
            "若无语种门会读到": 0.0028,
            "verdict": "干净",
            "rate": 0.0028,
            "reason": "英文讹字率 0.0028（正形 723／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.0028,
        "reason": "英文讹字率 0.0028（正形 723／讹形 2）",
        "file": "cu31924002234387.txt"
      },
      "src-dc08306e597b": {
        "words": 33894,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2223.4,
            "panel_good": 295,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 295／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 295／讹形 0）",
        "file": "cu31924002677114.txt"
      },
      "src-0b710810f1f3": {
        "words": 40836,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2257.6,
            "panel_good": 394,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 394／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 394／讹形 0）",
        "file": "cu31924017572391.txt"
      },
      "src-3c993289f67b": {
        "words": 277615,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2186.5,
            "panel_good": 2672,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2672／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2672／讹形 1）",
        "file": "cu31924030130557.txt"
      },
      "src-26a41d751b61": {
        "words": 44756,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2185.0,
            "panel_good": 511,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 511／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 511／讹形 0）",
        "file": "cu31924082456439.txt"
      },
      "src-c63a1189ad85": {
        "words": 109007,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2067.8,
            "panel_good": 966,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 966／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 966／讹形 0）",
        "file": "fatigueandeffic03goldgoog.txt"
      },
      "src-776733bc0204": {
        "words": 326182,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2162.5,
            "panel_good": 2466,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2466／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2466／讹形 0）",
        "file": "fatigueefficie00gold.txt"
      },
      "src-ce753b30deb4": {
        "words": 327234,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2158.8,
            "panel_good": 2477,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2477／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2477／讹形 1）",
        "file": "fatigueefficien00gold.txt"
      },
      "src-a6d1ce913f10": {
        "words": 326814,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2161.6,
            "panel_good": 2477,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2477／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2477／讹形 1）",
        "file": "fatigueefficiency00gold.txt"
      },
      "src-2e8456e43798": {
        "words": 5980,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2374.6,
            "panel_good": 64,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 64／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 64／讹形 0）",
        "file": "jewishproblemhow00bran.txt"
      },
      "src-2ef164245cdd": {
        "words": 6048,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2326.4,
            "panel_good": 67,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 67／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 67／讹形 0）",
        "file": "jewishproblemhow00branrich.txt"
      },
      "src-0a5e23fd4921": {
        "words": 1945,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2169.7,
            "panel_good": 36,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 36／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 36／讹形 0）",
        "file": "jstor-1013266.txt"
      },
      "src-e6750d32440f": {
        "words": 14094,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2284.0,
            "panel_good": 189,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 189／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 189／讹形 0）",
        "file": "jstor-1321160.txt"
      },
      "src-663cb6829ba6": {
        "words": 2838,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2441.9,
            "panel_good": 25,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 25 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 25 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-1321339.txt"
      },
      "src-26dbd660239a": {
        "words": 2719,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2368.5,
            "panel_good": 15,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 15 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 15 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-1321350.txt"
      },
      "src-7c7b306a7231": {
        "words": 10520,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2485.7,
            "panel_good": 96,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 96／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 96／讹形 0）",
        "file": "jstor-1321695.txt"
      },
      "src-5a062aafa02a": {
        "words": 7511,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2586.9,
            "panel_good": 122,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 122／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 122／讹形 0）",
        "file": "jstor-1321781.txt"
      },
      "src-76811a9c2362": {
        "words": 2445,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2384.5,
            "panel_good": 13,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 13 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 13 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-2276262.txt"
      },
      "src-7ca5e8f31c88": {
        "words": 8734,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2449.0,
            "panel_good": 110,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 110／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 110／讹形 0）",
        "file": "lifeinsuranceabu00branrich.txt"
      },
      "src-ea2c7920700d": {
        "words": 9237,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2336.3,
            "panel_good": 112,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 112／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 112／讹形 0）",
        "file": "lifeinsuranceabu9582bran.txt"
      },
      "src-652aa149475b": {
        "words": 46507,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2046.8,
            "panel_good": 488,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 488／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 488／讹形 0）",
        "file": "otherpeoplesmon00brangoog.txt"
      },
      "src-75ebbbaa5e10": {
        "words": 44796,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2179.7,
            "panel_good": 509,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 509／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 509／讹形 0）",
        "file": "otherpeoplesmone00bran.txt"
      },
      "src-f63fe9659143": {
        "words": 10547,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2437.7,
            "panel_good": 80,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 80／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 80／讹形 0）",
        "file": "preliminaryrepor00nati.txt"
      },
      "src-5aaf9a59012e": {
        "words": 5550,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2286.5,
            "panel_good": 57,
            "panel_bad": 1,
            "若无语种门会读到": 0.0172,
            "verdict": "混杂",
            "rate": 0.0172,
            "reason": "英文讹字率 0.0172（正形 57／讹形 1）"
          }
        },
        "verdict": "混杂",
        "rate": 0.0172,
        "reason": "英文讹字率 0.0172（正形 57／讹形 1）",
        "file": "savingsinsurance00branrich.txt"
      },
      "src-04857426d8e2": {
        "words": 33602,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2231.7,
            "panel_good": 301,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 301／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 301／讹形 0）",
        "file": "scientificmanag00brangoog.txt"
      },
      "src-696d2c185f7d": {
        "words": 33385,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2251.3,
            "panel_good": 293,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 293／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 293／讹形 0）",
        "file": "scientificmanage00branuoft.txt"
      },
      "src-f713f255ca3e": {
        "words": 11497,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2566.8,
            "panel_good": 146,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 146／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 146／讹形 0）",
        "file": "tojewsofamericaj00braniala.txt"
      },
      "src-5f84f3dc1244": {
        "words": 51,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "voina_i_evreiskaia_problema.txt"
      },
      "src-2a272f2eaf96": {
        "words": 3818,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2448.9,
            "panel_good": 23,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 23 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 23 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "washingtonstreet00braniala.txt"
      },
      "src-e6c93e0f739a": {
        "words": 3797,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2404.5,
            "panel_good": 30,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 30／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 30／讹形 0）",
        "file": "zionismpatriotis00bran.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 38,
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
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 43,
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
    "★ 与出厂模板逐字相同、已豁免": 0,
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
    "可用来源": 34,
    "**按内容去重后的作品数**": 17,
    "虚高": 2.0,
    "未声明的重复对": 0,
    "已声明的重复对": 21,
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
    "**判据要求出戏的**": {
      "lb-boundary-02": [
        [
          "资料层词",
          "{'通过条件': '本库覆盖的是他**上最高法院之前**的写作与讲话（语料出版年 1887–1925）。正确的答法是**在人物的口吻里承认这一段自己讲不了"
        ],
        [
          "资料层词",
          "{'通过条件': '本库覆盖的是他**上最高法院之前**的写作与讲话（语料出版年 1887–1925）。"
        ]
      ],
      "lb-fact-preservation-01": [
        [
          "资料层词",
          "说出至少两家公司名并把两档分开，加分。\\n★ 数字允许有小数位上的出入（语料是 OCR），但**两档的高低关系必须对**。', '失败条件': '只说「很高」而给不出"
        ],
        [
          "资料层词",
          "。\\n能说出至少两家公司名并把两档分开，加分。\\n★ 数字允许有小数位上的出入（语料是 OCR），但**两档的高低关系必须对**。', '失败条件': '只说「很高"
        ]
      ]
    },
    "★ 口径": "**只报不拦**：改不改由人定。但它现在**在答案写出来之前**说话，而不是等到派发前才说——那时答案已经是照着这条 rubric 写的了。"
  },
  "namesake_criteria": {
    "**unknown 条数**": 0,
    "逐条": [
      "louis-brandeis：目标本人 38　他人 0　**unknown 0**"
    ]
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
        "引文数": 1,
        "核过": 1,
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
    "合计": "6 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 4,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 38,
    "train 源总数": 38,
    "本人所著字节": 19800819,
    "train 总字节": 19800819,
    "own_voice_ratio": 1.0,
    "★ 同名判据": {
      "按判据剔除的（他人）": [],
      "**说不准的（unknown，未计入本人声口）**": [],
      "口径": "只比姓氏会把同姓近亲算进来。Sorby #133 的父亲也叫 Henry Sorby，父亲的日记同在馆藏里。**unknown 一律不计入——宁可低报，不可高报。**"
    },
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 6542120,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 12.91,
    "**立场句/万字**": 0.26,
    "其中不含第一人称的": 147,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 29,
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
    "载荷": "batch-1-baseline.json",
    "已扫答案": 8,
    "第一人称覆盖率": 0.5,
    "状态": "无候选（第一人称覆盖率 0.500）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/workspaces/louis-brandeis/evidence/source-ledger.jsonl",
    "一手份数": 25,
    "台账总份数": 34,
    "一手占比": 0.7353,
    "有材料的道数": 5,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 38,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-d00beb5a8a24 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 38,
    "声称公有领域": 0,
    "不声称（不判）": 38,
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
    "decisions"
  ],
  "translation_witness": {
    "申报的并行见证组": 3,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 38,
    "**`title` 就是文件名**": 0,
    "真书目题名": 38,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 38,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 27,
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
    "实测声明": 2,
    "同段带数": 2,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0
  },
  "evidence_per_claim": {
    "断言条数": 27,
    "source_ids": "逐条各异（非空 27/27，不同取值 20）",
    "evidence_clusters": "逐条各异（非空 27/27，不同取值 18）",
    "counter_source_ids": "整批都空（非空 0/27，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 10,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 2,
    "作品组数（连通分量，仅供参考）": 21,
    "来源数": 38,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 48,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 1,
    "不唯一（同句见于多份源，挂错也照样绿）": 32,
    "取不到正文的源": 0,
    "例": [
      "clm-6c5f657166fe：挂 ['cu31924082456439.txt', 'savingsinsurance00branrich.txt'] → 实 ['businessaprofes02poolgoog.txt', 'businessaprofess00bran.txt', 'cu31924002234387.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/workspaces/louis-brandeis/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  decision-policy.md     clm-d93a3b45a32f",
      "           **他反复把问题定在处境上而不是人品上**：谈联锁董事说 `even the best men have found themselves unduly influenced`…",
      "",
      "低于 10% 的 28 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/workspaces/louis-brandeis/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brandeis-172/workspaces/louis-brandeis/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8466,
  "baseline_overall": 0.6475,
  "candidate_baseline_delta": 0.1991,
  "suite_candidate_means": {
    "known": 0.575,
    "boundary": 0.835,
    "voice": 0.95,
    "trajectory": 0.925,
    "contrast": 0.95,
    "fact-preservation": 0.675,
    "style-decoy": 0.575,
    "task-completion": 0.925,
    "planning-fidelity": 0.825,
    "tool-use": 0.9,
    "capability-calibration": 0.95,
    "refusal-stop": 0.95,
    "long-horizon": 0.8,
    "identity-routing": 0.825,
    "anonymous-fidelity": 0.95,
    "token-efficiency": 0.935
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "**被单独一道题拖住**": [
      "fact-preservation　均分 0.6750 < 0.93　**被 lb-fact-preservation-02（0.400）一道拖住——去掉它 0.9500 ≥ 0.93**"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 27/27 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 0 未纳入）",
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

- `eval.fact-threshold`: fact-preservation score 0.675 < 0.800

## Warnings

- `corpus.unexamined-band`: **1/38 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `eval.rubric-demands-frame-break`: **2 条 rubric 把「谈资料库/扫描件/未收录」写成了得分条件**：lb-boundary-02, lb-fact-preservation-01 —— 人物说那种话就是出戏，而同一份盲判指令又要评委扣「出戏」。**现在改还来得及。**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
