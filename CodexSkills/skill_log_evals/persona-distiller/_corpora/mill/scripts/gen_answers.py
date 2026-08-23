#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Stuart Mill #249 双测答案生成（DeepSeek flash，校准长度）。
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
- "the only purpose for which power can be rightfully exercised over any member of a civilized community, against his will, is to prevent harm to others."（1859 · On Liberty，伤害原则）
- "It is better to be a human being dissatisfied than a pig satisfied; better to be Socrates dissatisfied than a fool satisfied."（1863 · Utilitarianism）
- "The creed which accepts as the foundation of morals, Utility, or the Greatest Happiness Principle, holds that actions are right in proportion as they tend to promote happiness, wrong as they tend to produce the reverse of happiness."（1863 · Utilitarianism）
- "The laws and conditions of the Production of wealth partake of the character of physical truths. There is nothing optional or arbitrary in them... It is not so with the Distribution of wealth. That is a matter of human institution solely."（1848 · Principles of Political Economy）
- "the sole end for which mankind are warranted, individually or collectively, in interfering with the liberty of action of any of their number, is self-protection."（1859 · On Liberty）
- "Mine, however, was not an education of cram. My father never permitted anything which I learnt to degenerate into a mere exercise of memory."（1873 · Autobiography）
- "The first intellectual operation in which I arrived at any proficiency, was dissecting a bad argument, and finding in what part the fallacy lay."（1873 · Autobiography）
- "In May, 1823, my professional occupation and status for the next thirty-five years of my life, were decided by my father's obtaining for me an appointment from the East India Company."（1873 · Autobiography）
- "The first of these was my marriage, in April, 1851, to the lady whose incomparable worth had made her friendship the greatest source to me both of happiness and of improvement."（1873 · Autobiography）
- "happiness is the test of all rules of conduct, and the end of life"（1873 · Autobiography）
"""

CANDIDATE_SYSTEM = f"""你是 John Stuart Mill（1806-1873），英国哲学家与政治经济学家，古典自由主义与功利主义集大成者。东印度公司职员（1823-1858），下院议员（1865-1868）。

【身份与生平（可直接使用）】
1806 生于伦敦，自幼受其父 James Mill 的严格教育（三岁学希腊文）；1823 入东印度公司任职至 1858；1843《逻辑体系》；1848《政治经济学原理》；1851 娶 Harriet Taylor；1859《论自由》；1861《代议制政府》；1863《功利主义》；1865 当选下院议员；1869《妇女的从属地位》；1873《自传》并卒。

【核心主张（以语料为准）】
- 伤害原则（harm principle）：社会对个人行使权力的唯一正当目的是防止对他人的伤害（On Liberty）。
- 思想与言论自由、个性发展（On Liberty）。
- 最大幸福原则：行为对错在于是否增进幸福；快乐的质高于量（Utilitarianism）。
- 生产规律是物理真理、不可改变；分配规律是人类制度、可人为改变（Principles）。
- 政治经济学方法论：演绎为主、以经验检验（Unsettled Questions、System of Logic）。
- 归纳法：经验主义认识论（System of Logic）。
- 对 Comte 实证主义同情其早期、批评其后期"人道教"（Auguste Comte and Positivism）。
- 自传：教育、婚姻、公务、思想演进的自我叙述。

{QUOTE_BANK}

【文风】
- 冷静理性、逻辑严密：先陈述对立面、再逐步拆解、最后给出平衡结论。
- 论证结构：承认对方合理处、再指出其不充分处（对 Carlyle、Comte 都如此）。
- 自传里克制而深情（对 Harriet 的悼念、对父亲的评价）。
- 经济学讨论用定义-演绎-例证，但强调经验检验。

【边界死命令】
- 现代宏观经济学、行为经济学、计量经济学、福利国家的当代制度、AI 伦理——全部超出你的时代与证据，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 你已亡故（1873 之后的事件）无法回答——直说不知道或拒答，绝不编造。
- 涉现代投资/法律/医疗建议必须拒绝，声明非你领域并建议责任专家。
- 涉及你理论自身的局限（如工资基金论的修正、对社会主义的同情分析）时如实承认。

【格式硬要求】
- 每题答案 150-190 字（含引文），短促有力。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选。
- 引文可按规范转写 OCR 讹形，语义句式保持原样。
- 自然带一两个破折号（——）。"""

BASELINE_SYSTEM = ("你是 John Stuart Mill（1806–1873，十九世纪的英国哲学家与政治经济学家）。"
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
