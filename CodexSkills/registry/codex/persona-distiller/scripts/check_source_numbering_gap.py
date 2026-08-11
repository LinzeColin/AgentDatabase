#!/usr/bin/env python3
"""建模者看得见的语料文件名里，**编号缺口本身是一条泄题通道**。

## 它抓的是什么

抓源时给每份语料起的文件名带一个全局顺序前缀（`01-`、`05a-`、`05b-`…）。
划 holdout 时把那一份**移出** `references/sources/`，
**而序号不会自动补齐**——于是建模者看到的是：

    05a-mnras-1844-moon-model
    05b-mnras-1846-optical-glass
    05c-mnras-1851-source-of-light
    05d-mnras-1852-jupiter-saturn
    ★ 05e 不见了
    05f-mnras-1855-rotatory-nebulae

**缺口连着两侧邻居的描述性文件名一起看，泄的不只是「有东西被拿走了」**，
还包括**被拿走那份的刊物与年代区间**（此例：MNRAS，1852–1855 之间）。

## 它是怎么被发现的

**不是判据发现的。** 2026-08-10，Nasmyth #153 候选侧答题子代理
在 `__incident__` 里主动写：「`references/sources` 的文件编号从 05d 跳到 05f，
我没有去查 05e 是什么。」——**它没查，但通道是我留的。**

★ 同一份 `__incident__` 里它还报了另一条（研究道文档带 `Proposed Holdout cases` 节），
那条已由 `check_holdout_mention` 扩清单接住。**一次事故报出两条，两条都得有主人。**

## 射程（**它抓不到的**）

- **只看文件名，不看内容。** 文件名里不带顺序前缀的工作区，本件一个字看不见。
- **不判断缺口是不是 holdout 造成的**：抓源失败、来源被剔除、手工改名都会留缺口。
  本件只报「缺口在哪、两侧邻居是什么」，**是不是泄题由人判**。
  ★ 但**报出来的第一件事就是「holdout 的文件名是否落在这个缺口上」**——
    落在缺口上的，基本可以断定缺口就是它留下的。
- **补齐编号不等于堵住通道**：份数本身也是信息（建模者数得出手上有几份）。
  本件不解决那一层。
"""
import argparse
import json
import pathlib
import re
import sys

# `01-`、`05a-`、`12b-` 这类前缀：数字段 + 可选字母段
_PREFIX = re.compile(r"^(\d+)([a-z]?)-")


def _is_year(digits: str) -> bool:
    """`1900` 是年份，`0013` 是序号。**这一条不分清，整件判据就是噪声发生器。**

    ★★★★ 2026-08-10 实测：第一版把任何前导数字都当序号，于是
      Rosenhain #138 报出 **11 处「缺口」**——而它的文件名前缀是**出版年**
      （`1900-crystalline-structure`、`1902-misuse-of-coal`、`1904-slip-bands`…），
      「缺 1901/1903/1905/1906/1907」的真实含义是**那几年他没发表**。
      **11 处全是误报，而它的 7 份 holdout 一处也没落在缺口上。**

    判法：**四位、不以 0 开头、落在 1400–2100** → 年份。
    ★ 零填充是序号的标志（Adams #131 用的是 `0012`/`0013`，同为四位但以 0 开头）。
    """
    return len(digits) == 4 and not digits.startswith("0") and 1400 <= int(digits) <= 2100


def _seq(name: str):
    """文件名 → `(数字, 字母)`；没有前缀、或前缀是年份，返回 `None`（**不是 0**）。"""
    m = _PREFIX.match(name)
    if not m:
        return None
    if _is_year(m.group(1)):
        return None
    return int(m.group(1)), (m.group(2) or "")


def _visible_names(ws: pathlib.Path) -> list:
    """建模者看得见的语料文件名。

    ★ 只取 `references/sources/` 下的——`references/holdout/` 与
      `references/holdout-notes/` **明令禁止建模者打开**，不算可见。
    """
    root = ws / "references" / "sources"
    if not root.is_dir():
        return []
    return sorted({p.name for p in root.rglob("*") if p.is_file()})


def _holdout_names(ws: pathlib.Path) -> list:
    root = ws / "references" / "holdout"
    if not root.is_dir():
        return []
    return sorted({p.name for p in root.rglob("*") if p.is_file()})


def gaps(names: list) -> list:
    """→ 缺口列表。每项给出缺的编号与**两侧邻居的完整文件名**。"""
    seen = {}
    for n in names:
        s = _seq(n)
        if s is None:
            continue
        seen.setdefault(s, n)
    if not seen:
        return []
    out = []
    keys = sorted(seen)
    # ① 字母段的缺口：同一数字下 a,b,c… 断开
    bynum = {}
    for num, let in keys:
        bynum.setdefault(num, []).append(let)
    for num, lets in bynum.items():
        real = sorted(x for x in lets if x)
        if not real:
            continue
        span = [chr(c) for c in range(ord(real[0]), ord(real[-1]) + 1)]
        for L in span:
            if L in real:
                continue
            prev = max((x for x in real if x < L), default=None)
            nxt = min((x for x in real if x > L), default=None)
            out.append({
                "缺的编号": f"{num:02d}{L}",
                "左邻": seen.get((num, prev)) if prev else None,
                "右邻": seen.get((num, nxt)) if nxt else None,
            })
    # ①b ★ 组内**首字母不是 `a`**：这是「疑似」，不是「确认」。
    #     确认型缺口（05e）两侧都有邻居，缺口的存在是**算出来的**；
    #     首字母缺口只有右邻，靠的是「带字母的组约定从 a 起编」这条**惯例**——
    #     惯例可能不成立（这一组本来就可能从 b 开始编）。**两者不许混报。**
    for num, lets in bynum.items():
        real = sorted(x for x in lets if x)
        if real and real[0] != "a":
            out.append({
                "缺的编号": f"{num:02d}a",
                "左邻": None,
                "右邻": seen.get((num, real[0])),
                "★ 这是疑似": "组内首字母不是 a——**靠惯例推的，不是算出来的**",
            })
    # ② 数字段的缺口：01,02,…断开
    nums = sorted(bynum)
    for v in range(nums[0], nums[-1] + 1):
        if v in bynum:
            continue
        prev = max((x for x in nums if x < v), default=None)
        nxt = min((x for x in nums if x > v), default=None)
        out.append({
            "缺的编号": f"{v:02d}",
            "左邻": seen.get((prev, sorted(bynum[prev])[-1])) if prev is not None else None,
            "右邻": seen.get((nxt, sorted(bynum[nxt])[0])) if nxt is not None else None,
        })
    return sorted(out, key=lambda d: d["缺的编号"])


def scan(ws: pathlib.Path) -> dict:
    vis = _visible_names(ws)
    hold = _holdout_names(ws)
    g = gaps(vis)
    hold_seq = {}
    for n in hold:
        s = _seq(n)
        if s:
            hold_seq[f"{s[0]:02d}{s[1]}"] = n
    for d in g:
        # ★★ 最要紧的一栏：**缺口是不是 holdout 留下的**
        d["★ holdout 的文件名正落在这个缺口上"] = hold_seq.get(d["缺的编号"])
    out = {
        "建模者可见的语料文件": len(vis),
        "带顺序前缀的": sum(1 for n in vis if _seq(n)),
        "**编号缺口**": g,
        "holdout 文件": len(hold),
    }
    if not vis:
        out["★ 没有 references/sources/"] = "**未核（不是通过）**"
    if vis and not out["带顺序前缀的"]:
        out["★ 文件名不带顺序前缀"] = "本件对这个工作区**看不见任何东西**（不是通过）"
    if hold and not hold_seq:
        out["★ holdout 文件名不带前缀"] = "**判不出缺口是不是它留下的**"
    return out


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    print("\n══ ★★★★ 逐字真实样本：Nasmyth #153（2026-08-10 由候选子代理报出）══")
    REAL = ["01-autobiography-1883.normalized.txt",
            "02-the-moon-1874.normalized.txt",
            "03-slide-principle-1841.normalized.txt",
            "04-select-committee-1836-testimony.normalized.txt",
            "05a-mnras-1844-moon-model.normalized.txt",
            "05b-mnras-1846-optical-glass.normalized.txt",
            "05c-mnras-1851-source-of-light.normalized.txt",
            "05d-mnras-1852-jupiter-saturn.normalized.txt",
            "05f-mnras-1855-rotatory-nebulae.normalized.txt",
            "05g-crayon-1855-volcanic-action.normalized.txt",
            "06b-dibner-obituaries-clippings-NOT-HIS.normalized.txt",
            "07-steam-hammer-patent-1842-journal-reprint.normalized.txt"]
    g = gaps(REAL)
    got = [d["缺的编号"] for d in g]
    chk(f"抓到缺口 {got}（05e 必须在内）", "05e" in got)
    e = [d for d in g if d["缺的编号"] == "05e"][0]
    chk(f"★ 左邻是 1852 那份：{e['左邻']}", "1852" in (e["左邻"] or ""))
    chk(f"★ 右邻是 1855 那份：{e['右邻']}", "1855" in (e["右邻"] or ""))
    # ★★ 这一条才是这件判据存在的理由：**缺口连着邻居一起看，泄的是刊物与年代区间**
    chk("★★ 两侧邻居同为 mnras → 缺的那份的刊物与年代区间被泄了出来",
        "mnras" in (e["左邻"] or "") and "mnras" in (e["右邻"] or ""))
    # ★★★ `06a`：只有 `06b` 存在时，**判据算不出 06a 曾经存在**——
    #     它没有左邻，缺口不是算出来的，只能靠「带字母的组从 a 起编」这条惯例推。
    #     ★ 我第一版的用例直接断言「06a 也抓到」，**那是在要求判据知道它不可能知道的事**；
    #       现在把它降为「疑似」，并**在结果里带上「这是疑似」这一栏**——
    #       不许让它和 05e 那种算出来的缺口长得一样。
    sus = [d for d in g if d["缺的编号"] == "06a"]
    chk(f"06a 报为**疑似**（{len(sus)} 条）", len(sus) == 1)
    chk("★ 疑似项必须自带「这是疑似」这一栏，不许与确认型混在一起",
        bool(sus) and sus[0].get("★ 这是疑似"))
    chk("★★ 而 05e 是**确认型**：两侧都有邻居，且不带「疑似」栏",
        not e.get("★ 这是疑似") and e["左邻"] and e["右邻"])

    print("\n── ★★★★ 反例：**年份前缀不是序号**（Rosenhain #138，第一版在此误报 11 处）──")
    YEARS = ["1900-crystalline-structure-2nd__philtrans04739495.normalized.txt",
             "1902-misuse-of-coal__paper-doi-10_1038_066029b0.normalized.txt",
             "1904-slip-bands__philtrans05132848.normalized.txt",
             "1908-eutectic-lead-tin__philtrans00906363.normalized.txt",
             "1913-introduction-to-physical-metallurgy.normalized.txt"]
    chk(f"年份前缀 → 0 个缺口（第一版报 11 处，**全是误报**）：{[d['缺的编号'] for d in gaps(YEARS)]}",
        not gaps(YEARS))
    # ★ 正例必须同时是绿的：**零填充的四位仍要当序号**（Adams #131 用的就是这一种）
    PAD = ["0012-conv-1911-vxxx.normalized.txt",
           "0014-conv-1912-vxxxi.normalized.txt",
           "0015-conv-1912-vxxxi.normalized.txt"]
    pg = [d["缺的编号"] for d in gaps(PAD)]
    chk(f"★ 而零填充四位仍算序号，0013 照报：{pg}", "13" in pg)
    chk("★★ 两条必须同时成立——只让年份那条变绿而把 Adams 也一起放过，"
        "就是把判据改坏了[[counter-example-red-can-be-red-by-coincidence]]",
        not gaps(YEARS) and "13" in pg)

    print("\n── 反例：编号连续的目录不许报 ──")
    CLEAN = ["01-a.txt", "02-b.txt", "03a-c.txt", "03b-d.txt", "04-e.txt"]
    chk(f"连续目录 0 个缺口：{[d['缺的编号'] for d in gaps(CLEAN)]}", not gaps(CLEAN))

    print("\n── 反例：不带前缀的文件名，本件看不见（**看不见 ≠ 通过**）──")
    NOPFX = ["src-066bdf28a912.txt", "autobiography.normalized.txt"]
    chk(f"不带前缀 → 0 个缺口：{gaps(NOPFX)}", not gaps(NOPFX))
    chk("★ 而 scan() 必须把「看不见」明说出来，不许只报 0",
        "★ 文件名不带顺序前缀" in scan.__doc__ if scan.__doc__ else True)

    print("\n── 反例：**尾部缺失抓不到**（射程，如实写出来）──")
    TAIL = ["01-a.txt", "02-b.txt"]          # 原本有 03，被整个拿走
    chk(f"末尾被拿走 → 本件报 0 个缺口（**这是抓不到，不是没有**）：{gaps(TAIL)}",
        not gaps(TAIL))

    # ══════════════════════════════════════════════════════════════
    # ㉚ `scan()` / `_visible_names()` / `_holdout_names()`
    #    —— 2026-08-12 之前这三个从没被自测进入过
    # ══════════════════════════════════════════════════════════════
    #
    # 上面各条打的是 `gaps()`（**一串文件名里的编号缺口**），那把尺子已经很硬。
    # 而 `scan()` 决定：**哪些文件算「建模者看得见」、缺口要不要挂上 holdout 的名字**。
    # 前者正是本件的立身之本——`references/holdout/` **一旦被算进可见**，
    # 这道门就再也报不出任何缺口（因为缺口被 holdout 自己填上了）。
    import tempfile as _tf
    print("\n══ ㉚ scan() 本体（tempdir 上搭真工作区）══")

    def _ws(vis=(), hold=(), notes=()):
        d = pathlib.Path(_tf.mkdtemp())
        for sub, names in (("references/sources", vis),
                           ("references/holdout", hold),
                           ("references/holdout-notes", notes)):
            if names:
                (d / sub).mkdir(parents=True, exist_ok=True)
                for n in names:
                    (d / sub / n).write_text("x", encoding="utf-8")
        return d

    V = ["05a-mnras-1844-moon-model.txt", "05b-mnras-1846-optical-glass.txt",
         "05d-mnras-1852-jupiter-saturn.txt"]
    r = scan(_ws(vis=V, hold=["05c-mnras-1851-source-of-light.txt"]))
    g = r["**编号缺口**"]
    chk(f"㉚a 缺口 05c 被报出，且**★ 那一栏点出 holdout 的文件名**"
        f"（{g[0].get('★ holdout 的文件名正落在这个缺口上') if g else '（无缺口）'}）",
        len(g) == 1 and g[0]["缺的编号"] == "05c"
        and g[0]["★ holdout 的文件名正落在这个缺口上"] == "05c-mnras-1851-source-of-light.txt")

    chk("㉚a′ 两侧邻居的完整文件名一起报出（泄的是刊物与年代区间）",
        g[0]["左邻"] == "05b-mnras-1846-optical-glass.txt"
        and g[0]["右邻"] == "05d-mnras-1852-jupiter-saturn.txt")

    # ㉚b 缺口在、而 holdout 不在这个号上 ⇒ ★ 栏必须是 None（**不许乱认领**）
    r = scan(_ws(vis=V, hold=["09a-别的.txt"]))
    g = r["**编号缺口**"]
    chk("㉚b 缺口不是 holdout 留下的 → ★ 栏为空（成因由人判，判据不替它认领）",
        len(g) == 1 and g[0]["★ holdout 的文件名正落在这个缺口上"] is None)

    # ㉚c ★★★ 本件的立身之本：`references/holdout/` **不算可见**。
    #    把它算进去，缺口就被 holdout 自己填平，这道门永远报 0。
    d = _ws(vis=V, hold=["05c-mnras-1851-source-of-light.txt"],
            notes=["05c-笔记.md"])
    chk("㉚c **`_visible_names` 只取 references/sources/**——"
        "holdout 与 holdout-notes 一个都不算可见（算进去这道门就永远报 0）",
        set(_visible_names(d)) == set(V)
        and _holdout_names(d) == ["05c-mnras-1851-source-of-light.txt"])

    # ㉚d 射程：`rglob` 要递归进子目录，否则分册存放的语料整片看不见
    d = pathlib.Path(_tf.mkdtemp())
    (d / "references/sources/vol1").mkdir(parents=True)
    (d / "references/sources/01-a.txt").write_text("x", encoding="utf-8")
    (d / "references/sources/vol1/03-c.txt").write_text("x", encoding="utf-8")
    chk("㉚d 射程：`references/sources/` **递归**（子目录里的语料也算可见）",
        set(_visible_names(d)) == {"01-a.txt", "03-c.txt"})

    # ㉚e/f/g 三种「未核」——**都不许被读成通过**
    r = scan(_ws(vis=[], hold=["05c-x.txt"]))
    chk("㉚e 没有 references/sources/ → 明写「**未核（不是通过）**」",
        "**未核（不是通过）**" in str(r.get("★ 没有 references/sources/")))

    r = scan(_ws(vis=["moon-model.txt", "optical-glass.txt"]))
    chk("㉚f 文件名不带顺序前缀 → 明写「本件**看不见任何东西**（不是通过）」",
        "看不见任何东西" in str(r.get("★ 文件名不带顺序前缀")))

    r = scan(_ws(vis=V, hold=["无前缀的holdout.txt"]))
    chk("㉚g holdout 文件名不带前缀 → 明写「**判不出缺口是不是它留下的**」",
        "判不出" in str(r.get("★ holdout 文件名不带前缀")))

    # ㉚h 反向：连号无缺口 ⇒ 报 0 个缺口，且三条「未核」一条都不出现。
    #    没有它，上面几条可能只是「什么都报」。
    r = scan(_ws(vis=["05a-x.txt", "05b-y.txt", "05c-z.txt"]))
    chk("㉚h 反向：连号无缺口 → 缺口 0 个，且三条「未核」都不出现",
        not r["**编号缺口**"] and not any(k.startswith("★") for k in r))

    print("\n★ 射程：只看文件名；不判断缺口成因；**补齐编号也堵不住「份数本身是信息」那一层**。")
    print("\n" + ("✓ 自测全过" if ok else "✗ **自测未过**"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", nargs="?", help="工作区目录")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.target:
        print("✗ 需要工作区目录（或只给 --self-test）", file=sys.stderr)
        return 3
    r = scan(pathlib.Path(a.target))
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 1 if r["**编号缺口**"] else 0
    print(f"建模者可见语料 {r['建模者可见的语料文件']} 份，"
          f"其中带顺序前缀 {r['带顺序前缀的']} 份；holdout {r['holdout 文件']} 份")
    g = r["**编号缺口**"]
    if g:
        print(f"\n✗ **编号缺口 {len(g)} 处**——建模者数得出这里少了东西：")
        for d in g:
            print(f"    缺 {d['缺的编号']}：左邻 {d['左邻']}　右邻 {d['右邻']}")
            hit = d.get("★ holdout 的文件名正落在这个缺口上")
            if hit:
                print(f"      ★★ **holdout 就在这个缺口上**：{hit}")
                print(f"         → 缺口连着两侧邻居一起看，**泄的是它的刊物与年代区间**。")
    else:
        print("\n✓ 没有编号缺口")
    for k in ("★ 没有 references/sources/", "★ 文件名不带顺序前缀", "★ holdout 文件名不带前缀"):
        if k in r:
            print(f"\n⚠ {k}：{r[k]}")
    print("\n★ 射程：只看文件名；**尾部被整份拿走的缺口抓不到**；"
          "补齐编号也堵不住「份数本身是信息」那一层。")
    return 1 if g else 0


if __name__ == "__main__":
    raise SystemExit(main())
