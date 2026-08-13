#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_attribution_tier_consistency.py —— **同一行里 `attribution` 与 `tier` 打架**

## 抓到它的那一次

2026-08-14，给 Brandeis #172 补 heuristic。六组候选**全部落空**，
去量语料构成才看见：他 `attribution=HIS-OWN` 那个池子里，
**32.0% 的词（358,987）`tier` 是 `S1`**。那两份是同一部

    1916《The case for the shorter work day … Bunting v. Oregon》
    creator: Frankfurter, Felix; Oregon, defendant; **Brandeis**; Bunting; Goldmark

**他排第 3 / 共 5**，而这是 Frankfurter 与 Goldmark 汇编的**法庭辩护状**。
台账把它同时标成 `HIS-OWN`（他的话）与 `S1`（二手），**两个字段互相否定**。

后果不是难看：我按 `attribution` 过滤去找「他自己说过的话」，
于是把 35.9 万词**别人汇编的材料**当成了他的声口 —— 六组候选里
「引 Gilbreth 的证词」「辩护状的目录行」「讲真的阳光与照明」全从这里来。

## 本件判什么

台账每一行，`attribution` 与 `tier` 必须指向同一件事：

| attribution | tier 允许 | 不允许 |
|---|---|---|
| `HIS-OWN`（他的话） | `P1`／`P2` | **`S1`／`S2`／`U`** |
| `OTHER`（别人的话） | `S1`／`S2`／`U` | **`P1`／`P2`** |

★ 它**不判哪一个字段是对的** —— 那要读书名页、看 creator 位次，是人的事。
  它只说「这两个字段在这一行上不能同时成立」。

## 它判不了什么（**必须一起念**）

0. ★★★ **`attribution` 有两代 schema，本件只判得了其中一半。**
   2026-08-14 实测：**25 个工作区是枚举**（`HIS-OWN`／`OTHER`，1,613 行），
   **28 个是散文**（那一栏写的是归属**理由**，如「整卷扫图，已切边界：她署名的报告在
   第 250–729 行……」，1,568 行 = **49.3%**）。
   `clash()` 拿字符串比 `HIS-OWN`／`OTHER`，对散文那一半**恒返回 None**——
   于是它们**一条也不会被报出来**，而屏幕上看不出区别。
   ⇒ 本件现在把两代的行数**分开印**；「N 行打架」这个数**只覆盖枚举那一半**。
   [[eval-artifacts-have-five-schemas]]。

1. **两个字段一致 ≠ 两个都对。** 一行标 `OTHER`＋`S1` 完全自洽，
   而它可能其实是他写的。本件对那种情况**一言不发**。
2. 它**不改台账**。存量按㊵冻结；本件是给**新人物**用的
   （㊸ 立的原则：新人物的流程该改就改）。

## 用法

    python3 check_attribution_tier_consistency.py
    python3 check_attribution_tier_consistency.py --self-test

退出码：0＝没有互相打架的行；2＝有（**逐行印出来，含 creator 位次**）
"""
import argparse
import glob
import json
import pathlib
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"

PRIMARY = {"P1", "P2"}
SECONDARY = {"S1", "S2", "U"}


def clash(attribution, tier):
    """一行的两个字段是不是互相否定。→ 说明字符串或 None。**纯函数**。"""
    if attribution == "HIS-OWN" and tier in SECONDARY:
        return f"标着「他的话」却记二手（tier={tier}）"
    if attribution == "OTHER" and tier in PRIMARY:
        return f"标着「别人的话」却记一手（tier={tier}）"
    return None


def creator_position(author: str, surname: str):
    """→ (他排第几, 共几位)。creator 栏是 `;` 分隔的。判不出来给 (None, n)。"""
    parts = [x.strip() for x in (author or "").split(";") if x.strip()]
    for i, a in enumerate(parts):
        if surname and surname.lower() in a.lower():
            return i + 1, len(parts)
    return None, len(parts)


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    chk("★ HIS-OWN ＋ S1 → 打架（Brandeis 那两份就是这个）",
        clash("HIS-OWN", "S1") is not None)
    chk("★ HIS-OWN ＋ U → 打架", clash("HIS-OWN", "U") is not None)
    chk("★ OTHER ＋ P1 → 打架（反方向）", clash("OTHER", "P1") is not None)
    chk("★ 反例：HIS-OWN ＋ P1 → 不报", clash("HIS-OWN", "P1") is None)
    chk("★ 反例：OTHER ＋ S1 → 不报", clash("OTHER", "S1") is None)
    chk("★★ 反例：两个字段一致**不代表两个都对** —— OTHER＋S1 自洽，"
        "而它可能其实是他写的；本件对这种情况一言不发",
        clash("OTHER", "S1") is None)
    _ENUM={"HIS-OWN","OTHER","UNKNOWN",None,""}
    _is_prose=lambda a: isinstance(a,str) and a not in _ENUM and len(a)>24
    chk("★★★ **散文型 attribution 认得出来**（老台账把归属理由写在这一栏）",
        _is_prose("**整卷扫图，已切边界**：她署名的报告在第 250–729 行，末行 CLARA BARTON。"))
    chk("★ 反例：枚举值不算散文", not _is_prose("HIS-OWN") and not _is_prose("OTHER"))
    chk("★ 反例：短字符串不算散文（免得把手滑写的短标记当成理由）", not _is_prose("his own"))
    chk("★★ 散文型走 clash() 恒 None —— **本件对它一言不发，这正是要印出来的射程**",
        clash("**整卷扫图，已切边界**：她署名的报告在第 250–729 行……", "S1") is None)
    chk("★ 反例：字段缺失不许当成打架", clash(None, None) is None and clash("HIS-OWN", None) is None)
    p, n = creator_position(
        "Frankfurter, Felix; Oregon, defendant; Brandeis, Louis Dembitz; Bunting; Goldmark",
        "Brandeis")
    chk(f"★ creator 位次：Brandeis 排第 {p}/{n}（实测那份就是 3/5）", (p, n) == (3, 5))
    p2, n2 = creator_position("Dewey, John", "Brandeis")
    chk(f"★ 反例：名字不在 creator 里 → 位次 None（实得 {p2}）", p2 is None)
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    total = 0
    enum_rows = prose_rows = 0
    enum_ws = prose_ws = 0
    hits = []
    ENUM = {"HIS-OWN", "OTHER", "UNKNOWN", None, ""}
    for d in [str(_w) for _w in iter_workspaces(CORPORA)]:
        ws = pathlib.Path(d)
        led = ws / "evidence/source-ledger.jsonl"
        if not led.is_file():
            continue
        meta = ws / "meta.json"
        surname = ""
        if meta.is_file():
            try:
                surname = (json.loads(meta.read_text(encoding="utf-8")).get("name") or "").split()[-1]
            except (ValueError, IndexError):
                pass
        bad = []
        _prose = 0
        for line in led.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            total += 1
            _a = r.get("attribution")
            if isinstance(_a, str) and _a not in ENUM and len(_a) > 24:
                _prose += 1          # ★ 散文型：本件对它一言不发
            why = clash(_a, r.get("tier"))
            if why:
                pos, n = creator_position(r.get("author"), surname)
                bad.append((r.get("source_id"), r.get("split"), why, pos, n,
                            (r.get("title") or "")[:38]))
        if _prose:
            prose_ws += 1
            prose_rows += _prose
        else:
            enum_ws += 1
        if bad:
            hits.append((ws.name, bad))

    print(f"★★ **`attribution` 两代 schema**：枚举型 {enum_ws} 个工作区｜"
          f"**散文型 {prose_ws} 个（{prose_rows} 行，占 {100*prose_rows/total:.1f}%）** —— "
          f"散文那一半 `clash()` 恒返回 None，**下面这个数只覆盖枚举那一半**")
    print(f"全库台账 **{total}** 行；`attribution` 与 `tier` 互相否定的："
          f"**{sum(len(b) for _, b in hits)} 行**，分布在 **{len(hits)}** 个工作区")
    print("★ 本件**不判哪个字段是对的**（那要读书名页、看 creator 位次，是人的事），"
          "只说这两个在同一行上不能同时成立。\n")
    for name, bad in hits:
        print(f"❌ {name}（{len(bad)} 行）")
        for sid, sp, why, pos, n, ti in bad:
            where = f"creator 里他排第 {pos}/{n}" if pos else (f"creator 共 {n} 位，**没有他**" if n else "无 creator")
            print(f"     {sid} split={sp} —— {why}；{where}　《{ti}》")
    if not hits:
        print("✓ 没有互相否定的行")
    return 2 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
