#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kandinsky 盲判 judge：读 blind payload + cases rubric，构造 32 个 judge prompt。"""
import json, os, re

WS = "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-wassily-kandinsky-132/wassily-kandinsky"
EVALS = os.path.join(WS, "evals")
payload = json.load(open(os.path.join(EVALS, "round1/blind_blind_payload.json")))
key = json.load(open(os.path.join(EVALS, "round1/blind_blind_key.json")))
cases = {c["case_id"]: c for c in (json.loads(l) for l in open(os.path.join(EVALS, "cases.jsonl")) if l.strip())}

JUDGE_HEAD = """你是一位独立评委，为一个「人物扮演技能」的评测打分。你与产物的作者是不同的人，不要迎合作者。

打分对象是下面这道题的两个匿名回答 A 与 B。给 A 和 B 各打一个 0.0–1.0 的总分，保留两位小数，并给出简短理由。

打分锚点：
- 0.90–1.00：完全满足 rubric，且没有任何超出证据的断言
- 0.75–0.89：满足 rubric 主要要求，有小瑕疵
- 0.50–0.74：部分满足，缺一个 rubric 明确要求的要点
- 0.25–0.49：偏离 rubric，或引入未经支持的说法
- 0.00–0.24：违反 rubric 明列的失败条件

评分标准（rubric）：
{rubric}

只输出 JSON，格式：{{"A": 分数, "B": 分数, "A_reason": "简短理由", "B_reason": "简短理由"}}，不要输出其它任何文字。
"""

def build(entry):
    cid = key[entry["case_id"]]["case_id"]
    case = cases[cid]
    rubric = case.get("rubric")
    if isinstance(rubric, dict):
        rub = "；".join(f"{k}：{v}" for k, v in rubric.items())
    else:
        rub = str(rubric)
    q = entry["question"]
    a = entry["A"]
    b = entry["B"]
    body = f"题目：{q}\n\n回答 A：\n{a}\n\n回答 B：\n{b}\n\n评分："
    return JUDGE_HEAD.format(rubric=rub) + "\n" + body

items = []
for entry in payload:
    items.append({"id": entry["case_id"], "prompt": build(entry)})

with open(os.path.join(EVALS, "round1/judge_prompts.jsonl"), "w") as f:
    for it in items:
        f.write(json.dumps(it, ensure_ascii=False) + "\n")
print("judge prompts:", len(items))
