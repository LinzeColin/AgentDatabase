from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from persona_registry import CATEGORIES, register_product, validate_registry, write_index


def initialize_registry(root: Path) -> None:
    for category in CATEGORIES:
        folder = root / category['folder']
        folder.mkdir(parents=True)
        (folder / '_category.json').write_text(json.dumps({
            'schema_version': '1.0',
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
        'builder_version': 'v0.0.0.3',
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
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, content in payloads.items():
            archive.writestr(f'{top}/{relative}', content)
        archive.writestr(f'{top}/checksums.sha256', checksums)
        archive.writestr(f'{top}/PACKAGE_MANIFEST.json', json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return path


class PersonaRegistryTests(unittest.TestCase):
    def test_skill_root_layout_allows_non_registry_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_registry(root)
            (root / 'scripts').mkdir()
            self.assertTrue(validate_registry(root)['passed'])

    def test_legacy_nested_registry_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            initialize_registry(root)
            (root / '产物登记').mkdir()
            result = validate_registry(root)
            self.assertFalse(result['passed'])
            self.assertTrue(any('legacy nested registry directory' in error for error in result['errors']))

    def test_single_identity_routes_to_exact_category_and_preserves_full_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / 'registry'
            initialize_registry(registry)
            product = create_product_zip(root / 'person.zip')
            result = register_product(product, registry)
            self.assertEqual(result['category'], '技术工程')
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
            registry = root / 'registry'
            initialize_registry(registry)
            private = create_product_zip(root / 'private.zip', origin='private')
            with self.assertRaisesRegex(ValueError, 'private/self'):
                register_product(private, registry)


if __name__ == '__main__':
    unittest.main()
