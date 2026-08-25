#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""journal.py —— 日记与发展方向。

Owner 的两句原话，这个模块各回答一句：

1)「还有日记日历时间线等需求」
   日历和时间线早就有了，**日记一直没有**。
   日历回答「哪天忙」，日记回答「那天你在干什么」——
   所以日记必须由**你自己的原话**构成，不是又一张统计表。

2)「按最近 3 天、7 天、15 天、30 天、45 天、60 天、90 天、180 天和全历史不同的时间切片
   来分析我的发展方向、路径、范围……我依旧不能用它去创造实际的经济价值，去帮我赚钱。」
   切片早就有了，**「方向 / 路径 / 范围」三个词一个都没被回答过**。
   这里把它们各自定义成一个可算的量，并且直说最后那句话的答案。

运行期不调用任何模型：日记是原话摘录，方向是计数与比值。
"""
from __future__ import annotations

from collections import Counter, defaultdict

# 阶梯的三级。ladder 里还有「学习」，它不在这条链上 —— 学习是投入不是产出。
CHAIN = ("建设", "交付", "换钱")


def diary(sessions: list, days: list, gh: dict | None, limit: int = 120) -> dict:
    """一天一条。**主体是你那天说的第一句话**，统计只做配角。

    为什么第一句话：一场会话的第一句是**你带着问题来的时候说的**，
    后面的都是被上一轮答案带着走的。要还原「那天在想什么」，第一句最准。
    """
    gh_days = {r["d"]: r for r in ((gh or {}).get("days") or [])}
    by_day = defaultdict(list)
    for s in sessions:
        if s.get("kind") != "human":
            continue                      # 日记只写你自己开口的那些
        by_day[(s.get("start") or "")[:10]].append(s)

    day_stat = {d["d"]: d for d in days}
    rows = []
    for d in sorted(by_day, reverse=True)[:limit]:
        ss = sorted(by_day[d], key=lambda x: x.get("start") or "")
        first = next((p for s in ss for p in (s.get("prompts") or []) if p and len(p.strip()) > 6), "")
        st = day_stat.get(d, {})
        g = gh_days.get(d, {})
        topics = Counter(t for s in ss for t in (s.get("topics") or []))
        files = []
        for s in reversed(ss):
            for f in (s.get("files") or []):
                if f not in files and len(files) < 4:
                    files.append(f)
        rows.append({
            "d": d,
            "opening": (first or "").strip()[:220],
            "sessions": len(ss),
            "turns": sum(s.get("turns", 0) for s in ss),
            "topics": [k for k, _ in topics.most_common(4)],
            "projects": [k for k, _ in Counter(s.get("project") or "未标注" for s in ss).most_common(3)],
            "tok": st.get("tok_in", 0) + st.get("tok_cache_r", 0),
            "errors_tool": st.get("errors_tool", 0),
            "commits": g.get("commits", 0),
            "merged": g.get("merged", 0),
            "files": files,
            "shipped": bool(g.get("commits")),
        })
    silent = [d["d"] for d in days if d.get("human", 0) == 0][-14:]
    return {
        "rows": rows,
        "note": ("一天一条，主体是你那天说的第一句话（原话，没有改写）。"
                 "第一句最能还原「那天你带着什么问题来」—— 后面的话都被上一轮的答案带着走了。"),
        "silent_days": silent,
        "silent_note": "这些天机器在跑，但你一次都没开口。它们不是空白，是「你没参与」。",
        "coverage": f"最近 {len(rows)} 个你开过口的日子",
    }


def _bucket(ss: list) -> dict:
    lad = Counter()
    for s in ss:
        for t in (s.get("topics") or []):
            lad[t] += 1
    return lad


def direction(slices: dict, sessions: list, delivery: dict | None,
              outward: dict | None, lessons: dict | None) -> dict:
    """按九个时间切片回答「方向 / 路径 / 范围」，并直答那句「为什么还没赚到钱」。

    三个词各自的定义（**先定义再计算**，否则就是又三个说不清的指标）：
      方向  这一段时间里注意力最重的三件事，以及和上一段比谁进谁出
      路径  造 → 交 → 换钱 三级阶梯上，你走到了哪一级、卡在哪一级
      范围  碰过多少个不同项目、多少个不同主题（广度），以及集中度（深度）
    """
    keys = ["3", "7", "15", "30", "45", "60", "90", "180", "0"]
    rows = []
    prev_top = None
    for k in keys:
        sl = slices.get(k)
        if not sl:
            continue
        top = [t for t, _ in Counter(sl.get("topics") or {}).most_common(3)]
        lad = sl.get("ladder") or {}
        build_n, ship_n, money_n = (lad.get(x, 0) for x in CHAIN)
        # 阶梯转化率：**只用相邻两级的比**，不用「换钱 ÷ 建设」——
        # 后者把两次转化压成一个数，卡在哪一级就看不出来了。
        r1 = round(ship_n / build_n, 4) if build_n else None
        r2 = round(money_n / ship_n, 4) if ship_n else None
        entered = [t for t in top if prev_top and t not in prev_top]
        left = [t for t in (prev_top or []) if t not in top]
        rows.append({
            "key": k, "label": sl.get("label"), "from": sl.get("from"),
            "human": sl.get("human", 0), "days_active": sl.get("days_active", 0),
            "top_topics": top, "entered": entered, "left": left,
            "projects": len(sl.get("projects") or {}),
            "topics_n": len(sl.get("topics") or {}),
            "ladder": {"建设": build_n, "交付": ship_n, "换钱": money_n},
            "build_to_ship": r1, "ship_to_money": r2,
            "unclassified": sl.get("unclassified", 0),
        })
        prev_top = top

    all_row = next((r for r in rows if r["key"] == "0"), None)
    d30 = next((r for r in rows if r["key"] == "30"), None)

    # ── 那句话的答案 ──
    # 「三个月了，我依旧不能用它去创造实际的经济价值，去帮我赚钱。」
    # 不给鸡汤，也不给「再努力一点」。只把链条上每一环的实测数摆出来，
    # 让断点自己显出来。
    ship_hard = None
    if outward and outward.get("signals"):
        ship_hard = next((s for s in outward["signals"] if s.get("kind") == "ship"), None)
    repeats = len((lessons or {}).get("repeats") or [])
    dl = (delivery or {}).get("totals") or {}

    links = [
        {"step": "① 造出来", "value": f"{(all_row or {}).get('ladder', {}).get('建设', 0)} 场",
         "state": "通", "why": "这一环从来不是瓶颈。"},
        {"step": "② 交出去（进 git）",
         "value": f"{dl.get('commits', 0)} 提交 / {dl.get('merged', '—')} 合并 PR",
         "state": "通" if dl.get("commits") else "说不准",
         "why": f"聊过的 {dl.get('days_talked', 0)} 天里有 {dl.get('days_shipped', 0)} 天真的提交了。"},
        {"step": "③ 放到别人拿得到的地方",
         "value": (f"{ship_hard.get('n_all')} 次" if ship_hard and ship_hard.get("n_all") is not None else "说不准"),
         "state": "断了" if (ship_hard and ship_hard.get("n_all") == 0) else "说不准",
         "why": "「把做出来的东西放到外面」的全期次数。这是链条上第一个断口。"},
        {"step": "④ 有人用了", "value": "说不准", "state": "说不准",
         "why": "需要外部遥测，本机没有。不假装它是 0，也不假装它是正数。"},
        {"step": "⑤ 有人付钱", "value": "说不准", "state": "说不准",
         "why": "需要账目，本机不读。"},
    ]
    broken = next((l for l in links if l["state"] == "断了"), None)

    return {
        "rows": rows,
        "definitions": {
            "方向": "这一段里注意力最重的三件事，以及和上一段相比谁进来了、谁出去了。",
            "路径": "造 → 交 → 换钱 三级阶梯上你走到哪一级。两次转化分开算 —— "
                    "合成一个数就看不出卡在哪一级。",
            "范围": "碰过多少个不同项目、多少个不同主题（广度），配合集中度看深度。",
        },
        "chain": links,
        "verdict": (
            f"链条在「{broken['step']}」断了。前两环是通的 —— 你确实在造、也确实在交进 git。"
            "断口不在产出，在分发：做出来的东西没有放到任何别人拿得到的地方，"
            "所以后面「有人用」「有人付钱」根本没有机会发生。"
            if broken else
            "这一轮没有认出明确的断口 —— 要么数据不够，要么判据写松了，"
            "不要把「没认出来」读成「没有问题」。"),
        "next_action": (
            "最小的一步不是再造一个东西，是把已经造好的其中一个放出去一次："
            "一个公开 release、一篇带链接的帖子、或者一次报价。"
            "这一步做完，③ 才会从 0 变成 1，④⑤ 才有可能开始被测量。"
            if broken else "—"),
        "repeats_debt": repeats,
        "widest": (max(rows, key=lambda r: r["projects"]) if rows else None),
        "note": ("九个切片用的是同一套定义，所以可以横着比。"
                 "注意 3 天 / 7 天这类短切片样本很小 —— 一天的异常就能把它整个带偏，"
                 "看趋势要看 30 天以上那几档。"),
    }
