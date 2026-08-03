#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#112 Nightingale：attribution_basis + 逐份挂 attribution。

**逐份点名，不用整批声明**（v0.0.0.24 那条整批声明曾把逐源检查整个关掉，绿了十版）。

写进去的每一条都来自抓源方逐份核过印刷页后写下的第 9 列，
**没核过的一律不写**。
"""
import json
import pathlib

WS = pathlib.Path("workspaces/florence-nightingale/florence-nightingale")
LED = WS / "evidence/source-ledger.jsonl"

IDS = {}
for line in pathlib.Path("raw/_ids.txt").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.startswith("#"):
        f = line.split("\t")
        if len(f) == 9:
            IDS[f[0]] = {"flags": [m for m in f[7].split(";") if m], "note": f[8],
                         "title": f[2], "year": f[3]}

# 归属标记 → 写进 attribution 的那句话
MARK_NOTE = {
    "HER-OWN": "**她本人署名。** 扉页或正文署名经抓源方逐份核过。",
    "COMMISSION-COLLECTIVE":
        "**委员会／部门集体署名的公文，不是她本人的文章。** "
        "她主导了那场调查是一回事，「这份文件是我写的」是另一回事——"
        "**不得以第一人称转述。**",
    "CO-AUTHORED": "**合著。** 合著不等于不是她写的，但「哪一部分是她的」要写清。",
    "THIRD-PARTY": "**第三方所写**，不属她的署名范畴——**不得以第一人称引用。**",
    "ATTRIBUTION-UNCLEAR":
        "⚠ **署名查不准。** 详见下方逐份记录里 `ATTRIBUTION CHECKED AND FLAGGED` 那一段。"
        "**可作旁证，不得拿它撑承重句，更不得以第一人称引用。**",
    "HAS-OWN-STATS":
        "★ **本份含她自己算出的数表**（表目见下方逐份记录）。"
        "v0.0.0.63 的实测声明门要求「说我量过的地方必须有数」——**这里就是那些数的来源。**",
    "FULL-PAGE-SCAN":
        "⚠ **整版扫图转文，同页可能混着别人的文章。** "
        "取逐字引文前先确认落在哪一段（`raw/_BOUNDARIES.json`）。",
    "DUPLICATE-SCAN": "同一材料的另一次扫描（**降 P2**）。",
    "OCR-POOR": "同一材料的降质 OCR（**降 P2**）。",
    "POSTHUMOUS": "身后出版，非其生前定稿（**降 P2**）。她 1910-08-13 卒。",
    "TRANSCRIPTION": "后人转录，非原扫本（**降 P2**）。",
    "TRANSLATION": "译本；她用英文写作（**降 P2**）。",
}

U_NOTE = ("**本份归 `U`（未定档）。** `P1` 的定义是「本人的话」，"
          "而本份给不出作者——**留在库里作证据，但不得作她的声音**。"
          "（降成 P2 是错的：P2 是「同一材料的降质版本」，与归属不确定不是一回事。）")

rows = [json.loads(l) for l in LED.read_text(encoding="utf-8").splitlines() if l.strip()]
n = 0
for r in rows:
    name = pathlib.Path(r.get("local_path", "")).parent.name
    if name not in IDS:
        name = (r.get("original_name") or "").rsplit(".", 1)[0]
    rec = IDS.get(name)
    if not rec:
        continue
    parts = [MARK_NOTE[m] for m in rec["flags"] if m in MARK_NOTE]
    if r.get("tier") == "U":
        parts.append(U_NOTE)
    parts.append("抓源逐份记录：" + rec["note"])
    r["attribution"] = "　".join(parts)
    n += 1

LED.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
               encoding="utf-8")

meta_p = WS / "meta.json"
if meta_p.is_file():
    m = json.loads(meta_p.read_text(encoding="utf-8"))

    # ★ `covered_sources` **逐份点名**，不用整批声明
    #   （v0.0.0.24 那条整批声明曾把逐源检查整个关掉，绿了十版）。
    covered = [
        {"source_id": r["source_id"],
         "original_name": r.get("original_name") or pathlib.Path(r["local_path"]).name,
         "locator": (r.get("locator") or "")[:200],
         "basis": (r.get("attribution") or "")[:400]}
        for r in rows
        if r.get("author") == "Florence Nightingale"
    ]

    m["attribution_basis"] = {
        "authority":
            "十九世纪人物，**署名证据不能靠正文里的 byline 找**——"
            "她的著作多为私人印行的单行本，署名在**扉页**，"
            "而扫本转文常把扉页排在正文之外或整页丢失。"
            "故本人物的归属依据是**抓源阶段逐份翻到印刷页核对**，"
            "结论写在 `raw/_ids.txt` 第 9 列，逐条抄进本条目的 `covered_sources`。\n\n"
            "① **有扉页署名的**：`notes-british-army-1858` 扉页印 `FLORENCE NIGHTINGALE.`，"
            "`notes-on-nursing`、`notes-on-hospitals`、`lying-in-institutions-1871` 等同类。\n"
            "② **无扉页署名、归 `U` 的三份**：见 `unattributed`。\n"
            "③ **委员会公文**：5 份标 `COMMISSION-COLLECTIVE`，`author` 留空——"
            "**她主导了那场调查是一回事，「这份文件是我写的」是另一回事。**",
        "citation":
            "Nightingale, Florence. *Notes on Matters Affecting the Health, Efficiency, "
            "and Hospital Administration of the British Army*. London, 1858（853 页，私人印行，"
            "扉页署名）；同氏 *Notes on Hospitals*, 1859 / 1863；"
            "*Notes on Nursing: What It Is, and What It Is Not*, 1859；"
            "*Introductory Notes on Lying-in Institutions*, 1871。",
        "disputed_policy":
            "**争议著作不为空——这是本人物与 Fleming #111 最大的不同。**\n"
            "十九世纪私人印行物大量匿名或以「Presented by request」体例刊行，"
            "**目录 creator 字段与印刷页经常不一致**。处置三条：\n"
            "**一、扉页无署名的一律归 `U`**，留作证据、不得作她的声音（三份，见 `disputed_works`）。\n"
            "**二、目录 creator 里有她的名字不等于署名**——"
            "`travelsinslavoni01mack` 的角色限定词是 `inscriber`（题赠者），序是格莱斯顿写的、"
            "签 `W.E.G.`；该份已下载核对后删除。\n"
            "**三、同名四类**逐条记在 `raw/_EXCLUDED.txt`，每条附著录原文。"
            "**最险的一条是 Florence Nightingale David（1909–1993）**——"
            "她也是统计学家、且以本人物命名，"
            "唯一可靠判别式是 creator 字段里的生卒年。",
        "disputed_works": [
            {"what": "Mortality of the British Army（1858，玫瑰图背后的表）",
             "why": "扉页无署名，全文里 `Nightingale` 一次都不出现；扉页写着"
                    "「[Reprinted from the Report of the Royal Commission…]」。"
                    "**两条 archive.org 记录彼此打架**："
                    "`mortalityofbriti00lond` 无 creator 字段，"
                    "`mortality-of-the-british-army` 写 `Florence Nightingale`。"
                    "**表是她的乃是公认，但文件本身没这么说。** 归 `U`。"},
            {"what": "The Institution of Kaiserswerth on the Rhine（1851）",
             "why": "1851 年匿名刊行，全文无其姓；唯一依据是 archive.org/Wellcome 的 "
                    "creator 字段 `Nightingale, Florence, 1820-1910`。归 `U`。"},
            {"what": "Subsidiary Notes as to the Introduction of Female Nursing（1858）",
             "why": "扉页无署名（已对 Project Gutenberg 清本核过），"
                    "**正文用第三人称称她**（`Miss Nightingale is recognized by "
                    "Her Majesty's Government…`）。"
                    "**同年、同印厂、同「Presented by request」体例的 "
                    "`notes-british-army-1858` 扉页印着 `FLORENCE NIGHTINGALE.`——这一本没有。** 归 `U`。"},
        ],
        "exclusions": [
            {"what": "Florence Nightingale David（1909–1993）的著作",
             "why": "同名不同人。creator 字段原文 `David, F. N. (Florence Nightingale), 1909-1993`；"
                    "题材为对称函数与概率史。**她也是统计学家且以本人物命名，本批最危险的混淆源。**"},
            {"what": "以商号 Elizabeth Arden 著录者（1878–1966）的著作",
             "why": "生卒年与题材（Beauty, Personal; Cosmetics）皆不容。"
                    "**「Arden 即 Florence Nightingale Graham」这一身份不是本次检索证实的，未作判据使用。**"},
            {"what": "Florence Nightingale Boyd, M.D. 的讣告",
             "why": "其讣告在 BMJ 1910 **vol.1** pp.1582-3，本人物讣告在同刊 **vol.2** pp.437-9"
                    "——同年同刊，**卷次即可分**。"},
            {"what": "`travelsinslavoni01mack`（角色误认，非同名）",
             "why": "creator 字段里确有她，但角色限定词是 **inscriber**（她在书上写了赠言）；"
                    "序是格莱斯顿写的、签 `W.E.G.`。"
                    "**名字在 creator 字段里不等于署名。** 已下载核对后删除。"},
        ],
        "counting_convention":
            f"covered_sources 逐份点名 {len(covered)} 条署她名的源，"
            "不使用整批声明（v0.0.0.24 曾因整批声明导致逐源检查整个关闭，v0.0.0.34 已堵）。\n"
            "**`author` 只在 `HER-OWN` 时填**；`COMMISSION-COLLECTIVE` 与 `THIRD-PARTY` 一律留空"
            "——留空是下游「不得以第一人称引用」的机器可读依据。\n"
            "**分档**：P1 35 + P2 44 + S1 20 + S2 15 + U 3 = 117；"
            "一手占比 79/117 = **0.6752**（deep 门 0.65）。",
        "covered_sources": covered,
    }
    meta_p.write_text(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")

print(f"attribution 逐条挂 {n} 条 / 共 {len(rows)} 条")
missing = [pathlib.Path(r.get("local_path", "")).parent.name
           for r in rows if not r.get("attribution")]
if missing:
    print(f"⚠ **{len(missing)} 条没挂上**：{missing[:6]}")
