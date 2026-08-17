#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_primary_excludes_failed_extraction.py —— **台账说抽取失败，一手计数里却还有它**

## 抓到它的那一次（2026-08-18，Jefferson #175）

`raw/_primary.json`：

    {"identifier": "version-final-de-la-declaracion-de-la-independencia",
     "档": "一手", "title": "Versión Final De La Declaración De La Independencia",
     "creator": "Jefferson Thomas (1743-1826)", "words": 0}

同一份材料在 `evidence/source-ledger.jsonl` 里：

    {"source_id": "src-6a3cf5192354", "extraction_status": "failed", "words": null, …}

**台账知道它是空的，一手计数不知道。** 已裁的「抽取失败的源不再算进覆盖数」
（#119，Jefferson 26→25）落在 `check_profile_declared.py` 上 —— 那件读的是**台账**；
而 `_primary.json` 是**另一条链**，同一条规则在这条链上**没有执行者**。
[[one-requirement-two-consumers]]｜[[every-requirement-needs-an-owner]]

## ★★★ 两个产物的 join 键**不一样** —— 第一版我据此报了「全库 0 条」

    台账          `source_id`: "src-6a3cf5192354"      ← 本地编号
    _primary.json `identifier`: "version-final-de-…"    ← IA 的标识

两边**没有共用字段**。按 `identifier` 直接 join ⇒ 一条也对不上 ⇒ 报「全库 0 条干净」。
**一个坏 join 给出的是干净答案，不是报错。**
唯一的桥是台账 `url` 里的 `archive.org/download/<identifier>`。
按它重做之后：998 条一手里 **994 条（99.6%）对得上**，命中 **1 条**。
⇒ 本件**必须印出 join 命中率**；对不上的比例一高，结论就不成立。
[[zero-hit-gates-must-prove-they-can-hit]]｜[[read-the-hits-before-reporting-the-rate]]

## 射程

只判**一手**那一档（二手不进一手占比，不影响档位）。
没有台账的工作区**报「未核」，不算通过**（实测 19 个里有 1 个：`wip-plato-186`
停在阶段 2，还没建台账 —— 而那正是判据最容易漏掉的一类）。

退出码：0＝没有；1＝有；4＝一份 `_primary.json` 都没有（未量）。
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
IA_ID = re.compile(r"archive\.org/(?:download|details)/([^/?#\s\"']+)")


def ledger_status(ledger_text: str) -> dict:
    """→ {IA identifier: extraction_status}。纯函数。

    ★ 台账里没有 `identifier` 字段，只有 `source_id`（本地编号）与 `url`。
      桥只能从 url 里取。整行扫，因为 url 可能出现在 `url` / `local_path` / 派生字段里。
    """
    out = {}
    for line in (ledger_text or "").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        blob = json.dumps(r, ensure_ascii=False)
        for m in IA_ID.finditer(blob):
            out[m.group(1)] = r.get("extraction_status")
    return out


def offenders(primary: dict, status: dict):
    """→ (一手总数, join 上的, [台账标 failed 却算一手的条目])。纯函数。"""
    p1 = [r for r in (primary.get("明细") or []) if r.get("档") == "一手"]
    joined = [r for r in p1 if r.get("identifier") in status]
    bad = [r for r in joined if status.get(r.get("identifier")) == "failed"]
    return len(p1), len(joined), bad


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    # ★ 台账行**逐字取自** wip-jefferson-175（只截了字段，值没改）
    LED = ('{"source_id": "src-6a3cf5192354", "extraction_status": "failed", "words": null,'
           ' "url": "https://archive.org/download/version-final-de-la-declaracion-de-la-independencia/x.pdf"}\n'
           '{"source_id": "src-000000000001", "extraction_status": "ok", "words": 119065,'
           ' "url": "https://archive.org/download/writingsofthomas01jeff/y.pdf"}\n')
    st = ledger_status(LED)
    chk("★★★ 桥只能从 url 取：两条都解析出 IA identifier", len(st) == 2)
    chk("★★ failed 与 ok 分得开",
        st.get("version-final-de-la-declaracion-de-la-independencia") == "failed"
        and st.get("writingsofthomas01jeff") == "ok")
    P = {"明细": [
        {"identifier": "version-final-de-la-declaracion-de-la-independencia", "档": "一手", "words": 0},
        {"identifier": "writingsofthomas01jeff", "档": "一手", "words": 119065},
        {"identifier": "somebodyelse00xxxx", "档": "二手", "words": 5000},
    ]}
    tot, jn, off = offenders(P, st)
    chk("★★★ 正例：台账标 failed 而算一手 ⇒ 报出来", len(off) == 1)
    chk("★★ 负例：抽取成功的一手 ⇒ 不报", all(o["identifier"] != "writingsofthomas01jeff" for o in off))
    chk("★★★ 负例：**二手**不判（它不进一手占比）", tot == 2 and jn == 2)
    chk("★ join 命中率算得出（本例 2/2）", jn == tot)
    # ★★ 坏 join 的反例：identifier 与台账完全对不上 ⇒ 命中率 0，**不许报「干净」**
    tot2, jn2, off2 = offenders({"明细": [{"identifier": "src-6a3cf5192354", "档": "一手"}]}, st)
    chk("★★★ **坏 join 的反例**：键对不上 ⇒ join 命中 0（调用方据此判未核，不是通过）",
        tot2 == 1 and jn2 == 0 and off2 == [])
    chk("★ 空输入不炸", offenders({}, {}) == (0, 0, []) and ledger_status("") == {})
    chk("★ 台账里的坏行跳过、不中断", len(ledger_status('{"bad json\n' + LED)) == 2)
    chk("★★ `details/` 形式的 url 也认（不是只认 download/）",
        "abc123" in ledger_status('{"url": "https://archive.org/details/abc123"}\n'))
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora", default=None)
    ap.add_argument("--min-join", type=float, default=0.90,
                    help="join 命中率低于此值 ⇒ 该工作区判**未核**，不算通过（默认 0.90）")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    corp = pathlib.Path(a.corpora or (HERE.parents[1] / "_corpora"))
    files = sorted(corp.glob("wip-*/**/raw/_primary.json"))
    print("扫描面：%s" % corp)
    if not files:
        print("★ **未量，不是通过**（rc=4）—— 一份 `_primary.json` 都没有")
        return 4
    print("`_primary.json` **%d** 份\n" % len(files))

    print("%-24s %6s %8s %7s %8s" % ("工作区", "一手", "join 上", "命中率", "★ 违规"))
    tot = jn_tot = off_tot = 0
    unchecked, rows = [], []
    for f in files:
        ws = f.parent.parent
        name = next((p for p in ws.parts if p.startswith("wip-")), ws.name)
        led = ws / "evidence" / "source-ledger.jsonl"
        if not led.is_file():
            unchecked.append((name, "没有 `evidence/source-ledger.jsonl`（多半停在建台账之前）"))
            print("  %-22s %6s %8s %7s %8s  ← **未核**" % (name, "—", "—", "—", "—"))
            continue
        st = ledger_status(led.read_text(encoding="utf-8", errors="replace"))
        t, j, off = offenders(json.loads(f.read_text(encoding="utf-8")), st)
        rate = (j / t) if t else 0.0
        tot += t; jn_tot += j; off_tot += len(off)
        if t and rate < a.min_join:
            unchecked.append((name, "join 命中率只有 %.0f%%（阈值 %.0f%%）—— 键对不上时"
                                    "「0 违规」是坏 join 的假干净" % (100 * rate, 100 * a.min_join)))
            print("  %-22s %6d %8d %6.0f%% %8s  ← **未核**" % (name, t, j, 100 * rate, "—"))
            continue
        print("  %-22s %6d %8d %6.0f%% %8d%s"
              % (name, t, j, 100 * rate, len(off), "  ← ★" if off else ""))
        for o in off:
            rows.append((name, o.get("identifier"), (o.get("title") or "")[:44], o.get("words")))

    print("\n合计一手 **%d**｜join 上 **%d**（%.1f%%）｜**违规 %d**｜未核 %d 个工作区"
          % (tot, jn_tot, 100.0 * jn_tot / tot if tot else 0, off_tot, len(unchecked)))
    for n_, why in unchecked:
        print("   · %-20s %s" % (n_, why))
    if not rows:
        if unchecked:
            print("\n★ 已核的部分没有违规 —— **但上面那些是未核的，不算通过**")
        else:
            print("\n✓ 没有「台账标抽取失败却算进一手」的")
        return 0
    print("\n✗ **台账标 `extraction_status=failed`，而一手计数里还有它 —— %d 条**：" % len(rows))
    for a_ in rows:
        print("   · %-20s %-46s %-44s %s 词" % (a_[0], str(a_[1])[:46], a_[2], a_[3]))
    print("\n  ★ 处置：**先看它是不是已判分**（㊵ 冻结的不动，记档即可）；")
    print("    未判分的重跑 `classify_primary.py` 并把 `extraction_status` 纳入判定。")
    print("  ★★ 影响的是**一手占比**这条分母，档位（quick/standard/deep）可能因此变。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
