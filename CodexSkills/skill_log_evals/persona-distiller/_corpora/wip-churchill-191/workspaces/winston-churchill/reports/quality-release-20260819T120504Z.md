# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill`
- Phase: `release`
- Profile: `standard`
- Generated: `2026-08-19T12:05:04Z`
- Result: **FAIL**

## Metrics

```json
{
  "profile_fallback": "★ **meta.json 里没有 `profile`**，本件按 **standard** 判（min_sources 24、min_lanes 6）。★★ 而 `check_corpus_feasibility.py` 对同一情形回退到 **quick**（min_sources 8、min_lanes 3）—— **两件判据会给出不同结论**，差的不是数据，是这个缺失字段。要定档就把 `profile` 写进 meta.json。",
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 21,
    "claims": 13
  },
  "sources_total": 21,
  "sources_train": 19,
  "sources_usable_train": 19,
  "sources_holdout": 2,
  "primary_sources": 15,
  "primary_ratio": 0.7895,
  "lane_source_counts": {
    "writings": 13,
    "conversations": 0,
    "expression": 0,
    "external": 4,
    "decisions": 0,
    "timeline": 2
  },
  "authorship": {
    "P1 声称为本人所著": 17,
    "已证实归属": 14,
    "存疑（有正面证据但另有他人署名）": [
      "src-934c9771e8e3 dli.ministry.04026.txt [A-byline] 另有他人署名：by G. F. SAVAGE ARMSTRONG"
    ]
  },
  "corpus_integrity": {
    "已扫": 21,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "(未声明)",
    "状态": "非 historical，本门只报不判（署名证据归 check_authorship.py）"
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
    "subject_origin": null,
    "状态": "**本门不适用**——免检口子只在 historical 路上存在，其他 subject_origin 由 check_authorship 的 A-* 证据路认定"
  },
  "fact_density": {
    "usable_train": 19,
    "fact 类条数": 6,
    "**人物事实**（计入）": 6,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 4,
    "**可复用做法**（计入）": 4,
    "复述式（不计入）": 0,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实"
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 21,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "in.ernet.dli.2015.206774.txt",
        "非拉丁字符": 4,
        "全同形字词": 2,
        "样例": [
          "а 读作 a",
          "а 读作 a"
        ]
      }
    ]
  },
  "longs_corruption": {
    "分布": {
      "干净": 21
    },
    "逐份": {
      "src-85285ec0b5d9": {
        "words": 121355,
        "diagnostic_est_eft": [
          8,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2147.7,
            "panel_good": 639,
            "panel_bad": 1,
            "若无语种门会读到": 0.0016,
            "verdict": "干净",
            "rate": 0.0016,
            "reason": "英文讹字率 0.0016（正形 639／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0016,
        "reason": "英文讹字率 0.0016（正形 639／讹形 1）",
        "file": "1914frenuoft.txt"
      },
      "src-075a1b0e47a6": {
        "words": 133421,
        "diagnostic_est_eft": [
          5,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2365.4,
            "panel_good": 654,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 654／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 654／讹形 0）",
        "file": "churchill_winston_1874_1965_river_war.txt"
      },
      "src-c53e1c37f040": {
        "words": 157387,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2238.0,
            "panel_good": 1185,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1185／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1185／讹形 0）",
        "file": "cu31924026407597.txt"
      },
      "src-934c9771e8e3": {
        "words": 104790,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2049.0,
            "panel_good": 568,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 568／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 568／讹形 0）",
        "file": "dli.ministry.04026.txt"
      },
      "src-0db9f607011e": {
        "words": 125759,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1940.4,
            "panel_good": 959,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 959／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 959／讹形 0）",
        "file": "dli.ministry.17592.txt"
      },
      "src-c9bbe07b2555": {
        "words": 129702,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2371.6,
            "panel_good": 1051,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1051／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1051／讹形 0）",
        "file": "greatspeechesofw00greyuoft.txt"
      },
      "src-1066d2415bd7": {
        "words": 46808,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2087.3,
            "panel_good": 277,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 277／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 277／讹形 0）",
        "file": "in.ernet.dli.2015.148729.txt"
      },
      "src-ca97b1037a22": {
        "words": 109018,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2246.4,
            "panel_good": 725,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 725／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 725／讹形 0）",
        "file": "in.ernet.dli.2015.206774.txt"
      },
      "src-d6dfa533902a": {
        "words": 91341,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2305.8,
            "panel_good": 636,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 636／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 636／讹形 0）",
        "file": "in.ernet.dli.2015.209887.txt"
      },
      "src-615074b71a84": {
        "words": 373736,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2260.1,
            "panel_good": 2494,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2494／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2494／讹形 1）",
        "file": "in.ernet.dli.2015.41900.txt"
      },
      "src-925ef102d33e": {
        "words": 123103,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2415.4,
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
        "file": "in.ernet.dli.2015.81282.txt"
      },
      "src-65f64bece1f1": {
        "words": 132338,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2225.0,
            "panel_good": 747,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 747／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 747／讹形 0）",
        "file": "in.ernet.dli.2015.81283.txt"
      },
      "src-3d7cfcb18b3a": {
        "words": 132840,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2228.8,
            "panel_good": 752,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 752／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 752／讹形 0）",
        "file": "india.history.resource.106285.txt"
      },
      "src-20956de1d83c": {
        "words": 148556,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2164.2,
            "panel_good": 1190,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1190／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1190／讹形 0）",
        "file": "lordrandolphchur0002chur.txt"
      },
      "src-6e3057d83176": {
        "words": 90001,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1947.6,
            "panel_good": 529,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 529／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 529／讹形 0）",
        "file": "marksykeshislife00lesluoft.txt"
      },
      "src-8ed06251e9a7": {
        "words": 127085,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1937.3,
            "panel_good": 969,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 969／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 969／讹形 0）",
        "file": "myearlyliferovin0000chur_b7k8.txt"
      },
      "src-4603171fd82d": {
        "words": 206386,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2229.8,
            "panel_good": 1562,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1562／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1562／讹形 0）",
        "file": "reportofproceed00macd.txt"
      },
      "src-0af00d0f0365": {
        "words": 63028,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2055.9,
            "panel_good": 720,
            "panel_bad": 3,
            "若无语种门会读到": 0.0041,
            "verdict": "干净",
            "rate": 0.0041,
            "reason": "英文讹字率 0.0041（正形 720／讹形 3）"
          }
        },
        "verdict": "干净",
        "rate": 0.0041,
        "reason": "英文讹字率 0.0041（正形 720／讹形 3）",
        "file": "savrolaatalerev00churgoog.txt"
      },
      "src-cd511a154ee0": {
        "words": 60418,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2104.8,
            "panel_good": 702,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 702／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 702／讹形 0）",
        "file": "savrolataleofrev0000chur.txt"
      },
      "src-122e7b521b7d": {
        "words": 108064,
        "diagnostic_est_eft": [
          6,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2256.3,
            "panel_good": 732,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 732／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 732／讹形 0）",
        "file": "worldcrisis0004unse.txt"
      },
      "src-0a5a49a4001e": {
        "words": 203952,
        "diagnostic_est_eft": [
          10,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2164.2,
            "panel_good": 1375,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1375／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1375／讹形 0）",
        "file": "worldcrisis00chur.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 21,
    "与台账不一致的道": [],
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
    "★ 没有 references/sources/": "**未核（不是通过）**"
  },
  "source_dedup": {
    "可用来源": 19,
    "**按内容去重后的作品数**": 12,
    "虚高": 1.583,
    "未声明的重复对": 0,
    "已声明的重复对": 4,
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
        "引文数": 4,
        "核过": 4,
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
        "引文数": 2,
        "核过": 2,
        "**对不上**": []
      },
      "05-decisions.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "06-timeline.md": {
        "引文数": 2,
        "核过": 2,
        "**对不上**": []
      }
    },
    "合计": "8 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 2,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 21,
    "train 源总数": 21,
    "本人所著字节": 18451945,
    "train 总字节": 18451945,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 14520977,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 13.39,
    "**立场句/万字**": 0.13,
    "其中不含第一人称的": 143,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 17,
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
    "状态": "未启用（本人物没有 corrections.jsonl）——**不是通过**"
  },
  "refusal_overflow": {
    "已扫载荷": 0,
    "已扫答案": 0,
    "拒答溢出候选": 0
  },
  "baseline_in_persona": {
    "载荷": "baseline_bare.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.469,
    "状态": "无候选（第一人称覆盖率 0.469）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill/evidence/source-ledger.jsonl",
    "一手份数": 15,
    "台账总份数": 19,
    "一手占比": 0.7895,
    "有材料的道数": 3,
    "standard 要的一手份数": 12,
    "够得着吗": "够不着：份数 19 < 24——**材料本身就不够**；六条道只占 3 < 6——**空着的道抓再多别的也补不上**"
  },
  "corpus_feasibility": {
    "profile": "standard",
    "可用材料总数": 21,
    "min_sources": 24,
    "min_lanes": 6,
    "min_primary_ratio": 0.5,
    "★ 真实下限": 25,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": false,
    "结论": "impossible-without-more-material",
    "还差": 4,
    "拦路的": [
      "可用材料总数 21 < **真实下限 25**（24 份 train + 至少 1 份 holdout）"
    ]
  },
  "rights_basis": {
    "源条数": 21,
    "声称公有领域": 0,
    "不声称（不判）": 21,
    "有据可查": 0,
    "有结论无依据": 0,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": [
    "writings",
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
    "台账行数": 21,
    "**`title` 就是文件名**": 0,
    "真书目题名": 21,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 1,
    "差一年": 0,
    "跨PD分界": 7,
    "两边都有年份": 8,
    "有一边没年份": 13,
    "**逐条**": [
      {
        "source_id": "src-075a1b0e47a6",
        "文件名": "churchill_winston_1874_1965_river_war.txt",
        "文件名里的年份": [
          1874,
          1965
        ],
        "台账 published_at": 1902,
        "差": 28,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-1066d2415bd7",
        "文件名": "in.ernet.dli.2015.148729.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1922,
        "差": 93,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-ca97b1037a22",
        "文件名": "in.ernet.dli.2015.206774.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1927,
        "差": 88,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-d6dfa533902a",
        "文件名": "in.ernet.dli.2015.209887.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1899,
        "差": 116,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-615074b71a84",
        "文件名": "in.ernet.dli.2015.41900.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1923,
        "差": 92,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-925ef102d33e",
        "文件名": "in.ernet.dli.2015.81282.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1899,
        "差": 116,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-65f64bece1f1",
        "文件名": "in.ernet.dli.2015.81283.txt",
        "文件名里的年份": [
          2015
        ],
        "台账 published_at": 1899,
        "差": 116,
        "★": "**跨 PD 分界（1931）**：一边 ≤1930 一边 ≥1931，这一条会直接改变「这份源能不能用」——**必须去读题名页定案**"
      },
      {
        "source_id": "src-85285ec0b5d9",
        "文件名": "1914frenuoft.txt",
        "文件名里的年份": [
          1914
        ],
        "台账 published_at": 1919,
        "差": 5
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
  "mental_models": 1,
  "heuristics": 0,
  "claim_markers": 13,
  "eval_cases": 32,
  "eval_suite_counts": {
    "known": 2,
    "fact-preservation": 2,
    "voice": 2,
    "boundary": 2,
    "capability-calibration": 2,
    "refusal-stop": 2,
    "contrast": 2,
    "identity-routing": 2,
    "style-decoy": 2,
    "task-completion": 2,
    "planning-fidelity": 2,
    "long-horizon": 2,
    "trajectory": 2,
    "tool-use": 2,
    "token-efficiency": 2,
    "anonymous-fidelity": 2
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
    "断言条数": 13,
    "source_ids": "逐条各异（非空 13/13，不同取值 7）",
    "evidence_clusters": "逐条各异（非空 13/13，不同取值 10）",
    "counter_source_ids": "整批都空（非空 0/13，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 0,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 14,
    "来源数": 21,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 9,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 4,
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  decision-policy.md     clm-c24f74807c7d",
      "           **转述别人给的细节时明写出处**：第一步给出细节，第二步紧跟一句「这一段我得自某人」。判据：句中出现 `I am indebted to` 这类致谢式归属——`To comm…",
      "",
      "低于 10% 的 24 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8862,
  "baseline_overall": 0.5537,
  "candidate_baseline_delta": 0.3325,
  "suite_candidate_means": {
    "known": 0.935,
    "fact-preservation": 0.96,
    "voice": 0.95,
    "boundary": 0.85,
    "capability-calibration": 0.95,
    "refusal-stop": 0.95,
    "contrast": 0.85,
    "identity-routing": 0.9,
    "style-decoy": 0.625,
    "task-completion": 0.95,
    "planning-fidelity": 0.95,
    "long-horizon": 0.75,
    "trajectory": 0.95,
    "tool-use": 0.935,
    "token-efficiency": 0.75,
    "anonymous-fidelity": 0.925
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 13/13 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 0 未纳入）",
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

- `structure.missing`: missing required file: README.md
- `structure.missing`: missing required file: identity-catalog.json
- `structure.missing`: missing required file: route-manifest.json
- `structure.missing`: missing required file: agents/openai.yaml
- `structure.missing`: missing required file: scripts/runtime_recorder.py
- `structure.missing`: missing required file: scripts/runtime_router.py
- `structure.missing`: missing required file: runtime/invocations.jsonl
- `structure.missing`: missing required file: corrections/corrections.jsonl
- `structure.missing`: missing required file: corrections/ACTIVE.md
- `route.invalid`: [Errno 2] No such file or directory: '/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill/route-manifest.json'
- `runtime.versioning-enabled`: target metadata must disable per-invocation versioning
- `model.placeholder`: strategy.md is not substantive enough for release
- `model.placeholder`: divergence-map.md is not substantive enough for release
- `identity.catalog-invalid`: [Errno 2] No such file or directory: '/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-churchill-191/workspaces/winston-churchill/identity-catalog.json'
- `source.minimum`: usable train sources 19 < profile minimum 24
- `source.lane-coverage`: source metadata covers 3 lanes < profile minimum 6: ['writings', 'external', 'timeline']
- `research.authorship-unproven`: src-ca97b1037a22 in.ernet.dli.2015.206774.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `research.authorship-unproven`: src-0a5a49a4001e worldcrisis00chur.txt｜文中他人署名：无 —— 账本声称本人所著，但文中查无归属证据（署名／编者注／逐字稿轮次三者皆无）
- `corpus.structurally-infeasible`: **这批材料在结构上走不完全程**：可用 21 份 < **真实下限 25**（24 份 train + 至少 1 份 holdout，因为 `min_sources` 只数 train 而合成阶段强制要有 holdout） —— **至少还要 4 份材料**；**再写多少文字都过不去**，现在停手比做完十份产物再撞上便宜
- `research.lane-completion`: completed source-linked lanes 3 < profile minimum 6: ['writings', 'external', 'timeline']
- `claim.model-minimum`: mental models 1 < 3
- `claim.heuristic-minimum`: heuristics 0 < 5
- `claim.insufficient-support`: clm-09e4178d7931 needs at least two supporting sources
- `claim.non-independent`: clm-09e4178d7931 needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-06eee64a36c9 needs at least two supporting sources
- `claim.insufficient-contexts`: clm-06eee64a36c9 needs at least two materially different contexts
- `claim.non-independent`: clm-06eee64a36c9 needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-2c049723c46c needs at least two supporting sources
- `claim.insufficient-contexts`: clm-2c049723c46c needs at least two materially different contexts
- `claim.non-independent`: clm-2c049723c46c needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-c24f74807c7d needs at least two supporting sources
- `claim.insufficient-contexts`: clm-c24f74807c7d needs at least two materially different contexts
- `claim.non-independent`: clm-c24f74807c7d needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-0d751356252d needs at least two supporting sources
- `claim.insufficient-contexts`: clm-0d751356252d needs at least two materially different contexts
- `claim.non-independent`: clm-0d751356252d needs at least two independent evidence clusters
- `claim.insufficient-support`: clm-efa05f1953a7 needs at least two supporting sources
- `claim.non-independent`: clm-efa05f1953a7 needs at least two independent evidence clusters
- `eval.judge-count`: wc-known-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-known-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-known-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-known-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-fact-preservation-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-fact-preservation-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-fact-preservation-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-fact-preservation-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-voice-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-voice-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-voice-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-voice-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-boundary-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-boundary-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-boundary-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-boundary-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-capability-calibration-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-capability-calibration-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-capability-calibration-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-capability-calibration-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-refusal-stop-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-refusal-stop-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-refusal-stop-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-refusal-stop-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-contrast-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-contrast-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-contrast-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-contrast-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-identity-routing-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-identity-routing-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-identity-routing-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-identity-routing-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-style-decoy-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-style-decoy-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-style-decoy-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-style-decoy-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-task-completion-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-task-completion-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-task-completion-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-task-completion-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-planning-fidelity-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-planning-fidelity-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-planning-fidelity-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-planning-fidelity-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-long-horizon-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-long-horizon-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-long-horizon-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-long-horizon-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-trajectory-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-trajectory-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-trajectory-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-trajectory-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-tool-use-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-tool-use-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-tool-use-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-tool-use-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-token-efficiency-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-token-efficiency-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-token-efficiency-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-token-efficiency-02/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-anonymous-fidelity-01/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-anonymous-fidelity-01/candidate has fewer than 2 independent judges
- `eval.judge-count`: wc-anonymous-fidelity-02/baseline has fewer than 2 independent judges
- `eval.judge-count`: wc-anonymous-fidelity-02/candidate has fewer than 2 independent judges

## Warnings

- `source.year-straddles-pd-cutoff`: **7 条的文件名年份与 `published_at` 跨过 PD 分界 1931** —— 这一类直接改变「这份源能不能用」，**必须逐份读题名页定案**，不要凭其中一个数下结论
- `source.filename-year-mismatch`: 1 条文件名年份与 `published_at` 差 ≥2 年 —— **至少有一处记错了**；判据不知道是哪一处
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
