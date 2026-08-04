#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同一份载荷里，**一处说「我没有这个」，另一处却给了出来**。

## 触发本判据的实例（席 E，Jenner #104，一条评语里点了两处）

> B 写「同年我因此入了皇家学会」是错的（当选在次年），
> **而且与它自己在 `long-horizon-02` 说的「入会确切日子不在我手上这批材料里」互相否定**，
> 同时它这里说「月份我不报，有两说」，**别处又两次报出 1788 年 3 月 13 日**。

**这不是风格问题，是正确性问题**：读者拿到的两句话互相取消。
而它跨题出现——**逐题看每一题都说得通**，只有把整份载荷放在一起才看得见。

## 判据（两条同时成立才报）

1. 某一题里有**弃权句**：在同一句中出现「不在我手上／我不报／没有记录／不能确定／
   拿不准／无从确认」等，且该句带一个**主题词**（弃权句里的专名或名词短语）
2. **另一题**里，同一个主题词的 40 字内出现**具体值**（年份、完整日期、卷页号）

★ **两条是「且」，而且必须跨题**：同一题里「我不确定，但材料里写的是 X」
是诚实的分层表述，**不报**。

## 它不做什么

- **不判哪一句对。** 它只说这两句互相取消，**由人去看哪句该改**。
- **不判事实真伪。** 「当选在次年」那个错是评委用外部知识判的，本件判不了。
- **不跨人物比。** 只在同一份载荷内。

## 分母

**必须连「弃权句共几句」一起读。** 一句弃权都没有时报「未核」，**不报「通过」**。
"""
import argparse
import json
import pathlib
import re
import sys

# 弃权句：说「这个我没有／我不给」
DISCLAIM = re.compile(
    r"(不在我手上|不在我这批|我不报|没有记录|不能确定|无法确认|无从确认|拿不准|"
    r"我手上没有|材料里没有|查不到|说不准|不敢断言)")
# 具体值：年份 / 完整日期 / 卷页
CONCRETE = re.compile(
    r"1[5-9]\d{2}\s*年|20\d{2}\s*年|\d{1,2}\s*月\s*\d{1,2}\s*日|"
    r"第?\s*\d+\s*[卷期]|\d+\s*[-–]\s*\d+\s*页|p{1,2}\.\s*\d+")
# 主题词候选：汉字 2–6 连字的 n-gram（贪婪整串取不到共同子串——第一版就栽在这），
# 或首字母大写的西文词组。**再按「特异性」筛一道**，见 topics_of。
HAN = re.compile(r"[一-龥]+")
WEST = re.compile(r"[A-Z][A-Za-z.]{2,}(?:\s+[A-Z][A-Za-z.]{2,}){0,2}")
NGRAM_MIN, NGRAM_MAX = 3, 8
SENT = re.compile(r"[^。；！？\n]{4,120}")

STOP = {"我不报", "没有记录", "不能确定", "无法确认", "拿不准", "查不到", "说不准",
        "这批材料", "我手上", "材料里", "确切", "具体", "如果", "因为", "所以",
        "但是", "不过", "那么", "这样", "这里", "别处", "以及", "并且", "而且",
        "不在我手上", "不敢断言", "无从确认", "不在我这批"}
NEAR = 40


def topics_of(sentence):
    """→ 弃权句里的主题词候选（n-gram）。**停用词剔掉，含弃权词的剔掉。**

    ★ 第一版用 `[一-龥]{2,8}` 贪婪整串，取到「入会确切日子不在」这种东西，
      两边根本没有共同子串——**正向用例当场不过**。改成 n-gram。
    """
    out = set(WEST.findall(sentence))
    for run in HAN.findall(sentence):
        for n in range(NGRAM_MIN, NGRAM_MAX + 1):
            for i in range(len(run) - n + 1):
                w = run[i:i + n]
                if w not in STOP and not DISCLAIM.search(w) and not any(s in w for s in STOP):
                    out.add(w)
    return out


# ★ 虚词字：全部由这些字组成的 n-gram 一律不算主题词。
#   第一版没有这一道，真数据实测抽出「我手」「没有」「也不」「的东西」当主题词，
#   **12 条抽样里 0 条是真的**。
FUNC = set("我你他她它的了是在有没不也就都还很和与及或对把被给让从到于之其此那这"
           "个些么什么样子上下里外前后中间时候地得着过来去要会能可以所因为但而且然则"
           "如果虽然并且以及至于关于对于手上具体细处东西记录材料两三四五六七八九十")
def specific(topics, texts, max_frac=0.20):
    """只留**特异**的主题词：出现在 ≥2 份答案里，但不超过 max_frac。

    没有这一道，「那年」「我的」这类到处都有的 2-gram 会把精确率打穿。
    """
    n = max(1, len(texts))
    keep = set()
    for w in topics:
        if all(ch in FUNC for ch in w):          # ★ 全虚词 → 不是主题
            continue
        c = sum(1 for t in texts.values() if w in t)
        if 2 <= c <= max(2, int(n * max_frac)):
            keep.add(w)
    # 同一处只留最长的那些：短 n-gram 多半是长词的子串
    return {w for w in keep if not any(w != v and w in v for v in keep)}


def evaluate(answers):
    """→ (问题列表, 计量)。**只报跨题的互相取消。**"""
    texts, unreadable = {}, []
    for cid, v in (answers or {}).items():
        s = (v.get("answer") or v.get("text") or "") if isinstance(v, dict) else v
        if isinstance(s, str):
            texts[cid] = s
        else:
            # ★ 不静默强转：读不出的要报出来，否则「没读到」会被当成「没问题」
            unreadable.append(f"{cid}（{type(s).__name__}）")

    claims = []          # (题号, 主题词, 弃权原句)
    for cid, t in texts.items():
        for s in SENT.findall(t):
            if DISCLAIM.search(s):
                for w in specific(topics_of(s), texts):
                    claims.append((cid, w, s.strip()))

    problems = []
    for cid, w, s in claims:
        for other, t in texts.items():
            if other == cid:
                continue                     # ★ 同一题内的分层表述不报
            for m in re.finditer(re.escape(w), t):
                seg = t[max(0, m.start() - NEAR): m.end() + NEAR]
                hit = CONCRETE.search(seg)
                if hit:
                    problems.append(
                        f"{cid} 说「{s[:44]}」——而 {other} 在「{w}」附近给出了"
                        f"「{hit.group(0)}」")
                    break
            else:
                continue
            break

    info = {"答案数": len(texts), "**弃权句里的主题词**": len(claims),
            "跨题互相取消的": len(problems)}
    if unreadable:
        info["**读不出正文的**"] = f"{len(unreadable)} 条 → {unreadable[:5]}（**没读到 ≠ 没问题**）"
    if not claims:
        info["状态"] = "**一句弃权都没有——未核，不是通过**"
    return problems, info


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★★ 正向：Jenner 那一幕——一处说没有，另一处报出来了 ──")
    p, _ = evaluate({"a": "入皇家学会的确切日子不在我手上这批材料里。",
                     "b": "我入皇家学会是 1788 年 3 月 13 日的事。",
                     "c": "那年天气不好。", "d": "我在乡下行医。", "e": "牛痘的事另说。"})
    chk(f"报出 {len(p)} 处", bool(p))

    print("── ★★★ 反向对照 ①：**同一题内**的分层表述是诚实的，不报 ──")
    p2, _ = evaluate({"a": "入皇家学会的确切日子不在我手上这批材料里，"
                           "别人转述说是 1788 年 3 月 13 日，我不担保。",
                      "b": "我入皇家学会那件事说来话长。", "c": "那年天气不好。",
                      "d": "我在乡下行医。", "e": "牛痘的事另说。"})
    chk("同题内 → 不报", not p2)

    print("── ★★ 反向对照 ②：两处谈的不是同一件事 → 不报 ──")
    p3, _ = evaluate({"a": "入皇家学会的确切日子不在我手上这批材料里。",
                      "b": "我做那次接种是 1796 年 5 月 14 日。", "c": "那年天气不好。",
                      "d": "我在乡下行医。", "e": "牛痘的事另说。"})
    chk("主题词不重合 → 不报", not p3)

    print("── ★ 反向对照 ③：另一处只是提到，没给具体值 → 不报 ──")
    p4, _ = evaluate({"a": "入皇家学会的确切日子不在我手上这批材料里。",
                      "b": "我入皇家学会那件事，说来话长。", "c": "那年天气不好。",
                      "d": "我在乡下行医。", "e": "牛痘的事另说。"})
    chk("无年份/日期/卷页 → 不报", not p4)

    print("── ★★ 反向对照 ④：分母——一句弃权都没有时报「未核」，不报「通过」 ──")
    _, info = evaluate({"a": "我 1796 年做的那次接种。"})
    chk(f"主题词 {info['**弃权句里的主题词**']}，状态：{info.get('状态','（无）')[:14]}",
        info["**弃权句里的主题词**"] == 0 and "未核" in info.get("状态", ""))

    print("── ★★ 反向对照 ⑤：停用词不许当主题词（否则「确切」会到处命中）──")
    t = topics_of("入皇家学会的确切日子不在我手上这批材料里")
    chk(f"含「皇家学会」且不含停用词", "皇家学会" in t and "确切" not in t and "我手上" not in t)
    sp = specific(t, {"a": "入皇家学会的确切日子不在我手上这批材料里",
                      "b": "我入皇家学会是 1788 年", "c": "无关", "d": "无关", "e": "无关"})
    chk(f"特异性筛后 {sorted(sp)}——留住了含「皇家学会」的那个（最长子串优先，"
        f"所以是「入皇家学会」不是「皇家学会」）",
        any("皇家学会" in w for w in sp))
    print("── ★★ 反向对照 ⑤b：到处都有的词要被特异性筛掉 ──")
    everywhere = {c: "那年我在乡下行医" for c in "abcdefghij"}
    everywhere["a"] = "那年的确切日子不在我手上，我在乡下行医"
    sp2 = specific(topics_of(everywhere["a"]), everywhere)
    chk(f"「乡下行医」出现在 10/10 份里 → 被筛掉（剩 {sorted(sp2)}）",
        not any("乡下行医" in w for w in sp2))

    print("── ★★ 反向对照 ⑤c：答案值不是字符串 → **报出来**，不静默强转 ──")
    _, iu = evaluate({"a": {"answer": ["列表不是字符串"]}, "b": "正常文本。",
                      "c": 12345})   # ★ 这两种正是真数据里让第一版崩掉的形态
    chk(f"读不出的被报出：{iu.get('**读不出正文的**', '（没报）')[:30]}",
        "**读不出正文的**" in iu)

    print("── ★ 反向对照 ⑥：空载荷不报错，也不许读成通过 ──")
    p6, i6 = evaluate({})
    chk("空 → 无问题且明说未核", not p6 and "未核" in i6.get("状态", ""))

    print("── ★ 反向对照 ⑦：一处弃权、多处给值，只报一次不刷屏 ──")
    # ★ 夹具给 10 份：真实载荷是 32 题，5 份会让 3/5=60% 撞上特异性上限，那是夹具不真实
    fx = {c: f"第 {c} 题的无关内容。" for c in "defghij"}
    fx.update({"a": "入皇家学会的日子不在我手上。", "b": "入皇家学会是 1788 年。",
               "c": "入皇家学会那年是 1788 年 3 月。"})
    p7, _ = evaluate(fx)
    chk(f"报 {len(p7)} 条（同一弃权句只报一次）", len(p7) == 1)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", help="{case_id: 答案} 的 JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.answers:
        print("✗ **什么都没核**——没给 --answers。这不是通过。")
        return 2

    d = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    if isinstance(d, list):
        d = {x.get("case_id"): x for x in d if isinstance(x, dict)}
    problems, info = evaluate(d)
    for k, v in info.items():
        print(f"  {k}: {v}")
    for p in problems[:12]:
        print(f"  ⚠ {p}")
    if problems:
        print("\n  ⚠ **本件只说这两句互相取消，不判哪一句对**——由人去看该改哪一句。")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
