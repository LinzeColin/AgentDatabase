#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**评委指令要求按某个字段打分，而载荷里根本没有那个字段。**

## 为什么有这件

Mendel #125 第 1 轮**派发之后**才发现：

```
build_blind_payload.py  全文搜 `rubric` → **0 处**
载荷每项的键            → case_id / question / A / B
seat_D_score.md 提到 rubric → **5 处**，且四个分档全部以它为准：
    0.90–1.00：完全满足 rubric，且没有任何超出证据的断言
    0.50–0.74：部分满足，**缺一个 rubric 明确要求的要点**
```

**冻结指令要求按一份载荷里不存在的东西打分。**

这不是新缺陷（v0.0.0.41 就记过，是待裁定 ④ 与 ① 的根因之一），
**新的是它一直到派发之后才被人看见**——而那时已经改不得了：
改指令＝中途换尺子，补载荷＝两席看到不同的东西。

## 它做什么，不做什么

- **做**：把冻结指令里以反引号标出的字段名，与载荷实际的键**比一比**，
  指令里有而载荷里没有的，**在派发之前报出来**。
- **不做**：不判「该不该有 rubric」。**那是待裁定 ④，一个我不能自行选的口子**
  （给了 rubric 就不再是盲判，而 rubric 是产物作者写的）。
  本件只保证：**这个不一致不会再到派发之后才被发现。**

## 射程边界

- 只认**反引号里的标识符**（`` `rubric` ``）。指令里用散文说「按评分标准打分」，本件看不见。
- 只比字段名，不比语义：载荷有个 `question` 而指令写 `prompt`，
  **本件会报出来**——那正是该报的，两者是同一个东西却对不上名字。
"""
import argparse
import json
import pathlib
import re
import sys

# ★★ 第一版把 `candidate`／`baseline` 放进了忽略名单，**结果把最大的一处不一致藏住了**：
#   两席都写「给 `candidate` 和 `baseline` 各打一个分」，而载荷里是 `A`／`B`。
#   我当时想的是「这两个词不是载荷字段」——**恰恰相反，它们正是指令期望的字段名**，
#   而它们对不上才是要报的东西。忽略名单只该放**打分用语**，不该放字段名。
IGNORE = {"json", "note", "0", "1"}
_TICK = re.compile(r"`([A-Za-z_][A-Za-z0-9_]{1,24})`")


def fields_in_prompt(text: str) -> set:
    return {m.group(1) for m in _TICK.finditer(text)} - IGNORE


def payload_fields(payload: list) -> set:
    out = set()
    for item in payload:
        if isinstance(item, dict):
            out |= set(item.keys())
    return out


def audit(prompt_paths: list, payload_path: pathlib.Path) -> dict:
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except Exception as exc:                                     # noqa: BLE001
        return {"状态": f"载荷读不了，**未核（不是通过）**：{exc}"}
    have = payload_fields(payload)
    rows, missing_total = [], 0
    for p in prompt_paths:
        p = pathlib.Path(p)
        if not p.is_file():
            rows.append({"指令": str(p), "状态": "**文件不在——未核**"})
            continue
        want = fields_in_prompt(p.read_text(encoding="utf-8"))
        missing = sorted(want - have)
        missing_total += len(missing)
        rows.append({"指令": p.name, "指令里引到的字段": sorted(want),
                     "**载荷里没有的**": missing})
    return {"载荷字段": sorted(have), "**对不上的字段数**": missing_total, "逐席": rows,
            "★ 口径": "只报不判——「该不该有 rubric」是待裁定 ④，本件不替它选",
            "★ 射程": "只认反引号里的标识符；散文式的「按评分标准打分」看不见"}


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        pl = root / "payload.json"
        pl.write_text(json.dumps([{"case_id": "q-01", "question": "x", "A": "a", "B": "b"}]),
                      encoding="utf-8")
        bad = root / "seat_bad.md"
        bad.write_text("给 `A` 和 `B` 打分。0.90–1.00：完全满足 `rubric`。"
                       "每项含 `case_id` / `prompt` / `rubric`。", encoding="utf-8")
        good = root / "seat_good.md"
        good.write_text("只读 `case_id` 与 `question`，给 `A`/`B` 打分。", encoding="utf-8")

        print("── ★★ 反向对照①：指令要 `rubric` 而载荷没有 → 必须报出来 ──")
        r = audit([bad], pl)
        chk(f"{r['逐席'][0]['**载荷里没有的**']}", "rubric" in r["逐席"][0]["**载荷里没有的**"])
        print("── ★★ 反向对照②：`prompt` vs `question` 同物异名，**也要报** ──")
        chk("prompt 被报出", "prompt" in r["逐席"][0]["**载荷里没有的**"])
        print("── ★★ 反向对照③：对得上的指令**不报** ──")
        r2 = audit([good], pl)
        chk(f"{r2['**对不上的字段数**']}", r2["**对不上的字段数**"] == 0)
        print("── ★★ 反向对照④：**指令写 `candidate`/`baseline` 而载荷是 `A`/`B` → 必须报** ──")
        bad2 = root / "seat_ab.md"
        bad2.write_text("给 `candidate` 和 `baseline` 各打一个分。", encoding="utf-8")
        r4 = audit([bad2], pl)
        chk(f"{r4['逐席'][0]['**载荷里没有的**']}",
            {"candidate", "baseline"} <= set(r4["逐席"][0]["**载荷里没有的**"]))
        chk("★ 而载荷真有的 `A`/`B` 不被误报", not {"A", "B"} & set(r4["逐席"][0]["**载荷里没有的**"]))
        print("── ★ 反向对照⑤：载荷读不了 → 说「未核」，不说「通过」 ──")
        r3 = audit([good], root / "nope.json")
        chk(f"{r3.get('状态','')[:40]}", "未核" in str(r3.get("状态", "")))
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--payload", help="盲判载荷 JSON")
    ap.add_argument("--prompt", action="append", default=[], help="冻结指令 .md，可给多次")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.payload and a.prompt):
        ap.error("要么 --self-test，要么给 --payload 与至少一个 --prompt")
    info = audit(a.prompt, pathlib.Path(a.payload))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 1 if info.get("**对不上的字段数**") else 0


if __name__ == "__main__":
    sys.exit(main())
