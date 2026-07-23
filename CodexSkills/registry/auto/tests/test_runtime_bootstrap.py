from __future__ import annotations

import tempfile
import unittest
import importlib.util
import json
from pathlib import Path

from CodexSkills.registry.auto.runtime.bootstrap import bootstrap_runtime
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError
from CodexSkills.registry.auto.runtime.orchestrator import SkillOpsOrchestrator
from CodexSkills.registry.auto.runtime.roots import RootEntry
from CodexSkills.governance.tools.validate_mechanism import TrustTuple

from runtime_helpers import CANDIDATE_DIGEST, CANDIDATE_GIT_OBJECT, MANIFEST_PATH, REPO_ROOT, clock, context, trust, uid


class RuntimeBootstrapTests(unittest.TestCase):
    def test_exact_external_candidate_trust_builds_29_plus_4_registry(self) -> None:
        observed = context()
        self.assertEqual(len(observed.contract.shared.schemas), 29)
        self.assertEqual(len(observed.contract.development.schemas), 33)
        self.assertEqual(observed.trust.expected_bundle_digest, CANDIDATE_DIGEST)

    def test_wrong_external_digest_fails_closed(self) -> None:
        with self.assertRaisesRegex(AutoRuntimeError, "BOOTSTRAP_TRUST_FAILED"):
            bootstrap_runtime(REPO_ROOT, trust(digest="0" * 64))

    def test_unapproved_manifest_path_fails_before_bundle_load(self) -> None:
        bad = TrustTuple(CANDIDATE_GIT_OBJECT, CANDIDATE_DIGEST, "CodexSkills/other.json", "CANDIDATE")
        with self.assertRaisesRegex(AutoRuntimeError, "BOOTSTRAP_MANIFEST_PATH_MISMATCH"):
            bootstrap_runtime(REPO_ROOT, bad)

    def test_active_mode_requires_version_in_trusted_commit(self) -> None:
        with self.assertRaisesRegex(AutoRuntimeError, "BOOTSTRAP_ACTIVE_VERSION_REQUIRED"):
            bootstrap_runtime(REPO_ROOT, trust(mode="ACTIVE"))

    def test_capability_evidence_is_public_path_free(self) -> None:
        capabilities = context().capabilities
        self.assertEqual(capabilities["network_schema_resolution"], "DISABLED")
        self.assertEqual(capabilities["runtime_install"], "FORBIDDEN")
        self.assertNotIn("interpreter_path", capabilities)
        self.assertRegex(capabilities["canonicalizer_code_digest"], r"^[0-9a-f]{64}$")

    def test_runtime_interface_is_byte_equivalent_and_not_a_trust_root(self) -> None:
        builder_path = REPO_ROOT / "CodexSkills/registry/auto/tools/build_runtime_interface.py"
        spec = importlib.util.spec_from_file_location("build_runtime_interface", builder_path)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = module.render(module.build())
        interface_path = REPO_ROOT / "CodexSkills/registry/auto/runtime-interface.json"
        self.assertEqual(interface_path.read_bytes(), expected)
        interface = json.loads(expected)
        self.assertTrue(interface["trust_tuple_repo_external_only"])
        self.assertFalse(interface["canonical_publication_permitted"])
        self.assertEqual(interface["candidate_bundle_digest"], CANDIDATE_DIGEST)
        self.assertTrue(interface["consumer_first_gate_satisfied"])
        self.assertFalse(
            interface["consumer_first_trust_tuple_drift_detected"]
        )
        self.assertEqual(
            interface["consumer_first_verified_git_object_id"],
            "sha1:2177986e897fdc50a7273f099a1305b21de2096b",
        )
        self.assertEqual(
            interface["consumer_first_observed_candidate_git_object_id"],
            CANDIDATE_GIT_OBJECT,
        )
        self.assertEqual(
            interface["consumer_first_observed_bundle_digest"],
            CANDIDATE_DIGEST,
        )
        self.assertEqual(
            interface["consumer_first_observed_status"],
            "DRAFT_NON_ACTIVE_CONSUMER_READY",
        )
        self.assertFalse(
            interface["consumer_first_canonical_publication_permitted"]
        )
        self.assertFalse(
            interface["consumer_first_repository_shards_permitted"]
        )
        self.assertFalse(interface["au_040_manifest_contract_resolved"])
        self.assertFalse(
            interface["au_040_consumer_manifest_path_contract_present"]
        )
        self.assertEqual(
            interface["au_040_authority_ruling_status"],
            "AUTO_SCHEMA_PROMOTED_MECHANISM_MATERIALIZATION_PENDING",
        )
        self.assertTrue(interface["au_040_transport_schema_draft_complete"])
        self.assertFalse(interface["au_040_retention_policy_v3_present"])
        self.assertTrue(
            interface[
                "au_040_retention_policy_v3_repository_accepted"
            ]
        )
        self.assertTrue(
            interface["au_040_semantic_policy_acceptance_complete"]
        )
        self.assertTrue(interface["au_040_schema_promotion_complete"])
        self.assertFalse(
            interface["au_040_transport_contract"]["repository_bound"]
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "current_candidate_schema_count"
            ],
            29,
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "proposed_active_schema_count"
            ],
            31,
        )
        self.assertTrue(
            interface["au_040_transport_contract"][
                "proposed_active_policy_contract_complete"
            ]
        )
        self.assertTrue(
            interface["au_040_transport_contract"][
                "promotion_required_before_candidate_materialization"
            ]
        )
        self.assertTrue(
            interface["au_040_transport_contract"][
                "promotion_requirement_satisfied"
            ]
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "schema_promotion_interface_raw_sha256"
            ],
            "65c2e83bb2491d1cb3059767cf1705fc"
            "7541bd7e97449f33a51ba17a04f5e595",
        )
        self.assertTrue(
            interface["au_040_transport_contract"][
                "historical_candidate_manifest_exact_blob_verified"
            ]
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "historical_candidate_manifest_raw_sha256"
            ],
            "0d2600fd54fcb1fb5dd0901d9acc31b4"
            "3b5cae0be8ee599f5c3c7ca0b01f9109",
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "schema_promotion_evidence_git_object_id"
            ],
            "sha1:ab49666bd3343c2abbfc6766478fad63d44163d0",
        )
        self.assertFalse(
            interface["au_040_transport_contract"][
                "working_tree_manifest_assumed_historical_candidate"
            ]
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "production_semantic_guard_codes_acknowledged"
            ],
            [
                "CANONICAL_BYTES_PHYSICAL_DIGEST_CLOSURE",
                "INDEX_EVENT_MANIFEST_CLOSURE",
                "MANIFEST_PART_IMMUTABILITY",
                "MANIFEST_PREDECESSOR_EXACT_CHAIN",
                "PRUNE_TRANSACTION_ARTIFACT_SET_CLOSURE",
                "RETENTION_ANCHOR_EXACT_365D",
                "SHARD_TRANSACTION_ARTIFACT_SET_CLOSURE",
            ],
        )
        self.assertTrue(
            interface["au_040_transport_contract"][
                "draft_paths_forbidden_in_candidate_manifest"
            ]
        )
        self.assertEqual(
            interface["au_040_transport_contract"]["loader_isolation_root"],
            "CodexSkills/registry/auto/schemas/public-v2/",
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "daily_manifest_schema_id"
            ],
            "urn:linzecolin:agentdatabase:skillops:"
            "schema:daily-run-shard-manifest:v1",
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "transaction_manifest_v1_role"
            ],
            "TRANSACTION_SETTLEMENT_ONLY",
        )
        self.assertEqual(
            interface["next_phase"],
            "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL",
        )
        self.assertTrue(interface["schedule_authority_conflict_detected"])
        self.assertFalse(interface["schedule_authority_resolved"])
        self.assertFalse(interface["schedule_complete"])
        self.assertTrue(
            interface["notification_preflight_query_endpoint_implemented"]
        )
        self.assertFalse(
            interface[
                "notification_preflight_query_endpoint_runtime_verified"
            ]
        )
        self.assertFalse(
            interface[
                "notification_real_message_metadata_readback_verified"
            ]
        )
        self.assertFalse(interface["external_gmail_ready_gate_satisfied"])
        self.assertFalse(interface["m0c_b_permitted"])
        with tempfile.TemporaryDirectory() as temporary:
            tampered = Path(temporary) / "skill_run_consumer.json"
            tampered.write_bytes(b"{}\n")
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_CONSUMER_INTERFACE_RAW_DIGEST_MISMATCH",
            ):
                module._consumer_first_evidence(tampered)
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_TRANSPORT_DRAFT_INTERFACE_RAW_DIGEST_MISMATCH",
            ):
                module._transport_draft_evidence(tampered)
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_SCHEMA_PROMOTION_INTERFACE_RAW_DIGEST_MISMATCH",
            ):
                module._schema_promotion_evidence(tampered)

    def test_bootstrap_failure_precedes_state_root_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            state = base / "state"

            def fail_bootstrap(_repo, _trust):
                raise AutoRuntimeError("SYNTHETIC_CAPABILITY_FAILURE")

            orchestrator = SkillOpsOrchestrator(
                repo_root=REPO_ROOT,
                state_root=state,
                protected_roots=(RootEntry("source", "SKILL_SOURCE", source),),
                trust=trust(),
                clock=clock(),
                bootstrap=fail_bootstrap,
            )
            with self.assertRaisesRegex(AutoRuntimeError, "SYNTHETIC_CAPABILITY_FAILURE"):
                orchestrator.run(
                    owner_run_uid=uid("run"),
                    trigger_kind="MANUAL",
                    last_full_local_date=None,
                    lane_executors={},
                )
            self.assertFalse(state.exists())


if __name__ == "__main__":
    unittest.main()
