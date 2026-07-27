#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""冗余体检：同一引文／同一事实在一段里说了两遍。

## 为什么需要它（RUNBOOK 第十七种的落地面）

订正的默认动作是**加**，而订正常常需要的是**换**。
Jesse Vincent #94 里，我把新的说法追加进括号、没删掉原来那句，
结果同一条英文引文在一句话里引了两遍——
**而这正是三位评委都指出过、我自己刚写进 RUNBOOK 的那个模式。**

写进 RUNBOOK 挡不住它，因为落地订正时人是在「改这一处」的模式里，
看不见整段。**必须有一个机器来看整段。**

## 查什么

- 同一段英文引文（≥20 字符投影）出现 ≥2 次
- 同一串数字组合（如「技术 9、纯个人 11」）出现 ≥2 次
- 同一句中文短语（≥12 字）出现 ≥2 次

**只列不判**——有些重复是刻意的（如 rubric 复述要点、分层作答的收束）。
"""
import argparse, collections, pathlib, re, sys

NONWORD = re.compile(r"[^0-9A-Za-z]+")
EN = re.compile(r"[「\"]([A-Za-z][^」\"]{18,300})[」\"]")
CN = re.compile(r"[一-鿿，、]{12,40}")
NUM = re.compile(r"(?:[一-鿿]{2,4}\s*\d+[、，]){2,}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=pathlib.Path)
    ap.add_argument("--extra", nargs="*", default=[], type=pathlib.Path)
    a = ap.parse_args()

    # ★ 元数据文件不进冗余检查：source-ledger 的 title/checksum 字段天然重复，
    #   把它算进来会产生成百上千条误报，把真命中淹没
    #   （Salatin #95：217 处误报全部来自 source-ledger.jsonl）。
    SKIP = {"source-ledger.jsonl", "results.jsonl"}
    files = [f for f in sorted(list(a.workspace.rglob("*.md"))
                               + list(a.workspace.rglob("*.jsonl")) + list(a.extra))
             if f.name not in SKIP]
    total = 0
    for f in files:
        rows = []
        for para in f.read_text(encoding="utf-8", errors="replace").split("\n"):
            if len(para) < 60:
                continue
            for label, rx, norm in (("英文引文", EN, lambda s: NONWORD.sub("", s).lower()),
                                    ("计数串", NUM, lambda s: s.strip()),
                                    ("中文短语", CN, lambda s: s.strip())):
                c = collections.Counter(norm(m if isinstance(m, str) else m)
                                        for m in rx.findall(para))
                for k, n in c.items():
                    if n >= 2 and len(k) >= 12:
                        rows.append((label, n, k[:70]))
        if rows:
            print(f"── {f.name}")
            for label, n, k in rows[:6]:
                print(f"   [{label} ×{n}] {k}")
            total += len(rows)
    print(f"\n{'✓ 无段内重复' if not total else f'⚠ {total} 处段内重复——只列不判，逐条判断是否刻意'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
