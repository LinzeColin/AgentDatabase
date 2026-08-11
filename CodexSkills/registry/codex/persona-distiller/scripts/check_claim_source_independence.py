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

#: ★ 剥掉抓源方写的出处表头再量——**表头是给人看的出处说明，不是他的话**。
#:   Adams 实测表头占全文中位 39.1%，两两 2556 对里 1764 对因此越线。
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402
import re
import sys
import zlib

SHINGLE = 8
DUP_THRESHOLD = 0.30
WORD = re.compile(r"[a-z0-9]+")
MULTI_SOURCE_CATEGORIES = {"mental-model", "heuristic", "value", "work-method",
                           "blind-spot", "contradiction"}


# ★ 确定性采样：只保留哈希落在 1/SAMPLE 的片。
#   两两比对是 O(n²)，而本人物 89 份源里最大的一份有 40 万个片——
#   **第一版接进门之后 release 与 synthesis 双双超时（>2 分钟）。**
#   一道跑不完的门等于没有门。
#   采样是无偏的：分子分母同样被抽稀，比值的期望不变；
#   `SAMPLE=8` 下最小的源仍留下上百个片，够判。
SAMPLE = 8


def shingles(text: str, n: int = SHINGLE) -> set:
    """→ 采样后的 n 词片集合。

    ★★ **必须用确定性哈希。** 第一版用了内建 `hash()`——
    Python 对 tuple/str 的 `hash()` **带每进程随机种子**（PYTHONHASHSEED），
    实测同一个 `('a','b')` 两次进程给出 -112675601284210612 与 -2838368082701080650。
    那样采样不可复现：**同一份语料两次跑能给出不同结论**。
    `zlib.crc32` 无种子、跨进程稳定。
    """
    w = WORD.findall(text.lower())
    out = set()
    for i in range(len(w) - n + 1):
        s = tuple(w[i:i + n])
        if zlib.crc32(" ".join(s).encode()) % SAMPLE == 0:
            out.add(s)
    return out


def overlap(a: set, b: set) -> float:
    """→ 重叠率，**以较短的一侧为分母**。

    草稿常常只是印本的一节：拿印本当分母会把 90% 的重复算成 5%。
    """
    small = min(len(a), len(b))
    return len(a & b) / small if small else 0.0


def pairwise(texts: dict) -> dict:
    """→ {(a, b): 重叠率}，**直接**两两，不做任何传递。"""
    ids = sorted(texts)
    sh = {i: shingles(texts[i]) for i in ids}
    return {(a, b): overlap(sh[a], sh[b])
            for i, a in enumerate(ids) for b in ids[i + 1:]}


def group_works(texts: dict, _pw: dict = None) -> dict:
    """→ {source_id: 作品组代表}。重叠 ≥30% 的并进同一组（并查集）。

    ★★★★ **这个函数的结果只能当参考，不能当判据**——见 `evaluate` 里那段注释。
    并查集是**传递闭包**：A↔B 0.35、B↔C 0.35 就把 A 与 C 判成同一部，
    而 A↔C 实测可以是 **0.000**。Lister 工作区实测：最大分量 **32 份（占 52%）**，
    分量内随手挑的三对重叠是 **0.001 / 0.000 / 0.000**。
    """
    ids = sorted(texts)
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    pw = _pw if _pw is not None else pairwise(texts)
    for (a, b), v in pw.items():
        if v >= DUP_THRESHOLD:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
    return {i: find(i) for i in ids}


def evaluate(claims: list, works: dict, pw: dict = None, declared: dict = None) -> tuple:
    """→ (问题列表, 计量)。

    ★★★★ **判「塌缩」用被引源之间的直接重叠，不用全局连通分量。**

    原先用 `works`（并查集分量）判，实测把两类东西混在一起：

    - 真塌缩：草稿与它的印本，直接重叠 0.9+；
    - **传递噪声**：A↔B 0.35、B↔C 0.35，而 **A↔C = 0.000**，
      整个工作区被一条条边串成一个 32 份的大分量（Lister 实测占 52%），
      于是「引了这两份」必然被判成同一部。

    现在的口径：**被引的源两两直接重叠都 ≥30%，才算实质只有 1 处证据。**
    只要存在一对直接重叠 <30%，那就是两处证据，不报。

    分量口径的结果**不丢弃**，作为 `参考·按连通分量` 一并打印——
    [[empty-default-swallows-unknown]]：换口径不许把旧口径的数字静默吞掉。
    """
    problems, collapsed, checked, comp_only, by_decl = [], 0, 0, 0, 0
    pw = pw or {}
    declared = declared or {}

    def ov(a, b):
        return pw.get((a, b), pw.get((b, a), 0.0))

    def same_work_declared(a, b) -> bool:
        """台账**自己声明过**这两份是同一部作品吗。

        ★★★★ 2026-08-11 新增。此前本件**只看内容重叠**，
        而 `derived_from` 这个字段一次都没被读过——它比 30% 阈值确定得多。

        Koch #107 实测：`src-9115214f10fd.derived_from` 里**明写着**
        `src-94dc006b6b8a`，而 **41 条断言**拿这两份当两处证据。
        本件靠 74% 重叠才发现，**信息其实早就在台账里躺着**。

        ★★ 更要紧的是**重叠抓不到的那一类**：
        跨语种的同一部作品（拉丁原本 vs 英译本）**内容重叠在结构上恒为 0**——
        Grotius #168 的 holdout 就是这样，`check_holdout_overlap` 报 0.007%。
        **那种情形只有声明抓得到。**
        """
        return b in declared.get(a, ()) or a in declared.get(b, ())

    for c in claims:
        if c.get("status") == "superseded":
            continue
        if c.get("category") not in MULTI_SOURCE_CATEGORIES:
            continue
        sids = [s for s in (c.get("source_ids") or []) if s in works]
        if len(sids) < 2:
            continue
        checked += 1
        pairs = [(a, b) for i, a in enumerate(sids) for b in sids[i + 1:]]
        lowest = min((ov(a, b) for a, b in pairs), default=1.0)
        by_comp = len({works[s] for s in sids}) < 2
        all_declared = pairs and all(same_work_declared(a, b) for a, b in pairs)
        if lowest >= DUP_THRESHOLD or all_declared:
            collapsed += 1
            by_decl += bool(all_declared)
            why = ("**台账自己声明过它们同源**（`derived_from`）"
                   if all_declared else
                   f"**它们两两直接重叠都 ≥{DUP_THRESHOLD:.0%}（最低 {lowest:.0%}）**")
            problems.append(
                f"`{c.get('claim_id')}`（{c.get('category')}）引了 {len(sids)} 个 source_id，"
                f"{why}——是同一部作品的多个见证，"
                f"实质只有 1 处证据：{', '.join(sids[:4])}")
        elif by_comp:
            comp_only += 1
    info = {
        "检查的断言": checked,
        "**全部来源塌缩成一部作品的**": collapsed,
        "★ 其中**靠台账声明**判出的": by_decl,
        "参考·按连通分量多报的": comp_only,
        "作品组数（连通分量，仅供参考）": len({v for v in works.values()}),
        "来源数": len(works),
        "口径": ("判「两份源是不是同一部作品」，**不判「引得对不对」**——"
                 f"**被引的源两两直接** {SHINGLE} 词片重叠都 ≥{DUP_THRESHOLD:.0%}"
                 "（以较短一侧为分母）才判塌缩；**不做传递闭包**。"
                 "★ 或者**台账的 `derived_from` 已声明它们同源**——"
                 "那一条比阈值确定，且能抓到重叠恒为 0 的跨语种同源"),
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
    TEXTS = {"pub-a": BODY_A, "ms-a": DRAFT_A, "pub-b": BODY_B}
    PW = pairwise(TEXTS)
    works = group_works(TEXTS, PW)
    chk("草稿与印本同组", works["pub-a"] == works["ms-a"])
    chk("另一部书不同组", works["pub-b"] != works["pub-a"])

    print("── 正向：断言只引「草稿＋其印本」→ 必须报出 ──")
    pb, info = evaluate([{"claim_id": "clm-x", "category": "heuristic",
                          "source_ids": ["pub-a", "ms-a"]}], works, PW)
    chk(f"报出 1 条（实报 {len(pb)}）", len(pb) == 1 and "同一部作品" in pb[0])

    print("── 反向对照 ①：引两部真不同的书 → 不许报 ──")
    pb2, _ = evaluate([{"claim_id": "clm-y", "category": "heuristic",
                        "source_ids": ["pub-a", "pub-b"]}], works, PW)
    chk("一条不报", not pb2)

    print("── 反向对照 ②：**只引一个源的断言不归本门管** ──")
    #   「只有一个来源」是 `check_claim_anchors` 的活；本门只判「多个源是不是同一物」。
    pb3, info3 = evaluate([{"claim_id": "clm-z", "category": "heuristic",
                            "source_ids": ["pub-a"]}], works, PW)
    chk("不报，且不计入「检查的断言」", not pb3 and info3["检查的断言"] == 0)

    print("── 反向对照 ③：fact 类不要求多源，不归本门管 ──")
    pb4, info4 = evaluate([{"claim_id": "clm-f", "category": "fact",
                            "source_ids": ["pub-a", "ms-a"]}], works, PW)
    chk("不报", not pb4 and info4["检查的断言"] == 0)

    print("── 反向对照 ④：superseded 的断言不判 ──")
    pb5, _ = evaluate([{"claim_id": "clm-s", "category": "heuristic", "status": "superseded",
                        "source_ids": ["pub-a", "ms-a"]}], works, PW)
    chk("不报", not pb5)

    print("── ★ 反向对照 ⑤：分母取较短一侧——取长的会漏判 ──")
    a, b = shingles(BODY_A), shingles(DRAFT_A)
    long_denom = len(a & b) / len(a)
    chk(f"以长侧为分母只有 {long_denom:.1%}（<{DUP_THRESHOLD:.0%}，**会漏判**）；"
        f"以短侧为分母 {overlap(a, b):.1%}（≥{DUP_THRESHOLD:.0%}，判对）",
        long_denom < DUP_THRESHOLD <= overlap(a, b))

    print("── 反向对照 ⑥：引了不在语料里的 source_id → 跳过，不许当成独立证据 ──")
    pb6, info6 = evaluate([{"claim_id": "clm-u", "category": "heuristic",
                            "source_ids": ["pub-a", "不存在的源"]}], works, PW)
    chk("有效源不足 2 个 → 不计入检查（**由 check_claim_anchors 管**）",
        not pb6 and info6["检查的断言"] == 0)

    print("── ★★★★ 反向对照 ⑦：**传递链不许把两处证据判成一处** ──")
    #   夹具照着真事故造：Lister 工作区里一条条 0.3x 的边把 32 份源串成一个分量，
    #   而分量内随手挑的三对重叠是 0.001 / 0.000 / 0.000。
    #   [[fixtures-cleaner-than-the-real-thing]]：原先 6 条反向对照，一条都没造出链条。
    HALF1 = _mk(*[f"chain left segment token {i} of the shared middle document" for i in range(30)])
    HALF2 = _mk(*[f"chain right segment token {i} of the shared middle document" for i in range(30)])
    MID = HALF1 + " " + HALF2                      # B 同时含 A 与 C 的内容
    T2 = {"end-a": HALF1, "mid-b": MID, "end-c": HALF2}
    PW2 = pairwise(T2)
    #   ★ pairwise 的键按 sorted(ids) 排，取的时候必须两个方向都试——
    #     第一版写死一个方向，`bc` 取到 None 当场炸了。宁可炸，也别默默取到 0.0。
    def pv(x, y):
        v = PW2.get((x, y), PW2.get((y, x)))
        assert v is not None, f"自测取不到 {x}↔{y} 的重叠——夹具或键序变了"
        return v
    ab, ac, bc = pv("end-a", "mid-b"), pv("end-a", "end-c"), pv("mid-b", "end-c")
    chk(f"链条造对了：A↔B {ab:.0%} ≥30%、B↔C {bc:.0%} ≥30%、**A↔C {ac:.0%} <30%**",
        ab >= DUP_THRESHOLD and bc >= DUP_THRESHOLD and ac < DUP_THRESHOLD)
    W2 = group_works(T2, PW2)
    chk("并查集**确实**把 A 与 C 并成了一组（所以旧口径必然误报）",
        W2["end-a"] == W2["end-c"])
    pb7, info7 = evaluate([{"claim_id": "clm-t", "category": "heuristic",
                            "source_ids": ["end-a", "end-c"]}], W2, PW2)
    chk(f"**新口径不报**（实报 {len(pb7)}），并记下「按分量会多报 {info7['参考·按连通分量多报的']} 条」",
        not pb7 and info7["参考·按连通分量多报的"] == 1)

    print("── ★ 正例仍须是绿的：真塌缩不许因为这次改口径而漏掉 ──")
    #   [[counter-example-red-can-be-red-by-coincidence]]：只看反例红了不算数。
    pb8, _ = evaluate([{"claim_id": "clm-x2", "category": "heuristic",
                        "source_ids": ["end-a", "mid-b"]}], W2, PW2)
    chk(f"A 与 B 直接重叠 {ab:.0%} ≥30% → **仍然报出**（实报 {len(pb8)}）", len(pb8) == 1)

    print("\n── ★★ `derived_from`：台账自己声明的同源（2026-08-11 新增）──")
    # Koch #107 实测：`src-9115...` 的 derived_from 里明写着 `src-94dc...`，
    # 而 41 条断言拿这两份当两处证据。本件此前**只看内容重叠**，一次都没读过这个字段。
    W3 = {"la": "la", "en": "en", "z": "z"}          # 三份「作品」，两两重叠 0
    PW3 = {("la", "en"): 0.0, ("la", "z"): 0.0, ("en", "z"): 0.0}
    DECL = {"la": {"en"}, "en": {"la"}}              # 台账声明 la 与 en 同源（拉丁本 vs 英译本）

    pbA, infoA = evaluate([{"claim_id": "clm-lang", "category": "heuristic",
                            "source_ids": ["la", "en"]}], W3, PW3, DECL)
    chk("跨语种同源：**重叠 0% 而台账已声明** → 报出（重叠口径永远抓不到这一类）",
        len(pbA) == 1)
    chk("  且报文说明是靠声明判的", bool(pbA) and "台账自己声明过" in pbA[0])
    chk("  计量里单列「靠台账声明判出的」= 1", infoA.get("★ 其中**靠台账声明**判出的") == 1)

    # ★ 反对照①：**没有声明**的两份，重叠 0% → 不许报（否则本件变成「凡两份皆报」）
    pbB, _ = evaluate([{"claim_id": "clm-ok", "category": "heuristic",
                        "source_ids": ["la", "z"]}], W3, PW3, DECL)
    chk("**反对照**：未声明且重叠 0% → 不报（两处真独立证据）", len(pbB) == 0)

    # ★ 反对照②：**只有一对声明、另一对没有**时，不许报——
    #   要求是「两两都同源」才算塌缩，一条独立的边就够撑起两处证据。
    pbC, _ = evaluate([{"claim_id": "clm-mix", "category": "heuristic",
                        "source_ids": ["la", "en", "z"]}], W3, PW3, DECL)
    chk("**反对照**：三份里只有一对声明同源 → 不报（还剩独立的边）", len(pbC) == 0)

    # ★ 反对照③：不传 declared 时行为与改动前一致（默认参数不许改变旧结论）
    pbD, _ = evaluate([{"claim_id": "clm-lang2", "category": "heuristic",
                        "source_ids": ["la", "en"]}], W3, PW3)
    chk("**反对照**：不传 declared → 回到旧行为，不报", len(pbD) == 0)

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

    texts, declared = {}, {}
    for line in lf.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        sid = r.get("source_id")
        # ★ 台账**自己声明过**的同源关系，双向记下——比内容重叠确定，
        #   且能抓到重叠恒为 0 的跨语种同源。
        for other in (r.get("derived_from") or []):
            if sid and other:
                declared.setdefault(sid, set()).add(other)
                declared.setdefault(other, set()).add(sid)
        p = a.workspace / (r.get("local_path") or "")
        if sid and p.is_file():
            texts[sid] = corpus_body(p.read_text(encoding="utf-8", errors="replace"))
    if not texts:
        print("✗ **一份正文都读不到——未核验（不是通过）**"); return 3

    pw = pairwise(texts)
    works = group_works(texts, pw)
    problems, info = evaluate(claims, works, pw, declared)
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
