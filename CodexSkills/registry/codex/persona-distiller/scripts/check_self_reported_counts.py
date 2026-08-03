#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""答案里自称「X 字」「共 N 条」「连发 N 期」时，**把它数一遍**。

## 为什么有这件

一个主动邀请读者核对的数字，**如果它自己是错的，伤害比不给还大**——
读者去数了，发现对不上，此后每一个数字都要被重新怀疑。

Virchow #109 第 1 轮，**两席各自独立抓到同一处**：

> 席 D：「q-26 那一侧自称『不含标点十七字，数过的』，实为 14 字 ——
>        自证式的数错，比不数更伤，该组因此被反超（6.5 对 8.0）。」
> 席 E：「主动邀请核对的那一处自己算错，直接打在产品卖点上。」

`token-efficiency` 套组因此 **−0.0700**，是那一轮**唯一为负**的套组。

**而我的生成器里本来就有一段自检**——它数的是整串（含括注），
所以它算出 24 而我写了 17，两个都不是真值 14。
**判据数错了地方，比没有判据更坏：它给了我一个「已经核过」的错觉。**

同类此前已发生多次（Koch 字数、Lister 字数各一轮），
每次都是「下次注意」，**没有一次落成判据**。这一次落成。

## 判据形状：只数它自己声明要数的那一段

本件**不猜**该数哪一段。它只处理**紧挨着数字声明的那一句**：

- 「（不含标点十七字）」→ 数**声明之前**那一段正文的非标点字符
- 「（含标点二十一字）」→ 数**声明之前**那一段正文的全部字符
- 「三十字以内」「不超过 N 字」→ 同上，判是否越界

## 射程边界（写清楚，不假装能干更多）

- **只认中文数字与阿拉伯数字的「N 字」形态**，不认「不到一百个词」这类模糊说法。
- **只数声明之前最近的那一段**（以 `\\n\\n`、`（`、`——` 为界）。
  声明若离被数的内容很远，本件会数错——**故它报的是「对不上」，不是「你错了」**。
- 「共 N 条」「连发 N 期」这类**不数**：条与期的边界因文体而异，
  没有一个不出错的切法。**能数准的才数，数不准的明写不数。**

用法：

    python3 check_self_reported_counts.py --answers evals/judge_payload.v1.json
    python3 check_self_reported_counts.py --self-test

退出码：0=每处自报数都对（或无自报数）　1=有对不上的　2=自测未过
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

PUNCT = set("：，。、；！？（）「」『』《》〈〉—…·,.;:!?()[]{}\"'‘’“”-–")

CN = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9}


def cn2int(s: str) -> int | None:
    # ★ v0.0.0.67：**千分位在两处都要处理**——正则吃掉了，这里也得吃掉，
    #   否则 `1,234` 解析失败返回 None，声明被静默跳过（`seen` 都不加一）。
    if isinstance(s, str):
        s = s.replace(",", "").replace("，", "")
    """中文数字 → 整数。只处理 1–99，够用且不会悄悄算错。"""
    s = s.strip()
    if s.isdigit():
        return int(s)
    if not s or any(c not in CN and c != "十" for c in s):
        return None
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN.get(s[1:], 0) if len(s) == 2 else None
    if "十" in s:
        a, _, b = s.partition("十")
        if a not in CN:
            return None
        return CN[a] * 10 + (CN.get(b, 0) if b else 0)
    return CN.get(s)


# 「不含标点十七字」「含标点二十一字」「三十字以内」「不超过三十字」
# ★ v0.0.0.67 两处假阳性，都出在 Nightingale #112 第 3 轮的同一句上：
#   答案写 `正文 101,610 字符里 Nightingale 零命中`，判据报
#   「自称 610 字，实数 134」——**它把千分位切断，又把 `字符` 当成了 `字`**。
#
#   ① **千分位要整个吃掉**：`(?<![\d,])` 前瞻 + 允许 `,` 分组。
#      只取 `610` 等于把一个七位数读成三位数，而这种数字**恰好出现在
#      「我扫了多少字符」这类可核陈述里**——判据把最该鼓励的写法报成了缺陷。
#   ② **`字符` 不是 `字`**：本判据数的是「这一段有多少字」，
#      而 `101,610 字符` 说的是**另一份文件**有多长，根本不在射程内。
DECL = re.compile(
    r"(?P<kind>不含标点|含标点|)\s*"
    r"(?P<num>(?<![\d,])[0-9]{1,3}(?:,[0-9]{3})+|(?<![\d,])[0-9]{1,3}|[零〇一二两三四五六七八九十]{1,3})"
    r"\s*字(?!符|节|母|号|典|据|样|里|体|面|句|里行)"
    r"(?P<bound>以内|以下|之内|)")


def strip_marks(s: str) -> str:
    return s.replace("**", "").replace("`", "").strip()


def segment_before(text: str, pos: int) -> str:
    """取声明之前最近的那一段**正文**。

    ★ 第一版以 `（` 为界，而字数声明几乎总是紧跟在 `（` 后面，
      于是切出来是空串、判据静默漏报——**自测当场抓到，没让它进产物。**
      改法：先跳过声明所在的那一层括注，再往前找段界。
    """
    head = text[:pos]
    # ① 跳过声明所在的括注：若声明前最近的是一个未闭合的 `（`，从它之前开始算
    op = head.rfind("（")
    if op >= 0 and "）" not in head[op:]:
        head = head[:op]
    # ② 再往前找段界。**取到空串时要继续往前找，不能就此放弃**——
    #    `\n\n` 与 `（` 相邻时（「…**\n\n（不含标点十六字…」），
    #    跳过括注后剩下的正好被段界切光，第二版因此**漏掉了 Lister #108 那处真声明**。
    #    这是同一个函数上的第二次漏报；两次都是回验历史数据才暴露的。
    for cut in (max(head.rfind("\n\n"), head.rfind("——")),
                head.rfind("\n"), -1):
        seg = strip_marks(head[cut + 1:].strip("（—\n ") if cut >= 0
                          else head.strip("（—\n "))
        if seg:
            return seg
    return ""


# ★ 「一字未动」「一字不改」这类是**成语，不是字数声明**。
#   回验 Lister #108 时暴露：「扉页原样是这一串（**一字未动**，含扫本的讹字）」
#   被判成「自称 1 字、实为 8 字」——**假阳比漏报更坏，它会让人开始忽略这件判据。**
IDIOM = re.compile(r"[一半]\s*字\s*(?:未|不|没)\s*(?:动|改|漏|差|提|落)"
                   r"|只字|片字|白纸黑字|一字千金")


def check_text(uid: str, text: str, acc):
    for m in DECL.finditer(text):
        # 命中处若落在成语里，跳过
        around = text[max(0, m.start() - 2): m.end() + 6]
        if IDIOM.search(around):
            continue
        n = cn2int(m.group("num"))
        if n is None:
            continue
        seg = segment_before(text, m.start())
        if not seg:
            continue
        acc["seen"] += 1
        full = len(seg)
        bare = sum(1 for c in seg if c not in PUNCT)
        kind, bound = m.group("kind"), m.group("bound")
        actual = bare if kind == "不含标点" else (full if kind == "含标点" else bare)
        label = kind or ("上限" if bound else "字数")
        ok = (actual <= n) if bound else (actual == n)
        if not ok:
            acc["bad"].append((uid, f"自称「{label}{m.group('num')}字"
                                    f"{bound}」，实数 {actual}"
                                    f"（含标点 {full}／不含 {bare}）：「{seg[:34]}」"))


def scan(paths):
    acc = {"seen": 0, "bad": []}
    for path in paths:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        if isinstance(data, list):
            for row in data:
                for side in ("A", "B"):
                    if isinstance(row.get(side), str):
                        check_text(f"{row.get('case_id')}:{side}", row[side], acc)
        elif isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and not k.startswith("_"):
                    check_text(k, v, acc)
    return acc


def self_test() -> int:
    """负对照 + 四条反向对照。"""
    print("══ 负对照 ══")
    fail = 0

    # Virchow #109 真实样本，一字未改：自称十七字，实为 14
    REAL_BAD = "**因为成因常在住房、口粮与教育里。**（不含标点十七字，数过的。）"
    a = {"seen": 0, "bad": []}
    check_text("real", REAL_BAD, a)
    got = len(a["bad"]) == 1 and "实数 14" in a["bad"][0][1]
    print(f"  {'✓ 抓到' if got else '✗ 漏掉'} 真实样本：自称十七字、实为 14"
          f"（{a['bad'][0][1][:46] if a['bad'] else '未报'}）")
    fail += not got

    print("\n══ 反向对照 ══")
    # ① 数对了 → 不得报（否则本件只是「凡自报皆报」）
    OK = "**因为成因常在住房、口粮与教育里。**（不含标点十四字，数过的。）"
    b = {"seen": 0, "bad": []}
    check_text("ok", OK, b)
    print(f"  {'✓' if not b['bad'] else '✗'} 同一句改成十四字 → 不报（数对了）")
    fail += bool(b["bad"])

    # ② 上限形态：在限内 → 不报
    UNDER = "**要挡的是空气里的活物。**（三十字以内。）"
    c = {"seen": 0, "bad": []}
    check_text("under", UNDER, c)
    print(f"  {'✓' if not c['bad'] else '✗'} 「三十字以内」而实为 11 字 → 不报")
    fail += bool(c["bad"])

    # ③ 上限形态：越界 → 须报
    OVER = ("**因为疾病的成因常常落在住房、口粮、教育与劳动条件这些社会条件里面，"
            "而不只是在人的身体内部。**（三十字以内。）")
    d = {"seen": 0, "bad": []}
    check_text("over", OVER, d)
    print(f"  {'✓ 抓到' if d['bad'] else '✗ 漏掉'} 「三十字以内」而实际超出 → 报")
    fail += not d["bad"]

    # ④ **成语不是字数声明**。回验 Lister #108 时暴露的假阳，一字未改地做成夹具。
    IDIOM_CASE = ("扉页原样是这一串（一字未动，含扫本的讹字）：\n"
                  "> «XXXI. On the Early Stages of Inflammation»")
    f = {"seen": 0, "bad": []}
    check_text("idiom", IDIOM_CASE, f)
    print(f"  {'✓' if not f['bad'] else '✗'} 「一字未动」是成语 → 不报"
          f"（**假阳会让人开始忽略这件判据**）")
    fail += bool(f["bad"])

    # ⑤ Lister #108 真实样本（一字未改）：两处声明都对，**必须都数到、且都不报**。
    #    第二版在这里静默漏报——`\n\n` 与 `（` 相邻时段落被切光。
    JL = "**要挡的是空气里的活物，不是空气本身。**\n\n（不含标点十六字，含标点十八字——**数出来的，不是估的。**）"
    g = {"seen": 0, "bad": []}
    check_text("jl", JL, g)
    ok5 = g["seen"] == 2 and not g["bad"]
    print(f"  {'✓' if ok5 else '✗'} Lister #108 真实样本：两处声明**都数到**（seen={g['seen']}）"
          f"且都对（bad={len(g['bad'])}）")
    fail += not ok5

    # ⑥ 没有自报数 → seen=0，调用方须据此报「未检查」而非「通过」
    e = {"seen": 0, "bad": []}
    check_text("none", "**这一段里没有任何字数声明。**", e)
    print(f"  {'✓' if e['seen'] == 0 else '✗'} 无自报数 → seen=0"
          f"（调用方须报「未检查」而非「通过」）")
    fail += e["seen"] != 0

    print("── ★★ 反向对照 ⑤：**千分位不许切断**（v0.0.0.67，实测假阳性）──")
    # Nightingale #112 第 3 轮：答案写「正文 101,610 字符里 Nightingale 零命中」，
    # 判据报「自称 610 字，实数 134」——它把千分位切断，又把「字符」当成了「字」。
    # **这种数字恰好出现在「我扫了多少字符」这类可核陈述里**，
    # 判据把最该鼓励的写法报成了缺陷。
    c5 = {"seen": 0, "bad": []}
    check_text("x", "**正文 101,610 字符里 `Nightingale` 零命中**——逐字扫过，不是印象。", c5)
    ok5 = c5["seen"] == 0 and not c5["bad"]
    print(f"  {'✓' if ok5 else '✗'} 「101,610 字符」→ 不计入（`字符` 不是 `字`，且千分位要整个吃）")
    fail += not ok5

    c5b = {"seen": 0, "bad": []}
    # ★ 这一条要能**区分「读成 1234」与「读成 234」**：
    #   造一段恰好 1234 字的正文，声明 `1,234 字`。读对 → 不报；读成 234 → 报。
    BIG = "甲" * 1234 + "。"
    check_text("y", f"**{BIG}**（不含标点 1,234 字。）", c5b)
    ok5b = c5b["seen"] == 1 and not c5b["bad"]
    print(f"  {'✓' if ok5b else '✗'} 1234 字的正文 + 「1,234 字」→ 不报"
          f"（**证明读成了 1234 不是 234**）")
    fail += not ok5b

    c5c = {"seen": 0, "bad": []}
    check_text("y2", "**" + "甲" * 234 + "。**（不含标点 1,234 字。）", c5c)
    ok5c = len(c5c["bad"]) == 1
    print(f"  {'✓' if ok5c else '✗'} 234 字的正文 + 「1,234 字」→ **报出**（不是悄悄放过）")
    fail += not ok5c

    print("── 反向对照 ⑥：`字节` `字母` `字典` 这些都不是 `字` ──")
    for s in ("这份有 512 字节。", "他写了 26 字母。", "查了 300 字典条目。"):
        c6 = {"seen": 0, "bad": []}
        check_text("z", s, c6)
        okz = c6["seen"] == 0
        print(f"  {'✓' if okz else '✗'} 「{s}」→ 不计入")
        fail += not okz

    print("\n  ✓ 负对照通过（13/13）" if not fail
          else f"\n  ✗ {fail} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", nargs="*", default=[])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test and not a.answers:
        return 2 if self_test() else 0
    if not a.answers:
        ap.error("--answers 必填（除非只跑 --self-test）")

    acc = scan(a.answers)
    if not acc["seen"]:
        print("没有自报字数的地方——**本次未检查（不是通过）**")
        return 0
    print(f"自报字数 {acc['seen']} 处，**对不上的 {len(acc['bad'])} 处**")
    for uid, why in acc["bad"]:
        print(f"  ⚠ {uid}: {why}")
    if acc["bad"]:
        print("\n  ★ **一个主动邀请核对的数字，如果它自己是错的，伤害比不给还大。**\n"
              "    Virchow #109 第 1 轮实测：两席各自独立抓到同一处，"
              "token-efficiency 套组因此 −0.0700，是那一轮唯一为负的套组。")
    else:
        print("  ✓ 每一处自报字数都数得对")
    return 1 if acc["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())
