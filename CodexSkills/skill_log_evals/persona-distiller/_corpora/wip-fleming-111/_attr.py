#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#111 Fleming：attribution_basis + 逐份挂 attribution。

**逐份点名，不用整批声明**（v0.0.0.24 那条整批声明曾把逐源检查整个关掉，绿了十版）。

写进去的每一条都回语料核过；核不到的一律不写。
"""
import json
import pathlib
import re

WS = pathlib.Path("workspaces/alexander-fleming/alexander-fleming")
LED = WS / "evidence/source-ledger.jsonl"
rows = [json.loads(l) for l in LED.read_text(encoding="utf-8").splitlines() if l.strip()]

IDS = {}
for line in pathlib.Path("raw/_ids.txt").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.startswith("#"):
        f = line.split("\t")
        if len(f) >= 9:
            IDS[f[0].strip()] = {"year": f[3].strip(), "edition": f[4].strip(),
                                 "tier": f[6].strip(), "flags": f[7].strip(),
                                 "note": f[8].strip()}


def attr(name: str) -> str:
    n = name.replace(".txt", "")
    m = IDS.get(n, {})
    fl, yr, note = m.get("flags", ""), m.get("year", ""), m.get("note", "")

    if n.startswith("s1-") or n.startswith("s2-"):
        return ("第三方材料，**不计为其所著**。S1 为同时代记述（含牛津一侧的一手论文与"
                "诺奖官方记录），S2 为后世研究。**牛津那一侧收进来不是给他加分，"
                "是给归属分层做证据。**")

    base = ""
    if "PAGE-SPILL" in fl:
        base = ("**⚠ 本份是整版扫图转文，正文里混着邻栏的内容。**"
                "PMC 把旧 BMJ／PRSM／Proc R Soc 按整页提供，"
                "**从本份取逐字引文前，必须先确认那一段落在哪一栏**"
                "——否则会把别人的文字挂到他名下。\n")

    if "-CO" in n or "CO-AUTHORED" in fl:
        return (base + f"**合著，{yr or '年份见扉页'}。** "
                "**合著不等于不是他写的，但「哪一部分是他的」要单独确认**——"
                "本流水线在 Osler #110 上因为漏了这一层被两席各扣一次。\n"
                f"台账备注：{note[:150]}")

    if "POSTHUMOUS" in fl:
        return (base + f"**身后印次／身后版（{yr}）**，已降 P2。他 1955-03-11 卒。"
                "**逐字引文不得取。**")

    if "HANDWRITING-OCR-UNUSABLE" in fl:
        return (base + "**手稿，只有影像**，OCR 出来读不出字。"
                "留在库里作旁证与来源证据，**已降 P2，逐字引文不得取**。")

    return (base + f"其生前发表之论文、演讲或著作，署 Alexander Fleming，"
            f"{yr or '年份见扉页'}。\n"
            "**同名排除四类**（详见 `raw/_EXCLUDED.txt`）：\n"
            "　· **Alexander Fleming（1824–1875）**，苏格兰医师、materia medica 教授——"
            "archive.org 把其 1845 年《An inquiry into the physiological and medicinal "
            "properties of the Aconitum Napellus》著录在 `Fleming, Alexander, 1824-1875` 名下，"
            "**那本书比本人出生早 36 年**；\n"
            "　· **John Ambrose Fleming（1849–1945）**，电子管发明人——"
            "其 1904 年那篇与 1922 年溶菌酶两篇**在同一个 Royal Society 合集里**；\n"
            "　· **A. Grant Fleming**（蒙特利尔公共卫生）、**Robert Alexander Fleming**"
            "（爱丁堡，另有其本人讣告）等——裸检索 `Fleming A` 时前者排第一；\n"
            "　· 判据：**作者字段／生卒年／题材**三条同时看，任何一条对不上即排除。")


n = 0
out = []
for r in rows:
    if r.get("tier") in ("P1", "P2") and not r.get("attribution"):
        r["attribution"] = attr(r.get("original_name") or pathlib.Path(r["local_path"]).name)
        n += 1
    out.append(r)
LED.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in out) + "\n",
               encoding="utf-8")

prim = [r for r in out if r.get("tier") in ("P1", "P2")]
covered = [{"source_id": r["source_id"],
            "original_name": r.get("original_name") or pathlib.Path(r["local_path"]).name,
            "locator": (r.get("locator") or "")[:200]} for r in prim]

m = json.loads((WS / "meta.json").read_text(encoding="utf-8"))
m["attribution_basis"] = {
 "authority": (
   "二十世纪人物，署名证据充分。**本人物的头号风险不是同名，"
   "是通俗叙事把一整支牛津团队从青霉素的故事里抹掉了。**\n\n"
   "① **1928 年那次观察与 1929 年那篇论文确实是他的。**\n"
   "　　`ON THE ANTIBACTERIAL ACTION OF CULTURES OF A PENICILLIUM, WITH SPECIAL "
   "REFERENCE TO THEIR USE IN THE ISOLATION OF B. INFLUENZÆ`，"
   "*British Journal of Experimental Pathology*，1929——**本工作区握有全文**。\n"
   "② **分离、纯化与临床验证不是他做的。** 1939–1945 由牛津的 Howard Florey、"
   "Ernst Chain、Norman Heatley 完成。**诺奖官方记录写着 `Prize share: 1/3`**"
   "（nobelprize.org 1945 年页面，本工作区有存档），三人各三分之一。\n"
   "　　本工作区**同时收了牛津一侧的一手材料**（Florey 的诺奖演说、1946 年 Yale 讲稿等，"
   "按 S1 收）——**它们不是给他加分的，是给归属分层做证据的。**\n"
   "③ **两个方向都要设障**：既不许写成他一人发明了青霉素，"
   "也不许否认 1928 的观察与 1929 的论文确实是他的。\n"
   "④ **1922 年的溶菌酶完全是他的**，而通俗叙事几乎不提："
   "`On a Remarkable Bacteriolytic Element Found in Tissues and Secretions`，"
   "*Proc. Roy. Soc. B*，1922——本工作区握有全文，另有其 1932 年会长演说等四份。\n"
   "⑤ **他用英文写作，无译文层**——不存在「译者的字被当成本人原话」这一整类问题。"),
 "citation": ("Fleming, Alexander. “On the Antibacterial Action of Cultures of a "
   "Penicillium…”, *Brit. J. Exp. Path.*, 1929；同氏 “On a Remarkable Bacteriolytic "
   "Element Found in Tissues and Secretions”, *Proc. Roy. Soc. B*, 1922；"
   "并及其诺奖演说与历年学会演讲。归属分层另据 nobelprize.org 1945 年官方页面。"),
 "disputed_policy": (
   "**争议著作为空，但不是「没查过」。** 他身处二十世纪英语医学期刊的公开制度下，"
   "署名逐篇可查。**真正的风险是三层：**\n"
   "**一、荣誉归属**——通俗叙事把牛津团队抹掉。已按上文分层，两个方向都设障。\n"
   "**二、同名**——四类，逐条记在 `raw/_EXCLUDED.txt`。"
   "**最险的一条是 archive.org 把 1845 年那本 Aconitum Napellus 著录在 "
   "`Fleming, Alexander, 1824-1875` 名下——那本书比本人出生早 36 年。**"
   "另有 John Ambrose Fleming（1849–1945）的 1904 年论文**与 1922 年溶菌酶两篇同处一个 "
   "Royal Society 合集**；裸检索 `Fleming A` 时 A. Grant Fleming 排第一。\n"
   "**三、整版扫图串栏**——PMC 把旧刊按整页提供，"
   "**14 份带 `PAGE-SPILL` 标记的文件正文里混着邻栏内容**。"
   "从这些文件取逐字引文前必须先确认段落在哪一栏，"
   "**否则会把别人的文字挂到他名下**。"),
 "disputed_works": [],
 "exclusions": [
   {"what": "Alexander Fleming（1824–1875）苏格兰医师的著作",
    "why": "同名不同人；archive.org 将其 1845 年 Aconitum Napellus 一书著录在 "
           "`Fleming, Alexander, 1824-1875` 名下，**早于本人出生 36 年**"},
   {"what": "John Ambrose Fleming（1849–1945）的著作",
    "why": "名不同但检索 `Fleming` 必然捞到；其 1904 年论文与本人 1922 年溶菌酶两篇"
           "**同处一个 Royal Society 合集**"},
   {"what": "A. Grant Fleming、Robert Alexander Fleming 等其他同姓者",
    "why": "裸检索 `Fleming A` 时 A. Grant Fleming 排第一；后者另有其本人讣告"},
   {"what": "付费墙／验证门后的材料", "why": "**按政策未尝试绕过**，已逐条记入排除表"},
   {"what": "只有图像、无可用文本的件", "why": "OCR 读不出字，不留空文件"}],
 "counting_convention": (
   f"covered_sources 逐份点名全部 {len(prim)} 条一手源（P1 {sum(1 for r in prim if r['tier']=='P1')} "
   f"+ P2 {sum(1 for r in prim if r['tier']=='P2')}），不使用整批声明"
   "（v0.0.0.24 曾因整批声明导致逐源检查整个关闭，v0.0.0.34 已堵）。\n"
   "**注意**：`primary_ratio` = 45/69 = **0.6522**，deep 门 0.65，"
   "**余量只有 0.0022——一份错档就掉下去。**"),
 "covered_sources": covered,
}
(WS / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"attribution 逐条挂 {n} 条；covered_sources 点名 {len(covered)} 条")
