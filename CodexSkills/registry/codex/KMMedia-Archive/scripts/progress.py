#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KMMedia-Archive 白箱进度：百分比 + 已完成/未完成 + 阶段运行状态，一条命令看清。

    python3 progress.py                # 一次快照
    python3 progress.py --watch        # 每 60 秒刷一次
    python3 progress.py --workdir <dir> # 指定 pipeline 工作目录

模仿 character-skin-pipeline v0.0.2 的 progress.py：三段输出——
① 本轮进度：登记表已改名/总数、标注已/待、accept 状态
② 阶段是否在跑：scan/probe/thumbs/dedup/label/rename/registry/accept/report 谁活着
③ 素材库概况：照片/视频/文件、缩略图数、账本条目

数据全部来自本地产物（workdir 下 csv/jsonl），不碰 SMB、不打扰运行中的 pipeline。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import subprocess
import time

DEFAULT_WORKDIR = pathlib.Path("/tmp/kmvideo_work/pipeline")
REG = DEFAULT_WORKDIR / "素材登记表.new.csv"
DESC = DEFAULT_WORKDIR / "desc.csv"
ACCEPT = DEFAULT_WORKDIR / "accept_report.json"

STAGES = [("scan 扫描", "kmvideo_pipeline.py scan"),
          ("probe 探测", "kmvideo_pipeline.py probe"),
          ("thumbs 缩略图", "kmvideo_pipeline.py thumbs"),
          ("dedup 去重", "kmvideo_pipeline.py dedup"),
          ("label 标注", "kmvideo_pipeline.py label"),
          ("rename 改名", "kmvideo_pipeline.py rename"),
          ("registry 登记", "kmvideo_pipeline.py registry"),
          ("accept 自验收", "kmvideo_pipeline.py accept"),
          ("report 汇总", "kmvideo_pipeline.py report")]


def bar(done: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "—" * width
    filled = int(done / total * width)
    return "█" * filled + "░" * (width - filled)


def running(pattern: str) -> bool:
    pids = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True).stdout.split()
    if not pids:
        return False
    ps = subprocess.run(["ps", "-o", "command=", "-p", ",".join(pids)],
                        capture_output=True, text=True).stdout
    for cmd in ps.splitlines():
        cmd = cmd.strip()
        if "progress.py" in cmd or cmd.startswith("/bin/bash -c") or cmd.startswith("/bin/zsh -c"):
            continue  # 排除自身与包装层
        if "kmvideo_pipeline.py" in cmd:
            return True
    return False


def read_reg(reg: pathlib.Path):
    """登记表：总行、已改名、脱敏非无数、有描述数。"""
    if not reg.exists():
        return {}
    with open(reg, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    renamed = sum(1 for r in rows if r.get("文件名") != r.get("原文件名"))
    sens = sum(1 for r in rows if (r.get("脱敏风险") or "").strip() not in ("", "无"))
    desc = sum(1 for r in rows if (r.get("描述") or "").strip())
    videos = sum(1 for r in rows if r.get("文件名", "").lower().endswith((".mp4", ".mov")))
    return {"total": total, "renamed": renamed, "sens": sens, "desc": desc, "videos": videos,
            "photos": total - videos}


def read_desc(desc: pathlib.Path):
    """desc.csv：已标注 / 待确认。"""
    if not desc.exists():
        return {"labeled": 0, "pending": 0}
    with open(desc, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    pending = sum(1 for r in rows if (r.get("说明") or "").strip() in ("", "待确认"))
    return {"labeled": len(rows) - pending, "pending": pending}


def read_accept(acc: pathlib.Path):
    if not acc.exists():
        return {}
    try:
        d = json.loads(acc.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {"pass": len(d.get("pass", [])), "fail": len(d.get("fail", [])),
            "fail_items": [x["项"] for x in d.get("fail", [])]}


def snapshot(workdir: pathlib.Path) -> str:
    reg = workdir / "素材登记表.new.csv"
    desc = workdir / "desc.csv"
    acc = workdir / "accept_report.json"
    reg_csv = workdir / "素材登记表.csv"

    r = read_reg(reg if reg.exists() else reg_csv)
    d = read_desc(desc)
    a = read_accept(acc)

    L = [f"═══ KMMedia 进度 {time.strftime('%m-%d %H:%M:%S')} ═══", ""]

    # ① 本轮进度
    if r:
        pct = r["renamed"] / r["total"] * 100 if r["total"] else 0
        L += ["【登记表】",
              f"  {bar(r['renamed'], r['total'])} {pct:5.1f}%   已改名 {r['renamed']} / {r['total']}"]
        if d:
            lpct = d["labeled"] / (d["labeled"] + d["pending"]) * 100 if (d["labeled"] + d["pending"]) else 0
            L.append(f"  标注 {bar(d['labeled'], d['labeled']+d['pending'], 20)} {lpct:4.1f}%"
                     f"  已标 {d['labeled']} · 待确认 {d['pending']}")
        if a:
            status = "pass ✅" if a["fail"] == 0 else f"fail {a['fail']}: {a['fail_items'][0] if a['fail_items'] else ''}"
            L.append(f"  accept {status}")
    else:
        L.append("【登记表】暂无产物（还没跑 registry，或在别的 workdir）")

    # ② 阶段是否在跑
    L += ["", "【阶段】"]
    any_run = False
    for name, pat in STAGES:
        run = running(pat)
        any_run = any_run or run
        L.append(f"  {'▶ 跑着' if run else '· 停  '}  {name}")
    if not any_run:
        L.append("  （无 pipeline 进程在跑 —— 若刚提交增量，见 workdir 日志确认）")

    # ③ 素材库概况
    L += ["", "【素材库】"]
    if r:
        L.append(f"  照片 {r['photos']} · 视频 {r['videos']} · 脱敏非无 {r['sens']} · 有描述 {r['desc']}")
    thumbs = workdir / "thumbs"
    if thumbs.is_dir():
        try:
            n = sum(1 for _ in thumbs.iterdir())
            L.append(f"  缩略图 {n}")
        except Exception:
            pass
    L.append(f"  workdir {workdir}")

    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workdir", default=str(DEFAULT_WORKDIR))
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()
    wd = pathlib.Path(args.workdir)
    while True:
        print(snapshot(wd), flush=True)
        if not args.watch:
            return
        print(flush=True)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
