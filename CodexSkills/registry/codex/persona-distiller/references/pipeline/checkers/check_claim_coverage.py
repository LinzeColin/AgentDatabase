#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""断言覆盖度检查：被引来源的正文，到底谈没谈这条断言。

## 为什么需要它

Icahn #92 的实测：72 个源、一手占比 94%（全项目最高）、每条 claim 挂 2 个源、
lane 引用全部合法——**四道门全过**。但整条 TWA 事实链所挂的两个源是
《致苹果股东信》与《国会必须行动，辉瑞正在离开美国》，
**正文里没有 TWA、Karabu、1993、bankrupt、airline 任何一个词。**

**现有的门只数 source_id 的个数，从不看来源内容。**
于是「挂两个不相干的源」和「挂两个真正支撑的源」在门上完全等价。

本脚本补的就是这一层：对每条 claim 抽出关键实体（专名、年份、金额），
到被引来源的**缓存正文**里去找。一个都找不到的，判为**装饰性引用**。

## 负对照（`--self-test`，RUNBOOK 第十八种）

本脚本是硬门，且有一个隐蔽的失效方式：**`key_terms` 抽不出实体的断言会被静默跳过**
（`if not terms: continue`）。一条纯中文、无专名无年份的断言，
无论挂什么源都不会被检查——**它在报告里表现为「通过」，而不是「未检查」**。

负对照因此要测三件事：
  ① 挂了不相干源的断言，必须被判为装饰性引用；
  ② 挂了真正支撑源的断言，必须不被误判；
  ③ 抽不出关键实体的断言，必须**显式计入「未检查」**而不是混进通过数。

实测 3/3。**改动 `key_terms` 或 STOP 表后必须重跑**——
停用词多加一个，就可能让一批断言从「有实体可查」掉进「静默跳过」。

用法：
    python3 check_claim_coverage.py --workspace <target> --cache <cache_dir>
    python3 check_claim_coverage.py --workspace ... --cache ... --min-hit 0.34
    python3 check_claim_coverage.py --self-test          # 只跑负对照
"""
from __future__ import annotations

import argparse, hashlib, json, pathlib, re, sys

#: ★ 剥掉抓源方写的出处表头再量——**表头是出处说明，不是他的话**。
#:   全库只有 Adams（144 份）与 Coffin（36 份）有这种表头，
#:   实测占全文**聚合 17.2% / 11.7%**，**逐份中位 39.1% / 16.1%**。
#: ★★ 接上之后**逐个量过前后差**，只写量到的：
#:   · `check_lane_quotes_verbatim` @ Coffin：核过 1 → 0，
#:     报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
#:     那句「逐字引文」只存在于**我自己写的表头里**。这是 Barton 事故的引文版，实锤一条。
#:   · ★★★★ `check_ocr_language_death` @ Coffin：不剥时「**每一份都在下限之上**」，
#:     剥掉表头后报出 **2 份虚词占比 0.101（下限 0.15）**——
#:     **我那段干净的英文表头把 OCR 烂掉的文件托过了及格线。**
#:     同一件在 Adams 上是「可判份数 94 → 60」：34 份**只因表头的词数才够得上判**。
#:   · `check_first_person_density`：正文字符 −0.6%，密度 1.68 → **1.69**——
#:     **几乎没变**。我一度在这里写「第一人称密度被表头拉偏」，**那句没有实测支撑，已删**。
#:   · 其余多数判据前后一致。**接线是按「表头不是他的话」这条原则做的，不是因为每个都变了。**
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

# 停用词：出现频率过高、不具指示性，纳入会让覆盖率虚高
STOP = {"The", "And", "But", "For", "This", "That", "With", "From", "Not", "You",
        "His", "Her", "Its", "All", "One", "Two", "New", "Inc", "Corp", "LLC", "Ltd"}


# 引文投影：标点／空白／markdown 全抹平后做子串匹配。
# 与 check_quote_integrity.py 同一套投影——那边验过负对照（4 类伪造全抓、0 误报）。
_NONWORD = re.compile(r"[^0-9A-Za-z]+")
_QUOTE = re.compile(r"[「\"]([A-Za-z][^」\"]{18,300})[」\"]")
_ELLIPSIS = re.compile(r"…|\.\.\.")
_MINQ = 20


def _proj(s: str) -> str:
    return _NONWORD.sub("", s).lower()


def quoted_spans(claim: str) -> list[str]:
    """抽出断言里的英文引文片段（按省略号切段，投影后过短的丢弃）。

    这些片段比 key_terms 更强的判据：**引文必须出现在它自己引的那个源里**，
    而不是「语料里某处有」。后者只能证明这句话是真的，
    证明不了「这条断言挂的源支撑这条断言」——而后者才是装饰性引用要查的东西。
    """
    out = []
    for m in _QUOTE.finditer(claim):
        for seg in _ELLIPSIS.split(m.group(1)):
            if len(_proj(seg)) >= _MINQ:
                out.append(seg)
    return out


def key_terms(claim: str) -> set[str]:
    """抽取可判定的关键实体：英文专名、四位年份、金额。

    中文断言里的专名多以英文原名或数字出现（TWA／Karabu／1993／2 亿），
    因此以英文词与数字为主，避免对中文做不可靠的分词。
    """
    terms: set[str] = set()
    terms |= {w for w in re.findall(r"\b[A-Z][A-Za-z&.\-]{2,}\b", claim) if w not in STOP}
    terms |= set(re.findall(r"\b(?:1[5-9]\d{2}|20\d{2})\b", claim))
    return terms


def load_cache(cache: pathlib.Path) -> dict[str, str]:
    """checksum -> 正文。产物只存校验和，靠它回连缓存正文。

    ★ v0.0.0.38：`glob` 改 `rglob`。
    本流水线自己产出的语料布局是 `raw/<source_id>/<file>.txt`——**深一层**，
    非递归的 `glob("*.txt")` 对着 `raw/` 读到的永远是 0 份。
    Lister #108 实测：`glob` 0 份、`rglob` 60 份、校验和命中 60/61。
    也就是说这件检查器**从来没有在标准工作区上真正跑起来过**，
    除非调用方手工把 61 个子目录一个个传进来。
    """
    out: dict[str, str] = {}
    for f in cache.rglob("*.txt"):
        try:
            t = corpus_body(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        out[hashlib.sha256(t.encode("utf-8")).hexdigest()] = t
    return out


def self_test() -> int:
    """三向负对照：装饰性引用抓到、真支撑不误判、无实体断言显式计入未检查。"""
    print("══ 负对照 ══")
    fail = 0

    SUPPORT = ("In 1993, TWA emerged from bankruptcy under the Karabu ticket agreement, "
               "which Icahn negotiated as part of the airline's restructuring.")
    IRRELEVANT = ("Dear Apple shareholders, we believe the board should authorize "
                  "a larger buyback program to return capital.")
    CLAIM = "**1993 年 TWA 破产重整时他谈下了 Karabu 票务协议**"

    terms = key_terms(CLAIM)
    got = bool(terms)
    print(f"  {'✓' if got else '✗'} 能抽出关键实体: {sorted(terms)}")
    fail += not got

    hit_bad = {x for x in terms if x in IRRELEVANT}
    print(f"  {'✓' if not hit_bad else '✗'} 挂不相干源 → 判为装饰性引用"
          f"（命中 {sorted(hit_bad) or '空'}）")
    fail += bool(hit_bad)

    hit_ok = {x for x in terms if x in SUPPORT}
    print(f"  {'✓' if hit_ok else '✗'} 挂真支撑源 → 不误判（命中 {sorted(hit_ok)}）")
    fail += not hit_ok

    NOENT = "**他倾向于先把话说清楚再动手**"
    no_ent = not key_terms(NOENT) and not quoted_spans(NOENT)
    print(f"  {'✓' if no_ent else '✗'} 无实体无引文的断言被识别为不可查"
          f"——这类**必须显式计入「未检查」**，不得混进通过数")
    fail += not no_ent

    QC = '**停手的理由可以是风险而非能力**：「I stepped back right at the point where it was going to involve reverse engineering iCloud」'
    qs = quoted_spans(QC)
    ok_q = len(qs) == 1 and _proj(qs[0]) in _proj(
        "and so I stepped back right at the point where it was going to involve "
        "reverse engineering iCloud, because that felt like a bad idea")
    bad_q = _proj(qs[0]) in _proj("a completely unrelated post about keyboards") if qs else True
    print(f"  {'✓' if ok_q else '✗'} 引文判据：命中真正引它的源")
    print(f"  {'✓' if not bad_q else '✗'} 引文判据：不误命中不相干的源")
    fail += (not ok_q) + bad_q

    # ── v0.0.0.38 新增：语料回连本身的负对照 ────────────────────────
    # 此前 5 项全在「拿到正文之后判得对不对」这一层，
    # **没有一项管「有没有拿到正文」**——于是 rglob 缺陷躲过了历次自测。
    # 判据自测全绿而射程根本没覆盖到被判的东西，这是第四次。
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        body = "Lister applied carbolic acid to compound fracture in 1867."
        want = hashlib.sha256(body.encode("utf-8")).hexdigest()

        nest = root / "raw" / "src-deadbeef"
        nest.mkdir(parents=True)
        (nest / "a.txt").write_text(body, encoding="utf-8")
        got_nested = want in load_cache(root / "raw")
        print(f"  {'✓' if got_nested else '✗'} 嵌套布局 raw/<src>/x.txt **能**读到"
              f"——这是流水线自己产出的布局")
        fail += not got_nested

        # 反向对照：平铺布局不得因为改成递归就退化
        flat = root / "flat"
        flat.mkdir()
        (flat / "b.txt").write_text(body, encoding="utf-8")
        got_flat = want in load_cache(flat)
        print(f"  {'✓' if got_flat else '✗'} 平铺布局 dir/x.txt 仍能读到（反向对照）")
        fail += not got_flat

        # 反向对照之二：目录里没有任何 .txt 时必须是空，不得凭空命中
        empty = root / "empty"
        empty.mkdir()
        got_empty = load_cache(empty)
        print(f"  {'✓' if not got_empty else '✗'} 空目录读到 0 份，不凭空命中（反向对照）")
        fail += bool(got_empty)

    print("  ✓ 负对照通过（8/8）" if not fail
          else f"  ✗ {fail} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true", help="只跑负对照")
    ap.add_argument("--workspace", type=pathlib.Path)
    # 一个人物的语料可能分布在多个缓存目录（如正文与外部视角分开抓）。
    # 只传一个目录会让另一部分源「回连不上」，从而**把工具缺陷误报成装饰性引用**。
    ap.add_argument("--cache", type=pathlib.Path, nargs="+")
    ap.add_argument("--min-hit", type=float, default=0.0,
                    help="关键实体命中比例低于该值即告警；默认 0 表示只查「一个都没命中」")
    args = ap.parse_args()
    if args.self_test:
        return 1 if self_test() else 0
    if not args.workspace or not args.cache:
        ap.error("--workspace 与 --cache 必填（除非用 --self-test）")

    W = args.workspace
    led = {}
    for line in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            led[r["source_id"]] = r
    texts = {}
    for c in args.cache:
        texts.update(load_cache(c))
    resolved = sum(1 for r in led.values() if r.get("checksum") in texts)
    print(f"源账本 {len(led)} 条，其中 {resolved} 条能回连到缓存正文")
    if resolved < len(led) * 0.6:
        print("⚠️  过半来源取不到正文，本次检查结果不可信——先确认 cache 目录是否正确")
        return 2

    claims = [json.loads(l) for l in (W / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    decorative, weak, corpus_meta, unverifiable = [], [], [], []
    quote_checked = 0
    for c in claims:
        claim_txt = c.get("claim", "")

        # ★ 语料元断言必须**先于** terms 判断。
        #   它陈述的是「这份语料本身长什么样」，证据是源账本与抓取记录，
        #   不可能出现在任何单一来源正文里。
        #   **原来这段在 `if not terms: continue` 之后**，于是抽不出实体的语料元断言
        #   走不到这里，被误归为「无实体无引文」——分类错了，覆盖率报告因此失真。
        if "语料" in str(c.get("applicability", "")):
            corpus_meta.append((c["claim_id"], claim_txt[:70]))
            continue

        terms = key_terms(claim_txt)
        quotes = quoted_spans(claim_txt)

        # 无专名可查时，退到引文判据：引文须出现在**被引的那个源**里
        if not terms and quotes:
            bodies = "".join(texts.get(led.get(sid, {}).get("checksum", ""), "")
                             for sid in c.get("source_ids", []))
            pj = _proj(bodies)
            missing = [q for q in quotes if _proj(q) not in pj]
            if missing:
                decorative.append((c["claim_id"], c.get("category"),
                                   [f"引文不在被引源中: 「{m[:46]}…」" for m in missing[:2]],
                                   claim_txt[:64]))
            else:
                quote_checked += 1
            continue
        if not terms:
            unverifiable.append((c["claim_id"], claim_txt[:64]))
            continue
        hit: set[str] = set()
        for sid in c.get("source_ids", []):
            r = led.get(sid, {})
            body = texts.get(r.get("checksum", ""), "") + " " + str(r.get("title", ""))
            hit |= {t for t in terms if t in body}
        ratio = len(hit) / len(terms)
        if not hit:
            decorative.append((c["claim_id"], c.get("category"), sorted(terms)[:8], c["claim"][:64]))
        elif ratio < args.min_hit:
            weak.append((c["claim_id"], c.get("category"), round(ratio, 2), sorted(terms - hit)[:6]))

    print(f"\n══ 装饰性引用（关键实体一个都没在被引来源里出现）: {len(decorative)}/{len(claims)} ══")
    for cid, cat, terms, txt in decorative:
        print(f"  ✗ {cid} [{cat}] 缺 {terms}\n      {txt}")
    if args.min_hit > 0:
        print(f"\n══ 覆盖偏弱（命中率 < {args.min_hit}）: {len(weak)} ══")
        for cid, cat, ratio, missing in weak:
            print(f"  ⚠ {cid} [{cat}] 命中率 {ratio} 缺 {missing}")

    if corpus_meta:
        print(f"\n══ 语料元断言（证据为源账本／抓取记录，需人工核对）: {len(corpus_meta)} ══")
        for cid, txt in corpus_meta:
            print(f"  · {cid} {txt}")

    # ★ 抽不出关键实体的断言 = **未检查**，不是「通过」。
    #   静默跳过会让报告上的「0 装饰性引用」名不副实——
    #   分母里混着一批从来没查过的断言，而读报告的人看不出来。
    if unverifiable:
        print(f"\n══ 无关键实体、本工具查不了（**未检查，不等于通过**）: {len(unverifiable)} ══")
        for cid, txt in unverifiable:
            print(f"  ? {cid} {txt}")

    checked = len(claims) - len(corpus_meta) - len(unverifiable)
    print(f"\n实际检查 {checked}/{len(claims)} 条"
          f"（其中按引文判据 {quote_checked} 条；语料元断言 {len(corpus_meta)}、"
          f"无实体无引文 {len(unverifiable)} 未纳入）")
    print(f"结论: {'不通过——存在装饰性引用' if decorative else '通过'}")
    return 1 if decorative else 0


if __name__ == "__main__":
    sys.exit(main())
