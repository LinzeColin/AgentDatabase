#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐字引文核查（文档层 + 用例层）—— `check_quote_integrity.py` 的姊妹件。

`check_quote_integrity.py` 只扫 `evidence/claims.jsonl`。
而**渲染文档、身份分面、评测用例里的引文一样会伪造**，此前没有常规检查，
每个人物都在临时写脚本——Robertson #97 临时写的那版还把判据的维度选错了两次。

## 判据：引号内**没有汉字**才当逐字英文引文核

先后错过两版，记在这里免得再错：

1. 「含 ≥4 个连续拉丁字母」→ 把「Tiger 由他与 Thorpe McKenzie 共同创立」
   这种中文强调句误判为英文引文（专名里有拉丁字母）。
2. 「拉丁字符占比 ≥60%」→ **仍然误判**，因为专名把一个短中文句撑到了 73%。

**一段逐字英文引文里不会出现汉字。** 这才是干净的维度。
（RUNBOOK 第六十种附记：判据连续误报两次以上，停止调参数，换维度。）

用法：
    python3 check_verbatim_quotes.py --workspace <target> --cache <corpus dir> \
        [--extra judge_payload_x.json ...]
"""
import argparse, json, pathlib, re, sys

CJK = re.compile(r"[\u4e00-\u9fff]")
QUOTE = re.compile(r"\u300c([^\u300d]{16,})\u300d")
LAT = re.compile(r"[A-Za-z]{4}")
NORM = re.compile(r"[^a-z0-9]+")


def norm(s: str) -> str:
    return NORM.sub("", s.lower())


def verbatim(q: str) -> bool:
    """逐字英文引文 = 引号内无汉字，且确实含英文词。"""
    return not CJK.search(q) and bool(LAT.search(q))


def collect(ws: pathlib.Path, extra: list) -> list:
    out = []
    for f in sorted(list(ws.glob("*.md")) + list(ws.glob("identity-facets/*.md"))
                    + list(ws.glob("references/research/*.md"))):
        for q in QUOTE.findall(f.read_text(encoding="utf-8")):
            if verbatim(q):
                out.append((f.name, q))
    for p in extra:
        try:
            data = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        rows = data if isinstance(data, list) else [data]
        for r in rows:
            for key in ("candidate", "rubric", "prompt"):
                for q in QUOTE.findall(str(r.get(key, ""))):
                    if verbatim(q):
                        out.append((f"{pathlib.Path(p).name}:{r.get('case_id', key)}", q))
    return out


# ── 负对照（v0.0.0.13 补）──────────────────────────────────────────────
# 本件是**硬门**，却一直没有负对照——`check_checkers.py` 首跑就把它点了出来。
# RUNBOOK 第十八种：**没有负对照的检查器，其「全绿」不构成任何证据。**
#
# ★ 负对照必须包含**它历史上真实错过的那两版误判形态**（见文件头判据一节），
#   而不只是我此刻想得到的形态。上一版（元检查器）刚因为「样本没覆盖真实形态」
#   而误判了 6 件检查器，同样的错不该在下一件上再犯一次。
SELFTEST_CORPUS = (
    "I have always believed that the best investments are the ones you "
    "understand deeply. Tiger was founded with eight million dollars.\n")
SELFTEST_DOC = """# 自测文档

他说：「I have always believed that the best investments are the ones you understand deeply.」

改了一个词的伪造引文：「I have never believed that the best investments are the ones you understand deeply.」

整句杜撰：「This sentence was never spoken by anyone anywhere in the corpus.」

中文强调句（含拉丁专名，**不是**英文引文）：「Tiger 由他与 Thorpe McKenzie 共同创立」

拉丁占比很高的短中文句（**仍然不是**英文引文）：「Alpha 与 Beta 的 Sharpe ratio 都不算高」
"""


def self_test() -> int:
    import tempfile
    bad_cases = []
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        ws, cache = root / "ws", root / "cache"
        ws.mkdir(); cache.mkdir()
        (ws / "persona.md").write_text(SELFTEST_DOC, encoding="utf-8")
        (cache / "corpus.txt").write_text(SELFTEST_CORPUS, encoding="utf-8")

        corpus = norm((cache / "corpus.txt").read_text(encoding="utf-8"))
        found = collect(ws, [])
        texts = [q for _, q in found]
        missed = [q for q in texts if norm(q) not in corpus]

        checks = [
            ("真引文被认出且命中语料",
             any(q.startswith("I have always believed") for q in texts)
             and all(norm(q) in corpus for q in texts if q.startswith("I have always"))),
            ("改一个词的伪造引文被抓",
             any(q.startswith("I have never believed") for q in missed)),
            ("整句杜撰被抓",
             any(q.startswith("This sentence was never") for q in missed)),
            # ↓ 两条误判形态：这才是它真正栽过的地方
            ("中文强调句未被当成英文引文（专名含拉丁字母）",
             not any("共同创立" in q for q in texts)),
            ("拉丁占比高的短中文句未被当成英文引文",
             not any("都不算高" in q for q in texts)),
            ("逐字英文引文恰好 3 条", len(texts) == 3),
            ("未命中恰好 2 条", len(missed) == 2),
        ]
    for label, ok in checks:
        print(f"  {'✓' if ok else '✗'} {label}")
        if not ok:
            bad_cases.append(label)
    if bad_cases:
        print("\n负对照未过：")
        for b in bad_cases:
            print(f"  · {b}")
        return 2
    print(f"\n负对照通过（{len(checks)} 项：3 正 + 2 伪造 + 2 误判形态）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    # ★ 不再 required —— 负对照必须能**独立跑**。
    #   `--self-test` 却要求 `--workspace/--cache`，等于负对照依赖它本该独立于的数据；
    #   `check_checkers.py` 把这种形态单列为 NOT-STANDALONE，因为它实际上从没被跑过。
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--cache", nargs="+", type=pathlib.Path)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--self-test", action="store_true", help="只跑内置双向负对照")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace or not a.cache:
        ap.error("需要 --workspace 与 --cache（或只给 --self-test）")
    corpus = "\n".join(norm(p.read_text(encoding="utf-8", errors="replace"))
                       for d in a.cache for p in d.rglob("*.txt"))
    qs = collect(a.workspace, a.extra)
    bad = [(w, q) for w, q in qs if norm(q) not in corpus]
    print(f"逐字英文引文 {len(qs)} 条（判据：引号内无汉字），未命中 {len(bad)}")
    for w, q in bad:
        print(f"   \u2717 {w}: {q[:100]}")
    if not bad:
        print("   \u2713 全部可在语料中找到")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
