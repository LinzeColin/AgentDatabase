#!/usr/bin/env python3
"""一个 IP 名字进，一份立项报告出。花钱之前跑这个。

为什么要有它：给「异环」从零走一遍，五步里有三步是纯机械的（找 wiki、
找花名册分类、找锚图命名规律），我却每次都手工试。手工试的代价不是时间，
是**每次都可能试出不同的结论**——同一个 wiki 换个人问，锚图类别就选错了。

报告里的每个数字都来自探测。**不许来自记忆**：上一轮凭记忆说的三条源素材全是错的。

Usage:
    python3 scout_ip.py --name "异环" --out ../research/scout-nte.md
    python3 scout_ip.py --name "Honor of Kings" --slug hok --wiki honor-of-kings
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# 花名册分类的候选名。取**交集**而不是单个分类：
# 异环上 Playable 21 人、Female 29 人，交集才是我们要的 15 人。
ROSTER_CATS = ["Playable Characters", "Agents", "Resonators", "Playable Agents",
               "Female Resonators", "Heroes", "Characters"]
FEMALE_CATS = ["Female Characters", "Female Resonators", "Female Agents", "Female Heroes"]
# 锚图候选类。先按名字筛立绘类再比大小——直接按面积挑会挑到抽卡横幅
# （164 个角色里错了 51 个，甘尤的横幅比她自己的立绘还大）。
ANCHOR_KINDS = ["Portrait", "Full Sprite", "Splash Art", "Full", "Card",
                "Full Wish", "Render", "Artwork"]
BANNED_KINDS = ["Wish", "Banner", "Icon", "Namecard"]


def api(wiki: str, params: dict, *, zh: bool = False, timeout: int = 30):
    base = f"https://{wiki}.fandom.com/{'zh/' if zh else ''}api.php"
    url = f"{base}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.load(r)
    except Exception as exc:
        return {"_err": str(exc)[:80]}


def find_wiki(name: str) -> list[str]:
    """按名字猜 Fandom 子域并逐个验活。Fandom 的全站搜索 API 返 403，只能试。"""
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    cands = [base, base.replace("-", ""), base.split("-")[0]]
    alive = []
    for sub in dict.fromkeys(cands):
        d = api(sub, {"action": "query", "meta": "siteinfo", "format": "json"})
        site = (d.get("query", {}).get("general", {}) or {}).get("sitename")
        if site:
            alive.append((sub, site))
        time.sleep(0.2)
    return alive


def members(wiki: str, cat: str) -> list[str]:
    out, cont = [], {}
    while True:
        d = api(wiki, {"action": "query", "list": "categorymembers", "cmtitle": f"Category:{cat}",
                       "cmlimit": "500", "cmnamespace": "0", "format": "json", **cont})
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d:
            return [t for t in out if t != cat]
        cont = d["continue"]


def roster_of(wiki: str) -> tuple[list[str], str]:
    """可玩 ∩ 女性。两个都拿不到就退回单个分类，并在报告里说清楚退了。"""
    playable, p_used = [], None
    for c in ROSTER_CATS:
        m = members(wiki, c)
        if m:
            playable, p_used = m, c
            break
        time.sleep(0.15)
    female, f_used = [], None
    for c in FEMALE_CATS:
        m = members(wiki, c)
        if m:
            female, f_used = m, c
            break
        time.sleep(0.15)
    if playable and female:
        return sorted(set(playable) & set(female)), f"{p_used} ∩ {f_used}"
    if playable:
        return sorted(playable), f"{p_used}（**没有性别分类，未筛性别**）"
    return [], "找不到花名册分类"


def anchor_sizes(wiki: str, roster: list[str]) -> dict:
    """每个角色每个候选类的实际尺寸。竖构图优先于面积。"""
    titles = [f"File:{n} {k}.png" for n in roster for k in ANCHOR_KINDS]
    found: dict[str, tuple[int, int]] = {}
    for i in range(0, len(titles), 40):
        d = api(wiki, {"action": "query", "titles": "|".join(titles[i:i + 40]),
                       "prop": "imageinfo", "iiprop": "url|size", "format": "json"})
        for p in d.get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [None])[0]
            if ii and ii.get("width"):
                found[p["title"][5:]] = (ii["width"], ii["height"])
        time.sleep(0.2)
    best = {}
    for n in roster:
        cands = []
        for k in ANCHOR_KINDS:
            if any(b in k for b in BANNED_KINDS) and k != "Full Wish":
                continue
            wh = found.get(f"{n} {k}.png")
            if wh:
                cands.append(((1 if wh[1] >= wh[0] else 0), wh[0] * wh[1], k, wh))
        best[n] = max(cands)[2:] if cands else None
    return best


def chinese_names(wiki: str, roster: list[str]) -> dict:
    """三条常规路。异环三条全空——那时候就要去找第四个源，别硬凑。"""
    got = {}
    for i in range(0, len(roster), 40):
        d = api(wiki, {"action": "query", "titles": "|".join(roster[i:i + 40]),
                       "prop": "langlinks", "lllang": "zh", "lllimit": "500", "format": "json"})
        for p in d.get("query", {}).get("pages", {}).values():
            zh = (p.get("langlinks") or [{}])[0].get("*")
            if zh:
                got[p["title"]] = zh
        time.sleep(0.2)
    missing = [n for n in roster if n not in got]
    for i in range(0, len(missing), 20):
        d = api(wiki, {"action": "query", "titles": "|".join(missing[i:i + 20]),
                       "prop": "revisions", "rvprop": "content", "rvslots": "main", "format": "json"})
        for p in d.get("query", {}).get("pages", {}).values():
            wt = ((p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}) or {}).get("*", "")
            m = re.search(r"zhs\s*=\s*([一-鿿·・「」]{1,14})", wt)
            if m:
                got[p["title"]] = m.group(1)
        time.sleep(0.2)
    return got


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True)
    ap.add_argument("--wiki", help="已知的 Fandom 子域，跳过猜")
    ap.add_argument("--slug", help="产线里的短名，默认按 name 生成")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--price", type=float, default=0.0772,
                    help="上一轮实测单张成本（含重试），默认 v1.7.0 的 $0.0772")
    args = ap.parse_args()

    lines = [f"# 立项报告 · {args.name}", ""]
    if args.wiki:
        wikis = [(args.wiki, "（调用方指定）")]
    else:
        wikis = find_wiki(args.name)
    if not wikis:
        lines += ["**找不到 Fandom 站。** 换官方接口或第三方源，见 02-roster.md。", ""]
        print("\n".join(lines))
        return
    wiki = wikis[0][0]
    lines += [f"- 素材源：`{wiki}.fandom.com`（{wikis[0][1]}）", ""]

    roster, how = roster_of(wiki)
    lines += [f"## 人物清单（{len(roster)} 人）", "", f"筛法：`{how}`", ""]

    best = anchor_sizes(wiki, roster)
    zh = chinese_names(wiki, roster)
    upright = sum(1 for v in best.values() if v and v[1][1] >= v[1][0])
    land = sum(1 for v in best.values() if v and v[1][1] < v[1][0])
    none = sum(1 for v in best.values() if not v)
    shorts = sorted(min(v[1]) for v in best.values() if v)
    median = shorts[len(shorts) // 2] if shorts else 0

    lines += ["| 角色 | 中文名 | 锚图类 | 尺寸 |", "|---|---|---|---|"]
    for n in roster:
        v = best.get(n)
        lines.append(f"| {n} | {zh.get(n) or '**缺**'} | {v[0] if v else '**无候选**'} | "
                     f"{f'{v[1][0]}x{v[1][1]}' if v else '-'} |")
    lines += ["",
              f"- 锚图：竖 {upright} · 横 {land} · 无候选 {none} · **短边中位数 {median}px**",
              f"- 中文名：{len(zh)}/{len(roster)}"
              + ("" if len(zh) == len(roster) else "，**缺的要另找源，别硬凑**"),
              ""]

    variants = len(roster)          # 换装要另外跑 collect_outfits.py 才知道
    images = variants * 2
    lines += ["## 规模与成本（**换装未计入，跑完 collect_outfits.py 再更新**）", "",
              f"- 变体数（仅默认）：{variants}",
              f"- 出图数：{images}（昼+夜）",
              f"- 预估成本：**${images * args.price:.2f}**（按实测单价 ${args.price}/张，含重试）",
              "",
              "## 花钱前还要做",
              "",
              "1. `collect_outfits.py` 数清换装，更新上面的规模与成本",
              "2. `collect_refs.py` + `probe_res.py` + `collect_hires.py` 落锚图",
              "3. `build_taskpack.py` 后跑需求核对，16 项全满分才准开跑",
              "4. 试跑 5 条最难的（新场景池 / 换装锚图 / 无 hires / 最小锚图 / 方图）",
              ""]
    text = "\n".join(lines)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"立项报告 → {args.out}")
    print(text if not args.out else "\n".join(lines[:14]))


if __name__ == "__main__":
    main()
