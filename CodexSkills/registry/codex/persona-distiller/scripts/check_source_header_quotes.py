#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**语料文件头里引的话，正文里必须真有**——头部是判据的盲区。

## 撞出它的那一次

Slavyanov #115 的 `stahl-eisen-1888-…` 文件头写着：

```
# SOURCE: Patentbericht, Stahl und Eisen 1888: «Kl. 48, Nr. 43194, vom 23. September 1887. …»
```

**用书名号引着，形态上是照录。** 而同一个文件的正文印的是：

```
Kl. 48» Kr. 48194, vom 23. September 1887.
```

**是 48194，不是 43194。** 头部把 OCR 改了一位再当逐字引文用。

同一天 Carver #127 也撞到同类（`iSyy.` 被写成 `1899.`），
**两次都不是门抓出来的**——一次是我重跑判据时偶然撞到，
一次是子代理如实报跨语料矛盾牵出来的。

## 为什么这道特别容易漏

`check_quote_integrity` 管断言层、答案层，v0.0.0.130 起加了研究文档层。
**唯独没管过语料文件自己的头部**——而头部恰恰是「这份东西是什么」的唯一说明，
下游的分档、归属、坐标全从它来。**头错了，下游全部跟着错，而且看起来有据。**

## 判据

扫 `raw/**/*.txt`：把开头连续的 `#` 注释行当作**头部**，
头部里被 `«»` / `「」` / `""` 包起来、且投影后 ≥18 个字母数字的片段，
**必须能在同一文件的正文里找到**（投影与 `check_quote_integrity` 同口径）。

## ★★★ 它的覆盖面很小，这一点必须先说

**全库实跑（2026-08-05）：5,016 份 .txt，1,405 份带头部，
而头部里被引号包起来的片段只有 2 条。**

也就是说：**「全库 0 缺陷」的真实含义是「它能看见的那 2 处没问题」，
不是「语料是干净的」。** 绝大多数语料文件的头部**根本不引原文**
（只写 SOURCE/URL/retrieved/extraction 这类著录），本件对它们无话可说。

★ 它抓到的三处真缺陷，**全部集中在最近抓的俄德语料**
（Slavyanov #115 两处、Carver #127 一处由别的判据抓到）——
因为只有那批抓源方养成了「在头部引一句原文」的习惯。
**习惯不同的抓源方，本件看不见他们的错。**

★★ 所以本件的正确用法是：**它是一道窄而深的门，不是普查工具。**
报「0」时必须连同「头部引文只有 N 条」一起报，否则那个 0 会被读成全库体检合格。

## ★ 它不做什么

- **不管头部里的散文**。只认被引号包起来的部分——那才是在声称「原文如此」。
- **不跨文件找**。头部引的若是别处的话，本件报不出来，也不该报。
- **不判对错**。它只说「你说是照录的这句，这份文件里没有」。
"""
import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from check_quote_integrity import proj                    # 与引文核验器同一投影
except Exception:                                             # noqa: BLE001
    def proj(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

MIN = 18
QUOTED = re.compile(r"«([^»]{4,400})»|「([^」]{4,400})」|“([^”]{4,400})”")
# ★★★ 书目标题 vs 引正文：**德文/法文书目惯例把篇名放进 «»**，
#   那是在报「这篇文章叫什么」，**不是在声称「本文件正文里有这句」**。
#   实测：不区分的话 11 条头部引文里报出 8 条，**其中大半是篇名** —— 那种误报率
#   会让人学会忽略这道门（本项目已有明训）。
#
#   可用的区分点是**位置**：
#     · 篇名式：`作者，«篇名»，刊名 年份` —— 刊名/年份在引号**之后**
#     · 引正文式：`Patentbericht, Stahl und Eisen 1888: «Kl. 48, Nr. 43194 …»` —— 刊名/年份在**之前**
#   四例实测（两真两误）全部分对。
TAIL_BIB = re.compile(r"^[^«»「」“”]{0,60}?"
                      r"(?:\b(?:1[5-9]|20)\d{2}\b|Jahrgang|Band|vol\.|ETZ|Zeitschrift|"
                      r"Proceedings|Journal|Review|Magazine)", re.I)


def header_and_body(text: str) -> tuple:
    lines = text.splitlines()
    head, i = [], 0
    while i < len(lines) and (lines[i].startswith("#") or not lines[i].strip()):
        head.append(lines[i])
        i += 1
    return "\n".join(head), "\n".join(lines[i:])


def scan(paths: list) -> dict:
    files = []
    for p in paths:
        p = pathlib.Path(p)
        files.extend(sorted(f for f in p.rglob("*.txt") if not f.name.startswith("_"))
                     if p.is_dir() else [p])
    if not files:
        return {"状态": "**未核（不是通过）**：没有找到任何 .txt"}

    n_head, n_q, bad = 0, 0, []
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except Exception:                                     # noqa: BLE001
            continue
        head, body = header_and_body(t)
        if not head.strip():
            continue
        n_head += 1
        pbody = proj(body)
        for m in QUOTED.finditer(head):
            q = next(g for g in m.groups() if g is not None)
            pq = proj(q)
            if len(pq) < MIN:
                continue
            if TAIL_BIB.match(head[m.end():]):
                continue            # 书目标题，不是在声称本文件正文里有这句
            n_q += 1
            if pq not in pbody:
                bad.append({"文件": f.name, "头部引的": " ".join(q.split())[:120]})

    return {
        "扫到的 .txt": len(files),
        "带头部的": n_head,
        "头部里的引文": n_q,
        "**正文里找不到的**": len(bad),
        "逐条": bad[:40],
        "★ 口径": ("**只认被引号包起来的部分**——那才是在声称「原文如此」。"
                   "头部里的散文不管，跨文件不找。"),
        "★★ 为什么要它": ("Slavyanov #115 头部引 `«Nr. 43194»` 而同文件正文印的是 `48194`；"
                          "Carver #127 把 `iSyy.` 写成 `1899.`。**同一天、两个工作区、"
                          "都不是门抓出来的**——头部此前不在任何判据的射程里。"),
    }


def self_test() -> int:
    import tempfile
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    with tempfile.TemporaryDirectory() as td:
        r = pathlib.Path(td)
        # ① Slavyanov 的真实形状：头部 43194，正文 48194
        (r / "slav.txt").write_text(
            "# SOURCE: Patentbericht, Stahl und Eisen 1888: «Kl. 48, Nr. 43194, vom 23. September 1887.»\n"
            "# URL: https://archive.org/details/x\n\n"
            "gakgl und vollgegossen.\nKl. 48» Kr. 48194, vom 23. September 1887.\n"
            "Nicolas de Benardos in 8t. Petersburg.\n", encoding="utf-8")
        # ② 头部引的与正文一致——不许报
        (r / "good.txt").write_text(
            "# SOURCE: «Kl. 48» Kr. 48194, vom 23. September 1887.»\n\n"
            "Kl. 48» Kr. 48194, vom 23. September 1887.\n", encoding="utf-8")
        # ③ 头部只有散文，没有引号——不许报
        (r / "prose.txt").write_text(
            "# SOURCE: Stahl und Eisen 1888 patent bulletin, Benardos entry\n\n"
            "Kl. 48» Kr. 48194.\n", encoding="utf-8")
        # ④ 引号里太短——不足 18 个字母数字，不报
        (r / "short.txt").write_text("# SOURCE: «Nr. 431»\n\n无关正文 abcdefgh\n", encoding="utf-8")

        # ⑤ 德文书目惯例：篇名放 «»，刊名年份在**后**——不许报
        (r / "title_de.txt").write_text(
            "# SOURCE: F. C. Muehlhaeuser, «Das Benardossche elektrische Schmelzverfahren», "
            "Stahl und Eisen (Duesseldorf), Jahrgang 1894.\n\n"
            "voellig anderer Fliesstext ohne den Titel.\n", encoding="utf-8")
        # ⑥ 引正文式：刊名年份在**前**，引号里是正文——必须报
        (r / "quote_de.txt").write_text(
            "# SOURCE: Patentbericht, Stahl und Eisen 1888: "
            "«Kl. 48, Nr. 43194, vom 23. September 1887.»\n\n"
            "Kl. 48» Kr. 48194, vom 23. September 1887.\n", encoding="utf-8")

        out = scan([r])
        names = {b["文件"] for b in out["逐条"]}
        print("── ★★★ 反向对照①：**Slavyanov 那种改了一位的必须抓到** ──")
        # ★ 本条原写 `names == {"slav.txt"}`，加了夹具⑥之后就该是两个了。
        #   **是这条对照自己陈旧了，不是代码错**——照实改成两个。
        chk(f"报出 {sorted(names)}", names == {"slav.txt", "quote_de.txt"})

        print("── ★★ 反向对照②：**头部与正文一致的不许报**（否则天天误报） ──")
        chk("good.txt 不在报出里", "good.txt" not in names)

        print("── ★★ 反向对照③：**头部只有散文的不许报**——散文不是在声称照录 ──")
        chk("prose.txt 不在报出里", "prose.txt" not in names)

        print("── ★ 反向对照④：**太短的片段不报**（与引文核验器同一下限 18） ──")
        chk("short.txt 不在报出里", "short.txt" not in names)

        print("── ★★★ 反向对照⑤：**德文书目惯例的篇名不许报**（刊名年份在引号后） ──")
        chk("title_de.txt 不在报出里", "title_de.txt" not in names)

        print("── ★★★ 反向对照⑥：**引正文式必须报**（刊名年份在引号前） ──")
        chk("quote_de.txt 在报出里", "quote_de.txt" in names)

        print("── ★ 反向对照⑦：一个 .txt 都没有 → 说「未核」不说「通过」 ──")
        with tempfile.TemporaryDirectory() as t2:
            chk("未核", "未核" in str(scan([pathlib.Path(t2)]).get("状态", "")))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="语料目录或 .txt")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.paths:
        ap.error("要么 --self-test，要么给至少一个路径")
    out = scan(a.paths)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if out.get("**正文里找不到的**") else 0


if __name__ == "__main__":
    sys.exit(main())
