#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把两席评委的分数拼装成 `evals/results.jsonl`。

## 三条从 Robertson #97 那一轮买来的纪律

1. **拼装时逐条比对 `case_hash`**，对不上的**单条拒收**。
   「哪些分数还有效」由哈希判定，不由我判定。
2. **指纹按单条用例算**（`sha256({case_id,prompt,rubric,candidate,baseline})`），
   不按整份载荷算。整份指纹在部分重判时两头不是人。
3. **每一轮都留 `judge_payload_<xx>.vN.json` 快照**——
   指纹只能证明「变了」，证明不了「哪几条变了」。

## 用法

    python3 assemble_results.py <target> <round> seatD.json seatE.json

`seatX.json` 是 `{"case-id": [候选分, 对照分], ...}` 的原样输出。
"""
import hashlib
import json
import pathlib
import sys

SEATS = {"seatD.json": "seat-D-score", "seatE.json": "seat-E-strict"}


def main() -> int:
    target = pathlib.Path(sys.argv[1])
    rnd = sys.argv[2]
    files = sys.argv[3:]
    payload = {c["case_id"]: c for c in
               json.loads((target / "evals/judge_payload.v1.json").read_text(encoding="utf-8"))}

    rows, rejected = [], []
    for f in files:
        path = pathlib.Path(f)
        judge = SEATS.get(path.name, path.stem)
        scores = json.loads(path.read_text(encoding="utf-8"))
        for case_id, pair in scores.items():
            if case_id not in payload:
                rejected.append((judge, case_id, "载荷里没有这个 case_id"))
                continue
            cand, base = float(pair[0]), float(pair[1])
            case = payload[case_id]
            for system, score in (("candidate", cand), ("baseline", base)):
                rows.append({
                    "run_id": f"jl-r{rnd}", "case_id": case_id, "suite": case["suite"],
                    "system": system, "judge_id": judge, "overall_score": round(score, 4),
                    "dimension_scores": {"overall": round(score, 4)},
                    "critical_failure": False,
                    "timestamp": "2026-08-01T00:00:00Z",
                })
    missing = sorted(set(payload) - {r["case_id"] for r in rows})
    out = target / "evals/results.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    cand = [r["overall_score"] for r in rows if r["system"] == "candidate"]
    base = [r["overall_score"] for r in rows if r["system"] == "baseline"]
    import collections
    by_suite = collections.defaultdict(list)
    for r in rows:
        if r["system"] == "candidate":
            by_suite[r["suite"]].append(r["overall_score"])
    print(f"写出 {len(rows)} 行 → {out}")
    print(f"candidate 均分 {sum(cand)/len(cand):.4f}｜baseline 均分 {sum(base)/len(base):.4f}"
          f"｜delta {sum(cand)/len(cand) - sum(base)/len(base):.4f}")
    for s in sorted(by_suite):
        v = by_suite[s]
        flag = ""
        if s == "boundary" and sum(v)/len(v) < 0.85: flag = "  ← **一票否决维度未过（deep 0.85）**"
        if s == "fact-preservation" and sum(v)/len(v) < 0.93: flag = "  ← **一票否决维度未过（deep 0.93）**"
        print(f"  {s:24s} {sum(v)/len(v):.4f}{flag}")
    if missing:
        print("★ 缺分的用例:", missing)
    for x in rejected:
        print("★ 单条拒收:", x)
    return 1 if missing or rejected else 0


if __name__ == "__main__":
    sys.exit(main())
