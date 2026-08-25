#!/usr/bin/env python3
"""Validate and normalize external tool results without granting verdict authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = "1.0"
ADAPTER_TYPES = {
    "static_analysis",
    "test_execution",
    "release_observation",
    "ai_evaluation",
    "supply_chain",
    "human_manual",
}
STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "WAIVED", "UNKNOWN"}
NON_PASS_SOURCE = {"warning", "warn", "skipped", "skip", "unstable", "partial", "incomplete", "unknown", "not_run"}
FORBIDDEN_AUTHORITY_KEYS = {"verdict", "release_decision", "approval", "accepted", "acceptance_status"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_no_duplicates(path: Path) -> Any:
    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid adapter JSON: {error}") from error


def safe_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ValueError(f"unsafe {label}: {value!r}")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe {label}: {value!r}")
    return path.as_posix()


def find_forbidden_keys(value: Any, prefix: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold() in FORBIDDEN_AUTHORITY_KEYS:
                findings.append(f"{prefix}.{key}")
            findings.extend(find_forbidden_keys(item, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(find_forbidden_keys(item, f"{prefix}[{index}]"))
    return findings


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def normalize(payload: Any, evidence_root: Optional[Path] = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("adapter result root must be an object")
    forbidden = find_forbidden_keys(payload)
    if forbidden:
        raise ValueError(f"adapter cannot assert acceptance/release authority: {forbidden[:5]}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")

    adapter_type = _require_string(payload.get("adapter_type"), "adapter_type")
    if adapter_type not in ADAPTER_TYPES:
        raise ValueError(f"unsupported adapter_type: {adapter_type}")
    adapter = payload.get("adapter")
    if not isinstance(adapter, dict):
        raise ValueError("adapter must be an object")
    adapter_name = _require_string(adapter.get("name"), "adapter.name")
    adapter_version = _require_string(adapter.get("version"), "adapter.version")
    source = _require_string(adapter.get("source"), "adapter.source")

    subject_identity = _require_string(payload.get("subject_identity"), "subject_identity")
    if len(subject_identity) < 8:
        raise ValueError("subject_identity is too weak")

    execution = payload.get("execution")
    if not isinstance(execution, dict):
        raise ValueError("execution must be an object")
    argv = execution.get("argv")
    if not isinstance(argv, list) or not argv or any(not isinstance(item, str) or not item for item in argv):
        raise ValueError("execution.argv must be a non-empty string array")
    if any("\x00" in item for item in argv):
        raise ValueError("execution.argv contains NUL")
    cwd = _require_string(execution.get("cwd"), "execution.cwd")
    exit_code = execution.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise ValueError("execution.exit_code must be an integer")
    timed_out = execution.get("timed_out")
    if not isinstance(timed_out, bool):
        raise ValueError("execution.timed_out must be boolean")

    mapping = payload.get("status_mapping")
    if not isinstance(mapping, dict):
        raise ValueError("status_mapping must be an object")
    source_status = _require_string(mapping.get("source_status"), "status_mapping.source_status")
    normalized_status = _require_string(mapping.get("normalized_status"), "status_mapping.normalized_status").upper()
    mapping_rule = _require_string(mapping.get("mapping_rule"), "status_mapping.mapping_rule")
    if normalized_status not in STATUSES:
        raise ValueError(f"unsupported normalized status: {normalized_status}")
    if source_status.casefold() in NON_PASS_SOURCE and normalized_status == "PASS":
        raise ValueError(f"ambiguous source status cannot map to PASS: {source_status}")
    if timed_out and normalized_status == "PASS":
        raise ValueError("timed-out execution cannot map to PASS")

    raw_evidence = payload.get("raw_evidence")
    if not isinstance(raw_evidence, list):
        raise ValueError("raw_evidence must be an array")
    evidence: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    evidence_root_resolved = evidence_root.resolve(strict=True) if evidence_root is not None else None
    for index, item in enumerate(raw_evidence):
        if not isinstance(item, dict):
            raise ValueError(f"raw_evidence[{index}] must be an object")
        rel = safe_relative_path(item.get("path"), f"raw_evidence[{index}].path")
        if rel.casefold() in {path.casefold() for path in seen_paths}:
            raise ValueError(f"duplicate/case-colliding evidence path: {rel}")
        seen_paths.add(rel)
        digest = item.get("sha256")
        size = item.get("size")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError(f"raw_evidence[{index}].sha256 must be lowercase SHA-256")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError(f"raw_evidence[{index}].size must be a non-negative integer")
        if evidence_root_resolved is not None:
            unresolved = evidence_root_resolved
            for part in Path(rel).parts:
                unresolved = unresolved / part
                if unresolved.is_symlink():
                    raise ValueError(f"evidence is missing, non-regular, or symlinked: {rel}")
            candidate = unresolved.resolve(strict=True)
            try:
                candidate.relative_to(evidence_root_resolved)
            except ValueError as error:
                raise ValueError(f"evidence path escapes evidence root: {rel}") from error
            if not candidate.is_file():
                raise ValueError(f"evidence is missing, non-regular, or symlinked: {rel}")
            if candidate.stat().st_size != size or sha256_file(candidate) != digest:
                raise ValueError(f"evidence size/hash mismatch: {rel}")
        evidence.append({"path": rel, "sha256": digest, "size": size, "media_type": item.get("media_type", "application/octet-stream")})

    if normalized_status == "PASS" and not evidence:
        raise ValueError("PASS requires hashed raw evidence")

    claims_raw = payload.get("claims")
    if not isinstance(claims_raw, list) or not claims_raw:
        raise ValueError("claims must be a non-empty array")
    claims: list[dict[str, Any]] = []
    claim_statuses: list[str] = []
    evidence_paths = {item["path"] for item in evidence}
    seen_ids: set[str] = set()
    for index, item in enumerate(claims_raw):
        if not isinstance(item, dict):
            raise ValueError(f"claims[{index}] must be an object")
        claim_id = _require_string(item.get("claim_id"), f"claims[{index}].claim_id")
        if claim_id in seen_ids:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        seen_ids.add(claim_id)
        status = _require_string(item.get("status"), f"claims[{index}].status").upper()
        if status not in STATUSES:
            raise ValueError(f"claims[{index}] unsupported status: {status}")
        oracle = _require_string(item.get("oracle"), f"claims[{index}].oracle")
        refs = item.get("evidence_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            raise ValueError(f"claims[{index}].evidence_refs must be a string array")
        if any(ref not in evidence_paths for ref in refs):
            raise ValueError(f"claims[{index}] references unknown evidence")
        if status == "PASS" and not refs:
            raise ValueError(f"claims[{index}] PASS requires evidence_refs")
        claim_statuses.append(status)
        claims.append({"claim_id": claim_id, "status": status, "oracle": oracle, "evidence_refs": refs, "notes": item.get("notes", "")})

    if normalized_status == "PASS" and any(status != "PASS" for status in claim_statuses):
        raise ValueError("top-level PASS cannot hide non-PASS claim status")

    limitations = payload.get("limitations", [])
    if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
        raise ValueError("limitations must be a string array")

    return {
        "schema_version": SCHEMA_VERSION,
        "normalized_by": "verifier",
        "decision_authority": "none",
        "verdict_eligible": False,
        "adapter_type": adapter_type,
        "adapter": {"name": adapter_name, "version": adapter_version, "source": source},
        "subject_identity": subject_identity,
        "execution": {"argv": argv, "cwd": cwd, "exit_code": exit_code, "timed_out": timed_out},
        "status_mapping": {"source_status": source_status, "normalized_status": normalized_status, "mapping_rule": mapping_rule},
        "normalized_status": normalized_status,
        "claims": claims,
        "evidence": evidence,
        "limitations": limitations,
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = normalize(load_json_no_duplicates(args.input), args.evidence_root)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        response = {"ok": True, "normalized": result, "output": str(args.output) if args.output else None}
    except (OSError, ValueError) as error:
        response = {"ok": False, "error": str(error)}
    if args.json or not response["ok"]:
        print(json.dumps(response, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stdout if response["ok"] else sys.stderr)
    else:
        print(f"ADAPTER RESULT VALID: {response['normalized']['adapter']['name']} status={response['normalized']['normalized_status']}")
    return 0 if response["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
