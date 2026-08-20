#!/usr/bin/env python3
"""Re-fetch each character's anchor at native resolution, losslessly.

Fixes two defects in the first collection pass, both found on 2026-08-19 by
auditing what was actually on disk rather than trusting the collector:

*   **Wrong file.** The page image the wiki nominates is the small character
    *card* — Sucrose arrived at 750x1800. The game's own full-body art lives
    under `Character <Name> Portrait.png` and is 5000x9700 for the same
    character. That naming pattern was simply never queried.
*   **Lossy transport.** Fandom's CDN answers with a WebP transcode for every
    user agent tried; the URL needs `?format=original` to return the stored
    PNG. Same pixels, 313KB versus 1.66MB — every asset collected before this
    was the transcode.

Together those put a hard ceiling on anchor fidelity that no amount of prompt
work could lift, since character identity in this pipeline comes entirely from
the anchor image.

Writes `refs/hires.png` plus provenance; leaves the earlier files untouched so
nothing that already points at them breaks.

Usage:
    python3 collect_hires.py --game genshin --library … --probe ../../scratchpad/best-genshin.json
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
GAMES = {"genshin": "原神", "hsr": "崩铁", "zzz": "绝区零", "wuwa": "鸣潮"}


def original_url(url: str) -> str:
    """Force the lossless original instead of the CDN's WebP transcode."""
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parts.query)
    query["format"] = ["original"]
    return urllib.parse.urlunsplit(
        parts._replace(query=urllib.parse.urlencode(query, doseq=True)))


def fetch(url: str, target: Path, *, timeout: int = 300) -> int:
    request = urllib.request.Request(url, headers={**UA, "Accept": "image/png,image/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return len(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, choices=GAMES)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True,
                        help="best-<game>.json produced by probe_res.py")
    parser.add_argument("--pause", type=float, default=0.4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    best = json.loads(args.probe.read_text(encoding="utf-8"))
    game_zh = GAMES[args.game]
    done = cached = missing = failed = 0
    gained = 0

    for character, entry in best.items():
        refs = args.library / game_zh / character / "refs"
        target = refs / "hires.png"
        if entry is None:
            missing += 1
            print(f"  - {character:<22} 无候选")
            continue
        if target.exists() and not args.force:
            cached += 1
            continue

        try:
            size = fetch(original_url(entry["url"]), target)
        except Exception as error:
            failed += 1
            print(f"  ! {character:<22} {str(error)[:70]}")
            continue

        record = refs / "source.json"
        if record.exists():
            try:
                data = json.loads(record.read_text(encoding="utf-8"))
            except Exception:
                data = {"files": []}
            data.setdefault("files", []).append({
                "file": "hires.png", "kind": "official-native-art",
                "wiki_title": entry["title"], "url": original_url(entry["url"]),
                "pixels": f"{entry['w']}x{entry['h']}", "bytes": size,
                "note": "lossless original; the CDN serves WebP without ?format=original",
            })
            data["anchor"] = "hires.png"
            record.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

        gained += size
        done += 1
        print(f"  + {character:<22}{entry['w']}x{entry['h']:<6} {size // 1024:>6}KB  {entry['title'][:40]}")
        time.sleep(args.pause)

    print(f"\n新增 {done} · 已有 {cached} · 无候选 {missing} · 失败 {failed} · "
          f"下载 {gained / 1048576:.0f} MB")


if __name__ == "__main__":
    main()
