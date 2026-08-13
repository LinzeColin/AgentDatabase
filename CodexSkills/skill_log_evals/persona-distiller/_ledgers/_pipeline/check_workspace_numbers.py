#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_workspace_numbers.py —— **`wip-<人>-<号>` 的号有没有撞、有没有断**

## 为什么有这件

2026-08-13 排第 3 批时，`_corpora/` 里同时存在：

    wip-hopkins-189     ← 第 2 批（只有 04-探源.tsv，人记了延后）
    wip-churchill-189   ← 第 3 批（有 24 份语料）

**同一个号发了两次。** 追根问底：**这个号根本没有真源**——

* `_延后名单.json` 一条里有 `name`/`reason`/`处置类` …… **没有编号字段**；
* `next_person.py` 判「做没做过」看的是**磁盘上有没有工作区目录**，不看号；
* 于是号只活在目录名里，**由我每次手敲**，没有任何东西保证它唯一。

★ [[every-requirement-needs-an-owner]]：**门不会提醒你少了一道门。**
  「编号唯一」这条要求从头到尾没有主人，撞了 73 个工作区都没人吭声。

★ 也是 [[a-checkers-scan-set-is-smaller-than-reality]] 的反面：
  这次不是判据扫得太窄，而是**压根没有判据**。

## 判什么

拿 `_corpora/wip-*` 逐个拆成 `(名, 号)`：

1. **撞号** —— 同一个号出现两次以上 ⇒ ✗ **红**（rc=1）
2. **拆不出号**（`wip-godin`）—— 单列一档 **只报不判**（老式目录本来就没发过号）
3. 号断档（1,2,4）—— **只报不判**：延后／出局的人不建工作区就会留空档，
   空档是正常的，**不是缺陷**。

★★★ **射程切在「形状」上，绝不切在「唯一」上** —— 这里我连错两次：

  第一版：`wip-godin`（673 份语料的老式扁平暂存目录，从来没有号）被报成
  「形状不对」⇒ 一道**永远红的门**（[[a-red-that-can-never-turn-green-is-not-a-signal]]）。

  第二版：我改成「只收有 `workspaces/` 子层的目录」，结果
  **`wip-hopkins-189` 只有一个 tsv、没有那一层，当场落到射程外** ——
  这道判据于是扫不到它自己那个例子了。[[a-gates-scan-set-is-smaller-than-reality]]

  ⇒ 定版：**唯一性收全部 `wip-*-<号>`，不看目录里长什么样**；
    只有「没有号」的老式目录（`wip-godin`）单列一档，**不判**。

★ 本件**不**判「这个号该给谁」——它没有真源，也就没有对错，
   只有**唯一**这一条能判。撞了之后改谁的号是人的事。

## 用法

    python3 check_workspace_numbers.py
    python3 check_workspace_numbers.py --self-test

退出码：0＝没撞号；1＝撞号了；4＝一个 wip-* 都没有（**未判**）
"""
import argparse
import glob
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CORPORA = HERE.parent.parent / "_corpora"

SHAPE = re.compile(r"^wip-(?P<name>.+)-(?P<no>\d+)$")


def parse(dirnames):
    """→ (按号归组 {号: [名…]}, 没有号的 [目录名…])。**纯函数**。

    ★★ 传进来的是**全部** `wip-*` 目录，**不按内部布局过滤**。
       撞号跟目录里长什么样无关；按布局过滤会让判据扫不到自己那个例子。
    """
    by_no, bad_shape = {}, []
    for d in dirnames:
        m = SHAPE.match(d)
        if not m:
            bad_shape.append(d)
            continue
        by_no.setdefault(int(m.group("no")), []).append(m.group("name"))
    return by_no, bad_shape


def gaps(by_no):
    """号断档——**只报不判**（延后的人不建工作区，空档正常）。"""
    if not by_no:
        return []
    lo, hi = min(by_no), max(by_no)
    return [n for n in range(lo, hi + 1) if n not in by_no]


def self_test() -> int:
    """★ 正例逐字取自 2026-08-13 真实撞到的那一对。"""
    ok = 0
    total = 0

    def chk(desc, cond):
        nonlocal ok, total
        total += 1
        ok += 1 if cond else 0
        print(f"  {'✓' if cond else '✗'} {desc}")

    # ① 真实撞号
    by_no, bad = parse(["wip-churchill-189", "wip-hopkins-189", "wip-dewey-190"])
    dup = {n: v for n, v in by_no.items() if len(v) > 1}
    chk("★ 真实那一对必须报：189 → churchill + hopkins",
        dup == {189: ["churchill", "hopkins"]} and not bad)

    # ② 改完之后必须不报
    by_no2, bad2 = parse(["wip-churchill-191", "wip-hopkins-189", "wip-dewey-190"])
    chk("改号之后：一条都不许报",
        not [n for n, v in by_no2.items() if len(v) > 1] and not bad2)

    # ③ 名字里带连字符——**不许把它拆成号**
    by_no3, bad3 = parse(["wip-roberts-austen-135", "wip-von-liebig-124"])
    chk("★ 名字含连字符（roberts-austen／von-liebig）要拆对，不许当成撞号",
        by_no3 == {135: ["roberts-austen"], 124: ["von-liebig"]} and not bad3)

    # ④ 没有号的必须单列报出（而不是安静跳过，也不算红）
    _, non4 = parse(["wip-godin", "wip-dewey-190"])
    chk("★ `wip-godin` 没有号：必须报出来（不许安静吞掉），但**不算红**",
        non4 == ["wip-godin"])

    # ⑤ ★★ 回归守卫：撞号的一方是**老式目录**时也必须报
    #    我第二版按「有没有 workspaces/ 子层」过滤，`wip-hopkins-189` 当场落到射程外，
    #    判据于是扫不到自己那个例子。这一条钉死：唯一性不看目录布局。
    by_no5, _ = parse(["wip-churchill-189", "wip-hopkins-189"])
    chk("★★ 撞号一方是老式目录（hopkins 只有 1 个 tsv）时**照样必须报**"
        "——唯一性不许按目录布局过滤",
        {n: v for n, v in by_no5.items() if len(v) > 1} == {189: ["churchill", "hopkins"]})

    # ⑥ 断档只报不判
    chk("★ 断档只报不判：183,184,186 中间缺 185 要报出来但不算红",
        gaps({183: ["a"], 184: ["b"], 186: ["c"]}) == [185])

    # ⑦ 空输入 ⇒ 未判，**不是通过**
    chk("空输入 ⇒ 没有号可判（由 main 报 rc=4，不许当成绿）",
        parse([]) == ({}, []))

    print(f"\n{'✓ 全过' if ok == total else f'✗ {total - ok}/{total} 项不符'}"
          "（① 逐字取自 2026-08-13 真实撞到的 churchill/hopkins）")
    return 0 if ok == total else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", default=str(CORPORA))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    # ★★ 唯一性收**全部** wip-*，不按目录布局过滤（见文件头「连错两次」）
    allw = sorted(p for p in glob.glob(os.path.join(a.corpora, "wip-*")) if os.path.isdir(p))
    dirs = [os.path.basename(p) for p in allw]
    sizes = {os.path.basename(p): sum(len(f) for _, _, f in os.walk(p)) for p in allw}
    if not dirs:
        print(f"★★ **未判，不是通过**：{a.corpora} 下一个 wip-* 都没有")
        return 4

    by_no, no_number = parse(dirs)
    dup = {n: v for n, v in sorted(by_no.items()) if len(v) > 1}
    g = gaps(by_no)

    print(f"扫了 {len(dirs)} 个工作区，号从 {min(by_no) if by_no else '—'} "
          f"到 {max(by_no) if by_no else '—'}")
    if dup:
        print(f"\n✗ **撞号 {len(dup)} 处**：")
        for n, v in dup.items():
            print(f"  · {n} 发给了 {len(v)} 个人：{'、'.join(sorted(v))}")
        print("  怎么修：改**没有任何文档按号引用过**的那一个"
              "（先 `grep -rn \"wip-<名>-<号>\"` 确认没人引用）。")
    if not dup:
        print(f"\n✓ 没有撞号（{len(dirs)} 个目录里 {len(dirs) - len(no_number)} 个带号）")
    if g:
        print(f"\n· 号断档 {len(g)} 个（**只报不判**——延后/出局的人不建工作区，空档正常）："
              f"{g[:20]}{' …' if len(g) > 20 else ''}")

    if no_number:
        print(f"\n· 没有号 {len(no_number)} 个（**不判**——老式扁平暂存目录，本来就没发过号）：")
        for nm in no_number:
            print(f"    {nm}　{sizes.get(nm, 0)} 个文件")
    print("\n★ 射程：**只判唯一**（形状/断档只报不判）。号没有真源"
          "（`_延后名单.json` 没有编号字段，`next_person.py` 看目录不看号），"
          "所以「这个号该给谁」无所谓对错，本件不判。")
    return 1 if dup else 0


if __name__ == "__main__":
    raise SystemExit(main())
