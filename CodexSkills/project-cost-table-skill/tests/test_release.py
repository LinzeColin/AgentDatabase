import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.current_reconstruction import (  # noqa: E402
    CURRENT_BASIS_IDS,
    CURRENT_METRICS,
    CURRENT_REQUIREMENT_SPECS,
    metadata_fingerprint,
)
from project_cost_table.inventory import scan_inventory_metadata, verify_source_file  # noqa: E402
from project_cost_table.release import (  # noqa: E402
    PerformanceBudget,
    PerformanceSample,
    ReleaseError,
    evaluate_performance,
    measure_bound_snapshot_once,
    publish_performance_summary,
    release_code_fingerprint,
    verify_performance_bundle,
)


def _sample(
    *,
    phase="SUBSEQUENT_PROCESS",
    sample_index=1,
    wall_time_ns=100,
    peak_rss_bytes=1000,
    full_digest_verification_count=2,
    max_full_digest_verifications_per_source=1,
    candidate_pairs=0,
    application_cache_hits=0,
    full_digest_required=True,
    full_digest_completed=True,
    global_unpartitioned_matching=False,
):
    return PerformanceSample.from_mapping(
        {
            "phase": phase,
            "sample_index": sample_index,
            "wall_time_ns": wall_time_ns,
            "cpu_time_ns": 80,
            "peak_rss_bytes": peak_rss_bytes,
            "bytes_read": 20,
            "inventory_entry_count": 3,
            "selected_source_count": 2,
            "full_digest_verification_count": full_digest_verification_count,
            "max_full_digest_verifications_per_source": max_full_digest_verifications_per_source,
            "archive_members_parsed": 0,
            "business_files_parsed": 0,
            "rows_parsed": 0,
            "candidate_pairs": candidate_pairs,
            "application_cache_hits": application_cache_hits,
            "full_digest_required": full_digest_required,
            "full_digest_completed": full_digest_completed,
            "global_unpartitioned_matching": global_unpartitioned_matching,
        }
    )


def _hardware():
    return {
        "operating_system": "TestOS",
        "machine_architecture": "test64",
        "logical_cpu_count": 4,
        "python_implementation": "CPython",
        "python_version": "3.12.1",
    }


def _budget_mapping():
    return yaml.safe_load((MODULE_ROOT / "config" / "performance_budgets.yml").read_text(encoding="utf-8"))


class ReleaseBudgetTests(unittest.TestCase):
    def setUp(self):
        self.budget = PerformanceBudget.from_yaml(MODULE_ROOT / "config" / "performance_budgets.yml")

    def test_public_budget_and_schemas_are_strict(self):
        self.assertEqual(self.budget.public_dict()["max_wall_regression_factor"], "1.50")
        self.assertFalse(self.budget.global_unpartitioned_matching_allowed)
        self.assertFalse(self.budget.application_cache_allowed)
        for name in ("performance_budget.schema.json", "performance_summary.schema.json"):
            schema = json.loads((MODULE_ROOT / "schemas" / name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        budget_schema = json.loads(
            (MODULE_ROOT / "schemas" / "performance_budget.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(budget_schema).iter_errors(_budget_mapping())), [])

    def test_relaxed_or_coerced_budget_is_rejected(self):
        mutations = (
            (lambda value: value["baseline"].__setitem__("max_wall_regression_factor", "1.51"), "WALL_REGRESSION_FACTOR"),
            (lambda value: value["baseline"].__setitem__("cold_process_runs", True), "COLD_RUN_COUNT"),
            (lambda value: value["workload"].__setitem__("candidate_pair_budget_max", 1_000_001), "CANDIDATE_PAIR_BUDGET"),
            (lambda value: value["workload"].__setitem__("selected_full_digest_verifications_per_source_max", 2), "DIGEST_VERIFICATION_MAX"),
            (lambda value: value["workload"].__setitem__("global_unpartitioned_matching_allowed", True), "GLOBAL_MATCHING_POLICY"),
            (lambda value: value["release_gates"].__setitem__("staged_privacy_scan_required", False), "STAGED_PRIVACY_GATE"),
            (lambda value: value["release_gates"].__setitem__("global_install_in_r12_allowed", True), "GLOBAL_INSTALL_BOUNDARY"),
        )
        for mutate, code in mutations:
            with self.subTest(code=code):
                value = copy.deepcopy(_budget_mapping())
                mutate(value)
                with self.assertRaisesRegex(ReleaseError, "^%s:" % code):
                    PerformanceBudget.from_mapping(value)

    def test_exact_factor_boundary_passes_and_one_nanosecond_over_fails(self):
        baseline = _sample(phase="COLD_PROCESS", wall_time_ns=100, peak_rss_bytes=1000)
        passing = [
            baseline,
            _sample(sample_index=1, wall_time_ns=150, peak_rss_bytes=1500),
            _sample(sample_index=2, wall_time_ns=120, peak_rss_bytes=1400),
            _sample(sample_index=3, wall_time_ns=90, peak_rss_bytes=1000),
        ]
        result = evaluate_performance(self.budget, passing, hardware=_hardware())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["issues"], [])
        for field, value, issue in (
            ("wall_time_ns", 151, "WALL_TIME_REGRESSION"),
            ("peak_rss_bytes", 1501, "PEAK_RSS_REGRESSION"),
        ):
            kwargs = {field: value, "sample_index": 1}
            failed = [baseline, _sample(**kwargs), _sample(sample_index=2), _sample(sample_index=3)]
            observed = evaluate_performance(self.budget, failed, hardware=_hardware())
            self.assertEqual(observed["status"], "FAILED")
            self.assertIn(issue, observed["issues"])

    def test_resource_and_algorithm_guards_fail_closed(self):
        baseline = _sample(phase="COLD_PROCESS")
        mutations = (
            ({"max_full_digest_verifications_per_source": 2}, "SOURCE_PARSED_OR_HASHED_MORE_THAN_ONCE"),
            ({"candidate_pairs": 1_000_001}, "CANDIDATE_PAIR_BUDGET_EXCEEDED"),
            ({"global_unpartitioned_matching": True}, "GLOBAL_UNPARTITIONED_MATCHING_FORBIDDEN"),
            ({"application_cache_hits": 1}, "APPLICATION_CACHE_FORBIDDEN"),
            ({"full_digest_completed": False}, "FULL_DIGEST_NOT_COMPLETED"),
            ({"full_digest_verification_count": 1}, "DIGEST_VERIFICATION_COUNT_MISMATCH"),
        )
        for kwargs, issue in mutations:
            with self.subTest(issue=issue):
                samples = [baseline, _sample(sample_index=1, **kwargs), _sample(sample_index=2), _sample(sample_index=3)]
                result = evaluate_performance(self.budget, samples, hardware=_hardware())
                self.assertEqual(result["status"], "FAILED")
                self.assertIn(issue, result["issues"])

    def test_same_scope_cannot_silently_read_less_work(self):
        baseline = _sample(phase="COLD_PROCESS")
        changed = _sample(sample_index=1)
        changed = PerformanceSample.from_mapping({**changed.as_dict(), "bytes_read": changed.bytes_read - 1})
        result = evaluate_performance(
            self.budget,
            [baseline, changed, _sample(sample_index=2), _sample(sample_index=3)],
            hardware=_hardware(),
        )
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("WORKLOAD_SCOPE_DRIFT", result["issues"])

    def test_sample_order_is_metamorphic_and_public_summary_is_aggregate_only(self):
        samples = [
            _sample(phase="COLD_PROCESS"),
            _sample(sample_index=1),
            _sample(sample_index=2),
            _sample(sample_index=3),
        ]
        forward = evaluate_performance(self.budget, samples, hardware=_hardware())
        reverse = evaluate_performance(self.budget, tuple(reversed(samples)), hardware=_hardware())
        self.assertEqual(forward, reverse)
        encoded = json.dumps(forward, ensure_ascii=False, sort_keys=True)
        for prohibited in (
            "private_relative_path",
            "source_id",
            "source_sha256",
            "business_amount",
            "KMFA_" + "MetaData",
        ):
            self.assertNotIn(prohibited, encoded)
        self.assertEqual(forward["real_calculation_baseline_status"], "NOT_EVALUATED_BLOCKED_SOURCE")
        self.assertFalse(forward["company_approval_state_managed"])
        self.assertFalse(forward["global_install_performed"])
        self.assertEqual(forward["product_version"], "0.2.0")
        self.assertEqual(len(forward["performance_budget_sha256"]), 64)
        summary_schema = json.loads(
            (MODULE_ROOT / "schemas" / "performance_summary.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(summary_schema).iter_errors(forward)), [])

    def test_release_code_fingerprint_is_stable_and_content_bound(self):
        first = release_code_fingerprint(MODULE_ROOT)
        second = release_code_fingerprint(MODULE_ROOT)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_published_bundle_is_atomic_sealed_and_locatable(self):
        samples = [
            _sample(phase="COLD_PROCESS"),
            _sample(sample_index=1),
            _sample(sample_index=2),
            _sample(sample_index=3),
        ]
        summary = evaluate_performance(self.budget, samples, hardware=_hardware())
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "release-performance"
            published = publish_performance_summary(summary, output_dir=output)
            self.assertTrue(published.output_dir.is_absolute())
            self.assertTrue(verify_performance_bundle(output))
            self.assertIn(str(output), published.locator_text())
            with self.assertRaisesRegex(ReleaseError, "OUTPUT_DIR_INVALID"):
                publish_performance_summary(summary, output_dir=output)


class BoundSnapshotBenchmarkTests(unittest.TestCase):
    def _build_contract(self, root: Path, contract_path: Path) -> str:
        entries = scan_inventory_metadata(root)
        selected = []
        for index, entry in enumerate(entries, start=1):
            verified = verify_source_file(root, entry)
            selected.append(
                {
                    "slot_id": "source_slot_%d" % index,
                    "source_id": entry.source_id,
                    "private_relative_path": entry.relative_path,
                    "sha256": verified.sha256,
                }
            )
        payload = {
            "schema_version": "kmfa.project_cost.current_source_contract.private.v1",
            "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
            "contract_id": "contract-r12-test",
            "input_root": str(root),
            "as_of": "2026-07-18",
            "scope": {
                "project_count": 1,
                "requested_metrics": list(CURRENT_METRICS),
                "requested_basis_ids": list(CURRENT_BASIS_IDS),
            },
            "source_snapshot": {
                "metadata_fingerprint": metadata_fingerprint(entries),
                "entry_count": len(entries),
                "total_size_bytes": sum(item.identity.size_bytes for item in entries),
                "unsafe_entry_count": 0,
                "task_pack_manifest_sha256": "a" * 64,
                "drift_review_sha256": "b" * 64,
                "drift_classification": "OUT_OF_SCOPE_INVENTORY_DRIFT_REVIEWED",
                "snapshot_overwritten": False,
            },
            "selected_sources": selected,
            "evidence_requirements": [
                {
                    "requirement_id": requirement_id,
                    "observed_status": "PRESENT",
                    "evidence_ref": "test-evidence:%s" % requirement_id.lower(),
                }
                for requirement_id in sorted(CURRENT_REQUIREMENT_SPECS)
            ],
            "calculate_source_boundary": {
                "baseline_values_allowed": False,
                "report_line_items_allowed": False,
                "replay_adapters_allowed": False,
            },
        }
        encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        contract_path.write_bytes(encoded)
        return hashlib.sha256(encoded).hexdigest()

    def test_each_selected_source_is_fully_verified_once_without_business_parse(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "raw"
            root.mkdir()
            (root / "one.bin").write_bytes(b"one" * 100)
            (root / "two.bin").write_bytes(b"two" * 100)
            contract = base / "contract.json"
            digest = self._build_contract(root, contract)
            sample = measure_bound_snapshot_once(
                phase="COLD_PROCESS",
                sample_index=1,
                input_root=root,
                contract_path=contract,
                contract_sha256=digest,
            )
            self.assertEqual(sample.selected_source_count, 2)
            self.assertEqual(sample.full_digest_verification_count, 2)
            self.assertEqual(sample.max_full_digest_verifications_per_source, 1)
            self.assertEqual(sample.business_files_parsed, 0)
            self.assertEqual(sample.archive_members_parsed, 0)
            self.assertEqual(sample.rows_parsed, 0)
            self.assertTrue(sample.full_digest_completed)

    def test_metadata_or_content_drift_blocks_benchmark(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "raw"
            root.mkdir()
            source = root / "one.bin"
            source.write_bytes(b"before")
            contract = base / "contract.json"
            digest = self._build_contract(root, contract)
            source.write_bytes(b"after-with-different-size")
            with self.assertRaisesRegex(ReleaseError, "CURRENT_SOURCE_METADATA_DRIFT"):
                measure_bound_snapshot_once(
                    phase="COLD_PROCESS",
                    sample_index=1,
                    input_root=root,
                    contract_path=contract,
                    contract_sha256=digest,
                )


if __name__ == "__main__":
    unittest.main()
