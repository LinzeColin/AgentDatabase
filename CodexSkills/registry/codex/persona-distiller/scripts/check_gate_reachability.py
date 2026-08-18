#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门槛是不是设在了评委的实测天花板之上——**在烧掉第四个人之前问一次**。

## 为什么有这件

Pasteur #106、Koch #107、Lister #108 连续三人死在同一项 `min_fact 0.93`：

| 人物 | `fact-preservation` 候选绝对 | 差 |
|---|---:|---:|
| Pasteur | 0.8725 | −0.0575 |
| Koch | 0.8050 | −0.1250 |
| Lister（三轮） | 0.8800 → 0.8950 → **0.8925** | −0.0375 |

到第三个人的第三轮我才去数了一下两席的分数分布：

| 席 | 最高分 | ≥9.3 的题数 | ≥9.0 的题数 |
|---|---:|---:|---:|
| D | 9.5 | 15 / 96 | 38 / 96 |
| **E** | **8.9** | **0 / 96** | **0 / 96** |

套组分是 (题数 × 席数) 的均值。若每题都拿到各席的**实测上限**：

    (9.5 + 9.5 + 8.9 + 8.9) / 4 = 9.20  →  0.920 < 0.930

**门槛高于可达上限。** 不是产物差 0.037，是这道门在这两把尺子下根本到不了。

**三个人、九轮评审、十八次判分之后我才想到去数这一下。**
本件把那一下变成每次发布门都做的事。

## 判据形状：报告，不阻塞

它**不判**「门槛该不该改」——那是人的决定，而且三条化解路径每一条都带着
一个作者能自己滥用的旋钮（调阈值／放松席位／给回 rubric）。
它只回答一个纯算术问题：**以这批实测分为据，这道门够不够得着。**

**够不着**时它报出来；**够得着而没过**，那就是产物的问题，与本件无关。

## 射程边界

- **「实测上限」不是「证明的上限」。** 席 E 理论上可以给 9.5，只是 96 次没给过。
  样本越小，这个上限越不可信——故输出必带样本量。
- **它不看产物。** 同一批评委分数，换个产物结论一样。
- **只在有判分数据时可用。** 没有 `results.jsonl` 就是「未检查」，不是「通过」。

用法：

    python3 check_gate_reachability.py --results evals/results.jsonl --profile deep
    python3 check_gate_reachability.py --results a.jsonl b.jsonl --profile deep   # 多轮合并
    python3 check_gate_reachability.py --self-test

退出码：0=每道门都够得着（或本次未检查）　1=有门够不着　2=自测未过
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

# 与 scripts/common.py 的 PROFILE_THRESHOLDS 对齐。**在这里重抄一份是有意的**：
# 本件要能对着任意一批历史判分独立跑，不依赖某个工作区的 common.py 版本。
# 若两处分叉，check_contract_drift 之外还有下面这条自检会报出来。
SUITE_GATES = {
    "quick":    {"fact-preservation": 0.80, "boundary": 0.70},
    "standard": {"fact-preservation": 0.88, "boundary": 0.78},
    "deep":     {"fact-preservation": 0.93, "boundary": 0.85},
}


def load(paths):
    """读 results.jsonl → {席: [候选分…]}（0–10 制）与套组归属。

    ★ **两种格式都要认。** 本流水线同时存在两份 results.jsonl：
      · 工作区 `evals/results.jsonl` 是**扁平**格式，发布门读的是这一份：
        `{case_id, system: candidate|baseline, overall_score: 0–1, judge_id, suite}`
      · 工作台 `./results.jsonl` 是**逐对**格式：
        `{case_id, seat, candidate: 0–10, baseline: 0–10, suite, note}`
      第一版只认逐对格式，接进发布门后**一条都没读到**，于是报「本次未检查」、
      退出 0、警告不出现——**判据是绿的，只是它看的不是被判的那份东西**。
      这是同类第五次；接线之后必须实跑一次看警告真的出来，不能只看代码。
    """
    by_seat = collections.defaultdict(list)
    by_suite_seat = collections.defaultdict(lambda: collections.defaultdict(list))

    # ★★★★★ 2026-08-19：**逐对格式的量纲不是恒定的 0–10，要从数据推。**
    #   实测：Barton #117 的工作台 `results.jsonl` 是 **0–1** 制
    #   （`candidate: 0.7966`），而 Fleming/Nightingale/Osler/Virchow 四人是 0–10
    #   （`candidate: 8.4031`）——逐行核过，两份文件是同一批读数、比值恰好 10。
    #   按「逐对一律 0–10」读 Barton，上限算出 **0.0895**（真值 0.8950），
    #   quick 0.80 / standard 0.88 / deep 0.93 **三道门全部报「够不着」**——
    #   一个永远变不绿的红。[[a-red-that-can-never-turn-green-is-not-a-signal]]
    #   ★ 射程要说清：发布门读的是**扁平**那份，所以**正常流水线上不发生**；
    #     把本工具单独指向工作台那份才会。[[proved-the-mechanism-never-asked-if-it-happened]]
    _pair_vals = []
    for p in paths:
        for line in pathlib.Path(p).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "candidate" in r and "seat" in r:
                _pair_vals.append(float(r["candidate"]))
    # ≥8 个读数且全部 ≤1.0 ⇒ 判为 0–1 制。样本太少不敢判，宁可按原样读。
    _pair_scale = 10.0 if (len(_pair_vals) >= 8 and max(_pair_vals) <= 1.0) else 1.0
    if _pair_scale != 1.0:
        print(f"  ★ 逐对表实测最大值 {max(_pair_vals):.4f} ≤ 1.0 且有 {len(_pair_vals)} 个读数"
              f" ⇒ 判为 **0–1 制**，按 ×10 归一（默认按 0–10 读）")

    for p in paths:
        for line in pathlib.Path(p).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "candidate" in r and "seat" in r:                 # 逐对格式，量纲现推
                seat, score = r["seat"], float(r["candidate"]) * _pair_scale
            elif r.get("system") == "candidate" and "overall_score" in r:  # 扁平，0–1
                seat, score = r.get("judge_id", "?"), float(r["overall_score"]) * 10.0
            else:
                continue
            by_seat[seat].append(score)
            if r.get("suite"):
                by_suite_seat[r["suite"]][seat].append(score)
    return by_seat, by_suite_seat


def ceiling(by_seat) -> tuple[float, dict]:
    """各席实测最高分的**均值**——即「每题都拿到各席上限」时套组分能到多少。"""
    per = {s: max(v) for s, v in by_seat.items() if v}
    if not per:
        return 0.0, {}
    return sum(per.values()) / len(per) / 10.0, per


def self_test() -> int:
    """负对照 + 三条反向对照。"""
    print("══ 负对照 ══")
    fail = 0

    # 席 E 封顶 8.9、席 D 封顶 9.5 → 上限 0.92，低于 deep 的 0.93 → 必须报出
    lo = {"D": [9.5, 9.4, 9.0], "E": [8.9, 8.5, 8.0]}
    c, _ = ceiling(lo)
    caught = c < SUITE_GATES["deep"]["fact-preservation"]
    print(f"  {'✓ 抓到' if caught else '✗ 漏掉'} 上限 {c:.3f} < deep 的 "
          f"{SUITE_GATES['deep']['fact-preservation']} → 够不着")
    fail += not caught

    print("\n══ 量纲现推 ══")
    import tempfile as _tf, json as _j
    def _mk(vals):
        f = pathlib.Path(_tf.mkdtemp()) / "results.jsonl"
        f.write_text("\n".join(_j.dumps({"case_id": f"q-{i:02d}", "seat": "D",
                                          "candidate": v, "baseline": v,
                                          "suite": "voice"}) for i, v in enumerate(vals)) + "\n",
                     encoding="utf-8")
        return [str(f)]
    b1, _ = load(_mk([0.93, 0.86, 0.90, 0.88, 0.79, 0.81, 0.84, 0.77]))   # 0–1 制
    c1, _ = ceiling(b1)
    ok = abs(c1 - 0.93) < 1e-3
    print(f"  {'✓' if ok else '✗'} 0–1 制的逐对表归一后上限 {c1:.4f}（不归一会是 0.0930）")
    fail += not ok
    b2, _ = load(_mk([9.3, 8.6, 9.0, 8.8, 7.9, 8.1, 8.4, 7.7]))          # 0–10 制
    c2, _ = ceiling(b2)
    ok2 = abs(c2 - 0.93) < 1e-3
    print(f"  {'✓' if ok2 else '✗'} ★ 反对照：0–10 制**不许**被再乘 10，上限 {c2:.4f}（应 0.9300）")
    fail += not ok2
    # ★★ 最要紧的一条：**同一批读数换个量纲，上限必须一模一样**。
    #    单看某一边的数值对不对，看不出「两边不等价」这件事。
    ok23 = abs(c1 - c2) < 1e-9
    print(f"  {'✓' if ok23 else '✗'} ★★ 同一批读数写成 0–1 与 0–10，上限必须相等：{c1:.4f} vs {c2:.4f}")
    fail += not ok23
    b3, _ = load(_mk([0.9, 0.8]))                                         # 样本太少
    c3, _ = ceiling(b3)
    ok3 = abs(c3 - 0.09) < 1e-3
    print(f"  {'✓' if ok3 else '✗'} ★★ 反对照：只有 2 个读数**不敢判**，按原样读，上限 {c3:.4f}")
    fail += not ok3

    print("\n══ 反向对照 ══")
    # ① 两席都能给到 9.5 → 上限 0.95，够得着 → **不得报**
    hi = {"D": [9.5, 9.0], "E": [9.6, 9.2]}
    c2, _ = ceiling(hi)
    ok1 = c2 >= SUITE_GATES["deep"]["fact-preservation"]
    print(f"  {'✓' if ok1 else '✗'} 两席都能给到 9.5+ → 上限 {c2:.3f}，够得着，不报")
    fail += not ok1

    # ② 同一批分数对着 quick 的 0.80 → 必须够得着（证明不是「凡门皆报」）
    ok2 = ceiling(lo)[0] >= SUITE_GATES["quick"]["fact-preservation"]
    print(f"  {'✓' if ok2 else '✗'} 同一批分数对 quick 的 0.80 → 够得着，不报"
          f"（证明不是凡门皆报）")
    fail += not ok2

    # ③ 扁平格式（发布门实际读的那一份）必须也能读进来。
    #    第一版只认逐对格式，接进门后一条都没读到——**判据绿了但指错了文件**，第五次。
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / "flat.jsonl"
        f.write_text("\n".join(json.dumps(r) for r in [
            {"case_id": "c1", "system": "candidate", "overall_score": 0.89,
             "judge_id": "seat-E", "suite": "fact-preservation"},
            {"case_id": "c1", "system": "baseline", "overall_score": 0.60,
             "judge_id": "seat-E", "suite": "fact-preservation"},
            {"case_id": "c1", "system": "candidate", "overall_score": 0.95,
             "judge_id": "seat-D", "suite": "fact-preservation"},
        ]) + "\n", encoding="utf-8")
        bs, _ = load([f])
        okf = sorted(bs) == ["seat-D", "seat-E"] and bs["seat-E"] == [8.9] and bs["seat-D"] == [9.5]
        print(f"  {'✓' if okf else '✗'} 扁平格式（发布门实读的那一份）也能读进来"
              f"，且基线行不计入（读到 {dict(bs)}）")
        fail += not okf

    # ④ 无数据 → 上限为 0，调用方须据此报「未检查」而非「够不着」
    c3, per3 = ceiling({})
    ok3 = c3 == 0.0 and not per3
    print(f"  {'✓' if ok3 else '✗'} 无判分数据 → 返回空，调用方须报「未检查」而非结论")
    fail += not ok3

    print("\n  ✓ 负对照通过（5/5）" if not fail
          else f"\n  ✗ {fail} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="*", default=[],
                    help="assemble_*.py 产出的 results.jsonl，可给多份（多轮合并）")
    ap.add_argument("--profile", default="deep", choices=sorted(SUITE_GATES))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test and not a.results:
        return 2 if self_test() else 0
    if not a.results:
        ap.error("--results 必填（除非只跑 --self-test）")

    by_seat, by_suite_seat = load(a.results)
    if not by_seat:
        print("没有可用的判分数据——**本次未检查（不是通过）**")
        return 0

    c, per = ceiling(by_seat)
    n = sum(len(v) for v in by_seat.values())
    print(f"判分样本 {n} 个，席 {len(per)} 个")
    for s in sorted(per):
        v = by_seat[s]
        ge9 = sum(1 for x in v if x >= 9.0)
        print(f"  席 {s}: n={len(v)}　最高 {max(v)}　≥9.0 的 {ge9} 个")
    print(f"**各席实测上限的均值 = {c:.3f}**"
          f"（即每题都拿到各席上限时，套组分能到的位置）")
    print(f"（这是**实测**上限不是**证明**的上限；样本 {n} 个，样本越小越不可信）\n")

    bad = []
    for suite, th in sorted(SUITE_GATES[a.profile].items()):
        mark = "✅ 够得着" if c >= th else f"❌ **够不着**（差 {th - c:.3f}）"
        print(f"  {a.profile} min_{suite:20} {th:.2f}　vs 上限 {c:.3f}　{mark}")
        if c < th:
            bad.append((suite, th))
    if bad:
        print("\n  ⚠ **这些门在当前评委分布下到不了**——"
              "产物再好也过不去，所以「未过」不构成「产物不够好」的证据。\n"
              "    不要因此自行放宽阈值：三条化解路径（调阈值／放松席位／给回 rubric）"
              "每一条都带着一个作者能自己滥用的旋钮。**这是人的决定。**\n"
              "    见 skill_log_evals/persona-distiller/"
              "FINDING_min-fact-threshold-above-seat-ceiling.md")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
