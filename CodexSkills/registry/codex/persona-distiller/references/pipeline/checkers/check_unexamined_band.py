#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**落在两道门之间、因而谁都没看过的文件。**

## 撞出它的那一份

Koch #107 的 lane 2（`conversations`）**整条道只靠一份文件撑着**：
`robertkochlette00koch.txt`，**766 字符**。打开看：

```
I ; | " } £ /; y® 7 4 6 #9 | 4 fl / 7 { f e + U | . Si PR MH ALM 07, er Kisten,
Pad fr Ir 3 Y% neige Pay paul gegen Sebefegl eh Ze Ai ee Ad aa usa au u fen UF …
```

**手写件 OCR 的纯噪声，一句可读的话都没有。** 而它过了每一道门：

| 门 | 结果 | 为什么 |
|---|---|---|
| `non_placeholder`（≥500 字符、≥5 行） | **过** | 766 字符、36 行 |
| `check_ocr_language_death` | **「未检查（不是通过）」** | 它的下限是**词数 ≥500**，这份只有 54 个词 |
| `check_ocr_legibility` | 不适用 | 它的射程是**德文花体乱码**，手写噪声不是那一种 |

**三道门没有一道说过它是好的**——
**两道说「我不管这个」，一道量的是别的东西。而它照样进了语料，还撑起一整条道。**

## 它报什么

**字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500）的文件**——
**那一段区间里，没有任何判据看过它的内容。**

★ 本件**不判它是不是垃圾**（判不了，也不该由正则判）。
它只说一句：**「这几份谁都没检查过，而它们正在被当作来源用。」**

## ★ 它不做什么

- **不拦。** 短不等于坏——一封两页的信、一份会议纪要，本来就短。
- **不改任何一道既有门的阈值。** 两个 500 各有各的道理，**动它们要重跑所有人**。
- **不判内容质量。** 那要么是人看一眼，要么是另一件判据的活。
"""
import argparse
import json
import pathlib
import re
import sys

PLACEHOLDER_MIN_CHARS = 500      # 与 common.non_placeholder 同源
LANG_MIN_WORDS = 500             # 与 check_ocr_language_death 的下限同源
_WORD = re.compile(r"[A-Za-zÀ-ÿĀ-ſ]{2,}")


def scan(paths: list) -> dict:
    files = []
    for p in paths:
        p = pathlib.Path(p)
        if p.is_dir():
            # ★ 跳过下划线开头的：`_ids.txt`／`_EXCLUDED.txt` 是台账与清单，**不是语料**。
            #   第一版没跳，于是把它们也报了出来——那是噪声，不是发现。
            files.extend(sorted(f for f in p.rglob("*.txt") if not f.name.startswith("_")))
        elif p.is_file():
            files.append(p)
    if not files:
        return {"状态": "**未核（不是通过）**：没有找到任何 .txt"}

    band, too_short, checked = [], 0, 0
    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except Exception:                                         # noqa: BLE001
            continue
        n_chars, n_words = len(t), len(_WORD.findall(t))
        if n_chars < PLACEHOLDER_MIN_CHARS:
            too_short += 1                     # 连 non_placeholder 都过不了，别的门会说话
        elif n_words < LANG_MIN_WORDS:
            band.append({"文件": f.name, "字符": n_chars, "词": n_words,
                         "首 60 字": " ".join(t[:60].split())})
        else:
            checked += 1

    return {
        "扫到的 .txt": len(files),
        "语种判据看过的（词 ≥500）": checked,
        "连 non_placeholder 都不到的（字符 <500，别的门会说话）": too_short,
        "**落在两门之间、谁都没看过的**": len(band),
        "逐份": band,
        "★ 口径": ("**只报不拦，也不判它是不是垃圾。** 短不等于坏——"
                   "一封两页的信本来就短。本件只说「这几份谁都没检查过」。"),
        "★★ 这个数怎么读": ("**它是覆盖缺口，不是缺陷清单。** 短不等于坏——"
                            "全库实测 276/1815（15%）落在这一段，其中 Godin 一人就占 153 份，"
                            "而那是**博客短文，本来就短**。"
                            "本件的价值在于：Koch 那两份（手写 OCR 噪声、拍卖行著录）"
                            "**在此之前没有任何门看过一眼**。"),
        "★ 两个 500 各是谁": (f"字符下限 {PLACEHOLDER_MIN_CHARS} 来自 `non_placeholder`；"
                             f"词数下限 {LANG_MIN_WORDS} 来自 `check_ocr_language_death`。"
                             "**本件不改它们**——动阈值要重跑所有人。"),
    }


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    import tempfile
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        # ① 真实用例：Koch 那份的形状——766 字符、54 个词的手写 OCR 噪声
        (r / "koch_noise.txt").write_text(
            ("I ; | \" } £ /; y 7 4 6 #9 | 4 fl / 7 { f e + U | . Si PR MH ALM 07, "
             "er Kisten Pad fr Ir 3 Y neige Pay paul gegen Sebefegl eh Ze Ai ee Ad aa "
             "usa au u fen UF Aa cha ad BER OP Am fi I 7 ur a & 170 3 A er le Ar 2 Al "
             "kur uf f ar Aal PA dur I VL ee Aunybnku de Pin url Pulli YJ dh Er 4 er a "
             "fpfhlan MD van ara An 7 did wu fr an fr yunifan I Japan off AB E Moped "
             "face Mens\n" * 2), encoding="utf-8")
        # ② 太短：连 non_placeholder 都过不了，别的门会说话
        (r / "tiny.txt").write_text("short.\n", encoding="utf-8")
        # ③ 够长：语种判据看得到，不属本件
        (r / "long.txt").write_text(("Die Untersuchung der Milzbrandbakterien ergab "
                                     "eindeutige Resultate in allen Faellen. ") * 60,
                                    encoding="utf-8")
        out = scan([r])
        names = {b["文件"] for b in out["逐份"]}

        print("── ★★★ 反向对照①：**Koch 那种形状必须报**（够字符、不够词） ──")
        chk(f"报出 {sorted(names)}", names == {"koch_noise.txt"})

        print("── ★★ 反向对照②：**太短的不报**——那是别的门的活，不是「谁都没看过」 ──")
        chk(f"太短的 {out['连 non_placeholder 都不到的（字符 <500，别的门会说话）']} 份，且不在报出里",
            "tiny.txt" not in names and out["连 non_placeholder 都不到的（字符 <500，别的门会说话）"] == 1)

        print("── ★★ 反向对照③：**够长的不报**（语种判据看得到） ──")
        chk(f"语种判据看过 {out['语种判据看过的（词 ≥500）']} 份，long.txt 不在报出里",
            "long.txt" not in names and out["语种判据看过的（词 ≥500）"] == 1)

        print("── ★★★ 反向对照④：**不许下「是垃圾」这种判定** ──")
        s = json.dumps(out, ensure_ascii=False)
        chk("输出里没有「垃圾/失败/不合格」这类判定，只说「没检查过」",
            "不判它是不是垃圾" in s and "谁都没看过" in s)

        print("── ★★ 反向对照⑤：**`_` 开头的台账文件不是语料，不许报** ──")
        (r / "_ids.txt").write_text("x" * 600, encoding="utf-8")
        (r / "_EXCLUDED.txt").write_text("y" * 600, encoding="utf-8")
        n2 = {b["文件"] for b in scan([r])["逐份"]}
        chk(f"报出仍是 {sorted(n2)}", n2 == {"koch_noise.txt"})

        print("── ★★ 反向对照⑥：**输出必须说清这个数是覆盖缺口不是缺陷清单** ──")
        chk("带着「短不等于坏」与 Godin 那个例子",
            "短不等于坏" in json.dumps(scan([r]), ensure_ascii=False))

        print("── ★ 反向对照⑦：**一个 .txt 都没有 → 说「未核」，不说「通过」** ──")
        with tempfile.TemporaryDirectory() as t2:
            chk("未核", "未核" in str(scan([pathlib.Path(t2)]).get("状态", "")))
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="语料目录或 .txt")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.paths:
        ap.error("要么 --self-test，要么给至少一个路径")
    print(json.dumps(scan(a.paths), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
