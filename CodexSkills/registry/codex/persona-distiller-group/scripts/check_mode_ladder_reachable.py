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
    tasks = sample_tasks(idx, a.limit)
    print("样本：**%d** 条任务，全部取自产物自带的 `application_scenarios`"
          "（**不是判据作者编的**）" % len(tasks))
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

    dead = unreachable(rep)
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
