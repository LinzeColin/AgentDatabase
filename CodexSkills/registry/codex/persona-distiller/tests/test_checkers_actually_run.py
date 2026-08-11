from __future__ import annotations

import subprocess
import sys
import time
import unittest

from helpers import ROOT

# 真跑一遍的上限。全 89 件实测 10.3 秒；单件最慢 check_contract_drift 5.3 秒
# （它自己还会再起一个子进程）。给到 180 秒是为了留出慢盘余量，不是预期值。
_PER_CHECKER_TIMEOUT = 180

_TRACEBACK = 'Traceback (most recent call last)'


class CheckersActuallyRunTests(unittest.TestCase):
    """**判据必须真的跑得起来**——不是「能 import」，是「按入口跑一遍不崩」。

    回归的是 [[a-checker-nothing-calls-is-not-a-checker]] 的第五种形态：
    `py_compile` 绿、`--list` 绿，**工具一跑就 NameError**——
    缺的那个 import 两个检查都碰不到，因为它们都不经过被保证之物。

    同族还有一条更贵的：94/100 件判据的 `--self-test` 不经过 `main()`，
    于是 argparse 层、模块级常量、跨函数引用**全在自测射程之外**。
    本测试补的就是这一格：**按真实入口起进程**，只断言一件事——没有未捕获的崩溃。

    ★ 只断言「不崩」，**不断言「无发现」**：判据报出问题是它的本职。
      在缺目录的干净克隆上，判据应当友好退出（有话说、无 traceback）；
      若它反而抛栈，那正是接手方第一天会撞上的东西，此测试就该红。
      ⇒ 与 [[untested-fallback-branches-only-fire-on-their-machine]] 同一个用意。
    """

    def test_every_checker_runs_without_an_uncaught_crash(self) -> None:
        checkers = sorted(ROOT.glob('scripts/check_*.py'))
        self.assertGreaterEqual(len(checkers), 80, '判据数量骤降，先确认不是 glob 写错了')

        crashed: list[str] = []
        for path in checkers:
            try:
                proc = subprocess.run(
                    [sys.executable, str(path)],
                    capture_output=True, text=True, cwd=str(ROOT),
                    timeout=_PER_CHECKER_TIMEOUT,
                )
            except subprocess.TimeoutExpired:
                crashed.append(f'{path.name}: 超过 {_PER_CHECKER_TIMEOUT} 秒没跑完')
                continue

            # ★ 只认 stderr 里的真 traceback。**不要**去 grep stdout 里的
            #   "NameError"/"ModuleNotFoundError" 字样——写这条测试时我就是那样
            #   误报了一件：check_contract_drift 的正常输出里有一句
            #   「delivery_builder.py 起不来是按设计如此：ModuleNotFoundError…」，
            #   那是它在**说明**跳过的理由，不是它自己崩了。
            #   ⇒ [[read-the-hits-before-reporting-the-rate]]
            if _TRACEBACK in (proc.stderr or ''):
                tail = (proc.stderr or '').strip().splitlines()[-1]
                crashed.append(f'{path.name}: 抛栈（rc={proc.returncode}）{tail[:160]}')
            elif proc.returncode < 0:
                crashed.append(f'{path.name}: 被信号 {-proc.returncode} 杀死')

        self.assertEqual(crashed, [], '这些判据按入口跑一遍就崩：\n  ' + '\n  '.join(crashed))

    def test_the_whole_sweep_is_cheap_enough_to_keep_running(self) -> None:
        """**这条是给上一条兜底的**：扫一遍要是变慢到几分钟，下一个人就会把它注释掉。

        实测 **30.3 秒 / 90 件**（2026-08-12 现算）。90 秒的闸——不是性能指标，
        是「别让它悄悄退化成没人跑」。

        ★ 这一天里它就涨了三倍（10.3 → 30.3 秒），涨在两件上，**都是有意的**：
          · `check_selftest_reach` 10.0 秒——它要起 89 个子进程各跑一遍自测
          · `check_contract_drift` 15.2 秒——它现在会转调上面那件
          写下来是因为**下一个看到 30 秒的人应该知道钱花在哪**，
          而不是先怀疑哪里退化了。
        """
        checkers = sorted(ROOT.glob('scripts/check_*.py'))
        start = time.time()
        for path in checkers:
            subprocess.run([sys.executable, str(path)], capture_output=True, text=True,
                           cwd=str(ROOT), timeout=_PER_CHECKER_TIMEOUT)
        elapsed = time.time() - start
        self.assertLess(elapsed, 90.0,
                        f'全量跑判据要 {elapsed:.1f} 秒（实测基线 10.3 秒）——'
                        '慢下来的那件要么在下载、要么在扫不该扫的东西')


if __name__ == '__main__':
    unittest.main()
