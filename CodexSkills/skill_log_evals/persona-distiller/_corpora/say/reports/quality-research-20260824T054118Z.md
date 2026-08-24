# Persona Distiller quality report

- Target: `/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/say`
- Phase: `research`
- Profile: `quick`
- Generated: `2026-08-24T05:41:18Z`
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
    "research_quote": "**有引文未在语料中找到**——未命中不等于伪造，须人工核对；但「改了 OCR 错字再当逐字引文」也落在这里。引文 67 条，切分后核验片段 57 个，未命中 11 个，长 s 还原后才命中 0 个｜⚠ 研究/01-writings.md: 「cherche à obtenir de l'autorité une protection féconde en mauvais résultats」｜⚠ 研究/01-writings.md: 「un produit terminé offre, dès cet instant, un débouché à d'autres produits」｜⚠ 研究/01-writings.md: 「superabundant article / vent」｜⚠ 研究/02-conversations.md: 「a greater number of the industrious find enn ployment」｜⚠ 研究/03-expression.md: 「ma méthode présente, au lieu de raisonnemens, des tableaux」｜⚠ 研究/03-expression.md: 「Je n'ai presque jamais été content de ma conversation」",
    "first_person_density": {
      "实质第一人称句": null,
      "密度/万字": null,
      "正文字符": 32189770,
      "★ 口径": "**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。"
    }
  },
  "quote_speaker": {
    "长逐字引文": 99,
    "**引到别人的话**": 0,
    "正文已注明出自他人（不判为误引）": 0,
    "★ 定位不到（未判，不是通过）": 27,
    "★★ 射程": "只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语"
  },
  "holdout_mention": {
    "字面提及": 1,
    "**其中点名了是哪一份的**": 1,
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
        "核过": 34,
        "**对不上**": [
          "L'ÉCONOMIE politique n'est pas la politique; elle ne s'occupe point de la distribution ni de la balance des pouvoirs; mais elle fait connaît",
          "je voulais que l'on pût y être initié en dépensant si peu d'attention, de tems et d'argent, qu'il fût honteux de les ignorer",
          "la richesse d'un homme, d'un peuple, loin de nuire à la nôtre, lui est favorable; et les guerres livrées à l'industrie des autres peuples, p",
          "This work does not pretend to furnish the means of becoming rich. It professes only to point them out.",
          "How is value given to a thing ? By giving it utility.",
          "The utility, the faculty they have acquired of being serviceable, gives them a value, and this value is riches.",
          "but you ought to understand by that word whatever is capable of satisfying the wants and desires of man such as he is. His vanity and his pa",
          "There is no other effective demand than that which is accompanied by the offer of a price",
          "this is precisely the case, when authority grants to a particular class of merchants the exclusive privilege of carrying on a certain branch",
          "when a government imposes on wine a tax, which raises to 15 sous the bottle what would otherwise be sold for 10 sous, what does it else, but",
          "one kind of production would seldom outstrip the rest, and its products be disproportionately cheapened, were production left entirely to it",
          "ce qui ouvre des débouchés aux produits de l'industrie ... d'où il résulte, quoiqu'au premier aperçu cela semble un paradoxe, que c'est la p",
          "L'homme dont l'industrie s'applique à donner de la valeur aux choses en leur créant un usage quelconque, ne peut espérer que cette valeur se",
          "Il y a toujours assez d'argent pour servir à la circulation et à l'échange réciproque des autres valeurs, lorsque ces valeurs existent réell",
          "La vente ne va pas, parce que l'argent est rare, mais parce que les autres produits le sont",
          "il est bon de remarquer qu'un produit terminé offre, dès cet instant, un débouché à d'autres produits pour tout le montant de sa valeur",
          "un prêtre va chez un marchand pour y acheter une étole ou un surplis. La valeur qu'il y porte est sous la forme d'une somme d'argent: de qui",
          "dans tout état, plus les producteurs sont nombreux et les productions multipliées, et plus les débouchés sont faciles, variés et vastes",
          "L'argent ne remplit qu'un office passager dans ce double échange; et, les échanges terminés, il se trouve toujours qu'on a payé des produits",
          "Il Trattato di Economia politica di G. B. Say, e la Ricchezza commerciale di Simonde, più tardi Sismondi, apparvero nel 1803.",
          "nella questione del general glut, non v'ha, io credo, che Sismondi e Malthus, i quali abbiano saputo resistere all'evidenza della teoria deg",
          "la solidité de l'esprit consiste à vouloir s'instruire exactement de la manière dont se font les choses qui sont le fondement de la vie huma",
          "Vous savez, messieurs, qu'on peut en être dédommagé de deux manières: soit par le bien-être qui résulte d'un besoin satisfait; soit par une ",
          "De toutes les consommations, la plus rapide est celle que l'on fait des produits immatériels: ils n'ont aucune durée; et si l'on veut que le",
          "un produit terminé offre, dès cet instant, un débouché à d'autres produits"
        ]
      },
      "02-conversations.md": {
        "引文数": 22,
        "核过": 18,
        "**对不上**": [
          "I think I have proved in my first letter that productions can only be purchased with productions: I do not therefore yet see any reason to a",
          "the hypothesis of unrestricted production is more favourable to your cause, because it is much more difficult to dispose of unlimited produc",
          "If they save, I say, that they promote industry and production... In expending it unproductively, the expenditure has not been [productive]",
          "What is this but an increase of prosperity?"
        ]
      },
      "03-expression.md": {
        "引文数": 36,
        "核过": 19,
        "**对不上**": [
          "ma méthode présente, au lieu de raisonnemens, des tableaux, et met en action ce que d'autres ont mis en théorie et en système",
          "il est deux sortes d'institutions dont il est nécessaire qu'ils s'occupent : celles qui doivent donner de bonnes moeurs aux hommes à venir, ",
          "le manouvrier qui boit en quelques heures ses profits de la semaine... calcule moins bien que cet ouvrier diligent qui, loin de dissiper ses",
          "Le premier il rapproche ce fait, insignifiant en apparence, de la déviation de la lune au-dessous de sa tangente; il mesure la rapidité de c",
          "Une vérité non contestée a souvent des conséquences que l'on conteste beaucoup. Elles ne sont pas exprimées ces conséquences; cherchez-les d",
          "Personne ne mit plus de soin que lui, n'employa plus de temps à se former un corps de doctrines; personne aussi, quand il fut formé, ne s'y ",
          "Les faits lui donnaient-ils raison? Il l'acceptait sans orgueil comme une conséquence prévue. Semblaient-ils témoigner contre lui, il les di",
          "On se plaint que chacun n'écoute que son intérêt, disait Jean-Baptiste Say, je m'afflige du contraire.",
          "Je n'ai presque jamais été content de ma conversation.",
          "J'ai quelquefois éprouvé une difficulté extrême à écrire certains morceaux. Une considération m'a soutenu. Si cela était facile, pensais-je ",
          "La richesse des nations se compose de la valeur échangeable de toutes les choses qu'elles possèdent, et cependant les nations sont d'autant ",
          "J'ai perdu une fenêtre, se disait-il, et le Trésor n'y a rien gagné.",
          "pris de / viï,batsa femme",
          "ma méthode présente, au lieu de raisonnemens, des tableaux",
          "Je n'ai presque jamais été content de ma conversation",
          "Si cela était facile... tout autre le ferait",
          "Les faits lui donnaient-ils raison?..."
        ]
      },
      "04-external.md": {
        "引文数": 6,
        "核过": 2,
        "**对不上**": [
          "It is remarkable, that he should throughout the whole of Book I. treat value as founded wholly upon utility, whereas in Book II. he seems to",
          "Personne ne mit plus de soin que lui, n'employa plus de temps à se former un corps de doctrines; personne aussi, quand il fut formé, ne s'y ",
          "La théorie des débouchés, en prouvant que chaque nation est intéressée à la prospérité de toutes les autres, exercera la plus heureuse influ",
          "nella questione del general glut, non v'ha, io credo, che Sismondi e Malthus, i quali abbiano saputo resistere all'evidenza della teoria deg"
        ]
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
    "合计": "155 条引文，对不上 78 条",
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
  }
}
```

## Errors

- `corpus.holdout-work-named-in-artifacts`: **建模者读得到的文件里有 1 处直接说出了 holdout 是哪一份**（书名／卷次页码／文件名／源 id）——这比「提到有个 holdout」严重得多，**它把那道题考什么也告诉了**。　[('02-conversations.md', 115)]
- `corpus.holdout-mentioned-in-artifacts`: **建模者读得到的文件里有 1 处提到 holdout**——知道「存在一份取不到的材料、它关于某某」已足够定位那道题。　[('02-conversations.md', 'holdout')]

## Warnings

- research.lane_quotes：78 条逐字引文回原文对不上——**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区
