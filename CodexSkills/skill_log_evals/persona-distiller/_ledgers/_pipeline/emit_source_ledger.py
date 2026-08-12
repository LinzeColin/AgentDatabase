#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线产物 → `evidence/source-ledger.jsonl`（判据与研究道真正读的那份台账）。

用法：
    python3 emit_source_ledger.py --raw <raw 目录> --workspace <workspaces/<slug> 目录>

输入：`_fetch-manifest.json`＋`_primary.json`＋`_lanes.json`＋`_dedup.json`
输出：`<workspace>/evidence/source-ledger.jsonl`

**四件不能省的：**

① **`derived_from` 由查重簇填。**
   同一部书的 N 个扫描件必须互相指认，否则下游把它们数成 N 处独立证据
   （[[two-source-ids-is-not-two-evidences]]：落成判据后 11 人里 7 人有塌缩、共 57 条）。
   ★ 簇内取**词数最多**的那份当代表，其余 `derived_from` 指向它。

② **`title` 用真题名，不用文件名。**
   存量里 `title` 一直是文件名（`0001-conv-1907-vxxvi.txt`），
   那是已知缺陷（台账「title=文件名」）。**新做的不重蹈。**

③ **`split` 一律先写 `train`，holdout 由人另行指定。**
   holdout 分错比不分更糟——被判过分的产物无法回退
   （[[a-checker-nothing-calls-is-not-a-checker]]：45 份 holdout 里 18 份从未真隔离）。
   本工具**不猜**，并在输出里印一行提醒。

④ **`rights` 写 `pre<PD分界>`（= `pre1931`）并带上依据年份。**
   PD 分界随年份滚动（2026 年是 ≤1930），**不写死**
   （[[pd-cutoff-rolls-every-january]]：曾写死 1929 陈旧两年）。

★ 退出码：0=写出；2=输入缺；3=一条都没写出。
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

THIS_YEAR = 2026
# ★★ 与仓内判据同名同值：`check_filename_year_vs_ledger.py` 写的是
#   `PD_CUTOFF = 1931  # 公有领域 = 出版于 ≤1930，即「1931 年以前」`
#   —— **分界值是 1931，而「可用的最晚出版年」是 1930**。这两个数差 1，
#   我第一版把 rights 印成 `pre1932`、依据写成「≤1931」，**两处都差一年**
#   （[[pd-cutoff-rolls-every-january]] 点名的正是这个坑）。
PD_CUTOFF = THIS_YEAR - 95            # 2026 → 1931（「1931 年以前」）
LATEST_PD_YEAR = PD_CUTOFF - 1        # 2026 → 1930（可用的最晚出版年）


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--workspace", required=True)
    a = ap.parse_args()
    raw, ws = pathlib.Path(a.raw), pathlib.Path(a.workspace)
    need = ["_fetch-manifest.json", "_primary.json", "_lanes.json", "_dedup.json"]
    missing = [n for n in need if not (raw / n).exists()]
    if missing:
        print("缺输入：" + "、".join(missing) + "——先跑完流水线", file=sys.stderr)
        return 2

    mf = json.loads((raw / "_fetch-manifest.json").read_text(encoding="utf-8"))
    prim = {o["identifier"]: o for o in json.loads((raw / "_primary.json").read_text(encoding="utf-8"))["明细"]}
    lanes = {o["identifier"]: o["道"] for o in json.loads((raw / "_lanes.json").read_text(encoding="utf-8"))["明细"]}
    dedup = json.loads((raw / "_dedup.json").read_text(encoding="utf-8"))

    recs = [r for r in mf["记录"] if r["status"] == "已取回"]
    words = {r["identifier"]: r.get("words", 0) for r in recs}

    # ① 簇 → derived_from
    rep, parent = {}, {}
    for cl in dedup.get("重复簇", []):
        head = max(cl, key=lambda i: words.get(i, 0))
        rep[head] = cl
        for i in cl:
            if i != head:
                parent[i] = head

    def sid(ident):
        r = next((x for x in recs if x["identifier"] == ident), None)
        return "src-" + (r["sha256"][:12] if r else ident[:12])

    out, skipped = [], 0
    for r in recs:
        i = r["identifier"]
        lane = lanes.get(i, "")
        if lane == "未分道":
            skipped += 1
            continue
        p = prim.get(i, {})
        is_primary = p.get("档") == "一手"
        ti = r.get("ia_title"); ti = "; ".join(ti) if isinstance(ti, list) else str(ti or "")
        au = r.get("ia_creator"); au = "; ".join(au) if isinstance(au, list) else str(au or "")
        # ★★ 出版年**不取 `min(titlepage_years)`**。
        #   第一版这么取，于是 Bismarck（1815–1898）的书信集被标成
        #   **出版年 1647 / 1761 / 1815** —— 正文前几页里最早那个四位数
        #   往往是**文中提到的年份**（或藏书章、OCR 噪声），不是版次年。
        #   ⇒ 优先用 IA 的编目年（图书馆说的），题名页年份留作**佐证与交叉核对**。
        #   ★ 仍要记住 `ia_date` 可能是原作年不是版次年
        #     （`_IA的date是原作年不是版次年-2026-08-11.md`），所以两者不一致时**印出来**。
        yrs = sorted(int(y) for y in (r.get("titlepage_years") or []) if y.isdigit())
        cat = ""
        for fld in ("ia_date", "ia_year"):
            v = str(r.get(fld, "") or "")
            m = re.search(r"\b(1[5-9]\d{2}|20[0-2]\d)\b", v)
            if m:
                cat = m.group(1)
                break
        if cat:
            pub, basis = cat, "IA 编目年"
        elif yrs:
            pub, basis = str(yrs[-1]), "**题名页年份取最大，未经编目确认**"
        else:
            pub, basis = "", "**取不到**"
        out.append({
            "source_id": sid(i),
            "title": ti or i,                       # ② 真题名，不用文件名
            "author": au,
            "published_at": pub,
            "url": r.get("source_url", ""),
            "locator": f"archive.org item {i}",
            "local_path": f"raw/{i}.txt",
            "original_name": f"{i}.txt",
            "checksum": r.get("sha256", ""),
            "source_type": "document",
            "language": None,
            "dimensions": [lane],
            "tier": "P1" if is_primary else "S1",
            "split": "train",                       # ③ holdout 由人另指
            "attribution": "HIS-OWN" if is_primary else "OTHER",
            "authorship_evidence": ["ia-creator-field"],
            "authorship_detail": {"code": "ia-creator-field",
                                  "evidence": (p.get("依据") or "")[:200]},
            "rights": f"pre{PD_CUTOFF}",            # ④ 随年份滚动；= pre1931
            "published_at_basis": basis,
            "titlepage_years": [str(y) for y in yrs],
            "rights_basis": (f"公有领域 = 出版于 ≤{LATEST_PD_YEAR}"
                             f"（分界 {PD_CUTOFF} = {THIS_YEAR} − 95）；"
                             f"出版年 {pub or '**未取到**'}（{basis}）；"
                             f"题名页年份 {yrs or '无'}"),
            "extraction_status": "raw",
            "normalized_path": None,
            "normalized_checksum": None,
            "abstract": None,
            "redactions": None,
            "derived_from": ([sid(parent[i])] if i in parent else []),
            "accessed_at": r.get("fetched_at", ""),
            "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        })

    if not out:
        print("**一条都没写出** —— 不是「没有源」，是全部落在未分道", file=sys.stderr)
        return 3

    ev = ws / "evidence"; ev.mkdir(parents=True, exist_ok=True)
    (ev / "source-ledger.jsonl").write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in out) + "\n", encoding="utf-8")

    lane_n = len({o["dimensions"][0] for o in out})
    pn = sum(1 for o in out if o["tier"] == "P1")
    dn = sum(1 for o in out if o["derived_from"])
    print(f"→ {ev / 'source-ledger.jsonl'}｜{len(out)} 条"
          + (f"（**未分道跳过 {skipped} 条**）" if skipped else ""))
    print(f"  一手 P1 {pn}｜二手 S1 {len(out) - pn}｜道 {lane_n}"
          f"｜**derived_from 已填 {dn} 条**（{len(rep)} 个重复簇）")
    print(f"  ★ `split` 全部写作 `train` —— **holdout 由人另行指定，本工具不猜**")
    print(f"  ★ `rights` = pre{PD_CUTOFF}（出版年 ≤{LATEST_PD_YEAR}；{THIS_YEAR} − 95，随年份滚动）")
    noc = [o for o in out if "未经编目确认" in o["published_at_basis"]]
    if noc:
        print(f"  ⚠️ **{len(noc)} 条没有编目年**，出版年取自题名页最大值——**这些要人核**")
    odd = [o for o in out if o["published_at"].isdigit() and o["titlepage_years"]
           and int(o["published_at"]) < min(int(y) for y in o["titlepage_years"]) - 60]
    if odd:
        print(f"  ⚠️ 编目年比题名页最早年份还早 60 年以上的 {len(odd)} 条（**原作年 vs 版次年**）："
              + "、".join(f'{o["source_id"]}({o["published_at"]})' for o in odd[:5]))
    late = [o for o in out if o["published_at"].isdigit() and int(o["published_at"]) > LATEST_PD_YEAR]
    if late:
        print(f"  ⚠️ **题名页年份 >{LATEST_PD_YEAR} 的有 {len(late)} 条**，逐条核："
              + "、".join(f'{o["source_id"]}({o["published_at"]})' for o in late[:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
