#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#118 Elizabeth Blackwell 入库驱动 —— 逐行读 `raw/_ids.txt`，按行调 `ingest.py`。

## 口径（照抄，别自行发挥）

- **分档一律取台账第 7 列，本脚本不重新判档。**
  `S1`（LoC 一般通信）是**寄给她的来信**——收信人是她 ≠ 她写的。
  **不许在入库环节把它们提成 P1**，那是靠技术性做高一手占比。
- **道取第 9 列的 `lane=`**，权利依据取 `RIGHTS=`。
- `author` 只在归属标记为 `HIS-OWN` / `CO-AUTHORED` 时填；
  `THIRD-PARTY` / `ATTRIBUTION-UNCLEAR` **一律留空**——填了就等于把别人的话记在她名下。

## ★★ holdout 按短名逐条列出，不按篇名分组

Nightingale #112 与 Barton #117 各栽过一次：**同一著作的不同版次/著录名被拆到两侧**，
`check_holdout_overlap` 实测覆盖 53.1% 与 89.4%。

**「按篇名分组」不等于「按著作分组」——著录题名会变，书不会变。**

本人物的重复关系已经在台账里标死（`DUPLICATE-SCAN` 四份），
所以 holdout **只从没有任何重复兄弟的单副本材料里选**：

- 四册日记（1872–74 / 1891–93 / 1903–05 / 1836）——LoC 各只有一个 folder，
  且日记内容不进任何出版著作；
- 两份**只此一处**的手稿（`Anatomy`、`Why Hygienic Congresses Fail`）——
  台账第 9 列已注明「出版著作里没有」。

**选完必须实跑 `check_holdout_overlap` 验一遍，不许凭设计自信。**

## ★ holdout 选的是她自己的东西，这会拉低一手占比

holdout 不计入 usable，留出 P1 等于同时减小分子与分母，占比高时净效果是**下降**。
**明知如此仍这么选**：holdout 是用来验「没读过也能像她」的，留第三方材料测不出这件事。
**判据该难的地方就得难**——何况本人物一手 78 份，抽 6 份仍远超 deep 要的 30 份。
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = HERE / "raw" / "_ids.txt"
TARGET = HERE / "workspaces" / "elizabeth-blackwell"
INGEST = (HERE.parents[3] / "registry" / "codex" / "persona-distiller" / "scripts" / "ingest.py")

SUBJECT = "Elizabeth Blackwell"

# ★ 短名必须与 `raw/<短名>/` 目录名**一字不差**（含双横线）。
#   第一版我按「应该长什么样」写，6 份里 5 份没匹配上——
#   而 `ingest.py` 不会报错，它只是**没加 --holdout**。
#   这一条脚本里有硬检查：没匹配上就退出 1 并点名，不许当成「少留了几份」。
HOLDOUT_IDS = {
    "diary-1872-1874-mss959",
    "diary-1903-1905-mss969",
    "diary-1836-mss956",
    # ★ 换掉 diary-1891-1893：它与相邻两册重叠 13–15%，**而重叠的不是她的字**，
    #   是商品袖珍日记本的印刷扉页（邮资表、印花税则、王室年表）被众包连同手写一起转写了。
    #   作为 holdout 不算泄漏，但它是全 16 册里印刷页最多的一册（13.4%），
    #   换成 1900–02（0.1%）严格更好。
    "diary-1900-1902-mss968",
    "sp-1237-anatomy--手稿",
    # ★★ 换掉 sp-1260：`check_holdout_overlap` 实测它与 Essays 卷二覆盖 **80.7%**——
    #   **它被收进了文集**。我照抄了探测报告的「只此一处」，**判据当场推翻**。
    #   替补 sp-1251（1889 年费城 The Press 撰文）实测与全部 94 份的最高重叠 **0.0%**。
    "sp-1251-the-position-of-women--费城-the-press",
}

OWN = {"HIS-OWN", "CO-AUTHORED"}


def main() -> int:
    if not LEDGER.is_file():
        print(f"✗ **台账不在：{LEDGER}**——先跑 build_ledger.py"); return 3
    rows = [l for l in LEDGER.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]
    print(f"台账 {len(rows)} 行；holdout 指定 {len(HOLDOUT_IDS)} 份")

    seen_holdout, ok, bad = set(), 0, []
    for line in rows:
        c = line.split("\t")
        if len(c) != 9:
            bad.append(f"列数 {len(c)} ≠ 9：{c[0] if c else line[:40]}"); continue
        short, url, title, year, locator, lang, tier, mark, note = c
        m = re.match(r"lane=(\w+)\.", note)
        if not m:
            bad.append(f"第 9 列不以 lane= 开头：{short}"); continue
        lane = m.group(1)
        rights = note.split("RIGHTS=", 1)[1] if "RIGHTS=" in note else ""
        marks = set(mark.split())
        attrib = marks & (OWN | {"THIRD-PARTY", "ATTRIBUTION-UNCLEAR", "OTHER-INVENTOR"})
        if len(attrib) != 1:
            bad.append(f"归属标记不是恰好一个（{mark}）：{short}"); continue

        f = HERE / "raw" / short / f"{short}.txt"
        if not f.is_file():
            bad.append(f"正文不在：{f}"); continue

        cmd = [sys.executable, str(INGEST), str(TARGET), str(f),
               "--tier", tier, "--dimension", lane, "--language", lang,
               "--published-at", year, "--rights", rights,
               "--locator", f"{title}｜{year}｜{locator}｜{url}"]
        if attrib & OWN:
            cmd += ["--author", SUBJECT]
        if short in HOLDOUT_IDS:
            cmd.append("--holdout"); seen_holdout.add(short)
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            bad.append(f"{short} → 退出码 {p.returncode}：{(p.stderr or p.stdout).strip()[:150]}")
        else:
            ok += 1

    missing = HOLDOUT_IDS - seen_holdout
    print(f"\n入库成功 {ok} / {len(rows)}")
    if missing:
        print(f"★ **指定的 holdout 有 {len(missing)} 份没匹配上台账短名**："
              f"{sorted(missing)}——**这不是「少留了几份」，是短名写错了，必须改对**")
    if bad:
        print(f"✗ **{len(bad)} 条未入库**：")
        for b in bad[:12]:
            print("   ", b)
        return 1
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
