#!/usr/bin/env python3
"""Collect official character art into the SMB material library.

Why official art and not fan art or LoRAs: the roster is 178 characters and
the LoRA supply on the reachable sources covers well under half of it
(`research/lora-coverage.md`), so a LoRA-first pipeline cannot reach the 90%
coverage target. Every character does have official art, and mmx accepts it as
`--subject-ref type=character`, so anchoring on official art is the only route
that covers the whole roster.

Each character gets, under `<library>/<游戏>/<角色>/refs/`:

    portrait.png    card / splash art, full resolution   (the generation anchor)
    thumb.jpg       512px thumbnail                      (for the review sheet)
    source.json     where each file came from, when, and what it may be used for

`source.json` is the governance record — a file with no provenance entry is
treated as unusable, not as "probably fine".

Usage:
    python3 collect_refs.py ../research/roster-genshin.json --library "/Volumes/share/03_资料库/MetaData/HarnessUI"
    python3 collect_refs.py ../research/roster-hsr.json --library … --limit 5
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "harness-ui-collector/1.0 (personal, non-commercial)"}
THUMB_PX = 512


def api(wiki: str, params: dict, *, timeout: int = 25) -> dict:
    """One Fandom API call."""
    url = f"https://{wiki}.fandom.com/api.php?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def resolve(wiki: str, name: str) -> str | None:
    """Find the real page title for a character.

    Rosters carry short names ("Ellen", "Anby", "Topaz") while the wikis file
    agents under their full names ("Ellen Joe", "Anby Demara"). Guessing the
    title from the roster name missed 29 of 45 ZZZ agents on the first pass, so
    fall back to the wiki's own search rather than to a hand-maintained
    alias table that would rot with every new agent.
    """
    try:
        data = api(wiki, {"action": "query", "list": "search", "srsearch": name,
                          "srlimit": 5, "format": "json"})
    except Exception:
        return None
    hits = data.get("query", {}).get("search", [])
    lowered = name.lower()
    # Prefer a title that starts with the roster name over a mere mention.
    for hit in hits:
        if hit["title"].lower().startswith(lowered):
            return hit["title"]
    return hits[0]["title"] if hits else None


def lookup(wiki: str, page: str) -> tuple[str | None, str | None]:
    """Return (full-size image url, thumbnail url) for a character page."""
    data = api(wiki, {
        "action": "query", "titles": page, "prop": "pageimages",
        "piprop": "original|thumbnail", "pithumbsize": THUMB_PX, "format": "json",
    })
    for entry in data.get("query", {}).get("pages", {}).values():
        if "missing" in entry:
            return None, None
        return (
            (entry.get("original") or {}).get("source"),
            (entry.get("thumbnail") or {}).get("source"),
        )
    return None, None


def download(url: str, target: Path, *, timeout: int = 60) -> int:
    """Fetch one file; returns bytes written."""
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return len(payload)


def collect(character: dict, wiki: str, library: Path, *, force: bool) -> dict:
    """Fetch one character's official art and write its provenance record."""
    home = library / character["game_zh"] / character["id"] / "refs"
    record = home / "source.json"
    if record.exists() and not force:
        return {"status": "cached", "dir": str(home)}

    page = character["wiki_page"]
    original, thumb = lookup(wiki, page)
    if original is None and thumb is None:
        found = resolve(wiki, character["name_en"])
        if found and found != page:
            page = found.replace(" ", "_")
            original, thumb = lookup(wiki, page)
            character["wiki_page"] = page   # remember the corrected title
    if original is None and thumb is None:
        return {"status": "missing", "dir": str(home)}

    files = []
    if original:
        size = download(original, home / "portrait.png")
        files.append({"file": "portrait.png", "kind": "official-art", "url": original, "bytes": size})
    if thumb:
        size = download(thumb, home / "thumb.jpg")
        files.append({"file": "thumb.jpg", "kind": "thumbnail", "url": thumb, "bytes": size})

    record.write_text(json.dumps({
        "character": character["id"],
        "name_en": character["name_en"],
        "game": character["game"],
        "wiki": f"https://{wiki}.fandom.com/wiki/{page}",
        "fetched": "2026-08-19",
        "usage": "个人非商业：仅作生成锚定与质量校验，不进入分发产物",
        "rights": "角色与官方美术版权归 miHoYo / HoYoverse",
        "files": files,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"status": "ok", "dir": str(home), "files": len(files)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roster", type=Path)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pause", type=float, default=0.4)
    parser.add_argument("--force", action="store_true", help="re-fetch even when cached")
    parser.add_argument("--write", action="store_true", help="record status back into the roster")
    args = parser.parse_args()

    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    wiki = roster["wiki"]
    characters = roster["characters"][: args.limit] if args.limit else roster["characters"]

    tally = {"ok": 0, "cached": 0, "missing": 0, "error": 0}
    misses = []
    for index, character in enumerate(characters, 1):
        try:
            result = collect(character, wiki, args.library, force=args.force)
        except Exception as error:
            result = {"status": "error", "error": str(error)[:100]}
        tally[result["status"]] = tally.get(result["status"], 0) + 1
        if result["status"] in ("missing", "error"):
            misses.append(f"{character['name_en']} ({result.get('error', 'page not found')})")
        character["refs_status"] = result["status"]
        mark = {"ok": "+", "cached": "=", "missing": "-", "error": "!"}[result["status"]]
        print(f"  {mark} [{index:>3}/{len(characters)}] {character['name_en']}")
        if result["status"] == "ok":
            time.sleep(args.pause)

    print(f"\n新增 {tally['ok']} · 已有 {tally['cached']} · 缺页 {tally['missing']} · 出错 {tally['error']}")
    got = tally["ok"] + tally["cached"]
    print(f"素材覆盖率 {got / len(characters) * 100:.0f}%  ({got}/{len(characters)})")
    if misses:
        print("需要手工补的：")
        for entry in misses:
            print(f"  · {entry}")

    if args.write:
        args.roster.write_text(json.dumps(roster, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"已写回 {args.roster}")


if __name__ == "__main__":
    main()
