#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路由到底有没有分辨力 —— **对着随机抽人比一次**。

为什么要有这份文件
------------------
2026-08-15 Owner 的评价：「路由、覆盖、记录、自优化迭代、有效激活调用、命中率
**都没有实质性收益和效果**」。任务包自己的验收是 PASS 的 —— 它验的是
「链路跑得通」，不是「选对了人」。**两件不同的事。**

实测触发：给「小团队项目管理 SaaS 该按人头月付还是按项目计费」跑真实入口，
`small_team` 选出 9 人，里面有**焊接裂纹与失效机理**专家、**压力设备与管道**
专家、两个**编程语言设计者**。而分数带是：

    入选 9 人 base_score  0.1375 – 0.2060（σ=0.0228）
    排除 61 人 base_score  0.0000 – 0.1989
    ⇒ **入选最低 < 排除最高，两个区间重叠**

## 这份判据回答的那一个问题

**路由选出的队伍，含相关身份族的比例，比「从同一个可选池里按同样人数随机抽」
高多少？** 高不了就是没有分辨力 —— 无论链路多完整。

## 它怎么不作弊

★ **相关族是按任务文本预先标的，与路由器用的字段无关**（路由器用
  `application_scenarios`／`key_capabilities`／`base_score`；本件只用
  `registration_category`）。不拿路由器自己的信号当答案。
★ **随机基线从真实可选池抽，带着池子本身的族偏斜**（软件开发师 34、
  投资资本师 21、材料建工师 15……）。拿均匀分布当 null 会把偏斜算成本事。
  [[negative-control-must-not-share-the-assumption]]
★ **正对照**：内置一个「答案明显」的任务（写 Python API 的可读性），
  若连它都不比随机高，那是本件的尺子坏了，不是产品坏了。
★ 随机基线用**固定种子**，可复算。

## 它答不了什么（必须一起念）

1. 它**不判最终答案对不对** —— 那要盲测，要两个互相独立的会话。
   本件只量路由这一层。[[bibliographic-proxy-instead-of-the-measurement]]
2. 族相关性是**我标的**。标签逐条写在 TASKS 里，可以被推翻；
   推翻它就推翻本件的结论。[[self-report-is-not-evidence]]
3. 「随机抽也差不多」**不等于人物无用** —— 只等于**这一层的选择没有增益**。

用法
----
    python3 measure_routing_discrimination.py --self-test
    python3 measure_routing_discrimination.py --registry-root <group 目录>
    python3 measure_routing_discrimination.py --registry-root <...> --trials 500
"""
import argparse
import json
import pathlib
import random
import statistics
import subprocess
import sys

# ── 任务集：`relevant` 是**按任务文本标的**，与路由器用的字段无关 ──────────
#   每条都写清「为什么这几族相关」，让它可以被逐条反驳。
TASKS = [
    {
        "id": "pricing-saas",
        "task": "我们要给一款面向小团队的项目管理 SaaS 定价，"
                "现在有按人头月付和按项目数计费两种方案，选哪个？",
        "relevant": ["创业经营师", "客户营销师", "财务合规师", "投资资本师"],
        "why": "定价 = 商业模式（创业经营）＋ 获客与包装（客户营销）＋ "
               "收入确认与合规（财务合规）＋ 单位经济与回报（投资资本）。",
    },
    {
        "id": "api-readability",
        "task": "我们的 Python SDK 有 40 个公开函数，命名和参数顺序很不一致，"
                "要怎么重新设计才让人一看就会用？",
        "relevant": ["软件开发师", "艺术设计师"],
        "why": "★ **正对照**：API 可读性设计是软件开发师的正题；"
               "「让人一看就会用」把设计师也拉进来。这一条若不比随机高，"
               "是尺子坏了。",
    },
    {
        "id": "steel-weld-failure",
        "task": "一批压力容器的焊缝在服役 8 个月后出现裂纹，"
                "要判断是材料、工艺还是设计的问题，怎么查？",
        "relevant": ["材料建工师", "建造采购师"],
        "why": "焊缝失效机理与压力设备评价，正是材料建工与建造采购的正题。",
    },
    {
        "id": "clinical-triage",
        "task": "县医院急诊分诊流程要重做，怎么在护士人手不足的情况下"
                "既不漏掉重症又不让轻症等太久？",
        "relevant": ["医疗护理师"],
        "why": "★ 这一条**注定命中 0** —— 名册里医疗护理师是 0 人。"
               "留着它是为了让「族缺口」在数字上现形，不是为了凑分。",
    },
    {
        "id": "land-lease-dispute",
        "task": "一块租了 20 年的农地，出租方现在要提前收回，"
                "合同里没写提前解约条款，我们该怎么谈？",
        "relevant": ["政治法律师", "农林牧渔师"],
        "why": "合同争议与谈判（政治法律）＋ 农地经营实务（农林牧渔）。",
    },
    {
        "id": "factory-layout",
        "task": "新车间要排产线，工位怎么摆能让在制品最少、换型最快？",
        "relevant": ["建造采购师", "创业经营师", "材料建工师"],
        "why": "厂房与工位布置（建造采购）＋ 生产组织（创业经营）＋ 工艺约束（材料建工）。",
    },
    # ── 2026-08-16 补到 18 条 ──────────────────────────────────────────────
    #   前 6 条给出 +4.0 pp / SE 3.5 / **离零 1.16 SE**，本件自己算出
    #   「要达到 2 SE 需要约 18 个任务」。补的这 12 条**在看任何路由结果之前
    #   就写好了标签与理由** —— 先写标签、后跑路由，顺序不能反，否则就是
    #   拿结果去凑标签。[[i-create-the-leak-channels-myself]]
    #   ★ 12 族各有覆盖，且**故意保留两条注定命中低的**（医疗护理师 0 人、
    #     客户营销师 1 人），不为了让平均值好看而挑题。
    {
        "id": "code-review-culture",
        "task": "团队 30 个人，代码评审经常拖三天没人看，怎么改？",
        "relevant": ["软件开发师", "创业经营师"],
        "why": "评审实践（软件开发）＋ 团队流程与激励（创业经营）。",
    },
    {
        "id": "portfolio-drawdown",
        "task": "组合今年回撤 22%，该止损离场还是加仓摊平？",
        "relevant": ["投资资本师", "财务合规师"],
        "why": "回撤与仓位（投资资本）＋ 风险披露与合规约束（财务合规）。",
    },
    {
        "id": "brand-relaunch",
        "task": "一个做了 15 年的老品牌要面向年轻人重做，从哪儿下手？",
        "relevant": ["客户营销师", "艺术设计师", "创业经营师"],
        "why": "定位与叙事（客户营销）＋ 视觉与体验（艺术设计）＋ 商业模式（创业经营）。",
    },
    {
        "id": "curriculum-design",
        "task": "小学三年级的科学课要重编，怎么让孩子自己提出问题而不是背结论？",
        "relevant": ["思想教育师"],
        "why": "探究式教学与认知发展，是思想教育师的正题。",
    },
    {
        "id": "bridge-inspection",
        "task": "一座 40 年的钢桥要做延寿评估，先查哪些部位、按什么判废？",
        "relevant": ["材料建工师", "建造采购师"],
        "why": "疲劳与失效评估（材料建工）＋ 结构检测与工程决策（建造采购）。",
    },
    {
        "id": "audit-disagreement",
        "task": "审计师认为一笔收入不能在本季确认，业务方坚持要确认，怎么处理？",
        "relevant": ["财务合规师", "政治法律师"],
        "why": "收入确认准则（财务合规）＋ 争议处理与责任边界（政治法律）。",
    },
    {
        "id": "orchard-disease",
        "task": "果园连续两年在同一片区烂根，是病害、涝还是砧木问题，怎么分辨？",
        "relevant": ["农林牧渔师"],
        "why": "田间诊断与栽培，是农林牧渔师的正题。",
    },
    {
        "id": "db-migration-risk",
        "task": "要把一个跑了八年的单体数据库拆成三个服务，怎么排风险和回退？",
        "relevant": ["软件开发师", "建造采购师"],
        "why": "系统拆分与回退（软件开发）＋ 分阶段实施与依赖排程（建造采购）。",
    },
    {
        "id": "clinic-staffing",
        "task": "社区诊所夜班只有一名护士，怎么排班既安全又不让人熬垮？",
        "relevant": ["医疗护理师"],
        "why": "★ 第二条**注定命中 0** 的题（名册里医疗护理师 0 人）。"
               "保留它是为了让族缺口在 18 条里按真实比例现形，不是为了压低平均值。",
    },
    {
        "id": "constitutional-challenge",
        "task": "一条新出的地方规章可能越权，要不要提起复议，胜算怎么估？",
        "relevant": ["政治法律师"],
        "why": "行政法与诉讼策略，是政治法律师的正题。",
    },
    {
        "id": "typography-system",
        "task": "产品有 40 个页面，字号和行距各写各的，怎么定一套用得下去的规范？",
        "relevant": ["艺术设计师", "软件开发师"],
        "why": "排版系统（艺术设计）＋ 落地为可执行的设计令牌（软件开发）。",
    },
    {
        "id": "supplier-single-source",
        "task": "一个关键件只有一家供应商，涨价 30% 还交期不稳，怎么办？",
        "relevant": ["建造采购师", "创业经营师", "财务合规师"],
        "why": "供应商策略（建造采购）＋ 议价与替代方案（创业经营）＋ 成本影响（财务合规）。",
    },
    # ── 2026-08-16 第二次补，18 → 24 ────────────────────────────────────────
    #   18 条给出 +11.7 pp / SE 6.5 / **离零 1.80 SE**，本件算出还需约 23 个。
    #   ★★ 这 6 条**有意偏向「相关族常见」那一侧**（软件开发师 34/101、
    #     投资资本师 21、材料建工师 15 —— 随机基线本来就高，路由更难赢）。
    #     分层结果已显示常见族只有 +7.5 pp，**往这边加题是把测试变难，不是变易**。
    #     若挑稀有族题（那边 +22.5 pp）就是拿题去凑结论。
    #   标签同样在跑任何路由之前写好。
    {
        "id": "flaky-test-suite",
        "task": "CI 里有 200 个测试，每次都有三五个随机失败，重跑就过，怎么根治？",
        "relevant": ["软件开发师"],
        "why": "测试稳定性与工程规范，纯软件开发师题（随机基线约 34%，难赢）。",
    },
    {
        "id": "hedge-currency-exposure",
        "task": "海外收入占四成，汇率一年波动 12%，要不要做对冲、做多少？",
        "relevant": ["投资资本师", "财务合规师"],
        "why": "对冲比例与成本（投资资本）＋ 套保会计与披露（财务合规）；两族合计 23/101。",
    },
    {
        "id": "heat-treatment-spec",
        "task": "一批合金钢件热处理后硬度不均，是炉温、装炉方式还是材料批次问题？",
        "relevant": ["材料建工师"],
        "why": "热处理工艺与失效分析，纯材料建工师题（该族 15/101）。",
    },
    {
        "id": "legacy-refactor-budget",
        "task": "老系统重构要 6 个月，业务方只批 2 个月，怎么切分才不半途而废？",
        "relevant": ["软件开发师", "创业经营师", "建造采购师"],
        "why": "增量重构（软件开发）＋ 范围谈判（创业经营）＋ 分阶段交付（建造采购）；三族合计 53/101，**随机基线极高**。",
    },
    {
        "id": "founder-equity-split",
        "task": "三个联合创始人贡献差别很大，股权怎么分才不在第二年吵翻？",
        "relevant": ["创业经营师", "财务合规师", "政治法律师"],
        "why": "创始人治理（创业经营）＋ 股权与税务（财务合规）＋ 协议与争议预防（政治法律）。",
    },
    {
        "id": "warehouse-automation-roi",
        "task": "仓库要不要上自动分拣，投入 800 万，三年能不能回本？",
        "relevant": ["建造采购师", "投资资本师", "创业经营师"],
        "why": "设备选型与实施（建造采购）＋ 回报测算（投资资本）＋ 运营改造（创业经营）；三族合计 40/101。",
    },
]

DEFAULT_TRIALS = 400
SEED = 20260815


def run_router(registry_root, task, mode="auto"):
    """→ (选中成员的 registration_category 列表, 可选池大小, route-plan)。"""
    script = pathlib.Path(registry_root) / "scripts" / "route_team_moe.py"
    out = subprocess.run(
        [sys.executable, str(script), "--task", task,
         "--mode", mode, "--registry-root", str(registry_root)],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("route_team_moe 失败 rc=%d：%s" % (out.returncode, out.stderr[:300]))
    plan = json.loads(out.stdout[out.stdout.find("{"):])
    cats = [m.get("registration_category") for m in plan.get("members", [])]
    obs = plan.get("routing_observability") or {}
    return cats, obs.get("eligible_candidates"), plan


class MissingRegistry(Exception):
    """输入缺失 —— **未量**，与「量了但不达标」分开。退出码 4。"""


def eligible_pool_categories(registry_root):
    """随机基线的池子 —— **全部车队准入者（101 人）**，带着池子本身的族偏斜。

    ★★ **为什么用 101，而不用 route-plan 里那个 `eligible_candidates`？**

    route-plan 每题印的 `eligible_candidates` 是**逐任务的**（实测 61 / 58 / 43），
    因为路由在车队准入之上还加了一道 `expert-choice compatibility threshold`。
    实测 `eligible + excluded = 102`（整个名册），二者互为补集。

      · 用 **101（全部准入者）** 当 null ⇒ 问的是「路由**整条栈**
        （准入 + 兼容阈值 + 排序）比随机抽好多少」——**这是对的问题**。
      · 若改用「本题通过兼容阈值的那 61 人」当 null ⇒ 等于**把路由自己的
        过滤白送给基线**，会**高估**路由。

    ★★★ 而且那个窄 null **根本重建不出来**：route-plan 只列**被排除的**
      那 41 个的名字，**没有列「eligible 但未入选」的 52 个**。
      2026-08-17 我试过拿「入选 9 + 被排除 41 = 50 人」当窄池子，
      得到 n≥5 **+23.8 pp / 8.25 SE** —— **那是假的**：
      它把 9 个高相关的人混进 41 个低相关的人里当基线，
      基线被人为压到 9.7%（宽 null 是 29.9%），差值自然虚高。**已撤回。**
      [[a-gates-scan-set-is-smaller-than-reality]]｜[[negative-control-must-not-share-the-assumption]]
    """
    admission = pathlib.Path(registry_root) / "expert-fleet-admission.json"
    # ★★★ 2026-08-17：传错目录时**不许抛栈**。实测：`--registry-root` 指到
    #   `registry/codex`（少一级）会得到一个 `FileNotFoundError` 回溯 ——
    #   读的人看到的是 Python 栈，不是「哪里错了、该怎么办」。
    #   这正是 Owner 说的「使用过程有显著性故障和阻碍点」。
    #   ⇒ 换成一条能照着做的话，并用**未量码 4**（不是 0，也不是 1）。
    #   [[error-message-points-at-an-exit-that-isnt-there]]
    if not admission.is_file():
        _hint = pathlib.Path(registry_root) / "persona-distiller-group"
        raise MissingRegistry(
            "★ **未量，不是通过** —— 找不到 %s\n"
            "   `--registry-root` 要指向 **persona-distiller-group 目录本身**"
            "（那里面有 `expert-fleet-admission.json` 和 `scripts/route_team_moe.py`）。\n"
            "   %s" % (admission,
                       ("看着你想要的是：%s" % _hint) if (_hint / "expert-fleet-admission.json").is_file()
                       else "本机没找到候选目录；先确认这个仓里有没有 persona-distiller-group。"))
    d = json.loads(admission.read_text(encoding="utf-8"))
    rows = d if isinstance(d, list) else None
    if rows is None:
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                rows = v
                break
    rows = rows or []
    ok = [r for r in rows if str(r.get("admission")) == "eligible"]
    return [r.get("registration_category") for r in ok]


def hit_rate(cats, relevant):
    if not cats:
        return 0.0
    return sum(1 for c in cats if c in relevant) / len(cats)


def random_baseline(pool, k, relevant, trials, rng):
    """从**真实可选池**抽 k 人（不放回），重复 trials 次。"""
    if len(pool) < k:
        return None, None
    xs = []
    for _ in range(trials):
        xs.append(hit_rate(rng.sample(pool, k), relevant))
    return statistics.mean(xs), statistics.pstdev(xs)


def selftest():
    bad = []
    rng = random.Random(SEED)
    pool = ["A"] * 30 + ["B"] * 30 + ["C"] * 40

    # ① 全命中 / 全不命中 / 一半
    for cats, rel, want in [(["A", "A"], ["A"], 1.0), (["B", "C"], ["A"], 0.0),
                            (["A", "B"], ["A"], 0.5), ([], ["A"], 0.0)]:
        got = hit_rate(cats, rel)
        if abs(got - want) > 1e-9:
            bad.append("hit_rate(%s,%s) 期望 %.2f 得 %.2f" % (cats, rel, want, got))

    # ② 随机基线要贴近池子里该族的占比 —— 抽 10 人、A 占 30% ⇒ 均值≈0.30
    mean, _ = random_baseline(pool, 10, ["A"], 2000, rng)
    if not (0.27 <= mean <= 0.33):
        bad.append("随机基线偏了：抽 10 人 A 命中率均值 %.4f，池中 A 占 0.30" % mean)

    # ③ ★ 负对照：**基线必须带池子的偏斜**。若拿均匀分布当 null，
    #    抽 C（占 40%）会被算成 1/3 而不是 0.40 —— 那样偏斜会被记成本事。
    meanC, _ = random_baseline(pool, 10, ["C"], 2000, rng)
    if not (0.37 <= meanC <= 0.43):
        bad.append("★ 基线没带偏斜：C 占 0.40 而基线给 %.4f" % meanC)
    if abs(meanC - mean) < 0.05:
        bad.append("★ 基线对不同占比的族给了几乎一样的数 —— 它没在看池子")

    # ④ 池子比队伍还小时明说不可算，不许悄悄返回 0
    m, _ = random_baseline(["A"] * 3, 5, ["A"], 10, rng)
    if m is not None:
        bad.append("池子(3) < 队伍(5) 时应返回 None，实得 %r" % m)

    # ── ★★★ 2026-08-17：输入缺失时**不许抛栈**，要给一条能照着做的话 ──
    #   实测事故：`--registry-root` 指到 `registry/codex`（少一级）⇒ 一个
    #   `FileNotFoundError` 回溯。读的人看到的是 Python 栈，不是「该怎么办」。
    import tempfile as _tf, subprocess as _sp
    _self = str(pathlib.Path(__file__).resolve())
    with _tf.TemporaryDirectory() as _td:
        _empty = pathlib.Path(_td)
        try:
            eligible_pool_categories(_empty)
            bad.append("★★★ 目录里没有 expert-fleet-admission.json，却没有抛 MissingRegistry")
        except MissingRegistry as _e:
            _m = str(_e)
            if "未量，不是通过" not in _m:
                bad.append("★★★ 缺输入的提示里没有「未量，不是通过」")
            if "--registry-root" not in _m:
                bad.append("★★★ 缺输入的提示里没告诉人该改哪个参数")
        except FileNotFoundError:
            bad.append("★★★ **还在抛 FileNotFoundError** —— 缺输入必须变成可读的一句话")
        # ★ 真跑一次子进程：退出码必须是 **4（未量）**，不是 0 也不是 1
        _r = _sp.run([sys.executable, _self, "--registry-root", str(_empty)],
                     capture_output=True, text=True)
        if _r.returncode != 4:
            bad.append("★★★ 缺输入时退出码 %d，应为 **4（未量）**" % _r.returncode)
        if "Traceback" in (_r.stdout + _r.stderr):
            bad.append("★★★ 缺输入时**仍然印出了回溯**")
    for b in bad:
        print("  ✗ " + b)
    n = 4 + 3 + 1 + 5      # ★ +5：2026-08-17「输入缺失不抛栈」那一组
    print("自测 %d/%d" % (n - len(bad), n))
    return 1 if bad else 0


SCORE_WEIGHTS = {
    "task_similarity": 0.24, "packet_similarity": 0.15, "domain_match": 0.15,
    "scenario_match": 0.10, "capability_match": 0.14, "user_value_match": 0.07,
    "evidence": 0.05, "boundary": 0.04, "currentness": 0.06,
}


def variance_contribution(seat_values):
    """Which component actually drives the ranking? **Weight alone is misleading.**

    `task_similarity` carries the largest weight (0.24) while `domain_match`
    carries 0.15 -- so the formula reads as if similarity dominates. It does
    not. A component only moves the ordering to the extent it *varies* across
    candidates, so the driver is `weight x sigma`, not `weight`.

    Measured 2026-08-17 over 22 selected seats / 6 tasks:

        domain_match       w=0.15  sigma=0.2989  w*sigma=0.0448  **49.0%**
        packet_similarity  w=0.15  sigma=0.0964  w*sigma=0.0145    15.8%
        task_similarity    w=0.24  sigma=0.0527  w*sigma=0.0126    13.8%

    ★★ This matters beyond curiosity. `domain_match` is computed **entirely
    from a hand-written keyword list** (`compile_task_graph.DOMAIN_SIGNALS`),
    and the task pack's own `moe-routing-contract.md` says, under the A layer:

        "A 保持旧类别和场景匹配，只用于兼容。人工关键词不得成为冠军路由的主要证据。"

    Half the ranking signal in the B layer therefore comes from the mechanism
    the contract designates as compatibility-only. The measured routing gain
    (n>=5: +6.3 pp) rests on it. **Report the caveat alongside the number.**

    The contract's intended champion evidence is C-layer outcome telemetry --
    which has never accumulated a single record. Hand keywords dominate
    *because* C never turned on, not because anyone chose them as champion.
    """
    rows = []
    for key, weight in SCORE_WEIGHTS.items():
        xs = seat_values.get(key) or [0.0]
        sd = statistics.pstdev(xs) if len(xs) > 1 else 0.0
        rows.append((weight * sd, key, weight, sd))
    total = sum(r[0] for r in rows) or 1.0
    return sorted(rows, reverse=True), total


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry-root")
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.registry_root:
        ap.error("要 --registry-root（persona-distiller-group 目录），或只跑 --self-test")

    root = pathlib.Path(a.registry_root).resolve()
    try:
        pool = eligible_pool_categories(root)
    except MissingRegistry as exc:                                # noqa: PERF203
        print(str(exc), file=sys.stderr)
        return 4
    rng = random.Random(SEED)
    print("可选池 %d 人；随机基线 %d 次（seed=%d，**从真实池按其族偏斜抽**）\n"
          % (len(pool), a.trials, SEED))

    rows = []
    for t in TASKS:
        cats, n_elig, plan = run_router(root, t["task"])
        routed = hit_rate(cats, t["relevant"])
        base, sd = random_baseline(pool, len(cats), t["relevant"], a.trials, rng)
        rows.append({
            "id": t["id"], "team_size": len(cats),
            "routed_hit": routed, "random_hit": base, "random_sd": sd,
            "delta": None if base is None else routed - base,
            "mode": plan.get("mode"), "strategy": plan.get("strategy"),
            "relevant": t["relevant"], "picked": cats,
            "_breakdowns": [m["score_breakdown"] for m in plan.get("members", [])
                            if isinstance(m.get("score_breakdown"), dict)],
            "_dm_all_zero": all(
                (m.get("score_breakdown") or {}).get("values", {}).get("domain_match", 0) == 0
                for m in plan.get("members", [])) if plan.get("members") else None,
        })

    print("%-20s %5s  %8s  %8s  %9s  %s" % ("任务", "人数", "路由命中", "随机命中", "差值", "模式/策略"))
    for r in rows:
        d = r["delta"]
        print("%-20s %5d  %7.1f%%  %7.1f%%  %+8.1f%%  %s/%s"
              % (r["id"], r["team_size"], 100 * r["routed_hit"], 100 * r["random_hit"],
                 100 * d, r["mode"], r["strategy"]))

    deltas = [r["delta"] for r in rows if r["delta"] is not None]
    mean_d = statistics.mean(deltas)
    wins = sum(1 for d in deltas if d > 0)
    print("\n  %d 个任务：路由高于随机 **%d** 个、低于 %d 个、平均差值 %+.1f 个百分点"
          % (len(deltas), wins, sum(1 for d in deltas if d < 0), 100 * mean_d))

    # ★★ **报均值必须连它离零几个 SE 一起报。** 本项目已栽过：
    #   +0.0291 被当成正收益，实际门落在它的不确定区间里；
    #   +0.00265 离零 0.48 SE，要 18 轮才判得出。
    #   [[a-reading-exactly-at-the-threshold-is-load-bearing]]｜[[gate-below-instrument-noise]]
    if len(deltas) >= 2:
        sd = statistics.stdev(deltas)
        se = sd / (len(deltas) ** 0.5)
        n_se = abs(mean_d) / se if se else float("inf")
        print("     σ %.1f pp｜SE %.1f pp｜**离零 %.2f SE** ⇒ %s"
              % (100 * sd, 100 * se, n_se,
                 "判不出与零的差别（<2 SE）—— **不许写成「有收益」**" if n_se < 2
                 else "离零 ≥2 SE"))
        need = int((2 * sd / abs(mean_d)) ** 2) + 1 if mean_d else None
        if need and n_se < 2:
            print("     要让这个效应量达到 2 SE，任务集需要约 **%d 个任务**（现有 %d 个）"
                  % (need, len(deltas)))

    # ★★★ **先按队伍规模分开，再谈平均。**
    #   `single_expert` 的队伍只有 1 人 ⇒ 命中率只能是 0% 或 100%，
    #   一条题就能给出 +89.2 或 −39.5，**方差几乎全被这几条支配**。
    #   把 n=1 与 n=9 混进同一个平均，是拿两把尺子当一把用。
    #   [[changing-the-sampling-unit-changes-the-ruler]]｜[[length-confound-in-blind-eval]]
    solo = [r for r in rows if r["team_size"] == 1 and r["delta"] is not None]
    team = [r for r in rows if r["team_size"] > 1 and r["delta"] is not None]
    print("\n  ★★★ 按队伍规模分开（**混着算会被 n=1 的二值命中率支配**）：")
    for label, grp in (("single_expert（n=1，命中率只能 0% 或 100%）", solo),
                       ("small_team 及以上（n≥5）", team)):
        if not grp:
            continue
        ds = [r["delta"] for r in grp]
        m = statistics.mean(ds)
        line = "     %-38s %2d 题｜平均 **%+.1f pp**" % (label, len(grp), 100 * m)
        if len(ds) >= 2:
            se_ = statistics.stdev(ds) / (len(ds) ** 0.5)
            line += "｜SE %.1f｜离零 %.2f SE" % (100 * se_, abs(m) / se_ if se_ else 0)
        print(line)
    if team:
        ds = [r["delta"] for r in team]
        print("     ⇒ **真正的团队模式（n≥5）才是产品的常态**，它的数是 %+.1f pp。"
              % (100 * statistics.mean(ds)))

    # ★ 分层看：相关族在池子里**稀有**时路由才显出信号
    rare = [r for r in rows if r["random_hit"] is not None and 0 < r["random_hit"] < 0.15]
    common = [r for r in rows if r["random_hit"] is not None and r["random_hit"] >= 0.15]
    if rare and common:
        print("\n  ★★ 分层（按相关族在池中的稀有度）：")
        print("     随机基线 <15%%（相关族稀有）%d 个 → 平均 **%+.1f pp**：%s"
              % (len(rare), 100 * statistics.mean(r["delta"] for r in rare),
                 "、".join(r["id"] for r in rare)))
        print("     随机基线 ≥15%%（相关族常见）%d 个 → 平均 **%+.1f pp**：%s"
              % (len(common), 100 * statistics.mean(r["delta"] for r in common),
                 "、".join(r["id"] for r in common)))
        print("     ⇒ 相关族越常见，路由越接近（甚至低于）随机抽。")

    pos = next(r for r in rows if r["id"] == "api-readability")
    print("  ★ 正对照（api-readability，答案明显）：路由 %.1f%% vs 随机 %.1f%% ⇒ %s"
          % (100 * pos["routed_hit"], 100 * pos["random_hit"],
             "尺子是活的" if pos["delta"] > 0 else "**连正对照都不高 —— 先查本件，别急着判产品**"))

    zero = next(r for r in rows if r["id"] == "clinical-triage")
    print("  ★ 族缺口（clinical-triage）：路由 %.1f%% —— 名册里医疗护理师 **0 人**，"
          "这一条注定命中 0，是名册的洞不是路由的错" % (100 * zero["routed_hit"]))

    # ★★★ 2026-08-17：**这把尺子够得着词表的多少？**
    #   今天修「`设计`/`design` 一个动词就把整个 creative-design 拉进来」时，
    #   前后跑本件只动了 +0.4 pp（0.15 SE，判不出）。查原因：
    #   **`设计` 在这 24 道题里只命中 2 道** —— 尺子几乎没碰到那个 bug。
    #   逐词数一遍才看清：**290 个词里只有 61 个在这 24 道题上命中过**。
    #   ⇒ 任何基于本件的「改好了／改坏了」，对**没被碰到的那些词是未量**，
    #     不是「没问题」。这句必须跟着数一起报。
    #   [[a-gates-scan-set-is-smaller-than-reality]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    try:
        # ★ 本件平时是**起子进程**跑路由的，从不 import 它 —— 所以这里要显式加路径。
        #   （第一版没加，兜底分支如实报了「未量」而不是假装全覆盖，那一点是对的。）
        _gs = str((pathlib.Path(a.registry_root) / "scripts").resolve())
        if _gs not in sys.path:
            sys.path.insert(0, _gs)
        from compile_task_graph import DOMAIN_SIGNALS, _signal_hits
        _all = [w for ws in DOMAIN_SIGNALS.values() for w in ws]
        _lows = [str(t["task"]).casefold() for t in TASKS]
        _hit = sum(1 for w in _all if any(_signal_hits(w, low) for low in _lows))
        print("\n  ★★★ **本件够得着的词表射程**：%d 道题只命中了 %d / %d 个关键词"
              "（**%.0f%%**）——剩下 %d 个词**本件从未验过**，"
              "对它们的任何改动本件都判不出好坏。"
              % (len(TASKS), _hit, len(_all), 100.0 * _hit / max(1, len(_all)), len(_all) - _hit))
    except Exception as exc:                                  # noqa: BLE001
        print("\n  ★ 词表射程**未量**（读不到 DOMAIN_SIGNALS：%s）—— 不是「全覆盖」" % exc)

    # ★★★★ **任务分类器兜底率** —— 这是「54% 没有领域信号」的上游真因。
    #   `compile_task_graph.infer_domains()` 拿 9 个关键词表撞任务文本，
    #   撞不上就返回 `["general-decision"]` —— 而 **`general-decision`
    #   不在任何一个族的 CATEGORY_DOMAINS 集合里**，于是
    #   `domain_match = |交集| / |domains| = 0`，**对全部 101 个候选恒为 0**。
    #   实测撞不上的例子：`flaky-test-suite`（文本有「测试」，词表里没有）、
    #   `pricing-saas`（有「定价」，词表里没有）、`bridge-inspection`
    #   （有「钢桥」，词表里没有）。**词表是瞎的，而系统把账记在「没有合适的人」上。**
    #   [[blamed-the-channel-my-own-wordlist-was-blind]]｜[[regex-must-clear-the-corpus-language]]
    blind_rows = [r for r in rows if r.get("_dm_all_zero")]
    if rows:
        print("\n  ★★★★ 任务分类器兜底率（`domain_match` 对全队恒为 0）："
              "**%d / %d = %.0f%%**" % (len(blind_rows), len(rows), 100 * len(blind_rows) / len(rows)))
        if blind_rows:
            print("     %s" % "、".join(r["id"] for r in blind_rows))
        big = [r for r in rows if r["team_size"] > 1]
        b1 = [r for r in big if r.get("_dm_all_zero")]
        b0 = [r for r in big if not r.get("_dm_all_zero")]
        for lab, grp in (("有领域信号", b0), ("失去领域信号", b1)):
            if len(grp) >= 2:
                ds = [r["delta"] for r in grp]
                se_ = statistics.stdev(ds) / (len(ds) ** 0.5)
                print("     n≥5 · %s %2d 题 → 平均 **%+.1f pp**（SE %.1f）"
                      % (lab, len(grp), 100 * statistics.mean(ds), 100 * se_))
        print("     ⇒ 机制**有效**（有信号时为正），但它一半以上的时间**没有信号**，"
              "且 route-plan 的 `limitations` 里**不提这件事**。")

    # ★★★ 分项诊断：**哪一项在真正分辨人**。
    #   路由≈随机不是玄学，去看打分的分项就知道 —— 若唯一有极差的那一项
    #   与任务无关（比如「人物年代新旧」），那它排的就是年代不是本事。
    flat = {}
    n_bd = 0
    for r in rows:
        for m in r.get("_breakdowns", []):
            n_bd += 1

            def walk(d, prefix=""):
                for k, v in d.items():
                    if isinstance(v, dict):
                        walk(v, prefix + k + ".")
                    elif isinstance(v, (int, float)):
                        flat.setdefault(prefix + k, []).append(v)
            walk(m)
    if flat:
        print("\n  ★★★ 打分分项的分辨力（样本：%d 个入选席位 / %d 个任务；"
              "**排除者不带 score_breakdown，取不到**）" % (n_bd, len(rows)))
        print("     %-32s %8s %8s" % ("分项", "极差", "σ"))
        dead = []
        for k, vs in sorted(flat.items(), key=lambda kv: -(max(kv[1]) - min(kv[1]))):
            rng_ = max(vs) - min(vs)
            print("     %-32s %8.4f %8.4f" % (k, rng_, statistics.pstdev(vs)))
            if rng_ == 0:
                dead.append(k)
        top = max(flat.items(), key=lambda kv: max(kv[1]) - min(kv[1]))
        print("     ⇒ 分辨力最大的是 **%s**（极差 %.4f）" % (top[0], max(top[1]) - min(top[1])))
        if dead:
            print("     ⇒ **对所有候选恒定、一点分辨力都没有的分项：%s**" % "、".join(dead))

        # ★★ 极差只说「谁在动」，不说「谁在driving排序」。
        #    真正驱动排序的是 **权重 × σ** —— 权重最大的 task_similarity(0.24)
        #    实际只贡献一成多，而权重 0.15 的 domain_match 占了近一半。
        seat_values = {k.split(".")[-1]: v for k, v in flat.items() if k.startswith("values.")}
        contrib, total = variance_contribution(seat_values)
        print("\n  ★★★★ 谁在**驱动排序**（权重 × σ；权重本身会骗人）")
        print("     %-24s %6s %8s %9s %7s" % ("分项", "权重", "σ", "权重×σ", "占比"))
        for c, k, w, sd in contrib:
            tag = "  ← **纯人工关键词表算出来的**" if k == "domain_match" else ""
            print("     %-24s %6.2f %8.4f %9.4f %6.1f%%%s" % (k, w, sd, c, 100 * c / total, tag))
        dm = next((c for c, k, _, _ in contrib if k == "domain_match"), 0.0)
        print("     ⇒ `domain_match` 占 **%.1f%%** —— 它由 `DOMAIN_SIGNALS` 关键词表算出。"
              % (100 * dm / total))
        print("     ★ 任务包 `moe-routing-contract.md` 的 A 层一节写着：")
        print("       **「人工关键词不得成为冠军路由的主要证据」**")
        print("     ⇒ 本工具报出的路由增益，**主要证据正是人工关键词**；报数必须连这句一起报。")
        print("     ★ 合同想要的冠军证据是 C 层结果遥测 —— 而遥测至今 **0 条**。")
        print("       关键词之所以主导，是因为 **C 从来没有打开过**，不是有人选它当冠军。")

    if a.as_json:
        print("\n" + json.dumps({"seed": SEED, "trials": a.trials,
                                 "pool_size": len(pool), "rows": rows},
                                ensure_ascii=False, indent=1))
    # 只报数，不设阈值 —— 阈值要 Owner 定。永远 rc=0。
    return 0


if __name__ == "__main__":
    sys.exit(main())
