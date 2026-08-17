#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**按人物定制的同名判据**——因为「名 + 姓」对某些人物根本不够。

## 起因：Sorby #133 的父亲也叫 Henry Sorby

`check_authorship.ocr_byline_evidence` 比的是「名 + 姓」。实跑：

    ocr_byline_evidence("By Henry Sorby.", first="Henry", last="Sorby")
    → **判为目标本人**

而那是他父亲（c.1791–1846/47，Sheffield 刀具商）。
**父子二人「名 + 姓」两样全同，只差一个中名。**

这不是理论风险：
- University of Sheffield 的 Sorby Collection 明写着
  `one diary from his father covering 1845-1846`——**同一馆藏里「Sorby 的日记」指两个人**；
- **1841 年人口普查里目标本人也只登记为「Henry Sorby」**，没有 Clifton。

★ 上一次同形事故是 GE 总裁 Charles A. Coffin 被当成焊接发明人的署名放行
（见 [[test-the-guard-against-this-persons-namesake]]）。
**那一次是入库之后才发现的；Sorby 这次是抓源之前测出来的。**

## 它怎么用

工作区里放一份 `namesake-criteria.json`：

    {
      "subject": "Henry Clifton Sorby",
      "any_of_markers": ["Clifton", "F.R.S.", "F.G.S."],
      "excluded_names": ["T. C. Sorby", "Thomas Charles Sorby", "Robert Sorby"],
      "bare_name_before_year": {"year": 1850, "bare": "Henry Sorby",
                                "reason": "父亲卒于 1846/47；目标 1826 年生，1850 年才 24 岁"}
    }

判定顺序（**先排除，后确认**）：

1. 命中 `excluded_names` 里的任何一个 → **判为他人**，理由写明是哪一条；
2. 年份早于 `bare_name_before_year.year` 且只有 `bare` 那个署名 → **判为他人**（默认归属更早的同名者）；
3. 命中 `any_of_markers` 任一 → **判为目标本人**；
4. 都没命中 → **`unknown`——不是通过。**

★★ 第 4 条是本件的要害：**「说不准」必须是独立的一档**，
不许并进「是本人」也不许并进「是他人」。
本项目吃过太多次「空值被读成没问题」的亏（见 [[empty-default-swallows-unknown]]）。

## 只报不拦？——**报，且把 unknown 单列**

它不替 `check_authorship` 做判定，它给的是**逐份的归属结论与理由**，
供 `ingest` 之前人工过一遍。**没有 criteria 文件的人物一律跳过**（不是通过，是不适用）。
"""
import argparse
import json
import pathlib
import re
import sys


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def classify(text: str, crit: dict, year: int = None) -> dict:
    """→ {判定, 理由}。判定 ∈ {目标本人, 他人, unknown}。"""
    t = _norm(text)
    for bad in crit.get("excluded_names") or []:
        # 归一化空白后按「忽略空格」比，`T. C. Sorby` 与 `T.C. Sorby` 算同一个。
        # ★★★ v0.0.0.154：**必须带词首边界。** Sorby #133 抓源实测：
        #   MMJ v.XIII p.205 的页眉被 OCR 打成 `IT. C. Sorby`——**那是目标本人的页眉**，
        #   而它的字面里含 `T. C. Sorby`（建筑师）。不加边界，**他自己的文章会被判成他人**。
        #   这是「丢掉真材料」的方向，比误收更难发现——**少了的东西不会报错**。
        # ★ 第一版把空白**抹掉**再比，结果 `By T. C. Sorby` 变成 `byt.c.sorby`，
        #   词首边界被自己抹没了，真的建筑师反而漏判。**抹空白与查边界不能同时做。**
        #   改成：把名字编成「记号之间允许任意空白」的正则，边界在**原文**上查。
        toks = [re.escape(x) for x in re.split(r"\s+", bad.strip()) if x]
        if not toks:
            continue
        pat = r"(?<![A-Za-z])" + r"\s*".join(toks)
        if re.search(pat, t, re.I):
            return {"判定": "他人", "理由": f"命中排除名单：{bad}"}
    # ★★★ 2026-08-17：**缺 `year` 时这两条规则的方向相反** ——
    #   `before`：`year < int(bn.get("year", 0))` ⇒ `year < 0` 恒假，**失败关闭**（安全）；
    #   `after`： `year > int(ba.get("year", 0))` ⇒ `year > 0` 对任何正年份**恒真**，
    #            会把**所有**源提升为「目标本人」—— **失败打开**。
    #   实测：全库 8 份 `namesake-criteria.json` 里含该规则的 2 份都写了 `year`，
    #   **0 处够得到** ⇒ 这是潜伏的，不是现行缺陷；本次改动**移动的判定为 0**。
    #   ⇒ 两条都改成「缺 `year` 就不触发，并把这件事说出来」。
    #   [[a-pd-claim-with-no-year-satisfied-the-rule]]（凡「X ≤ 阈值」先问「X 存在吗」）
    def _rule_year(rule, which):
        """→ (阈值, 说明)。阈值为 None ⇒ **本条规则不触发**（不是「阈值 0」）。"""
        v = rule.get("year")
        if v in (None, ""):
            return None, ("★ `%s` 写了但**没有 `year`** —— 本条规则**不触发**"
                          "（不是「阈值 0」；缺阈值的比较在 `after` 方向上恒真）" % which)
        try:
            return int(v), ""
        except (TypeError, ValueError):
            return None, "★ `%s` 的 `year` 不是整数（%r）—— 本条规则**不触发**" % (which, v)

    bn = crit.get("bare_name_before_year") or {}
    _bn_year, _bn_note = _rule_year(bn, "bare_name_before_year") if bn else (None, "")
    if bn and _bn_year is not None and year is not None and year < _bn_year:
        bare = _norm(bn.get("bare") or "")
        if bare and re.sub(r"\s+", "", bare.lower()) in re.sub(r"\s+", "", t.lower()):
            if not any(m.lower() in t.lower() for m in (crit.get("any_of_markers") or [])):
                return {"判定": "他人",
                        "理由": f"{year} < {_bn_year} 且只有「{bare}」这个署名"
                                f"——{bn.get('reason', '默认归属更早的同名者')}"}
    # ★★★ v0.0.0.154：`bare_name_before_year` 的**对称一半**。
    #   原本只有「早于某年的裸名 → 归更早的同名者」，而反方向没有规则：
    #   更早那位一旦去世，之后印行的裸名印本**不可能是他**。
    #   Holmes #170 实测：父 1809–1894，而 1920 年的《Collected Legal Papers》
    #   题名页只署裸名 `By Oliver Wendell Holmes`——没有这条就永远是 `unknown`。
    #   ★ 用的是**卒年**，不是生年，也不是「目标出道年」：卒年之后是硬的。
    #   ★ 它只把 `unknown` 提升为「目标本人」，**不会把任何东西判成他人**——
    #     排除名单在它之前跑，误收的风险面比 before_year 那条小。
    ba = crit.get("bare_name_after_year") or {}
    _ba_year, _ba_note = _rule_year(ba, "bare_name_after_year") if ba else (None, "")
    if ba and _ba_year is not None and year is not None and year > _ba_year:
        bare2 = _norm(ba.get("bare") or "")
        if bare2 and re.sub(r"\s+", "", bare2.lower()) in re.sub(r"\s+", "", t.lower()):
            return {"判定": "目标本人",
                    "理由": f"{year} > {_ba_year} 且署「{bare2}」"
                            f"——{ba.get('reason', '更早的同名者已不在世')}"}
    # ★★★ v0.0.0.154：区分符**必须贴着姓氏**，不许全篇找。
    #   Sorby #133 抓源实测：A8 是他自己的文，正文写着
    #   `Professor Clifton's laboratory at Oxford`——那是 R. B. Clifton，牛津物理学家。
    #   全篇找 `Clifton` 会把**任何提到那位物理学家的文章**判成目标本人。
    #   本次那一篇碰巧确实是他的，**结论对而理由错**——这种最难发现。
    surname = str(crit.get("surname") or "").strip()
    if not surname:
        subj = str(crit.get("subject") or "").split()
        surname = subj[-1] if subj else ""
    near = crit.get("marker_window", 40)
    hit = []
    for mk in (crit.get("any_of_markers") or []):
        for mm in re.finditer(re.escape(mk.lower()), t.lower()):
            if not surname:
                hit.append(mk); break
            lo, hi = max(0, mm.start() - near), mm.end() + near
            if surname.lower() in t[lo:hi].lower():
                hit.append(mk); break
    if hit:
        return {"判定": "目标本人",
                "理由": f"命中区分符（贴着姓氏 {near} 字以内）：{sorted(set(hit))}"}
    return {"判定": "unknown",
            "理由": ("既没命中排除名单，也没命中任何区分符——"
                     "**这不是通过，是没核**。人工定夺或补一条区分符。")}


def run(ws: pathlib.Path, crit_file: pathlib.Path = None) -> int:
    """`ws` 是**放台账的工作区**；`crit_file` 是判据文件（可以在更上层）。

    ★ 这两个常常不在同一层：判据按**人物**放在 `wip-<人>/`，
      而台账在 `wip-<人>/workspaces/<slug>/<slug>/evidence/`。
      先前把两者绑在一起找，结果判据找到了、台账却按判据那一层去找，
      报「还没有 source-ledger.jsonl」——**看着像没抓源，其实是路径错了**。
    """
    crit_f = crit_file if crit_file is not None else (ws / "namesake-criteria.json")
    if not crit_f.is_file():
        print(f"  {ws.name}：没有 namesake-criteria.json——**不适用**（不是通过）")
        return 0
    crit = json.loads(crit_f.read_text(encoding="utf-8"))
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        print(f"  {ws.name}：还没有 source-ledger.jsonl，**只做自检不判源**")
        return 0
    # ★★★ v0.0.0.154：`adjudicated` —— **把「人工定夺」做成机器看得见的动作**。
    #   判据原来只会说「人工定夺或补一条区分符」，而定夺的结果没有落脚点：
    #   写在散文里没人读，写进 `excluded_names` 是反的，改区分符又会放松判据。
    #   现在 criteria 可以写 `{"adjudicated": {"src-xxx": "理由"}}`，
    #   ★ 它**单独计数**，不并进「目标本人」——[[empty-default-swallows-unknown]]：
    #     人工定夺过的和判据自动认定的，读的人必须能分开看。
    #   ★ 理由为空一律不认（空字符串不是定夺）。
    adjudged = {k: v for k, v in (crit.get("adjudicated") or {}).items()
                if str(v).strip()}
    tally = {"目标本人": 0, "他人": 0, "unknown": 0, "人工定夺": 0}
    rows = []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:                                       # noqa: BLE001
            continue
        # ★★★ v0.0.0.154：**加上 `attribution`。**
        #   台账里题名页／版权页的**逐字照录**放在 `attribution`，而这道门原本不读它——
        #   于是 Holmes #170 的 U.S. Reports 各卷全判 `unknown`：
        #   判例正文从不写全名（写的是 `Mr. Justice Holmes`），而 `title` 只有卷次范围，
        #   **唯一带署名证据的那个字段偏偏不在 blob 里**。
        #   与 [[gate-green-but-pointed-at-wrong-artifact]] 同类：判据读的键不是产者写的键。
        blob = " ".join(str(r.get(k, "")) for k in
                        ("original_name", "locator", "title", "author", "byline",
                         "notes", "attribution"))
        y = None
        m = re.search(r"\b(1[6-9]\d{2}|20[0-2]\d)\b", blob)
        if m:
            y = int(m.group(1))
        v = classify(blob, crit, y)
        sid = r.get("source_id") or r.get("id") or "?"
        if v["判定"] == "unknown" and sid in adjudged:
            v = {"判定": "人工定夺", "理由": "人工定夺：%s" % adjudged[sid]}
        tally[v["判定"]] += 1
        if v["判定"] != "目标本人":
            rows.append((r.get("source_id") or r.get("id") or "?", v))
    print(f"  {ws.name}：目标本人 {tally['目标本人']}　他人 {tally['他人']}　"
          f"**unknown {tally['unknown']}**"
          + (f"　人工定夺 {tally['人工定夺']}" if tally["人工定夺"] else ""))
    for sid, v in rows[:12]:
        print(f"    · {sid}  [{v['判定']}] {v['理由'][:70]}")
    return tally["unknown"]


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    CRIT = {
        "subject": "Henry Clifton Sorby",
        "any_of_markers": ["Clifton", "F.R.S.", "F.G.S."],
        "excluded_names": ["T. C. Sorby", "Thomas Charles Sorby", "Robert Sorby"],
        "bare_name_before_year": {"year": 1850, "bare": "Henry Sorby",
                                  "reason": "父亲卒于 1846/47；目标 1826 年生"},
    }

    print("── ★★★ 真例：父亲的署名，现有护栏挡不住，本件要挡住 ──")
    v = classify("By Henry Sorby.", CRIT, 1845)
    chk(f"1845 年只署「Henry Sorby」→ {v['判定']}：{v['理由'][:44]}", v["判定"] == "他人")

    print("── 真例：目标本人（带中名）──")
    chk("Clifton 命中 → 目标本人",
        classify("By Henry Clifton Sorby, F.R.S.", CRIT, 1863)["判定"] == "目标本人")

    print("── 真例：目标本人（无中名但有 F.R.S.）──")
    chk("F.R.S. 命中 → 目标本人",
        classify("By H. C. Sorby, F.R.S.", CRIT, 1863)["判定"] == "目标本人")

    print("── 真例：建筑师与锉刀商 ──")
    chk("T. C. Sorby → 他人", classify("By T. C. Sorby, Architect.", CRIT)["判定"] == "他人")
    chk("Robert Sorby → 他人", classify("Robert Sorby, Sheffield.", CRIT)["判定"] == "他人")

    print("\n── ★★★ 反向对照①：**说不准必须单列，不许并进任何一边** ──")
    v = classify("By Henry Sorby.", CRIT, 1870)
    chk(f"1870 年只署「Henry Sorby」→ {v['判定']}（不是「目标本人」）", v["判定"] == "unknown")
    chk("也不是「他人」——1870 年父亲已故，不能默认归他", v["判定"] != "他人")

    print("── ★★ 反向对照②：排除名单**先于**区分符判——同一行两者都有时按排除处理 ──")
    v = classify("By T. C. Sorby, F.R.S.（同行混排）", CRIT, 1880)
    chk(f"→ {v['判定']}", v["判定"] == "他人")

    print("── ★★ 反向对照③：**没有 criteria 文件不算通过**，算不适用 ──")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        n = run(pathlib.Path(tmp))
        chk(f"返回 {n}，且打印「不适用（不是通过）」", n == 0)

    print("── ★ 反向对照④：年份缺失时**不许**用年份规则（不能假设它早于分界）──")
    v = classify("By Henry Sorby.", CRIT, None)
    chk(f"无年份 → {v['判定']}（不是「他人」）", v["判定"] == "unknown")

    # ── bare_name_after_year：对称的那一半 ──
    crit_a = {"subject": "Oliver Wendell Holmes Jr.", "surname": "Holmes",
              "any_of_markers": ["Justice"], "marker_window": 60,
              "excluded_names": ["Oliver Wendell Holmes Sr."],
              "bare_name_after_year": {"year": 1894, "bare": "Oliver Wendell Holmes",
                                       "reason": "父卒于 1894"}}
    v = classify("Collected Legal Papers. By Oliver Wendell Holmes. 1920", crit_a, 1920)
    chk(f"卒年之后的裸名 → {v['判定']}（应为目标本人）", v["判定"] == "目标本人")
    # ★ 反对照①：**卒年之前**的同一署名不许被这条提升
    v = classify("The Autocrat. By Oliver Wendell Holmes. 1858", crit_a, 1858)
    chk(f"卒年之前的裸名 → {v['判定']}（不许判成目标本人）", v["判定"] != "目标本人")
    # ★★ 反对照②：**排除名单优先**——命中排除名单的，哪怕年份在卒年之后也判他人
    v = classify("By Oliver Wendell Holmes Sr. 1920", crit_a, 1920)
    chk(f"卒年之后但命中排除名单 → {v['判定']}（应为他人）", v["判定"] == "他人")
    # ★★★ 反对照③：**没有这个字段时不许凭空生效**（缺省不许被读成「通过」）
    v = classify("By Oliver Wendell Holmes. 1920",
                 {k: x for k, x in crit_a.items() if k != "bare_name_after_year"}, 1920)
    chk(f"未配置该规则 → {v['判定']}（应为 unknown）", v["判定"] == "unknown")

    print("\n══ ★★★ 抓源实测打回来的两个真 bug（v0.0.0.154 修）══")
    print("── ⑥ 排除名单必须带词首边界——否则**他自己的页眉会把他排掉** ──")
    #   MMJ v.XIII p.205 的页眉被 OCR 打成 `IT. C. Sorby`，那是**目标本人**的页眉，
    #   字面里却含建筑师的 `T. C. Sorby`。
    #   ★ 这是「丢掉真材料」的方向——**少了的东西不会报错**，比误收更难发现。
    v = classify("running head: IT. C. Sorby | MMJ v.XIII p.205", CRIT, 1876)
    chk(f"`IT. C. Sorby` → {v['判定']}（**不许是「他人」**）", v["判定"] != "他人")
    chk("而真的 `T. C. Sorby` 仍要排掉",
        classify("By T. C. Sorby, Architect.", CRIT, 1866)["判定"] == "他人")

    print("── ⑦ 区分符必须贴着姓氏——否则**另一个 Clifton 会把别人认成他** ──")
    #   A8 是 Sorby 自己的文，正文写着 `Professor Clifton's laboratory at Oxford`,
    #   那是 R. B. Clifton，牛津物理学家。**那一篇碰巧确实是他的——结论对而理由错**，
    #   这种最难发现：换一篇不是他的、同样提到那位物理学家的文，就会被认成他。
    v = classify("Professor Clifton's laboratory at Oxford（正文，作者字段为空）", CRIT, 1870)
    chk(f"孤立的 `Clifton` → {v['判定']}（**不许是「目标本人」**）", v["判定"] != "目标本人")
    chk("而贴着姓氏的 `Clifton` 仍算区分符",
        classify("By Henry Clifton Sorby, F.R.S.", CRIT, 1863)["判定"] == "目标本人")

    print("── ★ 反向对照⑤：忽略空格差异，`T.C. Sorby` 与 `T. C. Sorby` 同判 ──")
    chk("→ 他人", classify("By T.C. Sorby", CRIT)["判定"] == "他人")

    # ── ★★★ 2026-08-17：**缺 `year` 时两条规则的方向相反** ──
    #   before：`year < int(get("year", 0))` ⇒ 恒假，失败关闭（安全）
    #   after： `year > int(get("year", 0))` ⇒ 对任何正年份**恒真**，失败打开
    #   实测全库 8 份配置里含该规则的 2 份都写了 year ⇒ **0 处够得到**，是潜伏的。
    print("\n── 缺 `year` 时必须**不触发**（失败关闭）──")
    _C_after_noyear = {"any_of_markers": [], "exclude_names": [],
                       "bare_name_after_year": {"bare": "Oliver Wendell Holmes"}}
    _v = classify("By Oliver Wendell Holmes", _C_after_noyear, year=1920)
    chk("★★★ `bare_name_after_year` 缺 year → **不许**判成「目标本人」（实得 %s）"
        % _v["判定"], _v["判定"] != "目标本人")
    _C_after_ok = {"any_of_markers": [], "exclude_names": [],
                   "bare_name_after_year": {"bare": "Oliver Wendell Holmes", "year": 1894}}
    _v2 = classify("By Oliver Wendell Holmes", _C_after_ok, year=1920)
    chk("★★★ 反对照：**写了 year 就照旧判「目标本人」**（1920 > 1894，实得 %s）"
        % _v2["判定"], _v2["判定"] == "目标本人")
    _C_after_bad = {"any_of_markers": [], "exclude_names": [],
                    "bare_name_after_year": {"bare": "Oliver Wendell Holmes", "year": "不是数字"}}
    _v3 = classify("By Oliver Wendell Holmes", _C_after_bad, year=1920)
    chk("★★ year 不是整数 → 也不触发（不许抛，也不许判「目标本人」）",
        _v3["判定"] != "目标本人")
    _C_before_noyear = {"any_of_markers": [], "exclude_names": [],
                        "bare_name_before_year": {"bare": "Henry Sorby"}}
    _v4 = classify("By Henry Sorby", _C_before_noyear, year=1845)
    chk("★★ `bare_name_before_year` 缺 year → 照旧不触发（它本来就失败关闭）",
        _v4["判定"] != "他人")

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace or not a.workspace.is_dir():
        print("✗ 需要一个工作区目录——**未核，不是通过**")
        return 3
    n = run(a.workspace)
    print(f"\n{'⚠' if n else '✓'} unknown {n} 条"
          + ("　**「说不准」不是通过**——入库前逐条定夺或补一条区分符" if n else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
