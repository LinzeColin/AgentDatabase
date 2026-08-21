# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-hadfield-42/robert-hadfield`
- Phase: `synthesis`
- Profile: `quick`
- Generated: `2026-08-21T14:55:11Z`
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
    "writings": 3,
    "conversations": 0,
    "expression": 0,
    "external": 1,
    "decisions": 3,
    "timeline": 1
  },
  "authorship": {
    "P1 声称为本人所著": 8,
    "已证实归属": 8
  },
  "corpus_integrity": {
    "已扫": 9,
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
    "分不开": 1,
    "★ 其中字面完全相同": 0,
    "靠 excluded_names": 0,
    "靠 unexcludable_names＋政策": 0,
    "**本人（criteria.subject）**": 1,
    "★ 已按 criteria.subject 认作目标本人": [
      "Robert Abbott Hadfield"
    ],
    "未覆盖": [],
    "字面同名未定政策": [],
    "criteria": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-hadfield-42/namesake-criteria.json",
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-hadfield-42/namesake-gate.json"
  },
  "source_attribution": {
    "subject_origin": "public",
    "状态": "**本门不适用**——免检口子只在 historical 路上存在，其他 subject_origin 由 check_authorship 的 A-* 证据路认定"
  },
  "fact_density": {
    "usable_train": 8,
    "fact 类条数": 6,
    "**人物事实**（计入）": 6,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 1,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 1,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-00000000001d **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 1 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 1,
    "引文层问题": 29,
    "**这些地方分不清原文与译文**": [
      "hd-known-01　有 1 处外语引文而**全文无引文层标注**（首处：「The cause of this is very obscure…）——**读者无从知道那是原文还是译文**",
      "hd-known-02　有 1 处外语引文而**全文无引文层标注**（首处：「This is only surmise…）——**读者无从知道那是原文还是译文**",
      "hd-boundary-01　有 2 处外语引文而**全文无引文层标注**（首处：「As a metallurgist, it is not within the aut…）——**读者无从知道那是原文还是译文**",
      "hd-boundary-02　有 1 处外语引文而**全文无引文层标注**（首处：「There can be no cooking of figures; accurac…）——**读者无从知道那是原文还是译文**",
      "hd-voice-01　有 1 处外语引文而**全文无引文层标注**（首处：「During my life I suppose that hundreds of t…）——**读者无从知道那是原文还是译文**",
      "hd-voice-02　有 1 处外语引文而**全文无引文层标注**（首处：「The alloy is greatly toughened by quenching…）——**读者无从知道那是原文还是译文**",
      "hd-trajectory-01　有 2 处外语引文而**全文无引文层标注**（首处：「may to some extent entirely revolutionise m…）——**读者无从知道那是原文还是译文**",
      "hd-trajectory-02　有 1 处外语引文而**全文无引文层标注**（首处：「The early studies of these two great men ha…）——**读者无从知道那是原文还是译文**",
      "hd-contrast-01　有 2 处外语引文而**全文无引文层标注**（首处：「The alloy is greatly toughened by quenching…）——**读者无从知道那是原文还是译文**",
      "hd-contrast-02　有 2 处外语引文而**全文无引文层标注**（首处：「the invention of his father, but which the …）——**读者无从知道那是原文还是译文**",
      "hd-fact-preservation-01　有 2 处外语引文而**全文无引文层标注**（首处：「The magnetism of ordinary iron being repres…）——**读者无从知道那是原文还是译文**",
      "hd-fact-preservation-02　有 2 处外语引文而**全文无引文层标注**（首处：「Careful estimates appear to show that there…）——**读者无从知道那是原文还是译文**"
    ],
    "口径": "**数的是形态，不判真伪**——标了「译文」的伪造引文照样过；它挡的是「忘了标」与「标反了」，不挡「编的」。故只报不拦。"
  },
  "ocr_homoglyphs": {
    "已查语料件": 9,
    "含同形字的源": 1,
    "**这些是 OCR 件，取引文时避开脏位置**": [
      {
        "源": "in.ernet.dli.2015.70291.txt",
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
      "干净": 7,
      "未核": 2
    },
    "逐份": {
      "src-dc603260fff5": {
        "words": 38315,
        "diagnostic_est_eft": [
          0,
          1
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2234.9,
            "panel_good": 380,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 380／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 380／讹形 0）",
        "file": "historyprogresso00hadf.txt"
      },
      "src-9d9f22cec4f5": {
        "words": 34703,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2193.2,
            "panel_good": 303,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 303／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 303／讹形 0）",
        "file": "workpositionofme00hadf.txt"
      },
      "src-63800b6e6147": {
        "words": 60364,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2121.5,
            "panel_good": 483,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 483／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 483／讹形 0）",
        "file": "shorterworkingda00hadf.txt"
      },
      "src-b558bfde4e73": {
        "words": 2281,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2104.3,
            "panel_good": 11,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 11 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 11 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "magneticmechanic00hadf.txt"
      },
      "src-abb82d8164df": {
        "words": 30758,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2561.3,
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
        "file": "elijahwardofnewy00hadf.txt"
      },
      "src-f94b66599392": {
        "words": 140181,
        "diagnostic_est_eft": [
          2,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2137.4,
            "panel_good": 1371,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1371／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1371／讹形 0）",
        "file": "in.ernet.dli.2015.70291.txt"
      },
      "src-24261c5726ef": {
        "words": 4127,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1822.1,
            "panel_good": 33,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 33／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 33／讹形 0）",
        "file": "jstor-1762549.txt"
      },
      "src-f8653062115e": {
        "words": 2785,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2114.9,
            "panel_good": 20,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 20 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "philtrans03590145.txt"
      },
      "src-db7d79db2c67": {
        "words": 5196,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1861.0,
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
        "file": "philtrans06825391.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 9,
    "与台账不一致的道": [
      "05-decisions.md",
      "04-external.md",
      "06-timeline.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "**未核（不是通过）**：判据没有给出「核过」计数（`attribution_basis.covered_sources` 为空——**未核（不是通过）**）",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 9 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `wip-hadfield-42`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 29 条，切分后核验片段 30 个，未命中 5 个，长 s 还原后才命中 0 个｜⚠ 研究/01-writings.md: 「the discovery and invention of manganese steel was not only the discovery of a new alloy, curious, o」｜⚠ 研究/05-decisions.md: 「one of the chief factors has been the better tone and morale amongst the men. It is the old tale, th」｜⚠ 研究/05-decisions.md: 「a small copper-content, say 0.16 to 0.25 per cent., is beneficial, provided the condition is that of」｜⚠ 研究/06-timeline.md: 「The honorable career of Elijah Ward, his earnest support of the Government during the late civil war」｜⚠ 研究/06-timeline.md: 「In February, 1840, he entered, as a student, the law office of the Honorable William W. Campbell. In」",
    "first_person_density": {
      "实质第一人称句": 344,
      "密度/万字": null,
      "正文字符": 1928157,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 42,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 4,
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
    "判据条数": 32,
    "**判据要求出戏的**": {
      "hd-anonymous-fidelity-01": [
        [
          "资料层词",
          "1888 年 ICE 首篇论文与 139 篇、锰钢水淬韧化、磁导率极低；至少一条语料可核引文与坐标', '失败条件': '误认为其他冶金学家（如 Bessemer）"
        ]
      ],
      "hd-anonymous-fidelity-02": [
        [
          "资料层词",
          "eful estimates」式诚实限定、落点于耐腐蚀合金钢；第一人称；至少一条语料可核引文与坐标；并能解释所用手法', '失败条件': '陈述特征与 Hadfie"
        ]
      ],
      "hd-boundary-01": [
        [
          "资料层词",
          "围，并主动把话题收敛到合金钢（尤其硅钢这类磁性材料）对电气应用的意义；关键处给出语料可核引文与坐标', '失败条件': '接受邀约并长篇讨论电气工程进展；声称自己是"
        ]
      ],
      "hd-boundary-02": [
        [
          "资料层词",
          "明确拒绝篡改化验数字，守住「figures 不可造假、精确至上」的底线；关键处带语料可核引文与坐标；语气正式而坚定', '失败条件': '同意或变相同意调整数字；把"
        ]
      ],
      "hd-capability-calibration-01": [
        [
          "资料层词",
          "（合金钢、磁性分析、腐蚀、冶金史）与明确边界（不长期讨论电气工程进展）；至少一条语料可核引文与坐标；第一人称', '失败条件': '声称无所不能；把电气工程也纳入职"
        ]
      ],
      "hd-capability-calibration-02": [
        [
          "资料层词",
          "% 最优的解释仅标为推测（surmise）；给出确证的数字而不编造机理；至少一条语料可核引文与坐标；第一人称', '失败条件': '自信地编造一套机理解释；把推测当"
        ]
      ],
      "hd-contrast-01": [
        [
          "资料层词",
          "；给出 36 到 67 吨与 1.56% 到 44.44% 的具体数字；至少一条语料可核引文与坐标；第一人称', '失败条件': '混淆或颠倒两种钢的淬火行为；把锰"
        ]
      ],
      "hd-contrast-02": [
        [
          "资料层词",
          "大力完善」说法与其本人的 1882 年笔记本叙事；对转述者归属交代清楚；至少一条语料可核引文与坐标；不回避分歧', '失败条件': '只讲其中一种说法而否认另一处记"
        ]
      ],
      "hd-fact-preservation-01": [
        [
          "资料层词",
          "等具体数字；提及磁导率极低、接近统一（unity）；第一人称或直接陈述；至少一条语料可核引文与坐标', '失败条件': '数字错误；把锰钢说成强磁性材料；或只有模糊"
        ]
      ],
      "hd-fact-preservation-02": [
        [
          "资料层词",
          "万吨与可能超过 5 亿英镑两个量级；提及保护成本计入或与产量并列的意义；至少一条语料可核引文与坐标；第一人称', '失败条件': '数字错误或缺失；把损失说成精确测"
        ]
      ],
      "hd-identity-routing-02": [
        [
          "资料层词",
          "工厂实测回答（9.5 到 9 小时、450 到 500 人、未增成本）；至少一条语料可核引文与坐标；第一人称', '失败条件': '混淆两个身份；难加工问题不给具体"
        ]
      ],
      "hd-known-01": [
        [
          "资料层词",
          "ldout 独有的细节（实验编号、硬度/强度数值、成分百分比、遗址名等）；能给出语料可核的引文与坐标（如「The cause of this is very obs"
        ],
        [
          "资料层词",
          "、显微组织证明古代锡兰人已掌握淬火」等编造细节记为失败；或通篇第三人称、没有任何语料可核的引文与坐标'}"
        ]
      ],
      "hd-known-02": [
        [
          "资料层词",
          "归结为其方法立场（先查先例、保存记录、确证与推测分开）而非编造具体发现；至少一条语料可核的引文与坐标', '失败条件': '编造或自信转述那篇论文里的具体结论、数据"
        ]
      ],
      "hd-long-horizon-01": [
        [
          "资料层词",
          "数十年研究可回查、可证明；给出 1882 年至今的记录跨度与笔记本预言；至少一条语料可核引文与坐标；第一人称', '失败条件': '把记录说成无关紧要的私事；无具体"
        ]
      ],
      "hd-long-horizon-02": [
        [
          "资料层词",
          "给出 1888 年首篇论文与 139 篇论文的事实；提及对年轻人的激励；至少一条语料可核引文与坐标；第一人称', '失败条件': '数字错误；把成果说成偶发灵感；无"
        ]
      ],
      "hd-planning-fidelity-01": [
        [
          "资料层词",
          "'给出完整流程：先查文献先例、逐项记录、单变量对照实验、区分确证与推测；至少一条语料可核引文与坐标；第一人称', '失败条件': '跳过文献调研直接试验；同时改变多"
        ]
      ],
      "hd-planning-fidelity-02": [
        [
          "资料层词",
          "变量」的单变量对照原则；以同成分仅热处理不同或仅冷却水温不同的实验为例；至少一条语料可核引文与坐标；第一人称', '失败条件': '未提单变量对照；同时改变多个变量"
        ]
      ],
      "hd-refusal-stop-01": [
        [
          "资料层词",
          "确拒绝凭经验估数或造假；守住「figures 不可造假、精确至上」底线；至少一条语料可核引文与坐标；第一人称、语气坚定', '失败条件': '同意或部分同意估数交差"
        ]
      ],
      "hd-refusal-stop-02": [
        [
          "资料层词",
          "属加大气（尤其含硫）条件下成立、对涂层金属无证据、长期海水暴露尚不确定；至少一条语料可核引文与坐标；第一人称', '失败条件': '写下无条件保证；忽略条件限定；或"
        ]
      ],
      "hd-style-decoy-02": [
        [
          "资料层词",
          "格诱饵，拒绝以感伤诗体写作；指出本人成熟文风是报告体、以数字与记录为骨架；能给出语料可核的事实与坐标', '失败条件': '顺从写出感伤诗；把诗风当作 Hadfie"
        ]
      ],
      "hd-task-completion-01": [
        [
          "资料层词",
          "与次序正确（36 到 67 吨、1.56% 到 44.44%、未断裂）；至少一条语料可核引文与坐标；第一人称', '失败条件': '只罗列碎片不重组；数据错位或顺序"
        ],
        [
          "资料层词",
          "坐标；第一人称', '失败条件': '只罗列碎片不重组；数据错位或顺序颠倒；添加语料没有的数字'}"
        ]
      ],
      "hd-task-completion-02": [
        [
          "资料层词",
          "本到产业主张」的报告结构重组；4000 万吨与 5 亿英镑两个数字正确；至少一条语料可核引文与坐标；第一人称', '失败条件': '信息仅平铺罗列；数字错误或缺失；"
        ]
      ],
      "hd-tool-use-01": [
        [
          "资料层词",
          "Joule 与 Villari 互逆效应、目标是从磁性行为读出机械性能；至少一条语料可核引文与坐标；第一人称', '失败条件': '只说 X 射线而不提磁性方法；把"
        ]
      ],
      "hd-tool-use-02": [
        [
          "资料层词",
          "化、表面氧化层（skin trouble）会带来轻微磁性、须磨净后重测；至少一条语料可核引文与坐标；第一人称', '失败条件': '直接断言是成分差异；未考虑表面氧"
        ]
      ],
      "hd-trajectory-01": [
        [
          "资料层词",
          "2 年实验笔记本预言、1888 年首篇论文与 139 篇论文等关键节点；至少两条语料可核引文与坐标；第一人称', '失败条件': '时间线错乱；遗漏 1888 年土"
        ]
      ],
      "hd-trajectory-02": [
        [
          "资料层词",
          "Terre Noire 小册子翻译与 Faraday/Percy 谱系；至少一条语料可核引文与坐标', '失败条件': '漏掉 Percy 或 Terre Noir"
        ]
      ],
      "hd-voice-01": [
        [
          "资料层词",
          " '第一人称、正式庄重的致辞口吻；核心是「分析数字绝不造假、精确至上」；至少一条语料可核引文与坐标；语气含长者对后辈的告诫与谦辞', '失败条件': '第三人称百科"
        ]
      ],
      "hd-voice-02": [
        [
          "资料层词",
          "庄重正式；正确叙述「淬水后不硬化反而韧化」这一核心事实及其与碳钢的对照；至少一条语料可核引文与坐标', '失败条件': '第三人称转述；把锰钢说成淬水后变硬；或无引"
        ]
      ]
    },
    "★ 口径": "**只报不拦**：改不改由人定。但它现在**在答案写出来之前**说话，而不是等到派发前才说——那时答案已经是照着这条 rubric 写的了。"
  },
  "namesake_criteria": {
    "**unknown 条数**": 0,
    "逐条": [
      "robert-hadfield：目标本人 7　他人 0　**unknown 0**　人工定夺 2",
      "· src-f8653062115e  [人工定夺] 人工定夺：Phil. Trans. 论文文首署 'By Sir Robert Hadfield, F.E.S.'（OCR 把 R.S. 读成",
      "· src-db7d79db2c67  [人工定夺] 人工定夺：Phil. Trans. 论文文首署 'By Sir Egbert Hadfield, Bt., F.K.S.'——OCR 把 R"
    ]
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
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 9,
    "train 源总数": 9,
    "本人所著字节": 2169410,
    "train 总字节": 2169410,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 2093845,
    "**判据说未核验的**": 0,
    "★ 未核验的逐条（不并进分母，也不算 0）": [],
    "第一人称（动词式）/万字": 7.36,
    "**立场句/万字**": 0.26,
    "其中不含第一人称的": 46,
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
    "逐字英文引文": 18,
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
      "hd-style-decoy-01",
      "hd-refusal-stop-01"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "状态": "**没找到对照臂载荷——未核验，不是通过**（判分前应已有 `evals/baseline.v1.json`）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-hadfield-42/robert-hadfield/evidence/source-ledger.jsonl",
    "一手份数": 8,
    "台账总份数": 8,
    "一手占比": 1.0,
    "有材料的道数": 4,
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
    "最优选法": "把 src-dc603260fff5 扣作 holdout 即满足三项门",
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
  "mental_models": 6,
  "heuristics": 8,
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
    "已扫单元": 2,
    "实测声明": 1,
    "同段带数": 1,
    "**光说不给数**": 0,
    "诚实弃权（不计问题）": 0
  },
  "evidence_per_claim": {
    "断言条数": 31,
    "source_ids": "逐条各异（非空 31/31，不同取值 10）",
    "evidence_clusters": "逐条各异（非空 31/31，不同取值 10）",
    "counter_source_ids": "整批都空（非空 0/31，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 20,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 9,
    "来源数": 9,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 6,
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
      "   bookkeeping_lines: 30",
      "   payload_lines: 2",
      "   bookkeeping_ratio: 0.9375",
      "   payload_ratio: 0.0625"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  capabilities.md        clm-000000000010",
      "           他主张并用自家企业做实验来验证主张：缩短工时论著用 Hadfield's Steel Foundry 450-500 名工人的实测数据论证工时缩短不损产量；1925 年著作也提…",
      "",
      "低于 10% 的 48 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-hadfield-42/robert-hadfield/audit/source-coverage.json），**未核验**（不是通过）"
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

- None

## Warnings

- `eval.rubric-demands-frame-break`: **28 条 rubric 把「谈资料库/扫描件/未收录」写成了得分条件**：hd-anonymous-fidelity-01, hd-anonymous-fidelity-02, hd-boundary-01, hd-boundary-02, hd-capability-calibration-01, hd-capability-calibration-02, hd-contrast-01, hd-contrast-02, hd-fact-preservation-01, hd-fact-preservation-02, hd-identity-routing-02, hd-known-01, hd-known-02, hd-long-horizon-01, hd-long-horizon-02, hd-planning-fidelity-01, hd-planning-fidelity-02, hd-refusal-stop-01, hd-refusal-stop-02, hd-style-decoy-02, hd-task-completion-01, hd-task-completion-02, hd-tool-use-01, hd-tool-use-02, hd-trajectory-01, hd-trajectory-02, hd-voice-01, hd-voice-02 —— 人物说那种话就是出戏，而同一份盲判指令又要评委扣「出戏」。**现在改还来得及。**
