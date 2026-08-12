#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探源结果 → 抓取清单的**筛选器**。只做机械筛，**每一条被丢掉的都要报数**。

用法：
    python3 curate_ia.py --tsv <probe 出的 tsv> --person <人物键> --out <ids.txt>

**五道筛，每道都报丢了多少（[[empty-default-swallows-unknown]]：不许静默丢）：**

① **访问受限**：`collection` 含 `inlibrary`／`printdisabled`／`lendinglibrary`
   ⇒ 丢。**这不是「筛掉噪声」，是本项目不绕访问控制。**
② **版次年 > 1930**：现代版本，PD 判定站不住（且多半同时受限）。
   ★ 年份取 `year` 字段；**该字段在 IA 上时而是原作年时而是版次年**
   （`_IA的date是原作年不是版次年-2026-08-11.md`），所以它**只用来丢，不用来留**——
   留下的仍要靠正文题名页复核。
③ **同名者排除**：按 `EXCLUDE[person]` 逐条匹配 creator 串。
   ★ 名单来自各人 `00-抓源前必读.md`，**不是我现编的**。
④ **目标不在 creator 里**：收紧检索式后仍会有漏网（creator 多值）。
⑤ **上限**：`--cap` 条为止，**按「目标是第一作者」优先，并在馆之间轮转取**。
   ★★ **轮转不是锦上添花，是硬需求**：按字母序取会让 Kant／Bismarck 一次取到
   30 卷同一批 `bsb`（巴伐利亚州立图书馆的同一套），于是
   ①`min_lanes` 是虚的（只有一条道）；②OCR 错误无从互校。
   Kant 的 `00-抓源前必读.md` 原话是「**有意跨馆取件，不要让 bsb 占到八成**」。
   被上限丢掉的条数单独报，**不许混进前四道**
   （[[samples-cannot-support-universal-claims]]）。

★ 退出码：0=有留存；2=参数错；3=**一条都没留下**。
"""
import argparse
import pathlib
import re
import sys

RESTRICTED = ("inlibrary", "printdisabled", "lendinglibrary")

# ★ 每一条都出自对应工作区的 00-抓源前必读.md / *-selected.json 的「必须逐份排除」
EXCLUDE = {
    "marshall": ["Marshall, John Marshall", "Harlan", "1818-1891", "1783-1841",
                 "1786-1880", "1756-1824", "1664-1732", "1845-1915", "fl. 1895",
                 "Marshall, John W", "Marshall, John G"],
    "lincoln": ["1744-1786", "Lincoln, Abe", "1907-2000"],
    "jefferson": ["Randolph", "Hogg", "Thomas Garland", "1847-1864", "1856-1932"],
    "bismarck": ["1897-1975", "Bismarck, Herbert", "1849-1904", "1901-1949"],
    "machiavelli": [],
    "rousseau": ["Rousseau, Jean-Baptiste", "Rousseau, Henri", "Rousseau, Th"],
    "kant": [],
    "pestalozzi": ["1674-1742"],
    # ★ Karl Friedrich Fröbel 的**姓名完整含目标全名**，收紧到全名也挡不住，
    #   只能按生卒年与「Karl」排（见 wip-frobel-181/02-探源分析 第二刀）
    "frobel": ["Karl Friedrich", "Fröbel, Karl", "Fröbel, Julius", "Guido von"],
    "comenius": ["Comenius, Bernhard"],
}
# 目标必须出现在 creator 里的**姓名词元**（同一个 creator 段里全部出现即命中）。
# ★★ 曾写成 `["Fröbel, Friedrich"]` 这种「姓, 名」定串，于是
#   `creator: Friedrich Fröbel`（**名在前、无逗号**）一律匹配不上。
#   实测代价：Fröbel 的德文原著 **《Die Menschenerziehung》(1863,
#   bub_gb_SMoJAQAAIAAJ) 被当成「目标不在 creator 里」丢掉**，
#   而他当时正差 1 份独立文献够 standard 门。
#   ⇒ 改为**词元匹配**：段里同时含「fröbel」与「friedrich」才算，顺序不论。
REQUIRE = {
    "marshall": [["marshall", "john", "1755-1835"]],
    "lincoln": [["lincoln", "abraham"]],
    "jefferson": [["jefferson", "thomas"]],
    "bismarck": [["bismarck"]],
    "machiavelli": [["machiavelli"]],
    "rousseau": [["rousseau", "jean"]],
    "kant": [["kant", "immanuel"]],
    "pestalozzi": [["pestalozzi"]],
    "frobel": [["fröbel", "friedrich"], ["froebel", "friedrich"], ["frobel", "friedrich"]],
    "comenius": [["comenius"], ["komensk"]],
}


def target_pos(creator: str, person: str) -> int:
    """目标在 creator 的第几段（0 起）；-1 = 不在。**按词元匹配，不认名序。**"""
    segs = [s.strip().lower() for s in creator.split(";")]
    for i, s in enumerate(segs):
        for toks in REQUIRE[person]:
            if all(tok in s for tok in toks):
                return i
    return -1


YEAR_RE = re.compile(r"^(\d{4})")
# 一个「馆／来源家族」的粗标记：先看 collection 里的可辨馆名，再退回 identifier 形态
LANE_HINTS = ("bsb", "cdl", "americana", "library_of_congress", "toronto", "robarts",
              "europeanlibraries", "wellcomelibrary", "digitallibraryindia",
              "jaigyan", "brynmawrcollege", "harvard", "getty", "biodiversity")


def family_of(ident: str, collection: str) -> str:
    """粗判来源家族。**只用于上限时的轮转，不用于任何判定。**"""
    c = collection.lower()
    for h in LANE_HINTS:
        if h in c:
            return h
    if ident.startswith("bim_"):
        return "bim"
    if ident.startswith("dli."):
        return "dli"
    if re.match(r"^\d{6,}bsb$", ident):
        return "bsb"
    return "其他"


def round_robin(rows: list, cap: int) -> tuple:
    """按家族轮转取满 cap；**同族内保序**。返回 (取中, 被上限截掉)。"""
    if len(rows) <= cap:
        return rows, []
    buckets: dict = {}
    for r in rows:
        buckets.setdefault(r[5], []).append(r)
    order = sorted(buckets, key=lambda k: (-len(buckets[k]), k))
    picked, i = [], 0
    while len(picked) < cap and any(buckets[k] for k in order):
        k = order[i % len(order)]
        if buckets[k]:
            picked.append(buckets[k].pop(0))
        i += 1
    rest = [r for k in order for r in buckets[k]]
    return picked, rest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--person", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap", type=int, default=30)
    ap.add_argument("--pd-cutoff", type=int, default=1930)
    a = ap.parse_args()
    if a.person not in EXCLUDE:
        print(f"未知人物键 {a.person}；已知：{sorted(EXCLUDE)}", file=sys.stderr)
        return 2

    lines = [l for l in pathlib.Path(a.tsv).read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    hdr = lines[0].split("\t")
    rows = [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]

    drop = {"访问受限": [], "版次年>%d" % a.pd_cutoff: [], "同名者": [], "目标不在creator": []}
    keep = []
    for r in rows:
        ident = r.get("identifier", "")
        coll = r.get("collection", "").lower()
        cre = r.get("creator", "")
        if any(x in coll for x in RESTRICTED):
            drop["访问受限"].append(ident); continue
        m = YEAR_RE.match(r.get("year", "") or "")
        if m and int(m.group(1)) > a.pd_cutoff:
            drop["版次年>%d" % a.pd_cutoff].append(ident); continue
        if any(x in cre for x in EXCLUDE[a.person]):
            drop["同名者"].append(ident); continue
        tp = target_pos(cre, a.person)
        if tp < 0:
            drop["目标不在creator"].append(ident); continue
        first = (tp == 0)   # 目标是不是第一作者（用于上限排序，不用于丢弃）
        keep.append((0 if first else 1, ident, r.get("year", "")[:4], cre[:70],
                     r.get("title", "")[:60], family_of(ident, r.get("collection", ""))))

    keep.sort()
    keep, capped = round_robin(keep, a.cap)

    total = len(rows)
    print(f"人物 {a.person}｜输入 {total} 条")
    for k, v in drop.items():
        print(f"  丢·{k:<14} {len(v):>4} 条" + (f"  例：{v[0]}" if v else ""))
    fams = {}
    for x in keep:
        fams[x[5]] = fams.get(x[5], 0) + 1
    print(f"  留                 {len(keep) + len(capped):>4} 条"
          f"（其中目标为第一作者 {sum(1 for x in keep + capped if x[0] == 0)}）")
    print("  取中的馆分布：" + "、".join(f"{k} {v}" for k, v in sorted(fams.items(), key=lambda kv: -kv[1])))
    if capped:
        print(f"  ⚠️ **上限 {a.cap} 截掉 {len(capped)} 条**——不是没有，是本轮不抓：")
        print("     " + "、".join(x[1] for x in capped[:8]) + ("…" if len(capped) > 8 else ""))
    if not keep:
        print("**一条都没留下** —— 检索式或排除名单有问题，不是「这个人没有语料」", file=sys.stderr)
        return 3

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(f"# {a.person}：探源 {total} 条 → 留 {len(keep)} 条（上限 {a.cap}，截掉 {len(capped)}）\n")
        f.write("# 丢：" + "；".join(f"{k} {len(v)}" for k, v in drop.items()) + "\n")
        for _, ident, y, cre, ti, fam in keep:
            f.write(f"{ident}\n")
    print(f"→ {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
