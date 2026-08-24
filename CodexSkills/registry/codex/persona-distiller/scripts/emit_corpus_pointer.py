#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料指针清单 —— 语料移出仓之后，**仓里留下的就只有这一份**。

## 为什么有这件

2026-08-11 移交 GitHub 时量出来：本分支相对 `origin/main` 新增 **2742.6 MB**，
其中 **2711.6 MB 是语料**，产物 + 账本 + 判据 + 交接文档合起来只有 30.6 MB。
而 `origin/main` 上 8-10 新加的 pre-push 钩子上限是 **200 MB**，
它的注释里点名的就是这个分支。

决定：**语料另存，仓里只放指针。**

## ★★ 先量清楚「丢了能不能捞回来」，再决定指针要写多细

2071 行台账逐行分类（**这是实测，不是估计**）：

    ① 有 URL                    1993   73.5%
    ② 有档案条目号（可再取）        134    4.9%
    ③ 只有文字性 locator           507   18.7%
    ④ **什么坐标都没有**             79    2.9%

**① + ② = 78.4%，这是「丢了还能捞回来」的上界。**
剩下 21.6% 凭元数据取不回来——所以这份清单的职责**不只是**「怎么重抓」，
更是「**拿到别处存的那份之后，怎么证明它就是原来那份**」。

★★★ **上面这组数我先报错过一次，错法比数本身重要。**
第一版 `build()` 写的是 `glob("wip-*/workspaces/*/evidence/source-ledger.jsonl")`，
**漏了 10 份台账**（全库台账落在三种深度：5 段 27 份、6 段 6 份、2 段 4 份）。
于是我报出：

    工作区 24（真值 34）　台账 952 行（真值 2071）
    ① 有 URL 43.5%（真值 73.5%）　①+② 57.6%（真值 78.4%）
    ④ 什么坐标都没有 8.3%（真值 2.9%）

**而且这些错数我已经报给用户了**，还据此说过「1323.8 MB 的 raw/ 没有任何台账行」——
那 1323.8 MB 里绝大部分是**我自己没找到台账**，不是它们真的没登记。
★ 教训与 [[gates-cover-json-not-the-prose-users-read]] 同族：
**先猜路径形状、再去 glob，就会把「我没找到」报成「它不存在」。**
现在改用 `rglob`，不猜深度。

★ 另一处已改正的错话：我一度在给用户的选项里写「台账里有每份的 URL，需要时按台账重抓」，
当时只看了 `url` 字段（2.6%）——**而 73.5% 的链接藏在 `locator` 里**。
两次都是同一个毛病：**只看一个字段、只扫一种路径，就下全称结论。**

## 清单里放什么

每个工作区一条，逐份文件记：

- `source_id` / `local_path` / `original_name`
- `checksum`（台账里 **100% 齐**）与 `normalized_checksum`
- `bytes`（现算，不抄台账）
- `refetch`：`url` / `item` / `prose` / `none` —— 上面那四类
- 以及该行原本的 `locator`（有什么记什么，不美化）

**不写「怎么下载」**——那要 URL，而 URL 只有 43.5% 有。
**只写「怎么验」**——checksum 是齐的，验得了。

用法：

    python3 emit_corpus_pointer.py --corpora <_corpora 根> --out <清单.json>
    python3 emit_corpus_pointer.py --verify <清单.json> --corpora <_corpora 根>
    python3 emit_corpus_pointer.py --self-test

退出码：0=成功　1=校验有出入　2=自测未过
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

URL = re.compile(r"https?://[^\s\"')]+")
ITEM = re.compile(r"\bitem\s+[\w.\-]{6,}|\bark:/|\bdoi:|10\.\d{4,}/|hdl\.handle|\bMS\s?\d+|\bcatalog(?:ue)?\s+no")


def refetch_class(row: dict) -> str:
    """这一份**丢了能不能捞回来**。四档，按可操作性从强到弱。

    ★ 判据看的是**整行**里有没有 URL（`url` 字段只覆盖 2.6%，
      而 `locator` 里藏着 373 行的链接），不是只看 `url` 字段。
      只看一个字段会把 43.5% 报成 2.6%。
    """
    blob = json.dumps(row, ensure_ascii=False)
    loc = str(row.get("locator") or "")
    if URL.search(blob):
        return "url"
    if ITEM.search(loc):
        return "item"
    if loc.strip():
        return "prose"
    return "none"


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_ledgers(corpora: pathlib.Path) -> list:
    """找**全部** `source-ledger.jsonl`，不猜深度。

    ★★ 2026-08-11：第一版写的是 `glob("wip-*/workspaces/*/evidence/...")`，
    **漏了 10 份台账**。实测全库台账落在三种深度上：

        相对 _corpora 的路径段数 → 份数：{5: 27, 6: 6, 2: 4}

    5 段是常规布局；**6 段是那 6 个「路径重了一层」的工作区**
    （`workspaces/<slug>/<slug>/`，HANDOFF 里专门记过）；
    2 段是直接落在 `wip-X/` 根下的。
    漏掉后果不是少几行——**1323.8 MB 的 raw/ 会被判成「台账没登记」**。
    """
    return sorted(corpora.rglob("source-ledger.jsonl"))


def build(corpora: pathlib.Path) -> dict:
    out = {"schema": "corpus-pointer/1", "workspaces": {}}
    tally = collections.Counter()
    for led in find_ledgers(corpora):
        ws_dir = led.parent.parent          # <ws>/evidence/source-ledger.jsonl → <ws>
        # ★ 键用**相对 _corpora 的路径**，不用目录名：
        #   双层嵌套的两级同名（clara-barton/clara-barton），只用名字会互相覆盖。
        ws = str(ws_dir.relative_to(corpora))
        items = []
        for line in led.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            lp = str(r.get("local_path") or "")
            f = (ws_dir / lp) if lp else None
            size = f.stat().st_size if (f and f.is_file()) else None
            cls = refetch_class(r)
            tally[cls] += 1
            items.append({
                "source_id": r.get("source_id"),
                "local_path": lp,
                "original_name": r.get("original_name"),
                "checksum": r.get("checksum"),
                "normalized_checksum": r.get("normalized_checksum"),
                "bytes": size,                       # ★ 现算，不抄台账
                "present": bool(size is not None),
                "split": r.get("split"),
                "tier": r.get("tier"),
                "refetch": cls,
                "locator": r.get("locator"),
            })
        out["workspaces"][ws] = {
            "ledger_rows": len(items),
            "present": sum(1 for i in items if i["present"]),
            "bytes_present": sum(i["bytes"] or 0 for i in items),
            "items": items,
        }
    out["tally_refetch"] = dict(tally)
    out["totals"] = {
        "workspaces": len(out["workspaces"]),
        "rows": sum(w["ledger_rows"] for w in out["workspaces"].values()),
        "present": sum(w["present"] for w in out["workspaces"].values()),
        "bytes_present": sum(w["bytes_present"] for w in out["workspaces"].values()),
    }
    return out


def verify(manifest: dict, corpora: pathlib.Path) -> int:
    """拿清单去核一棵语料树。**只报事实，不修任何东西。**"""
    miss = bad = ok = noc = 0
    problems = []
    for ws, w in manifest["workspaces"].items():
        base = corpora / ws           # ★ ws 现在就是相对 _corpora 的路径，不必再 glob
        if not base.is_dir():
            base = None
        if base is None:
            miss += w["ledger_rows"]
            problems.append((ws, "整个工作区不在", ""))
            continue
        for it in w["items"]:
            p = base / (it["local_path"] or "")
            if not it["local_path"] or not p.is_file():
                miss += 1
                problems.append((ws, "文件不在", it["local_path"] or "(无 local_path)"))
                continue
            want = it.get("checksum")
            if not want:
                noc += 1
                continue
            got = sha256_of(p)
            if got == want:
                ok += 1
            else:
                bad += 1
                problems.append((ws, "校验和对不上", f"{it['local_path']} 期望 {want[:12]} 实得 {got[:12]}"))
    print(f"核过 {ok + bad + miss + noc} 份：**校验通过 {ok}**，"
          f"校验和对不上 {bad}，文件不在 {miss}，台账无校验和 {noc}")
    for ws, kind, det in problems[:25]:
        print(f"  ⚠ {ws}　{kind}　{det}")
    if len(problems) > 25:
        print(f"  …另有 {len(problems) - 25} 条")
    if bad or miss:
        print("\n  ✗ **这棵语料树与清单不一致**——别拿它当原件用")
        return 1
    if not ok:
        print("\n  ⚠ **一份都没校验成功——本次未检查（不是通过）**")
        return 1
    print("\n  ✓ 清单里的每一份都在，且校验和逐份对上")
    return 0


def self_test() -> int:
    n = [0]
    fail = 0

    def note(label, ok):
        n[0] += 1
        print(f"  {'✓' if ok else '✗'} {label}")

    print("══ 负对照 ══")
    # ① 四档分类：URL 藏在 locator 里也要认出来（只看 url 字段会把 43.5% 报成 2.6%）
    ok1 = refetch_class({"locator": "见 https://archive.org/details/foo"}) == "url"
    note("`locator` 里的链接算「有 URL」（不是只看 `url` 字段）", ok1)
    fail += not ok1

    ok1b = refetch_class({"url": "https://x/y"}) == "url"
    note("`url` 字段照样算", ok1b)
    fail += not ok1b

    ok2 = refetch_class({"locator": "item transactions-american-institute_1907_26, file p12"}) == "item"
    note("档案条目号算「可再取」", ok2)
    fail += not ok2

    ok3 = refetch_class({"locator": "第 12 卷第 3 章，题名页"}) == "prose"
    note("只有文字性 locator → prose", ok3)
    fail += not ok3

    # ★ **反对照**：什么都没有必须落到 none，不许被前三档顺手接走。
    ok4 = refetch_class({"locator": "", "source_id": "src-1"}) == "none"
    note("**反对照**：坐标为空 → none（不许静默升档）", ok4)
    fail += not ok4

    ok4b = refetch_class({"locator": None}) == "none"
    note("**反对照**：locator 是 null 也算 none", ok4b)
    fail += not ok4b

    # ② 校验：真改坏一个字节，必须报出来
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        ws = root / "wip-t-1" / "workspaces" / "tester"
        (ws / "raw" / "src-a").mkdir(parents=True)
        f = ws / "raw" / "src-a" / "x.txt"
        f.write_text("hello corpus", encoding="utf-8")
        (ws / "evidence").mkdir()
        row = {"source_id": "src-a", "local_path": "raw/src-a/x.txt",
               "original_name": "x.txt", "checksum": sha256_of(f),
               "locator": "https://example.org/x"}
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

        m = build(root)
        ok5 = m["totals"]["rows"] == 1 and m["totals"]["present"] == 1
        note("build 扫到 1 份且标为存在", ok5)
        fail += not ok5

        ok5b = verify(m, root) == 0
        note("**反对照**：没动过的树 → 校验通过（不是凡树皆红）", ok5b)
        fail += not ok5b

        f.write_text("hello corpuz", encoding="utf-8")     # 改一个字节
        ok6 = verify(m, root) == 1
        note("改一个字节 → 校验报错（退出 1）", ok6)
        fail += not ok6

        f.unlink()
        ok7 = verify(m, root) == 1
        note("文件删掉 → 报「文件不在」（退出 1）", ok7)
        fail += not ok7

    print(f"\n  ✓ 自测通过（{n[0]}/{n[0]}）" if not fail
          else f"\n  ✗ {fail}/{n[0]} 项未过——本件的输出不作数")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", type=pathlib.Path, help="_corpora 根目录")
    ap.add_argument("--out", type=pathlib.Path, help="清单落盘路径")
    ap.add_argument("--verify", type=pathlib.Path, help="拿这份清单去核 --corpora 那棵树")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return 2 if self_test() else 0
    if not a.corpora:
        ap.error("须给 --corpora")

    if a.verify:
        return verify(json.loads(a.verify.read_text(encoding="utf-8")), a.corpora)

    m = build(a.corpora)
    t = m["totals"]
    print(f"工作区 {t['workspaces']} 个，台账 {t['rows']} 行，"
          f"文件在位 {t['present']} 份，合计 {t['bytes_present'] / 1048576:.1f} MB")
    tal = m["tally_refetch"]
    tot = sum(tal.values()) or 1
    print("「丢了能不能捞回来」：")
    for k, label in (("url", "① 有 URL"), ("item", "② 有档案条目号"),
                     ("prose", "③ 只有文字性 locator"), ("none", "④ **什么坐标都没有**")):
        v = tal.get(k, 0)
        print(f"   {label:<24} {v:4d}  {100 * v / tot:5.1f}%")
    up = (tal.get("url", 0) + tal.get("item", 0)) / tot
    print(f"   ★ ①+② = {100 * up:.1f}% —— **这是能捞回来的上界，不是保证**")
    if a.out:
        a.out.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  ✓ 已写 {a.out}（{a.out.stat().st_size / 1048576:.1f} MB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
