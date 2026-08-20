#!/usr/bin/env python3
"""给每个角色补上简体中文名。

菜单和画廊里全是 acheron / guinaifen 这种罗马字，对着中文界面找人很别扭。
花名册里 name_zh 字段一直存在但始终是 None —— 采集时根本没取过。

两条路各有各的洞，所以两条都走：
*   英文站的 `zh` 跨语言链接，原神几乎全中，崩铁一半，绝区零一个都没有；
*   各游戏的中文站（`<wiki>.fandom.com/zh`）反向查它自己的 `en` 链接再取反，
    绝区零只能靠这条。
两边给的都是繁体，统一用 OpenCC 转简体 —— 用户界面通篇简体，混着繁体更难认。

Usage:
    python3 fetch_zh_names.py --out names_zh.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.parse
import urllib.request

from opencc import OpenCC

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
RES = (pathlib.Path.home() / "Documents/Codex/GithubProject/_scratch"
       "/agentdatabase-harness-ui/HarnessUI/research")
WIKIS = {"genshin": "genshin-impact", "hsr": "honkai-star-rail", "zzz": "zenless-zone-zero",
         "wuwa": "wutheringwaves"}
# 异环不进这张表：它的英文站没有任何中文字段（Other Languages 只有 en/ru），
# 也没有中文 Fandom 站，三条常规路全空。中文名走萌娘百科，见 tools/fetch_zh_moegirl.py。
CC = OpenCC("t2s")


def api(base: str, params: dict) -> dict:
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as response:
            return json.load(response)
    except Exception:
        return {}


def from_english_site(wiki: str, titles: list[str]) -> dict[str, str]:
    """English page -> zh title, via the page's own language links."""
    base = f"https://{wiki}.fandom.com/api.php"
    found = {}
    for i in range(0, len(titles), 40):
        data = api(base, {"action": "query", "titles": "|".join(titles[i:i + 40]),
                          "prop": "langlinks", "lllang": "zh", "lllimit": "500", "format": "json"})
        for page in data.get("query", {}).get("pages", {}).values():
            zh = (page.get("langlinks") or [{}])[0].get("*")
            if zh:
                found[page["title"]] = zh
        time.sleep(0.25)
    return found


def from_chinese_site(wiki: str, wanted: set[str]) -> dict[str, str]:
    """zh page -> English title, by asking the Chinese wiki for ITS `en` links.

    Needed because the English ZZZ wiki carries no `zh` link at all, so the
    mapping only exists in one direction and has to be walked backwards.
    """
    base = f"https://{wiki}.fandom.com/zh/api.php"
    found, cont = {}, None
    for _ in range(40):
        params = {"action": "query", "generator": "allpages", "gaplimit": "200",
                  "gapnamespace": "0", "prop": "langlinks", "lllang": "en",
                  "lllimit": "500", "format": "json"}
        if cont:
            params.update(cont)
        data = api(base, params)
        for page in data.get("query", {}).get("pages", {}).values():
            en = (page.get("langlinks") or [{}])[0].get("*")
            if en and en in wanted:
                found[en] = page["title"]
        cont = data.get("continue")
        if not cont:
            break
        time.sleep(0.25)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()

    names: dict[str, str] = {}
    for game, wiki in WIKIS.items():
        roster = json.loads((RES / f"roster-{game}.json").read_text(encoding="utf-8"))
        # A character can hang off a /Lore subpage; the artwork and the language
        # links both live on the base page.
        pages: dict[str, list[str]] = {}
        for character in roster["characters"]:
            page = (character.get("wiki_page") or character["id"]).replace("_", " ").split("/")[0]
            pages.setdefault(page, []).append(character["id"])

        got = from_english_site(wiki, list(pages))
        missing = {p for p in pages if p not in got}
        if missing:
            got.update(from_chinese_site(wiki, missing))

        for page, ids in pages.items():
            zh = got.get(page)
            if not zh:
                continue
            simplified = CC.convert(zh)
            for cid in ids:
                names[f"{game}/{cid}"] = simplified
        have = sum(1 for c in roster["characters"] if f"{game}/{c['id']}" in names)
        print(f"{game}: {have}/{len(roster['characters'])}")

    args.out.write_text(json.dumps(names, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n共 {len(names)} 个中文名 → {args.out}")


if __name__ == "__main__":
    main()
