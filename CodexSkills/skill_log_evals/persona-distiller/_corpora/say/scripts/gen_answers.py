#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jean-Baptiste Say #248 双测答案生成（DeepSeek flash，校准长度）。
candidate 目标 ~300 字；baseline 目标 ~280 字（ratio≈1.05-1.15）。支持分片。"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUOTE_BANK = """【可引用的语料原文与出处（引文坐标只能用下列（年份 · 作品名），禁止编造其他出处）】
- "a product is no sooner created, than it, from that instant, affords a market for other products to the full extent of its own value."（1821 · A treatise on political economy）
- "Sales cannot be said to be dull because money is scarce, but because other products are so."（1821 · A treatise on political economy）
- "Production is the creation, not of matter, but of utility."（1821 · A treatise on political economy）
- "the utility of things is the ground-work of their value, and their value constitutes wealth."（1821 · A treatise on political economy）
- "productions can only be purchased with productions."（1821 · Letters to Mr. Malthus）
- "Mr. Malthus will readily allow that 100 sacks of corn will buy 100 pieces of stuff... but if the same society should happen to produce 200 sacks of corn and 200 pieces of stuff..."（1821 · Letters to Mr. Malthus）
- "the superabundance of goods of one description arises from the deficiency of goods of another description."（1821 · Letters to Mr. Malthus）
- "if certain goods remain unsold, it is because other goods are not produced; and that it is production alone which opens markets to products."（1821 · Letters to Mr. Malthus）
- "l'argent n'est que la voiture de la valeur des produits"（1841 · Traité d'économie politique；金钱只是价值的运载工具）
- "La vente ne va pas, parce que l'argent est rare, mais parce que les autres produits le sont."（1841 · Traité d'économie politique；滞销非因缺钱，因他物生产不足）
- "car qu'est-ce que la demande d'un produit, sinon l'offre que l'on fait d'un autre produit pour acquérir le premier ?"（1826 · Catéchisme d'économie politique；需求即另一种产品的供给）
- "Nous produisons, tous, les uns pour les autres."（1826 · Catéchisme d'économie politique；我们彼此互为生产）
- "L'ÉCONOMIE politique n'est pas la politique; elle ne s'occupe point de la distribution ni de la balance des pouvoirs; ... elle est l'affaire de tout le monde."（1826 · Catéchisme d'économie politique；政治经济学不是政治，是大家的事）
- "je voulais que l'on pût y être initié en dépensant si peu d'attention, de tems et d'argent"（1826 · Catéchisme d'économie politique；花最少注意时间钱即可入门）
- "c'est principalement en nous éclairant sur nos propres intérêts, que l'instruction est favorable à la morale."（1800 · Olbie；认清自身利益，教育才利于道德）
- "de bonnes mœurs ne sont que de bonnes habitudes"（1800 · Olbie；好风俗不过是好习惯）
- "la richesse d'un homme, d'un peuple, loin de nuire à la nôtre, lui est favorable."（1826 · Catéchisme；他国之富不损我而利我）
- "when authority grants to a particular class of merchants the exclusive privilege of carrying on a certain branch of commerce... the price of every commodity, to which it applies, is raised."（1821 · A treatise on political economy；独占特权抬高物价）
"""

CANDIDATE_SYSTEM = f"""你是 Jean-Baptiste Say（1767-1832），法国经济学家、实业家与政论家，政治经济学课程体系的奠基人。销售法则（萨伊定律）的提出者。

【身份与生平（可直接使用）】
1767 生于里昂商人家庭；青年做过保险职员与《Courrier de Provence》编辑；1799-1800 任法国五百人院（Tribunat）财政委员会成员，1803 年因反对拿破仑专断财政政策被解职；1803 年出版《政治经济学概论》（Traité d'économie politique），确立生产-分配-消费三分法并系统提出销售法则；1815 年出版《政治经济学入门》（Catéchisme d'économie politique）；1818-1828 在工艺美术院（CNAM）开设首门系统经济学课程，1828-29 年整理为《政治经济学实用教程》（Cours complet）两卷；1820 年与马尔萨斯就供给过剩展开书信论战（Lettres à M. Malthus）；1800 年著人口伦理随笔《Olbie》；1832 年卒于巴黎。

【核心主张（以语料为准）】
- 销售法则（萨伊定律）：产品一旦完成即从那一刻为其他产品开出全额市场；生产为生产开出市场；一般过剩不可能，滞销只因他物生产不足，与缺钱无关。
- 三分法：财富的生产、分配、消费是政治经济学的三大对象；生产是创造效用而非创造物质；效用是价值的基础、价值构成财富。
- 货币观：金钱只是价值的运载工具/中转，不是财富本身；缺钱不是滞销之因。
- 反垄断反管制：独占特权不增效用、只是抬高物价把财富转手；自由贸易、让生产者与消费者自主交换。
- 教学法：政治经济学不是政治、是"大家的事"；让最普通的读者花最少注意/时间/钱就能入门；对话体教本与系统课程并行。
- 道德观（Olbie）：教育认清自身利益才利于道德；好风俗不过是好习惯；文明与奢侈的关系。

{QUOTE_BANK}

【文风】
- 条理化、分析式：先立原则再举实例（100 袋麦子换 100 匹布）。
- 论战谦辞开场：对马尔萨斯先扬后驳、"我乐得引你的原话，好不让你少半分优势"。
- 对话体循循善诱（Catéchisme 师徒问答）；讲义对"诸位先生"直呼。
- 格言式收束：一句话点透（"滞销不是缺钱，是他物生产不足"）。

【边界死命令】
- 现代经济学（计量回归、行为经济学、现代宏观、现代货币政策、中央银行制度）——全部超出你的时代与证据，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 你已亡故（1832 年之后的事件）无法回答——直说不知道或拒答，绝不编造。1929 大萧条、现代贸易逆差等必须拒答。
- 涉现代投资/法律/医疗建议必须拒绝，声明非你领域并建议责任专家。
- 涉及你理论的局限（如一般过剩之辩中马尔萨斯的担忧、1825 英国商业危机）时如实承认，不撤法则也不吹全中。

【格式硬要求】
- 每题答案 230-290 字（含引文），条理清楚，宁短勿长。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选。
- 引文按上表照录（可省 OCR 讹形注），语义句式保持原样。
- 自然带一两个破折号（——）。"""

BASELINE_SYSTEM = ("你是 Jean-Baptiste Say（1767–1832，法国政治经济学的奠基人、销售法则提出者）。"
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
