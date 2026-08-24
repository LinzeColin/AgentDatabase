#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**抓到了、记进台账了、却没进工作区**——而所有既有的门都说「齐的」。

## 为什么现有的门看不见它

`check_corpus_presence` 比的是**工作区自己的**账本（`evidence/source-ledger.jsonl`）
与磁盘上的文件。**一份来源如果压根没被 `ingest`，那它在账本里也没有**——
于是账本 89 条、磁盘 89 份，**完全一致**，它报绿。

**一致，但不完整。** 缺的那一层在上游：抓源阶段的九列台账
（`_corpora/wip-<人>/raw/_ids.txt`），它记的是**抓到了什么**；
工作区记的是**用上了什么**。**没有任何判据比过这两个。**

## 实测（2026-08-04，全量 11 个工作区）

```
台账有、工作区没有：合计 **18** 份
★★ **2026-08-05 补**：本件按制表符切 `_ids.txt` 且要求 >6 列，
而 26 个工作区里 **5 个用的是竖线分隔的老格式**（koch／lister／pasteur／semmelweis／jenner）——
**它们一列都切不出来，分档全是 `?`，此前被静默算进「不是一手」。**
现已单列一项「分档未知」。**「不知道」不是「否」。**

其中带一手分档（P1/P2）的两个人：
  Barton   #117  6 份缺，**4 份是 P1**  ← 她本人的日记 1864／1867／1871／1897（timeline 道）
  Blackwell #118 6 份缺，**6 份全是 P1** ← 日记 1836／1872-74／1900-02／1903-05
                                          + `sp-1237-anatomy` 手稿
                                          + `sp-1251-the-position-of-women` 报刊撰文
```

**Blackwell 那两份的台账注里就写着「只此一处的手稿，出版著作里没有」
与「报刊撰文，只此一处」。**

★ 必须与「**故意不要**」分开：Barton 那 6 份里有 **2 份**（两本信件簿）
写在 `_EXCLUDED.txt` 里，是**有意排除**，不算缺口。
本件因此**先读 `_EXCLUDED.txt`，被点名的一律不报**。
（Blackwell 的 `_EXCLUDED.txt` 是空的，所以她那 6 份一份都不是有意排除。）

## 这不推翻谁的判分

Barton 三轮用尽记拒发、Blackwell 卡在裁定 ⑤——**产物是按当时工作区里的语料判的，
判分本身没有问题**。本件说的是另一件事：
**「语料充足、全流程走完」这句话，对这两人不成立**——
他们的成品建在一个比台账小的语料上，而没有任何地方记着这一点。

## 判据形状：只比名字，不比内容

台账第 1 列的短名 vs 工作区 `raw/` 下所有 `.txt` 的文件名（去扩展名）。
**不比 sha256**——`ingest` 会做归一化，字节本就不同，比内容会得到一堆假阳。
"""
import argparse
import json
import pathlib
import re
import sys

# ★★★ 2026-08-05 重大更正：**必须把 `references/holdout/` 也算作「进了工作区」。**
#
#   本件原来只看 `raw/`，于是把**按设计隔离出来的 holdout 材料**报成「没进工作区」。
#   2026-08-05 我据此得出「Barton 缺 4 本日记、Blackwell 缺 4 本日记＋2 份手稿、
#   合计 14.6 万词一手材料被静默丢弃」，写成待裁定 ⑯，**并把它当成重大发现报给了用户**。
#
#   **全错。** 那 10 份一份不少地躺在 `references/holdout/` 里：
#   Barton 的 holdout 目录正好 4 个、对上她那 4 本；Blackwell 8 个里有这 6 个。
#   **holdout 本来就必须不在 `raw/`——建模的人不许读它，那是判分用的。**
#   **一份被正确隔离的材料，被我报成了「丢失的证据」。**
#
#   ★ 教训不是「多写一个目录」，是：**本件比的是「抓到的」与「建模能看到的」，
#     而「建模能看到的」≠「工作区全部内容」。** holdout 是工作区的一部分，
#     只是**故意不给建模的人看**——它不在 raw/ 正是它在正常工作。
WS_PATTERNS = ("workspaces/*/raw", "workspaces/*/*/raw", "ws-*/*/raw", "eval/raw")
# holdout：**已落地但按设计隔离**，不算缺口
HOLDOUT_PATTERNS = ("workspaces/*/references/holdout", "workspaces/*/*/references/holdout",
                    "references/holdout")
_TIER_RE = re.compile(r"^(P[123]|S[12]|U)$")   # 与 check_corpus_ceiling 同口径
META = {"_ids", "_EXCLUDED"}


def staged_names(person: pathlib.Path) -> set:
    d = person / "raw"
    return ({p.stem for p in d.rglob("*.txt")} - META) if d.is_dir() else set()


def ingested_names(person: pathlib.Path) -> set:
    """已落地的短名。**`raw/` 与 `references/holdout/` 都算**。

    ★ holdout 不在 `raw/` 是**它在正常工作**，不是缺口——建模的人不许读它。
      本件曾因为漏了这一句，把 Barton 4 本、Blackwell 6 份**正确隔离**的日记与手稿
      报成「静默丢失的一手材料」。
    """
    out = set()
    for pat in WS_PATTERNS + HOLDOUT_PATTERNS:
        for d in person.glob(pat):
            # `.normalized.txt` 的 stem 是 `xxx.normalized`，要再去一层
            for f in d.rglob("*.txt"):
                out.add(f.stem)
                if f.stem.endswith(".normalized"):
                    out.add(f.stem[: -len(".normalized")])
    return out


def excluded_blob(person: pathlib.Path) -> str:
    f = person / "raw" / "_EXCLUDED.txt"
    return f.read_text(encoding="utf-8", errors="ignore") if f.is_file() else ""


def tiers_of(person: pathlib.Path, names: set) -> dict:
    ids = person / "raw" / "_ids.txt"
    out = {}
    if not ids.is_file():
        return out
    for line in ids.read_text(encoding="utf-8", errors="ignore").splitlines():
        c = line.split("\t")
        # ★★ 2026-08-05：**不许按固定列位取分档。**
        #   全库 14 份 `_ids.txt` 有四种格式，其中 **virchow 是 8 列、少了 `locator` 那一列**：
        #     现行 9 列  [0]short [1]url [2]title [3]year [4]locator [5]lang [6]tier [7]mark [8]note
        #     virchow 8  [0]short [1]url [2]title [3]year [4]**lang** [5]**tier** [6]- [7]-
        #   照 `c[6]` 取，virchow 拿到的是 `-`，不是 `P1`。
        #   `check_corpus_ceiling` 早就不按列位取了（它在所有列里找匹配分档正则的那一个），
        #   **同一个仓里两种做法，一个稳一个脆**——这里改成和它一样。
        if len(c) > 2 and c[0] in names:
            tier = next((x.strip() for x in c if _TIER_RE.match(x.strip())), None)
            if tier:
                out[c[0]] = tier
    return out


def audit(corpora: pathlib.Path) -> dict:
    rows, skipped = [], []
    for person in sorted(p for p in corpora.iterdir() if p.is_dir()):
        staged, ingested = staged_names(person), ingested_names(person)
        if not staged or not ingested:
            # ★★ 「没比」有三种，**后果完全不同，不许混成一句「未核」**：
            #   ① 扁平布局：只有一个 `raw/`，抓源与工作区共用同一个目录——
            #      **本件要问的那个差结构上不存在**，且 `check_corpus_presence`
            #      已经在比「账本 vs 磁盘」，是**被别的判据覆盖了**，不是漏洞。
            #   ② 没有外层 `raw/`：这人**没走过抓源台账那一步**，本件无从比。
            #   ③ **清单里有、而一份都没灌进工作区**（`ingested` 为空）：
            #      这人抓源被挡住了（如 Benardos #128：清单 21 份、灌 0 份，
            #      通道受限记延后）。**那不是缺口，是「一份都没抓到」这个事实本身。**
            #      ★★ 2026-08-10 之前这一档落进「说不清」，全库唯一的一条就是它。
            #      ★ 我第一版写成「外层 raw/ 只有标记文件」——**那是我 `ls raw/` 看到
            #        2 个文件就断的，而清单在 `_ids.txt` 文件里，不在目录里**，
            #        `staged_names` 实际给出 21 个真名。**读错了前提，改了两次。**
            #   ④ 其它：真的说不清，那才是缺口。
            has_ws = bool(list(person.glob("workspaces/*")) + list(person.glob("ws-*")))
            if staged and not has_ws:
                kind = "扁平布局（抓源与工作区共用 raw/）——本件的差结构上不存在，归 check_corpus_presence 管"
            elif not staged:
                kind = "没有外层 raw/：**没走过抓源台账那一步**，无从比"
            elif staged and not ingested:
                kind = (f"抓源清单里 {len(staged)} 份，**一份都没灌进工作区**"
                        f"（灌 0 份）：抓源被挡住了，**不是缺口**")
            else:
                kind = "**说不清**"
            skipped.append(f"{person.name}：{kind}")
            continue
        blob = excluded_blob(person)
        gap = sorted(n for n in staged - ingested if n not in blob)
        deliberate = sorted(n for n in staged - ingested if n in blob)
        if not gap:
            continue
        t = tiers_of(person, set(gap))
        rows.append({"人物": person.name, "台账": len(staged), "工作区": len(ingested),
                     "**没进工作区**": len(gap),
                     "其中一手": sum(1 for v in t.values() if v in ("P1", "P2")),
                     # ★★ 2026-08-05：**分档解析不出来的，不许算成「不是一手」。**
                     #   `staged_names` 按制表符切、要求 >6 列；而 26 个工作区里有
                     #   **5 个的 `_ids.txt` 是竖线分隔的老格式**（koch/lister/pasteur/
                     #   semmelweis/jenner），它们一列都切不出来，分档全是 `?`。
                     #   于是那 6 条缺口被静默计成「不是一手」——
                     #   **「不知道」被当成了「否」，而这两件事后果完全不同。**
                     #   ★ 第一版我写成「t.values() 里不是 P1/P2/S1/P3 的」——**那是错的**：
                     #     切不出来时 `tiers_of` 返回的是**空 dict**，`values()` 一个都没有，
                     #     于是「未知」恒为 0，我自己的反向对照当场把它照出来了。
                     #     正确的数法是「缺口里**压根没进分档表**的那些」。
                     "★ 分档未知（**不是「不是一手」**）":
                         sum(1 for name in gap if name not in t),
                     "有意排除（不计）": len(deliberate),
                     "清单": [f"{n}[{t.get(n, '?')}]" for n in gap]})
    return {"扫了": len([p for p in corpora.iterdir() if p.is_dir()]),
            "**有缺口的人物**": len(rows),
            "缺口合计": sum(r["**没进工作区**"] for r in rows),
            "**其中一手合计**": sum(r["其中一手"] for r in rows),
            "★★ 分档未知合计（**未核，不是「不是一手」**）":
                sum(r.get("★ 分档未知（**不是「不是一手」**）", 0) for r in rows),
            "明细": rows,
            "★ 两侧不齐备、没比的": skipped,
            "★ 其中「说不清」的": [s for s in skipped if "说不清" in s],
            "★ 口径": "只比文件名，不比 sha256——ingest 会归一化，比内容会得到一堆假阳"}


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)

        def mk(name, staged, ingested, excluded="", ids=None):
            p = root / name
            (p / "raw").mkdir(parents=True)
            for s in staged:
                (p / "raw" / s).mkdir()
                (p / "raw" / s / f"{s}.txt").write_text("x", encoding="utf-8")
            w = p / "workspaces" / "who" / "raw"
            w.mkdir(parents=True)
            for s in ingested:
                (w / f"src-{s}").mkdir()
                (w / f"src-{s}" / f"{s}.txt").write_text("x", encoding="utf-8")
            if excluded:
                (p / "raw" / "_EXCLUDED.txt").write_text(excluded, encoding="utf-8")
            if ids:
                (p / "raw" / "_ids.txt").write_text(ids, encoding="utf-8")

        mk("wip-gap", ["a", "b", "c"], ["a"],
           ids="a\t\t\t\t\t\tP1\t\t\nb\t\t\t\t\t\tP1\t\t\nc\t\t\t\t\t\tS1\t\t\n")
        mk("wip-clean", ["a", "b"], ["a", "b"])
        mk("wip-deliberate", ["a", "b"], ["a"], excluded="b 这份是有意不要的\n")
        mk("wip-empty", [], [])
        r = audit(root)
        print("── 正向：有缺口的报出来 ──")
        chk(f"有缺口的人物 {r['**有缺口的人物**']} 应为 1", r["**有缺口的人物**"] == 1)
        chk(f"缺口合计 {r['缺口合计']} 应为 2（b、c）", r["缺口合计"] == 2)
        chk(f"其中一手 {r['**其中一手合计**']} 应为 1（只有 b 是 P1）",
            r["**其中一手合计**"] == 1)
        print("── ★★★ 反向对照①·补：**竖线老格式切不出分档 → 记「未知」，不许算成「不是一手」** ──")
        mk("wip-pipe", ["a", "b"], ["a"],
           ids="a|writings|1900|t|u|v\nb|writings|1900|t|u|v\n")
        r2 = audit(root)
        pipe = [x for x in r2["明细"] if x["人物"] == "wip-pipe"]
        chk(f"wip-pipe 被报成有缺口（1 条）", len(pipe) == 1 and pipe[0]["**没进工作区**"] == 1)
        chk(f"它的「其中一手」= {pipe[0]['其中一手'] if pipe else '?'}（切不出分档，不该有一手）",
            bool(pipe) and pipe[0]["其中一手"] == 0)
        k = "★ 分档未知（**不是「不是一手」**）"
        chk(f"而它的「{k}」= {pipe[0].get(k) if pipe else '?'} **必须 >0**"
            f"——否则「不知道」又被吞成「否」",
            bool(pipe) and (pipe[0].get(k) or 0) > 0)

        print("── ★★ 反向对照①：齐的**不报** ──")
        chk("wip-clean 不在明细里", all(x["人物"] != "wip-clean" for x in r["明细"]))
        print("── ★★ 反向对照②：**写在 _EXCLUDED 里的是有意排除，不许报成缺口** ──")
        chk("wip-deliberate 不在明细里", all(x["人物"] != "wip-deliberate" for x in r["明细"]))
        print("── ★★ 反向对照③：两侧不齐备的**说出来**，不静默跳过 ──")
        chk(f"{r['★ 两侧不齐备、没比的']}", any("wip-empty" in s for s in r["★ 两侧不齐备、没比的"]))
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpora", nargs="?", help="`_corpora` 目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.corpora:
        ap.error("要么 --self-test，要么给 _corpora 目录")
    info = audit(pathlib.Path(a.corpora))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 1 if info["**有缺口的人物**"] else 0


if __name__ == "__main__":
    sys.exit(main())
