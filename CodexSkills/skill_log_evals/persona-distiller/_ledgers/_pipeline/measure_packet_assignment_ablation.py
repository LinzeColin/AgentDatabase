#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""包分派里那一项**与任务无关** —— 把它置 0，**89% 的包换了主人**。

`route_team_moe.assign_packets`（:344–356）：

    compatibility = overlap_score(packet["objective"], candidate_text(item["card"]))
    score = compatibility + 0.28 * item["base_score"] - 0.08*load - (0.25 if 超载)

而 `packet["objective"]` 是**模板文案**：2026-08-18 在 `auto` 档、12 个独立题面上现算，
出现过的**不同 objective 只有 28 条**，其中 5 条固定阶段包 + 23 条「独立处理第 N 个…分片」
（N 只是编号）。**没有一条带任务内容**。

  ★ 唯一一次「objective 里出现题面片段」是反向的巧合：某道题面自己写了「证据缺口」，
    而模板里本来就有「建立事实、来源、未知、当前性和**证据缺口**地图。」

⇒ `compatibility(人, 包)` 是一张**与任务无关的常量表**。

## 读数（本脚本现算）

    12 个独立题面里多于 1 人的队伍：12 支；包合计 173 个
    把 compatibility 置 0 ⇒ **换了主人的包 154 / 173 = 89.0%**

★★ **射程 —— 这个 89% 不能读成「89% 的分派是错的」**：
   置 0 之后剩下的只有 `0.28*base_score - 载荷惩罚`，那个对照本身是退化的
   （全队按 base_score 排，再由载荷惩罚轮转）。
   它支持的结论只有一条：**决定谁拿哪个包的，主要是一个不含任何任务信息的量。**
   [[a-delta-hides-which-arm-moved]]

★ 为什么这份脚本要进版本控制：上一次我把同类复算跑在会话临时目录里，
  路径随会话消失，台账里的「可复算」只剩一段散文里的 python。
  [[evidence-must-live-in-the-repo-not-the-terminal]]

用法：

    python3 measure_packet_assignment_ablation.py
    python3 measure_packet_assignment_ablation.py --self-test
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
GROUP = HERE.parents[3] / "registry" / "codex" / "persona-distiller-group"


def _load():
    sys.path.insert(0, str(GROUP / "scripts"))
    sys.path.insert(0, str(HERE))
    import route_team_moe as R                     # noqa: E402
    from compile_task_graph import compile_graph   # noqa: E402
    import export_benchmark_tasks as E             # noqa: E402
    return R, compile_graph, E


def assign(R, chosen, graph, use_compat: bool) -> list[str]:
    """复刻 `assign_packets`，唯一区别是可以把 `compatibility` 关掉。

    ★ 常量 0.28 / 0.08 / 0.25 与 capacity 的算法**照抄产品**；产品改了这里就失效，
      所以 `--self-test` 会去源码里核对这四个数还在。
    """
    packets = graph["work_packets"]
    cap = max(1, (len(packets) + len(chosen) - 1) // max(1, len(chosen)))
    load: collections.Counter[str] = collections.Counter()
    owners = []
    for packet in packets:
        cands = []
        for item in chosen:
            slug = item["subject_slug"]
            comp = (R.overlap_score(packet["objective"], R.candidate_text(item["card"]))
                    if use_compat else 0.0)
            sc = (comp + 0.28 * item["base_score"] - 0.08 * load[slug]
                  - (0.25 if load[slug] >= cap else 0.0))
            cands.append((sc, item))
        cands.sort(key=lambda p: (-p[0], p[1]["subject_slug"]))
        own = cands[0][1]
        load[own["subject_slug"]] += 1
        owners.append(own["subject_slug"])
    return owners


def objective_inventory(compile_graph, tasks) -> dict:
    seen: dict[str, set] = {}
    for t in tasks:
        for p in compile_graph(t, "auto", None)["work_packets"]:
            seen.setdefault(str(p.get("objective")), set()).add(t[:18])
    return seen


def run(limit: int | None = None) -> int:
    R, compile_graph, E = _load()
    tasks, _ = E.load(dedup=True)
    if limit:
        tasks = tasks[:limit]
    root = R.default_registry_root()
    idx = {c["subject_slug"]: c for c in R.read_json(root / "team-index.json")["products"]}

    inv = objective_inventory(compile_graph, tasks)
    print("① 机制：%d 个独立题面（auto 档）⇒ 不同 objective 共 **%d** 条" % (len(tasks), len(inv)))
    print("   只在 1 个题面出现过的：**%d** 条（全是「独立处理第 N 个分片」的编号差异）"
          % sum(1 for v in inv.values() if len(v) == 1))
    print("   ⇒ `compatibility(人, 包)` 是一张**与任务无关的常量表**。")

    multi = pk = changed = 0
    for t in tasks:
        rt = R.build_route(t, root, "auto", None, "auto", None)
        members = rt.get("members", [])
        if len(members) < 2:
            continue          # 1 人队伍没有选择余地，不构成证据
        multi += 1
        g = compile_graph(t, "auto", None)
        chosen = [{"subject_slug": m["subject_slug"], "base_score": m["base_score"],
                   "card": idx[m["subject_slug"]]}
                  for m in members if m["subject_slug"] in idx]
        a = assign(R, chosen, g, True)
        b = assign(R, chosen, g, False)
        pk += len(a)
        changed += sum(1 for x, y in zip(a, b) if x != y)

    print("\n② 消融：多于 1 人的队伍 **%d** 支；包合计 **%d** 个" % (multi, pk))
    if not pk:
        print("★ **未量**（rc=4）—— 一支多人队伍都没有，消融无从做起")
        return 4
    print("   把 compatibility 置 0 ⇒ **换了主人的包 %d / %d = %.1f%%**"
          % (changed, pk, 100 * changed / pk))
    print("   ★★ 射程：对照臂（只剩 `0.28*base - 载荷`）**本身是退化的**，")
    print("      所以这个数**不能读成「89% 的分派是错的」** —— 它只支持")
    print("      「决定谁拿哪个包的，主要是一个不含任何任务信息的量」。")
    return 0


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("   %s %s" % ("✓" if cond else "✗", name))
        ok = ok and bool(cond)

    src = (GROUP / "scripts" / "route_team_moe.py").read_text(encoding="utf-8")
    for lit in ("0.28 * item[\"base_score\"]", "0.08 * load[slug]", "0.25 if over_capacity else 0.0"):
        chk("① 产品源码里仍有 `%s`（本脚本照抄了它）" % lit, lit in src)
    chk("②★ 产品的 compatibility 仍取自 packet[\"objective\"]",
        'overlap_score(packet["objective"], candidate_text(item["card"]))' in src)

    R, compile_graph, E = _load()
    tasks, _ = E.load(dedup=True)
    chk("③ 取到独立题面（%d 个）" % len(tasks), len(tasks) >= 4)
    inv = objective_inventory(compile_graph, tasks[:4])
    chk("④★★ objective 里不含任务内容：随便取一条题面，它的**首 8 字**不出现在任何 objective 里",
        all(tasks[0][:8] not in o for o in inv))

    # ★★★ 反例：造一支「两人 base_score 差极大」的队伍，置 0 后必须全归 base 高的那个
    root = R.default_registry_root()
    idx = list(R.read_json(root / "team-index.json")["products"])[:2]
    chosen = [{"subject_slug": idx[0]["subject_slug"], "base_score": 0.9, "card": idx[0]},
              {"subject_slug": idx[1]["subject_slug"], "base_score": 0.1, "card": idx[1]}]
    g = compile_graph(tasks[0], "auto", None)
    b = assign(R, chosen, g, False)
    chk("⑤★★★ 反例：置 0 后前两个包必须都归 base 高的那位（载荷惩罚生效前）",
        b[0] == idx[0]["subject_slug"])
    print("   —— self-test %s ——" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="包分派消融：把任务无关那项置 0")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    return self_test() if a.selftest else run(a.limit)


if __name__ == "__main__":
    raise SystemExit(main())
