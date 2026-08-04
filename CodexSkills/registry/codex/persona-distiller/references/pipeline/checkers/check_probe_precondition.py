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
        if isinstance(rec, dict) and rec.get("source") and rec.get("died") is not None:
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


def probe_artifacts(corpora: pathlib.Path, slug: str) -> list[str]:
    """探测产物：`VERDICT.md` 或 `raw/_PROBE.md`（任一即可）。"""
    found = []
    for d in sorted(corpora.glob(f"wip-{slug}*")):
        for rel in ("VERDICT.md", "raw/_PROBE.md"):
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
