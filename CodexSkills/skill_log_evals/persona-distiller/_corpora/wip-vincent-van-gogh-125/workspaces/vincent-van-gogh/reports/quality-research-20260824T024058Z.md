# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-vincent-van-gogh-125/workspaces/vincent-van-gogh`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-24T02:40:58Z`
- Result: **PASS**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 23,
    "claims": 14
  },
  "sources_total": 23,
  "sources_train": 20,
  "sources_usable_train": 20,
  "sources_holdout": 3,
  "primary_sources": 18,
  "primary_ratio": 0.9,
  "lane_source_counts": {
    "writings": 2,
    "conversations": 8,
    "expression": 0,
    "external": 9,
    "decisions": 0,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 11,
    "已证实归属": 10,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "1 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 23,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Vincent van Gogh（1853-03-30 生于荷兰 Zundert – 1890-07-29 卒于 Auvers-sur-Oise）书信著作归属依",
    "citation": "archive.org 元数据 creator 字段（Gogh, Vincent van, 1853-1890）+ 各载体题名页（见 covered_sourc",
    "争议篇目数": 0,
    "P1 声称本人所著": 9,
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
    "usable_train": 20,
    "fact 类条数": 5,
    "**人物事实**（计入）": 5,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 1,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 1,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-5b402c51af3a **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 1 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 1,
    "引文层问题": 31,
    "**这些地方分不清原文与译文**": [
      "case-known-1　有 1 处外语引文而**全文无引文层标注**（首处：「One cannot be at the Pole and at the Equato…）——**读者无从知道那是原文还是译文**",
      "case-known-2　有 2 处外语引文而**全文无引文层标注**（首处：「my way will be the road to colour…）——**读者无从知道那是原文还是译文**",
      "case-fact-preservation-1　有 1 处外语引文而**全文无引文层标注**（首处：「One cannot be at the Pole and at the Equato…）——**读者无从知道那是原文还是译文**",
      "case-fact-preservation-2　有 3 处外语引文而**全文无引文层标注**（首处：「my way will be the road to colour…）——**读者无从知道那是原文还是译文**",
      "case-boundary-1　有 1 处外语引文而**全文无引文层标注**（首处：「One cannot be at the Pole and at the Equato…）——**读者无从知道那是原文还是译文**",
      "case-boundary-2　有 2 处外语引文而**全文无引文层标注**（首处：「Colour as colour means something…）——**读者无从知道那是原文还是译文**",
      "case-voice-1　有 2 处外语引文而**全文无引文层标注**（首处：「Colour as colour means something…）——**读者无从知道那是原文还是译文**",
      "case-voice-2　有 2 处外语引文而**全文无引文层标注**（首处：「Colour as colour means something…）——**读者无从知道那是原文还是译文**",
      "case-trajectory-1　有 3 处外语引文而**全文无引文层标注**（首处：「my way will be the road to colour…）——**读者无从知道那是原文还是译文**",
      "case-contrast-1　有 2 处外语引文而**全文无引文层标注**（首处：「Colour as colour means something…）——**读者无从知道那是原文还是译文**",
      "case-contrast-2　有 2 处外语引文而**全文无引文层标注**（首处：「Colour as colour means something…）——**读者无从知道那是原文还是译文**",
      "case-style-decoy-1　有 1 处外语引文而**全文无引文层标注**（首处：「One cannot be at the Pole and at the Equato…）——**读者无从知道那是原文还是译文**"
    ],
    "口径": "**数的是形态，不判真伪**——标了「译文」的伪造引文照样过；它挡的是「忘了标」与「标反了」，不挡「编的」。故只报不拦。"
  },
  "ocr_homoglyphs": {
    "已查语料件": 23,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 12,
      "不适用": 9,
      "不可用": 1,
      "未核": 1
    },
    "逐份": {
      "src-3194bc93ac68": {
        "words": 2943,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 285.4,
            "panel_good": 36,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 36／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 42,
          "变音符每千词": 99.2,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 36／讹形 0）",
        "file": "McGillLibrary-rbsc_stern_vincent-van-gogh_ND653G7A41928-17738.txt"
      },
      "src-5fb2d553bd1a": {
        "words": 37042,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 704.9,
            "panel_good": 855,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 855／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 993,
          "变音符每千词": 71.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 855／讹形 0）",
        "file": "briefe0000gogh.txt"
      },
      "src-7d22c26873fd": {
        "words": 32454,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 703.8,
            "panel_good": 732,
            "panel_bad": 2,
            "若无语种门会读到": 0.0027,
            "verdict": "干净",
            "rate": 0.0027,
            "reason": "德语讹字率 0.0027（正形 732／讹形 2）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 879,
          "变音符每千词": 98.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0027,
        "reason": "德语讹字率 0.0027（正形 732／讹形 2）",
        "file": "briefe1906gogh.txt"
      },
      "src-eb5be7530935": {
        "words": 32938,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 700.7,
            "panel_good": 731,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 731／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 876,
          "变音符每千词": 97.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 731／讹形 0）",
        "file": "briefego00goghuoft.txt"
      },
      "src-9367176204f7": {
        "words": 236503,
        "diagnostic_est_eft": [
          249,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0167；英文：锚 88.6<500.0，若强行读 0.0000；德语：锚 1.2<15.0，若强行读 0.2800）",
        "file": "brievenaanzijnbr01gogh.txt"
      },
      "src-f10cdf272eba": {
        "words": 252853,
        "diagnostic_est_eft": [
          74,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0435；英文：锚 69.6<500.0，若强行读 0.0000；德语：锚 0.8<15.0，若强行读 0.4000）",
        "file": "brievenaanzijnbr02gogh.txt"
      },
      "src-528bd48d45fd": {
        "words": 195818,
        "diagnostic_est_eft": [
          2387,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0053；英文：锚 1.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0000）",
        "file": "brievenaanzijnbr03gogh.txt"
      },
      "src-683020755a90": {
        "words": 236838,
        "diagnostic_est_eft": [
          30,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1850.5,
            "panel_good": 2272,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2272／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2272／讹形 0）",
        "file": "bwb_C0-BNZ-746_1.txt"
      },
      "src-be2e33dfe784": {
        "words": 253812,
        "diagnostic_est_eft": [
          74,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1811.1,
            "panel_good": 2391,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2391／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2391／讹形 0）",
        "file": "bwb_C0-BNZ-755_2.txt"
      },
      "src-83dba76ee577": {
        "words": 8788,
        "diagnostic_est_eft": [
          37,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 25.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "catalogusdertent00gogh.txt"
      },
      "src-ac0ac7a914af": {
        "words": 54483,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2053.3,
            "panel_good": 533,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 533／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 533／讹形 0）",
        "file": "cu31924101831505.txt"
      },
      "src-e973a58df312": {
        "words": 3411,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "gri_33125012764672.txt"
      },
      "src-15ac632b9c8b": {
        "words": 38458,
        "diagnostic_est_eft": [
          327,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0197；英文：锚 3.1<500.0，若强行读 0.0000；德语：锚 2.3<15.0，若强行读 0.4545）",
        "file": "lafoliedevincent00doit.txt"
      },
      "src-5751a200cf57": {
        "words": 55421,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2031.7,
            "panel_good": 533,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 533／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 533／讹形 0）",
        "file": "lettersofpostimp00gogh.txt"
      },
      "src-f5617484c043": {
        "words": 54473,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2051.7,
            "panel_good": 533,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 533／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 533／讹形 0）",
        "file": "lettersofpostimp00goghuoft.txt"
      },
      "src-2bde83f62227": {
        "words": 16618,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 560.8,
            "panel_good": 355,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 355／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 420,
          "变音符每千词": 94.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 355／讹形 0）",
        "file": "persnlicheerinne00duqu.txt"
      },
      "src-8e3cd60bfeea": {
        "words": 18468,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1978.0,
            "panel_good": 149,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 149／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 149／讹形 0）",
        "file": "persrecollec00gogh.txt"
      },
      "src-0511febaa048": {
        "words": 1228,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 16.3<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "tentoonstellingd00gogh.txt"
      },
      "src-b3328eb38b77": {
        "words": 20951,
        "diagnostic_est_eft": [
          177,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 1.9<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.0000）",
        "file": "vangoghvincent00dureuoft.txt"
      },
      "src-aa28f9129a99": {
        "words": 35382,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1852.9,
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
        "file": "vincentvangoghbi02meie.txt"
      },
      "src-e1168364413e": {
        "words": 29783,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 757.5,
            "panel_good": 705,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 705／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 864,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 705／讹形 0）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "vincentvangoghbr00maut.txt"
      },
      "src-e9d58b40a500": {
        "words": 300,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 733.3,
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
        "file": "vincentvangoghex00gogh.txt"
      },
      "src-b6ad5f245978": {
        "words": 16402,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.1176；英文：锚 48.2<500.0，若强行读 0.0000；德语：锚 6.7<15.0，若强行读 0.0000）",
        "file": "vincentvangoghpe02duqu.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 23,
    "与台账不一致的道": [
      "04-external.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "unexamined_band": {
      "n": 1,
      "of": 23,
      "files": [
        "vincentvangoghex00gogh.txt"
      ]
    },
    "byline_in_carrier": "核过 21 条，指错 0 条",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 0 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `wip-vincent-van-gogh-125`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 10 条，切分后核验片段 12 个，未命中 1 个，长 s 还原后才命中 0 个｜⚠ 研究/04-external.md: 「CATALOGUS DER TENTOONSTELLING VAN SCHILDERIJEN EN TEEKENINGEN DOOR VINCENT VAN GOGH STEDELIJK MUSEUM」",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 8874846,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
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
    "可用来源": 20,
    "**按内容去重后的作品数**": 15,
    "虚高": 1.333,
    "未声明的重复对": 0,
    "已声明的重复对": 3,
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
    "抄答案": {
      "英文原串层": 2,
      "**中译/压缩层**": 17,
      "占比": "53%",
      "★": "冻结指令写着「中译与压缩也算抄」；上一层只比英文，**中文要 12 个字才够**，实测违规在 3–5 字之间"
    },
    "要求出戏": {
      "判据要求出戏": 5,
      "产物出戏（已扣除判据招来的）": 0,
      "**判据招来的**": []
    },
    "忠实度自相矛盾": {
      "题数": 0,
      "逐题": [],
      "★": "声称逐字忠实于**印本**，却展示只有影印/OCR 才有的痕迹——要么「照印本录」这句错了，要么引文被动过。**只报不拦**：改法涉及引文，改哪一头由人定。"
    },
    "★★ 口径": "**只写 metrics，不改判定。** 改判据要动按人物冻结的指令，那是下一个人物的事（见 RUBRIC-RULES-v2 第 ⑥ 条）。"
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
    "holdout 源数": 3,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 19,
    "train 源总数": 23,
    "本人所著字节": 9256348,
    "train 总字节": 10027885,
    "own_voice_ratio": 0.9231,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 6781580,
    "**判据说未核验的**": 5,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-5fb2d553bd1a",
        "原因": "语种判为 **de**（en=0.000 de=0.135 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-7d22c26873fd",
        "原因": "语种判为 **de**（en=0.000 de=0.137 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-eb5be7530935",
        "原因": "语种判为 **de**（en=0.000 de=0.136 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-528bd48d45fd",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.077）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-e1168364413e",
        "原因": "语种判为 **de**（en=0.000 de=0.136 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 22.62,
    "**立场句/万字**": 0.56,
    "其中不含第一人称的": 266,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 12,
    "**疑似著录卡**": {},
    "读不到正文的": [],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "逐字英文引文": 0,
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
    "拒答溢出候选": 2,
    "**这几条值得人去读一眼**": [
      "case-trajectory-1",
      "case-refusal-stop-1"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "载荷": "baseline.v1.json",
    "已扫答案": 32,
    "第一人称覆盖率": 1.0,
    "状态": "无候选（第一人称覆盖率 1.000）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-vincent-van-gogh-125/workspaces/vincent-van-gogh/evidence/source-ledger.jsonl",
    "一手份数": 18,
    "台账总份数": 20,
    "一手占比": 0.9,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 23,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-3194bc93ac68 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 23,
    "声称公有领域": 0,
    "不声称（不判）": 23,
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
    "external",
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
    "台账行数": 23,
    "**`title` 就是文件名**": 0,
    "真书目题名": 23,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 1,
    "有一边没年份": 22,
    "**逐条**": [],
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

- None

## Warnings

- `corpus.longs-corruption`: **1 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-e1168364413e` vincentvangoghbr00maut.txt —— 德语讹字率 0.0000（正形 705／讹形 0）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形，**不可做逐字引文**
- `corpus.unexamined-band`: **1/23 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
