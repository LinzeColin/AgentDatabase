#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓源台账生成 —— **把每人一份的 `build_*_ledger.py` 收成共享件**。

## 为什么收

本件的逻辑已经手写过两遍（Barton #117、Blackwell #118），形状完全一样，
只有数据不同。而今天刚在 `assemble_*_results.py` 上付过一次代价：
**每人一份的临时脚本不在 `scripts/` 下、不进任何门、没有自测**，
Blackwell 那次「除以 10 做两遍」就是这么活下来的。

**规矩是：出现第 2 个人要用同一段逻辑时就收成共享件，不要复制一份改三个变量。**

## 它做什么

调用方给一张**纯数据**表（每份来源一条），本件负责：

1. **落盘**：`raw/<短名>/<短名>.txt`，并按 sha256 去重
   （同一份下了两次会被跳过并报出，不是静默合并）
2. **写 9 列台账**：格式照 `_corpora/_next/LEDGER_FORMAT.md`，
   制表符分隔、第 7 列分档不许空、第 8 列归属标记恰好一个、第 9 列以 `lane=` 开头
3. **自检**：分档只许 P1/P2/S1/S2/U；道只许六条之一；归属标记恰好一个；
   短名与目录名一致——**任一条不过就退出，不写半份台账**
4. **报计量**：分档分布、道分布、**一手去重后的份数**
   （P2 是重复见证，计入 primary 但必须让人一眼看出去重后是多少）

## 它不做什么

- **不判档**。分档由调用方给，本件只校验取值合法。
  「不许在入库环节把 S1 提成 P1」那条纪律**属于调用方**，本件管不了。
- **不判道**。同上。
- **不去重内容**。sha256 相同才算重复；草稿与印本内容高度重合但字节不同，
  那是 `check_claim_source_independence` 管的事。
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import sys

TIERS = {"P1", "P2", "S1", "S2", "U"}
LANES = {"writings", "conversations", "expression", "external", "decisions", "timeline"}
ATTRIB = {"HIS-OWN", "CO-AUTHORED", "THIRD-PARTY", "ATTRIBUTION-UNCLEAR", "OTHER-INVENTOR"}
EXTRA_MARKS = {"POSTHUMOUS", "TRANSLATION", "DUPLICATE-SCAN", "OCR-POOR", "FULL-PAGE-SCAN"}


def validate(rows: list) -> list:
    """→ 问题列表；空表示都合法。**任一条不过，调用方就不该写台账。**"""
    bad, seen = [], set()
    for i, r in enumerate(rows):
        w = f"第 {i+1} 条（{r.get('short') or '无短名'}）"
        if not r.get("short"):
            bad.append(f"{w}：**短名为空**")
        elif r["short"] in seen:
            bad.append(f"{w}：**短名重复**")
        else:
            seen.add(r["short"])
        if r.get("tier") not in TIERS:
            bad.append(f"{w}：分档 `{r.get('tier')}` 不在 {sorted(TIERS)} 里")
        if r.get("lane") not in LANES:
            bad.append(f"{w}：道 `{r.get('lane')}` 不在六条道里")
        marks = set(str(r.get("mark") or "").split())
        n = len(marks & ATTRIB)
        if n != 1:
            bad.append(f"{w}：归属标记要**恰好一个**，实得 {n}（`{r.get('mark')}`）")
        if marks - ATTRIB - EXTRA_MARKS:
            bad.append(f"{w}：认不得的标记 {sorted(marks - ATTRIB - EXTRA_MARKS)}")
        if not str(r.get("why") or "").strip():
            bad.append(f"{w}：**第 9 列的依据为空**——不写依据等于没有依据")
    return bad


def row_line(r: dict) -> str:
    """→ 一行 9 列台账。第 9 列以 `lane=` 开头，权利依据以 ` RIGHTS=` 附在末尾。"""
    note = f"lane={r['lane']}. {r['why']}"
    if r.get("rights"):
        note += f" RIGHTS={r['rights']}"
    return "\t".join([r["short"], r.get("url", ""), r.get("title", ""), str(r.get("year", "")),
                      r.get("locator", ""), r.get("lang", "en"), r["tier"], r["mark"], note])


def build(rows: list, src_dir: pathlib.Path, raw_dir: pathlib.Path, header: str) -> dict:
    """落盘 + 写台账 → 计量。**校验不过就抛，不写半份。**"""
    problems = validate(rows)
    if problems:
        raise SystemExit("✗ **台账校验未过，一行都没写**：\n  " + "\n  ".join(problems[:12]))

    raw_dir.mkdir(parents=True, exist_ok=True)
    lines, seen_sha, copied, skipped = [f"# {header}"], {}, 0, 0
    for r in rows:
        src = src_dir / r["file"]
        if not src.is_file():
            print(f"  ✗ 源文件不在：{r['file']}"); skipped += 1; continue
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        if sha in seen_sha:
            print(f"  ⚠ **{r['short']} 与 {seen_sha[sha]} 逐位相同，跳过**（同一份下了两次）")
            skipped += 1; continue
        seen_sha[sha] = r["short"]
        d = raw_dir / r["short"]; d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, d / f"{r['short']}.txt"); copied += 1
        lines.append(row_line(r))

    (raw_dir / "_ids.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body = lines[1:]
    tiers, lanes = {}, {}
    for l in body:
        c = l.split("\t")
        tiers[c[6]] = tiers.get(c[6], 0) + 1
        ln = c[8].split(".")[0].replace("lane=", "")
        lanes[ln] = lanes.get(ln, 0) + 1
    p1, p2 = tiers.get("P1", 0), tiers.get("P2", 0)
    return {"落盘": copied, "跳过": skipped, "台账行数": len(body),
            "分档": tiers, "道": lanes,
            "一手（P1+P2）": p1 + p2, "其中 P2 重复见证": p2, "**去重后一手**": p1}


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    ok = {"short": "a", "file": "a.txt", "tier": "P1", "mark": "HIS-OWN",
          "lane": "writings", "why": "扉页署名"}

    print("── 正向：合法的一条不报 ──")
    chk("一条不报", not validate([ok]))

    print("── 反向对照 ①：分档不在白名单 → 报出 ──")
    chk("tier=P9 报出", any("分档" in p for p in validate([dict(ok, tier="P9")])))

    print("── 反向对照 ②：道不在六条里 → 报出 ──")
    chk("lane=misc 报出", any("六条道" in p for p in validate([dict(ok, lane="misc")])))

    print("── ★ 反向对照 ③：归属标记两个或零个都要报 ──")
    chk("两个 → 报出",
        any("恰好一个" in p for p in validate([dict(ok, mark="HIS-OWN THIRD-PARTY")])))
    chk("零个 → 报出", any("恰好一个" in p for p in validate([dict(ok, mark="POSTHUMOUS")])))
    chk("一个 + 附加标记 → **不报**（DUPLICATE-SCAN 是合法附加）",
        not validate([dict(ok, mark="HIS-OWN DUPLICATE-SCAN")]))

    print("── ★ 反向对照 ④：第 9 列依据为空 → 报出（不写依据等于没有依据）──")
    chk("why 为空 → 报出", any("依据为空" in p for p in validate([dict(ok, why="  ")])))

    print("── 反向对照 ⑤：短名重复 → 报出 ──")
    chk("两条同短名 → 报出", any("短名重复" in p for p in validate([ok, dict(ok, file="b.txt")])))

    print("── ★★ 反向对照 ⑥：校验不过时**一行都不写** ──")
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); (root / "src").mkdir(); (root / "src" / "a.txt").write_bytes(b"x")
        raw = root / "raw"
        try:
            build([dict(ok, tier="P9")], root / "src", raw, "h")
            wrote = True
        except SystemExit:
            wrote = False
        chk("抛出且 `raw/_ids.txt` 不存在", not wrote and not (raw / "_ids.txt").exists())

    print("── ★ 反向对照 ⑦：逐位相同的两份只落一份，且**报出来**不静默 ──")
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); s = root / "src"; s.mkdir()
        (s / "a.txt").write_bytes(b"same"); (s / "b.txt").write_bytes(b"same")
        info = build([ok, dict(ok, short="b", file="b.txt")], s, root / "raw", "h")
        chk(f"落盘 {info['落盘']} 份、跳过 {info['跳过']} 份、台账 {info['台账行数']} 行",
            info["落盘"] == 1 and info["跳过"] == 1 and info["台账行数"] == 1)

    print("── ★ 反向对照 ⑧：P2 计入一手，但去重后的数要单独报 ──")
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); s = root / "src"; s.mkdir()
        for n in "abc":
            (s / f"{n}.txt").write_bytes(n.encode())
        info = build([ok,
                      dict(ok, short="b", file="b.txt", tier="P2", mark="HIS-OWN DUPLICATE-SCAN"),
                      dict(ok, short="c", file="c.txt", tier="S1", mark="THIRD-PARTY")],
                     s, root / "raw", "h")
        chk(f"一手 {info['一手（P1+P2）']}、其中 P2 {info['其中 P2 重复见证']}、"
            f"去重后 {info['**去重后一手**']}",
            info["一手（P1+P2）"] == 2 and info["**去重后一手**"] == 1)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", help="纯数据的 JSON 数组，每条含 short/file/tier/mark/lane/why 等")
    ap.add_argument("--src", help="源文件所在目录")
    ap.add_argument("--raw", help="要写入的 raw/ 目录")
    ap.add_argument("--header", default="corpus ledger", help="台账首行注释")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.rows and a.src and a.raw):
        ap.error("要么 --self-test，要么给齐 --rows/--src/--raw")

    rows = json.loads(pathlib.Path(a.rows).read_text(encoding="utf-8"))
    info = build(rows, pathlib.Path(a.src), pathlib.Path(a.raw), a.header)
    for k, v in info.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
