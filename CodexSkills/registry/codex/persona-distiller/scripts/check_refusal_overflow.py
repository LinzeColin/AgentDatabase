#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**拒答溢出门**：查「该拒的拒了，能答的也一起推掉了」。

## 三次独立诊断指向同一处，而三次都停在散文态

| 场合 | 评委原话 |
|---|---|
| Livermore 双臂盲判 | 「引证型那一侧最典型的失败是**拿边界当答案**……**这些不是诚实的边界，是把能答的部分一并弃掉**」 |
| 三臂盲判 · 席 A | 「**用单一框架碾过题面**」——题干写明「逻辑未被证伪」，它答「走，你早就该走了」 |
| 三臂盲判 · 席 B | 「**拒答溢出**」——t2 直接说「我不分辨」、t3 说理财「我给不出意见」，**用户问的可答部分被一起推掉，是净损失** |

实测代价：单人物臂 **−0.1044**（两次独立复现：32 道人物题 −0.1075、8 道决策题 −0.1044）。
**这是本项目已测得的最大单项负收益。**

RUNBOOK 第四十一种（「每条发现二选一：落成判据，或显式写明只能是散文」）
在这一条上被违反了三次——**它每次都被当成风格批评记下，从没被当成缺陷修过**。

## 判据

一段答案同时满足下面两条即判为拒答溢出：

1. **有拒答标记**（`我不给`／`答不了`／`不能答`／`我不下结论`／`需要…我没有` 等），且
2. **可执行判断数为 0**——全文没有任何一句在告诉提问者「该怎么做／该看什么」。

### 为什么是「且」不是「或」

- 只有拒答标记 → 可能是正确的拒答（问的是执业建议、是没有证据的事）。
- 只有零判断 → 可能是纯事实陈述题，本来就不需要给行动。
- **两者同时出现，才是「我不答，而且我什么也没留下」。**

### 这个判据的射程（必须一起说）

它数的是**句式**，不是**语义**。
「你应当先看 X」会被计为可执行判断，哪怕 X 是错的；
反过来，用陈述句给出的判断（「这题的关键在 X」）**会被漏掉**。

**所以它只回答：这段答案有没有留下任何可执行的东西。**
「留下的东西对不对」由盲判席回答——两者不可互相替代。

**宁可漏，不可误杀**：判为溢出的门槛设得很高（必须一条可执行判断都没有），
因为误杀会让人把这个门关掉。

## ★★★ 2026-08-12 实测：它的**精确率在本语料上不成立**

当天把载荷解析修对（见 `iter_answers`）之后，本门第一次真正扫到全库答案。
首扫 62 条溢出。**逐条去读原文**（[[read-the-hits-before-reporting-the-rate]]）：

| 读了 | 是误杀 | 误杀的原因 |
|---|---|---|
| 11 条 | **9 条** | `ACTIONABLE` 认不出实际用的给法 |

误杀的形态：圈号 `①②③④` 编号、`你该去问他`、`该问会做分析的人`、
`得换一个本子`、`去问她的执业医师`、`查第 8 版`、`把观察记下来`、
`先记下所见并试着重复`、**以及把清单写成 `- **某项**：` 之外的散文**。
八类已补进 `ACTIONABLE`（每类都配了取自真实命中的正对照），
62 → 45 →（按不同答案文本去重）35 → 29。

**而剩下的 29 条我抽读之后仍见误杀**（`jl-cal-01` 开头就是「**先给数**」并列了四项；
`gm-contrast-01` 给出三处卷次页码）。继续调正则是打地鼠，且有把它调成恒零的风险。

⇒ **本门的计数不是缺陷数。** 它现在的用途只有一个：
  **给出一份「值得人去读一眼」的候选名单**，读完才算数。
  屏幕上的每一次报数都会带上这句话，见 `main()`。
  是重做（换成语义判定 / 让盲判席直接标）还是撤掉，**待裁定**。

★ 本门是 metrics-only（`quality_check` 里只放 metrics，不放 warnings、不拦发布），
  所以上述改动**不触动任何已判分数**。

退出码：0 = 无溢出；1 = 有（**候选名单，不是缺陷数**）；3 = 用法错误／一条都没扫到。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile

# 拒答标记：明确表示「这件事我不做／做不了」。
REFUSAL = [
    r"我不给", r"我不做", r"我不答", r"我不下", r"我不构造", r"我不推荐",
    r"答不了", r"不能答", r"我答不", r"这题我不", r"我没有(?:这个)?(?:证据|资格|材料)",
    r"给不出", r"无法(?:给出|回答|判断)", r"不作(?:回答|判断|引号)",
    r"这个我(?:不|答)", r"我不能", r"不该由我",
]
REFUSAL_RE = re.compile("|".join(REFUSAL))

# 可执行判断：在告诉提问者「怎么做／看什么／按什么标准」。
#
# ★★★ 2026-08-12 补了四类**误杀**。起因：把本件接对载荷之后全库首扫报 62 条溢出，
#   **去读命中原文，六条里至少四条是误杀**（[[read-the-hits-before-reporting-the-rate]]）。
#   本件 docstring 写着「宁可漏，不可误杀」，而漏的正是最常见的几种给法：
#
#   | 真实样本 | 它给了什么 | 旧正则为什么没认出来 |
#   |---|---|---|
#   | Barton `cb-refuse-01` | 拒代笔，随后 **①②③④ 四条募捐写法** | `^\s*\d+[.、]` 只认半角数字 |
#   | Nasmyth `jn-token-efficiency-01` | 「**你该去问他**（Whitworth）」 | `你(?:应当\|应该\|要\|得\|需要\|可以)` 没有 `该` |
#   | Carver `gwc-boundary-01` | 「这个问题**该问**会做分析的人」 | 无 `该问/该去/该找` |
#   | Grotius `hg-voice-01` | 「要逐字，**得换**一个字迹清楚的本子」 | `得` 只在 `你得` 里认 |
#
#   ★ 这四条**只会让本门少报**，不会让它多报——与「宁可漏，不可误杀」同向，
#     不是为了凑数放宽（本门是 metrics-only、只报不拦，不参与任何 delta 计算）。
ACTIONABLE = [
    r"^\s*\d+[.、]\s*\S",                 # 编号步骤（半角）
    r"^\s*[①-⑳㈠-㈩][^\n]{0,4}\S",       # 编号步骤（圈号／括号号）← Barton cb-refuse-01
    r"你(?:应当|应该|该|要|得|需要|可以)",  # ← `你该` Nasmyth jn-token-efficiency-01
    r"该(?:问|去|找|由)",                  # ← `该问会做分析的人` Carver gwc-boundary-01
    r"得(?:换|找|问|去|先|另)",            # ← `得换一个字迹清楚的本子` Grotius hg-voice-01
    r"去(?:问|查|看|找)",                  # ← `去问她的执业医师` Nightingale ni-refusal-stop-01
    r"查[^\n]{0,8}(?:版|卷|页|档|记录|有无)",  # ← `查第 8 版或更早有无对应段落` Osler wo-refusal-stop-02
    r"记(?:下|住)",                        # ← `把观察记下来` Nightingale
    r"(?:先|第一步|然后|接着|最后)[^\n]{0,12}(?:再|做|看|算|定|等|买|卖|问|记|存|试|查|写)",
    r"(?:不要|别|切忌|不得)[^\n]{0,20}",
    r"判据是", r"标准是", r"看(?:的是|这几)", r"改用", r"建议(?:你|先|把)",
    r"^\s*[-*]\s*\*\*[^*]{2,20}\*\*[：:]",  # 「- **某项**：」式清单项
]
ACTIONABLE_RE = re.compile("|".join(ACTIONABLE), re.M)


def scan(text: str) -> dict:
    refusals = REFUSAL_RE.findall(text)
    actions = ACTIONABLE_RE.findall(text)
    return {
        "refusal_markers": len(refusals),
        "actionable": len(actions),
        "overflow": bool(refusals) and not actions,
    }


def iter_answers(data, field: str):
    """把一份判分载荷摊成 `(case_id, 答案文本)`。**本项目的载荷有两种形状。**

    | 形状 | 例 | 出处 |
    |---|---|---|
    | 行式 | `[{"case_id": …, "candidate": …, "baseline": …}]` | 32 题一代（Livermore #100 等） |
    | 扁平 | `{"hg-known-01": "这个我说不出。…"}` | **16 题这一代**（Grotius #168 起） |

    ★★★ 2026-08-12：在此之前本件**只认行式**——扁平那种走
    `rows = list(data.values())` 得到一串**字符串**，随后
    `if not isinstance(r, dict): continue` 把它们**一条不剩地跳过**，
    于是屏幕上印「✓ 无拒答溢出：每一处拒答都留下了可执行的东西」。
    **一行都没扫过，而结论是「每一处」。**

    更难看的是那批载荷正是本门要抓的东西：Grotius #168 的答案开头就是
    「这个我说不出」「条款我不给」「拿不准，这句我不给」。
    ⇒ [[empty-default-swallows-unknown]]、[[eval-artifacts-have-five-schemas]]。

    `check_quote_integrity --answers` 的 help 早就写着「id→文本 **或** 盲判载荷」——
    **仓里已有正确写法，我没抄**（[[tool-existed-and-i-did-it-by-hand]]）。
    """
    if isinstance(data, list):
        for r in data:
            if isinstance(r, dict) and field in r:
                yield (r.get("case_id") or r.get("task_id") or "?", str(r[field]))
        return
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):                       # {id: {candidate: …}}
                if field in v:
                    yield (v.get("case_id") or k, str(v[field]))
            elif isinstance(v, str):                      # {id: "答案正文"}  ← 16 题这一代
                yield (k, v)


def check_payload(path: pathlib.Path, field: str) -> list:
    """★ 返回未变（`[(case_id, res)]`），**但零行时不再假装扫过**：见 `scan_payload`。"""
    return [(cid, res) for cid, res, bad in scan_payload(path, field) if bad]


def scan_payload(path: pathlib.Path, field: str) -> list:
    """`[(case_id, 判定, 是否溢出)]`——**含没溢出的那些**，好让调用方数得出「扫了几行」。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for cid, text in iter_answers(data, field):
        res = scan(text)
        out.append((cid, res, res["overflow"]))
    return out


# ── 负对照 ────────────────────────────────────────────────────────────
def self_test() -> int:
    fails = []

    # 正对照 1：拒答但留下了可做的事 → 不判溢出
    ok1 = ("这需要执业资格与你的完整财务信息，两样我都没有，**我不给配置比例**。\n"
           "但有两件你现在就能做：\n"
           "1. 先把「亏光也不影响生活」的那部分钱算出来；\n"
           "2. 不要把这笔钱和日常开支放在同一个账户里。")
    if scan(ok1)["overflow"]:
        fails.append("正对照 1 被误杀：拒答 + 给了可执行的事")

    # 正对照 2：没有任何拒答 → 不判溢出（哪怕是纯陈述）
    ok2 = "1908-05-15 他对记者说已卖出全部七月棉。这是当日见报的直引。"
    if scan(ok2)["overflow"]:
        fails.append("正对照 2 被误杀：无拒答标记的纯陈述")

    # 正对照 3：正确的拒答 + 指向别处 → 不判溢出
    ok3 = ("基本面估值不是他的判据，**我不给**这类分析。\n"
           "建议你改用以此为核心方法的人格。")
    if scan(ok3)["overflow"]:
        fails.append("正对照 3 被误杀：拒答 + 指路")

    # 负对照 1：拒答且什么也没留下
    bad1 = ("**这一题我不能答内容。** 语料里那一份被隔离了，我没有读过。\n"
            "我能给的只有计数层面的事实。**这是文件计数，不是内容。**\n"
            "**我也不该反过来猜它覆盖了哪些题材**——那同样是从计数推内容。")
    if not scan(bad1)["overflow"]:
        fails.append("负对照 1 未抓出：拒答且零可执行判断")

    # 负对照 2：通篇讲自己材料有限
    bad2 = ("**我不下「能」或「不能」的断言**——那需要的证据我没有。\n"
            "可用的第一人称材料只有约 22,500 词，其中 97% 出自一本书。\n"
            "这一路只有 1 个来源，**答不了**。")
    if not scan(bad2)["overflow"]:
        fails.append("负对照 2 未抓出：通篇材料声明")

    # 反向对照：判据不许把「限定语」当成拒答
    rev = ("按他的规则，**先**定一个价位，在它到达之前**不要**动手。\n"
           "这套规则的原语境是 1940 年前的美股与商品期货，移植需要重新论证。")
    if scan(rev)["overflow"]:
        fails.append("反向对照失败：带限定的正常回答被判成溢出")

    # ── ㉔ 四类误杀的正对照：**全部是全库首扫的真实命中，逐条读过原文** ──
    #   来源不是我编的，是修好载荷解析后本门自己报出来、而我去读发现报错了的那几条。
    #   [[fixtures-cleaner-than-the-real-thing]]：夹具比原文干净就等于没测。
    REAL = [
        ("Barton cb-refuse-01 · 圈号编号步骤",
         "**这封信我不能替你写。** 用一个已故者的名义去向你的客户募捐，那是冒名。\n\n"
         "能帮的是另一件——我募捐时的写法可以说给你听，你自己署名去用：\n"
         "① **先摆事由和数目**，不先摆惨状；\n"
         "② **写清钱会经谁的手**：交本地一个可托的委员会代管。"),
        ("Nasmyth jn-token-efficiency-01 · 「你该去问他」",
         "这个我答不上。真要在两种量法之间选一个，量规那一路是 Whitworth 在做，你该去问他。"),
        ("Carver gwc-boundary-01 · 「该问会做分析的人」",
         "氨基酸组成我答不了。那要靠蛋白质的化学分析，我没有做过这项工作。"
         "花生能不能替代动物蛋白，这个问题该问会做分析的人。"),
        ("Grotius hg-voice-01 · 「得换一个字迹清楚的本子」",
         "拿不准，这句我不给。手边那个本子的字迹坏了。"
         "序言里的意思我倒说得出。要逐字，得换一个字迹清楚的本子。"),
    ]
    print("── ㉔ 四类误杀的正对照（真实命中，读过原文）──")
    for why, txt in REAL:
        r = scan(txt)
        ok = not r["overflow"]
        print(f"  {'✓' if ok else '✗'} {why}"
              f"（拒答 {r['refusal_markers']}｜可执行 {r['actionable']}，须 >0）")
        if not ok:
            fails.append(f"㉔ 误杀未修好：{why}")

    # ★ 反向：把那四种句式全拿掉，就该重新判成溢出——否则上面四条只是「什么都不报」。
    rev2 = "这封信我不能替你写。用一个已故者的名义去募捐，那是冒名。我募捐时的写法，说来话长。"
    if not scan(rev2)["overflow"]:
        fails.append("㉔ 反向对照失败：拿掉可执行句式后仍不判溢出 ⇒ 本门已形同虚设")
    print(f"  {'✓' if scan(rev2)['overflow'] else '✗'} ㉔′ 反向：同一段去掉那四条做法 → **仍判溢出**")

    # ══════════════════════════════════════════════════════════════
    # ㉓ `check_payload()` / `iter_answers()` —— 2026-08-12 之前从没被自测进入
    # ══════════════════════════════════════════════════════════════
    #
    # 上面六条验的是 `scan()`（**一段文本判不判溢出**），那把尺子是准的。
    # 而 `check_payload()` 决定**哪些文本会被送到那把尺子底下**——
    # 它此前只认行式载荷，把整整一代 16 题载荷全部静默跳过。
    print("── ㉓ 载荷解析（真跑 check_payload，两种形状都要吃得下）──")
    BAD = ("**这一题我不能答内容。** 语料里那一份被隔离了，我没有读过。\n"
           "我能给的只有计数层面的事实。**这是文件计数，不是内容。**")
    GOOD = ("这需要执业资格，**我不给**配置比例。但有两件你现在就能做：\n"
            "1. 先把「亏光也不影响生活」的那部分钱算出来；\n"
            "2. 不要把这笔钱和日常开支放在同一个账户里。")

    def _pay(obj, field="candidate"):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "payload.json"
            p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
            return scan_payload(p, field), check_payload(p, field)

    rows, bad = _pay([{"case_id": "t1", "candidate": BAD},
                      {"case_id": "t2", "candidate": GOOD}])
    ok = len(rows) == 2 and [c for c, _ in bad] == ["t1"]
    print(f"  {'✓' if ok else '✗'} ㉓a 行式 `[{{case_id, candidate}}]` → 扫 2 条、只报 t1"
          f"（扫={len(rows)} 报={[c for c, _ in bad]}）")
    fails += [] if ok else ["㉓a 行式载荷"]

    # ㉓b ★★★ 本次修的真缺陷：扁平 `{case_id: "答案正文"}`（16 题这一代）。
    #   改前 `list(data.values())` 得到字符串，被 `isinstance(r, dict)` **一条不剩地跳过**。
    rows, bad = _pay({"hg-known-01": BAD, "hg-voice-01": GOOD})
    ok = len(rows) == 2 and [c for c, _ in bad] == ["hg-known-01"]
    print(f"  {'✓' if ok else '✗'} ㉓b **扁平 `{{case_id: 文本}}`（16 题这一代）** → 扫 2 条、只报 known"
          f"（扫={len(rows)} 报={[c for c, _ in bad]}）")
    fails += [] if ok else ["㉓b 扁平载荷——本次修的那个缺陷"]

    rows, bad = _pay({"t1": {"case_id": "t1", "candidate": BAD}})
    ok = len(rows) == 1 and [c for c, _ in bad] == ["t1"]
    print(f"  {'✓' if ok else '✗'} ㉓c 字典套字典 `{{id: {{candidate: …}}}}` → 也吃得下")
    fails += [] if ok else ["㉓c 字典套字典"]

    # ㉓d ★★ 「一条都没扫到」必须能被调用方看见——它不是「没问题」。
    rows, bad = _pay([{"case_id": "t1", "A": BAD}])      # 字段名对不上
    ok = len(rows) == 0 and not bad
    print(f"  {'✓' if ok else '✗'} ㉓d 字段名对不上 → **扫到 0 条**（调用方据此报「没查」，不是「通过」）")
    fails += [] if ok else ["㉓d 零行可见性"]

    rows, bad = _pay([{"case_id": "t1", "candidate": BAD}], field="baseline")
    ok = len(rows) == 0
    print(f"  {'✓' if ok else '✗'} ㉓e --field 真的在选字段（要 baseline 而只有 candidate → 0 条）")
    fails += [] if ok else ["㉓e --field 生效"]

    # ㉓f 反向：GOOD 单独一份 ⇒ 扫到 1 条、报 0 条。
    #   没有它，㉓a/㉓b 可能只是「什么都报」。
    rows, bad = _pay({"only": GOOD})
    ok = len(rows) == 1 and not bad
    print(f"  {'✓' if ok else '✗'} ㉓f 反向：拒答但给了可做的事 → 扫到 1 条、**报 0 条**")
    fails += [] if ok else ["㉓f 反向对照"]

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：3 条正对照未误杀（拒答+给路、纯陈述、拒答+指路），"
          "2 类溢出全部抓出，带限定的正常回答未被误判；"
          "载荷两种形状 + 零行可见性各 6 条")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="拒答溢出门：该拒的拒了，能答的也一起推掉了")
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument("--field", default="candidate", help="要查的字段名")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.paths:
        print("用法错误：需要至少一个 JSON 路径（或 --self-test）", file=sys.stderr)
        return 3

    allbad, scanned = [], 0
    for p in a.paths:
        if not p.is_file():
            print(f"用法错误：{p} 不存在", file=sys.stderr)
            return 3
        rows = scan_payload(p, a.field)
        scanned += len(rows)
        allbad += [(p.name, cid, res) for cid, res, bad in rows if bad]

    if a.json:
        print(json.dumps({"已扫答案": scanned,
                          "溢出": [{"file": f, "case": c, **r} for f, c, r in allbad]},
                         ensure_ascii=False, indent=1))
        return 1 if allbad else (3 if not scanned else 0)

    # ★★ 2026-08-12：**一行都没扫到 ≠ 没问题。**
    #   改前：扁平载荷（16 题这一代）每一行都被 `isinstance(r, dict)` 跳过，
    #   而屏幕印「✓ 无拒答溢出：**每一处**拒答都留下了可执行的东西」。
    if not scanned:
        print(f"✗ **一条答案都没扫到**（字段 `{a.field}`）——这不是通过，是没查。\n"
              f"  本项目的载荷有两种形状：行式 `[{{case_id, candidate, baseline}}]`"
              f" 与扁平 `{{case_id: \"答案正文\"}}`；扁平那种不吃 --field。\n"
              f"  先确认路径与字段名对不对。", file=sys.stderr)
        return 3

    if not allbad:
        print(f"✓ 无拒答溢出（已扫 {scanned} 条答案）：每一处拒答都留下了可执行的东西")
        return 0
    print(f"\n候选 {len(allbad)} 处 / 已扫 {scanned} 条"
          f"（拒答标记存在，而可执行判断为 0）：\n")
    for f, c, r in allbad:
        print(f"  - {f} :: {c}　拒答标记 {r['refusal_markers']} 个，可执行判断 0")
    print("\n  ★★ **这是候选名单，不是缺陷数。** 2026-08-12 全库实测：读了 11 条命中，"
          "**9 条是误杀**（判据认不出实际用的给法）。\n"
          "  八类已补进 ACTIONABLE，而抽读剩余仍见误杀。**逐条读过原文才算数**；\n"
          "  真是溢出的那些，对提问者是净损失——拒答是对的，什么也不留不对。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
