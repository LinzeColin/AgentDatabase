#!/usr/bin/env python3
"""检查一手源「书自印的题名里说这是谁的集子」是否等于台账著录的人。

起因：Jefferson #175 的 src-106864c12dfa 台账写着
《Writings. Library ed. …》、IA 标识符 writingslibrarye01jeffuoft，
而正文第一页印的是 **THE WRITINGS OF JAMES MONROE, VOLUME I**。
它还在 holdout 里——盲判题面本来要从别人的书里出。

★ 为什么不按词频量（试过，失败）
  该文件头 2000 字里 Jefferson 出现 5 次、Monroe 只 1 次——
  那 5 次全是**门罗写给杰斐逊的信的目录条目**。
  「与他有关 ≠ 他写的」，词频在这类源上恒定指错方向。
  按词频跑全批：221 份可疑、几乎全是噪声（WHICH／Education／Herr／JSTOR），
  而唯一已知的真阳性**不在其中**。

★ 改判的口径：只认**作者式集子**的题名构式
  WRITINGS / WORKS / LETTERS / PAPERS / CORRESPONDENCE / SPEECHES
  / Werke / Schriften / Oeuvres / Opere —— 「X 的著作集」，X 是作者。
  **LIFE OF / MEMOIRS OF / BIOGRAPHY 一律不算**：传记的主角本来就该是别人
  （马歇尔写《华盛顿传》，题名页印 LIFE OF GEORGE WASHINGTON，完全正常）。

只在**整段题名区里一次都没提到目标**时才报——
「威廉一世与俾斯麦通信集」这类题名里目标在后半句，不报。
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re
import sys

# 题名区：题名页常在装订页/藏书票/卷首图之后，取宽一点
HEAD = 6000

# 作者式集子（题名里的人＝作者）
# ★ 去掉了 JOURNALS／MESSAGES／DIARY：太泛，`Journals of Congress` 是刊物不是人
EN = (r"WRITINGS|WORKS|LETTERS|PAPERS|CORRESPONDENCE|SPEECHES|ADDRESSES|AUTOBIOGRAPHY")
# 传记式（题名里的人＝传主，与作者无关）—— 明确排除，不参与判定
BIO = r"LIFE|MEMOIR|MEMOIRS|BIOGRAPHY|IN\s+MEMORIAM|PROCEEDINGS"

# ★★★ 本工具的核心原则：**指控要严，开脱可以宽。**
#
#   我一度把 FLAG 侧的 `OF` 也改成可选，好让 `THE WRITINGS THOMAS JEFFERSON`
#   （OCR 吃掉了 OF）被认成「自己的书」。结果是正文/目录里每一个
#   WRITINGS・LETTERS・PAPERS 都成了题名构式，**误报 4 → 61**
#   （`CHAPTER Invasion Canada`、`I I`、`Appendix No. I.`、`Swan's Song My Ex-`）。
#
#   放松只允许出现在 SELF 侧：它**只会少报，不会多报**。
#   FLAG 侧一律要求显式的 OF／BY／de／di／von ＋ ≥2 个名字词。

# ── FLAG 侧（指认「题名里的人不是他」）：严 ──
# ★ `de-von`（`Briefe von …`）已整个撤出本侧：全批一条真阳性没抓到，
#   只贡献了两条噪声（`Schriften von a 1 Profeſſor`、`Briefe von 21ufana |Z69`）。
#   它仍留在 SELF 侧的 KW_ANY 里——在那边它只会开脱，不会指控。
PATTERNS = [
    ("en", re.compile(r"\b(?:THE\s+)?(?:%s)\b\s+(?:OF|BY)\s+(.{0,90})" % EN, re.I | re.S)),
    ("de-gen", re.compile(r"([A-ZÄÖÜ][A-Za-zäöüß.\- ]{2,40}?)\s*['’]?s\s+"
                          r"(?:s[äa]m{1,2}t?liche|gesammelte|ausgew[äa]hlte|kleine|vorz[üu]gliche)?\s*"
                          r"(?:Werke|Schriften)\b", re.S)),
    ("fr", re.compile(r"\b[ŒOEœoe]{1,2}uvres\s+(?:compl[eè]t{1,2}es\s+)?d[eu]\s+(.{0,60})",
                      re.S | re.I)),
    ("it", re.compile(r"\bOpere\s+(?:complete\s+)?di\s+(.{0,60})", re.S | re.I)),
]
BIO_RE = re.compile(r"\b(?:%s)\b\s*(?:OF|ON)\b" % BIO, re.I)

# ★★ 排版门：题名页是**排成大写的**，正文和目录不是。
#   实测把真阳性和噪声完全分开——`THE WRITINGS OF JAMES MONROE` 大写率 94%，
#   而 11 条噪声全落在 2–11%（`Letters of general Washington to the governors`、
#   `speeches of him who now addresses you`、`letters of credence to the respective Rectors`）。
#   只对英/法/意生效：德语题名页本来就是混合大小写（`Immanuel Kant's sämmtliche Werke`），
#   而 de-gen 的构式本身够紧（大写人名 ＋ 属格 ＋ Werke／Schriften），全批零噪声。
CAPS_GATED = {"en", "fr", "it"}
MIN_CAPS = 0.50


def caps_ratio(s: str) -> float:
    let = [c for c in s if c.isalpha()]
    return sum(c.isupper() for c in let) / len(let) if let else 0.0

# ── SELF 侧（认出「这书自印的就是他」）：宽 ──
# 集子类词（四语），目标姓氏出现在它前后 40 字内即算自称。
# 这一条同时覆盖三种真 OCR 写法：OF 被吃掉、连字 ŒUVRES、英语所有格 FROEBEL'S。
KW_ANY = (r"WRITINGS|WORKS|LETTERS|PAPERS|CORRESPONDENCE|SPEECHES|ADDRESSES|AUTOBIOGRAPHY"
          r"|Werke|Schriften|Briefe|uvres|Opere")


def self_named(head: str, target: re.Pattern) -> bool:
    t = target.pattern
    fwd = re.compile(r"(?:%s)\W[\w.,'’\- ]{0,40}?(?:%s)" % (KW_ANY, t), re.I | re.S)
    bwd = re.compile(r"(?:%s)[\w.,'’\- ]{0,40}?\W(?:%s)" % (t, KW_ANY), re.I | re.S)
    return bool(fwd.search(head) or bwd.search(head))

# 这些词一旦出现，人名到此为止（出版信息／体裁／功能词，四种语言）
NOT_NAME = set("""
the a an of and or by with in on to for from his her their its this that all some various
now first time printed collected complete chief educational classics series professor
university press sons street edition volume vol tome band including edited editor editors
rendered translated translation being containing comprising new york london paris leipzig
berlin boston philadelphia public private papers correspondence writings works letters
speeches addresses autobiography which what where when general state united states america
et de du des la le les un une il lo gli della di con par avec chez libraire editeur
der die das den dem ein eine und von nebst herausgegeben mit sämmtliche sämtliche gesammelte
""".split())


def named_person(tail: str) -> str:
    """从题名构式后面截出人名；截不出返回空串。

    ★ 硬要求 **≥2 个名字词**。三条实测误报全靠它挡：
      `Congress`（目录行）、`LOCKE. Edited by`（丛书广告）、`VOLTAIRE ET DE RACINE`（书商广告）
      各自都只剩 1 个词。
    ⚠ 已知盲区：题名页只印姓氏的错源抓不到，宁可漏不可吵。
    """
    t = re.sub(r"\s+", " ", tail).strip()
    toks = []
    for w in re.findall(r"[A-ZÄÖÜ][A-Za-zÄÖÜäöüßçéèêàìòù.\-']*", t)[:6]:
        if w.lower().strip(".") in NOT_NAME:
            break
        toks.append(w)
    return " ".join(toks) if len(toks) >= 2 else ""


def scan(text: str, target: re.Pattern) -> dict:
    # ★ 题名页必须先压平：真 OCR 是 `THE WRITINGS \n\n\n\nTHOMAS \n\n\n\nJEFFERSON`，
    #   带换行时 self_named 的间隔字符类一个都对不上（两份真语料夹具因此变红）。
    head = re.sub(r"\s+", " ", text[:HEAD])
    hits, names = [], []
    for kind, pat in PATTERNS:
        for m in pat.finditer(head):
            # 传记式构式跳过：LIFE OF X 的 X 是传主不是作者
            if BIO_RE.search(head[max(0, m.start() - 24):m.start() + 24]):
                continue
            if target.search(m.group(0)):
                continue
            if kind in CAPS_GATED and caps_ratio(m.group(0)[:56]) < MIN_CAPS:
                continue                    # 混合大小写 ⇒ 是正文/目录，不是题名页
            who = named_person(m.group(1))
            if who and not target.search(who):
                hits.append(re.sub(r"\s+", " ", m.group(0))[:80])
                names.append(who)
    return {"self_named": self_named(head, target), "other_names": names, "quotes": hits}


def verdict(text: str, target: re.Pattern) -> tuple[str, dict]:
    r = scan(text, target)
    if r["self_named"]:
        return "ok", r                      # 题名区提到了目标
    if not r["other_names"]:
        return "no-title", r                # 没有可判的题名构式（不是缺陷，是没证据）
    return "MISMATCH", r


SELF_TESTS = [
    # 正例：真事故（Jefferson 台账 ← Monroe 正文）
    ("MISMATCH", r"Jefferson",
     "HANDBOUND AT THE UNIVERSITY OF TORONTO PRESS\n\nTHE WRITINGS\n\nOF\n\nJAMES MONROE\n\n"
     "VOLUME I.\n\nINCLUDING A COLLECTION OF HIS PUBLIC AND PRIVATE PAPERS\n"
     "EDITED BY STANISLAUS MURRAY HAMILTON\n"
     "To Thomas Jefferson, Richmond, September 9th\n"),
    # 负例①：传记——马歇尔写的《华盛顿传》，题名主角本就是别人
    ("no-title", r"Marshall",
     "THE LIFE OF GEORGE WASHINGTON, COMMANDER IN CHIEF OF THE AMERICAN FORCES\n"
     "PHILADELPHIA: PRINTED BY C. P. WAYNE 1804\n"),
    # 负例②：目标在题名后半句（威廉一世与俾斯麦通信集）
    ("ok", r"Bismarck",
     "THE CORRESPONDENCE OF WILLIAM I. AND BISMARCK\nWITH OTHER LETTERS\nNEW YORK 1903\n"),
    # 负例③：德语属格，目标本人
    ("ok", r"Kant",
     "Immanuel Kant's sämmtliche Werke\nherausgegeben von G. Hartenstein\nLeipzig 1867\n"),
    # 负例④：法语，目标本人
    ("ok", r"Rousseau",
     "OEUVRES COMPLETTES DE J. J. ROUSSEAU\nTOME PREMIER\nA GENEVE 1782\n"),
    # 负例⑤：意语，目标本人
    ("ok", r"Machiavell",
     "OPERE DI NICCOLO MACHIAVELLI\nCITTADINO E SEGRETARIO FIORENTINO\nTOMO II\n"),
    # 负例⑥：构式后面是体裁/主题词，不是人
    ("no-title", r"Kant",
     "THE WORKS OF THE GERMAN PHILOSOPHERS\nA REFERENCE LIBRARY\nLondon\n"),
    # 负例⑦：纪念集（PROCEEDINGS … IN MEMORY OF）——传记式，不判
    ("no-title", r"Marshall",
     "PROCEEDINGS OF THE BAR IN MEMORY OF JOHN MARSHALL HARLAN\nDecember 16, 1911\n"),
    # 负例⑧：没有任何题名构式（OCR 掉了题名页）
    ("no-title", r"Lincoln",
     "CHAPTER I.\n\nThe early years were spent upon a farm in Kentucky, where the family\n"),
    # 正例②：德语属格指向别人
    ("MISMATCH", r"Pestalozz",
     "Johann Gottlieb Fichte's sämmtliche Werke\nBand I\nBerlin 1845\n"),
]


# ★★ 真语料夹具：上面十条是我手打的，**干净得不像 OCR**，
#    十条全绿的那一版在真文件上报了 3 条误报。这四条读真文件，不许再手打。
REAL_CASES = [
    ("MISMATCH", "wip-jefferson-175/workspaces/thomas-jefferson", "src-106864c12dfa",
     r"Jefferson", "台账说杰斐逊，正文印的是《门罗文集》第一卷"),
    ("ok", "wip-jefferson-175/workspaces/thomas-jefferson", "src-7e5b59c7c6af",
     r"Jefferson", "题名页 OCR 把 OF 吃了：THE WRITINGS THOMAS JEFFERSON"),
    ("ok", "wip-rousseau-178/workspaces/jean-jacques-rousseau", "src-5a6c67b00ba5",
     r"Rousseau", "真题名是连字 ŒUVRES；OEUVRES 那处是书商广告"),
    ("ok", "wip-frobel-181/workspaces/friedrich-frobel", "src-b9e8ee0a133a",
     r"Fr[oö]e?bel|Froebel", "真题名是所有格 FROEBEL'S；Locke 那处是丛书广告页"),
    # —— 下面六条是排版门／de-von 撤出之前报错的噪声，锁住不许回潮 ——
    ("not-MISMATCH", "wip-marshall-173/workspaces/john-marshall", "src-0de0c9013eb0",
     r"Marshall", "目录行 `Letters of general Washington to the governors`（大写率 4%）"),
    ("not-MISMATCH", "wip-lincoln-174/workspaces/abraham-lincoln", "src-aa53d1f400e4",
     r"Lincoln", "正文 `speeches of him who now addresses you`（大写率 2%）"),
    ("not-MISMATCH", "wip-machiavelli-177/workspaces/niccolo-machiavelli", "src-97742d71c132",
     r"Machiavell|Macchiavell", "正文 `letters of credence to the respective Rectors`（2%）"),
    ("not-MISMATCH", "wip-rousseau-178/workspaces/jean-jacques-rousseau", "src-c7701238aaa1",
     r"Rousseau", "副题 `Letters of two Lovers`——那是体裁不是人名（4%）"),
    ("not-MISMATCH", "wip-kant-179/workspaces/immanuel-kant", "src-66a095d80263",
     r"Kant", "`Schriften von a 1 Profeſſor in Koͤnigsberg`——匿名署名，正是他本人"),
    ("not-MISMATCH", "wip-pestalozzi-180/workspaces/johann-pestalozzi", "src-64aeef8c354a",
     r"Pestalozz", "Fraktur OCR 乱码 `Briefe von 21ufana |Z69 bis 3ur Derl^eiiatun^`"),
]


def self_test() -> int:
    bad = 0
    for want, pat, txt in SELF_TESTS:
        got, r = verdict(txt, re.compile(pat, re.I))
        ok = got == want
        bad += not ok
        print("%s want=%-9s got=%-9s %s" % ("✅" if ok else "❌", want, got,
                                            (r["other_names"] or ["—"])[0]))
    print("手打夹具 %d/%d" % (len(SELF_TESTS) - bad, len(SELF_TESTS)))

    root = pathlib.Path(__file__).resolve().parents[2] / "_corpora"
    print("\n—— 真语料夹具（%s）——" % ("在盘上" if root.exists() else "★ 不在盘上，本段跳过"))
    real = 0
    for want, ws, sid, pat, why in REAL_CASES:
        led = root / ws / "evidence" / "source-ledger.jsonl"
        if not led.exists():
            print("⏭  跳过 %s（语料不在本机）" % sid)
            continue
        rec = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines()
               if l.strip() and sid in l]
        if not rec:
            print("⏭  跳过 %s（台账里没有这一条）" % sid)
            continue
        f = root / ws / "raw" / pathlib.Path(rec[0]["local_path"]).name
        if not f.exists():
            print("⏭  跳过 %s（正文不在盘上）" % sid)
            continue
        got, _ = verdict(f.read_text(encoding="utf-8", errors="replace"),
                         re.compile(pat, re.I))
        # `not-MISMATCH`：只要求「不指控」——ok 与 no-title 都算过，
        # 因为这几份是否有可判的题名构式取决于扫描窗口，不该锁死。
        ok = (got != "MISMATCH") if want == "not-MISMATCH" else (got == want)
        bad += not ok
        real += 1
        print("%s want=%-9s got=%-9s %s ｜%s" % ("✅" if ok else "❌", want, got, sid, why))
    print("真语料夹具 %d 条" % real)
    print("\n合计不合 %d 处" % bad)
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--surname", help="目标姓氏正则，如 Fr[oö]e?bel")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.workspace and a.surname):
        ap.error("--workspace 与 --surname 都要给")

    W = pathlib.Path(a.workspace)
    tgt = re.compile(a.surname, re.I)
    rows, tally = [], {"ok": 0, "no-title": 0, "MISMATCH": 0}
    led = W / "evidence" / "source-ledger.jsonl"
    for r in (json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()):
        if not (r.get("tier") or "").startswith("P"):
            continue                       # 只判一手：它自称「他的著作」
        f = W / "raw" / pathlib.Path(r["local_path"]).name
        if not f.exists():
            continue
        v, d = verdict(f.read_text(encoding="utf-8", errors="replace"), tgt)
        tally[v] += 1
        if v == "MISMATCH":
            rows.append((r["source_id"], r.get("split", "?"), d["other_names"][0],
                         r["title"][:50], d["quotes"][0]))
    for s, sp, who, t, q in rows:
        print("MISMATCH %-22s %-8s 题名印的是「%s」｜台账「%s」\n         %s" % (s, sp, who, t, q))
    print("一手 %d 份：相符 %d ｜无题名构式 %d ｜**不符 %d**"
          % (sum(tally.values()), tally["ok"], tally["no-title"], tally["MISMATCH"]))
    return 1 if tally["MISMATCH"] else 0


if __name__ == "__main__":
    sys.exit(main())
