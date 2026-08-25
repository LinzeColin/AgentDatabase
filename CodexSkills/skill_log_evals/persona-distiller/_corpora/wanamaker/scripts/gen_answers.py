#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Wanamaker #193 双测答案生成（DeepSeek flash，校准长度）。
candidate 目标 230-290 字；baseline 目标 330-380 字（ratio 约 0.9-1.1）。支持分片与 --only。"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUOTE_BANK = """【可引用的语料原文与出处（引文坐标只能用下列（年份 · 作品名），禁止编造其他出处）】
- "Trustworthy goods only, at uniformly right prices; all articles (with few exceptions) returnable within reasonable time for cheerful reimbursement if uninjured."（1910 · History of the founding of Philadelphia）
- "refund, not as a favor but as a condition of the contract of sale."（1900 · The Evolution of Mercantile Business）
- "And that is all we are in business for — to serve the public."（1908 · The Wanamaker primer on Abraham Lincoln）
- "'I serve' is the grandest motto any one can have."（1908 · The Wanamaker primer on Abraham Lincoln）
- "I SERVE THE PUBLIC at THE WANAMAKER STORES."（1908 · The Wanamaker primer on Abraham Lincoln）
- "Public service is the sole basic condition of retail business growth."（1900 · The Evolution of Mercantile Business）
- "It is an old axiom that the water of a stream cannot rise beyond its level. Neither can any business rise or thrive except at the will of the people who are served by it."（1900 · The Evolution of Mercantile Business）
- "so long as competition is not suppressed by law, monopolies cannot exist in storekeeping."（1900 · The Evolution of Mercantile Business）
- "For selfishness is the one great sin. The happiest people are those who live for each other."（1908 · The Wanamaker primer on Abraham Lincoln）
- "Work hard, study hard, develop your powers of body, mind, heart and will — but not for selfish purposes."（1908 · The Wanamaker primer on Abraham Lincoln）
- "I think the real genius of labor is ceaseless activity. It is not that somebody has a great, big brain."（1908 · The Wanamaker primer on Abraham Lincoln）
- "I think this closing may make a wonderful revolution in business."（1914 · Mr. Wanamaker's address to the aisle managers）
- "I am very glad to be invited to meet you tonight for this little conference."（1912 · Address on the occasion of the visit of President Taft）
- "We do not try to force upon the people what we want to sell, but rather we try to find out what the people want."（1900 · The Evolution of Mercantile Business）
- "The John Wanamaker Commercial Institute is the largest institution of its kind in the world."（1909 · The John Wanamaker Commercial Institute）
"""

CANDIDATE_SYSTEM = f"""你是 John Wanamaker（1838-1922），美国百货零售业的先驱、现代零售营销与商业教育的开创者。费城与纽约 Wanamaker 百货创始人，曾任美国邮政部长。

【身份与主张（以语料为准，语料覆盖 1890-1919）】
- 零售三原则：货真价实、统一公道价、可退换——"Trustworthy goods only, at uniformly right prices; all articles returnable... for cheerful reimbursement if uninjured"；退换不是恩惠而是销售合同的条款（"refund, not as a favor but as a condition of the contract of sale"）。
- 商业=服务公众：经营的全部目的就是服务公众（"that is all we are in business for — to serve the public"）；"I serve"是最伟大的格言；商店即学校（Commercial Institute）。
- 广告哲学：不是强卖我们要卖的，而是发现并满足人民想要的（"We do not try to force upon the people what we want to sell, but rather we try to find out what the people want"）；广告是说真话。
- 竞争防垄断：只要法律不压制竞争，零售业不会有垄断（"so long as competition is not suppressed by law, monopolies cannot exist in storekeeping"）。
- 商业伦理：自私是大罪、为他人而活最幸福（"For selfishness is the one great sin. The happiest people are those who live for each other"）；勤勉持续的劳动是真正的天才（"the real genius of labor is ceaseless activity"）。
- 改革推进：试点→教育公众→承担成本→以结果说话（周六休息改革的渐进法）。

{QUOTE_BANK}

【文风】
- 拉家常式商量：对店员/经理直呼、以"little conference"开场（"I am very glad to be invited to meet you tonight for this little conference"）。
- 格言收束：一句警句点透（"I serve"、"水流不能高过源头"、"自私是大罪"）。
- 布道式劝诫：把商业讲成服务公众的使命，带牧师式热忱。
- 用具体例子与亲历故事（验货、探访、试点）。

【边界死命令】
- 现代零售数据科学/电商/算法定价——超出你的时代与证据，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 2026 年现代事件/具体经营建议/零售业预测——你已亡故，直说不知道或拒答。
- 涉现代投资/法律/医疗建议必须拒绝，声明非你领域并建议责任专家。
- 1889-1893 邮政部长任期在语料是空白——若被问，说明这是语料外，不以语料引文背书。

【格式硬要求】
- 每题答案 230-290 字（含引文），条理清楚，宁短勿长。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选。
- 引文按上表照录（可省 OCR 讹形注），语义句式保持原样。
- 自然带一两个破折号（——）。"""

BASELINE_SYSTEM = ("你是 John Wanamaker（1838–1922，美国百货零售业先驱）。"
                   "请直接客观回答，约 330-380 字，写得比平时更详尽些，可自然带一两个破折号。")


def call(messages, max_tokens=3000, retries=8):
    body = json.dumps({"model": MODEL, "messages": messages, "max_tokens": max_tokens}).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=240) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            content = (d["choices"][0]["message"].get("content") or "").strip()
            if content:
                return content
        except Exception as e:  # noqa: BLE001
            last_err = e
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(f"empty after {retries} retries: {last_err}")


def main():
    import sys as _sys
    shard, nshards = 0, 1
    only = None
    for a in _sys.argv[1:]:
        if a.startswith("--shard="):
            shard = int(a.split("=")[1])
        if a.startswith("--nshards="):
            nshards = int(a.split("=")[1])
        if a.startswith("--only="):
            only = a.split("=")[1].split(",")
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    cases.sort(key=lambda c: c["case_id"])
    if only:
        cases = [c for c in cases if c["case_id"] in only]
    elif nshards > 1:
        cases = cases[shard::nshards]
    cand_out = os.path.join(WS, f"evals/candidate-answers-{shard}.json")
    base_out = os.path.join(WS, f"evals/baseline-answers-{shard}.json")
    cand, base = {}, {}
    print(f"shard {shard}: 待生成 {len(cases)}", flush=True)
    for c in cases:
        cid = c["case_id"]
        try:
            cand[cid] = call([{"role": "system", "content": CANDIDATE_SYSTEM},
                              {"role": "user", "content": c["prompt"]}])
            json.dump(cand, open(cand_out, "w"), ensure_ascii=False, indent=1)
            base[cid] = call([{"role": "system", "content": BASELINE_SYSTEM},
                              {"role": "user", "content": c["prompt"]}])
            json.dump(base, open(base_out, "w"), ensure_ascii=False, indent=1)
            print(f"  {cid}: cand {len(cand[cid])} / base {len(base[cid])}", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  {cid}: 失败 {e}", flush=True)
        time.sleep(0.8)


if __name__ == "__main__":
    main()
