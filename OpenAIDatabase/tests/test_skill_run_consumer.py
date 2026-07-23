from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


DATABASE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DATABASE_ROOT.parent
GOVERNANCE_TOOLS = REPO_ROOT / "CodexSkills/governance/tools"
sys.path.insert(0, str(GOVERNANCE_TOOLS))

from canonical_json import canonical_digest, canonicalize_object  # noqa: E402


CANDIDATE_GIT_OBJECT = "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
CANDIDATE_DIGEST = (
    "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
)
PRE_RELOCATION_GIT_OBJECT = (
    "sha1:4b1e1a318c8f9e1014839a8a3a46e057679c4b6b"
)
PRE_RELOCATION_DIGEST = (
    "fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1"
)
SCHEMA_ID = "urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2"
PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"


def load_script(name: str):
    script = DATABASE_ROOT / f"scripts/{name}.py"
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    scripts_dir = str(DATABASE_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec.loader.exec_module(module)
    return module


def make_database(root: Path) -> None:
    shutil.copytree(
        DATABASE_ROOT / "config/evaluation",
        root / "config/evaluation",
    )
    target = root / "data/run_logs/skills_runs"
    target.mkdir(parents=True)
    shutil.copy(
        DATABASE_ROOT / "data/run_logs/skills_runs/README.md",
        target / "README.md",
    )


def uid(prefix: str, discriminator: str = "0") -> str:
    return f"{prefix}_{discriminator}{'0' * 25}"


def reseal(value: dict) -> dict:
    result = copy.deepcopy(value)
    result["event_digest"] = "0" * 64
    result["event_digest"] = canonical_digest(result, "/event_digest")
    return result


def valid_unknown_event() -> dict:
    value = {
        "schema_version": SCHEMA_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_DIGEST,
        "event_uid": uid("evt"),
        "run_uid": uid("run"),
        "event_type": "RUN_OBSERVED",
        "occurred_at": "2026-07-23T00:01:00.000000Z",
        "surface_class": "CODEX_AUTOMATION",
        "actor_role": "AUTOMATION",
        "adapter_id": "run-observer-adapter",
        "adapter_version": "2.0.0",
        "adapter_schema_digest": "b" * 64,
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:run-mapping:v1"
        ),
        "mapping_policy_digest": "c" * 64,
        "trigger_kind": "MANUAL",
        "run_status": "SUCCESS",
        "model_ref": "gpt-5-6-sol",
        "reasoning_effort": "ULTRA",
        "metrics": {
            "duration_ms": 1000,
            "tool_call_count": 2,
            "input_tokens": None,
            "output_tokens": None,
            "token_usage_status": "UNAVAILABLE",
        },
        "binding_state": "UNKNOWN",
        "unknown_reason_code": "MAPPING_NOT_PROVABLE",
        "redaction": {
            "policy_snapshot_digest": "b" * 64,
            "unknown_fields_dropped": 0,
            "omitted_category_codes": [],
            "post_serialization_scan_passed": True,
        },
        "immutable": True,
        "event_digest": "0" * 64,
    }
    return reseal(value)


class SkillRunConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.consumer = load_script("validate_skill_run_logs")

    def test_trust_tuple_matches_relocated_candidate(self) -> None:
        contract = self.consumer.load_consumer_contract(
            DATABASE_ROOT / self.consumer.CONFIG_PATH
        )
        self.assertEqual(
            contract.trust.verified_git_object_id,
            CANDIDATE_GIT_OBJECT,
        )
        self.assertEqual(contract.trust.expected_bundle_digest, CANDIDATE_DIGEST)
        self.assertEqual(contract.expected_bundle_digest, CANDIDATE_DIGEST)

    def test_pre_relocation_candidate_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            config_path = database / self.consumer.CONFIG_PATH
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["candidate_trust"].update(
                {
                    "expected_bundle_digest": PRE_RELOCATION_DIGEST,
                    "verified_git_object_id": PRE_RELOCATION_GIT_OBJECT,
                }
            )
            config_path.write_text(
                json.dumps(config, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertEqual(
            errors,
            [
                "skill_run_consumer_bootstrap_failed:"
                "TRUST_SCHEMA_PATH_OWNER_MISMATCH"
            ],
        )

    def test_empty_preactivation_root_passes_trusted_consumer_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertEqual(errors, [])

    def test_direct_or_unknown_files_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            root = database / "data/run_logs/skills_runs"
            (root / "example.jsonl").write_text("{}\n", encoding="utf-8")
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertIn("skill_run_unapproved_path", errors)
        self.assertNotIn("example.jsonl", "\n".join(errors))

    def test_final_layout_is_recognized_but_publication_remains_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            part = (
                database
                / "data/run_logs/skills_runs/2026/07/23/part-0001.jsonl"
            )
            part.parent.mkdir(parents=True)
            part.write_text("{}\n", encoding="utf-8")
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertEqual(
            errors,
            [
                "skill_run_canonical_publication_blocked:"
                "2026/07/23/part-0001.jsonl"
            ],
        )

    def test_unapproved_empty_directory_and_part_gap_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            root = database / "data/run_logs/skills_runs"
            (root / "unexpected").mkdir()
            part = root / "2026/07/23/part-0002.jsonl"
            part.parent.mkdir(parents=True)
            part.write_text("{}\n", encoding="utf-8")
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertIn("skill_run_unapproved_directory", errors)
        self.assertIn("skill_run_part_sequence_invalid:2026/07/23", errors)
        self.assertTrue(
            any(
                error.startswith("skill_run_canonical_publication_blocked:")
                for error in errors
            )
        )

    def test_symlink_entry_is_never_followed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            root = database / "data/run_logs/skills_runs"
            outside = database / "outside"
            outside.mkdir()
            (root / "2026").symlink_to(outside, target_is_directory=True)
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertIn("skill_run_tree_unsafe_entry", errors)

    def test_tree_scan_has_a_hard_entry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            root = database / "data/run_logs/skills_runs"
            (root / "extra.txt").write_text("x", encoding="utf-8")
            with mock.patch.object(self.consumer, "MAX_TREE_ENTRIES", 1):
                errors = self.consumer.validate_skill_run_logs(
                    database,
                    repo_root=REPO_ROOT,
                )
        self.assertIn("skill_run_tree_entry_limit_exceeded", errors)

    def test_config_parent_symlink_is_never_followed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            evaluation = database / "config/evaluation"
            outside = database / "outside-evaluation"
            evaluation.rename(outside)
            evaluation.symlink_to(outside, target_is_directory=True)
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertTrue(
            errors[0].startswith("skill_run_consumer_bootstrap_failed:")
        )

    def test_config_file_symlink_is_never_followed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            config = database / self.consumer.CONFIG_PATH
            outside = database / "outside-config.json"
            config.rename(outside)
            config.symlink_to(outside)
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertTrue(
            errors[0].startswith("skill_run_consumer_bootstrap_failed:")
        )

    def test_part_parser_enforces_jcs_lf_date_and_size(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            contract = self.consumer.load_consumer_contract(
                database / self.consumer.CONFIG_PATH
            )
            bundle = self.consumer.load_trusted_bundle(
                REPO_ROOT,
                contract.trust,
            )
            events, errors = self.consumer.validate_part_bytes(
                canonicalize_object(valid_unknown_event()) + b"\n",
                relative_path="2026/07/23/part-0001.jsonl",
                bundle=bundle,
                contract=contract,
            )
            _events, framing_errors = self.consumer.validate_part_bytes(
                b"{}",
                relative_path="2026/07/23/part-0001.jsonl",
                bundle=bundle,
                contract=contract,
            )
            _events, path_errors = self.consumer.validate_part_bytes(
                b"{}\n",
                relative_path="2026/02/30/part-0001.jsonl",
                bundle=bundle,
                contract=contract,
            )
        self.assertEqual(len(events), 1)
        self.assertEqual(errors, [])
        self.assertTrue(
            any(
                "skill_run_part_final_lf_required" in error
                for error in framing_errors
            )
        )
        self.assertEqual(
            path_errors,
            ["skill_run_part_date_invalid:2026/02/30/part-0001.jsonl"],
        )

    def test_part_parser_rejects_zero_part_wrong_day_and_bad_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            contract = self.consumer.load_consumer_contract(
                database / self.consumer.CONFIG_PATH
            )
            bundle = self.consumer.load_trusted_bundle(
                REPO_ROOT,
                contract.trust,
            )
            event = valid_unknown_event()
            raw = canonicalize_object(event) + b"\n"
            _events, zero_errors = self.consumer.validate_part_bytes(
                raw,
                relative_path="2026/07/23/part-0000.jsonl",
                bundle=bundle,
                contract=contract,
            )
            _events, date_errors = self.consumer.validate_part_bytes(
                raw,
                relative_path="2026/07/22/part-0001.jsonl",
                bundle=bundle,
                contract=contract,
            )
            later = copy.deepcopy(event)
            later["event_uid"] = uid("evt", "1")
            later["occurred_at"] = "2026-07-23T00:02:00.000000Z"
            earlier = copy.deepcopy(event)
            earlier["event_uid"] = uid("evt", "2")
            ordered_raw = (
                canonicalize_object(reseal(later))
                + b"\n"
                + canonicalize_object(reseal(earlier))
                + b"\n"
            )
            _events, order_errors = self.consumer.validate_part_bytes(
                ordered_raw,
                relative_path="2026/07/23/part-0001.jsonl",
                bundle=bundle,
                contract=contract,
            )
        self.assertEqual(
            zero_errors,
            ["skill_run_part_number_invalid:2026/07/23/part-0000.jsonl"],
        )
        self.assertIn(
            "skill_run_event_shard_date_mismatch:"
            "2026/07/22/part-0001.jsonl:1",
            date_errors,
        )
        self.assertIn(
            "skill_run_part_order_invalid:2026/07/23/part-0001.jsonl",
            order_errors,
        )

    def test_invalid_event_diagnostic_never_echoes_rejected_value(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            contract = self.consumer.load_consumer_contract(
                database / self.consumer.CONFIG_PATH
            )
            bundle = self.consumer.load_trusted_bundle(
                REPO_ROOT,
                contract.trust,
            )
            invalid = valid_unknown_event()
            invalid["prompt"] = "sensitive-marker-must-not-echo"
            _events, errors = self.consumer.validate_part_bytes(
                canonicalize_object(reseal(invalid)) + b"\n",
                relative_path="2026/07/23/part-0001.jsonl",
                bundle=bundle,
                contract=contract,
            )
        rendered = "\n".join(errors)
        self.assertIn("SCHEMA_VALIDATION_FAILED", rendered)
        self.assertNotIn("sensitive-marker-must-not-echo", rendered)

    def test_config_duplicate_keys_fail_before_trust_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            make_database(database)
            config = database / self.consumer.CONFIG_PATH
            config.write_bytes(b'{"schema_version":"a","schema_version":"b"}')
            errors = self.consumer.validate_skill_run_logs(
                database,
                repo_root=REPO_ROOT,
            )
        self.assertTrue(
            errors[0].startswith("skill_run_consumer_bootstrap_failed:")
        )


if __name__ == "__main__":
    unittest.main()
