#!/usr/bin/env python3
"""Fail-closed consumer for SkillOps public daily JSONL run shards."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_TOOLS = REPO_ROOT / "CodexSkills" / "governance" / "tools"
sys.path.insert(0, str(GOVERNANCE_TOOLS))

from canonical_json import (  # noqa: E402
    CanonicalizationError,
    parse_json_bytes,
)
from validate_mechanism import (  # noqa: E402
    CANONICAL_MANIFEST_PATH,
    PROTOCOL,
    ContractError,
    TrustTuple,
    load_trusted_bundle,
)
from validate_public_run_event import (  # noqa: E402
    PUBLIC_RUN_EVENT_SCHEMA_ID,
    PublicRunEventError,
    parse_canonical_public_run_event,
)


CONFIG_PATH = PurePosixPath("config/evaluation/skill_run_consumer.json")
EXPECTED_STATUS = "DRAFT_NON_ACTIVE_CONSUMER_READY"
EXPECTED_REQUIRED_GATES = (
    "ACTIVE_EXTERNAL_TRUST",
    "AU_040_DAILY_JSONL_SHARD_MANIFEST",
    "BOUND_REFERENCE_RESOLVER",
)
PART_PATH_RE = re.compile(
    r"^(?P<year>[0-9]{4})/"
    r"(?P<month>0[1-9]|1[0-2])/"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])/"
    r"part-(?P<part>[0-9]{4})\.jsonl$"
)
MAX_CONFIG_BYTES = 1024 * 1024
MAX_TREE_ENTRIES = 10_000
MAX_TREE_ERRORS = 128


class SkillRunConsumerError(ValueError):
    """The consumer contract or repository tree is unsafe."""


@dataclass(frozen=True)
class SkillRunConsumerContract:
    trust: TrustTuple
    expected_bundle_digest: str
    log_root: PurePosixPath
    max_part_bytes: int
    timezone: ZoneInfo
    allowed_root_files: tuple[str, ...]
    repository_shards_permitted: bool


def _exact_keys(value: Any, expected: Iterable[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SkillRunConsumerError(f"{code}_NOT_OBJECT")
    expected_set = set(expected)
    if set(value) != expected_set:
        raise SkillRunConsumerError(f"{code}_KEY_SET_MISMATCH")
    return value


def _safe_reason_code(exc: BaseException) -> str:
    candidate = str(exc).split(":", 1)[0]
    if re.fullmatch(r"[A-Z][A-Z0-9_]*", candidate):
        return candidate
    return type(exc).__name__.upper()


def _open_flags(*, directory: bool) -> int:
    required = ("O_NOFOLLOW", "O_DIRECTORY")
    missing = [name for name in required if not hasattr(os, name)]
    if missing:
        raise SkillRunConsumerError(
            "SKILL_RUN_NOFOLLOW_CAPABILITY_MISSING:" + ",".join(missing)
        )
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _validate_relative_path(relative: PurePosixPath) -> None:
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise SkillRunConsumerError("SKILL_RUN_RELATIVE_PATH_INVALID")


def _open_root_directory(path: Path) -> int:
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise SkillRunConsumerError("SKILL_RUN_ROOT_NOT_REAL_DIRECTORY")
        descriptor = os.open(path, _open_flags(directory=True))
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or opened.st_dev != info.st_dev
            or opened.st_ino != info.st_ino
        ):
            os.close(descriptor)
            raise SkillRunConsumerError("SKILL_RUN_ROOT_CHANGED_DURING_OPEN")
        return descriptor
    except SkillRunConsumerError:
        raise
    except OSError as exc:
        raise SkillRunConsumerError("SKILL_RUN_ROOT_OPEN_FAILED") from exc


def _open_relative_directory(root: Path, relative: PurePosixPath) -> int:
    _validate_relative_path(relative)
    descriptor = _open_root_directory(root)
    try:
        for part in relative.parts:
            next_descriptor = os.open(
                part,
                _open_flags(directory=True),
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except (OSError, SkillRunConsumerError) as exc:
        os.close(descriptor)
        if isinstance(exc, SkillRunConsumerError):
            raise
        raise SkillRunConsumerError(
            "SKILL_RUN_DIRECTORY_COMPONENT_OPEN_FAILED"
        ) from exc


def _read_relative_regular_file(
    root: Path,
    relative: PurePosixPath,
    *,
    max_bytes: int,
) -> bytes:
    _validate_relative_path(relative)
    root_descriptor = _open_root_directory(root)
    parent_descriptor = root_descriptor
    file_descriptor: Optional[int] = None
    try:
        for part in relative.parts[:-1]:
            next_descriptor = os.open(
                part,
                _open_flags(directory=True),
                dir_fd=parent_descriptor,
            )
            if parent_descriptor != root_descriptor:
                os.close(parent_descriptor)
            parent_descriptor = next_descriptor
        file_descriptor = os.open(
            relative.parts[-1],
            _open_flags(directory=False),
            dir_fd=parent_descriptor,
        )
        info = os.fstat(file_descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise SkillRunConsumerError("SKILL_RUN_CONFIG_NOT_REAL_FILE")
        if info.st_size > max_bytes:
            raise SkillRunConsumerError("SKILL_RUN_CONFIG_OVERSIZE")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(file_descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > max_bytes:
            raise SkillRunConsumerError("SKILL_RUN_CONFIG_OVERSIZE")
        return raw
    except SkillRunConsumerError:
        raise
    except OSError as exc:
        raise SkillRunConsumerError("SKILL_RUN_CONFIG_OPEN_FAILED") from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if parent_descriptor != root_descriptor:
            os.close(parent_descriptor)
        os.close(root_descriptor)


def _parse_consumer_contract(raw: bytes) -> SkillRunConsumerContract:
    try:
        payload = parse_json_bytes(raw)
    except CanonicalizationError as exc:
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_CONFIG_INVALID") from exc
    root = _exact_keys(
        payload,
        {
            "schema_version",
            "status",
            "consumer_owner_plane",
            "protocol_revision",
            "log_root",
            "record_schema_id",
            "candidate_trust",
            "layout",
            "allowed_root_files",
            "publication_gate",
        },
        "SKILL_RUN_CONSUMER_CONFIG",
    )
    if (
        root["schema_version"] != "openai_database.skill_run_consumer.v1"
        or root["status"] != EXPECTED_STATUS
        or root["consumer_owner_plane"] != "MECHANISM"
        or root["protocol_revision"] != PROTOCOL
        or root["record_schema_id"] != PUBLIC_RUN_EVENT_SCHEMA_ID
        or root["log_root"] != "data/run_logs/skills_runs"
    ):
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_CONFIG_IDENTITY_MISMATCH")

    trust = _exact_keys(
        root["candidate_trust"],
        {
            "verified_git_object_id",
            "expected_bundle_digest",
            "canonical_manifest_path",
            "mode",
        },
        "SKILL_RUN_CONSUMER_TRUST",
    )
    if trust["canonical_manifest_path"] != CANONICAL_MANIFEST_PATH:
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_MANIFEST_PATH_MISMATCH")
    if trust["mode"] != "CANDIDATE":
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_TRUST_MODE_INVALID")

    layout = _exact_keys(
        root["layout"],
        {
            "relative_pattern",
            "part_name_regex",
            "shard_calendar_timezone",
            "max_part_bytes",
            "record_framing",
            "part_numbers_start_at",
            "part_numbers_gapless",
        },
        "SKILL_RUN_CONSUMER_LAYOUT",
    )
    if (
        layout["relative_pattern"] != "YYYY/MM/DD/part-NNNN.jsonl"
        or layout["part_name_regex"] != r"^part-[0-9]{4}\.jsonl$"
        or layout["shard_calendar_timezone"] != "Australia/Sydney"
        or layout["max_part_bytes"] != 20 * 1024 * 1024
        or layout["record_framing"] != "RFC8785_JCS_PER_LINE_LF"
        or layout["part_numbers_start_at"] != 1
        or layout["part_numbers_gapless"] is not True
    ):
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_LAYOUT_MISMATCH")

    gate = _exact_keys(
        root["publication_gate"],
        {
            "canonical_publication_permitted",
            "repository_shards_permitted",
            "required_before_enable",
        },
        "SKILL_RUN_CONSUMER_PUBLICATION_GATE",
    )
    required_before_enable = gate["required_before_enable"]
    if (
        gate["canonical_publication_permitted"] is not False
        or gate["repository_shards_permitted"] is not False
        or not isinstance(required_before_enable, list)
        or tuple(required_before_enable) != EXPECTED_REQUIRED_GATES
    ):
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_PREACTIVE_GATE_INVALID")
    allowed = root["allowed_root_files"]
    if allowed != ["README.md"]:
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_ALLOWED_ROOT_FILES_INVALID")

    try:
        timezone = ZoneInfo(layout["shard_calendar_timezone"])
    except Exception as exc:
        raise SkillRunConsumerError("SKILL_RUN_CONSUMER_TIMEZONE_UNAVAILABLE") from exc
    return SkillRunConsumerContract(
        trust=TrustTuple(
            str(trust["verified_git_object_id"]),
            str(trust["expected_bundle_digest"]),
            str(trust["canonical_manifest_path"]),
            str(trust["mode"]),
        ),
        expected_bundle_digest=str(trust["expected_bundle_digest"]),
        log_root=PurePosixPath(str(root["log_root"])),
        max_part_bytes=int(layout["max_part_bytes"]),
        timezone=timezone,
        allowed_root_files=tuple(allowed),
        repository_shards_permitted=bool(
            gate["repository_shards_permitted"]
        ),
    )


def load_consumer_contract(path: Path) -> SkillRunConsumerContract:
    """Load a directly addressed config file without following its final node."""
    raw = _read_relative_regular_file(
        path.parent,
        PurePosixPath(path.name),
        max_bytes=MAX_CONFIG_BYTES,
    )
    return _parse_consumer_contract(raw)


def _directory_shape_valid(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    if len(parts) == 1:
        return bool(re.fullmatch(r"[0-9]{4}", parts[0]))
    if len(parts) == 2:
        return bool(
            re.fullmatch(r"[0-9]{4}", parts[0])
            and re.fullmatch(r"0[1-9]|1[0-2]", parts[1])
        )
    if len(parts) == 3:
        try:
            dt.date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (TypeError, ValueError):
            return False
        return (
            bool(re.fullmatch(r"[0-9]{4}", parts[0]))
            and bool(re.fullmatch(r"0[1-9]|1[0-2]", parts[1]))
            and bool(re.fullmatch(r"0[1-9]|[12][0-9]|3[01]", parts[2]))
        )
    return False


def _safe_tree_files(root_descriptor: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    files: list[str] = []
    entry_count = 0
    stopped = False

    def record_error(code: str) -> None:
        nonlocal stopped
        if len(errors) < MAX_TREE_ERRORS:
            errors.append(code)
            return
        if not errors or errors[-1] != "skill_run_tree_error_limit_exceeded":
            errors.append("skill_run_tree_error_limit_exceeded")
        stopped = True

    def walk(directory_descriptor: int, prefix: tuple[str, ...]) -> None:
        nonlocal entry_count, stopped
        if stopped:
            return
        before = os.fstat(directory_descriptor)
        try:
            with os.scandir(directory_descriptor) as entries:
                ordered = []
                for entry in entries:
                    entry_count += 1
                    if entry_count > MAX_TREE_ENTRIES:
                        record_error("skill_run_tree_entry_limit_exceeded")
                        stopped = True
                        break
                    ordered.append(entry)
                ordered.sort(key=lambda item: item.name)
        except OSError as exc:
            record_error(
                f"skill_run_tree_walk_failed:{type(exc).__name__}"
            )
            return
        if stopped:
            return
        for entry in ordered:
            if stopped:
                break
            relative = "/".join((*prefix, entry.name))
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                record_error("skill_run_tree_lstat_failed")
                continue
            if stat.S_ISLNK(info.st_mode):
                record_error("skill_run_tree_unsafe_entry")
                continue
            if stat.S_ISDIR(info.st_mode):
                if not _directory_shape_valid(relative):
                    record_error("skill_run_unapproved_directory")
                    continue
                try:
                    child = os.open(
                        entry.name,
                        _open_flags(directory=True),
                        dir_fd=directory_descriptor,
                    )
                    opened = os.fstat(child)
                    if (
                        opened.st_dev != info.st_dev
                        or opened.st_ino != info.st_ino
                    ):
                        record_error("skill_run_tree_entry_changed_during_open")
                        os.close(child)
                        continue
                except OSError:
                    record_error("skill_run_tree_directory_open_failed")
                    continue
                try:
                    walk(child, (*prefix, entry.name))
                finally:
                    os.close(child)
                continue
            if stat.S_ISREG(info.st_mode):
                files.append(relative)
                continue
            record_error("skill_run_tree_unsafe_entry")
        after = os.fstat(directory_descriptor)
        if (
            before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
        ):
            record_error("skill_run_tree_changed_during_scan")

    walk(root_descriptor, ())
    return sorted(files), errors


def _parse_event_time(value: str) -> dt.datetime:
    return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=dt.timezone.utc
    )


def validate_part_bytes(
    raw: bytes,
    *,
    relative_path: str,
    bundle: Any,
    contract: SkillRunConsumerContract,
) -> tuple[list[Mapping[str, Any]], list[str]]:
    """Validate a synthetic or future daily part without granting publication."""
    errors: list[str] = []
    match = PART_PATH_RE.fullmatch(relative_path)
    if match is None:
        return [], ["skill_run_part_path_invalid"]
    if int(match["part"]) < 1:
        return [], [f"skill_run_part_number_invalid:{relative_path}"]
    try:
        expected_date = dt.date(
            int(match["year"]), int(match["month"]), int(match["day"])
        )
    except ValueError:
        return [], [f"skill_run_part_date_invalid:{relative_path}"]
    if not raw:
        return [], [f"skill_run_part_empty:{relative_path}"]
    if len(raw) > contract.max_part_bytes:
        return [], [f"skill_run_part_oversize:{relative_path}:{len(raw)}"]
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"skill_run_part_bom_forbidden:{relative_path}")
    if b"\r" in raw:
        errors.append(f"skill_run_part_cr_forbidden:{relative_path}")
    if not raw.endswith(b"\n"):
        errors.append(f"skill_run_part_final_lf_required:{relative_path}")
        framed = raw
    else:
        framed = raw[:-1]
    lines = framed.split(b"\n")
    if any(not line for line in lines):
        errors.append(f"skill_run_part_blank_record:{relative_path}")

    events: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line:
            continue
        try:
            event = parse_canonical_public_run_event(
                bundle,
                line,
                expected_bundle_digest=contract.expected_bundle_digest,
            )
        except (CanonicalizationError, ContractError, PublicRunEventError) as exc:
            errors.append(
                "skill_run_event_invalid:"
                f"{relative_path}:{line_number}:{_safe_reason_code(exc)}"
            )
            continue
        occurred_date = _parse_event_time(event["occurred_at"]).astimezone(
            contract.timezone
        ).date()
        if occurred_date != expected_date:
            errors.append(
                f"skill_run_event_shard_date_mismatch:{relative_path}:{line_number}"
            )
        events.append(event)

    order = [(event["occurred_at"], event["event_uid"]) for event in events]
    if order != sorted(order) or len(order) != len(set(order)):
        errors.append(f"skill_run_part_order_invalid:{relative_path}")
    return events, errors


def validate_skill_run_logs(
    database_dir: Path,
    *,
    repo_root: Optional[Path] = None,
) -> list[str]:
    database_dir = database_dir.absolute()
    repository = (repo_root or REPO_ROOT).absolute()
    try:
        repository_info = repository.lstat()
        if stat.S_ISLNK(repository_info.st_mode) or not stat.S_ISDIR(
            repository_info.st_mode
        ):
            raise SkillRunConsumerError("SKILL_RUN_REPOSITORY_ROOT_UNSAFE")
        config_raw = _read_relative_regular_file(
            database_dir,
            CONFIG_PATH,
            max_bytes=MAX_CONFIG_BYTES,
        )
        contract = _parse_consumer_contract(config_raw)
        load_trusted_bundle(repository, contract.trust)
        root_descriptor = _open_relative_directory(
            database_dir,
            contract.log_root,
        )
    except (OSError, ContractError, SkillRunConsumerError) as exc:
        return [f"skill_run_consumer_bootstrap_failed:{_safe_reason_code(exc)}"]

    try:
        files, errors = _safe_tree_files(root_descriptor)
    finally:
        os.close(root_descriptor)
    part_paths: list[str] = []
    for relative in files:
        if "/" not in relative and relative in contract.allowed_root_files:
            continue
        if PART_PATH_RE.fullmatch(relative) is None:
            errors.append("skill_run_unapproved_path")
            continue
        try:
            match = PART_PATH_RE.fullmatch(relative)
            assert match is not None
            dt.date(int(match["year"]), int(match["month"]), int(match["day"]))
        except ValueError:
            errors.append(f"skill_run_part_date_invalid:{relative}")
            continue
        part_paths.append(relative)

    parts_by_day: dict[str, list[int]] = {}
    for relative in part_paths:
        match = PART_PATH_RE.fullmatch(relative)
        assert match is not None
        day = f"{match['year']}/{match['month']}/{match['day']}"
        parts_by_day.setdefault(day, []).append(int(match["part"]))
    for day, part_numbers in sorted(parts_by_day.items()):
        observed = sorted(part_numbers)
        expected = list(range(1, len(observed) + 1))
        if observed != expected:
            errors.append(f"skill_run_part_sequence_invalid:{day}")

    if part_paths and not contract.repository_shards_permitted:
        errors.append(
            "skill_run_canonical_publication_blocked:"
            + ",".join(sorted(part_paths))
        )
    return errors


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--database-dir", type=Path, default=Path("OpenAIDatabase"))
    args = parser.parse_args(argv)
    errors = validate_skill_run_logs(
        args.database_dir,
        repo_root=args.repo_root,
    )
    result = {
        "schema_version": "openai_database.skill_run_consumer_result.v1",
        "status": "PASS" if not errors else "FAIL",
        "consumer_state": EXPECTED_STATUS,
        "canonical_publication_permitted": False,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(_main())
