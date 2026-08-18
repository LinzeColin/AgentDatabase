#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C 层（自优化）只在**团队真实成功率约 4%–38%** 时才启用得了。

## 事实（2026-08-18 实测 @v0.0.0.43，整条回路实跑过）

C 层启用要三条同时成立（`route_team_moe.load_telemetry`）：

    sample_count >= 60  且  expected_calibration_error <= 0.12  且  task_slice_coverage >= 0.75

而 `record_team_outcome.append_outcome` 里：

    routing_scores = [row["marginal_score"] or row["base_score"] for row in members]
    predicted      = mean(routing_scores)            # ← 存进 `predicted_success`

`calibration_error` = 分箱的 `|mean(predicted) − mean(actual)|` 加权平均（标准 ECE）。

**`predicted_success` 是一个排序分，不是概率。** 而它的取值范围**依赖样本**
（★★ 两份都要报，别只报对自己有利的那份）：

    72 道 oracle 的 12 个独立题面 ⇒ **0.1559–0.2552**（中位 0.2444）⇒ 窗口 **0.04–0.38**
    名册场景标签 12 条（本件默认）⇒ **0.2155–0.5160**（中位 0.3914）⇒ 窗口 **0.10–0.64**

**取对产品最有利的那份（窗口上沿 0.64）来说话**，结论仍然成立：

    真实成功率 70% ⇒ ECE **0.1840** ⇒ eligible_for_c **False**
    真实成功率 80% ⇒ ECE **0.2840** ⇒ eligible_for_c **False**
    真实成功率 90% ⇒ ECE **0.3840** ⇒ eligible_for_c **False**

**⇒ 自优化层被绑在「产品表现得差」这个条件上。**
★ 基线 `BASELINE_WINDOW_HI` 绑的是**本件默认样本**（名册标签）的 0.6360 ——
  换样本就是换尺子，别拿 oracle 那份去判它。[[baseline-must-be-the-same-kind-as-what-you-compare]]

## 整条回路实跑过（所以这不是「没实现」，是「校准错了对象」）

在**临时遥测文件**上写满 60 条（12 个切片 × 5，coverage 1.00），默认遥测路径一字节未碰：

    actual_success = 0.2409（＝匹配排序分）⇒ ECE **0.0000** ⇒ eligible_for_c **True**  ⇒ 实跑 strategy = **C**
    actual_success = 0.85（一个能用的产品）⇒ ECE **0.6091** ⇒ eligible_for_c **False** ⇒ 实跑 strategy = **B**

**机制是通的。坏的是「预测量」选错了。** [[measure-a-change-at-the-layer-it-acts-on]]

★ 本件**不改任何门**（改 `predicted_success` 的定义或 ECE 阈值会改变每一次路由的策略层，
  属「门、席位一概不动」，见 Task #137）。本件钉的是：
  **那个可启用窗口的上沿不许再往下掉**，外加钉住「预测量取自 marginal/base_score」这个事实还在。

用法：

    python3 check_c_layer_is_reachable_for_a_working_product.py
    python3 check_c_layer_is_reachable_for_a_working_product.py --baseline-window-hi 0.99   # 看它红不红得了
    python3 check_c_layer_is_reachable_for_a_working_product.py --self-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

BASELINE_WINDOW_HI = 0.63   # 2026-08-18 实测（**本件默认样本**）max(predicted)+ECE门 = 0.5160+0.12 = 0.6360
ECE_GATE = 0.12             # 与 route_team_moe.load_telemetry 里的常数对齐（自测会核对）
MIN_TASKS = 4
WORKING_RATES = (0.70, 0.80, 0.90)   # 「一个能用的产品」的几档真实成功率


def _load():
    sys.path.insert(0, str(HERE))
    import route_team_moe as R              # noqa: E402
    import record_team_outcome as W         # noqa: E402
    return R, W


def predicted_range(R, tasks) -> list[float]:
    """→ 每道题的 `predicted_success`（＝队伍 marginal_score 均值），**照抄写手的取法**。"""
    root = R.default_registry_root()
    out = []
    for t in tasks:
        rt = R.build_route(t, root, "auto", None, "auto", None)
        vals = [float(m.get("marginal_score", m.get("base_score", 0.5)))
                for m in rt.get("members", [])]
        if vals:
            out.append(sum(vals) / len(vals))
    return out


def eligible_with(R, W, predicted: float, actual: float, n: int = 60) -> tuple[bool, float]:
    """在**临时文件**上造 n 条遥测，问产品自己 `eligible_for_c`。默认路径一字节不碰。"""
    runs = [{"predicted_success": predicted, "actual_success": actual} for _ in range(n)]
    ece = W.calibration_error(runs)
    doc = {"sample_count": n, "expected_calibration_error": ece, "task_slice_coverage": 1.0}
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "t.json"
        p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return bool(R.load_telemetry(p).get("eligible_for_c")), ece


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("   %s %s" % ("✓" if cond else "✗", name))
        ok = ok and bool(cond)

    R, W = _load()
    src = (HERE / "route_team_moe.py").read_text(encoding="utf-8")
    chk("① 门里的 ECE 阈值仍是 %.2f（源码现读）" % ECE_GATE,
        "calibration_error <= %s" % ECE_GATE in src or "<= 0.12" in src)
    wsrc = (HERE / "record_team_outcome.py").read_text(encoding="utf-8")
    chk("②★ 预测量仍取自 marginal_score／base_score（本件的全部前提）",
        'row.get("marginal_score", row.get("base_score"' in wsrc)

    # ★★ 正对照：预测与实际对齐 ⇒ ECE 0 ⇒ 必须能启用（证明这条回路是通的）
    on, ece0 = eligible_with(R, W, 0.24, 0.24)
    chk("③★★ 正对照：predicted==actual ⇒ ECE %.4f ⇒ eligible **必须为真**" % ece0, on and ece0 <= 1e-9)
    # ★★★ 反对照：一个能用的产品（85%）⇒ 必须开不了
    off, ece1 = eligible_with(R, W, 0.24, 0.85)
    chk("④★★★ 反对照：predicted 0.24 vs 真实 0.85 ⇒ ECE %.4f ⇒ eligible **必须为假**" % ece1,
        (not off) and ece1 > ECE_GATE)

    sys.path.insert(0, str(HERE))
    from check_mode_ladder_reachable import sample_tasks
    tasks = sample_tasks(HERE.parent / "team-index.json", 12)
    preds = predicted_range(R, tasks)
    chk("⑤ 取得到 ≥%d 道题的 predicted（现测 %d 道）" % (MIN_TASKS, len(preds)), len(preds) >= MIN_TASKS)
    chk("⑥★ predicted 确实落在**远低于 1** 的区间（现测 %.4f–%.4f）—— 它是排序分不是概率"
        % (min(preds), max(preds)), max(preds) < 0.6)
    chk("⑦ 地板可达：0 < BASELINE_WINDOW_HI < 1", 0.0 < BASELINE_WINDOW_HI < 1.0)
    print("   —— self-test %s ——" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="C 层对一个能用的产品是否可达")
    ap.add_argument("--baseline-window-hi", type=float, default=None)
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    floor = BASELINE_WINDOW_HI if a.baseline_window_hi is None else a.baseline_window_hi
    R, W = _load()
    sys.path.insert(0, str(HERE))
    from check_mode_ladder_reachable import sample_tasks
    tasks = sample_tasks(HERE.parent / "team-index.json", a.limit)
    preds = predicted_range(R, tasks)
    if len(preds) < MIN_TASKS:
        print("★ **未量，不是通过**（rc=4）—— 只取到 %d 道题" % len(preds))
        return 4

    lo, hi = min(preds), max(preds)
    on, _ = eligible_with(R, W, (lo + hi) / 2, (lo + hi) / 2)
    if not on:
        print("★ **未量，不是通过**（rc=4）—— **正对照没过**：预测与实际完全对齐都启用不了 ⇒ "
              "是我的探针死了，不是产品的结论。")
        return 4

    print("C 层启用要：sample_count ≥ 60 且 ECE ≤ %.2f 且 coverage ≥ 0.75" % ECE_GATE)
    print("而 `predicted_success` = 队伍 **marginal_score 均值**（record_team_outcome:95）")
    print("  %d 道题上实测：**%.4f–%.4f**（中位 %.4f）"
          % (len(preds), lo, hi, sorted(preds)[len(preds) // 2]))
    print("  ⇒ ECE ≤ %.2f ⇔ |排序分 − 真实成功率| ≲ %.2f" % (ECE_GATE, ECE_GATE))
    print("  ⇒ **真实成功率必须落在 %.2f–%.2f，C 才可能启用**"
          % (max(0.0, lo - ECE_GATE), hi + ECE_GATE))
    print("\n  一个**能用的产品**会怎样：")
    for s in WORKING_RATES:
        elig, ece = eligible_with(R, W, hi, s)
        print("     真实成功率 %.0f%% ⇒ ECE **%.4f** ⇒ eligible_for_c = **%s**"
              % (100 * s, ece, elig))
    print("  ⇒ **自优化层被绑在「产品表现得差」这个条件上。**")
    print("  ★ 机制本身是通的（正对照：predicted==actual ⇒ ECE 0 ⇒ 启用）——"
          "**坏的是预测量选错了对象**，不是没实现。")

    window_hi = hi + ECE_GATE
    print()
    if window_hi < floor:
        print("✗ **可启用窗口的上沿又掉了**：%.4f < 地板 %.4f" % (window_hi, floor))
        return 1
    print("✓ 未低于地板：窗口上沿 %.4f ≥ %.4f（**不代表 C 用得上** —— 见 Task #137）"
          % (window_hi, floor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
