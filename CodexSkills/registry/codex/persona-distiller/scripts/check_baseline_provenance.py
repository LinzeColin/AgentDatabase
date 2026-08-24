#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**基线来源门**：`delta` 到底是跟什么比出来的。

## 触发本检查器的实例

用户 2026-08-02 评分：

> 没有提供「专家团队相对裸模型，在真实盲测任务上提高多少正确率」的公开结果。
> 目前专家团队 skill 只是纸面数据很强，实际能力非常差，接近 0 分甚至负收益。

而**最硬的证据来自本项目自己的评委**。Livermore #100 第 2 轮，E 席原话：

> 17 条 baseline 全是零对冲零出处的稻草人，
> **候选/对照的分差被显著放大，不能当作能力证据。**

这句话被抄进了提交信息，然后 `delta 0.8012` 继续被当成绩报。
**已入库 100 人的全部 delta 都是这个性质**——量的是
「我写的产物 vs 我写的稻草人」，在能力问题上等于零信息。

## 一句话诊断

**每一件检查器都有负对照，唯独产品本身没有。**
RUNBOOK 第十八种（没有负对照的检查器，其「全绿」不构成任何证据）
被执行了三十多个版本，**从未对整个工程执行过**。
「团队比裸模型强多少」就是这个工程的负对照。

## 判据

`evals/results.jsonl` 里每一条 `system == "baseline"` 的记录必须带 `baseline_source`：

| 值 | 含义 | 能否作能力证据 |
|---|---|---|
| `bare-model-run` | **裸模型对同一 prompt 的实答**，附运行记录 | **能** |
| `prior-version` | 本人物的上一版产物 | 能（但只证明「比上一版强」） |
| `self-authored-strawman` | 作者手写的对照答案 | **不能** |
| `unknown` | 没写 | **不能** |

**缺字段一律按 `unknown` 处理**——「没标」与「标了不能用」在证据上是同一件事，
不许因为省略而获得沉默的通过。

## 为什么是 warning 不是 error

100 人已入库，全部是 `self-authored-strawman`。判成 error 会让既有产物集体不可发布，
而按既定裁定「门达不到时选诚实退路继续，绝不为凑数放宽判据」——
正确动作是**把这个事实报出来并挡住它冒充能力证据**，不是拦住流程。

**门要拦的是「拿这个 delta 说自己比裸模型强」，不是拦住发布。**

退出码：0 = 全部基线可作能力证据；1 = 存在不可作能力证据的基线；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

USABLE = {"bare-model-run", "prior-version"}
UNUSABLE = {"self-authored-strawman", "unknown"}
ALL = USABLE | UNUSABLE


def summarize(rows: list) -> dict:
    """→ {'total','by_source','usable','unusable','capability_evidence'}"""
    by: dict = {}
    for r in rows:
        if r.get("system") != "baseline":
            continue
        src = str(r.get("baseline_source") or "unknown")
        if src not in ALL:
            src = f"invalid:{src}"
        by[src] = by.get(src, 0) + 1
    total = sum(by.values())
    usable = sum(n for s, n in by.items() if s in USABLE)
    return {
        "baseline_rows": total,
        "by_source": by,
        "usable_rows": usable,
        "unusable_rows": total - usable,
        # ★ 全部可用才算「这个 delta 能当能力证据」——混着算等于没算。
        "capability_evidence": bool(total) and usable == total,
    }


def check(target: pathlib.Path) -> tuple:
    path = target / "evals" / "results.jsonl"
    try:
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError as exc:
        return [f"读不到 {path}：{exc}"], {}
    s = summarize(rows)
    problems = []
    if not s["baseline_rows"]:
        problems.append("没有任何 baseline 记录——delta 无从谈起")
    elif not s["capability_evidence"]:
        bad = {k: v for k, v in s["by_source"].items() if k not in USABLE}
        problems.append(
            f"{s['unusable_rows']}/{s['baseline_rows']} 条基线不可作能力证据（{bad}）——"
            f"**此产物的 delta 不得用于支持「比裸模型强」这类结论**；"
            f"它只说明产物比该对照写得好")
    return problems, s


# --------------------------------------------------------------------------
# 负对照。没有负对照的检查器，其「全绿」不构成任何证据（第十八种）。
# --------------------------------------------------------------------------
def _rows(*sources):
    out = [{"system": "candidate", "overall_score": 0.9}]
    for s in sources:
        r = {"system": "baseline", "overall_score": 0.1}
        if s is not None:
            r["baseline_source"] = s
        out.append(r)
    return out


def self_test() -> int:
    fails = []

    # ★★★ 2026-08-11 变异实测补的：**`invalid:` 这个标记从没被断言过**。
    #   把 `if src not in ALL: src = f"invalid:{src}"` 删掉，**自测一条都没红**——
    #   因为它不影响 `usable`／`capability_evidence`（不认识的来源本来就不在 USABLE 里），
    #   **它只影响人读 `by_source` 时能不能看出「这个来源名我不认识」**。
    #   拼错一个来源名、或换了个新来源忘了登记，全靠这个标记暴露。
    _s = summarize([
        {"system": "baseline", "baseline_source": "bare-model-run"},
        {"system": "baseline", "baseline_source": "typo-source-xyz"},
        {"system": "candidate", "baseline_source": "ignored"},
    ])
    if not any(k.startswith("invalid:") for k in _s["by_source"]):
        fails.append("**不认识的 baseline_source 没有被标成 `invalid:`**——"
                     "拼错来源名就看不出来了")
    if "invalid:bare-model-run" in _s["by_source"]:
        fails.append("**认识的来源被误标成 invalid**")
    if _s["baseline_rows"] != 2:
        fails.append("baseline 行数应为 2（candidate 那行不该算）")
    print("  %s `invalid:` 标记：%s" % (
        "✓" if not fails else "✗", _s["by_source"]))
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        def mk(name, rows):
            t = tmp / name
            (t / "evals").mkdir(parents=True)
            (t / "evals" / "results.jsonl").write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
            return t

        # 正对照：全部裸模型实答 → 可作能力证据
        p, s = check(mk("good", _rows("bare-model-run", "bare-model-run")))
        if p or not s["capability_evidence"]:
            fails.append(f"正对照·全裸模型基线被误报：{p}")

        # 负对照 1：全部自撰稻草人
        p, s = check(mk("b1", _rows("self-authored-strawman", "self-authored-strawman")))
        if not p or s["capability_evidence"]:
            fails.append("负对照未抓出：全部自撰稻草人")

        # 负对照 2：**缺字段**必须按 unknown 处理，不许沉默通过
        p, s = check(mk("b2", _rows(None, None)))
        if not p or s["capability_evidence"]:
            fails.append("负对照未抓出：缺 baseline_source 时沉默通过了")

        # 负对照 3：混着来也不算——一条不可用就不能当能力证据
        p, s = check(mk("b3", _rows("bare-model-run", "self-authored-strawman")))
        if not p or s["capability_evidence"]:
            fails.append("负对照未抓出：可用与不可用混合时仍被判为能力证据")

        # 负对照 4：没有任何 baseline
        p, s = check(mk("b4", [{"system": "candidate", "overall_score": 0.9}]))
        if not p:
            fails.append("负对照未抓出：没有 baseline 记录")

        # 反向对照：`prior-version` 是合法基线，不许被误杀
        p, s = check(mk("r1", _rows("prior-version", "prior-version")))
        if p or not s["capability_evidence"]:
            fails.append(f"反向对照失败：prior-version 被误判为不可用：{p}")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：正对照 0 报，坏样本 4 类全部抓出（含「缺字段沉默通过」），"
          "且 prior-version 未被误杀")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="基线来源门：delta 到底是跟什么比出来的")
    ap.add_argument("target", nargs="?", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.target or not a.target.is_dir():
        print("用法错误：需要 target 目录（或 --self-test）", file=sys.stderr)
        return 3
    problems, s = check(a.target)
    if a.json:
        print(json.dumps({"summary": s, "problems": problems}, ensure_ascii=False, indent=2))
        return 1 if problems else 0
    print(json.dumps(s, ensure_ascii=False, indent=2))
    if not problems:
        print("\n✓ 全部基线可作能力证据")
        return 0
    print()
    for p in problems:
        print(f"✗ {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
