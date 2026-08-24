# -*- coding: utf-8 -*-
"""构建 Palladio 盲判判分输入（8 批 × 4 题），输出 /tmp/pall_judge_in_b{N}.jsonl"""
import json, pathlib

T = pathlib.Path("andrea-palladio")
payload = json.load(open(T / "evals/round1/palladio147_blind_payload.json", encoding="utf-8"))
key = json.load(open(T / "evals/round1/palladio147_blind_key.json", encoding="utf-8"))
cases = {json.loads(l)["case_id"]: json.loads(l) for l in open(T / "evals/cases.jsonl", encoding="utf-8") if l.strip()}

JUDGE = """你是盲判评委。给你一道题、两个匿名答案 A 与 B，以及评分标准（rubric）。请你独立给 A、B 各打一个 0 到 1 之间的分（0=完全失败，1=完美符合）。

评分标准（rubric）：
- 通过条件：{passc}
- 失败条件：{failc}

题目：{question}

答案 A：
{A}

答案 B：
{B}

只输出一个 JSON 对象，格式严格为 {{"A": 分数, "B": 分数}}，不要任何多余文字、不要 Markdown、不要注释。"""

batches = []
for i in range(0, len(payload), 4):
    batch = payload[i:i+4]
    items = []
    for item in batch:
        qid = item["case_id"]  # q-01 ...
        meta = key[qid]
        cid = meta["case_id"]
        case = cases[cid]
        rub = case.get("rubric", {})
        items.append({
            "id": qid,
            "prompt": JUDGE.format(passc=rub.get("通过条件", ""), failc=rub.get("失败条件", ""),
                                   question=item["question"], A=item["A"], B=item["B"]),
        })
    batches.append(items)

for idx, items in enumerate(batches):
    with open(f"/tmp/pall_judge_in_b{idx}.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
print("batches:", len(batches), "| per batch:", len(batches[0]))
