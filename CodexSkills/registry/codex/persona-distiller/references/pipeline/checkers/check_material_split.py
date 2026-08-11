#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第九件检查器：账本里的 split 与磁盘上的物料是否一致。

## 它补的是哪个缺口

前八件检查器的方向是：
- 七件：**产物 → 语料**（引文在不在、实体在不在、有没有残留）
- 一件：**产物 → 现算值**（我的算术对不对）

**没有一件在查「账本说的」与「磁盘上放的」是否一致。**

本轮的实际事故：换 holdout 时我只改了账本的 `split` 字段，没搬物料。结果是

    raw/ 94 份，train 也是 94 条 —— 计数完全正确
    但里面装着已成 holdout 的 three_principles，缺着已回 train 的 design_is_isms

**一进一出，数目恰好抵消。** holdout 的正文因此躺在建模者能读到的目录里，
holdout 隔离在物理上失效，而所有的门都放行。

## 判据

成员级（不是计数级）两向核对：

- `raw/` 与 `references/sources/` 的目录集合，必须**恰好等于** train 源集合
- 缺（train 有而磁盘无）与多（磁盘有而 train 无）**分别报**

只查「有没有缺」会漏掉「多了 holdout」；只查计数则一进一出全看不见。

## 为什么 holdout 那一侧是硬门

train 少一份物料只是下游工具会漏读，可以补。
**holdout 的正文出现在 raw/ 里则是隔离失效**——建模者可能已经读过它，
而 `known` 套组的全部意义就是「用没见过的材料验证」。这一侧一旦破，
这一轮的 known 分数就不可信，必须换 holdout 重来。
"""
import contextlib, io, json, os, sys, tempfile
from pathlib import Path

MATERIAL_DIRS = ("raw", "references/sources")


def check(workspace: str) -> int:
    W = Path(workspace)
    ledger = W / "evidence/source-ledger.jsonl"
    if not ledger.is_file():
        print(f"✗ 找不到账本：{ledger}")
        return 2
    rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    train = {r["source_id"] for r in rows if r.get("split") == "train"}
    hold = {r["source_id"] for r in rows if r.get("split") == "holdout"}
    print(f"账本：{len(rows)} 条（train {len(train)} / holdout {len(hold)}）\n")

    fatal = soft = checked = 0
    for sub in MATERIAL_DIRS:
        d = W / sub
        if not d.is_dir():
            print(f"  ? {sub}/ 不存在——未检查，不等于通过")
            continue
        checked += 1
        have = {x for x in os.listdir(d) if x.startswith("src-")}
        missing = sorted(train - have)          # train 有、磁盘无
        leaked = sorted(have & hold)            # 磁盘上出现了 holdout ← 致命
        extra = sorted(have - train - hold)     # 既不在 train 也不在 holdout
        status = "✓" if not (missing or leaked or extra) else "✗"
        print(f"  {status} {sub}/  {len(have)} 份"
              f" | 缺 {len(missing)} | **holdout 泄漏 {len(leaked)}** | 未知 {len(extra)}")
        for s in leaked:
            print(f"       ✗✗ holdout 正文出现在此：{s}  ← 隔离失效，本轮 known 分数不可信")
            fatal += 1
        for s in missing:
            print(f"       ✗  train 缺物料：{s}")
            soft += 1
        for s in extra:
            print(f"       ✗  账本里没有的目录：{s}")
            soft += 1

    print()
    # ★★ 2026-08-12：**「未检查」不许走到「通过」。**
    #   在此之前，两个物料目录都不存在时本件会印两行「不等于通过」，
    #   然后印 **「结论: 通过」并返回 0** ——正文说不知道，退出码说没问题。
    #   本件已接进 `quality_check`，于是一个还没落物料的工作区能拿到绿章。
    #   实测爆炸半径：36 个有账本的工作区**全部**两个目录俱在 ⇒ 改它零影响，
    #   只在真出问题时才响（[[empty-default-swallows-unknown]]）。
    if checked == 0:
        print(f"结论: 不通过（**一个物料目录都没检查到**：{'、'.join(MATERIAL_DIRS)} 都不存在——"
              f"账本里却有 {len(train)} 条 train。这不是通过，是没查）")
        return 2
    if fatal:
        print(f"结论: 不通过（**{fatal} 处 holdout 泄漏，硬门**）")
        return 2
    if soft:
        print(f"结论: 不通过（{soft} 处成员错配）")
        return 2
    print("结论: 通过")
    return 0


# ★ 2026-08-12：原先这里有个 `SELF_TEST` 常量（五个纯集合场景），
#   配一段把 `check()` 的判定式抄了一遍的 `self_test()`。**常量留着会误导**——
#   它长得像「本件的测试用例」，而那五条从来没经过 `check()`。
#   场景本身是好的，已原样搬进 `self_test()` 的 `CASES`，在真工作区上跑。


def _fixture(td, train, hold, have, sub="raw", ledger=True):
    """在 tempdir 上搭一个真工作区：账本 + 物料目录。"""
    w = Path(td)
    (w / "evidence").mkdir(parents=True, exist_ok=True)
    if ledger:
        rows = ([{"source_id": f"src-{s}", "split": "train"} for s in sorted(train)] +
                [{"source_id": f"src-{s}", "split": "holdout"} for s in sorted(hold)])
        (w / "evidence/source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    if sub:
        d = w / sub
        d.mkdir(parents=True, exist_ok=True)
        for s in sorted(have):
            (d / f"src-{s}").mkdir(exist_ok=True)
    return w


def _run(**kw):
    """跑真 `check()`，返回 (rc, 屏幕输出)。"""
    with tempfile.TemporaryDirectory() as td:
        w = _fixture(td, **kw)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(str(w))
        return rc, buf.getvalue()


def self_test() -> int:
    """★★★ 2026-08-12 重写：**原自测把判定逻辑抄了一遍，等于没测。**

    原文一行：

        fired = bool((train - have) or (have & hold) or (have - train - hold))

    ——这是 `check()` 里那三行的**复制品**，不是对它的检验。
    把 `check()` 整个删掉，五条断言照样全绿；`check_selftest_reach` 因此把本件
    列在「验了配料、没验判决」名单上。同一个病在 `check_quote_integrity`
    的 `count_unchecked` 上也犯过一次（见该件 docstring）。

    现在每一条都在 tempdir 上搭真工作区、跑真 `check()`、看它的 **rc 与屏幕输出**。
    """
    missed = 0
    print("══ 成员级两向核对（tempdir 上跑真 check()）══")
    T, H = {"a", "b"}, {"c"}
    CASES = [
        ({"a", "b"},      0, None,          "正常：磁盘 == train"),
        ({"a", "b", "c"}, 2, "holdout 正文出现在此",
         "**holdout 泄漏（硬门）**——本轮 known 分数不可信"),
        ({"a"},           2, "train 缺物料",  "train 缺物料"),
        ({"a", "c"},      2, "holdout 正文出现在此",
         "★ 一进一出：**计数相等而成员错**——本件的立身之本"),
        ({"a", "b", "z"}, 2, "账本里没有的目录", "账本里没有的目录"),
    ]
    for have, want_rc, want_txt, why in CASES:
        rc, out = _run(train=T, hold=H, have=have)
        ok = rc == want_rc and (want_txt is None or want_txt in out)
        print(f"  {'✓' if ok else '✗'} rc={rc}（应 {want_rc}）  {why}")
        missed += not ok

    # ★ 泄漏与缺料都返回 2，**光看 rc 分不开**——所以上面每条都验了屏幕文字。
    #   这一条把「分得开」单独钉一遍：缺料时**不许**出现泄漏那句话。
    rc, out = _run(train=T, hold=H, have={"a"})
    ok = "holdout 正文出现在此" not in out and "train 缺物料" in out
    print(f"  {'✓' if ok else '✗'} 缺料 ≠ 泄漏：同为 rc=2，**诊断文字必须分得开**")
    missed += not ok

    # ★★ 「未检查」不许走到「通过」（2026-08-12 修的真缺陷）
    rc, out = _run(train=T, hold=H, have=set(), sub=None)
    ok = rc == 2 and "一个物料目录都没检查到" in out and "结论: 通过" not in out
    print(f"  {'✓' if ok else '✗'} **两个物料目录都不存在 → rc=2**"
          f"（改前印「不等于通过」却返回 0，rc={rc}）")
    missed += not ok

    # ★ 反向：`references/sources/` 缺而 `raw/` 在且正确 ⇒ 仍算通过。
    #   没有这一条，上一条可能只是「少一个目录就报错」——那会误伤 36 个现存工作区。
    rc, out = _run(train=T, hold=H, have={"a", "b"}, sub="raw")
    ok = rc == 0 and "references/sources/ 不存在" in out
    print(f"  {'✓' if ok else '✗'} 反向：只有 raw/ 且正确 → 仍 rc=0（不误伤单目录布局）")
    missed += not ok

    # ★ 账本本身不在 → rc=2，且**不许**报「通过」
    rc, out = _run(train=T, hold=H, have=set(), ledger=False)
    ok = rc == 2 and "找不到账本" in out
    print(f"  {'✓' if ok else '✗'} 账本不存在 → rc=2 且点名找不到账本")
    missed += not ok

    print(f"\n自测 {'全部通过' if not missed else f'{missed} 条不合——本检查器已失效'}")
    return 0 if not missed else 2


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if len(sys.argv) < 2:
        print("usage: check_material_split.py <workspace> | --self-test")
        sys.exit(2)
    sys.exit(check(sys.argv[1]))
