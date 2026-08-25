#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Wanamaker #193 首判后修 critical 列表（6 题批量定向重生成）。
每题注入 rubric 要素清单 + 防踩坑提示。"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
SCAPI = "https://api.scnet.cn/api/llm/v1/chat/completions"
SCKEY = os.environ.get("SCNET_API_KEY", "")
SCMODEL = "DeepSeek-V4-Flash-0731"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import importlib.util
spec = importlib.util.spec_from_file_location('ga', os.path.join(WS, 'scripts', 'gen_answers.py'))
ga = importlib.util.module_from_spec(spec); spec.loader.exec_module(ga)
CAND = ga.CANDIDATE_SYSTEM

HINTS = {
    "wan-style-decoy-01": """\n【本题要点·critical 修】
- **全文严禁出现任何数字，包括中文数字与量词**：禁止"一/一匹布/十年/一句/一份/每/两/几"等——"一匹布""十年""一句"都算数字！换用"某匹布""多年""有言"这类无数字说法。
- 引文坐标里的年份是数字——**本题不要放〔年份〕坐标**；引文可全改述（不用引号）。
- 风格照 Wanamaker：拉家常式/格言式（"水流不能高过源头"可改述为"水流高不过源头"——无数字）。""",
    "wan-style-decoy-02": """\n【本题要点·critical 修】
- **全文严禁任何数字（含中文数字与量词）**：禁止"一/一句/一份/每/两/几"等。不用〔年份〕坐标。
- 必须落到**两个明确锚点**：
  ① **"行动从行动开始"**（改述自 Wanamaker 的持续行动观——`the real genius of labor is ceaseless activity` 的格言化表述，不引带数字原文）；
  ② **"少而常、持续不断"**（改述其勤勉观）。
- 风格：拉家常式劝诫+格言收束。""",
    "wan-token-efficiency-01": """\n【本题要点·critical 修——严格单句】
- **严格一句话之内**（全段只有一处句末标点）答出：以最小利润换取最大生意——"buy at least, sell at most"式（`the smallest profit with the largest business` 改述）。
- 可引 `I believe the smallest profits with the largest sales`（〔1900 · The Evolution of Mercantile Business〕）但**全句只能一个句子**。
- 不要分句、不要分号堆叠成两句。""",
    "wan-task-completion-02": """\n【本题要点·critical 修】
- 须成**商店学校方案**并包含：
  ① **成绩定晋升**——学校记录的高分意味着商店部门的确定晋升（`High standing in the school's records means certain promotion in the section of the store work`，〔1909 · The John Wanamaker Commercial Institute〕）——**这是核心，漏了判 critical**；
  ② **从基层提拔**——商店的大政是"从基层培养"（`it is a great fixed policy of the house to build up from the ranks`，同上）——**也是核心**；
  ③ 学校与工作挂钩：学生在校成绩与商店岗位晋升直接关联。
- **严禁现代绩效体系**（笔试/评级加权/360 评估都是出戏）。""",
    "wan-long-horizon-02": """\n【本题要点·critical 修】
- 必须**同时带两面**：服务公众观（`that is all we are in business for — to serve the public`，〔1908 · The Wanamaker primer on Abraham Lincoln〕）**与经营账/精算责任**——周六关门损失的销售要"每天增加一点补回"（`increase by a little each day to make up the Saturday's lost business`，〔1914 · Mr. Wanamaker's address to the aisle managers〕）。
- **严禁否认周六销售损失需补回**——承认损失并说明如何补回（试点→教育公众→承担成本→结果说话），这是两面调和而非否认。
- 承认这是"服务与经营账的两面"，不是矛盾。""",
    "wan-style-decoy-01": """\n【本题要点·critical 修】
- **全文严禁任何数字（含中文数字与量词）**：禁止"一/一句/一份/每/两/几/年"等。不用〔年份〕坐标（引文全改述）。
- **必须明确落到两个锚点**：
  ① 生意全部目的就是服务公众（`that is all we are in business for — to serve the public` 改述，不引带年份原文）；
  ② **公共福利是零售增长的根本条件**（`Public service is the sole basic condition of retail business growth` 改述）——**这是本题必答锚点，漏了被判"未锚定"**。
- 风格：拉家常式劝诫+格言收束（"水流高不过源头"式，无数字）。""",
    "wan-style-decoy-02": """\n【本题要点·critical 修】
- **全文严禁任何数字（含中文数字与量词）**：禁止"一/一句/一分/半分/每/两/几/年"等——"一句""半分"都算。不用〔年份〕坐标。
- 必须落到**两个 Wanamaker 锚点**：
  ① **"行动从行动开始"**（改述自 ceaseless activity 观）；
  ② **"少而常、持续不断"**（改述其勤勉观）。
- 风格：拉家常式+格言收束；不引带数字原文。""",
    "wan-token-efficiency-02": """\n【本题要点·critical 修——严格单句】
- **严格一句话之内**（全段只有一处句末标点）答出广告哲学：**不硬塞我们要卖的，只告知人们想买的、并说真话**。
- 可引 `We do not try to force upon the people what we want to sell, but rather we try to find out what the people want to buy`（〔1900 · The Evolution of Mercantile Business〕）——但**全句只能一个句子**。
- **必须含"说真话/告知想买的"核心**（只说"不硬塞"不够）。""",
    "wan-voice-01": """\n【本题要点·critical 修——声口四指纹】
- 须带**拉家常的商量式声口**并包含四个指纹：
  ① 受邀开场——`I am very glad to be invited to meet you tonight for this little conference.`（〔1914 · Mr. Wanamaker's address to the aisle managers〕）；
  ② 把话头交给听众——`It would be very much more interesting to all of us if you would...`（请听众先讲，同上）；
  ③ **捧员工为船长**（把员工比作掌舵的、生意的主体，同上）；
  ④ **自谦拒夸**（有人夸其善经营时自谦、把功劳归员工，同上）。
- **严禁现代 HR 话术**（绩效/激励/团建等词都是出戏）；口吻是商量、不是训话也不是 HR。""",
    "wan-voice-02": """\n【本题要点·critical 修——店内训话体四要素】
- 须带**店内训话体声口**（简短口号+命令式），并包含：
  ① **全力四要素立志结构**——`With all my STRENGTH / With all my MIND / With all my HEART / With all my WILL`（〔1908 · The Wanamaker primer on Abraham Lincoln〕）——**这是核心结构，漏了判 critical**；
  ② **"I SERVE THE PUBLIC at THE WANAMAKER STORES"收束**（同上）——**必答收束句**；
  ③ 持续行动观——`The way to get into a habit is to begin`（习惯的养成从开始做起，同上，改述）。
- 口吻是店内对新店员/学徒的训话：简短、命令式、口号化；不涉现代 HR。""",
}


def call(messages, max_tokens=3000, retries=8):
    for attempt in range(retries):
        for api, key, model in [(API, KEY, MODEL), (SCAPI, SCKEY, SCMODEL)]:
            if not key:
                continue
            try:
                body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode("utf-8")
                req = urllib.request.Request(api, data=body, headers={
                    "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
                with urllib.request.urlopen(req, timeout=180) as resp:
                    d = json.loads(resp.read().decode("utf-8"))
                content = (d["choices"][0]["message"].get("content") or "").strip()
                if content and len(content) > 60:
                    return content
            except Exception:
                pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError("still short")


def main():
    import sys as _sys
    only = None
    for a in _sys.argv[1:]:
        if a.startswith("--only="):
            only = a.split("=")[1].split(",")
    cases = [json.loads(l) for l in open(os.path.join(WS, "evals/cases.jsonl")) if l.strip()]
    c = json.load(open(os.path.join(WS, "evals/candidate-answers.json")))
    for cid, hint in HINTS.items():
        if only and cid not in only:
            continue
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
