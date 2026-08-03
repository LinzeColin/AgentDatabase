#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#109 Virchow 逐份入库。读 `raw/_ids.txt`，按其判定调 ingest.py。

## 三条口径（照抄，别自行发挥）

- **`mixed` 一律记 `U`，不记 S1。** `_ids.txt` 里 44 份 `mixed` 是「他创办并主编的
  期刊卷次／他任编者的多人合著」——**既不是他的字，也不是关于他的记述**。
  记 S1 会把它们算进「同时代第三方」，从而虚高覆盖；记 U 则明白写着「未归类」。
  他本人在这些卷里的署名文章，抓源阶段已单独抽成 22 个 `art-*` 单元记 P1。

- **`translation` 一律 P2，且 language 记译本的语种。** 他用德文写作；
  英译／法译是**译者的字**。P2 的定义是「同一材料的降质版本」——译本正是那个。
  逐字引文将来只能取德文 P1。（Pasteur #106 在这上面出过事。）

- **`OCR-BROKEN` 保留入库但绝不记 P1。** 文件不删——删了就没人知道那份扫本坏过。
  `check_ocr_language_death --ledger` 会硬拦「已毁的被记作 P1」。

## 六路归属

按题材粗分，**分不清的记 writings**（他绝大多数材料确实是著作）。
`external` 只给 S1（他人写他的）。
"""
import json
import pathlib
import re
import subprocess
import sys

WS = "workspaces/rudolf-virchow/rudolf-virchow"
ING = "../../../../registry/codex/persona-distiller/scripts/ingest.py"

LANE = [
    (r"^s1-", "external"),
    (r"^s2-", "external"),
    (r"rede|reden|vortrag|ansprache|festrede", "expression"),
    (r"kanalisation|abfuhr|entwaesserung|entwässerung|reinigung|spessart|"
     r"schulen|sanitaets|sanitäts|hunger|typhus|noth|oeffentl|öffentl|"
     r"gesundheitspflege|anstalten", "decisions"),
    (r"brief|correspond", "conversations"),
    (r"chronolog|lebenslauf|zur-erinnerung|nekrolog", "timeline"),
]


def lane(name: str, tier: str) -> str:
    if tier == "S1":
        return "external"
    for pat, ln in LANE:
        if re.search(pat, name, re.I):
            return ln
    return "writings"


def main() -> int:
    rows = []
    for line in pathlib.Path("raw/_ids.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split("\t")
        if len(f) < 8:
            print(f"⚠ 列数不足，跳过：{line[:60]}")
            continue
        rows.append({"sub": f[0].strip(), "url": f[1].strip(), "title": f[2].strip(),
                     "year": f[3].strip(), "lang": f[4].strip(),
                     "tier": f[5].strip(), "flags": f[6].strip(), "note": f[7].strip()})

    ok = fail = 0
    for r in rows:
        p = pathlib.Path("raw") / r["sub"] / f"{r['sub']}.txt"
        if not p.is_file():
            cand = sorted((pathlib.Path("raw") / r["sub"]).glob("*.txt"))
            if not cand:
                print(f"✗ 文件不在：{r['sub']}")
                fail += 1
                continue
            p = cand[0]

        tier = r["tier"]
        if tier == "mixed":
            tier = "U"                      # 见文件头第一条
        if "translation" in r["flags"]:
            tier = "P2"                     # 见文件头第二条
        if "OCR-BROKEN" in r["flags"] and tier == "P1":
            tier = "P2"                     # 见文件头第三条（保底，理应已是 P2）

        year = r["year"] if re.fullmatch(r"1[6-9]\d{2}|20\d{2}", r["year"]) else ""
        argv = [sys.executable, ING, WS, str(p),
                "--tier", tier,
                "--language", r["lang"] or "de",
                "--dimension", lane(r["sub"], tier),
                "--source-type", "document",
                "--author", "Rudolf Virchow" if tier == "P1" else "",
                "--locator", f"{r['title'][:180]}｜{r['url']}",
                "--rights", "public-domain"]
        if year:
            argv += ["--published-at", year]
        proc = subprocess.run(argv, capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"✗ {r['sub']}: {(proc.stderr or proc.stdout).strip().splitlines()[-1][:150]}")
            fail += 1
        else:
            ok += 1
            if ok % 40 == 0:
                print(f"  … 已入 {ok}")
    print(f"\n入库成功 {ok}，失败 {fail}")

    led = pathlib.Path(WS) / "evidence/source-ledger.jsonl"
    if led.is_file():
        import collections
        c = collections.Counter()
        ln = collections.Counter()
        for line in led.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                c[d.get("tier")] += 1
                ln[d.get("dimension") or d.get("lane")] += 1
        print("账本 tier：", dict(c))
        print("账本 六路：", dict(ln))
        p1 = c["P1"]
        prim = p1 + c["P2"]
        tot = sum(c.values())
        print(f"**primary_ratio = (P1 {p1} + P2 {c['P2']}) / {tot} = {prim/max(tot,1):.4f}**"
              f"　（deep 门要 ≥0.65）")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
