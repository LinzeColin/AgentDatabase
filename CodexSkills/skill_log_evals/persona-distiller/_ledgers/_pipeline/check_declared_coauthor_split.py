#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_declared_coauthor_split.py —— **书自己在序言里写明「哪部分是谁写的」**

## 为什么有这件

2026-08-13 Dewey #190 阶段 3 取引文之前，打开《Ethics》(1908) 的序言，逐字读到：

> As to the respective shares of the work for which the authors are severally
> responsible, … **Part I. has been written by Mr. Tufts, Part II. by Mr. Dewey,
> and in Part III., Chapters XX. and XXI. are by Mr. Dewey, Chapters XXII.-XXVI.
> by Mr. Tufts.**

按这段声明逐段量：三份《Ethics》各 21 万词，**Tufts 占 50.7%**
（Part I 29.1% ＋ Part III 第 XXII–XXVI 章 21.6%），Dewey 只占 45.0%。
而台账把整册记成 `tier=P1`「他的」——**三份合计约 32.6 万词挂错了人。**

★ 这不是「著录字段有两个名字」那件事。全库 **376 行** `tier=P1` 而 `author` 有多位，
  绝大多数是**编者/译者**（`Lincoln, Abraham; Perry, Bliss, ed`、
  `Kant; Hartenstein`）——那种情况下主体确实是作者。
  真正致命的信号是**正文自己声明了分工**：一部合著书里，整整几部分是别人写的。
  [[creator-field-is-not-authorship]]、[[related-to-him-is-not-written-by-him]]

## 判什么

在每份语料的**前 10% 或前 15 万字符**（序言区）里找这类声明：

    Part I. has been written by Mr. Tufts
    Chapters XX. and XXI. are by Mr. Dewey
    the chapters on X are by Professor Y

命中且**归属人里出现主体以外的名字** ⇒ ✗ 红（rc=1）：这份语料里有明确不是他写的部分。

★★ **只有形态①（明写分工）判红**。形态②（题名页共同署名而无分工声明）**只报不判**：
   它靠版式识别署名，而题献行、出版社行、地名在版式上跟署名一模一样。
   收敛过程实测：**1038 → 49 → 32 → 9 → 109 → 89 条**，每一步都是读了命中之后
   补一条约束（全大写／只看前 4000 字／出版社印厂译者／人名词形／完整主体名／折叠空白）。
   ① 全库 **4 份，逐条核过全是真的**；② 85 份是**线索清单，要人读一眼**。
   把 ② 算进红会变成一道永远红的门。[[a-red-that-can-never-turn-green-is-not-a-signal]]

★ 本件**只报「书自己说了什么」**，不去判某一段到底是谁写的——
   那要靠分部边界，边界定位不到时**说未判，不许猜**。
   能定位到就顺带把词数占比算出来（Dewey 那三份就是这样量到 50.7% 的）。

★ 反过来也**不许**把「没找到声明」当成「没有合著」——
   没声明只是没证据，本件对它不置一词。[[negative-capability-claims-need-evidence-too]]

## 用法

    python3 check_declared_coauthor_split.py --workspace <工作区> --subject Dewey
    python3 check_declared_coauthor_split.py --scan _corpora
    python3 check_declared_coauthor_split.py --self-test

退出码：0＝没有「划归他人」的声明；1＝有；4＝读不到语料（**未判**）
"""
import argparse
import glob
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CORPORA = HERE.parent.parent / "_corpora"

# 序言区：前 10%，但至少 20000、至多 150000 字符
def _front(text: str) -> str:
    return text[:max(20000, min(150000, len(text) // 10))]


# 「哪几部分 由 谁 写」——单元词 + 归属动词 + 人名
UNIT = r"(?:Parts?|Chapters?|Books?|Sections?|Appendix|Appendices)"
ROMAN = r"[IVXLCivxlc]+\.?"
# ★ 人名用**具名组**：`units` 是 (?P<units>…) 占了第 1 组，
#   写 `m.group(1)` 取到的是单元号（自测当场抓到：who 全成了 "I."／"XX. and XXI."）。
NAME = r"(?:Mr\.|Mrs\.|Miss|Dr\.|Prof(?:essor)?\.?|Sir)?\s*(?P<who>[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,})?)"
DECL = re.compile(
    rf"{UNIT}\s+(?P<units>{ROMAN}(?:\s*(?:,|and|to|-|–)\s*{ROMAN})*)\s*"
    rf"(?:has been|have been|is|are|was|were)?\s*(?:written\s+)?by\s+{NAME}",
    re.I)

# 「分工」这个话题本身的标记词——命中才认为这是一段分工声明，
# ★ 只靠上面的正则会把「Chapter X by Mr. Smith」这种**引用别人的书**也捞进来。
# ★★ 第二种形态（2026-08-13 同一天撞到）：**题名页共同署名，而全书没有分工声明**。
#   《Letters from China and Japan》(1920) 题名页：
#     「BY JOHN DEWEY, Ph.D., LL.D. … AND ALICE CHIPMAN DEWEY  Edited by EVELYN DEWEY」
#   序言：「John Dewey … and his wife, Alice C. Dewey, **who wrote the letters**」。
#   这本书**没有**「Part I 由谁写」那种声明，上面的 DECL 一条都抓不到——
#   而它是 Dewey 的 conversations 道**唯一**的源。
#   实测：逐封署名 0 处；唯一可用信号是写信人怎么称呼配偶
#   （只出现 `Mamma` ⇒ John；只出现 `Papa`/`your father` ⇒ Alice）。
#   按日期头切 112 段之后：John 19.6%／Alice 11.3%／**归属不了 69.1%**。
#   ⇒ 本件只负责**报出「这是合著且没有分工声明」**，逐篇归属要另做（结果写台账）。
#   ★ 两个署名之间可能隔着一长串头衔：真例里
#     「BY JOHN DEWEY, Ph.D., LL.D. Professor of Philosophy in Columbia University AND …」
#     中间**71 个字符**——第一版写 {2,60} 一条都抓不到，自测当场抓到。
BYLINE = re.compile(
    r"\bBY\b[ \t]+(?P<span>[^\n]{2,140}?)\bAND\b[ \t]+"
    # ★ 续接词元允许**混入小写**：OCR 会把 `ALICE CHIPMAN DEWEY` 打成
    #   `ALICE CfflPMAN DEWEY`——只认全大写的话，**当初 motivate 这一档的那个例子
    #   自己就落到射程外了**（[[a-gates-scan-set-is-smaller-than-reality]]，今天第四次）。
    r"(?P<other>[A-Z][A-Z.\'\-]{2,}(?:[ \t]+[A-Z][A-Za-z.\'\-]{2,}){0,2})")

# 题名页上，人名后面常跟一长串头衔；截到第一个头衔词为止。
TITLE_WORD = re.compile(
    r"^(PH|LL|D|M|A|B|SC|LITT|F|R|S|ESQ|JR|SR|PROFESSOR|PROF|DR|MR|MRS|MISS|SIR|"
    r"OF|IN|THE|AT|LATE|EMERITUS|UNIVERSITY|COLLEGE|SCHOOL|DEPARTMENT)[.,]?$", re.I)


STOP_TOK = {"HIS","HER","THEIR","ITS","IT","THE","A","AN","OF","IN","AND","TO","BY",
            "DECEASED","RELATIVE","COMRADE","FRIEND","OLD","LATE","ANALYTICAL","WISE",
            "COMPANY","SONS","PRESS","RIGHTS","RESERVED","OTHER","ALL"}


def _looks_like_person(name: str) -> bool:
    """像不像一个人名？**不像就不报。**

    ★ 收紧到 32 条之后逐条读，剩下的假阳几乎全是**题献行与形容词短语**：
      「BY HIS OLD COMRADE AND FRIEND」（Fröbel）、
      「…AND HIS DECEASED RELATIVE」（Marshall，19 份都是同一行）、
      「AND IT」「AND ANALYTICAL」「AND WISE」。
      它们都全大写、都跟在 BY…AND 后面，靠版式分不开——**只能靠词形**。
    判据：① 首字母缩写＋姓（`L. H. PAMMEL`），或
         ② ≥2 个词且**没有一个**落在停用词表里（`ALICE CHIPMAN DEWEY`）。
    """
    toks = [x for x in name.replace(".", ". ").split() if x.strip(" .")]
    if not toks:
        return False
    if any(x.strip(" .").upper() in STOP_TOK for x in toks):
        return False
    if re.match(r"^(?:[A-Z]\.\s*){1,3}[A-Z][A-Za-z'\-]{1,}$", name.strip()):
        return True
    return len([x for x in toks if len(x.strip(" .")) > 1]) >= 2


def _lead_name(span: str) -> str:
    """从 BY 与 AND 之间那一段里截出**第一个署名人**。

    ★ 第一版直接用一个非贪婪组当 `first`，实测被截成 `L. H`
      （“BY L. H. PAMMEL AND GEO. W. CARVER”）——于是「他人」报成了 Carver 自己，
      **方向正好反了**。改成先取整段、再按头衔词截断。
    """
    toks, out = span.replace(",", " , ").split(), []
    for tk in toks:
        if tk == ",":
            continue
        if TITLE_WORD.match(tk):
            break
        if not re.match(r"^[A-Z][A-Za-z.\'\-]*$", tk):
            break
        out.append(tk)
        if len(out) >= 4:
            break
    return " ".join(out).strip(" ,.")


BYLINE_WINDOW = 4000        # 只在最前面这一段里找——题名页就在那儿

# ★★ 题名页附近**不只有作者**：出版社、印厂、版权行、译者、编者都长成
#   「BY X AND Y」。收紧到 49 条之后逐条读，剩下的假阳全是这几类，
#   逐条钉成反例（每条都逐字取自全库真实命中）：
#     COPYRIGHT, 1898, BY J. G. COTTA'SCHE … AND ALL OTHER RIGHTS RESERVED   （版权行）
#     PRINTED BY W. CLOWES AND SONS                                          （印厂）
#     COPYRIGHT, 1922, BY HENRY HOLT AND COMPANY                             （出版社）
#     TRANSLATED FROM THE GERMAN BY FANNIE E. DWIGHT AND JOSEPHINE JARVIS    （译者）
NOT_AUTHOR_PRE = re.compile(
    # ★ 词干后面必须允许词尾：写 `translat\b` 匹配不上 "TRANSLATED"（词没断），
#   译者那条假阳因此漏网——自测当场抓到。
    r"(copyright|print\w*|publish\w*|translat\w*|edit\w*|revis\w*|compil\w*|"
    r"electrotyp\w*|entered according)[^.]{0,60}$", re.I)
NOT_AUTHOR_NAME = re.compile(
    r"\b(COMPANY|CO|SONS|BROTHERS|BROS|PRESS|LTD|INC|RIGHTS|RESERVED|"
    r"UNIVERSITY|SENATE|COMMITTEE|FRIEND|PUBLISHERS?)\b")

TOPIC = re.compile(
    r"respective shares|severally responsible|has been written by|"
    r"were written by|is by|are by|joint work|collaborat",
    re.I)


def declarations(text: str):
    """→ [(声明原句, 归属人)]。**纯函数**，只看序言区。"""
    front = _front(text)
    out = []
    for m in DECL.finditer(front):
        a = max(0, m.start() - 260)
        ctx = " ".join(front[a:m.end() + 60].split())
        if not TOPIC.search(ctx):
            continue                       # 不是分工声明，多半是在引用别人的书
        out.append((ctx[-300:], m.group("who").strip()))
    return out


def _is_subject(cand: str, subject: str) -> bool:
    """候选名是不是主体本人？**按词元子集判，不许只比姓。**

    ★★ 第一版写的是 `w.split()[-1] == sub.split()[-1]`（只比姓），
       于是《Letters from China and Japan》的共同署名人
       **Alice Chipman Dewey** 被当成了 John Dewey 本人 —— 妻子同姓，护栏当场失效。
       [[test-the-guard-against-this-persons-namesake]]：**同姓的人一个也挡不住。**
    ⇒ 只有候选的词元**全部落在**主体词元里才算同一人
      （`Dewey` ⊆ {john, dewey} 算；`Alice Chipman Dewey` ⊄ {john, dewey} 不算）。
    """
    ct = {w for w in re.split(r"[^A-Za-z]+", cand.lower()) if len(w) > 1}
    st = {w for w in re.split(r"[^A-Za-z]+", subject.lower()) if len(w) > 1}
    # ★★ **双向**：候选 ⊆ 主体（`Dewey` ⊆ {john, dewey}），
    #   或 主体 ⊆ 候选（`JOHN DEWEY Ph.D. LL.D` ⊇ {john, dewey}——题名页常带头衔）。
    #   ★ 这两条都成立时才算同一人；配偶 `ALICE CHIPMAN DEWEY` 两边都不成立
    #     （少了 `john`），所以**照样报得出来**。
    return bool(ct) and (ct <= st or st <= ct)


def joint_byline(text: str, subject: str):
    """→ [(署名原句, 另一位署名人)]。**题名页/序言里的共同署名**，没有分工声明也算。

    ★ 只在序言区找，且要求另一位**不是**主体、也不是「edited by」那一串。
    """
    # ★★★ 只在**最前 4000 字符**里找，且 `BY`/`AND` 必须是**全大写**。
    #   第一版用 re.I + 前 10%，全库报出 **1034 份**——绝大多数是正文里
    #   普普通通的 “determined by Fa, Es-, Ic, Jy and their phase relations”。
    #   [[read-the-hits-before-reporting-the-rate]]：**先读命中再谈比率。**
    #   代价：Title Case 的署名（“by John Dewey and Alice Dewey”）会漏掉——
    #   宁可少报也不要 1034 条噪声；漏掉的那一档写在射程里。
    # ★★★ **先把空白折叠**再匹配。题名页在原文里是
    #     「BY \n JOHN  DEWEY, Ph.D., LL.D. \n ... \n AND \n ALICE ...」，
    #   而我的自测夹具用的是**已经折叠好**的一行字符串——
    #   于是自测全绿、真文件一条都不命中（[[fixtures-cleaner-than-the-real-thing]]）。
    front = " ".join(text[:BYLINE_WINDOW].split())
    out, seen = [], set()
    for m in BYLINE.finditer(front):
        # ★★ **两个署名都要看**：不能只看后一个。
        #   Carver 那篇是 “BY L. H. PAMMEL AND GEO. W. CARVER”——
        #   只看后一个就把 **Carver 自己**报成了「他人」，方向正好反了。
        cands = [_lead_name(m.group("span")), m.group("other").strip(" ,.")]
        cands = [c for c in cands
                 if c and not _is_subject(c, subject) and _looks_like_person(c)]
        if not cands:
            continue
        other = cands[0]
        w = other.lower()
        if w in seen:
            continue
        # 出版社/印厂/版权行/译者/编者都不算共同署名——**窗口要够宽**：
        # 「TRANSLATED FROM THE GERMAN BY …」这一串就有 29 个字符，
        # 第一版只回看 24 个字符，当场漏掉。
        pre = front[max(0, m.start() - 80):m.start()]
        if NOT_AUTHOR_PRE.search(pre) or NOT_AUTHOR_NAME.search(other.upper()):
            continue
        seen.add(w)
        out.append((" ".join(front[max(0, m.start() - 90):m.end() + 40].split()), other))
    return out


def foreign(decls, subject: str):
    """→ 归属人里**不是主体**的那些（去重，保序）。"""
    seen, out = set(), []
    for _, who in decls:
        w = who.lower()
        if _is_subject(who, subject):          # ★ 同姓不算同一人，见 _is_subject
            continue
        if w not in seen:
            seen.add(w)
            out.append(who)
    return out


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★ 逐字取自《Ethics》(1908) src-dc899c319809 的序言
    real = ("As to the respective shares of the work for which the authors are "
            "severally responsible, while each has contributed suggestions and "
            "criticisms to the work of the other in sufficient degree to make the "
            "book throughout a joint work, Part I. has been written by Mr. Tufts, "
            "Part II. by Mr. Dewey, and in Part III., Chapters XX. and XXI. are by "
            "Mr. Dewey, Chapters XXII.-XXVI. by Mr. Tufts.")
    d = declarations(real)
    chk("★ 真例：《Ethics》序言那段必须被认出来", len(d) >= 1)
    chk("★ 真例：归属人里必须出现 Tufts（主体是 Dewey）",
        "tufts" in " ".join(x[1] for x in d).lower())
    chk("★ 真例：以 Dewey 为主体时，报出来的「他人」是 Tufts 而不是 Dewey",
        [w.lower() for w in foreign(d, "Dewey")] == ["tufts"])
    chk("★ 反向：以 Tufts 为主体时，报出来的是 Dewey",
        "dewey" in [w.lower() for w in foreign(d, "Tufts")])

    # ★★ 第二种形态：题名页共同署名（逐字取自《Letters from China and Japan》1920）
    byl = ("LETTERS FROM CHINA AND JAPAN BY JOHN DEWEY, Ph.D., LL.D. Professor of "
           "Philosophy in Columbia University AND ALICE CHIPMAN DEWEY Edited by "
           "EVELYN DEWEY NEW YORK E. P. DUTTON & COMPANY")
    chk("★★ 题名页共同署名必须报出来——它**没有**分工声明，DECL 一条抓不到",
        not declarations(byl) and len(joint_byline(byl, "John Dewey")) >= 1)
    chk("★★ OCR 把名字打花了也要认出来（真例：`ALICE CfflPMAN DEWEY`）",
        len(joint_byline("LETTERS FROM CHINA AND JAPAN BY JOHN DEWEY, Ph.D., LL.D. "
                         "FBOVBsaoB or Philosopht ii( CoiitniBiA TTmrBBBrTT "
                         "AND ALICE CfflPMAN DEWEY Edited by EVELYN DEWEY",
                         "John Dewey")) >= 1)
    chk("★★ **带换行的真版式**也要命中（夹具折叠过空白，真文件没有）",
        len(joint_byline("LETTERS FROM CHINA AND JAPAN\n\nBY\n\nJOHN  DEWEY, Ph.D., LL.D.\n"
                         "Professor of Philosophy\n\nAND\n\nALICE CfflPMAN DEWEY\n"
                         "Edited by EVELYN DEWEY", "John Dewey")) >= 1)
    chk("★ 独著题名页不许报",
        not joint_byline("HOW WE THINK BY JOHN DEWEY Professor of Philosophy", "John Dewey"))
    chk("★★ **配偶同姓**：Alice Chipman Dewey 不许被当成 John Dewey 本人"
        "（只比姓的护栏在这里当场失效）",
        not _is_subject("Alice Chipman Dewey", "John Dewey")
        and _is_subject("Dewey", "John Dewey"))
    # ★★ 真实误报（2026-08-13 全库跑出 1034 条，这是其中一条，逐字取自
    #    comfort-avery-adams／0004-conv-1908-vxxvii.txt）
    noise = ("There should therefore be a power-factor so definable that it is "
             "wholly determined by Fa, Es-, Ic, Jy and their phase relations, and "
             "thus independent of the number of phases.")
    chk("★★ 真实误报：正文里的 “determined by … and their phase relations” **不许**报",
        not joint_byline(noise, "Adams"))
    # ★★ 逐条取自收紧到 49 条之后仍然假阳的那几类（全库真实命中，逐字）
    for txt, why in [
        ("COPYRIGHT, 1898, BY J. G. COTTA'SCHE BUCHHANDLUNG NACHFOLGER. "
         "RIGHTS OF TRANSLATION AND ALL OTHER RIGHTS RESERVED.", "版权行"),
        ("PRINTED BY W. CLOWES AND SONS, STAMFORD STREET AND CHARING CROSS.", "印厂"),
        ("HUMAN NATURE AND CONDUCT COPYRIGHT, 1922, BY HENRY HOLT AND COMPANY", "出版社"),
        ("MOTHER-PLAY TRANSLATED FROM THE GERMAN BY FANNIE E. DWIGHT AND "
         "JOSEPHINE JARVIS EDITED BY ELIZABETH P. PEABODY", "译者"),
    ]:
        chk(f"★★ 真实假阳（{why}）不许报：{txt[:44]}…",
            not joint_byline(txt, "Dewey"))
    # ★ 而**真的**共同署名必须留住（Carver #127 已入库，1895 年那篇论文）
    cv = joint_byline("FUNGUS DISEASES OF PLANTS AT AMES, IOWA, 1895. "
                      "BY L. H. PAMMEL AND GEO. W. CARVER.", "Carver")
    chk("★★ 真例：Carver 那篇 “BY L. H. PAMMEL AND GEO. W. CARVER” 必须报", len(cv) >= 1)
    chk("★★ **方向不许反**：报出来的「他人」是 PAMMEL，不是 Carver 自己",
        cv and "pammel" in cv[0][1].lower() and "carver" not in cv[0][1].lower())
    for txt, why in [
        ("DESIGNED TO SERVE THE CAUSE OF HUMANE EDUCATION IS DEDICATED "
         "BY HER OLD COMRADE AND FRIEND", "题献行·形容词短语"),
        ("PUBLISHED FOR THE BENEFIT OF HIS WIDOW AND HIS DECEASED RELATIVE", "题献行·亲属"),
    ]:
        chk(f"★★ 真实假阳（{why}）不许报：{txt[-42:]}",
            not joint_byline(txt, "Frobel"))
    chk("★ 「edited by X」不算共同署名（编者是另一件事）",
        not joint_byline("THE WORKS OF DEWEY edited by Jo Ann Boydston and others",
                         "Dewey"))

    # ★ 负例①：引用别人的书，**不是**分工声明
    cite = ("For a fuller account see Chapter IV by Mr. Smith in the volume "
            "edited by the Society, and compare the bibliography below.")
    chk("★ 负例：正文里「Chapter IV by Mr. Smith」（引别人的书）不许报",
        not declarations(cite))

    # ★ 负例②：独著的序言
    solo = ("In preparing this book I have had the assistance of many friends, "
            "to whom my thanks are due. The whole of the work is my own.")
    chk("负例：独著序言不许报", not declarations(solo))

    # ★ 只看序言区：同样的句子放到正文很后面，不许报
    tail = "x " * 200000 + real
    chk("★ 只看序言区（前 10%／上限 15 万字符）——同句落在正文深处不许报",
        not declarations(tail))

    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}"
          "（真例逐字取自《Ethics》(1908) 的序言）")
    return 0 if ok == t else 1


def scan_ws(ws: pathlib.Path, subject: str):
    led = ws / "evidence/source-ledger.jsonl"
    if not led.is_file():
        return None
    hits = []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        p = ws / (r.get("local_path") or "")
        if not p.is_file():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        d = declarations(txt)
        fo = foreign(d, subject) if d else []
        jb = joint_byline(txt, subject)
        if fo:
            hits.append({"source_id": r.get("source_id"), "tier": r.get("tier"),
                         "split": r.get("split"), "title": (r.get("title") or "")[:52],
                         "形态": "① 声明了分工", "归给他人": fo,
                         "声明原句": d[0][0][-220:]})
        elif jb:
            hits.append({"source_id": r.get("source_id"), "tier": r.get("tier"),
                         "split": r.get("split"), "title": (r.get("title") or "")[:52],
                         "形态": "② **共同署名而没有分工声明** ⇒ 逐篇归属要另做",
                         "归给他人": [w for _, w in jb][:3],
                         "声明原句": jb[0][0][-220:]})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--subject",
                    help="主体姓名（如 `John Dewey`）；缺省时用工作区目录名整体"
                         "（`john-dewey` → `john dewey`）。★ **不要只给姓**："
                         "只给 `dewey` 会把题名页上带头衔的本人 `JOHN DEWEY Ph.D. LL.D` "
                         "当成他人，实测一下多报 100 条。")
    ap.add_argument("--scan", help="扫 _corpora 下全部工作区")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    targets = []
    if a.scan:
        for d in sorted(glob.glob(os.path.join(a.scan, "wip-*", "workspaces", "*"))):
            if os.path.isdir(d):
                targets.append(pathlib.Path(d))
    elif a.workspace:
        targets.append(pathlib.Path(a.workspace))
    else:
        print("★★ **未判**：要给 --workspace 或 --scan")
        return 4

    total, bad, nolead = 0, [], 0
    for ws in targets:
        subj = a.subject or ws.name.replace("-", " ")
        h = scan_ws(ws, subj)
        if h is None:
            nolead += 1
            continue
        total += 1
        for x in h:
            x["工作区"] = ws.name
            x["主体"] = subj
            bad.append(x)

    print(f"扫了 {total} 个有台账的工作区"
          f"{f'（另有 {nolead} 个没有台账，**未判**）' if nolead else ''}\n")
    if bad:
        print(f"✗ **{len(bad)} 份语料在序言里声明了分工，且有部分明确归给他人**：")
        for x in bad:
            print(f"  · {x['工作区']}／{x['source_id']}　tier={x['tier']} split={x['split']}"
                  f"　{x.get('形态','')}")
            print(f"      {x['title']}")
            print(f"      归给：{'、'.join(x['归给他人'])}（主体 {x['主体']}）")
            print(f"      声明：…{x['声明原句']}")
    else:
        print("✓ 没有「书自己声明某部分归他人」的语料")
    print("\n★ 射程：只报**书自己说了什么**。没找到声明**不等于**没有合著"
          "——那只是没证据，本件对它不置一词。"
          "\n★ 分部边界能定位时才算词数占比；定位不到就说未判，**不许猜**。")
    hard = [x for x in bad if x.get("形态", "").startswith("①")]
    print(f"\n★★ **只有 ① 判红**（{len(hard)} 份）。② 是**线索，不是判决**："
          "\n  它靠版式识别题名页署名，而题献行／形容词短语在版式上跟署名一模一样"
          "（实测「BY HIS OLD COMRADE AND FRIEND」「AND HIS DECEASED RELATIVE」×19）。"
          "\n  ⇒ ② 逐条要人读一眼；把它算进红会变成一道永远红的门。")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
