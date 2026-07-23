#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

GROUP_SCRIPTS = Path(__file__).resolve().parents[2] / "persona-distiller-group" / "scripts"
if str(GROUP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(GROUP_SCRIPTS))

from registry_core import (  # noqa: E402
    BUILDER_VERSION,
    DELIVERY_CONTRACT,
    inspect_delivery_zip,
    inspect_runtime_zip,
    sha256_file,
)

TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates" / "delivery"
FIXED_ZIP_TIME = (2026, 7, 23, 0, 0, 0)
AUDIT_FILES = (
    "verification.json",
    "provenance.json",
    "source-coverage.json",
    "evaluation-summary.json",
    "review-record.json",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def deterministic_zip(staging: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            relative = path.relative_to(staging.parent).as_posix()
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.suffix in {".py", ".sh"} else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def human_readme(runtime: dict[str, Any], delivery_status: str) -> str:
    return f"""# {runtime['canonical_name']} — 人物蒸馏完整交付

这是单一、完整、可校验的交付 ZIP。它包含人物运行时 Skill、安装器、登记卡、团队卡、来源覆盖、评测、验证、provenance 和交接信息。

- 人物产品版本：`{runtime['product_version']}`
- 模型快照：`{runtime['model_version']}`
- 唯一身份：`{runtime['category']}`
- 运行时 SHA-256：`{runtime['sha256']}`
- 交付状态：`{delivery_status}`

安装到默认 Codex Skills 目录：

```bash
python3 install.py
```

覆盖同名旧版本：

```bash
python3 install.py --force
```

`0.0.0.N` 只标识已登记人物产品；人物 Skill 的单次调用不编号。人物模型不是本人、授权、背书或实时观点。
"""


def human_handoff(runtime: dict[str, Any], audit: dict[str, dict[str, Any]]) -> str:
    statuses = "\n".join(
        f"- `{name}`: `{audit[name]['status']}`"
        for name in AUDIT_FILES
    )
    return f"""# Handoff

## 安装与调用

运行 `python3 install.py` 安装 `{runtime['subject_slug']}`。安装后直接调用人物 Skill 并给出任务；不需要选择身份、编号或权重。

## 不可变边界

- 产品版本：`{runtime['product_version']}`
- 内层运行时 SHA-256：`{runtime['sha256']}`
- 运行时调用版本：无
- 唯一登记身份：`{runtime['category']}`

## 审计可用性

{statuses}

`not-available-in-source-artifact` 表示历史来源包没有该证据，不表示已通过，也不得据此补造。
"""


def normalize_audit(audit: dict[str, dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    source = audit or {}
    result: dict[str, dict[str, Any]] = {}
    for name in AUDIT_FILES:
        value = source.get(name)
        if isinstance(value, dict) and isinstance(value.get("status"), str) and value["status"].strip():
            result[name] = value
        else:
            result[name] = {
                "schema_version": "1.0",
                "status": "not-available-in-source-artifact",
                "claims": [],
            }
    return result


def safe_report_name(relative: str) -> str:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe report path: {relative}")
    if path.parts[0] == "reports":
        path = PurePosixPath(*path.parts[1:])
    if not path.parts:
        raise ValueError("report path cannot be the reports directory itself")
    return path.as_posix()


def build_full_delivery(
    runtime_zip: Path,
    output: Path,
    *,
    team_card: dict[str, Any],
    audit: dict[str, dict[str, Any]] | None = None,
    reports: Iterable[tuple[Path, str]] = (),
    delivery_contract_status: str = "native-v0.0.0.5",
    created_at: str | None = None,
    provenance_mode: str = "native-build",
) -> dict[str, Any]:
    runtime_zip = runtime_zip.expanduser().resolve()
    output = output.expanduser().resolve()
    runtime = inspect_runtime_zip(runtime_zip)
    if delivery_contract_status not in {
        "native-v0.0.0.5",
        "legacy-normalized-v0.0.0.5",
    }:
        raise ValueError("unsupported delivery_contract_status")
    expected_team = {
        "schema_version": "1.0",
        "subject_uid": runtime["subject_uid"],
        "canonical_name": runtime["canonical_name"],
        "subject_slug": runtime["subject_slug"],
        "identity_family_id": runtime["identity_family_id"],
        "latest_product_version": runtime["product_version"],
    }
    for key, expected in expected_team.items():
        if team_card.get(key) != expected:
            raise ValueError(f"team card {key} must be {expected!r}")
    audit_payload = normalize_audit(audit)
    created_at = created_at or runtime["artifact_created_at"] or "2026-07-23T00:00:00Z"
    top_name = (
        f"{runtime['subject_slug']}-persona-distillation-delivery-v"
        f"{runtime['product_version']}"
    )
    runtime_name = (
        f"{runtime['subject_slug']}-persona-skill-v"
        f"{runtime['product_version']}.zip"
    )
    with tempfile.TemporaryDirectory(prefix="persona-full-delivery-") as temporary:
        staging = Path(temporary) / top_name
        (staging / "runtime").mkdir(parents=True)
        (staging / "audit").mkdir()
        shutil.copy2(runtime_zip, staging / "runtime" / runtime_name)
        for name in ("install.py", "install.sh", "install.ps1"):
            shutil.copy2(TEMPLATE_ROOT / name, staging / name)
        (staging / "README.md").write_text(
            human_readme(runtime, delivery_contract_status),
            encoding="utf-8",
        )
        (staging / "handoff.md").write_text(
            human_handoff(runtime, audit_payload),
            encoding="utf-8",
        )
        write_json(staging / "team-card.json", team_card)
        portable_registration = {
            "schema_version": "1.0",
            "subject_uid": runtime["subject_uid"],
            "canonical_name": runtime["canonical_name"],
            "subject_slug": runtime["subject_slug"],
            "subject_origin": runtime["subject_origin"],
            "registration_category": runtime["category"],
            "identity_family_id": runtime["identity_family_id"],
            "identity_mode": runtime["identity_mode"],
            "product_version": runtime["product_version"],
            "model_version": runtime["model_version"],
            "runtime_artifact": f"runtime/{runtime_name}",
            "runtime_sha256": runtime["sha256"],
            "runtime_size_bytes": runtime["size_bytes"],
            "outer_sha256_trust_anchor": "canonical-registry",
            "delivery_contract_status": delivery_contract_status,
        }
        write_json(staging / "registration.json", portable_registration)
        for name, value in audit_payload.items():
            write_json(staging / "audit" / name, value)
        report_records = []
        for source, relative in reports:
            source = source.expanduser().resolve()
            if not source.is_file():
                raise ValueError(f"report does not exist: {source}")
            safe_relative = safe_report_name(relative)
            destination = staging / "reports" / safe_relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            report_records.append(
                {
                    "path": f"reports/{safe_relative}",
                    "sha256": sha256_file(destination),
                    "size_bytes": destination.stat().st_size,
                }
            )
        payload_paths = sorted(
            path
            for path in staging.rglob("*")
            if path.is_file()
            and path.relative_to(staging).as_posix()
            not in {"delivery-manifest.json", "delivery-checksums.sha256"}
        )
        payload_records = [
            {
                "path": path.relative_to(staging).as_posix(),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in payload_paths
        ]
        manifest = {
            "schema_version": "1.0",
            "artifact_kind": "persona-distillation-full-delivery",
            "delivery_contract": DELIVERY_CONTRACT,
            "delivery_contract_status": delivery_contract_status,
            "builder": "persona-distiller",
            "builder_version": BUILDER_VERSION,
            "created_at": created_at,
            "single_archive_only": True,
            "top_level_count": 1,
            "subject": {
                "uid": runtime["subject_uid"],
                "canonical_name": runtime["canonical_name"],
                "slug": runtime["subject_slug"],
                "origin": runtime["subject_origin"],
            },
            "identity": {
                "folder": runtime["category"],
                "family_id": runtime["identity_family_id"],
                "mode": runtime["identity_mode"],
            },
            "product_version": runtime["product_version"],
            "model_version": runtime["model_version"],
            "runtime": {
                "path": f"runtime/{runtime_name}",
                "sha256": runtime["sha256"],
                "size_bytes": runtime["size_bytes"],
                "builder_version": runtime["builder_version"],
            },
            "evidence_status": {
                name.removesuffix(".json"): value["status"]
                for name, value in audit_payload.items()
            },
            "provenance_mode": provenance_mode,
            "compatibility": {
                "default_install_root": "~/.codex/skills",
                "python": ">=3.10",
                "verified_hosts": ["codex"],
            },
            "privacy": {
                "raw_included": False,
                "holdout_bodies_included": False,
                "private_source_bodies_included": False,
                "runtime_history_reset": True,
                "credentials_included": False,
            },
            "reports": report_records,
            "files": payload_records,
        }
        write_json(staging / "delivery-manifest.json", manifest)
        checksum_paths = sorted(
            path
            for path in staging.rglob("*")
            if path.is_file()
            and path.relative_to(staging).as_posix() != "delivery-checksums.sha256"
        )
        checksums = "".join(
            f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}\n"
            for path in checksum_paths
        )
        (staging / "delivery-checksums.sha256").write_text(checksums, encoding="utf-8")
        deterministic_zip(staging, output)
    inspected = inspect_delivery_zip(output)
    return {
        "delivery": str(output),
        "outer_sha256": inspected["outer_sha256"],
        "runtime_sha256": inspected["runtime_sha256"],
        "product_version": inspected["product_version"],
        "subject_uid": inspected["subject_uid"],
        "category": inspected["category"],
        "single_archive_only": True,
        "sidecars": [],
        "delivery_contract_status": inspected["delivery_contract_status"],
    }
