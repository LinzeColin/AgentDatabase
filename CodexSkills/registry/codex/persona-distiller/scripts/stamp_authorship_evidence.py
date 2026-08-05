#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**把 `check_authorship` 的 A-* 结论盖回 source-ledger**——判据升级后，旧记录不会自己变。

## 为什么要它（Coffin #130 撞出来的）

`check_source_attribution` 判 `research.source-unclaimed` 时读的是**记录上的**
`authorship_evidence` 字段；而 `check_authorship` 是**现算**的。两者会脱节：

| | 现算（`check_authorship`） | 记录上（`authorship_evidence`） |
|---|---|---|
| Coffin #130 | **13/14 已证实** | **0/14** —— 全是 `None` |

于是同一次门里，`metrics.authorship` 说「已证实归属 13」，
而 `errors` 里躺着 **14 条 `research.source-unclaimed`**。**两个数彼此打架，我先信了错的那个。**

根因：`ingest.py` 落记录时判据还是旧版（**形态 D 专利题页署名尚未存在**），
落完之后判据升级了，**而记录不会回头重算**。

★ Thomson #129 的记录里有 `authorship_evidence: ['A-byline']`——
那是当时**每人一份的临时脚本**盖上去的，不在 `scripts/` 下、不进任何门、没有自测。
本项目已经为这种「每人一份的临时脚本」付过账（`build_source_ledger` 的文件头写着同一件事）：
**出现第 2 个人要用同一段逻辑时就收成共享件。** Coffin 是第 2 个。

## 它做什么

对 `evidence/source-ledger.jsonl` 里每条 **P1 且 author 是本人** 的记录：
跑一遍 `check_authorship.check_text`，把结论写回两个字段——
`authorship_evidence`（如 `["A-byline-ocr"]`）与 `authorship_detail`（含命中的原文片段）。

## ★ 它不做什么

- **不改分档、不改 lane、不改任何别的字段。** 只写这两个。
- **不凭空造证据。** 判据说没有就是没有，字段写空数组，
  该报 `source-unclaimed` 就让它报——**盖章不是放行**。
- **默认 dry-run。** 要真写必须 `--write`。
"""
import argparse
import importlib.util
import json
import pathlib
import sys


def _load_checker(scripts: pathlib.Path):
    spec = importlib.util.spec_from_file_location(
        "_pd_auth", scripts / "check_authorship.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stamp(target: pathlib.Path, scripts: pathlib.Path, write: bool = False) -> dict:
    meta = json.loads((target / "meta.json").read_text(encoding="utf-8"))
    name = (meta.get("target_name") or meta.get("name") or "").strip()
    mod = _load_checker(scripts)
    pat = mod.build_patterns(name)
    pat["namesakes"] = tuple(meta.get("known_namesakes") or ())
    pat["own_mid"] = str(meta.get("middle_initial") or "").strip().lower()[:1]

    led = target / "evidence" / "source-ledger.jsonl"
    rows = [json.loads(x) for x in led.read_text(encoding="utf-8").splitlines() if x.strip()]

    got, none_, skipped, changed = 0, 0, 0, []
    for r in rows:
        if r.get("tier") != "P1" or (r.get("author") or "").strip() != name:
            skipped += 1
            continue
        rel = r.get("normalized_path") or r.get("local_path")
        p = (target / rel) if rel else None
        if not p or not p.is_file():
            none_ += 1
            continue
        ok, code, ev, _counter = mod.check_text(
            p.read_text(encoding="utf-8", errors="replace"), pat)
        before = r.get("authorship_evidence")
        if ok:
            r["authorship_evidence"] = [code]
            r["authorship_detail"] = {"code": code, "evidence": ev[:400]}
            got += 1
        else:
            r["authorship_evidence"] = []
            r.pop("authorship_detail", None)
            none_ += 1
        if before != r.get("authorship_evidence"):
            changed.append(f"{r['source_id']} {before} → {r['authorship_evidence']}")

    if write:
        led.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                       encoding="utf-8")

    return {
        "人物": name,
        "台账行数": len(rows),
        "本门管的（P1 且署他名）": len(rows) - skipped,
        "**盖到 A-* 的**": got,
        "**判据说没有的**": none_,
        "改动": changed[:20],
        "写盘": "已写" if write else "**dry-run，没写**（要写加 --write）",
        "★ 口径": "**盖章不是放行**——判据说没有就写空数组，该报 source-unclaimed 就让它报。",
    }


def self_test() -> int:
    import tempfile
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    here = pathlib.Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td)
        (t / "evidence").mkdir(parents=True)
        (t / "raw" / "s1").mkdir(parents=True)
        (t / "raw" / "s2").mkdir(parents=True)
        (t / "meta.json").write_text(json.dumps({
            "target_name": "Charles L. Coffin",
            "known_namesakes": ["Charles A. Coffin"],
            "middle_initial": "L"}, ensure_ascii=False), encoding="utf-8")
        # s1：真题页署名　s2：**同名者的**题页署名
        (t / "raw/s1/a.txt").write_text("body\n" * 30 +
                                        "CHARLES L. OOFFIN, OF DETROIT, MICHIGAN.\n", encoding="utf-8")
        (t / "raw/s2/b.txt").write_text("body\n" * 30 +
                                        "CHARLES A. COFFIN, OF BOSTON, MASSACHUSETTS.\n", encoding="utf-8")
        rows = [
            {"source_id": "s1", "tier": "P1", "author": "Charles L. Coffin",
             "local_path": "raw/s1/a.txt"},
            {"source_id": "s2", "tier": "P1", "author": "Charles L. Coffin",
             "local_path": "raw/s2/b.txt"},
            {"source_id": "s3", "tier": "S1", "author": "third-party",
             "local_path": "raw/s1/a.txt"},
        ]
        (t / "evidence/source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

        print("── ★★★ 正向：专利题页署名要盖上 A-* ──")
        r = stamp(t, here, write=False)
        chk(f"盖到 1 条：{r['**盖到 A-* 的**']}", r["**盖到 A-* 的**"] == 1)
        chk(f"S1 那条不归本门管：管 {r['本门管的（P1 且署他名）']} 条", r["本门管的（P1 且署他名）"] == 2)

        print("\n── ★★★ 反向对照①：**同名者的署名不许盖章** ──")
        chk(f"判据说没有的 1 条：{r['**判据说没有的**']}", r["**判据说没有的**"] == 1)

        print("\n── ★★ 反向对照②：**默认 dry-run，不许偷偷写盘** ──")
        after = [json.loads(x) for x in
                 (t / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        chk(f"文件没被改：{after[0].get('authorship_evidence')}",
            after[0].get("authorship_evidence") is None)

        print("\n── ★★ 反向对照③：--write 之后才落盘，且同名者写的是空数组 ──")
        stamp(t, here, write=True)
        after = [json.loads(x) for x in
                 (t / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        chk(f"s1 盖上了：{after[0].get('authorship_evidence')}",
            after[0].get("authorship_evidence") == ["A-byline-ocr"])
        chk(f"s2 是空数组（**不是没有这个字段**）：{after[1].get('authorship_evidence')}",
            after[1].get("authorship_evidence") == [])
        chk("s3 一个字段都没动", "authorship_evidence" not in after[2])

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="人物工作区")
    ap.add_argument("--write", action="store_true", help="真写盘（默认 dry-run）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.target:
        ap.error("要么 --self-test，要么给工作区")
    t = pathlib.Path(a.target)
    if not (t / "evidence" / "source-ledger.jsonl").is_file():
        print(json.dumps({"状态": f"**未核（不是通过）**：{t} 下没有 evidence/source-ledger.jsonl"},
                         ensure_ascii=False))
        return 3
    print(json.dumps(stamp(t, pathlib.Path(__file__).resolve().parent, a.write),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
