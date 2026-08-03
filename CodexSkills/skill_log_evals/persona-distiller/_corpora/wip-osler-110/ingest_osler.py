#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#110 Osler 逐份入库。读 `raw/_ids.txt`（9 列），按其判定调 ingest.py。

## 四条口径（照抄，别自行发挥）

- **`POSTHUMOUS*` 一律降 P2。** 他 1919-12-29 卒；《Principles and Practice》
  第 9 版（1920/1921）扉页作「BY **THE LATE** SIR WILLIAM OSLER … **AND** THOMAS
  McCRAE」——**那是他身后由别人续修的，不是他写的**。
  抓源阶段已逐份翻扉页确认，本脚本按 flag 兜底。

- **`CO-AUTHORED` 保留 P1 但记进 attribution。** 合著不等于不是他写的，
  但「哪一部分是他的」要写清（如 1877 年那篇，只有病理报告是他的，临床报告是 John Bell 的）。

- **`HANDWRITING-OCR-UNUSABLE` 降 P2。** 手稿只有影像、OCR 出来读不出字——
  **留在库里作旁证，但不得取逐字引文。**（与 Virchow 那 17 份 Fraktur 报废同一处理。）

- **`translation` 降 P2。** 他用英文写作，**没有译文层**——
  这是本人物相对 Virchow 的结构优势，但抓到的两份译本仍按译者的字处理。

## 六路归属

按题材粗分，**分不清的记 writings**。`external` 只给 S1/S2。
"""
import json
import pathlib
import re
import subprocess
import sys

WS = "workspaces/william-osler/william-osler"
ING = "../../../../registry/codex/persona-distiller/scripts/ingest.py"

LANE = [
    (r"^s1-|^s2-", "external"),
    (r"aequanimitas|address|oration|valedictory|counsels|ideals|master-word|"
     r"teacher|student|book|library|chauvinism", "expression"),
    (r"letter|correspond|note-?book|memorandum", "conversations"),
    (r"bibliotheca|chronolog|obituary|in-memoriam", "timeline"),
    (r"hospital|nursing|public-health|typhoid-.*campaign|tuberculosis-crusade|"
     r"medical-education|clinical-teaching|residency", "decisions"),
]


def lane(name: str, tier: str) -> str:
    if tier in ("S1", "S2"):
        return "external"
    for pat, ln in LANE:
        if re.search(pat, name, re.I):
            return ln
    return "writings"


def main() -> int:
    rows = []
    for line in pathlib.Path("raw/_ids.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < 9:
            print(f"⚠ 列数 {len(f)}，跳过：{line[:50]}")
            continue
        rows.append({"sub": f[0].strip(), "url": f[1].strip(), "title": f[2].strip(),
                     "year": f[3].strip(), "edition": f[4].strip(), "lang": f[5].strip(),
                     "tier": f[6].strip(), "flags": f[7].strip(), "note": f[8].strip()})

    ok = fail = demoted = 0
    for r in rows:
        cand = sorted((pathlib.Path("raw") / r["sub"]).glob("*.txt"))
        if not cand:
            print(f"✗ 文件不在：{r['sub']}")
            fail += 1
            continue
        p = cand[0]

        tier = r["tier"]
        fl = r["flags"]
        if tier == "P1" and ("POSTHUMOUS" in fl or "HANDWRITING-OCR-UNUSABLE" in fl
                             or "translation" in fl):
            tier, demoted = "P2", demoted + 1

        year = r["year"] if re.fullmatch(r"1[6-9]\d{2}|20\d{2}", r["year"]) else ""
        loc = f"{r['title'][:150]}"
        if r["edition"] and not r["edition"].startswith("["):
            loc += f"｜{r['edition']}"
        loc += f"｜{r['url']}"

        argv = [sys.executable, ING, WS, str(p),
                "--tier", tier,
                "--language", r["lang"] or "en",
                "--dimension", lane(r["sub"], tier),
                "--source-type", "document",
                "--author", "William Osler" if tier == "P1" else "",
                "--locator", loc,
                "--rights", "public-domain"]
        if year:
            argv += ["--published-at", year]
        proc = subprocess.run(argv, capture_output=True, text=True)
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()
            print(f"✗ {r['sub']}: {tail[-1][:140] if tail else '?'}")
            fail += 1
        else:
            ok += 1
            if ok % 25 == 0:
                print(f"  … 已入 {ok}")
    print(f"\n入库成功 {ok}，失败 {fail}，**按 flag 降级 {demoted} 条**")

    led = pathlib.Path(WS) / "evidence/source-ledger.jsonl"
    if led.is_file():
        import collections
        c, ln = collections.Counter(), collections.Counter()
        for line in led.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                c[d.get("tier")] += 1
                for x in (d.get("dimensions") or ["?"]):
                    ln[x] += 1
        tot = sum(c.values())
        print("账本 tier：", dict(c))
        print("账本 六路：", dict(ln))
        print(f"**primary_ratio = (P1 {c['P1']} + P2 {c['P2']}) / {tot} = "
              f"{(c['P1']+c['P2'])/max(tot,1):.4f}**　（deep 门要 ≥0.65）")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
