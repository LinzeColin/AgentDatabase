from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any


class StatusProjectionError(ValueError):
    pass


def build_status_projection(private_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe, read-only operational projection.

    The projection intentionally excludes normalized event payloads, source paths,
    object keys, object hashes, incident titles/details, prompts and raw content.
    It is safe for the existing status collector to consume as a projection only;
    Private-Database and the verified GitHub private Releases remain the authorities.
    """
    if private_snapshot.get("schema_version") != "memory_atlas.private_analytics.v1":
        raise StatusProjectionError("私有快照 schema_version 不匹配")
    run = private_snapshot.get("run")
    behavior = private_snapshot.get("behavior_economics")
    failure = private_snapshot.get("failure_compound")
    if not isinstance(run, dict) or not isinstance(behavior, dict) or not isinstance(failure, dict):
        raise StatusProjectionError("私有快照缺少 run / behavior_economics / failure_compound")

    coverages = run.get("source_coverages") if isinstance(run.get("source_coverages"), list) else []
    coverage_counts: dict[str, int] = {}
    for row in coverages:
        if not isinstance(row, dict):
            continue
        state = str(row.get("state", "UNKNOWN"))
        coverage_counts[state] = coverage_counts.get(state, 0) + 1

    objects = run.get("objects") if isinstance(run.get("objects"), list) else []
    vor = behavior.get("verified_outcome_rate") if isinstance(behavior.get("verified_outcome_rate"), dict) else {}
    failure_metrics = failure.get("metrics") if isinstance(failure.get("metrics"), dict) else {}
    run_state = str(run.get("state", "UNKNOWN"))
    state = "PASS" if run_state in {"SUCCEEDED", "REBUILT_FROM_AUTHORITIES"} else run_state

    return {
        "schema_version": "memory_atlas.status_projection.v1",
        "generated_at": private_snapshot.get("generated_at"),
        "state": state,
        "run_id": run.get("run_id"),
        "source_completed_at": run.get("source_completed_at"),
        "source_coverage_counts": dict(sorted(coverage_counts.items())),
        "object_count": len(objects),
        "behavior_economics": {
            "event_count": int(behavior.get("event_count", 0) or 0),
            "verified_outcome_rate": vor.get("value"),
            "verified_outcome_rate_state": vor.get("state", "UNKNOWN"),
            "recommendation_count": len(behavior.get("recommendations", []))
            if isinstance(behavior.get("recommendations"), list) else 0,
        },
        "failure_compound": {
            "compound_score": int(failure.get("compound_score", 0) or 0),
            "incident_count": int(failure_metrics.get("incident_count", 0) or 0),
            "active_regression_assets": int(failure_metrics.get("active_regression_assets", 0) or 0),
            "historical_recurrences": int(failure_metrics.get("historical_recurrences", 0) or 0),
            "blocked_recurrences": int(failure_metrics.get("blocked_recurrences", 0) or 0),
        },
        "authority": {
            "object_bytes": "GitHub private Releases (encrypted source archive + canonical events)",
            "long_term_facts": "Private-Database",
            "runtime_journal": "OVH SQLite (rebuildable)",
            "this_document": "read_only_projection_not_authority",
        },
        "private_content_included": False,
    }


def publish_status_projection(target: Path, projection: dict[str, Any]) -> dict[str, Any]:
    """Register the public-safe projection in the existing status data plane."""
    if projection.get("schema_version") != "memory_atlas.status_projection.v1":
        raise StatusProjectionError("status 投影 schema_version 不匹配")
    if projection.get("private_content_included") is not False:
        raise StatusProjectionError("status 投影包含私有内容")
    authority = projection.get("authority")
    if not isinstance(authority, dict) or authority.get("this_document") != "read_only_projection_not_authority":
        raise StatusProjectionError("status 投影未声明只读非权威边界")
    if not target.is_absolute() or target.is_symlink():
        raise StatusProjectionError("status 投影目标必须是非符号链接绝对路径")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise StatusProjectionError("status 投影目标目录必须既有且不能是符号链接")
    payload = json.dumps(projection, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    temporary = target.with_suffix(target.suffix + ".partial")
    temporary.write_bytes(payload)
    os.chmod(temporary, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    temporary.replace(target)
    observed = target.read_bytes()
    if observed != payload:
        raise StatusProjectionError("status 投影登记后读回不一致")
    return {
        "schema_version": "memory_atlas.status_registration.v1",
        "state": "PASS",
        "target": str(target),
        "sha256": hashlib.sha256(observed).hexdigest(),
        "readback_verified": True,
        "mode": f"{stat.S_IMODE(target.stat().st_mode):04o}",
        "authority": "read_only_projection_not_authority",
    }
