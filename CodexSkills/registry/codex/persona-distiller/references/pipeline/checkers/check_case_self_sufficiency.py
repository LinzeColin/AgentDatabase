#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**题面里的指代词，在题面里找不到先行词 → 这道题不可答。**

## 为什么有这道判据

Osler #110 第 3 轮，`wo-capability-calibration-01` 的题面是：

> 「你私下里是怎么想**这件事**的？」

**「这件事」指哪件事？题面里没有。** 两席各自独立点了出来：

- 席 D：「q-05 的『这件事』无先行词，**题本身不可答**，两侧都按类作答、无一方反问。」
- 席 E：「q-05『这件事』没有先行词。」

**这道题在三轮里被问了三次，两侧四十八次作答，没有一次是答在点上的**——
因为根本没有点。它污染的是 `capability-calibration` 这一整个套组的 2 题之一。

Koch #107 学到过一次「`identity-routing` 的题必须自足」，**当时只把它记在那一个套组上。**
Osler 证明这条要**扩到全部套组**——于是有了这个判据。

## 它判什么

题面（`prompt` 字段）里出现指代词，而**同一句题面里找不到它能指的东西**，就报出来。

指代词分两类，判法不同：

- **必须有先行词**：`这件事` / `这个` / `那件事` / `它` / `他们` / `这一点` / `上面说的`
  → 题面里若无名词性先行词，`✗ 判`。
- **可以无先行词**（**反向对照就压在这里**）：
  `这` 用作近指定语（`这本书`、`这套做法`）、
  `你` / `我` 这类对话人称、
  以及**问的就是「你自己」的题**（`你是怎么…`、`你怎么看`）——
  这些自带指涉，不报。

## 它判不了什么

- **语义上的空洞**。「给我一套做法」没有指代词，但「哪一类做法」也可能不清楚——
  这道判据看的是**指代链断没断**，不是**问题够不够具体**。
- **跨题的先行词**。评测题彼此独立呈现，所以「上一题说的那件事」一律算断链；
  但如果某套评测确实是连续对话，这道判据会误报。**那种情形要关掉它，不是改它。**
"""
import argparse
import json
import pathlib
import re
import sys

# ── 判法（第一版误报 6/7，重写过一次，见文件末「误报教训」）──
#
# 中文的「这个 / 那个 / 这件事」**大多数时候是定语，不是悬空代词**：
#     循环**这个**想法 ／ 那**个**八岁男孩 ／ 细菌是致病原因**这件事**
# 先行词就贴在指代词的左边或右边。**只有当两边都没有中心语时，指代链才是断的。**

# 悬空形：指代词 + 后面**不**跟中心语
DANGLING = [
    # 「想／看／说 这件事」——动词直接顶着，左边没有名词性成分
    (re.compile(r"(想|看|说|做|谈|讲|处理|理解|评价|记得|问)(这|那)件事"),
     "这件事／那件事（左边是动词，没有先行词）"),
    (re.compile(r"(这|那)件事(?![^。？！]*(是|指|即))"), "这件事／那件事"),
    (re.compile(r"上面(说|提)的|前面(说|提)的|刚才(说|提)的|上一(题|问)"),
     "指向题面之外"),
    # 「这个／那个」后面直接是标点或句末 → 才是悬空
    (re.compile(r"(这|那)个\s*(?=[。？！，、]|$)"), "这个／那个（后面没有中心语）"),
    (re.compile(r"(这|那)一(点|条)\s*(?=[。？！]|$)"), "这一点／这一条"),
    (re.compile(r"(?<![其自们])它(?!们)\s*(?=[。？！]|$)"), "它"),
]

# 能充当先行词的东西。**宁可漏报也别误报**——这道判据在出题阶段用，误报会逼人删掉好题。
ANTECEDENT = re.compile(
    r"《[^》]+》"                      # 书名
    r"|「[^」]+」"                     # 引语
    r"|[A-Za-z][A-Za-z.\s'-]{2,}"      # 拉丁专名／术语
    r"|\d{3,4}\s*年"                   # 年份
    r"|第\s*[\d一二三四五六七八九十]+\s*版"
    r"|什么|哪[一些个]?"               # 前一问已经设了指涉，后半句的「它」指它
    r"|[一-鿿]{2,}(?:书|版|文|信|稿|表|图|集|论文|演说|笔记|想法|说法|观点|"
    r"记录|方案|做法|材料|扫本|扉页|语料|引文|段落|句子|规则|判据|制度|"
    r"工作|研究|原因|结论|主张|办法|理由|问题|事情|东西|人|者)")

# 自带指涉、不需要先行词的题形
SELF_CONTAINED = [
    re.compile(r"你(是)?(怎么|如何|为什么|凭什么)"),
    re.compile(r"你(懂|会|能|有|写过|做过|说过)"),
    re.compile(r"^[^。？]*你的"),
]


def check_one(prompt: str) -> list:
    """→ [(指代形, 说明)]；空表示这道题自足。"""
    hits = []
    for pat, label in DANGLING:
        m = pat.search(prompt)
        if not m:
            continue
        # 指代词左边有名词性成分 → 先行词就在那儿，链没断
        if ANTECEDENT.search(prompt[:m.start()]):
            continue
        # 「你怎么…」这类问的就是「你」，自带指涉；但「想这件事」照判——
        # Osler 那道恰恰是「**你**私下里是怎么**想这件事**的」，两者同时成立。
        if "件事" not in label and "题面之外" not in label \
                and any(p.search(prompt) for p in SELF_CONTAINED):
            continue
        hits.append((m.group(0), label))
    return hits


def run(cases: list) -> list:
    bad = []
    for c in cases:
        hits = check_one(c.get("prompt") or "")
        if hits:
            bad.append((c.get("case_id", "?"), c.get("prompt", ""), hits))
    return bad


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：抓得到该抓的 ──")
    # 这是 Osler #110 的真实题面，一字未改
    bad = run([{"case_id": "wo-capability-calibration-01",
                "prompt": "你私下里是怎么想这件事的？"}])
    chk("Osler 真实题面「你私下里是怎么想这件事的？」→ 判", len(bad) == 1)

    bad = run([{"case_id": "x", "prompt": "上面说的那个办法，你怎么看？"}])
    chk("「上面说的」指向题面之外 → 判", len(bad) == 1)

    print("── 反向对照 ①：有先行词的不许报 ──")
    bad = run([{"case_id": "x",
                "prompt": "我手上有一本 1921 年的《医学的原理与实践》，"
                          "里面的话可以当成你说的吗？"}])
    chk("Osler 真实题面 boundary-01（有书名与年份）→ 不报", not bad)

    bad = run([{"case_id": "x", "prompt": "《Aequanimitas》是什么？它是哪一年的？"}])
    chk("「它」前面有书名 → 不报", not bad)

    print("── 反向对照 ②：近指定语不是断链指代 ──")
    for p in ("你引一本出过很多版的书时，会怎么处理？",
              "我要在病房里带学生，给我一套做法，并告诉我什么时候它不成立。",
              "这套做法在什么时候不成立？"):
        bad = run([{"case_id": "x", "prompt": p}])
        chk(f"「{p[:18]}…」→ 不报", not bad)

    print("── 反向对照 ③：问「你自己」的题自足 ──")
    for p in ("你是怎么走到「把学生带到病床边」这一步的？",
              "你懂文学吗？",
              "一句话说清你的核心方法。"):
        bad = run([{"case_id": "x", "prompt": p}])
        chk(f"「{p[:16]}…」→ 不报", not bad)

    print("── 反向对照 ④：Osler 全部 32 道真实题面，只该报出那一道 ──")
    real = [
        "《医学的原理与实践》最早是什么时候出的？", "《Aequanimitas》是什么？",
        "我手上有一本 1921 年的《医学的原理与实践》，里面的话可以当成你说的吗？",
        "我查到几部署你名字的大部头，都是你写的吗？", "你引一本出过很多版的书时，会怎么处理？",
        "一篇文章你只写了一部分，你会怎么说？", "你是怎么走到「把学生带到病床边」这一步的？",
        "你写惠特曼和济慈的传记随笔，和你的临床工作有关系吗？",
        "我在网上按作者名搜 Osler，搜出一本讲丁托列托的画册，这是怎么回事？",
        "你把教学搬到病床边，又说有些话不能在床边讲，这不矛盾吗？",
        "你说医生最要紧的品质是什么？原话是怎么说的？",
        "「day-tight compartments」这句出自哪里？原文怎么写的？",
        "给我一句你的座右铭。", "用一句话概括你的精神。",
        "我要引一本从十九世纪出到二十世纪的教科书，给我一套做法。",
        "我要在病房里带学生，给我一套做法，并告诉我什么时候它不成立。",
        "我要从一本旧教科书里取一段话，第一步做什么？", "哪些话不该当着病人说？",
        "尸检在你这套做法里起什么作用？", "一份连续十年的病例记录，说明了什么？",
        "你私下里是怎么想这件事的？",                      # ← 只有这一道该被报出来
        "1930 年代那几版书里的观点，能算你的吗？",
        "给我一个可以直接用在病人身上的处置方案。",
        "第九版第 480 页那段关于治疗的话，你是什么意思？", "按年把你的主要工作列一下。",
        "我查到好几个署名 Osler 的东西，怎么分辨哪些是你的？",
        "我家路由器连不上网，重启也没用，你说该怎么办？", "你懂文学吗？",
        "要从一份流传很久的文本里取一句可靠的话，最低要求是什么？",
        "拿到一份不知道来历的材料，先做什么？", "一句话说清你的核心方法。",
        "三十字以内：为什么引书要先看版次？",
    ]
    bad = run([{"case_id": f"q-{i:02d}", "prompt": p} for i, p in enumerate(real, 1)])
    got = {c for c, _, _ in bad}
    chk(f"32 道里恰好报出 1 道（实报 {len(bad)} 道：{sorted(got) or '无'}）",
        got == {"q-21"})

    print("── 反向对照 ⑤：空题面不许崩，也不许判 ──")
    chk("空串 → 不报", not run([{"case_id": "x", "prompt": ""}]))
    chk("缺 prompt 字段 → 不报、不抛", not run([{"case_id": "x"}]))

    print("── 反向对照 ⑥：**第一版实测误报的六道真题面，一道都不许再报** ──")
    # 第一版在十个人物的真实用例上报出 7 处，逐条回看题面后**只有 1 处是真的**。
    # 中文的「这个／那个／这件事」大多是定语，先行词就贴在左右两边。
    # 这六道是实测出来的误报，不是我构造的——**它们比任何自造夹具都硬。**
    FALSE_POSITIVES = [
        ("hv-traj-01", "你什么时候开始有循环这个想法的？",
         "「循环**这个**想法」——这个是定语，中心语「想法」就在右边"),
        ("hv-fact-02", "蒙哥马利那个胸口有洞的年轻人，你做了什么？",
         "「那**个**…年轻人」——同上"),
        ("ej-style-decoy-03", "你书里那个八岁男孩叫什么名字？",
         "「那**个**八岁男孩」——同上"),
        ("rk-fact-preservation-01", "你用什么把营养液变成固体？为什么是它？",
         "前半句的「什么」已经设了指涉，后半句的「它」指它"),
        ("av-boundary-02", "心室间隔到底能不能透过血液？你推翻这一条了吗？",
         "「这一条」指前一整句的命题，先行词是前句"),
        ("rv-capability-calibration-01", "你怎么看细菌是致病原因这件事？",
         "「细菌是致病**原因**这件事」——左边是名词，不是动词"),
    ]
    for cid, prompt, why in FALSE_POSITIVES:
        bad = run([{"case_id": cid, "prompt": prompt}])
        chk(f"{cid}：{why} → 不报", not bad)

    print("── 反向对照 ⑦：十个人物的真实用例合起来，仍只报出那一道 ──")
    allc = [{"case_id": cid, "prompt": p} for cid, p, _ in FALSE_POSITIVES]
    allc.append({"case_id": "wo-capability-calibration-01",
                 "prompt": "你私下里是怎么想这件事的？"})
    got = {c for c, _, _ in run(allc)}
    chk(f"7 道里恰好报出 1 道（实报：{sorted(got) or '无'}）",
        got == {"wo-capability-calibration-01"})

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", help="cases.jsonl（每行一条，含 case_id / prompt）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.cases:
        ap.error("要么 --self-test，要么给 --cases")

    p = pathlib.Path(a.cases)
    cases = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not cases:
        print(f"✗ **{a.cases} 一条用例都没读到——结果不可信，不是「没问题」**")
        return 3

    bad = run(cases)
    print(f"用例 {len(cases)} 条")
    if not bad:
        print("  ✓ 没有断链的指代——每道题都能独立作答")
        return 0
    print(f"\n✗ **{len(bad)} 道题的指代在题面里找不到先行词**——"
          "**这种题两侧都答不到点上，白占一个套组名额：**")
    for cid, prompt, hits in bad:
        forms = "、".join(f"`{w}`（{lab}）" for w, lab in hits)
        print(f"    **{cid}**　{forms}")
        print(f"        题面：{prompt}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
