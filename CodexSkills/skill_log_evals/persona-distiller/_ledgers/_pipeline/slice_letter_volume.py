#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slice_letter_volume.py —— **书信集按封切段，并逐封判「是不是他写的」**

## 为什么要有这件

2026-08-14 从捷克国图取回 1892 年 Patera 编《Korrespondence》（143,711 词）。
它填得上 Comenius #182 缺的 `conversations` 道 —— **但整卷判 `HIS-OWN` 是错的**：
逐封数完 117 封，**至少 10 封连他都不在场**（`Mr. Hartlib to Mr. Pell.` ×5、
`Ex literis P. Figuli ad Nicolaum Arnoldům`、`Ex responso S. Maresii Nikolao Arnoldo`、
`Literae Seniorum ad Susanna Lorántfy`、Susanna Lorántfy 自己署名的文书 ×3）。
[[related-to-him-is-not-written-by-him]]（Liebig 那次混进 9 份，一手占比 0.7419→0.5192）

⇒ 要么整卷不用，要么**按封切开、逐封定归属**。本件做后者。

## ★★ 它判什么、不判什么

- **判**：每封信的**抬头形状**（第一条非空行）。这是 Patera 版里唯一稳定的方向信号。
- **不判**：只有问候语开头的那批（`Gratiam et pacem !`／`Reverende Vir!`）——
  一律归 `?`，**必须人打开读**。本件不猜。
- **不写工作区**：只往 `--out` 指定的目录写，且默认只报不写。

## ★ 试过、不用的第二把尺子：信末署名

同样 117 段取每封末 14 行找署名：**无署名 69**（Patera 大量收的是摘录，
结尾就是 `etc. Vale.`）／他的 31／别人的 12（**含正文误报**：
`dominus Wolzogen, cum generosis…` 是正文里提到，不是署名）／两者都有 5。
⇒ **抬头判得出 67，署名只判得出 31 且带误报。** 用抬头。
[[two-checkers-same-text-different-rules]]

## ★★★ 同一个抬头正则我写窄了三次

`^Ad\\s+[A-Z][a-zé]+\\.?$` → 漏掉 `Ad eundem.`（小写）、`Ad.`（带点）、多词抬头。
第一次报 **9** 条、第二次 **35** 条、第三次 **67** 条 —— 同一份文件，三个数。
[[the-comment-states-the-rule-the-code-narrows-it]]
★ 每次救我的都是**把命中全部原样打出来读**，不是再想一遍正则。

## 用法

    python3 slice_letter_volume.py <正文.txt> --from 0.05 --to 0.70      # 只报
    python3 slice_letter_volume.py <正文.txt> --from 0.05 --to 0.70 \\
        --out <目录>                                                     # 切片＋sha256
    python3 slice_letter_volume.py --self-test

退出码：0＝跑完（**不等于全判出来了**，看 `?` 计数）；2＝参数错；3＝一封都没切出来。
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

# ★ 一封信的起点：独立成行的罗马数字编号（Patera 版的编号方式）
MARKER = re.compile(r"^\s*([IVXLCDM]{1,8})\.\s*$")

# ★★ 抬头 → 方向。**顺序有意义**：先判「不是他」的强形状，再判「是他」。
#   反过来会把 `Fragmentum epistolae Joh. Bythneri ad J. Comenium` 判成他写的
#   —— 那句里也有 `ad …`。
NOT_HIS = [
    # `Mr. Hartlib to Mr. Pell.` —— 英文的「甲致乙」，两头都不是他
    (r"\bto\s+(?:Mr\.?|Dr\.?|Sir)\b", "英文『甲致乙』"),
    # `Epistola M. Mersenni ad J. A. Comenium.` / `Fragmentum epistolae X ad J. Comenium`
    # ★ 首字母缩写要通吃：实测有 `ad J. Comenium`／`ad J. A. Comenium`／`ad D. Comenium`。
    #   第一版写死 `(?:J\.?\s*A\.?\s*)?`，**`ad J. Comenium` 当场判不出**——
    #   自测里那一条红了，才没让它跑到数据上。
    (r"\bad\s+(?:[A-Z]\.?\s*){0,3}Comeni(?:um|o)\b", "别人写给他"),
    # `Ex literis P. Figuli ad Nicolaum Arnoldům` —— `Ex literis` 后面**先有人名再有 ad**
    (r"\bEx\s+(?:literis|epistola)\s+(?!ad\b)(?!J\.?\s*A?\.?\s*Comeni)\S+.*\bad\b", "第三方之间的信"),
    (r"\bEx\s+responso\s+(?!J\.?\s*A?\.?\s*Comeni)\S", "第三方的回信"),
    (r"^\s*Literae\s+\w+\s+ad\b", "某某等人致某某"),
    (r"^\s*(?:Nos\s+)?Susanna\s+Lor[áa]ntfy\b", "她自己署名的文书"),
    (r"Domine\s+Comeni\b", "抬头在称呼他 ⇒ 他是收信人"),
]

IS_HIS = [
    (r"^\s*Ad\.?\s+\S", "`Ad <某人>`"),
    (r"^\s*Ex\s+(?:literis|epistola)\s+ad\b", "`Ex literis ad <某人>`"),
    (r"\b(?:Ex\s+literis|Excerpta\s*!?\s*ex\s+literis|Fragmentum\s+responsi)\s+"
     r"(?:clariss\.\s*)?(?:d\.\s*)?(?:J\.?\s*A?\.?\s*)?Comenii\b", "`… ex literis Comenii`"),
    (r"^\s*Responsum\s+ad\b", "`Responsum ad <某人>`"),
    # ★ `Copia epistolae ad r. d. Ernestům Andreae` ——「致某某的信的抄件」，
    #   仍是他发出的。第一版归进 `?`，是**读那 18 条 `?` 时逐条看出来的**，
    #   不是又想了一遍正则。[[read-the-hits-before-reporting-the-rate]]
    (r"^\s*Copia\s+epistolae\s+ad\b", "`Copia epistolae ad <某人>`"),
    # ★ 敬称不许写死：OCR 把 `Nobilissimo` 出成 **`Nobüissimo`**（i→ü），
    #   `Nobi{1,2}lissim\w+` 当场落空。改成「开头 40 字内出现与格 `domino`」。
    #   [[aggregator-ocr-can-be-silently-broken]] 会顺手打坏你锚点里的每一个字母。
    (r"^.{0,40}?\b[Dd]omino\b", "拉丁与格抬头 `Domino …`"),
    (r"^\s*D\.\s*d\.\s+\w", "`D. d. <某人>`（与格缩写）"),
    (r"^\s*Bratru\s+\w", "捷克与格 `Bratru …`"),
    (r"^\s*(?:Já|Ja),\s*Jan\s+A\.?\s*Komensk", "他自述『我，Jan A. Komenský』"),
]


def split_by_marker(text: str):
    """正文 → [(编号, 抬头, 正文)]。**纯函数**。

    抬头 = 编号之后**第一条非空行**；正文 = 到下一个编号为止。
    """
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if MARKER.match(l)]
    out = []
    for a, b in zip(idx, idx[1:] + [len(lines)]):
        num = MARKER.match(lines[a]).group(1)
        head = ""
        for j in range(a + 1, min(a + 6, b)):
            if lines[j].strip():
                head = lines[j].strip()
                break
        out.append((num, head, "\n".join(lines[a:b])))
    return out


def direction(head: str):
    """抬头 → (`HIS-OWN` / `OTHER` / `?`, 命中的理由)。**纯函数**。

    ★ `?` 不是失败，是**诚实**：只有问候语的抬头判不出方向，要人读。
      把 `?` 默认成 `HIS-OWN` 就是 [[empty-default-swallows-unknown]]。
    """
    h = head or ""
    for pat, why in NOT_HIS:
        if re.search(pat, h, re.I):
            return "OTHER", why
    for pat, why in IS_HIS:
        if re.search(pat, h, re.I):
            return "HIS-OWN", why
    return "?", "抬头只有问候语／判不出 —— **要人打开读**"


def self_test() -> int:
    ok = n = 0

    def chk(d, c):
        nonlocal ok, n
        n += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★★ 正例与反例**全部逐字取自 uuid:32d4d830… 的真抬头**，不是我照着正则编的。
    HIS = [
        "Ad eundem.",
        "Ad D. Joh. Mochingerum",
        "Ad illustrissimum D D. Palatinum Belzensem.",
        "Ad. Dominum Hottonum.*",
        "Ad amicos Lesznae in Polonia agentes.*",
        "Ex literis ad dominum Hottonum.",
        "Ex epistola ad d. d. Zb. Goray, castellanum Chelmensem.",
        "Domino Ludovico de Geer.",
        "Nobüissimo et strenuo domino Johanni a Wolzogen.",
        "D. d. Baroni Sadovio.",
        "Bratru Chodniciovi.",
        "Ex literis J. Comenii ad N. Arnoldům.*",
        "Excerpta! ex literis clariss. Comenii,",
        "Responsum ad Susannam Lorántfy.",
        "Já, Jan A. Komenský, zanechávám po sobě poznamenání, za bratrem a",
        "Copia epistolae ad r. d. Ernestům Andreae (et clarissimum",
    ]
    OTH = [
        "Mr. Hartlib to Mr. Pell.*",
        "MR Pell to Mr. Hartlib.*",
        "Epistola M. Mersenni ad J. A. Comenium.**",
        "Fragmentum epistolae Joh. Bythneri ad J. Comenium.",
        "Ex literis P. Figuli ad Nicolaum Arnoldům *",
        "Ex responso S. Maresii Nikolao Arnoldo.**",
        "Literae Seniorum ad Susanna Lorántfy.",
        "Susanna Lorántfy, celsissimi quondam Principis Domini Georgi! Rákóczy,",
        "Nos Susanna Lorántfy, celsissimi quondam Principis, Domini Georgii Rákóczy,",
        "Grata nobis omnia Tua, reverende, clarissime Domine Comeni, gratus ad Vestros",
    ]
    UNK = [
        "Gratiam et pacem !",
        "Salutem et observantiam !",
        "Reverende et clarissime Domine!",
        "Pacem Jesu Christi!",
        "Vivit, vincit, regnat Christus!*",
    ]
    for h in HIS:
        d, w = direction(h)
        chk(f"HIS-OWN｜{h[:52]:54s}→ {d} [{w}]", d == "HIS-OWN")
    for h in OTH:
        d, w = direction(h)
        chk(f"**OTHER**｜{h[:52]:54s}→ {d} [{w}]", d == "OTHER")
    for h in UNK:
        d, _ = direction(h)
        chk(f"**?（不许猜）**｜{h[:48]:50s}→ {d}", d == "?")

    # ★★ `Fragmentum responsi J. Comenii ad epistolam Joh. Bythneri` 是**他的回信**，
    #   而 `Fragmentum epistolae Joh. Bythneri ad J. Comenium` 是**别人写给他**——
    #   两句都含 `Fragmentum`＋`ad`，差别只在中间那个名字是谁。**这一对是本件最容易切反的地方。**
    a, _ = direction("Fragmentum responsi J. Comenii ad epistolam Joh. By timeri.")
    b, _ = direction("Fragmentum epistolae Joh. Bythneri ad J. Comenium.")
    chk(f"★★★ **最易切反的一对**：他的回信判 {a}／别人来信判 {b}",
        a == "HIS-OWN" and b == "OTHER")

    # ★ 切段：三封信，中间那封抬头空一行
    txt = "\n".join(["I.", "Ad eundem.", "corpus a", "", "II.", "", "Mr. Hartlib to Mr. Pell.",
                     "corpus b", "III.", "Gratiam et pacem !", "corpus c"])
    seg = split_by_marker(txt)
    chk(f"★ 切出 3 封（实得 {len(seg)}）", len(seg) == 3)
    chk("★ 抬头跳过空行也取得到", seg[1][1] == "Mr. Hartlib to Mr. Pell.")
    chk("★★ **没有编号时切出 0 封，不许当成 1 封整卷**", split_by_marker("abc\ndef") == [])
    print(f"\n{'✓ 全过' if ok == n else f'✗ {n - ok}/{n} 项不符'}")
    return 0 if ok == n else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?", help="整卷正文 .txt")
    ap.add_argument("--from", dest="lo", type=float, default=0.0, help="只看全文的这个起点比例")
    ap.add_argument("--to", dest="hi", type=float, default=1.0)
    ap.add_argument("--out", help="给了才切片落盘；不给只报")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.text:
        ap.error("要 <正文.txt> 或 --self-test")

    t = pathlib.Path(a.text).read_text(encoding="utf-8", errors="replace")
    seg_txt = t[int(len(t) * a.lo):int(len(t) * a.hi)]
    segs = split_by_marker(seg_txt)
    if not segs:
        print("★★ **切出 0 封** —— 这一段里没有独立成行的罗马数字编号；"
              "**未切，不是「整卷一封」**", file=sys.stderr)
        return 3

    rows, tally = [], {"HIS-OWN": 0, "OTHER": 0, "?": 0}
    for num, head, body in segs:
        d, why = direction(head)
        tally[d] += 1
        rows.append({"编号": num, "抬头": head[:96], "方向": d, "判据": why,
                     "词数": len(body.split()),
                     "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()})

    print(f"★★ **分母**：{a.text}｜取全文 {a.lo:.0%}–{a.hi:.0%} 段（{len(seg_txt):,} 字）"
          f" → **切出 {len(segs)} 封**\n")
    print(f"   HIS-OWN **{tally['HIS-OWN']}**｜OTHER **{tally['OTHER']}**"
          f"｜**?（要人读）{tally['?']}**")
    w = {k: sum(r["词数"] for r in rows if r["方向"] == k) for k in tally}
    tot = sum(w.values()) or 1
    print(f"   按词数：HIS-OWN {w['HIS-OWN']:,}（{w['HIS-OWN']/tot:.1%}）"
          f"｜OTHER {w['OTHER']:,}（{w['OTHER']/tot:.1%}）"
          f"｜? {w['?']:,}（{w['?']/tot:.1%}）")

    print(f"\n── **OTHER {tally['OTHER']} 封**（收信人与写信人都不是他，或他是收信人）")
    for r in rows:
        if r["方向"] == "OTHER":
            print(f"   {r['编号']:>7s} {r['词数']:>6,} 词  {r['抬头'][:62]:64s} [{r['判据']}]")
    print(f"\n── **? {tally['?']} 封 —— 本件不猜，要人打开读**")
    for r in rows:
        if r["方向"] == "?":
            print(f"   {r['编号']:>7s} {r['词数']:>6,} 词  {r['抬头'][:62]}")

    if a.out:
        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        for (num, head, body), r in zip(segs, rows):
            (out / f"{num}.txt").write_text(body, encoding="utf-8")
        (out / "_slices.json").write_text(json.dumps(
            {"源文件": str(pathlib.Path(a.text).resolve()),
             "配方": f"取全文 {a.lo}–{a.hi} 段，按 `^[IVXLCDM]+\\.$` 独立成行切",
             "★口径": "方向只看抬头；`?` 表示判不出，**不是 HIS-OWN**",
             "封数": len(rows), "逐封": rows},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n★ 已切片落盘：{out}（{len(rows)} 段 ＋ `_slices.json` 含逐封 sha256）")
    else:
        print("\n★ 没给 `--out` ⇒ **只报不写**。")
    print("★★ 落进工作区之前：`?` 那批必须逐封读过并定案，"
          "**不许把 `?` 当成 HIS-OWN**（[[empty-default-swallows-unknown]]）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
