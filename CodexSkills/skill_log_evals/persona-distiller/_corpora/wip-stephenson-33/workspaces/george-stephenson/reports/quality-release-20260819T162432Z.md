# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-stephenson-33/workspaces/george-stephenson`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T16:24:32Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 13,
    "claims": 13
  },
  "sources_total": 13,
  "sources_train": 12,
  "sources_usable_train": 12,
  "sources_holdout": 1,
  "primary_sources": 12,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 1,
    "conversations": 1,
    "expression": 0,
    "external": 9,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 4,
    "已证实归属": 1,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "3 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 13,
    "不是语料": 0,
    "可疑": 1,
    "可疑（只报不拦）": [
      "raw/src-2c255ecc41b1/georgestephenso00step.txt　过短：1056 字节 < 2000——**确认这是不是一份完整的件**"
    ],
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "George Stephenson（1781-1848）的署名形态在题名页/著录上可见：\n  ① 1817 安全灯说明书（b29302766）：题名即《A de",
    "citation": "George Stephenson（1781-1848）的一手载体：1817 安全灯说明书、1828 致子信、1832 书信集、1838 铁路报告（均题名或著录",
    "争议篇目数": 0,
    "P1 声称本人所著": 4,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-stephenson-33/namesake-gate.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 4,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 4,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 12,
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
    "已查语料件": 13,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "不适用": 1,
      "未核": 2,
      "干净": 9,
      "不可用": 1
    },
    "逐份": {
      "src-2c255ecc41b1": {
        "words": 220,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 1.0000；英文：锚 90.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "georgestephenso00step.txt"
      },
      "src-df2863f7fe19": {
        "words": 2591,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2358.2,
            "panel_good": 16,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 16 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "b29302766.txt"
      },
      "src-1378888e2d03": {
        "words": 1769,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1401.9,
            "panel_good": 6,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 6 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 6 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "letters00step.normalized.txt"
      },
      "src-6423b28a4504": {
        "words": 3935,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2493.0,
            "panel_good": 32,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 32／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 32／讹形 0）",
        "file": "londonblackwallc00step.txt"
      },
      "src-593a0cef2b4c": {
        "words": 186777,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2316.7,
            "panel_good": 1404,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1404／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1404／讹形 0）",
        "file": "lifestephenson00smilrich.txt"
      },
      "src-9cd5e89841f6": {
        "words": 184168,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2308.7,
            "panel_good": 1407,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1407／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1407／讹形 0）",
        "file": "lifegeorgesteph05smilgoog.txt"
      },
      "src-1e53e3f9e332": {
        "words": 191409,
        "diagnostic_est_eft": [
          11,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2268.8,
            "panel_good": 1326,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1326／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1326／讹形 0）",
        "file": "lifeofgeorgestep00smiluoft.txt"
      },
      "src-4610275de781": {
        "words": 36741,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2360.6,
            "panel_good": 293,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 293／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 293／讹形 0）",
        "file": "georgestephenso00laysgoog.txt"
      },
      "src-5192fef08086": {
        "words": 181284,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2248.6,
            "panel_good": 1304,
            "panel_bad": 1,
            "若无语种门会读到": 0.0008,
            "verdict": "干净",
            "rate": 0.0008,
            "reason": "英文讹字率 0.0008（正形 1304／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0008,
        "reason": "英文讹字率 0.0008（正形 1304／讹形 1）",
        "file": "lifegeorgesteph01stepgoog.txt"
      },
      "src-0c1ec956834a": {
        "words": 201721,
        "diagnostic_est_eft": [
          11,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2239.3,
            "panel_good": 1393,
            "panel_bad": 1,
            "若无语种门会读到": 0.0007,
            "verdict": "干净",
            "rate": 0.0007,
            "reason": "英文讹字率 0.0007（正形 1393／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0007,
        "reason": "英文讹字率 0.0007（正形 1393／讹形 1）",
        "file": "lifegeorgesteph00smilgoog.txt"
      },
      "src-cdeb7a2ccf14": {
        "words": 124794,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 535.4,
            "panel_good": 155,
            "panel_bad": 1674,
            "若无语种门会读到": 0.9153,
            "verdict": "不可用",
            "rate": 0.9153,
            "reason": "德语讹字率 0.9153（正形 155／讹形 1674）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 1985,
          "变音符每千词": 96.0,
          "h→b坏": false,
          "变音符湮灭": false
        },
        "verdict": "不可用",
        "rate": 0.9153,
        "reason": "德语讹字率 0.9153（正形 155／讹形 1674）",
        "file": "bub_gb_FjVMAAAAIAAJ.txt"
      },
      "src-95903112fd85": {
        "words": 17214,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2501.5,
            "panel_good": 152,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 152／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 152／讹形 0）",
        "file": "sketchesofourinf00adam.txt"
      },
      "src-c479752acdfd": {
        "words": 88337,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2441.8,
            "panel_good": 633,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 633／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 633／讹形 0）",
        "file": "jubileememorial00jeangoog.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 13,
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
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里没有跨题共享的语料片段——**无从比对，不是通过**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "unsourced_names": "⚠ **11 个不是一手依据**（只列不判）——拿它撑承重句之前，先知道它薄在哪：",
    "self_counts": "没有自报字数的地方——**本次未检查（不是通过）**",
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认",
    "quote_locator": "一条长逐字引文都没扫到——**本次未检查（不是通过）**"
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
    "★ 与出厂模板逐字相同、已豁免": 4,
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
    "可用来源": 12,
    "**按内容去重后的作品数**": 9,
    "虚高": 1.333,
    "未声明的重复对": 0,
    "已声明的重复对": 4,
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
    "holdout 源数": 1,
    "通过": null,
    "★ 未核（不是通过）": "研究道 `references/research/0*.md` 里**一条引文都没抽到** —— 本件一条也没核过。`通过` 置 null 表示**既不算通过也不算失败**。"
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.0068,
      "第三人称": 0.9932,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0,
      "已标的份数": 13,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 5,
    "train 源总数": 13,
    "本人所著字节": 843298,
    "train 总字节": 8263862,
    "own_voice_ratio": 0.102,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 53427,
    "**判据说未核验的**": 1,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-2c255ecc41b1",
        "原因": "语种判为 **?**（en=0.005 de=0.000 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 12.73,
    "**立场句/万字**": 0.19,
    "其中不含第一人称的": 1,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 4,
    "**疑似著录卡**": {
      "src-1378888e2d03": {
        "文件": "letters00step.txt",
        "字符数": 9550,
        "著录话术": [
          "A.L.S",
          "Autograph Letter Signed"
        ]
      }
    },
    "读不到正文的": [],
    "计数": "1 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "逐字英文引文": 0,
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
    "拒答溢出候选": 0
  },
  "baseline_in_persona": {
    "载荷": "baseline.v1.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.219,
    "状态": "**候选：基线可能不入戏**（第一人称覆盖率 0.219 < 0.4）",
    "**这几条值得人去读一眼**": [
      "case-known-1",
      "case-known-2",
      "case-boundary-1",
      "case-voice-2",
      "case-trajectory-1",
      "case-trajectory-2",
      "case-contrast-1",
      "case-contrast-2"
    ],
    "★ 口径": "按整份载荷算第一人称覆盖率，**不判单条**——中文成句常省主语，Harvey #103 的 `hv-decoy-01` 通篇无「我」而完全是入戏的。\n★★ **这是候选名单，不是判决**：阈值在 22 个已判分人物上拟合，对第 23 个人没有保证。**去读原文，看它是在扮演这个人还是在介绍这个人。**"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-stephenson-33/workspaces/george-stephenson/evidence/source-ledger.jsonl",
    "一手份数": 12,
    "台账总份数": 12,
    "一手占比": 1.0,
    "有材料的道数": 4,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 13,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-2c255ecc41b1 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 13,
    "声称公有领域": 13,
    "不声称（不判）": 0,
    "有据可查": 0,
    "有结论无依据": 13,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": [
    "writings",
    "conversations",
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
    "台账行数": 13,
    "**`title` 就是文件名**": 0,
    "真书目题名": 13,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 13,
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
    "实测声明": 25,
    "同段带数": 17,
    "**光说不给数**": 8,
    "诚实弃权（不计问题）": 0,
    "**逐条**": [
      "断言/clm-000000000007　「实测」：自修者的实用主义：不依赖学院理论，以实测数字与可行成本为准绳；对理论主张（如 Davy 的科学优先）保持务实怀疑。",
      "断言/clm-000000000009　「实测」：工程报告以踏勘与造价核算支撑推荐：不写无实测依据的方案。",
      "断言/clm-00000000000c　「实测」：不越界宣称：对铁路工程给确定性判断，对学院科学（如 Davy 的化学理论）不冒充权威，只坚持自己的实测立场。",
      "judge_payload.v1.json/case-task-completion-2　「实测」：进气管口一律朝下开，煤灰落不进去。在基灵沃思井实测，把灯放进含瓦斯的气流里，火苗只在管内跳、不外炸；拿它下井，矿工敢提着走。",
      "judge_payload.v1.json/case-capability-calibration-1　「实测」：我不信那些学院派的漂亮理论，信的是实测：跑一趟，量煤耗、量速度、量闸车距离，数字说话。你要造，先给我线路的坡度图和运量，我按吨位和里程把马力算给你，这台机器包它跑得动、拉得走、修得起。",
      "baseline.v1.json/case-anonymous-fidelity-1　「实测」：它们共同指向一套实证型工程思维：**从现场实际出发反推设计规格**（现场到规格），**让实测数据优先于纸面估算**（实测优先），**并以运输效益作为方案的检验标准**（运输效益）。这套\"现场—实测—效益\"的组合，辨识度明",
      "baseline.v1.json/case-anonymous-fidelity-2　「实测」：判据不在名字里，而在可测量的生产效益（省煤、省工）里——测量与复现是公开、可核验的，不依赖署名或权威；去掉名字只去掉身份标签，判据的客观根基未动。它还能反身检验自身：把\"实用优先\"应用于\"实用优先\"，它剔除不产生效益的方",
      "baseline.v1.json/case-token-efficiency-2　「实测」：已确认题干出处：该问题取自本仓 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/example-knuth/gen_cases.py` "
    ],
    "口径": "借了实测的权威却没交出实测的内容。**两条出路：把数补上，或改成弃权式**——弃权不会被报出，它是诚实的。"
  },
  "evidence_per_claim": {
    "断言条数": 13,
    "source_ids": "逐条各异（非空 13/13，不同取值 9）",
    "evidence_clusters": "逐条各异（非空 13/13，不同取值 9）",
    "counter_source_ids": "整批都空（非空 0/13，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 7,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 2,
    "作品组数（连通分量，仅供参考）": 10,
    "来源数": 13,
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
      "   substantive_lines: 75",
      "   bookkeeping_lines: 3",
      "   payload_lines: 72",
      "   bookkeeping_ratio: 0.04",
      "   payload_ratio: 0.96"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  capabilities.md        clm-000000000008",
      "           速度与安全的平衡：早期主张 10 mph 极限，Rocket 时代转向更高速度——每次只推进到实测安全的上限，不冒险突破。…",
      "",
      "低于 10% 的 40 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-stephenson-33/workspaces/george-stephenson/audit/source-coverage.json），**未核验**（不是通过）"
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
  "candidate_overall": 0.8222,
  "baseline_overall": 0.7134,
  "candidate_baseline_delta": 0.1088,
  "suite_candidate_means": {
    "known": 0.85,
    "boundary": 0.905,
    "voice": 0.84,
    "trajectory": 0.895,
    "contrast": 0.845,
    "fact-preservation": 0.865,
    "style-decoy": 0.85,
    "task-completion": 0.905,
    "planning-fidelity": 0.89,
    "tool-use": 0.7,
    "capability-calibration": 0.925,
    "refusal-stop": 0.9,
    "long-horizon": 0.8,
    "identity-routing": 0.65,
    "anonymous-fidelity": 0.8,
    "token-efficiency": 0.535
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "整组偏弱": [
      "fact-preservation　均分 0.8650 < 0.93　整组偏弱（去掉最低仍 0.8800）"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 10/13 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 3 未纳入）",
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

- `model.placeholder`: boundaries.md is not substantive enough for release
- `model.placeholder`: divergence-map.md is not substantive enough for release
- `content.ocr-homoglyph`: /Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-stephenson-33/workspaces/george-stephenson/evals/baseline.v1.json: 引文含 OCR 同形字 'ΔG'→'ΔG'——读者拿这句去原件里搜是搜不到的｜工作我可以胜任：\n\n- 化学方程式配平、反应机理与产物预测；\n- 摩尔、浓度、稀释、滴定等化学计量计算；\n- 酸…
- `content.ocr-homoglyph`: /Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-stephenson-33/workspaces/george-stephenson/evals/round1/stephenson33_blind_payload.json: 引文含 OCR 同形字 'ΔG'→'ΔG'——读者拿这句去原件里搜是搜不到的｜工作我可以胜任：\n\n- 化学方程式配平、反应机理与产物预测；\n- 摩尔、浓度、稀释、滴定等化学计量计算；\n- 酸…
- `content.no-quotes-to-verify`: 引文核验**没有可核的对象**（不是通过）：语料读到了，而断言与答案里**一条引文都没扫到**——本产品的立身之本是能出示一手逐字引文，一条都没有本身就是问题
- `eval.surface-leak`: **表面特征会指出哪一侧是候选**，这一轮的盲判不成立：**总体均长比 0.68 < 0.77**——候选整体过短，长度同样会变成指认信号（**反方向的同一个问题**）；**候选更短的题多达 28/32 = 88%，要 ≤75%**——一边倒同样能指认，只是倒的方向反了

## Warnings

- `corpus.longs-corruption`: **1 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-cdeb7a2ccf14` bub_gb_FjVMAAAAIAAJ.txt —— 德语讹字率 0.9153（正形 155／讹形 1674），**不可做逐字引文**
- `corpus.unexamined-band`: **1/13 份语料落在两道门之间**：字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；但若某条道只靠这类文件撑着，请人看一眼。
- research.catalogue-entry：1 份 P1 像是「著录方描述这份文献」而不是文献本身——**改分档是人的判断，本项只报不拦**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
