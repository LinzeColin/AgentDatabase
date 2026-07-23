#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_text, ensure_dir, ensure_target, safe_filename, sha256_file, utc_now


def detect_kind(source: Path) -> str:
    if (source / 'work.md').exists() and (source / 'persona.md').exists():
        return 'dot'
    if (source / 'references' / 'research').is_dir() or any(source.rglob('01-writings.md')):
        return 'nuwa'
    skill = source / 'SKILL.md'
    if skill.is_file():
        text = skill.read_text(encoding='utf-8', errors='ignore')[:200000]
        if any(token in text.lower() for token in ('soul', '灵魂', '七层', '上帝')):
            return 'god'
    return 'unknown'


def copy_selected(source: Path, destination: Path, kind: str) -> list[dict[str, object]]:
    selected: list[Path] = []
    if kind == 'nuwa':
        selected.extend(path for path in source.rglob('*') if path.is_file() and ('research' in path.parts or path.name in {'SKILL.md', 'fidelity-scorecard.md', 'extraction-framework.md'}) )
    elif kind == 'dot':
        for name in ('SKILL.md', 'work.md', 'persona.md', 'correction.md', 'corrections.md', 'meta.json'):
            selected.extend(source.rglob(name))
        selected.extend(path for path in source.rglob('*') if path.is_file() and ('research' in path.parts or 'versions' in path.parts))
    elif kind == 'god':
        selected.extend(path for path in source.rglob('*') if path.is_file() and path.name in {'SKILL.md', 'README.md', 'README_CN.md'})
    else:
        selected.extend(path for path in source.rglob('*') if path.is_file())
    records = []
    seen = set()
    for path in sorted(selected):
        if path in seen:
            continue
        seen.add(path)
        try:
            rel = path.relative_to(source)
        except ValueError:
            rel = Path(safe_filename(path.name))
        dest = destination / rel
        ensure_dir(dest.parent)
        shutil.copy2(path, dest)
        records.append({'source': rel.as_posix(), 'destination': dest.as_posix(), 'sha256': sha256_file(dest), 'size': dest.stat().st_size})
    return records


def promote_dot(source: Path, target: Path, force: bool) -> list[str]:
    promoted: list[str] = []
    for name in ('persona.md', 'work.md'):
        candidates = list(source.rglob(name))
        if not candidates:
            continue
        destination = target / name
        current = destination.read_text(encoding='utf-8') if destination.exists() else ''
        blank_template = ('Status: draft' in current) or (('待研究' in current or 'Pending' in current) and '<!-- claim:' not in current)
        if not blank_template and not force:
            raise ValueError(f'{name} is no longer a blank template; pass --force to promote legacy content')
        header = (
            f'# Legacy {name[:-3].title()} import\n\n'
            '> Imported as an unverified candidate. Rebuild Claim IDs and evidence before release.\n\n'
        )
        atomic_write_text(destination, header + candidates[0].read_text(encoding='utf-8', errors='replace'))
        promoted.append(name)
    return promoted


def main() -> int:
    parser = argparse.ArgumentParser(description='Conservatively import Nuwa, God, or dot-skill artifacts without treating prompts as evidence.')
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    parser.add_argument('--from', dest='kind', choices=['auto', 'nuwa', 'god', 'dot', 'unknown'], default='auto')
    parser.add_argument('--promote', action='store_true', help='For dot imports, copy work/persona into current draft with an unverified banner.')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    target = args.target.expanduser().resolve()
    ensure_target(target)
    if not source.is_dir():
        parser.error(f'source directory does not exist: {source}')
    kind = detect_kind(source) if args.kind == 'auto' else args.kind
    destination = target / 'references' / 'legacy' / f'{kind}-{utc_now().replace(":", "").replace("-", "")}'
    records = copy_selected(source, destination, kind)
    promoted: list[str] = []
    if args.promote:
        if kind != 'dot':
            parser.error('--promote currently supports dot-style persona.md/work.md only; other formats require evidence-aware synthesis')
        promoted = promote_dot(source, target, args.force)

    lines = [
        '# Legacy migration report', '',
        f'- Imported at: `{utc_now()}`',
        f'- Detected format: `{kind}`',
        f'- Source: `{source}`',
        f'- Files copied: `{len(records)}`',
        f'- Promoted current artifacts: `{", ".join(promoted) or "none"}`', '',
        '## Safety status', '',
        '- Imported prompts and generated prose are not evidence.',
        '- Reconstruct source IDs and atomic Claims before release.',
        '- Keep God-style existential content in `hypotheses.md` only.',
        '- Keep Holdout material isolated; imported known-case examples may be contaminated and should be replaced.', '',
        '## Recommended next step', '',
        'Run Source Adjudicator and Claim Extractor against the original lawful source corpus, then compare imported conclusions as hypotheses rather than ground truth.',
    ]
    atomic_write_text(destination / 'migration-report.md', '\n'.join(lines) + '\n')
    print(json.dumps({'kind': kind, 'destination': str(destination), 'files': len(records), 'promoted': promoted}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
