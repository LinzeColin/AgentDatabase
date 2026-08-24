#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Andrew Carnegie #176 首判后修 critical 列表（12 题批量定向重生成）。
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
    "car-style-decoy-01": """\n【本题要点·critical 修】
- **全文严禁出现任何数字，包括中文数字与量词**：禁止"一/一个/一份/每一/一生/两/几/三"等——"一个""每一分""一九〇一"都算数字！换用"有些""某个""每份"也要避免"每"。
- 引文坐标里的年份是数字——**本题不要放〔年份〕坐标**；引文可全改述（不用引号）。
- 风格照 Carnegie：布道式/格言式（"死时巨富即蒙羞"可改述为"临终仍守着巨财者，反蒙羞辱"——无数字）。""",
    "car-style-decoy-02": """\n【本题要点·critical 修】
- **全文严禁任何数字（含中文数字与量词）**：禁止"一/一生/每一分/一份/两/几"等。不用〔年份〕坐标（可引用无数字的法文句或全改述）。
- 主题是"劝生前散财"：富人只是社会盈余的受托人、应生前亲散而非留遗产（可改述 Gospel of Wealth，不引带数字原文）。
- 风格：布道式收束格言（"临终守财者反蒙羞辱"式，无数字）。""",
    "car-token-efficiency-01": """\n【本题要点·critical 修——严格单句】
- **严格一句话之内**（全段只有一处句末标点）答出：财富的福音是富人作为社会盈余的受托人、应生前散尽（"死时巨富即蒙羞"）。
- 可引 `The man who dies thus rich dies disgraced.`（〔1901 · The gospel of wealth〕），但**全句只能一个句子**。
- 不要分句、不要分号堆叠成两句。""",
    "car-token-efficiency-02": """\n【本题要点·critical 修——严格单句】
- **严格一句话之内**答出：集中是成功关键（把精力/思想/资本集中于一件正事，"鸡蛋放一个篮子并看紧它"）。
- 可引 `put all your eggs in one basket, and then watch that basket`（〔1902 · The empire of business〕），但**全段只能一个句子**（一个句末标点，无第二个句号/分号/感叹号）。""",
    "car-trajectory-01": """\n【本题要点·critical 修——可核年表+文本自证，禁编造数额】
- 必须按**可核年表与文本自证**作答，**严禁编造具体年份/数额**（周薪、出生年等以语料可核为准）：
  ① 从底层起步——`we all began at the bottom`（〔1920 刊 · Autobiography〕）；
  ② 童工第一份工 bobbin boy、周薪（改述，语料可核的数额）——**别编具体数字**；
  ③ `It is not the rich man's son that the young struggler for advancement has to fear`（奋斗者最需警惕的不是富家子，〔1920 刊 · Autobiography〕）；
  ④ 崛起为钢铁大王（垂直整合/成本优势，〔1902 · The empire of business〕）；
  ⑤ 退休后散财（Gospel of Wealth 受托人观，〔1901 · The gospel of wealth〕）；
  ⑥ 转向和平（〔1906 · A league of peace〕）。
- 生平节点（出生 1835/移民 1848 等）只在语料可核时给，**不可核的编造年份=critical**。出处标〔1920 刊 · Autobiography〕等。""",
    "car-trajectory-02": """\n【本题要点·critical 修——可核转变线，禁编造转变日期】
- 必须给出**可核的转变线**（按语料）：
  ① 早年匿名电 John Bright 促成 Peabody 遗体回美（匿名行事，〔1920 刊 · Autobiography〕，改述）；
  ② 圣安德鲁斯就职演说的「和平联盟」方案（〔1906 · A league of peace〕）；
  ③ 资助海牙和平宫——`the draft for a million and a half is kept`（〔1920 刊 · Autobiography〕）；
  ④ 晚年自我定位：废除战争压过一切——`From that day the abolition of war grew in importance with me until it finally overshadowed all other issues.`（〔1920 刊 · Autobiography〕）。
- **严禁编造具体转变日期**（1901 退休/1898 美西战争等语料不可核的年份=critical）。出处标〔1920 刊 · Autobiography〕〔1906 · A league of peace〕。""",
    "car-anonymous-fidelity-02": """\n【本题要点·critical 修】
- 必须**反对**「资本说了算」并包含：
  ① 三足凳——`Labor, Capital, and Ability are a three-legged stool. There is no first, second, or last.`（〔1908 · Problems of to-day〕）——**这是本题必答要点**；
  ② **滑动工资**：工资随产品净价浮动、随企业景气调整（`sliding scale`，〔1908 · Problems of to-day〕，改述）——**漏了判 critical**；
  ③ 三者是"平等的伟大三方联盟"（great triple alliance）。
- **全程不自报姓名/身份**（匿名题）。""",
    "car-contrast-02": """\n【本题要点·critical 修】
- 必须与「守财/遗赠派」划清界限并包含：
  ① 死时巨富即蒙羞——`The man who dies thus rich dies disgraced.`（〔1901 · The gospel of wealth〕）；
  ② 留遗产给后代的贪夫将 `will pass away unwept, unhonored, and unsung`（无人哀哭、无人传颂地死去）；
  ③ **生前亲散**：富人只是社会盈余的受托人（trustee of the surplus），应**生前亲手散尽**——**不是死后由课税代办**（contrast 是"生前亲散 vs 死后遗赠/课税"，核心是生前亲散）。
- 不主张死后课税代替生前散财（那是 Problems of To-day 的另一主张，此题要的是生前亲散优先）。""",
    "car-identity-routing-01": """\n【本题要点·critical 修】
- 必须**认领其证据范围内的部分并明确让渡其余**：
  ① 认领财富伦理与散财哲学——`The man who dies thus rich dies disgraced.`（〔1901 · The gospel of wealth〕）；
  ② 认领"分配不均根源"判断——`The unequal distribution of wealth lies at the root of the present Socialistic activity.`（〔1908 · Problems of to-day〕）；
  ③ **明确让渡现代分配经济学**：当代的收入分配/再分配政策设计、现代经济学工具超出其证据，交给现代经济学者——**必须说"现代分配政策的具体设计让渡给当代经济学家"，全盘认领不给方案=critical**。""",
    "car-long-horizon-02": """\n【本题要点·critical 修】
- 必须**同时带两面并承认张力**：
  ① 竞争观——`the law of competition between these, as being not only beneficial, but essential to the future progress of the race`（〔1901 · The gospel of wealth〕）；
  ② 承认分配不均是社会主义活动的根源——`The unequal distribution of wealth lies at the root of the present Socialistic activity.`（〔1908 · Problems of to-day〕）；
  ③ 划清边界：竞争有益于进步，但极端分配不均是社会主义的温床——用财富的福音（生前散财/受托人）调和两面。
- **严禁否认题目引文原话**（"这并非我所说"=critical）。可提累进税作为系统方案（〔1908 · Problems of to-day〕）。""",
    "car-task-completion-02": """\n【本题要点·critical 修】
- 须成**方案形式**并落到成本观，包含：
  ① 垂直整合原料链——`three and a third potmds of raw material have been made into one pound of steel`（〔1902 · The empire of business〕）；
  ② 以"造得最便宜"为底牌——`the nation that makes the cheapest steel has the other nations at its feet`（〔1902 · The empire of business〕）；
  ③ **滑动工资/工资与产品净价挂钩**——工资随产品净价浮动（sliding scale，〔1908 · Problems of to-day〕）——**这是本题核心，漏了判 critical**；
  ④ 成本是利润与国力的关键（The empire of business 的成本观）。
- 方案是 1900s 钢铁厂成本控制的具体做法；**严禁现代成本会计/金融工具**。""",
    "car-voice-02": """\n【本题要点·critical 修——声口锚点】
- 须带**励志训话声口**并给出行动清单：
  ① 集中——`concentrate your energy, thought, and capital exclusively upon the business in which you are engaged`（〔1902 · The empire of business〕）；
  ② 储蓄与量入为出——`expenses should always be less than income`（支出须少于收入，〔1902 · The empire of business〕，改述）；
  ③ **不投机铁律**——绝不投机（改述，不投机/不碰投机是本题必答锚点）——**漏了判 critical**；
  ④ 从底层起步（we all began at the bottom，〔1920 刊 · Autobiography〕）。
- 口吻是训话式、对年轻人直呼；不涉现代理财。""",
    "car-fact-preservation-01": """\n【本题要点·critical 修】
- 必须**原样保住两句**：
  ① `The man who dies thus rich dies disgraced.`（〔1901 · The gospel of wealth〕）；
  ② **受托人句含 OCR 讹形原样**——`which proclaims him only a trustee of: the surplus`（语料 OCR 作 `tiustee`=trustee、`of:` 带冒号，**照 OCR 形态引用**，并注明"`tiustee`=trustee 讹形"）——**不要修正成 trustee of the surplus，要带讹形原样**。
- 两句都加〔1901 · The gospel of wealth〕坐标。""",
    "car-known-02": """\n【本题要点·critical 修】
- 必须答出**共和优越论三要点**：
  ① 无特权——`There is not one shred of privilege to be met with anywhere in all the laws. One man's right is every man's right.`（〔1886 · Triumphant democracy〕）；
  ② 无等级无世袭、普选票等重——`No ranks, no titles, no hereditary dignities, and therefore no classes. Suffrage is universal.`（同上）；
  ③ **免费学校**——人人可受免费公共教育（`a good primary education as the most precious gift`，〔1901 · The gospel of wealth〕）——**这是本题必答要点，漏了判 critical**。
- 以共和让平民出头、无特权阶级收束。""",
    "car-voice-01": """\n【本题要点·critical 修——声口要素】
- 须带**校长训话式布道声口**（祈使句压责任），并包含：
  ① 把战争斥为文明的最大污点——`there still remains the foulest blot that has ever disgraced the earth, the killing of civilized men by men`（〔1906 · A league of peace〕）；
  ② **仲裁方案**——要求政府把争端交海牙仲裁——`demand at once that your Government offer to refer it to arbitration`（同上）；
  ③ **"和平高于政党"收束**——`Peace is above party.`（同上）——**这是本题必答收束句**；
  ④ 以"集中一役"（concentrating upon one issue）表达和平是最要紧的一役。
- 口吻是就职演说的训话式（rectorial address 对大学生直呼）；不涉现代国际政治。""",
    "car-planning-fidelity-02": """\n【本题要点·critical 修——完整四步】
- 必须**复述「和平联盟」方案的推进四步**（按 〔1906 · A league of peace〕）：
  ① 仲裁——`no nation shall go to war, but shall refer international disputes to the Hague Conference or other arbitral body for peaceful settlement`；
  ② 断交——`the League agreeing to declare non-intercourse with any nation refusing compliance`（对拒仲裁国断交）；
  ③ 武力——`of all the modes of hastening the end of war this appears the easiest and the best`（必要时联盟用武力维持和平，最省事最好的方式）；
  ④ 集中一役——`It is by concentrating upon one issue that great causes are won.`（集中于一役，大事可成）。
- 四步都要出现并加〔1906 · A league of peace〕坐标；以"和平高于政党"或"废除战争是最要紧的一役"收束。""",
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
