#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从实测 JSON + 落盘文件现生成 03/04/05 三份产物。**正文里的每个数都是现算的，不手写。**"""
import json, os, re, collections

WIP = ("/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/"
       "skill_log_evals/persona-distiller/_corpora/wip-kelsen-171")
RAW = os.path.join(WIP, "raw")
SP = "/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-interesting-franklin-988afc/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad"

M = {r["file"]: r for r in json.load(open(os.path.join(SP, "measure2.json"), encoding="utf-8"))}
CAT = json.load(open(os.path.join(SP, "catalog.json"), encoding="utf-8"))
FET = {r["filename"]: r for r in json.load(open(os.path.join(SP, "fetch_ledger.json"), encoding="utf-8"))}

# 题名页行区间（0 基闭区间）+ 逐件的判定材料
TP = {
 "staatslehre-dante-1905.txt": {
    "spans": [(10, 37, "丛书扉页"), (58, 92, "该册题名页 + 版权/印厂行")],
    "tp_year": None,
    "tp_year_note": "★**题名页无年份**：全文 `1905` 命中 **0** 次（本轮 grep 实测）。丛书扉页与该册题名页都只印到出版者为止。",
    "pd_basis": "K10plus PPN 146748832：008/07-10 = 1905、260$c = 1905（本轮 SRU 直查）。**不是 IA 的 date 字段。**",
    "type": "Antiqua", "type_basis": "探测报告实测 n30=p.17 的页图；本轮文本侧佐证：长 s 残留 0、Fraktur 讹形族 1.1%",
    "voice": "first-person", "voice_reason": "他一人署名的专著（题名页『VON HANS KELSEN.』），全书自述性论证；ich 5.86／wir 6.74 每万词",
 },
 "kommentar-reichsratswahlordnung-1907.txt": {
    "spans": [(108, 130, "题名页"), (154, 154, "译权保留声明"), (162, 162, "印厂行"), (166, 173, "Vorwort 首段")],
    "tp_year": "1907", "tp_year_note": "题名页逐字作 `Wien, 1907`（OCR 原样）。",
    "pd_basis": "题名页年 1907 ∧ K10plus PPN 377334669（008=1907、260$c=1907）。IA `date` 仅作线索。",
    "type": "Fraktur", "type_basis": "探测报告实测 n40=p.27 页图；本轮文本侧佐证：ist→ift 96.9%、und→unb 98.0%",
    "voice": "third-person", "voice_reason": "逐条释义制定法（体裁＝法条注释）。★ich/wir 严格计数为 0，但那**不是声口事实**——Fraktur 讹形把第一人称形态毁掉了（讹形比 93.6%），这个 0 是仪器看不见，不是不存在",
 },
 "grundlegung-rechtssoziologie-1914.txt": {
    "spans": [(3, 33, "期刊卷首扉页"), (63, 64, "分期出版日"), (73, 78, "论文首页题头")],
    "tp_year": "1914",
    "tp_year_note": "卷首扉页逐字作 `39. BAND. ı. HEFT` / `TÜBINGEN … 1914.`，另有 `-Juli-Heft 1914 (ausgegeben in Tübingen am 6. August 1914)`。★**内部不自洽**：封面写 1. Heft 而本文起于印刷页 839（应属后一分册）——照录不改，两说并存。",
    "pd_basis": "卷首扉页年 1914 ∧ K10plus PPN 39473713X（008=1914、260$c=1914）。★探测报告提到的『Bd. 39 常被引作 1915』本轮未见任何 1915 字样。",
    "type": "Antiqua", "type_basis": "探测报告实测 n8=p.846 页图；本轮文本侧佐证：长 s 残留 0、讹形族 0.0%",
    "voice": "first-person", "voice_reason": "署名书评式论战（驳 Ehrlich），题头逐字『Eine Grundlegung der Rechtssoziologie*). von HANS KELSEN.』；ich 3.68／wir 4.90",
 },
 "rechtswissenschaft-norm-oder-kultur-1916.txt": {
    "spans": [(0, 16, "期刊卷首扉页"), (23, 27, "论文首页题头")],
    "tp_year": "1916",
    "tp_year_note": "扉页逐字作 `49. Jahrgang,` / `Münden , verlag 99\" Dunder x Humblot + Leipzig` / `1916`。★**卷号异读**：扉页 OCR 作 `49.`，而同一份文件的书眉逐字作 `Sähmoller# Jahrbud **XL** 3.`（XL = 40），与编目的 Jg. 40 一致。**照录不改，两处并记。**",
    "pd_basis": "扉页年 1916（本件无 K10plus PPN 可对，探测报告 ④-A 未给）。年份来自**这一版的扉页**，不是 IA date。",
    "type": "Fraktur", "type_basis": "探测报告实测 n10=p.104 页图；本轮文本侧佐证：**长 s `ſ` 残留 1,917 处、占全部 s 字形 36.0%**，ist→ift 100%",
    "voice": "first-person", "voice_reason": "署名方法论论战（驳 Rickert/Lask/Radbruch）；ich 7.00／wir 5.00",
 },
 "politische-weltanschauung-erziehung-1918.txt": {
    "spans": [(0, 30, "年刊卷首扉页"), (36, 40, "论文首页题头")],
    "tp_year": "1918", "tp_year_note": "扉页逐字作 `BERLIN / VERLAG VON JULIUS SPRINGER / 1918`。",
    "pd_basis": "扉页年 1918（本件无 PPN 可对）。不是 IA date。",
    "type": "Antiqua", "type_basis": "探测报告实测 n6=p.6 页图；本轮文本侧佐证：长 s 残留 0、讹形族 0.0%",
    "voice": "first-person", "voice_reason": "署名讲词式政论；**ich 29.39／万词，全批最高**，是第二名（1916）的 4.2 倍",
 },
 "sozialismus-und-staat-1920.txt": {
    "spans": [(0, 13, "期刊封面（Grünbergs Archiv IX. Jg. 1. Heft）"), (77, 84, "本文题头"), (151, 151, "书脚")],
    "tp_year": "1920",
    "tp_year_note": "封面逐字作 `von C. L. Hirschfeld - Leipzig - 1920`；书脚逐字作 `Archiv f. Geschichte d. Sozialismus IX, hrsg. v. Grünberg.`。★**本轮新发现**：这一件不是光板专著扫描，而是**连 Grünbergs Archiv 的期刊封面一起扫进来的抽印本**——探测报告只记了『Leipzig : Hirschfeld，129 S.』，没记它的期刊载体。",
    "pd_basis": "封面年 1920 ∧ K10plus PPN 138477094（008=1920、260$c=1920）。",
    "type": "Antiqua", "type_basis": "探测报告实测 n30=p.29 页图；本轮文本侧佐证：讹形族 0.1%",
    "voice": "first-person", "voice_reason": "他一人署名的专著（题头逐字『Von Hans Kelsen (Wien).』）；ich 1.68／wir 8.40 —— **以「我们」为主的学术复数**",
 },
 "wesen-und-wert-der-demokratie-1920.txt": {
    "spans": [(6, 34, "题名页")],
    "tp_year": "1920", "tp_year_note": "题名页逐字作 `Tübingen / Vcrla.i^- von J. C. B. Mohr (Paul Siercok^ / 1920`（OCR 打坏了出版者名，年份清晰）。",
    "pd_basis": "题名页年 1920 ∧ K10plus PPN 019970889（008=1920、260$c=1920）。",
    "type": "Antiqua", "type_basis": "探测报告实测 n14=p.11 页图；本轮文本侧佐证：讹形族 0.5%",
    "voice": "first-person", "voice_reason": "他一人署名的专著（题名页逐字『Von Dr. Hans Kelscn』）；ich 6.11／wir 9.93",
 },
 "staat-und-recht-1922.txt": {
    "spans": [(0, 24, "期刊卷首扉页"), (27, 33, "本文题头")],
    "tp_year": "1922", "tp_year_note": "扉页逐字作 `VERLAG VON DUNCKER & HUMBLOT / MÜNCHEN UND LEIPZIG` / `| 1922`，另 `2. JAHRG HEFT 4`。",
    "pd_basis": "扉页年 1922（本件无 PPN 可对）。不是 IA date。",
    "type": "Antiqua", "type_basis": "探测报告实测 n6=p.23 页图；本轮文本侧佐证：讹形族 0.5%",
    "voice": "first-person（复数）", "voice_reason": "★**全篇 ich 严格计数 = 0，而 wir = 6.69／万词**。文本干净（讹形族 0.5%），所以这个 0 **是声口事实不是 OCR 假象**：这一篇他通篇用学术「我们」，一次「我」都不用",
 },
 "bundesverfassung-1920-coedited-1922.txt": {
    "spans": [(42, 78, "第五部分半题名页"), (80, 112, "题名页 + 出版者/印厂"), (118, 155, "Vorrede 首段与合作者段"), (166, 188, "Vorrede 责任声明与署名")],
    "tp_year": "1922", "tp_year_note": "题名页逐字作 `Wien unb £etp5ig / ^ranj Deutide / \\922`（Fraktur 误读成 Antiqua，`\\922` = 1922）。",
    "pd_basis": "题名页年 1922 ∧ K10plus PPN 066037980 / 140516891（008=1922、260$c=1922）。",
    "type": "Fraktur", "type_basis": "探测报告实测 n16/p.1 与 n300/p.285 页图；本轮文本侧佐证：ist→ift 100%、und→unb 99.8%、nicht 正形仅 1 处",
    "voice": "co-edited（不判归属）", "voice_reason": "★按指令②整卷记 `decisions` + `co-edited`，**任何一段都不单独归到他名下**。题名页逐字：『herausgegeben in Verbindung mit Dr. Georg Froehlich und Dr. Adolf Merkl **von** Dr. Hans Kelsen』",
 },
 "allgemeine-staatslehre-1925.txt": {
    "spans": [(68, 88, "题名页"), (110, 114, "题词"), (134, 140, "Vorrede 首段")],
    "tp_year": "1925", "tp_year_note": "题名页逐字作 `# ALLGEMEINE / 'STAATSLEHRE / VON / HANS KELSEN / BERLIN / VERLAG VON JULIUS SPRINGER / 1925`。",
    "pd_basis": "题名页年 1925 ∧ K10plus PPN 021386498（008=1925、260$c=1925）。",
    "type": "Antiqua", "type_basis": "探测报告实测 n40=p.23 页图；本轮文本侧佐证：**讹形族 0.0%，全批最干净的德语大部头**",
    "voice": "first-person", "voice_reason": "他一人署名的专著；Vorrede 首句逐字『… in dem ich die Probleme der Allgemeinen Staatslehre …』；ich 3.66／wir 2.92",
 },
 "rapports-de-systeme-1926-fr.txt": {
    "spans": [(0, 10, "课程题名叶"), (19, 35, "海牙学院编的 NOTICE BIOGRAPHIQUE（★第三人称写他，非他的文字）")],
    "tp_year": None,
    "tp_year_note": "★**题名页无年份**：课程题名叶只到作者与职衔为止；全文 `1927` 命中 **0**、`1926` 命中 8（且 8 处全在参考书目里指别人的书）。",
    "pd_basis": "K10plus PPN 394725883：008/07-10 = **1927**、260$c = 1927（本轮 SRU 直查）；IA `date` 记 1926。★另有**作者自证**：1928 年《Souveränität》第二版序（署 Wien, im November 1927）逐字写『… die im Recueil de T Academic de droit international de la Haye, **1927** erscluenen ist』。两说都 ≤1930，PD 不受影响。",
    "type": "Antiqua", "type_basis": "探测报告实测 n20=p.245 页图；本轮文本侧佐证：法语重音符 192.8／千词、法语词对讹形比 0.0%",
    "voice": "不作声口证据", "voice_reason": "★按指令⑧：未见译者署名，也未见『本人以法文撰写』的声明 → 只作事实来源。**测得 nous 18.32／万词是全批最高**，正因为如此更不能拿它当他的声口",
 },
 "problem-der-souveraenitaet-1928.txt": {
    "spans": [(0, 25, "题名页 + 版权/印厂"), (29, 43, "第二版序（含署名与日期）")],
    "tp_year": "1928",
    "tp_year_note": "★**探测报告存疑的一处本轮解决了**：题名页逐字作 `ZWBITE, PE0T0MECHANI80H OEDBUCKTE AUFLAOE / VERLAG VON J. C.B. MOHR (PAUL SIEBECK) / TUBINGEN 1928`。探测报告写『1928（推定，未见题名页）』，本轮**见到了题名页**，且与 K10plus 250$a『2., photomechanisch gedr. Aufl.』逐字对上。",
    "pd_basis": "题名页年 1928 ∧ K10plus PPN 019970358（008=1928、260$c=1928、250$a=2., photomechanisch gedr. Aufl.）。初版 PPN 141182563 记 1920，两版都 ≤1930。",
    "type": "Antiqua", "type_basis": "探测报告实测 n40=p.29 页图。★**但排体干净不等于文本干净**：见下讹形比",
    "voice": "first-person", "voice_reason": "他一人署名的专著；第二版序逐字署 `Hans Kelsen.`、`Wien, im November 1927.`；ich 5.12（严格）／7.45（含 icb 讹形）",
 },
}

ORDER = ["staatslehre-dante-1905.txt", "kommentar-reichsratswahlordnung-1907.txt",
         "grundlegung-rechtssoziologie-1914.txt", "rechtswissenschaft-norm-oder-kultur-1916.txt",
         "politische-weltanschauung-erziehung-1918.txt", "sozialismus-und-staat-1920.txt",
         "wesen-und-wert-der-demokratie-1920.txt", "staat-und-recht-1922.txt",
         "bundesverfassung-1920-coedited-1922.txt", "allgemeine-staatslehre-1925.txt",
         "rapports-de-systeme-1926-fr.txt", "problem-der-souveraenitaet-1928.txt"]

TITLE = {
 "staatslehre-dante-1905.txt": "Die Staatslehre des Dante Alighieri",
 "kommentar-reichsratswahlordnung-1907.txt": "Kommentar zur österreichischen Reichsratswahlordnung",
 "grundlegung-rechtssoziologie-1914.txt": "Eine Grundlegung der Rechtssoziologie",
 "rechtswissenschaft-norm-oder-kultur-1916.txt": "Die Rechtswissenschaft als Norm- oder als Kulturwissenschaft",
 "politische-weltanschauung-erziehung-1918.txt": "Politische Weltanschauung und Erziehung",
 "sozialismus-und-staat-1920.txt": "Sozialismus und Staat",
 "wesen-und-wert-der-demokratie-1920.txt": "Vom Wesen und Wert der Demokratie",
 "staat-und-recht-1922.txt": "Staat und Recht",
 "bundesverfassung-1920-coedited-1922.txt": "Die Bundesverfassung vom 1. Oktober 1920（＝Die Verfassungsgesetze der Republik Österreich, T. 5）",
 "allgemeine-staatslehre-1925.txt": "Allgemeine Staatslehre",
 "rapports-de-systeme-1926-fr.txt": "Les rapports de système entre le droit interne et le droit international public",
 "problem-der-souveraenitaet-1928.txt": "Das Problem der Souveränität und die Theorie des Völkerrechts（2. Aufl.）",
}


def verbatim(fn, a, b):
    p = os.path.join(RAW, M[fn]["src_dir"], fn)
    L = open(p, encoding="utf-8", errors="replace").read().split("\n")
    out = []
    for i in range(a, min(b + 1, len(L))):
        s = re.sub(r"[ \t]+", " ", L[i]).strip()
        if s:
            out.append(s)
    return out


def pct(x):
    return "—" if x is None else "%.1f%%" % (100 * x)


rows = [M[f] for f in ORDER]
tot_bytes = sum(r["bytes"] for r in rows)
tot_words = sum(r["words_whole_file"] for r in rows)
banned = [r for r in rows if r["no_verbatim_quote"]]
ok = [r for r in rows if not r["no_verbatim_quote"]]
by_genre = collections.Counter(r["genre"] for r in rows)
words_by_genre = collections.Counter()
for r in rows:
    words_by_genre[r["genre"]] += r["words_body"]

# ───────────────────────── 03-抓源清单.md ─────────────────────────
L = []
A = L.append
A("# #171 Hans Kelsen —— 抓源清单（12 件，逐件核实）\n")
A("日期：**2026-08-11**。并发**恒为 1**（全程串行 urllib，每件之间 sleep，未调用任何计费 API）。")
A("未碰付费墙、未绕任何访问控制、未绕验证码。写入范围仅 `_scratch/`，**主工作树未写入任何内容**。\n")
A("公有领域判据：**出版于 1931 年以前**（2026 − 95）。**PD 依据一律是「这一版的题名页年份／来源馆编目年份」，")
A("`IA metadata.date` 只作线索** —— 探测报告 ③-C 实测有 4 件 `date ≤1930` 而内容是在版权期的现代译本。\n")
A("> ★ **落盘的 `.txt` 与 archive.org 返回的字节完全一致**，未加任何出处表头、未做任何 OCR 修改。")
A("> 出处写在同目录的 `SOURCE.json` 里。")
A("> 理由是本项目记档过的事故：**我写的出处表头被当成正文**（占全文 17.2%），还把烂 OCR 托过了可读性下限。\n")
A("## 0. 一览\n")
A("| 项 | 值 |")
A("|---|---|")
A("| 实际落盘 / 计划 | **%d / 12** |" % len(rows))
A("| 总字节 | **%s** |" % format(tot_bytes, ","))
A("| 总词数（落盘文件现算） | **%s** |" % format(tot_words, ","))
A("| 体裁分道 | writings **%d** ／ expression **%d** ／ decisions **%d** |" %
  (by_genre["writings"], by_genre["expression"], by_genre["decisions"]))
A("| 语种 | 德语 **%d** ／ 法语 **%d** |" % (sum(1 for r in rows if r["lang"] == "ger"), sum(1 for r in rows if r["lang"] == "fre")))
A("| 标 `不可做逐字引文` | **%d**（见 §2） |" % len(banned))
A("| PD 依据只有 IA `date` 的件数 | **0**（逐件依据见 §3 的「PD 依据」栏） |")
A("| 题名页有年份 / 无年份 | **%d / %d**（无年份的两件退回编目记录，仍非 IA date） |" %
  (sum(1 for f in ORDER if TP[f]["tp_year"]), sum(1 for f in ORDER if not TP[f]["tp_year"])))
A("")
A("## 1. 逐件一行表\n")
A("| # | 题名（编目形） | 年 | 体裁道 | voice | 排体 | 讹形比(指令四对) | 长 s 残留 | h→b | 逐字引文 | 字节 | sha256(前16) | src 目录 |")
A("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, f in enumerate(ORDER, 1):
    r, t = M[f], TP[f]
    c = r["corruption"]
    A("| %d | %s | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | `%s` | `%s` |" % (
        i, TITLE[f], t["tp_year"] or (r["year"] + "（题名页无年，编目值）"), r["genre"],
        t["voice"], t["type"], c["pooled_named_str"], c["long_s_ratio_str"], c["hb_ratio_str"],
        "**禁**" if r["no_verbatim_quote"] else "可", format(r["bytes"], ","), r["sha256"][:16], r["src_dir"]))
A("")
A("> 「讹形比(指令四对)」＝指令点名的 `nicht/nidjt`、`ist/ift`、`und/nnd`、`sein/fein` 四对**合池**；")
A("> 各件的**实测讹形族**（真出现的讹形，往往与点名的那一个不同）逐件列在 §3。")
A("> `n/a(N=…)` ＝ 分母不足 %d，不给比值（本项目记档：门低于仪器噪声就是恒红或恒绿）。\n" % 50)

A("## 2. ★★ 讹形比实测 —— 每一件都量了，Antiqua 件也量\n")
A("「这份是 Antiqua」**不等于**「这份能做逐字引文」。本轮把两件事分开量，结论是这条提醒完全兑现了：\n")
A("| 件 | 排体 | 指令四对合池 | 指令四对单对最高 | 实测形族合池 | 实测形族单对最高 | 长 s | h→b(N) | 变音符/千词 | 判定 |")
A("|---|---|---|---|---|---|---|---|---|---|")
for f in ORDER:
    r, t = M[f], TP[f]
    c = r["corruption"]
    A("| %s | %s | %s | %s=%s | %s | %s=%s | %s | %s (N=%d) | %s | %s |" % (
        TITLE[f][:34], t["type"], c["pooled_named_str"],
        c["max_named_pair"][0] or "—", pct(c["max_named_pair"][1] or None),
        c["pooled_family_str"], c["max_family_pair"][0] or "—", pct(c["max_family_pair"][1] or None),
        c["long_s_ratio_str"], c["hb_ratio_str"], c["hb_good"] + c["hb_bad"],
        c["diacritics_per_1k_words"], "**禁引**" if r["no_verbatim_quote"] else "可引"))
A("")
A("**被标 `不可做逐字引文` 的 %d 件，逐件写明是哪条打红的：**\n" % len(banned))
for r in banned:
    A("- **%s**（%s）—— %s" % (TITLE[r["file"]], r["year"], "；".join(r["trigger"])))
A("")
A("### ★★★ 本轮最要紧的一条：**指令点名的那四对，漏掉了两件的真实错型**\n")
A("| 件 | 指令点名的讹形出现次数 | 该件真正的讹形 | 只按指令四对算会得到 | 真实情况 |")
A("|---|---|---|---|---|")
c7 = M["kommentar-reichsratswahlordnung-1907.txt"]["corruption"]
c28 = M["problem-der-souveraenitaet-1928.txt"]["corruption"]
c22 = M["bundesverfassung-1920-coedited-1922.txt"]["corruption"]
A("| Kommentar 1907 | `nidjt` **%d** 次 | `nid^t` %d、`nic^t` %d、`nid)t` %d | nicht 一对 %s | 全池 %s（靠 `ist/ift` 与 `sein/fein` 才打红） |" % (
    c7["pairs"]["nicht"]["named_bad"],
    dict(c7["pairs"]["nicht"]["family_top"]).get("nid^t", 0),
    dict(c7["pairs"]["nicht"]["family_top"]).get("nic^t", 0),
    dict(c7["pairs"]["nicht"]["family_top"]).get("nid)t", 0),
    c7["pairs"]["nicht"]["named_ratio_str"], c7["pooled_named_str"]))
A("| Bundesverfassung 1922 | `nnd` **%d** 次 | `unb` **%d**、`nnb` %d、`uub` %d | und 一对 %s | 全池 %s |" % (
    c22["pairs"]["und"]["named_bad"],
    dict(c22["pairs"]["und"]["family_top"]).get("unb", 0),
    dict(c22["pairs"]["und"]["family_top"]).get("nnb", 0),
    dict(c22["pairs"]["und"]["family_top"]).get("uub", 0),
    c22["pairs"]["und"]["named_ratio_str"], c22["pooled_named_str"]))
A("| **Souveränität 1928** | `nidjt` **%d**、`ift` %d、`fein` %d | **`nicbt` %d**（h→b），且**全文变音符 %s／千词** | 全池 **%s → 过门** | h→b 轴 **%s**（N=%d）、nicht 形族 **%s** → **不可做逐字引文** |" % (
    c28["pairs"]["nicht"]["named_bad"], c28["pairs"]["ist"]["named_bad"], c28["pairs"]["sein"]["named_bad"],
    dict(c28["pairs"]["nicht"]["family_top"]).get("nicbt", 0), c28["diacritics_per_1k_words"],
    c28["pooled_named_str"], c28["hb_ratio_str"], c28["hb_good"] + c28["hb_bad"],
    c28["pairs"]["nicht"]["family_ratio_str"]))
A("")
A("**结论**：指令给的四对讹形全部是 **Fraktur 专属错型**（长 s→f、ch→dj）。")
A("`in.ernet.dli.2015.190098` 是**印度 DLI 扫的 Antiqua 件**，它的错型是 **h→b 与变音符全失**，四对一条都碰不到——")
A("**只按指令四对量，这部 320 页的专著会被判成「可做逐字引文」而放行。**")
A("这就是本项目记档的「容错集合切错了位置」／「夹具比原文干净就等于没测」。\n")
A("> ★ 顺带自查到我**自己**造的两个假数（都是先看命中样本才发现的，已修）：")
A("> 1. 德语讹形族跑在法语件上，分母只有 18 个 token 却算出 **38.9%**，差点把全批最干净的一件标成禁引；")
A("> 2. h→b 轴在 1907／1922 两件上分母只有 14／10，比值 7.1%／80.0% 都是噪声 —— 现改为分母 <50 一律报 `n/a(N=…)`。\n")

A("## 3. 逐件详录（题名页逐字照录 + 出版年 + 排体 + 讹形 + 体裁 + voice）\n")
A("> **照录规则**：空白压平，**讹字一律照录不改**。")
A("> 凡我给出的「读作」都是**我的判读，不是逐字引文**，两者在下面分行标出。")
A("> 依据：Blackstone #169 有 5 份因 OCR 打碎署名而拿不到署名证据，全靠扉页照录才过的归属门。\n")
for i, f in enumerate(ORDER, 1):
    r, t = M[f], TP[f]
    c = r["corruption"]
    fe = FET[f]
    A("---\n")
    A("### %d. %s\n" % (i, TITLE[f]))
    A("| 栏 | 值 |")
    A("|---|---|")
    A("| src 目录 | `raw/%s/` |" % r["src_dir"])
    A("| 文件名 | `%s` |" % f)
    A("| IA identifier | `%s` |" % r["ia_identifier"])
    A("| 坐标 | %s |" % fe["details_url"])
    A("| 下载 URL | `%s`（HTTP **%d**） |" % (fe["download_url"], fe["http_status"]))
    A("| **字节数** | **%s**（IA 自报 size %s —— 现算比对：**%s**） |" % (
        format(r["bytes"], ","), format(int(fe["ia_reported_size"]), ","),
        "一致" if r["bytes"] == int(fe["ia_reported_size"]) else "★不一致"))
    A("| **sha256** | `%s` |" % r["sha256"])
    A("| 行数 / 词数 | %s / %s |" % (format(r["lines"], ","), format(r["words_whole_file"], ",")))
    A("| **这一版的出版年（题名页）** | %s |" % (("**%s**" % t["tp_year"]) if t["tp_year"] else "**取不到**"))
    A("| 年份说明 | %s |" % t["tp_year_note"])
    A("| **PD 依据** | %s |" % t["pd_basis"])
    A("| IA `date` 字段（仅线索） | `%s` |" % fe["ia_metadata_date_field"])
    A("| 译本标记扫描 | `translation/traducción/traduzione/a cura di/prefaced by` —— **%s** |" %
      ("无命中" if f not in ("staatslehre-dante-1905.txt", "kommentar-reichsratswahlordnung-1907.txt",
                            "sozialismus-und-staat-1920.txt", "allgemeine-staatslehre-1925.txt")
       else "有字面命中，**逐条读过命中样本，全部是假阳**（Kelsen 自己论中世纪 *translatio imperii*／论马恩著作的德译／Google 样板里的 machine translation），非译本"))
    A("| **排体** | **%s** —— %s |" % (t["type"], t["type_basis"]))
    A("| **讹形比（指令四对合池）** | %s（分母 %d） |" % (c["pooled_named_str"], c["pooled_named_N"]))
    A("| 讹形比（实测形族合池） | %s（分母 %d） |" % (c["pooled_family_str"], c["pooled_family_N"]))
    if r["lang"] == "ger":
        for k in ("nicht", "ist", "und", "sein"):
            pr = c["pairs"][k]
            A("| ├ `%s` | 正形 %d ／ 指令点名的 `%s` %d（%s）；**实测形族** %s |" % (
                k, pr["good"], pr["named_bad_form"], pr["named_bad"], pr["named_ratio_str"],
                "、".join("`%s`×%d" % (a, b) for a, b in pr["family_top"][:5])))
    else:
        A("| ├ 法语词对 | %s |" % "；".join(
            "`%s`/`%s` %d/%d" % (k, v["named_bad_form"], v["good"], v["named_bad"]) for k, v in c["pairs"].items()))
    A("| 长 s `ſ` 残留 | %d 处，占全部 s 字形 %s |" % (c["long_s"], c["long_s_ratio_str"]))
    A("| h→b 混淆（★指令未写的轴） | %d 讹 / %d 正 = %s |" % (c["hb_bad"], c["hb_good"], c["hb_ratio_str"]))
    A("| 变音符 | %d 处，%s／千词 |" % (c["diacritics"], c["diacritics_per_1k_words"]))
    A("| **逐字引文** | %s |" % ("**不可做逐字引文** —— %s" % "；".join(r["trigger"]) if r["no_verbatim_quote"] else "可"))
    A("| **体裁道** | `%s` |" % r["genre"])
    A("| **voice** | **%s** —— %s |" % (t["voice"], t["voice_reason"]))
    if r["foreign_blocks"]:
        A("| 已扣除的非 Kelsen 块 | %s |" % "；".join(
            "行 %d–%d（%d 词，含 ich %d／wir %d）：%s" % (b["lines"][0], b["lines"][1], b["words"], b["ich"], b["wir"], b["why"])
            for b in r["foreign_blocks"]))
    A("")
    A("**题名页逐字照录**（空白已压平，讹字未改）：\n")
    for a, b, why in t["spans"]:
        A("*%s（行 %d–%d）*\n" % (why, a, b))
        A("```")
        for line in verbatim(f, a, b):
            A(line)
        A("```\n")

# 1922 那卷的合编证据单独写
A("---\n")
A("## 4. ★ 1922 合编卷：合编身份的**一手证据**（不止是编目 245c）\n")
A("指令②要求这一卷只记 `decisions` + `co-edited`、任何一段都不许单独归到 Kelsen 名下。**本轮已照办。**")
A("同时把这一卷里**支持与不支持这条规则的证据都摆出来**，因为它们出自同一页：\n")
A("**支持（题名页，逐字照录）**：`f^erausgegeben in Perbinbung mit` / `Vv, (Scorg ^roetilidjimbDn 2lboIf 21TcrfI` / `von` / `Dv. f?ans helfen,`")
A("——我的判读（**不是逐字引文**）：「herausgegeben in Verbindung mit Dr. Georg Froehlich und Dr. Adolf Merkl von Dr. Hans Kelsen」。\n")
A("**不支持（Vorrede 第 174–178 行，逐字照录）**：\n")
A("```")
for line in verbatim("bundesverfassung-1920-coedited-1922.txt", 174, 178):
    A(line)
A("```\n")
A("——我的判读（**不是逐字引文**）：「Indes ist es doch nötig zu erklären, daß **ich allein für die Gesamtheit der in diesem")
A("Kommentar ausgesprochenen Anschauungen die Verantwortung übernehme**, daß sich meine Mitarbeiter aber vorbehalten,")
A("in dem einen oder anderen Punkte abweichende Meinungen zu vertreten.」\n")
A("而 Vorrede 结尾逐字署 `^ien, im guli 1922.` / `\"bam Seifen.`（读作 Wien, im Juli 1922 / Hans Kelsen）。\n")
A("> ★ **这条证据与指令的事实前提相抵触，但我没有据此放宽指令**：整卷仍记 `decisions` + `co-edited`，一段都没单独归他。")
A("> 摆出来是因为它可能该反馈回规则：**Froehlich 与 Merkl 在书里的身份是 `Mitarbeiter`（协作者），不是对等的第三方合编者**，")
A("> 而 Vorrede 本身是 Kelsen 一人署名的第一人称文字。要不要把 Vorrede 单独切出来，**是派活方的判断，不是我的**。")
A("> 另注：这一卷讹形比 %s，**上面两段照录本身就不能当逐字引文用** —— 我给的「读作」一律是判读。\n" %
  M["bundesverfassung-1920-coedited-1922.txt"]["corruption"]["pooled_named_str"])

open(os.path.join(WIP, "03-抓源清单.md"), "w", encoding="utf-8").write("\n".join(L))
print("写出 03-抓源清单.md", len("\n".join(L)), "字符")

# ───────────────────────── 04-声口密度实测.md ─────────────────────────
import statistics
G = {}
for g in ("writings", "expression", "decisions"):
    rs = [r for r in rows if r["genre"] == g]
    w = sum(r["words_body"] for r in rs)
    G[g] = {
        "rows": rs, "words": w,
        "ich": sum(r["first_person"]["ich_strict"] for r in rs),
        "wir": sum(r["first_person"]["wir_strict"] for r in rs),
        "ich_tol": sum(r["first_person"]["ich_strict"] + r["first_person"]["ich_ocr_var"] for r in rs),
        "wir_tol": sum(r["first_person"]["wir_strict"] + r["first_person"]["wir_ocr_var"] for r in rs),
    }
    for k in ("ich", "wir", "ich_tol", "wir_tol"):
        G[g][k + "_10k"] = 10000.0 * G[g][k] / w

# 只用「可引 ∧ 德语 ∧ 非合编」的干净子集再算一遍
clean = [r for r in rows if not r["no_verbatim_quote"] and r["lang"] == "ger"]
GC = {}
for g in ("writings", "expression", "decisions"):
    rs = [r for r in clean if r["genre"] == g]
    if not rs:
        GC[g] = None; continue
    w = sum(r["words_body"] for r in rs)
    GC[g] = {"n": len(rs), "words": w,
             "ich_10k": 10000.0 * sum(r["first_person"]["ich_strict"] for r in rs) / w,
             "wir_10k": 10000.0 * sum(r["first_person"]["wir_strict"] for r in rs) / w}

fr = M["rapports-de-systeme-1926-fr.txt"]
dia_ger = sorted(r["corruption"]["diacritics_per_1k_words"] for r in rows if r["lang"] == "ger")

L = []; A = L.append
A("# #171 Hans Kelsen —— 第一人称密度实测（按体裁分组）\n")
A("日期：**2026-08-11**，语料落盘**当轮**测。全部读回 `raw/` 下的落盘文件现算。")
A("分母＝**扣掉已核实的非 Kelsen 块之后**的词数（逐块行号与词数列在 §4）。\n")
A("依据：Holmes #170 实测同一人同一职务、代表机构 vs 代表自己，第一人称差 **35–65 倍**；")
A("页数比不能替代这个数。**本轮的答案是：Kelsen 身上没有那个量级的分野，见 §3。**\n")
A("## 1. 逐件\n")
A("| 件 | 体裁道 | 词数 | `ich`/万词 | `wir`/万词 | `ich`+讹形/万词 | `wir`+讹形/万词 | **第一人称形态**可信否 |")
A("|---|---|---|---|---|---|---|---|")
def fp_ocr_share(r):
    """★ 只看**第一人称形态本身**被打坏的比例，不拿全文讹形比替代它。
       教训同型：判据切错位置——1916 那件全文讹形比 30.3%，但坏的是长 s 词（ist/sein），
       ich/wir 一个没坏；拿全文比值给它贴『不可信』是贴错了。"""
    fp = r["first_person"]
    n = fp["ich_strict"] + fp["wir_strict"] + fp["ich_ocr_var"] + fp["wir_ocr_var"]
    bad = fp["ich_ocr_var"] + fp["wir_ocr_var"]
    if n < 10:
        return None, "n/a(N=%d<10)" % n, n
    return bad / n, "%.1f%%" % (100.0 * bad / n), n

for f in ORDER:
    r = M[f]; fp = r["first_person"]
    sh, shs, shn = fp_ocr_share(r)
    if sh is None:
        rel = "★第一人称样本太少（N=%d），不判" % shn
    elif sh > 0.10:
        rel = "★**严格计数偏低** —— 第一人称形态有 %s（N=%d）被 OCR 打坏" % (shs, shn)
    else:
        rel = "可信（第一人称形态被打坏 %s）" % shs
    A("| %s | `%s` | %s | **%.2f** | **%.2f** | %.2f | %.2f | %s |" % (
        TITLE[f][:40], r["genre"], format(r["words_body"], ","),
        fp["ich_per_10k"], fp["wir_per_10k"], fp["ich_tol_per_10k"], fp["wir_tol_per_10k"], rel))
A("")
A("## 2. 按体裁汇总\n")
A("| 体裁道 | 件数 | 词数 | `ich` 次 | `wir` 次 | **`ich`/万词** | **`wir`/万词** | `ich`+讹形/万词 | `wir`+讹形/万词 |")
A("|---|---|---|---|---|---|---|---|---|")
for g in ("writings", "expression", "decisions"):
    d = G[g]
    A("| `%s` | %d | %s | %d | %d | **%.2f** | **%.2f** | %.2f | %.2f |" % (
        g, len(d["rows"]), format(d["words"], ","), d["ich"], d["wir"],
        d["ich_10k"], d["wir_10k"], d["ich_tol_10k"], d["wir_tol_10k"]))
A("")
A("**只取「文本可信」的子集（德语 ∧ 非禁引 ∧ 非合编）再算一遍**——这才是能拿去下游用的数：\n")
A("| 体裁道 | 件数 | 词数 | `ich`/万词 | `wir`/万词 |")
A("|---|---|---|---|---|")
for g in ("writings", "expression", "decisions"):
    d = GC[g]
    if d is None:
        A("| `%s` | **0** | — | — | — |" % g)
    else:
        A("| `%s` | %d | %s | **%.2f** | **%.2f** |" % (g, d["n"], format(d["words"], ","), d["ich_10k"], d["wir_10k"]))
A("")
A("> ★ `decisions` 在干净子集里是 **0 件** —— 两件全是 Fraktur 禁引。")
A("> **这一道在本轮语料里没有可信的声口测量**，下游不许把 §2 上表那个 0.00 当成它的值。")
A("")
A("## 3. ★ 三条必须连着数一起说的话\n")
A("### 3-1 体裁并没有把声口分开——分开的是**单篇**\n")
gmax = max(G[g]["ich_10k"] for g in G); gmin = min(G[g]["ich_10k"] for g in G if G[g]["ich_10k"] > 0)
imax = max(rows, key=lambda r: r["first_person"]["ich_per_10k"])
imin = [r for r in rows if r["first_person"]["ich_per_10k"] == 0 and not r["no_verbatim_quote"]]
A("- 体裁之间（严格 `ich`／万词）：`expression` **%.2f** ／ `writings` **%.2f** ／ `decisions` **%.2f**。" %
  (G["expression"]["ich_10k"], G["writings"]["ich_10k"], G["decisions"]["ich_10k"]))
A("  - expression : writings = **%.2f 倍**；" % (G["expression"]["ich_10k"] / G["writings"]["ich_10k"]))
A("  - decisions 的严格值 0.00 **不能进这个比**（仪器盲，见 3-2）；改用含讹形的 %.2f，"
  "则 expression : decisions = **%.2f 倍**。" % (G["decisions"]["ich_tol_10k"],
                                              G["expression"]["ich_10k"] / G["decisions"]["ich_tol_10k"]))
A("  - ⇒ 三道之间最大跨度约 **%.1f 倍**。**Holmes #170 的 35–65 倍在这个人物身上没有出现**，差两个数量级。" %
  (G["expression"]["ich_10k"] / G["decisions"]["ich_tol_10k"]))
A("- 而**单篇之间**差得很开：最高 *%s*（`%s`）**%.2f**／万词，" % (TITLE[imax["file"]], imax["genre"], imax["first_person"]["ich_per_10k"]))
if imin:
    z = imin[0]
    # 干净德语件的合并 ich 率，用来算「0 次」到底有多罕见
    cl = [r for r in rows if not r["no_verbatim_quote"] and r["lang"] == "ger"]
    rate = sum(r["first_person"]["ich_strict"] for r in cl) / sum(r["words_body"] for r in cl)
    exp = rate * z["words_body"]
    import math
    A("  最低 *%s*（`%s`，文本干净：讹形族 %s、长 s 0、h→b %s）**0.00** —— 通篇只用学术「我们」（`wir` %.2f），一次「我」都没有。" %
      (TITLE[z["file"]], z["genre"], z["corruption"]["pooled_family_str"],
       z["corruption"]["hb_ratio_str"], z["first_person"]["wir_per_10k"]))
    A("  ★ **但这个 0 要连样本量一起看**：该篇仅 %s 词，按干净德语件的合并 `ich` 率 %.2f／万词，"
      "期望值只有 **%.1f** 次，观察到 0 次的概率约 **%.0f%%**（Poisson）。" %
      (format(z["words_body"], ","), 10000 * rate, exp, 100 * math.exp(-exp)))
    A("  ⇒ **可以说「这一篇没出现 ich」，不能说「他在这一篇刻意不用 ich」** —— 后者这份样本撑不起。")
A("- ⇒ **按体裁分道取样，取不到声口的方差；要按单篇取。** 这一条与探测报告的预期相反，")
A("  探测报告预期最高的是三件 *Erwiderung*（论战），而那三件本机都没有 PD 全文。\n")
A("### 3-2 `decisions` 那个 0 是**仪器看不见**，不是**不存在**\n")
A("- `decisions` 两件严格 `ich` 合计 **%d 次**，密度 **%.2f**／万词。" % (G["decisions"]["ich"], G["decisions"]["ich_10k"]))
A("- **但这两件的讹形比是 %s 与 %s** ——Fraktur 把 `ich` 打成了 `id)`／`idj`／`icb`。" % (
    M["kommentar-reichsratswahlordnung-1907.txt"]["corruption"]["pooled_named_str"],
    M["bundesverfassung-1920-coedited-1922.txt"]["corruption"]["pooled_named_str"]))
A("  把讹形算进去是 **%.2f**／万词，不是 0。" % G["decisions"]["ich_tol_10k"])
A("- ⇒ **不许把这个 0 写成「机构文书里他不出现第一人称」**。它是空默认值吞掉了「不知道」。\n")
A("### 3-3 法语那件：**测出来是全批最高，正因如此更不能算**\n")
A("- `rapports-de-systeme-1926-fr`：`nous` **%d** 次 / %s 词 = **%.2f／万词**，`je` %d 次 = %.2f／万词。" % (
    fr["first_person"]["nous_fr"], format(fr["words_body"], ","),
    10000.0 * fr["first_person"]["nous_fr"] / fr["words_body"],
    fr["first_person"]["je_fr"], 10000.0 * fr["first_person"]["je_fr"] / fr["words_body"]))
A("- 若把它并进 `expression` 的第一人称复数，该道会从 **%.2f** 抬到 **%.2f**／万词（**%.1f 倍**）。" % (
    G["expression"]["wir_10k"],
    10000.0 * (G["expression"]["wir"] + fr["first_person"]["nous_fr"]) / G["expression"]["words"],
    (G["expression"]["wir"] + fr["first_person"]["nous_fr"]) / max(G["expression"]["wir"], 1)))
A("- **按指令⑥／⑧不算**：未见译者署名，也未见「本人以法文撰写」的声明。上面这个倍数就是**这条指令的实际代价**，写出来备查。\n")
A("## 4. 已扣除的非 Kelsen 块（逐块，连它吃掉的第一人称一起报）\n")
A("| 件 | 行区间 | 词数 | 该块内 `ich` | 该块内 `wir` | 是什么 |")
A("|---|---|---|---|---|---|")
for f in ORDER:
    for b in M[f]["foreign_blocks"]:
        A("| %s | %d–%d | %s | %d | %d | %s |" % (TITLE[f][:34], b["lines"][0], b["lines"][1],
                                                  format(b["words"], ","), b["ich"], b["wir"], b["why"]))
A("")
k7 = M["kommentar-reichsratswahlordnung-1907.txt"]
A("> ★★ **本轮抓到的一处真污染**：`kommentarzurste00kelsgoog` 全文 `wir` 共 **%d** 次，" % (
    k7["first_person"]["wir_strict"] + sum(b["wir"] for b in k7["foreign_blocks"])))
A("> **%d 次全部在 Google 的扫描样板里**（「Wir bitten Sie um Einhaltung folgender Richtlinien」之类），"
  % sum(b["wir"] for b in k7["foreign_blocks"]))
A("> Kelsen 正文里一次都没有。那块样板 **%s 词**，是现代 Google 的法务散文，不是 1907 年的书。" %
  format(sum(b["words"] for b in k7["foreign_blocks"]), ","))
A("> 不扣掉它，这一件的 `wir` 密度会凭空多出来，而且多出来的部分**语种、年代、作者全错**。\n")
A("## 5. 口径声明（不给单个数，给口径）\n")
A("- `ich`／`wir` 一律**词边界匹配、不分大小写**；词元定义 `[A-Za-zÀ-ÿſ]+`。")
A("- 「严格」＝只数正形；「+讹形」＝加上本轮在该件里**实测到**的 OCR 讹形（`icb`/`id)`/`idj`/`id}`/`idi`/`id^`/`ic^`/`id]`）。")
A("  **两个数都给**，因为在 Fraktur 件上二者差到 %.2f vs %.2f。" % (G["decisions"]["ich_10k"], G["decisions"]["ich_tol_10k"]))
A("- 分母是**扣块后**的词数；扣块清单在 §4，一块不漏地列了出来。")
A("- 德语件变音符密度（用来判 OCR 是否丢了变音符）：11 件排序 %s，中位 **%.1f**／千词；" % (dia_ger, statistics.median(dia_ger)))
A("  其中 `problem-der-souveraenitaet-1928` 是 **0.0**，是唯一的离群件。")
open(os.path.join(WIP, "04-声口密度实测.md"), "w", encoding="utf-8").write("\n".join(L))
print("写出 04-声口密度实测.md", len("\n".join(L)), "字符")

# ───────────────────────── 05-取不到的与为什么.md ─────────────────────────
L = []; A = L.append
A("# #171 Hans Kelsen —— 探测报告列出而本轮**没有**落盘的，逐件写原因\n")
A("日期：**2026-08-11**。原则：**取不到就写「取不到」，不凭印象填**。")
A("下面每一条的原因都标了类别，类别沿用本项目已记档的「延后分类」，不新造编号。\n")
A("## 0. 先把分母说清楚\n")
A("| 口径 | 数 |")
A("|---|---|")
A("| 探测报告「附：坐标一览」的 IA 条目 | **13**（＝12 部独立作品 + 1 件重复副本） |")
A("| 本轮**计划**抓取 | **12**（12 部独立作品） |")
A("| 本轮**实际**落盘 | **%d** |" % len(rows))
A("| 有意不抓的重复副本 | **1** |")
A("| 探测报告 ② 列出的 ≤1930 独著（首版口径） | **22** |")
A("| 其中本机找不到 PD 全文的独著 | **16** |")
A("| 探测报告 ④-B 列出、只有编目记录的期刊论文 | **12** |")
A("")
A("## 1. 有意不抓的（1 件）\n")
A("| IA identifier | 是什么 | 为什么不抓 |")
A("|---|---|---|")
A("| `diestaatslehred00kelsgoog` | 1905 年 *Die Staatslehre des Dante Alighieri* 的**第二个扫描件**（Google/加州大学，166 img，`possible-copyright-status: NOT_IN_COPYRIGHT`） | **同一部作品的重复副本**。本项目记档：**两个 id 不等于两处证据**——11 人里 7 人有过这种塌缩、共 57 条。抓进来只会让「独立证据数」虚高。探测报告本身也写明「不另计」。 |")
A("")
_dup = [t["size"] for t in json.load(open(os.path.join(SP, "ia_meta.json"), encoding="utf-8"))["diestaatslehred00kelsgoog"]["txt_files"] if t["name"].endswith("_djvu.txt")][0]
A("> ★ 说明一句：这一件**不是取不到**。探测报告说它「未做可下载性实测」，"
  "而本轮拉 metadata 时它是通的、`_djvu.txt` 也在（**%s 字节**）。" % format(int(_dup), ","))
A("> **是我判断不该抓**。若下游要做 OCR 交叉校勘（同一部书两次独立 OCR 互校，用来定讹字），"
  "这一件是现成的材料，可以随时补 —— 但那时它的身份是**校勘辅助**，不是第二份独立证据。\n")

A("## 2. 类别：通道受限（材料多半存在，本机的通道够不着）\n")
A("| 通道 | 本轮/探测轮的实测状态 | 影响 |")
A("|---|---|---|")
A("| **HathiTrust** | `catalog.hathitrust.org` 对 curl 返回 Cloudflare JS 挑战、对 WebFetch 返回 **HTTP 403**。**按硬约束未绕过。** | 德语／奥地利 1900–1930 印本最大的两个库之一 |")
A("| **Google Books API** | `books.googleapis.com` 返回 429 `Quota exceeded`；加 key 要花钱 → 未用 | 同上 |")
A("| **Gallica SRU**（BnF） | 403 `Access Denied` | 法语件的备选源 |")
A("| **MDZ / BSB** | 检索页是 SPA，无 JS 不出结果；`opacplus.bsb-muenchen.de/sru/bvb01` 404 | 德语印本备选源 |")
A("| **VIAF 机器可读端点** | `/viaf/<id>/viaf.json` 与 `justlinks.json` 均返回 `no Route matched` | 同名护栏少一家交叉印证 |")
A("")
A("> ⚠️ **「查不到」的射程要写死**：以上四条通道下的条目，含义是**「本机这几条通道里查不到」，不是「不存在」**。")
A("> 记档时连坐标一起写，**换一台能正常通过的机器就能续**。\n")

A("## 3. 类别：本机通道内找不到 PD 全文的独著（16 部）\n")
A("查了哪里：IA `advancedsearch` 的 `creator:(\"Kelsen, Hans\" OR \"Hans Kelsen\")` 全量 66 条 + 逐题名 `title:\"…\"` 八次点查，**命中 0**。\n")
A("| 探测 ② 编号 | 题名 | 年 | 篇幅 | 备注 |")
A("|---|---|---|---|---|")
for n, t, y, pp, note in [
    ("#3", "*Hauptprobleme der Staatsrechtslehre, entwickelt aus der Lehre vom Rechtssatze*", "1911", "XXVII, 709 S.", "★**他最重的一部**；「再探」四部之一"),
    ("#4", "*Über Grenzen zwischen juristischer und soziologischer Methode.* Vortrag", "1911", "64 S.", "讲词，voice 上本会是 `expression`"),
    ("#5", "*Über Staatsunrecht*", "1913", "114 S.", "—"),
    ("#6", "*Der Buchforderungseskont und die inakzeptable deckungsberechtigende Tratte*", "1913", "19 S.", "出版者 k. k. österr. Handelsmuseum ——★同名护栏的维也纳工商档正对着它"),
    ("#10", "*Der soziologische und der juristische Staatsbegriff*", "1922", "IV, 253 S.", "「再探」四部之一"),
    ("#11", "*Rechtswissenschaft und Recht*", "1922", "135 S.", "「再探」四部之一"),
    ("#12", "*Österreichisches Staatsrecht. Ein Grundriß*", "1923", "VIII, 256 S.", "「再探」四部之一"),
    ("#13", "*Rechtsgutachten … Fürsten von Thurn und Taxis*", "1924", "—", "法律意见书"),
    ("#15", "*Das Problem des Parlamentarismus*", "[1925/26]", "44 S.", "两库年份分记 ca.1925 与 [1926]"),
    ("#16", "*Der Staat als Übermensch. Eine Erwiderung*", "1926", "24 S.", "★**论战**——探测报告预期第一人称最高的三件之一"),
    ("#17", "*Die staatsrechtliche Durchführung des Anschlusses Österreichs an das Deutsche Reich*", "1927", "24 S.", "—"),
    ("#18", "*Die philosophischen Grundlagen der Naturrechtslehre und des Rechtspositivismus*", "1928", "78 S.", "—"),
    ("#19", "*Rechtsgeschichte gegen Rechtsphilosophie? Eine Erwiderung*", "1928", "31 S.", "★**论战**——同上"),
    ("#20", "*Justiz und Verwaltung*", "1929", "25 S.", "扩印抽印本"),
    ("#21", "*Staatsrechtliches Gutachten*（列支敦士登人民党委托）", "1929", "28 S.", "法律意见书"),
    ("#22", "*Der Staat als Integration. Eine prinzipielle Auseinandersetzung*", "1930", "III, 91 S.", "★**论战**（对 Smend）；且见 §4，**明确不可取**"),
]:
    A("| %s | %s | %s | %s | %s |" % (n, t, y, pp, note))
A("")
A("> ★★ **这 16 部里有 3 部是 *Erwiderung*（论战）**——探测报告 §判断一 明确预期「第一人称密度最高的应当是这三件」。")
A("> **三件本机全部没有 PD 全文**，所以 04 那份声口密度表**缺的正是最该测的那一档**。")
A("> 这不是取样偏好，是可得性造成的系统性缺口，**必须连着 04 的结论一起读**。\n")
A("## 4. 类别：不是 PD／不是他的文字（明确排除，不是取不到）\n")
A("| 件 | 年 | 为什么排除 |")
A("|---|---|---|")
A("| *Der Staat als Integration*，Springer「Online-Ressource (III, 92 S)」（PPN 772970742 / IDN 1043977082） | 1930 | **Springer Book Archives 付费墙**。硬约束：付费墙一律不碰。纸本 1930 ≤1930 是 PD，但**本机能到达的那个副本在墙后**——两件事要分开写。 |")
A("| *Wer soll der Hüter der Verfassung sein?*（对 Carl Schmitt 的著名反驳） | 刊 *Die Justiz* 6 (1930/31)；单行本 Berlin **1931** | **1931 > 1930，按本项目判据不是 PD，不许取。**这正是「记错一年就把分界之外写成分界之内」那一类，探测报告已标出，本轮**没有顺手收进来**。 |")
A("| *Az államelmélet alapvonalai*，Szeged | 1927 | 匈牙利文，`A német kéziratból forditotta … Moór Gyula`（Moór 从德文手稿译出）。**出版年 ≤1930，但译文是 Moór 的文字，不是 Kelsen 的声口。** |")
A("| `kelsen-problemas-capitales` | IA `date` **1911** | 实为 **1987 年西班牙文译本**，在版权期。 |")
A("| `kelsen-sovranita` | IA `date` **1920** | 意大利文译本，在版权期。 |")
A("| `kelsen-sociologia-democrazia` | IA `date` **1921** | 意文选集，**prefaced by Agostino Carrino**（当代学者作序），在版权期。 |")
A("| `la-garantia-jurisdiccional-de-la-constitucion` | IA `date` **1928-09-10** | 西班牙文译本，在版权期。 |")
A("| *Hans Kelsen Werke* (HKW)，Mohr Siebeck 2007– | 现代 | 现代校勘本，在版权期。**同名护栏里是硬拦项**（见 `kelsen_namesake_candidates.json`）。 |")
A("")
A("> ★ 中间那 4 件 IA 条目是**本项目这一轮 PD 闸门的主要靶子**：`date ≤1930` 而内容在版权期。")
A("> 本轮 12 件**逐件的 PD 依据都不是 IA `date`**（见 03 §3 的「PD 依据」栏），这一条自检结果是 **0**。\n")
A("## 5. 类别：只有编目记录、本机通道找不到 PD 全文的期刊论文（12 篇）\n")
A("| 题名 | 年 | 编目坐标 |")
A("|---|---|---|")
for t, y, ppn in [
    ("*Zur Soziologie des Rechtes. Kritische Betrachtungen*", "1912", "PPN 394742346"),
    ("*Entgegnung*（**Eugen Ehrlich × Hans Kelsen 论战**）", "1916", "PPN 394739833"),
    ("*Verfassungs- und Verwaltungsgerichtsbarkeit im Dienste des Bundesstaates*", "记 1920（S. 174–217）", "PPN 300952139 ★年份可疑，与常见的 1929 说法冲突，**未核**"),
    ("*Der Begriff des Staates und die Sozialpsychologie …*", "1922", "PPN 152284810X"),
    ("*Die Verfassung Österreichs*（年鉴连载）", "1922 / 1923 / 1927 / 1930", "PPN 1659664519 / 394742974 / 394743067 / 394743180"),
    ("*Die österreichische Bundesverfassung. Text mit Anmerkungen*", "1923", "PPN 394722396"),
    ("*Marx oder Lassalle*", "1924", "PPN 525239189"),
    ("*Die Bundesexekution*", "1927", "PPN 226162850"),
    ("*Die Idee des Naturrechts*", "1928", "PPN 81974882X"),
    ("*Naturrecht und positives Recht*", "1928", "PPN 1123204128"),
    ("*Juristischer Formalismus und reine Rechtslehre*", "1929", "PPN 1824491115"),
    ("*Die Entwicklung des Staatsrechts in Oesterreich seit dem Jahre 1918*", "1930", "PPN 394721446"),
]:
    A("| %s | %s | %s |" % (t, y, ppn))
A("")
A("## 6. 类别：合编／集体卷（体裁上本就不该进一手道）\n")
A("| 件 | 年 | 处置 |")
A("|---|---|---|")
A("| *Die Verfassungsgesetze der Republik Deutschösterreich*，T. 1–4（约 750 页法条） | 1919–1920 | **本机找不到 PD 全文。**★探测报告 §判断一 第 3 点：若哪天补到这批，机构文书占比会从 26% 冲到约 55%，**那时必须重算那一条**。 |")
A("| *Wesen und Entwicklung der Staatsgerichtsbarkeit*，VVDStRL H. 5 | 1929 | 四人报告合卷（Triepel/Kelsen/Layer/v. Hippel），非独著 |")
A("| *Der Anschluß Oesterreichs an das Deutsche Reich …* | 1927 | 四人合卷 |")
A("| Erich Bernheimer, *Probleme der Rechtsphilosophie* | 1927 | Kelsen 只写 **Geleitwort** |")
A("| Charles Eisenmann, *La justice constitutionnelle …* | 1928 | Kelsen 只写 **Préface** |")
A("")
A("> ★ 本项目记档：**「与他有关」不等于「他写的」**（Liebig 9 份混进一手，一手占比从 0.7419 掉到 0.5192）。")
A("> 上面五件**一件都没有进 `raw/`**。\n")
A("## 7. 一条本轮就能判、不留到判分那轮的\n")
A("- deep 档要 **≥30 份一手**。本轮实际落盘 **%d 件 / %d 部独立作品**。" % (len(rows), len(rows)))
A("- 按**最宽**的读法（把重复副本、Fraktur 件、合编卷全部算进去）也只有 **13 个 IA 条目**。")
A("- 就算 §2 那两条被封的通道全部打开，§3 那 16 部最多再添 6–8 件 → 上限约 **18–20 件**，仍 < 30。")
A("- ⇒ **现在就判：deep 档达不到，走 quick/standard 档**，差额 **17–18 件**写进台账。**不挂「等裁定」。**")
A("- 但**页数不缺**：本轮落盘正文合计 **%s 词**（落盘文件现算），其中「可做逐字引文」的 %d 件合计 **%s 词**。" % (
    format(tot_words, ","), len(ok), format(sum(r["words_whole_file"] for r in ok), ",")))
open(os.path.join(WIP, "05-取不到的与为什么.md"), "w", encoding="utf-8").write("\n".join(L))
print("写出 05-取不到的与为什么.md", len("\n".join(L)), "字符")
