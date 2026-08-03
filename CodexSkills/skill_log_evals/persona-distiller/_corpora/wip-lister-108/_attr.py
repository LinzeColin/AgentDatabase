#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#108 Lister：attribution_basis + 44 条 P1 逐份挂 attribution。"""
import json, pathlib, re

WS = pathlib.Path("workspaces/joseph-lister")
LED = WS / "evidence/source-ledger.jsonl"
rows = [json.loads(l) for l in LED.read_text(encoding="utf-8").splitlines() if l.strip()]
p1 = [r for r in rows if r.get("tier") == "P1"]


def attr(name: str) -> str:
    n = name.lower()
    if "collectedpaperso" in n or "b31363088" in n:
        vol = "I" if ("01" in n or "0001" in n) else "II"
        return (f"《The Collected Papers of Joseph, Baron Lister》卷 {vol}"
                "（Oxford: Clarendon Press, 1909）。**出版于其生前**（他 1912 年卒），"
                "且序言逐字写明**选目权在他本人**：「the Committee ... has had the inestimable "
                "advantage of **his guidance and advice**. The two volumes contain all the papers "
                "and addresses which **he himself considers** to possess permanent interest and "
                "importance」。**这与身后编成的全集性质不同。**"
                "本工作区对该集握有两套独立扫本（archive.org 与 Wellcome），可逐页互核。"
                "**排除**：卷 I 的 PREFACE 与 Cameron 所撰 INTRODUCTION 是编者文字，不计为其本人之言。")
    if "sim_the-lancet" in n or "lancet" in n:
        return ("《The Lancet》相应期的**本人署名原刊**。1867 年那一系列"
                "《On a New Method of Treating Compound Fracture, Abscess, etc.》"
                "共五篇（Iss. 2272/2273/2274/2278/2291）均在库，可与全集卷内重排本互核。"
                "**同期他人文章不计为其所著。**")
    if "british-medical-journal" in n or "bmj" in n:
        return ("《British Medical Journal》1867 年半年合订卷，含其"
                "《On the Antiseptic Principle in the Practice of Surgery》原刊；"
                "同篇另有 Lancet 版可互核。**同卷他人文章不计为其所著。**")
    if "philtrans" in n or "inflammation" in n:
        return ("《Philosophical Transactions》原刊，扉页署 "
                "「Joseph Lister, Esq., F.R.C.S., **Assistant Surgeon to the Royal Infirmary, "
                "Edinburgh**, communicated by Dr. Sharpey」——**身份、职务、年份三重锁定为本人**，"
                "而非其父 Joseph Jackson Lister（1786–1869，光学）。")
    return ("其生前发表之论文、演讲或抽印本，署 Joseph Lister，发表年在 1853–1912 之间。"
            "**同名排除三条**：archive.org creator 字段对父作 `Lister, Joseph Jackson`、"
            "对子作 `Lister, Joseph`；**1850 年前之作必非子**（子 1827 年生、1853 年首发）；"
            "显微镜光学与水螅／海鞘解剖属父，子无此类著作。")


n = 0
out = []
for r in rows:
    if r.get("tier") == "P1" and not r.get("attribution"):
        r["attribution"] = attr(r.get("original_name") or pathlib.Path(r["local_path"]).name)
        n += 1
    out.append(r)
LED.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in out) + "\n",
               encoding="utf-8")

covered = [{"source_id": r["source_id"],
            "original_name": r.get("original_name") or pathlib.Path(r["local_path"]).name,
            "locator": r.get("locator", "")} for r in p1]
m = json.loads((WS / "meta.json").read_text(encoding="utf-8"))
m["attribution_basis"] = {
 "authority": (
   "印刷时代人物，署名证据充分。有两处须写明，且两处都与前几位人物相反——**是优势不是风险**。\n"
   "① **《Collected Papers》(Oxford, 1909, 2 卷) 出版于其生前**（他 1912-02-10 卒），"
   "且序言逐字写明选目权在他本人：「the Committee which has prepared these volumes for the press "
   "has had the inestimable advantage of **his guidance and advice**. The two volumes contain all "
   "the papers and addresses which **he himself considers** to possess permanent interest and "
   "importance」。**与 Koch 那种身后编成、编者文字混入的全集性质不同。**\n"
   "② **他用英文写作，无译文层**——不存在「译者的字被当成本人原话」这一整类问题。\n"
   "核心篇目均有原刊与全集双份可互核：1867 Lancet 五篇（Iss. 2272/2273/2274/2278/2291）、"
   "1867 BMJ《On the Antiseptic Principle in the Practice of Surgery》、"
   "1858《On the Early Stages of Inflammation》(Phil. Trans.)。"),
 "citation": ("Lister, Joseph. *The Collected Papers of Joseph, Baron Lister*. "
   "2 vols. Oxford: Clarendon Press, 1909。并对照原刊："
   "*The Lancet* 1867 年各期、*British Medical Journal* 1867、"
   "*Philosophical Transactions of the Royal Society* 1858 等。"),
 "disputed_policy": (
   "**争议著作为空，但不是「没查过」。** 他身处英国医学期刊的公开发表制度下，"
   "论文有期号与日期可查，不存在伪托问题。\n"
   "**本人物真正的归属风险是血亲同名，而且危险的那个是他父亲：**\n"
   "**Joseph Jackson Lister（1786–1869）**，业余光学家、消色差显微镜物镜的关键改进者，"
   "署名常作 **J. J. Lister**，与子的 **J. Lister** 只差一个字母；"
   "**领域紧邻**——子能看见微生物，靠的正是父改良的镜子。"
   "**十九世纪显微镜光学文献里的「Lister」默认是父，不是他。**\n"
   "另有 **Joseph Jackson Lister（1857–1927）博物学家**，与父完全同名——三人共用两个名字。\n"
   "抓源阶段已据三条机器可复核的判法排除父的 4 条（含 1830 年那篇消色差物镜）"
   "与博物学家的 6 条。\n"
   "**★ 一处必须写明的例外**：全集卷 II 里有 16 处 "
   "「Joseph Jackson Lister」，查下来是**他本人写的悼父文**"
   "《Obituary Notice of the late Joseph Jackson Lister, F.R.S.》及其引用父亲 1830 年那篇。"
   "**那是子写父，不是父的作品**，记 writings。\n"
   "另有 **Listerine**（1879 年以他命名的商品，**不是他做的、也未经他同意**）与 "
   "**Lister Institute**（1891 起）造成的机构与商品名淹没——全文搜 \"Lister\" 不可用。"),
 "disputed_works": [],
 "exclusions": [
   {"what": "《Collected Papers》卷 I 的 PREFACE 与 Cameron 所撰 INTRODUCTION",
    "why": "编者文字，非其本人之言；位置已定，其余卷内正文为其自选篇目"},
   {"what": "其父 Joseph Jackson Lister（1786–1869）的著作",
    "why": "同姓且领域紧邻；判法：creator 字段 / 1850 年前必非子 / 显微镜光学与水螅海鞘解剖属父",
    "excluded_ids": ["jstor-107900（1830 消色差物镜）", "jstor-110225", "jstor-110397", "jstor-108069"]},
   {"what": "博物学家 Joseph Jackson Lister（1857–1927）的著作",
    "why": "与父完全同名；已排除 6 条（Foraminifera 等）"},
   {"what": "各期刊卷中他人所撰文章", "why": "同卷不等于同一作者"}],
 "counting_convention": ("covered_sources 逐份点名全部 44 条 P1 源，不使用整批声明"
   "（v0.0.0.24 曾因整批声明导致逐源检查整个关闭，v0.0.0.34 已堵）。"
   "**注意**：44 份 writings 含同文异扫（全集 2 卷各 2 扫、炎症早期 3 扫等），"
   "**对应约 26 种独立著作**——算独立著作数时不得重复计。"),
 "covered_sources": covered,
}
(WS / "meta.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"attribution 逐条挂 {n} 条；covered_sources 点名 {len(covered)} 条")
