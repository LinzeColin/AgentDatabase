#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import stat
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from common import SECRET_PATTERNS, atomic_write_json, sha256_file

REGISTRY_SCHEMA_VERSION = '1.0'
PRIVATE_ORIGINS = {'private', 'self'}
SAFE_COMPONENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$')
SAFE_SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
HEX_SHA256 = re.compile(r'^[0-9a-f]{64}$')
TEXT_SUFFIXES = {
    '.csv', '.json', '.jsonl', '.md', '.py', '.rst', '.sh', '.toml', '.tsv', '.txt', '.yaml', '.yml',
}

CATEGORIES: tuple[dict[str, str], ...] = (
    {'folder': '技术工程', 'identity_family_id': 'technical-engineer', 'identity_mode': 'single'},
    {'folder': '企业领导', 'identity_family_id': 'entrepreneur-operator', 'identity_mode': 'single'},
    {'folder': '金融投资', 'identity_family_id': 'investor-capital-allocator', 'identity_mode': 'single'},
    {'folder': '软开设计', 'identity_family_id': 'developer-designer', 'identity_mode': 'single'},
    {'folder': '思想教育', 'identity_family_id': 'thinker-educator', 'identity_mode': 'single'},
    {'folder': '政治法律', 'identity_family_id': 'political-legal', 'identity_mode': 'single'},
    {'folder': '多重身份', 'identity_family_id': 'multi-identity', 'identity_mode': 'multi'},
)
CATEGORY_BY_FOLDER = {item['folder']: item for item in CATEGORIES}
CATEGORY_BY_IDENTITY = {item['identity_family_id']: item for item in CATEGORIES}


def default_registry_root() -> Path:
    return Path(__file__).resolve().parents[1] / '产物登记'


def canonical_key(name: str, subject_origin: str) -> str:
    normalized = unicodedata.normalize('NFKC', name).casefold()
    normalized = re.sub(r'[\s\-_·•.]+', '', normalized)
    if not normalized:
        raise ValueError('target name becomes empty after normalization')
    return f'{subject_origin}:{normalized}'


def subject_uid(name: str, subject_origin: str) -> str:
    digest = hashlib.sha256(canonical_key(name, subject_origin).encode('utf-8')).hexdigest()
    return f'person-{digest[:16]}'


def _safe_zip_members(archive: zipfile.ZipFile) -> tuple[str, dict[str, zipfile.ZipInfo]]:
    members: dict[str, zipfile.ZipInfo] = {}
    top_levels: set[str] = set()
    for info in archive.infolist():
        name = info.filename
        if name in members:
            raise ValueError(f'duplicate ZIP member: {name}')
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or '\x00' in name:
            raise ValueError(f'unsafe ZIP member: {name}')
        if not path.parts:
            raise ValueError('empty ZIP member name')
        mode = (info.external_attr >> 16) & 0o170000
        if mode == stat.S_IFLNK:
            raise ValueError(f'ZIP symlink is forbidden: {name}')
        top_levels.add(path.parts[0])
        members[name] = info
    if len(top_levels) != 1:
        raise ValueError(f'target package must have exactly one top-level directory; found {sorted(top_levels)}')
    return next(iter(top_levels)), members


def _read_json_member(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        value = json.loads(archive.read(name).decode('utf-8'))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'invalid JSON member {name}: {exc}') from exc
    if not isinstance(value, dict):
        raise ValueError(f'JSON member must be an object: {name}')
    return value


def _verify_checksums(
    archive: zipfile.ZipFile,
    top_level: str,
    members: dict[str, zipfile.ZipInfo],
) -> dict[str, str]:
    checksum_member = f'{top_level}/checksums.sha256'
    try:
        lines = archive.read(checksum_member).decode('utf-8').splitlines()
    except (KeyError, UnicodeDecodeError) as exc:
        raise ValueError(f'invalid checksum member: {exc}') from exc
    records: dict[str, str] = {}
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        checksum, separator, relative = line.partition('  ')
        if not separator or not HEX_SHA256.fullmatch(checksum):
            raise ValueError(f'invalid checksum line {line_number}')
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or '..' in relative_path.parts or relative in records:
            raise ValueError(f'unsafe or duplicate checksum path: {relative}')
        member_name = f'{top_level}/{relative}'
        if member_name not in members or members[member_name].is_dir():
            raise ValueError(f'checksum references missing member: {relative}')
        actual = hashlib.sha256(archive.read(member_name)).hexdigest()
        if actual != checksum:
            raise ValueError(f'checksum mismatch: {relative}')
        records[relative] = checksum
    if not records:
        raise ValueError('target checksum file contains no payload files')
    return records


def _scan_zip_secrets(archive: zipfile.ZipFile, top_level: str, members: dict[str, zipfile.ZipInfo]) -> None:
    findings: list[str] = []
    for name, info in members.items():
        if info.is_dir() or info.file_size > 5 * 1024 * 1024:
            continue
        relative = PurePosixPath(name).relative_to(top_level)
        if relative.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        try:
            text = archive.read(name).decode('utf-8')
        except UnicodeDecodeError:
            continue
        for pattern_name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f'{relative.as_posix()}:{pattern_name}')
    if findings:
        raise ValueError('secret-like content detected: ' + ', '.join(findings[:10]))


def category_for_identity(selection: dict[str, Any]) -> dict[str, str]:
    mode = selection.get('mode')
    if mode == 'multi':
        return CATEGORY_BY_IDENTITY['multi-identity']
    if mode != 'single':
        raise ValueError(f'unsupported identity mode: {mode!r}')
    primary = selection.get('primary')
    category = CATEGORY_BY_IDENTITY.get(str(primary))
    if not category or category['identity_mode'] != 'single':
        raise ValueError(f'unsupported primary identity: {primary!r}')
    return category


def inspect_target_zip(zip_path: Path) -> dict[str, Any]:
    zip_path = zip_path.expanduser().resolve()
    if not zip_path.is_file() or zip_path.suffix.casefold() != '.zip':
        raise ValueError(f'target product must be a ZIP file: {zip_path}')
    with zipfile.ZipFile(zip_path) as archive:
        top_level, members = _safe_zip_members(archive)
        required = {
            f'{top_level}/SKILL.md',
            f'{top_level}/meta.json',
            f'{top_level}/PACKAGE_MANIFEST.json',
            f'{top_level}/checksums.sha256',
        }
        missing = sorted(required - set(members))
        if missing:
            raise ValueError(f'target package missing required members: {missing}')
        forbidden_fragments = ('/raw/', '/references/holdout/', '/references/sources/')
        forbidden = sorted(name for name in members if any(fragment in f'/{name}' for fragment in forbidden_fragments))
        if forbidden:
            raise ValueError(f'target package contains private build material: {forbidden[:10]}')
        checksum_records = _verify_checksums(archive, top_level, members)
        manifest = _read_json_member(archive, f'{top_level}/PACKAGE_MANIFEST.json')
        meta = _read_json_member(archive, f'{top_level}/meta.json')
        manifest_files = manifest.get('files')
        if not isinstance(manifest_files, list):
            raise ValueError('target PACKAGE_MANIFEST.json files must be an array')
        manifest_records: dict[str, str] = {}
        for item in manifest_files:
            if not isinstance(item, dict):
                raise ValueError('target manifest file entries must be objects')
            path = item.get('path')
            checksum = item.get('sha256')
            if not isinstance(path, str) or not isinstance(checksum, str) or path in manifest_records:
                raise ValueError('target manifest contains an invalid or duplicate file entry')
            manifest_records[path] = checksum
        if manifest_records != checksum_records:
            raise ValueError('target manifest and checksum records disagree')
        privacy = manifest.get('privacy')
        expected_privacy = {
            'raw_included': False,
            'holdout_included': False,
            'private_source_bodies_included': False,
            'runtime_history_reset': True,
        }
        if not isinstance(privacy, dict) or any(privacy.get(key) != value for key, value in expected_privacy.items()):
            raise ValueError('target package privacy contract is missing or unsafe')
        if manifest.get('builder') != 'persona-distiller' or manifest.get('builder_version') != 'v0.0.0.3':
            raise ValueError('target package was not built by persona-distiller v0.0.0.3')
        if manifest.get('top_level_count') != 1:
            raise ValueError('target package manifest must declare one top-level directory')
        if meta.get('subject_origin') in PRIVATE_ORIGINS:
            raise ValueError('private/self products cannot be published in this public GitHub registry')
        name = meta.get('name')
        slug = meta.get('slug')
        model_version = manifest.get('model_version')
        if not isinstance(name, str) or not name.strip():
            raise ValueError('target meta.json name is required')
        if not isinstance(slug, str) or not SAFE_SLUG.fullmatch(slug):
            raise ValueError(f'invalid target slug: {slug!r}')
        if top_level != slug:
            raise ValueError(f'ZIP top-level directory {top_level!r} must match target slug {slug!r}')
        if not isinstance(model_version, str) or not SAFE_COMPONENT.fullmatch(model_version):
            raise ValueError(f'invalid model version: {model_version!r}')
        if meta.get('model_version') != model_version:
            raise ValueError('target meta and package manifest model versions disagree')
        selection = meta.get('identity_selection')
        if not isinstance(selection, dict):
            raise ValueError('target identity_selection must be an object')
        category = category_for_identity(selection)
        _scan_zip_secrets(archive, top_level, members)
    origin = str(meta.get('subject_origin'))
    key = canonical_key(name, origin)
    return {
        'zip_path': zip_path,
        'sha256': sha256_file(zip_path),
        'size_bytes': zip_path.stat().st_size,
        'top_level': top_level,
        'canonical_name': name.strip(),
        'canonical_key': key,
        'subject_uid': subject_uid(name, origin),
        'subject_slug': slug,
        'subject_origin': origin,
        'identity_family_id': category['identity_family_id'],
        'identity_mode': category['identity_mode'],
        'category': category['folder'],
        'model_version': model_version,
        'builder_version': str(manifest.get('builder_version')),
        'artifact_created_at': str(manifest.get('created_at') or meta.get('updated_at') or ''),
    }


def load_records(registry_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    if not registry_root.is_dir():
        return records
    for path in sorted(registry_root.glob('*/*/registration.json')):
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f'invalid registration JSON {path}: {exc}') from exc
        if not isinstance(value, dict):
            raise ValueError(f'registration must be a JSON object: {path}')
        records.append((path, value))
    return records


def build_index(registry_root: Path, records: list[tuple[Path, dict[str, Any]]] | None = None) -> dict[str, Any]:
    records = load_records(registry_root) if records is None else records
    products: list[dict[str, Any]] = []
    counts = {item['folder']: 0 for item in CATEGORIES}
    for path, record in records:
        versions = record.get('versions') or []
        latest = sorted(versions, key=lambda item: (str(item.get('artifact_created_at', '')), str(item.get('model_version', ''))))[-1]
        category = str(record.get('registration_category'))
        if category in counts:
            counts[category] += 1
        products.append({
            'subject_uid': record.get('subject_uid'),
            'canonical_name': record.get('canonical_name'),
            'subject_slug': record.get('subject_slug'),
            'subject_origin': record.get('subject_origin'),
            'registration_category': category,
            'identity_family_id': record.get('identity_family_id'),
            'registration': path.relative_to(registry_root).as_posix(),
            'latest_model_version': latest.get('model_version'),
            'latest_artifact': f"{path.parent.relative_to(registry_root).as_posix()}/{latest.get('artifact')}",
            'latest_sha256': latest.get('sha256'),
            'version_count': len(versions),
        })
    products.sort(key=lambda item: (str(item['registration_category']), str(item['canonical_name']).casefold(), str(item['subject_uid'])))
    return {
        'schema_version': REGISTRY_SCHEMA_VERSION,
        'generated': True,
        'uniqueness_scope': 'all-seven-categories',
        'category_counts': counts,
        'products': products,
    }


def write_index(registry_root: Path, records: list[tuple[Path, dict[str, Any]]] | None = None) -> dict[str, Any]:
    index = build_index(registry_root, records)
    atomic_write_json(registry_root / 'index.json', index)
    return index


def register_product(zip_path: Path, registry_root: Path | None = None) -> dict[str, Any]:
    registry_root = (registry_root or default_registry_root()).expanduser().resolve()
    product = inspect_target_zip(zip_path)
    category = CATEGORY_BY_FOLDER[product['category']]
    category_root = registry_root / category['folder']
    if not (category_root / '_category.json').is_file():
        raise ValueError(f'registry category is not initialized: {category_root}')
    records = load_records(registry_root)
    existing: tuple[Path, dict[str, Any]] | None = None
    for path, record in records:
        same_subject = (
            record.get('subject_uid') == product['subject_uid']
            or record.get('canonical_key') == product['canonical_key']
        )
        for version in record.get('versions') or []:
            if version.get('sha256') == product['sha256'] and not same_subject:
                raise ValueError(f'artifact hash is already registered to another subject: {path}')
        if same_subject:
            if existing and existing[0] != path:
                raise ValueError(f'subject is duplicated across registry folders: {existing[0]} and {path}')
            existing = (path, record)
    if existing:
        record_path, record = existing
        if record.get('registration_category') != product['category']:
            raise ValueError(
                f'subject is already registered under {record.get("registration_category")}; '
                'reclassification must move the canonical record instead of copying it'
            )
        if record_path.parent.name != product['subject_slug']:
            raise ValueError(
                f'subject slug differs from canonical registration: {record_path.parent.name} vs {product["subject_slug"]}'
            )
    else:
        record_path = category_root / product['subject_slug'] / 'registration.json'
        if record_path.parent.exists():
            raise ValueError(f'subject folder already exists without a matching canonical record: {record_path.parent}')
        record = {
            'schema_version': REGISTRY_SCHEMA_VERSION,
            'subject_uid': product['subject_uid'],
            'canonical_name': product['canonical_name'],
            'canonical_key': product['canonical_key'],
            'subject_slug': product['subject_slug'],
            'subject_origin': product['subject_origin'],
            'registration_category': product['category'],
            'identity_family_id': product['identity_family_id'],
            'identity_mode': product['identity_mode'],
            'versions': [],
        }
    versions = record.get('versions')
    if not isinstance(versions, list):
        raise ValueError(f'invalid versions array: {record_path}')
    for version in versions:
        if version.get('model_version') != product['model_version']:
            continue
        if version.get('sha256') != product['sha256']:
            raise ValueError(
                f'model version {product["model_version"]} is already registered with a different artifact hash'
            )
        artifact = record_path.parent / str(version.get('artifact'))
        if artifact.is_file() and sha256_file(artifact) == product['sha256']:
            index = write_index(registry_root, records)
            return {
                'action': 'already-registered',
                'registration': str(record_path),
                'artifact': str(artifact),
                'subject_uid': product['subject_uid'],
                'category': product['category'],
                'index_products': len(index['products']),
            }
        break
    safe_model = product['model_version'].replace('-draft', '')
    artifact_name = f'{product["subject_slug"]}-persona-skill-v{safe_model}.zip'
    artifact_relative = Path('versions') / product['model_version'] / artifact_name
    artifact = record_path.parent / artifact_relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if artifact.exists() and sha256_file(artifact) != product['sha256']:
        raise ValueError(f'artifact destination exists with a different hash: {artifact}')
    shutil.copy2(product['zip_path'], artifact)
    version_record = {
        'model_version': product['model_version'],
        'artifact': artifact_relative.as_posix(),
        'sha256': product['sha256'],
        'size_bytes': product['size_bytes'],
        'builder_version': product['builder_version'],
        'artifact_created_at': product['artifact_created_at'],
    }
    replaced = False
    for index, version in enumerate(versions):
        if version.get('model_version') == product['model_version']:
            versions[index] = version_record
            replaced = True
            break
    if not replaced:
        versions.append(version_record)
    versions.sort(key=lambda item: (str(item.get('artifact_created_at', '')), str(item.get('model_version', ''))))
    atomic_write_json(record_path, record)
    records = [(path, value) for path, value in records if path != record_path]
    records.append((record_path, record))
    index = write_index(registry_root, records)
    return {
        'action': 'registered',
        'registration': str(record_path),
        'artifact': str(artifact),
        'subject_uid': product['subject_uid'],
        'category': product['category'],
        'sha256': product['sha256'],
        'index_products': len(index['products']),
    }


def validate_registry(registry_root: Path | None = None) -> dict[str, Any]:
    registry_root = (registry_root or default_registry_root()).expanduser().resolve()
    errors: list[str] = []
    expected_folders = set(CATEGORY_BY_FOLDER)
    actual_folders = {path.name for path in registry_root.iterdir() if path.is_dir()} if registry_root.is_dir() else set()
    if actual_folders != expected_folders:
        errors.append(f'category folders mismatch: expected={sorted(expected_folders)} actual={sorted(actual_folders)}')
    for category in CATEGORIES:
        path = registry_root / category['folder'] / '_category.json'
        try:
            value = json.loads(path.read_text(encoding='utf-8'))
            expected = {
                'schema_version': REGISTRY_SCHEMA_VERSION,
                'folder': category['folder'],
                'identity_family_id': category['identity_family_id'],
                'identity_mode': category['identity_mode'],
            }
            if value != expected:
                errors.append(f'category manifest mismatch: {path}')
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f'invalid category manifest {path}: {exc}')
    try:
        records = load_records(registry_root)
    except ValueError as exc:
        records = []
        errors.append(str(exc))
    seen_uids: dict[str, Path] = {}
    seen_keys: dict[str, Path] = {}
    seen_hashes: dict[str, Path] = {}
    for path, record in records:
        category = path.parents[1].name
        subject_dir = path.parent
        spec = CATEGORY_BY_FOLDER.get(category)
        required = {
            'schema_version', 'subject_uid', 'canonical_name', 'canonical_key', 'subject_slug',
            'subject_origin', 'registration_category', 'identity_family_id', 'identity_mode', 'versions',
        }
        missing = sorted(required - set(record))
        if missing:
            errors.append(f'{path}: missing fields {missing}')
            continue
        if record.get('schema_version') != REGISTRY_SCHEMA_VERSION:
            errors.append(f'{path}: unsupported schema_version')
        if not spec or record.get('registration_category') != category:
            errors.append(f'{path}: registration category does not match folder')
        elif (
            record.get('identity_family_id') != spec['identity_family_id']
            or record.get('identity_mode') != spec['identity_mode']
        ):
            errors.append(f'{path}: identity metadata does not match category')
        if record.get('subject_slug') != subject_dir.name or not SAFE_SLUG.fullmatch(str(record.get('subject_slug', ''))):
            errors.append(f'{path}: subject slug does not match folder')
        if record.get('subject_origin') in PRIVATE_ORIGINS:
            errors.append(f'{path}: private/self products are forbidden in the public registry')
        try:
            expected_key = canonical_key(str(record.get('canonical_name', '')), str(record.get('subject_origin', '')))
            expected_uid = subject_uid(str(record.get('canonical_name', '')), str(record.get('subject_origin', '')))
            if record.get('canonical_key') != expected_key or record.get('subject_uid') != expected_uid:
                errors.append(f'{path}: canonical identity fields are not deterministic')
        except ValueError as exc:
            errors.append(f'{path}: {exc}')
        for field, seen in [('subject_uid', seen_uids), ('canonical_key', seen_keys)]:
            value = str(record.get(field))
            if value in seen and seen[value] != path:
                errors.append(f'{field} duplicated across {seen[value]} and {path}')
            seen[value] = path
        versions = record.get('versions')
        if not isinstance(versions, list) or not versions:
            errors.append(f'{path}: versions must contain at least one release')
            continue
        seen_versions: set[str] = set()
        for version in versions:
            if not isinstance(version, dict):
                errors.append(f'{path}: version entry must be an object')
                continue
            model_version = str(version.get('model_version', ''))
            if model_version in seen_versions:
                errors.append(f'{path}: duplicate model version {model_version}')
            seen_versions.add(model_version)
            relative = Path(str(version.get('artifact', '')))
            if (
                relative.is_absolute()
                or '..' in relative.parts
                or len(relative.parts) != 3
                or relative.parts[0] != 'versions'
                or relative.parts[1] != model_version
            ):
                errors.append(f'{path}: invalid artifact path {relative}')
                continue
            artifact = (subject_dir / relative).resolve()
            try:
                artifact.relative_to(subject_dir.resolve())
            except ValueError:
                errors.append(f'{path}: artifact escapes subject folder')
                continue
            checksum = str(version.get('sha256', ''))
            if not artifact.is_file():
                errors.append(f'{path}: missing artifact {relative}')
                continue
            if not HEX_SHA256.fullmatch(checksum) or sha256_file(artifact) != checksum:
                errors.append(f'{path}: artifact checksum mismatch {relative}')
                continue
            if artifact.stat().st_size != version.get('size_bytes'):
                errors.append(f'{path}: artifact size mismatch {relative}')
            if checksum in seen_hashes and seen_hashes[checksum] != path:
                errors.append(f'artifact hash duplicated across {seen_hashes[checksum]} and {path}')
            seen_hashes[checksum] = path
            try:
                inspected = inspect_target_zip(artifact)
                comparisons = {
                    'subject_uid': record.get('subject_uid'),
                    'canonical_name': record.get('canonical_name'),
                    'subject_slug': record.get('subject_slug'),
                    'subject_origin': record.get('subject_origin'),
                    'category': record.get('registration_category'),
                    'identity_family_id': record.get('identity_family_id'),
                    'model_version': model_version,
                    'sha256': checksum,
                }
                for key, expected in comparisons.items():
                    if inspected.get(key) != expected:
                        errors.append(f'{path}: artifact {key} mismatch for {relative}')
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                errors.append(f'{path}: invalid artifact {relative}: {exc}')
    expected_index = build_index(registry_root, records)
    index_path = registry_root / 'index.json'
    try:
        actual_index = json.loads(index_path.read_text(encoding='utf-8'))
        if actual_index != expected_index:
            errors.append(f'{index_path}: generated index is stale or inconsistent')
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f'invalid registry index {index_path}: {exc}')
    return {
        'passed': not errors,
        'registry_root': str(registry_root),
        'categories': len(CATEGORIES),
        'products': len(records),
        'artifacts': sum(len(record.get('versions') or []) for _, record in records),
        'errors': errors,
    }
