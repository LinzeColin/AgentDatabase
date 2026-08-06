#!/usr/bin/env python3
"""**同一行里的三个数要能对上**——`X / Y　摆动 Z` 里 Z 必须等于 X − Y。

## 撞出它的那一次（2026-08-06，周报）

我在周报里写：

    Thomson #129  +0.4084 / −0.0859   摆动 **0.6038**

**+0.4084 −(−0.0859) = 0.4944。** 0.6038 是**第 1 轮**的摆动，
而 +0.4084 / −0.0859 是**第 3 轮**的两个数。

★★★ 这个错的形状值得单说：**六个 delta 单独看全部复算一致**——
是那一行把**两个真数配成了一个假组合**。
逐个核数核不出它；只有把同一行里的数**放在一起算**才看得见。

★ 而人物自己的记录是对的（`FINAL-三轮用尽记拒发.md` 三行摆动逐个列着）。
**错只出在手写的汇总表里**——汇总表是这类错的高发地，因为它把
不同轮次、不同口径的数抄到同一行上。

## 判法

在 Markdown 里找形如

    <数> / <数>  ...  摆动 <数>
    <数> ／ <数>  ...  摆动 <数>

的行，检查第三个数是否等于前两个之差（容差 5e-4）。

- **只报不拦**：正当的写法也存在（例如三轮摆动并列 `0.6038 / 0.4878 / 0.4944`），
  本件对**三个以上数的行**一律跳过——那是列表不是等式。
- **不认没有「摆动」二字的行**：`a / b` 在本项目里也用来写「候选/基线」，
  没有第三个数就没有可核的算术。

## ★★★★ 射程为什么停在「摆动」这一个词上（有实测，不是保守）

2026-08-06 试着把同一思路推到另外三种形态，在 **1477 份**台账与产物上扫：

    候选 X / 基线 Y → Z      命中  2　对不上 **0**
    X / Y → Z（箭头式）       命中  2　对不上 **2**   ← 全是假阳
    n / m = R（占比）         命中 21　对不上 **11**  ← 全是假阳

**真错 0 处；13 处「对不上」全是我的模式错了。** 逐条读命中才看出来：

- `533/536 = 99.4` 是**百分数**（99.44%），我按分数算成 0.9944；
  `51/62 = 82.3`、`1/69 = 1.4` 同理。
- `0.94/0.95→0.95`、`0.915 / 0.900 → 0.915` 是「**两席 → 聚合**」，
  那个箭头是**汇总，不是相减**。

★ 结论：**`/` 与 `=` 在本项目里是重载的**——同一个符号写占比、写两席并列、写前后变化。
只有「**摆动**」这个词有唯一的意思（两个 delta 之差），因此只有它可机械核算。
**扩到别的形态会把 11 行本来就对的台账判成错**——
[[read-the-hits-before-reporting-the-rate]] 的又一次：**先读命中，再报率。**
"""
from __future__ import annotations
import argparse, pathlib, re, sys

# `+0.4084 / −0.0859` 或 `+0.4084 ／ −0.0859`；数字允许 ASCII 与全角负号
_NUM = r"[+\-−]?\d+\.\d+"
# ★★ 第一版用「后面不许再有第三个 `/ 数`」的负向前瞻做护栏，**挡不住四数行**——
#   `+0.1 / +0.2 / +0.3 / +0.4  摆动 0.5` 会从**最后一对**开始匹配，前瞻自然成立。
#   改成：先切出「摆动」之前那一段，**要求整段里恰好两个数**。
_SWING = re.compile(r"^(.*?)摆动\s*\**\s*(" + _NUM + r")", re.M)
_ALLNUM = re.compile(_NUM)
_PAIR = re.compile(rf"({_NUM})\s*[/／]\s*({_NUM})")
# ★★★ 引述并否认不算。**抓到这条的是判据自己**：修完周报那一行后重跑，
#   它仍报 1 处——命中的正是我写的更正说明「初稿写成「…摆动 0.6038」——」。
#   与 check_persona_frame_break 的 `_NEG` 是同一条道理：
#   **一段被否认的原文，不是一个还活着的断言。**
#   ★ 只看命中之前的 30 字，射程与那边一致。
_RETRACT = re.compile(r"(初稿|原文写|原表|已作废|改过|更正|曾写|误|错的是|写错)")


def _f(s: str) -> float:
    return float(s.replace("−", "-").replace("＋", "+"))


def scan_text(text: str, tol: float = 5e-4):
    """→ [(行号, 左, 右, 声称的摆动, 应为)]，只返回对不上的。

    ★★ `tol` 默认 5e-4 不是随手定的：两个输入各自按四位小数显示，
      各可差 5e-5，**它们的差因此可差 1e-4**。
      实测：显示的 `+0.4084 −(−0.0859) = 0.4943`，而从未舍入的原始分算是 **0.4944**。
      **容差必须容得下这一档，否则会把「显示舍入」误报成「配错了数」。**
    """
    bad = []
    for m in _SWING.finditer(text):
        head, z = m.group(1), _f(m.group(2))
        nums = _ALLNUM.findall(head)
        if len(nums) != 2:          # ★ 不是「两个数 + 摆动」的等式行，一律跳过
            continue
        pm = _PAIR.search(head)
        if not pm:                  # 两个数之间没有 `/`，不是本件管的形态
            continue
        if _RETRACT.search(head[-30:]) or _RETRACT.search(
                text[max(0, m.start() - 30):m.start()]):
            continue                # ★ 引述并否认的原文，不是活着的断言
        a, b = _f(pm.group(1)), _f(pm.group(2))
        want = a - b
        if abs(want - z) > tol:
            line = text[:m.start()].count("\n") + 1
            bad.append((line, a, b, z, want))
    return bad


def self_test() -> int:
    fails = []

    def chk(msg, cond):
        print(f"  {'✓' if cond else '✗'} {msg}")
        if not cond:
            fails.append(msg)

    # ★ 撞出它的原句
    t1 = "    Thomson #129  +0.4084 / −0.0859   摆动 **0.6038**\n"
    got = scan_text(t1)
    chk("★ **撞出它的原句**：+0.4084 / −0.0859 摆动 0.6038 → 报错",
        len(got) == 1 and abs(got[0][4] - 0.4943) < 1e-6)
    # ★★ 这条断言我第一版写成 0.4944，**错的**——
    #   0.4944 是从**未舍入的原始分**算出来的，而本件只看得见显示的四位小数：
    #   `+0.4084 −(−0.0859) = 0.4943`。两者差 1e-4，正是舍入。
    #   **判据能核的是「显示的数自洽吗」，不是「真值是多少」。**
    chk("★★ 显示舍入造成的 1e-4 差不报（+0.4084 / −0.0859 摆动 0.4944）",
        not scan_text("  +0.4084 / −0.0859  摆动 0.4944\n"))

    # 正例：对得上的不许报
    chk("对得上的不报（+0.4516 / −0.1522 摆动 0.6038）",
        not scan_text("  +0.4516 / −0.1522   摆动 **0.6038**\n"))
    chk("对得上的不报（Carver +0.3791 / −0.2019 摆动 0.5810）",
        not scan_text("  Carver #127   +0.3791 / −0.2019   摆动 **0.5810**\n"))

    # ★★ 三个以上数的行是列表不是等式，一律跳过
    chk("★★ 三轮摆动并列 `0.6038 / 0.4878 / 0.4944` **不报**",
        not scan_text("  Thomson 三轮摆动 **0.6038 / 0.4878 / 0.4944**\n"))
    chk("★★ 四数列表也不报",
        not scan_text("  +0.1 / +0.2 / +0.3 / +0.4  摆动 0.5\n"))

    # ★ 没有「摆动」二字的不认
    chk("★★★ **引述并否认不报**：初稿写成「+0.4084 / −0.0859 摆动 0.6038」",
        not scan_text("★ 这一行改过：初稿写成「+0.4084 / −0.0859　摆动 0.6038」——配错了。\n"))
    chk("★★★ 而**没有否认词**时仍要报",
        len(scan_text("  某某 #129  +0.4084 / −0.0859   摆动 0.6038\n")) == 1)
    chk("★ 没有「摆动」的 `候选 0.8474 / 基线 0.8456` **不报**",
        not scan_text("  候选 0.8474 / 基线 0.8456 → +0.0018\n"))

    # 全角负号与 ASCII 负号都要认
    chk("全角负号认得（−）", len(scan_text("  +0.40 / −0.09  摆动 0.60\n")) == 1)
    chk("ASCII 负号认得（-）", len(scan_text("  +0.40 / -0.09  摆动 0.60\n")) == 1)

    # ★★★ 容差：0.0004 之内算对，0.0006 报错
    chk("★★★ 容差内不报（差 0.0004）", not scan_text("  +0.5000 / +0.1000  摆动 0.4004\n"))
    chk("★★★ 容差外要报（差 0.0006）", len(scan_text("  +0.5000 / +0.1000  摆动 0.4006\n")) == 1)

    print("\n" + ("✓ 自测全过" if not fails else "✗ 自测未过"))
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="同一行里的三个数要能对上：`X / Y 摆动 Z` 须 Z = X − Y")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.paths:
        print("✗ 需要文件或目录（或只给 --self-test）")
        return 2
    files = []
    for p in a.paths:
        q = pathlib.Path(p)
        files += sorted(q.rglob("*.md")) if q.is_dir() else [q]
    n_bad = 0
    for f in files:
        try:
            bad = scan_text(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for line, x, y, z, want in bad:
            n_bad += 1
            print(f"  ✗ {f}:{line}　写着摆动 {z:+.4f}，而 {x:+.4f} − {y:+.4f} = **{want:+.4f}**")
    print(f"\n扫了 {len(files)} 份，**对不上的 {n_bad} 处**"
          + ("　★ 只报不拦——请回原始分复算，别照着改数" if n_bad else ""))
    return 0


# ★★★★ 这三行是补上去的。第一版**漏了整个入口块**——
#   `python3 check_delta_arithmetic.py --self-test` 什么都不打印，**而退出码是 0**。
#   「没输出 + exit 0」看起来与「通过」一模一样。
#   这是 [[a-checker-nothing-calls-is-not-a-checker]] 最纯粹的形态：
#   **判据不是没人调，是它自己根本不会被执行。**
#   ★ 抓到它的是「跑一遍看输出」，不是看退出码——[[pipe-to-tail-hides-the-exit-code]] 同族。
if __name__ == "__main__":
    sys.exit(main())
