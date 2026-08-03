#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绝对化／不在场断言体检 —— 产物文档专用（RUNBOOK 第十六种的第二个工具）。

## 为什么单独做一个

评委只看 evals，**产物文档没有评委**。Jesse Vincent #94 里同一个 star 错误有三个落点，
其中两个在产物文档（`boundaries.md`、`references/research/04-external.md`），
分别在第一轮和第二轮才被翻出来——而 `case-boundary-1` 第一轮就被评委抓到了。

## 它查什么

「完全没有」「从未」「无任何」「只有」这类断言**本身不是错**，
错的是**下断言时没有说明检索方式**。本脚本把它们全部列出来，
由人逐条确认：**这一条的依据在哪，检索范围是什么。**

**不做自动判定**——判定不在场需要看语料，脚本看不了。它只保证「一条都不漏看」。
"""
import argparse, pathlib, re, sys

# **只匹配关键词本身，上下文另取。**
# 第一版写成 `[^。\n]{0,60}(关键词)[^。\n]{0,60}`，两侧贪婪，
# 于是「他**从未**这样说过，也**毫无**记录，而且**一次也没**提起」——
# **三条断言被吞成一条**（finditer 不重叠）。自测抓出来的。
PAT = re.compile(r"完全没有|从未|从没|从来没|毫无|一次也没|无任何|没有任何|"
                 r"绝无|全部都是|一律是|只有|唯一|均未|皆无")
# 依据词：同句/邻近出现即视为已给检索方式
GROUND = re.compile(r"(全文检索|逐条查|命中\s*0|0\s*次|份来源|份书面|检索过|逐字|原话|原文|"
                    r"其本人|一手|有日期|可逐字核)")


def scan_text(text: str, context: int = 160) -> list:
    """→ [(是否带依据, 断言所在的那一句)]。**不做自动判定**，只保证一条都不漏看。

    每命中一个绝对化词就是一条——**同一句里有几个就报几条**。
    """
    rows = []
    for m in PAT.finditer(text):
        # 展示用：取所在句（到最近的句号／换行为止），不参与判定
        lo = max((text.rfind(ch, 0, m.start()) for ch in "。\n"), default=-1) + 1
        hi = min((p for p in (text.find(ch, m.end()) for ch in "。\n") if p >= 0),
                 default=len(text))
        sent = re.sub(r"\s+", " ", text[lo:hi + 1]).strip()
        ctx = text[max(0, m.start() - context):m.end() + context]
        rows.append((bool(GROUND.search(ctx)), sent))
    return rows


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：光秃秃的不在场断言 ──")
    # Jesse Vincent #94 的形状：同一个绝对化说法有三个落点，两个在产物文档里
    bare = "他**从未**在任何公开场合谈论过这件事。"
    out = scan_text(bare)
    chk("「从未…」且邻近无检索依据 → 标 ⚠", len(out) == 1 and out[0][0] is False)

    print("── 反向对照 ①：带了检索方式的不许标 ⚠ ──")
    grounded = ("对全部 61 份来源做过**全文检索**，"
                "他**从未**在任何公开场合谈论过这件事——命中 0 次。")
    out = scan_text(grounded)
    chk("同句给了「全文检索」与「命中 0」→ 标 ✓", len(out) == 1 and out[0][0] is True)

    print("── 反向对照 ②：依据在窗口之外就不算数 ──")
    far = "对全部 61 份来源做过全文检索。" + "。" * 400 + "他**从未**谈论过这件事。"
    out = scan_text(far, context=160)
    chk("依据隔了 400 字 → 仍标 ⚠（窗口是有射程的，不许无限远认亲）",
        any(ok is False for ok, _ in out))

    print("── 反向对照 ③：没有绝对化词的句子不许报 ──")
    chk("普通陈述句 → 一条不报",
        scan_text("他在 1929 年那篇论文里报告了这一观察，并注明了培养条件。") == [])

    print("── 反向对照 ④：**「只有」「唯一」也是绝对化断言**，不许漏 ──")
    # 这两个词最像普通措辞，却同样是不在场断言（「只有 X」＝「除 X 之外都没有」）
    for w, s in (("只有", "**只有**这一份扫本保留了那一行。"),
                 ("唯一", "这是**唯一**能证实那件事的材料。")):
        chk(f"「{w}」→ 报出", len(scan_text(s)) == 1)

    print("── 反向对照 ⑤：一段里多条绝对化断言，一条都不许合并掉 ──")
    multi = "他**从未**这样说过，也**毫无**这方面的记录，而且**一次也没**在信里提起。"
    chk(f"三条分开报（实报 {len(scan_text(multi))} 条）", len(scan_text(multi)) == 3)

    print("── 反向对照 ⑥：空文本不许报「全部带依据」，也不许崩 ──")
    chk("空串 → 返回空，由调用方决定怎么说", scan_text("") == [])

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--context", type=int, default=160, help="判定依据的邻近窗口")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    files = sorted(a.workspace.rglob("*.md"))
    if not files:
        print(f"✗ **{a.workspace} 下一份 .md 都没读到——结果不可信，不是「没问题」**")
        return 3

    n_all = n_bare = 0
    for f in files:
        rows = scan_text(f.read_text(encoding="utf-8", errors="replace"), a.context)
        n_all += len(rows)
        n_bare += sum(1 for ok, _ in rows if not ok)
        if rows:
            print(f"\n── {f.relative_to(a.workspace)}")
            for ok, s in rows:
                print(f"   {'✓' if ok else '⚠'} {s[:110]}")

    print(f"\n扫过 {len(files)} 份 .md；合计 {n_all} 条绝对化断言，"
          f"其中 {n_bare} 条邻近未见检索依据")
    print("⚠ 标记的须人工确认依据；本脚本不做自动判定" if n_bare else "✓ 全部带依据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
