#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`VERIFICATION.md` 里那些**可数的数**，和仓库的实况对不对得上。

## 为什么有这件——**这份文件自己预言过它会再漂，然后它真的又漂了**

`VERIFICATION.md` 的警示块里写着（v0.0.0.76 那次）：

> 五行数字停在两到四个版本以前——检查器元普查 **30 件**（真值 43）、
> 真实夹具 **5/19**、checksum **305 files**（真值 341）、Python 脚本 **66**（真值 84）。
> 五行全部朝**偏小**的方向错，也就是**每一行都在低报本项目自己的规模**。
> **没有任何门会说话**：`check_contract_drift` 只核首行标题里的版本号，
> **表格正文不在任何判据的射程里**。

2026-08-04 复核：**又漂了，方向一样还是偏小**——
判据 **51**（真值 53）、Python 脚本 **66**（真值 81）、checksum **341 files**（真值 368）。

**一份文件预言了自己的失效方式，两个版本之后原样复发。**
预言不是判据；**只有判据是判据。**

## 判据形状

对每一类**能从仓库直接数出来的**量，各配一条正则去 `VERIFICATION.md` 里找那句话，
数出来，比一比。**对不上就报，不改文件**——改哪个数是人的事
（有可能是文件陈旧，也有可能是仓库真的少了东西）。

## ★ 「怎么数」本身要按**定义属性**，不按目录位置

第一版我数身份族用 `find -maxdepth 1 -type d`，得到 **16**——
因为它把 `agents/`／`references/`／`schemas/`／`scripts/` 也算进去了。
**真值是 12，判据是「目录里有没有 `_category.json`」。**
这与本仓已记过的几次同形（台账按列号猜、判分按文件名数、处置按单一文件名数）是同一个病。

## 射程边界

- **只管能机械数出来的那几类。** 「真实夹具 5/19」这种要读判据内部结构的，本件不碰。
- **只报不改。** 数对不上时不知道该改哪边，这是人的判断。
"""
import argparse
import json
import pathlib
import re
import sys


def real_counts(root: pathlib.Path) -> dict:
    """★ 每一项都按**定义属性**数，不按目录位置。"""
    root = root.resolve()          # ★ 传 `.` 进来时 root.parent 会塌成上一级，先解析
    group = root.parent / "persona-distiller-group"
    fams = sorted(p for p in group.glob("*/_category.json")) if group.is_dir() else []
    people = [d for f in fams for d in f.parent.iterdir()
              if d.is_dir() and not d.name.startswith("_")]
    cks = root / "checksums.sha256"
    return {
        "判据件数": len(list((root / "scripts").glob("check_*.py"))),
        "Python脚本数": len(list((root / "scripts").glob("*.py"))),
        "checksum行数": len([l for l in cks.read_text(encoding="utf-8").splitlines() if l.strip()])
                        if cks.is_file() else None,
        "身份族数": len(fams),
        "名册人数": len(people),
    }


# 每条：(键, 在 VERIFICATION.md 里找它的正则)
# ★ `\*{0,2}` 必须**前后都写**——文中的写法是 `判据 **53** 件`，
#   第一版只允许数字**前**有星号，于是正向对照三条全红。**夹具照着真文本配。**
PATTERNS = {
    "判据件数":     re.compile(r"判据\s*\*{0,2}(\d+)\*{0,2}\s*件"),
    "Python脚本数": re.compile(r"Python\s*脚本\s*\*{0,2}(\d+)\*{0,2}"),
    "checksum行数": re.compile(r"checksum[^0-9\n]{0,40}?\*{0,2}(\d+)\*{0,2}\s*files"),
    "身份族数":     re.compile(r"identity_families[^0-9]{0,12}(\d+)|身份族\s*\*{0,2}(\d+)\*{0,2}\s*族"),
}
# ★★ 「名册人数」**故意不做**。第一版做了，实跑立刻误报：
#    文中 `600 人名册` 是**项目的目标规模**（「600 人名册跨 12 族与整部人类史」），
#    不是「现在有 600 人」的状态断言，而实况是 100 人。
#    **正则分不出「目标」与「状态」**——分不出就不要猜，宁可不管这一项。
#    （这与本件自己写在射程里的那句一致：只管能机械数出来、且**语义无歧义**的量。）


# ★★ 带「真值」二字的行是**在引用一个已知错值做记录**，不是当前断言。
#   实例（VERIFICATION.md 第 18 行的警示块）：
#     `checksum **305 files**（真值 341）、Python 脚本 **66**（真值 84）`
#   那是 v0.0.0.76 复盘时留下的历史记录，**改掉它就是抹掉证据**。
#   本件因此**跳过这类行**——分不出「当前断言」与「引用旧错值」就会误报，
#   而误报会让这道判据被当成噪声关掉。
_HISTORICAL = "真值"


def stated(text: str) -> dict:
    """→ {键: [文中出现过的所有该类数字]}。**全都收，不只取第一个**——
    同一个数在文中出现多次而彼此不一致，本身就是要报的事。"""
    text = "\n".join(l for l in text.splitlines() if _HISTORICAL not in l)
    out = {}
    for key, rx in PATTERNS.items():
        vals = []
        for m in rx.finditer(text):
            g = next((x for x in m.groups() if x), None)
            if g:
                vals.append(int(g))
        if vals:
            out[key] = vals
    return out


def audit(root: pathlib.Path) -> dict:
    f = root / "VERIFICATION.md"
    if not f.is_file():
        return {"状态": "VERIFICATION.md 不在——**未核（不是通过）**"}
    text = f.read_text(encoding="utf-8")
    real, said = real_counts(root), stated(text)
    rows, bad = [], 0
    for key, r in real.items():
        vals = said.get(key)
        if r is None:
            rows.append({"项": key, "实况": "数不出来", "文中": vals, "判定": "**未核**"})
            continue
        if not vals:
            rows.append({"项": key, "实况": r, "文中": None,
                         "判定": "文中没有这个数——**本件管不到，不算通过**"})
            continue
        ok = r in vals
        bad += not ok
        rows.append({"项": key, "实况": r, "文中": vals,
                     "判定": "✓" if ok else f"**对不上**（文中最新写 {vals[0]}，实况 {r}）"})
    # ★★ 2026-08-05 加：**待裁定台账自己声明的条数**，与实际的 `## ①…` 条数。
    #   实测那天它标题写「十条」、导语写「十一条」，而实际有 **12 条**——
    #   同一份文件里两个数字，两个都错。**和 VERIFICATION.md 那次同一种漂**，
    #   而此前没有任何门看它一眼。
    led = root / "references" / "ledgers" / "_待用户裁定.md"
    if led.is_file():
        lt = led.read_text(encoding="utf-8")
        n_real = len(re.findall(r"^## [①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]", lt, re.M))
        CN = "〇一二三四五六七八九十"
        def _cn(x):
            return "十" + CN[x - 10] if 10 < x < 20 else ("十" if x == 10 else CN[x])
        want = _cn(n_real)
        saids = re.findall(r"待用户裁定（\*\*(.+?)条\*\*）|一眼看完：(.+?)条各是什么", lt)
        flat = [x for pair in saids for x in pair if x]
        off = [s for s in flat if s != want]
        # ★★ 同日再补：**「一眼看完」表里的行数，与正文节数**。
        #   实测 ⑫ 只有正文、**没进表**——自称条数那一项当时是 ✓，因为它只比标题与导语。
        #   **一眼看完漏一行，这张表就不再是一眼看完。**
        n_tab = len(re.findall(r"^\| \*\*[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]\*\* \|", lt, re.M))
        rows.append({"项": "待裁定台账·表行数 vs 正文节数",
                     "实况": f"正文 {n_real} 节", "文中": f"表 {n_tab} 行",
                     "判定": "✓" if n_tab == n_real
                             else f"**对不上**（表 {n_tab} 行，正文 {n_real} 节——有条目没进表）"})
        bad += (n_tab != n_real)

        rows.append({"项": "待裁定台账条数", "实况": f"{n_real}（{want}条）",
                     "文中": flat or None,
                     "判定": "✓" if (flat and not off)
                             else (f"**对不上**（文中写 {off}，实况 {want}条）" if off
                                   else "文中没有声明条数——**本件管不到，不算通过**")})
        bad += bool(off)

    return {"**对不上的项数**": bad, "明细": rows,
            "★ 射程": "只管能机械数出来的几类；「真实夹具 5/19」那种要读判据内部结构的本件不碰",
            "★ 口径": "**只报不改**——对不上时不知道该改哪边（文件陈旧 or 仓库真少了东西），那是人的判断"}


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    print("── 正向：文中的数与实况一致 → 不报 ──")
    s = stated("判据 **53** 件，Python 脚本 **81**，checksum 全量校验 368 files")
    chk(f"{s}", s.get("判据件数") == [53] and s.get("Python脚本数") == [81]
        and s.get("checksum行数") == [368])
    print("── ★★ 反向对照①：同一个数在文中出现两次且不一致，**两个都要收上来** ──")
    s2 = stated("判据 51 件 …… 后文又写 判据 **53** 件")
    chk(f"{s2}", s2.get("判据件数") == [51, 53])
    print("── ★★ 反向对照④：**带「真值」的行是引用旧错值，不许当成当前断言** ──")
    s4 = stated("checksum **305 files**（真值 341）、Python 脚本 **66**（真值 84）")
    chk(f"{s4}", not s4)
    chk("★ 而同一段去掉「真值」注解后**要收上来**（证明不是正则本身失效）",
        stated("checksum **305 files**、Python 脚本 **66**").get("Python脚本数") == [66])
    print("── ★★★ 反向对照⑤：**待裁定台账自称的条数与实际 `## ①…` 条数对不上 → 必须报** ──")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "VERIFICATION.md").write_text("判据 **1** 件", encoding="utf-8")
        led = root / "references" / "ledgers"
        led.mkdir(parents=True)
        # 标题写「十条」、导语写「十一条」，而实际写了 12 条 —— 2026-08-05 的真实状态
        body = ("# 待用户裁定（**十条**）\n\n## 一眼看完：十一条各是什么\n\n"
                + "".join(f"## {c} x\n\n" for c in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"))
        (led / "_待用户裁定.md").write_text(body, encoding="utf-8")
        r = audit(root)
        row = [x for x in r["明细"] if x["项"] == "待裁定台账条数"][0]
        chk(f"实况 {row['实况']}，文中 {row['文中']} → {row['判定'][:24]}",
            "对不上" in row["判定"] and r["**对不上的项数**"] >= 1)

        print("── ★★★ 反向对照⑥：**正文有 ⑫ 而表里没有 → 必须报**（自称条数那项是 ✓ 也不行） ──")
        tab = ("# 待用户裁定（**十二条**）\n\n## 一眼看完：十二条各是什么\n\n"
               + "".join(f"| **{c}** | x | y | z |\n" for c in "①②③④⑤⑥⑦⑧⑨⑩⑪")   # 少 ⑫
               + "\n" + "".join(f"## {c} x\n\n" for c in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"))
        (led / "_待用户裁定.md").write_text(tab, encoding="utf-8")
        rr = audit(root)
        t_row = [x for x in rr["明细"] if "表行数" in x["项"]][0]
        c_row = [x for x in rr["明细"] if x["项"] == "待裁定台账条数"][0]
        chk(f"{t_row['判定'][:40]}", "对不上" in t_row["判定"])
        chk("★ 而自称条数那一项此时是 ✓——**证明两项各管各的**", c_row["判定"] == "✓")

        print("── ★★ 反向对照⑦：**改成一致之后就不许再报**（证明不是恒报） ──")
        good = ("# 待用户裁定（**十二条**）\n\n## 一眼看完：十二条各是什么\n\n"
                + "".join(f"| **{c}** | x | y | z |\n" for c in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫")
                + "\n" + "".join(f"## {c} x\n\n" for c in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"))
        (led / "_待用户裁定.md").write_text(good, encoding="utf-8")
        det = audit(root)["明细"]
        chk("两项都 ✓", all(x["判定"] == "✓" for x in det if "台账" in x["项"]))

        print("── ★ 反向对照⑧：**台账不存在时不报，也不算通过** ──")
        (led / "_待用户裁定.md").unlink()
        chk("台账缺失 → 明细里没有这一项",
            not [x for x in audit(root)["明细"] if x["项"] == "待裁定台账条数"])

    print("── ★★ 反向对照②：文中根本没写这个数 → 报「管不到」，**不许算通过** ──")
    s3 = stated("这段里什么数都没有")
    chk(f"{s3}", not s3)
    print("── ★★ 反向对照③：**按定义属性数，不按目录位置** ──")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d) / "persona-distiller"
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "check_a.py").write_text("x", encoding="utf-8")
        (root / "scripts" / "check_b.py").write_text("x", encoding="utf-8")
        (root / "scripts" / "helper.py").write_text("x", encoding="utf-8")
        g = root.parent / "persona-distiller-group"
        for fam in ("族甲", "族乙"):
            (g / fam).mkdir(parents=True)
            (g / fam / "_category.json").write_text("{}", encoding="utf-8")
            (g / fam / "someone").mkdir()
        for noise in ("agents", "schemas", "scripts"):     # ★ 不是族，不许被数进去
            (g / noise).mkdir(parents=True)
        rc = real_counts(root)
        chk(f"判据 {rc['判据件数']} 应为 2（不含 helper.py）", rc["判据件数"] == 2)
        chk(f"Python 脚本 {rc['Python脚本数']} 应为 3", rc["Python脚本数"] == 3)
        chk(f"**身份族 {rc['身份族数']} 应为 2**（agents/schemas/scripts 三个不是族）",
            rc["身份族数"] == 2)
        chk(f"名册人数 {rc['名册人数']} 应为 2（**实况仍算，只是不与文中比**）",
            rc["名册人数"] == 2)
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", help="persona-distiller 根目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    info = audit(pathlib.Path(a.root or "."))
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 1 if info.get("**对不上的项数**") else 0


if __name__ == "__main__":
    sys.exit(main())
