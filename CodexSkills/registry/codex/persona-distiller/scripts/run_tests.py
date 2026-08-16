#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `tests/` 下的 15 件测试**真的跑一遍**，并把已知未决与新回归分开。

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
    return sorted(TESTS.glob("test_*.py")) if TESTS.is_dir() else []


def run_one(path):
    t = time.time()
    r = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
    tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    return r.returncode, (tail[-1][:60] if tail else ""), time.time() - t


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
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d（发现 %d 件测试）" % (3 - len(bad), 3, len(files)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="有红就 rc=1")
    ap.add_argument("--allow-known", action="store_true",
                    help="配 --strict：只有**不在已知名单里**的红才 rc=1")
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
    print("扫描面：%s（**%d 件**）" % (TESTS, len(files)))
    if not files:
        print("✗ 一件都没发现 —— **未检查，不是通过**")
        return 0

    # ★★ **并行跑。** 实测串行整套要 **333.5 秒**（5 分半）——
    #   这正是那件红能留这么久的真原因：**太慢，没人会随手跑**。
    #   14 件互相独立（各自建临时目录、不共享状态），并行是安全的。
    #   ★ 顺序仍按文件名排，输出可比；耗时逐件打印，**下次谁最慢一眼看得见**。
    t0 = time.time()
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(files))) as ex:
        futs = {ex.submit(run_one, f): f for f in files}
        for fut in concurrent.futures.as_completed(futs):
            results[futs[fut]] = fut.result()

    red, green, fixed = [], [], []
    for f in files:
        rc, tail, secs = results[f]
        mark = "✓" if rc == 0 else "✗"
        known = f.name in KNOWN
        note = ""
        if rc != 0 and known:
            note = "  ← **已知未决**"
        elif rc != 0:
            note = "  ← **新回归**"
            red.append(f.name)
        elif known:
            note = "  ← **已知失败已修复：请把它从 KNOWN 里删掉**"
            fixed.append(f.name)
        if rc == 0:
            green.append(f.name)
        print("  %s rc=%d %6.1fs  %-38s %-40s%s" % (mark, rc, secs, f.name, tail, note))

    print("\n合计：绿 %d｜红 %d（其中已知未决 %d、**新回归 %d**）｜**墙钟 %.1fs**"
          " —— 串行跑同一批实测 333.5s"
          % (len(green), len(files) - len(green),
             len(files) - len(green) - len(red), len(red), time.time() - t0))
    if KNOWN:
        print("\n已知未决（每条都写明谁能让它变绿）：")
        for n, why in KNOWN.items():
            print("  · %s\n      %s" % (n, why))
    if fixed:
        print("\n★★ **下列已知项已经变绿，名单该缩了**：%s" % "、".join(fixed))
    if red:
        print("\n✗ **新回归 %d 件**：%s" % (len(red), "、".join(red)))

    if a.strict:
        return 1 if (red or (not a.allow_known and len(green) != len(files))) else 0
    return 0          # 默认只报告，永远 rc=0


if __name__ == "__main__":
    sys.exit(main())
