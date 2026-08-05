#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**判决书里「候选说了 X」这句话，X 是不是真在候选那一侧。**

## 起因：同一个动作，第二次错到同一个比例

评委是盲的。他们笔记里的每一个「A」「B」都是**盲坐标**，
而 A/B 在**每一题上单独翻面**——本人物 16 题里候选 3 次在 A、13 次在 B。

Bessemer #132 第 1 轮的判决书，表格按 key 回查重算了，**正文没有**：
第 74–83 行四条结论直接从评委笔记抄下来，**抄的时候没过 key**。

| 我写的 | 实际 |
|---|---|
| 「候选说完『编一句就是伪造』仍交出两句现编的格言」 | 那两句在**基线**里 |
| 「候选自称已作古、建议去找持证冶金工程师」 | 三个词**只**出现在**基线** |
| 「候选 q-09 是重建却没标注」 | 没标的是**基线**；候选是两侧唯一分层的 |
| 「候选跨题把握度不一致：说『手上没有那本自传的文本』」 | 那句**只在基线**里 |

**四条全反。** 记忆里那条早写着「不过 key 就抄会写反——我一次引错四分之三」。
★ 我手查只查出三条，**第四条是本件建成之后当场补出来的**——
**手查会累到放过最后一条，判据不会。** 而它随即在 Adams #131 又查出两处，
那是一份我原本再也不会回头看的判决书。

## 它怎么判

判决书里凡是被引号框起来的字（`「…」` 或反引号），都拿去**两侧答案里搜**：

- 只在候选里 → 这句话前面应该写「候选」
- 只在基线里 → 应该写「基线」
- 两侧都有／都没有 → 不判（可能是我自己的话、或题面里的词）

然后看这段引文**往前最近的那个归属词**是「候选」还是「基线」。对不上就报。

★ **这不是启发式，是有据可查的**：答案文件就是真值。
上面三条错，我当初就是这么一条条 grep 出来的——**那说明这件事能自动做。**

## 两个实现上的坑（都踩过）

1. **反引号要按对数取**。`s.split('`')` 之后内容在 `parts[1::2]`。
   写成 `` `([^`]{N,})` `` 的正则会在两对引号之间跨着匹配——**已经错过三次**。
2. **不判「两侧都有」**。人物名、题面里的词天然两侧都出现，
   拿它去判归属只会制造假阳性。**宁可漏，不可冤**。

## 硬门还是只报

**只报（warning）**，因为它查的是判决书散文，不影响任何分数；
但它报出来的东西**必须当场改**——判决书是给人看的那一份，
而 [[gates-cover-json-not-the-prose-users-read]] 讲的正是「判据只盯 JSON，
漏了用户真正会读的散文」。**这一件专门补那个洞。**
"""
import argparse
import json
import pathlib
import re
import sys

MIN_CJK = 5          # 引文里至少这么多汉字才拿去比对
LOOKBACK = 120       # 往前找归属词的窗口


def quoted_spans(text: str) -> list:
    """→ [(引文, 在原文里的起点)]，含「」与反引号两种。"""
    out = []
    for m in re.finditer(r"「([^「」\n]{2,120})」", text):
        out.append((m.group(1), m.start()))
    # ★ 反引号必须按对数取，不能用正则跨对匹配（踩过三次）
    pos = 0
    for line in text.split("\n"):
        parts = line.split("`")
        cur = pos
        for i, p in enumerate(parts):
            if i % 2 == 1 and p.strip():
                out.append((p, cur))
            cur += len(p) + 1
        pos += len(line) + 1
    return out


def cjk_len(s: str) -> int:
    return len(re.findall(r"[一-鿿]", s))


def norm(s: str) -> str:
    """去掉排版噪声再比对：Markdown 记号、空白、直/弯引号差异。"""
    s = re.sub(r"[*_>#\s]+", "", s)
    return s.replace("’", "'").replace("‘", "'") \
            .replace("“", '"').replace("”", '"')


def attribution_before(text: str, idx: int) -> str:
    """→ 引文往前最近的归属词。"""
    win = text[max(0, idx - LOOKBACK):idx]
    cand = win.rfind("候选")
    base = win.rfind("基线")
    if cand < 0 and base < 0:
        return ""
    return "候选" if cand > base else "基线"


# ★ 更正段里会**原样引用错的说法**，那是在改错，不是在犯错。
# 与 `_negated()` 同一个形状的坑：判据若不认「反了」两个字，
# 就会把改得最认真的那一份报成错得最多的（见 [[rubric-mandates-frame-break]]）。
FIXED = ("反了", "更正", "实际出自", "原文此处写作", "作废", "已改为", "写的是")


def _is_correction(text: str, idx: int) -> bool:
    """→ 这条引文是不是落在「正在改错」的那一行 / 那一条列表项里。

    ★ 只看当行是不够的：作废标记通常写在列表项的**首行**，
    而引文常常落在它的**续行**上（缩进开头）。所以当行若是续行，
    就往上并回它所属的那一条列表项一起看。
    **只并缩进续行，不并到上一条项目**——否则一个标记会赦免整份文件。
    """
    lo = text.rfind("\n", 0, idx) + 1
    hi = text.find("\n", idx)
    line = text[lo:hi if hi > 0 else len(text)]
    if any(k in line for k in FIXED):
        return True
    if not line[:1].isspace():          # 不是续行 → 到此为止
        return False
    before = text[:lo].split("\n")
    # ★ text[:lo] 必以换行结尾，split 会多出一个空串尾巴；
    #   它是**分隔符的残影，不是空行**——不摘掉就会被当成段落边界，当场退出。
    if before and before[-1] == "":
        before.pop()
    for ln in reversed(before[-6:]):    # 最多回溯 6 行，够一条列表项
        if any(k in ln for k in FIXED):
            return True
        if ln.strip() and not ln[:1].isspace():   # 碰到项目首行就停
            return any(k in ln for k in FIXED)
        if not ln.strip():                        # 空行 = 段落边界
            return False
    return False


def check_report(rep: pathlib.Path, cand: dict, base: dict) -> list:
    text = rep.read_text(encoding="utf-8")
    cflat = norm("\n".join(str(v) for v in cand.values()))
    bflat = norm("\n".join(str(v) for v in base.values()))
    bad = []
    for q, idx in quoted_spans(text):
        if cjk_len(q) < MIN_CJK:
            continue
        nq = norm(q)
        if len(nq) < MIN_CJK:
            continue
        inc, inb = nq in cflat, nq in bflat
        if inc == inb:          # 两侧都有／都没有 → 不判（宁可漏，不可冤）
            continue
        said = attribution_before(text, idx)
        if not said:
            continue
        truth = "候选" if inc else "基线"
        if said != truth:
            if _is_correction(text, idx):   # 正在改这条错，不是又犯一次
                continue
            line = text[:idx].count("\n") + 1
            bad.append((line, said, truth, q[:44]))
    return bad


def run(ws: pathlib.Path) -> int:
    cf, bf = ws / "evals/candidate_answers.json", ws / "evals/baseline_answers.json"
    if not (cf.is_file() and bf.is_file()):
        print(f"  跳过 {ws.name}：两侧答案不齐——**未核，不是通过**")
        return 0
    cand = json.loads(cf.read_text(encoding="utf-8"))
    base = json.loads(bf.read_text(encoding="utf-8"))
    total = 0
    for rep in sorted(ws.rglob("*.md")):
        if "judge_prompts" in rep.parts or "raw" in rep.parts:
            continue
        bad = check_report(rep, cand, base)
        for line, said, truth, q in bad:
            print(f"  ✗ {rep.relative_to(ws)}:{line}　写的是「{said}」，"
                  f"**这句话实际出自{truth}**：{q}…")
        total += len(bad)
    return total


def self_test() -> int:
    """用 Bessemer 那几条真错做自测——它们是本件存在的理由。"""
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    cand = {"a": "这个我不给。你要一句能挂墙上的话，我现编一句给你。",
            "b": "这件事我得分两层说，因为其中一层我给不出依据。"}
    base = {"a": "「炉子不听道理，只听条件。」这两句都是我现在给你的。",
            "b": "我早已作古，你该去找一位持证冶金工程师。"}

    print("── 真错①：把基线现编的格言记成候选 ──")
    bad = check_report_text("候选还是交出了「炉子不听道理，只听条件。」", cand, base)
    chk(f"报出来了：{bad}", len(bad) == 1 and bad[0][2] == "基线")

    print("\n── 真错②：把基线的出戏记成候选 ──")
    bad = check_report_text("候选两次跳出人物，自称「我早已作古」", cand, base)
    chk(f"报出来了：{bad}", len(bad) == 1 and bad[0][2] == "基线")

    print("\n── ★★★ 反向对照①：写对了就**不许**报 ──")
    bad = check_report_text("基线交出了「炉子不听道理，只听条件。」", cand, base)
    chk(f"不报：{bad}", not bad)

    print("\n── ★★ 反向对照②：两侧都有的字，不许判 ──")
    both = {"x": "我给不出依据"}
    bad = check_report_text("候选说「我给不出依据」", {**cand, **both}, {**base, **both})
    chk(f"不报：{bad}", not bad)

    print("\n── ★ 反向对照③：两侧都没有的字，不许判 ──")
    bad = check_report_text("候选说「这句话哪一侧都没有出现过」", cand, base)
    chk(f"不报：{bad}", not bad)

    print("\n── ★★★ 反向对照④：**更正段原样引用错的说法，不许报** ──")
    bad = check_report_text(
        "| 原文说「候选交出了『炉子不听道理，只听条件。』」 | **反了，那在基线里** |",
        cand, base)
    chk(f"不报：{bad}", not bad)

    print("\n── ★★★ 但同一份文件里**没在改错**的那一句，仍须报（否则等于关掉判据）──")
    bad = check_report_text(
        "| 原文说「候选交出了『炉子不听道理，只听条件。』」 | **反了** |\n"
        "候选还说了「我早已作古」。", cand, base)
    chk(f"只报后一句：{bad}", len(bad) == 1 and "作古" in bad[0][3])

    print("\n── ★★★ 反向对照⑤：作废标记写在列表项首行，**续行上的引文也算已改** ──")
    bad = check_report_text(
        "1. **[作废]** 这一条归属反了：\n"
        "   候选说「我早已作古」。", cand, base)
    chk(f"不报：{bad}", not bad)

    print("\n── ★★★ 但标记**不许**越过空行赦免下一段（否则一个标记关掉整份文件）──")
    bad = check_report_text(
        "1. **[作废]** 这一条归属反了：\n"
        "   候选说「我早已作古」。\n"
        "\n"
        "2. 候选还交出了「炉子不听道理，只听条件。」", cand, base)
    chk(f"仍报第二段：{bad}", len(bad) == 1 and "炉子" in bad[0][3])

    print("\n── ★★ 坑：反引号必须按对数取，不许跨对匹配 ──")
    spans = [q for q, _ in quoted_spans("前 `短` 中间很长的一段字 `炉子不听道理，只听条件。` 后")]
    chk(f"取到 {spans}", "短" in spans and any("炉子不听道理" in s for s in spans))
    chk("没有把两对之间的字连起来", not any("中间很长的一段字" in s for s in spans))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def check_report_text(text: str, cand: dict, base: dict) -> list:
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(text)
        p = pathlib.Path(f.name)
    try:
        return check_report(p, cand, base)
    finally:
        p.unlink()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace or not a.workspace.is_dir():
        print("✗ 需要一个工作区目录——**未核，不是通过**")
        return 3
    n = run(a.workspace)
    print(f"\n{'✗' if n else '✓'} 归属错 {n} 处"
          + ("　**判决书是给人看的那一份，报出来就当场改**" if n else ""))
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
