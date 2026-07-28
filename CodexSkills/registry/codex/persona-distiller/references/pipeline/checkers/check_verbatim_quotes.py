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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path, required=True)
    ap.add_argument("--cache", nargs="+", type=pathlib.Path, required=True)
    ap.add_argument("--extra", nargs="*", default=[])
    a = ap.parse_args()
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
