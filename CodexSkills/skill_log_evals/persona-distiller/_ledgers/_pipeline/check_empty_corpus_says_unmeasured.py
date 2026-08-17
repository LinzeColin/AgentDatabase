#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_empty_corpus_says_unmeasured.py —— **语料为空时，每一栏都必须说「未核」**

## 为什么建它：静态扫描抓不到的那一种

2026-08-18 一天里修了 6 处同形状缺陷（「判据说未核、记录写成一个干净的 0」）。
**前 5 处静态扫描能标出来，第 6 处标不出来** —— 它的措辞、默认值都不沾：

    if not _me:  review[...] = '⚠ **未核，不是通过**'
    if _me:      ...
    else:        review[...] = '✓ 台账与工作区一致（**该人物在判据明细里**…）'
                 # ↑ 这个 else 配的是 `if _me:`，把上面那句未核覆盖了，
                 #   而 ✓ 的正文在这条分支上是**假的**

抓到它的是**端到端负对照**：拿一个 `raw/` 为空的真实工作区跑
`quality_check --phase research`，`content_review` 六栏里唯一印 ✓ 的就是它。
**一条命令过完全部消费点。** 本件把那条命令固化下来。
[[empty-default-swallows-unknown]]｜[[zero-hit-gates-must-prove-they-can-hit]]

## 判什么

语料一份没有时，`content_review` 的每一栏若**读起来像一个测量结果**
（含「0 条 / 0 处 / 0 个」或以 ✓ 开头），就**必须同时带未核标记**。
否则它是在用一个干净的数冒充「查过了，没问题」。

★ 判定不点名具体栏位 —— **新加的栏自动被覆盖**，不需要回来改名单。

## ★★★ 本件自己的两个坑（都踩过，写在这里免得再踩）

1. **试验台不许喂饱自己的断言。** 跑之前必须**清空副本里的 `reports/`**，
   否则读回来的可能是随工作区一起拷过来的**旧报告**（`cp -R` 会把
   mtime 一起改成拷贝时刻，**按 mtime 挑最新是分不出来的**）。
   [[the-harness-copied-the-artifact-then-read-the-copy-back]]
2. **目录名必须与 meta slug 一致**，否则 target 校验直接拒检（rc=1，
   `Target directory name must match meta slug`），而拒检**不是通过**。

退出码：0＝每栏都诚实；1＝有栏用干净读数冒充通过；4＝未量（没有合适的工作区／跑不起来）。
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
QUALITY = HERE.parents[3] / "registry/codex/persona-distiller/scripts/quality_check.py"

#: 「读起来像一个测量结果」的形状
MEASUREMENT = re.compile(r"(?<!\d)0\s*(条|处|个|份)|^\s*✓")
#: 未核标记 —— 这一族的任一出现都算「它承认自己没量」
UNMEASURED = ("未核", "未检查", "未量", "不适用", "无从比", "没读到", "0 份 ——")


def is_dishonest(text: str) -> bool:
    """→ True 表示：像个测量结果，却没有承认自己没量过。**纯函数。**"""
    s = str(text)
    if any(u in s for u in UNMEASURED):
        return False
    return bool(MEASUREMENT.search(s))


def pick_target(corpora: pathlib.Path):
    """→ (target, wip 根) 或 (None, 原因)。挑一个**结构完整而语料为空**的工作区。"""
    for meta in sorted(corpora.rglob("meta.json")):
        t = meta.parent
        if not (t / "SKILL.md").is_file():
            continue                                   # 不是完整 target，跑了会被拒检
        raw = t / "raw"
        if raw.is_dir() and any(p for p in raw.rglob("*.txt")
                                if not p.name.startswith("_")):
            continue                                   # 有语料，不是本件要的条件
        # 往上找到 wip-* 那一层，连着拷才有生产布局
        for anc in [t, *t.parents]:
            if anc.name.startswith("wip-"):
                return t, anc
        return t, t
    return None, "没有找到「结构完整（有 SKILL.md）且 raw/ 为空」的工作区"


def run_once(target: pathlib.Path, wip: pathlib.Path):
    """拷贝 → 清空 reports/ → 跑 quality_check → 读回新报告。→ (content_review, 说明)"""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="emptycorpus-"))
    dst_wip = tmp / wip.name                            # ★ 名字必须原样，否则拒检
    shutil.copytree(wip, dst_wip, symlinks=True)
    rel = target.relative_to(wip)
    dst = dst_wip / rel if str(rel) != "." else dst_wip
    reports = dst / "reports"
    # ★★★ 先清空，否则读回来的可能是拷过来的旧报告（mtime 已被 cp 改写，分不出）
    stale = sorted(reports.glob("quality-research-*.json")) if reports.is_dir() else []
    for p in stale:
        p.unlink()
    r = subprocess.run([sys.executable, str(QUALITY), str(dst),
                        "--phase", "research", "--write-report"],
                       capture_output=True, text=True)
    fresh = sorted(reports.glob("quality-research-*.json")) if reports.is_dir() else []
    if not fresh:
        return None, ("跑完没有生成报告（rc=%d）：%s"
                      % (r.returncode, (r.stdout or r.stderr)[:160]))
    d = json.loads(fresh[-1].read_text(encoding="utf-8"))
    if d.get("refused"):
        return None, "quality_check **拒检**（checks_run=0）——拒检不是通过"
    cr = (d.get("metrics") or {}).get("content_review") or {}
    return cr, "清掉旧报告 %d 份，新生成 %d 份" % (len(stale), len(fresh))


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    chk("★★★ 负例（**本件的整个理由**）：第六处那句 ✓ 必须被判不诚实",
        is_dishonest("✓ 台账与工作区一致（该人物在判据明细里，**没进工作区 0 份**）"))
    chk("★★★ 负例：第一处那句「0 条」必须被判不诚实",
        is_dishonest("头部引文 0 条，**正文里找不到 0 条**"))
    chk("★★ 正例：改后的第一处（带未核）不算",
        not is_dishonest("**未核（不是通过）**：判据没有给出计数（没有找到任何 .txt）"))
    chk("★★ 正例：改后的第六处（带未核）不算",
        not is_dishonest("⚠ **未核，不是通过** —— 明细里没有 `wip-adams-131`"))
    chk("★ 正例：真读数不含 0 的不报（本件只管**冒充通过**的那种）",
        not is_dishonest("核过 7 条，指错 2 条"))
    chk("★★ 正例：真读数 0 指错但**语料确实读到了** —— 本件会误报，"
        "所以只在语料为空时跑（射程写进 main）",
        is_dishonest("核过 7 条，指错 0 条"))
    chk("★ 「德文语料 0 份 —— 未核」这种自带说明的不算",
        not is_dishonest("⚠ **德文语料 0 份 —— 未核，不是通过**（在空集上恒真）"))
    chk("★ 空输入不炸", not is_dishonest("") and not is_dishonest(None))
    chk("★★ `quality_check.py` 真的在（不在则 main 判 rc=4，不判绿）", QUALITY.is_file())
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora", type=pathlib.Path,
                    default=HERE.parents[1] / "_corpora")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    if not QUALITY.is_file():
        print("★ **未量，不是通过**（rc=4）—— 读不到 %s" % QUALITY)
        return 4
    if not a.corpora.is_dir():
        print("★ **未量，不是通过**（rc=4）—— 语料根不在：%s" % a.corpora)
        return 4

    target, wip = pick_target(a.corpora)
    if target is None:
        print("★ **未量，不是通过**（rc=4）—— %s" % wip)
        return 4
    print("被测工作区：%s" % target)
    print("  （条件：结构完整、`raw/` 一份 .txt 都没有 —— 这是本仓的常态，"
          "「语料只放指针、不进 git」）")

    cr, note = run_once(target, wip)
    if cr is None:
        print("★ **未量，不是通过**（rc=4）—— %s" % note)
        return 4
    print("  %s｜`content_review` **%d** 栏\n" % (note, len(cr)))

    offenders = []
    for k, v in cr.items():
        dis = is_dishonest(v)
        print("   %-28s %s  %s" % (k[:28], "**✗ 冒充通过**" if dis else "诚实",
                                   str(v)[:52].replace("\n", " ")))
        if dis:
            offenders.append((k, str(v)[:120]))

    if not offenders:
        print("\n✓ 语料为空时，没有任何一栏用干净读数冒充「查过了」")
        return 0
    print("\n✗ **用干净读数冒充通过的 %d 栏**：" % len(offenders))
    for k, v in offenders:
        print("     · %s → %s" % (k, v))
    print("\n  ★ 处置：让那一栏说「未核（不是通过）」。**不要把它删掉了事** ——")
    print("    删掉之后读的人只会以为这一项从来不存在。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
