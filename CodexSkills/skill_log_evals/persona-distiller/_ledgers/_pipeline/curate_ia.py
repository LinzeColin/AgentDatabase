#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探源结果 → 抓取清单的**筛选器**。只做机械筛，**每一条被丢掉的都要报数**。

用法：
    python3 curate_ia.py --tsv <probe 出的 tsv> --person <人物键> --out <ids.txt>

**五道筛，每道都报丢了多少（[[empty-default-swallows-unknown]]：不许静默丢）：**

① **访问受限**：`collection` 含 `inlibrary`／`printdisabled`／`lendinglibrary`
   ⇒ 丢。**这不是「筛掉噪声」，是本项目不绕访问控制。**
② **版次年 > 1930**：现代版本，PD 判定站不住（且多半同时受限）。
   ★ 年份取 `year` 字段；**该字段在 IA 上时而是原作年时而是版次年**
   （`_IA的date是原作年不是版次年-2026-08-11.md`），所以它**只用来丢，不用来留**——
   留下的仍要靠正文题名页复核。
③ **同名者排除**：按 `EXCLUDE[person]` 逐条匹配 creator 串。
   ★ 名单来自各人 `00-抓源前必读.md`，**不是我现编的**。
④ **目标不在 creator 里**：收紧检索式后仍会有漏网（creator 多值）。
⑤ **上限**：`--cap` 条为止，**按「目标是第一作者」优先，并在馆之间轮转取**。
   ★★ **轮转不是锦上添花，是硬需求**：按字母序取会让 Kant／Bismarck 一次取到
   30 卷同一批 `bsb`（巴伐利亚州立图书馆的同一套），于是
   ①`min_lanes` 是虚的（只有一条道）；②OCR 错误无从互校。
   Kant 的 `00-抓源前必读.md` 原话是「**有意跨馆取件，不要让 bsb 占到八成**」。
   被上限丢掉的条数单独报，**不许混进前四道**
   （[[samples-cannot-support-universal-claims]]）。

★ 退出码：0=有留存；2=参数错；3=**一条都没留下**。
"""
import argparse
import pathlib
import re
import sys

RESTRICTED = ("inlibrary", "printdisabled", "lendinglibrary")

# ★ 每一条都出自对应工作区的 00-抓源前必读.md / *-selected.json 的「必须逐份排除」
EXCLUDE = {
    "marshall": ["Marshall, John Marshall", "Harlan", "1818-1891", "1783-1841",
                 "1786-1880", "1756-1824", "1664-1732", "1845-1915", "fl. 1895",
                 "Marshall, John W", "Marshall, John G"],
    "lincoln": ["1744-1786", "Lincoln, Abe", "1907-2000"],
    "jefferson": ["Randolph", "Hogg", "Thomas Garland", "1847-1864", "1856-1932"],
    "bismarck": ["1897-1975", "Bismarck, Herbert", "1849-1904", "1901-1949"],
    "machiavelli": [],
    "rousseau": ["Rousseau, Jean-Baptiste", "Rousseau, Henri", "Rousseau, Th"],
    "kant": [],
    "pestalozzi": ["1674-1742"],
    # ★ Karl Friedrich Fröbel 的**姓名完整含目标全名**，收紧到全名也挡不住，
    #   只能按生卒年与「Karl」排（见 wip-frobel-181/02-探源分析 第二刀）
    "frobel": ["Karl Friedrich", "Fröbel, Karl", "Fröbel, Julius", "Guido von"],
    "comenius": ["Comenius, Bernhard"],
    # ★★ Burbank 的污染形态是**法人商号**，不是同名自然人——而**不能按商号排**：
    #   实测 184 行里 **123 行同时含「Burbank, Luther, 1849-1926」与某个商号段**
    #   （`Luther Burbank (Firm)`／`Burbank, Luther Company`／`Luther Burbank Society`
    #    ／`Burbank's Experiment Farms`／`Henry G. Gilbert Nursery and Seed Trade Catalog Collection`）。
    #   按商号排会砍掉 **67%**，其中包括他自己的书。
    #   ⇒ EXCLUDE 留空，一手／二手交给 `classify_primary.py` 判（它的 `需人判` 不默认成一手）。
    #   ★ 真正的风险在别处：**184 行里 103 行（56%）是种苗价目表／商品目录**，
    #     其余去重只剩 **11 种题名**。这是「语料够份数而声口不够」的高风险面
    #     （同 Coffin #130／Sellers #154），**抓完必须先量声口再往下走**。
    "burbank": [],
    # ★ Leonardo 与 Burbank **正好相反**：这里的「同现」本身就是污染。
    #   实测 337 条里 50 条同时列着 Hollar／Dürer 与 Leonardo——那是**照他的画刻的版画**
    #   （Met 的 `mma_*` 图像记录），其中 **49 条首位就是刻工**。
    #   ⇒ 排掉是对的；而 Burbank 那次「按商号排会砍掉 67% 的自著」，所以那边留空。
    #   **同一个字段，两个人物要相反的处置——不能照抄。**
    "leonardo": ["Hollar", "Dürer", "Durer"],
    # ★★★ Michelangelo #185：**同一个字段，第三种处置**。
    # burbank  → EXCLUDE 空（按商号排会砍掉 67% 的自著）
    # leonardo → 按同现排（50 条 Hollar/Dürer **全部**同时列着 Leonardo，同现即污染）
    # michelangelo → **只能按名逐个排**：池 287 条里首位 creator 不是他的有 **68 条**，
    #   而这 68 条**全部**同时列着他 —— 若照 leonardo 的「同现即污染」一刀切，
    #   会连带砍掉**正好是补道用的那几份**：
    #     · Milanesi 编《Le lettere di Michelangelo Buonarroti》 ← conversations 道的核心
    #     · Hollanda《Quatro diálogos da pintura antiga》         ← 与他的对话录
    #     · Symonds 12（传记＋十四行诗英译）／Gotti 2《Vita di Michelangelo》／
    #       Rolland 4《Das leben Michelangelos》＋《Michel-Ange poète》／
    #       Knapp 5／Holroyd 4                                    ← external 道
    #   ⇒ 排掉的只有两类，**逐条读过题名**：
    #     ① 别人自己的著作（与他无关）：Vignola 6《Regola delli cinque ordini d'architettura》、
    #        Aviler 4《Cours d'architecture》、Speroni 9《Teatro italiano antico》、
    #        Dante 1《La vita nuova》
    #     ② 照他的作品刻/画的复制品（同 leonardo 的 Hollar/Dürer）：
    #        Sargent 3《Night》《Dawn》、Timothy Cole 2《Old Italian Masters》、
    #        Enea Vico 1、Raimondi 2《The Climbers》、Melchior Lorck 2《Crucified Man》
    # ★★★ Brandeis #172：**14 个同名候选，2026-08-13 逐条补裁定后才接的线**。
    #   原来只裁定了 1 个（目标本人），另 13 个没处置，而 `namesake_gate.json` 的 `ready`
    #   是从**只有 1 个候选**的那次搜索建的 —— 它没见过另外 13 个。
    #   ★ 判定不是靠时间戳，是**靠覆盖率**：裁定覆盖 1/14 ⇒ 更晚那次广搜（14 候选、
    #     resolution=multiple、status=blocked）才是有效判定。
    #   三个最危险的：
    #     ① **Brandeis University 及其约 20 个下属机构** —— 候选文件实测
    #        「检索 `Brandeis` 首屏 25 条里 **20 条属此族**」。**以他命名，但不是他**，
    #        与 Michelangelo 的画册同型（题名里全是他，作者不是他）。
    #     ② **Louis Brandeis Wehle（1880–1959），目标的侄子，也是律师** ——
    #        他的全名**整个包含**目标的全名（同 Gantt #156 的 `Mrs. H. L. Gantt` 形态）。
    #     ③ **另一个 Louis Brandeis（1902–1945）** —— 姓名完全相同、年代重叠，**只能靠生卒年分**。
    "brandeis": ["Wehle", "1902-1945", "1902–1945",
                 "Brandeis University", "Brandeis Univ", "Brandeis Press",
                 "Brandeis law journal", "Brandeis Medal",
                 "Alfred Brandeis", "1854-1928",
                 "Madeline Brandeis", "Irma Brandeis", "Antonietta Brandeis",
                 "Eugen Brandeis", "Antoine Brandeis", "Friedrich Brandeis",
                 "Jan Adolf Brandeis", "Adele Brandeis"],
    # ★★★ Henry Ford #188：`creator:"Ford, Henry"` 的池子里**绝大多数不是他**。
    #   PD（≤1930）136 条按 creator 原样统计：
    #     Ford, Henry Jones            49   ← **历史学家 Henry Jones Ford（1851–1925）**
    #     Ford, Henry Jones, 1851-1925 47   ← 同上
    #     Ford, Henry, 1863-1947        8   ← ★ 工业家本人
    #     Worthington Chauncey Ford…    2   ← 第三个人
    #     Ford, Henry A., comp…         3   ← 第四个人（编县志的）
    #   ⇒ **历史学家一系占 70.6%，工业家只占 7.4%。**
    #   ★★ 年代筛不掉他：Henry Jones Ford 卒 **1925**，同期、同样在公有领域。
    #     [[namesakes-whose-works-are-also-public-domain]]
    #   ★ 而且他会**凭空造出一条道**：那 96 条里 27 条被 assign_lanes 判进 timeline
    #     （`chronicle` 命中《…a chronicle of the rise and fall of federalism》），
    #     **那条道里一份都不是工业家的**。
    #   ★★★ 排除跑完再看剩下的，又现出**第五个人**：
    #     `Ford, Henry Justice`（1860–1941）—— 安德鲁·朗童话集的**插画家**，
    #     《The Golden mermaid, and other stories from the fairy books》(1906)、
    #     《The book of saints and heroes》(1912)，同样在公有领域、年代重叠。
    #     以及编县志那位的另一种写法（《The history of Putnam and Marshall counties》1860）。
    #   ⇒ 这个姓名下**至少五个人**。[[namesakes-whose-works-are-also-public-domain]]
    "ford": ["Henry Jones", "Ford, Henry J.", "1851-1925", "1851–1925",
             "Worthington Chauncey", "Henry A., comp", "Kate B.",
             "Ford, Henry Neville",
             "Henry Justice", "1860-1941", "1860–1941",
             # ★ 题名词**不能写在这里**：本表只比 creator。
             #   我第一版把 `saints and heroes` 一类写了进来，于是童话集照样被抓
             #   —— 已挪到 EXCLUDE_TITLE。**两张表比的字段不同，别放错。**
             "Henry Clinton", "1867-1936",
             # ★ 第三轮才现出的写法：`Ford, Henry A. [from old catalog]`
             #   （《Michigan》1891）——我原来只写了 `Henry A., comp`。
             #   **枚举永远不全**，这正是 check_impossible_by_lifespan 存在的理由。
             "Ford, Henry A"],
    # ★★★ Plato #186：**四类同名，全在抓源前实测过**（池 2617 条）。
    #   ① `PLATO Learning, Inc.`（1990s–2000s 教学软件公司，前身是 PLATO 计算机教学系统）32 条
    #      —— Foshay／Hannafin／Quinn／Sherman 的 "PLATO Evaluation Series"、"PLATO Courseware"。
    #      ★ 这一类**全部 >1930，PD 筛就挡住了**，写在这里是为了让下一个人知道它存在。
    #   ② `Shaw, P. E. (Plato Ernest), 1883-1947` 5 条 —— **中名叫 Plato 的人**。
    #      ★★ 其中 **1930 年那本《The early tractarians and the Eastern church》会穿过 PD 筛**，
    #      是四类里唯一靠年份挡不住的实体。
    #   ③ `Sinclair y el plato lleno de espantapájaros`（乐队）8 条 —— 西语 `plato` ＝**盘子**。
    #      ★★ **全部无年份 ⇒ 年份筛一条也挡不住**，只能按名排。
    #   ④ `Giovanni De Plato`（意大利作者，姓氏含 Plato）2 条。
    #   ★★★ **负对照做过**：题名含 `de Platon` 的 **26 条是他著作的法译本**
    #   （《Oeuvres de Platon》《La Republique de Platon》），**不许排**。
    #   我第一版写 `De Plato` 没加词边界，把这 26 条全误判成同名者
    #   —— 与 `letter` ⊂ `letterari` 同型（[[regex-must-clear-the-corpus-language]]）。
    "plato": ["PLATO Learning", "PLATO Evaluation", "PLATO Courseware", "PLATO Technical",
              "(Plato Ernest)", "plato lleno", "Espantap", "Giovanni De Plato"],
    "michelangelo": ["Vignola", "Aviler", "Speroni", "Dante Alighieri",
                     "Sargent", "Timothy Cole", "Enea Vico", "Raimondi", "Lorck",
                     # ★★ **侄孙 Michelangelo Buonarroti il Giovane（1568–1646）**——
                     #   同姓同名，写喜剧的，与雕刻家不是一个人。
                     "1568-1646", "il Giovane", "il giovane"],
}

# ★★★ 2026-08-13 新增：**按题名排除**。
# 起因：`EXCLUDE` 只比 creator 串，而侄孙有一条 `bub_gb_az-3FvsPFwYC`
# 《La Tancia commedia rusticale》的 creator **只写「Michelangelo Buonarroti」**——
# 没有年份、没有 il Giovane、没有任何可比的标记 ⇒ **按 creator 永远挡不住**。
# 实测：上一版清单 85 条里混进 **8 条侄孙的作品**（La Tancia 3、La Fiera 5），
# 其中 5 条 creator 明写 `1568-1646` 也照样放行了，因为那时排除名单里没写这一条。
# [[test-the-guard-against-this-persons-namesake]]：**护栏要拿这个人物的同名者重测一遍。**
# ★ 只排他侄孙**自己写的**那几部；侄孙 1623 年**编**的伯祖父《Rime》不在此列（那是雕刻家的诗）。
EXCLUDE_TITLE = {
    # ★ Ford #188：这些是**题名**词，属于另外四个同名者（插画家／编县志的／语文学家）。
    #   逐条实测：`bookofsaintshe00lang` 的 creator 是 `Lang, Mrs; Lang, Andrew; Fo…`，
    #   creator 那一侧根本比不着，**只能按题名排**。
    "ford": ["saints and heroes", "golden mermaid", "fairy book",
             "putnam and marshall", "hamilton county", "poems of history",
             "language of chaucer", "dance manual"],
    "michelangelo": [
        "La Tancia", "La Fiera", "Il Giulè", "La Dote",
        "Il giudizio di Paride", "Frottole della peste",
        "Quaderno delle rime burlesche",
        "Epistola al Signor Niccolò Arrighetti",
    ],
}
# 目标必须出现在 creator 里的**姓名词元**（同一个 creator 段里全部出现即命中）。
# ★★ 曾写成 `["Fröbel, Friedrich"]` 这种「姓, 名」定串，于是
#   `creator: Friedrich Fröbel`（**名在前、无逗号**）一律匹配不上。
#   实测代价：Fröbel 的德文原著 **《Die Menschenerziehung》(1863,
#   bub_gb_SMoJAQAAIAAJ) 被当成「目标不在 creator 里」丢掉**，
#   而他当时正差 1 份独立文献够 standard 门。
#   ⇒ 改为**词元匹配**：段里同时含「fröbel」与「friedrich」才算，顺序不论。
REQUIRE = {
    "marshall": [["marshall", "john", "1755-1835"]],
    "lincoln": [["lincoln", "abraham"]],
    "jefferson": [["jefferson", "thomas"]],
    "bismarck": [["bismarck"]],
    "machiavelli": [["machiavelli"]],
    "rousseau": [["rousseau", "jean"]],
    "kant": [["kant", "immanuel"]],
    "pestalozzi": [["pestalozzi"]],
    "frobel": [["fröbel", "friedrich"], ["froebel", "friedrich"], ["frobel", "friedrich"]],
    "comenius": [["comenius"], ["komensk"]],
    "burbank": [["burbank", "luther"]],
    "leonardo": [["leonardo", "vinci"], ["leonardo"]],
    # ★ 三种拼法都要收：IA 里同时存在 `Michelangelo Buonarroti`、
    #   `Buonarroti, Michelangelo`（22 条，与前式**零重叠**）与古体 `Michelagniolo`
    #   （1907 年那本 *Die Briefe des Michelagniolo Buonarroti*）。
    "michelangelo": [["michelangelo"], ["michelagniolo"], ["buonarroti"]],
    # ★ Brandeis：只收「brandeis ＋ louis」同段。
    #   ★★ 这**挡不住侄子 `Louis Brandeis Wehle`**（他同段里也含 brandeis 与 louis）——
    #   靠 EXCLUDE 的 `Wehle` 挡。**REQUIRE 与 EXCLUDE 要一起看，单看一侧会以为漏了。**
    # ★ 只加 EXCLUDE 不够：工业家有 2 条 creator 只写 `Ford, Henry`（无生卒年），
    #   靠 REQUIRE 把「必须同时出现的词」钉住。**两侧要一起看**，单看一侧会以为漏了。
    "ford": [["ford", "henry"]],
    "brandeis": [["brandeis", "louis"]],
    # ★ Plato 的著录有多种拼法：`Plato`／`PLATO`／`Plato, 427? BC-347? BC`／`Plato, Curt. Red.`，
    #   还有希腊文题名直接落在 creator 字段（`Πολιτεια του Πλατωνα`、`Ἀπολογία Σωκράτους`）。
    "plato": [["plato"], ["platon"], ["πλάτ"], ["πλατ"]],
}


def target_pos(creator: str, person: str) -> int:
    """目标在 creator 的第几段（0 起）；-1 = 不在。**按词元匹配，不认名序。**"""
    segs = [s.strip().lower() for s in creator.split(";")]
    for i, s in enumerate(segs):
        for toks in REQUIRE[person]:
            if all(tok in s for tok in toks):
                return i
    return -1


YEAR_RE = re.compile(r"^(\d{4})")
# 一个「馆／来源家族」的粗标记：先看 collection 里的可辨馆名，再退回 identifier 形态
LANE_HINTS = ("bsb", "cdl", "americana", "library_of_congress", "toronto", "robarts",
              "europeanlibraries", "wellcomelibrary", "digitallibraryindia",
              "jaigyan", "brynmawrcollege", "harvard", "getty", "biodiversity")


def family_of(ident: str, collection: str) -> str:
    """粗判来源家族。**只用于上限时的轮转，不用于任何判定。**"""
    c = collection.lower()
    for h in LANE_HINTS:
        if h in c:
            return h
    if ident.startswith("bim_"):
        return "bim"
    if ident.startswith("dli."):
        return "dli"
    if re.match(r"^\d{6,}bsb$", ident):
        return "bsb"
    return "其他"


def round_robin(rows: list, cap: int) -> tuple:
    """按家族轮转取满 cap；**同族内保序**。返回 (取中, 被上限截掉)。"""
    if len(rows) <= cap:
        return rows, []
    buckets: dict = {}
    for r in rows:
        buckets.setdefault(r[5], []).append(r)
    order = sorted(buckets, key=lambda k: (-len(buckets[k]), k))
    picked, i = [], 0
    while len(picked) < cap and any(buckets[k] for k in order):
        k = order[i % len(order)]
        if buckets[k]:
            picked.append(buckets[k].pop(0))
        i += 1
    rest = [r for k in order for r in buckets[k]]
    return picked, rest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--person", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap", type=int, default=30)
    ap.add_argument("--pd-cutoff", type=int, default=1930)
    a = ap.parse_args()
    if a.person not in EXCLUDE:
        print(f"未知人物键 {a.person}；已知：{sorted(EXCLUDE)}", file=sys.stderr)
        return 2

    lines = [l for l in pathlib.Path(a.tsv).read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    hdr = lines[0].split("\t")
    rows = [dict(zip(hdr, l.split("\t"))) for l in lines[1:]]

    drop = {"访问受限": [], "版次年>%d" % a.pd_cutoff: [], "同名者": [],
            "同名者·按题名": [], "目标不在creator": []}
    keep = []
    for r in rows:
        ident = r.get("identifier", "")
        coll = r.get("collection", "").lower()
        cre = r.get("creator", "")
        if any(x in coll for x in RESTRICTED):
            drop["访问受限"].append(ident); continue
        m = YEAR_RE.match(r.get("year", "") or "")
        if m and int(m.group(1)) > a.pd_cutoff:
            drop["版次年>%d" % a.pd_cutoff].append(ident); continue
        # ★★★ 2026-08-13 改成**大小写不敏感**。原来是原样比串，
        #   而 IA 的 creator 字段大小写乱七八糟：`Ford,henry Jones`、
        #   `Washington, George) Ford, Henry jones` —— 我写的排除词是 `Henry Jones`，
        #   **三条 Henry Jones Ford 的书就这么被抓了回来**（fetch 之后逐条核才看见）。
        #   全库前后实测：只多丢 **4 条**（Ford 3、Plato 1），且都是真该丢的。
        cre_l = cre.lower()
        if any(x.lower() in cre_l for x in EXCLUDE[a.person]):
            drop["同名者"].append(ident); continue
        ti_raw = r.get("title", "") or ""
        if any(x.lower() in ti_raw.lower() for x in EXCLUDE_TITLE.get(a.person, [])):
            drop["同名者·按题名"].append(ident); continue
        tp = target_pos(cre, a.person)
        if tp < 0:
            drop["目标不在creator"].append(ident); continue
        first = (tp == 0)   # 目标是不是第一作者（用于上限排序，不用于丢弃）
        keep.append((0 if first else 1, ident, r.get("year", "")[:4], cre[:70],
                     r.get("title", "")[:60], family_of(ident, r.get("collection", ""))))

    keep.sort()
    keep, capped = round_robin(keep, a.cap)

    total = len(rows)
    print(f"人物 {a.person}｜输入 {total} 条")
    for k, v in drop.items():
        print(f"  丢·{k:<14} {len(v):>4} 条" + (f"  例：{v[0]}" if v else ""))
    fams = {}
    for x in keep:
        fams[x[5]] = fams.get(x[5], 0) + 1
    print(f"  留                 {len(keep) + len(capped):>4} 条"
          f"（其中目标为第一作者 {sum(1 for x in keep + capped if x[0] == 0)}）")
    print("  取中的馆分布：" + "、".join(f"{k} {v}" for k, v in sorted(fams.items(), key=lambda kv: -kv[1])))
    if capped:
        print(f"  ⚠️ **上限 {a.cap} 截掉 {len(capped)} 条**——不是没有，是本轮不抓：")
        print("     " + "、".join(x[1] for x in capped[:8]) + ("…" if len(capped) > 8 else ""))
    if not keep:
        print("**一条都没留下** —— 检索式或排除名单有问题，不是「这个人没有语料」", file=sys.stderr)
        return 3

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(f"# {a.person}：探源 {total} 条 → 留 {len(keep)} 条（上限 {a.cap}，截掉 {len(capped)}）\n")
        f.write("# 丢：" + "；".join(f"{k} {len(v)}" for k, v in drop.items()) + "\n")
        for _, ident, y, cre, ti, fam in keep:
            f.write(f"{ident}\n")
    print(f"→ {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
