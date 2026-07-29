from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any, Dict, List, Optional

from .io import deterministic_zip, ensure_external, sha256_file, sha256_tree, write_json

DEFAULT_EVIDENCE_PATHS = [
    "SKILL.md",
    "README.md",
    "VERSION",
    "metadata/release.json",
    "constitution/genesis-lock.json",
    "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md",
    "delivery/BASELINE_CHANGE_DECISION.md",
    "delivery/MARKET_LEADERSHIP_ANALYSIS.md",
    "delivery/SELF_ITERATION_REPORT.md",
    "delivery/MECHANISM_ADOPTION_LEDGER.md",
    "delivery/RELEASE_NOTES.md",
    "MANIFEST.sha256",
]


def _binding(root: Path, relative: str) -> Optional[Dict[str, Any]]:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        return None
    return {"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def export_verifier_packet(
    subject: Path,
    output: Path,
    valid_as_of: str,
    acceptance_contract: Optional[Path] = None,
) -> Dict[str, Any]:
    subject = subject.resolve()
    output = output.resolve()
    if not subject.is_dir():
        raise ValueError("verifier subject must be a directory")
    ensure_external(output, [subject], "verifier packet output")
    if not valid_as_of or len(valid_as_of) != 10:
        raise ValueError("valid_as_of must be YYYY-MM-DD")

    evidence = [item for item in (_binding(subject, rel) for rel in DEFAULT_EVIDENCE_PATHS) if item]
    if len(evidence) < 6:
        raise ValueError("subject lacks minimum verifier evidence set")
    subject_hash = sha256_tree(subject, exclude={"MANIFEST.sha256"})
    contract_binding = None
    contract_value: Optional[Dict[str, Any]] = None
    if acceptance_contract:
        if not acceptance_contract.is_file() or acceptance_contract.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("acceptance contract missing or exceeds 2 MiB")
        value = json.loads(acceptance_contract.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("acceptance contract must be a JSON object")
        contract_value = value
        contract_binding = {
            "path": str(acceptance_contract.resolve()),
            "sha256": sha256_file(acceptance_contract),
            "bytes": acceptance_contract.stat().st_size,
        }

    request = {
        "schema_version": "1.0",
        "request_type": "independent-read-only-skill-acceptance",
        "valid_as_of": valid_as_of,
        "subject": {
            "name": subject.name,
            "root_tree_sha256_excluding_manifest": subject_hash,
            "version": (subject / "VERSION").read_text(encoding="utf-8").strip() if (subject / "VERSION").is_file() else None,
            "genesis_sha256": "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086",
        },
        "acceptance_items": [
            {"id": "A01", "critical": True, "requirement": "Locked Genesis remains byte-identical and externally anchored."},
            {"id": "A02", "critical": True, "requirement": "All bundled regression tests pass from the packaged artifact."},
            {"id": "A03", "critical": True, "requirement": "Peer taxonomy excludes engineering analogies from the market-peer minimum."},
            {"id": "A04", "critical": True, "requirement": "Utility guard reverts protected-task or hard-metric regressions."},
            {"id": "A05", "critical": True, "requirement": "Packaging, install, committed-state verification and rollback are executable and fail closed."},
            {"id": "A06", "critical": True, "requirement": "No local role simulation is represented as independent 2x6+1 review."},
            {"id": "A07", "critical": False, "requirement": "Operator dashboard is static, escaped, dependency-free and status-faithful."},
            {"id": "A08", "critical": False, "requirement": "Documentation separates engineering installability, outcome evidence and formal promotion."},
        ],
        "verification_commands": [
            ["python3", "scripts/wbi.py", "verify-self", "--strict", "--expected-genesis-hash", "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"],
            ["python3", "scripts/wbi.py", "self-test"],
            ["python3", "scripts/wbi.py", "release-smoke", "--expected-genesis-hash", "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"],
        ],
        "evidence_index": evidence,
        "acceptance_contract_binding": contract_binding,
        "verdict_policy": {
            "critical_items_require_independent_positive_verdict": True,
            "builder_self_attestation_is_insufficient": True,
            "missing_or_ambiguous_evidence": "BLOCK",
            "single_aggregate_score_can_override_critical_failure": False,
        },
        "expected_output": {
            "one_acceptance_review_zip": True,
            "exact_subject_hash_required": subject_hash,
            "verdicts": ["PASS", "FAIL", "BLOCKED"],
        },
    }

    with tempfile.TemporaryDirectory(prefix="teleiosis-verifier-export-") as td:
        packet = Path(td) / "teleiosis-verifier-packet"
        packet.mkdir()
        write_json(packet / "verification-request.json", request)
        write_json(packet / "evidence-index.json", {"schema_version": "1.0", "subject_hash": subject_hash, "files": evidence})
        if contract_value is not None:
            write_json(packet / "acceptance-contract.json", contract_value)
        (packet / "README.md").write_text(
            "# Teleiosis independent verifier packet\n\n"
            "This packet requests a read-only acceptance review. It is not a verdict, approval, or external attestation.\n\n"
            "The verifier must resolve the subject by the exact tree hash in `verification-request.json`, execute the listed commands in an isolated copy, and fail closed on missing evidence.\n",
            encoding="utf-8",
        )
        packaged = deterministic_zip(packet, output)
    return {
        "status": "PASS",
        "review_status": "PACKET_READY_REVIEW_PENDING",
        "subject_tree_sha256": subject_hash,
        "evidence_count": len(evidence),
        "packet": packaged,
        "formal_promotion_granted": False,
    }
