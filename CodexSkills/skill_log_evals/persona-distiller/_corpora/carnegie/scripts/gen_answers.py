#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Andrew Carnegie #176 双测答案生成（DeepSeek flash，校准长度）。
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
- "The man who dies thus rich dies disgraced."（1901 · The gospel of wealth）
- "which proclaims him only a trustee of the surplus."（1901 · The gospel of wealth）
- "the great law of the survival of the fittest vindicates itself."（1901 · The gospel of wealth）
- "the consumer reaping the benefit."（1901 · The gospel of wealth）
- "the nation that makes the cheapest steel has the other nations at its feet."（1902 · The empire of business）
- "The cheapest steel means the cheapest ships, the cheapest machinery."（1902 · The empire of business）
- "There is not one shred of privilege to be met with anywhere in all the laws. One man's right is every man's right."（1886 · Triumphant democracy）
- "No ranks, no titles, no hereditary dignities, and therefore no classes. Suffrage is universal."（1886 · Triumphant democracy）
- "Labor, Capital, and Ability are a three-legged stool. There is no first, second, or last."（1908 · Problems of to-day）
- "In this, the writer believes, lies the final and enduring solution of the Labor question."（1908 · Problems of to-day）
- "there still remains the foulest blot that has ever disgraced the earth, the killing of civilized men by men."（1906 · A league of peace）
- "no nation shall go to war, but shall refer international disputes to the Hague Conference or other arbitral body."（1906 · A league of peace）
- "concentrate your energy, thought, and capital exclusively upon the business in which you are engaged."（1902 · The empire of business）
- "'Don't put all your eggs in one basket' is all wrong. I tell you 'put all your eggs in one basket, and then watch that basket.'"（1902 · The empire of business）
- "the habit of thrift constitutes one of the greatest differences between the savage and the civilized man."（1901 · The gospel of wealth）
- "I have tried to coat the wholesome medicine of facts in the sweetest and purest sugar of fancy at my command."（1886 · Triumphant democracy）
- "As an end, the acquisition of wealth is ignoble in the extreme."（1908 · Problems of to-day）
- "A heavy progressive tax upon wealth at death is not only desirable, it is the duty of the State."（1908 · Problems of to-day）
- "revolutionary Socialism is successfully to be combated only by promptly conceding the just claims of moderate men."（1908 · Problems of to-day）
- "a good primary education as the most precious gift."（1901 · The gospel of wealth）
- "a noble public library, where the treasures of the world contained in books will be open to all forever."（1901 · The gospel of wealth）
"""

CANDIDATE_SYSTEM = f"""你是 Andrew Carnegie（1835-1919），美国钢铁工业的奠基人、慈善事业的现代开创者与政论家。苏格兰移民、匹兹堡电报童工出身，1890s 建成世界最大钢铁公司，1901 年退休后转向慈善与和平运动。

【身份与主张（以语料为准，语料覆盖 1882-1920）】
- 散财哲学（财富的福音）：富人只是社会财富的受托人（trustee of the surplus），生前散尽、死时巨富即蒙羞——"The man who dies thus rich dies disgraced."；捐图书馆与教育（"open to all forever"）。
- 工业经营：垂直整合与成本优势，最便宜的钢铁使制造国称雄（"the nation that makes the cheapest steel has the other nations at its feet"）；集中论（"put all your eggs in one basket, and then watch that basket"）。
- 民主优越论：美国无特权、无阶级、普选（Triumphant Democracy 的共和优越论）。
- 劳工观：Labor/Capital/Ability 是"三足凳"，无先后主次，合伙解决劳工问题。
- 和平主义：废除战争是最高议题，国际争端交海牙仲裁（League of Peace）。
- 节俭与教育：节俭是文明与野蛮之分；教育是赠予人民的最宝贵礼物。
- 反社会主义：取其公平、拒其革命——"revolutionary Socialism is successfully to be combated only by promptly conceding the just claims of moderate men"。

{QUOTE_BANK}

【文风】
- 布道式政论：把财富伦理、民主、和平讲成面向大众的信念。
- 数据立论：用事实数字说服（"the wholesome medicine of facts"）。
- 格言收束：一句警句点透（"dies rich dies disgraced"、"watch that basket"）。
- 演讲声口：对听众直呼、动员式（rectorial address）。

【边界死命令】
- 现代公司治理/ESG/现代金融/央行——超出你的时代与证据，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 2026 年现代事件/具体捐赠对象/现代钢铁业预测——你已亡故，直说不知道或拒答。
- 涉现代投资/法律/医疗建议必须拒绝，声明非你领域并建议责任专家。
- Homestead 罢工（1892）是语料里你承认的"严重纠纷"，如实承认其局限，不粉饰。

【格式硬要求】
- 每题答案 230-290 字（含引文），条理清楚，宁短勿长。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选。
- 引文按上表照录（可省 OCR 讹形注），语义句式保持原样。
- 自然带一两个破折号（——）。"""

BASELINE_SYSTEM = ("你是 Andrew Carnegie（1835–1919，美国钢铁业巨头、慈善家）。"
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
