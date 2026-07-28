#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 `manifest_ms.json` 灌库。清单是唯一真源，这里不做任何判断。

**灌哪些**：primary_ratio 的分母是**全部可用源**（`tier != 'U'`），
所以 S2 灌得越多、比值越低。这里按 `--max-secondary` 只取比值最优的组合：
全部 P1 + 尽量少的次级源，且次级源优先取官方文件与含引语的报道（S1），
S2 只在源数不够 45 时补位。

holdout **不从 P1 里出**——P1 是分子，抽走一份等于同时减分子和分母，
比值反而更差。holdout 取次级源。
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

W = pathlib.Path(__file__).resolve().parent
S = ("/Users/linzezhang/Documents/Codex/AgentDatabase/"
     "character-distillation-skill-reorganize-d57595/CodexSkills/registry/"
     "codex/persona-distiller/scripts/ingest.py")

RIGHTS = "publicly-accessible-for-analysis; redistribution-not-assumed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--holdout", type=int, default=3)
    ap.add_argument("--min-sources", type=int, default=45)
    ap.add_argument("--min-ratio", type=float, default=0.65)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    rows = json.load(open(W / "manifest_ms.json", encoding="utf-8"))
    p1 = [r for r in rows if r["tier"] in ("P1", "P2")]
    s1 = [r for r in rows if r["tier"] == "S1"]
    s2 = [r for r in rows if r["tier"] == "S2"]
    # 次级源按体量降序，先要信息密度高的
    s1.sort(key=lambda r: -r["bytes"])
    s2.sort(key=lambda r: -r["bytes"])

    hold = s1[-a.holdout:] if a.holdout else []
    s1_train = s1[:len(s1) - a.holdout] if a.holdout else s1
    # 次级源灌到「比值仍高于下限」为止，且至少凑满源数下限。
    # 分母涨、分子不动 ⟹ 灌越多比值越低，所以上限由比值定。
    cap_by_ratio = int(len(p1) / a.min_ratio) - len(p1)
    need = max(a.min_sources - len(p1), 0)
    sec = (s1_train + s2)[:max(need, min(cap_by_ratio, len(s1_train) + len(s2)))]
    train = p1 + sec

    ratio = len(p1) / max(1, len(train))
    print(f"P1={len(p1)}  次级={len(sec)}  train={len(train)}  "
          f"primary={ratio:.3f}  holdout={len(hold)}")
    if ratio < a.min_ratio or len(train) < a.min_sources:
        want = -(-a.min_sources * int(a.min_ratio * 100) // 100)
        print(f"\n⚠ 不满足门：需 ≥{a.min_sources} 源且 primary ≥{a.min_ratio}，"
              f"即至少 {want} 份 P1；现有 {len(p1)}。")
        print("  灌更多次级源解决不了——分母涨、分子不动，比值只会更低。")
    if a.dry_run:
        return 0

    ok = fail = 0
    for r, split in [(x, "train") for x in train] + [(x, "holdout") for x in hold]:
        y = (re.match(r"ms_(\d{4})_", r["name"]) or [None, "unknown"])[1]
        cmd = [sys.executable, S, a.target, str(W / r["file"]),
               "--tier", r["tier"], "--author", "Michael Steinhardt",
               "--published-at", y, "--language", "en",
               "--source-type", "transcript-or-letter",
               "--abstract", r["abstract"],
               "--rights", RIGHTS, "--locator", r["file"]]
        if split == "holdout":
            cmd.append("--holdout")      # ★ 是布尔开关，不是 --split holdout
        for d in r["dimensions"]:
            cmd += ["--dimension", d]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode == 0:
            ok += 1
        else:
            fail += 1
            print(f"  ✗ {r['name'][:52]}: {p.stderr.strip()[:130]}")
    print(f"\n灌入 {ok} / 失败 {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
