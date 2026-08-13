#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按题名把语料分到**六条研究道**，给出 `min_lanes` 的输入。阶段 2 的最后一件。

用法：
    python3 assign_lanes.py --raw <raw 目录>

六条道取自 `check_corpus_ceiling.py` 的 `LANES`（**去仓里读的，不是我定的**）：

**道的语义是从 35 个存量工作区的 `source-ledger.jsonl` 里实测出来的，不是我按字面猜的。**
（首版按字面猜，把 `timeline` 定成「自传/日记」、`decisions` 定成「判决书」，
 于是十个人里九个的 timeline 与 decisions 都是空的 —— 那是我的定义太窄。）

| 道 | **存量里实际装的** | 实例（存量原文件名） |
|---|---|---|
| `writings` | 书、论著、文集 | `11756487bsb` |
| `conversations` | 书信往还 | `briefwechselzwis00liebuoft`、`berzeliusundlieb00berzuoft` |
| `expression` | **对外的短篇表达**：期刊短文、讲词 | Roberts-Austen 的 6 篇 Nature 短文 |
| `decisions` | **他做判断的记录**：技术报告、专利、官方报告——**不只是判决书** | `imeche1895-alloys-research-third-report`、`03-slide-principle-1841` |
| `timeline` | **生平年表类，可以是第三方**：大学校史、ADB／DNB 传记条目、讣告、自传 | `chronikderunive00giesgoog`、`de_ADB_Liebig`、`06b-dibner-obituaries-clippings-NOT-HIS` |
| `external` | 别人写他的（分类器判为「二手」的） | `erklrungveranl00buffuoft` |

★ **`timeline` 与 `external` 都可以是第三方，区别在于**：
  `timeline` 回答「什么时候发生了什么」，`external` 回答「别人怎么看他」。

**两条硬规矩：**

① **不许把分不出来的塞进一条「空着的」道**——那会让 `min_lanes` 凭空多一道，
   而门只做算术、不问分道对不对
   （[[related-to-him-is-not-written-by-him]]／[[empty-default-swallows-unknown]]）。
   ★ **一手且不属前四道 ⇒ `writings`**，这是**剩余类不是默认值**：
     一份他署名、又不是书信/演说/判决/自传的文本，本来就是著述；
     且 writings 在有语料的人身上从不为空，落进去只可能让**道数不变**。
   ★ 首版真按「一律进未分道」写过，实测 **Marshall 73 份里 51 份未分道（70%）**，
     `lanes` 被压到 4 —— 那不是「他只有 4 道」，是**我的题名表太窄**。

② **`external` 由「二手」**且**题名不是年表类**决定。
   —— 首版写成「二手一律进 external」，于是
   《John Marshall and the Constitution; **a chronicle** of the Supreme court》(1919)、
   《Jefferson and his colleagues: **a chronicle** of the Virginia dynasty》、
   《**Calendar** of the correspondence of Thomas Jefferson》
   全被塞进 external，而**存量口径里第三方年表正是 `timeline` 那一道**
   （Liebig 的 timeline 装的就是大学校史 `chronikderunive00giesgoog` 与 ADB 条目）。
   ⇒ **二手 + 年表类题名 ⇒ timeline；二手 + 其余 ⇒ external。**
   反方向的错同样要防：他自己的书不能因为题名像评论而进 external。

★ 本工具**只按题名分**，是粗判。`check_paper_lanes.py` 会再问
  「这几道里有几道是纸面的」——**一道只有 1 份的道，多半是纸面的**，
  所以输出里逐道印份数，不只印道数。

★ 退出码：0=跑完；2=参数错；3=没有可分的文件。
"""
import argparse
import json
import pathlib
import re
import sys

LANES = ["writings", "conversations", "expression", "decisions", "timeline", "external"]

# 题名模式，按**优先级从高到低**匹配（一份只进一道——道数要能被门直接用）
PATTERNS = [
    # ★ 按存量实测放宽：**他做判断的记录**，含技术报告/专利/官方报告
    # ★★★ 2026-08-13 三处子串误配，**只加右边界不加左边界**——
    #   德语复合词把中心词放在末尾（`Bismarck+reden`、`Jahres+bericht`），
    #   加左边界会把它们一起误杀（文件里那条「`briefe` 必须无词边界」写的就是这个）。
    #     `opinion`  ⊂ 拉丁语 `opinionem`（Aristotle《De natura partus…adversus vulgatam opinionem》）
    #     `bericht`  ⊂ 德语 `berichtigter`（＝「校订过的」，Aristotle《kritisch-berichtigter Text》）
    #     `rede`     ⊂ 英语 `p-rede-cessors`（Aristotle《on his predecessors》）
    #   ⇒ 这三条把 Aristotle 的道数从真值 **1** 虚报成 **3**——正好压在 quick 的下限上，
    #     与 Leonardo #184（`letter` ⊂ `letterari`）、Plato #186（`dialogue`）同一类，这是**第三次**。
    #   ★ 全库前后实测：**0 个工作区受影响**（右边界保住了 `Bismarckreden` 等 18 份真演说集）。
    ("decisions", r"opinions?\b|judgment|judgement|decision|decree|ordinance|statute|"
                  r"proclamation|message of the president|verordnung|erlass|"
                  # ★ `leges`（拉丁语「法律」）加词边界：`leges` ⊂ 英语 **`colleges`**。
                  #   Dewey #190 实测：《Inventory of Philosophy Taught in American Col-leges》
                  #   被判成判决记录。与 `opinion`⊂`opinionem` 同族，**这是第四次子串误配**。
                  r"legge|editto|\bleges\b|constitutiones|justice of the peace|"
                  r"\breport\b|bericht(?:e|en|s)?\b|gutachten|patent|specification|"
                  r"state paper|staatsschrift|denkschrift|minutes of|protokoll"),
    # ★★ 2026-08-13 `letter` 加词边界：`letter` ⊂ 意大利语 **`letterari`**（＝「文学的」），
    #    于是 Leonardo 的《Frammenti **letterari** e filosofici》（文学与哲学残篇选，
    #    副题自印 FAVOLE-ALLEGORIE-PENSIERI-PAESI-FIGURE-PROFEZIE-FACEZIE）被判成书信。
    #    **后果不是分错一个格子**：那 2 份（同一部书的两个印本）是他 conversations 道的**全部**，
    #    lanes 因此从真值 2 虚报成 3 —— **正好压在 quick 的下限**，一个够不着的人被判成过门。
    #    同类先例就在下面三行：`oration` ⊂ `commemoration`。[[regex-must-clear-the-corpus-language]]
    #    ★ `briefe` **必须保持无词边界**：`bismarckbriefe`(×5)、`bismarck-briefe`(×1) 靠它命中。
    #    射程是穷举出来的，不是抽样：全库 92 份命中拆成**所嵌整词 14 类**，
    #    只有 `letterari`(×2) 是误配，其余 12 类（letters 38／correspondence 23／
    #    bismarckbriefe 5／briefe 4／briefwechsel 4／letter 4／carteggio 3／lettres 3／
    #    correspondance 2／briefen 1／dialogue 1／table-talk 1）全是真书信词汇。
    # ★★★ 2026-08-13 移除 `dialogue|dialog`：**自撰的对话体作品是著作，不是往来记录。**
    #   Plato #186 实测：conversations 报 7 份，**7 份全错**——
    #     4 份靠 `Dialog`／`Dialogue`（《Ausgewählte Dialoge》《Platonis Dialogi》
    #       《The Myths of Plato [extracted from the Dialogues]》《Dialogue on Laws》第十卷）
    #     2 份靠 `letter`（`together with a critical letter` —— **编者附的评论信**）
    #     1 份靠 `epistol`（`Platonis Convivium : cum epistola ad Thompsonum` —— **编者致 Thompson**）
    #   ⇒ 他的真值是 **1 条道**，而工具报 2 —— 与 Leonardo #184 同型
    #     （那次是 `letter` ⊂ 意大利语 `letterari`）。
    #   ★ `conversation`／`tischgespr`／`table talk`／`kolloqui`／`colloqui` **保留**：
    #     那些是**别人记下来的谈话**，本来就属这一道；`dialogue` 指的是作者写的体裁。
    #   ★★ 全库前后对比：只有 **Plato（4 份）** 与 **Rousseau（1 份，14 份里的 1 份）** 受影响，
    #     Rousseau 的道数不变 ⇒ **没有任何已交付人物的档位因此改变**。
    ("conversations", r"\bletters?\b|correspond|briefe|briefwechsel|epistol|"
                      r"\blettres?\b|\blettere\b|"
                      r"carteggio|conversation|tischgespr|tabletalk|"
                      r"table.?talk|kolloqui|colloqui"),
    # ★★ 2026-08-12 移除 `discourse|discours|discorsi`：**这个词分不出讲辞和专著**。
    #    17–18 世纪它就是「论」——实测本批两个人的 expression 道几乎全是专著：
    #      Rousseau  9 份里 8 份是《Discours sur l'origine … de l'inégalité》（论著，非讲辞）
    #      Machiavelli 10 份里 9 份是《论李维》（Discorsi / Discourses on the first decade）
    #    移除后它们落进 residual ⇒ writings，**道数不虚增**（见文件末尾 lane_of 的注释）。
    #    `oration` 加了词边界：`oration` ⊂ `commemoration`，把 Kant 的 KrV 英译本判成了讲辞。
    ("expression", r"speech|speeches|address|\borations?\b|sermon|reden?\b|"
                   r"orazioni|poem|poesie|songs|lieder|"
                   r"predigt|vortrag|commedie|comed"),
    # ★ 按存量实测放宽：年表类**可以是第三方**（校史、传记辞典条目、讣告）
    # ★★★ 2026-08-13 语种对称：自传词表**只有德语**，于是**同一部书按译本分道**。
    #   Ford #188 实测：《My Life and Work》的
    #     英文原本   → writings（`my life` 不在表里）
    #     德译本     → timeline（`mein leben` 在表里）
    #     意译本     → writings（`la mia vita` 不在表里）
    #   **一部书的道不该取决于你手上是哪个译本。** 道的定义里写着 timeline 含「自传」，
    #   所以补齐英/意/法/西，而不是把德语那条删掉。
    #   全库前后实测：**只有 Ford 一人受影响**（道数不变，逐道从 18/1/1 变成 9/10/1
    #   —— 反而消掉了两条只有 1 份的纸面道）。
    ("timeline", r"autobiograph|selbstbiograph|diary|journal intime|tagebuch|"
                 r"lebensbild|lebensschick|meine? leben|"
                 r"my life(?: and| in|,|$)|la mia vita|ma vie|mi vida|"
                 r"erinnerungen|reminiscence|"
                 r"memoir|confession|vita propria|chronik|chronicle|chronolog|"
                 r"obituary|nachruf|in memoriam|annals|annalen|jahrbuch|"
                 r"biographical dictionary|dictionary of national|allgemeine deutsche bio"),
]
DEFAULT_WRITINGS = r"work|works|writing|schriften|s[äa]mtliche|opere|scritti|" \
                   r"[oœ]uvres|treatise|essay|abhandlung|didactic|didakt|magna|" \
                   r"education|erziehung|pictus|janua|porta|principe|prince|" \
                   r"histor|geschichte|storia|critique|kritik|prolegomena|notes on"


TIMELINE_PAT = next(p for l, p in PATTERNS if l == "timeline")

# ★★ 覆盖规则：题名命中了某道的词，**而那本书其实是他的著作**。
#    2026-08-12 实测，676 份里 10 份中招，全落在两个人身上，
#    且**把 Kant 的道数从 6 顶到了 6**——deep 档要求 6 道，他是靠这三条假道够到的。
#
#    | 误配 | 实例 | 真相 |
#    |---|---|---|
#    | `chronolog` | `sämmtliche Werke : in chronologischer Reihenfolge` | **版本的编排方式**，不是生平年表 |
#    | `judgment`  | `Critique of judgment` | 《判断力批判》是著作，不是判决记录 |
#    | `oration` ⊂ `commemoration` | `Critique of pure reason : in commemoration of the centenary` | **子串误配**，同 `lister` ⊂ `callister` |
#    | `discourse` | `Discourses on the first decade of Titus Livius` | 《论李维》是专著，不是短篇讲辞 |
#
#    ★ 只对 conversations/expression/decisions/timeline 生效；命中即归 writings。
WORKS_OVERRIDE = [
    ("版本编排词不是体裁",
     re.compile(r"(?:s[äa]mmtliche|s[äa]mtliche|collected|complete)\s+werke"
                r"|werke\s*:?\s*in\s+chronolog", re.I)),
    ("`logic of judgments` 是哲学论文不是判决记录",
     # Dewey #190：《The Logic of Judgments of Practise》(1915) 靠 `judgment` 进 decisions。
     # 与 Kant《判断力批判》同型——**judgment 在哲学语域里是「判断」不是「判决」**。
     re.compile(r"logic\s+of\s+judgments?|judgments?\s+of\s+practi[cs]e"
                r"|theory\s+of\s+judgment|judgment\s+and\s+reasoning", re.I)),
    ("critique/kritik 是他的著作",
     re.compile(r"\b(?:critique|critik|kritik)\b", re.I)),
    ("discorsi/discourses 论某部史书是专著",
     # ★ 意大利语是 discorsi（无 u），英语是 discourses——第一版只写了英语那一支，
     #   正对照当场抓到：`Discorsi sopra la prima deca de Tito Livio` 没被覆盖。
     re.compile(r"(?:discours?e?s?|discorsi)\b[^,;]{0,24}\b(?:upon|on|sopra|sulla)\b[^,;]{0,20}"
                r"\b(?:first|prima|deca|decade)\b", re.I)),
]


# ★★ 2026-08-13：**画名不是判决记录。**
# Michelangelo #185 探源池 287 条里，`decisions` 判出 11 条——**11 条全是《最后的审判》**
# （西斯廷壁画）：`Michelangelo: the Last Judgment`、`Christ as Judge Surrounded by Saints
# (upper central section of the Last Judgment)`、`Study of Figures from Michelangelo's
# Last Judgment, Sistine Chapel`…… 命中的是 `judgment`。
# 与 Leonardo 的 `letter` ⊂ `letterari` 同一类，**区别是这次在抓源之前就抓到了**
# ——道分布是按题名先估的，没有先抓 60 份再发现。
# 射程实测：全库**已抓**语料里 `judgment|judgement` 只命中 1 条，
# 是 Kant 的 *Critique of judgment*，而它已被 WORKS_OVERRIDE 的 `critique` 一支救回 writings
# ⇒ **本次修改对存量 37 个工作区一条都不动**（已跑全库对比确认）。
# 命中后落进 residual ⇒ writings；按 lane_of 末尾的注释，residual **不会虚增道数**。
# ★ 编者附在版本后面的信，不是他的往来书信。
#   Plato #186 实测三份：`Philebus … together with a critical letter`（两个印本，Badham 致 Thompson）、
#   `Platonis Convivium : cum epistola ad Thompsonum`。
#   判法看**「随本版附上」这个结构**（`together with` / `cum` / `with a … letter`），
#   不是看有没有 `letter` —— 真正的书信集题名是「Letters of X」「Briefwechsel」那种。
EDITOR_APPENDED_LETTER = re.compile(
    r"(?:together\s+with|cum|with)\s+(?:an?\s+|the\s+)?(?:critical\s+|introductory\s+|prefatory\s+)?"
    r"(?:letters?|epistola[me]?)\b"
    # ★ `man of letters` 是成语「文人」，与书信无关。Rousseau #178 实测那 1 份
    #   《A dialogue between **a man of letters** and Mr. J. J. Rousseau》靠它进的 conversations。
    #   与 `letterari` 同族：**同一个词根，两种意思**。
    r"|\b(?:m[ae]n|wom[ae]n|people)\s+of\s+letters\b"
    r"|\brepublic\s+of\s+letters\b", re.I)

ARTWORK_NOT_DECISION = re.compile(
    r"last\s+judg[e]?ment|giudizio\s+universale|j[üu]ngste[sn]?\s+gericht|jugement\s+dernier",
    re.I)


def lane_of(title: str, is_secondary: bool) -> str:
    t = (title or "").lower()
    if is_secondary:
        # ★ 第三方的**年表类**归 timeline，不归 external（存量口径）
        return "timeline" if re.search(TIMELINE_PAT, t) else "external"
    for lane, pat in PATTERNS:
        if re.search(pat, t):
            if lane == "conversations" and EDITOR_APPENDED_LETTER.search(t):
                continue          # 编者随本版附上的信，不是他的往来 —— 继续试别的道
            if lane == "decisions" and ARTWORK_NOT_DECISION.search(t):
                continue          # 画名，不是判决记录 —— 让它继续往后试别的道
            if lane != "writings":
                for _why, ov in WORKS_OVERRIDE:
                    if ov.search(t):
                        return "writings"
            return lane
    if re.search(DEFAULT_WRITINGS, t):
        return "writings"
    # ★ **一手且不属前四道 ⇒ writings。这不是「默认值」，是正确的剩余类**：
    #   一份由他署名的文本，不是书信/演说/判决/自传，那它就是著述。
    #   ——它也**不会虚增道数**：writings 在任何有语料的人身上都非空，
    #     residual 落进去只可能让计数不变。真正会虚增的是把它塞进空着的道。
    #   ★ 首版写成「一律进未分道」，实测 Marshall 73 份里 51 份未分道（70%），
    #     `lanes` 被压到 4 —— 那不是「他只有 4 道」，是**我的题名表太窄**。
    return "writings" if not is_secondary and t.strip() else "未分道"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    a = ap.parse_args()
    raw = pathlib.Path(a.raw)
    mf, pf = raw / "_fetch-manifest.json", raw / "_primary.json"
    if not mf.exists() or not pf.exists():
        print("要先跑 fetch_ia.py 与 classify_primary.py", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(mf.read_text(encoding="utf-8"))["记录"]
            if r["status"] == "已取回"]
    prim = {o["identifier"]: o["档"] for o in json.loads(pf.read_text(encoding="utf-8"))["明细"]}
    if not recs:
        print("没有可分的文件", file=sys.stderr)
        return 3

    tally, detail = {}, []
    for r in recs:
        ti = r.get("ia_title")
        ti = "; ".join(ti) if isinstance(ti, list) else str(ti or "")
        lane = lane_of(ti, prim.get(r["identifier"]) == "二手")
        tally[lane] = tally.get(lane, 0) + 1
        detail.append({"identifier": r["identifier"], "道": lane, "title": ti[:70]})

    filled = [l for l in LANES if tally.get(l, 0) > 0]
    thin = [l for l in filled if tally[l] == 1]
    unassigned = tally.get("未分道", 0)

    print(f"{raw}｜{len(recs)} 份")
    for l in LANES:
        n = tally.get(l, 0)
        mark = "  ← **只有 1 份，很可能是纸面的道**" if n == 1 else ("  ← **空**" if n == 0 else "")
        print(f"  {l:<15}{n:>4}{mark}")
    print(f"  {'未分道':<15}{unassigned:>4}"
          + ("  ← **这些没有被塞进任何一道**（不许默认成 writings）" if unassigned else ""))
    # ★★★ 2026-08-13 Ford #188：**一道只有 1 份，而那 1 份的文本层是空的。**
    #   他的 `conversations` 道全部支撑是《Henry Ford letter to Judge R.A. Parker, 1923》
    #   —— 手写信的扫描件，OCR 只出了 **7 个词、42 字节**
    #   （全文：`Yea born, Mick af GPS Conry Jord`）。
    #   本工具原来只数文件个数，**不问那份文件里有没有字**，于是把它算成一条道。
    #   `check_paper_lanes.py` 抓的是另一种（一条源同时挂多道），够不到这一种。
    #   ⇒ 单份道逐份量词数；少于 EMPTY_WORDS 就明说**文本层空壳**。
    EMPTY_WORDS = 100
    empty = []
    for l in thin:
        ident = next((r["identifier"] for r in detail if r["道"] == l), None)
        f = raw / f"{ident}.txt" if ident else None
        if f and f.exists():
            n_w = len(re.findall(r"[A-Za-zÀ-ɏ\u0370-\u03ff]+", f.read_text(encoding="utf-8", errors="replace")))
            if n_w < EMPTY_WORDS:
                empty.append((l, ident, n_w))

    print(f"\n**lanes = {len(filled)}**（quick 要 3、standard/deep 要 6）")
    if thin:
        print(f"★ 其中 {len(thin)} 道只有 1 份：{'、'.join(thin)}"
              f" —— 去掉纸面道就只剩 **{len(filled) - len(thin)}** 道")
    for l, ident, n_w in empty:
        print(f"★★ **`{l}` 那唯一一份的文本层是空的**：{ident} 只有 **{n_w} 个词**"
              f"（下限 {EMPTY_WORDS}）—— 数得出一条道，**一个字都用不了**。")

    (raw / "_lanes.json").write_text(json.dumps(
        {"lanes": len(filled), "去掉纸面道后": len(filled) - len(thin),
         "逐道份数": {l: tally.get(l, 0) for l in LANES}, "未分道": unassigned,
         "★口径": "按题名粗判，一份只进一道；external 只由一手/二手分类定；"
                  "一手的剩余类归 writings（**不是默认值，且不虚增道数**）",
         "明细": detail}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def selftest() -> int:
    """★ 夹具**全部取自全库真 manifest 的 ia_title 原文**，不是我照着正则编的。
    （夹具比原文干净就等于没测——本项目已犯八次。）

    正例 12 条 = 2026-08-13 穷举全库 92 份 conversations 命中、
    拆出「命中词所嵌整词」得到的 14 类里，**判定为真书信的那 12 类各取 1 条**；
    反例是那 14 类里的误配类 `letterari`，**再加两条同族反例**
    （`letteratura`／`letterarie` 是我按同一构词法补的，标注清楚）。

    ★★ 反例红了可能是红得凑巧 ⇒ **正例必须同时是绿的**：只要有一条真书信被误伤，
    这次「修好」就等于把 12 类里的一类换成了另一类错误。
    """
    POS = [  # (题名原文, 来源工作区) —— 全部逐字取自 manifest
        ("Bismarck's letters to his wife from the seat of war, 1870-1871;", "bismarck-176"),
        ("The correspondence of William I. and Bismarck : with other letters", "bismarck-176"),
        ("Bismarckbriefe: 1844-1870 ; Originalbriefe Bismarcks an seine Gemahlin", "bismarck-176"),
        ("(Bismarcks) Briefe an Schwester und Schwager;", "bismarck-176"),
        ("Bismarck-Briefe: I. Familien-Briefe ; II. Politische Briefe", "bismarck-176"),
        ("Briefwechsel von Imm. Kant", "kant-179"),
        ("Letter signed by Luther Burbank to Mr. A. B. Swain", "burbank-183"),
        ("Carteggio displomatico e familiare", "machiavelli-177"),
        ("Lettres politiques confidentielles de M. de Bismarck, 1851-1858", "bismarck-176"),
        ("Correspondance diplomatique de m. de Bismarck (1851-1859)", "bismarck-176"),
        ("Julie oder die neue Heloise: in Briefen zweyer Liebenden", "rousseau-178"),
        ("Bismarck's table-talk", "bismarck-176"),
    ]
    NEG = [  # 必须**不**判成 conversations
        ("Frammenti letterari e filosofici", "leonardo-184（真误配，本次的起因）"),
        ("Storia della letteratura italiana", "同族反例，按同一构词法补"),
        ("Opere letterarie e scientifiche", "同族反例，按同一构词法补"),
        # ★★ 2026-08-13 Plato #186：conversations 报 7 份**全错**，下面逐字取自他的探源池
        ("Ausgewählte Dialoge;", "自撰的对话体作品是著作，不是往来记录"),
        ("Platonis Dialogi secundum Thrasylli Tetralogias Dispositi, Vol. V", "同上"),
        ("The Myths of Plato [extracted from the Dialogues]. Translated with introduction",
         "同上——`Dialogues` 指的是他写的体裁"),
        ("Plato contra atheos = Plato against the atheists ; or, The tenth book of the Dialogue on Laws",
         "同上"),
        ("Philebus; with introd., notes, and appendix; together with a critical letter",
         "`together with a critical letter` 是**编者附的评论信**，不是他的往来"),
        ("The philebus of Plato : with introduction, notes and appendix ; together with a critical letter",
         "同上（另一印本）"),
        ("Platonis Convivium : cum epistola ad Thompsonum",
         "`cum epistola ad …` 是**编者致某人**，不是他的往来"),
        ("A dialogue between a man of letters and Mr. J. J. Rousseau",
         "Rousseau #178 实测的那 1 份——同样是对话体作品"),
    ]
    # ★★★ 2026-08-13：自测原来直接拿 conversations 那条正则去比，
    #   **而真正做决定的是 `lane_of()`**（排除规则、WORKS_OVERRIDE 都在那里面）。
    #   于是我新加的三条排除写完之后，自测报「仍误配」——
    #   不是排除没生效，是**自测没经过被保证的那段代码**。
    #   [[a-checker-nothing-calls-is-not-a-checker]] 的第五种形态：检查不经过被保证之物。
    #   ⇒ 一律改走 `lane_of(title, is_secondary=False)`。
    def _judge(title):
        return lane_of(title, False)

    bad = 0
    print("正例（必须仍判 conversations）：")
    for ti, ws in POS:
        ok = _judge(ti) == "conversations"
        bad += 0 if ok else 1
        print("  %s %-62s [%s]%s" % ("✅" if ok else "❌ 误伤", ti[:62], ws,
                                     "" if ok else "  ← 真书信被这次收紧挡住了"))
    print("\n反例（必须**不**判 conversations）：")
    for ti, why in NEG:
        got = _judge(ti)
        ok = got != "conversations"
        bad += 0 if ok else 1
        print("  %s %-62s %s%s" % ("✅" if ok else "❌ 仍误配", ti[:62], why,
                                   "" if ok else "  ← 实判 %s" % got))
    # ===== 第二组：decisions 不许吃画名（Michelangelo #185）=====
    # ===== 第五组：Dewey #190 实测的两条 =====
    DEWEY_NEG = [
        ("Inventory of Philosophy Taught in American Colleges", "decisions",
         "`leges`（拉丁语法律）⊂ 英语 `col-leges`"),
        ("The Logic of Judgments of Practise", "decisions",
         "`judgment` 在哲学语域里是「判断」不是「判决」"),
    ]
    DEWEY_POS = [("Letters from China and Japan", "conversations"),
                 ("Address of the President: Delivered at the Annual Meeting", "expression")]
    print("\nDewey #190 实测（反例必须不判该道，正例必须判该道）：")
    for ti, wrong, why in DEWEY_NEG:
        got = _judge(ti); ok = got != wrong
        bad += 0 if ok else 1
        print("  %s %-56s %s%s" % ("✅" if ok else "❌ 仍误配", ti[:56], why,
                                   "" if ok else "  ← 实判 %s" % got))
    for ti, want in DEWEY_POS:
        got = _judge(ti); ok = got == want
        bad += 0 if ok else 1
        print("  %s %-56s → %-13s（应为 %s）" % ("✅" if ok else "❌ 被误杀", ti[:56], got, want))

    # ===== 第四组：语种对称（Ford #188，同一部自传的四个版本必须同道）=====
    SYM = [("My life and work", "英文原本"),
           ("Mein Leben und Werk. Unter Mitwirkung von Samuel Crowther", "德译本"),
           ("La mia vita e la mia opera", "意译本"),
           ("My Life and Work by Henry Ford", "英文另一印本")]
    got = {ti: _judge(ti) for ti, _ in SYM}
    same = len(set(got.values())) == 1
    bad += 0 if same else 1
    print("\n语种对称：同一部自传的四个版本必须落在**同一条道**")
    for ti, note in SYM:
        print(f"  {'✅' if same else '❌'} {note:<10} → {got[ti]:<12} {ti[:44]}")
    if not same:
        print(f"      ← 实得 {sorted(set(got.values()))}，**一部书的道不该取决于哪个译本**")

    # ===== 第三组：子串误配（Aristotle #187 探源池，逐字）=====
    SUB_NEG = [
        ("De natura partus octomestris adversus vulgatam opinionem libri decem",
         "decisions", "`opinion` ⊂ 拉丁语 `opinionem`"),
        ("Istoriai peri zoon / kritisch-berichtigter Text / Aristoteles ; mit deutscher Übersetzung",
         "decisions", "`bericht` ⊂ 德语 `berichtigter`（校订过的）"),
        ("Aristotle on his predecessors, being the first book of his Metaphysics",
         "expression", "`rede` ⊂ 英语 `p-rede-cessors`"),
    ]
    SUB_POS = [   # ★ 右边界必须**保住**这些德语复合词与真报告
        ("Bismarckreden, 1847-1895. Hrsg. von Horst Kohl", "expression"),
        ("Die Reden des Grafen von Bismarck-Schönhausen. 1", "expression"),
        ("Jahresbericht über die Fortschritte", "decisions"),
        ("Opinion of the Court delivered by Chief Justice Marshall", "decisions"),
        ("Alloys research third report", "decisions"),
    ]
    print("\n子串误配（反例，逐字取自 Aristotle 探源池）：")
    for ti, wrong, why in SUB_NEG:
        got = _judge(ti)
        ok = got != wrong
        bad += 0 if ok else 1
        print("  %s %-62s %s%s" % ("✅" if ok else "❌ 仍误配", ti[:62], why,
                                   "" if ok else "  ← 实判 %s" % got))
    print("\n★ 右边界不许误杀的（正例；德语复合词把中心词放在末尾）：")
    for ti, want in SUB_POS:
        got = _judge(ti)
        ok = got == want
        bad += 0 if ok else 1
        print("  %s %-52s → %-12s（应为 %s）" % ("✅" if ok else "❌ 被误杀", ti[:52], got, want))

    ART_NEG = [  # 必须**不**判 decisions —— 逐字取自 Michelangelo 探源池
        "Michelangelo: the Last Judgment",
        "Christ as Judge Surrounded by Saints (upper central section of the Last Judgment)",
        "Study of Figures from Michelangelo's Last Judgment, Sistine Chapel",
        "Trumpeting Angels and Damned Souls Being Pulled Down by Devils (lower center a",
        "The Last Judgment",
    ]
    DEC_POS = [  # 必须**仍**判 decisions —— 前三条逐字取自真 manifest，第四条标注为构造
        ("The Virginia and Kentucky resolutions of 1798 and '99; with Jefferson's original "
         "draught thereof. Also, Madison's report", "jefferson-175 真题名"),
        ("Rede des reichskanzlers fürsten Bismarck über das bündniss … (Nach dem amtlichen "
         "stenographischen bericht über die Reichstags-verhandlung", "bismarck-176 真题名"),
        ("Alloys research third report", "roberts-austen-135 同型（技术报告）"),
        ("Opinion of the Court delivered by Chief Justice Marshall",
         "★ **构造**：全库已抓语料里没有 judgment 命中的真判决书，"
         "这条用 `opinion` 一支，证明本次改动没碰别的分支"),
    ]
    print("\n画名不许判 decisions（反例，全部逐字取自 Michelangelo 探源池）：")
    for ti in ART_NEG:
        L = lane_of(ti, False)
        ok = L != "decisions"
        bad += 0 if ok else 1
        print("  %s %-72s → %s" % ("✅" if ok else "❌ 仍判 decisions", ti[:72], L))
    print("\n真决策记录必须仍判 decisions（正例）：")
    for ti, src in DEC_POS:
        L = lane_of(ti, False)
        ok = L == "decisions"
        bad += 0 if ok else 1
        print("  %s %-58s → %-12s [%s]" % ("✅" if ok else "❌ 误伤", ti[:58], L, src[:40]))

    print("\n" + ("自测通过：书信 正 %d／反 %d ＋ 画名 反 %d／正 %d，全绿"
                  % (len(POS), len(NEG), len(ART_NEG), len(DEC_POS))
                  if not bad else "★ 自测有 %d 条不通过" % bad))
    return 0 if not bad else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
