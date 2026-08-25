#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**文件名里的四位年份 vs 台账 `published_at`** —— 两边不一致就说明至少有一处记错了。

## 撞出它的那一次（2026-08-10）

在 Virchow 上查一件别的事时看见：`cellularpath-1858-de-gutenberg.txt`
的台账 `published_at` 写的是 **1871**。文件名说 1858、台账说 1871，
**必有一处是错的**。去读文件自己印的字：`Vierte Auflage. Berlin, 1871.`，
且全篇前 9000 字**没有出现过 1858** —— 台账对，文件名错。

顺手全库扫了一遍：**1262 行两边都有年份，56 行不一致（4.4%），涉及 12 个工作区。**

## ★★ 为什么这不只是难看：`published_at` 是 PD 判定的输入

本项目只取公有领域（出版于 ≤1930）。那 56 条里 **5 条跨过 1931 分界**，
逐份读原文之后定案，其中**两条是台账错了**：

| 文件 | 台账 | 文件自己印的字 | 定案 |
|---|---|---|---|
| `b_vie_oeuvre_semmelweis_1924` | 1938 | `IMPRIMERIE FRANCIS SIMON … 1924` | **台账错 → 1924** |
| `x_holmes_medical_essays_1842_1882` | 1934 | `Copyright, 1892, BY HOUGHTON, MIFFLIN & CO.` | **台账错 → 1892** |

两条错的方向都是**把合规的 PD 源标成非 PD**——不会放进不该放的东西，
但会让 PD 审计报出并不存在的违规，而人会照着那个假违规去换源。

## 它判什么、不判什么

- **只判「两边对不上」，不判哪一边对。** 判据没有读原文的能力，
  哪一边错必须由人去看题名页。报文里两个数都给出来。
- **差 1 年单独归一类**：刊期年与出版年差一年是常态（`asme-v36-1914-…` 台账 1915），
  多半不是错。默认**只把差 ≥2 年的算问题**，`--strict` 才把差 1 年也算上。
- **跨 PD 分界的单独升级**：一边 ≤1930 一边 ≥1931 的，无论差几年都报出来，
  因为那一条会直接改变「这份源能不能用」的结论。
- **文件名里的年份未必是出版年**：`in.ernet.dli.2015.43651_…` 里的 2015 是
  Internet Archive 的数字化编号，`paton-1916-1931-timeline-…` 是年份区间。
  所以本判据**只报不拦**，它给的是「去看一眼」的名单，不是判决。

★ 一个已知的假阳来源：文件名里有多个年份时（区间、丛书年、编号），
本判据只要 `published_at` 命中**其中任一个**就算一致；命中不了才报。

退出码：0 = 无不一致；1 = 有；2 = 自测未过；3 = 用法错误。
"""
import argparse
import json
import pathlib
import re
import sys

YEAR = re.compile(r"(?<!\d)(1[5-9]\d\d|20[0-2]\d)(?!\d)")
PD_CUTOFF = 1931          # 公有领域 = 出版于 ≤1930，即「1931 年以前」


def scan_rows(rows: list[dict], strict: bool = False) -> dict:
    """→ {'不一致': [...], '差一年': [...], '跨PD分界': [...], '两边都有年份': n}"""
    out = {"不一致": [], "差一年": [], "跨PD分界": [], "两边都有年份": 0, "有一边没年份": 0}
    for r in rows:
        nm = pathlib.PurePath(str(r.get("local_path") or "")).name
        ys = [int(y) for y in YEAR.findall(nm)]
        pa = str(r.get("published_at") or "")[:4]
        if not ys or not pa.isdigit():
            out["有一边没年份"] += 1
            continue
        out["两边都有年份"] += 1
        pa = int(pa)
        if pa in ys:
            continue
        gap = min(abs(y - pa) for y in ys)
        item = {"source_id": r.get("source_id"), "文件名": nm,
                "文件名里的年份": ys, "台账 published_at": pa, "差": gap}
        straddles = len({pa < PD_CUTOFF} | {y < PD_CUTOFF for y in ys}) > 1
        if straddles:
            item["★"] = (f"**跨 PD 分界（{PD_CUTOFF}）**：一边 ≤{PD_CUTOFF-1} 一边 ≥{PD_CUTOFF}，"
                         "这一条会直接改变「这份源能不能用」——**必须去读题名页定案**")
            out["跨PD分界"].append(item)
        elif gap == 1:
            item["★"] = "差 1 年——刊期年与出版年之别是常态，多半不是错"
            (out["不一致"] if strict else out["差一年"]).append(item)
        else:
            out["不一致"].append(item)
    return out


def evaluate(target: pathlib.Path, strict: bool = False) -> tuple[list[str], dict]:
    led = target / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        return [], {"状态": f"没有 {led}，**未核验**（不是通过）"}
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    res = scan_rows(rows, strict)
    problems = []
    if res["跨PD分界"]:
        problems.append(
            f"**{len(res['跨PD分界'])} 条的文件名年份与 `published_at` 跨过 PD 分界**"
            f"（{', '.join(str(x['source_id']) for x in res['跨PD分界'][:6])}）"
            " —— 这一类会改变「能不能用」的结论，**必须逐份读题名页定案**")
    if res["不一致"]:
        problems.append(
            f"{len(res['不一致'])} 条文件名年份与 `published_at` 差 ≥2 年"
            f"（{', '.join(str(x['source_id']) for x in res['不一致'][:6])}）"
            " —— **至少有一处记错了**；判据不知道是哪一处，去看题名页")
    info = {k: (len(v) if isinstance(v, list) else v) for k, v in res.items()}
    info["**逐条**"] = res["跨PD分界"] + res["不一致"]
    info["★ 射程"] = ("只判「两边对不上」，**不判哪一边对**；文件名里的年份未必是出版年"
                      "（Internet Archive 编号、年份区间、丛书年都会混进来）；**只报不拦**。")
    return problems, info


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    R = lambda p, y: {"source_id": "src-x", "local_path": p, "published_at": y}
    # ① 一致 → 不报
    r = scan_rows([R("raw/a/book-1899.txt", "1899")])
    chk("① 文件名与台账同为 1899 → 不报", not r["不一致"] and not r["跨PD分界"])
    # ② 差 1 年 → 默认归「差一年」，不算问题
    r = scan_rows([R("raw/a/asme-v36-1914-x.txt", "1915")])
    chk("② 差 1 年 → 默认不算问题（刊期 vs 出版年）", not r["不一致"] and len(r["差一年"]) == 1)
    # ③ --strict 下差 1 年要算
    r = scan_rows([R("raw/a/asme-v36-1914-x.txt", "1915")], strict=True)
    chk("③ --strict 下差 1 年 → 要算", len(r["不一致"]) == 1)
    # ④ 差 13 年 → 报
    r = scan_rows([R("raw/a/cellularpath-1858-de-gutenberg.txt", "1871")])
    chk("④ 1858 vs 1871（真实例）→ 报", len(r["不一致"]) == 1)
    # ⑤ ★ 跨 PD 分界 → 单独升级，**哪怕只差 6 年**
    r = scan_rows([R("raw/a/b_vie_oeuvre_semmelweis_1924.txt", "1938")])
    chk("⑤ 1924 vs 1938 跨 1931 分界 → 归「跨PD分界」而不是普通不一致",
        len(r["跨PD分界"]) == 1 and not r["不一致"])
    # ⑥ ★★ 反例：跨分界但**只差 1 年**，也必须报（不能被「差一年」那条规则吃掉）
    r = scan_rows([R("raw/a/x-1930.txt", "1931")])
    chk("⑥ **1930 vs 1931 只差 1 年却跨分界 → 仍必须报**（差一年的豁免不能盖过它）",
        len(r["跨PD分界"]) == 1 and not r["差一年"])
    # ⑦ 文件名多个年份，台账命中其一 → 不报
    r = scan_rows([R("raw/a/fam-985-1849-1872.txt", "1872")])
    chk("⑦ 文件名有 1849/1872、台账 1872 → 命中其一即不报", not r["不一致"])
    # ⑧ 一边没年份 → 不判（不是通过，是没得判）
    r = scan_rows([R("raw/a/notes-on-nursing.txt", "1860")])
    chk("⑧ 文件名无年份 → 计入「有一边没年份」，不报", r["有一边没年份"] == 1 and not r["不一致"])
    # ⑨ ★ 真实假阳：Internet Archive 编号
    r = scan_rows([R("raw/a/in.ernet.dli.2015.43651_eminent-persons-vol4.txt", "1893")])
    chk("⑨ 文件名里的 2015 是 IA 编号 → 判据仍会报（**已知假阳，射程里写明了**）",
        len(r["跨PD分界"]) == 1)

    # ══════════════════════════════════════════════════════════════
    # ⑩ `evaluate()` 本身——**2026-08-12 之前它一次也没被自测进入过**
    # ══════════════════════════════════════════════════════════════
    #
    # 上面 ①–⑨ 全在考 `scan_rows`（纯函数），而 `evaluate()` 才是
    # **从磁盘读账本、拼出给人看的那句判决**的那一段。
    # 用 `sys.settrace` 逐件量过：本件在「判定函数没被自测进入」的名单里。
    #
    # ★ 补它的直接动机是 #172 Brandeis：他的 `decisions` 道要取 U.S. Reports 合订本，
    #   而 **archive.org 那批件的 `date` 字段一律是 `1754-01-01`**（265/282 卷实测）。
    #   谁照它填 `published_at`，全库会多出一批 1754 年的伪年份——
    #   **而挡这一类的就是本判据**。它自己没被自测跑过，等于那道防线没验过。
    import tempfile as _tf

    def _mk(td, rows):
        ws = pathlib.Path(td)
        (ws / "evidence").mkdir(parents=True, exist_ok=True)
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8")
        return ws

    with _tf.TemporaryDirectory() as td:
        # ⑩a ★ Brandeis 的真实形状：卷号文件名 + 被 archive.org 的 1754 污染的 published_at
        ws = _mk(td + "/a", [{"source_id": "s1",
                              "local_path": "raw/unitedstatesrepo0281unse_1930.txt",
                              "published_at": "1754-01-01"}])
        problems, info = evaluate(ws)
        # ★★★ **我第一版把这条的预期写错了**：以为 1754 会触发「跨 PD 分界」。
        #   去读实际输出才明白：**1754 与 1930 都 < 1931，两边同侧，不跨界**，
        #   它落进的是「差 ≥2 年」那一栏（差 176 年）。判据是对的，错的是我的预期。
        #   ⇒ 这一条**对 #172 的抓源指令是个更正**：archive.org 的 1754 污染
        #     在 **≤1930 的卷上只会报「差 ≥2 年」**，不会触发 PD 警报；
        #     **只有当真实年份 ≥1931 时才跨界**（见下面 ⑩a″）。
        chk("⑩a 1754 伪年份 vs 文件名 1930 → 报「差 ≥2 年」（两边同在 PD 内，不跨界）",
            len(problems) == 1 and "差 ≥2 年" in problems[0]
            and info["跨PD分界"] == 0 and info["不一致"] == 1)
        chk("⑩a′ 且 info 里逐条列出了 source_id", any(
            x.get("source_id") == "s1" for x in info["**逐条**"]))

        # ⑩a″ 真正跨界的形状：文件名 1932 而台账被填成 1754 → **必须报跨 PD 分界**
        ws2 = _mk(td + "/a2", [{"source_id": "s1b",
                                "local_path": "raw/unitedstatesrepo0286unse_1932.txt",
                                "published_at": "1754-01-01"}])
        problems2, info2 = evaluate(ws2)
        chk("⑩a″ 文件名 1932 vs 台账 1754 → **跨 PD 分界**（这一条会改变能不能用）",
            info2["跨PD分界"] == 1 and any("跨过 PD 分界" in s for s in problems2))

        # ⑩b 正对照：两边一致 → 一句都不报
        ws = _mk(td + "/b", [{"source_id": "s2", "local_path": "raw/x_1914.txt",
                              "published_at": "1914-05-01"}])
        problems, _ = evaluate(ws)
        chk("⑩b 两边年份一致 → 不报", problems == [])

        # ⑩c ★★ **账本不存在时必须明说「未核验」，不许静默当通过**
        problems, info = evaluate(pathlib.Path(td) / "nope")
        chk("⑩c 没有账本 → 明写「未核验（不是通过）」而不是空过",
            problems == [] and "未核验" in str(info.get("状态", "")))

        # ⑩d 差 1 年默认不算问题，`--strict` 才算——两个方向都验
        rows = [{"source_id": "s3", "local_path": "raw/y_1929.txt",
                 "published_at": "1930-01-01"}]
        p0, _ = evaluate(_mk(td + "/d0", rows), strict=False)
        p1, _ = evaluate(_mk(td + "/d1", rows), strict=True)
        chk("⑩d 差 1 年：默认不报", p0 == [])
        chk("⑩d′ 差 1 年：--strict 报", len(p1) == 1)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--strict", action="store_true", help="差 1 年也算问题")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要么 --self-test，要么给 workspace")
    problems, info = evaluate(pathlib.Path(a.workspace), a.strict)
    if a.json:
        print(json.dumps({"problems": problems, "info": info}, ensure_ascii=False, indent=2))
    else:
        print(f"{pathlib.Path(a.workspace).name}：两边都有年份 {info.get('两边都有年份')}"
              f"｜不一致 {info.get('不一致')}｜差一年 {info.get('差一年')}"
              f"｜**跨 PD 分界 {info.get('跨PD分界')}**")
        for p in problems:
            print("  ✗ " + p)
        for x in info.get("**逐条**", [])[:10]:
            print(f"     {x['source_id']}  文件名 {x['文件名里的年份']} vs 台账 {x['台账 published_at']}"
                  f"  差 {x['差']}   {x['文件名'][:46]}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
