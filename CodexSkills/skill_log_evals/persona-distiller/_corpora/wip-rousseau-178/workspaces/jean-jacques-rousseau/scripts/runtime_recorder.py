#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_router import plan

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'runtime' / '.audit.lock'
LEDGER = ROOT / 'runtime' / 'invocations.jsonl'
EPISODIC = ROOT / 'memory' / 'episodic.jsonl'
FORBIDDEN_VERSION_FIELDS = {'artifact_version', 'run_id', 'serial', 'version_override'}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, 'a', encoding='utf-8') as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


@contextlib.contextmanager
def file_lock(timeout: float = 15.0) -> Iterator[None]:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open('a+b')
    started = time.monotonic()
    try:
        try:
            import fcntl  # type: ignore
        except ImportError:
            fcntl = None  # type: ignore
        if fcntl is not None:
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() - started > timeout:
                        raise TimeoutError('runtime audit lock timeout')
                    time.sleep(0.02)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return

        try:
            import msvcrt  # type: ignore
        except ImportError:
            msvcrt = None  # type: ignore
        if msvcrt is not None:
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() - started > timeout:
                        raise TimeoutError('runtime audit lock timeout')
                    time.sleep(0.02)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return

        sentinel = LOCK.with_suffix('.exclusive')
        while True:
            try:
                fd = os.open(sentinel, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() - started > timeout:
                    raise TimeoutError(f'runtime audit lock timeout; inspect {sentinel}')
                time.sleep(0.02)
        try:
            yield
        finally:
            sentinel.unlink(missing_ok=True)
    finally:
        handle.close()


def artifact_record(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f'result path not found or not a file: {path}')
    return {
        'source_name': path.name,
        'sha256': sha256_file(path),
        'size_bytes': path.stat().st_size,
    }


def record(args: argparse.Namespace) -> dict[str, Any]:
    if args.status == 'failed' and not args.error:
        raise ValueError('--error is required when --status failed')
    task = args.task or ''
    route = plan(task)
    artifacts = [artifact_record(value) for value in args.result_path]
    value = {
        'schema_version': '1.0',
        'status': args.status,
        'recorded_at': now(),
        'task_sha256': hashlib.sha256(task.encode('utf-8')).hexdigest(),
        'task_content': task if args.store_task else None,
        'privacy_mode': 'content' if args.store_task else 'metadata',
        'identity_route': route['identity_route'],
        'scenarios': route['scenarios'],
        'result_summary': args.summary,
        'error': args.error,
        'artifacts': artifacts,
    }
    if FORBIDDEN_VERSION_FIELDS.intersection(value):
        raise ValueError('runtime records must not contain invocation identifiers or versions')
    episodic = dict(value, promotion_status='not-promoted')
    with file_lock(args.lock_timeout):
        append_jsonl(LEDGER, value)
        append_jsonl(EPISODIC, episodic)
    return value


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'invalid JSONL at {path}:{line_number}: {exc}') from exc
        if not isinstance(value, dict):
            raise ValueError(f'runtime record must be an object at {path}:{line_number}')
        records.append(value)
    return records


def verify() -> dict[str, Any]:
    errors: list[str] = []
    ledger = read_records(LEDGER)
    episodic = read_records(EPISODIC)
    for index, value in enumerate(ledger, 1):
        forbidden = sorted(FORBIDDEN_VERSION_FIELDS.intersection(value))
        if forbidden:
            errors.append(f'ledger row {index} contains forbidden fields: {forbidden}')
        if value.get('status') not in {'completed', 'failed'}:
            errors.append(f'ledger row {index} has invalid status')
        if not isinstance(value.get('task_sha256'), str) or len(value['task_sha256']) != 64:
            errors.append(f'ledger row {index} has invalid task_sha256')
    if len(ledger) != len(episodic):
        errors.append(f'ledger/episodic count mismatch: {len(ledger)} != {len(episodic)}')
    return {
        'valid': not errors,
        'record_count': len(ledger),
        'numbered_records': 0,
        'errors': errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Optional unnumbered runtime audit and episodic-memory recorder.')
    sub = parser.add_subparsers(dest='command', required=True)
    child = sub.add_parser('record')
    child.add_argument('--status', choices=['completed', 'failed'], required=True)
    child.add_argument('--task', default='')
    child.add_argument('--summary')
    child.add_argument('--error')
    child.add_argument('--result-path', action='append', default=[])
    child.add_argument('--store-task', action='store_true')
    child.add_argument('--lock-timeout', type=float, default=15.0)
    sub.add_parser('list')
    sub.add_parser('verify')
    args = parser.parse_args()
    try:
        if args.command == 'record':
            result: Any = record(args)
        elif args.command == 'list':
            result = read_records(LEDGER)
        else:
            result = verify()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not isinstance(result, dict) or result.get('valid', True) else 1
    except (ValueError, OSError, json.JSONDecodeError, TimeoutError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
