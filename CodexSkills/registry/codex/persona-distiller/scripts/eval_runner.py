#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PROFILE_THRESHOLDS, append_jsonl, atomic_write_json, atomic_write_text, ensure_target, make_id, read_json, read_jsonl, utc_now

SYSTEMS = ('baseline', 'candidate', 'foil', 'prior')


def validate_cases(target: Path) -> tuple[list[dict[str, Any]], list[str]]:
    cases = read_jsonl(target / 'evals' / 'cases.jsonl')
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        case_id = case.get('case_id')
        if not case_id:
            errors.append('case missing case_id')
            continue
        if case_id in seen:
            errors.append(f'duplicate case_id: {case_id}')
        seen.add(case_id)
        if not case.get('suite'):
            errors.append(f'{case_id} missing suite')
        if not case.get('prompt'):
            errors.append(f'{case_id} missing prompt')
        if not isinstance(case.get('rubric'), dict) or not case.get('rubric'):
            errors.append(f'{case_id} missing rubric object')
    return cases, errors


def prepare_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    cases, errors = validate_cases(target)
    if errors:
        raise ValueError('; '.join(errors))
    systems = list(dict.fromkeys(args.system))
    if 'baseline' not in systems or 'candidate' not in systems:
        raise ValueError('prepare requires baseline and candidate systems')
    rng = random.Random(args.seed)
    run_id = f'run-{utc_now().replace(":", "").replace("-", "")}-{make_id("x").split("-")[1][:6]}'
    private_cases = []
    judge_cases = []
    output_root = target / 'evals' / 'outputs' / run_id
    for case in cases:
        shuffled = systems[:]
        rng.shuffle(shuffled)
        labels = [chr(ord('A') + i) for i in range(len(shuffled))]
        mapping = dict(zip(labels, shuffled))
        private_cases.append({'case_id': case['case_id'], 'suite': case['suite'], 'mapping': mapping})
        judge_cases.append({
            'case_id': case['case_id'],
            'suite': case['suite'],
            'prompt': case['prompt'],
            'turns': case.get('turns', []),
            'rubric': case['rubric'],
            'critical': bool(case.get('critical')),
            'labels': labels,
        })
        for label in labels:
            path = output_root / case['case_id'] / f'{label}.md'
            path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(path, f'# Output {label}\n\nPending generation. Do not reveal system identity to judges.\n', mode=0o600)
    private_plan = {
        'schema_version': '1.0',
        'run_id': run_id,
        'created_at': utc_now(),
        'seed': args.seed,
        'systems': systems,
        'cases': private_cases,
        'warning': 'Private mapping. Do not provide this file to blind judges.',
    }
    judge_packet = {
        'schema_version': '1.0',
        'run_id': run_id,
        'created_at': utc_now(),
        'cases': judge_cases,
        'instructions': 'Judge labels blindly. Return one record per label/case. Do not infer system identity.',
    }
    atomic_write_json(target / 'evals' / 'run-plan.json', private_plan, mode=0o600)
    atomic_write_json(target / 'evals' / 'judge-packet.json', judge_packet, mode=0o600)
    print(json.dumps({'run_id': run_id, 'cases': len(cases), 'systems': systems, 'output_root': str(output_root)}, ensure_ascii=False, indent=2))
    return 0


def parse_dimensions(items: list[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    for item in items:
        key, sep, raw = item.partition('=')
        if not sep:
            raise ValueError(f'dimension must be key=value: {item}')
        score = float(raw)
        if not 0 <= score <= 1:
            raise ValueError(f'dimension score must be 0..1: {item}')
        values[key.strip()] = score
    return values


def record_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    cases, errors = validate_cases(target)
    if errors:
        raise ValueError('; '.join(errors))
    case_map = {case['case_id']: case for case in cases}
    if args.case_id not in case_map:
        raise ValueError(f'unknown case_id: {args.case_id}')
    if not 0 <= args.score <= 1:
        raise ValueError('score must be 0..1')
    record = {
        'run_id': args.run_id,
        'case_id': args.case_id,
        'suite': case_map[args.case_id]['suite'],
        'system': args.system,
        'blind_label': args.blind_label,
        'judge_id': args.judge_id,
        'overall_score': args.score,
        'dimension_scores': parse_dimensions(args.dimension),
        'critical_failure': args.critical_failure,
        'critical_failure_type': args.critical_failure_type,
        'rationale': args.rationale,
        'timestamp': utc_now(),
    }
    append_jsonl(target / 'evals' / 'results.jsonl', record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def aggregate_data(target: Path, run_id: str | None = None) -> dict[str, Any]:
    meta = ensure_target(target)
    cases, case_errors = validate_cases(target)
    results = read_jsonl(target / 'evals' / 'results.jsonl')
    if run_id:
        results = [row for row in results if row.get('run_id') == run_id]
    case_map = {case.get('case_id'): case for case in cases}
    errors = list(case_errors)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    critical: list[dict[str, Any]] = []
    for row in results:
        case_id = row.get('case_id')
        system = row.get('system')
        if case_id not in case_map:
            errors.append(f'unknown result case: {case_id}')
            continue
        if system not in SYSTEMS:
            errors.append(f'invalid result system: {system}')
            continue
        score = row.get('overall_score')
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            errors.append(f'invalid score for {case_id}/{system}')
            continue
        grouped[(case_id, system)].append(row)
        if row.get('critical_failure'):
            critical.append(row)

    per_case: list[dict[str, Any]] = []
    system_scores: dict[str, list[float]] = defaultdict(list)
    suite_system_scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    judge_counts: dict[str, int] = {}
    for case_id, case in case_map.items():
        item: dict[str, Any] = {'case_id': case_id, 'suite': case.get('suite'), 'systems': {}}
        for system in SYSTEMS:
            rows = grouped.get((case_id, system), [])
            if not rows:
                continue
            scores = [float(row['overall_score']) for row in rows]
            mean = statistics.fmean(scores)
            median = statistics.median(scores)
            judges = sorted({str(row.get('judge_id')) for row in rows})
            item['systems'][system] = {'mean': round(mean, 4), 'median': round(median, 4), 'judges': judges, 'n': len(rows)}
            system_scores[system].append(mean)
            suite_system_scores[(str(case.get('suite')), system)].append(mean)
            judge_counts[f'{case_id}/{system}'] = len(judges)
        candidate = item['systems'].get('candidate', {}).get('mean')
        baseline = item['systems'].get('baseline', {}).get('mean')
        if candidate is not None and baseline is not None:
            item['candidate_baseline_delta'] = round(candidate - baseline, 4)
        per_case.append(item)

    overall = {system: round(statistics.fmean(scores), 4) for system, scores in system_scores.items() if scores}
    suite_means: dict[str, dict[str, float]] = defaultdict(dict)
    for (suite, system), scores in suite_system_scores.items():
        suite_means[suite][system] = round(statistics.fmean(scores), 4)
    candidate = overall.get('candidate', 0.0)
    baseline = overall.get('baseline', 0.0)
    thresholds = PROFILE_THRESHOLDS.get(meta.get('profile', 'standard'), PROFILE_THRESHOLDS['standard'])
    gates = {
        'candidate_overall': candidate >= thresholds['min_overall_score'],
        'baseline_delta': candidate - baseline >= thresholds['min_baseline_delta'],
        'boundary': suite_means.get('boundary', {}).get('candidate', 0.0) >= thresholds['min_boundary_score'],
        'fact_preservation': suite_means.get('fact-preservation', {}).get('candidate', 0.0) >= thresholds['min_fact_score'],
        'no_candidate_critical_failure': not any(row.get('system') == 'candidate' for row in critical),
        'has_results': bool(results),
    }
    return {
        'schema_version': '1.0',
        'target': str(target),
        'run_id': run_id,
        'generated_at': utc_now(),
        'profile': meta.get('profile'),
        'result_count': len(results),
        'errors': errors,
        'critical_failures': critical,
        'overall': overall,
        'candidate_baseline_delta': round(candidate - baseline, 4),
        'suite_means': dict(suite_means),
        'judge_counts': judge_counts,
        'per_case': per_case,
        'gates': gates,
        'passed': not errors and all(gates.values()),
    }


def aggregate_markdown(data: dict[str, Any]) -> str:
    lines = [
        '# Evaluation aggregate', '',
        f'- Run: `{data.get("run_id") or "all"}`',
        f'- Profile: `{data.get("profile")}`',
        f'- Result: **{"PASS" if data.get("passed") else "FAIL"}**',
        f'- Candidate overall: `{data.get("overall", {}).get("candidate", 0):.4f}`',
        f'- Baseline overall: `{data.get("overall", {}).get("baseline", 0):.4f}`',
        f'- Delta: `{data.get("candidate_baseline_delta", 0):.4f}`', '',
        '## Gates', '',
    ]
    lines.extend(f'- {"PASS" if passed else "FAIL"}: `{name}`' for name, passed in data.get('gates', {}).items())
    lines.extend(['', '## Suite means', '', '```json', json.dumps(data.get('suite_means', {}), ensure_ascii=False, indent=2), '```', '', '## Critical failures', ''])
    if data.get('critical_failures'):
        for row in data['critical_failures']:
            lines.append(f'- `{row.get("case_id")}/{row.get("system")}`: {row.get("critical_failure_type") or "unspecified"}')
    else:
        lines.append('- None')
    lines.extend(['', '## Errors', ''])
    lines.extend(f'- {error}' for error in data.get('errors', []))
    if not data.get('errors'):
        lines.append('- None')
    return '\n'.join(lines).rstrip() + '\n'


def aggregate_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    data = aggregate_data(target, args.run_id)
    if args.write_report:
        reports = target / 'reports'
        reports.mkdir(parents=True, exist_ok=True)
        suffix = args.run_id or 'all'
        atomic_write_json(reports / f'eval-{suffix}.json', data, mode=0o600)
        atomic_write_text(reports / f'eval-{suffix}.md', aggregate_markdown(data), mode=0o600)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if data['passed'] else 1


def validate_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    cases, errors = validate_cases(target)
    results = read_jsonl(target / 'evals' / 'results.jsonl')
    case_ids = {case.get('case_id') for case in cases}
    for index, row in enumerate(results, 1):
        if row.get('case_id') not in case_ids:
            errors.append(f'result {index} references unknown case {row.get("case_id")}')
        if row.get('system') not in SYSTEMS:
            errors.append(f'result {index} has invalid system {row.get("system")}')
        score = row.get('overall_score')
        if not isinstance(score, (int, float)) or not 0 <= score <= 1:
            errors.append(f'result {index} has invalid score')
    data = {'passed': not errors, 'cases': len(cases), 'results': len(results), 'errors': errors}
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(description='Prepare blind plans, append judge results, and aggregate evaluations.')
    sub = parser.add_subparsers(dest='command', required=True)

    prepare = sub.add_parser('prepare')
    prepare.add_argument('target', type=Path)
    prepare.add_argument('--seed', type=int, default=42)
    prepare.add_argument('--system', action='append', choices=SYSTEMS, default=['baseline', 'candidate'])
    prepare.set_defaults(func=prepare_command)

    record = sub.add_parser('record')
    record.add_argument('target', type=Path)
    record.add_argument('--run-id', required=True)
    record.add_argument('--case-id', required=True)
    record.add_argument('--system', choices=SYSTEMS, required=True)
    record.add_argument('--blind-label')
    record.add_argument('--judge-id', required=True)
    record.add_argument('--score', type=float, required=True)
    record.add_argument('--dimension', action='append', default=[])
    record.add_argument('--critical-failure', action='store_true')
    record.add_argument('--critical-failure-type')
    record.add_argument('--rationale')
    record.set_defaults(func=record_command)

    aggregate = sub.add_parser('aggregate')
    aggregate.add_argument('target', type=Path)
    aggregate.add_argument('--run-id')
    aggregate.add_argument('--write-report', action='store_true')
    aggregate.set_defaults(func=aggregate_command)

    validate = sub.add_parser('validate')
    validate.add_argument('target', type=Path)
    validate.set_defaults(func=validate_command)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
