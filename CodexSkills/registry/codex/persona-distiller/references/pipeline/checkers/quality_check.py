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
            elif code == 2:
                report.error('content.selftest-failed',
                             'check_quote_integrity 负对照未过——其检查结论不作数')
            elif code != 0:
                review['quote_integrity'] = ('有引文未在语料中找到'
                                             '——**未命中不等于伪造**，须人工核对；'
                                             '但「改了 OCR 错字再当逐字引文」也落在这里')

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
    if not loc_argv:
        review['quote_locator'] = '断言与答案都取不到，**引文坐标未核（不是通过）**'
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
        review['answer_length_leak'] = (
            'evals/baseline.v1.json 不在——**长度泄题未核（不是通过）**；'
            '基线只存在于人物工作目录里，没落进工作区，**门看不见它**')
    elif not payload.exists():
        review['answer_length_leak'] = 'judge_payload 不在——**长度泄题未核（不是通过）**'
    else:
        code, out = run('check_answer_length_leak.py',
                        ['--candidate', str(payload), '--baseline', str(baseline)])
        if code == -1:
            review['checker_missing'] = out
        elif code == 3:
            report.error('eval.length-unresolved',
                         '长度泄题**未核成**（不是通过）：两侧没有共有的题号')
        elif code == 2:
            report.error('content.selftest-failed',
                         'check_answer_length_leak 负对照未过——其检查结论不作数')
        elif code != 0:
            hit = [l for l in out.splitlines() if l.startswith('✗')]
            report.error('eval.length-leak',
                         '**长度会指出哪一侧是候选**，这一轮的盲判不成立：'
                         + '；'.join(h.lstrip('✗ ') for h in hit)[:200])
        else:
            line = next((l for l in out.splitlines() if l.startswith('**总体均长比')), '')
            review['answer_length_leak'] = '✓ ' + line.replace('**', '')[:120]

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
        report_own_voice(report, target, meta, sources)
        report_refusal_overflow(report, target)
        train_ids = {record.get('source_id') for record in sources if record.get('split') == 'train'}
        evaluate_research(report, target, thresholds, train_ids, args.allow_provisional)
        cases: list[dict[str, Any]] = []
        if args.phase in {'synthesis', 'release'}:
            evaluate_claims(report, target, thresholds, sources, args.allow_provisional)
            cases = evaluate_cases(report, target, thresholds, {record.get('source_id') for record in holdout}, args.allow_provisional)
            run_case_self_sufficiency(report, cases)
            run_measurement_claims(report, target)
            run_sole_authorship(report, target)
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
