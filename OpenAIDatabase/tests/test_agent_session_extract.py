#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_session_extract 的正控与负控。

每条正控都配负控：只证明「正常情况能跑」等于没测 ——
一个永远返回固定结果的抽取器也能过。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "OpenAIDatabase" / "scripts" / "agent_session_extract.py"
sys.path.insert(0, str(SCRIPT.parent))
import agent_session_extract as X  # noqa: E402


def make_session(d: Path, name: str, turns: int = 3) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    f = d / name
    lines = []
    for i in range(turns):
        lines.append(json.dumps({"type": "user", "timestamp": f"2026-08-{10+i:02d}T01:00:00Z",
                                 "message": {"text": f"第{i}个问题 部署上线"}}, ensure_ascii=False))
        lines.append(json.dumps({"type": "assistant", "message": {"text": "好的"},
                                 "toolUseResult": {"x": "y"}}, ensure_ascii=False))
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f


class ExtractTest(unittest.TestCase):

    def test_同名文件在不同目录不能碰撞(self):
        """kimi-code 的 419 个会话**全部叫 wire.jsonl**，只分散在不同目录。
        record_id 只取文件名就会 419 碰成 1，增量去重时塌掉 418 条 ——
        2026-08-19 真踩过，这条是那个缺陷的回归锁。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ids = set()
            for i in range(5):
                f = make_session(root / f"s{i}", "wire.jsonl")
                ev = X.extract_jsonl_session(f, "t")
                self.assertIsNotNone(ev)
                ids.add(ev["record_id"])
            self.assertEqual(len(ids), 5, f"同名文件 record_id 碰撞了: {ids}")

    def test_负控_只用文件名就会碰撞(self):
        """证明上一条测的是真问题：只取 stem 时必然塌成 1 个。"""
        stems = {Path(f"s{i}/wire.jsonl").stem for i in range(5)}
        self.assertEqual(len(stems), 1, "前提失效：文件名本就不同，那条回归锁没有意义")

    def test_抽取保留信号且压缩(self):
        with tempfile.TemporaryDirectory() as td:
            f = make_session(Path(td), "a.jsonl", turns=10)
            ev = X.extract_jsonl_session(f, "t")
            m = ev["behavior_metrics"]
            self.assertEqual(m["user_turn_count"], 10)
            self.assertEqual(m["tool_call_count"], 10)
            self.assertIn("部署上线", ev["topics"])
            out = len(json.dumps(ev, ensure_ascii=False).encode())
            self.assertLess(out, f.stat().st_size, "抽取后反而更大了")

    def test_负控_脱敏必须生效(self):
        secret = "ghp_" + "a" * 30
        text = f"我的 token 是 {secret}，路径 {Path.home()}/x"
        red = X.redact(text)
        self.assertNotIn(secret, red, "凭据没被脱敏")
        self.assertNotIn(str(Path.home()), red, "家目录路径没被脱敏")

    def test_增量幂等(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "src", Path(td) / "out"
            for i in range(3):
                make_session(src / f"d{i}", "wire.jsonl")
            X.SOURCES["_t"] = {"root": src, "parser": "jsonl_dir", "payload_mb": 0}
            try:
                a = X.extract_source("_t", out, incremental=True)
                b = X.extract_source("_t", out, incremental=True)
                self.assertEqual(a["events"], 3)
                self.assertEqual(b["events"], 3, "增量第二次事件数变了")
                self.assertEqual(b["rescanned"], 0, "没有变化却重算了")
            finally:
                X.SOURCES.pop("_t", None)

    def test_负控_文件变了必须重算(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "src", Path(td) / "out"
            f = make_session(src, "wire.jsonl")
            X.SOURCES["_t2"] = {"root": src, "parser": "jsonl_dir", "payload_mb": 0}
            try:
                X.extract_source("_t2", out, incremental=True)
                import os, time
                f.write_text(f.read_text(encoding="utf-8") + json.dumps(
                    {"type": "user", "message": {"text": "新增一句 赚钱"}}) + "\n", encoding="utf-8")
                os.utime(f, (time.time() + 10, time.time() + 10))
                r = X.extract_source("_t2", out, incremental=True)
                self.assertEqual(r["rescanned"], 1, "文件变了却没重算 —— 增量是假的")
            finally:
                X.SOURCES.pop("_t2", None)

    def test_零外部依赖(self):
        """0 agent 0 token 的前提：不许引入任何第三方库或网络调用。"""
        import ast
        src = SCRIPT.read_text(encoding="utf-8")
        for bad in ("requests", "urllib.request", "openai", "anthropic", "httpx"):
            self.assertNotIn(bad, src, f"引入了 {bad} —— 破坏零依赖零 token")
        ast.parse(src)


if __name__ == "__main__":
    unittest.main()
