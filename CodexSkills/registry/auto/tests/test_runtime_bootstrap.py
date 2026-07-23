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
        self.assertFalse(interface["consumer_first_gate_satisfied"])
        self.assertTrue(
            interface["consumer_first_trust_tuple_drift_detected"]
        )
        self.assertEqual(
            interface["consumer_first_observed_failure_code"],
            "skill_run_consumer_bootstrap_failed:"
            "TRUST_SCHEMA_PATH_OWNER_MISMATCH",
        )
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
