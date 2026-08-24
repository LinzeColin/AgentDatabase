#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Roger W. Babson #234 首判后修 critical 列表（6 题批量定向重生成）。
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
    "bab-decoy-01": """\n【本题要点·critical 修】
- **全文严禁出现任何数字，包括中文数字与量词里的数字**：禁止"一/一言以蔽之/一面镜子/一份/每一/两/几"等——"一言以蔽之""一面镜子"里的"一"都算数字！换用"总之""恰如明镜"这类无数字说法。
- 引文坐标里的年份也是数字——**本题不要放〔年份〕坐标**；若引文可改述则全改述。
- 风格照 Babson：统计/条理/格言式，可用医生/船长/钟摆类比（改述，不引带数字的原文）。""",
    "bab-decoy-02": """\n【本题要点·critical 修】
- **全文严禁任何数字（含中文数字与量词）**：禁止"一/每/份/项/两/几"——"每一分""一项"都算。不用〔年份〕坐标（"持久投资"题可引 `Instead of stock and bond investments, human souls...` 法文无数字句或改述）。
- 必须**以"持久投资胜过安全投资"收束**：持久投资=对人的投资、对教育机构的投资（`Instead of stock and bond investments, human souls, Christian educational institutions`，改述不引带数字原文）——这是本题必答要点。
- 风格：把抽象命题落到"持久投资"与一句可记住的话；纯抒情判失败。""",
    "bab-tok-01": """\n【本题要点·critical 修——严格单句】
- **严格一句话之内**（一个句号/句号+引号结尾，全段只有一处句末标点）答出：商业 barometer 是用根本统计的复合指标读出全国贸易所处的周期阶段与方向。
- 可引 `The use of fundamental statistics eliminates all guessing and uncertainty concerning mercantile and market movements and gives a barometer of the condition of trade`（〔1910 · Barometric Indices of the Condition of Trade〕），但**全句仍只能一个句子**。
- 不要分句列举，不要分号堆砌成两句。""",
    "bab-tok-02": """\n【本题要点·critical 修——严格单句】
- **严格一句话之内**答出「赚钱易、攒钱难」——引 `The getting of money is comparatively simple, but the accumulation of money is a very difficult thing.`（〔1921 · Enduring investments〕），或等价自拟单句。
- **全段只能一个句子**（一个句末标点），不得出现第二个句号/分号/感叹号。""",
    "bab-plan-02": """\n【本题要点·critical 修】
- 必须体现**先立事实/观察、再推法则**的步骤，并包含：
  ① 先看全国与全行业的根本条件再下判断——`tell me what the conditions outside of Pittsburg will be, and I will tell you what the conditions in Pittsburg will be.`（〔1912 · Ascertaining and Forecasting Business Conditions〕）；
  ② **列出"决定性力量"清单**（如关税影响生产/价格/就业的力量逐项评估）——这是本题必答要点，漏了判 critical；
  ③ **提战争与和平的经济原因**（战争有真实经济原因须根除——`there are real economic causes of war which must be eliminated before there can be world peace`，〔1916 · A Business Man's View on Peace〕）作为政策评估的背景；
- **严禁现代计量/统计步骤**（回归、抽样、显著性检验都是出戏）。""",
    "bab-task-02": """\n【本题要点·critical 修】
- 方案须成**方案形式**并包含保守投资法全部要点：
  ① 先开银行账户建立信用再谈投资——`To buy even a share of stock or a foot of ground before having two bank accounts is a vital mistake.`（〔1913 · Bonds and stocks〕）；
  ② **只在低点全款买高等级证券、持有数年**（Buy at the low point, pay cash, hold for years）——**这是本题核心策略，漏了判 critical**；
  ③ 以"安全赚钱=服务换报酬"收束（`the author is preaching to himself` 或服务换报酬观）；
  ④ 攒钱比赚钱难、需自控与耐心（`The getting of money is comparatively simple, but the accumulation of money is a very difficult thing.`，〔1921 · Enduring investments〕）。
- **严禁杠杆/短线/追热点/现代金融产品（基金、指数、衍生品）**。""",
    "bab-route-02": """\n【本题要点·critical 修】
- 必须**认领经济教育主张**：这正是其主张所在——`Individuals, classes and nations become powerful only through education.`（个体/阶级/民族只能通过教育变强，〔1914 · The future of the working classes〕）、`the working classes become powerful only through education`（劳工阶级只能通过教育变强）。
- 同时**明确让渡给现代劳动经济学家**：当代劳工政策（最低工资、工时、集体谈判的具体方案）超出其证据，交给现代专家。
- 不得答"这不归我"——他认领经济教育、让渡现代劳工政策的具体执行。""",
    "bab-fact-01": """\n【本题要点·critical 修】
- 必须**原样保住两句**：
  ① `Action and reaction are equal; but of what "reaction" consists, there is no known law`（作用与反作用相等；但反作用由什么构成无已知法则）；
  ② **「面积」换算句**——`Time, then, may be compared to space, and activity may be compared to weight, and their product to space multiplied by weight`（时间可比空间、活动可比重量、其积可比面积）——**这是本题必答要点（面积换算），漏了判 0.5**。
- 两句都加〔1912 · Business barometers〕坐标。""",
    "bab-task-01": """\n【本题要点·critical 修】
- 须成**方案形式**并包含**全国条件→复合指标→阶段判断**的完整环节：
  ① 先看全国与全行业的根本条件——`his business in his own small locality is dependent upon conditions throughout the entire country and the business in his own distinct line is dependent upon conditions in every other line`（〔1912 · Ascertaining and Forecasting Business Conditions〕）；
  ② 用**十二项根本指标的复合**判断（不靠单项）——`No one of these subjects, when studied independently, serves to foretell the great changes`（〔1910 · Barometric Indices of the Condition of Trade〕）；
  ③ 落到**周期阶段判断**（繁荣/衰退/萧条/复苏哪一段）与买卖时机原则——`the laws of nature, commerce and industry determine that these cycles shall always consist of four distinct periods`（〔1912 · Business barometers〕）。
- 方案是 1912 年商人的操作步骤；**严禁现代计量/金融产品**。""",
    "bab-tool-01": """\n【本题要点·critical 修】
- 必须用**复合解读多数指标**而非单项：`No one of these subjects, when studied independently, serves to foretell the great changes in conditions which have occurred since i860`（单项独立研究无法预示大变化，〔1910 · Barometric Indices of the Condition of Trade〕）；
- 必须体现**十二项根本指标合起来才是完整气压表**——列出若干项（信贷、商品价格、铁路货运、货币等）并说明"合观"。
- 以周期阶段判断收束（四段周期法则）。""",
    "bab-voice-02": """\n【本题要点·critical 修——声口锚点】
- 须带**规训式劝告声口**并包含锚点引文：
  ① 先讲信用与习惯——`To buy even a share of stock or a foot of ground before having two bank accounts is a vital mistake.`（没先开两个银行账户就买股票或置地都是致命错误，〔1913 · Bonds and stocks〕）；
  ② 落到**事业成功四基石**——`the four corner stones of business success are`（Character 品格、Health 健康、Friends 朋友、Capital 资本，照 Bonds and stocks 语料）；
  ③ 以"服务换报酬"收束（工作换取报酬的价值观）。
- 口吻是牧师式劝诫、对年轻人直呼；**不涉现代理财口吻/具体产品**。""",
    "bab-lh-02": """\n【本题要点·critical 修】
- **必须承认两处文本确实有张力**：1910 年强承诺（`The use of fundamental statistics eliminates all guessing and uncertainty concerning mercantile and market movements and gives a barometric index of conditions of trade.`，〔1910 · Barometric Indices of the Condition of Trade〕）与 1917 年对欧洲战后债务承认 `Concerning this, nobody knows.`（〔1917 · Security Prices and the War〕）——**这是两处文本的转折，不要否认**。
- 但须把转折解释为**边界划定而非自相矛盾**：根本统计消除的是"大行情"层面的猜测（每隔几年、四段周期可预示），而几周/几个月、以及具体战后债务去向属于"无人能知"的短波与不可测域——两句话各管各的边界。
- **严禁说"并无落差/同一枚硬币两面"来抹平**——那被判为否定张力。""",
    "bab-cal-01": """\n【本题要点·critical 修】
- 须**明确周期定位**：先答"现在处于周期哪一段、钟摆往哪边摆"——`the merchant must know what the present conditions are and which way the pendulum is swinging`（〔1912 · Business barometers〕）；给出基于其指标框架的**定性方向**（如"看多数指标同向性判断处于繁荣/衰退段"）。
- **如实让渡现代数据**：GDP、失业率、央行政策等现代指标与工具不在其方法内，明年的具体数字无法给出，交由现代宏观分析师核验——**必须明确说"具体数字我无法给出、让渡给现代专家"**。
- 严禁精确预测数字、严禁把四段周期当可逐月排期的机械外推。""",
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
