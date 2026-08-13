#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""workspace_roots.py —— **按台账找工作区，不按路径形状找**

## 抓到它的那一次

2026-08-14，从裸 clone 做交付验收，`measure_distinct_works --all` 报
「能量到 24 个、**未量 29 个**」。去翻那 29 个里的 `clara-barton`，
发现它的台账在

    _corpora/wip-barton-117/workspaces/clara-barton/**clara-barton**/evidence/source-ledger.jsonl
                                       ^^^^^^^^^^^^  ^^^^^^^^^^^^
                                       名字重复了一层

而判据的 glob 是 `wip-*/workspaces/*`，落在**外层**那一级——那一级没有 `evidence/`，
于是整个工作区被判成「未量」。

**这样的工作区有 8 个，合计 train 778 份，而且它们的正文一份不缺地在包里。**

    alexander-fleming 68｜clara-barton 210｜florence-nightingale 108｜henry-clifton-sorby 36
    oliver-wendell-holmes-jr 13｜rudolf-virchow 226｜william-blackstone 14｜william-osler 103

⇒ 我当天发的「全库 1950 份 train」少算了 778 份（**28.5%**）。
[[a-gates-scan-set-is-smaller-than-reality]] 的**第八种**：
前七种是 glob 只认一层、`fns.get("main")`、只扫本技能、Python 版本、
写在正则里的长度下限……这一种是**目录名多重复了一层**。

## 本件怎么找

**不按路径形状找，按「哪里有 `evidence/source-ledger.jsonl`」找。**
一个工作区就是「含 `evidence/source-ledger.jsonl` 的那个目录」，
无论它在 `wip-X/workspaces/Y/` 还是 `wip-X/workspaces/Y/Y/` 还是 `wip-X/`。

★ 去重规则：若 A 是 B 的祖先且两者都有台账，**只留最深的那个**
  （外层那个是空壳，留着会把同一批源数两遍）。

## 用法

    from workspace_roots import iter_workspaces
    for ws in iter_workspaces(CORPORA): ...

    python3 workspace_roots.py            # 列出所有工作区 ＋ 标出非常规布局
    python3 workspace_roots.py --self-test
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"
LEDGER = "evidence/source-ledger.jsonl"


def iter_workspaces(corpora: pathlib.Path):
    """→ 排好序的工作区目录列表。**按台账定位**，不按路径层数。"""
    found = {p.parent.parent for p in corpora.glob("wip-*/**/" + LEDGER)}
    # ★ 去掉「自己是别人的祖先」的那些外层空壳 —— **留最深的**。
    #   我第一版写反了：`o in d.parents` 是「d 有祖先在 found 里」⇒ 反而把**深的**删掉、
    #   留下空壳外层。自测里那条「留下的是深的那个」当场判红，才发现。
    #   正确的是 `d in o.parents`：d 是别人的祖先 ⇒ d 是外层空壳，删 d。
    out = [d for d in found if not any(o != d and d in o.parents for o in found)]
    return sorted(out)


def layout_of(ws: pathlib.Path, corpora: pathlib.Path) -> str:
    """这个工作区是哪种布局。给人看的，不参与判定。"""
    rel = ws.relative_to(corpora).parts
    if len(rel) == 3 and rel[1] == "workspaces":
        return "常规 wip-X/workspaces/Y"
    if len(rel) == 4 and rel[1] == "workspaces" and rel[2] == rel[3]:
        return "★ 名字重复一层 wip-X/workspaces/Y/Y"
    if len(rel) == 1:
        return "★ 扁平 wip-X"
    return "★ 其他：" + "/".join(rel)


def self_test() -> int:
    import tempfile
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    with tempfile.TemporaryDirectory() as td:
        C = pathlib.Path(td)
        def mk(p):
            q = C / p / "evidence"
            q.mkdir(parents=True, exist_ok=True)
            (q / "source-ledger.jsonl").write_text("{}\n", encoding="utf-8")
        mk("wip-a-1/workspaces/alice")                 # 常规
        mk("wip-b-2/workspaces/bob/bob")               # ★ 名字重复一层
        mk("wip-c-3")                                  # ★ 扁平
        (C / "wip-d-4/workspaces/dan").mkdir(parents=True)   # 没有台账 ⇒ 不算工作区
        got = iter_workspaces(C)
        names = sorted(p.name for p in got)
        chk(f"★ 三种布局都找得到（实得 {names}）", names == ["alice", "bob", "wip-c-3"])
        chk("★★ **名字重复一层的能找到**（原来的 glob 会漏掉它）",
            any(p.parts[-2:] == ("bob", "bob") for p in got))
        chk("★ 反例：没有台账的目录不算工作区", not any(p.name == "dan" for p in got))
        # ★★ 外层也放一份台账 ⇒ 只留最深的，不许数两遍
        mk("wip-b-2/workspaces/bob")
        got2 = iter_workspaces(C)
        bobs = [p for p in got2 if "bob" in p.parts]
        chk(f"★★ 外层也有台账时**只留最深的一个**（实得 {len(bobs)} 个）", len(bobs) == 1)
        chk("★ 留下的是深的那个", bobs and bobs[0].parts[-2:] == ("bob", "bob"))
        chk(f"★ 布局标注：常规 → 「{layout_of(C/'wip-a-1/workspaces/alice', C)}」",
            layout_of(C / "wip-a-1/workspaces/alice", C).startswith("常规"))
        chk("★ 布局标注：重复一层被标星",
            layout_of(C / "wip-b-2/workspaces/bob/bob", C).startswith("★ 名字重复"))
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    ws = iter_workspaces(CORPORA)
    odd = [w for w in ws if not layout_of(w, CORPORA).startswith("常规")]
    print(f"按台账找到工作区 **{len(ws)}** 个；其中**非常规布局 {len(odd)}** 个")
    print("★ 判据若用 `wip-*/workspaces/*` 这个 glob，**下面这些会被整个漏掉**：\n")
    for w in odd:
        print(f"   {layout_of(w, CORPORA):32s} {w.relative_to(CORPORA)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
