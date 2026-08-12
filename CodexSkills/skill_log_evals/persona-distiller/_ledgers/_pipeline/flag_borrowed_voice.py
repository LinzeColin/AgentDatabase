#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flag_borrowed_voice.py —— 标记「这一句的第一人称可能不是本人」

## 为什么有这件工具

2026-08-12，第 1 批 10 人写研究道时，**同一个错误出现了 5 次、4 种机制**：

| 机制 | 实例 | 「我」实际是谁 |
|---|---|---|
| ① 传记转录传主书信 | Marshall《华盛顿传》 | **华盛顿** |
| ② 小说角色对白 | Pestalozzi《Lienhard und Gertrud》 | 他**虚构的人物** |
| ③ 校勘者／编者序言 | Kant 1867/1868/1889 编本 | **校订者** |
| ④ 图书馆数字化声明 | Jefferson 一份 P1 源 | **图书馆** |

★ Marshall 最严重：`writings` 道 **10 条候选 10 条**都是华盛顿的话，
而**三道现有的门（来源数／道数／一手占比）一道都不会因此变红**——
门数的是来源，不问那些第一人称属于谁。

## 本工具**不判断**

它只做一件事：**把可疑的理由连同原文证据一起打印出来**，由人判。
理由必须能在正文里指出位置——不打印「疑似对白」，只打印命中的那几个词和它的偏移。

## 用法

    python3 pull_quotes.py --raw R --ledger L --lane writings --lang de --first-person \\
      | python3 flag_borrowed_voice.py --raw R --ledger L

    python3 flag_borrowed_voice.py --self-test        # 正负对照，跑真语料

退出码：0＝没有「高」级标记；3＝有「高」级标记（需人判）；4＝读不到正文
"""
import argparse
import json
import pathlib
import re
import sys

WS = re.compile(r"\s+")

# ---- 前置引导语：「他在给某人的信里说」。英/德/法。
LEADIN = re.compile(
    r"(?:said|says|writes|wrote|observed|observes|remarked|remarks)\s+(?:he|she|the\s+\w+|Mr\.|Gen\.|Col\.)\b"
    r"|(?:he|she)\s+(?:writes|wrote|says|said|observes|remarks)\b"
    r"|in\s+a\s+letter\s+(?:to|of|from)\b"
    r"|schreibt\s+(?:er|sie)\b|(?:er|sie)\s+schreibt\b|in\s+einem\s+Briefe?\s+an\b"
    r"|écrit[- ]il\b|dans\s+une\s+lettre\s+à\b",
    re.I)

# ---- 对白：命中句之后紧跟「……回答道／说道」+ 人名；或之前是说话人标记行。
DIALOG_AFTER = re.compile(
    r"\b(?:erwiedert|erwiederte|erwidert|erwiderte|sagte|sagt|rief|sprach|antwortete|entgegnete|fragte)\s+[A-ZÄÖÜ]"
    r"|\b(?:replied|answered|rejoined|cried|exclaimed)\s+(?:he|she|[A-Z])")
# 说话人标记行：一个首字母大写的词 + 句点 + 空格，且该词像人名/身份而不是句子结尾
SPEAKER_LABEL = re.compile(r"(?:^|\.\s|\s)([A-ZÄÖÜ][a-zäöüßſ]{2,14})\.\s+(?=[A-ZÄÖÜ])")

# ---- 校勘者／编者：谈版本、比对、印本、本版说明。
EDITOR = re.compile(
    r"verglichen(?:en)?\s+(?:zwei\s+)?Exemplare|Vergleichung\s+des\s+Originaltextes|Separatausgabe"
    r"|Druckfehler|Herausgeber|herausgegeben\s+von|Vorrede\s+(?:des|zur)|dieser\s+Ausgabe"
    r"|meines\s+Erachtens"
    r"|the\s+(?:present\s+)?editor|in\s+this\s+edition|are\s+now\s+offered\s+.{0,30}to\s+the\s+public"
    r"|the\s+text\s+here\s+(?:printed|given)",
    re.I)

# ---- 数字化／馆藏声明：图书馆或扫描方**在说话**（不是扫描留下的水印）。
# ★ 变异测试查出的坑：第一版把 `Digitized by` / `Google Book` / `Internet Archive` 也算进来，
#   而那是**扫描水印**（实测：随机抽 40 份，3 份含 `Digitized by`，8%——
#   不是我原先以为的「每份都有」，但足以让 ④ 在不相干的地方放红）。
#   一条本该由 ①（传记引导语）判红的候选，拆掉 ① 之后**仍然红**：红得凑巧。
#   水印只说明这份文件被扫描过，不说明**这句话是图书馆说的**，已移出规则。
DIGITIZE = re.compile(
    r"domaine\s+public|Nous\s+encourageons|dans\s+le\s+domaine\s+public"
    r"|(?:is|are)\s+in\s+the\s+public\s+domain|copyright\s+(?:has\s+)?expired"
    r"|biblioth[eè]que\s+(?:nationale|numérique)|Sponsored\s+by",
    re.I)

# 序言区：正文开头这一段里的第一人称，默认可疑（多半是序、献词、编者说明）。
FRONT_MATTER_CHARS = 12000


def dehyphen(t: str) -> str:
    t = re.sub(r"(\w)[-‐‑]\s*\n\s*([a-z])", r"\1\2", t)
    return re.sub(r"(\w)[-‐‑]\s+([a-z])", r"\1\2", t)


def load_norm(raw: pathlib.Path, rec: dict):
    f = raw / pathlib.Path(rec["local_path"]).name
    if not f.exists():
        return None
    return WS.sub(" ", dehyphen(f.read_text(encoding="utf-8", errors="replace")))


def evidence(text: str, m: re.Match, pad: int = 34) -> str:
    """★ 打印证据必须打印**未截断**的命中片段本身。
    夹具比原文干净就等于没测——判据自己输出的例句也不许是截断过的。"""
    a = max(0, m.start() - pad)
    b = min(len(text), m.end() + pad)
    return ("…" if a > 0 else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def judge(norm: str, off: int, quote: str):
    """返回 [(级别, 机制, 证据原文)]。**不下结论，只给理由。**"""
    out = []
    before = norm[max(0, off - 340):off]
    after = norm[off + len(quote):off + len(quote) + 160]
    head = norm[:FRONT_MATTER_CHARS]

    m = LEADIN.search(before)
    if m:
        out.append(("高", "①传记/文集转录他人书信：命中句之前有引导语", evidence(before, m)))

    m = DIALOG_AFTER.search(after)
    if m:
        out.append(("高", "②小说对白：命中句之后跟着「某人答道」", evidence(after, m)))
    else:
        m = SPEAKER_LABEL.search(before[-90:])
        if m:
            out.append(("中", "②小说对白：命中句之前疑似说话人标记行", evidence(before[-90:], m)))

    m = DIGITIZE.search(before) or DIGITIZE.search(quote)
    if m:
        src = before if DIGITIZE.search(before) else quote
        out.append(("高", "④数字化/馆藏声明：说话的是图书馆或扫描方", evidence(src, m)))

    m = EDITOR.search(before) or EDITOR.search(quote)
    if m:
        src = before if EDITOR.search(before) else quote
        lv = "高" if off < FRONT_MATTER_CHARS else "中"
        out.append((lv, "③校勘者/编者：谈版本、比对、印本或本版体例", evidence(src, m)))
    elif off < FRONT_MATTER_CHARS:
        out.append(("中", f"③序言区：偏移 {off} < {FRONT_MATTER_CHARS}，多半是序/献词/编者说明",
                    evidence(head, re.search(re.escape(quote[:40]), head) or re.compile(r"^").match(head))))
    return out


def run(raw: pathlib.Path, ledger: pathlib.Path, quotes: list):
    recs = {r["source_id"]: r for r in
            (json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip())}
    cache, rows, unread = {}, [], []
    for q in quotes:
        sid, off, txt = q["source_id"], q["norm_offset"], q["quote"]
        if sid not in recs:
            unread.append(sid)
            continue
        if sid not in cache:
            cache[sid] = load_norm(raw, recs[sid])
        norm = cache[sid]
        if norm is None:
            unread.append(sid)
            continue
        if norm[off:off + len(txt)] != txt:
            rows.append({"source_id": sid, "norm_offset": off, "★": "定位对不上，先修偏移", "flags": []})
            continue
        fl = judge(norm, off, txt)
        rows.append({"source_id": sid, "norm_offset": off,
                     "title": recs[sid].get("title", "")[:44], "quote": txt[:110], "flags": fl})
    return rows, unread


# ---------------- 正负对照：**全部跑真语料，不用自编夹具** ----------------
BASE = pathlib.Path(__file__).resolve().parents[2] / "_corpora"
# 必须标出「高」的：本批 5 次实际踩到的
POS = [
    ("wip-marshall-173/workspaces/john-marshall", "src-e03fa3b73336", 12486, "①传记"),
    ("wip-marshall-173/workspaces/john-marshall", "src-2e4088bec901", 172766, "①传记"),
    ("wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-0ac0430b0bd5", 21950, "②对白"),
    ("wip-kant-179/workspaces/immanuel-kant", "src-21c82472024f", 970, "③校勘"),
    ("wip-kant-179/workspaces/immanuel-kant", "src-c90e1301fe6c", 9299, "③校勘"),
    ("wip-kant-179/workspaces/immanuel-kant", "src-64ab9f79bfb5", 2242, "③校勘"),
    ("wip-jefferson-175/workspaces/thomas-jefferson", "src-843f7cba4fcc", 5568, "④数字化"),
]
# 必须**没有**「高」的：已逐条核过、确属本人的
NEG = [
    ("wip-marshall-173/workspaces/john-marshall", "src-8c46f27be355", 69739),
    ("wip-marshall-173/workspaces/john-marshall", "src-8c46f27be355", 483554),
    ("wip-marshall-173/workspaces/john-marshall", "src-8c46f27be355", 523989),
    ("wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-e8dc4740199f", 82643),
    ("wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-413dab629c0f", 6447),
    ("wip-bismarck-176/workspaces/otto-von-bismarck", "src-ee3963b8a368", 36381),
    ("wip-bismarck-176/workspaces/otto-von-bismarck", "src-0e926803e259", 75928),
    ("wip-kant-179/workspaces/immanuel-kant", "src-deba15392d05", 65591),
    ("wip-kant-179/workspaces/immanuel-kant", "src-ff581bf0e357", 297380),
    ("wip-kant-179/workspaces/immanuel-kant", "src-1487a594f356", 777540),
    ("wip-jefferson-175/workspaces/thomas-jefferson", "src-29b9a8e05249", 60368),
    ("wip-jefferson-175/workspaces/thomas-jefferson", "src-ac2df69c6c36", 5495),
]


def _sentence_at(norm, off):
    e = norm.find(".", off + 40)
    return norm[off:(e + 1) if e > 0 else off + 150]


def self_test() -> int:
    bad = 0
    for label, cases, want_high in (("正对照（必须标红）", POS, True), ("负对照（必须不红）", NEG, False)):
        print(f"\n### {label}")
        for case in cases:
            ws, sid, off = case[0], case[1], case[2]
            W = BASE / ws
            recs = {r["source_id"]: r for r in
                    (json.loads(l) for l in (W / "evidence" / "source-ledger.jsonl")
                     .read_text(encoding="utf-8").splitlines() if l.strip())}
            norm = load_norm(W / "raw", recs[sid])
            if norm is None:
                print(f"  ✗ 读不到正文 {sid}")
                bad += 1
                continue
            q = _sentence_at(norm, off)
            fl = judge(norm, off, q)
            high = [f for f in fl if f[0] == "高"]
            ok = bool(high) == want_high
            bad += 0 if ok else 1
            mark = "✓" if ok else "✗"
            why = ("｜".join(f[1].split("：")[0] for f in high)) or ("中级:" + "｜".join(
                f[1].split("：")[0] for f in fl) if fl else "无标记")
            print(f"  {mark} {sid}@{off} {why}")
            if not ok:
                print(f"      句: {q[:110]}")
                for lv, mech, ev in fl:
                    print(f"      [{lv}] {mech}\n          {ev}")
    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}"
          f"（正 {len(POS)} 例全部取自真语料、负 {len(NEG)} 例是已逐条核过的本人原话）")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--ledger")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.raw and a.ledger):
        print("要么 --self-test，要么同时给 --raw 与 --ledger", file=sys.stderr)
        return 2
    blob = sys.stdin.read()
    data = json.loads(blob[blob.find("{"):])
    quotes = data.get("引文", data.get("quotes", []))
    rows, unread = run(pathlib.Path(a.raw), pathlib.Path(a.ledger), quotes)
    n_high = sum(1 for r in rows if any(f[0] == "高" for f in r["flags"]))
    n_mid = sum(1 for r in rows if r["flags"] and not any(f[0] == "高" for f in r["flags"]))
    print(json.dumps({
        "候选数": len(rows),
        "**高·几乎肯定不是本人**": n_high,
        "中·需看上下文": n_mid,
        "无标记": len(rows) - n_high - n_mid,
        "读不到正文": unread,
        "★ 本工具不判断": "只给理由和原文证据，说话人由人定",
        "逐条": rows,
    }, ensure_ascii=False, indent=1))
    return 4 if unread else (3 if n_high else 0)


if __name__ == "__main__":
    sys.exit(main())
