# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-machiavelli-177/workspaces/niccolo-machiavelli`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T01:16:12Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 79,
    "claims": 27
  },
  "sources_total": 79,
  "sources_train": 69,
  "sources_usable_train": 68,
  "sources_holdout": 10,
  "primary_sources": 57,
  "primary_ratio": 0.8382,
  "lane_source_counts": {
    "writings": 53,
    "conversations": 3,
    "expression": 1,
    "external": 11,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 67,
    "已证实归属": 45,
    "存疑（有正面证据但另有他人署名）": [
      "src-c0544cf6ca89 discoursesonthef02machuoft.txt [A-byline] 另有他人署名：by LINDA VILLARI",
      "src-b117d884ad80 discoursesonthef03machuoft.txt [A-byline] 另有他人署名：by LINDA VILLARI"
    ],
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "20 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 79,
    "不是语料": 0,
    "可疑": 3,
    "可疑（只报不拦）": [
      "raw/bub_gb_EbbqmRdN78cC.txt　可读字符占比 34% < 55%——多半是二进制或彻底崩坏的 OCR",
      "raw/bub_gb_Ibk8AAAAYAAJ.txt　可读字符占比 34% < 55%——多半是二进制或彻底崩坏的 OCR",
      "raw/in.ernet.dli.2015.553355.txt　可读字符占比 53% < 55%——多半是二进制或彻底崩坏的 OCR"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "主干编本的题名页与编者序逐字（`src-ab73327e1fed`）：`OPERE COMPLETE DI NICCOLÒ MACHIAVELLI CON MO",
    "citation": "archive.org item（`src-ab73327e1fed` 的 locator 见 source-ledger）",
    "争议篇目数": 1,
    "P1 声称本人所著": 20,
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
    "usable_train": 69,
    "fact 类条数": 15,
    "**人物事实**（计入）": 15,
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
    "已查语料件": 79,
    "含同形字的源": 4,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "10602820bsb.txt",
        "非拉丁字符": 13,
        "全同形字词": 7,
        "样例": [
          "ο 读作 o",
          "ο 读作 o",
          "οο 读作 oo"
        ]
      },
      {
        "源": "bim_early-english-books-1641-1700_machivaels-discourses-_machiavelli-niccolo_1663.txt",
        "非拉丁字符": 6,
        "全同形字词": 0,
        "样例": [
          "οοj 读作 ooj",
          "ad¹νF 读作 ad¹vF",
          "πꝰπ¾hnn 读作 πꝰπ¾hnn"
        ]
      },
      {
        "源": "bim_early-english-books-1641-1700_machivaels-discourses-_machiavelli-niccolo_1663_0.txt",
        "非拉丁字符": 11,
        "全同形字词": 1,
        "样例": [
          "νν 读作 vv",
          "Mν 读作 Mv",
          "goο 读作 goo"
        ]
      },
      {
        "源": "bub_gb_EbbqmRdN78cC.txt",
        "非拉丁字符": 801861,
        "全同形字词": 0,
        "样例": [
          "ькиxъ 读作 ьkиxъ",
          "Iаш 读作 Iaш",
          "иосI 读作 иocI"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 16,
      "干净": 23,
      "不适用": 35,
      "未核": 5
    },
    "逐份": {
      "src-b55ae3897fc3": {
        "words": 94596,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 629.6,
            "panel_good": 102,
            "panel_bad": 671,
            "若无语种门会读到": 0.868,
            "verdict": "不可用",
            "rate": 0.868,
            "reason": "德语讹字率 0.8680（正形 102／讹形 671）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1936,
          "变音符每千词": 89.4,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.868,
        "reason": "德语讹字率 0.8680（正形 102／讹形 671）",
        "file": "10078626bsb.txt"
      },
      "src-4049f36a6764": {
        "words": 98568,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 648.9,
            "panel_good": 82,
            "panel_bad": 727,
            "若无语种门会读到": 0.8986,
            "verdict": "不可用",
            "rate": 0.8986,
            "reason": "德语讹字率 0.8986（正形 82／讹形 727）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2294,
          "变音符每千词": 90.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8986,
        "reason": "德语讹字率 0.8986（正形 82／讹形 727）",
        "file": "10078627bsb.txt"
      },
      "src-29668eaffa16": {
        "words": 21739,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 643.5,
            "panel_good": 622,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 622／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 541,
          "变音符每千词": 70.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 622／讹形 0）",
        "file": "10078631bsb.txt"
      },
      "src-f268293359ed": {
        "words": 134968,
        "diagnostic_est_eft": [
          16,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 641.0,
            "panel_good": 193,
            "panel_bad": 703,
            "若无语种门会读到": 0.7846,
            "verdict": "不可用",
            "rate": 0.7846,
            "reason": "德语讹字率 0.7846（正形 193／讹形 703）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2203,
          "变音符每千词": 94.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7846,
        "reason": "德语讹字率 0.7846（正形 193／讹形 703）",
        "file": "10602820bsb.txt"
      },
      "src-281a0059403d": {
        "words": 171494,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 663.0,
            "panel_good": 337,
            "panel_bad": 946,
            "若无语种门会读到": 0.7373,
            "verdict": "不可用",
            "rate": 0.7373,
            "reason": "德语讹字率 0.7373（正形 337／讹形 946）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3673,
          "变音符每千词": 89.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.7373,
        "reason": "德语讹字率 0.7373（正形 337／讹形 946）",
        "file": "10602821bsb.txt"
      },
      "src-03d0625a5881": {
        "words": 134324,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 624.8,
            "panel_good": 258,
            "panel_bad": 605,
            "若无语种门会读到": 0.701,
            "verdict": "不可用",
            "rate": 0.701,
            "reason": "德语讹字率 0.7010（正形 258／讹形 605）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2727,
          "变音符每千词": 82.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.701,
        "reason": "德语讹字率 0.7010（正形 258／讹形 605）",
        "file": "10602822bsb.txt"
      },
      "src-411f7d502510": {
        "words": 104507,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 611.5,
            "panel_good": 344,
            "panel_bad": 737,
            "若无语种门会读到": 0.6818,
            "verdict": "不可用",
            "rate": 0.6818,
            "reason": "德语讹字率 0.6818（正形 344／讹形 737）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 2193,
          "变音符每千词": 82.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6818,
        "reason": "德语讹字率 0.6818（正形 344／讹形 737）",
        "file": "10602824bsb.txt"
      },
      "src-547f91a924db": {
        "words": 63193,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 636.6,
            "panel_good": 112,
            "panel_bad": 524,
            "若无语种门会读到": 0.8239,
            "verdict": "不可用",
            "rate": 0.8239,
            "reason": "德语讹字率 0.8239（正形 112／讹形 524）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1215,
          "变音符每千词": 51.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.8239,
        "reason": "德语讹字率 0.8239（正形 112／讹形 524）",
        "file": "10769804bsb.txt"
      },
      "src-f5f9f13ea0f3": {
        "words": 55534,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 663.6,
            "panel_good": 61,
            "panel_bad": 130,
            "若无语种门会读到": 0.6806,
            "verdict": "不可用",
            "rate": 0.6806,
            "reason": "德语讹字率 0.6806（正形 61／讹形 130）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1105,
          "变音符每千词": 97.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.6806,
        "reason": "德语讹字率 0.6806（正形 61／讹形 130）",
        "file": "10769805bsb.txt"
      },
      "src-669314671026": {
        "words": 41538,
        "diagnostic_est_eft": [
          50,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.0<15.0，若强行读 0.0210；英文：锚 12.0<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.0833）",
        "file": "A1090181.txt"
      },
      "src-d9697c904daf": {
        "words": 106454,
        "diagnostic_est_eft": [
          21,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 6.9<15.0，若强行读 0.0109；英文：锚 7.7<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.0556）",
        "file": "BRes092067.txt"
      },
      "src-46247817a37a": {
        "words": 120996,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0145；英文：锚 10.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0294）",
        "file": "BRes092068.txt"
      },
      "src-077a5a6933d9": {
        "words": 127334,
        "diagnostic_est_eft": [
          17,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 2.0<15.0，若强行读 0.0060；英文：锚 6.0<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1053）",
        "file": "BRes092069.txt"
      },
      "src-d0aed8c13344": {
        "words": 98738,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.6<15.0，若强行读 0.0483；英文：锚 5.0<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1579）",
        "file": "BRes092070.txt"
      },
      "src-2e17f1173fb3": {
        "words": 157340,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 6.6<15.0，若强行读 0.0097；英文：锚 3.8<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.2632）",
        "file": "BRes092071.txt"
      },
      "src-25bb2005d7e9": {
        "words": 135587,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 4.7<15.0，若强行读 0.0099；英文：锚 3.8<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1786）",
        "file": "BRes092072.txt"
      },
      "src-1f1e1a06686f": {
        "words": 72495,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 2.3<15.0，若强行读 0.0085；英文：锚 4.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.2195）",
        "file": "BRes092073.txt"
      },
      "src-dda96083bec1": {
        "words": 3906,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1886.8,
            "panel_good": 0,
            "panel_bad": 38,
            "若无语种门会读到": 1.0,
            "verdict": "不可用",
            "rate": 1.0,
            "reason": "英文讹字率 1.0000（正形 0／讹形 38）"
          }
        },
        "verdict": "不可用",
        "rate": 1.0,
        "reason": "英文讹字率 1.0000（正形 0／讹形 38）",
        "file": "MarriageOfBelfagor.txt"
      },
      "src-ae7b06865247": {
        "words": 8845,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0370；英文：锚 4.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "TO01040218.txt"
      },
      "src-62a70771b546": {
        "words": 190493,
        "diagnostic_est_eft": [
          115,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1180.8,
            "panel_good": 601,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 601／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 601／讹形 0）",
        "file": "a591295400machuoft.txt"
      },
      "src-03a8b0f68c9e": {
        "words": 139996,
        "diagnostic_est_eft": [
          0,
          7
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1984.6,
            "panel_good": 6,
            "panel_bad": 1056,
            "若无语种门会读到": 0.9944,
            "verdict": "不可用",
            "rate": 0.9944,
            "reason": "英文讹字率 0.9944（正形 6／讹形 1056）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9944,
        "reason": "英文讹字率 0.9944（正形 6／讹形 1056）",
        "file": "b30335073.txt"
      },
      "src-1fe9f6e5a6f8": {
        "words": 3393,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1329.2,
            "panel_good": 0,
            "panel_bad": 1,
            "若无语种门会读到": 1.0,
            "verdict": "未核",
            "reason": "英文面板只命中 1 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 1 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_early-english-books-1641-1700_a-caveat-for-wives_machiavelli-niccolo_1660.txt"
      },
      "src-d0b80f15fd68": {
        "words": 12588,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2120.3,
            "panel_good": 0,
            "panel_bad": 7,
            "若无语种门会读到": 1.0,
            "verdict": "未核",
            "reason": "英文面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "bim_early-english-books-1641-1700_a-true-copy-of-a-letter-_machiavelli-niccol_1691.txt"
      },
      "src-4f4d806207d5": {
        "words": 220089,
        "diagnostic_est_eft": [
          0,
          5
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1954.5,
            "panel_good": 8,
            "panel_bad": 163,
            "若无语种门会读到": 0.9532,
            "verdict": "不可用",
            "rate": 0.9532,
            "reason": "英文讹字率 0.9532（正形 8／讹形 163）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9532,
        "reason": "英文讹字率 0.9532（正形 8／讹形 163）",
        "file": "bim_early-english-books-1641-1700_machiavels-discourses-u_machiavelli-niccolo_1674.txt"
      },
      "src-bd3e638d3612": {
        "words": 8017,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1959.6,
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
        "file": "bim_early-english-books-1641-1700_machiavels-vindication-_machiavelli-niccolo_1691.txt"
      },
      "src-85705eb7600a": {
        "words": 3226,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1580.9,
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
        "file": "bim_early-english-books-1641-1700_machiavils-advice-to-hi_machiavelli-niccolo_1681.txt"
      },
      "src-6c075ad39d35": {
        "words": 214938,
        "diagnostic_est_eft": [
          1,
          3
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1861.9,
            "panel_good": 9,
            "panel_bad": 56,
            "若无语种门会读到": 0.8615,
            "verdict": "不可用",
            "rate": 0.8615,
            "reason": "英文讹字率 0.8615（正形 9／讹形 56）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8615,
        "reason": "英文讹字率 0.8615（正形 9／讹形 56）",
        "file": "bim_early-english-books-1641-1700_machivaels-discourses-_machiavelli-niccolo_1663.txt"
      },
      "src-5deb53be8eb3": {
        "words": 102251,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1661.9,
            "panel_good": 4,
            "panel_bad": 34,
            "若无语种门会读到": 0.8947,
            "verdict": "不可用",
            "rate": 0.8947,
            "reason": "英文讹字率 0.8947（正形 4／讹形 34）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8947,
        "reason": "英文讹字率 0.8947（正形 4／讹形 34）",
        "file": "bim_early-english-books-1641-1700_machivaels-discourses-_machiavelli-niccolo_1663_0.txt"
      },
      "src-7daa94568cae": {
        "words": 178059,
        "diagnostic_est_eft": [
          2,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1816.3,
            "panel_good": 7,
            "panel_bad": 135,
            "若无语种门会读到": 0.9507,
            "verdict": "不可用",
            "rate": 0.9507,
            "reason": "英文讹字率 0.9507（正形 7／讹形 135）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9507,
        "reason": "英文讹字率 0.9507（正形 7／讹形 135）",
        "file": "bim_early-english-books-1641-1700_machivaels-discourses-_machiavelli-niccolo_1674.txt"
      },
      "src-ca55f85a835b": {
        "words": 234409,
        "diagnostic_est_eft": [
          0,
          5
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1572.7,
            "panel_good": 11,
            "panel_bad": 91,
            "若无语种门会读到": 0.8922,
            "verdict": "不可用",
            "rate": 0.8922,
            "reason": "英文讹字率 0.8922（正形 11／讹形 91）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8922,
        "reason": "英文讹字率 0.8922（正形 11／讹形 91）",
        "file": "bim_early-english-books-1641-1700_machivaels-discourses_machiavelli-niccolo_1663.txt"
      },
      "src-110e4fc80a93": {
        "words": 341,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "bub_gb_EbbqmRdN78cC.txt"
      },
      "src-ae6ca10912e9": {
        "words": 350,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "bub_gb_Ibk8AAAAYAAJ.txt"
      },
      "src-a2eb00fe307e": {
        "words": 150385,
        "diagnostic_est_eft": [
          1403,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.7<15.0，若强行读 0.0012；英文：锚 2.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1818）",
        "file": "bub_gb_OLtLAAAAcAAJ.txt"
      },
      "src-ab73327e1fed": {
        "words": 1060199,
        "diagnostic_est_eft": [
          32,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.9<15.0，若强行读 0.0134；英文：锚 6.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1117）",
        "file": "bub_gb_PTYaAQAAMAAJ.txt"
      },
      "src-5815e6dfa23d": {
        "words": 125425,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 7.0<15.0，若强行读 0.0057；英文：锚 3.6<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.0476）",
        "file": "bub_gb_dCVvnsDWyJ0C.txt"
      },
      "src-0fdb5af6a75f": {
        "words": 167930,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0330；英文：锚 8.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1404）",
        "file": "bub_gb_hepDAAAAYAAJ.txt"
      },
      "src-b8e175378823": {
        "words": 168803,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0414；英文：锚 9.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1321）",
        "file": "bub_gb_jzPjhqlQI24C.txt"
      },
      "src-644bdbe0ab36": {
        "words": 159689,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0415；英文：锚 9.5<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0976）",
        "file": "bub_gb_l2pd8wG-VCoC.txt"
      },
      "src-c05b43017052": {
        "words": 126664,
        "diagnostic_est_eft": [
          14,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.7<15.0，若强行读 0.0226；英文：锚 4.3<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0741）",
        "file": "bub_gb_sm_ojzpYQkAC.txt"
      },
      "src-7d02c9a9fdab": {
        "words": 156761,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 8.2<15.0，若强行读 0.0022；英文：锚 3.9<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.2347）",
        "file": "carteggiodisplom00mach.txt"
      },
      "src-657097138ae4": {
        "words": 135074,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 5.7<15.0，若强行读 0.0011；英文：锚 3.3<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1566）",
        "file": "carteggiodisplom2mach.txt"
      },
      "src-8e480ca71d4b": {
        "words": 71777,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 3.1<15.0，若强行读 0.0017；英文：锚 3.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1918）",
        "file": "carteggiodisplom3mach.txt"
      },
      "src-ebcce4239159": {
        "words": 66169,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.3<15.0，若强行读 0.0067；英文：锚 8.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1163）",
        "file": "commedie00mach.txt"
      },
      "src-989e18fd9ccd": {
        "words": 193455,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2595.8,
            "panel_good": 2077,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2077／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2077／讹形 0）",
        "file": "diplomaticwritin01machuoft.txt"
      },
      "src-a5798839b4de": {
        "words": 186960,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2407.8,
            "panel_good": 2591,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2591／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2591／讹形 0）",
        "file": "diplomaticwritin02machuoft.txt"
      },
      "src-54cdf1fe6f5c": {
        "words": 201186,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2438.0,
            "panel_good": 2421,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2421／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2421／讹形 0）",
        "file": "diplomaticwritin03machuoft.txt"
      },
      "src-97742d71c132": {
        "words": 184148,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2262.1,
            "panel_good": 1950,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1950／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1950／讹形 0）",
        "file": "diplomaticwritin04machuoft.txt"
      },
      "src-cb5329dc766f": {
        "words": 162224,
        "diagnostic_est_eft": [
          16,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.5<15.0，若强行读 0.0078；英文：锚 5.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0286）",
        "file": "discorsisullapri00machuoft.txt"
      },
      "src-c0544cf6ca89": {
        "words": 145501,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2219.8,
            "panel_good": 1985,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1985／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1985／讹形 0）",
        "file": "discoursesonthef02machuoft.txt"
      },
      "src-b117d884ad80": {
        "words": 145397,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2232.6,
            "panel_good": 1985,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1985／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1985／讹形 0）",
        "file": "discoursesonthef03machuoft.txt"
      },
      "src-58b7a687d396": {
        "words": 222416,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2389.5,
            "panel_good": 2242,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2242／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2242／讹形 0）",
        "file": "dli.bengal.10689.19369.txt"
      },
      "src-32e3db098783": {
        "words": 220933,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2425.6,
            "panel_good": 2207,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2207／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2207／讹形 0）",
        "file": "dli.ministry.02746.txt"
      },
      "src-28d09bc3bd8e": {
        "words": 33167,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2174.5,
            "panel_good": 513,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 513／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 513／讹形 0）",
        "file": "dli.ministry.05369.txt"
      },
      "src-8fc1ca17653a": {
        "words": 221008,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2446.9,
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
        "file": "dli.ministry.14051.txt"
      },
      "src-d5b51baa8b4c": {
        "words": 154301,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 9.7<15.0，若强行读 0.0125；英文：锚 8.6<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2288）",
        "file": "dli.ministry.16183.txt"
      },
      "src-b3a444c96490": {
        "words": 83963,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.8<15.0，若强行读 0.0308；英文：锚 7.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0370）",
        "file": "dli.ministry.18162.txt"
      },
      "src-1b36bba7f3aa": {
        "words": 66069,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0795；英文：锚 7.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0488）",
        "file": "dli.ministry.18163.txt"
      },
      "src-5041bd545dab": {
        "words": 70001,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.7<15.0，若强行读 0.0591；英文：锚 9.6<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.0000）",
        "file": "dli.ministry.18164.txt"
      },
      "src-e84bc7f2ee1b": {
        "words": 75962,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0755；英文：锚 11.2<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.1304）",
        "file": "dli.ministry.18165.txt"
      },
      "src-4007f9b9cb97": {
        "words": 166657,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2431.8,
            "panel_good": 1818,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1818／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1818／讹形 0）",
        "file": "florentinehistor00machuoft.txt"
      },
      "src-14995a470083": {
        "words": 86421,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2294.0,
            "panel_good": 890,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 890／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 890／讹形 0）",
        "file": "florentinehistor01machuoft.txt"
      },
      "src-4afb89c70e63": {
        "words": 181289,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 693.9,
            "panel_good": 181,
            "panel_bad": 4885,
            "若无语种门会读到": 0.9643,
            "verdict": "不可用",
            "rate": 0.9643,
            "reason": "德语讹字率 0.9643（正形 181／讹形 4885）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 3863,
          "变音符每千词": 79.8,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9643,
        "reason": "德语讹字率 0.9643（正形 181／讹形 4885）",
        "file": "florentinischege00mach.txt"
      },
      "src-213511a1f84a": {
        "verdict": "未核",
        "reason": "空文本",
        "words": 0,
        "file": "in.ernet.dli.2015.553355.txt"
      },
      "src-ee19b76b409e": {
        "words": 92161,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 3.7<15.0，若强行读 0.0564；英文：锚 15.3<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.0930）",
        "file": "india.history.resource.72474.txt"
      },
      "src-f7a27e5efcb6": {
        "words": 66774,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.2<15.0，若强行读 0.0234；英文：锚 19.2<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.1667）",
        "file": "india.history.resource.72475.txt"
      },
      "src-7f5e7ce5f0d1": {
        "words": 83136,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 1.7<15.0，若强行读 0.0254；英文：锚 14.7<500.0，若强行读 0.0000；德语：锚 0.6<15.0，若强行读 0.0690）",
        "file": "india.history.resource.72476.txt"
      },
      "src-a0499b626bab": {
        "words": 71817,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 2.1<15.0，若强行读 0.0276；英文：锚 17.8<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0698）",
        "file": "india.history.resource.72477.txt"
      },
      "src-f5fe91d951e6": {
        "words": 77471,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.8<15.0，若强行读 0.0152；英文：锚 13.9<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1385）",
        "file": "india.history.resource.72478.txt"
      },
      "src-4bf15fe30dbb": {
        "words": 118493,
        "diagnostic_est_eft": [
          11,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2060.4,
            "panel_good": 927,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 927／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 927／讹形 0）",
        "file": "india.history.resource.85209.txt"
      },
      "src-71d023632e39": {
        "words": 248418,
        "diagnostic_est_eft": [
          19,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2107.7,
            "panel_good": 2042,
            "panel_bad": 6,
            "若无语种门会读到": 0.0029,
            "verdict": "干净",
            "rate": 0.0029,
            "reason": "英文讹字率 0.0029（正形 2042／讹形 6）"
          }
        },
        "verdict": "干净",
        "rate": 0.0029,
        "reason": "英文讹字率 0.0029（正形 2042／讹形 6）",
        "file": "lifeandtimesnic00villgoog.txt"
      },
      "src-402c44d1a4a1": {
        "words": 124654,
        "diagnostic_est_eft": [
          14,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1644.1,
            "panel_good": 783,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 783／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 783／讹形 0）",
        "file": "niccolmachiavel00villgoog.txt"
      },
      "src-385f5ba4714f": {
        "words": 131279,
        "diagnostic_est_eft": [
          18,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2226.2,
            "panel_good": 1002,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1002／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1002／讹形 0）",
        "file": "niccolmachiavel01villgoog.txt"
      },
      "src-adc11f95eade": {
        "words": 123844,
        "diagnostic_est_eft": [
          9,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2205.4,
            "panel_good": 1094,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1094／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1094／讹形 0）",
        "file": "niccolmachiavel05villgoog.txt"
      },
      "src-6f8aba6067ce": {
        "words": 117499,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2018.4,
            "panel_good": 913,
            "panel_bad": 1,
            "若无语种门会读到": 0.0011,
            "verdict": "干净",
            "rate": 0.0011,
            "reason": "英文讹字率 0.0011（正形 913／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0011,
        "reason": "英文讹字率 0.0011（正形 913／讹形 1）",
        "file": "niccolmachiavel10villgoog.txt"
      },
      "src-28b88a9e7e14": {
        "words": 104860,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2152.0,
            "panel_good": 922,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 922／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 922／讹形 0）",
        "file": "niccolmachiavel12villgoog.txt"
      },
      "src-a64b55ffb644": {
        "words": 119300,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0197；英文：锚 13.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0526）",
        "file": "operediniccolm02mach.txt"
      },
      "src-c337cd6aef37": {
        "words": 40057,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.2<15.0，若强行读 0.0088；英文：锚 229.4<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.0588）",
        "file": "threeprosewriter00moor.txt"
      },
      "src-bd9990100dd4": {
        "words": 245952,
        "diagnostic_est_eft": [
          15,
          3
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2153.5,
            "panel_good": 2070,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2070／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2070／讹形 0）",
        "file": "villari-the-life-and-times-of-niccolo-machiavelli-v-1.txt"
      },
      "src-bf853d07951e": {
        "words": 261460,
        "diagnostic_est_eft": [
          79,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2098.7,
            "panel_good": 2034,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2034／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2034／讹形 0）",
        "file": "villari-the-life-and-times-of-niccolo-machiavelli-v-2.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 79,
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
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 19,
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
    "可用来源": 68,
    "**按内容去重后的作品数**": 52,
    "虚高": 1.308,
    "未声明的重复对": 23,
    "已声明的重复对": 1,
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
        "引文数": 3,
        "核过": 3,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "04-external.md": {
        "引文数": 3,
        "核过": 2,
        "**对不上**": [
          "extraction_status: failed"
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
    "合计": "11 条引文，对不上 1 条",
    "读不到正文的来源": [],
    "holdout 源数": 10,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 69,
    "train 源总数": 79,
    "本人所著字节": 58417492,
    "train 总字节": 72630935,
    "own_voice_ratio": 0.8043,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 19503683,
    "**判据说未核验的**": 43,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-b55ae3897fc3",
        "原因": "语种判为 **de**（en=0.000 de=0.129 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-4049f36a6764",
        "原因": "语种判为 **de**（en=0.000 de=0.122 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-29668eaffa16",
        "原因": "语种判为 **de**（en=0.000 de=0.129 fr=0.009）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-f268293359ed",
        "原因": "语种判为 **de**（en=0.000 de=0.132 fr=0.008）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-281a0059403d",
        "原因": "语种判为 **de**（en=0.000 de=0.138 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-03d0625a5881",
        "原因": "语种判为 **de**（en=0.000 de=0.115 fr=0.006）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-411f7d502510",
        "原因": "语种判为 **de**（en=0.000 de=0.113 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-547f91a924db",
        "原因": "语种判为 **de**（en=0.000 de=0.126 fr=0.007）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 8.23,
    "**立场句/万字**": 0.26,
    "其中不含第一人称的": 425,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 67,
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-machiavelli-177/workspaces/niccolo-machiavelli/evidence/source-ledger.jsonl",
    "一手份数": 57,
    "台账总份数": 68,
    "一手占比": 0.8382,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 78,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-b55ae3897fc3 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 79,
    "声称公有领域": 0,
    "不声称（不判）": 79,
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
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 79,
    "**`title` 就是文件名**": 1,
    "真书目题名": 78,
    "比例": 0.0127,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 1,
    "两边都有年份": 10,
    "有一边没年份": 69,
    "**逐条**": [
      {
        "source_id": "src-213511a1f84a",
        "文件名": "in.ernet.dli.2015.553355.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1892,
        "差": 123,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
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
  "claims_total": 27,
  "claims_active": 27,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 27,
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
    "断言条数": 27,
    "source_ids": "逐条各异（非空 27/27，不同取值 18）",
    "evidence_clusters": "逐条各异（非空 27/27，不同取值 25）",
    "counter_source_ids": "整批都空（非空 0/27，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 8,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 63,
    "来源数": 79,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 26,
    "挂错作品": 1,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 11,
    "取不到正文的源": 0,
    "例": [
      "clm-6303ab330421：挂 ['india.history.resource.72477.txt'] → 实 ['BRes092068.txt', 'bub_gb_PTYaAQAAMAAJ.txt', 'bub_gb_hepDAAAAYAAJ.txt', 'bub_gb_jzPjhqlQI24C.txt', 'bub_gb_l2pd8wG-VCoC.txt', 'bub_gb_sm_ojzpYQkAC.txt', 'diplomaticwritin01machuoft.txt', 'diplomaticwritin02machuoft.txt', 'discorsisullapri00machuoft.txt', 'dli.ministry.18163.txt', 'dli.ministry.18164.txt', 'florentinehistor00machuoft.txt', 'operediniccolm02mach.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-machiavelli-177/workspaces/niccolo-machiavelli/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-f93200963de8",
      "           **他的能动性模型：一半归命运，一半归自己，而这一半还要打个折。** `arbitra della metà … ma che ancora ella ne lasci gov…",
      "",
      "低于 10% 的 43 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-machiavelli-177/workspaces/niccolo-machiavelli/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-machiavelli-177/workspaces/niccolo-machiavelli/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8191,
  "baseline_overall": 0.5353,
  "candidate_baseline_delta": 0.2838,
  "suite_candidate_means": {
    "known": 0.575,
    "boundary": 0.7,
    "voice": 0.9,
    "trajectory": 0.725,
    "contrast": 0.55,
    "fact-preservation": 0.925,
    "style-decoy": 0.75,
    "task-completion": 0.95,
    "planning-fidelity": 0.75,
    "tool-use": 0.935,
    "capability-calibration": 0.905,
    "refusal-stop": 0.935,
    "long-horizon": 0.86,
    "identity-routing": 0.85,
    "anonymous-fidelity": 0.91,
    "token-efficiency": 0.885
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "**被单独一道题拖住**": [
      "fact-preservation　均分 0.9250 < 0.93　**被 nm-fact-preservation-01（0.900）一道拖住——去掉它 0.9500 ≥ 0.93**"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 18/27 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 9 未纳入）",
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

- `corpus.undeclared-duplicate-sources`: **23 对来源重叠 ≥0.3 而两边都没声明 `derived_from`**——台账上看不出它们是同一部作品。**清掉这条错有两条路**：① 补 `derived_from`（同一部作品的另一份扫本）；② 在 `meta.json` 的 `attribution_basis.counting_convention` 里**逐对点名**说明为什么它们该当两处证据（2026-08-17 起这条路真的通了——在那之前它只是句话，代码从没读过 `counting_convention`）——★★ 2026-08-17 订正：上面这几句原本写的是「本件只读 `derived_from`，在 `counting_convention` 里写散文不会让它变绿」——**那句当时是对的**，因为那条出路从没被实现。今天已实现，但**只认逐对点名**：约定文本里要同时出现这一对的两个文件名才算，泛泛的散文仍然不豁免任何一对。　[('BRes092070.txt', 'commedie00mach.txt', 0.3061), ('BRes092071.txt', 'carteggiodisplom00mach.txt', 0.6304), ('BRes092072.txt', 'carteggiodisplom2mach.txt', 0.5915)]

## Warnings

- `corpus.longs-corruption`: **16 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-b55ae3897fc3` 10078626bsb.txt —— 德语讹字率 0.8680（正形 102／讹形 671），**不可做逐字引文**
- `corpus.unexamined-band`: **3/79 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- research.lane_quotes：1 条逐字引文回原文对不上——**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区
- `corpus.title-is-just-the-filename`: **1/79 行的 `title` 就是文件名**（1%）——这个字段没有承载信息。后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**，引文坐标与「挂到哪部作品」也全落在文件名上。★ 与空值不同——**空值至少诚实，填成文件名的字段看起来是填过的**。
- `source.year-straddles-pd-cutoff`: **1 条的文件名年份与 `published_at` 跨过 PD 分界 1931** —— 这一类直接改变「这份源能不能用」，**必须逐份读题名页定案**，不要凭其中一个数下结论
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
