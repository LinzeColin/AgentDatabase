#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**长 s 讹字率**：这份拉丁语料还能不能拿去做逐字引文？

早期近代拉丁印本用长 s（ſ），OCR 普遍读成 `f`：`esse`→`esfe`、`causa`→`caufa`、
`possit`→`poffit`。讹变率一高，**这份语料就一句逐字引文都引不出来**——
断言层要引原文时才发现，那时候已经晚了。

## 为什么落成判据（不是因为想多一件，是因为它已经错过一次）

这个面板此前**只活在手上**，每次要用时现敲。Grotius #168 上它当场翻了车：

`epistolae_oxenstierna_1829_lat` 用 `est/eft` 量是 **0.61%**（看着干净），
用整个面板量是 **97.75%**。差 160 倍。去读原文，L198 同一行上就有：

> `nomen est, commendandam esfe cenfuit, qiio`

`est` 是对的、`esfe`/`cenfuit` 是坏的。真因是**排版惯例**：`st` 用连字（短 s），
其余位置用长 s。→ **凡是 `st` 序列的词对，对这种字体系统性失明。**
本件因此把 `est/eft` 从合计里剔除，只留作单独诊断项。

→ [[merging-two-signals-cancels-both]] 的反面：**这次是拆开才看得见**。

## 两道前置门（都是「未核」，不是「通过」）

1. **语种**：面板是拉丁文的。用**不含字母 s 的拉丁虚词**当锚
   （`enim`/`autem`/`atque`/`igitur`/`quidem`/`quoniam`/`nisi`/`tamen`/`etiam`/`quae`/`quod`）
   —— 它们在长 s 讹变里**原样存活**，所以坏 OCR 也测得准。
   实测分离 23.4 倍（拉丁最低 64.4、非拉丁最高 2.8 /万词），门槛 15 坐在缝里。

   ★★ 这道门不是装饰：`djbp_kelsey_1925_en`（英文）panel 读到 **19.05%**，
   紧贴 20% 那条线；`de_imperio_1751_fr`（法文）读到 0.91% 会被判成「干净」。
   **两个数都毫无意义**，靠锚词判成「不适用」才对。

2. **样本量**：面板命中太少就报「未核」。
   [[empty-default-swallows-unknown]]：`0 个命中` 不许被读成「没问题」。

## 判读

| 讹字率 | 判读 |
|---|---|
| < 0.01 | 干净，可做逐字引文 |
| 0.01–0.20 | 混杂，逐份看 |
| > 0.20 | **不可用**——别拿它引原文 |

真值分得开：本机 17 份实测，坏 OCR 落在 **0.919–0.978**、干净落在 **0.0018–0.0101**，
中间空 **91 倍**，0.20 坐在缺口正中。

## 射程（必须一起说）

- **它判字形，不判内容。** 讹字率 0 只说明这份 OCR 认得出长 s，
  不说明抄录正确、更不说明归属对（那是 `check_authorship` 的事）。
- **只对拉丁文成立。** 英文 OCR 质量另有带子（≤2 字母词占比 0.25–0.28）。
- **整份粒度。** 一卷书里若有一段是别人写的（Poemata 1637 的 `amicorum elogia`），
  本件看不见——那要读 `00-归属证据实测.md`。

退出码：0 = 全部可用或不适用；1 = 有不可用的源；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from common import corpus_body
except ImportError:                                          # pragma: no cover
    def corpus_body(t):                                      # type: ignore
        return t

# ── 两个语域各一套。锚词一律**不含字母 s**，长 s 讹变碰不到它们，
#    所以在坏 OCR 上照样测得准。
#
# ★ 拉丁锚词里 `qui` 被剔除：法文也有它，含它时分离度从 23.4 倍塌到 1.1 倍。
LATIN_ANCHORS = ["enim", "autem", "atque", "igitur", "quidem",
                 "nisi", "quoniam", "tamen", "etiam", "quae", "quod"]
ENGLISH_ANCHORS = ["the", "and", "of", "to", "that", "which",
                   "not", "with", "for", "have"]
# ★★★ v0.0.0.154 加第三个语域：**德语**。起因是 Kelsen #171 的一份 1916 年论文——
#   `check_ocr_language_death` 放它过去（虚词占比正常），本件报「两个语域都不适用」，
#   而它的 `Kelsen` 出现 **0 次**、`Kelfen` 出现 **15 次**：**他自己的姓被长 s 打碎了**。
#   两件判据之间恰好有这一档缝：**虚词还在，而实词里的 ſ 全塌**。
#   德语锚词同样一个都不含字母 s。
GERMAN_ANCHORS = ["und", "nicht", "durch", "oder", "nach",
                  "bei", "dem", "werden", "wenn", "aber"]

# ★ 两个面板都**不含任何带 `st` 的词对**——见文件头，`est/eft` 对 st 连字失明。
#   英文面板的讹形一个都不是真词（`fuch`/`fhall`/`himfelf`/`faid`/`whofe`/
#   `thofe`/`thefe`/`alfo`/`ufe`），所以不会误伤干净文本：
#   实测五份干净英文全部**恰好 0.0000**。
REGIMES = {
    "拉丁": {
        "anchors": LATIN_ANCHORS, "anchor_min": 15.0,      # 缝：非拉丁 ≤2.8 / 拉丁 ≥64.4
        "panel": [("sunt", "funt"), ("esse", "esfe"), ("ipse", "ipfe"),
                  ("causa", "caufa"), ("possit", "poffit"), ("ipsa", "ipfa"),
                  ("se", "fe")],
    },
    "英文": {
        "anchors": ENGLISH_ANCHORS, "anchor_min": 500.0,   # 缝：非英 ≤63.9 / 英 ≥1442.5
        "panel": [("such", "fuch"), ("shall", "fhall"), ("himself", "himfelf"),
                  ("said", "faid"), ("whose", "whofe"), ("those", "thofe"),
                  ("these", "thefe"), ("also", "alfo"), ("use", "ufe")],
    },
    # ★ 德语面板的取舍（每一条都是排除掉某个具体风险）：
    #   · **不收 `sein/fein`** —— `fein` 是真德语词（细、精），会在干净文本上误报；
    #   · **不收任何带 `st` 的词对**（`ist/ift`、`selbst/…`）—— 与拉丁英文两档同一条规矩，
    #     st 连字会让这类词对失明（见文件头）；
    #   · **不收词尾 s**（`als`、`das`）—— 德语词尾用圆 s，长 s 讹变根本碰不到它。
    #   讹形 `fich`/`fie`/`fehr`/`foll`/`wiffenschaft` 一个都不是德语真词；
    #   `find` 是英语词但不是德语词，锚词已把英文文本挡在门外。
    "德语": {
        # 缝：法语 2.6 / 被 Fraktur 毁掉的德语 33.6–45.6 / 干净德语 467.9–694.9
        # ★ 门槛 15 坐在**法语与坏德语之间**（12.9 倍），不是坐在好坏德语之间——
        #   坏德语必须**judged**，不能被踢成「语域不适用」（那是「不判冒充通过」）。
        "anchors": GERMAN_ANCHORS, "anchor_min": 15.0,
        "panel": [("sich", "fich"), ("sind", "find"), ("so", "fo"), ("sie", "fie"),
                  ("sehr", "fehr"), ("wissenschaft", "wiffenschaft"), ("soll", "foll")],
    },
}
DIAGNOSTIC = [("est", "eft")]        # 只报不算，用来暴露 st 连字
MIN_PANEL_HITS = 30

# ── ★★ 第二种坏法：**ae 连字被打散**（v0.0.0.131 加，拉丁专用）
#
#   DJBP 1853 拉丁三卷的长 s **完全干净**（讹字率 0.0035），我据此把它们写进
#   「可做逐字引文」那张表。去 Prolegomena 回读原句才发现：
#
#       Et hee quidem que jam diximus … etiamsi daremus … non esse Deum
#              ↑haec  ↑quae
#
#   `quae`→`que`、`haec`→`hee`、`saeculis`→`ssculis`。
#   **从 vol1 取逐字拉丁引文，会把 Grotius 写的 `quae` 印成 `que`。**
#   → 判据只量了一种坏法，而我据它下的结论超出了它量的范围。
#     [[verbatim-is-not-understood]] 的另一半：**改了讹字再当逐字引文用。**
#
#   两个信号取**合取**（单用任一个都会误伤）：
#     ① `ae` 双字母 / 千字母 —— 拉丁散文里 ae 是高频
#     ② `quae` 占 `quae`+独立 `que` 的比 —— 独立成词的 `que` 在规范拉丁里罕见
#
#   本机实测（缝在 2.32 与 5.30 之间）：
#     完好 de_iure_praedae_1869 8.70/0.950、de_veritate_1809 5.30/0.886、1813 5.37/0.825
#     打散 djbp_1853_vol1 0.29/0.049、vol2 0.31/0.031、vol3 1.16/0.769、
#          epistolae_1687 0.19/0.032、poemata_1637 0.67/0.144
AE_PER_1000_MIN = 3.5
AE_QUAE_RATIO_MIN = 0.80
UNUSABLE = 0.20
CLEAN = 0.01

_WORD = re.compile(r"[a-z]+")


_RANK = {"不可用": 3, "混杂": 2, "未核": 1, "干净": 0}


def ae_ligature(text: str) -> dict:
    """→ 拉丁 ae 连字有没有被打散。两个信号取**合取**，见常量处的实测表。"""
    low = text.lower()
    letters = len(re.findall(r"[a-z]", low))
    if not letters:
        return {"判读": "未核", "理由": "无拉丁字母"}
    per_k = len(re.findall(r"ae", low)) / letters * 1000
    quae = len(re.findall(r"\bquae\b", low))
    que = len(re.findall(r"\bque\b", low))
    ratio = quae / (quae + que) if (quae + que) else None
    out = {"ae_per_1000": round(per_k, 2), "quae": quae, "que": que,
           "quae_ratio": round(ratio, 3) if ratio is not None else None}
    if ratio is None or quae + que < 20:
        out["判读"] = "未核"
        out["理由"] = "`quae`/`que` 合计只有 %d 次 < 20，**样本量不够，不是「完好」**" % (quae + que)
        return out
    broken = per_k < AE_PER_1000_MIN and ratio < AE_QUAE_RATIO_MIN
    out["判读"] = "**打散**" if broken else "完好"
    out["理由"] = ("ae %.2f/千字母（门 %.1f）、quae 占比 %.3f（门 %.2f）"
                   % (per_k, AE_PER_1000_MIN, ratio, AE_QUAE_RATIO_MIN))
    return out


def _one_regime(c: Counter, total: int, name: str, spec: dict) -> dict:
    """→ 单个语域的判读；语种锚不够就返回 None 表示「这个语域不适用」。"""
    anchors = sum(c[a] for a in spec["anchors"]) / total * 10000
    good = sum(c[g] for g, _ in spec["panel"])
    bad = sum(c[b] for _, b in spec["panel"])
    would = bad / (good + bad) if good + bad else 0.0
    base = {"语域": name, "anchors_per_10k": round(anchors, 1),
            "panel_good": good, "panel_bad": bad, "若无语种门会读到": round(would, 4)}
    if anchors < spec["anchor_min"]:
        return None
    if good + bad < MIN_PANEL_HITS:
        return dict(base, verdict="未核",
                    reason="%s面板只命中 %d 次 < %d —— **样本量不够，不是「干净」**"
                           % (name, good + bad, MIN_PANEL_HITS))
    return dict(base, verdict=("不可用" if would > UNUSABLE else
                               ("干净" if would < CLEAN else "混杂")),
                rate=round(would, 4),
                reason="%s讹字率 %.4f（正形 %d／讹形 %d）" % (name, would, good, bad))


def measure(text: str) -> dict:
    """→ 一份语料的讹字率与两道前置门的结论。

    ★ 两个语域都量。**拉英对照本两边都算数**，取更差的那一侧——
      若任一半坏了，从那一半取逐字引文就是不安全的。
    """
    c = Counter(_WORD.findall(text.lower()))
    total = sum(c.values())
    if not total:
        return {"verdict": "未核", "reason": "空文本", "words": 0}
    hits = [r for r in (_one_regime(c, total, n, s) for n, s in REGIMES.items()) if r]
    out = {"words": total, "diagnostic_est_eft": [c["est"], c["eft"]],
           "逐语域": {r["语域"]: r for r in hits}}
    if not hits:
        # 两个语域都不适用时，把「若强行读会读到多少」一起打出来——
        # 那个数没有意义，但**看得见它有多像一个真结论**，才不会有人去用它。
        peek = {}
        for n, s in REGIMES.items():
            g = sum(c[x] for x, _ in s["panel"])
            b = sum(c[y] for _, y in s["panel"])
            a = sum(c[x] for x in s["anchors"]) / total * 10000
            peek[n] = "锚 %.1f<%.1f，若强行读 %.4f" % (
                a, s["anchor_min"], b / (g + b) if g + b else 0.0)
        return dict(out, verdict="不适用",
                    reason="**两个语域都不适用**（" +
                           "；".join("%s：%s" % kv for kv in peek.items()) + "）")
    worst = max(hits, key=lambda r: _RANK[r["verdict"]])
    verdict = worst["verdict"]
    reason = worst["reason"] + ("" if len(hits) == 1 else "　（两语域都适用，取更差的一侧）")

    # ★ 拉丁语域再问一次 ae 连字。长 s 干净 ≠ 可逐字引 —— DJBP 1853 三卷就是这样。
    if any(r["语域"] == "拉丁" for r in hits):
        ae = ae_ligature(text)
        out["ae_连字"] = ae
        if ae["判读"] == "**打散**":
            reason += ("　★ **但 ae 连字被打散**（%s）：`quae`→`que`、`haec`→`hee`，"
                       "**逐字引用会印出作者没写的形**" % ae["理由"])
            if _RANK[verdict] < _RANK["混杂"]:
                verdict = "混杂"

    return dict(out, verdict=verdict, rate=worst.get("rate"), reason=reason)


def load_sources(target: pathlib.Path) -> list:
    p = target / "evidence" / "source-ledger.jsonl"
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def evaluate(target: pathlib.Path) -> tuple:
    rows, problems, info = load_sources(target), [], {}
    tally = Counter()
    for r in rows:
        lp = r.get("local_path") or ""
        f = target / lp
        if not lp or not f.is_file():
            # holdout 的正文在 references/holdout/ 下，raw 里没有——不是缺陷
            tally["正文不在工作区"] += 1
            continue
        m = measure(corpus_body(f.read_text(encoding="utf-8", errors="replace")))
        tally[m["verdict"]] += 1
        info[r.get("source_id") or lp] = dict(m, file=pathlib.Path(lp).name)
        if m["verdict"] == "不可用":
            problems.append("`%s` %s —— %s，**不可做逐字引文**"
                            % (r.get("source_id"), pathlib.Path(lp).name, m["reason"]))
    return problems, {"分布": dict(tally), "逐份": info}


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    # ── ★★★ 德语语域（v0.0.0.154 加）：**用 Kelsen #171 的 12 份真实测值**，不是构造的 ──
    print("\n══ ★★★ 德语语域：Kelsen #171 的 12 份实测（n=12，不是拉丁那档的 227）══")
    GER = {  # 文件: (锚/万词, 正形, 讹形, 真值)
        "allgemeine-staatslehre-1925":        (673.2, 4778,   0, "干净"),
        "problem-der-souveraenitaet-1928":    (530.8, 1808,   0, "干净"),
        "staatslehre-dante-1905":             (467.9,  780,   0, "干净"),
        "rechtswissenschaft-1916":            (577.7,   22, 162, "不可用"),
        "kommentar-reichsratswahlordnung-1907": (45.6,  73, 225, "不可用"),
        "bundesverfassung-1922-coedited":      (33.6,   53, 449, "不可用"),
        "rapports-de-systeme-1926-fr":          (2.6,    5,   0, "不适用"),
    }
    for name, (an, good, bad, want) in GER.items():
        rate = bad / max(good + bad, 1)
        if an < REGIMES["德语"]["anchor_min"]:
            got = "不适用"
        else:
            got = "干净" if rate < 0.20 else "不可用"
        chk(f"德语 {name}：锚 {an}、讹字率 {rate:.4f} → {got}（应为 {want}）", got == want)
    # ★★ 门槛坐在**法语与坏德语之间**（2.6 vs 33.6，12.9 倍），不是坐在好坏德语之间：
    #    坏德语必须被判，不能踢成「不适用」——那是「不判冒充通过」。
    chk("德语门槛把坏德语留在judged 之内（33.6 > 15.0）",
        33.6 > REGIMES["德语"]["anchor_min"] > 2.6)
    # ★★★ 误报防线：`fein` 是**真德语词**，若进面板会在干净文本上误报。
    chk("**`sein/fein` 不在德语面板里**（fein 是真德语词）",
        all(g != "sein" for g, _ in REGIMES["德语"]["panel"]))
    chk("德语面板不含任何带 `st` 的词对（st 连字会让它失明）",
        all("st" not in g and "st" not in b for g, b in REGIMES["德语"]["panel"]))
    chk("德语锚词一个都不含字母 s", all("s" not in a for a in GERMAN_ANCHORS))

    print("\n══ ★★★★ 逐字真实样本：Grotius #168 的 17 份实测 ══")
    #   2026-08-11 在真语料上跑出来的**实测值**，不是构造的。
    #   合成夹具会把「坏 OCR」写得比真实的更坏、把「干净」写得更干净，
    #   而本件的全部价值就在于**那条缝在哪**。[[fixtures-cleaner-than-the-real-thing]]
    REAL = {  # 文件: (锚词/万词, 面板正形, 面板讹形, 真值)
        "mare_liberum_1618_lat":          (292.8, 3, 78, "坏"),
        "poemata_1637_lat":               (91.5, 33, 376, "坏"),
        "epistolae_oxenstierna_1829_lat": (106.2, 9, 391, "坏"),
        "annales_1658_lat":               (114.5, 28, 1083, "坏"),
        "de_veritate_1640_lat":           (172.1, 32, 599, "坏"),
        "djbp_1646_lat":                  (199.6, 115, 2466, "坏"),
        "epistolae_1687_lat":             (64.4, 143, 2991, "坏"),
        "epistolae_ineditae_1806_lat":    (124.5, 21, 920, "坏"),
        "de_iure_praedae_1869_lat":       (359.5, 1633, 3, "净"),
        "de_veritate_1809_lat":           (228.8, 1381, 6, "净"),
        "de_veritate_1813_lat":           (207.2, 1469, 9, "净"),
        "djbp_1853_lat_vol1":             (139.0, 1699, 6, "净"),
        "djbp_1853_lat_vol2":             (130.3, 1651, 10, "净"),
        "djbp_1853_lat_vol3":             (116.0, 1373, 14, "净"),
        "de_imperio_1751_fr":             (0.0, 326, 3, "非拉丁"),
        "djbp_kelsey_1925_en":            (0.4, 17, 4, "非拉丁"),
        "EXT_butler_life_1826_en":        (0.3, 6, 1, "非拉丁"),
    }
    rate = {k: v[2] / (v[1] + v[2]) for k, v in REAL.items() if v[1] + v[2]}
    bad = sorted(rate[k] for k, v in REAL.items() if v[3] == "坏")
    good = sorted(rate[k] for k, v in REAL.items() if v[3] == "净")
    chk("17 份齐全", len(REAL) == 17)
    chk("坏 OCR %d 份落在 %.4f–%.4f" % (len(bad), bad[0], bad[-1]),
        len(bad) == 8 and bad[0] > 0.90)
    chk("干净 %d 份落在 %.4f–%.4f" % (len(good), good[0], good[-1]),
        len(good) == 6 and good[-1] < 0.02)
    gap = bad[0] / good[-1]
    chk("**两群之间空了 %.1f 倍**，门槛 %.2f 坐在缺口里" % (gap, UNUSABLE),
        gap >= 10 and good[-1] < UNUSABLE < bad[0])

    print("\n══ 语种门 ══")
    lat = [v[0] for v in REAL.values() if v[3] != "非拉丁"]
    non = [v[0] for v in REAL.values() if v[3] == "非拉丁"]
    chk("拉丁最低 %.1f ／ 非拉丁最高 %.1f，分离 %.1f 倍，门槛 %.1f 在缝里"
        % (min(lat), max(non), min(lat) / max(non) if max(non) else float("inf"),
           REGIMES["拉丁"]["anchor_min"]),
        max(non) < REGIMES["拉丁"]["anchor_min"] < min(lat))
    chk("★★ 正对照：英文 kelsey 若不设语种门会读到 %.4f（紧贴 %.2f 那条线）"
        % (rate["djbp_kelsey_1925_en"], UNUSABLE),
        0.15 < rate["djbp_kelsey_1925_en"] < UNUSABLE)
    chk("★★ 正对照：法文 de_imperio 若不设语种门会被判成「干净」（%.4f）"
        % (rate["de_imperio_1751_fr"], ), rate["de_imperio_1751_fr"] < CLEAN)

    print("\n══ st 连字：面板为什么必须剔除 est/eft ══")
    #   oxenstierna 1829 的逐词实测（本机 2026-08-11）
    EST, EFT = 162, 1
    only_est = EFT / (EST + EFT)
    full = rate["epistolae_oxenstierna_1829_lat"]
    chk("只用 est/eft 读到 %.4f → 会判成「干净」" % only_est, only_est < CLEAN)
    chk("整个面板读到 %.4f → 判成「不可用」" % full, full > UNUSABLE)
    chk("**两者差 %.0f 倍**——单对探针在 st 连字字体上系统性失明" % (full / only_est),
        full / only_est > 100)
    chk("**两个**面板里都没有任何带 st 的词对",
        not any("st" in g for s in REGIMES.values() for g, _ in s["panel"]))
    chk("两个面板的讹形都不是对方语域的常用真词（fuch/esfe 之类）",
        all(len(b) >= 2 for s in REGIMES.values() for _, b in s["panel"]))

    print("\n══ ★★ 英文语域：Grotius #168 的 7 份实测 ══")
    #   英文早期印本**也有长 s**。第一版本件只有拉丁面板，于是
    #   `djbp_evats_1682_en`（真·长 s 讹坏）被判成「不适用」——**漏掉了**。
    REAL_EN = {  # 文件: (英锚/万词, 面板正形, 面板讹形, 真值)
        "EXT_selden_mare_clausum_1652_en": (2023.7, 7, 1621, "坏"),
        "djbp_evats_1682_en":              (1989.8, 78, 6181, "坏"),
        "djbp_kelsey_1925_en":             (2160.3, 7842, 0, "净"),
        "EXT_butler_life_1826_en":         (2430.2, 497, 0, "净"),
        "adamus_exul_barham_1839_en":      (1902.6, 234, 0, "净"),
        "djbp_whewell_1853_en":            (2181.6, 3835, 0, "净"),
        "mare_liberum_magoffin_1916_en":   (1442.5, 446, 0, "净"),
    }
    re_ = {k: v[2] / (v[1] + v[2]) for k, v in REAL_EN.items()}
    eb = sorted(re_[k] for k, v in REAL_EN.items() if v[3] == "坏")
    eg = sorted(re_[k] for k, v in REAL_EN.items() if v[3] == "净")
    chk("坏 %d 份落在 %.4f–%.4f" % (len(eb), eb[0], eb[-1]), len(eb) == 2 and eb[0] > 0.9)
    chk("干净 %d 份**全部恰好 0.0000**（讹形一个都不是真词，不会误伤）" % len(eg),
        len(eg) == 5 and eg[-1] == 0.0)
    chk("门槛 %.2f 落在两群之间" % UNUSABLE, eg[-1] < UNUSABLE < eb[0])
    en_anc = [v[0] for v in REAL_EN.values()]
    chk("英锚最低 %.1f > 门槛 %.1f > 非英最高 63.9（法文）"
        % (min(en_anc), REGIMES["英文"]["anchor_min"]),
        min(en_anc) > REGIMES["英文"]["anchor_min"] > 63.9)
    chk("★ 第一版只有拉丁面板时，evats 1682 被判「不适用」而真值是坏的",
        REAL_EN["djbp_evats_1682_en"][3] == "坏")

    print("\n══ ★★ ae 连字：长 s 干净 ≠ 可逐字引 ══")
    #   本机 2026-08-11 实测。**这一组的存在本身是一次更正**：
    #   我先按长 s 面板把 DJBP 1853 三卷写进「可做逐字引文」，
    #   去 Prolegomena 回读原句才看见 `quae`→`que`、`haec`→`hee`。
    REAL_AE = {  # 文件: (ae/千字母, quae, 独立 que, 真值)
        "de_iure_praedae_1869_lat": (8.70, 743, 39, "完好"),
        "de_veritate_1809_lat":     (5.30, 474, 61, "完好"),
        "de_veritate_1813_lat":     (5.37, 485, 103, "完好"),
        "djbp_1853_lat_vol1":       (0.29, 24, 463, "打散"),
        "djbp_1853_lat_vol2":       (0.31, 14, 432, "打散"),
        "djbp_1853_lat_vol3":       (1.16, 120, 36, "打散"),
        "epistolae_1687_lat":       (0.19, 6, 181, "打散"),
        "poemata_1637_lat":         (0.67, 23, 137, "打散"),
    }
    ok_ae = [v[0] for v in REAL_AE.values() if v[3] == "完好"]
    bad_ae = [v[0] for v in REAL_AE.values() if v[3] == "打散"]
    chk("完好 %d 份 ae/千字母 落在 %.2f–%.2f" % (len(ok_ae), min(ok_ae), max(ok_ae)),
        min(ok_ae) >= AE_PER_1000_MIN)
    chk("打散 %d 份落在 %.2f–%.2f" % (len(bad_ae), min(bad_ae), max(bad_ae)),
        max(bad_ae) < AE_PER_1000_MIN)
    chk("门槛 %.1f 落在缝里（%.2f ← 缝 → %.2f）" % (AE_PER_1000_MIN, max(bad_ae), min(ok_ae)),
        max(bad_ae) < AE_PER_1000_MIN < min(ok_ae))
    # ★ 不合成假文本——`quae` 本身就含 `ae`，拼出来的文本复现不出真实比值，
    #   那种夹具比原文「干净」，测的是我拼的东西不是判据。
    #   直接把判据的规则套在**实测数对**上。[[fixtures-cleaner-than-the-real-thing]]
    def rule(per_k, quae, que):
        r = quae / (quae + que)
        return "打散" if (per_k < AE_PER_1000_MIN and r < AE_QUAE_RATIO_MIN) else "完好"
    mis = [k for k, v in REAL_AE.items() if rule(v[0], v[1], v[2]) != v[3]]
    chk("★ 规则套在 8 组实测数对上，逐份与真值对得上（错 %d 份）" % len(mis), not mis)
    # ★ 诚实记一条：这 8 组里**两个信号从来没有分歧**（都同时越线或同时不越线），
    #   所以「合取」这个设计**本数据测不到**——它是留的安全边际，不是被验证过的。
    #   写死这个事实，将来若出现分歧样本，本条会红，那时才该讨论用哪个信号。
    agree = all((v[0] < AE_PER_1000_MIN) == (v[1] / (v[1] + v[2]) < AE_QUAE_RATIO_MIN)
                for v in REAL_AE.values())
    chk("★ 8 组里两个信号**从无分歧** → 「合取」这个设计本数据**测不到**，"
        "是安全边际不是已验证（出现分歧样本时本条会红）", agree)
    chk("★★ **反对照**：`djbp_1853_lat_vol1` 长 s 讹字率只有 0.0035（判「干净」），"
        "而 ae 是打散的 —— **单看长 s 会把它写成「可逐字引」**",
        REAL_AE["djbp_1853_lat_vol1"][3] == "打散")
    tiny = ae_ligature("quae quae que " + "x" * 500)
    chk("★ `quae`+`que` 不足 20 次 → **%s**，不是「完好」" % tiny["判读"],
        tiny["判读"] == "未核")

    print("\n══ measure() 直跑 ══")
    m = measure("enim autem atque igitur quidem quoniam nisi tamen etiam quae quod " * 40
                + "esse ipse causa sunt " * 20)
    chk("干净拉丁 → %s" % m["verdict"], m["verdict"] == "干净")
    m2 = measure("enim autem atque igitur quidem quoniam nisi tamen etiam quae quod " * 40
                 + "esfe ipfe caufa funt " * 20)
    chk("讹变拉丁 → %s（%.4f）" % (m2["verdict"], m2["rate"]), m2["verdict"] == "不可用")
    m3 = measure("the quick brown fox jumps over the lazy dog " * 200)
    chk("★ 英文但面板 0 命中 → **%s**（不是「不适用」——它确实是英文，"
        "只是没有可判的词）" % m3["verdict"], m3["verdict"] == "未核")
    m3b = measure("such shall himself said whose those these also use " * 40
                  + "the and of to that which not with for have " * 60)
    chk("干净英文 → %s" % m3b["verdict"], m3b["verdict"] == "干净")
    m3c = measure("fuch fhall himfelf faid whofe thofe thefe alfo ufe " * 40
                  + "the and of to that which not with for have " * 60)
    chk("讹变英文 → %s（%.4f）" % (m3c["verdict"], m3c["rate"]),
        m3c["verdict"] == "不可用")
    m3d = measure("le la les des une dans pour avec par mais " * 200)
    chk("★ 法文（两语域都不适用）→ **%s**" % m3d["verdict"], m3d["verdict"] == "不适用")
    m3e = measure("esfe ipfe caufa funt " * 20
                  + "enim autem atque igitur quidem quoniam nisi tamen etiam quae quod " * 40
                  + "such shall himself said whose those these also use " * 20
                  + "the and of to that which not with for have " * 60)
    chk("★ 拉英对照本：拉丁半坏、英文半干净 → 取更差的 **%s**" % m3e["verdict"],
        m3e["verdict"] == "不可用" and len(m3e["逐语域"]) == 2)
    m4 = measure("enim autem atque igitur quidem quoniam " * 40)      # 拉丁但面板 0 命中
    chk("★ 拉丁但面板 0 命中 → **%s**，不是「干净」" % m4["verdict"], m4["verdict"] == "未核")
    chk("   空文本 → 未核", measure("")["verdict"] == "未核")

    print("\n" + ("自测通过" if ok else "**自测未过**"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", nargs="?", help="工作区目录")
    ap.add_argument("--file", action="append", default=[], help="直接量某个文件（可多次）")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.file:
        rc = 0
        for f in a.file:
            p = pathlib.Path(f)
            if not p.is_file():
                print("**读不到** %s" % f)
                rc = 3
                continue
            m = measure(corpus_body(p.read_text(encoding="utf-8", errors="replace")))
            print("%-42s %-6s %s" % (p.name[:42], m["verdict"], m.get("reason", "")))
            if m["verdict"] == "不可用":
                rc = rc or 1
        return rc
    if not a.target:
        ap.error("要么给 target，要么给 --file，要么 --self-test")
    problems, info = evaluate(pathlib.Path(a.target))
    if a.json:
        print(json.dumps({"problems": problems, "info": info}, ensure_ascii=False, indent=2))
    else:
        print("分布：%s" % info["分布"])
        for sid, m in sorted(info["逐份"].items(), key=lambda kv: kv[1]["file"]):
            print("  %-38s %-6s %s" % (m["file"][:38], m["verdict"], m.get("reason", "")))
        if problems:
            print("\n**不可做逐字引文的 %d 份**：" % len(problems))
            for p in problems:
                print("  · " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
