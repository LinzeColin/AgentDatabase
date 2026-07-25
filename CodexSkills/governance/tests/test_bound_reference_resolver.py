#!/usr/bin/env python3
"""Identity/version Registry and BOUND resolver deterministic gates."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
TOOLS_DIR = GOVERNANCE_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build_bound_reference_resolver as builder  # noqa: E402
import resolve_skill_binding as resolver  # noqa: E402
from canonical_json import (  # noqa: E402
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from validate_mechanism import (  # noqa: E402
    CANONICAL_MANIFEST_PATH,
    ContractError,
    TrustTuple,
    load_trusted_bundle,
    strict_load,
)


CANDIDATE_TRUST = TrustTuple(
    builder.CANDIDATE_GIT_OBJECT_ID,
    builder.CANDIDATE_BUNDLE_DIGEST,
    builder.CANDIDATE_MANIFEST_PATH,
    "CANDIDATE",
)
TS = "2026-07-25T21:44:29.000000Z"


def _with_digest(value: Dict[str, Any], field: str) -> Dict[str, Any]:
    value[field] = "0" * 64
    value[field] = canonical_digest(value, "/" + field)
    return value


def _request(
    entry: Mapping[str, Any],
    *,
    content_digest: Optional[str] = None,
    tree_digest: Optional[str] = None,
) -> Dict[str, Any]:
    invocation = {
        "evidence_type": "CONTROLLED_INVOCATION_EXACT_VERSION",
        "invocation_envelope_digest": "0" * 64,
        "invocation_uid": "inv_" + "0" * 26,
        "observed_at": TS,
        "surface_class": "CODEX_CLI",
    }
    invocation["invocation_envelope_digest"] = canonical_digest(
        invocation,
        "/invocation_envelope_digest",
    )
    return _with_digest(
        {
            "bundle_digest": builder.CANDIDATE_BUNDLE_DIGEST,
            "content_digest": (
                content_digest
                if content_digest is not None
                else entry["material"]["content_digest"]
            ),
            "controlled_invocation": invocation,
            "envelope_digest": "0" * 64,
            "protocol_revision": resolver.PROTOCOL,
            "schema_version": resolver.REQUEST_ID,
            "source_class": "AGENTS",
            "source_relative_path": entry["source_relative_path"],
            "tree_digest": (
                tree_digest
                if tree_digest is not None
                else entry["material"]["tree_digest"]
            ),
        },
        "envelope_digest",
    )


def _registered_fixture(
    snapshot: Mapping[str, Any],
    catalogs: Mapping[str, Mapping[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], Mapping[str, Any]]:
    registered_snapshot = copy.deepcopy(snapshot)
    registered_catalogs = copy.deepcopy(catalogs)
    target_entry = registered_catalogs["AGENTS"]["entries"][0]
    identity_uid = target_entry["identity_ref"]["skill_identity_uid"]
    instance_uid = target_entry["instance_ref"]["skill_instance_uid"]
    version_uid = target_entry["version_ref"]["skill_version_uid"]

    identity_row = next(
        row
        for row in registered_snapshot["identities"]
        if row["record"]["skill_identity_uid"] == identity_uid
    )
    instance_row = next(
        row
        for row in registered_snapshot["instances"]
        if row["record"]["skill_instance_uid"] == instance_uid
    )
    version_row = next(
        row
        for row in registered_snapshot["versions"]
        if row["record"]["skill_version_uid"] == version_uid
    )
    identity_row["record"]["lifecycle_status"] = "REGISTERED"
    instance_row["record"]["lifecycle_status"] = "REGISTERED"
    instance_row["record"]["provenance"]["license_id"] = "Apache-2.0"
    instance_row["record"]["provenance"][
        "license_state"
    ] = "KNOWN_ALLOWED"
    instance_row["record"]["provenance"]["trust_tier"] = "LOCAL_TRUSTED"
    known_permissions = {
        "external_side_effect": "NONE",
        "filesystem_write": "WORKSPACE_ONLY",
        "network": "NONE",
        "secrets": "NONE",
    }
    instance_row["record"]["permissions"] = known_permissions
    version_row["record"]["lifecycle_status"] = "REGISTERED"
    version_row["record"]["permissions"] = known_permissions
    version_row["record"]["permission_manifest_digest"] = hashlib.sha256(
        canonicalize_object(known_permissions)
    ).hexdigest()
    version_row["record"]["trust_tier"] = "LOCAL_TRUSTED"

    identity_row["artifact_digest"] = hashlib.sha256(
        canonicalize_object(identity_row["record"])
    ).hexdigest()
    instance_row["artifact_digest"] = hashlib.sha256(
        canonicalize_object(instance_row["record"])
    ).hexdigest()
    version_row["version_record_digest"] = hashlib.sha256(
        canonicalize_object(version_row["record"])
    ).hexdigest()
    target_entry["identity_ref"]["artifact_digest"] = identity_row[
        "artifact_digest"
    ]
    target_entry["instance_ref"]["artifact_digest"] = instance_row[
        "artifact_digest"
    ]
    target_entry["version_ref"]["version_record_digest"] = version_row[
        "version_record_digest"
    ]

    for catalog in registered_catalogs.values():
        catalog["status"] = "REGISTERED"
        _with_digest(catalog, "artifact_digest")
    catalog_by_class = registered_catalogs
    for reference in registered_snapshot["source_catalogs"]:
        reference["artifact_digest"] = catalog_by_class[
            reference["source_class"]
        ]["artifact_digest"]
    registered_snapshot["status"] = "REGISTERED"
    registered_snapshot["source_mirror_parity"] = {
        "binding_eligible": True,
        "expected_external_symlink_alias_count": 0,
        "reason_codes": [],
        "status": "COMPLETE",
        "tracked_symlink_alias_count": 0,
    }
    registered_snapshot["counts"][
        "binding_eligible_version_count"
    ] = 1
    registered_snapshot["counts"]["quarantined_version_count"] -= 1
    _with_digest(registered_snapshot, "registry_snapshot_digest")
    return registered_snapshot, registered_catalogs, target_entry


class BoundReferenceResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_trusted_bundle(REPO_ROOT, CANDIDATE_TRUST)
        cls.schemas = {
            resolver.CATALOG_ID: strict_load(
                REPO_ROOT / resolver.CATALOG_SCHEMA_PATH
            ),
            resolver.SNAPSHOT_ID: strict_load(
                REPO_ROOT / resolver.SNAPSHOT_SCHEMA_PATH
            ),
            resolver.REQUEST_ID: strict_load(
                REPO_ROOT / resolver.REQUEST_SCHEMA_PATH
            ),
        }
        cls.snapshot = strict_load(REPO_ROOT / resolver.DRAFT_SNAPSHOT_PATH)
        cls.catalogs = {
            source_class: strict_load(
                REPO_ROOT
                / resolver._expected_catalog_path(
                    source_class,
                    "DRAFT_NON_ACTIVE",
                )
            )
            for source_class in resolver.SOURCE_CLASSES
        }
        cls.context = resolver.validate_registry_documents(
            bundle=cls.bundle,
            schemas=cls.schemas,
            snapshot=cls.snapshot,
            catalogs=cls.catalogs,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            expected_snapshot_digest=cls.snapshot[
                "registry_snapshot_digest"
            ],
            trust_mode="DRAFT_NON_ACTIVE",
        )

    def test_01_builder_is_byte_equivalent(self) -> None:
        process = subprocess.run(
            [
                "/usr/bin/python3",
                "-B",
                str(TOOLS_DIR / "build_bound_reference_resolver.py"),
                "--check",
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn(
            "BOUND_REFERENCE_RESOLVER_BYTE_EQUIVALENT",
            process.stdout,
        )

    def test_02_real_snapshot_is_complete_but_not_binding_eligible(self) -> None:
        counts = self.snapshot["counts"]
        self.assertEqual(
            counts,
            {
                "binding_eligible_version_count": 0,
                "identity_count": 89,
                "instance_count": 89,
                "metadata_invalid_count": 1,
                "quarantined_version_count": 89,
                "source_catalog_count": 4,
                "source_skill_count": 89,
                "tracked_symlink_alias_count": 0,
                "version_count": 89,
            },
        )
        self.assertEqual(
            self.snapshot["source_mirror_parity"],
            {
                "binding_eligible": False,
                "expected_external_symlink_alias_count": 20,
                "reason_codes": ["SOURCE_MIRROR_SYMLINK_ALIAS_LOSS"],
                "status": "INCOMPLETE",
                "tracked_symlink_alias_count": 0,
            },
        )
        invalid = {
            entry["source_relative_path"]
            for catalog in self.catalogs.values()
            for entry in catalog["entries"]
            if entry["material"]["metadata_state"] == "INVALID"
        }
        self.assertEqual(invalid, {"codex/context-kernel"})
        self.assertEqual(len(self.context.eligible_version_uids), 0)

    def test_03_source_counts_and_catalog_closure_are_exact(self) -> None:
        self.assertEqual(
            {
                source: len(self.catalogs[builder.SOURCE_CLASSES[source]][
                    "entries"
                ])
                for source in builder.SOURCE_NAMES
            },
            builder.EXPECTED_SOURCE_SKILL_COUNTS,
        )
        self.assertEqual(
            sum(len(catalog["entries"]) for catalog in self.catalogs.values()),
            89,
        )
        self.assertEqual(len(self.context.assignments), 89)
        self.assertEqual(len(self.context.identities), 89)
        self.assertEqual(len(self.context.instances), 89)
        self.assertEqual(len(self.context.versions), 89)

    def test_04_same_names_remain_distinct_owner_review_candidates(self) -> None:
        candidates = {
            row["canonical_name"]: row
            for row in self.snapshot["identity_merge_candidates"]
        }
        self.assertIn("agent-reach", candidates)
        self.assertIn("dws", candidates)
        self.assertGreaterEqual(len(candidates["dws"]["identity_uids"]), 2)
        self.assertEqual(
            candidates["dws"]["reason_code"],
            "OWNER_REVIEW_REQUIRED",
        )
        self.assertFalse(self.snapshot["same_name_auto_merge_permitted"])

    def test_05_current_snapshot_projects_exact_observation_unknown(self) -> None:
        entry = self.catalogs["AGENTS"]["entries"][0]
        self.assertEqual(
            resolver.resolve_binding(self.context, _request(entry)),
            {
                "binding_state": "UNKNOWN",
                "unknown_reason_code": "MAPPING_NOT_PROVABLE",
            },
        )

    def test_06_request_and_controlled_invocation_digests_are_exact(self) -> None:
        entry = self.catalogs["AGENTS"]["entries"][0]
        request = _request(entry)
        request["envelope_digest"] = "f" * 64
        with self.assertRaisesRegex(
            ContractError,
            "BOUND_REFERENCE_REQUEST_DIGEST_MISMATCH",
        ):
            resolver.resolve_binding(self.context, request)
        request = _request(entry)
        request["controlled_invocation"][
            "invocation_envelope_digest"
        ] = "f" * 64
        _with_digest(request, "envelope_digest")
        with self.assertRaisesRegex(
            ContractError,
            "BOUND_REFERENCE_CONTROLLED_INVOCATION_DIGEST_MISMATCH",
        ):
            resolver.resolve_binding(self.context, request)

    def test_07_malformed_surface_and_context_fail_closed(self) -> None:
        entry = self.catalogs["AGENTS"]["entries"][0]
        request = _request(entry)
        request["controlled_invocation"]["surface_class"] = "CODEX_DESKTOP"
        request["controlled_invocation"][
            "invocation_envelope_digest"
        ] = canonical_digest(
            request["controlled_invocation"],
            "/invocation_envelope_digest",
        )
        _with_digest(request, "envelope_digest")
        with self.assertRaisesRegex(
            ContractError,
            "BOUND_REFERENCE_REQUEST_SCHEMA_INVALID",
        ):
            resolver.resolve_binding(self.context, request)
        request = _request(entry)
        request["bundle_digest"] = "f" * 64
        _with_digest(request, "envelope_digest")
        with self.assertRaisesRegex(
            ContractError,
            "BOUND_REFERENCE_REQUEST_CONTEXT_MISMATCH",
        ):
            resolver.resolve_binding(self.context, request)

    def test_08_registered_complete_fixture_resolves_bound(self) -> None:
        snapshot, catalogs, entry = _registered_fixture(
            self.snapshot,
            self.catalogs,
        )
        context = resolver.validate_registry_documents(
            bundle=self.bundle,
            schemas=self.schemas,
            snapshot=snapshot,
            catalogs=catalogs,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            expected_snapshot_digest=snapshot[
                "registry_snapshot_digest"
            ],
            trust_mode="REGISTERED",
        )
        result = resolver.resolve_binding(context, _request(entry))
        self.assertEqual(result["binding_state"], "BOUND")
        self.assertEqual(
            set(result["skill_ref"]),
            {
                "content_digest",
                "registry_snapshot_digest",
                "skill_identity_uid",
                "skill_instance_uid",
                "skill_version_uid",
                "tree_digest",
                "version_record_digest",
            },
        )
        self.assertEqual(
            result["skill_ref"]["registry_snapshot_digest"],
            snapshot["registry_snapshot_digest"],
        )

    def test_09_registered_digest_or_tree_mismatch_never_binds(self) -> None:
        snapshot, catalogs, entry = _registered_fixture(
            self.snapshot,
            self.catalogs,
        )
        context = resolver.validate_registry_documents(
            bundle=self.bundle,
            schemas=self.schemas,
            snapshot=snapshot,
            catalogs=catalogs,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            expected_snapshot_digest=snapshot[
                "registry_snapshot_digest"
            ],
            trust_mode="REGISTERED",
        )
        for request in (
            _request(entry, content_digest="f" * 64),
            _request(entry, tree_digest="f" * 64),
        ):
            self.assertEqual(
                resolver.resolve_binding(context, request),
                {
                    "binding_state": "UNKNOWN",
                    "unknown_reason_code": "MAPPING_NOT_PROVABLE",
                },
            )

    def test_10_snapshot_catalog_and_record_tamper_fail_closed(self) -> None:
        with self.assertRaisesRegex(
            ContractError,
            "REGISTRY_SNAPSHOT_BUNDLE_CONTEXT_MISMATCH",
        ):
            resolver.validate_registry_documents(
                bundle=self.bundle,
                schemas=self.schemas,
                snapshot=self.snapshot,
                catalogs=self.catalogs,
                expected_bundle_digest="f" * 64,
                expected_snapshot_digest=self.snapshot[
                    "registry_snapshot_digest"
                ],
                trust_mode="DRAFT_NON_ACTIVE",
            )
        tampered = copy.deepcopy(self.snapshot)
        tampered["counts"]["source_skill_count"] = 88
        _with_digest(tampered, "registry_snapshot_digest")
        with self.assertRaisesRegex(
            ContractError,
            "REGISTRY_SNAPSHOT_COUNT_MISMATCH",
        ):
            resolver.validate_registry_documents(
                bundle=self.bundle,
                schemas=self.schemas,
                snapshot=tampered,
                catalogs=self.catalogs,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
                expected_snapshot_digest=tampered[
                    "registry_snapshot_digest"
                ],
                trust_mode="DRAFT_NON_ACTIVE",
            )
        tampered_catalogs = copy.deepcopy(self.catalogs)
        tampered_catalogs["AGENTS"]["entries"][0]["canonical_name"] = (
            "tampered"
        )
        with self.assertRaisesRegex(
            ContractError,
            "REGISTRY_CATALOG_DIGEST_MISMATCH",
        ):
            resolver.validate_registry_documents(
                bundle=self.bundle,
                schemas=self.schemas,
                snapshot=self.snapshot,
                catalogs=tampered_catalogs,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
                expected_snapshot_digest=self.snapshot[
                    "registry_snapshot_digest"
                ],
                trust_mode="DRAFT_NON_ACTIVE",
            )
        tampered = copy.deepcopy(self.snapshot)
        tampered["versions"][0]["record"]["tree_digest"] = "f" * 64
        _with_digest(tampered, "registry_snapshot_digest")
        with self.assertRaisesRegex(
            ContractError,
            "REGISTRY_VERSION_DIGEST_MISMATCH",
        ):
            resolver.validate_registry_documents(
                bundle=self.bundle,
                schemas=self.schemas,
                snapshot=tampered,
                catalogs=self.catalogs,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
                expected_snapshot_digest=tampered[
                    "registry_snapshot_digest"
                ],
                trust_mode="DRAFT_NON_ACTIVE",
            )

    def test_11_external_git_tuple_loads_exact_draft_and_rejects_drift(
        self,
    ) -> None:
        manifest = strict_load(
            GOVERNANCE_DIR / "bundles/schema-bundle-manifest.v1.json"
        )
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            source_paths = {
                entry["relative_path"]
                for entry in [*manifest["schemas"], *manifest["policies"]]
            }
            source_paths.add(CANONICAL_MANIFEST_PATH)
            source_paths.add(
                "CodexSkills/governance/test_vectors/"
                "canonicalization-v1.json"
            )
            for relative_path in sorted(source_paths):
                source = REPO_ROOT / relative_path
                target = repo / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            shutil.copytree(
                GOVERNANCE_DIR / "registry",
                repo / "CodexSkills/governance/registry",
            )
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.name", "Mechanism Test"],
                [
                    "git",
                    "config",
                    "user.email",
                    "mechanism-test" + chr(64) + "example.invalid",
                ],
                ["git", "add", "CodexSkills"],
                ["git", "commit", "-q", "-m", "registry trust fixture"],
            ):
                process = subprocess.run(
                    command,
                    cwd=repo,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                text=True,
            ).strip()
            tagged = "sha1:" + head
            context = resolver.load_trusted_registry(
                repo,
                TrustTuple(
                    tagged,
                    builder.CANDIDATE_BUNDLE_DIGEST,
                    CANONICAL_MANIFEST_PATH,
                    "CANDIDATE",
                ),
                resolver.RegistrySnapshotTrustTuple(
                    tagged,
                    self.snapshot["registry_snapshot_digest"],
                    resolver.DRAFT_SNAPSHOT_PATH,
                    resolver.SNAPSHOT_ID,
                    "DRAFT_NON_ACTIVE",
                ),
            )
            self.assertEqual(len(context.versions), 89)
            with self.assertRaisesRegex(
                ContractError,
                "REGISTRY_SNAPSHOT_EXTERNAL_DIGEST_MISMATCH",
            ):
                resolver.load_trusted_registry(
                    repo,
                    TrustTuple(
                        tagged,
                        builder.CANDIDATE_BUNDLE_DIGEST,
                        CANONICAL_MANIFEST_PATH,
                        "CANDIDATE",
                    ),
                    resolver.RegistrySnapshotTrustTuple(
                        tagged,
                        "f" * 64,
                        resolver.DRAFT_SNAPSHOT_PATH,
                        resolver.SNAPSHOT_ID,
                        "DRAFT_NON_ACTIVE",
                    ),
                )
            with self.assertRaisesRegex(
                ContractError,
                "REGISTRY_TRUST_TUPLE_CONTRACT_MISMATCH",
            ):
                resolver.load_trusted_registry(
                    repo,
                    TrustTuple(
                        tagged,
                        builder.CANDIDATE_BUNDLE_DIGEST,
                        CANONICAL_MANIFEST_PATH,
                        "CANDIDATE",
                    ),
                    resolver.RegistrySnapshotTrustTuple(
                        tagged,
                        self.snapshot["registry_snapshot_digest"],
                        resolver.DRAFT_SNAPSHOT_PATH,
                        resolver.SNAPSHOT_ID,
                        "REGISTERED",
                    ),
                )

    def test_12_interface_and_path_ownership_remain_non_active(self) -> None:
        interface = strict_load(
            GOVERNANCE_DIR / "registry/resolver-interface.json"
        )
        self.assertEqual(
            interface["next_phase"],
            "AUTO_REGISTRY_CATALOG_PATH_RESERVATION",
        )
        self.assertFalse(interface["auto_integration_complete"])
        self.assertFalse(interface["production_trust_permitted"])
        self.assertFalse(interface["canonical_publication_permitted"])
        self.assertFalse(interface["current_materialization_promotable"])
        self.assertTrue(interface["post_reservation_rebuild_required"])
        self.assertEqual(
            interface["exact_byte_promotion_scope"],
            "POST_PARITY_COMPLETE_SUCCESSOR_MATERIALIZATION",
        )
        self.assertTrue(interface["catalog_path_reservation_required"])
        self.assertEqual(
            interface["registry_snapshot"][
                "binding_eligible_version_count"
            ],
            0,
        )
        self.assertTrue(
            interface["current_sync_executor_contract"][
                "deletes_unreserved_source_directories"
            ]
        )
        self.assertTrue(
            interface["current_sync_executor_contract"][
                "enumerates_unreserved_source_directories_as_skills"
            ]
        )
        self.assertFalse(
            (
                REPO_ROOT
                / "CodexSkills/registry/_global/"
                "registry-snapshot.v1.json"
            ).exists()
        )
        for source in builder.SOURCE_NAMES:
            self.assertFalse(
                (
                    REPO_ROOT
                    / "CodexSkills/registry"
                    / source
                    / "_catalog/catalog.v1.json"
                ).exists()
            )
        self.assertFalse((REPO_ROOT / "CodexSkills/VERSION").exists())
        manifest_schema_ids = {
            entry["id"]
            for entry in strict_load(
                GOVERNANCE_DIR
                / "bundles/schema-bundle-manifest.v1.json"
            )["schemas"]
        }
        self.assertEqual(len(manifest_schema_ids), 31)
        self.assertTrue(
            {
                resolver.CATALOG_ID,
                resolver.SNAPSHOT_ID,
                resolver.REQUEST_ID,
            }.isdisjoint(manifest_schema_ids)
        )


if __name__ == "__main__":
    unittest.main()
