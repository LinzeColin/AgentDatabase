#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**逐字 ≠ 他的**：引文确实在语料里，可它是别人说的。

## 起因（Whitworth #152，**是候选子代理查出来的，不是任何一道门**）

断言 `clm-e120a051a8ad` 引这一句当作他本人的推测语气：

    "I think it not improbable that good cast iron would stand the test shdwn."

而语料里它前后是这样的（`src-548b27e71548`，逐字）：

    Referring to the experiment of the discharge of powder in a closed
    steel cylinder, which had been made before him, General
    Lefroy stated : —

    "I think it not improbable that good cast iron would stand the
    test shdwn."

    Although I was perfectly aware that cast iron is
    incapable of standing such a test, I, nevertheless …

**那是 General Lefroy 的话**，而他紧接着说的是**相反的意思**。

★★ `check_quote_integrity` 放行了它，而且放行是对的：**那句话逐字确实在语料里。**
  它问的是「在不在」，**不问「是谁说的」**。这两个问题不是同一个，
  而整条流水线此前只问了前一个。

## 它查什么，不查什么

**查**：产物正文与 `evidence/claims.jsonl` 里 ≥ MIN_QUOTE 字符的长逐字引文，
在 train 语料里定位，往回看 LOOKBACK 字符，若命中「<姓名> <转引动词> :「引号」」
这类**显式转引标记**，且那个姓与本人物的姓对不上 → 报。

**射程（必须连着说，别人才知道绿了代表什么）**：

- 只认**英文**转引标记，只认下面那张动词表；
- 只往回看 260 字符；再往前的转引**抓不到**；
- **无标记的间接引语一概抓不到**（「他附议了前一位发言人的说法，即……」）；
- 只比**姓**，不比名——同姓者抓不出来（[[test-the-guard-against-this-persons-namesake]]）；
- **定位不到的引文单列一节，那是「未判」，不是「通过」**。

## 为什么只吃 train 语料

holdout 的正文按设计不许出现在产物里；拿 holdout 去定位引文，
等于把隔离墙上开一个洞。**定位不到就老实报定位不到。**

## ★★★★ 扩到研究道之后的**第一次全库实测**（2026-08-10，18 个工作区）

| | |
|---|---|
| 长逐字引文 | **432 条** |
| **引到别人的话** | **0 条** |
| 在语料里定位不到（**未判，不是通过**） | **22 条** |
| 带省略号、分段逐条都在同一源里（引文是真的，只是判不了说话人） | 8 条 |

★★★★ **402 那个数是我加错的**：逐工作区的表是对的（25+29+26+86+14+12+7+57+53+13+22+28+30+30），
**我心算成了 402，真值 432**，而且它已经写进了一次提交信息。
[[self-reported-numbers-must-be-computed]]——**列都在眼前了还是要让机器加。**

★ 「定位不到」由 29 降到 22，降的那 7 条不是修好了文档，是**本件补上了省略号分段定位**：
带 `…` 的引文此前一律落进「定位不到」，而 `check_lane_quotes_verbatim.verify`
早就按 `…` 分段验了——**同一批引文在两件判据下一绿一红，是两件判据的口径没对齐。**

逐工作区：Carver 86／Mendel 57／Nasmyth 53／Whitworth 30／Thomson 30／Bessemer 29／
Rosenhain 28／Blackwell 26／Adams 25／RA 22／Coffin 14／Pasteur 13／Koch 12／Lister 7。
（Benardos／Liebig／Martens／Semmelweis 各 0 条——它们还没有产物或研究道正文。）

★ **「0 条引错」不等于引文都对。** 本件的射程写在上面：
只认英文转引标记、只往回看 260 字符、只比姓、抓不到无标记的间接引语。
**它只说明「这一类没抓到」。**

★★ **29 条「定位不到」是真缺口**，分两种：
① 抄自未入库来源（索引页、目次页）——**未定位就不该当逐字引文用**，Nasmyth 与 Carver 已按此处理；
② 判据的投影层看不见的形态。**两种都要人去分，不许当成通过。**
"""
import argparse
import glob
import json
import pathlib
import re
import sys

# ★★★★ 2026-08-10：归一**复用 `check_quote_integrity`，不另写一套**。
#   本件原先只做逐字 `find`，于是全库报「25 条定位不到」，
#   而拿 Adams #131 的一条去问既有判据：**投影后与长 s 折叠后都命中**——
#   **它在语料里，只是我的定位太粗。**
#   今天已经为「重复造轮子」付过一次代价（我造了一件仓里早有的镜像判据），
#   **同一天不再犯第二次**：能复用就复用。
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from check_quote_integrity import proj as _qi_proj, fold_s as _qi_fold   # noqa: E402
except Exception:                                                            # noqa: BLE001
    _qi_proj = _qi_fold = None

# 显式转引的动词表。**加词要有实例**，不许凭想象扩。
_VERBS = (r"stated|said|wrote|remarked|observed|reported|replied|"
          r"answered|adds?|writes?|says?|continued|declared")

# ★ 姓名允许跨行：真语料里就是 `General\nLefroy stated : —`
#   （`General` 在行末、`Lefroy` 在下一行行首）。
#   第一版我写的是 `\s+` 之外只允许空格，**那条真夹具一条都匹配不到**。
ATTR = re.compile(
    r"\b((?:[A-Z][A-Za-z.'\-]+)(?:[ \t]*\n?[ \t]*[A-Z][A-Za-z.'\-]+){0,3})[ \t\n]+"
    r"(?:" + _VERBS + r")[ \t]*[:：][ \t]*[—\-]*[ \t\n]*[\"“«„]",
    re.M)

LOOKBACK = 260          # 往回看多少字符找转引标记
MIN_QUOTE = 40          # 短于这个的引文不查（噪声太大）

# 断词折行：`incapa-\nble` / `incapa¬\nble`
_HYPHEN_BREAK = re.compile(r"[-¬][ \t]*\n[ \t]*")
_WS = re.compile(r"\s+")
_CJK = re.compile(r"[㐀-䶿一-鿿]")

# 产物正文里的长逐字引文。★★ **本项目的引文主要用反引号**——
#   实测 Whitworth #152：反引号 33 条、双引号 8 条（而那 8 条全是中文块，被 CJK 过滤掉）。
#   第一版我只写了双引号，于是 33 条一条没抓到，抓到的 2 条还是 SKILL.md 里的代码块。
#   ★ 每一个分支都**不许跨行**（`[^\n]`）：跨行就会把代码围栏整段吞进来。
_QUOTED = re.compile(
    r"`([^`\n]{%(n)d,400})`"
    r"|\"([^\"\n]{%(n)d,400})\""
    r"|“([^”\n]{%(n)d,400})”"
    r"|「([^」\n]{%(n)d,400})」" % {"n": MIN_QUOTE})

# 建模者读得到的产物正文（与 quality_check.RENDER_FILES 对齐）。
# ★ 不扫 SKILL.md / README.md：那两份是操作说明，里面的代码块不是引文。
RENDER_FILES = ('facts.md', 'cognitive-os.md', 'decision-policy.md', 'strategy.md',
                'capabilities.md', 'persona.md', 'work.md', 'boundaries.md',
                'hypotheses.md', 'divergence-map.md')


def _string_values(obj):
    """递归吐出一个 JSON 值里所有的字符串**值**（不含键）。"""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _string_values(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _string_values(v)


def _quoted_texts(blob: str):
    """把 `_QUOTED` 的多分支还原成一串引文正文。"""
    for m in _QUOTED.finditer(blob):
        for g in m.groups():
            if g:
                yield g
                break


# 产物正文里的 Markdown 强调。**剥掉再去语料里找**，否则一条都定位不到。
# ★★★★ 2026-08-10 实测：本件第一版没有这一步，于是 Koch #107 报「11 条引文里 10 条定位不到」、
#   Pasteur #106 报 9 条。去读命中才看见，那些引文里嵌着 `**粗体**`：
#   `mit **Sputum von Phthisikern**, mit Tuberkelmassen …`
#   ——**产物没问题，是我的判据拿着带标记的串去逐字比对**。
#   两人的产物都**已入库**，我差一点把这 19 条报成「已交付产物里的引文核不了」。
#   [[read-the-hits-before-reporting-the-rate]]；`check_lane_quotes_verbatim` 早有这一步。
_EMPH = re.compile(r"\*\*|__|\*(?=\S)|(?<=\S)\*")


_APOSTROPHE = re.compile(r"[\u2018\u2019\u201b\u02bc\u00b4]")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?)\]])")


def norm(s: str) -> str:
    """折行断词接回来，剥掉 Markdown 强调，空白压平。**定位用这一版，报数用原文。**

    ★★★★ 2026-08-10：**撇号与「标点前空白」两条是从 `check_lane_quotes_verbatim` 移植的。**
      这是**今天第四次**撞上「两件判据看同一批文本、口径各写各的」：
        · 省略号分段（本件缺）
        · 行内反引号提取（那件缺）
        · 中日韩标点／表格行／URL 过滤（本件缺）
        · **撇号与标点前空白归一（本件缺）** ← 这一条
      ★★ **这一条移植过来之后实测 0 变化**（定位不到仍是 19 条）——
        我以为会修好的那几条（如 Rosenhain 的 `Prof. Perry's plea` vs 语料 `Prof. Perry’s`）
        **早就被下面的投影兜底接住了**。
        **仍然保留**：口径对齐是为了不让两件判据将来再分叉，
        但**不能把它记成一次修复**——它现在没修好任何一条。
      ★ 与那件一致：**只动排印，不动字母**。
    """
    s = _WS.sub(" ", _EMPH.sub("", _HYPHEN_BREAK.sub("", s))).strip()
    s = _APOSTROPHE.sub("'", s)
    return _SPACE_BEFORE_PUNCT.sub(r"\1", s)


def is_cjk_heavy(s: str, ratio: float = 0.15) -> bool:
    """中文占比超过 ratio 就不当英文引文查。

    ★ 不加这一条会怎样：第一版把 SKILL.md 里的中文结构串
      （流水线箭头、优先级链）当成引文抓了一把，全是假阳。
    """
    return bool(s) and len(_CJK.findall(s)) / len(s) > ratio


def surname_of(name: str) -> str:
    """取姓：末位那个词。**只比姓是有意的**，射程已在文件头写明。"""
    toks = [t for t in re.split(r"\s+", norm(name)) if t]
    return toks[-1].lower().strip(".'-") if toks else ""


_URLISH = re.compile(r"^(?:https?://|www\.|/|\./|[A-Za-z]:\\)|\.(?:txt|md|json|jsonl|pdf|html?)$", re.I)


_CJK_PUNCT = re.compile(r"[《》「」『』，、。；：？！（）【】]")
_TABLE_ROW = re.compile(r"^\s*\|")


def _not_a_quote(t: str) -> bool:
    """URL、路径、索引行**不是引文**——扩清单进研究道之后才冒出来的一类噪声。

    ★★★★ 2026-08-10：把研究道并进清单，引文从 31 条涨到 53 条，
      其中混进了这些（它们同样被反引号括着）：

        `https://archive.org/details/practicalessays00nasmgoog`
        `Nasmyth, James … Manufacturing Engineer from Manchester, 290`   ← 索书索引行

      它们当然在语料里定位不到，于是**冒充「未判」那一节的问题**——
      这与 `check_lane_quotes_verbatim` 里记过的
      「`proceedingsofiow07iowa.txt` 被当成引文报失败」是同一件事。
      **同一个坑在两件判据上各踩一次，说明它是「反引号即引文」这个假设本身的毛病。**

    判法（与那件保持一致的部分 + 本件特有的索引行）：
      · URL / 路径 / 文件名；
      · 没有空格、或整体只由 `[\w.\-/]` 组成的标识符；
      · **索引行**：逗号分隔且以页码收尾（`…, 290`），且不含句号句读。
    """
    t = t.strip()
    # ★★★★ 2026-08-10：**这三条是从 `check_lane_quotes_verbatim` 移植过来的。**
    #   同一天我在那件判据上加了它们，**本件一条都没有**——
    #   于是同一批字符串在两件判据下一个被滤掉、一个被当成「定位不到的引文」。
    #   **今天第三次撞上「两件判据的口径没对齐」**（前两次：省略号分段、行内反引号）。
    #   实测本件因此虚报的：Bessemer 2 条（`《The Times》…，落款`）、
    #   Blackwell 1 条（表格行 `| P1 | …`）、Roberts-Austen 2 条、Whitworth 1 条（索引行）。
    if _CJK_PUNCT.search(t):        # 带中日韩标点 → 是我写的散文，不是英文逐字引文
        return True
    if _TABLE_ROW.match(t):         # Markdown 表格行
        return True
    if _URLISH.search(t):
        return True
    if " " not in t or re.fullmatch(r"[\w.\-/]+", t):
        return True
    # 索引行：`姓, 名 … 说明, 页码`——**以数字收尾且通篇无句号**
    if re.search(r",\s*\d{1,4}$", t) and "." not in t:
        return True
    return False


_ELISION_RE = re.compile(r"\s*(?:\.\.\.|…)\s*")


def load_corpus(ws: pathlib.Path) -> list:
    """**只读 train**（`references/sources/`），holdout 一律不进来。"""
    out = []
    for f in sorted(glob.glob(str(ws / "references/sources/**/*.txt"), recursive=True)):
        out.append((f, pathlib.Path(f).read_text(encoding="utf-8", errors="replace")))
    return out


def collect_quotes(ws: pathlib.Path) -> list:
    """产物正文 + claims.jsonl 里的长逐字引文 → [(出处, 引文原文, **所处那段正文**)]

    ★ 第三项是给「正文有没有自己署上真说话人」用的，见 `check()`。
    """
    got, seen = [], set()
    # ★★★★ 2026-08-10：**研究道文档此前不在这张清单里。**
    #   同一天 `check_holdout_mention` 刚因为同一个毛病被扩过清单
    #   （它当时只扫十份产物，而研究道是建模者读得最多的一类）。
    #   本件是**系统审计**找出来的第二例，不是又撞上的：
    #   做法是「把所有带硬编码文件清单的判据列出来，逐个问它扫的是不是它保证的全部」。
    #
    #   ★ 为什么研究道必须进来：Nasmyth #153 的六份研究道里有 **33 条逐字引文**，
    #     `check_lane_quotes_verbatim` 查过它们「是不是逐字」，
    #     **但从来没有人查过「这话是不是他说的」**——
    #     而那两件事是独立的：一句逐字抄自语料的话，完全可能是**别人在他的书里说的**。
    #   ★★ 出处名保持带路径（`research/01-writings.md`），
    #     这样报出来时**一眼看得出是产物还是研究道**，两类的处置不一样。
    scan_files = [(n, ws / n) for n in RENDER_FILES]
    scan_files += [(f"research/{p.name}", p)
                   for p in sorted((ws / "references" / "research").glob("*.md"))]
    for label, p in scan_files:
        if not p.is_file():
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        for para in body.split("\n\n"):          # 段为单位，引文的上下文就在同一段里
            for q in _quoted_texts(para):
                q = q.strip()
                if (len(q) >= MIN_QUOTE and not is_cjk_heavy(q)
                        and not _not_a_quote(q) and q not in seen):
                    seen.add(q)
                    got.append((label, q, para))
    cj = ws / "evidence/claims.jsonl"
    if cj.is_file():
        for line in cj.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:                                    # noqa: BLE001
                continue
            # ★★★★ **不许 `json.dumps` 之后再正则。**
            #   实测：那样做的话 JSON 自己的 `"` 就成了引号，
            #   **每一个 ≥40 字符的字段值都会被当成一条「引文」**——
            #   Whitworth 上因此多出一条以 `**答问先把东西端出来…` 开头的假引文，
            #   它当然在语料里定位不到，于是又混进「未判」那一节冒充问题。
            #   逐个字符串值提取，JSON 的定界符就永远不会露面。
            for val in _string_values(row):
                for q in _quoted_texts(val):
                    q = q.strip()
                    if len(q) >= MIN_QUOTE and not is_cjk_heavy(q) and q not in seen:
                        seen.add(q)
                        got.append((f"claims.jsonl:{row.get('claim_id', '?')}", q, val))
    return got


def speaker_before(corpus_text: str, at: int) -> str:
    """定位点往回 LOOKBACK 字符里**最靠近**的那个转引标记的姓名。

    ★★★★ **转引在哪里关掉，必须一起判。** 真语料实测（同一段 Lefroy）：

        General Lefroy stated : —
        "I think it not improbable that good cast iron would stand the test shdwn."
        Although I was perfectly aware that cast iron is incapable of …

    第一句是 Lefroy 的，**第二句是 Whitworth 自己接着说的**——
    可它离那个转引标记也在 260 字符之内。只按「往回找标记」判，
    **他本人的话会被判成别人的**，而且报出来的样子跟真事故一模一样。

    判法：转引标记本身以**开引号**结尾；若从标记末尾到定位点之间
    出现过**闭引号**，说明那段转引已经关掉，此处已经回到叙述者。
    """
    lo = max(0, at - LOOKBACK)
    seg = corpus_text[lo:at]
    hits = list(ATTR.finditer(seg))
    if not hits:
        return ""
    m = hits[-1]
    if re.search(r"[\"”»“]", seg[m.end():]):     # 转引已闭合 → 不归给他
        return ""
    return m.group(1)


def check(quotes, corpus, subject: str) -> dict:
    """→ {引文数, 引到别人的话[], 定位不到[]}"""
    sub_sur = surname_of(subject)
    normed = [(f, norm(t)) for f, t in corpus]
    wrong, unlocated, declared, by_projection = [], [], [], []
    elided_ok = []   # 带省略号、分段都在同一源里、但首段太短判不了说话人
    for item in quotes:
        src, q = item[0], item[1]
        around = item[2] if len(item) > 2 else ""     # 引文在产物里所处的那段文字
        nq = norm(q)
        where = None
        for f, t in normed:
            i = t.find(nq)
            if i >= 0:
                where = (f, t, i)
                break
        if where is None:
            # ★★★★ 2026-08-10：**带省略号的引文此前一律落进「定位不到」。**
            #   Nasmyth #153 实测：7 条「定位不到」里 **5 条只是带了 `…`**——
            #     `It would be blamable indeed … were I to suppress the name of …`
            #     `devoting himself to astronomical … researches`
            #   `check_lane_quotes_verbatim.verify` 早就按 `…` 分段验了，**本件没有**，
            #   于是同一批引文在两件判据下一绿一红。**两件判据的口径必须自己对齐。**
            #
            #   ★ 用**第一段**去定位，不是最长的那段：
            #     本件接下来要往回看 260 字符找说话人标记，
            #     而那个标记在**引文开头之前**——锚到后面的段就找不到它了。
            #   ★★ 第一段仍要够长（`MIN_QUOTE`），否则短前缀会乱命中。
            segs = [x.strip() for x in _ELISION_RE.split(nq) if x.strip()]
            if len(segs) > 1:
                head = segs[0]
                if len(head) >= MIN_QUOTE:
                    for f, t in normed:
                        i = t.find(head)
                        if i >= 0:
                            where = (f, t, i)
                            break
                if where is None:
                    # ★★★★ **首段太短，判不了说话人——但那不等于「语料里没有」。**
                    #   只要**每一段都在同一份来源里、且顺序不乱**，这条引文就是真的；
                    #   缺的只是「往回看 260 字符找说话人标记」所需要的那个位置。
                    #   ★ 分开报：混进「定位不到」会把「判据够不着」说成「文档有问题」，
                    #     那正是 [[checker-blindspot-read-as-defect]] 记的那个形状。
                    long_segs = [x for x in segs if len(x) >= 12]
                    for f, t in normed:
                        pos, ok = 0, bool(long_segs)
                        for x in long_segs:
                            j = t.find(x, pos)
                            if j < 0:
                                ok = False
                                break
                            pos = j + len(x)
                        if ok:
                            elided_ok.append({"出处": src, "引文": q,
                                              "语料": pathlib.Path(f).name})
                            break
                    else:
                        pass
                    if elided_ok and elided_ok[-1].get("引文") == q:
                        continue
        if where is None:
            # ★ 兜底：既有判据的投影（抹平标点/markdown/引号形态）与长 s 折叠。
            #   命中就**不算「定位不到」**——但那一层没有位置可用，
            #   **该位置的说话人本件判不了**，所以单列，不混进「通过」。
            hit = False
            # ★★★★ **空投影匹配一切。** `check_quote_integrity.proj` 只保留字母数字，
            #   非拉丁文本（中文、纯标点串）投影后是**空串**，而 `"" in 任何串` 恒为真——
            #   于是「语料里根本没有」的句子会被兜底判成「找到了」。
            #   **这是我自己的反例抓到的**：加兜底之前那条是绿的，加完变红。
            #   下限 20：低于它的投影不足以证明是同一句。[[empty-default-swallows-unknown]]
            _MIN_PROJ = 20
            if _qi_proj is not None and len(_qi_proj(nq)) >= _MIN_PROJ:
                pq = _qi_proj(nq)
                fq = _qi_fold(pq) if _qi_fold else pq
                for _f, t in corpus:
                    pt = _qi_proj(t)
                    if pq in pt or (_qi_fold and fq in _qi_fold(pt)):
                        hit = True
                        by_projection.append({"出处": src, "引文": q,
                                              "语料": pathlib.Path(_f).name})
                        break
            if not hit:
                unlocated.append({"出处": src, "引文": q})
            continue
        f, t, i = where
        who = speaker_before(t, i)
        if who and surname_of(who) != sub_sur:
            rec = {"出处": src, "转引自": norm(who), "引文": q,
                   "语料": pathlib.Path(f).name}
            # ★★★★ **产物自己点了真说话人的名，就不是误引。**
            #   实测（Whitworth #152）：这条判据落地后报的第一条，
            #   指的是 `clm-e120a051a8ad` 的 `alternative_explanations`——
            #   **那一段正是记录「我曾误引 Lefroy」的事故记录本身**，
            #   原文白纸黑字写着「那是 General Lefroy 的话」。
            #   缺陷是「把别人的话当成他的」；正文既已署了真名，缺陷就不成立。
            #   ★ 这一条不是网开一面：**判据是「真说话人的姓在不在这段正文里」**，
            #     而不是「这个字段叫什么名字」——按字段名豁免才是可以被绕过的那种。
            if surname_of(who) and surname_of(who) in norm(around).lower():
                rec["已在正文里注明出自"] = norm(who)
                declared.append(rec)
            else:
                wrong.append(rec)
    return {"引文数": len(quotes),
            "**引到别人的话**": wrong,
            "★ 只在投影/长s折叠后才定位到的（在语料里，但本件判不了说话人）": by_projection,
            "★ 正文已注明出自他人的（不判为误引，但列出来）": declared,
            "★ 带省略号、分段都在同一源里（在语料里，但首段太短，说话人判不了）": elided_ok,
            "★ 在语料里定位不到的（本件未判，不是通过）": unlocated}


# ── 自测：真夹具，不是我编的 ─────────────────────────────────────────
_REAL_LEFROY = (
    "Referring to\nthe experiment of the discharge of powder in a closed\n"
    "steel cylinder, which had been made before him, General\nLefroy stated : —\n\n"
    "\"I think it not improbable that good cast iron would stand the\ntest shdwn.\"\n\n"
    "Although I was perfectly aware that cast iron is\nincapable of standing such a test, I, ")
# ↑ 逐字取自 `wip-whitworth-152/.../src-548b27e71548/miscellaneouspa01whitgoog_djvu.normalized.txt`

_REAL_BARTON = (
    "At the annual meeting, Miss  Barton  said:  \"I have never yet been able to "
    "realize that this work was mine, or that it was done by me.\"  The audience rose.")
# ↑ 反例：**主语自己被第三人称转引**——转引标记在，而姓与人物相同，不许报。


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★★★★ 真夹具①：Lefroy 的话被当成 Whitworth 的（**事故原件**）──")
    q = "I think it not improbable that good cast iron would stand the test shdwn."
    r = check([("facts.md", q)], [("src.txt", _REAL_LEFROY)], "Joseph Whitworth")
    chk(f"抓到了，转引自「{r['**引到别人的话**'][0]['转引自'] if r['**引到别人的话**'] else '—'}」",
        len(r["**引到别人的话**"]) == 1
        and surname_of(r["**引到别人的话**"][0]["转引自"]) == "lefroy")
    chk("★ 姓名跨行也认（真语料里 `General` 在行末、`Lefroy` 在下一行）",
        bool(ATTR.search(_REAL_LEFROY)))

    print("── ★★★ 同一段真语料里的**第二句**：转引已闭合，那是他自己的话 ──")
    q_own = "Although I was perfectly aware that cast iron is incapable of standing such a test"
    r1b = check([("facts.md", q_own)], [("src.txt", _REAL_LEFROY)], "Joseph Whitworth")
    chk("闭引号之后的叙述**不许**判给 Lefroy（否则真假两条长得一模一样）",
        len(r1b["**引到别人的话**"]) == 0
        and not r1b["★ 在语料里定位不到的（本件未判，不是通过）"])
    chk("★ 而闭引号**之前**那一句仍然要报（**修完没把真事故一起修没**）",
        len(check([("facts.md", q)], [("src.txt", _REAL_LEFROY)],
                  "Joseph Whitworth")["**引到别人的话**"]) == 1)

    print("── ★★★★ 真夹具③：**事故记录本身含有那句被误引的话** ──")
    #   下面这段逐字取自 `clm-e120a051a8ad` 的 `alternative_explanations`。
    #   它是**修好之后**的正文，专门在记录「我曾误引 Lefroy」这件事。
    #   判据落地后报的第一条就是它——**而它恰恰是已经改对了的那一条**。
    _REAL_INCIDENT = (
        "★★ 本条改过一次，是候选侧子代理主动报上来的：初稿引 "
        "`I think it not improbable that good cast iron would stand the test` "
        "当作他的推测语气，而那是 General Lefroy 的话——原文逐字为 "
        "`General Lefroy stated : —` 之后的引语。")
    r_inc = check([("claims.jsonl:clm-e120a051a8ad", q, _REAL_INCIDENT)],
                  [("src.txt", _REAL_LEFROY)], "Joseph Whitworth")
    chk("正文自己署了 `General Lefroy` → 不判为误引",
        len(r_inc["**引到别人的话**"]) == 0
        and len(r_inc["★ 正文已注明出自他人的（不判为误引，但列出来）"]) == 1)
    chk("★★ 而把那段正文里的署名去掉，**同一条立刻变回误引**（豁免不是网开一面）",
        len(check([("claims.jsonl:x", q, "他当时推测铸铁也许扛得住这个试验。")],
                  [("src.txt", _REAL_LEFROY)], "Joseph Whitworth")["**引到别人的话**"]) == 1)

    print("── ★★ 反例①：**同一个人被第三人称转引，不许报** ──")
    q2 = "I have never yet been able to realize that this work was mine, or that it was done by me."
    r2 = check([("persona.md", q2)], [("src.txt", _REAL_BARTON)], "Clara Barton")
    chk("`Miss Barton said:` + 引文 → 0 条（姓对得上）",
        len(r2["**引到别人的话**"]) == 0 and not r2["★ 在语料里定位不到的（本件未判，不是通过）"])
    print("── ★ 正例：同一段语料，换一个人物就必须报 ──")
    r2b = check([("persona.md", q2)], [("src.txt", _REAL_BARTON)], "Florence Nightingale")
    chk("同一条引文、人物换成 Nightingale → 报 1 条（**反例红得不是凑巧**）",
        len(r2b["**引到别人的话**"]) == 1)

    print("── ★★ 反例②：**没有转引标记就不许猜** ──")
    plain = ("The committee met in May. \"I have found the tensile strength to be "
             "twenty-seven tons per square inch upon the section.\" This was recorded.")
    r3 = check([("facts.md", "I have found the tensile strength to be twenty-seven "
                 "tons per square inch upon the section.")],
               [("src.txt", plain)], "Joseph Whitworth")
    chk("无标记 → 0 条（**不报，也不算通过；这一类本件抓不到，已写在射程里**）",
        len(r3["**引到别人的话**"]) == 0)

    print("── ★★ 反例③：**定位不到必须单列，不许混进「通过」** ──")
    r4 = check([("facts.md", "A sentence that appears nowhere in the corpus at all, forty plus.")],
               [("src.txt", _REAL_LEFROY)], "Joseph Whitworth")
    chk("定位不到 → 进「未判」那一节，且不进「引到别人的话」",
        len(r4["★ 在语料里定位不到的（本件未判，不是通过）"]) == 1
        and len(r4["**引到别人的话**"]) == 0)

    print("── ★ 反例④：中文结构串不许当英文引文抓 ──")
    chk("中文占比 >15% 判为非英文引文",
        is_cjk_heavy("抓源 → ingest → 质检 → 盲判 → 打包 → 入库，共六步不可跳") is True)
    chk("纯英文不误判", is_cjk_heavy(_REAL_BARTON) is False)

    print("── ★ 折行断词接得回来 ──")
    chk("`incapa-\\nble` → `incapable`", norm("incapa-\nble of standing") == "incapable of standing")

    print("── ★★★★ 真夹具④：引文里嵌着 `**粗体**`（Koch #107 的形态）──")
    #   逐字取自 `wip-koch-107/.../facts.md`，语料侧是同一句没有标记的德文。
    _koch_q = "mit **Sputum von Phthisikern**, mit Tuberkelmassen von"
    _koch_corpus = "Impfungen mit Sputum von Phthisikern, mit Tuberkelmassen von Rindern"
    chk("剥掉强调后定位得到（此前 Koch 11 条里 10 条报「定位不到」，全是这个原因）",
        not check([("facts.md", _koch_q)], [("s.txt", _koch_corpus)],
                  "Robert Koch")["★ 在语料里定位不到的（本件未判，不是通过）"])
    chk("★ 而**真的不在语料里**的仍要报定位不到（剥标记没把这道门剥没）",
        len(check([("facts.md", "**这一句语料里根本没有，四十个字符以上，用于反例**")],
                  [("s.txt", _koch_corpus)], "Robert Koch")
            ["★ 在语料里定位不到的（本件未判，不是通过）"]) == 1)
    chk("★ 乘号/脚注星号不许被当成强调剥掉（`3 * 4` 里的空格星号保留）",
        norm("the ratio 3 * 4 held") == "the ratio 3 * 4 held")

    print("── ★★★★ 真夹具②：**本项目的引文用反引号**（第一版漏掉的正是这一族）──")
    import tempfile                                              # noqa: PLC0415
    real_line = ("这一条的原话：`These surfaces were got up without grinding. "
                 "The only operations performed upon them were planing and scraping.`")
    # ↑ 引文正文逐字取自 wip-whitworth-152 的 `evidence/claims.jsonl`
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td)
        (w / "facts.md").write_text(real_line, encoding="utf-8")
        # 反例同时布下：SKILL.md 里的代码围栏**不许**被当成引文
        (w / "SKILL.md").write_text("```bash\npython3 scripts/run.py --result-path <文件> ...\n```\n",
                                    encoding="utf-8")
        qs = collect_quotes(w)
        chk(f"反引号长引文抓得到（{len(qs)} 条）",
            len(qs) == 1 and qs[0][1].startswith("These surfaces were got up"))
        chk("★ SKILL.md 的代码围栏没被当成引文（**不扫它，且每个分支都禁跨行**）",
            all("scripts/run.py" not in x[1] for x in qs))
        # ★ 反例：真有一条跨行的东西摆在 RENDER_FILES 里，也不许抓
        (w / "work.md").write_text("```\nfoo bar baz qux quux corge grault garply waldo fred\n```\n",
                                   encoding="utf-8")
        chk("RENDER_FILES 里的代码围栏同样不抓（禁跨行这一条真的在起作用）",
            len(collect_quotes(w)) == 1)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="人物工作区")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not a.target:
        ap.error("给一个工作区，或 --self-test")

    ws = pathlib.Path(a.target)
    meta = json.loads((ws / "meta.json").read_text(encoding="utf-8"))
    subject = str(meta.get("name") or "")
    corpus = load_corpus(ws)
    quotes = collect_quotes(ws)
    r = check(quotes, corpus, subject)

    if a.json:
        # ★ `--json` 只印 JSON。混印散文会让调用方的 json.loads 抛，
        #   而抛出来的后果是「这项检查静默变成 0 条」——同一个坑今天已经踩过一次。
        print(json.dumps(r, ensure_ascii=False))
        return 1 if r["**引到别人的话**"] else 0

    print(f"人物 {subject}；train 语料 {len(corpus)} 份；长逐字引文 {r['引文数']} 条")
    if r["**引到别人的话**"]:
        print(f"\n✗ **{len(r['**引到别人的话**'])} 条引文是别人说的**（逐字在语料里，但转引自他人）：")
        for x in r["**引到别人的话**"]:
            print(f"  · {x['出处']}　转引自 **{x['转引自']}**")
            print(f"    「{x['引文'][:90]}」")
    else:
        print("✓ 没有引到别人的话")
    dec = r["★ 正文已注明出自他人的（不判为误引，但列出来）"]
    if dec:
        # ★ 不判为误引，**但一定要印出来**——不印就等于我替读者做了这个判断。
        print(f"\n★ 正文里已注明出自他人的：{len(dec)} 条（**不判为误引**）")
        for x in dec:
            print(f"  · {x['出处']}　正文自己署了 **{x['已在正文里注明出自']}**")
    bp = r["★ 只在投影/长s折叠后才定位到的（在语料里，但本件判不了说话人）"]
    if bp:
        print(f"\n★ 只在投影/长 s 折叠后才定位到的：{len(bp)} 条"
              f"（**它们在语料里**，但那一层没有位置，说话人本件判不了）")
    eo = r.get("★ 带省略号、分段都在同一源里（在语料里，但首段太短，说话人判不了）") or []
    if eo:
        print(f"\n★ 带省略号、分段逐条都在同一份来源里：{len(eo)} 条"
              "（**引文是真的**，缺的只是判说话人所需要的那个位置——"
              "**这一档不该混进「定位不到」**）")
        for x in eo[:6]:
            print(f"  · {x['出处']}：「{x['引文'][:72]}」")
    un = r["★ 在语料里定位不到的（本件未判，不是通过）"]
    if un:
        print(f"\n⚠ ★ 在语料里定位不到的（**本件未判，不是通过**）：{len(un)} 条")
        for x in un[:6]:
            print(f"  · {x['出处']}：「{x['引文'][:70]}」")
    print("\n★★ 射程：只认英文转引标记、只往回看 260 字符、只比姓、"
          "抓不到无标记的间接引语。**绿不代表引文都对，只代表这一类没抓到。**")
    return 1 if r["**引到别人的话**"] else 0


if __name__ == "__main__":
    sys.exit(main())
