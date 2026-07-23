from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from persona_registry import (
    CATEGORIES,
    next_product_version,
    next_product_version_for,
    register_product,
    subject_uid,
    validate_registry,
    write_index,
)
from delivery_builder import build_full_delivery


def initialize_registry(root: Path) -> None:
    for category in CATEGORIES:
        folder = root / category['folder']
        folder.mkdir(parents=True)
        (folder / '_category.json').write_text(json.dumps({
            'schema_version': '3.0',
            'folder': category['folder'],
            'identity_family_id': category['identity_family_id'],
            'identity_mode': category['identity_mode'],
        }, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    write_index(root)


def create_product_zip(
    path: Path,
    *,
    name: str = 'Example Person',
    slug: str = 'example-person',
    primary: str = 'technical-engineer',
    mode: str = 'single',
    origin: str = 'public',
    model_version: str = '0.1.0',
    product_version: str = '0.0.0.1',
) -> Path:
    top = slug
    selection = {
        'mode': mode,
        'primary': primary,
        'weights': {primary: 1.0},
        'canonical': primary,
    }
    meta = {
        'name': name,
        'slug': slug,
        'subject_origin': origin,
        'identity_selection': selection,
        'model_version': model_version,
        'product_version': product_version,
        'runtime_invocation_versioning': False,
    }
    payloads = {
        'SKILL.md': f'---\nname: {slug}\ndescription: Synthetic registry fixture.\n---\n',
        'meta.json': json.dumps(meta, ensure_ascii=False, sort_keys=True) + '\n',
    }
    records = [
        {'path': relative, 'sha256': hashlib.sha256(content.encode()).hexdigest(), 'size': len(content.encode())}
        for relative, content in sorted(payloads.items())
    ]
    checksums = ''.join(f'{item["sha256"]}  {item["path"]}\n' for item in records)
    manifest = {
        'schema_version': '2.0',
        'name': slug,
        'target_name': name,
        'builder': 'persona-distiller',
        'builder_version': 'v0.0.0.5',
        'product_version': product_version,
        'model_version': model_version,
        'created_at': '2026-07-23T00:00:00Z',
        'top_level_count': 1,
        'privacy': {
            'raw_included': False,
            'holdout_included': False,
            'private_source_bodies_included': False,
            'runtime_history_reset': True,
        },
        'files': records,
    }
    runtime_path = path.with_name(path.stem + '.runtime.zip')
    with zipfile.ZipFile(runtime_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, content in payloads.items():
            archive.writestr(f'{top}/{relative}', content)
        archive.writestr(f'{top}/checksums.sha256', checksums)
        archive.writestr(f'{top}/PACKAGE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    category_by_identity = {
        'technical-engineer': 'technical-engineer',
        'entrepreneur-operator': 'entrepreneur-operator',
        'investor-capital-allocator': 'investor-capital-allocator',
        'developer-designer': 'developer-designer',
        'thinker-educator': 'thinker-educator',
        'political-legal': 'political-legal',
    }
    identity_family = 'multi-identity' if mode == 'multi' else category_by_identity[primary]
    card = {
        'schema_version': '1.0',
        'subject_uid': subject_uid(name, origin),
        'canonical_name': name,
        'subject_slug': slug,
        'identity_family_id': identity_family,
        'readiness': 'ready',
        'research_cutoff': '2026-07-23',
        'latest_product_version': product_version,
        'selection_reasons': ['Synthetic registry fixture.'],
        'distillation_traits': ['Evidence-bounded synthetic reasoning.'],
        'user_value': ['Tests canonical delivery registration.'],
        'application_scenarios': ['general-agentic-work'],
        'key_capabilities': ['Synthetic verification'],
        'hard_boundaries': ['Not a real person model.'],
    }
    audit = {
        name: {'schema_version': '1.0', 'status': 'passed'}
        for name in (
            'verification.json',
            'provenance.json',
            'source-coverage.json',
            'evaluation-summary.json',
            'review-record.json',
        )
    }
    build_full_delivery(
        runtime_path,
        path,
        team_card=card,
        audit=audit,
        created_at='2026-07-23T00:00:00Z',
    )
    return path


class PersonaRegistryTests(unittest.TestCase):
    def test_skill_root_layout_allows_non_registry_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_registry(root)
            (root / 'scripts').mkdir()
            self.assertTrue(validate_registry(root)['passed'])

    def test_missing_canonical_category_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_registry(root)
            (root / '技术工程师' / '_category.json').unlink()
            result = validate_registry(root)
            self.assertFalse(result['passed'])
            self.assertTrue(any('category manifest' in error for error in result['errors']))

    def test_single_identity_routes_to_exact_category_and_preserves_full_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            product = create_product_zip(root / 'person.zip')
            result = register_product(product, registry)
            self.assertEqual(result['category'], '技术工程师')
            self.assertEqual(result['product_version'], '0.0.0.1')
            self.assertTrue(Path(result['artifact']).is_file())
            self.assertTrue(validate_registry(registry)['passed'])

    def test_multi_identity_always_routes_to_multi_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            product = create_product_zip(
                root / 'person.zip',
                mode='multi',
                primary='developer-designer',
            )
            result = register_product(product, registry)
            self.assertEqual(result['category'], '多重身份')
            self.assertTrue(validate_registry(registry)['passed'])

    def test_registration_is_idempotent_for_same_version_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            product = create_product_zip(root / 'person.zip')
            register_product(product, registry)
            repeated = register_product(product, registry)
            self.assertEqual(repeated['action'], 'already-registered')
            self.assertEqual(validate_registry(registry)['products'], 1)

    def test_same_person_distillations_receive_contiguous_product_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            first = create_product_zip(root / 'one.zip', product_version='0.0.0.1')
            second = create_product_zip(
                root / 'two.zip',
                product_version='0.0.0.2',
                model_version='0.1.0',
            )
            register_product(first, registry)
            result = register_product(second, registry)
            registration = json.loads(Path(result['registration']).read_text(encoding='utf-8'))
            self.assertEqual(
                [item['product_version'] for item in registration['versions']],
                ['0.0.0.1', '0.0.0.2'],
            )
            self.assertTrue(validate_registry(registry)['passed'])

    def test_out_of_sequence_product_version_is_rejected_without_consuming_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            skipped = create_product_zip(root / 'skipped.zip', product_version='0.0.0.2')
            with self.assertRaisesRegex(ValueError, 'next product version.*0.0.0.1'):
                register_product(skipped, registry)
            self.assertEqual(validate_registry(registry)['products'], 0)
            self.assertEqual(next_product_version_for('Example Person', 'public', registry), '0.0.0.1')

    def test_product_version_range_starts_at_one_and_hard_stops_at_999(self) -> None:
        self.assertEqual(next_product_version([]), '0.0.0.1')
        self.assertEqual(
            next_product_version([
                {'product_version': f'0.0.0.{serial}'}
                for serial in range(1, 999)
            ]),
            '0.0.0.999',
        )
        with self.assertRaisesRegex(ValueError, 'exhausted'):
            next_product_version([
                {'product_version': f'0.0.0.{serial}'}
                for serial in range(1, 1000)
            ])

    def test_concurrent_competing_first_releases_cannot_both_take_same_number(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            candidates = [
                create_product_zip(root / 'one.zip', model_version='snapshot-a'),
                create_product_zip(root / 'two.zip', model_version='snapshot-b'),
            ]

            def attempt(path: Path) -> str:
                try:
                    return str(register_product(path, registry)['action'])
                except ValueError as exc:
                    return f'ERROR:{exc}'

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(attempt, candidates))
            self.assertEqual(sum(value == 'registered' for value in outcomes), 1)
            self.assertEqual(sum(value.startswith('ERROR:') for value in outcomes), 1)
            validation = validate_registry(registry)
            self.assertTrue(validation['passed'], validation)
            self.assertEqual(validation['artifacts'], 1)
            self.assertEqual(next_product_version_for('Example Person', 'public', registry), '0.0.0.2')

    def test_same_subject_cannot_be_registered_in_another_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            register_product(create_product_zip(root / 'one.zip'), registry)
            other = create_product_zip(
                root / 'two.zip',
                primary='thinker-educator',
            )
            with self.assertRaisesRegex(ValueError, 'already registered under'):
                register_product(other, registry)

    def test_private_product_is_rejected_from_public_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, 'private/self'):
                create_product_zip(root / 'private.zip', origin='private')


if __name__ == '__main__':
    unittest.main()
