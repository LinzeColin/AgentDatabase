#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲判载荷：A/B 由 sha256(case_id) % 2 定，**评委不给判据**。"""
import hashlib, json, pathlib
cand = json.loads(pathlib.Path("ej_candidate.json").read_text(encoding="utf-8"))
base = json.loads(pathlib.Path("round1/ej_baseline_bare.json").read_text(encoding="utf-8"))
cases = {json.loads(l)["case_id"]: json.loads(l)["prompt"]
         for l in pathlib.Path("cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
payload, key = [], {}
for cid in sorted(cases):
    if cid not in cand or cid not in base:
        raise SystemExit(f"缺答案：{cid}")
    flip = int(hashlib.sha256(cid.encode()).hexdigest(), 16) % 2
    A, B = (cand[cid], base[cid]) if flip == 0 else (base[cid], cand[cid])
    key[cid] = {"A": "candidate" if flip == 0 else "baseline",
                "B": "baseline" if flip == 0 else "candidate"}
    payload.append({"case_id": cid, "question": cases[cid], "A": A, "B": B})
pathlib.Path("round1/ej_blind_payload.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
pathlib.Path("round1/ej_blind_key.json").write_text(
    json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
la=[len(p["A"]) for p in payload]; lb=[len(p["B"]) for p in payload]
print(f"{len(payload)} 对；A 均长 {sum(la)//len(la)}，B 均长 {sum(lb)//len(lb)}"
      f"（差 {abs(sum(la)-sum(lb))*100//max(sum(la),sum(lb))}%）")
print("A 侧是候选的题数：", sum(1 for v in key.values() if v['A']=='candidate'))
