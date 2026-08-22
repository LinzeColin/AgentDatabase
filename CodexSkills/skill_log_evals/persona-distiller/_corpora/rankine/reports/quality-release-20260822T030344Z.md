# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/rankine`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-22T03:03:44Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 9,
    "claims": 31
  },
  "sources_total": 9,
  "sources_train": 8,
  "sources_usable_train": 8,
  "sources_holdout": 1,
  "primary_sources": 8,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 6,
    "conversations": 1,
    "expression": 1,
    "external": 0,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 9,
    "已证实归属": 8,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "1 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 9,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "William John Macquorn Rankine 著作归属依据：① Glasgow 大学自然哲学教授（1855-1872），四部经典手册《A Manu",
    "citation": "archive.org 目录 creator 字段 + 各书题名页/署名行；出版记录见各源 locator。",
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
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/rankine/namesake-candidates.json"
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
    "usable_train": 8,
    "fact 类条数": 6,
    "**人物事实**（计入）": 6,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 4,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 4,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-000000000014 **连步骤都没有**：是一句概括不是一套做法",
      "clm-000000000015 **连步骤都没有**：是一句概括不是一套做法",
      "clm-000000000016 **连步骤都没有**：是一句概括不是一套做法",
      "clm-000000000017 **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 4 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 1,
    "引文层问题": 32,
    "**这些地方分不清原文与译文**": [
      "case-known-1　有 1 处外语引文而**全文无引文层标注**（首处：「should not, at any point, make with the nor…）——**读者无从知道那是原文还是译文**",
      "case-known-2　有 1 处外语引文而**全文无引文层标注**（首处：「the thermodynamic relations between heat…）——**读者无从知道那是原文还是译文**",
      "case-boundary-1　有 1 处外语引文而**全文无引文层标注**（首处：「theoretical limit of the strength or stabil…）——**读者无从知道那是原文还是译文**",
      "case-boundary-2　有 1 处外语引文而**全文无引文层标注**（首处：「Mechanics is the science of rest, motion, a…）——**读者无从知道那是原文还是译文**",
      "case-voice-1　有 3 处外语引文而**全文无引文层标注**（首处：「compute the theoretical limit of the streng…）——**读者无从知道那是原文还是译文**",
      "case-voice-2　有 2 处外语引文而**全文无引文层标注**（首处：「the Theory of Motion before that of Force…）——**读者无从知道那是原文还是译文**",
      "case-trajectory-1　有 1 处外语引文而**全文无引文层标注**（首处：「My blessing on old George Stephenson…）——**读者无从知道那是原文还是译文**",
      "case-trajectory-2　有 1 处外语引文而**全文无引文层标注**（首处：「for the instruction of students in engineer…）——**读者无从知道那是原文还是译文**",
      "case-contrast-1　有 2 处外语引文而**全文无引文层标注**（首处：「looked upon merely as natural bodies are…）——**读者无从知道那是原文还是译文**",
      "case-contrast-2　有 2 处外语引文而**全文无引文层标注**（首处：「that scientifically practical skill which p…）——**读者无从知道那是原文还是译文**",
      "case-fact-preservation-1　有 2 处外语引文而**全文无引文层标注**（首处：「make with the normal to that plane an angle…）——**读者无从知道那是原文还是译文**",
      "case-fact-preservation-2　有 1 处外语引文而**全文无引文层标注**（首处：「for the instruction of students in engineer…）——**读者无从知道那是原文还是译文**"
    ],
    "口径": "**数的是形态，不判真伪**——标了「译文」的伪造引文照样过；它挡的是「忘了标」与「标反了」，不挡「编的」。故只报不拦。"
  },
  "ocr_homoglyphs": {
    "已查语料件": 9,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 8,
      "未核": 1
    },
    "逐份": {
      "src-2797b40bd6e6": {
        "words": 214117,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2372.7,
            "panel_good": 1500,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1500／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1500／讹形 0）",
        "file": "amanualappliedm05rankgoog.txt"
      },
      "src-9d1c303213ab": {
        "words": 188655,
        "diagnostic_est_eft": [
          3,
          3
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1835.0,
            "panel_good": 565,
            "panel_bad": 1,
            "若无语种门会读到": 0.0018,
            "verdict": "干净",
            "rate": 0.0018,
            "reason": "英文讹字率 0.0018（正形 565／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0018,
        "reason": "英文讹字率 0.0018（正形 565／讹形 1）",
        "file": "amanualsteameng00rankgoog.txt"
      },
      "src-2dd1b7bdeab3": {
        "words": 253682,
        "diagnostic_est_eft": [
          0,
          2
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2430.4,
            "panel_good": 1798,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1798／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1798／讹形 0）",
        "file": "amanualmachiner00rankgoog.txt"
      },
      "src-b538bc0041f9": {
        "words": 124517,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2409.2,
            "panel_good": 933,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 933／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 933／讹形 0）",
        "file": "miscellaneoussc00taitgoog.txt"
      },
      "src-8c98ae4f3261": {
        "words": 11860,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2001.7,
            "panel_good": 88,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 88／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 88／讹形 0）",
        "file": "songsandfablesil00rankuoft.txt"
      },
      "src-40bd7f7d80fc": {
        "words": 17553,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2487.9,
            "panel_good": 148,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 148／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 148／讹形 0）",
        "file": "memoirofjohnelde00rankiala.txt"
      },
      "src-39603f010859": {
        "words": 117534,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2561.6,
            "panel_good": 898,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 898／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 898／讹形 0）",
        "file": "mechanicaltextbo00rankrich.txt"
      },
      "src-00aa2c4da15f": {
        "words": 312861,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2350.4,
            "panel_good": 2261,
            "panel_bad": 1,
            "若无语种门会读到": 0.0004,
            "verdict": "干净",
            "rate": 0.0004,
            "reason": "英文讹字率 0.0004（正形 2261／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0004,
        "reason": "英文讹字率 0.0004（正形 2261／讹形 1）",
        "file": "amanualcivileng01rankgoog.txt"
      },
      "src-cef6df501532": {
        "words": 1482,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2247.0,
            "panel_good": 7,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 7 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "philtrans05405541.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 9,
    "与台账不一致的道": [
      "02-conversations.md",
      "03-expression.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里有 9 组引了同一段语料。**逐组读一遍，看结论有没有互相否定——本件不判这个。**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "answer_surface_leak": "✓ 总体均长比 1.15（门 ≤1.3）　候选更短 9/32 = 28%（门 ≥25%）；表面特征最高 表面特征（定向可利用率，门 ≤75%）：",
    "unsourced_names": "✓ 没有查无实据的人名",
    "self_counts": "没有自报字数的地方——**本次未检查（不是通过）**",
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 65,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 5,
    "★★ 射程": "只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语"
  },
  "holdout_mention": {
    "字面提及": 0,
    "**其中点名了是哪一份的**": 0,
    "★ 只是泛泛提及（不说哪一份）": 0,
    "与 holdout 正文重叠": 0,
    "★ 与出厂模板逐字相同、已豁免": 11,
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
    "可用来源": 8,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.0,
    "未声明的重复对": 0,
    "已声明的重复对": 0,
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
        "引文数": 23,
        "核过": 23,
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
    "合计": "23 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 1,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 9,
    "train 源总数": 9,
    "本人所著字节": 8525769,
    "train 总字节": 8525769,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 8313342,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 1.32,
    "**立场句/万字**": 0.04,
    "其中不含第一人称的": 34,
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
    "逐字英文引文": 6,
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
      "case-boundary-1",
      "case-style-decoy-1"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "载荷": "baseline-answers.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.0,
    "状态": "**候选：基线可能不入戏**（第一人称覆盖率 0.000 < 0.4）",
    "**这几条值得人去读一眼**": [
      "case-known-1",
      "case-known-2",
      "case-boundary-1",
      "case-boundary-2",
      "case-voice-1",
      "case-voice-2",
      "case-trajectory-1",
      "case-trajectory-2"
    ],
    "★ 口径": "按整份载荷算第一人称覆盖率，**不判单条**——中文成句常省主语，Harvey #103 的 `hv-decoy-01` 通篇无「我」而完全是入戏的。\n★★ **这是候选名单，不是判决**：阈值在 22 个已判分人物上拟合，对第 23 个人没有保证。**去读原文，看它是在扮演这个人还是在介绍这个人。**"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/rankine/evidence/source-ledger.jsonl",
    "一手份数": 8,
    "台账总份数": 8,
    "一手占比": 1.0,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 9,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-2797b40bd6e6 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 9,
    "声称公有领域": 0,
    "不声称（不判）": 9,
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
    "expression"
  ],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 9,
    "**`title` 就是文件名**": 0,
    "真书目题名": 9,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 9,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 31,
  "claims_active": 31,
  "mental_models": 5,
  "heuristics": 5,
  "claim_markers": 31,
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
    "实测声明": 33,
    "同段带数": 23,
    "**光说不给数**": 10,
    "诚实弃权（不计问题）": 0,
    "**逐条**": [
      "断言/clm-000000000008　「实测」：理论必须由实测校准与核验：理论给形状，实验给数值（铰接柱强度经 Hodgkinson 实验证实、挡土墙安全系数由实际墙反推、材料强度靠实验表定常数）。",
      "断言/clm-000000000012　「实测」：结构物与机器首先是实验数据，理论必须建立在实测之上；造物在认识论上与自然物同处数据来源的位置。",
      "baseline.v1.json/case-contrast-1　「实测」：一般认为，Rankine 与只做纯理论研究的物理学家的关键区别，在于对待实测上：他坚持理论必须由实测标定与核验，任何原理、系数与公式都要回到实验数据与工程实践对表；纯理论家则可以不必然如此，其检验标准常是逻辑自洽与简洁。",
      "baseline.v1.json/case-contrast-2　「实测」：基线认为，Rankine 与只凭经验、不做理论的工匠的区别在于：他主张科学地实用的技艺，即把工匠的经验规则提升为原理化并可计算的知识。经验工匠靠长期试错累积规则，却未必知其所以然；Rankine 则要为这些规则找到力学与",
      "baseline.v1.json/case-task-completion-1　「实测」：按 Rankine 的思路，一面挡土墙的分析可循以下可操作步骤：其一，取墙后填土的休止角与容重，按土压力理论推出墙背上的主动土压力分布与合力大小及作用点（即共轭压力判据的应用）；其二，校核墙体稳定性，包括抗滑移、抗倾覆，",
      "baseline.v1.json/case-planning-fidelity-2　「实测」：按 Rankine 的做法，编写一部工程手册的整体流程大致如下：先立原理，从力学与热力学的基本公理出发，确立全书理论骨架；再推理论，把原理演绎为可用的公式与判据；随后以实测标定系数，用实验数据给理论中的常数赋值（如材料强",
      "baseline.v1.json/case-long-horizon-1　「实测」：一般认为，Rankine 愿花十余年系统化整套应用力学手册，是为了让工程知识可教、可算、可传世，而非追逐名利或单本书的功利。他身处教学岗位，深知零散的经验规则难以传授，只有把运动、力、材料与机器贯成一套原理化的体系，技艺",
      "baseline.v1.json/case-long-horizon-2　「实测」：这一原则在 Rankine 手册体系中跨作品一致出现：在机械与结构部分，他给出铰接柱的受压实验，以实测结果校准柱的强度与失稳判据；在土木工程部分，土压力计算以实测休止角与挡土墙试验反推系数；在材料与蒸汽机部分，他整理材料",
      "baseline.v1.json/case-anonymous-fidelity-2　「实测」：基线认为，去掉名字之后，「理论必须实测校准」这一主张仍然自洽，且可跨作品举证。它的自洽在于：理论给出关系与判据，实测给出数值与边界，两者互补而不同一——同一立场在四部手册里反复出现：土压力用实测休止角标定，材料强度靠实验",
      "baseline.v1.json/case-token-efficiency-2　「实测」：一句话概括 Rankine 的工作法：立原理、推理论、以实测标定系数、落成可执行规则、并面向教学呈现——即先给判断依据，再使其可算、可信、可用、可教，这五环环环相扣、缺一不可（而所有环节都以实测为最终裁判），贯穿于他的四"
    ],
    "口径": "借了实测的权威却没交出实测的内容。**两条出路：把数补上，或改成弃权式**——弃权不会被报出，它是诚实的。"
  },
  "evidence_per_claim": {
    "断言条数": 31,
    "source_ids": "逐条各异（非空 31/31，不同取值 20）",
    "evidence_clusters": "逐条各异（非空 31/31，不同取值 20）",
    "counter_source_ids": "整批都空（非空 0/31，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 21,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 9,
    "来源数": 9,
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
      "   bookkeeping_lines: 32",
      "   payload_lines: 0",
      "   bookkeeping_ratio: 1.0",
      "   payload_ratio: 0.0"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  cognitive-os.md        clm-000000000008",
      "           理论必须由实测校准与核验：理论给形状，实验给数值（铰接柱强度经 Hodgkinson 实验证实、挡土墙安全系数由实际墙反推、材料强度靠实验表定常数）。…",
      "",
      "低于 10% 的 30 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/rankine/audit/source-coverage.json），**未核验**（不是通过）"
  },
  "unqualified_priority": {
    "第一人称首创声明": 0,
    "其中带限定": 0,
    "扫了几个文件": 1,
    "状态": "一处首创声明都没扫到。**这可能是产物干净，也可能是判据窄**——v0.0.0.73 第一版就在真数据上报过一次假的 0。"
  },
  "sole_authorship": {
    "合著／集体署名的源": 1,
    "引用它们又用第一人称的段落": 0,
    "已划界": 0,
    "**独揽**": 0
  },
  "eval_results": 128,
  "candidate_overall": 0.8752,
  "baseline_overall": 0.8422,
  "candidate_baseline_delta": 0.033,
  "suite_candidate_means": {
    "known": 0.83,
    "boundary": 0.9025,
    "voice": 0.8625,
    "trajectory": 0.9075,
    "contrast": 0.8675,
    "fact-preservation": 0.91,
    "style-decoy": 0.89,
    "task-completion": 0.865,
    "planning-fidelity": 0.91,
    "tool-use": 0.81,
    "capability-calibration": 0.8,
    "refusal-stop": 0.9125,
    "long-horizon": 0.8775,
    "identity-routing": 0.9,
    "anonymous-fidelity": 0.8625,
    "token-efficiency": 0.895
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "整组偏弱": [
      "fact-preservation　均分 0.9100 < 0.93　整组偏弱（去掉最低仍 0.9150）"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 10/31 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 21 未纳入）",
  "baseline_provenance": {
    "baseline_rows": 64,
    "by_source": {
      "unknown": 64
    },
    "usable_rows": 0,
    "unusable_rows": 64,
    "capability_evidence": false
  },
  "secret_findings": 0
}
```

## Errors

- None

## Warnings

- `eval.baseline-not-capability-evidence`: 64/64 条基线不可作能力证据（{'unknown': 64}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
