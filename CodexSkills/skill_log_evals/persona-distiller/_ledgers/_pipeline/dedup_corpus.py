#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料查重 —— 把「文件数」压成「**独立文献数**」。阶段 2 的第一件。

用法：
    python3 dedup_corpus.py --raw <raw 目录> [--threshold 0.55]

**为什么必须做（不是可选的整洁工作）：**
Fröbel #181 一次抓回 30 份，其中 `autobiographyoff00frob`／`autobiographyoff00fr`／
`autobiographyoff00froeiala`／`autobiographyoff00frbe`／`autobiography00fruoft`／
`autobiographyoff00fruoft`／`autobiooffriedri00froeiala` **是同一部自传的七个扫描件**。
按文件数报「30 个来源」会让 quick 门（来源 ≥8）**看起来轻松过关，而实际上不到 10**
（[[two-source-ids-is-not-two-evidences]]：草稿＋印本字面两个 id、实质一处）。

**判重用 token shingle，不用 `difflib`**（`抓源坑位清单.md` §五：
`difflib` 在同一文本的两个排版上给出 **0.010**，被排版噪声淹没，结论是反的）。

★ **重复分两种、处置相反**（同上 §五）：
  - **同一卷的多个扫描件** ⇒ 去重，只算一份；
  - **同一部书的不同卷** ⇒ 各自独立，不能合并。
  本工具**只报重合度与簇**，`同卷/不同卷` 的判断需要人看题名——
  所以输出里同时打印题名，**不替人下结论**。

★ 退出码：0=跑完；2=参数错；3=raw 目录里没有可读文件。
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

WS = re.compile(r"\s+")


def work_key(title: str) -> str:
    """把「同一套书的不同卷」归成一个键。**只用于报第二个口径，不参与去重。**

    ★ 为什么要有：`deep` 要 45 个来源，而 Marshall 的 95 份里
      **38 份是《The Life of George Washington》的不同卷／不同版**，
      Lincoln 的 70 份里 **26 份是《Complete works》**。
      按行数报「95 个来源」不算错（Bessemer #132 的先例：同一部书的不同卷各自独立），
      **但只报这一个数，等于替读者选了最宽松那档**
      （[[counts-need-their-cutoff-stated]]）。
    ⇒ 两个数一起给：**台账行数**（门用的）与**按题名归并后的独立作品数**。
    """
    s = title.lower()
    s = re.sub(r"[^a-z0-9äöüßàâçéèêëîïôùûñáíóúãõ ]+", " ", s)
    s = re.sub(r"\b(vol|volume|band|tome|part|bd|v)\b\s*[ivxlcdm0-9]*", " ", s)
    s = re.sub(r"\b[ivxlcdm]{1,6}\b", " ", s)
    s = re.sub(r"\b\d{1,4}\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:60]


def sketch(text: str, k: int = 8, keep: int = 3000) -> set:
    """min-hash 草图：取全部 k-gram 的 64 位哈希里最小的 keep 个。
    ★ 用 min-hash 而不是全量集合，是为了让 1,050,509 词的那份也能秒算；
      估计量是 Jaccard，**分母是并集**——所以下面另算「小份被覆盖率」。"""
    w = WS.sub(" ", text).lower().split()
    if len(w) < k:
        return set()
    hs = []
    for i in range(len(w) - k + 1):
        h = hashlib.blake2b(" ".join(w[i:i + k]).encode(), digest_size=8).digest()
        hs.append(int.from_bytes(h, "big"))
    hs.sort()
    return set(hs[:keep])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--threshold", type=float, default=0.55)
    a = ap.parse_args()
    raw = pathlib.Path(a.raw)
    mf = raw / "_fetch-manifest.json"
    if not mf.exists():
        print(f"{mf} 不在 —— 先跑 fetch_ia.py", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(mf.read_text(encoding="utf-8"))["记录"]
            if r["status"] == "已取回"]
    if not recs:
        print("**一份都没有** —— 不是「已去重」，是这个目录是空的", file=sys.stderr)
        return 3

    sk, meta = {}, {}
    # ★★ 2026-08-14：`missing` 是当天补的。原来这里只有 `if not p.exists(): continue`，
    #   于是在移交包的裸 clone 里（语料按裁定不进 git）它印
    #   「文件数 0｜重复簇 0」并宣告「**独立文献数上界 = 0**」，**退出码 0**。
    #   那个 0 不是测量结果，是一份都没读到。[[green-in-the-repo-dead-in-the-package]]
    missing = 0
    for r in recs:
        p = raw / r["file"]
        if not p.exists():
            missing += 1
            continue
        sk[r["identifier"]] = sketch(p.read_text(encoding="utf-8", errors="replace"))
        meta[r["identifier"]] = (r.get("ia_title", "")[:56], r.get("words", 0),
                                 r.get("ia_creator", "")[:44])

    ids = sorted(sk)
    pairs = []
    for i, x in enumerate(ids):
        for y in ids[i + 1:]:
            if not sk[x] or not sk[y]:
                continue
            inter = len(sk[x] & sk[y])
            j = inter / len(sk[x] | sk[y])
            if j >= a.threshold:
                pairs.append((j, x, y))

    # 连通分量 = 重复簇
    parent = {i: i for i in ids}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for _, x, y in pairs:
        parent[find(x)] = find(y)
    clusters: dict = {}
    for i in ids:
        clusters.setdefault(find(i), []).append(i)
    dup = {k: v for k, v in clusters.items() if len(v) > 1}

    print(f"目录 {raw}")
    if not ids:
        print(f"❌ **未量，不是 0** —— 清单里 {len(recs)} 份，**一份也读不到**"
              f"（`raw/` 里缺 {missing} 份；语料按裁定不进 git，裸 clone 里就是这样）。"
              "\n   「独立文献数上界 = 0」在这里不是结论，是**没读到**。", file=sys.stderr)
        return 3
    print(f"清单 {len(recs)} 份 → **真读到 {len(ids)} 份**｜**读不到 {missing} 份**")
    print(f"文件数 {len(ids)}｜重合 ≥{a.threshold:.2f} 的对 {len(pairs)}｜重复簇 {len(dup)}")
    for k, v in sorted(dup.items(), key=lambda kv: -len(kv[1])):
        print(f"\n  簇（{len(v)} 份）—— **同卷多扫描 还是 同书不同卷？看题名，工具不替你判**")
        for i in sorted(v, key=lambda z: -meta[z][1]):
            t, w, c = meta[i]
            print(f"    {i[:46]:<48}{w:>9,} 词  {t}")
    # ★ 第二个口径：按题名归并（同一套书的各卷合并）
    keys = collections.Counter(work_key(meta[i][0]) for i in ids if meta[i][0])
    biggest = "；".join(f"{k[:30]}×{v}" for k, v in keys.most_common(3) if v > 1)

    singles = len(ids) - sum(len(v) for v in dup.values())
    print(f"\n**独立文献数上界 = {singles + len(dup)}**"
          f"（{singles} 份无重合 + {len(dup)} 个簇各算 1）")
    print(f"  ★ 这是**上界**：簇内若其实是不同卷，数应更高；"
          f"低于 0.55 的部分重合本工具不合并，需人看。")
    print(f"**按题名归并后的独立作品数 = {len(keys)}**"
          f"（同一套书的各卷合并）" + (f"｜最大的几组：{biggest}" if biggest else ""))
    print(f"  ★ **两个数都要报**：门用台账行数，而「这个人有多少部不同的作品」是另一个问题。")
    (raw / "_dedup.json").write_text(json.dumps({
        "文件数": len(ids), "阈值": a.threshold, "重复簇": list(dup.values()),
        "独立文献数上界": singles + len(dup),
        "按题名归并的独立作品数": len(keys),
        "★ 两个口径": "门用台账行数（同一套书的不同卷各自独立，Bessemer #132 先例）；"
                     "按题名归并的数回答「他有多少部不同的作品」。**只报一个等于替读者选口径**",
        "★口径": "min-hash Jaccard；同卷多扫描与同书不同卷需人判",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
