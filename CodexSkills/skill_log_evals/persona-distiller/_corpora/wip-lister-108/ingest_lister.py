#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#108 Lister ingest。

tier 口径按 RUNBOOK 2651：P1 = 亲笔／署名；P2 = 同一材料的降质版本。
同时代他人记述是 S1，不是 P2。

★ 六路按内容分。Semmelweis #105 只覆盖 2 路被门拦下，
但补救办法不是把源乱塞进空 lane——是照它实际是什么记。
"""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
WS = HERE / "workspaces/joseph-lister"
D = pathlib.Path("/Users/linzezhang/Documents/Codex/AgentDatabase/"
                 "character-distillation-skill-reorganize-d57595/CodexSkills/"
                 "registry/codex/persona-distiller")

LANE = [
    (re.compile(r"letter|correspond|obituary notice", re.I), "conversations"),
    (re.compile(r"address|oration|lecture|introductory|presidential|"
                r"discussion|congress", re.I), "expression"),
    (re.compile(r"report|statistic|salubrity|hospital|committee|"
                r"observations on the", re.I), "decisions"),
    (re.compile(r"\blife\b|biograph|memoir|memorial", re.I), "timeline"),
]
DEF = {"writings": ("P1", "writings", "Joseph Lister"),
       "external": ("S1", "external", None),
       "biography": ("S2", "external", None)}

rows = []
for line in (HERE / "raw/_ids.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    p = line.split("|")
    if len(p) >= 5:
        rows.append({"id": p[0].strip(), "cat": p[1].strip(), "year": p[2].strip(),
                     "title": p[3].strip(), "url": p[4].strip()})

files = {p.stem: p for p in (HERE / "raw").glob("*.txt") if p.name != "_ids.txt"}
ok = fail = 0
hold = False
lanes = {}
for r in rows:
    f = files.pop(r["id"], None)
    if f is None:
        print(f"  ✗ 无落盘文件：{r['id']}")
        fail += 1
        continue
    tier, lane, author = DEF.get(r["cat"], ("U", "external", None))
    for rx, L in LANE:
        if rx.search(r["title"]):
            lane = L
            break
    argv = [sys.executable, str(D / "scripts/ingest.py"), str(WS), str(f),
            "--tier", tier, "--dimension", lane, "--language", "en",
            "--rights", "public-domain", "--locator", r["url"],
            "--published-at", r["year"] or "1870", "--source-type", "text"]
    if author:
        argv += ["--author", author]
    if not hold and r["cat"] == "biography":
        argv.append("--holdout")
        hold = True
    pr = subprocess.run(argv, capture_output=True, text=True)
    if pr.returncode == 0:
        ok += 1
        lanes[lane] = lanes.get(lane, 0) + 1
    else:
        fail += 1
        print(f"  ✗ {f.name}: {(pr.stderr or pr.stdout).strip()[:130]}")

print(f"\ningest 成功 {ok} / 失败 {fail}；_ids.txt 未覆盖的落盘文件 {len(files)}")
for n in list(files)[:6]:
    print(f"    · 未 ingest：{n}")
print("六路：", dict(sorted(lanes.items(), key=lambda x: -x[1])))
