from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from common import SUITES, append_jsonl, utc_now


def run_script(name: str, *args: object, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / name), *[str(arg) for arg in args]],
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
        timeout=60,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f'{name} failed ({completed.returncode})\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}'
        )
    return completed


def run_target_script(target: Path, name: str, *args: object, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(target / 'scripts' / name), *[str(arg) for arg in args]],
        cwd=str(target),
        text=True,
        capture_output=True,
        timeout=60,
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f'target {name} failed ({completed.returncode})\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}'
        )
    return completed


def create_target(
    temp_root: Path,
    slug: str = 'example-thinker',
    profile: str = 'quick',
    identity: str = '5',
    subject_origin: str = 'public',
    consent_authority: str | None = None,
    retention_policy: str | None = None,
) -> Path:
    workspace = temp_root / 'workspaces'
    args: list[object] = [
        '--name', 'Example Thinker', '--slug', slug,
        '--profile', profile, '--identity', identity,
        '--subject-origin', subject_origin, '--workspace', workspace,
    ]
    if consent_authority:
        args.extend(['--consent-authority', consent_authority])
    if retention_policy:
        args.extend(['--retention-policy', retention_policy])
    run_script('init_target.py', *args)
    return workspace / slug


def _substantive_model(title: str, claim_markers: str = '') -> str:
    paragraphs = [
        f'# {title}',
        '',
        '## Evidence-grounded operating content',
        '',
    ]
    for index in range(1, 14):
        paragraphs.append(
            f'{index}. In the synthetic validation fixture, this section defines an executable but bounded pattern: '
            'identify constraints, separate observations from inference, compare reversible options, state a stop rule, '
            'verify the result against evidence, and disclose uncertainty. The wording is intentionally substantive so '
            'the release gate tests real file loading rather than accepting empty template text.'
        )
    if claim_markers:
        paragraphs.extend(['', '## Linked Claims', '', claim_markers])
    paragraphs.extend([
        '', '## Limits', '',
        'This fixture does not claim real-person fidelity. It exists only to validate contracts, packaging, routing, '
        'evaluation plumbing, provenance handling, and privacy-minimized unnumbered runtime records.',
    ])
    return '\n\n'.join(paragraphs).rstrip() + '\n'


def populate_release_ready(target: Path, material_root: Path) -> dict[str, Any]:
    """Create a fully synthetic, rights-clean target that passes the quick release gate."""
    material_root.mkdir(parents=True, exist_ok=True)
    lanes = ['writings', 'conversations', 'decisions', 'expression', 'external', 'timeline', 'writings', 'decisions']
    source_paths: list[Path] = []
    for index, lane in enumerate(lanes, 1):
        source = material_root / f'source-{index}-{lane}.md'
        source.write_text(
            (f'# Synthetic source {index}\n\nThis is licensed synthetic evidence for testing lane {lane}. '
             f'It records a distinct context, constraint, action, outcome, and decision trace {index}.\n\n') * 15,
            encoding='utf-8',
        )
        source_paths.append(source)
    ingest_args: list[object] = [
        target, *source_paths, '--tier', 'P1', '--source-type', 'interview',
        '--rights', 'synthetic-test-material; redistribution-permitted',
    ]
    # Every fixture source is cross-indexed to all six lanes so metadata coverage is explicit.
    for dimension in ('writings', 'conversations', 'expression', 'external', 'decisions', 'timeline'):
        ingest_args.extend(['--dimension', dimension])
    payload = json.loads(run_script('ingest.py', *ingest_args).stdout)
    source_ids = [item['source_id'] for item in payload['results'] if item['status'] == 'normalized']

    holdout = material_root / 'holdout.md'
    holdout.write_text(('Held-out synthetic decision record. It must never enter model Claims.\n') * 20, encoding='utf-8')
    completed = run_script(
        'ingest.py', target, holdout, '--holdout', '--tier', 'P1',
        '--source-type', 'decision-record', '--dimension', 'decisions',
        '--rights', 'synthetic-test-material; redistribution-permitted',
    )
    holdout_id = json.loads(completed.stdout)['results'][0]['source_id']

    lane_files = {
        'writings': '01-writings.md',
        'conversations': '02-conversations.md',
        'expression': '03-expression.md',
        'external': '04-external.md',
        'decisions': '05-decisions.md',
        'timeline': '06-timeline.md',
    }
    for lane, rel in lane_files.items():
        relevant = [sid for sid, assigned in zip(source_ids, lanes) if assigned == lane]
        if len(relevant) < 2:
            for candidate in source_ids:
                if candidate not in relevant:
                    relevant.append(candidate)
                if len(relevant) >= 2:
                    break
        text = (
            f'# Synthetic {lane} research\n\n'
            '## Scope and assigned sources\n\n' + ', '.join(relevant) + '\n\n'
            '## Source-linked observations\n\n' +
            ''.join(
                f'- Distinct observation {i} is grounded in {relevant[i % len(relevant)]}; it records context, '
                'constraint, action, outcome, and at least one alternative explanation.\n'
                for i in range(36)
            ) +
            '\n## Candidate Claims\n\n- Atomic candidates remain separate from facts until adjudicated.\n\n'
            '## Contradictions and alternative explanations\n\n'
            '- Audience, role incentives, time period, and selective publication can explain part of the pattern.\n\n'
            '## Unknowns and source gaps\n\n- More longitudinal evidence would improve confidence.\n\n'
            '## Handoff to adjudication\n\n- Validate origin independence and Holdout separation before promotion.\n'
        )
        (target / 'references' / 'research' / rel).write_text(text, encoding='utf-8')

    claims = []
    categories = ['mental-model', 'mental-model', 'heuristic', 'heuristic', 'heuristic']
    for index, category in enumerate(categories, 1):
        claim_id = f'clm-{index:012x}'
        claims.append({
            'claim_id': claim_id,
            'claim': f'Synthetic executable cognitive pattern {index}.',
            'category': category,
            'status': 'pattern',
            'source_ids': [source_ids[index % len(source_ids)], source_ids[(index + 1) % len(source_ids)]],
            'counter_source_ids': [],
            'contexts': [f'context-{index}-a', f'context-{index}-b'],
            'evidence_clusters': [f'cluster-{index}-a', f'cluster-{index}-b'],
            'confidence': 0.7,
            'time_scope': 'synthetic test period',
            'applicability': 'synthetic test decisions',
            'falsifiers': ['A contrary decision under materially equivalent constraints.'],
            'alternative_explanations': ['Role incentives may explain part of the behavior.'],
            'supersedes': None,
            'author_role': 'test-fixture',
            'created_at': utc_now(),
            'updated_at': utc_now(),
        })
    for claim in claims:
        append_jsonl(target / 'evidence' / 'claims.jsonl', claim)
    marker_lines = '\n'.join(f'- {claim["claim"]} <!-- claim:{claim["claim_id"]} -->' for claim in claims)

    model_files = {
        'facts.md': 'Fact Boundary',
        'cognitive-os.md': 'Cognitive Operating System',
        'decision-policy.md': 'Decision Policy',
        'strategy.md': 'Strategy System',
        'capabilities.md': 'Capability Envelope',
        'work.md': 'Work System',
        'persona.md': 'Persona and Interaction',
        'boundaries.md': 'Boundaries and Stop Rules',
        'hypotheses.md': 'Quarantined Hypotheses',
        'divergence-map.md': 'Divergence Map',
    }
    for rel, title in model_files.items():
        markers = marker_lines if rel == 'cognitive-os.md' else ''
        (target / rel).write_text(_substantive_model(title, markers), encoding='utf-8')

    meta = json.loads((target / 'meta.json').read_text(encoding='utf-8'))
    team_card = json.loads((target / 'team-card.json').read_text(encoding='utf-8'))
    team_card.update({
        'readiness': 'ready',
        'research_cutoff': '2026-07-23',
        'selection_reasons': [
            'Synthetic evidence exercises all release, routing, provenance, and privacy contracts.',
        ],
        'distillation_traits': [
            'Separates observation from inference and uses explicit verification and stop rules.',
        ],
        'user_value': [
            'Produces bounded, executable decisions with visible uncertainty and validation.',
        ],
        'application_scenarios': [
            'research-problem-solving',
            'strategy-decision',
        ],
        'key_capabilities': [
            'Evidence synthesis',
            'Decision analysis',
            'Execution planning',
        ],
        'hard_boundaries': [
            'Synthetic fixture only; it makes no real-person fidelity claim.',
            'Never claim tools or actions ran when they did not.',
        ],
        'canonical_name': meta['name'],
        'subject_slug': meta['slug'],
    })
    (target / 'team-card.json').write_text(
        json.dumps(team_card, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )

    cases = []
    candidate_scores = {suite: 0.82 for suite in SUITES}
    candidate_scores.update({'voice': 0.78, 'fact-preservation': 0.92, 'boundary': 0.84})
    for suite in SUITES:
        case = {
            'case_id': f'case-{suite}',
            'suite': suite,
            'prompt': f'Synthetic prompt for {suite}.',
            'turns': ['turn one', 'turn two', 'turn three'] if suite in {'trajectory', 'long-horizon'} else [],
            'holdout_source_ids': [holdout_id] if suite == 'known' else [],
            'rubric': {'decision-model-fidelity': 1.0, 'factual-correctness': 1.0},
            'expected': {'note': 'synthetic'},
            'critical': suite in {'boundary', 'fact-preservation', 'tool-use', 'identity-routing'},
            'notes': None,
        }
        append_jsonl(target / 'evals' / 'cases.jsonl', case)
        cases.append(case)
        for system, score in [('baseline', 0.60), ('candidate', candidate_scores[suite])]:
            append_jsonl(target / 'evals' / 'results.jsonl', {
                'run_id': 'run-synthetic',
                'case_id': case['case_id'],
                'suite': suite,
                'system': system,
                'blind_label': 'A' if system == 'baseline' else 'B',
                'judge_id': 'judge-1',
                'overall_score': score,
                'dimension_scores': {'decision-model-fidelity': score, 'factual-correctness': score},
                'critical_failure': False,
                'critical_failure_type': None,
                'rationale': 'Synthetic fixture score.',
                'timestamp': utc_now(),
            })
    return {'source_ids': source_ids, 'holdout_id': holdout_id, 'claims': claims, 'cases': cases}
