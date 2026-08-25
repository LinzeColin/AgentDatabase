#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**摆出一串分项加一个合计，加得平吗。**

## 为什么有这道判据

Nightingale #112 第 1 轮，**两席各自独立**在同一处扣分。席 E：

> 以「懂，下面是数」立论，1871 年每千次分娩列意外 .3、产褥病 1.4、其他 .7，
> 自报总数 5-1；相加 2.4，差出一倍有余……
> **这是全卷唯一能交叉验算的地方，恰好没通过。**

席 D 更进一步，算出了配平所需的值。

**而语料把它定死了。** 紧挨着的十三年表是：

    Accidents of childbirth . . 3-22 per 1,000
    Puei-peral diseases . . . . 1-61
    Total, exclusive of other deaths . . 4'83

`3.22 + 1.61 = 4.83`——**`-` 与 `'` 都是小数点**。
于是 1867 那组里的 `,3` 是 **3**，不是 0.3：**3 + 1.4 + 0.7 = 5.1 ✓**。

**我照录了 OCR 却没验算。** 逐字照录是对的，
但**照录不等于读懂**——扫本把小数点认成逗号、引号、连字符，
一串数就会看起来像另一串数。

这是第六次把席位批评落成判据。

## 判据

在**同一段**里，若出现「若干分项 + 一个标着合计的数」，就把分项加起来对一对。

- 合计的标记：`Total` / `合计` / `总计` / `共` / `总` 。
- 容差：**0.05 或 1%，取大者**——四舍五入与末位进位是常态。

## ★ 它判不了什么

- **不判那串数抄得对不对**。抄错但抄得「自洽」的照样过。
- **不判语料里原本就加不平的表**。十九世纪的表确实有印错的；
  真遇上了，正确的写法是**照录并写明「原表分项与合计不符」**——
  那种段落里带着「不符」「对不上」这类字样，本判据放行（反向对照 ⑤）。
- **分项里若有「其中」「含」这类嵌套项**，加起来本就会超，故一律跳过（反向对照 ④）。
- **散文里的数列一概不判**，只判**分项行与合计行各占一行**的表格块。
  实跑证明散文分支只会造噪声：`男 12.3%、女 14%；男女合计 21.8%` 里的「合计」
  是**合并后的率**不是相加；一段话里的 `1859`、`1871` 会被当成分项（反向对照 ⑨）。
"""
import argparse
import json
import pathlib
import re
import sys

NUM = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})*|\d+)(?:[.’'‐-]\d{1,2})?(?![\d])")
# `总` 单字也算——但要跟着一个数或反引号，免得把「总是」「总体」也算进来
TOTAL = re.compile(r"Total|合计|总计|总共|共计|总数|总(?=\s*[`\d])")
# 段里明说「对不上」的，是**照录一张原本就错的表**，放行
DISCLOSED = re.compile(r"不符|对不上|加不平|不自洽|原表(?:有)?误|印错|与合计不符")
# 嵌套分项：加起来本就会超
NESTED = re.compile(r"其中|内含|含[^，。；]{0,8}项|including|of which")


def _val(s: str):
    """把扫本里的小数点还原：`3-22` / `4'83` / `1-4` → 3.22 / 4.83 / 1.4。

    ★ **首位的坏字符也要当小数点读，不许丢。**
      `"7` 若返回 None 就被静默丢出数列，合计跟着变——
      **丢掉比读错更坏**：读错会被判据报出来，丢掉不会。
      按字面读成 0.7；它到底是 0.7 还是 7，**要人回原文定**，
      判据只负责指出这一串加不平。
    """
    s = s.strip()
    m = re.fullmatch(r"[.,’'\"‐-](\d{1,2})", s)         # 首位是坏掉的小数点
    if m:
        return float("0." + m.group(1))
    s = s.replace(",", "")
    m = re.fullmatch(r"(\d+)[.’'‐-](\d{1,2})", s)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    try:
        return float(s)
    except ValueError:
        return None


def lines(text: str):
    for para in re.split(r"\n\s*\n", text or ""):
        if para.strip():
            yield para


def check_para(para: str):
    """→ (分项, 合计, 是否对得上) 或 None。"""
    if not TOTAL.search(para) or DISCLOSED.search(para) or NESTED.search(para):
        return None
    rows = [ln for ln in para.split("\n") if ln.strip()]
    total, parts = None, []
    for ln in rows:
        # ★ **只收「数在行尾」的行**——表格行把数放末尾，散文行不会。
        #   自测当场抓出：表头 `13 年表：` 里的 `13` 被当成了一个分项，
        #   于是 13+3.22+1.61≠4.83，一张**语料里真实且加得平**的表被报成错。
        ms = [m for m in NUM.finditer(ln) if _val(m.group(0)) is not None]
        if not ms:
            continue
        last = ms[-1]
        if len(ln.rstrip()) - last.end() > 12:
            continue                     # 数不在行尾 → 是散文，不是表格行
        # **表格行的数前面必有标签**；`13 年表：` 这种数在行首的是表头，不是分项。
        if not re.sub(r"[\s`*>|—-]", "", ln[:last.start()]):
            continue
        vals = [_val(last.group(0))]
        if TOTAL.search(ln):
            total = vals[-1] if total is None else total
        else:
            parts.append(vals[-1])
    # ★★ **只判多行表格块，散文里的数列一概不判。**
    #
    #   第一版有个「一行摆完」的兜底分支，实跑当场造出两条假阳性：
    #   · `男 12.3%、女 14%；另一处男女**合计** 21.8%` —— 「合计」在这里是
    #     **男女合并后的率**，不是两个率相加。判据把它当成 12.3+14=26.3≠21.8。
    #   · 一段散文里同时提到 1859 年那张表与 1871 年那组数，
    #     兜底分支把 `1859`、`1871` 这些**年份**也算成了分项，凑出 3783.99。
    #
    #   **我把表格行的规则用到了散文上。** 散文里的数列不可靠识别，
    #   而噪声正是这一系列判据反复栽的地方（v0.0.0.62 / v0.0.0.65 各一次）。
    #   缩到判得动的范围：**分项行与合计行各占一行，至少两个分项。**
    if total is None or len(parts) < 2:
        # ★★ 单行形态：**只吃反引号包住的数**，且相邻两数之间的间隔要短。
        #
        #   缩成「只判表格块」之后，判据**抓不到自己的动因用例**——
        #   我那条原答案是单行的：`意外 \`,3\`、产褥病 \`1-4\`、其他 \`"7\`、总 \`5-1\``。
        #   「报绿在动因用例上」这一条在本会话里已经犯到第三次。
        #
        #   两个限制把噪声挡在外面（各由一条实跑出的假阳性作对照）：
        #   · **必须在反引号里**——判据管的是「从源里抄来的数」。
        #     `男 12.3%、女 14%；男女合计 21.8%` 是散文里的率，不进射程。
        #   · **相邻两数间隔 ≤14 字**——同一串数才会挨得这么近。
        #     一段话里 1859 年那表与 1871 年那组之间隔着二十多字，不算一串。
        ms = [m for m in re.finditer(r"`([^`]{1,12})`", para)
              if _val(m.group(1)) is not None]
        if len(ms) < 3:
            return None
        for x, y in zip(ms, ms[1:]):
            if y.start() - x.end() > 14:
                return None
        tail = para[ms[-1].start() - 14:ms[-1].start()]
        if not TOTAL.search(tail) and not re.search(r"总|合计", tail):
            return None
        parts = [_val(m.group(1)) for m in ms[:-1]]
        total = _val(ms[-1].group(1))
    s = sum(parts)
    tol = max(0.05, abs(total) * 0.01)
    return parts, total, abs(s - total) <= tol


def scan(unit_id: str, text: str, acc):
    for para in lines(text):
        r = check_para(para)
        if r is None:
            continue
        parts, total, ok = r
        acc["total"] += 1
        if ok:
            acc["ok"] += 1
        else:
            acc["bad"].append((unit_id, parts, total, sum(parts), para.strip()[:120]))


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    def run(t):
        acc = {"total": 0, "ok": 0, "bad": []}
        scan("x", t, acc)
        return acc

    print("── ★ 正向：Nightingale #112 q-11 的真实形状（两席各自独立抓到）──")
    a = run("1867 年英格兰每千次分娩：\n意外 `,3`\n产褥病 `1-4`\n其他热病 `\"7`\nTotal `5-1`")
    chk("0.3+1.4+0.7 ≠ 5.1 → 报出", len(a["bad"]) == 1)

    print("── ★ 反向对照 ①：**把 OCR 还原成人读得懂的数，就该放行** ──")
    # 判据分辨不了 `,3` 到底是 3 还是 0.3、`"7` 是 7 还是 0.7——**那要人回原文读**。
    # 它能做的是指出「这串加不平」。作者读完原文改成还原值，判据即放行。
    b = run("1867 年英格兰每千次分娩（扫本把小数点认坏，此处按同书十三年表的体例还原）：\n"
            "意外 3\n产褥病 1.4\n其他热病 0.7\nTotal 5.1")
    chk("3+1.4+0.7 = 5.1 → 不报", b["total"] == 1 and not b["bad"])

    print("── 反向对照 ②：**扫本的 `-` `'` 都是小数点**，要还原 ──")
    chk("`3-22` → 3.22", _val("3-22") == 3.22)
    chk("`4'83` → 4.83", _val("4'83") == 4.83)
    chk("`1-4` → 1.4", _val("1-4") == 1.4)
    c = run("十三年表：\n意外 `3-22`\n产褥病 `1-61`\nTotal, exclusive of other deaths `4'83`")
    chk("3.22+1.61 = 4.83 → 不报（这是语料里真实的一张表）",
        c["total"] == 1 and not c["bad"])

    print("── 反向对照 ③：没有合计标记的一律不判 ──")
    d = run("我做过 1920、1924、1927 三年的三项工作。")
    chk("无 `Total`／`合计` → 不计入", d["total"] == 0 and not d["bad"])

    print("── ★ 反向对照 ④：**嵌套分项加起来本就会超**，跳过 ──")
    e = run("死亡 3933 例，**其中**血中毒相关 1203 例。Total 3933。")
    chk("段里有「其中」→ 跳过", e["total"] == 0)

    print("── ★★ 反向对照 ⑤：**照录一张原本就错的表，并写明了，要放行** ──")
    # 十九世纪的表确实有印错的。正确的写法是照录 + 写明「原表分项与合计不符」，
    # 判据若还报它，作者会去**改原表的数**——那是伪造。
    f = run("原表如此（**分项与合计不符，照录**）：\n甲 `1`\n乙 `1`\nTotal `9`")
    chk("段里写明「不符」→ 放行", f["total"] == 0 and not f["bad"])

    print("── 反向对照 ⑥：容差取 0.05 或 1% 的大者（末位进位是常态）──")
    g = run("甲 `3.33`\n乙 `3.33`\n乙二 `3.33`\nTotal `10.0`")
    chk("9.99 vs 10.0 → 放行", not g["bad"])
    h = run("甲 `10`\n乙 `10`\nTotal `30`")
    chk("20 vs 30 → 报出", len(h["bad"]) == 1)

    print("── ★ 反向对照 ⑧：**表头里的数不许当分项**（自测当场抓出的接线错）──")
    j = run("13 年表：\n意外 `3-22`\n产褥病 `1-61`\nTotal `4'83`")
    chk("表头 `13 年表：` 的 13 不计入 → 仍放行", j["total"] == 1 and not j["bad"])
    k = run("我 1867 年做了三件事，合计 Total 5。")
    chk("整段是散文、数不在行尾 → 不计入", k["total"] == 0)

    print("── ★★ 正向 ②：**单行形态也要抓到**（判据自己的动因用例就是单行的）──")
    n1 = run("1871 年：1867 年英格兰每千次分娩，意外 `,3`、产褥病 `1-4`、其他 `\"7`、总 `5-1`。")
    chk("单行、数全在反引号里、末位标「总」→ 报出", len(n1["bad"]) == 1)
    n2 = run("1871 年：意外 `3`、产褥病 `1.4`、其他 `0.7`、总 `5.1`。")
    chk("还原成对的数 → 不报", n2["total"] == 1 and not n2["bad"])

    print("── ★★ 反向对照 ⑨：**散文里的数列一概不判**（实跑造出的两条假阳性）──")
    m1 = run("**加拿大各医院的死亡率我也列了**：男 12.3%、女 14%；另一处男女合计 21.8%。")
    chk("「男女合计」是合并后的率不是相加 → 不判", m1["total"] == 0)
    m2 = run("1859 年那张表对照伦敦女性人口（`15.89 15.80 17.80 4'5.36`）；"
             "1871 年产褥期按成因分列，每千次分娩 `Total . . . . . 5-1`。")
    chk("一段散文里两组不相干的数 → 不判", m2["total"] == 0)

    print("── 反向对照 ⑦：一段里没有数 → 不计入，且不构成通过 ──")
    i = run("Total 是多少我没核过。")
    chk("无可加的数 → total=0", i["total"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[])
    ap.add_argument("--claims", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.answers or a.claims):
        ap.error("--answers 或 --claims 至少给一个（除非只跑 --self-test）")

    acc = {"total": 0, "ok": 0, "bad": []}
    if a.claims and a.claims.is_file():
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                scan(f"断言/{r.get('claim_id', '?')}", r.get("claim", ""), acc)
    for p in a.answers:
        if not p.is_file():
            # ★ **给了路径却不在，是「没查成」，不是「没问题」。**
            #   长度门失败会删掉候选文件，而本判据此前对着不存在的文件
            #   打印「可验算的数列 0 处」——看起来像扫过了。
            print(f"✗ **{p} 不在——本次未检查（不是通过）**")
            return 3
        data = json.loads(p.read_text(encoding="utf-8"))
        units = ([(f'{r.get("case_id", "?")}/{s}', r[s]) for r in data
                  for s in ("A", "B") if s in r]
                 if isinstance(data, list) else list(data.items()))
        for uid, text in units:
            if isinstance(text, str):
                scan(f"答案/{uid}", text, acc)

    print(f"可验算的数列 {acc['total']} 处，加得平 {acc['ok']} 处，**加不平 {len(acc['bad'])} 处**")
    if not acc["total"]:
        print("  ⚠ **一处可验算的数列都没扫到——本次未检查（不是通过）**")
        return 0
    if acc["bad"]:
        print("\n✗ **分项加起来对不上自报的合计**——"
              "逐字照录是对的，但**照录不等于读懂**："
              "扫本会把小数点认成逗号、引号、连字符：")
        for uid, parts, total, s, snip in acc["bad"]:
            print(f"    {uid}　分项 {parts} 合 {s:g}，自报合计 {total:g}\n        {snip}")
        print("\n  **两条出路**：回原文重读那几个字符（多半是小数点被认坏了），"
              "或者照录并写明「原表分项与合计不符」——后者本判据放行。")
        return 1
    print("  ✓ 每一处都加得平")
    return 0


if __name__ == "__main__":
    sys.exit(main())
