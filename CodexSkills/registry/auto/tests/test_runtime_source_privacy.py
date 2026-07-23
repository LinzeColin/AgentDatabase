from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from CodexSkills.registry.auto.runtime.core import AutoRuntimeError, SCHEMA_PREFIX, canonical_with_digest
from CodexSkills.registry.auto.runtime.privacy import SecretScanner, validate_public_serialization
from CodexSkills.registry.auto.runtime.queue import PublicSafeQueue
from CodexSkills.registry.auto.runtime.source import (
    SOURCE_POLICY_ID,
    SourceInventoryAdapter,
    SourceScanner,
    assert_source_unchanged,
)
from CodexSkills.governance.tools.canonical_json import canonicalize_object

from runtime_helpers import CANDIDATE_DIGEST, auto_receipt, clock, context, uid


class RuntimeSourcePrivacyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "source"
        self.root.mkdir()
        self.policy = context().contract.shared.policies[SOURCE_POLICY_ID]

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def scanner(self, **kwargs):
        return SourceScanner(self.policy, **kwargs)

    def test_policy_exclusions_are_accounted_and_other_dotfiles_remain(self) -> None:
        (self.root / "visible.txt").write_text("visible", encoding="utf-8")
        (self.root / ".custom").write_text("included", encoding="utf-8")
        git = self.root / ".git" / "objects"
        git.mkdir(parents=True)
        (git / "pack").write_bytes(b"x" * 40)
        cache = self.root / "pkg" / "__pycache__"
        cache.mkdir(parents=True)
        (cache / "x.pyc").write_bytes(b"cache")
        (self.root / ".DS_Store").write_bytes(b"meta")
        report = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.completeness_status, "COMPLETE_AFTER_POLICY_EXCLUSIONS")
        self.assertEqual(
            [item.relative_path for item in report.included_files],
            [".custom", "visible.txt"],
        )
        self.assertEqual([item.reason_code for item in report.exclusions], ["CACHE", "OS_METADATA", "VCS_METADATA"])
        self.assertEqual(report.errors, ())

    def test_codex_system_overlap_is_counted_not_duplicated(self) -> None:
        system = self.root / ".system" / "official"
        system.mkdir(parents=True)
        (system / "SKILL.md").write_text("official", encoding="utf-8")
        (self.root / "user.txt").write_text("user", encoding="utf-8")
        report = self.scanner().scan(self.root, "CODEX", "codex-skills")
        self.assertEqual([item.relative_path for item in report.included_files], ["user.txt"])
        self.assertEqual(report.exclusions[0].reason_code, "SOURCE_OVERLAP")

    def test_vcs_pack_over_size_limit_is_excluded_without_false_incomplete(self) -> None:
        pack = self.root / ".git" / "objects" / "pack"
        pack.mkdir(parents=True)
        target = pack / "large.pack"
        with target.open("wb") as handle:
            handle.truncate(1024)
        report = self.scanner(max_file_bytes=16).scan(self.root, "CLAUDE", "claude-skills")
        self.assertEqual(report.completeness_status, "COMPLETE_AFTER_POLICY_EXCLUSIONS")
        self.assertEqual(report.oversize_blocked_count, 0)
        self.assertEqual(report.excluded_bytes, 1024)

    def test_non_policy_oversize_file_makes_source_incomplete(self) -> None:
        (self.root / "large.bin").write_bytes(b"x" * 17)
        report = self.scanner(max_file_bytes=16).scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.completeness_status, "INCOMPLETE")
        self.assertEqual(report.oversize_blocked_count, 1)
        self.assertEqual(report.errors[0].reason_code, "OVERSIZE_NON_POLICY")

    def test_safe_relative_file_and_directory_symlinks_are_alias_evidence(self) -> None:
        (self.root / "file.txt").write_text("payload", encoding="utf-8")
        directory = self.root / "dir"
        directory.mkdir()
        (directory / "nested.txt").write_text("nested", encoding="utf-8")
        (self.root / "file-link").symlink_to("file.txt")
        (self.root / "dir-link").symlink_to("dir")
        report = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.completeness_status, "COMPLETE_AFTER_POLICY_EXCLUSIONS")
        self.assertEqual([item.alias_path for item in report.aliases], ["dir-link", "file-link"])
        self.assertTrue(all(len(item.content_digest) == 64 for item in report.aliases))

    def test_escape_dangling_and_cycle_symlinks_fail_closed(self) -> None:
        outside = self.root.parent / "outside"
        outside.write_text("outside", encoding="utf-8")
        (self.root / "escape").symlink_to("../outside")
        (self.root / "dangling").symlink_to("missing")
        (self.root / "cycle-a").symlink_to("cycle-b")
        (self.root / "cycle-b").symlink_to("cycle-a")
        report = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.completeness_status, "INCOMPLETE")
        self.assertEqual(dict((item.reason_code, item.count) for item in report.errors)["SYMLINK_UNSAFE"], 4)

    def test_intermediate_symlink_component_cannot_escape_root(self) -> None:
        outside = self.root.parent / "outside-dir"
        outside.mkdir()
        (outside / "secret.txt").write_text("outside", encoding="utf-8")
        (self.root / "pivot").symlink_to(outside)
        (self.root / "alias").symlink_to("pivot/secret.txt")
        report = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.completeness_status, "INCOMPLETE")
        self.assertEqual(dict((item.reason_code, item.count) for item in report.errors)["SYMLINK_UNSAFE"], 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO unsupported")
    def test_special_file_blocks_completeness(self) -> None:
        os.mkfifo(self.root / "pipe")
        report = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.errors[0].reason_code, "SPECIAL_FILE")

    def test_read_failure_is_enumerated_not_silently_skipped(self) -> None:
        (self.root / "file.txt").write_text("payload", encoding="utf-8")
        scanner = self.scanner()
        with mock.patch.object(scanner, "_read_regular", side_effect=AutoRuntimeError("READ_ERROR")):
            report = scanner.scan(self.root, "AGENTS", "agents-skills")
        self.assertEqual(report.completeness_status, "INCOMPLETE")
        self.assertEqual(report.errors[0].reason_code, "READ_ERROR")

    def test_missing_source_fails_before_any_delete_semantics(self) -> None:
        with self.assertRaisesRegex(AutoRuntimeError, "SOURCE_ROOT_MISSING"):
            self.scanner().scan(self.root / "missing", "AGENTS", "agents-skills")

    def test_source_pre_post_snapshot_detects_mutation(self) -> None:
        target = self.root / "file.txt"
        target.write_text("one", encoding="utf-8")
        before = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        target.write_text("two", encoding="utf-8")
        after = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        with self.assertRaisesRegex(AutoRuntimeError, "SOURCE_MUTATED_DURING_RUN"):
            assert_source_unchanged(before, after)

    def test_policy_digest_is_in_tree_domain(self) -> None:
        (self.root / "file.txt").write_text("same", encoding="utf-8")
        first = self.scanner().scan(self.root, "AGENTS", "agents-skills")
        changed_policy = dict(self.policy)
        changed_policy["other_dotfiles_excluded"] = True
        second = SourceScanner(changed_policy).scan(self.root, "AGENTS", "agents-skills")
        self.assertNotEqual(first.included_tree_digest, second.included_tree_digest)

    def test_adapter_emits_schema_valid_public_inventory_and_coverage(self) -> None:
        (self.root / "SKILL.md").write_text("# Demo", encoding="utf-8")
        adapter = SourceInventoryAdapter(
            self.scanner(), context().contract, CANDIDATE_DIGEST, clock()
        )
        observed = adapter.observe(
            self.root,
            "AGENTS",
            "agents-skills",
            entropy=(8).to_bytes(10, "big"),
        )
        self.assertEqual(observed.inventory["completeness_status"], "COMPLETE_AFTER_POLICY_EXCLUSIONS")
        self.assertEqual(observed.coverage_receipt["coverage_state"], "COVERED")
        serialized = canonicalize_object(observed.inventory)
        self.assertNotIn(str(self.root).encode("utf-8"), serialized)

    def test_incomplete_inventory_projects_unknown_not_false_covered(self) -> None:
        (self.root / "large.bin").write_bytes(b"x" * 17)
        adapter = SourceInventoryAdapter(
            self.scanner(max_file_bytes=16),
            context().contract,
            CANDIDATE_DIGEST,
            clock(),
        )
        observed = adapter.observe(
            self.root,
            "AGENTS",
            "agents-skills",
            entropy=(9).to_bytes(10, "big"),
        )
        self.assertEqual(observed.coverage_receipt["coverage_state"], "UNKNOWN")
        self.assertEqual(observed.coverage_receipt["reason_codes"], ["INVENTORY_INCOMPLETE"])

    def test_secret_scanner_crosses_chunk_boundary_and_never_returns_value(self) -> None:
        target = self.root / "large.bin"
        target.write_bytes(b"x" * 61 + b" " + b"ghp_" + b"A" * 24)
        hits = SecretScanner(chunk_bytes=64, overlap_bytes=32).scan_file(target, "skill/large.bin")
        self.assertEqual([(item.path_ref, item.reason_code) for item in hits], [("skill/large.bin", "GITHUB_TOKEN")])
        self.assertNotIn("AAAA", repr(hits))

    def test_public_serialization_rejects_forbidden_extra_field(self) -> None:
        receipt = auto_receipt()
        receipt["command"] = "forbidden"
        receipt = canonical_with_digest(receipt, "receipt_digest")
        with self.assertRaisesRegex(AutoRuntimeError, "PUBLIC_SERIALIZATION_GATE_FAILED"):
            validate_public_serialization(
                canonicalize_object(receipt),
                context().contract,
                SCHEMA_PREFIX + "auto-receipt:v2",
                CANDIDATE_DIGEST,
            )

    def test_public_queue_is_idempotent_and_detects_uid_digest_corruption(self) -> None:
        queue_root = self.root.parent / "queue"
        queue_root.mkdir(mode=0o700)
        queue = PublicSafeQueue(queue_root, context().contract, CANDIDATE_DIGEST, clock())
        first_artifact = auto_receipt(1)
        kwargs = dict(
            auto_transaction_uid=uid("atx", 1),
            lane="REGISTRY",
            artifact_schema_id=SCHEMA_PREFIX + "auto-receipt:v2",
            artifact_uid=first_artifact["receipt_uid"],
            artifact_repo_path="CodexSkills/governance/auto-receipts/receipt.json",
            artifact=first_artifact,
            entropy=(7).to_bytes(10, "big"),
        )
        self.assertEqual(queue.enqueue(**kwargs).status, "ENQUEUED")
        self.assertEqual(queue.enqueue(**kwargs).status, "IDEMPOTENT")
        envelope_uid = queue.enqueue(**kwargs).envelope["envelope_uid"]
        with self.assertRaisesRegex(AutoRuntimeError, "QUEUE_SETTLEMENT_REMOTE_READBACK_REQUIRED"):
            queue.mark_settled(
                envelope_uid,
                remote_head="sha1:" + "1" * 40,
                observed_artifact_digest=first_artifact["receipt_digest"],
                remote_readback_verified=False,
            )
        settled = queue.mark_settled(
            envelope_uid,
            remote_head="sha1:" + "1" * 40,
            observed_artifact_digest=first_artifact["receipt_digest"],
            remote_readback_verified=True,
        )
        self.assertEqual(settled["queue_state"], "SETTLED")
        second = auto_receipt(2)
        kwargs["artifact_uid"] = second["receipt_uid"]
        kwargs["artifact"] = second
        with self.assertRaisesRegex(AutoRuntimeError, "QUEUE_UID_DIGEST_CORRUPTION"):
            queue.enqueue(**kwargs)


if __name__ == "__main__":
    unittest.main()
