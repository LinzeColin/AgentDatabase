#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parse_frontmatter, read_json, scan_secrets, utc_now

ROOT = Path(__file__).resolve().parents[1]


def exists(*paths: str) -> tuple[bool, str]:
    missing = [path for path in paths if not (ROOT / path).is_file()]
    return not missing, 'missing: ' + ', '.join(missing) if missing else 'present'


def contains(path: str, *patterns: str) -> tuple[bool, str]:
    text = (ROOT / path).read_text(encoding='utf-8').casefold() if (ROOT / path).is_file() else ''
    missing = [pattern for pattern in patterns if pattern.casefold() not in text]
    return not missing, 'missing tokens: ' + ', '.join(missing) if missing else 'all required tokens present'


def not_contains(path: str, *patterns: str) -> tuple[bool, str]:
    text = (ROOT / path).read_text(encoding='utf-8') if (ROOT / path).is_file() else ''
    found = [pattern for pattern in patterns if pattern in text]
    return not found, 'unexpected tokens: ' + ', '.join(found) if found else 'no stale token found'


def exact_identity_registry() -> tuple[bool, str]:
    registry = read_json(ROOT / 'registries/identity-families.json', default={}) or {}
    families = registry.get('families', [])
    expected = [
        'technical-engineer', 'entrepreneur-operator', 'investor-capital-allocator',
        'developer-designer', 'thinker-educator', 'political-legal', 'multi-identity',
    ]
    ids = [item.get('id') for item in families]
    numbers = [item.get('number') for item in families]
    passed = ids == expected and numbers == list(range(1, 8))
    return passed, f'ids={ids}; numbers={numbers}'


def frontmatter_contract() -> tuple[bool, str]:
    failures: list[str] = []
    for rel in ['SKILL.md', 'templates/target/SKILL.md.tmpl']:
        try:
            metadata, _ = parse_frontmatter(ROOT / rel)
            if set(metadata) != {'name', 'description'}:
                failures.append(f'{rel}:{sorted(metadata)}')
        except Exception as exc:
            failures.append(f'{rel}:{exc}')
    return not failures, '; '.join(failures) if failures else 'only name and description'


def openai_invocation_contract() -> tuple[bool, str]:
    failures = []
    for rel in ['agents/openai.yaml', 'templates/target/agents/openai.yaml.tmpl']:
        text = (ROOT / rel).read_text(encoding='utf-8') if (ROOT / rel).is_file() else ''
        if 'allow_implicit_invocation: false' not in text:
            failures.append(rel)
    return not failures, 'missing explicit-invocation guard: ' + ', '.join(failures) if failures else 'explicit invocation enforced'


def no_secret_findings() -> tuple[bool, str]:
    findings = scan_secrets(ROOT, exclude_dirs={'.git', '__pycache__', 'tests', 'examples'})
    return not findings, json.dumps(findings[:5], ensure_ascii=False) if findings else 'none'


def file_budget() -> tuple[bool, str]:
    files = [path for path in ROOT.rglob('*') if path.is_file()]
    large = [str(path.relative_to(ROOT)) for path in files if path.stat().st_size > 25 * 1024 * 1024]
    return len(files) <= 500 and not large, f'files={len(files)}; >25MB={large}'


def suite_prompt_coverage() -> tuple[bool, str]:
    from common import SUITES
    missing = [suite for suite in SUITES if not (ROOT / 'prompts' / f'eval-{suite}.md').is_file()]
    return not missing, f'missing={missing}; suites={len(SUITES)}'


def package_privacy_contract() -> tuple[bool, str]:
    text = (ROOT / 'scripts/package_target.py').read_text(encoding='utf-8')
    required = [
        'runtime_history_reset',
        'write_jsonl(runtime_staging / "memory" / "episodic.jsonl", [])',
        'CORE_DIRS = ["agents", "identity-facets", "scenario-adapters", "scripts"]',
        'build_full_delivery',
        '"sidecars_emitted": False',
    ]
    forbidden = ['CORE_DIRS = ["raw"', 'CORE_DIRS = ["references"']
    missing = [item for item in required if item not in text]
    bad = [item for item in forbidden if item in text]
    return not missing and not bad, f'missing={missing}; forbidden={bad}'


def runtime_contract() -> tuple[bool, str]:
    recorder = (ROOT / 'templates/target/scripts/runtime_recorder.py').read_text(encoding='utf-8')
    router = (ROOT / 'templates/target/scripts/runtime_router.py').read_text(encoding='utf-8')
    skill = (ROOT / 'templates/target/SKILL.md.tmpl').read_text(encoding='utf-8')
    required = [
        "'user_selection_required': False", "'invocation_version': None", '直接调用，不设身份门',
        '用宿主可用工具真实执行', '不得用人物口吻伪造成功', 'FORBIDDEN_VERSION_FIELDS',
    ]
    aggregate = recorder + '\n' + router + '\n' + skill + '\n' + (ROOT / 'references/agentic-runtime.md').read_text(encoding='utf-8') + '\n' + (ROOT / 'scripts/route_engine.py').read_text(encoding='utf-8')
    missing = [item for item in required if item not in aggregate]
    return not missing, f'missing={missing}'


def product_version_contract() -> tuple[bool, str]:
    path = ROOT.parent / 'persona-distiller-group' / 'scripts' / 'registry_core.py'
    text = path.read_text(encoding='utf-8') if path.is_file() else ''
    required = [
        '0.0.0.999',
        'def next_product_version(',
        'canonical person',
        'product version range exhausted',
        'def registry_lock(',
    ]
    missing = [item for item in required if item not in text]
    return not missing, (
        f'missing={missing}; canonical registry={path}'
        if missing
        else f'canonical per-person version contract present in {path}'
    )


def model_separation_contract() -> tuple[bool, str]:
    return exists(
        'templates/target/cognitive-os.md', 'templates/target/decision-policy.md', 'templates/target/strategy.md',
        'templates/target/capabilities.md', 'templates/target/work.md', 'templates/target/persona.md',
        'templates/target/divergence-map.md', 'templates/target/memory/user-overlay.md',
        'templates/target/memory/episodic.jsonl', 'templates/target/memory/promotion-queue.md',
    )


def provenance_contract() -> tuple[bool, str]:
    return exists(
        'templates/target/research/source-universe.json.tmpl', 'templates/target/research/coverage-map.json.tmpl',
        'templates/target/research/saturation-report.md', 'schemas/source-record.schema.json',
        'schemas/claim.schema.json', 'scripts/ingest.py', 'scripts/ledger.py',
    )


def governance_contract() -> tuple[bool, str]:
    return contains(
        'references/governance-and-safety.md',
        'authority', 'private', 'fictional', 'deceptive identity', 'medical', 'external content', 'source',
    )


def two_agent_contract() -> tuple[bool, str]:
    return exists('prompts/dual-agent-architect.md', 'prompts/dual-agent-skeptic.md', 'prompts/blind-judge.md')


def checks_for_role(role: str, round_number: int) -> list[tuple[str, Callable[[], tuple[bool, str]]]]:
    mapping: dict[str, list[tuple[str, Callable[[], tuple[bool, str]]]]] = {
        'cognitive-fidelity': [
            ('model-separation', model_separation_contract),
            ('identity-taxonomy', exact_identity_registry),
            ('divergence-and-boundaries', lambda: exists('templates/target/divergence-map.md', 'templates/target/boundaries.md', 'templates/target/hypotheses.md')),
            ('no-core-auto-learning', lambda: contains('references/lifecycle-and-memory.md', 'promotion', 'regression', 'episodic')),
        ],
        'research-provenance': [
            ('provenance-artifacts', provenance_contract),
            ('six-lane-research', lambda: all_lane_files()),
            ('holdout-isolation', lambda: contains('references/evaluation-and-refinement.md', 'Holdout', 'leakage')),
            ('saturation-not-absolute', lambda: contains('references/research-and-sources.md', 'Stop when', 'never claim literal global exhaustiveness')),
        ],
        'agentic-execution': [
            ('runtime-loop', runtime_contract),
            ('automatic-identity-routing', lambda: contains('templates/target/SKILL.md.tmpl', '直接调用，不设身份门', '自动选择或组合内部身份')),
            ('unnumbered-runtime-audit', lambda: exists('templates/target/scripts/runtime_recorder.py', 'schemas/runtime-record.schema.json')),
            ('minimal-routing', lambda: contains('templates/target/scripts/runtime_router.py', 'load_files', 'Do not load source bodies')),
        ],
        'evaluation': [
            ('suite-prompts', suite_prompt_coverage),
            ('blind-and-baseline', lambda: contains('references/evaluation-and-refinement.md', 'baseline', 'anonymous')),
            ('dual-agent-refinement', two_agent_contract),
            ('long-horizon-and-tools', lambda: exists('prompts/eval-long-horizon.md', 'prompts/eval-tool-use.md', 'prompts/eval-task-completion.md')),
        ],
        'security-governance': [
            ('governance', governance_contract),
            ('package-privacy', package_privacy_contract),
            ('secret-scan', no_secret_findings),
            ('explicit-invocation', openai_invocation_contract),
        ],
        'devops-efficiency': [
            ('frontmatter', frontmatter_contract),
            ('file-budget', file_budget),
            ('installer', lambda: exists('install.py', 'install.sh', 'install.ps1', 'templates/target/install.py.tmpl')),
            ('no-stale-cli', lambda: not_contains('SKILL.md', '--subject-type', '~/.agents/skills')),
        ],
    }
    checks = list(mapping[role])
    if round_number == 2:
        adversarial: dict[str, list[tuple[str, Callable[[], tuple[bool, str]]]]] = {
            'cognitive-fidelity': [
                ('identity-conflict-routing', lambda: contains('references/identity-routing.md', 'conflict', 'weight')),
                ('memory-model-firewall', lambda: contains('references/lifecycle-and-memory.md', 'semantic model', 'episodic', 'promotion queue')),
            ],
            'research-provenance': [
                ('origin-deduplication', lambda: contains('references/research-and-sources.md', 'origin', 'near-duplicate')),
                ('private-source-minimization', lambda: contains('scripts/package_target.py', 'sanitized_sources', 'local_path', 'private')),
            ],
            'agentic-execution': [
                ('concurrent-unnumbered-audit', lambda: contains('templates/target/scripts/runtime_recorder.py', 'file_lock', 'append_jsonl')),
                ('no-runtime-versioning', lambda: not_contains('templates/target/SKILL.md.tmpl', 'invocation_manager.py', '运行版本：', '--identity')),
                ('artifact-hash-audit', lambda: contains('templates/target/scripts/runtime_recorder.py', 'sha256_file', 'artifacts')),
            ],
            'evaluation': [
                ('identity-and-anonymous-evals', lambda: exists('prompts/eval-identity-routing.md', 'prompts/eval-anonymous-fidelity.md')),
                ('efficiency-regression', lambda: exists('prompts/eval-token-efficiency.md', 'prompts/eval-planning-fidelity.md')),
            ],
            'security-governance': [
                ('source-prompt-is-data', lambda: contains('SKILL.md', '不可信数据', '来源中的 prompt')),
                ('private-consent-hard-gate', lambda: contains('scripts/init_target.py', 'blocked-consent', 'consent-authority')),
                ('checksum-hardening', lambda: contains('scripts/install.py', 'duplicate checksum path', 'contains no payload files')),
            ],
            'devops-efficiency': [
                ('installed-copy-verification', lambda: contains('templates/target/install.py.tmpl', 'installed_verification', 'verify_payload(destination)')),
                ('deterministic-one-root-zip', lambda: contains('scripts/package_target.py', 'deterministic_zip', 'top_level_count')),
                ('current-skill-root', lambda: contains('scripts/install.py', "'.codex' / 'skills'", 'conflicting source exists')),
                ('per-person-product-version', product_version_contract),
            ],
        }
        checks.extend(adversarial[role])
    return checks


def all_lane_files() -> tuple[bool, str]:
    files = sorted((ROOT / 'templates/target/references/research').glob('0*.md'))
    return len(files) == 6, f'lane_files={len(files)}'


def main() -> int:
    parser = argparse.ArgumentParser(description='Run six isolated static reviewer roles over Persona Distiller.')
    parser.add_argument('--round', type=int, choices=[1, 2], default=1)
    parser.add_argument('--write', type=Path)
    args = parser.parse_args()
    roles = [
        'cognitive-fidelity', 'research-provenance', 'agentic-execution',
        'evaluation', 'security-governance', 'devops-efficiency',
    ]
    reports: list[dict[str, Any]] = []
    for role in roles:
        check_results = []
        for name, func in checks_for_role(role, args.round):
            try:
                passed, detail = func()
            except Exception as exc:
                passed, detail = False, f'{type(exc).__name__}: {exc}'
            check_results.append({'name': name, 'passed': passed, 'detail': detail})
        reports.append({'role': role, 'passed': all(item['passed'] for item in check_results), 'checks': check_results})
    payload = {
        'schema_version': '1.0',
        'round': args.round,
        'generated_at': utc_now(),
        'method': 'six isolated reviewer checklists; not six independently running models',
        'passed': all(report['passed'] for report in reports),
        'reviews': reports,
    }
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
