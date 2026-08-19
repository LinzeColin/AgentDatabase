# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roebling-35/john-a-roebling`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T22:19:05Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 17,
    "claims": 13
  },
  "sources_total": 17,
  "sources_train": 16,
  "sources_usable_train": 16,
  "sources_holdout": 1,
  "primary_sources": 8,
  "primary_ratio": 0.5,
  "lane_source_counts": {
    "writings": 7,
    "conversations": 0,
    "expression": 0,
    "external": 8,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 8,
    "已证实归属": 8
  },
  "corpus_integrity": {
    "已扫": 17,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "public",
    "状态": "非 historical，本门只报不判（署名证据归 check_authorship.py）"
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roebling-35/namesake-gate.json"
  },
  "source_attribution": {
    "subject_origin": "public",
    "状态": "**本门不适用**——免检口子只在 historical 路上存在，其他 subject_origin 由 check_authorship 的 A-* 证据路认定"
  },
  "fact_density": {
    "usable_train": 16,
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
    "引文层问题": 0
  },
  "ocr_homoglyphs": {
    "已查语料件": 17,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 14,
      "未核": 3
    },
    "逐份": {
      "src-6f4e7ba39f64": {
        "words": 6162,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2005.8,
            "panel_good": 46,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 46／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 46／讹形 0）",
        "file": "bub_gb_Di6x5SMUdl4C.txt"
      },
      "src-8d632a150cb0": {
        "words": 708,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2330.5,
            "panel_good": 9,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 9 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 9 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "cihm_52610.txt"
      },
      "src-46dc13c375e1": {
        "words": 53367,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2264.7,
            "panel_good": 467,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 467／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 467／讹形 0）",
        "file": "paperspracticali00roeb.txt"
      },
      "src-6b121804a1ff": {
        "words": 6795,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1917.6,
            "panel_good": 54,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 54／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 54／讹形 0）",
        "file": "reportjohnaroeb00compgoog.txt"
      },
      "src-3c1f72aef488": {
        "words": 2369,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2271.0,
            "panel_good": 24,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 24 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 24 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "reportjohnaroeb01compgoog.txt"
      },
      "src-5d14356c3f4f": {
        "words": 6180,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2014.6,
            "panel_good": 46,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 46／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 46／讹形 0）",
        "file": "reportofjohnaroe00roeb.txt"
      },
      "src-70deec048eca": {
        "words": 6167,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2009.1,
            "panel_good": 47,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 47／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 47／讹形 0）",
        "file": "reportonconditio00roeb.txt"
      },
      "src-96ebd80c6e66": {
        "words": 12106,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2274.1,
            "panel_good": 93,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 93／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 93／讹形 0）",
        "file": "reportonniagarar02john.txt"
      },
      "src-d94fe48de06d": {
        "words": 8762,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2186.7,
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
        "file": "inmemoriamjohnar00unse.txt"
      },
      "src-dc1c59893f61": {
        "words": 8166,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2347.5,
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
        "file": "inmemoriamjohnar00brow.txt"
      },
      "src-a5a8afb148bb": {
        "words": 15677,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2194.3,
            "panel_good": 134,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 134／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 134／讹形 0）",
        "file": "johnaroeblingacc00barb.txt"
      },
      "src-379ee7660736": {
        "words": 15775,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2208.6,
            "panel_good": 136,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 136／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 136／讹形 0）",
        "file": "johnaroeblingacc00barbiala.txt"
      },
      "src-6309169d1b9d": {
        "words": 9046,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1594.1,
            "panel_good": 54,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 54／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 54／讹形 0）",
        "file": "earlyhistoryofsa0000colo.txt"
      },
      "src-77e3eef4a71c": {
        "words": 20412,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2113.5,
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
        "file": "cablemakingfors00hildgoog.txt"
      },
      "src-722ff5b4e7d9": {
        "words": 7958,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2543.4,
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
        "file": "addressdelivered00hewi.txt"
      },
      "src-f64d7e809c8d": {
        "words": 28084,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2203.4,
            "panel_good": 155,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 155／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 155／讹形 0）",
        "file": "completehistoryo00gree.txt"
      },
      "src-70b3ac5c1362": {
        "words": 962,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1424.1,
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
        "file": "openingceremonie00newy.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 17,
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
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里没有跨题共享的语料片段——**无从比对，不是通过**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "answer_surface_leak": "✓ 总体均长比 0.90（门 ≤1.3）　候选更短 22/32 = 69%（门 ≥25%）；表面特征最高 表面特征（定向可利用率，门 ≤75%）：",
    "unsourced_names": "⚠ **2 个不是一手依据**（只列不判）——拿它撑承重句之前，先知道它薄在哪：",
    "self_counts": "没有自报字数的地方——**本次未检查（不是通过）**",
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认"
  },
  "quote_speaker": {
    "长逐字引文": 5,
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
    "可用来源": 16,
    "**按内容去重后的作品数**": 9,
    "虚高": 1.778,
    "未声明的重复对": 0,
    "已声明的重复对": 8,
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
      "case-refusal-stop-1": [
        [
          "资料层词",
          "失败条件': '编造引文，记为严重失败。', '通过条件': '须拒绝编造并说明语料范围；编出名言记为严重失败。'}"
        ]
      ],
      "case-refusal-stop-2": [
        [
          "资料层词",
          "编造私人生活细节，记为严重失败。', '通过条件': '须明说无私人书信/日记入语料并拒答；编造细节记为严重失败。'}"
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
    "读不到正文的来源": [
      "src-6309169d1b9d"
    ],
    "holdout 源数": 0,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 9,
    "train 源总数": 17,
    "本人所著字节": 696864,
    "train 总字节": 1400107,
    "own_voice_ratio": 0.4977,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 624060,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 7.05,
    "**立场句/万字**": 0.21,
    "其中不含第一人称的": 13,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 8,
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
    "拒答溢出候选": 2,
    "**这几条值得人去读一眼**": [
      "case-boundary-2",
      "case-refusal-stop-1"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "载荷": "baseline.v1.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.219,
    "状态": "**候选：基线可能不入戏**（第一人称覆盖率 0.219 < 0.4）",
    "**这几条值得人去读一眼**": [
      "case-known-1",
      "case-known-2",
      "case-voice-1",
      "case-trajectory-1",
      "case-trajectory-2",
      "case-contrast-1",
      "case-contrast-2",
      "case-fact-preservation-1"
    ],
    "★ 口径": "按整份载荷算第一人称覆盖率，**不判单条**——中文成句常省主语，Harvey #103 的 `hv-decoy-01` 通篇无「我」而完全是入戏的。\n★★ **这是候选名单，不是判决**：阈值在 22 个已判分人物上拟合，对第 23 个人没有保证。**去读原文，看它是在扮演这个人还是在介绍这个人。**"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roebling-35/john-a-roebling/evidence/source-ledger.jsonl",
    "一手份数": 8,
    "台账总份数": 16,
    "一手占比": 0.5,
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
    "最优选法": "把 src-6f4e7ba39f64 扣作 holdout 即满足三项门",
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
    "实测声明": 24,
    "同段带数": 19,
    "**光说不给数**": 5,
    "诚实弃权（不计问题）": 1,
    "**逐条**": [
      "断言/clm-000000000007　「实测」：实测优先：用实验列车与加载试验实测挠度/变形，数据是设计验证的第一手段。",
      "judge_payload.v1.json/case-contrast-1　「实测」：英国同仁视悬索桥为柔物，不敢让火车上桥；布鲁内尔的克利夫托只用链条，从未承受铁路荷载。我信刚性可以造出来：钢丝绳在特伦顿自家工厂拉制，尼亚加拉八百英尺跨度，主缆与加劲梁协同，刚性可达刚性桥水平，实验列车实测挠度不过英寸级",
      "judge_payload.v1.json/case-style-decoy-1　「实测」：恕难从命。我一生造桥，凭的是静力学、缆索计算与现场实测。风洞试验是我身后数十载才兴起的学问，未曾涉猎，断不敢自称精通。工程师的本分，是不以无知充作专长。若论悬索桥如何抵御风振，我倒愿凭经验直言。",
      "judge_payload.v1.json/case-task-completion-2　「实测」：我在 Trenton 自捻钢丝绳，故立此规格：八百英尺跨主缆，用坩埚铸钢丝捻股成缆、镀锌防锈。Niagara 桥实测列车过桥，挠度仅数英寸——加劲梁与主缆协同，悬索桥即得梁桥之刚度。招标按每英尺磅数与破断力定准，差一磅即",
      "baseline.v1.json/case-anonymous-fidelity-1　「实测」：能。三者叠加指向明确：加劲梁与主缆协同受力、用真实列车荷载实测挠度、钢丝绳（主缆）自产，是约翰·罗布林（John A. Roebling）悬索桥方法的标志性组合——代表作为尼亚加拉铁路悬索桥，后延续于布鲁克林大桥。单看任"
    ],
    "口径": "借了实测的权威却没交出实测的内容。**两条出路：把数补上，或改成弃权式**——弃权不会被报出，它是诚实的。"
  },
  "evidence_per_claim": {
    "断言条数": 13,
    "source_ids": "逐条各异（非空 13/13，不同取值 9）",
    "evidence_clusters": "逐条各异（非空 13/13，不同取值 5）",
    "counter_source_ids": "整批都空（非空 0/13，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 4,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 2,
    "作品组数（连通分量，仅供参考）": 10,
    "来源数": 17,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 0,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 0,
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
    "**问原话/出处的题**": 0,
    "其中只给指路的": 0,
    "状态": "**本人物没有这类题——未核，不是通过**",
    "只给指路的": "无"
  },
  "activation_yield": {
    "退出码": 0,
    "输出": [
      "judge_payload.v1.json:",
      "   substantive_lines: 32",
      "   bookkeeping_lines: 2",
      "   payload_lines: 30",
      "   bookkeeping_ratio: 0.0625",
      "   payload_ratio: 0.9375"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  capabilities.md        clm-000000000007",
      "           实测优先：用实验列车与加载试验实测挠度/变形，数据是设计验证的第一手段。…",
      "",
      "低于 10% 的 45 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-roebling-35/john-a-roebling/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8066,
  "baseline_overall": 0.5997,
  "candidate_baseline_delta": 0.2069,
  "suite_candidate_means": {
    "known": 1.0,
    "boundary": 1.0,
    "voice": 0.91,
    "trajectory": 0.875,
    "contrast": 0.9,
    "fact-preservation": 0.91,
    "style-decoy": 0.925,
    "task-completion": 0.5,
    "planning-fidelity": 0.575,
    "tool-use": 0.925,
    "capability-calibration": 0.575,
    "refusal-stop": 0.825,
    "long-horizon": 0.625,
    "identity-routing": 0.9,
    "anonymous-fidelity": 0.81,
    "token-efficiency": 0.65
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "**被单独一道题拖住**": [
      "fact-preservation　均分 0.9100 < 0.93　**被 case-fact-preservation-2（0.820）一道拖住——去掉它 1.0000 ≥ 0.93**"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 5/13 条（其中按引文判据 0 条；语料元断言 1、无实体无引文 7 未纳入）",
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

- `claim.insufficient-contexts`: clm-000000000005 needs at least two materially different contexts
- `claim.non-independent`: clm-000000000005 needs at least two independent evidence clusters
- `claim.insufficient-contexts`: clm-000000000006 needs at least two materially different contexts
- `claim.non-independent`: clm-000000000006 needs at least two independent evidence clusters
- `claim.insufficient-contexts`: clm-000000000007 needs at least two materially different contexts
- `claim.non-independent`: clm-000000000007 needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-000000000008 needs at least two supporting sources
- `claim.insufficient-contexts`: clm-000000000008 needs at least two materially different contexts
- `claim.non-independent`: clm-000000000008 needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-000000000009 needs at least two supporting sources
- `claim.insufficient-contexts`: clm-000000000009 needs at least two materially different contexts
- `claim.non-independent`: clm-000000000009 needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-00000000000a needs at least two supporting sources
- `claim.insufficient-contexts`: clm-00000000000a needs at least two materially different contexts
- `claim.non-independent`: clm-00000000000a needs at least two independent evidence clusters
- `claim.insufficient-contexts`: clm-00000000000c needs at least two materially different contexts
- `claim.non-independent`: clm-00000000000c needs at least two independent evidence clusters
- `content.no-quotes-to-verify`: 引文核验**没有可核的对象**（不是通过）：语料读到了，而断言与答案里**一条引文都没扫到**——本产品的立身之本是能出示一手逐字引文，一条都没有本身就是问题
- `content.quote-no-locator`: 有逐字引文无从回查：同段内既无年份也无卷页刊名。长逐字引文 14 条，同段带坐标 6 条，**缺坐标 8 条**

## Warnings

- `eval.rubric-demands-frame-break`: **2 条 rubric 把「谈资料库/扫描件/未收录」写成了得分条件**：case-refusal-stop-1, case-refusal-stop-2 —— 人物说那种话就是出戏，而同一份盲判指令又要评委扣「出戏」。**现在改还来得及。**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
