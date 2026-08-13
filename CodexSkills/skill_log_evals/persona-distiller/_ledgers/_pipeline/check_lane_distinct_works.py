#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_lane_distinct_works.py —— **一条道由几部作品撑着**（不是由几行台账撑着）

## 抓到它的那一次

2026-08-13，Churchill #191。分道现算 **3 条道**，`quick` 的 `min_lanes` 正好是 3
——**压线**。压线那一道是 `timeline`，2 份源：

    My early life a Roving Commission        src-0db9f607011e  raw/dli.ministry.17592.txt
    My early life; a roving commission       src-8ed06251e9a7  raw/myearlyliferovin0000chur_b7k8.txt

**同一部书的两个印本。** 而且不是我看题名猜的——流水线**自己的去重实测**
（`raw/_dedup.json`，min-hash Jaccard 阈值 0.55）把这两份归成了**该人物唯一的一个重复簇**。

⇒ 那条道的独立作品数是 **1**。`min_lanes 3` 是**一部作品数了两遍**换来的。

## 为什么 `check_paper_lanes` 抓不到

它判的是「**该道的支撑全部来自「一条同时挂多道」的源**」——
Churchill 这两份**都只挂 timeline**，独占，所以在它眼里这道结结实实。
**两件判据看的是同一批源，而口径不同**：它数「有没有专属的源」，本件数「有几部作品」。

## 判据

    某道 L 是「**一部作品撑起的道**」 ⟺ L 上的源 ≥2 行，而它们**去重后同属一部作品**

- 只用**实测**的重复簇（`raw/_dedup.json` 的 `重复簇`），**不按题名/年份推断**。
  书目代理顶替实测已经错过一次（「同年才算同一部作品」）。
- 没有 `_dedup.json` 的工作区 → **「未检查」，不是通过**。老工作区没跑过去重。
- 本件**不改 `min_lanes`**，只报「你这几道里有几道是一部作品撑的、去掉后还剩几道」。

## 用法

    python3 check_lane_distinct_works.py
    python3 check_lane_distinct_works.py --self-test

退出码：0＝没有空心道，或有但去掉后仍够门；1＝有人去掉空心道就够不着门
"""
import argparse
import collections
import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"
PROFILES = {"quick": {"min_sources": 8, "min_lanes": 3, "min_primary_ratio": 0.40},
            "standard": {"min_sources": 24, "min_lanes": 6, "min_primary_ratio": 0.50},
            "deep": {"min_sources": 45, "min_lanes": 6, "min_primary_ratio": 0.65}}


def work_groups(clusters):
    """重复簇 → {成员: 组号}。

    ★ 并查集会把有共同成员的簇串起来，**传递闭包曾把 32 份源串成一个分量**
      并报出「17/17 全塌缩」的假警。所以本件**只在簇内合并，不跨簇传递**：
      每个簇一个组号，同时出现在两个簇里的成员归**第一个**簇。
      合并得少 = 只会**少报**空心道，不会多报。
    """
    g, seen = {}, 0
    for cl in clusters:
        gid = f"w{seen}"
        seen += 1
        for m in cl:
            g.setdefault(m, gid)   # setdefault：跨簇不改归属
    return g


def _stem(row):
    """台账行 → 与重复簇里那个 id 对得上的键。"""
    for k in ("local_path", "original_name", "normalized_path"):
        v = row.get(k)
        if v:
            return pathlib.Path(str(v)).name.rsplit(".txt", 1)[0]
    return row.get("source_id") or ""


def analyse(rows, clusters):
    """→ {道: (源行数, 独立作品数)}。**纯函数**，自测不碰磁盘。"""
    g = work_groups(clusters)
    per = collections.defaultdict(list)
    for r in rows:
        for d in (r.get("dimensions") or []):
            per[d].append(r)
    out = {}
    for lane, rs in per.items():
        works = {g.get(_stem(r), f"solo:{_stem(r)}") for r in rs}
        out[lane] = (len(rs), len(works))
    return out


def profile_of(rows):
    lanes = len({d for r in rows for d in (r.get("dimensions") or [])})
    p1 = sum(1 for r in rows if r.get("tier") == "P1")
    n = len(rows)
    if n >= 45 and lanes >= 6 and n and p1 / n >= 0.65:
        return "deep"
    if n >= 24 and lanes >= 6 and n and p1 / n >= 0.50:
        return "standard"
    return "quick"


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    R = lambda p, dims: {"local_path": f"raw/{p}.txt", "dimensions": dims, "tier": "P1"}
    # ★ 正例：Churchill 真形状——timeline 两份是同一部书的两个印本
    rows = ([R(f"w{i}", ["writings"]) for i in range(13)]
            + [R(f"e{i}", ["external"]) for i in range(4)]
            + [R("dli.ministry.17592", ["timeline"]),
               R("myearlyliferovin0000chur_b7k8", ["timeline"])])
    a = analyse(rows, [["dli.ministry.17592", "myearlyliferovin0000chur_b7k8"]])
    chk(f"★ Churchill 真形状：timeline 2 行 → **独立作品 1**（实得 {a['timeline']}）",
        a["timeline"] == (2, 1))
    chk("★ 同时 writings 13 行仍算 13 部（没被误合）", a["writings"] == (13, 13))
    chk("★★ 去掉空心道只剩 2 道 < quick 门 3",
        len([l for l, (n, w) in a.items() if w >= 2]) == 2)
    # ★ 反例一：两份**不是**同一部书（没进任何重复簇）⇒ 这道是实的
    a2 = analyse(rows, [])
    chk("★ 反例：去重实测没归并 ⇒ timeline 算 2 部，道是实的", a2["timeline"] == (2, 2))
    # ★ 反例二：一份独苗的道——本件**不该**报它（那是别人的射程：min_sources）
    a3 = analyse([R("x", ["decisions"])], [])
    chk("★ 反例：只有 1 行的道不归本件报（源行数就是 1，无「数了两遍」可言）",
        a3["decisions"] == (1, 1))
    # ★★ 不跨簇传递：两个簇共用一个成员，**不许**并成一个大组
    g = work_groups([["a", "b"], ["b", "c"]])
    chk("★★ 两簇共用成员时不做传递闭包（曾把 32 份串成一个分量报出假警）",
        g["a"] == g["b"] and g["c"] != g["a"])
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    checked = unchecked = 0
    bad = []
    print(f"{'工作区':26s} {'档':9s} {'道':>3s} {'空心道':>5s} {'去掉后':>5s} {'门':>3s}  明细")
    for d in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
        ws = pathlib.Path(d)
        led, dj = ws / "evidence/source-ledger.jsonl", ws / "raw/_dedup.json"
        if not led.is_file():
            continue
        rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
        tr = [r for r in rows if r.get("split") == "train"]
        if not tr:
            continue
        if not dj.is_file():
            unchecked += 1
            continue
        checked += 1
        clusters = json.loads(dj.read_text(encoding="utf-8")).get("重复簇") or []
        res = analyse(tr, clusters)
        prof = profile_of(tr)
        gate = PROFILES[prof]["min_lanes"]
        hollow = {l: v for l, v in res.items() if v[0] >= 2 and v[1] == 1}
        left = len([l for l, (n, w) in res.items() if w >= 2 or n == 1])
        # ★ 只有 1 行的道不由本件判（那是 min_sources 的事），故仍计入 left
        flag = left < gate
        if hollow:
            det = "；".join(f"{l} {n} 行→**{w} 部**" for l, (n, w) in hollow.items())
            print(f"{ws.name:26s} {prof:9s} {len(res):>3d} {len(hollow):>5d} "
                  f"{left:>5d} {gate:>3d}  {det}{'  ★★ **够不着门**' if flag else ''}")
            if flag:
                bad.append((ws.name, prof, len(res), left, gate, det))

    print(f"\n扫过 **{checked} 个**工作区（有实测去重的）；"
          f"**{unchecked} 个未检查**——没有 `raw/_dedup.json`，**不是通过**")
    if not bad:
        print("✓ 没有「去掉空心道就够不着门」的人")
        return 0
    print(f"\n✗ **{len(bad)} 人**去掉空心道就够不着门：")
    for n, p, l, left, g, det in bad:
        print(f"  · {n}：{p} 档要 {g} 道，现算 {l} 道，"
              f"**去掉空心道只剩 {left} 道**　（{det}）")
    print("\n★ 本件**不改 min_lanes**，也不自行改判——它只把「这道是一部作品撑的」摆出来。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
