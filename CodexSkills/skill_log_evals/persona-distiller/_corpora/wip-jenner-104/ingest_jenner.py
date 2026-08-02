#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 47 份实取语料入库。tier 判据写在这里，不写在别处。

P1 = Jenner 本人所著／本人书信；
P2 = 同时代他人的一手文献（反对者小册子、机构报告、同时代复现报告）——**不是 Jenner 写的，但是当时的原始记录**；
S1 = 后世研究（Crookshank 1889、Drewitt 1933）。
"""
import subprocess, sys, pathlib

WS = "ws-jenner/ws-jenner"
PD = "../../../../registry/codex/persona-distiller/scripts/ingest.py"
J  = "Edward Jenner"

# id, tier, lane, author, year, abstract
ROWS = [
 ("b24759247","P1","writings",J,"1798","An Inquiry into the Causes and Effects of the Variolae Vaccinae 初版。**本工作区基底文本**"),
 ("inquiryintocause00jenn","P1","writings",J,"1800","An Inquiry ... 第三版"),
 ("b33519420_0002","P1","writings",J,"1800","An Inquiry ... 另一版次"),
 ("b33519420_0003","P1","writings",J,"1800","An Inquiry ... 另一版次"),
 ("b24927764","P1","writings",J,"1801","An Enquiry into the Causes and Effects of the Variolae Vaccinae"),
 ("b28748657","P1","writings",J,"1799","Disquisitio de Caussis et Effectibus Variolarum Vaccinarum（**拉丁译本，字句非本人**）"),
 ("b21354273","P1","writings",J,"1799","Further Observations on the Variolae Vaccinae, or Cow Pox"),
 ("b22006345","P1","writings",J,"1800","A Comparative Statement of Facts and Observations"),
 ("b22010440","P1","writings",J,"1801","Instructions for Vaccine Inoculation"),
 ("b22010440_0002","P1","writings",J,"1801","Instructions for Vaccine Inoculation 另一版次"),
 ("39002011212074.med.yale.edu","P1","writings",J,"1807","Instructions for Vaccine Inoculation, Commonly Called Vaccination"),
 ("b22010452_0001","P1","writings",J,"1801","The Origin of the Vaccine Inoculation"),
 ("b22010452_0002","P1","writings",J,"1801","The Origin of the Vaccine Inoculation 另一版次"),
 ("b2200953x","P1","writings",J,"1806","On the Varieties and Modifications of the Vaccine Pustule"),
 ("b22013490_0002","P1","writings",J,"1819","On the Varieties and Modifications of the Vaccine Pustule"),
 ("b22012916_0001","P1","writings",J,"1809","Facts, for the Most Part Unobserved, or Not Duly Noticed"),
 ("b22007179_0001","P1","writings",J,"1822","A Letter to Charles Henry Parry, M.D."),
 ("b22007179_0003","P1","writings",J,"1822","A Letter to Charles Henry Parry, M.D. 另一版次"),
 ("b22007179_0006","P1","writings",J,"1822","A Letter to Charles Henry Parry, M.D. 另一版次"),
 ("b30796581","P1","writings",J,"1824","A Letter to Dr. Waterhouse Respecting the Niceties of the Practice"),
 ("jstor-106657","P1","writings",J,"1788","Observations on the Natural History of the Cuckoo。**Phil. Trans. 78:219-237，形态是写给 John Hunter 的一封信**"),
 ("b2201231x_0002","P1","writings",J,"1824","Some Observations on the Migration of Birds"),
 ("b21439114","P1","writings",J,"1799","Contributions to Physical and Medical Knowledge"),
 ("b33519390_0001","P1","writings",J,"1799","Further Observations on the Variolae Vaccinae 另一版次"),
 ("b33519390_0002","P1","writings",J,"1799","Further Observations on the Variolae Vaccinae 另一版次"),
 ("disquisitiodecau00jenn","P1","writings",J,"1799","Disquisitio de Caussis et Effectibus Variolarum Vaccinarum（**拉丁译本，字句非本人**）"),
 ("b22010440_0004","P1","writings",J,"1801","Instructions for Vaccine Inoculation 另一版次"),
 ("b22010452_0004","P1","writings",J,"1801","The Origin of the Vaccine Inoculation 另一版次"),
 ("b22034985_0001","P1","writings",J,"1803","Indagacao sobre as Causas e Effeitos das Bexigas de Vacca（**葡萄牙译本，字句非本人**）"),
 ("b30380868","P2","external","Benjamin Moseley","1806","An Oliver for a Rowland 另一版次。**反对者**"),
 ("b21354571","P2","external","Benjamin Moseley","1807","An Oliver for a Rowland 另一版次。**反对者**"),
 ("mcgill-letters-1790","P1","conversations",J,"1790","A Report and Two Letters of Edward Jenner（McGill Osler 藏）。**本人书信；OCR 极差但是真件**"),
 # —— Baron 的传记：正文是他写的（P2），但**书中大量转录 Jenner 原始书信**
 ("lifeofedwardjenn01barouoft","P2","conversations","John Baron","1838","The Life of Edward Jenner vol.1。**Baron 是 Jenner 的友人兼医师；书中转录大量原始书信**"),
 ("lifeofedwardjenn02barouoft","P2","conversations","John Baron","1838","The Life of Edward Jenner vol.2，同上"),
 ("b33279986_0001","P2","conversations","John Baron","1838","The Life of Edward Jenner 另一套"),
 ("b33279974_0001","P2","timeline","John Baron","1827","The Life of Edward Jenner 1827 初版"),
 # —— 同时代反对者：**这一路是「他驳过谁、那人说过什么」的直接来源**
 ("b22041862","P2","external","Benjamin Moseley","1806","An Oliver for a Rowland; or, a Cow Pox Epistle。**反对者**"),
 ("b31910890","P2","external","Benjamin Moseley","1805","A Treatise on the Lues Bovilla, or Cow Pox。**反对者**"),
 ("b21364060","P2","external","Benjamin Moseley","1800","Medical Tracts。**反对者**"),
 ("b22037615_0002","P2","external","John Birch","1807","A Copy of the Answer to the Queries of the London...。**反对者**"),
 ("b22281770","P2","external","George Lipscomb","1805","Inoculation for the Small-pox Vindicated。**反对者**"),
 ("b22037913","P2","external","James Carrick Moore","1806","Remarks on Mr. Birch's 'Serious Reasons'。**驳反对者**"),
 ("b21510775","P2","external","William Woodville","1799","Reports on a Series of Inoculations for the Variolae Vaccinae。**天花医院污染争议的一手报告**"),
 ("39002011127140.med.yale.edu","P2","external","Charles R. Aikin","1801","A Concise View of All the Most Important Facts"),
 ("b31914226_0002","P2","external","Richard Dunning","1804","Minutes of Some Experiments"),
 ("b33284246","P2","external","Thomas Christie","1811","An Account of the Ravages Committed in Ceylon"),
 ("39002086340867.med.yale.edu","P2","external",None,"1800","Reflections on the Cow-pox（同时代评论）"),
 # —— 机构决策
 ("b21970518","P2","decisions","Royal College of Physicians","1804","Report of a Medical Committee on the Cases of Supposed Failure"),
 ("b22470979","P2","decisions","Royal College of Surgeons","1803","A Comparative View of the Natural Small-pox"),
 ("b21308603","P2","decisions",None,"1857","Papers Relating to the History and Practice of Vaccination"),
 # —— 表达形态
 ("b30378035","P2","expression",None,"1820","A Cottage Dialogue on Vaccination。**通俗传播形态**"),
 # —— 后世研究
 ("b21463475_0001","S1","external","Edgar M. Crookshank","1889","History and Pathology of Vaccination"),
 ("b3135502x","S1","timeline","F. Dawtrey Drewitt","1933","The Life of Edward Jenner: Naturalist"),
]
HOLDOUT = {"b22013490_0002"}   # 留作评测，构建期一律不读

ok = fail = 0
for ident, tier, lane, author, year, abstract in ROWS:
    p = pathlib.Path(f"raw/{ident}.txt")
    if not p.is_file():
        print(f"✗ 缺文件 {ident}"); fail += 1; continue
    cmd = [sys.executable, PD, WS, str(p), "--tier", tier, "--dimension", lane,
           "--language", {"b28748657":"la","disquisitiodecau00jenn":"la","b22034985_0001":"pt"}.get(ident,"en"),
           "--rights", "public-domain", "--abstract", abstract,
           "--locator", f"archive.org/{ident}", "--published-at", f"{year}-01-01"]
    if author: cmd += ["--author", author]
    if ident in HOLDOUT: cmd += ["--holdout"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0: ok += 1
    else:
        fail += 1
        print(f"✗ {ident}: {(r.stderr or r.stdout).strip().splitlines()[-1][:150]}")
print(f"\n入库 {ok} 成功 / {fail} 失败")
