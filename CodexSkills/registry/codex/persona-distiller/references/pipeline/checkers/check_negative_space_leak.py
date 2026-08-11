#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**按体裁／题材描述「我手边缺什么」，等于把 holdout 的题目说出来。**

## 为什么有这件

`check_holdout_mention` 的文件头明写它抓不到这一类：

> 抓不到「不提 holdout 也不抄它、却把题目描述出来」的写法——
> 那一类只能靠人读或答题方主动上报。

2026-08-11 Grotius #168 一天内**撞了两次**，两次都是候选侧子代理的
`__incident__` 报上来的，**三道现有的门全绿且都没报错**：

1. `hypotheses.md` 与 `01-writings.md` 写着
   「（本工作区／本道）分到的十二份里**没有一份是护教／神学体裁**」——
   而该人物的 holdout 正是一部护教之作。
2. **修完之后我加的那段「为什么改」的注解**里写着
   「本人物的 holdout 恰好就是一部护教之作」——
   **比原来那句更直接**：原句要读者自己去连，这句直接给了答案。

★★ 第 2 条与 Whitworth #152 的事故一**完全同型**
（那次记的是「同一天第三次『堵漏的那段话本身成了新的漏』」）。
**记录读过，照样又犯**——所以要落成判据，不能只写教训。

## 判据形状：**规则，不是阈值**

**答题方读得到的文件里，不许按体裁／题材描述缺口。**

答题方读得到的是：工作区根目录的产物 `*.md` 与 `references/research/*.md`。
（`evals/` 与 `references/holdout/` 答题方读不到，**不在射程内**。）

两类命中：

- **A 类·按体裁描述缺口**：`没有一份是X` / `一份也没有X` / `都不是X体裁` /
  `手边没有X类` —— X 是体裁、题材、类别。
- **B 类·直接提 holdout 并说它是什么**：`holdout` 与 `密封`／`留出`
  同段出现，且同段还有体裁／题材词。

## ★ 它不管什么（先说清楚，免得被当成万能门）

1. **不判「缺口描述得对不对」**，只判「有没有按体裁描述缺口」。
2. **不认识 holdout 的题材**——本件不读 holdout，所以**不能说「这一句泄的正是那道题」**，
   只能说「这一句把缺口的体裁说出来了，而缺口的另一侧就是 holdout」。
3. **质量类的边界话不算**：`我手边的本子字迹已坏` / `我拿不准` / `复述不准`
   —— 那是说**读不读得清**，不是说**缺哪一类**。这一条在自测里反向验过。

用法：

    python3 check_negative_space_leak.py <工作区>
    python3 check_negative_space_leak.py --self-test

退出码：0=没有按体裁描述缺口　1=有　2=自测未过　3=没有可扫的文件（未检查，不是通过）
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# 体裁／题材词——**按类别说话**的标志
GENRE = (r"体裁|文体|类(?:的|型)?书|护教|神学|论战|自传|书信|讲稿|专著|论文|"
         r"日记|回忆录|传记|译本|手稿|通信|札记|诗|史|апологет")

# A 类：按体裁描述缺口
NEG = re.compile(
    r"(?:没有一[份篇部本]|一[份篇部本]也(?:没有|不是)|都不是|无一[份篇部本]|"
    r"手边没有|这里没有|找不到一[份篇部本]|缺(?:少)?(?:任何)?)"
    r"[^\n。；]{0,24}(?:%s)" % GENRE)

# A 类的另一种语序：「X 体裁的一份也没有」
NEG2 = re.compile(r"(?:%s)[^\n。；]{0,16}(?:一[份篇部本]也没有|都没有|一个也没有)" % GENRE)

# B 类：同段提 holdout 且说它是什么
HOLD = re.compile(r"holdout|留出集|密封(?:材料|集|的)|保留集")

# ★ 质量类边界话——**不算**。它说的是读不读得清，不是缺哪一类。
QUALITY = re.compile(
    r"字迹|读不出|拿不准|复述不准|OCR|讹字|模糊|残缺|扫描"
    # ★ 2026-08-11 收紧：**说「证据够不够」不等于说「缺哪一类材料」。**
    #   实测误报一处：`凡产物中出现「他在书信里写道……」形态的句子，都没有可核依据`
    #   ——它说的是**引文可不可核**，不是「手边没有书信」。
    #   `书信` 在体裁表里，`都没有` 命中否定式，两者一撞就误报。
    r"|可核依据|凭据|证据|逐字|出处|复核|回查")


def visible_files(ws: pathlib.Path) -> list:
    """答题方**读得到**的文件。`evals/` 与 `references/holdout/` 不在内。"""
    out = sorted(ws.glob("*.md"))
    rs = ws / "references" / "research"
    if rs.is_dir():
        out += sorted(rs.glob("*.md"))
    return out


def scan_text(text: str):
    """产出 (行号, 类别, 行文)。**按行判，不跨行**——跨行会把两句无关的话连起来。"""
    for i, line in enumerate(text.splitlines(), 1):
        if QUALITY.search(line):
            continue                      # 质量类边界话，放行
        if NEG.search(line) or NEG2.search(line):
            yield i, "A·按体裁描述缺口", line.strip()[:110]
        elif HOLD.search(line) and re.search(GENRE, line):
            yield i, "B·点了 holdout 又说它是什么", line.strip()[:110]


def self_test() -> int:
    n = [0]
    fail = 0

    def note(label, ok):
        n[0] += 1
        print(f"  {'✓' if ok else '✗'} {label}")

    print("══ 负对照：两次真事故的原句必须被抓到 ══")
    real1 = "本工作区分到的十二份里**没有一份是护教／神学体裁**，无从旁证。"
    ok1 = any(k.startswith("A") for _, k, _ in scan_text(real1))
    note("事故一原句（`没有一份是护教／神学体裁`）", ok1)
    fail += not ok1

    real2 = "那是一句按体裁描述缺口的话，而本人物的 holdout 恰好就是一部护教之作——"
    ok2 = bool(list(scan_text(real2)))
    note("事故二原句（注解里点了 holdout 又说它是护教之作）", ok2)
    fail += not ok2

    ok3 = any(k.startswith("A") for _, k, _ in
              scan_text("而本道分到的 12 份里没有一份是护教／神学体裁——"))
    note("事故一的研究道版本", ok3)
    fail += not ok3

    ok3b = any(k.startswith("A") for _, k, _ in
               scan_text("论战之作以外的体裁一份也没有。"))
    note("另一种语序（`X 体裁一份也没有`）", ok3b)
    fail += not ok3b

    print("\n══ 反对照：这些**不许**被抓 ══")
    # ① 质量类边界话是产物的正当内容，误报会让作者学会忽略这道门
    for s in ["我手边那些本子的字迹已坏，逐字引文多数复述不准。",
              "那部书的字迹坏得最厉害，卷内的叙事我不敢逐句担保。",
              "只有 1869 年那一版的字是清楚的，要逐字引就从那一版引。"]:
        ok = not list(scan_text(s))
        note(f"质量类边界话不算：「{s[:22]}…」", ok)
        fail += not ok

    # ② 不提体裁的缺口描述不算——本件只管「按体裁说」
    ok5 = not list(scan_text("这一条我手边没有旁证。"))
    note("**反对照**：不提体裁的缺口描述 → 不报", ok5)
    fail += not ok5

    # ③ 提了 holdout 但没说它是什么 → 不报（那是 check_holdout_mention 的活）
    ok6 = not list(scan_text("holdout 的正文不许研究方读。"))
    note("**反对照**：只提 holdout、不说它是什么 → 不报（那是另一件的射程）", ok6)
    fail += not ok6

    # ④ 正常谈体裁而不谈缺口 → 不报
    # ⑥ ★ 实测误报：说「证据够不够」不是说「缺哪一类材料」
    ok5b = not list(scan_text(
        "凡产物中出现「他在书信里写道……」形态的句子，**都没有可核依据**。"))
    note("**反对照**：说「引文没有可核依据」→ 不报（不是在说缺书信这一类）", ok5b)
    fail += not ok5b

    ok7 = not list(scan_text("《尼德兰史》是史书，按年编卷，一卷一年。"))
    note("**反对照**：正常谈体裁而不说缺什么 → 不报", ok7)
    fail += not ok7

    # ⑤ ★ 跨行不许连：两行各自无辜，合起来像命中
    two = "本道分到 12 份。\n其中最要紧的是护教传统里的那条线索。"
    ok8 = not list(scan_text(two))
    note("**反对照**：两行各自无辜 → 不许跨行连成命中", ok8)
    fail += not ok8

    print(f"\n  ✓ 自测通过（{n[0]}/{n[0]}）" if not fail
          else f"\n  ✗ {fail}/{n[0]} 项未过——本件的结论不作数")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", nargs="?", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return 2 if self_test() else 0
    if not a.workspace:
        ap.error("须给工作区（除非只跑 --self-test）")

    files = visible_files(a.workspace)
    if not files:
        print("✗ **答题方读得到的 md 一份都没有——未检查（不是通过）**")
        return 3

    hits = []
    for f in files:
        for ln, kind, line in scan_text(f.read_text(encoding="utf-8", errors="replace")):
            hits.append((f.name, ln, kind, line))

    print(f"扫了 {len(files)} 份**答题方读得到的**文件"
          f"（工作区根 `*.md` + `references/research/*.md`；"
          f"`evals/` 与 `references/holdout/` 不在射程内）")
    if not hits:
        print("  ✓ 没有按体裁／题材描述缺口的写法")
        print("  ★ 但**这不等于没泄题**：换个说法绕过本件的形状，它就看不见。"
              "答题方的 `__incident__` 上报**仍是这条通道上最后一道防线**。")
        return 0

    print(f"  ✗ **{len(hits)} 处按体裁／题材描述了缺口**——"
          f"缺口的另一侧就是 holdout，说出缺什么等于说出它是什么：")
    for fn, ln, kind, line in hits[:20]:
        print(f"     {fn}:{ln}  [{kind}]  {line}")
    if len(hits) > 20:
        print(f"     …另有 {len(hits) - 20} 处")
    print("\n  改法：**说不知道就直说「这个我说不出」**，不要说「我手边没有 X 类的」。"
          "\n  ★ 改动理由**不要写在这些文件里**——写在 `evals/` 下，答题方读不到那儿。"
          "\n    （2026-08-11 实测：我把改动理由写进研究道，那段注解本身成了更大的漏。）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
