#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产物全量体检 —— 一条命令跑完官方质检门之外的所有自建检查。

## 为什么要有这个

官方 `quality_check.py` 三个阶段全绿，**不代表产物没有事实错误**。
Jesse Vincent #94 在三个门全绿的状态下被评委抓出三类错误，
每类平均散布在 **4 个落点**，其中只有 1–2 个在评委看得到的用例里。

这些检查此前都是我手工记着跑的。**手工记着跑 = 迟早漏跑**——
`persona.md` 与 `01-writings.md` 里那两处「未作任何标记」，
就是因为我以为「用例改完就完了」而撑到第四轮才被翻出来。

## 跑什么

| 检查 | 拦什么 | 出处 |
|---|---|---|
| `quality_check --phase research/synthesis/release --strict` | 官方门 | 流水线自带 |
| `check_claim_coverage` | 装饰性引用（引了源但源里没这个事实）| Icahn #92 |
| `check_quote_integrity` | 伪造引文（引号里的英文原句语料里没有）| Vincent #94 |
| `check_semantic_residue` | 订正残留（同一个错换个措辞又活了）| Vincent #94 |
| `check_absence_claims` | 无依据的「从未／只有／完全没有」| Vincent #94 |

## 三条使用纪律

**一、`check_absence_claims` 与 `check_quote_integrity` 只列不判。**
它们输出的是「须人工看一眼」的清单，不是错误列表。
**把它们的输出当成错误直接改，会改坏真事实**——
核 `double-ESC` 时我的模式漏了原文里的空格，差点把一个真引文当伪造删掉。

**二、任何一项报 0，先怀疑是不是模式写窄了。**
本库有七次「正则写窄 → 0 命中 → 判定不存在」的记录。**0 命中不是结论。**

**三、每个自建检查器交付前都跑过负对照**（RUNBOOK 第十八种）。
`--self-test` 在三个硬门检查器里都固化了：
`check_quote_integrity.py`（4 类伪造全抓、36 条真引文 0 误报）、
`check_semantic_residue.py`（双向：残留抓到、订正豁免，2/2）、
`check_claim_coverage.py`（5 向：实体抽取、装饰性判定、真支撑不误判、
无实体无引文显式计未检查、引文须在被引源中）。
**改动这两个脚本后必须重跑负对照**——参数一动，抓与漏的平衡就变，
而变坏了不会有任何报错。本入口每次运行都会先跑一遍它们的负对照。

**四、语义残留规则是逐人物写的，不通用。**
`--rules` 指向的 JSON 由该人物的订正历史决定：每订正一个事实，
就往里加一条「该事实错误方向」的模式。**没有订正历史就没有这个文件，这是正常的。**
"""
import argparse, json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
GATE = pathlib.Path("/Users/linzezhang/Documents/Codex/AgentDatabase/"
                    "character-distillation-skill-reorganize-d57595/CodexSkills/registry/"
                    "codex/persona-distiller/scripts/quality_check.py")


def run(cmd, label):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return label, r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=pathlib.Path)
    ap.add_argument("--cache", nargs="*", default=[], help="语料目录，可多个")
    ap.add_argument("--rules", type=pathlib.Path, help="语义残留规则 JSON（该人物专属）")
    ap.add_argument("--extra", nargs="*", default=[], help="额外扫描的文件（如 judge payload）")
    a = ap.parse_args()

    ws = a.workspace
    hard, soft = [], []

    # ── 先验检查器本身：负对照不过，后面所有「全绿」都不作数 ──────────
    for script, args in (("check_quote_integrity.py", ["--claims", str(ws / "evidence" / "claims.jsonl"),
                                                       "--cache", *(a.cache or ["."]), "--self-test"]),
                         ("check_semantic_residue.py", ["--self-test"]),
                         ("check_claim_coverage.py", ["--self-test"])):
        sp = HERE / script
        if not sp.exists():
            continue
        _, rc, out = run([sys.executable, str(sp), *args], script)
        ok = "负对照通过" in out
        hard.append((f"self_test:{script.replace('check_','').replace('.py','')}",
                     0 if ok else 1,
                     [] if ok else ["负对照未过——本检查器的结论不作数"]))

    # ── 硬门：官方质检 ────────────────────────────────────────────────
    for ph in ("research", "synthesis", "release"):
        _, rc, out = run([sys.executable, str(GATE), str(ws), "--phase", ph, "--strict"], ph)
        try:
            d = json.loads(out)
            errs = d.get("errors", [])
        except (json.JSONDecodeError, ValueError):
            errs = [{"message": out.strip()[:200]}] if rc else []
        hard.append((f"quality_check:{ph}", len(errs),
                     [e.get("message", str(e)) if isinstance(e, dict) else str(e) for e in errs[:5]]))

    # ── 硬门：装饰性引用 ──────────────────────────────────────────────
    if a.cache:
        p = HERE / "check_claim_coverage.py"
        if p.exists():
            _, rc, out = run([sys.executable, str(p), "--workspace", str(ws),
                              "--cache", *a.cache], "coverage")
            hard.append(("claim_coverage", 0 if "通过" in out else 1, out.strip().splitlines()[-3:]))

    # ── 硬门：订正残留（有规则文件才跑）───────────────────────────────
    if a.rules and a.rules.exists():
        cmd = [sys.executable, str(HERE / "check_semantic_residue.py"),
               "--workspace", str(ws), "--rules", str(a.rules)]
        if a.extra:
            cmd += ["--extra", *a.extra]
        _, rc, out = run(cmd, "residue")
        n = 0 if "0 语义残留" in out else 1
        hard.append(("semantic_residue", n, [l for l in out.splitlines() if l.strip().startswith("✗")][:5]))
    else:
        soft.append(("semantic_residue", "跳过——该人物尚无订正历史，属正常"))

    # ── 只列不判：段内冗余与字段漂移 ─────────────────────────────────
    for script, args, label in (
            ("check_redundancy.py", ["--workspace", str(ws)] + (["--extra", *map(str, a.extra)] if a.extra else []), "redundancy"),
            ("check_schema_drift.py", ["--workspace", str(ws),
                                       "--expect", "cases.jsonl:holdout_source_ids"], "schema_drift"),
            ("check_claim_anchors.py", ["--workspace", str(ws)], "claim_anchors")):
        sp = HERE / script
        if not sp.exists():
            continue
        _, _, out = run([sys.executable, str(sp), *args], label)
        tail = [l for l in out.splitlines() if l.strip().startswith(("✓", "⚠"))]
        soft.append((label, tail[-1].strip() if tail else "（无输出）"))

    # ── 只列不判：不在场断言 ─────────────────────────────────────────
    p = HERE / "check_absence_claims.py"
    if p.exists():
        _, _, out = run([sys.executable, str(p), "--workspace", str(ws)], "absence")
        tail = [l for l in out.splitlines() if "合计" in l]
        soft.append(("absence_claims", tail[0] if tail else "（无输出）"))

    # ── 只列不判：引文真实性 ─────────────────────────────────────────
    p = HERE / "check_quote_integrity.py"
    cl = ws / "evidence" / "claims.jsonl"
    if p.exists() and cl.exists() and a.cache:
        _, _, out = run([sys.executable, str(p), "--claims", str(cl), "--cache", *a.cache], "quotes")
        tail = [l for l in out.splitlines() if "引文" in l and "片段" in l]
        soft.append(("quote_integrity", tail[0] if tail else "（无输出）"))

    print("══ 硬门 ══")
    failed = 0
    for name, n, detail in hard:
        print(f"  {'✓' if not n else '✗'} {name}: {n}")
        for d in detail:
            print(f"        {str(d)[:150]}")
        failed += bool(n)

    print("\n══ 只列不判（须人工看一眼，不得当错误直接改）══")
    for name, msg in soft:
        print(f"  · {name}: {msg}")

    print(f"\n{'✓ 硬门全过' if not failed else f'✗ {failed} 项硬门未过'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
