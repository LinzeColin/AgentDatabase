#!/usr/bin/env python3
"""**判据的 `--self-test` 有没有走到它自己的判定函数。**

## 撞出它的那一次（2026-08-12）

`check_holdout_overlap.py` 的自测有 11 条断言、全绿，验的却全是**配料**
（`shingles` / `runs` / `_is_boiler_run`）——**`check()` 一次也没被进入过**。
而 `check()` 才是分 train/holdout、套阈值、**出判决**的那一段，
**待裁定 ㊲（七个已入库人物 holdout 与 train 整段逐字重复）的全部依据就是它的输出。**

★ 更刺眼的是它内部的 `locate()`：注释自己写着「**这就是它从未跑通、也没人发现的原因**」
  （Nightingale #112 实测 117 条一条也定位不到）——**修好之后仍然没有自测。**

补完自测后当场做了五条变异，其中 `df_max = 0`（样板过滤把真转载一起吃掉）
让判据**给逐字转载发绿灯**。那条路此前没有任何东西挡着。

## 它测什么（以及**明确不测什么**）

用 `sys.settrace` 跑每件判据的 `--self-test`，记录本模块哪些函数被**真正进入**过。

★★ **只把「判定类」函数当问题**（`check* / audit / evaluate / scan* / verdict /
   locate / classify / census / detect / judge / analyse`）。
   其余没被进入的多数是**有意的**——`load_corpus` / `repo_root` / `body` 这类加载器，
   自测本就不该碰真实树（见 `check_checkers.selftest_touches_disk`）。
   **报大数是唬人，报判定类那个数才是这道判据的射程。**
   ★ 具体数字**不写死在这里**——它每补一件自测就往下走一格（当天就从 18 走到 17）。
     **跑一次 `python3 scripts/check_selftest_reach.py` 就有**，别信注释里的存量数。
     ⇒ [[self-reported-numbers-must-be-computed]]

## 冻结名单的用法

`KNOWN` 是 2026-08-12 的实况（当日 18 件，补完 `check_holdout_mention` 后 17 件）。
**它不是待办清单**——存量逐件补自测的成本很高，
且多数判据的判定函数需要构造完整工作区。本判据要挡的是**新增**：
新写的判据不许再交一个「验了配料、没验判决」的自测。

★ **补完一件就把它从 `KNOWN` 里删掉**（`check()` 会主动提醒），否则名单越来越假——
  那正是本判据要防的病换个地方复发。

⇒ 同族：[[a-checker-nothing-calls-is-not-a-checker]]（判据要有调用方）、
  本件是它的下一层：**自测要走到被保证之物**。
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT_DEFAULT = pathlib.Path(__file__).resolve().parent

DECISION = re.compile(
    r"^(check|audit|evaluate|scan|verdict|locate|classify|census|detect|judge|analy[sz]e)")

# 2026-08-12 实况。**冻结，不是待办**——见模块 docstring。
KNOWN = {
    "check_anchor_coherence.py",
    "check_corpus_integrity.py",
    "check_longs_corruption.py",
    "check_material_split.py", "check_ocr_homoglyphs.py",
    "check_ocr_language_death.py", "check_quote_integrity.py",
    "check_refusal_overflow.py",
    "check_semantic_residue.py",
    "check_source_numbering_gap.py", "check_threshold_doc_drift.py",
    "check_unqualified_priority_claim.py", "check_version_bump_ships_product.py",
}

_PROBE = r'''
import ast, contextlib, io, pathlib, runpy, sys, json
target = pathlib.Path(sys.argv[1]).resolve()
src = target.read_text(encoding="utf-8", errors="replace")
try:
    tree = ast.parse(src)
except SyntaxError:
    print(json.dumps({"file": target.name, "错": "语法错"})); raise SystemExit(0)
defined = {n.name for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
if not ({"self_test", "selftest"} & defined):
    print(json.dumps({"file": target.name, "无自测": True})); raise SystemExit(0)
entered = set()
def tracer(frame, event, arg):
    if event == "call" and frame.f_code.co_filename == str(target):
        entered.add(frame.f_code.co_name)
    return None
sys.argv = [str(target), "--self-test"]
rc, buf = 0, io.StringIO()
sys.settrace(tracer)
try:
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        runpy.run_path(str(target), run_name="__main__")
except SystemExit as e:
    rc = e.code if isinstance(e.code, int) else 1
except BaseException as e:
    rc = -1
    entered.add("<<崩了：%s>>" % type(e).__name__)
finally:
    sys.settrace(None)
skip = {"self_test", "selftest", "main", "tracer"}
print(json.dumps({"file": target.name, "rc": rc,
                  "没进入的": sorted(defined - entered - skip)}, ensure_ascii=False))
'''


def measure(directory: pathlib.Path, probe: pathlib.Path,
            exclude: set[str]) -> list[dict]:
    rows = []
    for f in sorted(directory.glob("check_*.py")):
        if f.name in exclude:
            continue
        r = subprocess.run([sys.executable, str(probe), str(f)],
                           capture_output=True, text=True, timeout=180)
        try:
            rows.append(json.loads(r.stdout.strip().splitlines()[-1]))
        except Exception:
            rows.append({"file": f.name, "错": (r.stderr or r.stdout)[:120]})
    return rows


def decision_gaps(rows: list[dict]) -> dict:
    out = {}
    for r in rows:
        miss = [n for n in r.get("没进入的", []) if DECISION.match(n)]
        if miss:
            out[r["file"]] = miss
    return out


def check(directory: pathlib.Path) -> int:
    with tempfile.TemporaryDirectory() as td:
        probe = pathlib.Path(td) / "_probe.py"
        probe.write_text(_PROBE, encoding="utf-8")
        # ★ **必须排除本件自己**：它的自测会再跑一遍全扫，递归下去指数级。
        #   ⇒ 按「不许静默截断」的规矩，把排除的事**印出来**，不藏在代码里。
        me = pathlib.Path(__file__).name
        rows = measure(directory, probe, exclude={me})

    print(f"扫了 {len(rows)} 件判据（**排除本件自己 {me}**——"
          f"它的自测会再跑一遍全扫，递归下去指数级）")
    broke = [r["file"] for r in rows if r.get("rc") not in (0, 1, 2, None)]
    if broke:
        print(f"⚠ 自测跑不通的 {len(broke)} 件：{broke[:6]}")

    gaps = decision_gaps(rows)
    total_miss = sum(len(r.get("没进入的", [])) for r in rows)
    print(f"有函数没被自测进入的：{sum(1 for r in rows if r.get('没进入的'))} 件"
          f"（共 {total_miss} 个函数）")
    print(f"**其中判定类函数没被进入的：{len(gaps)} 件**"
          f"——其余多是加载器，自测本就不该碰真实树")

    new = {k: v for k, v in gaps.items() if k not in KNOWN}
    fixed = sorted(KNOWN - set(gaps) - {pathlib.Path(__file__).name})
    if fixed:
        print(f"\n✓ 冻结名单里已补上自测的 {len(fixed)} 件：{fixed}"
              f"\n  —— **补完记得把它从 KNOWN 里删掉**，否则名单会越来越假")
    if new:
        print(f"\n✗ **新出现 {len(new)} 件「验了配料、没验判决」的自测**：")
        for f, fns in sorted(new.items()):
            print(f"    {f}：{'、'.join(fns)} 从没被自测进入")
        print("  —— 自测全绿而判定函数一次没跑，等于没测。"
              "\n  参照 check_holdout_overlap 的 ⑦a–⑦f：用 tempdir 造工作区，跑真 check()。")
        return 1
    print("\n✓ 判定类函数的自测覆盖没有新缺口")
    return 0


def self_test() -> int:
    """四向对照：自测调了判定函数 → 不报；没调 → 报；无自测 → 不报；判定名之外 → 不报。"""
    bad = []
    CASES = {
        # 名称: (源码, 是否应当被报为「判定函数没进入」)
        "check_fx_covered.py": (
            "import sys\n"
            "def check(x):\n    return 0\n"
            "def self_test():\n    return 0 if check(1) == 0 else 1\n"
            "if __name__ == '__main__':\n"
            "    sys.exit(self_test() if '--self-test' in sys.argv else check(None))\n", False),
        "check_fx_uncovered.py": (
            "import sys\n"
            "def check(x):\n    return 0\n"
            "def _helper():\n    return 1\n"
            "def self_test():\n    return 0 if _helper() == 1 else 1\n"
            "if __name__ == '__main__':\n"
            "    sys.exit(self_test() if '--self-test' in sys.argv else check(None))\n", True),
        # 无自测 → 本件不该报它（那是 check_checkers 的射程）
        "check_fx_nosel.py": ("def check(x):\n    return 0\n", False),
        # 没被进入的函数不是判定名 → 不该报（否则加载器会把名单灌爆）
        "check_fx_loader.py": (
            "import sys\n"
            "def load_corpus(p):\n    return {}\n"
            "def check(x):\n    return 0\n"
            "def self_test():\n    return 0 if check(1) == 0 else 1\n"
            "if __name__ == '__main__':\n"
            "    sys.exit(self_test() if '--self-test' in sys.argv else check(None))\n", False),
    }
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "scripts"
        d.mkdir(parents=True)
        for name, (src, _) in CASES.items():
            (d / name).write_text(src, encoding="utf-8")
        probe = pathlib.Path(td) / "_probe.py"
        probe.write_text(_PROBE, encoding="utf-8")
        gaps = decision_gaps(measure(d, probe, exclude=set()))
        for name, (_, want) in CASES.items():
            ok = (name in gaps) == want
            print(f"  {'✓' if ok else '✗'} {name}：期望{'报' if want else '不报'}，"
                  f"实得{'报' if name in gaps else '不报'}")
            if not ok:
                bad.append(name)

        # ★ 反向：`_PROBE` 必须**真的在跑自测**，不是靠猜。
        #   夹具 check_fx_uncovered 的 self_test 只调 _helper——
        #   若探针根本没跑起来，`没进入的` 会把 **check 和 _helper 一起**报出来。
        #   那样上面四条**照样全绿**，而探针其实是废的。
        rows = {r["file"]: r for r in measure(d, probe, exclude=set())}
        got = rows["check_fx_uncovered.py"].get("没进入的", [])
        if "_helper" in got:
            bad.append("探针没真跑自测：self_test 调过的 _helper 也被报成「没进入」")
            print("  ✗ 探针未真正执行自测（_helper 被误报为没进入）")
        else:
            print("  ✓ 探针确实执行了自测（自测调过的 _helper 未被误报）")

    if bad:
        print(f"\n负对照未过：{bad}")
        return 1
    print("\n负对照通过：四向对照 + 探针活性对照均过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="判据的自测有没有走到它自己的判定函数")
    ap.add_argument("directory", nargs="?", type=pathlib.Path, default=ROOT_DEFAULT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return check(a.directory)


if __name__ == "__main__":
    sys.exit(main())
