#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**蒸馏版本新鲜度**：专家团队里的人，是不是用够新的蒸馏版本做出来的。

## 原始意图，与它原来错在哪

原判据是 `build_release_bundle.py` 里的一行：
`persona-distiller/VERSION` 必须等于 `persona-distiller-group/VERSION`，
意图是「人物蒸馏到 v0.0.0.8 了，专家团队就不该是 v0.0.0.6/7 蒸出来的」。

**意图对，判据测的不是那件事**：

1. 它是**包级的一个数字，不是每人一条记录**。97 份 `registration.json` 里
   原本没有任何字段说明「这个人由哪个蒸馏版本产出」。
2. **它可以在属性不成立时被满足**——把 group 的 `VERSION` 从 8 改成 14
   是一次文本编辑，一个人也没重蒸，门当场变绿，保证变成假话。
3. 它**在打包时才触发**。用旧版本蒸的人照样入库，只是最后发行物构建不出来
   ——实际后果是自 v0.0.0.9 起 `PersonaDistiller-Final-*.zip` 一次也没构建成功。

## 现在的判据：滚动兼容下限（用户裁定）

> 最低兼容下限 = 人物蒸馏当前版本号 − 10。
> 例：人物蒸馏为 `v0.0.0.98`，则专家团队需要是 `0.0.0.88+`。

**下限以下的不重蒸**（同为用户裁定）——本检查器默认**只报不拦**，
低于下限的人进入重蒸台账，等 600 人整体完成后统一重蒸对齐。
`--strict` 才把低于下限变成非零退出码；发行流程**不使用** `--strict`。

严格相等在算术上就不成立：全库 97 人 × 约 120 万 token/人 ≈ 1.16 亿 token，
而周额度约 1500 万——单次升版要 7.7 周，而升版是按天发生的。

## 两类值不能混

`distilled_with_source` 区分第一手与推断：

| 来源 | 含义 |
|---|---|
| `artifact-manifest` | 打包时由 distiller 盖进交付 manifest，**实测** |
| `git-first-commit` | 事后从首次落盘提交重建，**推断**（登记时间 ≈ 蒸馏时间） |
| `git-first-commit:bulk-repackage` | 同上，但那次提交是批量重打包，**该值是上界**：正文更旧 |
| `unknown` | 归因不到，**不得当成合规** |

上界值单独统计。把上界当实测用，等于用「重打包」冒充「重蒸」——
那正是原判据可以被一次文本编辑骗过的同一个病。

退出码：0 = 通过（默认下限以下也算通过，只报）；1 = `--strict` 且有低于下限；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

FLOOR_OFFSET = 10  # 用户裁定：下限 = 当前版本号末位 − 10
ROOT_DEFAULT = pathlib.Path(__file__).resolve().parent.parent


def parse_version(text: str | None) -> tuple[int, ...] | None:
    if not text:
        return None
    body = text.strip()
    if body.startswith("v"):
        body = body[1:]
    parts = body.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def floor_for(current: tuple[int, ...]) -> tuple[int, ...]:
    """下限 = 当前版本末位 − 10，夹到 ≥1（版本号没有 0 或负数档）。"""
    return (*current[:-1], max(1, current[-1] - FLOOR_OFFSET))


def fmt(version: tuple[int, ...]) -> str:
    return "v" + ".".join(str(p) for p in version)


def survey(registry_root: pathlib.Path, current: tuple[int, ...]) -> dict:
    floor = floor_for(current)
    below, at_or_above, upper_bound_only, unknown = [], [], [], []

    for record_path in sorted(registry_root.glob("*/*/registration.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        name = record.get("canonical_name") or record_path.parent.name
        for entry in record.get("versions") or []:
            version = parse_version(entry.get("distilled_with"))
            source = entry.get("distilled_with_source") or "unknown"
            item = {
                "name": name,
                "category": record.get("registration_category"),
                "product_version": entry.get("product_version"),
                "distilled_with": entry.get("distilled_with"),
                "source": source,
            }
            if version is None or source == "unknown":
                unknown.append(item)
            elif version < floor:
                below.append(item)
            else:
                at_or_above.append(item)
                if source.endswith("bulk-repackage"):
                    upper_bound_only.append(item)

    return {
        "current": fmt(current),
        "floor": fmt(floor),
        "floor_rule": f"当前版本末位 − {FLOOR_OFFSET}（夹到 ≥1）",
        "total": len(below) + len(at_or_above) + len(unknown),
        "at_or_above_floor": len(at_or_above),
        "below_floor": len(below),
        "unknown": len(unknown),
        "upper_bound_only": len(upper_bound_only),
        "below_floor_detail": below,
        "unknown_detail": unknown,
    }


# --------------------------------------------------------------------------
# 负对照
# --------------------------------------------------------------------------
def _fixture(root: pathlib.Path, people: list[tuple[str, str | None, str]]) -> pathlib.Path:
    for index, (name, version, source) in enumerate(people):
        d = root / "族" / f"p{index}"
        d.mkdir(parents=True)
        entry = {"product_version": "0.0.0.1", "distilled_with_source": source}
        if version is not None:
            entry["distilled_with"] = version
        (d / "registration.json").write_text(json.dumps(
            {"canonical_name": name, "registration_category": "族", "versions": [entry]},
            ensure_ascii=False), encoding="utf-8")
    return root


def self_test() -> int:
    failures = []

    if floor_for((0, 0, 0, 98)) != (0, 0, 0, 88):
        failures.append("下限算错：v0.0.0.98 应得 v0.0.0.88（用户给的例子）")
    if floor_for((0, 0, 0, 14)) != (0, 0, 0, 4):
        failures.append("下限算错：v0.0.0.14 应得 v0.0.0.4")
    if floor_for((0, 0, 0, 3)) != (0, 0, 0, 1):
        failures.append("下限未夹到 ≥1：v0.0.0.3 不该得出 0 或负数")

    with tempfile.TemporaryDirectory() as td:
        root = _fixture(pathlib.Path(td) / "reg", [
            ("刚好在下限上", "v0.0.0.4", "artifact-manifest"),
            ("高于下限", "v0.0.0.9", "artifact-manifest"),
            ("低于下限一档", "v0.0.0.3", "git-first-commit"),
            ("远低于下限", "v0.0.0.1", "git-first-commit"),
            ("上界值，够新", "v0.0.0.6", "git-first-commit:bulk-repackage"),
            ("归因不到", None, "unknown"),
        ])
        r = survey(root, (0, 0, 0, 14))

        for label, key, want in (
            ("低于下限计数", "below_floor", 2),
            ("达标计数", "at_or_above_floor", 3),
            ("归因不到计数", "unknown", 1),
            ("上界值单独计数", "upper_bound_only", 1),
            ("总数", "total", 6),
        ):
            if r[key] != want:
                failures.append(f"{label}：得 {r[key]}，应为 {want}")

        # 边界：恰好等于下限的人**不算**低于下限
        if any(i["name"] == "刚好在下限上" for i in r["below_floor_detail"]):
            failures.append("边界错：恰好等于下限被判成低于下限")
        # 归因不到的人**不得**被算成达标
        if r["unknown"] and any(i["name"] == "归因不到" for i in r["below_floor_detail"]):
            failures.append("归因不到的人被混进了「低于下限」，两类含义不同")

    for f in failures:
        print(f"✗ {f}")
    if failures:
        print(f"负对照未通过：{len(failures)} 项")
        return 1
    print("负对照通过：下限算式 3 例（含用户给的 v0.0.0.98→v0.0.0.88）、"
          "分档 5 例、边界 1 例、上界值单独计数 1 例")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="蒸馏版本新鲜度：滚动兼容下限 = 当前版本 − 10")
    ap.add_argument("--root", type=pathlib.Path, default=ROOT_DEFAULT,
                    help="persona-distiller 根目录")
    ap.add_argument("--registry-root", type=pathlib.Path, default=None,
                    help="canonical group 根目录（默认取同级 persona-distiller-group）")
    ap.add_argument("--strict", action="store_true",
                    help="低于下限时以非零退出码失败。发行流程**不用**这个开关——"
                         "用户裁定下限以下不重蒸，只记台账。")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = args.root.resolve()
    current = parse_version((root / "VERSION").read_text(encoding="utf-8")
                            if (root / "VERSION").is_file() else None)
    if current is None:
        print(f"用法错误：读不到 {root / 'VERSION'}", file=sys.stderr)
        return 3
    registry_root = (args.registry_root or root.parent / "persona-distiller-group").resolve()
    if not registry_root.is_dir():
        print(f"用法错误：{registry_root} 不是目录", file=sys.stderr)
        return 3

    report = survey(registry_root, current)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"当前蒸馏版本 {report['current']}｜兼容下限 {report['floor']}"
              f"（{report['floor_rule']}）")
        print(f"  达标        {report['at_or_above_floor']:>3} / {report['total']}")
        print(f"  低于下限    {report['below_floor']:>3}"
              f"　← 按裁定不重蒸，进重蒸台账（任务 #29）")
        print(f"  归因不到    {report['unknown']:>3}"
              f"　← 不计入达标")
        if report["upper_bound_only"]:
            print(f"  其中上界值  {report['upper_bound_only']:>3}"
                  f"　← 来自批量重打包，只重打包未重蒸，实际正文更旧")
        for item in report["below_floor_detail"][:20]:
            print(f"    · {item['name']}（{item['category']}）"
                  f" {item['distilled_with']}｜{item['source']}")
        if len(report["below_floor_detail"]) > 20:
            print(f"    …… 另有 {len(report['below_floor_detail']) - 20} 人，用 --json 看全量")

    if args.strict and (report["below_floor"] or report["unknown"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
