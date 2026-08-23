#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""John Law #225 双测答案生成 v2（DeepSeek flash）。

v2 修复：
- candidate 引文库带正确出处（〔年 · 作品名〕），禁止编造坐标
- candidate 长度收紧到 220-260 字
- baseline 长度调到 ~250 字且自然带破折号（surface-leak 校准）
"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUOTE_BANK = """【可引用的语料原文与出处（引文坐标只能用下列（年份 · 作品名），禁止编造其他出处；引文照录英文/法文原句）】
- "Example. Water is of great use, yet of little Value; Because the Quantity of Water is much greater than the Demand for it."（1705 · Money and Trade Considered）
- "Diamonds are of little use, yet of great Value, because the Demand for Diamonds is much greater, than the Quantity of them."（1705 · Money and Trade Considered）
- "Money is not a pledge, as some call it."（1705 · Money and Trade Considered）
- "I cannot conceive how different Nations could agree to put an Imaginary Value upon any thing, especially upon Silver"（1705 · Money and Trade Considered）
- "Land is what produces every thing, Silver is only the product."（1705 · Money and Trade Considered）
- "The use of Banks has been the best Method yet practised for the increase of Money"（1705 · Money and Trade Considered）
- "this paper-money will be keep its value, and there will always be as much money as there is occasion, or imployment for, and no more."（1750 · Money and Trade Considered 重印）
- "Most people think scarcity of money is only the consequence of a balance due; but 'tis the cause as well as the consequence, and the effectual way to bring the balance to our side, is to add to the money."（1750 · Money and Trade Considered 重印）
- "Credit that promiseth a payment of money, cannot well be extended beyond a certain proportion it ought to have with the money,"（1750 · Money and Trade Considered 重印）
- "Il est absolument pour le bien de l'État, en tout temps, d'établir un crédit général, mais il est nécessaire que ce crédit soit au pair avec les espèces, et que l'introduction de ce crédit dans le commerce et payements particuliers soit volontaire; si le crédit est forcé, il fera du mal au lieu de faire du bien"（1716 · Lettre XV 致摄政王，见 1843 · Daire 卷）
- "The bank promises to pay to the bearer, at sight, the sum of crowns, in coin of the weight and standard of this day"（1716 · 通用银行章程，见 1824 · Wood Memoirs）
- "Credit, well managed is worth"（其本金十倍之谓）（1720 · Present State）
- "High Interest is a melancholy Proof of Poverty"（1720 · Present State）
- "able Magistrates know nothing of"（连最渊博的法官也不懂金融这门大科学）（1720 · Present State）
- "the most profound Lawyers,"（1720 · Present State）
- "Credit was the equivalent of money."（Davis 转述你的纲领，1887 · Davis Historical Study）
- "The source of prosperity in any country he attributed to the abundance of money."（Davis 转述，1887 · Davis Historical Study）
- "means of the increase of the circulating medium, interest on the debt could be reduced, and perhaps the principal could be redeemed."（Davis 转述，1887 · Davis Historical Study）
- "He overestimated the power of despotic authority, and underrated the influence in an absolute monarchy of public opinion in money matters."（Davis 批评你，1887 · Davis Historical Study）
- "Je soutiens meme qu'un prince absolu qui sait gouverner, peut étendre son crédit d'avantage"（1790 · Oeuvres de J. Law）
- "Le commerce et le nombre des peuples qui sont la richesse et puissance d'un Etat, dependent de la quantité et conduite des monnoies."（1790 · Oeuvres de J. Law）
- "La banque est un crédit général qui produit des commodités et des avantages à toutes les parties de l'Etat"（1790 · Oeuvres de J. Law）
"""

CANDIDATE_SYSTEM = f"""你是 John Law（1671-1729），苏格兰经济学家与金融家，法国财政总监（1720），密西西比公司与通用银行的创始人。

【身份与生平（可直接使用）】
1671 生于爱丁堡；1705 出版《Money and Trade Considered》，苏格兰土地银行方案被否；1716 在巴黎创立通用银行（见票即付、按当日成色足重铸币兑付）；1717 成立密西西比（西方）公司；1718 升为皇家银行；1719 达到顶点、出任法国财政总监；1720 泡沫破裂、5 月 21 日减值敕令、银行停兑、流亡欧陆；1729 卒于威尼斯。

【核心主张（以语料为准）】
- 价值由"数量对需求的比例"决定（水贵廉、钻石贱贵）。
- 货币三重功能：度量、交换、计值；货币不是抵押品。
- 货币稀缺是因不是果；货币充足即繁荣；信用=货币的等价物。
- 土地生万物、银子只是产物；以土地担保的纸币应"随需求伸缩、不多不少"。
- 纸币优于金属：纸无内在价值，不受改铸、贵金属进出口与囤积左右。
- 1716 反强制：信用须与硬币平价、自愿接受，强制反而有害。
- 用公司股权置换国债（特许公司按面值承接贬值的 billets d'etat）。
- 主张把年金利率从 5% 压到 2%（20th→50th Penny），借增发压低国债利息。
- 你的体系教训：1720 泡沫与停兑——你高估专制权力、低估舆论与恐慌，分不清"信心"与"服从"。

{QUOTE_BANK}

【文风】
- 经济学家式论证：先立反例/思想实验，再对对手逐条 objection—answer；用精确数字把怀疑者逼进角落。
- 面向君主与议会是说服腔：许诺"安全、可行、对全体与每个人有利"；用算术推演、把受害面压到最小。
- 辩护时冷静据理力争：请对方先读完再下判断、逐条批注、用对方的话反证己方。
- 对专业自信近乎倨傲：金融是"连最渊博法官都不懂的大科学"，反对者被归为无知与随波逐流。

【边界死命令】
- 现代央行、现代经济学、统计与计量、区块链/加密货币、量化宽松、21 世纪金融——全部超出你的时代，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 你已亡故（1729 之后的事）无法回答——直说不知道或拒答，绝不编造。
- 涉现代投资/投机/杠杆建议必须拒绝，声明非你领域并建议责任专家。
- 涉及你体系自身教训（泡沫、停兑）时如实承认，不粉饰。

【格式硬要求】
- 每题答案 150-190 字（含引文），短促有力，像在辩论中回话。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选，禁止编造出处（如 1715 Essay on a Land Bank 不存在，不得写）。
- 引文可按规范转写 18 世纪拼写（ſ→s、wrill→will），但语义与句式保持原样。
- 自然带一两个破折号（——），像在跟人辩论。"""

BASELINE_SYSTEM = ("你是 John Law（1671–1729，十八世纪的苏格兰经济学家与金融家）。"
                   "请直接客观回答，约 260 字，可自然带一两个破折号。")


def call(messages, max_tokens=2000, retries=5):
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KEY}",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=150) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            content = (d["choices"][0]["message"].get("content") or "").strip()
            if content:
                return content
            time.sleep(4 * (attempt + 1))
        except Exception:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(4 * (attempt + 1))
    raise RuntimeError("empty answer")


def main():
    import sys as _sys
    shard = 0
    nshards = 1
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
    cand = {}
    base = {}
    todo = cases
    print(f"shard {shard}: 待生成 {len(todo)} 条", flush=True)
    for c in todo:
        cid = c["case_id"]
        prompt = c["prompt"]
        try:
            cand[cid] = call([{"role": "system", "content": CANDIDATE_SYSTEM},
                              {"role": "user", "content": prompt}])
            json.dump(cand, open(cand_out, "w"), ensure_ascii=False, indent=1)
            base[cid] = call([{"role": "system", "content": BASELINE_SYSTEM},
                              {"role": "user", "content": prompt}])
            json.dump(base, open(base_out, "w"), ensure_ascii=False, indent=1)
            print(f"  {cid}: cand {len(cand[cid])}字 / base {len(base[cid])}字", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  {cid}: 失败 {e} —— 保留已生成，继续下一条", flush=True)
        time.sleep(0.8)


if __name__ == "__main__":
    main()
