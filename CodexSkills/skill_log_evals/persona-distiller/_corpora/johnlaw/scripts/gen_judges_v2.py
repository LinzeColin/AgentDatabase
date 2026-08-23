#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Law #225 盲判 v2：逐题落盘 + 短超时 + 简洁 prompt。

对 round1/judge_<seat>_g<g>.json 中缺失的 qid 逐个判分，写回。
"""
import json
import os
import re
import sys
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-30498de9e48d4d7b94e5184fd8787928")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
round_dir = os.path.join(WS, "evals", "round1")

JUDGE_SYS = ("你是盲判评委。只依据评分标准给两份匿名回答 A、B 各打 0-1 分"
             "（满分=完全达到通过条件，0=完全未达），并标出是否存在致命错误(critical)。"
             "只输出 JSON：{\"A\":0.5,\"B\":0.5,\"critical_A\":false,\"critical_B\":false,\"reason\":\"一句话\"}")


def judge(qid, prompt, rubric, a, b):
    text = (f"题目：{prompt}\n通过条件：{rubric.get('通过条件','')}\n"
            f"失败条件：{rubric.get('失败条件','')}\n\nA：{a}\n\nB：{b}\n\n输出 JSON。")
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": JUDGE_SYS},
                     {"role": "user", "content": text}],
        "max_tokens": 400,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY}",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            content = d["choices"][0]["message"].get("content") or ""
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
            m = re.search(r"\{[^{}]*\"A\"[^{}]*\}", cleaned, re.S) or re.search(r"\{.*\}", cleaned, re.S)
            if not m:
                raise ValueError("no json")
            obj = json.loads(m.group(0))
            return {"A": float(obj["A"]), "B": float(obj["B"]),
                    "critical_A": bool(obj.get("critical_A")), "critical_B": bool(obj.get("critical_B")),
                    "reason": str(obj.get("reason", ""))[:200], "q": qid}
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def load():
    payload = json.load(open(os.path.join(round_dir, "jl_blind_payload.json")))
    key = json.load(open(os.path.join(round_dir, "jl_blind_key.json")))
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    rub = {c["case_id"]: c.get("rubric", {}) for c in cases}
    return payload, key, rub


def process(seat, g, lo, hi, payload, key, rub):
    out = os.path.join(round_dir, f"judge_{seat}_g{g}.json")
    existing = {}
    if os.path.exists(out):
        for rec in json.load(open(out)):
            existing[rec["q"]] = rec
    todo = []
    for i in range(lo, hi):
        item = payload[i]
        qid = item["case_id"]
        if qid in existing:
            continue
        orig = (key.get(qid) or {}).get("case_id", "")
        todo.append((qid, item["question"], rub.get(orig, {}), item["A"], item["B"]))
    print(f"{seat}-g{g}: 缺 {len(todo)} 题", flush=True)
    for qid, question, rubric, a, b in todo:
        r = judge(qid, question, rubric, a, b)
        if r:
            existing[qid] = r
            json.dump([existing[k] for k in sorted(existing)], open(out, "w"), ensure_ascii=False, indent=1)
            print(f"  {qid}: A={r['A']} B={r['B']} cA={r['critical_A']} cB={r['critical_B']}", flush=True)
        else:
            print(f"  {qid}: 失败", flush=True)
        time.sleep(0.4)
    print(f"-> {out} ({len(existing)} 题)", flush=True)


def main():
    payload, key, rub = load()
    for seat, g, lo, hi in [("D", 1, 0, 16), ("D", 2, 16, 32), ("E", 1, 0, 16), ("E", 2, 16, 32)]:
        process(seat, g, lo, hi, payload, key, rub)


if __name__ == "__main__":
    main()
