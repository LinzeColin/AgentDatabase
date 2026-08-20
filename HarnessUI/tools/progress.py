#!/usr/bin/env python3
"""白箱进度：百分比 + 已完成/未完成 + **远端批次状态**，一条命令看清。

两个版本合并而来：
* 旧版给的是「百分比 + 已完成/未完成」——好在一眼能看出还剩多少；
* 新版加了「哪个阶段在跑」——好在能判断是不是卡住了。

新版单独用有个致命缺陷：**它只看本机进程**。批次提交出去之后本机没有任何进程在跑
（图在 OpenAI 那边烤），六个阶段全显示「停」，看起来像什么都没在做。
所以这一版必须直接问远端批次要 request_counts。

    python3 progress.py                # 一次快照
    python3 progress.py --watch        # 每 60 秒刷一次
    python3 progress.py --state <账本> # 指定批次账本
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import time
import urllib.request

SCRATCH = pathlib.Path("/private/tmp/claude-501/-Users-linzezhang-Movies-Hub-Projects"
                       "/c6201bcb-d0e5-4667-a951-f51367d1df4d/scratchpad")
RT = pathlib.Path.home() / ".harness-ui"
GAME_ZH = {"genshin": "原神", "hsr": "崩铁", "zzz": "绝区零", "wuwa": "鸣潮",
           "nte": "异环", "wzry": "王者荣耀"}

STAGES = [("锚图采集", "collect_refs.py"), ("换装采集", "collect_outfits.py"),
          ("锚图拉取", "pull_new.py"), ("任务包构建", "build_taskpack.py"),
          ("批次驱动", "batch_run.py|batch_watch.sh"), ("定点重出", "regen.py"),
          ("派生图", "make_derivatives.py"), ("归档 NAS", "archive.py")]


def bar(done: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "—" * width
    filled = int(done / total * width)
    return "█" * filled + "░" * (width - filled)


def running(pattern: str) -> bool:
    """pattern 可以用 | 分隔多个匹配串，逐个查——pgrep 的 ERE 在不同 macOS 版本上行为不一致。"""
    return any(_running_one(p) for p in pattern.split("|"))


def _running_one(pattern: str) -> bool:
    pids = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.split()
    if not pids:
        return False
    # macOS 的 pgrep 没有 -a，只给 PID；命令行要另外用 ps 取。
    ps = subprocess.run(["ps", "-o", "command=", "-p", ",".join(pids)],
                        capture_output=True, text=True).stdout
    for cmd in ps.splitlines():
        cmd = cmd.strip()
        # 包装用的 zsh 和等待循环的命令行里也含匹配串，不算数
        if "shell-snapshots" in cmd or cmd.startswith("/bin/zsh -c"):
            continue
        head = cmd.split(" ", 1)[0]
        if head.endswith(("python3", "python", "bash", "sh")):
            return True
    return False


def remote_counts(state: dict) -> tuple[int, int, str]:
    """问远端批次：已出图 / 总数 / 状态。本机没进程 ≠ 没在跑。"""
    try:
        token = pathlib.Path(state["key_file"]).read_text().strip()
    except Exception:
        return 0, 0, "取不到 key"
    done = total = 0
    status = "—"
    for b in state.get("batches", []):
        if b.get("harvested"):
            continue
        try:
            req = urllib.request.Request(f"https://api.openai.com/v1/batches/{b['id']}",
                                         headers={"Authorization": f"Bearer {token}"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            c = data.get("request_counts", {})
            done += c.get("completed", 0) + c.get("failed", 0)
            total += c.get("total", 0)
            status = data.get("status", "—")
        except Exception as exc:
            status = f"查询失败 {str(exc)[:24]}"
    return done, total, status


def find_state(explicit: str | None) -> pathlib.Path | None:
    if explicit:
        return pathlib.Path(explicit)
    cands = [p for p in SCRATCH.glob("**/state.json")] + list(SCRATCH.glob("batch*.json"))
    live = []
    for p in cands:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not s.get("units"):
            continue
        open_ = sum(1 for u in s["units"].values() if u["status"] in ("pending", "retry", "in_batch"))
        live.append((open_ > 0, p.stat().st_mtime, p))
    if not live:
        return None
    live.sort(reverse=True)          # 有未结算的优先，其次最近改动的
    return live[0][2]


def snapshot(state_path: pathlib.Path | None) -> str:
    L = [f"═══ 进度 {time.strftime('%m-%d %H:%M:%S')} ═══", ""]

    if state_path and state_path.exists():
        s = json.loads(state_path.read_text(encoding="utf-8"))
        units = s["units"]
        total = len(units)
        acc = sum(1 for u in units.values() if u["status"] == "accepted")
        openv = sum(1 for u in units.values() if u["status"] in ("pending", "retry", "in_batch"))
        pct = acc / total * 100 if total else 0
        L += [f"【本轮出图】包 {s.get('pack_version')} · 账本 {state_path.parent.name}/{state_path.name}",
              f"  {bar(acc, total)} {pct:5.1f}%   已落盘 {acc} / {total}",
              f"  未结算 {openv} · 已花 ${s.get('spend_usd', 0):.2f} · 轮次 {s.get('round')}"]
        if openv:
            done, tot, status = remote_counts(s)
            if tot:
                L.append(f"  远端批次 {status}：{bar(done, tot, 20)} {done}/{tot} 已出图"
                         f"（整批完成才落盘）")
            else:
                L.append(f"  远端批次 {status}")
        by: dict = {}
        for k, u in units.items():
            g = k.split("/")[0]
            d = by.setdefault(g, [0, 0])
            d[1] += 1
            if u["status"] == "accepted":
                d[0] += 1
        L.append("")
        L.append("  按 IP：" + " · ".join(f"{GAME_ZH.get(g,g)} {d[0]}/{d[1]}" for g, d in sorted(by.items())))
    else:
        L.append("【本轮出图】没有在跑的批次账本")

    L += ["", "【阶段】"]
    for name, pat in STAGES:
        L.append(f"  {'▶ 跑着' if running(pat) else '· 停  '}  {name}")

    try:
        cat = json.loads((RT / "catalog.json").read_text(encoding="utf-8"))
        per: dict = {}
        for e in cat["entries"]:
            per[e["gameName"]] = per.get(e["gameName"], 0) + 1
        L += ["", f"【素材库】目录 {cat['count']} 条 · " + " · ".join(f"{k} {v}" for k, v in sorted(per.items()))]
    except Exception:
        pass
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()
    while True:
        print(snapshot(find_state(args.state)), flush=True)
        if not args.watch:
            return
        print(flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
