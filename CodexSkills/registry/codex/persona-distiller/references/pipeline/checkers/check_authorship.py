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

- `A-byline`   —— 显式署名：`By Michael H. Steinhardt`
- `A-editorial`—— 编者注：`[Remarks delivered by Michael Steinhardt ...]`
- `A-turns`    —— 真·逐字稿：≥2 个说话人标签各出现 ≥3 次，
                  **且同一标签后面跟的文字每次都不同**
                  （否则那是标题里的冒号——`Michael Steinhardt: 某某标题`
                   在导航/og:title/h1 里重复出现，旧判据把它当成了说话人标记）

再做一次**反向检查**：文末若出现**别人**的身份署名
（`X is Chair of…` / `X is Managing Director of…` / `By <他人名>`），
一律降级并打印那一行。刊物型 PDF 的作者署名就在文末那一行。

退出码：0 = 全部有据；2 = 有文件缺正面证据（列出）。
"""
import argparse
import pathlib
import re
import sys

NAME = r"Michael\s+(?:H\.?\s+)?Steinhardt"

BYLINE = re.compile(rf"\bBy\s+{NAME}\b", re.I)
EDITORIAL = re.compile(
    rf"[\[\(][^\])]{{0,40}}\b(?:remarks|speech|address|excerpt|written|delivered|adapted)"
    rf"[^\])]{{0,40}}\bby\s+{NAME}", re.I)
# 说话人标签：行首「名字:」。**必须多次出现且后文每次不同**才算逐字稿。
# ★ 名字部分不能写成含空格的字符类再跟 `[ \t]*`——两者可以互相吞空格，
#   在十几万字的检方文书上会灾难性回溯直接卡死。改成「词(空格词){0,3}」的无歧义形式。
# ★ 冒号后的正文**可能在下一行、且中间隔着空行**——Charlie Rose 与
#   Knowledge@Wharton 的逐字稿是「说话人标记独占一行 + 空行 + 正文」。
#   只认同行会把 67 轮的真逐字稿判成 0 轮，只允许一个 \n 也还是 0 轮。
# ★ 标签第二个词起允许小写连接词——Knowledge@Wharton 的主持人标签就是
#   `Knowledge at Wharton:`，要求每词首字母大写会把它整条丢掉，
#   于是只剩 `Steinhardt` 一个标签，「≥2 个说话人」的判据就假阴性了。
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


def turns_evidence(text: str):
    """真逐字稿：≥2 个标签各 ≥3 轮，且同一标签后文互不相同。"""
    seen: dict[str, set] = {}
    for rx in (TURN, TURN_CAPS):
        for label, rest in rx.findall(text):
            seen.setdefault(label.strip().lower(), set()).add(rest.strip()[:60])
    good = {k: v for k, v in seen.items() if len(v) >= 3}
    mine = [k for k in good if re.search(r"steinhardt|^ms$", k, re.I)]
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


def check(path: pathlib.Path):
    """返回 (ok, 证据码, 证据原文, 反证列表)。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    counter = []

    for m in OTHER_ROLE.finditer(text):
        who = m.group(1)
        if re.search(r"steinhardt", who, re.I):
            continue
        counter.append(m.group(0).strip())
    for rx in (OTHER_BY, OTHER_BY_CAPS):
        for m in rx.finditer(text):
            if not re.search(r"steinhardt", m.group(1), re.I):
                counter.append(m.group(0).strip())

    for code, rx in (("A-byline", BYLINE), ("A-editorial", EDITORIAL)):
        for m in rx.finditer(text):
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

    ev = turns_evidence(text)
    if ev:
        # ★ 轮次型证据不受他人署名影响，反证清空。
        #   访谈/逐字稿里出现**提问者**的署名是应有之义
        #   （CONTACT 2000 春季刊的问答就署 `by ELI VALLEY`），
        #   而他的话是**逐轮标注**的，归属不靠整篇署名建立。
        #   署名型证据（随笔）则相反：文中出现别人的署名就说明切歪了。
        return True, "A-turns", ev, []

    return False, "", "", counter


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("corpus", help="语料目录")
    ap.add_argument("--claim-p1", nargs="*", default=None,
                    help="声称是 P1 的文件名；省略则检查目录里全部 .txt")
    a = ap.parse_args()

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
    print(f"检查 {len(files)} 份是否够格当「他的话」（P1）\n")
    for f in files:
        p = d / f
        if not p.exists():
            print(f"  ✗ {f}: 文件不存在")
            bad.append(f)
            continue
        ok, code, ev, counter = check(p)
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
