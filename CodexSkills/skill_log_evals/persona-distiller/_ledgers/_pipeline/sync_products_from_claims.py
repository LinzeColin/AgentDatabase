#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把产物里的要点正文**从 `evidence/claims.jsonl` 现取**，覆盖手抄的那一份。

## 为什么要有这件工具

十份产物的页脚一直印着这句话：

    ★ 每条要点后的 `<!-- claim:… -->` 指向 `evidence/claims.jsonl`；
    **反证条件**逐条从那里现取，不手抄。

**规则写了，没有任何工具执行它。** 2026-08-13 的后果：
Fröbel #181 有一条断言的次序写反了（说「代价在前、决定在后」，
而原文是决意在前、搏斗在后），我改了 `claims.jsonl`，
**5 份产物 + 1 份研究稿里那句话还是反的**——修了源，派生副本原样留着。

⇒ 本件把「现取」落成命令：改 `claims.jsonl` 之后跑一次，产物就跟上。

## 它改什么、不改什么

**只改**形如 `- <正文> <!-- claim:ID -->` 的行，以及紧随其后的
`  - **反证条件**：…` 子项（取 `falsifiers[0]`）。
**不动**标题、段落、页脚、以及任何没有 claim 标记的行。

★ 找不到对应 claim 的标记会**报出来**（不是静默跳过）——
那说明产物引了一条已删的断言。
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import sys

MARK = re.compile(r"^(- )(.*?)( <!-- claim:(clm-[0-9a-f]+) -->)\s*$")
FALS = re.compile(r"^(\s+- \*\*反证条件\*\*：).*$")
PRODUCTS = ("persona.md", "work.md", "capabilities.md", "cognitive-os.md", "strategy.md",
            "boundaries.md", "facts.md", "voice.md", "playbook.md", "scope.md")


def sync(ws: pathlib.Path, apply: bool) -> int:
    claims = {}
    cp = ws / "evidence" / "claims.jsonl"
    for line in cp.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            claims[r["claim_id"]] = r
    changed = missing = 0
    for name in PRODUCTS:
        f = ws / name
        if not f.exists():
            continue
        lines = f.read_text(encoding="utf-8").splitlines()
        out, i, touched = [], 0, False
        while i < len(lines):
            m = MARK.match(lines[i])
            if not m:
                out.append(lines[i]); i += 1; continue
            cid = m.group(4)
            c = claims.get(cid)
            if not c:
                print("★ %s:%d 引到的 %s 不在 claims.jsonl 里" % (name, i + 1, cid))
                missing += 1
                out.append(lines[i]); i += 1; continue
            new = "%s%s%s" % (m.group(1), c["claim"], m.group(3))
            if new != lines[i]:
                touched = True
            out.append(new); i += 1
            if i < len(lines) and FALS.match(lines[i]):
                fa = (c.get("falsifiers") or [""])[0]
                nf = FALS.match(lines[i]).group(1) + fa
                if nf != lines[i]:
                    touched = True
                out.append(nf); i += 1
        if touched:
            changed += 1
            print("%s %s" % ("改写" if apply else "将改写", name))
            if apply:
                f.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n%s：%d 份产物需要跟上；引到已删断言 %d 处"
          % ("已同步" if apply else "干跑", changed, missing))
    return 1 if missing else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--apply", action="store_true", help="不加就是干跑")
    a = ap.parse_args()
    return sync(pathlib.Path(a.workspace), a.apply)


if __name__ == "__main__":
    sys.exit(main())
