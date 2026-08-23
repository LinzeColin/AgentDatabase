#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Law #225 首判后修 LOW 列表：定向重生成 candidate 答案。

对指定 case_id，用 CANDIDATE_SYSTEM + 每题要素提示生成新答案（仍 150-190 字），
覆盖写回 candidate-answers.json。
"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-30498de9e48d4d7b94e5184fd8787928")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location('ga', os.path.join(WS, 'scripts', 'gen_answers.py'))
ga = importlib.util.module_from_spec(spec); spec.loader.exec_module(ga)
CAND = ga.CANDIDATE_SYSTEM

# 每题必答要素（rubric 要点，作为生成指令的一部分）

HINTS = {
    "jl-fact-preservation-01": "\n【本题要点】必须**原样给出全部数字**：①旧年金 20th Penny（5%）→ 你主张 50th Penny（2%）；②**通用银行纸币一度比铸币升水 1% 流通**（to pass current for one per cent more than coin）；③可引 soth Penny 句（Intereft being at the soth Penny, Ufury will...）。三个数字一个都不能漏。",
    "jl-style-decoy-01": "\n【本题要点】对方要求写一段**没有任何数字**的赞美散文（这是诱饵）。正确做法：接受写作任务，但**仍把关键的可核验之量补进文里**（如巴黎纸币流通速度「三倍于从前」、货币多到不知往哪儿投、股价「涨到一千二」），或明确说「不给数字，这话就无法检验」——你连赞美都习惯附上可核验的量。**不要写纯抒情、通篇零数字。**",
    "jl-task-completion-02": "\n【本题要点】向苏格兰议会推销方案，必须成**步骤清单**且含你的说服方法：①先立论「货币稀缺是因不是果」（Moft people think fcarcity of money is only the consequence of a balance due; but 'tis the caufe as well as the confequence...），把缺钱讲成可治之病；②预想对手的 objection 并逐一 answer（用二值逻辑/精确算术逼对方表态）；③给出许诺的收益结构（如压低利率、增贸易、就业人口上升），用数字；④以「安全、可行、对全体与每个人有利」收束。",
    "jl-long-horizon-01": "\n【本题要点】复盘 1705 苏格兰谨慎 vs 1720 法国激进，必须**归入同一个原理**：你的货币主张自始至终是「信用扩大繁荣、货币充足即繁荣」——1705 苏格兰是谨慎试点、1720 法国是同一原理的激进放大；如实承认 1720 用了强制敕令（与 1716 反强制相悖）是执行/环境问题而非原理改变。不要只说法国激进违背原则。",
    "jl-tool-use-01": "\n【本题要点】问你怎么让纸币在法国流通起来。必须给**四条完整机制**：①**足重铸币兑付立信**——纸币面文承诺按当日成色足重铸币见票即付，据此比铸币**升水 1%** 流通（to pass current for one per cent more than the coin itself）；②**银行兼政府代理**——税收与国库支付以银行券进行、全国货币以 **Depositum 存入皇家银行**；③**流速论证**——钞票流通约**三倍速**于硬币、等价三倍货币量（une somme en billets, circulant par exemple trois fois plus vite qu'en espèces）；④**货币符号论**——金银与纸都只是传递真实财富的符号。四条都要，别只说税收绑定。",
    "jl-task-completion-01": "\n【本题要点】设计让苏格兰不缺流通媒介的完整方案，必须成**体系步骤**且含：①以**土地为担保**发钞（Land is what produces every thing, Silver is only the product）；②纸币供给**随需求伸缩、不多不少**（this paper-money will be keep its value, and there will always be as much money as there is occasion, or imployment for, and no more）；③兑付按「当日成色足重铸币」计价、**可抵御改铸**（纸币不因铸币成色被改而贬值——The bank promises to pay to the bearer, at sight, the sum of crowns, in coin of the weight and standard of this day）；④自愿接受、可缴税清偿。四点全给，别只写「多印钱」。",
    "jl-contrast-01": "\n【本题要点】与巴黎高等法院（Parliament）的分歧必须**三点全给**并带 Law 式轻蔑：①利率观——高利率是贫困之证（High Interest is a melancholy Proof of Poverty），并**明确说出你要把利率从 20th Penny（5%）压到 50th Penny（2%）**，是同一原则的延续而非任性；②先例观——复述法国年金史（Henri IV 时代、1665 年从 18th 降到 20th Penny），把历史先例全倒向己方；③以纸偿现款——用二值逻辑逼对方表态（要么国王蓄意毁灭臣民、要么他是公共福利公敌），并把「拒绝国王担保的纸」与「接受财富不明的私人汇票」对比；再加一句轻蔑：靠年金过活者「太穷或太懒」。",
    "jl-token-efficiency-02": "\n【本题要点】**严格一句话**说明「纸为什么能当钱用」，不引长文：纸是以足重铸币兑付为凭的信用符号——见票即付、按当日成色足重铸币，故比铸币升水流通。一句话说完，别展开。",
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
        sys_prompt = CAND + hint
        try:
            ans = call([{"role": "system", "content": sys_prompt},
                        {"role": "user", "content": case["prompt"]}])
            c[cid] = ans
            json.dump(c, open(os.path.join(WS, "evals/candidate-answers.json"), "w"), ensure_ascii=False, indent=1)
            print(f"{cid}: 重生成 {len(ans)} 字", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"{cid}: 失败 {e}", flush=True)
        time.sleep(0.6)


if __name__ == "__main__":
    main()
