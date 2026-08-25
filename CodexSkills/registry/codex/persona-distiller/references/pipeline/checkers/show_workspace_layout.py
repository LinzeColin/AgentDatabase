#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**同一条流水线产出的工作区，目录深度不一致**——按固定深度写的 glob 会静默漏掉一半。

## 为什么有这件

2026-08-05 实测 `_corpora/` 下十个工作区：

```
workspaces/<人>/references/          → koch, lister, pasteur, mendel      （5 个）
workspaces/<人>/**<人>**/references/ → barton, fleming, nightingale,
                                        osler, virchow                    （5 个）
```

**同名目录多嵌了一层。** 我写引文回扫时 glob 只写了一层，
于是把那五个人报成「**语料目录不在本机 → 未核**」——**假的，语料一直都在。**

★ 更糟的是它制造了一个看起来像数据丢失的假象：
`git ls-files` 数出 735 个 `.txt`、`find` 数出 0 个、而 `git status` 干净。
**我差点去查是不是稀疏检出或者文件被删了。**

## 它做什么

对每个工作区，**找出 `references/` 实际在第几层**，把不一致报出来，
并给出**每个工作区的真实路径**——让调用方直接用，不要再自己拼。

## ★ 为什么叫 `show_` 而不是 `check_`

**它没有生产调用方，而且不该假装有。** 它的用处是「**跨工作区做事之前先问一句路径**」——
真正的使用者是人或代理，不是流水线里的某一步。
本项目要求每个 `check_*.py` 在生产代码里都有调用方（`check_checkers.py` 会验），
**与其硬接一个假的调用点，不如老实归到 `show_*`**——和 `show_gate.py` 一类：
**「别再手搓了，用这个读」。**

## ★ 它不做什么

- **不搬目录。** 那些工作区被台账、延后名单、FINDING 用路径引着，
  搬一次要同步改一堆记录，**是不是该搬由人定**。
- **不判哪种深度是对的。** 只判**它们不一致**，以及**具体各是哪种**。
"""
import argparse
import collections
import json
import pathlib
import sys


def find_refs(ws: pathlib.Path, max_depth: int = 3) -> pathlib.Path:
    """在 ws 下最多下探 max_depth 层找 references/。找不到返回 None。"""
    cur = [ws]
    for _ in range(max_depth):
        nxt = []
        for d in cur:
            if not d.is_dir():
                continue
            cand = d / "references"
            if cand.is_dir():
                return cand
            nxt.extend(x for x in d.iterdir() if x.is_dir())
        cur = nxt
    return None


def scan(corpora: pathlib.Path) -> dict:
    if not corpora.is_dir():
        return {"状态": f"**未核（不是通过）**：{corpora} 不是目录"}
    rows, shapes = [], collections.Counter()
    for wip in sorted(corpora.glob("wip-*")):
        wsdir = wip / "workspaces"
        if not wsdir.is_dir():
            rows.append({"人物": wip.name, "形状": "**无 workspaces 目录**", "references": None})
            shapes["无 workspaces"] += 1
            continue
        for ws in sorted(d for d in wsdir.iterdir() if d.is_dir()):
            refs = find_refs(ws)
            if refs is None:
                rows.append({"人物": wip.name, "形状": "**无 references**", "references": None})
                shapes["无 references"] += 1
                continue
            depth = len(refs.relative_to(ws).parts) - 1     # 0 = ws/references
            shape = f"workspaces/<人>{'/<人>' * depth}/references"
            shapes[shape] += 1
            rows.append({"人物": wip.name, "形状": shape,
                         "references": str(refs),
                         "txt 份数": len(list(refs.rglob("*.txt")))})
    real = {k: v for k, v in shapes.items() if k.startswith("workspaces/")}
    out = {"工作区数": len(rows), "**不同的形状数**": len(real),
           "各形状计数": dict(shapes), "逐个": rows}
    if len(real) > 1:
        out["⚠⚠ 结论"] = ("**目录深度不一致**——按固定深度写的 glob 会静默漏掉一部分，"
                          "且漏掉时看起来像「语料不在本机」。**请用本件给出的 references 路径。**")
    else:
        out["✓ 结论"] = "深度一致"
    out["★ 口径"] = "**只报不搬**；不判哪种深度对，只判它们一不一致。"
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    import tempfile
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)

        def mk(person, nested, with_refs=True):
            base = root / f"wip-{person}" / "workspaces" / person
            if nested:
                base = base / person
            if with_refs:
                (base / "references" / "sources").mkdir(parents=True)
                (base / "references" / "sources" / "a.txt").write_text("x", encoding="utf-8")
            else:
                base.mkdir(parents=True)

        print("── ★★★ 反向对照①：**一浅一深 → 必须报「不一致」** ──")
        mk("koch", False); mk("barton", True)
        r = scan(root)
        chk(f"形状数 {r['**不同的形状数**']}", r["**不同的形状数**"] == 2)
        chk("给出「会静默漏掉」的警告", "静默漏掉" in str(r.get("⚠⚠ 结论", "")))

        print("── ★★ 反向对照②：**深一层的那个也要找到 references，不许报缺失** ──")
        bar = [x for x in r["逐个"] if x["人物"] == "wip-barton"][0]
        chk(f"barton references = …{bar['references'][-40:]}", bar["references"] is not None)
        chk(f"并数到了 txt {bar.get('txt 份数')}", bar.get("txt 份数") == 1)

        print("── ★★ 反向对照③：**全都一样深 → 说「一致」，不许误报** ──")
        with tempfile.TemporaryDirectory() as t2:
            r2root = pathlib.Path(t2)
            for p in ("a", "b"):
                d = r2root / f"wip-{p}" / "workspaces" / p / "references"
                d.mkdir(parents=True)
            r2 = scan(r2root)
            chk(f"形状数 {r2['**不同的形状数**']}，结论：{r2.get('✓ 结论')}",
                r2["**不同的形状数**"] == 1 and "一致" in str(r2.get("✓ 结论", "")))

        print("── ★★ 反向对照④：**根本没有 references 的，单列，不混进形状统计** ──")
        mk("jenner", False, with_refs=False)
        r3 = scan(root)
        j = [x for x in r3["逐个"] if x["人物"] == "wip-jenner"][0]
        chk(f"jenner → {j['形状']}", "无 references" in j["形状"])
        chk("它不计入形状数", r3["**不同的形状数**"] == 2)

        print("── ★ 反向对照⑤：目录不存在 → 说「未核」，不说「通过」 ──")
        chk("未核", "未核" in str(scan(root / "nope").get("状态", "")))
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpora", nargs="?", help="_corpora 目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.corpora:
        ap.error("要么 --self-test，要么给 _corpora 路径")
    print(json.dumps(scan(pathlib.Path(a.corpora)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
