import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.identity import (  # noqa: E402
    IdentityError,
    IdentityLookup,
    IdentityMaster,
    IdentityPolicy,
    ProjectIdentityRecord,
    append_identity_candidate,
    append_identity_record,
    append_identity_review_task,
    build_cross_entity_view,
    project_identity_from_mapping,
    public_identity_summary,
)


POLICY_PATH = MODULE_ROOT / "config" / "identity_policy.yml"
SOURCE_RECORD_REF = "rec_source_record_" + "a" * 32


def synthetic_record(
    *,
    project: str = "PROJECT-SYNTHETIC-001",
    entity: str = "ENTITY-SYNTHETIC-001",
    wbs: str = "WBS-SYNTHETIC-001",
    project_code: str = "CODE-SYNTHETIC-001",
    project_name: str = "Synthetic project one",
    customer: str = "CUSTOMER-SYNTHETIC-001",
    contracts=("CONTRACT-SYNTHETIC-001",),
    source_aliases=("source://synthetic/SOURCE-001",),
    valid_from: str = "2026-01-01",
    valid_to=None,
    resolution_seed: str = "b",
    evidence_seed: str = "c",
    status: str = "APPROVED",
) -> ProjectIdentityRecord:
    record = ProjectIdentityRecord(
        canonical_project_id=project,
        legal_entity_id=entity,
        wbs_or_cost_code=wbs,
        project_code=project_code,
        project_name=project_name,
        customer_id=customer,
        contract_ids=tuple(contracts),
        source_aliases=tuple(source_aliases),
        valid_from=valid_from,
        valid_to=valid_to,
        identity_status=status,
        mapping_resolution_ref="identity_resolution_" + resolution_seed * 32,
        evidence_refs=("evidence:" + evidence_seed * 64,) if status == "APPROVED" else (),
    )
    record.validate()
    return record


def lookup_for(master: IdentityMaster, **overrides) -> IdentityLookup:
    values = {
        "valid_at": "2026-06-30",
        "expected_master_hash": master.content_hash,
        "source_record_refs": (SOURCE_RECORD_REF,),
        "requested_metrics": ("SYNTHETIC_JOB_COST",),
        "canonical_project_id": "PROJECT-SYNTHETIC-001",
        "legal_entity_id": "ENTITY-SYNTHETIC-001",
        "wbs_or_cost_code": "WBS-SYNTHETIC-001",
    }
    values.update(overrides)
    return IdentityLookup(**values)


class IdentityPolicyAndSchemaTests(unittest.TestCase):
    def test_policy_is_strict_and_cannot_enable_company_approval_or_ambiguity(self) -> None:
        policy = IdentityPolicy.from_yaml(POLICY_PATH)
        self.assertEqual(policy.identity_ambiguity_allowed, 0)
        self.assertEqual(policy.unresolved_final_mapping_allowed, 0)
        self.assertFalse(policy.fuzzy_final_mapping_allowed)
        self.assertFalse(policy.cross_entity_destructive_normalization_allowed)
        self.assertFalse(policy.company_approval_state_managed)

        raw = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        for key, value in (
            ("identity_ambiguity_allowed", 1),
            ("company_approval_state_managed", True),
            ("fuzzy_final_mapping_allowed", True),
            ("policy_id", "POLICY-NOT-CANONICAL"),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                changed = dict(raw)
                changed[key] = value
                path = Path(temporary) / "identity_policy.yml"
                path.write_text(yaml.safe_dump(changed, sort_keys=False), encoding="utf-8")
                with self.assertRaises(IdentityError) as caught:
                    IdentityPolicy.from_yaml(path)
                self.assertEqual(caught.exception.code, "IDENTITY_POLICY_RELAXED")

    def test_identity_master_hash_binds_policy_bytes_not_only_records(self) -> None:
        raw = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            reordered_path = Path(temporary) / "identity_policy.yml"
            reordered_path.write_text(yaml.safe_dump(raw, sort_keys=True), encoding="utf-8")
            original_policy = IdentityPolicy.from_yaml(POLICY_PATH)
            reordered_policy = IdentityPolicy.from_yaml(reordered_path)
            self.assertNotEqual(original_policy.content_sha256, reordered_policy.content_sha256)
            record = synthetic_record()
            self.assertNotEqual(
                IdentityMaster(original_policy, (record,)).content_hash,
                IdentityMaster(reordered_policy, (record,)).content_hash,
            )

    def test_direct_policy_construction_cannot_bypass_locked_invariants(self) -> None:
        policy = IdentityPolicy.from_yaml(POLICY_PATH)
        relaxed = replace(policy, fuzzy_final_mapping_allowed=True)
        with self.assertRaises(IdentityError) as caught:
            IdentityMaster(relaxed, (synthetic_record(),)).validate()
        self.assertEqual(caught.exception.code, "IDENTITY_POLICY_RELAXED")
        with self.assertRaises(IdentityError) as caught:
            IdentityMaster(policy, [synthetic_record()]).validate()
        self.assertEqual(caught.exception.code, "IDENTITY_MASTER_MUTABLE")

    def test_template_and_generated_review_task_validate_against_locked_schemas(self) -> None:
        template = json.loads(
            (MODULE_ROOT / "templates" / "project_identity.template.json").read_text(encoding="utf-8")
        )
        project_schema = json.loads(
            (MODULE_ROOT / "schemas" / "project_record.schema.json").read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(project_schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(template)), [])
        project_identity_from_mapping(template)

        policy = IdentityPolicy.from_yaml(POLICY_PATH)
        record = synthetic_record()
        master = IdentityMaster(policy, (record,))
        result = master.resolve(
            lookup_for(
                master,
                canonical_project_id=None,
                legal_entity_id=None,
                wbs_or_cost_code=None,
                project_code=record.project_code,
            )
        )
        review_schema = json.loads(
            (MODULE_ROOT / "schemas" / "review_task.schema.json").read_text(encoding="utf-8")
        )
        review_validator = Draft202012Validator(review_schema, format_checker=FormatChecker())
        self.assertEqual(list(review_validator.iter_errors(result.review_tasks[0].as_private_dict())), [])
        self.assertEqual(result.review_tasks[0].status, "PENDING")

    def test_identity_contract_has_no_finance_owner_or_authorized_person_fields(self) -> None:
        forbidden = {"finance_owner", "authorized_person", "approval_owner", "approver", "assignee"}
        for relative in (
            "config/identity_policy.yml",
            "schemas/project_record.schema.json",
            "schemas/review_task.schema.json",
            "templates/project_identity.template.json",
        ):
            with self.subTest(relative=relative):
                text = (MODULE_ROOT / relative).read_text(encoding="utf-8")
                self.assertTrue(forbidden.isdisjoint(set(json.loads(text).keys())) if relative.endswith(".json") else True)
                for field in forbidden:
                    self.assertNotIn(field + ":", text)
                    self.assertNotIn('"' + field + '"', text)


class IdentityResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = IdentityPolicy.from_yaml(POLICY_PATH)
        self.record = synthetic_record()
        self.master = IdentityMaster(self.policy, (self.record,))

    def test_effective_identity_uniqueness(self) -> None:
        result = self.master.resolve(lookup_for(self.master))
        self.assertTrue(result.resolved)
        self.assertEqual(result.calculation_status, "VALIDATED_IDENTITY")
        self.assertEqual(result.match_method, "EXACT_CANONICAL_SCOPE")
        self.assertEqual(result.identity_record_ref, self.record.identity_ref)
        self.assertEqual(result.review_tasks, ())

    def test_exact_contract_source_and_resolution_are_qualified_paths(self) -> None:
        cases = (
            ({"contract_id": self.record.contract_ids[0]}, "EXACT_CONTRACT_ID"),
            ({"governed_source_identifier": self.record.source_aliases[0]}, "EXACT_GOVERNED_SOURCE_ID"),
            ({"mapping_resolution_ref": self.record.mapping_resolution_ref}, "QUALIFIED_MAPPING_RESOLUTION"),
        )
        for fields, expected_method in cases:
            with self.subTest(expected_method=expected_method):
                result = self.master.resolve(
                    lookup_for(
                        self.master,
                        canonical_project_id=None,
                        legal_entity_id=None,
                        wbs_or_cost_code=None,
                        **fields,
                    )
                )
                self.assertTrue(result.resolved)
                self.assertEqual(result.match_method, expected_method)

    def test_alias_and_free_text_inputs_remain_candidates_even_when_exact(self) -> None:
        cases = (
            {"project_code": self.record.project_code},
            {"project_name": self.record.project_name},
            {"customer_id": self.record.customer_id},
            {"project_name": "Synthetic project one almost"},
            {"free_text_ref": "private://identity-note/opaque-001"},
        )
        for fields in cases:
            with self.subTest(fields=fields):
                result = self.master.resolve(
                    lookup_for(
                        self.master,
                        canonical_project_id=None,
                        legal_entity_id=None,
                        wbs_or_cost_code=None,
                        **fields,
                    )
                )
                self.assertFalse(result.resolved)
                self.assertEqual(result.calculation_status, "BLOCKED_IDENTITY")
                self.assertEqual(result.blocker_codes, ("IDENTITY_CANDIDATE_ONLY",))
                self.assertEqual(result.review_tasks[0].severity, "P0")

    def test_contract_and_canonical_project_disagreement_blocks(self) -> None:
        other = synthetic_record(
            project="PROJECT-SYNTHETIC-002",
            wbs="WBS-SYNTHETIC-002",
            project_code="CODE-SYNTHETIC-002",
            project_name="Synthetic project two",
            contracts=("CONTRACT-SYNTHETIC-002",),
            source_aliases=("source://synthetic/SOURCE-002",),
            resolution_seed="d",
            evidence_seed="e",
        )
        master = IdentityMaster(self.policy, (self.record, other))
        result = master.resolve(lookup_for(master, contract_id=other.contract_ids[0]))
        self.assertEqual(result.blocker_codes, ("IDENTITY_CONTRACT_PROJECT_CONFLICT",))
        self.assertEqual(len(result.candidates[0].candidate_record_refs), 2)

    def test_ambiguous_candidate_alias_blocks_even_with_other_exact_scope(self) -> None:
        other = synthetic_record(
            project="PROJECT-SYNTHETIC-002",
            wbs="WBS-SYNTHETIC-002",
            project_code=self.record.project_code,
            project_name="Synthetic project two",
            contracts=("CONTRACT-SYNTHETIC-002",),
            source_aliases=("source://synthetic/SOURCE-002",),
            resolution_seed="d",
            evidence_seed="e",
        )
        master = IdentityMaster(self.policy, (self.record, other))
        result = master.resolve(lookup_for(master, project_code=self.record.project_code))
        self.assertEqual(result.blocker_codes, ("IDENTITY_ALIAS_CONFLICT",))
        self.assertIn("IDENTITY_ALIAS_CONFLICT", {task.task_type for task in master.conflict_tasks()})

    def test_effective_period_end_is_inclusive_and_overlap_blocks(self) -> None:
        first = replace(self.record, valid_to="2026-06-30")
        overlapping = synthetic_record(
            valid_from="2026-06-30",
            project_code="CODE-SYNTHETIC-001-NEW",
            project_name="Synthetic project one remapped",
            contracts=("CONTRACT-SYNTHETIC-001-NEW",),
            source_aliases=("source://synthetic/SOURCE-001-NEW",),
            resolution_seed="d",
            evidence_seed="e",
        )
        master = IdentityMaster(self.policy, (first, overlapping))
        lookup = lookup_for(master, valid_at="2026-06-30")
        result = master.resolve(lookup)
        self.assertEqual(result.blocker_codes, ("IDENTITY_MULTIPLE_ACTIVE_MATCHES",))
        self.assertIn("IDENTITY_EFFECTIVE_PERIOD_OVERLAP", {task.task_type for task in master.conflict_tasks()})

        adjacent = replace(overlapping, valid_from="2026-07-01")
        nonoverlap_master = IdentityMaster(self.policy, (first, adjacent))
        self.assertNotIn(
            "IDENTITY_EFFECTIVE_PERIOD_OVERLAP",
            {task.task_type for task in nonoverlap_master.conflict_tasks()},
        )
        self.assertTrue(nonoverlap_master.resolve(lookup_for(nonoverlap_master, valid_at="2026-06-30")).resolved)
        with self.assertRaises(IdentityError) as caught:
            build_cross_entity_view(
                master,
                canonical_project_id=self.record.canonical_project_id,
                valid_at="2026-06-30",
            )
        self.assertEqual(caught.exception.code, "IDENTITY_MULTIPLE_ACTIVE_MATCHES")

    def test_cross_entity_view_preserves_dimensions_and_missing_entity_blocks(self) -> None:
        other_entity = synthetic_record(
            entity="ENTITY-SYNTHETIC-002",
            project_code="CODE-SYNTHETIC-ENTITY-002",
            project_name="Synthetic project one entity two",
            contracts=("CONTRACT-SYNTHETIC-ENTITY-002",),
            source_aliases=("source://synthetic/SOURCE-ENTITY-002",),
            resolution_seed="d",
            evidence_seed="e",
        )
        master = IdentityMaster(self.policy, (self.record, other_entity))
        self.assertNotIn("IDENTITY_CROSS_ENTITY_AMBIGUOUS", {task.task_type for task in master.conflict_tasks()})
        view = build_cross_entity_view(
            master,
            canonical_project_id=self.record.canonical_project_id,
            valid_at="2026-06-30",
        ).as_private_dict()
        self.assertEqual(len(view["entity_scopes"]), 2)
        self.assertEqual(
            {item["legal_entity_id"] for item in view["entity_scopes"]},
            {"ENTITY-SYNTHETIC-001", "ENTITY-SYNTHETIC-002"},
        )
        self.assertFalse(view["destructive_normalization_performed"])
        self.assertEqual(view["identity_master_hash"], master.content_hash)

        result = master.resolve(
            lookup_for(master, legal_entity_id=None)
        )
        self.assertEqual(result.blocker_codes, ("IDENTITY_CROSS_ENTITY_AMBIGUOUS",))

    def test_stale_master_or_mapping_resolution_blocks(self) -> None:
        stale_master = self.master.resolve(lookup_for(self.master, expected_master_hash="0" * 64))
        self.assertEqual(stale_master.blocker_codes, ("IDENTITY_STALE_MAPPING",))

        stale_resolution = self.master.resolve(
            lookup_for(
                self.master,
                canonical_project_id=None,
                legal_entity_id=None,
                wbs_or_cost_code=None,
                mapping_resolution_ref="identity_resolution_" + "f" * 32,
            )
        )
        self.assertEqual(stale_resolution.blocker_codes, ("IDENTITY_STALE_MAPPING",))

    def test_incomplete_and_unmapped_identity_each_create_blocking_task(self) -> None:
        incomplete = self.master.resolve(
            lookup_for(self.master, legal_entity_id=None)
        )
        unmapped = self.master.resolve(
            lookup_for(
                self.master,
                canonical_project_id=None,
                legal_entity_id=None,
                wbs_or_cost_code=None,
                contract_id="CONTRACT-SYNTHETIC-NOT-MAPPED",
            )
        )
        for result, code in (
            (incomplete, "IDENTITY_INCOMPLETE_CANONICAL_KEY"),
            (unmapped, "IDENTITY_UNMAPPED"),
        ):
            with self.subTest(code=code):
                self.assertEqual(result.blocker_codes, (code,))
                self.assertEqual(len(result.candidates), 1)
                self.assertEqual(len(result.review_tasks), 1)
                self.assertEqual(result.review_tasks[0].task_type, code)
                self.assertEqual(result.review_tasks[0].status, "PENDING")

    def test_free_text_reference_cannot_smuggle_raw_text(self) -> None:
        with self.assertRaises(IdentityError) as caught:
            lookup_for(
                self.master,
                canonical_project_id=None,
                legal_entity_id=None,
                wbs_or_cost_code=None,
                free_text_ref="private://contains raw human note",
            ).validate()
        self.assertEqual(caught.exception.code, "FREE_TEXT_REF_INVALID")

    def test_invalid_period_evidence_and_source_alias_fail_closed(self) -> None:
        cases = (
            (replace(self.record, valid_from="2026-02-01", valid_to="2026-01-31"), "IDENTITY_PERIOD_REVERSED"),
            (replace(self.record, contract_ids=()), "IDENTITY_CONTRACT_REQUIRED"),
            (replace(self.record, evidence_refs=()), "IDENTITY_EVIDENCE_REQUIRED"),
            (replace(self.record, source_aliases=("not-governed",)), "GOVERNED_SOURCE_ID_INVALID"),
        )
        for record, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(IdentityError) as caught:
                    record.validate()
                self.assertEqual(caught.exception.code, expected_code)

    def test_private_records_are_append_only_and_public_summary_is_aggregate_only(self) -> None:
        blocked = self.master.resolve(
            lookup_for(
                self.master,
                canonical_project_id=None,
                legal_entity_id=None,
                wbs_or_cost_code=None,
                project_code=self.record.project_code,
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            private_root = Path(temporary) / "private_runtime"
            record_path = append_identity_record(private_root, self.record)
            candidate_record_path = append_identity_record(
                private_root,
                replace(self.record, identity_status="CANDIDATE", evidence_refs=()),
            )
            candidate_path = append_identity_candidate(private_root, blocked.candidates[0])
            task_path = append_identity_review_task(private_root, blocked.review_tasks[0])
            self.assertTrue(record_path.is_file())
            self.assertEqual(record_path.parent.name, "approved_records")
            self.assertEqual(candidate_record_path.parent.name, "candidate_records")
            self.assertTrue(candidate_path.is_file())
            self.assertTrue(task_path.is_file())
            with self.assertRaises(IdentityError) as caught:
                append_identity_record(private_root, self.record)
            self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")
            task_payload = json.loads(task_path.read_text(encoding="utf-8"))
            self.assertTrue(
                {"finance_owner", "authorized_person", "approval_owner", "approver", "assignee"}.isdisjoint(
                    task_payload
                )
            )

        public = public_identity_summary(self.master)
        public_text = json.dumps(public, sort_keys=True)
        self.assertEqual(public["record_count"], 1)
        for private_value in (
            self.record.canonical_project_id,
            self.record.legal_entity_id,
            self.record.wbs_or_cost_code,
            self.record.identity_ref,
            self.master.content_hash,
        ):
            self.assertNotIn(private_value, public_text)

    def test_duplicate_mapping_resolution_across_scopes_is_a_blocking_conflict(self) -> None:
        other = synthetic_record(
            project="PROJECT-SYNTHETIC-002",
            wbs="WBS-SYNTHETIC-002",
            project_code="CODE-SYNTHETIC-002",
            project_name="Synthetic project two",
            contracts=("CONTRACT-SYNTHETIC-002",),
            source_aliases=("source://synthetic/SOURCE-002",),
            resolution_seed="b",
            evidence_seed="e",
        )
        master = IdentityMaster(self.policy, (self.record, other))
        tasks = master.conflict_tasks(("SYNTHETIC_JOB_COST",))
        self.assertIn("IDENTITY_IDENTIFIER_CONFLICT", {task.task_type for task in tasks})
        result = master.resolve(
            lookup_for(
                master,
                canonical_project_id=None,
                legal_entity_id=None,
                wbs_or_cost_code=None,
                mapping_resolution_ref=self.record.mapping_resolution_ref,
            )
        )
        self.assertEqual(result.blocker_codes, ("IDENTITY_MULTIPLE_ACTIVE_MATCHES",))

    def test_record_and_master_hashes_are_order_invariant(self) -> None:
        multi_value_record = replace(
            self.record,
            contract_ids=("CONTRACT-SYNTHETIC-001", "CONTRACT-SYNTHETIC-001-B"),
            source_aliases=("source://synthetic/SOURCE-001", "source://synthetic/SOURCE-001-B"),
            evidence_refs=("evidence:" + "c" * 64, "evidence:" + "d" * 64),
        )
        reordered_record = replace(
            multi_value_record,
            contract_ids=tuple(reversed(multi_value_record.contract_ids)),
            source_aliases=tuple(reversed(multi_value_record.source_aliases)),
            evidence_refs=tuple(reversed(multi_value_record.evidence_refs)),
        )
        self.assertEqual(multi_value_record.identity_ref, reordered_record.identity_ref)
        other = synthetic_record(
            project="PROJECT-SYNTHETIC-002",
            wbs="WBS-SYNTHETIC-002",
            project_code="CODE-SYNTHETIC-002",
            project_name="Synthetic project two",
            contracts=("CONTRACT-SYNTHETIC-002",),
            source_aliases=("source://synthetic/SOURCE-002",),
            resolution_seed="d",
            evidence_seed="e",
        )
        self.assertEqual(
            IdentityMaster(self.policy, (self.record, other)).content_hash,
            IdentityMaster(self.policy, (other, self.record)).content_hash,
        )


if __name__ == "__main__":
    unittest.main()
