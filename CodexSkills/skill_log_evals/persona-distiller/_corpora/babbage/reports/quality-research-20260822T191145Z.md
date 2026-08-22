# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babbage`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-22T19:11:45Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 68,
    "claims": 13
  },
  "sources_total": 68,
  "sources_train": 57,
  "sources_usable_train": 57,
  "sources_holdout": 11,
  "primary_sources": 56,
  "primary_ratio": 0.9825,
  "lane_source_counts": {
    "writings": 54,
    "conversations": 2,
    "expression": 0,
    "external": 1,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 67,
    "已证实归属": 48,
    "存疑（有正面证据但另有他人署名）": [
      "src-14b238725cab bub_gb_C2sYl7PskYgC.txt [A-byline] 另有他人署名：by II. II",
      "src-26e5d20da8bd in.ernet.dli.2015.92595.txt [A-byline] 另有他人署名：By Sn John",
      "src-45a5f5c534d9 india.history.resource.37569.txt [A-byline] 另有他人署名：by WILLIAM CLOWES"
    ],
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "16 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 68,
    "不是语料": 0,
    "可疑": 3,
    "可疑（只报不拦）": [
      "raw-holdout/charlesbabbagel00babb.txt　过短：255 字节 < 2000——**确认这是不是一份完整的件**",
      "raw/charlesbabbagel00babba.txt　过短：101 字节 < 2000——**确认这是不是一份完整的件**",
      "raw-holdout/in.ernet.dli.2015.514199.txt　可读字符占比 46% < 55%——多半是二进制或彻底崩坏的 OCR"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Charles Babbage 著作归属依据：① 各书题名页/署名行（见 covered_sources 逐份照录），如《Reflections on the ",
    "citation": "archive.org 目录 creator 字段 + 各书题名页/署名行；出版记录见各源 locator。",
    "争议篇目数": 0,
    "P1 声称本人所著": 67,
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
    "usable_train": 57,
    "fact 类条数": 5,
    "**人物事实**（计入）": 5,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 12,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 0,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 0,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**未达**": [
      "可核 `fact` 断言 5 条 < 要求 12 条（57 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因",
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 0 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 68,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "in.ernet.dli.2015.21299.txt",
        "非拉丁字符": 2,
        "全同形字词": 1,
        "样例": [
          "а 读作 a"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "干净": 51,
      "不适用": 8,
      "未核": 8,
      "混杂": 1
    },
    "逐份": {
      "src-3fc4b116cfaf": {
        "words": 121649,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 579.0,
            "panel_good": 3150,
            "panel_bad": 3,
            "若无语种门会读到": 0.001,
            "verdict": "干净",
            "rate": 0.001,
            "reason": "德语讹字率 0.0010（正形 3150／讹形 3）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2821,
          "变音符每千词": 84.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.001,
        "reason": "德语讹字率 0.0010（正形 3150／讹形 3）",
        "file": "10708873bsb.txt"
      },
      "src-39cf3746b17b": {
        "words": 52077,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2486.9,
            "panel_good": 740,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 740／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 740／讹形 0）",
        "file": "10730620bsb.txt"
      },
      "src-bf9aac1107fd": {
        "words": 125824,
        "diagnostic_est_eft": [
          211,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0009；英文：锚 7.5<500.0，若强行读 0.0000；德语：锚 0.6<15.0，若强行读 0.0400）",
        "file": "BRes141157.txt"
      },
      "src-efeb5b207fb5": {
        "words": 144160,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2159.5,
            "panel_good": 1333,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1333／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1333／讹形 0）",
        "file": "TO00961792_TO0324_62184_000000.txt"
      },
      "src-5080898e1739": {
        "words": 1761,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2606.5,
            "panel_good": 8,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "TO01157391_TO0324_62137_000000.txt"
      },
      "src-8247081817fb": {
        "words": 977,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1832.1,
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
        "file": "TO01157442_TO0324_62167_000000.txt"
      },
      "src-fc1a701f0fd1": {
        "words": 2438,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2186.2,
            "panel_good": 33,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 33／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 33／讹形 0）",
        "file": "TO01157472_TO0324_62180_000000.txt"
      },
      "src-6c2ab02ae2db": {
        "words": 3588,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2569.7,
            "panel_good": 60,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 60／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 60／讹形 0）",
        "file": "TO0E039268_TO0324_PNI-1546_000000.txt"
      },
      "src-c1c5320ab9d8": {
        "words": 3463,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1793.2,
            "panel_good": 43,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 43／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 43／讹形 0）",
        "file": "TO0E039272_TO0324_PNI-1551_000000.txt"
      },
      "src-f5e106f67225": {
        "words": 4135,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2316.8,
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
        "file": "TO0E039283_TO0324_PNI-1555_000000.txt"
      },
      "src-a58bfd6346ca": {
        "words": 5604,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2039.6,
            "panel_good": 54,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 54／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 54／讹形 0）",
        "file": "TO0E039289_TO0324_PNI-1557_000000.txt"
      },
      "src-411a9ded1e49": {
        "words": 8659,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2246.2,
            "panel_good": 62,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 62／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 62／讹形 0）",
        "file": "TO0E039502_TO0324_PNI-1635_000000.txt"
      },
      "src-99626bed2c1b": {
        "words": 150750,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1970.7,
            "panel_good": 1899,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1899／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1899／讹形 0）",
        "file": "anelementarytre00babbgoog.txt"
      },
      "src-eec0495f8470": {
        "words": 81705,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2305.1,
            "panel_good": 992,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 992／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 992／讹形 0）",
        "file": "b21495336.txt"
      },
      "src-2c12b07d067d": {
        "words": 10377,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2076.7,
            "panel_good": 91,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 91／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 91／讹形 0）",
        "file": "b22278114.txt"
      },
      "src-8e4335c0fb45": {
        "words": 16632,
        "diagnostic_est_eft": [
          15,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2307.0,
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
        "file": "b22290540.txt"
      },
      "src-4089f7c8c934": {
        "words": 1843,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2566.5,
            "panel_good": 8,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "b22376914.txt"
      },
      "src-b529b4917090": {
        "words": 51987,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2495.8,
            "panel_good": 745,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 745／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 745／讹形 0）",
        "file": "b28744597.txt"
      },
      "src-0ea37434eee7": {
        "words": 160864,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2079.0,
            "panel_good": 1341,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1341／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1341／讹形 0）",
        "file": "bub_gb_2T0AAAAAQAAJ.txt"
      },
      "src-06c1c60adeec": {
        "words": 147796,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2129.4,
            "panel_good": 1341,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1341／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1341／讹形 0）",
        "file": "bub_gb_8rtdVgQNCuwC.txt"
      },
      "src-1471aea47376": {
        "words": 37975,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2362.6,
            "panel_good": 503,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 503／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 503／讹形 0）",
        "file": "bub_gb_95dn9JDkB7YC.txt"
      },
      "src-14b238725cab": {
        "words": 40496,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2384.2,
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
        "file": "bub_gb_C2sYl7PskYgC.txt"
      },
      "src-98990a90f423": {
        "words": 131190,
        "diagnostic_est_eft": [
          1174,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0016；英文：锚 1.6<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1250）",
        "file": "bub_gb_CPdRAAAAcAAJ.txt"
      },
      "src-c7a7f0e377ea": {
        "words": 127716,
        "diagnostic_est_eft": [
          1115,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0066；英文：锚 2.0<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.3846）",
        "file": "bub_gb_DP0JAAAAIAAJ.txt"
      },
      "src-30cde21f13a6": {
        "words": 161318,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2063.1,
            "panel_good": 1340,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1340／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1340／讹形 0）",
        "file": "bub_gb_Fa1JAAAAMAAJ.txt"
      },
      "src-09d48035b032": {
        "words": 48,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "charlesbabbagel00babb.txt"
      },
      "src-68beb793935f": {
        "words": 17,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "charlesbabbagel00babba.txt"
      },
      "src-0a4c3f4044f4": {
        "words": 81863,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2272.7,
            "panel_good": 980,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 980／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 980／讹形 0）",
        "file": "dli.bengal.10689.13631.txt"
      },
      "src-0b6363f5c6b9": {
        "words": 5365,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1332.7,
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
        "file": "examplesofsoluti00babbrich.txt"
      },
      "src-7afebeeb6d8a": {
        "words": 44261,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2413.9,
            "panel_good": 583,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 583／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 583／讹形 0）",
        "file": "in.ernet.dli.2015.180977.txt"
      },
      "src-750d08b0eca8": {
        "words": 103854,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2065.7,
            "panel_good": 925,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 925／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 925／讹形 0）",
        "file": "in.ernet.dli.2015.21299.txt"
      },
      "src-7e5bf3bd8ee4": {
        "words": 44146,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2408.4,
            "panel_good": 578,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 578／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 578／讹形 0）",
        "file": "in.ernet.dli.2015.49255.txt"
      },
      "src-52cd50baa06b": {
        "verdict": "未核",
        "reason": "空文本",
        "words": 0,
        "file": "in.ernet.dli.2015.514199.txt"
      },
      "src-26e5d20da8bd": {
        "words": 81268,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2239.6,
            "panel_good": 961,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 961／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 961／讹形 0）",
        "file": "in.ernet.dli.2015.92595.txt"
      },
      "src-977b8203c771": {
        "words": 49886,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2526.2,
            "panel_good": 726,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 726／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 726／讹形 0）",
        "file": "india.history.resource.117183.txt"
      },
      "src-45a5f5c534d9": {
        "words": 34865,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 563.6,
            "panel_good": 58,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 58／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 58／讹形 0）",
        "file": "india.history.resource.37569.txt"
      },
      "src-1790fd4226bd": {
        "words": 37313,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2372.6,
            "panel_good": 490,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 490／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 490／讹形 0）",
        "file": "india.history.resource.37756.txt"
      },
      "src-a07f9f922a12": {
        "words": 114488,
        "diagnostic_est_eft": [
          5,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2332.0,
            "panel_good": 1118,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1118／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1118／讹形 0）",
        "file": "india.history.resource.52834.txt"
      },
      "src-92ba2380620c": {
        "words": 146281,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2169.6,
            "panel_good": 1356,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1356／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1356／讹形 0）",
        "file": "india.history.resource.73335.txt"
      },
      "src-72b5d663c4e2": {
        "words": 8078,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1665.0,
            "panel_good": 108,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 108／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 108／讹形 0）",
        "file": "jstor-107505.txt"
      },
      "src-21a1c352d9ab": {
        "words": 5403,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1928.6,
            "panel_good": 68,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 68／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 68／讹形 0）",
        "file": "jstor-107581.txt"
      },
      "src-fdb1dfe5b54a": {
        "words": 6061,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1937.0,
            "panel_good": 46,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 46／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 46／讹形 0）",
        "file": "jstor-107813.txt"
      },
      "src-89169b2b498c": {
        "words": 8876,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2404.2,
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
        "file": "jstor-107825.txt"
      },
      "src-0fb80bb4e7e4": {
        "words": 626,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2140.6,
            "panel_good": 4,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 4 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 4 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-109879.txt"
      },
      "src-0729c189c6ce": {
        "words": 682,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2390.0,
            "panel_good": 8,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-109936.txt"
      },
      "src-cf5b7dd4d166": {
        "words": 1178,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2351.4,
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
        "file": "jstor-110122.txt"
      },
      "src-2f534c66d013": {
        "words": 1182,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2419.6,
            "panel_good": 10,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 10 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 10 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-110134.txt"
      },
      "src-c36a5b28ade4": {
        "words": 4699,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2357.9,
            "panel_good": 76,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 76／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 76／讹形 0）",
        "file": "jstor-111607.txt"
      },
      "src-001f69019ce0": {
        "words": 5252,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2073.5,
            "panel_good": 62,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 62／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 62／讹形 0）",
        "file": "jstor-2338172.txt"
      },
      "src-5d78dfa08c37": {
        "words": 30898,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2428.0,
            "panel_good": 451,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 451／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 451／讹形 0）",
        "file": "ninthbridgewatai00babb.txt"
      },
      "src-fe2fdc9eaaff": {
        "words": 37531,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2408.1,
            "panel_good": 506,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 506／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 506／讹形 0）",
        "file": "ninthbridgewate00babb.txt"
      },
      "src-08553a7d62fb": {
        "words": 44249,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2411.8,
            "panel_good": 584,
            "panel_bad": 1,
            "若无语种门会读到": 0.0017,
            "verdict": "干净",
            "rate": 0.0017,
            "reason": "英文讹字率 0.0017（正形 584／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0017,
        "reason": "英文讹字率 0.0017（正形 584／讹形 1）",
        "file": "ninthbridgewater00babb.txt"
      },
      "src-6737eddb7c69": {
        "words": 37389,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2415.7,
            "panel_good": 505,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 505／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 505／讹形 0）",
        "file": "ninthbridgewater00babb_0.txt"
      },
      "src-d35dbecaa39b": {
        "words": 45251,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2422.9,
            "panel_good": 589,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 589／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 589／讹形 0）",
        "file": "ninthbridgewater00babbiala.txt"
      },
      "src-cfa05695f8f3": {
        "words": 18508,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2497.8,
            "panel_good": 161,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 161／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 161／讹形 0）",
        "file": "observationsonte00babb.txt"
      },
      "src-a592178f069b": {
        "words": 18639,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2508.2,
            "panel_good": 164,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 164／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 164／讹形 0）",
        "file": "observationsonte00babbiala.txt"
      },
      "src-4a91e703724a": {
        "words": 109924,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2361.3,
            "panel_good": 1100,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1100／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1100／讹形 0）",
        "file": "oneconomyofmac00babb.txt"
      },
      "src-a0ae1e653814": {
        "words": 87286,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2359.4,
            "panel_good": 878,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 878／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 878／讹形 0）",
        "file": "oneconomyofmach00babb.txt"
      },
      "src-6c9de8f52a6a": {
        "words": 107048,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2357.5,
            "panel_good": 1073,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1073／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1073／讹形 0）",
        "file": "oneconomyofmachi00babb.txt"
      },
      "src-2f9aab9c1faa": {
        "words": 114658,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2337.0,
            "panel_good": 1125,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1125／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1125／讹形 0）",
        "file": "oneconomyofmachi00babbrich.txt"
      },
      "src-2a33e0932cf3": {
        "words": 109855,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2364.7,
            "panel_good": 1101,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1101／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1101／讹形 0）",
        "file": "oneconomyofmanuf00babbiala.txt"
      },
      "src-807fd620de16": {
        "words": 105627,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2384.8,
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
        "file": "ontheeconomyofma04238gut.txt"
      },
      "src-29112773ef75": {
        "words": 2587,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.5000；英文：锚 444.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "papers00babb.txt"
      },
      "src-604f5e2effd5": {
        "words": 159313,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2122.7,
            "panel_good": 1361,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1361／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1361／讹形 0）",
        "file": "passagesfromlife00babb.txt"
      },
      "src-6602fa6218b7": {
        "words": 6358,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2266.4,
            "panel_good": 78,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 78／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 78／讹形 0）",
        "file": "thoughtsonprinci00babbrich.txt"
      },
      "src-df78df5e39f0": {
        "words": 130907,
        "diagnostic_est_eft": [
          1166,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0016；英文：锚 2.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.3333）",
        "file": "traitsurlcon00babb.txt"
      },
      "src-2545caca8ffb": {
        "words": 125771,
        "diagnostic_est_eft": [
          1090,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0098；英文：锚 8.7<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.3125）",
        "file": "traitsurlconomi00babbgoog.txt"
      },
      "src-8bb16bea438c": {
        "words": 121653,
        "diagnostic_est_eft": [
          2,
          7
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 382.6,
            "panel_good": 2021,
            "panel_bad": 31,
            "若无语种门会读到": 0.0151,
            "verdict": "混杂",
            "rate": 0.0151,
            "reason": "德语讹字率 0.0151（正形 2021／讹形 31）"
          }
        },
        "德语附加": {
          "h→b率": 0.0313,
          "h→b样本": 1659,
          "变音符每千词": 59.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.0151,
        "reason": "德语讹字率 0.0151（正形 2021／讹形 31）",
        "file": "uebermaschinenu00babbgoog.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 68,
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
    "byline_in_carrier": "核过 9 条，指错 0 条",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 0 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 90 条，切分后核验片段 80 个，未命中 16 个，长 s 还原后才命中 0 个，跳过标识符 9 个（判据名/字段名/来源号，不是引文）｜⚠ 研究/01-writings.md: 「truth is of much more importance than their origin」｜⚠ 研究/01-writings.md: 「shadow of an shadow of doubt」｜⚠ 研究/01-writings.md: 「thus by implication denying to him the possession of that foresight which is the highest attribute o」｜⚠ 研究/01-writings.md: 「render their name a kind of comet, carrying with it a tail of upwards of forty letters, at the avera」｜⚠ 研究/01-writings.md: 「I laid it down as a principle — that, except in rare cases, I would never do anything myself if I co」｜⚠ 研究/01-writings.md: 「The subject of this branch of Analysis is the passage of one or more quantities through different st」",
    "first_person_density": {
      "实质第一人称句": 9118,
      "密度/万字": null,
      "正文字符": 20963282,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 70,
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
    "★ 与出厂模板逐字相同、已豁免": 4,
    "★★ 射程": "抓不到「不提 holdout 也不抄它、却把题目描述出来」的写法——那一类只能靠人读或答题方主动上报"
  },
  "source_numbering_gap": {
    "编号缺口": 0,
    "其中确认型": 0,
    "其中疑似（组内首字母不是 a）": 0,
    "★ 缺口上正好是 holdout 的": 0,
    "★★ 射程": "只看文件名；**尾部被整份拿走的缺口抓不到**；补齐编号也堵不住「份数本身是信息」那一层",
    "★ 没有 references/sources/": "**未核（不是通过）**"
  },
  "source_dedup": {
    "可用来源": 57,
    "**按内容去重后的作品数**": 24,
    "虚高": 2.375,
    "未声明的重复对": 0,
    "已声明的重复对": 109,
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
        "引文数": 50,
        "核过": 33,
        "**对不上**": [
          "The present volume may be considered as one of the consequences that have resulted from the Calculating-Engine, the construction of which I ",
          "I was insensibly led to apply to them those principles of generalization to which my other pursuits had naturally given rise. <!-- src-4a91e",
          "Reasoning is to be combated and refuted by reasoning alone. Any endeavour to raise a prejudice, or throw the shadow of an shadow of doubt on",
          "On one point I shall speak decidedly, it is not connected in any degree with the calculating machine on which I have been engaged; the cause",
          "I have no desire to write my own biography, as long as I have strength and means to do better work. <!-- src-0ea37434eee7 -->",
          "X BB work of Lacroix, of which a Translation is no^r presented to the iPuhlic, forms one of a series of Elementary Treatises, by that distin",
          "The first part of this Treatise, which is devoted to the exposition of the principles of the Differential Calculus, was translated by Mr. Ba",
          "England has invited the judgment of the world upon its Arts and its Industry; — science appeals to the same tribunal against its ingratitude",
          "shadow of an shadow of doubt",
          "thus by implication denying to him the possession of that foresight which is the highest attribute of omnipotence",
          "render their name a kind of comet, carrying with it a tail of upwards of forty letters, at the average cost of 10l. 9s. 9½d. per letter",
          "like all deeply-rooted complaints, the operation which alone can contribute to its cure, is necessarily painful",
          "I laid it down as a principle — that, except in rare cases, I would never do anything myself if I could afford to hire another person who co",
          "The subject of this branch of Analysis is the passage of one or more quantities through different states of magnitude",
          "I know of no injury within the power of those who have never given me a single occasion for gratitude.",
          "If he agree with them in a principle, but differ in its application, he is called \"crotchety.\" If he cannot be induced by sophistry to vote ",
          "to dwell upon small affairs which are isolated, is not the province of a statesman; but to integrate the effect of their constant recurrence"
        ]
      },
      "02-conversations.md": {
        "引文数": 17,
        "核过": 0,
        "**对不上**": [
          "THE great interest you have expressed in the success of that system of contrivances which has lately occupied a considerable portion of my a",
          "I remain, my dear Sir, With the greatest respect, Faithfully yours, Devonshire Street, Portland Place, July 3rd, 1822. <!-- src-6c2ab02ae2db",
          "Conscious, from my own experience, of the difficulty of convincing those who are but little skilled in mathematical knowledge, of the possib",
          "It is gratifying to record this disinterested offer, so far above those little jealousies which frequently interfere between nations long ri",
          "The intolerable labour and fatiguing monotony of a continued repetition of similar arithmetical calculations, first excited the desire, and ",
          "One remarkable property of this machine is, that the greater the number of differences the more the engine will outstrip the most rapid calc",
          "In another trial it produced figures at the rate of forty-four in a minute. As the machine may be made to move uniformly by a weight, this r",
          "The quantity of errors from carelessness in correcting the press, even in tables of the greatest credit, will scarcely be believed, except b",
          "I have been informed that the publishers of a valuable collection of mathematical tables, now re-printing, pay to the gentleman employed in ",
          "The wheels ol which it consists are numerous, but few move at the same time; and I ha\\ e employed a principle by which any small error that ",
          "To remedy this evil, I have contrived means by which the machines themselves shall take from several boxes containing type, the numbers whic",
          "The third section, on whom the most laborious part of the operations devolved, consisted of from sixty to eighty persons, few of them posses",
          "Thus the number of calculators employed, instead of amounting to ninety-six, would be reduced to twelve. <!-- src-6c2ab02ae2db -->",
          "Such engines would however be far from useless: containing within themselves the power of generating to an almost unlimited extent tables wh",
          "I am aware that the statements contained in this Letter may perhaps be viewed as something more than Utopian, and that the philosophers of L",
          "Whether 1 shall construct a larger engine of this kind, and bring to perfection the others I have described, will in a great measure depend ",
          "Induced, by a conviction of the great utility of such engines, to withdraw for some time my attention from a subject on which it has been en"
        ]
      },
      "03-expression.md": {
        "引文数": 7,
        "核过": 0,
        "**对不上**": [
          "What is there in a name? It is merely an empty basket, until you put something into it. <!-- src-efeb5b207fb5 -->",
          "Truth only has been the object of my search, and I am not conscious of ever having turned aside in my inquiries from any fear of the conclus",
          "I took an odd mode of making the experiment; I resolved that at a certain hour of a certain day I would go to a certain room in the house, a",
          "But the machine upon which everybody could calculate, had little chance of fair play from the man on whom nobody could calculate. <!-- src-e",
          "It can not only calculate the millions the ex-Chancellor of the Exchequer squandered, but it can deal with the smallest quantities; nay, it ",
          "It is this substitution of the infinity of time for the infinity of space which I have made use of, to limit the size of the engine and yet ",
          "The great basis of virtue in man is truth— that is, the con¬stant application of the same word to the same thing. The first element of accur"
        ]
      },
      "04-external.md": {
        "引文数": 14,
        "核过": 0,
        "**对不上**": [
          "The following statement was drawn up by the late Sir Harris Nicolas, G.S.M. & G., from papers and documents in my possession relating to the",
          "“They had not the slightest hesitation in pronouncing their decided opinion in the affirmative.” <!-- src-efeb5b207fb5 -->",
          "The view of the Government was, to assist an able and ingenious man of science, whose zeal had induced him to exceed the limits of prudence,",
          "The public at first flocked to it : but it was so placed that only three persons could conveniently see it at the same time. <!-- src-efeb5b",
          "Upon one of these occasions I was insulted by impertinent questions conveyed in a loud voice from a person at a distance in the crowd. <!-- ",
          "At last they asked me whether the Commissioners were betes. I assured them that the only one with whom I was personally acquainted certainly",
          "To the King, your father, I am indebted for the first public and official acknowledgment of this invention. <!-- src-efeb5b207fb5 -->",
          "Prince instantly added, “I have seen it before.” I felt at once that the Prince was a “good man and true,” <!-- src-efeb5b207fb5 -->",
          "the Duke turned to Lady Wilton and said, “I know that diffi¬culty well.” <!-- src-efeb5b207fb5 -->",
          "He said to me, “What an extraordinary person you are! You have perfectly fascinated our King, who has done nothing but talk of you and the t",
          "I have so frequently been mortified by having the utterly- undeserved reputation of knowing everything <!-- src-efeb5b207fb5 -->",
          "I have obtained, in my own country, an unenviable cele¬brity, not by anything I have done, but simply by a deter¬mined 'resistance to the ty",
          "I have no desire to write my own biography, as long as 1 have strength and means to do better work. <!-- src-efeb5b207fb5 -->",
          "Some caterers lor the public offered to pay me for it. Others required that I should pay them for its insertion ; others oflered to insert i"
        ]
      },
      "05-decisions.md": {
        "引文数": 9,
        "核过": 0,
        "**对不上**": [
          "I am thinking that all these Tables (pointing to the logarithms) might be calculated by machinery. <!-- src-efeb5b207fb5 -->",
          "Would it be too much, in the first instance, to take 1,500?. ? <!-- src-efeb5b207fb5 -->",
          "To withhold those new views from the Government, and under such circumstances to have allowed the construction of the Engine to be resumed, ",
          "In 1839 the demands of the Analytical Engine upon my attention had become so incessant and so exhausting, that even tlie few duties of the L",
          "On the 6th of November, 1842, Mr. Babbage wrote to Sir Robert Peel and the Chancellor of the Exchequer, acknow¬ledging the receipt of their ",
          "My advice is — pursue it, even if it should oblige you to live on bread and cheese. <!-- src-efeb5b207fb5 -->",
          "This advice entirely accorded with my own feelings. I therefore retained my chief assistant at his advanced salary. <!-- src-efeb5b207fb5 --",
          "I at length laid it down as a principle — that, except in rare cases, I would never do anything myself if I could afford to hire another per",
          "I claim no merit for this resistance; although I am quite aware that I am fighting the battle of every one of my countrymen who gains his su"
        ]
      },
      "06-timeline.md": {
        "引文数": 19,
        "核过": 0,
        "**对不上**": [
          "When about five yeare old, I was walking with my nurse, who had in her arms an infant brother of mine, across London’ Bridge <!-- src-efeb5b",
          "Having suffered in health at the age of five years, and again at that of ten by violent fevers, from which I was with difficulty saved, I wa",
          "After I had been at this school for about a twelvemouth, I proposed to one of my school-fellows, who was of a studious habit, that we should",
          "In 1811, during the war, it was very difficult to procure foreign books. <!-- src-efeb5b207fb5 -->",
          "Elected Lucasian Professor of Mathematics in 1&8 <!-- src-efeb5b207fb5 -->",
          "In 1839 the demands of the Analytical Engine upon my attention had become so incessant and so exhausting, that even tlie few duties of the L",
          "The first Difference Engine with which I am acquainted comprised a few figures, and was made by myself, between 1820 and June 1822. <!-- src",
          "A much larger and more perfect engine was sub¬sequently commenced in 1823 for the Government. <!-- src-efeb5b207fb5 -->",
          "It was commenced 1823. This portion put together 1833. The construction abandoned 1842. <!-- src-efeb5b207fb5 -->",
          "It is now nearly fourteen years since I undertook for the Government to superintend the making of the Difference Engine. <!-- src-efeb5b207f",
          "The better part of my life has now been spent on that machine, and no progress whatever having been made since 1834 <!-- src-efeb5b207fb5 --",
          "This idea occurred to me in October, 1834. <!-- src-efeb5b207fb5 -->",
          "In 1840 I received from my friend M. Plana a letter pressing me strongly to visit Turin <!-- src-efeb5b207fb5 -->",
          "the late Countess of Lovelace * informed me that she had trans¬lated the memoir of Menabrea. <!-- src-efeb5b207fb5 -->",
          "ttT “ 1848> When 1 “ mastered the subject of the Analytical Engine, that I resolved on making a complete set of drawings of the Difference E",
          "These comprise a complete series of drawings and explanatory notations, finished in 1849, of the Difference Engine No. 2 <!-- src-efeb5b207f",
          "My Lord, June 8, 1852. <!-- src-efeb5b207fb5 -->",
          "This portion was in the Exhibition 1862. <!-- src-efeb5b207fb5 -->",
          "Passages from the Life of a Philosopher. 8vo. 1864. <!-- src-efeb5b207fb5 -->"
        ]
      }
    },
    "合计": "116 条引文，对不上 83 条",
    "读不到正文的来源": [
      "src-bf9aac1107fd",
      "src-8247081817fb",
      "src-c1c5320ab9d8",
      "src-a58bfd6346ca",
      "src-411a9ded1e49",
      "src-8e4335c0fb45",
      "src-09d48035b032",
      "src-0b6363f5c6b9",
      "src-52cd50baa06b",
      "src-45a5f5c534d9",
      "src-29112773ef75"
    ],
    "holdout 源数": 0,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 68,
    "train 源总数": 68,
    "本人所著字节": 27170405,
    "train 总字节": 27170405,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 17766652,
    "**判据说未核验的**": 7,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-3fc4b116cfaf",
        "原因": "语种判为 **de**（en=0.001 de=0.135 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-98990a90f423",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.099）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-c7a7f0e377ea",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.098）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-68beb793935f",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-df78df5e39f0",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.100）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-2545caca8ffb",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.097）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8bb16bea438c",
        "原因": "语种判为 **de**（en=0.002 de=0.101 fr=0.007）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 15.74,
    "**立场句/万字**": 0.09,
    "其中不含第一人称的": 118,
    "读不到正文的": [
      "src-bf9aac1107fd",
      "src-8247081817fb",
      "src-c1c5320ab9d8",
      "src-a58bfd6346ca",
      "src-411a9ded1e49",
      "src-8e4335c0fb45",
      "src-09d48035b032",
      "src-0b6363f5c6b9",
      "src-52cd50baa06b",
      "src-45a5f5c534d9",
      "src-29112773ef75"
    ],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 67,
    "**疑似著录卡**": {},
    "读不到正文的": [
      "src-bf9aac1107fd",
      "src-8247081817fb",
      "src-c1c5320ab9d8",
      "src-a58bfd6346ca",
      "src-411a9ded1e49",
      "src-8e4335c0fb45",
      "src-09d48035b032",
      "src-0b6363f5c6b9",
      "src-52cd50baa06b",
      "src-45a5f5c534d9",
      "src-29112773ef75"
    ],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "逐字英文引文": 18,
    "**未命中**": 6,
    "跨版口命中（引文为真）": 0,
    "未命中样例": [
      "04-external.md: Mr. Babbage thinks / his conviction was / he apprehended",
      "04-external.md: indefinitely expensive / the ultimate success so problematical / the expenditure...utterly incapable of being ",
      "04-external.md: put work on the universe",
      "04-external.md: second-rate man in prominent position",
      "05-decisions.md: whom he distinctly remembers",
      "06-timeline.md: It was in 1848, when I had mastered…"
    ],
    "跨版口样例": []
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babbage/evidence/source-ledger.jsonl",
    "一手份数": 56,
    "台账总份数": 57,
    "一手占比": 0.9825,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 68,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-3fc4b116cfaf 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 68,
    "声称公有领域": 0,
    "不声称（不判）": 68,
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
    "台账行数": 68,
    "**`title` 就是文件名**": 0,
    "真书目题名": 68,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 5,
    "差一年": 0,
    "跨PD分界": 5,
    "两边都有年份": 10,
    "有一边没年份": 58,
    "**逐条**": [
      {
        "source_id": "src-7afebeeb6d8a",
        "文件名": "in.ernet.dli.2015.180977.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1838,
        "差": 177,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-750d08b0eca8",
        "文件名": "in.ernet.dli.2015.21299.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1864,
        "差": 151,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-7e5bf3bd8ee4",
        "文件名": "in.ernet.dli.2015.49255.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1838,
        "差": 177,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-52cd50baa06b",
        "文件名": "in.ernet.dli.2015.514199.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1830,
        "差": 185,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-26e5d20da8bd",
        "文件名": "in.ernet.dli.2015.92595.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1851,
        "差": 164,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-6c2ab02ae2db",
        "文件名": "TO0E039268_TO0324_PNI-1546_000000.txt",
        "文件名里的年份": [
          1546
        ],
        "台账 published_at": 1822,
        "差": 276
      },
      {
        "source_id": "src-c1c5320ab9d8",
        "文件名": "TO0E039272_TO0324_PNI-1551_000000.txt",
        "文件名里的年份": [
          1551
        ],
        "台账 published_at": 1820,
        "差": 269
      },
      {
        "source_id": "src-f5e106f67225",
        "文件名": "TO0E039283_TO0324_PNI-1555_000000.txt",
        "文件名里的年份": [
          1555
        ],
        "台账 published_at": 1822,
        "差": 267
      },
      {
        "source_id": "src-a58bfd6346ca",
        "文件名": "TO0E039289_TO0324_PNI-1557_000000.txt",
        "文件名里的年份": [
          1557
        ],
        "台账 published_at": 1820,
        "差": 263
      },
      {
        "source_id": "src-411a9ded1e49",
        "文件名": "TO0E039502_TO0324_PNI-1635_000000.txt",
        "文件名里的年份": [
          1635
        ],
        "台账 published_at": 1825,
        "差": 190
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

- `identity.facet-missing`: missing identity facet: technical-engineer
- `identity.facet-missing`: missing identity facet: software-developer
- `identity.facet-missing`: missing identity facet: art-designer
- `identity.facet-missing`: missing identity facet: entrepreneur-operator
- `identity.facet-missing`: missing identity facet: investor-capital-allocator
- `identity.facet-missing`: missing identity facet: thinker-educator

## Warnings

- research.lane_quotes：83 条逐字引文回原文对不上——**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区
- content.verbatim-quote：6 条逐字引文在语料里找不到原样——**引文对不上就是引文对不上**
- `source.year-straddles-pd-cutoff`: **5 条的文件名年份与 `published_at` 跨过 PD 分界 1931** —— 这一类直接改变「这份源能不能用」，**必须逐份读题名页定案**，不要凭其中一个数下结论
- `source.filename-year-mismatch`: 5 条文件名年份与 `published_at` 差 ≥2 年 —— **至少有一处记错了**；判据不知道是哪一处
