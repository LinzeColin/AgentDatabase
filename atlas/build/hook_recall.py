#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hook_recall.py —— UserPromptSubmit 钩子。提问那一刻把踩过的坑摆出来。

装法（`~/.claude/settings.json`）：

    "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command",
      "command": "python3 ~/.memory-atlas/web/atlas/build/hook_recall.py"}]}]}

■ 三条不许违反的
  1. **绝不阻断提问。** 任何异常都当作「没命中」，exit 0，不输出。
     一个会让人问不了问题的沉淀系统，比没有沉淀更糟。
  2. **没命中就一个字都不输出。** 官方对钩子成本的原话是
     「Zero, unless the hook returns output」—— 空输出才是零成本。
  3. **不调用任何模型。** 全程只有 BM25 算术和文件读取。

■ 为什么不做成「让 agent 自己去查」
  【实测 2026-08-20】上一版注入的是一个 `gh api` 地址。本次会话里
  调研 agent 全程没执行过那条命令 —— 转化率 0。给地址等于没给。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_INDEX = Path(os.environ.get(
    "ATLAS_BRIEF_INDEX",
    str(Path(os.environ.get("ATLAS_WORK", str(Path.home() / ".memory-atlas")))
        / "brief_index.jsonl")))


def main() -> int:
    try:
        raw = sys.stdin.read()
        prompt = (json.loads(raw) or {}).get("prompt") or ""
    except Exception:
        return 0                       # 读不懂就当没这回事
    if not prompt.strip():
        return 0
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from recall import recall
        text = recall(prompt, DEFAULT_INDEX)
    except Exception:
        return 0                       # 检索炸了也不许挡住用户提问
    if not text:
        return 0                       # 没命中 = 零输出 = 零成本
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": text,
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
