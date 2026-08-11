#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四本名册**互不重叠**——「别让人同时留在两处」这条规矩此前没有判据。

## 规矩写在哪

`_受阻待裁.json` 自己的「★★ 怎么用」里写着：

> ① 用户裁定某一条之后，把对应的人从这里挪走——入库就进 `team-index`，
>   判不做就进 `_延后名单.json`。**别让人同时留在两处。**

**规矩在，判据不在**（[[every-requirement-needs-an-owner]]）。
一个人同时挂在「已入库」和「延后」两处，
`next_person.py` 的排期、分族配重、周报计数会同时把他算进两边。

## 判什么

三对交集必须为空：

    延后/拒发 ∩ 已入库　　延后/拒发 ∩ 受阻待裁　　受阻待裁 ∩ 已入库

## ★★★ 为什么第一件事是断言「集合不是空的」

2026-08-11 我第一次手跑这个核对时，`team-index.json` 的键取错了
（用 `name`／`person` 去取，而那份文件里叫 `canonical_name`），
**已入库集合只拿到 1 个**，于是三对交集全是 0，报「干净」。

**空集合让判据自动通过**——[[empty-default-swallows-unknown]]。
所以本件先断言三个来源都读到了合理数量，读不到就**退出 2（未核）而不是 0**。

用法：
    python3 check_roster_disjoint.py [--root <CodexSkills 根>]
    python3 check_roster_disjoint.py --self-test
"""
import argparse
import json
import pathlib
import sys

MIN_EXPECT = {"已入库": 50, "延后/拒发": 50, "受阻待裁": 0}


def load(root: pathlib.Path) -> dict:
    """→ {名册名: set(人名)}。读不出就抛，**不返回空集合冒充读到了**。"""
    led = root / "skill_log_evals/persona-distiller/_ledgers"
    idx = root / "registry/codex/persona-distiller-group/team-index.json"
    out = {}
    out["延后/拒发"] = {r["name"] for r in
                     json.loads((led / "_延后名单.json").read_text(encoding="utf-8"))["deferred"]}
    out["受阻待裁"] = {r["name"] for r in
                    json.loads((led / "_受阻待裁.json").read_text(encoding="utf-8"))["blocked"]}
    # ★ 键名是 `canonical_name`，不是 `name`——取错就只拿到 1 个，见文件头。
    out["已入库"] = {p["canonical_name"] for p in
                   json.loads(idx.read_text(encoding="utf-8"))["products"]}
    return out


def check(root: pathlib.Path) -> int:
    try:
        rosters = load(root)
    except Exception as exc:                                    # noqa: BLE001
        print(f"✗ 名册读不出，**未核（不是通过）**：{exc}")
        return 2
    thin = [(k, len(v), MIN_EXPECT[k]) for k, v in rosters.items()
            if len(v) < MIN_EXPECT[k]]
    for k, n, lo in thin:
        print(f"✗ 「{k}」只读到 {n} 条，低于合理下限 {lo}——"
              f"**这多半是键名取错，不是名册真的这么短**；空集合会让下面三对交集自动为 0")
    if thin:
        print("→ **未核（不是通过）**")
        return 2
    print("　".join(f"{k} {len(v)}" for k, v in rosters.items()))
    pairs = [("延后/拒发", "已入库"), ("延后/拒发", "受阻待裁"), ("受阻待裁", "已入库")]
    bad = 0
    for a, b in pairs:
        both = rosters[a] & rosters[b]
        bad += len(both)
        mark = "✗" if both else "✓"
        print(f"  {mark} {a} ∩ {b}：{len(both)}"
              + (f"　{sorted(both)[:6]}" if both else ""))
    if bad:
        print(f"\n✗ **{bad} 处同时留在两处**——排期、分族配重、周报计数都会把他算进两边。"
              f"\n  规矩见 `_受阻待裁.json` 的「★★ 怎么用」①：裁定之后要把人挪走。")
        return 1
    print("\n✓ 三对名册互不重叠")
    return 0


def self_test() -> int:
    import tempfile
    fails = []

    def chk(label, got, want):
        print(f"  {'✓' if got == want else '✗'} {label}"
              + ("" if got == want else f"　得 {got!r} 应为 {want!r}"))
        if got != want:
            fails.append(label)

    def build(d, deferred, blocked, products):
        led = d / "skill_log_evals/persona-distiller/_ledgers"
        led.mkdir(parents=True, exist_ok=True)
        (led / "_延后名单.json").write_text(json.dumps(
            {"deferred": [{"name": n} for n in deferred]}, ensure_ascii=False), encoding="utf-8")
        (led / "_受阻待裁.json").write_text(json.dumps(
            {"blocked": [{"name": n} for n in blocked]}, ensure_ascii=False), encoding="utf-8")
        idx = d / "registry/codex/persona-distiller-group"
        idx.mkdir(parents=True, exist_ok=True)
        (idx / "team-index.json").write_text(json.dumps(
            {"products": [{"canonical_name": n} for n in products]},
            ensure_ascii=False), encoding="utf-8")

    many_a = ["延后%d" % i for i in range(60)]
    many_b = ["入库%d" % i for i in range(60)]
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        build(d, many_a, [], many_b)
        chk("① 三册不相交 → 0", check(d), 0)
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        # ★ 反对照：一个人同时在延后与入库
        build(d, many_a + ["双挂的人"], [], many_b + ["双挂的人"])
        chk("② **有人同时留在两处 → 1**", check(d), 1)
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        # ★★ 反对照：入库集合读成空的（键名取错的等价物）——**不许报 0**
        build(d, many_a, [], [])
        chk("③ **入库读到 0 条 → 2（未核），不许当成干净**", check(d), 2)
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)
        chk("④ 文件不存在 → 2（未核）", check(d), 2)
    print(f"自测 4 项，失败 {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=pathlib.Path,
                    default=pathlib.Path(__file__).resolve().parents[4])
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    sys.exit(self_test() if a.self_test else check(a.root))
