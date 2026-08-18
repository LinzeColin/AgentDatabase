#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""准入那道门（Expert Choice）必须**至少有一个信号真的随任务变** —— 否则它拦不住任何人。

`route_team_moe.score_candidate` 末尾那行：

    # Expert Choice: the expert declines tasks outside its demonstrated competence.
    if max(task_similarity, packet_similarity, capabilities, scenarios, domain_match) < accept_threshold:
        return ... "expert-choice compatibility below threshold"

注释说的是「专家拒接**不在其能力范围内的任务**」。`max(...)` 意味着
**任何一项过线就够**。⇒ 只要其中有一项**与任务无关**，这道门对相当一部分人就形同虚设。

## 2026-08-18 实测到的事（本件的由来）

`packet_similarity = max(overlap_score(packet["objective"], 候选人卡片))`，
而 `compile_task_graph` 生成的 `work_packets` 的 `objective` 是**固定套话**：

    把用户目标编译为交付物、约束、成功条件和停止条件。
    建立事实、来源、未知、当前性和证据缺口地图。
    在人物能力与边界内形成可执行解决方案。
    …

**五道内容毫不相干的题**（遗留微服务重构／40 公顷农场轮作／医院灭菌安全论证／
供应商合同谈判／一串无意义词），14 条 objective 的 sha256 **完全相同**
⇒ 102 人的 `packet_similarity` 读数 **一个都不变**（本件 ① 每次现算复核）。

后果（本件 ② 现算）：**过了准入的人里，很大一部分是「其余四项全部低于门、
单靠这一项过线」** —— 也就是**没有任何与本任务有关的证据**却被判为「能接」。

★ 本件**不要求它变绿**。变绿要改 `packet_similarity` 的定义或把它移出 `max(...)`，
  那会移动每一道真实任务选出的人 —— 属「门、席位一概不动」，要 Owner 定（Task #135）。
  本件钉的是「**不许比现在更依赖这条任务无关的通道**」，外加钉住那句注释还在。
  [[a-rule-in-a-doc-has-no-enforcer]]｜[[zero-hit-gates-must-prove-they-can-hit]]

## 非退化守卫（判据不能自己空转）

- **正对照**：`task_similarity` 必须在这几道探针题之间**真的变**。
  它不变 ⇒ 是**我的探针死了**（读错卡片、图没编译…），不是产品的结论 ⇒ **rc=4 未量**。
  ★ 今天已第 6 次「自己写的抽取器扫描面为空」：第一版我拿 `load_admission()` 当卡片源，
    `candidate_text` 只捞到 32 字，102 人读数**全 0**，差点写成「恒 0」。
    [[a-gates-scan-set-is-smaller-than-reality]]
- **样本量绑定**：基线是在默认样本量上测的；传了 `--limit` 就**不适用** ⇒ rc=4。
  [[baseline-must-be-the-same-kind-as-what-you-compare]]
- 候选人数 < `MIN_CANDIDATES` ⇒ rc=4。

用法：

    python3 check_admission_signal_depends_on_the_task.py
    python3 check_admission_signal_depends_on_the_task.py --baseline-sole-share 0.01   # 看它红不红得了
    python3 check_admission_signal_depends_on_the_task.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

# ── 基线（2026-08-18 实测，默认样本量）─────────────────────────────────────
# 「唯一靠任务无关信号进来」的人数 ÷ 过准入人数，按 **策略 B 门 0.17**（auto 的实际取值）。
BASELINE_SOLE_SHARE = 0.63      # 实测均值 0.6282（24 条样本、策略 B）——地板贴着实测值
BASELINE_LIMIT = 24             # 基线绑定的样本量
MIN_CANDIDATES = 10
MIN_TASKS = 4

# ── ① 不变性探针：五道**内容毫不相干**的题 ────────────────────────────────
# ★ 这几条是我写的，但它们只用来**找差异**：写得越不一样，越容易证伪「不变」。
#   真正的护栏是下面的正对照 —— `task_similarity` 必须在它们之间变。
PROBES = (
    "为一个遗留微服务代码库设计测试策略与重构方案",
    "为一个 40 公顷的再生农场规划轮作",
    "Review the safety case for a new hospital sterilization protocol",
    "与一个难缠的供应商谈供货合同",
    "zzq0 zzq1 zzq2 zzq3 zzq4 zzq5 zzq6 zzq7 zzq8 zzq9",
)
COMPONENTS = ("task_similarity", "packet_similarity", "capability_match", "scenario_match", "domain_match")
# ★ 键名以 `values` 字典为准 —— 准入那行用的是局部变量 `capabilities`/`scenarios`，
#   而存进 `values` 时叫 `capability_match`/`scenario_match`。写错就恒读 0.0（我第一版如此）。
# ★★ 一律 round 到 **4 位**：接受路径 return 时 `round(v, 4)`，拒绝路径原样返回 ⇒
#   同一个数两种精度，不归一就会把 15 个人误判成「跨题会动」。
CONTRACT_LINE = "Expert Choice: the expert declines tasks outside its demonstrated competence."


def _load():
    sys.path.insert(0, str(HERE))
    import route_team_moe as R                      # noqa: E402
    from compile_task_graph import compile_graph    # noqa: E402
    root = R.default_registry_root()
    cards = R.read_json(root / "team-index.json").get("products", [])
    return R, compile_graph, root, cards


def objective_signature(compile_graph, task: str) -> str:
    """一道题编出来的 work_packet **objective 全集**的指纹。"""
    g = compile_graph(task, "deep_team", 14)
    blob = "\n".join(str(p.get("objective")) for p in g["work_packets"])
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def invariant_components(R, compile_graph, cards, tasks, strategy="B"):
    """→ (每个分量跨题**没变过**的人数, 每人每题的读数表)。"""
    import route_team_moe as _R  # noqa: F401
    root = R.default_registry_root()
    adm, tel = R.load_admission(root), R.load_telemetry(None)
    table = {}   # task -> slug -> {component: value}
    for t in tasks:
        g = compile_graph(t, "deep_team", 14)
        row = {}
        for c in cards:
            _, bd, _ = R.score_candidate(c, g, strategy, tel, adm)
            v = bd.get("values", {})
            row[c.get("subject_slug")] = {k: round(float(v.get(k, 0.0)), 4) for k in COMPONENTS}
        table[t] = row
    frozen = {}
    slugs = sorted(table[tasks[0]])
    for comp in COMPONENTS:
        same = sum(1 for s in slugs
                   if len({table[t][s][comp] for t in tasks}) == 1)
        frozen[comp] = same
    return frozen, table, slugs


def sole_admitter_share(table, slugs, tasks, frozen_comps, threshold):
    """过准入的人里，**只靠任务无关分量**过线的占比（按题取平均，并给最坏那题）。"""
    per_task = []
    for t in tasks:
        adm_n = sole = 0
        for s in slugs:
            v = table[t][s]
            if max(v.values()) < threshold:
                continue
            adm_n += 1
            live = [v[k] for k in COMPONENTS if k not in frozen_comps]
            if max(live, default=0.0) < threshold:
                sole += 1
        if adm_n:
            per_task.append((sole / adm_n, sole, adm_n, t))
    return per_task


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("   %s %s" % ("✓" if cond else "✗", name))
        ok = ok and bool(cond)

    R, compile_graph, root, cards = _load()
    chk("① 名册取自 team-index.json 的 products（**不是** load_admission）", len(cards) >= MIN_CANDIDATES)
    med = sorted(len(R.candidate_text(c)) for c in cards)[len(cards) // 2]
    chk("①b ★ 扫描面非空：candidate_text 中位 >200 字（错路只有 32 字）—— 现测 %d" % med, med > 200)

    sigs = {objective_signature(compile_graph, t) for t in PROBES}
    chk("② 五道探针题的 work_packet objective 指纹数 == 1（现测 %d）" % len(sigs), len(sigs) == 1)

    frozen, table, slugs = invariant_components(R, compile_graph, cards, list(PROBES))
    chk("③ ★正对照：task_similarity **必须**跨题变 —— 不变的人 %d/%d，要求 < 全体"
        % (frozen["task_similarity"], len(slugs)), frozen["task_similarity"] < len(slugs))
    chk("④ packet_similarity 跨题**一个人都没变**（现测不变 %d/%d）"
        % (frozen["packet_similarity"], len(slugs)), frozen["packet_similarity"] == len(slugs))

    fz = {k for k, n in frozen.items() if n == len(slugs)}
    per = sole_admitter_share(table, slugs, list(PROBES), fz, 0.17)
    chk("⑤ 「唯一靠任务无关项进来」在探针题上 > 0（否则本件无的放矢）",
        per and max(p[0] for p in per) > 0)

    # 反例：把冻结集合清空 ⇒ 占比必须掉到 0（证明这个数确实由「冻结」驱动）
    per0 = sole_admitter_share(table, slugs, list(PROBES), set(), 0.17)
    chk("⑥ ★反例：冻结集合置空 ⇒ 占比必须全为 0（现测最大 %.4f）"
        % max([p[0] for p in per0] or [0]), all(p[0] == 0 for p in per0))

    txt = (HERE / "route_team_moe.py").read_text(encoding="utf-8")
    chk("⑦ 被钉住的那句注释还在 route_team_moe.py 里", CONTRACT_LINE in txt)
    chk("⑧ 地板可达：0 < BASELINE_SOLE_SHARE < 1", 0.0 < BASELINE_SOLE_SHARE < 1.0)
    chk("⑨ 基线记着它自己的样本量", BASELINE_LIMIT > 0)
    print("   —— self-test %s ——" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="准入门必须至少有一个信号随任务变")
    ap.add_argument("--limit", type=int, default=BASELINE_LIMIT)
    ap.add_argument("--baseline-sole-share", type=float, default=None)
    ap.add_argument("--tasks", default=None, metavar="文件",
                    help="外部任务集（每行一条或 JSON 数组）。★ 用了它，下面的射程话不适用。")
    ap.add_argument("--strategy", default="B", choices=["A", "B", "C"])
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    floor = BASELINE_SOLE_SHARE if a.baseline_sole_share is None else a.baseline_sole_share
    explicit_floor = a.baseline_sole_share is not None
    if a.limit != BASELINE_LIMIT and not explicit_floor:
        print("★ **未量，不是通过**（rc=4）—— 基线 %.2f 是在样本量 %d 上测的，"
              "你换成了 %d 却没给新地板。" % (BASELINE_SOLE_SHARE, BASELINE_LIMIT, a.limit))
        return 4

    R, compile_graph, root, cards = _load()
    if len(cards) < MIN_CANDIDATES:
        print("★ **未量，不是通过**（rc=4）—— 候选只有 %d 人" % len(cards))
        return 4

    src = "产物自带的 `application_scenarios`（**标签，不是用户提问**）"
    if a.tasks:
        tp = pathlib.Path(a.tasks)
        if not tp.is_file():
            print("★ **未量，不是通过**（rc=4）—— 任务集文件不在：%s" % tp)
            return 4
        raw = tp.read_text(encoding="utf-8")
        try:
            tasks = [str(x) for x in json.loads(raw) if str(x).strip()]
        except ValueError:
            tasks = [ln.strip() for ln in raw.splitlines() if ln.strip()
                     and not ln.lstrip().startswith("#")]
        src = "外部任务集 `%s`" % tp.name
    else:
        sys.path.insert(0, str(HERE))
        from check_mode_ladder_reachable import sample_tasks
        tasks = sample_tasks(root / "team-index.json", a.limit)
    tasks = [t for t in tasks[:a.limit] if str(t).strip()]
    if len(tasks) < MIN_TASKS:
        print("★ **未量，不是通过**（rc=4）—— 只取到 %d 条任务" % len(tasks))
        return 4

    threshold = 0.13 if a.strategy == "A" else 0.17
    print("候选 **%d** 人；样本 **%d** 条，来自%s；策略 %s，准入门 **%.2f**"
          % (len(cards), len(tasks), src, a.strategy, threshold))

    sigs = {objective_signature(compile_graph, t) for t in PROBES}
    print("\n① 机制：五道**内容毫不相干**的探针题，work_packet objective 指纹 **%d** 种"
          % len(sigs) + ("（**同一份套话**）" if len(sigs) == 1 else ""))
    frozen, ptable, pslugs = invariant_components(R, compile_graph, cards, list(PROBES), a.strategy)
    if frozen["task_similarity"] >= len(pslugs):
        print("★ **未量，不是通过**（rc=4）—— **正对照没过**：task_similarity 跨题也不变 ⇒ "
              "是我的探针死了，不是产品的结论。")
        return 4
    for comp in COMPONENTS:
        flag = "  ← **与任务无关**" if frozen[comp] == len(pslugs) else ""
        print("   %-18s 跨 5 题读数没变过的人：**%3d**/%d%s" % (comp, frozen[comp], len(pslugs), flag))
    fz = {k for k, n in frozen.items() if n == len(pslugs)}
    if not fz:
        print("\n✓ 没有任何分量是任务无关的 ⇒ 本件无事可判（rc=0）")
        return 0

    _, table, slugs = invariant_components(R, compile_graph, cards, tasks, a.strategy)
    per = sole_admitter_share(table, slugs, tasks, fz, threshold)
    if not per:
        print("★ **未量，不是通过**（rc=4）—— 没有一道题有人过准入")
        return 4
    shares = [p[0] for p in per]
    avg, worst = sum(shares) / len(shares), max(per)
    print("\n② 规模：过准入的人里，**其余分量全部低于门、唯一靠 %s 过线**的占比"
          % "／".join(sorted(fz)))
    print("   均值 **%.1f%%**；最坏一题 **%.1f%%**（%d/%d 人）：%s"
          % (100 * avg, 100 * worst[0], worst[1], worst[2], str(worst[3])[:38]))
    print("   ★ 这些人**没有任何与本题有关的证据**，却被判为「能接」。")
    print("   ★★ 射程：占比依赖样本；换成真实用户提问会不会变 —— **没量过**。")

    print()
    if avg > floor:
        print("✗ **比基线更依赖那条任务无关的通道**：均值 %.4f > 地板 %.4f" % (avg, floor))
        return 1
    print("✓ 未超基线：均值 %.4f ≤ 地板 %.4f（**不代表这道门是好的** —— 见 Task #135）"
          % (avg, floor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
