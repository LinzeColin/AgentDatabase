#!/usr/bin/env python3
"""**「纸面道」**：某一道的全部支撑都来自「一条同时挂多道」的源。

## 撞出它的那一次（2026-08-12，#172 Brandeis 排期时）

Brandeis 的材料几乎全是最高法院意见。问「`min_lanes 3` 过不过」时读了判据
（`quality_check.evaluate_sources`）才发现：**`lane` 数的是每条源的 `dimensions` 字段，
而一条源可以同时挂多个 lane，每个都单独计数。**

⇒ 把**一卷** U.S. Reports 标成 `["decisions","expression"]`，**它一条就补上两道**；
  再加两本庭外著作，`min_lanes 3` **纸面上就过了**——实质只是「一种材料 + 两本书」。

★★ 这是 Vavilov #126 的**隐藏版**：他是明着凑不满三道被拦下，
  而这条路是**靠字段凑满三道混过去**。
  门只做分档字段的算术，**不问分档对不对**（[[related-to-him-is-not-written-by-him]]）。

## 判据怎么定义「纸面道」

对每个工作区，只看 `split == train` 且非 `tier U` / 非 `extraction_status failed` 的源
（**与 `quality_check` 的 `usable` 口径逐字相同**，口径不一致的比较没有意义）：

    某道 L 是「纸面道」  ⟺  覆盖 L 的源里，**没有任何一条是只挂 L 的**

也就是说：**这道没有一条专属的源**，它的存在完全依附于别的道。

## 它**不**做的事

- **不**禁止一条源挂多道。真有跨道的材料（书信里既谈决策又见声口）。
- **不**改 `min_lanes` 本身。它只报「你这三道里有几道是纸面的」。
- ★ **不**替人裁决要不要因此拒发——那是产物侧的决定。

## 冻结名单

`KNOWN` 是 2026-08-12 全库实测的四个。**四个都不在 registry**
（`subject_slug` 与 `canonical_name` 两种匹配都查过），**没有已发布产物受影响**。
它们的处置早已定（Gantt/Nasmyth/Rosenhain 记拒发、Pacioli 记延后），
**重开等于改动已判过的东西，按红线不动**。

本判据要挡的是**新增**。
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import tempfile

ROOT_DEFAULT = pathlib.Path(__file__).resolve().parent.parent

# 2026-08-12 实测。**冻结，不是待办**——见 docstring。
KNOWN = {
    # ★★ 这份名单**第一版是错的**：射程只扫了 `*/workspaces/*/evidence/`，
    #   漏掉 `*/workspaces/<slug>/<slug>/evidence/` 与 `_corpus/`，
    #   于是报「4 个」而真值是 **9 个**。抓到它的是变异测试，不是读代码。
    "wip-galen-101", "wip-gantt-156", "wip-holmes-170", "wip-livermore-100",
    "wip-nasmyth-153", "wip-pacioli-161", "wip-rosenhain-138", "wip-sorby-133",
    "wip-steinhardt-98",
}
# ★★★ 这 9 个里 **2 个是已发布产物**（按 team-index 的 102 个逐个精确核过）：
#   · **Jesse Livermore #100**  6 道里 5 道是纸面的；且 532 条可用源里
#     **516 条挂同一个三元组 decisions+external+timeline（97.0%）**
#   · **Michael Steinhardt #98** 6 道里 5 道是纸面的；最大组合只占 32.7%，分布是散的
#   其余 7 个都不在 registry（Galen/Gantt/Holmes/Nasmyth/Pacioli/Rosenhain/Sorby）。
#   ⇒ **要不要因此重估这两个已发布产物，是产物侧的决定，判据给不出。**
#     详见 `_ledgers/_纸面道-2026-08-12.md`。


def _usable(record: dict) -> bool:
    """与 `quality_check.evaluate_sources` 的 `usable` 逐字同口径。

    ★ 不许自己另起一套：口径不同的两个数放在一起比，比出来的差额是假的
      （同型教训：判据报「Python脚本数 130」而我按自己口径写了 242）。
    """
    return (record.get("split") == "train"
            and record.get("tier") != "U"
            and record.get("extraction_status") != "failed")


def analyse(ledger_lines: list[str]) -> dict:
    lane_all: dict[str, int] = collections.defaultdict(int)
    lane_solo: dict[str, int] = collections.defaultdict(int)
    combos: dict[tuple, int] = collections.Counter()
    for line in ledger_lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not _usable(record):
            continue
        dims = sorted({d for d in (record.get("dimensions") or []) if d})
        combos[tuple(dims)] += 1
        for d in dims:
            lane_all[d] += 1
            if len(dims) == 1:
                lane_solo[d] += 1
    covered = sorted(lane_all)
    paper = sorted(d for d in lane_all if lane_solo.get(d, 0) == 0)
    # ★★ 第二个、而且更锐的信号：**最大 dimensions 组合的占比**。
    #   Livermore #100 实测 532 条可用源里 **516 条挂着同一个三元组
    #   `decisions+external+timeline`（97.0%）**——那不是逐条判断，是**批量刷上去的**。
    #   Steinhardt #98 同样有 5 个纸面道，而最大组合只占 32.7%，组合分布是散的。
    #   ⇒ **两者性质不同，不能并成一条报。** 只报「纸面道」会把它们说成一回事。
    top = max(combos.items(), key=lambda kv: kv[1]) if combos else ((), 0)
    total = sum(combos.values())
    return {"覆盖的道": covered, "纸面道": paper,
            "去掉纸面道后还剩": len(covered) - len(paper),
            "可用源": total,
            "最大组合": "+".join(top[0]) if top[0] else "",
            "最大组合占比": (top[1] / total) if total else 0.0}


def check(corpora: pathlib.Path, min_lanes: int = 3) -> int:
    if not corpora.is_dir():
        print(f"· 语料根不在本树（{corpora}）——**未核，不是通过**")
        return 0
    # ★★★ 这里原写 `glob("*/workspaces/*/evidence/source-ledger.jsonl")`——**漏扫了四分之一**。
    #   真实布局有两种：`<wip>/workspaces/<slug>/evidence/`（25 份）与
    #   `<wip>/workspaces/<slug>/<slug>/evidence/`（9 份，`init_target` 会多建一层），
    #   另有 3 份在 `_corpus/`（那两个「一个工作区两份账本」的人物）。**rglob 共 37 份。**
    #   ★ 抓到它的**不是我读代码，是变异测试**：我给 #172 造了一个纸面道，
    #     判据却报「没有新增」——因为它根本没看见那个工作区。
    #   ⇒ 与 `check_scan_reach` 那次同型：**「扫了几个」对得上，而「扫的是谁」是错的。**
    ledgers = sorted(corpora.rglob("source-ledger.jsonl"))
    per_ws: dict[str, list[str]] = collections.defaultdict(list)
    for led in ledgers:
        rel = led.relative_to(corpora)
        per_ws[rel.parts[0]].append(str(rel))
    rows = []
    for ws, paths in sorted(per_ws.items()):
        lines: list[str] = []
        for rel in paths:
            lines += (corpora / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        res = analyse(lines)
        res["账本份数"] = len(paths)
        if res["覆盖的道"]:
            rows.append((ws, res))
    multi = [ws for ws, r in rows if r["账本份数"] > 1]
    print(f"扫了 {len(ledgers)} 份账本 / {len(rows)} 个有 train 源的工作区"
          + (f"（其中 {len(multi)} 个有多份账本，已合并：{multi}）" if multi else ""))
    hits = [(ws, r) for ws, r in rows if r["纸面道"]]
    print(f"**存在纸面道的：{len(hits)} 个**")
    new = [(ws, r) for ws, r in hits if ws not in KNOWN]
    fixed = sorted(KNOWN - {ws for ws, _ in hits})
    for ws, r in hits:
        drop = "  ★★ 去掉纸面道就掉到 %d 道（门 %d）" % (r["去掉纸面道后还剩"], min_lanes) \
            if r["去掉纸面道后还剩"] < min_lanes else ""
        tag = "（冻结名单内）" if ws in KNOWN else "**新增**"
        # ★★ 判「像批量刷的」要**两个条件同时成立**：占比高 **且** 那个组合本身含 ≥2 道。
        #   我第一版只看占比 ≥80%，**当天就自己量出误报率 4/5 = 80%**：
        #     Carver 94.7% 的最大组合是 `writings`、Semmelweis 88.1% 是 `external`、
        #     Adams 87.0% 是 `conversations`、Bessemer 83.3% 是 `writings`
        #     ——那只是**语料本来就以一种材料为主**，完全正常，不是没逐条判断。
        #   加上 `≥2 道` 之后全库只剩 **Livermore 一个**（97.0%，三元组）。
        #   ⇒ [[read-the-hits-before-reporting-the-rate]]：报率之前先读命中。
        ndim = len(r["最大组合"].split("+")) if r["最大组合"] else 0
        blanket = ("  ★★★ **最大组合 %s（%d 道）占 %.1f%%（%d 条源）"
                   "——一个多道组合刷在几乎所有源上，这不像逐条判断**"
                   % (r["最大组合"], ndim, 100 * r["最大组合占比"], r["可用源"])
                   ) if (r["最大组合占比"] >= 0.80 and ndim >= 2) else ""
        print(f"   {ws:<26} 覆盖 {len(r['覆盖的道'])} 道｜纸面 {len(r['纸面道'])}："
              f"{'+'.join(r['纸面道'])}{drop} {tag}{blanket}")
    if fixed:
        print(f"\n✓ 冻结名单里已不再有纸面道的 {len(fixed)} 个：{fixed}"
              f"\n  —— **补好了记得从 KNOWN 里删掉**，否则名单越来越假")
    if new:
        print(f"\n✗ **新出现 {len(new)} 个工作区有纸面道**——"
              "那一道没有任何一条专属的源，它的存在完全依附于别的道。"
              "\n  ⇒ 若它是靠这道才凑够 min_lanes，**这个门是纸面上过的**。"
              "\n  参照 #172 Brandeis 的做法：按 `opinion_type` 把一卷拆成两条源记录，"
              "\n  让 decisions 与 expression 各有专属的源。")
        return 1
    print("\n✓ 没有新出现的纸面道")
    return 0


def self_test() -> int:
    bad = []

    def row(sid, dims, split="train", tier="P1", status="ok"):
        return json.dumps({"source_id": sid, "split": split, "tier": tier,
                           "extraction_status": status, "dimensions": dims},
                          ensure_ascii=False)

    # A 负对照：expression 只由「同时挂 decisions+expression」的那条撑着 → 纸面道
    got = analyse([row("a", ["decisions"]), row("b", ["decisions", "expression"]),
                   row("c", ["writings"])])
    if got["纸面道"] != ["expression"]:
        bad.append(f"A·靠多道源撑起来的 expression 未被判为纸面道（实得 {got}）")
    if got["去掉纸面道后还剩"] != 2:
        bad.append(f"A′·去掉纸面道后应剩 2 道（实得 {got['去掉纸面道后还剩']}）")

    # B 正对照：每道各有专属源 → 一个纸面道都没有
    got = analyse([row("a", ["decisions"]), row("b", ["expression"]),
                   row("c", ["writings"]), row("d", ["decisions", "expression"])])
    if got["纸面道"]:
        bad.append(f"B·每道都有专属源，却报出纸面道（实得 {got['纸面道']}）")

    # C ★ 口径对照：**holdout / tier U / 抽取失败的行不许参与**。
    #   这三条若被算进来，一条 holdout 就能把纸面道「洗白」。
    got = analyse([row("a", ["decisions"]), row("b", ["decisions", "expression"]),
                   row("h", ["expression"], split="holdout"),
                   row("u", ["expression"], tier="U"),
                   row("f", ["expression"], status="failed")])
    if got["纸面道"] != ["expression"]:
        bad.append(f"C·holdout/U/failed 的行被算进了专属源（实得 {got}）")

    # D 边界：一条源挂三道且是唯一的源 → 三道**全是**纸面道
    got = analyse([row("a", ["decisions", "expression", "writings"])])
    if sorted(got["纸面道"]) != ["decisions", "expression", "writings"]:
        bad.append(f"D·一条源顶三道时三道都应是纸面道（实得 {got}）")
    if got["去掉纸面道后还剩"] != 0:
        bad.append("D′·全是纸面道时应剩 0 道")

    # D″ ★ 单道组合占比再高，也**不许**被说成「批量刷」——这是当天量出的 80% 误报。
    #   （这里只验 analyse 给出的量；文案在 check() 里按 `ndim>=2` 判。）
    got = analyse([row(f"s{i}", ["writings"]) for i in range(19)] + [row("x", ["external"])])
    if got["最大组合"] != "writings" or abs(got["最大组合占比"] - 0.95) > 1e-9:
        bad.append(f"D″·单道组合的占比算错（实得 {got['最大组合']} {got['最大组合占比']:.4f}）")
    if len(got["最大组合"].split("+")) != 1:
        bad.append("D″′·单道组合被算成多道")

    # E 反向：空账本不许崩，也不许报出东西
    got = analyse([])
    if got["覆盖的道"] or got["纸面道"]:
        bad.append(f"E·空账本报出了东西（实得 {got}）")

    # F ★★ 真跑一遍 `check()`（不是只调 analyse）——今天刚立的规矩：
    #    自测要走到判定函数，不能只验配料。
    with tempfile.TemporaryDirectory() as td:
        corp = pathlib.Path(td) / "corpora"
        ev = corp / "wip-zz-999" / "workspaces" / "zz" / "evidence"
        ev.mkdir(parents=True)
        (ev / "source-ledger.jsonl").write_text(
            "\n".join([row("a", ["decisions"]), row("b", ["decisions", "expression"]),
                       row("c", ["writings"])]) + "\n", encoding="utf-8")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(corp)
        out = buf.getvalue()
        if rc != 1:
            bad.append(f"F·check() 遇到新增纸面道应返回 1（实得 {rc}）")
        if "wip-zz-999" not in out or "expression" not in out:
            bad.append("F′·check() 没有点名是哪个工作区／哪一道")
        # F‴ ★★★ **「≥2 道」那个条件必须由夹具来验，production 验不出来。**
        #   实测：在真实语料上去掉该条件，全库输出**一个字都不变**（1 → 1）——
        #   因为没有任何现存工作区同时满足「有纸面道」与「单道组合占比 ≥80%」。
        #   **我第一次的变异因此是无效的**：数据表达不出这个差别。
        #   这个夹具造的正是那个形状：95% 单道 `writings` + 5% `writings+expression`
        #   ⇒ `expression` 是纸面道，而最大组合是**单道** `writings`、占比 95%。
        #   ⇒ [[counter-example-red-can-be-red-by-coincidence]] 的反面：
        #     **变异没红，也可能是数据碰巧盖不到那条分支。**
        corp2 = pathlib.Path(td) / "c2"
        ev2 = corp2 / "wip-fx-002" / "workspaces" / "fx" / "evidence"
        ev2.mkdir(parents=True)
        (ev2 / "source-ledger.jsonl").write_text(
            "\n".join([row(f"w{i}", ["writings"]) for i in range(19)]
                      + [row("x", ["writings", "expression"])]) + "\n", encoding="utf-8")
        buf3 = io.StringIO()
        with contextlib.redirect_stdout(buf3):
            check(corp2)
        out3 = buf3.getvalue()
        if "expression" not in out3:
            bad.append("F‴·95%单道+5%双道 时 expression 应被判为纸面道")
        if "像逐条判断" in out3:
            bad.append("F‴′·**单道组合占比 95% 被误报成「批量刷」**——`ndim>=2` 那个条件没起作用")

        # F″ 语料根不存在 → 明说「未核」，**不许静默当通过**
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc2 = check(pathlib.Path(td) / "nope")
        if "未核" not in buf2.getvalue():
            bad.append("F″·语料根不存在时没有明说「未核，不是通过」")

    for b in bad:
        print(f"✗ {b}")
    if bad:
        print(f"负对照未过：{len(bad)} 项")
        return 1
    print("负对照通过：A 纸面道抓出｜B 专属源不误报｜C holdout/U/failed 不参与｜"
          "D 一条顶三道全是纸面｜**D″ 单道组合占比高不算批量刷**｜E 空账本｜"
          "F **真跑 check() 并点名**")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="纸面道：某道的全部支撑都来自多道源")
    ap.add_argument("--corpora", type=pathlib.Path, default=None,
                    help="语料根；默认按 skill 根推出 skill_log_evals/persona-distiller/_corpora")
    ap.add_argument("--min-lanes", type=int, default=3)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    corpora = a.corpora or (ROOT_DEFAULT.parent.parent.parent
                            / "skill_log_evals/persona-distiller/_corpora")
    return check(corpora, a.min_lanes)


if __name__ == "__main__":
    sys.exit(main())
