#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这批语料的一手上限够得着哪一档**——在抓 53 份之前先数一遍。

## 为什么有这件

`check_gate_reachability` 问的是「门槛是不是设在**评委**的天花板之上」。
本件问的是另一半：「门槛是不是设在**语料**的天花板之上」。
两件都是「先问够不够得着，再花力气」，但看的是完全不同的两个上限。

## 实测（#115 Nikolai Slavyanov，2026-08-04）

抓源跑了 65 分钟，落 **53 份**（deep 的 `min_sources` 是 45——**份数是够的**）。
然后才发现：

| | 实测 | deep 门槛 | |
|---|---:|---:|---|
| 份数 | 53 | 45 | ✅ |
| 一手占比 | **0.1509**（8/53） | 0.65 | ❌ **差 4.3 倍** |
| 六条道 | **5**（`conversations` 一封信都没有） | 6 | ❌ |

**他传世著述本来就少**：一本书、两份俄国特权、一次有记录的讲演、一件美国专利
——**八份，就是全部**。这个数不会因为再抓一天而变大。

## ★ 关键换算：deep 要的不是 45 份源，是 **30 份一手**

`primary_ratio` 是**比值**，而 `min_sources` 给分母定了下限。
两条门联立之后，真正的约束是一个绝对数：

    需要的一手份数 = ceil(min_sources × min_primary_ratio)

    quick    ceil( 8 × 0.40) =  4
    standard ceil(24 × 0.50) = 12
    deep     ceil(45 × 0.65) = **30**

**「45 份」这个数一直挂在嘴边，「30 份一手」这个数从来没被说出来过。**
Slavyanov 有 8 份。Henderson #113 全部只有 2 份，Peplau #114 只有 3 份。
**三个人排期之前都没有人数过这一下。**

## ★★ 它同时要拦住一件我差点做的事：缩分母

比值门有一个人人都想得到的过法：**别抬分子，去砍分母。**

Slavyanov 若只吃 8 份 P1 + 4 份 S1：

    12 份 ≥ quick 的 8 份 ✅　　占比 8/12 = 0.667 ≥ 0.40 ✅　　道数 5 ≥ 3 ✅
    **quick 当场变绿——而我手上那 41 份真材料被丢掉了。**

产物不会因此更贴近他，只会更空。**这不是达标，这是缩分母。**
所以本件在报「够得着」时必须分两种说法，**不许合并**：

- **吃掉全部已取到的材料就够得着** → 真的够得着
- **只有丢掉 N 份才够得着** → **报出来，并且说明它是缩分母**

（判据不替人决定丢不丢——策展与凑数在门这一侧长得一模一样。
　**它的职责是让这个选择在报告里现形，而不是悄悄发生。**）

## 它判不了什么

- **判不了「再抓能不能抓到」。** 它只算手上这批的上限。
  一手可能还有没找到的；空着的道**也可能**只是没找着。
- **判不了分档对不对。** 台账里写 P1 它就当 P1。分错档的输入 → 分错档的结论。
- **★ 台账格式不统一，解析不出分档时必须报「未检查」，绝不许报 0。**
  实测四个人四种格式：#115／#111 是 9 列制表符（分档在第 7 列），
  #107 是竖线分隔且**根本没有分档列**，#104 只有 `id|道|年|题`。
  **一个把「没有分档列」读成「零份一手」的判据，会给每个老台账伪造一条硬失败。**
"""
import argparse
import json
import math
import pathlib
import re
import sys

# 与 scripts/common.py 的 PROFILE_THRESHOLDS 同源；此处只取本件用得到的三项。
PROFILES = {
    "quick":    {"min_sources": 8,  "min_lanes": 3, "min_primary_ratio": 0.40},
    "standard": {"min_sources": 24, "min_lanes": 6, "min_primary_ratio": 0.50},
    "deep":     {"min_sources": 45, "min_lanes": 6, "min_primary_ratio": 0.65},
}
PRIMARY_TIERS = {"P1", "P2"}
TIER_RE = re.compile(r"^(P1|P2|S1|S2|U)$")
LANE_RE = re.compile(r"lane=([a-z]+)")
LANES = ("writings", "expression", "conversations", "decisions", "timeline", "external")


def required_primary(prof):
    """**这一档到底要几份一手**——两条门联立之后的那个绝对数。"""
    p = PROFILES[prof]
    return math.ceil(p["min_sources"] * p["min_primary_ratio"] - 1e-9)


def verdict(primary, total, lanes, prof):
    """→ (够得着吗, 要不要缩分母, [说不通的地方])。

    吃全部材料时的占比是 primary/total；
    **上限**占比是 primary/max(min_sources, primary)——分母压到门槛线为止。
    """
    p = PROFILES[prof]
    need = required_primary(prof)
    bad = []

    if total < p["min_sources"]:
        bad.append(f"份数 {total} < {p['min_sources']}——**材料本身就不够**")
    if lanes < p["min_lanes"]:
        bad.append(f"六条道只占 {lanes} < {p['min_lanes']}"
                   f"——**空着的道抓再多别的也补不上**")

    ceiling = primary / max(p["min_sources"], primary) if primary else 0.0
    if ceiling < p["min_primary_ratio"]:
        bad.append(f"一手 {primary} 份 < **{need} 份**"
                   f"（占比上限 {ceiling:.4f} < {p['min_primary_ratio']:.2f}）")

    if bad:
        return False, False, bad

    as_is = primary / total if total else 0.0
    shrink = as_is < p["min_primary_ratio"]
    return True, shrink, []


def parse_ledger(path):
    """→ (rows, note)。**解析不出分档时 rows 为 None**，note 说清为什么。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" not in line:
            continue
        cols = line.split("\t")
        tier = next((c.strip() for c in cols if TIER_RE.match(c.strip())), None)
        lane = LANE_RE.search(line)
        rows.append((tier, lane.group(1) if lane else None))

    if not rows:
        return None, "台账里没有制表符分隔的数据行——**这份台账不是本件认得的格式**"
    if not any(t for t, _ in rows):
        return None, (f"{len(rows)} 行里一行都没有分档列（P1/P2/S1/S2/U）"
                      "——**判不了一手占比**")
    return rows, ""


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★ 换算：两条门联立之后要几份一手 ──")
    got = {p: required_primary(p) for p in PROFILES}
    print(f"    {got}")
    chk("quick 4 / standard 12 / **deep 30**",
        got == {"quick": 4, "standard": 12, "deep": 30})
    chk("30/45 = 0.6667 ≥ 0.65 而 29/45 = 0.6444 < 0.65（边界正好卡在 30）",
        30 / 45 >= 0.65 > 29 / 45)

    print("── ★ 正向：#115 Slavyanov 的真实形状（8 一手 / 53 份 / 5 道）──")
    ok, shrink, bad = verdict(8, 53, 5, "deep")
    print(f"    deep     → {bad}")
    chk("deep 够不着，且两条理由都点出来（一手不足 + 缺一条道）",
        ok is False and len(bad) == 2
        and any("30 份" in b for b in bad) and any("道" in b for b in bad))
    ok, shrink, bad = verdict(8, 53, 5, "standard")
    chk("standard 也够不着（要 12 份一手，只有 8）",
        ok is False and any("12 份" in b for b in bad))

    print("── ★★ 反向对照 ①：**quick 够得着，但只有靠缩分母** ──")
    ok, shrink, bad = verdict(8, 53, 5, "quick")
    print(f"    quick 吃全部 8/53 = {8/53:.4f} < 0.40；上限 8/8 = 1.0000")
    chk("必须同时报「够得着」**和**「要缩分母」，不许只报前一半",
        ok is True and shrink is True and not bad)

    print("── ★★ 反向对照 ②：**吃全部就够得着的，不许被说成缩分母** ──")
    ok, shrink, bad = verdict(30, 45, 6, "deep")
    print(f"    30/45 = {30/45:.4f} ≥ 0.65")
    chk("刚好达标 → 够得着且**不**需要缩分母", ok is True and shrink is False)

    print("── 反向对照 ③：份数不够时不许说成一手不够 ──")
    ok, shrink, bad = verdict(6, 6, 6, "deep")
    chk("6 份 → 报「材料本身就不够」", any("材料本身就不够" in b for b in bad))

    print("── ★ 反向对照 ④：**一手再多也补不上空着的道** ──")
    ok, shrink, bad = verdict(45, 45, 5, "deep")
    chk("45 份全是一手、占比 1.0，仍因 5 道而不过",
        ok is False and len(bad) == 1 and "道" in bad[0])

    print("── 反向对照 ⑤：一手为 0 不许因除零而崩 ──")
    ok, shrink, bad = verdict(0, 50, 6, "deep")
    chk("0 份一手 → 够不着，且只因一手这一条", ok is False and len(bad) == 1)

    print("── ★★ 反向对照 ⑥：**没有分档列的台账必须报「判不了」，不许报 0** ──")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        # #107 Koch 的真实形状：竖线分隔，没有分档列
        p = pathlib.Path(td) / "koch.txt"
        p.write_text("# 标识符|类别|年份|标题\na|writings|1876|x\nb|external|1882|y\n",
                     encoding="utf-8")
        rows, note = parse_ledger(p)
        print(f"    → {note}")
        chk("竖线台账 → rows 为 None（不是空列表，更不是 0 份一手）", rows is None)

        # 有制表符但分档列缺失
        p2 = pathlib.Path(td) / "notier.txt"
        p2.write_text("a\thttp://x\t题\t1890\t位置\tru\tlane=writings\n", encoding="utf-8")
        rows, note = parse_ledger(p2)
        chk("有制表符但无 P1/S1 列 → 同样报「判不了」", rows is None)

        # #115 的真实形状，认得出来
        p3 = pathlib.Path(td) / "ok.txt"
        p3.write_text("# 注释\n"
                      "a\thttp://x\t题\t1892\t位置\tru\tP1\tHIS-OWN\tlane=writings. E=1\n"
                      "b\thttp://y\t题\t1914\t位置\ten\tS2\tTHIRD-PARTY\tlane=external. E=2\n",
                      encoding="utf-8")
        rows, note = parse_ledger(p3)
        chk("9 列制表符台账 → 2 行，分档与道都解析出来",
            rows is not None and len(rows) == 2
            and rows[0] == ("P1", "writings") and rows[1] == ("S2", "external"))

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=pathlib.Path, help="raw/_ids.txt")
    ap.add_argument("--primary", type=int, help="一手（P1+P2）份数——不给台账时直接给数")
    ap.add_argument("--total", type=int)
    ap.add_argument("--lanes", type=int, help="有材料的道数（0–6）")
    ap.add_argument("--profile", default="deep", choices=sorted(PROFILES))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()

    if a.ledger is not None:
        if not a.ledger.is_file():
            print(f"✗ **{a.ledger} 不在——本次未检查（不是通过）**")
            return 3
        rows, note = parse_ledger(a.ledger)
        if rows is None:
            print(f"✗ **{note}——本次未检查（不是通过）**")
            return 3
        total = len(rows)
        primary = sum(1 for t, _ in rows if t in PRIMARY_TIERS)
        lanes = len({l for _, l in rows if l})
        if not lanes:
            print("！ 台账里没有 `lane=` 标注——**道数按 0 算会误判，改为不判这一条**")
            lanes = PROFILES[a.profile]["min_lanes"]
    elif a.primary is not None and a.total is not None and a.lanes is not None:
        primary, total, lanes = a.primary, a.total, a.lanes
    else:
        print("✗ **既没给 --ledger 也没给齐 --primary/--total/--lanes"
              "——本次未检查（不是通过）**")
        return 3

    print(f"手上：一手 **{primary}** 份　总计 **{total}** 份　有材料的道 **{lanes}** 条\n")
    rc = 0
    for prof in ("quick", "standard", "deep"):
        p = PROFILES[prof]
        need = required_primary(prof)
        ok, shrink, bad = verdict(primary, total, lanes, prof)
        head = f"  **{prof:8}**（{p['min_sources']} 份 / {p['min_lanes']} 道 / 占比 {p['min_primary_ratio']:.2f} → **要 {need} 份一手**）"
        if not ok:
            print(head + "　**够不着**")
            for b in bad:
                print(f"      · {b}")
        elif shrink:
            drop = total - max(p["min_sources"], primary)
            print(head + "　**只有丢掉 %d 份已取到的材料才够得着**" % drop)
            print(f"      · 吃全部 {primary}/{total} = {primary/total:.4f}"
                  f" < {p['min_primary_ratio']:.2f}")
            print("      · **这是缩分母，不是达标。**判据不替你决定丢不丢，"
                  "但它不许这件事悄悄发生。")
        else:
            print(head + "　✓ 吃全部材料就够得着")
        print()

    ok_deep, shrink_deep, _ = verdict(primary, total, lanes, a.profile)
    if not ok_deep:
        print(f"★ **目标档 {a.profile} 够不着**——"
              "这不是抓得不够勤，是这个人**传世的一手材料就这么多**。\n"
              "  它判不了「再抓能不能抓到」，只算手上这批的上限。")
        rc = 1
    elif shrink_deep:
        print(f"★ **目标档 {a.profile} 只有靠缩分母才够得着**——请在台账里写明丢了哪些、为什么。")
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
