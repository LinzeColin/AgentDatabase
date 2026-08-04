#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#118 Elizabeth Blackwell 抓源台账生成 —— 把探测取到的 98 份落进 `raw/`，写 9 列台账。

## 口径

- **格式照 `_corpora/_next/LEDGER_FORMAT.md`**：制表符、恰好 9 列，
  第 7 列分档不许空，第 8 列归属标记恰好一个，第 9 列以 `lane=` 开头。
- **分档就是分档，不为凑一手占比提档**。deep 只要 30 份一手，
  而干净的一手已有 78 份——**没有任何padding 的必要，也就不许 padding**。
- **重复扫描标 `P2` + `DUPLICATE-SCAN`**，并在第 9 列写明它是谁的重复。
  P2 计入 `primary`，所以**必须让人一眼看出去重后是多少**。
- **受污染的标 `U`，不是丢掉**。丢掉等于假装没抓过；标 U 则不计入 usable，
  而且下一个人能看见「这里有 147,419 字不能用，成因是什么」。

## ★★ 同名：四个人，不是两个

探测按 `creator:"Blackwell, Elizabeth"` 在 archive.org 命中 85 条，逐条过三问后排除：

| 排除对象 | 条数 |
|---|---|
| 植物图谱画家（1707–1758，*A Curious Herbal*） | 15 |
| **现代旅游作家（Frommer's Chicago，2003–2012）** | **17** |
| 现代小说家（*While Beauty Slept* 等，2007–2017） | 9 |
| 其他同名无关 | 1 |

**我原先只警告了植物画家，而旅游作家命中比她还多。** 三批合计 41 条，占总命中 48%。

一处必须记下的反例：日记里 4 次 `botanic` 命中，**查证全是 "Botanical Gardens"**
（她本人去逛植物园），不是植物图谱——**只看 grep 计数会把它误判成污染。**
"""
import hashlib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path("/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-"
                   "character-distillation-skill-reorganize-d57595/"
                   "c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/eb")
RAW = HERE / "raw"

LOC = "https://www.loc.gov/item/{}/"
IA = "https://archive.org/download/{0}/{0}_djvu.txt"

# ── A. 已出版著作 15 份（探测组 A）──────────────────────────────
# (短名, 源文件, URL, 篇名, 年, 定位, 档, 标记, 道, 依据)
PUBLISHED = [
 ("laws-of-life-1852", "t_61360800R.nlm.nih.gov.txt",
  "https://collections.nlm.nih.gov/ext/dw/61360800R/PDF/61360800R.pdf",
  "The Laws of Life, with Special Reference to the Physical Education of Girls",
  "1852", "NLM 数字馆藏全本", "P1", "HIS-OWN", "writings",
  "扉页署 `ELIZABETH BLACKWELL, M. D.`"),
 ("medicine-profession-women-1860", "t_MedicineAsAProfessionForWomen.txt",
  IA.format("MedicineAsAProfessionForWomen"),
  "Medicine as a Profession for Women", "1860", "全本", "P1", "CO-AUTHORED", "decisions",
  "★ **正文自陈是姐妹合备**：`lecture was prepared by Drs. Elizabeth and Emily Blackwell`"
  "——我第一版标 HIS-OWN，逐份核归属时才读到这句，**改 CO-AUTHORED**。"
  "另有 New York Infirmary 3 处、Nightingale 出现；这是她为女性从医立论的纲领性讲辞。"),
 ("medical-education-women-1864", "t_AddressOnTheMedicalEducationOfWomen.txt",
  IA.format("AddressOnTheMedicalEducationOfWomen"),
  "Address on the Medical Education of Women", "1864", "全本", "P1", "CO-AUTHORED", "decisions",
  "扉页 `DRS. E. AND E. BLACKWELL` 与 `READ AT THE NEW YORK INFIRMARY, DEC 1863`"
  "——**与妹妹 Emily 合署，故标 CO-AUTHORED 不标 HIS-OWN**"),
 ("counsel-to-parents-1878", "t_b22354347.txt",
  "https://wellcomecollection.org/works/b22354347",
  "Counsel to Parents on the Moral Education of their Children", "1878", "全本",
  "P1", "HIS-OWN", "writings",
  "扉页 `Dr. ELIZABETH BLACKWELL`；正文自述「二十八年前开始行医时…我写了女子体育讲义」"
  "（1878−28=1850，与 1849 年毕业吻合，回指 1852 年《Laws of Life》）"),
 ("religion-of-health-1878", "t_b21483012.txt",
  "https://wellcomecollection.org/works/b21483012",
  "The Religion of Health", "1878", "全本", "P1", "HIS-OWN", "writings",
  "扉页 `DR. ELIZABETH BLACKWELL`"),
 ("human-element-sex-1880", "t_b22279052.txt",
  "https://wellcomecollection.org/works/b22279052",
  "The Human Element in Sex（私印小册）", "1880", "全本", "P1", "HIS-OWN", "writings",
  "`By Dr. E. Blackwell`（OCR 作 `R BLACK WELL`，**未代改**）＋`ADDRESSED TO STUDENTS OF MEDICINE`"),
 ("human-element-sex-1894", "t_b29342557.txt",
  "https://wellcomecollection.org/works/b29342557",
  "The Human Element in Sex（新版）", "1894", "全本", "P1", "HIS-OWN", "writings",
  "扉页 `Dr ELIZABETH BLACKWELL`，J. & A. Churchill 出版"),
 ("wrong-right-methods-1883", "t_WrongAndRightMethodsOfDealingWithSocialEvilElizabethBlackwell.txt",
  IA.format("WrongAndRightMethodsOfDealingWithSocialEvilElizabethBlackwell"),
  "Wrong and Right Methods of Dealing with Social Evil", "1883", "全本",
  "P1", "HIS-OWN", "writings",
  "Schlesinger Library 藏书章；内文引《Counsel to Parents》书评"),
 ("decay-municipal-govt-1885", "t_ondecayofmunicip00blac.txt",
  IA.format("ondecayofmunicip00blac"),
  "On the Decay of Municipal Representative Government", "1885", "全本",
  "P1", "HIS-OWN", "writings",
  "`By Dr. ELIZABETH BLACKWELL`，Moral Reform Union 刊行"),
 ("benevolence-malthus-1888", "t_medicaladdresson00blac.txt",
  IA.format("medicaladdresson00blac"),
  "A Medical Address on the Benevolence of Malthus", "1888", "全本",
  "P1", "HIS-OWN", "writings", "`Dr. ELIZABETH BLACKWELL`"),
 ("influence-of-women-1890", "t_influenceofwomen00blac.txt",
  IA.format("influenceofwomen00blac"),
  "The Influence of Women in the Profession of Medicine", "1890", "全本",
  "P1", "HIS-OWN", "expression",
  "`DR. ELIZABETH BLACKWELL`；London School of Medicine for Women 开学致辞，**是讲出来的，故归 expression**"),
 ("pioneer-work-1895", "pg65496.txt",
  "https://www.gutenberg.org/ebooks/65496",
  "Pioneer Work in Opening the Medical Profession to Women", "1895",
  "Project Gutenberg 人工校对本（优于 OCR）", "P1", "HIS-OWN", "timeline",
  "Geneva 22 处、New York Infirmary 6 处、Emily 10 处、Nightingale 6 处；自传，编年主干"),
 ("scientific-method-biology-1898", "t_b28071803.txt",
  "https://wellcomecollection.org/works/b28071803",
  "Scientific Method in Biology", "1898", "全本", "P1", "HIS-OWN", "writings",
  "书前 `WORKS BY THE SAME AUTHOR` 列《Pioneer Work in Opening the Medical Profession to Women》"),
 ("essays-medical-sociology-v1-1902", "pg69939.txt",
  "https://www.gutenberg.org/ebooks/69939",
  "Essays in Medical Sociology, Vol. I", "1902", "Project Gutenberg 人工校对本",
  "P1", "HIS-OWN", "writings",
  "扉页 `ELIZABETH BLACKWELL, M.D.`；序言署 `HASTINGS, May 1902`"),
 ("essays-medical-sociology-v2-1902", "pg69998.txt",
  "https://www.gutenberg.org/ebooks/69998",
  "Essays in Medical Sociology, Vol. II", "1902", "Project Gutenberg 人工校对本",
  "P1", "HIS-OWN", "writings",
  "内文 `Woman's Medical College of the New York Infirmary`"),
]

# ── B. Middlebury / Abernethy 书信 3 份 ────────────────────────
LETTERS = [
 ("letter-parsons-1847-10-29", "t_aberms.blackwelle.1847.10.29.txt",
  "https://cdi.middlebury.edu/aberms/blackwelle.1847.10.29",
  "致 Anna Q. T. Parsons", "1847", "单封", "P1", "HIS-OWN", "conversations",
  "本人写「在争取向女性开放医业」「决心取得医学博士学位」「纽约州一所医学院学生一致邀请我入学」"
  "——即 Geneva Medical College 1847 年 10 月录取"),
 ("letter-parsons-1848-06-24", "t_aberms.blackwelle.1848.06.24.txt",
  "https://cdi.middlebury.edu/aberms/blackwelle.1848.06.24",
  "致 Anna Q. T. Parsons", "1848", "单封", "P1", "HIS-OWN", "conversations",
  "抬头 `Blockley June 24th 1848`（费城 Blockley 施医院，她 1848 年夏在此实习）"),
 ("letter-parsons-1851-12-07", "t_aberms.blackwelle.18xx.12.07.txt",
  "https://cdi.middlebury.edu/aberms/blackwelle.18xx.12.07",
  "致 Anna Q. T. Parsons", "推定 1851", "单封", "P1", "HIS-OWN", "conversations",
  "署 `44 University Place, New York`；★ **年份是内证推定，不是馆方给的**"
  "（馆方只写 `18--`）：文中「昨天见到我们的匈牙利英雄」指 Kossuth 1851 年 12 月访纽约"),
]

# ── C. LoC 日记 16 册 ──────────────────────────────────────────
DIARIES = [
 ("956", "1836", 3114), ("957", "1837-1839", 41572), ("958", "1869-1871", 17247),
 ("959", "1872-1874", 16713), ("960", "1875-1877", 30727), ("961", "1878-1880", 37345),
 ("962", "1881,1883", 26031), ("963", "1885-1887", 42441), ("964", "1888-1890", 33580),
 ("965", "1891-1893", 28404), ("966", "1894-1896", 24617), ("967", "1897-1899", 34197),
 ("968", "1900-1902", 31528), ("969", "1903-1905", 43428), ("970", "1906-1908", 25681),
 # ★ 971 单独处理，见 UNDATED_NOTE：**不是损毁，是旅费清单**
]
UNDATED = ("971", "未系年", 1200)
UNDATED_NOTE = (
 "★★ **降级为 U，但不是因为损毁。** `check_ocr_language_death` 报它虚词占比 0.092、"
 "判为「已毁的文件被记作 P1」——**那是该判据自己列明的假阳 ②（索引/表格天然没有虚词）**。"
 "人工看过：本件是**旅费清单**（`Paris — Hotel de Faueille - 6 Rue Castiglione - 10 frs par jour`、"
 "`Lucerne. Pension Luter 5.50.8`、`Milano. Hotel Grande Bretagne. 45 Via Torino ... 12 frs per day`），"
 "文本完好、确是她的手笔。"
 "**降级的真实理由是：1,031 词全是旅馆与价钱，对六条道没有任何实质贡献，不宜作一手源。**"
 "照判据给的第二条出路（「降级不作一手源」）处理，**不假称它损毁**。")

# ── D. LoC 讲稿/文章/书稿 33 份（干净者）──────────────────────
#   道按内容分：手稿散文归 writings；诗、故事翻译、少年习作、演讲笔记归 expression；
#   创院动议与致校友会抗议归 decisions；书目归 timeline。
SPEECH = [
 ("1235", "Address, 开办 Woman's Medical College", "1868", "decisions",
  "创院开学辞——**建制决策文本**"),
 ("1236", "Address on the Medical Education of Women", "1864", "decisions", "同名单行本的手稿"),
 ("1237", "\"Anatomy\" 手稿", "未系年", "writings", "**只此一处的手稿，出版著作里没有**"),
 ("1238", "Christian Socialism", "未系年", "writings", "手稿"),
 ("1239", "Christianity in Medicine", "未系年", "writings", "**只此一处的手稿**"),
 ("1240", "Counsel to Parents", "1878", "writings", "同名单行本的手稿/誊本"),
 ("1241", "Criticism of Gronlund's Co-Operative Commonwealth", "未系年", "writings", "手稿"),
 ("1242", "Erroneous Method in Medical Education", "未系年", "writings", "手稿"),
 ("1244", "The Human Element in Sex", "未系年", "writings", "同名单行本的手稿"),
 ("1246", "Medicine and Morality", "未系年", "writings", "手稿"),
 ("1248", "On the Decay of Municipal Representative Government", "1885", "writings", "同名单行本手稿"),
 ("1249", "\"On the Education of Women Physicians\" 手稿", "未系年", "writings",
  "**只此一处的手稿**"),
 ("1250", "On the Humane Prevention of Rabies", "未系年", "writings", "手稿"),
 ("1251", "\"The Position of Women\"，费城 The Press", "1889", "expression",
  "**报刊撰文，只此一处**"),
 ("1252", "Purchase of Women", "未系年", "writings", "手稿"),
 ("1253", "The Religion of Health", "1878", "writings",
  "★ **一度被我标为受污染，查证是误报**：命中的 `apply to` 是正常散文里的用法。"
  "真实情况是 folder 内含同一小册子的**两份誊本**，故字数约为单行本的两倍"),
 ("1254", "Rescue Work（1/2）", "未系年", "writings", "手稿"),
 ("1255", "Rescue Work（2/2）", "未系年", "writings", "手稿"),
 ("1256", "Responsibility of Women Physicians", "未系年", "writings", "手稿"),
 ("1257", "Scientific Method in Biology", "1898", "writings", "同名单行本手稿"),
 ("1258", "A Serious Protest to the Alumnae Association", "未系年", "decisions",
  "**致校友会的正式抗议，是建制立场文本**"),
 ("1259", "\"Signs of the Times\" 手稿", "未系年", "writings", "**只此一处**"),
 ("1260", "Why Hygienic Congresses Fail", "未系年", "writings",
  "★ **原判「只此一处」是错的**：`check_holdout_overlap` 实测它与 Essays 卷二覆盖 **80.7%**"
  "——这一篇被收进了文集。**探测报告把它列进「只此一处的一手文本」，我照抄了，判据当场推翻。**"),
 ("1261", "Wrong and Right Methods（1/2）", "1883", "writings",
  "同名单行本手稿。★★ **末尾接了一张剪报**：第 1797–1811 行（约 284 词 = 1.7%）是一整栏"
  "「SITUATIONS WANTED」求职分类广告，从她的句子中断处突起"
  "（`…would be justified.SITUATIONS WANTED`）。**是她剪贴作论据、还是众包转写了无关剪报，"
  "从文本本身判不了**——但后果相同：**那 15 行不许当她的话引**。"
  "文中另有 3 处 `apply to` 是她自己的行文（`may apply to the police`、"
  "`This term should apply to both sexes`），**不是广告**——按密度筛会把它们一起冤枉。"),
 ("1262", "Wrong and Right Methods（2/2）", "1883", "writings", "同名单行本手稿"),
 ("1263", "Bibliography", "未系年", "timeline", "著作系年表"),
 ("1266", "Misc. notes 2/3", "未系年", "writings", "杂记"),
 ("1267", "Misc. notes 3/3（1830 年少年习作本）", "1830", "expression",
  "**九岁时的习作本，最早的文体样本**"),
 ("1268", "Notes for speech on English charities", "未系年", "expression", "演讲笔记"),
 ("1269", "Poetry（`copies in Dr. Eliz. hand`）", "未系年", "expression",
  "**诗，档案卡片注明是她手迹的誊本**"),
 ("1270", "Stories and translations 1/3", "未系年", "expression", "故事与译作"),
 ("1271", "Stories and translations 2/3", "未系年", "expression", "故事与译作"),
 ("1272", "Stories and translations 3/3", "未系年", "expression", "故事与译作"),
]

# ── E. LoC 家庭通信 11 份 ─────────────────────────────────────
# ★★ 方向必须逐卷读，不许按 folder 名推。
#   folder 名是**通信对象**（`Blackwell, Alice Stone`），**不指方向**。
#   我第一版把「方向已实测确认是她写出去的」从 Hannah 卷与 985 卷**推广到了 11 卷**，
#   逐卷读开头后实测：**4 卷是寄给她的，1 卷双向混装。**
#   （972「Dear Aunt Elizabeth」、973「Dear Doctor…send to you」、
#     976 是 Henry 的《Woman's Journal》信笺、978「Dear Cousin Elizabeth」。）
#   改完一手从 78 降到 74 —— **降下来的才是真的。**
# (folder, 通信对象, 方向, 分档, 归属标记)
FAMILY = [
 ("972", "Alice Stone Blackwell（侄女）", "in", "S1", "THIRD-PARTY"),
 ("973", "Anna Blackwell", "in", "S1", "THIRD-PARTY"),
 ("975", "Hannah Blackwell（母）", "out", "P1", "HIS-OWN"),
 ("976", "Henry Browne Blackwell", "in", "S1", "THIRD-PARTY"),
 ("978", "John Kenyon Blackwell", "in", "S1", "THIRD-PARTY"),
 ("979", "Kitty Barry Blackwell（养女）", "both", "P1", "HIS-OWN"),
 ("980", "Marian Blackwell", "out", "P1", "HIS-OWN"),
 ("981", "Samuel C. Blackwell", "out", "P1", "HIS-OWN"),
 ("982", "Sarah Ellen Blackwell", "out", "P1", "HIS-OWN"),
 ("983", "Lucy Stone", "out", "P1", "HIS-OWN"),
 ("985", "其他家庭通信 1849–1872", "out", "P1", "HIS-OWN"),
]
DIRECTION = {
 "out": ("**实测是她写出去的**：卷内出现 `My dear <收信人>` 式抬头（Hannah 卷 13 处）。"
         "Hannah 卷首封 `Asheville July 27, 1848. My dear Mother`；"
         "985 卷首封 `Portway May 2nd 1849. My own dear friends all, Thanks be to Heaven, "
         "I am on land once more`（1849 年 4 月渡英抵岸报平安）。"),
 "in":  ("★ **实测是寄给她的，不是她写的**——folder 名是通信对象，**不指方向**。"
         "972 开头 `Dear Aunt Elizabeth`；973 `Dear Doctor—enclosed the letters…send to you`；"
         "976 是 Henry B. 的《The Woman's Journal》信笺；978 `Dear Cousin Elizabeth`。"
         "故 S1/THIRD-PARTY，`author` 留空，**不计入一手**。"),
 "both":("★★ **双向混装**：实测收 5 / 发 4。她自己的信确实在里面，故仍计 P1；"
         "**但从本卷取任何引文之前必须先认清说话人**——"
         "引文判据只验「这句话在语料里」，它分不出是谁说的。"),
}

# ── F. 二手：LoC 一般通信（**寄给她的**）10 份 + 书评剪报 1 份 ──
GENERAL = ["988", "1025", "1038", "1063", "1088", "1138", "1143", "1163", "1188", "1213"]

# ── 重复扫描（P2）──────────────────────────────────────────────
DUPES = [
 ("medicine-profession-women-1860-nlm", "t_62630060R.nlm.nih.gov.txt",
  "https://collections.nlm.nih.gov/ext/dw/62630060R/PDF/62630060R.pdf",
  "Medicine as a Profession for Women（NLM 藏本另一扫描）", "1860", "全本",
  "首行 `MON. MED. / Blackwell / Medicine as a Profession for Women / I860`"
  "（`I860` 为 OCR 原样，未代改）；**是 medicine-profession-women-1860 的重复扫描**"),
 ("pioneer-work-1895-ia", "t_pioneerworkforwo00blacuoft.txt",
  IA.format("pioneerworkforwo00blacuoft"),
  "Pioneer Work in Opening the Medical Profession to Women（archive.org 扫描）", "1895", "全本",
  "**是 pioneer-work-1895 的重复扫描**；PG 本已人工校对，此本 OCR 杂讯较多"),
 ("essays-v1-1902-ia", "t_essaysinmedicals00blacuoft.txt",
  IA.format("essaysinmedicals00blacuoft"),
  "Essays in Medical Sociology, Vol. I（archive.org 扫描）", "1902", "全本",
  "**是 essays-medical-sociology-v1-1902 的重复扫描**"),
 ("essays-v2-1902-ia", "t_essaysinmedicals02blacuoft.txt",
  IA.format("essaysinmedicals02blacuoft"),
  "Essays in Medical Sociology, Vol. II（archive.org 扫描）", "1902", "全本",
  "**是 essays-medical-sociology-v2-1902 的重复扫描**"),
]

# ── 受污染：标 U，不丢掉 ───────────────────────────────────────
CONTAMINATED = [
 ("1247", "「A Miscarriage of Justice」致编辑信（整版报纸剪贴簿）", 132156,
  "★★ **folder 是整版报纸剪贴簿，众包转写把整页报纸连同分类广告一起抄了**："
  "实测 `to be sold/apply to/for sale` 命中 **524 次**、`£` 金额 **404 次**，"
  "抽样第 9000 行是「二手服装店转让」「圣伦纳兹海滨住宅出售」。"
  "她本人署名仅 3 次、`To the Editor` 78 次——**她的实际文字只占极小比例**。"
  "**直接入库会把维多利亚时代的分类广告当成她的文体样本。**"),
 ("1265", "Misc. notes 1/3", 15263,
  "同上：黑斯廷斯地方法庭报道与股票行情剪报"),
]

RIGHTS_PUB = "出版年 1852–1902，早于 1929 → 美国公有领域；作者卒于 1910 亦满足生前+70"
RIGHTS_MSS = ("LoC 藏品 rights 字段原文：`Copyright in the unpublished writings of members "
              "of the Blackwell family has been dedicated to the public.`；"
              "独立地，依 17 U.S.C. §303，1978 年前创作未出版、作者卒于 1955 年前者已于 "
              "2003-01-01 进入美国 PD")
RIGHTS_LET = ("★ **不采用馆方标签**：该 item 的 licenseurl 标 CC-BY 4.0、rightsstatement 标 CNE"
              "（版权未经评估），**两者自相矛盾且都不足为据**。"
              "本项目依据：写于 1847–1851、未刊、作者卒于 1910 → 依 17 U.S.C. §303 已入 PD")


def mss(n: str) -> str:
    """LoC 藏品 id：**一律 `mss128800` + 4 位补零**。

    此前按 `mss1288000{n}` / `mss1288001{n}` 两种拼法分别处理，
    speech（1235–1272）与 general（1025–1213）两组全拼成了 `mss12880011235` 这种，
    **实测 44 份没落盘**——而脚本只打印「源文件不在」，
    不看那 44 行就会以为语料本来就只有 51 份。
    """
    return f"mss128800{int(n):04d}"


def row(short, url, title, year, locator, lang, tier, mark, lane, why, rights):
    return "\t".join([short, url, title, year, locator, lang, tier, mark,
                      f"lane={lane}. {why} RIGHTS={rights}"])


def main() -> int:
    if not SRC.is_dir():
        print(f"✗ **抓源目录不在：{SRC}**"); return 3
    RAW.mkdir(parents=True, exist_ok=True)
    lines = ["# ── #118 Elizabeth Blackwell (1821-1910, 美国第一位取得 MD 学位的女性; "
             "wrote in en) corpus ledger ──"]
    copied = skipped = 0
    seen_sha = {}

    def put(short, fname):
        nonlocal copied, skipped
        src = SRC / fname
        if not src.is_file():
            print(f"  ✗ 源文件不在：{fname}"); skipped += 1; return False
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        if sha in seen_sha:
            print(f"  ⚠ **{short} 与 {seen_sha[sha]} 逐位相同，跳过**（同一份下了两次）")
            skipped += 1; return False
        seen_sha[sha] = short
        d = RAW / short; d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, d / f"{short}.txt"); copied += 1
        return True

    for short, f, url, title, year, loc, tier, mark, lane, why in PUBLISHED:
        if put(short, f):
            lines.append(row(short, url, title, year, loc, "en", tier, mark, lane, why, RIGHTS_PUB))
    for short, f, url, title, year, loc, tier, mark, lane, why in LETTERS:
        if put(short, f):
            lines.append(row(short, url, title, year, loc, "en", tier, mark, lane, why, RIGHTS_LET))
    for n, span, words in DIARIES + [UNDATED]:
        short = f"diary-{span.replace(',', '-')}-mss{n}"
        if put(short, f"diary_{mss(n)}.txt"):
            _u = (n == "971")
            lines.append(row(short, LOC.format(mss(n)),
                             f"Elizabeth Blackwell Papers: Diary, {span}", span.split("-")[0],
                             f"folder {mss(n)}，众包**人工转写**（非 OCR），{words:,} 词",
                             "en", "U" if _u else "P1",
                             "ATTRIBUTION-UNCLEAR" if _u else "HIS-OWN", "timeline",
                             UNDATED_NOTE if _u else
                             "归属（全组共用）：`Emily` 通篇出现、`Kitty`（养女 Kitty Barry）高频、"
                             "`N.Y. Infirmary` 见于 967/968/969 册；1836 年册首页自题 "
                             "`Private Journal. Elizabeth`", RIGHTS_MSS))
    for n, title, year, lane, why in SPEECH:
        short = f"sp-{n}-" + "".join(c if c.isalnum() else "-" for c in title.lower())[:40].strip("-")
        if put(short, f"sp_{mss(n)}.txt"):
            lines.append(row(short, LOC.format(mss(n)),
                             f"Elizabeth Blackwell Papers: {title}", year,
                             f"folder {mss(n)}，众包人工转写", "en", "P1", "HIS-OWN",
                             lane, why, RIGHTS_MSS))
    for n, who, direction, tier, mark in FAMILY:
        short = f"fam-{n}-" + "".join(c if c.isalnum() else "-" for c in who.lower())[:32].strip("-")
        if put(short, f"fm_{mss(n)}.txt"):
            lines.append(row(short, LOC.format(mss(n)),
                             f"Elizabeth Blackwell Papers: Family Correspondence, {who}",
                             "1844-1906", f"folder {mss(n)}，众包人工转写",
                             "en", tier, mark,
                             "conversations" if tier == "P1" else "external",
                             DIRECTION[direction], RIGHTS_MSS))
    for n in GENERAL:
        short = f"gen-{n}"
        pad = mss(n)
        if put(short, f"gn_{pad}.txt"):
            lines.append(row(short, LOC.format(pad),
                             f"Elizabeth Blackwell Papers: General Correspondence, folder {n}",
                             "1850-1910", f"folder {pad}，众包人工转写", "en", "S1", "THIRD-PARTY",
                             "external",
                             "★ **是寄给她的来信，不是她写的**——收信人是她 ≠ 她写的，"
                             "故 S1/THIRD-PARTY，不计入一手。"
                             + ("其中 1143 是 Florence Nightingale 卷，档案标注 `from + To`，"
                                "3,661 词" if n == "1143" else ""), RIGHTS_MSS))
    if put("book-reviews-clippings", f"sp_{mss('1264')}.txt"):
        lines.append(row("book-reviews-clippings", LOC.format(mss("1264")),
                         "Elizabeth Blackwell Papers: Book reviews（剪报）", "1880s",
                         f"folder {mss('1264')}", "en", "S1", "THIRD-PARTY", "external",
                         "当时医学界对《The Human Element in Sex》的书评——**别人写她的**",
                         RIGHTS_MSS))
    for short, f, url, title, year, loc, why in DUPES:
        if put(short, f):
            lines.append(row(short, url, title, year, loc, "en", "P2",
                             "HIS-OWN DUPLICATE-SCAN", "writings", why, RIGHTS_PUB))
    for n, title, words, why in CONTAMINATED:
        short = f"contaminated-{n}"
        if put(short, f"sp_{mss(n)}.txt"):
            lines.append(row(short, LOC.format(mss(n)),
                             f"Elizabeth Blackwell Papers: {title}", "未系年",
                             f"folder {mss(n)}，{words:,} 词", "en", "U",
                             "ATTRIBUTION-UNCLEAR", "writings",
                             why + " **标 U 而不是丢掉**：丢掉等于假装没抓过；"
                             "标 U 则不计入 usable，而且下一个人看得见这里有多少字不能用、成因是什么。",
                             RIGHTS_MSS))

    (RAW / "_ids.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body = [l for l in lines if not l.startswith("#")]
    tiers = {}
    for l in body:
        t = l.split("\t")[6]; tiers[t] = tiers.get(t, 0) + 1
    lanes = {}
    for l in body:
        ln = l.split("\t")[8].split(".")[0].replace("lane=", "")
        lanes[ln] = lanes.get(ln, 0) + 1
    print(f"\n落盘 {copied} 份，跳过 {skipped} 份；台账 {len(body)} 行")
    print(f"  分档 {tiers}")
    print(f"  道   {lanes}")
    prim = tiers.get("P1", 0) + tiers.get("P2", 0)
    print(f"  **一手（P1+P2）{prim} 份**，其中 P2 重复扫描 {tiers.get('P2',0)} 份"
          f" → **去重后 {tiers.get('P1',0)} 份**（deep 要 30）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
