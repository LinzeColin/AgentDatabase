#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Law #225 判分补漏：对 4 个 judge 文件里仍缺失的 qid 重判。

- 主通道 deepseek（max_tokens=1200）
- 备胎 scnet DeepSeek-V4-Flash-0731
逐题落盘。
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
WS = "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/johnlaw"
round_dir = os.path.join(WS, "evals", "round1")

JUDGE_SYS = ("你是盲判评委。只依据评分标准给两份匿名回答 A、B 各打 0-1 分"
             "（满分=完全达到通过条件，0=完全未达），并标出是否存在致命错误(critical)。"
             "只输出 JSON：{\"A\":0.5,\"B\":0.5,\"critical_A\":false,\"critical_B\":false,\"reason\":\"一句话\"}")


def _post(api, key, model, body):
    req = urllib.request.Request(api, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def judge(qid, prompt, rubric, a, b):
    text = (f"题目：{prompt}\n通过条件：{rubric.get('通过条件','')}\n"
            f"失败条件：{rubric.get('失败条件','')}\n\nA：{a}\n\nB：{b}\n\n输出 JSON。")
    msgs = [{"role": "system", "content": JUDGE_SYS}, {"role": "user", "content": text}]
    for attempt in range(3):
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
    pl = [x for x in os.listdir(round_dir) if x.endswith("_blind_payload.json")]; assert pl, "no payload"; payload = json.load(open(os.path.join(round_dir, pl[0])))
    kl = [x for x in os.listdir(round_dir) if x.endswith("_blind_key.json")]; assert kl, "no key"; key = json.load(open(os.path.join(round_dir, kl[0])))
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    rub = {c["case_id"]: c.get("rubric", {}) for c in cases}
    for seat, g, lo, hi in [("D", 1, 0, 16), ("D", 2, 16, 32), ("E", 1, 0, 16), ("E", 2, 16, 32)]:
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
        if not todo:
            print(f"{seat}-g{g}: 已完整 {len(existing)}"); continue
        print(f"{seat}-g{g}: 补 {len(todo)} 题: {[t[0] for t in todo]}", flush=True)
        for qid, question, rubric, a, b in todo:
            r = judge(qid, question, rubric, a, b)
            if r:
                existing[qid] = r
                json.dump([existing[k] for k in sorted(existing)], open(out, "w"), ensure_ascii=False, indent=1)
                print(f"  {qid}: A={r['A']} B={r['B']} cA={r['critical_A']} cB={r['critical_B']}", flush=True)
            else:
                print(f"  {qid}: 仍失败", flush=True)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
