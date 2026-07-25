"""FF-only physical publication from a verified activation settlement."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.registry.auto.tools.validate_auto import AutoContract

from .activation import ActivationHandshake
from .bootstrap import (
    BootstrapContext,
    require_canonical_publication_authority,
)
from .core import (
    AutoRuntimeError,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
    sha256_bytes,
)
from .privacy import (
    validate_public_jsonl_serialization,
    validate_public_serialization,
)
from .repository_binding import (
    RepositoryBindingPermit,
    assert_repository_binding_permit,
    validate_delete_prerequisites,
    validate_run_log_transaction,
)


GIT_OBJECT_RE = re.compile(r"^(sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
AUTO_TRANSACTION_RE = re.compile(
    r"^atx_[0-7][0-9A-HJKMNP-TV-Z]{25}$"
)
COMMIT_MESSAGE_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,120}$")
ACTIVATION_ARTIFACT_COUNT = 5
MAX_ACTIVATION_ARTIFACT_BYTES = 1024 * 1024
MAX_PUBLICATION_ARTIFACT_BYTES = 20 * 1024 * 1024
MAX_PUBLICATION_ARTIFACTS = 10_000
PUBLICATION_MANIFEST_V2_SCHEMA = (
    SCHEMA_PREFIX + "publication-manifest:v2"
)
OBJECT_SERIALIZATION = "RFC8785_JCS_OBJECT"
JSONL_SERIALIZATION = "RFC8785_JCS_PER_LINE_LF"
SHARED_GATE_CODES = (
    "BUNDLE_DIGEST",
    "EXPECTED_REMOTE_HEAD",
    "LOCK_OWNERSHIP",
    "PATH_BOUNDARY",
    "POLICY_DIGEST",
    "PRIVACY",
)


@dataclass(frozen=True)
class PublicationArtifact:
    relative_path: str
    payload: Optional[bytes]
    lane: Optional[str] = None
    schema_id: Optional[str] = None
    artifact_uid: Optional[str] = None
    operation: str = "PUT"
    serialization: Optional[str] = None
    record_count: Optional[int] = None
    prior_serialization: Optional[str] = None
    prior_digest: Optional[str] = None
    prior_bytes: Optional[int] = None
    prior_record_count: Optional[int] = None


@dataclass(frozen=True)
class PublicationRequest:
    auto_transaction_uid: str
    authority: str
    trust_mode: str
    expected_remote_head: str
    commit_message: str
    artifacts: Tuple[PublicationArtifact, ...]
    lock_owner_run_uid: str
    lock_state_digest: str
    activation_settlement_repo_path: Optional[str] = None
    publication_manifest_payload: Optional[bytes] = None


@dataclass(frozen=True)
class RemoteReadback:
    commit: str
    artifact_digests: Mapping[str, str]
    verified: bool


def _safe_relative_path(path: str) -> None:
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or not parsed.parts
        or any(
            part in {"", ".", ".."} or part.casefold() == ".git"
            for part in parsed.parts
        )
        or "\\" in path
        or path.endswith("/")
    ):
        raise AutoRuntimeError("PUBLICATION_PATH_INVALID")


def _positive_integer(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def _validate_put_payload(
    artifact: PublicationArtifact,
    contract: AutoContract,
    bundle_digest: str,
) -> int:
    if (
        not isinstance(artifact.payload, bytes)
        or len(artifact.payload) > MAX_PUBLICATION_ARTIFACT_BYTES
        or artifact.schema_id is None
    ):
        raise AutoRuntimeError(
            "PUBLICATION_ARTIFACT_PAYLOAD_INVALID"
        )
    if artifact.serialization == OBJECT_SERIALIZATION:
        validate_public_serialization(
            artifact.payload,
            contract,
            artifact.schema_id,
            bundle_digest,
        )
        return 1
    if artifact.serialization == JSONL_SERIALIZATION:
        return len(
            validate_public_jsonl_serialization(
                artifact.payload,
                contract,
                artifact.schema_id,
                bundle_digest,
                maximum_bytes=MAX_PUBLICATION_ARTIFACT_BYTES,
            )
        )
    raise AutoRuntimeError(
        "PUBLICATION_ARTIFACT_SERIALIZATION_INVALID"
    )


def _artifact_descriptor(
    artifact: PublicationArtifact,
    contract: AutoContract,
    bundle_digest: str,
) -> Mapping[str, object]:
    _safe_relative_path(artifact.relative_path)
    if (
        artifact.lane not in {"REGISTRY", "RUN_LOG"}
        or not isinstance(artifact.schema_id, str)
        or not isinstance(artifact.artifact_uid, str)
        or artifact.operation not in {"PUT", "DELETE"}
    ):
        raise AutoRuntimeError(
            "PUBLICATION_ACTIVE_ARTIFACT_METADATA_REQUIRED"
        )
    descriptor: Dict[str, object] = {
        "artifact_uid": artifact.artifact_uid,
        "artifact_operation": artifact.operation,
        "artifact_schema_id": artifact.schema_id,
        "artifact_repo_path": artifact.relative_path,
    }
    if artifact.operation == "PUT":
        if any(
            value is not None
            for value in (
                artifact.prior_serialization,
                artifact.prior_digest,
                artifact.prior_bytes,
                artifact.prior_record_count,
            )
        ):
            raise AutoRuntimeError(
                "PUBLICATION_PUT_PRIOR_EVIDENCE_FORBIDDEN"
            )
        observed_records = _validate_put_payload(
            artifact,
            contract,
            bundle_digest,
        )
        if (
            not _positive_integer(artifact.record_count)
            or artifact.record_count != observed_records
        ):
            raise AutoRuntimeError(
                "PUBLICATION_ARTIFACT_RECORD_COUNT_MISMATCH"
            )
        assert artifact.payload is not None
        descriptor.update(
            {
                "artifact_serialization": artifact.serialization,
                "artifact_digest": sha256_bytes(artifact.payload),
                "artifact_bytes": len(artifact.payload),
                "artifact_record_count": artifact.record_count,
            }
        )
        return descriptor

    if (
        artifact.payload is not None
        or artifact.serialization is not None
        or artifact.record_count is not None
        or artifact.prior_serialization
        not in {OBJECT_SERIALIZATION, JSONL_SERIALIZATION}
        or not isinstance(artifact.prior_digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", artifact.prior_digest)
        or not _positive_integer(artifact.prior_bytes)
        or not _positive_integer(artifact.prior_record_count)
    ):
        raise AutoRuntimeError(
            "PUBLICATION_DELETE_PRIOR_EVIDENCE_INVALID"
        )
    descriptor.update(
        {
            "prior_artifact_serialization": (
                artifact.prior_serialization
            ),
            "prior_artifact_digest": artifact.prior_digest,
            "prior_artifact_bytes": artifact.prior_bytes,
            "prior_artifact_record_count": (
                artifact.prior_record_count
            ),
        }
    )
    return descriptor


def _gate_evidence(
    *,
    contract: AutoContract,
    bundle_digest: str,
    expected_remote_head: str,
    lock_owner_run_uid: str,
    lock_state_digest: str,
    descriptors: Sequence[Mapping[str, object]],
) -> Tuple[Mapping[str, str], ...]:
    policy_material = [
        {
            "policy_id": policy_id,
            "policy_digest": sha256_bytes(
                canonicalize_object(contract.shared.policies[policy_id])
            ),
        }
        for policy_id in sorted(contract.shared.policies)
    ]
    descriptor_material = [
        dict(descriptor)
        for descriptor in descriptors
    ]
    evidence: Mapping[str, object] = {
        "BUNDLE_DIGEST": {
            "bundle_digest": bundle_digest,
        },
        "EXPECTED_REMOTE_HEAD": {
            "expected_remote_head": expected_remote_head,
        },
        "LOCK_OWNERSHIP": {
            "lock_owner_run_uid": lock_owner_run_uid,
            "lock_state_digest": lock_state_digest,
        },
        "PATH_BOUNDARY": {
            "artifacts": descriptor_material,
        },
        "POLICY_DIGEST": {
            "policies": policy_material,
        },
        "PRIVACY": {
            "artifacts": descriptor_material,
            "validation": (
                "SCHEMA_PUBLIC_VALUE_AND_EXACT_SERIALIZATION"
            ),
        },
    }
    return tuple(
        {
            "gate_code": code,
            "status": "PASS",
            "evidence_digest": sha256_bytes(
                canonicalize_object(
                    {
                        "domain": "SKILLOPS_PUBLICATION_GATE_V2",
                        "gate_code": code,
                        "evidence": evidence[code],
                    }
                )
            ),
        }
        for code in SHARED_GATE_CODES
    )


def build_publication_manifest_v2_payload(
    *,
    contract: AutoContract,
    bundle_digest: str,
    manifest_uid: str,
    auto_transaction_uid: str,
    trigger_kind: str,
    created_at: str,
    mechanism_srv_revision: str,
    expected_remote_head: str,
    artifacts: Sequence[PublicationArtifact],
    lane_transaction_uids: Mapping[str, str],
    source_watermark_refs: Mapping[str, str],
    lock_owner_run_uid: str,
    lock_state_digest: str,
) -> bytes:
    """Build exact v2 bytes solely from validated physical descriptors."""

    if (
        not artifacts
        or len(artifacts) > MAX_PUBLICATION_ARTIFACTS
    ):
        raise AutoRuntimeError(
            "PUBLICATION_ARTIFACT_COUNT_INVALID"
        )
    descriptors = [
        (artifact.lane, _artifact_descriptor(
            artifact,
            contract,
            bundle_digest,
        ))
        for artifact in artifacts
    ]
    lanes = sorted({lane for lane, _ in descriptors})
    if (
        set(lanes) != set(lane_transaction_uids)
        or set(lanes) != set(source_watermark_refs)
    ):
        raise AutoRuntimeError(
            "PUBLICATION_LANE_METADATA_SET_MISMATCH"
        )
    lane_manifests = []
    flat_descriptors = []
    for lane in lanes:
        lane_artifacts = sorted(
            (
                descriptor
                for observed_lane, descriptor in descriptors
                if observed_lane == lane
            ),
            key=lambda item: (
                str(item["artifact_repo_path"]),
                str(item["artifact_uid"]),
            ),
        )
        flat_descriptors.extend(lane_artifacts)
        lane_manifests.append(
            {
                "lane": lane,
                "lane_transaction_uid": lane_transaction_uids[lane],
                "source_watermark_ref": (
                    source_watermark_refs[lane]
                ),
                "artifact_count": len(lane_artifacts),
                "artifacts": lane_artifacts,
            }
        )
    value = canonical_with_digest(
        {
            "schema_version": PUBLICATION_MANIFEST_V2_SCHEMA,
            "protocol_revision": PROTOCOL,
            "bundle_digest": bundle_digest,
            "manifest_uid": manifest_uid,
            "auto_transaction_uid": auto_transaction_uid,
            "trigger_kind": trigger_kind,
            "created_at": created_at,
            "mechanism_srv_revision": mechanism_srv_revision,
            "expected_remote_head": expected_remote_head,
            "settled_lanes": lanes,
            "lane_manifests": lane_manifests,
            "shared_gates": list(
                _gate_evidence(
                    contract=contract,
                    bundle_digest=bundle_digest,
                    expected_remote_head=expected_remote_head,
                    lock_owner_run_uid=lock_owner_run_uid,
                    lock_state_digest=lock_state_digest,
                    descriptors=flat_descriptors,
                )
            ),
            "manifest_digest": "0" * 64,
        },
        "manifest_digest",
    )
    raw = canonicalize_object(value)
    validate_public_serialization(
        raw,
        contract,
        PUBLICATION_MANIFEST_V2_SCHEMA,
        bundle_digest,
    )
    return raw


class PublicationLock:
    def assert_owned(
        self,
        owner_run_uid: str,
        expected_digest: str,
    ) -> Mapping[str, object]:
        raise NotImplementedError


class GitBackend:
    def remote_head(self) -> str:
        raise NotImplementedError

    def create_worktree(self, expected_head: str, transaction_uid: str) -> Path:
        raise NotImplementedError

    def write_artifacts(self, worktree: Path, artifacts: Sequence[PublicationArtifact]) -> None:
        raise NotImplementedError

    def read_artifact(self, worktree: Path, relative_path: str) -> bytes:
        raise NotImplementedError

    def changed_paths(self, worktree: Path) -> Tuple[str, ...]:
        raise NotImplementedError

    def commit(self, worktree: Path, message: str, paths: Sequence[str]) -> str:
        raise NotImplementedError

    def push(self, worktree: Path, expected_head: str) -> None:
        raise NotImplementedError

    def readback(self, commit: str, artifacts: Sequence[PublicationArtifact]) -> RemoteReadback:
        raise NotImplementedError

    def find_transaction(self, transaction_uid: str, expected_parent: str) -> Optional[str]:
        raise NotImplementedError

    def cleanup(self, worktree: Path) -> None:
        raise NotImplementedError


class SubprocessGitBackend(GitBackend):
    """Production backend.  Commands intentionally contain no merge/rebase/force."""

    def __init__(
        self,
        repo_root: Path,
        scratch_root: Path,
        remote: str = "origin",
        *,
        repository_binding_permit: Optional[
            RepositoryBindingPermit
        ] = None,
    ) -> None:
        self.repo_root = repo_root.resolve(strict=True)
        self.scratch_root = scratch_root.resolve(strict=True)
        self.remote = remote
        self.repository_binding_permit = (
            repository_binding_permit
        )
        if repository_binding_permit is not None:
            observation = assert_repository_binding_permit(
                repository_binding_permit,
                repository_binding_permit.context,
                repository_binding_permit.observation.expected_remote_head,
            )
            if (
                self.repo_root != observation.repo_root
                or self.scratch_root != observation.scratch_root
                or self.remote != observation.remote_name
            ):
                raise AutoRuntimeError(
                    "REPOSITORY_BINDING_BACKEND_SCOPE_MISMATCH"
                )

    def _run(
        self,
        args: Sequence[str],
        *,
        cwd: Optional[Path] = None,
        timeout: int = 120,
        allow_cleanup_force: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        forbidden = {"rebase", "merge", "reset", "checkout", "--force", "--force-with-lease"}
        violations = forbidden.intersection(args)
        if violations and not (
            violations == {"--force"}
            and allow_cleanup_force
            and tuple(args[:3]) == ("git", "worktree", "remove")
        ):
            raise AutoRuntimeError("GIT_FORBIDDEN_COMMAND")
        try:
            result = subprocess.run(
                list(args),
                cwd=str(cwd or self.repo_root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AutoRuntimeError("GIT_COMMAND_UNAVAILABLE_OR_TIMEOUT") from exc
        if check and result.returncode != 0:
            raise AutoRuntimeError("GIT_COMMAND_FAILED")
        return result

    def _object_format(self) -> str:
        return self._run(("git", "rev-parse", "--show-object-format")).stdout.decode().strip()

    def _tag(self, raw: str) -> str:
        return f"{self._object_format()}:{raw}"

    def remote_head(self) -> str:
        output = self._run(("git", "ls-remote", self.remote, "refs/heads/main")).stdout.decode()
        fields = output.strip().split()
        if len(fields) != 2 or fields[1] != "refs/heads/main":
            raise AutoRuntimeError("REMOTE_HEAD_READ_FAILED")
        return self._tag(fields[0])

    def create_worktree(self, expected_head: str, transaction_uid: str) -> Path:
        if self._run(("git", "branch", "--show-current")).stdout.decode().strip() != "main":
            raise AutoRuntimeError("MAIN_REFERENCE_BRANCH_INVALID")
        if self._run(("git", "status", "--porcelain")).stdout:
            raise AutoRuntimeError("MAIN_REFERENCE_TREE_DIRTY")
        raw = expected_head.split(":", 1)[1]
        destination = self.scratch_root / f"skillops-publish-{transaction_uid}"
        if destination.exists():
            raise AutoRuntimeError("PUBLICATION_WORKTREE_ALREADY_EXISTS")
        self._run(("git", "worktree", "add", "--detach", str(destination), raw))
        return destination

    @staticmethod
    def _target(
        worktree: Path,
        relative_path: str,
        *,
        create_parents: bool,
    ) -> Path:
        try:
            root_info = os.lstat(str(worktree))
        except OSError as exc:
            raise AutoRuntimeError(
                "PUBLICATION_WORKTREE_ROOT_STAT_FAILED"
            ) from exc
        if (
            stat.S_ISLNK(root_info.st_mode)
            or not stat.S_ISDIR(root_info.st_mode)
        ):
            raise AutoRuntimeError(
                "PUBLICATION_WORKTREE_ROOT_NOT_REAL_DIRECTORY"
            )
        current = worktree
        for part in PurePosixPath(relative_path).parts[:-1]:
            current = current / part
            try:
                info = os.lstat(str(current))
            except FileNotFoundError:
                if not create_parents:
                    raise AutoRuntimeError(
                        "PUBLICATION_PARENT_MISSING"
                    )
                try:
                    current.mkdir(mode=0o755)
                    info = os.lstat(str(current))
                except OSError as exc:
                    raise AutoRuntimeError(
                        "PUBLICATION_PARENT_CREATE_FAILED"
                    ) from exc
            except OSError as exc:
                raise AutoRuntimeError(
                    "PUBLICATION_PARENT_STAT_FAILED"
                ) from exc
            if (
                stat.S_ISLNK(info.st_mode)
                or not stat.S_ISDIR(info.st_mode)
            ):
                raise AutoRuntimeError(
                    "PUBLICATION_PARENT_SYMLINK_OR_NON_DIRECTORY"
                )
        return worktree.joinpath(
            *PurePosixPath(relative_path).parts
        )

    def read_artifact(
        self,
        worktree: Path,
        relative_path: str,
    ) -> bytes:
        target = self._target(
            worktree,
            relative_path,
            create_parents=False,
        )
        try:
            before = os.lstat(str(target))
        except OSError as exc:
            raise AutoRuntimeError(
                "PUBLICATION_PRIOR_ARTIFACT_STAT_FAILED"
            ) from exc
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or before.st_size > MAX_PUBLICATION_ARTIFACT_BYTES
        ):
            raise AutoRuntimeError(
                "PUBLICATION_PRIOR_ARTIFACT_NOT_BOUNDED_REGULAR"
            )
        descriptor: Optional[int] = None
        try:
            descriptor = os.open(
                str(target),
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
            after = os.fstat(descriptor)
            if (
                not stat.S_ISREG(after.st_mode)
                or (before.st_dev, before.st_ino)
                != (after.st_dev, after.st_ino)
            ):
                raise AutoRuntimeError(
                    "PUBLICATION_PRIOR_ARTIFACT_REBOUND"
                )
            chunks = []
            observed = 0
            while True:
                block = os.read(
                    descriptor,
                    min(
                        1024 * 1024,
                        MAX_PUBLICATION_ARTIFACT_BYTES + 1 - observed,
                    ),
                )
                if not block:
                    break
                chunks.append(block)
                observed += len(block)
                if observed > MAX_PUBLICATION_ARTIFACT_BYTES:
                    raise AutoRuntimeError(
                        "PUBLICATION_PRIOR_ARTIFACT_TOO_LARGE"
                    )
            return b"".join(chunks)
        except AutoRuntimeError:
            raise
        except OSError as exc:
            raise AutoRuntimeError(
                "PUBLICATION_PRIOR_ARTIFACT_READ_FAILED"
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)

    def write_artifacts(self, worktree: Path, artifacts: Sequence[PublicationArtifact]) -> None:
        from .core import atomic_write_bytes

        for artifact in artifacts:
            target = self._target(
                worktree,
                artifact.relative_path,
                create_parents=artifact.operation == "PUT",
            )
            if artifact.operation == "PUT":
                if artifact.payload is None:
                    raise AutoRuntimeError(
                        "PUBLICATION_ARTIFACT_PAYLOAD_INVALID"
                    )
                try:
                    existing = os.lstat(str(target))
                except FileNotFoundError:
                    existing = None
                except OSError as exc:
                    raise AutoRuntimeError(
                        "PUBLICATION_TARGET_STAT_FAILED"
                    ) from exc
                if existing is not None and (
                    stat.S_ISLNK(existing.st_mode)
                    or not stat.S_ISREG(existing.st_mode)
                ):
                    raise AutoRuntimeError(
                        "PUBLICATION_TARGET_NOT_REGULAR"
                    )
                if existing is not None and artifact.lane == "RUN_LOG":
                    raise AutoRuntimeError(
                        "PUBLICATION_RUN_LOG_IMMUTABLE_PATH_EXISTS"
                    )
                atomic_write_bytes(
                    target,
                    artifact.payload,
                    mode=0o644,
                )
                continue
            prior = self.read_artifact(
                worktree,
                artifact.relative_path,
            )
            if (
                len(prior) != artifact.prior_bytes
                or sha256_bytes(prior) != artifact.prior_digest
            ):
                raise AutoRuntimeError(
                    "PUBLICATION_DELETE_PRIOR_BYTES_MISMATCH"
                )
            try:
                os.unlink(str(target))
                parent_fd = os.open(str(target.parent), os.O_RDONLY)
                try:
                    os.fsync(parent_fd)
                finally:
                    os.close(parent_fd)
            except OSError as exc:
                raise AutoRuntimeError(
                    "PUBLICATION_DELETE_FAILED"
                ) from exc

    def changed_paths(self, worktree: Path) -> Tuple[str, ...]:
        output = self._run(
            ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"), cwd=worktree
        ).stdout
        rows = [row for row in output.split(b"\0") if row]
        paths = []
        for row in rows:
            if len(row) < 4:
                raise AutoRuntimeError("GIT_STATUS_PARSE_FAILED")
            if b"R" in row[:2] or b"C" in row[:2]:
                raise AutoRuntimeError("GIT_RENAME_OR_COPY_UNEXPECTED")
            paths.append(row[3:].decode("utf-8", errors="strict"))
        return tuple(sorted(paths))

    def commit(self, worktree: Path, message: str, paths: Sequence[str]) -> str:
        self._run(("git", "add", "--", *paths), cwd=worktree)
        self._run(("git", "diff", "--cached", "--check"), cwd=worktree)
        self._run(("git", "commit", "-m", message), cwd=worktree)
        raw = self._run(("git", "rev-parse", "HEAD"), cwd=worktree).stdout.decode().strip()
        return self._tag(raw)

    def push(self, worktree: Path, expected_head: str) -> None:
        if self.remote_head() != expected_head:
            raise AutoRuntimeError("REMOTE_HEAD_CHANGED")
        self._run(("git", "push", self.remote, "HEAD:main"), cwd=worktree)

    def readback(self, commit: str, artifacts: Sequence[PublicationArtifact]) -> RemoteReadback:
        if self.remote_head() != commit:
            return RemoteReadback(commit, {}, False)
        self._run(("git", "fetch", self.remote, "main"))
        raw = commit.split(":", 1)[1]
        observed = {}
        for artifact in artifacts:
            if artifact.operation == "DELETE":
                exists = self._run(
                    (
                        "git",
                        "cat-file",
                        "-e",
                        f"{raw}:{artifact.relative_path}",
                    ),
                    timeout=60,
                    check=False,
                )
                if exists.returncode == 0:
                    return RemoteReadback(
                        commit,
                        observed,
                        False,
                    )
                assert artifact.prior_digest is not None
                observed[artifact.relative_path] = (
                    artifact.prior_digest
                )
                continue
            payload = self._run(
                ("git", "show", f"{raw}:{artifact.relative_path}"), timeout=60
            ).stdout
            if artifact.payload is None:
                return RemoteReadback(commit, observed, False)
            observed[artifact.relative_path] = sha256_bytes(payload)
            if payload != artifact.payload:
                return RemoteReadback(commit, observed, False)
        return RemoteReadback(commit, observed, True)

    def find_transaction(self, transaction_uid: str, expected_parent: str) -> Optional[str]:
        self._run(("git", "fetch", self.remote, "main"))
        output = self._run(
            (
                "git",
                "log",
                f"{self.remote}/main",
                "--max-count=200",
                "--format=%H%x1f%P%x1f%B%x1e",
            )
        ).stdout
        expected_raw = expected_parent.split(":", 1)[1]
        trailer = f"SkillOps-Auto-Transaction: {transaction_uid}"
        matches = []
        for raw_record in output.split(b"\x1e"):
            if not raw_record.strip():
                continue
            fields = raw_record.strip().split(b"\x1f", 2)
            if len(fields) != 3:
                raise AutoRuntimeError("GIT_LOG_RECONCILIATION_PARSE_FAILED")
            commit_raw = fields[0].decode("ascii")
            parents = fields[1].decode("ascii").split()
            message_lines = fields[2].decode("utf-8", errors="strict").splitlines()
            if parents == [expected_raw] and trailer in message_lines:
                matches.append(self._tag(commit_raw))
        if len(matches) > 1:
            raise AutoRuntimeError("PUBLICATION_TRANSACTION_DUPLICATE")
        return matches[0] if matches else None

    def cleanup(self, worktree: Path) -> None:
        if worktree.exists():
            try:
                self._run(("git", "worktree", "remove", str(worktree)))
            except AutoRuntimeError:
                self._run(
                    ("git", "worktree", "remove", "--force", str(worktree)),
                    allow_cleanup_force=True,
                )
        self._run(("git", "worktree", "prune"))


class PhysicalPublisher:
    def __init__(
        self,
        contract: AutoContract,
        bundle_digest: str,
        backend: GitBackend,
        *,
        trusted_mode: str,
        lock: PublicationLock,
        activation_handshake: Optional[ActivationHandshake] = None,
        runtime_context: Optional[BootstrapContext] = None,
        repository_binding_permit: Optional[
            RepositoryBindingPermit
        ] = None,
    ) -> None:
        if trusted_mode not in {"CANDIDATE", "ACTIVE"}:
            raise AutoRuntimeError("PUBLICATION_TRUST_MODE_INVALID")
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.backend = backend
        self.trusted_mode = trusted_mode
        self.lock = lock
        self.activation_handshake = activation_handshake
        self.runtime_context = runtime_context
        self.repository_binding_permit = repository_binding_permit
        self._run_log_transaction_closure: Optional[
            Mapping[str, Any]
        ] = None

    @staticmethod
    def _safe_relative(path: str) -> None:
        _safe_relative_path(path)

    def _validate_active_manifest(
        self,
        request: PublicationRequest,
    ) -> None:
        if self.runtime_context is None:
            raise AutoRuntimeError(
                "PUBLICATION_RUNTIME_BOOTSTRAP_CONTEXT_REQUIRED"
            )
        if (
            self.runtime_context.trust.mode != request.trust_mode
            or self.runtime_context.trust.expected_bundle_digest
            != self.bundle_digest
            or self.runtime_context.contract is not self.contract
        ):
            raise AutoRuntimeError(
                "PUBLICATION_RUNTIME_TRUST_CONTEXT_MISMATCH"
            )
        require_canonical_publication_authority(
            self.runtime_context
        )
        assert_repository_binding_permit(
            self.repository_binding_permit,
            self.runtime_context,
            request.expected_remote_head,
        )
        if isinstance(self.backend, SubprocessGitBackend):
            if (
                self.backend.repository_binding_permit
                is not self.repository_binding_permit
            ):
                raise AutoRuntimeError(
                    "REPOSITORY_BINDING_BACKEND_PERMIT_REQUIRED"
                )
        raw = request.publication_manifest_payload
        if not isinstance(raw, bytes):
            raise AutoRuntimeError(
                "PUBLICATION_MANIFEST_V2_REQUIRED"
            )
        manifest = validate_public_serialization(
            raw,
            self.contract,
            PUBLICATION_MANIFEST_V2_SCHEMA,
            self.bundle_digest,
        )
        if (
            manifest.get("auto_transaction_uid")
            != request.auto_transaction_uid
            or manifest.get("expected_remote_head")
            != request.expected_remote_head
        ):
            raise AutoRuntimeError(
                "PUBLICATION_MANIFEST_REQUEST_CONTEXT_MISMATCH"
            )
        lane_manifests = manifest.get("lane_manifests")
        if not isinstance(lane_manifests, list):
            raise AutoRuntimeError(
                "PUBLICATION_MANIFEST_LANES_INVALID"
            )
        lane_transaction_uids = {
            str(lane["lane"]): str(lane["lane_transaction_uid"])
            for lane in lane_manifests
        }
        source_watermark_refs = {
            str(lane["lane"]): str(lane["source_watermark_ref"])
            for lane in lane_manifests
        }
        expected = build_publication_manifest_v2_payload(
            contract=self.contract,
            bundle_digest=self.bundle_digest,
            manifest_uid=str(manifest["manifest_uid"]),
            auto_transaction_uid=request.auto_transaction_uid,
            trigger_kind=str(manifest["trigger_kind"]),
            created_at=str(manifest["created_at"]),
            mechanism_srv_revision=str(
                manifest["mechanism_srv_revision"]
            ),
            expected_remote_head=request.expected_remote_head,
            artifacts=request.artifacts,
            lane_transaction_uids=lane_transaction_uids,
            source_watermark_refs=source_watermark_refs,
            lock_owner_run_uid=request.lock_owner_run_uid,
            lock_state_digest=request.lock_state_digest,
        )
        if expected != raw:
            raise AutoRuntimeError(
                "PUBLICATION_MANIFEST_REQUEST_BYTES_MISMATCH"
            )
        assert self.repository_binding_permit is not None
        self._run_log_transaction_closure = (
            validate_run_log_transaction(
                self.repository_binding_permit,
                self.runtime_context,
                request.expected_remote_head,
                request.artifacts,
            )
        )

    def _validate_request(self, request: PublicationRequest) -> Tuple[str, ...]:
        if request.trust_mode != self.trusted_mode:
            raise AutoRuntimeError("PUBLICATION_TRUST_CONTEXT_MISMATCH")
        if not GIT_OBJECT_RE.fullmatch(request.expected_remote_head):
            raise AutoRuntimeError("PUBLICATION_EXPECTED_HEAD_INVALID")
        if not AUTO_TRANSACTION_RE.fullmatch(
            request.auto_transaction_uid
        ):
            raise AutoRuntimeError("PUBLICATION_TRANSACTION_UID_INVALID")
        if not COMMIT_MESSAGE_RE.fullmatch(request.commit_message):
            raise AutoRuntimeError("PUBLICATION_COMMIT_MESSAGE_INVALID")
        if (
            not request.lock_owner_run_uid
            or not re.fullmatch(r"[0-9a-f]{64}", request.lock_state_digest)
        ):
            raise AutoRuntimeError("PUBLICATION_LOCK_EVIDENCE_INVALID")
        if request.authority == "CANDIDATE_TEST":
            raise AutoRuntimeError("CANDIDATE_CANONICAL_PUBLICATION_FORBIDDEN")
        if request.authority == "ACTIVE_RUNTIME" and request.trust_mode != "ACTIVE":
            raise AutoRuntimeError("ACTIVE_PUBLICATION_REQUIRES_ACTIVE_TRUST")
        if request.authority == "COORDINATED_ACTIVATION":
            if (
                request.trust_mode != "CANDIDATE"
                or self.activation_handshake is None
                or request.activation_settlement_repo_path is None
                or request.publication_manifest_payload is not None
            ):
                raise AutoRuntimeError(
                    "ACTIVATION_SETTLEMENT_HANDSHAKE_REQUIRED"
                )
            self._safe_relative(
                request.activation_settlement_repo_path
            )
            if (
                request.lock_owner_run_uid
                != request.auto_transaction_uid
                or len(request.artifacts) != ACTIVATION_ARTIFACT_COUNT
            ):
                raise AutoRuntimeError(
                    "ACTIVATION_PUBLICATION_CONTEXT_INVALID"
                )
        elif request.authority != "ACTIVE_RUNTIME":
            raise AutoRuntimeError("PUBLICATION_AUTHORITY_UNKNOWN")
        elif request.activation_settlement_repo_path is not None:
            raise AutoRuntimeError(
                "ACTIVE_RUNTIME_ACTIVATION_SETTLEMENT_FORBIDDEN"
            )
        else:
            self._validate_active_manifest(request)

        paths = []
        uids = set()
        for artifact in request.artifacts:
            self._safe_relative(artifact.relative_path)
            if (
                request.authority == "COORDINATED_ACTIVATION"
                and (
                    artifact.operation != "PUT"
                    or not isinstance(artifact.payload, bytes)
                    or any(
                        value is not None
                        for value in (
                            artifact.serialization,
                            artifact.record_count,
                            artifact.prior_serialization,
                            artifact.prior_digest,
                            artifact.prior_bytes,
                            artifact.prior_record_count,
                        )
                    )
                )
            ):
                raise AutoRuntimeError(
                    "ACTIVATION_PUBLICATION_ARTIFACT_INVALID"
                )
            if (
                request.authority == "COORDINATED_ACTIVATION"
                and artifact.payload is not None
                and len(artifact.payload)
                > MAX_ACTIVATION_ARTIFACT_BYTES
            ):
                raise AutoRuntimeError(
                    "ACTIVATION_PUBLICATION_ARTIFACT_SIZE_INVALID"
                )
            if artifact.relative_path in paths or (
                artifact.artifact_uid is not None
                and artifact.artifact_uid in uids
            ):
                raise AutoRuntimeError("PUBLICATION_ARTIFACT_DUPLICATE")
            if request.authority == "ACTIVE_RUNTIME":
                _artifact_descriptor(
                    artifact,
                    self.contract,
                    self.bundle_digest,
                )
            paths.append(artifact.relative_path)
            if artifact.artifact_uid is not None:
                uids.add(artifact.artifact_uid)
        if not paths:
            raise AutoRuntimeError("PUBLICATION_EMPTY_TRANSACTION_FORBIDDEN")
        if paths != sorted(paths):
            raise AutoRuntimeError("PUBLICATION_ARTIFACT_ORDER_INVALID")
        if (
            request.authority == "COORDINATED_ACTIVATION"
            and request.activation_settlement_repo_path not in paths
        ):
            raise AutoRuntimeError(
                "ACTIVATION_SETTLEMENT_ARTIFACT_REQUIRED"
            )
        return tuple(paths)

    def _validate_delete_artifacts(
        self,
        request: PublicationRequest,
        worktree: Path,
    ) -> None:
        for artifact in request.artifacts:
            if artifact.operation != "DELETE":
                continue
            assert artifact.schema_id is not None
            prior = self.backend.read_artifact(
                worktree,
                artifact.relative_path,
            )
            if (
                len(prior) != artifact.prior_bytes
                or sha256_bytes(prior) != artifact.prior_digest
            ):
                raise AutoRuntimeError(
                    "PUBLICATION_DELETE_PRIOR_BYTES_MISMATCH"
                )
            if artifact.prior_serialization == OBJECT_SERIALIZATION:
                validate_public_serialization(
                    prior,
                    self.contract,
                    artifact.schema_id,
                    self.bundle_digest,
                )
                observed_records = 1
            elif (
                artifact.prior_serialization
                == JSONL_SERIALIZATION
            ):
                observed_records = len(
                    validate_public_jsonl_serialization(
                        prior,
                        self.contract,
                        artifact.schema_id,
                        self.bundle_digest,
                        maximum_bytes=(
                            MAX_PUBLICATION_ARTIFACT_BYTES
                        ),
                    )
                )
            else:
                raise AutoRuntimeError(
                    "PUBLICATION_DELETE_SERIALIZATION_INVALID"
                )
            if observed_records != artifact.prior_record_count:
                raise AutoRuntimeError(
                    "PUBLICATION_DELETE_PRIOR_RECORD_COUNT_MISMATCH"
                )

    def _validate_activation_worktree(
        self,
        request: PublicationRequest,
        worktree: Path,
    ) -> None:
        if (
            self.activation_handshake is None
            or request.activation_settlement_repo_path is None
        ):
            raise AutoRuntimeError(
                "ACTIVATION_SETTLEMENT_HANDSHAKE_REQUIRED"
            )
        verified = self.activation_handshake.verify_settlement_root(
            worktree,
            request.activation_settlement_repo_path,
            request.expected_remote_head,
        )
        requested = {
            artifact.relative_path: artifact.payload
            for artifact in request.artifacts
        }
        if (
            verified.auto_transaction_uid
            != request.auto_transaction_uid
            or verified.expected_remote_head
            != request.expected_remote_head
        ):
            raise AutoRuntimeError(
                "ACTIVATION_SETTLEMENT_REQUEST_CONTEXT_MISMATCH"
            )
        if (
            tuple(sorted(requested)) != verified.artifact_paths
            or requested != dict(verified.payloads)
        ):
            raise AutoRuntimeError(
                "ACTIVATION_SETTLEMENT_REQUEST_BYTES_MISMATCH"
            )

    def publish(self, request: PublicationRequest) -> RemoteReadback:
        paths = self._validate_request(request)
        self.lock.assert_owned(
            request.lock_owner_run_uid,
            request.lock_state_digest,
        )
        worktree = self.backend.create_worktree(
            request.expected_remote_head, request.auto_transaction_uid
        )
        try:
            if request.authority == "ACTIVE_RUNTIME":
                self._validate_delete_artifacts(
                    request,
                    worktree,
                )
                if self._run_log_transaction_closure is None:
                    raise AutoRuntimeError(
                        "REPOSITORY_BINDING_TRANSACTION_CLOSURE_MISSING"
                    )
                assert self.runtime_context is not None
                assert self.repository_binding_permit is not None
                validate_delete_prerequisites(
                    self.repository_binding_permit,
                    self.runtime_context,
                    request.expected_remote_head,
                    self._run_log_transaction_closure,
                    request.artifacts,
                    self.backend.read_artifact,
                    worktree,
                )
            self.backend.write_artifacts(worktree, request.artifacts)
            if request.authority == "COORDINATED_ACTIVATION":
                self._validate_activation_worktree(request, worktree)
            changed = self.backend.changed_paths(worktree)
            if changed != paths:
                raise AutoRuntimeError("PUBLICATION_CHANGED_PATH_SET_MISMATCH")
            self.lock.assert_owned(
                request.lock_owner_run_uid,
                request.lock_state_digest,
            )
            if self.backend.remote_head() != request.expected_remote_head:
                recovered = self.backend.find_transaction(
                    request.auto_transaction_uid,
                    request.expected_remote_head,
                )
                if recovered is None:
                    raise AutoRuntimeError("REMOTE_HEAD_CHANGED")
                readback = self.backend.readback(
                    recovered, request.artifacts
                )
                if not readback.verified:
                    raise AutoRuntimeError("REMOTE_READBACK_FAILED")
                return readback
            message = (
                request.commit_message
                + "\n\nSkillOps-Auto-Transaction: "
                + request.auto_transaction_uid
            )
            commit = self.backend.commit(worktree, message, paths)
            self.lock.assert_owned(
                request.lock_owner_run_uid,
                request.lock_state_digest,
            )
            self.backend.push(worktree, request.expected_remote_head)
            readback = self.backend.readback(commit, request.artifacts)
            if not readback.verified:
                raise AutoRuntimeError("REMOTE_READBACK_FAILED")
            return readback
        finally:
            self.backend.cleanup(worktree)
