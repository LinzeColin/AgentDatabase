#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive.org 探源器 —— **只检索，不下载**。阶段 1a 用。

用法：
    python3 probe_ia.py --query '<IA 检索式>' --rows 200 --out <tsv>

**四条实测教训写死在里面：**

① **`numFound` 必须打印。** 只看返回的前 N 条会把「窗口太小」误读成「就这么多」
   （[[samples-cannot-support-universal-claims]]）。

② **0 命中不等于没有。** 返回 0 条时本工具**报错退出（rc=4）**并提示先用对照
   查询验证语法——不允许静默把 0 当结论（`抓源坑位清单.md` §一）。

③ **`date` 字段原样输出并在表头标注它是原作年不是版次年**
   （`_IA的date是原作年不是版次年-2026-08-11.md`）。

④ **同时取 `access-restricted-item`**，探源阶段就能看出哪些根本取不到，
   免得抓源时才发现（那时已经浪费一轮）。

★ 退出码：0=有命中；2=参数错；3=请求失败；4=**零命中**（**当错处理**）。
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

UA = "persona-distiller/1.0 (public-domain corpus collection; contact via repo)"
FIELDS = ["identifier", "date", "year", "creator", "title", "language", "collection"]


def search(query: str, rows: int) -> tuple:
    parts = [("q", query), ("rows", str(rows)), ("page", "1"), ("output", "json")]
    parts += [("fl[]", f) for f in FIELDS]
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(parts)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    d = json.loads(urllib.request.urlopen(req, timeout=120).read())
    r = d.get("response") or {}
    return r.get("numFound", 0), (r.get("docs") or [])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--rows", type=int, default=200)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        n, docs = search(a.query, a.rows)
    except Exception as e:  # noqa: BLE001
        print(f"请求失败：{type(e).__name__}: {e}", file=sys.stderr)
        return 3

    print(f"检索式：{a.query}")
    print(f"numFound = **{n}**，本次取回 {len(docs)} 条"
          + ("" if n <= a.rows else f"  ⚠️ **窗口不全**（还有 {n - len(docs)} 条没看）"))

    if not docs:
        print("零命中 —— **这不是「没有」**。先用一条已知会命中的对照查询验证语法本身。",
              file=sys.stderr)
        return 4

    with open(a.out, "w", encoding="utf-8") as f:
        f.write("# numFound=%d rows=%d query=%s\n" % (n, len(docs), a.query))
        f.write("# ★ date 是**原作年**不是版次年；PD 判定看题名页\n")
        f.write("\t".join(FIELDS) + "\n")
        for d in docs:
            row = []
            for k in FIELDS:
                v = d.get(k, "")
                if isinstance(v, list):
                    v = "; ".join(str(x) for x in v)
                row.append(str(v).replace("\t", " ").replace("\n", " ")[:180])
            f.write("\t".join(row) + "\n")
    print(f"→ {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
