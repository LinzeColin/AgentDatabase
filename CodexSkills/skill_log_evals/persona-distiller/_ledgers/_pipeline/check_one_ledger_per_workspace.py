#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一个工作区应当只有**一份**关键产物 —— 有两份时，每个 rglob 统计都会虚高。

为什么要有这份文件
------------------
2026-08-17 追一个「多扫 2 个」的报警，追到底是：

    wip-holmes-170      `_corpus/` 16 条｜`evidence/` 14 条｜共有 14｜只在 _corpus 的 2 条
    wip-blackstone-169  `_corpus/` 15 条｜`evidence/` 15 条｜**source_id 完全相同**

全库 **60 个账本文件、只分布在 58 个工作区**。而仓里 45 件判据引用 `source-ledger`，
多数用 `rglob` —— **两个工作区各被数两次**。我当天报的全库数因此虚高，
一天之内订正了三遍：

    3901（文件口径）→ 3872（去重但取错副本）→ **3870（取权威的 evidence/）**

★ **权威位置是 `evidence/`**，不是我以为的「取超集」：
  `persona-distiller/scripts/check_attribution_basis.py` 记着 2026-08-07 的一次误判 ——
  判据原先读 `research/source-universe.json`（`init_target` 的覆盖轴脚手架），
  于是「未挂 attribution」**永远报 0**；订正时写明真台账在
  `evidence/source-ledger.jsonl`，回退链是 `evidence/` → `research/…`，
  **`_corpus/` 根本不在链里**。两份 mtime 完全相同，**定权威的是仓里的记录，不是时间戳**。

## 为什么只报数、不设门

删哪一份是**数据处置**：`wip-holmes-170` 已判分（`results.jsonl` 非空）⇒ 属 ㊵ 冻结区，
动它要 Owner 定。本件把这件事从「看不见」变成「可复算」，永远 rc=0。

用法
----
    python3 check_one_ledger_per_workspace.py --self-test
    python3 check_one_ledger_per_workspace.py --corpora <_corpora>
"""
import argparse
import collections
import json
import pathlib
import sys

# 按工作区**只应有一份**的产物，以及各自的权威位置。
# ★ 2026-08-17 把射程从「只看账本」扩到这一组之后，实测虚高远不止账本那一处：
#       source-ledger.jsonl  60 文件 / 58 工作区 → 2 个重复
#       results.jsonl        62 文件 / 53 工作区 → **9 个重复**
#       cases.jsonl          62 文件 / 54 工作区 → **8 个重复**
#       claims.jsonl         59 文件 / 53 工作区 → **6 个重复**
#       meta.json / team-card.json                 0 个重复 ✓
#   其中 cases.jsonl 那一处直接让我报过的「带 rubric 的题目 1432 道」
#   虚高到 **1174** 的 122%（已订正）。
ARTIFACTS = {
    "source-ledger.jsonl": "evidence",   # 见文件头：仓里记录定的权威位置
    "results.jsonl": "evals",
    "cases.jsonl": "evals",
    "claims.jsonl": "evidence",
    "meta.json": None,
    "team-card.json": None,
}
AUTHORITATIVE = "evidence"          # 账本的权威位置（保留，供既有调用）


def scan(corp: pathlib.Path, name: str = "source-ledger.jsonl") -> dict:
    by_ws = collections.defaultdict(list)
    for f in sorted(corp.rglob(name)):
        ws = str(f.relative_to(corp)).split("/")[0]
        by_ws[ws].append(f)
    return dict(by_ws)


def ids_of(f: pathlib.Path) -> set:
    out = set()
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            sid = json.loads(line).get("source_id")
        except ValueError:
            continue
        if sid:
            out.add(sid)
    return out


def selftest() -> int:
    import tempfile
    bad = []
    with tempfile.TemporaryDirectory() as td:
        c = pathlib.Path(td)
        # 正例：一个工作区一份
        (c / "wip-a" / "workspaces" / "a" / "evidence").mkdir(parents=True)
        (c / "wip-a" / "workspaces" / "a" / "evidence" / "source-ledger.jsonl").write_text(
            '{"source_id":"src-1"}\n', encoding="utf-8")
        got = scan(c)
        if len(got.get("wip-a", [])) != 1:
            bad.append("正例：wip-a 应为 1 份，得到 %d" % len(got.get("wip-a", [])))
        # 反例①：两份且内容不同 → 必须发现
        (c / "wip-b" / "workspaces" / "b" / "evidence").mkdir(parents=True)
        (c / "wip-b" / "workspaces" / "b" / "_corpus").mkdir(parents=True)
        (c / "wip-b" / "workspaces" / "b" / "evidence" / "source-ledger.jsonl").write_text(
            '{"source_id":"src-1"}\n', encoding="utf-8")
        (c / "wip-b" / "workspaces" / "b" / "_corpus" / "source-ledger.jsonl").write_text(
            '{"source_id":"src-1"}\n{"source_id":"src-2"}\n', encoding="utf-8")
        got = scan(c)
        if len(got.get("wip-b", [])) != 2:
            bad.append("反例①：wip-b 应发现 2 份，得到 %d" % len(got.get("wip-b", [])))
        else:
            a, b = sorted(got["wip-b"], key=lambda p: p.parent.name)
            if ids_of(a) == ids_of(b):
                bad.append("反例①：两份内容本就不同，却判成相同")
        # 反例②：深一层布局也要数得到（8 个工作区就是这个形状）
        deep = c / "wip-c" / "workspaces" / "c" / "c" / "evidence"
        deep.mkdir(parents=True)
        (deep / "source-ledger.jsonl").write_text('{"source_id":"src-9"}\n', encoding="utf-8")
        if len(scan(c).get("wip-c", [])) != 1:
            bad.append("反例②：深一层布局没数到")
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d" % (4 - len(bad), 4))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.corpora:
        ap.error("要 --corpora，或只跑 --self-test")

    corp = pathlib.Path(a.corpora).resolve()
    print("扫描面：%s" % corp)
    print("\n══ 全部关键产物：文件数 vs 工作区数")
    for _name, _auth in ARTIFACTS.items():
        _b = scan(corp, _name)
        _files = sum(len(v) for v in _b.values())
        _multi = [k for k, v in _b.items() if len(v) > 1]
        print("   %-22s 文件 %3d｜工作区 %3d｜**多于一份 %s**%s"
              % (_name, _files, len(_b), ("%d 个" % len(_multi)) if _multi else "0 ✓",
                 ("　权威位置 `%s/`" % _auth) if _auth else ""))
        for k in sorted(_multi)[:3]:
            print("        · %-22s %s" % (k, "、".join(p.parent.name for p in _b[k])))
        if len(_multi) > 3:
            print("        · …另 %d 个" % (len(_multi) - 3))
    print("\n══ 源账本逐份细看")

    by_ws = scan(corp)
    files = sum(len(v) for v in by_ws.values())
    multi = {k: v for k, v in by_ws.items() if len(v) > 1}
    print("  账本文件 **%d** 份｜工作区 **%d** 个｜**多于一份的 %d 个**"
          % (files, len(by_ws), len(multi)))
    if not by_ws:
        print("  ✗ **一份账本都没扫到 —— 未核，不是通过**")
        return 0
    if not multi:
        print("  ✓ 每个工作区都只有一份账本（文件数 == 工作区数）")
        return 0
    for ws, fs in sorted(multi.items()):
        print("\n  ✗ **%s 有 %d 份**：" % (ws, len(fs)))
        sets = {}
        for f in fs:
            sets[f.parent.name] = ids_of(f)
            print("      %-10s %3d 条  %s" % (f.parent.name, len(sets[f.parent.name]),
                                              f.relative_to(corp)))
        names = sorted(sets)
        for i in range(len(names) - 1):
            x, y = names[i], names[i + 1]
            only_x, only_y = sets[x] - sets[y], sets[y] - sets[x]
            if not only_x and not only_y:
                print("      → **两份 source_id 完全相同**（纯重复）")
            else:
                print("      → 只在 %s 的 %d 条、只在 %s 的 %d 条"
                      % (x, len(only_x), y, len(only_y)))
        auth = [f for f in fs if f.parent.name == AUTHORITATIVE]
        print("      → 权威位置 `%s/`：%s" % (AUTHORITATIVE,
              "**在**" if auth else "**不在这几份里 —— 需人判**"))
    dup = sum(len(ids_of(f)) for fs in multi.values() for f in fs[1:])
    print("\n  ⇒ 用 `rglob` 的统计会**多算约 %d 条源**。" % dup)
    print("  ★ 本件**只报数不设门**：删哪一份是数据处置，")
    print("    其中已判分的工作区属 ㊵ 冻结区，动它要 Owner 定。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
