#!/usr/bin/env python3
"""崩坏3 锚图采集：bh3.com 官网内容接口 → 库 refs/ 布局。

源（探测结论见 research/scout-hi3.md）：
    act-api-takumi-static.mihoyo.com/content_v2_user/app/b9d5f96cd69047eb/getContentList
    ?iChanId=703&iPage=1&iPageSize=200&sLangKey=zh-cn
返回 91 套装甲条目，`sExt` JSON 的 `703_3` 字段是装甲全身立绘（实测 1198×1151），
`703_0` 是装甲中文名，`sCategoryName` 是「官网<角色短名>」。

官网只有中文名，花名册只有英文名，桥接用 Fandom 装甲页 `{{Other Languages}}`
模板的 `zhs` 字段（en 页自带简中名，110 套装甲逐页取）。

落盘（照 03-anchors.md 的存法）：
    <library>/崩坏3/<char_id>/refs/
        portrait.png            该角色代表装甲的立绘（兼作 default 锚图）
        source.json             每文件的 wiki_title / url / 原生尺寸
        outfits.json            每套装甲一条（代表装甲带 "is_portrait": true，
                                build_taskpack 会跳过它避免与 default 重复）
        outfits/<battlesuit-slug>.jpg

官网无图的 19 套装甲（第二部 + 联动）只列清单，不硬凑。
网络请求一律带浏览器 UA、间隔 ≥0.15s。

Usage:
    python3 collect_hi3_official.py \\
        --library "/Volumes/share/03_资料库/MetaData/HarnessUI" \\
        --rosters ../research
"""

from __future__ import annotations

import argparse
import io
import json
import re
import statistics
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
API = ("https://act-api-takumi-static.mihoyo.com/content_v2_user/app/b9d5f96cd69047eb"
       "/getContentList?iChanId=703&iPage=1&iPageSize=200&sLangKey=zh-cn")
FANDOM = "https://honkaiimpact3.fandom.com/api.php"
INTERVAL = 0.2  # ≥0.15s 的纪律，官网与 Fandom 都按这个节奏

# sCategoryName 是「官网<短名>」，短名大多能 startswith 对上花名册中文全名，
# 对不上的显式登记，不靠猜。
SHORT_NAME_FIX = {"渡鸦": "natasha-cioara"}


def fetch(url: str) -> bytes:
    last: Exception | None = None
    for attempt in range(3):
        time.sleep(INTERVAL)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except Exception as exc:  # TLS 抖动实测存在，退避重试
            last = exc
            time.sleep(2 * (attempt + 1))
    raise last


def fetch_json(url: str) -> dict:
    return json.loads(fetch(url))


def norm(text: str) -> str:
    """比对用归一化：大小写、全半角、标点空格全部抹掉，只留字母数字和汉字。"""
    text = unicodedata.normalize("NFKC", text).lower()
    return "".join(ch for ch in text if ch.isalnum() or "一" <= ch <= "鿿")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def fetch_battlesuit_zhs(titles: list[str]) -> dict[str, str]:
    """Fandom 装甲页 en → zhs（{{Other Languages}} 模板），20 页一批。"""
    found: dict[str, str] = {}
    for i in range(0, len(titles), 20):
        params = urllib.parse.urlencode({
            "action": "query", "titles": "|".join(titles[i:i + 20]),
            "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "redirects": 1, "format": "json"})
        data = fetch_json(f"{FANDOM}?{params}")
        for page in data.get("query", {}).get("pages", {}).values():
            try:
                wikitext = page["revisions"][0]["slots"]["main"]["*"]
            except (KeyError, IndexError):
                continue
            match = re.search(r"\|\s*zhs\s*=\s*([^\n|]+)", wikitext)
            if match:
                found[page["title"]] = match.group(1).strip()
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rosters", type=Path, required=True)
    args = parser.parse_args()

    roster = json.loads((args.rosters / "roster-hi3.json").read_text(encoding="utf-8"))
    characters = {c["id"]: c for c in roster["characters"]}

    # 1. 官网 91 套装甲
    official = fetch_json(API)["data"]["list"]
    print(f"官网接口返回 {len(official)} 套装甲")

    # 2. sCategoryName → char_id
    def char_id_of(category: str) -> str | None:
        short = category.removeprefix("官网").strip()
        if short in SHORT_NAME_FIX:
            return SHORT_NAME_FIX[short]
        hits = [cid for cid, c in characters.items()
                if c["name_zh"].startswith(short) or short in c["name_zh"]]
        return hits[0] if len(hits) == 1 else None

    # 3. Fandom zhs 桥：en 装甲名 → 简中名
    titles = [b["name_en"] for c in characters.values() for b in c["battlesuits"]]
    zhs = fetch_battlesuit_zhs(titles)
    print(f"Fandom zhs 取到 {len(zhs)}/{len(titles)} 套装甲中文名")
    # char_id → {norm(zh): battlesuit_name_en}
    suit_zh: dict[str, dict[str, str]] = {}
    for c in characters.values():
        suit_zh[c["id"]] = {norm(zhs[b["name_en"]]): b["name_en"]
                            for b in c["battlesuits"] if b["name_en"] in zhs}

    # 4. 逐套匹配、下载、落盘
    collected: dict[str, list[dict]] = {cid: [] for cid in characters}
    unmatched_official: list[str] = []
    short_edges: list[int] = []
    landscape = 0
    for entry in official:
        ext = json.loads(entry["sExt"])
        name_zh_suit = ext["703_0"].strip()
        cid = char_id_of(entry["sCategoryName"])
        images = ext.get("703_3") or []
        if cid is None or not images:
            unmatched_official.append(
                f"{entry['sCategoryName']}/{name_zh_suit}（{'角色对不上' if cid is None else '无 703_3 图'}）")
            continue
        suit_en = suit_zh[cid].get(norm(name_zh_suit))
        if suit_en is None:
            unmatched_official.append(f"{characters[cid]['name_zh']}/{name_zh_suit}（zhs 对不上）")
            continue
        if any(o["battlesuit"] == suit_en for o in collected[cid]):
            continue  # 官网重复条目，留第一份

        refs = args.library / roster["game_zh"] / cid / "refs"
        target = refs / "outfits" / f"{slug(suit_en)}.jpg"
        url = images[0]["url"]
        if target.exists():
            raw = target.read_bytes()
        else:
            raw = fetch(url)
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
        short_edges.append(min(width, height))
        landscape += width > height
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        collected[cid].append({
            "battlesuit": suit_en, "battlesuit_zh": name_zh_suit,
            "file": target.name, "url": url, "pixels": f"{width}x{height}",
            "bytes": len(raw)})

    # 5. 每角色写 portrait.png / outfits.json / source.json
    n_files = n_entries = 0
    for cid, suits in collected.items():
        if not suits:
            continue
        character = characters[cid]
        refs = args.library / roster["game_zh"] / cid / "refs"
        refs.mkdir(parents=True, exist_ok=True)
        # 代表装甲：花名册里排在最前且有官图的那套
        order = [b["name_en"] for b in character["battlesuits"]]
        representative = min(suits, key=lambda s: order.index(s["battlesuit"]))
        (refs / "portrait.png").write_bytes((refs / "outfits" / representative["file"]).read_bytes())

        ledger = {"character": cid, "name_en": character["name_en"], "game": "hi3",
                  "count": len(suits), "fetched": "2026-08-23",
                  "usage": "个人非商业：仅作生成锚定与质量校验，不进入分发产物",
                  "rights": "角色与官方美术版权归 miHoYo / HoYoverse",
                  "outfits": [{"outfit": s["battlesuit"], "outfit_zh": s["battlesuit_zh"],
                               "file": s["file"], "wiki_title": s["battlesuit"], "url": s["url"],
                               "pixels": s["pixels"], "bytes": s["bytes"],
                               **({"is_portrait": True} if s is representative else {})}
                              for s in suits]}
        (refs / "outfits.json").write_text(
            json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        source = {"character": cid, "name_en": character["name_en"], "game": "hi3",
                  "wiki": f"https://honkaiimpact3.fandom.com/wiki/{character['wiki_page']}",
                  "fetched": "2026-08-23",
                  "usage": ledger["usage"], "rights": ledger["rights"],
                  "files": [{"file": "portrait.png", "kind": "official-art",
                             "wiki_title": representative["battlesuit"],
                             "url": representative["url"], "pixels": representative["pixels"],
                             "bytes": representative["bytes"],
                             "note": "bh3.com 官网 iChanId=703 sExt.703_3 装甲立绘；"
                                     f"代表装甲兼作 portrait，同 outfits/{representative['file']}"}]
                          + [{"file": f"outfits/{s['file']}", "kind": "official-art",
                              "wiki_title": s["battlesuit"], "url": s["url"],
                              "pixels": s["pixels"], "bytes": s["bytes"]} for s in suits],
                  "anchor": "portrait.png"}
        (refs / "source.json").write_text(
            json.dumps(source, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n_files += len([f for f in (refs / "outfits").glob("*.jpg")
                        if not f.name.startswith("._")])
        n_entries += len(suits)

    # 6. SMB 写入会留下 AppleDouble 渣文件（._*），删掉再核验
    for junk in (args.library / roster["game_zh"]).rglob("._*"):
        if junk.is_file():
            junk.unlink()

    # 7. 报告
    got = sum(len(s) for s in collected.values())
    covered_chars = sum(1 for s in collected.values() if s)
    missing = [f"{c['name_zh']} / {b['name_en']}"
               for c in characters.values()
               for b in c["battlesuits"]
               if b["name_en"] not in {s["battlesuit"] for s in collected[c['id']]}]
    print(f"\n采集 {got}/110 套装甲，覆盖 {covered_chars}/39 角色")
    print(f"落盘核验：outfits/*.jpg {n_files} 张 == outfits.json 条目 {n_entries} 条"
          f"（{'✅' if n_files == n_entries else '❌'}）")
    if short_edges:
        print(f"短边中位 {statistics.median(short_edges):.0f}px · "
              f"横构图 {landscape}/{len(short_edges)}")
    print(f"\n官网无图 / 未收（{len(missing)} 套，不硬凑）：")
    for line in missing:
        print(f"  · {line}")
    if unmatched_official:
        print(f"\n官网条目未匹配（{len(unmatched_official)} 条，需人工核）：")
        for line in unmatched_official:
            print(f"  · {line}")


if __name__ == "__main__":
    main()
