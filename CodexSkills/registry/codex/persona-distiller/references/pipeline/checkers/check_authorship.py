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

- **首字母 + 姓（`A. Fleming`）永远不认。** 这个人物恰有 `A. Grant Fleming`，
  裸检索 `Fleming A` 时排第一。`wound-infections-1920-CO` 全卷唯一的署名就是
  `A. Fleming, M.B.jB.S. Lond.`——三人从头合著到尾、无分节署名，**认它等于认下陷阱**。

  ⚠ **v0.0.0.55 我在这里写错过一次**：当时写「`lysozyme-1922-prsb` 的署名只在书眉、
  形态是 `Mr. A. Fleming.`」。**实际那份第 43 行有正规署名**
  `By Alexandee Fleming, M.B., F.B.G.S.`——**`r` 被 OCR 认成了 `e`**。
  结论（不认首字母+姓）没变，但**我当时给的理由是错的**：
  那一份过不了门不是因为署名形态，是因为**名字被 OCR 打坏了**。
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
    EPITHET = {"of", "de", "da", "del", "della", "di", "du", "al", "ibn", "bin", "ben"}
    # ★★★ **`von`／`van` 不是地名式后缀，是世袭姓的小品词。**（Liebig 实测撞出）
    #
    #   `build_patterns("Justus von Liebig")` 原来把 **`Justus`（他的名）当姓**，
    #   因为 `von` 在 EPITHET 里，走的是「帕加马的盖伦」那条。
    #   **可是「冯·李比希」的姓就是李比希**，不是地名。
    #
    #   实测代价（Liebig #124 的 30 份 P1，走 `check_text` 全链）：
    #       name='Justus von Liebig'  surname='Justus'  → 过归属 **1/30**
    #       name='Justus Liebig'      surname='Liebig'  → 过归属 **26/30**
    #   **判据拿着他的名去找他的姓，找了三十份，找到一份。**
    #
    #   ★ 分界：`of` 确实是地名式（`Galen of Pergamon`——姓不是帕加马），**原样保留**；
    #     `von`／`van` 在近代德语／荷兰语人名里是**继承来的姓的一部分**
    #     （van Gogh、van Leeuwenhoek、von Braun、von Neumann）。
    #   ★★ **`de`／`da`／`di`／`du` 故意没动。** 它们两种都有
    #     （`de Gaulle` 是姓，`Leonardo da Vinci` 的 `Vinci` 是地名），
    #     **本轮没有语料能判**——名册里一个这样的人物都还没做过。
    #     **没有依据就不改**，留给撞上它的那一轮，别凭想象扩大射程。
    PARTICLE = {"von", "van"}
    if len(tokens) >= 3 and tokens[1].lower() in PARTICLE:
        # 「X von Y」：**Y 才是姓**（名 X + 姓 Y，小品词可有可无）
        first, last = re.escape(tokens[0]), re.escape(tokens[-1])
        surname = tokens[-1]
        tokens = [tokens[0], tokens[-1]]
    elif len(tokens) >= 3 and tokens[1].lower() in EPITHET:
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
        # ★★ v0.0.0.129：**名可以是缩写**——`By G. W. Carver` / `By Geo. W. Carver`。
        #   Carver #127 实测：他 35 份塔斯基吉公报署的全是 `By G. W. Carver`
        #   或 `G. W. Carver, M. S. Agr. Director`，**名从不写全**。
        #   旧式只认拼全的 `George`，于是 **63 条 `research.authorship-unproven`**——
        #   一整批货真价实的亲笔公报被判「无据」。
        #   ★ 这与本件已经学过的那一课同形（逐字稿用缩写标签 `MS:`，v0.0.0.10），
        #     **只是那次学在「说话人标签」上，没学到「署名」上。**
        #   ★★ **首字母必须对得上**，所以射程没有放宽：
        #     同姓的 **T**homas Nixon Carver 与 **W**. A. Carver 仍然匹配不上——
        #     而这两个人正是本人物抓源时的已知混淆源。
        _fw = tokens[0]
        _init = re.escape(_fw[0])
        _abbr3 = re.escape(_fw[:3])          # George → Geo.（19 世纪常见缩写）
        first_alt = rf"(?:{first}|{_abbr3}\.|{_init}\.)"
        name_rx = rf"{first_alt}[ \t]+(?:[A-Z][A-Za-z.'\-]{{0,15}}[ \t]+){{0,2}}{last}"
    # 姓氏单独出现也算（`By Steinhardt` 式的短署名）——但只用于**标签归属**判定，
    # 不用于署名判定，避免把「谈论他」的句子当成他的署名。
    surname_rx = re.escape(surname)

    # ★★★★ 2026-08-07：**OCR 会把姓拆成两段**——`BY JOSEPH WHIT WORTH, F.R.S.`
    #   Whitworth #152 实测：1858 年 NYPL 扫描本的标题页就是这样，整卷 335 KB 判成「无据」。
    #
    #   ★ 落这个之前先全库量过（**先量后改，今天已救过我两次**）：
    #     归档 25 个工作区里，「无署名证据的一手件」中姓被空白拆开的共 **14 份 / 6 个人物**。
    #     **但逐条读命中，大多数不是署名**：
    #       `Bes semer converting-vessels`（正文断词）、`PROFESSOR ROBERTS -AUSTEN`（版口）、
    #       `Professor Vir chow's larger works`（第三人称提及）、`Mart ens, elektrische`（索引条目）
    #     **真的是署名的只有 4 处**：
    #       Blackwell #118 `BY DRS. E. AND E. BLACK WELL` 与 `By Dr. R BLACK WELL`
    #       Bessemer #132 `I, the said HENRY BEs SEMER, do hereby declare`
    #       Whitworth #152 `BY JOSEPH WHIT WORTH, F.R.S.`
    #
    #   ★★ 所以**只把容错放进 `name_rx`（署名路径）**，`surname_rx` 一个字不动——
    #     后者用于「标签归属」，放宽它会把上面那些正文提及全部收进来。
    #   ★ 只容忍**空格或制表符**、且只在词内部（首末各留 ≥2 个字母），
    #     不容忍换行（换行的折行由别处的 `_LN` 管，两件事不要混）。
    #   ★★ 第一版写的是**一个** `[ \t]`，而真串是 `JOSEPH  WHIT  WORTH`——**双空格**，
    #     于是自测里我编的单空格样本过、**真扫描件一份都匹配不上**。
    #     这是同一天里第三次「合成假设比真实的干净」（前两次是 `_LN` 的空行、
    #     以及夹具把多行题页压成一行）。**改成 `{1,3}`，上限压住不让它跨栏。**
    def _split_tolerant(word: str) -> str:
        """→ 容忍 OCR 在词内插 1–3 个空白的正则。`Whitworth` → `Whit[ \\t]{1,3}worth` 等 6 种。"""
        if len(word) < 5:
            return re.escape(word)          # 太短的姓拆开后噪声压过信号
        alts = [re.escape(word)]
        for i in range(2, len(word) - 1):
            alts.append(re.escape(word[:i]) + r"[ \t]{1,3}" + re.escape(word[i:]))
        return "(?:" + "|".join(alts) + ")"

    _last_split = _split_tolerant(surname)
    if first != last:
        name_rx = name_rx.replace(last, _last_split, 1) if last in name_rx else name_rx
    # ★ 「同一段之内」：允许单换行（题头会折行），**禁止空行**（空行＝段落边界）。
    #   给 BYLINE_COAUTHOR 用；见那一条的注释。
    _LN = r"(?:[^\n]|\n(?!\s*\n))"

    return {
        "name": full_name,
        "surname": surname,
        # ★ v0.0.0.56：OCR 容错要拿**未转义**的名与姓做编辑距离，
        #   `first`/`last` 是 re.escape 过的，不能直接用。
        "first_word": tokens[0] if tokens else "",
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
        # ★★★★ v0.0.0.168 `A-byline-coauthor`：**他站在第二作者位。**
        #   Rosenhain #138 实测三份，题头都在、名字有一份一个字母都没错，全被判「无据」：
        #       `By J. A. EwiNG, F.R.S., …University of Cambridge, and Walter Rosenhain, B.A.`
        #       `By James A. Ewing, F.E.S., and Walter EoSENHAiN, 1851 Exhibition…`
        #   `BYLINE` 要求 `By` 后**紧跟**名字（中间只许敬称），于是
        #   **凡是他不排第一的合著，署名一律取不到**。
        #   与 Fleming（敬称）／Livermore（分行）／Martens（德文 `Von`）是同一族：
        #   **判据认得出名字，认不出名字前面那一小截。**
        #   ★ 护栏三条，缺一不可：
        #     1. 名字必须由 `and`／`&` 引出——不许是逗号列举里随便一个名字；
        #     2. `By` 到名字之间不许出现角色词（communicated/edited/reported/cited/
        #        reviewed/translated/according），否则 `By A. Smith, as reported by X` 会中；
        #     3. 距离上限 240 字符——学会题头带头衔与任职，确实长，但不能无限。
        #   ★★★★ 第一版写死 `[^\n]`，**真实的折行题头一份都匹配不到**——
        #     而我的自测用例把题头写成了一行，于是**自测全绿、实际全漏**。
        #     判据的用例比原文干净，就等于没测。改成 `_LN`：
        #     允许单换行，**禁止空行**——空行是段落边界，跨过去就不是同一个署名了。
        "BYLINE_COAUTHOR": re.compile(
            rf"\bBy\s+(?!{_LN}{{0,240}}?\b(?:communicated|edited|reported|cited|reviewed|"
            rf"translated|according)\b{_LN}{{0,20}}?{name_rx})"
            rf"{_LN}{{0,240}}?(?:\band\b|&)\s+"
            rf"(?:(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady)\.?\s+)*"
            rf"{name_rx}\b", re.I),
        "EDITORIAL": re.compile(
            rf"[\[\(][^\])]{{0,40}}\b(?:remarks|speech|address|excerpt|written|delivered|adapted)"
            rf"[^\])]{{0,40}}\bby\s+{name_rx}", re.I),
        # ★ v0.0.0.54 `A-byline-standalone`：期刊署名不带 `By`，独占一行。
        #   行尾允许**逗号**——合著论文把下一位作者接在下一行，就是这个形态。
        #   学位后缀（`M.B.`、`B.S. Lond.`、`F.R.C.S.`）允许出现，但**只能在名字之后**。
        # ★ v0.0.0.56：行尾允许 `AND <另一位作者>`——**合著论文把作者列在同一行**。
        #   Fleming #111 实测两份：`ALEXANDER FLEMING AND IAN H. MACLEAN.`、
        #   `ALEXANDER FLEMING, F.R.C.S., AND V. D. ALLISON, M.D.`
        #   旧式要求他的学位后缀之后就收行，**两份货真价实的合著论文全判「无据」**。
        #   **合著者在场不是反证，是共同署名。**
        "STANDALONE": re.compile(
            rf"^[ \t]*(?:(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady)\.?[ \t]+)*"
            rf"{name_rx}"
            rf"(?:[ \t]*,[ \t]*[A-Za-z][A-Za-z.]{{0,10}}(?:[ \t]+[A-Za-z][A-Za-z.]{{0,10}}){{0,2}})*"
            rf"(?:[ \t]*(?:,|\bAND\b)[ \t]*[A-Za-z][A-Za-z.]{{0,14}}"
            rf"(?:[ \t]+[A-Za-z][A-Za-z.]{{0,14}}){{0,3}})*"
            rf"[ \t]*[.,]?[ \t]*$", re.M | re.I),
        # ★ v0.0.0.56 `A-discussion-turn`：**学会讨论记录里的发言归属**。
        #   `Mr. ALEXANDER FLEMING said that when salvarsan was first in-`
        #   `Dr. ALEXANDER FLEMING said that his contribution to the discussion`
        #   这是 Proc R Soc Med 一类会议记录的标准形态——
        #   **敬称 + 全名 + 报道动词**，归属比正文里的 by 更硬（是记录者写的）。
        #   **必须要求全名**：`Mr. A. Fleming said` 一律不认（见下文同名陷阱）。
        "DISCUSSION": re.compile(
            rf"\b(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Lord|Lady)\.?[ \t]+{name_rx}"
            rf"(?:[ \t]+(?:said|remarked|observed|replied|added|asked|stated|"
            rf"pointed[ \t]+out|thought|agreed)\b|[ \t]*:)", re.I),
        # ↑ 冒号形 `Dr. ALEXANDER FLEMING:` 也是发言标记。
        #   **敬称是必需的**，所以「标题里的冒号」（`Jane Public: 某标题`）不会被误收。
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
def _edits_within(a: str, b: str, k: int) -> bool:
    """两串的编辑距离是否 ≤ k。只用于 OCR 容错，串都很短。"""
    la, lb = len(a), len(b)
    if abs(la - lb) > k:
        return False
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[lb] <= k


# ★ 档案馆／图书馆给「一批文书」起的名字——**它不是署名，是馆藏名**。
#   形态与题页署名难分（整行大写 + 名 + 姓），靠这些词区分。
_COLLECTION_RX = re.compile(
    r"\b(?:PAPERS|CORRESPONDENCE|COLLECTION|ARCHIVES?|MANUSCRIPTS?|MSS|FONDS"
    r"|RECORDS|CATALOGUE|CATALOG|FINDING\s+AID|INVENTORY|REGISTER"
    r"|Papers|Correspondence|Collection|Archives?|Manuscripts?)\b")


def _compound_signoff(text, first_l, parts):
    """**信末／文末署名**：`Royal Mint, June 9. W. C. Roberts-Austen.`

    ## 为什么现有的两条路都够不着

    `ocr_byline_evidence` 要整行是 `By …` 或全大写；
    `standalone_ocr` 形态 B 要**整行只有名字**（`re.fullmatch`）。
    而 Nature 读者来信的体例是 **`地点, 日期. 名字.`** ——两条都不满足。

    实测（Roberts-Austen #135，30 份 P1）：这一类 **10 份**，
    9 份是真签名，1 份是版口（已由页码规则挡掉）。
    ★ 02-conversations 观察 ③ 引的正是这个形态
    （`Royal Mint, June 9. W. C. Roberts-Austen.`）——
    **道稿把它当他的签名用，而归属门认不出来。**

    ## 三条设防

    1. **只对复姓开**（与 `_compound_hit` 同一道闸）——单姓走不到这里，
       Fleming 那类「首字母 + 别的中名 + 同姓」的防线原样保留。
    2. **必须在行尾**，且名字前面要有句点（`… . 名字.`）——
       署名收尾的形态；散文中间提到他的名字不算。
    3. **页码打头的一律不算**：`148 Mr. F. Osmond and Prof. W. C. Roberts- A listen.`
       是**版口**，不是签名。实测就是这一份把 10 打成了 9。
       （`v0.0.0.146` 的版口守卫只挡全大写那种，这种是混合大小写。）
    """
    init = first_l[:1]
    for line in text.split("\n"):
        s = line.strip()
        if not s or len(s) > 200 or not s.endswith("."):
            continue
        if re.match(r"^\d{1,4}\s", s):          # ← 设防 3：版口
            continue
        tail = [x for x in re.split(r"[^A-Za-z]+", s) if x][-5:]   # ← 设防 2：只看行尾
        low = [x.lower() for x in tail]
        for i, a in enumerate(low):
            if not ((len(a) >= 4 and _edits_within(a, first_l, 2))
                    or (len(a) == 1 and a == init)):
                continue
            rest = low[i + 1:]
            for j, b in enumerate(rest):
                if len(b) < 3:
                    continue
                if not (_edits_within(b, parts[0], 2) or b.endswith(parts[0])):
                    continue
                nxt = rest[j + 1:j + 3]
                if any(_edits_within(c, parts[1], 2) or c.endswith(parts[1]) for c in nxt):
                    return s
    return None


def _compound_hit(toks, first_l, parts):
    """**复姓的署名行**：名可以是缩写，但**复姓每一段都必须在，且按顺序**。

    ## 为什么复姓要另开一条（Roberts-Austen #135 实测）

    30 份 P1 里 `ocr_byline_evidence` 只认出 **1** 份，而印本上他的署名是：

        By W. C. Roberts-Austen, C.B., F.R.S.
        By Professor W. C. EOBERTS-AUSTEN, C.B., F.R.S.
        By Pbofessob W. C. ROBERTS-AUSTEN, C.B., F.R.S.

    **署名就在那儿，是判据读不出来。** 两处叠着挡：
      ① `last_l` 是带连字符的 `roberts-austen`，分词把印本切成 `roberts`+`austen`，
         **距离 7 和 8**——`_edits_within(…, 2)` 永远不成立；
      ② 名写成缩写 `W.`，被 `len(a) < 4` 挡在外面。

    ★★★ **② 那道门是对的，不能一般性地拆。** 它是 Fleming #111 装的：
      同名陷阱恰恰是「首字母 + 别的中名 + 同姓」（该人物有 `A. Grant Fleming`）。
      **单姓人物一律不走本函数**，那道防线原样保留。

    ## 复姓凭什么可以放宽

    **姓本身补上了名让出的那份识别力。** 单姓 `Fleming` 配一个首字母区分不了人；
    而复姓要求**两段都命中**，`W. Roberts`／`W. Austen`／`Charles Austen`
    这些半截的一个都进不来（自测里全是反例）。
    **首字母仍必须对上**——`A. Grant Roberts-Austen` 照样挡住。

    ★ 这条**没有让 Roberts-Austen 过门**：端到端 3/30 → 12/30，
      离一手占比门差得远。**改的是「读不出来」，不是「够不够」。**
    """
    init = first_l[:1]
    for i, t0 in enumerate(toks):
        a = t0.lower()
        # 名：拼全（距离 ≤2）**或**单个首字母且与目标一致
        if not ((len(a) >= 4 and _edits_within(a, first_l, 2))
                or (len(a) == 1 and a == init)):
            continue
        tail = [x.lower() for x in toks[i + 1:]]
        for j, b in enumerate(tail):
            if len(b) < 3:
                continue
            # 第一段：容错，或被前缀污染（`1XFLEMING` 那一类）
            if not (_edits_within(b, parts[0], 2)
                    or (b.endswith(parts[0]) and len(b) - len(parts[0]) <= 3)):
                continue
            # ★ 其余各段必须**紧随其后**依次出现（中间最多隔一个词，容 OCR 插字）
            nxt = tail[j + 1:j + 1 + 2 * (len(parts) - 1)]
            k = 0
            for p in parts[1:]:
                while k < len(nxt) and not (_edits_within(nxt[k], p, 2)
                                            or nxt[k].endswith(p)):
                    k += 1
                if k >= len(nxt):
                    break
                k += 1
            else:
                return True
    return False


def ocr_byline_evidence(text, first, last):
    """**名字被 OCR 打坏的署名行。** 命中返回那一行，否则 None。

    Fleming #111 逐份读完 12 份未过的文件，真正的病根不是串栏而是**名字被打坏**：

        By Alexandbb Fleming, F.R.C.S., Estg.      ← er → bb
        By Alexandee Fleming, M.B., F.B.G.S.       ← r  → e
        ALEXANDER FLENMING.                        ← 多插一个 N
        ALEXANDER FLEMIING, F.R.C.S.,              ← 多插一个 I
        By Professor ALEXANDElA 1XFLEMING, F.R.C.S. ← 整段被打坏

    **放宽到编辑距离是危险方向**——它同样会把同姓的另一个人放进来。
    三条设防，缺一不可：

    1. **必须名与姓都在，且都是完整词。**
       `A. Fleming` 一律不认——同名陷阱恰恰是「首字母 + 别的中名 + 同姓」
       （本人物有 `A. Grant Fleming`，裸检索 `Fleming A` 时排第一）。
       **要求完整的名，就把这一整类挡在外面。**
    2. **名与姓各自的编辑距离 ≤2**，且**长度必须相近**（±2）。
    3. **必须落在署名结构里**：行首、或 `By` 之后；且该行不长于 80 字符。
       散文中间碰巧出现的近似词不算。
    """
    first_l, last_l = first.lower(), last.lower()
    # ★ 复姓专用的**行尾署名**（Nature 来信体例 `地点, 日期. 名字.`），见 `_compound_signoff`
    _p = [p for p in re.split(r"[^A-Za-z]+", last_l) if p]
    if len(_p) >= 2:
        _hit = _compound_signoff(text, first_l, _p)
        if _hit:
            return _hit
    for line in text.split("\n"):
        # ★★★ **`#` 开头的是我们自己写进文件的头，不是语料。**
        #   `standalone_ocr` 一直挡着（`s.startswith("#")`），本函数原来不用挡——
        #   它只看 `By …` 与整行大写，而 `# title: …` 两条都不像。
        #   **复姓那条路一开就不成立了**：它扫全部 token 位置，于是
        #       `# TITLE: W. C. ROBERTS-AUSTEN PAPERS`
        #   会被当成他的署名放行。**那是 ingest 写的头，因为档案馆按「他的文书」编目。**
        #   ★ 实测撞出这一类的过程记在 ㉕：模拟版一度报 Barton 109/109，
        #     去读命中，11/14 是 `# title: Clara Barton Papers…`——
        #     **判据把我们自己的元数据读回来当成了他的署名证据。**
        if line.lstrip().startswith("#"):
            continue
        s = line.strip()
        if not s or len(s) > 80:
            continue
        # ★ **必须像署名行**：`By …` 打头 / 整行大写 / 不以句读收尾的短行。
        #   散文中间碰巧出现的近似词不算——这一条是自测抓出来的
        #   （不加时「标题里的冒号」与「版权归别人」两条反例都被误放行）。
        # ★★★ v0.0.0.157：署名前缀**不止英文的 `By`**。
        #   Martens #134 抓源实测（拿他真实的印本署名打的）：
        #     `Von Adolf Martens.`        ← 目标本人的德文署名 → **旧版不认**
        #     `Von A. Martens, Berlin.`   ← 目标最常见的印本署名 → **旧版不认**
        #   本函数只认 `^by\s+` 与整行大写，于是**一个德语人物的自署论文会被整批判成不是他写的**。
        #   后果不是漏一两份：**一手占比是硬门（standard 0.50 / deep 0.65）**，
        #   德语／法语／意大利语人物会被系统性压低一手比例，
        #   而门只做算术、不问「分档对不对」（见 [[related-to-him-is-not-written-by-him]] 的反面）。
        #   ★ 只加**行首**的前缀，不动别处：`Eduard von Martens` 里的 `von` 是贵族小品词，
        #     它走的是整行大写那条路，不受影响。
        starts_by = bool(re.match(r"^(?:by|von|par|di|av|af|door|de|av\.)[ \t]+", s, re.I))
        allcaps = s == s.upper() and any(c.isalpha() for c in s)
        if not (starts_by or allcaps):
            continue
        # ★★★ v0.0.0.146：**「页码 + 全大写人名」是版口，不是署名。**
        #   Bessemer #132 实测：1905 自传每张偶数页的版口都是那种形状，
        #   而 pp.327 之后那一章是他**同名的儿子**写的。不设这道防线，本函数会把
        #   版口当成 A-byline-ocr，**给儿子写的正文盖上父亲的 HIS-OWN 章**——
        #   一条带「证据」的假归属，比没有证据更难查。
        #   ★ 本文件此前只挡住了**带冒号**的那一种版口（靠「冒号后全大写」判定）；
        #     这一种没有冒号，从来没被挡过。
        #   ★★ 页码在左在右都挡（有些书版口在右）。
        if re.match(r"^\d{1,4}\s+[A-Z][A-Z .,'-]*$", s) or \
           re.match(r"^[A-Z][A-Z .,'-]*\s+\d{1,4}$", s):
            continue
        body = re.sub(r"^(?:by|von|par|di|av|af|door|de)[ \t]+", "", s, flags=re.I)
        body = re.sub(r"^(?:(?:Sir|Dame|Prof(?:essor)?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady)\.?[ \t]+)*",
                      "", body, flags=re.I)
        toks = [t for t in re.split(r"[^A-Za-z]+", body) if t][:5]
        if len(toks) < 2:
            continue
        # ★★★ 复姓（`Roberts-Austen` 这一类）**必须单独走一条**，见 `_compound_hit`。
        #   走不通就 `continue`：复姓在这里**永远匹配不上**——
        #   `last_l` 是带连字符的 `roberts-austen`，而分词把印本上的
        #   `ROBERTS-AUSTEN` 切成 `roberts` + `austen`，两段与整串的距离是 7 和 8。
        _parts = [p for p in re.split(r"[^A-Za-z]+", last_l) if p]
        if len(_parts) >= 2:
            # ★★★ **馆藏名不是署名。** `W. C. ROBERTS-AUSTEN PAPERS AND CORRESPONDENCE`
            #   是档案馆给一批文书起的名字，整行大写、名与复姓俱全——
            #   **形态与题页署名一模一样**，而它出现在任何一份数字化检索工具书里。
            #   ★ 只否决**整行大写**那一支：`By …` 打头是明示署名，
            #     而「By X. Papers read before the Society」这种正文不该被误伤。
            if not starts_by and _COLLECTION_RX.search(s):
                continue
            if _compound_hit(toks, first_l, _parts):
                return s
            continue
        a = toks[0].lower()
        # ★ **名必须是完整词**——`A. Fleming` 这一整类在这里被挡住。
        #   同名陷阱恰是「首字母 + 别的中名 + 同姓」。
        if len(a) < 4 or not _edits_within(a, first_l, 2):
            continue
        # 姓在其后几个词里挑（中间可能夹中名或缩写），**同样必须是完整词**
        for b_raw in toks[1:]:
            b = b_raw.lower()
            if len(b) < 4:
                continue
            if _edits_within(b, last_l, 2):
                return s
            # `1XFLEMING`：姓被前缀污染，允许姓作为尾部出现
            if b.endswith(last_l) and len(b) - len(last_l) <= 3:
                return s
    return None


def _blocked(cand, last_l, namesakes):
    """候选姓与某个**已声明同名**的距离 ≤ 与目标姓的距离 → 拒绝。

    ★ `Thomson` 与 `Thompson` 距离仅 1。不声明就会把十二个 Thompson 收进来——
      Thomson #129 探测实测：索引里挨着他名字的 27 个号，**16 个是别人的**。

    ★★ **它只比姓。同姓的同名者它一个也挡不住**——见 `_initial_blocked`。
    """
    plain = [_last_token(ns) for ns in namesakes]
    d = next((k for k in range(3) if _edits_within(cand, last_l, k)), 3)
    return any(ns != last_l and _edits_within(cand, ns, d) for ns in plain)


def normalize_namesakes(raw) -> tuple:
    """`known_namesakes` 归一成姓名字符串元组。**两种形态都认。**

    ★★★★ 2026-08-10：既有契约是**字符串数组**（Coffin：`["Charles A. Coffin"]`），
    而我给 Nasmyth #153 写的是**对象数组**（每条带 `name`/`years`/`who`/常见称呼，
    因为那个人物有 19 个同姓者，只写名字说不清谁是谁）。

    **喂对象进去不会崩，会静默变成垃圾**：`_last_token({"name": …, "years": …})`
    取的是 `str(dict)` 的最后一个词 → `'years'`。于是 `_blocked` 拿着
    `['years', 'who', …]` 当同名者的姓去比对，**整道护栏形同虚设**。

    ★ 实测时它**看起来还是对的**——`By Alexander Nasmyth` 仍被拒绝，
      但拒它的是名字不匹配，不是护栏。**两个错抵消，绿得毫无意义。**
      [[two-errors-cancelled-so-the-gate-stayed-green]]

    所以两种形态都认，且**认的是同一个东西**：那个人的姓名串。
    """
    out = []
    for item in (raw or ()):
        if isinstance(item, str):
            if item.strip():
                out.append(item.strip())
        elif isinstance(item, dict):
            nm = re.sub(r"[*_`]", "", str(item.get("name")
                        or item.get("canonical_name") or "")).strip()
            if nm:
                out.append(nm)
            # 别名（如兄长 Patrick 在图录里作 `Peter Nasmyth`）也要进来，
            # ★ **但只收与本条姓名共享词元的**。实测 Nasmyth #153 的「文献里怎么称呼」
            #   一栏里混着 `my father`、`the English Hobbema` 这种**不是姓名的称呼**——
            #   收进去之后 `_last_token` 会把 `father`／`hobbema` 当成同名者的姓，
            #   于是同名者列表里多出两个根本不存在的姓氏。**噪声不该进护栏。**
            _toks = {t.lower() for t in re.split(r"[^A-Za-z]+", nm) if len(t) > 2}
            for alias in (item.get("文献里怎么称呼") or item.get("aliases") or ()):
                if not (isinstance(alias, str) and alias.strip()):
                    continue
                _a = re.sub(r"[*_`]", "", alias).strip()      # 去掉 Markdown 强调
                if _toks & {t.lower() for t in re.split(r"[^A-Za-z]+", _a) if len(t) > 2}:
                    out.append(_a)
    return tuple(dict.fromkeys(out))          # 去重且保序


# ★★★★ 2026-08-10（Gantt #156）：**这张表原来只有英国爵位与教职衔。**
#   排期前拿本人物的真实同名场测了一遍护栏，**10 条错 5 条**，两种新形态都栽在这张表上：
#     · `Col. Henry Gantt`（1831–1884，南军上校）——**姓名与目标人物完全相同**，
#       唯一的区分点就是那个 `Col.`，而表里没有军衔。
#     · `Mrs. H. L. Gantt` / `Mrs. Henry L. Gantt`（他妻子）——
#       **这两个串把目标人物的全名完整包含在内**，表里没有 `Mrs`。
#   ★ 机制本来就在（`_title_blocked` 拿候选行的头衔去比同名者声明的头衔），
#     **缺的只是这张表认不认得那些头衔**。
#   ★★ **`Mr` 有意不进表**：目标人物一手文献一律作 `Mr. Gantt`，把它算成头衔会把他自己挡掉。
_TITLES = re.compile(
    r"\b(Sir|Dame|Lord|Lady|Baronet|Bart|Bt|Rev|Revd"
    r"|Mrs|Miss|Ms|Mme|Mlle"                      # 指向另一个人的称谓（配偶／女性亲属）
    r"|Col|Colonel|Capt|Captain|Maj|Major|Gen|General|Lt|Lieut|Lieutenant|Adm|Admiral"  # 军衔
    r"|Dr|Prof|Professor)\b\.?", re.I)


def _titles_of(name) -> frozenset:
    """从一个姓名串里取出头衔集合（小写）。`Bart`/`Bt` 归并到 `baronet`。"""
    out = set()
    for t in _TITLES.findall(str(name)):
        t = t.lower()
        out.add("baronet" if t in ("bart", "bt", "baronet") else t)
    return frozenset(out)


def _own_toks(first_l, last_l, own_mid=""):
    """目标人物自己的词元集（名 + 中名 + **姓**）。

    ★★★★ 我第一版在 `standalone_ocr` 里直接写了 `full_name`，**那个名字不在这个函数的作用域里**。
      `py_compile` 是绿的、`--self-test` 也是绿的（自测走的是别的入口），
      **真跑一次才会 NameError**——[[a-checker-nothing-calls-is-not-a-checker]] 第五批那个形状。
      所以这里改成从**这个函数真的拿得到的三个参数**重建词元集。
    """
    out = {str(first_l or "").lower(), str(last_l or "").lower()}
    for t in re.split(r"[^A-Za-z]+", str(own_mid or "")):
        if t:
            out.add(t.lower())
    return {t for t in out if t}


def _given_tokens(name: str) -> set:
    """名字里除姓之外的词元（小写，去点）。`W. Horsley Gantt` → {`w`, `horsley`}。"""
    toks = [t.strip(".,;:'\"").lower() for t in re.split(r"\s+", str(name or "")) if t.strip(".,;:")]
    return {t for t in toks[:-1] if t and t.isalpha()} if len(toks) > 1 else set()


def _given_name_blocked(cand_line: str, own_tokens, namesakes) -> str:
    """**同姓、无头衔，只有名字不同**——这一层此前完全没有。

    ★★★★ 2026-08-10（Gantt #156）：拿本人物的真实同名场测护栏，扩了头衔表之后
      **10 条仍错 2 条**：`By W. Horsley Gantt` 与 `By Harvey Gantt` 双双被放行。
      它们与目标人物**同姓、都没有头衔**，唯一的区别就是名字——
      **而护栏此前只比姓**，那正是 [[test-the-guard-against-this-persons-namesake]] 的原始缺陷。

    ## ★★★★ 判法是「只认显式声明」，**一个字都不推断**

    只看同名者条目里的 `distinguishing_given_tokens`（人手写的）。
    候选行里出现其中任一词元即拒。

    ★ **第一版是推断的**（拿同名者名字里「目标人物没有的」词元当区分点），
      **自测当场把它打红**：Adams #131 是**父子同名**，
      `Comfort Avery Adams` 与 `Comfort Avery Adams, Jr.` **词元完全相同**，
      唯一的区别是 `Jr.`；而 `own_mid` 没声明时 `avery` 会被算成「父亲独有」，
      **于是把儿子（目标人物）自己挡掉**。
      → **推断出来的区分点在父子同名上必然出错，改成只认人写的。**
    ★★ 没写这个字段的人物，这一层**不生效**（返回空），**不影响任何既有人物**。
    """
    if not namesakes:
        return ""
    for ns in namesakes:
        if not isinstance(ns, dict):
            continue
        for tok in ns.get("distinguishing_given_tokens") or ():
            t = str(tok).strip()
            if len(t) < 3:
                continue
            if re.search(r"\b" + re.escape(t) + r"\b", cand_line, re.I):
                return t
    return ""

def _title_blocked(cand_line, own_titles, namesakes) -> str:
    """署名带的头衔**目标没有、而某个已声明同名者有** → 拒绝，返回那个头衔。

    ## 撞出它的那一次（Nasmyth #153，**在抓源落地之前**）

    `_blocked` 只比姓，`_initial_blocked` 只比中名首字母。而 Nasmyth 的同名场是：
    有**两位与他同名同姓**的准男爵（Sir James Nasmyth 第一代、第二代）。
    实测（本判别器加之前）：

        By Alexander Nasmyth（父，画家）      → 拒绝 ✓
        By Patrick / Peter Nasmyth（兄）      → 拒绝 ✓
        **By Sir James Nasmyth, Baronet      → 放行 ✗**

    ★ 顺带更正我自己写过的一句话：我在 #153 的开工记录里写「护栏只比姓，
      对这个人物几乎等于不设防」。**实测证伪**——画家家族那一串它全挡住了，
      真正漏的只有同名同姓的准男爵这一路。**说射程要量，不要从记忆里推。**

    ## 为什么必须是证据驱动，不能见 `Sir` 就拦

    **Whitworth 本人 1869 年受封准男爵**，语料里就有 `Sir Joseph Whitworth, Bart.`。
    一律拦 `Sir` 会把**他自己的署名**挡在门外——那正是 Coffin 那次
    「两个方向同时错」的重演。

    所以判法是：**署名的头衔不在目标自己的头衔里，且命中某个已声明同名者的头衔** → 拦。
    `own_titles` 为 `None`（没声明）时**一律不拦**，并由调用方印「未核，不是通过」。
    """
    if own_titles is None:
        return ""                      # 没声明就不判——**不判不等于通过**
    cand_t = _titles_of(cand_line)
    if not cand_t:
        return ""
    ns_t = set()
    for ns in namesakes or ():
        ns_t |= _titles_of(ns)
    for t in sorted(cand_t - set(own_titles)):
        if t in ns_t:
            return t
    return ""


def _last_token(name):
    toks = [x for x in re.split(r"[^A-Za-z]+", str(name)) if x]
    return toks[-1].lower() if toks else ""


def _mid_initial(name):
    """`Charles A. Coffin` → `a`；`C. A. Coffin` → `a`；没有中名 → `''`。

    取**姓之前的最后一个首字母**（单字母 token）。
    """
    toks = [x for x in re.split(r"[^A-Za-z]+", str(name)) if x]
    if len(toks) < 3:
        return ""
    for x in reversed(toks[:-1]):
        if len(x) == 1:
            return x.lower()
    return ""


_SUFFIX = re.compile(r",?\s*\b(JR|SR|II|III)\b\.?\s*$", re.I)


def _suffix_of(name):
    """`C. A. ADAMS, JR.` → `jr`；没有 → `''`。"""
    m = _SUFFIX.search(str(name).strip())
    return m.group(1).lower() if m else ""


def _strip_suffix(name):
    return _SUFFIX.sub("", str(name).strip()).strip(" ,")


def _initial_blocked(line, last_l, namesakes, own_mid):
    """**同姓、只差一个中名首字母**——`Charles A. Coffin` 不是 `Charles L. Coffin`。

    ## 撞出它的那一次（Coffin #130，2026-08-05，**在抓源落地之前**）

    `_blocked` 只比姓。而 Coffin 的同名者**姓完全相同**：

    | | 我们要的 | 不要的 |
    |---|---|---|
    | | Charles **L.** Coffin，电弧焊工艺发明人 | Charles **A.** Coffin，GE 首任总裁、汤姆森—休斯顿总裁 |

    实测（护栏加之前）：
      - `Charles A. Coffin.` → **放行**（当成他的署名收进来）
      - `C. L. Coffin.` → **拦下**（他自己的缩写形态反而不认）

    **两个方向同时错**：把别人的收进来，把他自己的挡在外面。
    而 Charles A. Coffin 正是 Elihu Thomson（#129）的合伙人——
    **当年电气刊物里的「Coffin」大量指他**，语料池里到处都是。

    ## 判法

    姓相同（距离 ≤1）时：署名里的中名首字母若与**目标的**不同、
    且命中任一**已声明同名的**中名首字母 → 拒绝。
    署名没有中名首字母的，**不拦**（宁可放过，不可拦错）。

    ## ★★ 世代后缀（`Jr.`）：能认定的和**认定不了的**

    Adams #131：**他父亲也叫 Comfort Avery Adams**——姓、名、中名首字母**全同**，
    `_initial_blocked` 那把尺子在这里完全失效。唯一能正面认定他的是 `Jr.`：
    1904 年卷 23 把他印作 `C. A. Adams, Jr.`。

    改之前**又是两个方向同时错**：`C. A. ADAMS, JR.`（能认定他的那一种）**被拦**，
    因为整行正则不容尾缀；而 `C. A. ADAMS`（认定不了的那一种）**放行**。

    ★★★ **`Jr.` 解决一部分；另一部分要靠「查这个人是干什么的」，不是靠判据。**
    我最初写「不带 `Jr.` 的 `C. A. Adams` 与父亲分不开」——**那句是错的，已更正**：
    抓源方查出**他父亲是克利夫兰的服装商人，根本不在工程刊物上出现**，
    所以工程刊物里的 `C. A. Adams` 不与父亲混。
    ★★ 教训：**「我分不开」与「客观上分不开」是两件事。**
    我把前者写成了后者，而多问一句「他父亲是干什么的」就分开了。

    **真正分不开的只剩 Conrad A. Adams**（缩写相同、同刊同代）——
    那一条只能靠内容与场合逐份判，**本件不假装能分开**，
    并要求写进 `attribution_basis.disputed_works`。

    ## ★ 已知射程缺口（实测，不是猜的）

    **形态 C（末行黏连签名）认不出纯缩写署名**：`of the weld C. L. Coffin.` 拦下。
    因为形态 C 要求名也对得上（≥4 字母），而 `C.`／`L.` 各只有一个字母。
    形态 B（整行只有名字）已开了「声明中名首字母且相同则放行」的例外，形态 C **没开**——
    它是句中锚定的，再放宽会把正文里的人名收进来。
    **代价：Coffin 这类惯用缩写的人，黏连在末行的签名会漏。宁可漏。**
    """
    if not own_mid:
        return False
    cand_mid = _mid_initial(line)
    if not cand_mid or cand_mid == own_mid:
        return False
    for ns in namesakes:
        if _edits_within(_last_token(ns), last_l, 1) and _mid_initial(ns) == cand_mid:
            return True
    return False


def standalone_ocr(text, first_l, last_l, namesakes, own_mid="", own_titles=None):
    """**独占一行的署名，名或姓被 OCR 打坏**——`Elihtt Thomson.`／`Pror. Tuomson :—`。

    ## 为什么要它

    Thomson #129 实测：56 份语料里 24 份被判「无据」，而证据都在文里，
    只是**名字被 OCR 打坏了**：
      - 期刊文末署名：`Elihtt Thomson.`（`Elihu` → `Elihtt`）
      - 学会讨论发言标签：`Pror. Tuomson :—`／`Pror. Taomson`／`Exinv Toomson`
        （抓源方实测：**几乎每次坏法都不一样，严格匹配找不到一半**）

    既有的编辑距离容错**只作用于 `By …` 与全大写行**；
    这两类都不是——于是整条路走不通。

    ## ★★★ 同名护栏：容错不许把两个真名连起来

    `Thomson` 与 `Thompson` 的编辑距离是 **1**。容忍 2 就把十二个 Thompson
    全并进来了——而 Thomson #129 的探测**实测**：1887 年索引里挨着他名字的
    27 个专利号，**16 个是别人的，其中十二个姓 Thompson**。

    所以本件要求调用方**声明已知同名**（`--namesake`）：
    候选姓氏若与任一已声明同名的距离 **≤ 与目标姓氏的距离**，一律拒绝。
    **宁可漏，不可把别人的东西记成他的。**
    """
    lines = text.splitlines()
    n = len(lines) or 1
    HON = (r"(?:Sir|Dame|Prof(?:essor)?|Pror[a-z]*|Prorf?|Dr|Mr|Mrs|Ms|Rev|Lord|Lady|"
           r"Pbesident|President|Chairman|Cuareman)")
    for idx, raw in enumerate(lines):
        s = raw.strip()
        if not (4 <= len(s) <= 80) or s.startswith("#"):
            continue

        # ── 形态 A：发言标签 `Pror. Tuomson :—…`
        #    ★ **敬称是必需的**——既有设计就是靠它挡住「标题里的冒号」
        #      （`<某名>: 某标题` 在导航/og:title 里重复出现）。**我第一版丢了它，自测当场抓到。**
        m = re.match(rf"^(?:{HON}[A-Za-z]{{0,6}}\.?[ \t]+)+([A-Za-z][A-Za-z.'\-]{{2,20}}"
                     rf"(?:[ \t]+[A-Za-z][A-Za-z.'\-]{{2,20}}){{0,2}})[ \t]*[:：]", s, re.I)
        if m:
            toks = [x for x in re.split(r"[^A-Za-z]+", m.group(1)) if x]
            cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
            if (cand and _edits_within(cand, last_l, 2)
                    and not _blocked(cand, last_l, namesakes)
                    and not _initial_blocked(m.group(1), last_l, namesakes, own_mid)
                    and not _title_blocked(m.group(1), own_titles, namesakes)
                    # ★ 第四道：同姓、无头衔、只有名字不同（Gantt #156 的 W. Horsley / Harvey）
                    and not _given_name_blocked(m.group(1), None, namesakes)):
                return s
            continue

        # ── 形态 B：**整行只有名字**（可带句点/逗号），如 `Elihtt Thomson.`
        #    ★ 位置护栏：只认**文首 10% 或文末 10%**——署名在头或尾。
        #      正文深处独占一行的名字是索引/参考文献，**自测里就有这条反例**。
        pos = idx / n
        if not (pos <= 0.10 or pos >= 0.90):
            continue
        # ★ `{0,20}` 而非 `{1,20}`：允许 `C. L. Coffin.` 这种首字母缩写。
        #   原来的 `{1,20}` 要求每段至少两个字母，**把他自己的缩写形态挡在外面**
        #   （Coffin #130 实测：`C. L. Coffin.` 被拦，而 `Charles A. Coffin.` 被放行）。
        if not re.fullmatch(r"[A-Za-z][A-Za-z.'\-]{0,20}(?:[ \t]+[A-Za-z][A-Za-z.'\-]{0,20}){1,3}[.,]?",
                            _strip_suffix(s)):
            continue
        # ★★★ 世代后缀（Coffin 之后的第二类同名：**父子同名同姓**）
        #   Adams #131 实测：他父亲也叫 Comfort Avery Adams，
        #   1904 年卷 23 把他印作 `C. A. Adams, Jr.`，后期卷又不带 Jr.。
        #   **带 Jr. 是正面认定他的最硬证据**，而改之前它反而被拦下（整行正则不容尾缀）。
        s_core = _strip_suffix(s)
        toks = [x for x in re.split(r"[^A-Za-z]+", s_core) if x]
        cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
        if (not cand or not _edits_within(cand, last_l, 2)
                or _blocked(cand, last_l, namesakes)
                or _initial_blocked(s, last_l, namesakes, own_mid)
                or _title_blocked(s, own_titles, namesakes)
                or _given_name_blocked(s, None, namesakes)):
            continue
        # 名也必须对得上（≥4 字母、距离 ≤2）——**只有首字母缩写的一律不认**
        if any(len(x) >= 4 and _edits_within(x.lower(), first_l, 2) for x in toks[:-1]):
            return s
        # ★ 例外：**声明了中名首字母且署名的中名首字母与之相同**时，
        #   `C. L. Coffin.` 这类纯缩写署名可以放行——
        #   因为此时中名首字母**正面认定了目标、同时排除了已声明的同名**
        #   （`C. A. Coffin.` 会先被 `_initial_blocked` 挡在上面）。
        #   没声明 own_mid 就仍旧一律不认，**射程不变**。
        if own_mid and _mid_initial(s) == own_mid:
            return s

    # ── 形态 G：**方括号里的编者告示式署名**
    #    `[COMMUNICATED AFTER ADJOURNMENT BY Comrort A. ADAMS.]`
    #    ★ Adams #131 的第 71 份（1904 年卷 XXIII 那篇 14 页署名文）就是这个形态：
    #      不是发言标签（没有冒号），也不是题页署名（在正文中间、且带方括号）。
    #      `Comrort` 是 `Comfort` 的 OCR 讹字。
    #    这是学会会刊的常见体例（会后书面补充），**值得认，不是一次性特例**。
    m = re.search(r"\[[^\]]{0,60}\bBY[ \t]+((?:[A-Za-z][A-Za-z.,'\-]{0,14}[ \t]+){1,3}"
                  r"[A-Za-z][A-Za-z.'\-]{2,20})\.?[ \t]*\]", text)
    if m:
        toks = [x for x in re.split(r"[^A-Za-z]+", _strip_suffix(m.group(1))) if x]
        cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
        if (cand and _edits_within(cand, last_l, 2)
                and not _blocked(cand, last_l, namesakes)
                and not _initial_blocked(m.group(1), last_l, namesakes, own_mid)
                and any(len(x) >= 4 and _edits_within(x.lower(), first_l, 2) for x in toks[:-1])):
            return " ".join(m.group(0).split())[:300]

    # ── 形态 F：**学会讨论环节的发言标签** `Comfort A. Adams: I think that…`
    #    ★★★ 撞出它的那一次（Adams #131）：61/71 份语料判「无据」，而它们全是讨论发言。
    #      形态 A 要求敬称（`Pror. Tuomson :—`），而这类**没有敬称**；
    #      形态 B 要求整行只有名字，而这类**后面直接跟正文**。
    #    真实形态（抓源方逐卷实测）：**混合大小写、行中、无敬称**，
    #      且首字母常因分栏折行跑到姓的上一行。
    #    ★★ 与「页眉」的分界（**这一条是全部要害**）：
    #      `ADAMS: HEYLAND MACHINE` 是论文页眉，不是发言——
    #      实测 31 卷共 210 处这种，**无一是发言**；卷 XX 与卷 XXIV 真实发言数为 0 和 0，
    #      **单这两卷就会制造 82 条幻影发言**。
    #    判别用三条，缺一不可：
    #      ① 名字**不是光秃秃的姓**——要有首字母或名（`C. A. Adams` / `Comfort A. Adams`）
    #      ② 冒号后**不是全大写**（全大写＝页眉的论文标题）
    #      ③ 冒号后要有**成句的正文**（至少若干个词）
    for idx_f, raw in enumerate(lines):
        s = raw.strip()
        if not (12 <= len(s) <= 400):
            continue
        # ★★ 两处实测形态（Adams #131 的 conv 源）：
        #   ① **首名可能被 OCR 削掉头一个字母**：`omfort A. Adams (by letter):`
        #      —— 所以第一段允许小写起头；姓仍须完整且与目标对得上。
        #   ② **冒号前可能有括注**：`(by letter)` / `(communicated after adjournment)`。
        m = re.match(r"^((?:[A-Za-z][A-Za-z.,'\-]{0,14}[ \t]+){1,3}[A-Z][A-Za-z.'\-]{2,20})"
                     r"(?:[ \t]*\([^)]{0,44}\))?[ \t]*:[ \t]*(.+)$", s)
        if not m:
            continue
        name, rest = m.group(1), m.group(2).strip()
        # ★★★ 与**导航菜单**的分界。既有反例：
        #     `Jane Public: Background & bio` / `Jane Public: Investment philosophy` / …
        #   我第一版用「冒号后 ≥5 个词」来挡，**那条是错的**——
        #   实测语料是**分栏折行**的，真发言的首行常常只有三四个词：
        #     `omfort A. Adams (by letter): Without wishing to subtract`（4 词）
        #     `C. A. Adams (communicated after adjournment): Not hav-`（2 词）
        #     `C. A. Adams: How many poles? :`（一句短问，3 词）
        #   **按词数挡会把这三种真发言全丢掉。**
        #   真正的分界是**重复**：菜单把同一个标签铺很多行，发言不会。
        if len(re.findall(r"[A-Za-z']+", rest)) < 2:
            continue
        # ★★★ 与菜单的真正分界：**下一非空行是不是又一个标签**。
        #   我上一版用「同一标签出现 ≥3 次 → 菜单」，**那条是错的**：
        #   实测 `src-90d7a04c81ea` 一份里有**他本人的 5 段发言**（同一场讨论里发言五次很正常），
        #   被我整份判成菜单。**重复的是菜单的排版，不是发言的次数。**
        #   菜单：每一行都是标签，标签之间没有正文。
        #   发言：标签之后跟的是正文，下一个标签隔着许多行。
        _LAB = (r"^(?:[A-Za-z][A-Za-z.,'\-]{0,14}[ \t]+){1,3}[A-Z][A-Za-z.'\-]{2,20}"
                r"(?:[ \t]*\([^)]{0,44}\))?[ \t]*:")
        _nxt = next((x.strip() for x in lines[idx_f + 1:] if x.strip()), "")
        _prv = next((x.strip() for x in reversed(lines[:idx_f]) if x.strip()), "")
        # ★ 前后**任一**边也是标签 → 菜单。
        #   只看下一行不够：**菜单的最后一项后面没有标签了**，会漏过去
        #   （自测的既有反例正是这么漏的）。
        if re.match(_LAB, _nxt) or re.match(_LAB, _prv):
            continue
        letters = [c for c in rest if c.isalpha()]
        if letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.8:
            continue                       # ★ 全大写 → 页眉的论文标题，不是发言
        # ★★★ 标题式大小写也要挡：`Elihu Thomson: The Field of Experimental Research`
        #   全大写那一条挡不住它（它是 Title Case 不是 ALL CAPS）。
        #   **自测的既有反例「标题里的冒号」当场抓到我这个漏。**
        #   判据：实词里首字母大写的占比 > 0.6 → 是标题不是话。
        words = [w for w in re.findall(r"[A-Za-z']+", rest) if len(w) >= 3]
        if words and sum(1 for w in words if w[0].isupper()) / len(words) > 0.6:
            continue
        toks = [x for x in re.split(r"[^A-Za-z]+", _strip_suffix(name)) if x]
        if len(toks) < 2:
            continue                       # ★ 光秃秃的姓不算
        cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
        if (not cand or not _edits_within(cand, last_l, 2)
                or _blocked(cand, last_l, namesakes)
                or _initial_blocked(name, last_l, namesakes, own_mid)):
            continue
        # 名要对得上：全名（≥4 字母且距离 ≤2）或首字母与目标一致
        if (any(len(x) >= 4 and _edits_within(x.lower(), first_l, 2) for x in toks[:-1])
                or (first_l and toks[0][:1].lower() == first_l[:1].lower())):
            return s[:300]

    # ── 形态 E：**专利正文开头的自述式署名** `Be it known that I, CHARLES L. COFFIN, of Detroit,`
    #    ★ 撞出它的那一次（Coffin #130 的 us395878）：题页被 OCR 打成
    #      `CHARLES Ii. (OFFIN, OF DETROIT, MICHIGAN.`——中名 `L.` 成了 `Ii.`、
    #      `C` 成了左括号，形态 D 的正则一个字都对不上。
    #      **而正文第一句是干净的**：`Be it known that I, CHARLES L. COFFIN, of t Detroit,`。
    #    ★★ 这是**最强的一种**：它是第一人称自述（`I, 姓名`），不是第三方给的标签。
    #      题页会被 OCR 打坏，这一句因为在正文里、字号正常，往往是完好的。
    m = re.search(r"[Bb]e it known that I,?\s+([A-Z][A-Za-z.'\-]{0,20}"
                  r"(?:\s+[A-Z][A-Za-z.'\-]{0,20}){1,3})\s*,", text)
    if m:
        toks = [x for x in re.split(r"[^A-Za-z]+", m.group(1)) if x]
        cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
        if (cand and _edits_within(cand, last_l, 2)
                and not _blocked(cand, last_l, namesakes)
                and not _initial_blocked(m.group(1), last_l, namesakes, own_mid)
                and (any(len(x) >= 4 and _edits_within(x.lower(), first_l, 2) for x in toks[:-1])
                     or (own_mid and _mid_initial(m.group(1)) == own_mid))):
            return " ".join(m.group(0).split())

    # ── 形态 D：**专利题页署名** `CHARLES L. COFFIN, OF DETROIT, MICHIGAN.`
    #    ★ 撞出它的那一次（Coffin #130）：A/B/C 三形态**一个都认不出专利题页**——
    #      形态 B 要求整行只有名字（≤4 段、行中不许有逗号），题页有「, OF 城市, 州.」；
    #      形态 C 要求名字在行尾，题页行尾是州名。
    #      于是 15 份专利全判「无据」，而署名就印在题页第一行。
    #      **既有三形态是照期刊文章的样子长的，不是照专利的样子长的。**
    #    射程：`姓名, OF 地名[, ASSIGNOR …]`，且**必须带 `OF 地名`**——
    #      光有逗号不算，否则正文里「…, Coffin, and others…」就混进来了。
    for idx, raw in enumerate(lines):
        s = raw.strip()
        if not (10 <= len(s) <= 160):
            continue
        m = re.match(r"^([A-Z][A-Za-z.'\-]{0,20}(?:[ \t]+[A-Z][A-Za-z.'\-]{0,20}){1,3})[ \t]*,"
                     r"[ \t]*(?:OF|OE|0F)[ \t]+[A-Z]", s)
            
        if not m:
            continue
        toks = [x for x in re.split(r"[^A-Za-z]+", m.group(1)) if x]
        cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
        if (not cand or not _edits_within(cand, last_l, 2)
                or _blocked(cand, last_l, namesakes)
                or _initial_blocked(m.group(1), last_l, namesakes, own_mid)):
            continue
        if any(len(x) >= 4 and _edits_within(x.lower(), first_l, 2) for x in toks[:-1]):
            return s
        # 纯缩写题页（`C. L. COFFIN, OF DETROIT, MICH.`）同形态 B 的例外
        if own_mid and _mid_initial(m.group(1)) == own_mid:
            return s

    # ── 形态 C：**签名被 OCR 并进了最后一行正文**
    #    `tion of the coil C. Elihu Thomson.` —— 期刊文末签名与末段黏在一起。
    #    ★ 射程钉死在**最后 3 行**：再放宽就会把正文里「据 Elihu Thomson 说」收进来。
    for idx in range(max(0, n - 3), n):
        s = lines[idx].strip()
        if not s or s.startswith("#"):
            continue
        m = re.search(r"(?:^|[.。!?]\s+)([A-Z][A-Za-z.'\-]{1,20}"
                      r"(?:[ \t]+[A-Z][A-Za-z.'\-]{1,20}){1,3})[ \t]*[.,]?[ \t]*$", s)
        if not m:
            continue
        toks = [x for x in re.split(r"[^A-Za-z]+", m.group(1)) if x]
        cand = next((x.lower() for x in reversed(toks) if len(x) >= 4), None)
        if (not cand or not _edits_within(cand, last_l, 2)
                or _blocked(cand, last_l, namesakes)
                or _initial_blocked(m.group(1), last_l, namesakes, own_mid)):
            continue
        if any(len(x) >= 4 and _edits_within(x.lower(), first_l, 2) for x in toks[:-1]):
            return s
    return None


def join_short_lines(text, max_len=14, run=2):
    """把连续的**极短行**并成一行，供比对用（不写回语料）。

    扫描件里被拆开的说话人标记就是这个形态：

        Dr.
        ALEXANDER
        FLEMING:

    三行没有任何一行同时含名与姓。并行之后成为 `Dr. ALEXANDER FLEMING:`，
    `DISCUSSION` 与 `STANDALONE` 才认得出。

    只并**连续 ≥2 行、每行都不超过 `max_len` 字符**的段落——
    正常散文行远长于此，不会被误并。
    """
    out, buf = [], []
    for line in text.split("\n"):
        s = line.strip()
        if s and len(s) <= max_len:
            buf.append(s)
            continue
        if len(buf) >= run:
            out.append(" ".join(buf))
        buf = []
        out.append(line)
    if len(buf) >= run:
        out.append(" ".join(buf))
    return "\n".join(out)


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

# ★ v0.0.0.57：**书评里被评那本书的署名不是竞争署名。**
#   Fleming #111 的 `freelance-science-1952` 是他写的书评，开头印着：
#       Louis Pasteur. Free Lance of Science. By Rend J. Dubos. (Pp. 418. 18s.)
#       London: Victor Gollancz. 1951.
#   反向检查把 `By Rend J. Dubos.` 当成别人的署名，于是**一篇他写的书评被判无据**。
#   **书评必然引被评书的作者**——这是整类文体的固有形态，不是这一份的特例。
#   判法：`By <他人名>` 之后 120 字符内出现**书目要素**
#   （页数 `Pp. 418`、定价 `18s.`／`$`／`£`、出版社行、四位年份）→ 判为**被引之作**。
CITED_WORK = re.compile(
    r"\(?\s*Pp?\.\s*\d{2,4}|\b\d{1,3}s\.\s*\d{0,2}d?\.|[$£]\s?\d"
    r"|\b(?:London|New York|Edinburgh|Oxford|Cambridge|Philadelphia|Boston)\s*:"
    r"|\b(?:Gollancz|Macmillan|Longmans|Churchill|Saunders|Blackwell|Heinemann)\b",
    re.I)

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
# ★★ v0.0.0.80：**必须锚在行首**（与 `OTHER_BY` 同法）。
#   撰稿人小传是**独占一行**的（`Jane Doe is President of the Foo Society.`），
#   而 `X is President` 出现在行中间时是**普通句子，不是署名**。
#   Barton #117 实测：不锚行首时 12 条「文中他人署名」里 **7 条是假阳**——
#     「the family grounds. Mr Roosevelt is President」（日记里的一句话）
#     「M. Moynier is President, is the only International Committee.」（关系从句）
#     「Thus we see that the Emperor of **Japan** is the President of the」
#        ——名字那一组抓到的是「Japan」，因为它是 `is the President` 前最后一个大写词
#   **这些都会被报成「卷内混有第三方材料」，而卷内并没有。**
OTHER_ROLE = re.compile(
    r"^[ \t]{0,4}([A-Z][a-z]{1,20}(?: [A-Z][a-z.']{1,20}){0,3}) is (?:the |a |an )?"
    r"(Chair|Chairman|President|Managing Director|Executive Director|Director|"
    r"Rabbi|Professor|founder|co-founder|CEO|Vice President|Senior)\b", re.M)
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


def check_text(text, pat):
    """先按原文判；全不中时，再用「连续短行并起来」的副本重判一次。

    ★ v0.0.0.56：**说话人标记会被 OCR 拆成连续几行。**
    Fleming #111 的 `vaccine-therapy-disc-1910` 里是 `Dr.` / `ALEXANDER` / `FLEMING:`
    三行，没有任何一行同时含名与姓，所有名字正则都匹配不上。

    **不能把两份文本拼起来一起判**——第一版那么写，位置一错乱，
    版权页那两条老对照当场被误判（`© 1998 by …` 变成了 A-byline，
    「版权归别人」被误放行）。**归一是重试，不是拼接。**
    """
    ok, code, ev, counter = _check_one(text, pat)
    if ok:
        return ok, code, ev, counter
    joined = join_short_lines(text)
    if joined != text:
        ok2, code2, ev2, counter2 = _check_one(joined, pat)
        # ★ **并短行只用来救「说话人标记」，不救别的档。**
        #   自测抓到：并行会把版权页上下两行的名字并到一起，
        #   于是「版权归 Richard Roe」那条反例被误放行成 A-copyright。
        #   **归一放宽了文本，就必须收窄它能证明的东西。**
        if ok2 and code2 in ("A-discussion-turn", "A-turns"):
            return ok2, code2 + "(并短行后)", ev2, counter2
    return ok, code, ev, counter


def _check_one(text, pat):
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
            if pat["SURNAME"].search(m.group(1)):
                continue
            # ★ v0.0.0.57：书评里被评那本书的署名，不算竞争署名。
            if CITED_WORK.search(text[m.end():m.end() + 120]):
                continue
            counter.append(m.group(0).strip())

    for code, key in (("A-byline", "BYLINE"),
                      ("A-byline-coauthor", "BYLINE_COAUTHOR"),
                      ("A-editorial", "EDITORIAL")):
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
            # ★★★★ 2026-08-10：**头衔判别必须接在这一条分支上。**
            #   我第一次把它接进了 `A-byline-standalone` 与 `standalone_ocr`——
            #   而 `By Sir James Nasmyth, Baronet` 走的是**这一条 `A-byline`**，
            #   于是加完判别器实测仍然放行。**接在了没人走的分支上。**
            #   ★ 同一个文件里上一轮刚撞过同形的事（`A-byline-standalone` 当时整个绕过了同名护栏），
            #     **两次都是「以为接上了，没沿真实路径验」**。
            #     [[a-checker-nothing-calls-is-not-a-checker]]
            _t = _title_blocked(m.group(0), pat.get("own_titles"),
                                tuple(pat.get("namesakes") or ()))
            if _t:
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
            # ★★★★ 2026-08-07：**这条路此前完全不查同名护栏。**
            #   `_blocked` / `_initial_blocked` 只装在 `standalone_ocr`（OCR 容错那条），
            #   而 `STANDALONE` 走的是精确正则，于是同姓同名只差中名首字母的人**长驱直入**。
            #
            #   定向复现（`Charles L. Coffin` 的护栏，喂了 `Charles A. Coffin` 与 `own_mid='l'`）：
            #       `CHARLES A. COFFIN, OF BOSTON…` 放在**文首 30%**   → **放行** A-byline-standalone
            #       同上放在**文末且带地址块**                          → **放行** A-signature-block
            #       同上放在文末、无地址块                              → 拒（**只是被位置规则挡的**）
            #
            #   ★★ 自测里那条反例（`_tail(...)` 版）一直是绿的，**红得凑巧**：
            #     它恰好落在唯一被位置规则挡住的那种摆法，
            #     而注释写着它在测「护栏射程」。
            #     ——[[counter-example-red-can-be-red-by-coincidence]] 的教科书形态。
            #
            #   ★ 这个人正是护栏被造出来要挡的那一个：Charles A. Coffin 是 GE 首任总裁，
            #     而当年电气刊物里的「Coffin」大量指他，语料池里到处都是。
            _ns = tuple(pat.get("namesakes") or ())
            _mid = str(pat.get("own_mid") or "")
            _last_l = str(pat.get("surname") or "").lower()
            if _ns and _initial_blocked(m.group(0), _last_l, _ns, _mid):
                continue
            # ★★★★ 头衔判别（Nasmyth #153）：`By Sir James Nasmyth, Baronet` 此前**放行**。
            #   见 `_title_blocked` 文件头——**证据驱动，不是见 Sir 就拦**
            #   （Whitworth 本人就是准男爵，一律拦会把他自己的署名挡在门外）。
            if _ns and _title_blocked(m.group(0), pat.get("own_titles"), _ns):
                continue
            code = "A-signature-block" if signed else "A-byline-standalone"
            a, b = max(0, m.start() - 60), min(len(text), m.end() + 60)
            return True, code, " ".join(text[a:b].split()), counter

    # ★ v0.0.0.56 `A-discussion-turn`：学会讨论记录里的发言归属。
    #   `Mr. ALEXANDER FLEMING said that…` —— 记录者写的，比正文里的 by 更硬。
    #   与显式 `By` 同级，**可以顶着反证走**：同场讨论里本来就有别人发言，
    #   把「别人也发了言」当反证会把整类会议记录判死。
    if pat.get("DISCUSSION"):
        m = pat["DISCUSSION"].search(text)
        if m:
            a, b = max(0, m.start() - 40), min(len(text), m.end() + 80)
            return True, "A-discussion-turn", " ".join(text[a:b].split()), counter


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

    # ★ v0.0.0.56 `A-byline-ocr`：名字被 OCR 打坏的署名行。
    #   **最弱的一档，受反证约束**——它靠编辑距离，本来就比逐字命中松。
    if not counter:
        hit = ocr_byline_evidence(text, pat.get("first_word") or "", pat.get("surname") or "")
        # ★★★ v0.0.0.137：**同名护栏必须也管这条路**。
        #   v0.0.0.136 把护栏加在了 `standalone_ocr` 上，而本函数**跑在它前面**、
        #   返回的却是同一个 `A-byline-ocr` 码——于是护栏形同虚设。
        #   Coffin #130 的自测当场抓到：`CHARLES A. COFFIN, OF BOSTON`（GE 总裁）被盖章。
        #   复核 Thomson #129 的用例更狠：**`ELIHU THOMPSON.` 也从这条路放行**——
        #   那正是当初造这道护栏要挡的人。
        #   （v0.0.0.136 的自测之所以是绿的，是因为它用的串是 `A. Thompson`，
        #     那个串根本走不到这条路。**自测绿了，挡的却不是这条路。**）
        if hit:
            _n = tuple(pat.get("namesakes", ()))
            _last = (pat.get("surname") or "").lower()
            _toks = [x for x in re.split(r"[^A-Za-z]+", hit) if x]
            _cand = next((x.lower() for x in reversed(_toks) if len(x) >= 4), "")
            _mid = str(pat.get("own_mid", "") or "").lower()[:1]
            if not (_blocked(_cand, _last, _n) or _initial_blocked(hit, _last, _n, _mid)):
                return True, "A-byline-ocr", hit, counter

    # ★★★ v0.0.0.136：**名字被 OCR 打坏的独占署名／发言标签**——最后一条路。
    #   Thomson #129 实测：56 份里 24 份走到这里仍判「无据」，而证据都在文里：
    #     期刊文末 `Elihtt Thomson.`（`Elihu`→`Elihtt`）
    #     讨论标签 `Pror. Tuomson :—`／`Pror. Taomson`／`Exinv Toomson`
    #   既有的编辑距离容错**只作用于 `By …` 与全大写行**，这两类都不是。
    #   ★ 同名护栏见 `standalone_ocr` 文件头：`Thomson` 与 `Thompson` 距离仅 1，
    #     而该人物的探测**实测**索引里挨着他名字的 27 个号有 16 个是别人的
    #     （十二个姓 Thompson）——**容错不许把两个真名连起来。**
    if not counter:
        ev = standalone_ocr(text, pat.get("first_word", "").lower(),
                            pat.get("surname", "").lower(),
                            tuple(pat.get("namesakes", ())),
                            str(pat.get("own_mid", "") or "").lower()[:1],
                            pat.get("own_titles"))
        if ev:
            return True, "A-byline-ocr", ev, counter
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
    # ★ v0.0.0.56（Fleming #111 逐份读完 12 份未过文件后的实测形态）
    ("合著者与他同行",
     "ON THE OCCURRENCE\n\nJANE Q. PUBLIC AND IAN H. MACLEAN.\n\n"
     "The occurrence was examined in a series of normal subjects here.\n"),
    ("合著者同行·带学位后缀",
     "ON THE DEVELOPMENT\n\nJANE Q. PUBLIC, F.R.C.S., AND V. D. ALLISON, M.D.\n\n"
     "The development of resistant strains was followed over some weeks.\n"),
    ("说话人标记被拆成三行",
     "DISCUSSION ON VACCINE THERAPY\n\nDr.\nJANE\nPUBLIC:\n"
     "I have used the method in a considerable number of cases over the years.\n"),
    ("学会讨论发言",
     "DISCUSSION ON THE USE\n\nMr. JANE Q. PUBLIC said that when the drug was first "
     "introduced there was much confusion about the dosage to be used.\n"),
    ("OCR 打坏的署名·姓少一个字母",
     "ON A REMARKABLE ELEMENT\n\nBy Jane Q. Publie, M.B., F.B.G.S.\n\n"
     "The substance was first noticed during some investigations here.\n"),
    ("OCR 打坏的署名·多插一个字母",
     "A long letter to the editor runs on for a while about the subject.\n" * 30
     + "JANE Q. PUBLIIC.\nInoculation Department,\nSt. Mary's Hospital, Jan. 5.\n"),
    # ★ v0.0.0.57（Fleming #111 `freelance-science-1952` 实测）：
    #   书评必然引被评书的作者，那不是竞争署名。
    ("书评：被评书的署名在开头",
     "Reviews\nFREELANCE OF SCIENCE\nLouis Pasteur. Free Lance of Science.\n"
     "By Richard Q. Roebuck. (Pp. 418. 18s.) London: Victor Gollancz. 1951.\n"
     + "The book is more than a mere biography of the great master here.\n" * 25
     + "JANE Q. PUBLIC.\nLondon, W.1.\n"),
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
    # ★ v0.0.0.56：OCR 容错**必须挡住「首字母 + 别的中名 + 同姓」这一整类**——
    #   本人物的同名陷阱恰是 `A. Grant Fleming`，裸检索 `Fleming A` 时排第一。
    ("首字母+姓（同名陷阱的形态）",
     "STUDIES IN SOMETHING\n\nQ. Public, M.B. B.S. Lond., Director, Department\n"
     "of Systematic Bacteriology, Some Hospital, London.\n"),
    ("首字母+别的中名+同姓",
     "ON PUBLIC HEALTH\n\nA. Grant Public, M.D.\n\n"
     "The survey was conducted in Montreal over several years running.\n"),
    # ★ v0.0.0.57：**书目豁免不许放宽过头**——没有书目要素的他人署名仍是反证。
    ("他人署名后面没有书目要素",
     "SOME TITLE\nBy Richard Q. Roebuck.\n"
     + "The argument proceeds over several paragraphs in the usual way.\n" * 25
     + "JANE Q. PUBLIC.\nLondon, W.1.\n"),
    ("并短行不许把散文并成署名",
     "The work\nwas done\nat a\nhospital\nin London\nover time.\n"
     "Jane Q. Public is mentioned in the body of this text somewhere later.\n"),
    ("OCR 容错不许把别人的名字放进来",
     "ON SOMETHING ELSE\n\nBy Richard Q. Roebuck, M.D.\n\n"
     "The matter was investigated at some length in the following pages.\n"),
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
    # ★★★ v0.0.0.129 回归守卫：**名缩写的署名必须认得，同姓异名的必须认不得。**
    #   Carver #127 实测：35 份公报署的是 `By G. W. Carver`，旧式只认拼全的 `George`，
    #   **63 条 authorship-unproven**。而放宽之后**射程不许跟着放宽**——
    #   同姓的 Thomas Nixon Carver（T）与 W. A. Carver（W）是本人物已知的混淆源。
    _cv = build_patterns("George Washington Carver")
    for _line, _should in (("By G. W. Carver As we learn", True),
                           ("By GEO. W. CARVER, M. S. AGR.", True),
                           ("By GEORGE W. CARVER, M. S. Agr.", True),
                           ("By George Washington Carver", True),
                           ("By T. N. Carver of Harvard", False),
                           ("By W. A. Carver", False),
                           ("By John F. Carew", False)):
        if bool(_cv["BYLINE"].search(_line)) is not _should:
            bad.append(f"名缩写署名：{_line!r} 的 BYLINE 判定应为 {_should}")

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

    # ── ★★ v0.0.0.80 `OTHER_ROLE` 必须锚行首：四条**真实假阳夹具**（Barton #117）──
    #   不锚行首时，12 条「文中他人署名」里 7 条是假阳，
    #   而它们会被读成「卷内混有第三方材料」——**卷内并没有**。
    for s, should, why in [
        ("the family grounds. Mr Roosevelt is President", False, "日记里的一句话"),
        ("of which M. Moynier is President, is the only International Committee.",
         False, "关系从句，句中"),
        ("Thus we see that the Emperor of Japan is the President of the",
         False, "名字组抓到的是「Japan」——`is the President` 前最后一个大写词"),
        ("Jane Doe is President of the Foo Society.", True, "**真的撰稿人小传，独占一行**"),
        ("  Mary Smith is Director of Nursing at St. Luke's.", True, "行首允许缩进"),
    ]:
        got = bool(OTHER_ROLE.search(s))
        ok = got is should
        if not ok:
            bad.append(f"OTHER_ROLE：{s[:48]!r} 应为 {should}，实得 {got}")
        print(f"  {'✓' if ok else '✗'} OTHER_ROLE {should}｜{why}：{s[:50]!r}")

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

    # ★★★ v0.0.0.136：`A-byline-ocr` 的十条对照（Thomson #129 实测形态）。
    #   五条必须认出（名或姓被 OCR 打坏），五条必须拒绝——
    #   **其中三条是同名陷阱**：Thomson↔Thompson 编辑距离只有 1，
    #   而该人物探测实测「索引里挨着他名字的 27 个号有 16 个是别人的」。
    #   ★ 另两条是我第一版真踩到的：**标题里的冒号**（丢了敬称要求）
    #     与**正文深处独占一行的名字**（丢了位置要求）——**自测当场抓住。**
    print("\n══ A-byline-ocr 十条对照（v0.0.0.136）══")
    _NS = {"thompson", "quimby", "thoms"}
    _tail = lambda s: "body line\n" * 30 + s
    _mid = lambda s: "body line\n" * 30 + s + "\nbody line" * 30
    for _lbl, _s, _want in (
            ("Elihtt Thomson.（文末署名）", _tail("Elihtt Thomson."), True),
            ("ELIHU THOMSON.（全大写文末）", _tail("ELIHU THOMSON."), True),
            ("Pror. Tuomson :—（发言标签）", "Pror. Tuomson :—On my own account, having had", True),
            ("Pror. Taomson : —（发言标签）", "Pror. Taomson : —That is, with a small current", True),
            ("Prof. Thomson:（干净发言标签）", "Prof. Thomson: I am sure we have", True),
            ("A. Thompson（**同名**）", _tail("A. Thompson."), False),
            ("Elihu T. Quimby（**同名**）", _tail("Elihu T. Quimby."), False),
            ("E. P. Thomson（只有缩写）", _tail("E. P. Thomson."), False),
            ("正文深处独占一行的名字", _mid("Elihu Thomson."), False),
            ("标题里的冒号", "Elihu Thomson: The Field of Experimental Research", False)):
        _got = bool(standalone_ocr(_s, "elihu", "thomson", _NS))
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"A-byline-ocr：{_lbl}")

    # ★★★ 同姓同名护栏（Coffin #130）——`_blocked` 只比姓，同姓的它一个也挡不住
    print("\n══ 同姓不同中名首字母 六条对照（v0.0.0.137）══")
    _NSC = ("Charles A. Coffin",)            # GE 首任总裁；与目标同姓同时代同行业
    for _lbl, _s, _want in (
            ("Charles L. Coffin.（**目标本人**）", _tail("Charles L. Coffin."), True),
            ("C. L. Coffin.（他惯用的缩写形态）", _tail("C. L. Coffin."), True),
            ("Charles A. Coffin.（**GE 总裁，不是他**）", _tail("Charles A. Coffin."), False),
            ("C. A. Coffin.（**同上，缩写**）", _tail("C. A. Coffin."), False),
            ("CHARLES A. COFFIN, President.（**带职务**）", _tail("CHARLES A. COFFIN, President."), False),
            ("of the weld Charles A. Coffin.（**末行黏连**）",
             _tail("of the weld Charles A. Coffin."), False)):
        _got = bool(standalone_ocr(_s, "charles", "coffin", _NSC, "l"))
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"同姓中名护栏：{_lbl}")

    # ★★★ 世代后缀：**父子同名同姓**（Adams #131 —— 比 Coffin 那类更难）
    # ★★★ 形态 F：学会讨论环节的发言标签（Adams #131 —— 61/71 份因它而判无据）
    # ★★★ 版口不是署名（Bessemer #132，v0.0.0.146）
    print("\n══ 版口不是署名 五条对照（v0.0.0.146）══")
    _PB = build_patterns("Henry Bessemer")
    for _lbl, _s, _want in (
            ("★ 儿子写的那一章，版口却印着父亲的名（**不挡就会盖错章**）",
             "328 HENRY BESSEMER\nrr^HE unfortunate destruction of my father's notes.\n", False),
            ("父亲的正文，同样的版口（**版口对谁都不算署名**）",
             "156 HENRY BESSEMER\nThe manufacture of iron in this country.\n", False),
            ("★ 同一种版口，页码在右",
             "HENRY BESSEMER 328\nsome prose follows here.\n", False),
            ("★★ 反向：专利说明书必须仍然认出",
             "Be it known that I, HENRY BESSEMER, of Queen Street Place,\ncivil engineer.\n", True),
            ("★★ 反向：真署名必须仍然认出",
             "By HENRY BESSEMER, F.R.S.\nSome remarks follow.\n", True)):
        _got, _code, _ev, _ = check_text(_s, _PB)
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"版口护栏：{_lbl}（got={_got} code={_code}）")

    print("\n══ 学会讨论的发言标签（形态 F） 八条对照（v0.0.0.137）══")
    _NSF = ("Conrad A. Adams", "Alton D. Adams", "Edwin Plimpton Adams", "Lee F. Adams")
    for _lbl, _s, _want in (
            ("Comfort A. Adams: First, I want tosay…（v38p1 真实样张）",
             _tail("Comfort A. Adams: First, I want tosay that I fear Mr. Peek has misinterpreted my statement"), True),
            ("C. A. Adams: I think all of those present…（缩写形态）",
             _tail("C. A. Adams: I think all of those present who have been concerned with research work"), True),
            ("**ADAMS: HEYLAND MACHINE**（页眉，31 卷共 210 处无一是发言）",
             _tail("ADAMS: HEYLAND MACHINE"), False),
            ("**ADAMS: DESIGN OF INDUCTION MOTORS**（页眉）",
             _tail("ADAMS: DESIGN OF INDUCTION MOTORS"), False),
            ("**Alton D. Adams: …**（同名，中名 D）",
             _tail("Alton D. Adams: I wish to point out that the load factor here"), False),
            ("Adams: I think that…（**光秃秃的姓，射程内不认，宁可漏**）",
             _tail("Adams: I think that at least a part of Mr."), False),
            ("omfort A. Adams (by letter): …（**首名被 OCR 削掉头一字母 + 括注**）",
             _tail("omfort A. Adams (by letter): Without wishing to subtract in any way "
                   "from the credit due Professor Brooks"), True),
            ("Comfort A. Adams (communicated after adjournment): …（另一种括注）",
             _tail("Comfort A. Adams (communicated after adjournment): I should like to add "
                   "one further point here"), True)):
        _got = bool(standalone_ocr(_s, "comfort", "adams", _NSF, "a"))
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"形态 F：{_lbl}")

    print("\n══ 方括号编者告示式署名（形态 G） 三条对照（v0.0.0.137）══")
    for _lbl, _s, _want in (
            ("[COMMUNICATED AFTER ADJOURNMENT BY Comrort A. ADAMS.]（真实样张，Comrort 是讹字）",
             _tail("[COMMUNICATED AFTER ADJOURNMENT BY Comrort A. ADAMS.]}"), True),
            ("**…BY Alton D. Adams.**（同名，中名 D）",
             _tail("[COMMUNICATED AFTER ADJOURNMENT BY Alton D. Adams.]"), False),
            ("**…BY Charles P. Steinmetz.**（别人）",
             _tail("[COMMUNICATED AFTER ADJOURNMENT BY Charles P. Steinmetz.]"), False)):
        _got = bool(standalone_ocr(_s, "comfort", "adams",
                                   ("Conrad A. Adams", "Alton D. Adams"), "a"))
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"形态 G：{_lbl}")

    print("\n══ ★★★★ Gantt #156 的真实同名场（12 条，2026-08-10 排期前实测）══")
    #   ★ 这 12 条**在第一份语料落地之前**跑过一次，当时 10 条错 5 条。
    #     写成常设自测是因为：**判据的自测只能证明它挡得住它见过的那一类**，
    #     而每换一个人物，失效的方式都不一样（相似姓 → 相同姓 → 全名被包含 → 头衔方向相反）。
    _G_NS = [
        {"name": "Henry Gantt", "titles": ["Col", "Colonel"]},          # 同名南军上校
        {"name": "Mary E. Snow Gantt", "titles": ["Mrs"],               # 他妻子
         "distinguishing_given_tokens": ["Snow"]},
        {"name": "William Andrew Horsley Gantt", "titles": ["Dr"],
         "distinguishing_given_tokens": ["Horsley"]},
        {"name": "Harvey Gantt", "distinguishing_given_tokens": ["Harvey"]},
        {"name": "Love Rosa Gantt", "distinguishing_given_tokens": ["Rosa"]},
        {"name": "Edward W. Gantt", "distinguishing_given_tokens": ["Edward"]},
    ]
    _G_OWN_TITLES = []          # ★ 本人物无头衔——候选行里只要出现头衔就不是他
    for _line, _accept, _why in [
        ("BY H. L. GANTT.", True, "他惯用的缩写"),
        ("By Henry L. Gantt.", True, "全名"),
        ("By Henry Laurence Gantt", True, "ASME 讣告的中名拼写"),
        ("TESTIMONY OF HENRY LAWRENCE GANTT", True,
         "★ 国会记录用 Lawrence——**也是一手用法，不是 OCR 讹误**"),
        ("Mrs. H. L. Gantt", False,
         "★★★★ 他妻子——**这个串把 `H. L. Gantt` 完整包含在内**"),
        ("Mrs. Henry L. Gantt", False, "★★★★ 同上"),
        ("Col. Henry Gantt", False,
         "★★★ 同名上校——**姓名完全相同，只能靠军衔挡**；本人物无头衔，规则方向是反的"),
        ("By W. Horsley Gantt", False, "同姓＋同校（Johns Hopkins）＋同城"),
        ("By Harvey Gantt", False, "同姓建筑师——本人物族别正是建造采购师"),
        ("By Edward W. Gantt", False, "同姓政客"),
        ("By Love Rosa Gantt", False, "同姓医生，生卒年与本人重叠"),
        ("By Frederick W. Taylor", False, "他的同事——Taylor 写他的段落最多"),
    ]:
        _b = (_title_blocked(_line, _G_OWN_TITLES, _G_NS)
              or _given_name_blocked(_line, None, _G_NS))
        _got = ("gantt" in _line.lower()) and not _b
        _ok = _got == _accept
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _accept else '应拒绝'}　"
              f"{_line[:36]}　（{_why[:34]}）")
        if not _ok:
            bad.append(f"Gantt 同名场：{_line}")

    print("\n══ 父子同名，只有 Jr. 能正面认定 四条对照（v0.0.0.137）══")
    _NSA = ("Comfort Avery Adams",)          # 他父亲的全名与他一字不差
    for _lbl, _s, _want in (
            ("C. A. ADAMS, JR.（1904 年卷 23 的印法）", _tail("C. A. ADAMS, JR."), True),
            ("COMFORT AVERY ADAMS, JR.（全名带 Jr.）", _tail("COMFORT AVERY ADAMS, JR."), True),
            ("Comfort Avery Adams, Jr.（小写）", _tail("Comfort Avery Adams, Jr."), True),
            ("**ADAMS: THE TESTING OF ELECTRICAL MACHINERY**（页眉，不是发言）",
             _tail("ADAMS: THE TESTING OF ELECTRICAL MACHINERY"), False)):
        _got = bool(standalone_ocr(_s, "comfort", "adams", _NSA, "a"))
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"世代后缀：{_lbl}")

    print("\n══ 专利正文自述式署名（形态 E） 三条对照（v0.0.0.137）══")
    for _lbl, _who, _ns, _mid, _s, _want in (
            ("Be it known that I, CHARLES L. COFFIN, of t Detroit（题页被打坏时的救命稻草）",
             "Charles L. Coffin", ("Charles A. Coffin",), "l",
             _tail("Be it known that I, CHARLES L. COFFIN, of t Detroit, in the county of Wayne"), True),
            ("**Be it known that I, CHARLES A. COFFIN, of Boston**（GE 总裁）",
             "Charles L. Coffin", ("Charles A. Coffin",), "l",
             _tail("Be it known that I, CHARLES A. COFFIN, of Boston, in the county of Suffolk"), False),
            ("**Be it known that I, ELIHU THOMPSON, of Lynn**（同名）",
             "Elihu Thomson", ("Thompson",), "",
             _tail("Be it known that I, ELIHU THOMPSON, of Lynn"), False)):
        _p = build_patterns(_who)
        _p["namesakes"] = _ns
        _p["own_mid"] = _mid
        _got = check_text(_s, _p)[0]
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"形态 E：{_lbl}")

    # ★★★ v0.0.0.157：**非英文的署名前缀**（Martens #134 抓源实测打回来的）
    #   本函数原先只认 `^by\s+` 与整行大写。而德语印本的署名是 `Von …`——
    #   **一个德语人物的自署论文会被整批判成不是他写的**，
    #   而一手占比是硬门（standard 0.50 / deep 0.65）。
    print("\n══ 非英文署名前缀（v0.0.0.157）══")
    for _s, _want in (
            ("By Adolf Martens.", True),
            ("Von Adolf Martens.", True),                 # ← 旧版在这里返回 None
            ("VON ADOLF MARTENS.", True),
            # ↓ 反向对照：加了 `Von` 之后，这些**仍然必须挡住**
            ("Von Alfred Martens, Architekt.", False),    # 建筑师，1881-1920
            ("Von A. Martens, Berlin.", False),           # ★ 首字母式按设计不认（同名陷阱）
            ("By Arthur Martens.", False),                # 滑翔机工程师
            ("EDUARD VON MARTENS.", False),               # 动物学家；`von` 是贵族小品词
            ("By F. F. Martens.", False)):                # 物理学家
        _got = ocr_byline_evidence(_s, "Adolf", "Martens") is not None
        print(("  ✓ " if _got == _want else "  ✗ ") + f"{_s:<34} → {_got}")
        if _got != _want:
            bad.append(f"非英文署名前缀：{_s}")

    # ★★★ **`von`／`van` 是姓的一部分，不是地名式后缀**（Liebig 实测）
    #   原来 `Justus von Liebig` 的 surname 取成 `Justus`——**拿他的名去找他的姓**，
    #   30 份 P1 只认出 1 份；改对之后 26 份。
    print("\n══ 小品词：von/van 取姓，of 取名 ══")
    for _n, _first, _sur in (
            ("Justus von Liebig", "Justus", "Liebig"),
            ("Wernher von Braun", "Wernher", "Braun"),
            ("Vincent van Gogh", "Vincent", "Gogh"),
            ("Antonie van Leeuwenhoek", "Antonie", "Leeuwenhoek"),
            # ↓ ★ 反向对照：`of` 是地名式，**必须原样不动**
            ("Galen of Pergamon", "Galen", "Galen"),
            ("Hippocrates of Kos", "Hippocrates", "Hippocrates"),
            # ↓ ★ 不带小品词的老路径不许受影响
            ("Adolf Martens", "Adolf", "Martens"),
            ("Comfort Avery Adams", "Comfort", "Adams")):
        _p = build_patterns(_n)
        _ok = (_p.get("first_word") == _first and _p.get("surname") == _sur)
        print(("  ✓ " if _ok else "  ✗ ")
              + f"{_n:<26} first={_p.get('first_word')!r:<14} surname={_p.get('surname')!r}")
        if not _ok:
            bad.append(f"小品词切分：{_n}")

    # ★★★ **复姓署名**（Roberts-Austen #135 实测）。
    #   正例全部取自他的印本原文，反例是**半截复姓**与**首字母不对**的人。
    #   ★ 关键：放宽的是「名可以写成缩写」，而**复姓两段必须都在**——
    #     姓补上了名让出的识别力。`A. Grant Roberts-Austen` 仍旧挡住。
    print("\n══ 复姓的**行尾署名**（Nature 来信体例 `地点, 日期. 名字.`）══")
    for _s, _want in (
            # ↓ 正例：他印本上的真签名（02-conversations 观察 ③ 引的就是第一条）
            ("Royal Mint, June 9. W. C. Roberts-Austen.", True),
            ("for ready reference. W. C. ROBERTS-AUSTEN.", True),
            ("Illinois Steel Company. W. C. Roberts-Austen.", True),
            ("imperfectly mounted. W. C. RobErts-Austen.", True),
            # ↓ ★★★ 版口不是签名——就是这一份把 10 打成了 9
            ("148 Mr. F. Osmond and Prof. W. C. Roberts- A listen.", False),
            ("57 W. C. ROBERTS-AUSTEN.", False),
            # ↓ ★ 别人的签名一个都不许认成他
            ("and so it was. Reginald Roberts.", False),
            ("and so it was. W. Roberts.", False),
            ("and so it was. F. Osmond.", False),
            ("and so it was. Charles Austen.", False),
            ("Royal Mint, June 9. A. Grant Roberts-Austen.", False)):
        _got = ocr_byline_evidence(_s, "William", "Roberts-Austen") is not None
        print(("  ✓ " if _got == _want else "  ✗ ") + f"{_s:<52} → {_got}")
        if _got != _want:
            bad.append(f"复姓行尾署名：{_s}")

    print("\n══ 复姓署名：名可缩写，但两段都要在 ══")
    for _s, _want in (
            # ↓ 正例：印本原文（`EOBERTS`/`ROBEKTS` 是 OCR 讹字，`Pbofessob` 是敬称被打坏）
            ("By W. C. Roberts-Austen, C.B., F.R.S.", True),
            ("By Professor W. C. EOBERTS-AUSTEN, C.B., F.R.S.", True),
            ("By Pbofessob W. C. ROBERTS-AUSTEN, C.B., F.R.S.", True),
            ("By Sir Williaji C. EOBERTS-AUSTEN, K.C.B., D.C.L.", True),
            ("By W. Chandler Koberts- Austen, F.RS", True),
            # ★★★ **已知的漏，故意留着**：`^V.` 是 `W.` 被 OCR 打坏。
            #   名只剩一个字母时**没有容错余地**——单字母容 1 个编辑距离
            #   就等于「任何字母都算」，那条路一开，复姓这条的全部约束就废了。
            #   **认不出来就认不出来，不许为了多救一份把判据变成摆设。**
            #   （实测代价：imeche1893 那一份走不通这条路。）
            ("By  Professor  ^V.  C.  ROBEKTS-AUSTEN,  C.B.", False),
            # ↓ ★★★ 反例：**半截复姓一个都不许进**——名让出识别力之后全靠姓补
            ("By W. Roberts, F.R.S.", False),
            ("By W. C. Austen, F.R.S.", False),
            ("By William Roberts, F.R.S.", False),      # 真人：内科医生 F.R.S.，1830-1899
            ("By Sir William Roberts, M.D.", False),
            ("By Charles Austen, F.R.S.", False),
            ("By Reginald Roberts.", False),
            # ↓ ★ Fleming 那一类的陷阱形态：首字母不对，照样挡住
            ("By A. Grant Roberts-Austen.", False),
            # ↓ ★ 顺序反了不算——`Austen-Roberts` 是另一个人
            ("By W. C. Austen-Roberts, F.R.S.", False),
            # ↓ ★★★ **我们自己写进文件的头**，不是语料（复姓那条路一开就漏了它）
            ("# TITLE: W. C. ROBERTS-AUSTEN PAPERS", False),
            ("# title: W. C. Roberts-Austen Papers, 1876-1902", False),
            # ↓ ★★★ **馆藏名不是署名**——形态与题页署名一模一样
            ("W. C. ROBERTS-AUSTEN PAPERS AND CORRESPONDENCE", False),
            ("W. C. ROBERTS-AUSTEN COLLECTION, ROYAL MINT ARCHIVES", False),
            # ↓ ★ 反向对照：`By` 打头是明示署名，**不许被馆藏词误伤**
            ("By W. C. Roberts-Austen. Papers read before the Society.", True)):
        _got = ocr_byline_evidence(_s, "William", "Roberts-Austen") is not None
        print(("  ✓ " if _got == _want else "  ✗ ") + f"{_s:<50} → {_got}")
        if _got != _want:
            bad.append(f"复姓署名：{_s}")

    # ★★ **单姓人物一律不许受影响**——复姓那条路只对复姓开。
    #   （Fleming 的 `A. Grant Fleming` 防线是本文件最老的一条，不许被顺手拆掉。）
    print("\n══ 单姓不受复姓那条路影响 ══")
    for _who, _first, _last, _s, _want in (
            ("Fleming", "Alexander", "Fleming", "By A. Fleming, F.R.C.S.", False),
            ("Fleming", "Alexander", "Fleming", "By A. Grant Fleming.", False),
            ("Fleming", "Alexander", "Fleming", "By Alexandbb Fleming, F.R.C.S.", True),
            ("Martens", "Adolf", "Martens", "Von A. Martens, Berlin.", False),
            ("Martens", "Adolf", "Martens", "Von Adolf Martens.", True)):
        _got = ocr_byline_evidence(_s, _first, _last) is not None
        print(("  ✓ " if _got == _want else "  ✗ ") + f"{_who:<9}{_s:<36} → {_got}")
        if _got != _want:
            bad.append(f"单姓射程：{_s}")

    # ★★★ 护栏射程：**`ocr_byline_evidence` 那条路也必须被同名护栏管住**
    #   v0.0.0.136 只把护栏加在 `standalone_ocr` 上，而那条路跑在它前面、
    #   返回同一个码——护栏形同虚设。**这四条走的是 `check_text` 全链，不是单个函数。**
    print("\n══ 同名护栏的射程 四条对照（v0.0.0.137，走全链）══")
    for _lbl, _who, _ns, _mid, _s, _want in (
            ("**ELIHU THOMPSON.**（v0.0.0.136 从这条路漏过去了）",
             "Elihu Thomson", ("Thompson",), "", _tail("ELIHU THOMPSON."), False),
            ("Elihtt Thomson.（本人，OCR 讹字，不许误伤）",
             "Elihu Thomson", ("Thompson",), "", _tail("Elihtt Thomson."), True),
            ("**CHARLES A. COFFIN, OF BOSTON**（GE 总裁）",
             "Charles L. Coffin", ("Charles A. Coffin",), "l",
             _tail("CHARLES A. COFFIN, OF BOSTON, MASSACHUSETTS."), False),
            ("CHARLES L. OOFFIN, OF DETROIT（本人）",
             "Charles L. Coffin", ("Charles A. Coffin",), "l",
             _tail("CHARLES L. OOFFIN, OF DETROIT, MICHIGAN."), True)):
        _p = build_patterns(_who)
        _p["namesakes"] = _ns
        _p["own_mid"] = _mid
        _got = check_text(_s, _p)[0]
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"护栏射程：{_lbl}")

    # ★★★ 形态 D：专利题页署名（Coffin #130 —— A/B/C 三形态一个都认不出它）
    print("\n══ 专利题页署名 七条对照（v0.0.0.137）══")
    for _lbl, _s, _want in (
            ("CHARLES L. COFFIN, OF DETROIT, MICHIGAN.（本人）",
             _tail("CHARLES L. COFFIN, OF DETROIT, MICHIGAN."), True),
            ("同上但姓被 OCR 打坏（OOFFIN）",
             _tail("CHARLES L. OOFFIN, OF DETROIT, MICHIGAN."), True),
            ("OF→OE 讹字 ＋ ASSIGNOR 子句",
             _tail("CHARLES L. COFFIN, OE DETROIT, MICHIGAN, ASSIGNOR OF ONE-HALF TO GEORGE H. LOTHROP."), True),
            ("C. L. COFFIN, OF DETROIT, MICH.（纯缩写题页）",
             _tail("C. L. COFFIN, OF DETROIT, MICH."), True),
            ("**CHARLES A. COFFIN, OF BOSTON**（GE 总裁，不是他）",
             _tail("CHARLES A. COFFIN, OF BOSTON, MASSACHUSETTS."), False),
            ("**C. A. COFFIN, OF LYNN**（同上，缩写）",
             _tail("C. A. COFFIN, OF LYNN, MASSACHUSETTS."), False),
            ("正文里的逗号不许混进来",
             _tail("and the process described by Coffin, and others in the art."), False)):
        _got = bool(standalone_ocr(_s, "charles", "coffin", ("Charles A. Coffin",), "l"))
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应认出' if _want else '应拒绝'}　{_lbl}")
        if not _ok:
            bad.append(f"专利题页：{_lbl}")

    # ★ 没声明中名首字母时，射程必须与 v0.0.0.136 完全一致（缩写一律不认）
    _got = bool(standalone_ocr(_tail("C. L. Coffin."), "charles", "coffin", _NSC, ""))
    print(f"  {'✓' if not _got else '✗'} 应拒绝　C. L. Coffin.（**没声明中名时，缩写仍旧不认**）")
    if _got:
        bad.append("同姓中名护栏：没声明中名时不该放行缩写")

    print("\n══ ★★★★ A-byline-coauthor：他站在第二作者位（Rosenhain #138 实测）══")
    import tempfile as _tf2, os as _os2
    _pc = build_patterns("Walter Rosenhain"); _pc["namesakes"] = (); _pc["own_mid"] = ""
    _CO = [
      ("\nBy J. A. EwiNG, F.R.S., Professor of Mechanism and Applied Mechanics in the "
       "University of Cambridge, and Walter Rosenhain, B.A., St, John's College.\n",
       True, "第二作者位、名字拼写正确——**旧版整份判无据**"),
      ("\nBy Sir Alexander Fleming and Walter Rosenhain.\n", True, "敬称 + and"),
      # ★★★★ 用例必须和原文一样脏：第一版全写成一行，于是自测全绿而实际全漏
      ("\nBy J. A. EwiNG, F.R.S.,\nProfessor of Mechanism and Applied Mechanics\n"
       "in the University of Cambridge,\nand Walter Rosenhain, B.A.\n",
       True, "★★★★ **折行**题头——第一版 `[^\\n]` 匹配不到，而真实印本全是折行的"),
      ("\nBy A. Smith.\n\nand Walter Rosenhain wrote separately.\n",
       False, "★★ 跨**空行**不许连——空行是段落边界"),
      ("\nBy A. Smith, as reported by Walter Rosenhain in a later note.\n",
       False, "★ `reported by`：转述者不是作者"),
      ("\nBy J. E. Stead, edited by Walter Rosenhain.\n", False, "★ `edited by`：编者不是作者"),
      ("\nBy Professor Ewing and the present author have described phenomena.\n",
       False, "★ 没点他的名"),
      ("\nBy J. E. Stead, and his somewhat slavish adherence to equilibrium curves did not "
       "appeal to the authors, since as practical men their faith in such curves fell far "
       "short of that of Dr. Rosenhain, who was not present.\n",
       False, "★★ 超 240 字符：正文提到他，不是署名"),
      ("\nBy J. A. Ewing, W. Rosenhain, and C. Smith.\n", False,
       "★★★ 逗号列举里的名字**不由 and 引出**——故意不认，宁可漏不可冤"),
      ("\nBy James A. Ewing, F.E.S., and Walter EoSENHAiN, 1851 Exhibition Scholar.\n",
       False,
       "★★★★ **已知限制**：OCR 讹形 + 第二作者位两条同时放宽，风险成倍涨；"
       "本条只认精确名，那一份留给 attribution_basis 逐份声明"),
    ]
    for _txt, _should, _why in _CO:
        with _tf2.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as _f:
            _f.write(_txt); _fp = _f.name
        _ok, _code, _, _ = check(pathlib.Path(_fp), _pc); _os2.unlink(_fp)
        print(f"  {'✓' if _ok == _should else '✗'} {_why}")
        if _ok != _should:
            bad.append(f"A-byline-coauthor：{_why}（得到 ok={_ok} code={_code}）")

    print("\n══ ★★★★ **真实样本**：Rosenhain #138 四份取不到署名的印本题头（逐字）══")
    # 这四段**逐字取自 `_corpora/wip-rosenhain-138/.../raw/` 下的语料文件**，不是构造的。
    # 它们把「本判据现在取不到什么」冻在这里：**日后谁放宽 OCR 容错，这四条会立刻变绿**，
    # 那时必须同时回答「会不会把别人的东西收进来」。
    # ★ 现在四条**都应判「取不到」**——这不是缺陷，是有意的射程边界：
    #   位置放宽（第二作者位）+ 拼写放宽（OCR 讹形）两条叠加，冤枉的风险成倍涨。
    _pr = build_patterns("Walter Rosenhain"); _pr["namesakes"] = (); _pr["own_mid"] = ""
    _REAL = [
        (" and Apijlieel Meeha/mcs in tin. University of Cambridge, and Walter Kosenhaik, "
         "St John's College, Ccmv bridge, 1851 Exhibitio7i Research Scholar",
         "1899 Bakerian Lecture：第二作者位 + `Rosenhain`→`Kosenhaik`"),
        ("train. Pre- liminary Notice/' By James A. Ewing, F.E.S., and Walter EoSENHAiN, "
         "1851 Exhibition Eesearch Scholar, Melbourne.",
         "1899 Micro-metallurgy：第二作者位 + `Rosenhain`→`EoSENHAiN`"),
        ("252 Mr. W. Eosenhain. [May 1, The authors hope that these experiments may prove",
         "1902 Platinum：版口式 + `Rosenhain`→`Eosenhain`"),
        (" on Slip-Bands in Metallic Fractures. — Preliminary Note.\" By Walter EosENiiAiisr, "
         "B.A., B.C.E. Communicated by Professor Ewing, F.R.S.",
         "1904 Slip-Bands：`Rosenhain`→`EosENiiAiisr`，坏了四处以上"),
    ]
    import tempfile as _tf3, os as _os3
    for _txt, _why in _REAL:
        with _tf3.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as _f:
            _f.write(_txt); _fp = _f.name
        _ok, _code, _, _ = check(pathlib.Path(_fp), _pr); _os3.unlink(_fp)
        print(f"  {'✓' if not _ok else '✗'} 仍取不到（**有意的射程边界**）：{_why}")
        if _ok:
            bad.append(f"真实样本：{_why} **本该取不到，却取到了 {_code}**"
                       "——放宽了容错就要回答「会不会把别人的东西收进来」")

    # ★★ 与之成对：**同一批语料里取得到的那几种**，也用逐字原文钉住，
    #   否则上面四条会诱使人「干脆全放宽」。
    _REAL_OK = [
        # ★★★ **连换行一起逐字取**。第一版我把它拼成了一行，自测当场变红——
        #   判据要求署名是**结构元素**（行首或分隔符之后），而真实印本是跨行的。
        #   **夹具比原文干净，就等于没测**（同日在 `A-byline-coauthor` 的 `_LN` 上刚栽过一次）。
        ("alline StritcfMre of Metals, (Second Paper.) \n\nBy J. A. EwiNG, F.R.S., Professor "
         "of Mechanism and Applied Mechanics in the \nUniversity of Cambridge, and Walter "
         "Rosenhain, B.A., St, John's College, \nCambridge^ 1851 Exhibition Research Scholar, "
         "University of Melbourne. \n",
         "1900 Second Paper：第二作者位、**名字一个字母都没错**、**跨三行** → A-byline-coauthor"),
    ]
    for _txt, _why in _REAL_OK:
        with _tf3.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as _f:
            _f.write(_txt); _fp = _f.name
        _ok, _code, _, _ = check(pathlib.Path(_fp), _pr); _os3.unlink(_fp)
        print(f"  {'✓' if _ok else '✗'} 取得到：{_why}（得到 {_code or '—'}）")
        if not _ok:
            bad.append(f"真实样本：{_why} **本该取到，却没取到**")

    # ══ ★★★★ **真实样本**：Whitworth #152——OCR 把姓拆成两段（2026-08-07）══
    #   1858 年 NYPL 扫描本的标题页逐字就是 `JOSEPH  WHIT  WORTH,  F.R.S.`（**双空格**），
    #   整卷 335 KB 因此被判「无据」。Oxford 扫描本同一版是 `JOSEPH WHITWORTH, F.R.S.`。
    #   ★ 落这条容错前**全库量过**：25 个工作区里「无署名的一手件」中姓被拆开的 14 份，
    #     而**逐条读命中，真的是署名的只有 4 处**（Blackwell ×2、Bessemer ×1、Whitworth ×1），
    #     其余是正文断词（`Bes semer converting-vessels`）、版口（`PROFESSOR ROBERTS -AUSTEN`）、
    #     第三人称提及（`Professor Vir chow's`）、索引条目（`Mart ens, elektrische`）。
    #     **所以容错只放进 `name_rx`（署名路径），`surname_rx` 一个字没动。**
    #   ★★ 第一版只容忍**一个**空白，自测里我编的单空格样本过而**真扫描件一份都不中**——
    #     同日第三次「合成假设比真实的干净」。现在是 `{1,3}`。
    print("\n══ ★★★★ **真实样本**：Whitworth #152 姓被 OCR 拆开（双空格，逐字）══")
    _pw = build_patterns("Joseph Whitworth")
    _pw["namesakes"] = ("Whitworth Porter", "William Allen Whitworth", "Robert Whitworth",
                        "Charles Whitworth", "Robert Percy Whitworth",
                        "George Frederick Whitworth")
    _pw["own_mid"] = ""
    _WQ = [
        ('MISCELLANEOUS  PAPERS \n\n\nov \n\n\nMECHANICAL   SUBJECTS \n\n\nBY \n\n\n'
         'JOSEPH  WHIT  WORTH,  F.R.S. \n\n\nLONDON: \n', True,
         "1858 NYPL 扫描题页：**姓被拆成 `WHIT  WORTH`、双空格**"),
        ('MISCELLANEOUS PAPERS \n\n\n\nov \n\n\n\nMECHANICAL SUBJECTS \n\n\n\nBY \n\n\n\n'
         'JOSEPH WHITWORTH, F.R.S. \n\n\n\nLONDON: \n', True,
         "1858 Oxford 扫描题页：正常拼写（**回归对照，放宽不许影响它**）"),
        ("\n\n\nHISTORY OF THE CORPS OF ROYAL ENGINEERS. BY WHITWORTH PORTER.\n\n\n", False,
         "★★ `Whitworth` 是他的**名**、姓是 Porter"),
        ("\n\n\nBY WHIT  WORTH PORTER.\n\n\n", False,
         "★★ 同上且姓被拆开——**放宽后仍必须拒**"),
        ("\n\n\nCHOICE AND CHANCE. BY WILLIAM ALLEN WHIT  WORTH, M.A.\n\n\n", False,
         "★ 数学家 W. A. Whitworth，姓被拆开"),
        ("\n\n\nObservations by Robert Whit  worth, Esq; engineer\n\n\n", False,
         "★ 运河工程师 Robert Whitworth（卒 1799），姓被拆开"),
        ("\n\n\nthe Whit worth measuring machine was described by others\n\n\n", False,
         "★ **正文断词提及**，不是署名"),
    ]
    for _s, _want, _why in _WQ:
        _got = check_text(_s, _pw)[0]
        _ok = _got == _want
        print(f"  {'✓' if _ok else '✗'} {'应取到' if _want else '应拒绝'}　{_why}")
        if not _ok:
            bad.append(f"Whitworth 拆姓：{_why}")

    # ── ★★★★ 头衔判别（Nasmyth #153 撞出来，**在抓源落地之前**）──
    #   `_blocked` 只比姓、`_initial_blocked` 只比中名首字母，两者都不管头衔。
    #   而 Nasmyth 有**两位与他同名同姓的准男爵**，实测（本判别器加之前）：
    #       By Alexander Nasmyth（父，画家）  → 拒绝 ✓
    #       By Patrick / Peter Nasmyth（兄）  → 拒绝 ✓
    #       **By Sir James Nasmyth, Baronet   → 放行 ✗**
    #   ★ 因此更正一句我自己写过的话：「护栏只比姓，对这个人物几乎等于不设防」——
    #     **实测证伪**，画家家族那一串它全挡住了，漏的只有同名同姓那一路。
    #   ★★ 判别器第一次接在了 `A-byline-standalone` 与 `standalone_ocr` 上，
    #     而这条署名走的是 `A-byline`，**加完仍然放行**——接在了没人走的分支上。
    _NSN = ("Alexander Nasmyth", "Patrick Nasmyth",
            "Sir James Nasmyth, 1st Baronet", "Sir James Nasmyth, 2nd Baronet")

    def _title_case(_name, _text, _ns, _ot, _want, _why):
        _p = build_patterns(_name)
        _p["namesakes"] = _ns; _p["own_mid"] = ""; _p["own_titles"] = _ot
        _g = bool(check_text(_text, _p)[0])
        print(f"  {'✓' if _g == _want else '✗'} {'应取到' if _want else '应拒绝'}　{_why}")
        if _g != _want:
            bad.append(f"头衔判别：{_why}")

    print("\n★★★★ 头衔判别（证据驱动，不是见 Sir 就拦）")
    _title_case("James Nasmyth", "By Sir James Nasmyth, Baronet\n\nOn botany.",
                _NSN, (), False, "By Sir James Nasmyth, Baronet —— **同名同姓的准男爵**")
    _title_case("James Nasmyth", "By James Nasmyth\n\nOn the slide principle.",
                _NSN, (), True, "By James Nasmyth —— 本人")
    _title_case("James Nasmyth", "By Sir James Nasmyth, Baronet\n\nOn botany.",
                _NSN, None, True, "同一条署名而 own_titles=None —— **没声明就不许拦**（不判 ≠ 通过）")
    # ★★★★ 这一条是全组最要紧的：**Whitworth 本人 1869 年受封准男爵**。
    #   一律拦 `Sir` 会把他自己的署名挡在门外——Coffin 那次「两个方向同时错」的重演。
    _title_case("Joseph Whitworth", "By Sir Joseph Whitworth, Bart.\n\nOn the true plane.",
                ("Charles Whitworth",), ("sir", "baronet"), True,
                "By Sir Joseph Whitworth, Bart. —— **他自己就是准男爵，不许拦**")
    _title_case("James Nasmyth", "By Rev. James Nasmyth\n\nA sermon.",
                _NSN, (), True, "By Rev. James Nasmyth —— 没有已声明同名者持此衔，不拦")
    _title_case("James Nasmyth", "By Alexander Nasmyth\n\nA view of Edinburgh.",
                _NSN, (), False, "By Alexander Nasmyth（父）—— 新判别器不许把它改坏")
    _title_case("James Nasmyth", "By Patrick Nasmyth\n\nA wooded landscape.",
                _NSN, (), False, "By Patrick Nasmyth（兄）—— 新判别器不许把它改坏")

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
    ap.add_argument("--namesake", action="append", default=[],
                    help="**已知同名的姓氏**（可给多次）。OCR 容错不许把两个真名连起来："
                         "候选姓与任一已声明同名的距离 ≤ 与目标姓的距离时一律拒绝。"
                         "★ Thomson 与 Thompson 距离仅 1——不声明就会把十二个 Thompson 收进来。"
                         "★★ 也可以给**全名**（如 \"Charles A. Coffin\"）——同姓的同名者"
                         "只能靠中名首字母区分，那时必须同时给 --middle-initial。")
    ap.add_argument("--own-title", action="append", default=[],
                    help="**目标本人持有的头衔**（可给多次，如 Sir / Bart）。"
                         "★ 与 `--declares-no-title` 二选一：两者都不给时**头衔判别不启用**，"
                         "并印「未核（不是通过）」——`None`（没声明）与 `()`（声明他没有）必须分得开。")
    ap.add_argument("--declares-no-title", action="store_true",
                    help="**明确声明目标本人不持有任何头衔**，从而启用头衔判别。"
                         "★ 实测（Nasmyth #153，本判别器加之前）："
                         "`By Sir James Nasmyth, Baronet`（两位同名同姓的准男爵之一）**被放行**；"
                         "而 `By Alexander Nasmyth`（父，画家）与 `By Patrick/Peter Nasmyth`（兄）"
                         "本来就挡得住。**漏的只有同名同姓那一路。**"
                         "★★ 为什么不是见 Sir 就拦：**Whitworth 本人 1869 年受封准男爵**，"
                         "语料里就有 `Sir Joseph Whitworth, Bart.`——"
                         "一律拦会把他自己的署名挡在门外（Coffin 那次「两个方向同时错」的重演）。")
    ap.add_argument("--middle-initial", default="",
                    help="**目标本人的中名首字母**（如 Charles L. Coffin 给 \"L\"）。"
                         "只在有**同姓**同名者时需要：`_blocked` 只比姓，同姓的它一个也挡不住。"
                         "★ 实测（Coffin #130，护栏加之前）：`Charles A. Coffin.`（GE 首任总裁）"
                         "被当成他的署名放行，而他惯用的 `C. L. Coffin.` 反而被拦——两个方向同时错。"
                         "**不给就退回不认缩写署名的老射程。**")
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
        # ★ 已知同名注入：OCR 容错不许把两个真名连起来（见 standalone_ocr 文件头）
        pat["namesakes"] = normalize_namesakes(a.namesake)
        pat["own_mid"] = str(a.middle_initial or "").strip().lower()[:1]
        # ★ `None` = 没声明 → 头衔判别**不启用**；`()` = 明确声明「他没有头衔」。
        #   两者必须分得开：[[empty-default-swallows-unknown]]
        pat["own_titles"] = (tuple(t.strip().lower() for t in (a.own_title or ()))
                             if (a.own_title or a.declares_no_title) else None)
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
