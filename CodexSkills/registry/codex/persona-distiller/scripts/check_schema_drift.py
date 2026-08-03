#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONL 字段一致性体检 —— 抓订正脚本留下的字段污染。

## 为什么需要它

Jesse Vincent #94：我的订正脚本里有个 `patch(obj)` 无差别地给对象设了 `candidate`，
于是**产物的 `evals/cases.jsonl` 里有 1 条带了 `candidate` 字段，另外 31 条没有**。
`quality_check.py` 忽略多余字段，三个门全绿；**它会就这么打进 ZIP 入库。**

这类污染的特征是**只影响一部分记录**——正因为不是全体，肉眼看首行看不出来。
所以判据不是「有没有这个字段」，而是「**这个字段是不是所有记录都有**」。

## 判据

对每个 JSONL 文件统计字段出现频次：
- 出现在**全部**记录里 → 正常
- 出现在**部分**记录里 → 报出来，人工确认是「合法可选字段」还是「污染」

合法可选的例子：`holdout_source_ids` 只有 known 套组的用例才有。
所以**只列不判**，但必须列——不列就等于放行。

## 负对照（v0.0.0.49 补）

在此之前**这个脚本没有 `--self-test`**——它报「✓ 无字段漂移」时，
那句话不构成任何证据（RUNBOOK 第十八种）。这是 v0.0.0.48 逐件跑自测时查出来的：
27 件判据里有 4 件是这样，本件是其中之一。
"""
import argparse, collections, json, pathlib, sys


def scan(rows: list, known: set) -> list:
    """→ [(字段, 出现数, 总数, 是否已知合法)]；只列部分记录才有的字段。"""
    if not rows:
        return []
    cnt = collections.Counter(k for r in rows for k in r)
    return [(k, v, len(rows), k in known)
            for k, v in sorted(cnt.items(), key=lambda x: x[1]) if v < len(rows)]


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：Jesse Vincent #94 的真实形态 ──")
    # 订正脚本的 patch(obj) 给 1 条设了 candidate，另外 31 条没有。三个官方门全绿。
    rows = [{"case_id": f"jv-{i:02d}", "suite": "known", "prompt": "x"} for i in range(31)]
    rows.append({"case_id": "jv-31", "suite": "known", "prompt": "x", "candidate": "污染"})
    out = scan(rows, set())
    chk("32 条里 1 条多了 candidate → 报出", any(k == "candidate" and v == 1 for k, v, _, _ in out))

    print("── 反向对照 ①：全体都有的字段不许报 ──")
    chk("case_id / suite / prompt 三个字段 32 条全有 → 不报",
        not any(k in ("case_id", "suite", "prompt") for k, _, _, _ in out))

    print("── 反向对照 ②：合法可选字段要标出来，不许和污染混为一谈 ──")
    rows2 = [{"case_id": "a", "suite": "known", "holdout_source_ids": ["s1"]},
             {"case_id": "b", "suite": "voice"}]
    out2 = scan(rows2, {"holdout_source_ids"})
    hit = [r for r in out2 if r[0] == "holdout_source_ids"]
    chk("holdout_source_ids 只有 known 套组有 → 列出但标「已知合法」",
        bool(hit) and hit[0][3] is True)

    print("── 反向对照 ③：空文件不许报「无漂移」，也不许崩 ──")
    chk("空列表 → 返回空，由调用方决定怎么说", scan([], set()) == [])

    print("── 反向对照 ④：只有一条记录时，不许把它自己的字段全报成漂移 ──")
    chk("单条记录 → 它的字段都是 1/1，不报", scan([{"a": 1, "b": 2}], set()) == [])

    print("── 反向对照 ⑤：字段值为 None 也算「有这个字段」 ──")
    # 否则订正脚本把字段设成 None 就能绕过去
    out5 = scan([{"a": 1, "b": None}, {"a": 2, "b": None}], set())
    chk("b 两条都是 None，但两条都有 → 不报（它没漂移，只是空）", out5 == [])
    out5b = scan([{"a": 1, "b": None}, {"a": 2}], set())
    chk("b 只有一条有（哪怕值是 None）→ 报出",
        any(k == "b" and v == 1 for k, v, _, _ in out5b))

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--expect", nargs="*", default=[],
                    help="已知的合法可选字段，形如 cases.jsonl:holdout_source_ids")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    known = collections.defaultdict(set)
    for e in a.expect:
        fn, _, k = e.partition(":")
        known[fn].add(k)

    flagged = scanned = 0
    for f in sorted(a.workspace.rglob("*.jsonl")):
        try:
            rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ✗ {f.name}: 解析失败 {e}")
            flagged += 1
            continue
        if not rows:
            continue
        scanned += 1
        partial = scan(rows, known.get(f.name, set()))
        if partial:
            print(f"── {f.relative_to(a.workspace)}（{len(rows)} 条）")
            for k, v, total, ok in partial:
                print(f"   {k}: {v}/{total}  {'已知合法' if ok else '**须确认**'}")
                flagged += not ok
    if not scanned:
        print(f"✗ **{a.workspace} 下一个非空 .jsonl 都没读到——结果不可信，不是「没问题」**")
        return 3
    print(f"\n扫过 {scanned} 个 .jsonl；"
          f"{'✓ 无字段漂移' if not flagged else f'⚠ {flagged} 处须确认——只列不判'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
