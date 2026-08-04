#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**抓源抓到一半，离语料三道门还有多远**——在继续抓之前先看一眼。

## 撞出它的那一次

Benardos #128 抓到 17 份时我手算了一遍，才发现方向错了：

| | 实测 | quick 门 |
|---|---|---|
| 来源数 | 17 | ≥8 ✓ |
| **一手占比** | **6/17 = 35.3%** | **≥0.40 ✗** |
| **道数** | **2**（writings + external） | **≥3 ✗** |

抓源方当时正在一份接一份地收《Электричество》里「提到他」的条目——
**每多收一份，一手占比就掉一点，而道数一点不涨。**
这不是它的错：**没有人告诉它门在哪，它也看不到自己离门有多远。**

★ 本会话我手算了两次同样的东西。**手算两次就该落成工具**——
不是因为省事，是因为**手算的结果不进任何记录，下一个人还得再算一遍。**

## 它报什么

读**暂存目录**（`raw/src-*/` ＋ 可选的 `raw/_ids.txt`），对着
`PROFILE_THRESHOLDS` 报三项距离：来源数、道数、一手占比。

## ★ 它不做什么

- **不猜分档。** 没有 `_ids.txt` 就明说「分档与道**未知**」，
  **不拿目录名去推**（`src-us-patent-…` 看着像一手，但那是命名巧合不是证据）。
- **不拦。** 抓源阶段没有门；这只是一面镜子。
- **不建议抓什么。** 那要看人物，不是正则能定的。
"""
import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from common import PROFILE_THRESHOLDS
except Exception:                                            # noqa: BLE001
    PROFILE_THRESHOLDS = {}

PRIMARY = {"P1", "P2"}          # 与 build_source_ledger 的一手口径同源
_TIER_RE = re.compile(r"^(P1|P2|S1|S2|U)$")


def read_ids(raw: pathlib.Path) -> tuple:
    """→ (rows, note)。读不到就返回 ([], 原因) ——**不猜**。"""
    f = raw / "_ids.txt"
    if not f.is_file():
        return [], "`_ids.txt` 不在——**分档与道未知（不是「没有一手」）**"
    rows, bad = [], 0
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        c = line.split("\t")
        tier = next((x for x in c if _TIER_RE.match(x.strip())), None)
        lane = None
        for x in c:
            m = re.search(r"lane=([a-z]+)", x)
            if m:
                lane = m.group(1)
                break
        if tier is None and lane is None:
            bad += 1
            continue
        rows.append({"tier": tier, "lane": lane})
    note = f"读到 {len(rows)} 行" + (f"，**{bad} 行既无分档也无 lane，未计入**" if bad else "")
    return rows, note


def scan(raw: pathlib.Path, profile: str) -> dict:
    dirs = sorted(d for d in raw.glob("src-*") if d.is_dir())
    with_txt = [d for d in dirs if any(d.glob("*.txt"))]
    rows, note = read_ids(raw)
    th = PROFILE_THRESHOLDS.get(profile, {})

    out = {
        "暂存目录": str(raw),
        "profile": profile,
        "来源目录数": len(dirs),
        "其中已有 .txt 的": len(with_txt),
        "_ids.txt": note,
    }

    need_src = th.get("min_sources")
    if need_src is not None:
        out["① 来源数"] = (f"{len(dirs)} / 需 {need_src} → "
                          + ("✓ 已过" if len(dirs) >= need_src else f"**还差 {need_src - len(dirs)}**"))

    if not rows:
        out["② 道数"] = "**未知**（没有 `_ids.txt`）"
        out["③ 一手占比"] = "**未知**（没有 `_ids.txt`）"
        out["★ 口径"] = ("**没有台账就不报这两项，也不拿目录名去推。**"
                         "`src-us-patent-…` 看着像一手，但那是命名巧合不是证据。")
        return out

    lanes = {r["lane"] for r in rows if r["lane"]}
    need_lane = th.get("min_lanes")
    if need_lane is not None:
        out["② 道数"] = (f"{len(lanes)} {sorted(lanes)} / 需 {need_lane} → "
                        + ("✓ 已过" if len(lanes) >= need_lane
                           else f"**还差 {need_lane - len(lanes)} 道**"))

    tiered = [r for r in rows if r["tier"]]
    n_pri = sum(1 for r in tiered if r["tier"] in PRIMARY)
    need_ratio = th.get("min_primary_ratio")
    if tiered and need_ratio is not None:
        ratio = n_pri / len(tiered)
        out["③ 一手占比"] = (f"{n_pri}/{len(tiered)} = {ratio:.1%} / 需 {need_ratio:.0%} → "
                            + ("✓ 已过" if ratio >= need_ratio else "**没过**"))
        if ratio < need_ratio:
            # 还要再补几份纯一手才够——解 (n_pri+k)/(len+k) >= need
            k = 0
            while (n_pri + k) / (len(tiered) + k) < need_ratio and k < 10000:
                k += 1
            out["★★ 若只靠加一手来补"] = (f"**还需再收 {k} 份一手**（在现有基础上），"
                                          f"或**少收三方**——每多收一份三方，这个数还会掉。")
    elif not tiered:
        out["③ 一手占比"] = "**未知**：台账里一行分档都没有"

    return out


def self_test() -> int:
    import tempfile
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    with tempfile.TemporaryDirectory() as td:
        raw = pathlib.Path(td) / "raw"
        for i in range(17):
            (raw / f"src-{i:02d}").mkdir(parents=True)
            (raw / f"src-{i:02d}" / "a.txt").write_text("x" * 600, encoding="utf-8")

        print("── ★★★ 反向对照①：**没有 _ids.txt 时不许猜分档** ──")
        r = scan(raw, "quick")
        chk(f"道数报未知：{r['② 道数']}", "未知" in r["② 道数"])
        chk(f"一手占比报未知：{r['③ 一手占比']}", "未知" in r["③ 一手占比"])
        chk("明说不拿目录名去推", "命名巧合不是证据" in r.get("★ 口径", ""))

        print("\n── ★★ 反向对照②：Benardos 的真实形状（6 一手 / 11 三方，2 道） ──")
        lines = []
        for i in range(6):
            lines.append(f"p{i}\t\t\t1888\t\ten\tP1\tHIS-OWN\tlane=writings. 专利")
        for i in range(11):
            lines.append(f"s{i}\t\t\t1892\t\tru\tS2\tTHIRD-PARTY\tlane=external. 期刊提到他")
        (raw / "_ids.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        r = scan(raw, "quick")
        chk(f"来源数已过：{r['① 来源数']}", "✓" in r["① 来源数"])
        chk(f"道数没过（2 < 3）：{r['② 道数']}", "还差 1 道" in r["② 道数"])
        chk(f"一手占比没过（35.3%）：{r['③ 一手占比']}", "35.3%" in r["③ 一手占比"] and "没过" in r["③ 一手占比"])

        print("\n── ★★ 反向对照③：**补多少份一手才够**要算对 ──")
        # 6/17=0.353，需 0.40：(6+k)/(17+k) >= 0.40 → k >= 1.33 → k=2
        chk(f"报出 {r.get('★★ 若只靠加一手来补','')}", "还需再收 2 份一手" in r.get("★★ 若只靠加一手来补", ""))

        print("\n── ★ 反向对照④：够了就不该报「还差」 ──")
        lines = [f"p{i}\t\t\t1888\t\ten\tP1\tHIS-OWN\tlane=writings. x" for i in range(8)]
        lines += [f"c{i}\t\t\t1888\t\ten\tP1\tHIS-OWN\tlane=conversations. x" for i in range(2)]
        lines += [f"s{i}\t\t\t1888\t\ten\tS2\tTHIRD-PARTY\tlane=external. x" for i in range(2)]
        (raw / "_ids.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        r2 = scan(raw, "quick")
        chk(f"三项全过：{r2['② 道数']} | {r2['③ 一手占比']}",
            "✓" in r2["② 道数"] and "✓" in r2["③ 一手占比"] and "★★ 若只靠加一手来补" not in r2)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="?", help="暂存目录（含 src-*/ 与可选的 _ids.txt）")
    ap.add_argument("--profile", default="quick", choices=["quick", "standard", "deep"])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.raw:
        ap.error("要么 --self-test，要么给暂存目录")
    p = pathlib.Path(a.raw)
    if not p.is_dir():
        print(json.dumps({"状态": f"**未核（不是通过）**：{p} 不是目录"}, ensure_ascii=False))
        return 3
    print(json.dumps(scan(p, a.profile), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
