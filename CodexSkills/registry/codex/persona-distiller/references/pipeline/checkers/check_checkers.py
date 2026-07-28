#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**元检查器**：查「检查器自己有没有被验证过」。

## 为什么它排在全量分诊的第一位

RUNBOOK 第十八种：

> **规则：任何新写的检查器，交付前必须做一次负对照——
> 植入一个已知的坏样本，确认它真的报错。**
> **推论：没有负对照的检查器，其「全绿」不构成任何证据。**

这条推论一旦成立，它就**决定其余每一件检查器的结论算不算数**。
而这条规则本身此前**只是散文**——写在 RUNBOOK 里，靠执行者记得照做。
实测结果：12 件检查器里 **5 件从来没有负对照**，
另有 **1 件是硬门、负对照写了却跑不起来**。

**一个专门用来讲「没有负对照的检查器不算数」的项目，
自己有一半检查器没有负对照。** 这就是「记下来 ≠ 处理了」的样子。

## 三档判定

| 档 | 判据 | 含义 |
|---|---|---|
| `OK` | `--self-test` 独立可跑且退出码 0 | 结论可用 |
| `NOT-STANDALONE` | 有 `--self-test`，但还要求别的参数 | **负对照无法独立验证**——它依赖它本该独立于的那份数据 |
| `NO-SELFTEST` | 根本没有 `--self-test` | **其「全绿」不构成任何证据** |
| `FAILED` | 能跑但退出码非 0 | 负对照本身没过，结论一律不作数 |

**判据一律用退出码，不用输出串。** 七件检查器的通过标记各不相同
（`负对照通过` / `自测 5/5` / `✓ 无关文本被放过`），按串匹配必然漏判；
而且中文里「不通过」包含「通过」，v0.0.0.8 接线时已经踩过一次。

退出码：0 = 全部 OK；2 = 有 FAILED（硬）；3 = 用法错误。
**`NO-SELFTEST` 与 `NOT-STANDALONE` 只报不拦** —— 拦了会让 5 件既有检查器
当场把整条流水线堵死，违反「不因为过不了门而卡住流程」。
缺口计数逐次可见，不会被误当成通过。
"""
import argparse
import json
import pathlib
import subprocess
import sys

OK = "OK"
FAILED = "FAILED"
NOT_STANDALONE = "NOT-STANDALONE"
NO_SELFTEST = "NO-SELFTEST"


def classify(path: pathlib.Path, timeout: int = 60) -> tuple[str, str]:
    """跑 `<checker> --self-test`，只按**退出码 + argparse 的报错形态**判。"""
    try:
        proc = subprocess.run([sys.executable, str(path), "--self-test"],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return FAILED, f"负对照超时（>{timeout}s）"
    err = (proc.stderr or "") + (proc.stdout or "")
    if proc.returncode == 0:
        return OK, (proc.stdout or "").strip().splitlines()[-1][:80] if proc.stdout.strip() else ""
    # argparse 的两种拒绝形态要分开——它们的含义完全不同。
    if "unrecognized arguments" in err and "--self-test" in err:
        return NO_SELFTEST, "没有 --self-test 参数"
    if "the following arguments are required" in err:
        # ★ 这里**不能**直接判成 NOT-STANDALONE。
        #   argparse 缺必填参数时**先报这一条就退出**，永远不会再报
        #   「unrecognized arguments: --self-test」——于是「压根没有 --self-test」
        #   与「有 --self-test 但还要别的参数」会落进同一个分支，含义天差地别。
        #   必须再问一次 `--help` 才能分开。
        #   （本缺陷是本检查器交付前被自己的普查结果抓到的：`grep` 说那几件
        #     源码里没有 self_test，分类器却报 NOT-STANDALONE。
        #     根因是我的负对照样本把 `--workspace` 写成了**可选**，
        #     而真实的检查器把它写成**必填**——**样本没覆盖真实形态**。）
        need = err.split("the following arguments are required:", 1)[1].strip()
        if not _has_flag(path, "--self-test"):
            return NO_SELFTEST, f"没有 --self-test（且必填：{need[:40]}）"
        return NOT_STANDALONE, f"--self-test 还要求：{need[:60]}"
    return FAILED, err.strip().splitlines()[-1][:100] if err.strip() else f"退出码 {proc.returncode}"


def _has_flag(path: pathlib.Path, flag: str) -> bool:
    """问 `--help`：这个参数到底存不存在。判源码文本会被注释与文档字符串骗到。"""
    try:
        proc = subprocess.run([sys.executable, str(path), "--help"],
                              capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False
    return flag in (proc.stdout or "")


def census(directory: pathlib.Path, exclude: set[str]) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("check_*.py")):
        if path.name in exclude:
            continue
        verdict, detail = classify(path)
        rows.append({"checker": path.name, "verdict": verdict, "detail": detail})
    return rows


# ── 元负对照：本检查器自己也必须有负对照，否则它就是它自己在讲的那个问题 ──
FIXTURES = {
    "check_meta_ok.py": (
        "import argparse,sys\n"
        "p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true')\n"
        "a=p.parse_args()\n"
        "print('负对照通过（假的，只为测元检查器）')\n"
        "sys.exit(0)\n", OK),
    "check_meta_failing.py": (
        "import argparse,sys\n"
        "p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true')\n"
        "a=p.parse_args()\n"
        "print('负对照未过')\n"
        "sys.exit(2)\n", FAILED),
    "check_meta_none.py": (
        "import argparse\n"
        "p=argparse.ArgumentParser();p.add_argument('--workspace')\n"
        "p.parse_args()\n", NO_SELFTEST),
    # ★ 真实形态：**没有 --self-test，而且有必填参数**。
    #   这一档最初漏了，于是分类器把 6 件「压根没有负对照」的检查器
    #   误报成「有但不能独立跑」——两者的处置完全不同。
    #   **负对照的样本必须覆盖真实形态，否则它只验证了我想象的形态。**
    "check_meta_none_required.py": (
        "import argparse\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--workspace',required=True)\n"
        "p.parse_args()\n", NO_SELFTEST),
    "check_meta_coupled.py": (
        "import argparse\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--cache',required=True)\n"
        "p.add_argument('--self-test',action='store_true')\n"
        "p.parse_args()\n", NOT_STANDALONE),
}


def self_test() -> int:
    import tempfile
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        for name, (src, _) in FIXTURES.items():
            (d / name).write_text(src, encoding="utf-8")
        got = {r["checker"]: r["verdict"] for r in census(d, exclude=set())}
        for name, (_, want) in FIXTURES.items():
            actual = got.get(name)
            ok = actual == want
            print(f"  {'✓' if ok else '✗'} {name}: 期望 {want}，实得 {actual}")
            if not ok:
                bad.append(f"{name}: 期望 {want}，实得 {actual}")
    if bad:
        print("\n负对照未过：")
        for b in bad:
            print(f"  · {b}")
        return 2
    print(f"\n负对照通过（{len(FIXTURES)} 档各一例）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("directory", nargs="?", help="检查器目录")
    ap.add_argument("--self-test", action="store_true", help="只跑内置元负对照")
    ap.add_argument("--json", action="store_true", help="输出 JSON 供门消费")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.directory:
        print("✗ 需要检查器目录（或只给 --self-test）", file=sys.stderr)
        return 3
    d = pathlib.Path(a.directory)
    if not d.is_dir():
        print(f"✗ 目录不存在：{d}", file=sys.stderr)
        return 3

    rows = census(d, exclude={pathlib.Path(__file__).name})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"检查 {len(rows)} 件检查器有没有可用的负对照\n")
        for r in rows:
            mark = {OK: "✓", FAILED: "✗", NO_SELFTEST: "⚠", NOT_STANDALONE: "⚠"}[r["verdict"]]
            print(f"  {mark} {r['checker']:<32} {r['verdict']:<15} {r['detail']}")
        tally = {v: sum(1 for r in rows if r["verdict"] == v) for v in
                 (OK, FAILED, NOT_STANDALONE, NO_SELFTEST)}
        print(f"\n可用 {tally[OK]} / 未过 {tally[FAILED]}"
              f" / 不可独立验证 {tally[NOT_STANDALONE]} / 无负对照 {tally[NO_SELFTEST]}")
        if tally[NO_SELFTEST] or tally[NOT_STANDALONE]:
            print("\n**下面这些检查器的「全绿」不构成任何证据**（RUNBOOK 第十八种）：")
            for r in rows:
                if r["verdict"] in (NO_SELFTEST, NOT_STANDALONE):
                    print(f"  {r['checker']}  —— {r['detail']}")
    return 2 if any(r["verdict"] == FAILED for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
