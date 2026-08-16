#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这个证据字段是逐条的，还是填了一次抄了 N 遍？**

## 为什么有这件

`check_claim_anchors` / `check_claim_coverage` 核的是「断言有没有挂上源」。
**Koch #107 的 46 条断言全部挂上了源——挂的是同一对文件。**

实测（2026-08-04，十个工作区）：

| 人物 | 断言 | `source_ids` 不同组合 | `evidence_clusters` 不同取值 |
|---|---:|---:|---:|
| Fleming #111 | 33 | 26 | 32 |
| Godin | 31 | 30 | 30 |
| Nightingale #112 | 41 | 31 | 38 |
| Virchow #109 | 60 | 20 | 21 |
| Steinhardt #98 | 39 | 18 | 21 |
| Pasteur #106 | 33 | 15 | 3 |
| Osler #110 | 44 | 11 | 11 |
| **Jenner #104** | 35 | 21 | **1** |
| **Koch #107** | 46 | **1** | **2** |
| **Lister #108** | 35 | **1** | **1** |

**七个人是逐条各异的，三个人不是。**

Koch 那一对是 `b21463608_0001.txt` 与 `b21353207_0001_0.txt`，两份都是 P1。
**问题不在于它们不是好源**，而在于：46 条断言共用同一对时，
**这个字段对「哪一条断言站得住」不提供任何区分度**——
读它的判据于是在核一个常量。

## ★ 它说的不是「这些断言是编的」

**它只说这个字段不再有信息量。** 那一对文件也许真的覆盖了绝大多数内容
（Koch 的《Gesammelte Werke》确实是合集）。
但**合集级的挂靠 ≈ 没有挂靠**：出了问题你回不到是哪一段。

**这是 v0.0.0.24 那条的同型第二例**——当年一句 `attribution_basis`
让**整批免检**，逐源检查从此十版没跑过。
**一个字段填了一次抄 N 遍，与一句话让整批免检，效果一样。**

## 三种状态必须分开，**不许合并**

| 状态 | 含义 | 报不报 |
|---|---|---|
| **逐条各异** | 真的是逐条证据 | 不报 |
| **整批同一个值** | **表头冒充证据** | **报** |
| **整批都空** | 这个字段没被使用 | **单独报，不是同一件事** |

`counter_source_ids` 十个人里六个全空——**那是「没用这个字段」，
不是「填了一个假值」**。混为一谈会把「诚实地没有对手材料」
（Godin、Nightingale、Osler）报成缺陷。

## 它判不了什么

- **判不了那一对源是不是真的支持这条断言**——那要回读正文，是 `check_quote_integrity` 的活。
- **断言少时不判**：3 条断言共用一组源完全正常，**没有「变化」可谈**。
- **判不了散文里的证据说明**。Koch 每条都写着「对手方原文（双方语料均在本机）」，
  而 `counter_source_ids` **0/46**——**散文里的证据声明不是机器可核的链接**
  （见 `self-report-is-not-evidence`）。本件只报字段，不解释散文。
"""
import argparse
import collections
import json
import pathlib
import sys

# 断言里带证据含义的字段。值可能是列表，也可能是标量。
EVIDENCE_FIELDS = ("source_ids", "evidence_clusters", "counter_source_ids")
MIN_RECORDS = 10          # 少于这个数不判——**没有「变化」可谈**
FEW_RATIO = 0.10          # 不同取值数 < 记录数 × 这个比例，也算「几乎是表头」


def _key(value):
    """把字段值收敛成可哈希的比较键；**列表按排序后比较**（顺序不算差异）。"""
    if isinstance(value, list):
        return tuple(sorted(str(v) for v in value))
    if value is None:
        return ()
    return (str(value),)


def audit(claims, fields=EVIDENCE_FIELDS, min_records=MIN_RECORDS):
    """→ {field: (状态, 记录数, 非空数, 不同取值数)}。

    状态 ∈ {'逐条各异', '表头', '几乎是表头', '整批都空', '记录太少不判'}
    """
    out = {}
    n = len(claims)
    for f in fields:
        keys = [_key(c.get(f)) for c in claims]
        nonempty = [k for k in keys if k]
        distinct = len(set(nonempty))
        # ★★ 分母必须是**非空数**，不是记录总数。
        #    第一版拿 n 当分母，真实数据立刻误报三处：
        #    Jenner `counter_source_ids` 非空 1/35、Steinhardt 非空 4/39、
        #    Pasteur 非空 3/33——**它们是「这个字段用得少」，不是「填了一个假值」**。
        #    （Steinhardt 4 条里有 3 种取值，变化度其实很好。）
        if not nonempty:
            state = "整批都空"
        elif len(nonempty) < min_records:
            # **用得太少就没有「变化」可谈**——少数几条共用一组完全正常。
            state = "用得太少不判"
        elif distinct <= 1:
            state = "表头"
        elif distinct < max(2, len(nonempty) * FEW_RATIO):
            state = "几乎是表头"
        else:
            state = "逐条各异"
        out[f] = (state, n, len(nonempty), distinct)
    return out


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    def claims(vals, field="source_ids"):
        return [{field: v} for v in vals]

    print("── ★ 正向：Koch #107 的真实形状（46 条共用同一对源）──")
    r = audit(claims([["a", "b"]] * 46))
    print(f"    source_ids → {r['source_ids']}")
    chk("46 条同一组 → **表头**（不是「逐条各异」）", r["source_ids"][0] == "表头")
    chk("同时报出不同取值数 = 1", r["source_ids"][3] == 1)

    print("── ★ 正向：Jenner #104 的形状（evidence_clusters 35 条一个值）──")
    r = audit(claims([["x", "y", "z"]] * 35, field="evidence_clusters"))
    chk("35 条同一个 clusters → 表头", r["evidence_clusters"][0] == "表头")

    print("── ★★ 反向对照 ①：**逐条各异的七个人不许被报** ──")
    r = audit(claims([[f"s{i}"] for i in range(33)]))
    print(f"    33 条各不相同 → {r['source_ids'][0]}")
    chk("Fleming 那种 26/33 的形状 → 逐条各异", r["source_ids"][0] == "逐条各异")
    r = audit(claims([[f"s{i//2}"] for i in range(44)]))    # Osler 11/44 量级
    chk("Osler 那种 11 组 / 44 条 → 仍算逐条各异（不是表头）",
        r["source_ids"][0] == "逐条各异")

    print("── ★★ 反向对照 ②：**「整批都空」不许报成「表头」** ──")
    r = audit([{"counter_source_ids": []} for _ in range(46)])
    print(f"    counter_source_ids → {r['counter_source_ids'][0]}")
    chk("六个人的 counter 全空 → 报「整批都空」，**不是缺陷同一件事**",
        r["counter_source_ids"][0] == "整批都空")
    chk("Godin 那种诚实地没有对手材料，不许被当成填假值",
        r["counter_source_ids"][0] != "表头")

    print("── ★ 反向对照 ③：**断言少时不判**（没有「变化」可谈）──")
    r = audit(claims([["a", "b"]] * 3))
    chk("3 条共用一组 → 不判", r["source_ids"][0] == "用得太少不判")

    print("── ★★★ 反向对照 ⑦：**三处真实误报夹具**（第一版拿总数当分母，真数据一跑就错）──")
    # Jenner #104：counter_source_ids 非空 1 / 35
    r = audit([{"counter_source_ids": ["c1"] if i == 0 else []} for i in range(35)])
    print(f"    Jenner 形状 非空 1/35 → {r['counter_source_ids'][0]}")
    chk("非空 1/35 → **用得太少不判**（第一版报「表头」，错）",
        r["counter_source_ids"][0] == "用得太少不判")
    # Steinhardt #98：非空 4 / 39，其中 3 种取值——**变化度其实很好**
    r = audit([{"counter_source_ids": [f"c{i}"] if i < 3 else (["c0"] if i == 3 else [])}
               for i in range(39)])
    print(f"    Steinhardt 形状 非空 4/39、3 种 → {r['counter_source_ids'][0]}")
    chk("非空 4/39 且 3 种取值 → 不判（第一版报「几乎是表头」，错）",
        r["counter_source_ids"][0] == "用得太少不判")
    # Pasteur #106：非空 3 / 33，3 种取值——**三条各不相同**
    r = audit([{"counter_source_ids": [f"p{i}"] if i < 3 else []} for i in range(33)])
    chk("非空 3/33 且三条各不相同 → 不判（第一版报「几乎是表头」，错）",
        r["counter_source_ids"][0] == "用得太少不判")

    print("── ★★ 反向对照 ⑧：**广泛填充**才判表头（分母是非空数，不是记录数）──")
    r = audit([{"source_ids": ["a"]} for _ in range(35)])
    chk("非空 35/35、1 种 → 表头（这一侧必须仍然报）", r["source_ids"][0] == "表头")

    print("── ★ 反向对照 ④：**顺序不同不算差异** ──")
    r = audit(claims([["a", "b"], ["b", "a"]] * 20))
    chk("[a,b] 与 [b,a] 视为同一组 → 表头", r["source_ids"][0] == "表头")

    print("── 反向对照 ⑤：几乎是表头（2 种 / 46 条，Koch 的 clusters）──")
    r = audit([{"evidence_clusters": ["A"] if i < 27 else ["A", "B"]}
               for i in range(46)])
    chk("2 种取值 / 46 条 → **几乎是表头**（与「表头」分开报）",
        r["evidence_clusters"][0] == "几乎是表头")

    print("── ★★ 反向对照 ⑥：**空值不计入不同取值数** ──")
    r = audit([{"source_ids": ["a"]} if i % 2 else {"source_ids": []}
               for i in range(40)])
    print(f"    20 条有值（都一样）+ 20 条空 → {r['source_ids']}")
    chk("非空数 20、不同取值 1 → 表头（空的不许充当「第二种取值」）",
        r["source_ids"][0] == "表头" and r["source_ids"][2] == 20
        and r["source_ids"][3] == 1)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claims", type=pathlib.Path, help="evidence/claims.jsonl")
    ap.add_argument("--min-records", type=int, default=MIN_RECORDS)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.claims:
        ap.error("要么 --self-test，要么给 --claims")
    if not a.claims.is_file():
        print(f"✗ **{a.claims} 不在——本次未检查（不是通过）**")
        return 3

    claims = [json.loads(l) for l in a.claims.read_text(encoding="utf-8").splitlines()
              if l.strip()]
    if not claims:
        print("✗ **断言文件是空的——本次未检查（不是通过）**")
        return 3

    res = audit(claims, min_records=a.min_records)
    print(f"断言 **{len(claims)}** 条\n")
    bad = []
    for f, (state, n, nonempty, distinct) in res.items():
        mark = {"表头": "✗", "几乎是表头": "！", "整批都空": "·",
                "逐条各异": "✓", "记录太少不判": "·"}[state]
        print(f"  {mark} {f:22} {state:<8} 非空 {nonempty}/{n}　不同取值 **{distinct}**")
        if state in ("表头", "几乎是表头"):
            bad.append((f, state, distinct, n))

    # ★★ 零扫描面不许印肯定句：`bad` 为空既可能是「都合格」，也可能是
    #   「一个字段都没有实数据」。实测喂无关文档 → 照印 ✓、rc=0。
    #   ★ 我第一版判在 `not res` 上 —— **错了**：`res` 按固定字段名建，永远有 3 项，
    #     所以那个条件永不成立。真正的空信号在**每个字段的 state**：
    #     全是「整批都空／记录太少不判」就等于什么也没查。
    #     [[zero-hit-gates-must-prove-they-can-hit]]｜[[gate-green-but-pointed-at-wrong-artifact]]
    judged = [f for f, (state, *_ ) in res.items()
              if state not in ("整批都空", "记录太少不判")]
    if not judged:
        print("\n  ⚠ **没有一个证据字段有可判的数据（全是「整批都空／记录太少不判」）"
              "—— 本次未核，不是通过。**")
        return 0
    if not bad:
        print("\n  ✓ 有数据可判的 **%d** 个证据字段都不是「填一次抄 N 遍」" % len(judged))
        return 0

    print("\n✗ **下列字段是表头，不是逐条证据**：")
    for f, state, distinct, n in bad:
        print(f"    {f}：{n} 条断言只有 **{distinct}** 种取值")
    print("\n  **它说的不是「这些断言是编的」，只说这个字段不再有信息量**——\n"
          "  读它的判据于是在核一个常量（`check_claim_anchors` 会全绿）。\n"
          "  同型第二例：v0.0.0.24 一句 `attribution_basis` 让整批免检，逐源检查十版没跑过。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
