#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引文真实性核验 —— 把断言里的每一句英文原文拿去语料里逐字找。

## 这个脚本第一版是错的，错法值得写下来（RUNBOOK ⑮ 的第四个实例）

第一版直接拿 `「...」` 里的整段去匹配，报出 8 条「未命中」。全是误报，三个原因：

1. **撇号**：`I'm prone to...` 被我的字符类从 `m` 截断，拿 `m prone to...` 去找当然找不到。
2. **省略号是我自己的省略标记**：`「A… B」` 里的 A 与 B 在原文中**并不相邻**，
   当成一整句去找必然落空。**必须按 `…`／`...` 切开，分段各自核。**
3. **引文里嵌了 markdown 粗体**：`「...**My intuition for what's easy**...」`，
   `**` 是我加的强调，不在原文里。

**8 条全是我的工具坏了，不是引文假。** 差一步就报出「产物里有 8 条伪造引文」——
**误报的检查比没有检查更糟**，因为它会触发一轮根本不需要的订正，
而那轮订正很可能把真引文改坏。

## 现在的做法

- 按 `…` / `...` 切段，每段单独核，短于 12 字符的段跳过（太短匹配无意义）
- 剥掉 markdown `**` `*` `_`
- 撇号／引号统一（`'` `'` `'` → `'`，`"` `"` → `"`）
- 词间用 `\\s*` 连接（语料是 HTML 转文本，词间常有多余空格——`double- ESC` 就是这么漏的）
- 大小写不敏感

**未命中仍不等于伪造**，只等于「换这几种方式都没找到」，须人工看一眼再定。
"""
import argparse, glob, json, pathlib, re, sys

SPLIT = re.compile(r"…|\.\.\.")
NONWORD = re.compile(r"[^0-9A-Za-z]+")
MIN = 20        # 投影后的最小长度；再短就不足以判定


def proj(s: str) -> str:
    """投影成只保留字母数字的小写串——标点／空白／markdown／引号形态全部抹平。"""
    return NONWORD.sub("", s).lower()


def find(seg: str, projected) -> bool:
    q = proj(seg)
    if len(q) < MIN:
        return True                      # 太短，不作判据
    return any(q in t for t in projected)


# 负对照样本：四类伪造，覆盖从整句编造到「真句只改一个词」
SELF_TEST = [
    ("整句伪造", "I have always believed that writing tests before code is the single most important discipline"),
    ("真句改数字", "SD currently has 456 dependencies which weren't core in Perl 5.8.5"),
    ("真句改主语", "My colleague is prone to just tuning out a bit and thinking it's probably fine"),
    ("真句只改一词", "This reduces context bloat for the reviewer and gets it to look at again"),
]


def self_test(projected) -> int:
    """负对照：植入的伪造引文必须全部被抓到，一条漏掉即判本检查器失效。"""
    print("\n══ 负对照（伪造引文必须全部抓到）══")
    missed = 0
    for label, q in SELF_TEST:
        caught = not find(q, projected)
        print(f"  {'✓ 抓到' if caught else '✗ 漏掉'}  {label}: 「{q[:62]}…」")
        missed += not caught
    print("  ✓ 负对照通过" if not missed else f"  ✗ 漏掉 {missed} 条——本检查器已失效，不得依赖其结论")
    return missed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True, type=pathlib.Path)
    ap.add_argument("--cache", required=True, nargs="+")
    ap.add_argument("--self-test", action="store_true",
                    help="同时跑负对照；改动本脚本后必须跑一次")
    a = ap.parse_args()

    texts = []
    for d in a.cache:
        for f in glob.glob(f"{d}/*.txt"):
            texts.append(proj(pathlib.Path(f).read_text(encoding="utf-8", errors="replace")))
    print(f"语料 {len(texts)} 份（已投影为字母数字串）")

    Q = re.compile(r"[「\"]([A-Za-z][^」\"]{18,300})[」\"]")
    tot = seg_tot = 0
    bad = []
    for line in a.claims.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        for m in Q.finditer(r["claim"]):
            tot += 1
            for seg in SPLIT.split(m.group(1)):
                if len(proj(seg)) < MIN:
                    continue
                seg_tot += 1
                if not find(seg, texts):
                    bad.append((r["claim_id"], re.sub(r"\s+", " ", seg).strip()[:100]))

    print(f"引文 {tot} 条，切分后核验片段 {seg_tot} 个，未命中 {len(bad)} 个")
    for cid, s in bad:
        print(f"  ⚠ {cid}: 「{s}」")
    print("  ✓ 全部可在语料中找到" if not bad
          else "\n  ⚠ 未命中不等于伪造——须人工看一眼原文再定（见文件头）")
    if a.self_test and self_test(texts):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
