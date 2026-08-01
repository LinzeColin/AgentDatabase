#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐条核验断言里的英文引文是否**逐字**出现在语料中。

## 为什么本人物必须单独跑这一步

那本书是 OCR 扫描件。抄写时**把 `cach` 顺手写成 `each`、`prcvious onc` 写成
`previous one` 是最省力的动作**，而那样写出来的「原话」在语料里根本不存在——
读者拿去原书里搜一个字也搜不到。

本轮实测：第一版 30 条断言里有 **13 个片段**是这样被我无声修好的。
**是这个脚本抓出来的，不是我自己想起来的。**

## 判据

比对用「骨架」：同形字还原 + 断字合并 + **只保留字母数字**。
标点与空白一律忽略——OCR 在这两类上噪声最大，且它们不承载归属。
含 `…` 的引文按片段分别核。
"""
import json, re, sys, pathlib
sys.path.insert(0, "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller/scripts")
from check_ocr_homoglyphs import HOMOGLYPHS

def skel(t):
    t = "".join(HOMOGLYPHS.get(ch, ch) for ch in t)
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
    return re.sub(r"[^a-z0-9]", "", t.lower())

def main():
    claims, corpus_dirs = pathlib.Path(sys.argv[1]), [pathlib.Path(p) for p in sys.argv[2:]]
    corpus = {}
    for d in corpus_dirs:
        for f in (d.rglob("*.txt") if d.is_dir() else [d]):
            corpus[f.name] = skel(f.read_text(encoding="utf-8", errors="replace"))
    QUOTE = re.compile(r"「([^」]{12,400})」")
    bad, ok = [], 0
    for line in claims.read_text(encoding="utf-8").splitlines():
        c = json.loads(line)
        for q in QUOTE.findall(c["claim"]):
            if not re.search(r"[A-Za-z]{3}", q) or re.search(r"[一-鿿]", q):
                continue
            frags = [f for f in re.split(r"…|\.\.\.", q) if len(re.sub(r"[^A-Za-z]", "", f)) >= 12]
            miss = [fr for fr in frags if not any(skel(fr) in v for v in corpus.values())]
            if miss:
                bad += [(c["claim_id"], m.strip()[:80]) for m in miss]
            else:
                ok += 1
    print(f"英文引文：整条命中 {ok}｜未命中片段 {len(bad)}")
    for cid, q in bad:
        print(f"  ✗ {cid}: {q!r}")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
