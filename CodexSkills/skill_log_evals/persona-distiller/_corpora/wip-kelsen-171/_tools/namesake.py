#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#171 Kelsen 同名护栏：产出 kelsen_namesake_candidates.json，并**当场对自己跑正反对照**。
设计依据 = 01-可得性探测.md ⑤-D 的五条 + 02-九条 的第 ④ 条。
"""
import json, os, re

OUT = ("/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/"
       "skill_log_evals/persona-distiller/_corpora/wip-kelsen-171/kelsen_namesake_candidates.json")

# ── 匹配规则（写死在产物里，谁都能复算）──────────────────────────────
# 1) 姓名位：词边界 + 两种语序 + **规范档登记的全部变体拼法**
#    ★ v1 只收 Hans Kelsen / Kelsen, Hans，自测当场打红：9 条必须放行的负对照
#      全部「全名位未命中」。那与「把 H. Kelsen 当排除词」净效果相同——
#      本人的材料照样进不来。变体名一律**收进识别位**（不是排除位）。
NAME_FORMS = [
    r"Hans\s+Kelsen", r"Kelsen,\s*Hans",
    r"Kelsen,\s*H\.", r"H\.\s*Kelsen",   # GND 400（★本人变体，绝不当排除词）；正序写法同收
    r"Kelsen,\s*Frantisek",        # GND 400
    r"Kelzen,\s*Hans", r"Keruzen,\s*Hansu", r"Qelzen,\s*Hans",  # GND 400
    r"Κέλσεν,\s*Χανς",             # GND 400 $9 U:Grek
    r"Kel[ʹ']zen,\s*Gans",         # LCCN n50045680 variantLabel (und-latn)
    r"קלזן,\s*הנס",                 # LCCN n50045680 variantLabel (und-hebr)
    r"K[ʻ']o-lu-sun",              # LCCN n50045680 variantLabel（中文罗马化）
]
NAME_RE = r"(?<![A-Za-zÀ-ÿ])(?:%s)(?![a-zà-ÿ])" % "|".join(NAME_FORMS)
# 2) 判别位：生卒 或 规范档号（三元组的后两元，命中任一即可）
DISCRIM_RE = r"(?<![0-9])1881(?![0-9])[^\n]{0,40}(?<![0-9])1973(?![0-9])|118561219|n\s?50045680"
# 3) 硬拦：现代校勘本 —— 名字与目标完全一致，最像一手件
HARD_BLOCK_RE = r"(?<![A-Za-zÀ-ÿ])(?:Hans[\s\-]Kelsen[\s\-]Institut|Hans[\s\-]Kelsen[\s\-]Werke|HKW)(?![A-Za-zÀ-ÿ])"
# 4) ★ 不许用 `H. Kelsen` 做排除词——它是本人的 GND 400 变体名
FORBIDDEN_AS_EXCLUSION = ["H. Kelsen", "Kelsen, H.", "Kelsen H"]
# 5) 姓氏位匹配对巴西的「名＝Kelsen」无效 → 名位也要扫
GIVEN_NAME_KELSEN_RE = r"(?<![A-Za-zÀ-ÿ])Kelsen\s+[A-ZÀ-Þ][a-zà-ÿ]+"
# 6) 1900–1913 维也纳工商类 → 只比姓一律升级为「核全称」
VIENNA_TRADE_ESCALATE = {
    "year_range": [1900, 1913],
    "trigger_terms": ["Wien", "Vienna", "Handelsmuseum", "Handelskammer", "Lampen", "Fabrik",
                      "Firma", "Gewerbe", "Adressbuch", "Lehmann"],
    "action": "不许只比姓；必须读出作者全称，与 Adolf Kelsen (1850-1907, GND 137731892, Lampenfabrikant) 分开",
}


def judge(s):
    """
    ★ 三值，不是两值：target / not_target / undecided。
    「全名命中但判别位缺」是**不知道**，不是**不是他**——
    判成 not_target 就等于用空默认值吞掉不知道（本项目记档过的事故形态）。
    """
    if re.search(HARD_BLOCK_RE, s, re.I):
        return "not_target", "hard_block(现代校勘本 HKW / Kelsen-Institut)"
    if not re.search(NAME_RE, s):
        return "not_target", "姓名位（含 11 种规范档变体）未命中"
    if not re.search(DISCRIM_RE, s):
        return "undecided", "姓名位命中、判别位（1881–1973 / GND 118561219 / LCCN n50045680）缺 → 必须人工核全称，不许默认放过或默认排除"
    return "target", "三元组齐"


def is_target(s):
    v, r = judge(s)
    return v == "target", r


# ── 必须放行的负对照（本轮从规范档现取，不抄探测报告）───────────────
MUST_PASS = [
    {"s": "Kelsen, Hans, 1881-1973", "src": "GND 118561219 $100a$d / LCCN n50045680 authoritativeLabel"},
    {"s": "Kelsen, H., 1881-1973", "src": "GND 400 ——★本人变体名，绝不许当排除词"},
    {"s": "Kelsen, Frantisek, 1881-1973", "src": "GND 400"},
    {"s": "Kelzen, Hans, 1881-1973", "src": "GND 400"},
    {"s": "Keruzen, Hansu, 1881-1973", "src": "GND 400"},
    {"s": "Qelzen, Hans, 1881-1973", "src": "GND 400"},
    {"s": "Κέλσεν, Χανς, 1881-1973", "src": "GND 400 $9 U:Grek"},
    {"s": "Kelʹzen, Gans, 1881-1973", "src": "★本轮新取：LCCN n50045680 variantLabel (und-latn)，探测报告未列"},
    {"s": "קלזן, הנס, 1881-1973", "src": "★本轮新取：LCCN n50045680 variantLabel (und-hebr)，探测报告未列"},
    {"s": "Kʻo-lu-sun, 1881-1973", "src": "★本轮新取：LCCN n50045680 variantLabel（中文罗马化），探测报告未列"},
    {"s": "Hans Kelsen (GND 118561219)", "src": "只给规范档号、不给生卒的写法"},
    {"s": "Hans Kelsen, LCCN n50045680", "src": "只给 LCCN 的写法"},
]

# ── 必须拦住的正例 ─────────────────────────────────────────────
MUST_BLOCK = [
    {"s": "Hans Kelsen-Institut, Wien", "why": "现代校勘机构（LCCN n83039512 / Q135652732）"},
    {"s": "Hans Kelsen Werke, Bd. 3, Mohr Siebeck 2010", "why": "HKW 现代校勘本，在版权期，最像一手件"},
    {"s": "HKW 5, hrsg. vom Hans Kelsen-Institut", "why": "缩写形态"},
    {"s": "Kelsen, Adolf, 1850-1907", "why": "父亲，Lampenfabrikant，GND 137731892；同姓同城，卒年落在他前两部书之间"},
    {"s": "Kelsen Dantas Eulálio", "why": "巴西，Kelsen 是**名**不是姓（Q96646133）——姓氏位匹配对它无效"},
    {"s": "Kelsen DE Oliveira Teixeira", "why": "同上（Q95269382）"},
    {"s": "Sylvio Kelsen Coelho", "why": "巴西，Kelsen 是中名（LCCN n2024253062）"},
    {"s": "K̇elsengdongrub", "why": "纯子串碰撞（LCCN no2024137962）——不加词边界必中"},
    {"s": "David P. Kelsen, Gastrointestinal oncology, 2002", "why": "美国肿瘤科医师 LCCN n86148559"},
    {"s": "Irene Kelsen, Victorian law of real estate", "why": "★同为法律著作者（OL13477572A），题材筛不掉"},
    {"s": "Keith Kelsen, Unleashing the power of digital signage", "why": "LCCN n2009069881"},
    {"s": "Judith R. Kelsen", "why": "LCCN n2024180963"},
    {"s": "Dominique Kelsen (1895-1945)", "why": "卢森堡足球运动员 Q16568780"},
    {"s": "Pierre Kelsen", "why": "卢森堡篮球运动员 Q49970641"},
    {"s": "Hanna Renate Kelsen, 1914-2001", "why": "Hans Kelsen 之女 Q113633781"},
    {"s": "Kelsen Familie", "why": "GND 13725945X，家族项不是人"},
    {"s": "Kelsen Group / Kelsen Arts", "why": "公司名 Q115864759 / Q139498739"},
    {"s": "Kelsenstraße, Linz", "why": "地名 Q134309783"},
    {"s": "Kelsenova, Praha", "why": "地名 Q43388234"},
    {"s": "Adolf Kelsen, Lampenfabrik, Wien 1905", "why": "★1900–1913 维也纳工商类，必须升级核全称"},
    {"s": "Brent Kelsen", "why": "GND 171752449 / Q89913885"},
]

# ── 24 位「Hans Kelsen 之外」的自然人 + 6 项非自然人（来源：01 探测 ⑤）──
CANDIDATES = [
    # (name, dates, role, authority, evidence_level, verified_this_round)
    ("Adolf Kelsen", "1850-06-06 – 1907-07-12", "奥地利灯具制造商（GND 550: Unternehmer；678: Lampenfabrikant）；Wikidata P40 直指 Q84165 —— 目标人物之父",
     "GND 137731892; VIAF 81878324; Q55853330", "high",
     "是——本轮直查 DNB SRU WOE=137731892，100$a『Kelsen, Adolf』$d1850-1907、678$b『Lampenfabrikant』逐字取回"),
    ("Brent Kelsen", "—", "—", "GND 171752449; Q89913885", "medium", "否（沿用探测报告）"),
    ("Dominique Kelsen", "1895-01-18 – 1945-11-14", "卢森堡足球运动员", "Q16568780", "medium", "否"),
    ("Pierre Kelsen", "生 1950", "卢森堡篮球运动员", "Q49970641", "medium", "否"),
    ("Pierre Kelsen（第二实体）", "—", "未核是否与上一条重复", "Q102197062", "low", "否"),
    ("Broche Kelsen", "1858-03-15 – 1943-02-01", "—", "Q105355395", "low", "否"),
    ("Hanna Renate Kelsen", "1914-11-23 – 2001-06-02", "Hans Kelsen 之女（Q84165 P40 指向她）", "Q113633781", "medium", "否"),
    ("（Q115004308）", "—", "Hans Kelsen 另一子女", "Q115004308", "low", "否"),
    ("Léa Kelsen", "生 1997", "—", "Q126367617", "low", "否"),
    ("David (P./Paul) Kelsen", "1984–2002+", "美国肿瘤科医师，Memorial Sloan-Kettering；著 Gastrointestinal oncology (2002)", "LCCN n86148559", "high", "否"),
    ("Judith R. Kelsen", "2022", "儿科消化科医师，费城儿童医院", "LCCN n2024180963", "medium", "否"),
    ("Keith Kelsen", "2010", "著 Unleashing the power of digital signage", "LCCN n2009069881", "medium", "否"),
    ("Sylvio Kelsen Coelho", "2020", "巴西；**Kelsen 是中名**；著 Empresas estatais", "LCCN n2024253062", "high", "否"),
    ("Kelsen Dantas Eulálio / Kelsen DE Oliveira Teixeira", "当代", "巴西研究者；**Kelsen 是名不是姓**", "Q96646133 / Q95269382", "high", "否"),
    ("Irene Kelsen", "生 1915", "★同为法律著作者：Victorian law of real estate", "OL13477572A（无规范档）", "medium", "否"),
    ("Emma Kelsen", "—", "—", "OL10982604A", "low", "否"),
    ("Kate Kelsen", "—", "—", "OL14436542A", "low", "否"),
    ("Don Kelsen", "—", "—", "OL9323424A", "low", "否"),
    ("Michael Robert Kelsen", "—", "—", "OL15070028A", "low", "否"),
    ("D. Kelsen", "—", "著 Magenkarzinom", "OL3333664A", "low", "否"),
    ("Kelsen Jacobs", "—", "Kelsen 是名", "OL14271769A", "low", "否"),
    ("Jens Kelsen", "—", "IA/PubMed 条目", "—", "low", "否"),
    ("Jesper Kelsen", "—", "IA/PubMed 条目", "—", "low", "否"),
    ("Angel Kelsen Arbaiza", "—", "IA 条目", "—", "low", "否"),
]
NON_PERSONS = [
    ("Hans Kelsen-Institut", "LCCN n83039512; Q135652732", "★本轮最大污染源：它编的 Hans Kelsen Werke (HKW) 是现代校勘本、在版权期，而书名与作者名与目标完全一致"),
    ("Hans Kelsen Werke (HKW)", "Q116111193; Mohr Siebeck, 2007–", "现代校勘本，在版权期"),
    ("Kelsen Familie", "GND 13725945X", "家族项，不是人，但会命中姓名匹配"),
    ("K̇elsengdongrub", "LCCN no2024137962（蒙文，1945）", "纯子串碰撞 K̇elsen|gdongrub，naive contains(\"Kelsen\") 必中"),
    ("Kelsen（德国聚落）/ Kelsenstraße（林茨）/ Kelsenova（布拉格）", "Q1437153 / Q134309783 / Q43388234", "地名子串"),
    ("Kelsen Group / Kelsen Arts", "Q115864759 / Q139498739", "公司名"),
]


MUST_UNDECIDED = [
    {"s": "Hans Kelsen", "why": "只有名字、没有生卒也没有规范档号 —— 判『不是他』和判『是他』都是编的"},
    {"s": "H. Kelsen, Reine Rechtslehre", "why": "★本人变体名的正序写法，无判别位；判成 not_target 就等于把他自己挡了"},
    {"s": "Kelsen, H.", "why": "GND 400 变体名，无判别位"},
    {"s": "Kelsen, Hans, Wien 1907", "why": "有年份但不是生卒 → ★1900–1913 维也纳档，必须升级核全称（父亲 Adolf Kelsen 卒于 1907）"},
]


def main():
    # ── 自测：正例必须被拦，负对照必须放行，判别位缺的必须落在 undecided ──
    #    ★ 三侧用的是同一个 judge()，不是三把尺子
    blocked = [dict(s=b["s"], why=b["why"], verdict=judge(b["s"])[0], reason=judge(b["s"])[1]) for b in MUST_BLOCK]
    passed = [dict(s=m["s"], src=m["src"], verdict=judge(m["s"])[0], reason=judge(m["s"])[1]) for m in MUST_PASS]
    undec = [dict(s=u["s"], why=u["why"], verdict=judge(u["s"])[0], reason=judge(u["s"])[1]) for u in MUST_UNDECIDED]
    fp = [b for b in blocked if b["verdict"] != "not_target"]   # 该拦没拦
    fn = [m for m in passed if m["verdict"] != "target"]        # 该放没放
    fu = [u for u in undec if u["verdict"] != "undecided"]      # 该存疑却给了定论

    # ── 对本轮真落盘的 12 件跑一遍（护栏必须放行它们）──
    raw = os.path.join(os.path.dirname(OUT), "raw")
    corpus = []
    for d in sorted(os.listdir(raw)):
        p = os.path.join(raw, d)
        if not os.path.isdir(p):
            continue
        src = json.load(open(os.path.join(p, "SOURCE.json"), encoding="utf-8"))
        txt = [f for f in os.listdir(p) if f.endswith(".txt")][0]
        t = open(os.path.join(p, txt), encoding="utf-8", errors="replace").read()
        corpus.append({
            "src_dir": d, "file": txt,
            "hard_block_hits": len(re.findall(HARD_BLOCK_RE, t, re.I)),
            "given_name_kelsen_hits": len(re.findall(GIVEN_NAME_KELSEN_RE, t)),
            "fullname_hits_in_text": len(re.findall(NAME_RE, t)),
            "ia_creator_field": src.get("ia_creator_field"),
            "creator_field_verdict": judge(str(src.get("ia_creator_field")))[0],
            "creator_field_reason": judge(str(src.get("ia_creator_field")))[1],
        })

    # ── 变异测试：逐条改坏护栏，看自测会不会打红。不红＝我的测试集覆盖不到它 ──
    import unicodedata as _ud
    g_name, g_hard, g_disc = NAME_RE, HARD_BLOCK_RE, DISCRIM_RE

    def _run(nr, hr, dr):
        def j(s):
            if re.search(hr, s, re.I): return "not_target"
            if not re.search(nr, s):   return "not_target"
            if not re.search(dr, s):   return "undecided"
            return "target"
        return (sum(1 for b in MUST_BLOCK if j(b["s"]) != "not_target"),
                sum(1 for m in MUST_PASS if j(m["s"]) != "target"),
                sum(1 for u in MUST_UNDECIDED if j(u["s"]) != "undecided"))

    base = _run(g_name, g_hard, g_disc)
    muts = [
        ("M1 去掉尾部词边界", g_name.replace("(?![a-zà-ÿ])", ""), g_hard, g_disc),
        ("M2 去掉首部词边界", g_name.replace("(?<![A-Za-zÀ-ÿ])", ""), g_hard, g_disc),
        ("M3 姓名位退化成只比姓 Kelsen", r"(?<![A-Za-zÀ-ÿ])Kelsen(?![a-zà-ÿ])", g_hard, g_disc),
        ("M4 拆掉硬拦 HKW/Kelsen-Institut", g_name, r"(?!x)x", g_disc),
        ("M5 判别位放宽成『有 4 位数年份即可』", g_name, g_hard, r"\d{4}"),
        ("M6 判别位收紧成只认 GND", g_name, g_hard, r"118561219"),
        ("M7 把 H. Kelsen 从识别位删掉（＝指令禁止的那种做法）",
         r"(?<![A-Za-zÀ-ÿ])(?:%s)(?![a-zà-ÿ])" % "|".join(f for f in NAME_FORMS if "H\\." not in f), g_hard, g_disc),
        ("M3+M1 只比姓 ∧ 无词边界", r"Kelsen", g_hard, g_disc),
    ]
    mut_rows = []
    for label, nr, hr, dr in muts:
        r = _run(nr, hr, dr)
        d = [r[i] - base[i] for i in range(3)]
        mut_rows.append({"mutation": label, "delta_block_leak": d[0], "delta_pass_lost": d[1],
                         "delta_wrong_verdict": d[2], "went_red": any(d)})

    # ★ 归一化实验：探测报告 ⑤-C 说 naive contains("Kelsen") 对 K̇elsengdongrub「必中」
    _k = "K̇elsengdongrub"
    _folded = "".join(c for c in _ud.normalize("NFD", _k) if not _ud.combining(c))
    norm_probe = {
        "string": _k, "codepoints_head": [hex(ord(c)) for c in _k[:4]],
        "naive_contains_Kelsen_raw": "Kelsen" in _k,
        "naive_contains_Kelsen_after_diacritic_folding": "Kelsen" in _folded,
        "surname_match_with_word_boundary_after_folding":
            bool(re.search(r"(?<![A-Za-zÀ-ÿ])Kelsen(?![a-zà-ÿ])", _folded)),
        "finding": ("★ 探测报告 ⑤-C 写的『naive contains(\"Kelsen\") 必中』**未归一化时不成立**："
                    "K 与 e 之间夹着组合符 U+0307，原串里根本没有 `Kelsen` 这个子串。"
                    "只有上游做过去组合符/折叠（多数检索管道会做）它才会中——"
                    "那时词边界确实是唯一挡住它的东西。结论方向没错，触发条件报告里漏了一步。"),
    }

    doc = {
        "person": "Hans Kelsen",
        "life_dates": "1881-10-11 – 1973-04-19（GND 548 datx『11.10.1881-19.04.1973』）",
        "life_dates_dispute": ("★ 死亡日两说：GND 记 19.04.1973、Wikidata preferred 记 1973-04-19；"
                               "而 **LCCN n50045680 的 deathDate 字段本轮直查是 1973-04-20**，Wikidata normal-rank 亦为 04-20。"
                               "→ 01-可得性探测.md §① 写的『GND 与 LCCN 都记 4-19』**在 LCCN 一侧不成立**，本轮已改记为 2 对 2。"
                               "对护栏无影响（护栏只用到年份 1881–1973）。"),
        "authority_ids": {"GND": "118561219", "LCCN": "n50045680", "Wikidata": "Q84165",
                          "VIAF": "31998356（★未在 VIAF 侧核过：机器可读端点不可达，见探测 §0）"},
        "generated": "2026-08-11",
        "rule": {
            "triple": "全名位 ∧ （生卒 1881–1973 ∨ GND 118561219 ∨ LCCN n50045680）",
            "name_regex": NAME_RE,
            "discriminator_regex": DISCRIM_RE,
            "hard_block_regex": HARD_BLOCK_RE,
            "given_name_kelsen_regex": GIVEN_NAME_KELSEN_RE,
            "forbidden_as_exclusion_term": FORBIDDEN_AS_EXCLUSION,
            "forbidden_reason": "`H. Kelsen` / `Kelsen, H.` 是本人的 GND 400 变体名；拿它当排除词会把目标人物本人挡掉",
            "word_boundary": "所有子串匹配带 (?<![A-Za-zÀ-ÿ]) / (?![A-Za-zÀ-ÿ]) 词边界，否则 K̇elsengdongrub 必中",
            "surname_position_invalid_for": "巴西的『名＝Kelsen』（Kelsen Dantas Eulálio / Kelsen DE Oliveira Teixeira / Sylvio Kelsen Coelho）——姓氏位匹配对它们无效，必须另扫名位",
            "vienna_trade_escalation": VIENNA_TRADE_ESCALATE,
        },
        "self_test": {
            "must_block": blocked, "must_pass": passed, "must_be_undecided": undec,
            "false_positive_count": len(fp), "false_negative_count": len(fn), "wrong_undecided_count": len(fu),
            "false_positives": fp, "false_negatives": fn, "wrong_undecided": fu,
            "verdict": "PASS" if not fp and not fn and not fu else "FAIL",
            "note": ("★ 三侧用的是同一个 judge()，不是三把尺子（本项目记档：判据方向反了、两侧同跑一把尺才查出来）。"
                     "★★ 本护栏第一版自测就打红：11 种规范档变体名里有 9 种『姓名位未命中』——"
                     "我没有把 `H. Kelsen` 写进排除词，但**没写进识别位**的净效果一样是把本人挡在外面。"
                     "指令只禁止了前一种写法，后一种是自测抓出来的。"),
        },
        "mutation_test": {
            "why": ("绿了不等于起作用——本项目记档：切错位置的判据照样能在两个状态间给出不同答案。"
                    "所以逐条把护栏改坏，看自测会不会打红。"),
            "baseline": {"block_leak": base[0], "pass_lost": base[1], "wrong_verdict": base[2]},
            "rows": mut_rows,
            "covered": [m["mutation"] for m in mut_rows if m["went_red"]],
            "NOT_covered": [m["mutation"] for m in mut_rows if not m["went_red"]],
            "honest_note": ("★ M1/M2（词边界）单独改坏时自测**不打红**——因为本护栏用的是全名匹配，"
                            "词边界在当前形态下不是承重件。它只有在护栏退化成『只比姓』时才承重："
                            "M3+M1 一起改才漏。**不许据此宣称『词边界已验过』**，只能说："
                            "当前形态下它是冗余防线，一旦有人把匹配放宽到姓氏位，它立刻变成唯一那道。"),
        },
        "unicode_normalization_probe": norm_probe,
        "run_against_this_round_corpus": {
            "n_items": len(corpus),
            "hard_block_hits_total": sum(c["hard_block_hits"] for c in corpus),
            "given_name_kelsen_hits_total": sum(c["given_name_kelsen_hits"] for c in corpus),
            "items": corpus,
            "note": ("★ 『0 次拦截』与『没跑』打印出来是同一个 0（本项目记档），所以这里连**分母**一起给："
                     "12 件全部真跑过，硬拦命中 0、名位 Kelsen 命中 0。"
                     "另注：本轮 12 件是**按给定 IA identifier 直取**的，不走检索路径 —— "
                     "护栏在这条通道上本来就没有拦截机会，这个 0 只证明『没有污染混进来』，不证明『护栏有效』；"
                     "护栏的有效性由上面的 self_test 正反对照证明。"),
        },
        "candidates": [
            {"name": n, "dates": d, "role": r, "authority": a, "evidence_level": e,
             "verified_this_round": v, "identity_category": "namesake"}
            for (n, d, r, a, e, v) in CANDIDATES
        ],
        "non_person_entities": [
            {"name": n, "authority": a, "why_dangerous": w} for (n, a, w) in NON_PERSONS
        ],
        "provenance": {
            "候选清单来源": "01-可得性探测.md ⑤（Wikidata SPARQL + wbsearchentities 七语种 + GND SRU + LC suggest2 + OpenLibrary + IA creator）",
            "本轮独立复核的": ["GND 118561219 的 100/400/548 字段（DNB SRU，MARC21）",
                          "GND 137731892 Adolf Kelsen（同上）",
                          "LCCN n50045680 的 variantLabel / birthDate / deathDate（id.loc.gov JSON）"],
            "本轮未复核、沿用探测报告的": "其余 22 位自然人与 6 项非自然人的标识符",
        },
    }
    json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("self_test:", doc["self_test"]["verdict"], "| 该拦没拦", len(fp), "| 该放没放", len(fn), "| 该存疑却给定论", len(fu))
    for x in fp: print("  该拦没拦:", x["s"], "->", x["verdict"], "|", x["reason"])
    for x in fn: print("  该放没放:", x["s"], "->", x["verdict"], "|", x["reason"])
    for x in fu: print("  该存疑:", x["s"], "->", x["verdict"], "|", x["reason"])
    print("  三侧样本数：拦 %d / 放 %d / 存疑 %d" % (len(blocked), len(passed), len(undec)))
    print("语料侧：硬拦命中", doc["run_against_this_round_corpus"]["hard_block_hits_total"],
          "／名位 Kelsen 命中", doc["run_against_this_round_corpus"]["given_name_kelsen_hits_total"],
          "／分母", len(corpus))
    print("->", OUT)


if __name__ == "__main__":
    main()
