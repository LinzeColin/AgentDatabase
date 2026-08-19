# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-lincoln-174/workspaces/abraham-lincoln`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T09:55:43Z`
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
  "sources_train": 67,
  "sources_usable_train": 67,
  "sources_holdout": 3,
  "primary_sources": 65,
  "primary_ratio": 0.9701,
  "lane_source_counts": {
    "writings": 43,
    "conversations": 7,
    "expression": 9,
    "external": 2,
    "decisions": 5,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 68,
    "已证实归属": 62,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "6 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 70,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "本批语料的主干是 Nicolay–Hay 编《Complete Works of Abraham Lincoln》。依据取自语料自身的题名页（逐字）：`Comp",
    "citation": "archive.org item `completeworksofa11linco`（题名页原文见上，本地校验和记于 evidence/source-ledge",
    "争议篇目数": 1,
    "P1 声称本人所著": 68,
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
    "usable_train": 67,
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
    "已查语料件": 70,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 62,
      "未核": 8
    },
    "逐份": {
      "src-6546cbb74276": {
        "words": 128330,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2266.1,
            "panel_good": 1236,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1236／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1236／讹形 0）",
        "file": "LapsleyLincWritLifeofLinc.txt"
      },
      "src-9cfd53e7a422": {
        "words": 106897,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2275.5,
            "panel_good": 989,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 989／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 989／讹形 0）",
        "file": "LapsleyLincWritsLincDoug1.txt"
      },
      "src-187a0d34e657": {
        "words": 3101,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2186.4,
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
        "file": "LincLastSpeech2.txt"
      },
      "src-3c98457dd41d": {
        "words": 52200,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1918.0,
            "panel_good": 551,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 551／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 551／讹形 0）",
        "file": "anecdotesofabrah03linc.txt"
      },
      "src-be0b3ab8adad": {
        "words": 38884,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2136.6,
            "panel_good": 357,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 357／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 357／讹形 0）",
        "file": "bestoflincolnear00linc.txt"
      },
      "src-5ef6cad0be44": {
        "words": 550543,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2242.8,
            "panel_good": 5814,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 5814／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 5814／讹形 0）",
        "file": "completeprojectg03253gut.txt"
      },
      "src-0ac5bc9653c1": {
        "words": 98865,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2168.8,
            "panel_good": 954,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 954／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 954／讹形 0）",
        "file": "completeworksab09fishgoog.txt"
      },
      "src-9a3f427492d9": {
        "words": 99623,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2153.5,
            "panel_good": 957,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 957／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 957／讹形 0）",
        "file": "completeworksab11fishgoog.txt"
      },
      "src-bcceedbd3d14": {
        "words": 400769,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2213.1,
            "panel_good": 4026,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 4026／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 4026／讹形 0）",
        "file": "completeworkscov1linc.txt"
      },
      "src-f9611096ce5f": {
        "words": 87861,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2114.0,
            "panel_good": 837,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 837／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 837／讹形 0）",
        "file": "completeworkso2127linc.txt"
      },
      "src-2709403b5402": {
        "words": 97466,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2201.9,
            "panel_good": 953,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 953／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 953／讹形 0）",
        "file": "completeworkso2129linc.txt"
      },
      "src-533cd619bcd0": {
        "words": 98464,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2218.9,
            "panel_good": 930,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 930／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 930／讹形 0）",
        "file": "completeworksof03linc.txt"
      },
      "src-0d2525d49e61": {
        "words": 96342,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2118.8,
            "panel_good": 907,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 907／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 907／讹形 0）",
        "file": "completeworksof05linc.txt"
      },
      "src-40dea3180bd4": {
        "words": 74387,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2264.1,
            "panel_good": 660,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 660／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 660／讹形 0）",
        "file": "completeworksof07linc.txt"
      },
      "src-bdc84412b7df": {
        "words": 97619,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2197.7,
            "panel_good": 954,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 954／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 954／讹形 0）",
        "file": "completeworksofa04linc.txt"
      },
      "src-b4caa81ea573": {
        "words": 73863,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2276.2,
            "panel_good": 661,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 661／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 661／讹形 0）",
        "file": "completeworksofa06linco.txt"
      },
      "src-fe2a0f60853f": {
        "words": 77879,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2205.9,
            "panel_good": 706,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 706／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 706／讹形 0）",
        "file": "completeworksofa08linco.txt"
      },
      "src-56d370d40945": {
        "words": 85829,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1783.7,
            "panel_good": 364,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 364／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 364／讹形 0）",
        "file": "completeworksofa09linc.txt"
      },
      "src-73daf6c97460": {
        "words": 81744,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2217.8,
            "panel_good": 796,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 796／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 796／讹形 0）",
        "file": "completeworksofa11linco.txt"
      },
      "src-cdb68ea774e5": {
        "words": 79518,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2192.6,
            "panel_good": 708,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 708／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 708／讹形 0）",
        "file": "completeworksofa13linc.txt"
      },
      "src-5d7e14cf08e2": {
        "words": 76668,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1400.6,
            "panel_good": 205,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 205／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 205／讹形 0）",
        "file": "completeworksofa16linc.txt"
      },
      "src-a50adfc3d4fb": {
        "words": 76630,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1400.0,
            "panel_good": 205,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 205／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 205／讹形 0）",
        "file": "completeworksofav12linc.txt"
      },
      "src-732a649f26ff": {
        "words": 88756,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2125.6,
            "panel_good": 910,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 910／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 910／讹形 0）",
        "file": "completeworksofv1linc.txt"
      },
      "src-78d403e6d5f5": {
        "words": 98278,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2224.4,
            "panel_good": 930,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 930／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 930／讹形 0）",
        "file": "completeworksofv3linc.txt"
      },
      "src-3ece5a115755": {
        "words": 97253,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2204.7,
            "panel_good": 954,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 954／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 954／讹形 0）",
        "file": "completeworksofv4linc.txt"
      },
      "src-5c96f622593c": {
        "words": 74056,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2276.3,
            "panel_good": 670,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 670／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 670／讹形 0）",
        "file": "completeworksov7linc.txt"
      },
      "src-e343dec9cc6b": {
        "words": 77702,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2130.8,
            "panel_good": 829,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 829／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 829／讹形 0）",
        "file": "completeworksov9linc.txt"
      },
      "src-93c32e416ad7": {
        "words": 88752,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2125.4,
            "panel_good": 908,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 908／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 908／讹形 0）",
        "file": "completeworkv1linc.txt"
      },
      "src-17e372b665cb": {
        "words": 78066,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2204.2,
            "panel_good": 706,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 706／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 706／讹形 0）",
        "file": "completewov10linc.txt"
      },
      "src-6d5409e5b358": {
        "words": 97199,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2204.9,
            "panel_good": 954,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 954／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 954／讹形 0）",
        "file": "completewov4linc.txt"
      },
      "src-4f1fe162a884": {
        "words": 78104,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2202.8,
            "panel_good": 705,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 705／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 705／讹形 0）",
        "file": "completewv10linc.txt"
      },
      "src-0cbd54408b14": {
        "words": 88803,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2124.6,
            "panel_good": 909,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 909／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 909／讹形 0）",
        "file": "completewv1linc.txt"
      },
      "src-c80788c2eea1": {
        "words": 374511,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2204.2,
            "panel_good": 3154,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 3154／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 3154／讹形 0）",
        "file": "completewv2linc.txt"
      },
      "src-420cfacc1b7a": {
        "words": 97405,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2204.6,
            "panel_good": 956,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 956／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 956／讹形 0）",
        "file": "completewv4linc.txt"
      },
      "src-5067960bb8f2": {
        "words": 339,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1946.9,
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
        "file": "crossofgettysbur5050linc.txt"
      },
      "src-7e649f429905": {
        "words": 374440,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2182.1,
            "panel_good": 3119,
            "panel_bad": 1,
            "若无语种门会读到": 0.0003,
            "verdict": "干净",
            "rate": 0.0003,
            "reason": "英文讹字率 0.0003（正形 3119／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0003,
        "reason": "英文讹字率 0.0003（正形 3119／讹形 1）",
        "file": "cu31924103069070.txt"
      },
      "src-34ec715ab9ad": {
        "words": 1734,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2168.4,
            "panel_good": 6,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 6 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 6 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "earlyspeechesofa1858linc.txt"
      },
      "src-3994ac473078": {
        "words": 3681,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2203.2,
            "panel_good": 63,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 63／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 63／讹形 0）",
        "file": "earlyspeechesofatslinc.txt"
      },
      "src-dc0a040e9036": {
        "words": 38953,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2123.6,
            "panel_good": 355,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 355／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 355／讹形 0）",
        "file": "earlyspeechesspr00linc.txt"
      },
      "src-81327220bc31": {
        "words": 925,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2432.4,
            "panel_good": 16,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "emancipationproc00linc.txt"
      },
      "src-db8fa016fda1": {
        "words": 11876,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2343.4,
            "panel_good": 154,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 154／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 154／讹形 0）",
        "file": "firstsecondinaug01link.txt"
      },
      "src-604e07555b56": {
        "words": 11864,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2345.8,
            "panel_good": 154,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 154／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 154／讹形 0）",
        "file": "firstsecondinaug02link.txt"
      },
      "src-9e17d9796521": {
        "words": 5401,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2294.0,
            "panel_good": 77,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 77／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 77／讹形 0）",
        "file": "gemsfromabrahaml00linc.txt"
      },
      "src-11166a3889de": {
        "words": 793,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2547.3,
            "panel_good": 16,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "generalordersno14149linc.txt"
      },
      "src-af9d9ae573da": {
        "words": 319,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2194.4,
            "panel_good": 6,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 6 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 6 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "gettysburgaddres02linc.txt"
      },
      "src-51dd7f2ad228": {
        "words": 29442,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2099.4,
            "panel_good": 288,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 288／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 288／讹形 0）",
        "file": "gettysburghspeech00lincrich.txt"
      },
      "src-ab69e48d1697": {
        "words": 23427,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2112.9,
            "panel_good": 233,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 233／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 233／讹形 0）",
        "file": "gettysburgspeec3835linc.txt"
      },
      "src-aa53d1f400e4": {
        "words": 3800,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2202.6,
            "panel_good": 49,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 49／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 49／讹形 0）",
        "file": "inauguraladdress00linc.txt"
      },
      "src-244c03202b38": {
        "words": 396813,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2205.8,
            "panel_good": 3945,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 3945／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 3945／讹形 0）",
        "file": "india.history.resource.111513.txt"
      },
      "src-2723a0056843": {
        "words": 105808,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2504.4,
            "panel_good": 809,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 809／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 809／讹形 0）",
        "file": "insurgentprivate00linc.txt"
      },
      "src-3176773929d7": {
        "words": 942,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1751.6,
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
        "file": "jstor-20086068.txt"
      },
      "src-01cdd68a3dfa": {
        "words": 123224,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2139.9,
            "panel_good": 1214,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1214／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1214／讹形 0）",
        "file": "lettersaddresses00inlinc.txt"
      },
      "src-fb5c5f0f20c2": {
        "words": 125762,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2146.8,
            "panel_good": 1230,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1230／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1230／讹形 0）",
        "file": "lettersaddresses00link.txt"
      },
      "src-ad151187f39b": {
        "words": 125832,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2141.4,
            "panel_good": 1235,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1235／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1235／讹形 0）",
        "file": "lettersaddresses02linc.txt"
      },
      "src-d2370d713009": {
        "words": 93613,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2227.3,
            "panel_good": 955,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 955／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 955／讹形 0）",
        "file": "lifeworks02lincuoft.txt"
      },
      "src-0004a5f8b45d": {
        "words": 111908,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2239.3,
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
        "file": "lifeworks03lincuoft.txt"
      },
      "src-c45f37859100": {
        "words": 93803,
        "diagnostic_est_eft": [
          3,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2220.7,
            "panel_good": 955,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 955／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 955／讹形 0）",
        "file": "lifeworksofab1136linc.txt"
      },
      "src-a6dbf2130a2f": {
        "words": 111910,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2240.1,
            "panel_good": 1135,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1135／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1135／讹形 0）",
        "file": "lifeworksofab1137linc.txt"
      },
      "src-92e8d29fbc61": {
        "words": 3509,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1923.6,
            "panel_good": 20,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "lincolnowenletters00lincrich.txt"
      },
      "src-32716caed453": {
        "words": 69143,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2160.0,
            "panel_good": 749,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 749／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 749／讹形 0）",
        "file": "lincstoriesspeech00lincrich.txt"
      },
      "src-7a4265076f1c": {
        "words": 87610,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2218.4,
            "panel_good": 837,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 837／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 837／讹形 0）",
        "file": "writingslincoln04lincrich.txt"
      },
      "src-85a1bad742d4": {
        "words": 122100,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2287.8,
            "panel_good": 1248,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1248／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1248／讹形 0）",
        "file": "writingslincoln05lincrich.txt"
      },
      "src-6ba0625bdf71": {
        "words": 129376,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2275.1,
            "panel_good": 1247,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1247／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1247／讹形 0）",
        "file": "writingsofabraha0000linc.txt"
      },
      "src-accfb35ec5a5": {
        "words": 87759,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2215.5,
            "panel_good": 837,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 837／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 837／讹形 0）",
        "file": "writingsofabraha0004linc.txt"
      },
      "src-77eca3ffa74f": {
        "words": 122073,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2287.7,
            "panel_good": 1249,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1249／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1249／讹形 0）",
        "file": "writingsofabraha0005linc.txt"
      },
      "src-eda7d8153527": {
        "words": 90161,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2197.7,
            "panel_good": 871,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 871／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 871／讹形 0）",
        "file": "writingsofabraha02lincuoft.txt"
      },
      "src-05936dd1587b": {
        "words": 109649,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2301.9,
            "panel_good": 1033,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1033／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1033／讹形 0）",
        "file": "writingsofabraha03lincuoft.txt"
      },
      "src-7562ecd0b70d": {
        "words": 125105,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2280.9,
            "panel_good": 1275,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1275／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1275／讹形 0）",
        "file": "writingsofabraha05lincuoft.txt"
      },
      "src-ec23f282b09c": {
        "words": 107508,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2167.8,
            "panel_good": 951,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 951／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 951／讹形 0）",
        "file": "writingsofabraha07lincuoft.txt"
      },
      "src-83e3586b5411": {
        "words": 2739,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2449.8,
            "panel_good": 45,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 45／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 45／讹形 0）",
        "file": "wsb18f36_images.txt"
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
    "长逐字引文": 29,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 2,
    "★★ 射程": "只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语"
  },
  "holdout_mention": {
    "字面提及": 0,
    "**其中点名了是哪一份的**": 0,
    "★ 只是泛泛提及（不说哪一份）": 0,
    "与 holdout 正文重叠": 0,
    "★ 与出厂模板逐字相同、已豁免": 8,
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
    "可用来源": 67,
    "**按内容去重后的作品数**": 5,
    "虚高": 13.4,
    "未声明的重复对": 0,
    "已声明的重复对": 49,
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
        "引文数": 1,
        "核过": 1,
        "**对不上**": []
      },
      "06-timeline.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      }
    },
    "合计": "10 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 3,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 70,
    "train 源总数": 70,
    "本人所著字节": 44963665,
    "train 总字节": 44963665,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 43682536,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 14.85,
    "**立场句/万字**": 0.13,
    "其中不含第一人称的": 387,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 68,
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-lincoln-174/workspaces/abraham-lincoln/evidence/source-ledger.jsonl",
    "一手份数": 65,
    "台账总份数": 67,
    "一手占比": 0.9701,
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
    "最优选法": "把 src-6546cbb74276 扣作 holdout 即满足三项门",
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
    "台账行数": 70,
    "**`title` 就是文件名**": 0,
    "真书目题名": 70,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 1,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 1,
    "有一边没年份": 69,
    "**逐条**": [
      {
        "source_id": "src-34ec715ab9ad",
        "文件名": "earlyspeechesofa1858linc.txt",
        "文件名里的年份": [
          1858
        ],
        "台账 published_at": 1924,
        "差": 66
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
    "source_ids": "逐条各异（非空 25/25，不同取值 16）",
    "evidence_clusters": "逐条各异（非空 25/25，不同取值 25）",
    "counter_source_ids": "整批都空（非空 0/25，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 8,
    "作品组数（连通分量，仅供参考）": 8,
    "来源数": 70,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 27,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 25,
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-lincoln-174/workspaces/abraham-lincoln/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-bf724593cbe6",
      "           **他的分裂模型：不可持续的是「政府」这一形态，不是国民感情。** `I believe this Government cannot endure permanently h…",
      "",
      "低于 10% 的 35 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-lincoln-174/workspaces/abraham-lincoln/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-lincoln-174/workspaces/abraham-lincoln/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.785,
  "baseline_overall": 0.4694,
  "candidate_baseline_delta": 0.3156,
  "suite_candidate_means": {
    "known": 0.6,
    "boundary": 1.0,
    "voice": 0.55,
    "trajectory": 0.475,
    "contrast": 1.0,
    "fact-preservation": 0.975,
    "style-decoy": 0.91,
    "task-completion": 0.9,
    "planning-fidelity": 0.9,
    "tool-use": 0.95,
    "capability-calibration": 0.925,
    "refusal-stop": 0.75,
    "long-horizon": 0.775,
    "identity-routing": 0.425,
    "anonymous-fidelity": 0.575,
    "token-efficiency": 0.85
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
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

- `corpus.source-count-inflated-by-duplicates`: **`source.minimum` 只是被重份撑绿的**：可用来源 67 ≥ 门 8，而按内容去重后只有 **5 部作品**（虚高 13.4×）。**这道门量的是「有几个 source_id」，不是「有几处独立证据」。**
- `content.decorative-citation`: 存在装饰性引用：断言挂的来源正文里找不到其关键实体

## Warnings

- `corpus.unexamined-band`: **2/70 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `source.filename-year-mismatch`: 1 条文件名年份与 `published_at` 差 ≥2 年 —— **至少有一处记错了**；判据不知道是哪一处
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
