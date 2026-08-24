#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**合著的东西，被用第一人称独揽了吗。**

## 为什么有这道判据

席 E 在 Fleming #111 第 3 轮 q-30 抓到：

> A 有 MRC 报告 57 与 1940 年文，但……**按 q-15 该报告系与 Douglas、Colebrook 合著，
> 此处以第一人称独揽**，正违反 q-32 自定的规矩。

要命的地方是**产物自己在别处把规矩说得很好**——
q-32 讲「一项发现拆成几段，逐段问这段是谁做的」，q-15 老老实实写了合著者，
**唯独在最需要显得有权威的那一句上独揽了。**

这是第五次把席位批评落成判据。前四次的形状相同：
**评委在一处看出症状，判据能把范围数出来。**

## 判据

账本里每条源都有 `attribution`。若其中出现合著／集体署名的标记
（`合著` / `CO-AUTHORED` / `COMMISSION-COLLECTIVE` / `第一作者是` / `集体署名` …），
则任何**引用了这条源**、又用**第一人称独揽语**（`我做的` / `我写的` /
`我的报告` / `我发表了` / `我证明了` …）的断言或答案，报出。

## ★ 它不禁止第一人称

**「我参与了」「我那一部分是」「我与 X 合著」全都放行。**
禁的只是**独揽**：把集体成果说成「我的」。
反向对照 ③④⑤ 守这一条——判据若把正常的第一人称也报出来，
作者会把所有第一人称都改掉，**而第一人称正是这个产物的形态。**

## 它判不了什么

- **不判「哪一部分确实是他的」**。合著里他可能确实主导了那一段；
  判据只问「有没有在字面上把合著说成独作」。
- **只看引用了该源的单元**。没引源的第一人称句子不在射程内
  （那是 `check_unsourced_names` 与人工的活）。
"""
import argparse
import json
import pathlib
import re
import sys

# 账本 attribution 里表示「不是他一个人的」的标记
SHARED = re.compile(
    r"合著|合撰|共同署名|集体署名|联名"
    r"|CO-AUTHORED|COMMISSION-COLLECTIVE|THIRD-PARTY"
    r"|第一作者(?:是|为)|第二作者|署名顺序"
    r"|委员会(?:的)?(?:报告|公文|文件)")

# 第一人称叙述一份合著成果——注意不含「我参与」「我那一部分」
#
# ★ 判准比「明说独占」宽。Fleming #111 q-30 的实际形状是：
#     「一战期间**我研究**伤口感染，**成果是** MRC 特别报告 57 号（1920）」
#   ——它没有说「那是我一个人的」，它是**只字不提合著者**。
#   第一版只找 `我做的／我的报告` 这类显式独揽语，在它的动因用例上报绿。
#   **缺陷是遗漏，不是明说**，判准必须跟着改。
SOLE = re.compile(
    r"我(?:亲手)?(?:研究|写|做|完成|发表|提出|证明|设计|建立|主持|负责|发现|调查)"
    r"|我的(?:那)?(?:篇|份|本)?(?:论文|报告|文章|著作|研究|发现|方法|成果|工作)"
    r"|(?:这|那)(?:篇|份|本)是我(?:写|做|发表)的"
    r"|由我(?:一人|独自|单独)"
    r"|成果是")

# 明确说了「不是我一个人」的措辞——同段出现即视为已划界，不报。
# **修法是划界，不是删第一人称**（反向对照 ⑧）。
#
# ★★ 还必须认**否定式的划界**。Nightingale #112 实测：
#   答案写的是「**所以我说「那份文件里的表」，不说「我的报告」**」——
#   `SOLE` 命中了引号里的「我的报告」，而那整句正是在**拒绝**这么说。
#   判据若报它，作者为了变绿会**把那句拒绝删掉**——
#   **判据把产物推向了它本该防的方向**，与 v0.0.0.63「弃权不是缺陷」同一条道理。
#   （同一个坑我在断言生成器的护栏上先踩过一次，当时只修了生成器没修这里。）
DISCLAIMED = re.compile(
    r"不说(?:成|是)?「?我的|不(?:把它)?称作|不算我的|不是我(?:的|写|做)|并非我"
    r"|扉页(?:上)?(?:没有|无)(?:我的)?(?:名字|署名)|全文(?:里)?(?:我的姓|无我的姓)"
    r"|匿名(?:刊行)?|第三人称称我|我说不清|我不替它下断语"
    r"|合著|合撰"
    r"|与[^，。；]{1,24}(?:合|共同|一起|同)(?:著|写|做|完成|署名)"
    r"|我(?:只|仅)(?:是|做了|负责)"
    r"|我负责(?:的)?(?:是)?[^，。；]{0,12}部分"
    r"|我那一部分"
    r"|我参与"
    r"|不是我一个人"
    r"|第一作者(?:是|为)|第二作者"
    r"|集体署名|委员会(?:的)?文件")

SRCID = re.compile(r"src-[a-f0-9]{12}")

# ★★ 「合著」形容的是**整卷**，不是这一篇——这类一律不算合著源。
#
#   Virchow #109 实测：`src-51df3ba90ac1` 的 attribution 写着
#   「**从卷内按署名切出的单篇**……他本人的文章按正文署名『Von R. Virchow』定位，
#   切至下一位作者的署名为止」——**那是他独著的一篇**，
#   「卷内为多人合著」说的是母卷。
#   第一版按整段 attribution 匹配「合著」二字，把三条独著文章全报成独揽。
#   **精确率 1/5。** 这种噪声正是 v0.0.0.62 刚修掉的那一类：
#   假阳性堆到一定密度，作者就学会跳过这道判据的输出。
VOLUME_LEVEL = re.compile(
    r"按署名切出的单篇|卷内按署名|signed article"
    r"|卷次本身|母卷|切至下一位作者")


def shared_sources(ledger: pathlib.Path) -> dict:
    """→ {source_id: 触发的标记}。只收 attribution 里显示「不是他一个人」的。"""
    out = {}
    for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        attrib = r.get("attribution") or ""
        if VOLUME_LEVEL.search(attrib):
            continue                      # 「合著」形容母卷，这一篇是独著
        m = SHARED.search(attrib)
        if m and r.get("source_id"):
            out[r["source_id"]] = m.group(0)
    return out


# 篇名里没有区分力的词，用它们匹配会把所有答案都算成引了这条源
_STOP = {"the", "of", "on", "and", "a", "an", "in", "to", "for", "with",
         "some", "its", "their", "from", "by", "at", "report", "notes", "studies"}
MIN_KEY = 6          # 关键词至少这么长，短词噪声太大


def title_index(ledger: pathlib.Path, shared: dict) -> dict:
    """→ {source_id: [可用于在答案里认出它的关键词]}。

    ★ **答案层不带 `source_ids`，只带篇名。**
      按 `source_ids` 找，答案层一条也匹配不到——判据接上了却什么也没扫。
      所以对答案层改按**篇名关键词**认：取 `title` 与 `locator` 里
      长度 ≥6、且不在停用词表里的词。
    """
    idx = {}
    for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            continue
        sid = r.get("source_id")
        if sid not in shared:
            continue
        blob = f"{r.get('title') or ''} {r.get('locator') or ''}"
        keys = [w for w in re.findall(r"[A-Za-z][A-Za-z'-]+", blob)
                if len(w) >= MIN_KEY and w.lower() not in _STOP]
        # ★★ **答案是用中文写的。**
        #   Fleming q-30 写的是「MRC 特别报告 57 号（1920）」，
        #   而索引里全是 `Studies` / `Infections` / `Council` 这些英文词——
        #   一个都对不上，判据在它的动因用例上再次报绿。
        #   补两类跨语言仍然出现的键：**缩写**（MRC、BMJ）与**编号**（57、1920）。
        #   仍要求两个键同时命中，单个「57」不算。
        keys += [w for w in re.findall(r"\b[A-Z]{3,6}\b", blob)]
        keys += [w for w in re.findall(r"\b\d{2,4}\b", blob)]
        if keys:
            idx[sid] = sorted(set(keys), key=len, reverse=True)[:10]
    return idx


def cited_by_title(text: str, idx: dict) -> set:
    """答案段落里提到了哪些源的篇名关键词。**要两个关键词同时出现**，
    单个词太容易撞（`Infections` 在多篇里都有）。"""
    low = text.lower()
    out = set()
    for sid, keys in idx.items():
        if sum(1 for k in keys if k.lower() in low) >= 2:
            out.add(sid)
    return out


def paragraphs(text: str):
    for p in re.split(r"\n\s*\n", text or ""):
        if p.strip():
            yield p


def scan(unit_id: str, text: str, cited: set, shared: dict, acc):
    """`cited` 是该单元引用的 source_id 集合。"""
    hit = cited & set(shared)
    if not hit:
        return
    for para in paragraphs(text):
        m = SOLE.search(para)
        if not m:
            continue
        acc["total"] += 1
        if DISCLAIMED.search(para):
            acc["ok"] += 1                     # 同段已划界，放行
            continue
        acc["bad"].append((unit_id, sorted(hit)[0], shared[sorted(hit)[0]],
                           m.group(0), para.strip()[:110]))


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    SH = {"src-000000000001": "合著"}

    def run(text, cited=("src-000000000001",)):
        acc = {"total": 0, "ok": 0, "bad": []}
        scan("x", text, set(cited), SH, acc)
        return acc

    print("── 正向：Fleming #111 q-30 的真实形状 ──")
    a = run("我反对往伤口里灌防腐剂，**因为我量过**——"
            "见《Studies in Wound Infections》，MRC 特别报告 57，1920。"
            "那是我做的研究。")
    chk("引了合著源 + 「我做的研究」→ 报出", len(a["bad"]) == 1)

    print("── ★★ 正向 ②：**Fleming q-30 的逐字原文**（判据的动因用例）──")
    # 它没有说「那是我一个人的」，它是**只字不提合著者**。
    # 第一版只找显式独揽语，在这条上报绿——**动因用例必须能被抓到**。
    a2 = run("一战期间我研究伤口感染，成果是 **MRC 特别报告 57 号（1920）**："
             "深部伤口形状复杂，防腐剂到不了细菌那里。")
    chk("「我研究…成果是 MRC 报告 57」且不提合著者 → 报出", len(a2["bad"]) == 1)

    print("── ★ 反向对照 ①：同段划了界的不许报 ──")
    b = run("《Studies in Wound Infections》是我与 Douglas、Colebrook 合著的，"
            "我那一部分是伤口渗出液那几组。")
    chk("同段写了「合著」「我那一部分」→ 放行", not b["bad"])

    print("── ★ 反向对照 ②：**没引这条源就不在射程内** ──")
    c = run("那是我做的研究。", cited=("src-ffffffffffff",))
    chk("引的是别的源 → 不计入、不报", c["total"] == 0 and not c["bad"])

    print("── ★★ 反向对照 ③：**判据不禁止第一人称** ──")
    # 若把正常第一人称也报出来，作者会把所有第一人称改掉，
    # **而第一人称正是这个产物的形态。**
    for s in ("我参与了那项调查，报告是委员会署名的。",
              "我只负责其中的统计部分。",
              "不是我一个人做的。"):
        d = run(s)
        chk(f"「{s[:14]}…」→ 不报", not d["bad"])

    print("── 反向对照 ④：账本没标合著的源，一律不报 ──")
    acc = {"total": 0, "ok": 0, "bad": []}
    scan("y", "那是我做的研究。", {"src-000000000002"}, SH, acc)
    chk("源不在 shared 表里 → 不计入", acc["total"] == 0 and not acc["bad"])

    print("── 反向对照 ⑤：独揽语在另一段、划界在这一段——**按段判，不许跨段抵消** ──")
    e = run("《Studies in Wound Infections》是我与 Douglas 合著的。\n\n那是我做的研究。")
    chk("划界在上一段 → 下一段仍报出", len(e["bad"]) == 1)

    print("── ★★ 反向对照 ⑥：**答案层按篇名认，且要两个关键词同时出现** ──")
    # 第一版只吃 --claims，而席 E 抓到的那处在答案层：判据接上了、自测全过、
    # 实跑「✓」，唯独没扫那个出问题的层。这是射程写错，我自己记过还是犯了。
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p2 = pathlib.Path(d) / "l.jsonl"
        p2.write_text(json.dumps({
            "source_id": "src-000000000001",
            "attribution": "与 Douglas、Colebrook 合著",
            "title": "Studies in Wound Infections",
            "locator": "MRC Special Report Series 57"}, ensure_ascii=False) + "\n",
            encoding="utf-8")
        idx = title_index(p2, SH)
        chk("篇名关键词抽得出（去掉 the/of/report/studies 这类）",
            bool(idx.get("src-000000000001")))
        chk("两个关键词同时出现 → 认作引了这条源",
            cited_by_title("见《Studies in Wound Infections》，MRC Special Report 57。", idx)
            == {"src-000000000001"})
        chk("**只出现一个关键词 → 不认**（`Infections` 在多篇里都有）",
            not cited_by_title("那几年我做的是 wound infections 的研究。", idx))
        # ★★ 答案是中文写的：「MRC 特别报告 57 号」里一个英文篇名词都没有
        chk("**中文答案里的缩写 + 编号也要认得出**（MRC + 57）",
            cited_by_title("成果是 **MRC 特别报告 57 号（1920）**。", idx)
            == {"src-000000000001"})
        chk("光有一个编号不认（`57` 太常见）",
            not cited_by_title("我做过 57 次实验。", idx))

    print("── 反向对照 ⑦：`shared_sources` 只收 attribution 里真有标记的 ──")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "l.jsonl"
        p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
            {"source_id": "src-aaaaaaaaaaaa", "attribution": "其生前发表之论文，署 X，1920。"},
            {"source_id": "src-bbbbbbbbbbbb", "attribution": "与 Douglas 合著，第一作者是 Douglas。"},
            {"source_id": "src-cccccccccccc", "attribution": "COMMISSION-COLLECTIVE 委员会的报告。"},
        ]) + "\n", encoding="utf-8")
        got = shared_sources(p)
        chk("独著的不收、合著与委员会的要收",
            "src-aaaaaaaaaaaa" not in got and len(got) == 2)

    print("── ★★ 反向对照 ⑨：**「合著」形容整卷时，卷内独著的单篇不许报** ──")
    # Virchow #109 实测：三条独著文章被报成独揽，只因母卷 attribution 里有「合著」二字。
    import tempfile as _tf
    with _tf.TemporaryDirectory() as d:
        p3 = pathlib.Path(d) / "l.jsonl"
        p3.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in [
            {"source_id": "src-vvvvvvvvvvvv",
             "attribution": "**从《Archiv》卷内按署名切出的单篇**。卷内为多人合著，"
                            "他本人的文章按正文署名定位，切至下一位作者的署名为止。"},
            {"source_id": "src-wwwwwwwwwwww", "attribution": "与 Ogilvie 合著，1951。"},
        ]) + "\n", encoding="utf-8")
        got = shared_sources(p3)
        chk("卷内切出的单篇 → **不算合著源**", "src-vvvvvvvvvvvv" not in got)
        chk("真合著的那条仍要收", "src-wwwwwwwwwwww" in got)

    print("── ★★ 反向对照 ⑩：**否定式的划界也要认**（Nightingale #112 实测）──")
    # 「所以我说「那份文件里的表」，**不说「我的报告」**」——SOLE 命中引号里的「我的报告」，
    # 而整句正是在**拒绝**这么说。判据若报它，作者会把那句拒绝删掉。
    for s in ("那些表在那份文件里。**那份扉页上没有我的名字。** "
              "所以我说「那份文件里的表」，不说「我的报告」。",
              "那本是匿名刊行的，全文无我的姓——我不替它下断语。",
              "扉页上没有署名，正文还第三人称称我。那不是我写的。"):
        z = run(s)
        chk(f"「{s[:16]}…」→ 不报", not z["bad"])

    print("── 反向对照 ⑧：**补一句合著者就该放行**——修法是划界不是删第一人称 ──")
    a3 = run("一战期间我与 Douglas、Colebrook 合著了 MRC 特别报告 57 号（1920）："
             "深部伤口形状复杂，防腐剂到不了细菌那里。")
    chk("同一句补上合著者 → 不报", not a3["bad"])

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=pathlib.Path, help="source-ledger.jsonl")
    ap.add_argument("--claims", type=pathlib.Path, help="claims.jsonl")
    # ★ 第一版只吃 `--claims`——**而席 E 抓到的那一处在答案层**。
    #   判据接上了、自测全过、实跑也「✓」，唯独**没扫那个出问题的层**。
    #   这是我自己记过的第三种失效形态（射程写错），当场又犯一次。
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[],
                    help="候选答案 JSON（id→文本）或盲判载荷（[{case_id,A,B}]）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.ledger and (a.claims or a.answers)):
        ap.error("要么 --self-test，要么给 --ledger 加上 --claims／--answers 之一")

    if not a.ledger.is_file():
        print(f"✗ **{a.ledger} 不在——本次未检查（不是通过）**")
        return 3
    shared = shared_sources(a.ledger)
    if not shared:
        print("  ⚠ **账本里一条合著／集体署名的源都没有**——"
              "本判据这一轮什么也没查到，不构成通过")
        return 0

    acc = {"total": 0, "ok": 0, "bad": []}
    idx = title_index(a.ledger, shared)
    if a.claims and a.claims.is_file():
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            cited = (set(r.get("source_ids") or [])
                     | set(SRCID.findall(json.dumps(r, ensure_ascii=False))))
            # ★★ **引了这条源 ≠ 这一段在讲这条源。**
            #   Fleming #111 实测：一条断言同时引了 1951 年那篇合著文与别的源，
            #   而被标出的句子讲的是 **1924 年**另一篇——判据把账算到了错的源头上。
            #   所以断言层也要过篇名匹配这一关：**段落里得真的提到那部作品。**
            text = r.get("claim", "")
            for para in paragraphs(text):
                scan(f"断言/{r.get('claim_id', '?')}", para,
                     cited & cited_by_title(para, idx), shared, acc)

    for path in a.answers:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        units = ([(f'{r.get("case_id", "?")}/{s}', r[s])
                  for r in data for s in ("A", "B") if s in r]
                 if isinstance(data, list) else list(data.items()))
        for uid, text in units:
            for para in paragraphs(text):
                scan(f"答案/{uid}", para, cited_by_title(para, idx), shared, acc)

    print(f"账本里合著／集体署名的源 {len(shared)} 条；"
          f"引用了它们又用第一人称的段落 {acc['total']} 处，"
          f"其中已划界 {acc['ok']} 处，**独揽 {len(acc['bad'])} 处**")
    if acc["bad"]:
        print("\n✗ **把合著／集体署名的成果用第一人称独揽了**——"
              "「我主导了那件事」与「这份文件是我写的」是两句话：")
        for uid, sid, mark, kw, snip in acc["bad"]:
            print(f"    {uid}　@{sid}（账本记「{mark}」）　「{kw}」\n        {snip}")
        print("\n  **修法是划界，不是删第一人称**——"
              "写「我与 X 合著」「我那一部分是……」即可，本判据不报这类。")
        return 1
    print("  ✓ 引用合著源的地方都划了界")
    return 0


if __name__ == "__main__":
    sys.exit(main())
