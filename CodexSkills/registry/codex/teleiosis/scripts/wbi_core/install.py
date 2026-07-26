from __future__ import annotations

from contextlib import contextmanager
import datetime as dt
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid
from typing import Any, Dict, Iterator, List, Optional

from .io import copy_clean, load_json, safe_extract_zip, sha256_file, sha256_tree, utc_now, write_json
from .process import run_bounded
from .validation import detect_profile, validate_skill

TERMINAL_TRANSACTION_STATES = {
    "COMMITTED", "RECOVERED_COMMITTED", "ROLLED_BACK", "RECOVERED_ROLLED_BACK", "ROLLED_BACK_BY_REQUEST", "FAILED", "ABORTED_NO_SWITCH",
}


class InstallBusy(RuntimeError):
    pass


def _ensure_private_directory(path: Path) -> Path:
    """Create one controller-owned directory without following a link."""
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        raise ValueError("control path must be a real directory: %s" % path)
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("control path must not be a symlink: %s" % path)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def _transaction_directory(skills_root: Path, *, create: bool = True) -> Path:
    path = skills_root / ".wbi-install-transactions"
    if create:
        return _ensure_private_directory(path)
    if path.is_symlink() or (path.exists() and not path.is_dir()):
        raise ValueError("install transaction control path is linked or invalid")
    return path


@contextmanager
def _install_lock(skills_root: Path) -> Iterator[None]:
    """Hold a process-scoped non-blocking lock without stale-lock deadlocks.

    The lock file is opened with ``O_NOFOLLOW`` where supported so an attacker
    cannot redirect controller writes through a pre-created symbolic link.
    """
    lock_path = skills_root / ".wbi-install.lock"
    if lock_path.is_symlink() or (lock_path.exists() and not lock_path.is_file()):
        raise ValueError("install lock control path is linked or invalid")
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(str(lock_path), flags, 0o600)
    handle = os.fdopen(descriptor, "r+b", buffering=0)
    locked = False
    try:
        if os.name == "posix":
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError as exc:
                raise InstallBusy("another Skill installation is active in this skills root") from exc
        else:  # pragma: no cover - Windows runtime
            import msvcrt
            try:
                handle.seek(0)
                if os.fstat(handle.fileno()).st_size == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError as exc:
                raise InstallBusy("another Skill installation is active in this skills root") from exc
        yield
    finally:
        if locked:
            try:
                if os.name == "posix":
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                else:  # pragma: no cover - Windows runtime
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        handle.close()


def _fsync_directory(path: Path) -> None:
    if os.name != "posix":  # pragma: no cover - best effort on Windows
        return
    try:
        descriptor = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _freeze_archive(source: Path, destination: Path) -> Dict[str, Any]:
    """Copy a regular archive to a private snapshot and detect source mutation."""
    maximum = int(os.environ.get("WBI_MAX_ARCHIVE_BYTES", str(512 * 1024 * 1024)))
    if maximum <= 0:
        raise ValueError("WBI_MAX_ARCHIVE_BYTES must be positive")
    before_size = source.stat().st_size
    if before_size > maximum:
        raise ValueError("archive exceeds WBI_MAX_ARCHIVE_BYTES")
    before_hash = sha256_file(source)
    with source.open("rb") as reader, destination.open("xb") as writer:
        shutil.copyfileobj(reader, writer, length=1024 * 1024)
        writer.flush()
        os.fsync(writer.fileno())
    frozen_hash = sha256_file(destination)
    after_size = source.stat().st_size
    after_hash = sha256_file(source)
    if before_size != after_size or before_hash != after_hash or frozen_hash != before_hash:
        destination.unlink(missing_ok=True)
        raise ValueError("archive changed while the installer was freezing its input")
    return {"archive_sha256": frozen_hash, "archive_bytes": before_size, "source_stable": True}


def _optimizer_timeout(arguments: List[str]) -> int:
    """Return a configurable bounded timeout without conflating smoke and deep checks."""
    legacy = os.environ.get("WBI_COMMAND_TIMEOUT_SECONDS")
    if legacy:
        value = int(legacy)
    elif arguments and arguments[0] == "self-test":
        value = int(os.environ.get("WBI_SELF_TEST_TIMEOUT_SECONDS", "600"))
    else:
        value = int(os.environ.get("WBI_FAST_CHECK_TIMEOUT_SECONDS", "90"))
    if value <= 0:
        raise ValueError("optimizer command timeout must be positive")
    return value


def _optimizer_check(
    root: Path, arguments: List[str], expected_genesis_hash: str,
    expected_effective_genesis_hash: str = "",
) -> Dict[str, Any]:
    command = [sys.executable, str(root / "scripts/wbi.py")] + arguments
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "WBI_NESTED_SELF_TEST": "1"}
    env["WBI_EXPECTED_GENESIS_SHA256"] = expected_genesis_hash
    if expected_effective_genesis_hash:
        env["WBI_EXPECTED_EFFECTIVE_GENESIS_SHA256"] = expected_effective_genesis_hash
    timeout = _optimizer_timeout(arguments)
    completed = run_bounded(command, cwd=root, env=env, timeout_seconds=timeout)
    return {
        "command": arguments, "returncode": completed["returncode"],
        "timed_out": completed["timed_out"], "timeout_seconds": completed["timeout_seconds"],
        "elapsed_seconds": completed["elapsed_seconds"],
        "stdout": completed["stdout"][-4000:], "stderr": completed["stderr"][-4000:],
    }


def _transaction_path(skills_root: Path, transaction_id: str) -> Path:
    return _transaction_directory(skills_root) / (transaction_id + ".json")


def _update_transaction(path: Path, transaction: Dict[str, Any], status: str, **updates: Any) -> None:
    if path.is_symlink():
        raise ValueError("install transaction receipt must not be a symlink")
    _ensure_private_directory(path.parent)
    transaction.update(updates)
    transaction["status"] = status
    transaction["updated_at"] = utc_now()
    write_json(path, transaction)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    _fsync_directory(path.parent)


def _backup_tree_hash(backup: Path, schema_version: str) -> str:
    """Hash a backup using the receipt schema that created it.

    Schema 1.0 excluded the manifest. Schema 1.1 covers every restored byte except
    the receipt itself, so a tampered integrity manifest cannot pass rollback.
    """
    excluded = {".wbi-backup-receipt.json"}
    if schema_version == "1.0":
        excluded.add("MANIFEST.sha256")
    return sha256_tree(backup, exclude=excluded)


def inspect_install_transaction(
    skills_root: Path,
    transaction_id: str = "",
    *,
    verify_installed: bool = False,
    expected_genesis_hash: str = "",
    expected_effective_genesis_hash: str = "",
    profile: str = "auto",
) -> Dict[str, Any]:
    """Inspect one durable install receipt without mutating installation state."""
    skills_root = skills_root.resolve()
    try:
        transaction_dir = _transaction_directory(skills_root, create=False)
    except ValueError as exc:
        return {"status": "BLOCKED", "errors": [str(exc)]}
    if not transaction_dir.is_dir():
        return {"status": "NOT_FOUND", "errors": ["install transaction directory missing"]}
    if transaction_id:
        if not transaction_id.replace("-", "").isalnum():
            return {"status": "FAIL", "errors": ["invalid transaction id"]}
        path = transaction_dir / (transaction_id + ".json")
        candidates = [path] if path.is_file() else []
    else:
        candidates = sorted(
            (item for item in transaction_dir.glob("*.json") if item.is_file() and not item.is_symlink()),
            key=lambda item: item.stat().st_mtime_ns, reverse=True,
        )
    if not candidates:
        return {"status": "NOT_FOUND", "errors": ["install transaction receipt not found"]}
    path = candidates[0]
    if path.is_symlink():
        return {"status": "BLOCKED", "transaction_receipt": str(path), "errors": ["install transaction receipt must not be a symlink"]}
    try:
        transaction = load_json(path)
    except Exception as exc:
        return {"status": "BLOCKED", "transaction_receipt": str(path), "errors": ["invalid transaction receipt: %s" % exc]}
    observed = str(transaction.get("status") or "UNKNOWN")
    result: Dict[str, Any] = {
        "status": "PASS", "transaction_receipt": str(path),
        "transaction_id": transaction.get("transaction_id"),
        "observed_transaction_status": observed,
        "terminal": observed in TERMINAL_TRANSACTION_STATES,
        "transaction": transaction,
    }
    if not verify_installed:
        return result
    destination_value = transaction.get("destination")
    if not isinstance(destination_value, str) or not destination_value:
        result["status"] = "BLOCKED"
        result["installed_verification"] = {"status": "BLOCKED", "errors": ["transaction destination missing"]}
        return result
    destination = Path(destination_value).resolve()
    if destination.parent != skills_root:
        result["status"] = "BLOCKED"
        result["installed_verification"] = {"status": "BLOCKED", "errors": ["transaction destination escaped skills root"]}
        return result
    if observed not in {"COMMITTED", "RECOVERED_COMMITTED"}:
        result["installed_verification"] = {"status": "NOT_APPLICABLE", "reason": "transaction is not a committed installation"}
        return result
    transaction_profile = str(transaction.get("profile") or profile)
    expected = str(transaction.get("expected_genesis_hash") or expected_genesis_hash)
    expected_effective = str(transaction.get("expected_effective_genesis_hash") or expected_effective_genesis_hash)
    if not destination.is_dir() or destination.is_symlink():
        result["status"] = "BLOCKED"
        result["installed_verification"] = {"status": "FAIL", "errors": ["committed destination missing or is a symlink"]}
        return result
    validation = validate_skill(
        destination, strict=True,
        expected_genesis_hash=expected if transaction_profile == "optimizer" else "",
        expected_effective_genesis_hash=expected_effective if transaction_profile == "optimizer" else "",
        profile=transaction_profile,
    )
    expected_tree = str(transaction.get("destination_tree_hash") or transaction.get("staged_tree_hash") or "")
    actual_tree = sha256_tree(destination, exclude={"MANIFEST.sha256"})
    tree_match = bool(expected_tree) and actual_tree == expected_tree
    verification_status = "PASS" if validation.get("status") == "PASS" and tree_match else "FAIL"
    result["installed_verification"] = {
        "status": verification_status, "validation": validation.get("status"),
        "tree_hash_expected": expected_tree, "tree_hash_actual": actual_tree, "tree_hash_match": tree_match,
    }
    if verification_status != "PASS":
        result["status"] = "BLOCKED"
    return result


def _valid_backup_for_destination(destination: Path, backup: Path) -> bool:
    if destination.parent != backup.parent or not backup.is_dir() or backup.is_symlink():
        return False
    receipt_path = backup / ".wbi-backup-receipt.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return False
    try:
        receipt = load_json(receipt_path)
        schema_version = str(receipt.get("schema_version") or "")
        if schema_version not in {"1.0", "1.1"}:
            return False
        expected_tree = _backup_tree_hash(backup, schema_version)
    except Exception:
        return False
    return bool(
        receipt.get("destination_name") == destination.name
        and receipt.get("backup_name") == backup.name
        and receipt.get("source_tree_hash") == expected_tree
    )


def _safe_incoming_path(skills_root: Path, destination_name: str, value: Any) -> Optional[Path]:
    if not isinstance(value, str) or not value:
        return None
    candidate = Path(value).resolve()
    prefix = ".%s.incoming." % destination_name
    if candidate.parent != skills_root or not candidate.name.startswith(prefix) or candidate.is_symlink():
        return None
    return candidate


def _reconstruct_interrupted_backup_receipt(destination: Path, backup: Path, transaction: Dict[str, Any]) -> bool:
    """Close the tiny crash window after rename but before backup receipt write."""
    if transaction.get("status") != "BACKUP_PLANNED":
        return False
    if destination.parent != backup.parent or backup.is_symlink() or not backup.is_dir():
        return False
    if not backup.name.startswith(".%s.backup." % destination.name):
        return False
    receipt_path = backup / ".wbi-backup-receipt.json"
    if receipt_path.exists():
        return False
    predecessor = str(transaction.get("predecessor_tree_hash") or "")
    if len(predecessor) != 64 or sha256_tree(backup) != predecessor:
        return False
    receipt = {
        "schema_version": "1.1", "created_at": utc_now(),
        "destination_name": destination.name, "backup_name": backup.name,
        "source_tree_hash": predecessor,
        "install_transaction_id": transaction.get("transaction_id"),
        "reconstructed_after_interruption": True,
    }
    write_json(receipt_path, receipt)
    try:
        receipt_path.chmod(0o444)
    except OSError:
        pass
    _fsync_directory(backup)
    return _valid_backup_for_destination(destination, backup)


def _recover_install_transactions_unlocked(
    skills_root: Path,
    expected_genesis_hash: str = "",
    profile: str = "auto",
    destination_name: str = "teleiosis",
    expected_effective_genesis_hash: str = "",
) -> Dict[str, Any]:
    """Reconcile interrupted installs from durable transaction receipts.

    A valid switched destination is committed; otherwise a valid generated
    backup is restored. Ambiguous evidence is never guessed and remains blocked.
    """
    skills_root = skills_root.resolve()
    results = []
    unresolved = []
    try:
        transaction_dir = _transaction_directory(skills_root, create=False)
    except ValueError as exc:
        return {"status": "BLOCKED", "recovered": [], "unresolved": [{"error": str(exc)}]}
    if not transaction_dir.is_dir():
        return {"status": "PASS", "recovered": [], "unresolved": []}
    for path in sorted(transaction_dir.glob("*.json")):
        if path.is_symlink() or not path.is_file():
            unresolved.append({"path": str(path), "error": "transaction receipt is linked or invalid"})
            continue
        try:
            transaction = load_json(path)
        except Exception as exc:
            unresolved.append({"path": str(path), "error": "invalid transaction receipt: %s" % exc})
            continue
        if transaction.get("destination_name") != destination_name or transaction.get("status") in TERMINAL_TRANSACTION_STATES:
            continue
        destination = (skills_root / destination_name).resolve()
        if destination.parent != skills_root:
            unresolved.append({"path": str(path), "error": "destination escaped skills root"})
            continue
        transaction_profile = str(transaction.get("profile") or profile)
        expected = str(transaction.get("expected_genesis_hash") or expected_genesis_hash)
        expected_effective = str(transaction.get("expected_effective_genesis_hash") or expected_effective_genesis_hash)
        staged_tree = str(transaction.get("staged_tree_hash") or "")
        destination_valid = False
        if destination.is_dir():
            validation = validate_skill(
                destination, strict=True,
                expected_genesis_hash=expected if transaction_profile == "optimizer" else "",
                expected_effective_genesis_hash=expected_effective if transaction_profile == "optimizer" else "",
                profile=transaction_profile,
            )
            destination_valid = validation.get("status") == "PASS" and bool(staged_tree) and sha256_tree(destination, exclude={"MANIFEST.sha256"}) == staged_tree
        if destination_valid:
            _update_transaction(path, transaction, "RECOVERED_COMMITTED", recovery_action="validated-existing-switched-destination")
            results.append({"transaction": str(path), "action": "RECOVERED_COMMITTED", "destination": str(destination)})
            continue
        backup_value = transaction.get("backup")
        backup = Path(str(backup_value)).resolve() if backup_value else None
        if backup and not _valid_backup_for_destination(destination, backup):
            _reconstruct_interrupted_backup_receipt(destination, backup, transaction)
        if backup and _valid_backup_for_destination(destination, backup):
            rolled = _rollback_install_unlocked(destination, backup)
            if rolled.get("status") == "PASS":
                _update_transaction(path, transaction, "RECOVERED_ROLLED_BACK", recovery_action="restored-valid-backup")
                results.append({"transaction": str(path), "action": "RECOVERED_ROLLED_BACK", "destination": str(destination)})
                continue

        status = str(transaction.get("status") or "")
        predecessor = str(transaction.get("predecessor_tree_hash") or "")
        incoming = _safe_incoming_path(skills_root, destination_name, transaction.get("incoming"))
        # A fresh install can be abandoned before the atomic switch. Remove only
        # a controller-generated incoming path whose identity is fully bounded.
        if not destination.exists() and not backup_value and status in {"PREPARED", "INCOMING_PLANNED", "INCOMING_READY"}:
            if incoming and incoming.exists():
                shutil.rmtree(str(incoming), ignore_errors=True)
            _update_transaction(path, transaction, "ABORTED_NO_SWITCH", recovery_action="no-filesystem-switch-observed")
            results.append({"transaction": str(path), "action": "ABORTED_NO_SWITCH"})
            continue
        # If interruption occurred before the predecessor rename, the original
        # tree is still authoritative and can be closed without modifying it.
        if (
            destination.is_dir() and not backup and status in {"PREPARED", "BACKUP_PLANNED"}
            and len(predecessor) == 64 and sha256_tree(destination) == predecessor
        ):
            if incoming and incoming.exists():
                shutil.rmtree(str(incoming), ignore_errors=True)
            _update_transaction(path, transaction, "ABORTED_NO_SWITCH", recovery_action="validated-original-predecessor-before-switch")
            results.append({"transaction": str(path), "action": "ABORTED_NO_SWITCH", "destination": str(destination)})
            continue
        unresolved.append({"path": str(path), "status": transaction.get("status"), "error": "insufficient evidence for safe automatic recovery"})
    return {"status": "PASS" if not unresolved else "BLOCKED", "recovered": results, "unresolved": unresolved}


def recover_install_transactions(
    skills_root: Path,
    expected_genesis_hash: str = "",
    profile: str = "auto",
    destination_name: str = "teleiosis",
    expected_effective_genesis_hash: str = "",
) -> Dict[str, Any]:
    """Safely reconcile interrupted installs while excluding concurrent writers."""
    skills_root_input = Path(skills_root)
    if skills_root_input.exists() and skills_root_input.is_symlink():
        return {"status": "BLOCKED", "recovered": [], "unresolved": [{"error": "skills root must not be a symlink"}]}
    skills_root = skills_root_input.resolve()
    skills_root.mkdir(parents=True, exist_ok=True)
    try:
        with _install_lock(skills_root):
            return _recover_install_transactions_unlocked(
                skills_root, expected_genesis_hash, profile, destination_name, expected_effective_genesis_hash
            )
    except (InstallBusy, ValueError, OSError) as exc:
        return {"status": "BLOCKED", "recovered": [], "unresolved": [{"error": str(exc)}]}


def _rollback_after_failure(destination: Path, backup: Optional[Path]) -> Dict[str, Any]:
    if backup and backup.exists():
        return _rollback_install_unlocked(destination, backup)
    shutil.rmtree(str(destination), ignore_errors=True)
    _fsync_directory(destination.parent)
    return {"status": "PASS", "action": "removed-new-install-without-predecessor"}


def install_archive(
    archive: Path,
    skills_root: Path,
    expected_genesis_hash: str = "",
    replace: bool = False,
    profile: str = "auto",
    verification_level: str = "structural",
    expected_archive_sha256: str = "",
    expected_effective_genesis_hash: str = "",
) -> Dict[str, Any]:
    archive_input, skills_root_input = Path(archive), Path(skills_root)
    if archive_input.is_symlink():
        return {"status": "FAIL", "stage": "input", "errors": ["archive path must not be a symlink"]}
    if skills_root_input.exists() and skills_root_input.is_symlink():
        return {"status": "BLOCKED", "stage": "input", "errors": ["skills root must not be a symlink"]}
    archive, skills_root = archive_input.resolve(), skills_root_input.resolve()
    if verification_level not in {"structural", "release", "deep"}:
        return {"status": "FAIL", "stage": "verification-level", "errors": ["verification level must be structural, release or deep"]}
    if not archive.is_file():
        return {"status": "FAIL", "stage": "input", "errors": ["archive missing"]}
    normalized_archive_anchor = str(expected_archive_sha256 or "").strip().lower()
    if normalized_archive_anchor and (len(normalized_archive_anchor) != 64 or any(ch not in "0123456789abcdef" for ch in normalized_archive_anchor)):
        return {"status": "FAIL", "stage": "external-archive-anchor", "errors": ["expected archive SHA-256 must be 64 lowercase hexadecimal characters"]}
    if normalized_archive_anchor:
        observed_archive_hash = sha256_file(archive)
        if observed_archive_hash != normalized_archive_anchor:
            return {"status": "FAIL", "stage": "external-archive-anchor", "errors": ["archive SHA-256 does not match external trust anchor"], "archive_sha256": observed_archive_hash}
    skills_root.mkdir(parents=True, exist_ok=True)
    try:
        lock = _install_lock(skills_root)
        lock.__enter__()
    except (InstallBusy, ValueError, OSError) as exc:
        return {"status": "BLOCKED", "stage": "install-lock", "errors": [str(exc)]}
    try:
        with tempfile.TemporaryDirectory(prefix="wbi-install-", dir=str(skills_root)) as temp:
            temp_root = Path(temp)
            extract = temp_root / "extract"
            frozen_archive = temp_root / "frozen-input.zip"
            try:
                frozen = _freeze_archive(archive, frozen_archive)
                safe_extract_zip(frozen_archive, extract)
            except Exception as exc:
                return {"status": "FAIL", "stage": "archive-freeze-or-extract", "errors": [str(exc)]}
            top = [path for path in extract.iterdir()]
            if len(top) != 1 or not top[0].is_dir():
                return {"status": "FAIL", "stage": "structure", "errors": ["archive must contain exactly one top-level Skill directory"]}
            staged = top[0]
            resolved_profile = detect_profile(staged, profile)
            if resolved_profile == "optimizer" and not expected_genesis_hash:
                return {"status": "FAIL", "stage": "external-genesis-anchor", "errors": ["optimizer installation requires an external Genesis hash anchor"]}
            if resolved_profile == "optimizer" and verification_level in {"release", "deep"} and not normalized_archive_anchor:
                return {"status": "FAIL", "stage": "external-archive-anchor", "errors": ["release/deep optimizer installation requires an external archive SHA-256 anchor"]}
            effective_configured = (staged / "constitution/effective-genesis-lock.v0.0.0.2.json").is_file()
            if resolved_profile == "optimizer" and effective_configured and verification_level in {"release", "deep"} and not expected_effective_genesis_hash:
                return {"status": "FAIL", "stage": "external-effective-genesis-anchor", "errors": ["release/deep optimizer installation requires an external effective Genesis hash anchor"]}
            if normalized_archive_anchor and frozen["archive_sha256"] != normalized_archive_anchor:
                return {"status": "FAIL", "stage": "external-archive-anchor", "errors": ["frozen archive SHA-256 differs from external trust anchor"], "archive_sha256": frozen["archive_sha256"]}

            recovered = _recover_install_transactions_unlocked(
                skills_root, expected_genesis_hash, resolved_profile, staged.name, expected_effective_genesis_hash
            )
            if recovered["status"] != "PASS":
                return {"status": "BLOCKED", "stage": "recovery-required", "recovery": recovered}

            validation = validate_skill(
                staged, strict=True, expected_genesis_hash=expected_genesis_hash if resolved_profile == "optimizer" else "",
                expected_effective_genesis_hash=expected_effective_genesis_hash if resolved_profile == "optimizer" else "",
                profile=resolved_profile,
            )
            if validation["status"] != "PASS":
                return {"status": "FAIL", "stage": "validation", "validation": validation}

            checks: Dict[str, Any] = {"profile": resolved_profile, "verification_level": verification_level, "executed_target_code": False, "external_archive_anchor_verified": bool(normalized_archive_anchor)}
            if resolved_profile == "optimizer" and verification_level in {"release", "deep"}:
                verify = _optimizer_check(
                    staged, ["verify-self", "--strict", "--expected-genesis-hash", expected_genesis_hash,
                             "--expected-effective-genesis-hash", expected_effective_genesis_hash],
                    expected_genesis_hash, expected_effective_genesis_hash,
                )
                checks["verify_self"] = verify
                if verify["returncode"] != 0:
                    return {"status": "FAIL", "stage": "verify-self", "checks": checks}
                smoke_args = ["release-smoke", "--expected-genesis-hash", expected_genesis_hash,
                              "--expected-effective-genesis-hash", expected_effective_genesis_hash]
                smoke = _optimizer_check(staged, smoke_args, expected_genesis_hash, expected_effective_genesis_hash)
                checks["release_smoke"] = smoke
                checks["executed_target_code"] = True
                if smoke["returncode"] != 0:
                    return {"status": "FAIL", "stage": "release-smoke", "checks": checks}
                if verification_level == "deep" and not os.environ.get("WBI_NESTED_SELF_TEST"):
                    self_test = _optimizer_check(staged, ["self-test"], expected_genesis_hash, expected_effective_genesis_hash)
                    checks["deep_self_test"] = self_test
                    if self_test["returncode"] != 0:
                        return {"status": "FAIL", "stage": "deep-self-test", "checks": checks}
                elif verification_level == "deep":
                    checks["deep_self_test"] = {"status": "SKIPPED_NESTED_RECURSION_GUARD"}
            elif resolved_profile == "optimizer":
                checks["verify_self"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}
                checks["release_smoke"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}

            destination = skills_root / staged.name
            if destination.is_symlink():
                return {"status": "BLOCKED", "stage": "existing", "errors": ["destination must not be a symlink"]}
            if destination.exists() and not replace:
                return {"status": "BLOCKED", "stage": "existing", "errors": ["destination exists; use explicit replace to create a backup and upgrade"]}

            transaction_id = uuid.uuid4().hex
            transaction_path = _transaction_path(skills_root, transaction_id)
            transaction: Dict[str, Any] = {
                "schema_version": "1.0", "transaction_id": transaction_id,
                "created_at": utc_now(), "updated_at": utc_now(), "status": "PREPARED",
                "archive": str(archive), "archive_sha256": frozen["archive_sha256"],
                "archive_bytes": frozen["archive_bytes"], "archive_source_stable": frozen["source_stable"],
                "profile": resolved_profile, "verification_level": verification_level,
                "expected_genesis_hash": expected_genesis_hash if resolved_profile == "optimizer" else None,
                "expected_effective_genesis_hash": expected_effective_genesis_hash if resolved_profile == "optimizer" else None,
                "expected_archive_sha256": normalized_archive_anchor or None,
                "external_archive_anchor_verified": bool(normalized_archive_anchor),
                "destination_name": destination.name, "destination": str(destination),
                "staged_tree_hash": sha256_tree(staged, exclude={"MANIFEST.sha256"}),
                "predecessor_tree_hash": sha256_tree(destination) if destination.exists() else None,
                "backup": None, "incoming": None,
            }
            _update_transaction(transaction_path, transaction, "PREPARED")

            backup: Optional[Path] = None
            if destination.exists():
                stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                backup = skills_root / (".%s.backup.%s" % (destination.name, stamp))
                suffix = 1
                while backup.exists():
                    backup = skills_root / (".%s.backup.%s.%d" % (destination.name, stamp, suffix))
                    suffix += 1
                _update_transaction(transaction_path, transaction, "BACKUP_PLANNED", backup=str(backup))
                os.replace(str(destination), str(backup))
                _fsync_directory(skills_root)
                receipt_path = backup / ".wbi-backup-receipt.json"
                receipt = {
                    "schema_version": "1.1", "created_at": utc_now(), "destination_name": destination.name,
                    "backup_name": backup.name, "source_tree_hash": transaction["predecessor_tree_hash"],
                    "install_transaction_id": transaction_id,
                }
                write_json(receipt_path, receipt)
                try:
                    receipt_path.chmod(0o444)
                except OSError:
                    pass
                _update_transaction(transaction_path, transaction, "BACKUP_CREATED", backup=str(backup))

            incoming = skills_root / (".%s.incoming.%s" % (staged.name, uuid.uuid4().hex))
            try:
                _update_transaction(transaction_path, transaction, "INCOMING_PLANNED", incoming=str(incoming))
                copy_clean(staged, incoming)
                incoming_tree = sha256_tree(incoming, exclude={"MANIFEST.sha256"})
                if incoming_tree != transaction["staged_tree_hash"]:
                    raise ValueError("incoming tree hash differs from validated staged tree")
                _update_transaction(transaction_path, transaction, "INCOMING_READY", incoming=str(incoming), incoming_tree_hash=incoming_tree)
                os.replace(str(incoming), str(destination))
                _fsync_directory(skills_root)
                _update_transaction(
                    transaction_path, transaction, "SWITCHED",
                    incoming=None, destination_tree_hash=sha256_tree(destination, exclude={"MANIFEST.sha256"}),
                )
            except Exception as exc:
                shutil.rmtree(str(incoming), ignore_errors=True)
                rollback = _rollback_after_failure(destination, backup)
                _update_transaction(transaction_path, transaction, "ROLLED_BACK" if rollback.get("status") == "PASS" else "FAILED", error=str(exc), rollback=rollback)
                return {"status": "FAIL", "stage": "atomic-switch", "errors": [str(exc)], "transaction_receipt": str(transaction_path), "rollback": rollback}

            post = validate_skill(
                destination, strict=True, expected_genesis_hash=expected_genesis_hash if resolved_profile == "optimizer" else "",
                expected_effective_genesis_hash=expected_effective_genesis_hash if resolved_profile == "optimizer" else "",
                profile=resolved_profile,
            )
            if post["status"] != "PASS":
                rollback = _rollback_after_failure(destination, backup)
                _update_transaction(transaction_path, transaction, "ROLLED_BACK" if rollback.get("status") == "PASS" else "FAILED", post_validation=post, rollback=rollback)
                return {"status": "FAIL", "stage": "post-install", "validation": post, "transaction_receipt": str(transaction_path), "rollback": rollback}

            if resolved_profile == "optimizer" and verification_level in {"release", "deep"}:
                post_verify = _optimizer_check(
                    destination, ["verify-self", "--strict", "--expected-genesis-hash", expected_genesis_hash,
                                  "--expected-effective-genesis-hash", expected_effective_genesis_hash],
                    expected_genesis_hash, expected_effective_genesis_hash,
                )
                checks["post_install_verify_self"] = post_verify
                if post_verify["returncode"] != 0:
                    rollback = _rollback_after_failure(destination, backup)
                    _update_transaction(transaction_path, transaction, "ROLLED_BACK" if rollback.get("status") == "PASS" else "FAILED", checks=checks, rollback=rollback)
                    return {"status": "FAIL", "stage": "post-install-verify-self", "checks": checks, "transaction_receipt": str(transaction_path), "rollback": rollback}
                post_smoke = _optimizer_check(
                    destination, ["release-smoke", "--expected-genesis-hash", expected_genesis_hash,
                                  "--expected-effective-genesis-hash", expected_effective_genesis_hash],
                    expected_genesis_hash, expected_effective_genesis_hash,
                )
                checks["post_install_release_smoke"] = post_smoke
                if post_smoke["returncode"] != 0:
                    rollback = _rollback_after_failure(destination, backup)
                    _update_transaction(transaction_path, transaction, "ROLLED_BACK" if rollback.get("status") == "PASS" else "FAILED", checks=checks, rollback=rollback)
                    return {"status": "FAIL", "stage": "post-install-release-smoke", "checks": checks, "transaction_receipt": str(transaction_path), "rollback": rollback}
            elif resolved_profile == "optimizer":
                checks["post_install_verify_self"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}
                checks["post_install_release_smoke"] = {"status": "SKIPPED_STRUCTURAL_LEVEL"}

            _update_transaction(
                transaction_path, transaction, "COMMITTED",
                destination_tree_hash=sha256_tree(destination, exclude={"MANIFEST.sha256"}),
                backup=str(backup) if backup else None,
                checks_summary={key: (value.get("returncode", value.get("status")) if isinstance(value, dict) else value) for key, value in checks.items()},
            )
            return {
                "status": "PASS", "profile": resolved_profile, "archive": str(archive), "archive_sha256": frozen["archive_sha256"],
                "external_archive_anchor_verified": bool(normalized_archive_anchor),
                "destination": str(destination), "backup": str(backup) if backup else None,
                "rollback_command": ("wbi rollback-install --destination %r --backup %r" % (str(destination), str(backup))) if backup else None,
                "transaction_id": transaction_id, "transaction_receipt": str(transaction_path),
                "recovery": recovered,
                "checks": checks, "post_install_validation": "PASS",
            }
    finally:
        lock.__exit__(None, None, None)


def _rollback_install_unlocked(destination: Path, backup: Path) -> Dict[str, Any]:
    destination_input, backup_input = Path(destination), Path(backup)
    if destination_input.is_symlink() or backup_input.is_symlink():
        return {"status": "FAIL", "errors": ["destination and backup must not be symlinks"]}
    destination, backup = destination_input.resolve(), backup_input.resolve()
    if destination.parent != backup.parent:
        return {"status": "FAIL", "errors": ["backup and destination must share the same parent"]}
    expected_prefix = ".%s.backup." % destination.name
    if not backup.name.startswith(expected_prefix):
        return {"status": "FAIL", "errors": ["backup name was not generated for this destination"]}
    if not backup.is_dir():
        return {"status": "FAIL", "errors": ["backup missing"]}
    receipt_path = backup / ".wbi-backup-receipt.json"
    if not receipt_path.is_file() or receipt_path.is_symlink():
        return {"status": "FAIL", "errors": ["backup receipt missing"]}
    try:
        receipt = load_json(receipt_path)
    except Exception as exc:
        return {"status": "FAIL", "errors": ["backup receipt invalid: %s" % exc]}
    schema_version = str(receipt.get("schema_version") or "")
    if schema_version not in {"1.0", "1.1"}:
        return {"status": "FAIL", "errors": ["unsupported backup receipt schema"]}
    expected_tree = _backup_tree_hash(backup, schema_version)
    if (
        receipt.get("destination_name") != destination.name
        or receipt.get("backup_name") != backup.name
        or receipt.get("source_tree_hash") != expected_tree
    ):
        return {"status": "FAIL", "errors": ["backup identity or content hash mismatch"]}
    displaced = destination.parent / (".%s.displaced.%s" % (destination.name, uuid.uuid4().hex))
    if destination.exists():
        os.replace(str(destination), str(displaced))
    try:
        os.replace(str(backup), str(destination))
        restored_receipt = destination / ".wbi-backup-receipt.json"
        restored_receipt.unlink(missing_ok=True)
        shutil.rmtree(str(displaced), ignore_errors=True)
        _fsync_directory(destination.parent)
    except Exception:
        if displaced.exists() and not destination.exists():
            os.replace(str(displaced), str(destination))
        raise
    transaction_id = receipt.get("install_transaction_id")
    transaction_receipt = None
    if isinstance(transaction_id, str) and transaction_id:
        candidate = destination.parent / ".wbi-install-transactions" / (transaction_id + ".json")
        if candidate.is_file():
            try:
                transaction = load_json(candidate)
                _update_transaction(
                    candidate, transaction, "ROLLED_BACK_BY_REQUEST",
                    rollback_completed_at=utc_now(), restored_tree_hash=expected_tree, restored_from=str(backup),
                )
                transaction_receipt = str(candidate)
            except Exception:
                # The restore itself is authoritative; a damaged external audit
                # receipt is reported but must not undo a safe completed rollback.
                transaction_receipt = "AUDIT_RECEIPT_UPDATE_FAILED:%s" % candidate
    return {
        "status": "PASS", "destination": str(destination), "restored_from": str(backup),
        "restored_tree_hash": expected_tree, "transaction_receipt": transaction_receipt,
        "backup_receipt_schema": schema_version, "legacy_receipt": schema_version == "1.0",
    }


def rollback_install(destination: Path, backup: Path) -> Dict[str, Any]:
    """Restore a verified installer backup while excluding concurrent writers."""
    destination_input, backup_input = Path(destination), Path(backup)
    if destination_input.is_symlink() or backup_input.is_symlink():
        return {"status": "FAIL", "errors": ["destination and backup must not be symlinks"]}
    destination_resolved, backup_resolved = destination_input.resolve(), backup_input.resolve()
    if destination_resolved.parent != backup_resolved.parent:
        return {"status": "FAIL", "errors": ["backup and destination must share the same parent"]}
    skills_root = destination_resolved.parent
    try:
        with _install_lock(skills_root):
            return _rollback_install_unlocked(destination_resolved, backup_resolved)
    except (InstallBusy, ValueError, OSError) as exc:
        return {"status": "BLOCKED", "errors": [str(exc)]}

