#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**文档里写「怎么重跑」，那个脚本得真的在用户拿到的包里。**

## 抓到它的那一次（2026-08-18）

`SKILL.md` 有一张「已测量的边界」表，八行，每行一列「怎么重跑」——
这张表是本 skill 最诚实的一页，也是**读文档的人据以决定用不用**的那一页。
以读者视角逐个点名的脚本查过去：

    ✓ 包内   audit_persona_fleet_for_team.py｜record_team_outcome.py｜run_tests.py
    ✗ 包外   measure_routing_discrimination.py
    ✗ 包外   check_benchmark_mode_accuracy.py
    ✗ 包外   check_registered_products_have_delta_evidence.py
    ✗ 包外   report_expert_team_state.py

四个都在 `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/` ——
那是**开发台账树，不随 skill 分发**。

⇒ 装了这个 skill 的人，**八行里有四行的「怎么重跑」在他机器上不存在**。
  仓里全绿，装进包里够不着。
  [[green-in-the-repo-dead-in-the-package]]｜[[pointer-only-handoff-makes-the-pointer-load-bearing]]

★ 我第一次查是 `python3 scripts/check_benchmark_mode_accuracy.py`，得
  `can't open file`，而**后面接了 `| head` ⇒ `$?` 印出 0** ——
  差点把「文件不存在」读成「跑通了」。[[pipe-to-tail-hides-the-exit-code]]

## 它不按措辞判，按**闭集合**判

「这一条是不是已经披露过了」如果去文里找「包外」「不随包分发」之类的字样，
就成了追别人的措辞，改一次文案漏一次。
本件改成：包外但**已在下面这张明码表里**的算通过，其余算未披露。
表要改就得改代码，改代码就会被 review 看到。
[[checkers-must-key-on-a-closed-set-not-on-wording]]｜[[a-checker-that-chases-someone-elses-wording-always-lags]]

## 射程与守卫

* 只看**随包分发的 `.md`**（包根目录下的），不看 `tests/`、不看台账树。
* **零命中报未核**：一个脚本名都没扫到 ⇒ rc=4，不是通过
  （文档改版把反引号去掉，本件会哑，那时它必须喊而不是绿）。
  [[zero-hit-gates-must-prove-they-can-hit]]
* 判「在不在包内」用 **realpath 前缀**，不做子串匹配。
  [[path-prefix-checks-need-realpath]]

退出码：0＝都在包内或已明码披露；1＝有未披露的包外脚本；4＝一个都没扫到（未核）。
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent

#: ★★★ **告诉用户「去跑这个」的文档** —— 只有这几份判红。
#: 缺陷的形状是「文档叫用户跑一个他没有的脚本」，所以判定面就是**指令性文档**。
INSTRUCTION_DOCS = ("SKILL.md", "README.md", "CANONICAL-ROOT-ROUTE.md")

#: **历史性文档** —— 只报告，不判红。CHANGELOG 记的是「当时用什么工具做了什么」，
#: 不是「你现在去跑它」；而且它必然会提到**举例用的占位名**和**后来被移走的工具**。
#: ★ 这不是为了让灯变绿才划的线：本件第一版把 CHANGELOG 也算进判定面，
#:   于是我自己写在 v0.0.0.31 条目里的三个**举例名**（讨论自测负对照时写的）
#:   被判成「未披露的包外脚本」——**误报，而且方向是逼我去改一段正确的散文**。
#:   ⇒ 分成两栏：指令性文档判红，历史文档只报。**两边都印，不藏。**
#:   [[a-signal-that-both-overfires-and-underfires]]｜[[a-gates-scan-set-is-smaller-than-reality]]
HISTORY_DOCS = ("CHANGELOG.md",)

#: `` `xxx.py` `` —— 只认反引号里的，避免把散文里的普通词当脚本名。
CITED = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*\.py)`")

#: ★★★ **已明码披露「在包外」的脚本 → 它实际在哪**（闭集合，不靠措辞识别）。
#: 往这里加一条，就等于承诺文档里同时写清「它不随包分发、在哪儿」。
#: ★ 值是**路径**不是 True —— 判据的输出要能直接告诉用户去哪找，
#:   否则它只说了「你跑不了」，没说「那怎么办」。
#:   [[error-message-points-at-an-exit-that-isnt-there]]
OUT_OF_PACKAGE_ACKNOWLEDGED = {
    # ① 开发台账树，**从不随任何 skill 分发**
    "measure_routing_discrimination.py":
        "skill_log_evals/persona-distiller/_ledgers/_pipeline/（开发台账树，不分发）",
    "check_benchmark_mode_accuracy.py":
        "skill_log_evals/persona-distiller/_ledgers/_pipeline/（开发台账树，不分发）",
    "check_registered_products_have_delta_evidence.py":
        "skill_log_evals/persona-distiller/_ledgers/_pipeline/（开发台账树，不分发）",
    "report_expert_team_state.py":
        "skill_log_evals/persona-distiller/_ledgers/_pipeline/（开发台账树，不分发）",
    "measure_packet_assignment_ablation.py":
        "skill_log_evals/persona-distiller/_ledgers/_pipeline/（开发台账树，不分发）",
    # ② **上游 skill 的构建工具** —— 随 persona-distiller 分发，不随本 skill
    "build_release_bundle.py": "registry/codex/persona-distiller/scripts/（上游 skill，另装）",
    "bump_version.py":         "registry/codex/persona-distiller/scripts/（上游 skill，另装）",
    "self_check.py":           "registry/codex/persona-distiller/scripts/（上游 skill，另装）",
}


def in_package(name: str, pkg: pathlib.Path) -> bool:
    """`name` 能在包内找到吗。★ 用 realpath 前缀判，不做子串。"""
    root = os.path.realpath(str(pkg))
    for p in pkg.rglob(name):
        if os.path.realpath(str(p)).startswith(root + os.sep):
            return True
    return False


def scan(pkg: pathlib.Path, docs=None) -> tuple[dict, int]:
    """→ `({脚本名: {"docs": [...], "in_pkg": bool}}, 扫过的文档数)`。

    `docs=None` ⇒ 包根下全部 `.md`（自测与「历史文档」栏用）；
    传入文件名元组则只扫那几份。★ `tests/` 与台账树一律不进扫描面。
    """
    found: dict[str, dict] = {}
    n_docs = 0
    pool = (sorted(pkg.glob("*.md")) if docs is None
            else [pkg / d for d in docs if (pkg / d).is_file()])
    for doc in pool:
        n_docs += 1
        try:
            text = doc.read_text(encoding="utf-8")
        except OSError:
            continue
        for name in set(CITED.findall(text)):
            row = found.setdefault(name, {"docs": [], "in_pkg": None})
            row["docs"].append(doc.name)
    for name, row in found.items():
        row["in_pkg"] = in_package(name, pkg)
    return found, n_docs


def self_test() -> int:
    import tempfile
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %s %s" % ("✓" if cond else "**✗**", name))

    print("自测：")
    with tempfile.TemporaryDirectory() as td:
        pkg = pathlib.Path(td)
        (pkg / "scripts").mkdir()
        (pkg / "scripts" / "inside.py").write_text("# x", encoding="utf-8")
        (pkg / "SKILL.md").write_text(
            "跑 `inside.py` 和 `outside.py`。", encoding="utf-8")
        found, n_docs = scan(pkg)
        chk("① 扫到两个被点名的脚本", set(found) == {"inside.py", "outside.py"})
        chk("② 包内的判 in_pkg=True", found["inside.py"]["in_pkg"] is True)
        chk("③ **包外的判 in_pkg=False**", found["outside.py"]["in_pkg"] is False)
        chk("④ 文档数记对（1 份）", n_docs == 1)

        # ★ 负对照①：**子串不算在包内** —— `side.py` 不该被 `inside.py` 满足
        (pkg / "README.md").write_text("还有 `side.py`。", encoding="utf-8")
        found2, _ = scan(pkg)
        chk("⑤ ★ 负对照：`side.py` 不因 `inside.py` 存在而算在包内",
            found2["side.py"]["in_pkg"] is False)

        # ★ 负对照②：不许把 tests/ 下的文档也算成随包文档
        (pkg / "tests").mkdir()
        (pkg / "tests" / "NOTES.md").write_text("`only_in_tests.py`", encoding="utf-8")
        found3, n3 = scan(pkg)
        chk("⑥ ★ 负对照：`tests/` 下的 .md 不进扫描面（仍是 2 份文档）",
            n3 == 2 and "only_in_tests.py" not in found3)

        # ★ 零命中要判未核
        with tempfile.TemporaryDirectory() as td2:
            empty = pathlib.Path(td2)
            (empty / "SKILL.md").write_text("一个脚本名都没有。", encoding="utf-8")
            f4, n4 = scan(empty)
            chk("⑦ ★★ 零命中：扫到 0 个脚本名（由 main 判 rc=4 未核）",
                f4 == {} and n4 == 1)

    # ★ 闭集合本身：不许把包内的也塞进「已披露包外」名单（那会掩盖真相）
    real, _ = scan(PKG)
    mislabeled = [n for n in OUT_OF_PACKAGE_ACKNOWLEDGED
                  if real.get(n, {}).get("in_pkg") is True]
    chk("⑧ ★★★ 名单里没有「其实在包内」的条目（%s）"
        % (",".join(mislabeled) or "空"), not mislabeled)

    print("自测：%s" % ("**全过**" if ok else "**有失败**"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--package-root", default=str(PKG))
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    pkg = pathlib.Path(a.package_root).resolve()
    found, n_docs = scan(pkg, INSTRUCTION_DOCS)
    print("# 随包文档里点名的脚本，在不在用户拿到的包里\n")
    print("**判定面**：%s —— 实到 **%d** 份（这几份是**告诉用户去跑什么**的）"
          % ("、".join("`%s`" % d for d in INSTRUCTION_DOCS), n_docs))
    print("**只报不判**：%s —— 历史文档，必然含举例名与已移走的工具"
          % "、".join("`%s`" % d for d in HISTORY_DOCS))
    if not found:
        print("\n★ **未核，不是通过**（rc=4）—— 一个 `` `xxx.py` `` 都没扫到。")
        print("  文档改版把反引号去掉也会长这样，**本件此时必须喊，不能绿**。")
        return 4

    inside = sorted(n for n, r in found.items() if r["in_pkg"])
    outside = sorted(n for n, r in found.items() if not r["in_pkg"])
    print("\n被点名 **%d** 个：包内 **%d**｜**包外 %d**" % (len(found), len(inside), len(outside)))
    for n in inside:
        print("  ✓ 包内  %-46s ← %s" % (n, "、".join(sorted(set(found[n]["docs"])))))
    undisclosed = []
    for n in outside:
        ack = n in OUT_OF_PACKAGE_ACKNOWLEDGED
        if not ack:
            undisclosed.append(n)
        where = OUT_OF_PACKAGE_ACKNOWLEDGED.get(n)
        print("  %s 包外  %-46s ← %s"
              % ("△" if ack else "✗", n, "、".join(sorted(set(found[n]["docs"])))))
        print("        %s" % ("在：`%s`" % where if ack else "★ **未披露** —— 用户照文档跑会得到 can't open file"))

    if undisclosed:
        print("\n✗ **%d 个包外脚本没有明码披露**：%s" % (len(undisclosed), "、".join(undisclosed)))
        print("  ⇒ 装了这个 skill 的人照文档去跑，会得到 `can't open file`。")
        print("  两条出路：**把它放进包**，或**在文档里写清它不随包分发、在哪儿**，")
        print("  并把它加进本件的 `OUT_OF_PACKAGE_ACKNOWLEDGED`（闭集合，改它要改代码）。")
        return 1
    if outside:
        print("\n✓ 包外的 %d 个**都已明码披露** —— 读文档的人知道它们要去哪儿找。" % len(outside))
    else:
        print("\n✓ 被点名的脚本全部在包内。")

    hist, n_hist = scan(pkg, HISTORY_DOCS)
    h_out = sorted(n for n, r in hist.items() if not r["in_pkg"])
    print("\n—— 只报不判：%s（%d 份）——" % ("、".join(HISTORY_DOCS), n_hist))
    if not n_hist:
        print("  **未核**：一份历史文档都没读到。")
    elif h_out:
        print("  里面提到 **%d** 个包外脚本：%s" % (len(h_out), "、".join(h_out)))
        print("  ★ **不判红**：其中含讨论自测时写的举例名，以及当时用过、后来移走的工具。")
    else:
        print("  里面提到的脚本都在包内。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
