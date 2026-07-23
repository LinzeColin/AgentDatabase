"""FF-only physical publication from a verified activation settlement."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Optional, Sequence, Tuple

from CodexSkills.auto.tools.validate_auto import AutoContract, _validate_artifact_target

from .activation import ActivationHandshake
from .core import AutoRuntimeError, sha256_bytes
from .privacy import validate_public_serialization


GIT_OBJECT_RE = re.compile(r"^(sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
AUTO_TRANSACTION_RE = re.compile(
    r"^atx_[0-7][0-9A-HJKMNP-TV-Z]{25}$"
)
COMMIT_MESSAGE_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,120}$")
ACTIVATION_ARTIFACT_COUNT = 5
MAX_ACTIVATION_ARTIFACT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class PublicationArtifact:
    relative_path: str
    payload: bytes
    lane: Optional[str] = None
    schema_id: Optional[str] = None
    artifact_uid: Optional[str] = None


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


@dataclass(frozen=True)
class RemoteReadback:
    commit: str
    artifact_digests: Mapping[str, str]
    verified: bool


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

    def __init__(self, repo_root: Path, scratch_root: Path, remote: str = "origin") -> None:
        self.repo_root = repo_root.resolve(strict=True)
        self.scratch_root = scratch_root.resolve(strict=True)
        self.remote = remote

    def _run(
        self,
        args: Sequence[str],
        *,
        cwd: Optional[Path] = None,
        timeout: int = 120,
        allow_cleanup_force: bool = False,
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
        if result.returncode != 0:
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

    def write_artifacts(self, worktree: Path, artifacts: Sequence[PublicationArtifact]) -> None:
        from .core import atomic_write_bytes

        for artifact in artifacts:
            target = worktree.joinpath(*PurePosixPath(artifact.relative_path).parts)
            current = worktree
            for part in PurePosixPath(artifact.relative_path).parts[:-1]:
                current = current / part
                if current.exists():
                    info = os.lstat(str(current))
                    if not os.path.isdir(current) or stat.S_ISLNK(info.st_mode):
                        raise AutoRuntimeError("PUBLICATION_PARENT_SYMLINK_OR_NON_DIRECTORY")
                else:
                    current.mkdir(mode=0o755)
            atomic_write_bytes(target, artifact.payload, mode=0o644)

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
            payload = self._run(
                ("git", "show", f"{raw}:{artifact.relative_path}"), timeout=60
            ).stdout
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
    ) -> None:
        if trusted_mode not in {"CANDIDATE", "ACTIVE"}:
            raise AutoRuntimeError("PUBLICATION_TRUST_MODE_INVALID")
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.backend = backend
        self.trusted_mode = trusted_mode
        self.lock = lock
        self.activation_handshake = activation_handshake

    @staticmethod
    def _safe_relative(path: str) -> None:
        parsed = PurePosixPath(path)
        if (
            parsed.is_absolute()
            or not parsed.parts
            or any(
                part in {"", ".", ".."} or part.casefold() == ".git"
                for part in parsed.parts
            )
        ):
            raise AutoRuntimeError("PUBLICATION_PATH_INVALID")
        if "\\" in path or path.endswith("/"):
            raise AutoRuntimeError("PUBLICATION_PATH_INVALID")

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

        paths = []
        uids = set()
        for artifact in request.artifacts:
            self._safe_relative(artifact.relative_path)
            if not isinstance(artifact.payload, bytes):
                raise AutoRuntimeError("PUBLICATION_ARTIFACT_PAYLOAD_INVALID")
            if (
                request.authority == "COORDINATED_ACTIVATION"
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
                if (
                    artifact.lane is None
                    or artifact.schema_id is None
                    or artifact.artifact_uid is None
                ):
                    raise AutoRuntimeError(
                        "PUBLICATION_ACTIVE_ARTIFACT_METADATA_REQUIRED"
                    )
                _validate_artifact_target(
                    artifact.lane,
                    artifact.schema_id,
                    artifact.relative_path,
                )
                validate_public_serialization(
                    artifact.payload,
                    self.contract,
                    artifact.schema_id,
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
