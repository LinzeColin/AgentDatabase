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
ING = "../../../../registry/codex/persona-distiller/scripts/ingest.py"

# 降档标记 → 理由（由 `_attr.py` 写进 attribution）
DEMOTE = {
    "POSTHUMOUS": "身后出版，非其生前定稿",
    "POSTHUMOUS-EDITION": "身后重排本",
    "TRANSLATION": "译本；她用英文写作",
    "DUPLICATE-SCAN": "同一材料的另一次扫描",
    "OCR-POOR": "同一材料的降质 OCR",
    "EDITION-LATER": "同一著作的后出版本，不是首版那份文本",
    "TRANSCRIPTION": "后人转录，非原扫本",
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
    if any(k in n for k in ("address", "speech")):
        return "expression"
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

    ok, fail, demoted, lanes_seen = 0, [], 0, {}
    for short, url, title, year, locator, langu, tier, flags, note in rows:
        marks = [m for m in flags.split(";") if m]

        if not (ATTRIB_REQUIRED & set(marks)):
            print(f"✗ {short}：**归属标记缺失**——"
                  f"{'／'.join(sorted(ATTRIB_REQUIRED))} 至少要有一个。"
                  "\n    **查不准就标 `ATTRIBUTION-UNCLEAR` 并写清署名字段原文，不要猜。**")
            fail.append(short)
            continue

        t = tier
        if t == "P1" and any(m in DEMOTE for m in marks):
            t, demoted = "P2", demoted + 1

        # ★★ **P1 的定义是「本人的话」。没有 `HER-OWN` 就不是 P1。**
        #
        #   流水线自己也这么说：`ingest.py` 对 `--tier P1` 强制要求 `--author`，
        #   而这几份**恰恰给不出作者**。三份实测形态（抓源方逐份核过印刷页）：
        #
        #   · `mortality-british-army-1858`（玫瑰图背后的表）——扉页无署名，
        #     全文里 `Nightingale` 一次都不出现，扉页写着
        #     「[Reprinted from the Report of the Royal Commission…]」；
        #     两条 archive.org 记录**彼此打架**（一条无 creator，一条写 Florence Nightingale）。
        #     **表是她的乃是公认，但文件本身没这么说。**
        #   · `kaiserswerth-1851`——1851 年匿名刊行，全文无其姓；唯一依据是目录 creator 字段。
        #   · `subsidiary-notes-1858`——扉页无署名（已对 Gutenberg 清本核过），
        #     **正文用第三人称称她**（`Miss Nightingale is recognized by…`）。
        #     **同年、同印厂、同「Presented by request」体例的 `notes-british-army-1858`
        #     扉页印着 `FLORENCE NIGHTINGALE.`——这一本没有。**
        #
        #   归 `U`（流水线自带的「未定档」）：**留在库里作证据，但不得作她的声音。**
        #   降成 P2 是错的——P2 是「同一材料的降质版本」，与归属不确定不是一回事。
        if t == "P1" and "HER-OWN" not in marks:
            t = "U"

        cand = sorted((pathlib.Path("raw") / short).glob("*.txt"))
        if not cand:
            print(f"✗ 文件不在：raw/{short}/")
            fail.append(short)
            continue

        ln = lane(short, note)
        lanes_seen[ln] = lanes_seen.get(ln, 0) + 1

        # **文件名的年份不是版次年份**（Virchow #109 的教训）——只认台账那一格
        yr = year if re.fullmatch(r"1[6-9]\d{2}|20\d{2}", year.strip()) else ""
        loc = title[:150] + (f"｜{locator}" if locator else "") + (f"｜{url}" if url else "")

        # ★ **`author` 只在她本人署名时填。** `COMMISSION-COLLECTIVE` 与
        #   `THIRD-PARTY` 一律留空——留空是下游「不得以第一人称引用」的机器可读依据。
        #   Fleming #111 的 MRC 报告 57 就是这么处理的（author 留空、tier 保持 P1）。
        author = "Florence Nightingale" if "HER-OWN" in marks else ""

        argv = [sys.executable, ING, WS, str(cand[0]),
                "--tier", t, "--language", langu or "en",
                "--dimension", ln, "--source-type", "document",
                "--author", author, "--locator", loc,
                "--rights", "public-domain"]
        if yr:
            argv += ["--published-at", yr]
        proc = subprocess.run(argv, capture_output=True, text=True)
        if proc.returncode == 0:
            ok += 1
            if ok % 25 == 0:
                print(f"  … 已入 {ok}")
        else:
            tail = (proc.stderr or proc.stdout).strip().splitlines()
            print(f"✗ {short}: {tail[-1][:140] if tail else '?'}")
            fail.append(short)

    print(f"\n入库 {ok} 份，失败 {len(fail)} 份，**按 flag 降级 {demoted} 条**")
    print("六条道分布：" + "　".join(f"{k} {v}" for k, v in sorted(lanes_seen.items())))
    missing = LANES - set(lanes_seen)
    if missing:
        print(f"⚠ **这几条道一份都没有**：{'、'.join(sorted(missing))}")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
