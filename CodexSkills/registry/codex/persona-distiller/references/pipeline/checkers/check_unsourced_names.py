#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**答案里的人名，回语料查它有没有依据。**

## 为什么有这道判据

Osler #110 第 2 轮，我在一条答案里写了「第 9 版起是 Thomas McCrae 续修，**后来是
Henry A. Christian**」。McCrae 有依据——第 8、9 版扉页印着他的名字。**Christian 没有。**
回语料查：这个名字在 104 份材料里只出现 1 次，在 Cushing 那部**后世传记**（S2）里，
说的还是他当院长，**跟续修那套书毫无关系**。那半句是我编的。

两位评委三轮六次评审，**没有一次抓到它**——他们手上没有语料，抓不了。
席位 E 只能说「这是全题唯一无扉页依据的名字」，靠的是同题内的对比，不是核查。
**这件事只有能读语料的判据能做。**（与 check_quote_integrity 同一道理：
评委验不了引文，一行 grep 全抓得出。）

## 它判什么

对答案里出现的每个拉丁人名，报三个数：**P1 命中 / P2 命中 / S1·S2 命中**。

- **P1 命中 0 且总命中 0** → `✗ 判为无依据`。这是编造的形状。
- **P1 命中 0，但 S1/S2 或排除记录里有** → `⚠ 只列不判`。
  二手依据不是没依据，但**用它撑承重句之前要自己知道它是二手的**。
  （Curschmann 就是这一类：他那本书按归属被排除、不在 raw/ 里，
  依据在 `_EXCLUDED.txt` 的扉页转录中。**排除记录也是记录。**）
- **P1 命中 ≥1** → 过。

## 它判不了什么（说在前面，免得下次拿它当挡箭牌）

- **命中不等于说的是同一件事。** Christian 若被写成「他当过哈佛医学院院长」，
  这道判据会放行——语料里确实有这句。**它查的是「这个名字有没有依据」，
  不是「你挂在这名字上的那句话有没有依据」。**后者只有人能判。
- **中文人名、只在正文提及而不在扉页的人**，都可能被误报。看 ⚠ 那一档，别当硬错。
"""
import argparse
import collections
import json
import pathlib
import re
import sys

# **先剥掉引文区再抽名**——否则整段英文原文会被当成一串人名。
# 引文只会出现在这四种壳里：`「…」` / 反引号 / `> ` 行 / `《…》`。
QUOTED = re.compile(r"「[^」]*」|`[^`]*`|《[^》]*》|^>.*$", re.M)

# 词内大写是人名的常态（`McCrae`、`MacLeod`、`O'Brien`），
# 第一版写成 `[A-Z][a-z]{1,15}` 结果 `Thomas McCrae` 一个都抓不到——自测抓出来的。
_TOK = r"[A-Z][a-zA-Z'’]{1,15}"
NAME = re.compile(
    rf"\b({_TOK}(?:\s+(?:[A-Z]\.|{_TOK}|van|von|de|du|della|del)){{0,3}})\b")

# 机构、地名、扉页套话——大写但不是人。**判据抓错人比抓不到更坏**（会逼作者删掉真依据）。
NOT_A_NAME = {
    "The", "Late", "Regius", "Professor", "Medicine", "Oxford", "Hospital",
    "University", "Company", "Press", "Edition", "Impression", "Series",
    "Address", "Students", "Sunday", "April", "October", "March", "August",
    "The Late", "Late Regius", "Regius Professor", "New York", "Johns Hopkins",
    "Johns Hopkins Hospital", "Johns Hopkins University", "United States",
    "Great Britain", "Modern Medicine", "Typhoid Fever", "Typhus Fever",
    "Normal Histology", "Eminent Authorities", "Class Use", "Laboratory And",
    "Blakiston", "The Blakiston",
    "Blakiston Company", "The Blakiston Company", "Oxford University",
    "University Press", "McGill", "Yale", "Harvard", "London", "Philadelphia",
    "Montreal", "Baltimore", "Edinburgh",
}


def load_corpus(cache: pathlib.Path) -> tuple:
    """→ (语料, 项目台账合并文本)。**递归**——v0.0.0.38 两道判据都因非递归 glob 把 61 份读成 0 份。

    **`_` 开头的文件是我自己写的台账，不是语料。**
    第一版把 `raw/_EXCLUDED.txt` 与 `raw/_ids.txt` 一并读进来，
    于是「我在台账里写过这个名字」被算成「语料里有这个名字」——
    **判据拿作者自己的笔记当证据，等于没判。**
    它们仍要读，但归到「项目记录」那一档（二手），不进一手。
    """
    corpus, notes = {}, []
    for p in sorted(cache.rglob("*.txt")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if p.name.startswith("_"):
            notes.append(text)
        else:
            corpus[p] = text
    return corpus, "\n".join(notes)


def tier_of(path: pathlib.Path, ledger: dict) -> str:
    """按账本给这份语料定档；账本里查不到的按文件名前缀兜底。

    **兜底档写作 `未定档`，不写 `P1?`。**
    第一版写 `P1?`，而分档那行判的是 `t.startswith("P1")`——
    **于是「我不知道这是什么」被当成了「这是一手材料」。**
    定不了档就该往严处落，不是往宽处落。
    """
    for key in (path.name, path.stem, path.parent.name):
        if key in ledger:
            return ledger[key]
    n = path.stem
    if n.startswith("s1-"):
        return "S1"
    if n.startswith("s2-"):
        return "S2"
    return "未定档"


def read_ledger(led: pathlib.Path) -> dict:
    """source-ledger.jsonl → {原名: tier}。读不到就返回空，由文件名兜底。"""
    out = {}
    if not led or not led.is_file():
        return out
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("tier") or ""
        for key in (d.get("original_name"), d.get("local_path")):
            if key:
                stem = pathlib.Path(key).stem
                out[stem] = t
                out[pathlib.Path(key).name] = t
    return out


def extract_names(answers: dict) -> dict:
    """{人名: [出现的 case_id]}。同一答案里重复出现只记一次。

    **先把引文区整段挖空**，只在中文行文里抽名——
    否则 `no quality takes rank with imperturbability` 会被拆成一串「人名」。
    """
    found = collections.defaultdict(list)
    for cid, text in answers.items():
        prose = QUOTED.sub(" ", text)
        for m in NAME.finditer(prose):
            name = re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".")
            if name in NOT_A_NAME or len(name) < 5:
                continue
            # 单个词的，得像姓：至少 5 个字母，且不是常见英文实词
            if " " not in name and name.lower() in _COMMON_WORDS:
                continue
            if cid not in found[name]:
                found[name].append(cid)
    return dict(found)


# 单词形只在「像姓氏」时才收。这些是会漏进中文行文的普通英文词。
_COMMON_WORDS = {
    "author", "authors", "edited", "edition", "editor", "medicine", "practice",
    "principles", "system", "modern", "original", "contributions", "american",
    "foreign", "normal", "histology", "laboratory", "class", "eminent",
    "authorities", "assistance", "revised", "ninth", "eighth", "professor",
    "hospital", "university", "company", "students", "address", "sunday",
}


def _tally(pat, corpus: dict, ledger: dict, extra: str) -> dict:
    c = collections.Counter()
    for p, text in corpus.items():
        n = len(pat.findall(text))
        if n:
            t = tier_of(p, ledger)
            c[t if t in ("P1", "P2", "S1", "S2") else "未定档"] += n
    c["项目记录"] = len(pat.findall(extra))
    return dict(c)


def count_hits(name: str, corpus: dict, ledger: dict, extra: str) -> tuple:
    """回 (全名命中, 姓氏命中)。

    **必须分开数。** 第一版只数姓氏，结果 `Henry A. Christian` 报成「有 P1 依据」——
    因为 `Christian` 是个常见英文词，随便哪份维多利亚时代的书里都有。
    **判据绿了，指的却是别的东西。**（本会话第七次同型。）
    姓氏一路仍要留：扉页常只印 `McCRAE`，全名反而不出现——但它只算**弱**证据。
    """
    parts = name.split()
    full = re.compile(r"(?i)" + r"\s+".join(re.escape(w) for w in parts))
    sur = re.compile(r"(?i)\b" + re.escape(parts[-1].rstrip(".")) + r"\b")
    return _tally(full, corpus, ledger, extra), _tally(sur, corpus, ledger, extra)


def run(answers: dict, corpus: dict, ledger: dict, extra: str) -> tuple:
    """→ (判为无依据, 只列不判, 有 P1 全名依据)"""
    names = extract_names(answers)
    bad, soft, ok = [], [], []
    for name, cids in sorted(names.items()):
        hf, hs = count_hits(name, corpus, ledger, extra)
        anywhere = sum(hf.values())
        row = (name, cids, hf, hs)
        if hf.get("P1", 0):
            ok.append(row)                    # 全名就在 P1 里 → 过
        elif anywhere or sum(hs.values()):
            soft.append(row)                  # 只有二手／只有姓氏 → 只列不判
        else:
            bad.append(row)                   # 哪儿都查不到 → 判
    return bad, soft, ok


# ══════════════════ 自测 ══════════════════
# 反向对照是这套判据的硬要求：**只证明「它抓得到」不算过，还要证明「它不乱抓」。**

_FIX_CORPUS = {
    "p1-titlepage.txt": (
        "THE PRINCIPLES AND PRACTICE OF MEDICINE\n"
        "BY WILLIAM OSLER, M.D.\n"
        "EIGHTH EDITION - WITH THE ASSISTANCE OF THOMAS McCRAE, M.D.\n"),
    "s2-biography.txt": (
        "to an alumni gathering which the new Dean of the school,\n"
        "Henry A. Christian, one of his old pupils, had invited him\n"),
}
_FIX_LEDGER = {"p1-titlepage": "P1", "s2-biography": "S2"}
_FIX_EXCLUDED = (
    "cihm_990060\t`Typhoid Fever and Typhus Fever` - title leaf reads "
    "\"BY DR. H. CURSCHMANN, Professor of Medicine, Leipzig\"\tR5-attribution\n")


def selftest() -> int:
    corpus = {pathlib.Path(k): v for k, v in _FIX_CORPUS.items()}
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：抓得到该抓的 ──")
    bad, soft, ok = run(
        {"a": "第 9 版起是 Thomas McCrae 续修，后来是 Henry A. Christian。"},
        corpus, _FIX_LEDGER, "")
    names_soft = [r[0] for r in soft]
    names_ok = [r[0] for r in ok]
    chk("McCrae 在 P1 扉页里 → 过", any("McCrae" in n for n in names_ok))
    chk("Christian 只在 S2 传记里 → ⚠ 只列不判", any("Christian" in n for n in names_soft))

    print("── 正向：完全查无此人 → 判 ──")
    bad, soft, ok = run({"a": "后来交给 Reginald Fitzhugh 续修。"},
                        corpus, _FIX_LEDGER, "")
    chk("语料与排除记录里都没有 → ✗ 判为无依据",
        any("Fitzhugh" in r[0] for r in bad))

    print("── 反向对照 ①：排除记录也是记录，不许判成编造 ──")
    bad, soft, ok = run({"a": "《Typhoid Fever》正文是 Curschmann 的。"},
                        corpus, _FIX_LEDGER, _FIX_EXCLUDED)
    chk("Curschmann 依据在排除记录里 → ⚠ 而非 ✗",
        any("Curschmann" in r[0] for r in soft)
        and not any("Curschmann" in r[0] for r in bad))

    print("── 反向对照 ②：机构名、书名不许当人名抓 ──")
    bad, soft, ok = run(
        {"a": "扉页写着 Johns Hopkins Hospital，书名是 Modern Medicine，"
              "印所 The Blakiston Company。"},
        corpus, _FIX_LEDGER, "")
    allrows = bad + soft + ok
    chk("Johns Hopkins / Modern Medicine / Blakiston 一个都不报",
        not allrows)

    print("── 反向对照 ③：只印姓的扉页，全名也要算有依据 ──")
    bad, soft, ok = run({"a": "第 8 版由 Thomas McCrae 协助。"},
                        corpus, _FIX_LEDGER, "")
    chk("语料只有 `THOMAS McCRAE` 大写形 → 仍判为 P1 有依据",
        any("McCrae" in r[0] for r in ok))

    print("── 反向对照 ④：语料读不到时不许报「全是编造」 ──")
    bad, soft, ok = run({"a": "Thomas McCrae 与 Henry A. Christian。"}, {}, {}, "")
    chk("空语料 → 由调用方按 exit 3 处理，判据本身不吞掉这一层",
        len(bad) == 2)

    print("── 反向对照 ⑤：姓氏是常见英文词时，不许把它算成依据 ──")
    # `Christian` 在维多利亚时代的书里满地都是；第一版就是栽在这儿报了绿。
    corpus2 = dict(corpus)
    corpus2[pathlib.Path("p1-prose.txt")] = (
        "the Christian era, his Christian name, and a Christian burial\n")
    ledger2 = dict(_FIX_LEDGER, **{"p1-prose": "P1"})
    bad, soft, ok = run({"a": "后来是 Henry A. Christian。"}, corpus2, ledger2, "")
    hit = [r for r in soft if "Christian" in r[0]]
    chk("姓氏在 P1 里撞了 3 次，但全名只在 S2 → 仍归 ⚠，不许进 ✓",
        bool(hit) and not any("Christian" in r[0] for r in ok))
    chk("并且报告要能看出「全名 0 次、姓氏 N 次」这个差别",
        bool(hit) and hit[0][2].get("P1", 0) == 0 and hit[0][3].get("P1", 0) == 3)

    print("── 反向对照 ⑥：作者自己的台账不许当语料 ──")
    # 第一版把 `raw/_EXCLUDED.txt`、`raw/_ids.txt` 读成语料，
    # 于是「我在台账里写过这名字」= 「语料里有这名字」。**判据拿我的笔记当证据。**
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "sub").mkdir()
        (root / "sub" / "p1-real.txt").write_text("BY WILLIAM OSLER, M.D.\n", encoding="utf-8")
        (root / "_ids.txt").write_text("x\tHenry A. Christian 续修\ty\n", encoding="utf-8")
        corp, notes = load_corpus(root)
        chk("`_ids.txt` 不进语料", len(corp) == 1)
        chk("但它仍被读进「项目记录」，不是丢掉", "Christian" in notes)
        bad, soft, ok = run({"a": "后来是 Henry A. Christian。"}, corp, {}, notes)
        chk("台账里有 → ⚠ 只列不判，**不许算 ✓ 一手**",
            any("Christian" in r[0] for r in soft)
            and not any("Christian" in r[0] for r in ok))

    print("── 反向对照 ⑦：定不了档的材料不许算成一手 ──")
    # 第一版兜底档写 `P1?`，而分档判的是 `startswith("P1")`——
    # **「我不知道这是什么」被当成了「这是一手材料」。**
    unknown = {pathlib.Path("mystery.txt"): "Henry A. Christian was here\n"}
    bad, soft, ok = run({"a": "后来是 Henry A. Christian。"}, unknown, {}, "")
    chk("账本查不到、文件名也认不出 → 归「未定档」，落 ⚠ 不落 ✓",
        any("Christian" in r[0] for r in soft)
        and not any("Christian" in r[0] for r in ok))

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", help="{case_id: 答案文本} 的 JSON")
    ap.add_argument("--cache", help="语料目录（递归读 *.txt）")
    ap.add_argument("--ledger", help="source-ledger.jsonl，用于定档")
    ap.add_argument("--excluded", help="_EXCLUDED.txt 等项目记录，算作二手依据")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.answers or not a.cache:
        ap.error("要么 --self-test，要么同时给 --answers 与 --cache")

    answers = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    corpus, notes = load_corpus(pathlib.Path(a.cache))
    if not corpus:
        print(f"✗ **{a.cache} 下一份 .txt 都没读到——结果不可信，不是「没问题」**")
        return 3
    ledger = read_ledger(pathlib.Path(a.ledger) if a.ledger else None)
    extra = notes
    if a.excluded and pathlib.Path(a.excluded).is_file():
        extra += "\n" + pathlib.Path(a.excluded).read_text(encoding="utf-8", errors="replace")

    bad, soft, ok = run(answers, corpus, ledger, extra)
    print(f"语料 {len(corpus)} 份（`_` 开头的台账 {'有' if notes else '无'}，"
          "已归项目记录、不计一手）；"
          f"答案里的人名 {len(bad) + len(soft) + len(ok)} 个")

    if bad:
        print(f"\n✗ **无依据 {len(bad)} 个**——全名与姓氏在语料、排除记录里都查不到：")
        for name, cids, _, _ in bad:
            print(f"    **{name}**　出现在 {', '.join(cids)}")
    if soft:
        print(f"\n⚠ **{len(soft)} 个不是一手依据**（只列不判）——"
              "拿它撑承重句之前，先知道它薄在哪：")
        for name, cids, hf, hs in soft:
            wf = "、".join(f"{k} {v}" for k, v in sorted(hf.items()) if v) or "0"
            ws = "、".join(f"{k} {v}" for k, v in sorted(hs.items()) if v) or "0"
            print(f"    **{name}**　全名命中：{wf}　｜姓氏命中：{ws}　"
                  f"（{', '.join(cids)}）")
            if not sum(hf.values()):
                print("        ↳ **全名一次都没出现，上面那串是姓氏撞的**——"
                      "姓氏若是常见词，这一行等于没有证据。")
    if ok:
        print(f"\n✓ 全名在 P1 里 {len(ok)} 个：" + "、".join(r[0] for r in ok))
    if not bad:
        print("\n  ✓ 没有查无实据的人名")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
