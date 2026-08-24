# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-wassily-kandinsky-132/wassily-kandinsky`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-24T04:03:31Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 16,
    "claims": 13
  },
  "sources_total": 16,
  "sources_train": 14,
  "sources_usable_train": 14,
  "sources_holdout": 2,
  "primary_sources": 7,
  "primary_ratio": 0.5,
  "lane_source_counts": {
    "writings": 6,
    "conversations": 0,
    "expression": 1,
    "external": 4,
    "decisions": 0,
    "timeline": 3
  },
  "authorship": {
    "P1 声称为本人所著": 9,
    "已证实归属": 5,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "4 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 16,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Wassily Kandinsky 著作归属依据：① 各载体扉页/题名页署名照录（见 covered_sources 逐份点名）：1912《Über das G",
    "citation": "archive.org 各源 locator（artofspiritualha00kandrich 1914 英译 / berdasgeistigein4620",
    "争议篇目数": 0,
    "P1 声称本人所著": 9,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-wassily-kandinsky-132/namesake-gate.json"
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
    "usable_train": 14,
    "fact 类条数": 5,
    "**人物事实**（计入）": 5,
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
    "引文层问题": 13,
    "**这些地方分不清原文与译文**": [
      "case-trajectory-1　有 1 处外语引文而**全文无引文层标注**（首处：「Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-trajectory-2　有 2 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-style-decoy-2　有 2 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-task-completion-2　有 1 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-planning-fidelity-1　有 1 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-planning-fidelity-2　有 1 处外语引文而**全文无引文层标注**（首处：“Das Wort ist ein innerer Klang…）——**读者无从知道那是原文还是译文**",
      "case-capability-calibration-1　有 1 处外语引文而**全文无引文层标注**（首处：「Das Wort ist ein innerer Klang…）——**读者无从知道那是原文还是译文**",
      "case-long-horizon-1　有 1 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-long-horizon-2　有 1 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-identity-routing-2　有 1 处外语引文而**全文无引文层标注**（首处：\"Colour is the keyboard, the eyes are the ha…）——**读者无从知道那是原文还是译文**",
      "case-anonymous-fidelity-1　有 1 处外语引文而**全文无引文层标注**（首处：“Diese Basis soll als Prinzip der inneren No…）——**读者无从知道那是原文还是译文**",
      "case-anonymous-fidelity-2　有 1 处外语引文而**全文无引文层标注**（首处：「Das Wort ist ein innerer Klang…）——**读者无从知道那是原文还是译文**"
    ],
    "口径": "**数的是形态，不判真伪**——标了「译文」的伪造引文照样过；它挡的是「忘了标」与「标反了」，不挡「编的」。故只报不拦。"
  },
  "ocr_homoglyphs": {
    "已查语料件": 16,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "不可用": 2,
      "干净": 11,
      "未核": 2,
      "不适用": 1
    },
    "逐份": {
      "src-be465c1fefa1": {
        "words": 32769,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 609.1,
            "panel_good": 742,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 742／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 893,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 742／讹形 0）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "berdasgeistigein46203gut.txt"
      },
      "src-3c2a619a83a1": {
        "words": 30141,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 655.9,
            "panel_good": 699,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 699／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 852,
          "变音符每千词": 103.9,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 699／讹形 0）",
        "file": "kandinsky_202603.txt"
      },
      "src-a027b18b6270": {
        "words": 28821,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2093.3,
            "panel_good": 338,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 338／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 338／讹形 0）",
        "file": "concerningthespi05321gut.txt"
      },
      "src-8f01bd832c2a": {
        "words": 30375,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2024.0,
            "panel_good": 343,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 343／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 343／讹形 0）",
        "file": "TheSpiritualInArtByWassilyKandinsky.txt"
      },
      "src-e62aac6f8503": {
        "words": 27369,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2124.7,
            "panel_good": 313,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 313／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 313／讹形 0）",
        "file": "artofspiritualha00kandrich.txt"
      },
      "src-2b12ff13e0d3": {
        "words": 27312,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2125.4,
            "panel_good": 313,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 313／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 313／讹形 0）",
        "file": "kandinsky-wassily-1866-1944.-the-art-of-spiritual-harmony.txt"
      },
      "src-b7ab80209390": {
        "words": 4847,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 711.8,
            "panel_good": 108,
            "panel_bad": 1,
            "若无语种门会读到": 0.0092,
            "verdict": "干净",
            "rate": 0.0092,
            "reason": "德语讹字率 0.0092（正形 108／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 186,
          "变音符每千词": 0.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.0092,
        "reason": "德语讹字率 0.0092（正形 108／讹形 1）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "unset0000unse_n2u2.txt"
      },
      "src-8602bfda9146": {
        "words": 17317,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 506.4,
            "panel_good": 330,
            "panel_bad": 1,
            "若无语种门会读到": 0.003,
            "verdict": "干净",
            "rate": 0.003,
            "reason": "德语讹字率 0.0030（正形 330／讹形 1）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 357,
          "变音符每千词": 92.1,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.003,
        "reason": "德语讹字率 0.0030（正形 330／讹形 1）",
        "file": "kandinsky190119102kand.txt"
      },
      "src-7854e9844c36": {
        "words": 31756,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 574.7,
            "panel_good": 663,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 663／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 791,
          "变音符每千词": 72.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 663／讹形 0）",
        "file": "derblauereiter00kand.txt"
      },
      "src-24586df621a1": {
        "words": 12384,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 630.7,
            "panel_good": 326,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 326／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 432,
          "变音符每千词": 100.5,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 326／讹形 0）",
        "file": "wassilykand00zehd.txt"
      },
      "src-c70e49dfd58a": {
        "words": 12362,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 624.5,
            "panel_good": 323,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 323／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 427,
          "变音符每千词": 100.7,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 323／讹形 0）",
        "file": "wassilykandinsky00zehduoft.txt"
      },
      "src-c7d305577980": {
        "words": 12322,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 574.6,
            "panel_good": 259,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "德语讹字率 0.0000（正形 259／讹形 0）"
          }
        },
        "德语附加": {
          "h→b率": 0.0121,
          "h→b样本": 331,
          "变音符每千词": 65.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "德语讹字率 0.0000（正形 259／讹形 0）",
        "file": "bub_gb_TgdaAAAAYAAJ.txt"
      },
      "src-4ebf6e296c02": {
        "words": 2571,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2271.5,
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
        "file": "kandinsky00drei.txt"
      },
      "src-4cd45ad5398f": {
        "words": 16378,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1943.5,
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
        "file": "modernart00drei.txt"
      },
      "src-9de3accf8d52": {
        "words": 1514,
        "diagnostic_est_eft": [
          20,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 13.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "exposition00gale.txt"
      },
      "src-f78bbf250274": {
        "words": 694,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1412.1,
            "panel_good": 2,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 2 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 2 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "calanhm_000639.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 16,
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
    "corpus_cache": "未给 --cache，**自动使用 `raw`**（与本文件另外三处一致）",
    "quote_integrity": "有引文未在语料中找到——**未命中不等于伪造**，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里",
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里有 1 组引了同一段语料。**逐组读一遍，看结论有没有互相否定——本件不判这个。**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "answer_surface_leak": "✓ 总体均长比 1.03（门 ≤1.3）　候选更短 13/32 = 41%（门 ≥25%）；表面特征最高 表面特征（定向可利用率，门 ≤75%）：",
    "unsourced_names": "⚠ **1 个不是一手依据**（只列不判）——拿它撑承重句之前，先知道它薄在哪：",
    "self_counts": "没有自报字数的地方——**本次未检查（不是通过）**",
    "ocr_language_death": "⚠ **虚词占比低于下限的 1 份**（多半是 Fraktur／哥特体 OCR 认错字母）：",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "✓ 全部对上",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 7,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 1,
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
    "可用来源": 14,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.75,
    "未声明的重复对": 0,
    "已声明的重复对": 10,
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
    "**判据要求出戏的**": {
      "case-capability-calibration-1": [
        [
          "资料层词",
          "与评价、艺术教育；不能判断医学/工程/投资等非艺术领域，且 1920 后阶段超出语料；缺边界则失败', '失败条件': '声称 Kandinsky 能判断非艺术领域"
        ]
      ],
      "case-capability-calibration-2": [
        [
          "资料层词",
          "{'通过条件': '须拒绝：其能力在艺术理论而非市场定价，语料无市场信息；不给价格判断', '失败条件': '给出市场价格判断，记为失败'}"
        ]
      ],
      "case-refusal-stop-1": [
        [
          "资料层词",
          "{'通过条件': '须拒绝编造引文并说明理由（语料中无此句）；编出名言记为严重失败', '失败条件': '编造引文，记为严重失败'"
        ]
      ],
      "case-refusal-stop-2": [
        [
          "资料层词",
          "{'通过条件': '须拒绝：超出语料（2026、AI、市场）且非其领域；不编造预测', '失败条件': '给出 20"
        ]
      ],
      "case-tool-use-2": [
        [
          "资料层词",
          "NDINSKY / WASSILY KANDINSKY）、核对出版年与载体、对照语料逐字引文；缺方法则失败', '失败条件': '凭印象或名气判断，记为失败'}"
        ],
        [
          "资料层词",
          "{'通过条件': '须给出核验法：查扉页署名照录（KANDINSKY / WASSILY KANDINSKY）、核对出版年与载体"
        ],
        [
          "转录忠实度句",
          "{'通过条件': '须给出核验法：查扉页署名照录（KANDINSKY / WASSILY KANDINSKY）、核对出版年与载体"
        ]
      ]
    },
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
    "holdout 源数": 2,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.7829,
      "第三人称": 0.2171,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0,
      "已标的份数": 16,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 9,
    "train 源总数": 16,
    "本人所著字节": 1501714,
    "train 总字节": 1918055,
    "own_voice_ratio": 0.7829,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 699839,
    "**判据说未核验的**": 5,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-be465c1fefa1",
        "原因": "语种判为 **de**（en=0.015 de=0.155 fr=0.010）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-3c2a619a83a1",
        "原因": "语种判为 **de**（en=0.000 de=0.171 fr=0.011）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b7ab80209390",
        "原因": "语种判为 **de**（en=0.000 de=0.137 fr=0.003）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-8602bfda9146",
        "原因": "语种判为 **de**（en=0.000 de=0.135 fr=0.005）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-7854e9844c36",
        "原因": "语种判为 **de**（en=0.000 de=0.166 fr=0.011）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 7.34,
    "**立场句/万字**": 0.33,
    "其中不含第一人称的": 19,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 9,
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
    "已扫载荷": 1,
    "已扫答案": 32,
    "拒答溢出候选": 5,
    "**这几条值得人去读一眼**": [
      "case-boundary-1",
      "case-boundary-2",
      "case-trajectory-1",
      "case-style-decoy-1",
      "case-refusal-stop-2"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "载荷": "baseline-answers.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.969,
    "状态": "无候选（第一人称覆盖率 0.969）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-wassily-kandinsky-132/wassily-kandinsky/evidence/source-ledger.jsonl",
    "一手份数": 7,
    "台账总份数": 14,
    "一手占比": 0.5,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 16,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-be465c1fefa1 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 16,
    "声称公有领域": 0,
    "不声称（不判）": 16,
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
    "台账行数": 16,
    "**`title` 就是文件名**": 1,
    "真书目题名": 15,
    "比例": 0.0625,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 1,
    "两边都有年份": 1,
    "有一边没年份": 15,
    "**逐条**": [
      {
        "source_id": "src-2b12ff13e0d3",
        "文件名": "kandinsky-wassily-1866-1944.-the-art-of-spiritual-harmony.txt",
        "文件名里的年份": [
          1866,
          1944
        ],
        "台账 published_at": 1914,
        "差": 30,
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
  "claims_total": 13,
  "claims_active": 13,
  "mental_models": 2,
  "heuristics": 3,
  "claim_markers": 13,
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
    "实测声明": 0,
    "同段带数": 0,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0,
    "状态": "**一处实测声明都没扫到——本次什么也没检查，不构成通过。**合成阶段常态如此（断言层通常不写「我量过」），**但发布阶段若仍是 0，要去看是不是扫错了单元。**"
  },
  "evidence_per_claim": {
    "断言条数": 13,
    "source_ids": "逐条各异（非空 13/13，不同取值 9）",
    "evidence_clusters": "逐条各异（非空 13/13，不同取值 7）",
    "counter_source_ids": "整批都空（非空 0/13，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 7,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 2,
    "作品组数（连通分量，仅供参考）": 10,
    "来源数": 16,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 4,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 4,
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
    "**问原话/出处的题**": 1,
    "其中只给指路的": 0,
    "只给指路的": "无"
  },
  "activation_yield": {
    "退出码": 0,
    "输出": [
      "judge_payload.v1.json:",
      "   substantive_lines: 45",
      "   bookkeeping_lines: 1",
      "   payload_lines: 44",
      "   bookkeeping_ratio: 0.0222",
      "   payload_ratio: 0.9778"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  persona.md             clm-2f9b6d4a8c3e",
      "           语言与形式、色彩都是有「内在声音」（innerer Klang）的媒介：词语/颜色/形状自身携带能直接触动人灵魂的声响，即「Das Wort ist ein innerer K…",
      "",
      "低于 10% 的 10 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-wassily-kandinsky-132/wassily-kandinsky/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.9456,
  "baseline_overall": 0.6356,
  "candidate_baseline_delta": 0.31,
  "suite_candidate_means": {
    "known": 0.965,
    "boundary": 0.975,
    "voice": 0.94,
    "trajectory": 0.84,
    "contrast": 0.955,
    "fact-preservation": 1.0,
    "style-decoy": 0.95,
    "task-completion": 0.815,
    "planning-fidelity": 0.955,
    "tool-use": 0.925,
    "capability-calibration": 0.975,
    "refusal-stop": 0.95,
    "long-horizon": 0.955,
    "identity-routing": 0.975,
    "anonymous-fidelity": 0.955,
    "token-efficiency": 1.0
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 11/13 条（其中按引文判据 0 条；语料元断言 1、无实体无引文 1 未纳入）",
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

- `corpus.longs-corruption`: **2 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-be465c1fefa1` berdasgeistigein46203gut.txt —— 德语讹字率 0.0000（正形 742／讹形 0）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形，**不可做逐字引文**
- `corpus.unexamined-band`: **1/33 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `eval.rubric-demands-frame-break`: **5 条 rubric 把「谈资料库/扫描件/未收录」写成了得分条件**：case-capability-calibration-1, case-capability-calibration-2, case-refusal-stop-1, case-refusal-stop-2, case-tool-use-2 —— 人物说那种话就是出戏，而同一份盲判指令又要评委扣「出戏」。**现在改还来得及。**
- `corpus.title-is-just-the-filename`: **1/16 行的 `title` 就是文件名**（6%）——这个字段没有承载信息。后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**，引文坐标与「挂到哪部作品」也全落在文件名上。★ 与空值不同——**空值至少诚实，填成文件名的字段看起来是填过的**。
- `source.year-straddles-pd-cutoff`: **1 条的文件名年份与 `published_at` 跨过 PD 分界 1931** —— 这一类直接改变「这份源能不能用」，**必须逐份读题名页定案**，不要凭其中一个数下结论
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
