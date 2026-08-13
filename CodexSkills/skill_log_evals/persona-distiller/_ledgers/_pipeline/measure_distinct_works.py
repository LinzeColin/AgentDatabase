#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""measure_distinct_works.py —— **这些源里有几部是同一本书**（重量一次，不信旧读数）

## 为什么要重量

流水线的 `raw/_dedup.json` 用 min-hash（8-gram、阈值 **0.55**）判重，**算在原样文本上**。
2026-08-14 实测：这把尺子被 OCR 噪声压过了。

    同一部书（Michelangelo 的 1875 Milanesi 书信集，四次数字化，6 对）
        原样      0.1521 – 0.2462     ← 门 0.55，**一对都过不了**
        狠归一后  0.2155 – 0.4254

    确定不同的两部
        Brandeis 1889《The Law of Ponds》 vs 1905《Life insurance》   0.0000 → 0.0000
        Michelangelo 书信集 vs 诗集                                   0.0002 → 0.0018

**归一化之后同书最低 0.2155、不同书最高 0.0018，相差 120 倍**，中间是一条极宽的空带。
⇒ 本件把文本先狠归一化再切 8-gram，阈值取 **0.05**（落在空带正中）。

## 它判不了什么（**必须一起念**）

1. **跨语言判不了。** 同一封信的原文与译文，归一化前后都是 **0.0000**。
   那一类只能在「同一次话语」这一层由人判（踩坑库
   `original-and-translation-are-one-utterance-with-zero-overlap`）。
2. **并查集有传递性 ⇒ 会高估。** 选集收录了单行本时，选集会把几部单行本串成一组
   （Rousseau 实测：`Contrat social` ↔ `Petits chefs-d'oeuvre` 0.2084，后者是选集）。
   所以本件**同时给出不传递的那个数**，两个数夹出真值区间。
3. **它不改任何门**，也不写 `_dedup.json`。只报数。
4. ★★ **在人工细读过的人身上，它的塌缩明显偏低。** 与 Blackwell #118 对照过：
   他的延后记录（**人工逐对认定**，95 份口径）记「独立作品 56 部、塌缩 **39**」，
   而本件 train 89 份只报塌缩 **13–25**。逐对量过分布，本件**确实抓到了**那些
   手稿/印本对（≥0.5 有 10 对，最高 0.9007；记录说它们重叠 51–90%），
   差在塌缩的记法与分母。⇒ **本件的数是下界，不是「已经去重干净了」。**

## 用法

    python3 measure_distinct_works.py --workspace <工作区>
    python3 measure_distinct_works.py --all            # 扫 _corpora 下所有有 train 语料的
    python3 measure_distinct_works.py --self-test

退出码：0＝跑完（**这不是一道门**，没有红绿）；4＝没读到任何正文（未量，不是通过）
"""
import argparse
import collections
import glob
import itertools
import json
import pathlib
import re
import sys
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces, layout_of  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"

# ★ 只留字母数字与常见重音字母：OCR 把 `e'` 打成 `e*`、把 `perdè` 打成 `perde`，
#   标点与变音记号是噪声最集中的地方，去掉它们同书的重叠才浮出来。
KEEP = re.compile(r"[^a-z0-9àâäçèéêëìíîïñòóôöùúûüßœ ]+")
NGRAM = 8
SAMPLE_MOD = 8          # 哈希抽样 1/8：省内存与时间，对 Jaccard 是无偏估计
DEFAULT_T = 0.05
# ★★ 2026-08-14 加：**Jaccard 一个人判不了「短文被收进文集」**。
#   分母是并集，|B| ≫ |A| 时哪怕 A 整个在 B 里，Jaccard 上限也只有 |A|/|B|。
#   实测 Brandeis 1907《Savings insurance》(727 个签名) 整篇被收进《Business—a
#   profession》(9738–11210)：**Jaccard 0.0349／0.0365／0.0396 —— 三对全在 0.05 门底下**，
#   而**包含率 0.5089／0.5488／0.5543**。旧版把这三对判成「不同作品」。
#   逐对量出来的空带（本工作区 6 正 6 负）：
#       同一次话语   包含率 0.5089 – 0.9445（含同书多次扫描）
#       不同作品     包含率 0.0000 – 0.1162（含两对同题材）
#   ⇒ 阈值取 **0.25**，是最坏负对照的 2.15 倍、最低正例的 0.49 倍。
#   ★ 已知弱点：|A| 很小时包含率抖（最坏那对负对照 |A|=241）；所以两条规则是**或**的
#     关系，且报里印出是哪条触发的，不把两种证据混成一个数。
CONTAIN_T = 0.25


def signature(text: str, ngram: int = NGRAM, mod: int = SAMPLE_MOD) -> set:
    """正文 → 抽样后的 8-gram 哈希集合。**纯函数**，自测不碰磁盘。"""
    t = KEEP.sub(" ", text.lower())
    w = t.split()
    out = set()
    for i in range(0, max(0, len(w) - ngram)):
        h = zlib.crc32(" ".join(w[i:i + ngram]).encode())
        if h % mod == 0:
            out.add(h)
    return out


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def containment(a: set, b: set) -> float:
    """**小的那一份有多少落在大的那一份里**。判「短文被收进文集」只能靠它。"""
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


def group_transitive(ids, pairs):
    """并查集（**会传递**）→ {id: 组号}。上界那一侧。"""
    par = {i: i for i in ids}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p in pairs:
        a, b = p[1], p[2]
        par[find(a)] = find(b)
    return {i: find(i) for i in ids}


def group_pairwise(ids, pairs):
    """**不传递**：按分数从高到低做贪心匹配 —— **每份源最多只与一份并一次**。

    ★★ 2026-08-14 改。原来写的是「每条边一个新组号 ＋ `setdefault`」，注释说
      「并到第一次出现的那一组」，**而代码并没有这么做**：边 (a,b)、(b,c) 里
      b 已归 g0，于是 c 拿到一个**新组号 g1 并且只有它自己**——一个被证据并过的源
      却被算成一部独立作品。后果是这个「上界」**加了合并证据反而变大**：
      2026-08-14 全库实测 **8 个工作区的上界不降反升**（Lister 46→47、Rousseau 73→75），
      而上界的定义就是「合并得最少时还剩几部」，只可能降不可能升。
      [[the-comment-states-the-rule-the-code-narrows-it]]

    改成贪心匹配后语义是明确的：**一份源只允许被一条边用掉**，
    于是 a-b-c 这条链只并 a-b，c 单独站着 ⇒ 2 组（传递口径是 1 组）。
    两个数仍然夹出区间，而上界这一侧不再自相矛盾。

    ★ 仍不保证严格单调：一条高分边可能占掉两个本可各自配对的点。所以 `measure()`
      把两个口径都返回，**报里从不只印一个数**。
    """
    used, g, n = set(), {}, 0
    for p in pairs:                      # pairs 已按分数降序
        a, b = p[1], p[2]
        if a in used or b in used:
            continue                     # ★ 每份源只被用掉一次
        g[a] = g[b] = f"g{n}"
        used.add(a)
        used.add(b)
        n += 1
    return {i: g.get(i, f"solo:{i}") for i in ids}


def measure(texts: dict, threshold: float = DEFAULT_T, contain_t: float = CONTAIN_T):
    """{id: 正文} → 报告 dict。**这一层不碰磁盘**，自测直接喂字符串。"""
    sig = {k: signature(v) for k, v in texts.items()}
    sig = {k: v for k, v in sig.items() if v}
    pairs = []
    for a, b in itertools.combinations(sorted(sig), 2):
        j = jaccard(sig[a], sig[b])
        c = containment(sig[a], sig[b])
        why = ("J" if j >= threshold else "") + ("C" if c >= contain_t else "")
        if why:
            pairs.append((max(j, c), a, b, j, c, why))
    pairs.sort(reverse=True)
    gt = group_transitive(list(sig), pairs)
    gp = group_pairwise(list(sig), pairs)
    return {
        "份数": len(sig),
        "达阈值的对数": len(pairs),
        "只有包含率抓到的对数": sum(1 for p in pairs if p[5] == "C"),
        "独立作品·传递（下界的作品数／上界的塌缩）": len(set(gt.values())),
        "独立作品·不传递（上界的作品数／下界的塌缩）": len(set(gp.values())),
        "阈值": threshold,
        "包含率阈值": contain_t,
        "对": pairs,
    }


# ══════════════════ 自测 ══════════════════

def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    base = ("the test of perceptible current is not a legal test it is both unpractical "
            "and unscientific perceptible in what degree it may be asked to the eye and to "
            "what eye to one of powerful or of weak refraction again must the water be "
            "perceived itself to move or a chip upon its surface ") * 40
    # ★ 同一部书的两次 OCR：标点/撇号不同，词一样
    ocr = base.replace("the test", "the te*st").replace("degree", "degr ee").replace("eye", "e'ye")
    other = ("the size of a life insurance company is no evidence of success it is evidence "
             "only of the extent to which the business has been pushed and of the amount of "
             "money which policy holders have paid in premiums ") * 40
    r = measure({"a": base, "b": ocr, "c": other})
    ja = jaccard(signature(base), signature(ocr))
    jc = jaccard(signature(base), signature(other))
    chk(f"★ 同书两次 OCR 的 Jaccard 明显高于阈值（实得 {ja:.4f}）", ja >= DEFAULT_T)
    chk(f"★ 反例：两部不同的书远低于阈值（实得 {jc:.4f}）", jc < DEFAULT_T)
    chk("★ 3 份 → 独立作品 2（同书两份并成一组）",
        r["独立作品·传递（下界的作品数／上界的塌缩）"] == 2)
    # ★ 反例：全是不同的书，一对都不该达阈值
    r2 = measure({"x": base, "y": other})
    chk("★ 反例：两份不同的书 → 达阈值 0 对、独立作品 2",
        r2["达阈值的对数"] == 0 and r2["独立作品·传递（下界的作品数／上界的塌缩）"] == 2)
    # ★★ 传递性：a↔b、b↔c 达阈值而 a↔c 不达 ⇒ 两个口径必须给出不同的数
    pairs = [(0.9, "a", "b"), (0.9, "b", "c")]
    gt = group_transitive(["a", "b", "c"], pairs)
    gp = group_pairwise(["a", "b", "c"], pairs)
    chk("★★ 传递口径把 a-b-c 并成 1 组（上界侧）", len(set(gt.values())) == 1)
    chk(f"★★ 不传递口径给出 **2** 组（下界侧；两个数夹出区间。实得 {len(set(gp.values()))}）",
        len(set(gp.values())) == 2)
    # ★★ 2026-08-14：上界**只可能降不可能升**。原实现会升（全库 8 个工作区实证）。
    few = [(0.9, "a", "b", 0.9, 0.9, "J")]
    more = [(0.95, "b", "c", 0.95, 0.95, "J"), (0.9, "a", "b", 0.9, 0.9, "J")]
    n_few = len(set(group_pairwise(["a", "b", "c", "d"], few).values()))
    n_more = len(set(group_pairwise(["a", "b", "c", "d"], more).values()))
    chk(f"★★ **加一条边，不传递口径的组数不许变多**（{n_few} → {n_more}）", n_more <= n_few)
    chk(f"★ 链 a-b-c：不传递只并一对，c 单独站着 ⇒ 3 组（含孤立的 d）（实得 {n_more}）",
        n_more == 3)
    # ★ 反例：一份源不许被两条边用掉
    two = [(0.9, "a", "b", 0.9, 0.9, "J"), (0.8, "a", "c", 0.8, 0.8, "J")]
    gg = group_pairwise(["a", "b", "c"], two)
    chk("★ 反例：a 已与 b 并过，第二条 a-c 不生效 ⇒ c 仍独立",
        gg["a"] == gg["b"] and gg["c"].startswith("solo:"))
    # ★ 跨语言：本件判不了，必须仍是 0 对（写进自测，免得下一个人以为它能）
    en = ("but ye have never understood me in the past and ye do not understand me now "
          "may god forgive you for he of his grace has allowed me to bear what i am bearing ") * 40
    it = ("ma voi non mavete mai conosciuto e non mi conosciete idio ve lo perdoni perchè "
          "lui mà fatto la grazia che io rega a quello che io rego ") * 40
    chk(f"★ **跨语言判不了**：同一句的原文与译文仍是 0 对（实得 {jaccard(signature(en), signature(it)):.4f}）",
        jaccard(signature(en), signature(it)) < DEFAULT_T)

    # ══ 包含率：短文被收进文集 ══（2026-08-14 Brandeis 1907 短文 ⊂《Business—a profession》）
    essay = base                                      # 727 量级的短文
    filler = (" ".join(f"unrelated filler sentence number {i} about wholly other matters "
                       f"with distinct vocabulary {i * 7}" for i in range(1, 900)))
    anthology = filler + " " + essay + " " + filler   # 文集：短文整篇在内，四周全是别的文章
    sa, sb = signature(essay), signature(anthology)
    j_ea, c_ea = jaccard(sa, sb), containment(sa, sb)
    chk(f"★★ **整篇被收进文集，Jaccard 反而在门底下**（实得 {j_ea:.4f} < {DEFAULT_T}）"
        f"——这正是旧版漏掉三对的原因", j_ea < DEFAULT_T)
    chk(f"★★ 同一处话语的**包含率**过门（实得 {c_ea:.4f} ≥ {CONTAIN_T}）", c_ea >= CONTAIN_T)
    r3 = measure({"essay": essay, "anth": anthology})
    chk(f"★★ 于是 2 份 → 独立作品 **1**（旧版会报 2）"
        f"（实得 {r3['独立作品·传递（下界的作品数／上界的塌缩）']}）",
        r3["独立作品·传递（下界的作品数／上界的塌缩）"] == 1)
    chk(f"★ 报里认得出是「只有包含率抓到的」（实得 {r3['只有包含率抓到的对数']}）",
        r3["只有包含率抓到的对数"] == 1)
    # ★★ 反例组：包含率不许把不同作品并起来
    c_no = containment(signature(other), sb)
    chk(f"★★ **反例：另一部书对文集的包含率必须在门下**（实得 {c_no:.4f} < {CONTAIN_T}）",
        c_no < CONTAIN_T)
    r4 = measure({"x": base, "y": other})
    chk(f"★★ **反例：加了包含率之后，两部不同的书仍是 0 对**"
        f"（实得 {r4['达阈值的对数']} 对）", r4["达阈值的对数"] == 0)
    # ★ 反例：一份很短的源不许因为「短」就被判进别人（本工作区最坏负对照 0.1162）
    tiny = "the water be perceived itself to move or a chip upon its surface " * 3
    c_tiny = containment(signature(tiny), signature(other))
    chk(f"★ 反例：极短的源 vs 无关的书 仍在门下（实得 {c_tiny:.4f}）", c_tiny < CONTAIN_T)
    # ★ 空签名不许除零
    chk("★ 反例：空集合 → 包含率 0.0，不抛异常",
        containment(set(), signature(other)) == 0.0 and containment(sa, set()) == 0.0)
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


# ══════════════════ 磁盘一侧 ══════════════════

def load_texts(ws: pathlib.Path):
    """→ ({id: 正文}, {id: 题名}, 读不到的份数)。**读不到要报出来，不当 0。**"""
    led = ws / "evidence/source-ledger.jsonl"
    if not led.is_file():
        return {}, {}, 0
    texts, titles, miss = {}, {}, 0
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if d.get("split") != "train":
            continue
        p = ws / str(d.get("local_path") or "")
        if not p.is_file():
            miss += 1
            continue
        texts[d["source_id"]] = p.read_text(encoding="utf-8", errors="replace")
        titles[d["source_id"]] = str(d.get("title"))[:44]
    return texts, titles, miss


def report(ws: pathlib.Path, threshold: float, top: int = 8,
           contain_t: float = CONTAIN_T, tally=None) -> int:
    texts, titles, miss = load_texts(ws)
    if not texts:
        if tally is not None:
            tally[3] += 1
        print(f"★ {ws.name}：**未量，不是通过** —— 读不到任何 train 正文"
              f"（台账指到的文件 {miss} 份不在本机；语料按裁定不进 git）")
        return 4
    r = measure(texts, threshold, contain_t)
    if tally is not None:
        tally[1] += 1
        tally[2] += r["份数"]
    old = ws / "raw/_dedup.json"
    o = json.loads(old.read_text(encoding="utf-8")) if old.is_file() else {}
    n, mh, bt = o.get("文件数"), o.get("独立文献数上界"), o.get("按题名归并的独立作品数")
    print(f"{ws.name}：train {r['份数']} 份"
          + (f"（另有 {miss} 份文件不在本机）" if miss else "")
          + f" → **独立作品 {r['独立作品·传递（下界的作品数／上界的塌缩）']}"
            f"–{r['独立作品·不传递（上界的作品数／下界的塌缩）']}**"
            f"（塌缩 {r['份数'] - r['独立作品·不传递（上界的作品数／下界的塌缩）']}"
            f"–{r['份数'] - r['独立作品·传递（下界的作品数／上界的塌缩）']}）")
    if isinstance(n, int):
        print(f"    旧读数（`_dedup.json`，原样文本、门 0.55）：{n} 份，"
              f"min-hash 塌缩 {n - mh if isinstance(mh, int) else '?'}，"
              f"按题名塌缩 {n - bt if isinstance(bt, int) else '?'}")
    conly = r["只有包含率抓到的对数"]
    if conly:
        print(f"    ★ 其中 **{conly} 对是只靠包含率抓到的**（Jaccard 在门底下）"
              f"——「短文被收进文集」这一类，旧版全判成不同作品")
    for _, a, b, j, c, why in r["对"][:top]:
        tag = {"J": "Jaccard", "C": "**只有包含率**", "JC": "两条都过"}[why]
        print(f"      J={j:.4f} 包含={c:.4f} [{tag}]  "
              f"{titles.get(a,'')[:34]:36s} ↔ {titles.get(b,'')[:34]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--threshold", type=float, default=DEFAULT_T)
    ap.add_argument("--contain-threshold", type=float, default=CONTAIN_T)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(f"★ 尺子：狠归一化 ＋ {NGRAM}-gram ＋ 抽样 1/{SAMPLE_MOD}；"
          f"**两条规则取或** —— Jaccard ≥ {a.threshold}（同书实测 0.2155–0.4254／不同书 ≤0.0018）"
          f"**或** 包含率 ≥ {a.contain_threshold}（同话语 0.5089–0.9445／不同作品 ≤0.1162）")
    print("★ **跨语言判不了**（原文 vs 译文恒 0.0000）；并查集会因选集串组而高估，"
          "所以两个口径都印出来。\n")
    if a.workspace:
        return report(pathlib.Path(a.workspace), a.threshold, contain_t=a.contain_threshold)
    if a.all:
        rc = 0
        _seen = [0, 0, 0, 0]   # [找到, 量到, train 份数, 未量]
        # ★★ 2026-08-14：原来这里是 `glob(CORPORA/"wip-*"/"workspaces"/"*")`，
        #   **漏掉 8 个「名字重复一层」的工作区（train 778 份，占全库 28.5%）**，
        #   而且它们的正文一份不缺。当天我据此发的「全库 1950 份」是少算的。
        #   改成按台账定位（workspace_roots），三种布局都收得到。
        for d in iter_workspaces(CORPORA):
            _seen[0] += 1
            r = report(pathlib.Path(d), a.threshold, contain_t=a.contain_threshold,
                       tally=_seen)
            rc = rc or (0 if r in (0, 4) else r)
        # ★★ 2026-08-14：**印分母，不只印命中**。今天四次栽在「集合比实况小」，
        #   而每一次屏幕上都只有一个看着正常的数。这里把「量到多少／没量到多少」
        #   摆在最后一行，读的人才知道上面那些数是从多大的集合里出来的。
        print(f"\n★★ **覆盖面**：按台账找到工作区 **{_seen[0]}** 个｜"
              f"量到 **{_seen[1]}** 个（train **{_seen[2]:,}** 份）｜"
              f"**未量 {_seen[3]} 个**（读不到 train 正文——语料按裁定不进 git）")
        print("   ⇒ 上面每一行的「独立作品／塌缩」**只覆盖量到的那部分**；"
              "未量的不是「干净」，是**没被问到**。")
        return rc
    ap.error("要 --workspace 或 --all 或 --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
