# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/carnegie`
- Phase: `synthesis`
- Profile: `quick`
- Generated: `2026-08-24T21:04:33Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 11,
    "claims": 15
  },
  "sources_total": 11,
  "sources_train": 8,
  "sources_usable_train": 8,
  "sources_holdout": 3,
  "primary_sources": 8,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 4,
    "conversations": 0,
    "expression": 3,
    "external": 0,
    "decisions": 0,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 11,
    "已证实归属": 8,
    "存疑（有正面证据但另有他人署名）": [
      "src-8a5d4e1793b6 gospelofwealthot00carn.txt [A-byline] 另有他人署名：by THE NORTH AMERICAN REVI"
    ],
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "2 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 11,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Andrew Carnegie（1835-1919）著作归属依据：① archive.org creator 字段（Carnegie, Andrew, 1835",
    "citation": "archive.org creator 检索（numFound 219/179，合并去重 262 条，独立一手 95 部）；各源 archive.org ite",
    "争议篇目数": 0,
    "P1 声称本人所著": 11,
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
    "usable_train": 8,
    "fact 类条数": 1,
    "**人物事实**（计入）": 1,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 0,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 0,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**未达**": [
      "可核 `fact` 断言 1 条 < 要求 5 条（8 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因",
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 0 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 11,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 10,
      "未核": 1
    },
    "逐份": {
      "src-f4dde1785991": {
        "words": 89501,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1988.4,
            "panel_good": 718,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 718／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 718／讹形 0）",
        "file": "americanfourinha00carn.txt"
      },
      "src-f942339e1cea": {
        "words": 119512,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1926.8,
            "panel_good": 921,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 921／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 921／讹形 0）",
        "file": "autobiographyofa01carn.txt"
      },
      "src-552bbfdc799f": {
        "words": 57577,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2095.8,
            "panel_good": 483,
            "panel_bad": 1,
            "若无语种门会读到": 0.0021,
            "verdict": "干净",
            "rate": 0.0021,
            "reason": "英文讹字率 0.0021（正形 483／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0021,
        "reason": "英文讹字率 0.0021（正形 483／讹形 1）",
        "file": "cu31924002470700.txt"
      },
      "src-b465964357a3": {
        "words": 77413,
        "diagnostic_est_eft": [
          4,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2214.7,
            "panel_good": 701,
            "panel_bad": 1,
            "若无语种门会读到": 0.0014,
            "verdict": "干净",
            "rate": 0.0014,
            "reason": "英文讹字率 0.0014（正形 701／讹形 1）"
          }
        },
        "verdict": "干净",
        "rate": 0.0014,
        "reason": "英文讹字率 0.0014（正形 701／讹形 1）",
        "file": "empireofbusiness00carnuoft.txt"
      },
      "src-8a5d4e1793b6": {
        "words": 86963,
        "diagnostic_est_eft": [
          7,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2182.9,
            "panel_good": 720,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 720／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 720／讹形 0）",
        "file": "gospelofwealthot00carn.txt"
      },
      "src-eabcbd209294": {
        "words": 13408,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2173.3,
            "panel_good": 111,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 111／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 111／讹形 0）",
        "file": "leagueofpeacerec00carn_1.txt"
      },
      "src-4769b2a7c8a7": {
        "words": 11061,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2062.2,
            "panel_good": 80,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 80／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 80／讹形 0）",
        "file": "negroinamericaad00carn_0.txt"
      },
      "src-5512c8642a23": {
        "words": 37848,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2206.2,
            "panel_good": 308,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 308／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 308／讹形 0）",
        "file": "problemsoftodayw00carnuoft.txt"
      },
      "src-d1a85cb73073": {
        "words": 130211,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2180.5,
            "panel_good": 954,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 954／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 954／讹形 0）",
        "file": "triumphantdemo00carn.txt"
      },
      "src-c9f9e79154ad": {
        "words": 1050,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1628.6,
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
        "file": "warasmotherofval00carn.txt"
      },
      "src-5a457dfece71": {
        "words": 6995,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2208.7,
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
        "file": "edwinmstantonad00carn.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 11,
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
    "byline_in_carrier": "核过 10 条，指错 0 条",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 8 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 84 条，切分后核验片段 83 个，未命中 4 个，长 s 还原后才命中 0 个｜⚠ 研究/01-writings.md: 「before he could be ranked as one of the <!-- src-5512c8642a23 --> （后文」｜⚠ 研究/04-external.md: 「the impression was widespread among the highest officials there that there was something in the char」｜⚠ 研究/05-decisions.md: 「Carnegie Steel Company sells out to United States Steel Corporation」｜⚠ 研究/06-timeline.md: 「the grandeur of the republican system, the superiority of America」",
    "first_person_density": {
      "实质第一人称句": 3447,
      "密度/万字": null,
      "正文字符": 6397596,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 105,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 8,
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
    "可用来源": 8,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.0,
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
        "引文数": 77,
        "核过": 77,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 47,
        "核过": 47,
        "**对不上**": []
      },
      "04-external.md": {
        "引文数": 3,
        "核过": 3,
        "**对不上**": []
      },
      "05-decisions.md": {
        "引文数": 5,
        "核过": 5,
        "**对不上**": []
      },
      "06-timeline.md": {
        "引文数": 40,
        "核过": 40,
        "**对不上**": []
      }
    },
    "合计": "172 条引文，对不上 0 条",
    "读不到正文的来源": [
      "src-f4dde1785991",
      "src-552bbfdc799f",
      "src-c9f9e79154ad"
    ],
    "holdout 源数": 0,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 11,
    "train 源总数": 11,
    "本人所著字节": 4039994,
    "train 总字节": 4039994,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 3038597,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 18.18,
    "**立场句/万字**": 0.16,
    "其中不含第一人称的": 37,
    "读不到正文的": [
      "src-f4dde1785991",
      "src-552bbfdc799f",
      "src-c9f9e79154ad"
    ],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 11,
    "**疑似著录卡**": {},
    "读不到正文的": [
      "src-f4dde1785991",
      "src-552bbfdc799f",
      "src-c9f9e79154ad"
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/carnegie/evidence/source-ledger.jsonl",
    "一手份数": 8,
    "台账总份数": 8,
    "一手占比": 1.0,
    "有材料的道数": 3,
    "quick 要的一手份数": 4,
    "够得着吗": "吃全部材料就够得着"
  },
  "corpus_feasibility": {
    "profile": "quick",
    "可用材料总数": 11,
    "min_sources": 8,
    "min_lanes": 3,
    "min_primary_ratio": 0.4,
    "★ 真实下限": 9,
    "★ 口径": "`min_sources` 只数 train，而 synthesis/release **强制要有 holdout**，holdout 要从总数里扣 —— **所以真实下限是 min_sources + 1，而文档写的是 min_sources**。",
    "可行": true,
    "结论": "feasible",
    "还差": 0,
    "最优选法": "把 src-f4dde1785991 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 11,
    "声称公有领域": 0,
    "不声称（不判）": 11,
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
    "台账行数": 11,
    "**`title` 就是文件名**": 0,
    "真书目题名": 11,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 0,
    "有一边没年份": 11,
    "**逐条**": [],
    "★ 射程": "只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。"
  },
  "holdout_overlap": {
    "返回码": 0,
    "**硬失败**": 0,
    "其中·真重合": 0,
    "其中·无法判定": 0
  },
  "claims_total": 15,
  "claims_active": 15,
  "mental_models": 5,
  "heuristics": 3,
  "claim_markers": 15,
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
    "断言条数": 15,
    "source_ids": "逐条各异（非空 15/15，不同取值 12）",
    "evidence_clusters": "逐条各异（非空 15/15，不同取值 15）",
    "counter_source_ids": "整批都空（非空 0/15，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 12,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 11,
    "来源数": 11,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 59,
    "挂错作品": 0,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 58,
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/carnegie/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "   100.0%  cognitive-os.md        clm-000000000005",
      "           **劳工观：资本、经营才能、熟练劳工是\"三足凳\"，三者缺一不可、无先后贵贱；劳工的终极出路是\"合伙/持股\"而非革命；工资应按产品净价滑动**：1908《Problems of …",
      "",
      "低于 10% 的 0 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/carnegie/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/carnegie/audit/source-coverage.json），**未核验**（不是通过）"
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
