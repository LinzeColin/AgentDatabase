#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这条引文在语料里——但在不在它自己引的那份源里？**

## 为什么有这件

`check_quote_integrity` 判的是「这句话在不在语料里」，**它扫的是全语料**。
于是下面这种错它一定放行：

```
断言：他在 1908 年 ASME v30 论文里写 `Habits of industry are far more valuable…`
source_ids: [src-<v30-1908>]
```

而这句话**同时**出现在 v30 与 1913 那本书里（本项目实测 v30→书重印重叠 57.6%）。
若我把它挂到书上、正文却说「1908 年那篇论文里」，**全语料能找到，门是绿的**——
读者按 `source_ids` 回查，会落到另一份文献、另一个年份、另一种体裁上。

这不是假想。Gantt #156 建引文库时实测：`Habits of industry` / `the era of force` /
`we make it a rule` / `Before intelligent action` / `Estimates of a busy foreman` /
`neither employer nor employee` **六句都命中两份以上**，而
**两份的 OCR 字形还不一样**（1910 本作 `they nm^er know ex-] actly how long`，
1913 本作 `they never Jcnoiv ex- actly lioiu long`）——
**挂错源的同时，逐字引文也会跟着错，而两件事都不改变任何计数。**

同族：[[gate-green-but-pointed-at-wrong-artifact]]、[[two-source-ids-is-not-two-evidences]]。

## 判据

对每条断言的每段长逐字引文（投影后 ≥ `MIN` 字符）：

1. 先看它在不在**这条断言自己的 `source_ids`** 对应的正文里 → 在，绿；
2. 不在，则去全语料找 → **找得到，报错**，并打印它的真实出处；
3. 全语料也找不到 → **本件不报**，那是 `check_quote_integrity` 的射程，
   两件都报会让同一个错被数两遍。

**归一与 `check_quote_integrity` 完全一致**（投影成字母数字小写串 + 长 s 折叠）——
**本件只隔离一个变量：归属。** 字形、标点、连字符的差异不由本件裁决。

## 射程边界（本件看不见的）

- **`source_ids` 里只要有一份含这句话就算过。** 一条断言引三份源、引文全出自其中一份，
  本件不报——那是 `check_claim_source_independence` 与「每类 ≥2 独立源」在管的事。
- **正文里「1908 年那篇」这类年份说法，本件不核。** 它只核 `source_ids` 这个机器可读字段。
- **`local_path` 指不到文件的源，本件跳过并计数**——跳过数会打印，
  不打印就会变成又一个「空默认值吞掉不知道」。[[empty-default-swallows-unknown]]

## ★★★★ 首扫那个数是**上界**，两类已知假阳（读过命中才发现的）

落成当天全库首扫报「挂错作品 19」。**逐条读过之后，其中至少两类不是缺陷**：

1. **目录/著录行被当成引文。** Virchow 第 23 条的「引文」是 `Virchow, Rudolf, 1821-1902`——
   一行图书馆著录。它满足 `Q` 的条件（拉丁字母开头、≥18 字符），于是被当成逐字引文核。
   **这是引号形态正则的固有假阳，本件继承了它**（[[read-the-hits-before-reporting-the-rate]]）。
2. **同一部书的不同卷被判成不同作品。** Virchow 第 44 条挂 `gesabh-oeffmed-1879-de-bd1`，
   而句子在 `-bd2`——**那是同一部文集的第 1 卷与第 2 卷**，
   两卷内容本来就不重叠，8 词片重叠必然 <30%，于是被判「不同作品」。
   **卷次关系本件看不见**，台账里的 `derived_from` 也不表达它。

**所以：本件的输出是「要人去看的清单」，不是「缺陷数」。**
真缺陷的样子长这样——Koch 四条全部挂 `b21353207_0001_0` / `b21463608_0001`，
而句子在 `s3728id1397087` 与一份 1909 年的周刊上，**三份不是同一部作品**。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
try:
    import check_quote_integrity as _QI
except Exception as exc:                      # pragma: no cover
    raise SystemExit(
        "本件必须与 check_quote_integrity.py 同目录：引号形态、投影、长 s 折叠、"
        "MIN 全部复用它的定义，**不许在这里另写一套**。导入失败：%r" % (exc,))

# ★★★★ **第一版我只认 markdown 反引号**，于是全库 27 个工作区里
#   Koch(46 条断言)／Lister(35)／Blackwell(34)／Virchow(60) 等一律报「长引文 0 条 ✓」——
#   而它们的引文用的是「」和 «»。**判据的覆盖面比数据窄，而它照样报绿。**
#   这正是 `check_quote_integrity` 自己的 Q 正则用四次事故换来的东西
#   （«» 漏 64%、反引号漏 16 条），**复用它，不许另写。**
Q = _QI.Q
SPLIT = _QI.SPLIT
MIN = _QI.MIN                # 投影后的最小长度，与引文完整性门同一档


def proj(s: str) -> str:
    """投影成只保留字母数字的小写串——直接复用引文完整性门的实现。"""
    return _QI.proj(s)


def fold_s(s: str) -> str:
    """长 s 折叠——同上，只容这一种字形差。"""
    return _QI.fold_s(s)


def quotes_of(claim: str) -> list[str]:
    """按 `check_quote_integrity` 的四类引号形态取引文，再按省略号切段。

    ★ 省略号两侧是两段独立的原文，**必须分开核**——
      合起来核会把「跨段拼接」当成一条连续引文放行。
    """
    segs: list[str] = []
    for m in Q.finditer(claim):
        for g in m.groups():
            if g:
                segs.extend(s for s in SPLIT.split(g) if s.strip())
                break
    return segs


try:
    import check_claim_source_independence as _SI
except Exception as exc:                      # pragma: no cover
    raise SystemExit(
        "本件要用 check_claim_source_independence 的作品分组来分辨"
        "「挂错作品」与「同一作品的另一版」，导入失败：%r" % (exc,))

# ★★★★ **分「挂错作品」与「版本差」，用的是规则不是阈值。**
#   第一版我拿「命中片段占比 ≥40%」去分类，**在真数据上立刻分错**：
#   Osler 那句 imperturbability **确实在 1904 ed1 里**，只是 ed1 的 OCR 烂成
#   `Imperturba! coolness and presence of mind under all d calmness`，
#   占比只有 26% → 被我的阈值判成「挂错作品」。
#   **占比低是因为 OCR 烂，不是因为挂错了。**
#   改用本项目已有的作品分组（8 词片重叠 ≥30%）：
#   所引源与真实出处**同组** → 同一部作品的另一版；**不同组** → 真的挂到了别的作品上。
#   [[gate-below-instrument-noise]] 的同族：**能写成规则就别写成阈值。**


def longest_fragment(pq: str, texts) -> int:
    """投影后的引文 `pq`，在 `texts` 里能连续命中的最长片段长度。

    ★ **不要用 `difflib.SequenceMatcher`**：它默认 `autojunk=True`，
      把出现率 >1% 的字符当垃圾；投影串只有小写字母，于是**每个字母都成了垃圾**，
      在 656 KB 的 Osler ed1 上返回「最长公共片段 = 2」——一个完全错的数。
      这里逐起点二分，慢一点但没有隐含假设。
    """
    best = 0
    for i in range(len(pq)):
        if len(pq) - i <= best:
            break
        lo, hi = best, len(pq) - i
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if any(pq[i:i + mid] in t for t in texts):
                lo = mid
            else:
                hi = mid - 1
        best = max(best, lo)
    return best


def load_corpus(ws: pathlib.Path) -> dict[str, str]:
    raw = ws / "raw"
    out: dict[str, str] = {}
    if not raw.is_dir():
        return out
    for p in raw.rglob("*"):
        if p.is_file():
            out[p.name] = re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="replace"))
    return out


def resolve(ledger: dict, corpus: dict[str, str], sid: str) -> tuple[str | None, str | None]:
    rec = ledger.get(sid)
    if not rec:
        return None, None
    name = pathlib.Path(rec.get("local_path") or "").name
    if name and name in corpus:
        return name, corpus[name]
    stem = pathlib.Path(rec.get("local_path") or "").stem[:30]
    if stem:
        for k in corpus:
            if k.startswith(stem):
                return k, corpus[k]
    return None, None


def scan(ws: pathlib.Path) -> dict:
    ws = ws.expanduser().resolve()
    corpus = load_corpus(ws)
    projected = {k: fold_s(proj(v)) for k, v in corpus.items()}
    lf = ws / "evidence" / "source-ledger.jsonl"
    cf = ws / "evidence" / "claims.jsonl"
    if not (lf.is_file() and cf.is_file()):
        # ★ 早退分支的键必须与正常分支**完全一致**——第一版少了「不唯一」，
        #   下游一取就 KeyError。**「未核验」和「通过」的形状要一样，差别只在 `状态` 字段。**
        return {"状态": "claims.jsonl 或 source-ledger.jsonl 不在，**未核验**（不是通过）",
                "错挂": [], "不唯一": [], "引文数": 0, "取不到正文的源": 0,
                "语料份数": len(corpus)}

    ledger = {}
    for line in lf.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            ledger[r.get("source_id")] = r

    # 作品分组：8 词片重叠 ≥30% 的并进一组（复用来源独立性门的并查集）
    works = _SI.group_works(corpus)

    bad, ambiguous, total, unresolved = [], [], 0, 0
    for idx, line in enumerate(cf.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        c = json.loads(line)
        own: dict[str, str] = {}
        for sid in c.get("source_ids") or []:
            name, _ = resolve(ledger, corpus, sid)
            if name is None:
                unresolved += 1
            else:
                own[name] = projected[name]
        for q in quotes_of(c.get("claim") or ""):
            pq = fold_s(proj(q))
            if len(pq) < MIN:
                continue
            total += 1
            where = [n for n, t in projected.items() if pq in t]
            record = {
                "断言序号": idx,
                "claim_id": c.get("claim_id"),
                "引文": re.sub(r"\s+", " ", q).strip()[:120],
                "它引的源": sorted(own),
                "真实出处": sorted(where),
            }
            if not any(pq in t for t in own.values()):
                if where:                      # 全语料都没有 → check_quote_integrity 的事
                    # ★★★★ **「不在它引的源里」有两种，后果完全不同，不许混成一个数**：
                    #   ① 挂错了作品——所引源里连片段都找不到，读者去查会一无所获；
                    #   ② 挂对了作品，但**逐字文本是从另一个版本抄的**——
                    #      Osler #110 实测：1904 ed1 的 OCR 坏成
                    #      `Imperturba! coolness and presence of mind under all d calmness`，
                    #      而断言引的是 1906 ed2 的干净文本却署 ed1。
                    #      **句子确实在 ed1 里，但那段「逐字」不是 ed1 的字。**
                    frag = longest_fragment(pq, list(own.values())) if own else 0
                    record["最长命中片段"] = frag
                    record["片段占比"] = round(frag / len(pq), 3)   # 只作线索，不作分类依据
                    cited_g = {works.get(n) for n in own}
                    real_g = {works.get(n) for n in where}
                    same = bool(cited_g & real_g)
                    record["同一作品组"] = same
                    record["判读"] = ("版本差：作品挂对了，**但这段逐字文本是另一版的字**"
                                      if same else
                                      "**挂错作品**：真实出处与所引源不是同一部作品")
                    bad.append(record)
                continue
            if len(where) > 1:
                # **挂对了，但这句话不止一份源含它**——重印／改订本／文集重复收录。
                # 挂错了也照样绿，所以要把这种「引文不足以唯一定位来源」的情况说出来。
                ambiguous.append(record)
    return {"引文数": total, "错挂": bad, "不唯一": ambiguous,
            "取不到正文的源": unresolved, "语料份数": len(corpus)}


SELF_TESTS = """正例：引文出自它引的那份源 → 不报
反例①：引文挂到了另一份也含这句话的源 → 报出，并打印真实出处
反例②：引文全语料都找不到 → **本件不报**（射程外，归 check_quote_integrity）
反例③：投影后短于 MIN 的串 → 不当引文核
反例④：挂对了但同句见于多份源 → 报「不唯一」警告，且**不算错挂**
反例⑤：同句只见于一份源 → **不许**报不唯一（负对照的负对照）
反例⑥：source_id 的 local_path 指不到文件 → 计数并打印，不静默
反例⑦：「」/ 弯引号 / «» / ‹› 四种非反引号形态各挂错一次 → **四种都要抓**
        （**只认反引号的第一版在这四条上全部静默报绿**）
反例⑧：同一部作品的另一版（同组）→ 判「版本差」，**不许**判成「挂错作品」
        （拿「片段占比 ≥40%」当分类依据的那一版在 Osler 真数据上分错，占比低是 OCR 烂）"""


def self_test() -> int:
    import tempfile
    bad = []

    def chk(cond: str, got, want):
        if got != want:
            bad.append(f"{cond}: 得到 {got!r}，应为 {want!r}")

    with tempfile.TemporaryDirectory() as td:
        ws = pathlib.Path(td)
        (ws / "raw").mkdir()
        (ws / "evidence").mkdir()
        # A 与 B 都含同一句话（模拟论文与它的重印本）；C 只有自己的话。
        # ★★ **夹具必须够厚**：作品分组用 8 词片重叠 ≥30%，
        #   第一版我拿三句话当夹具，论文与重印本压根分不进同一组，
        #   于是「版本差」那条自测恒错。**夹具比真东西薄，等于没测。**
        #   [[fixtures-cleaner-than-the-real-thing]]
        shared = "Habits of industry are far more valuable than any kind of knowledge or skill."
        body = " ".join(
            f"paragraph {i} discusses the bonus system and the instruction card in detail "
            f"with reference to the machine shop and the workman and his day rate"
            for i in range(40))
        (ws / "raw" / "paper.txt").write_text("preamble " + shared + " " + body + " tail",
                                              encoding="utf-8")
        (ws / "raw" / "book.txt").write_text("front " + shared + " " + body + " back",
                                             encoding="utf-8")
        (ws / "raw" / "other.txt").write_text(
            "a wholly different sentence about castings " + " ".join(
                f"section {i} concerns steel castings moulding sand and the cupola furnace"
                for i in range(40)), encoding="utf-8")
        (ws / "evidence" / "source-ledger.jsonl").write_text("\n".join(json.dumps(r) for r in [
            {"source_id": "src-paper", "local_path": "raw/paper.txt"},
            {"source_id": "src-book", "local_path": "raw/book.txt"},
            {"source_id": "src-other", "local_path": "raw/other.txt"},
        ]), encoding="utf-8")

        def claims(*rows):
            (ws / "evidence" / "claims.jsonl").write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")

        # 正例
        claims({"claim_id": "clm-1", "claim": f"论文里写 `{shared}`", "source_ids": ["src-paper"]})
        chk("正例：挂对了源", len(scan(ws)["错挂"]), 0)

        # 反例① —— 挂到 other，而句子其实在 paper/book
        claims({"claim_id": "clm-2", "claim": f"他写过 `{shared}`", "source_ids": ["src-other"]})
        r = scan(ws)
        chk("反例①：报出条数", len(r["错挂"]), 1)
        chk("反例①：打印真实出处", r["错挂"][0]["真实出处"] if r["错挂"] else None,
            ["book.txt", "paper.txt"])
        # ★ other.txt 与 paper/book 不是同一部作品 → 必须判「挂错作品」
        chk("反例①：判读为挂错作品",
            r["错挂"][0]["同一作品组"] if r["错挂"] else None, False)

        # ★★★★ 反例⑧：**同一部作品的另一版**——paper 与 book 共享大段文本（同组），
        #   而 book 里那句被「OCR 弄坏」，断言引 book 却写着 paper 的干净字。
        #   **这必须判成「版本差」，不能判成「挂错作品」**——
        #   两者后果完全不同：一个是引文该重抄，一个是整条断言的出处是错的。
        (ws / "raw" / "book.txt").write_text(
            "front " + shared.replace("valuable", "valuahle") + " " + body + " back",
            encoding="utf-8")
        claims({"claim_id": "clm-10", "claim": f"书里写 `{shared}`", "source_ids": ["src-book"]})
        r = scan(ws)
        chk("反例⑧：报出条数", len(r["错挂"]), 1)
        chk("反例⑧：判读为版本差（同组）",
            r["错挂"][0]["同一作品组"] if r["错挂"] else None, True)
        (ws / "raw" / "book.txt").write_text("front " + shared + " " + body + " back",
                                             encoding="utf-8")

        # 反例② —— 全语料都没有 → 本件不报
        claims({"claim_id": "clm-3",
                "claim": "他写过 `a sentence that appears in no source whatsoever at all`",
                "source_ids": ["src-paper"]})
        chk("反例②：射程外不报", len(scan(ws)["错挂"]), 0)

        # 反例③ —— 短串不当引文
        claims({"claim_id": "clm-4", "claim": "字段名是 `Habits of industry`",
                "source_ids": ["src-other"]})
        r = scan(ws)
        chk("反例③：短串不计入", r["引文数"], 0)
        chk("反例③：短串不报", len(r["错挂"]), 0)

        # 多源：只要有一份含就算过
        claims({"claim_id": "clm-5", "claim": f"他写过 `{shared}`",
                "source_ids": ["src-other", "src-book"]})
        chk("多源：一份含即过", len(scan(ws)["错挂"]), 0)

        # ★★ 「不唯一」这一档：挂对了，但 paper 与 book 都含这句话
        claims({"claim_id": "clm-7", "claim": f"论文里写 `{shared}`", "source_ids": ["src-paper"]})
        r = scan(ws)
        chk("不唯一：报警告", len(r["不唯一"]), 1)
        chk("不唯一：不算错挂", len(r["错挂"]), 0)
        chk("不唯一：列出同句还见于何处",
            r["不唯一"][0]["真实出处"] if r["不唯一"] else None, ["book.txt", "paper.txt"])

        # ★ 负对照的负对照：只有一份源含这句话时，**不许**报「不唯一」
        uniq = "a wholly different sentence about castings"
        claims({"claim_id": "clm-8", "claim": f"他写过 `{uniq}`", "source_ids": ["src-other"]})
        r = scan(ws)
        chk("唯一时不报不唯一", len(r["不唯一"]), 0)
        chk("唯一时也不报错挂", len(r["错挂"]), 0)

        # 取不到正文的源要计数，不能静默
        claims({"claim_id": "clm-6", "claim": f"他写过 `{shared}`",
                "source_ids": ["src-missing"]})
        chk("取不到正文的源要计数", scan(ws)["取不到正文的源"], 1)

        # ★★★★ 反例⑦：**只认反引号的那一版会在这里静默报绿。**
        #   四类引号形态（「」/ "" / «» / ‹›）逐一挂到不含它的源上，都必须报出。
        for tag, (lq, rq) in {"「」": ("「", "」"), "英文弯引号": ("“", "”"),
                              "«»": ("«", "»"), "‹›": ("‹", "›")}.items():
            claims({"claim_id": "clm-9", "claim": f"他写过 {lq}{shared}{rq}",
                    "source_ids": ["src-other"]})
            chk(f"反例⑦（{tag}）：非反引号形态也要抓", len(scan(ws)["错挂"]), 1)

    print(SELF_TESTS)
    for b in bad:
        print("  ✗", b)
    print(("  ✗ 自测 %d 条不过" % len(bad)) if bad else "  ✓ 自测全过（正例 3、反例 13）")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workspace", nargs="?", type=pathlib.Path)
    ap.add_argument("--workspace", dest="ws_kw", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    ws = a.ws_kw or a.workspace
    if ws is None:
        ap.error("要给 workspace")
    r = scan(ws)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 1 if r.get("错挂") else 0
    if "状态" in r:
        print(" ", r["状态"])
        return 0
    print("语料 %d 份；长逐字引文 %d 条（投影后 ≥%d 字符）"
          % (r["语料份数"], r["引文数"], MIN))
    if r["取不到正文的源"]:
        print("  ★ 有 %d 个 source_id 的 local_path 指不到文件，**本件没核过它们**"
              % r["取不到正文的源"])
    if r["不唯一"]:
        print("  ⚠ **%d 条引文不止一份源含它**（重印／改订本），"
              "**挂错了源也照样绿——本件在这些条上给不出保证**：" % len(r["不唯一"]))
        for b in r["不唯一"]:
            print(f"      第 {b['断言序号']} 条 挂 {b['它引的源']}｜同句还见于 {b['真实出处']}")
    if not r["错挂"]:
        print("  ✓ 每条引文都出自它自己引的源")
        return 0
    print("  ✗ **%d 条引文不在它自己引的源里**（但在语料里——所以引文门是绿的）" % len(r["错挂"]))
    for b in r["错挂"]:
        print(f"\n    第 {b['断言序号']} 条 {b['claim_id']}")
        print(f"      引文  「{b['引文']}」")
        print(f"      它引的源  {b['它引的源']}")
        print(f"      真实出处  {b['真实出处']}")
        print(f"      判读      {b.get('判读','')}"
              f"（所引源里最长命中片段 {b.get('最长命中片段',0)}/{b.get('片段占比',0):.0%}）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
