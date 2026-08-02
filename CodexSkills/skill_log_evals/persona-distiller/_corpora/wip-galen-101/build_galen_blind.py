#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构造 Galen #101 的盲判载荷。

A/B 归属按 `case_id` 的 sha256 逐条翻转——**确定性、与内容无关、可复核**。
**不给评委任何 rubric**：两轮评委都点名过「rubric 的形状取自答案」，
给了就等于告诉评委我想要什么。
"""
import hashlib, json, pathlib, sys

SP = pathlib.Path(__file__).resolve().parent


def side(cid: str) -> bool:
    """True = 产物落 A 位。"""
    return int(hashlib.sha256(cid.encode()).hexdigest(), 16) % 2 == 0


def main() -> int:
    cand = json.loads((SP / "galen_candidate.json").read_text(encoding="utf-8"))
    bare_p = SP / "galen_baseline_bare.json"
    if not bare_p.is_file():
        print("缺 galen_baseline_bare.json —— 裸模型对照臂未就绪，**不构造载荷**", file=sys.stderr)
        return 3
    bare = json.loads(bare_p.read_text(encoding="utf-8"))
    cases = {json.loads(l)["case_id"]: json.loads(l)
             for l in (SP / "ws-galen/galen-of-pergamon/evals/cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

    miss = set(cases) - set(bare)
    if miss:
        print(f"裸模型缺 {len(miss)} 条：{sorted(miss)[:5]} …", file=sys.stderr)
        return 3

    payload, key = [], {}
    for cid in sorted(cases):
        prod_is_a = side(cid)
        a = cand[cid] if prod_is_a else bare[cid]
        b = bare[cid] if prod_is_a else cand[cid]
        payload.append({"case_id": cid, "question": cases[cid]["prompt"], "A": a, "B": b})
        key[cid] = "A" if prod_is_a else "B"

    (SP / "galen_blind_payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    (SP / "galen_blind_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    na = sum(1 for v in key.values() if v == "A")
    la = sum(len(p["A"]) for p in payload) / len(payload)
    lb = sum(len(p["B"]) for p in payload) / len(payload)
    print(f"载荷 {len(payload)} 条；产物落 A 位 {na} 次 / B 位 {len(payload)-na} 次")
    print(f"平均长度 A {la:.0f} / B {lb:.0f} 字符"
          + ("　← **长度差 >25%，须提醒评委按长度打折**" if max(la, lb) / max(1, min(la, lb)) > 1.25 else "　（长度可比）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
