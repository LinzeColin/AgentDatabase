#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#112 Florence Nightingale 逐份入库。读 `raw/_ids.txt`（9 列），按其判定调 `ingest.py`。

## 口径（照抄，别自行发挥）

- **`POSTHUMOUS*` 一律降 P2。** 她 1910-08-13 卒。
- **`TRANSLATION` 降 P2。** 她用英文写作。
- **`DUPLICATE-SCAN` / `OCR-POOR` 降 P2**（同一材料的降质版本）。
- **`EDITION-LATER` 降 P2。** 她的几种书有多版（`Notes on Nursing` 1859/1860/1861、
  `Notes on Hospitals` 1859/1863），**后出版本仍是她署名，但不是首版那份文本**；
  取逐字引文时必须说清是哪一版。

## ★★ 本人物的头号归属风险：**委员会的报告不是她的文章**

Fleming #111 身上是「MRC 特别报告 57 号，与 Douglas、Colebrook 合著」——
第 3 轮席 E 抓到答案以第一人称独揽了那份合著报告。**同一个形状在她身上更重。**

1857–58 年的 Royal Commission on the Health of the Army，
其**报告是委员会集体署名的公文**；而她 1858 年那本
*Notes on Matters Affecting the Health, Efficiency, and Hospital Administration
of the British Army*（853 页，私人印行）**是她自己署名的**。

两者内容高度重叠、常被混引。**判据：**

| 标记 | 含义 | 处置 |
|---|---|---|
| `HER-OWN` | 她署名的著作／书信／备忘录 | P1，可作第一人称引用 |
| `COMMISSION-COLLECTIVE` | 委员会／部门集体署名的公文 | **P1 保留，但 attribution 必须写明「这是委员会的文件，不是她的文章」** |
| `CO-AUTHORED` | 与 Farr 等人合作的成果 | P1 保留，attribution 写清哪一部分是她的 |
| `THIRD-PARTY` | 第三方所写（S1／S2） | 不属她的署名范畴，**不得以第一人称引用** |
| `ATTRIBUTION-UNCLEAR` | 抓源方查不准署名 | **不拦，但落 ⚠**——下游不得拿它撑承重句 |

**入库时把这三类分开记，是为了让答案层不能含混过去。**
她确实主导了那场调查——但「主导」与「这份文件是我写的」是两句话。

## ★ `HAS-OWN-STATS` 要带进 attribution

抓源方给含她自己算出的数表的那些份打了 `HAS-OWN-STATS` 并简述了表里是什么数。
**这条不许在入库时丢掉**——v0.0.0.63 的实测声明门要求
「说我量过的地方必须有数」，而这些数表就是那些数的来源。
attribution 里留着它，下游才知道去哪一份找。

## lane 先读台账，猜文件名只是兜底

与 Fleming #111 同：台账每行都带 `lane=`，是抓源方逐份看过文档写下的，
比按文件名猜准。**猜只在台账没写时用。**
"""
import json
import pathlib
import re
import subprocess
import sys

WS = "workspaces/florence-nightingale/florence-nightingale"
INGEST = "../../../../registry/codex/persona-distiller/scripts/ingest.py"

# 降档标记 → 理由（写进 attribution）
DEMOTE = {
    "POSTHUMOUS": "身后出版，非其生前定稿",
    "POSTHUMOUS-EDITION": "身后重排本",
    "TRANSLATION": "译本；她用英文写作",
    "DUPLICATE-SCAN": "同一材料的另一次扫描",
    "OCR-POOR": "同一材料的降质 OCR",
    "EDITION-LATER": "同一著作的后出版本，不是首版那份文本",
}

# 归属标记 → 必须写进 attribution 的那句话
ATTRIB_NOTE = {
    "COMMISSION-COLLECTIVE":
        "**这是委员会／部门集体署名的公文，不是她本人的文章。**"
        "她主导了那场调查是一回事，「这份文件是我写的」是另一回事——"
        "取逐字引文时不得以第一人称转述。",
    "CO-AUTHORED":
        "**合著。** 合著不等于不是她写的，但「哪一部分是她的」要写清。",
    "HER-OWN":
        "她本人署名的著作／书信／备忘录。",
    "THIRD-PARTY":
        "**第三方所写**，不属她的署名范畴——**不得以第一人称引用。**",
    "ATTRIBUTION-UNCLEAR":
        "⚠ **抓源方查不准署名。** 可作旁证，**不得拿它撑承重句**。",
    "HAS-OWN-STATS":
        "**本份含她自己算出的数表**——实测声明门要求「说我量过的地方必须有数」，"
        "这里就是那些数的来源。",
}

# 归属那一列：每行至少要中一个，否则下游无从判断能不能第一人称引用
ATTRIB_REQUIRED = {"HER-OWN", "COMMISSION-COLLECTIVE", "CO-AUTHORED",
                   "THIRD-PARTY", "ATTRIBUTION-UNCLEAR"}

LANES = {"writings", "expression", "conversations", "decisions", "timeline", "external"}


def lane(name: str, note: str) -> str:
    """**先读台账里的 `lane=`，猜文件名只是兜底。**"""
    m = re.search(r"lane=([a-z]+)", note)
    if m and m.group(1) in LANES:
        return m.group(1)
    n = name.lower()
    if any(k in n for k in ("letter", "corresp", "note-to", "memo")):
        return "conversations"
    if any(k in n for k in ("obit", "chronology", "timeline", "biograph")):
        return "timeline"
    if any(k in n for k in ("commission", "evidence", "report", "recommend")):
        return "decisions"
    if any(k in n for k in ("address", "speech", "letter-to-nurses")):
        return "expression"
    if any(k in n for k in ("review", "about", "on-miss")):
        return "external"
    return "writings"


def main() -> int:
    ids = pathlib.Path("raw/_ids.txt")
    if not ids.is_file():
        print("✗ **raw/_ids.txt 不在**——抓源还没写台账，不能入库")
        return 3

    rows = []
    for i, line in enumerate(ids.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 9:
            print(f"✗ 第 {i} 行 {len(cols)} 列，应为 9 列——**不猜，请抓源方修**")
            print(f"    {line[:120]}")
            return 3
        rows.append(cols)

    if not rows:
        print("✗ **台账里一条数据行都没有**——不是「没问题」")
        return 3

    ok, fail, lanes_seen = 0, [], {}
    for short, url, title, year, locator, langu, tier, flags, note in rows:
        marks = [m for m in flags.split(";") if m]
        t = tier
        reasons = []
        for m in marks:
            if m in DEMOTE and t == "P1":
                t = "P2"
                reasons.append(DEMOTE[m])
        notes = [ATTRIB_NOTE[m] for m in marks if m in ATTRIB_NOTE]

        # ★ 归属那一列必须至少中一条，否则不知道这份能不能第一人称引用
        if not (ATTRIB_REQUIRED & set(marks)):
            print(f"✗ {short}：**归属标记缺失**——"
                  f"{'／'.join(sorted(ATTRIB_REQUIRED))} 至少要有一个。"
                  "\n    没有它，下游无从判断这份能不能以第一人称引用。"
                  "\n    **查不准就标 `ATTRIBUTION-UNCLEAR` 并写清署名字段原文，不要猜。**")
            fail.append(short)
            continue

        ln = lane(short, note)
        lanes_seen[ln] = lanes_seen.get(ln, 0) + 1
        attribution = "　".join([note] + notes
                                + ([f"**降 {t}**：" + "；".join(reasons)] if reasons else []))
        cmd = [sys.executable, INGEST,
               "--workspace", WS, "--path", f"raw/{short}/{short}.txt",
               "--title", title, "--published-at", year, "--locator", locator,
               "--language", langu, "--tier", t, "--dimension", ln,
               "--attribution", attribution]
        if url:
            cmd += ["--url", url]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
        else:
            fail.append(short)
            print(f"✗ {short}: {(r.stderr or r.stdout).strip().splitlines()[-1][:150]}")

    print(f"\n入库 {ok} 份，失败 {len(fail)} 份")
    print("六条道分布：" + "　".join(f"{k} {v}" for k, v in sorted(lanes_seen.items())))
    missing = LANES - set(lanes_seen)
    if missing:
        print(f"⚠ **这几条道一份都没有**：{'、'.join(sorted(missing))}")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
