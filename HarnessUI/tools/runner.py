#!/usr/bin/env python3
"""The night watchman: keeps the state so a 30-minute session is never wasted.

MiniMax Design cannot be driven headlessly and reportedly holds for 30-50
minutes per session, so "run 594 images unattended" is not on the table. What
*is* on the table is making every interruption cost nothing: the generator does
one image, the watchman checks it the moment it lands, records the verdict, and
prints the next single work order. Stop anywhere and `resume` picks up on the
exact image that was in flight.

Three rules, taken from what went wrong when this was done by hand:

*   **Check on arrival, not at the end.** The first pilot produced ten images
    before anyone noticed every dark version was unusable at 0.12-0.23
    brightness. A per-image gate would have caught it on image two.
*   **Retry only the failing image.** Never the batch, never the character.
    Anything already passed is frozen.
*   **Every retry carries a new constraint.** A retry with the same prompt is
    a coin flip; the ledger records what was tightened, so attempt 3 is not a
    re-roll of attempt 1. (Observed: an over-corrected retry pushed a dark
    version from 0.43 to 0.56 and out the other side of the band.)

Usage:
    python3 runner.py init   --pack … --out … --batch v1.3
    python3 runner.py next   --state progress.json
    python3 runner.py watch  --state progress.json          # 落盘即判，自动推进
    python3 runner.py status --state progress.json
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageStat
except ImportError:
    raise SystemExit("需要 Pillow：python3 -m pip install Pillow")

DARK_MIN, DARK_MAX = 0.28, 0.50
LIGHT_MIN = 0.55
RIGHT_DETAIL_MAX = 14.0
SPILL_MAX = 0.55
MAX_ATTEMPTS = 3
SIDES = ("light", "dark")


def measure(path: Path) -> dict:
    with Image.open(path) as image:
        width, height = image.size
        grey = image.convert("L")
        brightness = ImageStat.Stat(grey).mean[0] / 255
        right = grey.crop((int(width * 0.35), 0, width, height)).resize((800, 450))
        left = grey.crop((0, 0, int(width * 0.35), height)).resize((400, 450))
        mid = grey.crop((int(width * 0.35), 0, int(width * 0.62), height)).resize((400, 450))
        edges = lambda im: ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).mean[0]
        right_edge, left_edge, mid_edge = edges(right), edges(left), edges(mid)
    return {"width": width, "height": height, "brightness": round(brightness, 3),
            "right_edge": round(right_edge, 1),
            "spill": round(mid_edge / left_edge, 3) if left_edge else None}


def gate(metrics: dict, side: str) -> list[str]:
    """Machine gate. Returns the failed clauses, each with the constraint to add."""
    fails = []
    if abs(metrics["width"] / metrics["height"] - 16 / 9) > 0.01:
        fails.append("B1 比例不是 16:9")
    if metrics["width"] < 2048:
        fails.append(f"B2 宽度 {metrics['width']} < 2048")
    if metrics["right_edge"] > RIGHT_DETAIL_MAX:
        fails.append(f"C3 右侧细节 {metrics['right_edge']} > {RIGHT_DETAIL_MAX}"
                     "（下次：右侧只要天空与水面，去掉一切远景物件）")
    if metrics["spill"] is not None and metrics["spill"] > SPILL_MAX:
        fails.append(f"C2 主体溢出比 {metrics['spill']} > {SPILL_MAX}"
                     "（下次：把人物再往左压，飘发收进左 35%）")
    if side == "dark":
        level = metrics["brightness"]
        if level < DARK_MIN:
            fails.append(f"G1 暗版过暗 {level}（下次：提高主体主光，整体亮度目标 0.35 左右）")
        elif level > DARK_MAX:
            fails.append(f"G1 暗版过亮 {level}（下次：压低天空亮度，保留主体打光，目标 0.35 左右）")
    elif metrics["brightness"] < LIGHT_MIN:
        fails.append(f"G1b 白昼版偏暗 {metrics['brightness']}（下次：提高整体曝光）")
    return fails


def unit_key(task: dict, side: str) -> str:
    return f"{task['id']}|{side}"


def cmd_init(args: argparse.Namespace) -> None:
    manifest = json.loads((args.pack / "manifest.json").read_text(encoding="utf-8"))
    units = {}
    for task in manifest["tasks"]:
        for side in SIDES:
            units[unit_key(task, side)] = {
                "task": task["id"], "side": side, "anchor": task["anchor"],
                "prompt": task["outputs"][side]["prompt"],
                "expected": task["outputs"][side]["file"],
                "attempt": 0, "status": "pending", "fails": [], "metrics": None,
                "accepted_file": None,
            }
    state = {
        "batch": args.batch or manifest.get("batch", "v1"),
        "pack": str(args.pack), "out": str(args.out),
        "pack_version": manifest.get("version"),
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        # Epoch cut-off: files older than this belong to an earlier batch.
        "since": args.since if args.since is not None else time.time(),
        "max_attempts": MAX_ATTEMPTS,
        "units": units,
    }
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"账本已建：{len(units)} 个任务单元（{len(manifest['tasks'])} 变体 × 2）→ {args.state}")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, state: dict) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def pick_next(state: dict) -> tuple[str, dict] | None:
    """First unit still owed work. Order is manifest order, so it is resumable."""
    for key, unit in state["units"].items():
        if unit["status"] in ("pending", "retry"):
            return key, unit
    return None


def print_order(key: str, unit: dict, state: dict) -> None:
    print(f"\n── 下一张 ───────────────────────────────")
    print(f"任务   {unit['task']}   [{unit['side']}]")
    print(f"批次   {state['batch']}    第 {unit['attempt'] + 1} 次尝试")
    print(f"锚图   {unit['anchor']}")
    print(f"输出   {unit['expected']}")
    if unit["fails"]:
        print("上一次不合格，本次必须收紧：")
        for fail in unit["fails"]:
            print(f"  · {fail}")
    print(f"\nPROMPT:\n{unit['prompt']}\n")


def cmd_next(args: argparse.Namespace) -> None:
    state = load(args.state)
    nxt = pick_next(state)
    if nxt is None:
        print("没有待办单元了。")
        return
    print_order(*nxt, state)


def find_arrival(out_dir: Path, unit: dict, batch: str, since: float) -> Path | None:
    """Locate the file the generator just wrote for this unit.

    Accepts both the nested path from the spec and the flat
    `<character>-<variant>-<side>[-aN].png` shape the generator has actually
    been producing, so the watchman works with what exists rather than only
    with what was asked for.
    """
    expected = out_dir.parent / unit["expected"]
    if expected.exists():
        return expected
    character, variant = unit["task"].split("/")[1:]
    pattern = re.compile(rf"^{re.escape(character)}-{re.escape(variant)}-{unit['side']}"
                         rf"(-{re.escape(batch.replace('.', ''))})?(-a\d+)?\.png$")
    # Only files written after this batch started count. Without the cut-off the
    # watchman adopted a previous batch's output as the current attempt — a
    # v1.0 image was graded, failed, and blocked a unit that had never been run.
    candidates = [p for p in out_dir.glob("*.png")
                  if not p.name.startswith("._") and pattern.match(p.name)
                  and p.stat().st_mtime >= since]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def judge_unit(key: str, unit: dict, state: dict, out_dir: Path) -> bool:
    """Grade one arrived image; returns True when the unit advanced."""
    found = find_arrival(out_dir, unit, state["batch"], state["since"])
    if found is None:
        return False
    try:
        metrics = measure(found)
    except Exception as error:
        unit["status"] = "retry"
        unit["fails"] = [f"读取失败：{str(error)[:60]}"]
        return True

    fails = gate(metrics, unit["side"])
    unit["attempt"] += 1
    unit["metrics"] = metrics
    unit["fails"] = fails
    if not fails:
        unit["status"] = "accepted"
        unit["accepted_file"] = found.name
        print(f"  ✓ {unit['task']} [{unit['side']}]  第 {unit['attempt']} 次通过  {found.name}")
    elif unit["attempt"] >= state.get("max_attempts", MAX_ATTEMPTS):
        unit["status"] = "blocked"
        print(f"  ⛔ {unit['task']} [{unit['side']}]  {unit['attempt']} 次仍不合格，标记 blocked")
        for fail in fails:
            print(f"       {fail}")
    else:
        unit["status"] = "retry"
        print(f"  ✗ {unit['task']} [{unit['side']}]  第 {unit['attempt']} 次不合格，需重出")
        for fail in fails:
            print(f"       {fail}")
    return True


def cmd_watch(args: argparse.Namespace) -> None:
    state = load(args.state)
    out_dir = Path(state["out"])
    print(f"守夜中：{out_dir}\n每张落盘即判，通过就推进，不合格就给出收紧条件。Ctrl-C 退出。")
    nxt = pick_next(state)
    if nxt:
        print_order(*nxt, state)
    while True:
        nxt = pick_next(state)
        if nxt is None:
            print("\n全部单元已结算。")
            break
        key, unit = nxt
        before = unit["attempt"]
        if judge_unit(key, unit, state, out_dir) and unit["attempt"] != before:
            save(args.state, state)
            following = pick_next(state)
            if following:
                print_order(*following, state)
        time.sleep(args.poll)


def cmd_status(args: argparse.Namespace) -> None:
    state = load(args.state)
    tally: dict[str, int] = {}
    blocked = []
    for key, unit in state["units"].items():
        tally[unit["status"]] = tally.get(unit["status"], 0) + 1
        if unit["status"] == "blocked":
            blocked.append((key, unit["fails"]))
    total = len(state["units"])
    done = tally.get("accepted", 0)
    print(f"批次 {state['batch']} · 包 {state['pack_version']}")
    print(f"  已通过 {done}/{total} ({done / total * 100:.0f}%)")
    for status in ("pending", "retry", "blocked"):
        if tally.get(status):
            print(f"  {status:<10}{tally[status]}")
    nxt = pick_next(state)
    if nxt:
        print(f"\n续跑点：{nxt[1]['task']} [{nxt[1]['side']}] 第 {nxt[1]['attempt'] + 1} 次")
    for key, fails in blocked[:10]:
        print(f"  ⛔ {key}: {'; '.join(fails)[:90]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("--pack", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True); p.add_argument("--batch")
    p.add_argument("--state", type=Path, default=Path("progress.json"))
    p.add_argument("--since", type=float, help="纪元秒；早于它的产物视为旧批次，默认取当前时间")
    p.set_defaults(func=cmd_init)

    for name, func in (("next", cmd_next), ("status", cmd_status)):
        p = sub.add_parser(name); p.add_argument("--state", type=Path, default=Path("progress.json"))
        p.set_defaults(func=func)

    p = sub.add_parser("watch"); p.add_argument("--state", type=Path, default=Path("progress.json"))
    p.add_argument("--poll", type=float, default=5.0); p.set_defaults(func=cmd_watch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
