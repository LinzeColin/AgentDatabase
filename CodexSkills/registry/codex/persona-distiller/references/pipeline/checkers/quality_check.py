#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import re
import subprocess
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
    'agents/openai.yaml', 'scripts/runtime_recorder.py', 'scripts/runtime_router.py',
    'runtime/invocations.jsonl', 'evidence/source-ledger.jsonl',
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
        routing = route.get('runtime_identity_routing', {})
        if routing.get('mode') != 'automatic' or routing.get('user_selection_required') is not False:
            report.error('route.identity-routing', 'runtime identity routing must be automatic and require no user selection')
        runtime_versioning = route.get('runtime_invocation_versioning', {})
        if (
            runtime_versioning.get('enabled') is not False
            or runtime_versioning.get('user_visible_version') is not False
            or runtime_versioning.get('versioned_output_names') is not False
        ):
            report.error('route.runtime-versioning', 'per-invocation versioning must be disabled')
        product_versioning = route.get('product_release_versioning', {})
        if (
            product_versioning.get('format') != '0.0.0.N'
            or product_versioning.get('scope') != 'per-canonical-person'
            or product_versioning.get('consumed_on') != 'successful-registration'
        ):
            report.error('route.product-versioning', 'product release versioning contract is incomplete')
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report.error('route.invalid', str(exc))

    if meta.get('runtime_invocation_versioning') is not False:
        report.error('runtime.versioning-enabled', 'target metadata must disable per-invocation versioning')
    if meta.get('product_version') is not None:
        report.warn('product.version-preassigned', 'workspace product_version is normally assigned only while packaging')

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



def report_semantic_residue(report, target: Path) -> None:
    """**被订正掉的说法，换个措辞又活了**（只报不拦）。

    ## 为什么它此前没有调用方——**不是忘了接，是接不上**

    `check_semantic_residue` 要一份 `--rules`（name→正则）。
    全库回查（2026-08-06）：**没有任何人物产出过 rules 文件**，
    而 `corrections.jsonl` 里唯一有内容的是 Bessemer #132 的 2 条，
    **两条的 `scope` 都是 `evaluation`**（判分方法的错），
    不是「产物里某个说法被订正掉了」。

    **→ 它找的那种输入，全库从来没有出现过。**
    「无调用方」这个报警是对的，但根因是**上游没有产出**，不是接线漏了。

    ## 本件的接法：从 `corrections.jsonl` 里 `scope == "content"` 的条目现取规则

    这样它在**第一条内容域订正出现的那一刻**自动生效，不用再记得去接。
    没有这类订正时报「未启用」——**不是「通过」**。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_semantic_residue.py'
    if not script.exists():
        report.metrics['semantic_residue'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    cor = None
    for cand in (target / 'corrections' / 'corrections.jsonl',
                 target.parent / 'corrections' / 'corrections.jsonl'):
        if cand.is_file():
            cor = cand
            break
    if cor is None:
        report.metrics['semantic_residue'] = {
            '状态': '未启用（本人物没有 corrections.jsonl）——**不是通过**'}
        return
    rules, skipped = {}, 0
    for line in cor.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(rec.get('scope') or '') != 'content':
            skipped += 1
            continue
        # 订正文本里被引号括起来的旧说法 → 规则
        for old in re.findall(r'[「"“]([^「」"“”]{4,40})[」"”]',
                              str(rec.get('text') or '')):
            rules[f"{rec.get('correction_id', '?')}::{old[:20]}"] = re.escape(old)
    if not rules:
        report.metrics['semantic_residue'] = {
            '状态': f'未启用（{skipped} 条订正全是非 content 域，取不到规则）——**不是通过**',
            '★': ('全库回查：唯一有内容的订正是 Bessemer #132 的 2 条，'
                  'scope 都是 `evaluation`。**这判据找的输入从来没出现过。**')}
        return
    try:
        spec = importlib.util.spec_from_file_location('_pd_semres', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        files = sorted(set(list(target.rglob('*.md')) + list(target.rglob('*.jsonl'))))
        hits = {}
        for name, pat in rules.items():
            rx = re.compile(pat)
            for f in files:
                if 'corrections' in f.parts:      # ★ 订正记录本身当然含旧说法
                    continue
                for m in rx.finditer(mod.scannable(f)):
                    hits.setdefault(name, []).append(f'{f.name}@{m.start()}')
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['semantic_residue'] = {'状态': f'跑不起来，**未核验**：{exc}'}
        return
    report.metrics['semantic_residue'] = {
        '规则条数': len(rules), '非 content 域跳过': skipped,
        '**残留命中**': {k: v[:4] for k, v in hits.items()},
    }
    if hits:
        report.warnings.append(
            f'content.semantic-residue：{len(hits)} 条被订正过的说法仍在产物里')


def report_verbatim_quotes(report, target: Path, cache) -> None:
    """**渲染文档／身份分面／评测用例里的引文一样会伪造**（只报不拦）。

    `check_quote_integrity` 只扫 `evidence/claims.jsonl`；本件补的是文档层与用例层。
    ★ 它此前**在生产代码里没有任何调用方**——`check_checkers` 的接线审计报出来的。
      「每个人物都在临时写脚本」（Robertson #97 那版还把维度选错了两次），
      **而常规检查一直没接上。**

    ★★ 它有两道语料：原样，与**去掉版口（页眉／页码）之后**的。
      第二道只在第一道未命中时重试，**且必须报出来是靠它才命中的**——
      「引文为真、只是横跨了版口」与「引文是编的」是两回事。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_verbatim_quotes.py'
    if not script.exists():
        report.metrics['verbatim_quotes'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    # ★ `--cache` 是 `nargs="+"`，**传进来是列表**——第一版按单个路径写，
    #   当场 `TypeError: expected str… not list`。接线必须实跑，不能只看语法过。
    dirs = [Path(c) for c in (cache if isinstance(cache, (list, tuple)) else [cache])
            if c is not None and Path(c).is_dir()]
    if not dirs:
        report.metrics['verbatim_quotes'] = {
            '状态': '**未核验**（不是通过）——没有可用的 --cache，取不到语料原文'}
        return
    try:
        spec = importlib.util.spec_from_file_location('_pd_vq', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        raw = [p.read_text(encoding='utf-8', errors='replace')
               for d in dirs for p in d.rglob('*.txt')]
        corpus = "\n".join(mod.norm(t) for t in raw)
        corpus2 = "\n".join(mod.norm(mod.strip_page_furniture(t)[0]) for t in raw)
        qs = mod.collect(target, [])
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['verbatim_quotes'] = {'状态': f'跑不起来，**未核验**：{exc}'}
        return
    bad, crossed = [], []
    for where, q in qs:
        if mod._hit(q, corpus):
            continue
        (crossed if mod._hit(q, corpus2) else bad).append((where, q))
    report.metrics['verbatim_quotes'] = {
        '逐字英文引文': len(qs),
        '**未命中**': len(bad),
        '跨版口命中（引文为真）': len(crossed),
        '未命中样例': [f'{w}: {q[:110]}' for w, q in bad[:6]],
        '跨版口样例': [f'{w}: {q[:80]}' for w, q in crossed[:4]],
    }
    if bad:
        report.warnings.append(
            f'content.verbatim-quote：{len(bad)} 条逐字引文在语料里找不到原样'
            '——**引文对不上就是引文对不上**')


def report_catalogue_entries(report, target: Path,
                            sources: list[dict[str, Any]]) -> None:
    """**这份 P1 是「著录方描述这份文献」，不是文献本身**（只报不拦）。

    三例确凿跨三个人物（见 `check_source_is_catalogue_entry.py` 文件头）：
    Roberts-Austen 的 `letter00robe.txt`（他的话占 13%）、
    Koch 的 `letter00koch.txt`（著录说 240 词而文件里几乎没有信文）、
    Osler 的 `walt-whitman-1919.txt`（**描述一场从没发生过的演讲**）。

    ★ 归属门问「文中有没有他的署名」——著录卡里**有**
      （`A.L.S: (W. C, ROBERTS-AUSTEN)`），于是它过了归属门，
      **而他 22 份真论文没过**。**没有一道门问「这份文件里有多少是他的话」。**

    ★★ **只报不拦**：改分档是人的判断（判据文件头写着）。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_source_is_catalogue_entry.py'
    if not script.exists():
        report.metrics['catalogue_entries'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    try:
        spec = importlib.util.spec_from_file_location('_pd_catent', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['catalogue_entries'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return

    def _read(record):
        rel = record.get('normalized_path') or record.get('local_path') or ''
        p = target / str(rel)
        if not p.is_file():
            return None
        try:
            return p.read_text(encoding='utf-8', errors='replace')
        except OSError:
            return None

    rep = mod.check(sources, _read)
    report.metrics['catalogue_entries'] = rep
    hits = rep.get('**疑似著录卡**') or {}
    if hits:
        report.warnings.append(
            f'research.catalogue-entry：{len(hits)} 份 P1 像是「著录方描述这份文献」'
            '而不是文献本身——**改分档是人的判断，本项只报不拦**')


def report_stance_density(report, target: Path,
                          sources: list[dict[str, Any]]) -> None:
    """**声口的第二维：立场句密度**（只写 metrics，**不拦、不设阈值**）。

    `report_own_voice` 答的是「他说了多少话」，用的是第一人称。
    Mehl #137 实测撞出：**人可以在完全非人称的语域里有极强的声口**——
    1936 年具名讲演开篇第一人称 0，而通篇是判断
    （`the critic must remember` / `has been irregular, and little given to`）。

    ★ 六个样本实测（详见 ㉙）：**两维并用能把三类人分开**——
      两维都低（Coffin 0.95/0.00、Bain 0.91/0.23）／两维中等（Mehl 讲演 1.57/0.43）／
      单维极高（Nasmyth 自传 29.67/0.07，叙事体）。

    ★★★ **但差距只有 2 倍量级、绝对数是个位数句子。**
      本件因此**只排序、只提示，不设阈值、不参与任何处置**——㉙ 的裁定要人做。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_stance_density.py'
    if not script.exists():
        report.metrics['stance_density'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    try:
        spec = importlib.util.spec_from_file_location('_pd_stance', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['stance_density'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    tot = fp = st = st_nofp = 0
    unread = []
    unmeasured = []                 # ★ 判据自己说「未核验」的，**单列，不并进分母**
    for record in sources:
        if not str(record.get('tier') or '').startswith('P1'):
            continue
        rel = record.get('normalized_path') or record.get('local_path') or ''
        p = target / str(rel)
        if not p.is_file():
            unread.append(record.get('source_id'))
            continue
        r = mod.measure(p.read_text(encoding='utf-8', errors='replace'))
        # ★★★★ 2026-08-10：`check_stance_density.measure` 在**判不出语种**时
        #   把三个计数字段返回 `None`（连同一句 `★ 未核验：语种判为 ?
        #   ——本件只认英语，不是「这个人没有声口」`）。那是它有意的「我不知道」。
        #   而这里原先写的是 `fp += r['第一人称命中']` ——
        #   **`int + None` 直接 TypeError，整个质检门崩掉**（全库 6 个测试因此长红）。
        #
        #   ★ 修法**不许写 `or 0`**：那会把「判不出语种」静默算成
        #     「这份材料里第一人称是 0」，即把「不知道」记成一个具体的好数——
        #     而这一维正是 ㉙ 用来分辨「有没有声口」的。[[empty-default-swallows-unknown]]
        #   **跳过，并单列出来。**
        if r.get('第一人称命中') is None:
            unmeasured.append({'source_id': record.get('source_id'),
                               '原因': r.get('★ 未核验') or '判据未给计数'})
            continue
        tot += r['字符']
        fp += r['第一人称命中']
        st += r['**立场句**']
        st_nofp += r['★ 其中不含第一人称的']
    report.metrics['stance_density'] = {
        'P1 字符合计': tot,
        '**判据说未核验的**': len(unmeasured),
        '★ 未核验的逐条（不并进分母，也不算 0）': unmeasured[:8],
        '第一人称（动词式）/万字': round(fp / tot * 10000, 2) if tot else None,
        '**立场句/万字**': round(st / tot * 10000, 2) if tot else None,
        '其中不含第一人称的': st_nofp,
        '读不到正文的': unread,          # ★ 读不到就说读不到
        '★ 口径': ('**只排序、只提示，不设阈值。** 第一人称已排除图纸标号／化学式／'
                   '罗马数字（三处真实假阳，见判据文件头），**但未排除专利套语**——'
                   'Coffin 实测 73% 是 `I claim as my invention` 这一类，'
                   '**专利型语料要另减一道**。'),
        '★★ 参照（㉙ 六样本）': ('Coffin 0.95/0.00、Bain 0.91/0.23、'
                                'Mehl 讲演 1.57/0.43、Nasmyth 自传 29.67/0.07'),
    }


def report_own_voice(report, target: Path, meta: dict[str, Any],
                     sources: list[dict[str, Any]]) -> None:
    """**语料里有多少字真是他自己写／说的**（v0.0.0.19 新增，只报不拦）。

    ## 为什么 `primary_ratio` 不够用

    RUNBOOK 第 822 行定：**第三人称叙述体（含"关于他"的报道）→ 降 P2**，
    而 `primary_ratio` 的分子是 `P1 ∪ P2`。于是——

    Livermore #100 实测：532 份可用 train 里 530 份是同期报纸对他的报道，
    `primary_ratio = 0.9887`，**deep 的 0.65 轻松通过**。
    而他本人的话总共只有约 **22,500 词**，其中 **97% 压在一本书上**；
    去掉那本书，一生可公开抓取的原话**只剩约 600 词**（散在 33 年 14 份报纸里）。
    对照：Lefèvre 那本小说 112,180 词，是他全部存世文字的 **5 倍**。

    **`primary_ratio = 0.99` 与「他的话只有 2 万字」同时为真**，
    因为那两个数量的是两件事：前者量「材料是不是同时代一手文献」，
    后者量「材料里有多少是他本人的表达」。
    **人物蒸馏要建的是后者的模型。**

    ## 判据

    `own_voice_ratio = 账本 author 命中人物姓氏的 train 源字节 ÷ 全部 train 源字节`

    **它不是代理量**：改 tier、改 dimension、再多抓一万份报道，这个数都不动；
    唯一能抬高它的是**真的拿到更多他本人的文字**。

    ## 为什么只报不拦

    对历史人物设阈值会直接判死一整类人物——他只出过一本书、没写过专栏、
    无公开书信集，**瓶颈是史料本身不存在，不是抓取力度**。
    按既定裁定「门达不到时选诚实退路继续，绝不为凑数放宽判据」，
    正确动作是**把这个数报出来并写进硬边界**，不是拦住流程，也不是假装没这回事。
    """
    # ★ v0.0.0.27：识别标记**向归属门要**，不再自己 `split()[-1]`。
    #   `name.split()[-1]` 对 `Galen of Pergamon` 取出的是 `Pergamon`（一个地名），
    #   于是 244 万词的亲笔语料被静默算成 `own_voice_ratio = 0.0`。
    #   v0.0.0.26 修了 `check_authorship.build_patterns`，**却漏了这里的第二份实现**——
    #   同一个西方姓名假设写在两个地方，只改一个等于没改。
    #   **「什么算他的名字」只许有一个真源。**
    name = str(meta.get('name') or '').strip()
    surname = ''
    if name:
        here = Path(__file__).resolve().parent
        script = here / 'check_authorship.py'
        if script.exists():
            spec = importlib.util.spec_from_file_location('_pd_auth_name', script)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                surname = mod.build_patterns(name)['surname']
            except Exception:                                   # noqa: BLE001
                surname = ''
    if not surname:
        report.metrics['own_voice'] = {'状态': 'meta 无 name 或识别标记取不到，**未核验**（不是通过）'}
        return
    rx = re.compile(re.escape(surname), re.I)

    # ★★★ v0.0.0.152：**只比姓氏，会把同姓近亲的材料算成「他自己的声口」。**
    #   Sorby #133 实测：`build_patterns` 取到的姓氏就是 `Sorby`，
    #   而他**父亲也叫 Henry Sorby**——父亲那本 1845–46 的日记同在 Sheffield 馆藏里，
    #   账本 author 写成 `Henry Sorby` 一样命中，**父亲的日记会被算进儿子的声口**。
    #   ★ 这是同一个同名问题打穿的**第二处**：第一处是 `check_authorship` 的署名护栏。
    #   而 own_voice_ratio 正是决定 profile（quick vs deep）时要看的那个数——
    #   **决定会建在一个被污染的比值上。**
    #
    #   修法：工作区里若有 `namesake-criteria.json`，就用它先把「他人」剔掉；
    #   **没有那份文件的人物一律走原路，一个数都不变**（向后兼容）。
    nsc = None
    crit_path = None
    for cand in (target / 'namesake-criteria.json',
                 target.parent.parent / 'namesake-criteria.json',
                 target.parent.parent.parent / 'namesake-criteria.json'):
        if cand.is_file():
            crit_path = cand
            break
    if crit_path is not None:
        try:
            spec_n = importlib.util.spec_from_file_location(
                '_pd_nsc_ov', Path(__file__).resolve().parent / 'check_namesake_criteria.py')
            nsc_mod = importlib.util.module_from_spec(spec_n)
            spec_n.loader.exec_module(nsc_mod)
            nsc = (nsc_mod, json.loads(crit_path.read_text(encoding='utf-8')))
        except Exception:                                       # noqa: BLE001
            nsc = None

    own_bytes = all_bytes = 0
    own_ids: list[str] = []
    excluded: list[str] = []
    unknown: list[str] = []
    for record in sources:
        rel = record.get('local_path')
        path = (target / rel) if rel else None
        if not path or not path.is_file():
            continue
        size = path.stat().st_size
        all_bytes += size
        if not rx.search(str(record.get('author') or '')):
            continue
        if nsc is not None:
            mod_n, crit = nsc
            blob = ' '.join(str(record.get(k, '')) for k in
                            ('author', 'byline', 'original_name', 'locator', 'title', 'notes'))
            ym = re.search(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', blob)
            verdict = mod_n.classify(blob, crit, int(ym.group(1)) if ym else None)
            if verdict['判定'] == '他人':
                excluded.append(f"{record.get('source_id')}：{verdict['理由'][:60]}")
                continue
            if verdict['判定'] == 'unknown':
                unknown.append(str(record.get('source_id')))
                continue                      # ★ 说不准的**不计入本人声口**——宁可低报
        own_bytes += size
        own_ids.append(str(record.get('source_id')))
    ratio = (own_bytes / all_bytes) if all_bytes else 0.0

    # ★★★ v0.0.0.153 起台账有 `voice` 字段——**它比按 author 猜准得多**。
    #   `author` 认的是「谁署名」；`voice` 认的是「这份材料里是不是他在说话」。
    #   两者会分岔的真实形态：某人物三道门全过、author 也都是他，
    #   而 17 万字里他本人实质的话只有 8 句（Coffin #130）。
    #   ★ `communicated`（作者自供而第三人称写的）**单独算，不并进 first-person**。
    #   ★★ 全库都没标时**不报这一项**，而不是报 0——**没标不是没有**。
    by_voice: dict[str, int] = {}
    tagged = 0
    for record in sources:
        rel = record.get('local_path')
        path = (target / rel) if rel else None
        if not path or not path.is_file():
            continue
        v = str(record.get('voice') or 'unknown')
        by_voice[v] = by_voice.get(v, 0) + path.stat().st_size
        if v != 'unknown':
            tagged += 1
    voice_block: Any
    if tagged == 0:
        voice_block = ('本人物的台账**没有一份标了 `voice`**——'
                       '**不报占比**（没标不是没有）。v0.0.0.153 起 `ingest.py --voice` 可以标。')
    else:
        tot = sum(by_voice.values()) or 1
        voice_block = {
            '**第一人称字节占比**': round(by_voice.get('first-person', 0) / tot, 4),
            '第三人称': round(by_voice.get('third-person', 0) / tot, 4),
            '作者自供但第三人称写的（communicated）': round(by_voice.get('communicated', 0) / tot, 4),
            '未标（unknown）': round(by_voice.get('unknown', 0) / tot, 4),
            '已标的份数': tagged,
            '★': ('**这个数才是排期与 profile 该看的**。`own_voice_ratio` 按 author 算，'
                  '答的是「谁署名」；本项答的是「他本人说了多少」。'
                  'Coffin #130 两者分岔到极处：门全过而实质的话只有 8 句。'),
        }

    report.metrics['own_voice'] = {
        '★★ 按 voice 字段算的声口分布': voice_block,
        '本人所著的 train 源数': len(own_ids),
        'train 源总数': len(sources),
        '本人所著字节': own_bytes,
        'train 总字节': all_bytes,
        'own_voice_ratio': round(ratio, 4),
        '★ 同名判据': ('未启用（本人物没有 namesake-criteria.json）' if crit_path is None else {
            '按判据剔除的（他人）': excluded[:8],
            '**说不准的（unknown，未计入本人声口）**': unknown[:8],
            '口径': ('只比姓氏会把同姓近亲算进来。Sorby #133 的父亲也叫 Henry Sorby，'
                     '父亲的日记同在馆藏里。**unknown 一律不计入——宁可低报，不可高报。**'),
        }),
        '口径': ('账本 author 命中人物姓氏的 train 源字节占比。'
                 '**与 primary_ratio 量的不是一回事**：后者含「关于他的同期报道」（P2），'
                 '前者只含他本人的表达。改 tier／再多抓报道都不会让这个数变大。'),
    }


def report_refusal_overflow(report, target: Path) -> None:
    """**拒答溢出**（v0.0.0.22，只报不拦）：该拒的拒了，能答的也一起推掉了。

    三次独立盲判指向同一处（「拿边界当答案」／「用单一框架碾过题面」／「拒答溢出」），
    实测代价是单人物臂 **-0.1044**——本项目已测得的最大单项负收益。
    **前三次都被当成风格批评记下，没有一次被当成缺陷修过。**

    ## 为什么只报不拦，不设成 error

    判据数的是**句式**：`你应当`／`不要`／编号步骤会被计为可执行判断，
    而**用陈述句给出的判断（「这题的关键在 X」）会被漏掉**。
    以一个已知有假阴性的判据去硬拦发布，会误杀正当答案，
    而误杀会让人把这个门关掉。

    ## 也不放 warnings

    `--strict` 下任何 warning 都会让门失败（`passed = not errors and not (strict and warnings)`）。
    v0.0.0.8 的教训：「只列不判」放进一个会阻塞的通道，等于自相矛盾。
    **放 metrics，让数字大到无法忽略，但不替执行者做发布决定。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_refusal_overflow.py'
    if not script.exists():
        report.metrics['refusal_overflow'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_refusal', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['refusal_overflow'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.metrics['refusal_overflow'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    hits, scanned = [], 0
    for rel in ('evals/judge_payload.v1.json',):
        p = target / rel
        if not p.is_file():
            continue
        try:
            for cid, res in module.check_payload(p, 'candidate'):
                hits.append(cid)
        except Exception:                                        # noqa: BLE001
            continue
        scanned += 1
    info: dict[str, Any] = {'已扫载荷': scanned, '拒答溢出条数': len(hits)}
    if hits:
        info['**这些答案拒了答且什么也没留下**'] = hits[:12]
        info['口径'] = ('有拒答标记且可执行判断为 0。**数的是句式不是语义**——'
                        '陈述句形式的判断会被漏掉，故只报不拦。')
    report.metrics['refusal_overflow'] = info


def run_ocr_gate(report, target: Path, sources: list[dict[str, Any]]) -> None:
    """OCR 同形字门（v0.0.0.17 新增）。

    ## 触发实例

    Jesse Livermore #100 是本项目第一个**只有扫描件**的人物（1877–1940）。
    他唯一的亲笔著作《How to Trade in Stocks》(1940) 只有 OCR 文本可得，
    实测 12.5 万字里含 **1405 个西里尔字符**、**314 个「全同形字词」**：
    `HOW ТО TRADE` 的 `ТО`、`РКЕҒАСЕ`（PREFACE 七个字母全是西里尔同形字）。

    ## 为什么已有的门一件也拦不住

    `check_verbatim_quotes.py` 拿引文回语料里比对——**从语料里复制一段带同形字的话，
    它会说「找到了」**。逐字引文检查回答的是「语料里有没有这句」，
    不是「这句里的字符是不是真的」。于是门全绿，而交付出去的「他的原话」
    含有他绝不可能写下的字符，读者拿去原书里搜一个字也搜不到。

    ## 两级严重度

    - **语料层：只报不拦**（写进 metrics）。扫描件的 OCR 质量不是执行者能修的，
      而扫描件常常是历史人物**唯一**的一手件。把它判成 error 只会逼人不用扫描件。
    - **引文层：release 阶段 error**。引文必须能被读者拿回原件核对。

    在 research 阶段就报语料层，是为了**在写第一个字之前**知道哪些源是脏的。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_ocr_homoglyphs.py'
    if not script.exists():
        report.metrics['ocr_homoglyphs'] = {
            '状态': 'check_ocr_homoglyphs.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_ocr', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['ocr_homoglyphs'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.error('content.selftest-failed',
                         'check_ocr_homoglyphs.py 负对照未过——其检查结论不作数')
            return

    # ── 语料层：只报不拦 ──────────────────────────────────────────────
    corpus_paths = []
    for record in sources:
        rel = record.get('local_path')
        if not rel:
            continue
        path = target / rel
        if path.is_file():
            corpus_paths.append(path)
    dirty = module.check_corpus(corpus_paths) if corpus_paths else []
    info: dict[str, Any] = {'已查语料件': len(corpus_paths), '含同形字的源': len(dirty)}
    if dirty:
        info['**这些是 OCR 件，取引文时避开脏位置**'] = [
            {'源': Path(rep['file']).name,
             '非拉丁字符': rep.get('counts', {}).get('non_latin_chars'),
             '全同形字词': rep.get('counts', {}).get('all_homoglyph_words'),
             '样例': [f"{s['as_scanned']} 读作 {s['reads_as']}" for s in rep.get('samples', [])[:3]]}
            for rep in dirty[:6]
        ]
    report.metrics['ocr_homoglyphs'] = info

    # ── 引文层：release 阶段是硬门 ────────────────────────────────────
    if report.phase != 'release':
        return
    quote_files = [p for p in (
        list((target / 'evidence').glob('*.jsonl'))
        + list((target / 'references').rglob('*.md'))
        + list((target / 'evals').rglob('*.json*'))
    ) if p.is_file()]
    for problem in module.check_quotes(quote_files):
        report.error('content.ocr-homoglyph', problem)


def run_baseline_provenance(report, target: Path) -> None:
    """delta 到底是跟什么比出来的（v0.0.0.20 新增，**只报不拦**）。

    ## 为什么要有它

    用户 2026-08-02 评分：「没有提供『专家团队相对裸模型，在真实盲测任务上
    提高多少正确率』的公开结果……实际能力非常差，接近 0 分甚至负收益。」

    而最硬的证据来自本项目自己的评委——Livermore #100 第 2 轮 E 席：
    「17 条 baseline 全是零对冲零出处的稻草人，**候选/对照的分差被显著放大，
    不能当作能力证据**。」这句话被抄进提交信息，然后 delta 0.8012 继续被当成绩报。

    **每一件检查器都有负对照，唯独产品本身没有。** 第十八种执行了三十多个版本，
    从未对整个工程执行过；「团队比裸模型强多少」就是这个工程的负对照。

    ## 为什么只报不拦

    100 人已入库、基线全是自撰稻草人。判成 error 会让既有产物集体不可发布，
    而按既定裁定应「选诚实退路继续，绝不为凑数放宽判据」。
    **门要拦的是「拿这个 delta 说自己比裸模型强」，不是拦住发布。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_baseline_provenance.py'
    if not script.exists():
        report.metrics['baseline_provenance'] = {
            '状态': 'check_baseline_provenance.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_baseprov', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['baseline_provenance'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.error('content.selftest-failed',
                         'check_baseline_provenance.py 负对照未过——其结论不作数')
            return
    problems, summary = module.check(target)
    report.metrics['baseline_provenance'] = summary
    for message in problems:
        report.warn('eval.baseline-not-capability-evidence', message)


def run_corpus_text_checks(report, target: Path, cache_dirs: list[str]) -> None:
    """语料**正文层**的两道检查——**研究门与发布门都跑**。

    ★★ v0.0.0.116 更正：这两件（`check_ocr_legibility` v0.0.0.105、
    `check_byline_in_carrier` v0.0.0.116）原本写在 `run_content_checks` 里，
    而**那个函数只在 `--phase release` 被调用**。
    我在 v0.0.0.105 的 CHANGELOG 里写的「已接进 `--phase research`」**是错的**。

    **它们必须在研究门就跑**：这两件问的是「语料本身能不能用」——
    等到发布门才发现「有 10 份是乱码」「有 1 份装错了文件」，
    **中间那一整轮断言、渲染、判分都建在坏语料上了。**
    """
    review = report.metrics.setdefault('content_review', {})
    cache_arg = list(cache_dirs) if cache_dirs else [str(target / 'raw')]
    here = Path(__file__).resolve().parent

    def run(script: str, argv: list[str]) -> tuple[int, str]:
        path = here / script
        if not path.exists():
            return -1, f'{script} 未安装'
        proc = subprocess.run([sys.executable, str(path), *argv],
                              capture_output=True, text=True)
        return proc.returncode, (proc.stdout or '') + (proc.stderr or '')

    # ── v0.0.0.126：**落在两道门之间、谁都没看过的文件** ──────────────────
    #   Koch #107 的 lane 2 整条道只靠 `robertkochlette00koch.txt` 撑着——
    #   **766 字符的手写件 OCR 纯噪声**。而三道门没有一道说过它是好的：
    #   `non_placeholder` 只看字符数（766 ≥ 500，过）；
    #   `check_ocr_language_death` 的下限是**词数 ≥500**，它只有 134 词 → **明说「未检查」**；
    #   `check_ocr_legibility` 的射程是德文花体，**手写噪声不是那一种**。
    #   ★ **只报不拦**——短不等于坏（Godin 的 153 份博客短文全落在这一段）。
    #     它报的是**覆盖缺口**：这几份正在被当作来源用，而没有任何判据看过它们的内容。
    code, out = run('check_unexamined_band.py', cache_arg)
    if code == -1:
        review.setdefault('checker_missing', out)
    else:
        try:
            info = json.loads(out)
        except Exception:                                          # noqa: BLE001
            info = {}
        n_band = info.get('**落在两门之间、谁都没看过的**')
        if n_band:
            review['unexamined_band'] = {
                'n': n_band, 'of': info.get('扫到的 .txt'),
                'files': [b['文件'] for b in (info.get('逐份') or [])[:8]],
            }
            report.warn('corpus.unexamined-band',
                        f'**{n_band}/{info.get("扫到的 .txt")} 份语料落在两道门之间**：'
                        f'字符数够 `non_placeholder`（≥500）而词数不够语种判据（<500），'
                        f'**没有任何判据看过它们的内容**。★ 短不等于坏，本条是覆盖缺口不是缺陷；'
                        f'但若某条道只靠这类文件撑着，请人看一眼。')

    # ── v0.0.0.116：**这份文件里真的有那句署名吗** ────────────────────────
    #   #125 Mendel 抓源存盘用 `p[:8]` 截断 UUID 当文件名，同一期两页前 8 位相同，
    #   **后写的音乐会评论页把讣闻页覆盖了**。三道判据全放行：
    #   花体自查 0.1252 过（那页德文确实干净，只是内容是别的）、
    #   sha256 过（文件不重复）、抓源方的「Mendel 是否出现」过（命中 Mendelssohn）。
    #   ★ 抓出它的是**拿该件自己的特征词回查载体**。这是「判据绿了但指错了文件」
    #   的第 17 起，形态新：**文件名截断造成同名覆盖**。
    code, out = run('check_byline_in_carrier.py', ['--target', str(target)])
    if code == -1:
        review['checker_missing'] = out
    elif code == 2:
        report.error('content.selftest-failed',
                     'check_byline_in_carrier 负对照未过——其检查结论不作数')
    else:
        try:
            info = json.loads(out)
        except Exception:                                          # noqa: BLE001
            info = {}
        n_bad = info.get('**指错文件**') or 0
        if n_bad:
            report.error('corpus.byline-not-in-carrier',
                         f'**{n_bad} 条来源的署名照录，在它自己的载体文件里搜不到**——'
                         '要么记录指错了文件，要么那段引文不是从这份文件里来的。'
                         f'　{[x.get("original_name") for x in info.get("对不上的", [])][:5]}')
        review['byline_in_carrier'] = (
            f"核过 {info.get('核过', 0)} 条，指错 {n_bad} 条"
            + (f"，**没核 {len(info.get('★ 没核的') or [])} 条（不是通过）**"
               if info.get('★ 没核的') else "")
            if info else '**未核（不是通过）**')

    # ── 2026-08-07：**引文逐字在语料里，可它是别人说的**（候选子代理抓出来的） ──
    #   Whitworth #152 的 `clm-e120a051a8ad` 初稿引 General Lefroy 的话当他本人的推测语气，
    #   而他转引之后紧接着写自己确知铸铁做不到——**意思正好相反**。
    #   ★★ `check_quote_integrity` 放行是因为**那句逐字确实在语料里**。
    #     它问「在不在」，**不问「是谁说的」。逐字 ≠ 他的。**
    code, out = run('check_quote_speaker.py', [str(target), '--json'])
    if code == -1:
        review['checker_missing'] = out
    else:
        try:
            qs = json.loads(out)
        except Exception:                                          # noqa: BLE001
            qs = {}
        if qs and '**引到别人的话**' in qs:
            n_other = len(qs['**引到别人的话**'])
            report.metrics['quote_speaker'] = {
                '长逐字引文': qs.get('引文数'),
                '**引到别人的话**': n_other,
                '正文已注明出自他人（不判为误引）':
                    len(qs.get('★ 正文已注明出自他人的（不判为误引，但列出来）') or []),
                '★ 定位不到（未判，不是通过）':
                    len(qs.get('★ 在语料里定位不到的（本件未判，不是通过）') or []),
                '★★ 射程': '只认英文转引标记、只往回看 260 字符、只比姓、'
                            '抓不到无标记的间接引语',
            }
            if n_other:
                report.error('content.quote-is-someone-elses',
                             f'**{n_other} 条引文是别人说的**（逐字在语料里，但转引自他人）：'
                             f'　{[(x["转引自"], x["引文"][:40]) for x in qs["**引到别人的话**"][:3]]}')

    # ── 2026-08-07：**建模者读得到的文件里提了 holdout**（Whitworth #152 撞出来） ──
    #   候选方（隔离子代理）**主动上报**：`hypotheses.md` 写着「证据只有 holdout 里那一条，
    #   train 侧没有第二处」——**把 holdout 的主题直接说了出来**，而它恰好对应那道 known 题。
    #   ★ 那句话是我在「说明我已经把 holdout 内容删干净了」的语境里写下的。
    #   ★★ **同一轮里 `corpus.holdout-leak` 与 `research.invalid-source` 两道门全绿**——
    #     它们只认「id 与文件」，不认「有这么一份、它考什么」。
    code, out = run('check_holdout_mention.py', [str(target), '--json'])
    if code == -1:
        review['checker_missing'] = out
    else:
        try:
            hm = json.loads(out)
        except Exception:                                          # noqa: BLE001
            hm = {}
        if hm and '状态' not in hm:
            n_men = len(hm.get('**字面提及**') or [])
            n_ov = len(hm.get('**与 holdout 正文的 8 词片重叠**') or [])
            # ★★★ 2026-08-10：**「泛提」与「点名」后果差很远，但只报一个总数看不出来。**
            #   全库实测：Barton **16 处字面提及、点名 0**（全是「本路不引 holdout」这类，
            #   不说是哪一份）；而真正泄题的是 Adams 1 处、Virchow 2 处。
            #   **旧的不分档计数会把 Barton 显示成全库最严重的。**
            #   ★ **报错条件一个字没改**——任何提及仍然报错。
            #     这道门当初就是被一句「善意的泛提」触发的（「我已经把 holdout 删干净了」），
            #     把泛提放行等于把它的立门理由删掉。分档只进计量，供人分轻重。
            n_named = len(hm.get('**其中点名了是哪一份的**') or [])
            report.metrics['holdout_mention'] = {
                '字面提及': n_men,
                '**其中点名了是哪一份的**': n_named,
                '★ 只是泛泛提及（不说哪一份）': n_men - n_named,
                '与 holdout 正文重叠': n_ov,
                '★ 与出厂模板逐字相同、已豁免': len(hm.get('★ 与出厂模板逐字相同、已豁免的') or []),
                '★★ 射程': '抓不到「不提 holdout 也不抄它、却把题目描述出来」的写法——'
                           '那一类只能靠人读或答题方主动上报',
            }
            if n_named:
                report.error('corpus.holdout-work-named-in-artifacts',
                             f'**建模者读得到的文件里有 {n_named} 处直接说出了 holdout 是哪一份**'
                             f'（书名／卷次页码／文件名／源 id）——这比「提到有个 holdout」严重得多，'
                             f'**它把那道题考什么也告诉了**。'
                             f'　{[(m["文件"], m["行"]) for m in hm["**其中点名了是哪一份的**"][:3]]}')
            if n_men:
                report.error('corpus.holdout-mentioned-in-artifacts',
                             f'**建模者读得到的文件里有 {n_men} 处提到 holdout**——'
                             '知道「存在一份取不到的材料、它关于某某」已足够定位那道题。'
                             f'　{[(m["文件"], m["命中"]) for m in hm["**字面提及**"][:3]]}')
            if n_ov:
                report.error('corpus.holdout-text-in-artifacts',
                             f'**建模者读得到的文件与 holdout 正文有 {n_ov} 处 8 词片重叠**')

    # ── 2026-08-10：**编号缺口本身泄题**（Nasmyth #153，候选侧子代理主动上报） ──
    #   它在 `__incident__` 里写：「`references/sources` 的文件编号从 05d 跳到 05f，
    #   我没有去查 05e 是什么。」——**它没查，但通道是我留的。**
    #   ★ 上面那道 `check_holdout_mention` 抓的是「有没有**写**出 holdout」，
    #     本件抓的是「**没写**，但目录结构自己说了出来」——**两道门管的不是同一件事**。
    #   ★★ 缺口连着两侧邻居的描述性文件名一起看，泄的是**刊物与年代区间**
    #     （Nasmyth 此例：05d 是 mnras-1852、05f 是 mnras-1855 → 缺的那份是 MNRAS 1852–1855）。
    code, out = run('check_source_numbering_gap.py', [str(target), '--json'])
    if code == -1:
        review['checker_missing'] = out
    else:
        try:
            ng = json.loads(out)
        except Exception:                                          # noqa: BLE001
            ng = {}
        if ng:
            g = ng.get('**编号缺口**') or []
            confirmed = [d for d in g if not d.get('★ 这是疑似')]
            on_holdout = [d for d in g if d.get('★ holdout 的文件名正落在这个缺口上')]
            report.metrics['source_numbering_gap'] = {
                '编号缺口': len(g),
                '其中确认型': len(confirmed),
                '其中疑似（组内首字母不是 a）': len(g) - len(confirmed),
                '★ 缺口上正好是 holdout 的': len(on_holdout),
                '★★ 射程': '只看文件名；**尾部被整份拿走的缺口抓不到**；'
                           '补齐编号也堵不住「份数本身是信息」那一层',
            }
            for k in ('★ 没有 references/sources/', '★ 文件名不带顺序前缀',
                      '★ holdout 文件名不带前缀'):
                if k in ng:
                    # ★ 「看不见」要留痕，**不许被读成通过**
                    report.metrics['source_numbering_gap'][k] = ng[k]
            if on_holdout:
                report.error(
                    'corpus.holdout-visible-as-numbering-gap',
                    f'**holdout 的编号缺口暴露在建模者看得见的文件名序列里（{len(on_holdout)} 处）**——'
                    '建模者不必打开任何禁读目录，数一遍文件名就知道「这里有一份被拿走了」，'
                    '连着两侧邻居还能读出它的刊物与年代区间。'
                    f'　{[(d["缺的编号"], d["左邻"], d["右邻"]) for d in on_holdout[:2]]}')
            elif confirmed:
                report.warn(
                    'corpus.source-numbering-gap',
                    f'**编号缺口 {len(confirmed)} 处**（不在 holdout 上，成因未判）：'
                    f'　{[d["缺的编号"] for d in confirmed[:5]]}')

    # ── 2026-08-07：**来源计数里有几份其实是同一部作品**（Whitworth #152 撞出来） ──
    #   `source.minimum` 判的是 `len(usable)`，**`derived_from` 从头到尾没被读过**。
    #   Whitworth #152 实测 `usable = 7`，而按内容去重只有 **3 部作品**（虚高 2.333×）：
    #   quick 门要 8 份，**再抓 1 份门就转绿，而实质仍是 3 部**——靠灌分子过门。
    #   ★★ 而且**光读声明不够**：同一批 7 对重叠 ≥30% 的关系里，
    #     我自己只声明了 3 对，**漏的 4 对含我明知道的那一对**
    #     （1854 报告整篇是 1858 卷的附录，写进了散文没写进字段）。
    #     所以本件不信声明，直接比 8 词片内容。
    #   ★ **不改 `source.minimum` 的口径**——中途改测量工具会让在做的人物前后不可比。
    #     这里发的是「门是靠重份才绿的」这一条独立错，以及去重后的实数。
    code, out = run('check_source_dedup.py', [str(target), '--json'])
    if code == -1:
        review['checker_missing'] = out
    else:
        try:
            dd = json.loads(out)
        except Exception:                                          # noqa: BLE001
            dd = {}
        if dd:
            n_un = len(dd.get('**未声明的重复对**') or [])
            report.metrics['source_dedup'] = {
                '可用来源': dd.get('usable'),
                '**按内容去重后的作品数**': dd.get('distinct_works'),
                '虚高': dd.get('inflation'),
                '未声明的重复对': n_un,
                '已声明的重复对': dd.get('已声明的重复对数'),
                '★ 本件看不见的份数（中日韩语料一律看不见，不是已核）':
                    len(dd.get('★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）') or []),
            }
            if n_un:
                report.error(
                    'corpus.undeclared-duplicate-sources',
                    f'**{n_un} 对来源重叠 ≥{dd.get("threshold")} 而两边都没声明 `derived_from`**——'
                    '台账上看不出它们是同一部作品。**清掉这条错的唯一办法是补 `derived_from`**——'
                    '★ 本件只读 `derived_from`（`check_source_dedup.py` 第 182 行），'
                    '**在 `counting_convention` 里写散文不会让它变绿**：'
                    '那件判据当初正是因为「散文里写了、机器读得到的字段里没写」才建的。'
                    '散文该写，但它是给人看的，不是给这道门看的。'
                    f'　{[(p["甲"][:26], p["乙"][:26], p["重叠"]) for p in dd["**未声明的重复对**"][:3]]}')
            # ★ `thresholds` **不在本函数的作用域里**（`run_corpus_text_checks(report, target,
            #   cache_dirs)`）。第一版直接写 `thresholds.get(...)`：`py_compile` 绿、
            #   语法检查绿，**一跑就 NameError，整个 JSON 输出被打断**。
            #   与 [[a-checker-nothing-calls-is-not-a-checker]] 第五批同形——
            #   **只有真跑一次才看得见**。就地从 meta 取。
            try:
                _profile = json.loads((target / 'meta.json').read_text(encoding='utf-8')
                                      ).get('profile', 'standard')
                _min = (PROFILE_THRESHOLDS.get(_profile) or {}).get('min_sources')
            except (OSError, ValueError):
                _min = None
            if (_min and dd.get('usable') is not None and dd.get('distinct_works') is not None
                    and dd['usable'] >= _min > dd['distinct_works']):
                report.error(
                    'corpus.source-count-inflated-by-duplicates',
                    f'**`source.minimum` 只是被重份撑绿的**：可用来源 {dd["usable"]} ≥ 门 {_min}，'
                    f'而按内容去重后只有 **{dd["distinct_works"]} 部作品**（虚高 {dd["inflation"]}×）。'
                    '**这道门量的是「有几个 source_id」，不是「有几处独立证据」。**')

    # ── v0.0.0.105：花体乱码是**替换**不是**缺失**，上面那件按「缺失」判，会漏 ────
    #   Liebig #124 实测，10 份已知的 Fraktur 乱码里 `check_ocr_language_death` 只抓到 **5**。
    #   漏的成因可指认：它取**多语种里最高的虚词占比**，而乱码德文会被别的语种接住——
    #     bub_gb_QlVBAAAAYAAJ 0.109 **[pt]**、vollstndigerunt00liebgoog 0.159 **[pt]**、
    #     b2130886x 0.189 **[fr]**、diemodernelandw00liebgoog **0.327 [de]**
    #   最后那份尤其说明问题：短虚词（in/so/an/um）扛过了花体 OCR，
    #   而 `der/die/und/ist` 整批变成 `ber/bie/unb/ift`——**总量没掉，是被换掉了。**
    #   本件直接比「正确形 vs 乱码形」，那 10 份 **10/10 全中**。
    #   两件在 Virchow 上 16 vs 16、交集 15，**各自还能抓到对方漏的一份**——是互补不是替代。
    code, out = run('check_ocr_legibility.py', list(cache_arg))
    if code == -1:
        review['checker_missing'] = out
    elif code == 2:
        report.error('content.selftest-failed',
                     'check_ocr_legibility 负对照未过——其检查结论不作数')
    else:
        try:
            n_bad = json.loads(out).get('**判为花体乱码**', 0)
        except Exception:
            n_bad = 0
        if n_bad:
            report.warn('corpus.fraktur-mojibake',
                        f'**{n_bad} 份德文语料是花体 OCR 乱码**——'
                        'der→ber、und→unb、ist→ift，整篇没有一个词能拿去检索或引用。'
                        '份数／分档／字数三样都是真的，所以既有的门都放行了；'
                        '**从这些文件里取不出任何可核的逐字引文**。')
        review['fraktur_mojibake'] = f'{n_bad} 份' if n_bad else '✓ 没有花体乱码'

    # ★★★ v0.0.0.136：**台账上有、磁盘上没有的源。**
    #   Blackwell #118 实测：台账 95 行里有 6 行（4 本日记＋2 份手稿，**88,685 词，全是 P1**）
    #   **正文根本不在工作区**——而它们照样被计进 `min_sources` 与 `primary_ratio`。
    #   也就是说：**门在给没有正文的源发学分。**
    #   Barton #117 同类 4 份（4 本日记，57,073 词）。
    #
    # ★★★ 2026-08-05 当天撤回上面那段：**那 10 份全在 `references/holdout/` 里，
    #   是按设计隔离的判分材料，不是丢失。** 判据当时不认识 holdout 目录，
    #   我拿着它的输出没去问「文件到底在哪」就写成了「门在给没有正文的源发学分」。
    #   **判据已修（`ingested_names` 纳入 holdout），全库一手缺口 10 → 0。**
    #   ★ 接线保留——**修好之后它反而看见了真的**：
    #     Galen #101 台账 66 / 工作区 1、Harvey #103 105 / 1、Vesalius #102 46 / 1，
    #     三人工作区 `raw/` 几乎是空的（任务 #37 与 check_corpus_presence 的老账）。
    #
    #   ★ 为什么此前没人发现：`check_staged_but_not_ingested` 与 `check_corpus_presence`
    #     **两件都没接进任何一道门**，只在 `check_checkers` 元普查里跑——
    #     而元普查是审计工具，不是门。**判据建好而不接线，等于没有。**
    #   ★★ 我曾在这里写「`check_corpus_presence` 按目录算、看不出正文不在」——**那句也是错的，已撤回**。
    #     实测：Blackwell 95 行 `local_path` **逐条解析得到真实文件、0 行落空**（含 6 行指向 holdout）。
    #     **它报 ✓ 是对的。** 两件判据管的是不同的事：
    #     `check_corpus_presence` 问「台账指的文件在不在」，
    #     `check_staged_but_not_ingested` 问「抓到的东西有没有进到建模看得见的地方」。
    outer = target.parent.parent if target.parent.name == 'workspaces' else target.parent
    # ★ 判据按「_corpora 根下每个 wip-* 是一个人物」扫，**给它单个工作区它会扫成空**
    #   （我第一版就是这么传的，于是它对 Blackwell 报「✓ 一致」——**假绿**）。
    code, out = run('check_staged_but_not_ingested.py', [str(outer.parent)])
    if code == -1:
        review['staged_not_ingested'] = out
    else:
        try:
            _s = json.loads(out[out.find('{'):])
            _me = [m for m in _s.get('明细', []) if m.get('人物') in (outer.name,)]
            if _me:
                m0 = _me[0]
                n_miss = m0.get('**没进工作区**', 0)
                n_pri = m0.get('其中一手', 0)
                review['staged_not_ingested'] = (
                    f"台账 {m0.get('台账')} / 工作区 {m0.get('工作区')}，"
                    f"**没进工作区 {n_miss} 份，其中一手 {n_pri} 份**"
                    + ("　★ 这些源仍被计进 min_sources 与 primary_ratio——**门在给没有正文的源发学分**"
                       "（★★ `references/holdout/` 已排除在外，**这不是 holdout 被误报**；"
                       "若仍存疑，先 `find` 一遍再下结论——⑯ 就是没 find 就升级出来的误报）"
                       if n_pri else "")
                    + "　★ 清单：" + "、".join(str(x) for x in m0.get('清单', [])[:6]))
            else:
                review['staged_not_ingested'] = '✓ 台账与工作区一致（或本人物没走过抓源台账）'
        except (json.JSONDecodeError, ValueError, TypeError):
            review['staged_not_ingested'] = '**未核（不是通过）**：输出解析不了'

    # ★ v0.0.0.135：**语料文件头里引的话，正文里必须真有。**
    #   头部此前不在任何判据的射程里，而它恰恰是「这份东西是什么」的唯一说明——
    #   下游的分档、归属、坐标全从它来。**头错了下游全跟着错，而且看起来有据。**
    #   实测抓出三处「改了 OCR 讹字再当逐字引文用」（Slavyanov #115 两处、
    #   另一处同类在 Carver #127 由别的判据抓到）。
    #   ★★ 覆盖面很窄：全库 5,016 份 .txt 里，头部带引文的只有 2 条——
    #   **报 0 时必须连「头部引文只有几条」一起报**，否则那个 0 会被读成全库体检合格。
    code, out = run('check_source_header_quotes.py', [str(target / 'raw')])
    if code == -1:
        review['source_header_quotes'] = out
    else:
        try:
            _h = json.loads(out)
            _n, _bad = _h.get('头部里的引文', 0), _h.get('**正文里找不到的**', 0)
            review['source_header_quotes'] = (
                f"头部引文 {_n} 条，**正文里找不到 {_bad} 条**"
                + ("　★ 逐条：" + "｜".join(f"{b['文件']}: {b['头部引的'][:60]}"
                                            for b in _h.get('逐条', [])[:4]) if _bad else "")
                + ("　★★ 覆盖面窄：头部不引原文的文件本件看不见，**这个数不是全库体检**"
                   if not _bad else ""))
        except (json.JSONDecodeError, TypeError):
            review['source_header_quotes'] = '**未核（不是通过）**：输出解析不了'

    # ★ v0.0.0.130：**研究文档层的逐字引文**——放在本函数而不是 run_content_checks，
    #   因为**后者只在 --phase release 被调用**（本文件 v0.0.0.116 已经为同一件事
    #   更正过一次，而我今天又原样犯了一遍：先写进 run_content_checks，
    #   跑研究门时它一声不吭，我差点当成「✓ 通过」）。
    #
    #   此前 `check_quote_integrity` 只在 `claims.exists()` 时才跑，
    #   而 claims 是**合成阶段**才有的东西：于是 `references/research/*.md` 里的
    #   逐字引文**在整条流水线上从未被任何判据核过一次**——而断言正是从这些文档里提出来的。
    #   Carver #127 实测：78 条研究文档引文，我手工声称「58/58 逐字核过」，
    #   工具一跑就查出 `iSyy.` 被我写成了 `1899.`（**改 OCR 讹字再当逐字引文**）。
    #   ★★ **手工核不是核。**
    research_docs = sorted((target / 'references/research').glob('*.md'))
    if research_docs:
        code, out = run('check_quote_integrity.py',
                        ['--docs', *[str(x) for x in research_docs], '--cache', *cache_arg])
        n = next((l for l in out.splitlines() if l.startswith('引文 ')), '')
        if code == -1:
            review['research_quote'] = out
        elif code == 3:
            review['research_quote'] = '研究文档引文**未核成**（不是通过）：**一份语料都没读到**'
        elif code == 4:
            # ★ 研究文档里没有引文是**允许的**（不是每份研究道文档都必然带逐字引文），
            #   但要说清是「没有可核的」而不是「核过了没问题」。
            review['research_quote'] = '研究文档里**一条引文都没扫到**——没有可核的对象（不是通过）'
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_quote_integrity 负对照未过——其研究文档结论不作数')
        elif code != 0:
            bad = [l.strip() for l in out.splitlines() if l.strip().startswith('⚠ 研究/')]
            review['research_quote'] = (f'**有引文未在语料中找到**——未命中不等于伪造，须人工核对；'
                                        f'但「改了 OCR 错字再当逐字引文」也落在这里。{n}｜'
                                        + '｜'.join(bad[:6]))
        else:
            review['research_quote'] = f'✓ 研究文档每条逐字引文都在语料中（{n}）'

    # ── v0.0.0.137：**声口密度**（只报不拦）────────────────────────────────
    #   Coffin #130 撞出来的：三道门全过（18 源 / 3 道 / 一手 83.3%）、研究门 16 errors → 0，
    #   **而 172,138 字符里他自己说的实质的话只有 15 句**——18 份里 14 份是专利说明书，
    #   文体决定了几乎全是第三人称装置描述加权利要求样板。
    #   ★ `min_sources`/`min_lanes`/`min_primary_ratio` 三个门量的都是**来源的属性**，
    #     没有一个量「语料里有多少句是他说的」。
    #     一份 30k 字的专利和一段 300 字的答辩，在门那里**一样是 1 份 P1 writings**。
    #   ★★ 所以它必须在**研究门**就报：等到判分才发现无话可引，
    #     中间那一整轮断言与用例都白写了。**只报不拦**——
    #     分析型/第三人称产物本来就不靠第一人称，够不够取决于要出哪些用例。
    rc, out = run('check_first_person_density.py', [str(target / 'raw')])
    if rc == -1:
        review['first_person_density'] = 'check_first_person_density.py 未安装，**未核验**（不是通过）'
    else:
        try:
            d = json.loads(out)
            n = d.get('**实质第一人称句**')
            dens = d.get('**密度（每万字）**')
            review['first_person_density'] = {
                '实质第一人称句': n, '密度/万字': dens,
                '正文字符': d.get('正文字符'),
                '★ 口径': '**只报不拦**。参照：Coffin #130 = 15 句 / 0.87，三道门全过而声口不够，已记延后。',
            }
            if isinstance(n, int) and isinstance(dens, (int, float)) and dens < 1.0:
                # ★★★ **不许走 `report.warn`。** 我第一版这么写了，同时在注释里写着「只报不拦」——
                #   **注释与代码不一致**：`package_target` 的 strict 发布门下 **warning 也会拦**，
                #   于是它拦掉了 3 个合成夹具（正文里本来就 0 句第一人称），全量测试 5 红。
                #   「只报不拦」的意思是**只进 metrics**，不进 warnings、不进 errors。
                review['first_person_density']['⚠ 声口薄'] = (
                    f'**{dens}/万字（实质第一人称 {n} 句）**——门量的是来源不是声口。'
                    f'`voice`/`trajectory`/`contrast` 这类要他谈自己的题很可能无据；'
                    f'出题前先看 `references/research/` 里有没有他开口说话的材料。'
                    f'★ 参照 Coffin #130：15 句 / 0.87，三道门全过而声口不够，已记延后。')
        except Exception as exc:                                    # noqa: BLE001
            review['first_person_density'] = f'输出解析失败，**未核验**：{exc}'


def run_content_checks(report, target: Path, cache_dirs: list[str]) -> None:
    """把内容层检查接进发布门（v0.0.0.8 新增）。

    ## 为什么要接进来

    官方门原本只查**结构完整性**：文件在不在、字段全不全、数量对不对。
    而 Icahn #92 到 Salatin #95 这五人暴露的严重缺陷**全部属于内容层**——
    引了源但源里没这事实、伪造引文、订正换个措辞又活了、claim 标记错挂、
    订正脚本留下的字段污染。**三个门当时全绿。**

    结构完整的产物，完全可以每一句都错。

    ## 硬门 vs 只列不判

    - **硬门**（不过即拦）：装饰性引用、伪造引文、订正残留。
      这三件都带负对照（`--self-test`），**负对照不过则其结论一律不作数**。
    - **只列不判**（写进 `metrics['content_review']` 供人工看）：绝对化断言、
      段内冗余、字段漂移、claim 标记锚点。它们有已知的合理误报形态，自动判定会误伤。

      **★ 必须放 metrics 不能放 warnings**：`--strict` 下任何 warning 都会让门失败
      （`passed = not errors and not (strict and warnings)`）。
      第一版放进 warnings，直接让 skill 自带的 11 个测试全红——
      **「只列不判」的语义就是不阻塞，放进一个会阻塞的通道等于自相矛盾。**

    ## 没有 cache 时怎么办

    `check_claim_coverage` 与 `check_quote_integrity` 需要原始语料。
    取不到时**不静默跳过**——记一条 warning 说明「本次未做内容层核验」，
    因为「没查」和「查过没问题」必须能被区分出来。
    """
    here = Path(__file__).resolve().parent
    claims = target / 'evidence' / 'claims.jsonl'

    def run(script: str, argv: list[str]) -> tuple[int, str]:
        path = here / script
        if not path.exists():
            return -1, f'{script} 未安装'
        proc = subprocess.run([sys.executable, str(path), *argv],
                              capture_output=True, text=True)
        return proc.returncode, (proc.stdout or '') + (proc.stderr or '')

    # ── 先验检查器本身：负对照不过，它的「全绿」不构成任何证据 ──────────
    # v0.0.0.12：此前这里**只点名先验两件**（claim_coverage / semantic_residue），
    # 于是其余检查器有没有负对照从来没人问过。实测普查结果：
    # **5 件根本没有负对照，1 件有但跑不起来**，其中 `check_verbatim_quotes`
    # 还是硬门。改为交给元检查器普查全部，不再手工点名。
    # ★ 判据用**退出码**，不再用 `'负对照通过' not in out` ——
    #   各检查器的通过标记本就不统一（`自测 5/5`、`✓ 无关文本被放过`…），
    #   按串匹配等于只认其中两件的写法。
    code, out = run('check_checkers.py', [str(here), '--json'])
    if code == -1:
        report.metrics.setdefault('content_review', {})['checker_census'] = out
    else:
        try:
            rows = json.loads(out)
        except json.JSONDecodeError:
            rows = []
            report.metrics.setdefault('content_review', {})['checker_census'] = \
                '元检查器输出无法解析，**本次未做检查器先验**（不是通过）'
        tally: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            tally[row['verdict']].append(row['checker'])
        for name in tally.get('FAILED', []):
            report.error('content.selftest-failed',
                         f'{name} 负对照未过——其检查结论不作数')
        census: dict[str, Any] = {'负对照可用': len(tally.get('OK', []))}
        if tally.get('NO-SELFTEST'):
            census['**无负对照**（其「全绿」不构成证据）'] = tally['NO-SELFTEST']
        if tally.get('NOT-STANDALONE'):
            census['**负对照不可独立验证**'] = tally['NOT-STANDALONE']
        report.metrics['checker_census'] = census

    review: dict[str, str] = {}
    # ★★★★ v0.0.0.155：**没给 --cache 时自动用 `<target>/raw`**。
    #   本文件里另外三处早就这么做了（run_corpus_text_checks 1069 行、
    #   report_verbatim_quotes 1825 行、run_holdout_overlap 3199 行），
    #   **只有管内容层的这一处没有** —— 于是：
    #     · `package_target.py` 跑的是 `quality_check --phase release --strict`，**不带 --cache**；
    #     · 「未做」只写进 review 说明，**不算 warning**，所以 `--strict` 也咬不住；
    #     · 结果 `passed=True / errors=0 / warnings=0` —— **装饰性引用与伪造引文
    #       从来没有在任何一次打包里被查过**。
    #   2026-08-11 干净检出演练实测（Shewhart #165，昨天刚入库的第 102 个产物）：
    #     无 cache + strict → passed=True  errors=0
    #     有 cache + strict → **passed=False errors=1**（`content.decorative-citation`）
    #   ★ 这不是放宽判据，是把一个函数改成和它三个兄弟一致；
    #     判据本身一直是好的，**缺的是调用方给它输入**。
    if not cache_dirs:
        _auto = target / 'raw'
        if _auto.is_dir() and any(p.is_file() for p in _auto.rglob('*')):
            cache_dirs = [str(_auto)]
            review['corpus_cache'] = (
                '未给 --cache，**自动使用 `%s`**（与本文件另外三处一致）' % _auto.name)
    if not cache_dirs:
        # ★ 语料目录真的不在标准位置时，「未做」必须有牙齿：记成 warning，
        #   这样 `--strict`（打包走的就是 strict）会拦下来，而不是静默放行。
        review['corpus'] = (
            '没有 `--cache`，`<工作区>/raw` 也不存在或为空——'
            '装饰性引用与伪造引文两项**未做（不是通过）**')
        report.warn('content.corpus-unavailable',
                    '内容层未核：既没给 --cache，工作区里也没有 raw/ 语料')
    if cache_dirs:
        code, out = run('check_claim_coverage.py',
                        ['--workspace', str(target), '--cache', *cache_dirs])
        if code == -1:
            review['checker_missing'] = out
        elif code == 2:
            # ★ v0.0.0.38：退出码 2 是**「语料回连不上，本次结论不可信」**，
            #   不是「查出了装饰性引用」。此前这里写的是 `elif code != 0`，
            #   把 2 和 1 收成同一个错——于是「没查成」被报成了「查出问题」。
            #   Lister #108 实测撞出：`--cache` 指到 `raw/` 时 60 份语料一份没读到，
            #   门照样报「存在装饰性引用」，而真实情况是**一条都还没核过**。
            #   检查器自己是设了防的（它 return 2 并打印「结果不可信」），
            #   **防线设在检查器里、在调用点被抹掉了。**
            #   这仍是硬错——不可信的结论不能当通过——但错要报对。
            report.error('content.coverage-unresolved',
                         '装饰性引用**未核成**（不是通过）：过半来源回连不上缓存正文，'
                         '先确认 --cache 是否指到工作区根（本流水线语料在 raw/<source_id>/ 下）')
        elif code != 0:
            # ★ 判据用**退出码**，不用输出串。
            #   第一版写的是 `'结论: 通过' not in out`——而输出里的「不通过」
            #   **包含「通过」这两个字**，于是判断整个反了：真有装饰性引用时反而放行。
            #   接线当场做了负对照才发现（植入一条假断言，门没拦住）。
            #   **中文子串匹配天然有这个坑：否定式包含肯定式。**
            report.error('content.decorative-citation',
                         '存在装饰性引用：断言挂的来源正文里找不到其关键实体')
        for line in out.splitlines():
            if line.startswith('实际检查'):
                report.metrics['claim_coverage_checked'] = line.strip()

        if claims.exists():
            # v0.0.0.35：射程从断言层扩到**答案层**。
            # Jenner #104 实测：断言层 6 条引文全绿，而答案层 20 条里有 1 条是
            # 「把 OCR 错字（DoHors→Doctors、WOQDVILLE→WOODVILLE）顺手改正了再当逐字引文用」。
            # **断言层绿不代表答案层绿——被判、被发布的是答案层。**
            argv = ['--claims', str(claims), '--cache', *cache_dirs]
            payload = target / 'evals/judge_payload.v1.json'
            if payload.exists():
                argv += ['--answers', str(payload)]
            else:
                review['quote_integrity_scope'] = (
                    'evals/judge_payload.v1.json 不在——**答案层未核验（不是通过）**；'
                    '候选答案没落进工作区时，任何门都看不见它')
            code, out = run('check_quote_integrity.py', argv)
            # ★ v0.0.0.38：改用**退出码**。此前是 `'未命中 0 个' not in out`——
            #   串匹配在语料读到 0 份时同样成立，于是「没核成」被印成
            #   「有引文未在语料中找到」，与真发现长得一模一样。
            #   0=干净　1=查出未命中　2=自测未过　3=语料读不到
            if code == -1:
                review['checker_missing'] = out
            elif code == 3:
                report.error('content.quote-unresolved',
                             '引文核验**未做成**（不是通过）：一份语料都没读到，'
                             '确认 --cache 指到含 .txt 的目录（本流水线在 <工作区>/raw/ 下）')
            elif code == 4:
                # ★ 语料读到了，只是断言/答案里一条引文都没有。
                #   与「语料读不到」是两回事，**不要印成同一句话**。
                report.error('content.no-quotes-to-verify',
                             '引文核验**没有可核的对象**（不是通过）：语料读到了，'
                             '而断言与答案里**一条引文都没扫到**——'
                             '本产品的立身之本是能出示一手逐字引文，一条都没有本身就是问题')
            elif code == 2:
                report.error('content.selftest-failed',
                             'check_quote_integrity 负对照未过——其检查结论不作数')
            elif code != 0:
                review['quote_integrity'] = ('有引文未在语料中找到'
                                             '——**未命中不等于伪造**，须人工核对；'
                                             '但「改了 OCR 错字再当逐字引文」也落在这里')


    #   ★ 2026-08-11：`payload` 原本在上面那段「引文坐标」里定义，
    #     我把那段挪到函数末尾时**把定义一起带走了**，而这里还在用它
    #     → `UnboundLocalError`。**搬运一段代码时，要问它给别人留下了什么。**
    payload = target / 'evals/judge_payload.v1.json'

    # ── v0.0.0.40：同一段语料被多处引用时并排列出（**只列不判**）────────
    #   Lister #108 第 2 轮，两席各自独立报出同一处：boundary-01 据 PREFACE 说
    #   「选目是我自己定的」，refusal-stop-02 引同样两句却说「这样讲就说过头了」。
    #   代价实测：boundary 套组 0.8875 → 0.8300，把一道**本来已经过了**的 deep 门
    #   （0.85）打回不过。根因是同一说法我改了两处、漏了第三处。
    #   本件不判两处结论是否互相否定（那要读懂中文语义），
    #   它把 32 题压成几组并排，让人在几行内看完。**不阻塞。**
    if payload.exists():
        code, out = run('check_shared_anchor.py', ['--answers', str(payload)])
        if code == -1:
            review['checker_missing'] = out
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_shared_anchor 负对照未过——其检查结论不作数')
        else:
            head = next((l for l in out.splitlines() if l.strip()), '')
            review['shared_anchor'] = f'⚠ 只列不判，须逐组人工读：{head.strip()[:120]}'
    else:
        review['shared_anchor'] = 'evals/judge_payload.v1.json 不在——**同源引用未比对（不是通过）**'

    # ── v0.0.0.59：引文有没有落在别人那一段（**硬门**）────────────────
    #   `check_quote_integrity` 只问「这句在不在语料里」。
    #   **整版扫图的语料里，「在」是不够的**——同一个 .txt 常常还装着同页别人的文章。
    #   Fleming #111：`penicillin-letter-1941` 的下半版是新西兰医院财政的另一篇，
    #   `freelance-science-1952` 同版还有 P. A. Gorer 的两篇书评。
    #   **从这些文件取引文而不确认落在哪一段，会把别人的文字挂到本人物名下，
    #   而引文核查会说「在」。**
    #   需要一份由读过原文的人写的边界清单；**没有清单就明说没查，不猜边界。**
    bounds = None
    for cd in (cache_dirs or []):
        cand = Path(cd) / '_BOUNDARIES.json'
        if cand.is_file():
            bounds = cand
            break
    if not bounds:
        review['quote_in_span'] = (
            '没有 `_BOUNDARIES.json` 作者边界清单——**引文落段未核（不是通过）**；'
            '语料若含整版扫图，须由读过原文的人写出每篇的起止行')
    elif not payload.exists():
        review['quote_in_span'] = 'judge_payload 不在——**引文落段未核（不是通过）**'
    else:
        argv = ['--answers', str(payload), '--boundaries', str(bounds),
                '--cache', str(bounds.parent)]
        if claims.exists():
            argv += ['--claims', str(claims)]
        code, out = run('check_quote_in_span.py', argv)
        if code == -1:
            review['checker_missing'] = out
        elif code == 3:
            review['quote_in_span'] = '边界清单读不到——**未核（不是通过）**'
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_quote_in_span 负对照未过——其检查结论不作数')
        elif code != 0:
            hit = next((l for l in out.splitlines() if l.startswith('✗')), '')
            report.error('content.quote-out-of-span',
                         '**有引文落在别人那一段里**——整版扫图同页有别的文章：'
                         + hit.lstrip('✗ ')[:160])
        else:
            line = next((l for l in out.splitlines() if l.startswith('逐字引文')), '')
            review['quote_in_span'] = '✓ ' + line[:120]

    # ── v0.0.0.51：长度不许成为指认候选侧的信号（**硬门**）──────────────
    #   盲判的前提是评委看不出哪一侧是候选。Lister #108 第 3 轮实测：
    #   候选比基线长 **+144%**，**64 题里候选没有一道不比基线长**——
    #   席 D 直接写「长的一侧在 32/32 全部命中同一个系统」。
    #   那一轮 delta +0.1292，**多少是内容挣的、多少是长度送的，数据内部无对照可答。**
    #   此前这条规则是每人 `gen_*_answers.py` 里手抄的一段，**没有负对照、也没人统一跑**。
    baseline = target / 'evals/baseline.v1.json'
    if not baseline.exists():
        # ★ 这是个真缺口：**基线从来没落进工作区**，所以任何门都看不见它。
        #   与「候选答案没落进工作区时任何门都看不见它」同一类。
        review['answer_surface_leak'] = (
            'evals/baseline.v1.json 不在——**表面特征泄题未核（不是通过）**；'
            '基线只存在于人物工作目录里，没落进工作区，**门看不见它**')
    elif not payload.exists():
        review['answer_surface_leak'] = 'judge_payload 不在——**表面特征泄题未核（不是通过）**'
    else:
        # ★★ 2026-08-05 用户裁定（待裁定 ⑭）：长度两条对 `bare-model-run` 基线只报不拦。
        #   基线来源**从 results.jsonl 自己读**，不另立一个可以随手填的开关——
        #   否则「声明成 bare-model-run 就免拦」会变成一句谁都能写的话。
        #   口径与 check_baseline_provenance 同源：全部 baseline 行都标同一个来源才算数，
        #   混杂或缺标一律按最严的 self-authored 处理。
        _srcs = set()
        _res = target / 'evals/results.jsonl'
        if _res.exists():
            for _l in _res.read_text(encoding='utf-8').splitlines():
                if not _l.strip():
                    continue
                try:
                    _r = json.loads(_l)
                except json.JSONDecodeError:
                    continue
                if _r.get('system') == 'baseline':
                    _srcs.add(str(_r.get('baseline_source') or 'unknown'))
        _bsrc = _srcs.pop() if len(_srcs) == 1 else 'self-authored-strawman'
        review['answer_surface_leak_baseline_source'] = (
            f'{_bsrc}' + ('' if len(_srcs) == 0 else '（**来源混杂，按最严处理**）'))
        code, out = run('check_answer_surface_leak.py',
                        ['--candidate', str(payload), '--baseline', str(baseline),
                         '--baseline-source', _bsrc])
        if code == -1:
            review['checker_missing'] = out
        elif code == 3:
            report.error('eval.surface-leak-unresolved',
                         '表面特征泄题**未核成**（不是通过）：两侧没有共有的题号')
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_answer_surface_leak 负对照未过——其检查结论不作数')
        elif code != 0:
            hit = [l for l in out.splitlines() if l.startswith('✗')]
            report.error('eval.surface-leak',
                         '**表面特征会指出哪一侧是候选**，这一轮的盲判不成立：'
                         + '；'.join(h.lstrip('✗ ') for h in hit)[:200])
        else:
            # ★ 2026-08-04：原先只回显长度那一行。**格式通道的数不回显，
            #   等于让人以为「长度过了＝盲判成立」——Barton #117 正是这么过的。**
            line = next((l for l in out.splitlines() if l.startswith('**总体均长比')), '')
            worst = max((l for l in out.splitlines() if '可利用' in l),
                        key=lambda l: l.split('可利用')[-1], default='')
            review['answer_surface_leak'] = ('✓ ' + line.replace('**', '')[:100]
                                             + '；表面特征最高 ' + worst.strip()[:60])

    # ── v0.0.0.49：答案里的人名，回语料查它有没有依据（**只列不判**）────────
    #   Osler #110 第 2 轮我写「第 9 版起是 McCrae 续修，**后来是 Henry A. Christian**」。
    #   McCrae 有扉页依据，Christian 没有——**那半句是我编的。**
    #   席位 E 在盲判里说中了，但**它证实不了**：评委手上没有语料。
    #   两席三轮共六次评审，对这半句只能停在「起疑」。
    #   与 `check_quote_integrity` 同一道理：**评委验不了引文，一行 grep 全抓得出。**
    #   **必须接进来**——没人调用的判据等于不存在，而这条正是零编造那条铁律的机检对应物。
    if cache_dirs and payload.exists():
        argv = ['--answers', str(payload), '--cache', cache_dirs[0]]
        led = target / 'evidence' / 'source-ledger.jsonl'
        if led.exists():
            argv += ['--ledger', str(led)]
        code, out = run('check_unsourced_names.py', argv)
        if code == -1:
            review['checker_missing'] = out
        elif code == 3:
            report.error('content.names-unresolved',
                         '承重人名**未核成**（不是通过）：一份语料都没读到')
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_unsourced_names 负对照未过——其检查结论不作数')
        elif code != 0:
            # 硬错：语料与项目记录里都查不到这个名字，**那是编造的形状**
            bad = next((l for l in out.splitlines() if l.startswith('✗')), '')
            report.error('content.unsourced-name',
                         f'答案里有查无实据的人名——{bad.strip()[:120]}')
        else:
            soft = next((l for l in out.splitlines() if l.startswith('⚠')), '')
            review['unsourced_names'] = soft.strip()[:140] or '✓ 没有查无实据的人名'
    else:
        review['unsourced_names'] = (
            '缺 --cache 或 judge_payload，**承重人名未核（不是通过）**')

    # ── v0.0.0.41：这道门在当前评委分布下够不够得着 ──────────────────
    #   Pasteur / Koch / Lister 连续三人死在 min_fact 0.93。
    #   到第三人第三轮才去数两席的分数分布：席 E 在 130 次候选打分里
    #   **给出 ≥9.0 的次数是 0**，实测可达上限 0.885–0.920，全都低于 0.93。
    #   三个人、九轮评审之后才想到数这一下——本条把那一下变成每次都做。
    #   **它不判「门槛该不该改」**（那是人的决定，三条化解路径各带一个
    #   作者能自己滥用的旋钮），只回答纯算术：以这批实测分为据，够不够得着。
    # ── v0.0.0.45：自报字数必须数得对 ────────────────────────────────
    #   一个主动邀请读者核对的数字，**如果它自己是错的，伤害比不给还大**。
    #   Virchow #109 第 1 轮：两席各自独立抓到同一处（自称十七字、实为 14），
    #   token-efficiency 套组因此 −0.0700，是那一轮唯一为负的套组。
    #   同类此前已发生多次（Koch、Lister 各一轮），每次都是「下次注意」，
    #   **没有一次落成判据**。这一次落成，且回验三人：
    #   Virchow 1 处错、Lister 2 处全对、Koch 2 处全对——不是「凡自报皆报」。
    if payload.exists():
        code, out = run('check_self_reported_counts.py', ['--answers', str(payload)])
        if code == -1:
            review['checker_missing'] = out
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_self_reported_counts 负对照未过——其检查结论不作数')
        elif code != 0:
            bad = [l.strip() for l in out.splitlines() if l.strip().startswith('⚠')]
            report.error('content.self-count-wrong',
                         '**自报字数与实数对不上**——主动邀请核对的数字自己错了，'
                         '比不给更伤。' + ('　' + '；'.join(bad[:3]) if bad else ''))
        else:
            review['self_counts'] = next(
                (l for l in out.splitlines() if l.startswith(('自报字数', '没有自报'))),
                '✓ 自报字数已核')
    else:
        review['self_counts'] = 'evals/judge_payload.v1.json 不在——**自报字数未核（不是通过）**'

    # ── v0.0.0.42：OCR 把整份文本毁掉了，而它仍是一份「真文档」──────────
    #   Virchow #109（德文）撞出：227 份语料里 18 份被 Fraktur OCR 毁掉，
    #   `check_corpus_integrity` 扫同一批报 0 可疑（它只判「是不是错误页」），
    #   `check_ocr_homoglyphs` 也报不出（它查的是西里尔／希腊同形字）。
    #   本件按虚词占比判，阈值 0.15 是从 227 份真实分布里**读出来的**
    #   （0.117–0.239 之间一份都没有）。已在 Jenner/Lister/Pasteur 三人 289 份上零误报。
    cache_arg = list(cache_dirs) if cache_dirs else [str(target / 'raw')]
    ledger = target / 'evidence/source-ledger.jsonl'
    argv = list(cache_arg) + (['--ledger', str(ledger)] if ledger.exists() else [])
    code, out = run('check_ocr_language_death.py', argv)
    if code == -1:
        review['checker_missing'] = out
    elif code == 2:
        report.error('content.selftest-failed',
                     'check_ocr_language_death 负对照未过——其检查结论不作数')
    elif code == 1:
        report.error('corpus.ocr-dead-as-primary',
                     '**有被 OCR 整份毁掉的文件被记作 P1**——'
                     '你正打算从一份读不出字的文件里取逐字引文；换干净扫本或降级')
    else:
        n = next((l for l in out.splitlines() if '低于下限' in l), '')
        review['ocr_language_death'] = (n.strip()[:150] if n
                                        else '✓ 没有被 OCR 整份毁掉的语料')

    res = target / 'evals/results.jsonl'
    if not res.exists():
        review['gate_reachability'] = 'evals/results.jsonl 不在——**门槛可达性未检查（不是通过）**'
    else:
        code, out = run('check_gate_reachability.py',
                        ['--results', str(res), '--profile', str(report.profile)])
        if code == -1:
            review['checker_missing'] = out
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_gate_reachability 负对照未过——其检查结论不作数')
        elif code != 0:
            hit = [l.strip() for l in out.splitlines() if '够不着' in l and 'min_' in l]
            report.warn('eval.gate-above-judge-ceiling',
                           '**有绝对分门高于两席的实测可达上限**——'
                           '产物再好也过不去，故「未过」不构成「产物不够好」的证据；'
                           '**不要因此自行放宽阈值，这是人的决定**。'
                           + ('　' + '；'.join(hit) if hit else ''))
        else:
            review['gate_reachability'] = '✓ 各绝对分门都在两席实测可达范围内'

    # ── 只列不判：写进 warnings，不拦 ────────────────────────────────
    for script, argv, key in (
            ('check_absence_claims.py', ['--workspace', str(target)], 'absence_claims'),
            ('check_redundancy.py', ['--workspace', str(target)], 'redundancy'),
            ('check_schema_drift.py', ['--workspace', str(target),
                                       '--expect', 'cases.jsonl:holdout_source_ids'],
             'schema_drift'),
            ('check_claim_anchors.py', ['--workspace', str(target)], 'claim_anchors')):
        rc, out = run(script, argv)
        if rc == -1:
            continue
        tail = [l.strip() for l in out.splitlines()
                if l.strip().startswith(('✓', '⚠', '✗', '合计', 'claim 标记'))]
        if tail:
            review[key] = tail[-1][:160]

    if review:
        report.metrics['content_review'] = review


    # ★★★★ 2026-08-11：**这一段原本关在 `--cache` 分支里，而它自己写着「不需要 cache」。**
    #   于是不带 `--cache` 跑门时，引文坐标**一次都没被查过**——
    #   Shewhart #165 与 Thomson 的合成门都报 0 错，而独立跑判据分别是 0 缺 / 15 缺。
    #   ★ 抓到它的是**反向对照**：我接完 `--products` 之后去跑一个已知 19/19 全缺的人物，
    #     它却报 0 错。**若只跑正例（Shewhart 0 缺、门也 0 错），会以为接上了。**
    #   [[a-checker-nothing-calls-is-not-a-checker]]／[[counter-example-red-can-be-red-by-coincidence]]
    # ── v0.0.0.39：引文坐标（**不需要 cache**，判的是文本自身可不可回查）────
    #   `check_quote_integrity` 管「这句在不在语料里」，管不了另一半：
    #   **读者拿什么去回查。** 一句真引文若不写清出自哪篇哪年哪页，
    #   读者只能选择信或不信——而这套产物的全部主张正是「你可以不信我，去核」。
    #   Lister #108 席 E 在四处 note 与 _overall 里点了同一件事，判据数出范围：
    #   17 条长引文，**9 条同段内无任何坐标线索**（评委的印象是「无一处」，实为 8 条有）。
    loc_argv: list[str] = []
    if claims.exists():
        loc_argv += ['--claims', str(claims)]
    payload = target / 'evals/judge_payload.v1.json'
    if payload.exists():
        loc_argv += ['--answers', str(payload)]
    #   ★★★★ 2026-08-11（Shewhart #165）：**产物此前从来没被传进来。**
    #     上面两行只喂 `--claims` 与盲判载荷，于是**十份 Markdown 产物——
    #     用户真正读的那一份——一次都没被扫过引文坐标**。
    #     缺陷因此坐在产物里，直到有人生成盲判载荷才冒出来，
    #     那时它看着还像「答题方没写坐标」：**根因被移了位。**
    #   ★ 全库实测 424 条 ≥30 字符的逐字引文，**176 条缺坐标（41.5%）**，
    #     17 个工作区只有 4 个干净；**Adams 27/27、Thomson 19/19 全缺，
    #     而这两人都已经判过分、delta 已入账**。
    #   [[gates-cover-json-not-the-prose-users-read]]
    _prods = [str(target / rel) for rel in RENDER_FILES if (target / rel).is_file()]
    if _prods:
        loc_argv += ['--products', *_prods]
    if not loc_argv:
        review['quote_locator'] = '断言、答案、产物都取不到，**引文坐标未核（不是通过）**'
    else:
        code, out = run('check_quote_locator.py', loc_argv)
        if code == -1:
            review['checker_missing'] = out
        elif code == 3:
            review['quote_locator'] = '一条长逐字引文都没扫到——**本次未检查（不是通过）**'
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_quote_locator 负对照未过——其检查结论不作数')
        elif code != 0:
            n = next((l for l in out.splitlines() if l.startswith('长逐字引文')), '')
            report.error('content.quote-no-locator',
                         f'有逐字引文无从回查：同段内既无年份也无卷页刊名。{n}')
        else:
            review['quote_locator'] = '✓ 每条长引文同段内都能找到坐标线索'

def run_authorship_gate(report, target: Path, meta: dict[str, Any],
                        sources: list[dict[str, Any]]) -> None:
    """语料层归属门（v0.0.0.10 新增）——**在 research 阶段就拦**。

    ## 它补的是「假设层」缺口，不是实现层缺口

    v0.0.0.8 的七件内容检查器**共享一个从未言明的假设：语料里的话就是他的话**。
    Steinhardt #98 证明这个假设可以整体失效——抓源子代理把基金会季刊按页切片、
    一律冠上人物前缀，十份里九份是别人写的，灌库命令再带 `--author "<人物名>"`，
    两步就把别人的文章洗成了他的话。`check_quote_integrity` 甚至会给出肯定结论
    （「这句在语料里」——它确实在，只是不是他说的）。

    **把七件检查器各自加强都补不上**，因为它们都在下游。

    ## 门开在哪个断言上

    只查**账本自己声称的东西**：`tier == 'P1'` 且 `author` 指向本人物的源。
    ——账本说「这是他写的」，门就要求它拿出证据。没声称作者的源不在射程内
    （测试夹具、二手材料都属此类），因此本门对既有产物零误伤。

    **这也是它唯一的射程边界**：`tier=P1` 但 `author` 留空的源，本门不判，
    只在 metrics 里报数。这条缺口是有意留的——堵它会把所有历史产物一起拦下，
    而那违反「不因为过不了门而卡住流程」。缺口大小随时可见，不会被误当成通过。

    ## 为什么在 research 而不是 release

    归属错了，后面**六路研究、断言、文档、用例全部要重做**。
    v0.0.0.9 把它放在收口手动跑，等于把这笔返工的可能性一直背到最后。
    现在它跟着 research 门跑，**在写第一个字之前**给出答案。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_authorship.py'
    info: dict[str, Any] = {}
    name = str(meta.get('name') or '').strip()

    if not script.exists():
        report.metrics['authorship'] = {'状态': 'check_authorship.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_authorship', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['authorship'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return

    # ★ 负对照不过 → 它的「全绿」不构成任何证据。与 v0.0.0.8 三件硬门同一条纪律。
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        selftest_rc = module.self_test()
    if selftest_rc != 0:
        report.error('content.selftest-failed',
                     'check_authorship.py 负对照未过——其检查结论不作数')
        return

    try:
        patterns = module.build_patterns(name)
        # ★★★ v0.0.0.136：**已知同名注入**。`A-byline-ocr` 用编辑距离容错 OCR 打坏的名字，
        #   而 `Thomson` 与 `Thompson` 的距离只有 1——不声明同名就会把别人的东西收进来。
        #   Thomson #129 探测实测：1887 年索引里挨着他名字的 27 个专利号，**16 个是别人的**
        #   （十二个姓 Thompson，另有 Nash／Smith／Jones／Thoms）。
        #   ★ 取自 `meta.json` 的 `known_namesakes`（没有就是空，**空不等于安全，只等于没声明**）。
        patterns["namesakes"] = tuple(meta.get("known_namesakes") or ())
        #   ★★ 中名首字母：**同姓的同名者，姓的编辑距离一个也挡不住**。
        #   Coffin #130 实测（护栏加之前）：`Charles A. Coffin.`（GE 首任总裁）被当成
        #   `Charles L. Coffin`（电弧焊发明人）的署名**放行**，而他自己惯用的
        #   `C. L. Coffin.` 反而**拦下**——两个方向同时错。
        #   取自 `meta.json` 的 `middle_initial`；**没声明就退回 v0.0.0.136 的射程**。
        patterns["own_mid"] = str(meta.get("middle_initial") or "").strip().lower()[:1]
        # ★ 单作者站点报头（如 seths.blog 的 `| Seth's Blog`）作为第四类归属证据。
        #   声明放在 meta.json 的 `single_author_masthead`，**不是命令行开关**——
        #   它必须随工作区走、可审计、且事后能被复核。
        #   检查器自己会拒绝不含人物名的报头（多作者刊物的形态）。
        masthead = str(meta.get('single_author_masthead') or '').strip()
        if masthead and hasattr(module, 'attach_masthead'):
            patterns = module.attach_masthead(patterns, masthead)
        elif masthead:
            report.warn('research.masthead-unsupported',
                           'meta 声明了 single_author_masthead，但检查器版本不支持——该声明被忽略')
    except ValueError as exc:
        report.metrics['authorship'] = {
            '状态': f'判据生成失败，**未核验**：{exc}'}
        return

    claimed, proven, unverified, suspect, unproven, no_author = [], [], [], [], [], 0
    for record in sources:
        if record.get('tier') != 'P1':
            continue
        author = str(record.get('author') or '').strip()
        if not author:
            no_author += 1
            continue
        if not patterns['SURNAME'].search(author):
            continue                       # 账本明说是别人写的，本门不管归属
        claimed.append(record)
        rel = record.get('local_path')
        path = (target / rel) if rel else None
        if not path or not path.exists():
            unverified.append(f'{record.get("source_id")} ({rel or "无 local_path"})')
            continue
        try:
            ok, code, _, counter = module.check(path, patterns)
        except OSError as exc:
            unverified.append(f'{record.get("source_id")} (读取失败 {exc})')
            continue
        label = f'{record.get("source_id")} {path.name}'
        if ok and counter:
            suspect.append(f'{label} [{code}] 另有他人署名：{counter[0][:60]}')
        elif ok:
            proven.append(label)
        else:
            unproven.append(f'{label}｜文中他人署名：{counter[0][:60] if counter else "无"}')

    info['P1 声称为本人所著'] = len(claimed)
    info['已证实归属'] = len(proven)
    if no_author:
        info['P1 未声称作者（本门射程外）'] = no_author
    if unverified:
        info['**未核验**（无落盘原文，不是通过）'] = unverified[:8]
    if suspect:
        info['存疑（有正面证据但另有他人署名）'] = suspect[:8]
    report.metrics['authorship'] = info

    # ★ v0.0.0.27：**historical + 已声明 attribution_basis 时降为报告，不硬拦。**
    #
    #   两道门原本互相矛盾：`check_attribution_basis` 说「印刷时代的署名证据对你不适用，
    #   请另行写明依据」，写明了；本门转头仍要求 `By <名>`——**而那是它永远拿不出的东西**。
    #   Galen #101 实测：55 部希腊文校勘本正文，A-* 五种证据一条也不可能有，
    #   `research.authorship-unproven` 报了 55 次。
    #
    #   **这不是放宽。** historical 路的要求更硬：要一个具名外部权威（他本人的真作目录 +
    #   Fichtner 目录）、要可查证出处、要逐条列出伪托篇目并写明裁定政策。
    #   **换的是证据种类，不是证据强度。**
    hist = (str(meta.get('subject_origin') or '') == 'historical'
            and isinstance(meta.get('attribution_basis'), dict))
    if hist and unproven:
        info['**historical 路**：A-* 五种证据结构上不存在，归属改由 attribution_basis 认定'] = (
            f'{len(unproven)} 条无 A-* 证据，**已按已声明的归属依据放行**'
            f'（依据本身由 check_attribution_basis 硬拦）')
        report.metrics['authorship'] = info
        return
    for item in unproven:
        report.error('research.authorship-unproven',
                     f'{item} —— 账本声称本人所著，但文中查无归属证据'
                     f'（署名／编者注／逐字稿轮次三者皆无）')


def run_fact_density(report, target: Path, sources: list[dict[str, Any]]) -> None:
    """事实密度门（v0.0.0.28 新增，**只报不拦**）。

    Galen #101 被拒发之后倒推出来的：59 条可用源、244 万词一手语料，
    `fact` 类断言只有 **5** 条。第 2 轮改答案把真 delta 从 −0.1944 拉到 −0.1259 就到顶——
    **天花板在断言层，不在答案层。**

    **只报不拦**：已入库 100 人普遍是 5 条上下，硬拦会把整个名册一起拦下
    （与 `NO-SELFTEST`、新鲜度门同一条纪律）。数字大到无法忽略，但不替执行者做发布决定。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_fact_density.py'
    if not script.exists():
        report.metrics['fact_density'] = {'状态': 'check_fact_density.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_factdens', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['fact_density'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.error('content.selftest-failed',
                         'check_fact_density.py 负对照未过——其检查结论不作数')
            return
    claims = read_jsonl(target / 'evidence/claims.jsonl')
    usable = [r for r in sources if r.get('split') == 'train' and r.get('tier') != 'U']
    problems, info = module.evaluate(claims, len(usable))
    if problems:
        info['**未达**'] = problems
    report.metrics['fact_density'] = info


def run_case_self_sufficiency(report, cases: list[dict[str, Any]]) -> None:
    """题面自足门（v0.0.0.48 新增，**只报不拦**）——题面里的指代，在题面里找得到吗？

    Osler #110 的 `wo-capability-calibration-01`：「你私下里是怎么想**这件事**的？」
    ——「这件事」指哪件事，题面里没有。两席**各自独立**点出来，
    而它已经被问了三轮、两侧作答四十八次，**没有一次答在点上，因为根本没有点。**

    这种题白占一个套组名额：`capability-calibration` 只有 2 题，废掉一题就是废掉一半。

    **只报不拦**：已入库 100 人的用例集从未按这条扫过，硬拦会把发布一起拦下。
    但出题阶段（`synthesis`）看到它就该改——**那时候改还来得及，判分之后就晚了。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_case_self_sufficiency.py'
    if not script.exists():
        report.metrics['case_self_sufficiency'] = {
            '状态': 'check_case_self_sufficiency.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_selfsuff', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['case_self_sufficiency'] = {
            '状态': f'检查器加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.error('content.selftest-failed',
                         'check_case_self_sufficiency.py 负对照未过——其检查结论不作数')
            return
    if not cases:
        report.metrics['case_self_sufficiency'] = {
            '状态': '**没有用例可扫**——这不是通过'}
        return
    bad = module.run(cases)
    info: dict[str, Any] = {'用例数': len(cases), '断链的题': len(bad)}
    if bad:
        info['**逐条**'] = [
            f'{cid}：{"、".join(w for w, _ in hits)}　题面「{prompt}」'
            for cid, prompt, hits in bad]
        report.warn('cases.dangling-reference',
                    f'**{len(bad)} 道题的指代在题面里找不到先行词**——'
                    '这种题两侧都答不到点上，**白占一个套组名额**。'
                    '出题阶段改还来得及。')
    report.metrics['case_self_sufficiency'] = info


def run_measurement_claims(report, target: Path) -> None:
    """实测声明门（v0.0.0.63 新增，**只报不拦**）——说「我量过」的地方有没有数？

    ## 触发实例

    席 E 在**八个人物**身上反复扣同一处分。原话（Fleming #111 第 3 轮 q-30）：

    > 「因为我量过，不是因为不喜欢」这句最承重，**全文却没有任何测得的数**。

    评委每人只能点出一两处（他们要在 32 题里通读），
    **判据把范围数出来了**：21 份载荷、43 处实测声明、**17 处光说不给数**，
    分布在 Koch #107、Lister #108、Virchow #109、Fleming #111 四个人身上。
    而席 E 只在其中一处说过话——**它三轮都在，他第 3 轮才提。**

    这是第四次把席位批评落成判据。

    ## ★ 弃权不是缺陷

    Fleming 有一句「那两篇的数值**我没逐个核过，不核就不报数**」，
    席 E 专门表扬了它。判据若把这类也报出来，
    作者为了让门变绿会**去掉弃权、或者随便补个数**——**把产物推向不诚实。**
    检查器里 `ABSTAIN` 单独成立并单独计数，自测反向对照 ④⑤⑥ 守这一条。

    ## 只报不拦

    已入库 100 人的答案层从未按这条扫过，硬拦会把发布一起拦下。
    但**合成阶段看到它就该改**——那时候改还来得及。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_measurement_claims.py'
    if not script.exists():
        report.metrics['measurement_claims'] = {
            '状态': 'check_measurement_claims.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_measure', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['measurement_claims'] = {
            '状态': f'检查器加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['measurement_claims'] = {
                '状态': '**负对照未过，其结论不作数**'}
            return

    acc = {'total': 0, 'ok': 0, 'bad': [], 'abstain': 0}
    scanned = 0

    # ★ **合成阶段还没有载荷，但断言层已经有了。**
    #   第一版只读 `evals/judge_payload.v1.json`，于是接在 synthesis 上等于没接——
    #   那时那份文件根本不存在，判据只会说「没有载荷可扫」。
    #   而这道判据的全部意义就是「**合成阶段看到就该改，判分之后就晚了**」。
    #   （在 Fleming 身上试跑看不出来：他早已跑完发布，载荷一直在。
    #   **拿一个已完成的人物去验「早期阶段的门」，验不出这类缺陷。**）
    for rel in ('evidence/claims.jsonl', 'claims.jsonl'):
        p = target / rel
        if not p.is_file():
            continue
        for line in p.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            module.scan(f'断言/{r.get("claim_id", "?")}', r.get('claim', ''), acc)
        scanned += 1
        break

    for rel in ('evals/judge_payload.v1.json', 'evals/baseline.v1.json'):
        p = target / rel
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except Exception:                                        # noqa: BLE001
            continue
        if isinstance(data, list):
            for row in data:
                for side in ('A', 'B'):
                    if side in row:
                        module.scan(f'{row.get("case_id", "?")}/{side}', row[side], acc)
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    module.scan(f'{p.name}/{key}', value, acc)
        scanned += 1

    info: dict[str, Any] = {
        '已扫单元': scanned,
        '实测声明': acc['total'],
        '同段带数': acc['ok'],
        '**光说不给数**': len(acc['bad']),
        '诚实弃权（不计问题）': acc['abstain'],
    }
    if not scanned:
        info['状态'] = '**没有可扫的单元（断言层与载荷都不在）——这不是通过**'
    elif not acc['total'] and not acc['abstain']:
        # 检查器自己的口径里有这一条，接线时漏了：**扫到 0 处不等于通过。**
        info['状态'] = ('**一处实测声明都没扫到——本次什么也没检查，不构成通过。**'
                        '合成阶段常态如此（断言层通常不写「我量过」），'
                        '**但发布阶段若仍是 0，要去看是不是扫错了单元。**')
    elif acc['bad']:
        info['**逐条**'] = [f'{uid}　「{kw}」：{snip}' for uid, kw, snip in acc['bad'][:12]]
        info['口径'] = ('借了实测的权威却没交出实测的内容。'
                        '**两条出路：把数补上，或改成弃权式**——'
                        '弃权不会被报出，它是诚实的。')
    report.metrics['measurement_claims'] = info


def run_sole_authorship(report, target: Path) -> None:
    """独揽门（v0.0.0.65 新增，**只写 metrics，连 warning 都不发**）。

    ## 为什么连 warning 都不发

    这道判据第一次跑真数据时**精确率 1/5**（Virchow 三处「合著形容母卷」、
    Fleming 一处「引了这条源 ≠ 这段在讲它」）。修完在三个人物上是 5/5，
    但**三个人物不足以把它放进会阻塞的通道**。

    接进来是为了**攒样本**：每个人物自动跑一遍，
    等它在更多人身上稳住了再谈提级。
    （`--strict` 下任何 warning 都会让门失败，所以只能进 `metrics`。）
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_sole_authorship_overreach.py'
    if not script.exists():
        report.metrics['sole_authorship'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_sole', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['sole_authorship'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['sole_authorship'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    ledger = target / 'evidence' / 'source-ledger.jsonl'
    if not ledger.is_file():
        report.metrics['sole_authorship'] = {'状态': '**账本不在，未核验**'}
        return
    shared = module.shared_sources(ledger)
    if not shared:
        report.metrics['sole_authorship'] = {
            '合著／集体署名的源': 0,
            '状态': '**账本里一条合著／集体署名的源都没有——本次什么也没查，不构成通过。**'
                    '十一个人物里只有三个的账本记了这一层，'
                    '**多半是抓源阶段没记，不是真的没有合著。**'}
        return

    idx = module.title_index(ledger, shared)
    acc = {'total': 0, 'ok': 0, 'bad': []}
    claims = target / 'evidence' / 'claims.jsonl'
    if claims.is_file():
        for line in claims.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            cited = (set(r.get('source_ids') or [])
                     | set(module.SRCID.findall(json.dumps(r, ensure_ascii=False))))
            for para in module.paragraphs(r.get('claim', '')):
                module.scan(f'断言/{r.get("claim_id", "?")}', para,
                            cited & module.cited_by_title(para, idx), shared, acc)
    for rel in ('evals/judge_payload.v1.json', 'evals/baseline.v1.json'):
        p = target / rel
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except Exception:                                        # noqa: BLE001
            continue
        items = (data.items() if isinstance(data, dict) else
                 [(f'{r.get("case_id", "?")}/{s}', r[s]) for r in data
                  for s in ('A', 'B') if s in r])
        for uid, text in items:
            if not isinstance(text, str):
                continue
            for para in module.paragraphs(text):
                module.scan(f'{p.name}/{uid}', para,
                            module.cited_by_title(para, idx), shared, acc)

    info: dict[str, Any] = {
        '合著／集体署名的源': len(shared),
        '引用它们又用第一人称的段落': acc['total'],
        '已划界': acc['ok'],
        '**独揽**': len(acc['bad']),
    }
    if acc['bad']:
        info['**逐条**'] = [f'{u}　@{s}（账本记「{m}」）「{k}」：{sn}'
                            for u, s, m, k, sn in acc['bad'][:10]]
        info['口径'] = ('**修法是划界不是删第一人称**——写「我与 X 合著」'
                        '「我那一部分是……」即可，本判据不报这类；'
                        '否定式的划界（「我不把它称作我的报告」）也不报。')
    report.metrics['sole_authorship'] = info


def run_suite_single_drag(report, target: Path, thresholds: dict) -> None:
    """套组诊断（v0.0.0.69，**只写 metrics，不改任何分数**）。

    每个套组只有 2 题——**一道答坏的题，套组均分立刻掉一半的量**，
    而套组均分会把它摊薄成「整组偏弱」，让人去改整组。**修法完全不同。**

    实测：`boundary` 有三人是**被单独一道题拖住**
    （Nightingale `ni-boundary-01` 0.705、Osler `wo-boundary-02` 0.815、
    Jenner `ej-boundary-02` 0.820）；
    而 `fact-preservation` 在十个人身上**无一例外是「整组偏弱」**——
    **不是一道坏答案沉了它，是整组稳定坐在 0.88–0.90。**

    **它不改任何分数。** 「去掉最低那道能过」是关于**修哪里**的话，
    不是关于**该不该过**的话。**门还是门。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_suite_single_drag.py'
    if not script.exists():
        report.metrics['suite_single_drag'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    results = target / 'evals' / 'results.jsonl'
    if not results.is_file():
        report.metrics['suite_single_drag'] = {'状态': '**没有判分记录，未核验**'}
        return
    spec = importlib.util.spec_from_file_location('_pd_drag', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['suite_single_drag'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['suite_single_drag'] = {'状态': '**负对照未过，其结论不作数**'}
            return
    try:
        rows = [json.loads(l) for l in results.read_text(encoding='utf-8').splitlines()
                if l.strip()]
        thr = {'boundary': float(thresholds.get('min_boundary_score', 0.85)),
               'fact-preservation': float(thresholds.get('min_fact_preservation_score', 0.93))}
        by = module.suite_cases(rows)
        diag = module.diagnose(by, thr)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['suite_single_drag'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return

    single, whole = [], []
    for suite, mean, t0, worst, wval, rmean, can in diag:
        if worst is None:
            continue
        (single if can else whole).append(
            f'{suite}　均分 {mean:.4f} < {t0:.2f}　'
            + (f'**被 {worst}（{wval:.3f}）一道拖住——去掉它 {rmean:.4f} ≥ {t0:.2f}**'
               if can else f'整组偏弱（去掉最低仍 {rmean:.4f}）'))
    info: dict[str, Any] = {'未过阈值的套组': len(diag)}
    if single:
        info['**被单独一道题拖住**'] = single
    if whole:
        info['整组偏弱'] = whole
    if diag and not single and not whole:
        info['状态'] = '未过的套组都只有 1 题，**没有「其余」可比，不诊断**'
    if not diag:
        info['状态'] = '有阈值的套组都过了——无需诊断'
    info['口径'] = ('这只是「修哪里」，不是「该不该过」。**门还是门。**'
                    '另：**「知道该改哪一道」与「知道该怎么改」是两件事**——'
                    'Nightingale #112 那一道改完从 0.760 掉到 0.705。')
    report.metrics['suite_single_drag'] = info


def run_rights_basis(report, target: Path) -> None:
    """公有领域的依据在不在（v0.0.0.79，**只写 metrics**）。

    #116 Watson 探测撞到一条**已发生、可复现**的误判：
    Unpaywall 对 `10.1111/j.1365-2702.2005.01256.x` 返回 `license = "public-domain"`，
    而同一 DOI 的 Crossref 写的是 Wiley 标准条款——**作者 1940 年生且在世**。
    **照抄聚合器的 `license` 字段 = 把受保护作品当公有领域入库。**

    十一个账本实测：**872 条声称公有领域，0 条依据取自聚合器**（本件是预防），
    **230 条有可核依据、642 条只有结论没有依据**。

    **它不说那 642 条判断错了**——八位历史人物的结论都站得住。
    但公有领域**随时间与法域变化**：Fleming 卒于 1955，
    「终身+70」法域里是 **2025 年**才进入公有领域的——**同一句话 2024 年写就是错的**。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_rights_basis.py'
    if not script.exists():
        report.metrics['rights_basis'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_rightsbasis', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['rights_basis'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['rights_basis'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    path = target / 'evidence' / 'source-ledger.jsonl'
    if not path.is_file():
        report.metrics['rights_basis'] = {'状态': '找不到 source-ledger.jsonl，**未核验**（不是通过）'}
        return
    records = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()
               if line.strip()]
    if not records:
        report.metrics['rights_basis'] = {'状态': '**账本是空的——未核验（不是通过）**'}
        return

    agg, nb, ok, npd = module.audit(records)
    entry = {
        '源条数': len(records),
        '声称公有领域': len(agg) + len(nb) + len(ok),
        '不声称（不判）': len(npd),
        '有据可查': len(ok),
        '有结论无依据': len(nb),
        '依据取自聚合器': len(agg),
    }
    if agg:
        entry['**依据不作数**'] = [f'{sid}：{txt}' for sid, txt in agg[:5]]
    report.metrics['rights_basis'] = entry


def run_pd_grounds(report, target: Path) -> None:
    """「它是公有领域」凭哪一条？（v0.0.0.85，**只写 metrics**）

    #119 DeBakey 的探测暴露了一处我自己的混淆：三卷 GPO 政府出版物**确实是 PD**，
    但依据是「1978 年前出版、无版权标记」（1909 年法），**不是 §105 联邦职务作品**
    ——作者脚注实录 `Formerly Colonel, MC, AUS`，写作时他已是平民教授。

    两者结论相同、**射程完全不同**：§105 可外推到他同期的其他作品；
    1909 那条只判这一份印本，一份一份地判。
    把后者当成前者，就会得出「他有 §105 的口子、可按 deep 排期」——**实际口径是 0**。

    真数据回归：把那三卷按天真直觉标成 §105，本判据**三卷全部抓住**，
    「§105 且本人署名」从 3 条纠正为 **0 条**。
    同一跑还抓出探测报告自己的分档错误：两份 28 人集体署名的委员会报告标了 P2（一手）。

    **缺依据表时明说「未核」，不写依据不算通过。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_pd_grounds.py'
    if not script.exists():
        report.metrics['pd_grounds'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_grounds', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['pd_grounds'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    f = target / 'references/research/_pd_grounds.json'
    if not f.is_file():
        report.metrics['pd_grounds'] = {'状态': (
            '**本人物未提供 `references/research/_pd_grounds.json`——未核，不是通过。**'
            '「它是公有领域」须写明凭哪一条（§105 ／ 1909 年法无标记 ／ '
            '1929 年前出版 ／ 国会记录）并附证据')}
        return
    try:
        claims = json.loads(f.read_text(encoding='utf-8'))
        problems = module.check(claims)
        info = module.summarize(claims)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['pd_grounds'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    ids = set()                           # ★ 分母：按标识符比集合，不比份数
    for sub in ('references/sources', 'references/holdout'):
        d = target / sub
        if d.is_dir():
            for one in d.iterdir():
                if one.is_dir():
                    ids |= {f.name.split('.')[0] for f in one.glob('*.normalized.txt')}
    if ids:
        info.update(module.coverage(claims, ids))
    else:
        info['覆盖率'] = ('**一个来源标识符都数不到，分母未知**——'
                       '不许把「N 条全合格」读成「每一份来源都有依据」')
    info['形式不完整的'] = problems[:8] or '无（★ 这只说明主张形式完整，不是法律结论）'
    report.metrics['pd_grounds'] = info


def run_verbatim_pointer(report, target: Path) -> None:
    """问原话，答「你自己去查」（v0.0.0.87，**只写 metrics**；这是回归护栏）。

    ★ 立这道判据时我把评语读反了：以为那几条说的是候选，**跑真数据才知道是基线**。
    同一批题面 5 人配对实测，10 道「问原话/出处」的题——
    **候选 0/10（0%）、基线 3/10（30%）**。
    **「让人自己去查」是基线的失败形态，候选恰恰是给引文与卷页的那一侧。**

    所以它守的是产品**已经有**的一项优势：哪天候选开始把原话推给读者，这里会红。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_asked_verbatim_got_pointer.py'
    if not script.exists():
        report.metrics['verbatim_pointer'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_vptr', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['verbatim_pointer'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    cf, pf = target / 'evals/cases.jsonl', target / 'evals/judge_payload.v1.json'
    if not (cf.is_file() and pf.is_file()):
        report.metrics['verbatim_pointer'] = {
            '状态': 'cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）'}
        return
    try:
        cases = [json.loads(l) for l in cf.read_text(encoding='utf-8').splitlines() if l.strip()]
        answers = json.loads(pf.read_text(encoding='utf-8'))
        if isinstance(answers, list):
            answers = {a.get('case_id'): a for a in answers if isinstance(a, dict)}
        problems, info = module.evaluate(cases, answers)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['verbatim_pointer'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    info['只给指路的'] = problems[:6] or '无'
    report.metrics['verbatim_pointer'] = info


def run_unwired_three(report, target: Path) -> None:
    """把三件**从来没有被任何代码调用过**的判据接上（v0.0.0.91，**只写 metrics**）。

    起因：`check_checkers` 之外自查了一遍「谁调用谁」——
    **51 件判据里 7 件在生产代码里找不到调用方**。
    三处所谓「被调用」实为**注释里的提及**（`check_contract_drift` 讲历史、
    `check_scan_reach` 讲射程边界、`check_extreme_result_is_suspect` 讲归属）。

    **这是「第 9 次」那个坑长回来了**：判据存在、自测全绿、文档里反复引用，
    而它从来没有跑过。本函数接三件（其余四件另有归属，见 CHANGELOG）：

    - `check_activation_yield`   —— 有效激活率（Livermore 真 delta −0.1219 的成因之一）
    - `check_anchor_coherence`   —— 断言改了，渲染它的段落跟着改了吗
    - `check_quoted_arithmetic`  —— 摆出一串分项加一个合计，加得平吗

    **全部 metrics-only**：接线不改动任何已判过的人的门。
    """
    here = Path(__file__).resolve().parent
    pf = target / 'evals/judge_payload.v1.json'
    cf = target / 'evidence/claims.jsonl'

    def call(script, argv, key, need=()):
        path = here / script
        if not path.exists():
            report.metrics[key] = {'状态': f'{script} 未安装，**未核验**（不是通过）'}
            return
        missing = [str(x) for x in need if not x.is_file()]
        if missing:
            report.metrics[key] = {'状态': f'输入不在（{missing[0]}），**未核验**（不是通过）'}
            return
        proc = subprocess.run([sys.executable, str(path), *argv],
                              capture_output=True, text=True)
        out = ((proc.stdout or '') + (proc.stderr or '')).strip()
        report.metrics[key] = {'退出码': proc.returncode,
                               '输出': out.splitlines()[-6:] or ['（无输出）']}

    # ★ 它收**位置参数**不是 --answers；第一版写成 --answers，接线第一跑退出码 2。
    #   **这正是「接了线不等于跑通了」——只看代码看不出来。**
    call('check_activation_yield.py', [str(pf)], 'activation_yield', (pf,))
    call('check_anchor_coherence.py', ['--workspace', str(target)], 'anchor_coherence')
    call('check_quoted_arithmetic.py', ['--answers', str(pf), '--claims', str(cf)],
         'quoted_arithmetic', (pf, cf))
    # ★ 第 4 件：交付里带齐分母了吗（v0.0.0.92）。
    #   实测起因：想从产物侧回算「事实密度债」，而 `usable_train` 从没被写进交付产物，
    #   source-coverage.json 只有 sources_total —— 于是那一整类债**只能给上界**。
    cov = target / 'audit/source-coverage.json'
    call('check_delivery_carries_denominators.py', [str(cov)], 'delivery_denominators', (cov,))


def run_answer_constraints(report, target: Path) -> None:
    """题面写死的约束，答案接住了吗（v0.0.0.83，**只写 metrics**）。

    Barton #117 第 3 轮两席点名的候选缺陷里**三处不是知识缺口**：
    题目要「用这个称号写自我介绍」答成了否认＋履历、题面已写「不用管史实」仍拒写、
    题设「三天后才能进场」而头一条仍讲「能早到一刻就早到一刻」。
    **当时没有任何判据在看这件事**——`check_case_self_sufficiency` 管题面自不自足，
    不管答案有没有照题面答。

    **只检 `cases.jsonl` 里显式声明的 `constraints`**：题面里的自然语言约束提取不了
    （拿「题面数字答案碰没碰」做过探针，32 题只覆盖 9 题且抓不到动因用例——
    题面写的是「五万」，汉字数词）。
    **「0 处未过」不等于「全部接住了」，要连「声明了几条」一起读。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_answer_honors_constraints.py'
    if not script.exists():
        report.metrics['answer_constraints'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_answercons', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['answer_constraints'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    cf = target / 'evals/cases.jsonl'
    pf = target / 'evals/judge_payload.v1.json'
    if not (cf.is_file() and pf.is_file()):
        report.metrics['answer_constraints'] = {
            '状态': 'cases.jsonl 或 judge_payload 不在，**未核验**（不是通过）'}
        return
    try:
        cases = [json.loads(l) for l in cf.read_text(encoding='utf-8').splitlines() if l.strip()]
        answers = json.loads(pf.read_text(encoding='utf-8'))
        problems, info = module.evaluate(cases, answers)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['answer_constraints'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    info['未接住的'] = problems[:8]
    report.metrics['answer_constraints'] = info


def run_claim_source_independence(report, target: Path) -> None:
    """一条断言引的两份源，是不是同一部作品的两个见证（v0.0.0.82，**只写 metrics**）。

    六类断言各要求 ≥2 个 `source_ids`，那条要求想要的是**互相独立的两处证据**。
    **而此前没有任何判据在问这两份源是不是同一部作品。**

    #118 Blackwell 实测：LoC 33 份讲稿手稿里 **18 份是印本的草稿**（重叠 51–90%）。
    引手稿＋引它的印本，字面两个 id，实质一处证据。

    落成后九人回扫，**五人有塌缩**：
    Koch **17/17**（手工发现过的那件，现在机器抓得住）、Lister **17/17**（新发现）、
    Osler 5/17、Jenner 3/16、Nightingale 2/12；Barton 0/12、Fleming 0/15、Godin 0/20 干净。

    **只写 metrics 不拦**：已入库的人未回扫过，硬拦会把整个名册一起拦下
    （与 `NO-SELFTEST`、新鲜度门、引文层门同一条纪律）。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_claim_source_independence.py'
    if not script.exists():
        report.metrics['claim_source_independence'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_claimindep', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['claim_source_independence'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    ev = target / 'evidence'
    cf, lf = ev / 'claims.jsonl', ev / 'source-ledger.jsonl'
    if not (cf.is_file() and lf.is_file()):
        report.metrics['claim_source_independence'] = {
            '状态': 'claims.jsonl 或 source-ledger.jsonl 不在，**未核验**（不是通过）'}
        return
    try:
        claims = [json.loads(l) for l in cf.read_text(encoding='utf-8').splitlines() if l.strip()]
        texts = {}
        for line in lf.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            p = target / (r.get('local_path') or '')
            if r.get('source_id') and p.is_file():
                texts[r['source_id']] = p.read_text(encoding='utf-8', errors='replace')
        if not claims or not texts:
            report.metrics['claim_source_independence'] = {
                '状态': '断言或正文为空，**未核验**（不是通过）'}
            return
        problems, info = module.evaluate(claims, module.group_works(texts))
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['claim_source_independence'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    info['塌缩的断言'] = [p.split('（')[0].strip('`') for p in problems][:12]
    report.metrics['claim_source_independence'] = info


def run_corpus_feasibility(report, target: Path) -> None:
    """**手上这批材料，还有没有可能走完全程？**（v0.0.0.-新增，Shewhart #165 撞出）

    ★★★ 本文件自己的两条规则合起来是矛盾的，而没有任何地方写着：

    - L132：`len(usable) >= min_sources`，`usable` **只含 `split == 'train'`**；
    - L149：synthesis/release 阶段**没有 holdout 就报错**。

    → holdout 那一份必须从总数里扣，**所以真实下限是 `min_sources + 1`**。
    quick 档文档写 8，真实是 9。Shewhart #165 一手正好 8 份：
    **研究门绿、合成门必错，且怎么改文字都过不去**。

    ★★ 代价不是多跑一次门：研究门放行之后，人会去写六道研究、几十条断言、
    十份产物、一整套用例，**全部做完之后**才撞见 `source.no-holdout`。
    本判据把这一撞提前到抓源刚结束的时候。

    判据穷举「扣哪一份当 holdout」——★ 只试一种选法会误判：
    某一道可能只有 1 份材料撑着，恰好扣掉它道数就掉了，换一份扣就没事。

    全库实测（2026-08-10，23 个有 meta 的工作区）：**17 绿 / 6 红**，
    红的 6 个里 5 个是**已知受阻**的人（Benardos/Koch/Liebig/Martens/Semmelweis），
    **新增只有 Shewhart 一个**；所有已判分出货的人全绿——正对照成立。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_corpus_feasibility.py'
    if not script.exists():
        report.metrics['corpus_feasibility'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_feas', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        problems, info = module.evaluate(target, report.profile)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['corpus_feasibility'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    report.metrics['corpus_feasibility'] = info
    if info.get('结论') == 'impossible-without-more-material':
        report.error(
            'corpus.structurally-infeasible',
            f"**这批材料在结构上走不完全程**：可用 {info.get('可用材料总数')} 份 < "
            f"**真实下限 {info.get('★ 真实下限')}**"
            f"（{info.get('min_sources')} 份 train + 至少 1 份 holdout，"
            f"因为 `min_sources` 只数 train 而合成阶段强制要有 holdout）"
            f" —— **至少还要 {info.get('还差')} 份材料**；"
            f"**再写多少文字都过不去**，现在停手比做完十份产物再撞上便宜")
    elif info.get('结论') == 'needs-more-material':
        report.warn(
            'corpus.no-viable-holdout-split',
            f"**扣任何一份当 holdout 都满足不了 profile 门**："
            f"{'；'.join(info.get('拦路的') or [])} —— 差的是材料，不是文字")


def run_filename_year_vs_ledger(report, target: Path) -> None:
    """文件名里的四位年份 vs 台账 `published_at`——两边对不上，就至少有一处记错了。

    ★★ 为什么它值得进研究门：`published_at` 是 **PD 判定的输入**。
    2026-08-10 全库实测 1262 行两边都有年份、**56 行不一致（4.4%）**，
    其中 **5 条跨过 1931 分界**，逐份读题名页后发现**两条是台账错了**
    （Semmelweis 的 1938→1924、Holmes 的 1934→1892）——
    两条都把**合规的 PD 源标成了非 PD**，会让审计报出并不存在的违规。

    **只报不拦**：判据不知道是哪一边错（文件名里的年份可能是 IA 编号或年份区间），
    它给的是「去看一眼题名页」的名单。跨 PD 分界的那一类单独升级为独立警告。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_filename_year_vs_ledger.py'
    if not script.exists():
        report.metrics['filename_year_vs_ledger'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_fyvl', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        problems, info = module.evaluate(target)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['filename_year_vs_ledger'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    report.metrics['filename_year_vs_ledger'] = info
    if info.get('跨PD分界'):
        report.warn('source.year-straddles-pd-cutoff',
                    f"**{info['跨PD分界']} 条的文件名年份与 `published_at` 跨过 PD 分界 "
                    f"{module.PD_CUTOFF}** —— 这一类直接改变「这份源能不能用」，"
                    f"**必须逐份读题名页定案**，不要凭其中一个数下结论")
    if info.get('不一致'):
        report.warn('source.filename-year-mismatch',
                    f"{info['不一致']} 条文件名年份与 `published_at` 差 ≥2 年"
                    f" —— **至少有一处记错了**；判据不知道是哪一处")


def run_title_is_not_filename(report, target: Path) -> None:
    """台账的 `title` 是真书目题名，还是文件名的副本？（v0.0.0.-新增）

    ★★★★ 撞出它的是 Jenner #104 那次撤回：我发明了一条判据去分「同一部作品」，
    负对照打掉之后想找第二个证据源，才发现 **`title` 就是文件名**。
    全库实测 **1,941 / 1,969 行（99%）** 如此，真书目题名只有 28 行。

    **只报不拦。** 99% 的行是这样，做成硬门会让每个工作区当场全红——
    而这不是某一次操作的错，是历史累积。**拦不解决问题，只会让人去关门。**
    把数字打出来，让它每次跑都被看见。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_title_is_not_filename.py'
    if not script.exists():
        report.metrics['title_is_not_filename'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_titlefn', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        led = target / 'evidence' / 'source-ledger.jsonl'
        if not led.is_file():
            report.metrics['title_is_not_filename'] = {'状态': '没有台账，**未核验**（不是通过）'}
            return
        rows = [json.loads(l) for l in led.read_text(encoding='utf-8').splitlines() if l.strip()]
        info = module.analyse(rows)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['title_is_not_filename'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    n = info['**`title` 就是文件名**']
    report.metrics['title_is_not_filename'] = {
        '台账行数': info['台账行数'],
        '**`title` 就是文件名**': n,
        '真书目题名': info['`title` 是真书目题名'],
        '比例': info['比例'],
        '★': '**只报不拦**——全库 99% 如此；拦不解决问题，只会让人去关门',
    }
    if n:
        report.warn(
            'corpus.title-is-just-the-filename',
            f'**{n}/{info["台账行数"]} 行的 `title` 就是文件名**（{info["比例"]:.0%}）——'
            '这个字段没有承载信息。后果不是难看：判「两份是不是同一部作品」时'
            '**除了内容重叠没有第二个证据源**，引文坐标与「挂到哪部作品」也全落在文件名上。'
            '★ 与空值不同——**空值至少诚实，填成文件名的字段看起来是填过的**。')


def run_translation_witness(report, target: Path) -> None:
    """同一部作品的多个译本**不许当两处独立证据**（v0.0.0.80）。

    `check_claim_source_independence` 的作品分组**是语言盲的**：实测 Pacioli #161 的
    10 份源被它分成 **10 个作品组**，而其中三份译的是同一篇《Particularis de computis
    et scripturis》。于是「方法类断言要 ≥2 处独立证据」**可以靠引两种译本过掉**。

    ★ **本件敢当硬错**（与 `claim_source_independence` 只写 metrics 不同）：
      它只在工作区**自己申报了** `parallel_witnesses` 时才可能报错，
      而已入库的人一个都没申报过 → 对存量恒为 0 错，**拦不到无辜的人**。
      申报之后的判定是**精确的集合运算，没有启发式，没有误报**。

    ★★ 「自动认出哪些是译本」实测做不出来，已砍掉：阈值在一个工作区上标定，
       全库一跑 **38,368 对**（Barton 10,502、Virchow 6,973），
       而真阳性 0.080–0.102 **低于别处的噪声 0.12–0.19**。见检查器文件头。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_translation_witness.py'
    if not script.exists():
        report.metrics['translation_witness'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_transwit', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        errors, collapsed, lines = module.check(target)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['translation_witness'] = {'状态': f'运行失败，**未核验**：{exc}'}
        report.error('corpus.translation-witness-crashed',
                     f'并行见证判据跑不起来，**没核过不算通过**：{exc}')
        return
    groups = module.declared_groups(target)
    report.metrics['translation_witness'] = {
        '申报的并行见证组': len(groups),
        '组内塌缩的断言': collapsed,
        '错': errors,
        '明细': [l for l in lines if l.startswith('✗')][:6],
        '★': '申报 0 组**不等于**没有并行见证——本件不猜，只查申报',
    }
    for l in lines:
        if l.startswith('✗'):
            report.error('claim.parallel-witness-collapse', l.replace('\n', ' ').strip())


def run_quote_attributed_source(report, target: Path) -> None:
    """引文在不在**它自己引的那份源**里（v0.0.0.79，**只写 metrics**）。

    `check_quote_integrity` 扫的是全语料，所以「挂错源」它一定放行——
    读者按 `source_ids` 回查会落到另一份文献上，而所有计数都不变。

    落成时全库 27 个工作区回扫（长引文 **410** 条）：
    **挂错作品 / 版本差合计 35 条**，集中在 Osler 9、Virchow 8、Koch 5、Nightingale 4。
    **只写 metrics 不拦**：已入库的人未回扫过，硬拦会把整个名册一起拦下
    （与 `claim_source_independence` 同一条纪律）。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_quote_attributed_source.py'
    if not script.exists():
        report.metrics['quote_attributed_source'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_quoteattr', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        r = module.scan(target)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['quote_attributed_source'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    if '状态' in r:
        report.metrics['quote_attributed_source'] = {'状态': r['状态']}
        return
    wrong = [b for b in r['错挂'] if not b.get('同一作品组')]
    verz = [b for b in r['错挂'] if b.get('同一作品组')]
    report.metrics['quote_attributed_source'] = {
        '长引文': r['引文数'],
        '挂错作品': len(wrong),
        '版本差（作品对、逐字文本取自另一版）': len(verz),
        '不唯一（同句见于多份源，挂错也照样绿）': len(r['不唯一']),
        '取不到正文的源': r['取不到正文的源'],
        '例': [f"{b['claim_id']}：挂 {b['它引的源']} → 实 {b['真实出处']}"
               for b in (wrong + verz)[:6]],
    }


def run_evidence_per_claim(report, target: Path) -> None:
    """证据字段是逐条的还是填一次抄 N 遍（v0.0.0.78，**只写 metrics**）。

    `check_claim_anchors` 核的是「断言有没有挂上源」。
    **Koch #107 的 46 条断言全部挂上了源——挂的是同一对文件。**
    十个工作区实测：七个逐条各异，**三个不是**
    （Koch `source_ids` 1 种／46 条，Lister 两个字段各 1 种／35 条，
    Jenner `evidence_clusters` 1 种／35 条）。

    **它说的不是「这些断言是编的」，只说这个字段不再有信息量**——
    读它的判据于是在核一个常量。
    同型第二例：v0.0.0.24 一句 `attribution_basis` 让整批免检，逐源检查十版没跑过。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_evidence_is_per_claim.py'
    if not script.exists():
        report.metrics['evidence_per_claim'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_evperclaim', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['evidence_per_claim'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['evidence_per_claim'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    path = target / 'evidence' / 'claims.jsonl'
    if not path.is_file():
        report.metrics['evidence_per_claim'] = {'状态': '找不到 claims.jsonl，**未核验**（不是通过）'}
        return
    claims = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()
              if line.strip()]
    if not claims:
        report.metrics['evidence_per_claim'] = {'状态': '**断言文件是空的——未核验（不是通过）**'}
        return

    res = module.audit(claims)
    entry = {'断言条数': len(claims)}
    flagged = []
    for field, (state, _n, nonempty, distinct) in res.items():
        entry[field] = f'{state}（非空 {nonempty}/{len(claims)}，不同取值 {distinct}）'
        if state in ('表头', '几乎是表头'):
            flagged.append(f'{field}：{len(claims)} 条只有 {distinct} 种取值')
    if flagged:
        entry['**表头冒充证据**'] = flagged
    report.metrics['evidence_per_claim'] = entry


def run_corpus_ceiling(report, target: Path, profile: str) -> None:
    """抓源台账的一手上限够得着哪一档（v0.0.0.76，**只写 metrics**）。

    #115 Slavyanov 抓了 65 分钟、落 53 份（`min_sources` 45 是够的），
    才发现一手只有 8 份、占比 **0.1509**——deep 要的一手是 `ceil(45×0.65)` = **30 份**。
    **「45 份源」一直挂在嘴边，「30 份一手」从来没被说出来过。**

    **只写 metrics，不设门**：真正拦人的是 `min_primary_ratio` / `min_lanes` 本身，
    本件的用处是**在抓之前**（或至少在判分之前）把那个绝对数说出来。

    **老台账（竖线格式、无分档列）必须报「判不了」**——
    十份台账实测只有 5 份是本件认得的格式，
    **把「没有分档列」读成「零份一手」会给另外五个人伪造一条硬失败。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_corpus_ceiling.py'
    if not script.exists():
        report.metrics['corpus_ceiling'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_ceiling', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['corpus_ceiling'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['corpus_ceiling'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    # ★ 已入库的 attest 优先：`evidence/source-ledger.jsonl` schema 统一，
    #   且**发布门就是按它算的**——同口径才不会出现「我算的和门算的不是一个数」。
    #   抓源台账 `raw/_ids.txt` 只在还没入库时用（那才是本件真正的用武之地：抓之前），
    #   而它的格式因人而异：十份实测只有 5 份带分档列。
    ledger = None
    parse = module.parse_ledger
    which = '抓源台账'
    attest = target / 'evidence' / 'source-ledger.jsonl'
    if attest.is_file():
        ledger, parse, which = attest, module.parse_source_ledger, '入库 attest（口径同发布门）'
    else:
        # 抓源台账在 `<wip-…>/raw/_ids.txt`，工作区在 `<wip-…>/workspaces/<slug>/<slug>`——
        # **要往上走三层才够得到**（射程写窄和判据出错，表征一样是「没报错」）。
        base = target
        for _ in range(5):
            cand = base / 'raw' / '_ids.txt'
            if cand.is_file():
                ledger = cand
                break
            if base.parent == base:
                break
            base = base.parent
    if ledger is None:
        report.metrics['corpus_ceiling'] = {'状态': '既无入库 attest 也无抓源台账，**未核验**（不是通过）'}
        return

    rows, note = parse(ledger)
    if rows is None:
        report.metrics['corpus_ceiling'] = {
            '台账': str(ledger), '状态': f'**未核验**（不是通过）：{note}'}
        return

    total = len(rows)
    primary = sum(1 for tier, _ in rows if tier in module.PRIMARY_TIERS)
    lanes = len({lane for _, lanes_ in rows for lane in lanes_ if lane})
    need = module.required_primary(profile) if profile in module.PROFILES else None
    entry = {
        '读的是': which,
        '台账': str(ledger),
        '一手份数': primary,
        '台账总份数': total,
        '一手占比': round(primary / total, 4) if total else None,
        '有材料的道数': lanes,
    }
    if need is not None:
        ok, shrink, bad = module.verdict(primary, total, lanes, profile)
        entry[f'{profile} 要的一手份数'] = need
        entry['够得着吗'] = ('够不着：' + '；'.join(bad) if not ok
                             else ('**只有丢掉已取到的材料才够得着——那是缩分母，不是达标**'
                                   if shrink else '吃全部材料就够得着'))
    report.metrics['corpus_ceiling'] = entry


def run_unqualified_priority(report, target: Path) -> None:
    """无限定的首创声明（v0.0.0.73，**只写 metrics**）。

    评委没有语料——**「电弧焊是我发明的」读起来和真的一模一样。**
    直接风险：#115 Slavyanov 与 Benardos 都在队列里（金属电极 vs 碳电极，
    长期被互相混记），**两份产物将来同时在册**。

    **它绝不惩罚诚实的分层**：只要句子里有让渡（「不是我一个人」
    「只是其中一段」「在此之前已有人」），就算限定，直接放行。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_unqualified_priority_claim.py'
    if not script.exists():
        report.metrics['unqualified_priority'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_priority', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['unqualified_priority'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.selftest() != 0:
            report.metrics['unqualified_priority'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    paths = [p for p in (target / 'evidence' / 'claims.jsonl',) if p.is_file()]
    # ★ 答案文件常在工作区上面**两三层**（`wip-<人>-<编号>/xx_candidate.json`）。
    #   只上一层就只扫得到 claims.jsonl——**射程写错和判据出错，表征一样是绿的。**
    seen = set()
    base = target
    for _ in range(4):
        for c in sorted(base.glob('*_candidate.json')):
            if c not in seen:
                seen.add(c)
                paths.append(c)
        if base.parent == base:
            break
        base = base.parent
    if not paths:
        report.metrics['unqualified_priority'] = {'状态': '**没有断言也没有答案，未核验**'}
        return
    try:
        acc = module.scan(paths)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['unqualified_priority'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return

    info: dict[str, Any] = {'第一人称首创声明': acc['claims'],
                            '其中带限定': acc['qualified'],
                            '扫了几个文件': len(paths)}
    if acc['bad']:
        info['**无限定**'] = [f'{u}：{s}' for u, s in acc['bad'][:8]]
        info['口径'] = ('限定要么是年份，要么是材料／方法／范围，**要么是分层让渡**。'
                        '评委没有语料——**「这是我发明的」读起来和真的一模一样。**')
    elif acc['claims'] == 0:
        info['状态'] = ('一处首创声明都没扫到。**这可能是产物干净，也可能是判据窄**——'
                        'v0.0.0.73 第一版就在真数据上报过一次假的 0。')
    report.metrics['unqualified_priority'] = info


def run_holdout_overlap(report, target: Path, cache_dirs: list[str]) -> None:
    """holdout ↔ train 内容重合（v0.0.0.68 接进门，**此前从未跑过**）。

    ## 它为什么此前从未跑过

    这件判据**只存在于 `references/pipeline/checkers/`**，而 `scripts/` 里没有。
    `check_contract_drift` 的镜像比对写着 `if not twin.is_file(): continue`——
    **只存在于一侧的文件被静默跳过**，于是四件判据（含这一件自称硬门的）
    从来没有被任何调用点加载过。

    ## 接进来第一次跑就抓到

    Nightingale #112 实测：`notes-on-nursing-1906` 与 train 里的 1908 版
    **覆盖 53.1%**，1888 版与 1883 版覆盖 32.6%——
    **我把同一本书的不同版次一半放 train、一半放 holdout**。
    用它出的 `known` 题不测泛化，且一定得高分。

    **这本该在第 1 轮之前就拦下。**

    ## 只报不拦

    已入库 100 人的 holdout 从未按这条扫过，硬拦会把发布一起拦下。
    但**划 holdout 的时候看到它就该换源**——那时候换还来得及。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_holdout_overlap.py'
    if not script.exists():
        report.metrics['holdout_overlap'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_holdout', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['holdout_overlap'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    caches = [Path(c) for c in (cache_dirs or [])] or [target / 'raw']
    caches = [c for c in caches if c.is_dir()]
    if not caches:
        report.metrics['holdout_overlap'] = {'状态': '**找不到语料目录，未核验**'}
        return
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            rc = module.check(target, caches)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['holdout_overlap'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    out = buffer.getvalue()
    hard = [ln.strip() for ln in out.splitlines() if ln.strip().startswith('✗')]
    info: dict[str, Any] = {'返回码': rc, '**硬失败**': len(hard)}
    if hard:
        info['**逐条**'] = hard[:8]
        info['口径'] = ('holdout 的内容已在 train 中出现——**用它出的 known 题不测泛化，'
                        '且一定得高分**。正解是换源，不是调阈值。')
    report.metrics['holdout_overlap'] = info


def run_lane_quotes_verbatim(report, target: Path) -> None:
    """**六道研究稿里的每条逐字引文，都要能在语料里原样找到。**

    Roberts-Austen #135 实测：六道逐条标了 `source_id`、看上去无懈可击，
    回原文比对 **31 条里 2 条对不上**，其中最难查的一条是
    `Koyal` 被悄悄改回 `Royal`，**且句中一道版口被抹掉、两半缝成一句连续引文**。
    **缝合处不留痕迹，读起来完全通顺。**

    ★ 判准：**看得见的编辑记号（`**加粗**`／`<sup>`／`«»`／显式省略号）允许，
      不留痕迹的改动不允许。**
    ★★ 只写 metrics 不拦——**判据自己校了六轮**，全库还有 19 条未逐条分诊，
      在那之前不拿它卡流程（见 `check_lane_quotes_verbatim.py` 文件头）。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_lane_quotes_verbatim.py'
    if not script.exists():
        report.metrics['lane_quotes'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    # ★ 与本文件其它件同一套查找层级（工作区可能嵌 1–3 层）
    _cands = [target, target.parent, target.parent.parent]
    ws = next((c for c in _cands if (c / 'references' / 'research').is_dir()), None)
    if ws is None:
        report.metrics['lane_quotes'] = {'状态': '没有 references/research，**未核验**（不是通过）'}
        return
    try:
        spec = importlib.util.spec_from_file_location('_pd_lane_quotes', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _, rep = mod.check(ws)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['lane_quotes'] = {'状态': f'跑不起来，**未核验**（不是通过）：{exc}'}
        return
    report.metrics['lane_quotes'] = rep
    bad = sum(len(v.get('**对不上**', [])) for v in rep.get('逐道', {}).values())
    if bad:
        report.warnings.append(
            f'research.lane_quotes：{bad} 条逐字引文回原文对不上——'
            '**引文对不上就是引文对不上**，逐条读过再决定是改引文还是记盲区')


def run_namesake_criteria(report, target: Path) -> None:
    """**按人物定制的同名判据**（v0.0.0.151 接线，只写 metrics）。

    `check_authorship` 比的是「名 + 姓」，而 Sorby #133 的**父亲也叫 Henry Sorby**——
    父子二人这两样全同，只差一个中名，**现有护栏实测挡不住**。
    本件读工作区里的 `namesake-criteria.json`，逐份给出归属结论，
    并把「说不准」单列成 `unknown`——**不许并进任何一边**。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_namesake_criteria.py'
    if not script.exists():
        report.metrics['namesake_criteria'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    # ★ 与 `report_own_voice` 用同一套查找层级——**先前这里只查 2 层、那边查 3 层**，
    #   于是同一个工作区里一个说「已启用」、另一个说「不适用」。
    #   Sorby 的工作区嵌了三层（wip/workspaces/<slug>/<slug>），正好卡在差的那一层。
    _crit_paths = [target / 'namesake-criteria.json',
                   target.parent / 'namesake-criteria.json',
                   target.parent.parent / 'namesake-criteria.json',
                   target.parent.parent.parent / 'namesake-criteria.json']
    _crit = next((c for c in _crit_paths if c.is_file()), None)
    if _crit is None:
        report.metrics['namesake_criteria'] = {
            '状态': '本人物没有定制判据——**不适用**（不是通过）',
            '★': '「名+姓」够不够，取决于这个人物有没有同名近亲。**每个人物都要单测一次。**'}
        return
    spec = importlib.util.spec_from_file_location('_pd_nsc', script)
    mod = importlib.util.module_from_spec(spec)
    buffer = io.StringIO()
    try:
        spec.loader.exec_module(mod)
        with contextlib.redirect_stdout(buffer):
            n = mod.run(target, _crit)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['namesake_criteria'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    lines = [x.strip() for x in buffer.getvalue().splitlines() if x.strip()]
    info: dict[str, Any] = {'**unknown 条数**': n, '逐条': lines[:10]}
    if n:
        info['口径'] = ('**「说不准」不是通过。** 入库前逐条定夺，'
                        '或给那份材料补一条能站住的区分符。')
        report.warn('corpus.namesake-unknown', f'同名归属说不准 {n} 条（**不是通过**）')
    report.metrics['namesake_criteria'] = info


def run_rubric_health(report, target: Path) -> None:
    """**判据本身的两项体检**：抄没抄答案、要不要求人物出戏（v0.0.0.150 接线，**只写 metrics**）。

    ## 为什么发布门也要看一眼

    这两件此前**只在 `build_blind_payload` 里跑**——那是派发前，位置是对的。
    但**发布记录里一个数都没有**，而发布记录正是我判「过没过」时读的那一份。
    今天刚吃过一次亏：[[gates-cover-json-not-the-prose-users-read]]。

    ## 两个数都**只报不拦**

    改判据是要动冻结指令的事（按人物冻结，中途不得增删检查项），
    所以这里**只把数写进发布记录**，不改任何判定。
    """
    here = Path(__file__).resolve().parent
    cases_f = target / 'evals' / 'cases.jsonl'
    cand_f = target / 'evals' / 'candidate_answers.json'
    if not (cases_f.is_file() and cand_f.is_file()):
        # ★★★ 2026-08-10：**答案还不存在的时候，rubric 已经可以查了。**
        #   原来这里直接 return「未核验」，于是「判据要求出戏」这件事最早也要等到
        #   `build_blind_payload`（候选答案已产出）才被看见——那时 rubric 还改得动，
        #   但整套答案已经是照着它写出来的了。
        #   而 rubric 就写在 `cases.jsonl` 里，**写完那一刻就能查**。
        #   实测（Cicero #166）：写完 16 条当场跑，**红了我自己 3 条**——
        #   两条是真把「OCR 讹字」「本语料」写进了得分条件，一条是豁免表的缺口。
        if cases_f.is_file():
            fb = here / 'check_persona_frame_break.py'
            if not fb.exists():
                report.metrics['rubric_health'] = {'状态': '判据未安装，**未核验**（不是通过）'}
                return
            try:
                rub, pro = {}, {}
                for line in cases_f.read_text(encoding='utf-8').splitlines():
                    if line.strip():
                        r = json.loads(line)
                        rub[r['case_id']] = str(r.get('rubric') or '')
                        pro[r['case_id']] = str(r.get('prompt') or '')
                spec = importlib.util.spec_from_file_location('_pd_fb_early', fb)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                bad = {}
                for cid, ru in sorted(rub.items()):
                    if not mod.scan_text(ru):
                        continue
                    q = pro.get(cid) or ''
                    if q and any(re.search(p, q) for p in mod.ASKS_ABOUT_STOCK):
                        continue
                    if (q and any(re.search(p, q) for p in mod.USER_BRINGS_MATERIAL)
                            and any(re.search(p, q) for p in mod.PROCESSING_ASK)):
                        continue
                    bad[cid] = mod.scan_text(ru)
            except Exception as exc:                            # noqa: BLE001
                report.metrics['rubric_health'] = {'状态': f'只验判据时读入失败，**未核验**：{exc}'}
                return
            report.metrics['rubric_health'] = {
                '状态': '**答案尚未产出——本轮只验了 rubric**（不是全部核验）',
                '判据条数': len(rub),
                '**判据要求出戏的**': bad,
                '★ 口径': '**只报不拦**：改不改由人定。但它现在**在答案写出来之前**说话，'
                          '而不是等到派发前才说——那时答案已经是照着这条 rubric 写的了。'}
            if bad:
                report.warn('eval.rubric-demands-frame-break',
                            f'**{len(bad)} 条 rubric 把「谈资料库/扫描件/未收录」写成了得分条件**：'
                            f'{", ".join(sorted(bad))} —— 人物说那种话就是出戏，'
                            f'而同一份盲判指令又要评委扣「出戏」。**现在改还来得及。**')
            return
        report.metrics['rubric_health'] = {'状态': '没有 cases/答案，**未核验**（不是通过）'}
        return
    try:
        rubrics, prompts = {}, {}
        for line in cases_f.read_text(encoding='utf-8').splitlines():
            if line.strip():
                r = json.loads(line)
                rubrics[r['case_id']] = str(r.get('rubric') or '')
                prompts[r['case_id']] = str(r.get('prompt') or '')
        cand = json.loads(cand_f.read_text(encoding='utf-8'))
        base_f = target / 'evals' / 'baseline_answers.json'
        base = json.loads(base_f.read_text(encoding='utf-8')) if base_f.is_file() else None
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['rubric_health'] = {'状态': f'读入失败，**未核验**：{exc}'}
        return
    info: dict[str, Any] = {}
    for name, mod_name in (('抄答案', 'check_rubric_copies_answer'),
                           ('要求出戏', 'check_persona_frame_break'),
                           # ★ 席 F 与席 G 在 Sorby #133 第 2 轮**各自独立**指出：
                           #   答案声明「照印本录，一字不改」，随即录出 `immu- nity`、
                           #   `balf`、`wbat`——印本不可能有这些。**两句话自己打架，
                           #   不需要语料就能判**（评委正是在没有语料的条件下抓到的）。
                           ('忠实度自相矛盾', 'check_fidelity_claim_vs_artifacts')):
        script = here / f'{mod_name}.py'
        if not script.exists():
            info[name] = '判据未安装，**未核验**（不是通过）'
            continue
        spec = importlib.util.spec_from_file_location(f'_pd_{mod_name}', script)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            if name == '抄答案':
                r = mod.check(rubrics, cand, answers_b=base)
                z = r.get('★★★ **中译/压缩层（冻结指令要求，原先完全没查）**') or {}
                info[name] = {
                    '英文原串层': r.get('**rubric 抄了答案原文的题**'),
                    '**中译/压缩层**': z.get('越线题数'),
                    '占比': z.get('占比'),
                    '★': ('冻结指令写着「中译与压缩也算抄」；上一层只比英文，'
                          '**中文要 12 个字才够**，实测违规在 3–5 字之间'),
                }
            elif name == '忠实度自相矛盾':
                r = mod.check(cand)
                z = r.get('**声明与痕迹同现**') or {}
                info[name] = {
                    '题数': len(z),
                    '逐题': sorted(z),
                    '★': ('声称逐字忠实于**印本**，却展示只有影印/OCR 才有的痕迹——'
                          '要么「照印本录」这句错了，要么引文被动过。**只报不拦**：'
                          '改法涉及引文，改哪一头由人定。'),
                }
            else:
                r = mod.check(cand, rubrics, prompts)
                blamed = r.get('★★★ 判据招来的产物出戏（不算产物的账）', {}).get('题', {})
                info[name] = {
                    '判据要求出戏': len(r.get('判据要求出戏') or {}),
                    '产物出戏（已扣除判据招来的）': len(r.get('产物出戏') or {}),
                    '**判据招来的**': sorted(blamed),
                }
        except Exception as exc:                                # noqa: BLE001
            info[name] = f'运行失败，**未核验**：{exc}'
    info['★★ 口径'] = ('**只写 metrics，不改判定。** 改判据要动按人物冻结的指令，'
                       '那是下一个人物的事（见 RUBRIC-RULES-v2 第 ⑥ 条）。')
    report.metrics['rubric_health'] = info


def run_verdict_attribution(report, target: Path) -> None:
    """**判决书里「候选说了 X」，X 是不是真在候选那一侧**（v0.0.0.148 接线，**只报警**）。

    评委是盲的，笔记里每个「A」「B」都是盲坐标，而 A/B **逐题翻面**。
    从评委笔记往判决书里抄结论时**必须过 key**——Bessemer #132 第 1 轮没过，
    **四条结论全部把基线的毛病记到了候选头上**，其中一条正是
    「候选自相矛盾，说完不许现编还是编了两句格言」，
    而那两句**在基线里**；候选原文是「这个我不给」。

    ★ 我手查只查出三条；**第四条是本件建成后当场补出来的**，
    随后它又在 **Adams #131** 查出两处——那是一份我原本再也不会回头看的判决书。

    ## 为什么只报警不拦

    它查的是**散文**，不动任何分数。但 [[gates-cover-json-not-the-prose-users-read]]
    记的正是「判据只盯 JSON，漏了用户真正会读的那份散文」——
    **判决书恰恰是给人看的那一份。报出来就当场改。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_verdict_attribution.py'
    if not script.exists():
        report.metrics['verdict_attribution'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_verdict_attr', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['verdict_attribution'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            n = module.run(target)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['verdict_attribution'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    hits = [ln.strip() for ln in buffer.getvalue().splitlines() if ln.strip().startswith('✗')]
    info: dict[str, Any] = {'**归属错**': n}
    if n:
        info['**逐条**'] = hits[:8]
        info['口径'] = ('引文只在一侧出现，而判决书把它记到了另一侧。'
                        '**改判决书，不要改判据**——真值是 evals/*_answers.json。')
        report.warn('verdict.attribution-flipped', f'判决书归属写反 {n} 处（**盲坐标没过 key**）')
    report.metrics['verdict_attribution'] = info


def run_threshold_doc_drift(report, target: Path) -> None:
    """**文档里写的门槛，与代码里在用的那套，是不是同一套**（v0.0.0.141，硬门）。

    起因是我自己：`RUNBOOK.md` 那行「阈值：总分≥0.80、delta≥0.07、…」写的是 **deep** 的数
    而没写「deep」，我据此把 Thomson #129（跑 quick）的门槛记成 0.07，真值 0.03。
    ★ 那次结论没被改变（−0.0859 对 0.03 也过不了），**但那只是这一次刚好不影响。**

    与工作区无关，是仓级检查；放无条件段，**每次跑门都顺带核一次**。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_threshold_doc_drift.py'
    if not script.exists():
        report.metrics['threshold_doc_drift'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    code, out = proc.returncode, (proc.stdout or '') + (proc.stderr or '')
    bad = [ln.strip() for ln in out.splitlines() if ln.strip().startswith('✗')]
    info: dict[str, Any] = {'返回码': code, '**不一致处**': len(bad)}
    if code != 0:
        info['**逐条**'] = bad[:6]
        info['口径'] = ('文档门槛表与 PROFILE_THRESHOLDS 不一致——'
                        '**改文档去迁就代码，不许反过来**。'
                        '读文档的人会按错的数下判断，而这条流水线里读文档的主要是我自己。')
        report.errors.append(f'doc.threshold-drift: {len(bad)} 处')
    report.metrics['threshold_doc_drift'] = info


def run_material_split(report, target: Path) -> None:
    """**holdout 的正文有没有同时躺在 train 目录里**（v0.0.0.137 接线，**硬门**）。

    ## 这道判据一直存在、一直是对的，而**从来没有被任何代码调用过**

    全仓搜 `check_material_split`，命中只有两处注释与一句文档字符串，
    **没有一处 import 或 spec_from_file_location**。
    接上之后**第一跑就在 6 个工作区抓到硬失败**：

    | 工作区 | 泄漏份数 | 状态 |
    |---|---|---|
    | florence-nightingale | **9** | **已入库** |
    | comfort-avery-adams | 3 | 本轮正在判 |
    | elihu-thomson | 3 | 已记拒发 |
    | alexander-fleming | 1 | 已记拒发 |
    | william-osler | 1 | —— |
    | rudolf-virchow | 1 | —— |

    ## 它与 `check_holdout_overlap` 不是一回事

    后者查**内容**相似（不同源之间抄没抄），前者查**成员**（同一个源在不在两边）。
    ★★ 而后者恰恰**看不见**这一种：它按 source_id 把 holdout 从 train 里剔掉，
    于是「同一个 id 在两边各有一份」对它是不可见的——
    它照样报「train 69 份 … ✓ 无内容重合」。**两道判据缺一不可。**

    ## 成因不在 ingest

    `ingest.py` 现在是对的（`split == 'holdout'` 时写进 `references/holdout/`）。
    出事的是**先按 train 入库、事后在账本里改成 holdout**——**文件没跟着走。**

    ## 硬门

    与 `check_holdout_overlap` 的「只报不拦」不同：内容相似是程度问题，
    **而「同一份文件同时在 train 和 holdout」是事实问题，没有程度**。
    判据自己的输出已经写明后果：**「隔离失效，本轮 known 分数不可信」**。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_material_split.py'
    if not script.exists():
        report.metrics['material_split'] = {'状态': '检查器未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_material_split', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['material_split'] = {'状态': f'加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            rc = module.check(target)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['material_split'] = {'状态': f'运行失败，**未核验**：{exc}'}
        return
    out = buffer.getvalue()
    leaks = [ln.strip() for ln in out.splitlines() if 'holdout 正文出现在此' in ln]
    info: dict[str, Any] = {'返回码': rc, '**holdout 泄漏处**': len(leaks)}
    if leaks:
        info['**逐条**'] = leaks[:8]
        info['口径'] = ('同一个 source_id 的正文同时在 train 与 holdout 目录里——'
                        '**隔离失效，本轮 known 分数不可信**。'
                        '正解是把 holdout 的正文从 train 目录移走，不是调判据。')
        report.errors.append(f'corpus.holdout-leak: {len(leaks)} 处（隔离失效）')
    report.metrics['material_split'] = info


def run_corpus_integrity(report, target: Path) -> None:
    """语料真伪门（v0.0.0.33 新增，**只报不拦**）——已入库的这些文件，是语料吗？

    硬拦点在 `ingest.py` 入口（错误页根本进不来）。这里再扫一遍，是为了
    **已经建好的工作区**——已入库 100 人从未被扫过，谁也不知道里面有没有错误页。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_corpus_integrity.py'
    if not script.exists():
        report.metrics['corpus_integrity'] = {'状态': 'check_corpus_integrity.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_corpusint', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['corpus_integrity'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.metrics['corpus_integrity'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    hard, soft, missing, scanned = [], [], [], 0
    for rec in read_jsonl(target / 'evidence/source-ledger.jsonl'):
        lp = rec.get('local_path')
        if not lp:
            continue
        f = target / lp
        if not f.is_file():
            missing.append(lp)
            continue
        scanned += 1
        h, sf = module.check_file(f)
        hard += [f'{lp}　{x}' for x in h]
        soft += [f'{lp}　{x}' for x in sf]
    info: dict[str, Any] = {'已扫': scanned, '不是语料': len(hard), '可疑': len(soft)}
    if missing:
        # ★ v0.0.0.46：**改成硬错**。此前这里只写进 metrics、不拦，
        #   于是「账本指着不存在的文件」这件事从来没有拦下过任何人。
        #   回验实测：
        #     Galen #101      账本 60 条，盘上 **9** 份 —— 缺 51
        #     Vesalius #102   账本 47 条，盘上 **0** 份 —— 缺 47
        #     Livermore #100  账本 536 条，盘上 **0** 份 —— 缺 536
        #   **文件不在，则 primary_ratio、引文核查、覆盖率全都是对着虚空算的。**
        #   （Lister #108 与 Virchow #109 的账本零缺失，所以不存在「合法缺失」这一类。
        #    将来若真有只存图像的源，应当在账本里显式声明，而不是让它静默缺失。）
        info['**账本有记录但文件不在**'] = missing[:8]
        report.error('research.ledger-file-missing',
                     f'**{len(missing)} 条账本记录指着不存在的文件**——'
                     f'primary_ratio、引文核查与覆盖率都会对着虚空算。'
                     f'　示例：{"、".join(missing[:3])}')
    if hard:
        info['**这些不是语料**'] = hard[:10]
        report.error('research.corpus-not-a-document',
                     f'{len(hard)} 份已入库的「语料」其实不是文档'
                     f'——**它们有字节数、有校验和、算进了 primary_ratio**')
    if soft:
        info['可疑（只报不拦）'] = soft[:8]
    info['口径'] = ('**只判「这是不是一份文档」，不判「这是不是这个人的文档」**——'
                    '抓错了书、抓了译本当原本，本门一概看不见。')
    report.metrics['corpus_integrity'] = info


def run_source_attribution(report, target: Path, meta: dict[str, Any],
                           sources: list[dict[str, Any]]) -> None:
    """逐源归属门（v0.0.0.34 新增，**硬拦**）——`attribution_basis` 不是每本书的免检。

    v0.0.0.24 给 historical 人物开的那条路，实际把逐源归属检查整个关掉了：
    一份声明放行全部 P1。Jenner #104 实测，**两本不是他写的书**因此坐进了 P1——
    `b22006345`（第三方对照 Jenner 与 Woodville 已发表事实的小册子，题献给他们两个）
    与 `b21439114`（扉页 BY THOMAS BEDDOES）。

    **`check_authorship` 的 BYLINE 一处都没命中——它没被骗，它压根没被问。**
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_source_attribution.py'
    if not script.exists():
        report.metrics['source_attribution'] = {'状态': 'check_source_attribution.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_srcattr', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['source_attribution'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.error('content.selftest-failed',
                         'check_source_attribution.py 负对照未过——其检查结论不作数')
            return
    problems, info = module.evaluate(meta, sources, root=target)
    report.metrics['source_attribution'] = info
    for pb in problems:
        report.error('research.source-unclaimed', pb.split('\n')[0])


def run_quote_layer(report, target: Path) -> None:
    """引文层门（v0.0.0.32 新增，**只报不拦**）——这句外语是他写的，还是译者写的？

    三个人物、六轮盲判，同一条错反复出现（Livermore 把 Dies 的前言当自陈、
    Vesalius 把第三人称的 `suum` 写成「我自己称它」、Harvey 把译者的英文修辞
    分析成「我有意堆的」）。**而人工修不干净**：Harvey 第 3 轮我做的正是
    「把这个错一次改到位」，改完席 E 复核仍点出四处零标注 + 两处贴反。

    落成后回跑 Harvey 第 3 轮定稿：**席 E 手工点名的 7 处全中，另多抓 3 处**
    （`known-01`／`decoy-01`／`anon-02`）。

    **只报不拦**：它数的是形态不判真伪，标了「译文」的伪造引文照样过；
    已入库 100 人未回扫，硬拦会把整个名册一起拦下（与 `NO-SELFTEST`、新鲜度门同一条纪律）。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_quote_layer.py'
    if not script.exists():
        report.metrics['quote_layer'] = {'状态': 'check_quote_layer.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_quotelayer', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['quote_layer'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.metrics['quote_layer'] = {'状态': '**负对照未过，其结论不作数**'}
            return

    hits, scanned = [], 0
    payload = target / 'evals/judge_payload.v1.json'
    if payload.is_file():
        try:
            data = json.loads(payload.read_text(encoding='utf-8'))
            rows = (data if isinstance(data, list)
                    else [{'case_id': k, 'candidate': v} for k, v in data.items()])
            for r in rows:
                if not isinstance(r, dict):
                    continue
                for x in module.check_text(str(r.get('candidate', ''))):
                    hits.append((r.get('case_id') or '?', x))
            scanned += 1
        except Exception:                                        # noqa: BLE001
            pass
    for md in sorted((target / 'docs').glob('*.md')):
        try:
            for x in module.check_text(md.read_text(encoding='utf-8')):
                hits.append((f'docs/{md.name}', x))
            scanned += 1
        except Exception:                                        # noqa: BLE001
            continue

    info: dict[str, Any] = {'已扫文件': scanned, '引文层问题': len(hits)}
    if hits:
        info['**这些地方分不清原文与译文**'] = [f'{c}　{x}' for c, x in hits[:12]]
        info['口径'] = ('**数的是形态，不判真伪**——标了「译文」的伪造引文照样过；'
                        '它挡的是「忘了标」与「标反了」，不挡「编的」。故只报不拦。')
    report.metrics['quote_layer'] = info


def run_attribution_basis(report, target: Path, meta: dict[str, Any],
                          sources: list[dict[str, Any]]) -> None:
    """归属依据门（v0.0.0.24 新增）——**印刷时代之前的人物，靠什么证明是他写的**。

    ## 它补的是 `check_authorship.py` 结构上够不到的地方

    归属门认五种证据：`A-byline`／`A-editorial`／`A-turns`／`A-masthead`／`A-copyright`。
    **五种全部是印刷出版机器的产物。** 公元前五世纪的希腊一样都没有。

    更糟的是它**可能会通过**：现代译本扉页印着人物名，`A-byline` 照样命中；
    而 Kühn 版 22 卷里今天已知为伪托的篇目，**扉页署名与真作一模一样**。
    于是那条判据在最需要它的地方分辨力为零。

    起因是 2026-08-02 的 Hippocrates：一手源随手可取（Perseus／Gutenberg 实测均 200），
    而学界公认无一篇能归到他名下——**抓 45 条源毫无难度，抓完 `own_voice_ratio` 真值是 0。**

    ## 只在 research 阶段、只对 historical 人物硬拦

    归属错了，六路研究、断言、文档、用例全部要重做——和归属门同一个理由。
    非 historical 人物只记指标不判错：印刷时代的署名证据由归属门负责，本门不重复。

    既有 13 份 historical 产物**不受影响**：它们已打包登记，research 门不会重跑。
    """
    here = Path(__file__).resolve().parent
    script = here / 'check_attribution_basis.py'
    if not script.exists():
        report.metrics['attribution_basis'] = {
            '状态': 'check_attribution_basis.py 未安装，**未核验**（不是通过）'}
        return
    spec = importlib.util.spec_from_file_location('_pd_attribution', script)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                                    # noqa: BLE001
        report.metrics['attribution_basis'] = {'状态': f'检查器加载失败，**未核验**：{exc}'}
        return

    # ★ 负对照不过 → 它的「全绿」不构成任何证据。与其余硬门同一条纪律。
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        if module.self_test() != 0:
            report.error('content.selftest-failed',
                         'check_attribution_basis.py 负对照未过——其检查结论不作数')
            return

    problems, info = module.check_meta(meta)
    surname = str(meta.get('name') or '').split()[0] if meta.get('name') else ''
    if str(meta.get('subject_origin') or '') == 'historical':
        sp, si = module.check_sources(sources, surname)
        problems += sp
        info.update(si)
    report.metrics['attribution_basis'] = info
    for item in problems:
        report.error('research.attribution-basis', item)


def main() -> int:
    parser = argparse.ArgumentParser(description='Evidence-aware quality gate for Persona Distiller targets.')
    parser.add_argument('target', type=Path)
    parser.add_argument('--phase', choices=['research', 'synthesis', 'release'], default='release')
    parser.add_argument('--cache', nargs='*', default=[],
                        help='原始语料目录（可多个）。发布门的内容层核验需要它；'
                             '不给则记 warning 说明「未做」，而不是当作通过。')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as failures.')
    parser.add_argument('--allow-provisional', action='store_true', help='Downgrade quantitative minimum misses to warnings; never hides leakage or structural errors.')
    parser.add_argument('--write-report', action='store_true')
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    # ★★★ 2026-08-10：**双层嵌套的工作区**（`workspaces/<slug>/<slug>/`）今天绊了我四次。
    #   Osler / Nightingale / Virchow / Barton 都是这个形状，
    #   而 `ls -d .../workspaces/*/` 取到的是**外层**，于是报 `target.invalid`。
    #   判据没错，是调用方每次都要多走一步。**在入口处替它走掉。**
    #
    #   ★ 条件收得很紧：**当前目录没有 `meta.json`，而恰好只有一个直接子目录有**。
    #     多于一个就不猜——那说明这个路径本来就有歧义。
    #   ★★ **下降之后必须大声打印实际用的路径**：不打印就变成了另一种「指错文件」
    #     （见 `gate-green-but-pointed-at-wrong-artifact`：门绿了而指的不是你以为的那份）。
    if not (target / 'meta.json').is_file():
        _kids = [d for d in sorted(target.iterdir()) if d.is_dir() and (d / 'meta.json').is_file()]             if target.is_dir() else []
        if len(_kids) == 1:
            print(f"★ 给的目录没有 meta.json，**自动下降一层**：{target.name} → {_kids[0].name}\n"
                  f"  ★★ 实际用的路径：{_kids[0]}", file=sys.stderr)
            target = _kids[0]
        elif len(_kids) > 1:
            print(f"★ 给的目录没有 meta.json，而有 {len(_kids)} 个子目录都有——"
                  f"**不猜**，请指明是哪一个：{[d.name for d in _kids]}", file=sys.stderr)
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
        run_authorship_gate(report, target, meta, sources)
        run_corpus_integrity(report, target)
        run_attribution_basis(report, target, meta, sources)
        run_source_attribution(report, target, meta, sources)
        run_fact_density(report, target, sources)
        run_quote_layer(report, target)
        run_ocr_gate(report, target, sources)
        # ★★ 放在**无条件段**：本文件没有 `if args.phase == 'research'` 分支，
        #   2547 行之前的都是三个 phase 共跑的。这两件问「语料本身能不能用」，
        #   **必须最早跑**——等到发布门才发现「10 份乱码」「1 份装错文件」，
        #   中间整轮断言／渲染／判分都建在坏语料上了。
        run_corpus_text_checks(report, target, args.cache)
        # ★ 同理放无条件段：holdout 泄漏是**语料成员**问题，
        #   等到合成门才报就已经拿泄漏的源出过 known 题了。
        run_material_split(report, target)
        run_threshold_doc_drift(report, target)
        run_verdict_attribution(report, target)
        run_rubric_health(report, target)
        run_namesake_criteria(report, target)
        run_lane_quotes_verbatim(report, target)
        report_own_voice(report, target, meta, sources)
        report_stance_density(report, target, sources)
        report_catalogue_entries(report, target, sources)
        report_verbatim_quotes(report, target, args.cache)
        report_semantic_residue(report, target)
        report_refusal_overflow(report, target)
        run_corpus_ceiling(report, target, report.profile)
        run_corpus_feasibility(report, target)
        run_rights_basis(report, target)
        run_pd_grounds(report, target)
        train_ids = {record.get('source_id') for record in sources if record.get('split') == 'train'}
        evaluate_research(report, target, thresholds, train_ids, args.allow_provisional)
        run_translation_witness(report, target)
        run_title_is_not_filename(report, target)
        run_filename_year_vs_ledger(report, target)
        cases: list[dict[str, Any]] = []
        if args.phase in {'synthesis', 'release'}:
            evaluate_claims(report, target, thresholds, sources, args.allow_provisional)
            cases = evaluate_cases(report, target, thresholds, {record.get('source_id') for record in holdout}, args.allow_provisional)
            run_case_self_sufficiency(report, cases)
            run_measurement_claims(report, target)
            run_evidence_per_claim(report, target)
            run_claim_source_independence(report, target)
            run_quote_attributed_source(report, target)
            run_answer_constraints(report, target)
            run_verbatim_pointer(report, target)
            run_unwired_three(report, target)
            run_unqualified_priority(report, target)
            run_sole_authorship(report, target)
            run_holdout_overlap(report, target, args.cache)
        if args.phase == 'release':
            evaluate_results(report, target, thresholds, cases)
            run_suite_single_drag(report, target, thresholds)
            run_content_checks(report, target, args.cache)
            run_baseline_provenance(report, target)
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
