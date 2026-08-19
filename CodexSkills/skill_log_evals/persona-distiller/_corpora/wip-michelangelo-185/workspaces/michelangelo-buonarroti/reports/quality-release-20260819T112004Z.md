# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-michelangelo-185/workspaces/michelangelo-buonarroti`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T11:20:04Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 56,
    "claims": 23
  },
  "sources_total": 56,
  "sources_train": 47,
  "sources_usable_train": 44,
  "sources_holdout": 9,
  "primary_sources": 28,
  "primary_ratio": 0.6364,
  "lane_source_counts": {
    "writings": 21,
    "conversations": 6,
    "expression": 1,
    "external": 16,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 36,
    "已证实归属": 12,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "24 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 56,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干编本的题名页逐字（`src-34bb6d56038a`，1875）：`LE LETTERE DI MICHELANGELO BUONARROTI PUBBL",
    "citation": "https://archive.org/details/leletteredimiche00mich（台账 `src-34bb6d56038a` 的 `loca",
    "争议篇目数": 15,
    "P1 声称本人所著": 36,
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
    "声称本人所著的 P1 源": 6,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 6,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 44,
    "fact 类条数": 13,
    "**人物事实**（计入）": 13,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 9,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 2,
    "**可复用做法**（计入）": 1,
    "复述式（不计入）": 1,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-a928f1063ac7 **只有步骤没有判据**：照着做的人不知道自己做错没有"
    ],
    "**未达**": [
      "可复用 `work-method` 断言 1 条 < 暂定 3 条（另有 1 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 56,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "10754532bsb.txt",
        "非拉丁字符": 2,
        "全同形字词": 0,
        "样例": [
          "uαν 读作 uαv"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 9,
      "干净": 19,
      "不适用": 22,
      "未核": 4,
      "混杂": 2
    },
    "逐份": {
      "src-0f90e46d5f7b": {
        "words": 44817,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 320.0,
            "panel_good": 124,
            "panel_bad": 95,
            "若无语种门会读到": 0.4338,
            "verdict": "不可用",
            "rate": 0.4338,
            "reason": "德语讹字率 0.4338（正形 124／讹形 95）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 526,
          "变音符每千词": 30.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.4338,
        "reason": "德语讹字率 0.4338（正形 124／讹形 95）",
        "file": "10542478bsb.txt"
      },
      "src-60cd9a49f915": {
        "words": 43794,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 333.2,
            "panel_good": 132,
            "panel_bad": 64,
            "若无语种门会读到": 0.3265,
            "verdict": "不可用",
            "rate": 0.3265,
            "reason": "德语讹字率 0.3265（正形 132／讹形 64）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 536,
          "变音符每千词": 28.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.3265,
        "reason": "德语讹字率 0.3265（正形 132／讹形 64）",
        "file": "10754532bsb.txt"
      },
      "src-4b92a7f08408": {
        "words": 93675,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2140.5,
            "panel_good": 1021,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1021／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1021／讹形 0）",
        "file": "MICHELANGELO_753.txt"
      },
      "src-5a9c6f4bef17": {
        "words": 66873,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2134.9,
            "panel_good": 640,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 640／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 640／讹形 0）",
        "file": "artistmerchanta00bottgoog.txt"
      },
      "src-d3a820576752": {
        "words": 15552,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.4697；英文：锚 14.8<500.0，若强行读 0.0000；德语：锚 1.3<15.0，若强行读 0.6316）",
        "file": "bub_gb_-Ex3yhDSSTcC.txt"
      },
      "src-7bd7f20fa044": {
        "words": 19805,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.0<15.0，若强行读 0.0353；英文：锚 6.1<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.2500）",
        "file": "bub_gb_4srIAdQY3UsC.txt"
      },
      "src-f547bc4a71ad": {
        "words": 94698,
        "diagnostic_est_eft": [
          611,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0020；英文：锚 1.0<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.2439）",
        "file": "bub_gb_A4VTAAAAcAAJ.txt"
      },
      "src-a774edeb44f1": {
        "words": 95134,
        "diagnostic_est_eft": [
          597,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.0020；英文：锚 1.2<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.1739）",
        "file": "bub_gb_FplWAAAAcAAJ.txt"
      },
      "src-fc3cd1b895bb": {
        "words": 69030,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 277.6,
            "panel_good": 275,
            "panel_bad": 523,
            "若无语种门会读到": 0.6554,
            "verdict": "不可用",
            "rate": 0.6554,
            "reason": "德语讹字率 0.6554（正形 275／讹形 523）"
          }
        },
        "德语附加": {
          "h→b率": 0.0037,
          "h→b样本": 267,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.6554,
        "reason": "德语讹字率 0.6554（正形 275／讹形 523）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "bub_gb_VogLAQAAIAAJ.txt"
      },
      "src-f3ac5691f1e3": {
        "words": 168710,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0532；英文：锚 6.1<500.0，若强行读 0.0000；德语：锚 1.1<15.0，若强行读 0.2746）",
        "file": "bub_gb_eyp5Is6AwlcC.txt"
      },
      "src-3863a0005b65": {
        "words": 168389,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0479；英文：锚 3.7<500.0，若强行读 0.0000；德语：锚 1.0<15.0，若强行读 0.2283）",
        "file": "bub_gb_g9rj_o_cnSAC.txt"
      },
      "src-28683b5f4292": {
        "words": 94585,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.8<15.0，若强行读 0.0201；英文：锚 2.6<500.0，若强行读 0.0000；德语：锚 1.3<15.0，若强行读 0.1143）",
        "file": "bub_gb_rHu4_709T2oC.txt"
      },
      "src-6094206729a1": {
        "words": 186975,
        "diagnostic_est_eft": [
          25,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 7.8<15.0，若强行读 0.0132；英文：锚 9.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.2682）",
        "file": "buonarroti_le_lettere_di_michelangelo_buonarroti.txt"
      },
      "src-ff3f7006072b": {
        "words": 5326,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2164.9,
            "panel_good": 42,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 42／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 42／讹形 0）",
        "file": "cu31924008756847.txt"
      },
      "src-05d67ff7e9df": {
        "words": 24998,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1082.9,
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
        "file": "cu31924014269975.txt"
      },
      "src-dff6d04bdd38": {
        "words": 4914,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1709.4,
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
        "file": "cu31924032174173.txt"
      },
      "src-1ba2ff2c67ee": {
        "words": 3013,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "拉丁": {
            "语域": "拉丁",
            "anchors_per_10k": 23.2,
            "panel_good": 2,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "拉丁面板只命中 2 次 < 30 —— **样本量不够，不是「干净」**"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 86.3,
            "panel_good": 7,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "德语面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 8,
          "变音符每千词": 17.8,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "ae_连字": {
          "ae_per_1000": 1.04,
          "quae": 2,
          "que": 0,
          "quae_ratio": 1.0,
          "判读": "未核",
          "理由": "`quae`/`que` 合计只有 2 次 < 20，**样本量不够，不是「完好」**"
        },
        "verdict": "不可用",
        "rate": null,
        "reason": "拉丁面板只命中 2 次 < 30 —— **样本量不够，不是「干净」**　（两语域都适用，取更差的一侧）　★ **长 s 之外还坏了**：**变音符湮灭**（17.8/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "dervonmichelang00vatigoog.txt"
      },
      "src-4228373b40fa": {
        "words": 71245,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 721.7,
            "panel_good": 1457,
            "panel_bad": 1,
            "若无语种门会读到": 0.0007,
            "verdict": "干净",
            "rate": 0.0007,
            "reason": "德语讹字率 0.0007（正形 1457／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0005,
          "h→b样本": 1938,
          "变音符每千词": 84.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0007,
        "reason": "德语讹字率 0.0007（正形 1457／讹形 1）",
        "file": "diebriefedesmich00mich.txt"
      },
      "src-9c282d5b3385": {
        "words": 214670,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 330.6,
            "panel_good": 1904,
            "panel_bad": 105,
            "若无语种门会读到": 0.0523,
            "verdict": "混杂",
            "rate": 0.0523,
            "reason": "德语讹字率 0.0523（正形 1904／讹形 105）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3730,
          "变音符每千词": 39.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.0523,
        "reason": "德语讹字率 0.0523（正形 1904／讹形 105）",
        "file": "diedichtungendes00mich.txt"
      },
      "src-4d7176e3057b": {
        "words": 74518,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 19.9,
            "panel_good": 222,
            "panel_bad": 298,
            "若无语种门会读到": 0.5731,
            "verdict": "不可用",
            "rate": 0.5731,
            "reason": "德语讹字率 0.5731（正形 222／讹形 298）"
          }
        },
        "德语附加": {
          "h→b率": 0.3333,
          "h→b样本": 3,
          "变音符每千词": 44.6,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5731,
        "reason": "德语讹字率 0.5731（正形 222／讹形 298）",
        "file": "diegedichte00michuoft.txt"
      },
      "src-f800dc9a4827": {
        "words": 2985,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2201.0,
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
        "file": "eightyfouretche00raphgoog.txt"
      },
      "src-2141d0967120": {
        "words": 2586,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2351.1,
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
        "file": "eightyfouretched00michuoft.txt"
      },
      "src-3adec5b59f19": {
        "words": 5347,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2229.3,
            "panel_good": 51,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 51／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 51／讹形 0）",
        "file": "facsimilesorigi01fishgoog.txt"
      },
      "src-57f4222a1885": {
        "words": 5319,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2250.4,
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
        "file": "facsimilesorigi02fishgoog.txt"
      },
      "src-172dcf3de9b2": {
        "words": 25821,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 503.1,
            "panel_good": 399,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 399／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 560,
          "变音符每千词": 86.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 399／讹形 0）",
        "file": "gri_33125004476533.txt"
      },
      "src-c85f2025c5a7": {
        "words": 8495,
        "diagnostic_est_eft": [
          45,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0192；英文：锚 121.2<500.0，若强行读 0.0000；德语：锚 5.9<15.0，若强行读 1.0000）",
        "file": "gri_33125016373926.txt"
      },
      "src-2a5c6cdc444e": {
        "words": 3698,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 462.4,
            "panel_good": 103,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 103／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 116,
          "变音符每千词": 88.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 103／讹形 0）",
        "file": "gri_33125016448520.txt"
      },
      "src-52bee34f4999": {
        "words": 10773,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0227；英文：锚 8.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2000）",
        "file": "ilritrattomiglio00mich.txt"
      },
      "src-14161091ddb3": {
        "words": 161613,
        "diagnostic_est_eft": [
          26,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 8.0<15.0，若强行读 0.0038；英文：锚 9.3<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.3478）",
        "file": "laletteredimich00buongoog.txt"
      },
      "src-8999a5688bea": {
        "words": 190248,
        "diagnostic_est_eft": [
          24,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 7.1<15.0，若强行读 0.0042；英文：锚 9.3<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.3203）",
        "file": "laletteredimich00milagoog.txt"
      },
      "src-2b654ec5cfb3": {
        "words": 5598,
        "diagnostic_est_eft": [
          53,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "ldpd_9355154_000.txt"
      },
      "src-34bb6d56038a": {
        "words": 193022,
        "diagnostic_est_eft": [
          25,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 7.5<15.0，若强行读 0.0112；英文：锚 2.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.3208）",
        "file": "leletteredimiche00mich.txt"
      },
      "src-e7ab3c2184e2": {
        "words": 79994,
        "diagnostic_est_eft": [
          11,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.0123；英文：锚 24.1<500.0，若强行读 0.0769；德语：锚 1.9<15.0，若强行读 0.2447）",
        "file": "lerimedimichela00magggoog.txt"
      },
      "src-43c819c03a55": {
        "words": 76905,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.9<15.0，若强行读 0.0018；英文：锚 12.0<500.0，若强行读 0.0000；德语：锚 1.8<15.0，若强行读 0.1471）",
        "file": "lerimedimichelag00mich.txt"
      },
      "src-b69075a7bf0b": {
        "words": 77664,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.0070；英文：锚 11.3<500.0，若强行读 0.0000；德语：锚 1.7<15.0，若强行读 0.1852）",
        "file": "lerimedimichelag00mich_1.txt"
      },
      "src-1a70dbd068ca": {
        "words": 101651,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2247.9,
            "panel_good": 884,
            "panel_bad": 3,
            "若无语种门会读到": 0.0034,
            "verdict": "干净",
            "rate": 0.0034,
            "reason": "英文讹字率 0.0034（正形 884／讹形 3）"
          }
        },
        "verdict": "干净",
        "rate": 0.0034,
        "reason": "英文讹字率 0.0034（正形 884／讹形 3）",
        "file": "lifemichaelange02buongoog.txt"
      },
      "src-53e19db4cba0": {
        "words": 109415,
        "diagnostic_est_eft": [
          753,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0109；英文：锚 0.5<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.2000）",
        "file": "loeuvrelittrai00michuoft.txt"
      },
      "src-7c1b6c3e60fe": {
        "words": 7389,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2215.5,
            "panel_good": 72,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 72／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 72／讹形 0）",
        "file": "michaelangelo00michrich.txt"
      },
      "src-20b35d40dc1d": {
        "words": 108131,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2250.1,
            "panel_good": 1061,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1061／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1061／讹形 0）",
        "file": "michaelangelobuo0000unse_y1s3.txt"
      },
      "src-acd20e592f1e": {
        "words": 106799,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2263.8,
            "panel_good": 1062,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1062／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1062／讹形 0）",
        "file": "michaelangelobuo00holrrich.txt"
      },
      "src-e010372f95e3": {
        "words": 14042,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2054.6,
            "panel_good": 107,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 107／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 107／讹形 0）",
        "file": "michelangeloaspa00michrich.txt"
      },
      "src-f06a8e0a2268": {
        "words": 102267,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 638.7,
            "panel_good": 253,
            "panel_bad": 333,
            "若无语种门会读到": 0.5683,
            "verdict": "不可用",
            "rate": 0.5683,
            "reason": "德语讹字率 0.5683（正形 253／讹形 333）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2362,
          "变音符每千词": 84.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.5683,
        "reason": "德语讹字率 0.5683（正形 253／讹形 333）",
        "file": "michelangelodesm00michuoft.txt"
      },
      "src-9b7ef7d45470": {
        "words": 51400,
        "diagnostic_est_eft": [
          0,
          5
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 62.5,
            "panel_good": 176,
            "panel_bad": 243,
            "若无语种门会读到": 0.58,
            "verdict": "不可用",
            "rate": 0.58,
            "reason": "德语讹字率 0.5800（正形 176／讹形 243）"
          }
        },
        "德语附加": {
          "h→b率": 0.0541,
          "h→b样本": 37,
          "变音符每千词": 131.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.58,
        "reason": "德语讹字率 0.5800（正形 176／讹形 243）",
        "file": "michelangeloeine00hild.txt"
      },
      "src-6ccb3d0796b1": {
        "words": 29975,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 530.1,
            "panel_good": 648,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 648／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 794,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 648／讹形 0）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "michelangelogedi15813gut.txt"
      },
      "src-e578ad29a2aa": {
        "words": 14045,
        "diagnostic_est_eft": [
          60,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 3.6<500.0，若强行读 0.0000；德语：锚 0.7<15.0，若强行读 0.0000）",
        "file": "oeuvrescomplte00mich.txt"
      },
      "src-d89e65b8002f": {
        "words": 171049,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0182；英文：锚 8.6<500.0，若强行读 0.0000；德语：锚 1.1<15.0，若强行读 0.2209）",
        "file": "operevarieinver01fanfgoog.txt"
      },
      "src-d8fee32cb32d": {
        "words": 33335,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 2.1<500.0，若强行读 0.0000；德语：锚 0.9<15.0，若强行读 0.3667）",
        "file": "poesiemic00michuoft.txt"
      },
      "src-8539ad71569a": {
        "words": 93708,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2139.2,
            "panel_good": 1021,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1021／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1021／讹形 0）",
        "file": "recordofhislifea00michuoft.txt"
      },
      "src-7af49c8ef468": {
        "words": 92494,
        "diagnostic_est_eft": [
          11,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.0277；英文：锚 17.3<500.0，若强行读 0.0000；德语：锚 1.3<15.0，若强行读 0.1977）",
        "file": "rimedimichelagn00biaggoog.txt"
      },
      "src-2bcd0f7adde8": {
        "words": 61791,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 246.6,
            "panel_good": 828,
            "panel_bad": 48,
            "若无语种门会读到": 0.0548,
            "verdict": "混杂",
            "rate": 0.0548,
            "reason": "德语讹字率 0.0548（正形 828／讹形 48）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 862,
          "变音符每千词": 41.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "混杂",
        "rate": 0.0548,
        "reason": "德语讹字率 0.0548（正形 828／讹形 48）",
        "file": "saemmtlichegedic00michuoft.txt"
      },
      "src-319c5b194292": {
        "words": 23163,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1208.0,
            "panel_good": 126,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 126／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 126／讹形 0）",
        "file": "selectedpoemsfro00michrich.txt"
      },
      "src-bde8403de0f8": {
        "words": 2009,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2070.7,
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
        "file": "seventyetchedfa00fishgoog.txt"
      },
      "src-85c5b7662cb5": {
        "words": 24099,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1642.0,
            "panel_good": 150,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 150／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 150／讹形 0）",
        "file": "sonnetsmadrigals00michrich.txt"
      },
      "src-dc47a809071f": {
        "words": 32847,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1798.0,
            "panel_good": 276,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 276／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 276／讹形 0）",
        "file": "sonnetsofmichael00michrich.txt"
      },
      "src-7e58c4daeade": {
        "words": 37649,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2134.2,
            "panel_good": 412,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 412／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 412／讹形 0）",
        "file": "sonnetsofmichela00michrich.txt"
      },
      "src-3e9fd617a136": {
        "words": 8715,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1744.1,
            "panel_good": 31,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 31／讹形 0）"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 86.1,
            "panel_good": 31,
            "panel_bad": 3,
            "若无语种门会读到": 0.0882,
            "verdict": "混杂",
            "rate": 0.0882,
            "reason": "德语讹字率 0.0882（正形 31／讹形 3）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 24,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.0882,
        "reason": "德语讹字率 0.0882（正形 31／讹形 3）　（两语域都适用，取更差的一侧）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "workofmichelange00mich.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 56,
    "与台账不一致的道": [
      "01-writings.md"
    ],
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
    "ocr_language_death": "⚠ **虚词占比低于下限的 1 份**（多半是 Fraktur／哥特体 OCR 认错字母）：",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上"
  },
  "quote_speaker": {
    "长逐字引文": 20,
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
    "可用来源": 44,
    "**按内容去重后的作品数**": 31,
    "虚高": 1.419,
    "未声明的重复对": 0,
    "已声明的重复对": 14,
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
        "引文数": 4,
        "核过": 3,
        "**对不上**": [
          "## Scope and assigned sources"
        ]
      },
      "03-expression.md": {
        "引文数": 1,
        "核过": 1,
        "**对不上**": []
      },
      "04-external.md": {
        "引文数": 4,
        "核过": 3,
        "**对不上**": [
          "## Scope and assigned sources"
        ]
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
    "合计": "12 条引文，对不上 2 条",
    "读不到正文的来源": [],
    "holdout 源数": 9,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 56,
    "train 源总数": 56,
    "本人所著字节": 23554295,
    "train 总字节": 23554295,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 2741445,
    "**判据说未核验的**": 27,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-0f90e46d5f7b",
        "原因": "语种判为 **de**（en=0.001 de=0.059 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-60cd9a49f915",
        "原因": "语种判为 **de**（en=0.001 de=0.061 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-d3a820576752",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-7bd7f20fa044",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-f547bc4a71ad",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.056）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-a774edeb44f1",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.055）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-fc3cd1b895bb",
        "原因": "语种判为 **de**（en=0.001 de=0.056 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-28683b5f4292",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.001）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 20.01,
    "**立场句/万字**": 0.16,
    "其中不含第一人称的": 28,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 36,
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
    "第一人称覆盖率": 0.375,
    "状态": "**候选：基线可能不入戏**（第一人称覆盖率 0.375 < 0.4）",
    "**这几条值得人去读一眼**": [
      "q-00e7cdc5",
      "q-2dfb787a",
      "q-3a1c1557",
      "q-5734d518",
      "q-711832ed",
      "q-8e3587b0",
      "q-92131978",
      "q-9d0c3166"
    ],
    "★ 口径": "按整份载荷算第一人称覆盖率，**不判单条**——中文成句常省主语，Harvey #103 的 `hv-decoy-01` 通篇无「我」而完全是入戏的。\n★★ **这是候选名单，不是判决**：阈值在 22 个已判分人物上拟合，对第 23 个人没有保证。**去读原文，看它是在扮演这个人还是在介绍这个人。**"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-michelangelo-185/workspaces/michelangelo-buonarroti/evidence/source-ledger.jsonl",
    "一手份数": 28,
    "台账总份数": 44,
    "一手占比": 0.6364,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 53,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-0f90e46d5f7b 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 56,
    "声称公有领域": 0,
    "不声称（不判）": 56,
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
    "external"
  ],
  "translation_witness": {
    "申报的并行见证组": 9,
    "组内塌缩的断言": 1,
    "错": 1,
    "明细": [
      "✗ clm-7cee3cb6b511（value）把同一部作品的 2 份见证当成了 2 处来源：['src-6094206729a1', 'src-8999a5688bea']\n    → **它们是同一部作品的不同译本／版本，只算一处。**「≥2 处独立证据」实际未达成。"
    ],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 56,
    "**`title` 就是文件名**": 1,
    "真书目题名": 55,
    "比例": 0.0179,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 56,
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
  "claim_markers": 22,
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
    "断言条数": 23,
    "source_ids": "逐条各异（非空 23/23，不同取值 16）",
    "evidence_clusters": "逐条各异（非空 23/23，不同取值 16）",
    "counter_source_ids": "整批都空（非空 0/23，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 9,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 41,
    "来源数": 56,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 24,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 14,
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-michelangelo-185/workspaces/michelangelo-buonarroti/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  decision-policy.md     clm-85415c0c4457",
      "           **他知道自己写得琐碎，而把最终判断交给对方**：`lo scrivo cose da ridere , ma so ben , c#e voi troverete cosa …",
      "",
      "低于 10% 的 32 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-michelangelo-185/workspaces/michelangelo-buonarroti/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-michelangelo-185/workspaces/michelangelo-buonarroti/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.7944,
  "baseline_overall": 0.6466,
  "candidate_baseline_delta": 0.1478,
  "suite_candidate_means": {
    "known": 0.45,
    "boundary": 0.8,
    "voice": 0.95,
    "trajectory": 0.95,
    "contrast": 0.925,
    "fact-preservation": 0.95,
    "style-decoy": 0.525,
    "task-completion": 0.9,
    "planning-fidelity": 0.95,
    "tool-use": 0.95,
    "capability-calibration": 0.9,
    "refusal-stop": 0.2,
    "long-horizon": 0.85,
    "identity-routing": 0.7,
    "anonymous-fidelity": 0.91,
    "token-efficiency": 0.8
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 22/23 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 1 未纳入）",
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

- `claim.parallel-witness-collapse`: ✗ clm-7cee3cb6b511（value）把同一部作品的 2 份见证当成了 2 处来源：['src-6094206729a1', 'src-8999a5688bea']     → **它们是同一部作品的不同译本／版本，只算一处。**「≥2 处独立证据」实际未达成。
- `claim.orphan`: active Claim clm-mc-mm-01 is not rendered in any core artifact
- `content.quote-no-locator`: 有逐字引文无从回查：同段内既无年份也无卷页刊名。长逐字引文 63 条，同段带坐标 62 条，**缺坐标 1 条**

## Warnings

- `corpus.longs-corruption`: **9 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-0f90e46d5f7b` 10542478bsb.txt —— 德语讹字率 0.4338（正形 124／讹形 95），**不可做逐字引文**
- research.lane_quotes：2 条逐字引文回原文对不上——**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区
- `corpus.title-is-just-the-filename`: **1/56 行的 `title` 就是文件名**（2%）——这个字段没有承载信息。后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**，引文坐标与「挂到哪部作品」也全落在文件名上。★ 与空值不同——**空值至少诚实，填成文件名的字段看起来是填过的**。
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
