#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_lessons_library.py —— **踩坑库：条数、索引、文件三者对不对得上**

## 为什么有这件

`文档/踩坑库/` 被 `START-HERE.md` 列为**开工前必读**。2026-08-13 核了一遍：

* README 标题写「**153 条**」，而目录里的教训文件是 **151** 条 ——
  那个 153 是 `ls *.md | wc -l`，**把 `README.md` 与 `00-索引.md` 自己也数了进去**；
* 另有 **3 条**教训根本没搬进仓（源目录 154，仓里 151）；
* 还有 **2 条**搬进来之后源侧又改过，仓里那份是旧的。

★ 三个毛病同一个成因：**搬运是手工的，没有任何东西回头核过。**
  [[every-requirement-needs-an-owner]]

★ 本件**不**去比对那个私有记忆目录（`~/.claude/…`）——
  那是某一家助手的目录，收件人机器上根本没有，拿它当判据会变成
  一道**在别人机器上永远红的门**（[[a-red-that-can-never-turn-green-is-not-a-signal]]、
  [[untested-fallback-branches-only-fire-on-their-machine]]）。
  它只判**仓内三者自洽**：README 说的数 ／ 索引的行 ／ 实际的文件。

## 判什么

1. README 首行写的条数 ＝ 实际教训文件数（`*.md` 去掉 `README.md`、`00-索引.md`）
2. `00-索引.md` 的条目数 ＝ 实际教训文件数
3. 索引里每条链接指向的文件**存在**
4. 每个教训文件**在索引里有一条**

任一不符 ⇒ ✗ 红（rc=1）。

## 用法

    python3 check_lessons_library.py
    python3 check_lessons_library.py --self-test

退出码：0＝三者一致；1＝不一致；4＝找不到踩坑库目录（**未判**）
"""
import argparse
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent


def _root():
    r = subprocess.run(["git", "-C", str(PD), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return pathlib.Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else PD.parents[2]


LIB = _root() / "文档" / "踩坑库"
META = {"README.md", "00-索引.md"}
LINK = re.compile(r"^-\s*\[[^\]]*\]\(([^)]+\.md)\)")
TITLE_N = re.compile(r"(\d+)\s*条")


def audit(lesson_names, index_lines, readme_first_line):
    """→ [(项, 通过?, 说明)]。**纯函数**，自测不碰磁盘。"""
    lessons = set(lesson_names)
    linked, dup = [], []
    for l in index_lines:
        m = LINK.match(l.strip())
        if m:
            (dup if m.group(1) in linked else linked).append(m.group(1))
    m = TITLE_N.search(readme_first_line or "")
    said = int(m.group(1)) if m else None
    dangling = sorted(set(linked) - lessons)
    unlisted = sorted(lessons - set(linked))
    return [
        ("README 标题的条数 ＝ 教训文件数",
         said == len(lessons),
         f"标题说 {said}，实际 {len(lessons)}"
         + ("　★ 多半是把 README.md／00-索引.md 自己也数了进去" if said and said > len(lessons) else "")),
        ("索引条目数 ＝ 教训文件数",
         len(linked) == len(lessons),
         f"索引 {len(linked)} 条（重复 {len(dup)}），文件 {len(lessons)} 个"),
        ("索引里的链接都指向存在的文件", not dangling,
         f"指空 {len(dangling)} 条" + (f"：{dangling[:3]}" if dangling else "")),
        ("每个教训文件都在索引里", not unlisted,
         f"没进索引 {len(unlisted)} 个" + (f"：{unlisted[:3]}" if unlisted else "")),
    ]


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★ 逐字取自 2026-08-13 的真实状态：标题 153、文件 151（多数了那两份 meta）
    bad = audit(["a.md", "b.md"] + [f"x{i}.md" for i in range(149)],
                ["- [甲](a.md)", "- [乙](b.md)"] + [f"- [x](x{i}.md)" for i in range(149)],
                "# 踩坑库 —— 153 条实测教训")
    chk("★ 真实那一次：标题 153 而文件 151 ⇒ 第 1 项必须红",
        bad[0][1] is False and "多半是把" in bad[0][2])
    chk("★ 同一次里索引是齐的 ⇒ 第 2/3/4 项**不许**跟着红"
        "（一个毛病只报一处，否则分不清是几件事）",
        all(x[1] for x in bad[1:]))

    good = audit(["a.md", "b.md"], ["- [甲](a.md)", "- [乙](b.md)"], "# 踩坑库 —— 2 条实测教训")
    chk("对齐之后四项全绿", all(x[1] for x in good))

    miss = audit(["a.md", "b.md"], ["- [甲](a.md)"], "# 踩坑库 —— 2 条实测教训")
    chk("★ 有文件没进索引：第 4 项要报，并点名是哪个",
        miss[3][1] is False and "b.md" in miss[3][2])

    dang = audit(["a.md"], ["- [甲](a.md)", "- [鬼](ghost.md)"], "# 踩坑库 —— 1 条实测教训")
    chk("★ 索引指向不存在的文件：第 3 项要报，并点名",
        dang[2][1] is False and "ghost.md" in dang[2][2])

    nb = audit(["a.md"], ["- [甲](a.md)"], "# 踩坑库")
    chk("标题里没有数字 ⇒ 第 1 项算不符（**不许当成通过**）", nb[0][1] is False)

    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}"
          "（① 逐字取自 2026-08-13 真实状态：标题 153 / 文件 151）")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    if not LIB.is_dir():
        print(f"★★ **未判，不是通过**：找不到 {LIB}")
        return 4
    names = sorted(p.name for p in LIB.glob("*.md") if p.name not in META)
    idx = LIB / "00-索引.md"
    readme = LIB / "README.md"
    rows = audit(names,
                 idx.read_text(encoding="utf-8").splitlines() if idx.is_file() else [],
                 (readme.read_text(encoding="utf-8").splitlines() or [""])[0] if readme.is_file() else "")

    print(f"踩坑库 {LIB}　教训文件 {len(names)} 个"
          f"（`*.md` 去掉 {'、'.join(sorted(META))}）\n")
    bad = 0
    for item, good, why in rows:
        bad += 0 if good else 1
        print(f"  {'✓' if good else '✗'} {item}")
        print(f"       {why}")
    print(f"\n{'✓ 三者一致' if not bad else f'✗ {bad} 项不符'}")
    print("\n★ 射程：**只判仓内三者自洽**。它不去比对那个私有记忆目录"
          "（`~/.claude/…`）——收件人机器上没有那个目录，拿它当判据"
          "会变成一道在别人机器上永远红的门。")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
