#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 galenus_cts 的 TEI-XML 变成可灌库的纯文本，并**按真伪分层**。

## 这一步存在的唯一理由

探源报告的第一条结论：

> **两个语料库都没有机读的真伪标记。** `galenus_cts` 105 部里只有 1 个加星（噪声不是体系），
> First1KGreek 一个也没有。**照单全收会让伪作以 P1 身份进账本而无人拦截。**

所以真伪分层必须在**灌库之前**、由**外部权威**决定，不能靠语料自带的字段。
本脚本的 `DISPUTED` 表来自 `meta.json:attribution_basis.disputed_works`，
其来源是 Fichtner《CORPUS GALENICUM》与 CMG 自身的方括号约定。

**tier 只有两种去处**：不在 DISPUTED 表里 → `P1`；在表里 → `P1-D`（**永不计入 P1**）。
"""
import hashlib, json, pathlib, re, sys, unicodedata

G = pathlib.Path("/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-"
                 "character-distillation-skill-reorganize-d57595/"
                 "c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/galen")
GV = G / "gv/galenus_cts-master/data/tlg0057"
OUT = pathlib.Path(__file__).resolve().parent / "galen-corpus"
WS = pathlib.Path(__file__).resolve().parent / "ws-galen/galen-of-pergamon"

TAG = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t\r\f\v]+")


def plain(xml: str) -> str:
    """TEI → 纯文本。只去标签，**不做任何字符替换**——语料是希腊文，
    任何「顺手规范化」都可能改掉原字（OCR 同形字门的教训）。"""
    body = xml.split("<text", 1)[-1]
    txt = TAG.sub(" ", body)
    txt = txt.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    txt = WS_RE.sub(" ", txt)
    return "\n".join(l.strip() for l in txt.split("\n") if l.strip())


def main() -> int:
    counts = {w["work"]: w for w in json.loads((G / "gv_wordcounts.json").read_text(encoding="utf-8"))}
    meta = json.loads((WS / "meta.json").read_text(encoding="utf-8"))
    disputed = {w["tlg"] for w in meta["attribution_basis"]["disputed_works"] if w["tlg"] != "—"}
    OUT.mkdir(exist_ok=True)

    rows = []
    for tlg, info in sorted(counts.items()):
        # ★ 文件名不统一：verbatim-grc1 / 1st1K-grc1 / 1st1K-grc2 / opp-grc1 都出现过。
        #   第一版硬写 verbatim-grc1，105 部只捞到 7 部——**探源报告里就写着这个坑**
        #   （「不是 1st1K-grc1 的命名，我猜错文件名吃了个 404」），我照样又踩了一次。
        #   改为按 glob 取该目录下最大的希腊文件。
        cands = sorted(GV.glob(f"{tlg}/tlg0057.{tlg}.*grc*.xml"),
                       key=lambda q: q.stat().st_size, reverse=True)
        if not cands:
            continue
        src = cands[0]
        txt = plain(src.read_text(encoding="utf-8"))
        if len(txt) < 400:
            continue
        name = f"galen_{tlg}_grc.txt"
        (OUT / name).write_text(txt, encoding="utf-8")
        rows.append({
            "tlg": tlg, "title": info["title"], "file": name,
            "edition": src.name.rsplit(".", 2)[-2],
            "grc_words": info["grc"], "chars": len(txt),
            "tier": "P1-D" if tlg in disputed else "P1",
            "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest(),
        })

    p1 = [r for r in rows if r["tier"] == "P1"]
    p1d = [r for r in rows if r["tier"] == "P1-D"]
    (OUT / "_manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"落盘 {len(rows)} 部：P1 {len(p1)} ｜ **P1-D {len(p1d)}（按外部权威分层，永不计入 P1）**")
    print(f"  P1 希腊文词数合计 {sum(r['grc_words'] for r in p1):,}")
    print(f"  被分层出去的：{', '.join(sorted(r['tlg'] for r in p1d))}")
    miss = disputed - {r['tlg'] for r in rows}
    if miss:
        print(f"  ⚠ DISPUTED 表里有 {len(miss)} 条在语料中找不到（正常，表里含非 galenus_cts 条目）：{sorted(miss)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
