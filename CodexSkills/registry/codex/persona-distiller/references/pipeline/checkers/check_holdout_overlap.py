#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""holdout ↔ train **内容重合**检查 —— 硬门。

## 为什么成员级核对不够（Robertson #97 实战）

`check_material_split.py` 查的是**成员**：哪个文件在 train、哪个在 holdout、
有没有串目录。Robertson 一轮它报「holdout 泄漏 0」，**这个结论按它自己的判据是对的**。

而真实情况是：holdout 里的 `jr_2019_wb_medium_competitive_spirit.txt`
与 train 里的 `jr_2012_gd_issue15_management.txt` **是同一篇访谈**——
Columbia《Graham & Doddsville》2012 年春季号，2019 年被 Medium 转载。
文件名年份不同、URL 不同、source_id 不同，**成员级检查因此一路绿灯**。

用它出的 known 题不测泛化，测的是**同一段文字换个 source_id 我还认不认得**。
而这类题一定会得高分——于是评测分数虚高，且没有任何门会报警。

**成员对 ≠ 内容不重合。** 转载、合辑、同一次访谈的多处誊录，都会造成
「两个 source_id、一份内容」。这是抽 holdout 时最难自查的一种污染，
因为它在文件名、日期、域名三个维度上全都看不出来。

## 判据

对每个 holdout，与每个 train 源算 **shingle（连续 n 词）Jaccard 与覆盖率**：

- `覆盖率 = |holdout 的 shingle ∩ train 的 shingle| / |holdout 的 shingle|`
  —— 问的是「这份 holdout 有多少内容在 train 里已经有了」，**方向不能反**。
  用 Jaccard 会被长度差稀释：一份 1.5 万字的 holdout 完全包含在一份
  20 万字的 train 里，Jaccard 只有 0.07，而覆盖率是 1.0。

- 默认 `n=8`：短到能穿过誊录差异（标点、说话人标记、软连字符），
  长到不会被「the first thing is」这类通用短语误触发。

## 阈值

| 覆盖率 | 判定 |
|---|---|
| ≥ 0.30 | **✗ 硬失败**，该 holdout 必须换掉 |
| 0.10–0.30 | ⚠ 逐条人工核（可能是同一场活动的不同报道，也可能是真转载） |
| < 0.10 | ✓ |

低区间不设为失败：同一人的访谈天然共享大量措辞（他会反复讲同一个棒球类比），
把阈值压到 5% 会让每个人物都误报。**0.30 是「半篇以上重复」的保守线。**

## 样板噪声：本工具自己踩过的坑（Robertson #97，第一版就误报）

第一版对 2009 年那份 holdout 报 37.8% 硬失败，且**同时与三份不同的 train 源都是 37.8%**
——「与三份互不相干的文件重合度完全相同」本身就是仪器出错的signature。
查出来交集长这样：

    01 01 18 01 25 01 11 01
    05 11 04 27 05 04 04 20
    jim simons launched the quant revolution recommended reading

全是 marketfolly 的**月份归档侧栏与推荐阅读栏**。同站抓下来的任意两篇都共享它们。

**两条防线，都不靠维护站点黑名单**（黑名单换个站点就失效）：

① **纯数字 shingle 一律丢弃**——不含任何字母词的 n 元组永远不是内容。
② **文档频率过滤**：一个 shingle 若在 `df_max` 份以上的 train 源里都出现，
   按定义就是样板而非共享内容。**真转载在 train 里的 df 是 1**
   （只有被转载的那一份有它）。这一条是站点无关的。

**定则：判重之前先问「这段字在语料里出现了多少次」。出现得越普遍，越不是证据。**
"""
import argparse, json, pathlib, re, sys

N = 8
HARD, SOFT = 0.30, 0.10
# ★★★ 连续逐字段的两条线，**由全库 29 个工作区的实测分布定**
#   （见 `_ledgers/_holdout连续段全库分布-2026-08-11.md`）。
#
#   `RUN_WARN=50`：非样板的连续逐字段一到 50 词，就逐段落盘，**出评测题必须避开**。
#
#   `RUN_HARD_COUNT=50`：**按段数、不按长度**硬失败。为什么不按长度——实测：
#
#       Whitworth 最长 496 词 = Google 图书扫描声明（**样板**）
#       Lister   最长 215 词 = 他本人的换药指示（**真内容**）
#
#   **样板可以比内容长一倍以上**，所以长度分不开这两类。样板过滤（df）能滤掉一部分
#   （Whitworth 496→89、Blackstone 82→0、Thomson 66→0、Fleming 54→0），
#   但滤不干净：Whitworth 剩下的 89 词仍是 Google 的使用条款，
#   因为它只出现在他 2–3 份源里、够不着 `df_max`。而**把 df_max 压到 2 会连
#   Lister 这个真阳性一起杀掉**——他那段正好也在两份 train 源里。
#
#   → 工作区内的 df **原理上分不开**这两类。所以本件的产物是**逐段清单**，
#     它要被读；硬失败的判据因此是「**还读不读得完、避不避得开**」：
#     段数 ≥50 时人工避开不再可信（Lister 247 段 → ✗；Blackwell 40、
#     Holmes 17、Whitworth 1 → ⚠ 逐段读）。
RUN_WARN, RUN_HARD_COUNT = 50, 50
_WORD = re.compile(r"[a-z0-9']+")
_ALPHA = re.compile(r"[a-z]")
# ★★★ 连续段专用分词：**不含撇号**。
#   `_WORD` 把撇号算进词里（`plaintiffs'` 是一个词），这对 shingle 无所谓，
#   但对「连续多少词相同」是致命的：OCR 在两个印本上撒的游离撇号位置不同，
#   一个撇号就把一整段截成两段。Holmes #170 实测**同一段被量成 94 词，
#   换成本分词后是 136 词**——差 42 词，且方向是**低报泄漏**。
#   （与自测 ④ 的 M1 变异同类：低报比误报危险。）
#   `_WORD` 不动，因为覆盖率那一栏的历史行为不能改。
_RUN_WORD = re.compile(r"[a-z0-9]+")


def shingles(text: str, n: int = N) -> set:
    """★ 只保留「至少含 3 个字母词」的 n 元组。

    纯数字串（归档侧栏的日期列表、表格）在任何站点上都会造成同站文件间的高重合，
    而它们不携带任何内容信息。3 是经验值：允许 `$8 million in 1980` 这类
    数字与词混排的真内容，挡住 `01 01 18 01 25 01 11 01` 这类纯日期串。
    """
    w = _WORD.findall(text.lower())
    if len(w) < n:
        return set()
    out = set()
    for i in range(len(w) - n + 1):
        g = w[i:i + n]
        if sum(1 for x in g if _ALPHA.search(x)) >= 3:
            out.add(" ".join(g))
    return out


def body(path: pathlib.Path) -> str:
    """剥掉抓取包装：SOURCE_URL 行、站点导航、订阅语。

    **不剥会怎样**：同一个站点抓下来的两篇文章共享几百词的页眉页脚，
    于是同站的任意两篇都显示 20% 重合，真信号被站点模板淹没。
    """
    t = path.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"^SOURCE_URL:.*$", " ", t, flags=re.M)
    t = re.sub(r"skip to (main|sidebar)|market folly|Tracking top hedge funds"
               r"|About/Contact|New Hedge Fund Newsletter[^\n]*", " ", t, flags=re.I)
    return t


def runs(hold_words: list, train_words: list, n: int = N, cap: int = 64) -> list:
    """→ [(词数, train 侧起点, holdout 侧起点)]，两侧**连续逐字相同**的段，长的在前。

    ## ★★★ 为什么覆盖率不够——Holmes #170 实测

    覆盖率的分母是**整份 holdout**。Holmes 的 holdout 是 34.7 万片 shingle，
    而 train 里那本 1929 年 Vanguard 合辑有一节标题就叫
    `EXCERPTS FROM OTHER MAJORITY OPINIONS`，逐字转载了 holdout 卷次里的多数意见——
    **≥8 词的连续共有段 167 处、合计 3700 词（占 holdout 全文 1.04%）；
    其中 ≥50 词的 17 处，最长一段 136 词**。（两个口径要分开写——
    只给一个数等于替读者选了对自己有利的那档，[[counts-need-their-cutoff-stated]]。）

        覆盖率 = 0.0157 → 远低于 SOFT 0.10 → **这道门当时是绿的**。

    分母越大，绝对量再大的转载也压不动比值。**holdout 越大，比值门越瞎**
    （同一形态见 [[ratio-gates-can-be-passed-by-shrinking]]）。

    而评测题是**按段出的，不是按语料出的**：一段 136 词的逐字文字既在 holdout
    又在 train，用它出的题就不测泛化——**不管它占全份的百分之几**。
    所以这里量的是**绝对长度**，与 holdout 的大小无关。

    做法：holdout 的每个 n 元组记下**全部**出现位置（不是只记第一个——
    只记第一个会把重复出现的段量短，那是**低报泄漏**的方向），
    再从 train 侧逐个贪婪向后延伸取最长。`cap` 限制单个 n 元组的候选位置数，
    防止高频短语让复杂度爆掉。
    """
    idx = {}
    for i in range(len(hold_words) - n + 1):
        idx.setdefault(" ".join(hold_words[i:i + n]), []).append(i)
    out, i = [], 0
    while i <= len(train_words) - n:
        pos = idx.get(" ".join(train_words[i:i + n]))
        if not pos:
            i += 1
            continue
        best_len, best_j = 0, pos[0]
        for j in pos[:cap]:
            L = n
            while i + L < len(train_words) and j + L < len(hold_words) \
                    and train_words[i + L] == hold_words[j + L]:
                L += 1
            if L > best_len:
                best_len, best_j = L, j
        out.append((best_len, i, best_j))
        i += best_len
    out.sort(reverse=True)
    return out


BOILER_RUN_FRAC = 0.5

# ★★★ 2026-08-13 Dewey #190：**df 判样板在「只有两三份带它」时失效。**
#   JSTOR 的开卷声明（"Early Journal Content on JSTOR, Free to Anyone in the World"）
#   出现在全库 **148 份**语料的开头、跨 13 个工作区；但 Dewey 的 train 里只有 2 份带它，
#   df=2 太低 ⇒ 判成「内容重合」，报出 194 词的假重合。
#   ⇒ 补一层**字面识别**：数字化供方的固定声明，不管 df 多少一律算样板。
#   ★ 这是往**开脱侧**放松（[[loosen-only-the-exonerating-side]]），所以加一道约束：
#     声明本身必须**占到这一段的 BOILER_RUN_FRAC 以上**，
#     否则一段真内容里夹一句声明就会被整段放过。
PROVIDER_NOTICE = re.compile(
    r"early journal content on jstor"                      # JSTOR
    # ★ 连续段可能**从声明中间切起**（Dewey 实测两处 85 词就是这样），
    #   所以同一份声明的中段短语也要各写一条，不能只认开头那句。
    r"|known as the early journal content"
    r"|scholarly works digitized and made freely available"
    r"|jstor is a (?:digital library|not-for-profit)"        # JSTOR 机构简介（页脚那段）
    r"|this book is a digital copy of a work"              # Google 图书
    r"|digitized by (?:google|the internet archive)"
    r"|about google book search"
    r"|the project gutenberg (?:etext|ebook)"              # Project Gutenberg
    r"|produced by the online distributed proofreading"
    r"|this work is in the public domain in the united states"
    # ★★★ 2026-08-13：**Google「使用条款」那一段里有 `machine translation`。**
    #   量 Michelangelo #185 的语料里译本占多少时，扫「翻译」字样得 23/47=49%，
    #   而 13 处扉页命中里 **8 处是这一句**——每份 Google 扫描件都有，
    #   与这本书是不是译本毫无关系。真值 11/47=23%。
    #   ★ 它特别难防：不是 OCR 噪声，是干净的整句；每份都有；
    #     且用的就是领域词（translation / text / access / research）。
    r"|conducting research on machine translation"
    r"|optical character recognition or other areas"
    r"|access to a large amount of text is helpful"
    r"|please do not remove it|refrain from automated querying"
    # ★ 版权/权利套话里也有 `traduction`（法文书常见）
    r"|tous droits de (?:reproduction|traduction)"
    r"|all rights of (?:reproduction|translation) reserved",
    re.I)


def _provider_notice_share(text: str) -> float:
    """→ 供方声明在这段文字里占的字符比例（0..1）。**只认整段被声明淹没的情形。**"""
    if not text:
        return 0.0
    hit = sum(m.end() - m.start() for m in PROVIDER_NOTICE.finditer(text))
    if not hit:
        return 0.0
    # 声明是**整块**出现的：一旦命中，把命中点前后各 600 字符算进去更贴近实际，
    # 但**上限就是这一段本身**——不许算出 >1。
    return min(1.0, (hit + 600 * len(PROVIDER_NOTICE.findall(text))) / len(text))


def _is_boiler_run(train_words: list, run, boiler: set, n: int = N) -> bool:
    """这一段连续文字是**样板**还是**内容**？

    ## ★★★ 为什么不能只看长度（2026-08-11 全库实测，29 个工作区）

    在「覆盖率 <0.10、旧门全绿」那一组里，**最长的几段几乎都不是内容**：

    | 工作区 | 最长段 | 那段是什么 |
    |---|---|---|
    | joseph-whitworth | **496 词** | Google 图书的扫描声明 |
    | joseph-lister | 215 词 | **真内容**（换药手法） |
    | elizabeth-blackwell | 193 词 | **真内容**（法条原文） |
    | oliver-wendell-holmes-jr | 136 词 | **真内容**（转载的意见正文） |
    | william-blackstone | 82 词 | 题名页 |
    | elihu-thomson | 66 词 | **本流水线自己写的溯源头** |
    | alexander-fleming | 54 词 | 出版社简介 |

    **样板可以比内容长得多**——496 > 215。所以阈值再怎么调也分不开这两类，
    分它们的**不是长度，是「这段字在本工作区出现了几次」**：
    扫描声明、题名页、溯源头会出现在同一工作区的多份源里，
    而真转载只出现在被转载的那一份里（df == 1）。这正是本件文件头写的那条定则。

    第一版把它写成「抽样中**有一处**不是样板就保留」——太松，
    上表里 496／82／66 三段全被放过。改成**按比例**：
    整段的 n 元组里有 ≥`BOILER_RUN_FRAC` 落在样板集里，判为样板。
    """
    seg = " ".join(train_words[run[1]:run[1] + run[0]])
    # ★ 先看字面：命中已知供方声明且声明占了这一段的多数 ⇒ 样板（不依赖 df）
    if _provider_notice_share(seg) >= BOILER_RUN_FRAC:
        return True
    grams = [" ".join(train_words[run[1] + k:run[1] + k + n])
             for k in range(0, run[0] - n + 1)]
    if not grams:
        return False
    return sum(1 for g in grams if g in boiler) / len(grams) >= BOILER_RUN_FRAC


def check(ws: pathlib.Path, cache: list[pathlib.Path]) -> int:
    led = [json.loads(l) for l in (ws / "evidence/source-ledger.jsonl")
           .read_text(encoding="utf-8").splitlines() if l.strip()]
    files = {}
    for d in cache:
        for p in d.rglob("*.txt"):
            files.setdefault(p.name, p)

    def locate(r):
        # ★★ v0.0.0.68：**原本按 `locator` 的最后一段当文件名找。**
        #   而本流水线的 locator 是「篇名｜出处｜URL」，切出来是 URL 的尾巴——
        #   Nightingale #112 实测 117 条**一条也定位不到**，判据只会说「无法判定」。
        #   **这就是它从未跑通、也没人发现的原因**：它只存在于
        #   `references/pipeline/checkers/`，而把门的是 `scripts/`，所以从没被调用过。
        #   改用 `local_path`（与其余判据一致），并按两种账本布局解析。
        lp = r.get("local_path")
        if lp:
            for b in (ws, ws.parent):
                if (b / lp).is_file():
                    return b / lp
            hit = files.get(pathlib.Path(lp).name)
            if hit:
                return hit
        return files.get((r.get("locator") or "").rsplit("/", 1)[-1])

    tr = [(r["source_id"], locate(r)) for r in led if r.get("split") == "train"]
    ho = [(r["source_id"], locate(r)) for r in led if r.get("split") == "holdout"]
    miss = [s for s, p in tr + ho if p is None]
    if miss:
        print(f"✗ 找不到正文的源 {len(miss)} 条：{miss[:4]} —— 无法判定，**不算通过**")
        return 2
    if not ho:
        print("✗ 账本里没有 holdout —— 无法判定")
        return 2

    tr_sh = {s: shingles(body(p)) for s, p in tr}

    # ★ 文档频率过滤：在 df_max 份以上 train 源中都出现的 shingle 是**站点样板**，
    #   不是共享内容。真转载在 train 里只有一份，df == 1。
    #   这一条站点无关——不需要为每个新站点维护 strip 规则。
    df_max = max(3, len(tr) // 10)
    df = {}
    for t in tr_sh.values():
        for g in t:
            df[g] = df.get(g, 0) + 1
    boiler = {g for g, c in df.items() if c > df_max}
    tr_sh = {s: t - boiler for s, t in tr_sh.items()}
    print(f"train {len(tr)} 份 / holdout {len(ho)} 份，n={N} 连续词")
    print(f"样板过滤：出现在 >{df_max} 份 train 源中的 shingle 共 {len(boiler)} 个，已剔除\n")
    hard = soft = n_pass = 0
    for s, p in ho:
        hs = shingles(body(p)) - boiler
        if not hs:
            print(f"  ? {s} 剔除样板后正文过短，测不了"); continue
        best = sorted(((len(hs & t) / len(hs), ts) for ts, t in tr_sh.items()),
                      reverse=True)[:3]
        cov, top = best[0]
        mark = "✗" if cov >= HARD else ("⚠" if cov >= SOFT else "✓")
        hard += cov >= HARD
        soft += HARD > cov >= SOFT
        print(f"  {mark} {s}  {p.name[:52]}")
        for c, ts in best:
            if c >= 0.01:
                print(f"        与 {ts} 覆盖 {c:.1%}")
        if cov < 0.01:
            print(f"        最高覆盖 {cov:.2%}（与 {top}）")

    # ── ★ 第二把尺子：**连续逐字段的绝对长度**（比值门看不见的那一种，见 runs()）──
    tr_w = {s: _RUN_WORD.findall(body(p).lower()) for s, p in tr}
    longest = 0
    passages = {}
    for s, p in ho:
        hw = _RUN_WORD.findall(body(p).lower())
        rows = []
        for ts, tw in tr_w.items():
            rs = [r for r in runs(hw, tw) if r[0] >= RUN_WARN]
            rs = [r for r in rs if not _is_boiler_run(tw, r, boiler)]
            if rs:
                rows.append((rs[0][0], len(rs), ts, rs))
        rows.sort(reverse=True)
        if not rows:
            print(f"  ✓ {s} 最长连续逐字段 < {RUN_WARN} 词")
            continue
        top = rows[0][0]
        cnt_all = sum(r[1] for r in rows)
        longest = max(longest, top)
        n_pass += cnt_all
        mark = "✗" if cnt_all >= RUN_HARD_COUNT else "⚠"
        print(f"  {mark} {s} **最长连续逐字段 {top} 词**"
              f"（≥{RUN_WARN} 词的段共 {cnt_all} 处）")
        for mx, cnt, ts, rs in rows[:3]:
            print(f"        与 {ts}：最长 {mx} 词、{cnt} 处｜"
                  f"「{' '.join(tr_w[ts][rs[0][1]:rs[0][1] + 12])}…」")
        passages[s] = [{"words": r[0], "train_source": ts,
                        "text_head": " ".join(tr_w[ts][r[1]:r[1] + 20])}
                       for mx, cnt, ts, rs in rows for r in rs]
    # ★★ 报告**每次都写**，哪怕是空的。
    #   原来写成 `if passages:`——2026-08-13 Dewey #190 当场撞上：
    #   修好样板识别之后本轮判定是「无内容重合」，而磁盘上**还留着上一轮那条 72 词**，
    #   一份写着「出题必须避开这些段」的清单与当前判定互相矛盾，
    #   读的人无从知道该信哪个。[[stale-artifacts-from-my-machine-leak-into-the-build]]
    out = ws / "reports/holdout-contaminated-passages.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(passages, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    if passages:
        print(f"\n  ★ 受污染段已逐段落盘：{out.relative_to(ws)}"
              f"——**出评测题时必须避开这些段**")
    else:
        print(f"\n  ★ 无受污染段；{out.relative_to(ws)} 已**写成空**"
              f"（不留上一轮的旧清单）")

    print(f"\n硬失败 {hard} / 待人工核 {soft}")
    if n_pass >= RUN_HARD_COUNT:
        print(f"✗ **非样板的连续逐字段 {n_pass} 处 ≥ {RUN_HARD_COUNT}（最长 {longest} 词）**"
              f"\n  ——多到无法逐段避开，该 holdout 必须换掉。"
              f"\n  覆盖率那一栏看不见这件事：分母是整份 holdout，绝对量再大也压不动比值。")
        return 1
    if n_pass:
        print(f"⚠ **非样板的连续逐字段 {n_pass} 处（最长 {longest} 词）**"
              f"\n  ——逐段读清单，**出评测题必须避开这些段**；避不开就换 holdout。")
    if hard:
        print("✗ 有 holdout 的内容已在 train 中出现——**必须换源**。"
              "\n  用它出的 known 题不测泛化，且一定得高分。")
        return 1
    if soft:
        print("⚠ 有中等重合，逐条核完再往下走（同场活动的不同报道可接受，转载不可）")
    elif not n_pass:
        print("✓ 无内容重合")
    # ★ `n_pass > 0` 时**不许再印「✓ 无内容重合」**：上一行刚说有 17 处受污染段，
    #   下一行盖一个绿章，读的人只会记住绿章。[[empty-default-swallows-unknown]]
    return 0


def self_test() -> int:
    """负对照：构造的重复必须抓到，无关文本必须放过。"""
    a = "the quick brown fox jumps over the lazy dog and then keeps running far away"
    dup = shingles(a)
    print("══ 负对照 ══")
    ok1 = len(dup & shingles(a + " extra tail words here")) / len(dup) >= HARD
    b = "an entirely different sentence about markets and interest rates in the year"
    ok2 = len(dup & shingles(b)) / len(dup) < SOFT
    print(f"  {'✓' if ok1 else '✗'} 重复文本被抓到")
    print(f"  {'✓' if ok2 else '✗'} 无关文本被放过")

    # ── runs()：连续逐字段 ──
    fails = []

    def chk(label, got, want):
        print(f"  {'✓' if got == want else '✗'} {label}"
              + ("" if got == want else f"  得 {got!r} 应为 {want!r}"))
        if got != want:
            fails.append(label)

    para = ("the common law is not a brachylogous system but grows by the "
            "slow accretion of decisions each of which is a compromise between "
            "the felt necessities of the time and the received tradition of the "
            "past and no general proposition can settle a concrete case for the "
            "line has to be drawn somewhere between the extremes that everyone "
            "admits and the point at which reasonable men will differ in their "
            "judgment of degree").split()
    noise = ("an entirely unrelated discussion of tariffs and freight rates in "
             "the several states during the same period").split()
    # ① 正对照：整段逐字转载必须量到**整段的长度**
    r1 = runs(noise + para + noise, ["prelude"] + para + ["tail"])
    chk("① 60+ 词整段 → 量到整段", r1[0][0] if r1 else 0, len(para))
    # ② 反对照：不相干文本一段都不许有
    chk("② 不相干文本 → 无连续段", runs(noise, "wholly different words about "
                                    "chemistry and metallurgy here".split()), [])
    # ③ 反对照：**换行方式不同不许影响判定**（真语料两侧折行必然不同；
    #    夹具若两侧折行一样，就是 [[fixtures-cleaner-than-the-real-thing]]）
    wrapped = _RUN_WORD.findall("\n".join(" ".join(para[i:i + 7])
                                      for i in range(0, len(para), 7)).lower())
    chk("③ 折行不同 → 仍量到整段", (runs(para, wrapped) or [(0,)])[0][0], len(para))
    # ★★★ ④ 反对照：**同一段在 holdout 里出现两次，而第一次被截断**。
    #    只记第一个出现位置的实现会报 8 词（= 低报泄漏），必须报整段。
    hold2 = para[:N] + ["INTERRUPTED"] + noise + para
    chk("④ 首次出现被截断 → 不许低报", (runs(hold2, para) or [(0,)])[0][0], len(para))
    # ★★★ ⑤b 反对照：**一侧多一个 OCR 游离撇号，不许把连续段截断**。
    #    含撇号的分词在 Holmes #170 上把 136 词的段量成 94 词（低报泄漏）。
    dirty = list(para)
    dirty[len(para) // 2] = dirty[len(para) // 2] + "'"
    chk("⑤b 游离撇号 → 仍量到整段",
        (runs(para, _RUN_WORD.findall(" ".join(dirty))) or [(0,)])[0][0], len(para))
    # ⑤ 正对照：**线本身要能分档**——刚好够 RUN_WARN 的段不算硬失败
    chk("⑤ 两条线都为正且段数线可达", RUN_WARN > 0 and RUN_HARD_COUNT > 0, True)

    # ── _is_boiler_run：样板段与内容段 ──
    # ★ 这一对是**成对**的：只测「样板被丢掉」而不测「内容被留下」，
    #   一个恒返回 True 的实现也能全绿（[[counter-example-red-can-be-coincidence]]）。
    boiler_set = {" ".join(noise[k:k + N]) for k in range(len(noise) - N + 1)}
    long_boiler = (noise * 6)[:60]
    chk("⑥ 样板段（多份源共有）→ 判为样板",
        _is_boiler_run(long_boiler, (len(long_boiler), 0, 0), boiler_set), True)
    chk("⑥b **内容段 → 不许判成样板**",
        _is_boiler_run(para, (len(para), 0, 0), boiler_set), False)
    # ⑥c 边界：**样板占少数时必须留下**（否则真内容会被样板过滤吃掉）。
    #   ★ 这里有个反直觉的点，写下来免得下次又算错：
    #     「一半词数」不等于「一半 n 元组」——**跨接缝的 n 元组一个都不是样板**，
    #     所以 60 词样板 + 60 词内容实测只有 39/113 = 0.345 是样板。
    #     我第一版把这条的预期写成「判为样板」，红的是预期不是实现。
    chk("⑥c 样板占少数 → 不许判成样板",
        _is_boiler_run(long_boiler[:24] + para, (24 + len(para), 0, 0), boiler_set), False)

    # ── ★★ 供方声明：df 太低时字面识别必须顶上（2026-08-13 Dewey #190 真例）──
    #   那段逐字取自 raw/…/Knowledge and Speech Reaction 的开头，
    #   全库 148 份语料带它，而 Dewey 的 train 里只有 2 份 ⇒ df=2，df 法判不出来。
    jstor = ("stop early journal content on jstor free to anyone in the world this "
             "article is one of nearly 500000 scholarly works digitized and made "
             "freely available to everyone in the world by jstor known as the early "
             "journal content this set of works include research articles news "
             "letters and other writings published in more than 200 of the oldest "
             "leading academic journals").split()
    chk("★ JSTOR 开卷声明必须判成样板——**即使 df 只有 2**（df 法在这里失效）",
        _is_boiler_run(jstor, (len(jstor), 0, 0), set()), True)
    chk("★ 反向：真内容不许因为「没命中声明」以外的理由被放过",
        _is_boiler_run(para, (len(para), 0, 0), set()), False)
    # ★ 开脱侧放松要有约束：一段真内容里**夹一句**声明，不许整段被放过
    mixed = jstor[:12] + para * 3
    chk("★★ 真内容里夹一句声明：**不许**整段判成样板（声明占比不到一半）",
        _is_boiler_run(mixed, (len(mixed), 0, 0), set()), False)
    mid = ("known as the early journal content this set of works include research "
           "articles news letters and other writings published in more than 200 of "
           "the oldest leading academic journals the content covers a range of "
           "areas including business history political science").split()
    chk("★ 从声明**中间**切起的段（Dewey 实测 85 词那两处）也必须判成样板",
        _is_boiler_run(mid, (len(mid), 0, 0), set()), True)
    foot = ("individuals early journal content jstor is a digital library of academic "
            "journals books and primary source objects jstor helps people discover use "
            "and build upon a wide range of content through a powerful research and "
            "teaching platform and preserves this content for future generations").split()
    chk("★ JSTOR **页脚机构简介**（Dewey 剩下那处 72 词）也必须判成样板",
        _is_boiler_run(foot, (len(foot), 0, 0), set()), True)
    chk("Google 图书扫描声明同样认得",
        _is_boiler_run("this book is a digital copy of a work that has been preserved".split(),
                       (11, 0, 0), set()), True)

    # ══════════════════════════════════════════════════════════════════════
    # ⑦ ★★★ `check()` 本身 —— **在 2026-08-12 之前，这个函数从没被自测进入过**
    # ══════════════════════════════════════════════════════════════════════
    #
    # 上面 ①–⑥ 验的全是**配料**（shingles / runs / _is_boiler_run），
    # 而 `check()` 才是分 train/holdout、套阈值、**出判决**的那一段。
    # 用 `sys.settrace` 逐件量过：89 件判据里 37 件有函数从没被自测进入，本件是其一。
    #
    # ★ 利害最大的一条在 `locate()` 里：它的注释自己写着
    #   「**这就是它从未跑通、也没人发现的原因**」（Nightingale #112 实测 117 条
    #   一条也定位不到，判据只会说「无法判定」）——**修好之后仍然没有自测**。
    #
    # ★★ 而 `check()` 的输出正是待裁定 ㊲ 的全部依据
    #   （七个已入库人物 holdout 与 train 整段逐字重复）。**判决所依赖的函数没有对照。**
    #
    # ★★★ `selftest_touches_disk` 也看不见本件：它取 `fns.get("main")`，
    #   而本文件用的是内联 `if __name__` 块（全库 3 件如此）——见 check_checkers 那条已记的盲区。
    import contextlib as _ctx, io as _io, tempfile as _tmp

    def _run_check(ws, cache):
        """跑 check() 并吞掉它的正常输出，只取返回码。"""
        buf = _io.StringIO()
        with _ctx.redirect_stdout(buf):
            rc = check(ws, cache)
        return rc, buf.getvalue()

    def _mkws(td, rows, files, sub="evidence"):
        ws = pathlib.Path(td) / "ws"
        (ws / sub).mkdir(parents=True, exist_ok=True)
        (ws / sub / "source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8")
        for rel, text in files.items():
            p = ws.parent / rel if rel.startswith("..") else ws / rel
            p = pathlib.Path(str(p).replace("../", ""))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return ws

    # 造语料：三段互不相干的词流，长度都远超 RUN_WARN(50) 与 N(8)
    def _words(tag, k):
        return " ".join(f"{tag}word{i:03d}" for i in range(k))
    SHARED = _words("shared", 200)      # 会被逐字转载的那一段
    UNIQ_A = _words("alpha", 200)
    UNIQ_B = _words("bravo", 200)
    BOILER = _words("boiler", 120)      # 多份 train 共有 ⇒ 应被样板过滤剔除

    with _tmp.TemporaryDirectory() as td:
        cache = [pathlib.Path(td) / "cache"]
        cache[0].mkdir(parents=True, exist_ok=True)

        # ⑦a ★ locate() 的三种布局都必须解析得到（这是那次事故的原样）
        (cache[0] / "byname.txt").write_text(UNIQ_B, encoding="utf-8")
        ws = _mkws(td, [
            {"source_id": "t-rel", "split": "train", "local_path": "raw/t1.txt"},
            {"source_id": "t-parent", "split": "train", "local_path": "sib/t2.txt"},
            {"source_id": "h-basename", "split": "holdout", "local_path": "nowhere/byname.txt"},
        ], {"raw/t1.txt": UNIQ_A, "../sib/t2.txt": SHARED})
        rc, out = _run_check(ws, cache)
        chk("⑦a locate 三种布局（ws 相对 / ws.parent 相对 / cache 按文件名）全部解析",
            "找不到正文的源" not in out, True)
        chk("⑦a′ 无关 holdout → 判通过", rc, 0)

        # ⑦b ★★ 定位不到时**必须报「无法判定，不算通过」**，绝不许静默返回 0
        ws = _mkws(td + "/b", [
            {"source_id": "t1", "split": "train", "local_path": "raw/t1.txt"},
            {"source_id": "h1", "split": "holdout", "local_path": "raw/ghost.txt"},
        ], {"raw/t1.txt": UNIQ_A})
        rc, out = _run_check(ws, cache)
        chk("⑦b 有源定位不到 → rc=2（无法判定），不是 0", rc, 2)

        # ⑦c 账本里没有 holdout → 同样是「无法判定」，不是「没问题」
        ws = _mkws(td + "/c", [
            {"source_id": "t1", "split": "train", "local_path": "raw/t1.txt"},
        ], {"raw/t1.txt": UNIQ_A})
        rc, out = _run_check(ws, cache)
        chk("⑦c 账本无 holdout → rc=2，不是 0（[[empty-default-swallows-unknown]]）", rc, 2)

        # ⑦d 负对照：holdout 是某份 train 的逐字转载 → 硬失败
        ws = _mkws(td + "/d", [
            {"source_id": "t1", "split": "train", "local_path": "raw/t1.txt"},
            {"source_id": "t2", "split": "train", "local_path": "raw/t2.txt"},
            {"source_id": "h1", "split": "holdout", "local_path": "raw/h1.txt"},
        ], {"raw/t1.txt": UNIQ_A, "raw/t2.txt": SHARED, "raw/h1.txt": SHARED})
        rc, out = _run_check(ws, cache)
        chk("⑦d holdout 是 train 的逐字转载 → rc=1", rc, 1)
        chk("⑦d′ 且点名了是哪一份 train", "t2" in out, True)

        # ⑦e ★★★ **样板过滤不许把真内容一起吃掉**——这是「两个错抵消」的入口：
        #   若 df 阈值算错，样板与真重复会一起被剔除，于是**转载也报绿**。
        rows = [{"source_id": f"t{i}", "split": "train", "local_path": f"raw/t{i}.txt"}
                for i in range(6)]
        rows.append({"source_id": "h1", "split": "holdout", "local_path": "raw/h1.txt"})
        files = {f"raw/t{i}.txt": BOILER + " " + _words(f"filler{i}", 150) for i in range(6)}
        files["raw/t3.txt"] = BOILER + " " + SHARED          # 只有 t3 含真内容
        files["raw/h1.txt"] = BOILER + " " + SHARED          # holdout = 样板 + 真转载
        ws = _mkws(td + "/e", rows, files)
        rc, out = _run_check(ws, cache)
        chk("⑦e 样板被剔除后**真转载仍须抓到** → rc=1", rc, 1)
        chk("⑦e′ 且指的是 t3（不是任意一份共享样板的源）", "t3" in out, True)

        # ⑦f 正对照：六份 train 共享样板、holdout 只有样板 → **不许**报硬失败
        files["raw/h1.txt"] = BOILER + " " + _words("clean", 150)
        ws = _mkws(td + "/f", rows, files)
        rc, out = _run_check(ws, cache)
        chk("⑦f holdout 只与 train 共享样板 → 不许判硬失败", rc, 0)

    return 0 if (ok1 and ok2 and not fails) else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--cache", nargs="+", type=pathlib.Path, default=[])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if not a.workspace or not a.cache:
        ap.error("--workspace 与 --cache 必填（除非 --self-test）")
    sys.exit(check(a.workspace, a.cache))
