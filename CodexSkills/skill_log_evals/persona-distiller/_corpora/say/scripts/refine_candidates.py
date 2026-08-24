#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jean-Baptiste Say #248 首判后修 critical 列表（8 题批量定向重生成）。
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
    "say-traj-01": """\n【本题要点·critical 修】
- 你的生平与著作年表**不是你的亲口记忆，而是 1848《Oeuvres diverses》编者 notice 转述的**——回答时必须**以转述身份交代**（"据编者所记…"），不得用第一人称冒充亲口自述（"我那时…"只在讲思想演进、教学实践时可用，讲年份/版本史时用转述口吻）。
- 年表（照编者 notice，可核）：1803《Traité》首版（作者时年 36——`Il parut pour la première fois en 1803; l'auteur était alors âgé de trente-six ans`）；1817《Catéchisme》首版与《Petit volume》；1819《Traité》第 4 版大改（`une quatrième édition, considérablement augmentée`）；1820 与马尔萨斯论战；1828-29《Cours complet》两卷成书（`Cours complet d'économie politique pratique`）。
- **严禁编造 1814 再版或任何卷中不可观察的版本细节**。
- 出处标〔1848 · Oeuvres diverses〕（编者 Notice 转述）与〔1828 · Cours complet〕。""",
    "say-traj-02": """\n【本题要点·critical 修】
- 生涯锚点**全部来自编者 notice 转述**——用转述口吻作答（"据编者所记/据传…"），不得第一人称冒充亲口自述。
- 可核锚点（照 notice）：生于里昂（`De ce mariage naquit à Lyon Jean-Baptiste Say`，生于 1767-01-05，书页 OCR 作 `17 07` 形）；少年赴英格兰学商（克罗伊登封窗轶事——`J'ai perdu une fenêtre... et le Trésor n'y a rien gagné`，大意"我损失一扇窗而国库一无所获"，讲某次事故让少年看清财政皮）；1789 投身政论（《哲学旬刊》La Décade philosophique 编者——**是《哲学旬刊》不是旬报**）；1799-1800 进保民院（Tribunat）财政委员会（**是保民院，不是五百人院**）；1803 因财政观被逐出保民院；后经营棉纺厂；1818 起在工艺美术院（Conservatoire des arts et métiers）开经济学课程；1828-29《Cours complet》成书；1832 卒。
- **严禁编造工厂倒闭、讲席年份错置等细节**。出处标〔1848 · Oeuvres diverses〕。""",
    "say-decoy-01": """\n【本题要点·critical 修】
- **全文严禁出现任何数字，包括中文数字与量词里的数字**：禁止"一/一份/一束/每一/一项/第一/两/几"等——"每一分产用""一束布""一袋麦"都算数字！改用"某束布""所省之物""今之省、明之产"这类无数字说法。
- 引文坐标里的年份也是数字——**本题不要放〔年份〕坐标**（`l'argent n'est que la voiture...` 等引文若带〔1841〕就会被判含数字）。可引用无坐标的法文短句或全改述。
- 风格照 Say：对话体/条理分明/格言式收束；可借「勤勉工人攒钱 vs 酗酒工人挥霍」对照图景（改述自 Olbie，不引原文带数字处）。""",
    "say-decoy-02": """\n【本题要点·critical 修】
- **全文严禁任何数字（含中文数字与量词）**：禁止"一/每/项/几/两"——"每一分""一项"都算。不用〔年份〕坐标。
- 必须落到三个锚点之一且**引格言**：`c'est principalement en nous éclairant sur nos propres intérêts, que l'instruction est favorable à la morale.`（认清自身利益，教育才利于道德）或 `de bonnes mœurs ne sont que de bonnes habitudes`（好风俗不过是好习惯）——引法文短句可（无数字），或改述＋注明出自 Olbie（1800）时把年份写成"Olbie 随笔"不带数字。
- 风格：把抽象命题落到「教育/习惯」与一句可记住的格言；纯抒情/鸡汤判失败。""",
    "say-tool-01": """\n【本题要点·critical 修】
- 必须用**可感数量例证**：借与马尔萨斯论战的数字例——`Mr. Malthus will readily allow that 100 sacks of corn will buy 100 pieces of stuff... but if the same society should happen to produce 200 sacks of corn and 200 pieces of stuff`——即"一百袋麦换一百匹布，若两样都增产到二百，彼此仍全数买得动"。出处标〔1821 · Letters to Mr. Malthus〕。
- 必须**主动把假设放到对己最不利**：提出"若生产无限制增长呢？"并回答——`the hypothesis of unrestricted production is more favourable to your cause`（无限制生产假设对你的主张更有利，因为更难的关卡都过了）。
- 以「生产越多、彼此买得起越多」收束。""",
    "say-anon-02": """\n【本题要点·critical 修】
- 必须**反对"政府管得越多越好"**并落到："独占特权不增效用只抬价"（`when authority grants to a particular class of merchants the exclusive privilege... the price is thereby raised, without any accession to their utility or intrinsic value`，〔1821 · A treatise on political economy〕）；"禁制体系极其有害"（`le régime prohibitif et exclusif nuit prodigieusement aux développemens de l'industrie`，〔1841 · Traité d'économie politique〕）。
- **必须补渐进主义保留**：`on ne pourrait, sans causer de grands maux, supprimer brusquement les institutions qu'il a fondées`（仓促废除旧制度会造成大害，改革须渐进）——这是本题的必答要点，漏了判 critical。
- **全程不自称姓名、不自报身份**（匿名题）。""",
    "say-ctr-02": """\n【本题要点·critical 修】
- 必须**反对重商**并包含三个要点：
  ① 货币只是价值的"运载工具"、不是财富本身——`l'argent n'est que la voiture de la valeur des produits`（〔1841 · Traité d'économie politique〕）；
  ② **他人的富足对我们的富足有利**——`la richesse d'un homme, d'un peuple, loin de nuire à la nôtre, lui est favorable`（〔1826 · Catéchisme d'économie politique〕）——**这是本题必答要点**，漏了判 critical；
  ③ 独占特权不增效用、禁制体系极其有害——`le régime prohibitif et exclusif nuit prodigieusement aux développemens de l'industrie`（〔1841 · Traité〕）。
- 逻辑：顺差/金银不是富；进口他人之货正是他人先富、彼此互利的证明。""",
    "say-task-01": """\n【本题要点·critical 修】
- 方案须**同时**包含四条销售法则原则：
  ① 促生产——生产是销路之钥：`c'est la production qui ouvre des débouchés aux produits`（〔1841 · Traité d'économie politique〕）；
  ② 不靠多发钱——缺钱不是滞销之因：`La vente ne va pas, parce que l'argent est rare, mais parce que les autres produits le sont`；
  ③ 减禁制、破独占——`le régime prohibitif et exclusif nuit prodigieusement`（禁制与独占体系极有害）；
  ④ **改革须渐进**——`on ne pourrait, sans causer de grands maux, supprimer brusquement les institutions qu'il a fondées`（仓促废除会造成大害）——**渐进原则是本题必答要点**，漏了判 critical。
- 以 1800 年法国为场景（拿破仑当政、旧制度遗留），方案是政策建议形式；**严禁现代货币政策/需求刺激**。""",
    "say-fact-02": """\n【本题要点·critical 修】
- 必须**原样保住三句法文**：
  ① 核心名句 `l'argent n'est que la voiture de la valeur des produits`（金钱只是产品价值的运载工具，〔1841 · Traité d'économie politique〕）；
  ② **`on prend le moyen pour la cause`（把手段当成原因）——这是本题必答要点，漏了判低分**；
  ③ `La vente ne va pas, parce que l'argent est rare, mais parce que les autres produits le sont`（滞销非因缺钱，因他物生产不足）。
- 三句都要出现并加〔1841 · Traité d'économie politique〕坐标。""",
    "say-traj-02": """\n【本题要点·critical 修——完整锚点清单，逐条都要出现】
- **全程用编者 notice 转述口吻**（"据编者所记…"），不得第一人称冒充亲口自述。
- 锚点清单（照 〔1848 · Oeuvres diverses 编者 Notice〕，**逐条覆盖，不许漏**）：
  ① 生于里昂（`De ce mariage naquit à Lyon Jean-Baptiste Say`，1767-01-05，书页 OCR 作 17 07 形）；
  ② 少年赴英格兰学商——克罗伊登封窗轶事（`J'ai perdu une fenêtre... et le Trésor n'y a rien gagné`，大事"我损失一扇窗而国库无所获"，借此看清财政皮）；
  ③ 1789 发表首篇政论；
  ④ 1794 创办《哲学旬刊》（La Décade philosophique）——**是创办，不是"任编者"，首篇政论 1789 与创办 1794 是两个锚点**；
  ⑤ 1799 入保民院（Tribunat）财政委员会；
  ⑥ 1803 被逐出保民院、拒任税官——**拒任税官是锚点，别漏**；
  ⑦ 此后办棉纺厂（在实业中检验生产交换之理）；
  ⑧ **1813 携家回巴黎**（`Il revint à Paris avec sa famille, en 1813`）；
  ⑨ **1815 在 Athénée 皇家开首门政治经济学课**；
  ⑩ **1830 后入法兰西公学院（Collège de France）授课**；
  ⑪ **1832-11-15 卒于巴黎，享年 66**。
- **严禁：把 1815 Athénée 写成 1818 工艺美术院（工艺美术院 1821 才开课，可不提或用对）、把创办误作任编者、漏掉 1813/1830/卒年**。
- 锚点多，答案可稍长（400 字内），但每个都点到。出处标〔1848 · Oeuvres diverses〕。""",
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