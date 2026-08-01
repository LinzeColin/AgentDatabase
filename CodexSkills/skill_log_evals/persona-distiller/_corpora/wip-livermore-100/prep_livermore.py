#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Livermore #100 的入库前处理：去重 → 定 holdout → 逐条 ingest。

## 三件事，顺序不能换

### 1. 去重（149 份里 41 份的摘录正文在同一文件内重复 ≥2 次）

抓源脚本的产物特征。不去重的后果是**下游两道门同时失准**：
`check_holdout_overlap` 会被文件内重复顶高重叠率，
`check_claim_coverage` 会在重复文本里重复命中。

### 2. holdout 必须在「读内容之前」定下，且定法要**与内容无关**

本轮的实情必须写清楚，否则就是自己给自己出题（RUNBOOK 第二十八种）：

- **我已经读过抓源报告**，因此知道**哪 8 份带本人直引**、直引句是什么。
  → **这 8 份一律进 train**，不得进 holdout。
- 我**没有**读过那本书的任何一章正文（只看过扉页、Dies 前言、章节标题）。
  → **book 的一章可以进 holdout**，且它是验证力最强的一份（他自己的话）。
- 其余 141 份报纸我只看过文件名与「无直引」这一个属性。
  → 可以进 holdout，选法用 **sha256(文件名) 排序**，与内容无关。

### 3. 逐条 ingest，每条带自己的 URL 与日期

Godin #99 的教训：`--locator` 全批一个值，内容级去重再也定位不到原文。
**每份来源的 locator、published_at、author、dimension 都从它自己的头部取。**

## 分层依据（RUNBOOK 第 822 行）

> **第三人称叙述体**（含访谈整理稿、"关于他"的报道）→ 降 **P2**，
> **只有明确标注的直接引语可引**

| 层 | 内容 |
|---|---|
| `P1` | 书的正文（扉页 + 章节，`A-copyright` 有据） |
| `P2` | 1907–1940 同期报道 |
| `S1` | Dies 的前言；1942 / 1949 两份身后回顾 |
"""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

HEADER_RE = {
    "url": re.compile(r"^SOURCE-URL:\s*(\S+)", re.M),
    "page": re.compile(r"^PAGE-URL:\s*(\S+)", re.M),
    "date": re.compile(r"^DATE:\s*(\S+)", re.M),
    "paper": re.compile(r"^PAPER:\s*(.+)$", re.M),
    "quotes": re.compile(r"^DIRECT-QUOTES-DETECTED:\s*(\d+)", re.M),
}
# 抓源报告第三节列明、且逐条人工核过的 14 份带本人直引的文件（542 份全量抓完后的终版）。
# 它们一律进 train——我已经读过这些引语。
# ⚠ 第一版只有 8 份，那是抓源子代理跑到 150 份时的中间态；
#   它后来继续抓到 542 份，直引从 16 条涨到 28 条。**中间态的清单不要留着当终版用。**
QUOTE_FILES = {
    "jl_1908_thenewsdemocrat_282.txt",
    "jl_1910_thedetroittimes_023.txt",
    "jl_1922_theindianapolist_247.txt",
    "jl_1923_americustimesrec_390.txt",
    "jl_1923_eldoradodailynew_080.txt",
    "jl_1923_thewashingtontim_016.txt",
    "jl_1923_thewashingtontim_122.txt",
    "jl_1924_casperdailytribu_505.txt",
    "jl_1932_theindianapolist_052.txt",
    "jl_1934_sanantoniolight_086.txt",
    "jl_1934_thewashingtontim_034.txt",
    "jl_1940_eveningstar_009.txt",
    "jl_1940_eveningstar_431.txt",
    "jl_1940_thewaterburydemo_409.txt",
}
# 抓源报告第四节：自动检测器初筛出、人工核后说话人**不是他**的文件。
# 它们同样一律进 train——我读过那些被剔除的句子，知道说话人是谁。
REJECTED_FILES = {
    "jl_1917_newyorktribune_135.txt", "jl_1922_thethermopolisin_010.txt",
    "jl_1924_thewashingtondai_491.txt", "jl_1925_thewashingtontim_054.txt",
    "jl_1933_theindianapolist_064.txt", "jl_1933_thewashingtontim_134.txt",
    "jl_1934_eveningstar_056.txt", "jl_1935_sanantoniolight_027.txt",
    "jl_1940_thewilmingtonmor_563.txt",
}
POSTHUMOUS = {"jl_1942_", "jl_1949_"}


def dedupe(text: str) -> tuple:
    """把文件内重复出现的摘录段落压掉。→ (新正文, 压掉了几段)"""
    head, sep, body = text.partition("=" * 60)
    parts = re.split(r"\n\s*\n", body)
    seen, out, removed = set(), [], 0
    for p in parts:
        key = " ".join(p.split())
        if len(key) < 80:                    # 短片段（分隔线、标题）不参与去重
            out.append(p)
            continue
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(p)
    return head + sep + "\n\n".join(out), removed


def dims_for(name: str, quotes: int) -> list:
    """★ `conversations` **只认人工核过的那 8 份**，不认抓源脚本的自动检测。

    第一版写成 `if quotes > 0 or name in QUOTE_FILES`，`conversations` 路
    立刻涨到 **40**。而抓源报告第四节白纸黑字写着：自动检测器初筛出的候选
    大量是**他太太、他的律师、国会议员、同版面无关报道**在说话，已逐条剔除。

    **拿一个自己都声明不可靠的信号去填车道计数，就是把门喂饱。**
    `quotes` 这个头部字段只留作参考，不参与判定。
    """
    d = ["external", "timeline", "decisions"]
    if name in QUOTE_FILES:
        d.append("conversations")
    return d


def run(argv, dry):
    if dry:
        print("  $ " + " ".join(str(x) for x in argv[:6]) + " …")
        return 0
    p = subprocess.run(argv, capture_output=True, text=True)
    if p.returncode != 0:
        print(f"  ✗ {p.stderr.strip()[:200]}", file=sys.stderr)
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=pathlib.Path, required=True)
    ap.add_argument("--clean", type=pathlib.Path, required=True)
    ap.add_argument("--target", type=pathlib.Path, required=True)
    ap.add_argument("--skill", type=pathlib.Path, required=True)
    ap.add_argument("--holdout-news", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    a.clean.mkdir(parents=True, exist_ok=True)

    files = sorted(f for f in a.raw.glob("*.txt") if "HowToTrade" not in f.name)
    meta, total_removed = {}, 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        cleaned, removed = dedupe(text)
        total_removed += removed
        (a.clean / f.name).write_text(cleaned, encoding="utf-8")
        m = {k: (rx.search(text).group(1).strip() if rx.search(text) else "")
             for k, rx in HEADER_RE.items()}
        meta[f.name] = m
    print(f"去重：{len(files)} 份，压掉重复段 {total_removed} 处")

    # holdout：与内容无关的选法（文件名 sha256 排序），且排除 8 份已读的带引语文件
    pool = [n for n in sorted(meta)
            if n not in QUOTE_FILES and n not in REJECTED_FILES
            and not any(n.startswith(p) for p in POSTHUMOUS)]
    pool.sort(key=lambda n: hashlib.sha256(n.encode()).hexdigest())
    holdout = set(pool[:a.holdout_news])
    print(f"holdout（报纸，按 sha256(文件名) 取前 {a.holdout_news}）：{sorted(holdout)}")

    ing = a.skill / "scripts" / "ingest.py"
    ok = bad = 0
    for name in sorted(meta):
        m = meta[name]
        posth = any(name.startswith(p) for p in POSTHUMOUS)
        argv = [sys.executable, str(ing), str(a.target), str(a.clean / name),
                "--tier", "S1" if posth else "P2",
                "--source-type", "newspaper-page-ocr",
                "--rights", "public-domain-us-federal (Library of Congress, Chronicling America)",
                "--author", "third-party newspaper report",
                "--language", "en",
                "--locator", m["url"] or m["page"],
                "--abstract", f"{m['paper']}｜{m['date']}｜整版 OCR 中与本人物相关的摘录",
                ]
        if m["date"]:
            argv += ["--published-at", m["date"]]
        for d in dims_for(name, int(m["quotes"] or 0)):
            argv += ["--dimension", d]
        if name in holdout:
            argv += ["--holdout"]
        rc = run(argv, a.dry_run)
        ok += rc == 0
        bad += rc != 0
    print(f"\ningest：成功 {ok}，失败 {bad}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
