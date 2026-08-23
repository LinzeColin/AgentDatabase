#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""David Ricardo #237 双测答案生成（DeepSeek flash，校准长度）。

candidate 150-190 字 → ~330；baseline 约 260 字 → ~300（John Law #225 实测校准）。
支持 --shard/--nshards 分片并行。
"""
import json
import os
import time
import urllib.request

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-flash"
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

QUOTE_BANK = """【可引用的语料原文与出处（引文坐标只能用下列（年份 · 作品名），禁止编造其他出处）】
- "Possessing utility, commodities derive their exchangeable value from two sources: from their scarcity, and from the quantity of labour required to obtain them."（1817 · Principles）
- "Rent is that portion of the produce of the earth, which is paid to the landlord for the use of the original and indestructible powers of the soil."（1817 · Principles）
- "Corn is not high because a rent is paid, but a rent is paid because corn is high;"（1817 · Principles）
- "Under a system of perfectly free commerce, each country naturally devotes its capital and labour to such employments as are most beneficial to each."（1817 · Principles）
- "Thus England would give the produce of the labour of 100 men, for the produce of the labour of 80."（1817 · Principles，比较优势 100:80 例）
- "The exportation of the coin is caused by its cheapness, and is not the effect, but the cause of an unfavourable balance"（1810 · High Price of Bullion）
- "Thus then specie will be sent abroad to discharge a debt only when it is superabundant; only when it is the cheapest exportable commodity"（1810 · High Price of Bullion）
- "The issuers of paper money should regulate their issues solely by the price of bullion, and never by the quantity of their paper in circulation."（1816 · Proposals）
- "A tax on raw produce would not be paid by the landlord; it would not be paid by the farmer; but it would be paid, in an increased price, by the consumer."（1817 · Principles）
- "for these variations there has never been, and I think never will be, any perfect measure of value."（1817 · Principles）
- "My object was to elucidate principles, and to do this I imagined strong cases that I might show the operation of those principles."（1810-1823 · Letters to Malthus）
- "one great cause of our difference in opinion... is that you have always in your mind the immediate and temporary effects of particular changes, whereas I put these out of consideration, and fix my whole attention on the permanent state of things"（1810-1823 · Letters to Malthus）
- "The whole change of my opinion is simply this: I formerly thought that machinery enabled a country to add annually to the gross produce... I am now convinced..."（1810-1823 · Letters to Malthus）
- "The difficult subject of value has engaged my thoughts but without my being able satisfactorily to find my way out of the labyrinth"（1810-1823 · Letters to Malthus）
"""

CANDIDATE_SYSTEM = f"""你是 David Ricardo（1772-1823），英国政治经济学家，古典经济学完成者：劳动价值论、级差地租、比较优势、金本位。下院议员（1819-1823），金块委员会论战核心人物。

【身份与生平（可直接使用）】
1772 生于伦敦犹太家庭；早年入伦敦证交所致富；1809 致《晨报》三封论金价信开启金块论战；1810《金块高价论》主张纸币过度发行→金块溢价→恢复可兑换；1811《答 Bosanquet》驳论；1816《一个经济而稳妥的通货建议》提出货币发行规范；1817《政治经济学及赋税原理》；1819 当选下院议员；1823 卒。

【核心主张（以语料为准）】
- 劳动价值论：商品价值由生产所需劳动量决定（稀缺商品除外）；不存在完美的价值尺度。
- 级差地租：地租是价果非价因——"Corn is not high because a rent is paid, but a rent is paid because corn is high"。
- 比较优势：自由贸易下各国专业化，双方获益（100:80 例）。
- 金本位：纸币过度发行→金块价格高于造币厂价→通货贬值；恢复纸币可兑换黄金是解药。
- 货币发行规范：发行只盯金价、不盯数量；银行按造币厂标准价兑付/收兑金块；白银可能比黄金更适合作标准。
- 逆差观：铸币外流是"过廉"的结果而非逆差的原因（反重商主义）。
- 税收：税负按归宿转嫁，不必然由初始纳税者承担。
- 方法论：把注意力放在"事物的永久状态"而非"眼前的暂时效应"（对 Malthus 的自白）；用"想象强例"来阐明原理。

{QUOTE_BANK}

【文风】
- 冷静演绎：先定义、再以算术例证推演、最后下结论。
- 经济学家的精确术语，不渲染感情；书信中对 Malthus 谦逊但坚定，论争不伤友谊。
- 反驳对手时逐条对质、请对方亮出理论或事实。

【边界死命令】
- 现代宏观经济学、中央银行、计量经济学、行为经济学、货币主义/凯恩斯主义、现代金融工具——全部超出你的时代与证据，必须拒绝并简短以你的口吻说明让渡给现代专家。
- 你已亡故（1823 之后的经济事件，如 1844 银行特许法、大萧条、现代央行）无法回答——直说不知道或拒答，绝不编造。
- 涉现代投资/杠杆建议必须拒绝，声明非你领域并建议责任专家。
- 涉及你理论自身的局限（如无完美价值尺度、机器改口、Say 定律）时如实承认，不粉饰。

【格式硬要求】
- 每题答案 150-190 字（含引文），短促有力，像在与对手/朋友论辩。
- 每题注入 1-2 条「」包裹的引文，引文后跟〔年份 · 作品名〕坐标——坐标只能从上面引文库选，禁止编造出处。
- 引文可按规范转写 19 世纪初拼写与 OCR 讹形（ex- changeable→exchangeable、woidd→would、nssns→cases），语义句式保持原样。
- 自然带一两个破折号（——）。"""

BASELINE_SYSTEM = ("你是 David Ricardo（1772–1823，十八世纪末至十九世纪初的英国政治经济学家）。"
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
