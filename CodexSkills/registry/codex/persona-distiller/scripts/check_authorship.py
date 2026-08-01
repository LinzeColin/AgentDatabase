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

- `A-byline`   —— 显式署名：`By <人物名>`
- `A-editorial`—— 编者注：`[Remarks delivered by <人物名> ...]`
- `A-turns`    —— 真·逐字稿：≥2 个说话人标签各出现 ≥3 次，
                  **且同一标签后面跟的文字每次都不同**
                  （否则那是标题里的冒号——`<人物名>: 某某标题`
                   在导航/og:title/h1 里重复出现，旧判据把它当成了说话人标记）

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
    if len(tokens) < 2:
        raise ValueError(f"人物名至少要有名与姓两段：{full_name!r}")
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
        "BYLINE": re.compile(rf"\bBy\s+{name_rx}\b", re.I),
        "EDITORIAL": re.compile(
            rf"[\[\(][^\])]{{0,40}}\b(?:remarks|speech|address|excerpt|written|delivered|adapted)"
            rf"[^\])]{{0,40}}\bby\s+{name_rx}", re.I),
        "MINE": re.compile(
            rf"{surname_rx}|^(?:{'|'.join(re.escape(i) for i in sorted(initials))})$", re.I),
        "SURNAME": re.compile(surname_rx, re.I),
    }


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
SELFTEST_NEGATIVE = [
    ("他人署名的随笔", "By Richard Roe\n\nJane Public once told me the ratio matters.\n"
                       "Richard Roe is Chairman of the Example Foundation.\n"),
    ("散文里的 by X", "The autobiography by Jane Q. Public who rose from nothing is reviewed here.\n"),
    ("标题里的冒号", "Jane Public: Background & bio\nJane Public: Investment philosophy\n"
                     "Jane Public: Philanthropy\nJane Public: Background & bio\n"),
    ("完全没提到她", "This quarterly essay is about communal institutions and their funding.\n" * 5),
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
    print(f"\n负对照通过（{len(SELFTEST_POSITIVE) + len(SELFTEST_MASTHEAD_POSITIVE)} 正 + "
          f"{len(SELFTEST_NEGATIVE) + len(SELFTEST_MASTHEAD_NEGATIVE) + 1} 反）")
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
