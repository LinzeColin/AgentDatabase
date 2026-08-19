# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kant-179/workspaces/immanuel-kant`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T06:24:47Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 65,
    "claims": 23
  },
  "sources_total": 65,
  "sources_train": 55,
  "sources_usable_train": 55,
  "sources_holdout": 10,
  "primary_sources": 53,
  "primary_ratio": 0.9636,
  "lane_source_counts": {
    "writings": 51,
    "conversations": 2,
    "expression": 0,
    "external": 2,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 60,
    "已证实归属": 42,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "18 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 65,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/immanuelkantpap00kant.txt　过短：687 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干书简卷的扫描件自印定位（`src-88e3670ea28b`）：`Digitized by the Internet Archive in 2010 wit",
    "citation": "archive.org item `briefwechselvoni01kant`（其余 source_id 的 locator 与 sha256 记于 sou",
    "争议篇目数": 0,
    "P1 声称本人所著": 60,
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
    "usable_train": 55,
    "fact 类条数": 12,
    "**人物事实**（计入）": 12,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 11,
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
    "已查语料件": 65,
    "含同形字的源": 4,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "10043581bsb.txt",
        "非拉丁字符": 4,
        "全同形字词": 0,
        "样例": [
          "gα 读作 gα"
        ]
      },
      {
        "源": "10046172bsb.txt",
        "非拉丁字符": 6,
        "全同形字词": 0,
        "样例": [
          "νππẽẽů 读作 vππẽẽů",
          "νννẽƷm 读作 vvvẽƷm"
        ]
      },
      {
        "源": "bim_eighteenth-century_essays-and-treatises-on-_kant-immanuel_1798_2.txt",
        "非拉丁字符": 2,
        "全同形字词": 0,
        "样例": [
          "bonο 读作 bono",
          "οçc 读作 oçc"
        ]
      },
      {
        "源": "bim_eighteenth-century_the-metaphysic-of-morals_kant-immanuel_1799_1.txt",
        "非拉丁字符": 1,
        "全同形字词": 0,
        "样例": [
          "usαter 读作 usαter"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 22,
      "干净": 31,
      "混杂": 2,
      "不适用": 10
    },
    "逐份": {
      "src-231cd76552be": {
        "words": 74989,
        "diagnostic_est_eft": [
          1,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 507.1,
            "panel_good": 51,
            "panel_bad": 631,
            "若无语种门会读到": 0.9252,
            "verdict": "不可用",
            "rate": 0.9252,
            "reason": "德语讹字率 0.9252（正形 51／讹形 631）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1515,
          "变音符每千词": 50.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9252,
        "reason": "德语讹字率 0.9252（正形 51／讹形 631）",
        "file": "00074230bsb.txt"
      },
      "src-23dc040bd16b": {
        "words": 24571,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 572.2,
            "panel_good": 11,
            "panel_bad": 130,
            "若无语种门会读到": 0.922,
            "verdict": "不可用",
            "rate": 0.922,
            "reason": "德语讹字率 0.9220（正形 11／讹形 130）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 609,
          "变音符每千词": 44.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.922,
        "reason": "德语讹字率 0.9220（正形 11／讹形 130）",
        "file": "10040686bsb.txt"
      },
      "src-66a095d80263": {
        "words": 28802,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 595.8,
            "panel_good": 10,
            "panel_bad": 220,
            "若无语种门会读到": 0.9565,
            "verdict": "不可用",
            "rate": 0.9565,
            "reason": "德语讹字率 0.9565（正形 10／讹形 220）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 757,
          "变音符每千词": 60.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9565,
        "reason": "德语讹字率 0.9565（正形 10／讹形 220）",
        "file": "10040687bsb.txt"
      },
      "src-d7cda8167b58": {
        "words": 82614,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 585.0,
            "panel_good": 57,
            "panel_bad": 507,
            "若无语种门会读到": 0.8989,
            "verdict": "不可用",
            "rate": 0.8989,
            "reason": "德语讹字率 0.8989（正形 57／讹形 507）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2138,
          "变音符每千词": 40.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8989,
        "reason": "德语讹字率 0.8989（正形 57／讹形 507）",
        "file": "10042413bsb.txt"
      },
      "src-1487a594f356": {
        "words": 141280,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 562.5,
            "panel_good": 84,
            "panel_bad": 939,
            "若无语种门会读到": 0.9179,
            "verdict": "不可用",
            "rate": 0.9179,
            "reason": "德语讹字率 0.9179（正形 84／讹形 939）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3556,
          "变音符每千词": 41.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9179,
        "reason": "德语讹字率 0.9179（正形 84／讹形 939）",
        "file": "10043581bsb.txt"
      },
      "src-dbda401744b9": {
        "words": 57339,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 563.0,
            "panel_good": 58,
            "panel_bad": 364,
            "若无语种门会读到": 0.8626,
            "verdict": "不可用",
            "rate": 0.8626,
            "reason": "德语讹字率 0.8626（正形 58／讹形 364）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1352,
          "变音符每千词": 43.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8626,
        "reason": "德语讹字率 0.8626（正形 58／讹形 364）",
        "file": "10044864bsb.txt"
      },
      "src-e148cf5a20c5": {
        "words": 131887,
        "diagnostic_est_eft": [
          1,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 548.1,
            "panel_good": 86,
            "panel_bad": 1033,
            "若无语种门会读到": 0.9231,
            "verdict": "不可用",
            "rate": 0.9231,
            "reason": "德语讹字率 0.9231（正形 86／讹形 1033）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3204,
          "变音符每千词": 57.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9231,
        "reason": "德语讹字率 0.9231（正形 86／讹形 1033）",
        "file": "10045002bsb.txt"
      },
      "src-f56042424327": {
        "words": 105219,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 557.1,
            "panel_good": 59,
            "panel_bad": 627,
            "若无语种门会读到": 0.914,
            "verdict": "不可用",
            "rate": 0.914,
            "reason": "德语讹字率 0.9140（正形 59／讹形 627）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2499,
          "变音符每千词": 67.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.914,
        "reason": "德语讹字率 0.9140（正形 59／讹形 627）",
        "file": "10046171bsb.txt"
      },
      "src-b248bad33390": {
        "words": 114447,
        "diagnostic_est_eft": [
          5,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 569.6,
            "panel_good": 85,
            "panel_bad": 754,
            "若无语种门会读到": 0.8987,
            "verdict": "不可用",
            "rate": 0.8987,
            "reason": "德语讹字率 0.8987（正形 85／讹形 754）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2223,
          "变音符每千词": 69.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8987,
        "reason": "德语讹字率 0.8987（正形 85／讹形 754）",
        "file": "10046172bsb.txt"
      },
      "src-ff581bf0e357": {
        "words": 163345,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 602.3,
            "panel_good": 291,
            "panel_bad": 920,
            "若无语种门会读到": 0.7597,
            "verdict": "不可用",
            "rate": 0.7597,
            "reason": "德语讹字率 0.7597（正形 291／讹形 920）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2962,
          "变音符每千词": 42.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7597,
        "reason": "德语讹字率 0.7597（正形 291／讹形 920）",
        "file": "10046183bsb.txt"
      },
      "src-deba15392d05": {
        "words": 147503,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 661.0,
            "panel_good": 3928,
            "panel_bad": 1,
            "若无语种门会读到": 0.0003,
            "verdict": "干净",
            "rate": 0.0003,
            "reason": "德语讹字率 0.0003（正形 3928／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 5059,
          "变音符每千词": 89.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0003,
        "reason": "德语讹字率 0.0003（正形 3928／讹形 1）",
        "file": "10046188bsb.txt"
      },
      "src-1f75cd8ee674": {
        "words": 98104,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 633.2,
            "panel_good": 2838,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "德语讹字率 0.0004（正形 2838／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3420,
          "变音符每千词": 76.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "德语讹字率 0.0004（正形 2838／讹形 1）",
        "file": "10046192bsb.txt"
      },
      "src-d1201414c46b": {
        "words": 126381,
        "diagnostic_est_eft": [
          14,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 701.9,
            "panel_good": 3528,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 3528／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 5084,
          "变音符每千词": 73.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 3528／讹形 0）",
        "file": "10046194bsb.txt"
      },
      "src-77a77c26b3f0": {
        "words": 165326,
        "diagnostic_est_eft": [
          221,
          0
        ],
        "逐语域": {
          "拉丁": {
            "语域": "拉丁",
            "anchors_per_10k": 27.2,
            "panel_good": 185,
            "panel_bad": 2,
            "若无语种门会读到": 0.0107,
            "verdict": "混杂",
            "rate": 0.0107,
            "reason": "拉丁讹字率 0.0107（正形 185／讹形 2）"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 610.1,
            "panel_good": 4601,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 4601／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4599,
          "变音符每千词": 79.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "ae_连字": {
          "ae_per_1000": 0.67,
          "quae": 80,
          "que": 5,
          "quae_ratio": 0.941,
          "判读": "完好",
          "理由": "ae 0.67/千字母（门 3.5）、quae 占比 0.941（门 0.80）"
        },
        "verdict": "混杂",
        "rate": 0.0107,
        "reason": "拉丁讹字率 0.0107（正形 185／讹形 2）　（两语域都适用，取更差的一侧）",
        "file": "265433882.1678.emory.edu.txt"
      },
      "src-602d11e03dce": {
        "words": 185195,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 651.8,
            "panel_good": 5255,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 5255／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 6551,
          "变音符每千词": 78.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 5255／讹形 0）",
        "file": "265433882.1682.emory.edu.txt"
      },
      "src-4ec8e58d3909": {
        "words": 191531,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 657.1,
            "panel_good": 4769,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 4769／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 6873,
          "变音符每千词": 83.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 4769／讹形 0）",
        "file": "265433882.1713.emory.edu.txt"
      },
      "src-64ab9f79bfb5": {
        "words": 291049,
        "diagnostic_est_eft": [
          5,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 622.4,
            "panel_good": 7865,
            "panel_bad": 3,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "德语讹字率 0.0004（正形 7865／讹形 3）"
          }
        },
        "德语附加": {
          "h→b率": 0.0002,
          "h→b样本": 9594,
          "变音符每千词": 71.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "德语讹字率 0.0004（正形 7865／讹形 3）",
        "file": "ImmanuelKantsKritikDerReinenVernunftMitEinerEinleitungUnd.txt"
      },
      "src-9f952fc1b4f9": {
        "words": 80313,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.0000；英文：锚 1.7<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.3600）",
        "file": "KantAntropologiaPrammatica.txt"
      },
      "src-5e324d5180fb": {
        "words": 104962,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.5<15.0，若强行读 0.0273；英文：锚 3.5<500.0，若强行读 0.0000；德语：锚 0.9<15.0，若强行读 0.1343）",
        "file": "ProlegomeniKantMartinetti.txt"
      },
      "src-f264e93c21bf": {
        "words": 97706,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2227.2,
            "panel_good": 1153,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1153／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1153／讹形 0）",
        "file": "TheMetaphysicOfEthicsByImmanuelKantTranslatedByJ.w.SempleEdited.txt"
      },
      "src-2311e9d43ba5": {
        "words": 243018,
        "diagnostic_est_eft": [
          17,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 625.5,
            "panel_good": 5703,
            "panel_bad": 2,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "德语讹字率 0.0004（正形 5703／讹形 2）"
          }
        },
        "德语附加": {
          "h→b率": 0.0001,
          "h→b样本": 8413,
          "变音符每千词": 97.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "德语讹字率 0.0004（正形 5703／讹形 2）",
        "file": "aje7738.0003.001.umich.edu.txt"
      },
      "src-2277fd90245f": {
        "words": 150050,
        "diagnostic_est_eft": [
          2446,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.0081；英文：锚 6.9<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.1190）",
        "file": "anthropologiesu00kantgoog.txt"
      },
      "src-e75627a6abc8": {
        "words": 129415,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 630.3,
            "panel_good": 2852,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "德语讹字率 0.0004（正形 2852／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4261,
          "变音符每千词": 100.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "德语讹字率 0.0004（正形 2852／讹形 1）",
        "file": "b24885046.txt"
      },
      "src-0c9ca19f6c3a": {
        "words": 45151,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 547.3,
            "panel_good": 31,
            "panel_bad": 275,
            "若无语种门会读到": 0.8987,
            "verdict": "不可用",
            "rate": 0.8987,
            "reason": "德语讹字率 0.8987（正形 31／讹形 275）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1039,
          "变音符每千词": 49.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8987,
        "reason": "德语讹字率 0.8987（正形 31／讹形 275）",
        "file": "b28738615.txt"
      },
      "src-ecb363455da1": {
        "words": 92306,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 625.1,
            "panel_good": 87,
            "panel_bad": 474,
            "若无语种门会读到": 0.8449,
            "verdict": "不可用",
            "rate": 0.8449,
            "reason": "德语讹字率 0.8449（正形 87／讹形 474）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2517,
          "变音符每千词": 31.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8449,
        "reason": "德语讹字率 0.8449（正形 87／讹形 474）",
        "file": "b28764523.txt"
      },
      "src-2defe6d152fc": {
        "words": 122096,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2176.6,
            "panel_good": 1178,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1178／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1178／讹形 0）",
        "file": "bim_eighteenth-century_essays-and-treatises-on-_kant-immanuel_1798_2.txt"
      },
      "src-b0804850b654": {
        "words": 55916,
        "diagnostic_est_eft": [
          78,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2325.8,
            "panel_good": 590,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 590／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 590／讹形 0）",
        "file": "bim_eighteenth-century_the-metaphysic-of-morals_kant-immanuel_1799_1.txt"
      },
      "src-88e3670ea28b": {
        "words": 124415,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 610.6,
            "panel_good": 3806,
            "panel_bad": 4,
            "若无语种门会读到": 0.001,
            "verdict": "干净",
            "rate": 0.001,
            "reason": "德语讹字率 0.0010（正形 3806／讹形 4）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3398,
          "变音符每千词": 77.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.001,
        "reason": "德语讹字率 0.0010（正形 3806／讹形 4）",
        "file": "briefwechselvoni01kant.txt"
      },
      "src-9572eb3c50ec": {
        "words": 128170,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 589.8,
            "panel_good": 3808,
            "panel_bad": 2,
            "若无语种门会读到": 0.0005,
            "verdict": "干净",
            "rate": 0.0005,
            "reason": "德语讹字率 0.0005（正形 3808／讹形 2）"
          }
        },
        "德语附加": {
          "h→b率": 0.0032,
          "h→b样本": 3775,
          "变音符每千词": 75.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0005,
        "reason": "德语讹字率 0.0005（正形 3808／讹形 2）",
        "file": "briefwechselvoni02kant.txt"
      },
      "src-c9c95efc5799": {
        "words": 113311,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 562.8,
            "panel_good": 3162,
            "panel_bad": 2,
            "若无语种门会读到": 0.0006,
            "verdict": "干净",
            "rate": 0.0006,
            "reason": "德语讹字率 0.0006（正形 3162／讹形 2）"
          }
        },
        "德语附加": {
          "h→b率": 0.0013,
          "h→b样本": 2982,
          "变音符每千词": 74.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0006,
        "reason": "德语讹字率 0.0006（正形 3162／讹形 2）",
        "file": "briefwechselvoni03kant.txt"
      },
      "src-8acbe47be596": {
        "words": 78244,
        "diagnostic_est_eft": [
          0,
          8
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 33.2,
            "panel_good": 33,
            "panel_bad": 408,
            "若无语种门会读到": 0.9252,
            "verdict": "不可用",
            "rate": 0.9252,
            "reason": "德语讹字率 0.9252（正形 33／讹形 408）"
          }
        },
        "德语附加": {
          "h→b率": 0.9583,
          "h→b样本": 24,
          "变音符每千词": 56.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9252,
        "reason": "德语讹字率 0.9252（正形 33／讹形 408）",
        "file": "bub_gb_7rI_AAAAYAAJ.txt"
      },
      "src-e8b8978bb63b": {
        "words": 140813,
        "diagnostic_est_eft": [
          2168,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.0000；英文：锚 0.7<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0000）",
        "file": "bub_gb_F31ZAAAAcAAJ.txt"
      },
      "src-811017be508d": {
        "words": 140375,
        "diagnostic_est_eft": [
          2158,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.0000；英文：锚 0.9<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.1429）",
        "file": "bub_gb_F7gA_JUh5EYC.txt"
      },
      "src-7719bb793564": {
        "words": 46357,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 559.8,
            "panel_good": 25,
            "panel_bad": 296,
            "若无语种门会读到": 0.9221,
            "verdict": "不可用",
            "rate": 0.9221,
            "reason": "德语讹字率 0.9221（正形 25／讹形 296）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1104,
          "变音符每千词": 42.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9221,
        "reason": "德语讹字率 0.9221（正形 25／讹形 296）",
        "file": "bub_gb_Oc0AAAAAcAAJ.txt"
      },
      "src-c90e1301fe6c": {
        "words": 246770,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 563.1,
            "panel_good": 5908,
            "panel_bad": 5,
            "若无语种门会读到": 0.0008,
            "verdict": "干净",
            "rate": 0.0008,
            "reason": "德语讹字率 0.0008（正形 5908／讹形 5）"
          }
        },
        "德语附加": {
          "h→b率": 0.004,
          "h→b样本": 6779,
          "变音符每千词": 51.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0008,
        "reason": "德语讹字率 0.0008（正形 5908／讹形 5）",
        "file": "bub_gb_PiRNAAAAMAAJ.txt"
      },
      "src-f7319e6e8db3": {
        "words": 132469,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 528.7,
            "panel_good": 91,
            "panel_bad": 2344,
            "若无语种门会读到": 0.9626,
            "verdict": "不可用",
            "rate": 0.9626,
            "reason": "德语讹字率 0.9626（正形 91／讹形 2344）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2489,
          "变音符每千词": 68.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9626,
        "reason": "德语讹字率 0.9626（正形 91／讹形 2344）",
        "file": "bub_gb_Wiw-AAAAYAAJ.txt"
      },
      "src-5e054ba8e9ff": {
        "words": 199903,
        "diagnostic_est_eft": [
          11,
          33
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 154.9,
            "panel_good": 210,
            "panel_bad": 1505,
            "若无语种门会读到": 0.8776,
            "verdict": "不可用",
            "rate": 0.8776,
            "reason": "德语讹字率 0.8776（正形 210／讹形 1505）"
          }
        },
        "德语附加": {
          "h→b率": 0.2035,
          "h→b样本": 1263,
          "变音符每千词": 82.0,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8776,
        "reason": "德语讹字率 0.8776（正形 210／讹形 1505）　★ **长 s 之外还坏了**：**h→b 讹变 20.3%**（`nicht`→`nicbt` 这一族，样本 1263）——逐字引用会印出作者没写的形",
        "file": "bub_gb_mIdQAAAAYAAJ.txt"
      },
      "src-11ba5bebadda": {
        "words": 183993,
        "diagnostic_est_eft": [
          6,
          4
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 481.3,
            "panel_good": 1447,
            "panel_bad": 1442,
            "若无语种门会读到": 0.4991,
            "verdict": "不可用",
            "rate": 0.4991,
            "reason": "德语讹字率 0.4991（正形 1447／讹形 1442）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2690,
          "变音符每千词": 96.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.4991,
        "reason": "德语讹字率 0.4991（正形 1447／讹形 1442）",
        "file": "bub_gb_nsALAAAAIAAJ.txt"
      },
      "src-8cb47c41068f": {
        "words": 58705,
        "diagnostic_est_eft": [
          1,
          8
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 31.0,
            "panel_good": 16,
            "panel_bad": 253,
            "若无语种门会读到": 0.9405,
            "verdict": "不可用",
            "rate": 0.9405,
            "reason": "德语讹字率 0.9405（正形 16／讹形 253）"
          }
        },
        "德语附加": {
          "h→b率": 0.75,
          "h→b样本": 24,
          "变音符每千词": 56.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9405,
        "reason": "德语讹字率 0.9405（正形 16／讹形 253）",
        "file": "bub_gb_pbI_AAAAYAAJ.txt"
      },
      "src-693332ba2382": {
        "words": 89858,
        "diagnostic_est_eft": [
          0,
          15
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 168.3,
            "panel_good": 86,
            "panel_bad": 708,
            "若无语种门会读到": 0.8917,
            "verdict": "不可用",
            "rate": 0.8917,
            "reason": "德语讹字率 0.8917（正形 86／讹形 708）"
          }
        },
        "德语附加": {
          "h→b率": 0.0079,
          "h→b样本": 760,
          "变音符每千词": 96.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8917,
        "reason": "德语讹字率 0.8917（正形 86／讹形 708）",
        "file": "bub_gb_tawUAAAAQAAJ.txt"
      },
      "src-d1983cf5ea92": {
        "words": 156610,
        "diagnostic_est_eft": [
          2214,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0144；英文：锚 8.0<500.0，若强行读 0.0000；德语：锚 0.8<15.0，若强行读 0.5385）",
        "file": "critiquedelarai02tissgoog.txt"
      },
      "src-c7cddf7d7774": {
        "words": 138929,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2365.9,
            "panel_good": 1244,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1244／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1244／讹形 0）",
        "file": "critiqueofjudgem00kantuoft.txt"
      },
      "src-e4025e372da2": {
        "words": 32091,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2228.4,
            "panel_good": 370,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 370／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 370／讹形 0）",
        "file": "dli.ministry.13241.txt"
      },
      "src-31a40f5f4513": {
        "words": 87660,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2029.5,
            "panel_good": 873,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 873／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 873／讹形 0）",
        "file": "educationaltheor0000kant.txt"
      },
      "src-bb1683d6b975": {
        "words": 81990,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2192.2,
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
        "file": "educationaltheor00kantuoft.txt"
      },
      "src-86087e7cfa77": {
        "words": 26850,
        "diagnostic_est_eft": [
          11,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 221.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "ikuiseenrauhaanv53461gut.txt"
      },
      "src-fcbcea6ed0f0": {
        "words": 131,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "immanuelkantpap00kant.txt"
      },
      "src-9021c46737e7": {
        "words": 257142,
        "diagnostic_est_eft": [
          14,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2280.6,
            "panel_good": 2475,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2475／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2475／讹形 0）",
        "file": "immanuelkantscri0000kant_c7p6.txt"
      },
      "src-a33dcbcfacb0": {
        "words": 199212,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2255.5,
            "panel_good": 1906,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1906／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1906／讹形 0）",
        "file": "immanuelkantscri02kantuoft.txt"
      },
      "src-9261442ee7b4": {
        "words": 242072,
        "diagnostic_est_eft": [
          7,
          3
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 586.8,
            "panel_good": 6319,
            "panel_bad": 10,
            "若无语种门会读到": 0.0016,
            "verdict": "干净",
            "rate": 0.0016,
            "reason": "德语讹字率 0.0016（正形 6319／讹形 10）"
          }
        },
        "德语附加": {
          "h→b率": 0.0032,
          "h→b样本": 7247,
          "变音符每千词": 62.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0016,
        "reason": "德语讹字率 0.0016（正形 6319／讹形 10）",
        "file": "immanuelkantskr03kantgoog.txt"
      },
      "src-8ea90f250530": {
        "words": 161628,
        "diagnostic_est_eft": [
          106,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2267.0,
            "panel_good": 1345,
            "panel_bad": 1,
            "若无语种门会读到": 0.0007,
            "verdict": "干净",
            "rate": 0.0007,
            "reason": "英文讹字率 0.0007（正形 1345／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0007,
        "reason": "英文讹字率 0.0007（正形 1345／讹形 1）",
        "file": "india.history.resource.90167.txt"
      },
      "src-9d8b6c628788": {
        "words": 13386,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0625；英文：锚 0.7<500.0，若强行读 0.0000；德语：锚 0.7<15.0，若强行读 0.0000）",
        "file": "kant-della-forza-dell-animo.txt"
      },
      "src-1f9e083c4a88": {
        "words": 91086,
        "diagnostic_est_eft": [
          1530,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 1.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.2500）",
        "file": "kantchoixdetexte00kant.txt"
      },
      "src-cb0bedef8e59": {
        "words": 22669,
        "diagnostic_est_eft": [
          36,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 15.9,
            "panel_good": 12,
            "panel_bad": 1,
            "若无语种门会读到": 0.0769,
            "verdict": "未核",
            "reason": "德语面板只命中 13 次 < 30 —— **样本量不够，不是「干净」**"
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
        "reason": "德语面板只命中 13 次 < 30 —— **样本量不够，不是「干净」**　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "kantlobelloylosublime1919.txt"
      },
      "src-86b26ba6469e": {
        "words": 161706,
        "diagnostic_est_eft": [
          106,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2273.9,
            "panel_good": 1360,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1360／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1360／讹形 0）",
        "file": "kantscritique01kantuoft.txt"
      },
      "src-86ba585ee0aa": {
        "words": 199982,
        "diagnostic_est_eft": [
          23,
          27
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 110.9,
            "panel_good": 1109,
            "panel_bad": 2153,
            "若无语种门会读到": 0.66,
            "verdict": "不可用",
            "rate": 0.66,
            "reason": "德语讹字率 0.6600（正形 1109／讹形 2153）"
          }
        },
        "德语附加": {
          "h→b率": 0.0006,
          "h→b样本": 1624,
          "变音符每千词": 98.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.66,
        "reason": "德语讹字率 0.6600（正形 1109／讹形 2153）",
        "file": "kantsgesammeltes0010kant.txt"
      },
      "src-a261a5aa5094": {
        "words": 163454,
        "diagnostic_est_eft": [
          73,
          12
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 55.9,
            "panel_good": 451,
            "panel_bad": 1149,
            "若无语种门会读到": 0.7181,
            "verdict": "不可用",
            "rate": 0.7181,
            "reason": "德语讹字率 0.7181（正形 451／讹形 1149）"
          }
        },
        "德语附加": {
          "h→b率": 0.2619,
          "h→b样本": 42,
          "变音符每千词": 96.2,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7181,
        "reason": "德语讹字率 0.7181（正形 451／讹形 1149）　★ **长 s 之外还坏了**：**h→b 讹变 26.2%**（`nicht`→`nicbt` 这一族，样本 42）——逐字引用会印出作者没写的形",
        "file": "kantsgesammeltes12kant.txt"
      },
      "src-d58c8adb13b0": {
        "words": 233278,
        "diagnostic_est_eft": [
          28,
          31
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 322.5,
            "panel_good": 2211,
            "panel_bad": 480,
            "若无语种门会读到": 0.1784,
            "verdict": "混杂",
            "rate": 0.1784,
            "reason": "德语讹字率 0.1784（正形 2211／讹形 480）"
          }
        },
        "德语附加": {
          "h→b率": 0.002,
          "h→b样本": 3072,
          "变音符每千词": 75.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.1784,
        "reason": "德语讹字率 0.1784（正形 2211／讹形 480）",
        "file": "kantsgesammeltes13kant.txt"
      },
      "src-fa5013c12207": {
        "words": 137563,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 655.9,
            "panel_good": 3304,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 3304／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4879,
          "变音符每千词": 115.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 3304／讹形 0）",
        "file": "kantsgesammeltes55925gut.txt"
      },
      "src-2757219ba6a5": {
        "words": 136600,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2182.7,
            "panel_good": 1068,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1068／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1068／讹形 0）",
        "file": "kantsprolegomen00kantuoft.txt"
      },
      "src-69eaaa5ec8f7": {
        "words": 90804,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2175.2,
            "panel_good": 795,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 795／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 795／讹形 0）",
        "file": "kantsprolegomena00kantuoft.txt"
      },
      "src-4058bbdfafa4": {
        "words": 106625,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2245.9,
            "panel_good": 1238,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1238／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1238／讹形 0）",
        "file": "metaphysicofethi00kantiala.txt"
      },
      "src-5ec28c5c504d": {
        "words": 81187,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2295.6,
            "panel_good": 939,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 939／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 939／讹形 0）",
        "file": "philosophyoflawe0000kant.txt"
      },
      "src-21c82472024f": {
        "words": 186969,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 644.0,
            "panel_good": 5276,
            "panel_bad": 2,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "德语讹字率 0.0004（正形 5276／讹形 2）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 6486,
          "变音符每千词": 77.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "德语讹字率 0.0004（正形 5276／讹形 2）",
        "file": "saemmtlichewerke0004kant.txt"
      },
      "src-75b42fcb7fbd": {
        "words": 182768,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2140.8,
            "panel_good": 2461,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2461／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2461／讹形 0）",
        "file": "textbooktokantcr00kant.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 65,
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
    "ocr_language_death": "⚠ **虚词占比低于下限的 3 份**（多半是 Fraktur／哥特体 OCR 认错字母）：",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 24,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 4,
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
    "可用来源": 55,
    "**按内容去重后的作品数**": 47,
    "虚高": 1.17,
    "未声明的重复对": 0,
    "已声明的重复对": 6,
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
    "判据条数": 33,
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
        "引文数": 2,
        "核过": 2,
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
    "合计": "7 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 10,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 65,
    "train 源总数": 65,
    "本人所著字节": 54622406,
    "train 总字节": 54622406,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 12124814,
    "**判据说未核验的**": 44,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-231cd76552be",
        "原因": "语种判为 **de**（en=0.000 de=0.140 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-23dc040bd16b",
        "原因": "语种判为 **de**（en=0.001 de=0.120 fr=0.007）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-66a095d80263",
        "原因": "语种判为 **de**（en=0.000 de=0.123 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-d7cda8167b58",
        "原因": "语种判为 **de**（en=0.001 de=0.122 fr=0.009）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-1487a594f356",
        "原因": "语种判为 **de**（en=0.000 de=0.133 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-dbda401744b9",
        "原因": "语种判为 **de**（en=0.000 de=0.136 fr=0.007）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-e148cf5a20c5",
        "原因": "语种判为 **de**（en=0.001 de=0.131 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-f56042424327",
        "原因": "语种判为 **de**（en=0.000 de=0.127 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 14.69,
    "**立场句/万字**": 0.36,
    "其中不含第一人称的": 327,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 60,
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
    "已扫答案": 33,
    "第一人称覆盖率": 0.424,
    "状态": "无候选（第一人称覆盖率 0.424）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kant-179/workspaces/immanuel-kant/evidence/source-ledger.jsonl",
    "一手份数": 53,
    "台账总份数": 55,
    "一手占比": 0.9636,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 65,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-231cd76552be 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 65,
    "声称公有领域": 0,
    "不声称（不判）": 65,
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
    "external"
  ],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 65,
    "**`title` 就是文件名**": 0,
    "真书目题名": 65,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 3,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 6,
    "有一边没年份": 59,
    "**逐条**": [
      {
        "source_id": "src-77a77c26b3f0",
        "文件名": "265433882.1678.emory.edu.txt",
        "文件名里的年份": [
          1678
        ],
        "台账 published_at": 1867,
        "差": 189
      },
      {
        "source_id": "src-602d11e03dce",
        "文件名": "265433882.1682.emory.edu.txt",
        "文件名里的年份": [
          1682
        ],
        "台账 published_at": 1867,
        "差": 185
      },
      {
        "source_id": "src-4ec8e58d3909",
        "文件名": "265433882.1713.emory.edu.txt",
        "文件名里的年份": [
          1713
        ],
        "台账 published_at": 1867,
        "差": 154
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
  "claims_total": 23,
  "claims_active": 23,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 23,
  "eval_cases": 33,
  "eval_suite_counts": {
    "known": 3,
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
    "用例数": 33,
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
    "断言条数": 23,
    "source_ids": "逐条各异（非空 23/23，不同取值 21）",
    "evidence_clusters": "逐条各异（非空 23/23，不同取值 23）",
    "counter_source_ids": "整批都空（非空 0/23，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 57,
    "来源数": 65,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 27,
    "挂错作品": 1,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 7,
    "取不到正文的源": 0,
    "例": [
      "clm-775319aa61b6：挂 ['10046192bsb.txt'] → 实 ['265433882.1713.emory.edu.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kant-179/workspaces/immanuel-kant/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-602a1a676506",
      "           **他的认识模型：材料与形式各司其职，缺一方就失效。** `Gedanken ohne Inhalt sind leer, Anschauungen ohne Begriffe…",
      "",
      "低于 10% 的 39 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kant-179/workspaces/immanuel-kant/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kant-179/workspaces/immanuel-kant/audit/source-coverage.json），**未核验**（不是通过）"
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
  "eval_results": 66,
  "candidate_overall": 0.83,
  "baseline_overall": 0.5433,
  "candidate_baseline_delta": 0.2867,
  "suite_candidate_means": {
    "known": 0.7167,
    "boundary": 0.925,
    "voice": 0.95,
    "trajectory": 0.95,
    "contrast": 0.675,
    "fact-preservation": 0.95,
    "style-decoy": 0.55,
    "task-completion": 0.925,
    "planning-fidelity": 0.95,
    "tool-use": 0.95,
    "capability-calibration": 0.825,
    "refusal-stop": 0.9,
    "long-horizon": 0.585,
    "identity-routing": 0.925,
    "anonymous-fidelity": 0.95,
    "token-efficiency": 0.61
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 17/23 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 6 未纳入）",
  "baseline_provenance": {
    "baseline_rows": 33,
    "by_source": {
      "unknown": 33
    },
    "usable_rows": 0,
    "unusable_rows": 33,
    "capability_evidence": false
  },
  "secret_findings": 0
}
```

## Errors

- None

## Warnings

- `corpus.longs-corruption`: **22 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-231cd76552be` 00074230bsb.txt —— 德语讹字率 0.9252（正形 51／讹形 631），**不可做逐字引文**
- `corpus.unexamined-band`: **1/65 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `source.filename-year-mismatch`: 3 条文件名年份与 `published_at` 差 ≥2 年 —— **至少有一处记错了**；判据不知道是哪一处
- `eval.baseline-not-capability-evidence`: 33/33 条基线不可作能力证据（{'unknown': 33}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
