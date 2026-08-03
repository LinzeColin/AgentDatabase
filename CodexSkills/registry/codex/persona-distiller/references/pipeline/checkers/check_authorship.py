#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判一份语料能不能当「他的话」用（P1）——**要求正面证据，不接受「没有反证」**。

## 为什么要有这个门

Steinhardt 一轮实测：抓源子代理按刊物整本抓 PDF、按页切片、
然后**一律冠上人物前缀**（`ms_*_contact_essay_*.txt`）。
四份里没有一份是他写的——两份末尾署名 Lynn Schusterman 与 Adam Bronfman，
另两份是 HUC-JIR 与独立 minyan 的作者。

**它们进 `ingest.py` 时带的是 `--author "Michael Steinhardt"`。**
文件名前缀 + author 参数，两步就把别人的文章洗成了他的话。
其中一句「我小时候父亲教我的第一课是：慈善是我们付给这世界的房租」
本来必然会被我写成他与其父 Sol 的家世——那是 Lynn Schusterman 的父亲。

现有的门一个都拦不住：`quality_check.py` 不读原文，
`check_verbatim_quotes.py` 只查引文是否逐字出现在语料里
（**它会说「在」——因为那句话确实在语料里，只是不是他说的**），
`check_holdout_overlap.py` 查的是重复不是归属。

## 判据

P1 需要下列之一，且**把证据原文打印出来供复核**：

- `A-byline`   —— 显式署名：`By <人物名>`，**`By` 与名字之间允许敬称**
                  （`By SIR ALEXANDER FLEMING`——v0.0.0.54，Fleming #111 实测 7 份）
- `A-byline-standalone` —— **期刊署名不带 `By`**，名字独占一行、可带学位后缀、
                  行尾可以是逗号（合著者接在下一行）。v0.0.0.54 新增，四条收窄：
                  独占一行 / 落在文件前 30% / 行尾只许学位后缀与逗号句点 /
                  **有反证时一律不放行**（它比显式 `By` 弱）
- `A-editorial`—— 编者注：`[Remarks delivered by <人物名> ...]`
- `A-turns`    —— 真·逐字稿：≥2 个说话人标签各出现 ≥3 次，
                  **且同一标签后面跟的文字每次都不同**
                  （否则那是标题里的冒号——`<人物名>: 某某标题`
                   在导航/og:title/h1 里重复出现，旧判据把它当成了说话人标记）
- `A-masthead` —— 以他本人命名的**单作者站点报头**（v0.0.0.16，须显式声明且含其名）
- `A-copyright`—— **版权页**：行首 `COPYRIGHT … BY` 后跟其名（v0.0.0.18，专为扫描件）
- `A-signature-block` —— **来信／书评／讨论发言的末尾签名**：
                  名字独占一行且邻接机构地址或日期（v0.0.0.55，Fleming #111 实测 4 份）。
                  **位置不是判据，邻接的地址块才是**——这四份的署名落在 37%–75%。

## v0.0.0.55：字母间隔的展示排版

Fleming #111 的诺奖演说，标题页印的是

    AL E X A N D E R  F L E M I N G

排版为求视觉分量把字母拉开，OCR 忠实地把字母之间的空格也抄了下来，
**任何名字正则都匹配不上**。`despace_display()` 在比对前把这种行折回词形——
**归一只用于比对，不写回语料**，与 `check_quote_integrity` 的长 s 折叠同一条纪律。
反证也走归一后的文本，否则「把别人的名字拉开字母」就能绕过反向检查。

## Fleming #111 实测：35 → 13，以及**为什么停在 13**

他是本名册第一个语料主体为**期刊论文**的人物，四轮泛化每一轮都是真形态：
敬称（35→30）、独占署名（30→17）、末尾签名块（17→14）、字母间隔（14→13）。

**剩下 12 份不再往下放宽，理由逐类写明：**

- **`lysozyme-1922-prsb` 的署名在书眉里，形态是 `Mr. A. Fleming.`**——首字母 + 姓。
  **认它等于认下同名陷阱**：这个人物恰有 `A. Grant Fleming`，
  裸检索 `Fleming A` 时排第一。**这一条永远不加。**
- **`freelance-science-1952` 是他写的书评**，而被评那本书的署名 `By René J. Dubos`
  就印在开头。反证正确触发——**判据在干活，不是误报**。
- 合著与整版串栏那几份，**正确解法是按作者把文件切开再入库**（见上文），
  不是让判据认得更宽。

**判据的用处正是把这 12 份列出来交给人**，不是把它们变绿。

## v0.0.0.18：扫描件的署名页，以及本门看不见的那一类

Livermore #100 的 1940 年亲笔著作只有 OCR 文本可得，署名页成了

    BY
    JESSE 1. LIVERMORE          ← `L.` 认成 `1.`，且 BY 与名字分行

`BYLINE` 一条也匹配不上，**一份货真价实的亲笔著作被判成「无据」**。
新增 `A-copyright` 认版权页。写第一版时我给年份写了校验
（`1[5-9]\\d\\d|20\\d\\d`），在真件上仍然一条不中——那页印的是
`COPYRIGHT, 1040, BY`，**`1940` 也被 OCR 认错了**。
**定则：本判据不需要的字段就不要校验**，尤其当它来自最不可靠的那一层。

⚠ **本门按整份文件判归属，因此看不见「卷内换作者」。**
同一本书的前言署 `EDWARD JEROME DIES`，正文才是 Livermore 的；
整本以 `--tier P1 --author "Jesse L. Livermore"` 灌进去，
Dies 那句「Each move was touched with singular genius」就变成了他的自述。
`suspect_signature_lines()` 会把疑似他人署名行**列出来**，
但**精度不足以当反证**（同一本书上它也会命中 `NEW YORK`）。
**正确解法是按作者把文件切开再入库**，切法要留成可复核的脚本。

再做一次**反向检查**：文末若出现**别人**的身份署名
（`X is Chair of…` / `X is Managing Director of…` / `By <他人名>`），
一律降级并打印那一行。刊物型 PDF 的作者署名就在文末那一行。

## v0.0.0.10：按人物名参数化（本文件此前写死 Steinhardt）

写死一个人名的检查器**只能给一个人用**，于是它注定停在「靠记性跑的独立脚本」，
这正是 v0.0.0.9 记录里写下的已知缺口。现在名字由 `--name` 传入、
或由 `quality_check.py` 从 `meta.json` 的 `name` 字段自动取，
不再需要执行者记得改常量。

**取名字时不要用 `\\s+` 连接**：`First\\s+(?:Middle\\s+)?Last` 里
两个相邻量词会争抢同一段空白，在十几万字的文书上是灾难性回溯
（实测卡死 120 秒）。可选中间名**自带尾随空格**才是无歧义写法。

退出码：0 = 全部有据；2 = 有文件缺正面证据（列出）；3 = 用法错误。
"""
import argparse
import pathlib
import re
import sys


def build_patterns(full_name: str) -> dict:
    """由人物全名生成本检查器要用的全部正则。

    `full_name` 取 `meta.json` 的 `name`，例如 `Michael H. Steinhardt`
    或 `Julian Robertson`。判据只依赖**名 + 姓**，中间名一律当可选，
    这样两种写法互相都能命中（语料里写全中间名、账本里没写，反之亦然）。
    """
    tokens = [t for t in re.split(r"\s+", full_name.strip()) if t]

    # ★ v0.0.0.26：**「名 + 姓」是一个西方近代假设，名册里有大量人物不满足它。**
    #
    #   Galen #101 实测撞出两处：
    #     ① `build_patterns("Galen")` **直接抛**——「人物名至少要有名与姓两段」。
    #     ② `build_patterns("Galen of Pergamon")` 把 **`Pergamon`（一个地名）当姓**，
    #        于是 `--author "Galen"` 一条也匹配不上，
    #        `own_voice_ratio` 报 **0.0**——**而真值接近 1.0**。
    #        没有报错，没有警告：**一份 240 万词的亲笔语料被静默判成「他一个字也没写」。**
    #
    #   两类必须分开处理：
    #     · **单名（mononym）**：Galen、Hippocrates、Avicenna、Paracelsus、Rembrandt、孔子…
    #       识别标记就是那一个词本身。
    #     · **地名式后缀**：`X of Y` / `X von Y` / `X de Y` / `X da Y` / `X van Y`…
    #       **识别的是 X，不是 Y。** 「帕加马的盖伦」姓不是「帕加马」。
    #
    #   这不是为了 Galen 一个人开的口子：600 人名册跨 12 族与整部人类史，
    #   古典、中世纪、东亚人物普遍不是「名+姓」形态。
    EPITHET = {"of", "von", "van", "de", "da", "del", "della", "di", "du", "al", "ibn", "bin", "ben"}
    if len(tokens) >= 3 and tokens[1].lower() in EPITHET:
        # 「X of Y」：识别 X，Y 是地名／族名，**不是姓**
        first = last = re.escape(tokens[0])
        surname = tokens[0]
        tokens = [tokens[0]]
    elif len(tokens) == 1:
        # 单名：那一个词既是「名」也是识别标记
        first = last = re.escape(tokens[0])
        surname = tokens[0]
    else:
        first, last = re.escape(tokens[0]), re.escape(tokens[-1])
        surname = tokens[-1]
    # ★ 缩写标签要给**两种**：名姓首字母（`MS`）与全部首字母（`MHS`）。
    #   只按全名段数算一种是实测抓到的回归——The Media Line 那份 44 轮逐字稿
    #   用的是 `MS:`／`TML:`，而账本里他的名字是三段的 `Michael H. Steinhardt`，
    #   只生成 `mhs` 就把一份真逐字稿判成了无据。
    #   **人在语料里用的缩写取决于他惯用的名字形态，不取决于账本写了几段。**
    letters = [t[0].lower() for t in tokens if t[:1].isalpha()]
    initials = {letters[0] + letters[-1], "".join(letters)}

    # ★ 可选中间名**自带尾随空格**，与 `first` 后那个必需空格不重叠。
    #   写成 `first[ \t]+(?:mid[ \t]+)?{0,2}last` 才没有两个量词争同一段空白。
    # ★ 单名／地名式后缀时 first == last，**不能再要求「名 空格 姓」**——
    #   那会变成要求同一个词出现两次，`By Galen` 一条也匹配不上。
    if first == last:
        name_rx = first
    else:
        name_rx = rf"{first}[ \t]+(?:[A-Z][A-Za-z.'\-]{{0,15}}[ \t]+){{0,2}}{last}"
    # 姓氏单独出现也算（`By Steinhardt` 式的短署名）——但只用于**标签归属**判定，
    # 不用于署名判定，避免把「谈论他」的句子当成他的署名。
    surname_rx = re.escape(surname)

    return {
        "name": full_name,
        "surname": surname,
        "masthead": None,          # 由 --masthead 注入；见 attach_masthead
        "MASTHEAD": None,
        "name_rx": name_rx,
        # ★ v0.0.0.54：`By` 与名字之间允许**敬称／学位头衔**。
        #   Fleming #111 实测：`campbell-oration-1944` 等 **7 份**署的是
        #       `By SIR ALEXANDER FLEMING`
        #   而旧式 `\bBy\s+名姓\b` 要求 `By` 后面紧跟名字，**七份亲笔著作全判「无据」**。
        #   这与 Livermore #100 那次（`BY` 与名字分行）是同一类：
        #   **判据认得出名字，认不出名字前面那一小截。**
        #   敬称列表收窄到常见几个，且都要求后跟空白——
        #   不许写成 `\w*\s+` 那种什么都吞的形态，否则
        #   `By his colleague Alexander Fleming` 会被当成他的署名。
        "BYLINE": re.compile(
            rf"\bBy\s+(?:(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady)\.?\s+)*"
            rf"{name_rx}\b", re.I),
        "EDITORIAL": re.compile(
            rf"[\[\(][^\])]{{0,40}}\b(?:remarks|speech|address|excerpt|written|delivered|adapted)"
            rf"[^\])]{{0,40}}\bby\s+{name_rx}", re.I),
        # ★ v0.0.0.54 `A-byline-standalone`：期刊署名不带 `By`，独占一行。
        #   行尾允许**逗号**——合著论文把下一位作者接在下一行，就是这个形态。
        #   学位后缀（`M.B.`、`B.S. Lond.`、`F.R.C.S.`）允许出现，但**只能在名字之后**。
        "STANDALONE": re.compile(
            rf"^[ \t]*(?:(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady)\.?[ \t]+)*"
            rf"{name_rx}"
            rf"(?:[ \t]*,[ \t]*[A-Za-z][A-Za-z.]{{0,10}}(?:[ \t]+[A-Za-z][A-Za-z.]{{0,10}}){{0,2}})*"
            rf"[ \t]*[.,]?[ \t]*$", re.M | re.I),
        # ↑ `re.I` 是自测抓出来的：期刊署名印的是**全大写** `ALEXANDER FLEMING`，
        #   而 `name_rx` 是混合大小写的 `Alexander…Fleming`，不加 `re.I` 一条也不中。
        # ★ v0.0.0.18 `A-copyright`：扫描件的版权页。
        #
        #   Livermore #100 实测：他 1940 年那本亲笔著作的署名页 OCR 成
        #       BY
        #       JESSE 1. LIVERMORE          ← `L.` 被认成 `1.`，且 BY 与名字分行
        #   于是 `BYLINE`（`\bBy\s+名姓\b`，同一行、中间名须以大写字母开头）
        #   **一条也匹配不上**，一份货真价实的亲笔著作被判成「无据」。
        #
        #   版权声明是**结构元素**且由出版社出具，作为归属证据比正文里的 by 更硬。
        #   两条收窄，防止散文里的「the copyright by X was disputed」被误收：
        #     ① `COPYRIGHT` 必须在**行首**（MULTILINE `^`）；
        #     ② 名字允许跨行、允许中间名首字符是数字（专治 OCR 把 `L.` 认成 `1.`），
        #        **但名与姓本身必须逐字对上**。
        #   ★ 相邻量词不许吞同一段字符（第六十八种）：`[ \t\r\n]+` 之后接
        #     `[A-Z0-9]`，两者字符集不相交。
        #   ③ **年份一律不校验**。第一版写成 `(?:1[5-9]\d\d|20\d\d)?`，
        #      在真语料上一条也匹配不上——那一页印的是 `COPYRIGHT, 1040, BY`，
        #      **`1940` 被 OCR 认成了 `1040`**。
        #      我给一个「本判据根本不需要的字段」写了校验，
        #      而那个字段恰恰来自最不可靠的一层。**不需要的字段就不要校验。**
        "COPYRIGHT": re.compile(
            rf"^[ \t]*(?:COPYRIGHT|©)[^A-Za-z\r\n]{{0,12}}BY"
            rf"[ \t\r\n]+{first}[ \t\r\n]+"
            rf"(?:[A-Z0-9][A-Za-z0-9.'\-]{{0,15}}[ \t\r\n]+){{0,2}}{last}\b",
            re.I | re.M),
        "MINE": re.compile(
            rf"{surname_rx}|^(?:{'|'.join(re.escape(i) for i in sorted(initials))})$", re.I),
        "SURNAME": re.compile(surname_rx, re.I),
    }


# 「疑似他人署名行」：全大写、2–4 个词、无常见虚词、独占一行。
# 书籍前言／序的署名就是这个形态（`EDWARD JEROME DIES`）。
#
# ⚠ **只报不判**，绝不当作反证。实测在同一本书上会命中 `NEW YORK`、
# `EXPLANATORY RULES` 这类地名与小节标题——**精度不够，当反证会误杀整类书籍**。
# 要防的那件事（卷内换作者）正确的解法是**按作者切开再入库**，
# 本清单的用处是让人一眼看见「这份文件里还有别人的名字」。
def despace_display(text: str) -> str:
    """把**字母间隔的展示排版**折回正常词形，供匹配用（不改存盘文本）。

    Fleming #111 的诺奖演说，标题页印的是：

        AL E X A N D E R  F L E M I N G

    这是扫描件标题页与刊头的通例——排版为求视觉分量把字母拉开，
    OCR 忠实地把每个字母之间的空格也抄下来。
    **任何名字正则都匹配不上**，于是一份货真价实的诺奖演说被判「无据」。

    与 `check_quote_integrity` 里的长 s 折叠同类：
    **归一是为了比对，不是为了改语料。**

    判法：一行里**单字母词占多数且总数 ≥5** 时，
    去掉单字母之间的单个空格，把 2 个以上的空格收成一个词界。
    只动这种行——普通句子里没有这个形态。
    """
    out = []
    for line in text.split("\n"):
        toks = line.split()
        if len(toks) >= 5 and sum(1 for t in toks if len(t) == 1) / len(toks) >= 0.6:
            # 先把词界（≥2 空格）标出来，再删单空格，最后还原词界
            marked = re.sub(r"[ \t]{2,}", "\x00", line.strip())
            joined = re.sub(r"(?<=[A-Za-z])[ \t](?=[A-Za-z])", "", marked)
            out.append(joined.replace("\x00", " "))
        else:
            out.append(line)
    return "\n".join(out)


# 签名块的邻接特征：机构、地址、或日期。
# **不含人名**——判「是不是签名块」，不判「是谁的签名」；后者由 `STANDALONE` 判。
ADDRESS_BLOCK = re.compile(
    r"\b(?:Department|Hospital|Institute|Infirmary|Laborator(?:y|ies)|College|"
    r"University|School of Medicine|Royal Society|Clinic)\b"
    r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\b"
    r"|\b[A-Z]{1,2}\.?\s?\d{1,2}[.,]?\s*$",          # 伦敦邮区 `W.1.`
    re.I | re.M)

CAPS_LINE = re.compile(r"^[ \t]*([A-Z][A-Z'\-]{2,}(?:[ \t]+[A-Z][A-Z'\-]{2,}){1,3})[ \t]*$", re.M)
CAPS_STOPWORDS = {
    "THE", "AND", "OF", "IN", "TO", "A", "AN", "FOR", "ON", "BY", "WITH", "AT",
    "FROM", "OR", "AS", "IS", "ARE", "WAS", "HOW", "WHAT", "WHEN", "WHY", "NOT",
    "ALL", "NEW", "YOU", "YOUR", "THIS", "THAT", "INC", "CO", "COMPANY", "PRESS",
    "CHAPTER", "CONTENTS", "PREFACE", "INDEX", "PART", "RULES", "STOCKS", "MARKET",
}


def suspect_signature_lines(text: str, pat: dict) -> list:
    """→ 疑似他人署名行清单（**只报不判**）。"""
    out = []
    for m in CAPS_LINE.finditer(text):
        line = m.group(1)
        tokens = line.split()
        if any(t in CAPS_STOPWORDS for t in tokens):
            continue
        if pat["SURNAME"].search(line):
            continue                      # 是本人
        if line not in out:
            out.append(line)
    return out


def attach_masthead(pat, masthead):   # masthead: str | None（本机 3.9，注解不写联合类型）
    """把「单作者站点报头」注册成第四类归属证据。

    ## 为什么需要它

    Godin #99 实测：193 篇 seths.blog 正文**全部判为无据**。
    它们的署名是站点报头 `<标题> | Seth's Blog`，既不是 `By X`、
    不是编者注、也不是逐字稿轮次——**证据在文里，是判据看不见这个形态**。

    ## 为什么它不会把这道门变松

    三重约束，缺一不可：

    1. **必须显式声明**（`--masthead`），检查器绝不自己推断站点名；
    2. **报头必须含人物的名或姓**——`Seth's Blog` 含 `Seth` 才配声明。
       Steinhardt 那轮的 `CONTACT` 刊头不含 `Steinhardt`，**声明不了**，
       于是那四份别人写的随笔照旧拦得住；
    3. **反向检查照常生效**——文末出现别人的身份署名一样降级。

    换句话说：这一类放行的是「以他本人命名的单作者站点」，
    不是「任何有刊头的出版物」。
    """
    if not masthead or not masthead.strip():
        return pat
    head = masthead.strip()
    if not pat["SURNAME"].search(head) and not re.search(
            re.escape(pat["name"].split()[0]), head, re.I):
        raise ValueError(
            f"报头 {head!r} 里没有 {pat['name']!r} 的名或姓——"
            f"不含人物名的刊头不得当作归属证据（这正是多作者刊物的形态）")
    pat = dict(pat)
    pat["masthead"] = head
    pat["MASTHEAD"] = re.compile(re.escape(head), re.I)
    return pat


# 说话人标签：行首「名字:」。**必须多次出现且后文每次不同**才算逐字稿。
# ★ 名字部分不能写成含空格的字符类再跟 `[ \t]*`——两者可以互相吞空格，
#   在十几万字的检方文书上会灾难性回溯直接卡死。改成「词(空格词){0,3}」的无歧义形式。
# ★ 冒号后的正文**可能在下一行、且中间隔着空行**——Charlie Rose 与
#   Knowledge@Wharton 的逐字稿是「说话人标记独占一行 + 空行 + 正文」。
#   只认同行会把 67 轮的真逐字稿判成 0 轮，只允许一个 \n 也还是 0 轮。
# ★ 标签第二个词起允许小写连接词——Knowledge@Wharton 的主持人标签就是
#   `Knowledge at Wharton:`，要求每词首字母大写会把它整条丢掉，
#   于是只剩姓氏一个标签，「≥2 个说话人」的判据就假阴性了。
TURN = re.compile(
    r"^[ \t]{0,4}([A-Z][A-Za-z.'\-]{0,20}(?: [A-Za-z.'\-]{1,20}){0,3})"
    r"[:：](?:[ \t]*\n){0,3}[ \t]{0,4}(\S.{0,80})", re.M)
# 他人身份署名（刊物型 PDF 的作者行就长这样）。同理不用 `\s+`。
OTHER_ROLE = re.compile(
    r"\b([A-Z][a-z]{1,20}(?: [A-Z][a-z.']{1,20}){0,3}) is (?:the |a |an )?"
    r"(Chair|Chairman|President|Managing Director|Executive Director|Director|"
    r"Rabbi|Professor|founder|co-founder|CEO|Vice President|Senior)\b")
OTHER_BY = re.compile(
    r"^[ \t]{0,4}By ([A-Z][a-z]{1,20}(?: [A-Z][a-z.']{1,20}){1,3})[ \t]{0,4}$", re.M)
# ★ 刊物型排版里署名常是**行内全大写**：`… Why I Live In Israel by ANDREW KATZ 6 CONTACT`。
#   只认「独占一行的 By X」会漏掉它——实测一份 22KB 的切片因此混进了整篇邻文。
OTHER_BY_CAPS = re.compile(r"\bby ([A-Z][A-Z.]{1,18}(?: [A-Z][A-Z.]{1,18}){1,3})\b")


# ★ 第三种形态：**全大写标记、不带冒号**。charlierose.com 2001 年的逐字稿是
#   `MICHAEL STEINHARDT He grew up in Brooklyn.` / `CHARLIE ROSE Yeah. You?`
#   ——一份 100+ 轮的真逐字稿，只因没有冒号被判成 0 轮。
TURN_CAPS = re.compile(
    r"^[ \t]{0,4}([A-Z][A-Z.'\-]{1,18}(?: [A-Z][A-Z.'\-]{1,18}){0,3})"
    r"[ \t]+(?=[A-Z][a-z])(.{4,80})", re.M)


def turns_evidence(text: str, pat: dict):
    """真逐字稿：≥2 个标签各 ≥3 轮，且同一标签后文互不相同。"""
    seen: dict[str, set] = {}
    for rx in (TURN, TURN_CAPS):
        for label, rest in rx.findall(text):
            seen.setdefault(label.strip().lower(), set()).add(rest.strip()[:60])
    good = {k: v for k, v in seen.items() if len(v) >= 3}
    mine = [k for k in good if pat["MINE"].search(k)]
    if not mine:
        return None
    if len(good) < 2:
        # ★ 只有他一个标签也可以成立——**前提是后文足够多且互不相同**。
        #   Benzinga 2011 那篇访谈只给他的应答加标记、提问方不加标记，
        #   14 段应答各不相同，逐轮归属比双标签还硬。
        #   而「≥2 个标签」这条规则本来是为了挡住「标题里的冒号」，
        #   那一类的后文是**同一句**，distinct 判据已经挡住了；
        #   门槛取 5 是因为实测标题会以两种微异形态各出现一次
        #   （`… - Part 2 - Benzinga` 与 `… - Part 2`）。
        #   但只数「互不相同」还不够：资源页的小标题也各不相同
        #   （`Michael Steinhardt: Background & bio` /
        #    `… : Investment philosophy` / `… : Philanthropy`）。
        #   访谈的应答是**句子**，小标题是短名词短语——所以再要求
        #   ≥5 段后文各自 ≥40 字符。他确实会答「Yeah.」「I don't.」这类短句，
        #   所以要求的是「有 5 段长的」，不是「每段都长」。
        if max(sum(1 for x in good[k] if len(x) >= 40) for k in mine) < 5:
            return None
    labels = ", ".join(f"{k}×{len(v)}" for k, v in sorted(good.items())[:4])
    return f"说话人轮次 {labels}"


def check_text(text: str, pat: dict):
    """返回 (ok, 证据码, 证据原文, 反证列表)。"""
    # ★ v0.0.0.55：先把字母间隔的展示排版折回词形。
    #   **归一只用于比对，不写回语料**——与长 s 折叠同一条纪律。
    #   反证也走归一后的文本：否则「别人的名字被拉开字母」就绕过了反向检查。
    text = despace_display(text)
    counter = []

    for m in OTHER_ROLE.finditer(text):
        if pat["SURNAME"].search(m.group(1)):
            continue
        counter.append(m.group(0).strip())
    for rx in (OTHER_BY, OTHER_BY_CAPS):
        for m in rx.finditer(text):
            if not pat["SURNAME"].search(m.group(1)):
                counter.append(m.group(0).strip())

    for code, key in (("A-byline", "BYLINE"), ("A-editorial", "EDITORIAL")):
        for m in pat[key].finditer(text):
            # ★ 真署名是**结构元素**：行首，或跟在分隔符后面。
            #   句子中间的「by X」是在**谈论**作者身份，不是署名——
            #   实测 `No Bull is the … autobiography by Michael Steinhardt who rose
            #   from 'rags' in Brooklyn` 是一篇书评，真作者署名 Roy Sebag 在上一行。
            before = text[max(0, m.start() - 14):m.start()]
            after = text[m.end():m.end() + 14].lstrip(" ,.")
            structural = (m.start() == 0 or "\n" in before
                          or re.search(r"[*|·—–]\s*$", before))
            if not structural or re.match(r"(who|which|that)\b", after, re.I):
                continue
            a, b = max(0, m.start() - 60), min(len(text), m.end() + 60)
            return True, code, " ".join(text[a:b].split()), counter

    # ★ v0.0.0.54 `A-byline-standalone`：**期刊署名根本不带 `By`。**
    #
    #   Fleming #111 实测，同一批语料里三种形态：
    #       ALEXANDER FLEMING, M.B., B.S. Lonp.      ← 独占一行 + 学位后缀
    #       ALEXANDER FLEMING, F.R.C.S.,             ← **行尾是逗号**，下一行还有合著者
    #       ALEXANDER FLEMING.                       ← 光名字
    #   `BYLINE` 要求 `By` 打头，**三种一条也匹配不上**——
    #   四十二份 P1 里二十九份被判「无据」，而它们全是货真价实的期刊论文。
    #
    #   这不是给 Fleming 一个人开的口子：**十九至二十世纪的期刊论文普遍这样署名**，
    #   名册里凡是科学家，语料主体都是期刊论文。
    #
    #   三条收窄，防止把「关于他的书」里的章节标题当成署名：
    #     ① 必须**独占一行**（前后都是行边界），不许是句子的一部分；
    #     ② 必须落在**文件前 30%**——署名在文首，正文深处那个是索引或参考文献；
    #     ③ 行尾只许跟学位后缀、逗号或句点。**逗号必须放行**——
    #        那正是合著论文把下一位作者接在下一行的写法。
    #     ④ **有反证时一律不放行。** 独占一行的名字比显式 `By` 弱——
    #        它可能是标题、可能是被引用的人。**自测当场抓到**：
    #        「版权页在、但文末是别人的身份署名」那条反例被它误放行了。
    #        显式 `By` 可以顶着反证走，独占署名不行。
    if pat.get("STANDALONE") and not counter:
        for m in pat["STANDALONE"].finditer(text):
            # ★ v0.0.0.55 `A-signature-block`：**来信与书评的署名在末尾，不在文首。**
            #
            #   Fleming #111 实测四份，独占署名分别落在 37%／52%／57%／75%——
            #   全被「前 30%」这条位置规则挡住。而它们的形态是明白无误的签名块：
            #       ALEXANDER FLEMING.
            #       Inoculation Department,
            #       St. Mary's Hospital, Jan. 5.
            #   **名字 + 机构地址 + 日期**，这是医学期刊来信／讨论／书评的标准签名。
            #
            #   **位置不是对的判据，邻接的地址块才是。**
            #   位置规则留给「没有地址块」的那一类（期刊论文的文首署名）。
            near = text[max(0, m.start() - 160):m.end() + 160]
            signed = bool(ADDRESS_BLOCK.search(near))
            if not signed and m.start() > len(text) * 0.30:
                continue                    # 正文深处、又没有地址块的那个不是署名
            code = "A-signature-block" if signed else "A-byline-standalone"
            a, b = max(0, m.start() - 60), min(len(text), m.end() + 60)
            return True, code, " ".join(text[a:b].split()), counter

    # A-copyright：版权页。与上面两类同样受反证约束——
    # 文中出现别人的身份署名时不放行。
    if not counter:
        m = pat["COPYRIGHT"].search(text)
        if m:
            a, b = max(0, m.start() - 40), min(len(text), m.end() + 40)
            return True, "A-copyright", " ".join(text[a:b].split()), counter

    if pat.get("MASTHEAD"):
        for m in pat["MASTHEAD"].finditer(text):
            # 与署名同样要求**结构位置**：行首，或跟在 `|`／`·` 这类分隔符后面。
            before = text[max(0, m.start() - 14):m.start()]
            if not (m.start() == 0 or "\n" in before or re.search(r"[|·—–]\s*$", before)):
                continue
            if counter:      # 文末有别人的身份署名 → 报头不足以归属
                break
            a, b = max(0, m.start() - 60), min(len(text), m.end() + 60)
            return True, "A-masthead", " ".join(text[a:b].split()), counter

    ev = turns_evidence(text, pat)
    if ev:
        # ★ 轮次型证据不受他人署名影响，反证清空。
        #   访谈/逐字稿里出现**提问者**的署名是应有之义
        #   （CONTACT 2000 春季刊的问答就署 `by ELI VALLEY`），
        #   而他的话是**逐轮标注**的，归属不靠整篇署名建立。
        #   署名型证据（随笔）则相反：文中出现别人的署名就说明切歪了。
        return True, "A-turns", ev, []

    return False, "", "", counter


def check(path: pathlib.Path, pat: dict):
    return check_text(path.read_text(encoding="utf-8", errors="replace"), pat)


# ── 负对照：判据改动后必须双向都跑 ──────────────────────────────────
# v0.0.0.9 的过程教训是「判据改完只跑了一边」，三次都是修完假阳性就交付、
# 或修完假阴性就交付。这里把最小双向集内置，任何人改本文件都能当场验。
SELFTEST_NAME = "Jane Q. Public"
SELFTEST_POSITIVE = [
    ("行首署名", "By Jane Q. Public\n\nI have argued for years that the ratio matters.\n"),
    # ★ v0.0.0.54 回归守卫（Fleming #111 实测抓到）：署名里夹着敬称。
    #   `campbell-oration-1944` 等 **7 份**署的是 `By SIR ALEXANDER FLEMING`，
    #   而旧式 `\bBy\s+名姓\b` 要求 By 后面紧跟名字——**七份亲笔著作全判「无据」**。
    #   与 Livermore #100 那次（`BY` 与名字分行）同类：认得出名字，认不出前面那一小截。
    ("署名夹敬称 Sir", "By SIR JANE Q. PUBLIC\n\nThe ratio is what matters here.\n"),
    ("署名夹敬称 Dr.", "By Dr. Jane Q. Public\n\nThe ratio is what matters here.\n"),
    ("署名夹两级头衔", "By Professor Dame Jane Q. Public\n\nThe ratio matters.\n"),
    # ★ v0.0.0.54 `A-byline-standalone`（Fleming #111 实测抓到）：
    #   期刊署名**不带 `By`**，独占一行，行尾可能是逗号（下一行还有合著者）。
    #   42 份 P1 里 29 份因此被判「无据」，而它们全是货真价实的期刊论文。
    ("期刊署名·学位后缀",
     "ON THE ETIOLOGY OF ACNE VULGARIS\n\nJANE Q. PUBLIC, M.B., B.S. Lond.\n\n"
     "The organism was isolated from the lesions in every case examined here.\n"),
    ("期刊署名·行尾逗号（合著接下一行）",
     "ON THE ANTIGENIC PROPERTIES\n\nJANE Q. PUBLIC, F.R.C.S.,\nAND R. ROE, M.D.\n\n"
     "The antigenic properties were examined in a series of cultures.\n"),
    ("期刊署名·光名字",
     "ON THE INFLUENCE OF TEMPERATURE\n\nJANE Q. PUBLIC.\n\n"
     "The influence of temperature upon agglutination was measured.\n"),
    # ★ v0.0.0.55 `A-signature-block`（Fleming #111 实测四份）：
    #   来信／书评／讨论发言的署名在**末尾**，形态是「名字 + 机构地址 + 日期」。
    #   四份的独占署名落在 37%／52%／57%／75%，全被「前 30%」的位置规则挡住。
    ("来信签名块·文末",
     "A long discussion of the subject at hand goes on for a while here.\n" * 40
     + "JANE Q. PUBLIC.\nInoculation Department,\nSt. Mary's Hospital, Jan. 5.\n"),
    # ★ v0.0.0.55 字母间隔展示排版（Fleming #111 诺奖演说实测）：
    #   标题页印的是 `AL E X A N D E R  F L E M I N G`——任何名字正则都匹配不上。
    ("字母间隔的标题署名",
     "\n J AN E  Q.  P U B L I C\nPenicillin\nNobel Lecture, December 11, 1945\n"
     "I am going to tell you about the early days of the work described here.\n"),
    ("书评签名块·文中（同页还有下一篇）",
     "A review of somebody else's book runs on for several paragraphs here.\n" * 30
     + "JANE Q. PUBLIC.\nLondon, W.1.\n"
     + "GALTON AND EUGENICS\nThe next review begins here and is by someone else.\n" * 20),
    ("编者注", "[Remarks delivered by Jane Public at the 1998 annual meeting.]\n\nThank you.\n"),
    ("逐字稿双标签", "".join(
        f"HOST: Question number {i} about the portfolio and its construction over time?\n"
        f"PUBLIC: Answer number {i} explaining the reasoning in some detail here.\n"
        for i in range(1, 6))),
    # ★ 回归守卫（v0.0.0.10 实测抓到）：逐字稿常用**缩写标签**而不是姓氏。
    #   人物名三段时若只生成「全首字母」缩写，`JP:` 这种标签就整条丢掉，
    #   一份 44 轮的真逐字稿会被判成无据。名姓首字母与全首字母**两种都要认**。
    ("逐字稿缩写标签", "".join(
        f"TML: Question number {i} about communal priorities and their funding?\n"
        f"JP: Answer number {i} setting out the reasoning at some length here.\n"
        for i in range(1, 6))),
]
SELFTEST_POSITIVE_COPYRIGHT = [
    # ★ 实测形态（Livermore 1940 年那本书的版权页 OCR 结果）：
    #   BY 与名字分行，且中间名 `L.` 被 OCR 认成 `1.`。
    ("扫描件版权页·跨行 + 中间名被 OCR 成数字",
     "HOW TO TRADE\nIN STOCKS\n\nBY\nJANE 1. PUBLIC\n\n"
     "COPYRIGHT, 1940, BY\nJANE 1. PUBLIC\n\nAll rights reserved.\n"),
    ("© 记号 + 同行", "© 1998 by Jane Q. Public\n\nThe ratio matters.\n"),
    # ★ 真语料形态：年份本身也被 OCR 认错（1940 → 1040）。
    #   第一版判据校验了年份，在真件上一条也匹配不上。**不需要的字段不要校验。**
    ("年份被 OCR 认错（1940→1040）",
     "COPYRIGHT, 1040, BY\nJANE 1. PUBLIC\n\nAll rights reserved.\n"),
]
SELFTEST_NEGATIVE_COPYRIGHT = [
    ("散文里谈论版权归属，不是版权页",
     "The dispute over the copyright by Jane Q. Public dragged on for years.\n"),
    ("版权归别人", "COPYRIGHT, 1940, BY\nRICHARD ROE\n\nJane Public is discussed here.\n"),
    ("版权页在，但文末是别人的身份署名",
     "COPYRIGHT, 1940, BY\nJANE Q. PUBLIC\n\nText.\n"
     "Richard Roe is Chairman of the Example Foundation.\n"),
]
SELFTEST_NEGATIVE = [
    ("他人署名的随笔", "By Richard Roe\n\nJane Public once told me the ratio matters.\n"
                       "Richard Roe is Chairman of the Example Foundation.\n"),
    ("散文里的 by X", "The autobiography by Jane Q. Public who rose from nothing is reviewed here.\n"),
    ("标题里的冒号", "Jane Public: Background & bio\nJane Public: Investment philosophy\n"
                     "Jane Public: Philanthropy\nJane Public: Background & bio\n"),
    ("完全没提到她", "This quarterly essay is about communal institutions and their funding.\n" * 5),
    # ★ v0.0.0.54：放宽敬称之后**必须验它没放宽过头**。
    #   若写成 `By\s+\w*\s+名姓`，下面两条都会被误当成她的署名。
    ("By 后面是别人再提到她", "By her colleague Jane Q. Public was often quoted.\n"),
    ("By 后面是机构名", "By the Public Health Board of Jane Q. Public County.\n"),
    # ★ v0.0.0.54：独占一行的署名放宽之后，**必须验它没放宽过头**。
    ("正文深处独占一行的名字（索引／参考文献）",
     "A long article about something else entirely.\n" * 120
     + "Jane Q. Public\n" + "More body text follows here after it.\n" * 40),
    ("独占一行的是别人的名字",
     "ON SOMETHING\n\nRICHARD ROE, M.D.\n\nJane Q. Public is cited below in passing.\n"),
    # ★ v0.0.0.55：签名块放宽之后**必须验它没放宽过头**——
    #   正文里提到某医院，不能把同段里出现的名字认成签名。
    # ★ v0.0.0.55：字母间隔归一之后，**反证也要走归一后的文本**——
    #   否则把别人的名字拉开字母就能绕过反向检查。
    ("别人的署名被拉开字母",
     "\n R I C H A R D  R O E,  M. D.\nSome Title Here\n"
     "Jane Q. Public is mentioned somewhere in the body of this piece.\n"),
    ("普通句子不许被折成一团",
     "I a m n o t a d i s p l a y l i n e b u t t h i s i s p r o s e.\n"
     "Jane Q. Public appears nowhere as an author of this particular text.\n"),
    ("正文里提到医院，名字在句子中间",
     "The work was done at St. Mary's Hospital in London during that period.\n" * 30
     + "Later the results were confirmed by Jane Q. Public and her colleagues there.\n"
     + "Further discussion of the method follows in the next section below.\n" * 20),
]


SELFTEST_MASTHEAD = "Public's Blog"
SELFTEST_MASTHEAD_POSITIVE = [
    ("单作者站点报头", "Ratios matter | Public's Blog\n Ratios matter\n"
                       "I have argued for years that the ratio matters.\n"),
]
SELFTEST_MASTHEAD_NEGATIVE = [
    ("报头在，但文末是别人的署名",
     "Ratios matter | Public's Blog\n Ratios matter\nThe ratio matters.\n"
     "Richard Roe is Chairman of the Example Foundation.\n"),
    ("报头只出现在句子中间，不是结构位置",
     "She once wrote on Public's Blog that ratios matter, or so the story goes.\n"),
]


def self_test() -> int:
    pat = build_patterns(SELFTEST_NAME)
    bad = []
    for label, text in SELFTEST_POSITIVE:
        ok, code, ev, _ = check_text(text, pat)
        print(f"  {'✓' if ok else '✗'} 正例 {label}: {code or '——'} {ev[:60]}")
        if not ok:
            bad.append(f"正例 {label} 未通过")
    for label, text in SELFTEST_NEGATIVE:
        ok, code, _, _ = check_text(text, pat)
        print(f"  {'✓' if not ok else '✗'} 反例 {label}: {'已拒' if not ok else '误放行 ' + code}")
        if ok:
            bad.append(f"反例 {label} 被误放行（{code}）")
    # ── A-masthead 的双向对照 ──
    mp = attach_masthead(pat, SELFTEST_MASTHEAD)
    for label, text in SELFTEST_MASTHEAD_POSITIVE:
        ok, code, ev, _ = check_text(text, mp)
        print(f"  {'✓' if ok and code == 'A-masthead' else '✗'} 正例 {label}: {code or '——'} {ev[:50]}")
        if not (ok and code == "A-masthead"):
            bad.append(f"正例 {label} 未通过（得 {code or '无据'}）")
    for label, text in SELFTEST_MASTHEAD_NEGATIVE:
        ok, code, _, _ = check_text(text, mp)
        print(f"  {'✓' if not ok else '✗'} 反例 {label}: {'已拒' if not ok else '误放行 ' + code}")
        if ok:
            bad.append(f"反例 {label} 被误放行（{code}）")
    # ── A-copyright 的双向对照（v0.0.0.18）──
    for label, text in SELFTEST_POSITIVE_COPYRIGHT:
        ok, code, ev, _ = check_text(text, pat)
        print(f"  {'✓' if ok and code == 'A-copyright' else '✗'} 正例 {label}: {code or '——'} {ev[:50]}")
        if not (ok and code == "A-copyright"):
            bad.append(f"正例 {label} 未通过（得 {code or '无据'}）")
    for label, text in SELFTEST_NEGATIVE_COPYRIGHT:
        ok, code, _, _ = check_text(text, pat)
        print(f"  {'✓' if not ok else '✗'} 反例 {label}: {'已拒' if not ok else '误放行 ' + code}")
        if ok:
            bad.append(f"反例 {label} 被误放行（{code}）")

    # ★ v0.0.0.26 非西方姓名形态（Galen #101 实测撞出）：
    #   ① 单名必须能建判据且 `By Galen` 命中；② `X of Y` 的识别标记是 X 不是 Y。
    #   改动前：build_patterns("Galen") 直接抛；
    #           build_patterns("Galen of Pergamon") 把地名 Pergamon 当姓，
    #           于是 own_voice_ratio 静默报 0.0——而真值接近 1.0。
    for nm, want, line, should in [
        ("Galen", "Galen", "By Galen", True),
        ("Galen of Pergamon", "Galen", "By Galen", True),
        ("Leonardo da Vinci", "Leonardo", "By Leonardo", True),
        ("Jesse Lauriston Livermore", "Livermore", "By Jesse Lauriston Livermore", True),
        ("Galen of Pergamon", "Galen", "By Pergamon", False),   # 地名不得当成他
    ]:
        try:
            np_ = build_patterns(nm)
        except ValueError as exc:
            bad.append(f"姓名形态：{nm!r} 建判据失败——{exc}")
            print(f"  ✗ 姓名形态 {nm}: 建判据失败")
            continue
        okname = np_["surname"] == want
        okby = bool(np_["BYLINE"].search(line)) is should
        if not okname:
            bad.append(f"姓名形态：{nm!r} 识别标记应为 {want!r}，实得 {np_['surname']!r}")
        if not okby:
            bad.append(f"姓名形态：{nm!r} 对 {line!r} 的 BYLINE 判定应为 {should}")
        print(f"  {'✓' if okname and okby else '✗'} 姓名形态 {nm} → {np_['surname']}｜{line!r}={should}")

    # ── 疑似他人署名行：**只报不判**，此处只验它确实报得出来 ──
    lines = suspect_signature_lines(
        "COPYRIGHT, 1940, BY\nJANE Q. PUBLIC\n\nPREFACE\n\nText here.\n\n"
        "EDWARD JEROME DIES\n\nI. THE CHALLENGE OF SPECULATION\n", pat)
    if "EDWARD JEROME DIES" not in lines:
        bad.append(f"疑似他人署名行未报出：得 {lines}")
    print(f"  {'✓' if 'EDWARD JEROME DIES' in lines else '✗'} 只报不判 疑似他人署名行: {lines}")

    # ★ 最要命的一条：**不含人物名的刊头必须声明不了**。
    #   这一条守的是 Steinhardt 那轮的 CONTACT 形态——多作者季刊，
    #   刊头里没有他的名字，因此永远拿不到 masthead 豁免。
    try:
        attach_masthead(pat, "CONTACT Quarterly")
        bad.append("反例 不含人物名的刊头 被接受了声明（这会让多作者刊物全部洗白）")
        print("  ✗ 反例 不含人物名的刊头: 误接受")
    except ValueError:
        print("  ✓ 反例 不含人物名的刊头: 已拒绝声明")

    if bad:
        print("\n负对照未过：")
        for b in bad:
            print(f"  · {b}")
        return 2
    npos = (len(SELFTEST_POSITIVE) + len(SELFTEST_MASTHEAD_POSITIVE)
            + len(SELFTEST_POSITIVE_COPYRIGHT))
    nneg = (len(SELFTEST_NEGATIVE) + len(SELFTEST_MASTHEAD_NEGATIVE)
            + len(SELFTEST_NEGATIVE_COPYRIGHT) + 1)
    print(f"\n负对照通过（{npos} 正 + {nneg} 反，另含 1 条只报不判）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("corpus", nargs="?", help="语料目录")
    ap.add_argument("--name", help="人物全名（取 meta.json 的 name）")
    ap.add_argument("--claim-p1", nargs="*", default=None,
                    help="声称是 P1 的文件名；省略则检查目录里全部 .txt")
    ap.add_argument("--masthead", default=None,
                    help="单作者站点的报头（如 \"Seth's Blog\"）。**必须含人物的名或姓**，"
                         "否则拒绝声明——不含人物名的刊头正是多作者刊物的形态。")
    ap.add_argument("--self-test", action="store_true",
                    help="只跑内置双向负对照，不读语料")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.corpus or not a.name:
        print("✗ 需要 corpus 与 --name（或只给 --self-test）", file=sys.stderr)
        return 3

    try:
        pat = attach_masthead(build_patterns(a.name), a.masthead)
    except ValueError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 3

    d = pathlib.Path(a.corpus)
    if not d.is_dir():
        print(f"✗ 目录不存在：{d}", file=sys.stderr)
        return 3
    files = sorted(a.claim_p1) if a.claim_p1 else sorted(
        p.name for p in d.glob("*.txt"))
    if not files:
        print("✗ 没有要检查的文件", file=sys.stderr)
        return 3

    bad, sus = [], []
    print(f"检查 {len(files)} 份是否够格当「{a.name} 的话」（P1）\n")
    for f in files:
        p = d / f
        if not p.exists():
            print(f"  ✗ {f}: 文件不存在")
            bad.append(f)
            continue
        ok, code, ev, counter = check(p, pat)
        if ok and counter:
            sus.append((f, code, counter))
            print(f"  ⚠ {f}\n      有正面证据 [{code}]，**但文中另有他人署名**：")
            for c in counter[:3]:
                print(f"        · {c}")
        elif ok:
            print(f"  ✓ {f}\n      [{code}] {ev[:150]}")
        else:
            bad.append(f)
            print(f"  ✗ {f}  ——**查无归属证据，不得当作他的话**")
            for c in counter[:3]:
                print(f"        文中他人署名：{c}")

    print(f"\n有据 {len(files)-len(bad)} / 无据 {len(bad)} / 存疑 {len(sus)}")
    if bad:
        print("\n无据清单（这些不能标 P1，也不能用 --author 挂他的名字）：")
        for f in bad:
            print(f"  {f}")
        print("\n**处理方式不是降级成 S1 就完事**——若它整篇是别人写的，"
              "应当移出语料目录；留在库里只会让下游把别人的话当成他的。")
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
