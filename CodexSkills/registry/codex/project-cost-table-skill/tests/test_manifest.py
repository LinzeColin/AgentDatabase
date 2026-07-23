from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from jsonschema import Draft202012Validator, FormatChecker

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import project_cost_table.manifest as manifest_module
from project_cost_table.inventory import scan_inventory_metadata, source_id_for_relative_path
from project_cost_table.manifest import (
    ManifestError,
    SourceSchemaObservation,
    load_input_manifest,
    select_manifest_sources,
    selection_business_fingerprint,
    validate_manifest_request,
)
from r3_helpers import SCHEMA_FINGERPRINT, manifest_mapping, write_manifest, write_source


def observation(source_id: str, **changes: str) -> SourceSchemaObservation:
    values = {
        "source_id": source_id,
        "reader_version": "1.0.0",
        "schema_id": "schema.synthetic.v1",
        "schema_fingerprint": SCHEMA_FINGERPRINT,
        "security_profile_id": "LOCAL-FILE-SECURITY-V1",
        "security_status": "PREFLIGHT_PASS",
    }
    values.update(changes)
    return SourceSchemaObservation(**values)


class ManifestTests(unittest.TestCase):
    def test_public_template_matches_schema_but_is_not_runnable(self) -> None:
        schema = json.loads((MODULE_ROOT / "schemas" / "input_manifest.schema.json").read_text(encoding="utf-8"))
        template = yaml.safe_load((MODULE_ROOT / "config" / "input_manifest.template.yml").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(template)), [])
        self.assertTrue(all(slot["selected_source_id"] is None for slot in template["slots"].values()))
        self.assertTrue(all(slot["selected_sources"] == [] for slot in template["slots"].values()))

    def test_manifest_rejects_schema_drift_aliases_and_relaxed_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            write_source(raw, "source.dat")
            mapping = manifest_mapping(raw, {"general_ledger": "source.dat"})
            cases = []
            drift = dict(mapping, schema_version="kmfa.project_cost.input_manifest.v2")
            cases.append((drift, "MANIFEST_SCHEMA_DRIFT"))
            relaxed = dict(mapping)
            relaxed["selection_policy"] = dict(mapping["selection_policy"], mtime_is_authority=True)
            cases.append((relaxed, "SELECTION_POLICY_RELAXED"))
            unknown_top = dict(mapping, unknown_control=True)
            cases.append((unknown_top, "MANIFEST_SCHEMA_DRIFT"))
            unknown_slot = yaml.safe_load(yaml.safe_dump(mapping))
            unknown_slot["slots"]["general_ledger"]["finance_owner"] = "forbidden"
            cases.append((unknown_slot, "MANIFEST_SLOT_SCHEMA_DRIFT"))
            for index, (case, code) in enumerate(cases):
                path = write_manifest(root / ("case-%d.yml" % index), case)
                with self.subTest(code=code):
                    with self.assertRaises(ManifestError) as caught:
                        load_input_manifest(path)
                    self.assertEqual(caught.exception.code, code)
            alias_path = root / "alias.yml"
            alias_path.write_text(
                "schema_version: kmfa.project_cost.input_manifest.v3\nmanifest_id: &id X\ninput_root: *id\n",
                encoding="utf-8",
            )
            with self.assertRaises(ManifestError) as alias_error:
                load_input_manifest(alias_path)
            self.assertEqual(alias_error.exception.code, "MANIFEST_PARSE_ERROR")
            duplicate_path = root / "duplicate.yml"
            duplicate_path.write_text(
                yaml.safe_dump(mapping, sort_keys=False) + "manifest_id: SECOND_VALUE\n",
                encoding="utf-8",
            )
            with self.assertRaises(ManifestError) as duplicate_error:
                load_input_manifest(duplicate_path)
            self.assertEqual(duplicate_error.exception.code, "MANIFEST_PARSE_ERROR")

    def test_explicit_selection_with_multiple_candidates_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            write_source(raw, "one.dat", b"one")
            write_source(raw, "two.dat", b"two")
            mapping = manifest_mapping(raw, {"general_ledger": "two.dat"})
            mapping["slots"]["general_ledger"]["private_patterns"] = ["*.dat"]
            manifest = load_input_manifest(write_manifest(root / "manifest.yml", mapping))
            entries = scan_inventory_metadata(raw)
            source_id = source_id_for_relative_path("two.dat")
            selections = select_manifest_sources(
                manifest,
                input_root=raw,
                required_slot_ids=["general_ledger"],
                inventory_entries=tuple(reversed(entries)),
                schema_observations={source_id: observation(source_id)},
            )
            self.assertEqual(len(selections), 1)
            self.assertEqual(selections[0].source_id, source_id)
            self.assertEqual(len(selection_business_fingerprint(selections)), 64)

    def test_explicit_batch_selection_preserves_every_locked_source_in_one_slot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            first = write_source(raw, "first.dat", b"first")
            second = write_source(raw, "second.dat", b"second")
            mapping = manifest_mapping(raw, {"project_billing": "first.dat"})
            slot = mapping["slots"]["project_billing"]
            slot["private_patterns"] = ["*.dat"]
            slot["selected_source_id"] = None
            slot["selected_sha256"] = None
            slot["selected_sources"] = [
                {
                    "source_id": source_id_for_relative_path("second.dat"),
                    "sha256": hashlib.sha256(second.read_bytes()).hexdigest(),
                },
                {
                    "source_id": source_id_for_relative_path("first.dat"),
                    "sha256": hashlib.sha256(first.read_bytes()).hexdigest(),
                },
            ]
            manifest = load_input_manifest(write_manifest(root / "manifest.yml", mapping))
            entries = scan_inventory_metadata(raw)
            observations = {entry.source_id: observation(entry.source_id) for entry in entries}

            selections = select_manifest_sources(
                manifest,
                input_root=raw,
                required_slot_ids=["project_billing"],
                inventory_entries=tuple(reversed(entries)),
                schema_observations=observations,
            )

            self.assertEqual(len(selections), 2)
            self.assertEqual(
                [item.source_id for item in selections],
                sorted(entry.source_id for entry in entries),
            )
            self.assertEqual(
                selection_business_fingerprint(selections),
                selection_business_fingerprint(tuple(reversed(selections))),
            )

    def test_even_one_candidate_requires_explicit_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            write_source(raw, "one.dat")
            mapping = manifest_mapping(raw, {"general_ledger": "one.dat"})
            mapping["slots"]["general_ledger"]["selected_source_id"] = None
            mapping["slots"]["general_ledger"]["selected_sha256"] = None
            manifest = load_input_manifest(write_manifest(root / "manifest.yml", mapping))
            with self.assertRaises(ManifestError) as caught:
                select_manifest_sources(
                    manifest,
                    input_root=raw,
                    required_slot_ids=["general_ledger"],
                    inventory_entries=scan_inventory_metadata(raw),
                    schema_observations={},
                )
            self.assertEqual(caught.exception.code, "SLOT_SELECTION_REQUIRED")

    def test_formal_selection_rehashes_and_detects_digest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            source = write_source(raw, "one.dat", b"original")
            mapping = manifest_mapping(raw, {"general_ledger": "one.dat"})
            manifest = load_input_manifest(write_manifest(root / "manifest.yml", mapping))
            entries = scan_inventory_metadata(raw)
            source_id = entries[0].source_id
            source.write_bytes(b"changed")
            with mock.patch.object(
                manifest_module,
                "verify_source_file",
                wraps=manifest_module.verify_source_file,
            ) as digest_call:
                with self.assertRaises(ManifestError) as caught:
                    select_manifest_sources(
                        manifest,
                        input_root=raw,
                        required_slot_ids=["general_ledger"],
                        inventory_entries=entries,
                        schema_observations={source_id: observation(source_id)},
                    )
            self.assertEqual(caught.exception.code, "SOURCE_DIGEST_DRIFT")
            self.assertEqual(digest_call.call_count, 1)

    def test_schema_reader_and_security_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            write_source(raw, "one.dat")
            manifest = load_input_manifest(
                write_manifest(root / "manifest.yml", manifest_mapping(raw, {"general_ledger": "one.dat"}))
            )
            entries = scan_inventory_metadata(raw)
            source_id = entries[0].source_id
            cases = [
                (observation(source_id, schema_fingerprint="2" * 64), "SOURCE_SCHEMA_DRIFT"),
                (observation(source_id, reader_version="2.0.0"), "READER_VERSION_DRIFT"),
                (observation(source_id, security_status="NOT_RUN"), "SOURCE_SECURITY_NOT_VERIFIED"),
            ]
            for observed, code in cases:
                with self.subTest(code=code):
                    with self.assertRaises(ManifestError) as caught:
                        select_manifest_sources(
                            manifest,
                            input_root=raw,
                            required_slot_ids=["general_ledger"],
                            inventory_entries=entries,
                            schema_observations={source_id: observed},
                        )
                    self.assertEqual(caught.exception.code, code)

    def test_mtime_and_enumeration_order_do_not_change_business_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            source = write_source(raw, "one.dat")
            manifest = load_input_manifest(
                write_manifest(root / "manifest.yml", manifest_mapping(raw, {"general_ledger": "one.dat"}))
            )
            entries = scan_inventory_metadata(raw)
            source_id = entries[0].source_id
            first = select_manifest_sources(
                manifest,
                input_root=raw,
                required_slot_ids=["general_ledger"],
                inventory_entries=entries,
                schema_observations={source_id: observation(source_id)},
            )
            metadata = source.stat()
            os.utime(source, ns=(metadata.st_atime_ns, metadata.st_mtime_ns + 1_000_000_000))
            second = select_manifest_sources(
                manifest,
                input_root=raw,
                required_slot_ids=["general_ledger"],
                inventory_entries=tuple(reversed(scan_inventory_metadata(raw))),
                schema_observations={source_id: observation(source_id)},
            )
            self.assertNotEqual(first[0].identity.mtime_ns, second[0].identity.mtime_ns)
            self.assertEqual(selection_business_fingerprint(first), selection_business_fingerprint(second))

    def test_manifest_request_conflicts_and_reference_calculate_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            write_source(raw, "reference.dat")
            mapping = manifest_mapping(raw, {"reference_reports": "reference.dat"})
            mapping["slots"]["reference_reports"]["prohibited_in_calculate"] = True
            manifest = load_input_manifest(write_manifest(root / "manifest.yml", mapping))
            with self.assertRaises(ManifestError) as caught:
                validate_manifest_request(
                    manifest,
                    mode="calculate",
                    requested_metrics=["COST_PAID"],
                    requested_basis_ids=["CASH_VERIFIED"],
                    project_selector={"project_code": "SYNTHETIC-PROJECT"},
                    as_of="2000-01-31",
                )
            self.assertEqual(caught.exception.code, "REFERENCE_SELECTED_IN_CALCULATE")
            with self.assertRaises(ManifestError) as restate_caught:
                validate_manifest_request(
                    manifest,
                    mode="restate",
                    requested_metrics=["COST_PAID"],
                    requested_basis_ids=["CASH_VERIFIED"],
                    project_selector={"project_code": "SYNTHETIC-PROJECT"},
                    as_of="2000-01-31",
                )
            self.assertEqual(restate_caught.exception.code, "REFERENCE_SELECTED_IN_CALCULATE")

    def test_reference_slot_must_lock_calculate_isolation_and_replay_needs_no_manifest_metric_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            write_source(raw, "reference.dat")
            relaxed = manifest_mapping(raw, {"reference_reports": "reference.dat"})
            with self.assertRaises(ManifestError) as caught:
                load_input_manifest(write_manifest(root / "relaxed.yml", relaxed))
            self.assertEqual(caught.exception.code, "REFERENCE_CALCULATE_ISOLATION_RELAXED")

            locked = manifest_mapping(raw, {"reference_reports": "reference.dat"})
            locked["slots"]["reference_reports"]["prohibited_in_calculate"] = True
            manifest = load_input_manifest(write_manifest(root / "locked.yml", locked))
            validate_manifest_request(
                manifest,
                mode="reference-replay",
                requested_metrics=[],
                requested_basis_ids=["CASH_VERIFIED"],
                project_selector={"project_code": "SYNTHETIC-PROJECT"},
                as_of="2000-01-31",
            )


if __name__ == "__main__":
    unittest.main()
