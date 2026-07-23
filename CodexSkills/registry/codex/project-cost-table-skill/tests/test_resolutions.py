from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.resolutions import (
    ResolutionError,
    input_resolution_from_mapping,
    load_input_resolution,
    persist_input_resolution,
    validate_resolution_bindings,
)


def valid_mapping() -> dict[str, object]:
    return {
        "schema_version": "kmfa.project_cost.input_resolution.v1",
        "resolution_id": "resolution_" + "1" * 32,
        "run_id": "RUN-R3-SYNTHETIC",
        "recorded_at": "2000-01-01T00:00:00+00:00",
        "bound_request_hash": "2" * 64,
        "resulting_request_hash": "3" * 64,
        "bound_manifest_sha256": "4" * 64,
        "bound_requirements_sha256": "5" * 64,
        "items": [
            {
                "requirement_id": "POLICY:synthetic",
                "classification": "NON_WAIVABLE",
                "resolution": "QUALIFIED_ALTERNATE_EVIDENCE",
                "user_instruction": "use the supplied synthetic alternate",
                "user_instruction_ref": "instruction:synthetic-1",
                "affected_metrics": ["COST_PAID"],
                "effect_on_scope_or_metrics": "COST_PAID remains in scope after evidence revalidation",
                "evidence_refs": ["evidence:synthetic-1"],
            }
        ],
    }


class ResolutionTests(unittest.TestCase):
    def test_valid_resolution_matches_schema_and_loader(self) -> None:
        mapping = valid_mapping()
        schema = json.loads((MODULE_ROOT / "schemas" / "input_resolution.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(mapping)), [])
        resolution = input_resolution_from_mapping(mapping)
        self.assertEqual(resolution.items[0].resolution, "QUALIFIED_ALTERNATE_EVIDENCE")

    def test_non_waivable_omission_and_missing_instruction_or_evidence_fail(self) -> None:
        cases = []
        omission = valid_mapping()
        omission["items"][0]["resolution"] = "OMIT_OPTIONAL_PRESENTATION"
        cases.append((omission, "RESOLUTION_NOT_ALLOWED"))
        missing_instruction = valid_mapping()
        missing_instruction["items"][0]["user_instruction"] = None
        cases.append((missing_instruction, "USER_INSTRUCTION_REQUIRED"))
        missing_evidence = valid_mapping()
        missing_evidence["items"][0]["evidence_refs"] = []
        cases.append((missing_evidence, "EVIDENCE_REQUIRED"))
        for mapping, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(ResolutionError) as caught:
                    input_resolution_from_mapping(mapping)
                self.assertEqual(caught.exception.code, code)

    def test_scope_reduction_requires_affected_metrics(self) -> None:
        mapping = valid_mapping()
        item = mapping["items"][0]
        item["resolution"] = "SCOPE_REDUCED"
        item["evidence_refs"] = []
        item["affected_metrics"] = []
        with self.assertRaises(ResolutionError) as caught:
            input_resolution_from_mapping(mapping)
        self.assertEqual(caught.exception.code, "AFFECTED_METRICS_REQUIRED")

    def test_finance_owner_or_other_unknown_fields_are_rejected(self) -> None:
        mapping = valid_mapping()
        mapping["finance_owner"] = "nobody"
        with self.assertRaises(ResolutionError) as caught:
            input_resolution_from_mapping(mapping)
        self.assertEqual(caught.exception.code, "RESOLUTION_SCHEMA_DRIFT")

    def test_bindings_reject_stale_request_manifest_and_config(self) -> None:
        resolution = input_resolution_from_mapping(valid_mapping())
        valid = {
            "run_id": resolution.run_id,
            "bound_request_hash": resolution.bound_request_hash,
            "resulting_request_hash": resolution.resulting_request_hash,
            "manifest_sha256": resolution.bound_manifest_sha256,
            "requirements_sha256": resolution.bound_requirements_sha256,
        }
        validate_resolution_bindings(resolution, **valid)
        cases = [
            (dict(valid, bound_request_hash="9" * 64), "RESOLUTION_BOUND_REQUEST_STALE"),
            (dict(valid, resulting_request_hash="9" * 64), "RESOLUTION_REQUEST_STALE"),
            (dict(valid, manifest_sha256="9" * 64), "RESOLUTION_MANIFEST_STALE"),
            (dict(valid, requirements_sha256="9" * 64), "RESOLUTION_CONFIG_STALE"),
        ]
        for values, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(ResolutionError) as caught:
                    validate_resolution_bindings(resolution, **values)
                self.assertEqual(caught.exception.code, code)

    def test_persistence_is_append_only_and_single_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "private_runtime"
            resolution = input_resolution_from_mapping(valid_mapping())
            path = persist_input_resolution(runtime, resolution)
            self.assertEqual(load_input_resolution(path), resolution)
            self.assertEqual(path.stat().st_nlink, 1)
            with self.assertRaises(ResolutionError) as caught:
                persist_input_resolution(runtime, resolution)
            self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")


if __name__ == "__main__":
    unittest.main()
