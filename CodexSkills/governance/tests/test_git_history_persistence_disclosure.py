"""Regression gates for Mechanism M-064 Git-history disclosure."""

from __future__ import annotations

import copy
import inspect
import unittest

from CodexSkills.governance.retention import git_history_disclosure as policy
from CodexSkills.governance.retention.git_history_disclosure import (
    GitHistoryDisclosureError,
    build_disclosure,
    render_disclosure_markdown,
    validate_disclosure,
    validate_disclosure_markdown,
    validate_disclosure_surface,
)
from CodexSkills.governance.tools import (
    build_git_history_persistence_disclosure as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractError,
    validate_instance,
)


class GitHistoryPersistenceDisclosureTests(unittest.TestCase):
    """M-064 must disclose persistence and reject hard-erasure claims."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = builder._documents()
        cls.disclosure = parse_json_bytes(
            cls.documents[builder.DISCLOSURE_PATH]
        )
        cls.readiness = parse_json_bytes(
            cls.documents[builder.READINESS_PATH]
        )
        cls.markdown = cls.documents[builder.DISCLOSURE_MARKDOWN_PATH]

    def test_01_builder_is_byte_equivalent_and_predecessor_is_exact(
        self,
    ) -> None:
        builder._check()
        predecessor = builder._validate_predecessor()
        self.assertEqual(
            predecessor["artifact_digest"],
            builder.M063_READINESS_SELF_DIGEST,
        )
        self.assertEqual(
            predecessor["next_phase"],
            "MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE",
        )
        self.assertEqual(
            self.readiness["status"],
            (
                "DRAFT_NON_ACTIVE_"
                "GIT_HISTORY_PERSISTENCE_DISCLOSURE_READY"
            ),
        )
        self.assertEqual(
            self.readiness["next_phase"],
            "MECHANISM_READ_ONLY_MIGRATION_CUTOVER",
        )
        self.assertEqual(
            self.readiness["task_contract"]["completed_task_ids"],
            ["M-064"],
        )
        self.assertEqual(
            self.readiness["task_contract"]["pending_task_ids"],
            ["M-065"],
        )
        self.assertEqual(self.readiness["schema_closure_count"], 33)
        self.assertEqual(self.readiness["policy_count"], 5)

    def test_02_structured_disclosure_and_bilingual_markdown_are_exact(
        self,
    ) -> None:
        self.assertEqual(self.disclosure, build_disclosure())
        self.assertEqual(self.markdown, render_disclosure_markdown())
        validate_disclosure(self.disclosure)
        validate_disclosure_markdown(self.markdown)
        text = self.markdown.decode("utf-8")
        for required in policy.REQUIRED_DISCLOSURE_TEXT:
            self.assertEqual(text.count(required), 1)
        for heading in policy.REQUIRED_MARKDOWN_HEADINGS:
            self.assertEqual(text.count(heading), 1)

    def test_03_retention_scope_is_current_tree_only(self) -> None:
        active = self.disclosure["active_tree_contract"]
        self.assertEqual(active["scope"], "GIT_CURRENT_TREE_ONLY")
        self.assertEqual(
            active["full_fidelity_retention_seconds"],
            365 * 24 * 60 * 60,
        )
        self.assertEqual(
            active["eligibility_condition"],
            "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE",
        )
        self.assertEqual(
            active["ordinary_removal_effect"],
            "REMOVES_EXACT_BYTES_FROM_SUCCESSOR_CURRENT_TREE_ONLY",
        )

    def test_04_receipt_never_proves_hard_erasure(self) -> None:
        receipt = self.disclosure["receipt_contract"]
        self.assertTrue(
            receipt["proves_current_tree_transition_only"]
        )
        self.assertFalse(receipt["proves_git_history_erasure"])
        self.assertFalse(receipt["proves_other_copy_erasure"])
        self.assertFalse(receipt["proves_irrecoverability"])

    def test_05_every_copy_class_is_disclosed_as_persistent(self) -> None:
        persistence = self.disclosure["persistence_contract"]
        for field in (
            "git_history_may_retain_bytes_indefinitely",
            "forks_may_retain_bytes_indefinitely",
            "clones_may_retain_bytes_indefinitely",
            "caches_may_retain_bytes_indefinitely",
            "archives_may_retain_bytes_indefinitely",
            "provider_backups_may_retain_bytes_indefinitely",
        ):
            self.assertTrue(persistence[field], field)
        self.assertFalse(
            persistence["third_party_copy_deletion_guaranteed"]
        )

    def test_06_future_hard_erasure_is_separate_major_design(self) -> None:
        hard = self.disclosure["hard_erasure_contract"]
        self.assertFalse(hard["hard_deletion_claimed"])
        self.assertFalse(hard["automatic_history_rewrite_permitted"])
        self.assertFalse(hard["repository_rotation_performed"])
        self.assertFalse(hard["private_storage_rotation_performed"])
        self.assertEqual(
            hard["future_design_required"],
            (
                "OWNER_AUTHORIZED_MAJOR_"
                "REPOSITORY_ROTATION_OR_PRIVATE_STORAGE"
            ),
        )

    def test_07_english_positive_hard_erasure_claims_fail_closed(
        self,
    ) -> None:
        claims = (
            b"Hard deletion is complete.\n",
            b"The data has been permanently deleted.\n",
            b"The bytes were erased from Git history.\n",
            b"The item was removed from all backups.\n",
            b"The artifact is irrecoverable.\n",
            b"The record cannot be recovered.\n",
        )
        for index, raw in enumerate(claims):
            with self.subTest(index=index):
                with self.assertRaises(GitHistoryDisclosureError):
                    validate_disclosure_surface(
                        f"docs/claim-{index}.md",
                        raw,
                    )

    def test_08_chinese_positive_hard_erasure_claims_fail_closed(
        self,
    ) -> None:
        claims = (
            "数据已永久删除。\n",
            "永久删除已完成。\n",
            "数据已彻底删除。\n",
            "数据已从 Git 历史中清除。\n",
            "该记录无法恢复。\n",
            "该记录不可恢复。\n",
        )
        for index, claim in enumerate(claims):
            with self.subTest(index=index):
                with self.assertRaises(GitHistoryDisclosureError):
                    validate_disclosure_surface(
                        f"docs/zh-claim-{index}.md",
                        claim.encode("utf-8"),
                    )

    def test_09_truthful_negation_is_not_a_false_positive(self) -> None:
        safe = (
            "This receipt does not prove permanent deletion and never "
            "claims hard deletion.\n"
            "本 receipt 不证明数据不可恢复，也不声称永久删除。\n"
        ).encode("utf-8")
        validate_disclosure_surface("docs/safe.md", safe)
        validate_disclosure_markdown(self.markdown)

    def test_10_self_consistent_text_weakening_still_fails_semantics(
        self,
    ) -> None:
        altered = copy.deepcopy(self.disclosure)
        altered["disclosures"]["user_en"] = (
            "The receipt proves a transition."
        )
        altered["artifact_digest"] = canonical_digest(
            altered,
            policy.DISCLOSURE_SELF_POINTER,
        )
        with self.assertRaisesRegex(
            GitHistoryDisclosureError,
            "DISCLOSURE_TEXT_INVALID",
        ):
            validate_disclosure(altered)

    def test_11_schema_const_rejects_self_consistent_semantic_drift(
        self,
    ) -> None:
        acceptance = builder.load_au040_acceptance()
        disclosure_schema = builder.build_disclosure_schema(
            self.disclosure
        )
        contract = builder._extend_bundle(
            acceptance.bundle,
            {policy.DISCLOSURE_SCHEMA_ID: disclosure_schema},
            {
                policy.DISCLOSURE_SCHEMA_ID:
                policy.DISCLOSURE_SELF_POINTER
            },
        )
        altered = copy.deepcopy(self.disclosure)
        altered["persistence_contract"][
            "git_history_may_retain_bytes_indefinitely"
        ] = False
        altered["artifact_digest"] = canonical_digest(
            altered,
            policy.DISCLOSURE_SELF_POINTER,
        )
        with self.assertRaisesRegex(
            ContractError,
            "SCHEMA_VALIDATION_FAILED",
        ):
            validate_instance(
                contract,
                altered,
                policy.DISCLOSURE_SCHEMA_ID,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
                public=True,
            )

    def test_12_markdown_omission_fails_closed(self) -> None:
        altered = self.markdown.replace(
            policy.USER_DISCLOSURE_ZH.encode("utf-8"),
            b"",
        )
        with self.assertRaisesRegex(
            GitHistoryDisclosureError,
            "DISCLOSURE_MARKDOWN_TEXT_INVALID",
        ):
            validate_disclosure_markdown(altered)

    def test_13_declared_user_surfaces_are_clean(self) -> None:
        paths = builder._scan_declared_surfaces(self.markdown)
        declared = self.readiness["surface_guard"][
            "declared_surface_roots"
        ]
        self.assertEqual(
            [item["canonical_path"] for item in declared],
            list(builder.DISCLOSURE_SURFACE_ROOTS),
        )
        self.assertGreaterEqual(len(paths), 21)
        self.assertIn(builder.CANONICAL_DISCLOSURE_PATH, paths)
        self.assertTrue(
            all(item["glob"] == "**/*.md" for item in declared)
        )
        self.assertFalse(
            self.readiness["surface_guard"][
                "positive_hard_erasure_claims_permitted"
            ]
        )
        self.assertEqual(
            self.readiness["surface_guard"][
                "ui_runtime_integration_status"
            ],
            "NOT_BOUND",
        )

    def test_14_surface_framing_and_path_escape_fail_closed(self) -> None:
        for path, raw in (
            ("../outside.md", b"safe\n"),
            ("docs\\claim.md", b"safe\n"),
            ("docs/claim.md", b"\xef\xbb\xbfsafe\n"),
            ("docs/claim.md", b"safe\r\n"),
            ("docs/claim.md", b"safe\x00\n"),
        ):
            with self.subTest(path=path, raw=raw):
                with self.assertRaises(GitHistoryDisclosureError):
                    validate_disclosure_surface(path, raw)

    def test_15_guard_has_no_mutable_or_external_capability(self) -> None:
        source = inspect.getsource(policy)
        for forbidden in (
            "from pathlib",
            "import os",
            "import subprocess",
            "import socket",
            "import urllib",
            "requests.",
            "Path(",
            "open(",
            "unlink(",
            "write_bytes(",
            "rmtree(",
        ):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("CodexSkills.registry.auto.runtime", source)
        self.assertFalse(
            self.readiness["nonmutation"][
                "git_history_rewrite_performed"
            ]
        )
        self.assertFalse(
            self.readiness["nonmutation"][
                "repository_rotation_performed"
            ]
        )
        self.assertFalse(
            self.readiness["nonmutation"][
                "canonical_publication_permitted"
            ]
        )


if __name__ == "__main__":
    unittest.main()
