# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say`
- Phase: `research`
- Profile: `standard`
- Generated: `2026-08-24T03:27:03Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 36,
    "claims": 0
  },
  "sources_total": 36,
  "sources_train": 36,
  "sources_usable_train": 36,
  "sources_holdout": 0,
  "primary_sources": 36,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 29,
    "conversations": 2,
    "expression": 5,
    "external": 0,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 36,
    "已证实归属": 16
  },
  "corpus_integrity": {
    "已扫": 36,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "P1 声称本人所著": 0,
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
    "usable_train": 36,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 8,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 8 条（36 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 36,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 11,
      "不适用": 24,
      "不可用": 1
    },
    "逐份": {
      "src-f7154d6be8dd": {
        "words": 27041,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2292.8,
            "panel_good": 305,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 305／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 305／讹形 0）",
        "file": "catechismofpolit00sayj.txt"
      },
      "src-fc0be68317ed": {
        "words": 46153,
        "diagnostic_est_eft": [
          52,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0014；英文：锚 7.2<500.0，若强行读 0.0000；德语：锚 8.0<15.0，若强行读 0.0000）",
        "file": "catecismodeecon00sayjguat.txt"
      },
      "src-8e84be5ae5f5": {
        "words": 186613,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 567.3,
            "panel_good": 5076,
            "panel_bad": 3,
            "若无语种门会读到": 0.0006,
            "verdict": "干净",
            "rate": 0.0006,
            "reason": "德语讹字率 0.0006（正形 5076／讹形 3）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 4434,
          "变音符每千词": 85.3,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0006,
        "reason": "德语讹字率 0.0006（正形 5076／讹形 3）",
        "file": "10388811bsb.txt"
      },
      "src-3a1ed9696c08": {
        "words": 70612,
        "diagnostic_est_eft": [
          86,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0019；英文：锚 11.6<500.0，若强行读 0.0000；德语：锚 0.3<15.0，若强行读 0.2000）",
        "file": "A086B229.txt"
      },
      "src-d9920ebbab87": {
        "words": 34468,
        "diagnostic_est_eft": [
          427,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0117；英文：锚 4.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.5000）",
        "file": "b29287571.txt"
      },
      "src-009703937aa9": {
        "words": 756728,
        "diagnostic_est_eft": [
          9165,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0037；英文：锚 3.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1545）",
        "file": "bub_gb_-ywuSOEQ5d4C.txt"
      },
      "src-38086fffdcd8": {
        "words": 117265,
        "diagnostic_est_eft": [
          1485,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0067；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.1818）",
        "file": "bub_gb_LWhDAAAAcAAJ.txt"
      },
      "src-003d387aca63": {
        "words": 131322,
        "diagnostic_est_eft": [
          1598,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0227；英文：锚 3.1<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.3529）",
        "file": "bub_gb_N7JDAAAAcAAJ.txt"
      },
      "src-3d29c2292d5f": {
        "words": 70651,
        "diagnostic_est_eft": [
          0,
          6
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 44.0,
            "panel_good": 35,
            "panel_bad": 521,
            "若无语种门会读到": 0.9371,
            "verdict": "不可用",
            "rate": 0.9371,
            "reason": "德语讹字率 0.9371（正形 35／讹形 521）"
          }
        },
        "德语附加": {
          "h→b率": 0.8972,
          "h→b样本": 107,
          "变音符每千词": 73.9,
          "h→b坏": true,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9371,
        "reason": "德语讹字率 0.9371（正形 35／讹形 521）　★ **长 s 之外还坏了**：**h→b 讹变 89.7%**（`nicht`→`nicbt` 这一族，样本 107）——逐字引用会印出作者没写的形",
        "file": "bub_gb_O5pWHnpsheIC.txt"
      },
      "src-8249fec8789a": {
        "words": 678478,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0038；英文：锚 2.2<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.0681）",
        "file": "bub_gb_nGt2dzHrtIMC.txt"
      },
      "src-ddb5cbd94f9a": {
        "words": 67682,
        "diagnostic_est_eft": [
          1053,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 1.6<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.3077）",
        "file": "catchismedc00sayj.txt"
      },
      "src-1695e00c1f47": {
        "words": 63102,
        "diagnostic_est_eft": [
          1013,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0029；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.1429）",
        "file": "catchismedco00sayj.txt"
      },
      "src-cb25bd63b578": {
        "words": 643917,
        "diagnostic_est_eft": [
          8052,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0006；英文：锚 2.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1333）",
        "file": "courscompletdc00sayjuoft.txt"
      },
      "src-9bb51732fd5f": {
        "words": 332553,
        "diagnostic_est_eft": [
          3964,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0106；英文：锚 5.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.3333）",
        "file": "courscompletdco00saygoog.txt"
      },
      "src-47295e407c17": {
        "words": 322793,
        "diagnostic_est_eft": [
          3945,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0025；英文：锚 4.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1818）",
        "file": "courscompletdco04saygoog.txt"
      },
      "src-68e157418b30": {
        "words": 130399,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 411.2,
            "panel_good": 2810,
            "panel_bad": 11,
            "若无语种门会读到": 0.0039,
            "verdict": "干净",
            "rate": 0.0039,
            "reason": "德语讹字率 0.0039（正形 2810／讹形 11）"
          }
        },
        "德语附加": {
          "h→b率": 0.0179,
          "h→b样本": 2295,
          "变音符每千词": 61.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0039,
        "reason": "德语讹字率 0.0039（正形 2810／讹形 11）",
        "file": "darstellungdern00morsgoog.txt"
      },
      "src-f211656b0b01": {
        "words": 145902,
        "diagnostic_est_eft": [
          2012,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0286；英文：锚 4.2<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.2273）",
        "file": "india.history.resource.18485.txt"
      },
      "src-b1935dc2cb56": {
        "words": 94188,
        "diagnostic_est_eft": [
          998,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0290；英文：锚 3.8<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.1667）",
        "file": "india.history.resource.35409.txt"
      },
      "src-70e2899cb9db": {
        "words": 100582,
        "diagnostic_est_eft": [
          1222,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0239；英文：锚 6.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "india.history.resource.35412.txt"
      },
      "src-8e646f31d617": {
        "words": 327862,
        "diagnostic_est_eft": [
          4083,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0025；英文：锚 3.1<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.0357）",
        "file": "ldpd_6416326_000.txt"
      },
      "src-0d7cfabc38d1": {
        "words": 56287,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2325.4,
            "panel_good": 602,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 602／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 602／讹形 0）",
        "file": "letterstomrmalth00sayjrich.txt"
      },
      "src-7309a76950f4": {
        "words": 26871,
        "diagnostic_est_eft": [
          248,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.0133；英文：锚 4.1<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.0000）",
        "file": "micro_IA40244320_0069.txt"
      },
      "src-4f99e70027da": {
        "words": 371204,
        "diagnostic_est_eft": [
          3899,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0079；英文：锚 5.7<500.0，若强行读 0.1176；德语：锚 0.1<15.0，若强行读 0.4118）",
        "file": "oeuvresdiverses00saygoog.txt"
      },
      "src-cfbc1f979683": {
        "words": 27940,
        "diagnostic_est_eft": [
          287,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 3.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2000）",
        "file": "olbieouessaisurl00sayj.txt"
      },
      "src-b68240fb3bd9": {
        "words": 27766,
        "diagnostic_est_eft": [
          499,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0058；英文：锚 1.8<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.1111）",
        "file": "petitvolumeconte00sayj.txt"
      },
      "src-faac5dffedc7": {
        "words": 118375,
        "diagnostic_est_eft": [
          1419,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0069；英文：锚 8.9<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.1250）",
        "file": "traitdconomiepo03saygoog.txt"
      },
      "src-9ac3add24ba1": {
        "words": 316291,
        "diagnostic_est_eft": [
          3984,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0089；英文：锚 4.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2308）",
        "file": "traitedeconomie00saygoog.txt"
      },
      "src-2a7d780d65ba": {
        "words": 318834,
        "diagnostic_est_eft": [
          4114,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0045；英文：锚 4.5<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.3200）",
        "file": "traitedeconomiep00sayj.txt"
      },
      "src-342c06541c14": {
        "words": 103128,
        "diagnostic_est_eft": [
          140,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0053；英文：锚 14.4<500.0，若强行读 0.0000；德语：锚 6.8<15.0，若强行读 0.0889）",
        "file": "tratadodeeconom01sayjguat.txt"
      },
      "src-a9248c41ada4": {
        "words": 258508,
        "diagnostic_est_eft": [
          15,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2449.1,
            "panel_good": 2049,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2049／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2049／讹形 0）",
        "file": "treatiseonpoliti00sayj.txt"
      },
      "src-726f3ed9e168": {
        "words": 259684,
        "diagnostic_est_eft": [
          14,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2450.3,
            "panel_good": 2045,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2045／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2045／讹形 0）",
        "file": "treatiseonpoliti00sayjiala.txt"
      },
      "src-47686e48abd4": {
        "words": 135493,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2414.4,
            "panel_good": 1008,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1008／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1008／讹形 0）",
        "file": "treatiseonpoliti01sayjuoft.txt"
      },
      "src-34cf10568209": {
        "words": 117716,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2442.2,
            "panel_good": 893,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 893／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 893／讹形 0）",
        "file": "treatiseonpoliti02sayjuoft.txt"
      },
      "src-e6e4188e3ffb": {
        "words": 264520,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2412.1,
            "panel_good": 2057,
            "panel_bad": 2,
            "若无语种门会读到": 0.001,
            "verdict": "干净",
            "rate": 0.001,
            "reason": "英文讹字率 0.0010（正形 2057／讹形 2）"
          }
        },
        "verdict": "干净",
        "rate": 0.001,
        "reason": "英文讹字率 0.0010（正形 2057／讹形 2）",
        "file": "treatiseonpoliti03sayj.txt"
      },
      "src-c6438e6532b8": {
        "words": 263610,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2434.7,
            "panel_good": 2072,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2072／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2072／讹形 0）",
        "file": "treatiseonpoliti04sayj.txt"
      },
      "src-fdc4d2520aaa": {
        "words": 255509,
        "diagnostic_est_eft": [
          13,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2432.6,
            "panel_good": 2004,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2004／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2004／讹形 0）",
        "file": "treatiseonpoliti05sayj.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 36,
    "与台账不一致的道": [
      "02-conversations.md",
      "03-expression.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "**未核（不是通过）**：判据没有给出「核过」计数（`attribution_basis.covered_sources` 为空——**未核（不是通过）**）",
    "fraktur_mojibake": "1 份",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档里**一条引文都没扫到**——没有可核的对象（不是通过）",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 81484812,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 0,
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
    "可用来源": 36,
    "**按内容去重后的作品数**": 17,
    "虚高": 2.118,
    "未声明的重复对": 38,
    "已声明的重复对": 0,
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
    "holdout 源数": 0,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 36,
    "train 源总数": 36,
    "本人所著字节": 47413251,
    "train 总字节": 47413251,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 11151942,
    "**判据说未核验的**": 27,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-fc0be68317ed",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.001）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8e84be5ae5f5",
        "原因": "语种判为 **de**（en=0.000 de=0.140 fr=0.009）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-3a1ed9696c08",
        "原因": "语种判为 **?**（en=0.000 de=0.000 fr=0.002）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-d9920ebbab87",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.102）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-009703937aa9",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.102）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-38086fffdcd8",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.098）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-003d387aca63",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.090）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-3d29c2292d5f",
        "原因": "语种判为 **?**（en=0.001 de=0.006 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 4.04,
    "**立场句/万字**": 0.09,
    "其中不含第一人称的": 98,
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
    "状态": "**没找到对照臂载荷——未核验，不是通过**（判分前应已有 `evals/baseline.v1.json`）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say/evidence/source-ledger.jsonl",
    "一手份数": 36,
    "台账总份数": 36,
    "一手占比": 1.0,
    "有材料的道数": 3,
    "standard 要的一手份数": 12,
    "够得着吗": "够不着：六条道只占 3 < 6——**空着的道抓再多别的也补不上**"
  },
  "corpus_feasibility": {
    "profile": "standard",
    "可用材料总数": 36,
    "min_sources": 24,
    "min_lanes": 6,
    "min_primary_ratio": 0.5,
    "★ 真实下限": 25,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": false,
    "结论": "needs-more-material",
    "还差": null,
    "拦路的": [
      "道数 3 < min_lanes 6（['conversations', 'expression', 'writings']）"
    ],
    "★ 说明": "**扣任何一份当 holdout 都过不了**——差的是材料，不是文字。"
  },
  "rights_basis": {
    "源条数": 36,
    "声称公有领域": 0,
    "不声称（不判）": 36,
    "有据可查": 0,
    "有结论无依据": 0,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": [],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 36,
    "**`title` 就是文件名**": 36,
    "真书目题名": 0,
    "比例": 1.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 36,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 2,
    "**硬失败**": 1,
    "其中·真重合": 0,
    "其中·无法判定": 1,
    "**逐条**": [
      "✗ 账本里没有 holdout —— 无法判定"
    ],
    "未核口径": "定位不到 holdout 的正文 ⇒ **这道门没能跑起来**，既不是「有重合」也不是「没重合」。语料正文不进 git，在没有语料缓存的机器上这是预期结果——给 `--cache <语料目录>` 才核得成。"
  }
}
```

## Errors

- `source.lane-coverage`: source metadata covers 3 lanes < profile minimum 6: ['writings', 'conversations', 'expression']
- `research.authorship-unproven`: src-fc0be68317ed catecismodeecon00sayjguat.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-8e84be5ae5f5 10388811bsb.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-3a1ed9696c08 A086B229.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-d9920ebbab87 b29287571.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-009703937aa9 bub_gb_-ywuSOEQ5d4C.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-38086fffdcd8 bub_gb_LWhDAAAAcAAJ.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-003d387aca63 bub_gb_N7JDAAAAcAAJ.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-3d29c2292d5f bub_gb_O5pWHnpsheIC.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-8249fec8789a bub_gb_nGt2dzHrtIMC.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-ddb5cbd94f9a catchismedc00sayj.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-1695e00c1f47 catchismedco00sayj.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-9bb51732fd5f courscompletdco00saygoog.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-68e157418b30 darstellungdern00morsgoog.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-b1935dc2cb56 india.history.resource.35409.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-70e2899cb9db india.history.resource.35412.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-8e646f31d617 ldpd_6416326_000.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-4f99e70027da oeuvresdiverses00saygoog.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-342c06541c14 tratadodeeconom01sayjguat.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-47686e48abd4 treatiseonpoliti01sayjuoft.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-e6e4188e3ffb treatiseonpoliti03sayj.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.attribution-basis`: historical 人物未声明 attribution_basis —— **必须写明靠什么证明这是他写的**。前印刷时代人物：A-byline 等五种署名证据结构上不存在，须另找权威（如作者自著目录）；印刷时代人物：扉页与印工可用，但**须写明哪些版次／托名件不算**
- `corpus.undeclared-duplicate-sources`: **38 对来源重叠 ≥0.3 而两边都没声明 `derived_from`**——台账上看不出它们是同一部作品。**清掉这条错有两条路**：① 补 `derived_from`（同一部作品的另一份扫本）；② 在 `meta.json` 的 `attribution_basis.counting_convention` 里**逐对点名**说明为什么它们该当两处证据（2026-08-17 起这条路真的通了——在那之前它只是句话，代码从没读过 `counting_convention`）——★★ 2026-08-17 订正：上面这几句原本写的是「本件只读 `derived_from`，在 `counting_convention` 里写散文不会让它变绿」——**那句当时是对的**，因为那条出路从没被实现。今天已实现，但**只认逐对点名**：约定文本里要同时出现这一对的两个文件名才算，泛泛的散文仍然不豁免任何一对。　[('catechismofpolit00sayj.txt', 'letterstomrmalth00sayjrich', 0.6156), ('b29287571.txt', 'bub_gb_-ywuSOEQ5d4C.txt', 0.3302), ('b29287571.txt', 'ldpd_6416326_000.txt', 0.3975)]
- `corpus.source-count-inflated-by-duplicates`: **`source.minimum` 只是被重份撑绿的**：可用来源 36 ≥ 门 24，而按内容去重后只有 **17 部作品**（虚高 2.118×）。**这道门量的是「有几个 source_id」，不是「有几处独立证据」。**
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 6: []
- `corpus.holdout-unverifiable`: holdout 与 train 的重合**未能核验**（1 条定位不到正文）——**未核不等于通过，也不等于有重合**；给 `--cache <语料目录>` 重跑。逐条见 metrics.holdout_overlap

## Warnings

- `corpus.longs-corruption`: **1 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-3d29c2292d5f` bub_gb_O5pWHnpsheIC.txt —— 德语讹字率 0.9371（正形 35／讹形 521）　★ **长 s 之外还坏了**：**h→b 讹变 89.7%**（`nicht`→`nicbt` 这一族，样本 107）——逐字引用会印出作者没写的形，**不可做逐字引文**
- `corpus.fraktur-mojibake`: **1 份德文语料是花体 OCR 乱码**——der→ber、und→unb、ist→ift，整篇没有一个词能拿去检索或引用。份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。
- `corpus.no-viable-holdout-split`: **扣任何一份当 holdout 都满足不了 profile 门**：道数 3 < min_lanes 6（['conversations', 'expression', 'writings']） —— 差的是材料，不是文字
- `corpus.title-is-just-the-filename`: **36/36 行的 `title` 就是文件名**（100%）——这个字段没有承载信息。后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**，引文坐标与「挂到哪部作品」也全落在文件名上。★ 与空值不同——**空值至少诚实，填成文件名的字段看起来是填过的**。
