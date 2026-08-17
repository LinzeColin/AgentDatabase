#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_roster_name_join.py —— **三张表用姓名 join，而口径不同就会给出不同的队列状态**

## 抓到它的那一次

2026-08-17：两个**同名**的 `next_person.py`（一个 611 行在
`registry/.../references/pipeline/checkers/`，一个 245 行在 `_ledgers/_pipeline/`）
对**同一份数据**给出两组不同的数：

        _pipeline/next_person.py             done 40｜pending  **0**｜deferred 186
        references/.../next_person.py        done 39｜pending **66**｜deferred 132
        我自己现算（归一化姓名）              done 40｜pending **13**｜deferred 184

三个数的差**全部来自姓名 join 的口径**。而队列条目**根本没有状态字段**
（只有 `name / family_zh / family_id / order / priority`）——
「已入库 / 已延后 / 未动」三档是靠**跨表匹配姓名**推出来的。

逐对核完之后：**pending 真值是 0**。我那 13 个里
**11 个是「已做但未出货」**（有工作区、有 cases），**2 个是拼写不同**：

        队列 `Alfred Sloan`   ↔ 延后名单 `Alfred P. Sloan`
        队列 `William Paton`  ↔ 延后名单 `William Andrew Paton`

## ★★★ 为什么不能自动合并

同一次里还查出一对**看着一模一样、实际是两个人**：

        队列/延后 `Charles M. Eastman`  建造采购师｜1940-05-05 – 2020-11-09｜BIM 研究者
        名册      `Charles Eastman`     思想教育师｜active_through **1939**｜Ohiyesa

**「姓 + 名首字母相同」这个判别式对同名者恒为真。**
所以它只能用来**找疑似**，判定必须写进 `_ledgers/_姓名别名.json`，逐对附判据。
[[test-the-guard-against-this-persons-namesake]]｜[[namesakes-whose-works-are-also-public-domain]]

## 本件判什么

1. 三张表两两之间，(姓, 名首字母) 相同而归一化全名不同的**疑似对**；
2. 每一对**必须**在别名表里被显式判成 `same` 或 `different`；
3. **有一对没判 ⇒ rc=1**（不是「没问题」，是「没人裁过」）；
4. 顺带印出按别名表消解之后的三档计数，**并印出分母**。

退出码：0＝疑似全部已裁决；1＝有未裁决的疑似；4＝**读不到某张表（未量，不是通过）**。
"""
import argparse
import json
import pathlib
import re
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent


def _repo_root() -> pathlib.Path:
    import subprocess
    r = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return (pathlib.Path(r.stdout.strip())
            if r.returncode == 0 and r.stdout.strip() else HERE.parents[5])


LEDGERS = HERE.parent
QUEUE = LEDGERS / "_蒸馏队列.json"
DEFER = LEDGERS / "_延后名单.json"
ALIAS = LEDGERS / "_姓名别名.json"
INDEX = (_repo_root() / "CodexSkills/registry/codex/persona-distiller-group/team-index.json")


def norm(s) -> str:
    """归一化：NFKD 去变音符 → 非字母数字转空格 → 小写 → 折叠空白。"""
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", s).lower().split())


def key_fl(s):
    """(姓, 名首字母) —— **只用来找疑似，绝不用来合并**。"""
    t = norm(s).split()
    return (t[-1], t[0][:1]) if len(t) >= 2 else (norm(s), "")


def suspects(a: set, b: set) -> list:
    """→ [(甲, 乙)]：(姓, 名首字母) 相同而归一化全名不同的对。"""
    import collections
    ka, kb = collections.defaultdict(list), collections.defaultdict(list)
    for x in a:
        ka[key_fl(x)].append(x)
    for y in b:
        kb[key_fl(y)].append(y)
    out = []
    for k in set(ka) & set(kb):
        for x in ka[k]:
            for y in kb[k]:
                if norm(x) != norm(y):
                    out.append((x, y))
    return sorted(set(out))


def resolved_pairs(alias: dict) -> set:
    """别名表里已裁决的对（无序，按归一化比）。"""
    out = set()
    for row in alias.get("same", []):
        c = row.get("canonical", "")
        for a in row.get("aliases", []):
            out.add(frozenset((norm(c), norm(a))))
    for row in alias.get("different", []):
        out.add(frozenset((norm(row.get("甲", "")), norm(row.get("乙", "")))))
    return out


def self_test() -> int:
    bad = []

    def chk(lbl, ok):
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    chk("★ 归一化：去变音符 + 去标点 + 小写",
        norm("Jean-Jacques Rousseau") == "jean jacques rousseau"
        and norm("Frobel") == norm("Fröbel"))
    chk("★ (姓, 名首字母)：中名不影响",
        key_fl("William Paton") == key_fl("William Andrew Paton"))
    chk("★ 疑似判别式抓得到「中名多一个」",
        suspects({"William Paton"}, {"William Andrew Paton"})
        == [("William Paton", "William Andrew Paton")])
    chk("★★ 反对照：**全名完全相同不算疑似**（否则每个人都跟自己配一对）",
        suspects({"Immanuel Kant"}, {"Immanuel Kant"}) == [])
    chk("★★ 反对照：**姓相同而名不同不算疑似**（Coffin 家两个人不许配对）",
        suspects({"Charles Coffin"}, {"Levi Coffin"}) == [])
    # ★★★ 关键反对照：**同名者也满足这个判别式** —— 所以它只能找疑似
    chk("★★★ 同名者（Charles M. Eastman vs Charles Eastman）**照样是疑似** —— "
        "判别式对同名者恒为真，所以不许自动合并",
        len(suspects({"Charles M. Eastman"}, {"Charles Eastman"})) == 1)
    # ★★ 已裁决的对要认得出；**未裁决的不许被当成已裁决**
    _al = {"same": [{"canonical": "William Andrew Paton", "aliases": ["William Paton"]}],
           "different": [{"甲": "Charles M. Eastman", "乙": "Charles Eastman"}]}
    _r = resolved_pairs(_al)
    chk("★★ same 那一档认得出", frozenset((norm("William Paton"),
                                          norm("William Andrew Paton"))) in _r)
    chk("★★ different 那一档也认得出（**判成两个人也是裁决**）",
        frozenset((norm("Charles M. Eastman"), norm("Charles Eastman"))) in _r)
    chk("★★ 反对照：没写进别名表的对**不许**被当成已裁决",
        frozenset((norm("Alfred Sloan"), norm("Alfred P. Sloan"))) not in _r)

    # ★★★ 族别判别：判成同一人而两侧族别不同 ⇒ 多半是同名者
    def _fam_clash(same_rows, fam):
        out = []
        for row in same_rows:
            names = [row.get("canonical", "")] + list(row.get("aliases", []))
            fams = set()
            for n in names:
                fams |= {x for x in fam.get(norm(n), set()) if x}
            if len(fams) > 1:
                out.append(names)
        return out
    _fam = {norm("Charles M. Eastman"): {"建造采购师"},
            norm("Charles Eastman"): {"思想教育师"},
            norm("Alfred Sloan"): {"创业经营师"},
            norm("Alfred P. Sloan"): {"创业经营师"}}
    chk("★★★ 判成同一人而**族别不同** → 报出来（Eastman 那一对）",
        _fam_clash([{"canonical": "Charles Eastman",
                     "aliases": ["Charles M. Eastman"]}], _fam) != [])
    chk("★★★ 反对照：**族别一致的合并不许误报**（Sloan 那一对）",
        _fam_clash([{"canonical": "Alfred P. Sloan",
                     "aliases": ["Alfred Sloan"]}], _fam) == [])
    chk("★★ 反对照：**一侧没有族别信息时不许报**（缺信息 ≠ 冲突）",
        _fam_clash([{"canonical": "Alfred P. Sloan", "aliases": ["查无此人"]}], _fam) == [])

    print("\n自测 %d/%d" % (12 - len(bad), 12))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    # ★ 读不到任何一张表 ⇒ **未量（rc=4）**，不是通过。
    missing = [p for p in (QUEUE, DEFER, INDEX) if not p.is_file()]
    if missing:
        print("★ **未量，不是通过**（rc=4）—— 读不到这几张表：")
        for p in missing:
            print("     " + str(p))
        return 4

    q = json.loads(QUEUE.read_text(encoding="utf-8"))
    qrows = q if isinstance(q, list) else next(v for v in q.values() if isinstance(v, list))
    dfr = json.loads(DEFER.read_text(encoding="utf-8"))["deferred"]
    prods = json.loads(INDEX.read_text(encoding="utf-8"))["products"]
    alias = json.loads(ALIAS.read_text(encoding="utf-8")) if ALIAS.is_file() else {}

    QN = {r["name"] for r in qrows}
    DN = {r["name"] for r in dfr}
    PN = {p["canonical_name"] for p in prods if p.get("canonical_name")}
    print("扫描面：队列 **%d** 人｜延后名单 **%d** 人｜名册产物 **%d** 件"
          % (len(QN), len(DN), len(prods)))
    if not (QN and DN and PN):
        print("★ **未量，不是通过** —— 三张表里有一张是空的")
        return 4

    pairs = (suspects(QN, DN) + suspects(QN, PN) + suspects(DN, PN))
    pairs = sorted(set(frozenset((x, y)) for x, y in pairs))
    done = resolved_pairs(alias)
    unresolved = [p for p in pairs
                  if frozenset(norm(x) for x in p) not in done]
    print("\n(姓, 名首字母) 相同而全名不同的**疑似对**：**%d** 对"
          "｜别名表已裁决 **%d** 对｜**未裁决 %d 对**"
          % (len(pairs), len(pairs) - len(unresolved), len(unresolved)))
    if unresolved:
        print("\n✗ 下面这些**没人裁过** —— 不是「没问题」，是「不知道是不是同一个人」：")
        for p in unresolved:
            x, y = sorted(p)
            print("     %-32s ↔ %s" % (x, y))
        print("\n  ★ 处置：打开 `_ledgers/_姓名别名.json`，逐对写进 `same` 或 `different`，"
              "**并附判据**（族别、生卒、slug 至少各看一样）。")
        print("  ★★ **不许自动合并** —— 同名者满足同一个判别式"
              "（本仓实例：Charles M. Eastman 1940–2020 建造采购师 "
              "vs Charles Eastman 卒 1939 思想教育师）。")

    # ── ★★★ 合并对不对：**`same` 两侧的族别必须一致** ──
    #   本件原先只查「裁没裁」，不查「裁得对不对」——把 Charles M. Eastman
    #   错误地并进 Charles Eastman，它照样 rc=0（实测变异②）。
    #   而那次错误合并留下了可查的痕迹：**已入库 40 → 41**。
    #   ⇒ 加一道结构性判别：族别不一致 ⇒ **这多半是两个人**。
    #   （族别在三张表里的键不同：队列/延后用 `family_zh`，名册用 `registration_category`。）
    #   [[test-the-guard-against-this-persons-namesake]]
    _fam = {}
    for r in qrows:
        _fam.setdefault(norm(r["name"]), set()).add(str(r.get("family_zh") or ""))
    for r in dfr:
        _fam.setdefault(norm(r["name"]), set()).add(str(r.get("family_zh") or ""))
    for pr in prods:
        if pr.get("canonical_name"):
            _fam.setdefault(norm(pr["canonical_name"]), set()).add(
                str(pr.get("registration_category") or ""))
    _clash = []
    for row in alias.get("same", []):
        names = [row.get("canonical", "")] + list(row.get("aliases", []))
        fams = set()
        for n in names:
            fams |= {x for x in _fam.get(norm(n), set()) if x}
        if len(fams) > 1:
            _clash.append((names, sorted(fams)))
    if _clash:
        print("\n✗ **判成同一人、而族别对不上** —— 这多半是同名者，逐对复核：")
        for names, fams in _clash:
            print("     %-46s 族别：%s" % (" ＝ ".join(names)[:44], "／".join(fams)))
        print("  ★ 族别不同、生卒不同、题材不同 ⇒ 是两个人，应改写进 `different`。")

    # ── 顺带：按别名表消解之后的三档计数（**印分母**）──
    canon = {}
    for row in alias.get("same", []):
        for x in row.get("aliases", []):
            canon[norm(x)] = norm(row.get("canonical", x))
    c = lambda s: canon.get(norm(s), norm(s))          # noqa: E731
    P = {c(p["canonical_name"]) for p in prods if p.get("canonical_name")}
    P |= {c(str(p.get("subject_slug", "")).replace("-", " ")) for p in prods
          if p.get("subject_slug")}
    D = {c(r["name"]) for r in dfr}
    n_done = sum(1 for r in qrows if c(r["name"]) in P)
    n_def = sum(1 for r in qrows if c(r["name"]) in D and c(r["name"]) not in P)
    n_pend = len(qrows) - n_done - n_def
    print("\n按别名表消解后的队列三档（分母 = 队列 **%d** 条）：" % len(qrows))
    print("   已入库 **%d**｜已延后 **%d**｜**未动 %d**" % (n_done, n_def, n_pend))
    print("   ★ 「未动」里可能仍含**已开工但处置没落库**的人 —— 那要看工作区，不是看这三张表。")
    return 1 if (unresolved or _clash) else 0


if __name__ == "__main__":
    raise SystemExit(main())
