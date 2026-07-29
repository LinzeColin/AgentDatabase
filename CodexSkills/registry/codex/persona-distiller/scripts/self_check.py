#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parse_frontmatter, read_json, scan_secrets, valid_skill_name
from install import verify_tree


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate Persona Distiller and run offline tests.')
    parser.add_argument('--skip-tests', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, object] = {}

    try:
        fm, _ = parse_frontmatter(root / 'SKILL.md')
        if set(fm) != {'name', 'description'}:
            errors.append(f'root SKILL.md frontmatter must contain only name/description; found {sorted(fm)}')
        name = fm.get('name', '')
        description = fm.get('description', '')
        if name != root.name or not valid_skill_name(name):
            errors.append(f'invalid or mismatched Skill name: {name!r} vs {root.name!r}')
        if not 1 <= len(description) <= 1024:
            errors.append(f'description length out of range: {len(description)}')
        lines = len((root / 'SKILL.md').read_text(encoding='utf-8').splitlines())
        checks['skill_lines'] = lines
        if lines > 500:
            errors.append(f'SKILL.md has {lines} lines; progressive-disclosure limit is 500')
    except Exception as exc:
        errors.append(f'SKILL.md validation failed: {exc}')

    release_verification = verify_tree(root)
    checks['release_verification'] = release_verification
    if release_verification.get('mode') == 'checksums.sha256' and not release_verification.get('verified'):
        errors.append('release checksum verification failed: ' + '; '.join(release_verification.get('errors', [])))

    version = (root / 'VERSION').read_text(encoding='utf-8').strip() if (root / 'VERSION').is_file() else None
    manifest = read_json(root / 'manifest.json', default={}) or {}
    checks['version'] = version
    # ★ 版本以 VERSION 文件为单一真源，不硬编码。
    #   原来写死 'v0.0.0.6'，而 skill 早已升到 v0.0.0.7——
    #   **这个校验从那次升版起就一直失败，且无人发现**，
    #   因为它混在另外几个既有失败里。升版时漏改校验点，是典型的「单一真源没建立」。
    if not version or manifest.get('version') != version:
        errors.append(f'version mismatch: VERSION={version!r}, manifest={manifest.get("version")!r}')
    if manifest.get('runtime_identity_routing') != 'automatic':
        errors.append('manifest must declare automatic runtime identity routing')
    if manifest.get('runtime_invocation_versioning') is not False:
        errors.append('manifest must disable per-invocation versioning')

    required = [
        'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'SECURITY.md', 'handoff.md',
        'agents/openai.yaml', 'registries/identity-families.json',
        'templates/target/SKILL.md.tmpl', 'templates/target/agents/openai.yaml.tmpl',
        'templates/target/scripts/runtime_recorder.py', 'templates/target/scripts/runtime_router.py',
        'scripts/identity.py', 'scripts/route_engine.py', 'scripts/namesake_gate.py', 'scripts/init_target.py',
        'scripts/package_target.py', 'scripts/delivery_builder.py', 'scripts/normalize_delivery.py',
        'scripts/build_release_bundle.py',
        'scripts/register_persona.py', 'scripts/validate_persona_registry.py',
        'scripts/persona_registry.py', 'scripts/build_manifest.py', 'scripts/install.py',
        'scripts/review_harness.py', 'schemas/persona-registration.schema.json', 'schemas/runtime-record.schema.json',
        'templates/delivery/install.py', 'templates/target/team-card.json.tmpl',
        'templates/bundle/install.py', 'templates/bundle/README.md',
        'references/persona-product-registration.md', 'schemas/namesake-gate.schema.json',
        'audit/10-round-improvement.md', 'audit/2x6-review.md',
    ]
    for rel in required:
        if not (root / rel).is_file():
            errors.append(f'missing required file: {rel}')

    try:
        registry = read_json(root / 'registries/identity-families.json', default={}) or {}
        families = registry.get('families', [])
        checks['identity_families'] = len(families)
        if len(families) != 12:
            errors.append('identity registry must contain exactly twelve choices')
        numbers = [item.get('number') for item in families]
        ids = [item.get('id') for item in families]
        if numbers != list(range(1, 13)) or len(ids) != len(set(ids)):
            errors.append('identity numbers must be 1..12 and IDs unique')
    except Exception as exc:
        errors.append(f'identity registry invalid: {exc}')

    schema_count = 0
    for schema in sorted((root / 'schemas').glob('*.json')):
        schema_count += 1
        try:
            value = json.loads(schema.read_text(encoding='utf-8'))
            if value.get('$schema') != 'https://json-schema.org/draft/2020-12/schema':
                warnings.append(f'{schema.name} uses an unexpected JSON Schema draft')
        except Exception as exc:
            errors.append(f'invalid schema {schema.name}: {exc}')
    checks['schema_count'] = schema_count

    group_root = root.parent / 'persona-distiller-group'
    group_required = [
        'SKILL.md', 'README.md', 'CANONICAL-ROOT-ROUTE.md', 'team-index.json',
        'scripts/registry_core.py', 'scripts/route_team.py', 'scripts/validate_group.py',
    ]
    for rel in group_required:
        if not (group_root / rel).is_file():
            errors.append(f'missing sibling group file: {rel}')

    script_paths = (
        list((root / 'scripts').glob('*.py'))
        + list((root / 'templates/target/scripts').glob('*.py'))
        + list((root / 'templates/delivery').glob('*.py'))
        + list((group_root / 'scripts').glob('*.py'))
    )
    for script in sorted(script_paths):
        try:
            source = script.read_text(encoding='utf-8')
            compile(source, str(script), 'exec')
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(f'compile failed for {script.relative_to(root)}: {exc}')
    checks['python_script_count'] = len(script_paths)

    secret_findings = scan_secrets(root, exclude_dirs={'.git', '__pycache__', 'tests', 'examples'})
    checks['secret_findings'] = secret_findings
    if secret_findings:
        errors.extend(f'secret-like pattern {item["type"]} in {item["file"]}:{item["line"]}' for item in secret_findings)

    file_paths = [p for p in root.rglob('*') if p.is_file()]
    checks['file_count'] = len(file_paths)
    checks['total_size_bytes'] = sum(p.stat().st_size for p in file_paths)
    if len(file_paths) > 500:
        errors.append(f'package has {len(file_paths)} files; must remain <=500')
    oversize = [str(p.relative_to(root)) for p in file_paths if p.stat().st_size > 25 * 1024 * 1024]
    if oversize:
        errors.append(f'files exceed 25 MB: {oversize}')
    symlinks = [str(p.relative_to(root)) for p in root.rglob('*') if p.is_symlink()]
    checks['symlinks'] = symlinks
    if symlinks:
        errors.append(f'source package contains symlinks: {symlinks}')

    # Detect stale operational contracts without rejecting historical changelog/audit references.
    active_files = [
        root / 'SKILL.md', root / 'README.md', root / 'scripts/init_target.py',
        root / 'scripts/route_engine.py', root / 'templates/target/SKILL.md.tmpl',
        root / 'templates/target/scripts/runtime_router.py',
    ]
    for path in active_files:
        text = path.read_text(encoding='utf-8')
        if '--subject-type' in text or "builder-version: \"v0.0.0.1\"" in text:
            errors.append(f'stale v1 operational contract in {path.relative_to(root)}')
        for token in ['invocation_manager.py', 'runtime_identity_gate', '运行版本：']:
            if token in text:
                errors.append(f'stale numbered runtime token {token!r} in {path.relative_to(root)}')

    registry_check = subprocess.run(
        [sys.executable, str(root / 'scripts' / 'validate_persona_registry.py')],
        cwd=str(root), text=True, capture_output=True,
    )
    checks['persona_registry'] = {
        'returncode': registry_check.returncode,
        'stdout': registry_check.stdout,
        'stderr': registry_check.stderr,
    }
    if registry_check.returncode != 0:
        errors.append('persona product registry validation failed')

    # ★ 合同漂移门。上面那条 version 校验只比 VERSION 与 manifest.json **两处**，
    #   而对外声明版本的地方有八处——v0.0.0.8 说「版本已建立单一真源」，
    #   建立的其实是两点之间的一致，剩下六处一路漂到七个不同的版本号。
    #   独立脚本不是门（v0.0.0.10 的教训），必须挂进 self_check 才会有人跑。
    drift_check = subprocess.run(
        [sys.executable, str(root / 'scripts' / 'check_contract_drift.py'), '--json'],
        cwd=str(root), text=True, capture_output=True,
    )
    try:
        drift_payload = json.loads(drift_check.stdout or '{}')
    except json.JSONDecodeError:
        drift_payload = {'problems': ['check_contract_drift.py 输出不是 JSON'],
                         'stderr': drift_check.stderr}
    checks['contract_drift'] = drift_payload
    if drift_check.returncode != 0:
        for problem in drift_payload.get('problems') or ['contract drift check failed']:
            errors.append(f'contract drift: {problem}')

    # 蒸馏版本新鲜度：**warning 不是 error**。
    #   用户裁定「下限以下的不需要重新蒸馏，整体完成后再统一重蒸」，
    #   所以它不能阻塞发行；但也不能不说——不说就等于没记账。
    freshness = subprocess.run(
        [sys.executable, str(root / 'scripts' / 'check_distillation_freshness.py'), '--json'],
        cwd=str(root), text=True, capture_output=True,
    )
    try:
        freshness_payload = json.loads(freshness.stdout or '{}')
    except json.JSONDecodeError:
        freshness_payload = {'error': (freshness.stderr or '').strip()[:200]}
    checks['distillation_freshness'] = {
        k: v for k, v in freshness_payload.items() if not k.endswith('_detail')
    }
    if freshness_payload.get('below_floor'):
        warnings.append(
            f"{freshness_payload['below_floor']} 人低于兼容下限 "
            f"{freshness_payload.get('floor')}（按裁定不重蒸，进重蒸台账）")
    if freshness_payload.get('unknown'):
        warnings.append(
            f"{freshness_payload['unknown']} 人的 distilled_with 归因不到，不计入达标")
    if freshness_payload.get('upper_bound_only'):
        warnings.append(
            f"{freshness_payload['upper_bound_only']} 人的 distilled_with 是批量重打包的上界值，"
            f"只重打包未重蒸，实际正文更旧")

    test_result = None
    if not args.skip_tests:
        completed = subprocess.run(
            [sys.executable, '-m', 'unittest', 'discover', '-s', str(root / 'tests'), '-v'],
            cwd=str(root), text=True, capture_output=True,
        )
        test_result = {'returncode': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr}
        if completed.returncode != 0:
            errors.append('offline unittest suite failed')
    checks['tests'] = test_result

    result = {'passed': not errors, 'root': str(root), 'checks': checks, 'warnings': warnings, 'errors': errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
