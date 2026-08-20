#!/usr/bin/env python3
"""Collect every alternate outfit / skin into the material library.

The base collector (`collect_refs.py`) takes one portrait per character, which
is only the default look. Characters ship alternate outfits — 150 on the
Genshin wiki, 90 on Zenless, 28 on Star Rail — and a skin library that carries
only default looks covers a fraction of what the roster can actually produce.

Each outfit lives on its own wiki page, and two fields there do all the work:
the page image is the outfit's full splash art, and the page's categories
include `<Character> Outfits`, which is how an outfit is attributed back to its
owner without any hand-maintained mapping.

Writes to `<library>/<游戏>/<角色>/refs/outfits/<outfit>.png` alongside a
per-character `outfits.json` ledger.

Usage:
    python3 collect_outfits.py --roster ../research/roster-genshin.json --library …
    python3 collect_outfits.py --roster ../research/roster-zzz.json --library … --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

UA = {"User-Agent": "harness-ui-collector/1.0 (personal, non-commercial)"}
# "Ganyu Outfits" → Ganyu. Anchored so "Paid Outfits" / "4-Star Outfits" and the
# other bookkeeping categories on the same page never look like a character.
OWNER_CATEGORY = re.compile(r"^(?!Paid |Free |Bundled |\d)(.+?) Outfits$")
# 鸣潮把稀有度也写成 "<词> Outfits" 分类（Deluxe / Premium / Signature /
# Original），正则会把它们当成角色名。Original 尤其要挡：那是角色的默认装，
# 它的图就是 <Name> Full Sprite.png —— 和默认锚图同一个文件，收进来就是重复变体。
SKIP_OWNERS = {"Character", "Traveler", "Trailblazer", "Rover",
               "Deluxe", "Premium", "Signature", "Original", "Standard",
               "Default", "Limited Board", "Shop", "Battle Pass"}


def api(wiki: str, params: dict, *, timeout: int = 30) -> dict:
    url = f"https://{wiki}.fandom.com/api.php?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as response:
        return json.load(response)


# 换装分类不止一个：原神有 Outfits 149 + Alternate Outfits 7，
# 崩铁有 22 + 5。只读第一个就漏掉后面那些。
OUTFIT_CATS = ("Outfits", "Alternate Outfits", "Skins", "Costumes")


def list_outfits(wiki: str) -> list[str]:
    """Every page in the outfit categories, following continuation, de-duplicated."""
    seen: list[str] = []
    for cat in OUTFIT_CATS:
        cont: dict = {}
        while True:
            data = api(wiki, {"action": "query", "list": "categorymembers",
                              "cmtitle": f"Category:{cat}", "cmlimit": 500,
                              "format": "json", **cont})
            seen += [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
            if "continue" not in data:
                break
            cont = data["continue"]
    return [t for t in dict.fromkeys(seen) if t not in OUTFIT_CATS]


def describe(wiki: str, titles: list[str]) -> dict[str, dict]:
    """Page image + categories for up to 50 outfit pages per call."""
    out = {}
    for start in range(0, len(titles), 50):
        chunk = titles[start:start + 50]
        data = api(wiki, {"action": "query", "titles": "|".join(chunk),
                          "prop": "pageimages|categories", "piprop": "original",
                          "cllimit": "max", "format": "json"})
        for page in data.get("query", {}).get("pages", {}).values():
            owners = []
            for category in page.get("categories", []):
                match = OWNER_CATEGORY.match(category["title"].replace("Category:", ""))
                if match and match.group(1) not in SKIP_OWNERS:
                    owners.append(match.group(1))
            categories = {c["title"].replace("Category:", "") for c in page.get("categories", [])}
            original = page.get("original") or {}
            out[page["title"]] = {
                "image": original.get("source"),
                # piprop=original 本来就带宽高，不用再反查一次 File: 标题
                "size": (original.get("width"), original.get("height"))
                        if original.get("width") else None,
                "owners": [] if ({"Original Outfits", "Default Outfits"} & categories) else owners,
            }
        time.sleep(0.3)
    return out


def portrait_file(wiki: str, titles: list[str], owners: dict) -> dict:
    """换装自己的人物立绘。各 wiki 命名不同，所以试多套模式。

    page image 不可靠：鸣潮的换装页 page image 是 `<Outfit> Splash Art.png`，
    整幅场景宣传图 2048x1667，人物小小地躺在中间，当身份锚图等于没有锚。
    但也不能一律要求 `Full Sprite`——异环用的是 `<Outfit> - Portrait.png`
    和 `<角色> <Outfit> Portrait.png`，那条规则把它 73 套全挡了。

    所以：先按模式找，找不到再退回 page image，**并且用尺寸兜底**——
    真正要挡的场景宣传图一律是横构图。
    """
    wanted: dict[str, list[str]] = {}
    for title in titles:
        pats = [f"File:{title} Full Sprite.png",
                f"File:{title} - Portrait.png",
                f"File:{title} Portrait.png",
                f"File:{title} Sprite.png"]
        for owner in owners.get(title, []):
            pats.append(f"File:{owner} {title} Portrait.png")
            pats.append(f"File:{owner} {title} Full Sprite.png")
        wanted[title] = pats
    flat = [p for pats in wanted.values() for p in pats]
    found: dict[str, tuple[str, int, int]] = {}
    for start in range(0, len(flat), 40):
        data = api(wiki, {"action": "query", "titles": "|".join(flat[start:start + 40]),
                          "prop": "imageinfo", "iiprop": "url|size", "format": "json"})
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [None])[0]
            if info and info.get("width"):
                found[page["title"]] = (info["url"], info["width"], info["height"])
        time.sleep(0.25)
    out: dict[str, tuple[str, int, int]] = {}
    for title, pats in wanted.items():
        # 同名多个候选时挑竖构图里面积最大的
        cands = [found[p] for p in pats if p in found]
        upright = [c for c in cands if c[2] >= c[1] * 1.15]
        if upright:
            out[title] = max(upright, key=lambda c: c[1] * c[2])
    return out


def image_size(wiki: str, urls: dict) -> dict:
    """page image 的尺寸，用来判断它是不是横构图的场景宣传图。"""
    return urls


def original_url(url: str) -> str:
    """Fandom 的 CDN 对所有 UA 都返回 WebP 转码；不加这个参数拿到的不是原图。"""
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parts.query)
    query["format"] = ["original"]
    return urllib.parse.urlunsplit(
        parts._replace(query=urllib.parse.urlencode(query, doseq=True)))


def slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roster", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pause", type=float, default=0.3)
    args = parser.parse_args()

    roster = json.loads(args.roster.read_text(encoding="utf-8"))
    wiki, game_zh = roster["wiki"], roster["game_zh"]
    # Match on both the roster short name and the wiki title collect_refs.py
    # resolved and wrote back: outfit categories use the agent's full name
    # ("Evelyn Chevalier", "Hoshimi Miyabi") while the roster carries the short
    # one, which orphaned most Zenless outfits on the first run.
    by_name = {}
    for character in roster["characters"]:
        by_name[character["name_en"]] = character
        page = (character.get("wiki_page") or "").replace("_", " ")
        if page:
            by_name.setdefault(page, character)

    titles = list_outfits(wiki)
    if args.limit:
        titles = titles[: args.limit]
    print(f"{game_zh}: Category:Outfits 共 {len(titles)} 套")

    pages = describe(wiki, titles)
    # 归属先算出来，才能试 "<角色> <换装> Portrait.png" 这种带角色名的模式
    owners_of = {title: info["owners"] for title, info in pages.items()}
    sprites = portrait_file(wiki, titles, owners_of)
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    orphans = []
    for title, info in pages.items():
        sprite = sprites.get(title)
        image = sprite[0] if sprite else info["image"]
        if not image:
            orphans.append(f"{title} (无立绘)")
            continue
        # 场景宣传图当不了身份锚图：人物在里面只占很小一块，
        # 而锚图是这条产线里角色还原度的唯一来源。
        # 判据是**构图**不是文件名：场景宣传图一律是横的。
        if not sprite:
            wh = info.get("size")
            if not wh:
                orphans.append(f"{title} (取不到 page image 尺寸)")
                continue
            # 两条独立的判据，别混在一起：
            # 形状——真正的场景宣传图是明显横的（鸣潮 2048x1667=1.23、王者 1920x882=2.18）；
            #        方图是正经立绘（Pearl 的 2048x2048 锚图出图很好），不许当横的挡掉。
            # 尺寸——256x256 那些是图标，该挡，但理由是太小不是形状。
            if wh[0] > wh[1] * 1.15:
                orphans.append(f"{title} (横构图 {wh[0]}x{wh[1]}，是场景宣传图不是立绘)")
                continue
            if min(wh) < 600:
                orphans.append(f"{title} (只有 {wh[0]}x{wh[1]}，是图标不是立绘)")
                continue
        owner = next((o for o in info["owners"] if o in by_name), None)
        if owner is None:
            orphans.append(f"{title} (归属 {info['owners'] or '未知'} 不在女角色名单)")
            continue
        grouped[owner].append((title, image))

    saved = 0
    for owner, items in sorted(grouped.items()):
        character = by_name[owner]
        home = args.library / game_zh / character["id"] / "refs" / "outfits"
        home.mkdir(parents=True, exist_ok=True)
        ledger = []
        for title, url in items:
            target = home / f"{slug(title)}.png"
            if not target.exists():
                try:
                    with urllib.request.urlopen(urllib.request.Request(original_url(url), headers=UA), timeout=60) as response:
                        target.write_bytes(response.read())
                except Exception as error:
                    orphans.append(f"{title} (下载失败 {str(error)[:40]})")
                    continue
                time.sleep(args.pause)
            ledger.append({"outfit": title, "file": target.name,
                           "url": url, "bytes": target.stat().st_size})
            saved += 1
        (home.parent / "outfits.json").write_text(json.dumps({
            "character": character["id"], "name_en": owner, "game": roster["game"],
            "count": len(ledger), "fetched": "2026-08-19",
            "usage": "个人非商业：仅作生成锚定与质量校验，不进入分发产物",
            "rights": "角色与官方美术版权归 miHoYo / HoYoverse",
            "outfits": ledger,
        }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  + {owner:<22} {len(ledger)} 套")

    print(f"\n入库 {saved} 套，覆盖 {len(grouped)} 个角色")
    if orphans:
        print(f"未归入 {len(orphans)} 项（多为男性角色或联动款）：")
        for entry in orphans[:12]:
            print(f"  · {entry}")
        if len(orphans) > 12:
            print(f"  … 还有 {len(orphans) - 12}")


if __name__ == "__main__":
    main()
