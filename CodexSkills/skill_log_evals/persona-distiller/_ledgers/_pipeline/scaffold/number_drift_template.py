#!/usr/bin/env python3
# -*- coding: utf-8 -*-
## 为什么在 scaffold/ 而不在 checkers/（Robertson #97 移过来的）

它**不是通用检查器**：`RULES` 里的每一条正则都编码了「这个数字在这个人物的产物里
长什么句式」，换个人物一条都不能用；`import jm_stats` 与 `ws-maeda` 也都是硬编码。
放在 `checkers/` 里的后果是：跑 `--help` 直接 ImportError，
而一个跑不起来的「检查器」会让人误以为这一项检查做过了。

**定则：只要正文内容决定了规则本身，它就是模板不是工具。**

"""【脚手架】第八件检查器：产物里出现的计数，与从语料现算的值是否一致。

## 它补的是哪个缺口

已有的七件检查器方向都是「产物 → 语料」：引文在不在、实体在不在、有没有残留。
**没有一件查算术。** 而本轮真正的错误恰好是算术：

> 「38 篇动手笔记里 22 篇（58%）标题含年份」——真实值是 11 篇（29%）。

这个错误：
- 引文完整性检查器看不见（它不是引文）
- 覆盖度检查器看不见（关键实体「动手笔记」确实在源里）
- 官方质检门看不见（门查格式、引用、孤儿，不查我的乘除法）
- **人眼也很难看见**——58% 和 29% 都是「看起来合理」的数

它散在 6 处生成器 / 5 处产物。我是在自查计数时才发现的，
而自查是我自愿做的，不是任何门要求的。**自愿的检查不是检查。**

## 判据

从 `jm_stats.py` 取现算值，在产物文本里找**与之矛盾**的写法。

只对「有唯一正确答案」的量做检查（篇数、百分比、密度、维度源数）。
不检查描述性表述——那不是这件工具的职责。

**查不了要报查不了**：若某个量在产物里根本没出现，报「未出现」而不是「通过」。
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jm_stats import FACTS as F  # ← 每人改成自己的 <xx>_stats  # noqa: E402

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ws-maeda/john-maeda")

# (人类可读名, 正确值, 在产物里捕捉「这个位置的数」的正则)
# 正则必须捕获一个数字组；捕到的数字若与正确值不符即报错。
RULES = [
    # ★ 必须锚定「总数」的语境。第一版写成 r"(\d+)\s*篇动手笔记"，
    #   于是「涉及跑模型的 **8** 篇动手笔记」被当成总数，误报。
    #   与自指计数判据同一类错误：正则捕到了位置对、语义不同的数。
    ("动手笔记篇数", str(F["hands_n"]),
     r"(?:分母(?:均)?为|他的|共)\s*(\d+)\s*篇动手笔记|(\d+)\s*篇动手笔记[里中]"),
    # ★ 必须与「标题」或「年份」同现。原规则只写「动手笔记里 N 篇」，
    #   而我的产物里这个句式现在有两种含义（含年份 11 篇 / 含 because 8 篇），
    #   于是后者被当成前者误报。**同一句式承载两种量时，规则必须带语义锚。**
    ("标题含年份·篇数", str(F["year_hands"]),
     r"动手笔记里\s*(\d+)\s*篇(?=[^。\n]{0,12}(标题|年份))"),
    ("动手笔记含 because 篇数", str(F["because_n"]),
     r"动手笔记里\s*(\d+)\s*篇(?=[^。\n]{0,14}because)"),
    ("标题含年份·百分比", F["year_hands_pct"].rstrip("%"),
     r"动手笔记里\s*\d+\s*篇[（(](\d+)%"),
    ("随笔篇数", str(F["essay_n"]), r"署名随笔\s*(\d+)\s*篇中"),
    ("语料篇数", str(F["corpus_n"]), r"(\d+)\s*篇语料"),
    ("动手笔记密度", str(F["dens_hands"]), r"动手笔记为\s*([\d.]+)"),
    ("随笔密度", str(F["dens_essay"]), r"署名随笔为\s*([\d.]+)"),
    # ★ 判据放宽为「conversations 之后 30 字内出现 N 条源」。
    #   原来写死了「维度[仅只]有?」这一种句式，于是真实产物里的
    #   「`conversations` 只有 6 条源」（无「维度」二字）与
    #   「conversations 维度仅 7 条源」（无反引号）两种写法全部漏检，
    #   而漏检的那一处正是评委抓出来的 case-refuse-1。
    #   **句式枚举同样补不完**（第三十种），所以改为「锚词 + 邻近窗口」。
    ("conversations 源数", str(F["lanes_train"]["conversations"]),
     r"conversations[^。\n]{0,30}?(\d+)\s*条源"),
    ("Python 环境篇数", str(F["py"]), r"Python\s*环境管理\s*(\d+)\s*篇"),
    ("本机跑 LLM 篇数", str(F["llm"]), r"本机跑\s*LLM\s*(\d+)\s*篇"),
]


def scan():
    texts = {}
    for root, _, files in os.walk(W):
        for fn in files:
            if fn.endswith((".md", ".jsonl")):
                p = os.path.join(root, fn)
                texts[os.path.relpath(p, W)] = open(p, encoding="utf-8").read()
    return texts


def main() -> int:
    texts = scan()
    bad, checked, absent = [], 0, []
    for name, right, pat in RULES:
        rx = re.compile(pat)
        seen = 0
        for rel, txt in texts.items():
            for m in rx.finditer(txt):
                seen += 1
                got = next((g for g in m.groups() if g), None)
                if got is None:
                    continue
                if got != right:
                    ctx = txt[max(0, m.start() - 45):m.end() + 45].replace("\n", " ")
                    bad.append((name, right, got, rel, ctx))
        if seen == 0:
            absent.append(name)
        else:
            checked += seen

    print(f"产物文件 {len(texts)} 份；命中并核对 {checked} 处\n")
    if bad:
        print(f"══ 与语料现算值不符 {len(bad)} 处 ══")
        for name, right, got, rel, ctx in bad:
            print(f"  ✗ {name}：产物写 {got}，现算 {right}")
            print(f"     [{rel}] …{ctx}…")
    if absent:
        # ★ 未出现 ≠ 通过。若某个量本该出现却没出现，多半是我改文案时删掉了依据。
        print(f"\n══ 以下量在产物中**未出现**（未检查，不等于通过）: {len(absent)} ══")
        for n in absent:
            print(f"  ? {n}")
    print("\n结论: " + ("不通过" if bad else "通过"))
    return 2 if bad else 0


SELF_TEST = [
    # (文本, 规则名, 是否应报错)
    ("38 篇动手笔记里 11 篇标题嵌了年份", "标题含年份·篇数", False),
    ("38 篇动手笔记里 22 篇标题嵌了年份", "标题含年份·篇数", True),
    ("38 篇动手笔记里 8 篇含 because/reason", "标题含年份·篇数", False),   # 不同的量，不该被这条规则抓
    ("`conversations` 维度只有 6 条源，", "conversations 源数", True),
    ("`conversations` 只有 6 条源，", "conversations 源数", True),          # 无「维度」
    ("conversations 维度仅 7 条源（train 口径）", "conversations 源数", False),  # 无反引号
    ("`conversations` 维度仅 7 条源、为六维度中最少", "conversations 源数", False),
    ("他的 38 篇动手笔记里 11 篇标题嵌了年份", "动手笔记篇数", False),
    ("他的 40 篇动手笔记里 11 篇标题嵌了年份", "动手笔记篇数", True),
    ("涉及跑模型的 8 篇动手笔记全是本机方案", "动手笔记篇数", False),   # 不是总数，不该报
    ("（分母为 38 篇动手笔记）", "动手笔记篇数", False),
    ("（分母为 30 篇动手笔记）", "动手笔记篇数", True),
]


def self_test() -> int:
    """★ 检查器自身的负对照。本项目已有两次「写了检查器但从没验证过检查器本身」
    的教训（引文检查器前两版误报率均 100%）。没有自测的检查器不许进门。"""
    ok = 0
    for txt, rule, should in SELF_TEST:
        name, right, pat = next(r for r in RULES if r[0] == rule)
        fired = False
        for m in re.finditer(pat, txt):
            g = next((x for x in m.groups() if x), None)
            if g is not None and g != right:
                fired = True
        good = fired == should
        ok += good
        print(f"  {'✓' if good else '✗'} 应报={should!s:<5} 实报={fired!s:<5} {txt[:42]}")
    print(f"\n自测 {ok}/{len(SELF_TEST)}")
    return 0 if ok == len(SELF_TEST) else 2


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
