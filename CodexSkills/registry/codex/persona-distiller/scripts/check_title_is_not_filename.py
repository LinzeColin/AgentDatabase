#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**台账的 `title` 是真书目题名，还是文件名的副本？**

## 撞出它的那一次

2026-08-10 清 Jenner 的 13 对未声明重复源。8 词片重叠 0.47–0.60，
两种解释结论相反（同一篇的两份扫描／合集只收了一半）。
我发明了一条判据去分辨，**声明了 13 对、提交、还写了记忆**，
然后做负对照——**当场被打掉**（确定不同的两份公报表现与正例几乎一样）。

撤回的时候才想到去看第二个证据源：**台账里这几份的题名是什么。**

```
inquiryintocause00jenn.txt   published_at 1800   title: inquiryintocause00jenn.txt
b21354273.txt                published_at 1799   title: b21354273.txt
```

**`title` 就是文件名。** 于是「这两份是不是同一部作品」除了内容重叠**没有第二个证据源**，
那 13 对不是「换个判据就能过」，是**证据本身不在手上**。

## 全库实测（2026-08-10）

| | 行数 | 占比 |
|---|---:|---:|
| `title` **就是文件名** | **1,941** | **99%** |
| `title` 是真书目题名 | 28 | 1% |
| `title` 为空 | 0 | — |

**这不是「有几处漏了」，是这个字段从来没有承载过信息。**

## 为什么它比「未声明重复对」更要紧

`title` 看起来是数据，下游一律当数据用：
- 判「同一部作品」时没有书目侧的证据可交叉验证；
- 引文坐标、`check_quote_attributed_source` 的「挂到哪部作品」全落在文件名上；
- 人读交付物时，看到的「来源题名」是 `b21354273.txt` 这种东西。

★ 与 [[empty-default-swallows-unknown]] 反过来：**空值至少诚实**，
而**填成文件名的字段，看起来是填过的**。

## 判据

对每一条 usable 的台账行：`title` 若等于 `local_path` 的文件名（或去掉扩展名后相等），
判为**没有题名**。**报出比例与条数，不拦。**

★ **为什么只报不拦**：99% 的行是这样，做成硬门会让每个工作区当场全红，
而这不是某一次操作的错，是历史累积。**拦不解决问题，只会让人去关门。**
把数字打出来，让它每次跑都被看见。

退出码：0 = 全部有真题名；1 = 有文件名当题名的行（**报告用，调用方按警告处理**）；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def analyse(rows: list) -> dict:
    same, real, empty, examples = 0, 0, 0, []
    for r in rows:
        t = (r.get("title") or "").strip()
        n = pathlib.PurePath(r.get("local_path") or "").name
        stem = pathlib.PurePath(n).stem
        if not t:
            empty += 1
        elif t == n or t == stem:
            same += 1
            if len(examples) < 5:
                examples.append({"source_id": r.get("source_id"), "title": t,
                                 "published_at": r.get("published_at")})
        else:
            real += 1
    tot = same + real + empty
    return {
        "台账行数": tot,
        "**`title` 就是文件名**": same,
        "`title` 是真书目题名": real,
        "`title` 为空": empty,
        "比例": round(same / tot, 4) if tot else 0.0,
        "抽样": examples,
        "口径": ("`title` 等于 `local_path` 的文件名（或去掉扩展名后相等）即判「没有题名」。"
                 "**只报不拦**——全库 99% 如此，做成硬门只会让人去关门。"),
    }


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：title 等于文件名 → 必须报出 ──")
    a = analyse([{"source_id": "s1", "local_path": "raw/x/b21354273.txt",
                  "title": "b21354273.txt"}])
    chk(f"报 1 条（实报 {a['**`title` 就是文件名**']}）", a["**`title` 就是文件名**"] == 1)

    print("── 正向：title 等于**去掉扩展名的**文件名 → 也必须报出 ──")
    a2 = analyse([{"source_id": "s2", "local_path": "raw/x/b21354273.txt",
                   "title": "b21354273"}])
    chk(f"报 1 条（实报 {a2['**`title` 就是文件名**']}）", a2["**`title` 就是文件名**"] == 1)

    print("── 反向对照 ①：真书目题名 → 不许报 ──")
    a3 = analyse([{"source_id": "s3", "local_path": "raw/x/b21354273.txt",
                   "title": "An Inquiry into the Causes and Effects of the Variolae Vaccinae"}])
    chk(f"不报（实报 {a3['**`title` 就是文件名**']}），且计入「真题名」",
        a3["**`title` 就是文件名**"] == 0 and a3["`title` 是真书目题名"] == 1)

    print("── 反向对照 ②：**空题名不算「文件名当题名」**，单独计 ──")
    #   空值至少诚实；把它并进来会掩盖两类完全不同的缺失。
    a4 = analyse([{"source_id": "s4", "local_path": "raw/x/y.txt", "title": ""}])
    chk(f"计入「为空」而不是「就是文件名」",
        a4["`title` 为空"] == 1 and a4["**`title` 就是文件名**"] == 0)

    print("── ★★ 反向对照 ③：**题名里恰好含文件名**但不相等 → 不许报 ──")
    a5 = analyse([{"source_id": "s5", "local_path": "raw/x/notes.txt",
                   "title": "notes.txt 的扫描件：Notes on Nursing, 1860"}])
    chk("不报（是包含不是相等）", a5["**`title` 就是文件名**"] == 0)

    print("── 反向对照 ④：`local_path` 缺失时不许把任意 title 判成文件名 ──")
    a6 = analyse([{"source_id": "s6", "title": "Some Real Title"}])
    chk("计入「真题名」", a6["`title` 是真书目题名"] == 1 and a6["**`title` 就是文件名**"] == 0)

    print("── ★ 空台账：比例必须是 0，不许除零炸 ──")
    a7 = analyse([])
    chk(f"比例 {a7['比例']}，行数 {a7['台账行数']}", a7["比例"] == 0.0 and a7["台账行数"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 --workspace")

    led = a.workspace / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        print(f"✗ **{led} 不在——未核验（不是通过）**")
        return 3
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    info = analyse(rows)
    if a.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        for k, v in info.items():
            if k == "抽样":
                continue
            print(f"  {k}: {v}")
        if info["抽样"]:
            print("  抽样：")
            for e in info["抽样"]:
                print(f"     {e['source_id']}  title={e['title']}  published_at={e['published_at']}")
    return 1 if info["**`title` 就是文件名**"] else 0


if __name__ == "__main__":
    sys.exit(main())
