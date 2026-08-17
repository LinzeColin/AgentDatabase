#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**一份 P1 是「著录方描述这份文献」，而不是文献本身。**

## 三例确凿，跨三个人物（2026-08-05 全库回扫，逐个打开读过）

| 人物 | 文件 | 实况 |
|---|---|---|
| Roberts-Austen #135 | `letter00robe.txt` | 1215 字符，**他的话 157 字符 = 13%**；其余是拍卖著录（`l6s`、`2 pages 8vo.`、信封描述）+ **另一个人（Prestwich）的条目** |
| **Koch #107** | `letter00koch.txt` | 著录说信有 `ca, 240 words`，**而文件里几乎没有信文**（德文 `ich/Sie/Ihnen` 全文 1 处）；内容是手迹扫描的 OCR 噪声 + `SPLENDID AUTOGRAPH LETTER…` 拍卖话术 + **收信人的小传** |
| **Osler #110** | `walt-whitman-1919.txt` | 书目条目 `7660. 'Walt Whitman…' **In preparation in 1919, but not delivered or published.**`——**描述的是一场从没发生过的演讲** |

## 为什么现有的门全都放行

- **归属门**问「文中有没有他的署名」——著录卡里**有**
  （`A.L.S: (W. C, ROBERTS-AUSTEN)`、`KOCH, Robert; M.D`）。
  于是 Roberts-Austen 这一份**过了归属门，而他 22 份真论文没过**。
- `non_placeholder` 只看**字符数 ≥500**——三份都过。
- **没有一道门问「这份文件里有多少是他的话」。**

★ 与 [[related-to-him-is-not-written-by-him]] 不同：那条是「**别人写他的**」（Liebig 9 份）。
这里是「**著录方提到他**」——拍卖行为了卖信而描述它，书目编者为了编目而登记一篇没写成的讲演。

## 判法：只认「描述文献」的话术，不数字数

字数占比难量（要判断哪几句是他的）。**换一个可判的：这份文件在不在描述一件文献。**

标记全部来自那三例的原文，**不是想出来的**：
`A.L.S`／`autograph letter signed`／`ca. N words`／`pages on N leaves`／
`not delivered`／`not published`／`in preparation`／`stamped and postmarked envelope`／
`Inserted:`／`(see no. N)`／`<数字>vo … <数字>s`（开本＋标价）。

★★ **实测分得开**：三例确凿命中 1／3／4 次；
而三个反例（Barton 本人日记、Blackwell 本人演讲提纲、Roberts-Austen 那篇带卷前杂项的论文）
**命中 0 次**。

★★★ 这个判据是**从三例里长出来的，再拿反例验**——
先前那版粗代理（数字 + `8vo` + `£`）**假阳率 1/3**，
六个候选里两个是真一手（LOC 众包日记、她本人的演讲提纲）。
**代理不等于判据；报之前必须逐个打开读。**

## 只报不拦

改分档是人的判断：`letter00robe` 那两句**确实是他的话**，
改判 S1 之后 Roberts-Austen 一手占比 26/27 → 25/27 = 0.9259，**仍远高于 standard 门 0.50**。
**所以这不是「为了过门」的调整，是记账要对**——而怎么记由人定。
"""

import argparse
import json
import pathlib
import re
import sys

#: ★ 剥掉抓源方写的出处表头再量——**表头是出处说明，不是他的话**。
#:   全库只有 Adams（144 份）与 Coffin（36 份）有这种表头，
#:   实测占全文**聚合 17.2% / 11.7%**，**逐份中位 39.1% / 16.1%**。
#: ★★ 接上之后**逐个量过前后差**，只写量到的：
#:   · `check_lane_quotes_verbatim` @ Coffin：核过 1 → 0，
#:     报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
#:     那句「逐字引文」只存在于**我自己写的表头里**。这是 Barton 事故的引文版，实锤一条。
#:   · ★★★★ `check_ocr_language_death` @ Coffin：不剥时「**每一份都在下限之上**」，
#:     剥掉表头后报出 **2 份虚词占比 0.101（下限 0.15）**——
#:     **我那段干净的英文表头把 OCR 烂掉的文件托过了及格线。**
#:     同一件在 Adams 上是「可判份数 94 → 60」：34 份**只因表头的词数才够得上判**。
#:   · `check_first_person_density`：正文字符 −0.6%，密度 1.68 → **1.69**——
#:     **几乎没变**。我一度在这里写「第一人称密度被表头拉偏」，**那句没有实测支撑，已删**。
#:   · 其余多数判据前后一致。**接线是按「表头不是他的话」这条原则做的，不是因为每个都变了。**
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

# ★ 全部取自三例原文
MARKERS = (
    # ★★★ **必须带句点。** 第一版写 `\bA\.?\s?L\.?\s?S\b` + `re.I`，
    #   它匹配德语最常用词之一 **`als`**——于是德语语料全线飘红：
    #   Koch 44/55、Liebig 28、Martens 16、Mendel 9、Semmelweis 7，全库 132 份。
    #   **我差一点把这 132 报成「著录卡」。**
    #   （真例里 Roberts-Austen 写的是 `A.L..S:`，带点；Koch 那份走的是
    #     `autograph letter signed` 那条拼全的，所以要点不丢命中。）
    r"\bA\.\s?L\.{1,2}\s?S\b",     # A.L.S / A.L..S（OCR 重点），但不匹配德语 `als`
    r"autograph letter signed",
    r"\bca\.?,?\s*\d+\s*words\b",
    r"pages? on \w+ leaves",
    # ★★★ `not delivered` 与 `in preparation` **也删了**——它们是普通英文：
    #   Nightingale 那句是她自己的正文「an important letter or message **not delivered**」；
    #   Barton 那份命中的是**信封回执戳**
    #   「IF NOT DELIVERED IN FIVE DAYS, RETURN TO AMERICAN NATIONAL RED CROSS」。
    #   Osler 的书目条目不靠它们也够：`Inserted:` + `(see no. 4611)` 两个。
    #   **删这两条之后，全库 8 → 3，正好是那三例确凿。**
    r"stamped and postmarked envelope",
    # ★★ 「开本＋标价」这条**删掉了**：它命中的是**书末装订的出版社广告页**
    #   （Nightingale `8vo., Price 38s` 四份、Koch `8vo, 5s`、Pasteur `8vo. 28s`），
    #   十九世纪的书后面普遍装订这种广告。**而三例确凿没有一例靠它命中**——
    #   Roberts-Austen 走 `A.L..S` + 信封描述，Koch 走拼全的话术，Osler 走 `Inserted:`。
    #   **对真例零贡献、对假阳贡献最大的标记，直接删。**
    r"\bInserted:",
    r"\(see no\.\s*\d+\)",
)
_RX = re.compile("|".join(MARKERS), re.I)


def scan(text):
    """→ 命中的著录话术（去重、保序）。"""
    out, seen = [], set()
    for m in _RX.finditer(str(text)):
        s = m.group(0).strip()
        k = s.lower()
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def check(rows, read_text):
    """`rows` 是台账记录；`read_text(row)` 返回正文（取不到返回 None）。"""
    hits = {}
    unread = []
    for r in rows:
        if not str(r.get("tier") or "").startswith("P1"):
            continue
        t = read_text(r)
        if t is None:
            unread.append(r.get("source_id"))
            continue
        m = scan(t)
        # ★★★ **要 ≥2 个不同标记。** 单个标记假阳太多，实测：
        #   `in preparation` 会命中正常散文（「另一篇论文 in preparation」）；
        #   `8vo. 5s` 会命中**书末装订的出版社广告页**（Nightingale `Price 38s`、Osler `each 5s`）。
        #   三例确凿各带 2–4 个标记，而这些假阳只有 1 个。
        if len(m) >= 2:
            hits[r.get("source_id")] = {
                "文件": str(r.get("original_name") or r.get("title") or ""),
                "字符数": len(t),
                "著录话术": m[:6],
            }
    return {
        "P1 份数": (_p1 := sum(1 for r in rows if str(r.get("tier") or "").startswith("P1"))),
        "**疑似著录卡**": hits,
        "读不到正文的": unread,          # ★ 读不到就说读不到，不当成「没问题」
        "计数": f"{len(hits)} 份 P1 像是「著录方描述这份文献」而不是文献本身",
        "★ 口径": "**只报不拦。** 改分档是人的判断——里头引的那几句确实是他的话。",
        # ★★★ 2026-08-17 第二轮：**零扫描面不许给 true**。
        #   P1 份数 0 时「没有著录卡」恒真 ⇒ 本件对着「一份也没看」印
        #   `"通过": true`，而这是**机器可读字段**，下游读的就是它。
        #   照仓里先例（`check_persona_frame_break` 对「不适用」置 None）办；
        #   **不翻成 false**（那是收紧判定，属决定不属清理）。
        #   [[zero-hit-gates-must-prove-they-can-hit]]
        "通过": (None if not _p1 else True),
        **({} if _p1 else {"★ 未核（不是通过）":
                           "P1 份数 0 —— 本件一份也没看过；`通过` 置 null "
                           "表示**既不算通过也不算失败**。"}),
    }


def self_test():
    bad = []

    def chk(label, ok):
        print(("  ✓ " if ok else "  ✗ ") + label)
        if not ok:
            bad.append(label)

    print("── 正例：三份真实的著录卡（原文片段） ──")
    pos = {
        "Roberts-Austen": "A.L..S: OW. C, ROBERTS-AUSTEN), Royal Mint, April 12. 98, "
                          "2 pages 8vo., with stamped and postmarked envelope, l6s",
        "Koch": "Autograph letter signed, two pages on two leaves, ca, 240 words, "
                "addressed to Professor Jakob Wasserman",
        "Osler": "7660. 'Walt Whitman. An anniversary address with personal reminiscences.' "
                 "In preparation in 1919, but not delivered or published. "
                 "Inserted: photo. of Maurice Bucke (see no. 4611).",
    }
    for who, t in pos.items():
        chk(f"{who} 认出来了：{scan(t)[:2]}", bool(scan(t)))

    print("\n── ★★★ 反例：三份**真一手**，一条都不许报 ──")
    #   这三份是先前那版粗代理的假阳（假阳率 1/3），**必须留在自测里**。
    neg = {
        "Barton 本人日记（LOC 众包转录）":
            "# URL: https://tile.loc.gov/storage-services/service/gdc/gdccrowd/mss/"
            "mss11973/002/1000/002_1008_1109.txt",
        "Blackwell 本人演讲提纲":
            "Note for speech: \"English Charities\" notes of speech on English charities "
            "1 184 Charities - all begging funds 50 religious 33 educational 17 medical",
        "Roberts-Austen 论文（扫本带卷前杂项）":
            "Jlie Gold^ Aluminium Series of Alloys. 367 Yarkand Mission, Second. "
            "Scientific Results. Introductory Note and Map. 4to. London 1891",
    }
    for who, t in neg.items():
        chk(f"{who}：没报（{len(scan(t))} 处）", not scan(t))

    print("\n── ★★ 反向对照：读不到正文时，**报「读不到」不报「通过」** ──")
    r = check([{"tier": "P1", "source_id": "src-x"}], lambda _r: None)
    chk(f"记进读不到：{r['读不到正文的']}", r["读不到正文的"] == ["src-x"])
    chk("没有把它算成疑似", not r["**疑似著录卡**"])

    print("\n── ★ 反向对照：非 P1 一律不看 ──")
    r = check([{"tier": "S1", "source_id": "src-y"}],
              lambda _r: "Autograph letter signed, ca, 240 words")
    chk(f"S1 不报：{r['计数']}", not r["**疑似著录卡**"])

    if bad:
        print("\n未过：")
        for b in bad:
            print("  · " + b)
        return 2
    print("\n✓ 自测全过（3 正 + 3 真一手反例 + 2 反向对照）")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?", help="含 evidence/source-ledger.jsonl 的人物目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要么 --self-test，要么给工作区")
    ws = pathlib.Path(a.workspace)
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        print(f"✗ 没有 {led}——**未核验（不是通过）**", file=sys.stderr)
        return 2
    rows = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()]

    def read_text(r):
        p = ws / str(r.get("normalized_path") or r.get("local_path") or "")
        if not p.is_file():
            return None
        try:
            return corpus_body(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:                                        # noqa: BLE001
            return None

    print(json.dumps(check(rows, read_text), ensure_ascii=False, indent=2))
    return 0            # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
