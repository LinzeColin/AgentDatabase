#!/usr/bin/env python3
"""Validate the non-active AU-040 schema promotion and target closure."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(
    0,
    str(REPO_ROOT / "CodexSkills" / "governance" / "tools"),
)

from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonicalize_object,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (  # noqa: E402
    AU040AcceptanceContract,
    load_au040_acceptance,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractError,
    load_schema_directories,
    strict_load,
)
from CodexSkills.registry.auto.tools import (  # noqa: E402
    build_schema_promotion as builder,
)


@dataclasses.dataclass(frozen=True)
class SchemaPromotionContract:
    interface: Mapping[str, Any]
    acceptance: AU040AcceptanceContract
    promoted_schemas: Mapping[str, Any]


def _fail(code: str) -> None:
    raise ContractError(code)


def validate_promoted_directory(
    sources: builder.PromotionSources,
    promoted_directory: Path = builder.PROMOTED_SCHEMA_DIR,
) -> Mapping[str, Any]:
    try:
        promoted = load_schema_directories([promoted_directory])
    except ContractError:
        raise
    except OSError as exc:
        raise ContractError(
            "AUTO_SCHEMA_PROMOTION_DIRECTORY_READ_FAILED"
        ) from exc
    expected_ids = set(builder.SCHEMA_CONTRACTS)
    if set(promoted) != expected_ids:
        _fail("AUTO_SCHEMA_PROMOTION_SCHEMA_SET_MISMATCH")
    for entry in sources.promoted_schema_entries:
        schema_id = entry["id"]
        final_path = promoted_directory / Path(
            entry["canonical_relative_path"]
        ).name
        draft_path = builder.REPO_ROOT / entry["draft_relative_path"]
        try:
            final_raw = final_path.read_bytes()
            draft_raw = draft_path.read_bytes()
        except OSError as exc:
            raise ContractError(
                f"AUTO_SCHEMA_PROMOTION_SCHEMA_READ_FAILED:{schema_id}"
            ) from exc
        if final_raw != draft_raw:
            _fail(f"AUTO_SCHEMA_PROMOTION_EXACT_BYTES_MISMATCH:{schema_id}")
        if hashlib.sha256(final_raw).hexdigest() != entry["raw_sha256"]:
            _fail(f"AUTO_SCHEMA_PROMOTION_RAW_DIGEST_MISMATCH:{schema_id}")
        if (
            hashlib.sha256(
                canonicalize_object(promoted[schema_id])
            ).hexdigest()
            != entry["schema_sha256"]
        ):
            _fail(
                f"AUTO_SCHEMA_PROMOTION_CANONICAL_DIGEST_MISMATCH:{schema_id}"
            )
    return promoted


def _validate_current_candidate_manifest() -> None:
    manifest = strict_load(
        REPO_ROOT / builder.CURRENT_CANDIDATE_MANIFEST_PATH
    )
    if (
        manifest.get("bundle_digest")
        != builder.CURRENT_CANDIDATE_BUNDLE_DIGEST
        or manifest.get("schema_count") != 29
        or manifest.get("policy_count") != 5
    ):
        _fail("AUTO_SCHEMA_PROMOTION_CURRENT_CANDIDATE_DRIFT")
    schema_paths = [
        entry.get("relative_path")
        for entry in manifest.get("schemas", [])
        if isinstance(entry, dict)
    ]
    if any(
        not isinstance(relative_path, str)
        or "/transport-draft/" in relative_path
        or relative_path.startswith(
            "CodexSkills/registry/auto/schemas/public-v2/"
        )
        for relative_path in schema_paths
    ):
        _fail("AUTO_SCHEMA_PROMOTION_CURRENT_CANDIDATE_PATH_CONTAMINATION")


def load_schema_promotion() -> SchemaPromotionContract:
    sources = builder.load_sources()
    expected_interface = builder.promotion_interface(sources)
    interface = strict_load(builder.PROMOTION_INTERFACE_PATH)
    if interface != expected_interface:
        _fail("AUTO_SCHEMA_PROMOTION_INTERFACE_SEMANTIC_DRIFT")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE_SCHEMA_PROMOTED"
        or interface.get("owner_plane") != "AUTO"
        or interface.get("exact_byte_promotion_complete") is not True
        or interface.get("promotion_requirement_satisfied") is not True
        or interface.get("repository_bound") is not False
        or interface.get("au_040_complete") is not False
        or interface.get("activation_forbidden") is not True
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("bundle_materialization_performed") is not False
        or interface.get("runtime_integration_performed") is not False
        or interface.get("next_phase")
        != "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL"
    ):
        _fail("AUTO_SCHEMA_PROMOTION_STATE_INVALID")
    guard_codes = interface.get(
        "mechanism_semantic_policy_acceptance", {}
    ).get("production_semantic_guard_codes_acknowledged")
    if guard_codes != list(builder.PRODUCTION_SEMANTIC_GUARD_CODES):
        _fail("AUTO_SCHEMA_PROMOTION_GUARD_ACKNOWLEDGEMENT_MISMATCH")

    promoted = validate_promoted_directory(sources)
    acceptance = load_au040_acceptance()
    if (
        len(acceptance.transport.current_candidate.schemas) != 29
        or len(acceptance.transport.current_candidate.policies) != 5
        or len(acceptance.bundle.schemas) != 31
        or len(acceptance.bundle.policies) != 5
    ):
        _fail("AUTO_SCHEMA_PROMOTION_TARGET_COUNT_MISMATCH")
    for schema_id, schema in promoted.items():
        accepted_schema = acceptance.bundle.schemas.get(schema_id)
        if (
            accepted_schema is None
            or canonicalize_object(schema)
            != canonicalize_object(accepted_schema)
        ):
            _fail(
                f"AUTO_SCHEMA_PROMOTION_ACCEPTED_BYTES_MISMATCH:{schema_id}"
            )
    _validate_current_candidate_manifest()
    return SchemaPromotionContract(interface, acceptance, promoted)


def lint_promotion() -> None:
    contract = load_schema_promotion()
    print(
        "AUTO_SCHEMA_PROMOTION_VALID "
        f"promoted={len(contract.promoted_schemas)} "
        "current=29/5 target=31/5 "
        "repository_bound=false active=false"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lint-promotion")
    args = parser.parse_args(argv)
    if args.command == "lint-promotion":
        lint_promotion()
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
