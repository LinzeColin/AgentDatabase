#!/usr/bin/env python3
"""Build the pilot pack: five tasks chosen to break the batch in five ways.

A pilot whose five characters all look alike proves nothing. Each entry below
loads a different axis that the full run of 297 could fail on independently, so
one round of results says *which* axis failed rather than just "quality is bad":

    ganyu       long flowing pale hair + wide skirt   → the left-35% containment
                                                        rule, the hardest one
    hu-tao      dark hair, hat, saturated red/black   → high-contrast subject
                                                        against a pale sky
    kafka       Star Rail, tight silhouette, sci-fi   → a different scene pool
                                                        and an easy shape
    ellen       Zenless, short bob, non-human tail,   → urban scene, and whether
                urban neon                              the anchor holds a
                                                        non-human feature
    <outfit>    an alternate outfit, not the default  → outfit fidelity: does the
                                                        result wear the right
                                                        clothes

Both light and dark are produced for each, so the day/night pairing rule is
exercised five times over.

Usage:
    python3 build_pilot.py --library … --rosters ../research --out /tmp/pilot
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_taskpack as base

# (game, character, variant, axis, what a failure here would mean)
PILOT = [
    ("genshin", "ganyu", "default",
     "长飘发 + 大裙摆",
     "若头发/裙摆越过左 35% 线 → 构图契约没被遵守，全量必然大面积返工"),
    ("genshin", "hu-tao", "default",
     "高饱和深色主体 + 浅色天空",
     "若主体与背景对比失衡或颜色溢出 → 需要在 prompt 里补光比约束"),
    ("hsr", "kafka", "default",
     "另一作 + 紧身剪影 + 科幻场景池",
     "若科幻场景池右侧仍然堆细节 → SCENES 里 hsr 那条要重写"),
    ("zzz", "ellen", "default",
     "短发 + 非人特征（鲨鱼尾）+ 都市霓虹",
     "若鲨鱼尾丢失或霓虹把右侧填满 → 锚图权重不足 / 都市场景池不可用"),
]
# The fifth is an outfit variant, resolved at build time from whatever the
# library actually has — hardcoding one risks pointing at a character whose
# outfit art failed to download.
OUTFIT_AXIS = ("时装变体（非默认装）",
               "若穿的还是默认装 → 锚图没被真正当作参考图使用，这是全量的致命问题")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rosters", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    full = json.loads((args.out.parent / "taskpack" / "manifest.json").read_text(encoding="utf-8")) \
        if (args.out.parent / "taskpack" / "manifest.json").exists() else None
    if full is None:
        sys.exit("先跑 build_taskpack.py 生成全量 manifest.json")
    index = {t["id"]: t for t in full["tasks"]}

    picked: list[tuple[dict, str, str]] = []
    for game, character, variant, axis, risk in PILOT:
        task = index.get(f"{game}/{character}/{variant}")
        if task is None:
            print(f"  ! 跳过 {game}/{character}/{variant}（不在全量清单里）")
            continue
        picked.append((task, axis, risk))

    chosen_ids = {t["id"] for t, _, _ in picked}
    outfit = next((t for t in full["tasks"]
                   if t["variant"] != "default"
                   and t["character"] not in {p[0]["character"] for p in picked}
                   and t["id"] not in chosen_ids), None)
    if outfit is not None:
        picked.append((outfit, *OUTFIT_AXIS))

    anchors = args.out / "anchors"
    if args.out.exists():
        shutil.rmtree(args.out)
    (args.out / "docs").mkdir(parents=True)

    tasks = []
    for task, axis, risk in picked:
        source = args.out.parent / "taskpack" / task["anchor"]
        target = anchors / Path(task["anchor"]).relative_to("anchors")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        entry = dict(task)
        entry["pilot_axis"] = axis
        entry["failure_meaning"] = risk
        tasks.append(entry)

    (args.out / "manifest.json").write_text(json.dumps({
        "pack": "HarnessUI-skin-backplates-PILOT",
        "version": "1.0.0-pilot",
        "built": "2026-08-19",
        "purpose": "全量 297 条之前的校准批次：5 个角色各压一个不同的失败维度",
        "task_count": len(tasks),
        "image_count": len(tasks) * 2,
        "read_first": ["README.md", "docs/SPEC.md", "docs/ACCEPTANCE.md"],
        "tasks": tasks,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for name in ("SPEC.md", "ACCEPTANCE.md"):
        shutil.copyfile(args.out.parent / "taskpack" / "docs" / name, args.out / "docs" / name)
    shutil.copytree(args.out.parent / "taskpack" / "tools", args.out / "tools")

    # The README is written here rather than kept as a file beside the script:
    # this builder wipes its output directory on every run, so a hand-placed
    # README silently disappeared on the first rebuild.
    rows = "\n".join(
        f"| `{t['id']}` | {t['pilot_axis']} | {t['failure_meaning']} |" for t in tasks)
    (args.out / "README.md").write_text(f"""# HarnessUI 试产包 v1.0.0-pilot

**{len(tasks)} 条任务 / {len(tasks) * 2} 张图。** 全量 297 条之前的校准批次。

## 为什么是这几个

不是抽样，是**每个角色压一个不同的失败维度**。五个都过，全量才有把握；
某一个不过，也能直接指出是哪条规则没落地，而不是笼统说"质量不行"。

| 任务 | 压的维度 | 不通过说明什么 |
|---|---|---|
{rows}

最后一条最关键：它验证**锚图到底有没有起作用**。
prompt 里**故意没有描述角色外观**——如果生成出来穿的是默认装而非指定时装，
说明模型只读了文字，那全量 297 条会全部产出"泛化动漫少女"。

## 怎么跑

1. 先读 `docs/SPEC.md`，尤其第 3 节构图契约。
2. 按 `manifest.json` 逐条生成，每条**必须把 `anchor` 指向的图作为角色参考图输入**。
3. 输出到 `output/<game>/<character>/<variant>/{{light,dark}}.png` + `meta.json`。
4. 交回前跑 `python3 tools/validate_output.py --pack . --output output`。

模型建议：`Midjourney Niji 7` 出主体 → `Seedream 5.0 Pro` 压构图 → `General Image Pro` 放 4K。
只能选一个就用 **Midjourney Niji 7**。

## 交回时请一并说明

- 用了哪些模型、每张的 seed
- `validate_output.py` 的输出
- 哪些 ACCEPTANCE 条款你觉得**做不到**——比"尽力了"有用得多，
  做不到我们改规范，不改就全量翻车

验收标准见 `docs/ACCEPTANCE.md`（A–G 共 26 条，每条可判定）。
版权与用途见 `docs/SPEC.md` 第 9 节。
""", encoding="utf-8")

    print(f"试产包 {len(tasks)} 条任务 / {len(tasks) * 2} 张图")
    for task in tasks:
        print(f"  · {task['id']:<38} {task['pilot_axis']}")


if __name__ == "__main__":
    main()
