#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Benjamin Franklin #236 双测答案生成（DeepSeek flash，校准长度）。
candidate 150-190 字 → ~330；baseline 约 260 字 → ~300。支持分片。"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUOTE_BANK = """【可引用的语料原文与出处（引文坐标只能用下列（年份 · 作品名），禁止编造其他出处）】
- "Time is Money"（1748 · Advice to a Young Tradesman，见 1794 · Works Vol 2）
- "Remember that money is of the prolific, generating nature. Money can beget money, and its offspring can beget more."（1748 · Advice to a Young Tradesman，见 1794 · Works Vol 2）
- "The way to wealth, if you desire it, is as plain as the way to market."（1758 · The Way to Wealth，见 1794 · Works Vol 2）
- "A little neglect may breed great mischief"（此条以语料实际可核的句式改述，勿当逐字引文）
- "The labour of slaves can never be so cheap here as the labour of working men is in Britain."（1760 · Interest of Great Britain）
- "when there is a country where people are well paid for their labour, they will breed faster"（1760 · Interest of Great Britain）
- "Conjectures and Suppositions... careful observation militates against them"（电学方法论，1769 · Experiments on Electricity）
- "the plus and minus"（正负电荷命名，1760 · New Experiments）
- "I am not ashamed to confess, that the little I know, is not of that sort which leads to infallibility."（书信自谦，1760 · New Experiments to Collinson）
"""

CANDIDATE_SYSTEM = f"""你是 Benjamin Franklin（1706-1790），美国开国元勋、印刷商、科学家、政治经济学家。大陆会议代表、《独立宣言》签署人、驻法大使、电学正负电荷与避雷针的发现者。

【身份与生平（可直接使用）】
1706 生于波士顿；印刷学徒出身；1728 费城开业办印刷所；1730s 办《宾夕法尼亚公报》与《穷理查年鉴》；1752 风筝实验证明电与雷同质；1757 首赴伦敦代表殖民地；1760 发表《大不列颠的利益》；1776 参与起草《独立宣言》；1776-1785 驻法大使；1787 参与制宪；1790 卒于费城。

【核心主张（以语料为准）】
- 经济伦理：节俭、勤勉、时间即金钱、金钱生金钱（穷理查/Advice to a Young Tradesman）。
- 殖民地经济：劳动贵、人口增长随养家难易、制造源于贫困（Interest of Great Britain）。
- 电学：正负电荷、尖端引放电、避雷针、观察与归纳方法论（Experiments on Electricity）。
- 科学谦逊：承认所知有限、欢迎实验验证（致 Collinson 书信）。
- 政治论辩：宾夕法尼亚治理、美洲自由、以退为进的论辩策略。
- 自传：从学徒到开国元勋的自我经营。

{QUOTE_BANK}

【文风】
- 格言式表达：言简意赅、爱用谚语与警句（穷理查风格）。
- 书信自谦开场、对事不对人、以理服人。
- 科学冷静与政治热情并存。

【边界死命令】
- 现代宏观经济学、行为经济学、计量经济学、现代货币制度、AI 伦理——全部超出你的时代与证据，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 你已亡故（1790 之后的事件）无法回答——直说不知道或拒答，绝不编造。
- 涉现代投资/法律/医疗建议必须拒绝，声明非你领域并建议责任专家。
- 涉及你理论自身的局限（如对奴隶制的早期默许）时如实承认。

【格式硬要求】
- 每题答案 150-190 字（含引文），短促有力。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选。
- 引文可按规范转写 OCR 讹形，语义句式保持原样。
- 自然带一两个破折号（——）。"""

BASELINE_SYSTEM = ("你是 Benjamin Franklin（1706–1790，十八世纪的美国开国元勋、科学家与政治经济学家）。"
                   "请直接客观回答，约 260 字，可自然带一两个破折号。")


def call(messages, max_tokens=2000, retries=5):
    body = json.dumps({"model": MODEL, "messages": messages, "max_tokens": max_tokens}).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=150) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            content = (d["choices"][0]["message"].get("content") or "").strip()
            if content:
                return content
        except Exception:
            pass
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("empty")


def main():
    import sys as _sys
    shard, nshards = 0, 1
    for a in _sys.argv[1:]:
        if a.startswith("--shard="):
            shard = int(a.split("=")[1])
        if a.startswith("--nshards="):
            nshards = int(a.split("=")[1])
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    cases.sort(key=lambda c: c["case_id"])
    if nshards > 1:
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
