#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_new_corpus_text_not_committed.py —— **新增的语料正文不许进 git**

## 为什么有这件（2026-08-17）

同一天连撞两件，都是「第三方正文被提交进 **PUBLIC 仓**」：

1. **Livermore 那本 1940 年的书**：`_ledgers/_corpora/livermore-100/` 下 5 个文件、
   375 KB，是《How to Trade in Stocks》(1940, Duell, Sloan & Pearce) 的全文，
   三份里逐字印着 `COPYRIGHT, 1[9]40, BY JESSE L. LIVERMORE / All rights reserved`。
   **而工作区自己的 README 明文写着「版权状态存疑，不宜随仓库分发」。** 已清。
2. **推广扫描**：按 `rights` 分档比对，公开领域那档正文**一份都不在 git**，
   而 `redistribution-not-assumed` / `public-web` 那两档 **811 份 / 4.35 MB 全在**。
   （待裁定 #131，见 `_权利依据未建立的正文在公开仓里-…-2026-08-17.md`）

两件的载体都是**批量提交**：`bfe16379a` 一次动了 **15,070 个文件**，
标题跟 Livermore 一个字都不沾 —— **没有人「决定」把它放进去**。

## 本件守的不变量（有实测支撑，不是我发明的）

    `_corpora/` 下进 git 的 .txt 共 925 份：
       `_*` 标识符清单/构建日志 = **指针**，本该进 git   → 108 份
       `evals/` 下的判分产物                          →   3 份
       其余 = **语料正文**，本该住仓外                  → **814 份 / 4.37 MB**

而那 814 份只落在 **4 个**工作区：godin 588、steinhardt-98 223，
另 3 份是 PD 年代材料（1914 年 Nature 论文、19 世纪 Virchow，在 `_excluded/`/`_rejected/`）。
**其余 40 个工作区 git 里只有 `_ids*.txt`、0 份正文。**
⇒ 这是既有惯例，不是新规矩；那 2 个是例外。

## ★ 只管新增，不管存量

按已裁 **㉜「规则只管新做的」**：本件只看**提交范围内新增的文件**
（默认 `origin/main..HEAD`，与 `check_private_assets_not_public.py` 同口径）。
⇒ 待裁定的那 615 份**不会让它变红** —— 那是 #131，人的决定，不是判据的事。
[[a-red-that-can-never-turn-green-is-not-a-signal]]

## ★★ 为什么判「进不进 git」而不判「权利够不够」

权利够不够要读原书、查续期库、看授权 —— **判据做不到，也不该假装做得到**。
而「语料正文别提交」是一条**机器判得了**、且**已经是惯例**的线。
守住它，权利问题就不会以「已公开分发」的形态出现。

退出码：0＝没有新增的语料正文；1＝有；4＝取不到提交范围（未量）。
"""
import argparse
import pathlib
import re
import subprocess
import sys

# ★★★ 射程按**实测**定，不按「像是语料目录」猜：
#   第一版写 `/_corpora/[^/]+/.*/(raw|sources|corpus|holdout)/` —— **盖不住引发它的那个案例**：
#   Livermore 那 5 份的实际路径是 `_ledgers/_corpora/livermore-100/*.txt`，**连 raw/ 都没有**。
#   再扫一遍又发现 Godin 有 **202 份**博客文直接躺在 `_corpora/wip-godin/` 与 `_holdout/` 下。
#   ⇒ 改成「**`_corpora/` 底下的一切**」，再用两条排除项收窄（下面两个常量）。
#   我为这个射程量了五轮（251→268→719→615→**814**），每放宽一次都多出一批。
#   [[a-gates-scan-set-is-smaller-than-reality]]
CORPUS_DIR = re.compile(r"/_corpora/")
# 排除① `evals/` 下的判分产物（实测 3 份，正当）
NOT_CORPUS = re.compile(r"/evals/")
TEXTY = (".txt", ".md.txt")
# `_ids.txt` / `_ids-delta.txt` / `_ids-round2.txt` …：标识符清单＝指针，本该进 git
MANIFEST = re.compile(r"^_")


def is_corpus_text(path: str) -> bool:
    """→ 这个路径是不是「本该住仓外的语料正文」。纯函数。

    ★ 两个条件都要：在语料目录里 **且** 不是 `_` 开头的标识符清单。
      只判目录会把 104 份指针全报进来；只判文件名会把 skill 里的 .txt 全报进来。
    """
    if not path.endswith(TEXTY):
        return False
    q = "/" + path.lstrip("/")
    if not CORPUS_DIR.search(q) or NOT_CORPUS.search(q):
        return False
    return not MANIFEST.match(path.rsplit("/", 1)[-1])


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    P = "CodexSkills/skill_log_evals/persona-distiller/_corpora"
    chk("★★★ 正例：raw/ 下的语料正文 ⇒ 报",
        is_corpus_text(P + "/wip-x-1/workspaces/x/raw/src-abc/book.txt"))
    chk("★★★ 负例：`_ids.txt` 是标识符清单（指针）⇒ 不报",
        not is_corpus_text(P + "/wip-x-1/workspaces/x/raw/_ids.txt"))
    chk("★★ 负例：`_ids-delta3.txt` 同上 ⇒ 不报",
        not is_corpus_text(P + "/wip-x-1/workspaces/x/raw/_ids-delta3.txt"))
    chk("★ 正例：sources/ 下的 normalized 正文也算",
        is_corpus_text(P + "/wip-x-1/ws/x/references/sources/src-1/a.normalized.txt"))
    chk("★★ 正例：holdout/ 下的更要报",
        is_corpus_text(P + "/wip-x-1/ws/x/holdout/chapter4.txt"))
    chk("★★★ 负例：**不在语料目录**里的 .txt（skill 自己的文档）⇒ 不报",
        not is_corpus_text("CodexSkills/registry/codex/persona-distiller/notes.txt"))
    chk("★★ 负例：语料目录下的**非文本**（json/py）⇒ 不报（本件只管正文）",
        not is_corpus_text(P + "/wip-x-1/ws/x/raw/source-ledger.jsonl")
        and not is_corpus_text(P + "/wip-x-1/ws/x/raw/split.py"))
    chk("★★★ 正例：**直接躺在 `_corpora/<人>/` 下的**（Godin 202 份就是这样）⇒ 报",
        is_corpus_text(P + "/wip-godin/sg_2003_gasp.txt"))
    chk("★★ 正例：`_holdout/` 目录下的（目录带 `_` 但文件不带）⇒ 报",
        is_corpus_text(P + "/wip-godin/_holdout/sg_2009_malcolm_is_wrong.txt"))
    chk("★★★ 负例（实测）：`evals/` 下的判分产物 ⇒ 不报",
        not is_corpus_text(P + "/wip-gantt-156/ws/x/evals/round1/incident_baseline.txt"))
    chk("★★ 正例：**`_ledgers/_corpora/` 那棵同名树**也要盖到（Livermore 那 5 份就在这儿）",
        is_corpus_text("CodexSkills/skill_log_evals/persona-distiller/_ledgers/"
                       "_corpora/livermore-100/raw/jl_1940_book_TRAIN.txt"))
    chk("★ 空串不炸", not is_corpus_text("") and not is_corpus_text("a.txt"))
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--range", default="origin/main..HEAD",
                    help="提交范围（默认 origin/main..HEAD，与 check_private_assets_not_public 同口径）")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    r = subprocess.run(["git", "-c", "core.quotepath=false", "diff", "--name-only",
                        "--diff-filter=A", a.range],      # ★ 只看**新增**（A），改动不算
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("★ **未量，不是通过**（rc=4）—— 取不到提交范围 %r：%s"
              % (a.range, r.stderr.strip()[:160]))
        return 4
    added = [p for p in r.stdout.split("\n") if p.strip()]
    hits = [p for p in added if is_corpus_text(p)]

    print("扫描面：`%s` 范围内**新增**文件 **%d** 个" % (a.range, len(added)))
    print("★ 只管新增（已裁 ㉜「规则只管新做的」）—— 存量那 811 份是 #131，人的决定。")
    if not hits:
        print("\n✓ 新增里没有语料正文")
        return 0
    tot = 0
    print("\n✗ **新增了语料正文 %d 份** —— 本该住仓外：" % len(hits))
    for p in hits:
        sz = pathlib.Path(p).stat().st_size if pathlib.Path(p).is_file() else 0
        tot += sz
        print("     %-72s %9d B" % (p[-72:], sz))
    print("\n   合计 %s 字节。" % f"{tot:,}")
    print("   ★ 处置：把正文放回**仓外**（`_scratch/` 或 `~/Downloads/蒸馏/`），")
    print("     git 里只留 `_ids*.txt` 那样的**标识符清单**（44 个工作区里 40 个就是这么做的）。")
    print("   ★★ 本件**不判权利够不够** —— 那要读原书、查续期库，判据做不到。")
    print("     它只守「语料正文别提交」这条已有惯例；守住它，")
    print("     权利问题就不会以「已公开分发」的形态出现。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
