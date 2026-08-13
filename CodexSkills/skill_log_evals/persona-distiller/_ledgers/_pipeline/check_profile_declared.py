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
ORDER = ("quick", "standard", "deep")
# (min_sources, min_lanes, min_primary_ratio) —— 与 common.PROFILE_THRESHOLDS 同源
TH = {"quick": (8, 3, 0.40), "standard": (24, 6, 0.50), "deep": (45, 6, 0.65)}


def computed(rows) -> str:
    """台账 → **材料够得着的最高一档**。纯函数。

    ★★ **口径必须与 `quality_check.evaluate_sources()` 逐字一致**，否则报出来的
      「不一致」是我自己算错的。2026-08-14 第一版就错了三处，被 Liebig #124 撞出来：
      他的延后记录写「一手占比 0.6094」，而我算出 0.4688 —— 因为

        ① `primary` 是 **`{'P1','P2'}`**，不是只有 P1（他 P1 30 ＋ P2 9 ＝ 39，39/64＝0.6094）；
        ② 分母是 **usable**：train 里去掉 `tier == 'U'` 与 `extraction_status == 'failed'`；
        ③ `min_sources` 比的是 **len(usable)**，`min_lanes` 数的也是 usable 的 `dimensions`。

      [[baseline-must-be-the-same-kind-as-what-you-compare]]：**别重实现判据的度量。**
    """
    train = [r for r in rows if r.get("split") == "train"]
    usable = [r for r in train
              if r.get("tier") != "U" and r.get("extraction_status") != "failed"]
    n = len(usable)
    lanes = len({x for r in usable for x in (r.get("dimensions") or [])})
    primary = sum(1 for r in usable if r.get("tier") in {"P1", "P2"})
    ratio = primary / n if n else 0.0
    for k in reversed(ORDER):
        a, b, c = TH[k]
        if n >= a and lanes >= b and ratio >= c:
            return k
    return "（够不着 quick）"


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

    # ── 第二项：声明的档 vs 由材料现算的档 ──
    R = lambda dims, tier="P1": {"split": "train", "dimensions": dims, "tier": tier}
    six = ["writings", "conversations", "expression", "decisions", "timeline", "external"]
    deep_rows = [R([six[i % 6]]) for i in range(50)]          # 50 源 / 6 道 / 一手 1.00
    chk(f"★ 50 源 6 道 一手 1.00 → 现算 deep（实得 {computed(deep_rows)}）",
        computed(deep_rows) == "deep")
    thin = [R(["writings"]) for _ in range(50)]               # 50 源但只有 1 道
    chk(f"★ 反例：50 源而只有 1 道 → 够不着 quick（实得 {computed(thin)}）",
        computed(thin) == "（够不着 quick）")
    mid = [R([six[i % 3]]) for i in range(30)]                # 30 源 / 3 道
    chk(f"★ 30 源 3 道 → quick（standard 要 6 道）（实得 {computed(mid)}）",
        computed(mid) == "quick")
    half = [R([six[i % 6]], "P1" if i % 2 else "S1") for i in range(50)]   # 一手比 0.50
    chk(f"★ 一手比 0.50 → standard 而不是 deep（deep 要 0.65）（实得 {computed(half)}）",
        computed(half) == "standard")
    # ★★ Liebig #124 撞出来的三处口径（第一版全错）
    p2 = [R([six[i % 6]], "P1" if i % 10 < 5 else ("P2" if i % 10 < 7 else "S1"))
          for i in range(50)]                       # P1 25 ＋ P2 10 ＝ 35/50 = 0.70
    chk(f"★★ **P2 也算一手**（P1 25＋P2 10＝0.70 → deep）（实得 {computed(p2)}）",
        computed(p2) == "deep")
    with_u = [R([six[i % 6]]) for i in range(50)] + [R(["writings"], "U") for _ in range(40)]
    chk(f"★★ **`tier == 'U'` 不进分母**（50 好 ＋ 40 个 U → 仍 deep）（实得 {computed(with_u)}）",
        computed(with_u) == "deep")
    failed = [R([six[i % 6]]) for i in range(50)]
    for r in failed[:40]:
        r["extraction_status"] = "failed"           # 只剩 10 份可用 ⇒ 掉到 quick
    chk(f"★★ **`extraction_status == 'failed'` 不进分母**（50 份里 40 份抽取失败 → quick）"
        f"（实得 {computed(failed)}）", computed(failed) == "quick")
    ho = [R([six[i % 6]]) for i in range(50)] + [
        {"split": "holdout", "dimensions": ["decisions"], "tier": "P1"} for _ in range(20)]
    chk(f"★ 反例：holdout 不算进来（50 train ＋ 20 holdout → 仍按 50 判）（实得 {computed(ho)}）",
        computed(ho) == "deep")
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    buckets = {"declared": [], "absent": [], "null": [], "invalid": []}
    mism = []
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
        # ★ 第二项：声明的 vs 现算的
        led = ws / "evidence/source-ledger.jsonl"
        if classify(meta) == "declared" and led.is_file():
            try:
                rows = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()]
            except ValueError:
                rows = []
            if rows:
                c = computed(rows)
                if c != meta["profile"]:
                    mism.append((wip, ws.name, meta["profile"], c))

    print(f"档位声明：{len(buckets['declared'])} 个已声明"
          f"｜**{len(buckets['absent'])} 个没有 `profile` 键**"
          f"｜{len(buckets['null'])} 个是 null｜{len(buckets['invalid'])} 个值不认识")
    print(f"  ★ 两个默认值不同：判据 `meta.get('profile', '{CHECKER_DEFAULT}')`，"
          f"建器 `--profile` 默认 `{BUILDER_DEFAULT}`")
    if buckets["absent"]:
        print(f"  ！ 下面这些**正在被 `{CHECKER_DEFAULT}` 的尺子量着**（不是错，但要知道）：")
        for x in buckets["absent"]:
            print(f"       {x}")
    if mism:
        lower = [m for m in mism if m[3] in ORDER and m[2] in ORDER
                 and ORDER.index(m[3]) > ORDER.index(m[2])]
        print(f"  ！ **{len(mism)} 个工作区声明的档与由材料现算的不一致**"
              f"（其中 **{len(lower)} 个声明得比材料低** ⇒ 门被放松）：")
        for wip, nm, dec, com in sorted(mism, key=lambda x: x[2]):
            mark = "  ← **门被放松**" if (com in ORDER and dec in ORDER
                                     and ORDER.index(com) > ORDER.index(dec)) else ""
            print(f"       {wip:24s} 声明 {dec:9s} 现算 {com}{mark}")
        print("     ★ 本件**不改任何 meta**——选档是 ㉞「按可得性选档 ＋ 退档写明理由」的事，"
              "要人写理由。判分之前先定一句用哪个。")
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
