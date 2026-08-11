# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-holmes-170/workspaces/oliver-wendell-holmes-jr/oliver-wendell-holmes-jr`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-11T08:12:15Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 14,
    "claims": 0
  },
  "sources_total": 14,
  "sources_train": 13,
  "sources_usable_train": 13,
  "sources_holdout": 1,
  "primary_sources": 12,
  "primary_ratio": 0.9231,
  "lane_source_counts": {
    "writings": 2,
    "conversations": 4,
    "expression": 5,
    "external": 1,
    "decisions": 6,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 13,
    "已证实归属": 8,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "5 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 14,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "印刷时代人物，扉页署名＋印工年份可用，**但对这个人单靠署名远远不够**——**同名的是他父亲**（Oliver Wendell Holmes Sr., 180",
    "citation": "本工作区 `../../namesake-excluded.json` 与 `../../holmes_namesake_candidates.json`：23",
    "争议篇目数": 2,
    "P1 声称本人所著": 13,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 23,
    "分不开": 12,
    "★ 其中字面完全相同": 0,
    "靠 excluded_names": 7,
    "靠 unexcludable_names＋政策": 5,
    "未覆盖": [],
    "字面同名未定政策": [],
    "criteria": "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-holmes-170/workspaces/oliver-wendell-holmes-jr/oliver-wendell-holmes-jr/namesake-criteria.json",
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-holmes-170/holmes_namesake_candidates.json"
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
    "已查语料件": 14,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 13,
      "未核": 1
    },
    "逐份": {
      "src-6deab2cc96a0": {
        "words": 137128,
        "diagnostic_est_eft": [
          23,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2159.7,
            "panel_good": 1231,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1231／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1231／讹形 0）",
        "file": "common_law_1882_macmillan_en.txt"
      },
      "src-de206b40fe7b": {
        "words": 15074,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2237.0,
            "panel_good": 162,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 162／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 162／讹形 0）",
        "file": "speeches_1891_little_brown_en.txt"
      },
      "src-4c4e28b10d9c": {
        "words": 28507,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2241.6,
            "panel_good": 243,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 243／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 243／讹形 0）",
        "file": "speeches_1913_little_brown_en.txt"
      },
      "src-48135d4164bd": {
        "words": 88028,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2222.1,
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
        "file": "collected_legal_papers_1920_harcourt_en.txt"
      },
      "src-96246ca9968e": {
        "words": 4344,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1975.1,
            "panel_good": 57,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 57／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 57／讹形 0）",
        "file": "dead_yet_living_1884_keene_address_en.txt"
      },
      "src-c7a49bbb129f": {
        "words": 1900,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2336.8,
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
        "file": "speech_harvard_law_assoc_ny_1913_gpo_en.txt"
      },
      "src-4daf4f3927bc": {
        "words": 286149,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2540.9,
            "panel_good": 2700,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2700／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2700／讹形 0）",
        "file": "decisions_opinions_of_court_usreports_v187_214_en.txt"
      },
      "src-45190156b44a": {
        "words": 342091,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2525.4,
            "panel_good": 3184,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 3184／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 3184／讹形 0）",
        "file": "decisions_opinions_of_court_usreports_v215_247_en.txt"
      },
      "src-5f7df25e761f": {
        "words": 277585,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2534.4,
            "panel_good": 2543,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2543／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2543／讹形 0）",
        "file": "decisions_opinions_of_court_usreports_v248_281_en.txt"
      },
      "src-2bba40c2b8a4": {
        "words": 55085,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2324.2,
            "panel_good": 427,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 427／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 427／讹形 0）",
        "file": "decisions_dissents_concurrences_usreports_v187_281_en.txt"
      },
      "src-fbc3bb4680f2": {
        "words": 364942,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2445.2,
            "panel_good": 3310,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 3310／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 3310／讹形 0）",
        "file": "decisions_mass_sjc_associate_justice_1883_1891_en.txt"
      },
      "src-737ead5f32e1": {
        "words": 322186,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2463.2,
            "panel_good": 2562,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2562／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2562／讹形 0）",
        "file": "decisions_mass_sjc_associate_justice_1892_1899_en.txt"
      },
      "src-11c067343c4d": {
        "words": 243976,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2453.8,
            "panel_good": 2113,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2113／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2113／讹形 0）",
        "file": "decisions_mass_sjc_chief_justice_1899_1902_en.txt"
      },
      "src-8975bb29e982": {
        "words": 91614,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2366.7,
            "panel_good": 811,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 811／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 811／讹形 0）",
        "file": "dissenting_opinions_1929_vanguard_en.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 14,
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
      "实质第一人称句": 1769,
      "密度/万字": 1.59,
      "正文字符": 11132445,
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
    "可用来源": 13,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.625,
    "未声明的重复对": 8,
    "已声明的重复对": 0,
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
    "**unknown 条数**": 8,
    "逐条": [
      "oliver-wendell-holmes-jr：目标本人 6　他人 0　**unknown 8**",
      "· src-de206b40fe7b  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-4c4e28b10d9c  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-48135d4164bd  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-96246ca9968e  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-4daf4f3927bc  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-45190156b44a  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-5f7df25e761f  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。",
      "· src-2bba40c2b8a4  [unknown] 既没命中排除名单，也没命中任何区分符——**这不是通过，是没核**。人工定夺或补一条区分符。"
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
      "**第一人称字节占比**": 0.1348,
      "第三人称": 0.8652,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0,
      "已标的份数": 14,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 6,
    "train 源总数": 14,
    "本人所著字节": 7056475,
    "train 总字节": 13570713,
    "own_voice_ratio": 0.52,
    "★ 同名判据": {
      "按判据剔除的（他人）": [
        "src-de206b40fe7b：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-4c4e28b10d9c：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-48135d4164bd：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-96246ca9968e：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-4daf4f3927bc：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-45190156b44a：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-5f7df25e761f：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自",
        "src-2bba40c2b8a4：1841 < 1881 且只有「Oliver Wendell Holmes」这个署名——**父亲 1809–1894 自"
      ],
      "**说不准的（unknown，未计入本人声口）**": [],
      "口径": "只比姓氏会把同姓近亲算进来。Sorby #133 的父亲也叫 Henry Sorby，父亲的日记同在馆藏里。**unknown 一律不计入——宁可低报，不可高报。**"
    },
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 12864376,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 9.22,
    "**立场句/万字**": 0.31,
    "其中不含第一人称的": 331,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 13,
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-holmes-170/workspaces/oliver-wendell-holmes-jr/oliver-wendell-holmes-jr/evidence/source-ledger.jsonl",
    "一手份数": 12,
    "台账总份数": 13,
    "一手占比": 0.9231,
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
    "最优选法": "把 src-6deab2cc96a0 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 14,
    "声称公有领域": 14,
    "不声称（不判）": 0,
    "有据可查": 4,
    "有结论无依据": 10,
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
    "台账行数": 14,
    "**`title` 就是文件名**": 0,
    "真书目题名": 14,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 3,
    "跨PD分界": 0,
    "两边都有年份": 10,
    "有一边没年份": 4,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  }
}
```

## Errors

- `structure.missing`: missing required file: evidence/claims.jsonl
- `corpus.undeclared-duplicate-sources`: **8 对来源重叠 ≥0.3 而两边都没声明 `derived_from`**——台账上看不出它们是同一部作品。**清掉这条错的唯一办法是补 `derived_from`**——★ 本件只读 `derived_from`（`check_source_dedup.py` 第 182 行），**在 `counting_convention` 里写散文不会让它变绿**：那件判据当初正是因为「散文里写了、机器读得到的字段里没写」才建的。散文该写，但它是给人看的，不是给这道门看的。　[('speeches_1891_little_brown', 'speeches_1913_little_brown', 0.9429), ('speeches_1891_little_brown', 'collected_legal_papers_192', 0.311), ('speeches_1891_little_brown', 'dead_yet_living_1884_keene', 0.6873)]
- `research.lane-completion`: completed source-linked lanes 0 < profile minimum 3: []

## Warnings

- `corpus.namesake-unknown`: 同名归属说不准 8 条（**不是通过**）
