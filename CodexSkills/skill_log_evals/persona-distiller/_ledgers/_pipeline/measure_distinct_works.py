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

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"

# ★ 只留字母数字与常见重音字母：OCR 把 `e'` 打成 `e*`、把 `perdè` 打成 `perde`，
#   标点与变音记号是噪声最集中的地方，去掉它们同书的重叠才浮出来。
KEEP = re.compile(r"[^a-z0-9àâäçèéêëìíîïñòóôöùúûüßœ ]+")
NGRAM = 8
SAMPLE_MOD = 8          # 哈希抽样 1/8：省内存与时间，对 Jaccard 是无偏估计
DEFAULT_T = 0.05


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


def group_transitive(ids, pairs):
    """并查集（**会传递**）→ {id: 组号}。上界那一侧。"""
    par = {i: i for i in ids}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for _, a, b in pairs:
        par[find(a)] = find(b)
    return {i: find(i) for i in ids}


def group_pairwise(ids, pairs):
    """**不传递**：只把每条边的两端并到第一次出现的那一组。下界那一侧。

    与 `check_lane_distinct_works.work_groups()` 同一个理由——
    传递闭包曾把 32 份源串成一个分量并报出假警。
    """
    g = {}
    for n, (_, a, b) in enumerate(pairs):
        gid = f"g{n}"                 # ★ 每条边一个新组号
        g.setdefault(a, gid)          # ★ setdefault：**先到先得，不改归属** ⇒ 不传递
        g.setdefault(b, gid)
    return {i: g.get(i, f"solo:{i}") for i in ids}


def measure(texts: dict, threshold: float = DEFAULT_T):
    """{id: 正文} → 报告 dict。**这一层不碰磁盘**，自测直接喂字符串。"""
    sig = {k: signature(v) for k, v in texts.items()}
    sig = {k: v for k, v in sig.items() if v}
    pairs = []
    for a, b in itertools.combinations(sorted(sig), 2):
        j = jaccard(sig[a], sig[b])
        if j >= threshold:
            pairs.append((j, a, b))
    pairs.sort(reverse=True)
    gt = group_transitive(list(sig), pairs)
    gp = group_pairwise(list(sig), pairs)
    return {
        "份数": len(sig),
        "达阈值的对数": len(pairs),
        "独立作品·传递（下界的作品数／上界的塌缩）": len(set(gt.values())),
        "独立作品·不传递（上界的作品数／下界的塌缩）": len(set(gp.values())),
        "阈值": threshold,
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
    # ★ 跨语言：本件判不了，必须仍是 0 对（写进自测，免得下一个人以为它能）
    en = ("but ye have never understood me in the past and ye do not understand me now "
          "may god forgive you for he of his grace has allowed me to bear what i am bearing ") * 40
    it = ("ma voi non mavete mai conosciuto e non mi conosciete idio ve lo perdoni perchè "
          "lui mà fatto la grazia che io rega a quello che io rego ") * 40
    chk(f"★ **跨语言判不了**：同一句的原文与译文仍是 0 对（实得 {jaccard(signature(en), signature(it)):.4f}）",
        jaccard(signature(en), signature(it)) < DEFAULT_T)
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


def report(ws: pathlib.Path, threshold: float, top: int = 8) -> int:
    texts, titles, miss = load_texts(ws)
    if not texts:
        print(f"★ {ws.name}：**未量，不是通过** —— 读不到任何 train 正文"
              f"（台账指到的文件 {miss} 份不在本机；语料按裁定不进 git）")
        return 4
    r = measure(texts, threshold)
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
    for j, a, b in r["对"][:top]:
        print(f"      {j:.4f}  {titles.get(a,'')[:38]:40s} ↔ {titles.get(b,'')[:38]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--threshold", type=float, default=DEFAULT_T)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    print(f"★ 尺子：狠归一化 ＋ {NGRAM}-gram ＋ 抽样 1/{SAMPLE_MOD} ＋ 阈值 {a.threshold}"
          f"（实测同书 0.2155–0.4254／不同书 ≤0.0018）")
    print("★ **跨语言判不了**（原文 vs 译文恒 0.0000）；并查集会因选集串组而高估，"
          "所以两个口径都印出来。\n")
    if a.workspace:
        return report(pathlib.Path(a.workspace), a.threshold)
    if a.all:
        rc = 0
        for d in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
            r = report(pathlib.Path(d), a.threshold)
            rc = rc or (0 if r in (0, 4) else r)
        return rc
    ap.error("要 --workspace 或 --all 或 --self-test")


if __name__ == "__main__":
    raise SystemExit(main())
