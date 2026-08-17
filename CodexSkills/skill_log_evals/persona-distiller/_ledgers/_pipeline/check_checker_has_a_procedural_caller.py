#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_checker_has_a_procedural_caller.py —— **每件判据都要有「流程调用方」**

## 为什么建它：同一个病第九次以上，而它一直只是散文

「判据没有调用方就不算做完」这条在 RUNBOOK 与教训库里写了很多遍。
**2026-08-18 我在同一天里：早上落下这条教训，傍晚一数当天新建的判据 ——
两件（`check_pinned_year_from_relative_date`、`check_primary_excludes_failed_extraction`）
在 RUNBOOK / quality_check / `*.sh` 三处**全是 0**。

按本项目自己的规矩：**同一个病犯到第三次，就不该再写「以后要记得」。**
[[a-checker-nothing-calls-is-not-a-checker]]｜[[a-rule-in-a-doc-has-no-enforcer]]

## ★★★ 本件的关键：**「自测层被调用」不算「流程层被调用」**

`run_checks.py` 是**按能力发现**的：凡源码里有 `add_argument("--self-test"` 的都跑。
于是每件判据**天然**都有一个「调用方」，`grep 判据名` 也找不到它（名字不在任何名单里）。
**这让「有没有调用方」这个问题看起来永远是绿的。**

而 `run_checks` 自己的 docstring 第 13 行写着：

> **不验**：判据跑在真语料上的结论 —— 那要各自的 `--corpora` / `--skill-root`，本件不代跑。

⇒ **一件判据可以同时「被调用」和「从没对现实跑过」。**
本件只数**流程层**的调用方：RUNBOOK 的步骤、`quality_check.py`、`_pipeline/*.sh`、
以及别的工具 import/subprocess 它。**自测层一律不算。**

## 判什么、不判什么

**判**：`_pipeline/check_*.py` 里，有没有哪一件在上述四处**一次都没出现**。
**不判**：调用方跑得对不对、参数给得全不全 —— 那是别的判据的事。

★ 白名单只放**有理由**的：元判据（本件自己）、以及**被别的判据调用**的库函数式判据。

退出码：0＝每件都有流程调用方；1＝有孤儿；4＝扫描面是空的（未量）。
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
RUNBOOK = HERE / "RUNBOOK.md"
QUALITY = HERE.parents[3] / "registry/codex/persona-distiller/scripts/quality_check.py"

#: ★★★ 2026-08-18 扩射程：**并列的兄弟树也要覆盖**。
#   本件建成当天只扫 `_pipeline/`，报出 11 件孤儿并清零。
#   两小时后**手查**团队 skill 的 4 件判据 —— 3 件同样只有自测层调用方，
#   而它的 `SKILL.md`（用户照着做的六步调用）对这 4 件提及 **0 次**。
#   ⇒ 同一个病在并列的树上活着，只是本件够不到。**够不到就等于没建。**
#   [[fixed-the-symptom-kept-the-root-cause]]｜[[a-gates-scan-set-is-smaller-than-reality]]
#
#   每棵树声明：(判据目录, [看这些文件算「有流程调用方」])
EXTRA_TREES = [
    (HERE.parents[3] / "registry/codex/persona-distiller-group/scripts",
     ["SKILL.md", "CHANGELOG.md", "tests/run_functional_acceptance.py"]),
]

# ★ 白名单：每条必须写清**为什么不需要流程调用方**，没理由的不许进。
EXEMPT = {
    "check_checker_has_a_procedural_caller.py":
        "本件自己 —— 元判据，由 run_checks 的自测层与推送前清单覆盖",
}


def callers_of(name: str, runbook_text: str, quality_text: str, sh_texts: dict, py_texts: dict):
    """→ [调用方描述]。纯函数，文本已由调用方读好。

    ★ `py_texts` 里**必须先把自己剔除**——一个判据在自己的源码里出现是必然的，
      把它算成调用方，本件就会永远全绿。这正是「判据扫的集合」那一族的反面：
      **扫描面太大也会假绿。**
    """
    stem = name[:-3] if name.endswith(".py") else name
    out = []
    if stem in (runbook_text or ""):
        out.append("RUNBOOK")
    if stem in (quality_text or ""):
        out.append("quality_check")
    out += ["%s(sh)" % k for k, v in (sh_texts or {}).items() if stem in v]
    out += ["%s(py)" % k for k, v in (py_texts or {}).items() if stem in v]
    return out


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    RB = "步骤 3 → python3 _pipeline/check_primary_excludes_failed_extraction.py"
    QC = "run('check_quote_in_span.py', ...)"
    SH = {"drop_source.sh": "python3 check_measurements_fresh.py"}
    PY = {"quality_check_wrapper.py": "check_authorship"}

    chk("★★★ 正例：出现在 RUNBOOK 步骤里 ⇒ 有调用方",
        callers_of("check_primary_excludes_failed_extraction.py", RB, "", {}, {}) == ["RUNBOOK"])
    chk("★★ 正例：出现在 quality_check 里 ⇒ 有调用方",
        callers_of("check_quote_in_span.py", "", QC, {}, {}) == ["quality_check"])
    chk("★★ 正例：出现在某个 .sh 里 ⇒ 有调用方",
        callers_of("check_measurements_fresh.py", "", "", SH, {}) == ["drop_source.sh(sh)"])
    chk("★★ 正例：被别的工具调用 ⇒ 有调用方",
        callers_of("check_authorship.py", "", "", {}, PY) == ["quality_check_wrapper.py(py)"])
    chk("★★★ 负例（**本件的整个理由**）：四处都没有 ⇒ 孤儿",
        callers_of("check_pinned_year_from_relative_date.py", RB, QC, SH, PY) == [])
    chk("★★★ 负例：**自己的源码不算调用方**（调用方集合里必须先剔除自己）",
        callers_of("check_x.py", "", "", {}, {"check_x.py": "check_x 自己"}) != []
        and callers_of("check_x.py", "", "", {}, {}) == [])
    chk("★ 多个调用方全部列出", len(callers_of("check_measurements_fresh.py",
        "check_measurements_fresh", "", SH, {})) == 2)
    chk("★ 空输入不炸", callers_of("check_z.py", "", "", {}, {}) == []
        and callers_of("check_z.py", None, None, None, None) == [])
    chk("★★ 白名单每条都写了理由（否则就是「把红灯关掉」）",
        all(isinstance(v, str) and len(v) > 8 for v in EXEMPT.values()))
    # ★★★ 兄弟树分支：**声明本身**要可核，否则那条分支可能永远全绿而没人知道
    chk("★★★ `EXTRA_TREES` 里每棵树都真实存在（不存在时 main 判未量 rc=4）",
        all(tree.is_dir() for tree, _faces in EXTRA_TREES))
    chk("★★★ 每棵兄弟树都**真的有 check_*.py**（0 件时这条分支恒绿，等于没建）",
        all(any(tree.glob("check_*.py")) for tree, _f in EXTRA_TREES))
    chk("★★ 每棵树声明的「流程面」文件至少有一个存在（全不存在 ⇒ 全判孤儿，是假红）",
        all(any((tree.parent / rel).is_file() for rel in faces)
            for tree, faces in EXTRA_TREES))
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    checkers = sorted(p for p in HERE.glob("check_*.py"))
    # ★ 兄弟树的判据也收进来；它们的「流程面」是各自 skill 的文件，单独读
    extra: list[tuple[pathlib.Path, str]] = []
    for tree, faces in EXTRA_TREES:
        if not tree.is_dir():
            print("★ **未量，不是通过**（rc=4）—— 兄弟树不在：%s" % tree)
            return 4
        face_text = ""
        for rel in faces:
            fp = tree.parent / rel
            if fp.is_file():
                face_text += fp.read_text(encoding="utf-8", errors="replace")
        for c in sorted(tree.glob("check_*.py")):
            extra.append((c, face_text))
    print("扫描面：%s ｜ `check_*.py` **%d** 件" % (HERE, len(checkers)))
    if not checkers:
        print("★ **未量，不是通过**（rc=4）—— 一件判据都没发现")
        return 4

    rb = RUNBOOK.read_text(encoding="utf-8", errors="replace") if RUNBOOK.is_file() else ""
    qc = QUALITY.read_text(encoding="utf-8", errors="replace") if QUALITY.is_file() else ""
    if not rb:
        print("★ **未量，不是通过**（rc=4）—— 读不到 RUNBOOK：%s" % RUNBOOK)
        return 4
    print("  参照面：RUNBOOK %d 字｜quality_check %s｜`_pipeline/*.sh` %d 个"
          % (len(rb), ("%d 字" % len(qc)) if qc else "**读不到**（不当通过）",
             len(list(HERE.glob("*.sh")))))
    sh = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in HERE.glob("*.sh")}

    orphan, ok = [], 0
    for c in checkers:
        if c.name in EXEMPT:
            continue
        py = {p.name: p.read_text(encoding="utf-8", errors="replace")
              for p in HERE.glob("*.py") if p.name != c.name}      # ★ 先剔除自己
        who = callers_of(c.name, rb, qc, sh, py)
        if who:
            ok += 1
        else:
            orphan.append(c.name)

    for c, face in extra:
        stem = c.name[:-3]
        # ★ 自己的源码不算调用方（同上，扫描面太大也会假绿）
        sib = {q.name: q.read_text(encoding="utf-8", errors="replace")
               for q in c.parent.glob("*.py") if q.name != c.name}
        if stem in face or any(stem in v for v in sib.values()):
            ok += 1
        else:
            orphan.append("%s/%s" % (c.parent.parent.name, c.name))

    print("\n有流程调用方 **%d**｜**孤儿 %d**｜白名单 %d｜（含兄弟树 %d 件）"
          % (ok, len(orphan), len(EXEMPT), len(extra)))
    print("★ 「自测层被 `run_checks` 按能力收编」**不算**流程调用方 ——")
    print("  它验的是判定逻辑站不站得住，不是「今天这批数据干不干净」。")
    if not orphan:
        print("\n✓ 每件判据都有流程调用方")
        return 0
    print("\n✗ **没有任何流程调用方的判据 %d 件**：" % len(orphan))
    for o in orphan:
        print("     · %s" % o)
    print("\n  ★ 处置：接进 RUNBOOK 的对应步骤、或 `quality_check.py` 的对应 phase、"
          "或推送前清单。")
    print("  ★★ 不要用「加进白名单」了事 —— 白名单每条都要写清**为什么不需要**。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
