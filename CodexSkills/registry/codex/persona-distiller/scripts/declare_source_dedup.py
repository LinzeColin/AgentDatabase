#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `check_source_dedup` 报出的重复对**逐边**声明成 `derived_from`。

## ★★★★ 为什么必须逐边，不能按连通分量

`check_source_dedup` 免报的条件是「声明的连通分量连得上」，
于是最省事的写法是「整簇指向一个基准件」。**那样会写出假话。**

Blackwell #118 实测：61 对 → **6 个连通分量，最大的两个是 15 份和 11 份**，
而它们之所以连成一片，是因为 **1902 年的《Essays in Medical Sociology》合集
重印了它收录的每一篇小册子**。按簇指基准件，等于宣称
「防治狂犬病演说」派生自「女子医学院开办词」——**两篇毫不相干的东西**。

**所以本工具只声明判据真正报出来的那些边，一条不多。**

## ★★★★ 默认只声明**机械上确定**的那一类，其余交给人读

**确定的**＝去掉来源后缀（`-ia` `-nlm` `-DUPSCANn` `-alt` `-bsb` `-uoft` `-emory` `-goog`…）
之后**词干相同**。那是同一件东西的另一份副本，没有判断余地。

**其余一律不写**，只列出来给人读。**为什么必须这样**——Nightingale #112 实测：

- 465 对里，**确定的只有 48 对**。
- 剩下 417 对里有大量**跨作品的真实重印**：
  `notes-british-army-1858` ↔ `subsidiary-notes-1858`（0.69）、
  `mortality-british-army-1858` ↔ `royal-commission-report-1858`（0.44）——
  **皇家委员会报告收录了她的 Notes，两者确实大段相同，但不是同一部作品。**
- 第一版工具用「干净词占比」做 tiebreak，于是排出了这种边：

  ```
  notes-british-army-1858.txt              → subsidiary-notes-1858-DUPSCAN.txt   ← 基准件是重复扫描件
  royal-commission-report-1858-DUPSCAN.txt → mortality-british-army-1858-DUPSCAN.txt ← 跨作品
  ```

  **方向是随意的，有的还是荒谬的。**

★ Blackwell #118 能一次做完（61 → 0）是因为它的对子干净（小册子 ↔ 合集 ↔ 另一份扫描）；
**别把那次的顺利当成通例。**

给 `--include-uncertain` 才会写不确定的那批，方向按：
合集（与 ≥3 份重叠）→ 小册子；否则正文更脏的指向更干净的。
**用它之前请先把 dry-run 的清单读一遍。**

## ★★ `derived_from` 在这里的口径

不必是字面上的转录派生，表示的是「**与所指来源实为同一部作品**」——
`check_source_dedup` 自己的问题就是「来源计数里有几份其实是同一部作品」。
每条声明都会写一句口径进台账，**不留下无解释的字段**。

## ★ 它不改变什么

`distinct_works` 与 `inflation` **一个字都不会变**——声明只是把已知的事实写下来。
Blackwell 实测：61 → 0 未声明，而 `distinct_works` 仍是 56、`inflation` 仍是 1.536。
**如果你看到 `distinct_works` 变了，那是出 bug 了。**
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SUFFIX = re.compile(
    r"[-_](?:ia|nlm|bsb|uoft|emory\d*|goog|google|alt\d*|dupscan\d*|"
    r"v\d|bd\d|vol\d|copy\d|scan\d|dup\d)$", re.I)
HUB_MIN = 3          # 与这么多份以上重叠 → 判为合集
CLEAN = re.compile(r"[A-Za-zÀ-ÿ]{2,}")


def clean_ratio(p: pathlib.Path) -> float:
    """干净词占比。★ 这把尺子很粗（`usriude` 这种 OCR 沙拉也算干净词），
    **只用来在两份同源文本之间比相对好坏**，不当绝对判据。"""
    if not p.is_file():
        return 0.0
    toks = p.read_text(encoding="utf-8", errors="replace").split()
    if not toks:
        return 0.0
    return sum(1 for w in toks if CLEAN.fullmatch(w)) / len(toks)


def strip_suffix(stem: str) -> str:
    prev = None
    while prev != stem:
        prev, stem = stem, SUFFIX.sub("", stem)
    return stem


def run_checker(ws: pathlib.Path) -> dict:
    r = subprocess.run([sys.executable, str(HERE / "check_source_dedup.py"), str(ws), "--json"],
                       capture_output=True, text=True)
    if not r.stdout.strip():
        raise SystemExit(f"✗ 判据没有输出：{r.stderr.strip()[:300]}")
    return json.loads(r.stdout)


def is_certain(a: str, b: str) -> bool:
    """去掉来源后缀之后词干相同 → **机械上确定是同一件的另一份副本**。"""
    sa, sb = pathlib.PurePath(a).stem, pathlib.PurePath(b).stem
    return sa != sb and strip_suffix(sa) == strip_suffix(sb)


def decide(pairs: list[dict], byname: dict[str, dict], ws: pathlib.Path
           ) -> list[tuple[str, str, str]]:
    """→ [(派生方文件名, 基准件文件名, 理由)]，逐边。"""
    deg = collections.Counter()
    for p in pairs:
        deg[p["甲"]] += 1
        deg[p["乙"]] += 1
    ratio: dict[str, float] = {}

    def cr(n: str) -> float:
        if n not in ratio:
            rec = byname.get(n) or {}
            ratio[n] = clean_ratio(ws / (rec.get("local_path") or ""))
        return ratio[n]

    out = []
    for p in pairs:
        a, b = p["甲"], p["乙"]
        sa, sb = pathlib.PurePath(a).stem, pathlib.PurePath(b).stem
        ha, hb = deg[a] >= HUB_MIN, deg[b] >= HUB_MIN
        if ha != hb:                                   # 合集 → 小册子
            src, base = (a, b) if ha else (b, a)
            out.append((src, base, f"**合集重印了它**（与 {deg[src]} 份其它源重叠）"))
            continue
        if strip_suffix(sa) == strip_suffix(sb) and sa != sb:   # 来源后缀
            src, base = (a, b) if len(sa) > len(sb) else (b, a)
            out.append((src, base, "**同一件的另一份扫描/来源副本**（只差来源后缀）"))
            continue
        src, base = (a, b) if cr(a) < cr(b) else (b, a)
        out.append((src, base,
                    f"**同一部作品的另一份见证**（正文干净度 {cr(src):.3f} < {cr(base):.3f}，"
                    f"脏的指向干净的）"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("workspace")
    ap.add_argument("--apply", action="store_true", help="真写台账；不给就是 dry-run")
    ap.add_argument("--include-uncertain", action="store_true",
                    help="连不确定的那批也写。**用之前先把 dry-run 清单读一遍。**")
    a = ap.parse_args()
    ws = pathlib.Path(a.workspace).resolve()
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        print(f"✗ 没有 {led}", file=sys.stderr)
        return 2

    before = run_checker(ws)
    pairs = before["**未声明的重复对**"]
    print(f"{ws.name}：未声明 {len(pairs)} 对｜可用 {before['usable']}｜"
          f"去重后作品 {before['distinct_works']}｜膨胀 {before['inflation']}")
    if not pairs:
        print("→ 无事可做")
        return 0

    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    byname = {pathlib.PurePath(r.get("local_path") or "").name: r for r in rows}
    certain = [p for p in pairs if is_certain(p["甲"], p["乙"])]
    uncertain = [p for p in pairs if not is_certain(p["甲"], p["乙"])]
    print(f"   **机械上确定（去后缀后词干相同）：{len(certain)} 对**")
    print(f"   需要人读的：{len(uncertain)} 对"
          + ("　★ 里面可能有**跨作品的真实重印**，方向不能靠干净度猜" if uncertain else ""))
    use = pairs if a.include_uncertain else certain
    if not use:
        print("→ 没有机械上确定的对；**全部需要人读，本工具不动它们**")
        for p in uncertain[:10]:
            print(f"      {p['重叠']:.2f}  {p['甲'][:42]:<44}{p['乙'][:42]}")
        return 0
    plan = decide(use, byname, ws)
    if not a.apply:
        print(f"\n（dry-run。加 --apply 才写台账。）将声明 {len(plan)} 条，前 6 条：")
        for s_, b_, w_ in plan[:6]:
            print(f"   {s_[:44]:<46}→ {b_[:44]}")
        if uncertain and not a.include_uncertain:
            print(f"\n★ 另有 {len(uncertain)} 对**不会被写**，前 6 条（请人读）：")
            for p in uncertain[:6]:
                print(f"   {p['重叠']:.2f}  {p['甲'][:42]:<44}{p['乙'][:42]}")
        return 0

    add: dict[str, set[str]] = collections.defaultdict(set)
    why: dict[str, set[str]] = collections.defaultdict(set)
    missing = 0
    for s, b, w in plan:
        rec = byname.get(b)
        if not rec:
            missing += 1
            continue
        add[s].add(rec["source_id"])
        why[s].add(w)
    if missing:
        print(f"★ {missing} 条的基准件在台账里找不到，**跳过而不是猜**")
    n = 0
    for r in rows:
        nm = pathlib.PurePath(r.get("local_path") or "").name
        if nm in add:
            r["derived_from"] = sorted(set(r.get("derived_from") or []) | add[nm])
            r["★ derived_from 口径"] = (
                "／".join(sorted(why[nm])) +
                "。★ 本字段在此表示「**与所指来源实为同一部作品**」，不必是字面转录派生——"
                "`check_source_dedup` 问的就是「来源计数里有几份其实是同一部作品」。"
                "★★ **逐边声明，不按连通分量**：合集会把它重印的每一篇连成巨簇，"
                "按簇指基准件等于宣称两篇毫不相干的东西互相派生。")
            n += 1
    led.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")
    after = run_checker(ws)
    left = len(after["**未声明的重复对**"])
    ok = (after["distinct_works"] == before["distinct_works"]
          and after["inflation"] == before["inflation"])
    print(f"\n→ 写了 {n} 份来源｜未声明 {len(pairs)} → **{left}**｜"
          f"已声明 {after['已声明的重复对数']}")
    if left and not a.include_uncertain:
        print(f"★ 剩下的 {left} 对**是有意留着的**——它们需要人读，不是漏了。")
    print(f"→ 去重后作品 {before['distinct_works']} → {after['distinct_works']}｜"
          f"膨胀 {before['inflation']} → {after['inflation']}  "
          f"{'✓ 未变（应该如此）' if ok else '✗ **变了——出 bug 了**'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
