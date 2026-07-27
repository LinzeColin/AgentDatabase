#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**提议**时效字段的候选值供作者核对——本脚本不自动写入。

## 为什么改成「只提议、不写入」

初版试图从产物自由文本里推导 subject_status，**连续两次给出错误结果**：
  - 用 time_scope 结束年判定 → 把 1996 年去世的 David Packard 标成 living；
  - 改用卒年正则 → John Bogle 判定已故正确，但卒年抓成 1951（实为 2019）。

**两次失败指向同一个结论：这个字段不该由启发式推导。**
而且它与本次要修的原始缺陷同源——**把一个字段当成它不表示的东西用**
（`time_scope` 是证据覆盖范围，不是生卒；`research_cutoff` 是研究日期，不是活跃度）。

**因此改为架构层修复**：`subject_status` 与 `subject_active_through`
成为**蒸馏时必须由作者显式填写**的字段（见 persona-distiller 的 release 硬门），
本脚本只做两件事：
  1. 扫描全库，报告哪些人物尚未填写（status = unauthored）；
  2. 对单个人物给出**候选值与依据**，供作者核对后手工确认——**绝不自动写入**。


## 这个脚本存在的理由

v0.0.0.6 的 `route_team.py::freshness_score()` 读的是 `research_cutoff`：

    research_cutoff 年份分布: {'2026': 86, '1976': 1, '2004': 1, '2013': 1, '2002': 1, '2011': 1}

**那是「做研究的日期」，不是人物的活跃度。** 86/91 完全相同，分数形同虚设。
更糟的是那 5 个例外——1976／2002／2004／2011／2013 是**卒年被误填成了研究日期**，
于是**唯一存在的时效信号在反向工作**：真正该被标注为已故的人，反而因为填了卒年而拿到更低分。

同时全库**没有任何字段表示在世／仍活跃**，因此无法回答
「这个团队能不能谈当前实践」这类问题。

## 本脚本写入的字段

- `subject_status`         : living | deceased | unknown
- `subject_active_through` : 其可核公开产出的最后年份（已故＝卒年；在世＝语料中最新一手年份）
- `evidence_recency`       : 该产物源账本中最新一手来源的年份
- `research_cutoff`        : 统一修正为「做研究的日期」，不再混入卒年

判定依据取自各产物 meta.json 的 `time_scope`（形如 1929-2019 / 1949-2026），
以及源账本中 `tier` 为 P1／P2 的最新 `published_at`。**不猜测，取不到就写 unknown。**
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Any


def registry_root() -> Path:
    return Path(__file__).resolve().parents[1]


def open_runtime(path: Path) -> zipfile.ZipFile:
    outer = zipfile.ZipFile(path)
    inner = next((n for n in outer.namelist() if "/runtime/" in n and n.endswith(".zip")), None)
    return zipfile.ZipFile(io.BytesIO(outer.read(inner))) if inner else outer


def probe(slug: str) -> dict[str, Any]:
    """从产物中读出时效事实。取不到就如实返回 unknown，不推断。"""
    hits = sorted(registry_root().glob(f"*/{slug}/versions/*/*.zip"))
    if not hits:
        return {"subject_status": "unknown", "reason": "no delivery zip"}
    this_year = date.today().year
    try:
        with open_runtime(hits[-1]) as zf:
            names = zf.namelist()
            scope = None
            meta = next((n for n in names if n.endswith("meta.json")), None)
            if meta:
                m = json.loads(zf.read(meta).decode("utf-8"))
                scope = m.get("time_scope") or (m.get("target") or {}).get("time_scope")

            recency = None
            led = next((n for n in names if n.endswith("evidence/source-ledger.jsonl")), None)
            if led:
                years: list[int] = []
                for line in zf.read(led).decode("utf-8").splitlines():
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    if r.get("tier") not in ("P1", "P2"):
                        continue
                    mm = re.match(r"^(\d{4})", str(r.get("published_at") or ""))
                    if mm:
                        years.append(int(mm.group(1)))
                if years:
                    recency = max(years)

            end = None
            if scope:
                # 覆盖三种实际存在的写法：
                #   1929-2019 / 1949–2026 / 1960-11-01 through 2026-07-24
                # 取字符串中出现的最后一个四位年份作为结束年。
                years_in_scope = re.findall(r"(1[6-9]\d{2}|20\d{2})", str(scope))
                if len(years_in_scope) >= 2:
                    end = int(years_in_scope[-1])

            # ⚠️ time_scope 表示「证据覆盖的时间范围」，**不是人物生卒**。
            # 初版误用它判定在世，把 1996 年去世的 David Packard 标成了 living——
            # 这与本次要修的缺陷是同一类错误：把字段当成它不表示的东西用。
            # 因此改为**只认明确的死亡证据**，其余一律 unknown，不推断。
            death_year = None
            for cand in ("facts.md", "meta.json", "team-card.json"):
                nm = next((n for n in names if n.endswith(cand)), None)
                if not nm:
                    continue
                blob = zf.read(nm).decode("utf-8", "replace")
                dm = re.search(
                    r"(?:卒于|逝世于|逝世|去世于|去世|d\.\s*|died\s+(?:in\s+)?)[^0-9]{0,12}((?:1[6-9]|20)\d{2})",
                    blob)
                if not dm:
                    dm = re.search(r"\b((?:1[6-9]|20)\d{2})\s*[-–]\s*((?:1[6-9]|20)\d{2})\b(?=[^0-9]{0,30}(?:生|卒|逝))", blob)
                    if dm:
                        dm = re.match(r".*?((?:1[6-9]|20)\d{2})$", dm.group(2)) or None
                if dm:
                    y = int(dm.group(1))
                    if 1600 <= y <= this_year:
                        death_year = y
                        break

            if death_year:
                return {"subject_status": "deceased", "subject_active_through": death_year,
                        "evidence_recency": recency, "time_scope": scope,
                        "basis": "产物中检出明确的卒年表述"}
            # 无死亡证据 + 一手证据延伸到近两年 → 判定在世（可核）
            if recency and recency >= this_year - 1:
                return {"subject_status": "living", "subject_active_through": recency,
                        "evidence_recency": recency, "time_scope": scope,
                        "basis": "无卒年表述，且存在近两年的一手来源"}
            return {"subject_status": "unknown", "evidence_recency": recency,
                    "time_scope": scope,
                    "reason": "无明确卒年表述，且一手证据不足以支持在世判定"}
    except Exception as exc:  # noqa: BLE001 - 读不出就如实报，不静默
        return {"subject_status": "unknown", "reason": f"read error: {exc}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--propose", metavar="SLUG", help="为单个人物提议候选值（仅输出，不写入）")
    ap.add_argument("--research-date", default=date.today().isoformat(),
                    help="统一写入的 research_cutoff（做研究的日期，非卒年）")
    args = ap.parse_args()

    idx_path = registry_root() / "team-index.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    products = idx.get("products", [])

    stats = {"living": 0, "deceased": 0, "unknown": 0, "cutoff_fixed": 0}
    unknown_names: list[str] = []
    for p in products:
        info = probe(p["subject_slug"])
        st = info.get("subject_status", "unknown")
        stats[st] = stats.get(st, 0) + 1
        if st == "unknown":
            unknown_names.append(p.get("canonical_name", p["subject_slug"]))
        old_cutoff = str(p.get("research_cutoff") or "")
        if not old_cutoff.startswith(str(date.today().year)[:2]) or len(old_cutoff) < 8:
            stats["cutoff_fixed"] += 1
        if False:  # 本脚本不再自动写入，见文件头说明
            p["subject_status"] = st
            if info.get("subject_active_through"):
                p["subject_active_through"] = info["subject_active_through"]
            if info.get("evidence_recency"):
                p["evidence_recency"] = info["evidence_recency"]
            p["research_cutoff"] = args.research_date

    report = {
        "total": len(products),
        **stats,
        "living_ratio": round(stats["living"] / max(1, len(products)), 3),
        "unknown_sample": unknown_names[:8],
        "applied": False,
        "policy": "本脚本只报告与提议，不写入；subject_status 须在蒸馏时由作者填写。",
        "note": ("research_cutoff 统一改写为做研究的日期；此前有 %d 条混入了卒年，"
                 "导致 freshness 信号反向工作。" % stats["cutoff_fixed"]),
    }
    if False:
        idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
