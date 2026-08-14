#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 `attribution_basis.parallel_witnesses` 申报 —— **默认只量不写**。

为什么要有这件工具
------------------
仓里早有两道判据管「同一部作品的两个见证不许当两处独立证据」：
`check_translation_witness.py` 与 `check_claim_source_independence.py`
（Pacioli #161 那轮落的）。**它们都好用，但都在等一个申报。**

2026-08-14 实测：**43 个工作区里 41 个没有申报 `parallel_witnesses`**，
于是 `check_translation_witness` 在全库都印「申报的并行见证组 0 个」——
它自己已经写明「0 组不等于没有并行见证，本件不猜，只查申报」，
可没有任何东西去做那个申报。㊸ 记的「40 条两处证据其实一部作品」，根因就在这里。
[[a-checker-nothing-calls-is-not-a-checker]]｜[[zero-hit-gates-must-prove-they-can-hit]]

本件不是第三把尺子
------------------
判定规则**照抄** `check_claim_source_independence` 的口径：
8 词片、包含率 `|A∩B| / min(|A|,|B|)`、阈值 0.30、**不做传递闭包**。
它只把结果写成申报，判定仍由那两道判据做。

★ 三条写死的纪律
1. **只申报「团」** —— 组内每一对都要直接超阈值。靠传递闭包串起来的分量单列出来、
   不申报（并查集把 32 份源串成一个分量那次，判据报了 17/17 全塌缩）。
   [[hundred-percent-failure-is-a-checker-bug]]
2. **跨语言恒 0，所以「没被合并 ≠ 独立」** —— 译本不会进任何组。
   本申报只覆盖同语种同源。输出里必须印这句。
   [[cross-language-holdout-leak-is-invisible]]
3. **默认 `--dry-run`**（不给 `--apply` 就不写盘）。㊵ 已裁「已判分即冻结」，
   给存量工作区写申报可能让现在绿的门变红 —— 那是**发现**，但要人先看见数再决定。

用法
----
    python3 emit_parallel_witnesses.py --self-test
    python3 emit_parallel_witnesses.py --root <_corpora>            # 全库只量
    python3 emit_parallel_witnesses.py --workspace <ws> --apply     # 写单个工作区
"""
import argparse
import collections
import hashlib
import itertools
import json
import pathlib
import re
import sys

SHINGLE = 8
SAMPLE = 12          # hash % SAMPLE == 0，约 1/12
THRESHOLD = 0.30


def signature(text):
    words = re.findall(r"\w+", text.lower())
    out = set()
    for i in range(0, max(0, len(words) - SHINGLE + 1)):
        h = hashlib.blake2b(" ".join(words[i:i + SHINGLE]).encode("utf-8"), digest_size=8).digest()
        if h[0] % SAMPLE == 0:
            out.add(h)
    return out


def containment(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def group_workspace(ws):
    """→ (团列表, 只靠传递闭包连起来的分量, 源数)"""
    led = ws / "evidence/source-ledger.jsonl"
    if not led.exists():
        return [], [], 0
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    sigs = {}
    for r in rows:
        p = ws / r.get("local_path", "")
        if p.exists() and p.is_file():
            s = signature(p.read_text(encoding="utf-8", errors="replace"))
            if s:
                sigs[r["source_id"]] = s
    ids = sorted(sigs)
    cont = {}
    for a, b in itertools.combinations(ids, 2):
        c = containment(sigs[a], sigs[b])
        if c > 0:
            cont[(a, b)] = c

    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), c in cont.items():
        if c >= THRESHOLD:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    comp = collections.defaultdict(list)
    for i in ids:
        comp[find(i)].append(i)

    cliques, transitive = [], []
    for members in comp.values():
        if len(members) < 2:
            continue
        members = sorted(members)
        weak = [(a, b, cont.get((min(a, b), max(a, b)), 0.0))
                for a, b in itertools.combinations(members, 2)
                if cont.get((min(a, b), max(a, b)), 0.0) < THRESHOLD]
        (transitive if weak else cliques).append((members, weak))
    return [m for m, _ in cliques], transitive, len(ids)


# ★ 分母必须与门一致 —— `quality_check.py` 只对这六类要求 ≥2 个 source_ids。
#   第一版没过滤类别，把 `fact` 也算进去：Koch 报 46，而权威判据报 15
#   （它印「检查的断言: 17」——分母是 17 不是 46）。**又一次往大里报。**
#   [[measurement-errors-all-point-the-same-way]]｜[[counts-need-their-cutoff-stated]]
MULTI_SOURCE_CATEGORIES = {
    "mental-model", "heuristic", "value", "work-method", "blind-spot", "contradiction",
}


def collapse_count(ws, groups):
    """→ (会塌的条数, 分母＝六类里引 ≥2 源的条数, 断言总数)"""
    cl = ws / "evidence/claims.jsonl"
    if not cl.exists():
        return 0, 0, 0
    claims = [json.loads(l) for l in cl.read_text(encoding="utf-8").splitlines() if l.strip()]
    scope = [c for c in claims
             if c.get("category") in MULTI_SOURCE_CATEGORIES
             and len(set(c.get("source_ids") or [])) >= 2]
    # ★ 判定式要与权威判据一致：它印的是「**全部**来源塌缩成一部作品」，
    #   不是「任意两份同源」。一条引 3 份、其中 2 份同源而第 3 份独立的，
    #   仍剩 2 部作品 —— **它判过，不判塌**。
    #   我第二版写成「任意两份同源就塌」，Koch 报 17 而权威判据报 15，
    #   差的正是那 5 条引 3 份里的 2 条。**第三次往大里报了。**
    #   [[measurement-errors-all-point-the-same-way]]
    work_of = {}
    for gi, g in enumerate(groups):
        for s in g:
            work_of[s] = "g%d" % gi
    hit = 0
    for c in scope:
        srcs = set(c.get("source_ids") or [])
        works = set(work_of.get(s, s) for s in srcs)   # 未成组的源，各算一部
        if len(works) < 2:
            hit += 1
    return hit, len(scope), len(claims)


def selftest():
    bad = 0
    a = {b"\x01", b"\x02", b"\x03", b"\x04"}
    b = {b"\x01", b"\x02", b"\x03", b"\x09"}
    if abs(containment(a, b) - 0.75) > 1e-9:
        print("  ✗ 包含率算错"); bad += 1
    # 小的整个在大的里面：Jaccard 会漏，包含率不该漏
    small = {b"\x01", b"\x02"}
    big = set(bytes([i]) for i in range(1, 60))
    if containment(small, big) != 1.0:
        print("  ✗ 小集合整个在大集合里，包含率该是 1.0"); bad += 1
    jac = len(small & big) / len(small | big)
    if jac >= THRESHOLD:
        print("  ✗ 这个反例本该证明 Jaccard 会漏（%.4f 应 < %.2f）" % (jac, THRESHOLD)); bad += 1
    if containment(set(), big) != 0.0:
        print("  ✗ 空集合该得 0"); bad += 1
    print("自测 %d/4" % (4 - bad))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--root", help="_corpora 目录，扫全部工作区")
    ap.add_argument("--apply", action="store_true", help="写进 meta.json（默认只量不写）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not (a.workspace or a.root):
        ap.error("要 --workspace 或 --root")

    targets = []
    if a.workspace:
        targets = [pathlib.Path(a.workspace)]
    else:
        # ★ 认工作区靠**它有没有台账**，不靠路径层数。
        #   第一版写 `*/workspaces/*/meta.json`，**57 个里漏了 14 个** ——
        #   9 个工作区的路径套了两层（`workspaces/<slug>/<slug>/`），
        #   还有 `ws-godin/seth-godin/`、`wip-galen-101/`（直接在顶层）等摆法。
        #   于是 Nightingale 整个没被扫到，而台账定案里正有「Nightingale 2 条」。
        #   [[a-gates-scan-set-is-smaller-than-reality]]｜[[eval-artifacts-have-five-schemas]]
        seen = set()
        for led in sorted(pathlib.Path(a.root).rglob("evidence/source-ledger.jsonl")):
            ws = led.parent.parent
            if (ws / "meta.json").exists() and ws not in seen:
                seen.add(ws)
                targets.append(ws)

    tot_ws = tot_groups = tot_ids = tot_collapse = tot_scope = 0
    already = 0
    print("★ 口径：8 词片｜包含率 ≥ %.2f｜**只申报团，不做传递闭包**｜默认不写盘" % THRESHOLD)
    print("★ 跨语言 n 元重叠恒 0 ⇒ **没被合并 ≠ 独立**，译本不会进任何组。\n")
    for ws in targets:
        metaf = ws / "meta.json"
        if not metaf.exists():
            continue
        try:
            meta = json.loads(metaf.read_text(encoding="utf-8"))
        except Exception:
            continue
        had = (meta.get("attribution_basis") or {}).get("parallel_witnesses")
        groups, transitive, n = group_workspace(ws)
        collapsed, in_scope, n_claims = collapse_count(ws, groups)
        tot_ws += 1
        tot_groups += len(groups)
        tot_ids += sum(len(g) for g in groups)
        tot_collapse += collapsed
        tot_scope += in_scope
        if had:
            already += 1
        flag = "已申报" if had else ("**要申报**" if groups else "无同源")
        print("  %-32s 源 %3d｜团 %2d（%2d id）｜传递分量 %d｜断言 %3d｜**六类里引≥2源 %2d 条 → 会塌 %2d**  %s"
              % (ws.name[:32], n, len(groups), sum(len(g) for g in groups),
                 len(transitive), n_claims, in_scope, collapsed, flag))
        if a.apply and groups:
            # ★ 沿用原文件的缩进 —— 第一版写死 indent=2，把 Dewey 的 meta.json
            #   整个重排（+129/−81 行），语义上只多了一个键，但复审时看不出来。
            #   **写盘工具不许顺手改排版。** [[dont-measure-a-file-while-its-writer-runs]]
            raw = metaf.read_text(encoding="utf-8")
            m = re.search(r"\n(\s+)\"", raw)
            indent = len(m.group(1)) if m else 2
            ab = meta.setdefault("attribution_basis", {})
            ab["parallel_witnesses"] = groups
            metaf.write_text(json.dumps(meta, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")

    print("\n  工作区 %d 个（已申报 %d）｜团合计 %d 组 / %d 个 id"
          % (tot_ws, already, tot_groups, tot_ids))
    print("  **分母 %d 条**（六类里引 ≥2 源的）→ **会塌 %d 条**"
          % (tot_scope, tot_collapse))
    print("  ★ 分母与门一致：`quality_check.py` 只对 mental-model/heuristic/value/")
    print("    work-method/blind-spot/contradiction 六类要求 ≥2 个 source_ids。")
    if not a.apply:
        print("  （只量未写。要写盘加 `--apply`——★ ㊵ 已裁「已判分即冻结」，写之前先看上面这个数。）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
