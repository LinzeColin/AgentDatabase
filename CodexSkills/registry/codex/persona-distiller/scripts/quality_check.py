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
    name = str(meta.get('name') or '').strip()
    surname = name.split()[-1] if name.split() else ''
    if not surname:
        report.metrics['own_voice'] = {'状态': 'meta 无 name，**未核验**'}
        return
    rx = re.compile(re.escape(surname), re.I)

    own_bytes = all_bytes = 0
    own_ids: list[str] = []
    for record in sources:
        rel = record.get('local_path')
        path = (target / rel) if rel else None
        if not path or not path.is_file():
            continue
        size = path.stat().st_size
        all_bytes += size
        if rx.search(str(record.get('author') or '')):
            own_bytes += size
            own_ids.append(str(record.get('source_id')))
    ratio = (own_bytes / all_bytes) if all_bytes else 0.0
    report.metrics['own_voice'] = {
        '本人所著的 train 源数': len(own_ids),
        'train 源总数': len(sources),
        '本人所著字节': own_bytes,
        'train 总字节': all_bytes,
        'own_voice_ratio': round(ratio, 4),
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
    if not cache_dirs:
        review['corpus'] = '未提供 --cache，装饰性引用与伪造引文两项**未做**（不是通过）'
    else:
        code, out = run('check_claim_coverage.py',
                        ['--workspace', str(target), '--cache', *cache_dirs])
        if code == -1:
            review['checker_missing'] = out
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
            code, out = run('check_quote_integrity.py',
                            ['--claims', str(claims), '--cache', *cache_dirs])
            if code == -1:
                review['checker_missing'] = out
            elif '未命中 0 个' not in out:
                review['quote_integrity'] = ('有引文未在语料中找到'
                                             '——**未命中不等于伪造**，须人工核对')

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

    for item in unproven:
        report.error('research.authorship-unproven',
                     f'{item} —— 账本声称本人所著，但文中查无归属证据'
                     f'（署名／编者注／逐字稿轮次三者皆无）')


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
        run_attribution_basis(report, target, meta, sources)
        run_ocr_gate(report, target, sources)
        report_own_voice(report, target, meta, sources)
        report_refusal_overflow(report, target)
        train_ids = {record.get('source_id') for record in sources if record.get('split') == 'train'}
        evaluate_research(report, target, thresholds, train_ids, args.allow_provisional)
        cases: list[dict[str, Any]] = []
        if args.phase in {'synthesis', 'release'}:
            evaluate_claims(report, target, thresholds, sources, args.allow_provisional)
            cases = evaluate_cases(report, target, thresholds, {record.get('source_id') for record in holdout}, args.allow_provisional)
        if args.phase == 'release':
            evaluate_results(report, target, thresholds, cases)
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
