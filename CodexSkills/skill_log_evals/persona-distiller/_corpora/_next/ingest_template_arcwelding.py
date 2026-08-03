#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""电弧焊两人（Slavyanov / Benardos）共用的入库口径。

**这一份是模板，两个人各拷一份改 `SUBJECT` 与 `WS` 即可。**
共用的理由：**归属判据必须两边一致**，否则两份产物会互相矛盾。

## ★★ 头号风险：两个人都在队列里，而他们的发明长期被互相混记

| | 生卒 | 电极 | 时间 |
|---|---|---|---|
| Nikolai **Benardos** | 1842–1905 | **碳** | 更早 |
| Nikolai **Slavyanov** | 1854–1897 | **金属**（可熔） | 稍后 |

**混记的形态**：通俗叙事常把「电弧焊」整体归给其中一位。
Fleming #111 身上是「通俗叙事把牛津团队从青霉素故事里抹掉」，
**这一次更险——两个人都要做，两份产物会同时在册。**

**所以两边的口径必须先统一：**

1. **任何一方的答案里不许出现「电弧焊是我发明的」这种无限定说法。**
   要说就说清**电极材料**（碳／金属）与**年份**。
2. 两人的 `attribution_basis.disputed_works` 里**互相点名**，
   并写明「这一处的功劳分层，另一位在 `_EXCLUDED.txt` 里有条目」。
3. 抓源阶段就把专利与论文**按电极材料归档**，
   台账 note 里标 `ELECTRODE=carbon` 或 `ELECTRODE=metal`；
   **两者都提到的材料标 `BOTH` 并写明它在讲谁。**

## 口径（照抄，别自行发挥）

- **`POSTHUMOUS*` 一律降 P2。**（Benardos 1905 卒、Slavyanov 1897 卒）
- **`TRANSLATION` 降 P2。** 两人都用**俄文**写作——
  **英译本不是他们的话**，取逐字引文必须回俄文原件。
- **`DUPLICATE-SCAN` / `OCR-POOR` 降 P2。**
- **`CYRILLIC-OCR-SUSPECT`**：本流水线在西里尔同形字上栽过一次
  （Livermore #100 的 OCR 里 1405 个西里尔字符、314 个「全同形字词」，
  `check_ocr_homoglyphs` 即为此落成）。
  **俄文件入库后必须跑一遍那道门**，可疑的降 P2 且不得取逐字引文。

## 归属标记（每行至少一个，与 Nightingale #112 同法）

| 标记 | 含义 | author 字段 |
|---|---|---|
| `HIS-OWN` | 他本人署名的专利／论文／书信 | 填 |
| `CO-AUTHORED` | 合著 | 填，attribution 写清哪部分是他的 |
| `THIRD-PARTY` | 第三方所写（S1／S2） | **留空** |
| `ATTRIBUTION-UNCLEAR` | 抓源方查不准署名 | **留空**，落 ⚠ |
| `OTHER-INVENTOR` | **讲的是另一位的发明** | **留空**——这一类是本人物的**负样本** |

**`OTHER-INVENTOR` 是这一对人物专有的**：
它标的材料仍要入库（**边界题需要它**），但**绝不可作本人物的声音**。
"""
import json
import pathlib
import re
import subprocess
import sys

# ── 两个人各改这两行 ──────────────────────────────
SUBJECT = "Nikolai Slavyanov"          # 或 "Nikolai Benardos"
WS = "workspaces/nikolai-slavyanov/nikolai-slavyanov"
MY_ELECTRODE = "metal"                 # Slavyanov=metal / Benardos=carbon
# ────────────────────────────────────────────────

ING = "../../../../registry/codex/persona-distiller/scripts/ingest.py"

DEMOTE = {
    "POSTHUMOUS": "身后出版，非其生前定稿",
    "TRANSLATION": "译本；他用俄文写作——**英译本不是他的话**",
    "DUPLICATE-SCAN": "同一材料的另一次扫描",
    "OCR-POOR": "同一材料的降质 OCR",
    "CYRILLIC-OCR-SUSPECT": "西里尔同形字可疑，**不得取逐字引文**",
}

ATTRIB_REQUIRED = {"HIS-OWN", "CO-AUTHORED", "THIRD-PARTY",
                   "ATTRIBUTION-UNCLEAR", "OTHER-INVENTOR"}

LANES = {"writings", "expression", "conversations", "decisions", "timeline", "external"}


def lane(name: str, note: str) -> str:
    """**先读台账里的 `lane=`，猜文件名只是兜底。**"""
    m = re.search(r"lane=([a-z]+)", note)
    if m and m.group(1) in LANES:
        return m.group(1)
    n = name.lower()
    if any(k in n for k in ("letter", "corresp", "memo")):
        return "conversations"
    if any(k in n for k in ("obit", "chronology", "biograph")):
        return "timeline"
    if any(k in n for k in ("patent", "privilege", "spec")):
        return "decisions"
    if any(k in n for k in ("about", "review", "on-")):
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
            return 3
        rows.append(cols)
    if not rows:
        print("✗ **台账里一条数据行都没有**——不是「没问题」")
        return 3

    ok, fail, demoted, other, lanes_seen = 0, [], 0, 0, {}
    for short, url, title, year, locator, langu, tier, flags, note in rows:
        marks = [m for m in flags.split(";") if m]

        if not (ATTRIB_REQUIRED & set(marks)):
            print(f"✗ {short}：**归属标记缺失**——{'／'.join(sorted(ATTRIB_REQUIRED))} 至少要有一个。"
                  "\n    **查不准就标 `ATTRIBUTION-UNCLEAR` 并写清署名字段原文，不要猜。**")
            fail.append(short)
            continue

        # ★★ 电极材料必须标，且要与本人物对得上
        em = re.search(r"ELECTRODE=(carbon|metal|both)", note)
        if not em:
            print(f"✗ {short}：**没标 `ELECTRODE=`**——"
                  "两位电弧焊先驱的发明长期被互相混记，**这一列不许空**。")
            fail.append(short)
            continue
        if em.group(1) not in (MY_ELECTRODE, "both") and "OTHER-INVENTOR" not in marks:
            print(f"✗ {short}：`ELECTRODE={em.group(1)}` 与本人物（{MY_ELECTRODE}）不符，"
                  "却没标 `OTHER-INVENTOR`——**讲另一位发明的材料必须标出来**。")
            fail.append(short)
            continue

        t = tier
        if t == "P1" and any(m in DEMOTE for m in marks):
            t, demoted = "P2", demoted + 1
        # 归属不明或讲的是另一位的，一律不作本人物的声音
        if t == "P1" and not ({"HIS-OWN", "CO-AUTHORED"} & set(marks)):
            t = "U"
        if "OTHER-INVENTOR" in marks:
            other += 1

        cand = sorted((pathlib.Path("raw") / short).glob("*.txt"))
        if not cand:
            print(f"✗ 文件不在：raw/{short}/")
            fail.append(short)
            continue

        ln = lane(short, note)
        lanes_seen[ln] = lanes_seen.get(ln, 0) + 1
        yr = year if re.fullmatch(r"1[6-9]\d{2}|20\d{2}", year.strip()) else ""
        loc = title[:150] + (f"｜{locator}" if locator else "") + (f"｜{url}" if url else "")
        author = SUBJECT if ({"HIS-OWN", "CO-AUTHORED"} & set(marks)) else ""

        argv = [sys.executable, ING, WS, str(cand[0]),
                "--tier", t, "--language", langu or "ru",
                "--dimension", ln, "--source-type", "document",
                "--author", author, "--locator", loc, "--rights", "public-domain"]
        if yr:
            argv += ["--published-at", yr]
        r = subprocess.run(argv, capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
        else:
            tail = (r.stderr or r.stdout).strip().splitlines()
            print(f"✗ {short}: {tail[-1][:140] if tail else '?'}")
            fail.append(short)

    print(f"\n入库 {ok} 份，失败 {len(fail)} 份，**按 flag 降级 {demoted} 条**，"
          f"**讲另一位发明的 {other} 条**")
    print("六条道分布：" + "　".join(f"{k} {v}" for k, v in sorted(lanes_seen.items())))
    missing = LANES - set(lanes_seen)
    if missing:
        print(f"⚠ **这几条道一份都没有**：{'、'.join(sorted(missing))}")
    print("\n★ 入库后必跑：`check_ocr_homoglyphs`（西里尔同形字），"
          "可疑的降 P2 且不得取逐字引文。")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
