from __future__ import annotations

import datetime as dt
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.registry.auto.runtime.bootstrap import BootstrapContext
from CodexSkills.registry.auto.runtime.core import (
    AutoRuntimeError,
    canonical_with_digest,
)
from CodexSkills.registry.auto.runtime.publication import (
    GitBackend,
    PhysicalPublisher,
    PublicationArtifact,
    PublicationRequest,
    RemoteReadback,
    SubprocessGitBackend,
    build_publication_manifest_v2_payload,
)
from CodexSkills.registry.auto.runtime.run_log_writer import (
    DailyRunShardWriter,
)

from runtime_helpers import (
    CANDIDATE_DIGEST,
    control_trust,
    final_contract,
    trust,
    uid,
)
from test_runtime_run_log_writer import event


class ExactLock:
    def __init__(self) -> None:
        self.calls = 0

    def assert_owned(self, owner_run_uid, expected_digest):
        self.calls += 1
        if (
            owner_run_uid != uid("atx", 1)
            or expected_digest != "e" * 64
        ):
            raise AutoRuntimeError("LOCK_OWNERSHIP_MISMATCH")
        return {
            "owner_run_uid": owner_run_uid,
            "state_digest": expected_digest,
        }


class InMemoryGitBackend(GitBackend):
    def __init__(self, initial=None) -> None:
        self.head = "sha1:" + ("a" * 40)
        self.commit_id = "sha1:" + ("b" * 40)
        self.files = dict(initial or {})
        self.artifacts = ()
        self.create_calls = 0
        self.write_calls = 0
        self.cleaned = False

    def remote_head(self):
        return self.head

    def create_worktree(self, expected_head, transaction_uid):
        self.create_calls += 1
        self.expected_head = expected_head
        return Path("/virtual/publication-v2")

    def read_artifact(self, worktree, relative_path):
        try:
            return self.files[relative_path]
        except KeyError as exc:
            raise AutoRuntimeError(
                "PUBLICATION_PRIOR_ARTIFACT_STAT_FAILED"
            ) from exc

    def write_artifacts(self, worktree, artifacts):
        self.write_calls += 1
        self.artifacts = tuple(artifacts)
        for artifact in artifacts:
            if artifact.operation == "DELETE":
                del self.files[artifact.relative_path]
            else:
                assert artifact.payload is not None
                self.files[artifact.relative_path] = artifact.payload

    def changed_paths(self, worktree):
        return tuple(
            sorted(
                artifact.relative_path
                for artifact in self.artifacts
            )
        )

    def commit(self, worktree, message, paths):
        self.message = message
        return self.commit_id

    def push(self, worktree, expected_head):
        if self.head != expected_head:
            raise AutoRuntimeError("REMOTE_HEAD_CHANGED")
        self.head = self.commit_id

    def readback(self, commit, artifacts):
        observed = {}
        for artifact in artifacts:
            if artifact.operation == "DELETE":
                if artifact.relative_path in self.files:
                    return RemoteReadback(commit, observed, False)
                observed[artifact.relative_path] = (
                    artifact.prior_digest
                )
                continue
            if self.files.get(artifact.relative_path) != artifact.payload:
                return RemoteReadback(commit, observed, False)
            assert artifact.payload is not None
            observed[artifact.relative_path] = hashlib.sha256(
                artifact.payload
            ).hexdigest()
        return RemoteReadback(commit, observed, True)

    def find_transaction(self, transaction_uid, expected_parent):
        return None

    def cleanup(self, worktree):
        self.cleaned = True


class RuntimePublicationV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = final_contract()
        self.lock = ExactLock()
        writer = DailyRunShardWriter(
            self.contract,
            CANDIDATE_DIGEST,
        )
        self.write_plan = writer.plan(
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
        self.artifacts = tuple(
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
            for number, artifact in enumerate(
                self.write_plan.artifacts,
                1,
            )
        )

    def context(
        self,
        *,
        publisher=True,
        repository_bound=True,
        canonical=True,
    ) -> BootstrapContext:
        return BootstrapContext(
            trust(mode="ACTIVE"),
            control_trust(),
            self.contract,
            MappingProxyType({}),
            MappingProxyType(
                {
                    "transition_contract": {
                        "auto_runtime_integration_complete": True,
                        "runtime_shard_writer_integration_complete": True,
                        "publisher_v2_runtime_integration_complete": (
                            publisher
                        ),
                        "repository_bound": repository_bound,
                        "canonical_publication_permitted": canonical,
                    }
                }
            ),
        )

    def manifest(self, artifacts=None) -> bytes:
        return build_publication_manifest_v2_payload(
            contract=self.contract,
            bundle_digest=CANDIDATE_DIGEST,
            manifest_uid=uid("pub", 1),
            auto_transaction_uid=uid("atx", 1),
            trigger_kind="MANUAL",
            created_at="2026-07-23T00:00:00.000000Z",
            mechanism_srv_revision="v0.0.0.2",
            expected_remote_head="sha1:" + ("a" * 40),
            artifacts=artifacts or self.artifacts,
            lane_transaction_uids={
                "RUN_LOG": uid("ltx", 1),
            },
            source_watermark_refs={
                "RUN_LOG": "run-log-daily",
            },
            lock_owner_run_uid=uid("atx", 1),
            lock_state_digest="e" * 64,
        )

    def request(self, *, artifacts=None, manifest=None):
        selected = artifacts or self.artifacts
        return PublicationRequest(
            auto_transaction_uid=uid("atx", 1),
            authority="ACTIVE_RUNTIME",
            trust_mode="ACTIVE",
            expected_remote_head="sha1:" + ("a" * 40),
            commit_message="Publish SkillOps daily run log",
            artifacts=selected,
            lock_owner_run_uid=uid("atx", 1),
            lock_state_digest="e" * 64,
            publication_manifest_payload=(
                self.manifest(selected)
                if manifest is None
                else manifest
            ),
        )

    def publisher(self, backend, *, context=None):
        return PhysicalPublisher(
            self.contract,
            CANDIDATE_DIGEST,
            backend,
            trusted_mode="ACTIVE",
            lock=self.lock,
            runtime_context=context,
        )

    def test_manifest_closes_exact_writer_bytes_and_gate_evidence(
        self,
    ) -> None:
        raw = self.manifest()
        self.assertFalse(raw.endswith(b"\n"))
        manifest = parse_json_bytes(raw)
        self.assertEqual(canonicalize_object(manifest), raw)
        descriptors = manifest["lane_manifests"][0]["artifacts"]
        self.assertEqual(
            [item["artifact_repo_path"] for item in descriptors],
            [item.relative_path for item in self.artifacts],
        )
        for descriptor, artifact in zip(
            descriptors,
            self.artifacts,
        ):
            assert artifact.payload is not None
            self.assertEqual(
                descriptor["artifact_digest"],
                hashlib.sha256(artifact.payload).hexdigest(),
            )
            self.assertEqual(
                descriptor["artifact_bytes"],
                len(artifact.payload),
            )
            self.assertEqual(
                descriptor["artifact_record_count"],
                artifact.record_count,
            )
        self.assertEqual(
            [gate["gate_code"] for gate in manifest["shared_gates"]],
            [
                "BUNDLE_DIGEST",
                "EXPECTED_REMOTE_HEAD",
                "LOCK_OWNERSHIP",
                "PATH_BOUNDARY",
                "POLICY_DIGEST",
                "PRIVACY",
            ],
        )

    def test_current_control_blocks_before_lock_or_backend(self) -> None:
        backend = InMemoryGitBackend()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^RUNTIME_PUBLISHER_V2_CONTROL_SYNC_REQUIRED$",
        ):
            self.publisher(
                backend,
                context=self.context(publisher=False),
            ).publish(self.request())
        self.assertEqual(self.lock.calls, 0)
        self.assertEqual(backend.create_calls, 0)
        self.assertEqual(backend.write_calls, 0)

    def test_repository_authority_blocks_after_control_sync(self) -> None:
        backend = InMemoryGitBackend()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^CANONICAL_PUBLICATION_NOT_AUTHORIZED$",
        ):
            self.publisher(
                backend,
                context=self.context(
                    repository_bound=False,
                    canonical=False,
                ),
            ).publish(self.request())
        self.assertEqual(self.lock.calls, 0)
        self.assertEqual(backend.create_calls, 0)
        self.assertEqual(backend.write_calls, 0)

    def test_runtime_context_is_not_replaceable_by_caller_manifest(
        self,
    ) -> None:
        backend = InMemoryGitBackend()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_RUNTIME_BOOTSTRAP_CONTEXT_REQUIRED$",
        ):
            self.publisher(backend).publish(self.request())
        self.assertEqual(backend.create_calls, 0)
        forged_context = replace(
            self.context(),
            contract=object(),
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_RUNTIME_TRUST_CONTEXT_MISMATCH$",
        ):
            self.publisher(
                backend,
                context=forged_context,
            ).publish(self.request())
        self.assertEqual(backend.create_calls, 0)

    def test_exact_put_set_ff_publishes_and_reads_back(self) -> None:
        backend = InMemoryGitBackend()
        readback = self.publisher(
            backend,
            context=self.context(),
        ).publish(self.request())
        self.assertTrue(readback.verified)
        self.assertEqual(backend.head, backend.commit_id)
        self.assertTrue(backend.cleaned)
        self.assertEqual(self.lock.calls, 3)
        self.assertEqual(
            set(backend.files),
            {artifact.relative_path for artifact in self.artifacts},
        )

    def test_manifest_gate_or_artifact_drift_fails_closed(self) -> None:
        value = dict(parse_json_bytes(self.manifest()))
        value["shared_gates"] = [
            dict(item) for item in value["shared_gates"]
        ]
        value["shared_gates"][0]["evidence_digest"] = "0" * 64
        value["manifest_digest"] = "0" * 64
        tampered = canonicalize_object(
            canonical_with_digest(value, "manifest_digest")
        )
        backend = InMemoryGitBackend()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_MANIFEST_REQUEST_BYTES_MISMATCH$",
        ):
            self.publisher(
                backend,
                context=self.context(),
            ).publish(self.request(manifest=tampered))
        self.assertEqual(backend.create_calls, 0)

        changed_uid = replace(
            self.artifacts[0],
            artifact_uid=uid("art", 9),
        )
        changed = (changed_uid, *self.artifacts[1:])
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_MANIFEST_REQUEST_BYTES_MISMATCH$",
        ):
            self.publisher(
                backend,
                context=self.context(),
            ).publish(
                self.request(
                    artifacts=changed,
                    manifest=self.manifest(),
                )
            )

    def test_jsonl_is_never_reinterpreted_as_one_json_object(self) -> None:
        part = next(
            item
            for item in self.artifacts
            if "/part-" in item.relative_path
        )
        whole_object = replace(
            part,
            serialization="RFC8785_JCS_OBJECT",
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLIC_SERIALIZATION_NOT_EXACT_JCS$",
        ):
            self.manifest((whole_object,))
        without_lf = replace(
            part,
            payload=part.payload[:-1],
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLIC_JSONL_FRAMING_INVALID$",
        ):
            self.manifest((without_lf,))

    def test_record_count_and_delete_conditionals_fail_closed(self) -> None:
        part = next(
            item
            for item in self.artifacts
            if "/part-" in item.relative_path
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_ARTIFACT_RECORD_COUNT_MISMATCH$",
        ):
            self.manifest(
                (replace(part, record_count=2),)
            )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_DELETE_PRIOR_EVIDENCE_INVALID$",
        ):
            self.manifest(
                (
                    replace(
                        part,
                        operation="DELETE",
                        prior_serialization=part.serialization,
                        prior_digest="1" * 64,
                        prior_bytes=len(part.payload),
                        prior_record_count=1,
                    ),
                )
            )

    def delete_artifact(self, *, digest=None):
        part = next(
            item
            for item in self.artifacts
            if "/part-" in item.relative_path
        )
        assert part.payload is not None
        return PublicationArtifact(
            part.relative_path,
            None,
            lane="RUN_LOG",
            schema_id=part.schema_id,
            artifact_uid=uid("art", 8),
            operation="DELETE",
            prior_serialization=part.serialization,
            prior_digest=(
                hashlib.sha256(part.payload).hexdigest()
                if digest is None
                else digest
            ),
            prior_bytes=len(part.payload),
            prior_record_count=part.record_count,
        ), part.payload

    def test_exact_part_delete_revalidates_prior_physical_bytes(self) -> None:
        deletion, prior = self.delete_artifact()
        backend = InMemoryGitBackend(
            {deletion.relative_path: prior}
        )
        readback = self.publisher(
            backend,
            context=self.context(),
        ).publish(self.request(artifacts=(deletion,)))
        self.assertTrue(readback.verified)
        self.assertNotIn(deletion.relative_path, backend.files)

    def test_unlisted_delete_and_prior_byte_drift_fail_closed(self) -> None:
        index = next(
            item
            for item in self.artifacts
            if "/index-" in item.relative_path
        )
        assert index.payload is not None
        unlisted = PublicationArtifact(
            index.relative_path,
            None,
            lane="RUN_LOG",
            schema_id=index.schema_id,
            artifact_uid=uid("art", 7),
            operation="DELETE",
            prior_serialization=index.serialization,
            prior_digest=hashlib.sha256(index.payload).hexdigest(),
            prior_bytes=len(index.payload),
            prior_record_count=index.record_count,
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "PUBLICATION_UNLISTED_DELETION",
        ):
            self.manifest((unlisted,))

        deletion, prior = self.delete_artifact(digest="1" * 64)
        backend = InMemoryGitBackend(
            {deletion.relative_path: prior}
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "^PUBLICATION_DELETE_PRIOR_BYTES_MISMATCH$",
        ):
            self.publisher(
                backend,
                context=self.context(),
            ).publish(self.request(artifacts=(deletion,)))
        self.assertEqual(backend.write_calls, 0)
        self.assertEqual(
            backend.files[deletion.relative_path],
            prior,
        )
        self.assertTrue(backend.cleaned)

    def test_physical_backend_put_and_delete_are_exact(self) -> None:
        part = next(
            item
            for item in self.artifacts
            if "/part-" in item.relative_path
        )
        assert part.payload is not None
        deletion, _ = self.delete_artifact()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            scratch = root / "scratch"
            worktree = root / "worktree"
            repo.mkdir()
            scratch.mkdir()
            worktree.mkdir()
            backend = SubprocessGitBackend(repo, scratch)
            backend.write_artifacts(worktree, (part,))
            target = worktree.joinpath(
                *part.relative_path.split("/")
            )
            self.assertEqual(target.read_bytes(), part.payload)
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "^PUBLICATION_RUN_LOG_IMMUTABLE_PATH_EXISTS$",
            ):
                backend.write_artifacts(worktree, (part,))
            self.assertEqual(
                backend.read_artifact(
                    worktree,
                    part.relative_path,
                ),
                part.payload,
            )
            backend.write_artifacts(worktree, (deletion,))
            self.assertFalse(target.exists())

    def test_physical_backend_rejects_symlink_parent(self) -> None:
        part = next(
            item
            for item in self.artifacts
            if "/part-" in item.relative_path
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            scratch = root / "scratch"
            worktree = root / "worktree"
            outside = root / "outside"
            for path in (repo, scratch, worktree, outside):
                path.mkdir()
            (
                worktree / "OpenAIDatabase"
            ).symlink_to(outside, target_is_directory=True)
            backend = SubprocessGitBackend(repo, scratch)
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "^PUBLICATION_PARENT_SYMLINK_OR_NON_DIRECTORY$",
            ):
                backend.write_artifacts(worktree, (part,))


if __name__ == "__main__":
    unittest.main()
