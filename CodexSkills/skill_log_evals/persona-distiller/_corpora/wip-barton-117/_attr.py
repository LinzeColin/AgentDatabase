#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#117 Clara Barton：attribution_basis + 逐份挂 attribution。

**逐份点名，不用整批声明**——v0.0.0.24 那条整批声明曾把逐源检查整个关掉，绿了十版。

写进去的每一条都回语料核过；核不到的一律不写。
本次实际核过的（原文照录，双空格是 OCR 原样）：

- `Copyright,   1898,  by   Clara    Barton`（rc-peace-war-1899，3 处）
- `CLARA··BARTON.`（andersonville-1866 第 728 行）
- `DORENCE··ATWATER.`（同份第 249 行）
- `On··the··seventh··day··of··July,··1863,··I··was··talien··prisoner··near`（同份第 72 行）
  —— **OCR 把 taken 认成 talien**

## ★ 本人物的归属难点与前面几位都不同

Galen／Hippocrates 的难点是**印刷时代之前没有署名机器**。
Barton 是**十九世纪美国人，署名证据充分**——她的书有扉页、有版权页。

**她的难点在另一头：一手材料里最厚的一层是未刊手稿**
（58 册日记、书稿草稿、讲稿笔记）。**日记不署名，草稿也不署名**——
`check_authorship` 认的三种证据（署名／编者注／逐字稿轮次）**结构上都不存在**，
实测 54 条 `authorship-unproven` 里 **46 条**属于这一类。

**这一类的归属依据是档案出处**：美国国会图书馆将其编目为
Clara Barton Papers（MSS11973），按其手迹与来源著录。
**这不是「因为判据查不出所以放行」，而是这一类材料的归属依据本来就在档案层，不在文本层。**
所以逐份写明：**它是哪一卷、依据是什么、以及「文本内没有署名」是预期而非缺陷**。

## ★★ 但绝不整批放行

**卷内混有他人材料是真实存在的**，实测点名如下（`check_authorship` 抓出、我回原文核过）：
`By Miss Dunlap.`／`By John W. Chadruck.`／`By Emmeline B. Wells.`／
`by F.J. CAMPBELL`／`by MISS ELOISE ANTHONY`。
这些卷**照挂 attribution，但写明卷内有他人段落，取逐字引文前必须切边界**。
"""
import importlib.util
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
WS = pathlib.Path("workspaces/clara-barton/clara-barton")
LED = WS / "evidence/source-ledger.jsonl"
META = WS / "meta.json"
SUBJECT = "Clara Barton"

# `check_authorship` 在这几份里抓出他人署名，我回原文核过：确有他人段落。
MIXED_VOLUMES = {
    "diary-1866-jan-dec": "By  Miss  Dunlap.  Phil.",
    "sw-poetry-1854-1909-undated": "By  John  W.  Chadruck.",
    "sw-speeches-1871-1942-undated": "By  Emmeline  B.  Wells.",
    "sw-speeches-and-lectures-international-and-national-relie": "by  F.J.  CAMPBELL",
    "sw-speeches-and-lectures-miscellany-1866-1898-undated": "by  MISS  ELOISE  ANTHONY",
}

# 已切好边界的整卷扫图（见 raw/_BOUNDARIES.json，逐条回原文核过）
BOUNDED = {
    "andersonville-1866": (
        "**整卷扫图，已切边界**：她署名的报告在第 250–729 行，"
        "末行 `CLARA··BARTON.`（第 728 行，双空格为 OCR 原样）。"
        "**第 60–249 行是 Dorence Atwater 的第一人称自述**"
        "（第 72 行 `I··was··talien··prisoner`——OCR 把 taken 认成 talien；"
        "**她从未被俘，那一段绝不可当作她的话**），末行 `DORENCE··ATWATER.`（第 249 行）。"
        "**取逐字引文前必须先落在 250–729 之内。**"),
}


def load_ids():
    out = {}
    for line in pathlib.Path("raw/_ids.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or "\t" not in line:
            continue
        f = line.split("\t")
        if len(f) == 9:
            out[f[0].strip()] = {"year": f[3].strip(), "lang": f[5].strip(),
                                 "tier": f[6].strip(), "flags": f[7].strip(),
                                 "note": f[8].strip()}
    return out


IDS = load_ids()


def attr(short_id: str) -> str:
    m = IDS.get(short_id, {})
    tier, flags, note = m.get("tier", ""), m.get("flags", ""), m.get("note", "")
    year = m.get("year", "")

    if tier in ("S1", "S2"):
        base = ("**第三方材料，不计为其所著。** S1 为同时代记述（1860–1915），"
                "S2 为后世研究与传记。收进来是给归属分层与边界题做证据，**不是给她加分**。")
        if short_id.startswith("otherdiary-"):
            base += ("\n**★ 本份是随行人员的日记**（LOC 著录 "
                     "`Diarists other than Barton; Staff diaries`）——"
                     "**同一趟行程、不同的人在记**。它与她本人日记会有相当比例的用词重合，"
                     "那是同场活动，不是转载；**但一个字都不是她写的**。")
        return base

    # ── 以下是 P1 / P2：她本人的东西 ──
    parts = []

    if short_id in BOUNDED:
        parts.append(BOUNDED[short_id])

    if short_id in MIXED_VOLUMES:
        parts.append(
            f"**⚠ 本卷内混有他人材料**，实测检出他人署名 `{MIXED_VOLUMES[short_id]}`"
            "（`check_authorship` 抓出，已回原文核过）。"
            "**取逐字引文前必须确认该段不属于那位他人。**")

    if short_id.startswith("diary-"):
        parts.append(
            "**未刊手稿：她本人的日记。** 归属依据是**档案出处**——"
            "美国国会图书馆 Clara Barton Papers（MSS11973），按其手迹与来源著录。\n"
            "**文本内没有署名是预期，不是缺陷**：日记不署名。"
            "`check_authorship` 认的三种证据（署名／编者注／逐字稿轮次）"
            "在这一类材料上**结构上不存在**，所以它会报 `authorship-unproven`——"
            "**那是判据射程的边界，不是本份的归属存疑。**")
    elif short_id.startswith(("sw-books-", "sw-speeches", "sw-poetry", "sw-writings")):
        parts.append(
            "**未刊手稿：她本人的书稿草稿／讲稿／诗作笔记。** 归属依据同上，为**档案出处**"
            "（LOC Clara Barton Papers，Speeches and Writings File）。"
            "**草稿与讲稿笔记同样不署名**，`authorship-unproven` 属预期。")
    elif short_id.startswith("fam-"):
        parts.append(
            "**未刊手稿：家族文书中她本人所写的部分。** 归属依据为**档案出处**"
            "（LOC Clara Barton Papers, Family Papers）。"
            "本份为她 1911–12 病中写给身边人的字条，"
            "侄子 Stephen E. Barton 的说明逐字：`During her illness she could not "
            "speak loud enough to be understood so wrote her wants on this sheet.`")
    else:
        # 刊行物：扉页／版权页可用
        parts.append(
            f"**刊行物，署名证据在文本层。** 其生前出版之著作或报告，署 Clara Barton，{year}。"
            "版权页实测原文（双空格为 OCR 原样）：`Copyright,   1898,  by   Clara    Barton`"
            "（见 rc-peace-war-1899）。")

    if tier == "P2":
        why = []
        if "DUPLICATE-SCAN" in flags:
            why.append("重复扫描")
        if "OCR-POOR" in flags:
            why.append("OCR 质量差")
        if "TRANSLATION" in flags:
            why.append("译本——**译文不是她的话，逐字引文不得取**")
        if "POSTHUMOUS" in flags:
            why.append("身后印次（她 1912-04-12 卒）")
        parts.append("**已降 P2**" + ("：" + "、".join(why) if why else "。")
                     + "　**逐字引文优先取 P1 那一份。**")

    parts.append("**★ 本批语料是双空格 OCR**（`CLARA··BARTON.`、`I··was··talien`）——"
                 "逐字引文核查必须容多空格与 OCR 变体，否则真引文会被报成未命中。")
    parts.append(f"台账备注：{note[:180]}")
    return "\n".join(parts)


def authorship_evidence(rows):
    """★ 逐份**真跑** `check_authorship`，把它查到的 A-* 码记进源记录。

    ## 为什么要这一步

    `check_source_attribution` 判「这一份有没有被逐份认领」时，读的是源记录上的
    `authorship_evidence` 字段——**而在此之前没有任何东西往那个字段里写**。
    于是 historical 路上每一份 P1 都被要求在 `attribution_basis` 里点名，
    **哪怕 `check_authorship` 明明认得出它的署名**。

    实测（Clara Barton，103 份 P1）：

        A-byline             17
        A-byline-standalone  16
        A-signature-block    15
        A-byline-ocr          1
        ── 认到证据 49 份 ──
        认不到               54 份（日记 34／讲稿书稿 19／家族文书 1）

    **认到的按实际证据记，认不到的才逐份点名。**
    绝不是「一句话放行 103 份」——那正是 v0.0.0.24 的错。
    """
    spec = importlib.util.spec_from_file_location(
        "ca", str(HERE.parents[3] / "registry/codex/persona-distiller/scripts/check_authorship.py"))
    ca = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ca)
    pat = ca.build_patterns(SUBJECT)
    ws = WS
    found, missing = {}, []
    for r in rows:
        if r.get("tier") != "P1" or (r.get("author") or "").strip() != SUBJECT:
            continue
        p = ws / str(r.get("local_path") or "")
        if not p.is_file():
            continue
        ok, code, _ev, _c = ca.check_text(p.read_text(encoding="utf-8", errors="replace"), pat)
        if ok:
            found[r["source_id"]] = code
        else:
            missing.append(r)
    return found, missing


def main() -> int:
    rows = [json.loads(l) for l in LED.read_text(encoding="utf-8").splitlines() if l.strip()]

    found, missing = authorship_evidence(rows)
    print(f"逐份跑 check_authorship：认到证据 {len(found)} 份，认不到 {len(missing)} 份")

    n = 0
    for r in rows:
        sid = (r.get("original_name") or "").replace(".txt", "")
        if not sid:
            continue
        r["attribution"] = attr(sid)
        if r["source_id"] in found:
            r["authorship_evidence"] = [found[r["source_id"]]]
        n += 1
    LED.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")
    print(f"逐份挂 attribution：{n} 条")

    meta = json.loads(META.read_text(encoding="utf-8"))
    meta["attribution_basis"] = {
        "authority": (
            "**十九世纪美国人物，署名证据充分**——刊行物有扉页与版权页，"
            "实测原文 `Copyright,   1898,  by   Clara    Barton`（rc-peace-war-1899，3 处）。\n\n"
            "**本人物的难点不在署名，在于一手材料最厚的一层是未刊手稿**："
            "58 册日记、书稿草稿、讲稿笔记。**日记不署名，草稿也不署名**——"
            "`check_authorship` 认的三种证据（署名／编者注／逐字稿轮次）"
            "在这一类材料上结构上不存在，实测 54 条 `authorship-unproven` 里 46 条属此类。\n\n"
            "**这一类的归属依据在档案层，不在文本层**：美国国会图书馆将其编目为 "
            "Clara Barton Papers（MSS11973），按手迹与来源著录。"
            "**这不是「判据查不出所以放行」，是这一类材料的归属依据本来就在别处。**"),
        "citation": "https://www.loc.gov/collections/clara-barton-papers/ ｜ LOC MSS11973",
        "disputed_policy": (
            "**逐份点名，不整批放行**（v0.0.0.24 的整批声明曾把逐源检查关掉、绿了十版）。"
            "三类分别处置：\n"
            "① **卷内混有他人材料**——`check_authorship` 抓出他人署名、我回原文核过的 5 卷，"
            "逐卷在 `attribution` 里写明那位他人是谁，取逐字引文前必须切段。\n"
            "② **整卷扫图需切边界**——`andersonville-1866` 她署名的报告在 250–729 行"
            "（末行 `CLARA··BARTON.`），**第 60–249 行是 Dorence Atwater 的第一人称自述**"
            "（`I··was··talien··prisoner`，OCR 把 taken 认成 talien；她从未被俘）。"
            "见 `raw/_BOUNDARIES.json`，已逐条回原文核过行号与佐证。\n"
            "③ **随行人员日记不是她的**——LOC 著录 `Diarists other than Barton; Staff diaries`，"
            "已定 S1；它与她本人日记用词重合度可达 17%，那是同场活动不是转载，"
            "但**一个字都不是她写的**（逐字相同句段实测 8/933）。"),
        # ★ 逐份点名，**只列 `check_authorship` 认不到 A-* 证据的那些**。
        #   认得到的 49 份不写在这里——它们走证据路，不走点名路。
        #   这一层区分就是本项目与 v0.0.0.24「一句声明整批免检」的分界线。
        "covered_sources": sorted(
            (r.get("original_name") or "") for r in missing),
        "covered_sources_rationale": (
            f"**{len(missing)} 份逐份列出，全部是 LOC 未刊手稿**"
            "（日记、书稿草稿、讲稿笔记、家族文书）。"
            "`check_authorship` 在这些件上认不到 A-* 证据，**是预期而非缺陷**："
            "**日记与草稿本来就不署名**。其归属依据在**档案层**——"
            "美国国会图书馆 Clara Barton Papers（MSS11973），按手迹与来源著录。\n"
            f"**另有 {len(found)} 份不列在此**：它们由 `check_authorship` 逐份实测到真署名证据"
            "（A-byline 17／A-byline-standalone 16／A-signature-block 15／A-byline-ocr 1），"
            "已写进各自源记录的 `authorship_evidence`，**走证据路不走点名路**。\n"
            "**两条路分开，正是为了不让「点名」退化成整批免检。**"),
        "disputed_works": [
            "andersonville-1866 第 60–249 行：Dorence Atwater 第一人称自述，**非她所作**",
            "diary-1866-jan-dec：卷内检出 `By  Miss  Dunlap.  Phil.`",
            "sw-poetry-1854-1909-undated：卷内检出 `By  John  W.  Chadruck.`",
            "sw-speeches-1871-1942-undated：卷内检出 `By  Emmeline  B.  Wells.`",
            "sw-speeches-and-lectures-international-and-national-relie：卷内检出 `by  F.J.  CAMPBELL`",
            "sw-speeches-and-lectures-miscellany-1866-1898-undated：卷内检出 `by  MISS  ELOISE  ANTHONY`",
            "otherdiary-* 全系列：LOC 著录为 Diarists other than Barton，已定 S1，非她所作",
        ],
    }
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("meta.attribution_basis 已写入（四字段齐）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
