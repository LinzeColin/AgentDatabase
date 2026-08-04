#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正文是不是**可读的那种语言**——花体乱码会带着完整的字数混过所有既有的门。

## 为什么有这件

Liebig #124 落盘 62 份、字数 394 万、deep 门四项全过。
而逐份看正文时发现 **10 份是花体（Fraktur）OCR 乱码**：

    dürften, vor 2filem ber I)od)ftnntge ©rünber ^)of)eni)eim6, unfterb(id)e Ser*
    bienfte um bic beutfebe 2anbwirtbfd)aft erworben.

`ber`=der、`unb`=und、`bic`=die、`ift`=ist、`I)`=h、`2)`=D、`©`=G。
**这不是「OCR 有点差」，是整篇没有一个词能拿去检索或引用。**

**十份里九份是 P1（一手）**，合计 583 万字符。它们此前：

- 过了 `sha256` 去重（字节当然不同）
- 过了来源数门（份数是真的）
- 过了一手占比门（分档是真的）
- 过了字数统计（字数是真的）
- **`near_duplicates` 也抓不到**——见 `ocr_variant_pairs` 那条，长 s 把 shingle 打灭

**没有任何一道门问过「这些字能不能读」。**

## 判据形状

德文正常散文里 `der/die/und/ist/sich/nicht/den/dem/eine/auch` 占词数 **9%–16%**；
花体乱码里这些词变成 `ber/bie/unb/ift/ben/bem/aud/nid/fid/baf`。

Liebig 全量实测，两群**完全不重叠**：

| | 正确形词率 | 乱码形词率 | 乱码/正确 |
|---|---:|---:|---:|
| 可用的 27 份 | 0.0502–0.1638 | 0.0000–0.0183 | **0.00–0.19** |
| 乱码的 10 份 | 0.0051–0.0239 | 0.0685–0.1126 | **4.09–16.83** |

判据取 **乱码形 > 正确形**（即比值 > 1）——落在那道 0.19 与 4.09 之间的空档里，
**离两侧都远**，不是卡着边界挑出来的。

## 射程边界

- **只认德文花体这一种坏法。** 英文长 s、拉丁文、中文 OCR 的坏法不同，本件看不见。
  返回值里 `checked` 会说清只测了哪些文件。
- **不判「OCR 差」只判「整篇不可读」**。个别讹字是正常的，
  Osler/Blackwell 那种「保留扫本讹字并标出」反而是加分项。
- **只报不删。** 剔不剔是调用方的事；本件只保证它不静默。
"""
import argparse
import json
import pathlib
import re
import sys

GOOD_DE = re.compile(r"\b(der|die|und|ist|sich|nicht|den|dem|eine|auch)\b", re.I)
MOJI_DE = re.compile(r"\b(ber|bie|unb|ift|ben|bem|aud|nid|fid|baf)\b", re.I)
MIN_SIGNAL = 0.005          # 两侧都低于此 → 判「不是德文，没测」
MOJI_FLOOR = 0.02           # ★ 判乱码还要过这条绝对线，见下

# ★★ 第一版只判 `moji > good`，在 Slavyanov #115 的语料上误报了一份：
#    `viall-electric-welding-1921-contents` 是**英文目录页**，good=0.0000、moji=0.0051
#    （`ben`/`nid` 这类三字母串在英文里偶尔撞上），moji>good 成立于是被判乱码。
#    真乱码的 moji 实测在 **0.0685–0.1126**，离 0.02 这条线远得很；
#    而误报那份是 0.0051。加一条绝对下限即可分开，**且两侧都不贴线**。


def legibility(text: str) -> dict:
    n = max(len(text.split()), 1)
    good = len(GOOD_DE.findall(text)) / n
    moji = len(MOJI_DE.findall(text)) / n
    if max(good, moji) < MIN_SIGNAL:
        return {"verdict": "not-german", "good": round(good, 4), "moji": round(moji, 4)}
    bad = moji > good and moji >= MOJI_FLOOR
    if not bad and moji > good:          # 过了相对判据、没过绝对线 → 说清楚，别当 ok 混过去
        return {"verdict": "too-little-german", "good": round(good, 4), "moji": round(moji, 4)}
    return {"verdict": "mojibake" if bad else "ok",
            "good": round(good, 4), "moji": round(moji, 4),
            "ratio": round(moji / good, 2) if good else None}


def scan(raw_dir: pathlib.Path) -> dict:
    out, checked = [], 0
    for d in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        f = d / f"{d.name}.txt"
        if not f.is_file():
            continue
        r = legibility(f.read_text(encoding="utf-8", errors="ignore"))
        r["short"] = d.name
        if r["verdict"] != "not-german":
            checked += 1
        out.append(r)
    bad = [r for r in out if r["verdict"] == "mojibake"]
    return {"落盘份数": len(out), "**测到的德文份数**": checked,
            "**判为花体乱码**": len(bad), "乱码清单": bad,
            "★ 射程": "只认德文花体这一种坏法；英文长 s／拉丁文／中文的坏法本件看不见"}


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    good = ("Der Boden ist nicht eine tote Masse und auch nicht bloss ein Behälter. "
            "Die Pflanze nimmt sich aus dem Boden den Stoff den sie braucht. ") * 40
    moji = ("Ber Soben ift nid)t eine tote 9Jlaffe unb aud) nid)t bloss ein 33ef)älter. "
            "Bie ^flanje nimmt fid) aus bem Soben ben ©toff ben fie braucht. ") * 40
    eng = "The soil is not a dead mass and not merely a container for the plant. " * 40

    print("── 正向：正常德文判 ok ──")
    chk(f"{legibility(good)}", legibility(good)["verdict"] == "ok")
    print("── ★★ 反向对照①：花体乱码判 mojibake ──")
    chk(f"{legibility(moji)}", legibility(moji)["verdict"] == "mojibake")
    print("── ★★ 反向对照②：英文**不**误判成乱码（本件看不见它，要说出来）──")
    chk(f"{legibility(eng)}", legibility(eng)["verdict"] == "not-german")
    print("── ★★ 反向对照③：两群的比值要**离判据线都远**，不是卡着边界 ──")
    chk(f"正常德文 ratio={legibility(good).get('ratio')} 应 <0.5",
        (legibility(good).get("ratio") or 0) < 0.5)
    chk(f"乱码 ratio={legibility(moji).get('ratio')} 应 >2",
        (legibility(moji).get("ratio") or 0) > 2)
    print("── ★★ 反向对照④：**第一版真的误报过的那一份**，现在不许再报 ──")
    # Slavyanov #115 `viall-electric-welding-1921-contents` 的实测形状：
    # 英文目录页，good=0.0000、moji=0.0051 —— moji>good 成立，但远低于绝对线
    # ★ 夹具第一版把 `ben nid` 放进**每一段**，算出 moji=0.1053——
    #   那不是那份文件的形状（实测 0.0051），等于换了个案子测。**夹具要照着实测的数配。**
    fp = (("Contents Chapter Index Table Figure Plate Section Appendix Notes Reference "
           "List Welding Electric Arc Process Machine Shop Steel Iron Current ") * 30
          + " ben nid baf ")          # 3 / ~603 词 ≈ 0.005，与实测同量级
    r = legibility(fp)
    chk(f"★ 夹具形状对得上实测（moji≈0.005）：moji={r['moji']}", 0.002 <= r["moji"] <= 0.010)
    chk(f"{r}", r["verdict"] != "mojibake")
    chk("★ 而且它被明确标成 too-little-german，不是悄悄算成 ok",
        r["verdict"] in ("too-little-german", "not-german"))
    print("── ★ 反向对照⑤：空输入不崩 ──")
    chk(f"{legibility('')}", legibility("")["verdict"] == "not-german")
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    # ★ 退出码按仓内约定：**2 = 负对照未过**（调用方据此判「本件结论不作数」），
    #   不是 1 —— 1 留给「跑通了，且发现了问题」。
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="?", help="工作区的 raw/ 目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.raw:
        ap.error("要么 --self-test，要么给 raw/ 目录")
    info = scan(pathlib.Path(a.raw))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 1 if info["**判为花体乱码**"] else 0


if __name__ == "__main__":
    sys.exit(main())
