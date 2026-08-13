#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_profile_declared.py —— **谁没声明档位，就是在被另一把尺子量着**

## 抓到它的那一次

2026-08-14，Dewey #190。他的合成门报

    source.lane-coverage: 3 lanes < profile minimum 6
    claim.model-minimum: mental models 1 < 3
    claim.heuristic-minimum: heuristics 0 < 5

`min_lanes 6` 正是第 2 批十人**九人出局的第一死因**，照这个读法他该直接记延后。
去查档位才发现：**他的 `meta.json` 里根本没有 `profile` 这个键**，
而同一批返工的另外两人（Brandeis #172、Michelangelo #185）都是 `quick`。
**三个人里有一个被拿另一把尺子量着，而没有任何东西提醒。**

## 同一个概念，两个默认值

    quality_check.py:4325     profile = meta.get('profile', 'standard')     ← 判的时候按 standard
    init_target.py:83         --profile ... default='deep'                  ← 建的时候写 deep

**建器不写 `--profile` 就落 `deep`；判据读不到 `profile` 就按 `standard`。**
两边差着两档：`min_sources` 45 vs 24、`min_lanes` 6 vs 6、`min_primary_ratio` 0.65 vs 0.50、
`min_fact_score` 0.93 vs 0.88。

## 本件判什么

**只回答一句：哪些工作区没有声明 `profile`。** 它

- **不改任何门**、不替谁选档（选档是 ㉞「按可得性选档 ＋ 退档写明理由」的事，要人写理由）；
- **不把「没声明」判成错**——老工作区没声明是历史，不是回归；
- 但**必须把名字印出来**：`meta.get('profile', 'standard')` 是**静默**的，
  不印出来就没有人知道自己在被哪把尺子量。

★ 另判一种更险的：`profile` **键在而值是 `null`**。
那时 `PROFILE_THRESHOLDS.get(None)` → `None`，`quality_check` 直接
`ERROR: invalid profile None` 退出——**整个工作区一项都不检查**，
与 `target.invalid` 同形（[[a-refusal-to-check-prints-one-error]]）。2026-08-14 实测 0 个。

## 用法

    python3 check_profile_declared.py
    python3 check_profile_declared.py --self-test

退出码：0＝跑完（**这不是一道门**）；2＝有 `profile: null`（那一种会让判据拒检，要修）
"""
import argparse
import glob
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"
CHECKER_DEFAULT = "standard"     # quality_check.py:4325
BUILDER_DEFAULT = "deep"         # init_target.py:83
VALID = ("quick", "standard", "deep")


def classify(meta: dict) -> str:
    """meta → 'declared' / 'absent' / 'null' / 'invalid'。**纯函数**，自测不碰磁盘。"""
    if "profile" not in meta:
        return "absent"
    v = meta["profile"]
    if v is None:
        return "null"
    return "declared" if v in VALID else "invalid"


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    chk("声明了 quick → declared", classify({"profile": "quick"}) == "declared")
    chk("★ 键不存在 → absent（判据会静默按 standard 判）", classify({"name": "x"}) == "absent")
    chk("★★ 键在而值是 null → null（判据会 ERROR 退出，整个工作区不被检查）",
        classify({"profile": None}) == "null")
    chk("★ 反例：写了个不认识的档 → invalid，**不许当成 declared**",
        classify({"profile": "ultra"}) == "invalid")
    chk("★ 反例：空字符串也不算声明", classify({"profile": ""}) == "invalid")
    chk("★ 两个默认值确实不同（本件存在的理由）", CHECKER_DEFAULT != BUILDER_DEFAULT)
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    buckets = {"declared": [], "absent": [], "null": [], "invalid": []}
    for d in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
        ws = pathlib.Path(d)
        mp = ws / "meta.json"
        if not mp.is_file():
            continue
        try:
            meta = json.loads(mp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        wip = next((s for s in ws.parts if s.startswith("wip-")), ws.name)
        buckets[classify(meta)].append(f"{wip}／{ws.name}")

    print(f"档位声明：{len(buckets['declared'])} 个已声明"
          f"｜**{len(buckets['absent'])} 个没有 `profile` 键**"
          f"｜{len(buckets['null'])} 个是 null｜{len(buckets['invalid'])} 个值不认识")
    print(f"  ★ 两个默认值不同：判据 `meta.get('profile', '{CHECKER_DEFAULT}')`，"
          f"建器 `--profile` 默认 `{BUILDER_DEFAULT}`")
    if buckets["absent"]:
        print(f"  ！ 下面这些**正在被 `{CHECKER_DEFAULT}` 的尺子量着**（不是错，但要知道）：")
        for x in buckets["absent"]:
            print(f"       {x}")
    rc = 0
    for k, note in (("null", "判据会 `ERROR: invalid profile None` **拒检整个工作区**"),
                    ("invalid", "值不在 quick/standard/deep 里，同样会拒检")):
        if buckets[k]:
            rc = 2
            print(f"  ❌ **{len(buckets[k])} 个 `profile` 是 {k}** —— {note}：")
            for x in buckets[k]:
                print(f"       {x}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
