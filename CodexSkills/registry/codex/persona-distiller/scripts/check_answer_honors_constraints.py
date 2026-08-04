#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**题面写死的约束，答案接住了吗？**

## 为什么有这道判据

Barton #117 第 3 轮两席点名的候选缺陷里，**三处不是知识缺口**：

- 题目要「用这个称号写一段自我介绍」→ 答成了「否认称号＋履历条目」
- 题面已写明「不用管史实」→ 仍然拒写
- 题设「三天后才能进场」→ 头一条仍讲「能早到一刻就早到一刻」

**这三条都是没接住题面写死的约束。** 而当时没有任何判据在看这件事——
`check_case_self_sufficiency` 管题面自不自足，**不管答案有没有照题面答**。

## 它只检**声明过的**约束

题面里的约束是自然语言写的，**提取它本身就要理解题面**——这一点已经试过并否掉：
拿「题面出现的数字，答案碰没碰」做探针，32 题只覆盖 9 题，
而且**没抓到席 E 抱怨的那道**（题面写的是「五万」，汉字数词，正则看不见）。

所以本件**不猜**：只检 `cases.jsonl` 里显式写下的 `constraints`。
出题人把约束写成可机检的形式，判据才管得着；**没写的，本件明说「未声明」，不当成通过**。

## 支持的约束种类

| `kind` | `value` | 含义 |
|---|---|---|
| `exact_sentences` | 整数 | 句子数必须恰好等于（按 `。！？.!?` 数） |
| `max_sentences` | 整数 | 句子数不得超过 |
| `max_lines` | 整数 | 非空行数不得超过 |
| `must_contain` | 字符串或字符串数组 | 必须出现（全部） |
| `must_not_match` | 正则 | 不得命中 |
| `min_items` | 整数 | 至少这么多个列举项（按行首序号／「第 N」计） |

## 它判不了什么

- **判不了答得对不对**——约束全过，内容仍可能是错的。
- **判不了没声明的约束。** 出题人不写，它就看不见——
  **所以「0 处未过」不等于「全部接住了」，要连「声明了几条」一起读。**
"""
import argparse
import json
import pathlib
import re
import sys

SENT_END = re.compile(r"[。！？!?]|\.(?:\s|$)")
ITEM = re.compile(r"^\s*(?:[一二三四五六七八九十]+[、.）)]|\d+[.、）)]|第[一二三四五六七八九十\d]+)", re.M)


def count_sentences(text: str) -> int:
    return len(SENT_END.findall(text))


def count_lines(text: str) -> int:
    return len([l for l in text.splitlines() if l.strip()])


INLINE_ITEM = re.compile(r"第[一二三四五六七八九十]")


def count_items(text: str) -> int:
    """→ 列举项数，取「行首序号」与「行内『第 N』」两种计法的**较大值**。

    ★ 第一版写成「行首计法有命中就返回它，否则回退」——
    单行文本 `第一，甲。第二，乙。第三，丙。` 里 `^` 只在开头匹配一次，
    于是返回 1 而不是 3，**永远走不到回退分支**。
    自测当场抓到。
    """
    return max(len(ITEM.findall(text)), len(INLINE_ITEM.findall(text)))


def check_one(answer: str, kind: str, value) -> str:
    """→ 未过时的说明；过了返回空串。"""
    if kind == "exact_sentences":
        n = count_sentences(answer)
        return "" if n == value else f"句子数 {n} ≠ 要求的 {value}"
    if kind == "max_sentences":
        n = count_sentences(answer)
        return "" if n <= value else f"句子数 {n} > 上限 {value}"
    if kind == "max_lines":
        n = count_lines(answer)
        return "" if n <= value else f"非空行数 {n} > 上限 {value}"
    if kind == "must_contain":
        want = [value] if isinstance(value, str) else list(value)
        miss = [w for w in want if w not in answer]
        return "" if not miss else f"缺少必须出现的内容：{miss}"
    if kind == "must_not_match":
        m = re.search(value, answer)
        return "" if not m else f"命中了不许出现的形态 `{value}`：`{m.group(0)[:40]}`"
    if kind == "min_items":
        n = count_items(answer)
        return "" if n >= value else f"列举项 {n} < 要求的 {value}"
    return f"★ **未知的约束种类 `{kind}`——本件看不懂它，不当成通过**"


def evaluate(cases: list, answers: dict) -> tuple:
    problems, declared, checked = [], 0, 0
    for c in cases:
        cid = c.get("case_id")
        cons = c.get("constraints") or []
        if not cons:
            continue
        declared += len(cons)
        if cid not in answers:
            problems.append(f"`{cid}` 声明了 {len(cons)} 条约束，**但没有答案**——未核（不是通过）")
            continue
        checked += len(cons)
        for con in cons:
            why = check_one(answers[cid], con.get("kind", ""), con.get("value"))
            if why:
                problems.append(f"`{cid}`（{con.get('kind')}）：{why}")
    info = {
        "用例数": len(cases),
        "声明了约束的用例": sum(1 for c in cases if c.get("constraints")),
        "声明的约束条数": declared,
        "实际核过的": checked,
        "**未过**": len(problems),
        "口径": ("**只检显式声明的约束**——题面里的自然语言约束提取不了（已试过并否掉）。"
                 "**「0 处未过」不等于「全部接住了」**，要连「声明了几条」一起读。"),
    }
    return problems, info


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：Barton #117 那三处失分的形状 ──")
    # ① 题目要「用这个称号写自我介绍」，答成了否认＋履历
    cases = [{"case_id": "x-decoy", "constraints": [{"kind": "must_contain", "value": "战地天使"}]}]
    pb, _ = evaluate(cases, {"x-decoy": "我不接受这个说法。我做过的事如下：一、……二、……"})
    chk(f"没用那个称号 → 报出（实报 {len(pb)}）", len(pb) == 1 and "缺少必须出现" in pb[0])
    # ② 题面写死「只用一个句子」，答了三句
    cases = [{"case_id": "x-one", "constraints": [{"kind": "exact_sentences", "value": 1}]}]
    pb, _ = evaluate(cases, {"x-one": "第一句。第二句。第三句。"})
    chk("三句 vs 要求一句 → 报出", len(pb) == 1 and "句子数 3" in pb[0])
    # ③ 题设「三天后才能进场」——写成不许出现「立刻/马上」
    cases = [{"case_id": "x-plan",
              "constraints": [{"kind": "must_not_match", "value": r"立刻|马上|第一时间"}]}]
    pb, _ = evaluate(cases, {"x-plan": "能早到一刻就早到一刻，第一时间进场。"})
    chk("命中不许出现的形态 → 报出", len(pb) == 1 and "不许出现" in pb[0])

    print("── 反向对照 ①：接住了的一条都不报 ──")
    cases = [{"case_id": "ok", "constraints": [
        {"kind": "exact_sentences", "value": 1},
        {"kind": "must_contain", "value": "卫生"}]}]
    pb, info = evaluate(cases, {"ok": "一国的健康首先取决于卫生条件。"})
    chk(f"两条都过 → 一条不报（核过 {info['实际核过的']} 条）", not pb and info["实际核过的"] == 2)

    print("── ★ 反向对照 ②：没声明约束的用例不归本件管 ──")
    #   出题人不写，本件就看不见——这一条必须显式，不许假装检过。
    pb, info = evaluate([{"case_id": "bare"}], {"bare": "随便答的。"})
    chk("不报，且「声明的约束条数」为 0", not pb and info["声明的约束条数"] == 0)

    print("── ★ 反向对照 ③：声明了约束却没有答案 → 报「未核（不是通过）」──")
    pb, _ = evaluate([{"case_id": "no-ans", "constraints": [{"kind": "max_lines", "value": 3}]}], {})
    chk("报出且写明未核", len(pb) == 1 and "未核" in pb[0])

    print("── ★ 反向对照 ④：看不懂的约束种类不许当成通过 ──")
    pb, _ = evaluate([{"case_id": "weird", "constraints": [{"kind": "vibes", "value": 1}]}],
                     {"weird": "答案"})
    chk("报出「未知的约束种类」", len(pb) == 1 and "未知的约束种类" in pb[0])

    print("── 反向对照 ⑤：句子数按中英标点都算 ──")
    chk("「甲。乙！丙？」= 3 句", count_sentences("甲。乙！丙？") == 3)
    chk("英文句点后跟空白才算句末（小数点不算）",
        count_sentences("It is 3.5 metres. And more.") == 2)

    print("── 反向对照 ⑥：列举项按序号或「第 N」计 ──")
    chk("「第一，…第二，…第三，…」= 3 项", count_items("第一，甲。第二，乙。第三，丙。") == 3)
    chk("「一、…二、…」= 2 项", count_items("一、甲\n二、乙") == 2)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", help="cases.jsonl")
    ap.add_argument("--answers", help="{case_id: 答案} 的 JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.cases and a.answers):
        ap.error("要么 --self-test，要么同时给 --cases 与 --answers")

    cases = [json.loads(l) for l in
             pathlib.Path(a.cases).read_text(encoding="utf-8").splitlines() if l.strip()]
    answers = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    problems, info = evaluate(cases, answers)
    for k, v in info.items():
        print(f"  {k}: {v}")
    if not info["声明的约束条数"]:
        print("\n  ⚠ **一条约束都没声明——本次未检查（不是通过）**")
        return 0
    if not problems:
        print("\n  ✓ 声明的约束全部接住")
        return 0
    print()
    for p in problems:
        print("✗ " + p)
    print("\n**题面写死的约束不接住，内容再好也不算答对——改答案，不要改题。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
