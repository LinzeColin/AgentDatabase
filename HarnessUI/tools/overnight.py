#!/usr/bin/env python3
"""Unattended overnight runner: generate, grade, retry, resume — no operator.

MiniMax Design is a desktop app that holds a session for 30-50 minutes, so it
cannot carry an overnight run no matter how the task pack is written. The two
engines on this machine that *can* run unattended are the mmx CLI and the local
ComfyUI. This drives the mmx CLI.

The trade is explicit: mmx CLI exposes only `image-01`, which scored well below
Midjourney Niji 7 on the pilot. What it buys is throughput while nobody is
awake. Anything it produces is graded by the same gate as everything else and
lands as its own batch, so a weak image never displaces a good one — the
morning's job is to re-shoot rejects on the better engine, not to start over.

Every image is graded the moment it lands. A failure retries only that image,
with the failing clause appended to the prompt as a new constraint, up to
`--max-attempts`. State lives in the runner ledger, so killing this at any
point costs nothing.

Usage:
    python3 overnight.py --pack … --state progress.json --out … --batch v1.4-auto
    python3 overnight.py --pack … --state progress.json --out … --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from runner import DARK_MAX, DARK_MIN, MAX_ATTEMPTS, gate, measure, pick_next, save  # noqa: E402

WIDTH, HEIGHT = 2048, 1152


def build_prompt(unit: dict) -> str:
    """The prompt, plus the correction the previous attempt earned.

    A retry that resends the identical prompt is just another roll of the dice.
    The gate phrases each failure with the fix in a `（下次：…）` clause, so the
    retry carries a constraint the first attempt did not have.
    """
    prompt = unit["prompt"]
    if not unit["fails"]:
        return prompt
    corrections = []
    for fail in unit["fails"]:
        corrections.append(fail.split("（下次：")[-1].rstrip("）") if "（下次：" in fail else fail)
    return prompt + " CORRECTIONS REQUIRED: " + " ".join(corrections)


def generate(unit: dict, pack: Path, out: Path, batch: str, *, timeout: int) -> Path | None:
    """One mmx call. Returns the produced file, or None."""
    character, variant = unit["task"].split("/")[1:]
    prefix = f"{character}-{variant}-{unit['side']}-{batch}"
    command = [
        "mmx", "image", "generate",
        "--prompt", build_prompt(unit),
        "--width", str(WIDTH), "--height", str(HEIGHT),
        "--subject-ref", f"type=character,image={pack / unit['anchor']}",
        "--out-dir", str(out), "--out-prefix", prefix,
        "--quiet", "--non-interactive",
    ]
    before = {p.name for p in out.glob(f"{prefix}*")}
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        return None
    fresh = [p for p in out.glob(f"{prefix}*") if p.name not in before]
    if not fresh:
        return None
    produced = max(fresh, key=lambda p: p.stat().st_mtime)
    final = out / f"{prefix}-a{unit['attempt'] + 1}.png"
    produced.rename(final)
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch", default="auto")
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--pause", type=float, default=2.0)
    parser.add_argument("--stop-after", type=int, help="生成这么多张后停（试跑用）")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    state = json.loads(args.state.read_text(encoding="utf-8"))
    state["max_attempts"] = args.max_attempts
    args.out.mkdir(parents=True, exist_ok=True)

    made = passed = failed = blocked = 0
    started = time.time()
    while True:
        nxt = pick_next(state)
        if nxt is None:
            print("\n全部单元已结算。")
            break
        key, unit = nxt
        if args.stop_after and made >= args.stop_after:
            print(f"\n达到 --stop-after {args.stop_after}，停止。")
            break

        label = f"{unit['task']} [{unit['side']}] a{unit['attempt'] + 1}"
        if args.dry_run:
            print(f"  [dry-run] {label}")
            unit["status"] = "accepted"
            continue

        try:
            produced = generate(unit, args.pack, args.out, args.batch, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            produced = None
        made += 1

        if produced is None:
            unit["attempt"] += 1
            unit["fails"] = ["生成失败或超时"]
            unit["status"] = "retry" if unit["attempt"] < args.max_attempts else "blocked"
            failed += 1
            print(f"  ! {label} 生成失败")
        else:
            metrics = measure(produced)
            fails = gate(metrics, unit["side"])
            unit["attempt"] += 1
            unit["metrics"] = metrics
            unit["fails"] = fails
            if not fails:
                unit["status"] = "accepted"
                unit["accepted_file"] = produced.name
                passed += 1
                print(f"  ✓ {label}  {produced.name}")
            elif unit["attempt"] >= args.max_attempts:
                unit["status"] = "blocked"
                blocked += 1
                print(f"  ⛔ {label} 三次不合格：{'; '.join(fails)[:90]}")
            else:
                unit["status"] = "retry"
                print(f"  ✗ {label}：{'; '.join(fails)[:90]}")

        save(args.state, state)
        elapsed = time.time() - started
        if made and made % 10 == 0:
            print(f"     —— 已生成 {made} 张 · 通过 {passed} · 重试 {failed} · "
                  f"blocked {blocked} · 用时 {elapsed / 60:.0f} 分")
        time.sleep(args.pause)

    print(f"\n生成 {made} · 通过 {passed} · 失败 {failed} · blocked {blocked} · "
          f"用时 {(time.time() - started) / 60:.0f} 分")


if __name__ == "__main__":
    main()
