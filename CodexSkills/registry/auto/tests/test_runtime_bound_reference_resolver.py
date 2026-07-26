from __future__ import annotations

import copy
import dataclasses
import hashlib
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest import mock

from CodexSkills.governance.tools.canonical_json import parse_json_bytes
from CodexSkills.registry.auto.runtime import binding_resolver
from CodexSkills.registry.auto.runtime.binding_resolver import (
    RegistrySnapshotTrustTuple,
    load_verified_bound_reference_resolver,
)
from CodexSkills.registry.auto.runtime.bootstrap import (
    BootstrapContext,
    TRUSTED_MECHANISM_RUNTIME_PATHS,
    bootstrap_runtime,
    require_bound_reference_resolver_authority,
)
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError
from CodexSkills.registry.auto.tools import bound_reference_resolver_cli

from runtime_helpers import (
    BOUND_REFERENCE_CONTROL_GIT_OBJECT,
    REPO_ROOT,
    bound_reference_control_trust,
    expected_bound_reference_control_failure_pattern,
    final_contract,
    registered_snapshot_trust,
    synthetic_repository_bound_context,
    trust,
    verified_binding_resolver,
)


def control_interface():
    object_id = BOUND_REFERENCE_CONTROL_GIT_OBJECT.split(":", 1)[1]
    raw = binding_resolver._git_blob(
        REPO_ROOT,
        object_id,
        "CodexSkills/governance/activation/control-interface.json",
    )
    return parse_json_bytes(raw)


class RuntimeBoundReferenceResolverTests(unittest.TestCase):
    def test_exact_external_tuple_proves_unknown_only_snapshot(self) -> None:
        proof = verified_binding_resolver()
        self.assertEqual(proof.source_skill_count, 88)
        self.assertEqual(proof.binding_eligible_version_count, 0)
        self.assertTrue(proof.all_current_versions_unknown_verified)
        observed = 0
        for source_class in proof._module.SOURCE_CLASSES:
            for entry in proof._context.catalogs[source_class]["entries"]:
                request = binding_resolver._request_for_entry(
                    proof._module,
                    entry,
                    bundle_digest=(
                        proof._context.snapshot["bundle_digest"]
                    ),
                    source_class=source_class,
                )
                self.assertEqual(
                    proof.resolve(request),
                    {
                        "binding_state": "UNKNOWN",
                        "unknown_reason_code": "MAPPING_NOT_PROVABLE",
                    },
                )
                observed += 1
        self.assertEqual(observed, 88)

    def test_external_snapshot_tuple_is_exact_and_non_substitutable(
        self,
    ) -> None:
        exact = registered_snapshot_trust()
        mutations = (
            dataclasses.replace(
                exact,
                verified_git_object_id=trust().verified_git_object_id,
            ),
            dataclasses.replace(
                exact,
                canonical_snapshot_digest="0" * 64,
            ),
            dataclasses.replace(
                exact,
                canonical_snapshot_path="CodexSkills/registry/other.json",
            ),
            dataclasses.replace(
                exact,
                canonical_snapshot_schema_id="urn:invalid",
            ),
            dataclasses.replace(exact, mode="ACTIVE"),
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                with self.assertRaisesRegex(
                    AutoRuntimeError,
                    "BOUND_REFERENCE_RESOLVER_"
                    "(?:EXTERNAL_TUPLE|SNAPSHOT_CONTRACT)_MISMATCH",
                ):
                    load_verified_bound_reference_resolver(
                        REPO_ROOT,
                        trust(),
                        bound_reference_control_trust(),
                        control_interface(),
                        mutated,
                    )

    def test_control_cannot_rebind_resolver_interface_digest(self) -> None:
        forged = copy.deepcopy(control_interface())
        forged["bound_reference_resolver_contract"][
            "artifact_digest"
        ] = "0" * 64
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "BOUND_REFERENCE_RESOLVER_INTERFACE_RAW_DIGEST_MISMATCH",
        ):
            load_verified_bound_reference_resolver(
                REPO_ROOT,
                trust(),
                bound_reference_control_trust(),
                forged,
                registered_snapshot_trust(),
            )

    def test_successor_control_phase_can_reuse_exact_registered_closure(
        self,
    ) -> None:
        successor = copy.deepcopy(control_interface())
        successor["next_phase"] = "AUTO_SUCCESSOR_PHASE"
        successor["transition_contract"][
            "bound_reference_resolver_auto_integration_complete"
        ] = True
        successor["transition_contract"][
            "bound_reference_resolver_gate_satisfied"
        ] = True
        successor["transition_contract"][
            "effective_runtime_state_write_permitted"
        ] = True
        proof = load_verified_bound_reference_resolver(
            REPO_ROOT,
            trust(),
            bound_reference_control_trust(),
            successor,
            registered_snapshot_trust(),
        )
        self.assertTrue(proof.all_current_versions_unknown_verified)
        self.assertEqual(proof.source_skill_count, 88)

    def test_local_mechanism_resolver_drift_fails_closed(self) -> None:
        target = REPO_ROOT / (
            "CodexSkills/governance/tools/resolve_skill_binding.py"
        )
        original = Path.read_bytes

        def forged(path):
            if path == target:
                return b"forged resolver runtime\n"
            return original(path)

        with mock.patch.object(Path, "read_bytes", forged):
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT",
            ):
                load_verified_bound_reference_resolver(
                    REPO_ROOT,
                    trust(),
                    bound_reference_control_trust(),
                    control_interface(),
                    registered_snapshot_trust(),
                )

    def test_runtime_authority_requires_gate_and_exact_proof(self) -> None:
        exact = synthetic_repository_bound_context()
        self.assertIs(
            require_bound_reference_resolver_authority(exact),
            exact.binding_resolver,
        )
        interface = copy.deepcopy(dict(exact.control_interface))
        interface["transition_contract"][
            "bound_reference_resolver_gate_satisfied"
        ] = False
        pending = dataclasses.replace(
            exact,
            control_interface=MappingProxyType(interface),
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^BOUND_REFERENCE_RESOLVER_NOT_SATISFIED$",
        ):
            require_bound_reference_resolver_authority(pending)
        forged_proof = dataclasses.replace(
            exact.binding_resolver,
            source_skill_count=87,
        )
        forged = dataclasses.replace(
            exact,
            binding_resolver=forged_proof,
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^RUNTIME_BOUND_REFERENCE_RESOLVER_NOT_VERIFIED$",
        ):
            require_bound_reference_resolver_authority(forged)

    def test_predecessor_control_never_authorizes_new_local_auto_bytes(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            expected_bound_reference_control_failure_pattern(),
        ):
            bootstrap_runtime(
                REPO_ROOT,
                trust(),
                bound_reference_control_trust(),
                registered_snapshot_trust(),
            )

    def test_promoted_snapshot_control_requires_external_snapshot_tuple(
        self,
    ) -> None:
        interface = control_interface()
        transport = interface["transport_runtime_interface"]
        auto_object = transport["verified_git_object_id"].split(":", 1)[1]
        auto_raw = binding_resolver._git_blob(
            REPO_ROOT,
            auto_object,
            transport["relative_path"],
        )
        auto_interface = parse_json_bytes(auto_raw)
        bound_object = BOUND_REFERENCE_CONTROL_GIT_OBJECT.split(":", 1)[1]
        coherent = {
            REPO_ROOT.joinpath(*relative_path.split("/")): (
                binding_resolver._git_blob(
                    REPO_ROOT,
                    bound_object,
                    relative_path,
                )
            )
            for relative_path in TRUSTED_MECHANISM_RUNTIME_PATHS
        }
        coherent[
            REPO_ROOT.joinpath(*transport["relative_path"].split("/"))
        ] = auto_raw
        for entry in auto_interface["module_artifacts"]:
            relative_path = entry["relative_path"]
            coherent[
                REPO_ROOT.joinpath(*relative_path.split("/"))
            ] = binding_resolver._git_blob(
                REPO_ROOT,
                auto_object,
                relative_path,
            )
        original = Path.read_bytes

        def predecessor_view(path):
            if path in coherent:
                return coherent[path]
            return original(path)

        with mock.patch.object(Path, "read_bytes", predecessor_view):
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "^BOOTSTRAP_REGISTRY_SNAPSHOT_TRUST_REQUIRED$",
            ):
                bootstrap_runtime(
                    REPO_ROOT,
                    trust(),
                    bound_reference_control_trust(),
                )

    def test_production_cli_fails_before_reading_request_on_stale_control(
        self,
    ) -> None:
        argv = [
            "--repo-root",
            str(REPO_ROOT),
            "--verified-candidate-git-object-id",
            trust().verified_git_object_id,
            "--expected-bundle-digest",
            trust().expected_bundle_digest,
            "--canonical-manifest-path",
            trust().canonical_manifest_path,
            "--candidate-mode",
            trust().mode,
            "--verified-control-git-object-id",
            bound_reference_control_trust().verified_git_object_id,
            "--expected-control-interface-raw-sha256",
            (
                bound_reference_control_trust()
                .expected_control_interface_raw_sha256
            ),
            "--canonical-control-interface-path",
            (
                bound_reference_control_trust()
                .canonical_control_interface_path
            ),
            "--control-mode",
            bound_reference_control_trust().mode,
            "--verified-registry-git-object-id",
            registered_snapshot_trust().verified_git_object_id,
            "--expected-registry-snapshot-digest",
            registered_snapshot_trust().canonical_snapshot_digest,
            "--canonical-registry-snapshot-path",
            registered_snapshot_trust().canonical_snapshot_path,
            "--canonical-registry-snapshot-schema-id",
            registered_snapshot_trust().canonical_snapshot_schema_id,
            "--registry-mode",
            registered_snapshot_trust().mode,
        ]
        with mock.patch.object(
            bound_reference_resolver_cli,
            "_request",
        ) as request_reader:
            with self.assertRaisesRegex(
                AutoRuntimeError,
                expected_bound_reference_control_failure_pattern(),
            ):
                bound_reference_resolver_cli.main(argv)
            request_reader.assert_not_called()

    def test_proof_fingerprint_is_not_caller_supplied(self) -> None:
        proof = verified_binding_resolver()
        self.assertEqual(
            hashlib.sha256(
                (
                    REPO_ROOT
                    / "CodexSkills/governance/registry/"
                    "resolver-interface.json"
                ).read_bytes()
            ).hexdigest(),
            proof.resolver_interface_raw_sha256,
        )
        self.assertEqual(
            proof.registry_snapshot_digest,
            registered_snapshot_trust().canonical_snapshot_digest,
        )
        self.assertIsInstance(
            synthetic_repository_bound_context(),
            BootstrapContext,
        )
        self.assertIs(final_contract(), final_contract())


if __name__ == "__main__":
    unittest.main()
