#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#110 Osler：attribution_basis + 逐份挂 attribution。

**逐份点名，不用整批声明**（v0.0.0.24 那条整批声明曾把逐源检查整个关掉，绿了十版）。
"""
import json
import pathlib
import re

WS = pathlib.Path("workspaces/william-osler/william-osler")
LED = WS / "evidence/source-ledger.jsonl"
rows = [json.loads(l) for l in LED.read_text(encoding="utf-8").splitlines() if l.strip()]

IDS = {}
for line in pathlib.Path("raw/_ids.txt").read_text(encoding="utf-8").splitlines():
    if line.strip() and not line.startswith("#"):
        f = line.split("\t")
        if len(f) >= 9:
            IDS[f[0].strip()] = {"year": f[3].strip(), "edition": f[4].strip(),
                                 "flags": f[7].strip(), "note": f[8].strip()}


def attr(name: str) -> str:
    n = name.replace(".txt", "")
    meta = IDS.get(n, {})
    ed, yr, fl = meta.get("edition", ""), meta.get("year", ""), meta.get("flags", "")

    if n.startswith("ppm-"):
        base = ("《The Principles and Practice of Medicine》**逐版次认定**——"
                "本人物的头号归属风险就在这套书上。\n")
        if "POSTHUMOUS" in fl:
            return (base + f"**本份是身后版（{yr}）**，扉页作「BY **THE LATE** SIR WILLIAM "
                    "OSLER … **AND** THOMAS McCRAE / NINTH THOROUGHLY REVISED EDITION」"
                    "——**不是他写的，已降 P2，逐字引文不得取。**")
        if "ASSISTED-BY-McCRAE" in fl:
            return (base + f"**本份是第 8 版（{yr}）**，扉页作「…EIGHTH EDITION — "
                    "**WITH THE ASSISTANCE OF THOMAS McCRAE**」——"
                    "**署名仍是他，McCrae 是助手**；引用时须写明是第 8 版。")
        return (base + f"**本份扉页署 `BY WILLIAM OSLER, M.D.`，{ed or '版次见扉页'}，"
                f"{yr or '扉页年份不清（已在账本标明）'}**。"
                "第 1–7 版（1892–1909）皆为其独著。")

    if n.startswith("aequanimitas"):
        if "POSTHUMOUS" in fl:
            return ("《Aequanimitas》**身后印次**，已降 P2。")
        return (f"《Aequanimitas, with Other Addresses》，署 William Osler，{yr}。"
                "**含 1889 年那篇告别演说**，其生前结集。")

    if n.startswith("collected-reprints"):
        return ("《Collected Reprints》——**他本人辑印的抽印本合订**，"
                "卷内为其署名论文；**同卷若混入他人文章，不计为其所著**。")

    if n.startswith("s1-") or n.startswith("s2-"):
        return ("第三方材料，**不计为其所著**。S1 为同时代记述（如 1919 年祝寿文集、"
                "1920 年悼念文字），S2 为后世研究（如 Cushing 传记）。")

    if "-CO" in n or "CO-AUTHORED" in fl:
        return (f"**合著，{yr}**。扉页与正文署名显示不止他一人——"
                "**合著不等于不是他写的，但「哪一部分是他的」要单独确认**。"
                f"账本备注：{meta.get('note','')[:110]}")

    if "HANDWRITING-OCR-UNUSABLE" in fl:
        return ("**手稿，只有影像**，OCR 出来读不出字。"
                "留在库里作旁证与来源证据，**已降 P2，逐字引文不得取**。")

    return (f"其生前发表之著作、演讲或论文，署 William Osler，{yr or '年份见扉页'}。\n"
            "**同姓排除三条**：archive.org creator 字段作 `Osler, William, Sir, 1849-1919`；"
            "其兄 **Sir Edmund Boyd Osler（1845–1924）** 题材为金融／铁路／议会，非医学；"
            "**另有 William Roscoe Osler**（《Tintoretto》1879 作者）——"
            "**任何 `william AND osler` 的检索都会把他捞进来**，抓源阶段已排除 6 条。")


n = 0
out = []
for r in rows:
    if r.get("tier") == "P1" and not r.get("attribution"):
        r["attribution"] = attr(r.get("original_name") or pathlib.Path(r["local_path"]).name)
        n += 1
    out.append(r)
LED.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in out) + "\n",
               encoding="utf-8")

p1 = [r for r in out if r.get("tier") == "P1"]
covered = [{"source_id": r["source_id"],
            "original_name": r.get("original_name") or pathlib.Path(r["local_path"]).name,
            "locator": (r.get("locator") or "")[:200]} for r in p1]

m = json.loads((WS / "meta.json").read_text(encoding="utf-8"))
m["attribution_basis"] = {
 "authority": (
   "印刷时代人物，署名证据充分。**本人物的头号风险不是同名，是同一本书的后期版次不是他写的。**\n\n"
   "① **《The Principles and Practice of Medicine》跨越他的生死。** "
   "初版 1892，他 1919-12-29 卒，而该书继续出到 1940 年代。逐版次翻扉页确认：\n"
   "　　**第 1–7 版（1892–1909）**：「BY WILLIAM OSLER, M.D.」——**他独著**；\n"
   "　　**第 8 版（1912–1919）**：「…EIGHTH EDITION — WITH THE ASSISTANCE OF THOMAS "
   "McCRAE」——**署名仍是他**，McCrae 为助手；\n"
   "　　**第 9 版（1920/1921）**：「BY **THE LATE** SIR WILLIAM OSLER … **AND** THOMAS "
   "McCRAE / NINTH THOROUGHLY REVISED EDITION」——**身后续修，不计 P1**；\n"
   "　　第 9 版之后（Christian 续修）**一份未取**。\n"
   "本工作区握有**八个生前版次**（第 1–8 版）与 1919 年最后一次生前印次，可逐版互核。\n\n"
   "② **三处著录与扉页不符，一律以扉页为准**（v0.0.0.43 就是为这一类落的判据）：\n"
   "　　`principlesandpr00mccrgoog` 著录 1920、**扉页 1921**；\n"
   "　　`in.ernet.dli.2015.149801` 著录 1906，**扉页无年、署「Late Regius Professor」、"
   "印次表到 1930**——他死后十年；\n"
   "　　`principlesandpr09oslegoog` 著录 1892 而扉页作「SIXTH EDITION」，**不可能**，"
   "年份判为不可辨并如实记录。\n\n"
   "③ **他用英文写作，无译文层**——与 Lister #108 同，"
   "**不存在「译者的字被当成本人原话」这一整类问题**。抓到的两份译本已降 P2。\n\n"
   "④ **有七份合著**，其中两份的第一作者不是他：1886 年胃萎缩那篇 "
   "**Frederick P. Henry 为第一作者**；1877 年恶性贫血那篇**只有病理报告是他的，"
   "临床报告是 John Bell 的**。**合著不等于不是他写的，但哪一部分是他的要单独说。**"),
 "citation": ("Osler, William. *The Principles and Practice of Medicine*. "
   "New York: D. Appleton / Edinburgh: Young J. Pentland, 1892（初版）"
   "——并对照其第 2–8 版逐版扉页。"
   "并及：*Aequanimitas, with Other Addresses*（1904）；"
   "*An Alabama Student and Other Biographical Essays*（1908）；"
   "*Science and Immortality*（1904）；*Collected Reprints* Series 2–6（1882–1920）。"),
 "disputed_policy": (
   "**争议著作为空，但不是「没查过」。** 他身处英语医学期刊与教科书出版的公开制度下，"
   "版次、印次与扉页署名逐一可查。\n\n"
   "**真正的风险是三层，都不是「有人冒他的名」：**\n"
   "**一、身后续修**——《Principles and Practice》第 9 版起由 McCrae、后由 Christian 续修。"
   "**扉页写着「THE LATE」，但文件名与馆藏著录不写。**\n"
   "**二、他任编者而非作者的书**——*Typhoid Fever and Typhus Fever* 实为 **Curschmann** 的正文、"
   "他只任编者；*Modern Medicine* 与 *A System of Medicine* 同理。"
   "**这三部若按 creator 字段收，会变成假的 P1**，抓源阶段已按归属排除。\n"
   "**三、同姓**——其兄 **Sir Edmund Boyd Osler（1845–1924）**（金融／议会，已排除 4 条）；"
   "其子 **Edward Revere Osler（1895–1917）**（在 creator 字段里一次都没出现，"
   "只作两本书的旧藏批注，**已记录以使这次检查可见**）；"
   "**以及 William Roscoe Osler**——《Tintoretto》(1879) 的作者，"
   "**archive.org 的 creator 字段就写着这个名字，任何 `william AND osler` 的检索都会把他捞进来**，"
   "已排除 6 条。另有 Edward Osler（1798–1863）12 条、其父 Featherstone Lake Osler 1 条等。"),
 "disputed_works": [],
 "exclusions": [
   {"what": "《Principles and Practice》第 9 版及其后（1920 起）",
    "why": "他 1919-12-29 卒；扉页作「BY THE LATE SIR WILLIAM OSLER … AND THOMAS McCRAE」——身后续修",
    "excluded_ids": ["ppm-ed9-1920-POSTHUMOUS", "ppm-ed9-1921-POSTHUMOUS"]},
   {"what": "他任编者而非作者的书",
    "why": "*Typhoid Fever and Typhus Fever* 实为 Curschmann 正文；*Modern Medicine*、"
           "*A System of Medicine* 同理。**按 creator 字段收会变成假的 P1。**"},
   {"what": "William Roscoe Osler（《Tintoretto》1879 作者）的著作",
    "why": "**creator 字段就写着 `William Roscoe Osler`**，任何 william AND osler 检索都会捞到；已排除 6 条"},
   {"what": "其兄 Sir Edmund Boyd Osler（1845–1924）的材料",
    "why": "同姓同代；题材为金融／铁路／议会，非医学；已排除 4 条"},
   {"what": "Edward Osler（1798–1863）等其他同姓者", "why": "同姓不同人；已排除 12 条"},
   {"what": "两份译本", "why": "译者的字，不是他的字；已降 P2"},
   {"what": "手稿（只有影像、OCR 读不出字）",
    "why": "留作来源旁证，**已降 P2，逐字引文不得取**"}],
 "counting_convention": (
   f"covered_sources 逐份点名全部 {len(p1)} 条 P1 源，不使用整批声明"
   "（v0.0.0.24 曾因整批声明导致逐源检查整个关闭，v0.0.0.34 已堵）。\n"
   "**注意**：76 条 P1 含《Principles and Practice》的**八个版次**与若干同版异印，"
   "**算独立著作数时不得重复计**。"),
 "covered_sources": covered,
}
(WS / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"attribution 逐条挂 {n} 条；covered_sources 点名 {len(covered)} 条")
