#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同说 `small_team` 是 5–15 人，**而靠描述任务永远要不到 5–8 人**。

## 事实（2026-08-18 实测 @v0.0.0.38）

只靠推断（不给 `--size`／`--mode`），`persona_expert_target` 取得到的值：

    纯长度扫 1–240 词 ⇒ **{1, 9, 10, 11, 21, 22}**
    72 道 oracle      ⇒ **{10, 11, 12, 24, 25, 28}**

**2–8 这一整段，两种样本上一次都没出现过。** 用户拿到的要么是 **1 人**，
要么直接是 **9 人以上** —— 中间没有档。

## 成因（可从公式推，不靠样本）

    single_expert: size = 1                                              MODE_LIMITS (1, 1)
    small_team   : size = min(15, max(5, round(5 + 6c + 3r + |domains|)))  MODE_LIMITS (5, 15)
    进 small_team 的门：complexity ≥ 0.38

⇒ **2–4 结构上不可能**（single 恰好 1，small_team 地板 5）。
⇒ **5–8 合同允许但推断不到**：门一过（c=0.3838）、各分量落地板（r=0.08、domains=1），
   `5 + 6(0.3838) + 3(0.08) + 1 = 8.54 → **9**`。要 <9 就得 c<0.38，
   而那时候已经掉回 `single_expert` 了。

## 出口存在，但它要求的正是它要绕开的那件事

`--size 5..8` **是被接受的** —— 前提是**推断出来的模式已经是 `small_team`**。
任务短到落在 `single_expert` 时，`--size 6` 被拒：

    requested size 6 is invalid for inferred mode single_expert (valid: 1–1).

⇒ **想要 6 个人，你得先把任务写到足以拿 9 个人。**
   而且 `--size` 是运行时旗标，**不是用户在自然语言里能表达的东西**。

★ 本件**不要求补上那个洞**（改公式或改门会移动每一道任务的人数，属「门、席位一概不动」，
  见 Task #134）。本件钉的是「**推断可达的人数档位不许再少**」，
  外加钉住「合同区间与实际可达区间不一致」这件事本身还在被计算。
  [[a-red-that-can-never-turn-green-is-not-a-signal]]｜[[zero-hit-gates-must-prove-they-can-hit]]

用法：

    python3 check_team_size_ladder_has_no_hole.py
    python3 check_team_size_ladder_has_no_hole.py --baseline-reachable 99   # 看它红不红得了
    python3 check_team_size_ladder_has_no_hole.py --self-test
"""
from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

LADDER = tuple(range(1, 241))     # 纯长度探针的词数
BASELINE_REACHABLE = 6            # 2026-08-18 实测：{1, 9, 10, 11, 21, 22}
BASELINE_HOLE = tuple(range(2, 9))  # 实测取不到的那一段
MIN_DISTINCT = 2                  # 探针至少要分出两档，否则是探针死了


def gibberish(n: int) -> str:
    """**纯长度**探针：撞不上任何词表、域落兜底档、无连词无交付物词。"""
    return " ".join("zzq%d" % i for i in range(n))


def reachable_by_inference(compile_graph, ladder=LADDER) -> dict[int, int]:
    """→ {人数: 覆盖到它的词数个数}。只走推断，不给 --size / --mode。"""
    out: dict[int, int] = {}
    for n in ladder:
        size = compile_graph(gibberish(n), "auto", None)["persona_expert_target"]
        out[size] = out.get(size, 0) + 1
    return out


def explicit_size_accepted(compile_graph, sizes) -> dict[int, str]:
    """出口探针：任务已落在 `small_team` 时，显式 `--size` 收不收。"""
    task = gibberish(32)          # 刚过 small_team 门
    out = {}
    for s in sizes:
        try:
            g = compile_graph(task, "auto", s)
            out[s] = "接受 → %s / %d 人" % (g["mode"], g["persona_expert_target"])
        except Exception as exc:
            out[s] = "拒绝：%s" % str(exc)[:60]
    return out


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("   %s %s" % ("✓" if cond else "✗", name))
        ok = ok and bool(cond)

    sys.path.insert(0, str(HERE))
    import compile_task_graph as C

    reach = reachable_by_inference(C.compile_graph)
    chk("①★探针没死：推断出的人数至少 %d 档（现测 %d 档：%s）"
        % (MIN_DISTINCT, len(reach), sorted(reach)), len(reach) >= MIN_DISTINCT)
    hole = [k for k in BASELINE_HOLE if k in reach]
    chk("② 记录的空洞 %s 仍然是空的（现测落在洞里的：%s）"
        % (list(BASELINE_HOLE), hole or "无"), not hole)
    chk("③ 合同确实声明 small_team 下限是 5（现测 %s）" % (C.MODE_LIMITS["small_team"],),
        C.MODE_LIMITS["small_team"][0] == 5)
    chk("④ single_expert 恰好 1 人（%s）" % (C.MODE_LIMITS["single_expert"],),
        C.MODE_LIMITS["single_expert"] == (1, 1))

    # ★★ 从公式复算「门一过就 ≥9」，不靠样本
    g = C.compile_graph(gibberish(32), "auto", None)
    p = g["profile"]
    calc = round(5 + 6 * p["complexity"] + 3 * p["risk"] + len(p["domains"]))
    chk("⑤★★ 公式复算 == 产品读数（算得 %d，产品给 %d）"
        % (calc, g["persona_expert_target"]), calc == g["persona_expert_target"])

    # ★★★ 出口对照：显式 --size 5..8 必须被接受（证明这是**推断**的洞，不是合同的洞）
    exits = explicit_size_accepted(C.compile_graph, (5, 6, 7, 8))
    chk("⑥★★★ 出口在：small_team 下 --size 5..8 全部被接受（%s）"
        % ("是" if all(v.startswith("接受") for v in exits.values()) else exits),
        all(v.startswith("接受") for v in exits.values()))

    # ★★★ 反例：任务短到 single_expert 时，--size 6 必须被拒（出口要求的正是它要绕开的）
    try:
        C.compile_graph(gibberish(10), "auto", 6)
        refused = False
    except Exception:
        refused = True
    chk("⑦★★★ 反例：single_expert 下 --size 6 必须被拒 —— "
        "「想要 6 人，先把任务写到够拿 9 人」", refused)
    print("   —— self-test %s ——" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="推断可达的团队人数档位不许再少")
    ap.add_argument("--baseline-reachable", type=int, default=None)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    floor = BASELINE_REACHABLE if a.baseline_reachable is None else a.baseline_reachable
    sys.path.insert(0, str(HERE))
    import compile_task_graph as C

    reach = reachable_by_inference(C.compile_graph)
    if len(reach) < MIN_DISTINCT:
        print("★ **未量，不是通过**（rc=4）—— 探针只分出 %d 档，它死了" % len(reach))
        return 4

    print("只靠**推断**（不给 --size / --mode），纯长度扫 %d–%d 词："
          % (LADDER[0], LADDER[-1]))
    print("  取得到的人数：**%s**" % sorted(reach))
    print("  各值覆盖的词数段宽：%s" % dict(sorted(reach.items())))
    hole = [k for k in BASELINE_HOLE if k not in reach]
    print("  **%s 这一段一次都没出现**（合同却声明 small_team 是 %s）"
          % (list(BASELINE_HOLE), C.MODE_LIMITS["small_team"]))
    print("  ⇒ 用户拿到的要么 **1 人**，要么 **≥9 人**，中间没有档。")

    g = C.compile_graph(gibberish(32), "auto", None)
    p = g["profile"]
    print("\n成因（从公式推，不靠样本）：门一过（complexity %.4f）、各分量落地板"
          "（risk %.4f、domains %d）⇒ 5 + 6c + 3r + |domains| = %.2f ⇒ **%d 人**"
          % (p["complexity"], p["risk"], len(p["domains"]),
             5 + 6 * p["complexity"] + 3 * p["risk"] + len(p["domains"]),
             g["persona_expert_target"]))

    print("\n出口：small_team 下显式 `--size` —— %s"
          % "；".join("%d→%s" % (k, v.split("→")[0].strip())
                      for k, v in explicit_size_accepted(C.compile_graph, (5, 8)).items()))
    print("  ★ 但任务短到 `single_expert` 时 `--size 6` 被拒 ⇒ "
          "**想要 6 人，得先把任务写到足以拿 9 人**；且 `--size` 不是自然语言能表达的东西。")

    print()
    if len(reach) < floor:
        print("✗ **推断可达的人数档位少了**：%d < 地板 %d ⇒ 阶梯又塌了一档"
              % (len(reach), floor))
        return 1
    print("✓ 未低于地板：%d ≥ %d（**不代表阶梯是好的** —— 2–8 那个洞照旧，见 Task #134）"
          % (len(reach), floor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
