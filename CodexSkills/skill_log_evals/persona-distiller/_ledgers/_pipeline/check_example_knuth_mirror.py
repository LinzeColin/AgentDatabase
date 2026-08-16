#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`example-knuth` 有**两份**，必须逐字节一致 —— 漂移门看不见这一对。

为什么要有这份文件
------------------
2026-08-17 修好随包那份 `example-knuth/` 的 8 个样例（它们把 TARGET 写死成
另一个会话的死路径）之后，按「修了源，派生副本还是坏的」回头查 ——
**评测侧还有一份**，用 git 里改动前的版本比对**逐字节完全相同**，是镜像。
它被 `_决策台账.md` 与 `_pipeline/RUNBOOK.md` 引用着：不同步就等于
「文档指着一份仍然坏的样例」。

★ 为什么不接进 `check_contract_drift`：那道门的镜像检查只比
  `scripts/` ↔ `references/pipeline/checkers/`，而且它的 `root` 是**单个 skill 目录**
  —— 这一对**跨了两棵树**（`registry/codex/…` vs `skill_log_evals/…`），
  **它的射程根本看不见**。所以判据要放在能同时看见两边的评测侧。

★ 先数出口个数再动手：全仓扫「跨树、文件名集合相同且 ≥3 个 .py」的目录对，
  **只有这 1 对** ⇒ 造通用框架是过度设计，一件专判就够。

用法
----
    python3 check_example_knuth_mirror.py --self-test
    python3 check_example_knuth_mirror.py --repo-root <仓根>
"""
import argparse
import hashlib
import pathlib
import sys

A_REL = "CodexSkills/registry/codex/persona-distiller/references/pipeline/example-knuth"
B_REL = "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/example-knuth"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compare(a: pathlib.Path, b: pathlib.Path) -> tuple:
    """→ (只在 A、只在 B、内容不同、比过的份数)。"""
    fa = {p.name for p in a.glob("*.py")}
    fb = {p.name for p in b.glob("*.py")}
    diff = [n for n in sorted(fa & fb) if sha(a / n) != sha(b / n)]
    return sorted(fa - fb), sorted(fb - fa), diff, len(fa & fb)


def selftest() -> int:
    import tempfile
    bad = []
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        x, y = t / "x", t / "y"
        x.mkdir(); y.mkdir()
        (x / "a.py").write_text("1\n", encoding="utf-8")
        (y / "a.py").write_text("1\n", encoding="utf-8")
        if compare(x, y) != ([], [], [], 1):
            bad.append("正例：完全相同却报出了差异")
        (y / "a.py").write_text("2\n", encoding="utf-8")
        if compare(x, y)[2] != ["a.py"]:
            bad.append("反例①：内容不同没报出来")
        (x / "b.py").write_text("3\n", encoding="utf-8")
        if compare(x, y)[0] != ["b.py"]:
            bad.append("反例②：只在 A 的没报出来")
        # ★ 反例③：**空目录不算通过**
        e1, e2 = t / "e1", t / "e2"
        e1.mkdir(); e2.mkdir()
        if compare(e1, e2)[3] != 0:
            bad.append("反例③：空目录的比过份数应为 0")
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d" % (4 - len(bad), 4))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    root = pathlib.Path(a.repo_root or ".").resolve()
    A, B = root / A_REL, root / B_REL
    print("扫描面：\n  A（随包）%s\n  B（评测）%s" % (A, B))
    if not A.is_dir() or not B.is_dir():
        print("  ✗ **有一侧不存在 —— 未核，不是通过**（A=%s B=%s）"
              % (A.is_dir(), B.is_dir()))
        return 1
    only_a, only_b, diff, n = compare(A, B)
    # ★ 空扫描面不算通过
    if n == 0 and not only_a and not only_b:
        print("  ✗ **两侧都没有 .py —— 未核，不是通过**")
        return 1
    print("  比过 **%d** 份" % n)
    if not (only_a or only_b or diff):
        print("  ✓ 两份 example-knuth 逐字节一致")
        return 0
    for x in only_a:
        print("  ✗ **只在随包那份里**：%s —— 评测侧缺件" % x)
    for x in only_b:
        print("  ✗ **只在评测那份里**：%s —— 随包侧缺件" % x)
    for x in diff:
        print("  ✗ **两份内容不同**：%s" % x)
    print("\n  ⇒ 它们是镜像（改动前实测 8/8 逐字节相同），且评测侧那份被"
          "`_决策台账.md` 与 `_pipeline/RUNBOOK.md` 引用 —— **不同步等于文档指着坏样例**。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
