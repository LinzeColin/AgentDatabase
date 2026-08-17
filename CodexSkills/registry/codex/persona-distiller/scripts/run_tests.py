#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `tests/` 下的测试**真的跑一遍**（**件数以它自己印的「扫描面」为准，本文不写死** ——此处原写 15，2026-08-17 实测 19），并把已知未决与新回归分开。

为什么要有这份文件
------------------
2026-08-17 手工把 `tests/test_*.py` 逐个跑了一遍，发现
`test_group_contract.py` **一直红着**（`failures=1, errors=2`），
而且红在**四个产品从未有过的键**上（`inferred_identity` 在 git 全历史里 0 处）。

★★ **订正（2026-08-17 同日，写完本件之后）：我先前写的「没有任何东西会去跑它们」
   是错的。** `self_check.py` 第 216–224 行**本来就跑整套** —— `unittest discover -s tests`，
   失败即 `errors.append('offline unittest suite failed')` → **rc=1**。
   那件红**并非不可见**：它会让 `self_check` 失败，并把 `test_release_bundle` 一起拖红
   （我今天正是这么撞见的）。**它不是没人跑，是跑了没人修。**

真实的缺口只有两条，都比我原来说的窄：

1. **`install.py` 调的是 `self_check.py --skip-tests`** —— 安装路径**跳过**测试。
2. `self_check` 只给**一个聚合的 pass/fail**：14 件里哪一件红、红了多久、
   是新回归还是待裁定，**它一个字都不说**。

⇒ 本件的价值因此也要说窄：**不是「补上没人跑」，是「把一个聚合结果拆成逐件，
并把待裁定与新回归分开」**。[[a-checker-nothing-calls-is-not-a-checker]] 的说法
在这里**不成立**，我错用了它。

## 这套测试有多大力气——2026-08-17 变异实测（**对照本身必须干净**）

把最吃重的那个函数打坏：`quality_check.Report.error` 改成空操作
（**所有门无条件通过**），**两份镜像同改**（scripts/ 与 references/）、重算清单，
再跑 15 件测试：

    红 2 件 = `test_group_contract`（基线就红，待 Owner 裁定，不算察觉）
             + `test_quality_and_eval`
    ⇒ **真察觉 1/14 —— 只有 `test_quality_and_eval`**

★★★ 这个数我报错过两次，**两次都是对照没做干净**：

    第一版：直接把 5 件红报成「察觉 4/14」——
            没扣掉 `group_contract` 这个基线就红的。
    第二版：改成只动 `scripts/` 一处来做「空对照」，三件验清册的测试全红，
            我据此写「它们对任何改动都红 ⇒ 是混淆，真察觉 1/14」。
            **也错了**：只改一处会造出真实的镜像漂移
            （报错原文：「quality_check.py 两处不一致（镜像 253006 / 脚本 253024 字节）」），
            那三件红得**完全正确**，不是混淆。
    第三版（本节）：两处同改再对照 —— 三件**全绿**，证明它们没有混淆；
            变异也两处同改，红的就只剩 2 件。

    ⇒ 教训：**空对照自己不许带缺陷**。我那次「行为不变」的对照，
      在另一个维度上引入了一个真缺陷，于是把真报警读成了假报警。
      [[negative-control-must-not-share-the-assumption]]｜[[my-diagnostics-manufacture-false-leads]]

★ 结论要说准：**不是没人看**（`quality_and_eval` 看得见），
  是**只有一件在看**这个最吃重的出口。要不要补属产品决策，本文件只报数。
★ 复算方法：两份镜像同改一行 → `build_manifest.py` → 逐件跑 `tests/`。

## 为什么默认**不是门**

今天还剩 **2 条真失败**（路由没选中测试点名的人物），
它们是**待 Owner 裁定的契约分歧**，不是可以随手修好的 bug。
把 runner 直接接成硬门，等于**用一个未决问题卡住整条流程** ——
本项目明令「不许因为过不了门而卡住流程」。

⇒ 三档，由调用方选：

    （默认）           只报告，**永远 rc=0**
    --strict          任何一件红 → rc=1
    --strict --allow-known
                      **只有「不在已知名单里的」红才 rc=1** ← 推荐当门用

第三档是唯一既能挡住**新回归**、又不会被两条未决问题卡住的用法。
★ 已知名单写死在本文件里并**逐条附理由**；名单里的项一旦变绿，
本件会**主动报出来**（「已知失败已修复，请把它从名单里删掉」）——
**名单只许缩，不许悄悄长**。

用法
----
    python3 scripts/run_tests.py                     # 报告
    python3 scripts/run_tests.py --strict --allow-known   # 当门用
    python3 scripts/run_tests.py --self-test
"""
import argparse
import concurrent.futures
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TESTS = HERE.parent / "tests"

# ★ 已知未决：**每条都要写清「为什么还红着」与「谁能让它变绿」**。
#   没有理由的条目不许进这个名单 —— 那就成了「把红灯关掉」。
KNOWN = {
    "test_group_contract.py": (
        "2 条真失败（errors 已于 2026-08-17 清零）：软件题期望入选 Simon Willison、"
        "运营题期望入选 Anne Mulcahy／路易斯·郭士纳，而路由未选中。"
        "**五人全部在册**（逐个核过 team-index.json）⇒ 不是人物不存在，是路由没选中。"
        "改期望值＝把测试改成产品现在的样子，属「模式判定/路由该不该改」，**待 Owner 裁定**。"
    ),
}


def discover():
    """`test_*.py` **加** `run_*.py` —— 同一个教训只落在了另一棵树上。

    ★ 团队 skill 的 `scripts/run_tests.py` 早就是多模式：它的 `tests/` 里
    最重要的一件叫 `run_functional_acceptance.py`，**不叫 `test_*`**，
    只认一种命名就会漏掉它（那边的 CHANGELOG 与 SKILL.md 都写着，
    自测里还专门钉了「漏掉它直接判失败」）。
    而本 skill 这份一直只 `glob("test_*.py")` ——
    **今天 `tests/` 里恰好没有 `run_*.py`，所以现在漏 0 件**；
    但下一件叫 `run_` 的加进来时会被静默跳过，而「静默跳过」正是
    本仓记过十二种的那一族。[[a-gates-scan-set-is-smaller-than-reality]]

    一并印出**按哪些模式扫的**，让扫描面自己出现在输出里。
    """
    if not TESTS.is_dir():
        return []
    seen = {}
    for pat in ("test_*.py", "run_*.py"):
        for p in TESTS.glob(pat):
            seen[p.name] = p
    return [seen[k] for k in sorted(seen)]


# ★★★ 2026-08-17：本件此前**只留最后一行、截到 60 字**，其余输出全丢。
#   于是 `test_quality_and_eval.py` 报「新回归 FAILED (errors=2)」而**没有任何 traceback**，
#   而它**单独跑是绿的**（`Ran 3 tests in 88.1s OK`）——只在并行里失败。
#   ⇒ 被丢掉的那段输出是**唯一的证据**，丢了就无法诊断，也无法复现。
#   **一道说「红了」却不说「红在哪」的门，几乎没用。**
#   [[a-refusal-to-check-prints-one-error]]｜[[harness-resets-only-half-the-sandbox]]
FAIL_TAIL_LINES = 25          # 红件保留多少行原始输出

# ★★★ **必须独占跑的测试**：带**墙钟断言**的那些。
#   2026-08-18 实测：全套 19 件里**只有一件**有 `assertLess(elapsed, …)` ——
#   `test_checkers_actually_run.py` 的「全量扫一遍要 <90 秒」。
#   它同时还有一个 180 秒的单件超时（全 89 件安静时实测 10.3 秒，17 倍余量）。
#   并行跑时这两个数量的都不是判据，**是机器负载**：
#   4 路那两次跑，一次 0 盏假超时、一次 1 盏，红的都是它。
#   ⇒ 放到并行批之后单独跑，机器安静了它的断言才有意义。
#   ★ 这不是「把红灯关掉」：它照样会红，只是红的时候真的代表慢。
#   [[harness-limits-masquerade-as-product-defects]]｜[[changing-the-sampling-unit-changes-the-ruler]]
SERIAL_ONLY = frozenset({"test_checkers_actually_run.py"})


def run_one(path):
    t = time.time()
    r = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
    raw = (r.stdout + r.stderr).strip()
    tail = [l for l in raw.splitlines() if l.strip()]
    # 绿件只回一行摘要；**红件把原始输出一起回去**，由调用方打出来
    detail = "" if r.returncode == 0 else "\n".join(tail[-FAIL_TAIL_LINES:])
    # ★★★ **超时不是回归。** 2026-08-17 实测：本件 8 路并行把机器压到测试自己的
    #   `run_script` 超时（`subprocess.TimeoutExpired`），于是把**试验台自己造成的**
    #   压力报成「新回归」——两次连跑的失败集合还不一样（1 件 vs 4 件）。
    #   ⇒ 单独拎出来标注，不混进「新回归」。[[harness-limits-masquerade-as-product-defects]]
    timed_out = "TimeoutExpired" in raw
    return r.returncode, (tail[-1][:60] if tail else ""), time.time() - t, detail, timed_out


def selftest() -> int:
    bad = []
    files = discover()
    if not files:
        # ★ 空扫描面不算通过
        print("  ✗ tests/ 下一件 test_*.py 都没有 —— **未检查，不是通过**")
        return 1
    if len(files) < 5:
        bad.append("只发现 %d 件测试，少得可疑（应为十几件）" % len(files))
    # ★ 已知名单里的文件必须真实存在，否则名单会悄悄长草
    for name in KNOWN:
        if not (TESTS / name).is_file():
            bad.append("已知名单里的 %s 不存在 —— **名单陈旧**" % name)
    # ★ 每条已知项都要有理由
    for name, why in KNOWN.items():
        if not why or len(why) < 20:
            bad.append("%s 没有写清为什么还红着" % name)
    checks = 3
    # ★★★ SERIAL_ONLY 的名单必须**真实存在**，且**确实是带墙钟断言的那些**——
    #   否则它就成了一个「把某件挪到最后」的无理由特例，下次没人知道为什么。
    #   这里**现扫**，不写死：名单与实况对不上就报出来。
    wallclock = set()
    for p in files:
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "assertLess(elapsed" in src or "assertLess(\n" in src and "elapsed" in src:
            wallclock.add(p.name)
    checks += 2
    for name in SERIAL_ONLY:
        if not (TESTS / name).is_file():
            bad.append("SERIAL_ONLY 里的 %s 不存在 —— **名单陈旧**" % name)
    missing = wallclock - SERIAL_ONLY
    if missing:
        bad.append("这些测试有墙钟断言却**没进 SERIAL_ONLY**，并行会给它们假红：%s"
                   % "、".join(sorted(missing)))
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d（发现 %d 件测试；带墙钟断言 %d 件：%s；独占名单 %d 件）"
          % (checks - len(bad), checks, len(files), len(wallclock),
             "、".join(sorted(wallclock)) or "无", len(SERIAL_ONLY)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="有红就 rc=1")
    ap.add_argument("--allow-known", action="store_true",
                    help="配 --strict：只有**不在已知名单里**的红才 rc=1")
    ap.add_argument("--workers", type=int, default=4,
                    help="并行度（默认 **4**，2026-08-17 实测定的）。"
                         "8 路 3 次跑出 1–4 盏假超时；4 路 2 次跑出 0 和 1 盏 —— "
                         "**是少很多，不是没有**")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    # ★★ **先花 16 秒问一句「清单是不是陈旧的」，再跑那 108 秒。**
    #   2026-08-17 我两次栽在同一件事上：动了随包目录里的字节没跑 build_manifest ⇒
    #   test_skill_contract / test_release_bundle / test_package_install_migrate
    #   三件同时红，而红法**看起来像三个不相干的回归**，我两次都花时间去逐个诊断。
    #   而 `check_contract_drift` 早就会一句话说清：
    #     「[发布清单] **checksums.sha256 与磁盘对不上 1 个文件**：['scripts/xxx.py']」
    #   ⇒ **不是缺执行者（它一直都在），是我的顺序错了。** 这里替调用方先跑一次。
    #   ★ 只提示、不拦截：真有回归时仍要让那三件自己红出来。
    drift = subprocess.run([sys.executable, str(HERE / "check_contract_drift.py")],
                           capture_output=True, text=True)
    # ★★ **别只认自己上次撞见的那一种。** 本预检第一版只 grep
    #   「checksums.sha256 与磁盘对不上」—— 因为那是我写它时刚踩到的那个坑。
    #   当天晚些时候换成**镜像漂移**（scripts/ 改了、references/ 的副本没跟），
    #   同样把那三件验清册的测试拖红，而本预检**一声不吭**。
    #   判据的形状 = 我上一次探查的形状。⇒ 改成**漂移门只要非 0 就全文转述**。
    #   [[my-checkers-are-mis-cut-six-times-in-one-day]]｜[[fixed-the-symptom-kept-the-root-cause]]
    if drift.returncode != 0:
        print("★★ **先别看下面的红**：合同漂移门 rc=%d，它报的是 ——" % drift.returncode)
        for line in drift.stdout.splitlines():
            if line.strip().startswith("- "):
                print("   %s" % line.strip()[:160])
        print("   ⇒ 这几条多半会把验清册的那三件拖红成「不相干的新回归」。"
              "清单陈旧就跑 `build_manifest.py`；镜像不一致就把 scripts/ 那份"
              "拷到 references/pipeline/checkers/。\n")

    files = discover()
    print("扫描面：%s（模式 `test_*.py` + `run_*.py`，**%d 件**）" % (TESTS, len(files)))
    if not files:
        print("✗ 一件都没发现 —— **未检查，不是通过**")
        return 0

    # ★★ **并行跑。** 实测串行整套要 **333.5 秒**（5 分半）——
    #   这正是那件红能留这么久的真原因：**太慢，没人会随手跑**。
    #   14 件互相独立（各自建临时目录、不共享状态），并行是安全的。
    #   ★ 顺序仍按文件名排，输出可比；耗时逐件打印，**下次谁最慢一眼看得见**。
    t0 = time.time()
    results = {}
    # ★★★ 并行度 2026-08-17 实测定为 **4**，不是拍的：
    #       workers=8 → 墙钟 256.6 / 264.1 / 242.8 秒，**假超时 1–4 件**（逐跑还不一样）
    #       workers=4 → 墙钟 324.7s（假超时 **0**）／342.9s（假超时 **1**）
    #   8 路省 ~75 秒（23%），代价是 1–4 盏假红 —— 诊断一盏假红花的时间远超 75 秒。
    #   ★ 它此前自报「串行 333.5s → 并行约 110–150s」**是陈旧的**：三次实测都在 240s 以上。
    #
    #   ★★★ **订正（2026-08-18）**：我按 workers=4 的**第一次**跑就写下了「4 路 0 假红」，
    #     并把它抄进了 VERIFICATION.md 与本文件两处 —— **下一次跑就翻了号**（1 盏假超时）。
    #     一次观测撑不起一个全称判断。[[samples-cannot-support-universal-claims]]
    #     真正的机制在下面 SERIAL_ONLY：假超时**只出在唯一一件带墙钟断言的测试上**。
    _workers = max(1, min(a.workers, len(files)))
    par = [f for f in files if f.name not in SERIAL_ONLY]
    ser = [f for f in files if f.name in SERIAL_ONLY]
    with concurrent.futures.ThreadPoolExecutor(max_workers=_workers) as ex:
        futs = {ex.submit(run_one, f): f for f in par}
        for fut in concurrent.futures.as_completed(futs):
            results[futs[fut]] = fut.result()
    # ★ 独占件在并行批**跑完之后**逐个跑，机器此时是安静的 —— 它们的墙钟断言才有意义
    for f in ser:
        results[f] = run_one(f)

    red, green, fixed, slow = [], [], [], []
    for f in files:
        rc, tail, secs, detail, timed_out = results[f]
        mark = "✓" if rc == 0 else "✗"
        known = f.name in KNOWN
        note = ""
        if rc != 0 and known:
            note = "  ← **已知未决**"
        elif rc != 0 and timed_out:
            note = "  ← **超时（并行压力），不是回归**"
            slow.append(f.name)
        elif rc != 0:
            note = "  ← **新回归**"
            red.append(f.name)
        elif known:
            note = "  ← **已知失败已修复：请把它从 KNOWN 里删掉**"
            fixed.append(f.name)
        if rc == 0:
            green.append(f.name)
        print("  %s rc=%d %6.1fs  %-38s %-40s%s" % (mark, rc, secs, f.name, tail, note))

    print("\n合计：绿 %d｜红 %d（已知未决 %d、**超时 %d**、**新回归 %d**）｜**墙钟 %.1fs**"
          % (len(green), len(files) - len(green),
             len(files) - len(green) - len(red) - len(slow), len(slow), len(red),
             time.time() - t0))
    if slow:
        print("  ★ **超时的 %d 件不是回归** —— 是本件 8 路并行把机器压到测试自己的"
              " `run_script` 超时；实测两次连跑的超时集合**不一样**。%s"
              % (len(slow), "、".join(slow)))
        print("    单独跑它们通常是绿的（`cd tests && python3 <名>.py`）。")
    if KNOWN:
        print("\n已知未决（每条都写明谁能让它变绿）：")
        for n, why in KNOWN.items():
            print("  · %s\n      %s" % (n, why))
    if fixed:
        print("\n★★ **下列已知项已经变绿，名单该缩了**：%s" % "、".join(fixed))
    # ★ 把**红件的原始输出**打出来 —— 否则「红了」是个无法诊断的结论。
    #   尤其：并行才失败的件**单独跑是绿的**，这段输出是唯一证据。
    for _f in files:
        _rc, _t, _s, _detail, _to = results[_f]
        if _rc != 0 and _detail:
            print("\n── %s 的原始输出（末 %d 行）%s" %
                  (_f.name, FAIL_TAIL_LINES, ("  ← 已知未决" if _f.name in KNOWN else
                    "  ← **超时（并行压力）**" if _to else "  ← **新回归**")))
            for _l in _detail.splitlines():
                print("   %s" % _l[:150])

    if red:
        print("\n✗ **新回归 %d 件**：%s" % (len(red), "、".join(red)))

    if a.strict:
        return 1 if (red or (not a.allow_known and len(green) != len(files))) else 0
    return 0          # 默认只报告，永远 rc=0


if __name__ == "__main__":
    sys.exit(main())
