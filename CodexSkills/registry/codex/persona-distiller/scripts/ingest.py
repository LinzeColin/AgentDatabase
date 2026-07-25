#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import email
import html
import json
import mailbox
import re
import sys
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    EMAIL_EXTENSIONS,
    LANES,
    OPAQUE_EXTENSIONS,
    STRUCTURED_EXTENSIONS,
    SUBTITLE_EXTENSIONS,
    SUPPORTED_EXTENSIONS,
    TEXT_EXTENSIONS,
    append_jsonl,
    atomic_write_bytes,
    atomic_write_text,
    ensure_dir,
    ensure_target,
    iter_input_files,
    read_jsonl,
    redact_secrets,
    relpath_inside,
    safe_filename,
    sha256_bytes,
    sha256_file,
    target_lock,
    utc_now,
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return '\n'.join(self.parts)


def decode_bytes(data: bytes) -> str:
    for encoding in ('utf-8-sig', 'utf-8', 'utf-16', 'gb18030', 'cp1252', 'latin-1'):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode('utf-8', errors='replace')


def normalize_whitespace(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip() + '\n' if text.strip() else ''


def normalize_subtitles(text: str) -> str:
    lines: list[str] = []
    previous = None
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        line = raw.strip()
        if not line or line.upper() == 'WEBVTT' or line.isdigit():
            continue
        if '-->' in line:
            continue
        line = re.sub(r'<[^>]+>', '', line)
        line = html.unescape(line).strip()
        if line and line != previous:
            lines.append(line)
            previous = line
    return normalize_whitespace('\n'.join(lines))


def normalize_structured(path: Path, text: str) -> str:
    suffix = path.suffix.lower()
    if suffix == '.json':
        try:
            return json.dumps(json.loads(text), ensure_ascii=False, indent=2) + '\n'
        except json.JSONDecodeError:
            return normalize_whitespace(text)
    if suffix == '.jsonl':
        output: list[str] = []
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                output.append(json.dumps(json.loads(line), ensure_ascii=False, sort_keys=True))
            except json.JSONDecodeError:
                output.append(json.dumps({'_line': line_no, '_unparsed': line}, ensure_ascii=False))
        return '\n'.join(output) + ('\n' if output else '')
    delimiter = '\t' if suffix == '.tsv' else ','
    rows: list[str] = []
    for row in csv.reader(text.splitlines(), delimiter=delimiter):
        rows.append('\t'.join(cell.strip() for cell in row))
    return normalize_whitespace('\n'.join(rows))


def message_text(message: email.message.Message) -> str:
    headers = []
    for key in ('Date', 'From', 'To', 'Cc', 'Subject', 'Message-ID'):
        value = message.get(key)
        if value:
            headers.append(f'{key}: {value}')
    bodies: list[str] = []
    parts: Iterable[email.message.Message] = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.get_content_disposition() == 'attachment':
            continue
        content_type = part.get_content_type()
        if content_type not in ('text/plain', 'text/html'):
            continue
        try:
            content = part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b''
            content = decode_bytes(payload)
        if not isinstance(content, str):
            content = str(content)
        if content_type == 'text/html':
            parser = HTMLTextExtractor()
            parser.feed(content)
            content = parser.text()
        if content.strip():
            bodies.append(content.strip())
    return normalize_whitespace('\n'.join(headers + [''] + bodies))


def normalize_email(path: Path, data: bytes) -> str:
    if path.suffix.lower() == '.eml':
        message = BytesParser(policy=policy.default).parsebytes(data)
        return message_text(message)
    # mailbox.mbox expects a filesystem path and handles Unix mbox separators.
    output: list[str] = []
    box = mailbox.mbox(path, factory=lambda f: BytesParser(policy=policy.default).parse(f))
    try:
        for index, message in enumerate(box, 1):
            output.append(f'===== MESSAGE {index} =====')
            output.append(message_text(message))
    finally:
        box.close()
    return normalize_whitespace('\n'.join(output))


def redact_pii(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    email_pattern = re.compile(r'(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])')
    phone_pattern = re.compile(r'(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)')
    if email_pattern.search(text):
        hits.append('email')
        text = email_pattern.sub('[REDACTED:email]', text)
    if phone_pattern.search(text):
        hits.append('phone')
        text = phone_pattern.sub('[REDACTED:phone]', text)
    return text, hits


def infer_dimensions(source_type: str) -> list[str]:
    value = source_type.lower()
    mapping = {
        'book': ['writings'], 'essay': ['writings'], 'paper': ['writings'], 'memo': ['writings'], 'blog': ['writings'],
        'interview': ['conversations'], 'conversation': ['conversations'], 'speech': ['conversations'], 'podcast': ['conversations'],
        'social': ['expression'], 'chat': ['expression'], 'micro-post': ['expression'],
        'critique': ['external'], 'biography': ['external'], 'reporting': ['external'], 'review': ['external'],
        'decision-record': ['decisions'], 'postmortem': ['decisions'], 'commit': ['decisions'], 'filing': ['decisions'],
        'timeline': ['timeline'], 'chronology': ['timeline'],
    }
    return mapping.get(value, [])


def main() -> int:
    parser = argparse.ArgumentParser(description='Ingest local materials into a Persona Distiller target.')
    parser.add_argument('target', type=Path)
    parser.add_argument('inputs', nargs='+', type=Path)
    parser.add_argument('--source-type', default='local-file')
    parser.add_argument('--tier', choices=['P1', 'P2', 'S1', 'S2', 'U'], default='U')
    parser.add_argument('--rights', default='user-provided-or-publicly-accessible-for-analysis; redistribution-not-assumed')
    parser.add_argument('--author')
    parser.add_argument('--published-at')
    parser.add_argument('--language')
    parser.add_argument('--dimension', action='append', choices=LANES, default=[])
    parser.add_argument('--holdout', action='store_true', help='Reserve material for evaluation; builders must never read it.')
    parser.add_argument('--abstract')
    parser.add_argument('--locator')
    parser.add_argument('--redact-pii', action='store_true')
    parser.add_argument('--no-redact-secrets', action='store_true')
    parser.add_argument('--no-copy-raw', action='store_true')
    parser.add_argument('--include-unsupported', action='store_true', help='Register otherwise unsupported extensions as opaque.')
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    if meta.get('status') == 'blocked':
        parser.error('target is blocked; record required consent/authority before ingestion')

    ledger_path = target / 'evidence' / 'source-ledger.jsonl'
    existing = read_jsonl(ledger_path)
    by_checksum = {record.get('checksum'): record for record in existing}
    dimensions = list(dict.fromkeys(args.dimension or infer_dimensions(args.source_type)))
    split = 'holdout' if args.holdout else 'train'
    results: list[dict[str, object]] = []

    with target_lock(target):
        for source in iter_input_files(args.inputs):
            suffix = source.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS and not args.include_unsupported:
                results.append({'file': str(source), 'status': 'skipped-unsupported'})
                continue

            raw_data = source.read_bytes()
            checksum = sha256_bytes(raw_data)
            source_id = f'src-{checksum[:12]}'
            prior = by_checksum.get(checksum)
            if prior:
                if prior.get('split') != split:
                    raise ValueError(
                        f'Cross-split duplicate would leak Holdout: {source} already registered as {prior.get("split")} ({source_id})'
                    )
                results.append({'file': str(source), 'source_id': source_id, 'status': 'duplicate-skipped'})
                continue

            filename = safe_filename(source.name)
            if split == 'holdout':
                body_dir = target / 'references' / 'holdout' / source_id
            else:
                body_dir = target / 'raw' / source_id
            raw_path: Path | None = None
            if not args.no_copy_raw or split == 'holdout':
                raw_path = body_dir / filename
                atomic_write_bytes(raw_path, raw_data, mode=0o600)

            normalized: str | None = None
            extraction_status = 'normalized'
            try:
                if suffix in TEXT_EXTENSIONS:
                    normalized = normalize_whitespace(decode_bytes(raw_data))
                elif suffix in STRUCTURED_EXTENSIONS:
                    normalized = normalize_structured(source, decode_bytes(raw_data))
                elif suffix in SUBTITLE_EXTENSIONS:
                    normalized = normalize_subtitles(decode_bytes(raw_data))
                elif suffix in EMAIL_EXTENSIONS:
                    normalized = normalize_email(source, raw_data)
                else:
                    extraction_status = 'needs_agent_read'
            except Exception as exc:
                extraction_status = 'failed'
                normalized = f'[Extraction failed: {type(exc).__name__}: {exc}]\n'

            redactions: list[str] = []
            normalized_path: Path | None = None
            normalized_checksum: str | None = None
            if normalized is not None:
                if not args.no_redact_secrets:
                    normalized, secret_hits = redact_secrets(normalized)
                    redactions.extend(secret_hits)
                if args.redact_pii:
                    normalized, pii_hits = redact_pii(normalized)
                    redactions.extend(pii_hits)
                normalized_filename = f'{source.stem}.normalized.txt'
                normalized_dir = (target / 'references' / 'holdout' / source_id) if split == 'holdout' else (target / 'references' / 'sources' / source_id)
                normalized_path = normalized_dir / safe_filename(normalized_filename)
                atomic_write_text(normalized_path, normalized, mode=0o600)
                normalized_checksum = sha256_file(normalized_path)

            record = {
                'source_id': source_id,
                'title': source.name,
                'author': args.author,
                'published_at': args.published_at,
                'accessed_at': utc_now(),
                'url': None,
                'local_path': relpath_inside(raw_path, target) if raw_path else None,
                'normalized_path': relpath_inside(normalized_path, target) if normalized_path else None,
                'source_type': args.source_type,
                'tier': args.tier,
                'rights': args.rights,
                'language': args.language,
                'split': split,
                'checksum': checksum,
                'normalized_checksum': normalized_checksum,
                'dimensions': dimensions,
                'derived_from': [],
                'extraction_status': extraction_status,
                'abstract': args.abstract,
                'locator': args.locator,
                'redactions': sorted(set(redactions)),
                'original_name': source.name,
                'created_at': utc_now(),
            }
            append_jsonl(ledger_path, record)
            by_checksum[checksum] = record
            results.append({'file': str(source), 'source_id': source_id, 'status': extraction_status, 'split': split})

    summary = {
        'target': str(target),
        'registered': sum(1 for item in results if item.get('status') in {'normalized', 'needs_agent_read', 'failed'}),
        'duplicates': sum(1 for item in results if item.get('status') == 'duplicate-skipped'),
        'unsupported': sum(1 for item in results if item.get('status') == 'skipped-unsupported'),
        'results': results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if any(item.get('status') == 'failed' for item in results) else 0


if __name__ == '__main__':
    raise SystemExit(main())
