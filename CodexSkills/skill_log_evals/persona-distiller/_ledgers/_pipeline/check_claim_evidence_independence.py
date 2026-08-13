#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_claim_evidence_independence.py —— **两个 source_id 里，是不是同一部作品**

## 这道门现在怎么判的

`quality_check.evaluate_claims()`（scripts/quality_check.py:375-381）：

    if len(set(claim.get('source_ids', []))) < 2:
        report.error('claim.insufficient-support', …)
    clusters = set(claim.get('evidence_clusters', []))
    if len(clusters) < 2:
        report.error('claim.non-independent', …)

**两条都在数「不同的字符串有几个」。** 于是

- 同一本书的两次扫描 ＝ 两个 `source_id` ⇒ `insufficient-support` **过**；
- 同一部作品写成两句不同措辞的中文 ⇒ `evidence_clusters` 两条 ⇒ `non-independent` **过**。

两条门加起来仍然只要求**两个字符串**，而不是**两处证据**。
踩坑库 `two-source-ids-is-not-two-evidences` 记的就是这件事，
当时只能靠人逐条看；2026-08-14 判重尺子加上包含率之后，**这件事可以机器判了**。

## 本件判什么

对每条要求「≥2 处支撑」的 claim：把它的 `source_ids` 逐对拿去量，
**如果每一对都被判成同一部作品，就报出来** —— 那条 claim 的支撑实际只有一处。

尺子与 `measure_distinct_works.py` **同一份代码**（import 进来，不重实现）：
Jaccard ≥ 0.05 **或** 包含率 ≥ 0.25。
[[baseline-must-be-the-same-kind-as-what-you-compare]]：别重实现判据的度量。

## 它判不了什么（**必须一起念**）

1. ★★ **跨语言判不了**（原文 vs 译文恒 0.0000）⇒ 在**多语种工作区**它会**少报塌缩**。
   2026-08-14 在 Michelangelo #185 上实测到了这件事的活样本：

       src-34bb6d56038a《Le lettere di Michelangelo Buonarroti》 意大利文 202,781 词
       src-8539ad71569a《A record of his life…》(Carden 1913)    英译本   97,224 词
       两者 Jaccard 0.0000／包含率 0.0001 ⇒ 本件判「两部不同的作品」

   而**同一封信在两份里都在**：意大利本 `A BUONARROTO SUO FRATELLO … mai conosciuto,
   e non mi conosciete. Idio ve lo perdoni!`；英译本 `But ye have never understood me
   in the past… May God forgive you!`。**同一次话语，两个语种，重叠为零。**
   ⇒ 一条 claim 同时引这两份，本件会放行，而证据只有一处。
   [[original-and-translation-are-one-utterance-with-zero-overlap]]

   ★ 所以本件**按正文判语种**并在多语种工作区印警告。**不能用台账的 `language` 字段**：
   Michelangelo 那 47 行**全是 `null`**，照字段判会报「单语种」——正是要防的那种假绿。
2. ★★★ **「两部不同的书」≠「两处独立证据」——选集会把同一封信收进两本。**
   2026-08-14 在 Michelangelo #185 上量到：同一封写给 Vasari 的信（罗马 1550 年 9 月，
   讲劳伦齐亚纳图书馆楼梯）**同时在**

       src-43c819c03a55 1817《Le rime di Michelagnolo Buonarroti》（诗集，附书信）
       src-6094206729a1 1875《Le lettere di Michelangelo Buonarroti》（书信集）

   两本是**真的两部不同出版物**（本件判「不同作品」没判错），
   但这条 claim 的证据是**同一封信**：`si discostino con tutta la scala dal muro circa
   tre palmi, in modo che l'imbasamento del Ricetto non sia occupato in luogo nessuno`。
   ⇒ **作品层面的不同，不等于证据层面的独立。** 证据的单位是**那封信**，不是那本书。
   本件因此**另加一层按引文判**：claim 里反引号引的原话若同时出现在两份被引源里，
   直接报「两处支撑其实是一处」——这一层比作品层更贴近「证据」。

3. **读不到正文的源跳过**，跳过多少要印出来 —— 「跳过」不是「通过」。
4. **只有一个 `source_id` 的 claim 不归本件管** —— 那是 `insufficient-support`
   自己就会报的，本件只管「看起来有两处、其实是一处」。
5. 它**不改任何门、不改任何 claim**，只报数。要不要改是人的事。

## 用法

    python3 check_claim_evidence_independence.py --workspace <工作区>
    python3 check_claim_evidence_independence.py --all
    python3 check_claim_evidence_independence.py --self-test

退出码：0＝跑完（**这不是一道门**）；2＝有 claim 的支撑实际只有一处
"""
import argparse
import glob
import collections
import itertools
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure_distinct_works import (CONTAIN_T, DEFAULT_T, containment,  # noqa: E402
                                    jaccard, signature)

PD = HERE.parent.parent
CORPORA = PD / "_corpora"
# 与 quality_check.evaluate_claims 同一份名单
NEEDS_TWO = {"mental-model", "heuristic", "value", "work-method", "blind-spot", "contradiction"}

# ★ 虚词剖面判语种。够用就行——只要能回答「这个工作区是不是混着两种语言」。
STOPWORDS = {
    "en": {"the", "and", "of", "to", "in", "that", "it", "is", "was", "for", "with", "as", "his"},
    "it": {"che", "non", "di", "il", "la", "per", "con", "del", "una", "sono", "questo", "io", "mi"},
    "de": {"der", "die", "und", "den", "von", "zu", "das", "ist", "nicht", "ein", "mit", "auf"},
    "la": {"est", "non", "cum", "quod", "sed", "qui", "ad", "ex", "atque", "enim"},
    "fr": {"les", "des", "est", "une", "dans", "pour", "que", "qui", "pas", "sur", "avec"},
}
_WORD = re.compile(r"[a-zàâäçèéêëìíîïñòóôöùúûüß]+")


# ★★ 2026-08-14：先按**字符集**分流。原来只有拉丁虚词表，于是 Brandeis 那份 1917 年的
#   俄文《Война и еврейская проблема》被判成 `?`，他的工作区**被当成单语种**报了出去——
#   而他 train 里同时有英文《The Jewish problem, how to solve it》(1915/1919)。
#   正是本项要防的那种假绿，却出在本项自己身上。[[a-gates-scan-set-is-smaller-than-reality]]
_SCRIPTS = (
    ("ru", (0x0400, 0x04FF)),      # 西里尔
    ("el", (0x0370, 0x03FF)),      # 希腊
    ("he", (0x0590, 0x05FF)),      # 希伯来
    ("ar", (0x0600, 0x06FF)),      # 阿拉伯
    ("zh", (0x4E00, 0x9FFF)),      # 汉字
    ("ja", (0x3040, 0x30FF)),      # 假名
)


def guess_lang(text: str, cap: int = 20000) -> str:
    """正文 → 语种码。**纯函数**，自测不碰磁盘。判不出来返回 `?`。

    ★ 先看字符集（非拉丁文字整块判），再用拉丁虚词表分英/意/德/拉/法。
    """
    # ★★ 取样单位：字符集那一步按**字符**切，虚词剖面那一步仍按**词**切。
    #   改字符集分流时我把整段改成了 text[:cap]（字符），样本从 2 万词缩到约 3 千词，
    #   全库被标的工作区**换了一批**（Cicero／Liebig／Martens 掉出，Frobel／Machiavelli／
    #   Mendel／Pestalozzi 进来）——我却在提交里写成「5 → 6」，像是只多了一个。
    #   **换了取样单位就是换了尺子，不许当成同一把尺子的增量。**
    s = text[:cap]
    letters = sum(1 for c in s if c.isalpha())
    if letters:
        for code, (lo, hi) in _SCRIPTS:
            n = sum(1 for c in s if lo <= ord(c) <= hi)
            if n / letters >= 0.20:      # 混排也认得出来（书名页常有拉丁转写）
                return code
    w = _WORD.findall(text.lower())[:cap]
    if not w:
        return "?"
    sc = {k: sum(1 for x in w if x in v) / len(w) for k, v in STOPWORDS.items()}
    best = max(sc, key=sc.get)
    return best if sc[best] >= 0.02 else "?"


def same_work(sig_a: set, sig_b: set, t: float = DEFAULT_T, c: float = CONTAIN_T) -> bool:
    """两份签名是不是同一部作品。**纯函数**，自测不碰磁盘。"""
    return jaccard(sig_a, sig_b) >= t or containment(sig_a, sig_b) >= c


# ★★ 门槛别写在正则里：原来是 `{40,}`，于是 `We are not enemies, but friends.`（32 字符）
#   **根本没被抽出来**，Lincoln 那条看起来只有一处话语 —— 我在下游加了两个词数门槛都没用，
#   因为它压根没走到下游。抽的时候放宽，**判的时候再分档**。
_QUOTE = re.compile(r"`([^`]{10,})`")


def _norm(s: str) -> str:
    s = s.replace("\u00ad", "")
    s = re.sub(r"-\s*\n\s*", "", s)
    return re.sub(r"\s+", " ", s)


def shared_quote(claim_text: str, texts: dict):
    """claim 里反引号引的原话，是不是**同时**落在两份被引源里。

    → (共享的那段, [源 id…]) 或 (None, [])。**纯函数**，自测不碰磁盘。

    ★ 这一层比「是不是同一部作品」更贴近「是不是同一处证据」：
      选集把同一封信收进两本书时，作品层判「不同」，而证据只有一处。
    """
    raw = [_norm(m.group(1)) for m in _QUOTE.finditer(claim_text or "")]
    # ★★ **数引文**与**匹配引文**要用两个门槛，混用会误伤：
    #   Lincoln 的 clm-bf724593cbe6 第二处原话是 `We are not enemies, but friends.`——
    #   只有 6 词，被 ≥8 的门槛滤掉，于是这条 claim 看起来「只有一处话语」而被误报。
    #   数的时候用 ≥3 词并剔掉 `src-…` 这种 id；匹配的时候才要求 ≥8 词（短串会瞎撞）。
    _ID = re.compile(r"^src-[0-9a-f]+(\s|$)")
    counted = [q for q in raw if not _ID.match(q) and len(q.split()) >= 3]
    qs = [q for q in counted if len(q.split()) >= 8]
    # ★★★ 2026-08-14 收紧：**只有当这条 claim 通篇只有一处原话时才判**。
    #   第一版会误伤 Lincoln 的 clm-bf724593cbe6：它引的是**两场不同的演说**
    #   （分裂之家 1858 ／第一次就职 1861），而 1906《Complete works》与
    #   1911《The best of Lincoln》两本**都收了这两场**——于是「同一段话在两本里」成立，
    #   而 claim 的两处证据仍是**两次不同的话语**，本来就独立。
    #   ⇒ 本层要回答的是「这条 claim 是不是只有一次话语」，不是「两本书重不重叠」。
    if len(counted) != 1 or len(qs) != 1:
        return None, []
    q = qs[0]
    rx = re.compile(r"\s+".join(re.escape(w) for w in q.split()[:14]), re.I)
    # ★ 自己再归一一次：调用方**可能**传的是原样文本（自测就这么传的）。
    hit = [s for s, tx in texts.items() if rx.search(_norm(tx))]
    return (q, sorted(hit)) if len(hit) >= 2 else (None, [])


def judge_claim(sids, sigs, t=DEFAULT_T, c=CONTAIN_T):
    """→ ('ok'|'collapsed'|'unmeasurable'|'skip', 量到的份数, 独立作品数)。

    ★ 只有**每一对都是同一部作品**才判 collapsed；有一对不同就算 ok。
      往「少报」那一侧偏 —— [[loosen-only-the-exonerating-side]]。
    """
    uniq = sorted(set(sids))
    if len(uniq) < 2:
        return "skip", len(uniq), len(uniq)
    have = [s for s in uniq if sigs.get(s)]
    if len(have) < 2:
        return "unmeasurable", len(have), 0
    # 并查集：只要连通就算一部
    par = {s: s for s in have}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for a, b in itertools.combinations(have, 2):
        if same_work(sigs[a], sigs[b], t, c):
            par[find(a)] = find(b)
    works = len({find(s) for s in have})
    return ("collapsed" if works < 2 else "ok"), len(have), works


# ══════════════════ 自测 ══════════════════

def self_test() -> int:
    ok = t = 0

    def chk(d, cond):
        nonlocal ok, t
        t += 1
        ok += 1 if cond else 0
        print(f"  {'✓' if cond else '✗'} {d}")

    book = ("the test of perceptible current is not a legal test it is both unpractical and "
            "unscientific perceptible in what degree it may be asked to the eye and to what "
            "eye to one of powerful or of weak refraction ") * 40
    scan2 = book.replace("the test", "the te*st").replace("degree", "degr ee")
    other = ("the size of a life insurance company is no evidence of success it is evidence "
             "only of the extent to which the business has been pushed and of the amount of "
             "money which policy holders have paid in premiums ") * 40
    filler = " ".join(f"wholly unrelated filler sentence {i} with distinct vocabulary {i*7}"
                      for i in range(1, 900))
    anthology = filler + " " + book + " " + filler        # ★ 短文被收进文集
    S = {"a": signature(book), "b": signature(scan2), "c": signature(other),
         "d": signature(anthology), "e": set()}

    chk("★ 同一本书的两次扫描 → **塌成一处**（这道门现在会放它过）",
        judge_claim(["a", "b"], S)[0] == "collapsed")
    chk("★★ 短文 ＋ 收了它的文集 → **塌成一处**（Jaccard 看不见，靠包含率）",
        judge_claim(["a", "d"], S)[0] == "collapsed")
    chk("★ 反例：两部不同的书 → ok，**不许误报**",
        judge_claim(["a", "c"], S)[0] == "ok")
    chk("★★ 反例：三份里有一份是别的书 → ok（只有**每一对**都同一部才算塌）",
        judge_claim(["a", "b", "c"], S)[0] == "ok")
    chk("★ 反例：只有一个 source_id → skip，不归本件管（那是 insufficient-support 的事）",
        judge_claim(["a"], S)[0] == "skip")
    chk("★ 反例：重复写了两遍同一个 id → 去重后只剩一个 ⇒ skip",
        judge_claim(["a", "a"], S)[0] == "skip")
    chk("★★ 读不到正文 → **unmeasurable，不是 ok**（跳过不是通过）",
        judge_claim(["a", "e"], S)[0] == "unmeasurable")
    chk("★ 三份同一本书 → 独立作品数 1",
        judge_claim(["a", "b", "d"], S)[2] == 1)
    chk("★ 反例：门收紧到不可能（包含率 1.01、Jaccard 1.01）时，同书两扫描也判 ok "
        "—— 证明结论确实由这两个阈值决定，不是别处写死的",
        judge_claim(["a", "b"], S, t=1.01, c=1.01)[0] == "ok")
    chk("★★★ 两栏必须同一个口径：**引了那一对但另有第三部作品** ⇒ 不算塌"
        "（Koch 的 29 vs 26 就差在这 5 条上）",
        judge_claim(["a", "b", "c"], S)[0] == "ok")
    EN = ("the letters of a man to his brother about money and the debts of the house " * 30)
    IT = ("che non mi conosciete e non mi avete mai conosciuto io vi perdono per il denaro " * 30)
    chk(f"★ 判语种：英文段 → en（实得 {guess_lang(EN)}）", guess_lang(EN) == "en")
    chk(f"★ 判语种：意大利文段 → it（实得 {guess_lang(IT)}）", guess_lang(IT) == "it")
    chk(f"★ 反例：空文本 → `?`，不许瞎猜（实得 {guess_lang('')}）", guess_lang("") == "?")
    RU = "Война и Еврейская Проблема статьи Луи Д Брандейса и других авторов " * 20
    chk(f"★★ **西里尔 → ru，不是 `?`**（Brandeis 那份 1917 俄文集就栽在这里）"
        f"（实得 {guess_lang(RU)}）", guess_lang(RU) == "ru")
    chk(f"★ 书名页混排拉丁转写仍判 ru（实得 {guess_lang('Voina 1917 ' + RU)}）",
        guess_lang("Voina 1917 " + RU) == "ru")
    chk(f"★ 反例：纯英文不许被字符集分流误判（实得 {guess_lang(EN)}）", guess_lang(EN) == "en")
    chk(f"★ 反例：全是数字/符号 → `?`（实得 {guess_lang('123 456 %%% 789')}）",
        guess_lang("123 456 %%% 789") == "?")
    chk("★★ **同一次话语跨语言，重叠为零** —— 本件看不见，所以要靠语种警告兜底",
        judge_claim(["en", "it"], {"en": signature(EN), "it": signature(IT)})[0] == "ok")
    LET = ("si discostino con tutta la scala dal muro circa tre palmi in modo che "
           "l imbasamento del ricetto non sia occupato in luogo nessuno")
    BOOK_A = "poems and more poems " * 50 + LET + " and then more poems"
    BOOK_B = "letters and more letters " * 50 + LET + " and then more letters"
    CLAIM = "他下施工指令：先给尺寸再给判据。逐字：`" + LET + "`（src-a）。"
    q, hit = shared_quote(CLAIM, {"a": BOOK_A, "b": BOOK_B})
    chk(f"★★★ **同一段原话落在两本不同的书里 → 抓出来**（实得 {hit}）", hit == ["a", "b"])
    q2, h2 = shared_quote(CLAIM, {"a": BOOK_A, "c": "wholly different text " * 60})
    chk("★★ 反例：只有一本含这段 → 不报", h2 == [])
    chk("★ 反例：claim 里没有反引号引文 → 不报",
        shared_quote("没有引文的一句话", {"a": BOOK_A, "b": BOOK_B})[1] == [])
    TWO = ("他引了两场不同的演说：`" + LET + "`，另一处是 `" +
           "we are not enemies but friends we must not be enemies though passion may have" + "`。")
    chk("★★★ **反例：claim 引了两处不同的话 → 不报**（Lincoln 那条：两本选集都收了两场演说，"
        "而两处证据本来就是两次话语）",
        shared_quote(TWO, {"a": BOOK_A + " we are not enemies but friends we must not be "
                                        "enemies though passion may have",
                           "b": BOOK_B + " we are not enemies but friends we must not be "
                                        "enemies though passion may have"})[1] == [])
    SHORT = ("`" + LET + "`（`src-aaaa1111`）与另一处 `We are not enemies, but friends.`"
             "（`src-bbbb2222`）在同一个模型里。")
    chk("★★★ **反例：第二处原话只有 6 词，仍算「两处话语」→ 不报**"
        "（Lincoln clm-bf724593cbe6 就栽在这里；且 `src-…` 不算引文）",
        shared_quote(SHORT, {"a": BOOK_A, "b": BOOK_B})[1] == [])
    chk("★ 反例：引文太短（<8 词）→ 不报，免得误撞",
        shared_quote("逐字：`short quote here`", {"a": BOOK_A, "b": BOOK_B})[1] == [])
    chk("★ 归一：断字/换行不影响命中",
        shared_quote("`" + LET + "`", {"a": BOOK_A.replace("discostino", "discos-\ntino"),
                                       "b": BOOK_B})[1] == ["a", "b"])
    chk("★ 与 quality_check 的类目名单逐字一致",
        NEEDS_TWO == {"mental-model", "heuristic", "value", "work-method",
                      "blind-spot", "contradiction"})
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


# ══════════════════ 磁盘一侧 ══════════════════

def scan(ws: pathlib.Path):
    cl = ws / "evidence/claims.jsonl"
    led = ws / "evidence/source-ledger.jsonl"
    if not cl.is_file() or not led.is_file():
        return None
    paths = {}
    for line in led.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            paths[d.get("source_id")] = ws / str(d.get("local_path") or "")
    claims = [json.loads(x) for x in cl.read_text(encoding="utf-8").splitlines() if x.strip()]
    need = [c for c in claims if c.get("category") in NEEDS_TWO]
    want = {s for c in need for s in c.get("source_ids", [])}
    sigs = {}
    langs = collections.Counter()
    for s in want:
        p = paths.get(s)
        if p and p.is_file():
            txt = p.read_text(encoding="utf-8", errors="replace")
            sigs[s] = signature(txt)
            langs[guess_lang(txt)] += 1
    out = {"collapsed": [], "unmeasurable": [], "ok": 0, "skip": 0, "claims": len(need),
           "射程外同样引了塌缩对的": [], "语种": dict(langs), "同一段引文落在两份源里": []}
    # ★★ 证据层：把被引源的正文归一后留着，供 shared_quote 用
    body = {}
    for s in want:
        p2 = paths.get(s)
        if p2 and p2.is_file():
            body[s] = _norm(p2.read_text(encoding="utf-8", errors="replace"))
    collapsed_pairs = set()
    for c in need:
        v, n, w = judge_claim(c.get("source_ids", []), sigs)
        cid = c.get("claim_id", "<无 id>")
        if v == "collapsed":
            out["collapsed"].append((cid, c.get("category"), n,
                                     len(set(c.get("evidence_clusters", [])))))
            collapsed_pairs.add(frozenset(set(c.get("source_ids", []))))
        elif v == "unmeasurable":
            out["unmeasurable"].append(cid)
        else:
            out[v if v == "skip" else "ok"] += 1
        # ★★ 证据层**单独一支**，与上面那条 if/elif/else 链**互不影响**。
        #   2026-08-14 我第一次把它插在中间，`elif` 于是挂到了它头上——
        #   凡是有 ≥2 个 source_id 的 claim 都走进证据层这一支，**再也走不到 `ok` 那一格**，
        #   于是「实测两处」在全库报成 0。四格加起来不等于总数就是它在报警：
        #   Dewey 8 条报成 0+0+2+0=2。**分支加进已有链条时，先数一遍四格和对不对得上。**
        if len(set(c.get("source_ids", []))) >= 2:
            q, hit = shared_quote(c.get("claim"), {s: body[s] for s in set(c.get("source_ids", []))
                                                   if s in body})
            if q:
                out["同一段引文落在两份源里"].append((cid, hit, q[:70]))
    # ★★ 射程：本件只报 NEEDS_TWO 那 6 个类目（与 quality_check 同名单），
    #   但**问题的规模比射程大**。Koch #107 的旧台账已量过一次：报 15 条，
    #   而只引那一对源的断言共 41 条，其余 26 条是 fact／boundary／epistemic。
    #   ⇒ 「N 条」是**判据的射程**，不是问题的规模。[[counts-need-their-cutoff-stated]]
    #
    # ★★★ 2026-08-14 改：这一栏原本用的是「引了那一对源」（≥ 子集），
    #   而上面 collapsed 用的是「**所有**源塌成一部作品」——**同一个判据里两个口径**。
    #   于是 Koch 报 29 而旧台账记 26，两个数都对、量的不是一回事
    #   （46 条「引了那一对」里有 5 条另引了第三部作品，那 5 条的支撑并没有塌）。
    #   现在两栏都走 `judge_claim`，一个口径。[[two-checkers-same-text-different-rules]]
    want2 = {s for c in claims if c.get("category") not in NEEDS_TWO
             for s in c.get("source_ids", [])}
    for s in want2 - set(sigs):
        pp = paths.get(s)
        if pp and pp.is_file():
            sigs[s] = signature(pp.read_text(encoding="utf-8", errors="replace"))
    for c in claims:
        if c.get("category") in NEEDS_TWO:
            continue
        if judge_claim(c.get("source_ids", []), sigs)[0] == "collapsed":
            out["射程外同样引了塌缩对的"].append(c.get("claim_id", "<无 id>"))
    return out


def report(ws: pathlib.Path) -> int:
    r = scan(ws)
    if r is None:
        return 0
    tag = ws.name
    if not r["claims"]:
        return 0
    # ★ 四格之和必须等于总数——2026-08-14 那个分支 bug 就是靠它抓出来的：
    #   证据层的 if 插进了原来的 if/elif/else 链，凡有 ≥2 个 source_id 的 claim
    #   都走不到 `ok` 那一格，「实测两处」全库报成 0，而四格和 2 ≠ 总数 8。
    _sum = r["ok"] + len(r["collapsed"]) + r["skip"] + len(r["unmeasurable"])
    if _sum != r["claims"]:
        print(f"❌ {tag}：**四格加起来 {_sum} ≠ 总数 {r['claims']}** —— "
              f"计数分支漏了一格，下面的数不许用")
    print(f"{tag}：需要 ≥2 处支撑的 claim {r['claims']} 条 → "
          f"实测两处 {r['ok']}｜**塌成一处 {len(r['collapsed'])}**｜"
          f"只有一个 id {r['skip']}｜读不到正文 {len(r['unmeasurable'])}")
    for cid, cat, n, nc in r["collapsed"]:
        print(f"    ❌ {cid}  [{cat}]  {n} 个 source_id **是同一部作品**"
              f"；而 evidence_clusters 写了 {nc} 条 ⇒ 两道门都会放它过")
    for cid, hit, q in r["同一段引文落在两份源里"]:
        print(f"    ❌ {cid}：**同一段原话同时落在 {len(hit)} 份被引源里** {hit}")
        print(f"       「{q}…」 ⇒ 作品层可能判「两部不同的书」，而证据只有一处"
              f"（选集把同一封信收进两本）")
    real = {k: v for k, v in r["语种"].items() if k != "?"}
    if len(real) > 1:
        print(f"    ★★ **被引的源里混着 {len(real)} 种语言**（按正文判：{real}；"
              f"**只统计被这些 claim 引到的源**，不是整个工作区）——"
              f"原文与译文的重叠恒为 0，本件**看不见**它们是同一次话语 ⇒ "
              f"上面的「实测两处」在这里可能是**少报**，不是干净")
    if r["射程外同样引了塌缩对的"]:
        print(f"    ★ **射程**：另有 {len(r['射程外同样引了塌缩对的'])} 条断言引了同一对塌缩源，"
              f"但类目不在那 6 个里（fact／boundary／epistemic…）**所以本件不报**"
              f" —— 「{len(r['collapsed'])} 条」是判据的射程，不是问题的规模")
    if r["unmeasurable"]:
        print(f"    ！ 读不到正文、**未判**（不是通过）：{', '.join(r['unmeasurable'][:6])}"
              + (" …" if len(r["unmeasurable"]) > 6 else ""))
    return 2 if (r["collapsed"] or r["同一段引文落在两份源里"]) else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(f"★ 尺子与 measure_distinct_works 同源：Jaccard ≥ {DEFAULT_T} 或 包含率 ≥ {CONTAIN_T}")
    print("★ **跨语言判不了**、**读不到正文的算「未判」不算通过** ⇒ 本件只会少报。\n")
    if a.workspace:
        return report(pathlib.Path(a.workspace))
    if a.all:
        rc = 0
        tot = col = out_of_range = shared = 0
        for d in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
            ws = pathlib.Path(d)
            r = scan(ws)
            if r and r["claims"]:
                tot += r["claims"]
                col += len(r["collapsed"])
                out_of_range += len(r["射程外同样引了塌缩对的"])
                shared += len(r["同一段引文落在两份源里"])
                if report(ws) == 2:
                    rc = 2
        print(f"\n合计：需要 ≥2 处支撑的 claim **{tot}** 条，"
              f"其中 **{col}** 条的支撑实际只有一部作品；"
              f"★ 另有 **{out_of_range}** 条断言引了同一批塌缩源而类目不在射程内\n"
              f"★ 证据层（同一段原话落在两份被引源里）：**{shared}** 条"
              + ("　—— 0 不代表这条路安全：它是**给「补第二处」那条修法用的护栏**，"
                 "选集把同一封信收进两本时才会响" if shared == 0 else ""))
        return rc
    ap.error("要 --workspace 或 --all 或 --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
