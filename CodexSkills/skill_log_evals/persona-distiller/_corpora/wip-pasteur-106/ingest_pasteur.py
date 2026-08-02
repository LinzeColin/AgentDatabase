#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#106 Pasteur ingest。

tier 口径按 RUNBOOK 2651：**P1 = 亲笔／署名；P2 = 同一材料的降质版本。**
同时代他人记述是 S1，不是 P2（这一条我在 #105 上先想错、查了 RUNBOOK 才改回来）。

★ 六路分配按**内容**分，不按凑数分。Semmelweis #105 只覆盖 2 路被门拦下，
但补救办法不是把源乱塞进空的 lane——是照它实际是什么记。
覆盖不到 6 路就如实报，由门说话。
"""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE / "workspaces/louis-pasteur"
D = pathlib.Path("/Users/linzezhang/Documents/Codex/AgentDatabase/"
                 "character-distillation-skill-reorganize-d57595/CodexSkills/"
                 "registry/codex/persona-distiller")

# 题名关键词 → lane。**先判更具体的，再落到默认。**
LANE_RULES = [
    (re.compile(r"correspond|lettre|letter", re.I),                 "conversations"),
    (re.compile(r"discours|allocution|réception|reception|"
                r"réflexions|reflexions|budget de la science|"
                r"science en France", re.I),                        "expression"),
    (re.compile(r"rapport à|rapport a |ministre|commission|"
                r"examen critique", re.I),                          "decisions"),
    (re.compile(r"vie de pasteur|life of pasteur|biograph|"
                r"histoire d|his life", re.I),                      "timeline"),
]
DEFAULT_LANE = {"writings": "writings", "external": "external", "biography": "external"}
TIER = {"writings": "P1", "external": "S1", "biography": "S2"}

rows = []
for line in (HERE / "raw/_ids.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    p = line.split("|")
    if len(p) < 5:
        continue
    rows.append({"id": p[0].strip(), "cat": p[1].strip(), "year": p[2].strip(),
                 "title": p[3].strip(), "url": p[4].strip()})

files = {p.stem: p for p in (HERE / "raw").glob("*.txt") if p.name != "_ids.txt"}
ok = fail = 0
holdout_done = False
lanes_used = {}
for r in rows:
    f = files.pop(r["id"], None)
    if f is None:
        print(f"  ✗ 无落盘文件：{r['id']}")
        fail += 1
        continue
    lane = DEFAULT_LANE.get(r["cat"], "external")
    for rx, L in LANE_RULES:
        if rx.search(r["title"]):
            lane = L
            break
    tier = TIER.get(r["cat"], "U")
    argv = [sys.executable, str(D / "scripts/ingest.py"), str(WS), str(f),
            "--tier", tier, "--dimension", lane, "--language", "fr",
            "--rights", "public-domain", "--locator", r["url"],
            "--published-at", r["year"] or "1870", "--source-type", "text"]
    if r["cat"] == "writings":
        argv += ["--author", "Louis Pasteur"]
    if not holdout_done and r["cat"] == "biography":
        argv.append("--holdout"); holdout_done = True
    p = subprocess.run(argv, capture_output=True, text=True)
    if p.returncode == 0:
        ok += 1
        lanes_used[lane] = lanes_used.get(lane, 0) + 1
    else:
        fail += 1
        print(f"  ✗ {f.name}: {(p.stderr or p.stdout).strip()[:150]}")

print(f"\ningest 成功 {ok} ／ 失败 {fail}；_ids.txt 未覆盖的落盘文件 {len(files)} 份")
for n in list(files)[:6]:
    print(f"    · 未 ingest：{n}")
print("六路分布：", dict(sorted(lanes_used.items(), key=lambda x: -x[1])))
