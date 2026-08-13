#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_start_here_numbers.py —— **接手人第一眼那张表，数字对不对**

## 为什么有这件

`START-HERE.md` 是移交的入口，第一屏就是一张「现在做到哪了」的表，
表头写着「**数字由脚本现算**」。2026-08-13 逐个核过去：**六行里五行是错的。**

| 行 | 表里写的 | 实测 | 错在哪 |
|---|---:|---:|---|
| 已入库人物档案 | **71** | **102** | ★ 数了 `registry/codex/` 下的**技能目录**，根本不是人物 |
| 在制工作区 | 49 | 51 | 陈旧 |
| 语料 | 2,064 | 见下 | 口径含糊：`raw/` 与 `references/sources/` 两处布局，且 `.txt` 埋在再下一层 |
| 断言 | 601 | 976 | 陈旧 |
| 盲判用例 | 676 | 982 | 陈旧；且 676 那个数其实是别处的（语料份数） |
| 记延后/拒发 | 160 | 168 | 陈旧 |

**没有任何东西生成或校验过它。** 「由脚本现算」是句愿望，不是事实——
算过一次、手抄进去，此后一路漂。[[gates-cover-json-not-the-prose-users-read]]

★ 我数语料时**当场又踩了三次口径坑**，逐条记下来当反例：

1. `glob("references/sources/*")` 报 **0 份** —— 正文埋在 `sources/<src-id>/`
   **再下一层**，一层 glob 只看见目录。[[a-gates-scan-set-is-smaller-than-reality]]
2. `find -path "*/workspaces/*/raw/*.txt"` 报 **2856**，而 python 的
   `wip-*/workspaces/*/raw/*.txt` 报 **1124** —— `find` 的 `*` 跨斜杠，
   把别的布局层数也吃了进来。**同一个问题，两把尺子，两个数。**
3. 磁盘上有的 ≠ 收件人拿得到的：`raw/*.txt` 被 `.gitignore` 挡着，
   **而更早提交进去的那批仍然是跟踪状态**（gitignore 不会取消跟踪）。

⇒ **定版口径：一律以 `git ls-files` 为准**——「收件人 clone 之后真正拿到的东西」。
  它在任何机器上都一样，不受我这台机器的残留影响
  （[[stale-artifacts-from-my-machine-leak-into-the-build]]）。

## 判什么

逐行**现算**，与 `START-HERE.md` 表里那一格比对：不一致 ⇒ ✗ 红（rc=1）。
`--apply` 把那一格改成实测值。

★★ 比的是**整格文本**，不是只比那个数。第一版只比粗体里的数，
   而语料那格后面还挂着「＝ `raw/` 1,140 ＋ `references/sources/` 924」——
   把 2,064 改成 6,453 而分项还是旧的，**比原来更糟**：
   一格之内自相矛盾，读的人无从判断信哪个。
   ⇒ **整格由本件拥有**（含单位与分项），散文与数字不可能再分家。

★ 每行的口径**印在输出里**，因为「2,064 份语料」离开口径就没有意义
   （[[counts-need-their-cutoff-stated]]）。

## 用法

    python3 check_start_here_numbers.py            # 只查
    python3 check_start_here_numbers.py --apply    # 查 + 改表
    python3 check_start_here_numbers.py --self-test

退出码：0＝表与实测一致；1＝不一致；4＝找不到 START-HERE.md 或不在 git 树里（**未判**）
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent                      # …/persona-distiller
def _root():
    """仓根：**用 git 问，不用 parents[N] 数层数**（数错过，见踩坑库）。"""
    r = subprocess.run(["git", "-C", str(PD), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return pathlib.Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else PD.parents[2]


ROOT = _root()                               # 仓根
START = ROOT / "START-HERE.md"
GROUP = ROOT / "CodexSkills/registry/codex/persona-distiller-group"
DEFER = PD / "_ledgers/_延后名单.json"
REL = "CodexSkills/skill_log_evals/persona-distiller/_corpora"


def tracked():
    """→ `_corpora/` 下**被 git 跟踪**的全部路径。这是「clone 之后拿得到的」。

    ★★ 必须用 `-z`（NUL 分隔）。默认输出会把**含非 ASCII 的路径整条加引号**
       （`"CodexSkills/…/研究/x.txt"`），于是：
         · 按前缀切目录时，同一个工作区被数成 `X` 与 `"X` **两个** ——
           「在制工作区」当场从 51 虚高到 **77**，而我已经把 77 写进首屏了；
         · 拿这种带引号的路径去 `open()` 一律失败，claims/cases 的行数**少数**。
       `-z` 不做任何转义，一次修掉这两处。
    """
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", REL + "/"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return [l for l in r.stdout.split("\0") if l.strip()]


def _lines(paths):
    """跨若干 jsonl 数**非空行**。读不到的当 0 但**印出来**，不静默。"""
    n, missing = 0, []
    for p in paths:
        f = ROOT / p
        if not f.is_file():
            missing.append(p)
            continue
        n += sum(1 for l in f.read_text(encoding="utf-8", errors="replace").splitlines()
                 if l.strip())
    return n, missing


def measure():
    """→ [(标签, 整格文本, 口径)]。**整格由本件拥有**：数、单位、分项一起现算。"""
    out = []
    files = tracked()
    if files is None:
        return None

    # ① 已入库人物档案 —— 以产物名册为准，不数目录
    #    ★ 数目录会错：`医疗护理师/` 下 0 个子目录，而 Galen/Vesalius/… 确已入库。
    ti = GROUP / "team-index.json"
    n1 = len(json.loads(ti.read_text(encoding="utf-8")).get("products", [])) if ti.is_file() else 0
    out.append(("已入库人物档案", f"**{n1}**",
                "`persona-distiller-group/team-index.json` 的 `products` 条数（**产物名册为准**，不数目录）"))

    # ② 在制工作区
    ws = {p.split("/workspaces/")[0] + "/workspaces/" + p.split("/workspaces/")[1].split("/")[0]
          for p in files if "/workspaces/" in p}
    out.append(("在制工作区", f"**{len(ws)}**",
                "`git ls-files` 里出现过的 `wip-*/workspaces/<人>/` 去重计数"))

    # ③ 语料（★ 两处布局必须分开报，合成一个数就没法用）
    txt = [p for p in files if p.endswith(".txt") and "_ids" not in os.path.basename(p)]
    inraw = [p for p in txt if "/raw/" in p]
    inref = [p for p in txt if "/references/sources/" in p]
    other = len(txt) - len(inraw) - len(inref)
    out.append(("语料（进了仓的正文）",
                f"**{len(txt):,} 份** ＝ `raw/` {len(inraw):,} ＋ "
                f"`references/sources/` {len(inref):,}"
                + (f" ＋ 其它布局 {other:,}" if other else ""),
                f"`git ls-files` 下 `_corpora/**/*.txt`（去掉 `_ids*`）"
                f"＝ `raw/` {len(inraw)} ＋ `references/sources/` {len(inref)}"
                f"{' ＋ 其它布局 %d' % (len(txt) - len(inraw) - len(inref)) if len(txt) != len(inraw) + len(inref) else ''}"
                "；★ 新工作区的 `raw/*.txt` 已被 `.gitignore` 挡下，靠 `_ids-rebuild.txt` 重建"))

    # ④ 断言
    cl = [p for p in files if p.endswith("evidence/claims.jsonl")]
    n4, miss4 = _lines(cl)
    if miss4:                                    # ★ 读不到就吭声，不许当成 0
        print(f"  ！ 断言：{len(miss4)} 份 claims.jsonl 打不开，例 {miss4[0]}")
    out.append(("断言", f"**{n4:,} 条**", f"被跟踪的 {len(cl)} 份 `evidence/claims.jsonl` 非空行合计"))

    # ⑤ 盲判用例（★ 只数 cases.jsonl，results.jsonl 不是题）
    cs = [p for p in files if p.endswith("evals/cases.jsonl")]
    n5, miss5 = _lines(cs)
    if miss5:
        print(f"  ！ 盲判用例：{len(miss5)} 份 cases.jsonl 打不开，例 {miss5[0]}")
    out.append(("盲判用例", f"**{n5:,} 题**（{len(cs)} 个工作区）",
                f"被跟踪的 {len(cs)} 份 `evals/cases.jsonl` 非空行合计"
                "（★ **只数 cases，不数 results** —— 一起数会翻一倍）"))

    # ⑥ 记延后/拒发
    n6 = len(json.loads(DEFER.read_text(encoding="utf-8")).get("deferred", [])) if DEFER.is_file() else 0
    out.append(("记延后/拒发", f"**{n6} 条**（都写明了理由与解锁条件）", "`_ledgers/_延后名单.json` 的 `deferred` 条数"))
    return out


ROW = re.compile(r"^\|\s*(?P<label>[^|]*?)\s*\|\s*(?P<val>[^|]*?)\s*\|\s*$")
# ★ 只认「粗体一开头那个数」：真表里写的是 `**2,064 份**`、`**160 条**`——
#   数字后面还有字，要求紧跟 `**` 会一条都匹配不上（第一版就是这么错的）。
#   也**不许**贪到后面的 `1,140`：`\*\*` 只在粗体起始处出现一次。
NUM = re.compile(r"\*\*\s*([\d,]+)")


def parse_table(text):
    """→ {行标签前缀: (原始行, 表里那个数 or None)}。**只认 `| 标签 | **数** |` 那种行。**"""
    got = {}
    for line in text.splitlines():
        m = ROW.match(line)
        if not m:
            continue
        lab = m.group("label")
        num = NUM.search(m.group("val"))
        if lab and num:
            got[lab] = (line, m.group("val").strip())
    return got


def match_label(lab, want):
    """表里的标签可能带补注（「语料（★ 两处布局，口径见下）」）⇒ 按前缀认。"""
    key = want.split("（")[0]
    return lab.split("（")[0].strip() == key.strip()


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    tbl = parse_table("""
| | |
|---|---:|
| 已入库人物档案 | **71** |
| 语料（★ 两处布局，口径见下） | **2,064 份** ＝ `raw/` 1,140 ＋ `references/sources/` 924 |
| 记延后/拒发 | **160 条**（都写明了理由与解锁条件） |
| 不是表的一行 |
""")
    chk("★ 逐字取自真表：三行都要认出来", len(tbl) == 3)
    chk("★ 取的是**整格原文**，不是只取那个数",
        any(v.startswith("**71**") for _, v in tbl.values()))
    chk("★ 语料那格连分项一起取回来（分项与数字必须一起比，否则会一格之内自相矛盾）",
        [v for k, (_, v) in tbl.items() if k.startswith("语料")]
        == ["**2,064 份** ＝ `raw/` 1,140 ＋ `references/sources/` 924"])
    chk("★ 标签带补注也要认出来（「语料（★ 两处布局…）」对上「语料」）",
        any(match_label(k, "语料（进了仓的正文）") for k in tbl))
    chk("不是表格的行不许混进来", not any("不是表的一行" in k for k in tbl))
    chk("★ 没有粗体数字的行不认（避免把说明行当成数据行）",
        not parse_table("| 已入库人物档案 | 七十一 |"))
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}"
          "（表样逐字取自 2026-08-13 的 START-HERE.md）")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="把表改成实测值")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    if not START.is_file():
        print(f"★★ **未判，不是通过**：找不到 {START}")
        return 4
    rows = measure()
    if rows is None:
        print("★★ **未判，不是通过**：`git ls-files` 跑不了（不在 git 树里？）")
        return 4

    text = START.read_text(encoding="utf-8")
    tbl = parse_table(text)
    bad, miss = [], []
    print(f"START-HERE.md 首屏那张表　—— 口径一律以 `git ls-files` 为准"
          f"（收件人 clone 之后真正拿到的东西）\n")
    for lab, cell, how in rows:
        hit = [(k, v) for k, (_, v) in tbl.items() if match_label(k, lab)]
        if not hit:
            miss.append(lab)
            print(f"  ？ {lab:16s} **表里没有这一行**　实测应为：{cell}")
        else:
            k, shown = hit[0]
            same = " ".join(shown.split()) == " ".join(cell.split())
            if not same:
                bad.append((k, shown, cell))
            print(f"  {'✓' if same else '✗'} {lab}")
            print(f"       实测：{cell}")
            if not same:
                print(f"       表里：{shown}　← **不一致**")
        print(f"       口径：{how}")

    if a.apply and bad:
        wrote = 0
        for k, shown, cell in bad:
            line, _ = tbl[k]
            new = f"| {k} | {cell} |"
            if line not in text:                  # ★ 替换没命中要吭声，不许静默略过
                print(f"  ！ 改不动：{k}（表里那一行找不回来了，请人看一眼）")
                continue
            text = text.replace(line, new, 1)
            wrote += 1
        START.write_text(text, encoding="utf-8")
        print(f"\n✅ 已把 {wrote}/{len(bad)} 格改成实测值（**整格重写**：数、单位、分项一起）")
        print("★ 标签一个字没动；表外的散文本件够不着，**要人另行核**。")
        return 0 if wrote == len(bad) else 1

    if bad or miss:
        print(f"\n✗ **{len(bad)} 个数与实测不一致**"
              f"{f'，另有 {len(miss)} 行表里没有' if miss else ''}"
              "　—— 跑 `--apply` 改（整格重写）；表外的散文要人另行核")
        return 1
    print("\n✓ 表里每个数都与实测一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
