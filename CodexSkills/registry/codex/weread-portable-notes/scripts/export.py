#!/usr/bin/env python3
"""围绕共享“微信读书笔记迁移”Node 命令行的轻量安全包装器。"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通过共享“微信读书笔记迁移”核心导出个人微信读书笔记。")
    parser.add_argument("--app", required=True, help="MetaDatabase/WeReadPort 的绝对路径")
    parser.add_argument("--profile", default="portable", choices=("portable", "gfm", "obsidian", "notion"))
    parser.add_argument("--output", required=True)
    parser.add_argument("--book", action="append", default=[])
    parser.add_argument("--previous")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--include-cover", action="store_true")
    parser.add_argument("--no-offline-search", action="store_true")
    parser.add_argument("--no-reading-stats", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = Path(args.app).expanduser().resolve()
    cli = app / "scripts" / "export-cli.js"
    package = app / "package.json"
    if not cli.is_file() or not package.is_file():
        print(f"错误：未找到“微信读书笔记迁移”应用： {app}", file=sys.stderr)
        return 2
    if not args.demo and not os.environ.get("WEREAD_API_KEY"):
        print("错误：请只在当前本地终端设置 WEREAD_API_KEY；不得作为命令参数传入或粘贴到聊天。", file=sys.stderr)
        return 2
    command = ["node", str(cli), "--profile", args.profile, "--output", str(Path(args.output).expanduser())]
    if args.demo:
        command.append("--demo")
    for book_id in args.book:
        command.extend(("--book", book_id))
    if args.previous:
        command.extend(("--previous", str(Path(args.previous).expanduser())))
    if args.include_cover:
        command.append("--include-cover")
    if args.no_offline_search:
        command.append("--no-offline-search")
    if args.no_reading_stats:
        command.append("--no-reading-stats")
    # Never print the environment or the key. The Node CLI also refuses key arguments.
    completed = subprocess.run(command, cwd=app, env=os.environ.copy(), check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
