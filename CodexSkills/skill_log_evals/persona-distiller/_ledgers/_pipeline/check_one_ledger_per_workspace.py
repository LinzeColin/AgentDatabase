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
import re
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
HERE = pathlib.Path(__file__).resolve().parent
_ADJ: dict = {}
AUTHORITATIVE = "evidence"          # 账本的权威位置（保留，供既有调用）


def _adjudicated() -> dict:
    """去 `check_contract_drift.py` 里读**已裁定**的豁免名单。

    ★★★ 2026-08-17 的教训做成机器检查：我为「claims 6 处重复」查了半天，
    最后发现 `check_contract_drift.py` 早有 `CLAIMS_KNOWN` 豁免名单，成员**正是那 6 个**，
    并写着「权威的是 evidence/claims.jsonl，另一份是陈旧快照，**判决不受影响**，
    而**人照另一份数就会得到不同的数**；已判过分，不动」。
    —— **那句话预言了我当天的错**（我拿 rglob 数出 1432，权威口径 1174）。
    ⇒ 与其把教训写成散文，不如让本件**自己去读那份名单**，
      报重复时直接标「已裁定，不用再查」。
    """
    out = {}
    for rel in ("registry/codex/persona-distiller/scripts/check_contract_drift.py",):
        f = HERE.parents[3] / rel
        if not f.is_file():
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"CLAIMS_KNOWN\s*=\s*\{(.*?)\}", txt, re.S)
        if m:
            for name in re.findall(r'"(wip-[a-z0-9-]+)"', m.group(1)):
                # ★ 射程限定在它裁的那个产物上 —— `CLAIMS_KNOWN` 裁的是
                #   `claims.jsonl`，**套到 results/cases 上就是超范围**。
                out.setdefault(("claims.jsonl", name), []).append(
                    "CLAIMS_KNOWN@check_contract_drift")
    return out


def _keys(f: pathlib.Path) -> frozenset:
    """一份 jsonl/json 的键集合 —— 用来分辨「同物两份」与「同名不同物」。"""
    ks = set()
    txt = f.read_text(encoding="utf-8", errors="replace")
    for line in txt.splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict):
            ks |= set(d)
    if not ks:
        try:
            d = json.loads(txt)
            if isinstance(d, dict):
                ks = set(d)
        except ValueError:
            pass
    return frozenset(ks)


def _sha(f: pathlib.Path) -> str:
    import hashlib
    return hashlib.sha256(f.read_bytes()).hexdigest()


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
    global _ADJ
    _ADJ = _adjudicated()
    print("扫描面：%s" % corp)
    print("已裁定名单：**%d** 个工作区（读自 check_contract_drift.py）" % len(_ADJ))
    print("\n══ 全部关键产物：文件数 vs 工作区数")
    for _name, _auth in ARTIFACTS.items():
        _b = scan(corp, _name)
        _files = sum(len(v) for v in _b.values())
        _multi = [k for k, v in _b.items() if len(v) > 1]
        print("   %-22s 文件 %3d｜工作区 %3d｜**多于一份 %s**%s"
              % (_name, _files, len(_b), ("%d 个" % len(_multi)) if _multi else "0 ✓",
                 ("　权威位置 `%s/`" % _auth) if _auth else ""))
        # ★★ 「有重复」还不够行动 —— 要分清**逐字节相同**（删一份无风险）
        #   与**内容不同**（只能由人定）。2026-08-17 加，因为不分开的话
        #   这张表只能得出「有 23 处重复」，得不出「哪几处可以安全收掉」。
        # ★★★ **三层，不是两层。** 2026-08-17 我先按「同名 + 内容不同」就断言
        #   「两份副本，挑一份」，**错了**：打开 schema 才发现 `results.jsonl`
        #   那 9 处根本是**两种产物同名** ——
        #       evals/  键 case_id/judge_id/overall_score → 逐评委原始打分（128 行）
        #       wip-*/  键 baseline/candidate/case_id     → 成对记录（64 行）
        #   两者不冲突也不能互替，**不该删，该改名**。
        #   ⇒ 判「重复」之前先比**键集合**：键集合不同 = 同名不同物。
        same, diverge, notsame = [], [], []
        for k in sorted(_multi):
            fs = _b[k]
            if len({_sha(f) for f in fs}) == 1:
                same.append(k)
            elif len({_keys(f) for f in fs}) > 1:
                notsame.append(k)
            else:
                diverge.append(k)
        if same:
            print("        逐字节相同（删一份无风险）：**%d** 个　%s"
                  % (len(same), "、".join(same[:4]) + ("…" if len(same) > 4 else "")))
        if diverge:
            _open = [k for k in diverge if (_name, k) not in _ADJ]
            # ★ 不许同一节里先说「只能由人定」再说「已有裁定」——
            #   全部已裁定时就直接这么说。
            print("        同 schema、内容不同：**%d** 个；其中**未裁定的 %d 个**%s"
                  % (len(diverge), len(_open),
                     ("：" + "、".join(_open)) if _open else " —— **全部已有裁定**"))
        if notsame:
            print("        ★ **键集合不同 ⇒ 同名不同物，不该删、该改名：%d** 个　%s"
                  % (len(notsame), "、".join(notsame[:4]) + ("…" if len(notsame) > 4 else "")))
        _known = [k for k in _multi if (_name, k) in _ADJ]
        if _known:
            print("        ✓ **其中 %d 个已有裁定，不用再查**：%s"
                  % (len(_known), "、".join("%s（%s）" % (k, _ADJ[(_name, k)][0])
                                            for k in sorted(_known)[:3])
                     + ("…" if len(_known) > 3 else "")))
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
                # ★ 只说 source_id 层面 —— **不许说成「纯重复」**：
                #   blackstone 两份 source_id 一致，而键集合不同（同名不同物）。
                #   同一个工具里两句话打架，比少说一句更糟。
                _ks = {_keys(f) for f in fs}
                print("      → source_id **完全相同**；键集合 %s"
                      % ("也相同" if len(_ks) == 1 else "**不同 ⇒ 同名不同物，不是纯重复**"))
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
