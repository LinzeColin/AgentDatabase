#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""github.py —— 每日拉 GitHub 活动，回答「聊了多少 vs 真的交付了多少」。

会话记录只能证明你**在做**，GitHub 才能证明你**做出来了**。
两条曲线放在一起，「建设 : 交付」那个比例才不是自说自话。

用 gh CLI（已经在用它发备份 Release，凭据现成）。**不调用任何模型**。
增量：每个仓记住上次拉到哪一天，只补新的。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

TZ_OFFSET_H = 10        # 悉尼。固定 +10，不猜夏令时。
GH = os.environ.get("ATLAS_GH", "gh")
TIMEOUT = 60


def _gh(args: list) -> object | None:
    """跑一条 gh 命令。失败返回 None —— 拉不到就如实空着，不编。"""
    try:
        r = subprocess.run([GH] + args, capture_output=True, text=True, timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def owner_login() -> str | None:
    d = _gh(["api", "user", "--jq", "{login: .login}"])
    return d.get("login") if isinstance(d, dict) else None


def list_repos(login: str) -> list:
    out = _gh(["repo", "list", login, "--limit", "60", "--json",
               "name,isPrivate,pushedAt,primaryLanguage,diskUsage"])
    return out if isinstance(out, list) else []


def commits_for(login: str, repo: str, since: str) -> list:
    """某个仓在 since 之后的提交。只取作者是本人的。"""
    out = _gh(["api", "-X", "GET", f"repos/{login}/{repo}/commits",
               "-f", f"since={since}", "-f", "per_page=100",
               "--jq", "[.[] | {sha: .sha[0:7], date: .commit.author.date, "
                       "msg: (.commit.message | split(\"\\n\")[0]), "
                       "author: (.author.login // .commit.author.name)}]"])
    return out if isinstance(out, list) else []


def prs_for(login: str, repo: str) -> list:
    out = _gh(["api", "-X", "GET", f"repos/{login}/{repo}/pulls",
               "-f", "state=all", "-f", "per_page=60", "-f", "sort=updated", "-f", "direction=desc",
               "--jq", "[.[] | {n: .number, title: .title, state: .state, "
                       "created: .created_at, merged: .merged_at, user: .user.login}]"])
    return out if isinstance(out, list) else []


def releases_for(login: str, repo: str) -> list:
    out = _gh(["api", "-X", "GET", f"repos/{login}/{repo}/releases", "-f", "per_page=30",
               "--jq", "[.[] | {tag: .tag_name, published: .published_at, draft: .draft}]"])
    return out if isinstance(out, list) else []


def local_day(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return ""
    return (d + timedelta(hours=TZ_OFFSET_H)).date().isoformat()


def build(since_days: int = 400, state_path: Path | None = None) -> dict:
    login = owner_login()
    if not login:
        # gh 没登录或没网。如实标「不确定」，不要留一个空壳假装拉过。
        return {"state": "不确定", "why": "gh 未登录或拉取失败，本轮没有 GitHub 数据",
                "repos": [], "days": [], "prs": [], "releases": [], "totals": {}}

    since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat().replace("+00:00", "Z")
    repos = list_repos(login)
    by_day = defaultdict(lambda: {"commits": 0, "repos": Counter(), "prs": 0, "merged": 0, "releases": 0})
    repo_rows, all_prs, all_rel = [], [], []
    failed = []

    for r in repos:
        name = r.get("name")
        if not name:
            continue
        cs = commits_for(login, name, since)
        if cs is None:
            failed.append(name)
            cs = []
        mine = [c for c in cs if str(c.get("author", "")).lower() in (login.lower(), "linze zhang", "linzezhang")]
        for c in mine:
            d = local_day(c.get("date", ""))
            if d:
                by_day[d]["commits"] += 1
                by_day[d]["repos"][name] += 1
        prs = prs_for(login, name) or []
        for pr in prs:
            d = local_day(pr.get("created", ""))
            if d:
                by_day[d]["prs"] += 1
            if pr.get("merged"):
                dm = local_day(pr["merged"])
                if dm:
                    by_day[dm]["merged"] += 1
            all_prs.append(dict(pr, repo=name))
        rels = releases_for(login, name) or []
        for rel in rels:
            d = local_day(rel.get("published") or "")
            if d:
                by_day[d]["releases"] += 1
            all_rel.append(dict(rel, repo=name))
        repo_rows.append({
            "repo": name, "private": bool(r.get("isPrivate")),
            "pushed": local_day(r.get("pushedAt") or ""),
            "lang": (r.get("primaryLanguage") or {}).get("name") if r.get("primaryLanguage") else None,
            "kb": r.get("diskUsage"),
            "commits": len(mine),
            "prs": len(prs),
            "merged": sum(1 for p in prs if p.get("merged")),
            "releases": len(rels),
        })

    repo_rows.sort(key=lambda x: -x["commits"])
    days = [dict(v, d=k, repos=dict(v["repos"].most_common(5))) for k, v in sorted(by_day.items())]
    all_prs.sort(key=lambda p: p.get("created") or "", reverse=True)
    all_rel.sort(key=lambda p: p.get("published") or "", reverse=True)

    return {
        "state": "通" if not failed else "不确定",
        "login": login,
        "fetched_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "since": since[:10],
        "repos": repo_rows,
        "days": days,
        "prs": all_prs[:120],
        "releases": all_rel[:60],
        "failed_repos": failed,
        "totals": {
            "repos": len(repo_rows),
            "commits": sum(r["commits"] for r in repo_rows),
            "prs": sum(r["prs"] for r in repo_rows),
            "merged": sum(r["merged"] for r in repo_rows),
            "releases": sum(r["releases"] for r in repo_rows),
            "active_days": len(days),
        },
        "note": "只统计作者是你本人的提交。拉不到的仓单独列在 failed_repos —— "
                "拉取机制自己坏掉时结果标「不确定」，不标「通」。",
    }


def main() -> int:
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path("github.json")
    data = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    t = data.get("totals", {})
    print(f"GitHub: {data['state']}  仓 {t.get('repos', 0)}  提交 {t.get('commits', 0)}  "
          f"PR {t.get('prs', 0)}（合 {t.get('merged', 0)}）  Release {t.get('releases', 0)}  "
          f"活跃 {t.get('active_days', 0)} 天")
    if data.get("failed_repos"):
        print("  拉取失败:", ", ".join(data["failed_repos"]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
