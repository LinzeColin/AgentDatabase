from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

LANES = ('writings', 'conversations', 'expression', 'external', 'decisions', 'timeline')
SUITES = (
    'known', 'boundary', 'voice', 'trajectory', 'contrast', 'fact-preservation', 'style-decoy',
    'task-completion', 'planning-fidelity', 'tool-use', 'capability-calibration', 'refusal-stop',
    'long-horizon', 'identity-routing', 'anonymous-fidelity', 'token-efficiency',
)
PROFILE_THRESHOLDS = {
    'quick': {
        'min_sources': 8,
        'min_lanes': 3,
        'min_primary_ratio': 0.40,
        'min_models': 2,
        'min_heuristics': 3,
        'min_suite_cases': 1,
        'min_overall_score': 0.65,
        'min_baseline_delta': 0.03,
        'min_boundary_score': 0.70,
        'min_fact_score': 0.80,
    },
    'standard': {
        'min_sources': 24,
        'min_lanes': 6,
        'min_primary_ratio': 0.50,
        'min_models': 3,
        'min_heuristics': 5,
        'min_suite_cases': 1,
        'min_overall_score': 0.72,
        'min_baseline_delta': 0.05,
        'min_boundary_score': 0.78,
        'min_fact_score': 0.88,
    },
    'deep': {
        'min_sources': 45,
        'min_lanes': 6,
        'min_primary_ratio': 0.65,
        'min_models': 4,
        'min_heuristics': 6,
        'min_suite_cases': 2,
        'min_overall_score': 0.80,
        'min_baseline_delta': 0.07,
        'min_boundary_score': 0.85,
        'min_fact_score': 0.93,
    },
}

TEXT_EXTENSIONS = {'.txt', '.md', '.markdown', '.rst', '.log'}
STRUCTURED_EXTENSIONS = {'.json', '.jsonl', '.csv', '.tsv'}
SUBTITLE_EXTENSIONS = {'.srt', '.vtt'}
EMAIL_EXTENSIONS = {'.eml', '.mbox'}
OPAQUE_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.tif', '.tiff',
    '.docx', '.pptx', '.xlsx', '.odt', '.ods', '.odp',
    '.mp3', '.wav', '.m4a', '.flac', '.mp4', '.mov', '.mkv', '.webm',
}
SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | STRUCTURED_EXTENSIONS | SUBTITLE_EXTENSIONS | EMAIL_EXTENSIONS | OPAQUE_EXTENSIONS

SECRET_PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'aws-access-key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'github-token': re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    'openai-style-key': re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b'),
    'generic-secret-assignment': re.compile(
        r'(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|passwd)\b\s*[:=]\s*["\']?([A-Za-z0-9_./+\-=]{12,})'
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def compact_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def make_id(prefix: str, seed: str | None = None) -> str:
    material = seed.encode('utf-8') if seed is not None else uuid.uuid4().bytes
    return f'{prefix}-{hashlib.sha256(material).hexdigest()[:12]}'


def slugify(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value)
    ascii_value = normalized.encode('ascii', 'ignore').decode('ascii').lower()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_value).strip('-')
    slug = re.sub(r'-{2,}', '-', slug)
    if not slug:
        slug = f'target-{hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]}'
    if len(slug) > 64:
        slug = slug[:64].rstrip('-')
    return slug


def valid_skill_name(name: str) -> bool:
    return bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name)) and len(name) <= 64


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_write_bytes(path: Path, data: bytes, mode: int | None = None) -> None:
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def atomic_write_text(path: Path, text: str, mode: int | None = None) -> None:
    atomic_write_bytes(path, text.encode('utf-8'), mode=mode)


def atomic_write_json(path: Path, obj: Any, mode: int | None = None) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', mode=mode)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'Invalid JSON at {path}: {exc}') from exc


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open('r', encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSONL at {path}:{line_number}: {exc}') from exc
            if not isinstance(value, dict):
                raise ValueError(f'JSONL record must be an object at {path}:{line_number}')
            records.append(value)
    return records


def append_jsonl(path: Path, record: dict[str, Any], mode: int = 0o600) -> None:
    ensure_dir(path.parent)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n'
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(path, flags, mode)
    try:
        with os.fdopen(fd, 'a', encoding='utf-8') as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        # fd is closed by fdopen; defensive only.
        pass


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise ValueError(f'Missing YAML frontmatter in {path}')
    end = text.find('\n---\n', 4)
    if end < 0:
        raise ValueError(f'Unterminated YAML frontmatter in {path}')
    raw = text[4:end]
    metadata: dict[str, str] = {}
    current_parent: str | None = None
    for raw_line in raw.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith('#'):
            continue
        if raw_line.startswith('  ') and current_parent:
            key, sep, value = raw_line.strip().partition(':')
            if sep:
                metadata[f'{current_parent}.{key.strip()}'] = value.strip().strip('"\'')
            continue
        key, sep, value = raw_line.partition(':')
        if not sep:
            continue
        key = key.strip()
        value = value.strip().strip('"\'')
        metadata[key] = value
        current_parent = key if not value else None
    return metadata, text[end + 5:]


def ensure_target(target: Path) -> dict[str, Any]:
    target = target.expanduser().resolve()
    meta_path = target / 'meta.json'
    skill_path = target / 'SKILL.md'
    if not target.is_dir() or not meta_path.is_file() or not skill_path.is_file():
        raise ValueError(f'Not a Persona Distiller target: {target}')
    meta = read_json(meta_path)
    if not isinstance(meta, dict):
        raise ValueError(f'Invalid target metadata: {meta_path}')
    if meta.get('slug') != target.name:
        raise ValueError(f'Target directory name must match meta slug: {target.name!r} != {meta.get("slug")!r}')
    fm, _ = parse_frontmatter(skill_path)
    if fm.get('name') != target.name:
        raise ValueError(f'SKILL.md name must match target directory: {fm.get("name")!r} != {target.name!r}')
    return meta


def save_meta(target: Path, meta: dict[str, Any]) -> None:
    meta = dict(meta)
    meta['updated_at'] = utc_now()
    atomic_write_json(target / 'meta.json', meta, mode=0o600)


def safe_filename(name: str) -> str:
    name = Path(name).name
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*]+', '_', name).strip(' .')
    return name[:180] or 'unnamed'


def relpath_inside(path: Path, root: Path) -> str:
    resolved = path.resolve()
    root_resolved = root.resolve()
    try:
        return resolved.relative_to(root_resolved).as_posix()
    except ValueError as exc:
        raise ValueError(f'Path escapes root: {path}') from exc


def copy_atomic(src: Path, dst: Path, mode: int | None = None) -> None:
    ensure_dir(dst.parent)
    data = src.read_bytes()
    atomic_write_bytes(dst, data, mode=mode)


def iter_input_files(inputs: Iterable[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for input_path in inputs:
        path = input_path.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file())
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            yield candidate


def iter_tracked_files(target: Path, include_sources: bool = False) -> Iterator[Path]:
    target = target.resolve()
    excluded_roots = {'versions', 'reports', 'raw', '.cache'}
    if not include_sources:
        excluded_prefixes = {Path('references/sources'), Path('references/holdout')}
    else:
        excluded_prefixes = set()
    for path in sorted(p for p in target.rglob('*') if p.is_file()):
        rel = path.relative_to(target)
        if rel.parts and rel.parts[0] in excluded_roots:
            continue
        if rel.name == '.persona-distiller.lock':
            continue
        if any(rel == prefix or prefix in rel.parents for prefix in excluded_prefixes):
            continue
        yield path


def scan_secrets(root: Path, exclude_dirs: set[str] | None = None) -> list[dict[str, Any]]:
    exclude_dirs = exclude_dirs or {'versions', 'raw', '.git', '__pycache__'}
    findings: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        rel = path.relative_to(root)
        if any(part in exclude_dirs for part in rel.parts):
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for name, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count('\n', 0, match.start()) + 1
                findings.append({'file': rel.as_posix(), 'line': line, 'type': name})
    return findings


def redact_secrets(text: str) -> tuple[str, list[str]]:
    redacted = text
    hits: list[str] = []
    for name, pattern in SECRET_PATTERNS.items():
        if pattern.search(redacted):
            hits.append(name)
            redacted = pattern.sub(f'[REDACTED:{name}]', redacted)
    return redacted, hits


def markdown_claim_markers(path: Path) -> set[str]:
    if not path.exists():
        return set()
    text = path.read_text(encoding='utf-8')
    return set(re.findall(r'<!--\s*claim:(clm-[a-f0-9]{12})\s*-->', text))


@contextlib.contextmanager
def target_lock(target: Path) -> Iterator[None]:
    lock = target / '.persona-distiller.lock'
    ensure_dir(target)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(f'Target is locked: {lock}. Remove only after confirming no process is active.') from exc
    try:
        os.write(fd, f'pid={os.getpid()} created={utc_now()}\n'.encode('utf-8'))
        os.close(fd)
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def remove_tree(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)
