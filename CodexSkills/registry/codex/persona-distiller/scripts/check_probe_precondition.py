#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这个人可以直接发抓源指令吗，还是得先跑可得性探测？**

## 为什么有这道判据

「卒于 1930 年后的人物，排期前先跑可得性探测」这条前置，
是 Henderson #113 与 Peplau #114 各用一次实测换来的：

| | 真取到 | 门槛 | 版权 |
|---|---:|---:|---|
| Henderson #113 | 2 份 | 45 | 两部教科书**本人亲自续展**（→2034／2050） |
| Peplau #114 | 3 份 | 45 | `RE66969 1980-09-29` **按时续展**（→2047），另一部自动续展（→2059） |

**没有它，两次都会是一整轮白抓。**

## ★★ 但它现在只是散文——靠我记得谁哪年死的

实测 2026-08-04：队列 216 个条目，**带生卒字段的是 0 个**。
也就是说这条前置**没有任何机器可核的输入**。

## 判据

发抓源指令前，这个人必须满足**其中之一**：

1. 有卒年且 **< 1930**——可以直接抓
2. 已有可得性探测产物（`VERDICT.md` 或 `raw/_PROBE.md`）——探过了，按结论走

### ★★ 卒年从哪来：必须带来源，否则不作数

队列条目里可以有 `died`；也可以放在队列旁边的 `_卒年.json`：

```json
{"Clara Barton": {"died": 1912, "source": "……（可核的出处）"}}
```

**没有 `source` 的条目一律不作数**——判据当它不存在。

实测 2026-08-04：队列 216 个条目**带生卒字段的是 0 个**，
已入库的 100 个人物产物里**也一个都没有**。
**这个数据在系统里根本不存在**，而**我不能凭记忆填**——
所以这里留的是一个「带来源才作数」的入口，不是一张让我敲年份的表。

## ★ 默认方向：不知道 → 要求探测

**卒年缺失一律当作「需要探测」，绝不当作「可以直接抓」。**

这条的方向是这道判据的全部价值所在。反过来写，
它就变成一台**为省事而放行**的机器——而省下的那一次探测，
代价是一整轮白抓。

**判据不许替我猜卒年。** 缺就是缺，缺就要探。

## 它判不了什么

- **判不了探测结论对不对**——只判「探过没有」。
- **判不了 1930 这个界怎么来的**：它是美国版权那条 95 年线的一个粗略代理，
  **不是法律判断**。卒于 1930 年前的人也可能有身后出版的受保护材料，
  那由抓源方的 `rights` 字段与 `POSTHUMOUS` 标记去管。
"""
import argparse
import json
import pathlib
import sys

CUTOFF = 1930


def load_years(path: pathlib.Path) -> dict:
    """`_卒年.json`：**没有 `source` 的条目一律不作数**（判据当它不存在）。

    ★★ v0.0.0.98：`confidence` 是**记录级**的，而它标的常常只是某一个字段。
    实测（2026-08-04 补卒年后）：13 条 `low` 里有 3 条**卒年是精确的**
    （Carver 1943-01-05、Pacioli 1517、Socrates -399-02-15），
    标 low 的原因是**生年**近似。本判据只用卒年，所以这三条实际可用。

    **但记录级的置信度不能替字段级的判断**——所以用到 `low` 记录时要**报出来**，
    让人自己看那一条的 `source` 里写的是哪个字段近似。
    （这与查证方自己报的坑 ⑳「近似要按字段判不按人判」是同一件事。）
    """
    if not path or not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    out = {}
    for name, rec in (raw or {}).items():
        # ★★ v0.0.0.99：**在世的人（died 为 null）以前在这里就被丢掉了**，
        #   于是下游只能报「没有卒年」——把一条已知（在世）讲成了未知。
        #   现在保留「有 source 且（有卒年 或 明确标了 alive）」的。
        if isinstance(rec, dict) and rec.get("source") and (
                rec.get("died") is not None or rec.get("alive") is True):
            out[name.strip().lower()] = rec
    return out


def low_confidence_used(years: dict, names) -> list:
    """→ 本次用到的记录里，哪几条是 `confidence: low`。**只报，不拦。**"""
    out = []
    for n in names:
        r = years.get(str(n).strip().lower())
        if r and r.get("confidence") == "low":
            out.append(f"{r.get('name', n)}（卒 {r.get('died')}）——"
                       f"该记录标 `low`，**看清是哪个字段近似**：{str(r.get('source'))[:64]}")
    return out


# ★★★★ **探测产物有五种命名，本件原来只认两种。**
#   2026-08-06 全库实测：
#       VERDICT.md          10 份   ← 原来认
#       PROBE.md（顶层）      5 份   ← **不认**（bain / bessemer / mehl / rosenhain / sorby）
#       raw/_PROBE.md        3 份   ← 原来认
#       _PROBE.md            1 份   ← **不认**
#       COPYRIGHT_NOTE.md    1 份   ← **不认**（DeBakey #119 的 §105 分析就写在这里）
#   **7 个人物的探测产物它看不见**，于是对他们一律报「没有探测产物——先探再抓」，
#   而那几位**探过了，有的还已经据此记了延后**。
#
#   ★ 这与 [[eval-artifacts-have-five-schemas]] 是同一件事的另一处：
#     「按一种命名去统计，一天错三次」。**判据不该假设命名统一，除非有东西在强制它。**
#   ★★ 修法是**认全五种并报出认的是哪一种**——不是挑一种去改 7 个人物的文件，
#     那会动到已关闭的处置。
PROBE_NAMES = ("VERDICT.md", "PROBE.md", "raw/_PROBE.md", "_PROBE.md",
               "COPYRIGHT_NOTE.md")


def probe_artifacts(corpora: pathlib.Path, slug: str) -> list[str]:
    """探测产物：`PROBE_NAMES` 里任一份即可。**返回认到的是哪一种。**"""
    found = []
    for d in sorted(corpora.glob(f"wip-{slug}*")):
        for rel in PROBE_NAMES:
            if (d / rel).is_file():
                found.append(f"{d.name}/{rel}")
    return found


def verdict(entry, probes, years=None):
    """→ (可否直接抓源, 理由)。**不知道卒年一律要求探测。**"""
    ext = (years or {}).get(entry.get("name", "").strip().lower(), {})
    died = entry.get("died", entry.get("death_year", ext.get("died")))
    if entry.get("alive") is True:
        died = None
    if isinstance(died, str) and died.strip().isdigit():
        died = int(died.strip())
    if isinstance(died, int) and died < CUTOFF:
        return True, f"卒于 {died}（< {CUTOFF}）——可直接发抓源指令"
    if probes:
        return True, "已有可得性探测产物：" + "、".join(probes)
    if isinstance(died, int):
        return False, f"卒于 {died}（≥ {CUTOFF}）而**没有探测产物**——先探再抓"
    # ★★ v0.0.0.99：**「在世」与「不知道」不是同一件事**，虽然两者都要探。
    #   在世（有出处）是一条**更强的已知**：著作必然在保护期内，**而且没有到期日**
    #   ——Watson #116 正是因此被延后（1976 年法终身+70，无须续展、无从漏续展）。
    #   把它说成「没有卒年」，等于把一条已知讲成未知。
    if (entry.get("alive") is True or ext.get("alive") is True) and ext.get("source"):
        return False, ("**在世（卒年表有出处）**——著作必然在保护期内，**而且没有到期日**"
                       "（不像「版权在保护期内」那一类还等得到）。仍要探，"
                       "但探之前先想清楚**要的是他哪一个声音**"
                       "——Gawande #120 的 §105 语料 26,005 字全是公务散文，"
                       "而值得建模的那个声音一个字都取不到。")
    return False, ("**队列里没有卒年**——按默认方向当作「需要探测」。"
                   "**判据不许替你猜卒年；缺就是缺，缺就要探。**")


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★ 正向：卒年早于 1930 且已知 → 直接抓 ──")
    ok, why = verdict({"name": "Clara Barton", "died": 1912}, [])
    print(f"    {why}")
    chk("Barton（1912）放行", ok)

    print("── ★★ 反向对照 ①：**卒年缺失不许当作「可以直接抓」** ──")
    ok, why = verdict({"name": "某人"}, [])
    chk("没有卒年 → 拦住（不是放行）", not ok)

    print("── ★★ 反向对照 ②：**卒于 1930 后且没探过 → 拦住** ──")
    ok, _ = verdict({"name": "Peplau", "died": 1999}, [])
    chk("Peplau（1999）无探测产物 → 拦住", not ok)

    print("── ★ 反向对照 ③：探过了就放行，按结论走 ──")
    ok, why = verdict({"name": "Peplau", "died": 1999}, ["wip-peplau-114/VERDICT.md"])
    print(f"    {why}")
    chk("有 VERDICT.md → 放行", ok)

    print("── ★★★ 反向对照 ⑤a：**走完整路径**（load_years → verdict），不许绕过加载器 ──")
    import tempfile as _tf, json as _j
    with _tf.TemporaryDirectory() as _d:
        _f = pathlib.Path(_d) / "y.json"
        _f.write_text(_j.dumps({
            "活着的": {"name": "活着的", "alive": True, "died": None, "source": "Wikidata Qx（无 P570）"},
            "死了的": {"name": "死了的", "died": 1900, "source": "Wikidata Qy"},
            "没出处的": {"name": "没出处的", "alive": True},
        }, ensure_ascii=False), encoding="utf-8")
        _y = load_years(_f)
        chk(f"加载后留下 {sorted(_y)}——**在世的没有被丢掉**",
            set(_y) == {"活着的", "死了的"})
        chk("在世的走完整路径后报「在世」",
            "在世" in verdict({"name": "活着的"}, [], _y)[1])
        chk("★ 无出处的仍被丢掉", "没出处的" not in _y)

    print("── ★★ 反向对照 ⑤b：**「在世」与「不知道」要分开报**（v0.0.0.99）──")
    y = {"某人": {"name": "某人", "alive": True, "died": None, "source": "Wikidata Qx（无 P570）"}}
    ok1, why1 = verdict({"name": "某人"}, [], y)
    ok2, why2 = verdict({"name": "查无此人"}, [], y)
    chk("在世的报「在世（有出处）」而不是「没有卒年」", not ok1 and "在世" in why1)
    chk("真不知道的仍报「没有卒年」", not ok2 and "没有卒年" in why2)
    chk("★ 两者都**不放行**（方向没变）", (not ok1) and (not ok2))
    chk("★ 在世但**无出处**时，不许当成「在世」——退回「没有卒年」",
        "没有卒年" in verdict({"name": "某人"}, [],
                            {"某人": {"name": "某人", "alive": True}})[1])

    print("── ★★ 反向对照 ④：**在世作者不许因为「没有卒年」而被当成古人** ──")
    ok, _ = verdict({"name": "Jean Watson", "alive": True}, [])
    chk("alive=True → 拦住", not ok)

    print("── ★★ 反向对照 ⑤：**`alive` 要压过误填的卒年** ──")
    ok, _ = verdict({"name": "在世但卒年填错", "alive": True, "died": 1900}, [])
    chk("alive=True 时忽略 died=1900 → 仍拦住", not ok)

    print("── ★★ 反向对照 ⑧：**`_卒年.json` 里没有 `source` 的条目不作数** ──")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / "_卒年.json"
        f.write_text(json.dumps({"甲": {"died": 1900},                    # 无 source
                                 "乙": {"died": 1900, "source": "某处"}},
                                ensure_ascii=False), encoding="utf-8")
        y = load_years(f)
        chk("无 source 的「甲」被丢掉，带 source 的「乙」留下",
            "甲" not in y and "乙" in y)
        ok_a, _ = verdict({"name": "甲"}, [], y)
        ok_b, _ = verdict({"name": "乙"}, [], y)
        chk("→ 甲仍被拦住，乙放行", (not ok_a) and ok_b)

    print("── 反向对照 ⑥：卒年是字符串也要认 ──")
    ok, _ = verdict({"name": "x", "died": "1912"}, [])
    chk("died='1912' → 放行", ok)
    print("── ★★★★ 五种探测产物命名，一种都不许漏（2026-08-06 实测分布）──")

    import tempfile as _tf

    with _tf.TemporaryDirectory() as _d:

        _root = pathlib.Path(_d)

        for _i, _rel in enumerate(PROBE_NAMES):

            _w = _root / f"wip-probe{_i}-900"

            (_w / _rel).parent.mkdir(parents=True, exist_ok=True)

            (_w / _rel).write_text("x", encoding="utf-8")

            _got = probe_artifacts(_root, f"probe{_i}")

            chk(f"认得 `{_rel}`（{len(_got)} 份）", len(_got) == 1)

        # ★ 反向：没有任何一种时必须报 0，不能因为目录存在就算探过

        _w2 = _root / "wip-none-901"

        (_w2 / "raw").mkdir(parents=True, exist_ok=True)

        (_w2 / "README.md").write_text("x", encoding="utf-8")

        chk("目录在而没有探测产物 → 0 份", not probe_artifacts(_root, "none"))



    print("── ★ 反向对照 ⑦：**边界年份 1930 本身要拦**（界是「< 1930」） ──")
    ok, _ = verdict({"name": "x", "died": 1930}, [])
    chk("died=1930 → 拦住", not ok)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--queue", type=pathlib.Path)
    ap.add_argument("--corpora", type=pathlib.Path, help="_corpora 目录")
    ap.add_argument("--name", help="只看这一个人；不给就全表扫")
    ap.add_argument("--years", type=pathlib.Path,
                    help="_卒年.json（**没有 source 的条目不作数**）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not (a.queue and a.corpora):
        ap.error("要么 --self-test，要么给 --queue 与 --corpora")
    if not a.queue.is_file():
        print(f"✗ **{a.queue} 不在——本次未检查（不是通过）**")
        return 3

    q = json.loads(a.queue.read_text(encoding="utf-8"))
    items = q if isinstance(q, list) else q.get("queue", q.get("items", []))
    if a.name:
        items = [x for x in items if a.name.lower() in x.get("name", "").lower()]
        if not items:
            print(f"✗ **队列里没有 {a.name}——本次未检查（不是通过）**")
            return 3

    years = load_years(a.years) if a.years else {}
    blocked, no_year = [], 0
    for x in items:
        slug = x.get("name", "").split()[-1].lower()
        ok, why = verdict(x, probe_artifacts(a.corpora, slug), years)
        if not ok:
            blocked.append((x.get("name"), why))
        if not (x.get("died") or x.get("death_year") or x.get("alive")
                or x.get("name", "").strip().lower() in years):
            no_year += 1

    print(f"扫了 **{len(items)}** 个队列条目，其中 **{no_year}** 个没有卒年字段\n")
    if a.name:
        for nm, why in blocked or [(items[0].get("name"), "可直接发抓源指令")]:
            print(f"  {nm}：{why}")
        return 1 if blocked else 0
    if not blocked:
        print("  ✓ 都可以直接发抓源指令")
        return 0
    print(f"✗ **{len(blocked)} 个要先跑可得性探测**（只列前 8 个）：")
    for nm, why in blocked[:8]:
        print(f"    {nm:28} {why}")
    print("\n  **默认方向是「不知道就要探」。** 反过来写，"
          "它就成了一台为省事而放行的机器——\n"
          "  而省下的那一次探测，代价是一整轮白抓"
          "（Henderson #113、Peplau #114 各一次）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
