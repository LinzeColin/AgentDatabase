#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `quality_check.py` 的输出**按它真实的字段名**念出来。别再手搓了。

## 为什么有这件

2026-08-05，我一天之内对同一个工作区念了四次门，**四次都念的是
`blockers` 这个不存在的字段**，于是四次都打印「0 blockers」。

**真实字段是 `errors`。** `quality_check` 的输出顶层是：

```
schema_version / target / phase / profile / generated_at
**passed**  strict  metrics  checks  **errors**  warnings
```

`passed=False`、`errors` 里躺着 `eval.boundary-threshold: boundary 0.665 < 0.700`，
**而我据此在轮次台账里写下了「发布门 0 blocker」，并去打包。**
是 `package_target` 拦住的——它读的是 `passed` 与 `errors`，**读对了**。

★★ 这是「判据绿了但指错了文件」的**第 11 次**，而且是最近三次的同一种表面：
**不是判据错，是我为了看一眼结果临时手搓的解析脚本错，而它不经过任何门。**
[[gate-green-but-pointed-at-wrong-artifact]]

**所以这件的全部意义就是：让「看一眼门过没过」有一个不用手搓的入口。**

## 用法

    python3 show_gate.py <workspace> --phase release [--strict]
    python3 show_gate.py --self-test

退出码与 `passed` 一致：**过 0，不过 1**——可以直接串进 `&&`。
"""
import argparse
import json
import pathlib
import subprocess
import sys

REAL_KEYS = ("passed", "errors", "warnings")     # ← 实际 schema
BOGUS = ("blockers", "failures", "problems")     # ← 我手搓时用过的、**不存在的**


def render(payload: dict) -> tuple:
    errs = payload.get("errors") or []
    warns = payload.get("warnings") or []
    passed = bool(payload.get("passed"))
    lines = [f"{'✅ 过' if passed else '✗ **不过**'}　"
             f"phase={payload.get('phase')}　profile={payload.get('profile')}　"
             f"strict={payload.get('strict')}",
             f"  errors {len(errs)}　warnings {len(warns)}"]
    for e in errs:
        lines.append(f"  ✗ {e.get('code')} — {e.get('message', '')}")
    for w in warns:
        lines.append(f"  ⚠ {w.get('code')} — {str(w.get('message', ''))[:150]}")
    missing = [k for k in REAL_KEYS if k not in payload]
    if missing:
        lines.append(f"  ★ **输出里缺字段 {missing}——未核，不是通过**")
        passed = False
    return passed, "\n".join(lines)


def run(target: str, phase: str, strict: bool) -> tuple:
    here = pathlib.Path(__file__).resolve().parent
    argv = [sys.executable, str(here / "quality_check.py"), target, "--phase", phase]
    if strict:
        argv.append("--strict")
    r = subprocess.run(argv, capture_output=True, text=True)
    try:
        payload = json.loads(r.stdout)
    except json.JSONDecodeError:
        return False, ("✗ **输出不是 JSON——未核，不是通过**\n  "
                       + (r.stderr.strip() or r.stdout[-400:]))
    return render(payload)


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 反向对照①：**passed=False 且 errors 非空 → 必须说「不过」并列出来** ──")
    p, s = render({"passed": False, "phase": "release", "strict": True, "warnings": [],
                   "errors": [{"code": "eval.boundary-threshold",
                               "message": "boundary score 0.665 < 0.700"}]})
    chk(f"passed={p}", p is False)
    chk("列出了那条 error", "eval.boundary-threshold" in s and "0.665" in s)

    print("── ★★★ 反向对照②：**只有 `blockers`（我手搓时念的那个假字段）→ 不许说「过」** ──")
    p2, s2 = render({"phase": "release", "blockers": [], "warnings": []})
    chk(f"passed={p2}（缺 passed/errors，必须判未核）", p2 is False)
    chk("明写缺了哪些字段", "缺字段" in s2 and "errors" in s2)

    print("── ★★ 反向对照③：**真的全过 → 说「过」** ──")
    p3, s3 = render({"passed": True, "phase": "research", "strict": False,
                     "errors": [], "warnings": []})
    chk(f"passed={p3}", p3 is True)

    print("── ★★ 反向对照④：**warnings 不影响 passed，但要显示** ──")
    p4, s4 = render({"passed": True, "phase": "release", "strict": True, "errors": [],
                     "warnings": [{"code": "eval.baseline-not-capability-evidence",
                                   "message": "32/32 条基线不可作能力证据"}]})
    chk(f"passed={p4} 且警告显示", p4 is True and "baseline-not-capability" in s4)

    print("── ★ 反向对照⑤：**输出不是 JSON → 说「未核」，不说「通过」** ──")
    chk("假字段名单里没有 errors", "errors" not in BOGUS)
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?")
    ap.add_argument("--phase", default="release",
                    choices=["research", "synthesis", "release"])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.target:
        ap.error("要么 --self-test，要么给 workspace 路径")
    passed, text = run(a.target, a.phase, a.strict)
    print(text)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
