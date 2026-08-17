#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_measurements_fresh.py —— 量测产物是不是**当前这版工具**出的

## 为什么有这件

2026-08-13，为了排 Plato 进阶段 2，顺手全库重跑了一次 `assign_lanes.py`。
结果 **4 个工作区的产物与现算不一致**，而差异**远大于我那次改动**：

    kant-179          道 6 → 3    writings 53→60、expression 3→0、decisions 1→0、timeline 3→0
    machiavelli-177   道 4 → 4    expression 10 → 1
    plato-186         道 2 → 1    conversations 7 → 0
    rousseau-178      道 5 → 4    expression 9 → 0

★ Kant 那一条**工具的注释里早就写着**：

> 实测 676 份里 10 份中招…且**把 Kant 的道数从 6 顶到了 6** ——
> deep 档要求 6 道，他是靠这三条假道够到的。

**规则改了、注释写了、产物没重跑。** 台账里他仍然记着 6 道。
[[fixed-the-symptom-kept-the-root-cause]]：**修好判据不等于修好数据。**

★ 这一次侥幸没咬到人（判分清单是另算的，那里记的就是 quick）。
  但它是「下一次一定会咬」的那一类：**产物落后于工具，而两者看起来都是最新的。**

## 判什么

对每个工作区，把量测工具**在临时目录里重跑一遍**，与仓里存着的产物**逐字比对**。
不一致 ⇒ 报出来并给出逐项差异。

    assign_lanes.py     → raw/_lanes.json
    classify_primary.py → raw/_primary.json

★ **本件不改任何文件**：只读、只比、只报。要更新用 `--apply`。

★★ 与 `check_cases_match_generator.py` 同一形态——那件对**用例生成器**做这件事，
   而分道/分档这一侧此前**没有对应的**。这就是那个缺口。

## 用法

    python3 check_measurements_fresh.py                 # 全库只查
    python3 check_measurements_fresh.py --workspace <路径>
    python3 check_measurements_fresh.py --apply         # 重出不一致的那些
    python3 check_measurements_fresh.py --self-test

退出码：0＝全部一致（或全部跳过）；1＝有不一致；4＝一个工作区都跑不了
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
CORPORA = HERE.parents[1] / "_corpora"

# (产物文件名, 工具, 传给工具的参数模板)
TOOLS = [
    ("_lanes.json", "assign_lanes.py", ["--raw", "{raw}"]),
    ("_primary.json", "classify_primary.py", ["--raw", "{raw}"]),
    # ★★★ 2026-08-18 补两件**并列的兄弟产物**。
    #   起因：修完上面两件之后问了一句「raw/ 下还有几种工具生成物」——
    #   实测 19 个工作区**每个都有** `_dedup.json` 与 `_voice.json`，
    #   而它们**从来不在本件的名单里**。同一族的洞，只是没人撞上。
    #   `_dedup.json` 尤其承重：它填台账的 `derived_from`，
    #   决定「两个 source id 是不是两处独立证据」。
    #   [[fixed-the-symptom-kept-the-root-cause]]（并列的兄弟链有同样的洞）
    ("_dedup.json", "dedup_corpus.py", ["--raw", "{raw}"]),
    ("_voice.json", "measure_voice.py", ["--raw", "{raw}"]),
]

# ★★★ 有些工具还有**必填参数**，光给 `--raw` 会 argparse 报错、一个字节不写。
#   这里声明「从产物自带的 `★参数` 里取哪一项、用哪个开关重放」。
#   {产物: (命令行开关, `★参数` 里的键名)}
REPLAY_ARGS = {
    "_primary.json": ("--surname", "surname"),
}


def workspaces(base: pathlib.Path):
    """★★★ 按**本件真正要比的那份产物**定位，不只按台账定位（2026-08-18 补）。

    `iter_workspaces` 是按 `evidence/source-ledger.jsonl` 找工作区的 ——
    那是「走到建台账那一步」的标志。而**本件比的是 `raw/` 下的量测产物**，
    它在流程里出现得**早得多**。两者不是同一个集合。

    实测（2026-08-18）：全库有 `raw/_lanes.json` 的 **19** 个工作区里，
    **1 个**（`wip-plato-186`）没有台账 ⇒ 一直不在扫描面里。
    而 Plato 的**整条延后理由**（「真值只有 1 条道」）就建在那份 `_lanes.json` 上；
    当天我改了 `assign_lanes.py` 且**已证明会改动他那一行**，本件却照报「全部一致」。
    —— **一盏假绿，且恰好落在唯一一个靠它下结论的人身上。**

    ⇒ 取**并集**：台账定位的 ∪ 「`raw/` 下有本件任一产物的」。
      不动 `iter_workspaces`（它被十几件判据共用，射程各不相同）。
      [[a-gates-scan-set-is-smaller-than-reality]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    """
    by_ledger = {p for p in iter_workspaces(base) if (p / "raw").is_dir()}
    by_artifact = set()
    for artifact, _tool, _a in TOOLS:
        for f in base.glob("wip-*/**/raw/" + artifact):
            by_artifact.add(f.parent.parent)
    return sorted(by_ledger | by_artifact)


def rerun(ws: pathlib.Path, artifact: str, tool: str, argtpl: list):
    """在**临时目录**里重跑，返回 (现算内容 or None, 说明)。

    ★ 为什么要复制到临时目录：工具是**就地写产物**的。
      直接在仓里跑会把待比对的那份覆盖掉——第一次我就是这么干的，
      比对之前先把答案改掉了，得先 `git checkout` 才救回来。
    """
    src = ws / "raw" / artifact
    if not src.exists():
        return None, "仓里没有这份产物"
    with tempfile.TemporaryDirectory() as td:
        tmp_raw = pathlib.Path(td) / "raw"
        shutil.copytree(ws / "raw", tmp_raw)
        # ★★★ **先把待比对的那份从沙箱里删掉**（2026-08-18 加）。
        #   否则「重跑没产出」这道守卫**永远触发不了** —— 它看到的是
        #   `copytree` 自己刚拷进去的那一份。实证：`classify_primary.py` 缺
        #   `--surname` 必然 argparse 报错 rc=2、一个字节不写，而本函数照样
        #   读回原件、与仓里那份**逐字相同** ⇒ 报「✓ 一致」。
        #   **`_primary.json` 这一半从建成起就没被真验过。**
        #   ⇒ 删掉之后，「存在」才等于「这次真的生成了」。
        #   [[a-step-that-runs-after-the-write-changes-nothing]]｜[[harness-limits-masquerade-as-product-defects]]
        (tmp_raw / artifact).unlink(missing_ok=True)
        args = [a.format(raw=str(tmp_raw), ws=str(ws)) for a in argtpl]
        # ★★ 产物自带的生成参数**原样重放**（不从 meta.json 猜）。
        #   没有这个字段 ⇒ 说明它是**旧版工具**出的，本次判**未核**，不是一致。
        try:
            stored_meta = json.loads(src.read_text(encoding="utf-8"))
        except ValueError:
            stored_meta = {}
        need = REPLAY_ARGS.get(artifact)
        if need:
            recorded = (stored_meta.get("★参数") or {}).get(need[1])
            if not recorded:
                return None, ("产物里没有 `★参数.%s` —— 它是**旧版工具**出的，"
                              "本次判**未核**（重放参数不能从 meta.json 猜：`da Vinci`/"
                              "`von Bismarck` 会猜错，猜错就是假漂移）" % need[1])
            for v in (recorded if isinstance(recorded, list) else [recorded]):
                args += [need[0], str(v)]
        r = subprocess.run([sys.executable, str(HERE / tool)] + args,
                           capture_output=True, text=True)
        out = tmp_raw / artifact
        # ★★ 退出码非 0 ⇒ **未核**，不许再去读产物碰运气
        if r.returncode != 0:
            return None, ("重跑失败 rc=%d：%s" % (r.returncode,
                          ((r.stderr or "") + (r.stdout or "")).strip().replace("\n", " ")[:150]))
        if not out.exists():
            return None, f"重跑没产出（rc={r.returncode}）：{(r.stderr or '')[:120]}"
        try:
            return json.loads(out.read_text(encoding="utf-8")), ""
        except ValueError as e:
            return None, f"重跑产出不是合法 JSON：{e}"


def diff_of(stored: dict, now: dict):
    """只报**有意义的**差异：顶层标量 + 逐道/逐档计数。"""
    d = {}
    for k in ("lanes", "去掉纸面道后", "总数", "一手占比下界", "一手占比上界"):
        if k in stored or k in now:
            if stored.get(k) != now.get(k):
                d[k] = (stored.get(k), now.get(k))
    for k in ("逐道份数", "计数"):
        a, b = stored.get(k) or {}, now.get(k) or {}
        for kk in sorted(set(a) | set(b)):
            if a.get(kk) != b.get(kk):
                d[f"{k}.{kk}"] = (a.get(kk), b.get(kk))
    return d


def run(base: pathlib.Path, only=None, apply=False):
    wss = [only] if only else workspaces(base)
    rows, ran = [], 0
    for ws in wss:
        for artifact, tool, argtpl in TOOLS:
            stored_p = ws / "raw" / artifact
            if not stored_p.exists():
                continue
            stored = json.loads(stored_p.read_text(encoding="utf-8"))
            now, why = rerun(ws, artifact, tool, argtpl)
            if now is None:
                rows.append({"工作区": ws.parent.parent.name, "产物": artifact,
                             "★ 未判": why})
                continue
            ran += 1
            d = diff_of(stored, now)
            if d:
                rows.append({"工作区": ws.parent.parent.name, "产物": artifact,
                             "差异": {k: f"{v[0]} → {v[1]}" for k, v in d.items()}})
                if apply:
                    stored_p.write_text(json.dumps(now, ensure_ascii=False, indent=1) + "\n"
                                        if not stored_p.read_text(encoding="utf-8").startswith("{\n \"")
                                        else json.dumps(now, ensure_ascii=False, indent=1) + "\n",
                                        encoding="utf-8")
    return rows, ran, len(wss)


def self_test() -> int:
    """正反对照：**故意改坏一份产物**，本件必须报出来；改回去必须变绿。"""
    wss = workspaces(CORPORA)
    target = None
    for ws in wss:
        if (ws / "raw" / "_lanes.json").exists():
            target = ws
            break
    if target is None:
        print("★★ **未跑，不是通过**：这棵树里没有任何 `_lanes.json`，无从对照。")
        print("   见仓根 `START-HERE.md`「语料在哪」一节。退出码 5 = 跳过。")
        return 5

    p = target / "raw" / "_lanes.json"
    backup = p.read_text(encoding="utf-8")
    bad = 0
    try:
        # ① 未改之前：必须一致
        rows, ran, _ = run(CORPORA, only=target)
        drift = [r for r in rows if "差异" in r]
        ok1 = not drift
        bad += 0 if ok1 else 1
        print(f"  {'✓' if ok1 else '✗'} 正对照：未动 {target.parent.parent.name} 时应当一致"
              f"（实得差异 {len(drift)} 项）")
        if drift:
            print(f"      {drift[0].get('差异')}")

        # ② 改坏：把道数改掉一位，必须报出来
        d = json.loads(backup)
        d["lanes"] = (d.get("lanes") or 0) + 7
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rows2, _, _ = run(CORPORA, only=target)
        drift2 = [r for r in rows2 if "差异" in r and "lanes" in (r.get("差异") or {})]
        ok2 = bool(drift2)
        bad += 0 if ok2 else 1
        print(f"  {'✓' if ok2 else '✗'} 反对照：把 `lanes` 改成 +7 之后必须报出来"
              f"（实得 {len(drift2)} 项）")
        # ③ ★★★ **结构性守卫**：重跑失败时不许读回沙箱里那份拷贝。
        #   本件曾经就是这么假绿的 —— `copytree` 把待比对的产物一起拷进沙箱，
        #   工具因缺必填参数 argparse 报错 rc=2、一字未写，而「产物存在吗」
        #   看到的是拷贝，于是逐字相同 ⇒ 报「✓ 一致」。
        #   这里用一个**必然失败**的假工具验：必须得到「未判」，不许得到「一致」。
        import tempfile as _tf
        with _tf.TemporaryDirectory() as _td:
            fake = pathlib.Path(_td) / "always_fails.py"
            fake.write_text("import sys; sys.exit(9)\n", encoding="utf-8")
            shutil.copy(fake, HERE / "_selftest_always_fails.py")
            try:
                now, why = rerun(target, "_lanes.json", "_selftest_always_fails.py", ["--raw", "{raw}"])
                ok3 = now is None and "rc=9" in (why or "")
                bad += 0 if ok3 else 1
                print(f"  {'✓' if ok3 else '✗'} ★★★ 结构对照：重跑失败(rc=9) ⇒ 必须判**未判**，"
                      f"不许读回沙箱里的拷贝（实得：{('未判｜' + (why or ''))[:64] if now is None else '**读回了拷贝**'}）")
            finally:
                (HERE / "_selftest_always_fails.py").unlink(missing_ok=True)
    finally:
        p.write_text(backup, encoding="utf-8")

    # ③ 复原之后必须再次变绿 —— 不做这一步就不知道是不是我把文件改坏了
    rows3, _, _ = run(CORPORA, only=target)
    ok3 = not [r for r in rows3 if "差异" in r]
    bad += 0 if ok3 else 1
    print(f"  {'✓' if ok3 else '✗'} 复原对照：改回去之后必须重新变绿")

    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}"
          f"（★ 反例红了可能是红得凑巧，所以正例与复原例都要同时是绿的）")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--apply", action="store_true", help="重出不一致的产物（默认只查不改）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    only = pathlib.Path(a.workspace) if a.workspace else None
    rows, ran, n_ws = run(CORPORA, only=only, apply=a.apply)
    drift = [r for r in rows if "差异" in r]
    unjudged = [r for r in rows if "★ 未判" in r]
    out = {
        "工作区": n_ws, "实际比对的产物数": ran,
        "**与现算不一致**": len(drift),
        "★ 未判（跑不了，不是通过）": len(unjudged),
        "逐条": rows,
        "★ 口径": "把量测工具在临时目录里重跑一遍，与仓里的产物逐字比对；本件默认只读不改",
    }
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 1 if drift else (4 if ran == 0 else 0)

    print(f"工作区 {n_ws}｜实际比对 {ran} 份产物")
    if drift:
        print(f"\n✗ **{len(drift)} 份产物与现算不一致**"
              f"{'（已按 --apply 重出）' if a.apply else '（本件只报不改，用 --apply 重出）'}：")
        for r in drift:
            print(f"  · {r['工作区']} / {r['产物']}")
            for k, v in r["差异"].items():
                print(f"      {k}: {v}")
    elif unjudged:
        # ★★★ 2026-08-18：**结论不许算在未核之前。**
        #   本行原来无条件写「✓ 所有量测产物都与当前这版工具一致」，
        #   而下面紧跟着列出 19 份未核 —— 摘要与明细互相矛盾，读的人只看摘要。
        #   [[verdict-computed-before-the-corrections]]
        print("\n⚠ **比对成的都一致，但有 %d 份没比对成** —— 不下「全部一致」这个结论。"
              % len(unjudged))
    else:
        print("\n✓ 所有量测产物都与当前这版工具一致")
    if unjudged:
        # ★★★ 先把**结构性未核**分出来：`_dedup.json` / `_voice.json` 要**真语料在场**，
        #   而语料按裁定不进 git —— 在任何 git 检出里它们必然复验不了。
        #   这不是缺陷，是这棵树的射程；但**必须印出来**，否则它就变成一个隐形缺口
        #   （本件加它们之前，这两件产物压根不在名单里，无人知道没被验过）。
        #   逐条列 19 行近乎相同的话会淹掉真信号 ⇒ 归成一行。
        #   [[corpus-lives-outside-git-verify-the-pointers]]｜[[a-refusal-to-check-prints-one-error]]
        NEED_CORPUS = ("一份都没量到", "一份也读不到", "语料按裁定不进 git")
        struct = [r for r in unjudged if any(k in (r["★ 未判"] or "") for k in NEED_CORPUS)]
        rest = [r for r in unjudged if r not in struct]
        if struct:
            kinds = sorted({r["产物"] for r in struct})
            print("\n⚠ **结构性未核（本树没有语料，不是缺陷）**：%d 份，涉及 %s"
                  % (len(struct), "、".join(kinds)))
            print("   语料按裁定**不进 git**，`raw/` 里只有 `_ids*.txt` 指针 ⇒ "
                  "这两件产物在任何 git 检出里都复验不了。")
            print("   要真验：把语料放回 `raw/` 之后再跑本件（工具自己会说「未量，不是 0」）。")
        if rest:
            by_why = {}
            for r in rest:
                by_why.setdefault(r["★ 未判"], []).append("%s/%s" % (r["工作区"], r["产物"]))
            print(f"\n⚠ ★ **未判（跑不了，不是通过）**：{len(rest)} 份，{len(by_why)} 类")
            for why, who in sorted(by_why.items(), key=lambda x: -len(x[1])):
                print("  · **%d 份**：%s" % (len(who), why))
                print("      %s%s" % ("、".join(who[:4]), "…" if len(who) > 4 else ""))
        elif struct:
            print("\n✓ 除结构性未核之外，**没有其他未判项**")
    if ran == 0:
        print("\n★★ **一份都没比对成**——这不是通过。多半是语料不在本树，"
              "见仓根 `START-HERE.md`「语料在哪」。")
        return 4
    if drift:
        return 1
    # ★★ 有未核 ⇒ rc=4（未量），不是 rc=0。绿灯只留给「全都比过且都一致」。
    return 4 if unjudged else 0


if __name__ == "__main__":
    raise SystemExit(main())
