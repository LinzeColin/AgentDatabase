from __future__ import annotations

from pathlib import Path
import os
import platform
import sys
import tempfile
from typing import Any, Dict, Optional

from .io import load_json, safe_extract_zip, sha256_file, sha256_tree, utc_now, write_json
from .package import package_skill
from .process import run_bounded
from .validation import detect_profile, validate_skill


def _git_value(root: Path, args: list) -> Optional[str]:
    """Read optional Git provenance through bounded, credential-free execution."""
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
    completed = run_bounded(
        ["git", "-C", str(root)] + [str(item) for item in args], cwd=root, env=env,
        timeout_seconds=10, max_output_bytes=64 * 1024,
    )
    value = completed["stdout"].strip()
    return value if completed["returncode"] == 0 and not completed["timed_out"] and value else None


def generate_release_receipt(
    skill_root: Path,
    archive: Path,
    output: Path,
    workspace: Optional[Path] = None,
    gate_result: Optional[Dict[str, Any]] = None,
    install_result: Optional[Dict[str, Any]] = None,
    expected_genesis_hash: str = "",
    expected_effective_genesis_hash: str = "",
) -> Dict[str, Any]:
    skill_root, archive, output = skill_root.resolve(), archive.resolve(), output.resolve()
    profile = detect_profile(skill_root, "auto")
    errors = []
    archive_validation: Dict[str, Any] = {"status": "FAIL"}
    if not archive.is_file():
        errors.append("archive missing")
    else:
        with tempfile.TemporaryDirectory(prefix="wbi-receipt-") as td:
            extract = Path(td) / "extract"
            try:
                safe_extract_zip(archive, extract)
                top = list(extract.iterdir())
                if len(top) != 1 or not top[0].is_dir():
                    raise ValueError("archive must contain one Skill root")
                archive_validation = validate_skill(
                    top[0], strict=True,
                    expected_genesis_hash=expected_genesis_hash if profile == "optimizer" else "",
                    expected_effective_genesis_hash=expected_effective_genesis_hash if profile == "optimizer" else "",
                    profile=profile,
                )
            except Exception as exc:
                errors.append(str(exc))
    with tempfile.TemporaryDirectory(prefix="wbi-repro-") as td:
        rebuilt = Path(td) / archive.name
        reproduction = package_skill(
            skill_root, rebuilt, expected_genesis_hash, profile=profile, verification_level="structural",
            expected_effective_genesis_hash=expected_effective_genesis_hash,
        )
        deterministic = reproduction.get("status") == "PASS" and archive.is_file() and sha256_file(rebuilt) == sha256_file(archive)

    if profile == "optimizer":
        release = load_json(skill_root / "metadata/release.json")
        genesis = load_json(skill_root / "constitution/genesis-lock.json")
        identity = {
            "slug": release.get("slug", release.get("skill_slug", skill_root.name)),
            "english_brand": release.get("english_brand"),
            "functional_name_en": release.get("functional_name_en", release.get("functional_english_name")),
            "display_name_zh": release.get("display_name_zh"),
            "version": release.get("version"), "release_revision": release.get("release_revision"),
            "valid_as_of": release.get("valid_as_of"),
        }
        effective = load_json(skill_root / "constitution/effective-genesis-lock.v0.0.0.2.json")
        genesis_value: Optional[Dict[str, Any]] = {
            "baseline_id": genesis["baseline_id"], "locked_sha256": genesis["locked_genesis"]["sha256"],
            "source_candidate_sha256": genesis["source_candidate"]["sha256"],
            "effective_baseline_id": effective.get("effective_baseline_id"),
            "effective_composite_sha256": effective.get("effective_composite_sha256"),
            "external_base_anchor_verified": expected_genesis_hash == genesis["locked_genesis"]["sha256"],
            "external_effective_anchor_verified": expected_effective_genesis_hash == effective.get("effective_composite_sha256"),
            "external_anchor_required": True,
        }
    else:
        identity = {"slug": skill_root.name, "version": (skill_root / "VERSION").read_text(encoding="utf-8").strip() if (skill_root / "VERSION").is_file() else "UNVERSIONED"}
        genesis_value = None

    archive_digest = sha256_file(archive) if archive.is_file() else None
    install_transaction = install_result.get("transaction", {}) if isinstance(install_result, dict) else {}
    install_archive_digest = None
    if isinstance(install_result, dict):
        install_archive_digest = install_result.get("archive_sha256") or (install_transaction.get("archive_sha256") if isinstance(install_transaction, dict) else None)
    committed_status = None
    if isinstance(install_result, dict):
        committed_status = install_result.get("observed_transaction_status") or (install_transaction.get("status") if isinstance(install_transaction, dict) else None)
    installed_verification = install_result.get("installed_verification") if isinstance(install_result, dict) else None
    installed = bool(
        isinstance(install_result, dict)
        and install_result.get("status") == "PASS"
        and install_archive_digest == archive_digest
        and (committed_status in {None, "COMMITTED", "RECOVERED_COMMITTED"})
        and (not isinstance(installed_verification, dict) or installed_verification.get("status") == "PASS")
    )
    formal = bool(gate_result and gate_result.get("status") == "PASS")
    receipt_ok = archive_validation.get("status") == "PASS" and deterministic and not errors
    receipt: Dict[str, Any] = {
        "schema_version": "3.0", "receipt_status": "PASS" if receipt_ok else "FAIL",
        "generated_at": utc_now(), "artifact_kind": "Agent Skill archive", "profile": profile,
        **identity,
        "archive": archive.name, "archive_sha256": archive_digest,
        "source_tree_sha256": sha256_tree(skill_root, exclude={"MANIFEST.sha256"}),
        "manifest_sha256": sha256_file(skill_root / "MANIFEST.sha256") if (skill_root / "MANIFEST.sha256").is_file() else None,
        "genesis": genesis_value,
        "source_control": {"commit": _git_value(skill_root, ["rev-parse", "HEAD"]), "tree": _git_value(skill_root, ["rev-parse", "HEAD^{tree}"])},
        "build_environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "dependencies": {"runtime": ["Python 3.9+", "Git for live GitHub competitor pulls"] if profile == "optimizer" else [], "python_third_party": []},
        "verification": {
            "archive_validation": archive_validation,
            "reproduction": reproduction,
            "install_result": install_result or {"status": "NOT_SUPPLIED"},
            "gate": gate_result or {"status": "NOT_SUPPLIED"},
            "errors": errors,
        },
        "claims": {
            "archive_structurally_valid": archive_validation.get("status") == "PASS",
            "installable": installed,
            "deterministically_packaged": deterministic,
            "formal_independent_promotion": formal,
            "world_best": False,
            "boundary": "Current, scoped evidence only; reheat on expiry, regression, security advisory or materially stronger peer.",
        },
    }
    if workspace:
        receipt["run"] = {"workspace": str(workspace.resolve()), "run_id": load_json(workspace / "run.json")["run_id"]}
    write_json(output, receipt)
    return receipt
