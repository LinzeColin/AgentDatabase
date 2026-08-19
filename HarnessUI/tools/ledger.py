#!/usr/bin/env python3
"""Batch-aware material ledger.

The original schema assumed one product per character-variant, with `versions`
as a history where only the newest mattered. That is wrong for how this project
actually behaves: re-running the same character through a revised prompt does
not produce a *better* copy of the same thing, it produces a *different* one —
different pose, different outfit reading, different scene. Both the v1.0 and
v1.1 Ganyu are usable skins, and both deserve to be pickable in the gallery.

So a generation batch is a first-class axis. The registry counts

    characters × variants × batches × 2 sides

and every batch keeps its own engine, pack version, prompt hash, verdict and
measured metrics, so a batch can be accepted, rejected or retired without
touching the others.

`verdict` is deliberately per-batch and per-image: a batch can be accepted as a
whole while individual images inside it are rejected and reshot.

Usage:
    python3 ledger.py ingest --library … --batch v1.1 --engine "minimax/niji7" \\
        --pack-version 1.1.0 --source ~/Movies/Hub/Projects/根据任务包去执行和生成 --suffix -v11
    python3 ledger.py report --library …
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageStat
except ImportError:
    raise SystemExit("需要 Pillow：python3 -m pip install Pillow")

GAMES = {"genshin": "原神", "hsr": "崩铁", "zzz": "绝区零"}
DARK_MIN, DARK_MAX = 0.28, 0.50
RIGHT_DETAIL_MAX = 14.0
SUBJECT_EDGE = 0.35
MID_EDGE = 0.62


def measure(path: Path) -> dict:
    """The metrics the acceptance thresholds are expressed in."""
    with Image.open(path) as image:
        width, height = image.size
        grey = image.convert("L")
        brightness = ImageStat.Stat(grey).mean[0] / 255
        right = grey.crop((int(width * SUBJECT_EDGE), 0, width, height)).resize((800, 450))
        right_edge = ImageStat.Stat(right.filter(ImageFilter.FIND_EDGES)).mean[0]
        left = grey.crop((0, 0, int(width * SUBJECT_EDGE), height)).resize((400, 450))
        mid = grey.crop((int(width * SUBJECT_EDGE), 0, int(width * MID_EDGE), height)).resize((400, 450))
        left_edge = ImageStat.Stat(left.filter(ImageFilter.FIND_EDGES)).mean[0]
        mid_edge = ImageStat.Stat(mid.filter(ImageFilter.FIND_EDGES)).mean[0]
    return {
        "width": width, "height": height,
        "brightness": round(brightness, 3),
        "right_edge": round(right_edge, 1),
        # How much of the character bleeds past the left third. Ratio rather
        # than absolute, so a busy costume and a plain one compare fairly.
        "spill": round(mid_edge / left_edge, 3) if left_edge else None,
    }


def judge(metrics: dict, side: str) -> tuple[str, list[str]]:
    """Machine verdict for one image; human clauses stay out of this."""
    fails = []
    if abs(metrics["width"] / metrics["height"] - 16 / 9) > 0.01:
        fails.append("B1 比例")
    if metrics["width"] < 2048:
        fails.append("B2 宽度")
    if metrics["right_edge"] > RIGHT_DETAIL_MAX:
        fails.append(f"C3 右侧细节 {metrics['right_edge']}")
    if side == "dark" and not DARK_MIN <= metrics["brightness"] <= DARK_MAX:
        fails.append(f"G1 暗版亮度 {metrics['brightness']}")
    return ("reject" if fails else "accept"), fails


def ledger_path(library: Path, game_zh: str, character: str) -> Path:
    return library / game_zh / character / "ledger.json"


def load(path: Path, character: str, game: str) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"character": character, "game": game, "schema": 2, "batches": []}


def ingest(args: argparse.Namespace) -> None:
    """Fold one generation batch into every character's ledger."""
    source = args.source

    # Character ids are unique per game only; resolve via the rosters so a
    # Genshin Nicole never lands in the Zenless ledger.
    owner = {}
    for game in GAMES:
        roster = json.loads((args.rosters / f"roster-{game}.json").read_text(encoding="utf-8"))
        for character in roster["characters"]:
            owner.setdefault(character["id"], game)

    # Filenames are `<character>-<variant>-<side><suffix>.png` and BOTH halves
    # contain hyphens ("hu-tao", "machine-hunter"), so a regex split at the
    # first or last hyphen gets it wrong — the first run filed hu-tao under a
    # character called "hu". Match the longest known character id instead.
    ids = sorted(owner, key=len, reverse=True)
    tail = re.compile(rf"^-(?P<variant>.+)-(?P<side>light|dark){re.escape(args.suffix)}\.png$")
    found: dict[tuple[str, str], list] = {}
    for file in sorted(source.glob("*.png")):
        if file.name.startswith("._"):
            continue
        for character in ids:
            if not file.name.startswith(character):
                continue
            match = tail.match(file.name[len(character):])
            if match:
                found.setdefault((character, match["variant"]), []).append((match["side"], file))
                break

    if not found:
        raise SystemExit(f"{source} 里没有匹配 *-{{light,dark}}{args.suffix}.png 的文件")

    written = accepted = rejected = 0
    for (character, variant), files in sorted(found.items()):
        game = owner.get(character)
        if game is None:
            print(f"  ? {character} 不在任何名单里，跳过")
            continue
        path = ledger_path(args.library, GAMES[game], character)
        data = load(path, character, game)
        data["batches"] = [b for b in data["batches"]
                           if not (b["batch"] == args.batch and b["variant"] == variant)]

        images, fails_all = [], []
        for side, file in sorted(files):
            metrics = measure(file)
            verdict, fails = judge(metrics, side)
            fails_all += fails
            images.append({"side": side, "file": file.name, "bytes": file.stat().st_size,
                           "metrics": metrics, "verdict": verdict, "fails": fails})
        batch_verdict = "accept" if not fails_all else "reject"
        accepted += batch_verdict == "accept"
        rejected += batch_verdict == "reject"
        data["batches"].append({
            "batch": args.batch,
            "variant": variant,
            "engine": args.engine,
            "pack_version": args.pack_version,
            "generated": args.date,
            "source_dir": str(source),
            "verdict": batch_verdict,
            "machine_fails": sorted(set(fails_all)),
            "human_review": None,      # 人眼条款（C1/C2/C6/D/E/F）待填
            "images": images,
        })
        data["batch_count"] = len({b["batch"] for b in data["batches"]})
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        written += 1
        mark = "+" if batch_verdict == "accept" else "-"
        print(f"  {mark} {character}/{variant:<22} {args.batch:<8} {len(images)} 张 {batch_verdict}")

    print(f"\n写入 {written} 个角色 · 批次通过 {accepted} · 批次不通过 {rejected}")


def report(args: argparse.Namespace) -> None:
    """What the library holds, counted the way the gallery will count it."""
    totals = {"characters": 0, "ledgers": 0, "batches": 0, "images": 0, "accepted": 0}
    per_batch: dict[str, dict] = {}
    for game, game_zh in GAMES.items():
        root = args.library / game_zh
        if not root.is_dir():
            continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir() or folder.name.startswith("."):
                continue
            totals["characters"] += 1
            path = folder / "ledger.json"
            if not path.exists():
                continue
            totals["ledgers"] += 1
            data = json.loads(path.read_text(encoding="utf-8"))
            for batch in data["batches"]:
                totals["batches"] += 1
                slot = per_batch.setdefault(batch["batch"], {"images": 0, "accept": 0, "engine": batch["engine"]})
                for image in batch["images"]:
                    totals["images"] += 1
                    slot["images"] += 1
                    if image["verdict"] == "accept":
                        totals["accepted"] += 1
                        slot["accept"] += 1

    print(f"角色 {totals['characters']} · 有台账 {totals['ledgers']} · "
          f"批次记录 {totals['batches']} · 成品 {totals['images']} 张 · 机判通过 {totals['accepted']}")
    print(f"\n{'批次':<10}{'引擎':<22}{'张数':>6}{'机判通过':>9}{'通过率':>8}")
    for name, slot in sorted(per_batch.items()):
        rate = slot["accept"] / slot["images"] * 100 if slot["images"] else 0
        print(f"  {name:<8}{slot['engine']:<22}{slot['images']:>6}{slot['accept']:>9}{rate:>7.0f}%")
    print(f"\n可挑选皮肤总数 = 角色 × 变体 × 批次 × 2 = {totals['images']} 张")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_in = sub.add_parser("ingest")
    p_in.add_argument("--library", type=Path, required=True)
    p_in.add_argument("--rosters", type=Path, default=Path("../research"))
    p_in.add_argument("--source", type=Path, required=True)
    p_in.add_argument("--batch", required=True)
    p_in.add_argument("--engine", required=True)
    p_in.add_argument("--pack-version", required=True)
    p_in.add_argument("--suffix", default="")
    p_in.add_argument("--date", default="2026-08-19")
    p_in.set_defaults(func=ingest)

    p_rep = sub.add_parser("report")
    p_rep.add_argument("--library", type=Path, required=True)
    p_rep.set_defaults(func=report)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
