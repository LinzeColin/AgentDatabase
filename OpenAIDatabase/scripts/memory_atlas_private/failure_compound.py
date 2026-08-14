from __future__ import annotations

import json
import re
import sqlite3
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .hashing import stable_id


class FailureCompoundError(RuntimeError):
    pass


def normalize_signature_text(value: str) -> str:
    normalized = value.lower().strip()
    normalized = re.sub(r"0x[0-9a-f]+", "<hex>", normalized)
    normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}[t ][0-9:.+-z]+\b", "<time>", normalized)
    normalized = re.sub(r"\b\d+\b", "<n>", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized[:2000]


def failure_signature(component: str, category: str, error_code: str, title: str) -> str:
    return stable_id(
        normalize_signature_text(component),
        normalize_signature_text(category),
        normalize_signature_text(error_code),
        normalize_signature_text(title),
        prefix="fsig",
    )


@dataclass(frozen=True)
class IncidentResult:
    incident_id: str
    signature: str
    recurrence_count: int
    created: bool


class FailureCompoundStore:
    def __init__(self, sqlite_path: Path):
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = sqlite_path
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                PRAGMA foreign_keys=ON;
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    signature TEXT NOT NULL UNIQUE,
                    component TEXT NOT NULL,
                    category TEXT NOT NULL,
                    error_code TEXT NOT NULL DEFAULT '',
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    root_cause TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    recurrence_count INTEGER NOT NULL DEFAULT 1,
                    regression_asset_id TEXT,
                    fixed_by TEXT NOT NULL DEFAULT '',
                    closure_evidence_json TEXT NOT NULL DEFAULT '[]'
                );
                CREATE TABLE IF NOT EXISTS occurrences (
                    occurrence_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
                    occurred_at TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    details_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS regression_assets (
                    asset_id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL UNIQUE REFERENCES incidents(incident_id),
                    fixture_path TEXT NOT NULL,
                    oracle TEXT NOT NULL,
                    test_path TEXT NOT NULL,
                    red_evidence_ref TEXT NOT NULL,
                    green_evidence_ref TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_result TEXT NOT NULL DEFAULT 'NOT_RUN',
                    last_run_at TEXT,
                    blocked_recurrences INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS fault_injections (
                    injection_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL REFERENCES regression_assets(asset_id),
                    injected_at TEXT NOT NULL,
                    expected TEXT NOT NULL,
                    observed TEXT NOT NULL,
                    result TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL
                );
                """
            )
            incident_columns = {
                str(row[1]) for row in db.execute("PRAGMA table_info(incidents)")
            }
            if "error_code" not in incident_columns:
                db.execute(
                    "ALTER TABLE incidents ADD COLUMN error_code TEXT NOT NULL DEFAULT ''"
                )
            # AC-015 requires a closed incident to carry a rollback reference
            # alongside its evidence, fixture, oracle, red/green proof and
            # monitoring. Added additively with an empty default so incidents
            # closed before this column existed stay readable; the projection
            # reports how many still lack one instead of hiding the gap.
            if "rollback_ref" not in incident_columns:
                db.execute(
                    "ALTER TABLE incidents ADD COLUMN rollback_ref TEXT NOT NULL DEFAULT ''"
                )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def record_failure(
        self,
        *,
        component: str,
        category: str,
        severity: str,
        error_code: str,
        title: str,
        occurred_at: str,
        evidence_ref: str,
        environment: str,
        details: dict[str, Any] | None = None,
    ) -> IncidentResult:
        signature = failure_signature(component, category, error_code, title)
        incident_id = stable_id(signature, prefix="inc")
        occurrence_id = stable_id(signature, occurred_at, evidence_ref, prefix="occ")
        created = False
        with self._connect() as db:
            existing = db.execute("SELECT * FROM incidents WHERE signature=?", (signature,)).fetchone()
            if existing is None:
                created = True
                db.execute(
                    """
                    INSERT INTO incidents
                    (incident_id, signature, component, category, error_code, severity, title, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        signature,
                        component,
                        category,
                        error_code,
                        severity,
                        title,
                        occurred_at,
                        occurred_at,
                    ),
                )
            else:
                incident_id = str(existing["incident_id"])
                db.execute(
                    "UPDATE incidents SET error_code=CASE WHEN error_code='' THEN ? ELSE error_code END WHERE incident_id=?",
                    (error_code, incident_id),
                )
                if db.execute("SELECT 1 FROM occurrences WHERE occurrence_id=?", (occurrence_id,)).fetchone() is None:
                    db.execute(
                        "UPDATE incidents SET last_seen=?, recurrence_count=recurrence_count+1, status='REOPENED' WHERE incident_id=?",
                        (occurred_at, incident_id),
                    )
            db.execute(
                """
                INSERT OR IGNORE INTO occurrences
                (occurrence_id, incident_id, occurred_at, evidence_ref, environment, details_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    occurrence_id,
                    incident_id,
                    occurred_at,
                    evidence_ref,
                    environment,
                    json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
                ),
            )
            db.commit()
            count = int(db.execute(
                "SELECT recurrence_count FROM incidents WHERE incident_id=?", (incident_id,)
            ).fetchone()[0])
        return IncidentResult(incident_id=incident_id, signature=signature, recurrence_count=count, created=created)

    def promote_regression_asset(
        self,
        *,
        incident_id: str,
        fixture_path: str,
        oracle: str,
        test_path: str,
        red_evidence_ref: str,
        green_evidence_ref: str,
        fixed_by: str,
        root_cause: str = "",
        rollback_ref: str = "",
    ) -> str:
        required = [fixture_path, oracle, test_path, red_evidence_ref, green_evidence_ref, fixed_by]
        if any(not value.strip() for value in required):
            raise FailureCompoundError("回归资产必须同时绑定 Fixture、Oracle、测试、红灯、绿灯和修复身份")
        asset_id = stable_id(incident_id, prefix="reg")
        with self._connect() as db:
            if db.execute("SELECT 1 FROM incidents WHERE incident_id=?", (incident_id,)).fetchone() is None:
                raise FailureCompoundError(f"Incident 不存在：{incident_id}")
            db.execute(
                """
                INSERT INTO regression_assets
                (asset_id, incident_id, fixture_path, oracle, test_path, red_evidence_ref, green_evidence_ref, status, last_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', 'PASS')
                ON CONFLICT(incident_id) DO UPDATE SET
                    fixture_path=excluded.fixture_path,
                    oracle=excluded.oracle,
                    test_path=excluded.test_path,
                    red_evidence_ref=excluded.red_evidence_ref,
                    green_evidence_ref=excluded.green_evidence_ref,
                    status='ACTIVE',
                    last_result='PASS'
                """,
                (asset_id, incident_id, fixture_path, oracle, test_path, red_evidence_ref, green_evidence_ref),
            )
            db.execute(
                """
                UPDATE incidents SET regression_asset_id=?, fixed_by=?, status='CLOSED',
                    root_cause=CASE WHEN ?='' THEN root_cause ELSE ? END,
                    rollback_ref=CASE WHEN ?='' THEN rollback_ref ELSE ? END,
                    closure_evidence_json=? WHERE incident_id=?
                """,
                (
                    asset_id,
                    fixed_by,
                    root_cause,
                    root_cause,
                    rollback_ref,
                    rollback_ref,
                    json.dumps([red_evidence_ref, green_evidence_ref]),
                    incident_id,
                ),
            )
            db.commit()
        return asset_id

    def record_fault_injection(
        self,
        *,
        asset_id: str,
        injected_at: str,
        expected: str,
        observed: str,
        evidence_ref: str,
    ) -> str:
        result = "PASS" if expected == observed else "FAIL"
        injection_id = stable_id(asset_id, injected_at, evidence_ref, prefix="inject")
        with self._connect() as db:
            asset = db.execute("SELECT 1 FROM regression_assets WHERE asset_id=?", (asset_id,)).fetchone()
            if asset is None:
                raise FailureCompoundError(f"回归资产不存在：{asset_id}")
            db.execute(
                """
                INSERT OR REPLACE INTO fault_injections
                (injection_id, asset_id, injected_at, expected, observed, result, evidence_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (injection_id, asset_id, injected_at, expected, observed, result, evidence_ref),
            )
            db.execute(
                """
                UPDATE regression_assets
                SET last_result=?, last_run_at=?, blocked_recurrences=(
                    SELECT COUNT(*) FROM fault_injections
                    WHERE fault_injections.asset_id=? AND result='PASS'
                )
                WHERE asset_id=?
                """,
                (result, injected_at, asset_id, asset_id),
            )
            db.commit()
        return result

    def import_asset_registry(self, registry_path: Path) -> dict[str, Any]:
        """Import evidence-bound regression assets from one protected registry.

        The registry contains environment execution receipts, so it is deliberately
        kept outside Git. Re-importing the same file is idempotent at occurrence,
        asset and fault-injection level.
        """
        expanded = registry_path.expanduser()
        if expanded.is_symlink():
            raise FailureCompoundError("Failure Compound 资产注册表不能是符号链接")
        resolved = expanded.resolve(strict=True)
        if not resolved.is_file():
            raise FailureCompoundError("Failure Compound 资产注册表必须是普通文件")
        if stat.S_IMODE(resolved.stat().st_mode) != 0o600:
            raise FailureCompoundError("Failure Compound 资产注册表权限必须精确为 0600")
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8", errors="strict"))
        except (OSError, json.JSONDecodeError) as exc:
            raise FailureCompoundError(f"Failure Compound 资产注册表不可解析：{exc}") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != "memory_atlas.failure_asset_registry.v1":
            raise FailureCompoundError("Failure Compound 资产注册表 schema_version 不匹配")
        entries = payload.get("assets")
        if not isinstance(entries, list) or not entries:
            raise FailureCompoundError("Failure Compound 资产注册表必须包含非空 assets")

        required_text = (
            "id",
            "component",
            "category",
            "severity",
            "error_code",
            "title",
            "root_cause",
            "occurred_at",
            "evidence_ref",
            "environment",
            "fixture_path",
            "oracle",
            "test_path",
            "red_evidence_ref",
            "green_evidence_ref",
            "fixed_by",
        )
        seen_ids: set[str] = set()
        normalized_entries: list[tuple[dict[str, str], dict[str, Any], dict[str, str]]] = []
        for index, raw in enumerate(entries):
            if not isinstance(raw, dict):
                raise FailureCompoundError(f"assets[{index}] 必须是 JSON object")
            values: dict[str, str] = {}
            for key in required_text:
                value = raw.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise FailureCompoundError(f"assets[{index}].{key} 必须是非空字符串")
                values[key] = value.strip()
            if values["id"] in seen_ids:
                raise FailureCompoundError(f"Failure Compound 资产 id 重复：{values['id']}")
            seen_ids.add(values["id"])
            if values["severity"] not in {"P0", "P1", "P2"}:
                raise FailureCompoundError(f"assets[{index}].severity 不受支持")
            details = raw.get("details", {})
            if not isinstance(details, dict):
                raise FailureCompoundError(f"assets[{index}].details 必须是 JSON object")
            injection = raw.get("fault_injection")
            if not isinstance(injection, dict):
                raise FailureCompoundError(f"assets[{index}].fault_injection 必须存在")
            injection_values: dict[str, str] = {}
            for key in ("injected_at", "expected", "observed", "evidence_ref"):
                value = injection.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise FailureCompoundError(
                        f"assets[{index}].fault_injection.{key} 必须是非空字符串"
                    )
                injection_values[key] = value.strip()
            if injection_values["expected"] != injection_values["observed"]:
                raise FailureCompoundError(
                    f"Failure Compound 资产绿灯 Oracle 未通过：{values['id']}"
                )
            normalized_entries.append((values, details, injection_values))

        imported: list[dict[str, Any]] = []
        created_count = 0
        for values, details, injection_values in normalized_entries:
            incident = self.record_failure(
                component=values["component"],
                category=values["category"],
                severity=values["severity"],
                error_code=values["error_code"],
                title=values["title"],
                occurred_at=values["occurred_at"],
                evidence_ref=values["evidence_ref"],
                environment=values["environment"],
                details={"registry_asset_id": values["id"], **details},
            )
            created_count += int(incident.created)
            asset_id = self.promote_regression_asset(
                incident_id=incident.incident_id,
                fixture_path=values["fixture_path"],
                oracle=values["oracle"],
                test_path=values["test_path"],
                red_evidence_ref=values["red_evidence_ref"],
                green_evidence_ref=values["green_evidence_ref"],
                fixed_by=values["fixed_by"],
                root_cause=values["root_cause"],
                # Optional so registries written before AC-015's rollback element
                # keep ingesting; the snapshot counts what is still missing.
                rollback_ref=str(raw.get("rollback_ref") or "").strip(),
            )
            result = self.record_fault_injection(
                asset_id=asset_id,
                injected_at=injection_values["injected_at"],
                expected=injection_values["expected"],
                observed=injection_values["observed"],
                evidence_ref=injection_values["evidence_ref"],
            )
            if result != "PASS":  # all entries were validated before the first write
                raise AssertionError("validated fault injection changed result")
            imported.append({
                "registry_asset_id": values["id"],
                "incident_id": incident.incident_id,
                "regression_asset_id": asset_id,
                "created": incident.created,
                "fault_injection": result,
            })
        snapshot = self.export_snapshot(str(payload.get("generated_at", "registry-import")))
        return {
            "schema_version": "memory_atlas.failure_asset_import.v1",
            "state": "PASS",
            "registry": str(resolved),
            "assets_imported": len(imported),
            "incidents_created": created_count,
            "incident_count": snapshot["metrics"]["incident_count"],
            "active_regression_assets": snapshot["metrics"]["active_regression_assets"],
            "blocked_recurrences": snapshot["metrics"]["blocked_recurrences"],
            "results": imported,
        }

    def export_snapshot(self, generated_at: str) -> dict[str, Any]:
        with self._connect() as db:
            incidents = [dict(row) for row in db.execute("SELECT * FROM incidents ORDER BY last_seen DESC")]
            assets = [dict(row) for row in db.execute("SELECT * FROM regression_assets ORDER BY asset_id")]
            injections = [dict(row) for row in db.execute("SELECT * FROM fault_injections ORDER BY injected_at DESC")]
        active_assets = [row for row in assets if row["status"] == "ACTIVE"]
        passing_assets = [row for row in active_assets if row["last_result"] == "PASS"]
        total_recurrences = sum(max(0, int(row["recurrence_count"]) - 1) for row in incidents)
        blocked = sum(int(row["blocked_recurrences"]) for row in active_assets)
        asset_coverage = len(active_assets) / len(incidents) if incidents else 0.0
        pass_rate = len(passing_assets) / len(active_assets) if active_assets else 0.0
        nonrecurrence = blocked / (blocked + total_recurrences) if (blocked + total_recurrences) else 0.0
        score = round(100 * (0.4 * asset_coverage + 0.3 * pass_rate + 0.3 * nonrecurrence))
        # AC-015 counts a rollback reference among the elements a closed or
        # blocked incident must carry. Surface the shortfall as a number rather
        # than letting an absent field read as satisfied.
        closed = [row for row in incidents if str(row.get("status", "")).upper() in {"CLOSED", "BLOCKED"}]
        with_rollback = [row for row in closed if str(row.get("rollback_ref") or "").strip()]
        return {
            "schema_version": "memory_atlas.failure_compound.v1",
            "generated_at": generated_at,
            "compound_score": score,
            "metrics": {
                "incident_count": len(incidents),
                "active_regression_assets": len(active_assets),
                "passing_regression_assets": len(passing_assets),
                "historical_recurrences": total_recurrences,
                "blocked_recurrences": blocked,
                "asset_coverage": round(asset_coverage, 4),
                "last_pass_rate": round(pass_rate, 4),
                "nonrecurrence_ratio": round(nonrecurrence, 4),
                "closed_incident_count": len(closed),
                "closed_incidents_with_rollback": len(with_rollback),
                "closed_incidents_missing_rollback": len(closed) - len(with_rollback),
            },
            "incidents": incidents,
            "regression_assets": assets,
            "fault_injections": injections,
            "formula": "100 × (0.40×asset_coverage + 0.30×last_pass_rate + 0.30×nonrecurrence_ratio)",
        }
