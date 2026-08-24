#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问的是**原话**，答的是「你自己去查」——**回归护栏，不是缺陷修复**。

★ 原标题写的是「`fact-preservation` 整组偏弱的一个可判成因」。
  **那个说法已被真数据推翻**：候选 0/10、基线 3/10，这是基线的失败形态。
  `fact-preservation` 为什么整组偏弱，**至此仍未解释**——不要拿这条去顶那个坑。

## ★★★ 先说一处我自己的读错，因为它决定了这道判据是干什么用的

我最初把下面那几条评语读成**对候选的批评**，据此立本判据去「修缺陷」。
**跑了真数据才知道方向读反了。**

同一批题面、5 人配对实测（`fleming / lister / nightingale / osler / virchow`，
每人 32 题两侧都答，共 **10 道**「问原话/出处」的题）：

```
候选只给指路：**0 / 10（0%）**
基线只给指路：**3 / 10（30%）**
```

**「让人自己去查」是基线的失败形态，候选恰恰是给逐字引文与卷页的那一侧。**
评语里的 A/B 是盲态标签，我按「谁写得好」去猜哪边是候选——**猜错了**。

**所以本判据不是修缺陷的，是守住产品已经有的一项优势**——
它是回归护栏：哪天候选开始把原话推给读者，这里会红。

## 触发本判据的实例（两席各自独立写下，7 条评语，非我转述；★ 描述的是**基线**那一侧）

| 席 | 原话 |
|---|---|
| D | 「问『原话是怎么说的』，**A 描述完现象后让人自己去查论文，等于半题未答**」 |
| D | 「问原文措辞。**A 给两句原文……B 只作意译并让人去官网查，恰恰把被问的那部分省了**」 |
| E | 「问的是原话。**A 描述完却说「原文措辞需查阅那篇论文」，等于没答**」 |
| E | 「**卷页一概推给对方自查，属于该给而不给**」 |

## 为什么 `check_refusal_overflow` 抓不到

那道判据是「**有拒答标记 且 可执行判断数 == 0**」。
而这类答案**给了行动指示**（「去查那篇论文」），判断数 > 0，**按设计就不该被它抓到**。
两者是不同的缺陷：

- 拒答溢出：**我不答，而且什么也没留下**
- 本判据：**我答了别的、还指了路，唯独没给被问的那一项**

## 判据（三条同时满足才算）

1. **题面在问原话或出处**：原话／原文／措辞／怎么说的／确切用词／出处／卷／页／发在哪
2. **答案里有「你自己去查」的指路**：查阅／自行查／去官网／参见该文／见原刊
3. **答案里既没有逐字引文（「…」）也没有定位符**（卷/页/pp./No./期）

★ **三条是「且」**：单看任何一条都会误报——
题面问出处而答案给了卷页，那是**答对了**；答案给引文又顺带指路，那是**答得更好**。

## 它不做什么

- **不把诚实的「我手上没有原文」判为缺陷。** 那句话里没有「你去查」的指路，
  第 2 条就不成立。**「拒绝／弃权」不是缺陷**——这条纪律在本判据里是硬的。
- **不判引文真伪。** 那是 `check_quote_integrity` 与 `check_quote_locator` 的事。
- **不判题面好坏。** 那是 `check_case_self_sufficiency`。

## 分母

**必须连「这类题共几道」一起读。** 一个人物一道这类题都没有时，
本判据报「未核」，**不报「通过」**——两者长得一样，是本项目栽过很多次的地方。
"""
import argparse
import json
import pathlib
import re
import sys

ASKS_VERBATIM = re.compile(
    r"原话|原文|措辞|确切用词|怎么说的|原样|逐字|出处|卷[号期]?|页码|发(表)?在哪|哪一期|篇名", re.I)
POINTS_AWAY = re.compile(
    r"自[行己]查|请查阅|需查阅|去官网|上官网|参见(该|那)[篇本]|见原(刊|文|书)|"
    r"查(一下|阅)?(那|该)[篇本]|自己去查|可以查到|建议查", re.I)
HAS_QUOTE = re.compile(r"「[^」]{8,}」|“[^”]{8,}”|\"[^\"]{12,}\"")
HAS_LOCATOR = re.compile(
    r"\d+\s*[卷期]|\d+\s*[（(]\d+[)）]|pp?\.\s*\d+|[Nn]o\.\s*\d+|"
    r"\d+\s*[-–]\s*\d+\s*页|第\s*\d+\s*页|\d+:\d+[-–]\d+|vol\.?\s*\d+", re.I)


def judge(question, answer):
    """→ (是不是这类题, 有没有毛病, 命中了哪几条)。**三条同时成立才算有毛病。**"""
    asks = bool(ASKS_VERBATIM.search(question or ""))
    if not asks:
        return False, False, {}
    a = answer or ""
    hits = {"指路": bool(POINTS_AWAY.search(a)),
            "有引文": bool(HAS_QUOTE.search(a)),
            "有定位符": bool(HAS_LOCATOR.search(a))}
    bad = hits["指路"] and not hits["有引文"] and not hits["有定位符"]
    return True, bad, hits


def evaluate(cases, answers):
    """→ (问题列表, 计量)。**计量里必须带分母。**"""
    by_id = {}
    for c in cases:
        cid = c.get("case_id") or c.get("id")
        if cid:
            by_id[cid] = c.get("prompt") or c.get("question") or c.get("题面") or ""
    problems, n_kind = [], 0
    for cid, ans in (answers or {}).items():
        if isinstance(ans, dict):
            ans = ans.get("answer") or ans.get("text") or ""
        is_kind, bad, hits = judge(by_id.get(cid, ""), ans)
        if is_kind:
            n_kind += 1
            if bad:
                problems.append(f"{cid}：题面问原话/出处，答案**只给了指路**"
                                f"（无逐字引文、无卷页定位符）")
    info = {"答案总数": len(answers or {}),
            "**问原话/出处的题**": n_kind,
            "其中只给指路的": len(problems)}
    if not n_kind:
        info["状态"] = "**本人物没有这类题——未核，不是通过**"
    return problems, info


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    Q = "他当时的原话是怎么说的？"
    print("── ★★ 正向：Fleming 那一幕（席 D、E 各自写下的那种答案）──")
    chk("描述完现象 + 让人自己去查论文 → 报出",
        judge(Q, "培养皿边缘的菌落溶解了，很显眼。原文措辞需查阅那篇论文。")[1])

    print("── ★★ 反向对照 ①：给了逐字引文 → **不报**（那是答对了）──")
    chk("有「…」→ 不报",
        not judge(Q, "他写的是「a bacteriolytic element present in tissues」，"
                     "详见那篇论文。")[1])

    print("── ★★ 反向对照 ②：给了卷页定位符 → **不报** ──")
    chk("有 10(3):226-236 → 不报",
        not judge(Q, "见 Brit J Exp Path 10(3):226-236，可以查到。")[1])
    chk("有「第 219 页」→ 不报", not judge(Q, "请查阅原刊第 219 页。")[1])

    print("── ★★★ 反向对照 ③：诚实的「我手上没有原文」**不是缺陷** ──")
    chk("只说没有、不指路 → 不报",
        not judge(Q, "他确实说过这个意思，但**原文我手上没有**，我不复述我没有的东西。")[1])
    chk("只说没有、不指路 → 也不该被算成「有毛病」",
        judge(Q, "原文我手上没有。")[1] is False)

    print("── 反向对照 ④：题面根本不问原话 → 不是这类题 ──")
    is_kind, bad, _ = judge("他为什么坚持这么做？", "因为他觉得该这么做，你可以去查那篇论文。")
    chk("不是这类题，且不报", not is_kind and not bad)

    print("── ★★ 反向对照 ⑤：分母——一道这类题都没有时报「未核」，不报「通过」──")
    _, info = evaluate([{"case_id": "x", "prompt": "他为什么这么想？"}], {"x": "因为……"})
    chk(f"n_kind={info['**问原话/出处的题**']}，状态：{info.get('状态', '（无）')[:20]}",
        info["**问原话/出处的题**"] == 0 and "未核" in info.get("状态", ""))

    print("── ★ 反向对照 ⑥：分母不为 0 时不许再报「未核」──")
    _, info2 = evaluate([{"case_id": "y", "prompt": Q}], {"y": "「原话在此处」"})
    chk("有这类题 → 无「未核」字样", "状态" not in info2 and info2["**问原话/出处的题**"] == 1)

    print("── ★ 反向对照 ⑦：题面对不上号的答案不许静默算过 ──")
    _, info3 = evaluate([{"case_id": "a", "prompt": Q}], {"b": "答非所问"})
    chk(f"答案 id 与题面对不上 → 这类题数 {info3['**问原话/出处的题**']}（不是 1）",
        info3["**问原话/出处的题**"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", help="cases.jsonl")
    ap.add_argument("--answers", help="judge_payload.v1.json")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.cases and a.answers):
        print("✗ **什么都没核**——两个输入都要给。这不是通过。")
        return 2

    cases = [json.loads(l) for l in pathlib.Path(a.cases).read_text(encoding="utf-8").splitlines()
             if l.strip()]
    answers = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    problems, info = evaluate(cases, answers)
    for k, v in info.items():
        print(f"  {k}: {v}")
    for p in problems:
        print(f"  · {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
