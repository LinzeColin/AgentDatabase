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


def norm_title(s: str) -> str:
    """题名归一：小写、去标点、折叠空白。**只用于筛嫌疑，不用于判定。**"""
    import re as _re
    s = _re.sub(r"[^a-z0-9 ]+", " ", str(s).lower())
    return " ".join(s.split())


def _title_is_filename(row) -> bool:
    """title 栏是不是被填成了文件名。**筛子读的字段先自检，再报数。**"""
    import re as _re
    t = str(row.get("title") or "")
    stem = pathlib.Path(str(row.get("local_path") or "")).name
    return (not t) or t == stem or t == stem.rsplit(".txt", 1)[0] \
        or bool(_re.fullmatch(r"[\w.\-]+", t))     # 无空格的连写串


def suspects() -> int:
    """量不了的那些人：按题名筛出**待复核清单**。

    ★★ **这不是判定。** 本项目吃过亏：用书目代理（「同年才算同一部作品」）
      顶替直接量重叠，结论是错的。所以这里只回答一个问题——
      **「等语料能取到的时候，先复核谁」**，输出是清单，不是红绿。
    ★ 之所以只能这样：这 14 个人**既没有 `raw/_dedup.json`、本地也没有 `raw/*.txt`**
      （语料按 Owner 裁定不进 git），**本机跑不出 min-hash**。
    """
    print("★★ **以下是待复核清单，不是判定**——按题名筛的嫌疑，"
          "真判定要等语料能取到时跑 min-hash。\n")
    n_ws = n_hit = 0
    blind = []          # ★ 题名栏不可用 ⇒ 连嫌疑都筛不出来的工作区
    for d in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
        ws = pathlib.Path(d)
        led = ws / "evidence/source-ledger.jsonl"
        if not led.is_file() or (ws / "raw/_dedup.json").is_file():
            continue                       # 有实测的走 main()，不进本清单
        rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
        tr = [r for r in rows if r.get("split") == "train"]
        if not tr:
            continue
        n_ws += 1
        # ★★ **先问筛子读的那个字段有没有内容。**
        #   实测这批工作区 92.5% 的 `title` 就是文件名（`0001-conv-1907-vxxvi.txt`），
        #   于是「题名归一后相同」永远不成立，**本函数会稳定地报 0 个嫌疑**——
        #   而那个 0 是**筛子瞎了**，不是语料干净。空结果不许当成通过。
        fnish = sum(1 for r in tr if _title_is_filename(r))
        if tr and fnish / len(tr) >= 0.5:
            blind.append((ws.name, fnish, len(tr)))
            continue
        per = collections.defaultdict(list)
        for r in tr:
            for dim in (r.get("dimensions") or []):
                per[dim].append(r)
        lanes = len(per)
        prof = profile_of(tr)
        gate = PROFILES[prof]["min_lanes"]
        sus = {l: rs for l, rs in per.items()
               if len(rs) >= 2 and len({norm_title(r.get("title")) for r in rs}) == 1}
        if not sus:
            continue
        n_hit += 1
        left = lanes - len(sus)
        mark = "  ★★ **若坐实就够不着门**" if left < gate else ""
        print(f"  {ws.name}（{prof}，{lanes} 道，门 {gate}）{mark}")
        for l, rs in sus.items():
            print(f"      {l}：{len(rs)} 行，题名归一后**同一个**"
                  f"　「{(rs[0].get('title') or '')[:58]}」")
    print(f"\n扫过 **{n_ws} 个**没有实测去重的工作区："
          f"**{len(blind)} 个连嫌疑都筛不出**（题名栏是文件名），"
          f"其余 {n_ws - len(blind)} 个里 **{n_hit} 个**有嫌疑。")
    if blind:
        print("\n★★ **下面这些是「筛不了」，不是「干净」**——"
              "`title` 栏填的是文件名，题名比对无从谈起：")
        for n, f, a in blind:
            print(f"    {n:30s} {f}/{a} 行的 title 是文件名（{f / a:.0%}）")
        print("  ⇒ 要么补真题名（`_fetch-manifest.json` 的 `ia_title` 有），"
              "要么等语料可取时直接跑 min-hash。**两条都没做之前，它们是「未检查」。**")
    print("\n★ 处置：等语料可取时对这些人跑 `_dedup.json`，再用本文件的 main() 判。"
          "**在那之前，这些人的 `min_lanes` 属于「未检查」，不是「通过」。**")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--suspects", action="store_true",
                    help="量不了的那些人：按题名筛待复核清单（**不是判定**）")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.suspects:
        return suspects()

    checked = unchecked = 0
    bad = []
    zero = []      # ★ 跑过去重而 0 个簇的（见下面的注释）
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
        # ★★★ 2026-08-14 实测新增的第三档：**这份 `_dedup.json` 自己带着两个口径，
        #   而本件只读了其中较松的那个。** 文件里同时记着：
        #     `独立文献数上界`   —— min-hash（阈值 0.55）归并后的数
        #     `按题名归并的独立作品数` —— 另一把尺子
        #   Michelangelo #185 实测：文件数 56，min-hash 上界 **54**（只塌缩 2），
        #   按题名归并 **51**（塌缩 5）。**两个口径差 3。**
        #   而他台账里 1875 年 Milanesi 书信集占了 **4 个 source_id**
        #   （`leletteredimiche00mich`／`laletteredimich00milagoog`／
        #    `laletteredimich00buongoog`／`buonarroti_le_lettere_…`），
        #   逐对 8-gram Jaccard 只有 0.1510–0.2412 ⇒ **min-hash 一个都没聚起来**，
        #   而 min-hash 真正聚出的 2 个簇是别的东西（英译对、Fisher 两册）。
        #   拿一句本人原文当探针（`non è bene spronar quello cavallo che corre quanto e' può`）
        #   四份全中——**探针逐字，不受 OCR 讹形与语种影响；重叠分数两样都受。**
        #   ⇒ 两个口径对不上就单列一档：本件的结论在这些人身上**是下界，不是定论**。
        n_files = json.loads(dj.read_text(encoding="utf-8")).get("文件数")
        _d = json.loads(dj.read_text(encoding="utf-8"))
        mh, bt = _d.get("独立文献数上界"), _d.get("按题名归并的独立作品数")
        if isinstance(n_files, int) and isinstance(mh, int) and isinstance(bt, int) and mh != bt:
            zero.append((ws.name, n_files, n_files - mh, n_files - bt))
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
    if zero:
        print(f"\n！ 其中 **{len(zero)} 个的两把尺子对不上** —— `_dedup.json` 里 min-hash 与"
              "按题名归并给出的塌缩数不同，**本件只读 min-hash 那个**，所以这些人的结论是"
              "**下界不是定论**：\n"
              "     Michelangelo #185 实测：56 份，min-hash 只塌缩 2、按题名塌缩 5；"
              "而 1875 Milanesi 书信集在他台账里占 4 个 `source_id`（逐对 Jaccard 0.1510–0.2412），"
              "min-hash 一个都没聚。\n"
              "     ⇒ 这些人要**拿一句本人原文当探针**逐份搜，才判得了「是不是同一部书」。")
        for nm, nf, a, b in sorted(zero):
            print(f"     {nm:30s} {nf:>3d} 份　min-hash 塌缩 {a}　按题名塌缩 {b}")
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
