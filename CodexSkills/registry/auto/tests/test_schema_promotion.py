from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(
    0,
    str(REPO_ROOT / "CodexSkills" / "governance" / "tools"),
)

from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractError,
    validate_instance,
)
from CodexSkills.registry.auto.tools import build_schema_promotion as builder
from CodexSkills.registry.auto.tools.validate_schema_promotion import (
    load_schema_promotion,
    validate_promoted_directory,
)


class SchemaPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = builder.load_sources()
        cls.contract = load_schema_promotion()

    def test_builder_is_byte_equivalent(self) -> None:
        for output_path, expected in builder.generated_files(
            self.sources
        ).items():
            self.assertEqual(output_path.read_bytes(), expected)

    def test_four_promoted_schemas_are_exact_draft_bytes(self) -> None:
        self.assertEqual(
            set(self.contract.promoted_schemas),
            set(builder.SCHEMA_CONTRACTS),
        )
        for entry in self.sources.promoted_schema_entries:
            final_path = builder.REPO_ROOT / entry[
                "canonical_relative_path"
            ]
            draft_path = builder.REPO_ROOT / entry["draft_relative_path"]
            self.assertEqual(final_path.read_bytes(), draft_path.read_bytes())
            self.assertTrue(entry["exact_bytes_equal"])

    def test_interface_pins_external_acceptance_and_all_guards(self) -> None:
        interface = self.contract.interface
        acceptance = interface["mechanism_semantic_policy_acceptance"]
        self.assertEqual(
            acceptance["interface_raw_sha256"],
            builder.ACCEPTANCE_INTERFACE_RAW_SHA256,
        )
        self.assertEqual(
            acceptance["verified_git_object_id"],
            builder.ACCEPTANCE_INTERFACE_GIT_OBJECT,
        )
        self.assertEqual(
            acceptance[
                "production_semantic_guard_codes_acknowledged"
            ],
            list(builder.PRODUCTION_SEMANTIC_GUARD_CODES),
        )
        self.assertTrue(interface["exact_byte_promotion_complete"])
        self.assertTrue(interface["promotion_requirement_satisfied"])
        self.assertFalse(interface["bundle_materialization_performed"])
        self.assertFalse(interface["runtime_integration_performed"])
        self.assertFalse(interface["repository_bound"])
        self.assertFalse(interface["au_040_complete"])
        self.assertFalse(interface["canonical_publication_permitted"])
        self.assertTrue(interface["activation_forbidden"])

    def test_current_candidate_is_29_5_and_target_is_31_5(self) -> None:
        acceptance = self.contract.acceptance
        self.assertEqual(
            len(acceptance.transport.current_candidate.schemas),
            29,
        )
        self.assertEqual(
            len(acceptance.transport.current_candidate.policies),
            5,
        )
        self.assertEqual(len(acceptance.bundle.schemas), 31)
        self.assertEqual(len(acceptance.bundle.policies), 5)
        current = self.contract.interface["current_trusted_candidate"]
        self.assertEqual(current["schema_count"], 29)
        self.assertEqual(current["policy_count"], 5)
        self.assertTrue(current["unchanged_by_this_promotion"])

    def test_loader_isolation_and_next_owner_phase_are_explicit(self) -> None:
        interface = self.contract.interface
        isolation = interface["loader_isolation_invariant"]
        self.assertEqual(
            isolation["current_candidate_recursive_loader_root"],
            "CodexSkills/registry/auto/schemas/public/",
        )
        self.assertEqual(
            isolation["promoted_canonical_root"],
            "CodexSkills/registry/auto/schemas/public-v2/",
        )
        self.assertFalse(
            isolation["promoted_paths_visible_to_current_loader"]
        )
        self.assertEqual(
            interface["next_phase"],
            "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL",
        )
        self.assertEqual(
            interface["bundle_materialization_owner_plane"],
            "MECHANISM",
        )
        for entry in interface["promoted_schema_entries"]:
            self.assertNotIn(
                "draft",
                Path(entry["canonical_relative_path"]).parts,
            )

    def test_unknown_schema_urn_fails_closed_in_target_registry(self) -> None:
        with self.assertRaisesRegex(
            ContractError,
            "TRUSTED_SCHEMA_ID_UNKNOWN",
        ):
            validate_instance(
                self.contract.acceptance.bundle,
                {},
                builder.SCHEMA_PREFIX + "unknown-promotion:v1",
                verify_digest=False,
            )

    def test_draft_and_acceptance_raw_digest_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            tampered_draft = temporary_root / "draft-interface.json"
            tampered_draft.write_bytes(
                builder.DRAFT_INTERFACE_PATH.read_bytes() + b" "
            )
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_SCHEMA_PROMOTION_DRAFT_INTERFACE_RAW_DIGEST_MISMATCH",
            ):
                builder.load_sources(
                    draft_interface_path=tampered_draft,
                    acceptance_interface_path=(
                        builder.ACCEPTANCE_INTERFACE_PATH
                    ),
                )
            tampered_acceptance = temporary_root / "acceptance.json"
            tampered_acceptance.write_bytes(
                builder.ACCEPTANCE_INTERFACE_PATH.read_bytes() + b" "
            )
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_SCHEMA_PROMOTION_ACCEPTANCE_INTERFACE_RAW_DIGEST_MISMATCH",
            ):
                builder.load_sources(
                    draft_interface_path=builder.DRAFT_INTERFACE_PATH,
                    acceptance_interface_path=tampered_acceptance,
                )

    def test_guard_set_tamper_fails_closed(self) -> None:
        tampered = copy.deepcopy(self.sources.acceptance_interface)
        tampered["production_semantic_guard_codes_required"] = tampered[
            "production_semantic_guard_codes_required"
        ][:-1]
        with self.assertRaisesRegex(
            ValueError,
            "AUTO_SCHEMA_PROMOTION_ACCEPTANCE_CONTRACT_MISMATCH",
        ):
            builder._validate_acceptance_interface(tampered)

    def test_promoted_byte_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            promoted = Path(temporary)
            for entry in self.sources.promoted_schema_entries:
                source = builder.REPO_ROOT / entry["draft_relative_path"]
                destination = promoted / Path(
                    entry["canonical_relative_path"]
                ).name
                destination.write_bytes(source.read_bytes())
            first = next(iter(self.sources.promoted_schema_entries))
            first_path = promoted / Path(
                first["canonical_relative_path"]
            ).name
            first_path.write_bytes(first_path.read_bytes() + b" ")
            with self.assertRaisesRegex(
                ContractError,
                "AUTO_SCHEMA_PROMOTION_EXACT_BYTES_MISMATCH",
            ):
                validate_promoted_directory(self.sources, promoted)


if __name__ == "__main__":
    unittest.main()
