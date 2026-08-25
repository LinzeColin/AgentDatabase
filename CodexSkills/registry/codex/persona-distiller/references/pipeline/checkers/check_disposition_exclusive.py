#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一个人只能有**一种**处置，而处置有**三份**机器可读的文件。

## 三份文件

| 状态 | 文件 | 含义 |
|---|---|---|
| 已入库 | `persona-distiller-group/team-index.json` 的 `products` | 做完并注册 |
| 延后／拒发 | `_ledgers/_延后名单.json` 的 `deferred` | **我判的**：够不着门、材料不可得 |
| 受阻待裁 | `_ledgers/_受阻待裁.json` 的 `blocked` | **我判不了的**：只能由用户拍板 |

## 本件管两件事

1. **互斥**：同一个人**不许同时出现在两份里**。
   用户裁定之后要把人从受阻名单**挪走**——挪走是两步（加一处、删一处），
   **只做前一步就会留下两处并存**，而两处并存时下游按哪一份算全凭运气。
2. **孤儿**：`_corpora` 里有工作区、而三份里**一份都没有**的人。
   ★ **「有工作区」是事实，不是判断。** 处置只要没进机器可读的文件，
   这个人就会被当成「从没碰过」——实测漏过 Bessemer #132 与 Sorby #133
   （都已记拒发，却只写在 `_决策台账.md` 的散文里）。

## ★★★★ 为什么要有这件

`_受阻待裁.json` 是 **2026-08-10 移交前才建的**。在那之前，
「受阻待裁」这个状态**只活在会话的任务表里，而任务表不跟着仓走**——
核对时发现 Adams／Martens／Roberts-Austen 三人**既不在名册也不在延后名单**。

**建了台账还不够：台账不会提醒你它自己没被维护。**
[[every-requirement-needs-an-owner]] —— 所以本件是那份台账的看门人。

## ★ 姓名比对的口径

按**规范化后的全名**比（去空白、转小写、去标点）。
★ **不按姓比**——本项目的同名护栏就是只比姓，实测挡不住任何同姓者。
★★ 名字形式不同的（`W. A. Paton` vs `William Andrew Paton`）**本件认不出来**，
这是已知盲区，**不许当成「没有重复」**。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata

HERE = pathlib.Path(__file__).resolve().parent
# HERE = …/CodexSkills/registry/codex/persona-distiller/scripts
# parents: [0]persona-distiller [1]codex [2]registry [3]CodexSkills
# ★ 第一版写了 [4]（仓根），于是三份台账全部「读不到」——
#   **而本件当场报了错、没有把「读不到」读成「0 重复」**，[[empty-default-swallows-unknown]] 的守卫生效了。
REPO = HERE.parents[3]
GROUP = REPO / "registry/codex/persona-distiller-group/team-index.json"
LEDGERS = REPO / "skill_log_evals/persona-distiller/_ledgers"
CORPORA = REPO / "skill_log_evals/persona-distiller/_corpora"


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKC", str(name or "")).lower()
    return re.sub(r"[^a-z0-9一-鿿]+", "", s)


def scripts(name: str) -> set:
    """→ 这个名字的**同一串的两种投影**：拉丁部分、汉字部分（都归一后）。

    ★★ 2026-08-13 补：名册里有 **12 个双语名**
      （`田口玄一 Genichi Taguchi`、`John Carmack（约翰·卡马克）`、
        `Reed Hastings / 里德·哈斯廷斯` …），而延后名单写的是单语。
      按全名规范化一比，`田口玄一genichitaguchi` ≠ `genichitaguchi`，
      **本件对这 12 人全盲** —— 实测漏掉了 Taguchi 与 Carmack 两条真重复，
      而它们正是 2026-08-10 给 Steinhardt／Godin 修过的同一个分类错。
    ★ 这**不是猜**：投影只是把同一个串里另一种文字去掉，没有引入任何外部知识。
    ★ 只有投影长度 ≥4 才算（太短会把 `Li Lu` 这种和别人撞上）。
    """
    lat = re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKC", str(name or "")).lower())
    cjk = re.sub(r"[^\u4e00-\u9fff]+", "", str(name or ""))
    return {x for x in (lat, cjk) if len(x) >= 4}


def same_person(a_raw: str, b_raw: str) -> bool:
    """两个原名是不是同一个人。全名相等，**或**任一种文字的投影相等。"""
    if norm(a_raw) == norm(b_raw):
        return True
    return bool(scripts(a_raw) & scripts(b_raw))


def load_three(group: pathlib.Path, ledgers: pathlib.Path) -> tuple[dict, list[str]]:
    """→ ({状态: {规范名: 原名}}, 读不到的文件说明)。**读不到的记下来，不当空集。**"""
    out: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    if group.is_file():
        d = json.loads(group.read_text(encoding="utf-8"))
        out["已入库"] = {norm(p.get("canonical_name")): p.get("canonical_name")
                      for p in d.get("products", []) if p.get("canonical_name")}
    else:
        missing.append(f"名册读不到：{group}")
    for state, fn, key in [("延后／拒发", "_延后名单.json", "deferred"),
                           ("受阻待裁", "_受阻待裁.json", "blocked")]:
        p = ledgers / fn
        if p.is_file():
            d = json.loads(p.read_text(encoding="utf-8"))
            out[state] = {norm(e.get("name")): e.get("name")
                          for e in d.get(key, []) if e.get("name")}
        else:
            missing.append(f"{state}台账读不到：{p}")
    return out, missing


def workspace_names(corpora: pathlib.Path) -> tuple[dict[str, str], dict[str, str]]:
    """→ ({规范名: 工作区目录}, {规范名: 原始名})。名字取 `meta.json` 的 `target_name`／`name`。"""
    out: dict[str, str] = {}
    raw: dict[str, str] = {}
    if not corpora.is_dir():
        return out, raw
    for meta in corpora.rglob("meta.json"):
        try:
            d = json.loads(meta.read_text(encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            continue
        nm = d.get("target_name") or d.get("name") or d.get("person")
        if nm:
            out.setdefault(norm(nm), str(meta.parent.relative_to(corpora)))
            raw.setdefault(norm(nm), str(nm))
    return out, raw


def _tokens(name: str) -> set[str]:
    return {t for t in re.split(r"[^0-9A-Za-z\u4e00-\u9fff]+", str(name or "").lower())
            if len(t) > 1}


def _nearest(key: str, allnames: dict[str, str], raw: str = "") -> str:
    """报孤儿时把台账里最接近的名字一并给出来。

    ★ **不用它来放宽匹配**——`W. Paton` 与 `W. A. Paton` 靠得太近，
      放宽会把父子撞在一起（本项目最贵的同名风险就是这一对）。
      它只是给人看的线索，判定仍以全名严格相等为准。
    """
    best, score = "", 0.0
    rt = _tokens(raw)
    for k, n in allnames.items():
        if rt:
            nt = _tokens(n)
            if nt and len(rt & nt) / min(len(rt), len(nt)) >= 0.8:
                return n
        a, b = (key, k) if len(key) <= len(k) else (k, key)
        if not a:
            continue
        # 最长公共子串占较短一侧的比例：`galen` ⊂ `galenofpergamon` → 1.0
        m = 0
        for i in range(len(a)):
            for j in range(i + m + 1, len(a) + 1):
                if a[i:j] in b:
                    m = j - i
        r = m / len(a)
        if r > score:
            best, score = n, r
    return best if score >= 0.6 else ""


def check(group: pathlib.Path, ledgers: pathlib.Path, corpora: pathlib.Path
          ) -> tuple[int, list[str]]:
    three, missing = load_three(group, ledgers)
    lines = list(missing)
    if missing:
        lines.append("★ **有文件读不到时，本件的结论不完整** —— 不许读成「没有重复」")
    errors = len(missing)

    states = list(three)
    for i in range(len(states)):
        for j in range(i + 1, len(states)):
            a, b = states[i], states[j]
            # ★ 先按规范名求交，再补一轮**跨文字投影**（双语名，见 scripts()）
            both = set(three[a]) & set(three[b])
            for ka, ra in three[a].items():
                if ka in both:
                    continue
                for kb, rb in three[b].items():
                    if kb not in both and same_person(ra, rb):
                        both.add(ka)
                        break
            for k in sorted(both):
                errors += 1
                lines.append(
                    f"✗ **{three[a][k]}** 同时在「{a}」与「{b}」两份台账里。\n"
                    f"    → 一个人只能有一种处置。裁定之后要**挪走**（加一处、删一处），"
                    f"**只做前一步就会留下两处并存。**")
    total = {k for d in three.values() for k in d}
    lines.append(f"三份台账合计 {len(total)} 人（"
                 + "／".join(f"{s} {len(d)}" for s, d in three.items()) + "）")

    ws, ws_raw = workspace_names(corpora)
    allnames = {k: n for d in three.values() for k, n in d.items()}
    orphans = {k: v for k, v in ws.items() if k not in total}
    if orphans:
        lines.append(f"⚠ **有工作区却三份台账都没有的：{len(orphans)} 人**"
                     f"（★ 在办中的人属于正常；**其余多半是名字形式不同**，见每行的最近匹配）")
        for k, v in sorted(orphans.items())[:12]:
            near = _nearest(k, allnames, ws_raw.get(k, ""))
            lines.append(f"      {v}"
                         + (f"　← 台账里最接近的：**{near}**（★ 很可能就是同一个人，"
                            f"形式不同）" if near else "　← 台账里找不到相近的名字"))
    else:
        lines.append("工作区孤儿 0 人")
    lines.append("★ 盲区：名字形式不同的（`W. A. Paton` vs `William Andrew Paton`）本件认不出来，"
                 "**不许当成「没有重复」**"
                 "\n★ **双语名已不在盲区**（2026-08-13 补）：`田口玄一 Genichi Taguchi` 与 "
                 "`Genichi Taguchi` 现在按拉丁投影认得出来。")
    return errors, lines


# ---------------------------------------------------------------- 自测
def self_test() -> int:
    import tempfile
    bad = 0
    CASES = [
        ("正例：三份互不相交 → 不该报", ["A"], ["B"], ["C"], 0),
        ("★ 反例：同一人在名册与延后名单 → 必须报", ["A"], ["A"], ["C"], 1),
        ("★ 反例：同一人在延后与受阻 → 必须报", ["A"], ["B"], ["B"], 1),
        ("★ 反例：名字带空格/大小写差异也要认出来",
         ["Clara Barton"], ["clara  barton"], [], 1),
        ("正例：同姓不同人 → 不该报", ["William Paton"], ["William Agnew Paton"], [], 0),
        # ★★ 双语名（2026-08-13 补）：名册写双语、延后名单写单语，
        #   按全名规范化一比 `田口玄一genichitaguchi` ≠ `genichitaguchi`，本件曾对 12 人全盲，
        #   实测漏掉 Taguchi 与 Carmack 两条**真重复**。
        ("★★ 双语名：名册双语、延后单语 → 必须报",
         ["田口玄一 Genichi Taguchi"], ["Genichi Taguchi"], [], 1),
        ("★★ 双语名：括号形式 → 必须报",
         ["John Carmack（约翰·卡马克）"], ["John Carmack"], [], 1),
        ("★★ 双语名：斜杠形式 → 必须报",
         ["Reed Hastings / 里德·哈斯廷斯"], ["Reed Hastings"], [], 1),
        ("★★ 双语名：只给中文那半也要认出来",
         ["大野耐一 / Taiichi Ohno"], ["大野耐一"], [], 1),
        # ★ 反例：投影不许把不同的人并起来
        ("★ 反例：双语名 vs 另一个人 → 不该报",
         ["John Carmack（约翰·卡马克）"], ["John Maeda"], [], 0),
        ("★ 反例：两个中文名不同 → 不该报",
         ["大野耐一 / Taiichi Ohno"], ["新乡重夫"], [], 0),
        ("★ 反例：拉丁投影太短不算（`Li Lu`）", ["李录 Li Lu"], ["Lu Xun"], [], 0),
    ]
    for name, prods, defer, block, want in CASES:
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            g = root / "team-index.json"
            g.write_text(json.dumps({"products": [{"canonical_name": x} for x in prods]}),
                         encoding="utf-8")
            led = root / "_ledgers"
            led.mkdir()
            (led / "_延后名单.json").write_text(
                json.dumps({"deferred": [{"name": x} for x in defer]}), encoding="utf-8")
            (led / "_受阻待裁.json").write_text(
                json.dumps({"blocked": [{"name": x} for x in block]}), encoding="utf-8")
            err, _ = check(g, led, root / "_none")
            got = 1 if err else 0
            print(f"  {'✓' if got == want else '✗'} {name}｜错 {err}")
            bad += 0 if got == want else 1
    # 台账读不到时必须报错而不是当空集
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        g = root / "team-index.json"
        g.write_text(json.dumps({"products": []}), encoding="utf-8")
        err, ls = check(g, root / "_nowhere", root / "_none")
        ok = err > 0 and any("读不到" in l for l in ls)
        print(f"  {'✓' if ok else '✗'} 台账读不到必须报错，不当空集"
              f"（[[empty-default-swallows-unknown]]）")
        bad += 0 if ok else 1
    print(f"\n自测：{'全过' if not bad else f'**{bad} 项不过**'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--group", default=str(GROUP))
    ap.add_argument("--ledgers", default=str(LEDGERS))
    ap.add_argument("--corpora", default=str(CORPORA))
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    errors, lines = check(pathlib.Path(a.group), pathlib.Path(a.ledgers),
                          pathlib.Path(a.corpora))
    for l in lines:
        print(l)
    print(f"\n错 {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
