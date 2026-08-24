#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Law #225 盲判结果组装：key + 4 份 judge 文件 → evals/results.jsonl（128 行）。

每行: blind_label/case_id/critical_failure/dimension_scores/judge_id/overall_score/
rationale/run_id/suite/system
"""
import json
import os
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
round_dir = os.path.join(WS, "evals", "round1")

run_id = None
try:
    rp = json.load(open(os.path.join(WS, "evals", "run-plan.json")))
    run_id = rp.get("run_id") or rp.get("plan", {}).get("run_id")
except Exception:
    pass

# key：q-xx -> {A, B, case_id}
key_path = None
prefix = None
for fn in os.listdir(round_dir):
    if fn.endswith("_blind_key.json"):
        key_path = os.path.join(round_dir, fn)
        prefix = fn.replace("_blind_key.json", "")
        break
if not key_path:
    print("没找到 blind_key.json"); sys.exit(2)
key = json.load(open(key_path))
print(f"key: {len(key)} 题, prefix={prefix}, run_id={run_id}")

# 每席每题：case_id -> {A: score, B: score, critical_A, critical_B, reason}
per_seat = {}
for seat in ("D", "E"):
    scores = {}
    for g in (1, 2):
        p = os.path.join(round_dir, f"judge_{seat}_g{g}.json")
        if not os.path.exists(p):
            print(f"缺 {p}"); sys.exit(2)
        for rec in json.load(open(p)):
            scores[rec["q"]] = rec
    per_seat[seat] = scores

cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
suite_of = {c["case_id"]: c["suite"] for c in cases}

rows = []
for qid, kv in key.items():
    case_id = kv["case_id"]
    suite = suite_of.get(case_id, "")
    for seat in ("D", "E"):
        rec = per_seat[seat].get(qid)
        if not rec:
            print(f"缺 {seat} {qid}"); sys.exit(2)
        for label in ("A", "B"):
            sys_name = kv[label]
            rows.append({
                "blind_label": label,
                "case_id": case_id,
                "critical_failure": rec.get(f"critical_{label}", False),
                "dimension_scores": [],
                "judge_id": f"seat_{seat}",
                "overall_score": rec[label],
                "rationale": rec.get("reason", ""),
                "run_id": run_id or "",
                "suite": suite,
                "system": sys_name,
            })

out = os.path.join(WS, "evals", "results.jsonl")
with open(out, "w") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"results.jsonl: {len(rows)} 行")
# 统计
from collections import Counter
print("system 分布:", dict(Counter(r["system"] for r in rows)))
print("judge 分布:", dict(Counter(r["judge_id"] for r in rows)))
