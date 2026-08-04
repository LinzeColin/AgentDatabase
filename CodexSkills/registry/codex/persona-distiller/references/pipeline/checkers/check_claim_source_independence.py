#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**一条断言引的两份源，是不是同一部作品的两个见证？**

## 为什么有这道判据

`mental-model` / `heuristic` / `value` / `work-method` / `blind-spot` / `contradiction`
六类断言各要求 **≥2 个 `source_ids`**。那条要求想要的是**互相独立的两处证据**。

**但没有任何判据在问这两份源是不是同一部作品。**

#118 Elizabeth Blackwell 实测：LoC《Elizabeth Blackwell Papers》里的 33 份讲稿/文章手稿，
**18 份是印本的草稿**——重叠 51–90%：

```
essays-medical-sociology-v2-1902 ← sp-1235(89%) sp-1238(87%) sp-1242(85%) sp-1248(90%)
                                   sp-1250(59%) sp-1253(82%) sp-1257(84%) sp-1258(68%) sp-1260(81%)
essays-medical-sociology-v1-1902 ← sp-1244(73%) sp-1252(70%) sp-1254(64%) sp-1255(51%) sp-1256(64%)
wrong-right-methods-1883         ← sp-1261(60%) sp-1262(76%)
medical-education-women-1864     ← sp-1236(76%)
counsel-to-parents-1878          ← sp-1240(52%)
```

**引手稿＋引它的印本，字面上是两个 `source_id`，实质上是一处证据。**

这与 Koch #107 那件（`source_ids` 46 条全是同一对）**是同一个病的两个表面**：
那件是**同一对反复用**，本件是**两份看着不同、实为一物**。
前者 `check_evidence_is_per_claim` 拦得住，**后者它拦不住**——
它只看字段有没有区分度，不看字段指的东西是不是同一个。

## 判据

对每条有 ≥2 个 `source_ids` 的断言：两两算 8 词片重叠率
（**以较短的一侧为分母**，因为草稿常常只是印本的一节）。

- **重叠 ≥30% 判为同一作品**，这一对**不计作两份独立证据**
- 若一条断言的全部 `source_ids` 塌缩成 **1 部作品**，报出

## 它判不了什么

- **判不了引得对不对**——两份真独立的源，也可能都不支持那条断言。
  那是 `check_quote_integrity` 与人的活。
- **判不了「同一作者不同作品之间的自我重复」是否算独立**。
  她在两部书里说同一句话，本件会判为同一作品（重叠高）——
  **这是有意的**：那确实只是一处证据，说了两遍不会变成两处。
- **阈值 30% 是按 #118 实测形状定的**（真重复 51–90%，真独立 <10%，
  中间是空的）。**没有实测支持把它设在别处，也没有实测说它跨人物成立。**
"""
import argparse
import json
import pathlib
import re
import sys

SHINGLE = 8
DUP_THRESHOLD = 0.30
WORD = re.compile(r"[a-z0-9]+")
MULTI_SOURCE_CATEGORIES = {"mental-model", "heuristic", "value", "work-method",
                           "blind-spot", "contradiction"}


def shingles(text: str, n: int = SHINGLE) -> set:
    w = WORD.findall(text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def overlap(a: set, b: set) -> float:
    """→ 重叠率，**以较短的一侧为分母**。

    草稿常常只是印本的一节：拿印本当分母会把 90% 的重复算成 5%。
    """
    small = min(len(a), len(b))
    return len(a & b) / small if small else 0.0


def group_works(texts: dict) -> dict:
    """→ {source_id: 作品组代表}。重叠 ≥30% 的并进同一组（并查集）。"""
    ids = sorted(texts)
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    sh = {i: shingles(texts[i]) for i in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if overlap(sh[a], sh[b]) >= DUP_THRESHOLD:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra
    return {i: find(i) for i in ids}


def evaluate(claims: list, works: dict) -> tuple:
    """→ (问题列表, 计量)。"""
    problems, collapsed, checked = [], 0, 0
    for c in claims:
        if c.get("status") == "superseded":
            continue
        if c.get("category") not in MULTI_SOURCE_CATEGORIES:
            continue
        sids = [s for s in (c.get("source_ids") or []) if s in works]
        if len(sids) < 2:
            continue
        checked += 1
        distinct = {works[s] for s in sids}
        if len(distinct) < 2:
            collapsed += 1
            problems.append(
                f"`{c.get('claim_id')}`（{c.get('category')}）引了 {len(sids)} 个 source_id，"
                f"**但它们是同一部作品的多个见证**——实质只有 1 处证据：{', '.join(sids[:4])}")
    info = {
        "检查的断言": checked,
        "**全部来源塌缩成一部作品的**": collapsed,
        "作品组数": len({v for v in works.values()}),
        "来源数": len(works),
        "口径": ("判「两份源是不是同一部作品」，**不判「引得对不对」**——"
                 f"两两 {SHINGLE} 词片重叠 ≥{DUP_THRESHOLD:.0%}（以较短一侧为分母）即判同一作品"),
    }
    return problems, info


# ══════════════════ 自测 ══════════════════

def _mk(*parts) -> str:
    return " ".join(parts)


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    BODY_A = _mk(*[f"the practice of vivisection must be considered under its moral aspect number {i}"
                   for i in range(40)])
    BODY_B = _mk(*[f"sanitation is the ground of prevention and of cure in case {i}" for i in range(40)])
    # 草稿 = 印本的一节（**长度差很大**，这正是分母要取较短一侧的原因）
    DRAFT_A = _mk(*[f"the practice of vivisection must be considered under its moral aspect number {i}"
                    for i in range(12)])

    print("── 正向：草稿与其印本必须判为同一作品 ──")
    works = group_works({"pub-a": BODY_A, "ms-a": DRAFT_A, "pub-b": BODY_B})
    chk("草稿与印本同组", works["pub-a"] == works["ms-a"])
    chk("另一部书不同组", works["pub-b"] != works["pub-a"])

    print("── 正向：断言只引「草稿＋其印本」→ 必须报出 ──")
    pb, info = evaluate([{"claim_id": "clm-x", "category": "heuristic",
                          "source_ids": ["pub-a", "ms-a"]}], works)
    chk(f"报出 1 条（实报 {len(pb)}）", len(pb) == 1 and "同一部作品" in pb[0])

    print("── 反向对照 ①：引两部真不同的书 → 不许报 ──")
    pb2, _ = evaluate([{"claim_id": "clm-y", "category": "heuristic",
                        "source_ids": ["pub-a", "pub-b"]}], works)
    chk("一条不报", not pb2)

    print("── 反向对照 ②：**只引一个源的断言不归本门管** ──")
    #   「只有一个来源」是 `check_claim_anchors` 的活；本门只判「多个源是不是同一物」。
    pb3, info3 = evaluate([{"claim_id": "clm-z", "category": "heuristic",
                            "source_ids": ["pub-a"]}], works)
    chk("不报，且不计入「检查的断言」", not pb3 and info3["检查的断言"] == 0)

    print("── 反向对照 ③：fact 类不要求多源，不归本门管 ──")
    pb4, info4 = evaluate([{"claim_id": "clm-f", "category": "fact",
                            "source_ids": ["pub-a", "ms-a"]}], works)
    chk("不报", not pb4 and info4["检查的断言"] == 0)

    print("── 反向对照 ④：superseded 的断言不判 ──")
    pb5, _ = evaluate([{"claim_id": "clm-s", "category": "heuristic", "status": "superseded",
                        "source_ids": ["pub-a", "ms-a"]}], works)
    chk("不报", not pb5)

    print("── ★ 反向对照 ⑤：分母取较短一侧——取长的会漏判 ──")
    a, b = shingles(BODY_A), shingles(DRAFT_A)
    long_denom = len(a & b) / len(a)
    chk(f"以长侧为分母只有 {long_denom:.1%}（<{DUP_THRESHOLD:.0%}，**会漏判**）；"
        f"以短侧为分母 {overlap(a, b):.1%}（≥{DUP_THRESHOLD:.0%}，判对）",
        long_denom < DUP_THRESHOLD <= overlap(a, b))

    print("── 反向对照 ⑥：引了不在语料里的 source_id → 跳过，不许当成独立证据 ──")
    pb6, info6 = evaluate([{"claim_id": "clm-u", "category": "heuristic",
                            "source_ids": ["pub-a", "不存在的源"]}], works)
    chk("有效源不足 2 个 → 不计入检查（**由 check_claim_anchors 管**）",
        not pb6 and info6["检查的断言"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=pathlib.Path, help="人物工作区")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    ev = a.workspace / "evidence"
    cf, lf = ev / "claims.jsonl", ev / "source-ledger.jsonl"
    if not (cf.is_file() and lf.is_file()):
        print("✗ **claims.jsonl 或 source-ledger.jsonl 不在——未核验（不是通过）**"); return 3
    claims = [json.loads(l) for l in cf.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not claims:
        print("✗ **claims.jsonl 为空——未核验（不是通过）**"); return 3

    texts = {}
    for line in lf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        p = a.workspace / (r.get("local_path") or "")
        if r.get("source_id") and p.is_file():
            texts[r["source_id"]] = p.read_text(encoding="utf-8", errors="replace")
    if not texts:
        print("✗ **一份正文都读不到——未核验（不是通过）**"); return 3

    works = group_works(texts)
    problems, info = evaluate(claims, works)
    for k, v in info.items():
        print(f"  {k}: {v}")
    if not problems:
        print("\n  ✓ 没有断言的多个来源塌缩成同一部作品")
        return 0
    print()
    for p in problems:
        print("✗ " + p)
    print("\n**「两个 source_id」不等于「两处证据」——换一份真独立的源，不要改门。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
