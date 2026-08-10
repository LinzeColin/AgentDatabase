#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从**语料文件自己的题名页**读出**版次声明**。

★★★★ 原本还想读出书目题名，**实测做不出来，已砍掉**——见下面「砍掉的那一半」。

## 为什么需要它

全库 **1,943 / 1,969 行（99%）** 的 `title` 就是 `local_path` 的文件名。
后果不是难看：判「两份是不是同一部作品」时**除了内容重叠没有第二个证据源**——
全库剩下的 **931 对未声明重复源清不掉，根子就在这**。

## ★★★★ 唯一合法的来源是题名页，**不是文件名**

从文件名推题名，等于把「关于文件的断言」当成文件本身
（[[filename-matching-is-brittle]] 一天栽过三次）。
本件只读**文件正文的开头**（剥掉抓源方的出处表头之后），
把题名页上印着的东西抄出来。

Osler 的《Principles and Practice of Medicine》14 份实测：
**11 份读得到版次声明**，且与文件名对得上——

```
ppm-ed2-1895-pentland      SECOND EDITION, THOROUGHLY REVISED
ppm-ed7-1909               SEVENTH EDITION, THOROUGHLY REVISED
ppm-ed8-1912               EIGHTH EDITION— LARGELY RE-WRITTEN
ppm-ed2-yr-illegible       SECOND EDITION           ← 文件名说读不到年，题名页说了版次
ppm-ed6-yr-illegible       SIXTH EDITION, THOROUGHLY REVISED
```

## ★★★★ 砍掉的那一半：**题名提取，2/9 命中，不能用**

原设计是「题名页上第一个连续 4 个以上全大写词的块＝题名」。
Osler 的 PPM 14 份 dry-run，**9 条提议逐条读完，只有 2 条对**：

| | 提议 | 实际是什么 |
|---|---|---|
| ✓ ppm-ed3-1898 | The Principles And Practice | 对 |
| ✓ ppm-ed5-1902 | The Principles And Practice | 对 |
| ✗ ppm-ed4-1901 | The Intoxications And Sun-Stroke | **目录条目** |
| ✗ ppm-ed6-1905 | The Intoxications And Sun-Stroke | 目录条目 |
| ✗ ppm-ed7-1909 | Appleton And Company Feinted | **出版者行 ＋ OCR 噪声** |
| ✗ ppm-ed1-1892-pentland | Medical Center Stanford, Cauf | **图书馆藏章** |
| ✗ ppm-ed6-yr-illegible | William Arthur Johnson, Psibbt | **献词页** |
| ✗ ppm-ed8-1919 | Specific Infectious Diseases Page | 目录条目 |
| ✗ ppm-ed9-1921 | William Arthur Johnson Priest | 献词页 |

根因：**题名页不可靠地是「第一个全大写块」**——扫描件开头常是藏章、
Google 声明、献词、目录，而 `NOT_TITLE` 那张黑名单永远补不完。
**砍掉。** 数字留在这里，**别让下一个人再建一遍**
（与 `check_translation_witness` 砍掉自动认译本那一半同型）。

## 三条它做不到的事（**先说清楚**）

1. **一版书通常不印「FIRST EDITION」** —— Osler 的两份 ed1 都读不到版次声明。
   **读不到不等于不是一版**，本件报「读不到」，不猜。
2. **正文里的「first edition」不是版次声明。** 第一版正则命中了序言里的
   `first edition was used as my text-book`——**那是散文**。
   现已要求：版次声明必须**全大写**，且**不在句子中间**。
3. **本件只提议，不落库。** 给 `--apply` 才写，且写之前必须
   `--dry-run` 读一遍——题名页 OCR 会烂，抄错比不抄更坏。

退出码：0 = 有提议或无事可做；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

HEAD_CHARS = 9000

#: 版次声明：**必须全大写**（题名页的排法），且前后不是小写字母。
#:   ★ 不加这条，序言里的 `first edition was used as my text-book` 会被当成版次声明。
EDITION = re.compile(
    r"(?<![A-Za-z])((?:FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|"
    r"ELEVENTH|TWELFTH)[ \-]?EDITION)(?![a-z])")
#: 题名：题名页上连续 4 个以上全大写词（允许中间有 OF/AND/THE 这类小词）。
TITLE = re.compile(r"((?:\b[A-Z][A-Z'\-]{2,}\b[ ,]+){3,}\b[A-Z][A-Z'\-]{2,}\b)")
YEAR = re.compile(r"\b(1[5-9]\d\d|20[0-2]\d)\b")

#: 不是题名的全大写块——图书馆藏章、扫描声明、版权样板。
NOT_TITLE = re.compile(
    r"(LIBRARY|UNIVERSITY|COLLEGE|SOCIETY|INSTITUTE|HOSPITAL|MUSEUM|ARCHIVE|"
    r"DIGITIZED|GOOGLE|INTERNET|COPYRIGHT|ALL RIGHTS|PRESENTED|REFERENCE|BINDERS|"
    r"NOT FOR CIRCULATION|HONORARY|DISCOVERABLE|SCANNED|PUBLIC DOMAIN|"
    r"PRESERVED FOR GENERATIONS|BOOKSHELVES|LIBRARY SHELVES)", re.I)


def propose(text: str) -> dict:
    """→ {版次, 题名页附近出现的年}。读不到的一律 None，**不猜**。

    ★★★★ **不再返回题名**——那一半实测 2/9，已砍（见文件头）。
    `_title_candidate()` 留着只为自测能证明「它确实会把藏章/献词认成题名」，
    **生产路径一个字都不用它**。
    """
    head = re.sub(r"\s+", " ", corpus_body(text)[:HEAD_CHARS])
    ed = EDITION.search(head)
    years = sorted(set(YEAR.findall(head)))
    return {"版次": ed.group(1) if ed else None, "题名页附近出现的年": years[:8]}


def _title_candidate(head: str):
    """**已砍的那一半**，只在自测里用，用来证明它为什么不能用。"""
    for m in TITLE.finditer(head):
        cand = m.group(1).strip(" ,")
        #: ★★★ 要看**窗口**，不是只看候选串。
        #:   反向对照抓到过：Google 扫描声明里的
        #:   `MAKE THE WORLDS BOOKS DISCOVERABLE ONLINE` 全大写、够长、
        #:   候选串里没有 `GOOGLE` 这个词——**那个词在句子更前面**。
        window = head[max(0, m.start() - 120):m.end() + 120]
        if NOT_TITLE.search(window) or len(cand) < 14:
            continue
        return cand
    return None


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：题名页读得出版次 ──")
    a = propose("THE PRINCIPLES AND PRACTICE OF MEDICINE BY WILLIAM OSLER "
                "SEVENTH EDITION, THOROUGHLY REVISED NEW YORK D. APPLETON AND COMPANY 1909")
    chk(f"版次读到（{a['版次']}）", a["版次"] == "SEVENTH EDITION")
    chk(f"年读到 {a['题名页附近出现的年']}", "1909" in a["题名页附近出现的年"])
    chk("**不再返回题名**（那一半已砍）", "题名" not in a)

    print("── ★★★ 反向对照 ①：序言里的小写 `first edition` **不是版次声明** ──")
    b = propose("In the preparation of this volume the first edition was used as my "
                "text-book throughout the winter session.")
    chk(f"不报版次（实报 {b['版次']}）", b["版次"] is None)

    print("── ★ 反向对照 ②：`EDITIONS` 复数不许命中 ──")
    f = propose("PREVIOUS EDITIONS WERE ISSUED IN LONDON")
    chk(f"不报版次（实报 {f['版次']}）", f["版次"] is None)

    print("── 反向对照 ③：什么都读不到时是 None，**不许编** ──")
    e = propose("sia a God we STE ey Fe a neia ns Bat tA a Salepte OT er ti Rear ered")
    chk("版次 None", e["版次"] is None)

    print("── ★★★★ 砍掉的那一半：**留一条自测证明它为什么不能用** ──")
    #   Osler 的 PPM 14 份 dry-run，9 条题名提议只有 2 条对。这里复现两种典型坏法。
    bad1 = _title_candidate("MEDICAL CENTER STANFORD, CAUF THE PRINCIPLES AND PRACTICE")
    chk(f"藏章被当成题名（实得 {str(bad1)[:34]}）——**所以砍了**",
        bad1 is not None and "STANFORD" in str(bad1))
    bad2 = _title_candidate("WILLIAM ARTHUR JOHNSON PRIEST OF THE PARISH OF WESTON")
    chk(f"献词页被当成题名（实得 {str(bad2)[:34]}）——**所以砍了**",
        bad2 is not None and "JOHNSON" in str(bad2))

    print("\n" + ("✓ 自测全过" if not fails else f"✗ **{len(fails)} 项未过**"))
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--filter", default="", help="只看文件名含这个子串的")
    ap.add_argument("--apply", action="store_true",
                    help="真写台账。**给之前必须先 dry-run 读一遍**")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    led = a.workspace / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        print(f"✗ **{led} 不在——未核验（不是通过）**")
        return 3
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]

    proposals, unreadable = [], []
    for r in rows:
        lp = r.get("local_path") or ""
        nm = pathlib.PurePath(lp).name
        if a.filter and a.filter not in nm:
            continue
        f = a.workspace / lp
        if not f.is_file():
            g = list(a.workspace.rglob(nm)) if nm else []
            if not g:
                unreadable.append((nm, "文件找不到"))
                continue
            f = g[0]
        p = propose(f.read_text(encoding="utf-8", errors="ignore"))
        if not p["版次"]:
            unreadable.append((nm, "题名页读不出版次声明"))
            continue
        proposals.append((r, nm, p["版次"].title(), p))

    print(f"扫了 {len(proposals) + len(unreadable)} 份｜**读得出版次 {len(proposals)} 份**｜"
          f"读不出 {len(unreadable)} 份")
    for r, nm, t, p in proposals:
        print(f"\n  {nm}")
        print(f"     现 title：{r.get('title')}")
        print(f"     **提议**：{t}")
        print(f"     题名页附近的年：{p['题名页附近出现的年']}｜台账年：{r.get('published_at')}")
    if unreadable:
        print(f"\n★ 读不出的 {len(unreadable)} 份（**报出来，不猜**）：")
        for nm, why in unreadable[:10]:
            print(f"     {nm[:46]:48} {why}")

    if not a.apply:
        print("\n（dry-run。**先把上面逐条读一遍**，确认无误再加 --apply。）")
        return 0

    n = 0
    for r, nm, t, p in proposals:
        #: ★★★ **不碰 `title`**——版次不是题名。写进独立字段。
        r["edition_statement"] = t
        r["★ edition_statement 的来源"] = (
            f"**从 `{nm}` 自己的题名页读出来的**（剥掉出处表头后的前 {HEAD_CHARS} 字符）。"
            f"题名页附近出现的年：{p['题名页附近出现的年']}。"
            "★ 不是从文件名推的——文件名是关于文件的断言，不是文件本身。"
            "★★ 本工具**读不出书目题名**（实测 2/9），`title` 仍是待办。")
        n += 1
    led.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n",
                   encoding="utf-8")
    print(f"\n→ 写了 {n} 条 edition_statement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
