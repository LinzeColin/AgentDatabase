#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""德文扫本取句工具 —— 去连字符换行之后再匹配。

十九世纪德文排印每行都断词，OCR 原样保留：

    …dass sich aus irgend einer unzelligen Substanz eine neue Zelle auf-
    bauen könne. Wo eine Zelle entsteht…

不做这一步，任何跨行的短语都搜不到——**我因此一度以为抓源代理报告失实**
（搜「Die Medicin ist eine sociale Wissenschaft」全量 0 处，实为短语中间有换行）。

## 两条纪律

1. **`join()` 只用于「找」，不用于「引」。**
   逐字引文必须回原文取**原样**（含连字符与换行），
   否则就是「自己动手改了原文再当逐字引文用」——Jenner #104 立的规矩。
2. `span()` 返回原样片段与它在原文里的偏移，**引用时用它，不用 join 后的串**。
"""
import pathlib
import re

RAW = pathlib.Path("raw")


def load(sub: str) -> tuple[str, pathlib.Path]:
    fs = list(RAW.glob(f"{sub}/*.txt"))
    if not fs:
        raise SystemExit(f"语料不在：{sub}")
    return fs[0].read_text(encoding="utf-8", errors="replace"), fs[0]


def join(t: str) -> str:
    """去连字符换行 + 折行 → 单行。**只用于查找。**"""
    t = re.sub(r"[-¬]\s*\n\s*", "", t)      # 断词连字符
    t = re.sub(r"\s*\n\s*", " ", t)          # 其余换行
    return re.sub(r"\s{2,}", " ", t)


def find(sub: str, pat: str, n: int = 3, ctx: int = 0):
    """在去连字符后的文本里找，返回 (命中串, 原文原样片段)。"""
    t, path = load(sub)
    j = join(t)
    out = []
    for m in list(re.finditer(pat, j, re.I))[:n]:
        s = max(0, m.start() - ctx)
        hit = j[s:m.end() + ctx]
        # 回原文定位：用命中串的前 24 个非空字符去原文里找
        key = re.sub(r"\s+", "", m.group(0))[:24]
        raw_span = ""
        acc, idx = [], []
        for i, ch in enumerate(t):
            if not ch.isspace() and ch not in "-¬":
                acc.append(ch)
                idx.append(i)
        k = "".join(acc).find(key)
        if k >= 0:
            end = min(len(idx) - 1, k + len(re.sub(r"[\s\-¬]", "", m.group(0))) - 1)
            raw_span = t[idx[k]: idx[end] + 1]
        out.append((hit.strip(), raw_span))
    return out, path.name


if __name__ == "__main__":
    import sys
    sub, pat = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    hits, fn = find(sub, pat, n)
    print(f"[{fn}] {len(hits)} 处")
    for h, raw in hits:
        print(f"\n  去连字符后：«{h[:230]}»")
        print(f"  **原文原样**：{raw[:230]!r}")
