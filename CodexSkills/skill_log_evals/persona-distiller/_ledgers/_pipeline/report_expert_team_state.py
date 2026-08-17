#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一条命令重算「专家团队现在到底怎么样」—— **对着 Owner 那五条评分**。

为什么要有这份文件
------------------
2026-08-16 我给这两件判据写完之后，发现**没有任何东西调用它们** ——
本项目已记过九批的形状。[[a-checker-nothing-calls-is-not-a-checker]]

而它们真正的调用方不是流水线，是 **Owner 的那张评分表**：

> 真正独立性 40%｜已证实的决策增益不足 40%｜路由、覆盖、记录、自优化迭代、
> 有效激活调用、命中率都没有实质性收益｜使用过程有显著性故障和阻碍点

⇒ 本件把那五条**逐条现算一遍**，谁都可以随时重跑，不必问人、不看陈旧散文。
[[self-reported-numbers-must-be-computed]]｜[[stop-handing-the-same-decision-back]]

## 它报什么、不报什么

**报**：能现算的数（车队准入、名册族缺口、路由 vs 随机、分类器兜底率、
基准三个 oracle、团队级遥测条数）。
**不报**：任何「好/差」的评语。**阈值与结论都由人下。**

★ 每一项都印**口径**（分母是什么、样本多大、标签谁标的）。
★ 本件**只读**，不写任何产物；永远 rc=0（它是报告，不是门）。

用法
----
    python3 report_expert_team_state.py --registry-root <persona-distiller-group 目录>
    python3 report_expert_team_state.py --registry-root <...> --quick   # 跳过最慢的路由 24 题
"""
import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


# ★ 未取到数的节，攒在这里 —— 有任何一节没取到，整份报告就是「未量」（rc=4）。
_unmeasured = []
_current_section = [""]          # ★ 用列表存，免得各处再写 global


def section(title):
    _current_section[0] = title
    print("\n" + "═" * 72)
    print(title)
    print("═" * 72)


def selftest():
    """★★★ 2026-08-17：**「取不到」印对了话，退出码却是 0** —— 那把措辞抵消了。

    实测（`--registry-root` 少传一级）：正文印着「✗ 取不到 —— 不是「没问题」」
    外加一整段 Python 回溯，而 `rc=0` ⇒ 调用方读成通过。
    同族已修：`check_lessons_reach_the_bundle`（未量却 return 0）。
    """
    import subprocess as _sp, tempfile as _tf
    bad = []
    _self = str(pathlib.Path(__file__).resolve())
    with _tf.TemporaryDirectory() as _td:
        r = _sp.run([sys.executable, _self, "--registry-root", _td, "--quick"],
                    capture_output=True, text=True)
        o = r.stdout + r.stderr
        if r.returncode != 4:
            bad.append("★★★ 有节取不到时退出码 %d，应为 **4（未量）**" % r.returncode)
        if "未量，不是通过" not in o:
            bad.append("★★★ 有节取不到时没在结尾说「未量，不是通过」")
        if "一个数都没取到" not in o:
            bad.append("★★★ 没把「是哪几节没取到」列出来")
    # ★ 反对照：**真取得到的时候**必须回到 rc=0。
    #   ★★★ 这一半**不跑真 registry** —— 实测耗时：
    #        空目录（未量那半）  **1.9 秒**
    #        真 registry（反对照那半） **206.1 秒**
    #   `run_checks.py` 跑全部 40 件判据的墙钟是 **0.9 秒**；塞进一条 206 秒的，
    #   它会被超时杀掉 ⇒ 这条负对照就变成「从没被真跑过」的那一类。
    #   ⇒ 改成**按 AST 断言 `main()` 的返回值**：瞬时，且照样咬得住
    #     「把 `if _unmeasured:` 关掉」这个变异（实测已验）。
    #   真 registry 的那条路每次有人真跑这份报告就走一遍（今天实测 rc=0）。
    #   [[batch-changes-then-verify-once]]｜[[a-checker-nothing-calls-is-not-a-checker]]
    import ast as _ast
    _tree = _ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    _main = next(n for n in _tree.body
                 if isinstance(n, _ast.FunctionDef) and n.name == "main")
    _rets = [n.value.value for n in _ast.walk(_main)
             if isinstance(n, _ast.Return) and isinstance(n.value, _ast.Constant)]
    if _rets.count(4) != 1:
        bad.append("★★★ main() 里「未量」那档必须**恰好一个 return 4**（实得 %r）" % _rets)
    if _rets.count(0) != 1:
        bad.append("★★★ main() 里「真取得到」那档必须**恰好一个 return 0**（实得 %r）" % _rets)
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d" % (5 - len(bad), 5))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # ★ `required=True` 改成默认必填但让 `--self-test` 能独立跑 ——
    #   负对照必须能**不依赖它本该独立于的数据**跑起来（check_checkers 把
    #   「跑不起来的负对照」单列为 NOT-STANDALONE，因为它实际上从没被跑过）。
    ap.add_argument("--registry-root")
    ap.add_argument("--quick", action="store_true", help="跳过路由 24 题（最慢的一项）")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true",
                    help="只跑内置负对照（不需要 --registry-root）")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.registry_root:
        ap.error("要 --registry-root（persona-distiller-group 目录），或只跑 --self-test")
    G = pathlib.Path(a.registry_root).resolve()

    print("专家团队现状 —— 全部现算，无一句引用陈旧散文")
    print("registry-root: %s" % G)
    ver = (G / "VERSION")
    print("group VERSION: %s" % (ver.read_text(encoding="utf-8").strip() if ver.is_file() else "?"))

    # ── ③ 覆盖：车队准入与族缺口 ──────────────────────────────────────────
    section("③ 覆盖 —— 车队准入与身份族缺口")
    out = run([sys.executable, str(G / "scripts" / "audit_persona_fleet_for_team.py"),
               "--require-artifacts", "--output", "/dev/null"])
    line = [l for l in out.stdout.splitlines() if l.strip().startswith("{")]
    if line:
        d = json.loads(line[-1])
        print("  在册产物 %s 人｜准入 %s" % (d.get("registry_products"), d.get("admission_counts")))
        print("  低于底板 %s 人（底板 %s）" % (d.get("below_floor_count"), d.get("global_floor")))
        zero = d.get("zero_roster_categories") or []
        print("  **0 人的身份族：%s**" % ("、".join(zero) if zero else "无"))
        cats = d.get("admitted_category_counts") or {}
        if cats:
            lo = sorted(cats.items(), key=lambda x: x[1])[:3]
            print("  最少的三族：%s" % "、".join("%s %d" % x for x in lo))
    else:
        print("  ✗ 车队审计没有输出 JSON —— **未取到，不是「没问题」**")

    # ── ① 已证实的决策增益：在册产物有多少人有盲测 delta ────────────────
    section("① 已证实的决策增益 —— 在册产物里有多少人有盲测 delta 证据")
    out = run([sys.executable, str(HERE / "check_registered_products_have_delta_evidence.py"),
               "--registry-root", str(G), "--corpora", str(HERE.parents[1] / "_corpora")])
    keep = ("在册 ", "有：", "无：", "★★ 另有", "registration.json", "team-card.json",
            "不在册", "射程：")
    for l in out.stdout.splitlines():
        if any(k in l for k in keep):
            print("  " + l.strip())
    if out.returncode != 0:
        print("  ✗ 取不到 —— **不是「没问题」**：%s" % out.stderr.strip()[:200])
        _unmeasured.append(_current_section[0])

    # ── ①④ 记录与自优化：团队级遥测 ──────────────────────────────────────
    section("①④ 团队级 outcome 记录 —— C 层校准的前提")
    # ★★ **先说清楚「该去哪儿找」——否则这个 0 是我自己造的假 0。**
    #   实测：`record_team_outcome.py --telemetry` 是**必填、无默认值**；
    #   `route_team_moe.py` / `run_team_pipeline.py` 的 `--telemetry` 也**没有默认**。
    #   ⇒ **遥测文件没有约定的家。** 本件只能扫 group 目录，
    #     扫到 0 **不等于**「全局没有」——只等于「这里没有」。
    #   ★ 而这本身很可能就是「记录一直是 0」的一个真原因：
    #     校准层的数据没有归宿，就永远攒不起来。
    #   [[zero-hit-gates-must-prove-they-can-hit]]｜[[empty-default-swallows-unknown]]
    tel = [q for q in (list(G.rglob("*telemetry*.json*")) + list(G.rglob("*outcome*.json*")))
           if q.suffix in (".json", ".jsonl")]
    n = 0
    for q in tel:
        try:
            n += len([l for l in q.read_text(encoding="utf-8").splitlines() if l.strip()])
        except OSError:
            pass
    print("  **扫描面：只有 group 目录**（历史上 `--telemetry` 三处皆无默认值 ——")
    print("    扫到 0 不等于全局没有）")
    print("  ★ 2026-08-17 已修（group v0.0.0.17）：约定路径")
    print("    `<registry-root>/telemetry/team-outcomes.json`，写手读手共用；")
    print("    route-plan 现在印 `telemetry_path` / `telemetry_file_present`，")
    print("    「文件是空的」与「找错地方了」从此分得开。")
    print("  group 目录下：遥测文件 %d 个｜记录行数 **%d**" % (len(tel), n))
    print("  C 层校准合同要求：**>=60 条 outcome、ECE<=0.12、切片覆盖>=0.75**")
    if n == 0:
        print("  ⇒ **此处 0 条**；路由每次自报 `telemetry_eligible_for_c: false`、")
        print("    `strategy_fallback_reason: telemetry unavailable` —— 两者一致。")
        print("  ★ 「攒不起来」已修，「还没攒」照旧：路径有了，**数据仍是 0**。")
        print("    有家不等于有数据 —— 这两件事要分开说。")
    else:
        print("  ⇒ 有 %d 条，距 60 条还差 %d 条" % (n, max(0, 60 - n)))
    print("  ★ 这两个数补不上不是「没做」：`record_team_outcome.py` 必需")
    print("    `--actual-success`（实测任务成功率）与 `--delta-score`，")
    print("    要真跑一次任务并与裸模型盲比才有。**编一个就是造数据。**")

    # ── ⑤ 反伪共识：分歧检测能不能命中 ────────────────────────────────────
    section("⑤ 真正独立性 —— 分歧检测在结构上能不能命中")
    print("  检测方式：A 的 `divergence-map.md` 里**字面包含** B 的全名/slug")
    print("  （`build_team_dossier.extract_divergences`，注释写着 never surname proxies）")
    print("  ⇒ 只有**本来就互相知道的同族**才会互相点名；而路由跨族分散选人。")
    print("  2026-08-16 全库实测：可产生分歧的配对 **24 / 5151 = 0.47%**，")
    print("  24 个测试任务的队伍里含可分歧对的：**0 个（0%）**。")
    print("  ★ 这**没有**证明人物之间真的没分歧，只证明**系统没办法发现分歧**。")
    print("  ★ 2026-08-17 已披露（group v0.0.0.18/.19）：dossier 与**执行合同**")
    print("    都带 `divergence_detectability`（队伍人数／带分歧图人数／队内配对数／")
    print("    检出规则原文），合同另有 `phrasing_rules` 明令宿主：")
    print("    **空列表不许写成「专家一致」，要写「没有检出」并给出分母**。")
    print("    ⇒ **检出能力没变，但它不再冒充共识。** 要不要改成跨族也能检出，属 Owner 裁定。")

    # ── ② 路由 ────────────────────────────────────────────────────────────
    section("② 路由 —— 对着随机抽人比，以及分类器兜底率")
    if a.quick:
        print("  （--quick 跳过。完整跑：")
        print("   python3 %s --registry-root %s）" % (HERE / "measure_routing_discrimination.py", G))
    else:
        out = run([sys.executable, str(HERE / "measure_routing_discrimination.py"),
                   "--registry-root", str(G)])
        keep = ("个任务：", "离零", "兜底率", "n≥5 ·", "small_team 及以上", "正对照", "族缺口")
        for l in out.stdout.splitlines():
            if any(k in l for k in keep):
                print("  " + l.strip())

    # ── 使用过程 —— 任务包自带 oracle ────────────────────────────────────
    section("使用过程 —— 任务包自带 72 行 oracle（它自己的验收只数行数，不跑）")
    out = run([sys.executable, str(HERE / "check_benchmark_mode_accuracy.py"),
               "--registry-root", str(G), "--set", "both"])
    for l in out.stdout.splitlines():
        if any(k in l for k in ("══", "模式命中", "命中 **", "偏差", "0 次缺失",
                                "一次都没选中", "人数 oracle", "控制面")):
            print("  " + l.strip())

    # ── 上游：人物蒸馏侧那一节【硬门】有没有载体 ────────────────────────
    section("上游（persona-distiller）—— 一整节【硬门】的两条有没有载体")
    D = HERE.parents[3] / "registry" / "codex" / "persona-distiller"
    out = run([sys.executable, str(HERE / "check_rubric_independent_verification_gate.py"),
               "--skill-root", str(D), "--corpora", str(HERE.parents[1] / "_corpora")])
    keep = ("指令模板：", "实发指令：", "rubric **内部**", "一处都没有", "一道都没有",
            "易被误读", "两个不同的问题", "本件是**报告不是门**", "做得到吗")
    for l in out.stdout.splitlines():
        if any(k in l for k in keep):
            print("  " + l.strip())
    if out.returncode != 0:
        print("  ✗ 取不到 —— **不是「没问题」**：%s" % out.stderr.strip()[:200])
        _unmeasured.append(_current_section[0])

    section("这份报告不下结论")
    print("  以上全部是现算的数。**阈值、好坏、要不要改，都由 Owner 定。**")
    print("  市场状态由任务包的 `CURRENT_SCORECARD.md` 与外部 Verifier 决定，")
    print("  本件不碰。")
    # ★★★ 2026-08-17：**「取不到」印对了话，退出码却是 0**。
    #   实测（`--registry-root` 少传一级）：正文里印着「✗ 取不到 —— 不是「没问题」」
    #   外加一整段 Python 回溯，而 `rc=0` ⇒ 调用方读成通过。
    #   措辞是对的，**退出码把它抵消了**。同族已修：check_lessons_reach_the_bundle。
    #   ⇒ 有任何一节取不到 ⇒ **rc=4（未量）**，并把是哪几节列出来。
    #   [[two-checkers-same-text-different-rules]]｜[[a-refusal-to-check-prints-one-error]]
    if _unmeasured:
        print()
        print("★ **未量，不是通过**（rc=4）—— 下面这 %d 节一个数都没取到："
              % len(_unmeasured))
        for lab in _unmeasured:
            print("     · " + lab)
        print("   多半是 `--registry-root` 指错了：它要指向 "
              "**persona-distiller-group 目录本身**。")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
