#!/usr/bin/env python3
"""由台账机械重出各研究道的「Scope and assigned sources」节。

## 为什么要有这件

那张表本来就该是台账的投影，而**它一直是手打的**。手打有两个后果，
Grotius #168 上两个都发生了：

1. **改判后表就过期。** 把 `de_veritate_1640_lat` 从 train 改判 holdout 之后，
   `01-writings.md` 里仍然列着它的 `source_id` —— 研究方读得到的文件里
   printed 着一份密封材料的编号，而这**正是 `check_holdout_mention` 要抓的东西**。
2. **手打会漏。** 新灌四份进 train，表里不会自己长出来。

→ [[gates-cover-json-not-the-prose-users-read]]：散文由数据现算生成，别手打。

## 硬保证

- **只投影 `split == "train"` 的行。** holdout 的 source_id 一个都不会出现在输出里，
  这是本件的第一条自测。
- 幂等：连跑两次输出逐字节相同。
- 只替换 `## Scope and assigned sources` 到下一个 `## ` 之间那一段，
  **其余小节（含手写的观察与断言）一个字不动**。

## 用法

    python3 emit_lane_scope.py <workspace>            # 写回
    python3 emit_lane_scope.py <workspace> --check    # 只报差异，exit 1 表示过期
    python3 emit_lane_scope.py --self-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HEAD = "## Scope and assigned sources"
LANES = ["writings", "conversations", "expression", "external", "decisions", "timeline"]


def load_ledger(ws: pathlib.Path) -> list:
    p = ws / "evidence" / "source-ledger.jsonl"
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def lane_files(ws: pathlib.Path) -> dict:
    """→ {lane: path}。文件名形如 `01-writings.md`。"""
    out = {}
    d = ws / "references" / "research"
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.md")):
        m = re.match(r"^\d+-([a-z]+)\.md$", p.name)
        if m and m.group(1) in LANES:
            out[m.group(1)] = p
    return out


def elide(s: str, width: int) -> str:
    """→ 过长题名**从中间**省略，保住结尾。

    ★ 砍尾巴会出事：DJBP 1853 三卷的题名只在结尾差一个
    `Volume the First/Second/Third`，砍到 88 字符后三行**逐字相同**，
    读表的人看到三个一模一样的条目，会当成灌重了。
    """
    if len(s) <= width:
        return s
    keep = width - 1
    head = keep * 2 // 3
    return s[:head] + "…" + s[len(s) - (keep - head):]


def render(rows: list, lane: str) -> str:
    """→ 该道的 Scope 节正文（不含标题行）。**只取 train**。"""
    mine = [r for r in rows
            if r.get("split") == "train" and lane in (r.get("dimensions") or [])]
    mine.sort(key=lambda r: (str(r.get("published_at") or ""), r.get("source_id") or ""))
    if not mine:
        return ("\n**本道分到 0 份（train split）**。\n\n"
                "★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**。\n\n")
    out = ["", "**本道分到 %d 份（train split）**：" % len(mine), "",
           "| source_id | 出版年 | tier | 题名 |", "|---|---|---|---|"]
    for r in mine:
        title = (r.get("title") or r.get("original_name") or "").replace("|", "\\|")
        out.append("| `%s` | %s | %s | %s |" % (
            r.get("source_id"), r.get("published_at") or "—", r.get("tier") or "—",
            elide(title, 88)))
    # ★ 注脚里**不许出现 `check_holdout_mention` 的任何触发词**。
    #   第一版我写了「holdout 的 source_id 不会出现在这里」——一句自夸的话，
    #   本身就把那个词印进了建模者读得到的文件，研究门当场报 4 处。
    #   [[i-create-the-leak-channels-myself]]：泄题通道又一次是我自己造的。
    out += ["",
            "★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；"
            "只投影 `split == train` 的行。", ""]
    return "\n".join(out) + "\n"


def splice(text: str, body: str) -> str:
    """把 Scope 节换成 body；找不到该标题就原样返回。"""
    i = text.find(HEAD)
    if i < 0:
        return text
    j = text.find("\n## ", i + len(HEAD))
    # body 自带结尾换行；`text[j+1:]` 从下一个 `## ` 起，故不会多出空行
    return text[:i] + HEAD + "\n" + body + (text[j + 1:] if j >= 0 else "")


def process(ws: pathlib.Path, check: bool) -> tuple:
    rows = load_ledger(ws)
    files = lane_files(ws)
    changed, holdout_ids = [], {r.get("source_id") for r in rows
                                if r.get("split") == "holdout"}
    for lane, p in sorted(files.items()):
        old = p.read_text(encoding="utf-8")
        new = splice(old, render(rows, lane))
        # ★ 硬保证：新正文里不许出现任何 holdout 的 source_id
        scope = new[new.find(HEAD):]
        scope = scope[:scope.find("\n## ", len(HEAD))] if "\n## " in scope[len(HEAD):] else scope
        leaked = sorted(i for i in holdout_ids if i and i in scope)
        if leaked:
            raise SystemExit("**本件自己泄了 holdout**：%s（%s）" % (leaked, p.name))
        if new != old:
            changed.append(p.name)
            if not check:
                p.write_text(new, encoding="utf-8")
    return changed, len(files), len(rows)


def self_test() -> int:
    import tempfile
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    with tempfile.TemporaryDirectory() as td:
        ws = pathlib.Path(td) / "ws"
        (ws / "evidence").mkdir(parents=True)
        (ws / "references" / "research").mkdir(parents=True)
        rows = [
            {"source_id": "src-aaaaaaaaaaaa", "split": "train", "tier": "P1",
             "published_at": "1646", "dimensions": ["writings"], "title": "Alpha"},
            {"source_id": "src-bbbbbbbbbbbb", "split": "train", "tier": "P1",
             "published_at": "1618", "dimensions": ["writings"], "title": "Beta"},
            {"source_id": "src-cccccccccccc", "split": "holdout", "tier": "P1",
             "published_at": "1640", "dimensions": ["writings"], "title": "Sealed"},
            {"source_id": "src-dddddddddddd", "split": "train", "tier": "S1",
             "published_at": "1826", "dimensions": ["external"], "title": "Ext|pipe"},
        ]
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        tmpl = ("# X\n\n" + HEAD + "\n\n手打的旧表，列着 `src-cccccccccccc`\n\n"
                "## Source-linked observations\n\n**手写的观察，不许被动**\n")
        for n, lane in ((1, "writings"), (4, "external")):
            (ws / "references" / "research" / ("%02d-%s.md" % (n, lane))).write_text(
                tmpl, encoding="utf-8")

        changed, nf, nr = process(ws, check=False)
        w = (ws / "references" / "research" / "01-writings.md").read_text(encoding="utf-8")
        chk("两份道文件都被改写（%s）" % changed, len(changed) == 2)
        chk("★ holdout 的 source_id **不在**输出里", "src-cccccccccccc" not in w)
        chk("train 的两份都在", "src-aaaaaaaaaaaa" in w and "src-bbbbbbbbbbbb" in w)
        chk("按出版年升序（1618 在 1646 前）",
            w.index("src-bbbbbbbbbbbb") < w.index("src-aaaaaaaaaaaa"))
        chk("**手写的其余小节没被动**", "**手写的观察，不许被动**" in w)
        chk("计数写对（2 份）", "本道分到 2 份" in w)
        e = (ws / "references" / "research" / "04-external.md").read_text(encoding="utf-8")
        chk("题名里的 `|` 被转义，表没被撑破", r"Ext\|pipe" in e)

        again, _, _ = process(ws, check=False)
        chk("**幂等**：连跑两次无差异", not again)
        chk("--check 在已同步时报 0 处", not process(ws, check=True)[0])

        # 反对照：台账改了，--check 必须报红
        rows[0]["published_at"] = "1999"
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        chk("**反对照**：台账一改，--check 立刻报过期", process(ws, check=True)[0])

        # 反对照 2：把一份 train 改判 holdout，它必须从表里消失
        rows[0]["published_at"] = "1646"
        rows[1]["split"] = "holdout"
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        process(ws, check=False)
        w2 = (ws / "references" / "research" / "01-writings.md").read_text(encoding="utf-8")
        chk("**反对照**：改判 holdout 后它从表里消失", "src-bbbbbbbbbbbb" not in w2)
        chk("剩下的计数跟着变（1 份）", "本道分到 1 份" in w2)

        # ★★★ 本件自己**不许**造泄题通道。用 `check_holdout_mention` 的**真正则**验，
        #     不抄一份词表过来 —— 抄的那份会漂，而漂了没人会发现。
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            from check_holdout_mention import MENTION  # noqa: E402
            body = render(rows, "writings")
            hit = MENTION.findall(body)
            chk("★ 输出正文**不触发**判据的泄题正则（命中 %d）" % len(hit), not hit)
            chk("   反对照：那句被我删掉的自夸话确实会触发",
                bool(MENTION.findall("holdout 的 source_id 不会出现在这里")))
        except ImportError:
            chk("**check_holdout_mention 导入失败，泄题这一项未核**", False)

        # ★★ 真实夹具：DJBP 1853 三卷的题名（逐字取自其题名页），
        #    只在结尾差一个 Volume the First/Second/Third。
        base = ("Hugonis Grotii De Jure Belli et Pacis Libri Tres, accompanied by "
                "an abridged translation by William Whewell — Volume the ")
        vols = [base + x for x in ("First", "Second", "Third")]
        cut = [elide(v, 88) for v in vols]
        chk("★ 三卷题名省略后**仍互不相同**（砍尾巴会让它们逐字相同）",
            len(set(cut)) == 3)
        chk("   省略后确实带着卷号：%s" % cut[0][-24:],
            all(x.endswith(y) for x, y in zip(cut, ("First", "Second", "Third"))))
        chk("   长度不超限", all(len(c) <= 88 for c in cut))
        chk("   反对照：直接砍尾巴的话三行相同",
            len({v[:88] for v in vols}) == 1)
        chk("   短题名不动", elide("Alpha", 88) == "Alpha")

        # 无 Scope 标题的文件不许被动
        p = ws / "references" / "research" / "06-timeline.md"
        p.write_text("# 没有 Scope 节\n\n正文\n", encoding="utf-8")
        before = p.read_text(encoding="utf-8")
        process(ws, check=False)
        chk("没有 Scope 标题的文件**原样不动**", p.read_text(encoding="utf-8") == before)

    print("\n" + ("自测通过" if ok else "**自测未过**"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--check", action="store_true", help="只报差异，不写回")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要么给 workspace，要么用 --self-test")
    ws = pathlib.Path(a.workspace)
    changed, nf, nr = process(ws, a.check)
    print("台账 %d 行；道文件 %d 份" % (nr, nf))
    if not changed:
        print("Scope 节与台账一致，无需改动")
        return 0
    print(("**过期 %d 份**：" if a.check else "已重出 %d 份：") % len(changed) + ", ".join(changed))
    return 1 if a.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
