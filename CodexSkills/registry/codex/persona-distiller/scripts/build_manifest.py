#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, atomic_write_text, sha256_file

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "_build",
    "build",
    "dist",
    "workspaces",
}


_VER = (pathlib.Path(__file__).resolve().parent.parent / 'VERSION')\
       .read_text(encoding='utf-8').strip()


# ★ 不进 `files` 列表的两个，各有各的理由，**都不是「被排除在校验之外」**：
#   PACKAGE_MANIFEST.json —— 它就是这份列表本身；但下面第 74 行**会把它加回
#                            checksum_paths**，所以它是被校验的。
#   checksums.sha256      —— 不能对自己算校验和。这一个才是真正**不被校验**的。
EXCLUDED_FROM_FILES = {
    "PACKAGE_MANIFEST.json",
    "checksums.sha256",
}
# ★★ 真正不被校验的只有这一个。声明必须**从这里派生**，不许再手写。
#   2026-08-15 之前：`registry.yaml` 也在上面那个集合里被排掉，
#   而第 69 行硬写 `"excluded_from_release_checksums": []` ——
#   **代码排除了一个文件，它自己生成的声明说「什么都没排除」**，
#   同一个文件里自相矛盾。而 registry.yaml 是在册的版本契约文件
#   （134 次提交，`identity.version` 由 bump_version.py 写、
#   `check_contract_drift.py` 专门校验它那个字段），
#   且 bump_version **先于** build_manifest 跑 —— 算校验和时它早已定稿，
#   **排除它没有任何顺序上的理由**。现已纳入校验。
#   [[the-comment-states-the-rule-the-code-narrows-it]]
NOT_CHECKSUMMED = sorted(EXCLUDED_FROM_FILES - {"PACKAGE_MANIFEST.json"})


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if path.suffix in {".pyc", ".pyo", ".zip"}:
        return False
    if relative.as_posix() in EXCLUDED_FROM_FILES:
        return False
    return True


def main() -> int:
    manifest_path = ROOT / "PACKAGE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = sorted(path for path in ROOT.rglob("*") if path.is_file() and included(path))
    records = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in files
    ]
    manifest["files"] = records

    # ★★ **覆盖率现算并印出来。** 2026-08-17 把本工具搬去团队 skill 时，
    #   上游那句 `path.suffix in {".pyc",".pyo",".zip"}` 在那边**恰好排掉了产物本体**
    #   （那里 zip 就是运行时载荷，108 个），校验面 286/396 而清单照报「已校验」。
    #   我是**手工比对才发现的** —— 那说明它没有守卫。
    #   ⇒ 每次生成都印「收录 / 实况 / 未收录都是谁」，**未收录项必须逐条看得见**。
    #   [[a-gates-scan-set-is-smaller-than-reality]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    on_disk = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file())
    listed = {r["path"] for r in records}
    missing = [x for x in on_disk if x not in listed]
    print("清单覆盖：**%d / %d**｜未收录 %d 件%s"
          % (len(listed), len(on_disk), len(missing),
             ("：" + "、".join(missing[:6]) + ("…" if len(missing) > 6 else "")) if missing else ""))
    if missing:
        from collections import Counter
        by_suffix = Counter(pathlib.Path(m).suffix or "(无后缀)" for m in missing)
        print("  未收录按后缀：%s" % "、".join("%s×%d" % kv for kv in by_suffix.most_common()))
    # ★ 版本必须由**同一个真源**盖两个字段。
    #   原来只盖 distribution.kind，`version` 字段谁也不改——于是它从 v0.0.0.5 起
    #   一路冻在原地，同一个文件里两个版本号自相矛盾了 9 个版本没人发现。
    #   「生成器只覆盖它记得的那个字段」是漂移的常见来源。
    manifest["version"] = _VER
    manifest["distribution"] = {
        "kind": f"repository-customized-{_VER}",
        "lineage_base_archive_sha256": "e891912d98d14afb7677ac935a19be329d97d206f4ae74a644892f46b17f6748",
        "canonical_registry": "../persona-distiller-group",
    }
    manifest["mutable_paths"] = {
        # ★ 从 NOT_CHECKSUMMED 派生，**不许手写**。原来硬写 `[]`，
        #   而 `included()` 实际排掉了 registry.yaml —— 声明与代码在同一文件里打架。
        "excluded_from_release_checksums": list(NOT_CHECKSUMMED),
        "registry_is_external": "../persona-distiller-group",
        "validation": "python3 scripts/validate_persona_registry.py",
    }
    atomic_write_json(manifest_path, manifest)
    checksum_paths = files + [manifest_path]
    lines = "".join(
        f"{sha256_file(path)}  {path.relative_to(ROOT).as_posix()}\n"
        for path in sorted(checksum_paths)
    )
    atomic_write_text(ROOT / "checksums.sha256", lines)
    print(
        json.dumps(
            {
                "package_manifest_files": len(records),
                "checksum_files": len(checksum_paths),
                "canonical_registry": "../persona-distiller-group",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
