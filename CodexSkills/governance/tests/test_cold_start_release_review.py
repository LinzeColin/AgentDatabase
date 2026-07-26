from __future__ import annotations

import copy
import hashlib
import inspect
import json
import unittest

from CodexSkills.governance.release.cold_start import review
from CodexSkills.governance.tools import build_cold_start_release_review as builder
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (
    load_au040_acceptance,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractError,
    scan_public_value,
)


class ColdStartReleaseReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_documents = builder._source_material()
        cls.documents = builder._documents()
        cls.index = parse_json_bytes(
            builder.EVIDENCE_INDEX_FILE.read_bytes()
        )
        cls.handoff = parse_json_bytes(
            builder.MACHINE_HANDOFF_FILE.read_bytes()
        )
        cls.human_raw = builder.HUMAN_HANDOFF_FILE.read_bytes()
        cls.changelog_raw = builder.CHANGELOG_FILE.read_bytes()
        cls.policies = load_au040_acceptance().bundle.policies

    def test_01_builder_is_byte_equivalent_from_repository_only(self):
        self.assertEqual(
            set(self.documents),
            {
                builder.EVIDENCE_INDEX_FILE,
                builder.MACHINE_HANDOFF_FILE,
                builder.HUMAN_HANDOFF_FILE,
                builder.CHANGELOG_FILE,
                builder.EVIDENCE_INDEX_SCHEMA_FILE,
                builder.COLD_START_HANDOFF_SCHEMA_FILE,
            },
        )
        for path, expected in self.documents.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), expected)

    def test_02_evidence_index_is_exact_sorted_unique_closure(self):
        entries = self.index["entries"]
        codes = [entry["evidence_code"] for entry in entries]
        paths = [entry["canonical_path"] for entry in entries]
        self.assertEqual(codes, sorted(codes))
        self.assertEqual(len(codes), 23)
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(
            self.index["coverage"]["evidence_entry_count"],
            len(entries),
        )

    def test_03_every_entry_matches_external_git_blob_and_review_base(self):
        by_code = {
            entry["evidence_code"]: entry
            for entry in self.index["entries"]
        }
        for spec in review.EVIDENCE_SPECS:
            with self.subTest(code=spec.code):
                source = builder._git_blob(
                    spec.source_git_object_id,
                    spec.path,
                )
                reviewed = builder._git_blob(
                    review.REVIEW_BASE_GIT_OBJECT_ID,
                    spec.path,
                )
                self.assertEqual(source, reviewed)
                self.assertEqual(reviewed, builder._current(spec.path))
                self.assertEqual(
                    hashlib.sha256(source).hexdigest(),
                    by_code[spec.code]["content_digest"],
                )

    def test_04_index_and_handoff_self_digests_close(self):
        self.assertEqual(
            self.index["index_digest"],
            canonical_digest(self.index, review.INDEX_SELF_POINTER),
        )
        self.assertEqual(
            self.handoff["artifact_digest"],
            canonical_digest(self.handoff, review.SELF_POINTER),
        )

    def test_05_candidate_is_exact_non_active_31_plus_5(self):
        candidate = self.handoff["source_trust"]["candidate"]
        self.assertEqual(candidate["schema_count"], 31)
        self.assertEqual(candidate["policy_count"], 5)
        self.assertEqual(candidate["mode"], "CANDIDATE")
        self.assertEqual(
            candidate["bundle_digest"],
            review.CANDIDATE_BUNDLE_DIGEST,
        )
        self.assertFalse(
            self.handoff["current_state"]["active_trust_present"]
        )

    def test_06_task_pack_stops_at_m069_and_has_no_m070(self):
        contract = self.handoff["task_contract"]
        self.assertEqual(contract["task_pack_task_count"], 69)
        self.assertEqual(contract["task_pack_last_task_id"], "M-069")
        self.assertEqual(contract["implemented_task_ids"], ["M-069"])
        self.assertFalse(contract["m070_exists_in_task_pack"])
        self.assertTrue(contract["done_gate_satisfied"])

    def test_07_registered_89_and_mirror_90_drift_is_not_hidden(self):
        state = self.handoff["current_state"]
        self.assertEqual(
            (
                state["registry_identity_count"],
                state["registry_instance_count"],
                state["registry_version_count"],
            ),
            (89, 89, 89),
        )
        self.assertEqual(state["repository_mirror_skill_instance_count"], 90)
        self.assertEqual(state["binding_eligible_version_count"], 0)
        self.assertFalse(state["registry_mirror_parity"])

    def test_08_pilots_are_shadow_only_and_not_production(self):
        state = self.handoff["current_state"]
        self.assertEqual(state["pilot_count"], 3)
        self.assertEqual(state["shadow_pilot_cycle_count"], 9)
        self.assertFalse(state["production_pilots_executed"])
        self.assertFalse(state["mechanism_production_ready"])

    def test_09_schedule_authority_remains_unresolved(self):
        state = self.handoff["current_state"]
        self.assertFalse(state["schedule_authority_resolved"])
        self.assertEqual(
            state["schedule_candidates_local"],
            ["04:15", "05:30"],
        )

    def test_10_all_known_blockers_are_exact_and_sorted(self):
        self.assertEqual(
            self.handoff["blocker_codes"],
            list(review.BLOCKER_CODES),
        )
        self.assertEqual(
            self.handoff["blocker_codes"],
            sorted(self.handoff["blocker_codes"]),
        )

    def test_11_release_decision_stops_before_fresh_verifier(self):
        decision = self.handoff["release_decision"]
        self.assertEqual(
            decision["outcome"],
            "STOP_BEFORE_OWNER_FRESH_VERIFIER",
        )
        self.assertTrue(decision["owner_fresh_verifier_required"])
        self.assertFalse(decision["verifier_called_during_development"])
        self.assertFalse(
            decision["follow_on_mechanism_taskpack_phase_exists"]
        )
        self.assertEqual(
            decision["exact_next_action"],
            "OWNER_SELECT_AND_RUN_FRESH_VERIFIER",
        )

    def test_12_nonmutation_and_activation_boundaries_remain_false(self):
        state = self.handoff["current_state"]
        nonmutation = self.handoff["nonmutation"]
        self.assertFalse(state["canonical_publication_permitted"])
        self.assertFalse(state["activation_permitted"])
        self.assertFalse(state["version_file_present"])
        for field in (
            "auto_plane_unchanged",
            "openai_database_unchanged",
            "candidate_bundle_unchanged",
            "registry_unchanged",
            "source_roots_unchanged",
        ):
            self.assertTrue(nonmutation[field])
        for field in (
            "state_or_watermark_written",
            "notification_sent",
            "migration_executed",
            "canonical_artifact_published",
            "activation_executed",
            "automation_or_app_changed",
            "version_file_created",
        ):
            self.assertFalse(nonmutation[field])
        self.assertFalse(builder.VERSION_PATH.exists())

    def test_13_validation_baseline_is_complete_and_truthful(self):
        baseline = self.handoff["validation_baseline"]
        self.assertEqual(baseline["complete_mechanism"], {
            "tests_run": 307,
            "failures": 0,
            "errors": 0,
        })
        self.assertEqual(baseline["auto_known_transition"], {
            "tests_run": 200,
            "failures": 5,
            "errors": 20,
        })
        self.assertEqual(
            baseline["schema_sets"],
            {
                "base": 21,
                "candidate_compatible": 41,
                "version": 24,
                "repository_closure_before_m069": 85,
            },
        )

    def test_14_human_handoff_and_changelog_bytes_are_bound(self):
        documents = self.handoff["documents"]
        self.assertEqual(
            documents["human_handoff"]["content_digest"],
            hashlib.sha256(self.human_raw).hexdigest(),
        )
        self.assertEqual(
            documents["changelog"]["content_digest"],
            hashlib.sha256(self.changelog_raw).hexdigest(),
        )
        self.assertEqual(
            documents["human_handoff"]["canonical_path"],
            review.HUMAN_HANDOFF_PATH,
        )
        self.assertEqual(
            documents["changelog"]["canonical_path"],
            review.CHANGELOG_PATH,
        )

    def test_15_missing_evidence_input_fails_closed(self):
        altered = dict(self.raw_documents)
        del altered["REPRESENTATIVE_PILOTS"]
        with self.assertRaisesRegex(
            review.ColdStartReviewError,
            "COLD_START_EVIDENCE_INPUT_SET_INCOMPLETE",
        ):
            review.build_evidence_index(altered)

    def test_16_raw_byte_drift_fails_closed(self):
        altered = dict(self.raw_documents)
        altered["MIRROR_INDEX"] += b" "
        with self.assertRaisesRegex(
            review.ColdStartReviewError,
            "COLD_START_EVIDENCE_RAW_DIGEST_MISMATCH:MIRROR_INDEX",
        ):
            review.build_evidence_index(altered)

    def test_17_duplicate_json_key_fails_closed(self):
        altered = dict(self.raw_documents)
        altered["MIRROR_INDEX"] = b'{"schema":"x","schema":"y"}'
        with self.assertRaisesRegex(
            review.ColdStartReviewError,
            "COLD_START_EVIDENCE_JSON_INVALID:MIRROR_INDEX",
        ):
            review.build_evidence_index(altered)

    def test_18_self_rehashed_source_cannot_replace_pinned_bytes(self):
        altered = dict(self.raw_documents)
        source = parse_json_bytes(altered["FAILURE_TO_TEST"])
        source["production_conversion_ready"] = True
        source["artifact_digest"] = canonical_digest(
            source,
            review.SELF_POINTER,
        )
        altered["FAILURE_TO_TEST"] = (
            json.dumps(source, sort_keys=True) + "\n"
        ).encode()
        with self.assertRaisesRegex(
            review.ColdStartReviewError,
            "COLD_START_EVIDENCE_RAW_DIGEST_MISMATCH:FAILURE_TO_TEST",
        ):
            review.build_evidence_index(altered)

    def test_19_caller_cannot_change_index_and_rehash(self):
        altered = copy.deepcopy(self.index)
        altered["coverage"]["production_readiness_claimed"] = True
        altered["index_digest"] = canonical_digest(
            altered,
            review.INDEX_SELF_POINTER,
        )
        with self.assertRaisesRegex(
            review.ColdStartReviewError,
            "COLD_START_EVIDENCE_INDEX_RECOMPUTATION_MISMATCH",
        ):
            review.validate_evidence_index(
                altered,
                self.raw_documents,
            )

    def test_20_caller_cannot_change_handoff_and_rehash(self):
        altered = copy.deepcopy(self.handoff)
        altered["current_state"]["activation_permitted"] = True
        altered["artifact_digest"] = canonical_digest(
            altered,
            review.SELF_POINTER,
        )
        with self.assertRaisesRegex(
            review.ColdStartReviewError,
            "COLD_START_HANDOFF_RECOMPUTATION_MISMATCH",
        ):
            review.validate_machine_handoff(
                altered,
                self.index,
                hashlib.sha256(self.human_raw).hexdigest(),
                hashlib.sha256(self.changelog_raw).hexdigest(),
            )

    def test_21_public_scanner_accepts_machine_outputs(self):
        scan_public_value(self.index, self.policies)
        scan_public_value(self.handoff, self.policies)
        altered = copy.deepcopy(self.handoff)
        altered["raw"] = "forbidden"
        with self.assertRaisesRegex(
            ContractError,
            "PUBLIC_FORBIDDEN_FIELD",
        ):
            scan_public_value(altered, self.policies)

    def test_22_generated_schemas_are_closed_and_byte_equivalent(self):
        index_schema = parse_json_bytes(
            builder.EVIDENCE_INDEX_SCHEMA_FILE.read_bytes()
        )
        handoff_schema = parse_json_bytes(
            builder.COLD_START_HANDOFF_SCHEMA_FILE.read_bytes()
        )
        self.assertFalse(index_schema["additionalProperties"])
        self.assertFalse(handoff_schema["additionalProperties"])
        self.assertEqual(
            index_schema["$id"],
            review.EVIDENCE_INDEX_SCHEMA_ID,
        )
        self.assertEqual(
            handoff_schema["$id"],
            review.COLD_START_HANDOFF_SCHEMA_ID,
        )
        self.assertEqual(
            builder._render_json(index_schema),
            self.documents[builder.EVIDENCE_INDEX_SCHEMA_FILE],
        )
        self.assertEqual(
            builder._render_json(handoff_schema),
            self.documents[builder.COLD_START_HANDOFF_SCHEMA_FILE],
        )

    def test_23_pure_review_has_no_side_effect_or_chat_capability(self):
        source = inspect.getsource(review)
        for forbidden in (
            "subprocess",
            "pathlib",
            "socket",
            "requests",
            "urllib",
            "open(",
            "os.environ",
            "input(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_24_new_agent_entry_is_self_sufficient_without_chat(self):
        text = self.human_raw.decode("utf-8")
        self.assertIn(
            "build_cold_start_release_review.py --check",
            text,
        )
        self.assertIn("OWNER_SELECT_AND_RUN_FRESH_VERIFIER", text)
        self.assertIn("there is no M-070", text)
        self.assertIn("without chat history", text)
        self.assertNotIn("@", text)
        first = review.build_evidence_index(self.raw_documents)
        second = review.build_evidence_index(self.raw_documents)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
