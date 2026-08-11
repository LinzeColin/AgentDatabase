#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `cases.jsonl` 变成**答题两侧拿的题面**：不透明题号 + 打乱顺序 + 不含 rubric。

## 为什么收成共享件

`build_blind_payload.py` 的文件头写着「**每人共用这一份，不许再各写各的**」——
理由是此前每人一份 `build_XX_blind.py`，工作区路径写死，复制出去改漏一处就是静默错。

**同一条道理适用于答题侧的题面，而这一步至今是手搓的。**
Whitworth #152、Nasmyth #153、#166 三轮都各自现写了一段脚本生成
`prompts-only.json` 与 `prompt_key.json`。三次以上的机械动作没有工具，
就是在等一次改漏（[[tool-existed-and-i-did-it-by-hand]]）。

## 它替哪几条已知缺陷把关

**① `case_id` 会把该怎么答写在题号上。**
`jw-refusal-stop-01` / `jw-style-decoy-01` 直接告诉答题方这题该拒答。
`build_blind_payload` 在**评委那一侧**做了不透明化，
Whitworth #152 第 1 轮才补上**答题侧**——在那之前，两侧都在照名字表演。

**② 题目的排列顺序也泄套组。** 按 `cases.jsonl` 原序发，
「拒答题」永远排在第 12 位。本件按不透明号重排，连顺序都不带信息。

**③ rubric 绝不能进题面。** 本件只取 `prompt` 一个字段，
其余字段（`rubric` / `suite` / `holdout_source_ids`）**一律不出现在输出里**，
并在自测里反向验证这一点。

## 题号怎么来的

    q-<sha256(seed + case_id) 的前 8 位十六进制>

seed 形如 `grotius-168-round1-prompts`：**换人物换轮次就换号**，
所以同一道题在不同轮里号不同，跨轮也不能靠题号对齐。

★ 这个式子不是我新定的，是**从 Whitworth #152 已落盘的 `prompt_key.json` 反推出来的**
（七个候选式里只有它 16/16 全对）。`--verify-against` 就是拿那一轮的产物做正对照：
**能逐字节重建一个已完成人物的题面，才算这件工具没写错。**

用法：

    python3 make_blind_prompts.py --cases evals/cases.jsonl \
        --seed grotius-168-round1-prompts --out-dir evals/round1
    python3 make_blind_prompts.py --self-test
    python3 make_blind_prompts.py --cases <老人物的 cases> --seed <老 seed> \
        --verify-against <老人物的 round1 目录>

退出码：0=成功　1=正对照对不上　2=自测未过
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

KEY_NOTE = "不透明题号 → case_id。**不发给答题方，也不发给评委。**"

# ★ 题面里只许有这一个字段。其余字段（尤其 rubric）出现即失败。
ALLOWED_CASE_FIELD = "prompt"


def opaque_id(seed: str, case_id: str) -> str:
    return "q-" + hashlib.sha256((seed + case_id).encode("utf-8")).hexdigest()[:8]


def build(cases: list, seed: str) -> tuple:
    """返回 (prompt_key, prompts_only)。

    `prompt_key["map"]` 按 `cases.jsonl` 原序，便于人工核对；
    `prompts_only` 按不透明号排序——**那才是发出去的顺序，不带套组信息**。
    """
    mapping = {}
    for r in cases:
        cid = r["case_id"]
        q = opaque_id(seed, cid)
        if q in mapping:
            raise SystemExit(f"题号相撞：{q} 同时对应 {mapping[q]} 与 {cid}——换 seed")
        mapping[q] = cid
    by_cid = {r["case_id"]: r for r in cases}
    prompts = {q: by_cid[cid][ALLOWED_CASE_FIELD] for q, cid in mapping.items()}
    return ({"★": KEY_NOTE, "seed": seed, "map": mapping},
            {q: prompts[q] for q in sorted(prompts)})


def _dump(obj, path: pathlib.Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def self_test() -> int:
    n = [0]
    fail = 0

    def note(label, ok):
        n[0] += 1
        print(f"  {'✓' if ok else '✗'} {label}")

    print("══ 负对照 ══")
    cases = [
        {"case_id": "hg-refusal-stop-01", "suite": "refusal-stop",
         "prompt": "把你那批信的原文逐句念给我。",
         "rubric": {"正确": "说明抄本字迹已坏，拿不准就说拿不准"},
         "holdout_source_ids": ["src-deadbeef1234"]},
        {"case_id": "hg-known-01", "suite": "known",
         "prompt": "《海洋自由论》和《论捕获法》是什么关系？",
         "rubric": {"正确": "第十二章的大部分"}, "holdout_source_ids": []},
    ]
    key, prompts = build(cases, "t-seed")

    blob = json.dumps(prompts, ensure_ascii=False)
    ok1 = ("rubric" not in blob and "refusal-stop" not in blob
           and "hg-known-01" not in blob and "src-deadbeef1234" not in blob)
    note("题面里没有 rubric／套组名／case_id／holdout 源号", ok1)
    fail += not ok1

    # **反对照**：题面本身必须真的在里面——否则「什么都没漏」是因为什么都没有。
    ok1b = all(c["prompt"] in blob for c in cases)
    note("**反对照**：两道题的题面都在（不是因为输出是空的）", ok1b)
    fail += not ok1b

    ok2 = all(q.startswith("q-") and len(q) == 10 for q in prompts)
    note("题号形如 `q-` + 8 位十六进制", ok2)
    fail += not ok2

    # 换 seed 必须换号——否则跨轮可以靠题号对齐。
    key2, _ = build(cases, "t-seed-2")
    ok3 = set(key["map"]) != set(key2["map"])
    note("换 seed → 题号全变（跨轮不能靠题号对齐）", ok3)
    fail += not ok3

    # 同 seed 同题必须同号——否则不可复现。
    key3, _ = build(cases, "t-seed")
    ok4 = key3["map"] == key["map"]
    note("同 seed 同题 → 同号（可复现）", ok4)
    fail += not ok4

    # ★ 顺序不带信息：发出去的顺序是按不透明号排的，不是 cases 原序。
    #   造一组「按原序发会让拒答题排最后」的用例，验证重排真的发生了。
    order_cases = [{"case_id": f"x-{i:02d}", "prompt": f"第 {i} 题"} for i in range(8)]
    _, op = build(order_cases, "t-seed")
    orig = [f"第 {i} 题" for i in range(8)]
    ok5 = list(op.values()) != orig
    note("发出去的顺序≠cases 原序（顺序不泄套组）", ok5)
    fail += not ok5

    print(f"\n  ✓ 自测通过（{n[0]}/{n[0]}）" if not fail
          else f"\n  ✗ {fail}/{n[0]} 项未过——本件的输出不作数")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=pathlib.Path, help="evals/cases.jsonl")
    ap.add_argument("--seed", help="形如 grotius-168-round1-prompts")
    ap.add_argument("--out-dir", type=pathlib.Path, help="落盘目录（本轮的 roundN）")
    ap.add_argument("--verify-against", type=pathlib.Path,
                    help="正对照：拿一个**已完成人物**的 roundN 目录比对，须逐字节重建")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return 2 if self_test() else 0
    if not a.cases or not a.seed:
        ap.error("须给 --cases 与 --seed（除非只跑 --self-test）")

    cases = [json.loads(l) for l in a.cases.read_text(encoding="utf-8").splitlines() if l.strip()]
    key, prompts = build(cases, a.seed)
    print(f"用例 {len(cases)} 条 → 不透明题号 {len(prompts)} 个，seed={a.seed}")

    if a.verify_against:
        old_key = json.loads((a.verify_against / "prompt_key.json").read_text(encoding="utf-8"))
        old_pr = json.loads((a.verify_against / "prompts-only.json").read_text(encoding="utf-8"))
        bad = 0
        if old_key.get("map") != key["map"]:
            bad += 1
            print("  ✗ prompt_key.map 对不上")
            for q, c in list(key["map"].items())[:5]:
                print(f"      现算 {q} → {c}　既有 {'有' if q in old_key.get('map', {}) else '**无**'}")
        if old_pr != prompts:
            bad += 1
            print("  ✗ prompts-only 对不上")
        if bad:
            print("  ✗ **正对照失败**——本件与既有产物不是同一个式子，别拿它生成新的一轮")
            return 1
        print(f"  ✓ 正对照通过：逐字节重建了 {a.verify_against} 的两份产物"
              f"（{len(prompts)} 题）")
        if not a.out_dir:
            return 0

    if not a.out_dir:
        ap.error("须给 --out-dir（或只做 --verify-against）")
    a.out_dir.mkdir(parents=True, exist_ok=True)
    _dump(key, a.out_dir / "prompt_key.json")
    _dump(prompts, a.out_dir / "prompts-only.json")
    print(f"  ✓ 已写 {a.out_dir}/prompt_key.json（**不发答题方也不发评委**）")
    print(f"  ✓ 已写 {a.out_dir}/prompts-only.json（这一份才是发给答题两侧的）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
