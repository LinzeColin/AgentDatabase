# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-wassily-kandinsky-132/wassily-kandinsky`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-24T00:21:41Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 16,
    "claims": 0
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
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 5 条（14 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
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
      "03-expression.md",
      "04-external.md",
      "06-timeline.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "unexamined_band": {
      "n": 1,
      "of": 33,
      "files": [
        "tocka-i-linia-na-ploskosti.-o-duhovnom-v-iskusstve.ios.txt"
      ]
    },
    "byline_in_carrier": "核过 16 条，指错 0 条",
    "fraktur_mojibake": "✓ 没有花体乱码（德文 **6** 份逐份看过；共读到 15 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `wip-wassily-kandinsky-132`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档里**一条引文都没扫到**——没有可核的对象（不是通过）",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 4160800,
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
    "可用来源": 14,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.75,
    "未声明的重复对": 0,
    "已声明的重复对": 10,
    "★ 本件看不见的份数（文本太短／中日韩，不是已核）": 0
  },
  "material_split": {
    "返回码": 2,
    "**holdout 泄漏处**": 4,
    "**逐条**": [
      "✗✗ holdout 正文出现在此：src-7854e9844c36  ← 隔离失效，本轮 known 分数不可信",
      "✗✗ holdout 正文出现在此：src-b7ab80209390  ← 隔离失效，本轮 known 分数不可信",
      "✗✗ holdout 正文出现在此：src-7854e9844c36  ← 隔离失效，本轮 known 分数不可信",
      "✗✗ holdout 正文出现在此：src-b7ab80209390  ← 隔离失效，本轮 known 分数不可信"
    ],
    "口径": "同一个 source_id 的正文同时在 train 与 holdout 目录里——**隔离失效，本轮 known 分数不可信**。正解是把 holdout 的正文从 train 目录移走，不是调判据。"
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
    "已扫载荷": 0,
    "已扫答案": 0,
    "拒答溢出候选": 0
  },
  "baseline_in_persona": {
    "状态": "**没找到对照臂载荷——未核验，不是通过**（判分前应已有 `evals/baseline.v1.json`）"
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
  "research_lanes_complete": [],
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
  }
}
```

## Errors

- corpus.holdout-leak: 4 处（隔离失效）
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []

## Warnings

- `corpus.longs-corruption`: **2 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-be465c1fefa1` berdasgeistigein46203gut.txt —— 德语讹字率 0.0000（正形 742／讹形 0）　★ **长 s 之外还坏了**：**变音符湮灭**（0.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形，**不可做逐字引文**
- `corpus.unexamined-band`: **1/33 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- `corpus.title-is-just-the-filename`: **1/16 行的 `title` 就是文件名**（6%）——这个字段没有承载信息。后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**，引文坐标与「挂到哪部作品」也全落在文件名上。★ 与空值不同——**空值至少诚实，填成文件名的字段看起来是填过的**。
- `source.year-straddles-pd-cutoff`: **1 条的文件名年份与 `published_at` 跨过 PD 分界 1931** —— 这一类直接改变「这份源能不能用」，**必须逐份读题名页定案**，不要凭其中一个数下结论
