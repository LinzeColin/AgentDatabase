#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**门数的是「有几份来源」，不是「有几句他的话」**——语料够门，声口不够。

## 撞出它的那一次（Coffin #130，2026-08-05，**在写断言之前**）

三道 quick 门**全过**：

| 项 | 实测 | 门 | |
|---|---|---|---|
| 来源数 | 18 | ≥8 | ✓ |
| 道数 | 3 | ≥3 | ✓ |
| 一手占比 | 15/18 = 83.3% | ≥0.40 | ✓ |

**而整份语料（172,138 字符）里，他自己说的实质的话只有 8 句。**

因为那 18 份里 14 份是**专利说明书**——文体决定了它几乎全是第三人称的装置描述
加权利要求样板。**每多抓一件专利，来源数 +1，而他的话几乎 +0。**
实测：最长的两份（32k / 35k 字符）**各只有 1 句**实质第一人称。

抓源方为此把 `conversations` 一道找遍了（AIEE vols 4/6/7/8、ASME vol 10、
1918–1921 三部书、1913 年 NYPL 书目），**没有一份是他开口说话的**。
（AIEE 里的每一个「Coffin」都是 `CoFFIN, CHAs. A.`——汤姆森—休斯顿的副总裁兼司库，**另一个人**。）

## ★★★ 为什么裸数「I」会骗人（75% 是噪音）

第一版我量出 118 处第一人称，密度 7.2/万字，**差点当成「够用」写进风险单**。
去看样本才发现：**OCR 把零件标号读成了 `I`**——
`anvil I-I`、`extensions I and J`、`I serving to force the ends together`。

| | 数 |
|---|---|
| 裸 `\\bI\\b` | 118 |
| **其中零件标号等噪音** | **89（75%）** |
| 动词锚定（`I have`／`I find`／`I prefer`…） | 16 |
| 其中权利要求套语 | 6 |
| **实质** | **8** |

→ 本判据**只数动词锚定的、且不是套语的**。裸数一律不报。

## 它报什么

按源报实质第一人称句数与密度（每万字），并给出**逐句原文**——
**不给数就下结论是不许的，所以它必须能出示那几句。**

## ★ 它不做什么

- **不拦。** 密度低不等于做不成：分析型产物、第三人称产物本来就不靠第一人称
  （见 `check_persona_frame_break` 的 `analytic` 模式）。**它只把数摆出来。**
- **不判「够不够」。** 够不够取决于要出哪些用例——
  `voice`／`trajectory`／`contrast` 要他谈自己，`known`／`tool-use` 只要他讲做法。
"""
import argparse
import json
import pathlib
import re
import sys

# 只认动词锚定的第一人称——裸 `I` 在 OCR 语料里 75% 是零件标号
VERB = (r"\bI (?:have|had|am|was|claim|find|found|prefer|may|make|made|use|used|do|did|"
        r"desire|employ|shown|show|believe|consider|know|knew|think|thought|wish|intend)\b")
SENT = re.compile(rf"[^.]{{0,110}}{VERB}[^.]{{0,110}}\.")
# 专利/论文的套语——是他的字，但**不是他的话**
BOILER = re.compile(r"(What I claim|I claim as my invention|desire to secure by Letters Patent|"
                    r"Be it known that I|I, the undersigned)", re.I)
HDR = "=" * 40          # 抓源方写的表头与正文的分隔线


def body_of(text: str) -> str:
    """剥掉抓源方自己写的表头——**表头里的字不是文献的字**。"""
    return text.split(HDR, 1)[-1] if HDR in text else text


def scan_text(text: str) -> dict:
    b = re.sub(r"\s+", " ", body_of(text))
    raw = len(re.findall(r"\bI\b", b))
    subs = [m.group(0).strip() for m in SENT.finditer(b)
            if not BOILER.search(m.group(0))]
    # ★ 套语独立数，**不依赖 SENT 先匹配上**——
    #   `Be it known that I, CHARLES L. COFFIN, of Detroit, have invented…`
    #   的动词离 `I` 太远，SENT 根本不匹配，若挂在 SENT 下面就永远数不到它。
    #   （自测反向对照②当场抓到：期望 ≥2 而只得 1。）
    boil = len(BOILER.findall(b))
    return {"chars": len(b), "raw_I": raw, "boilerplate": boil, "substantive": subs}


def scan(root: pathlib.Path) -> dict:
    files = sorted(p for p in root.rglob("*.txt") if p.name != "_ids.txt")
    per, tot_c, tot_raw, tot_b, allsub = [], 0, 0, 0, []
    for f in files:
        r = scan_text(f.read_text(encoding="utf-8", errors="replace"))
        tot_c += r["chars"]
        tot_raw += r["raw_I"]
        tot_b += r["boilerplate"]
        allsub += [(f.parent.name, s) for s in r["substantive"]]
        per.append({"源": f.parent.name, "字符": r["chars"],
                    "裸I": r["raw_I"], "实质": len(r["substantive"])})
    n = len(allsub)
    out = {
        "语料": str(root),
        "源数": len(files),
        "正文字符": tot_c,
        "裸 I 命中": tot_raw,
        "★ 其中噪音（零件标号等，近似）": f"{max(0, tot_raw - n - tot_b)}"
                                    f"（{max(0, tot_raw - n - tot_b) / max(tot_raw,1):.0%}）"
                                    "——OCR 把 `anvil I-I`／`extensions I and J` 读成第一人称",
        "套语（是他的字，不是他的话）": tot_b,
        "**实质第一人称句**": n,
        "**密度（每万字）**": round(n / max(tot_c, 1) * 10000, 2),
        "逐句原文": [f"[{w}] {s[:150]}" for w, s in allsub[:40]],
        "逐源": sorted(per, key=lambda x: -x["实质"])[:12],
        "★ 口径": ("**只报不拦。** 密度低不等于做不成——分析型／第三人称产物本来就不靠第一人称。"
                   "够不够取决于要出哪些用例：`voice`/`trajectory`/`contrast` 要他谈自己，"
                   "`known`/`tool-use` 只要他讲做法。"),
    }
    if n and tot_c:
        out["★★ 参照"] = ("Coffin #130 实测 **8 句 / 0.5 每万字**——三道 quick 门全过，"
                          "而他自己说的实质的话只有 8 句。**门数的是来源，不是声口。**")
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 正向：Coffin #130 那 8 句里的三句必须认出来 ──")
    r = scan_text('Of course in using the word "vacuum" I do not mean absolute vacuum, '
                  "but that which is ordinarily obtained by the use of an air-pump. "
                  "but I prefer chloridation roasting. "
                  "The construction and use of leaching vats are so well known that "
                  "I have not deemed it necessary to illustrate them.")
    chk(f"三句全中：{len(r['substantive'])}", len(r["substantive"]) == 3)

    print("\n── ★★★ 反向对照①：**OCR 把零件标号读成 I，一句都不许算** ──")
    r = scan_text("R represents an upright arm on base C, carrying an anvil I-I, "
                  "insulated from arm P. M and N are tapped through the extensions I and J. "
                  "I serving to force the ends of the hoop together to form the weld.")
    chk(f"裸 I 命中 {r['raw_I']} 处而实质 {len(r['substantive'])} 句",
        r["raw_I"] >= 3 and len(r["substantive"]) == 0)

    print("\n── ★★ 反向对照②：权利要求套语是他的字，**不是他的话** ──")
    r = scan_text("What I claim as my invention, and desire to secure by Letters Patent, is—1. "
                  "Be it known that I, CHARLES L. COFFIN, of Detroit, have invented certain new "
                  "and useful Improvements.")
    chk(f"套语 {r['boilerplate']} 句、实质 {len(r['substantive'])} 句",
        r["boilerplate"] >= 2 and len(r["substantive"]) == 0)

    print("\n── ★★ 反向对照③：**抓源方写的表头不算语料** ──")
    head = ("SOURCE: US Patent 428,459\nINVENTOR: Charles L. Coffin, of Detroit\n"
            "NOTE: I have reproduced the OCR verbatim and I prefer not to correct it.\n"
            + "=" * 40 + "\nUNITED STATES PATENT OFFICE.")
    r = scan_text(head)
    chk(f"表头里的两句第一人称被剥掉：实质 {len(r['substantive'])}", len(r["substantive"]) == 0)

    print("\n── ★ 反向对照④：正常第一人称叙述要数得出来 ──")
    r = scan_text("I have tried that with considerable success. I find the arc steadier. "
                  "I prefer a soft under carbon.")
    chk(f"三句：{len(r['substantive'])}", len(r["substantive"]) == 3)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus", nargs="?", help="语料目录（递归找 *.txt）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.corpus:
        ap.error("要么 --self-test，要么给语料目录")
    p = pathlib.Path(a.corpus)
    if not p.is_dir():
        print(json.dumps({"状态": f"**未核（不是通过）**：{p} 不是目录"}, ensure_ascii=False))
        return 3
    print(json.dumps(scan(p), ensure_ascii=False, indent=2))
    return 0                      # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
