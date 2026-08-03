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
_WORD = re.compile(r"[a-z0-9']+")
_ALPHA = re.compile(r"[a-z]")


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
    hard = soft = 0
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

    print(f"\n硬失败 {hard} / 待人工核 {soft}")
    if hard:
        print("✗ 有 holdout 的内容已在 train 中出现——**必须换源**。"
              "\n  用它出的 known 题不测泛化，且一定得高分。")
        return 1
    if soft:
        print("⚠ 有中等重合，逐条核完再往下走（同场活动的不同报道可接受，转载不可）")
    else:
        print("✓ 无内容重合")
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
    return 0 if (ok1 and ok2) else 1


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
