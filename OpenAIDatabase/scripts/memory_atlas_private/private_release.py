from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..validate_private_encrypted_backup_policy import (
    PrivateBackupPolicyError,
    validate_policy as validate_private_backup_policy,
)
from .hashing import sha256_file
from .models import InventoryRecord


class PrivateReleaseBackupError(RuntimeError):
    """Fail-closed error that never embeds plaintext backup content."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrivateReleaseBackupError("backup_policy_unreadable") from exc
    if not isinstance(value, dict):
        raise PrivateReleaseBackupError("backup_policy_invalid")
    return value


def _command_path(env_key: str, candidates: Sequence[Path | str]) -> str:
    configured = os.environ.get(env_key, "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
        raise PrivateReleaseBackupError(f"{env_key.lower()}_unavailable")
    for raw in candidates:
        candidate = Path(raw).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise PrivateReleaseBackupError(f"{env_key.lower()}_unavailable")


def _safe_archive_path(source_id: str, relative_path: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", source_id):
        raise PrivateReleaseBackupError("source_id_invalid")
    relative = PurePosixPath(relative_path.replace("\\", "/"))
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise PrivateReleaseBackupError("source_relative_path_invalid")
    return PurePosixPath("sources", source_id, *relative.parts).as_posix()


@dataclass(frozen=True)
class BackupPolicy:
    repository: str
    max_part_bytes: int
    max_parts: int
    tag_prefix: str
    retention_count: int
    key_id: str
    keychain_account: str
    recipient: str
    recipient_fingerprint: str
    logical_sources: tuple[str, ...]

    @classmethod
    def load(cls, private_path: Path, public_path: Path) -> "BackupPolicy":
        private = _read_json(private_path)
        public = _read_json(public_path)
        try:
            validate_private_backup_policy(private, public, require_ready=True)
        except PrivateBackupPolicyError as exc:
            raise PrivateReleaseBackupError("backup_policy_validation_failed") from exc
        release = private["release"]
        private_key = private["unified_key"]
        public_key = public["unified_key"]
        recipient = str(public_key["public_recipient"])
        fingerprint = hashlib.sha256(recipient.encode("ascii")).hexdigest()
        if fingerprint != public_key.get("recipient_fingerprint"):
            raise PrivateReleaseBackupError("recipient_fingerprint_mismatch")
        return cls(
            repository=str(release["repository"]),
            max_part_bytes=int(release["max_ciphertext_part_bytes"]),
            max_parts=int(release["max_parts"]),
            tag_prefix=str(release["automatic_release_tag_prefix"]),
            retention_count=int(release["automatic_release_retention_count"]),
            key_id=str(private_key["key_id"]),
            keychain_account=str(private_key["keychain_account"]),
            recipient=recipient,
            recipient_fingerprint=fingerprint,
            logical_sources=tuple(str(item) for item in private["scope"]["logical_sources"]),
        )


@dataclass(frozen=True)
class CiphertextPart:
    path: Path
    sha256: str
    size_bytes: int
    part_number: int


class _PartWriter:
    def __init__(self, directory: Path, max_part_bytes: int, max_parts: int):
        self.directory = directory
        self.max_part_bytes = max_part_bytes
        self.max_parts = max_parts
        self._handle: Any = None
        self._hasher: Any = None
        self._size = 0
        self._number = 0
        self.parts: list[CiphertextPart] = []

    def _open_part(self) -> None:
        self._number += 1
        if self._number > self.max_parts:
            raise PrivateReleaseBackupError("ciphertext_part_limit_exceeded")
        path = self.directory / f"payload.part-{self._number:04d}.age"
        self._handle = path.open("xb")
        self._hasher = hashlib.sha256()
        self._size = 0

    def _close_part(self) -> None:
        if self._handle is None:
            return
        path = Path(self._handle.name)
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        self.parts.append(
            CiphertextPart(
                path=path,
                sha256=self._hasher.hexdigest(),
                size_bytes=self._size,
                part_number=self._number,
            )
        )
        self._handle = None
        self._hasher = None
        self._size = 0

    def write(self, payload: bytes) -> None:
        view = memoryview(payload)
        while view:
            if self._handle is None:
                self._open_part()
            available = self.max_part_bytes - self._size
            chunk = view[:available]
            self._handle.write(chunk)
            self._hasher.update(chunk)
            self._size += len(chunk)
            view = view[len(chunk) :]
            if self._size == self.max_part_bytes:
                self._close_part()

    def close(self) -> list[CiphertextPart]:
        self._close_part()
        if not self.parts:
            raise PrivateReleaseBackupError("ciphertext_empty")
        return list(self.parts)

    def abort(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


class KeychainIdentity:
    def __init__(self, *, service: str, account: str):
        self.service = service
        self.account = account

    def load(self) -> bytearray:
        completed = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-a",
                self.account,
                "-s",
                self.service,
                "-w",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
        value = bytearray(completed.stdout.strip())
        if completed.returncode != 0 or not value.startswith(b"AGE-SECRET-KEY-"):
            for index in range(len(value)):
                value[index] = 0
            raise PrivateReleaseBackupError("private_identity_unavailable")
        return value


class GithubReleaseClient:
    def __init__(self, repository: str, gh: str):
        self.repository = repository
        self.gh = gh

    def _run(
        self,
        args: Sequence[str],
        *,
        timeout: int = 3600,
        repository_flag: bool = True,
    ) -> str:
        command = [self.gh, *args]
        if repository_flag:
            command.extend(["--repo", self.repository])
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        if completed.returncode != 0:
            operation = {
                ("repo", "view"): "repo_view",
                ("release", "create"): "release_create",
                ("release", "upload"): "release_upload",
                ("release", "download"): "release_download",
                ("release", "view"): "release_view",
                ("release", "edit"): "release_edit",
                ("release", "list"): "release_list",
                ("release", "delete"): "release_delete",
            }.get(tuple(args[:2]), "unknown")
            raise PrivateReleaseBackupError(
                f"github_release_command_failed:{operation}"
            )
        return completed.stdout

    def assert_private_repository(self) -> None:
        payload = json.loads(
            self._run(
                ["repo", "view", self.repository, "--json", "visibility,nameWithOwner"],
                repository_flag=False,
            )
        )
        if payload.get("visibility") != "PRIVATE" or payload.get("nameWithOwner") != self.repository:
            raise PrivateReleaseBackupError("github_repository_scope_invalid")

    def create_draft(self, tag: str, title: str) -> None:
        self._run(
            [
                "release",
                "create",
                tag,
                "--draft",
                "--latest=false",
                "--title",
                title,
                "--notes",
                "Ciphertext-only automatic backup. Verify manifest and isolated restore receipt before use.",
            ]
        )

    def upload(self, tag: str, paths: Sequence[Path]) -> None:
        self._run(["release", "upload", tag, *(str(path) for path in paths)])

    def download(self, tag: str, destination: Path) -> None:
        self._run(["release", "download", tag, "--dir", str(destination), "--clobber"])

    def view(self, tag: str) -> dict[str, Any]:
        value = json.loads(self._run(["release", "view", tag, "--json", "assets,isDraft,url,tagName"]))
        if not isinstance(value, dict):
            raise PrivateReleaseBackupError("github_release_view_invalid")
        return value

    def publish(self, tag: str) -> None:
        self._run(["release", "edit", tag, "--draft=false", "--latest=false"])

    def enforce_retention(self, prefix: str, keep: int) -> list[str]:
        payload = json.loads(
            self._run(
                [
                    "release",
                    "list",
                    "--limit",
                    "100",
                    "--json",
                    "tagName,isDraft,publishedAt,createdAt",
                ]
            )
        )
        candidates = [
            row
            for row in payload
            if isinstance(row, dict)
            and str(row.get("tagName", "")).startswith(prefix)
            and row.get("isDraft") is False
        ]
        candidates.sort(
            key=lambda row: str(row.get("publishedAt") or row.get("createdAt") or ""),
            reverse=True,
        )
        deleted: list[str] = []
        for row in candidates[keep:]:
            tag = str(row["tagName"])
            self._run(["release", "delete", tag, "--cleanup-tag", "--yes"])
            deleted.append(tag)
        return deleted


def _derive_recipient(age_keygen: str, identity: bytearray) -> str:
    read_fd, write_fd = os.pipe()
    try:
        process = subprocess.Popen(
            [age_keygen, "-y", f"/dev/fd/{read_fd}"],
            pass_fds=(read_fd,),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        os.close(read_fd)
        read_fd = -1
        os.write(write_fd, bytes(identity) + b"\n")
        os.close(write_fd)
        write_fd = -1
        stdout, _ = process.communicate(timeout=30)
    finally:
        if read_fd >= 0:
            os.close(read_fd)
        if write_fd >= 0:
            os.close(write_fd)
    recipient = stdout.decode("ascii", errors="ignore").strip()
    if process.returncode != 0 or not recipient.startswith("age1"):
        raise PrivateReleaseBackupError("private_identity_validation_failed")
    return recipient


def _archive_manifest(records: Sequence[InventoryRecord], *, backup_id: str, created_at: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        archive_path = _safe_archive_path(record.source_id, record.relative_path)
        if archive_path in seen:
            raise PrivateReleaseBackupError("duplicate_archive_path")
        seen.add(archive_path)
        files.append(
            {
                "archive_path": archive_path,
                "source_id": record.source_id,
                "relative_path": record.relative_path,
                "sha256": record.sha256,
                "size_bytes": record.size_bytes,
                "mtime_ns": record.mtime_ns,
            }
        )
    return {
        "schema_version": "memory_atlas.encrypted_archive_manifest.v1",
        "backup_id": backup_id,
        "created_at": created_at,
        "files": files,
    }


def _encrypt_archive(
    *,
    records: Sequence[InventoryRecord],
    manifest: Mapping[str, Any],
    recipient: str,
    age: str,
    directory: Path,
    max_part_bytes: int,
    max_parts: int,
) -> list[CiphertextPart]:
    writer = _PartWriter(directory, max_part_bytes, max_parts)
    errors: list[BaseException] = []
    process = subprocess.Popen(
        [age, "--encrypt", "--recipient", recipient],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise PrivateReleaseBackupError("age_pipe_unavailable")

    def drain_ciphertext() -> None:
        try:
            while True:
                chunk = process.stdout.read(8 * 1024 * 1024)
                if not chunk:
                    break
                writer.write(chunk)
        except BaseException as exc:  # propagated in the main thread
            errors.append(exc)
            process.kill()

    reader = threading.Thread(target=drain_ciphertext, name="memory-atlas-age-reader", daemon=True)
    reader.start()
    try:
        encoded_manifest = json.dumps(
            manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8") + b"\n"
        with tarfile.open(fileobj=process.stdin, mode="w|gz", format=tarfile.PAX_FORMAT) as archive:
            info = tarfile.TarInfo("MANIFEST.json")
            info.size = len(encoded_manifest)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(encoded_manifest))
            for record in records:
                source = Path(record.materialized_path)
                if not source.is_file() or sha256_file(source) != record.sha256:
                    raise PrivateReleaseBackupError("source_snapshot_unstable")
                info = archive.gettarinfo(str(source), arcname=_safe_archive_path(record.source_id, record.relative_path))
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mode = 0o600
                with source.open("rb") as handle:
                    archive.addfile(info, handle)
        process.stdin.close()
        reader.join()
        stderr = process.stderr.read()
        returncode = process.wait(timeout=60)
        if errors:
            raise errors[0]
        if returncode != 0:
            raise PrivateReleaseBackupError("age_encryption_failed")
        return writer.close()
    except BaseException:
        writer.abort()
        if process.poll() is None:
            process.kill()
        reader.join(timeout=5)
        process.wait(timeout=10)
        raise


def _write_release_manifest(
    *,
    path: Path,
    policy: BackupPolicy,
    backup_id: str,
    created_at: str,
    parts: Sequence[CiphertextPart],
) -> str:
    payload = {
        "schema_version": "memory_atlas.private_release_manifest.v1",
        "backup_id": backup_id,
        "created_at": created_at,
        "key_id": policy.key_id,
        "recipient_fingerprint": policy.recipient_fingerprint,
        "logical_source_set": list(policy.logical_sources),
        "parts": [
            {
                "schema_version": "memory_atlas.private_release_part.v1",
                "backup_id": backup_id,
                "created_at": created_at,
                "key_id": policy.key_id,
                "recipient_fingerprint": policy.recipient_fingerprint,
                "ciphertext_sha256": part.sha256,
                "ciphertext_size_bytes": part.size_bytes,
                "part_number": part.part_number,
                "part_count": len(parts),
                "logical_source_set": list(policy.logical_sources),
            }
            for part in parts
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest()


def _verify_remote_assets(
    *,
    release: Mapping[str, Any],
    remote_dir: Path,
    local_manifest: Path,
    manifest_sha256: str,
    parts: Sequence[CiphertextPart],
) -> list[Path]:
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise PrivateReleaseBackupError("github_release_assets_invalid")
    expected_sizes = {part.path.name: part.size_bytes for part in parts}
    expected_sizes[local_manifest.name] = local_manifest.stat().st_size
    observed_sizes = {
        str(row.get("name")): int(row.get("size", -1))
        for row in assets
        if isinstance(row, dict)
    }
    if observed_sizes != expected_sizes:
        raise PrivateReleaseBackupError("github_release_asset_inventory_mismatch")
    remote_manifest = remote_dir / local_manifest.name
    if sha256_file(remote_manifest) != manifest_sha256:
        raise PrivateReleaseBackupError("remote_manifest_hash_mismatch")
    remote_parts: list[Path] = []
    for part in parts:
        remote = remote_dir / part.path.name
        if not remote.is_file() or sha256_file(remote) != part.sha256:
            raise PrivateReleaseBackupError("remote_ciphertext_hash_mismatch")
        remote_parts.append(remote)
    return remote_parts


def _restore_archive(
    *,
    parts: Sequence[Path],
    destination: Path,
    age: str,
    identity: bytearray,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen(
        [age, "--decrypt", "--identity", f"/dev/fd/{read_fd}"],
        pass_fds=(read_fd,),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    os.close(read_fd)
    os.write(write_fd, bytes(identity) + b"\n")
    os.close(write_fd)
    if process.stdin is None or process.stdout is None or process.stderr is None:
        process.kill()
        raise PrivateReleaseBackupError("age_restore_pipe_unavailable")
    feed_errors: list[BaseException] = []

    def feed_ciphertext() -> None:
        try:
            for part in parts:
                with part.open("rb") as handle:
                    shutil.copyfileobj(handle, process.stdin, length=8 * 1024 * 1024)
            process.stdin.close()
        except BaseException as exc:
            feed_errors.append(exc)
            process.kill()

    feeder = threading.Thread(target=feed_ciphertext, name="memory-atlas-age-feeder", daemon=True)
    feeder.start()
    manifest: dict[str, Any] | None = None
    restored: dict[str, dict[str, Any]] = {}
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|gz") as archive:
            for member in archive:
                if not member.isfile():
                    raise PrivateReleaseBackupError("restore_archive_member_invalid")
                stream = archive.extractfile(member)
                if stream is None:
                    raise PrivateReleaseBackupError("restore_archive_member_unreadable")
                if member.name == "MANIFEST.json":
                    value = json.loads(stream.read())
                    if not isinstance(value, dict):
                        raise PrivateReleaseBackupError("restore_manifest_invalid")
                    manifest = value
                    continue
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
                    raise PrivateReleaseBackupError("restore_path_invalid")
                target = (destination / Path(*pure.parts)).resolve()
                target.relative_to(destination.resolve())
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as handle:
                    shutil.copyfileobj(stream, handle, length=8 * 1024 * 1024)
                restored[member.name] = {
                    "sha256": sha256_file(target),
                    "size_bytes": target.stat().st_size,
                }
        feeder.join()
        stderr = process.stderr.read()
        returncode = process.wait(timeout=60)
        if feed_errors or returncode != 0:
            raise PrivateReleaseBackupError("isolated_restore_decryption_failed")
    except BaseException:
        if process.poll() is None:
            process.kill()
        feeder.join(timeout=5)
        process.wait(timeout=10)
        raise
    if manifest is None or manifest.get("schema_version") != "memory_atlas.encrypted_archive_manifest.v1":
        raise PrivateReleaseBackupError("restore_manifest_missing")
    expected = {
        str(row["archive_path"]): {
            "sha256": str(row["sha256"]),
            "size_bytes": int(row["size_bytes"]),
        }
        for row in manifest.get("files", [])
        if isinstance(row, dict)
    }
    if restored != expected:
        raise PrivateReleaseBackupError("isolated_restore_hash_mismatch")
    return {
        "state": "PASS",
        "restored_files": len(restored),
        "restored_bytes": sum(int(row["size_bytes"]) for row in restored.values()),
        "all_hashes_match": True,
    }


class PrivateReleaseBackup:
    def __init__(
        self,
        *,
        private_policy_path: Path,
        public_policy_path: Path,
        identity_loader: Callable[[], bytearray] | None = None,
        release_client: GithubReleaseClient | None = None,
    ):
        self.policy = BackupPolicy.load(private_policy_path, public_policy_path)
        self.age = _command_path(
            "MEMORY_ATLAS_AGE_BIN",
            (Path.home() / ".local/bin/age", shutil.which("age") or ""),
        )
        self.age_keygen = _command_path(
            "MEMORY_ATLAS_AGE_KEYGEN_BIN",
            (Path.home() / ".local/bin/age-keygen", shutil.which("age-keygen") or ""),
        )
        self.identity_loader = identity_loader or KeychainIdentity(
            service=self.policy.key_id,
            account=self.policy.keychain_account,
        ).load
        if release_client is None:
            gh = _command_path(
                "MEMORY_ATLAS_GH_BIN",
                (Path.home() / ".local/bin/gh", shutil.which("gh") or ""),
            )
            self.release_client = GithubReleaseClient(self.policy.repository, gh)
        else:
            self.release_client = release_client

    def _preflight(self, logical_source_set: Iterable[str]) -> None:
        self.validate_logical_source_set(logical_source_set)
        self.release_client.assert_private_repository()
        identity = self.identity_loader()
        try:
            if _derive_recipient(self.age_keygen, identity) != self.policy.recipient:
                raise PrivateReleaseBackupError("private_identity_recipient_mismatch")
        finally:
            for index in range(len(identity)):
                identity[index] = 0

    def validate_logical_source_set(self, logical_source_set: Iterable[str]) -> None:
        observed_sources = tuple(logical_source_set)
        if len(observed_sources) != len(self.policy.logical_sources) or set(observed_sources) != set(
            self.policy.logical_sources
        ):
            raise PrivateReleaseBackupError("logical_source_contract_mismatch")

    def run(
        self,
        *,
        records: Sequence[InventoryRecord],
        logical_source_set: Sequence[str],
        backup_id: str,
        created_at: str,
        work_root: Path,
    ) -> dict[str, Any]:
        self._preflight(logical_source_set)
        release_root = work_root / "private-github-release"
        release_root.mkdir(parents=True, exist_ok=False)
        result: dict[str, Any] | None = None
        try:
            archive_manifest = _archive_manifest(records, backup_id=backup_id, created_at=created_at)
            parts = _encrypt_archive(
                records=records,
                manifest=archive_manifest,
                recipient=self.policy.recipient,
                age=self.age,
                directory=release_root,
                max_part_bytes=self.policy.max_part_bytes,
                max_parts=self.policy.max_parts,
            )
            public_manifest = release_root / "manifest.json"
            public_manifest_sha256 = _write_release_manifest(
                path=public_manifest,
                policy=self.policy,
                backup_id=backup_id,
                created_at=created_at,
                parts=parts,
            )
            timestamp = re.sub(r"[^0-9]", "", created_at)[:14]
            tag = f"{self.policy.tag_prefix}{timestamp}-{backup_id[-12:]}"
            self.release_client.create_draft(tag, f"Memory Atlas automatic backup {timestamp}")
            self.release_client.upload(tag, [*(part.path for part in parts), public_manifest])
            remote_dir = release_root / "remote-readback"
            remote_dir.mkdir()
            self.release_client.download(tag, remote_dir)
            release = self.release_client.view(tag)
            if release.get("isDraft") is not True or release.get("tagName") != tag:
                raise PrivateReleaseBackupError("github_release_draft_state_invalid")
            remote_parts = _verify_remote_assets(
                release=release,
                remote_dir=remote_dir,
                local_manifest=public_manifest,
                manifest_sha256=public_manifest_sha256,
                parts=parts,
            )
            identity = self.identity_loader()
            try:
                restore = _restore_archive(
                    parts=remote_parts,
                    destination=release_root / "isolated-restore",
                    age=self.age,
                    identity=identity,
                )
            finally:
                for index in range(len(identity)):
                    identity[index] = 0
            self.release_client.publish(tag)
            published = self.release_client.view(tag)
            if published.get("isDraft") is not False:
                raise PrivateReleaseBackupError("github_release_publish_failed")
            deleted = self.release_client.enforce_retention(
                self.policy.tag_prefix, self.policy.retention_count
            )
            result = {
                "schema_version": "memory_atlas.private_release_backup.v1",
                "state": "PASS",
                "backup_id": backup_id,
                "created_at": created_at,
                "key_id": self.policy.key_id,
                "recipient_fingerprint": self.policy.recipient_fingerprint,
                "repository": self.policy.repository,
                "release_tag": tag,
                "release_url": str(published.get("url", "")),
                "logical_source_set": list(self.policy.logical_sources),
                "ciphertext_part_count": len(parts),
                "ciphertext_size_bytes": sum(part.size_bytes for part in parts),
                "parts": [
                    {
                        "ciphertext_sha256": part.sha256,
                        "ciphertext_size_bytes": part.size_bytes,
                        "part_number": part.part_number,
                        "part_count": len(parts),
                    }
                    for part in parts
                ],
                "remote_readback_verified": True,
                "isolated_restore": restore,
                "retention_deleted_count": len(deleted),
            }
        finally:
            shutil.rmtree(release_root, ignore_errors=False)
        if result is None:
            raise PrivateReleaseBackupError("private_release_backup_incomplete")
        result["local_payload_cleanup"] = {
            "state": "PASS" if not release_root.exists() else "FAIL",
            "remaining_paths": 0 if not release_root.exists() else 1,
        }
        if result["local_payload_cleanup"]["state"] != "PASS":
            raise PrivateReleaseBackupError("private_release_local_cleanup_failed")
        return result
