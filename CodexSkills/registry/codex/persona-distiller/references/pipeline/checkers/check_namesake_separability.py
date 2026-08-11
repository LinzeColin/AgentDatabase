#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**同名可分性门**：这个人的同名者，靠姓名分得开吗？分不开就必须有 criteria 文件。

## 起因：Blackstone #169 抓源之前的实测（2026-08-11）

`check_authorship.build_patterns("William Blackstone")["name_rx"]` 打他自己的 13 个同名候选：

    14 个署名变体 → **12 个被认成目标本人**

读 regex 就知道为什么：中间名允许 0–2 个词，`W.` 也认。而

- **4 位同名者的「名＋中名」字面就是 `William Blackstone`**
  （William Blackstone Hubbard / Bradbury / Rennell / Lee）
- ★ 而**逐字与目标同名的 `canonical_name` 有 4 条**（含目标本人）——实测数，不是印象：
  目标、1595–1675 的拓居者、**`William Blackstone, Jr.`（规范档主标目不带 Jr.）**、
  GND 1146806930 的未定档。**`Jr.` 那条是我第一版漏算的**，
  夹具里我只编了 2 条同字面的，**真工作区一跑才是 3 条（不含目标）**。

**这个人靠姓名根本分不开。**

## 为什么要有这道门（而不是靠人记得）

`check_namesake_criteria.py` 早就存在（Sorby 父子逼出来的），也早就接进了 `quality_check`。
**但它「没有 criteria 文件的人物一律跳过」**——于是：

    全库 31 个工作区，**只有 4 个有 criteria 文件**。

「跳过」在产物里和「通过」长得一模一样。这道门补的正是这一段：
**先量「分不分得开」，分不开才要求 criteria**——不搞一刀切，也不靠人记得。

## 全库实测（2026-08-11，25 个有候选名单的 wip）

    姓名分不开的同名者共 **35 条**，散在 8 个人身上：
    Blackstone 11｜Paton 12｜Galen 5｜Livermore 2｜Nasmyth 2｜Barton 1｜Cicero 1｜Harvey 1

★ **其中只有 Livermore #100 已交付**（他儿子 Jesse Livermore Jr.、孙子 Jesse Livermore III）。
  去查了有没有真发生：**536 行台账里 Jr./III 命中 0 行**，语料正文只有同名门产物自己提到。
  → **机制在，事故没发生。**（[[proved-the-mechanism-never-asked-if-it-happened]] 的反向：
  这次先问了「发生没有」，答案是没有，所以**不报警**。）

★ **这 35 条里至少 1 条不是人**：Harvey #103 的那条是
  `William Harvey Hospital / William Harvey Research Institute`——机构名。
  本判据数的是「名字挡不挡得住」，不区分人与机构；**报数时要带上这句**。

## 判定

1. 找不到候选名单 → **`skip`（不适用，不是通过）**，退出 0 但打印说明；
2. 候选里没有一条与目标姓名混淆 → **通过**；
3. 有混淆而**没有** `namesake-criteria.json` → **失败**；
4. 有混淆、有 criteria，但某条**字面不同的**混淆名没被 `excluded_names` 覆盖 → **失败**；
5. 有**字面完全相同**的候选，而 criteria 里没写 `identical_name_policy` → **失败**。

★ 第 4 条是要害：有文件不等于覆盖到。**存在性检查是最容易假绿的一种。**
★★ 第 5 条与第 4 条**必须分开**：字面同名那一档写进 `excluded_names` 等于排除目标本人，
   **要求它「被覆盖」是在要求一件做不到的事**，那会逼人去放宽判据
   （[[a-red-that-can-never-turn-green-is-not-a-signal]]）。它要的是**写明靠什么分开**。
"""
import argparse
import importlib.util
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent


def _load_authorship():
    """借 check_authorship 的 build_patterns——**同一把尺子**，不另写一套。"""
    spec = importlib.util.spec_from_file_location(
        "_pd_ca_sep", HERE / "check_authorship.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_candidates(target_dir: pathlib.Path):
    """→ (候选名 list, 出处 Path)；找不到返回 ([], None)。

    ★ 候选名单在这条流水线上有**三种落点**（实测）：工作区内、工作区外的 wip 根、
    以及同名门自己的 output。**逐层往上找，不猜深度。**
    """
    seen = []
    probe = [target_dir, target_dir.parent, target_dir.parent.parent,
             target_dir.parent.parent.parent]
    for d in probe:
        if not d or not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            if "namesake" not in f.name.lower():
                continue
            try:
                o = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            rows = o.get("candidates") if isinstance(o, dict) else None
            if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                names = [str(r.get("canonical_name") or "").strip() for r in rows]
                names = [n for n in names if n]
                if len(names) > len(seen):
                    seen, src = names, f
        if seen:
            return seen, src
    return [], None


def confusable(target_name: str, names, mod) -> list:
    """→ 姓名层面与目标分不开的候选名（已剔除与目标**逐字相同**的第一条自身）。"""
    pats = mod.build_patterns(target_name)
    raw = pats["name_rx"]
    rx = re.compile(raw) if isinstance(raw, str) else raw
    out, self_seen = [], False
    for n in names:
        if n.strip().lower() == target_name.strip().lower() and not self_seen:
            self_seen = True          # 名单里的目标本人只跳过一次
            continue                  # ——**第二条同字面的是真同名者，要算**
        if rx.search(n):
            out.append(n)
    return out


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def split_identical(target_name: str, confused: list):
    """→ (字面完全相同的, 字面不同但混淆的)。

    ★★★ Blackstone #169 真工作区实测逼出来的一档：**13 个候选里有 4 条的
    `canonical_name` 逐字就是 `William Blackstone`**——目标本人、1595–1675 的拓居者、
    `William Blackstone, Jr.`（规范档主标目不带 Jr.）、GND 1146806930 的未定档。

    这一档**结构上不可能靠 `excluded_names` 处理**：把 `William Blackstone` 写进排除名单，
    等于把目标本人也排除掉。**要求它被「覆盖」是在要求一件做不到的事**，
    而做不到的要求只会逼人去放宽判据（[[a-red-that-can-never-turn-green-is-not-a-signal]]）。

    所以改成：这一档单独计，**要求 criteria 里写明「靠什么把它们分开」**（标识符／年代／出处），
    而不是要求它出现在排除名单里。
    """
    t = _norm(target_name)
    same = [n for n in confused if _norm(n) == t]
    diff = [n for n in confused if _norm(n) != t]
    return same, diff


def criteria_gap(target_dir: pathlib.Path, diff_named: list, same_named: list):
    """→ (criteria 路径 or None, 排除名单没覆盖的, 字面同名但没写处置政策的)。"""
    crit = None
    for d in (target_dir, target_dir.parent, target_dir.parent.parent):
        f = d / "namesake-criteria.json"
        if f.is_file():
            crit = f
            break
    if crit is None:
        return None, list(diff_named), list(same_named)
    try:
        o = json.loads(crit.read_text(encoding="utf-8"))
    except Exception:
        return crit, list(diff_named), list(same_named)
    norm = {_norm(x) for x in (o.get("excluded_names") or [])}
    # ★★★ 第三档（Holmes #170 逼出来的）：**有些名字不能写进 excluded_names，
    #   因为那个字符串同时是目标本人的署名形式**。
    #   实例：西部小说作者署 `Oliver W. Holmes Jr.`，而目标本人常署
    #   `Oliver W. Holmes` / `O. W. Holmes`——把它排除掉就是**丢真材料**。
    #   这一档要的不是「被排除」，而是**逐条点名 + 有处置政策**，
    #   与「字面完全相同」那一档同理。**不点名照样红。**
    unex = {_norm(x) for x in (o.get("unexcludable_names") or [])}
    policy0 = str(o.get("identical_name_policy") or "").strip()
    missing = [n for n in diff_named
               if _norm(n) not in norm and not (_norm(n) in unex and policy0)]
    # 字面同名那一档：要的是**写明怎么分**，不是出现在排除名单里
    policy = str(o.get("identical_name_policy") or "").strip()
    unpolicied = [] if policy else list(same_named)
    return crit, missing, unpolicied


def evaluate(target_dir: pathlib.Path, target_name: str, mod) -> dict:
    names, src = find_candidates(target_dir)
    if not names:
        return {"状态": "skip", "说明": "**找不到同名候选名单——不适用，不是通过**",
                "候选数": 0, "分不开": 0, "未覆盖": [], "字面同名未定政策": []}
    confused = confusable(target_name, names, mod)
    if not confused:
        return {"状态": "ok", "候选数": len(names), "分不开": 0, "未覆盖": [],
                "字面同名未定政策": [], "出处": str(src)}
    same, diff = split_identical(target_name, confused)
    crit, missing, unpolicied = criteria_gap(target_dir, diff, same)
    # ★ 三档各自的条数要现算——**第一版把三档合报成「都靠 excluded_names」，
    #   同一个工具、同一类错误我犯了第二次**（[[gates-cover-json-not-the-prose-users-read]]）。
    _unex, _pol = set(), ""
    if crit:
        try:
            _o = json.loads(pathlib.Path(crit).read_text(encoding="utf-8"))
            _unex = {_norm(x) for x in (_o.get("unexcludable_names") or [])}
            _pol = str(_o.get("identical_name_policy") or "").strip()
        except Exception:
            pass
    n_unex = sum(1 for n in diff if _norm(n) in _unex and _pol)
    n_excl = len(diff) - n_unex - len(missing)
    bad = bool(missing) or bool(unpolicied)
    return {"状态": "fail" if bad else "ok",
            "候选数": len(names), "分不开": len(confused),
            "★ 其中字面完全相同": len(same),
            "靠 excluded_names": n_excl, "靠 unexcludable_names＋政策": n_unex,
            "分不开的是": confused, "未覆盖": missing,
            "字面同名未定政策": unpolicied,
            "criteria": str(crit) if crit else None, "出处": str(src)}


def _fixture(tmp: pathlib.Path, name, cands, excluded=None):
    d = tmp
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps({"name": name}, ensure_ascii=False),
                                 encoding="utf-8")
    (d / "namesake_candidates.json").write_text(
        json.dumps({"candidates": [{"canonical_name": c} for c in cands]},
                   ensure_ascii=False), encoding="utf-8")
    if excluded is not None:
        (d / "namesake-criteria.json").write_text(
            json.dumps({"subject": name, "excluded_names": excluded},
                       ensure_ascii=False), encoding="utf-8")
    return d


def self_test() -> int:
    import tempfile
    mod = _load_authorship()
    cases, fails = [], []

    def chk(label, got, want):
        cases.append(label)
        if got != want:
            fails.append("%s：得 %r，应为 %r" % (label, got, want))

    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # ① 分不开且**无 criteria** → fail
        d = _fixture(tmp / "a", "William Blackstone",
                     ["William Blackstone", "William Seymour Blackstone",
                      "William Blackstone Hubbard"])
        r = evaluate(d, "William Blackstone", mod)
        chk("① 分不开无 criteria → fail", r["状态"], "fail")
        chk("① 分不开条数", r["分不开"], 2)

        # ② 分不开、有 criteria **覆盖齐** → ok
        d = _fixture(tmp / "b", "William Blackstone",
                     ["William Blackstone", "William Seymour Blackstone",
                      "William Blackstone Hubbard"],
                     excluded=["William Seymour Blackstone",
                               "William Blackstone Hubbard"])
        r = evaluate(d, "William Blackstone", mod)
        chk("② 覆盖齐 → ok", r["状态"], "ok")

        # ③ ★ 反对照：有 criteria 但**漏一条** → 必须 fail（存在性检查会假绿）
        d = _fixture(tmp / "c", "William Blackstone",
                     ["William Blackstone", "William Seymour Blackstone",
                      "William Blackstone Hubbard"],
                     excluded=["William Seymour Blackstone"])
        r = evaluate(d, "William Blackstone", mod)
        chk("③ 漏一条 → fail", r["状态"], "fail")
        chk("③ 漏的是 Hubbard", r["未覆盖"], ["William Blackstone Hubbard"])

        # ④ 姓名本来就分得开 → ok，且不要求 criteria
        d = _fixture(tmp / "d", "Hugo Grotius",
                     ["Hugo Grotius", "Willem de Groot", "Jan de Groot"])
        r = evaluate(d, "Hugo Grotius", mod)
        chk("④ 分得开 → ok", r["状态"], "ok")
        chk("④ 分不开 0 条", r["分不开"], 0)

        # ⑤ ★ 反对照：没有候选名单 → **skip，不是 ok**
        d = tmp / "e"
        d.mkdir(parents=True, exist_ok=True)
        (d / "meta.json").write_text('{"name": "X Y"}', encoding="utf-8")
        r = evaluate(d, "X Y", mod)
        chk("⑤ 无候选名单 → skip（不是 ok）", r["状态"], "skip")

        # ★★★ ⑧ 第三档：声明为「不可用字符串排除」+ 有政策 → 放行；
        #   **只声明、不写政策 → 仍必须红**（反对照）。
        d = _fixture(tmp / "h", "William Blackstone",
                     ["William Blackstone", "William Seymour Blackstone"],
                     excluded=[])
        crit = d / "namesake-criteria.json"
        o = json.loads(crit.read_text(encoding="utf-8"))
        o["unexcludable_names"] = ["William Seymour Blackstone"]
        crit.write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
        r = evaluate(d, "William Blackstone", mod)
        chk("⑧ 只声明不可排除、没有政策 → 仍 fail", r["状态"], "fail")
        o["identical_name_policy"] = "靠 LCCN 与中名硬判"
        crit.write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
        r = evaluate(d, "William Blackstone", mod)
        chk("⑧ 声明 + 政策齐 → ok", r["状态"], "ok")

        # ⑥ ★ 名单里**两条同字面**：第一条是目标自己，第二条是真同名者，必须算
        d = _fixture(tmp / "f", "William Blackstone",
                     ["William Blackstone", "William Blackstone"])
        r = evaluate(d, "William Blackstone", mod)
        chk("⑥ 同字面的第二条要算", r["分不开"], 1)

        # ⑥b ★ 字面同名：没写 identical_name_policy → fail；写了 → ok
        d = _fixture(tmp / "g", "William Blackstone",
                     ["William Blackstone", "William Blackstone"],
                     excluded=["某个别人"])
        r = evaluate(d, "William Blackstone", mod)
        chk("⑥b 字面同名无政策 → fail", r["状态"], "fail")
        chk("⑥b 字面同名计数", r["★ 其中字面完全相同"], 1)
        crit = d / "namesake-criteria.json"
        o = json.loads(crit.read_text(encoding="utf-8"))
        o["identical_name_policy"] = "靠 LCCN 硬判"
        crit.write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
        r = evaluate(d, "William Blackstone", mod)
        chk("⑥b 写了政策 → ok", r["状态"], "ok")

        # ⑦ ★ 拿**真工作区**测，别只测自己编的夹具
        real = HERE.parent / ("../../../skill_log_evals/persona-distiller/_corpora/"
                              "wip-blackstone-169/workspaces/william-blackstone/"
                              "william-blackstone")
        real = real.resolve()
        if (real / "meta.json").is_file():
            r = evaluate(real, "William Blackstone", mod)
            chk("⑦ 真工作区 Blackstone → ok", r["状态"], "ok")
            chk("⑦ 真工作区分不开条数 == 11", r["分不开"], 11)
            chk("⑦ 真工作区字面同名 == 3", r["★ 其中字面完全相同"], 3)
        else:
            cases.append("⑦ 真工作区不在本机，跳过（**不算通过**）")

    print("自测 %d/%d 通过" % (len(cases) - len(fails), len(cases)))
    for f in fails:
        print("  ✗", f)
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="同名可分性门")
    ap.add_argument("target", nargs="?", help="工作区目标目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.target:
        ap.error("需要 target，或用 --self-test")
    d = pathlib.Path(a.target).resolve()
    meta = d / "meta.json"
    if not meta.is_file():
        print("✗ 找不到 meta.json：%s" % meta)
        return 2
    name = json.loads(meta.read_text(encoding="utf-8")).get("name") or ""
    if not name:
        print("✗ meta.json 里没有 name")
        return 2
    r = evaluate(d, name, _load_authorship())
    if r["状态"] == "skip":
        print("· 同名可分性 **跳过（不适用，不是通过）**：%s" % r["说明"])
        return 0
    if r["状态"] == "ok" and r["分不开"] == 0:
        print("✓ 同名可分性：%d 个候选，**姓名层面全部分得开**" % r["候选数"])
        return 0
    if r["状态"] == "ok":
        same = r.get("★ 其中字面完全相同", 0)
        print("✓ 同名可分性：%d 个候选里 **%d 条姓名分不开**，均已有处置：\n"
              "  · %d 条靠 excluded_names 排除\n"
              "  · %d 条**声明为不可用字符串排除**（那个串同时是目标本人的署名形式），"
              "靠 identical_name_policy 的硬判据分开\n"
              "  · %d 条**与目标字面完全相同**，同样靠 identical_name_policy\n"
              "  criteria：%s" % (r["候选数"], r["分不开"],
                                 r.get("靠 excluded_names", 0),
                                 r.get("靠 unexcludable_names＋政策", 0),
                                 same, r["criteria"]))
        return 0
    n_bad = len(r["未覆盖"]) + len(r["字面同名未定政策"])
    print("✗ 同名可分性 %d 条问题：\n" % n_bad)
    print("  %d 个候选里 **%d 条与目标姓名分不开**（其中 **%d 条字面完全相同**）："
          % (r["候选数"], r["分不开"], r.get("★ 其中字面完全相同", 0)))
    if r["未覆盖"]:
        print("\n  ① **%d 条没有被 excluded_names 覆盖**：" % len(r["未覆盖"]))
        for n in r["未覆盖"]:
            print("      - %s" % n)
    if r["字面同名未定政策"]:
        print("\n  ② **%d 条与目标字面完全相同**，而 criteria 里没有 `identical_name_policy`："
              % len(r["字面同名未定政策"]))
        for n in r["字面同名未定政策"]:
            print("      - %s" % n)
        print("      ↑ 这一档**不能靠 excluded_names**——写进去等于排除目标本人。"
              "\n        要写的是**靠什么把它们分开**：标识符／年代／出处。")
    if not r.get("criteria"):
        print("\n  ↑ **这个工作区没有 namesake-criteria.json**。"
              "`check_namesake_criteria.py` 对没有该文件的人物一律跳过——"
              "**「跳过」在产物里和「通过」长得一模一样。**")
    else:
        print("\n  ↑ 有 criteria 文件不等于覆盖到。**存在性检查是最容易假绿的一种。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
