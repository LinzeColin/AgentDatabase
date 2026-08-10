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


# ★★★ 2026-08-10：`SUFFIX` 里有 `bsb`/`alt`/`bd\d`，**独独没有语种标记**。
#   于是 `canalisation-abfuhr-1869-de` ↔ `canalisation-abfuhr-1869-bsb`
#   （同一份德文报告的两个扫描来源，重叠 0.68）被判成「词干不同」，
#   Virchow 整个工作区因此报「机械上确定 **0 对**」，126 对全推给人读。
#
#   ★★ **但语种标记不能无条件剥**：`x-de` ↔ `x-en` 是原文与译本，**不是同一件的副本**。
#   （本项目已记过「判据的作品分组是语言盲的」这个坑。）
#   所以剥语种标记有一个前提：**台账说这两份是同一种语言**。
#   台账没写 language 的，就**不剥**——宁可漏报，不可错并。
LANG_SUFFIX = re.compile(r"[-_](?:de|en|fr|la|it|es|nl|ru|el)$", re.I)


def strip_lang(stem: str) -> str:
    prev = None
    while prev != stem:
        prev, stem = stem, LANG_SUFFIX.sub("", stem)
    return stem


def is_certain(a: str, b: str, lang_a: str | None = None, lang_b: str | None = None) -> bool:
    """去掉来源后缀之后词干相同 → **机械上确定是同一件的另一份副本**。

    ★ 语种标记只在**台账明写两侧同语种**时才一并剥掉；
      两侧语种不同、或有一侧没写，一律不剥（`x-de` vs `x-en` 必须判为不确定）。
    """
    sa, sb = pathlib.PurePath(a).stem, pathlib.PurePath(b).stem
    if sa == sb:
        return False
    if strip_suffix(sa) == strip_suffix(sb):
        return True
    if lang_a and lang_b and lang_a == lang_b:
        return strip_lang(strip_suffix(sa)) == strip_lang(strip_suffix(sb))
    return False


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
        # ★★★★★ 用 `--include-uncertain` 之前先读这一段。
        #   2026-08-10 我一度打算「把全库剩下的 1,300 对一次声明完」，
        #   理由是「重叠 ≥30% 的要么是同一版、要么是同一书的两个版次，
        #   `derived_from` 两种都成立」。**dry-run 当场推翻了它。**
        #
        #   ★★★★ **订正（同日晚些时候）**：我最初举的反例是 Bessemer 的
        #     `us9608` ↔ `us9618`，说「两件不同专利共享法律套语」——**那个判断是错的**。
        #     真因是 `#` 出处表头：那份文件 **34.4% 是表头**，里面还抄了一整块
        #     `AUTHORSHIP EVIDENCE (verbatim from the scan)` 的专利原文。
        #     `corpus_body` 补上剥这种表头之后，**Bessemer 未声明 1 → 0、Thomson 11 → 0**。
        #
        #   **结论仍然成立，但反例要换成这个真的**：
        #     Barton 的 `rc-peace-war-*` ↔ `rc-history-*` 跨族重叠 **最高 0.922**
        #     （高于族内最低的 0.800），而**两族的题名页印着不同的书名**——
        #     7 份全印 `The Red Cross In Peace and War`，另一族印
        #     `THE RED CROSS: A HISTORY OF THIS REMARKABLE INTERNATIONAL MOVEMENT…`。
        #     **那是同一作者把前一本大段重用进后一本**，不是同一部作品。
        #   ★★ 所以：**≥30% 不等于同一部作品**，本工具的保守默认是对的；
        #     `--include-uncertain` 只能在**逐对读过之后**用，不许拿来清红。
        #
        # ★★★★ 第三档：**方向判不出来。**
        #   旧版在这里按「正文干净度」猜（脏的指向干净的）——
        #   而 HANDOFF 自己写着「方向靠干净度猜必然出错」：
        #   Nightingale 465 对里 417 对落在这一档，其中有
        #   `royal-commission-report-1858` ↔ `mortality-british-army-1858`（0.44）
        #   这种**跨作品的真实重印**，谁派生自谁，干净度答不了。
        #
        #   改法：**两个方向都声明**，并写明「先后关系未判定」。
        #   这不是含糊其辞——本字段的口径是「**与所指来源实为同一部作品**」，
        #   而「是同一部作品」**本来就是对称的**。
        #   `check_source_dedup` 按**声明的连通分量**免报（第 194 行），互指同样连得上。
        #   ★ 猜一个方向写下去，是在断言一件我没有证据的事；
        #     两边都写，断言的只是我真的量到的那件事。
        w = (f"**同一部作品的另一份见证**（实测重叠 {p['重叠']:.2f}）。"
             f"★★ **先后关系未判定，所以两个方向都声明**——"
             f"本字段表示「与所指来源实为同一部作品」，这层关系是对称的。"
             f"（干净度 {cr(a):.3f} / {cr(b):.3f}，**没有拿它当方向依据**："
             f"实测过它会在跨作品的真实重印上判反。）")
        out.append((a, b, w))
        out.append((b, a, w))
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
    lang = {k: (v.get("language") or None) for k, v in byname.items()}
    _cert = lambda p: is_certain(p["甲"], p["乙"], lang.get(p["甲"]), lang.get(p["乙"]))
    certain = [p for p in pairs if _cert(p)]
    uncertain = [p for p in pairs if not _cert(p)]
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
    new_edges = 0   # ★ 真正新加进去的边；原本就声明过的**不算**
    for r in rows:
        nm = pathlib.PurePath(r.get("local_path") or "").name
        if nm in add:
            prev = set(r.get("derived_from") or [])
            merged = prev | add[nm]
            new_edges += len(merged - prev)
            r["derived_from"] = sorted(merged)
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
    print(f"\n→ 写了 {n} 份来源（**真新增 {new_edges} 条边**，其余原本就声明过）｜"
          f"未声明 {len(pairs)} → **{left}**｜已声明 {after['已声明的重复对数']}")
    # ★★★ 2026-08-10：我在 Virchow 上用临时脚本报了「声明 7 条」，而门一动没动——
    #   那个计数器数的是「**判定通过的对**」，不是「**写盘新增的边**」：3 对早就声明过、
    #   4 对落在被拒区间，**真新增 0**。所以 `真新增` 这个数**永远要打印**：
    #   记账只认它，不认「判定了几对」。
    #
    #   ★ 下面这条**是不变量断言，不是信号** —— 现在的 `decide()` 只在这一对**自身**
    #   两个成员之间选基准件，而这一对是判据报出来的「未声明」，
    #   所以 `n>0 而 new_edges==0` 走不到。**故意留着**：哪天 `decide()` 改成
    #   可以指向第三方基准件（合集代表件之类），这条就是唯一会喊的人。
    #   —— 打不红的分支不许当信号用，所以它只做断言、不做「★ 提示」。
    if n and new_edges == 0:
        print("✗ **不变量破了**：写了 {} 份来源却一条新边都没加——"
              "说明 `decide()` 指向了本来就连着的基准件。**这一轮不是进展。**".format(n),
              file=sys.stderr)
        return 1
    if left and not a.include_uncertain:
        print(f"★ 剩下的 {left} 对**是有意留着的**——它们需要人读，不是漏了。")
    print(f"→ 去重后作品 {before['distinct_works']} → {after['distinct_works']}｜"
          f"膨胀 {before['inflation']} → {after['inflation']}  "
          f"{'✓ 未变（应该如此）' if ok else '✗ **变了——出 bug 了**'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
