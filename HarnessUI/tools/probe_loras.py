#!/usr/bin/env python3
"""Probe Hugging Face for a character LoRA per roster entry.

Civitai is the usual source for anime character LoRAs and it is unreachable
from this machine — the API answers HTTP 451 REGION_BLOCKED — so Hugging Face
is the primary source here instead. Coverage is therefore expected to be
patchy: this script's whole job is to turn "we'll find art for everyone" into
a real per-character yes/no before anyone commits to a roster.

A hit is recorded but NOT trusted: `base_model` is usually absent from the
search index, and an SD1.5-era LoRA cannot be used with an Illustrious/SDXL
checkpoint. Verifying that is a separate, per-candidate step.

Usage:
    python3 probe_loras.py ../research/roster-genshin.json --write
    python3 probe_loras.py ../research/roster-zzz.json --limit 5
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://huggingface.co/api/models"
GAME_TERMS = {"genshin": "genshin", "zzz": "zenless zone zero"}
# A repo only counts when its name carries the GAME, not merely the word
# "lora": character names like Amber, Barbara, Candace, Aino are ordinary
# words, and matching on the name alone pulled in a BERT adapter, an
# architecture-lighting LoRA and assorted unrelated weights on the first run.
FRANCHISE = ("genshin", "zenless", "zzz", "hoyo")


def search(query: str, limit: int = 8, *, timeout: int = 20) -> list[dict]:
    """One Hugging Face model search. Returns [] on any failure — a probe that
    errors must not look the same as a probe that found nothing, so the caller
    distinguishes them via the raised flag."""
    url = f"{API}?{urllib.parse.urlencode({'search': query, 'limit': limit})}"
    request = urllib.request.Request(url, headers={"User-Agent": "harness-ui-probe"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def score(model: dict, name: str, game: str) -> int:
    """Rough confidence that this repo is a LoRA for this character."""
    repo = model.get("modelId", "").lower()
    tokens = [t for t in name.lower().replace("-", " ").split() if len(t) > 2]
    if not tokens or not all(t in repo for t in tokens):
        return 0
    if not any(word in repo for word in FRANCHISE):
        return 0
    return 2 + ("lora" in repo)


def probe(character: dict, game: str, *, pause: float) -> dict:
    """Look for one character's LoRA; returns a candidates block."""
    name = character["name_en"]
    queries = [f"{name} {GAME_TERMS[game]} lora", f"{name} lora"]
    best: list[dict] = []
    for query in queries:
        try:
            results = search(query)
        except Exception as error:  # network/ratelimit: report, do not guess
            return {"probed": False, "error": str(error)[:120], "candidates": []}
        for model in results:
            if score(model, name, game) >= 2:
                best.append({
                    "repo": model.get("modelId"),
                    "downloads": model.get("downloads", 0),
                    "likes": model.get("likes", 0),
                    "base_model": None,  # not in the search index; verify per-candidate
                })
        if best:
            break
        time.sleep(pause)
    seen, unique = set(), []
    for candidate in best:
        if candidate["repo"] in seen:
            continue
        seen.add(candidate["repo"])
        unique.append(candidate)
    unique.sort(key=lambda c: -c["downloads"])
    return {"probed": True, "candidates": unique[:3]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roster", type=Path)
    parser.add_argument("--limit", type=int, help="probe only the first N characters")
    parser.add_argument("--pause", type=float, default=0.35, help="seconds between calls")
    parser.add_argument("--write", action="store_true", help="write results back into the roster")
    args = parser.parse_args()

    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    game = roster["game"]
    characters = roster["characters"][: args.limit] if args.limit else roster["characters"]

    hit = miss = failed = 0
    for index, character in enumerate(characters, 1):
        result = probe(character, game, pause=args.pause)
        character["lora_probe"] = result
        if not result["probed"]:
            failed += 1
            mark, detail = "!", result["error"]
        elif result["candidates"]:
            hit += 1
            top = result["candidates"][0]
            mark, detail = "+", f"{top['repo']}  ↓{top['downloads']}"
        else:
            miss += 1
            mark, detail = "-", ""
        print(f"  {mark} [{index:>3}/{len(characters)}] {character['name_en']:<24} {detail}")
        time.sleep(args.pause)

    print(f"\n有候选 {hit} · 无候选 {miss} · 探测失败 {failed} · 共 {len(characters)}")
    if hit + miss:
        print(f"覆盖率 {hit / (hit + miss) * 100:.0f}%（不含失败项，且候选未经底模兼容性核实）")

    if args.write:
        roster["lora_probe_at"] = "2026-08-19"
        roster["lora_probe_source"] = "huggingface (civitai unreachable: HTTP 451)"
        args.roster.write_text(json.dumps(roster, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"已写回 {args.roster}")


if __name__ == "__main__":
    main()
