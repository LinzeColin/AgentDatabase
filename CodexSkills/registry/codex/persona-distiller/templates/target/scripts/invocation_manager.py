#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_runtime import parse as parse_identity

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / 'runtime' / 'state.json'
LOCK = ROOT / 'runtime' / '.counter.lock'
RUNS = ROOT / 'runtime' / 'runs'
LEDGER = ROOT / 'runtime' / 'invocations.jsonl'
EPISODIC = ROOT / 'memory' / 'episodic.jsonl'


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f'.{path.name}.{uuid.uuid4().hex}.tmp')
    with temp.open('w', encoding='utf-8') as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(obj, ensure_ascii=False, sort_keys=True) + '\n'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, 'a', encoding='utf-8') as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def default_state() -> dict[str, Any]:
    meta = json.loads((ROOT / 'meta.json').read_text(encoding='utf-8'))
    return {
        'schema_version': '1.1',
        'target_slug': meta['slug'],
        'last_serial': 0,
        'last_artifact_version': None,
        'last_identity_selection': None,
        'updated_at': now(),
    }


@contextlib.contextmanager
def file_lock(timeout: float = 15.0) -> Iterator[None]:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open('a+b')
    start = time.monotonic()
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
                    if time.monotonic() - start > timeout:
                        raise TimeoutError('counter lock timeout')
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
                    if time.monotonic() - start > timeout:
                        raise TimeoutError('counter lock timeout')
                    time.sleep(0.02)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            return

        # Conservative fallback for unusual platforms. Common Unix/Windows paths use OS locks above.
        sentinel = LOCK.with_suffix('.exclusive')
        while True:
            try:
                fd = os.open(sentinel, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(fd, f'pid={os.getpid()} at={now()}\n'.encode('utf-8'))
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() - start > timeout:
                    raise TimeoutError(f'counter lock timeout; inspect stale fallback lock: {sentinel}')
                time.sleep(0.02)
        try:
            yield
        finally:
            sentinel.unlink(missing_ok=True)
    finally:
        handle.close()


def load_state() -> dict[str, Any]:
    if not STATE.exists():
        state = default_state()
        atomic_json(STATE, state)
        return state
    state = json.loads(STATE.read_text(encoding='utf-8'))
    if state.get('target_slug') != ROOT.name:
        raise ValueError('runtime state target_slug does not match installed Skill directory')
    return state


def parse_version(value: str) -> int:
    parts = value.split('.')
    if len(parts) != 4 or parts[:3] != ['0', '0', '0'] or not parts[3].isdigit() or int(parts[3]) < 1:
        raise ValueError('artifact version must match 0.0.0.N with N >= 1')
    return int(parts[3])


def existing_serials() -> list[int]:
    values: list[int] = []
    if not RUNS.exists():
        return values
    for path in RUNS.iterdir():
        if not path.is_dir() or not path.name.startswith('0.0.0.'):
            continue
        try:
            values.append(parse_version(path.name))
        except ValueError:
            continue
    return sorted(values)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def logical_artifact(path: Path, version: str) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(f'result path not found or not a file: {resolved}')
    suffix = ''.join(resolved.suffixes)
    stem = resolved.name[:-len(suffix)] if suffix else resolved.name
    logical_name = resolved.name if version in resolved.name else f'{stem}-v{version}{suffix}'
    return {
        'source_name': resolved.name,
        'logical_versioned_name': logical_name,
        'sha256': sha256_file(resolved),
        'size_bytes': resolved.stat().st_size,
    }


def write_artifact_manifest(record: dict[str, Any]) -> None:
    version = record['artifact_version']
    manifest = {
        'schema_version': '1.0',
        'artifact_version': version,
        'run_id': record['run_id'],
        'status': record['status'],
        'identity_selection': record['identity_selection'],
        'response_label': f'运行版本：{version}',
        'artifacts': record.get('artifacts', []),
        'result_summary': record.get('result_summary'),
        'updated_at': record.get('completed_at') or record.get('started_at'),
    }
    atomic_json(RUNS / version / 'artifact-manifest.json', manifest)


def begin(args: argparse.Namespace) -> dict[str, Any]:
    # Identity is parsed before the lock and before any serial is consumed.
    selection = parse_identity(args.identity)
    task = args.task or ''
    with file_lock(args.lock_timeout):
        state = load_state()
        history = existing_serials()
        # If a previous process committed a run directory but crashed before state update,
        # advance from history instead of reusing the serial.
        last = max(int(state.get('last_serial', 0)), max(history, default=0))
        if args.version_override:
            if not args.allow_override:
                raise ValueError('--version-override requires --allow-override and an explicit user instruction')
            serial = parse_version(args.version_override)
            if serial <= last:
                raise ValueError(f'override serial {serial} must be greater than current {last}; reuse is forbidden')
        else:
            serial = last + 1
        version = f'0.0.0.{serial}'
        run_dir = RUNS / version
        if run_dir.exists():
            raise ValueError(f'run already exists: {version}')
        meta = json.loads((ROOT / 'meta.json').read_text(encoding='utf-8'))
        record = {
            'schema_version': '1.1',
            'run_id': f'run-{uuid.uuid4().hex}',
            'artifact_version': version,
            'serial': serial,
            'status': 'started',
            'started_at': now(),
            'completed_at': None,
            'identity_selection': selection,
            'task_sha256': hashlib.sha256(task.encode('utf-8')).hexdigest(),
            'task_preview': task[:160] if args.store_task else None,
            'task_content': task if args.store_task else None,
            'privacy_mode': 'content' if args.store_task else 'metadata',
            'builder_version': meta.get('builder_version'),
            'model_version': meta.get('model_version'),
            'version_override': bool(args.version_override),
            'error': None,
            'result_summary': None,
            'result_sha256': None,
            'artifacts': [],
        }
        # Commit the run directory atomically. Hidden pending directories never count as serials.
        RUNS.mkdir(parents=True, exist_ok=True)
        pending = RUNS / f'.pending-{uuid.uuid4().hex}'
        pending.mkdir()
        try:
            atomic_json(pending / 'run.json', record)
            atomic_json(pending / 'artifact-manifest.json', {
                'schema_version': '1.0', 'artifact_version': version, 'run_id': record['run_id'],
                'status': 'started', 'identity_selection': selection,
                'response_label': f'运行版本：{version}', 'artifacts': [],
                'result_summary': None, 'updated_at': record['started_at'],
            })
            os.replace(pending, run_dir)
        finally:
            if pending.exists():
                for child in pending.iterdir():
                    child.unlink(missing_ok=True)
                pending.rmdir()
        state.update({
            'schema_version': '1.1',
            'last_serial': serial,
            'last_artifact_version': version,
            'last_identity_selection': selection,
            'updated_at': now(),
        })
        atomic_json(STATE, state)
        append_jsonl(LEDGER, {
            'event': 'begin', 'at': record['started_at'], 'run_id': record['run_id'],
            'artifact_version': version, 'identity_selection': selection,
            'task_sha256': record['task_sha256'], 'version_override': record['version_override'],
        })
    return record


def terminalize_locked(
    version: str,
    status: str,
    summary: str | None = None,
    error: str | None = None,
    result_paths: list[str] | None = None,
) -> dict[str, Any]:
    run_path = RUNS / version / 'run.json'
    if not run_path.is_file():
        raise ValueError(f'unknown run: {version}')
    record = json.loads(run_path.read_text(encoding='utf-8'))
    if record['status'] != 'started':
        raise ValueError(f'run {version} is already terminal: {record["status"]}')
    artifacts = [logical_artifact(Path(item), version) for item in (result_paths or [])]
    record['status'] = status
    record['completed_at'] = now()
    record['result_summary'] = summary
    record['error'] = error
    record['artifacts'] = artifacts
    if len(artifacts) == 1:
        record['result_sha256'] = artifacts[0]['sha256']
    elif artifacts:
        joined = ''.join(item['sha256'] for item in artifacts)
        record['result_sha256'] = hashlib.sha256(joined.encode('ascii')).hexdigest()
    atomic_json(run_path, record)
    write_artifact_manifest(record)
    event = {
        'event': status, 'at': record['completed_at'], 'run_id': record['run_id'],
        'artifact_version': version, 'summary': summary, 'error': error,
        'artifact_count': len(artifacts), 'result_sha256': record.get('result_sha256'),
    }
    append_jsonl(LEDGER, event)
    append_jsonl(EPISODIC, {
        'artifact_version': version,
        'run_id': record['run_id'],
        'status': status,
        'identity_selection': record['identity_selection'],
        'task_sha256': record['task_sha256'],
        'result_summary': summary,
        'result_sha256': record.get('result_sha256'),
        'error': error,
        'recorded_at': record['completed_at'],
        'promotion_status': 'not-promoted',
    })
    return record


def mutate(version: str, status: str, summary: str | None = None, error: str | None = None, result_paths: list[str] | None = None) -> dict[str, Any]:
    parse_version(version)
    with file_lock():
        return terminalize_locked(version, status, summary=summary, error=error, result_paths=result_paths)


def recover(older_than_seconds: float) -> dict[str, Any]:
    if older_than_seconds < 0:
        raise ValueError('--older-than-seconds must be >= 0')
    recovered: list[str] = []
    current = datetime.now(timezone.utc)
    with file_lock():
        for serial in existing_serials():
            version = f'0.0.0.{serial}'
            run_path = RUNS / version / 'run.json'
            if not run_path.is_file():
                continue
            record = json.loads(run_path.read_text(encoding='utf-8'))
            if record.get('status') != 'started':
                continue
            age = (current - parse_time(record['started_at'])).total_seconds()
            if age < older_than_seconds:
                continue
            terminalize_locked(
                version, 'failed', summary='Recovered stale unfinished invocation.',
                error='interrupted-before-terminal-record', result_paths=[],
            )
            recovered.append(version)
    return {'recovered': recovered, 'count': len(recovered), 'older_than_seconds': older_than_seconds}


def verify() -> dict[str, Any]:
    state = load_state()
    serials = existing_serials()
    errors: list[str] = []
    for serial in serials:
        version = f'0.0.0.{serial}'
        run_dir = RUNS / version
        run_path = run_dir / 'run.json'
        manifest_path = run_dir / 'artifact-manifest.json'
        if not run_path.is_file():
            errors.append(f'missing run.json: {version}')
            continue
        try:
            record = json.loads(run_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            errors.append(f'invalid run.json {version}: {exc}')
            continue
        if record.get('artifact_version') != version or int(record.get('serial', -1)) != serial:
            errors.append(f'version mismatch: {version}')
        if record.get('status') not in {'started', 'completed', 'failed'}:
            errors.append(f'invalid status: {version}')
        if not manifest_path.is_file():
            errors.append(f'missing artifact-manifest.json: {version}')
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
                if manifest.get('artifact_version') != version or manifest.get('status') != record.get('status'):
                    errors.append(f'artifact manifest mismatch: {version}')
            except json.JSONDecodeError as exc:
                errors.append(f'invalid artifact manifest {version}: {exc}')
    if len(serials) != len(set(serials)):
        errors.append('duplicate serial')
    max_serial = max(serials, default=0)
    state_serial = int(state.get('last_serial', 0))
    if state_serial != max_serial:
        errors.append(f'state/history mismatch: state={state_serial}, max_run={max_serial}')
    pending = [path.name for path in RUNS.glob('.pending-*') if path.is_dir()]
    if pending:
        errors.append(f'stale pending transaction directories: {pending}')
    return {
        'valid': not errors,
        'last_serial': state_serial,
        'run_count': len(serials),
        'serials': serials,
        'started_count': sum(1 for serial in serials if json.loads((RUNS / f"0.0.0.{serial}" / 'run.json').read_text()).get('status') == 'started'),
        'errors': errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Immutable per-invocation 0.0.0.N ledger and artifact manifest.')
    sub = parser.add_subparsers(dest='command', required=True)
    p_begin = sub.add_parser('begin')
    p_begin.add_argument('--identity', required=True)
    p_begin.add_argument('--task', default='')
    p_begin.add_argument('--store-task', action='store_true')
    p_begin.add_argument('--version-override')
    p_begin.add_argument('--allow-override', action='store_true')
    p_begin.add_argument('--lock-timeout', type=float, default=15.0)
    for name in ['complete', 'fail']:
        child = sub.add_parser(name)
        child.add_argument('version')
        child.add_argument('--summary')
        child.add_argument('--result-path', action='append', default=[])
        if name == 'fail':
            child.add_argument('--error', required=True)
    p_recover = sub.add_parser('recover')
    p_recover.add_argument('--older-than-seconds', type=float, default=3600)
    sub.add_parser('status')
    sub.add_parser('list')
    sub.add_parser('verify')
    args = parser.parse_args()
    try:
        if args.command == 'begin':
            result = begin(args)
        elif args.command == 'complete':
            result = mutate(args.version, 'completed', summary=args.summary, result_paths=args.result_path)
        elif args.command == 'fail':
            result = mutate(args.version, 'failed', summary=args.summary, error=args.error, result_paths=args.result_path)
        elif args.command == 'recover':
            result = recover(args.older_than_seconds)
        elif args.command == 'status':
            result = load_state()
        elif args.command == 'list':
            result = [
                json.loads((RUNS / f'0.0.0.{serial}' / 'run.json').read_text(encoding='utf-8'))
                for serial in existing_serials()
                if (RUNS / f'0.0.0.{serial}' / 'run.json').is_file()
            ]
        else:
            result = verify()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not isinstance(result, dict) or result.get('valid', True) else 1
    except (ValueError, OSError, json.JSONDecodeError, TimeoutError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
