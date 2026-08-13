#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flag_borrowed_voice.py —— 标记「这一句的第一人称可能不是本人」

## 为什么有这件工具

2026-08-12，第 1 批 10 人写研究道时，**同一个错误出现了 5 次、4 种机制**：

| 机制 | 实例 | 「我」实际是谁 |
|---|---|---|
| ① 传记转录传主书信 | Marshall《华盛顿传》 | **华盛顿** |
| ② 小说角色对白 | Pestalozzi《Lienhard und Gertrud》 | 他**虚构的人物** |
| ③ 校勘者／编者序言 | Kant 1867/1868/1889 编本 | **校订者** |
| ④ 图书馆数字化声明 | Jefferson 一份 P1 源 | **图书馆** |
| ⑤ **落在一段未闭合的引语里** | Brandeis《Other people's money》 | **尤蒂卡审计官 Reusswig** |
| ⑥ **听证／庭审转录里的证人** | Brandeis《Scientific management and railroads》 | **证人 Henry R. Towne** |

★ Marshall 最严重：`writings` 道 **10 条候选 10 条**都是华盛顿的话，
而**三道现有的门（来源数／道数／一手占比）一道都不会因此变红**——
门数的是来源，不问那些第一人称属于谁。

★★ ⑤⑥ 是 2026-08-13 Brandeis #172 实测补的，**代价已量清**：
本工具对他 `writings` 道 14 条候选**只标出 1 条**，而逐条读前 700 字核出
**9 条不是他**（Reusswig 3、Towne 3、North 法官 1、Fisher 1、工厂主 1）——
**漏检 8/9**。两条新机制补上后：命中 9/9、**误伤本人 0/5**。

⑥ 这一条尤其是 [[a-checker-nothing-calls-is-not-a-checker]] 的形态：
听证体的说话人标记检测**早就写在 `measure_voice.py` 里**（`SPEAKER_TAG`），
只是从没接进这里。而 ② 原有的 `SPEAKER_LABEL` 够不到它，有两个原因，
**两个都得改**：正则要求「首字母大写、其余小写」而 OCR 出来是 `Mr. TowNE.`；
窗口只看命中前 90 字，而听证里一个人的一段回答动辄两三千字
（实测最近的标记在命中前 **1357／2528／1359** 字）。

## 本工具**不判断**

它只做一件事：**把可疑的理由连同原文证据一起打印出来**，由人判。
理由必须能在正文里指出位置——不打印「疑似对白」，只打印命中的那几个词和它的偏移。

## 用法

    python3 pull_quotes.py --raw R --ledger L --lane writings --lang de --first-person \\
      | python3 flag_borrowed_voice.py --raw R --ledger L

    python3 flag_borrowed_voice.py --self-test        # 正负对照，跑真语料

退出码：0＝没有「高」级标记；3＝有「高」级标记（需人判）；4＝读不到正文；**5＝自测跳过（语料不在本树）**
"""
import argparse
import json
import pathlib
import re
import sys

WS = re.compile(r"\s+")

# ---- 前置引导语：「他在给某人的信里说」。英/德/法。
LEADIN = re.compile(
    r"(?:said|says|writes|wrote|observed|observes|remarked|remarks)\s+(?:he|she|the\s+\w+|Mr\.|Gen\.|Col\.)\b"
    r"|(?:he|she)\s+(?:writes|wrote|says|said|observes|remarks)\b"
    r"|in\s+a\s+letter\s+(?:to|of|from)\b"
    r"|schreibt\s+(?:er|sie)\b|(?:er|sie)\s+schreibt\b|in\s+einem\s+Briefe?\s+an\b"
    r"|écrit[- ]il\b|dans\s+une\s+lettre\s+à\b",
    re.I)

# ---- 对白：命中句之后紧跟「……回答道／说道」+ 人名；或之前是说话人标记行。
DIALOG_AFTER = re.compile(
    r"\b(?:erwiedert|erwiederte|erwidert|erwiderte|sagte|sagt|rief|sprach|antwortete|entgegnete|fragte)\s+[A-ZÄÖÜ]"
    r"|\b(?:replied|answered|rejoined|cried|exclaimed)\s+(?:he|she|[A-Z])")
# 说话人标记行：一个首字母大写的词 + 句点 + 空格，且该词像人名/身份而不是句子结尾
SPEAKER_LABEL = re.compile(r"(?:^|\.\s|\s)([A-ZÄÖÜ][a-zäöüßſ]{2,14})\.\s+(?=[A-ZÄÖÜ])")

# ---- 校勘者／编者：谈版本、比对、印本、本版说明。
EDITOR = re.compile(
    r"verglichen(?:en)?\s+(?:zwei\s+)?Exemplare|Vergleichung\s+des\s+Originaltextes|Separatausgabe"
    r"|Druckfehler|Herausgeber|herausgegeben\s+von|Vorrede\s+(?:des|zur)|dieser\s+Ausgabe"
    r"|meines\s+Erachtens"
    r"|the\s+(?:present\s+)?editor|in\s+this\s+edition|are\s+now\s+offered\s+.{0,30}to\s+the\s+public"
    r"|the\s+text\s+here\s+(?:printed|given)",
    re.I)

# ---- 数字化／馆藏声明：图书馆或扫描方**在说话**（不是扫描留下的水印）。
# ★ 变异测试查出的坑：第一版把 `Digitized by` / `Google Book` / `Internet Archive` 也算进来，
#   而那是**扫描水印**（实测：随机抽 40 份，3 份含 `Digitized by`，8%——
#   不是我原先以为的「每份都有」，但足以让 ④ 在不相干的地方放红）。
#   一条本该由 ①（传记引导语）判红的候选，拆掉 ① 之后**仍然红**：红得凑巧。
#   水印只说明这份文件被扫描过，不说明**这句话是图书馆说的**，已移出规则。
DIGITIZE = re.compile(
    r"domaine\s+public|Nous\s+encourageons|dans\s+le\s+domaine\s+public"
    r"|(?:is|are)\s+in\s+the\s+public\s+domain|copyright\s+(?:has\s+)?expired"
    r"|biblioth[eè]que\s+(?:nationale|numérique)|Sponsored\s+by",
    re.I)

# 序言区：正文开头这一段里的第一人称，默认可疑（多半是序、献词、编者说明）。
FRONT_MATTER_CHARS = 12000

# ---- ⑤ 未闭合的引语：命中落在别人一段长引语的内部。
# ★ 第一版用**奇偶校验**（往前 4000 字数引号，奇数＝在引语内），实测就废了：
#   Reusswig 那段漏 2 条（引语外还有 `"over-subscribed."`／`"over-the-counter"`
#   两对把奇偶数凑回了偶），同时把 Brandeis 自己的一句打红
#   （开引号落在 4000 窗口之外，只剩一个关引号）。**窗口一变，结论就变。**
# ⇒ 改成不数个数，只判**最近那一个引号是开还是关**：
#   开 ⇒ 命中与它之间没有关引号 ⇒ 在引语内。这个判断不依赖窗口多大。
QMARK = re.compile(r'["„“”]')
QUOTE_LOOKBACK = 12000
# ★★ 语种关：**德语的 `“` 是关引号**（`„Botſchafters“`），英语的 `“` 是开引号。
#   第一版按英语一套判，Bismarck 2 条、Kant 1 条本人原话当场被打红 ——
#   与 [[regex-must-clear-the-corpus-language]] 同一形态（`A.L.S` 匹配德语 `als`）。
#   ⇒ 按**这一份文件自己的用法**定约定：出现 ≥3 个 `„` 就按德语读。
GERMAN_OPEN_MIN = 3
# ★ 开引号到命中的最大距离。**这个数是量出来的，不是挑出来的**（2026-08-13，33 例真语料）：
#   ⑤ 单独撑起的正例最远 **1247**（North 法官脚注；Reusswig 三条是 260/386/1067），
#   而误伤的负例在 **3750**（Pestalozzi 献词——OCR 把那段引语的关引号丢了）。
#   取 2000：正例侧留 1.6 倍余量，负例侧留 1.9 倍余量。
#   依据不只是这两个数——**跑掉几千字还没闭合的引语，多半是 OCR 丢了关引号**：
#   真有那么长的引文，排版上会用缩进整段引，不会用行内引号。
QUOTE_OPEN_MAX_DIST = 2000
# 引导语落在**引文自身**里的形态：`In Mr. Fisher's own words, — "…`
OWN_WORDS = re.compile(r"""(?:own\s+words|as\s+stated\s+by|in\s+the\s+words\s+of)"""
                       r"""[^"“]{0,40}["“]""", re.I)

# ---- ⑥ 听证／庭审转录：第一人称属于**作证的那个人**。
# 标记形态取自真语料（OCR 大小写混乱，`Mr. TowNE.`／`Mr. TOWNE.`／`Mr. Towne.` 三种都出现过）。
SPEAKER_TURN = re.compile(
    r"(?:^|[.;!?]\s)("
    r"(?:Mr|Mrs|Ms|Dr|Prof|Senator|Representative|Commissioner|Chairman|Judge|Justice"
    r"|Gen|Col|Capt|Hon)\.\s+[A-Z][A-Za-z'\-]{1,20}"
    r"|The\s+CHAIRMAN|The\s+WITNESS"
    r"|[A-Z][A-Z'\-]{3,20}"          # 全大写姓氏单独成标记
    r")\.\s+(?=[A-Z])")
# ★ 单个 `Mr. Smith.` 在任何叙述文里都可能出现 —— 靠**密度**分辨体裁，不靠单次命中：
#   ±10000 字窗口里 ≥3 个说话人标记才算转录体。
SPEAKER_TURN_WINDOW = 10000
SPEAKER_TURN_MIN = 3

# ---- ⑦ 引证抬头：**不打引号**，靠一行「姓名，职衔：」把下面整段归给别人。
# 「Brandeis Brief」的标志写法——用大量他人的社会事实与医学证词立论，
# 每一段前面一行出处，段落本身不加引号。⑤ 因此完全够不到。
# 实测：Muller v. Oregon 那一卷里
#   `Report of the Committee on the Early Closing of Shops Bill, British House of Lords, 1901.`
#   `Sir W. MacCormac, President of the Royal College of Surgeons :`
# 之后整段第一人称都是 MacCormac 的。
CITE_HEADER = re.compile(
    r"(?:^|[.)]\s)"
    r"((?:Sir|Dr|Mr|Mrs|Miss|Prof|Professor|Hon|Judge|Justice|Lord|Rev|Col|Gen)\.?\s+"
    r"[A-Z][\w.'\-]+(?:\s+[A-Z][\w.'\-]+){0,3}"
    r"|[A-Z][\w.'\-]+(?:\s+[A-Z][\w.'\-]+){1,3})"
    r"\s*,\s*"
    r"([^:.]{0,90}?\b(?:President|Secretary|Commissioner|Inspector|Superintendent|Chief|"
    r"Director|Surgeon|Physician|Professor|Chairman|Warden|Registrar|Officer|Delegate|"
    r"Controller|Comptroller|Manager|Agent|Engineer|Editor)\b[^:.]{0,90})"
    r"\s*:\s")
CITE_HEADER_MAX_DIST = 2500


def dehyphen(t: str) -> str:
    t = re.sub(r"(\w)[-‐‑]\s*\n\s*([a-z])", r"\1\2", t)
    return re.sub(r"(\w)[-‐‑]\s+([a-z])", r"\1\2", t)


def load_norm(raw: pathlib.Path, rec: dict):
    f = raw / pathlib.Path(rec["local_path"]).name
    if not f.exists():
        return None
    return WS.sub(" ", dehyphen(f.read_text(encoding="utf-8", errors="replace")))


def evidence(text: str, m: re.Match, pad: int = 34) -> str:
    """★ 打印证据必须打印**未截断**的命中片段本身。
    夹具比原文干净就等于没测——判据自己输出的例句也不许是截断过的。"""
    a = max(0, m.start() - pad)
    b = min(len(text), m.end() + pad)
    return ("…" if a > 0 else "") + text[a:b].strip() + ("…" if b < len(text) else "")


def inside_open_quote(norm: str, off: int):
    """⑤ 命中是否落在一段**未闭合**的引语里 → (是否, 开引号处的原文)。

    只判**最近那一个引号是开还是关**——命中与它之间按定义没有别的引号，
    所以「它是开的」等价于「引语到命中处还没闭」。**不数个数，因此不吃窗口大小。**
    """
    w = norm[max(0, off - QUOTE_LOOKBACK):off]
    marks = list(QMARK.finditer(w))
    if not marks:
        return False, ""
    m = marks[-1]
    i, ch = m.start(), m.group()
    nxt = w[i + 1:i + 2]
    # ★ 无论哪种约定，**开引号后面都紧跟字母**。OCR 里满地的 `„ . . . ..`／`„ 18 1 38`
    #   全靠这一条挡掉（Marshall、Jefferson 各一条本人原话曾被它们打红）。
    if not re.match(r"[A-Za-zÀ-ɏſ]", nxt or ""):
        return False, ""
    if len(w) - i > QUOTE_OPEN_MAX_DIST:
        return False, ""
    german = norm.count("„") >= GERMAN_OPEN_MIN
    if german:
        # 德语：只有 `„` 是开；`“`／`”`／`"` 一律当关。
        return (True, "…" + w[max(0, i - 175):i + 45].strip() + "…") if ch == "„" else (False, "")
    if ch in "”„":
        return False, ""
    if ch != "“":
        # 关引号：前面是句末标点 —— `future." Our Duty`（后面跟字母的已在上面挡掉）
        if re.search(r"[.,;!?]\s?$", w[max(0, i - 2):i]):
            return False, ""
    return True, "…" + w[max(0, i - 175):i + 45].strip() + "…"


def nearest_speaker_turn(norm: str, off: int):
    """⑥ 命中是否落在听证／庭审转录里 → (是否, 最近的说话人标记及距离)。"""
    a = max(0, off - SPEAKER_TURN_WINDOW)
    b = min(len(norm), off + SPEAKER_TURN_WINDOW)
    turns = list(SPEAKER_TURN.finditer(norm[a:b]))
    if len(turns) < SPEAKER_TURN_MIN:
        return False, ""
    before = [m for m in turns if a + m.start() < off]
    if not before:
        return False, ""
    m = before[-1]
    d = off - (a + m.end())
    return True, (f"最近说话人标记「{m.group(1)}.」在命中前 {d} 字（本窗口共 {len(turns)} 个标记）："
                  f"…{norm[a + m.start():a + m.start() + 130].strip()}…")


def judge(norm: str, off: int, quote: str):
    """返回 [(级别, 机制, 证据原文)]。**不下结论，只给理由。**"""
    out = []
    before = norm[max(0, off - 340):off]
    after = norm[off + len(quote):off + len(quote) + 160]
    head = norm[:FRONT_MATTER_CHARS]

    m = LEADIN.search(before)
    if m:
        out.append(("高", "①传记/文集转录他人书信：命中句之前有引导语", evidence(before, m)))

    m = DIALOG_AFTER.search(after)
    if m:
        out.append(("高", "②小说对白：命中句之后跟着「某人答道」", evidence(after, m)))
    else:
        m = SPEAKER_LABEL.search(before[-90:])
        if m:
            out.append(("中", "②小说对白：命中句之前疑似说话人标记行", evidence(before[-90:], m)))

    m = DIGITIZE.search(before) or DIGITIZE.search(quote)
    if m:
        src = before if DIGITIZE.search(before) else quote
        out.append(("高", "④数字化/馆藏声明：说话的是图书馆或扫描方", evidence(src, m)))

    m = EDITOR.search(before) or EDITOR.search(quote)
    if m:
        src = before if EDITOR.search(before) else quote
        lv = "高" if off < FRONT_MATTER_CHARS else "中"
        out.append((lv, "③校勘者/编者：谈版本、比对、印本或本版体例", evidence(src, m)))
    elif off < FRONT_MATTER_CHARS:
        out.append(("中", f"③序言区：偏移 {off} < {FRONT_MATTER_CHARS}，多半是序/献词/编者说明",
                    evidence(head, re.search(re.escape(quote[:40]), head) or re.compile(r"^").match(head))))

    hit, ev = inside_open_quote(norm, off)
    if hit:
        out.append(("高", "⑤未闭合引语：命中落在别人一段长引语的内部，开引号处通常就写着是谁", ev))
    else:
        m = OWN_WORDS.search(quote)
        if m:
            out.append(("高", "⑤引导语落在**引文自身**里：`…own words / as stated by…` 之后就是引号", evidence(quote, m)))

    hit, ev = nearest_speaker_turn(norm, off)
    if hit:
        out.append(("高", "⑥听证/庭审转录：第一人称属于作证的那个人，不是编者也不是本人", ev))

    w = norm[max(0, off - CITE_HEADER_MAX_DIST):off]
    hs = list(CITE_HEADER.finditer(w))
    if hs:
        m = hs[-1]
        out.append(("高", f"⑦引证抬头（辩状/报告体，**整段不打引号**）：下面这段归「{m.group(1)}」，"
                          f"抬头在命中前 {len(w) - m.end()} 字", evidence(w, m, pad=20)))
    return out


def run(raw: pathlib.Path, ledger: pathlib.Path, quotes: list):
    recs = {r["source_id"]: r for r in
            (json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip())}
    cache, rows, unread = {}, [], []
    for q in quotes:
        sid, off, txt = q["source_id"], q["norm_offset"], q["quote"]
        if sid not in recs:
            unread.append(sid)
            continue
        if sid not in cache:
            cache[sid] = load_norm(raw, recs[sid])
        norm = cache[sid]
        if norm is None:
            unread.append(sid)
            continue
        if norm[off:off + len(txt)] != txt:
            rows.append({"source_id": sid, "norm_offset": off, "★": "定位对不上，先修偏移", "flags": []})
            continue
        fl = judge(norm, off, txt)
        rows.append({"source_id": sid, "norm_offset": off,
                     "title": recs[sid].get("title", "")[:44], "quote": txt[:110], "flags": fl})
    return rows, unread


# ---------------- 正负对照：**全部跑真语料，不用自编夹具** ----------------
BASE = pathlib.Path(__file__).resolve().parents[2] / "_corpora"
# 必须标出「高」的：本批 5 次实际踩到的
POS = [
    ("wip-marshall-173/workspaces/john-marshall", "src-e03fa3b73336", 12486, "①传记"),
    ("wip-marshall-173/workspaces/john-marshall", "src-2e4088bec901", 172766, "①传记"),
    ("wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-0ac0430b0bd5", 21950, "②对白"),
    ("wip-kant-179/workspaces/immanuel-kant", "src-21c82472024f", 970, "③校勘"),
    ("wip-kant-179/workspaces/immanuel-kant", "src-c90e1301fe6c", 9299, "③校勘"),
    ("wip-kant-179/workspaces/immanuel-kant", "src-64ab9f79bfb5", 2242, "③校勘"),
    ("wip-jefferson-175/workspaces/thomas-jefferson", "src-843f7cba4fcc", 5568, "④数字化"),
    # ★ 2026-08-13 Brandeis #172：本工具原来对这 9 条只标出 1 条（漏 8）
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-26a41d751b61", 154114, "⑤Reusswig"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-652aa149475b", 157119, "⑤Reusswig"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-75ebbbaa5e10", 154277, "⑤Reusswig"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-e6750d32440f", 50020, "⑤North法官脚注"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-26dbd660239a", 6445, "⑤b Fisher"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-04857426d8e2", 144742, "⑥Towne 证人"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-dc08306e597b", 142268, "⑥Towne 证人"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-696d2c185f7d", 141645, "⑥Towne 证人"),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-94baf0d4e64a", 446915, "①工厂主转述"),
    # ⑦「Brandeis Brief」体：MacCormac 在上议院委员会作证，整段不打引号
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-0b710810f1f3", 106161, "⑦引证抬头"),
]
# 必须**没有**「高」的：已逐条核过、确属本人的
NEG = [
    ("wip-marshall-173/workspaces/john-marshall", "src-8c46f27be355", 69739),
    ("wip-marshall-173/workspaces/john-marshall", "src-8c46f27be355", 483554),
    ("wip-marshall-173/workspaces/john-marshall", "src-8c46f27be355", 523989),
    ("wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-e8dc4740199f", 82643),
    ("wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-413dab629c0f", 6447),
    ("wip-bismarck-176/workspaces/otto-von-bismarck", "src-ee3963b8a368", 36381),
    ("wip-bismarck-176/workspaces/otto-von-bismarck", "src-0e926803e259", 75928),
    ("wip-kant-179/workspaces/immanuel-kant", "src-deba15392d05", 65591),
    ("wip-kant-179/workspaces/immanuel-kant", "src-ff581bf0e357", 297380),
    ("wip-kant-179/workspaces/immanuel-kant", "src-1487a594f356", 777540),
    ("wip-jefferson-175/workspaces/thomas-jefferson", "src-29b9a8e05249", 60368),
    ("wip-jefferson-175/workspaces/thomas-jefferson", "src-ac2df69c6c36", 5495),
    # ★ 2026-08-13 Brandeis #172：与上面 9 条同一批抽出、**逐条读前 700 字核过确属他本人**。
    #   ⑤ 的第一版（奇偶校验）把 `src-2ef164245cdd` 打红过 —— 它留在这里防那一版回来。
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-ea2c7920700d", 50928),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-3d16531d4151", 175321),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-f262a6c0fb76", 171201),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-2ef164245cdd", 32653),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-0a5e23fd4921", 9847),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-f713f255ca3e", 54040),
    ("wip-brandeis-172/workspaces/louis-brandeis", "src-7ca5e8f31c88", 29933),
]


def _sentence_at(norm, off):
    e = norm.find(".", off + 40)
    return norm[off:(e + 1) if e > 0 else off + 150]


SKIP_NO_CORPUS = 5      # 语料不在本树 ⇒ **未跑**，不是不过


def self_test() -> int:
    # ★★ 自测的正负例**全部取自真语料**，而语料按裁定不进 git。
    #   在干净 clone 里第一版逐条打印「✗ 读不到正文」并 rc=1 ——
    #   那读起来像「判据坏了」，其实是**语料不在**。两件事必须分开报。
    #
    #   ★ 第二版我加了个探测点（「raw 里有没有 txt」），**也是错的**：
    #     Marshall 在 clone 里有 11 份 txt，只是**不是自测要的那几份**。
    #     代理指标看不见「部分缺」。⇒ 改成**按结果判**：
    #     读不到的例子单独计数，全部读不到才叫跳过，读得到的照常判。
    bad = 0
    unread = 0
    for label, cases, want_high in (("正对照（必须标红）", POS, True), ("负对照（必须不红）", NEG, False)):
        print(f"\n### {label}")
        for case in cases:
            ws, sid, off = case[0], case[1], case[2]
            W = BASE / ws
            recs = {r["source_id"]: r for r in
                    (json.loads(l) for l in (W / "evidence" / "source-ledger.jsonl")
                     .read_text(encoding="utf-8").splitlines() if l.strip())}
            norm = load_norm(W / "raw", recs[sid])
            if norm is None:
                print(f"  — 读不到正文 {sid}（**未跑，不是不过**：这份语料不在本树里）")
                unread += 1
                continue
            q = _sentence_at(norm, off)
            fl = judge(norm, off, q)
            high = [f for f in fl if f[0] == "高"]
            ok = bool(high) == want_high
            bad += 0 if ok else 1
            mark = "✓" if ok else "✗"
            why = ("｜".join(f[1].split("：")[0] for f in high)) or ("中级:" + "｜".join(
                f[1].split("：")[0] for f in fl) if fl else "无标记")
            print(f"  {mark} {sid}@{off} {why}")
            if not ok:
                print(f"      句: {q[:110]}")
                for lv, mech, ev in fl:
                    print(f"      [{lv}] {mech}\n          {ev}")
    total = len(POS) + len(NEG)
    if unread == total:
        print(f"\n★★ **未跑，不是通过**：{total} 个例子的语料**一份都不在这棵树里**。")
        print("   语料按裁定不进 git —— 见仓根 `START-HERE.md`「语料在哪」一节。")
        print(f"   退出码 {SKIP_NO_CORPUS} = 跳过；0 = 全过；1 = 有不符。")
        return SKIP_NO_CORPUS
    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}"
          f"（正 {len(POS)} 例全部取自真语料、负 {len(NEG)} 例是已逐条核过的本人原话）")
    if unread:
        print(f"★ 其中 **{unread}/{total} 个例子读不到语料，未跑**（不是通过，也不是不过）。")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw")
    ap.add_argument("--ledger")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.raw and a.ledger):
        print("要么 --self-test，要么同时给 --raw 与 --ledger", file=sys.stderr)
        return 2
    blob = sys.stdin.read()
    data = json.loads(blob[blob.find("{"):])
    quotes = data.get("引文", data.get("quotes", []))
    rows, unread = run(pathlib.Path(a.raw), pathlib.Path(a.ledger), quotes)
    n_high = sum(1 for r in rows if any(f[0] == "高" for f in r["flags"]))
    n_mid = sum(1 for r in rows if r["flags"] and not any(f[0] == "高" for f in r["flags"]))
    print(json.dumps({
        "候选数": len(rows),
        "**高·几乎肯定不是本人**": n_high,
        "中·需看上下文": n_mid,
        "无标记": len(rows) - n_high - n_mid,
        "读不到正文": unread,
        "★ 本工具不判断": "只给理由和原文证据，说话人由人定",
        "逐条": rows,
    }, ensure_ascii=False, indent=1))
    return 4 if unread else (3 if n_high else 0)


if __name__ == "__main__":
    sys.exit(main())
