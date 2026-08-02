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
LONGS = re.compile(r"[fs]")


def proj(s: str) -> str:
    """投影成只保留字母数字的小写串——标点／空白／markdown／引号形态全部抹平。"""
    return NONWORD.sub("", s).lower()


def fold_s(s: str) -> str:
    """把 f 与 s 折叠成同一符号。**只允许这一种字形差**，不是通用模糊匹配。

    1800 年前的印本用长 s（ſ），OCR 普遍认成 f：`inferted`／`fuperficial incifions`／`Efq`。
    本项目允许引用时把它还原成 s 并注明，所以核验时必须容这一种差；
    **但也只容这一种**——OCR 的其它噪声（`DoHors`←Doctors、`WOQDVILLE`←WOODVILLE）
    折叠后仍然对不上，照样报出来。那正是本门要抓的：**把 OCR 错字顺手改正了再当逐字引文用。**
    """
    return LONGS.sub("§", s)


def find(seg: str, projected, folded=None) -> str:
    """返回 'exact' / 'longs' / '' —— 空串表示未命中。"""
    q = proj(seg)
    if len(q) < MIN:
        return "exact"                   # 太短，不作判据
    if any(q in t for t in projected):
        return "exact"
    if folded is not None and any(fold_s(q) in t for t in folded):
        return "longs"
    return ""


# 负对照样本：四类伪造，覆盖从整句编造到「真句只改一个词」（**构造夹具**）
SELF_TEST = [
    ("整句伪造", "I have always believed that writing tests before code is the single most important discipline"),
    ("真句改数字", "SD currently has 456 dependencies which weren't core in Perl 5.8.5"),
    ("真句改主语", "My colleague is prone to just tuning out a bit and thinking it's probably fine"),
    ("真句只改一词", "This reduces context bloat for the reviewer and gets it to look at again"),
]

# ★ 真实夹具：全部取自 #104 Edward Jenner 第 3 轮的实际答案与实际语料，一字未改。
# 前两条必须放行（长 s 还原是明写的允许），第三条必须抓出（改的是 OCR 错字，不是长 s）。
REAL_LONGS_OK = ("长 s 还原—须放行",
                 "it was inserted, on the 14th of May, 1796, into the arm of the boy "
                 "by means of two superficial incisions")
REAL_VERBATIM_OK = ("逐字命中—须放行",
                    "It was not with Sir Joseph, but with Home ; he took the paper. "
                    "It was shewn to the Council, and returned to me")
REAL_OCR_FIXED = ("改了 OCR 错字—须抓出",
                  "To Doctors JENNER and WOODVILLE")   # 语料作 "To DoHors JENNER and WOQDVILLE"


def self_test(projected, folded) -> int:
    """负对照 + 真实夹具 + 两条反向对照。任何一条不合即判本检查器失效。"""
    missed = 0
    print("\n══ 负对照（伪造引文必须全部抓到）══")
    for label, q in SELF_TEST:
        caught = not find(q, projected, folded)
        print(f"  {'✓ 抓到' if caught else '✗ 漏掉'}  {label}: 「{q[:62]}…」")
        missed += not caught

    print("\n══ 真实夹具（Jenner #104 实际数据，一字未改）══")
    for label, q in (REAL_LONGS_OK, REAL_VERBATIM_OK):
        hit = find(q, projected, folded)
        ok = bool(hit)
        print(f"  {'✓' if ok else '✗ 误杀'}  {label}（{hit or '未命中'}）: 「{q[:58]}…」")
        missed += not ok
    hit = find(REAL_OCR_FIXED[1], projected, folded)
    print(f"  {'✓ 抓到' if not hit else '✗ 漏掉'}  {REAL_OCR_FIXED[0]}: 「{REAL_OCR_FIXED[1]}」")
    missed += bool(hit)

    print("\n══ 反向对照 ══")
    # ① 抽掉语料：真实引文必须转红——证明放行来自语料，不是来自匹配太松
    a = find(REAL_VERBATIM_OK[1], [], [])
    print(f"  {'✓' if not a else '✗'} 抽掉语料后，逐字命中的那条转为未命中")
    missed += bool(a)
    # ② 关掉长 s 折叠：长 s 样本必须转红——证明放行来自这条明写的允许本身
    b = find(REAL_LONGS_OK[1], projected, None)
    print(f"  {'✓' if not b else '✗'} 关掉长 s 折叠后，长 s 样本转为未命中")
    missed += bool(b)

    print("\n  ✓ 负对照通过" if not missed else f"\n  ✗ {missed} 条不合——本检查器已失效，不得依赖其结论")
    return missed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", type=pathlib.Path,
                    help="断言层 claims.jsonl")
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[],
                    help="**答案层**：候选答案 JSON（id→文本）或盲判载荷（[{case_id,A,B}]）。"
                         "断言层绿不代表答案层绿——被判、被发布的是答案层。")
    ap.add_argument("--cache", required=True, nargs="+")
    ap.add_argument("--self-test", action="store_true",
                    help="同时跑负对照；改动本脚本后必须跑一次")
    a = ap.parse_args()

    texts, folded = [], []
    for d in a.cache:
        for f in glob.glob(f"{d}/*.txt"):
            p = proj(pathlib.Path(f).read_text(encoding="utf-8", errors="replace"))
            texts.append(p)
            folded.append(fold_s(p))
    print(f"语料 {len(texts)} 份（已投影为字母数字串）")

    Q = re.compile(r"[「\"]([A-Za-z][^」\"]{18,300})[」\"]")

    def scan(label: str, unit_id: str, text: str, acc):
        for m in Q.finditer(text):
            acc["quotes"] += 1
            for seg in SPLIT.split(m.group(1)):
                if len(proj(seg)) < MIN:
                    continue
                acc["segs"] += 1
                hit = find(seg, texts, folded)
                if hit == "longs":
                    acc["longs"].append((unit_id, re.sub(r"\s+", " ", seg).strip()[:100]))
                elif not hit:
                    acc["bad"].append((f"{label}/{unit_id}", re.sub(r"\s+", " ", seg).strip()[:100]))

    acc = {"quotes": 0, "segs": 0, "bad": [], "longs": []}

    if a.claims:
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                scan("断言", r["claim_id"], r["claim"], acc)

    for path in a.answers:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):           # 盲判载荷
            for row in data:
                for side in ("A", "B"):
                    if isinstance(row.get(side), str):
                        scan("答案", f"{row.get('case_id')}:{side}", row[side], acc)
        elif isinstance(data, dict):         # id → 文本
            for k, v in data.items():
                if isinstance(v, str) and not k.startswith("_"):
                    scan("答案", k, v, acc)

    if not a.claims and not a.answers:
        print("  ⚠ 既没给 --claims 也没给 --answers，**什么都没核**（不是通过）")

    print(f"引文 {acc['quotes']} 条，切分后核验片段 {acc['segs']} 个，"
          f"未命中 {len(acc['bad'])} 个，长 s 还原后才命中 {len(acc['longs'])} 个")
    for cid, s in acc["longs"]:
        print(f"  · 长 s 还原后命中 {cid}: 「{s[:70]}」")
    for cid, s in acc["bad"]:
        print(f"  ⚠ {cid}: 「{s}」")
    print("  ✓ 全部可在语料中找到" if not acc["bad"]
          else "\n  ⚠ 未命中不等于伪造——须人工看一眼原文再定（见文件头）。"
               "\n    但**「改了 OCR 错字再当逐字引文用」也会落在这里**，那一类是真问题。")
    if a.self_test and self_test(texts, folded):
        return 2
    return 2 if acc["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())
