#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同一部作品的多个译本，**不许当成两处独立证据**。

## 立这件判据的那次事故（2026-08-10，Pacioli #161）

`check_claim_source_independence` 的作品分组**是语言盲的**：它按 8 词片的词面重叠
分组，**跨语种的同一部作品一份都认不出来**。实测 Pacioli 的 10 份源被它分成
**10 个作品组**，而其中三份——`crivelli-1924`（英）／`geijsbeek-1914`（英）／
`pacioli-1896-dutch`（荷）——**译的是同一篇《Particularis de computis et scripturis》**。

于是「mental-model／heuristic／value／work-method 各要 ≥2 处独立证据」这条门，
**可以靠引两种译本轻松过掉**，而那实质上仍是一处证据。

★ 同一批材料还牵出另一件事：全库最像「他的思维模型」的那句
`Accounts are nothing else than the expressions in writing of the arrangement of
his affairs` **不是他的**——它在 Geijsbeek 的带页码格言摘要里，Crivelli 逐字搜 0 命中。
**那件事本件管不了**（见文末），本件只管「算几处证据」。

## 判法：**只查申报，不猜**

1. `meta.json` 的 `attribution_basis.parallel_witnesses` = `[[sid, sid, ...], ...]`，
   每组表示「这些来源是同一部作品的不同见证」。
2. **组内成员必须是真实存在的 source_id**（写错 id 会让整条纪律静默失效）。
3. **★ 真正的门**：任一断言的 `source_ids` 里若出现**同一组的 ≥2 个成员**，
   它的「两处来源」是假的 → **报错**。
   同理 `evidence_clusters` 若把同组的两份算成两簇 → 报错。

## ★★★★ 「自动认出哪些是译本」这一半，**实测做不出来，已砍掉**

第一版按罕见词（本份内出现 2–6 次）的 Jaccard 自动认组，阈值 0.060 ——
**那个阈值是在 Pacioli 一个工作区上标定的**，而全库一跑：

| 工作区 | 两两对 | J≥0.060 |
|---|---:|---:|
| clara-barton | 22,791 | **10,502** |
| rudolf-virchow | 25,651 | **6,973** |
| florence-nightingale | 6,786 | 3,727 |
| **全库合计** | — | **38,368** |

**它量的是「用词像不像」，不是「是不是同一部作品的译本」。**
同作者同题材同年代的语料天然就高。

★ **而且没有任何固定阈值可用**：Pacioli 的真阳性在 **0.080–0.102**，
而别处的噪声常态在 **0.12–0.19**——**真信号低于别处的噪声。**

改按各工作区自身分布取离群（≥99.5 分位且 ≥3× 中位）后降到约 250 对，
**但高分段全是近乎相同的文件**（Barton 0.995、Virchow 0.967）——
那是**重复源**，已由 `check_source_dedup.py` 管着（Blackwell 61 对就是它报的）；
**而 Pacioli 的两对真阳性被砍掉一对。**

**结论：这一半是个更差的重复源检测器，不是译本检测器。整段拿掉。**
[[samples-cannot-support-universal-claims]]：拿一个工作区标的尺子推到全库。

### 那「哪些是同一部作品的译本」靠什么

**靠人在建源时申报。** 抓源时本来就知道自己抓的是谁的哪一版译本，
`ingest.py` 的 `--abstract` 里也写着。**知道的时候写下来，比事后猜便宜得多。**

### 「某句是不是译者的编者话」又靠什么

**靠人跑一条固定动作**（也实测过自动化，同样分不开，数字附后）：

```
要引某句当「他的原话」之前，把句中最具体的那 2–3 个词组
拿到并行见证里逐字搜，**读命中**。
两份都有 → 是原著的；只有一份有 → 是那位译者的，不许当他的话引。
```

自动化失败的实测：按「另一份见证同窗覆盖率」判，**事故句 60% ＞ 真段落 56%，顺序是反的**；
按词频加权后反最高 61.0% vs 正最低 61.8%，**只差 0.8 个百分点**——
7 个例子上 0.8pp 是噪声不是判据（[[gate-below-instrument-noise]]）。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def load_ledger_ids(ws: pathlib.Path) -> set[str]:
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        return set()
    out = set()
    for line in led.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.add(json.loads(line).get("source_id"))
    return out


def declared_groups(ws: pathlib.Path) -> list[list[str]]:
    meta = ws / "meta.json"
    if not meta.is_file():
        return []
    d = json.loads(meta.read_text(encoding="utf-8"))
    raw = (d.get("attribution_basis") or {}).get("parallel_witnesses") or []
    return [g for g in raw if isinstance(g, list)]


def check(ws: pathlib.Path) -> tuple[int, int, list[str]]:
    lines: list[str] = []
    groups = declared_groups(ws)
    ids = load_ledger_ids(ws)
    if not ids:
        return 0, 0, ["状态：读不到来源台账，**未核验（不是通过）**"]
    if not groups:
        return 0, 0, [
            f"申报的并行见证组 0 个（来源 {len(ids)} 份）",
            "★ **0 组不等于没有并行见证**——本件不猜，只查申报。"
            "抓源时若取了同一部作品的多份译本／版本，**在 meta.json 的 "
            "attribution_basis.parallel_witnesses 里写下来**。"]

    errors = 0
    member_of: dict[str, int] = {}
    for i, g in enumerate(groups):
        for sid in g:
            if sid not in ids:
                errors += 1
                lines.append(f"✗ 第 {i + 1} 组申报了台账里没有的 source_id：{sid}"
                             f"（写错 id 会让整条纪律**静默失效**）")
            member_of.setdefault(sid, i)
    lines.append(f"申报的并行见证组 {len(groups)} 个，覆盖 {len(member_of)} 份来源")

    cj = ws / "evidence" / "claims.jsonl"
    checked = collapsed = 0
    if cj.is_file():
        for line in cj.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c.get("status") in {"superseded", "unknown"}:
                continue
            checked += 1
            by_group: dict[int, list[str]] = {}
            for sid in set(c.get("source_ids", [])):
                if sid in member_of:
                    by_group.setdefault(member_of[sid], []).append(sid)
            for gi, members in by_group.items():
                if len(members) >= 2:
                    collapsed += 1
                    errors += 1
                    lines.append(
                        f"✗ {c.get('claim_id', '<无 id>')}（{c.get('category')}）"
                        f"把同一部作品的 {len(members)} 份见证当成了 {len(members)} 处来源："
                        f"{sorted(members)}\n"
                        f"    → **它们是同一部作品的不同译本／版本，只算一处。**"
                        f"「≥2 处独立证据」实际未达成。")
    lines.append(f"断言核了 {checked} 条，**同组塌缩 {collapsed} 条**")
    return errors, collapsed, lines


# ---------------------------------------------------------------- 自测
def self_test() -> int:
    import tempfile
    bad = 0
    CASES = [
        ("正例：两处来源分属不同组 → 不该报",
         [["A", "B"], ["C", "D"]], ["A", "C"], 0),
        ("★ 反例：两处来源是同一部作品的两个译本 → 必须报",
         [["A", "B"], ["C", "D"]], ["A", "B"], 1),
        ("反例：三份译本全引了 → 必须报",
         [["A", "B", "E"]], ["A", "B", "E"], 1),
        ("正例：一份在组里、一份不在 → 不该报",
         [["A", "B"]], ["A", "Z"], 0),
        ("★ 反例：申报了台账里没有的 id → 必须报",
         [["A", "NOPE"]], ["A"], 1),
    ]
    for name, groups, sids, want in CASES:
        with tempfile.TemporaryDirectory() as d:
            ws = pathlib.Path(d)
            (ws / "evidence").mkdir()
            (ws / "evidence" / "source-ledger.jsonl").write_text(
                "\n".join(json.dumps({"source_id": s}) for s in "ABCDEZ"),
                encoding="utf-8")
            (ws / "meta.json").write_text(json.dumps(
                {"attribution_basis": {"parallel_witnesses": groups}}), encoding="utf-8")
            (ws / "evidence" / "claims.jsonl").write_text(json.dumps(
                {"claim_id": "c1", "category": "heuristic", "status": "pattern",
                 "source_ids": sids}, ensure_ascii=False), encoding="utf-8")
            err, _, _ = check(ws)
            got = 1 if err else 0
            print(f"  {'✓' if got == want else '✗'} {name}｜错 {err}（应{'报' if want else '不报'}）")
            bad += 0 if got == want else 1
    # 未申报时必须明说「未核验」而不是「通过」
    with tempfile.TemporaryDirectory() as d:
        ws = pathlib.Path(d)
        (ws / "evidence").mkdir()
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            json.dumps({"source_id": "A"}), encoding="utf-8")
        (ws / "meta.json").write_text("{}", encoding="utf-8")
        _, _, ls = check(ws)
        ok = any("不等于没有" in l for l in ls)
        print(f"  {'✓' if ok else '✗'} 空默认值不得读成通过"
              f"（[[empty-default-swallows-unknown]]）")
        bad += 0 if ok else 1
    print(f"\n自测：{'全过' if not bad else f'**{bad} 项不过**'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test or not a.workspace:
        return self_test()
    ws = pathlib.Path(a.workspace).resolve()
    if not ws.is_dir():
        print(f"✗ 不是目录：{ws}", file=sys.stderr)
        return 2
    errors, collapsed, lines = check(ws)
    for l in lines:
        print(l)
    print(f"\n错 {errors}｜同组塌缩 {collapsed}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
