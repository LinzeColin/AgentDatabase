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
            q = flat(m.group(1))
            hits = [s for s, b in bodies if q in b]
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

        #   ⑥ ★★ 命中的是 holdout → 必须报出来
        led.write_text(led.read_text(encoding="utf-8").replace(
            '"source_id": "src-b", "local_path": "raw/s2/b.txt", "locator": "ASCE Transactions 91 (1927) p.54", "split": "train"',
            '"source_id": "src-b", "local_path": "raw/s2/b.txt", "locator": "ASCE Transactions 91 (1927) p.54", "split": "holdout"'),
            encoding="utf-8")
        r3 = suggest(ws)
        b3 = next(x for x in r3["逐条"] if x["引文"].startswith("several of the"))
        chk("⑥ ★★ 引文命中的是 **holdout** → 必须报出来（产物不该引它）", "★★" in b3)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only-missing", action="store_true",
                    help="只列同段还没有坐标的那些（配合 check_quote_locator 用）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 workspace")
    r = suggest(pathlib.Path(a.workspace).expanduser().resolve())
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
