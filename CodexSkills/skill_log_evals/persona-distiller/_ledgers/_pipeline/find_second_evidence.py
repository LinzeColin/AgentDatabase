#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""find_second_evidence.py —— **给单源 claim 找第二处，且不许找出假的**

## 它是什么

2026-08-14 Dewey #190 上，三条「补不到第二处证据」的 claim 里有 **3 条其实补得到**。
我一开始按 Brandeis 的样本下了结论「40 条全部材料里没有」——**推错了**。
把当时手工做的那套动作固化成本件，免得下一个人再靠手感。

## 那套动作（**四步，缺一步就会出假证据**）

1. **正对照先跑**：拿你的正则去 claim **已引的那份源**上搜。
   **搜不到就停** —— 尺子抓不到已知正例时，它在别处报的数一律不算。
   （实测踩过：`aware of what resists` 里 aware 在 resist 前面，我的交替分支没覆盖，
     那一版报「8 部作品命中」，全是废数。）
2. **排除同一部作品**：候选源与已引源的 Jaccard ≥0.05 或包含率 ≥0.25 就跳过 ——
   同一本书的另一次扫描、短文被收进的文集，都不是第二处。
3. **候选之间也要归组**：不然一部书的三次印本会被数成三部。
4. **逐条读**，不看数。松正则的命中大多是误报（`in spite of the fact` 讲铁路滞留费、
   `The term is not much used in the West`）。**本件只交候选，不下结论。**

## 它不做什么

- **不改任何 claim**、不写盘。只把候选连上下文印出来给人读。
- **跨语言判不了** ⇒ 在多语种工作区，「不同作品」这个判断本身就不可靠，会额外印警告。
- **holdout 一律排除**，不许拿密封集当第二处。

## 用法

    python3 find_second_evidence.py --workspace <工作区> --claim <claim_id> --pattern '<正则>'
    python3 find_second_evidence.py --workspace <工作区>            # 只列出哪些 claim 是单源的
    python3 find_second_evidence.py --self-test

退出码：0＝跑完；3＝**正对照没过**（尺子坏了，别看结果）；4＝读不到正文
"""
import argparse
import glob
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_claim_evidence_independence import NEEDS_TWO, guess_lang, same_work  # noqa: E402
from measure_distinct_works import signature  # noqa: E402


def norm(t: str) -> str:
    """OCR 版面归一：去软连字符、接回断字、压空白。**纯函数**。

    ★ 不归一就搜不到：`in-\\ndustrial` 会让逐字搜索报「不存在」，
      而它明明在那里。[[filename-matching-is-brittle]] 的文本版。
    """
    t = t.replace("­", "")
    t = re.sub(r"-\s*\n\s*", "", t)
    return re.sub(r"\s+", " ", t)


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    chk("★ 归一：接回断字（`in- dustrial` → `industrial`）",
        "industrial premium" in norm("in-\ndustrial premium"))
    chk("★ 归一：压掉换行与多空格", norm("a  b\n  c") == "a b c")
    chk("★ 归一：软连字符去掉", norm("indus­trial") == "industrial")
    # ★★ 正对照这一步本身要能失败
    rx = re.compile(r"aware of what resists")
    cited = "we are acutely aware of what resists us"
    chk("★★ 正对照命中 → 允许继续", bool(rx.search(cited)))
    bad = re.compile(r"\bresist\w+\b[^.]{0,40}\baware\b")   # 顺序写反的尺子
    chk("★★ **反例：顺序写反的尺子在已知正例上不命中** ⇒ 必须判 3、不许出结果",
        not bad.search(cited))
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def load(ws: pathlib.Path):
    led = ws / "evidence/source-ledger.jsonl"
    rows = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()]
    txt, sig, meta = {}, {}, {}
    for r in rows:
        if r.get("split") != "train":      # ★ holdout 一律排除
            continue
        p = ws / str(r.get("local_path") or "")
        if not p.is_file():
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        s = r["source_id"]
        txt[s], sig[s] = norm(raw), signature(raw)
        meta[s] = (r.get("published_at"), (r.get("title") or "")[:36], guess_lang(raw))
    return txt, sig, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--claim")
    ap.add_argument("--pattern")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要 --workspace")
    ws = pathlib.Path(a.workspace)
    claims = [json.loads(x) for x in (ws / "evidence/claims.jsonl")
              .read_text(encoding="utf-8").splitlines() if x.strip()]

    if not a.claim:
        single = [c for c in claims if c.get("category") in NEEDS_TWO
                  and len(set(c.get("source_ids", []))) < 2]
        print(f"{ws.name}：需 ≥2 处支撑的 {sum(1 for c in claims if c.get('category') in NEEDS_TWO)} 条，"
              f"**只有 1 个 source_id 的 {len(single)} 条**：")
        for c in single:
            print(f"  {c['claim_id']} [{c.get('category')}] ← {c.get('source_ids')}")
            print(f"      {(c.get('claim') or '')[:120]}")
        print("\n★ 挑一条，把它**自带的判据**写成正则再跑一次：--claim <id> --pattern '<正则>'")
        return 0

    if not a.pattern:
        ap.error("给了 --claim 就要给 --pattern（把 claim 自带的判据写成正则）")
    tgt = next((c for c in claims if c.get("claim_id") == a.claim), None)
    if tgt is None:
        print(f"❌ 没有这条 claim：{a.claim}")
        return 3
    txt, sig, meta = load(ws)
    if not txt:
        print("★ **未量，不是通过** —— 读不到任何 train 正文（语料按裁定不进 git）")
        return 4
    cited = [s for s in tgt.get("source_ids", []) if s in txt]
    if not cited:
        print(f"★ **未量** —— 已引的源 {tgt.get('source_ids')} 在本机读不到")
        return 4
    rx = re.compile(a.pattern, re.I)

    # ── 第 1 步：正对照 ──
    hit0 = [s for s in cited if rx.search(txt[s])]
    if not hit0:
        print(f"❌ **正对照没过**：这把尺子在已引的 {cited} 上一处也不命中。")
        print("   ⇒ 尺子抓不到已知正例，它在别处报的数**一律不算**。先改尺子。")
        return 3
    m = rx.search(txt[hit0[0]])
    print(f"✓ 正对照：在 {hit0[0]} 上命中 —— 「{m.group()[:110]}」\n")

    # ── 第 2/3 步：排除同一部作品，候选之间也归组 ──
    cands = {}
    for s, t in txt.items():
        if s in cited or any(same_work(sig[s], sig[c]) for c in cited):
            continue
        for mm in rx.finditer(t):
            cands.setdefault(s, []).append(t[max(0, mm.start() - 170):mm.end() + 220])
    groups = {}
    for s in cands:
        g = next((k for k in groups if same_work(sig[k], sig[s])), s)
        groups.setdefault(g, []).append(s)

    langs = {meta[s][2] for s in txt if meta[s][2] != "?"}
    # ★★ 印分母：候选是从多大的集合里挑的。没有这一行，「候选 0 部」会被读成
    #   「这个人没有第二处」，而它也可能是「能搜的作品本来就只有一两部」。
    _works = {}
    for s in txt:
        g = next((k for k in _works if same_work(sig[k], sig[s])), s)
        _works.setdefault(g, []).append(s)
    _ex = sum(1 for s in txt if s in cited or any(same_work(sig[s], sig[c]) for c in cited))
    print(f"★★ **搜索面**：本工作区 train 有正文的 {len(txt)} 份 → **{len(_works)} 部独立作品**；"
          f"其中 {_ex} 份是已引源或与之同一部（已排除）")
    print(f"候选：{sum(len(v) for v in cands.values())} 处，落在 **{len(groups)} 部不同作品**"
          f"（已排除已引源本身及其同一部作品、已排除 holdout）")
    if len(langs) > 1:
        print(f"★★ 本工作区混着 {len(langs)} 种语言 {sorted(langs)} —— "
              f"**「不同作品」这个判断在这里本身就不可靠**（原文 vs 译文重叠恒为 0）")
    print("★ **本件只交候选，不下结论**。下面每一条都要打开读，松正则的命中大多是误报。\n")
    for g, members in groups.items():
        y, ti, lg = meta[g]
        extra = f"（另有同一部作品的 {len(members)-1} 份：{members[1:]}）" if len(members) > 1 else ""
        print(f"── {g} {y}《{ti}》[{lg}] {len(cands[g])} 处{extra}")
        print(f"   …{cands[g][0][:330]}…\n")
    if not groups:
        print("★ 一部也没有 —— **而正对照是过的**，所以这是**语料的结论**，不是尺子坏了。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
