#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选答案里**两类机器判得了的过度断言**——已故人物谈当下、指代悬空。

## 为什么有这件

Mendel #125 连续两轮，**我每修一处就引入一处，且新旧同类**（见
`_corpora/wip-mendel-125/_fix-introduces-new-defect.md`）：

| 轮 | 修什么 | 引入什么 |
|---|---|---|
| R2 | `contrast` 算术加不平 | **「至今未见数字化本」**——1884 年卒的人断言当代数字化档案现状 |
| R3 | `task-completion` 缺坐标 | **「图表在同一卷《Vereins-Jahresheft》」**——「同一」无所指，全篇没给过卷次 |

**修完之后没有任何一步去验「改的那一处自己站不站得住」**，
于是要等下一轮评委再抓一次。本件把这一步挪到**装进载荷之前**。

## 两类，各自的判据

1. **`已故人物谈当下`**——答案里出现「至今／迄今／目前／现在还／如今／当代」等
   指向说话当下的词。人物已故，**这类断言他说不出口**，除非同句标了越界。
2. **`指代悬空`**——出现「同一卷／该卷／那份 + 刊名类词」，
   而**整条答案里没有任何卷次、页码或年份**。「同一」指不到任何东西。

## ★ 它不做什么

- **不判「原文写的」后面的断言是否真在引文里**——那要跨语种比对语义，
  **本件做不到**（Mendel R3 的「谁实谁虚不在引文里」正是这一类，只能靠人）。
- **不判译文是否比原文宽**（「好收成」丢掉 `Obst-`）——同上。
- **只报不拦。** 它报的是「这句话人物说不出口／这个指代指不到东西」，
  **不判答案对不对**。

★ **落不成判据的那两类，明写在这里，不假装已解决。**
"""
import argparse
import json
import pathlib
import re
import sys

NOW_WORDS = ["至今", "迄今", "目前", "现在还", "如今", "当代", "眼下", "时至今日"]
# 同句里出现这些，说明作者自己标了越界，不算
HEDGE = ["身后", "我已故", "越界", "不是我能知道", "在世时", "我死后", "后世", "这超出"]
# ★ 卷类指代（「同一卷」）要的先行词**必须是卷次**，不是随便一个年份。
#   第一版 LOCATOR 把「1862 年」也算作先行词，于是漏掉了本件的**来源用例**：
#   Mendel R3 的 `task-completion` 说「图表在同一卷《Vereins-Jahresheft》」，
#   全篇只有数据年份（1862／1848），**一个卷次都没有**——而它被放过了。
DEIXIS_VOL = re.compile(r"(同一卷|该卷|那一卷|同卷)")
DEIXIS_ANY = re.compile(r"(该刊|那份|该篇)")
LOC_VOL = re.compile(r"(第\s*[IVXLC0-9]+\s*卷|卷\s*[0-9]|Bd\.\s*[0-9IVX])")
LOC_ANY = re.compile(r"(第\s*[IVXLC0-9]+\s*卷|卷\s*[0-9]|[0-9]+\s*[–—-]\s*[0-9]+\s*页"
                     r"|第\s*[0-9]+\s*页)")
SENT = re.compile(r"[^。；！？\n]+[。；！？]?")


def scan_text(text: str) -> list:
    out = []
    for m in SENT.finditer(text or ""):
        s = m.group(0)
        for w in NOW_WORDS:
            if w in s and not any(h in s for h in HEDGE):
                out.append({"类": "已故人物谈当下", "触发词": w, "句": s.strip()[:90]})
                break
    dv = DEIXIS_VOL.search(text or "")
    if dv and not LOC_VOL.search(text or ""):
        out.append({"类": "指代悬空", "触发词": dv.group(0),
                    "句": f"说了「{dv.group(0)}」，而整条答案里**没有任何卷次**"})
    elif not dv:
        da = DEIXIS_ANY.search(text or "")
        if da and not LOC_ANY.search(text or ""):
            out.append({"类": "指代悬空", "触发词": da.group(0),
                        "句": f"说了「{da.group(0)}」，而整条答案里没有卷次或页码"})
    return out


def scan(path: pathlib.Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:                                      # noqa: BLE001
        return {"状态": f"读不了，**未核（不是通过）**：{exc}"}
    if isinstance(data, list):
        data = {i.get("case_id", str(n)): (i.get("answer") or i.get("response") or "")
                for n, i in enumerate(data)}
    rows = []
    for cid, txt in sorted(data.items()):
        if not isinstance(txt, str):
            continue
        for hit in scan_text(txt):
            rows.append({"case_id": cid, **hit})
    return {"答案条数": len(data), "**报出**": len(rows), "逐条": rows,
            "★ 本件判不了的": ["「原文写的」后面的断言是否真在引文里（跨语种语义）",
                               "译文是否比原文宽（如「好收成」丢掉 Obst-）"],
            "★ 口径": "**只报不拦**；报的是「这句人物说不出口／这个指代指不到东西」，不判答案对不对。"}


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    import tempfile
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        f = root / "a.json"
        f.write_text(json.dumps({
            "c-now":    "那十件里有一件——1879 年的《Grundlage》——至今未见数字化本。",
            "c-hedged": "那件事至今如何我不知道，**那是我身后的事**。",
            "c-dangle": "图表在同一卷《Vereins-Jahresheft》，曲线是日均值。",
            "c-anchor": "图表在同一卷《Vereins-Jahresheft》，见第 IV 卷第 3 页。",
            # ★ 本件的**来源用例**：只有数据年份、没有卷次 → 必须报
            "c-realmiss": "坐标先给：图表在同一卷《Vereins-Jahresheft》，"
                          "实线是 1862 年、虚线是十五年平均，底子是 1848 bis 1862。",
            "c-clean":  "六月二十九日晚七时，半小时多一点落了五十四毫米。",
        }, ensure_ascii=False), encoding="utf-8")
        r = scan(f)
        by = {x["case_id"]: x["类"] for x in r["逐条"]}

        print("── ★★ 反向对照①：**已故人物说「至今」→ 必须报** ──")
        chk(f"c-now → {by.get('c-now')}", by.get("c-now") == "已故人物谈当下")

        print("── ★★ 反向对照②：**同句已标越界（「那是我身后的事」）→ 不许报** ──")
        chk("c-hedged 不在报出里", "c-hedged" not in by)

        print("── ★★ 反向对照③：**「同一卷」而全篇无卷次页码 → 必须报** ──")
        chk(f"c-dangle → {by.get('c-dangle')}", by.get("c-dangle") == "指代悬空")

        print("── ★★★ 反向对照④：**同样说「同一卷」但给了卷次页码 → 不许报** ──")
        chk("c-anchor 不在报出里", "c-anchor" not in by)

        print("── ★★★ 反向对照⑤：**来源用例——只有年份没有卷次，必须报** ──")
        chk(f"c-realmiss → {by.get('c-realmiss')}", by.get("c-realmiss") == "指代悬空")

        print("── ★★ 反向对照⑥：**干净的答案一条都不报** ──")
        chk("c-clean 不在报出里", "c-clean" not in by)

        print("── ★ 反向对照⑦：读不了 → 说「未核」，不说「通过」 ──")
        chk("未核", "未核" in str(scan(root / "nope.json").get("状态", "")))

        print("── ★ 反向对照⑧：**必须明写自己判不了什么** ──")
        chk("列出两类判不了的", len(r["★ 本件判不了的"]) == 2
            and "跨语种" in r["★ 本件判不了的"][0])
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", help="candidate_answers.json")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.answers:
        ap.error("要么 --self-test，要么给 --answers")
    print(json.dumps(scan(pathlib.Path(a.answers)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
