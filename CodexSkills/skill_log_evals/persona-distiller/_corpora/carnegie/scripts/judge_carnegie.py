#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jean-Baptiste Say #248 盲判：4 席位（D/E × g1/g2）各 16 题判分。
- 主通道 deepseek flash（max_tokens=1200），备胎 scnet DeepSeek-V4-Flash-0731
- 逐题落盘，可断点续判
"""
import json
import os
import re
import time
import urllib.request

DS_API = "https://api.deepseek.com/chat/completions"
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
SC_API = "https://api.scnet.cn/api/llm/v1/chat/completions"
SC_KEY = os.environ.get("SCNET_API_KEY", "")
MODEL = "deepseek-v4-flash"
SC_MODEL = "DeepSeek-V4-Flash-0731"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
round_dir = os.path.join(WS, "evals", "round1")

JUDGE_SYS = ("你是盲判评委。只依据评分标准给两份匿名回答 A、B 各打 0-1 分"
             "（满分=完全达到通过条件，0=完全未达），并标出是否存在致命错误(critical)。"
             "只输出 JSON：{\"A\":0.5,\"B\":0.5,\"critical_A\":false,\"critical_B\":false,\"reason\":\"一句话\"}")


def _post(api, key, model, body, timeout=120):
    req = urllib.request.Request(api, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def judge(qid, prompt, rubric, a, b):
    text = (f"题目：{prompt}\n通过条件：{rubric.get('通过条件','')}\n"
            f"失败条件：{rubric.get('失败条件','')}\n\nA：{a}\n\nB：{b}\n\n输出 JSON。")
    msgs = [{"role": "system", "content": JUDGE_SYS}, {"role": "user", "content": text}]
    for attempt in range(4):
        for api, key, model, mt in ((DS_API, DS_KEY, MODEL, 1200), (SC_API, SC_KEY, SC_MODEL, 1200)):
            try:
                d = _post(api, key, model, {"model": model, "messages": msgs, "max_tokens": mt})
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
                continue
        time.sleep(2 * (attempt + 1))
    return None


def main():
    import sys as _sys
    only_seat = None
    only_cases = None
    for a in _sys.argv[1:]:
        if a.startswith("--seat="):
            only_seat = a.split("=")[1]
        if a.startswith("--only-cases="):
            only_cases = a.split("=")[1].split(",")
    payload = json.load(open(os.path.join(round_dir, "car_blind_payload.json")))
    key = json.load(open(os.path.join(round_dir, "car_blind_key.json")))
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    rub = {c["case_id"]: c.get("rubric", {}) for c in cases}
    seats = [("D", 1), ("D", 2), ("E", 1), ("E", 2)]
    if only_seat:
        letter = only_seat[0]
        g = int(only_seat[1:])
        seats = [(letter, g)]
    for seat, g in seats:
        lo, hi = (0, 16) if g == 1 else (16, 32)
        out = os.path.join(round_dir, f"judge_{seat}_g{g}.json")
        existing = {}
        if os.path.exists(out):
            for rec in json.load(open(out)):
                existing[rec["q"]] = rec
        todo = []
        for i in range(lo, hi):
            item = payload[i]
            qid = item["case_id"]
            orig = (key.get(qid) or {}).get("case_id", "")
            if only_cases and orig not in only_cases:
                continue
            if qid in existing:
                existing.pop(qid, None)  # 重判：清旧分
            todo.append((qid, item["question"], rub.get(orig, {}), item["A"], item["B"]))
        if not todo:
            print(f"{seat}-g{g}: 已完整 {len(existing)}")
            continue
        print(f"{seat}-g{g}: 判 {len(todo)} 题: {[t[0] for t in todo]}", flush=True)
        for qid, prompt, rubric, a, b in todo:
            res = judge(qid, prompt, rubric, a, b)
            if res is None:
                print(f"  {qid}: 失败(4轮重试)", flush=True)
                continue
            existing[qid] = res
            with open(out, "w") as f:
                json.dump(list(existing.values()), f, ensure_ascii=False, indent=1)
            print(f"  {qid}: A={res['A']} B={res['B']} critA={res['critical_A']} critB={res['critical_B']}", flush=True)
            time.sleep(0.6)
        print(f"{seat}-g{g}: 完成 {len(existing)} 题")


if __name__ == "__main__":
    main()
