#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCR 把整份文本毁掉了，而它仍然是一份「真文档」。

## 为什么现有的门看不见它

- `check_corpus_integrity` 只判「这是语料还是一张取不到的错误页」。
  **被 Fraktur OCR 毁掉的德文仍是一份真文档**——它扫了 229 份，报 0 可疑。
- `check_ocr_homoglyphs` 只查冒充拉丁字母的西里尔／希腊字符。
  Fraktur 的坏法不是同形字，是**成批认错字母**：`der`→`bev`、`und`→`unb`、`sein`→`fein`。
  它扫同一批语料，报的是另外一类问题。

Virchow #109 抓源时撞出：227 份德文语料里有一批读起来像德文、
**实际虚词一个都对不上**——`der/die/das/und/in` 这些最常见的词在里面几乎不出现。

## 判据形状：阈值，而这一次阈值是**读出来的**

对每份文本算「虚词占比」，取**多语种里最高的那个**（见下面「为什么必须多语种」）。
227 份真实语料的分布：

```
最大的四个间隙：
  间隙 0.122：0.117 → 0.239   ← 空带，其下 18 份、其上 209 份
  间隙 0.014：0.255 → 0.268
  间隙 0.013：0.094 → 0.108
  间隙 0.012：0.268 → 0.280
```

**0.117 与 0.239 之间一份都没有**，而次大的间隙只有 0.014。
阈值取 `0.15` —— **落在这条空带里面**，不是我挑的一个数。

（对照 v0.0.0.36 的 `METHOD_FLOOR = 3`，那个至今标着「暂定值，无实测支持」。
**能从数据里读出来的阈值才写，读不出来的宁可标明没有支持。**）

## 为什么必须多语种

第一版只用德语词表，于是 **11 份法译本全被判成「已毁」**——
它们是好好的法文，只是不含德语虚词。
**语种判错会把整批健康语料报成坏的**，而那种假红比漏报更难收场
（v0.0.0.38 刚因为「假红」吃过一次亏）。

故：对每份文本取**各语种虚词占比的最大值**，即「它最像哪一种语言，就有多像」。

## 射程边界

- **它不判语料对不对、是不是这个人的。** 那是 `check_authorship` 与 `attribution_basis` 的事。
- **词数不足 500 的不判**——短文本的虚词占比噪声太大。
- 语种表只有 de/en/fr/la/it/es/pt 七种。**别的语种会被误判为已毁**，
  故输出必带「最佳语种」一栏，看到不认识的语种要先加词表再下结论。
- **索引、目录、表格类文本天然没有虚词，会被判成「已毁」。**
  Virchow #109 实测一例：`archiv-bdC-1847-de` 占比 0.117，实为该刊的 Sachregister
  （「Inversion s. Krebs, Blasenmastdarmfistel XIV. 218.」这类条目），文本本身完好。
  **它不造成实害**——索引本来就不该被当作他的散文逐字引用——**但标签是错的**，
  看到这一类要人工确认一句，别当成扫本坏了去重抓。

## 两种口径

- **不给 `--ledger`**：只报告有哪几份已毁（退出 0）。抓源阶段用。
- **给 `--ledger`**：已毁的文件若在账本里**记作 P1**，报错（退出 1）——
  **你正打算从一份读不出字的文件里取逐字引文。**

用法：

    python3 check_ocr_language_death.py raw/                       # 只报告
    python3 check_ocr_language_death.py raw/ --ledger <ws>/evidence/source-ledger.jsonl
    python3 check_ocr_language_death.py --self-test

退出码：0=没有已毁的 P1（或只报告）　1=已毁的文件被记作 P1　2=自测未过
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

#: ★ 剥掉抓源方写的出处表头再量——**表头是出处说明，不是他的话**。
#:   全库只有 Adams（144 份）与 Coffin（36 份）有这种表头，
#:   实测占全文**聚合 17.2% / 11.7%**，**逐份中位 39.1% / 16.1%**。
#: ★★ 接上之后**逐个量过前后差**，只写量到的：
#:   · `check_lane_quotes_verbatim` @ Coffin：核过 1 → 0，
#:     报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
#:     那句「逐字引文」只存在于**我自己写的表头里**。这是 Barton 事故的引文版，实锤一条。
#:   · ★★★★ `check_ocr_language_death` @ Coffin：不剥时「**每一份都在下限之上**」，
#:     剥掉表头后报出 **2 份虚词占比 0.101（下限 0.15）**——
#:     **我那段干净的英文表头把 OCR 烂掉的文件托过了及格线。**
#:     同一件在 Adams 上是「可判份数 94 → 60」：34 份**只因表头的词数才够得上判**。
#:   · `check_first_person_density`：正文字符 −0.6%，密度 1.68 → **1.69**——
#:     **几乎没变**。我一度在这里写「第一人称密度被表头拉偏」，**那句没有实测支撑，已删**。
#:   · 其余多数判据前后一致。**接线是按「表头不是他的话」这条原则做的，不是因为每个都变了。**
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

MIN_WORDS = 500
# ★ 这个数是从 227 份真实语料的分布里**读出来的**，不是挑的：
#   0.117 与 0.239 之间一份都没有（空带宽 0.122，次大间隙仅 0.014），0.15 落在带内。
FLOOR = 0.15

LEX: dict[str, set[str]] = {
 "de": {"der","die","das","und","in","zu","den","von","mit","des","dem","nicht","ist",
        "auf","ein","eine","als","auch","es","an","werden","aus","er","hat","dass",
        "sie","nach","bei","um","am","sind","noch","wie","einem","über","einen","so",
        "zum","war","haben","nur","oder","aber","vor","zur","bis","mehr","durch","man",
        "sich","wird","sein","einer","ich","wenn","diese","dieser","ihre","ihm","ihn",
        "dieses","welche","dabei"},
 "en": {"the","of","and","to","in","a","is","that","for","it","as","was","with","be",
        "by","on","not","he","this","are","or","his","from","at","which","but","have",
        "an","had","they","you","were","their","one","all","we","can","her","has",
        "been","would","there"},
 "fr": {"le","la","les","de","des","du","et","en","un","une","que","qui","dans","pour",
        "est","il","ne","pas","sur","au","aux","ce","se","par","plus","ou","nous","avec",
        "son","sa","ses","cette","comme","mais","dont","sont","été","être","a","à","on",
        "tout","leur","elle"},
 "la": {"et","in","est","non","ad","cum","quod","ut","si","sed","qui","quae","de","ex",
        "per","atque","autem","enim","ab","aut","nec","hoc","esse","sunt","etiam","quam",
        "tamen","ita","eius","eo","id","ea","ac","vel","quo","haec","hac","quibus","cui",
        "eam","eius","illa","ille","ipse","idem","nam","iam","tum","ubi","unde","sic",
        "quidem","vero","igitur","ergo","ante","post","sub","inter","apud","propter",
        "sine","contra","super","erat","fuit","fuerit","potest","possunt","habet"},
 "it": {"il","la","di","e","che","in","un","una","per","non","con","del","della","si",
        "da","al","le","dei","come","più","sono","ma","anche","alla","nel","questo"},
 "es": {"el","la","de","que","y","en","los","del","se","las","por","un","para","con",
        "no","una","su","al","es","lo","como","más","pero","sus","le","ya","o"},
 # pt：Jenner #104 的《Inquiry》葡译本实测被判为 fr、占比 0.144 而误报——
 # **判据自己的射程边界写着「看到不认识的语种要先加词表」，这就是那一次。**
 "pt": {"o","a","os","as","de","do","da","dos","das","em","no","na","nos","nas","que",
        "e","um","uma","por","para","com","não","se","como","mais","mas","ao","à","seu",
        "sua","seus","suas","este","esta","esse","essa","foi","era","ser","tem","muito",
        "quando","onde","depois","sobre","entre","até","já","ou","também","pelo","pela"},
}

WORD = re.compile(r"[a-zäöüßà-ÿ]{1,20}")

# ★ 长 s 折叠。十八世纪之前的印本里长 s 常被 OCR 成 `f`：
#   `est`→`eft`、`constat`→`conftat`、`nostri`→`noftri`、`posse`→`polTe`。
#   不折叠的话，**一份完全可读的拉丁文会被判成「已毁」**——
#   Jenner #104 的三份拉丁／法文源实测就是这么被误报的（0.136–0.143，贴着下限）。
#   本码库已有同一约定：`check_quote_integrity.fold_s`。
#   **词表与正文两侧都要折**，只折一侧等于没折。
_LONGS = re.compile(r"[fs]")


def _fold(w: str) -> str:
    return _LONGS.sub("§", w)


LEX_FOLDED = {k: {_fold(x) for x in v} for k, v in LEX.items()}


WINDOW = 2000          # ★ 窗口词数：约合一两千词的连续散文
WINDOW_MIN_WORDS = 4000  # 全份不足这个数就不开窗（小文件整份量即可）


def _rate_words(wf: list) -> tuple:
    best, lang = 0.0, "-"
    for k in LEX:
        r = sum(1 for x in wf if x in LEX_FOLDED[k]) / len(wf)
        if r > best:
            best, lang = r, k
    return best, lang


def rate(text: str) -> tuple[float, str, int]:
    """→ (最佳语种的虚词占比, 该语种, 词数)。词数不足则占比返回 -1。

    ★★ 2026-08-04：**取「最密的那一段窗口」，不取全份平均。**

    整份平均会被**名录／表格／历书**拖死，而那正是本判据自己写着的已知假阳类。
    #117 Barton 实测两处：

    | 文件 | 整份 | **她的散文段** | 拖累它的东西 |
    |---|---:|---:|---|
    | `andersonville-1866` | 0.052 | **0.367**（250–729 行） | 一万三千人的墓葬名录，**占全份 94% 词数** |
    | `diary-1888-jan-apr` | 0.147 | —— | 日记本印刷的历书：日月食表、天文计算 |

    两份文字都完全可读，**却都被判成「已毁且记作 P1」**，
    而报文说的是「你正打算从一份读不出字的文件里取逐字引文」——**那句话是错的**。

    **「这份文件有没有一段能读」与「这份文件平均起来像不像散文」是两个问题。**
    要防的是前者，所以按窗口取最大值。
    """
    w = WORD.findall(text.lower())
    if len(w) < MIN_WORDS:
        return -1.0, "-", len(w)
    wf = [_fold(x) for x in w]
    best, lang = _rate_words(wf)
    # 大文件再按滑动窗口找最密的一段；窗口步长取半窗，够密就够用
    if len(wf) >= WINDOW_MIN_WORDS:
        step = WINDOW // 2
        for i in range(0, len(wf) - WINDOW + 1, step):
            r, l = _rate_words(wf[i:i + WINDOW])
            if r > best:
                best, lang = r, l
    return best, lang, len(w)


def scan(paths):
    out = []
    for p in paths:
        p = pathlib.Path(p)
        files = sorted(p.rglob("*.txt")) if p.is_dir() else [p]
        for f in files:
            if f.name.startswith("_"):
                continue
            try:
                t = corpus_body(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            r, lang, n = rate(t)
            out.append({"path": str(f), "rate": r, "lang": lang, "words": n})
    return out


def self_test() -> int:
    """负对照 + 四条反向对照。"""
    print("══ 负对照 ══")
    fail = 0

    # ★ 真实夹具，取自 Virchow #109 语料原样，一字未改。
    #   **第一版我自己编了一段 `bev unb fein ift`——那是纯 f/s 替换，
    #   加上长 s 折叠之后它反而匹配上了德语词表，把判据折没了。**
    #   编的夹具证明不了任何事；坏样本必须来自真语料。
    #   ① 彻底乱码（raw/berl-ges-anthropologie-1891-alt）
    dead_a = ("ünitfkp. TTölnr dnu iitntr dim Litauj liJimtultidt^iL miv tidbiiniiini "
              "tsiuflnn aller Sclinl^tölJnr klliito nllfcirEliii^ nur in ÜctftiühL li " * 30)
    #   ② Fraktur 系统性错认（raw/vierreden-1862-de）：s→f、d→b、w→m、N→97、ch→d)
    dead_b = ("fenbern rem 3tt>ettBegriff Bebingte ßjrfftenj finbet fid) in ben Serien "
              "ber 97atnr; baS $iet aBer, meSmegen fie Beflehen eher gemorben finb, "
              "trennt gan$ BefonberS in ber Regien beS @cBönen " * 30)
    dead = dead_a + " " + dead_b
    for label, sample in (("彻底乱码", dead_a), ("Fraktur 系统性错认", dead_b)):
        r, lang, n = rate(sample)
        got = 0 <= r < FLOOR
        print(f"  {'✓ 抓到' if got else '✗ 漏掉'} {label}：占比 {r:.3f} < {FLOOR}（判为 {lang}）")
        fail += not got

    print("\n══ 反向对照 ══")
    # ① 健康德文 → 不得报（否则本件只是「凡德文皆报」）
    ok_de = ("der die das und in zu den von mit des dem nicht ist auf ein "
             "Zelle Gewebe Krankheit Untersuchung " * 60)
    r1, l1, _ = rate(ok_de)
    p1 = r1 >= FLOOR and l1 == "de"
    print(f"  {'✓' if p1 else '✗'} 健康德文 → 放行（占比 {r1:.3f}，判为 {l1}）")
    fail += not p1

    # ② 健康法文 → 不得报。**这是最要紧的一条**：第一版只有德语词表，
    #    11 份好好的法译本全被判成「已毁」。
    ok_fr = ("le la les de des du et en un une que qui dans pour est il ne pas "
             "cellule tissu maladie recherche " * 60)
    r2, l2, _ = rate(ok_fr)
    p2 = r2 >= FLOOR and l2 == "fr"
    print(f"  {'✓' if p2 else '✗'} 健康法文 → 放行且判为 fr（占比 {r2:.3f}，判为 {l2}）"
          f"——**语种判错会把整批健康语料报成坏的**")
    fail += not p2

    # ③ 长 s 的拉丁文 → **必须放行**。不折长 s 的话，
    #    一份完全可读的十八世纪拉丁文会被判成「已毁」（Jenner #104 实测 0.136–0.143）。
    longs_la = ("periodo ex aegro emilTo et alienae cuticulae infito vel ulceri immilTo "
                "contagium corpori ei communicet at experimentis conftat contagium hac "
                "methodo inferi non polTe id quoque verum eft materiam variolofam aqua "
                "dilutam et folita methodo cuti infitam variolofa fymptomata progignere " * 20)
    r5, l5, _ = rate(longs_la)
    p5 = r5 >= FLOOR
    print(f"  {'✓' if p5 else '✗'} 长 s 的拉丁文 → 放行（占比 {r5:.3f}，判为 {l5}）"
          f"——`eft`/`conftat`/`polTe` 都是 OCR 的长 s，不是坏文本")
    fail += not p5

    # ④ 折了长 s 之后，Fraktur 报废的仍须抓到（证明折叠没把判据折没了）
    r6, _, _ = rate(dead)
    p6 = 0 <= r6 < FLOOR
    print(f"  {'✓' if p6 else '✗'} 折长 s 之后，Fraktur 报废的仍抓到（占比 {r6:.3f}）")
    fail += not p6

    # ⑤ 词数不足 → 不判（短文本噪声太大）
    r3, _, n3 = rate("der die das und in zu den von")
    p3 = r3 < 0
    print(f"  {'✓' if p3 else '✗'} 词数 {n3} < {MIN_WORDS} → 不判，返回 -1")
    fail += not p3

    # ⑥ 空文本 → 不判，不得当作「已毁」
    r4, _, _ = rate("")
    p4 = r4 < 0
    print(f"  {'✓' if p4 else '✗'} 空文本 → 不判（不得当作已毁）")
    fail += not p4

    print("\n  ✓ 负对照通过（7/7）" if not fail
          else f"\n  ✗ {fail} 项未过——本检查器已失效，其「通过」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--ledger", type=pathlib.Path,
                    help="给了则检查：已毁的文件有没有被记作 P1（那是硬错）")
    ap.add_argument("--floor", type=float, default=FLOOR)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test and not a.paths:
        return 2 if self_test() else 0
    if not a.paths:
        ap.error("须给语料路径（除非只跑 --self-test）")

    rows = scan(a.paths)
    judged = [r for r in rows if r["rate"] >= 0]
    if not judged:
        print(f"没有词数 ≥{MIN_WORDS} 的文件——**本次未检查（不是通过）**")
        return 0

    dead = sorted((r for r in judged if r["rate"] < a.floor), key=lambda r: r["rate"])
    print(f"扫了 {len(rows)} 份，其中可判 {len(judged)} 份"
          f"（词数 <{MIN_WORDS} 的 {len(rows) - len(judged)} 份不判）")
    print(f"虚词占比下限 {a.floor}"
          f"（**从 227 份真实语料的分布里读出来的**：0.117–0.239 之间一份都没有）\n")

    if not dead:
        print("  ✓ 每一份的虚词占比都在下限之上——没有被 OCR 整份毁掉的")
        return 0

    print(f"  ⚠ **虚词占比低于下限的 {len(dead)} 份**（多半是 Fraktur／哥特体 OCR 认错字母）：")
    for r in dead:
        print(f"     {r['rate']:.3f} [{r['lang']}] n={r['words']:7d}  {r['path']}")
    print("\n  ★ 两类已知假阳，报出来之前先人工看一眼：\n"
          "     ① 词表里没有的语种（输出的「最佳语种」一栏是提示）\n"
          "     ② **索引／目录／表格**——它们天然没有虚词，文本本身可能完好")

    if not a.ledger or not a.ledger.is_file():
        print("\n  未给 --ledger：**只报告，不判这些文件有没有被当成一手源用**（不是通过）")
        return 0

    dead_paths = {pathlib.Path(r["path"]).name for r in dead}
    bad_p1 = []
    for line in a.ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("tier") == "P1" and pathlib.Path(rec.get("local_path", "")).name in dead_paths:
            bad_p1.append(rec.get("source_id", "?"))
    if bad_p1:
        print(f"\n  ✗ **已毁的文件里有 {len(bad_p1)} 条被记作 P1**："
              f"{', '.join(bad_p1[:8])}{' …' if len(bad_p1) > 8 else ''}")
        print("    你正打算从一份读不出字的文件里取逐字引文。**换干净扫本，或降级不作一手源。**")
        return 1
    print("\n  ✓ 已毁的文件都没有被记作 P1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
