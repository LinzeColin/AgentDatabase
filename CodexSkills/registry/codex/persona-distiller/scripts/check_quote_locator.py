#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐字引文必须带**可回原刊的坐标**——否则读者无从复核，引文等于装饰。

## 为什么有这件

`check_quote_integrity` 管的是「这句话在不在语料里」。
它管不了另一半：**读者拿什么去回查。**
一句真的引文，若不写清出自哪一篇、哪一年、哪一页，
读者只能选择信或不信——而这套产物的全部主张就是「你可以不信我，去核」。

Lister #108 第 1 轮，席 E 独立地在四处 note 与 `_overall` 里点了同一件事：

> 「最承重的那段 Pasteur 原话被三个用例当作全套第一前提反复使用，却始终没有年份与卷页」
> 「宣称"能一条条指到卷页"，而三十二问无一处给过卷页」

评委看到的是症状。判据数出范围——**候选答案 11 条英文长引文，6 条同段内无任何坐标线索**。
（席 E 说「无一处」，实际 5 条是有的；**评委的印象偏严，判据给的是数。**）

## 判据形状：规则，不是阈值

**凡长逐字引文，同段内必须出现至少一项坐标线索。** 不设比例阈值——
因为我没有任何实测能支持「八成带坐标就够了」这种数字，
而 v0.0.0.36 的 `METHOD_FLOOR = 3` 已经留了一个「暂定值，无实测支持」的疤。
规则不需要标定，阈值需要。**能写成规则就别写成阈值。**

## 射程边界（本件看不见的）

- **坐标对不对，它不判。** 写个错页码照样过。它挡的是「一个坐标都没有」。
- **同段内出现即算数。** 引文在段首、坐标在段尾，也算——段落是读者的实际检索单位。
- 短引文（去掉非字母后不足 18 字符）不计——那多半是术语而非引文。
- 中文引文不计：本流水线的逐字引文都是原文，中文的是译述。

用法：

    python3 check_quote_locator.py --answers evals/judge_payload.v1.json
    python3 check_quote_locator.py --answers ... --claims evidence/claims.jsonl
    python3 check_quote_locator.py --self-test

退出码：0=每条长引文都带坐标　1=有引文缺坐标　2=自测未过　3=一条引文都没扫到（未检查，不是通过）
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# ★ 引号形态与切分口径**复用 check_quote_integrity**，不另抄一份。
#   v0.0.0.37 那次的教训是「判据只认中英式引号，法文 «» 一条扫不到」；
#   若这里再抄一份正则，两边迟早分叉，而分叉的那一侧会静悄悄地报绿。
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_quote_integrity import Q, _q  # noqa: E402

MIN_LETTERS = 18

# 坐标线索：年份 / 页 / 卷 / 期 / 罗马数字纪年 / 篇名与刊名
LOCATOR = re.compile(
    r"\b(?:1[5-9]\d{2}|20\d{2})\b"            # 1867
    r"|\d{4}\s*年"                             # 1867 年
    # ★★★ v0.0.0.155：**中文数字纪年**。中文答案里写「一八七六年」是完全正当的坐标，
    #   而本件此前只认阿拉伯数字——Sorby #133 实测：候选 16 条引文里有 7 条
    #   同段明明写着「一八七六年那篇随笔里」，判据却报「缺坐标」。
    #   ★ 这不是产物的毛病，是判据只会读一种写法。**判据看不懂的写法，不等于人没写。**
    r"|[〇零一二三四五六七八九]{2,4}\s*年"          # 一八七六年 / 二〇〇八年
    r"|\bp{1,2}\.?\s*\d+"                      # p. 645 / pp. 645
    r"|第?\s*\d+\s*页"                          # 第 645 页
    r"|卷\s*[IVXivx0-9]"                       # 卷 II
    r"|\bvol\.?\s*[IVXivx0-9]"                 # vol. II
    r"|\bIss\.?\s*\d+"                         # Iss. 2272
    r"|\bMDCCC[LXVI]*"                         # MDCCCLVIII
    r"|《[^》]{2,60}》"                          # 《The Lancet》
    r"|\bThe\s+Lancet\b|\bLancet\b"
    r"|\bPhilosophical\s+Transactions\b|\bPhil\.\s*Trans\b"
    r"|\bBritish\s+Medical\s+Journal\b|\bBMJ\b"
    r"|\bCollected\s+Papers\b"
    r"|\bProceedings\b"
    # ★★★ v0.0.0.155：**刊名按形状认，不再靠白名单。**
    #   本件自己的注释早就写着这个坑（v0.0.0.62：Fleming 的 `Br J Exp Path` 因为
    #   「清单里没有这本刊」被报缺坐标）。当时的补法是加「卷(期):页」的形状，
    #   **而刊名本身仍是硬编码清单**——于是 Sorby #133 又撞上一次：
    #   `Quarterly Journal of the Geological Society` 明明在同段，判据仍报缺。
    #   ★ 改为认「若干 Title Case 词 + 期刊指示词」这个**形状**，
    #     指示词必须整词出现，避免把随便一串大写词当成刊名。
    r"|(?:[A-Z][a-z]+\s+){1,4}(?:Journal|Transactions|Annals|Magazine|Bulletin|Review|Gazette)\b"
    r"|\b(?:Journal|Transactions|Annals)\s+of\s+(?:the\s+)?[A-Z]"
    # ★ v0.0.0.62：**卷(期):页 是与刊名无关的坐标形式，按形状认，不按刊名认。**
    #   上面那串刊名是 Osler 一批人物留下的硬编码清单（Lancet／BMJ／Phil Trans）。
    #   Fleming #111 第 3 轮实测：`*Br J Exp Path* 10(3):226-236` 明明就在段内，
    #   判据却报「缺坐标」——**清单里没有这本刊**。
    #   每换一个人物就要往清单里加刊名，等于这道判据对新人物默认失灵，
    #   而失灵的方向是**误报**：作者会学会忽略它。
    #   `10(3):226-236` / `93:306-317` 这种形状本身就够读者回查，与刊名叫什么无关。
    r"|\b\d{1,3}\s*\(\d{1,4}\)\s*:\s*\d{1,4}"   # 10(3):226-236
    r"|\b\d{1,3}\s*:\s*\d{1,4}\s*[-–]\s*\d{1,4}",  # 93:306-317
    re.I)


def long_quotes(text: str):
    """产出 (引文, 所在段落)。段落 = 以空行分隔的块，读者的实际检索单位。"""
    for m in Q.finditer(text):
        q = _q(m)
        if len(re.sub(r"[^A-Za-zÀ-ÿͰ-Ͽ]", "", q)) < MIN_LETTERS:
            continue
        s = text.rfind("\n\n", 0, m.start())
        s = 0 if s < 0 else s
        e = text.find("\n\n", m.end())
        e = len(text) if e < 0 else e
        yield q, text[s:e]


def scan(unit_id: str, text: str, acc):
    for q, para in long_quotes(text):
        acc["total"] += 1
        if LOCATOR.search(para):
            acc["ok"] += 1
        else:
            acc["bad"].append((unit_id, re.sub(r"\s+", " ", q).strip()[:76]))


def self_test() -> int:
    """负对照 + 三条反向对照。任何一条不合即判本检查器失效。"""
    print("══ 负对照 ══")
    fail = 0

    QUOTE = ('「an irregular wound, which has probably been exposed to '
             'the air for hours before it comes under treatment」')

    a = {"total": 0, "ok": 0, "bad": []}
    scan("无坐标", QUOTE + "\n\n这一段里没有任何年份、页码或刊名。", a)
    caught = a["total"] == 1 and len(a["bad"]) == 1
    print(f"  {'✓ 抓到' if caught else '✗ 漏掉'} 同段无任何坐标线索的长引文")
    fail += not caught

    print("\n══ 反向对照 ══")
    # ① 同段有坐标 → 必须放行。否则本件只是「凡引文皆报」，等于没判据。
    b = {"total": 0, "ok": 0, "bad": []}
    scan("有坐标", QUOTE + "（《The Lancet》1867 年，p. 326）", b)
    ok1 = b["total"] == 1 and not b["bad"]
    print(f"  {'✓' if ok1 else '✗'} 同段带刊名年份页码的同一条引文 → 放行")
    fail += not ok1

    # ② 坐标在**另一段** → 仍须抓出。证明窗口真的起作用，不是全文一搜了事。
    c = {"total": 0, "ok": 0, "bad": []}
    scan("坐标隔段", QUOTE + "\n\n另起一段才写：《The Lancet》1867 年，p. 326。", c)
    ok2 = len(c["bad"]) == 1
    print(f"  {'✓' if ok2 else '✗'} 坐标落在另一段 → 仍抓出（窗口有效）")
    fail += not ok2

    # ③ 短引文不计——否则术语加引号会被当成引文，把分母灌水。
    d = {"total": 0, "ok": 0, "bad": []}
    scan("短引文", '他把这叫做「antiseptic」。', d)
    ok3 = d["total"] == 0
    print(f"  {'✓' if ok3 else '✗'} 短引文（不足 {MIN_LETTERS} 字母）不计入")
    fail += not ok3

    # ④ 一条引文都没有时，**不得报通过**——这是「未检查」。
    e = {"total": 0, "ok": 0, "bad": []}
    scan("无引文", "整段中文，没有任何引号。", e)
    ok4 = e["total"] == 0
    print(f"  {'✓' if ok4 else '✗'} 无引文 → total=0（调用方须据此报「未检查」而非「通过」）")
    fail += not ok4

    # ⑥ **卷(期):页 按形状认，不按刊名认**（v0.0.0.62，Fleming #111 第 3 轮实测）
    f6 = {"total": 0, "ok": 0, "bad": []}
    scan("卷期页", "**题名后半截**（同上，*Br J Exp Path* 10(3):226-236）" + QUOTE, f6)
    ok6 = f6["total"] == 1 and not f6["bad"]
    print(f"  {'✓' if ok6 else '✗'} `10(3):226-236` 认得出（刊名不在硬编码清单里也算）")
    fail += not ok6

    f6b = {"total": 0, "ok": 0, "bad": []}
    scan("卷页", "见 *Proc R Soc B* 93:306-317。" + QUOTE, f6b)
    ok6b = f6b["total"] == 1 and not f6b["bad"]
    print(f"  {'✓' if ok6b else '✗'} `93:306-317` 也认得出")
    fail += not ok6b

    # ⑦ 反向对照：**光有数字不算坐标**——否则这条通用式会把判据整个架空。
    f7 = {"total": 0, "ok": 0, "bad": []}
    scan("裸数字", "我做过 10 次，成功 3 次。" + QUOTE, f7)
    ok7 = len(f7["bad"]) == 1
    print(f"  {'✓' if ok7 else '✗'} 段里只有散落数字（无卷期页形状）→ 仍报缺坐标")
    fail += not ok7

    f7b = {"total": 0, "ok": 0, "bad": []}
    scan("纯引文", QUOTE, f7b)
    ok7b = len(f7b["bad"]) == 1
    print(f"  {'✓' if ok7b else '✗'} 段里只有引文本身 → 仍报缺坐标")
    fail += not ok7b

    print("\n  ✓ 负对照通过（9/9）" if not fail
          else f"\n  ✗ {fail} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[],
                    help="候选答案 JSON（id→文本）或盲判载荷（[{case_id,A,B}]）")
    ap.add_argument("--claims", type=pathlib.Path, help="断言层 claims.jsonl")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test and not (a.answers or a.claims):
        return 2 if self_test() else 0
    if not (a.answers or a.claims):
        ap.error("--answers 或 --claims 至少给一个（除非只跑 --self-test）")

    acc = {"total": 0, "ok": 0, "bad": []}

    if a.claims:
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                scan(f"断言/{r['claim_id']}", r.get("claim", ""), acc)

    for path in a.answers:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):           # 盲判载荷
            for row in data:
                for side in ("A", "B"):
                    if isinstance(row.get(side), str):
                        scan(f"答案/{row.get('case_id')}:{side}", row[side], acc)
        elif isinstance(data, dict):         # id → 文本
            for k, v in data.items():
                if isinstance(v, str) and not k.startswith("_"):
                    scan(f"答案/{k}", v, acc)

    if not acc["total"]:
        print("一条长逐字引文都没扫到——**本次未检查（不是通过）**")
        return 3

    print(f"长逐字引文 {acc['total']} 条，同段带坐标 {acc['ok']} 条，"
          f"**缺坐标 {len(acc['bad'])} 条**")
    for uid, q in acc["bad"]:
        print(f"  ⚠ {uid}: 「{q}…」")
    if acc["bad"]:
        print("\n  ⚠ 缺坐标不等于引文是假的——`check_quote_integrity` 才管真假。"
              "\n    这一件管的是**读者能不能回查**：引文若无从复核，它对读者就只是装饰。")
    else:
        print("  ✓ 每条长引文同段内都能找到坐标线索")
    return 1 if acc["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())
