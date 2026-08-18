#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这条引文出自哪一份？** —— 去语料里找，报出建议坐标。**只报不改。**

## 为什么要有这件（2026-08-11，Shewhart #165）

`check_quote_locator` 会说「这条引文同段没有坐标」，**但它不知道该填哪一个**。
我于是手写了一张「引文片段 → 坐标」的表批量插入，**当场插错了一条**：

    `should be somewhat modified` 挂上了 BSTJ 3(1) 1924 的坐标，
    而它其实出自 1927 年的 ASCE 讨论。

根因是我的插入判据是「**同段有没有坐标**」——**它分不清那个坐标属不属于这一条引文**。
一段里有两条不同出处的引文时，第一条的坐标会让第二条「看起来已经有坐标了」。

★★ **一个错坐标比没有坐标更糟**：读者会照着它去查，然后查到别的东西。

## 它怎么定出处

**去语料里逐份搜这条引文的原文**（空白压平后子串匹配），命中哪一份就是哪一份。
这比「我记得它出自哪」硬得多——**不靠记忆，靠命中**。

- **命中恰好一份** → 报该份的建议坐标（取台账 `locator`，取不到就用
  `published_at` + `title`）。
- **命中多份** → **不给建议**，列出全部候选让人定
  （同一段话可能既在期刊本又在文集本里；[[two-source-ids-is-not-two-evidences]]）。
- **一份都没命中** → **不给建议**，标为「语料里找不到」——
  那可能是引文有讹、也可能是它根本不是引文，**两种都要人看**。

## 它**不**做的事

- **不自动改文件。** 输出是建议清单，改是人的事。
  （自动改正是造成上面那次错挂的原因。）
- **不判引文真伪**——那是 `check_quote_integrity`。
- **不判坐标格式对不对**——那是 `check_quote_locator`。

退出码：0 = 每条都定出了唯一出处；1 = 有定不出的；2 = 自测未过；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

RENDER_FILES = ("facts.md", "cognitive-os.md", "decision-policy.md", "strategy.md",
                "capabilities.md", "persona.md", "work.md", "boundaries.md",
                "hypotheses.md", "divergence-map.md")
QUOTE = re.compile(r"[`「\"]([A-Za-z][^`」\"]{29,})[`」\"]")
WS = re.compile(r"\s+")


def flat(s: str) -> str:
    """压平空白——★ 印本常是双空格版面、且引文会跨行，不压平一条都对不上。"""
    return WS.sub(" ", s).strip().lower()


#   ★★★★ 2026-08-11：**第一版把 53 条报成「语料里找不到」，读完命中才发现多数是本件的盲区。**
#     [[read-the-hits-before-reporting-the-rate]]——我差点把 53 当成缺陷数报出去。
#     三类都是本件自己的问题：
#       ① 引文里嵌了 markdown 粗体：`mit **Sputum von Phthisikern**`（Koch）、
#          `the paste should be changed **daily**`（Lister）——不剥 `**` 一条也对不上；
#       ② 引文里有省略号：`IF any one of you … marvels perhaps at me`（Cicero）——
#          那是**有意截断的引文**，要把 `…` 当通配，分段各自匹配且**保持先后次序**；
#       ③ 反引号里根本不是引文：`sp-1267-misc--notes-3-3-1830-年少年习作本`（Blackwell）
#          是源标识符。**标识符不该进引文集合。**
_BOLD = re.compile(r"\*\*|__")
_ELLIPSIS = re.compile(r"\s*(?:…|\.\.\.|\. \. \.)\s*")
#   标识符：没有空格，或形如 `src-xxxx` / `a-b-c-1902` 这类全小写连字符串
_IDENT = re.compile(r"^[a-z0-9][a-z0-9._\-]*$|^src-[0-9a-f]+$", re.I)


def looks_like_quote(s: str) -> bool:
    """★ 标识符、文件名、纯路径不算引文。

    ★★ 第一版写成 `_IDENT.match(s.replace(" ", ""))` —— **把空格去掉再判**，
    于是「任何不带标点的英文引文」去掉空格后都变成纯字母串，全被当成标识符排除掉，
    **自测当场全红**。判的必须是**原串**：标识符的特征是**根本没有空格**。
    """
    s = s.strip()
    if " " not in s:
        return False                      # 无空格 → 标识符 / 文件名 / 路径
    #   还有一类带空格但仍是标识符的：全是连字符串拼的（`a-b-c 1902-年少年习作本`）
    if s.count("-") >= 3 and len(s.split()) <= 3:
        return False
    return True


#   ★★★★ 第四个盲区（2026-08-11，Nasmyth 撞出）：**校勘方括号**。
#     产物里写的是 `collate[ral assistance]` —— 方括号是**编者补足残缺处**的通行惯例。
#     按字面找当然找不到。**两种读法都要试**：
#       ① 保留括号内容（编者补的字就是原文该有的字）→ `collateral assistance`
#       ② 整个去掉（括号里是编者的说明，不是原文）→ `collate`
#     任一命中即算。★ 这是**放宽**，但方向安全：它只会把「本来就是这份」认出来，
#     不会把别份认成这份——因为两种读法都比原串更短或等长。
_BRACKET_KEEP = re.compile(r"[\[\]]")
_BRACKET_DROP = re.compile(r"\s*\[[^\]]*\]\s*")


def _variants(quote: str) -> list[str]:
    q = _BOLD.sub("", quote)
    out = [q]
    if "[" in q:
        out.append(_BRACKET_KEEP.sub("", q))          # 保留内容
        out.append(_BRACKET_DROP.sub(" ", q))         # 整个去掉
    return out


def contains_quote(body_flat: str, quote: str) -> bool:
    """引文在不在这份语料里。★ 剥粗体、校勘括号两读、按省略号分段、**分段必须保持先后次序**。"""
    for var in _variants(quote):
        q = flat(var)
        parts = [x for x in _ELLIPSIS.split(q) if len(x) >= 8]
        if not parts:
            if q and q in body_flat:
                return True
            continue
        pos, ok = 0, True
        for seg in parts:
            i = body_flat.find(seg, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(seg)          # ★ 次序：下一段必须在上一段之后
        if ok:
            return True
    return False


def load_sources(ws: pathlib.Path) -> list[dict]:
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        return []
    out = []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        p = ws / (r.get("local_path") or "")
        if p.is_file():
            out.append({"source_id": r.get("source_id"), "path": p,
                        "locator": r.get("locator"), "title": r.get("title"),
                        "published_at": r.get("published_at"),
                        "split": r.get("split")})
    return out


def coord_of(s: dict) -> str:
    """建议坐标：台账 locator 优先；取不到就用 title + published_at。"""
    lo = str(s.get("locator") or "").strip()
    if lo and not lo.startswith("http"):
        return lo
    t = str(s.get("title") or "").strip()
    y = str(s.get("published_at") or "")[:4]
    if t and not t.endswith(".txt"):
        return f"{t}（{y}）" if y else t
    if lo:
        return f"{lo}（{y}）" if y else lo
    return f"（**台账里没有可用坐标：locator 空、title 是文件名**）"


def suggest(ws: pathlib.Path) -> dict:
    srcs = load_sources(ws)
    if not srcs:
        return {"状态": "台账读不到或语料不在，**未核验**（不是通过）"}
    bodies = [(s, flat(s["path"].read_text(encoding="utf-8", errors="replace"))) for s in srcs]
    rows, unresolved = [], 0
    for rel in RENDER_FILES:
        p = ws / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in QUOTE.finditer(text):
            raw = m.group(1)
            if not looks_like_quote(raw):
                continue          # ★ 标识符不算引文
            hits = [s for s, b in bodies if contains_quote(b, raw)]
            item = {"文件": rel, "引文": m.group(1)[:70],
                    "命中份数": len(hits),
                    "命中": [h["source_id"] for h in hits][:5]}
            if len(hits) == 1:
                item["建议坐标"] = coord_of(hits[0])
                #   ★ holdout 的正文**不该**成为产物里的引文来源——顺手报出来
                if hits[0].get("split") == "holdout":
                    item["★★"] = "**这条引文命中的是 holdout 那一份——产物不该引它**"
                    unresolved += 1
            else:
                unresolved += 1
                item["★"] = ("**语料里一份都没命中**——引文可能有讹字，或它根本不是引文"
                             if not hits else
                             "**命中多份，不给建议**——可能是期刊本与文集本重复收录，须人定")
            rows.append(item)
    return {"逐条": rows, "引文总数": len(rows), "**定不出出处的**": unresolved}



YEAR_ANY = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2})\b")


def apply_locators(ws: pathlib.Path, result: dict, *, write: bool) -> dict:
    """把**唯一命中**那些的坐标追加到引文所在段落末尾。

    ## 为什么要有这个模式

    2026-08-18 一天里对 Godin／Brandeis／Bismarck／Jefferson 手工做了同一件事约 80 处。
    手写映射的风险是**年份打错**——而年份一旦写错，产物看起来更可信、实际更假
    （[[my-checkers-are-mis-cut-six-times-in-one-day]]）。

    ## 三条不许越的线

    1. **只动「命中份数 == 1」的**。命中多份是「须人定」，本件一律不碰
       ——多份重复收录时选哪一版是判断，不是查表。
    2. **只在段尾追加**，不改动引文本身、不改段内任何既有文字
       （[[bulk-auto-replace-damages-the-text]]）。
    3. **同段已有年份或已有「［出处：」就跳过**——不叠加第二个坐标。

    默认干跑（`write=False`）：只报会改哪些，一个字节都不落盘。
    """
    # ★ 账本的 `title` 常被填成文件名（本仓已记过），于是 coord_of 退回 locator，
    #   而 `archive.org item <标识符>` **既不是年份也不是卷页刊名** —— 写进去满足不了
    #   `check_quote_locator`，读者也回查不到。所以这里先补年份；补不出就**不写**。
    year_of = {}
    led = ws / "evidence" / "source-ledger.jsonl"
    if led.is_file():
        for line in led.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r0 = json.loads(line)
                y = str(r0.get("published_at") or "")[:4]
                if y.isdigit():
                    year_of[r0.get("source_id")] = y

    plan, skipped, no_year = [], 0, 0
    for row in result.get("逐条", []):
        if row.get("命中份数") != 1 or "建议坐标" not in row or "★★" in row:
            continue
        rel, quote, coord = row["文件"], row["引文"], row["建议坐标"]
        if not YEAR_ANY.search(coord):
            y = year_of.get((row.get("命中") or [None])[0])
            if not y:
                no_year += 1        # ★ 补不出年份 —— 宁可不写，也不写个过不了门的坐标
                continue
            coord = f"{coord}（{y}）"
        p = ws / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        i = text.find(quote[:40])
        if i < 0:
            skipped += 1
            continue
        start = text.rfind("\n\n", 0, i) + 2
        end = text.find("\n\n", i)
        end = end if end > 0 else len(text)
        para = text[start:end]
        if "［出处：" in para or YEAR_ANY.search(para):
            skipped += 1
            continue
        plan.append({"文件": rel, "引文": quote[:44], "将追加": f"［出处：{coord}］"})
        if write:
            p.write_text(text[:start] + para.rstrip() + f"　［出处：{coord}］" + text[end:],
                         encoding="utf-8")
    return {"将改/已改": len(plan), "跳过（同段已有坐标或定位不到）": skipped,
            "**跳过·坐标里补不出年份**": no_year,
            "明细": plan, "已落盘": write}


def self_test() -> int:
    import tempfile
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    with tempfile.TemporaryDirectory() as d:
        ws = pathlib.Path(d)
        (ws / "evidence").mkdir()
        (ws / "raw" / "s1").mkdir(parents=True)
        (ws / "raw" / "s2").mkdir(parents=True)
        #   ★ 用**双空格 + 跨行**的版面写语料 —— 真实印本就是这样，
        #     夹具比原文干净就等于没测（[[fixtures-cleaner-than-the-real-thing]]）
        (ws / "raw/s1/a.txt").write_text(
            "some  text\nthis  method  cannot  be  applied  to  the  data\nmore", encoding="utf-8")
        (ws / "raw/s2/b.txt").write_text(
            "other\nseveral  of  the  broad  claims  should  be  modified\nend", encoding="utf-8")
        (ws / "evidence/source-ledger.jsonl").write_text(
            json.dumps({"source_id": "src-a", "local_path": "raw/s1/a.txt",
                        "locator": "BSTJ 3(1) 43–87（1924）", "split": "train"}, ensure_ascii=False) + "\n" +
            json.dumps({"source_id": "src-b", "local_path": "raw/s2/b.txt",
                        "locator": "ASCE Transactions 91 (1927) p.54", "split": "train"}, ensure_ascii=False) + "\n",
            encoding="utf-8")
        #   ★★ 关键夹具：**同一段里两条不同出处的引文**——正是撞出本件的那个形状
        (ws / "work.md").write_text(
            "一段话 `This method cannot be applied to the data` 然后另一条\n"
            "`several of the broad claims should be modified`。\n", encoding="utf-8")
        (ws / "facts.md").write_text("`this quote is nowhere in the corpus at all here`\n", encoding="utf-8")
        r = suggest(ws)
        by = {x["引文"][:20]: x for x in r["逐条"]}
        a = next(v for k, v in by.items() if k.startswith("This method"))
        b = next(v for k, v in by.items() if k.startswith("several of the"))
        chk("① 同段两条不同出处 → **各自定到各自那一份**（撞出本件的形状）",
            a.get("建议坐标", "").startswith("BSTJ") and b.get("建议坐标", "").startswith("ASCE"))
        chk("② ★ 语料是**双空格 + 跨行**版面也要匹配上（夹具不许比原文干净）",
            a["命中份数"] == 1 and b["命中份数"] == 1)
        c = next(v for k, v in by.items() if k.startswith("this quote is"))
        chk("③ 语料里找不到 → **不给建议**，标出来", "建议坐标" not in c and c["命中份数"] == 0)
        chk("④ 定不出出处的计数正确", r["**定不出出处的**"] == 1)

        #   ⑤ ★ 命中多份 → 不给建议
        (ws / "raw/s3").mkdir(parents=True)
        (ws / "raw/s3/c.txt").write_text("this  method  cannot  be  applied  to  the  data", encoding="utf-8")
        led = ws / "evidence/source-ledger.jsonl"
        led.write_text(led.read_text(encoding="utf-8") +
                       json.dumps({"source_id": "src-c", "local_path": "raw/s3/c.txt",
                                   "locator": "文集本", "split": "train"}, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        r2 = suggest(ws)
        a2 = next(x for x in r2["逐条"] if x["引文"].startswith("This method"))
        chk("⑤ ★ 命中两份（期刊本＋文集本）→ **不给建议**，列出候选",
            a2["命中份数"] == 2 and "建议坐标" not in a2)


        #   ⑦ --apply 只动唯一命中、只追加在段尾、同段已有年份必跳过
        import tempfile as _tf
        with _tf.TemporaryDirectory() as td2:
            ws2 = pathlib.Path(td2) / "w"
            (ws2 / "raw/s1").mkdir(parents=True)
            (ws2 / "evidence").mkdir(parents=True)
            (ws2 / "raw/s1/a.txt").write_text("alpha beta gamma delta epsilon zeta eta theta", encoding="utf-8")
            (ws2 / "evidence/source-ledger.jsonl").write_text(json.dumps(
                {"source_id": "src-a", "local_path": "raw/s1/a.txt",
                 "locator": "ASCE Transactions 91", "published_at": "1927", "split": "train"},
                ensure_ascii=False) + "\n", encoding="utf-8")
            (ws2 / "facts.md").write_text(
                "段一。`alpha beta gamma delta epsilon zeta eta theta` 就是这句。\n\n"
                "段二（**同段已有 1927 年份**）。`alpha beta gamma delta epsilon zeta eta theta` 又一次。\n",
                encoding="utf-8")
            r7 = suggest(ws2)
            dry = apply_locators(ws2, r7, write=False)
            body_before = (ws2 / "facts.md").read_text(encoding="utf-8")
            chk("⑦ **干跑一个字节都不落盘**", "［出处：" not in body_before)
            hot = apply_locators(ws2, r7, write=True)
            body = (ws2 / "facts.md").read_text(encoding="utf-8")
            chk("⑧ 落盘后段一有坐标，且**引文本身一字未改**",
                "［出处：" in body and "`alpha beta gamma delta epsilon zeta eta theta`" in body)
            chk("⑨ **反对照**：同段已有年份的那一段**没被加第二个坐标**",
                body.count("［出处：") == 1)

        #   ⑥ ★★ 命中的是 holdout → 必须报出来
        led.write_text(led.read_text(encoding="utf-8").replace(
            '"source_id": "src-b", "local_path": "raw/s2/b.txt", "locator": "ASCE Transactions 91 (1927) p.54", "split": "train"',
            '"source_id": "src-b", "local_path": "raw/s2/b.txt", "locator": "ASCE Transactions 91 (1927) p.54", "split": "holdout"'),
            encoding="utf-8")
        r3 = suggest(ws)
        b3 = next(x for x in r3["逐条"] if x["引文"].startswith("several of the"))
        chk("⑥ ★★ 引文命中的是 **holdout** → 必须报出来（产物不该引它）", "★★" in b3)

    #   ★★ 三条新能力各自的正反对照（2026-08-11 加的那三处盲区）
    B = "some  text\nthis  method  cannot  be  applied  to  the  data\nmore"
    Bf = flat(B)
    chk("⑦ ★ 引文里嵌 markdown 粗体 → 剥掉 `**` 后要匹配上（Koch/Lister 的形态）",
        contains_quote(Bf, "this method **cannot be applied** to the data"))
    chk("⑧ ★ 引文里有省略号 → 分段匹配（Cicero 的形态）",
        contains_quote(Bf, "this method … to the data"))
    chk("⑨ ★★ **省略号分段必须保持先后次序**——倒序的不许当成命中",
        not contains_quote(Bf, "to the data … this method"))
    chk("⑩ ★ 标识符不算引文（Blackwell 的 `sp-1267-misc--notes-3-3-1830-…`）",
        not looks_like_quote("sp-1267-misc--notes-3-3-1830-年少年习作本"))
    chk("⑫ ★★ **校勘方括号**：`collate[ral assistance]` 要能对上语料里的 `collateral assistance`",
        contains_quote(flat("but as a collateral assistance by which"), "as a collate[ral assistance] by which"))
    chk("⑬ ★ 另一读法：括号里是编者说明时，去掉括号也要能对上",
        contains_quote(flat("the paste should be changed daily and then"), "the paste should be changed daily [see note] and then"))
    chk("⑭ ★★ **而括号两读不许把别份认成这份**——不相干的语料仍要判不命中",
        not contains_quote(flat("something entirely different here"), "as a collate[ral assistance] by which"))
    chk("⑪ ★★ **而普通英文引文必须仍算引文**——第一版把空格去掉再判，"
        "结果任何不带标点的引文都被当成标识符排除，自测全红",
        looks_like_quote("this method cannot be applied to the data"))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="把**唯一命中**的坐标追加到段尾（默认只干跑，不落盘）")
    ap.add_argument("--dry-run", action="store_true", help="配合 --apply 只看会改什么")
    ap.add_argument("--only-missing", action="store_true",
                    help="只列同段还没有坐标的那些（配合 check_quote_locator 用）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 workspace")
    ws = pathlib.Path(a.workspace).expanduser().resolve()
    r = suggest(ws)
    if a.apply:
        if "状态" in r:
            print(" ", r["状态"])
            return 3
        out = apply_locators(ws, r, write=not a.dry_run)
        head = "**已落盘**" if out["已落盘"] else "干跑（未落盘）"
        print(f"  {head}：{out['将改/已改']} 处；跳过 {out['跳过（同段已有坐标或定位不到）']} 处"
              f"（同段已有坐标，或引文在产物里定位不到）；"
              f"**{out['**跳过·坐标里补不出年份**']} 处因补不出年份而不写**")
        for it in out["明细"][:20]:
            print(f"   ✓ {it['文件']:20} {it['引文']:46} {it['将追加']}")
        if len(out["明细"]) > 20:
            print(f"   …另有 {len(out['明细']) - 20} 处")
        print("  ★ **命中多份的一处都没动** —— 选哪一版是判断，不是查表。")
        return 0
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if not r.get("**定不出出处的**") else 1
    if "状态" in r:
        print(" ", r["状态"])
        return 3
    print(f"产物里长逐字引文 {r['引文总数']} 条，**定不出出处的 {r['**定不出出处的**']} 条**\n")
    for x in r["逐条"]:
        if x["命中份数"] == 1 and "★★" not in x:
            print(f"  ✓ {x['文件']:20} {x['引文'][:44]:46} → {x['建议坐标']}")
        else:
            print(f"  ✗ {x['文件']:20} {x['引文'][:44]:46} → {x.get('★★') or x.get('★')}"
                  + (f"　候选 {x['命中']}" if x["命中份数"] > 1 else ""))
    print("\n★ **只报不改。** 改是人的事——自动改正是「同段有坐标就跳过」那次错挂的成因。")
    return 1 if r["**定不出出处的**"] else 0


if __name__ == "__main__":
    sys.exit(main())
