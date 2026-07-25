from __future__ import annotations

import copy
import datetime as dt
import hashlib
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from unittest import mock

from CodexSkills.registry.auto.runtime.bootstrap import BootstrapContext
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError
from CodexSkills.registry.auto.runtime.core import canonical_with_digest
from CodexSkills.registry.auto.runtime.publication import (
    PublicationArtifact,
)
from CodexSkills.registry.auto.runtime.repository_binding import (
    REMOTE_URL,
    RepositoryBindingInputs,
    RepositoryBindingPermit,
    authorize_repository_binding,
    probe_repository_binding,
    validate_run_log_transaction,
    validate_delete_prerequisites,
)
from CodexSkills.registry.auto.runtime.run_log_writer import (
    DailyRunShardWriter,
)

from runtime_helpers import (
    CANDIDATE_DIGEST,
    final_contract,
    repository_control_trust,
    synthetic_repository_bound_context,
    trust,
    uid,
)
from test_runtime_run_log_writer import event
from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
)


class RuntimeRepositoryBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "reference"
        self.scratch = self.root / "scratch"
        self.state = self.root / "state"
        self.repo.mkdir()
        self.scratch.mkdir()
        for command in (
            ("git", "init", "--initial-branch=main"),
            ("git", "config", "user.name", "SkillOps Test"),
            (
                "git",
                "config",
                "user.email",
                "skillops@example.invalid",
            ),
            ("git", "commit", "--allow-empty", "-m", "reference"),
            ("git", "remote", "add", "origin", REMOTE_URL),
        ):
            completed = subprocess.run(
                command,
                cwd=str(self.repo),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if completed.returncode != 0:
                self.fail(
                    completed.stderr.decode(
                        "utf-8",
                        errors="replace",
                    )
                )
        head = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=str(self.repo),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.decode("ascii").strip()
        self.expected_head = "sha1:" + head
        self.inputs = RepositoryBindingInputs(
            self.repo,
            self.scratch,
            self.state,
            self.expected_head,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def context(
        *,
        integration=True,
        repository_bound=True,
        resolver=True,
        canonical=False,
    ) -> BootstrapContext:
        return BootstrapContext(
            trust(),
            repository_control_trust(),
            final_contract(),
            MappingProxyType({}),
            MappingProxyType(
                {
                    "transition_contract": {
                        "auto_runtime_integration_complete": True,
                        "runtime_state_write_permitted": True,
                        "runtime_shard_writer_integration_complete": True,
                        "publisher_v2_runtime_integration_complete": True,
                        "repository_binding_integration_complete": (
                            integration
                        ),
                        "repository_bound": repository_bound,
                        "bound_reference_resolver_gate_satisfied": (
                            resolver
                        ),
                        "canonical_publication_permitted": canonical,
                    }
                }
            ),
        )

    def test_readonly_probe_binds_exact_logical_repository(self) -> None:
        observed = probe_repository_binding(self.inputs)
        self.assertEqual(
            observed.repository_id,
            "github.com/LinzeColin/AgentDatabase",
        )
        self.assertEqual(observed.fetch_url, REMOTE_URL)
        self.assertEqual(observed.push_url, REMOTE_URL)
        self.assertEqual(observed.branch, "main")
        self.assertEqual(observed.remote_ref, "refs/heads/main")
        self.assertEqual(observed.push_refspec, "HEAD:main")
        self.assertEqual(observed.object_format, "sha1")
        self.assertTrue(observed.reference_tree_clean)
        self.assertFalse(observed.network_accessed)
        self.assertFalse(self.state.exists())

    def test_url_head_dirty_symlink_and_containment_drift_fail_closed(
        self,
    ) -> None:
        subprocess.run(
            ("git", "remote", "set-url", "origin", "https://example.invalid/x"),
            cwd=str(self.repo),
            check=True,
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_REMOTE_URL_MISMATCH$",
        ):
            probe_repository_binding(self.inputs)
        subprocess.run(
            ("git", "remote", "set-url", "origin", REMOTE_URL),
            cwd=str(self.repo),
            check=True,
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_EXPECTED_HEAD_MISMATCH$",
        ):
            probe_repository_binding(
                replace(
                    self.inputs,
                    expected_remote_head="sha1:" + ("0" * 40),
                )
            )
        (self.repo / "untracked").write_text("drift", encoding="utf-8")
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_REFERENCE_TREE_DIRTY$",
        ):
            probe_repository_binding(self.inputs)
        (self.repo / "untracked").unlink()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_ROOT_CONTAINMENT_INVALID$",
        ):
            probe_repository_binding(
                replace(
                    self.inputs,
                    state_root=self.repo / "state",
                )
            )
        symlink = self.root / "reference-link"
        symlink.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_REPO_ROOT_NOT_REAL_DIRECTORY$",
        ):
            probe_repository_binding(
                replace(self.inputs, repo_root=symlink)
            )

    def test_control_and_resolver_gates_precede_every_git_probe(
        self,
    ) -> None:
        cases = (
            (
                self.context(integration=False),
                "RUNTIME_REPOSITORY_BINDING_CONTROL_SYNC_REQUIRED",
            ),
            (
                self.context(repository_bound=False),
                "REPOSITORY_BINDING_NOT_AUTHORIZED",
            ),
            (
                self.context(resolver=False),
                "BOUND_REFERENCE_RESOLVER_NOT_SATISFIED",
            ),
        )
        with mock.patch(
            "CodexSkills.registry.auto.runtime.repository_binding."
            "_run_git_readonly"
        ) as git_read:
            for context, code in cases:
                with self.subTest(code=code), self.assertRaisesRegex(
                    AutoRuntimeError,
                    "^" + code + "$",
                ):
                    authorize_repository_binding(
                        context,
                        self.inputs,
                    )
            git_read.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_caller_cannot_construct_or_rebind_permit(self) -> None:
        context = self.context()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_PERMIT_CONSTRUCTION_FORBIDDEN$",
        ):
            RepositoryBindingPermit(
                object(),
                context,
                probe_repository_binding(self.inputs),
            )
        permit = authorize_repository_binding(context, self.inputs)
        other = self.context()
        from CodexSkills.registry.auto.runtime.repository_binding import (
            assert_repository_binding_permit,
        )

        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_PERMIT_REQUIRED$",
        ):
            assert_repository_binding_permit(
                permit,
                other,
                self.expected_head,
            )

    def test_exact_writer_artifact_closure_is_accepted(self) -> None:
        context = synthetic_repository_bound_context()
        permit = authorize_repository_binding(context, self.inputs)
        writer = DailyRunShardWriter(
            final_contract(),
            CANDIDATE_DIGEST,
        )
        plan = writer.plan(
            [
                event(
                    1,
                    "2026-07-22T23:00:00.000000Z",
                )
            ],
            manifest_uid=uid("drm", 1),
            auto_transaction_uid=uid("atx", 1),
            publication_transaction_at=dt.datetime(
                2026,
                7,
                23,
                0,
                0,
                tzinfo=dt.timezone.utc,
            ),
        )
        artifacts = tuple(
            PublicationArtifact(
                artifact.relative_path,
                artifact.payload,
                lane="RUN_LOG",
                schema_id=artifact.schema_id,
                artifact_uid=uid("art", number),
                operation="PUT",
                serialization=artifact.serialization,
                record_count=artifact.record_count,
            )
            for number, artifact in enumerate(plan.artifacts, 1)
        )
        closure = validate_run_log_transaction(
            permit,
            context,
            self.expected_head,
            artifacts,
        )
        self.assertEqual(closure["local_date"], "2026-07-23")
        self.assertEqual(closure["put_part_numbers"], (1,))
        self.assertEqual(closure["delete_part_numbers"], ())
        self.assertEqual(
            closure["artifact_paths"],
            tuple(
                sorted(
                    artifact.relative_path for artifact in artifacts
                )
            ),
        )

        part = next(
            item
            for item in artifacts
            if "/part-" in item.relative_path
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_PART_INDEX_PUT_SET_MISMATCH$",
        ):
            validate_run_log_transaction(
                permit,
                context,
                self.expected_head,
                tuple(
                    item
                    for item in artifacts
                    if "/index-" not in item.relative_path
                ),
            )
        escaped = replace(
            part,
            relative_path="OpenAIDatabase/data/run_logs/other.jsonl",
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^REPOSITORY_BINDING_RUN_LOG_PATH_INVALID$",
        ):
            validate_run_log_transaction(
                permit,
                context,
                self.expected_head,
                (escaped,),
            )

    def test_bound_event_gate_is_not_inferred_from_event_fields(
        self,
    ) -> None:
        context = self.context(resolver=False)
        with mock.patch(
            "CodexSkills.registry.auto.runtime.repository_binding."
            "probe_repository_binding"
        ) as probe:
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "^BOUND_REFERENCE_RESOLVER_NOT_SATISFIED$",
            ):
                authorize_repository_binding(context, self.inputs)
            probe.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_retention_delete_closes_prior_part_index_receipt_and_manifest(
        self,
    ) -> None:
        context = synthetic_repository_bound_context()
        permit = authorize_repository_binding(context, self.inputs)
        writer = DailyRunShardWriter(
            final_contract(),
            CANDIDATE_DIGEST,
        )
        plan = writer.plan(
            [event(1, "2026-07-22T23:00:00.000000Z")],
            manifest_uid=uid("drm", 1),
            auto_transaction_uid=uid("atx", 1),
            publication_transaction_at=dt.datetime(
                2026,
                7,
                23,
                0,
                0,
                tzinfo=dt.timezone.utc,
            ),
        )
        part_artifact = next(
            item for item in plan.artifacts if "/part-" in item.relative_path
        )
        index_artifact = next(
            item for item in plan.artifacts if "/index-" in item.relative_path
        )
        prior_manifest_artifact = next(
            item
            for item in plan.artifacts
            if "/manifest-" in item.relative_path
        )
        prior = copy.deepcopy(dict(plan.manifest))
        prior_part = prior["parts"][0]
        retention_not_before = dt.datetime.strptime(
            prior_part["retention_not_before"],
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(tzinfo=dt.timezone.utc)
        executed = retention_not_before + dt.timedelta(seconds=1)
        deadline = retention_not_before + dt.timedelta(hours=24)

        def stamp(value: dt.datetime) -> str:
            return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        prefix = (
            "OpenAIDatabase/data/run_logs/skills_runs/2026/07/23"
        )
        receipt_path = prefix + "/retention-receipt-0001.json"
        receipt = canonical_with_digest(
            {
                "schema_version": (
                    "urn:linzecolin:agentdatabase:skillops:"
                    "schema:retention-receipt:v3"
                ),
                "protocol_revision": (
                    "urn:linzecolin:agentdatabase:skillops:"
                    "protocol:cross-pack:v1"
                ),
                "bundle_digest": CANDIDATE_DIGEST,
                "receipt_uid": uid("rtr", 1),
                "retention_action_uid": uid("rta", 1),
                "auto_transaction_uid": uid("atx", 2),
                "executed_at": stamp(executed),
                "cutoff_at": stamp(retention_not_before),
                "clock_basis": "UTC_WALL_CLOCK",
                "scope": "GIT_CURRENT_TREE",
                "action": "PRUNE_CURRENT_TREE",
                "retention_policy_id": (
                    "urn:linzecolin:agentdatabase:skillops:"
                    "policy:retention:v3"
                ),
                "policy_snapshot_digest": "a" * 64,
                "selected_count": 1,
                "selected_bytes": prior_part["shard_bytes"],
                "affected_count": 1,
                "affected_bytes": prior_part["shard_bytes"],
                "protected_candidate_count": 0,
                "legacy_candidate_count": 0,
                "reprojection_status": "NOT_APPLICABLE",
                "offline_duration_seconds": 0,
                "ttl_breach": False,
                "history_rewrite_performed": False,
                "hard_delete_claimed": False,
                "evidence_digest": "b" * 64,
                "affected_public_artifacts": [
                    {
                        "artifact_repo_path": (
                            prefix + "/part-0001.jsonl"
                        ),
                        "artifact_schema_id": (
                            "urn:linzecolin:agentdatabase:skillops:"
                            "schema:public-run-event:v2"
                        ),
                        "artifact_serialization": (
                            "RFC8785_JCS_PER_LINE_LF"
                        ),
                        "prior_artifact_digest": prior_part[
                            "shard_digest"
                        ],
                        "prior_artifact_bytes": prior_part[
                            "shard_bytes"
                        ],
                        "prior_record_count": prior_part[
                            "record_count"
                        ],
                        "first_published_at": prior_part[
                            "first_published_at"
                        ],
                        "retention_not_before": prior_part[
                            "retention_not_before"
                        ],
                        "prune_deadline_at": stamp(deadline),
                        "retained_index_path": (
                            prefix + "/index-0001.jsonl"
                        ),
                        "retained_index_digest": prior_part[
                            "index_digest"
                        ],
                        "prior_daily_manifest_digest": prior[
                            "manifest_digest"
                        ],
                    }
                ],
                "prune_deadline_breached": False,
                "receipt_digest": "0" * 64,
            },
            "receipt_digest",
        )
        receipt_raw = canonicalize_object(receipt)

        current = copy.deepcopy(prior)
        current.update(
            {
                "manifest_uid": uid("drm", 2),
                "manifest_revision": 2,
                "previous_manifest_digest": prior[
                    "manifest_digest"
                ],
                "auto_transaction_uid": uid("atx", 2),
                "publication_transaction_at": stamp(executed),
                "active_part_count": 0,
                "pruned_part_count": 1,
                "active_shard_bytes": 0,
                "active_record_count": 0,
            }
        )
        current_part = current["parts"][0]
        current_part.update(
            {
                "state": "PRUNED",
                "retention_receipt_path": receipt_path,
                "retention_receipt_uid": receipt["receipt_uid"],
                "retention_receipt_digest": receipt[
                    "receipt_digest"
                ],
                "pruned_at": receipt["executed_at"],
            }
        )
        current["manifest_digest"] = "0" * 64
        current = canonical_with_digest(current, "manifest_digest")
        current_raw = canonicalize_object(current)
        manifest_path = prefix + "/manifest-0002.json"
        deletion = PublicationArtifact(
            prefix + "/part-0001.jsonl",
            None,
            lane="RUN_LOG",
            schema_id=part_artifact.schema_id,
            artifact_uid=uid("art", 1),
            operation="DELETE",
            prior_serialization=part_artifact.serialization,
            prior_digest=prior_part["shard_digest"],
            prior_bytes=prior_part["shard_bytes"],
            prior_record_count=prior_part["record_count"],
        )
        artifacts = tuple(
            sorted(
                (
                    PublicationArtifact(
                        manifest_path,
                        current_raw,
                        lane="RUN_LOG",
                        schema_id=prior_manifest_artifact.schema_id,
                        artifact_uid=uid("art", 2),
                        operation="PUT",
                        serialization=(
                            prior_manifest_artifact.serialization
                        ),
                        record_count=1,
                    ),
                    deletion,
                    PublicationArtifact(
                        receipt_path,
                        receipt_raw,
                        lane="RUN_LOG",
                        schema_id=receipt["schema_version"],
                        artifact_uid=uid("art", 3),
                        operation="PUT",
                        serialization="RFC8785_JCS_OBJECT",
                        record_count=1,
                    ),
                ),
                key=lambda item: item.relative_path,
            )
        )
        closure = validate_run_log_transaction(
            permit,
            context,
            self.expected_head,
            artifacts,
        )
        self.assertEqual(closure["delete_part_numbers"], (1,))
        physical = {
            prefix + "/manifest-0001.json": (
                prior_manifest_artifact.payload
            ),
            prefix + "/index-0001.jsonl": index_artifact.payload,
        }
        validate_delete_prerequisites(
            permit,
            context,
            self.expected_head,
            closure,
            artifacts,
            lambda _worktree, path: physical[path],
            Path("/virtual/worktree"),
        )
        physical[prefix + "/index-0001.jsonl"] = b"{}\n"
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "REPOSITORY_BINDING_RETAINED_INDEX_MISMATCH|"
            "PUBLIC_JSONL_LINE_INVALID",
        ):
            validate_delete_prerequisites(
                permit,
                context,
                self.expected_head,
                closure,
                artifacts,
                lambda _worktree, path: physical[path],
                Path("/virtual/worktree"),
            )


if __name__ == "__main__":
    unittest.main()
