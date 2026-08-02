#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把两席盲判还原成 results.jsonl，并报出**真 delta**。

★ 算法在看到分数之前写定，看到分数之后不许改。
真 delta = mean(candidate 得分) − mean(baseline 得分)，按 (case × seat) 逐对配，归一到 0–1。
"""
import json, pathlib, sys, collections

WS = pathlib.Path("ws-jenner/ws-jenner")
SP = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "round1")
KEY = json.loads((pathlib.Path("round1") / "ej_blind_key.json").read_text(encoding="utf-8"))
SUITE = {json.loads(l)["case_id"]: json.loads(l)["suite"]
         for l in pathlib.Path("cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

rows, pair_win, pair_tie, pair_lose = [], 0, 0, 0
by_suite = collections.defaultdict(lambda: [0.0, 0.0, 0])
seats = [("seat-D-score-v1", "ej_judge_D.json"), ("seat-E-strict-v1", "ej_judge_E.json")]
n_seat = 0
for seat, fn in seats:
    f = SP / fn
    if not f.is_file():
        print(f"⚠ {fn} 不在，跳过"); continue
    n_seat += 1
    scored = json.loads(f.read_text(encoding="utf-8"))
    for cid, v in scored.items():
        if cid.startswith("_") or cid not in KEY:
            continue
        k = KEY[cid]
        c = float(v["A"]) if k["A"] == "candidate" else float(v["B"])
        d = float(v["B"]) if k["A"] == "candidate" else float(v["A"])
        rows.append({"case_id": cid, "seat": seat, "candidate": c, "baseline": d,
                     "suite": SUITE.get(cid), "note": v.get("note", "")})
        if c > d: pair_win += 1
        elif c == d: pair_tie += 1
        else: pair_lose += 1
        s = by_suite[SUITE.get(cid)]
        s[0] += c; s[1] += d; s[2] += 1

if not rows:
    raise SystemExit("没有任何一席落盘")
mc = sum(r["candidate"] for r in rows) / len(rows)
mb = sum(r["baseline"] for r in rows) / len(rows)
delta = (mc - mb) / 10.0

(WS / "evals").mkdir(parents=True, exist_ok=True)
# quality_check 要的是逐行 {case_id, system, overall_score(0–1), judge_id}，不是成对格式。
# 成对格式只留在工作区外供人读；进 ws 的必须是门认得的那一种，否则门读不到分数会报 0.000，
# 那是「判据没被调用」而不是「判据判了不过」——两者表征一样，不许混。
flat = []
for r in rows:
    for system in ("candidate", "baseline"):
        flat.append({"case_id": r["case_id"], "system": system,
                     "overall_score": round(r[system] / 10.0, 4),
                     "judge_id": r["seat"], "suite": r["suite"]})
(WS / "evals/results.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in flat) + "\n", encoding="utf-8")
pathlib.Path("results.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n", encoding="utf-8")

pos = sum(1 for s, v in by_suite.items() if v[2] and (v[0] - v[1]) > 0)
print(f"席数 {n_seat}　逐对 {len(rows)} 对")
print(f"候选均分 {mc:.3f}　基线均分 {mb:.3f}")
print(f"**真 delta = {delta:+.4f}**")
print(f"逐对：胜 {pair_win} / 平 {pair_tie} / 负 {pair_lose}（共 {len(rows)}）")
print(f"为正的套组：{pos} / {len(by_suite)}")
print("\n分档门：deep 0.07 ／ standard 0.05 ／ quick 0.03")
for name, th in (("deep", 0.07), ("standard", 0.05), ("quick", 0.03)):
    print(f"  {name:9} {'✅ 过' if delta >= th else '❌ 不过'}")
print("\n各套组 delta：")
for s, v in sorted(by_suite.items(), key=lambda x: -(x[1][0] - x[1][1]) / max(x[1][2], 1)):
    if v[2]: print(f"  {s:24} {(v[0]-v[1])/v[2]/10:+.4f}  ({v[2]} 对)")
