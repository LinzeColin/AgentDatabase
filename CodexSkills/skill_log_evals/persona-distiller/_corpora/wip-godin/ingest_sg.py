#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seth Godin #99 —— 把 193 篇博客正文 + 3 篇 holdout 灌进工作区。

## 归属：这个人物的语料在归属上是最干净的一类

每篇的首行都是 `<标题> | Seth's Blog`，seths.blog 是**单作者博客**，
不存在 Steinhardt 那轮「整期刊物按页切片后一律冠上他的前缀」的风险
（那次十份里九份不是他写的）。因此全部记 **P1 / author=Seth Godin**。

## 泳道归属是**我的判断**，不是来源自带的属性

纯博客语料没有天然的六泳道结构。下面的关键词表是我按标题与正文判的，
**它是一个分类决定，不是一个事实**——写进记录以便复核与推翻。

`conversations` 与 `external` 在这个人物身上必然薄：
他极少在博客里逐字转录对话，也极少长篇谈论具体外人。
**这是本人物的结构性特点，不是抓源不足**，不得靠灌次级源去凑。
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "ws-godin/seth-godin"
DISTILLER = pathlib.Path(
    "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595"
    "/CodexSkills/registry/codex/persona-distiller")

# 标题关键词 → 泳道。先匹配先生效；都不中则 writings。
LANE_RULES = [
    ("external", ("google", "murdoch", "byrne", "cowboy_junkies", "clarkes_law",
                  "famous_colleges", "wrestling", "hoodia", "rollyo", "iamoeba",
                  "the_market_has_spoken", "generational_shifts", "celebrity_art")),
    ("conversations", ("qa_", "may_i_have_your", "an_open_note", "thoughts_for_the_consigliere",
                       "who_is_cheering_you_on", "the_advice_gap", "advice_for_real",
                       "listening_to", "who_judges_your_work", "knowing_the_answer_before")),
    ("decisions", ("session_in_my_office", "patrons_and_assistants", "online_courses",
                   "last_chance_for_bonus", "some_reading_without_charge", "whats_new_at_purple_space",
                   "pay_what_you_want", "will_you_choose_to_do_it_live", "here_i_am",
                   "a_great_book_fo", "the_promised_bo")),
    ("timeline", ("thanksgiving", "thanks_", "black_friday", "predictions", "eventually_snow_melts",
                  "the_wrong_side_of_history", "old_buildings_on_the_edge", "common_pitfalls_of_the_new_economy",
                  "death_of_the_pe", "its_time", "about_to_be", "brace_for_impact")),
    ("expression", ("choices", "sprezzatura", "swagger", "short_and_funny", "writing_naked",
                    "deliberately_lo_fi", "fascinating", "rewrite_for_humans", "poison",
                    "two_confusions", "not_enough_if_or_not_enough_then", "turning_paradoxes")),
]


def lane_for(stem: str) -> str:
    for lane, keys in LANE_RULES:
        if any(k in stem for k in keys):
            return lane
    return "writings"


def run(paths, lane, year, holdout=False):
    cmd = [sys.executable, str(DISTILLER / "scripts/ingest.py"), str(TARGET), *[str(p) for p in paths],
           "--tier", "P1", "--author", "Seth Godin", "--language", "en",
           "--source-type", "blog-post", "--dimension", lane,
           "--rights", "public-web", "--locator", "https://seths.blog",
           "--published-at", f"{year}-01-01",
           "--abstract", ("seths.blog 单作者博客正文；首行含 `| Seth's Blog` 结构性署名。"
                          f"泳道 {lane} 为灌库时的分类判断，非来源自带属性。")]
    if holdout:
        cmd.append("--holdout")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"✗ {lane}/{year}: {(r.stderr or '').strip()[:200]}", file=sys.stderr)
        return 0
    return len(paths)


def main() -> int:
    import collections
    train = sorted(HERE.glob("sg_*.txt"))
    hold = sorted((HERE / "_holdout").glob("*.txt"))
    print(f"train {len(train)} 篇｜holdout {len(hold)} 篇")

    buckets = collections.defaultdict(list)
    for p in train:
        m = re.match(r"sg_(\d{4})_(.+)\.txt$", p.name)
        year, stem = (m.group(1), m.group(2)) if m else ("2010", p.stem)
        buckets[(lane_for(stem), year)].append(p)

    total = 0
    for (lane, year), paths in sorted(buckets.items()):
        total += run(paths, lane, year)
    print(f"\ntrain 灌入 {total}/{len(train)}")

    hb = collections.defaultdict(list)
    for p in hold:
        m = re.match(r"sg_(\d{4})_(.+)\.txt$", p.name)
        hb[m.group(1) if m else "2010"].append(p)
    ht = sum(run(paths, "writings", year, holdout=True) for year, paths in sorted(hb.items()))
    print(f"holdout 灌入 {ht}/{len(hold)}")

    lanes = collections.Counter(lane for (lane, _), v in buckets.items() for _ in v)
    print("\n泳道分布（我的分类判断）：")
    for lane, n in lanes.most_common():
        print(f"  {lane:<16} {n:>3}")
    return 0 if total == len(train) and ht == len(hold) else 1


if __name__ == "__main__":
    sys.exit(main())
