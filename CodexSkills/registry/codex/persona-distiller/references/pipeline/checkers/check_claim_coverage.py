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
    # ★★★★ 2026-08-11：**只认 `.txt` 是一个没说出口的口径**。
    #   `ingest.py` 收什么就该读什么。实测：
    #     · 生产侧 `raw/` 里 **1643 个 `.txt`、0 个 `.md`** —— 放宽对生产**零影响**；
    #     · 而**测试夹具的源全是 `.md`** → `rglob("*.txt")` 读到 0 份，
    #       于是夹具的内容层**从来没被真正跑过**，
    #       直到今天 `--cache` 自动接上才暴露（报「一份语料都没读到」）。
    #   `fixtures-cleaner-than-the-real-thing` 的又一形态：
    #   **夹具不是太干净，是它长得跟生产不一样，于是那道门在它身上一直是空转的。**
    for f in sorted(p for ext in ("*.txt", "*.md") for p in cache.rglob(ext)):
        try:
            raw_bytes = f.read_bytes()
            raw_text = raw_bytes.decode("utf-8", errors="replace")
        except Exception:
            continue
        body = corpus_body(raw_text)
        # ★★★★ 2026-08-11：**两把钥匙都登记，值都是剥了表头的正文**。
        #
        #   台账里的 `checksum` 是 `sha256(原始字节)`（`ingest.py:360`，
        #   且 `source_id = src-{checksum[:12]}` **就是从它派生的**——
        #   改生产端会动全库每一个 source_id，所以只能在这一侧对齐）。
        #   而这里为了「表头不是他的话」，比对用的正文是 `corpus_body()` 之后的 body。
        #   **两侧算法不一致，只在「这份文件没有抓源表头」时才偶然相等。**
        #
        #   2026-08-11 实测（台账条数 / 按 body 命中 / 按原始字节命中）：
        #     Adams    72 /  0 / 69      Bessemer 55 /  0 / 54
        #     Coffin   18 /  0 / 18      Thomson  56 /  0 / 53
        #     Cicero   19 / 11 / 11      Shewhart 13 / 12 / 12
        #   ——四个带表头的工作区**一条都对不上**，判据对它们一律 exit 2
        #   「语料回连不上，结论不可信」。不是语料坏了，是**join key 两边不一样**。
        #
        #   ★ 值仍然是 `body`：**表头不算他的话这条语义没有放宽**，
        #     放宽的只是「用哪个哈希找得到这份文件」。
        out[hashlib.sha256(raw_bytes).hexdigest()] = body
        out[hashlib.sha256(body.encode("utf-8")).hexdigest()] = body
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

        # ── 2026-08-11：**台账的 checksum 是原始字节的**，这一路要能回连 ──
        #   四个带抓源表头的工作区（Adams/Bessemer/Coffin/Thomson）此前
        #   **一条都对不上**，判据对它们一律 exit 2「结论不可信」。
        hdr = root / "hdr"
        hdr.mkdir()
        HEAD = "# source: archive.org/details/xyz\n# fetched: 2026-08-11\n"
        raw_with_head = HEAD + body
        (hdr / "c.txt").write_text(raw_with_head, encoding="utf-8")
        cache_h = load_cache(hdr)
        k_raw = hashlib.sha256(raw_with_head.encode("utf-8")).hexdigest()
        k_body = hashlib.sha256(body.encode("utf-8")).hexdigest()

        ok_raw = k_raw in cache_h
        print(f"  {'✓' if ok_raw else '✗'} 带表头的文件：**按原始字节的 checksum 找得到**"
              f"（台账存的就是这一种，ingest.py:360）")
        fail += not ok_raw

        ok_body_key = k_body in cache_h
        print(f"  {'✓' if ok_body_key else '✗'} 同一份文件：按剥表头后的 checksum 也找得到（向后兼容）")
        fail += not ok_body_key

        # ★★ 非放宽性的证明：**取到的值必须是剥了表头的正文**
        val_ok = (cache_h.get(k_raw) == body
                  and "archive.org/details/xyz" not in cache_h.get(k_raw, ""))
        print(f"  {'✓' if val_ok else '✗'} ★ 取到的**值仍是剥了表头的正文**——"
              f"「表头不算他的话」没有被放宽，放宽的只是「用哪个哈希找得到」")
        fail += not val_ok

        # 反向对照：不相干的 checksum 仍然找不到
        k_none = hashlib.sha256(b"nothing like this in the corpus").hexdigest()
        print(f"  {'✓' if k_none not in cache_h else '✗'} 反向对照：不相干的 checksum 仍然回连不上")
        fail += k_none in cache_h

        # 反向对照之二：目录里没有任何 .txt 时必须是空，不得凭空命中
        empty = root / "empty"
        empty.mkdir()
        got_empty = load_cache(empty)
        print(f"  {'✓' if not got_empty else '✗'} 空目录读到 0 份，不凭空命中（反向对照）")
        fail += bool(got_empty)

    # ── 2026-08-11 新增：**著录实体认台账**这条路径的正反对照 ──────────
    #   Shewhart #165 实测：断言写「BSTJ 1926 逐字：…」，而 BSTJ 那篇文章的正文里
    #   `BSTJ` 与 `1926` 各 0 次（`Bell System` 4 次）——著录信息在台账，不在正文。
    #   ★ 只有反例红不算数：⑨ 必须绿、⑩⑪ 必须红，否则「认台账」就成了万能通行证。
    BODY_BSTJ = ("The reason for trying to find assignable causes of variation is "
                 "economic. Bell System engineers observed that ...")
    META_OK = "1926 BSTJ 5(4) 593-603"
    CLAIM_CITE = "**他给出的理由是经济理由。** BSTJ 1926 逐字：「The reason for trying」"

    t_cite = key_terms(CLAIM_CITE)
    body_hit = {t for t in t_cite if t in BODY_BSTJ}
    meta_hit = {t for t in t_cite if t not in BODY_BSTJ and t in META_OK}
    ok9 = ("1926" in meta_hit and "BSTJ" in meta_hit
           and "1926" not in body_hit and "BSTJ" not in body_hit)
    print(f"  {'✓' if ok9 else '✗'} ⑨ 著录实体（BSTJ/1926）正文里没有、台账里有 → "
          f"算命中但**单列**（body={sorted(body_hit)} meta={sorted(meta_hit)}）")
    fail += not ok9

    META_WRONGYEAR = "1931 BSTJ 5(4) 593-603"
    bad10 = {t for t in t_cite if t not in BODY_BSTJ and t in META_WRONGYEAR}
    ok10 = "1926" not in bad10
    print(f"  {'✓' if ok10 else '✗'} ⑩ 台账年份写成 1931 → 断言里的 1926 仍**不**命中（红）")
    fail += not ok10

    META_WRONGJRNL = "1926 JASA 21(153) 65-72"
    bad11 = {t for t in t_cite if t not in BODY_BSTJ and t in META_WRONGJRNL}
    ok11 = "BSTJ" not in bad11
    print(f"  {'✓' if ok11 else '✗'} ⑪ 台账刊名写成 JASA → 断言里的 BSTJ 仍**不**命中（红）")
    fail += not ok11

    # ── ★★★ 2026-08-17：实际检查 0 条时不许印「通过」（子进程断言，正反各一）──
    #   benardos-128 实测：「源账本 0 条 … 实际检查 0/0 条 … 结论: 通过」rc=0。
    #   ★ 断言打在**子进程真正印出来的那一行**上：印字在 `main()` 里。
    import subprocess as _sp, sys as _sys, tempfile as _tf, json as _json
    _self = str(pathlib.Path(__file__).resolve())

    def _run(claims: list, corpus: str) -> str:
        with _tf.TemporaryDirectory() as _td:
            w = pathlib.Path(_td) / "ws"; (w / "evidence").mkdir(parents=True)
            c = pathlib.Path(_td) / "cache"; c.mkdir()
            (w / "evidence" / "claims.jsonl").write_text(
                "".join(_json.dumps(x, ensure_ascii=False) + "\n" for x in claims),
                encoding="utf-8")
            (w / "evidence" / "source-ledger.jsonl").write_text("", encoding="utf-8")
            (c / "a.txt").write_text(corpus, encoding="utf-8")
            return _sp.run([_sys.executable, _self, "--workspace", str(w), "--cache", str(c)],
                           capture_output=True, text=True).stdout

    _o0 = _run([], "irrelevant corpus text\n")
    ok_a = "**未核，不是通过**" in _o0
    ok_b = "实际检查 0/0" in _o0 and "结论: 通过" not in _o0
    print(f"  {'✓' if ok_a else '✗'} ★★★ 实际检查 0 条 → 印「未核，不是通过」")
    print(f"  {'✓' if ok_b else '✗'} ★★★ 实际检查 0 条 → **不许**印「结论: 通过」")
    fail += (not ok_a) + (not ok_b)

    print("  ✓ 负对照通过（15/15）" if not fail
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
    meta_backed = []   # 仅靠台账著录（published_at / locator）命中的，正文里没有
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
        meta_only: set[str] = set()
        for sid in c.get("source_ids", []):
            r = led.get(sid, {})
            body = texts.get(r.get("checksum", ""), "") + " " + str(r.get("title", ""))
            hit |= {t for t in terms if t in body}
            # ★★★★ 2026-08-11：**著录实体也要认台账**。
            #   2026-08-11 Shewhart #165 实测：断言写「BSTJ 1926 逐字：…」，
            #   而源 `src-f3562c1704fe` 的正文（`bstj5-4-593_djvu.txt`，25,183 字符）里
            #   `1926` **0 次**、`BSTJ` **0 次**（`Bell System` 倒有 4 次）——
            #   **期刊缩写与出版年本来就不印在文章正文里，它们在台账里。**
            #   台账记的正是 published_at=1926 / locator=`BSTJ 5(4) 593–603`，
            #   来源完全正确，而这条命中**永远变不绿**
            #   （`a-red-that-can-never-turn-green-is-not-a-signal`）。
            #   ★ 这不是放宽：写错年份（1931）或写错刊名仍然红，见自测 ⑦⑧。
            #   ★★ 且**不混进正文命中**——单列一节「仅靠台账著录命中」，
            #     免得「查过正文」和「只对上了著录」被读成同一件事。
            meta = " ".join(str(r.get(k, "")) for k in ("published_at", "locator"))
            meta_only |= {t for t in terms if t not in body and t in meta}
        if meta_only:
            meta_backed.append((c["claim_id"], c.get("category"), sorted(meta_only)[:6]))
        hit |= meta_only
        ratio = len(hit) / len(terms)
        if not hit:
            decorative.append((c["claim_id"], c.get("category"), sorted(terms)[:8], c["claim"][:64]))
        elif ratio < args.min_hit:
            weak.append((c["claim_id"], c.get("category"), round(ratio, 2), sorted(terms - hit)[:6]))

    if meta_backed:
        print(f"\n── 仅靠台账著录命中（正文里没有，**不等于正文核过**）: {len(meta_backed)} ──")
        for cid, cat, terms in meta_backed[:10]:
            print(f"  · {cid} [{cat}] {terms}　←　期刊缩写/出版年本就不印在文章正文里")

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
    # ★★★ 2026-08-17：**实际检查 0 条时不许印「通过」**。
    #   `decorative` 为空在空集上恒真 ⇒ benardos-128 实测输出是
    #   「源账本 0 条 … 实际检查 **0/0** 条 … 结论: 通过」并 rc=0。
    #   而本件上面几行**自己就写着**「未检查，不等于通过」——
    #   那句话对 `unverifiable` 那一档说了，对「一条都没有」这一档没说。
    #   ★ 只改措辞、**不改退出码**（收紧判定属决定不属清理；调用点
    #     `quality_check.py:1855` 只区分 rc 0/1/2，本改动不动它）。
    #   [[zero-hit-gates-must-prove-they-can-hit]]｜[[a-continue-hid-the-worst-case]]
    if decorative:
        print("结论: 不通过——存在装饰性引用")
    elif checked == 0:
        print(f"结论: **未核，不是通过** —— 实际检查 0 条"
              f"（账本 {len(claims)} 条断言：语料元 {len(corpus_meta)}、"
              f"无实体无引文 {len(unverifiable)}，**没有一条进入本件的射程**）")
    else:
        print(f"结论: 通过（**{checked}** 条逐条查过）")
    return 1 if decorative else 0


if __name__ == "__main__":
    sys.exit(main())
