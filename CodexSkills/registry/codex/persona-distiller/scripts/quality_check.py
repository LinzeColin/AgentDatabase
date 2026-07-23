#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    LANES,
    PROFILE_THRESHOLDS,
    SUITES,
    atomic_write_json,
    atomic_write_text,
    ensure_target,
    markdown_claim_markers,
    parse_frontmatter,
    read_jsonl,
    scan_secrets,
    utc_now,
)
from ledger import validate_target as validate_ledgers

REQUIRED_FILES = (
    'SKILL.md', 'README.md', 'meta.json', 'identity-catalog.json', 'route-manifest.json',
    'facts.md', 'cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md',
    'persona.md', 'work.md', 'boundaries.md', 'hypotheses.md', 'divergence-map.md',
    'agents/openai.yaml', 'scripts/invocation_manager.py', 'scripts/runtime_router.py',
    'runtime/state.json', 'evidence/source-ledger.jsonl',
    'evidence/claims.jsonl', 'corrections/corrections.jsonl',
    'corrections/ACTIVE.md', 'evals/cases.jsonl', 'evals/results.jsonl',
)
LANE_FILES = {
    'writings': 'references/research/01-writings.md',
    'conversations': 'references/research/02-conversations.md',
    'expression': 'references/research/03-expression.md',
    'external': 'references/research/04-external.md',
    'decisions': 'references/research/05-decisions.md',
    'timeline': 'references/research/06-timeline.md',
}
MODEL_CATEGORIES = {'mental-model'}
HEURISTIC_CATEGORIES = {'heuristic'}
RENDER_FILES = ('facts.md', 'cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md', 'persona.md', 'work.md', 'boundaries.md', 'hypotheses.md', 'divergence-map.md')


class Report:
    def __init__(self, target: Path, phase: str, profile: str) -> None:
        self.target = target
        self.phase = phase
        self.profile = profile
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []
        self.metrics: dict[str, Any] = {}
        self.checks: list[dict[str, Any]] = []

    def error(self, code: str, message: str) -> None:
        self.errors.append({'code': code, 'message': message})

    def warn(self, code: str, message: str) -> None:
        self.warnings.append({'code': code, 'message': message})

    def check(self, name: str, passed: bool, detail: str = '') -> None:
        self.checks.append({'name': name, 'passed': passed, 'detail': detail})

    def threshold(self, passed: bool, code: str, message: str, allow_provisional: bool) -> None:
        if passed:
            return
        if allow_provisional:
            self.warn(code, message)
        else:
            self.error(code, message)

    def as_dict(self, strict: bool = False) -> dict[str, Any]:
        passed = not self.errors and not (strict and self.warnings)
        return {
            'schema_version': '1.0',
            'target': str(self.target),
            'phase': self.phase,
            'profile': self.profile,
            'generated_at': utc_now(),
            'passed': passed,
            'strict': strict,
            'metrics': self.metrics,
            'checks': self.checks,
            'errors': self.errors,
            'warnings': self.warnings,
        }


def non_placeholder(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding='utf-8').strip()
    if len(text) < 500:
        return False
    meaningful = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
    placeholder_lines = [line for line in meaningful if re.search(r'\bPending\b|待补充|待研究|placeholder', line, re.I)]
    return len(meaningful) >= 5 and len(placeholder_lines) < max(2, len(meaningful) // 2)


def evaluate_sources(report: Report, target: Path, thresholds: dict[str, Any], allow_provisional: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sources = read_jsonl(target / 'evidence/source-ledger.jsonl')
    train = [record for record in sources if record.get('split') == 'train']
    holdout = [record for record in sources if record.get('split') == 'holdout']
    usable = [record for record in train if record.get('tier') != 'U' and record.get('extraction_status') != 'failed']
    primary = [record for record in usable if record.get('tier') in {'P1', 'P2'}]
    primary_ratio = len(primary) / len(usable) if usable else 0.0
    lane_sources = {lane: 0 for lane in LANES}
    for record in usable:
        for lane in set(record.get('dimensions', [])):
            if lane in lane_sources:
                lane_sources[lane] += 1
    covered = [lane for lane, count in lane_sources.items() if count > 0]
    report.metrics.update({
        'sources_total': len(sources),
        'sources_train': len(train),
        'sources_usable_train': len(usable),
        'sources_holdout': len(holdout),
        'primary_sources': len(primary),
        'primary_ratio': round(primary_ratio, 4),
        'lane_source_counts': lane_sources,
    })
    report.threshold(
        len(usable) >= thresholds['min_sources'],
        'source.minimum',
        f'usable train sources {len(usable)} < profile minimum {thresholds["min_sources"]}',
        allow_provisional,
    )
    report.threshold(
        primary_ratio >= thresholds['min_primary_ratio'],
        'source.primary-ratio',
        f'primary ratio {primary_ratio:.1%} < profile minimum {thresholds["min_primary_ratio"]:.0%}',
        allow_provisional,
    )
    report.threshold(
        len(covered) >= thresholds['min_lanes'],
        'source.lane-coverage',
        f'source metadata covers {len(covered)} lanes < profile minimum {thresholds["min_lanes"]}: {covered}',
        allow_provisional,
    )
    if report.phase in {'synthesis', 'release'} and not holdout:
        report.error('source.no-holdout', 'no Holdout source exists; evaluation would be circular or ungrounded')
    for record in usable:
        if record.get('checksum_basis') == 'url-locator-only':
            report.warn('source.locator-checksum', f'{record.get("source_id")} has no content checksum')
        if not record.get('rights') or 'unknown' in str(record.get('rights')).lower():
            report.warn('source.rights-unknown', f'{record.get("source_id")} has unresolved rights')
    return sources, holdout


def evaluate_research(report: Report, target: Path, thresholds: dict[str, Any], train_source_ids: set[str], allow_provisional: bool) -> None:
    complete: list[str] = []
    source_pattern = re.compile(r'src-[a-f0-9]{12}')
    for lane, rel in LANE_FILES.items():
        path = target / rel
        if not path.exists():
            report.error('research.missing-file', f'missing lane file: {rel}')
            continue
        text = path.read_text(encoding='utf-8')
        cited = set(source_pattern.findall(text))
        unknown = cited - train_source_ids
        if unknown:
            report.error('research.invalid-source', f'{rel} cites non-train or unknown sources: {sorted(unknown)}')
        if non_placeholder(path) and cited:
            complete.append(lane)
        elif non_placeholder(path) and not cited:
            report.error('research.no-source-ids', f'{rel} has substantive text but no source IDs')
    report.metrics['research_lanes_complete'] = complete
    report.threshold(
        len(complete) >= thresholds['min_lanes'],
        'research.lane-completion',
        f'completed source-linked lanes {len(complete)} < profile minimum {thresholds["min_lanes"]}: {complete}',
        allow_provisional,
    )


def evaluate_claims(report: Report, target: Path, thresholds: dict[str, Any], sources: list[dict[str, Any]], allow_provisional: bool) -> list[dict[str, Any]]:
    claims = read_jsonl(target / 'evidence/claims.jsonl')
    active = [claim for claim in claims if claim.get('status') not in {'superseded', 'unknown'}]
    models = [claim for claim in active if claim.get('category') in MODEL_CATEGORIES and claim.get('status') == 'pattern']
    heuristics = [claim for claim in active if claim.get('category') in HEURISTIC_CATEGORIES and claim.get('status') == 'pattern']
    report.metrics.update({
        'claims_total': len(claims),
        'claims_active': len(active),
        'mental_models': len(models),
        'heuristics': len(heuristics),
    })
    report.threshold(len(models) >= thresholds['min_models'], 'claim.model-minimum', f'mental models {len(models)} < {thresholds["min_models"]}', allow_provisional)
    report.threshold(len(heuristics) >= thresholds['min_heuristics'], 'claim.heuristic-minimum', f'heuristics {len(heuristics)} < {thresholds["min_heuristics"]}', allow_provisional)

    source_map = {record.get('source_id'): record for record in sources}
    for claim in active:
        claim_id = claim.get('claim_id', '<unknown>')
        if claim.get('category') in {'mental-model', 'heuristic', 'value', 'work-method', 'blind-spot', 'contradiction'}:
            if len(set(claim.get('source_ids', []))) < 2:
                report.error('claim.insufficient-support', f'{claim_id} needs at least two supporting sources')
            if len(set(claim.get('contexts', []))) < 2:
                report.error('claim.insufficient-contexts', f'{claim_id} needs at least two materially different contexts')
            clusters = set(claim.get('evidence_clusters', []))
            if len(clusters) < 2:
                report.error('claim.non-independent', f'{claim_id} needs at least two independent evidence clusters')
            if not claim.get('falsifiers'):
                report.error('claim.no-falsifier', f'{claim_id} lacks falsification/downgrade conditions')
            if not claim.get('time_scope'):
                report.warn('claim.no-time-scope', f'{claim_id} lacks time scope')
        for source_id in claim.get('source_ids', []):
            if source_map.get(source_id, {}).get('split') == 'holdout':
                report.error('claim.holdout-leakage', f'{claim_id} uses Holdout source {source_id}')
        if claim.get('category') == 'soul-hypothesis':
            if not claim.get('alternative_explanations'):
                report.error('claim.hypothesis-no-alternative', f'{claim_id} lacks alternatives')
            if not claim.get('falsifiers'):
                report.error('claim.hypothesis-no-falsifier', f'{claim_id} lacks falsifiers')
            if float(claim.get('confidence', 0)) > 0.8:
                report.warn('claim.hypothesis-overconfidence', f'{claim_id} existential hypothesis confidence exceeds 0.8')

    markers_by_file = {rel: markdown_claim_markers(target / rel) for rel in RENDER_FILES}
    all_markers = set().union(*markers_by_file.values()) if markers_by_file else set()
    active_ids = {claim.get('claim_id') for claim in active}
    unknown_markers = all_markers - {claim.get('claim_id') for claim in claims}
    for marker in sorted(unknown_markers):
        report.error('claim.unknown-marker', f'rendered artifact references unknown Claim {marker}')
    for claim in active:
        claim_id = claim.get('claim_id')
        if claim.get('category') in {'fact', 'mental-model', 'heuristic', 'value', 'epistemic', 'expression', 'blind-spot', 'work-method', 'boundary'} and claim_id not in all_markers:
            message = f'active Claim {claim_id} is not rendered in any core artifact'
            if report.phase == 'release':
                report.error('claim.orphan', message)
            else:
                report.warn('claim.orphan', message)
        if claim.get('category') == 'soul-hypothesis':
            for rel, markers in markers_by_file.items():
                if claim_id in markers and rel != 'hypotheses.md':
                    report.error('claim.hypothesis-escaped', f'{claim_id} appears outside hypotheses.md in {rel}')
    report.metrics['claim_markers'] = len(all_markers)
    return claims


def evaluate_cases(report: Report, target: Path, thresholds: dict[str, Any], holdout_ids: set[str], allow_provisional: bool) -> list[dict[str, Any]]:
    cases = read_jsonl(target / 'evals/cases.jsonl')
    ids: set[str] = set()
    suite_counts = Counter()
    for case in cases:
        case_id = case.get('case_id')
        suite = case.get('suite')
        if not case_id:
            report.error('eval.case-missing-id', 'evaluation case missing case_id')
            continue
        if case_id in ids:
            report.error('eval.duplicate-case', f'duplicate case_id: {case_id}')
        ids.add(case_id)
        if suite not in SUITES:
            report.error('eval.invalid-suite', f'{case_id} has invalid suite {suite!r}')
            continue
        suite_counts[suite] += 1
        if not case.get('prompt'):
            report.error('eval.empty-prompt', f'{case_id} has no prompt')
        if not case.get('rubric'):
            report.error('eval.no-rubric', f'{case_id} has no rubric')
        if suite == 'known':
            case_holdout = set(case.get('holdout_source_ids', []))
            if not case_holdout:
                report.error('eval.known-no-holdout', f'{case_id} known case has no Holdout source')
            bad = case_holdout - holdout_ids
            if bad:
                report.error('eval.known-invalid-holdout', f'{case_id} references non-Holdout IDs: {sorted(bad)}')
    report.metrics['eval_cases'] = len(cases)
    report.metrics['eval_suite_counts'] = dict(suite_counts)
    for suite in SUITES:
        required = thresholds['min_suite_cases']
        report.threshold(
            suite_counts[suite] >= required,
            'eval.suite-minimum',
            f'{suite} cases {suite_counts[suite]} < {required}',
            allow_provisional,
        )
    return cases


def evaluate_results(report: Report, target: Path, thresholds: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    results = read_jsonl(target / 'evals/results.jsonl')
    report.metrics['eval_results'] = len(results)
    if not results:
        report.error('eval.no-results', 'release phase requires evaluation results')
        return
    case_map = {case.get('case_id'): case for case in cases}
    valid_systems = {'baseline', 'candidate', 'foil', 'prior'}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    judges_by_case_system: dict[tuple[str, str], set[str]] = defaultdict(set)
    for result in results:
        case_id = result.get('case_id')
        system = result.get('system')
        if case_id not in case_map:
            report.error('eval.result-unknown-case', f'result references unknown case {case_id}')
            continue
        if system not in valid_systems:
            report.error('eval.result-invalid-system', f'{case_id} result has invalid system {system}')
            continue
        score = result.get('overall_score')
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            report.error('eval.result-score', f'{case_id}/{system} has invalid score')
            continue
        grouped[(case_id, system)].append(result)
        judges_by_case_system[(case_id, system)].add(str(result.get('judge_id')))
        if system == 'candidate' and result.get('critical_failure'):
            report.error('eval.critical-failure', f'{case_id} candidate critical failure: {result.get("critical_failure_type")}')

    required_judges = 1 if report.profile == 'quick' else 2
    candidate_scores: list[float] = []
    baseline_scores: list[float] = []
    suite_candidate: dict[str, list[float]] = defaultdict(list)
    per_case_delta: list[float] = []
    for case_id, case in case_map.items():
        for system in ('baseline', 'candidate'):
            rows = grouped.get((case_id, system), [])
            if not rows:
                report.error('eval.missing-system-result', f'{case_id} missing {system} result')
                continue
            if len(judges_by_case_system[(case_id, system)]) < required_judges:
                report.error('eval.judge-count', f'{case_id}/{system} has fewer than {required_judges} independent judges')
        candidate_rows = grouped.get((case_id, 'candidate'), [])
        baseline_rows = grouped.get((case_id, 'baseline'), [])
        if candidate_rows:
            candidate_mean = sum(float(row['overall_score']) for row in candidate_rows) / len(candidate_rows)
            candidate_scores.append(candidate_mean)
            suite_candidate[str(case.get('suite'))].append(candidate_mean)
        else:
            candidate_mean = None
        if baseline_rows:
            baseline_mean = sum(float(row['overall_score']) for row in baseline_rows) / len(baseline_rows)
            baseline_scores.append(baseline_mean)
        else:
            baseline_mean = None
        if candidate_mean is not None and baseline_mean is not None:
            per_case_delta.append(candidate_mean - baseline_mean)

    candidate_overall = sum(candidate_scores) / len(candidate_scores) if candidate_scores else 0.0
    baseline_overall = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0
    delta = candidate_overall - baseline_overall
    suite_means = {suite: sum(scores) / len(scores) for suite, scores in suite_candidate.items() if scores}
    report.metrics.update({
        'candidate_overall': round(candidate_overall, 4),
        'baseline_overall': round(baseline_overall, 4),
        'candidate_baseline_delta': round(delta, 4),
        'suite_candidate_means': {key: round(value, 4) for key, value in suite_means.items()},
    })
    if candidate_overall < thresholds['min_overall_score']:
        report.error('eval.overall-threshold', f'candidate overall {candidate_overall:.3f} < {thresholds["min_overall_score"]:.3f}')
    if delta < thresholds['min_baseline_delta']:
        report.error('eval.baseline-delta', f'candidate-baseline delta {delta:.3f} < {thresholds["min_baseline_delta"]:.3f}')
    if suite_means.get('boundary', 0.0) < thresholds['min_boundary_score']:
        report.error('eval.boundary-threshold', f'boundary score {suite_means.get("boundary", 0):.3f} < {thresholds["min_boundary_score"]:.3f}')
    if suite_means.get('fact-preservation', 0.0) < thresholds['min_fact_score']:
        report.error('eval.fact-threshold', f'fact-preservation score {suite_means.get("fact-preservation", 0):.3f} < {thresholds["min_fact_score"]:.3f}')



def evaluate_runtime_contract(report: Report, target: Path, meta: dict[str, Any]) -> None:
    try:
        route = json.loads((target / 'route-manifest.json').read_text(encoding='utf-8'))
        selection = route.get('identity_selection', {})
        weights = selection.get('weights', {})
        if selection.get('mode') not in {'single', 'multi'}:
            report.error('route.identity-mode', 'route identity mode must be single or multi')
        if not isinstance(weights, dict) or not weights:
            report.error('route.identity-weights', 'route identity weights are missing')
        else:
            total = sum(float(value) for value in weights.values())
            if abs(total - 1.0) > 1e-5:
                report.error('route.identity-sum', f'identity weights sum to {total}, not 1.0')
            if selection.get('mode') == 'multi' and len(weights) < 2:
                report.error('route.identity-multi-count', 'multi identity requires at least two weighted main identities')
        gate = route.get('runtime_identity_gate', {})
        if not gate.get('required_each_substantive_invocation'):
            report.error('route.identity-gate', 'runtime identity gate is not mandatory')
        versioning = route.get('runtime_versioning', {})
        if versioning.get('format') != '0.0.0.N' or not versioning.get('serial_reuse_forbidden'):
            report.error('route.versioning', 'runtime versioning contract is incomplete')
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report.error('route.invalid', str(exc))

    try:
        state = json.loads((target / 'runtime/state.json').read_text(encoding='utf-8'))
        if int(state.get('last_serial', -1)) < 0:
            report.error('runtime.counter', 'last_serial must be >= 0')
        if state.get('target_slug') != target.name:
            report.error('runtime.slug', 'runtime state target_slug must match directory')
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        report.error('runtime.state-invalid', str(exc))

    for rel in ('cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md', 'work.md', 'persona.md', 'boundaries.md', 'divergence-map.md'):
        path = target / rel
        if report.phase == 'release' and not non_placeholder(path):
            report.error('model.placeholder', f'{rel} is not substantive enough for release')

    # Every main identity facet must exist. Readiness may remain provisional, but the route must expose it honestly.
    try:
        catalog = json.loads((target / 'identity-catalog.json').read_text(encoding='utf-8'))
        main_ids = [item['id'] for item in catalog.get('families', []) if item.get('number') in range(1, 7)]
        if len(main_ids) != 6:
            report.error('identity.catalog', 'identity catalog must contain six main identities')
        for identity_id in main_ids:
            if not (target / 'identity-facets' / f'{identity_id}.md').is_file():
                report.error('identity.facet-missing', f'missing identity facet: {identity_id}')
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        report.error('identity.catalog-invalid', str(exc))

def markdown_report(data: dict[str, Any]) -> str:
    lines = [
        '# Persona Distiller quality report',
        '',
        f'- Target: `{data["target"]}`',
        f'- Phase: `{data["phase"]}`',
        f'- Profile: `{data["profile"]}`',
        f'- Generated: `{data["generated_at"]}`',
        f'- Result: **{"PASS" if data["passed"] else "FAIL"}**',
        '',
        '## Metrics',
        '',
        '```json',
        json.dumps(data['metrics'], ensure_ascii=False, indent=2),
        '```',
        '',
        '## Errors',
        '',
    ]
    lines.extend([f'- `{item["code"]}`: {item["message"]}' for item in data['errors']] or ['- None'])
    lines.extend(['', '## Warnings', ''])
    lines.extend([f'- `{item["code"]}`: {item["message"]}' for item in data['warnings']] or ['- None'])
    return '\n'.join(lines).rstrip() + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Evidence-aware quality gate for Persona Distiller targets.')
    parser.add_argument('target', type=Path)
    parser.add_argument('--phase', choices=['research', 'synthesis', 'release'], default='release')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as failures.')
    parser.add_argument('--allow-provisional', action='store_true', help='Downgrade quantitative minimum misses to warnings; never hides leakage or structural errors.')
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    try:
        meta = ensure_target(target)
    except (ValueError, OSError) as exc:
        print(json.dumps({'passed': False, 'errors': [{'code': 'target.invalid', 'message': str(exc)}]}, ensure_ascii=False, indent=2))
        return 1
    profile = meta.get('profile', 'standard')
    thresholds = PROFILE_THRESHOLDS.get(profile)
    if thresholds is None:
        print(f'ERROR: invalid profile {profile!r}', file=sys.stderr)
        return 2
    report = Report(target, args.phase, profile)

    for rel in REQUIRED_FILES:
        if not (target / rel).exists():
            report.error('structure.missing', f'missing required file: {rel}')
    if str(meta.get('status', '')).startswith('blocked'):
        report.error('governance.blocked', 'target is blocked by missing consent/authority or another governance condition')
    if meta.get('subject_origin') in {'private', 'self'}:
        if not meta.get('consent_authority'):
            report.error('governance.no-consent', 'private target lacks consent/authority record')
        if args.phase == 'release' and not meta.get('retention_policy'):
            report.error('governance.no-retention', 'private target release lacks retention policy')

    try:
        fm, _ = parse_frontmatter(target / 'SKILL.md')
        if fm.get('name') != target.name:
            report.error('skill.name-mismatch', f'SKILL.md name {fm.get("name")!r} != directory {target.name!r}')
        if set(fm) != {'name', 'description'}:
            report.error('skill.frontmatter-extra', f'SKILL.md frontmatter must contain only name and description; found {sorted(fm)}')
        line_count = len((target / 'SKILL.md').read_text(encoding='utf-8').splitlines())
        report.metrics['skill_lines'] = line_count
        if line_count > 500:
            report.warn('skill.progressive-disclosure', f'target SKILL.md has {line_count} lines; keep under 500')
    except (ValueError, OSError) as exc:
        report.error('skill.frontmatter', str(exc))

    evaluate_runtime_contract(report, target, meta)

    ledger_errors, ledger_warnings, counts = validate_ledgers(target)
    for message in ledger_errors:
        report.error('ledger.invalid', message)
    for message in ledger_warnings:
        report.warn('ledger.warning', message)
    report.metrics['ledger_counts'] = counts

    try:
        sources, holdout = evaluate_sources(report, target, thresholds, args.allow_provisional)
        train_ids = {record.get('source_id') for record in sources if record.get('split') == 'train'}
        evaluate_research(report, target, thresholds, train_ids, args.allow_provisional)
        cases: list[dict[str, Any]] = []
        if args.phase in {'synthesis', 'release'}:
            evaluate_claims(report, target, thresholds, sources, args.allow_provisional)
            cases = evaluate_cases(report, target, thresholds, {record.get('source_id') for record in holdout}, args.allow_provisional)
        if args.phase == 'release':
            evaluate_results(report, target, thresholds, cases)
            findings = scan_secrets(target)
            report.metrics['secret_findings'] = len(findings)
            for finding in findings:
                report.error('security.secret-pattern', f'{finding["file"]}:{finding["line"]} matched {finding["type"]}')
    except ValueError as exc:
        report.error('data.parse', str(exc))

    data = report.as_dict(strict=args.strict)
    if args.write_report:
        reports = target / 'reports'
        reports.mkdir(parents=True, exist_ok=True)
        stamp = data['generated_at'].replace(':', '').replace('-', '')
        atomic_write_json(reports / f'quality-{args.phase}-{stamp}.json', data, mode=0o600)
        atomic_write_text(reports / f'quality-{args.phase}-{stamp}.md', markdown_report(data), mode=0o600)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
