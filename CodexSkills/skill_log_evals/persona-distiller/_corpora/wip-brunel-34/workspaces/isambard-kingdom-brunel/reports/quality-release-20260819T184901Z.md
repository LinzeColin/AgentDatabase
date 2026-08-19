# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brunel-34/workspaces/isambard-kingdom-brunel`
- Phase: `release`
- Profile: `quick`
- Generated: `2026-08-19T18:49:01Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 11,
    "claims": 13
  },
  "sources_total": 11,
  "sources_train": 10,
  "sources_usable_train": 10,
  "sources_holdout": 1,
  "primary_sources": 10,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 3,
    "conversations": 1,
    "expression": 1,
    "external": 4,
    "decisions": 1,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 6,
    "已证实归属": 2,
    "存疑（有正面证据但另有他人署名）": [
      "src-b979dee5b871 11001081bsb.txt [A-byline] 另有他人署名：By Samver Rawson"
    ],
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "3 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 11,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Isambard Kingdom Brunel（1806-1859）的署名形态：\n  ① 1829 书信（letters00brun）：archive.org ",
    "citation": "Isambard Kingdom Brunel（1806-1859）的一手载体：1829 书信、1840 手稿、1857 Renkioi 报告、1870 子编传",
    "争议篇目数": 1,
    "P1 声称本人所著": 6,
    "未挂 attribution": 0
  },
  "namesake_separability": {
    "状态": "ok",
    "候选数": 1,
    "分不开": 0,
    "未覆盖": [],
    "字面同名未定政策": [],
    "出处": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brunel-34/namesake-gate.json"
  },
  "source_attribution": {
    "subject_origin": "historical",
    "声称本人所著的 P1 源": 3,
    "靠 A-* 署名证据认定": 0,
    "靠 attribution_basis 逐份点名认定": 3,
    "**未被逐份认领**": 0,
    "口径": "**判「有没有被逐份认领」，不判「认领得对不对」**——在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"
  },
  "fact_density": {
    "usable_train": 10,
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
    "已查语料件": 11,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "未核": 1,
      "干净": 8,
      "不适用": 1,
      "不可用": 1
    },
    "逐份": {
      "src-b0a018e88d61": {
        "words": 1001,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 1418.6,
            "panel_good": 8,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**"
          }
        },
        "verdict": "未核",
        "rate": null,
        "reason": "英文面板只命中 8 次 < 30 —— **样本量不够，不是「干净」**",
        "file": "letters00brun.txt"
      },
      "src-e26f969bb12b": {
        "words": 15100,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2219.9,
            "panel_good": 110,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 110／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 110／讹形 0）",
        "file": "b22280303.txt"
      },
      "src-dbcd11a9545f": {
        "words": 211070,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2448.0,
            "panel_good": 1616,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1616／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1616／讹形 0）",
        "file": "lifeofisambardki00brunuoft.txt"
      },
      "src-b979dee5b871": {
        "words": 224540,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2402.2,
            "panel_good": 1632,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1632／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1632／讹形 0）",
        "file": "11001081bsb.txt"
      },
      "src-6882e45e7b67": {
        "words": 210620,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2444.8,
            "panel_good": 1611,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1611／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1611／讹形 0）",
        "file": "india.history.resource.73330.txt"
      },
      "src-246958e8cd9b": {
        "words": 102530,
        "diagnostic_est_eft": [
          12,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2358.4,
            "panel_good": 675,
            "panel_bad": 4,
            "若无语种门会读到": 0.0059,
            "verdict": "干净",
            "rate": 0.0059,
            "reason": "英文讹字率 0.0059（正形 675／讹形 4）"
          }
        },
        "verdict": "干净",
        "rate": 0.0059,
        "reason": "英文讹字率 0.0059（正形 675／讹形 4）",
        "file": "memoirlifesirma00beamgoog.txt"
      },
      "src-98fae66c8896": {
        "words": 2761,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.1739；英文：锚 14.5<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2500）",
        "file": "memoriescientif00brun.txt"
      },
      "src-398ea6cca17d": {
        "words": 6373,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 574.3,
            "panel_good": 17,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "未核",
            "reason": "英文面板只命中 17 次 < 30 —— **样本量不够，不是「干净」**"
          },
          "德语": {
            "语域": "德语",
            "anchors_per_10k": 36.1,
            "panel_good": 12,
            "panel_bad": 20,
            "若无语种门会读到": 0.625,
            "verdict": "不可用",
            "rate": 0.625,
            "reason": "德语讹字率 0.6250（正形 12／讹形 20）"
          }
        },
        "德语附加": {
          "h→b率": 0.0,
          "h→b样本": 13,
          "变音符每千词": 2.0,
          "h→b坏": false,
          "变音符湮灭": true
        },
        "verdict": "不可用",
        "rate": 0.625,
        "reason": "德语讹字率 0.6250（正形 12／讹形 20）　（两语域都适用，取更差的一侧）　★ **长 s 之外还坏了**：**变音符湮灭**（2.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形",
        "file": "papers00brun.normalized.txt"
      },
      "src-e0ad337e12b8": {
        "words": 7799,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2340.0,
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
        "file": "railwayeccentri00brungoog.txt"
      },
      "src-1550ff2d709d": {
        "words": 11918,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2436.7,
            "panel_good": 85,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 85／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 85／讹形 0）",
        "file": "broadgaugebancg00unkngoog.txt"
      },
      "src-9c575b47bde7": {
        "words": 119189,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2378.8,
            "panel_good": 886,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 886／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 886／讹形 0）",
        "file": "historyofgreatw00seko.txt"
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
    "shared_anchor": "⚠ 只列不判，须逐组人工读：32 题里没有跨题共享的语料片段——**无从比对，不是通过**",
    "quote_in_span": "没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；语料若含整版扫图，须由读过原文的人写出每篇的起止行",
    "answer_surface_leak_baseline_source": "unknown",
    "answer_surface_leak": "✓ 总体均长比 1.28（门 ≤1.3）　候选更短 8/32 = 25%（门 ≥25%）；表面特征最高 表面特征（定向可利用率，门 ≤75%）：",
    "unsourced_names": "⚠ **1 个不是一手依据**（只列不判）——拿它撑承重句之前，先知道它薄在哪：",
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
    "可用来源": 10,
    "**按内容去重后的作品数**": 8,
    "虚高": 1.25,
    "未声明的重复对": 0,
    "已声明的重复对": 3,
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
      "**第一人称字节占比**": 0.7239,
      "第三人称": 0.2761,
      "作者自供但第三人称写的（communicated）": 0.0,
      "未标（unknown）": 0.0,
      "已标的份数": 11,
      "★": "**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，答的是「谁署名」；本项答的是「他本人说了多少」。Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。"
    },
    "本人所著的 train 源数": 7,
    "train 源总数": 11,
    "本人所著字节": 4257252,
    "train 总字节": 5837423,
    "own_voice_ratio": 0.7293,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 4112458,
    "**判据说未核验的**": 1,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-98fae66c8896",
        "原因": "语种判为 **?**（en=0.002 de=0.002 fr=0.002）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 8.9,
    "**立场句/万字**": 0.11,
    "其中不含第一人称的": 42,
    "读不到正文的": [],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 6,
    "**疑似著录卡**": {},
    "读不到正文的": [],
    "计数": "0 份 P1 像是「著录方描述这份文献」而不是文献本身",
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
    "第一人称覆盖率": 0.125,
    "状态": "**候选：基线可能不入戏**（第一人称覆盖率 0.125 < 0.4）",
    "**这几条值得人去读一眼**": [
      "case-known-1",
      "case-known-2",
      "case-boundary-1",
      "case-boundary-2",
      "case-trajectory-1",
      "case-trajectory-2",
      "case-contrast-1",
      "case-contrast-2"
    ],
    "★ 口径": "按整份载荷算第一人称覆盖率，**不判单条**——中文成句常省主语，Harvey #103 的 `hv-decoy-01` 通篇无「我」而完全是入戏的。\n★★ **这是候选名单，不是判决**：阈值在 22 个已判分人物上拟合，对第 23 个人没有保证。**去读原文，看它是在扮演这个人还是在介绍这个人。**"
  },
  "corpus_ceiling": {
    "读的是": "入库 attest（口径同发布门）",
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brunel-34/workspaces/isambard-kingdom-brunel/evidence/source-ledger.jsonl",
    "一手份数": 10,
    "台账总份数": 10,
    "一手占比": 1.0,
    "有材料的道数": 5,
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
    "最优选法": "把 src-b0a018e88d61 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 11,
    "声称公有领域": 11,
    "不声称（不判）": 0,
    "有据可查": 0,
    "有结论无依据": 11,
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
    "实测声明": 4,
    "同段带数": 1,
    "**光说不给数**": 3,
    "诚实弃权（不计问题）": 0,
    "**逐条**": [
      "断言/clm-000000000009　「实测」：数据与试验先行：以模型试验与实测数据支撑设计决策（GWR 轨道、船体试验）。",
      "judge_payload.v1.json/case-tool-use-2　「实测」：其一，凡数字必验算。轨距、坡度、弯道半径、Box 隧道长度，逐项与勘测图、董事会会议记录核对。我造 Great Western 号时以船长日志为记、以实测航速为准；史书若无同等的一手出处可核，先当它可疑。",
      "judge_payload.v1.json/case-refusal-stop-2　「实测」：没有数据，就说没有数据。我建桥、造船、铺铁路，从不靠猜测施工——每一段路基、每一根铁肋，都要先过试验、拿到实测数字，才有资格画进图纸。私人未公开的细节？我一向对私事守口如瓶；那不是工程档案，没有可查证的记录，就不该被硬造"
    ],
    "口径": "借了实测的权威却没交出实测的内容。**两条出路：把数补上，或改成弃权式**——弃权不会被报出，它是诚实的。"
  },
  "evidence_per_claim": {
    "断言条数": 13,
    "source_ids": "逐条各异（非空 13/13，不同取值 10）",
    "evidence_clusters": "逐条各异（非空 13/13，不同取值 10）",
    "counter_source_ids": "整批都空（非空 0/13，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 7,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 9,
    "来源数": 11,
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
      "   substantive_lines: 55",
      "   bookkeeping_lines: 0",
      "   payload_lines: 55",
      "   bookkeeping_ratio: 0.0",
      "   payload_ratio: 1.0"
    ]
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "     0.0%  boundaries.md          clm-00000000000d",
      "           低估商业与政治阻力：宽轨选择引发长期争论、Great Eastern 财务失败，显示其对商业/政治层面阻力的预判不足。…",
      "",
      "低于 10% 的 44 处 —— **只列不判，须逐条看完**。",
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
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-brunel-34/workspaces/isambard-kingdom-brunel/audit/source-coverage.json），**未核验**（不是通过）"
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
  "eval_results": 64,
  "candidate_overall": 0.8416,
  "baseline_overall": 0.5941,
  "candidate_baseline_delta": 0.2475,
  "suite_candidate_means": {
    "known": 0.85,
    "boundary": 0.86,
    "voice": 0.81,
    "trajectory": 0.9,
    "contrast": 0.7,
    "fact-preservation": 0.95,
    "style-decoy": 0.925,
    "task-completion": 0.815,
    "planning-fidelity": 0.85,
    "tool-use": 0.83,
    "capability-calibration": 0.625,
    "refusal-stop": 0.92,
    "long-horizon": 0.85,
    "identity-routing": 0.85,
    "anonymous-fidelity": 0.91,
    "token-efficiency": 0.82
  },
  "suite_single_drag": {
    "未过阈值的套组": 0,
    "状态": "有阈值的套组都过了——无需诊断",
    "口径": "这只是「修哪里」，不是「该不该过」。**门还是门。**另：**「知道该改哪一道」与「知道该怎么改」是两件事**——Nightingale #112 那一道改完从 0.760 掉到 0.705。"
  },
  "checker_census": {
    "负对照可用": 92
  },
  "claim_coverage_checked": "实际检查 11/13 条（其中按引文判据 0 条；语料元断言 0、无实体无引文 2 未纳入）",
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

- `content.decorative-citation`: 存在装饰性引用：断言挂的来源正文里找不到其关键实体
- `content.no-quotes-to-verify`: 引文核验**没有可核的对象**（不是通过）：语料读到了，而断言与答案里**一条引文都没扫到**——本产品的立身之本是能出示一手逐字引文，一条都没有本身就是问题

## Warnings

- `corpus.longs-corruption`: **1 份语料的长 s 讹字率超过 20%**——esse→esfe、such→fuch，份数／分档／字数三样都是真的，所以既有的门都放行了；**从这些文件里取不出任何可核的逐字引文**。★ 连带射程：`check_source_dedup` 对这些源的读数**不作数**——它读到的低值分不清「确实不同源」与「同源但字形认不出来」，**判重门对它们的沉默不构成「互相独立」的证据**（全库 245 对已声明同源实测中位 0.6709、低于门仅 1.6%，判据整体是好的；只有涉及本表这些源时它失去分辨力）。逐份见 metrics.longs_corruption。　`src-398ea6cca17d` papers00brun.normalized.txt —— 德语讹字率 0.6250（正形 12／讹形 20）　（两语域都适用，取更差的一侧）　★ **长 s 之外还坏了**：**变音符湮灭**（2.0/千词，干净德语件是 69.9–123.4）——逐字引用会印出作者没写的形，**不可做逐字引文**
- `eval.baseline-not-capability-evidence`: 32/32 条基线不可作能力证据（{'unknown': 32}）——**此产物的 delta 不得用于支持「比裸模型强」这类结论**；它只说明产物比该对照写得好
