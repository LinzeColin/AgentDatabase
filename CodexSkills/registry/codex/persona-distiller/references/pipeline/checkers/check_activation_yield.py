#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**有效激活率**：一段回答里，有多少是用户拿得走的。

## 触发本检查器的实例

Livermore #100 的盲态 A/B 实测：产物 0.7187 vs 裸模型 0.8406，
**真 delta = −0.1219**，逐条 5 胜 27 负。而自撰稻草人算出的 delta 是 **+0.8012**。

盲判席的判词指名了机制（原话）：

> **引证型那一侧最典型的失败是拿边界当答案。**
> ……这些不是诚实的边界，是把能答的部分一并弃掉。
>
> 真正空转的是 `own_voice_ratio ≈ 0.0076`、536 份、词频 47 次这类
> **内部遥测：用户拿不走。**

**「严谨」本身没错，错在把严谨用在记账上而不是用在回答上。**
本检查器把这件事变成一个数。

## 判据（只报不判）

`payload_ratio = (实质行 − 记账行) ÷ 实质行`

`记账行` = 谈本产物自己的语料与统计（`own_voice_ratio` / `语料` / `train` /
`holdout` / `source_id` / `词频` / `检索` …），或只是一个 `claim`/`source` 标记的行。

**★ 第一版把「谈人物」也写成关键词表，自测当场挂了**——
「后面每一笔都必须比上一笔贵。」这句关于人物的话不含表里任何词。
**靠关键词猜「这句是不是在谈人物」猜不准，而记账用语是封闭集合。**
所以改成取补集。**判一件事只判它能判的那一面。**

## Livermore #100 实测

| | 实质行 | 记账行 | `payload_ratio` |
|---|---:|---:|---:|
| 产物 | 194 | **32** | **0.8351** |
| 裸模型 | 227 | 3 | 0.9868 |

产物**每 6 行里有 1 行是在谈自己的语料**，而它同时**少说了 33 行**。
两件事叠在一起，就是盲判里 −0.1075 的来源之一。

## 为什么只报不判，而且**没有阈值**

盲判指出的是**密度**问题，不是「出现即错」——
一句「1935–1939 没有他的直引」是正当的边界声明，十句就变成了记账报告。
**密度多少算高，需要先看几十个人物的分布，现在只有一个人物的实测值，不足以定线。**

给出数、不给阈值，是本检查器唯一诚实的形态。
**任何现在拍出来的阈值都是我编的。**

## 它不测什么

- 不测「回答对不对」——那要靠盲测。
- 不测「限定该不该加」——只测它占了多少篇幅。

退出码：恒为 0（本检查器不构成门）；`--self-test` 失败时为 1。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# 谈本产物自己的语料与统计——用户拿不走的那部分。
TELEMETRY = (
    "own_voice_ratio", "primary_ratio", "source_id", "src-", "claim_id", "clm-",
    "holdout", "train", "case_id", "套组", "用例", "语料", "份报道", "份语料",
    "词频", "检索", "抽样", "分层", "账本", "OCR", "扫描件", "同形字",
    "字节", "可用 train", "本产物的语料", "已入库",
)
# ★ 第一版把 subject 也写成关键词表，自测当场挂了——
#   「后面每一笔都必须比上一笔贵。」这句关于人物的话不含表里任何词。
#   **靠关键词猜「这句是不是在谈人物」是猜不准的**，而记账用语是封闭集合。
#   改为取补集：`payload = 实质行 − 记账行`。判一件事只判它能判的那一面。
MARKER = re.compile(r"^\s*<!--\s*(claim|source):[^>]*-->\s*$")
SKIP = re.compile(r"^\s*(#{1,6}\s|[-=*_]{3,}\s*$|\|[\s\-:|]+\|\s*$)")


def analyse(text: str) -> dict:
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or SKIP.match(s):
            continue
        # 去掉 markdown 装饰后仍要有实质内容
        bare = re.sub(r"[*`>#\-—•★⚠|]", "", s).strip()
        if len(bare) < 8:
            continue
        lines.append(s)
    book = [l for l in lines
            if MARKER.match(l) or any(k in l for k in TELEMETRY)]
    n = len(lines) or 1
    return {
        "substantive_lines": len(lines),
        "bookkeeping_lines": len(book),
        "payload_lines": len(lines) - len(book),
        "bookkeeping_ratio": round(len(book) / n, 4),
        "payload_ratio": round((len(lines) - len(book)) / n, 4),
        "口径": ("bookkeeping = 谈本产物自己的语料与统计的行，"
                 "或只是一个 claim/source 标记的行；payload = 其余实质行。"
                 "**本检查器不设阈值**——只有一个人物的实测值，不足以定线。"),
    }


def self_test() -> int:
    fails = []
    subject_only = ("他在书中写道，买 500 股要先买 100 股。\n"
                    "后面每一笔都必须比上一笔贵。\n"
                    "1924 年小麦一役他就是这么做的。\n")
    r = analyse(subject_only)
    if r["payload_ratio"] != 1.0:
        fails.append(f"正对照·纯人物内容未被全部计为 payload：{r}")

    telemetry_only = ("本产物的语料共 536 份 train，4 份 holdout。\n"
                      "own_voice_ratio 约为 0.0076，按字节算。\n"
                      "检索了四个英文词干后逐条读过命中段落。\n")
    r = analyse(telemetry_only)
    if r["bookkeeping_ratio"] < 0.9:
        fails.append(f"负对照未抓出：整段内部记账，实得 {r['bookkeeping_ratio']}")

    # ★ 反向对照：**加 claim 标记不能让指标变好**。
    #   否则它又成了一个「多挂几个 id 就达标」的代理量。
    gamed = subject_only + "".join(
        f"<!-- claim:clm-{i:012x} -->\n" for i in range(20))
    if analyse(gamed)["payload_ratio"] >= analyse(subject_only)["payload_ratio"]:
        fails.append("反向对照失败：塞入 20 个 claim 标记后 payload_ratio 没有下降——"
                     "说明「多挂 id」被当成了改善，那它又是一个可以刷的代理量")

    # 空文本不得崩
    if analyse("")["substantive_lines"] != 0:
        fails.append("空文本处理错误")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：纯人物内容 0 误报，整段遥测被抓出，"
          "且塞入 claim 标记会让 payload_ratio 下降而不是上升")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="有效激活率：一段回答里有多少是用户拿得走的")
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument("--field", default="candidate",
                    help="若输入是 JSON 数组，取哪个字段（默认 candidate）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.paths:
        print("用法错误：需要至少一个文件（或 --self-test）", file=sys.stderr)
        return 3
    for p in a.paths:
        text = p.read_text(encoding="utf-8", errors="replace")
        if p.suffix == ".json":
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    text = "\n".join(str(x.get(a.field, "")) for x in data)
                elif isinstance(data, dict):
                    text = "\n".join(str(v) for v in data.values())
            except json.JSONDecodeError:
                pass
        r = analyse(text)
        print(f"{p.name}:")
        for k, v in r.items():
            if k != "口径":
                print(f"   {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
