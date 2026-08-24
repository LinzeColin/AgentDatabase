# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say`
- Phase: `synthesis`
- Profile: `quick`
- Generated: `2026-08-24T08:32:03Z`
- Result: **FAIL**

## Metrics

```json
{
  "skill_lines": 67,
  "ledger_counts": {
    "sources": 16,
    "claims": 15
  },
  "sources_total": 16,
  "sources_train": 12,
  "sources_usable_train": 12,
  "sources_holdout": 4,
  "primary_sources": 12,
  "primary_ratio": 1.0,
  "lane_source_counts": {
    "writings": 8,
    "conversations": 1,
    "expression": 3,
    "external": 0,
    "decisions": 0,
    "timeline": 0
  },
  "authorship": {
    "P1 声称为本人所著": 16,
    "已证实归属": 8,
    "**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定": "8 条无 A-* 证据，**已按已声明的归属依据放行**（依据本身由 check_attribution_basis 硬拦）"
  },
  "corpus_integrity": {
    "已扫": 16,
    "不是语料": 0,
    "可疑": 0,
    "口径": "**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——抓错了书、抓了译本当原本，本门一概看不见。"
  },
  "attribution_basis": {
    "subject_origin": "historical",
    "authority": "Jean-Baptiste Say（1767-1832）著作归属依据：① archive.org 目录 creator 字段（Say, Jean Baptist",
    "citation": "archive.org 目录检索 creator:\"Say, Jean Baptiste\" / creator:\"Say, Jean-Baptiste\"（num",
    "争议篇目数": 0,
    "P1 声称本人所著": 0,
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
    "usable_train": 12,
    "fact 类条数": 3,
    "**人物事实**（计入）": 3,
    "账本事实（不计入）": 0,
    "无可核内容": 0,
    "要求": 5,
    "口径": "每 5 条可用源至少 1 条**人物事实**，下限 5；每条须带专名或数字；**只说语料有多大的不算**",
    "work-method 条数": 1,
    "**可复用做法**（计入）": 0,
    "复述式（不计入）": 1,
    "方法口径": "至少 3 条**可复用做法**；可复用 = 有步骤**且**有验证/弃置判据。**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实",
    "**复述式 work-method**": [
      "clm-287701f6aa4a **连步骤都没有**：是一句概括不是一套做法"
    ],
    "**未达**": [
      "可核 `fact` 断言 3 条 < 要求 5 条（12 条可用源 ÷ 5） —— **语料里可核的具体事实没有进入断言层**；这正是 Galen #101 真 delta −0.1259 的根因",
      "可复用 `work-method` 断言 0 条 < 暂定 3 条（另有 1 条是复述式）—— **四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency 四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）"
    ]
  },
  "quote_layer": {
    "已扫文件": 0,
    "引文层问题": 0,
    "★★": "**一个文件都没扫到**——本项这一轮**没有起作用**，不是「查过没问题」"
  },
  "ocr_homoglyphs": {
    "已查语料件": 16,
    "含同形字的源": 0
  },
  "longs_corruption": {
    "分布": {
      "干净": 4,
      "不适用": 12
    },
    "逐份": {
      "src-f7154d6be8dd": {
        "words": 27041,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2292.8,
            "panel_good": 305,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 305／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 305／讹形 0）",
        "file": "catechismofpolit00sayj.txt"
      },
      "src-d9920ebbab87": {
        "words": 34468,
        "diagnostic_est_eft": [
          427,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0117；英文：锚 4.4<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.5000）",
        "file": "b29287571.txt"
      },
      "src-003d387aca63": {
        "words": 131322,
        "diagnostic_est_eft": [
          1598,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0227；英文：锚 3.1<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.3529）",
        "file": "bub_gb_N7JDAAAAcAAJ.txt"
      },
      "src-8249fec8789a": {
        "words": 678478,
        "diagnostic_est_eft": [
          3,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0038；英文：锚 2.2<500.0，若强行读 0.0000；德语：锚 0.2<15.0，若强行读 0.0681）",
        "file": "bub_gb_nGt2dzHrtIMC.txt"
      },
      "src-1695e00c1f47": {
        "words": 63102,
        "diagnostic_est_eft": [
          1013,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0029；英文：锚 2.7<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.1429）",
        "file": "catchismedco00sayj.txt"
      },
      "src-cb25bd63b578": {
        "words": 643917,
        "diagnostic_est_eft": [
          8052,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0006；英文：锚 2.1<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.1333）",
        "file": "courscompletdc00sayjuoft.txt"
      },
      "src-b1935dc2cb56": {
        "words": 94188,
        "diagnostic_est_eft": [
          998,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0290；英文：锚 3.8<500.0，若强行读 0.0000；德语：锚 0.5<15.0，若强行读 0.1667）",
        "file": "india.history.resource.35409.txt"
      },
      "src-0d7cfabc38d1": {
        "words": 56287,
        "diagnostic_est_eft": [
          0,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2325.4,
            "panel_good": 602,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 602／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 602／讹形 0）",
        "file": "letterstomrmalth00sayjrich.txt"
      },
      "src-7309a76950f4": {
        "words": 26871,
        "diagnostic_est_eft": [
          248,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.4<15.0，若强行读 0.0133；英文：锚 4.1<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.0000）",
        "file": "micro_IA40244320_0069.txt"
      },
      "src-4f99e70027da": {
        "words": 371204,
        "diagnostic_est_eft": [
          3899,
          2
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0079；英文：锚 5.7<500.0，若强行读 0.1176；德语：锚 0.1<15.0，若强行读 0.4118）",
        "file": "oeuvresdiverses00saygoog.txt"
      },
      "src-cfbc1f979683": {
        "words": 27940,
        "diagnostic_est_eft": [
          287,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0000；英文：锚 3.9<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2000）",
        "file": "olbieouessaisurl00sayj.txt"
      },
      "src-b68240fb3bd9": {
        "words": 27766,
        "diagnostic_est_eft": [
          499,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0058；英文：锚 1.8<500.0，若强行读 0.0000；德语：锚 0.4<15.0，若强行读 0.1111）",
        "file": "petitvolumeconte00sayj.txt"
      },
      "src-9ac3add24ba1": {
        "words": 316291,
        "diagnostic_est_eft": [
          3984,
          0
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.0<15.0，若强行读 0.0089；英文：锚 4.8<500.0，若强行读 0.0000；德语：锚 0.0<15.0，若强行读 0.2308）",
        "file": "traitedeconomie00saygoog.txt"
      },
      "src-342c06541c14": {
        "words": 103128,
        "diagnostic_est_eft": [
          140,
          1
        ],
        "逐语域": {},
        "verdict": "不适用",
        "reason": "**两个语域都不适用**（拉丁：锚 0.1<15.0，若强行读 0.0053；英文：锚 14.4<500.0，若强行读 0.0000；德语：锚 6.8<15.0，若强行读 0.0889）",
        "file": "tratadodeeconom01sayjguat.txt"
      },
      "src-a9248c41ada4": {
        "words": 258508,
        "diagnostic_est_eft": [
          15,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2449.1,
            "panel_good": 2049,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 2049／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 2049／讹形 0）",
        "file": "treatiseonpoliti00sayj.txt"
      },
      "src-47686e48abd4": {
        "words": 135493,
        "diagnostic_est_eft": [
          1,
          0
        ],
        "逐语域": {
          "英文": {
            "语域": "英文",
            "anchors_per_10k": 2414.4,
            "panel_good": 1008,
            "panel_bad": 0,
            "若无语种门会读到": 0.0,
            "verdict": "干净",
            "rate": 0.0,
            "reason": "英文讹字率 0.0000（正形 1008／讹形 0）"
          }
        },
        "verdict": "干净",
        "rate": 0.0,
        "reason": "英文讹字率 0.0000（正形 1008／讹形 0）",
        "file": "treatiseonpoliti01sayjuoft.txt"
      }
    }
  },
  "lane_scope": {
    "道文件": 6,
    "台账行": 16,
    "与台账不一致的道": [
      "05-decisions.md",
      "04-external.md",
      "06-timeline.md"
    ],
    "修法": "python3 scripts/emit_lane_scope.py <workspace>",
    "口径": "**只列不判**——全库实测 holdout 泄漏 0 处，差异全是分道记错"
  },
  "content_review": {
    "byline_in_carrier": "核过 16 条，指错 0 条，**没核 18 条（不是通过）**",
    "fraktur_mojibake": "⚠ **德文语料 0 份 —— 未核，不是通过**（「没有花体乱码」在空集上恒真；共读到 12 份）",
    "staged_not_ingested": "⚠ **未核，不是通过** —— `check_staged_but_not_ingested` 的明细里没有 `_corpora`（本人物可能压根没走过抓源台账）",
    "source_header_quotes": "头部引文 0 条，**正文里找不到 0 条**　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**",
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 70 条，切分后核验片段 64 个，未命中 11 个，长 s 还原后才命中 0 个｜⚠ 研究/01-writings.md: 「cherche à obtenir de l'autorité une protection féconde en mauvais résultats」｜⚠ 研究/01-writings.md: 「nella questione del general glut」｜⚠ 研究/01-writings.md: 「superabundant article / vent」｜⚠ 研究/02-conversations.md: 「a greater number of the industrious find enn ployment」｜⚠ 研究/03-expression.md: 「On ne plaint que chacun n'écoute」｜⚠ 研究/04-external.md: 「ne s'y attacha d'une manière plus inébranlable」",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 32189770,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 101,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 24,
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
    "可用来源": 12,
    "**按内容去重后的作品数**": 10,
    "虚高": 1.2,
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
        "引文数": 59,
        "核过": 59,
        "**对不上**": []
      },
      "02-conversations.md": {
        "引文数": 22,
        "核过": 22,
        "**对不上**": []
      },
      "03-expression.md": {
        "引文数": 29,
        "核过": 29,
        "**对不上**": []
      },
      "04-external.md": {
        "引文数": 6,
        "核过": 6,
        "**对不上**": []
      },
      "05-decisions.md": {
        "引文数": 12,
        "核过": 2,
        "**对不上**": [
          "il refusa cependant; sa conscience lui interdisait de concourir à l'application d'un système qu'il jugeait devoir être funeste à la France.",
          "la politique inquisitoriale glaçait tout homme consciencieux et d'un esprit indépendant. L'auteur se vit obligé de cacher son manuscrit comm",
          "M. Say fit un voyage à Sedan pour chercher à s'introduire dans une fabrique de draps",
          "c'est là que M. Say se fit ouvrier; son fils Horace, alors âgé de dix ans, lui servait de rattacheur",
          "J.-B. Say prévoyait la chute très-prochaine d'un système contraire au véritable intérêt des peuples; il craignait la perte qui ... résultera",
          "M. Say se fit donner par le Gouvernement la mission de visiter l'Angleterre pour en étudier l'état économique et pour en rapporter les infor",
          "Jean-Baptiste Say dédaigna le combat; il refusa de se commettre avec des gens qui ne parlaient ni la langue économique ni même la langue fra",
          "sa conscience lui interdisait de concourir à l'application d'un système qu'il jugeait devoir être funeste à la France",
          "il prit le parti de se retirer en réalisant un petit bénéfice",
          "il refusa de se commettre... il garda le silence le plus absolu"
        ]
      },
      "06-timeline.md": {
        "引文数": 20,
        "核过": 2,
        "**对不上**": [
          "Son enfance s'écoula dans cette ville industrieuse qu'il aima toujours à revoir",
          "il obtint d'aller, en compagnie de son frère Horace, achever en Angleterre ses études commerciales",
          "J'ai perdu une fenêtre, se disait-il, et le Trésor n'y a rien gagné.",
          "Son premier essai littéraire fut une brochure publiée en 1789 en faveur de la liberté de la Presse: il avait alors vingt-deux ans",
          "le premier numéro de la Décade philosophique, littéraire et politique ... parut au mois de floréal an II (avril 1794), avec cette épigraphe:",
          "Dans le mois de novembre 1799 (frimaire an viii), il fut nommé membre du Tribunal",
          "Le Mémoire à l'Institut était le précurseur du Traité d'Économie politique qui devait être publié quatre ans plus tard. Il parut pour la pre",
          "Il revint à Paris avec sa famille, en 1813",
          "ce fut, en 1815, un vif attrait pour le public qu'un cours de cette science ouvert à l'Athénée par J.-B. Say",
          "M. Say se fit donner par le Gouvernement la mission de visiter l'Angleterre",
          "Le Catéchisme d'Économie politique, publié pour la première fois en 1817, a eu de nombreuses éditions et a été traduit, ainsi que le Traité,",
          "Cet ouvrage a paru pour la première fois en 1817, et dès l'année suivante il fallut en faire une seconde édition",
          "En 1819, il en parut une quatrième [édition] avec des corrections et des augmentations considérables",
          "L'apparition des Nouveaux principes d'Économie politique de Malthus devint l'occasion d'une polémique qui fut livrée à l'impression. Six Let",
          "la chaire du Conservatoire elle-même ne fut ouverte qu'avec une modification dans le titre du Cours. Le mot de politique effrayait trop un p",
          "Les leçons écrites et professées étaient généralement extraites d'un travail ... publié ensuite en 1828 et 1829, en deux volumes, sous le ti",
          "ce n'est qu'après 1830 ... que Jean-Baptiste Say devait être appelé à professer au Collège de France l'économie politique proprement dite.",
          "Le 15 novembre 1832 il fut frappé d'une nouvelle attaque, qui devait être la dernière ... perdit bientôt connaissance, et, après une agonie "
        ]
      }
    },
    "合计": "148 条引文，对不上 28 条",
    "读不到正文的来源": [
      "src-d9920ebbab87",
      "src-003d387aca63",
      "src-7309a76950f4",
      "src-342c06541c14"
    ],
    "holdout 源数": 0,
    "通过": false
  },
  "own_voice": {
    "★★ 按 voice 字段算的声口分布": "本人物的台账**没有一份标了 `voice`**——**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。",
    "本人所著的 train 源数": 16,
    "train 源总数": 16,
    "本人所著字节": 19406077,
    "train 总字节": 19406077,
    "own_voice_ratio": 1.0,
    "★ 同名判据": "未启用（本人物没有 namesake-criteria.json）",
    "口径": "账本 author 命中人物姓氏的 train 源字节占比。**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。"
  },
  "stance_density": {
    "P1 字符合计": 3232109,
    "**判据说未核验的**": 8,
    "★ 未核验的逐条（不并进分母，也不算 0）": [
      {
        "source_id": "src-8249fec8789a",
        "原因": "语种判为 **?**（en=0.000 de=0.001 fr=0.000）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-1695e00c1f47",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.108）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-cb25bd63b578",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.106）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b1935dc2cb56",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.097）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-4f99e70027da",
        "原因": "语种判为 **fr**（en=0.001 de=0.000 fr=0.085）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-cfbc1f979683",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.100）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-b68240fb3bd9",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.093）——**本件只认英语，不是「这个人没有声口」**"
      },
      {
        "source_id": "src-9ac3add24ba1",
        "原因": "语种判为 **fr**（en=0.000 de=0.000 fr=0.099）——**本件只认英语，不是「这个人没有声口」**"
      }
    ],
    "第一人称（动词式）/万字": 5.1,
    "**立场句/万字**": 0.12,
    "其中不含第一人称的": 35,
    "读不到正文的": [
      "src-d9920ebbab87",
      "src-003d387aca63",
      "src-7309a76950f4",
      "src-342c06541c14"
    ],
    "★ 口径": "**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——Coffin 实测 73% 是 `I claim as my invention` 这一类，**专利型语料要另减一道**。",
    "★★ 参照（㉙ 六样本）": "Coffin 0.95/0.00、Bain 0.91/0.23、Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07"
  },
  "catalogue_entries": {
    "P1 份数": 16,
    "**疑似著录卡**": {},
    "读不到正文的": [
      "src-d9920ebbab87",
      "src-003d387aca63",
      "src-7309a76950f4",
      "src-342c06541c14"
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
    "台账": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say/evidence/source-ledger.jsonl",
    "一手份数": 12,
    "台账总份数": 12,
    "一手占比": 1.0,
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
    "最优选法": "把 src-f7154d6be8dd 扣作 holdout 即满足三项门",
    "拦路的": []
  },
  "rights_basis": {
    "源条数": 16,
    "声称公有领域": 0,
    "不声称（不判）": 16,
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
    "两边都有年份": 0,
    "有一边没年份": 16,
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
  "mental_models": 3,
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
    "source_ids": "逐条各异（非空 15/15，不同取值 13）",
    "evidence_clusters": "逐条各异（非空 15/15，不同取值 15）",
    "counter_source_ids": "整批都空（非空 0/15，不同取值 0）"
  },
  "claim_source_independence": {
    "检查的断言": 10,
    "**全部来源塌缩成一部作品的**": 0,
    "★ 其中**靠台账声明**判出的": 0,
    "参考·按连通分量多报的": 0,
    "作品组数（连通分量，仅供参考）": 14,
    "来源数": 16,
    "口径": "判「两份源是不是同一部作品」，**不判「引得对不对」**——**被引的源两两直接** 8 词片重叠都 ≥30%（以较短一侧为分母）才判塌缩；**不做传递闭包**。★ 或者**台账的 `derived_from` 已声明它们同源**——那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源",
    "塌缩的断言": []
  },
  "quote_attributed_source": {
    "长引文": 57,
    "挂错作品": 2,
    "版本差（作品对、逐字文本取自另一版）": 2,
    "不唯一（同句见于多份源，挂错也照样绿）": 40,
    "取不到正文的源": 0,
    "例": [
      "clm-3ab8c241850a：挂 ['india.history.resource.35409.txt', 'oeuvresdiverses00saygoog.txt'] → 实 ['courscompletdc00sayjuoft.txt', 'src-cb25bd63b578/courscompletdc00sayjuoft.txt']",
      "clm-e6e7f0321a3d：挂 ['bub_gb_nGt2dzHrtIMC.txt', 'letterstomrmalth00sayjrich.txt', 'oeuvresdiverses00saygoog.txt'] → 实 ['src-47686e48abd4/treatiseonpoliti01sayjuoft.txt', 'treatiseonpoliti01sayjuoft.txt']",
      "clm-a73d904e5fb9：挂 ['catechismofpolit00sayj.txt', 'treatiseonpoliti01sayjuoft.txt'] → 实 ['letterstomrmalth00sayjrich.txt', 'src-0d7cfabc38d1/letterstomrmalth00sayjrich.txt']",
      "clm-20174b23561b：挂 ['traitedeconomie00saygoog.txt', 'treatiseonpoliti01sayjuoft.txt'] → 实 ['src-a9248c41ada4/treatiseonpoliti00sayj.txt', 'treatiseonpoliti00sayj.txt']"
    ]
  },
  "answer_constraints": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "verbatim_pointer": {
    "状态": "cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）"
  },
  "activation_yield": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "anchor_coherence": {
    "退出码": 0,
    "输出": [
      "   100.0%  decision-policy.md     clm-661346a3e85f",
      "           **选择性不参与：对不值得的争论开头就声明不辩，晚年对\"不懂经济语言\"的新改革家保持绝对沉默**：1821 年《Letters to Mr. Malthus》第一封信开场即划界…",
      "",
      "低于 10% 的 0 处 —— **只列不判，须逐条看完**。",
      "  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。",
      "  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。"
    ]
  },
  "quoted_arithmetic": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say/evals/judge_payload.v1.json），**未核验**（不是通过）"
  },
  "delivery_denominators": {
    "状态": "输入不在（/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say/audit/source-coverage.json），**未核验**（不是通过）"
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

- research.lane_quotes：28 条逐字引文回原文对不上——**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区
