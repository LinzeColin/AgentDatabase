#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, atomic_write_text, ensure_target, sha256_file, utc_now

LANE_FILES = [
    ('01', 'writings', 'Writings and systematic works'),
    ('02', 'conversations', 'Conversations and interviews'),
    ('03', 'expression', 'Expression DNA and micro-behavior'),
    ('04', 'external', 'External views, criticism, and counterexamples'),
    ('05', 'decisions', 'Decisions and actions'),
    ('06', 'timeline', 'Timeline, stages, and drift'),
]


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a deterministic index of six research lanes.')
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    ensure_target(target)
    research = target / 'references' / 'research'
    sections: list[str] = ['# Merged research index', '', f'Generated: {utc_now()}', '']
    manifest = {'generated_at': utc_now(), 'lanes': []}
    missing = []
    for number, lane, title in LANE_FILES:
        path = research / f'{number}-{lane}.md'
        if not path.exists():
            missing.append(path.name)
            manifest['lanes'].append({'lane': lane, 'path': path.name, 'status': 'missing'})
            continue
        text = path.read_text(encoding='utf-8').strip()
        placeholder = 'Pending' in text and len(text) < 900
        status = 'placeholder' if placeholder else ('empty' if not text else 'present')
        entry = {
            'lane': lane,
            'title': title,
            'path': path.name,
            'status': status,
            'sha256': sha256_file(path),
            'characters': len(text),
        }
        manifest['lanes'].append(entry)
        sections.extend([
            f'## {number}. {title}',
            '',
            f'- File: `{path.name}`',
            f'- Status: `{status}`',
            f'- SHA-256: `{entry["sha256"]}`',
            '',
            text,
            '',
        ])
    atomic_write_text(research / 'merged.md', '\n'.join(sections).rstrip() + '\n')
    atomic_write_json(research / 'research-manifest.json', manifest, mode=0o600)
    result = {'ok': not missing, 'missing': missing, 'output': str(research / 'merged.md'), 'manifest': manifest}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if missing else 0


if __name__ == '__main__':
    raise SystemExit(main())
