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


def fetch_status(manifest: dict) -> dict:
    """→ {identifier: status}，取自 `raw/_fetch-manifest.json` 的 `记录`。纯函数。

    ★★★ **这才是正确的对照物。** 我第一版拿 `source-ledger.jsonl` 对，
      两边键不同（`source_id` vs `identifier`），只能靠 url 里的 IA 标识搭桥，
      命中率 994/998，还把 `wip-churchill-191`(89%) 与 `wip-plato-186`(无台账) 判成未核。
      换成抓取清单：**1051/1051，19 个工作区全中**，包括没有台账的 Plato。
      ⇒ 对「这份材料到底拿到没有」，权威记录是**抓取清单**，不是出处台账。
    """
    return {r.get("identifier"): r.get("status")
            for r in (manifest.get("记录") or []) if r.get("identifier")}


def offenders(primary: dict, status: dict, bad_values=None):
    """→ (一手总数, join 上的, [算作一手但没真拿到的条目])。纯函数。

    `bad_values` 为 None ⇒ 用抓取清单口径：**status 不是「已取回」就算**
    （实测出现过 `剔除` / `无文本层` / `失败` 三种；穷举「坏值」会漏掉下一种新值，
      所以判的是「不等于唯一那个好值」）。[[checkers-assume-a-shape-the-product-outgrows]]
    传入集合 ⇒ 用台账口径（`{"failed"}`）。
    """
    p1 = [r for r in (primary.get("明细") or []) if r.get("档") == "一手"]
    joined = [r for r in p1 if r.get("identifier") in status]
    if bad_values is None:
        bad = [r for r in joined if status.get(r.get("identifier")) != "已取回"]
    else:
        bad = [r for r in joined if status.get(r.get("identifier")) in bad_values]
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
    tot, jn, off = offenders(P, st, {"failed"})
    chk("★★★ 正例：台账标 failed 而算一手 ⇒ 报出来", len(off) == 1)
    chk("★★ 负例：抽取成功的一手 ⇒ 不报", all(o["identifier"] != "writingsofthomas01jeff" for o in off))
    chk("★★★ 负例：**二手**不判（它不进一手占比）", tot == 2 and jn == 2)
    chk("★ join 命中率算得出（本例 2/2）", jn == tot)
    # ★★ 坏 join 的反例：identifier 与台账完全对不上 ⇒ 命中率 0，**不许报「干净」**
    tot2, jn2, off2 = offenders({"明细": [{"identifier": "src-6a3cf5192354", "档": "一手"}]}, st, {"failed"})
    chk("★★★ **坏 join 的反例**：键对不上 ⇒ join 命中 0（调用方据此判未核，不是通过）",
        tot2 == 1 and jn2 == 0 and off2 == [])
    chk("★ 空输入不炸", offenders({}, {}, {"failed"}) == (0, 0, []) and ledger_status("") == {})

    # ── 抓取清单口径（本件的主口径）────────────────────────────────
    # ★ 三个 status 值**逐字取自**真清单：wip-churchill-191 的 `记录`
    FM = {"记录": [
        {"identifier": "1914frenuoft", "status": "已取回"},
        {"identifier": "theriverwar04943gut", "status": "剔除"},
        {"identifier": "synapseml_gutenberg_the_river_war", "status": "无文本层"},
    ]}
    fs = fetch_status(FM)
    P2 = {"明细": [{"identifier": i, "档": "一手"} for i in
                   ("1914frenuoft", "theriverwar04943gut", "synapseml_gutenberg_the_river_war")]}
    t3, j3, o3 = offenders(P2, fs)
    chk("★★★ 正例：`剔除` 与 `无文本层` 都算「没真拿到」⇒ 报 2 条", len(o3) == 2 and j3 == 3)
    chk("★★ 负例：`已取回` 不报", all(x["identifier"] != "1914frenuoft" for x in o3))
    chk("★★★ **判「不等于已取回」而不是穷举坏值** —— 出现没见过的新 status 也要报",
        len(offenders({"明细": [{"identifier": "x", "档": "一手"}]},
                      {"x": "某种以后才有的状态"})[2]) == 1)
    chk("★ `fetch_status` 跳过没有 identifier 的记录",
        fetch_status({"记录": [{"status": "已取回"}]}) == {} and fetch_status({}) == {})
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

    print("口径①（主）：`raw/_fetch-manifest.json` 的 `记录[].status` —— "
          "**不等于「已取回」就是没真拿到**")
    print("口径②（附）：`evidence/source-ledger.jsonl` 的 `extraction_status == failed`\n")
    print("%-22s %6s %7s %7s %6s %7s %12s" % ("工作区", "一手", "①join", "①违规", "②join", "②违规", "★缺的词数"))
    tot = j1 = j2 = o1 = o2 = 0
    words = 0
    unchecked, rows = [], []
    for f in files:
        ws = f.parent.parent
        name = next((p for p in ws.parts if p.startswith("wip-")), ws.name)
        prim = json.loads(f.read_text(encoding="utf-8"))
        # 口径①
        fm = ws / "raw" / "_fetch-manifest.json"
        if fm.is_file():
            fs = fetch_status(json.loads(fm.read_text(encoding="utf-8")))
            t, ja, offa = offenders(prim, fs)
        else:
            t, ja, offa = len([r for r in (prim.get("明细") or []) if r.get("档") == "一手"]), None, []
            unchecked.append((name, "没有 `raw/_fetch-manifest.json` ⇒ 口径① **未核**"))
        # 口径②
        led = ws / "evidence" / "source-ledger.jsonl"
        if led.is_file():
            ls = ledger_status(led.read_text(encoding="utf-8", errors="replace"))
            _t, jb, offb = offenders(prim, ls, {"failed"})
        else:
            jb, offb = None, []
            unchecked.append((name, "没有 `evidence/source-ledger.jsonl` ⇒ 口径② **未核**"))
        for tag, off in (("①", offa), ("②", offb)):
            for o in off:
                w = o.get("words") or 0
                rows.append((tag, name, o.get("identifier"), (o.get("title") or "")[:34], w))
                if tag == "①":
                    words += w
        tot += t; j1 += ja or 0; j2 += jb or 0; o1 += len(offa); o2 += len(offb)
        rate = lambda j: ("%5.0f%%" % (100.0 * j / t)) if (j is not None and t) else "  未核"
        print("  %-20s %6d %7s %7d %6s %7d %12s%s"
              % (name, t, rate(ja), len(offa), rate(jb), len(offb),
                 f"{sum(o.get('words') or 0 for o in offa):,}", "  ← ★" if (offa or offb) else ""))
        if ja is not None and t and (ja / t) < a.min_join:
            unchecked.append((name, "口径① join 命中率只有 %.0f%%（阈值 %.0f%%）—— "
                                    "键对不上时「0 违规」是坏 join 的假干净" % (100 * ja / t, 100 * a.min_join)))

    print("\n合计一手 **%d**｜①join %d（%.1f%%）**违规 %d**｜②join %d（%.1f%%）**违规 %d**"
          % (tot, j1, 100.0 * j1 / tot if tot else 0, o1, j2, 100.0 * j2 / tot if tot else 0, o2))
    print("★ 口径①违规的这些材料合计 **%s 词** —— 它们**从没进过语料**，却在一手计数里。" % f"{words:,}")
    for n_, why in unchecked:
        print("   · %-20s %s" % (n_, why))
    if not rows:
        print("\n✓ 一手计数里没有「没真拿到」的材料" + ("（但上面有未核项，不算全通过）" if unchecked else ""))
        return 0
    print("\n✗ **算作一手、而实际没拿到 —— %d 条**：" % len(rows))
    for a_ in rows:
        print("   %s %-20s %-30s %-34s %s 词" % (a_[0], a_[1], str(a_[2])[:30], a_[3], a_[4]))
    print("\n  ★ 处置：**先看它是不是已判分**（`evals/results.jsonl` **非空**才算，")
    print("    文件存在不算 —— ㊵ 冻结的不动，记档即可）；未判分的重跑 `classify_primary.py`。")
    print("  ★★ 影响的是**一手占比**这条分母。2026-08-18 实测那 4 条：")
    print("    churchill 19→17（0.826→0.810）、dewey 40→39、ford 17→16 ——")
    print("    **三个人都没跨过任何门，是口径缺陷不是分数缺陷。** 报数时要一起说。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
