#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""outward.py —— 「对外」那一列。

现有的每一个指标回答的都是同一个问题：我做了多少。
一个都回答不了另一个问题：有没有一个动作的收件人不是我自己。

「造 → 交」这段能测（github 有 commits/PR）。「交 → 换到钱」这段一条信号都没有。
这个模块只做最小的一步：把「往外走过没有」变成一个确定性可查的计数。

■ 这个数应该很小，甚至恒为 0
  它上来就很大，说明判据写错了，不是说明干得好。所以每一条命中都带证据（日期+出处），
  可以逐条核。一个不能逐条核的「对外次数」没有任何价值。

■ 强度分级是硬的，不许合并成一个总数
  hard  —— 机器可核的事实（公开仓上的 release）。发生了就是发生了。
  soft  —— 会话文本里的意图痕迹（说要发报价、说要发帖）。说过 ≠ 做过。
  none  —— 根本没有信号源。

■ 三件这里测不到的事，必须一直摆在页面上
  1. 有没有人真的下载/使用了 —— 需要外部遥测，本机没有。
  2. 有没有人为此付过钱 —— 需要账目，本机没有。
  3. 有没有人来找过我 —— 需要收件箱，本机不读。
  把这三条隐去，「对外 3 次」会被读成「有 3 个人在用」。差得很远。

运行期不调用任何模型，全部是正则与字段比对。
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone

TZ_OFFSET_H = 10
WINDOW_D = 30
RECENT_D = 7

# 匹配前必须先剥掉的东西。不剥就是在数文件名：
# 第一版实测 30 天命中 41 次，逐条查完发现绝大多数是
# `.../photo_sheets/2026年商务部报价群/sheet_0013.jpg` 这样的路径，
# 以及 `账龄回款`、`未来回款预测` 这样的表格列名 —— 全是内部文档处理，不是对外动作。
NOISE = [
    re.compile(r"https?://\S+"),                      # 链接
    re.compile(r"[~./][\w\-./\u4e00-\u9fff]{6,}"),    # 文件路径（含中文目录名）
    re.compile(r"`{1,3}[^`]*`{1,3}", re.S),           # 行内/围栏代码
    re.compile(r"\b[Ss]heet\s*\d+\b"),               # 表格页签
]


def _clean(t: str) -> str:
    for rx in NOISE:
        t = rx.sub(" ", t or "")
    return t


# 文本痕迹。故意分三类：把「谈钱」和「发东西」混成一个数，
# 就没法回答「我到底是没做出来，还是做出来了没开价」。
#
# 每一条都动词锚定：名词本身（「报价」「合同」）在这台机器上大量出现在
# 文件名和列名里，是 Owner 的本职文书工作，不是「把东西卖给谁」。
# 只认「做这个动作」的形态：发/开/收到/签了/寄给。
TEXT_SIGNALS = {
    "ship": {
        "label": "把做出来的东西放到外面",
        "pat": (r"(gh\s+release\s+create|npm\s+publish|poetry\s+publish|twine\s+upload)|"
                r"(发布|上架|公开|开源|投稿)(了|到|去|一下)?\s*(到)?\s*"
                r"(github|npm|pypi|应用商店|插件市场|社区|平台|线上)"),
    },
    "reach": {
        "label": "主动触达具体某个人",
        "pat": (r"(发|回|寄|转发)(一封)?(邮件|私信|消息|方案|报告)\s*(给|到)|"
                r"群发|联系一下\s*(客户|甲方|对方|老板|供应商)"),
    },
    "money": {
        "label": "谈到钱的动作",
        # 动词和名词两种语序都要认：第一版只认「发报价」，漏掉了
        # 「把报价发给甲方」和「收到回款 32000」。正反控各 7 条，见 test_outward.py。
        "pat": (r"(?:(?:发|寄|出|报|递)\s*(?:个|一份|一张)?\s*报价|"
                r"报价\s*(?:单)?\s*(?:已)?\s*(?:发|寄|报)\s*(?:给|过去|出去)?)|"
                r"开\s*(?:张|个|一)?\s*发票|"
                r"(?:收到|到账|回款|打款|付款|结款)\s*(?:了)?\s*(?:\d|货款|尾款|定金|款项|全款)|"
                r"(?:签|签了|签下|签成)\s*(?:了)?\s*(?:合同|单子|协议)|"
                r"(?:付款|打款|转账)\s*给我"),
    },
}


def _local(iso: str):
    try:
        d = datetime.fromisoformat((iso or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc) + timedelta(hours=TZ_OFFSET_H)


def _state(n30: int, has_source: bool) -> str:
    """四态。「从来没有」和「说不准」必须分开 —— 前者是结论，后者是没数据。"""
    if not has_source:
        return "说不准"
    return f"本月 {n30} 次" if n30 else "从来没有"


def build(sessions: list, gh: dict | None, today: str | None = None) -> dict:
    gh = gh or {}
    hum = [s for s in sessions if s.get("kind") == "human"]
    days = [s["start"][:10] for s in hum if s.get("start")]
    end = today or (max(days) if days else datetime.now(timezone.utc).date().isoformat())
    end_d = datetime.fromisoformat(end).date()
    w30 = (end_d - timedelta(days=WINDOW_D)).isoformat()
    w7 = (end_d - timedelta(days=RECENT_D)).isoformat()

    rows = []

    # ── hard：公开仓上的 release。这是本机唯一一个「机器可核的对外事实」──
    repos = gh.get("repos") or []
    pub = [r for r in repos if r.get("private") is False]
    if gh.get("state") == "通" and repos:
        rel_days = [(d["d"], d.get("releases", 0))
                    for d in (gh.get("days") or []) if d.get("releases")]
        # 逐日的 release 数没有分仓，只能给总量 + 公开仓清单，不硬凑到仓上
        n_all = sum(n for _, n in rel_days)
        n30 = sum(n for d, n in rel_days if d > w30)
        n7 = sum(n for d, n in rel_days if d > w7)
        rows.append({
            "kind": "public_release", "strength": "hard",
            "label": "公开仓上的 release",
            "n_all": n_all, "n_30d": n30, "n_7d": n7,
            "state": _state(n30, True),
            "evidence": [{"d": d, "n": n} for d, n in sorted(rel_days, reverse=True)[:8]],
            "caveat": ("release 只证明「东西挂在那儿了」，不证明有人下载、更不证明有人付钱。"
                       f"当前公开仓 {len(pub)} 个 / 共 {len(repos)} 个。"),
        })
    else:
        rows.append({
            "kind": "public_release", "strength": "none",
            "label": "公开仓上的 release",
            "state": "说不准", "n_all": None, "n_30d": None, "n_7d": None,
            "evidence": [], "caveat": "没有 GitHub 数据，这一条测不了。",
        })

    # ── soft：会话文本里的意图痕迹。说过不等于做过，所以永远是 soft ──
    for kind, cfg in TEXT_SIGNALS.items():
        pat = (cfg.get("pat") or "").strip()
        if not pat:
            # 负控要打的就是这里：判据被清空必须变「说不准」，不能变 0
            rows.append({"kind": kind, "strength": "none", "label": cfg["label"],
                         "state": "说不准", "n_all": None, "n_30d": None, "n_7d": None,
                         "evidence": [], "caveat": "判据为空，这一条测不了。"})
            continue
        rx = re.compile(pat, re.I)
        hits = []
        for s in hum:
            if any(rx.search(_clean(p)) for p in (s.get("prompts") or [])):
                hits.append(s)
        d_of = lambda s: (s.get("start") or "")[:10]
        rows.append({
            "kind": kind, "strength": "soft", "label": cfg["label"],
            "n_all": len(hits),
            "n_30d": sum(1 for s in hits if d_of(s) > w30),
            "n_7d": sum(1 for s in hits if d_of(s) > w7),
            "state": _state(sum(1 for s in hits if d_of(s) > w30), True),
            "evidence": [{"d": d_of(s), "title": (s.get("title") or "")[:60],
                          "project": s.get("project") or ""}
                         for s in sorted(hits, key=d_of, reverse=True)[:8]],
            "top_projects": dict(Counter(s.get("project") or "未标注" for s in hits).most_common(4)),
            "caveat": "这是会话里说到的次数，不是做成的次数。说过 ≠ 做过。",
        })

    hard = [r for r in rows if r["strength"] == "hard"]
    hard30 = sum(r.get("n_30d") or 0 for r in hard)
    return {
        "window_days": WINDOW_D,
        "as_of": end,
        "headline": {
            "state": _state(hard30, bool(hard)),
            "n_30d": hard30 if hard else None,
            "basis": "只数 hard 那一类。soft 是「说过」，不进这个数。",
        },
        "signals": rows,
        "public_repos": len(pub),
        "repos_total": len(repos),
        "not_measurable": [
            "有没有人真的下载／使用了 —— 需要外部遥测，本机没有。",
            "有没有人为此付过钱 —— 需要账目，本机不读。",
            "有没有人来找过我 —— 需要收件箱，本机不读。",
        ],
        "note": ("这一列回答的是「有没有一个动作的收件人不是我自己」。"
                 "它上来就很大说明判据写错了，不是说明干得好 —— 所以每条都带证据可以逐条核。"),
    }
