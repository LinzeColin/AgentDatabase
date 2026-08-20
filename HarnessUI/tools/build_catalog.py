#!/usr/bin/env python3
"""Emit the catalogue the DSH skin reads at runtime.

The skin cannot enumerate a directory — it is browser code talking to a static
file server — so the shape of the library has to be handed to it as one JSON
document. Keeping that generation here (rather than in the plugin) means the
plugin ships unchanged when the library grows.

Ordering matters for shuffle mode: the cycle is defined as "every entry exactly
once", so the catalogue is the authority on what "every" means, and its order is
stable so a persisted cursor keeps its meaning across restarts.

Usage:
    python3 build_catalog.py --assets …/run/skin-assets --out …/run/skin-assets/catalog.json
"""

from __future__ import annotations

import argparse
import json
import pathlib

GAME_ZH = {"genshin": "原神", "hsr": "崩坏：星穹铁道", "zzz": "绝区零"}


def chinese_names(assets: pathlib.Path) -> dict:
    """id -> 简体中文名。缺的就没有 —— 界面回退到英文 id，不编一个出来。"""
    for candidate in (assets / "names_zh.json",
                      pathlib.Path(__file__).parent.parent / "research/names_zh.json"):
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--base", default="http://127.0.0.1:3099")
    args = parser.parse_args()

    display = args.assets / "display"
    zh = chinese_names(args.assets)
    entries = []
    for light in sorted(display.rglob("light.webp")):
        rel = light.relative_to(display)
        game, character, variant = rel.parts[0], rel.parts[1], rel.parts[2]
        dark = light.with_name("dark.webp")
        # A one-sided entry would show a blank window in whichever theme is
        # missing, so pairs only — the odd one out is reported, not shipped.
        if not dark.exists():
            continue
        name_zh = zh.get(f"{game}/{character}")
        entries.append({
            "id": f"{game}/{character}/{variant}",
            "game": game, "gameName": GAME_ZH.get(game, game),
            "character": character, "variant": variant,
            "characterZh": name_zh,
            # 菜单和画廊统一用这个字段。有中文名就用中文，没有就用英文 id ——
            # 两种混排也比音译一个假名字强。
            "label": name_zh or character,
            "light": f"{args.base}/display/{game}/{character}/{variant}/light.webp",
            "dark": f"{args.base}/display/{game}/{character}/{variant}/dark.webp",
            "thumb": f"{args.base}/thumb/{game}/{character}/{variant}/light.webp",
        })
    catalog = {"version": 1, "base": args.base, "count": len(entries), "entries": entries}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(catalog, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    games = {}
    for e in entries:
        games[e["game"]] = games.get(e["game"], 0) + 1
    print(f"目录已生成：{len(entries)} 条 → {args.out}")
    for game, count in sorted(games.items()):
        print(f"  {GAME_ZH.get(game, game):<14}{count}")


if __name__ == "__main__":
    main()
