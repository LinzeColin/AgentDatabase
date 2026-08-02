#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把两席盲判还原成 results.jsonl，并报出**真 delta**。

`baseline_source: bare-model-run` —— 对照臂由独立子代理跑裸模型产生，
禁检索禁读盘，返回时确认未动用任何检索。**不是自撰稻草人。**
"""
import hashlib, json, pathlib, sys
from collections import defaultdict

SP = pathlib.Path(__file__).resolve().parent
WS = SP / "ws-galen/galen-of-pergamon"


def main() -> int:
    key = json.loads((SP / "galen_blind_key.json").read_text(encoding="utf-8"))
    cases = {json.loads(l)["case_id"]: json.loads(l)
             for l in (WS / "evals/cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    seats = {}
    for seat, f in (("seat-D-score-v1", "galen_judge_D2.json"), ("seat-E-strict-v1", "galen_judge_E2.json")):
        p = SP / f
        if not p.is_file():
            print(f"缺 {f} —— **两席不齐不出结论**", file=sys.stderr)
            return 3
        seats[seat] = json.loads(p.read_text(encoding="utf-8"))

    rows, cand_s, base_s = [], [], []
    per_suite = defaultdict(lambda: [[], []])
    wins = [0, 0, 0]  # 产物 / 裸模型 / 平
    for cid, spec in sorted(cases.items()):
        prod_side = key[cid]
        for seat, scores in seats.items():
            if cid not in scores:
                print(f"{seat} 缺 {cid}", file=sys.stderr); return 3
            a, b = scores[cid]
            c = a if prod_side == "A" else b
            d = b if prod_side == "A" else a
            cand_s.append(c); base_s.append(d)
            per_suite[spec["suite"]][0].append(c)
            per_suite[spec["suite"]][1].append(d)
            wins[0 if c > d else 1 if d > c else 2] += 1
            for sys_name, sc in (("candidate", c), ("baseline", d)):
                rows.append({"case_id": cid, "system": sys_name, "judge_id": seat,
                             "overall_score": round(float(sc), 2), "suite": spec["suite"],
                             "round": 2,
                             "baseline_source": "bare-model-run" if sys_name == "baseline" else None})
    (WS / "evals/results.jsonl").write_text(
        "\n".join(json.dumps({k: v for k, v in r.items() if v is not None},
                             ensure_ascii=False, sort_keys=True) for r in rows) + "\n", encoding="utf-8")

    C = sum(cand_s) / len(cand_s); B = sum(base_s) / len(base_s)
    print(f"对数 {len(cand_s)}（32 用例 × 2 席）")
    print(f"  产物   {C:.4f}")
    print(f"  裸模型 {B:.4f}")
    print(f"  **真 delta {C - B:+.4f}**")
    print(f"  逐对胜负：产物 {wins[0]} / 裸模型 {wins[1]} / 平 {wins[2]}")
    print("\n  逐套件（产物 / 裸模型 / 差）：")
    for s, (cs, bs) in sorted(per_suite.items(), key=lambda kv: -(sum(kv[1][0])/len(kv[1][0]) - sum(kv[1][1])/len(kv[1][1]))):
        c, b = sum(cs)/len(cs), sum(bs)/len(bs)
        print(f"    {s:22s} {c:.3f} / {b:.3f} = {c-b:+.3f}")
    json.dump({"candidate": round(C, 4), "bare_model": round(B, 4), "delta": round(C - B, 4),
               "pairs": len(cand_s), "wins_candidate": wins[0], "wins_bare": wins[1], "ties": wins[2],
               "baseline_source": "bare-model-run"},
              open(SP / "galen_blind_result_r2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
