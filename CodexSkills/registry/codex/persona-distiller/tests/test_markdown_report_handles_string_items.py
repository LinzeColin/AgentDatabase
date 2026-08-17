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


if __name__ == "__main__":
    unittest.main(verbosity=2)
