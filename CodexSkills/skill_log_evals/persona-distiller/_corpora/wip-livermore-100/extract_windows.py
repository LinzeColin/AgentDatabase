#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从整版报纸 OCR 里截出**与本人物相关的那一段**，再入库。

## 为什么必须截

抓回来的 149 份是 **Chronicling America 的整版 ALTO OCR**，
单份 30 万–190 万字节，而其中关于 Livermore 的通常只有一两段。
整版直接入库有三个后果，**每一个都会让下游的门失效**：

1. **来源数被口径撑大**：一版报纸算「一份来源」，与一本 2.2 万词的专著等量齐观。
   `min_sources` 于是量的是「提到过他的版面数」，不是「关于他的材料量」。
2. **内容层检查全部失准**：`check_claim_coverage` 会在整版报纸里找实体——
   同版面的船期表、讣告、广告里什么词都有，**装饰性引用必然查不出来**。
3. **holdout 重叠判据失效**：整版之间共享大量报头、栏目名、通讯社套语，
   重叠率被这些噪声顶起来，真正的转载反而淹了。

## 截法

对每个 `Livermore` 出现处取前后各 `--window` 字符，重叠的窗口合并。
**不做任何改写**——截出来的每个字符都与原文逐字相同，
只是丢掉了同版面的无关内容。窗口边界与命中数一并写进产出文件的头部注释，
**可复核**。

## 一条必须留在这里的注意

`Livermore` 也是**地名与他人姓氏**（如 Mary Livermore、Livermore 加州）。
本脚本只负责截取，**不负责判断这一段说的是不是他**——
那是入库后 `check_authorship` 与人工判读的事。
截出来的窗口里若混进了同名者，会在后续步骤被逐条读到。
"""
import argparse
import pathlib
import re
import sys

NAME = re.compile(r"Livermore", re.I)


def windows(text: str, size: int):
    spans = []
    for m in NAME.finditer(text):
        a, b = max(0, m.start() - size), min(len(text), m.end() + size)
        if spans and a <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], b))
        else:
            spans.append((a, b))
    return spans


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("indir", type=pathlib.Path)
    ap.add_argument("--outdir", type=pathlib.Path, required=True)
    ap.add_argument("--window", type=int, default=1500)
    ap.add_argument("--skip", nargs="*", default=["HowToTradeInStocks"],
                    help="文件名含这些字样的不截（专著自带完整语境）")
    a = ap.parse_args()
    a.outdir.mkdir(parents=True, exist_ok=True)

    kept = dropped = 0
    total_before = total_after = 0
    for src in sorted(a.indir.glob("*.txt")):
        if any(s in src.name for s in a.skip):
            continue
        text = src.read_text(encoding="utf-8", errors="replace")
        total_before += len(text)
        spans = windows(text, a.window)
        if not spans:
            dropped += 1
            print(f"· 丢弃（整版里没有 Livermore）：{src.name}")
            continue
        chunks = [text[s:e] for s, e in spans]
        header = (f"[extract] source={src.name} hits={len(spans)} "
                  f"window=±{a.window} orig_bytes={len(text)}\n"
                  f"[extract] 逐字截取，未做任何改写；窗口以 'Livermore' 为中心合并\n\n")
        body = header + "\n\n[…版面其余内容已略…]\n\n".join(chunks)
        (a.outdir / src.name).write_text(body, encoding="utf-8")
        total_after += len(body)
        kept += 1
    print(f"\n保留 {kept} 份，丢弃 {dropped} 份")
    if total_before:
        print(f"字节 {total_before:,} → {total_after:,}"
              f"（{total_after / total_before:.1%}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
