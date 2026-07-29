#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 git 回填既有登记记录的 `distilled_with`（哪个蒸馏版本产出了这个人）。

## 为什么需要回填

`distilled_with` 从 v0.0.0.15 起由 `delivery_builder.py` 在**打包时**盖进交付 manifest，
随产物一起走。但在那之前入库的人物，交付 manifest 里没有这个字段——
而「专家团队里的人是不是用正确的蒸馏版本做出来的」这件事，正是要靠它才能回答。

## 回填值是**推断**，不是测量——必须标注来源

唯一可用的证据是 git：`registration.json` 首次落盘的那个提交，
当时 `persona-distiller/VERSION` 是多少。据此得到的值有两个已知偏差：

1. **它是「登记时」的版本，不是「蒸馏时」的版本。** 两者通常同一天，但不保证。
2. **对批量重打包进来的人物，它是上界而非实际值。**
   `a31cb12d`（2026-07-26）把既有 70 人一次性迁进 12 族目录——
   那次**只重打包没重蒸**，正文内容来自 7 族时代（≤ v0.0.0.5），
   但 git 会把它们全部归到迁移当时的 v0.0.0.6。

因此本脚本写两个字段：`distilled_with` 与 `distilled_with_source`，
后者取值 `git-first-commit` 或 `git-first-commit:bulk-repackage`。
**上界值不得被当成实测值使用**——`check_distillation_freshness.py` 会分开统计。

`artifact_created_at` 不能用作证据：全库 99 条里 15 条恰好是 `00:00:00Z`、
54 条的分钟数不是 00/30，形态明显是回填与实测混在一起；
且已核实至少一例与 git 矛盾（`shigeo-shingo` 记 07-24，实际首次落盘 07-26）。

退出码：0 = 完成；1 = 有记录无法归因；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

# 已知的批量重打包提交 → 其归因值是上界。
# 新增条目时必须同时在这里登记，否则上界会被当成实测值。
BULK_REPACKAGE_COMMITS = {
    "a31cb12d": "2026-07-26 十二族重组：70 人只重打包未重蒸，正文来自 ≤v0.0.0.5",
}

REGISTRY_ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION_PATH_IN_REPO = "CodexSkills/registry/codex/persona-distiller/VERSION"


def _git(*args: str, cwd: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-c", "core.quotepath=false", *args],
                          cwd=str(cwd), capture_output=True, text=True)


def repo_root(start: pathlib.Path) -> pathlib.Path | None:
    proc = _git("rev-parse", "--show-toplevel", cwd=start)
    return pathlib.Path(proc.stdout.strip()) if proc.returncode == 0 else None


def attribute(record_path: pathlib.Path, repo: pathlib.Path) -> tuple[str | None, str, str]:
    """→ (版本, 来源, 说明)。归因不到就返回 (None, 'unknown', 原因)。"""
    rel = record_path.relative_to(repo).as_posix()
    proc = _git("log", "--diff-filter=A", "--format=%h", "-1", "--", rel, cwd=repo)
    commit = proc.stdout.strip()
    if not commit:
        return None, "unknown", "git 里找不到首次落盘提交（可能尚未提交）"
    shown = _git("show", f"{commit}:{VERSION_PATH_IN_REPO}", cwd=repo)
    if shown.returncode != 0:
        return None, "unknown", f"提交 {commit} 处读不到 VERSION"
    version = shown.stdout.strip()
    if commit in BULK_REPACKAGE_COMMITS:
        return version, "git-first-commit:bulk-repackage", BULK_REPACKAGE_COMMITS[commit]
    return version, "git-first-commit", f"首次落盘提交 {commit}"


def run(registry_root: pathlib.Path, apply_changes: bool) -> dict:
    repo = repo_root(registry_root)
    if repo is None:
        return {"error": "不在 git 仓库内，无法重建"}

    changed, skipped, failed = [], [], []
    for record_path in sorted(registry_root.glob("*/*/registration.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        version, source, note = attribute(record_path, repo)
        if version is None:
            failed.append({"record": str(record_path.relative_to(registry_root)), "why": note})
            continue
        touched = False
        for entry in record.get("versions") or []:
            # 第一手（打包时盖的）永远优先，绝不被重建值覆盖。
            if entry.get("distilled_with_source") == "artifact-manifest":
                continue
            if entry.get("distilled_with") == version and entry.get("distilled_with_source") == source:
                continue
            entry["distilled_with"] = version
            entry["distilled_with_source"] = source
            entry["distilled_with_note"] = note
            touched = True
        if not touched:
            skipped.append(str(record_path.relative_to(registry_root)))
            continue
        if apply_changes:
            # 用 registry_core 自己的原子写，格式与中断安全性都与既有记录一致。
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
            from registry_core import atomic_write_json  # noqa: PLC0415
            atomic_write_json(record_path, record)
        changed.append({"record": str(record_path.relative_to(registry_root)),
                        "distilled_with": version, "source": source})
    return {"applied": apply_changes, "changed": len(changed), "already_current": len(skipped),
            "failed": failed, "details": changed}


def main() -> int:
    ap = argparse.ArgumentParser(description="从 git 回填 distilled_with（推断值，会标注来源）")
    ap.add_argument("--registry-root", type=pathlib.Path, default=REGISTRY_ROOT)
    ap.add_argument("--apply", action="store_true", help="真的写盘；不给就是 dry-run")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = args.registry_root.resolve()
    if not root.is_dir():
        print(f"用法错误：{root} 不是目录", file=sys.stderr)
        return 3

    result = run(root, args.apply)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("error"):
            print(f"✗ {result['error']}", file=sys.stderr)
            return 1
        mode = "已写盘" if result["applied"] else "dry-run（未写盘，加 --apply 才写）"
        print(f"{mode}：需更新 {result['changed']} 份，已是最新 {result['already_current']} 份")
        by_source: dict[tuple[str, str], int] = {}
        for item in result["details"]:
            key = (item["distilled_with"], item["source"])
            by_source[key] = by_source.get(key, 0) + 1
        for (version, source), count in sorted(by_source.items()):
            mark = "  ← 上界，非实测" if source.endswith("bulk-repackage") else ""
            print(f"  {version:<12} {source:<32} {count:>3} 人{mark}")
        for item in result["failed"]:
            print(f"  ✗ 无法归因：{item['record']} —— {item['why']}")
    return 1 if result.get("failed") or result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
