#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**逐源归属门**：`attribution_basis` 是给人物开的，不是给每一本书开的免检。

## 它堵的是我自己开的口子

v0.0.0.24 给 `subject_origin: historical` 开了一条路：前印刷时代人物身上
`A-byline` 等五种署名证据结构上不存在，所以归属改由 `meta.json:attribution_basis` 认定。

**这条路把逐源检查整个关掉了。** 研究门当时是这么报的：

> 「**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定」
> 「14 条无 A-* 证据，**已按已声明的归属依据放行**」

**一份声明，放行全部。** 只要 `ingest.py --author` 里打了人物的名字，
一本不是他写的书就能坐进 P1，算进 `primary_ratio`，被断言层当亲笔引用。

## Jenner #104 实测：一本题献给他的书，被当成了他写的书

`b22006345` 扉页：

> A COMPARATIVE STATEMENT OF FACTS AND OBSERVATIONS RELATIVE TO THE COW-POX;
> **PUBLISHED By Doctors JENNER and WOODVILLE**

题献页：

> To Doctors JENNER and WOODVILLE / THIS COMPARATIVE STATEMENT is
> RESPECTFULLY INSCRIBED BY **THEIR OBEDIENT SERVANT, THE AUTHOR**

**这是第三方拿两人已发表的事实做对照，题献给他们两个。** 而它以
`P1 / writings / author="Edward Jenner"` 入了库，并进了断言与答案。

**注意 `check_authorship.py` 的 `BYLINE` 一处都没命中**——它没被骗，
它压根没被问。放行的是 historical 那条免检路。

## 判据三条

对每一条 `tier == P1` 且 `author` 等于人物名的源：

1. **有 A-* 证据 → 过。**（`check_authorship` 已认定的，本门不重复判。）
2. **无 A-* 证据，但在 `attribution_basis` 里被点名 → 过。**
   点名的判据：源的 `locator` 或 `original_name` 出现在 `attribution_basis`
   的 `citation` 或 `covered_sources` 里。**「点名」必须是逐份的，不是一句概括。**
3. **无 A-* 证据也没被点名 → 判错。** 报文里带上该源的开头 200 字，
   **强制人去看一眼扉页**。

## 射程（必须一起说）

- **它判「这一份有没有被逐份认领」，不判「认领得对不对」。**
  在 `citation` 里写上一个错的书名，本门照样放行——**它挡的是「整批免检」，
  不挡「点名点错了」。**
- 第 3 条的报文只给开头 200 字，**不替人读扉页**。
  Jenner 那次的真相在题献页，不在第一屏。
- **它不判 P2／S1。** 别人写的东西本来就不该声称是他写的。

退出码：0 = 通过；1 = 有未认领的 P1 源；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys


def evaluate(meta: dict, sources: list[dict], root: pathlib.Path | None = None
             ) -> tuple[list[str], dict]:
    """→ (问题列表, 计量)"""
    name = (meta.get("target_name") or meta.get("name") or "").strip()
    origin = meta.get("subject_origin")
    basis = meta.get("attribution_basis") or {}
    covered_blob = " ".join(str(basis.get(k, "")) for k in
                            ("citation", "authority", "covered_sources", "counting_convention"))
    if isinstance(basis.get("covered_sources"), list):
        covered_blob += " " + " ".join(str(x) for x in basis["covered_sources"])

    # ★ 只管 historical —— **免检口子只在这条路上存在**。
    #   其他 subject_origin 走的是 check_authorship 的 A-* 证据路，本门不该插手：
    #   第一版没设这道限，把 6 个合成测试工作区一起拦了（它们不是 historical，
    #   也从不声明 attribution_basis）。**判据的射程写错了，是判据的错，不是测试的错。**
    if origin != "historical":
        return [], {"subject_origin": origin,
                    "状态": "**本门不适用**——免检口子只在 historical 路上存在，"
                            "其他 subject_origin 由 check_authorship 的 A-* 证据路认定"}
    claimed = [s for s in sources
               if s.get("tier") == "P1" and (s.get("author") or "").strip() == name]
    problems, unclaimed, by_evidence, by_basis = [], [], 0, 0

    for s in claimed:
        kinds = s.get("authorship_evidence") or s.get("evidence_kinds") or []
        if any(str(k).startswith("A-") for k in kinds):
            by_evidence += 1
            continue
        loc = str(s.get("locator") or "")
        orig = str(s.get("original_name") or "")
        stem = orig.rsplit(".", 1)[0]
        named = any(tok and tok in covered_blob for tok in (loc, orig, stem))
        if named:
            by_basis += 1
            continue
        unclaimed.append(s)

    for s in unclaimed:
        head = ""
        if root is not None and s.get("local_path"):
            p = root / s["local_path"]
            if p.is_file():
                head = " ".join(p.read_text(encoding="utf-8", errors="replace")[:1200].split())[:200]
        problems.append(
            f"`{s.get('source_id')}` {s.get('original_name')} —— "
            f"声称 `{name}` 所著，**既无 A-* 署名证据，也未在 attribution_basis 里被逐份点名**。"
            + (f"\n      扉页开头：{head}…\n      **去看一眼扉页。**" if head else ""))

    info = {
        "subject_origin": origin,
        "声称本人所著的 P1 源": len(claimed),
        "靠 A-* 署名证据认定": by_evidence,
        "靠 attribution_basis 逐份点名认定": by_basis,
        "**未被逐份认领**": len(unclaimed),
        "口径": ("**判「有没有被逐份认领」，不判「认领得对不对」**——"
                 "在 citation 里写个错书名，本门照样放行。它挡的是整批免检。"),
    }
    return problems, info


# ── 负对照 ────────────────────────────────────────────────────────────
# ★ 真实样本：下面这段是 2026-08-02 实际入了库的 `b22006345.txt` 的开头，逐字取自落盘文件。
REAL_NOT_HIS = ("A COMPARATIVE STATEMENT OF FACTS AND OBSERVATIONS RELATIVE TO THE COW-POX; "
                "PUBLISHED By Doctors JENNER and JVOODVILLE . AUDI ALTERAM PARTEM. "
                "PRINTED AND SOLD BY SAMPSON LOW, No. 7, BERWICK STREET, SOHO ... 1800. "
                "To DoHors JENNER and WOQDVILLE THIS COMPARATIVE STATEMENT is RESPECTFULLY "
                "INSCRIBED BY THEIR OBEDIENT SERVANT, THE AUTHOR")
# ★ 真实样本：真正是他写的那一本，1798 初版扉页。
REAL_HIS = ("AN INQUIRY INTO THE CAUSES AND EFFECTS OF THE VARIOLAE VACCINAE ... "
            "BY EDWARD JENNER, M. D. F. R. S. &c. QUID NOBIS CERTIUS IPSIS SENSIBUS ESSE POTEST "
            "... London; PRINTED, FOR THE AUTHOR, BY SAMPSON LOW, N°. 7, BERWICK STREET, SOHO.")

META = {"target_name": "Edward Jenner", "subject_origin": "historical",
        "attribution_basis": {"citation": "1798《Inquiry》初版：archive.org/b24759247",
                              "authority": "扉页署名 Edward Jenner, M.D. F.R.S."}}


def self_test() -> int:
    fails = []

    # ★ 真实样本 1：题献给他、不是他写的那本 → 必须报
    bad = {"source_id": "src-6d5211d60581", "tier": "P1", "author": "Edward Jenner",
           "locator": "archive.org/b22006345", "original_name": "b22006345.txt"}
    probs, info = evaluate(META, [bad])
    if not probs:
        fails.append("真实样本 1 未抓出：题献给他的第三方著作被当成亲笔")

    # ★ 真实样本 2：真是他写的、且在 basis 里被点名 → 不许误杀
    good = {"source_id": "src-f38076294dd1", "tier": "P1", "author": "Edward Jenner",
            "locator": "archive.org/b24759247", "original_name": "b24759247.txt"}
    probs, info = evaluate(META, [good])
    if probs:
        fails.append(f"真实样本 2 被误杀：basis 里点了名的源却报 {probs}")

    # 正对照：有 A-* 证据 → 过（本门不重复判）
    withev = dict(bad, authorship_evidence=["A-byline"])
    if evaluate(META, [withev])[0]:
        fails.append("有 A-* 署名证据的源不该由本门再报")

    # 正对照：P2 别人写的 → 本门不管
    p2 = {"source_id": "x", "tier": "P2", "author": "Benjamin Moseley",
          "locator": "archive.org/b22041862", "original_name": "b22041862.txt"}
    if evaluate(META, [p2])[0]:
        fails.append("P2 他人著作不该由本门报")

    # 正对照：P1 但 author 不是本人（如译者）→ 本门不管
    tr = {"source_id": "y", "tier": "P1", "author": "translator",
          "locator": "archive.org/x", "original_name": "x.txt"}
    if evaluate(META, [tr])[0]:
        fails.append("author 非本人的 P1 源不该由本门报")

    # ★ 射程边界：非 historical 工作区**一条都不该报**
    #   （第一版漏了这道限，把 6 个合成测试工作区一起拦了）
    for og in ("public", "private", "self", "fictional", None):
        probs, info = evaluate(dict(META, subject_origin=og), [bad])
        if probs:
            fails.append(f"射程越界：subject_origin={og} 不该由本门报，实得 {probs[:1]}")

    # ★ 反向对照：把 basis 清空，**真样本 2 必须转红**
    #   —— 证明放行它的确实是「逐份点名」，不是别的什么巧合。
    empty = dict(META, attribution_basis={})
    if not evaluate(empty, [good])[0]:
        fails.append("反向对照失败：清空 attribution_basis 后，未点名的源仍被放行"
                     "——说明放行靠的不是逐份点名")

    # ★★ 复现 v0.0.0.24 那条口子：**整批免检**必须被本门堵住。
    #   旧行为是「只要声明了 basis，全部 P1 放行」；本门要求逐份点名。
    many = [dict(bad, source_id=f"src-{i:012x}", original_name=f"unknown{i}.txt",
                 locator=f"archive.org/unknown{i}") for i in range(14)]
    probs, info = evaluate(META, many)
    if len(probs) != 14:
        fails.append(f"整批免检未被堵住：14 份未点名的源只报了 {len(probs)} 份")

    # ── ★★★ 2026-08-17：三条支路的措辞各自钉住（子进程断言，印字在 main() 里）──
    #   缺陷形态：`problems` 为空就打「✓ 每一份声称亲笔的 P1 源都被逐份认领过」，
    #   而空可以来自三种完全不同的情形：真都认领过 / 本门不适用 / 一份都没有。
    #   全库 54 个实测：**9 个走「不适用」、jefferson 走「0 份」**。
    import subprocess as _sp, sys as _sys, tempfile as _tf, json as _json
    _self = str(pathlib.Path(__file__).resolve())

    def _run_ws(meta: dict, srcs: list) -> str:
        with _tf.TemporaryDirectory() as _td:
            w = pathlib.Path(_td) / "ws"; (w / "evidence").mkdir(parents=True)
            (w / "meta.json").write_text(_json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            (w / "evidence" / "source-ledger.jsonl").write_text(
                "".join(_json.dumps(x, ensure_ascii=False) + "\n" for x in srcs), encoding="utf-8")
            return _sp.run([_sys.executable, _self, str(w)], capture_output=True, text=True).stdout

    _m_hist = dict(META)
    _o_na = _run_ws({**_m_hist, "subject_origin": "public"}, [])
    if not ("本门不适用 —— 本次未核" in _o_na and "都被逐份认领过" not in _o_na):
        fails.append("★★★ subject_origin≠historical → 该说「不适用，未核」，不许打 ✓")
    _o_zero = _run_ws(_m_hist, [])
    if not ("0 份 —— 本次未核" in _o_zero and "都被逐份认领过" not in _o_zero):
        fails.append("★★★ historical 但声称亲笔的 P1 源 0 份 → 该说「未核」，不许打 ✓")
    # ★ META 的键是 `target_name`（不是 `name`）—— 今天第七次凭猜读键，读一眼比猜快。
    _ok_src = {"source_id": "s1", "tier": "P1", "author": META["target_name"],
               "authorship_evidence": ["A-1"], "original_name": "x.txt"}
    _o_ok = _run_ws(_m_hist, [_ok_src])
    if not ("都被逐份认领过" in _o_ok and "未核" not in _o_ok):
        fails.append("★★★ 反对照：真有 1 份且已认领 → 必须照旧打 ✓ 且不许说未核")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：**两条真实样本各自判对**（题献给他的第三方著作被抓出；"
          "basis 里点了名的亲笔著作未被误杀）；有 A-* 证据的、P2 的、author 非本人的三类未被误报；"
          "**清空 attribution_basis 后已点名的源转红**（证明放行靠的是逐份点名）；"
          "**14 份未点名的源全部报出**（复现并堵住 v0.0.0.24 的整批免检）；**非 historical 的五种 subject_origin 一条都不报**（射程边界）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="逐源归属门：attribution_basis 不是每本书的免检")
    ap.add_argument("target", nargs="?", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.target or not a.target.is_dir():
        print("用法错误：需要工作区目录（或 --self-test）", file=sys.stderr)
        return 3

    meta_p = a.target / "meta.json"
    led_p = a.target / "evidence/source-ledger.jsonl"
    if not meta_p.is_file() or not led_p.is_file():
        print("用法错误：缺 meta.json 或 evidence/source-ledger.jsonl", file=sys.stderr)
        return 3
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    sources = [json.loads(l) for l in led_p.read_text(encoding="utf-8").splitlines() if l.strip()]
    problems, info = evaluate(meta, sources, root=a.target)

    if a.json:
        print(json.dumps({"problems": problems, "info": info}, ensure_ascii=False, indent=1))
        return 1 if problems else 0
    print(json.dumps(info, ensure_ascii=False, indent=1))
    if problems:
        print(f"\n✗ {len(problems)} 份 P1 源未被逐份认领：\n")
        for p in problems:
            print(f"  - {p}")
        print("\n  ↑ **`attribution_basis` 是给人物开的，不是给每一本书开的免检。**"
              "\n  Jenner #104 实测：一本题献给他的第三方著作以 P1 亲笔入了库，"
              "\n  被断言层引用，算进了 primary_ratio。**归属门没被骗——它压根没被问。**")
        return 1
    # ★★★ 2026-08-17：**不适用 ≠ 通过**，**0 份可查 ≠ 全都认领过**。
    #   `evaluate()` 对 subject_origin != historical 直接返回 `[], {"状态": "本门不适用"}`，
    #   而这里照打「✓ 每一份声称亲笔的 P1 源都被逐份认领过」并 rc=0。
    #   全库 54 个实测：**9 个工作区**走的正是这条路
    #   （brandeis／burbank／churchill／dewey／fleming／ford／godin／leonardo／steinhardt）。
    #   仓里已有正确先例：`check_persona_frame_break` 对「不适用」把 `通过` 置 **None**，
    #   并在消费点写明「**不当成通过也不当成失败**」。照它办。
    #   ★ 只改措辞、**不改退出码**（收紧判定属决定不属清理）。
    #   [[zero-hit-gates-must-prove-they-can-hit]]
    if "本门不适用" in str(info.get("状态", "")):
        print("\n⚠ **本门不适用 —— 本次未核，不是通过。**")
        print("   免检口子只在 `subject_origin == historical` 上存在；"
              "这个工作区是 `%s`，" % info.get("subject_origin"))
        print("   由 `check_authorship` 的 A-* 证据路认定。**本件一份也没查过。**")
        return 0
    # ★ 份数直接读 `info` 里已有的字段，**不新造**（仓里有就别再造一个）。
    claimed_n = info.get("声称本人所著的 P1 源", 0)
    if not claimed_n:
        print("\n⚠ **声称亲笔的 P1 源 0 份 —— 本次未核，不是通过。**")
        print("   本件只查「声称亲笔的 P1 源有没有被逐份认领」；这个工作区一份也没有。")
        return 0
    print("\n✓ 全部 **%d** 份声称亲笔的 P1 源都被逐份认领过" % claimed_n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
