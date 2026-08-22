# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-eiffel-142/workspaces/gustave-eiffel`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-22T17:58:08Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 16,
    "claims": 13
  },
  "sources_total": 16,
  "sources_train": 15,
  "sources_usable_train": 15,
  "sources_holdout": 1,
  "primary_sources": 13,
  "primary_ratio": 0.8667,
  "lane_source_counts": {
    "writings": 12,
    "conversations": 0,
    "expression": 0,
    "external": 2,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 14,
    "已证实归属": 9,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "5 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 16,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "**法文印本的题名页署名**。他 1832–1923 在世，作品皆为印本。本库 15 份 train 源里，`check_authorship` 未取得署名证据",
    "citation": "逐份扉页原文见下 `disputed_works`；判定由 scripts/check_authorship.py 现算（2026-08-19）。",
    "争议篇目数": 5,
    "P1 声称本人所著": 14,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 3,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-eiffel-142/namesake-gate.PRE-NARROW-3cand.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 14,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 14,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 15,
    "fact 类条数": 2,
    "**人物事实**（计入）": 2,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 3,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 3,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-ef2b496d4538 **连步骤都没有**：是一句概括不是一套做法",
      "clm-4f0b3b11397f **只有步骤没有判据**：照着做的人不知道自己做错没有",
      "clm-0d0c24d49bd7 **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可核 `fact` 断言 2 条 < 要求 5 条（15 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因",
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 3 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 1,
    "引文层问题": 30,
    "**这些地方分不清原文与译文**": [
      "ef-known-01　有 2 处外语引文而**全文无引文层标注**（首处：「un vent uni forme de…）——**读者无从知道那是原文还是译文**",
      "ef-voice-01　有 2 处外语引文而**全文无引文层标注**（首处：「excellent acier de…）——**读者无从知道那是原文还是译文**",
      "ef-traj-01　有 2 处外语引文而**全文无引文层标注**（首处：「ce qui revient à supposer…）——**读者无从知道那是原文还是译文**",
      "ef-ctr-01　有 1 处外语引文而**全文无引文层标注**（首处：「Autres objections contre la Tour et son uti…）——**读者无从知道那是原文还是译文**",
      "ef-fact-01　有 1 处外语引文而**全文无引文层标注**（首处：「Aussi fus-je du très petit nombre de ceux…）——**读者无从知道那是原文还是译文**",
      "ef-decoy-01　有 1 处外语引文而**全文无引文层标注**（首处：「Leur flèche est de…）——**读者无从知道那是原文还是译文**",
      "ef-task-01　有 1 处外语引文而**全文无引文层标注**（首处：「la vérification des calculs à une Sous-Comm…）——**读者无从知道那是原文还是译文**",
      "ef-plan-01　有 2 处外语引文而**全文无引文层标注**（首处：「MÉTHODE ET APPAREIL EMPLOYÉS…）——**读者无从知道那是原文还是译文**",
      "ef-tool-01　有 1 处外语引文而**全文无引文层标注**（首处：「mâchoires arrondies à…）——**读者无从知道那是原文还是译文**",
      "ef-cal-01　有 1 处外语引文而**全文无引文层标注**（首处：「sur le choix d…）——**读者无从知道那是原文还是译文**",
      "ef-stop-01　有 1 处外语引文而**全文无引文层标注**（首处：「la Tour devint la propriété de la Ville…）——**读者无从知道那是原文还是译文**",
      "ef-lh-01　有 2 处外语引文而**全文无引文层标注**（首处：「proposant un type de…）——**读者无从知道那是原文还是译文**"
    ],
    "口径": "**数的是形态，不判真伪**——标了「译文」的伪造引文照样过；它挡的是「忘了标」与「标反了」，不挡「编的」。故只报不拦。"
  },
  "ocr_homoglyphs": {
    "已查语料件": 16,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "不适用": 15,
      "未核": 1
    },
    "逐份": {
      "src-01bd215aa6a3": {
        "words": 5563,
        "diagnostic_est_eft": [
          21,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "1879-pont-du-douro.txt"
      },
      "src-4f7805a8a1b1": {
        "words": 7468,
        "diagnostic_est_eft": [
          52,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "1888-garabit-notice-A.txt"
      },
      "src-74d717517b32": {
        "words": 7051,
        "diagnostic_est_eft": [
          52,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 2.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "1888-garabit-notice-B.txt"
      },
      "src-5764546dcc77": {
        "words": 8460,
        "diagnostic_est_eft": [
          110,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 2.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "1888-grandes-constructions.txt"
      },
      "src-d1045ba732f1": {
        "words": 43994,
        "diagnostic_est_eft": [
          399,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 3.2<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2500）",
        "file": "1889-memoire-viaduc.txt"
      },
      "src-64c2c4300777": {
        "words": 81881,
        "diagnostic_est_eft": [
          849,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 7.2<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.1000）",
        "file": "1900-travaux-scientifiques-A.txt"
      },
      "src-bef005979496": {
        "words": 83670,
        "diagnostic_est_eft": [
          847,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0075；英文：锚 12.3<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.3636）",
        "file": "1900-travaux-scientifiques-B.txt"
      },
      "src-e4ef8d8d1f62": {
        "words": 247705,
        "diagnostic_est_eft": [
          2625,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0410；英文：锚 2.0<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.1538）",
        "file": "1900-tour-de-trois-cents-metres.txt"
      },
      "src-7dc09014148b": {
        "words": 111722,
        "diagnostic_est_eft": [
          961,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0108；英文：锚 1.8<500.0，若强行读 0.0000；德语：锚 0.1<15.0，若强行读 0.2000）",
        "file": "1902-la-tour-eiffel-en-1900.txt"
      },
      "src-72329cd0626a": {
        "words": 71531,
        "diagnostic_est_eft": [
          412,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0719；英文：锚 2.9<500.0，若强行读 0.2500；德语：锚 0.1<15.0，若强行读 0.4600）",
        "file": "1910-resistance-de-lair-aviation.txt"
      },
      "src-2fd2776e6eb5": {
        "words": 1707,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2390.2,
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
        "file": "external-1889-jstor-gustave-eiffel.txt"
      },
      "src-a6d1730a72c1": {
        "words": 19290,
        "diagnostic_est_eft": [
          116,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.1505；英文：锚 8.3<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "external-1929-la-liberte.txt"
      },
      "src-20c8386535ea": {
        "words": 25019,
        "diagnostic_est_eft": [
          276,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.8<500.0，若强行读 0.0000；德语：锚 0.8<15.0，若强行读 0.0000）",
        "file": "1907-recherches-resistance-air.txt"
      },
      "src-56bc9705e2d3": {
        "words": 7504,
        "diagnostic_est_eft": [
          47,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 1.3<15.0，若强行读 0.0000）",
        "file": "1892-note-ecluses-panama.txt"
      },
      "src-553273d95ba5": {
        "words": 4958,
        "diagnostic_est_eft": [
          71,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 1.0000）",
        "file": "1910-laboratoire-aerodynamique.txt"
      },
      "src-00a22720411e": {
        "words": 1921,
        "diagnostic_est_eft": [
          21,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 0.0<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.0000）",
        "file": "1885-tour-en-fer-300m.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 16,
    "与台账不一致的道": [
      "05-decisions.md",
      "04-external.md",
      "01-writings.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "quote_integrity": "有引文未在语料中找到——**未命中不等于伪造**，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里",
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里没有跨题共享的语料片段——**无从比对，不是通过**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "answer_surface_leak": "✓ 总体均长比 1.10（门 ≤1.3）　候选更短 14/32 = 44%（门 ≥25%）；表面特征最高 表面特征（定向可利用率，门 ≤75%）：",
    "unsourced_names": "✓ 没有查无实据的人名",
    "self_counts": "没有自报字数的地方——**本次未检查（不是通过）**",
    "ocr_language_death": "✓ 没有被 OCR 整份毁掉的语料",
    "gate_reachability": "✓ 各绝对分门都在两席实测可达范围内",
    "absence_claims": "⚠ 标记的须人工确认依据；本脚本不做自动判定",
    "claim_anchors": "⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认",
    "quote_locator": "✓ 每条长引文同段内都能找到坐标线索"
  },
  "quote_speaker": {
    "长逐字引文": 74,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 7,
    "★★ 射程": "只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语"
  },
  "holdout_mention": {
    "字面提及": 0,
    "**其中点名了是哪一份的**": 0,
    "★ 只是泛泛提及（不说哪一份）": 0,
    "与 holdout 正文重叠": 0,
    "★ 与出厂模板逐字相同、已豁免": 6,
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
    "可用来源": 15,
    "**按内容去重后的作品数**": 11,
    "虚高": 1.364,
    "未声明的重复对": 0,
    "已声明的重复对": 5,
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
        "引文数": 5,
        "核过": 5,
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
        "引文数": 0,
        "核过": 0,
        "**对不上**": []
      }
    },
    "合计": "13 条引文，对不上 0 条",
    "读不到正文的来源": [],
    "holdout 源数": 1,
    "通过": true
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": {
      "**第一人称字节占比**": 0.9743,
      "第三人称": 0.0257,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0,
      "已标的份数": 16,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 14,
    "train 源总数": 16,
    "本人所著字节": 4658001,
    "train 总字节": 4780831,
    "own_voice_ratio": 0.9743,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 0,
    "**判据说未核验的**": 14,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-01bd215aa6a3",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.089）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-4f7805a8a1b1",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.088）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-74d717517b32",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.091）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-5764546dcc77",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.107）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-d1045ba732f1",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.113）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-64c2c4300777",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.090）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-bef005979496",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.088）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-e4ef8d8d1f62",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.092）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": null,
    "**立场句/万字**": null,
    "其中不含第一人称的": 0,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 14,
    "**疑似著录卡**": {},
    "读不到正文的": [],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
    "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
    "通过": true
  },
  "verbatim_quotes": {
    "逐字英文引文": 2,
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
    "拒答溢出候选": 3,
    "**这几条值得人去读一眼**": [
      "ef-stop-01",
      "ef-stop-02",
      "ef-route-02"
    ],
    "★ 口径": "有拒答标记且可执行判断为 0。**数的是句式不是语义**，故只报不拦。\n★★ **这是候选名单，不是缺陷数**：2026-08-12 全库实测（588 条不同答案）首扫 62 条，逐条读原文后发现**读了 11 条、9 条是误杀**——判据认不出圈号编号、「你该去问他」、「查第 8 版」这类给法。八类已补进 ACTIONABLE（62→29），而抽读剩余仍见误杀。**逐条读过才算数。**"
  },
  "baseline_in_persona": {
    "载荷": "baseline-answers.json",
    "已扫答案": 32,
    "第一人称覆盖率": 0.938,
    "状态": "无候选（第一人称覆盖率 0.938）"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-eiffel-142/workspaces/gustave-eiffel/evidence/source-ledger.jsonl",
    "一手份数": 13,
    "台账总份数": 15,
    "一手占比": 0.8667,
    "有材料的道数": 3,
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
    "最优选法": "把 src-01bd215aa6a3 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 16,
    "声称公有领域": 16,
    "不声称（不判）": 0,
    "有据可查": 1,
    "有结论无依据": 15,
    "依据取自聚合器": 0
  },
  "pd_grounds": {
    "状态": "**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ 1929 年前出版 ／ 国会记录）并附证据"
  },
  "research_lanes_complete": [
    "writings",
    "external",
    "decisions"
  ],
  "translation_witness": {
    "申报的并行见证组": 0,
    "组内塌缩的断言": 0,
    "错": 0,
    "明细": [],
    "★": "申报 0 组**不等于**没有并行见证——本件不猜，只查申报"
  },
  "title_is_not_filename": {
    "台账行数": 16,
    "**`title` 就是文件名**": 0,
    "真书目题名": 16,
    "比例": 0.0,
    "★": "**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门"
  },
  "filename_year_vs_ledger": {
    "不一致": 0,
    "差一年": 0,
    "跨PD分界": 0,
    "两边都有年份": 16,
    "有一边没年份": 0,
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
    "实测声明": 15,
    "同段带数": 14,
    "**光说不给数**": 1,
    "诚实弃权（不计问题）": 1,
    "**逐条**": [
      "baseline.v1.json/ef-cal-01　「实测」：我给不出唯一的答案，因为我的东西大多来自风洞里的实测，不是算出来的。我在塔下建过风洞，反复比较过平板和带弯度的曲面——同样面积、同样攻角下，略微拱起的曲面比平板升力大得多，所以我一向主张翼面要带弯度，别做成平的。可拱多少"
    ],
    "口径": "借了实测的权威却没交出实测的内容。**两条出路：把数补上，或改成弃权式**——弃权不会被报出，它是诚实的。"
  },
  "evidence_per_claim": {
    "断言条数": 13,
    "source_ids": "逐条各异（非空 13/13，不同取值 10）",
    "evidence_clusters": "逐条各异（非空 13/13，不同取值 13）",
    "counter_source_ids": "整批都空（非空 0/13，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 10,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 13,
    "来源数": 16,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 27,
    "挂错作品": 2,
    "版本差（作品对、逐字文本取自另一版）": 0,
    "不唯一（同句见于多份源，挂错也照样绿）": 1,
    "取不到正文的源": 0,
    "例": [
      "clm-b853881e1830：挂 ['src-20c8386535ea/1907-recherches-resistance-air.txt', 'src-72329cd0626a/1910-resistance-de-lair-aviation.txt', 'src-7dc09014148b/1902-la-tour-eiffel-en-1900.txt'] → 实 ['src-64c2c4300777/1900-travaux-scientifiques-A.txt', 'src-bef005979496/1900-travaux-scientifiques-B.txt', 'src-e4ef8d8d1f62/1900-tour-de-trois-cents-metres.txt']",
      "clm-b853881e1830：挂 ['src-20c8386535ea/1907-recherches-resistance-air.txt', 'src-72329cd0626a/1910-resistance-de-lair-aviation.txt', 'src-7dc09014148b/1902-la-tour-eiffel-en-1900.txt'] → 实 ['src-e4ef8d8d1f62/1900-tour-de-trois-cents-metres.txt']"
    ]
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
      "     0.0%  capabilities.md        clm-4f0b3b11397f",
      "           **「这方法/这计算站不站得住」要有一个明写的位置，不藏在脚注**：1907 那部给它一个自己的编号 —— `3. — Abaque donnant les valeurs d…",
      "",
      "低于 10% 的 51 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-eiffel-142/workspaces/gustave-eiffel/audit/source-coverage.json），**未核验**（不是通过）"
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
  "eval_results": 128,
  "candidate_overall": 0.9016,
  "baseline_overall": 0.5598,
  "candidate_baseline_delta": 0.3417,
  "suite_candidate_means": {
    "known": 0.895,
    "boundary": 0.905,
    "voice": 0.9,
    "trajectory": 0.915,
    "contrast": 0.9,
    "fact-preservation": 0.91,
    "style-decoy": 0.9,
    "task-completion": 0.8875,
    "planning-fidelity": 0.915,
    "tool-use": 0.91,
    "capability-calibration": 0.8675,
    "refusal-stop": 0.89,
    "long-horizon": 0.92,
    "identity-routing": 0.905,
    "anonymous-fidelity": 0.91,
    "token-efficiency": 0.895
  },
  "suite_single_drag": {
    "未过阈值的套组": 1,
    "整组偏弱": [
      "fact-preservation　均分 0.9100 < 0.93　整组偏弱（去掉最低仍 0.9200）"
    ],
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 13/13 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 0 未纳入）",
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
