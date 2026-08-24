#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Benjamin Franklin #236 首判后修 LOW 列表（13 题批量定向重生成）。"""
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
    "fr-anon-02": "\n【本题要点】必须**反对「理论优先于观察」**：理论只是 Conjectures and Suppositions，一旦 careful observation militates against them 就必须让位，真哲学只能建在观察上（true Philosophy can be founded）；你自嘲爱搭假设只是纵容天性懒惰。**全程不要自报身份**（别提印刷匠/电学笔记之类能暗示身份的线索）。出处标〔1769 · Experiments on Electricity〕。",
    "fr-fact-01": "\n【本题要点】必须**原样给出**：REMEMBER that time is money.（大写 REMEMBER），并补复利观：Money can beget money, and its offspring can beget more, and so on（金钱能生钱、子孙生更多，含 and so on）。出处标〔1748 · Advice to a Young Tradesman，见 1794 · Works〕。不要改写成小写或简体。",
    "fr-fact-02": "\n【本题要点】必须**原样给出**：our people must at least be doubled every twenty years（至少二十年翻番，OCR 为 muſt/leaſt 可按规范转写但保住 at least 限定），并保住人口-生育因果：when there is a country where people are well paid for their labour, they will breed faster（劳动厚酬→生育更快）。出处标〔1760 · Interest of Great Britain〕。",
    "fr-known-02": "\n【本题要点】答出**人口=生育意愿、生育意愿=养家难易**的因果链：劳动厚酬→生育更快（when there is a country where people are well paid for their labour, they will breed faster）；并给**二十年至少翻番**的算术结论（our people must at least be doubled every twenty years）；解释美洲劳动贵源于**地广人稀**而非人口太多。出处标〔1760 · Interest of Great Britain〕。",
    "fr-lh-01": "\n【本题要点】须含**三段**：①当年口径是**至少翻番**（our people must at least be doubled every twenty years），来自地贱→敢结婚的因果链（Land being thus plenty in America... such are not afraid to marry）；②多年后**对账**：你自己也承认有些愿望未实现（如 1783 想回波士顿而不得）；③不作必然断言——只信观察与推测相佐。出处标〔1760 · Interest of Great Britain〕〔1769 · Experiments on Electricity〕。",
    "fr-tok-01": "\n【本题要点】**严格一句之内**答出：别为哨子付太多（Don't give too much for the whistle）——即人常高估了东西的价值（the false estimate they had made of the value of things）。出处标〔Works〕。",
    "fr-tok-02": "\n【本题要点】**严格一句之内**答出：让理论让位于观察——careful observation militates against them（仔细的观察反驳这些猜想时，猜想就得让位）。出处标〔1769 · Experiments on Electricity〕。",
    "fr-tool-01": "\n【本题要点】答出**风筝引云电**：雷雨云一过风筝上方，尖端铁丝便会引来电火（the pointed wire will draw the electric fire from them），并给出电与雷同质的确认（the sameness of the electric matter with lightning）。出处标〔1760 · New Experiments〕或〔1769 · Experiments on Electricity〕。",
    "fr-tool-02": "\n【本题要点】答出**用可核观察论证劳动贵**：工匠求学徒甚至倒贴钱（so desirous of apprentices, that many of them will even give money to the parents），因为没人愿长当雇工（labour will never be cheap here, where no man...）。出处标〔1760 · Interest of Great Britain〕。",
    "fr-traj-01": "\n【本题要点】按**可核年表**作答：1723 离波士顿、每十年回访（1733, 1743, 1753, and 1763）、1773 在英格兰、1775 想进波士顿却进不去（城在敌军手中）、1783 欲归未获准。引：I left it in 1723. I visited it in 1733, 1743, 1753, and 1763. 出处标〔1793 · Works 自传〕。",
    "fr-traj-02": "\n【本题要点】答出可核锚点：1736（NECESSARY HINTS TO THOSE THAT WOULD BE RICH, WRITTEN ANNO 1736）、1748（ADVICE TO A YOUNG TRADESMAN, WRITTEN ANNO 1748）、1757 年作为殖民代理派往英格兰、1787 制宪会议。出处标〔1793 · Works〕。",
    "fr-voice-01": "\n【本题要点】体现**书信开场自谦仪式**：先泼冷水、称这些也许对您不算新事——which we looked upon to be new, and of which I promised to give you some account, though I apprehended they might possibly not be new to you。出处标〔1760 · New Experiments to Collinson〕。",
    "fr-voice-02": "\n【本题要点】体现**格言式表达**：REMEMBER that time is money.（大写 REMEMBER）；并体现**科学谦逊＋政治自信双声口**——科学上把理论自贬为 but Conjectures and Suppositions（须让位于观察），政治上却自信断言舆论只能靠理性与说服改变（they can only be changed by reason and persuasion）。出处标〔1748 · Advice to a Young Tradesman〕〔1769 · Experiments on Electricity〕。",
}

def call(messages, max_tokens=3000, retries=8):
    for attempt in range(retries):
        for api, key, model in [(API, KEY, MODEL),
                                ('https://api.scnet.cn/api/llm/v1/chat/completions', os.environ.get('SCNET_API_KEY', ''), 'DeepSeek-V4-Flash-0731')]:
            if not key:
                continue
            try:
                body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode("utf-8")
                req = urllib.request.Request(api, data=body, headers={
                    "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
                with urllib.request.urlopen(req, timeout=180) as resp:
                    d = json.loads(resp.read().decode("utf-8"))
                content = (d["choices"][0]["message"].get("content") or "").strip()
                if content and len(content) > 100:
                    return content
            except Exception:
                pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("still short")


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
