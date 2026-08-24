#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这份文件里，真的有那句署名吗**——用作品自己的特征词回查它自己的载体。

## 为什么有这件

#125 Mendel 抓源时存盘用 `p[:8]` 截断 UUID 当文件名。
同一期报纸里两页的 pid 前 8 位都是 `uuid:dd0`，**后写的音乐会评论页把讣闻页覆盖了**。

于是 `bz1884_0107_uuid:dd0.txt` 这个「1884-01-07 死讯」的载体里，
**正文是一篇音乐会评论**，唯一的 `Mendel` 命中是 `Mendelssohn's Schottische Symphonie`。

**三道判据全部放行：**

| 判据 | 结果 | 为什么看不见 |
|---|---|---|
| `check_ocr_legibility` 花体自查 | 0.1252 / 0.0000 **过** | 那一页德文确实干净——**只是内容是别的** |
| `sha256` 逐位判重 | **过** | 文件不重复，只是**装错了东西** |
| 抓源方自己的「`Mendel` 是否出现」检查 | **过** | 命中的是 **Mendelssohn** |

**抓出它的是拿该件自己的特征词回查载体**：`gestorben`／`Herzleiden` 两个词一查就露。

★ 这是「判据绿了但指错了文件」的**第 17 起**，而形态是新的：
前 16 起是**命令跑在错的条件下**，这一起是**文件名截断造成同名覆盖**——
`p[:8]` 在 UUID 上根本不足以区分。

## 判据形状

对每条来源，取它**自己记录里的证据串**（署名照录 `byline_verbatim`／
`attribution` 字段／台账第 9 列里引的原文），
从中抽出**特征词**，回到 `carrier_file` 里搜。**命中 0 → 指错文件。**

### 什么算「特征词」

- **长度 ≥4 的词**，且**不是**目标人物的姓名本身
  （★ 姓名恰恰是最会骗人的那个：`Mendel` 命中了 `Mendelssohn`）
- 优先取**罕见词**：证据串里最长的那几个

## 射程边界

- **只判「这份文件里有没有这句话」**，不判「这句话是不是真的出自他」——
  后者是 `check_authorship`／`attribution_basis` 的事。
- **证据串本身若是编的，本件抓不到**——它只核「文件对不对得上记录」。
- 命中 0 **不等于**文件坏了：也可能是 OCR 把那个词拼坏了。
  所以报的是「**对不上，去看一眼**」，不是「文件是错的」。
- ★★ **证据串若把变音字母转写过，本件会变弱**。#125 Mendel 的 TSV 把
  `über` 写成 `ueber`、`Prälat` 写成 `Praelat`，而载体里是原字形——
  实测 `ueber` 命中 **0**，`Versuche`/`Pflanzen`/`Hybriden` 命中 107/266/90。
  **只要还有一个词命中就判 ok，所以这次没假阴**；
  但**若某件的特征词恰好全带变音字母，它会被误报成「指错文件」。**
  真要收紧，得先把两侧都做变音归一——**那是另一件事，本件不做，只把风险写在这里。**
"""
import argparse
import json
import pathlib
import re
import sys

_WORD = re.compile(r"[A-Za-zÄÖÜäöüßÀ-ÿ]{4,}")


def salient_words(evidence: str, subject_name: str = "", k: int = 6) -> list:
    """→ 证据串里最长的 k 个词，**排除目标人物姓名的各部分**。

    ★ 排除姓名是本件的要害：Mendel 那次，`Mendel` 命中的是 `Mendelssohn`。
    **用人名去核「是不是这个人的文件」，正好会被同源词骗到。**
    """
    bad = {p.lower() for p in re.split(r"[\s,.]+", subject_name or "") if len(p) >= 3}
    words = [w for w in _WORD.findall(evidence or "") if w.lower() not in bad]
    seen, out = set(), []
    for w in sorted(words, key=len, reverse=True):
        if w.lower() in seen:
            continue
        seen.add(w.lower())
        out.append(w)
        if len(out) >= k:
            break
    return out


def check_one(evidence: str, carrier_text: str, subject_name: str = "") -> dict:
    words = salient_words(evidence, subject_name)
    if not words:
        return {"verdict": "no-salient-words", "words": [], "hits": {}}
    hits = {w: carrier_text.count(w) for w in words}
    n_hit = sum(1 for v in hits.values() if v)
    return {"verdict": "ok" if n_hit else "**not-in-carrier**",
            "words": words, "hits": hits, "命中的词数": n_hit}


def from_workspace(target: pathlib.Path, subject: str = "") -> dict:
    """★ 直接吃**工作区自己已有的产物**，不需要外部 TSV。

    - 证据串：`meta.json:attribution_basis.covered_sources` 里每条的
      「`原文件名 ｜ 署名照录：…`」
    - 载体：`evidence/source-ledger.jsonl` 里同名记录的 `local_path`

    这两样是 v0.0.0.106 之后每个 historical 人物都会有的，
    **所以本件能在研究门里真跑，而不是等人手工喂表。**
    """
    meta_f, led_f = target / "meta.json", target / "evidence/source-ledger.jsonl"
    if not meta_f.is_file() or not led_f.is_file():
        return {"状态": "meta.json 或 source-ledger.jsonl 不在——**未核（不是通过）**"}
    meta = json.loads(meta_f.read_text(encoding="utf-8"))
    subject = subject or meta.get("name") or meta.get("target_name") or ""
    covered = ((meta.get("attribution_basis") or {}).get("covered_sources")) or []
    if not covered:
        return {"状态": "`attribution_basis.covered_sources` 为空——**未核（不是通过）**"}
    by_name = {}
    for line in led_f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:                                    # noqa: BLE001
            continue
        if r.get("original_name"):
            by_name[r["original_name"]] = r
    rows, bad, skipped = [], 0, []
    for entry in covered:
        s = str(entry)
        name = s.split("｜")[0].strip()
        rec = by_name.get(name)
        if rec is None or not rec.get("local_path"):
            skipped.append({"covered_sources 条目": s[:70], "原因": "账本里找不到同名记录"})
            continue
        f = target / rec["local_path"]
        if not f.is_file():
            skipped.append({"covered_sources 条目": s[:70], "原因": "载体文件不在盘上"})
            continue
        res = check_one(s, f.read_text(encoding="utf-8", errors="ignore"), subject)
        res["original_name"] = name
        bad += res["verdict"] == "**not-in-carrier**"
        rows.append(res)
    return {"核过": len(rows), "**指错文件**": bad,
            "对不上的": [x for x in rows if x["verdict"] != "ok"],
            "★ 没核的": skipped,
            "★ 射程": "只判「这份文件里有没有这句话」；证据串本身是编的，本件抓不到"}


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    ev = "(† Gregor Mendel, Prälat.) … ist der Abt und Prälat gestorben. " \
         "Schon vor längerer Zeit von einem Herzleiden befallen"
    good = "In der Nacht ist der Abt und Prälat des Augustinerstiftes gestorben. " \
           "Schon vor längerer Zeit von einem Herzleiden befallen worden."
    # ★ 就是那份真的被覆盖的内容：一篇音乐会评论，只含 Mendelssohn
    wrong = "Das Concert brachte Mendelssohn's Schottische Symphonie zur Auffuehrung. " \
            "Das Publikum war zahlreich erschienen und spendete reichen Beifall."

    print("── 正向：载体里真有那句话 → ok ──")
    r = check_one(ev, good, "Gregor Mendel")
    chk(f"{r['verdict']}　命中 {r.get('命中的词数')} 个词", r["verdict"] == "ok")
    print("── ★★ 反向对照①：**那份被覆盖的音乐会评论必须报出来** ──")
    r2 = check_one(ev, wrong, "Gregor Mendel")
    chk(f"{r2['verdict']}　{r2['hits']}", r2["verdict"] == "**not-in-carrier**")
    print("── ★★ 反向对照②：**不许用人名去核**（Mendel 会命中 Mendelssohn）──")
    chk(f"特征词里没有 Mendel：{r2['words']}",
        all("mendel" not in w.lower() for w in r2["words"]))
    chk("★ 若允许人名，这份错文件会被判为 ok（证明排除姓名是必需的）",
        check_one("Mendel", wrong, "")["verdict"] == "ok")
    print("── ★ 反向对照③：证据串没有可用特征词 → 说出来，不算通过 ──")
    r3 = check_one("Gregor Mendel", "irgendein Text", "Gregor Mendel")
    chk(f"{r3['verdict']}", r3["verdict"] == "no-salient-words")
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", help="工作区目录（直接吃 meta.json + source-ledger.jsonl）")
    ap.add_argument("table", nargs="?",
                    help="TSV，需含 short / byline_verbatim / carrier_file 三列")
    ap.add_argument("--root", help="carrier_file 的所在目录")
    ap.add_argument("--subject", default="", help="目标人物姓名（用于把姓名排除出特征词）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.target:
        info = from_workspace(pathlib.Path(a.target), a.subject)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 1 if info.get("**指错文件**") else 0
    if not (a.table and a.root):
        ap.error("要么 --self-test，要么 --target 工作区，要么给 TSV 与 --root")
    import csv
    root = pathlib.Path(a.root)
    rows, bad, skipped = [], 0, []
    with open(a.table, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            cf = (r.get("carrier_file") or "").strip()
            f = root / cf
            if not cf or not f.is_file():
                skipped.append({"short": r.get("short"), "carrier_file": cf,
                                "原因": "载体文件不在盘上"})
                continue
            res = check_one(r.get("byline_verbatim", ""),
                            f.read_text(encoding="utf-8", errors="ignore"), a.subject)
            res["short"] = r.get("short")
            res["carrier_file"] = cf
            bad += res["verdict"] == "**not-in-carrier**"
            rows.append(res)
    print(json.dumps({"核过": len(rows), "**指错文件**": bad,
                      "对不上的": [x for x in rows if x["verdict"] != "ok"],
                      "★ 没核的（载体不在盘上）": skipped,
                      "★ 射程": "只判「这份文件里有没有这句话」；证据串本身是编的，本件抓不到"},
                     ensure_ascii=False, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
