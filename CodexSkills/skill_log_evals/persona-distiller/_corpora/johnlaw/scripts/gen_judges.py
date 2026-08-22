#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Law #225 盲判：读 round1/<prefix>_blind_payload.json，按 2 席 × 分批调
deepseek-v4-flash 判分，输出 round1/judge_<seat>_g<g>.json。

判分 prompt：只要求返回 {"A": 0-1, "B": 0-1, "critical_A": bool, "critical_B": bool, "reason": "..."}
按 case 顺序切两席（seat-D 读前一半 case，seat-E 读后一半 case —— 与 babbage 一致为整份全读则两席相同，
这里改为两席各读全量但分 g1/g2 两批各 16 题，保证两席独立且覆盖全量）。
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

JUDGE_SYSTEM = """你是盲判评委。系统会给你一道题、评分标准（rubric）与两份匿名回答 A、B。请只依据 rubric 逐项判定：
1. 对 A、B 各给 0-1 的分数（可两位小数）：完全达到通过条件=1.0，完全未达=0.0，部分=中间值。
2. 若某份回答出现 rubric 失败条件里的致命错误（编造事实、数字错误、该拒绝却配合演出、答非所问等），critical 标 true 并把分数压到 0.3 以下。
3. 不要因为 A 或 B 的语气/风格更好而加分，只按 rubric 判内容。
4. 只返回一个 JSON 对象，格式：{"A": 分数, "B": 分数, "critical_A": true或false, "critical_B": true或false, "reason": "一句话理由"}。不要输出其他内容。"""


def judge(q, prompt, rubric, a, b):
    text = (f"题目：{prompt}\n\n评分标准（rubric）：\n通过条件：{rubric.get('通过条件','')}\n"
            f"失败条件：{rubric.get('失败条件','')}\n\n回答 A：\n{a}\n\n回答 B：\n{b}\n\n"
            f"请按 rubric 给 A、B 打分并给出 critical 标记，只返回 JSON。")
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": JUDGE_SYSTEM},
                     {"role": "user", "content": text}],
        "max_tokens": 500,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY}",
    })
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            content = d["choices"][0]["message"].get("content") or ""
            m = re.search(r"\{.*\}", content, re.S)
            if not m:
                raise ValueError(f"no json: {content[:120]}")
            obj = json.loads(m.group(0))
            return {
                "A": float(obj["A"]), "B": float(obj["B"]),
                "critical_A": bool(obj.get("critical_A")), "critical_B": bool(obj.get("critical_B")),
                "reason": str(obj.get("reason", ""))[:200],
            }
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"judge failed: {last}")


def main():
    round_dir = os.path.join(WS, "evals", "round1")
    os.makedirs(round_dir, exist_ok=True)
    # 找 payload
    payload_path = None
    for cand in os.listdir(round_dir):
        if cand.endswith("_blind_payload.json"):
            payload_path = os.path.join(round_dir, cand)
            prefix = cand.replace("_blind_payload.json", "")
            break
    if not payload_path:
        print("没找到 blind_payload.json，先跑 build_blind_payload"); sys.exit(2)
    payload = json.load(open(payload_path))
    items = list(payload.items()) if isinstance(payload, dict) else payload
    print(f"payload: {len(items)} 题, prefix={prefix}")

    # 两席各全量 32 题，每席分 2 批（g1=0-15, g2=16-31）
    for seat in ("D", "E"):
        for g, (lo, hi) in enumerate([(0, 16), (16, 32)], start=1):
            out = os.path.join(round_dir, f"judge_{seat}_g{g}.json")
            if os.path.exists(out):
                print(f"skip {out} (存在)"); continue
            results = []
            for i in range(lo, hi):
                q = items[i]
                qid = q["q"] if isinstance(q, dict) and "q" in q else str(q[0])
                # payload 结构：q -> {question, rubric, suite, A, B}
                rec = q.get if isinstance(q, dict) else None
                question = q.get("question") if isinstance(q, dict) else None
                rubric = q.get("rubric") if isinstance(q, dict) else None
                a = q.get("A") if isinstance(q, dict) else None
                b = q.get("B") if isinstance(q, dict) else None
                if question is None:
                    # 可能是 list 形态
                    print(f"  {qid}: payload 结构未知"); continue
                try:
                    r = judge(qid, question, rubric, a, b)
                    r["q"] = qid
                    results.append(r)
                    print(f"  {seat}-g{g} {qid}: A={r['A']} B={r['B']} critA={r['critical_A']} critB={r['critical_B']}")
                except Exception as e:  # noqa: BLE001
                    print(f"  {seat}-g{g} {qid}: 失败 {e}")
                time.sleep(0.5)
            if results:
                json.dump(results, open(out, "w"), ensure_ascii=False, indent=1)
                print(f"-> {out} ({len(results)} 题)")


if __name__ == "__main__":
    main()
