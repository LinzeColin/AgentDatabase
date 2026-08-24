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
    assigned = [r for r in rows
                if r.get("split") == "train" and lane in (r.get("dimensions") or [])]
    # ★★ **抽取失败的源不算「分到」这道。**
    #   2026-08-17 实测：全库 3181 行里有 2 行 `extraction_status == "failed"` 却
    #   仍是 `split: train`，两行都被列进了各自研究道的 Scope 表，当成可用源计数——
    #     · Jefferson `01-writings.md`：一份 **3 字节、内容是 `\n\n\n`、0 词**的文件，
    #       列为 P1 一手源（archive.org 的 `_djvu.txt` 取回来是空的）；
    #     · Machiavelli `04-external.md`：一份 **41.68% 字符是天城文**的 OCR 垃圾，列为 S1。
    #   两份的失败理由**台账里早就写清楚了**，只是没人把它从「本道分到 N 份」里减掉。
    #   ⇒ 覆盖数被虚增，而虚增的方向是**让语料看起来比实际厚**。
    #
    #   ★ **不静默过滤。** 直接从表里删掉会让那一行整个消失，读的人分不清
    #   「没抓过」和「抓了是坏的」——后者是很贵的信息（别再去抓一次）。
    #   所以：不进表、不计数，但**单列一行写明它坏在哪**。
    #   [[filters-make-rows-vanish]]｜[[aggregator-ocr-can-be-silently-broken]]
    mine = [r for r in assigned if r.get("extraction_status") != "failed"]
    dead = [r for r in assigned if r.get("extraction_status") == "failed"]
    mine.sort(key=lambda r: (str(r.get("published_at") or ""), r.get("source_id") or ""))
    dead.sort(key=lambda r: (str(r.get("published_at") or ""), r.get("source_id") or ""))

    def dead_note():
        if not dead:
            return ""
        lines = ["", "★ **另有 %d 份取回来是坏的，不计入上面的份数**"
                 "（`extraction_status: failed`；保留在台账里是为了别再抓一次）：" % len(dead)]
        for r in dead:
            why = next((str(v)[:96] for k, v in r.items()
                        if k.startswith("★") and ("失败" in k or "OCR" in k)), "见台账该行")
            lines.append("- `%s` %s —— %s" % (
                r.get("source_id"), elide((r.get("title") or ""), 60), why))
        return "\n".join(lines) + "\n"

    if not mine:
        return ("\n**本道分到 0 份（train split）**。\n\n"
                "★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**。\n"
                + dead_note() + "\n")
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
    # ★★ 脚注**只在这道真有坏源时才改口**。
    #   第一版我无条件改成「且抽取成功」，结果全库 54 个工作区里 **29 个**当场变
    #   「过期」——其中 21 个是**已判分冻结**的（㊵），永远不能重生成，
    #   于是它们会永久停在「过期」状态。**为一句措辞把 21 份产物打成永久不一致，
    #   是净损失。** 没有坏源的道，渲染结果与改动前**逐字相同**。
    #   [[protecting-a-measurement-of-a-superseded-artifact]]
    tail = ("只投影 `split == train` **且抽取成功**的行。" if dead
            else "只投影 `split == train` 的行。")
    out += ["",
            "★ 本节由台账机械导出（`emit_lane_scope.py`），**不含任何阅读判断**；"
            + tail, ""]
    return "\n".join(out) + "\n" + dead_note()


def splice(text: str, body: str) -> str:
    """把 Scope 节换成 body；找不到该标题就原样返回。"""
    i = text.find(HEAD)
    if i < 0:
        return text
    j = text.find("\n## ", i + len(HEAD))
    # body 自带结尾换行；`text[j+1:]` 从下一个 `## ` 起，故不会多出空行
    return text[:i] + HEAD + "\n" + body + (text[j + 1:] if j >= 0 else "")


def scope_body(text: str) -> str:
    """→ Scope 节的正文（不含标题）。找不到返回空串。"""
    i = text.find(HEAD)
    if i < 0:
        return ""
    j = text.find("\n## ", i + len(HEAD))
    return text[i + len(HEAD):(j if j >= 0 else len(text))]


def dropped_lines(old: str, new: str) -> list:
    """→ 覆盖时会**丢掉的手写行**（老 Scope 节里有、新的里没有的实质行）。

    ★★★ 2026-08-11 实测逼出来的：Blackstone #169 的 `06-timeline.md` 是 0 源道，
    而我把模板的 `Pending.` 换成了自己写的两句判断
    （「本道是**印本年表不是生平年表**」「用的是扉页上逐字照录的印本年」）——
    于是上面那道「留着 Pending. 就不覆盖」的保护**不认识我写的东西**，
    重出时把它们**静默抹掉了**。

    本函数不阻止覆盖（Scope 节本就该由机器拥有），**只是不让它静默**：
    把要丢的行打出来，人自己决定搬到哪一节去。
    """
    have = {l.strip() for l in scope_body(new).splitlines() if l.strip()}
    out = []
    for l in scope_body(old).splitlines():
        s = l.strip()
        if not s or s in have:
            continue
        # 表格行与工具自己的说明不算手写
        if s.startswith("|") or s.startswith("★ 本节由台账机械导出"):
            continue
        if s.startswith("**本道分到") or s == "Pending. Use train-split source IDs only.":
            continue
        out.append(s)
    return out


def process(ws: pathlib.Path, check: bool) -> tuple:
    rows = load_ledger(ws)
    files = lane_files(ws)
    changed, holdout_ids = [], {r.get("source_id") for r in rows
                                if r.get("split") == "holdout"}
    dropped = {}
    for lane, p in sorted(files.items()):
        old = p.read_text(encoding="utf-8")
        # ★ 0 源的道若还留着模板原句，**不许覆盖**。
        #   模板写的是 `Pending. Use train-split source IDs only.` —— 那是给研究方的
        #   指示；用「本道分到 0 份」把它盖掉是净损失。全库实测：41 处「过期」
        #   全属此类，**一处真问题都不是**。[[read-the-hits-before-reporting-the-rate]]
        # ★ 这一处**有意不加** `extraction_status != "failed"`：它问的是
        #   「这道有没有分到**任何**东西」，而一份取回来是坏的源**也是分到了** ——
        #   要把「抓过、是坏的」这条信息写出去，就必须让这道进入重出流程。
        #   （render 里那一处才是「算不算进份数」，两处问的是不同的问题。）
        #   实测 2026-08-17：全库**没有**「唯一来源就是坏源」的道，所以这两处
        #   当前不会给出不同结论；写下来是为了下一个人不必再推一遍。
        #   [[one-requirement-two-consumers]]
        if not any(r.get("split") == "train" and lane in (r.get("dimensions") or [])
                   for r in rows):
            head = old.find(HEAD)
            if head >= 0:
                nxt = old.find("\n## ", head + len(HEAD))
                if "Pending." in old[head:nxt if nxt > 0 else len(old)]:
                    continue
        new = splice(old, render(rows, lane))
        # ★ 硬保证：新正文里不许出现任何 holdout 的 source_id
        scope = new[new.find(HEAD):]
        scope = scope[:scope.find("\n## ", len(HEAD))] if "\n## " in scope[len(HEAD):] else scope
        leaked = sorted(i for i in holdout_ids if i and i in scope)
        if leaked:
            raise SystemExit("**本件自己泄了 holdout**：%s（%s）" % (leaked, p.name))
        if new != old:
            changed.append(p.name)
            lost = dropped_lines(old, new)
            if lost:
                dropped[p.name] = lost
            if not check:
                p.write_text(new, encoding="utf-8")
    return changed, len(files), len(rows), dropped


def lanes_with_scope_section(ws: pathlib.Path) -> tuple:
    """→ (有 Scope 节的道文件数, 道文件总数)。**只为把分母印出来，不参与判定。**

    ★★ 2026-08-14 坐实的假绿就在这里：`splice()` 找不到 `## Scope and assigned
      sources` 时**原样返回**（见它的 docstring），于是**根本没有那一节**的
      研究稿永远「无差异」，`--check` 对着不存在的东西说「与台账一致」。
      全库实测 39 个有六道研究稿的工作区里：六份全有 27 个、**一份都没有 4 个**
      （Koch／Pasteur／Blackwell／Lister）、部分有 8 个。

    ★ **本轮只印分母，不改判定、不改退出码**：改判定会让 12 个工作区从「绿」
      变成「未检查」，其中四人已入库或已判分，而用户 8-12 的批次指令写着
      「门、席位一概不动」。诚实由**话**承载，绿不绿仍照旧。
      [[empty-default-swallows-unknown]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    """
    files = lane_files(ws)
    have = 0
    for p in files.values():
        try:
            if HEAD in p.read_text(encoding="utf-8"):
                have += 1
        except OSError:
            pass
    return have, len(files)


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

        changed, nf, nr, _ = process(ws, check=False)
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

        again, _, _, _ = process(ws, check=False)
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

        # ★ 0 源 + 模板原句 → 不许覆盖
        q = ws / "references" / "research" / "05-decisions.md"
        q.write_text("# D\n\n" + HEAD +
                     "\n\nPending. Use train-split source IDs only.\n\n"
                     "## Source-linked observations\n\nPending.\n", encoding="utf-8")
        before = q.read_text(encoding="utf-8")
        process(ws, check=False)
        chk("★ 0 源且还是模板 `Pending.` → **原样不动**（那句是给研究方的指示）",
            q.read_text(encoding="utf-8") == before)
        chk("   --check 也不该把它报成过期", "05-decisions.md" not in process(ws, check=True)[0])
        # 反对照：同样 0 源，但已被写过表 → 该清空
        q.write_text("# D\n\n" + HEAD + "\n\n| src-eeeeeeeeeeee | 1900 | P1 | 早已删掉的源 |\n\n"
                     "## Source-linked observations\n\nPending.\n", encoding="utf-8")
        process(ws, check=False)
        chk("**反对照**：0 源但表里还留着旧条目 → 被清成「0 份」",
            "本道分到 0 份" in q.read_text(encoding="utf-8"))

        # ★★★ 覆盖手写行时必须**报出来**——照搬 Blackstone #169 那次事故的形状：
        #   0 源道，模板的 `Pending.` 被换成了两句判断，于是「留着 Pending. 不覆盖」
        #   那道保护不认识它们，重出时静默抹掉。
        r = ws / "references" / "research" / "01-writings.md"
        r.write_text("# W\n\n" + HEAD + "\n\n"
                     "**本道的定位：印本年表，不是生平年表。**\n"
                     "它用的是扉页上逐字照录的印本年。\n\n"
                     "## Source-linked observations\n\nPending.\n", encoding="utf-8")
        _, _, _, dr = process(ws, check=True)
        chk("★ --check 就要报出会被覆盖的手写行",
            any("印本年表" in l for l in dr.get("01-writings.md", [])))
        _, _, _, dr2 = process(ws, check=False)
        chk("★ 真写盘时同样报出来",
            any("逐字照录" in l for l in dr2.get("01-writings.md", [])))
        chk("**反对照**：表格行与模板句不算手写行",
            all("|" not in l and "Pending." not in l
                for l in dr2.get("01-writings.md", [])))

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
    changed, nf, nr, dropped = process(ws, a.check)
    have, _tot = lanes_with_scope_section(ws)
    print("台账 %d 行；道文件 %d 份，其中**带 Scope 节的 %d 份**" % (nr, nf, have))
    if not changed:
        if not have:
            # ★ 没有那一节就无从比对 —— 不许说成「一致」。判定与 rc 都不变（见
            #   `lanes_with_scope_section` 的注释：本轮只让它说实话）。
            print("⚠ **%d 份研究稿里 0 份有 `%s` 节 ⇒ 本判据什么也没比，"
                  "「未检查」不是「一致」**" % (nf, HEAD))
            print("   （要真比对，先给研究稿加上这一节，再跑一次）")
            return 0
        if have < nf:
            print("Scope 节与台账一致（**只比了带该节的 %d/%d 份，"
                  "另 %d 份没有这一节、未比对**）" % (have, nf, nf - have))
            return 0
        print("Scope 节与台账一致，无需改动（%d/%d 份都比过）" % (have, nf))
        return 0
    print(("**过期 %d 份**：" if a.check else "已重出 %d 份：") % len(changed) + ", ".join(changed))
    if dropped:
        # ★★★ 不阻止覆盖（Scope 节本就该由机器拥有），**只是不让它静默**。
        #   起因：Blackstone #169 的 06-timeline.md 是 0 源道，我把模板的 `Pending.`
        #   换成了两句判断，于是「留着 Pending. 就不覆盖」那道保护不认识它们，
        #   重出时**静默抹掉**。判断性的话该搬到 Source-linked observations。
        verb = "会被覆盖掉" if a.check else "已被覆盖掉"
        print("\n★★ **下列手写行%s**（Scope 节由工具拥有，判断性的话请搬到 "
              "`Source-linked observations`）：" % verb)
        for name, lines in sorted(dropped.items()):
            print("  【%s】" % name)
            for l in lines:
                print("     %s" % l[:110])
    return 1 if a.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
