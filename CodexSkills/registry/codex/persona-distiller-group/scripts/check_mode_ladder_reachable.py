#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_mode_ladder_reachable.py —— **四档模式里，有几档是真够得到的？**

## 为什么有这件（2026-08-18）

`choose_mode` 有四档（single_expert / small_team / deep_team / swarm），
各自由一组阈值触发。拿**产物自己写的** `application_scenarios` 当任务
（60 条，不是我编的），逐条跑 `compile_task_graph` 量出来：

    mode 分布：single_expert **53** ／ small_team **7** ／ deep_team 0 ／ swarm 0

    domains    中位 1.000｜最大 4.000｜≥2（small_team 触发） 5/60
    complexity 中位 0.254｜**最大 0.494**｜≥0.38 6/60｜**≥0.76（deep_team）0/60**
    risk       中位 0.080｜**最大 0.270**｜**≥0.36（small_team）0/60**｜≥0.72 0/60

⇒ **`risk` 那条触发永远够不到**（它的最低门槛 0.36 比实测最大值 0.270 还高）；
  **`deep_team` 与 `swarm` 在这套语料上结构性不可达**。
  一个「团队 skill」在 88% 的任务上只坐 1 个人。

这是 `check_gate_reachability.py`（蒸馏侧：门槛设在评委实测天花板之上）
的**同形状问题，换了个主体**：那边是分数够不到门，这边是任务画像够不到档。
[[gate-above-judge-ceiling]]｜[[a-red-that-can-never-turn-green-is-not-a-signal]]

## ★★★★★★ 2026-08-18 晚：**把仓里现成的 72 条任务口吻题喂进 `--tasks` 之后，上面三条结论有两条被推翻**

本文件从建成起就写着「那个数没量过」并留了 `--tasks` 插座。**现在量了。**
样本：`_ledgers/_pipeline/benchmarks/development-48.jsonl` + `regression-24.jsonl`
（**72 条，任务口吻，平均 64 字，TaskPack 原样，不是我编的**）。

| | 名册标签 60 条（名词短语，33 字） | **72 道 oracle（任务口吻）** |
|---|---:|---:|
| `single_expert` | **53（88%）** | **0** |
| `small_team` | 7 | **54（75%）** |
| `deep_team` | **0** | **18（25%）** |
| `swarm` | 0 | **0** |

**① 「88% 只坐 1 个人」＝ 标签的产物** —— 真任务上单人档**一次也没被选中**。
**② 「deep_team 结构性不可达」不成立** —— 真任务 **18/72 = 25%**，靠 `complexity ≥ 0.76`。
**③ 「swarm 结构性不可达」被坐实** —— `parallelizability` 最大 **0.665 < 门 0.72**，
　 与那条**照着 swarm 门写的**验收题面**读数完全相同**；三处独立样本同一个上界。

逐触发（真任务）：`complexity` **72/72**（标签上只 6/60）｜`domains≥2` 42/72｜
`risk` 6/72 且最大 0.460（**仍够不到 deep 的 0.72**）｜`domains≥5` **0/72**｜`parallel` **0/72**。
⇒ **真任务上唯一在起作用的触发是 `complexity`。**

**④ 域分类器那一段也被推翻**：标签上兜底档 `general-decision` 占 **33/67 = 49.3%**，
**真任务 72 条里一次都没出现**（`research-education` 占 50%）。

★ 词表召回也换了面貌但结论不变：真任务上 `HIGH_RISK` 终于有 **6 条命中够 2 个**
（标签上 0 条），`PARALLEL` 最好的一条命中 **3 个**（竞品/矩阵/并行/批量）—— **仍差 1 个**。

★★ **仍要说清的射程**：这 72 条**也不是真实用户提问**，是任务包作者写的 oracle，
且每题带 3 个机械变体 ⇒ **独立题面只有 24 个**。**真实提问的分布依然没有量过。**

⇒ **下面各节里凡是没标注样本的百分数，默认说的是「名册标签」那一份。**
[[samples-cannot-support-universal-claims]]｜[[changing-the-sampling-unit-changes-the-ruler]]

## ★★★ 本件**只报可达性，不建议改数字**

「把 risk 门槛从 0.36 调到 0.25」会让更多任务进 small_team ——
**那正是「为凑数放宽判据」**。要不要改档位，得先有一个东西本件给不了：
**证据说明多人比单人做得更好**。而遥测现在是 `sample_count=1`、
`eligible_for_c=False` —— 策略 C 未标定，**一条产出数据都没有**。

⇒ 本件的产出是**一句可证伪的话**：「第 N 档在当前语料上 0 次触发，
它的最低门槛比实测最大值高 X」。改不改由人拿别的证据决定。
[[no-blocking-on-gate-shortfall]]｜[[a-penalty-is-not-a-rule]]

## ★★★★ `risk` 够不到的真因：**它量的不是「这活风险高不高」**

按本件新加的词表召回段实测（同 60 条任务）：

    HIGH_RISK **18** 个词｜**有过命中的只有 5 个**
    每条任务命中数：{0: **53**, 1: 7}   而够到最低门槛 0.36 需命中 **2** 个
    命中过的：投资×3、production×1、财务×1、安全×1、合规×1
    ⇒ **没有一条任务命中够 2 个** —— 结构性够不到，不是偶然

再看词表本身：

    compliance、financial、legal、medical、production、regulated、safety、
    人身、医疗、合规、安全、投资、法律、生产、监管、税、诉讼、财务

**这是「题材属不属受监管领域」的词表，不是「这活干起来风险高不高」的词表。**
「把单体拆成微服务、设计灰度发布」是一件真有执行风险的活（线上变更、回滚），
它一个词都不沾；而「设计一个投资组合」沾了 `投资`，但那是**题材**风险不是**执行**风险。

⇒ 变量名叫 `risk`、被 `choose_mode` 当作「这活要不要多派人」用，
  而它实际测的是另一个东西。**名字对了，量的语域错了。**
  [[measured-voice-in-the-wrong-register]]｜[[the-comment-states-the-rule-the-code-narrows-it]]

★ 本件**仍然不改词表**。补词会让更多任务进 small_team ——
  在「多人是否真的更好」没有证据之前，那还是「为凑数放宽判据」。
  本件只负责把这句话摆到台面上：**这个信号从建成起没被任何一道门用上过**。

## ★★ `parallelizability` 更极端：4 次命中里 3 次是子串事故

    PARALLEL **14** 个词｜有过命中的只有 3 个｜每条命中数 {0: **56**, 1: 4}
    够到 swarm 门槛 0.72 需命中 **4** 个（= 整张词表全中，一条 60 字的任务里）

逐条看上下文才发现（**只有计数看不出来**）：

    all   …Capital [all]ocation…            ← allocation
    all   …directional-c[all]-with-stated…  ← call
    所有   …利益是否在[所有]权层面与客户对齐…    ← 所有权（ownership）
    批量   …研发流、队列、WIP、[批量]与反馈诊断…  ← **唯一的真命中**

⇒ 60 条任务里真正沾「可并行」的只有 **1 条**。
  `all` 与 `所有` 是**子串匹配撞进更长的词**，本件已把它们标成「需人眼确认」并印出上下文。
  [[hit-that-the-user-cannot-see-is-not-a-hit]]｜[[a-signal-that-both-overfires-and-underfires]]

★ 这个标记本身我改了两版才对：
  第一版按「短纯 ASCII 词」猜 ⇒ 标出 `all`、**漏掉 `所有`**；
  放宽到中文之后又把大半张词表都标了（医疗/合规/监管…），**噪声盖过信号**；
  现在按**实测**标：只看真命中过、且命中处紧邻同语种字的词。

## ★★★★★ 最上游：**域分类器过半时候认不出来**

`domains >= 2` 是 small_team 三条触发里**唯一真正在起作用**的一条
（`complexity` 命中 6/60、`risk` 0/60）。而「域数」来自 `task_profile` 的分类器 ——
量它自己的召回（同 60 条任务，本件实跑印出）：

    名册里的身份族 **11** 个｜认出过的域 **8** 个

    general-decision      33 次（49.3%）  ← **兜底档**
    operations-product    13 次（19.4%）
    finance-investment     8 次（11.9%）
    research-education     7 次（10.4%）
    legal-policy           2 次｜healthcare 2 次
    engineering-industry   1 次｜**software-ai 1 次**

⇒ **占比最高的是兜底档，过半任务没被认成任何专业域。**
  而 `software-ai` 只认出 **1 次** —— 名册最大的族正是 **34 人的 software-developer**，
  这 60 条场景**就是他们自己写的**。

**整条因果链（每一环都有实测）：**

    分类器过半落兜底档  ⇒  域数几乎恒为 1  ⇒  `domains>=2` 不触发
                        ⇒  另两条触发（complexity 6/60、risk 0/60）也几乎不触发
                        ⇒  **恒 single_expert（53/60）**
                        ⇒  一个「团队 skill」在 88% 的任务上只坐 1 个人

**不是任务真的单一，是分类器认不出来。**
[[blamed-the-channel-my-own-wordlist-was-blind]]｜[[a-corpus-that-is-huge-but-single-lane]]

★ 本件**仍然不改分类器**。补词表会让更多任务被认成专业域、进而多派人 ——
  在「多人是否真的更好」没有证据之前，那还是「为凑数放宽判据」。
  本件负责把这条链**逐环量出来摆在台面上**，让下一个人知道该从哪一环动手。

## ★★★★★ 射程订正（2026-08-18，同日）：**这批样本不是用户会打的任务**

上面所有数字都成立，但**它们说的是「名册场景标签」，不是「用户提问」**。必须写清：

    样本平均长度 **33 字**，而且多数是**名词短语**：
      「表征与范式设计」（7 字）、「research-problem-solving」、
      「性能敏感场景下的抽象设计（零开销判据）」

对照实验（**同样长度、改成用户口吻**）：

    「性能敏感场景下的抽象设计（零开销判据）」        19 字 → software-ai      single_expert
    「帮我设计一个性能敏感模块的抽象层，要求零开销，
      并给出测试与回滚方案」                        33 字 → software-ai      **small_team**

⇒ **同样 33 字，换成用户口吻就够到了 small_team。**
  所以「88% 只坐 1 个人」这句的射程是**名册标签**，
  **不能读成「用户用起来 88% 只有 1 个人」**——那个数**没有量过**。

★ 我一度把它写成后者并提交了。订正在此。
  [[samples-cannot-support-universal-claims]]｜[[a-verdict-whose-scope-exceeds-its-inputs]]

★★ **订正（2026-08-18 同日）：上一句我写错了射程。**
  原话是「仓里没有一份保存下来的、代表性的用户口吻任务集」——**对 72 道 oracle 不成立**：
  `_ledgers/_pipeline/benchmarks/development-48.jsonl`（48 条）与 `regression-24.jsonl`（24 条）
  **一直都在**，`check_benchmark_mode_accuracy.py` 每次还会印出两份的 sha256 与
  「从 TaskPack 原样复制，不是我编的」。本文上面那句「88% 只坐 1 人」用的是**名册标签**，
  而那 72 条**是任务口吻的**——两者不是一回事，我把「本件没用」写成了「仓里没有」。

  仍然成立的那一半：`route_team_moe.py:420` 引的
  「24 pre-registered tasks / **54% 无域信号 / −1.7pp**」出自**另一次**运行，
  那次的任务与逐条读数确实没留，无法复算。
  ⇒ 射程该收窄成「**那一条**结论没留输入」，不是「仓里没有任务集」。
  [[evidence-must-carry-what-it-measured]]｜[[claims-my-own-next-delivery-falsifies]]｜[[a-verdict-whose-scope-exceeds-its-inputs]]

★★★ 那 72 条上的实测（2026-08-18 @v0.0.0.31）：模式命中 **25%**
  （development-48 12/48、regression-24 6/24），`single_expert` 与 `swarm`
  **一次都没被选中**——★ 注意这与本文上面「名册标签上 single_expert 占 88%」
  **方向相反**：同一个产品，两份样本给出两幅相反的图。**报这个数必须连样本一起报。**
  ⇒ 本件因此**只报它真的量过的那一面**，并在输出里把这句射程一起印出来。

## ★★★★ 为什么我**不**替它造一份「用户口吻任务集」

上一节说清了：现有样本是**标签**，缺的是**真实用户提问**。
自然的下一步像是「从 `key_capabilities` 按模板生成一批用户口吻的任务」。**我不做，理由是循环：**

    某个软件人的 `key_capabilities` 里必然带软件词 —— **因为他就是软件人**。
    拿它生成的任务去问「分类器认不认得出软件任务」，
    等于**题集与被测的分类器共用同一个措辞来源**。
    验出来的是我的模板，不是产品在真实提问上的表现。
    [[independent-is-not-realistic-shared-wording-source]]｜[[fixtures-are-clean-because-i-wrote-them]]

⇒ 造一份出来会让这道门变绿，而那个绿**什么也不证明**。

**能做的是把插座留好，不是造假数据**：本件加了 `--tasks <文件>`
（每行一条，或 JSON 数组）。等真实提问从遥测里攒出来（或 Owner 给一份），
直接喂进来即可；走外部任务集时，上面那句「标签不是用户提问」的射程话**自动关闭**，
并提示使用者**自己说明这份任务集怎么来的**。

★ 同时加了**最小样本量守卫**：样本 < 20 条时不许下「不可达」的结论（返回 rc=4 未量）——
  否则拿 `--tasks` 塞两条就能得出任意结论。本件自己也要守「样本撑不起全称判断」。

## ★★★★★ 旁边那柜「四档都验收过」的证据，**全是 `--mode` 指定跑出来的**

`evidence/v0.0.0.14-candidate-acceptance/` 下有 route-single_expert / small_team /
deep_team / swarm 四份，看着正是「四档都够得到」的反证。**逐份读它自己的字段：**

    四份都写着 requested_mode = 该档
    四份的 task_graph.mode_reasons 都是 **['explicit owner/runtime override']**

⇒ 它们证明的是「**每一档被指定时跑得起来**」，**不是**「自动推断够得到每一档」。
  这是两件事，而 `route-swarm.json` 这个文件名长得像后者。
  本件已把这两栏**分开印**，免得下一个人拿它当 swarm 可达的证据。
  [[self-report-is-not-evidence]]｜[[evidence-must-carry-what-it-measured]]

★ **我自己差点在这儿翻车。** 先拿这四条题面用 `auto` 重编译，得到「3/4 对不上它自己记的档」，
  几乎写成「验收证据漂了」。**是我在比两个不同的东西**：证据是 `--mode` 跑的，我是 auto 跑的。
  回查确认：profile 的每个数**当时与今天一模一样**（唯一变的是 swarm 的 domains 8→7，
  那是 08-17 `设计/design` 降弱信号的正确结果），
  门槛那三行 `git log -L` 只有一次提交、**从未改过**。
  [[stopping-at-the-first-answer-that-holds-together]]｜[[self-consistent-is-not-latest]]

★★ **最硬的那个数**：swarm 那条题面是**照着 swarm 的门写的** ——
  「全网」「批量」「并行」三个 PARALLEL 词全塞进去了，还写了「至少四十个独立分片」——
  它的 `parallelizability` 仍然只有 **0.665 < 门 0.72**。
  **有人专门为 swarm 写了一条任务，自动推断仍然不会选 swarm。**
  这比 60 条标签上的「0 次触发」更接近「结构性不可达」的直接证据。

## 任务从哪来（不许我自己编）

`team-index.json` 每个产物自带 `application_scenarios` —— 那是蒸馏流程写下的
「这个人适合办哪类事」。本件取它们当任务样本：**样本来自产品，不来自判据作者**。
[[fixtures-are-clean-because-i-wrote-them]]

退出码：0＝四档都够得到；1＝有档够不到；4＝取不到样本/编译器（未量）。
"""
import argparse
import collections
import json
import pathlib
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

#: `choose_mode` 里每一档的触发条件（**与 compile_task_graph.py 同源，改那边要改这里**）
#: 形如 {档: [(画像键, 最低值), …]}——满足**任一条**即触发该档。
TRIGGERS = {
    "swarm":       [("parallelizability", 0.72)],
    "deep_team":   [("complexity", 0.76), ("risk", 0.72), ("domains", 5)],
    "small_team":  [("complexity", 0.38), ("risk", 0.36), ("domains", 2)],
    "single_expert": [],          # 兜底档，天然可达
}


def reachability(profiles: list[dict]):
    """→ {档: {触发键: (门槛, 实测最大, 达到的条数)}}。纯函数，不跑子进程。

    ★ 「达到的条数」用的是**这一条触发**自己的门槛，不是整档的判定 ——
      整档还受前面几档的 if/elif 顺序影响，那是另一回事。本件只问
      「这条触发有没有可能被满足」。
    """
    out = {}
    n = len(profiles)
    for mode, conds in TRIGGERS.items():
        if not conds:
            continue
        row = {}
        for key, thr in conds:
            vals = [float(p.get(key) or 0) for p in profiles]
            row[key] = (thr, max(vals) if vals else 0.0,
                        sum(1 for v in vals if v >= thr), n)
        out[mode] = row
    return out


def evidence_arrival(ev_root) -> tuple:
    """`evidence/` 下每份 `route-*.json` 是**靠推断**到达该档，还是**被 `--mode` 指定**的。

    → `({档: {"推断": n, "指定": n}}, 读到的文件数)`。
    ★ 文件数单独返回：**0 份要判「未核」，不能判「没有指定的」**。
    """
    by_mode, n_files = {}, 0
    for ev in sorted(pathlib.Path(ev_root).rglob("route-*.json")):
        try:
            d = json.loads(ev.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(d, dict):
            continue
        n_files += 1
        forced = (d.get("requested_mode") not in (None, "auto")) or any(
            "override" in str(x) for x in
            ((d.get("task_graph") or {}).get("mode_reasons") or []))
        slot = by_mode.setdefault(d.get("mode"), {"推断": 0, "指定": 0})
        slot["指定" if forced else "推断"] += 1
    return by_mode, n_files


def unreachable(report: dict) -> list[str]:
    """→ 一次都触发不了的档。纯函数。"""
    bad = []
    for mode, row in report.items():
        if all(hit == 0 for (_thr, _mx, hit, _n) in row.values()):
            bad.append(mode)
    return bad


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    # ★ 数值逐字取自 2026-08-18 的 60 条真样本
    real = [{"complexity": 0.254, "risk": 0.080, "domains": 1, "parallelizability": 0.3}] * 54 + \
           [{"complexity": 0.494, "risk": 0.270, "domains": 4, "parallelizability": 0.5}] * 6
    rep = reachability(real)
    chk("★★★ 正例（真样本）：`risk` 最大 0.270 < 门槛 0.36 ⇒ 该触发 0 次命中",
        rep["small_team"]["risk"][2] == 0 and abs(rep["small_team"]["risk"][1] - 0.270) < 1e-9)
    chk("★★★ 正例：`deep_team` 三条触发全 0 ⇒ 判**不可达**",
        "deep_team" in unreachable(rep))
    chk("★★ 负例：`small_team` 有 `domains>=2` 命中 ⇒ **不判**不可达",
        "small_team" not in unreachable(rep))
    chk("★★ 命中数按**这一条触发**自己的门槛算（domains 4≥2 ⇒ 6 条）",
        rep["small_team"]["domains"][2] == 6)
    chk("★★★ 负例：全部远超门槛时，一档都不该判不可达",
        unreachable(reachability([{"complexity": 0.9, "risk": 0.9, "domains": 6,
                                   "parallelizability": 0.9}] * 3)) == [])
    chk("★ `single_expert` 是兜底档，不参与可达性判定", "single_expert" not in rep)
    chk("★ 空样本不炸（由调用方判未量，不在这里当通过）",
        reachability([])["deep_team"]["risk"][1] == 0.0)
    chk("★★ 缺字段按 0 计，不抛异常（画像多一个键少一个键都不该让判据崩）",
        reachability([{"domains": 3}])["small_team"]["domains"][2] == 1)

    # ── `evidence_arrival`：正对照 + 两个负对照 ──
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        chk("★ 空目录判「读到 0 份」——由调用方印**未核**，不是「没有指定的」",
            evidence_arrival(d) == ({}, 0))
        # ① 被 --mode 指定：requested_mode 非 auto
        (d / "route-swarm.json").write_text(json.dumps(
            {"mode": "swarm", "requested_mode": "swarm",
             "task_graph": {"mode_reasons": ["explicit owner/runtime override"]}}),
            encoding="utf-8")
        # ② 靠推断：requested_mode=auto 且 reasons 里没有 override
        (d / "route-auto.json").write_text(json.dumps(
            {"mode": "small_team", "requested_mode": "auto",
             "task_graph": {"mode_reasons": ["multi-capability task with bounded coordination"]}}),
            encoding="utf-8")
        by, nf = evidence_arrival(d)   # ★ 不叫 n：外层 chk 的计数器就叫 n
        chk("★★ 指定与推断分得开（swarm 记「指定」、small_team 记「推断」）",
            nf == 2 and by["swarm"] == {"推断": 0, "指定": 1}
            and by["small_team"] == {"推断": 1, "指定": 0})
        # ③ ★★★ 负对照：**只看 requested_mode 不够** —— 有的产物 requested_mode 缺失，
        #    但 mode_reasons 里写着 override。漏掉这一半会把「被指定」误报成「靠推断」，
        #    而那正是本段要防的那句话。
        (d / "route-sneaky.json").write_text(json.dumps(
            {"mode": "deep_team",
             "task_graph": {"mode_reasons": ["explicit owner/runtime override"]}}),
            encoding="utf-8")
        by, _ = evidence_arrival(d)
        chk("★★★ 负对照：缺 requested_mode 但 reasons 写着 override 的，仍判「指定」",
            by["deep_team"] == {"推断": 0, "指定": 1})
        # ④ 坏 JSON 不计数也不炸
        (d / "route-broken.json").write_text("{ not json", encoding="utf-8")
        _, nf2 = evidence_arrival(d)
        chk("★ 坏 JSON 跳过且不炸（读到 3 份，不是 4 份）", nf2 == 3)
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def sample_tasks(index_path: pathlib.Path, limit: int) -> list[str]:
    """从产物自带的 `application_scenarios` 取任务。**不许判据作者自己编任务。**"""
    d = json.loads(index_path.read_text(encoding="utf-8"))
    out = []
    for p in d.get("products", []):
        for sc in (p.get("application_scenarios") or [])[:2]:
            if isinstance(sc, str) and len(sc) > 12:
                out.append(sc.split("：")[0][:60])
    return list(dict.fromkeys(out))[:limit]


#: 由**词表**驱动的画像项 —— 够不到时要能说出「是词表撞不上，还是这批任务真的不沾」。
#: {画像键: (compile_task_graph 里的词表名, 需要命中几个才够到该项最低门槛)}
# ★★ 并列的兄弟也要覆盖 —— **画像的每一维都是词表驱动的**（compile_task_graph:216–226）：
#   complexity ← 多个词表合成｜risk ← HIGH_RISK｜parallel ← PARALLEL
#   coupling ← DEPENDENCY｜currentness ← CURRENTNESS
#   这里只列**驱动了不可达触发**的那些；「需命中几个」由各自公式反解：
#     risk     = 0.08 + n/4 × 0.76 ≥ 0.36  ⇒ n ≥ 1.47 ⇒ **2**
#     parallel = 0.08 + n/4 × 0.78 ≥ 0.72  ⇒ n ≥ 3.28 ⇒ **4**（即整张词表全中）
#   [[fixed-the-symptom-kept-the-root-cause]]（并列的兄弟链有同样的洞）
WORDLIST_DRIVEN = {"risk": ("HIGH_RISK", 2), "parallelizability": ("PARALLEL", 4)}


def wordlist_recall(mod, name: str, tasks: list[str]):
    """→ (词表大小, 有过命中的词数, {命中数: 任务条数}, [(词, 次数)])。纯函数式，不写盘。

    ★ 为什么要有这一段：`risk` 在 60 条真任务上最大只有 0.270，而它的最低门槛是 0.36。
      「够不到」有两种完全不同的成因，**处置相反**：
        ① 这批任务真的不沾风险 ⇒ 门槛没问题，是样本如此
        ② **词表撞不上** ⇒ 是尺子的召回问题，不是任务的问题
      不量一遍就分不出来。[[blamed-the-channel-my-own-wordlist-was-blind]]
    """
    import collections
    words = getattr(mod, name, None)
    if not words:
        return 0, 0, {}, [], {}, []
    hits = collections.Counter()
    per = collections.Counter()
    ctx: dict = collections.defaultdict(list)
    for t in tasks:
        low = (t or "").lower()
        n = 0
        for w in words:
            ws = str(w).lower()
            if ws in low:
                hits[w] += 1
                n += 1
                # ★ 把**命中的上下文**留下来 —— 只有计数看不出误报。
                #   实测：`all` 的 2 次命中全是 `Capital **all**ocation` 与
                #   `directional-c**all**`，子串撞进了别的词里。
                #   [[hit-that-the-user-cannot-see-is-not-a-hit]]
                i = low.index(ws)
                if len(ctx[w]) < 3:
                    ctx[w].append("…%s[%s]%s…" % (t[max(0, i - 14):i], t[i:i + len(ws)],
                                                  t[i + len(ws):i + len(ws) + 14]))
        per[n] += 1
    # ★★★ 「哪些命中可能是子串事故」**按实测标，不按猜**。
    #   第一版按「短词」猜：先只查纯 ASCII（漏了 `所有 ⊂ 所有权`），
    #   放宽到 CJK 之后又把大半张词表都标了（医疗/合规/监管…），**噪声盖过信号**。
    #   ⇒ 改成：只看**真的命中过**的词，且命中处**紧邻同语种的字**
    #     （英文两侧是字母、中文两侧是汉字）⇒ 它嵌在一个更长的词里。
    #     实测标出：`all`（allocation / call）、`所有`（所有权）。
    #   ★ 中文里这条**分不出** `投资假设`（真）与 `所有权`（假）——
    #     所以标签是「**需人眼确认**」，不是「误中」。上下文已逐条印出，人自己看。
    #   [[regex-must-clear-the-corpus-language]]｜[[read-the-hits-before-reporting-the-rate]]
    def _embedded(word: str, tasks_: list) -> bool:
        ws = str(word).lower()
        ascii_w = ws.isascii()
        for tk in tasks_:
            low = (tk or "").lower()
            i = low.find(ws)
            while i >= 0:
                left = low[i - 1] if i > 0 else ""
                right = low[i + len(ws)] if i + len(ws) < len(low) else ""
                for ch in (left, right):
                    if not ch:
                        continue
                    if ascii_w and ch.isalpha() and ch.isascii():
                        return True
                    if (not ascii_w) and "\u4e00" <= ch <= "\u9fff":
                        return True
                i = low.find(ws, i + 1)
        return False

    risky = sorted((str(w) for w in hits if _embedded(w, tasks)), key=str)
    return (len(words), len(hits), dict(sorted(per.items())), hits.most_common(8),
            dict(ctx), risky)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry-root", default=str(ROOT))
    ap.add_argument("--limit", type=int, default=60, help="取多少条任务样本（默认 60）")
    ap.add_argument("--tasks", default=None, metavar="文件",
                    help="改用**外部任务集**（每行一条，或 JSON 数组）。"
                         "★ 这是留给**真实用户提问**的插座 —— 见 docstring「为什么不自己造一份」。")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    root = pathlib.Path(a.registry_root)
    idx = root / "team-index.json"
    comp = root / "scripts" / "compile_task_graph.py"
    if not idx.is_file() or not comp.is_file():
        print("★ **未量，不是通过**（rc=4）—— 缺 %s"
              % ("team-index.json" if not idx.is_file() else "compile_task_graph.py"))
        return 4
    src = "产物自带的 `application_scenarios`"
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
        tasks = tasks[:a.limit]
        src = "外部任务集 `%s`" % tp.name
    else:
        tasks = sample_tasks(idx, a.limit)
    _avg = (sum(len(x) for x in tasks) / len(tasks)) if tasks else 0
    print("样本：**%d** 条，来自%s" % (len(tasks), src))
    if a.tasks:
        print("  ★ 用的是外部任务集 —— 下面的射程话（「标签不是用户提问」）**不适用于本次**；"
              "请自行说明这份任务集是怎么来的。")
    else:
        print("  ★★ **射程**：平均 **%.0f 字**，且多为**名词短语标签**（如「表征与范式设计」），"
              "**不是用户会打的任务**。" % _avg)
        print("     实测对照：同样 33 字改成用户口吻（「帮我设计一个性能敏感模块的抽象层，"
              "要求零开销，并给出测试与回滚方案」）⇒ **small_team**。")
        print("     ⇒ 下面的「N% 只坐 1 人」说的是**标签**，**不能读成用户用起来如此** —— 那个数没量过。")
    if not tasks:
        print("★ **未量，不是通过**（rc=4）—— 一条样本都取不到")
        return 4

    profiles, modes, failed = [], collections.Counter(), 0
    for t in tasks:
        r = subprocess.run([sys.executable, str(comp), "--task", t],
                           capture_output=True, text=True)
        if r.returncode != 0:
            failed += 1
            continue
        try:
            g = json.loads(r.stdout)
        except ValueError:
            failed += 1
            continue
        pr = dict(g["profile"])
        pr["domains"] = len(pr.get("domains") or [])
        profiles.append(pr)
        modes[g["mode"]] += 1
    if not profiles:
        print("★ **未量，不是通过**（rc=4）—— %d 条样本一条也编译不出画像" % len(tasks))
        return 4
    print("  编译成功 %d 条｜失败 %d 条\n" % (len(profiles), failed))

    print("实际落到各档：%s" % "｜".join("%s %d" % (m, n) for m, n in
                                        sorted(modes.items(), key=lambda x: -x[1])))
    for k in ("domains", "complexity", "risk", "parallelizability"):
        vals = [float(p.get(k) or 0) for p in profiles]
        print("  %-18s 中位 %.3f｜**最大 %.3f**" % (k, statistics.median(vals), max(vals)))

    rep = reachability(profiles)
    print("\n逐档逐触发（门槛 vs 实测最大 vs 命中数）：")
    for mode in ("small_team", "deep_team", "swarm"):
        row = rep.get(mode) or {}
        print("  【%s】" % mode)
        for key, (thr, mx, hit, n) in row.items():
            flag = "  ← ★ **够不到**" if hit == 0 else ""
            print("     %-18s 门槛 %-6s 实测最大 %-7.3f 命中 %d/%d%s"
                  % (key, thr, mx, hit, n, flag))

    # ★ 词表驱动的项：把**词表自己的召回**印出来，分开「样本不沾」与「尺子撞不上」
    try:
        import importlib.util as _ilu
        _s = _ilu.spec_from_file_location("_ctg", str(comp))
        _m = _ilu.module_from_spec(_s)
        sys.path.insert(0, str(comp.parent))
        _s.loader.exec_module(_m)
    except Exception as e:                                   # noqa: BLE001
        _m = None
        print("\n（词表召回未量：装不进 compile_task_graph —— %s）" % str(e)[:80])
    if _m is not None:
        print("\n词表驱动项的召回（分开「样本不沾」与「尺子撞不上」）：")
        for key, (wl, need) in WORDLIST_DRIVEN.items():
            size, used, per, top, ctx, risky = wordlist_recall(_m, wl, tasks)
            if not size:
                print("  %-10s 找不到词表 `%s`（未量）" % (key, wl))
                continue
            print("  %-10s 词表 `%s` **%d** 个词｜**有过命中的只有 %d 个**"
                  % (key, wl, size, used))
            print("             每条任务命中数分布：%s（够到最低门槛需 **%d** 个）"
                  % (per, need))
            if top:
                print("             命中过的：%s"
                      % "、".join("%s×%d" % (w, n) for w, n in top))
                # ★ 逐条印上下文 —— 只有计数分不出「真命中」与「子串撞进别的词」
                for w, _n in top:
                    for c in (ctx.get(w) or []):
                        print("               %-10s %s" % (str(w)[:10], c))
            if risky:
                print("             ⚠ **需人眼确认**（命中处紧邻同语种的字，可能嵌在更长的词里）：%s"
                      % "、".join(risky))
                print("               ⇒ **逐条看上面的上下文**，别只看计数。实测：`all` 全部来自 "
                      "`allocation`/`call`，`所有` 来自 `所有权` —— 三次都不是真命中。")
            if per.get(need, 0) == 0:
                print("             ⇒ **没有一条任务命中够 %d 个** —— 这项够不到"
                      "是**结构性的**，不是偶然。" % need)

    # ★★★★ 最上游那一环：**域分类器自己的召回**。
    #   `domains >= 2` 是 small_team 唯一真正在起作用的触发，
    #   而「域数」本身来自分类器 —— 它认不出来，后面全部塌。
    if _m is not None and hasattr(_m, "task_profile"):
        seen = collections.Counter()
        for tk in tasks:
            try:
                for d in (_m.task_profile(tk).get("domains") or []):
                    seen[d] += 1
            except Exception:                                # noqa: BLE001
                pass
        if seen:
            fams = set()
            try:
                fams = {p.get("identity_family_id") for p in
                        json.loads(idx.read_text(encoding="utf-8")).get("products", [])
                        if p.get("identity_family_id")}
            except Exception:                                # noqa: BLE001
                pass
            print("\n域分类器的召回（`domains` 是 small_team 唯一在起作用的触发）：")
            print("  名册里的身份族 **%d** 个｜60 条任务里认出过的域 **%d** 个"
                  % (len(fams), len(seen)))
            tot = sum(seen.values())
            for d, c in seen.most_common():
                mark = "  ← ★ **兜底档**" if "general" in str(d) else ""
                print("     %-24s %3d 次（%4.1f%%）%s" % (d, c, 100.0 * c / tot, mark))
            top, ntop = seen.most_common(1)[0]
            if "general" in str(top):
                print("  ⇒ ★★ **占比最高的是兜底档 `%s`（%d/%d）** —— "
                      "过半任务没被认成任何专业域。" % (top, ntop, tot))
                print("     这是「域数几乎恒为 1 ⇒ 恒 single_expert」的**最上游成因**：")
                print("     不是任务真的单一，是**分类器认不出来**。")
                print("     [[blamed-the-channel-my-own-wordlist-was-blind]]")

    # ★★★★ 2026-08-18：**旁边那一柜子「四档都验收过」的证据，全是 `--mode` 指定跑出来的。**
    #
    #   `evidence/v0.0.0.14-candidate-acceptance/` 下有 route-single_expert / small_team /
    #   deep_team / swarm 四份，看起来正是「四档都够得到」的反证。逐份读它自己的字段：
    #
    #       四份都写着 requested_mode = 该档
    #       四份的 task_graph.mode_reasons 都是 **['explicit owner/runtime override']**
    #
    #   ⇒ 它们证明的是「**每一档被指定时跑得起来**」，**不是**「自动推断够得到每一档」。
    #     这两句话是两件事，而文件名 `route-swarm.json` 长得像后者。
    #
    #   ★ 我自己差点在这里翻车：先拿这四条题面用 `auto` 重编译，得到「3/4 对不上它自己记的档」，
    #     几乎写成「验收证据漂了」。**是我在比两个不同的东西** —— 证据是 `--mode` 跑的，
    #     我是 auto 跑的。回查确认：profile 每个数**当时与今天一模一样**
    #     （唯一变的是 swarm 的 domains 8→7，那是 08-17 `设计/design` 降弱信号的正确结果），
    #     门槛那三行 `git log -L` 只有一次提交、**从未改过**。
    #     [[stopping-at-the-first-answer-that-holds-together]]
    #
    #   ★★ 最硬的那个数：swarm 那条题面是**照着 swarm 的门写的**
    #     （「全网」「批量」「并行」「至少四十个独立分片」三个 PARALLEL 词全塞进去了），
    #     它的 parallelizability 仍然只有 **0.665 < 门 0.72**。
    #     **有人专门为 swarm 写了一条任务，自动推断仍然不会选 swarm。**
    #
    #   本段只做一件事：把「靠推断到达」与「被指定到达」**分开印**，
    #   免得下一个人拿 route-swarm.json 当作 swarm 可达的证据。
    #   [[self-report-is-not-evidence]]｜[[evidence-must-carry-what-it-measured]]
    ev_root = root / "evidence"
    if ev_root.is_dir():
        by_mode, n_files = evidence_arrival(ev_root)
        print("\n`evidence/` 里的路由产物：**靠推断到达** vs **被 `--mode` 指定到达**")
        if not n_files:
            print("  **未核**：`evidence/` 下一份 `route-*.json` 都没有（不是「没有指定的」）。")
        else:
            print("  | 档 | 靠推断到达 | 被指定到达 |")
            print("  |---|---:|---:|")
            for m in sorted(by_mode):
                s = by_mode[m]
                print("  | %s | %s | %d |"
                      % (m, ("**%d**" % s["推断"]) if s["推断"] else "**0**", s["指定"]))
            only_forced = [m for m, s in by_mode.items() if s["推断"] == 0 and s["指定"]]
            if only_forced:
                print("  ⇒ ★ **%s** 在 `evidence/` 里只有「被指定」的产物，"
                      "**一份靠推断到达的都没有**。" % "、".join(sorted(only_forced)))
                print("     `route-<档>.json` 这个文件名看着像「该档可达」的证据，**它不是**。")

    dead = unreachable(rep)
    # ★★★ **样本撑不起全称判断**：3 条任务上「一次也没触发」说明不了「不可达」。
    #   本件自己也得守这条 —— 否则拿 `--tasks` 塞 2 条就能得出任意结论。
    #   门槛 20 是**下限不是目标**：它只保证「0 次触发」不是小样本的偶然。
    MIN_N = 20
    if len(profiles) < MIN_N and dead:
        print("\n★ **未量，不是通过**（rc=4）—— 只有 **%d** 条样本（下限 %d）。"
              % (len(profiles), MIN_N))
        print("  「%s 一次也没触发」在这个样本量上**说明不了不可达** ——"
              % "、".join(dead))
        print("  它可能只是没抽到。[[samples-cannot-support-universal-claims]]")
        return 4
    print("\n可达 %d 档｜**不可达 %d 档**" % (len(rep) - len(dead), len(dead)))
    if not dead:
        print("\n✓ 每一档都有任务够得到")
        return 0
    print("\n✗ **这些档在当前语料上一次也触发不了**：%s" % "、".join(dead))
    print("\n  ★ 本件**不建议改门槛** —— 把 risk 从 0.36 调到 0.25 会让更多任务进 small_team，")
    print("    而那正是「为凑数放宽判据」。要不要改，得先有本件给不了的东西：")
    print("    **证据说明多人比单人做得更好**。遥测若仍是 `sample_count=1`／`eligible_for_c=False`，")
    print("    就还没有任何产出数据能支持这个决定。")
    print("  ★★ 本件的产出是一句**可证伪的话**：「第 N 档 0 次触发，最低门槛比实测最大值高 X」。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
