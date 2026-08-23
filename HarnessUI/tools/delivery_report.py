#!/usr/bin/env python3
"""跑完之后的交付报告。数字全部从账本和磁盘读，不许估。

为什么要有它：上一轮我用「提交次数」报工期，比真实成品数乐观了 17 倍；
又用魔数校验报「0 坏」，换成摘要比对时才发现 266 张对不上。
**生成总数和可用成品是两个数，废片是它们的差，三个都要报。**

Usage:
    python3 delivery_report.py --state batch.json --out ../delivery/report-v1.8.0.md
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", type=pathlib.Path, required=True)
    ap.add_argument("--catalog", type=pathlib.Path,
                    default=pathlib.Path.home() / ".harness-ui/catalog.json")
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--share", default="smb://192.168.0.1/share/03_资料库/MetaData/HarnessUI")
    ap.add_argument("--started", help="提交时间，用来算耗时（HH:MM）")
    args = ap.parse_args()

    state = json.loads(args.state.read_text(encoding="utf-8"))
    units = state["units"]
    accepted = [u for u in units.values() if u["status"] == "accepted"]
    # attempt 是**第几次尝试**（1 起），不是重试次数。第一版当成重试次数算，
    # 报出「一次通过率 0%」——真实是 97.9%。这正是「数产出不数尝试」那条坑
    # 的同一个形状，只不过这次是在工具里犯的。
    generated = sum(max(u.get("attempt", 1), 1) for u in units.values())
    retries = generated - len(units)
    wasted = generated - len(accepted)
    first_pass = sum(1 for u in accepted if u.get("attempt", 1) <= 1)

    out_dir = pathlib.Path(state["out"]) / "output"
    on_disk = sum(1 for p in out_dir.rglob("*.png") if "reject" not in p.name) if out_dir.exists() else 0

    catalog = json.loads(args.catalog.read_text(encoding="utf-8")) if args.catalog.exists() else {}
    by_game: dict = {}
    for e in catalog.get("entries", []):
        by_game[e["gameName"]] = by_game.get(e["gameName"], 0) + 1

    spend = state.get("spend_usd", 0.0)
    lines = [
        f"# 交付报告 · 任务包 {state.get('pack_version')}", "",
        f"生成于 {time.strftime('%Y-%m-%d %H:%M')}，数字全部来自账本 `{args.state.name}` 与磁盘。", "",
        "## 产出", "",
        "| | |", "|---|---|",
        f"| **生成图片总数** | {generated}（{len(units)} 张目标 + {retries} 次重试）|",
        f"| **实际可用成品** | **{len(accepted)}** |",
        f"| **废片** | {wasted} |",
        f"| 一次通过率 | {first_pass}/{len(units)} = {first_pass / max(len(units),1) * 100:.1f}% |",
        f"| 落盘核对 | 输出目录实有 {on_disk} 张 |",
        f"| 规格 | {state.get('model')} @ {state.get('size')} |",
        f"| 轮次 | {state.get('round')} |", "",
        "## 成本", "",
        f"- **API 实付 ${spend:.2f}**（账本累计，不是估算）",
        f"- 单张均价 ${spend / max(len(accepted),1):.4f}（按可用成品算）",
        f"- 含废片的调用均价 ${spend / max(generated,1):.4f}", "",
        "## 素材保存地址", "",
        f"- 运行时（宿主直接读）：`~/.harness-ui/master/` · `display/` · `thumb/`",
        f"- NAS 归档：`{args.share}/<游戏中文>/<角色>/skins/<变体>/`",
        f"- 仓内治理：`HarnessUI/delivery/`（manifest + 验收台账）",
        f"- 人工复核页：`~/.harness-ui/review.html`（build_review.py 生成，需素材服务在跑）", "",
        "## 上线状态", "",
        f"- 目录 **{catalog.get('count', 0)} 条**：" + " · ".join(f"{k} {v}" for k, v in sorted(by_game.items())),
        "- 轮播周期：已清空重洗（不重洗新素材这轮走完前不会出现）",
        "- 菜单栏控制器：读盘即时生效",
        "- DSH：**Cmd+R**（catalog 只在挂载时取一次）",
        "- Kimi：**重启**（catalog 缓存在内存里）", "",
    ]
    fails: dict = {}
    for u in units.values():
        for f in (u.get("fails") or []):
            key = f.split("（")[0].split("(")[0][:40]
            fails[key] = fails.get(key, 0) + 1
    if fails:
        lines += ["## 重试原因分布", "", "| 原因 | 次数 |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in sorted(fails.items(), key=lambda x: -x[1])]
        lines += [""]

    text = "\n".join(lines)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(f"交付报告 → {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
