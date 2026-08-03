#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**账本说有这么多源，磁盘上还有几份。**

## 为什么有这道判据

v0.0.0.46 手工扫了一次十二个工作台，发现三个人物的语料**根本不在**：
Livermore #100（账本 536 条、语料 0 份）、Vesalius #102（47/0）、Galen #101（60/9）。
账本还在、断言还在、文档还在，**只有语料没了**——
于是 `primary_ratio`、引文核查、覆盖率**全都在对着虚空算**。

那一次是手工跑的。**手工的东西会漏，也会记错**：
当时的记录里写 Harvey #103 也缺，2026-08-04 我用份数比较「改正」为
「46 条账本、60 份语料，是齐的」。

### ★ 那次「改正」是错的，而且错法就是本判据 v0.0.0.63 之前的样子

2026-08-04 加上逐条解析后实测：Harvey 的账本每一条都指
`raw/src-<hash>/hv_works_willis_1847.txt`，磁盘上却是
`raw/s_bub_gb_CdDfAc_ENH0C.txt` 这样的扁平名，**没有一条指得到文件**。

**那 60 份与那 46 条是两批互不相干的东西。**
拿它们相减得出「多了 14 份，很健康」——**v0.0.0.46 原本的记录是对的，
是我用一个只会数数的判据把它改错了。**

## 判据（三项，缺一项都会放过一整类）

1. **份数**：账本条数 × 0.9 ≤ 语料 .txt 份数。
2. **指得到**：账本每条的 `local_path` 解析得到文件吗？
   —— 份数够而一条都指不到，是「两套编号」，不是健康。
3. **字节对**：解析到的文件，sha256 与账本记的 `checksum` 一致吗？
   —— 文件在、路径对，仍可能不是账本 attest 的那一份。

## 它判不了什么

- **不查内容是否可读**。文件在、哈希也对，但内容是错误页，
  那是 `check_corpus_integrity` 的活。
- 阈值取 0.9 而非 1.0：同一份源可能被切成多份、也可能有合并；
  **少几份是正常的，少一半以上不是。**

## ★ 找账本不许写死路径

本流水线里账本出现过**两种布局**：`<工作区>/evidence/source-ledger.jsonl`
与**目录顶层的** `source-ledger.jsonl`。
第一版审计脚本只按前者找，于是 Galen / Vesalius / Harvey / Livermore
**四个工作区整个从表里消失了**——报表看上去「全部齐」。
**用 rglob，不写死路径。**
"""
import argparse
import hashlib
import json
import pathlib
import sys

RATIO = 0.9


def verify_checksums(ledger: pathlib.Path):
    """→ (核过的份数, 对不上的 [(文件名, 账本哈希, 现盘哈希)])。

    ★ v0.0.0.64：**只数份数是不够的——错的文件也能凑够份数。**

    2026-08-04 我自己造出了这个场景：Galen #101 账本 60 条、磁盘 9 份，
    我从 CTS 仓库把 TEI 正文重新转成纯文本写回账本记的 `local_path`，
    份数当场从 9 补到 64，**本判据变绿**。
    但逐份核校验和，**55 份无一相同**——抽取方式与当初入库的不同。

    留在那里的后果：`primary_ratio`、引文核查、覆盖率**全都在对着另一份文本算**，
    而判据说「语料都在」。台账里已记过三次「判据绿了但指错了文件」，
    这一次是判据自己的口子。

    账本的 `source_id` 是 `src-<checksum 前 12 位>`，两者互证——
    所以 `checksum` 字段确实是当初那份文件的哈希，可以拿来核。
    """
    # ★ `local_path` 是相对**工作区根**的，不是相对账本所在目录。
    #   账本有两种布局（顶层 / `evidence/` 下），只按 `ledger.parent` 解析，
    #   在后一种布局下一条也解析不到——于是「0 份对不上」，**看起来像全对**。
    #   自测正向 ② 当场抓出：本文件开头早就警告过这两种布局，
    #   **同一个坑在另一处又咬了一次。**
    bases = [ledger.parent, ledger.parent.parent]
    bad, checked = [], 0
    for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rec = r.get("checksum")
        lp = r.get("local_path")
        if not (rec and lp):
            continue
        p = next((b / lp for b in bases if (b / lp).is_file()), None)
        if p is None:
            continue                      # 文件不在是「缺」，由份数那一支报
        checked += 1
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != rec:
            bad.append((pathlib.Path(lp).name, rec[:12], got[:12]))
    return checked, bad


def scan(root):
    """→ [(名, 账本条数, 语料份数, 是否缺, 校验和对不上的份数, 解析到文件的条数)]。

    ★ v0.0.0.64 第三项：**「份数够」与「账本指得到文件」是两件事。**

    Harvey #103 实测：账本 46 条、磁盘 60 份，份数比较判「齐 ✓」——
    而账本每一条都指向 `raw/src-<hash>/hv_works_willis_1847.txt` 这样的路径，
    磁盘上却是 `raw/s_bub_gb_CdDfAc_ENH0C.txt` 这样的扁平文件名，
    **没有一条解析得到文件。**

    也就是说这 60 份与那 46 条**是两批互不相干的东西**，
    份数比较拿它们相减，得出「多了 14 份，很健康」。

    我在册子里写过「Harvey 是好的（46/60）」，**那句话就是这么来的。**
    """
    rows = []
    for d in sorted(pathlib.Path(root).glob("*")):
        if not d.is_dir():
            continue
        leds = list(d.rglob("source-ledger.jsonl"))
        if not leds:
            rows.append((d.name, None, None, True, 0, 0))
            continue
        n = sum(1 for line in leds[0].read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip())
        t = len([p for p in d.rglob("*.txt") if "raw" in p.parts])
        resolved, bad = verify_checksums(leds[0])
        rows.append((d.name, n, t, t < n * RATIO, len(bad), resolved))
    return rows


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)

        def mk(name, ledger_at, n_led, n_txt, corrupt=0):
            """corrupt=k：让前 k 份的内容与账本记的校验和对不上。"""
            w = root / name
            (w / ledger_at).mkdir(parents=True, exist_ok=True)
            raw = w / "raw"
            raw.mkdir(exist_ok=True)
            lines = []
            for i in range(n_led):
                body = f"source {i}".encode()
                rel = f"raw/f{i}.txt"
                lines.append(json.dumps({
                    "source_id": f"src-{i:012x}",
                    "local_path": rel,
                    "checksum": hashlib.sha256(body).hexdigest()}))
                if i < n_txt:
                    (raw / f"f{i}.txt").write_bytes(
                        b"WRONG BYTES" if i < corrupt else body)
            for i in range(n_led, n_txt):
                (raw / f"f{i}.txt").write_bytes(b"extra")
            led_dir = w / ledger_at
            (led_dir / "source-ledger.jsonl").write_text("\n".join(lines) + "\n",
                                                        encoding="utf-8")

        print("── 正向：账本 536 条、语料 0 份（Livermore #100 的真实形态）──")
        mk("wip-a", "evidence", 536, 0)
        r = {x[0]: x for x in scan(root)}
        chk("报出缺口", r["wip-a"][3] and r["wip-a"][1] == 536 and r["wip-a"][2] == 0)

        print("── 反向对照 ①：齐的不许报 ──")
        mk("wip-b", "evidence", 46, 60)
        r = {x[0]: x for x in scan(root)}
        chk("46 条账本、60 份语料 → 不报", not r["wip-b"][3])

        print("── 反向对照 ②：**账本在目录顶层也要找得到** ──")
        # 第一版写死 `<工作区>/evidence/`，于是四个工作区整个从表里消失、报表显示「全部齐」
        mk("wip-c", ".", 60, 9)
        r = {x[0]: x for x in scan(root)}
        chk("顶层账本 60 条、语料 9 份 → 找得到并报出",
            "wip-c" in r and r["wip-c"][3] and r["wip-c"][1] == 60)

        print("── 反向对照 ③：少几份是正常的，不许报 ──")
        mk("wip-d", "evidence", 100, 95)
        r = {x[0]: x for x in scan(root)}
        chk(f"95/100 ≥ {RATIO:.0%} → 不报", not r["wip-d"][3])
        mk("wip-e", "evidence", 100, 80)
        r = {x[0]: x for x in scan(root)}
        chk(f"80/100 < {RATIO:.0%} → 报出", r["wip-e"][3])

        print("── 反向对照 ④：没有账本的目录要单列，不许当成「齐」 ──")
        (root / "wip-f").mkdir()
        r = {x[0]: x for x in scan(root)}
        chk("无账本 → 报出且账本数记 None", r["wip-f"][3] and r["wip-f"][1] is None)

        print("── 反向对照 ⑤：**只数 raw/ 下的 .txt**，别的目录不算 ──")
        (root / "wip-g" / "evidence").mkdir(parents=True)
        (root / "wip-g" / "evidence" / "source-ledger.jsonl").write_text(
            "\n".join('{"source_id":"x"}' for _ in range(50)) + "\n", encoding="utf-8")
        (root / "wip-g" / "notes").mkdir()
        for i in range(50):
            (root / "wip-g" / "notes" / f"n{i}.txt").write_text("x", encoding="utf-8")
        r = {x[0]: x for x in scan(root)}
        chk("50 份 .txt 全在 notes/ 而非 raw/ → 仍报缺",
            r["wip-g"][3] and r["wip-g"][2] == 0)

        print("── ★ 正向 ②：**份数够了，字节不对**（v0.0.0.64，我自己造出来的场景）──")
        mk("wip-h", "evidence", 20, 20, corrupt=15)
        r = {x[0]: x for x in scan(root)}
        chk("20/20 份数齐 → 份数那一支不报", not r["wip-h"][3])
        chk("**但 15 份校验和对不上 → 报出**", r["wip-h"][4] == 15)

        print("── 反向对照 ⑥：字节对得上的不许报 ──")
        mk("wip-i", "evidence", 20, 20, corrupt=0)
        r = {x[0]: x for x in scan(root)}
        chk("20 份全部一致 → 校验和那一支 0", r["wip-i"][4] == 0)

        print("── 反向对照 ⑦：文件不在算「缺」，不算「字节不对」──")
        # 两者的处置不同：缺是去补，不对是去查抽取方式。混为一谈会指错修法。
        mk("wip-j", "evidence", 20, 5, corrupt=0)
        r = {x[0]: x for x in scan(root)}
        chk("20 条账本、5 份文件 → 报缺，且校验和那一支为 0",
            r["wip-j"][3] and r["wip-j"][4] == 0)

        print("── ★★ 正向 ③：**账本一条都指不到文件**（Harvey #103 的真实形态）──")
        # 账本 46 条指 `raw/src-<hash>/…`，磁盘 60 份是 `raw/s_bub_gb_…txt`。
        # 份数比较判「齐 ✓，还多 14 份」——**多出来的不是健康，是两套编号。**
        w = root / "wip-k"
        (w / "raw").mkdir(parents=True)
        (w / "source-ledger.jsonl").write_text("\n".join(
            json.dumps({"source_id": f"src-{i:012x}",
                        "local_path": f"raw/src-{i:012x}/doc_{i}.txt",
                        "checksum": hashlib.sha256(f"s{i}".encode()).hexdigest()})
            for i in range(46)) + "\n", encoding="utf-8")
        for i in range(60):
            (w / "raw" / f"s_flat_{i}.txt").write_text("x", encoding="utf-8")
        r = {x[0]: x for x in scan(root)}
        chk("46 条 / 60 份 → 份数那一支仍判「不缺」", not r["wip-k"][3])
        chk("**但解析到文件的条数是 0 → 这才是真相**", r["wip-k"][5] == 0)

        print("── 反向对照 ⑧：路径对得上时，解析条数要如实反映 ──")
        mk("wip-l", "evidence", 30, 30, corrupt=0)
        r = {x[0]: x for x in scan(root)}
        chk("30 条全部指得到 → 解析条数 30", r["wip-l"][5] == 30)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="含多个工作区的目录（如 _corpora/）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.root:
        ap.error("要么 --self-test，要么给 --root")

    rows = scan(a.root)
    if not rows:
        print(f"✗ **{a.root} 下一个工作区都没扫到——结果不可信，不是「没问题」**")
        return 3

    print(f"{'工作区':24} {'账本':>6} {'语料':>6} {'指得到':>6}  状态")
    bad, mismatched, dangling = [], [], []
    for name, n, t, miss, nbad, resolved in rows:
        if nbad:
            mismatched.append((name, nbad))
        # 账本有条目、磁盘有文件，却一条也对不上路径——**两批互不相干的东西**
        if n and t and not resolved:
            dangling.append((name, n, t))
        if n is None:
            print(f"{name:24} {'—':>6} {'—':>6}  **无账本**")
            bad.append(name)
            continue
        flag = '✓' if not miss else f'**缺 {n - t}**'
        if nbad:
            flag += f'　**字节对不上 {nbad}**'
        if n and t and not resolved:
            flag = '**账本一条都指不到文件**'
        print(f"{name:24} {n:6} {t:6} {resolved:6}  {flag}")
        if miss:
            bad.append(name)

    if mismatched:
        print(f"\n✗ **{len(mismatched)} 个工作区里有文件与账本记的校验和对不上**——"
              "**文件在，但不是账本 attest 的那一份**。"
              "份数够了不等于对：引文核查会对着另一份文本算，而这道判据会变绿：")
        for name, k in mismatched:
            print(f"    {name}　{k} 份")
        print("  修法不是改账本的校验和——**那等于让账本去迁就磁盘**。"
              "要么找回当初的抽取方式，要么重新入库并让账本记录新的校验和。")

    if dangling:
        print(f"\n✗ **{len(dangling)} 个工作区：账本有条目、磁盘有文件，"
              "却没有一条账本指得到文件**——"
              "**这两批是互不相干的东西**，份数相减毫无意义：")
        for name, n, t in dangling:
            print(f"    {name}　账本 {n} 条、磁盘 {t} 份、**指得到 0**")
        print("  份数比较会把这种情形判成「齐 ✓」甚至「还多几份」。"
              "**「多了几份」不是健康，是两套编号。**")

    if not bad and not mismatched and not dangling:
        print(f"\n  ✓ {len(rows)} 个工作区的语料都在，且字节与账本一致")
        return 0
    if bad:
        print(f"\n✗ **{len(bad)} 个工作区的语料不全**——"
              "账本、断言、文档都还在，**只有语料没了**；"
              "`primary_ratio`、引文核查、覆盖率会对着虚空算：")
        for name in bad:
            print(f"    {name}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
