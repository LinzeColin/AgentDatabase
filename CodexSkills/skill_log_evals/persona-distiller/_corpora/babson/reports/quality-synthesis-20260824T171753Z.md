# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babson`
- Phase: `synthesis`
- Profile: `quick`
- Generated: `2026-08-24T17:17:53Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 17,
    "claims": 19
  },
  "sources_total": 17,
  "sources_train": 14,
  "sources_usable_train": 14,
  "sources_holdout": 3,
  "primary_sources": 14,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 9,
    "conversations": 0,
    "expression": 2,
    "external": 0,
    "decisions": 3,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 17,
    "已证实归属": 16,
    "存疑（有正面证据但另有他人署名）": [
      "src-49721f117be5 wbwilsonanddepa00babsgoog.txt [A-byline] 另有他人署名：By John Hays Hammond"
    ]
  },
  "corpus_integrity": {
    "已扫": 17,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Roger W. Babson（1875-1967）著作归属依据：① archive.org 目录 creator 字段（Babson, Roger W. / ",
    "citation": "archive.org 目录检索 creator:\"Babson, Roger W\"(numFound 16) + creator:\"Babson, Roger",
    "争议篇目数": 0,
    "P1 声称本人所著": 17,
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
    "usable_train": 14,
    "fact 类条数": 2,
    "**人物事实**（计入）": 2,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 1,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 1,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-bab1f3de3cc9 **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可核 `fact` 断言 2 条 < 要求 5 条（14 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因",
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 1 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 17,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 15,
      "未核": 2
    },
    "逐份": {
      "src-804503b37306": {
        "words": 103867,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2057.2,
            "panel_good": 1312,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1312／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1312／讹形 0）",
        "file": "bondsstockseleme00babs.txt"
      },
      "src-5d5edcec3c26": {
        "words": 93004,
        "diagnostic_est_eft": [
          5,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2009.1,
            "panel_good": 778,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 778／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 778／讹形 0）",
        "file": "businessbar00babs.txt"
      },
      "src-fce5969229e3": {
        "words": 26273,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2067.9,
            "panel_good": 196,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 196／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 196／讹形 0）",
        "file": "coxtheman00babs.txt"
      },
      "src-e3ca5f539a10": {
        "words": 9281,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2131.2,
            "panel_good": 116,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 116／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 116／讹形 0）",
        "file": "cu31924032459822.txt"
      },
      "src-a15abe41451f": {
        "words": 35549,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2016.1,
            "panel_good": 416,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 416／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 416／讹形 0）",
        "file": "enduringinvestme00babs.txt"
      },
      "src-06a4c0280f3d": {
        "words": 12041,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2104.5,
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
        "file": "fundamentalsofpr00babs.txt"
      },
      "src-a3099e89246a": {
        "words": 12801,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1968.6,
            "panel_good": 132,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 132／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 132／讹形 0）",
        "file": "futureofrailroad00babs.txt"
      },
      "src-ee7e9692aaf3": {
        "words": 109086,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2045.7,
            "panel_good": 972,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 972／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 972／讹形 0）",
        "file": "futureofsouthame01babs.txt"
      },
      "src-8fe78fbcd4b3": {
        "words": 9326,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2041.6,
            "panel_good": 145,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 145／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 145／讹形 0）",
        "file": "jstor-1011180.txt"
      },
      "src-e65abf55b47e": {
        "words": 3760,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1859.0,
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
        "file": "jstor-1011181.txt"
      },
      "src-55080b01fc0a": {
        "words": 1631,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2103.0,
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
        "file": "jstor-1814786.txt"
      },
      "src-8d6c1ba9f9d2": {
        "words": 60421,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2063.5,
            "panel_good": 698,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 698／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 698／讹形 0）",
        "file": "religionbusiness00babs.txt"
      },
      "src-49721f117be5": {
        "words": 75653,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2230.3,
            "panel_good": 796,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 796／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 796／讹形 0）",
        "file": "wbwilsonanddepa00babsgoog.txt"
      },
      "src-5c25345eaa86": {
        "words": 27043,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1878.1,
            "panel_good": 260,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 260／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 260／讹形 0）",
        "file": "whatissuccess00babs.txt"
      },
      "src-7f7930c5bcaa": {
        "words": 3473,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2061.6,
            "panel_good": 35,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 35／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 35／讹形 0）",
        "file": "jstor-20667504.txt"
      },
      "src-e8a7e154615a": {
        "words": 3328,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2136.4,
            "panel_good": 55,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 55／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 55／讹形 0）",
        "file": "jstor-2965047.txt"
      },
      "src-ca4e13110fb8": {
        "words": 2304,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2079.0,
            "panel_good": 28,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 28 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 28 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "jstor-29738396.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 17,
    "与台账不一致的道": [],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "核过 14 条，指错 0 条",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 14 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 40 条，切分后核验片段 37 个，未命中 8 个，长 s 还原后才命中 0 个｜⚠ 研究/01-writings.md: 「consists, there is no known law <!-- src-5d5edcec3c26 --> > Time, then, may be compared to space, an」｜⚠ 研究/01-writings.md: 「money, very few people make it a question for thought and study. <!-- src-804503b37306 --> （OCR 讹形：`」｜⚠ 研究/01-writings.md: 「To be efficient, education must develop character as well as intellect」｜⚠ 研究/02-conversations.md: 「Mr. Babson, I have only one use for wireless <!-- src-e8a7e154615a --> （此句跨页：`wireless` 后接 [版口：页眉 42」｜⚠ 研究/03-expression.md: 「consumed is considered <!-- src-8fe78fbcd4b3 --> - 方法断言——根本统计」｜⚠ 研究/05-decisions.md: 「preacher and statistician」",
    "first_person_density": {
      "实质第一人称句": 1352,
      "密度/万字": null,
      "正文字符": 6815247,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 78,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 3,
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
    "**按内容去重后的作品数**": 13,
    "虚高": 1.077,
    "未声明的重复对": 0,
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
        "引文数": 62,
        "核过": 62,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 5,
        "核过": 5,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 13,
        "核过": 13,
        "**对不上**": []
      },
      "04-external.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "05-decisions.md": {
        "引文数": 16,
        "核过": 16,
        "**对不上**": []
      },
      "06-timeline.md": {
        "引文数": 1,
        "核过": 1,
        "**对不上**": []
      }
    },
    "合计": "97 条引文，对不上 0 条",
    "读不到正文的来源": [
      "src-06a4c0280f3d",
      "src-e65abf55b47e",
      "src-5c25345eaa86"
    ],
    "holdout 源数": 0,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 17,
    "train 源总数": 17,
    "本人所著字节": 4079949,
    "train 总字节": 4079949,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 3708723,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 8.97,
    "**立场句/万字**": 0.42,
    "其中不含第一人称的": 130,
    "读不到正文的": [
      "src-06a4c0280f3d",
      "src-e65abf55b47e",
      "src-5c25345eaa86"
    ],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 17,
    "**疑似著录卡**": {},
    "读不到正文的": [
      "src-06a4c0280f3d",
      "src-e65abf55b47e",
      "src-5c25345eaa86"
    ],
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babson/evidence/source-ledger.jsonl",
    "一手份数": 14,
    "台账总份数": 14,
    "一手占比": 1.0,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 17,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-804503b37306 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 17,
    "声称公有领域": 0,
    "不声称（不判）": 17,
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
    "台账行数": 17,
    "**`title` 就是文件名**": 0,
    "真书目题名": 17,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 17,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 19,
  "claims_active": 19,
  "mental_models": 4,
  "heuristics": 3,
  "claim_markers": 19,
  "eval_cases": 0,
  "eval_suite_counts": {},
  "case_self_sufficiency": {
    "状态": "**没有用例可扫**——这不是通过"
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
    "断言条数": 19,
    "source_ids": "逐条各异（非空 19/19，不同取值 14）",
    "evidence_clusters": "逐条各异（非空 19/19，不同取值 19）",
    "counter_source_ids": "整批都空（非空 0/19，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 14,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 2,
    "作品组数（连通分量，仅供参考）": 16,
    "来源数": 17,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 59,
    "挂错作品": 1,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 58,
    "取不到正文的源": 0,
    "例": [
      "clm-bb965d7494c7：挂 ['bondsstockseleme00babs.txt', 'businessbar00babs.txt'] → 实 ['enduringinvestme00babs.txt', 'src-a15abe41451f/enduringinvestme00babs.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babson/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "   100.0%  cognitive-os.md        clm-afc425e4cbfe",
      "           **供给-需求框架是 Babson 判断具体证券与时局的通用工具——先列'决定价格的力量'再逐项判断**：1917 年《Security Prices and the War》…",
      "",
      "低于 10% 的 0 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babson/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/babson/audit/source-coverage.json），**未核验**（不是通过）"
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
  }
}
```

## Errors

- `eval.suite-minimum`: known cases 0 < 1
- `eval.suite-minimum`: boundary cases 0 < 1
- `eval.suite-minimum`: voice cases 0 < 1
- `eval.suite-minimum`: trajectory cases 0 < 1
- `eval.suite-minimum`: contrast cases 0 < 1
- `eval.suite-minimum`: fact-preservation cases 0 < 1
- `eval.suite-minimum`: style-decoy cases 0 < 1
- `eval.suite-minimum`: task-completion cases 0 < 1
- `eval.suite-minimum`: planning-fidelity cases 0 < 1
- `eval.suite-minimum`: tool-use cases 0 < 1
- `eval.suite-minimum`: capability-calibration cases 0 < 1
- `eval.suite-minimum`: refusal-stop cases 0 < 1
- `eval.suite-minimum`: long-horizon cases 0 < 1
- `eval.suite-minimum`: identity-routing cases 0 < 1
- `eval.suite-minimum`: anonymous-fidelity cases 0 < 1
- `eval.suite-minimum`: token-efficiency cases 0 < 1

## Warnings

- None
