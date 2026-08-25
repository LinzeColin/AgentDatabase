#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这道判据这次扫了几个单位？——和该扫的一样多吗？**

## 为什么有这道判据

「判据绿了，但它指错了文件」在本流水线里**已经发生四次**：

| # | 判据 | 表征 |
|---|---|---|
| 1 | `check_holdout_overlap` | **从来没被调用过** |
| 2 | `check_contract_drift` | 只存在于一侧的文件**静默跳过** |
| 3 | `check_corpus_presence` | 账本与文件是**两批不相干的东西**，相减得出「很健康」 |
| 4 | `check_corpus_presence` | root 传高一层，17 个工作区被 **collapse 成一行**，报绿 |

**四次的表征完全一样：一片绿。** 前三次我都只修了那一个实例。

**共同点不是「有 bug」，是「射程小于该扫的范围，而输出看不出来」。**
一道扫 0 个单位的判据和一道扫 17 个单位全过的判据，
在终端上**都是一个 ✓**。

## 判据

1. **该扫的**——磁盘上有账本的工作区目录（真源是文件系统，不是我的记忆）
2. **实际扫的**——`check_corpus_presence` 报出的每一行

**按路径包含关系判覆盖，不按名字相等。**
一条名册项算被盖住，当且仅当**某一行的路径是它的前缀**。

## ★★ 为什么不是「名字相等」——我第一版就在这里栽了

第一版拿两个名字集合相减，实测报「少扫 11 个」：

```
该扫 15 个工作区，实际扫了 15 个
✗ **少扫 11 个**：
    _corpora/wip-fleming-111/workspaces/alexander-fleming/alexander-fleming
    _corpora/wip-godin/ws-godin/seth-godin
    ...
```

**计数明明对得上（15 = 15），名字却一个都不匹配**——
`roster()` 报的是**账本所在的工作区**（`workspaces/<人>/`），
`scan()` 报的是**外层容器**（`wip-*`）。**它们指的是同一批东西。**

**这道判据自己犯了它要抓的错：拿两套不同的标识符空间相减。**
写进来，因为下一个改它的人会再犯一次。

## ★ 它不判语料本身

**它只判射程。** 一道判据可以射程正确而结论全错——
那是各自的反向对照要管的事。**这一道只回答「你看了几个」。**

## 它判不了什么

- **判不了那些不按工作区扫的判据**（如 `check_quoted_arithmetic` 按 payload 扫）。
  射程的定义因判据而异，**这一道只覆盖「按工作区扫」这一族**。
- **判不了「扫到了但读错了」**——第 3 次那种（两批不相干的东西相减）
  射程是对的，错在口径。**这一道抓不住它，别指望。**
"""
import argparse
import importlib.util
import pathlib
import sys


def roster(root: pathlib.Path) -> set[str]:
    """**该扫的**：磁盘上带账本的工作区目录（真源是文件系统）。"""
    out = set()
    for led in root.rglob("source-ledger.jsonl"):
        d = led.parent
        if d.name == "evidence":          # <工作区>/evidence/source-ledger.jsonl
            d = d.parent
        try:
            out.add(str(d.relative_to(root)))
        except ValueError:
            continue
    return out


def covers(row: str, want: str) -> bool:
    """**这一行盖住这条名册项了吗**——按路径前缀，不按名字相等。"""
    return want == row or want.startswith(row.rstrip("/") + "/")


def scanned(root: pathlib.Path, checker: pathlib.Path) -> set[str]:
    """**实际扫的**：调 check_corpus_presence.scan()，取它报出的行名。"""
    spec = importlib.util.spec_from_file_location("_pd_presence", checker)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {r[0] for r in mod.scan(root) if r[1] is not None}


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    import json
    import hashlib
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    def mk(root, rel, n=1, nested=False):
        w = root / rel
        (w / "raw").mkdir(parents=True, exist_ok=True)
        lines = []
        for i in range(n):
            f = w / "raw" / f"s{i}.txt"
            f.write_text(f"x{i}", encoding="utf-8")
            lines.append(json.dumps({"local_path": f"raw/s{i}.txt",
                                     "checksum": hashlib.sha256(f.read_bytes()).hexdigest()}))
        led = (w / "evidence") if nested else w
        led.mkdir(parents=True, exist_ok=True)
        (led / "source-ledger.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("── ★ 正向：两种账本布局都要数进来 ──")
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        mk(root, "wip-a", 2)                    # 顶层账本
        mk(root, "wip-b", 3, nested=True)       # evidence/ 下的账本
        chk("名册 = {wip-a, wip-b}", roster(root) == {"wip-a", "wip-b"})

    print("── ★★ 反向对照 ①：**容器套一层，名册不许缩水** ──")
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        mk(root, "_corpora/wip-a", 2)
        mk(root, "_corpora/wip-b", 3)
        got = roster(root)
        chk("名册 = 2 个（不是 1 个 `_corpora`）",
            got == {"_corpora/wip-a", "_corpora/wip-b"})

    print("── ★★ 反向对照 ②：**空目录不许算进名册**（否则永远对不上） ──")
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        mk(root, "wip-a", 2)
        (root / "wip-empty").mkdir()
        chk("没有账本的目录不进名册", roster(root) == {"wip-a"})

    print("── ★ 反向对照 ③：**少扫要报失败，不许当「没问题」** ──")
    want, got = {"wip-a", "wip-b"}, {"wip-a"}
    miss = {w for w in want if not any(covers(g, w) for g in got)}
    chk("名册 2 个、实扫 1 个 → 报出 wip-b", miss == {"wip-b"})

    print("── ★★ 反向对照 ④：**容器行盖住它底下的工作区，不算少扫** ──")
    want = {"wip-a/workspaces/alexander-fleming"}
    got = {"wip-a"}
    miss = {w for w in want if not any(covers(g, w) for g in got)}
    chk("`wip-a` 盖住 `wip-a/workspaces/…`（名字不等但路径包含）", not miss)

    print("── ★★ 反向对照 ⑤：**前缀必须按路径段，不许按字符** ──")
    want = {"wip-abc"}
    got = {"wip-a"}
    miss = {w for w in want if not any(covers(g, w) for g in got)}
    chk("`wip-a` **不**盖住 `wip-abc`（否则会假装盖住别人）", miss == {"wip-abc"})

    print("── 反向对照 ⑥：多扫也要报（射程超出名册同样是错） ──")
    want, got = {"wip-a"}, {"wip-a", "wip-x"}
    ext = {g for g in got if not any(covers(g, w) for w in want)}
    chk("实扫里有名册没有的 → 报出来", ext == {"wip-x"})

    # ══════════════════════════════════════════════════════════════
    # ★★★ `scanned()` 本身——**2026-08-12 之前从没被自测进入过**
    # ══════════════════════════════════════════════════════════════
    #
    # 上面全在验 `roster()`（该扫谁）与 `covers()`（覆盖判定），
    # 而 `scanned()`（**实际扫了谁**）一次没被调过。
    # 它做的事是**动态加载 `check_corpus_presence.py` 并调它的 `scan()`**——
    # 那个模块一改签名/一改返回形状，本件就空转，而**自测全绿**。
    #
    # ★ 讽刺之处：本件的职责正是「扫的集合对不对」。
    #   2026-08-12 一天撞到四次「判据扫的集合比实况小」，其中一次就是它报出来的
    #   （该扫 42 实扫 42，**计数对上而集合不同**）。
    #   ⇒ [[a-gates-scan-set-is-smaller-than-reality]]
    print("── ★★★ `scanned()`：真去调 check_corpus_presence.scan() ──")
    _presence = pathlib.Path(__file__).resolve().parent / "check_corpus_presence.py"
    if not _presence.is_file():
        chk("**找不到 check_corpus_presence.py——未核，不是通过**", False)
    else:
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            mk(root, "wip-a", 2)                  # 顶层账本
            mk(root, "wip-b", 3, nested=True)     # evidence/ 下的账本
            got = scanned(root, _presence)
            # ⑨ 两种布局都要被真正扫到——**不是「数得上」，是 scan() 真报出了它们**
            chk("⑨ scanned() 两种布局都取到：{wip-a, wip-b}",
                got == {"wip-a", "wip-b"})
            # ⑨′ ★ 与 roster() 对上——这两个数**必须比集合，不是比计数**
            chk("⑨′ scanned() 与 roster() 集合相等（不是只有个数相等）",
                got == roster(root))
        with tempfile.TemporaryDirectory() as td:
            # ⑨″ 空树：不许崩，也不许报出东西
            got = scanned(pathlib.Path(td), _presence)
            chk("⑨″ 空树 → scanned() 返回空集且不崩", got == set())

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2



def _extreme_note(covered: int, total: int) -> None:
    """**极端值先核工具**（v0.0.0.74）。只提示，不改任何判定。"""
    script = pathlib.Path(__file__).resolve().parent / "check_extreme_result_is_suspect.py"
    if not script.is_file():
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("_pd_extreme", script)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:                                        # noqa: BLE001
        return
    # ★★ **这道判据的成功状态本来就是 100%**——「全中」在它身上不是异常，
    #    否则每次全绿都要报一次，判据就成了噪音。
    #    真正可疑的是**反方向**：一条都没盖住，说明两边的标识符空间压根对不齐
    #    ——第一版就是这么错的（该扫 15／实扫 15，名字一个都不匹配）。
    for name, why in mod.suspect(covered, total):
        if "全体" in name:
            continue
        print(f"⚠ **{name}**\n    {why}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=pathlib.Path, help="语料根（如 _corpora 的上一层）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not a.root:
        ap.error("要么 --self-test，要么给 --root")
    if not a.root.is_dir():
        print(f"✗ **{a.root} 不在——本次未检查（不是通过）**")
        return 3

    checker = pathlib.Path(__file__).resolve().parent / "check_corpus_presence.py"
    if not checker.is_file():
        print("✗ **check_corpus_presence.py 不在——射程无从核起（不是通过）**")
        return 3

    want, got = roster(a.root), scanned(a.root, checker)

    print(f"该扫 **{len(want)}** 个工作区，实际扫了 **{len(got)}** 个\n")
    missing = {w for w in want if not any(covers(g, w) for g in got)}
    extra = {g for g in got if not any(covers(g, w) for w in want)}

    # ★★ v0.0.0.74：极端值先核工具。
    #   **这道判据的输出恰恰最容易在射程错时显得整齐**——
    #   第一版就报过「该扫 15 / 实扫 15，少扫 11 个」，
    #   两个数对得上，名字一个都不匹配。
    _extreme_note(len(want) - len(missing), len(want))
    if not missing and not extra:
        print("  ✓ 射程与名册一致")
        return 0
    if missing:
        print(f"✗ **少扫 {len(missing)} 个——判据即使全绿也盖不住它们**：")
        for m in sorted(missing):
            print(f"    {m}")
    if extra:
        print(f"⚠ 多扫 {len(extra)} 个（名册里没有）：")
        for e in sorted(extra):
            print(f"    {e}")
    print("\n  **一道扫 0 个单位的判据，和一道扫 17 个全过的判据，"
          "在终端上都是一个 ✓。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
