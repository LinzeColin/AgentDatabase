#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#105 Semmelweis 全量 ingest。**不预先优化比例——全部灌进去，让门自己报数。**

tier 口径按 RUNBOOK 2651：**P1 = 亲笔／署名；P2 = 同一材料的降质版本（如 ASR）。**
同时代第三方记述**不是** P2，是 S1——他们记的是他们看见的，不是他的话。
这一条我一开始想错了（以为同时代就算一手），查了 RUNBOOK 才改回来。
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE / "workspaces/ignaz-semmelweis"
D = pathlib.Path("/Users/linzezhang/Documents/Codex/AgentDatabase/"
                 "character-distillation-skill-reorganize-d57595/CodexSkills/"
                 "registry/codex/persona-distiller")

# 类别 → (tier, dimension, author)
#   writings   他本人 → P1 / writings
#   external   同时代他人 → S1 / external（**不是 P2**）
#   biography  后人传记 → S2 / external
PLAN = {
    "writings":  ("P1", "writings",  "Ignaz Semmelweis"),
    "external":  ("S1", "external",  None),
    "biography": ("S2", "external",  None),
}

rows = []
for line in (HERE / "raw/_ids.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    parts = line.split("|")
    if len(parts) < 5:
        continue
    rows.append({"id": parts[0], "cat": parts[1], "year": parts[2],
                 "title": parts[3], "url": parts[4]})

files = {p.name: p for p in (HERE / "raw").glob("*.txt") if p.name != "_ids.txt"}
ok = fail = 0
holdout_done = False
for r in rows:
    # _ids.txt 的 id 与落盘文件名不是一一对应，按前缀/包含匹配
    cand = [p for n, p in files.items() if r["id"] in n or n.startswith(r["id"][:14])]
    if not cand:
        cand = [p for n, p in files.items()
                if any(w and w.lower() in n.lower() for w in r["title"].split()[:2])]
    if not cand:
        print(f"  ✗ 找不到落盘文件：{r['id']}  {r['title'][:50]}")
        fail += 1
        continue
    src = cand[0]
    tier, dim, author = PLAN.get(r["cat"], ("U", "external", None))
    argv = [sys.executable, str(D / "scripts/ingest.py"), str(WS), str(src),
            "--tier", tier, "--dimension", dim, "--language", "de",
            "--rights", "public-domain", "--locator", r["url"],
            "--published-at", r["year"], "--source-type", "text"]
    if author:
        argv += ["--author", author]
    # 第一份 biography 留作 holdout（deep/standard/quick 都要求 ≥1）
    if not holdout_done and r["cat"] == "biography":
        argv.append("--holdout"); holdout_done = True
    p = subprocess.run(argv, capture_output=True, text=True)
    if p.returncode == 0:
        ok += 1
    else:
        fail += 1
        print(f"  ✗ {src.name}: {(p.stderr or p.stdout).strip()[:160]}")
    files.pop(src.name, None)

print(f"\ningest 成功 {ok} ／ 失败 {fail}；_ids.txt 未覆盖到的落盘文件 {len(files)} 份")
for n in list(files)[:8]:
    print(f"    · 未 ingest：{n}")
