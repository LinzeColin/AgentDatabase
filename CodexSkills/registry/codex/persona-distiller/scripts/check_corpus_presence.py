#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**账本说有这么多源，磁盘上还有几份。**

## 为什么有这道判据

v0.0.0.46 手工扫了一次十二个工作台，发现三个人物的语料**根本不在**：
Livermore #100（账本 536 条、语料 0 份）、Vesalius #102（47/0）、Galen #101（60/9）。
账本还在、断言还在、文档还在，**只有语料没了**——
于是 `primary_ratio`、引文核查、覆盖率**全都在对着虚空算**。

那一次是手工跑的。**手工的东西会漏，也会记错**：
当时的记录里写 Harvey #103 也缺，2026-08-04 复扫实测 **46 条账本、60 份语料，是齐的**。

## 判据

对每个工作区：**账本条数 × 0.9 ≤ 语料 .txt 份数**，否则报出缺口。

## 它判不了什么

- **不查内容**，只查在不在。文件在但是错误页，那是 `check_corpus_integrity` 的活。
- 阈值取 0.9 而非 1.0：同一份源可能被切成多份、也可能有合并；
  **少几份是正常的，少一半以上不是。**

## ★ 找账本不许写死路径

本流水线里账本出现过**两种布局**：`<工作区>/evidence/source-ledger.jsonl`
与**目录顶层的** `source-ledger.jsonl`。
第一版审计脚本只按前者找，于是 Galen / Vesalius / Harvey / Livermore
**四个工作区整个从表里消失了**——报表看上去「全部齐」。
**用 rglob，不写死路径。**
"""
import argparse
import json
import pathlib
import sys

RATIO = 0.9


def scan(root):
    """→ [(名, 账本条数, 语料份数, 是否缺)]。"""
    rows = []
    for d in sorted(pathlib.Path(root).glob("*")):
        if not d.is_dir():
            continue
        leds = list(d.rglob("source-ledger.jsonl"))
        if not leds:
            rows.append((d.name, None, None, True))
            continue
        n = sum(1 for line in leds[0].read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip())
        t = len([p for p in d.rglob("*.txt") if "raw" in p.parts])
        rows.append((d.name, n, t, t < n * RATIO))
    return rows


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)

        def mk(name, ledger_at, n_led, n_txt):
            w = root / name
            (w / ledger_at).mkdir(parents=True, exist_ok=True)
            (w / ledger_at / "source-ledger.jsonl").write_text(
                "\n".join(json.dumps({"source_id": f"src-{i:012x}"}) for i in range(n_led)) + "\n",
                encoding="utf-8")
            raw = w / "raw"
            raw.mkdir(exist_ok=True)
            for i in range(n_txt):
                (raw / f"f{i}.txt").write_text("x", encoding="utf-8")

        print("── 正向：账本 536 条、语料 0 份（Livermore #100 的真实形态）──")
        mk("wip-a", "evidence", 536, 0)
        r = {x[0]: x for x in scan(root)}
        chk("报出缺口", r["wip-a"][3] and r["wip-a"][1] == 536 and r["wip-a"][2] == 0)

        print("── 反向对照 ①：齐的不许报 ──")
        mk("wip-b", "evidence", 46, 60)
        r = {x[0]: x for x in scan(root)}
        chk("46 条账本、60 份语料 → 不报", not r["wip-b"][3])

        print("── 反向对照 ②：**账本在目录顶层也要找得到** ──")
        # 第一版写死 `<工作区>/evidence/`，于是四个工作区整个从表里消失、报表显示「全部齐」
        mk("wip-c", ".", 60, 9)
        r = {x[0]: x for x in scan(root)}
        chk("顶层账本 60 条、语料 9 份 → 找得到并报出",
            "wip-c" in r and r["wip-c"][3] and r["wip-c"][1] == 60)

        print("── 反向对照 ③：少几份是正常的，不许报 ──")
        mk("wip-d", "evidence", 100, 95)
        r = {x[0]: x for x in scan(root)}
        chk(f"95/100 ≥ {RATIO:.0%} → 不报", not r["wip-d"][3])
        mk("wip-e", "evidence", 100, 80)
        r = {x[0]: x for x in scan(root)}
        chk(f"80/100 < {RATIO:.0%} → 报出", r["wip-e"][3])

        print("── 反向对照 ④：没有账本的目录要单列，不许当成「齐」 ──")
        (root / "wip-f").mkdir()
        r = {x[0]: x for x in scan(root)}
        chk("无账本 → 报出且账本数记 None", r["wip-f"][3] and r["wip-f"][1] is None)

        print("── 反向对照 ⑤：**只数 raw/ 下的 .txt**，别的目录不算 ──")
        (root / "wip-g" / "evidence").mkdir(parents=True)
        (root / "wip-g" / "evidence" / "source-ledger.jsonl").write_text(
            "\n".join('{"source_id":"x"}' for _ in range(50)) + "\n", encoding="utf-8")
        (root / "wip-g" / "notes").mkdir()
        for i in range(50):
            (root / "wip-g" / "notes" / f"n{i}.txt").write_text("x", encoding="utf-8")
        r = {x[0]: x for x in scan(root)}
        chk("50 份 .txt 全在 notes/ 而非 raw/ → 仍报缺",
            r["wip-g"][3] and r["wip-g"][2] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="含多个工作区的目录（如 _corpora/）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.root:
        ap.error("要么 --self-test，要么给 --root")

    rows = scan(a.root)
    if not rows:
        print(f"✗ **{a.root} 下一个工作区都没扫到——结果不可信，不是「没问题」**")
        return 3

    print(f"{'工作区':24} {'账本':>6} {'语料':>6}  状态")
    bad = []
    for name, n, t, miss in rows:
        if n is None:
            print(f"{name:24} {'—':>6} {'—':>6}  **无账本**")
            bad.append(name)
            continue
        print(f"{name:24} {n:6} {t:6}  {'✓' if not miss else f'**缺 {n - t}**'}")
        if miss:
            bad.append(name)
    if not bad:
        print(f"\n  ✓ {len(rows)} 个工作区的语料都在")
        return 0
    print(f"\n✗ **{len(bad)} 个工作区的语料不全**——"
          "账本、断言、文档都还在，**只有语料没了**；"
          "`primary_ratio`、引文核查、覆盖率会对着虚空算：")
    for name in bad:
        print(f"    {name}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
