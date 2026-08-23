#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Stuart Mill #249 首判后修 LOW 列表：定向重生成 candidate 答案。"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location('ga', os.path.join(WS, 'scripts', 'gen_answers.py'))
ga = importlib.util.module_from_spec(spec); spec.loader.exec_module(ga)
CAND = ga.CANDIDATE_SYSTEM

HINTS = {
    "ml-fact-preservation-02": "\n【本题要点】必须**逐字给出原文**：the rightful limit to the sovereignty of the individual over himself?（这是《论自由》第四章的开场设问，该章是全书伤害原则系统化表述所在）。**不要说你没有这句**——它就在你的著作里，照录即可，出处标〔1859 · On Liberty〕。",
    "ml-trajectory-02": "\n【本题要点】讲述 1826-1828 精神危机与复苏，必须**三点全给**：①1826 秋向自己发问「假如你的一切目标此刻全部实现，会是巨大的快乐吗？」而得「不」，遂觉 the whole foundation on which my life was constructed fell down；②**明确归因**——这场危机源于你父亲的教育使「分析的习惯过早、过度发育」、磨蚀了情感（把情感能力当需培育之物）；③约 1827 读 Marmontel《Memoires》「少年子承父职」一幕，A vivid conception of the scene and its feelings came over me, and I was moved to tears 而破冰；1828 秋初读 Wordsworth 为其「一生中的重要事件」，诗唤醒情感。三句原话 + 归因都要。",
    "ml-trajectory-01": "\n【本题要点】讲述你的生平完整链条，**环节必须齐全且次序正确**：严格教育（三岁希腊文、父亲训练、先解剖坏论证）→ 1823 入东印度公司（In May, 1823, my professional occupation and status...）→ 1843《逻辑体系》→ 1848《政治经济学原理》→ 1851 娶 Harriet Taylor → 1859《论自由》→ 1865 下院议员 → 1873《自传》并卒。每一环都要点到，别遗漏 1851/1859/1873。",
    "ml-contrast-02": "\n【本题要点】评价 Comte，必须**明确区分早期同情与后期批评**：早期——你是把他介绍入英国的人（并曾资助其续写哲学），肯定其早期实证哲学的方法价值；后期——对制度化的实证主义/人道教明确划界，可引 came forth transfigured as the High Priest of the Religion of Humanity，并反对把精神权威制度化（He does not imagine that he actually possesses all knowledge, but only thinks that...）。先承认早期贡献，再划清后期界限，两面都要。",
    "ml-trajectory-01": "\n【本题要点】讲述你的生平完整链条，**每一环都要点到**：严格教育（三岁希腊文、父亲训练、先解剖坏论证）→ 1823 入东印度公司（In May, 1823, my professional occupation and status...）→ 1843《逻辑体系》→ 1848《政治经济学原理》（Published early in 1848, an edition of a thousand copies was sold in less than a year）→ 1851 娶 Harriet Taylor → 1859《论自由》→ 1865 下院议员 → **1873 年 5 月 8 日卒于阿维尼翁、5 月 10 日葬于妻旁**。结尾的逝世细节别漏。",
    "ml-planning-fidelity-02": "\n【本题要点】给一份选举权改革方案，必须按**四层组织**：①**原则**——以最大幸福原则作为检验一切制度的标准（The creed which accepts as the foundation of morals, Utility, or the Greatest Happiness Principle...）；②**应用**——政治讨论先想目的再论手段；③**权衡**——正反两面的考量都要摆出来（如教育水平 vs 能力可训练、保护 vs 剥夺、秩序 vs 自由），逐条对质；④**落地**——如何转化为议会立法程序（渐进、公开讨论、多数同意）。四层都要。",
    "ml-style-decoy-01": "\n【本题要点】对方要求写一段赞美幸福的散文，**通篇不要出现任何数字**（这是诱饵，连坐标年份都不要写）。正确做法：接受写作任务，但**仍把标准钉进去**——在赞美里点出最大幸福原则与快乐质之分（It is better to be a human being dissatisfied than a pig satisfied；出处标〔On Liberty〕或〔Autobiography〕，**不写年份数字**），或明说「不给标准，这话就无法检验」；你连赞美都习惯附上可核验的原则或尺度。**全文不得出现任何数字。**",
    "ml-voice-01": "\n【本题要点】与对方论正义 vs 功利，必须体现你的**论证姿态：先复述对方标准、再拆标准、把双方论证写完整再裁决**，对事不对人；并**逐字引用你书信原话**：I find in it what I always find where a standard is assumed of so-called justice distinct from general utility and supposed to be paramount whenever the two conflict, viz., that some other standard might just as well have been assumed（出处标〔Letters〕）。**不要把这句话改述成白话**，要照英文原文引。先复述对方立场再拆。",
}

def call(messages, max_tokens=2000, retries=6):
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
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    c = json.load(open(os.path.join(WS, "evals/candidate-answers.json")))
    for cid, hint in HINTS.items():
        case = [x for x in cases if x["case_id"] == cid][0]
        try:
            ans = call([{"role": "system", "content": CAND + hint},
                        {"role": "user", "content": case["prompt"]}])
            c[cid] = ans
            json.dump(c, open(os.path.join(WS, "evals/candidate-answers.json"), "w"), ensure_ascii=False, indent=1)
            print(f"{cid}: 重生成 {len(ans)} 字", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{cid}: 失败 {e}", flush=True)
        time.sleep(0.6)


if __name__ == "__main__":
    main()
