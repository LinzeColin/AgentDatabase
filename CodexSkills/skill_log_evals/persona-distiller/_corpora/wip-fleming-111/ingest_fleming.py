#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#111 Fleming 逐份入库。读 `raw/_ids.txt`（9 列），按其判定调 ingest.py。

## 口径（照抄，别自行发挥）

- **`POSTHUMOUS*` 一律降 P2。** 他 1955-03-11 卒。
- **`CO-AUTHORED` 保留 P1 但记进 attribution。** 合著不等于不是他写的，
  但「哪一部分是他的」要写清——**这个人物身上这一条是头号风险**，见下。
- **`HANDWRITING-OCR-UNUSABLE` 降 P2。** 手稿只有影像、OCR 读不出字，
  **留在库里作旁证，但不得取逐字引文。**（与 Virchow 那 17 份 Fraktur 报废同一处理。）
- **`translation` 降 P2。** 他用英文写作。

## ★ 头号风险不是同名，是**一整支团队被通俗叙事抹掉**

- **1928 年那次观察、1929 年那篇论文是他的。**
- **分离、纯化、临床验证不是他做的**——1939–1945 由牛津的 Florey、Chain、Heatley 完成；
  1945 年诺奖三人共享。
- 所以 Florey / Chain 那一侧的材料**按 S1 收**（同时代第三方），
  它们不是用来给他加分的，是**用来给归属分层做证据的**。
- **两个方向都要设障**：既不许写成他一人发明青霉素，
  也不许否认 1928 的观察与 1929 的论文确实是他的。

## 六路归属

按题材粗分，**分不清的记 writings**。`external` 只给 S1/S2。
"""
import json
import pathlib
import re
import subprocess
import sys

WS = "workspaces/alexander-fleming/alexander-fleming"
ING = "../../../../registry/codex/persona-distiller/scripts/ingest.py"

# 顺序有意义：先匹配先归。`external` 那条必须在最前，S1/S2 不进其它路。
LANE = [
    (r"^s1-|^s2-", "external"),
    (r"nobel|lecture|address|oration|harben|discourse|banquet|speech", "expression"),
    (r"letter|correspond|note-?book|memorandum|interview", "conversations"),
    (r"obituar|in-memoriam|chronolog|biograph|centenary", "timeline"),
    (r"laborator|st-?mary|inoculation-dept|wright|institute|committee|"
     r"war-?wound|casualty", "decisions"),
]


SIX = ("writings", "expression", "conversations", "decisions", "timeline", "external")


def lane(name: str, tier: str, note: str = "") -> str:
    """**先读台账里的 `lane=`，猜文件名只是兜底。**

    第一版只按文件名的正则猜，实测把 69 份归成
    `writings 38 / external 24 / expression 4 / decisions 2 / conversations 1 / timeline 0`
    ——**六路缺一路，deep 门直接过不去**。
    而台账 69 行**每一行都带 `lane=`**，是抓源方逐份看过文档写下的：
    `writings 17 / external 17 / expression 15 / timeline 7 / decisions 7 / conversations 6`。
    **抓源方看过内容，我只看得到文件名。谁看过谁说了算。**
    """
    m = re.search(r"lane=([a-z]+)", note)
    if m and m.group(1) in SIX:
        return m.group(1)
    if tier in ("S1", "S2"):
        return "external"
    for pat, ln in LANE:
        if re.search(pat, name, re.I):
            return ln
    return "writings"


def main() -> int:
    ids = pathlib.Path("raw/_ids.txt")
    if not ids.is_file():
        print("✗ **raw/_ids.txt 不在**——抓源还没写台账，不能入库")
        return 3

    rows = []
    for line in ids.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < 9:
            print(f"⚠ 列数 {len(f)}，跳过：{line[:60]}")
            continue
        rows.append({"sub": f[0].strip(), "url": f[1].strip(), "title": f[2].strip(),
                     "year": f[3].strip(), "edition": f[4].strip(), "lang": f[5].strip(),
                     "tier": f[6].strip(), "flags": f[7].strip(), "note": f[8].strip()})
    if not rows:
        print("✗ **台账里一行都没读到**——结果不可信，不是「没问题」")
        return 3

    ok = fail = demoted = 0
    for r in rows:
        cand = sorted((pathlib.Path("raw") / r["sub"]).glob("*.txt"))
        if not cand:
            print(f"✗ 文件不在：{r['sub']}")
            fail += 1
            continue
        p = cand[0]

        tier, fl = r["tier"], r["flags"]
        if tier == "P1" and ("POSTHUMOUS" in fl or "HANDWRITING-OCR-UNUSABLE" in fl
                             or "translation" in fl):
            tier, demoted = "P2", demoted + 1

        # **文件名的年份不是版次年份**（Virchow #109 的教训）——只认台账里那一格，
        # 而台账那一格由抓源阶段按扉页填。填不出的记 `[扉页年份不清]`，这里就留空。
        year = r["year"] if re.fullmatch(r"1[6-9]\d{2}|20\d{2}", r["year"]) else ""
        loc = r["title"][:150]
        if r["edition"] and not r["edition"].startswith("["):
            loc += f"｜{r['edition']}"
        loc += f"｜{r['url']}"

        argv = [sys.executable, ING, WS, str(p),
                "--tier", tier,
                "--language", r["lang"] or "en",
                "--dimension", lane(r["sub"], tier, r["note"]),
                "--source-type", "document",
                "--author", "Alexander Fleming" if tier == "P1" else "",
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
              f"{(c['P1'] + c['P2']) / max(tot, 1):.4f}**　（deep 门要 ≥0.65）")
        missing = [x for x in ("writings", "expression", "conversations",
                               "decisions", "timeline", "external") if not ln.get(x)]
        if missing:
            print(f"⚠ **六路缺 {len(missing)} 路**：{'、'.join(missing)}——deep 门要 6 路齐")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
