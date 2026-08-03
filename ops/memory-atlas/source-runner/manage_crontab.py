#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BEGIN = "# BEGIN MEMORY_ATLAS_SOURCE_RUNNER_V31"
END = "# END MEMORY_ATLAS_SOURCE_RUNNER_V31"


def existing() -> str:
    completed = subprocess.run(["crontab", "-l"], text=True, capture_output=True)
    return completed.stdout if completed.returncode == 0 else ""


def remove_block(text: str) -> str:
    output=[]; skipping=False
    for line in text.splitlines():
        if line.strip()==BEGIN: skipping=True; continue
        if line.strip()==END: skipping=False; continue
        if not skipping: output.append(line)
    return "\n".join(output).strip()


def install(text: str) -> None:
    completed = subprocess.run(["crontab", "-"], input=text.rstrip()+"\n", text=True, capture_output=True)
    if completed.returncode:
        raise SystemExit(f"crontab 写入失败：{completed.stderr}")


def main() -> None:
    parser=argparse.ArgumentParser(description="Manage Memory Atlas source-runner crontab without launchd")
    parser.add_argument("command", choices=["install","remove","verify"])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, default=Path.home()/".memory-atlas"/"cron-backups")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args=parser.parse_args()
    repo=args.repo.expanduser().resolve()
    runner=repo/"ops/memory-atlas/source-runner/run_due.py"
    if not runner.is_file(): raise SystemExit("run_due.py 不存在")
    current=existing()
    cleaned=remove_block(current)
    python=args.python.expanduser().resolve()
    if not python.is_file(): raise SystemExit(f"Python interpreter 不存在：{python}")
    (Path.home()/".memory-atlas"/"source-runner").mkdir(parents=True, exist_ok=True)
    command=f'cd "{repo}" && "{python}" -B "{runner}" --repo "{repo}" >> "$HOME/.memory-atlas/source-runner/cron.log" 2>&1'
    block=f"{BEGIN}\n*/30 * * * * {command}\n{END}"
    if args.command=="verify":
        present=BEGIN in current and END in current and str(runner) in current
        print("PASS" if present else "SOURCE_RUNNER_UNBOUND")
        raise SystemExit(0 if present else 2)
    args.backup_dir.expanduser().mkdir(parents=True, exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (args.backup_dir.expanduser()/f"crontab-before-{stamp}.txt").write_text(current,encoding="utf-8")
    if args.command=="remove":
        install(cleaned)
        print("REMOVED")
    else:
        merged=(cleaned+"\n\n"+block).strip()+"\n"
        install(merged)
        verify=existing()
        if BEGIN not in verify or str(runner) not in verify: raise SystemExit("安装后验证失败")
        print("INSTALLED_AND_VERIFIED")

if __name__=="__main__": main()
