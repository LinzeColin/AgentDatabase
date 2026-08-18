#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`--write-report` 的 `.md` 那一半 —— **它崩了很久，而没有任何测试跑过它**。

## 抓到它的那一次（2026-08-17）

在冻结工作区副本上验 ㊵ 守卫，顺手测 `--write-report`：只落了 `.json`，没有 `.md`。
stderr：

    File ".../quality_check.py", line 4585, in main
      atomic_write_text(... markdown_report(data) ...)
    File ".../quality_check.py", line 616, in markdown_report
      lines.extend([f'- `{item["code"]}`: {item["message"]}' for item in data['warnings']] ...)
    TypeError: string indices must be integers

**`errors` / `warnings` 里的条目不都是 dict，有的是纯字符串**
（实测 seth-godin 的 5 条 warning 里有 1 条）。于是：

* `.md` **从来没产出过**；
* 崩在 `print(json.dumps(data))` **之前** ⇒ 连 stdout 的报告也没有；
* rc=1 读起来像「门红了」，**其实是崩溃**。

## 为什么没人发现

`--write-report` 在全仓**没有任何测试**跑过。而 `init_target.py:217` 给每个新人物
生成的操作手册里写的正是

    python3 scripts/quality_check.py <target> --phase research --write-report

`publish_jl.sh:14` 也在用。**一条写进每份手册的命令，零测试。**
[[every-requirement-needs-an-owner]]｜[[a-checker-nothing-calls-is-not-a-checker]]

★ 本仓早记过「errors 的条目可能是纯字符串」，当时**只修了读的那一侧**；
  写的这一侧一直没修。[[one-requirement-two-consumers]]
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_r = subprocess.run(["git", "-C", str(pathlib.Path(__file__).resolve().parent),
                     "rev-parse", "--show-toplevel"], capture_output=True, text=True)
REPO = pathlib.Path(_r.stdout.strip()) if _r.returncode == 0 else pathlib.Path(".").resolve()
PD = REPO / "CodexSkills/registry/codex/persona-distiller"
sys.path.insert(0, str(PD / "scripts"))


def _payload(errors, warnings):
    """够 `markdown_report` 用的最小 data。字段名照它真实读的那些写。"""
    return {"schema_version": "1.0", "target": "/tmp/x", "phase": "release",
            "profile": "standard", "generated_at": "2026-08-17T00:00:00Z",
            "passed": False, "strict": False, "metrics": {}, "checks": [],
            "errors": errors, "warnings": warnings}


class MarkdownReportHandlesStringItems(unittest.TestCase):
    """`markdown_report` 必须同时认 dict 条目与纯字符串条目。"""

    @classmethod
    def setUpClass(cls):
        # ★★★ 不要写 `cls.md = markdown_report` —— 普通函数挂到类上会变成绑定方法，
        #   调用时 `self` 被当成第一个参数：`takes 1 positional argument but 2 were given`。
        #   我第一版就这么写，6 个测试**在没变异时全 error**；
        #   幸好先看了基线，否则那次变异对照就是假绿。用 staticmethod 包一层。
        from quality_check import markdown_report
        cls.md = staticmethod(markdown_report)

    def test_dict_items_render_with_code_and_message(self):
        out = self.md(_payload([{"code": "a.b", "message": "boom"}], []))
        self.assertIn("`a.b`", out)
        self.assertIn("boom", out)

    def test_string_warning_does_not_crash(self):
        """★★★ 这正是抓到的那一次：纯字符串 warning ⇒ 原写法 TypeError。"""
        out = self.md(_payload([], ["research.lane_quotes：36 条逐字引文回原文对不上"]))
        self.assertIn("lane_quotes", out)

    def test_string_error_does_not_crash(self):
        """★★ 另一侧同样要认 —— 这次 errors 恰好全是 dict，不改就是等下一次。"""
        out = self.md(_payload(["data.parse：某处炸了"], []))
        self.assertIn("data.parse", out)

    def test_mixed_dict_and_string(self):
        out = self.md(_payload([{"code": "e.1", "message": "m1"}, "e.2 纯字符串"],
                               ["w.1 纯字符串", {"code": "w.2", "message": "m2"}]))
        for token in ("`e.1`", "e.2 纯字符串", "w.1 纯字符串", "`w.2`"):
            self.assertIn(token, out)

    def test_dict_missing_keys_does_not_crash(self):
        """★ dict 缺 code/message 也不许炸（用 .get 不用 []）。"""
        out = self.md(_payload([{}], [{"code": "only-code"}]))
        self.assertIn("only-code", out)

    def test_empty_lists_say_none(self):
        """★ 反对照：两边都空时要说 None，不是什么都不印。"""
        out = self.md(_payload([], []))
        self.assertIn("- None", out)




# ══════════════════════════════════════════════════════════════════════════
# 并入自 test_show_gate_survives_mixed_shapes.py（2026-08-19）
#
# ★ 为什么并进来，而不是留成独立文件：
#   包内文件数硬上限 ≤500（`scripts/self_check.py:136`），而 2026-08-18 的提交
#   029a19699 加那个测试时把包从 500 顶到 **501** —— 当时没重跑文件数门，没人看见。
#   按仓里已有的裁定「**没有抬那道门** —— 为塞进自己的文件去放宽判据，
#   正是本仓一直在挑的毛病」，**测试一条不删，并进主题相邻的这一件**。
#
# ★★ 两者守的是同一族缺陷：**生产者同时发 dict 和裸字符串，而消费者只认 dict**。
#   上半件守 `markdown_report`，下半件守 `show_gate.render` —— 同一个 quality_check
#   输出，两个消费者各崩过一次（[[one-requirement-two-consumers]]）。
# ══════════════════════════════════════════════════════════════════════════

BASE = {"passed": False, "phase": "research", "profile": "quick", "strict": False,
        "target": "x", "metrics": {}, "checks": {},
        "schema_version": "1", "generated_at": "t"}


class ShowGateSurvivesMixedShapes(unittest.TestCase):

    def _render(self, errors, warnings):
        from show_gate import render
        return render({**BASE, "errors": errors, "warnings": warnings})

    def test_bare_string_warning_does_not_crash(self):
        """★★★ 这就是实测炸掉的那一幕。"""
        _ok, text = self._render([], ["裸字符串告警"])
        self.assertIn("裸字符串告警", text)

    def test_bare_string_error_does_not_crash(self):
        """★ errors 那条路同样有裸字符串（静态数出 3 处），只是我的工作区没触发。"""
        _ok, text = self._render(["裸字符串错误"], [])
        self.assertIn("裸字符串错误", text)

    def test_dict_shape_still_shows_its_code(self):
        """★ 反对照：dict 形状不许被新写法弄丢 code。"""
        _ok, text = self._render([{"code": "e.dict", "message": "m"}], [])
        self.assertIn("e.dict", text)

    def test_bare_ones_are_counted_and_disclosed(self):
        """★★ 不许悄悄格式化掉 —— 条数要汇总，且要点明「按 code 过滤会漏」。"""
        _ok, text = self._render(["a", {"code": "c", "message": "m"}], ["b"])
        self.assertIn("(无 code)", text)
        self.assertIn("**2** 条", text)
        self.assertIn("过滤", text)

    def test_no_bare_ones_means_no_extra_line(self):
        """★ 全是 dict 时不许加噪声。"""
        _ok, text = self._render([{"code": "c", "message": "m"}], [])
        self.assertNotIn("(无 code)", text)
        self.assertNotIn("没有 `code`", text)

    def test_producer_really_emits_both_shapes(self):
        """★★★ 本件的全部前提：生产者**确实**两种都发。它哪天统一了，这里要重写。"""
        import re
        src = (ROOT / "scripts" / "quality_check.py").read_text(encoding="utf-8")
        bare = len(re.findall(r'(?:warnings|errors)\.append\(\s*(?:f?["\'])', src))
        self.assertGreater(bare, 0,
                           "生产者已经不发裸字符串了 ⇒ 本件的前提没了，去重新量一次再决定留不留")

if __name__ == "__main__":
    unittest.main(verbosity=2)
