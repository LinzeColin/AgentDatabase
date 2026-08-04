#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#117 Clara Barton 入库驱动——逐行读抓源台账，按行调 `ingest.py`。

## 口径（照抄，别自行发挥）

- **分档一律取台账第 7 列**，本脚本**不重新判档**。
  抓源方已经逐卷实测过：LOC 通信卷来信占压倒多数（Willard 卷她的落款 0 处、
  写给她的 22 处），**因此定 S1 而不是 P1**。
  **不许在入库环节把它们提成 P1**——那是靠技术性做高一手占比。
- **道取第 9 列的 `lane=`**，权利依据取 `RIGHTS=`。
- `author` 只在归属标记为 `HIS-OWN` / `CO-AUTHORED` 时填；
  `THIRD-PARTY` / `ATTRIBUTION-UNCLEAR` **一律留空**——
  填了就等于把别人的话记在她名下。

## ★★ holdout 按**整部著作**留，不按份留

Nightingale #112 栽过一次：**同一本书的不同版次被拆到 train/holdout 两侧**，
`check_holdout_overlap` 实测覆盖 53.1%。
本人物这个风险更大——`A Story of the Red Cross` 一部书有 **8 份**扫描、
`The Red Cross in Peace and War` 有 **7 份**。

所以 holdout 以**篇名**为单位整组留出，**同名的每一份都留**。

## ★ holdout 选的是她自己的东西，而这会**拉低**一手占比

holdout 不计入 `usable`，所以留出 P1 等于同时减小分子与分母，
而分子占比高时净效果是**占比下降**。

**明知如此仍然这么选**：holdout 是用来验「没读过也能像她」的，
留第三方材料测不出这件事。**判据该难的地方就得难。**
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = HERE / "raw" / "_ids.txt"
TARGET = HERE / "workspaces" / "clara-barton" / "clara-barton"
INGEST = (HERE.parents[3] / "registry" / "codex" / "persona-distiller"
          / "scripts" / "ingest.py")

SUBJECT = "Clara Barton"

# ★ holdout：按**篇名**整组留出。选的都是她自己的东西，且覆盖两条道。
HOLDOUT_TITLES = {
    "The Story of My Childhood",                       # 自传，3 份（P1+P2×2）
    "A Story of the Red Cross: Glimpses of Field Work",  # 3 份（P1+P2×2）
}

OWN = {"HIS-OWN", "CO-AUTHORED"}


def rows():
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "\t" not in line:
            continue
        c = line.split("\t")
        if len(c) != 9:
            raise SystemExit(f"✗ 不是 9 列：{c[0]}")
        note = c[8]
        lane = re.search(r"lane=([a-z]+)", note)
        rights = re.search(r"RIGHTS=([^；;]+)", note)
        if not lane:
            raise SystemExit(f"✗ 第 9 列没有 lane=：{c[0]}")
        yield {
            "sid": c[0], "url": c[1], "title": c[2], "year": c[3],
            "lang": c[5], "tier": c[6], "flags": c[7],
            "lane": lane.group(1),
            "rights": (rights.group(1).strip() if rights else "public-domain"),
        }


def main() -> int:
    if not INGEST.is_file():
        raise SystemExit(f"✗ 找不到 ingest.py：{INGEST}")
    all_rows = list(rows())
    held = [r for r in all_rows if r["title"] in HOLDOUT_TITLES]
    print(f"台账 {len(all_rows)} 行　holdout {len(held)} 份"
          f"（{len(HOLDOUT_TITLES)} 部著作整组留出）\n")

    ok = fail = 0
    for r in all_rows:
        body = HERE / "raw" / r["sid"] / f"{r['sid']}.txt"
        if not body.is_file():
            print(f"  ✗ 正文不在：{body}")
            fail += 1
            continue
        cmd = [sys.executable, str(INGEST), str(TARGET), str(body),
               "--tier", r["tier"],
               "--dimension", r["lane"],
               "--rights", r["rights"][:200],
               "--language", r["lang"],
               "--locator", f"{r['title']}｜{r['year']}｜{r['url']}"[:400],
               "--source-type", "document"]
        if any(f in r["flags"] for f in OWN):
            cmd += ["--author", SUBJECT]
        if r["year"].strip().isdigit():
            cmd += ["--published-at", r["year"].strip()]
        if r["title"] in HOLDOUT_TITLES:
            cmd += ["--holdout"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode == 0:
            ok += 1
        else:
            fail += 1
            print(f"  ✗ {r['sid']}: {(p.stderr or p.stdout).strip()[:160]}")
    print(f"\n入库 {ok} 成功　{fail} 失败")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
