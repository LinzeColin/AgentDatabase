#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`show_gate` 渲染 `quality_check` 的输出时，**两种形状都得收**。

## 它守的那件事（2026-08-18 实测·工具侧不升版）

`quality_check` **两种形状都发**（静态现数）：

    warnings.append({...})  1 处 ｜ warnings.append("...")  **4 处**
    errors.append({...})    1 处 ｜ errors.append("...")    **3 处**

而 `show_gate.render` 原本只按 dict 处理 ⇒ 撞上裸字符串就

    AttributeError: 'str' object has no attribute 'get'

**实测在 Rousseau 的真工作区上必炸** —— 它的 research 档 warnings 恰好是那条裸字符串。

★ **同一个形状差异对两个消费者一冷一热**：吃 JSON 的下游毫发无伤，
  渲染给人看的这一个直接死。[[same-parse-bug-fatal-to-one-consumer-harmless-to-another]]

★★ **不把裸字符串悄悄格式化掉** —— 那会把「生产者形状不一致」藏起来。
  标 `(无 code)` 并在末尾汇总条数，让**按 code 做过滤/统计的人**知道自己会漏。
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

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
