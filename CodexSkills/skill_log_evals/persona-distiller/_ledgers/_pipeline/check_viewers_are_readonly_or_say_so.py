#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_viewers_are_readonly_or_say_so.py —— **名字承诺「只显示」的工具，要么不写盘，要么说出来**

## 抓到它的那一次（2026-08-17）

要扫全库看哪些人的 rubric 自相矛盾，按规矩先查 `show_gate.py` 写不写盘：

    grep -cE "write_text|open\\(...w|mkdir|json.dump" scripts/show_gate.py  →  **0**

判定「只读」，挂后台跑完全库。`git status` 冒出**两个新文件**：
`seth-godin` 与 `michael-steinhardt` 的 `reports/holdout-contaminated-passages.json`
—— 这两人**都已判分（各 128 行结果），按 ㊵ 是冻结的**。

链条：`show_gate.py` → 起子进程跑 `quality_check.py`（默认**不带** `--write-report`）
→ 它加载 `check_holdout_overlap.py` → 那里 **372–374 行无条件写**。

**我的 grep 只看直接写调用，不跟 subprocess。** 所以本件查**两层**。
[[calling-the-authoritative-checker-overwrote-frozen-evidence]]

## 射程：只收「名字只承诺显示」的那一类

    show_ / list_ / report_ / print_

★ **`render_` 有意不收**：render 的字面意思就是产出一份东西，写盘是它的本分
  （`render_claims.py` 的写还由 `if write:` 门控）。把它算进来是把正常行为报成缺陷。
★ **`check_` 也不收**：判据留下证据文件是分内事。今天 44 件「名字像只读」里
  41 件「没说」——那个数会误导，收干净之后真正的这一类只有 4 件。
  [[counts-need-their-cutoff-stated]]

## 判定

对每件 viewer：

1. **第一层**：AST 找 `write_text/mkdir/dump/copy/rmtree…`，**排除自测函数内的**
   （嵌套函数按最外层归属 —— 我第一版按 `ast.walk` 数，把 `self_test` 里的
   嵌套 `mk` 重复计了一遍，于是误报「两个 show_* 会写盘」）；
2. **第二层**：起不起子进程；起了就顺着被调的脚本再查一层第一层；
3. 只要**可能写**，文件头就必须说（含「不是只读／会在工作区写／会写盘」之一）；
   没说 ⇒ **rc=1**。

退出码：0＝这一类要么不写、要么都说了；1＝有工具会写却没说；4＝一件都没扫到（未量）。
"""
import argparse
import ast
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[4]
DIRS = [REPO / "CodexSkills/registry/codex/persona-distiller/scripts",
        REPO / "CodexSkills/registry/codex/persona-distiller-group/scripts",
        HERE]
VIEWER_PREFIX = ("show_", "list_", "report_", "print_")
WRITE_ATTRS = {"write_text", "write_bytes", "mkdir", "unlink", "rename", "replace",
               "copy", "copytree", "rmtree", "dump"}
SAYS_IT = re.compile(r"不是只读|会在工作区写|会写盘|writes into|not read-only")
SUBPROC = re.compile(r"\bsubprocess\b|os\.system|runpy")


def writes_outside_selftest(src: str):
    """→ [(行号, 所属最外层函数)]，**排除自测函数**。纯函数。

    ★ 归属按**最外层**函数算：`ast.walk` 会把 `self_test` 里的嵌套 `mk`
      当成独立函数再数一遍，于是同一处写盘被计两次、还被算成「不在自测里」。
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None                      # ★ 解析不了 ⇒ **未量**，不是「不写」
    seen = {}

    def walk(node, top):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walk(ch, top or ch.name)
            else:
                if (isinstance(ch, ast.Call) and isinstance(ch.func, ast.Attribute)
                        and ch.func.attr in WRITE_ATTRS):
                    seen.setdefault(ch.lineno, top or "<module>")
                walk(ch, top)

    walk(tree, None)
    return [(l, f) for l, f in sorted(seen.items())
            if "self_test" not in f and "selftest" not in f]


PY_LITERAL = re.compile(r'["\']([A-Za-z0-9_./-]+\.py)["\']')


def callees(src: str, resolver=None):
    """→ 源码里点名的 `*.py`（子进程被调方的候选）。resolver 把名字变成真路径。

    ★ 只认**字面量**。拼出来的路径认不出 —— 那种情况下第二层会**报未量**，
      不会当成「不写」。
    """
    names = sorted(set(PY_LITERAL.findall(src)))
    if resolver is None:
        return names
    out = []
    for n in names:
        p = resolver(n)
        if p is not None:
            out.append(p)
    return out


def resolve_callee(name, dirs, repo):
    """把源码里的 `*.py` 字面量解析成真路径；解析不出或**有歧义**就 None（⇒ 记未量）。

    ★★★ 兜底 rglob 会撞上**同名不同物**：`_ledgers/_pipeline/checkers/` 是
      2026-07-28 立的另一套「产物体检工具」，与 `scripts/` 有 **12 个同名文件**
      （`check_holdout_overlap` 那对是 193 行 vs 628 行，做的根本不是一件事）。
      随便挑第一个 = 拿另一棵树的文件回答这棵树的问题。
      ⇒ 先按**给定目录**顺序找；找不到才 rglob，且**多于一个候选就报未量**。
      [[filename-matching-is-brittle]]｜[[two-source-ids-is-not-two-evidences]]
    """
    base = pathlib.Path(name).name
    for d in dirs:
        q = d / base
        if q.is_file():
            return q
    cands = [q for q in repo.rglob(base) if q.is_file()]
    return cands[0] if len(cands) == 1 else None


def verdict(name: str, src: str, resolver=None):
    """→ (可能写?, 说了?, 理由)。纯函数，便于自测。

    ★★★ 第二层**真的顺着查**：文件头承诺「起了子进程就再查一层」，
      第一版却只写了「起子进程 ⇒ 可能写」——**注释承诺得比代码多**，
      于是把 `report_expert_team_state.py` 报成缺陷，而它调的三个工具各 0 处写盘。
      [[the-comment-states-the-rule-the-code-narrows-it]]
    """
    w = writes_outside_selftest(src)
    if w is None:
        return True, False, "**源码解析不了 —— 未量，按会写处理**"
    sub = bool(SUBPROC.search(src))
    said = bool(SAYS_IT.search(src))
    if w:
        return True, said, "直接写 %d 处（行 %s）" % (len(w), ", ".join(str(l) for l, _ in w[:3]))
    if not sub:
        return False, said, "不写"
    if resolver is None:
        return True, said, "起子进程（**第二层未查** —— 没给 resolver）"
    hits, unknown = [], 0
    for n in sorted(set(PY_LITERAL.findall(src))):
        p = resolver(n)
        if p is None:
            unknown += 1
            continue
        try:
            sub_w = writes_outside_selftest(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            unknown += 1
            continue
        if sub_w is None or sub_w:
            hits.append(p.name)
    if hits:
        return True, said, "子进程会写：%s" % "、".join(hits[:2])
    if unknown:
        return True, said, "起子进程、**有 %d 个被调方解析不出 ⇒ 未量**" % unknown
    return False, said, "起子进程，但被调方都不写（已顺查）"


def self_test() -> int:
    bad, tot = [], [0]

    def chk(lbl, ok):
        tot[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    chk("★ 完全不写 ⇒ 不算会写", verdict("show_x.py", "def main():\n    print(1)\n")[0] is False)
    chk("★★ 产线里直接写 ⇒ 算会写",
        verdict("show_x.py", "import pathlib\ndef main():\n    pathlib.Path('a').write_text('x')\n")[0] is True)
    chk("★★★ **自测函数里的写不算**（否则每件带夹具的都会被报）",
        verdict("show_x.py", "import pathlib\ndef self_test():\n    pathlib.Path('a').write_text('x')\n")[0] is False)
    chk("★★★ **自测里的嵌套函数也不算** —— 我第一版按 ast.walk 数，"
        "把 self_test 里的 mk 重复计了一遍，误报了两个 show_*",
        verdict("show_x.py",
                "import pathlib\ndef self_test():\n    def mk(p):\n        p.mkdir()\n    mk(pathlib.Path('a'))\n")[0] is False)
    chk("★★ 起子进程 ⇒ 也算「可能写」（第二层）",
        verdict("show_x.py", "import subprocess\ndef main():\n    subprocess.run(['git','log'])\n")[0] is True)
    chk("★★ 文件头说了就算说了",
        verdict("show_x.py", '"""本件**不是只读的**。"""\nimport subprocess\nsubprocess.run([])\n')[1] is True)
    chk("★★★ **源码解析不了 ⇒ 按会写处理**（未量不许当成不写）",
        verdict("show_x.py", "def (:\n")[0] is True)

    # ── ★★★ 第二层「顺着查」的三条 —— 第一版只写在文件头、代码没做 ──
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "quiet.py").write_text("def main():\n    print(1)\n", encoding="utf-8")
        (d / "noisy.py").write_text("import pathlib\ndef main():\n    pathlib.Path('a').write_text('x')\n",
                                    encoding="utf-8")
        res = lambda n: (d / pathlib.Path(n).name) if (d / pathlib.Path(n).name).is_file() else None
        src_q = 'import subprocess\nsubprocess.run(["python3", "quiet.py"])\n'
        src_n = 'import subprocess\nsubprocess.run(["python3", "noisy.py"])\n'
        src_u = 'import subprocess\nsubprocess.run(["python3", "nowhere.py"])\n'
        chk("★★★ 顺查到**被调方不写** ⇒ **不算会写**（这正是 report_expert_team_state 被误报的那一次）",
            verdict("show_x.py", src_q, res)[0] is False)
        chk("★★★ 顺查到**被调方会写** ⇒ 算会写，且理由点名是谁",
            verdict("show_x.py", src_n, res)[0] is True
            and "noisy.py" in verdict("show_x.py", src_n, res)[2])
        chk("★★★ 被调方**解析不出** ⇒ 算会写并写明「未量」，不许当成不写",
            verdict("show_x.py", src_u, res)[0] is True
            and "未量" in verdict("show_x.py", src_u, res)[2])
    # ── ★★★ 被调方解析：同名不同物必须报未量，不许挑第一个 ──
    with tempfile.TemporaryDirectory() as td2:
        r = pathlib.Path(td2)
        (r / "one").mkdir(); (r / "two").mkdir()
        (r / "one" / "solo.py").write_text("x = 1\n", encoding="utf-8")
        (r / "one" / "dup.py").write_text("x = 1\n", encoding="utf-8")
        (r / "two" / "dup.py").write_text("x = 2\n", encoding="utf-8")
        chk("★★ 唯一候选 ⇒ 解析得出", resolve_callee("solo.py", [], r) == (r / "one" / "solo.py"))
        chk("★★★ **同名不同物（两处 dup.py）⇒ None（未量），不许挑第一个**",
            resolve_callee("dup.py", [], r) is None)
        chk("★ 给定目录优先于 rglob（歧义也不影响）",
            resolve_callee("dup.py", [r / "two"], r) == (r / "two" / "dup.py"))

    print("\n自测 %d 项，不符 %d 项" % (tot[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    if ap.parse_args().selftest:
        return self_test()

    files = []
    for d in DIRS:
        if not d.is_dir():
            continue
        files += [p for p in sorted(d.glob("*.py")) if p.name.startswith(VIEWER_PREFIX)]
    _resolve = lambda n: resolve_callee(n, DIRS, REPO)

    print("扫描面：%d 个目录里名字以 %s 开头的工具 —— 共 **%d** 件"
          % (sum(1 for d in DIRS if d.is_dir()), "/".join(VIEWER_PREFIX), len(files)))
    print("★ `render_` 与 `check_` **有意不收**（产出文件是它们的本分），文件头写了理由。")
    if not files:
        print("★ **未量，不是通过**（rc=4）—— 一件都没扫到")
        return 4

    silent = []
    print("\n%-42s %-34s %s" % ("工具", "证据", "文件头说了吗"))
    for p in files:
        can, said, why = verdict(p.name, p.read_text(encoding="utf-8", errors="replace"), _resolve)
        tag = "—（不写，无需说）" if not can else ("✓ 说了" if said else "**没说**")
        if can and not said:
            silent.append(p)
        print("%-42s %-34s %s" % (p.name[:42], why[:34], tag))

    if silent:
        print("\n✗ **这些只承诺「显示」，却会写或可能写，而文件头没说**：%d 件" % len(silent))
        for p in silent:
            print("     " + str(p.relative_to(REPO)))
        print("\n  ★ 处置：要么真改成不写，要么在**文件头**与**运行时 stderr** 各说一次，"
              "并把它会碰的**绝对路径**印出来（`show_gate.py` 是范例）。")
        return 1
    print("\n✓ 这一类 **%d** 件：要么不写，要么都在文件头说了。" % len(files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
