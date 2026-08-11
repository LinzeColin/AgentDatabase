# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-blackstone-169/workspaces/william-blackstone/william-blackstone`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-11T05:50:18Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 15,
    "claims": 0
  },
  "sources_total": 15,
  "sources_train": 14,
  "sources_usable_train": 13,
  "sources_holdout": 1,
  "primary_sources": 11,
  "primary_ratio": 0.8462,
  "lane_source_counts": {
    "writings": 7,
    "conversations": 1,
    "expression": 2,
    "external": 2,
    "decisions": 2,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 12,
    "已证实归属": 6,
    "存疑（有正面证据但另有他人署名）": [
      "src-9a5ff4e9a5e6 reports_westminster_1781_en_vol1.txt [A-byline] 另有他人署名：by CE GATES EK"
    ],
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "5 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 15,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "印刷时代人物：扉页署名＋印工年份可用，但**单靠署名不够**——本人物的同名者中有 6 位的署名与目标字面不可分（4 位的名＋中名就是 `William Bla",
    "citation": "本工作区 `../../namesake-excluded.json` 与 `../../blackstone_namesake_candidates.json",
    "争议篇目数": 1,
    "P1 声称本人所著": 12,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 13,
    "分不开": 11,
    "★ 其中字面完全相同": 3,
    "未覆盖": [],
    "字面同名未定政策": [],
    "criteria": "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-blackstone-169/workspaces/william-blackstone/william-blackstone/namesake-criteria.json",
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-blackstone-169/blackstone_namesake_candidates.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 12,
    "靠 A-* 署名证据认定": 7,
    "靠 attribution_basis 逐份点名认定": 0,
    "**未被逐份认领**": 5,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 13,
    "fact 类条数": 0,
    "**人物事实**（计入）": 0,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "方法密度": "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过",
    "**未达**": [
      "可核 `fact` 断言 0 条 < 要求 5 条（13 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 15,
    "含同形字的源": 2,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "reports_westminster_1781_en_vol1.txt",
        "非拉丁字符": 5,
        "全同形字词": 1,
        "样例": [
          "νν 读作 vv",
          "rπ 读作 rπ",
          "νοs 读作 vos"
        ]
      },
      {
        "源": "reports_westminster_1781_en_vol2.txt",
        "非拉丁字符": 11,
        "全同形字词": 1,
        "样例": [
          "ο 读作 o",
          "οꝙ 读作 oꝙ",
          "αliament 读作 αliament"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "不可用": 8,
      "干净": 4,
      "未核": 3
    },
    "逐份": {
      "src-cef41ec3ad00": {
        "words": 34471,
        "diagnostic_est_eft": [
          0,
          3
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2267.1,
            "panel_good": 6,
            "panel_bad": 361,
            "若无语种门会读到": 0.9837,
            "verdict": "不可用",
            "rate": 0.9837,
            "reason": "英文讹字率 0.9837（正形 6／讹形 361）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9837,
        "reason": "英文讹字率 0.9837（正形 6／讹形 361）",
        "file": "EXT_furneaux_letters_to_blackstone_1770_en.txt"
      },
      "src-e7c18380b775": {
        "words": 99923,
        "diagnostic_est_eft": [
          0,
          4
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2271.5,
            "panel_good": 20,
            "panel_bad": 906,
            "若无语种门会读到": 0.9784,
            "verdict": "不可用",
            "rate": 0.9784,
            "reason": "英文讹字率 0.9784（正形 20／讹形 906）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9784,
        "reason": "英文讹字率 0.9784（正形 20／讹形 906）",
        "file": "EXT_interesting_appendix_priestley_1773_en.txt"
      },
      "src-bcf4065a0233": {
        "words": 62759,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2186.5,
            "panel_good": 11,
            "panel_bad": 913,
            "若无语种门会读到": 0.9881,
            "verdict": "不可用",
            "rate": 0.9881,
            "reason": "英文讹字率 0.9881（正形 11／讹形 913）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9881,
        "reason": "英文讹字率 0.9881（正形 11／讹形 913）",
        "file": "analysis_laws_england_1766_en.txt"
      },
      "src-5854111768a9": {
        "words": 377722,
        "diagnostic_est_eft": [
          61,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2258.7,
            "panel_good": 4685,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 4685／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 4685／讹形 0）",
        "file": "commentaries_bk1_1898_en.txt"
      },
      "src-7f12a15d6d46": {
        "words": 405386,
        "diagnostic_est_eft": [
          67,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2108.6,
            "panel_good": 5628,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 5628／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 5628／讹形 0）",
        "file": "commentaries_bk2_1898_en.txt"
      },
      "src-f7528e759247": {
        "words": 317377,
        "diagnostic_est_eft": [
          53,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2180.8,
            "panel_good": 4052,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 4052／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 4052／讹形 0）",
        "file": "commentaries_bk3_1898_en.txt"
      },
      "src-9525769f856e": {
        "words": 424749,
        "diagnostic_est_eft": [
          106,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1842.4,
            "panel_good": 4295,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 4295／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 4295／讹形 0）",
        "file": "commentaries_bk4_1898_en.txt"
      },
      "src-3e6b4b822d4f": {
        "words": 15801,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2006.2,
            "panel_good": 1,
            "panel_bad": 6,
            "若无语种门会读到": 0.8571,
            "verdict": "未核",
            "reason": "英文面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "discourse_study_of_law_1758_en.txt"
      },
      "src-1605220f591e": {
        "words": 54629,
        "diagnostic_est_eft": [
          1,
          11
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2058.8,
            "panel_good": 10,
            "panel_bad": 642,
            "若无语种门会读到": 0.9847,
            "verdict": "不可用",
            "rate": 0.9847,
            "reason": "英文讹字率 0.9847（正形 10／讹形 642）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9847,
        "reason": "英文讹字率 0.9847（正形 10／讹形 642）",
        "file": "law_tracts_1762_en_vol1.txt"
      },
      "src-435de4a6e51d": {
        "words": 58502,
        "diagnostic_est_eft": [
          0,
          35
        ],
        "逐语域": {
          "拉丁": {
            "语域": "拉丁",
            "anchors_per_10k": 53.8,
            "panel_good": 0,
            "panel_bad": 140,
            "若无语种门会读到": 1.0,
            "verdict": "不可用",
            "rate": 1.0,
            "reason": "拉丁讹字率 1.0000（正形 0／讹形 140）"
          },
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1011.6,
            "panel_good": 1,
            "panel_bad": 216,
            "若无语种门会读到": 0.9954,
            "verdict": "不可用",
            "rate": 0.9954,
            "reason": "英文讹字率 0.9954（正形 1／讹形 216）"
          }
        },
        "ae_连字": {
          "ae_per_1000": 0.46,
          "quae": 2,
          "que": 92,
          "quae_ratio": 0.021,
          "判读": "**打散**",
          "理由": "ae 0.46/千字母（门 3.5）、quae 占比 0.021（门 0.80）"
        },
        "verdict": "不可用",
        "rate": 1.0,
        "reason": "拉丁讹字率 1.0000（正形 0／讹形 140）　（两语域都适用，取更差的一侧）　★ **但 ae 连字被打散**（ae 0.46/千字母（门 3.5）、quae 占比 0.021（门 0.80））：`quae`→`que`、`haec`→`hee`，**逐字引用会印出作者没写的形**",
        "file": "law_tracts_1762_en_vol2.txt"
      },
      "src-80e44ce94930": {
        "words": 667,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1724.1,
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
        "file": "lawyers_farewell_to_his_muse_1763_en.txt"
      },
      "src-2c00f19a2df5": {
        "words": 3739,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2337.5,
            "panel_good": 2,
            "panel_bad": 36,
            "若无语种门会读到": 0.9474,
            "verdict": "不可用",
            "rate": 0.9474,
            "reason": "英文讹字率 0.9474（正形 2／讹形 36）"
          }
        },
        "verdict": "不可用",
        "rate": 0.9474,
        "reason": "英文讹字率 0.9474（正形 2／讹形 36）",
        "file": "reply_to_priestley_1773_en.txt"
      },
      "src-9a5ff4e9a5e6": {
        "words": 306941,
        "diagnostic_est_eft": [
          6,
          14
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1899.5,
            "panel_good": 20,
            "panel_bad": 72,
            "若无语种门会读到": 0.7826,
            "verdict": "不可用",
            "rate": 0.7826,
            "reason": "英文讹字率 0.7826（正形 20／讹形 72）"
          }
        },
        "verdict": "不可用",
        "rate": 0.7826,
        "reason": "英文讹字率 0.7826（正形 20／讹形 72）",
        "file": "reports_westminster_1781_en_vol1.txt"
      },
      "src-b9d9a74b4192": {
        "words": 288253,
        "diagnostic_est_eft": [
          1,
          13
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2031.0,
            "panel_good": 14,
            "panel_bad": 94,
            "若无语种门会读到": 0.8704,
            "verdict": "不可用",
            "rate": 0.8704,
            "reason": "英文讹字率 0.8704（正形 14／讹形 94）"
          }
        },
        "verdict": "不可用",
        "rate": 0.8704,
        "reason": "英文讹字率 0.8704（正形 14／讹形 94）",
        "file": "reports_westminster_1781_en_vol2.txt"
      },
      "src-e9e580101aaa": {
        "words": 3566,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1124.5,
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
        "file": "the_pantheon_a_vision_1747_en.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 15,
    "与台账不一致的道": [
      "02-conversations.md",
      "05-decisions.md",
      "03-expression.md",
      "04-external.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "核过 0 条，指错 0 条",
    "fraktur_mojibake": "✓ 没有花体乱码",
    "staged_not_ingested": "✓ 台账与工作区一致（或本人物没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "研究文档里**一条引文都没扫到**——没有可核的对象（不是通过）",
    "first_person_density": {
      "实质第一人称句": 1039,
      "密度/万字": 0.84,
      "正文字符": 12320945,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。",
      "⚠ 声口薄": "**0.84/万字（实质第一人称 1039 句）**——门量的是来源不是声口。`voice`/`trajectory`/`contrast` 这类要他谈自己的题很可能无据；出题前先看 `references/research/` 里有没有他开口说话的材料。★ 参照 Coffin #130：15 句 / 0.87，三道门全过而声口不够，已记延后。"
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
    "可用来源": 13,
    "**按内容去重后的作品数**": 12,
    "虚高": 1.083,
    "未声明的重复对": 0,
    "已声明的重复对": 1,
    "★ 本件看不见的份数（中日韩语料一律看不见，不是已核）": 0
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
    "**unknown 条数**": 13,
    "逐条": [
      "william-blackstone：目标本人 2　他人 0　**unknown 13**",
      "· src-cef41ec3ad00  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-e7c18380b775  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-bcf4065a0233  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-5854111768a9  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-7f12a15d6d46  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-f7528e759247  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-9525769f856e  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-3e6b4b822d4f  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-1605220f591e  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。"
    ],
    "口径": "**「说不准」不是通过。** 入库前逐条定夺，或给那份材料补一条能站住的区分符。"
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
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.002,
      "第三人称": 0.9507,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0473,
      "已标的份数": 13,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 2,
    "train 源总数": 15,
    "本人所著字节": 3354542,
    "train 总字节": 15021507,
    "own_voice_ratio": 0.2233,
    "★ 同名判据": {
      "按判据剔除的（他人）": [],
      "**说不准的（unknown，未计入本人声口）**": [
        "src-e7c18380b775",
        "src-bcf4065a0233",
        "src-5854111768a9",
        "src-7f12a15d6d46",
        "src-f7528e759247",
        "src-9525769f856e",
        "src-3e6b4b822d4f",
        "src-1605220f591e"
      ],
      "口径": "只比姓氏会把同姓近亲算进来。Sorby #133 的父亲也叫 Henry Sorby，父亲的日记同在馆藏里。**unknown 一律不计入——宁可低报，不可高报。**"
    },
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 13680797,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 3.68,
    "**立场句/万字**": 0.26,
    "其中不含第一人称的": 333,
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
    "状态": "**未核验**（不是通过）——没有可用的 --cache，取不到语料原文"
  },
  "semantic_residue": {
    "状态": "未启用（0 条订正全是非 content 域，取不到规则）——**不是通过**",
    "★": "全库回查：唯一有内容的订正是 Bessemer #132 的 2 条，scope 都是 `evaluation`。**这判据找的输入从来没出现过。**"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "拒答溢出条数": 0
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-blackstone-169/workspaces/william-blackstone/william-blackstone/evidence/source-ledger.jsonl",
    "一手份数": 11,
    "台账总份数": 13,
    "一手占比": 0.8462,
    "有材料的道数": 5,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 14,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-cef41ec3ad00 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 15,
    "声称公有领域": 15,
    "不声称（不判）": 0,
    "有据可查": 15,
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
    "台账行数": 15,
    "**`title` 就是文件名**": 0,
    "真书目题名": 15,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 15,
    "有一边没年份": 0,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  }
}
```

## Errors

- `structure.missing`: missing required file: evidence/claims.jsonl
- `research.source-unclaimed`: `src-7f12a15d6d46` commentaries_bk2_1898_en.txt —— 声称 `William Blackstone` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-3e6b4b822d4f` discourse_study_of_law_1758_en.txt —— 声称 `William Blackstone` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-80e44ce94930` lawyers_farewell_to_his_muse_1763_en.txt —— 声称 `William Blackstone` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-2c00f19a2df5` reply_to_priestley_1773_en.txt —— 声称 `William Blackstone` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.source-unclaimed`: `src-b9d9a74b4192` reports_westminster_1781_en_vol2.txt —— 声称 `William Blackstone` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []

## Warnings

- `corpus.longs-corruption`: **8 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-cef41ec3ad00` EXT_furneaux_letters_to_blackstone_1770_en.txt —— 英文讹字率 0.9837（正形 6／讹形 361），**不可做逐字引文**
- `corpus.namesake-unknown`: 同名归属说不准 13 条（**不是通过**）
