#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_mode_ladder_reachable.py —— **四档模式里，有几档是真够得到的？**

## 为什么有这件（2026-08-18）

`choose_mode` 有四档（single_expert / small_team / deep_team / swarm），
各自由一组阈值触发。拿**产物自己写的** `application_scenarios` 当任务
（60 条，不是我编的），逐条跑 `compile_task_graph` 量出来：

    mode 分布：single_expert **53** ／ small_team **7** ／ deep_team 0 ／ swarm 0

    domains    中位 1.000｜最大 4.000｜≥2（small_team 触发） 5/60
    complexity 中位 0.254｜**最大 0.494**｜≥0.38 6/60｜**≥0.76（deep_team）0/60**
    risk       中位 0.080｜**最大 0.270**｜**≥0.36（small_team）0/60**｜≥0.72 0/60

⇒ **`risk` 那条触发永远够不到**（它的最低门槛 0.36 比实测最大值 0.270 还高）；
  **`deep_team` 与 `swarm` 在这套语料上结构性不可达**。
  一个「团队 skill」在 88% 的任务上只坐 1 个人。

这是 `check_gate_reachability.py`（蒸馏侧：门槛设在评委实测天花板之上）
的**同形状问题，换了个主体**：那边是分数够不到门，这边是任务画像够不到档。
[[gate-above-judge-ceiling]]｜[[a-red-that-can-never-turn-green-is-not-a-signal]]

## ★★★ 本件**只报可达性，不建议改数字**

「把 risk 门槛从 0.36 调到 0.25」会让更多任务进 small_team ——
**那正是「为凑数放宽判据」**。要不要改档位，得先有一个东西本件给不了：
**证据说明多人比单人做得更好**。而遥测现在是 `sample_count=1`、
`eligible_for_c=False` —— 策略 C 未标定，**一条产出数据都没有**。

⇒ 本件的产出是**一句可证伪的话**：「第 N 档在当前语料上 0 次触发，
它的最低门槛比实测最大值高 X」。改不改由人拿别的证据决定。
[[no-blocking-on-gate-shortfall]]｜[[a-penalty-is-not-a-rule]]

## 任务从哪来（不许我自己编）

`team-index.json` 每个产物自带 `application_scenarios` —— 那是蒸馏流程写下的
「这个人适合办哪类事」。本件取它们当任务样本：**样本来自产品，不来自判据作者**。
[[fixtures-are-clean-because-i-wrote-them]]

退出码：0＝四档都够得到；1＝有档够不到；4＝取不到样本/编译器（未量）。
"""
import argparse
import collections
import json
import pathlib
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

#: `choose_mode` 里每一档的触发条件（**与 compile_task_graph.py 同源，改那边要改这里**）
#: 形如 {档: [(画像键, 最低值), …]}——满足**任一条**即触发该档。
TRIGGERS = {
    "swarm":       [("parallelizability", 0.72)],
    "deep_team":   [("complexity", 0.76), ("risk", 0.72), ("domains", 5)],
    "small_team":  [("complexity", 0.38), ("risk", 0.36), ("domains", 2)],
    "single_expert": [],          # 兜底档，天然可达
}


def reachability(profiles: list[dict]):
    """→ {档: {触发键: (门槛, 实测最大, 达到的条数)}}。纯函数，不跑子进程。

    ★ 「达到的条数」用的是**这一条触发**自己的门槛，不是整档的判定 ——
      整档还受前面几档的 if/elif 顺序影响，那是另一回事。本件只问
      「这条触发有没有可能被满足」。
    """
    out = {}
    n = len(profiles)
    for mode, conds in TRIGGERS.items():
        if not conds:
            continue
        row = {}
        for key, thr in conds:
            vals = [float(p.get(key) or 0) for p in profiles]
            row[key] = (thr, max(vals) if vals else 0.0,
                        sum(1 for v in vals if v >= thr), n)
        out[mode] = row
    return out


def unreachable(report: dict) -> list[str]:
    """→ 一次都触发不了的档。纯函数。"""
    bad = []
    for mode, row in report.items():
        if all(hit == 0 for (_thr, _mx, hit, _n) in row.values()):
            bad.append(mode)
    return bad


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    # ★ 数值逐字取自 2026-08-18 的 60 条真样本
    real = [{"complexity": 0.254, "risk": 0.080, "domains": 1, "parallelizability": 0.3}] * 54 + \
           [{"complexity": 0.494, "risk": 0.270, "domains": 4, "parallelizability": 0.5}] * 6
    rep = reachability(real)
    chk("★★★ 正例（真样本）：`risk` 最大 0.270 < 门槛 0.36 ⇒ 该触发 0 次命中",
        rep["small_team"]["risk"][2] == 0 and abs(rep["small_team"]["risk"][1] - 0.270) < 1e-9)
    chk("★★★ 正例：`deep_team` 三条触发全 0 ⇒ 判**不可达**",
        "deep_team" in unreachable(rep))
    chk("★★ 负例：`small_team` 有 `domains>=2` 命中 ⇒ **不判**不可达",
        "small_team" not in unreachable(rep))
    chk("★★ 命中数按**这一条触发**自己的门槛算（domains 4≥2 ⇒ 6 条）",
        rep["small_team"]["domains"][2] == 6)
    chk("★★★ 负例：全部远超门槛时，一档都不该判不可达",
        unreachable(reachability([{"complexity": 0.9, "risk": 0.9, "domains": 6,
                                   "parallelizability": 0.9}] * 3)) == [])
    chk("★ `single_expert` 是兜底档，不参与可达性判定", "single_expert" not in rep)
    chk("★ 空样本不炸（由调用方判未量，不在这里当通过）",
        reachability([])["deep_team"]["risk"][1] == 0.0)
    chk("★★ 缺字段按 0 计，不抛异常（画像多一个键少一个键都不该让判据崩）",
        reachability([{"domains": 3}])["small_team"]["domains"][2] == 1)
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def sample_tasks(index_path: pathlib.Path, limit: int) -> list[str]:
    """从产物自带的 `application_scenarios` 取任务。**不许判据作者自己编任务。**"""
    d = json.loads(index_path.read_text(encoding="utf-8"))
    out = []
    for p in d.get("products", []):
        for sc in (p.get("application_scenarios") or [])[:2]:
            if isinstance(sc, str) and len(sc) > 12:
                out.append(sc.split("：")[0][:60])
    return list(dict.fromkeys(out))[:limit]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry-root", default=str(ROOT))
    ap.add_argument("--limit", type=int, default=60, help="取多少条任务样本（默认 60）")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    root = pathlib.Path(a.registry_root)
    idx = root / "team-index.json"
    comp = root / "scripts" / "compile_task_graph.py"
    if not idx.is_file() or not comp.is_file():
        print("★ **未量，不是通过**（rc=4）—— 缺 %s"
              % ("team-index.json" if not idx.is_file() else "compile_task_graph.py"))
        return 4
    tasks = sample_tasks(idx, a.limit)
    print("样本：**%d** 条任务，全部取自产物自带的 `application_scenarios`"
          "（**不是判据作者编的**）" % len(tasks))
    if not tasks:
        print("★ **未量，不是通过**（rc=4）—— 一条样本都取不到")
        return 4

    profiles, modes, failed = [], collections.Counter(), 0
    for t in tasks:
        r = subprocess.run([sys.executable, str(comp), "--task", t],
                           capture_output=True, text=True)
        if r.returncode != 0:
            failed += 1
            continue
        try:
            g = json.loads(r.stdout)
        except ValueError:
            failed += 1
            continue
        pr = dict(g["profile"])
        pr["domains"] = len(pr.get("domains") or [])
        profiles.append(pr)
        modes[g["mode"]] += 1
    if not profiles:
        print("★ **未量，不是通过**（rc=4）—— %d 条样本一条也编译不出画像" % len(tasks))
        return 4
    print("  编译成功 %d 条｜失败 %d 条\n" % (len(profiles), failed))

    print("实际落到各档：%s" % "｜".join("%s %d" % (m, n) for m, n in
                                        sorted(modes.items(), key=lambda x: -x[1])))
    for k in ("domains", "complexity", "risk", "parallelizability"):
        vals = [float(p.get(k) or 0) for p in profiles]
        print("  %-18s 中位 %.3f｜**最大 %.3f**" % (k, statistics.median(vals), max(vals)))

    rep = reachability(profiles)
    print("\n逐档逐触发（门槛 vs 实测最大 vs 命中数）：")
    for mode in ("small_team", "deep_team", "swarm"):
        row = rep.get(mode) or {}
        print("  【%s】" % mode)
        for key, (thr, mx, hit, n) in row.items():
            flag = "  ← ★ **够不到**" if hit == 0 else ""
            print("     %-18s 门槛 %-6s 实测最大 %-7.3f 命中 %d/%d%s"
                  % (key, thr, mx, hit, n, flag))

    dead = unreachable(rep)
    print("\n可达 %d 档｜**不可达 %d 档**" % (len(rep) - len(dead), len(dead)))
    if not dead:
        print("\n✓ 每一档都有任务够得到")
        return 0
    print("\n✗ **这些档在当前语料上一次也触发不了**：%s" % "、".join(dead))
    print("\n  ★ 本件**不建议改门槛** —— 把 risk 从 0.36 调到 0.25 会让更多任务进 small_team，")
    print("    而那正是「为凑数放宽判据」。要不要改，得先有本件给不了的东西：")
    print("    **证据说明多人比单人做得更好**。遥测若仍是 `sample_count=1`／`eligible_for_c=False`，")
    print("    就还没有任何产出数据能支持这个决定。")
    print("  ★★ 本件的产出是一句**可证伪的话**：「第 N 档 0 次触发，最低门槛比实测最大值高 X」。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
