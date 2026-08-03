#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim 标记锚点体检：文段与它标注的断言，谈的是不是同一件事。

## 为什么官方门看不见这个

官方门查两件事：**每条断言都被渲染了吗**、**有没有孤儿标记**。
两条都是**计数**层面的——而 claim 标记错挂**不改变任何计数**。

Jesse Vincent #94 实测：三个标记发生了**循环错位**（A 段标了 B 的号、
B 段标了 C 的号、C 段标了 A 的号）。数量对得上、无孤儿、每条断言都被渲染，
**三个门全绿**。后果是读者顺着标记去查证据，会落到另一条断言上——
**引用链断了，而且断得看不出来。**

## 判据

取标记**两侧**各约 450 字作为「被标注的文段」，与断言正文求关键词重合
（英文实体 ≥5 字符、中文**滑动** 4-gram）。重合 < 2 即报出。

**v0.0.0.49 两处订正，都是补负对照时查出来的：**
① 第一版只看标记**之前**的 450 字，而本项目渲染器把标记写在文段**前面**——
   **它一直在看错边。** Osler #110 真工作区实测：44 个标记报出 41 个，几乎全是误报。
② 中文原本取 `[一-鿿]{4,8}` 极大连续块，转述与断言的分块方式差一个字就全对不上，
   **中文侧几乎恒报**。改滑动 4-gram。
**这个脚本此前没有 `--self-test`，所以这两个错一直没人发现。**

## 已知误报：中文文段 + 英文引文断言

断言正文常常主体是英文引文，而渲染文段是中文转述，**字面重合天然为 0**。
Vincent 那轮 4 处命中里有 1 处是这种情况
（中文「五个月内发生过一次实质推翻」↔ 英文「Over the past 5 months」）。

**所以只列不判。** 它的价值不在于自动判错，在于**把 33 个标记压缩成 3–4 个要看的**。
"""
import argparse, json, pathlib, re, sys

EN = re.compile(r"[A-Za-z][A-Za-z0-9./\-]{4,}")
CN_RUN = re.compile(r"[一-鿿]{4,}")
NGRAM = 4
WIN = 450
MIN_OVERLAP = 2


def keys(s: str) -> set:
    """英文实体（≥5 字符）+ 中文**滑动** 4-gram。

    第一版中文取的是 `[一-鿿]{4,8}` 这种**极大连续块**——
    转述与断言正文的分块方式只要差一个字，两边就一个都对不上。
    实测：文段「他 1928 年在培养皿上看到青霉菌抑制了葡萄球菌」
    与断言「1928 年他在培养皿上观察到青霉菌抑制葡萄球菌生长」**重合 0**，
    而它们说的分明是同一件事。**中文侧几乎恒报，等于这一路没在工作。**
    自测抓出来的，改用滑动窗口。
    """
    out = {k.lower() for k in EN.findall(s)}
    for run in CN_RUN.findall(s):
        for i in range(len(run) - NGRAM + 1):
            out.add(run[i:i + NGRAM])
    return out


MARK = re.compile(r"<!-- claim:(clm-[0-9a-f]+) -->")


def scan_doc(text: str, claims: dict, name: str = "?") -> tuple:
    """→ (标记总数, [(文件, claim_id, 原因, 断言摘要)])。"""
    total, flagged = 0, []
    for m in MARK.finditer(text):
        total += 1
        cid = m.group(1)
        if cid not in claims:
            flagged.append((name, cid, "断言不存在", ""))
            continue
        # **两侧都看。** 第一版只看标记**之前**的 450 字——
        # 而本项目的渲染器 `render_*_claims.py` 把标记写在文段**前面**：
        #     <!-- claim:clm-xxx -->
        #     **断言正文……**
        # 于是判据一直在看错边。Osler #110 真工作区实测：**44 个标记报出 41 个**，
        # 几乎全是误报。**它从来没有负对照，所以这个错一直没人发现。**
        seg = text[max(0, m.start() - WIN):m.end() + WIN]
        ov = keys(seg) & keys(claims[cid])
        if len(ov) < MIN_OVERLAP:
            flagged.append((name, cid, f"重合 {len(ov)}", claims[cid][:70]))
    return total, flagged


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    CLAIMS = {
        "clm-aaa1": "1928 年他在培养皿上观察到青霉菌抑制葡萄球菌生长，1929 年发表于 "
                    "British Journal of Experimental Pathology。",
        "clm-bbb2": "1922 年他报告了溶菌酶 lysozyme，见 Proceedings of the Royal Society B。",
        "clm-ccc3": "1945 年诺贝尔奖由 Fleming、Florey、Chain 三人共享。",
    }

    # 夹具形状照真文档来：**标记紧跟在它标注的那一句后面**，段与段之间隔着补白。
    # 第一版每段才 35 字，三段全落进同一个 450 字窗口——正向控制只报出 2/3；
    # 把补白垫在标记之前又会把主题句挤出窗口，正确挂号的也全被报出。
    # **两条控制互相顶住，说明夹具的形状不对，不是判据不对。**
    PAD = "\n\n" + "这一段与上下文无关，用来把两处标记隔开到判据窗口之外。" * 18 + "\n\n"
    SEG = [
        ("他 1928 年在培养皿上看到青霉菌抑制了葡萄球菌，1929 年发表论文。", "clm-aaa1"),
        ("1922 年他报告了溶菌酶 lysozyme，见 Proceedings of the Royal Society B。", "clm-bbb2"),
        ("1945 年诺贝尔奖由 Fleming、Florey、Chain 三人共享。", "clm-ccc3"),
    ]
    chk(f"隔离补白够宽（{len(PAD)} 字 > 窗口 {WIN}）", len(PAD) > WIN)

    print("── 正向：Jesse Vincent #94 的真实形态（三个标记循环错位）──")
    # A 段标了 B 的号、B 段标了 C 的号、C 段标了 A 的号。
    # 数量对得上、无孤儿、每条断言都被渲染，**三个官方门全绿**——因为它们只数数。
    rot = PAD.join(f"{s}<!-- claim:{SEG[(i + 1) % 3][1]} -->" for i, (s, _) in enumerate(SEG))
    total, flagged = scan_doc(rot, CLAIMS, "rot.md")
    chk(f"三个标记全部错位 → 三条都报出（实报 {len(flagged)}/3）",
        total == 3 and len(flagged) == 3)

    print("── 反向对照 ①：标记挂对了就不许报 ──")
    right = PAD.join(f"{s}<!-- claim:{cid} -->" for s, cid in SEG)
    total, flagged = scan_doc(right, CLAIMS, "right.md")
    chk(f"三个标记都挂对 → 一条不报（实报 {len(flagged)}）",
        total == 3 and not flagged)

    print("── 反向对照 ②：**标记写在文段前面**（本项目渲染器的真实约定）──")
    # `render_*_claims.py` 输出的是：
    #     <!-- claim:clm-xxx -->
    #     **断言正文……**
    # 第一版只看标记**之前**的 450 字，于是一直在看错边。
    # Osler #110 真工作区实测：**44 个标记报出 41 个**，几乎全是误报。
    before = PAD.join(f"<!-- claim:{cid} -->\n{s}" for s, cid in SEG)
    total, flagged = scan_doc(before, CLAIMS, "before.md")
    chk(f"标记在前、文段在后且挂对 → 一条不报（实报 {len(flagged)}）",
        total == 3 and not flagged)
    before_rot = PAD.join(f"<!-- claim:{SEG[(i + 1) % 3][1]} -->\n{s}"
                          for i, (s, _) in enumerate(SEG))
    total, flagged = scan_doc(before_rot, CLAIMS, "before_rot.md")
    chk(f"标记在前但错位 → 三条都报出（实报 {len(flagged)}/3）", len(flagged) == 3)

    print("── 反向对照 ③：孤儿标记（断言不存在）要报，且理由要写清 ──")
    total, flagged = scan_doc("随便一段文字。<!-- claim:clm-dead9 -->", CLAIMS, "x.md")
    chk("指向不存在的断言 → 报「断言不存在」",
        len(flagged) == 1 and flagged[0][2] == "断言不存在")

    print("── 反向对照 ④：**窗口是有射程的**，450 字之外的文段不算 ──")
    far = ("他 1928 年在培养皿上看到青霉菌抑制了葡萄球菌，1929 年发表论文。"
           + "另起一段与此无关的叙述。" * 60
           + "<!-- claim:clm-aaa1 -->")
    total, flagged = scan_doc(far, CLAIMS, "far.md")
    chk("对得上的文段被 600+ 字隔开 → 仍报出（不许无限远认亲）", len(flagged) == 1)

    print("── 反向对照 ⑤：已知误报——中文文段配英文引文断言，天然重合为 0 ──")
    # 这是文档里写明的射程。**它必须仍然被报出来**，因为脚本判不了，只能交给人。
    EN_CLAIM = {"clm-eee5": "Over the past 5 months the project has not been overturned once."}
    cn = "过去五个月里这个项目发生过一次实质推翻。<!-- claim:clm-eee5 -->"
    total, flagged = scan_doc(cn, EN_CLAIM, "cn.md")
    chk("中文文段 + 英文断言 → 报出（这是已知误报，脚本判不了，交给人）",
        len(flagged) == 1)

    print("── 反向对照 ⑥：没有标记的文档不许报「全部对上」 ──")
    total, flagged = scan_doc("一段没有任何 claim 标记的正文。", CLAIMS, "none.md")
    chk("标记数 0、报出数 0 → 由调用方区分「全对」与「没扫到」",
        total == 0 and not flagged)

    print("── 反向对照 ⑦：重合刚好等于门槛时不许报（边界值）──")
    chk(f"MIN_OVERLAP = {MIN_OVERLAP}，判的是 `< {MIN_OVERLAP}`，等于不报",
        MIN_OVERLAP == 2)
    seg = "1922 年他报告了那种酶。"
    ov = len(keys(seg) & keys(CLAIMS["clm-bbb2"]))
    chk(f"夹具重合数确为 {MIN_OVERLAP}（实测 {ov}）——**边界夹具必须真在边界上**",
        ov == MIN_OVERLAP)
    total, flagged = scan_doc(seg + "<!-- claim:clm-bbb2 -->", CLAIMS, "edge.md")
    chk("恰好重合 2 个 → 不报", not flagged)
    seg1 = "溶菌酶是 1922 年报告的。"
    ov1 = len(keys(seg1) & keys(CLAIMS["clm-bbb2"]))
    chk(f"重合 {ov1} < {MIN_OVERLAP} → 报出（下边界也要验）",
        ov1 < MIN_OVERLAP
        and len(scan_doc(seg1 + "<!-- claim:clm-bbb2 -->", CLAIMS, "e2.md")[1]) == 1)

    print("── 反向对照 ⑧：**中文改用滑动 n-gram 之后，不许归得过宽** ──")
    # 归一化放宽的风险是错位的标记也能撞上 2 个 n-gram。三条错位的实测重合必须是 0。
    for cid, seg in (("clm-bbb2", "他 1928 年在培养皿上看到青霉菌抑制了葡萄球菌。"),
                     ("clm-ccc3", "1922 年他报告了溶菌酶，那是完全属于他自己的工作。"),
                     ("clm-aaa1", "1945 年的诺贝尔奖不是他一个人的，是三个人共享。")):
        n = len(keys(seg) & keys(CLAIMS[cid]))
        chk(f"错位 {cid} 实测重合 {n} < {MIN_OVERLAP}", n < MIN_OVERLAP)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    cl = a.workspace / "evidence" / "claims.jsonl"
    if not cl.is_file():
        print(f"✗ **{cl} 不在——结果不可信，不是「没问题」**")
        return 3
    claims = {}
    for line in cl.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            claims[r["claim_id"]] = r["claim"]
    if not claims:
        print(f"✗ **{cl} 里一条断言都没有——结果不可信**")
        return 3

    total, flagged = 0, []
    for f in sorted(a.workspace.rglob("*.md")):
        n, rows = scan_doc(f.read_text(encoding="utf-8", errors="replace"),
                           claims, f.name)
        total += n
        flagged += rows

    print(f"断言 {len(claims)} 条；claim 标记 {total} 个，须人工看 {len(flagged)} 个")
    for fn, cid, why, txt in flagged:
        print(f"  ⚠ {fn} {cid}（{why}）\n      {txt}")
    if not total:
        print("\n✗ **一个 claim 标记都没扫到——这不是「全部对上」**")
        return 3
    print("\n✓ 全部对上" if not flagged
          else "\n⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认")
    return 0


if __name__ == "__main__":
    sys.exit(main())
