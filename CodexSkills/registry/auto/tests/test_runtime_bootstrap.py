from __future__ import annotations

import argparse
import contextlib
import hashlib
import tempfile
import unittest
import importlib.util
import json
from pathlib import Path
from unittest import mock

from CodexSkills.registry.auto.runtime.bootstrap import (
    _capability_smoke,
    bootstrap_runtime,
)
from CodexSkills.registry.auto.runtime import bootstrap as runtime_bootstrap
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError
from CodexSkills.registry.auto.runtime.orchestrator import SkillOpsOrchestrator
from CodexSkills.registry.auto.runtime.roots import RootEntry
from CodexSkills.registry.auto.runtime.writer_shadow import (
    validate_unbound_writer_candidate,
)
from CodexSkills.registry.auto.tools.activation_handshake_cli import (
    _context_and_handshake,
    _publish_settlement,
)
from CodexSkills.registry.auto.tools.notification_transport_cli import (
    _components,
)
from CodexSkills.governance.tools.validate_mechanism import TrustTuple

from runtime_helpers import (
    CANDIDATE_DIGEST,
    CANDIDATE_GIT_OBJECT,
    CONTROL_GIT_OBJECT,
    CONTROL_INTERFACE_RAW_SHA256,
    MANIFEST_PATH,
    REPO_ROOT,
    clock,
    control_trust,
    expected_stale_control_failure_pattern,
    final_contract,
    trust,
    uid,
)


class RuntimeBootstrapTests(unittest.TestCase):
    def test_unbound_writer_shadow_proves_31_plus_4_registry(self) -> None:
        contract = final_contract()
        self.assertEqual(len(contract.shared.schemas), 31)
        self.assertEqual(len(contract.development.schemas), 35)
        evidence = validate_unbound_writer_candidate(
            REPO_ROOT,
            trust(),
            control_trust(),
        )
        self.assertEqual(
            evidence.status,
            "UNBOUND_CONTROL_SYNC_PENDING",
        )
        self.assertEqual(evidence.schema_count, 31)
        self.assertEqual(evidence.policy_count, 5)
        self.assertEqual(evidence.historical_bound_module_count, 21)
        self.assertFalse(
            evidence.current_runtime_control_bound_at_materialization
        )
        self.assertFalse(evidence.runtime_state_write_permitted)
        self.assertTrue(
            evidence.runtime_shard_writer_integration_complete
        )
        self.assertFalse(
            evidence.publisher_v2_runtime_integration_complete
        )

    def test_production_bootstrap_rejects_unbound_local_writer(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            expected_stale_control_failure_pattern(),
        ):
            bootstrap_runtime(
                REPO_ROOT,
                trust(),
                control_trust(),
            )

    def test_shadow_rejects_forged_external_control_tuple(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "WRITER_SHADOW_CONTROL_TRUST_TUPLE_MISMATCH",
        ):
            validate_unbound_writer_candidate(
                REPO_ROOT,
                trust(),
                control_trust(raw_digest="0" * 64),
            )

    def test_successor_control_scope_is_exact(self) -> None:
        observed = control_trust()
        self.assertEqual(
            observed.verified_git_object_id,
            CONTROL_GIT_OBJECT,
        )
        self.assertEqual(
            observed.expected_control_interface_raw_sha256,
            CONTROL_INTERFACE_RAW_SHA256,
        )

    def test_wrong_external_digest_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "BOOTSTRAP_CONTROL_CANDIDATE_TRUST_MISMATCH",
        ):
            bootstrap_runtime(
                REPO_ROOT,
                trust(digest="0" * 64),
                control_trust(),
            )

    def test_unapproved_manifest_path_fails_before_bundle_load(self) -> None:
        bad = TrustTuple(CANDIDATE_GIT_OBJECT, CANDIDATE_DIGEST, "CodexSkills/other.json", "CANDIDATE")
        with self.assertRaisesRegex(AutoRuntimeError, "BOOTSTRAP_MANIFEST_PATH_MISMATCH"):
            bootstrap_runtime(REPO_ROOT, bad, control_trust())

    def test_active_mode_cannot_reinterpret_candidate_control(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "BOOTSTRAP_CONTROL_CANDIDATE_TRUST_MISMATCH",
        ):
            bootstrap_runtime(
                REPO_ROOT,
                trust(mode="ACTIVE"),
                control_trust(),
            )

    def test_forged_control_digest_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "BOOTSTRAP_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH",
        ):
            bootstrap_runtime(
                REPO_ROOT,
                trust(),
                control_trust(raw_digest="0" * 64),
            )

    def test_historical_29_profile_is_not_integrated_runtime(self) -> None:
        historical = TrustTuple(
            "sha1:899a4374bc02f5e18444fea7404864df7b118adf",
            "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5",
            MANIFEST_PATH,
            "CANDIDATE",
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "BOOTSTRAP_CONTROL_CANDIDATE_TRUST_MISMATCH",
        ):
            bootstrap_runtime(
                REPO_ROOT,
                historical,
                control_trust(),
            )

    def test_capability_evidence_is_public_path_free(self) -> None:
        capabilities = _capability_smoke(REPO_ROOT)
        self.assertEqual(capabilities["network_schema_resolution"], "DISABLED")
        self.assertEqual(capabilities["runtime_install"], "FORBIDDEN")
        self.assertNotIn("interpreter_path", capabilities)
        self.assertRegex(capabilities["canonicalizer_code_digest"], r"^[0-9a-f]{64}$")

    def test_current_control_blocks_production_clis_before_state_access(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_root = Path(temporary) / "state"
            common = {
                "repo_root": REPO_ROOT,
                "state_root": state_root,
                "expected_bundle_digest": CANDIDATE_DIGEST,
                "canonical_manifest_path": MANIFEST_PATH,
                "verified_control_git_object_id": CONTROL_GIT_OBJECT,
                "expected_control_interface_raw_sha256": (
                    CONTROL_INTERFACE_RAW_SHA256
                ),
                "canonical_control_interface_path": (
                    "CodexSkills/governance/activation/"
                    "control-interface.json"
                ),
                "control_mode": "DRAFT_NON_ACTIVE_CONTROL",
            }
            notification_args = argparse.Namespace(
                **common,
                verified_git_object_id=CANDIDATE_GIT_OBJECT,
                mode="CANDIDATE",
            )
            with contextlib.ExitStack() as stack:
                path_resolver = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "notification_transport_cli."
                        "NotificationPathContract.resolve"
                    )
                )
                recipient_loader = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "notification_transport_cli.RecipientMapping.load"
                    )
                )
                gmail_config_loader = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "notification_transport_cli.GmailApiConfig.load"
                    )
                )
                gmail_transport = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "notification_transport_cli."
                        "GmailApiNotificationTransport"
                    )
                )
                notifier = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "notification_transport_cli.TransactionalNotifier"
                    )
                )
                with self.assertRaisesRegex(
                    AutoRuntimeError,
                    expected_stale_control_failure_pattern(),
                ):
                    _components(
                        notification_args,
                        state_write_requested=True,
                    )
                path_resolver.assert_not_called()
                recipient_loader.assert_not_called()
                gmail_config_loader.assert_not_called()
                gmail_transport.assert_not_called()
                notifier.assert_not_called()
            activation_args = argparse.Namespace(
                **common,
                verified_candidate_git_object_id=(
                    CANDIDATE_GIT_OBJECT
                ),
                candidate_mode="CANDIDATE",
            )
            with contextlib.ExitStack() as stack:
                handshake = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "activation_handshake_cli.ActivationHandshake"
                    )
                )
                lock_preparer = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "activation_handshake_cli._prepare_lock"
                    )
                )
                git_backend = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "activation_handshake_cli.SubprocessGitBackend"
                    )
                )
                publisher = stack.enter_context(
                    mock.patch(
                        "CodexSkills.registry.auto.tools."
                        "activation_handshake_cli.PhysicalPublisher"
                    )
                )
                with self.assertRaisesRegex(
                    AutoRuntimeError,
                    expected_stale_control_failure_pattern(),
                ):
                    _context_and_handshake(activation_args)
                with self.assertRaisesRegex(
                    AutoRuntimeError,
                    expected_stale_control_failure_pattern(),
                ):
                    _publish_settlement(activation_args)
                handshake.assert_not_called()
                lock_preparer.assert_not_called()
                git_backend.assert_not_called()
                publisher.assert_not_called()
            self.assertFalse(state_root.exists())

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
            "sha1:91a12e48351be3ee05ec23ef61aec81056b02014",
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
        self.assertTrue(interface["au_040_manifest_contract_resolved"])
        self.assertTrue(
            interface["au_040_consumer_manifest_path_contract_present"]
        )
        self.assertEqual(
            interface["au_040_authority_ruling_status"],
            "RUNTIME_WRITER_INTEGRATED_CONTROL_SYNC_PENDING",
        )
        self.assertFalse(interface["au_040_complete"])
        self.assertTrue(interface["au_040_transport_schema_draft_complete"])
        self.assertTrue(interface["au_040_retention_policy_v3_present"])
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
            31,
        )
        self.assertEqual(
            interface["au_040_transport_contract"][
                "historical_candidate_schema_count"
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
        self.assertTrue(
            interface["au_040_transport_contract"][
                "final_candidate_materialization_complete"
            ]
        )
        self.assertTrue(
            interface["au_040_transport_contract"][
                "runtime_shard_writer_integration_complete"
            ]
        )
        self.assertFalse(
            interface["au_040_transport_contract"][
                "publisher_v2_runtime_integration_complete"
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
            "MECHANISM_POST_AU040_WRITER_CONTROL_SYNC",
        )
        self.assertTrue(
            interface["auto_exact_bundle_integration_complete"]
        )
        self.assertTrue(interface["dual_external_trust_tuples_required"])
        historical_control = interface[
            "historical_control_observation"
        ]
        self.assertTrue(
            historical_control[
                "observed_auto_runtime_integration_complete"
            ]
        )
        self.assertTrue(
            historical_control[
                "observed_runtime_state_write_permitted"
            ]
        )
        self.assertEqual(
            historical_control["bound_auto_git_object_id"],
            "sha1:7ed9e761921f557887440803d1fc7327f3e986a9",
        )
        self.assertEqual(
            historical_control[
                "bound_auto_runtime_interface_raw_sha256"
            ],
            "09af0c00273825e90a489f413a2f0bb6"
            "995042e5b4eea17973ce7582eab66340",
        )
        self.assertEqual(
            historical_control["bound_auto_module_count"],
            21,
        )
        self.assertEqual(
            historical_control["verified_git_object_id"],
            CONTROL_GIT_OBJECT,
        )
        self.assertEqual(
            historical_control["interface_raw_sha256"],
            CONTROL_INTERFACE_RAW_SHA256,
        )
        self.assertTrue(
            historical_control[
                "working_tree_control_is_not_historical_trust_evidence"
            ]
        )
        materialization = interface[
            "runtime_interface_materialization_snapshot"
        ]
        self.assertEqual(
            materialization["semantic_scope"],
            "INTERFACE_MATERIALIZATION_ONLY",
        )
        self.assertFalse(
            materialization["current_auto_runtime_control_bound"]
        )
        self.assertFalse(
            materialization["runtime_state_write_permitted"]
        )
        self.assertTrue(
            interface["control_sync_required_before_state_write"]
        )
        self.assertTrue(interface["runtime_preflight_shadow_permitted"])
        self.assertTrue(
            interface["runtime_shard_writer_integration_complete"]
        )
        self.assertFalse(
            interface["publisher_v2_runtime_integration_complete"]
        )
        self.assertFalse(interface["repository_bound"])
        self.assertFalse(interface["runtime_state_write_permitted"])
        self.assertEqual(
            interface["runtime_writer_shadow_status"],
            "UNBOUND_CONTROL_SYNC_PENDING",
        )
        self.assertEqual(
            interface["runtime_writer_shadow_validator_kind"],
            "DEVELOPMENT_ONLY_UNBOUND",
        )
        self.assertFalse(
            interface["runtime_writer_shadow_returns_bootstrap_context"]
        )
        self.assertFalse(
            interface["runtime_writer_shadow_state_access_permitted"]
        )
        self.assertEqual(interface["shared_bundle_schema_count"], 31)
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
            original_git_blob = module._git_blob

            def tampered_historical_blob(object_id, relative_path):
                if (
                    object_id == module.CONTROL_EVIDENCE_GIT_OBJECT
                    and relative_path
                    == module.CONTROL_INTERFACE_REPO_PATH
                ):
                    return b"{}\n"
                return original_git_blob(object_id, relative_path)

            with mock.patch.object(
                module,
                "_git_blob",
                side_effect=tampered_historical_blob,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "AUTO_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH",
                ):
                    module._historical_control_observation()

    def test_successor_control_change_preserves_historical_builder_and_shadow(
        self,
    ) -> None:
        builder_path = (
            REPO_ROOT
            / "CodexSkills/registry/auto/tools/build_runtime_interface.py"
        )
        spec = importlib.util.spec_from_file_location(
            "successor_stable_runtime_interface",
            builder_path,
        )
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = module.render(module.build())
        control_path = REPO_ROOT.joinpath(
            *(
                "CodexSkills/governance/activation/"
                "control-interface.json"
            ).split("/")
        )
        mechanism_builder_path = REPO_ROOT.joinpath(
            *(
                "CodexSkills/governance/tools/"
                "build_activation_control.py"
            ).split("/")
        )
        original_read_bytes = Path.read_bytes

        def successor_read_bytes(path):
            if path == control_path:
                return (
                    b'{"status":"DRAFT_NON_ACTIVE",'
                    b'"successor_simulation":true}\n'
                )
            if path == mechanism_builder_path:
                return b"# successor control builder simulation\n"
            return original_read_bytes(path)

        with mock.patch.object(
            Path,
            "read_bytes",
            successor_read_bytes,
        ):
            self.assertEqual(module.render(module.build()), expected)
            evidence = validate_unbound_writer_candidate(
                REPO_ROOT,
                trust(),
                control_trust(),
            )
            self.assertEqual(
                evidence.status,
                "UNBOUND_CONTROL_SYNC_PENDING",
            )
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "^BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT$",
            ):
                bootstrap_runtime(
                    REPO_ROOT,
                    trust(),
                    control_trust(),
                )

    def test_successor_bound_interface_and_git_modules_validate_exactly(
        self,
    ) -> None:
        control_object = runtime_bootstrap._split_git_object(
            REPO_ROOT,
            CONTROL_GIT_OBJECT,
            "TEST_SUCCESSOR_CONTROL",
        )
        historical_control_raw = runtime_bootstrap._git_blob(
            REPO_ROOT,
            control_object,
            runtime_bootstrap.CONTROL_INTERFACE_PATH,
        )
        successor_control = json.loads(historical_control_raw)
        current_interface_path = REPO_ROOT.joinpath(
            "CodexSkills/registry/auto/runtime-interface.json"
        )
        current_interface_raw = current_interface_path.read_bytes()
        current_interface = json.loads(current_interface_raw)
        successor_control["transport_runtime_interface"][
            "artifact_digest"
        ] = hashlib.sha256(current_interface_raw).hexdigest()
        successor_control["transport_runtime_interface"][
            "module_count"
        ] = current_interface["module_count"]
        successor_control_raw = (
            json.dumps(
                successor_control,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        successor_trust = runtime_bootstrap.ControlTrustTuple(
            CONTROL_GIT_OBJECT,
            hashlib.sha256(successor_control_raw).hexdigest(),
            runtime_bootstrap.CONTROL_INTERFACE_PATH,
            runtime_bootstrap.CONTROL_MODE,
        )
        source_object = runtime_bootstrap._split_git_object(
            REPO_ROOT,
            successor_control["transport_runtime_interface"][
                "verified_git_object_id"
            ],
            "TEST_SUCCESSOR_AUTO",
        )
        current_modules = {
            entry["relative_path"]: REPO_ROOT.joinpath(
                *entry["relative_path"].split("/")
            ).read_bytes()
            for entry in current_interface["module_artifacts"]
        }
        original_git_blob = runtime_bootstrap._git_blob
        original_read_bytes = Path.read_bytes
        control_path = REPO_ROOT.joinpath(
            *runtime_bootstrap.CONTROL_INTERFACE_PATH.split("/")
        )

        def successor_git_blob(repo_root, object_id, relative_path):
            if (
                object_id == control_object
                and relative_path
                == runtime_bootstrap.CONTROL_INTERFACE_PATH
            ):
                return successor_control_raw
            if (
                object_id == source_object
                and relative_path
                == "CodexSkills/registry/auto/runtime-interface.json"
            ):
                return current_interface_raw
            if (
                object_id == source_object
                and relative_path in current_modules
            ):
                return current_modules[relative_path]
            return original_git_blob(
                repo_root,
                object_id,
                relative_path,
            )

        def successor_read_bytes(path):
            if path == control_path:
                return successor_control_raw
            return original_read_bytes(path)

        with mock.patch.object(
            runtime_bootstrap,
            "_git_blob",
            side_effect=successor_git_blob,
        ), mock.patch.object(
            Path,
            "read_bytes",
            successor_read_bytes,
        ):
            observed = runtime_bootstrap._verify_control_trust(
                REPO_ROOT,
                trust(),
                successor_trust,
            )
            self.assertEqual(
                observed["transport_runtime_interface"][
                    "artifact_digest"
                ],
                hashlib.sha256(current_interface_raw).hexdigest(),
            )
            self.assertEqual(
                current_interface["next_phase"],
                "MECHANISM_POST_AU040_WRITER_CONTROL_SYNC",
            )

        first_module = current_interface["module_artifacts"][0][
            "relative_path"
        ]

        def forged_module_git_blob(repo_root, object_id, relative_path):
            if (
                object_id == source_object
                and relative_path == first_module
            ):
                return b"forged successor module\n"
            return successor_git_blob(
                repo_root,
                object_id,
                relative_path,
            )

        with mock.patch.object(
            runtime_bootstrap,
            "_git_blob",
            side_effect=forged_module_git_blob,
        ), mock.patch.object(
            Path,
            "read_bytes",
            successor_read_bytes,
        ):
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "^BOOTSTRAP_AUTO_RUNTIME_MODULE_GIT_DIGEST_MISMATCH$",
            ):
                runtime_bootstrap._verify_control_trust(
                    REPO_ROOT,
                    trust(),
                    successor_trust,
                )

    def test_bootstrap_failure_precedes_state_root_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            state = base / "state"

            def fail_bootstrap(_repo, _trust, _control_trust):
                raise AutoRuntimeError("SYNTHETIC_CAPABILITY_FAILURE")

            orchestrator = SkillOpsOrchestrator(
                repo_root=REPO_ROOT,
                state_root=state,
                protected_roots=(RootEntry("source", "SKILL_SOURCE", source),),
                trust=trust(),
                control_trust=control_trust(),
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
