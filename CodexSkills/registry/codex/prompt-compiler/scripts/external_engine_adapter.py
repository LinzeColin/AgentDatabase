#!/usr/bin/env python3
"""外部优化器通用桥模板。

复制本文件后，把 optimize() 替换为实际 DSPy/MIPROv2、Opik、MLflow、
OpenAI、Anthropic、Google、PromptHub 或 PromptLayer 调用。输入来自标准输入，
输出只能是一个 JSON 对象。最终测试与发布裁决始终由 Prompt Compiler 掌握。
"""
from __future__ import annotations

import json
import sys
from typing import Any


def optimize(payload: dict[str, Any]) -> list[dict[str, Any]]:
    seed = str(payload.get("seed_candidate", ""))
    if not seed:
        raise ValueError("缺少 seed_candidate")
    # 安全默认：未连接真实外部优化器时只返回原文副本，主控会去重并拒绝假提升。
    return [{"content": seed, "metadata": {"status": "NOT_CONNECTED"}}]


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        candidates = optimize(payload)
        print(json.dumps({"candidates": candidates, "metadata": {"adapter": "template"}}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
