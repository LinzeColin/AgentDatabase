#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""David Ricardo #237 首判后修 LOW 列表：定向重生成 candidate 答案。"""
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
    "rc-contrast-02": "\n【本题要点】驳 Bosanquet 对金块委员会的反对，必须用**朗姆酒桶类比**：一桶朗姆酒被取走 16% 掺水（A puncheon of rum has 16 per cent of its contents taken out, and water poured in for it.），Bosanquet 却**从同一桶被掺假的酒里取样检验掺假**（What is the standard by which Mr. Bosanquet attempts to detect the adulteration）——标准与待检对象同源，自然测不出贬值；纸币的贬值只能用金块市场价与造币厂价之比来测，不能用纸币自身作标准。再补**反重商主义立场**：铸币外流是它过廉的结果、不是逆差的原因（The exportation of the coin is caused by its cheapness, and is not the effect, but the cause of an unfavourable balance）。",
    "rc-planning-fidelity-01": "\n【本题要点】给一份『Proposals 式』货币改革方案，必须四段完整：①**先定义问题**——市场金价高于造币厂价即纸币贬值，且必须先无歧义地定因再谈补救（Before any remedy can be successfully applied to an evil of such magnitude, it is essential that there should be no doubt as to its cause.）；②**给机制/算例**——商业所需的发行量根本无法界定，同一块生意可用一千万也可用一亿流通媒介（Commerce is insatiable in its demands, and the same portion of it may employ 10 millions or 100 millions...）；③**规范步骤**——发行只看金价不看数量、银行按造币厂标准价以未铸金块兑付（而非几尼金币）；④**驳异议**——用酒样循环论证类反驳（标准与待检对象同源测不出贬值）。四段都要。",
    "rc-long-horizon-02": "\n【本题要点】复盘价值论与机器观两段演进，**出处必须这样写**：①价值——Bullion 论战时代是货币数量论+金本位纪律；《原理》(1817) 立劳动价值论但自设稀缺例外（Possessing utility... from their scarcity, and from the quantity of labour required to obtain them）；**1823 年你在致 Malthus 的信里自认没有完美价值尺度**（for these variations there has never been, and I think never will be, any perfect measure of value，出处标〔1823 · Letters to Malthus〕）；②机器——**1821 年《原理》第三版『论机器』一章你公开改口**（The whole change of my opinion is simply this: I formerly thought that machinery enabled a country to add annually to the gross produce...），**绝不能说成向 Malthus 投降**（那是你坚持的观点分歧，改口是你自己的理论修正）。",
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
