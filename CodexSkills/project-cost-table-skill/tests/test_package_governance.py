import csv
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import project_cost_table  # noqa: E402
from project_cost_table.accounting_basis import AccountingBasisError, AccountingBasisPolicy  # noqa: E402
from project_cost_table.formulas import FormulaError, FormulaProfile, FormulaStatus  # noqa: E402
from project_cost_table.input_gate import InputRequirements, MetricCatalog, OperationRequest  # noqa: E402
from project_cost_table.identity import IdentityPolicy  # noqa: E402
from project_cost_table.manifest import MANIFEST_BYTES_MAX  # noqa: E402
from project_cost_table.readers.kingdee import KingdeeReaderError, KingdeeReaderProfile  # noqa: E402
from project_cost_table.readers.kingdee_bundle import KingdeeBundleError, KingdeeBundleProfile  # noqa: E402
from project_cost_table.readers.lifecycle import (  # noqa: E402
    LIFECYCLE_READER_VERSION,
    LifecycleReaderError,
    LifecycleReaderProfile,
)
from project_cost_table.resolutions import RESOLUTION_BYTES_MAX  # noqa: E402
from project_cost_table.payroll import (  # noqa: E402
    PayComponentRegistry,
    PayrollAllocationPolicy,
    PayrollError,
)


class PackageGovernanceTests(unittest.TestCase):
    def test_skill_frontmatter_and_openai_interface_agree(self) -> None:
        skill_text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        parts = skill_text.split("---", 2)
        self.assertEqual(parts[0], "")
        frontmatter = yaml.safe_load(parts[1])
        self.assertEqual(set(frontmatter), {"name", "description"})
        self.assertEqual(frontmatter["name"], "project-cost-table-skill")
        agent = yaml.safe_load((MODULE_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8"))
        interface = agent["interface"]
        self.assertEqual(
            set(interface), {"display_name", "short_description", "default_prompt"}
        )
        self.assertIn("$" + frontmatter["name"], interface["default_prompt"])
        self.assertIn("输入", interface["short_description"])
        self.assertIn("输出路径", interface["short_description"])

    def test_product_task_and_canonical_ids_are_consistent(self) -> None:
        product_version = (MODULE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        governance = yaml.safe_load((MODULE_ROOT / "governance.yaml").read_text(encoding="utf-8"))
        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        self.assertEqual(product_version, project_cost_table.__version__)
        self.assertEqual(governance["task_pack_version"], "1.2.0")
        self.assertEqual(governance["product_version"], product_version)
        self.assertEqual(governance["task_id"], "KMFA-PROJECT-COST-TABLE-SKILL-V2-PROPOSED")
        self.assertEqual(governance["acceptance_id"], "ACC-KMFA-PROJECT-COST-TABLE-SKILL-V2-PROPOSED")
        self.assertEqual(governance["model_id"], "MODEL-KMFA-PROJECT-COST-002-PROPOSED")
        self.assertEqual(governance["run_status"]["R3"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R4"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R5"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R6"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R7"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R8"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R9"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R10"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R11"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R12"], "COMPLETE")
        self.assertEqual(governance["run_status"]["GLOBAL_INSTALL"], "MACHINE_LOCAL_EXTERNAL")
        models = {item["model_id"]: item for item in model_registry["models"]}
        self.assertIn(governance["model_id"], models)
        self.assertEqual(models[governance["model_id"]]["status"], "RELEASED_R12_FAIL_CLOSED_CURRENT_INPUT_GATED")
        for model in models.values():
            self.assertEqual(model["product_version"], product_version)
        r2_policy_ids = {
            "POLICY-KMFA-MONEY-STRICT-001",
            "POLICY-KMFA-FILE-SECURITY-001",
            "POLICY-KMFA-ATOMIC-PATHS-001",
        }
        self.assertTrue(r2_policy_ids.issubset(models))
        for policy_id in r2_policy_ids:
            self.assertEqual(models[policy_id]["status"], "IMPLEMENTED_R2")
        r3_policy_ids = {
            "POLICY-KMFA-INPUT-SUFFICIENCY-001",
            "MODEL-KMFA-SOURCE-LAYERS-001",
        }
        self.assertTrue(r3_policy_ids.issubset(models))
        for policy_id in r3_policy_ids:
            self.assertEqual(models[policy_id]["status"], "IMPLEMENTED_R3")
        self.assertEqual(
            models["POLICY-KMFA-MANIFEST-SELECTION-001"]["status"],
            "IMPLEMENTED_R3_MULTI_SOURCE_EXTENSION_R6",
        )
        self.assertEqual(models["POLICY-KMFA-IDENTITY-MASTER-001"]["status"], "IMPLEMENTED_R4")
        self.assertFalse(models["POLICY-KMFA-IDENTITY-MASTER-001"]["internal_company_approval_managed"])
        self.assertEqual(models["POLICY-KMFA-KINGDEE-READER-001"]["status"], "IMPLEMENTED_R5")
        self.assertEqual(models["POLICY-KMFA-KINGDEE-BUNDLE-001"]["status"], "IMPLEMENTED_R5")
        self.assertEqual(models["POLICY-KMFA-ACCOUNTING-BASIS-WIP-001"]["status"], "IMPLEMENTED_R5")
        self.assertFalse(models["POLICY-KMFA-ACCOUNTING-BASIS-WIP-001"]["internal_company_approval_managed"])
        self.assertEqual(
            models["POLICY-KMFA-LIFECYCLE-READERS-001"]["status"],
            "IMPLEMENTED_R6_ACTIVE_PRIVATE_PROFILES_REQUIRED",
        )
        self.assertEqual(
            models["MODEL-KMFA-ECONOMIC-EVENT-CANDIDATE-001"]["status"],
            "IMPLEMENTED_R6_WITH_R7_RELATION_VIEW_AND_R9_EXPLICIT_METRIC_ADAPTER",
        )
        self.assertEqual(
            models["POLICY-KMFA-EXACT-EXPORT-DUPLICATE-001"]["status"],
            "IMPLEMENTED_R6_WITH_GENERIC_SAME_STAGE_EXTENSION_R7",
        )
        self.assertFalse(models["POLICY-KMFA-LIFECYCLE-READERS-001"]["internal_company_approval_managed"])
        self.assertFalse(models["MODEL-KMFA-ECONOMIC-EVENT-CANDIDATE-001"]["internal_company_approval_managed"])

    def test_feature_requirement_and_registry_sets_are_complete_for_contract(self) -> None:
        feature_text = (MODULE_ROOT / "FEATURE_CATALOG.md").read_text(encoding="utf-8")
        feature_ids = set(re.findall(r"\| `(F-[0-9]{3})` \|", feature_text))
        self.assertEqual(feature_ids, {"F-%03d" % number for number in range(1, 31)})

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            requirement_ids = {row["requirement_id"] for row in csv.DictReader(handle)}
        self.assertEqual(requirement_ids, {"REQ-%03d" % number for number in range(1, 20)})

        formula_registry = yaml.safe_load((MODULE_ROOT / "formula_registry.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(formula_registry["formulas"]), 8)

    def test_boundary_parameter_matches_policy(self) -> None:
        policy = yaml.safe_load(
            (MODULE_ROOT / "config" / "artifact_classification.yml").read_text(encoding="utf-8")
        )
        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            int(parameters["ARTIFACT_MAX_TEXT_BYTES"]["value"]), policy["max_text_bytes"]
        )

    def test_r2_profiles_parameters_and_traceability_agree(self) -> None:
        money = yaml.safe_load((MODULE_ROOT / "config" / "money_profile.yml").read_text(encoding="utf-8"))
        security = yaml.safe_load(
            (MODULE_ROOT / "config" / "security_limits.yml").read_text(encoding="utf-8")
        )
        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "BASE_CURRENCY": money["currency"],
            "MONEY_SCALE": money["minor_unit_scale"],
            "DEFAULT_ROUNDING": money["rounding"],
            "FLOAT_MONEY_PATH_ALLOWED": int(money["float_input_allowed"]),
            "MONEY_DECIMAL_CONTEXT_PRECISION": money["decimal_context_precision"],
            "MONEY_MAX_INPUT_SCALE": money["max_input_scale"],
            "MONEY_MAX_ABS_MINOR_UNITS": money["max_abs_minor_units"],
            "SOURCE_FILE_BYTES_MAX": security["source_file_bytes_max"],
            "ARCHIVE_MEMBER_COUNT_MAX": security["archive_member_count_max"],
            "ARCHIVE_TOTAL_UNCOMPRESSED_MAX": security["archive_total_uncompressed_bytes_max"],
            "ARCHIVE_SINGLE_MEMBER_MAX": security["archive_single_member_bytes_max"],
            "ARCHIVE_COMPRESSION_RATIO_MAX": security["archive_compression_ratio_max"],
            "ARCHIVE_NESTED_DEPTH_MAX": security["archive_nested_depth_max"],
            "XML_SINGLE_PART_MAX": security["xml_single_part_bytes_max"],
        }
        for parameter_id, value in expected.items():
            with self.subTest(parameter_id=parameter_id):
                self.assertEqual(parameters[parameter_id]["value"], str(value))
                self.assertIn("ACTIVE_R2", parameters[parameter_id]["status"])

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-002"]["status"], "IMPLEMENTED_R2")
        self.assertEqual(traceability["REQ-003"]["status"], "IMPLEMENTED_R2")

    def test_r3_configs_templates_parameters_and_traceability_agree(self) -> None:
        requirements = InputRequirements.from_yaml(MODULE_ROOT / "config" / "input_requirements.yml")
        catalog = MetricCatalog.from_yaml(MODULE_ROOT / "config" / "metric_catalog.yml")
        self.assertEqual(set(requirements.metric_dependencies), set(catalog.metric_map()))
        source_priority = yaml.safe_load((MODULE_ROOT / "config" / "source_priority.yml").read_text(encoding="utf-8"))
        self.assertEqual(source_priority["reference_display"]["allowed_only_for"], ["reference-replay", "regression"])
        self.assertIn("calculate", source_priority["reference_display"]["prohibited_for"])

        template_pairs = [
            (
                MODULE_ROOT / "templates" / "operation_request.template.json",
                MODULE_ROOT / "schemas" / "operation_request.schema.json",
            ),
            (
                MODULE_ROOT / "templates" / "input_resolution.template.json",
                MODULE_ROOT / "schemas" / "input_resolution.schema.json",
            ),
        ]
        for template_path, schema_path in template_pairs:
            with self.subTest(template=template_path.name):
                payload = json.loads(template_path.read_text(encoding="utf-8"))
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                validator = Draft202012Validator(schema, format_checker=FormatChecker())
                self.assertEqual(list(validator.iter_errors(payload)), [])
        request = OperationRequest.from_mapping(
            json.loads((MODULE_ROOT / "templates" / "operation_request.template.json").read_text(encoding="utf-8"))
        )
        self.assertIsNone(request.mode)

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "MANIFEST_BYTES_MAX": MANIFEST_BYTES_MAX,
            "RESOLUTION_BYTES_MAX": RESOLUTION_BYTES_MAX,
            "INPUT_NO_RESPONSE_IS_PERMISSION": 0,
            "INPUT_NON_WAIVABLE_OMISSION_ALLOWED": 0,
        }
        for parameter_id, value in expected.items():
            self.assertEqual(parameters[parameter_id]["value"], str(value))
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R3")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        for requirement_id in ("REQ-001", "REQ-004"):
            self.assertEqual(traceability[requirement_id]["status"], "IMPLEMENTED_R3")
        self.assertEqual(traceability["REQ-018"]["status"], "IMPLEMENTED_R3_R11")

    def test_r4_identity_policy_schemas_parameters_and_traceability_agree(self) -> None:
        policy = IdentityPolicy.from_yaml(MODULE_ROOT / "config" / "identity_policy.yml")
        self.assertEqual(policy.policy_id, "POLICY-KMFA-IDENTITY-MASTER-001")
        self.assertEqual(
            policy.canonical_key_fields,
            ("canonical_project_id", "legal_entity_id", "wbs_or_cost_code", "valid_at"),
        )
        self.assertFalse(policy.fuzzy_final_mapping_allowed)
        self.assertFalse(policy.company_approval_state_managed)

        payload = json.loads(
            (MODULE_ROOT / "templates" / "project_identity.template.json").read_text(encoding="utf-8")
        )
        schema = json.loads(
            (MODULE_ROOT / "schemas" / "project_record.schema.json").read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(payload)), [])

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "IDENTITY_AMBIGUITY_ALLOWED": 0,
            "UNRESOLVED_FINAL_MAPPING_ALLOWED": 0,
            "IDENTITY_EFFECTIVE_END_INCLUSIVE": 1,
            "IDENTITY_FUZZY_FINAL_MAPPING_ALLOWED": 0,
        }
        for parameter_id, value in expected.items():
            self.assertEqual(parameters[parameter_id]["value"], str(value))
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R4")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-005"]["status"], "IMPLEMENTED_R4")
        self.assertIn("tests/test_identity.py", traceability["REQ-005"]["evidence"])

    def test_r5_reader_accounting_templates_schemas_parameters_and_traceability_agree(self) -> None:
        reader_path = MODULE_ROOT / "config" / "kingdee_reader_profile.template.yml"
        bundle_path = MODULE_ROOT / "config" / "kingdee_bundle_profile.template.yml"
        accounting_path = MODULE_ROOT / "config" / "accounting_basis_policy.template.yml"
        reader = KingdeeReaderProfile.from_yaml(reader_path)
        bundle = KingdeeBundleProfile.from_yaml(bundle_path)
        accounting = AccountingBasisPolicy.from_yaml(accounting_path)
        self.assertEqual(reader.status, "TEMPLATE_NOT_ACTIVE")
        self.assertEqual(bundle.status, "TEMPLATE_NOT_ACTIVE")
        self.assertEqual(accounting.status, "TEMPLATE_NOT_ACTIVE")
        with self.assertRaises(KingdeeReaderError) as reader_block:
            reader.validate(require_active=True)
        self.assertEqual(reader_block.exception.code, "READER_PROFILE_NOT_ACTIVE")
        with self.assertRaises(KingdeeBundleError) as bundle_block:
            bundle.validate(require_active=True)
        self.assertEqual(bundle_block.exception.code, "BUNDLE_PROFILE_NOT_ACTIVE")
        with self.assertRaises(AccountingBasisError) as accounting_block:
            accounting.validate(require_active=True)
        self.assertEqual(accounting_block.exception.code, "ACCOUNTING_POLICY_NOT_ACTIVE")

        template_pairs = [
            (reader_path, MODULE_ROOT / "schemas" / "kingdee_reader_profile.schema.json"),
            (bundle_path, MODULE_ROOT / "schemas" / "kingdee_bundle_profile.schema.json"),
            (accounting_path, MODULE_ROOT / "schemas" / "accounting_basis_policy.schema.json"),
        ]
        for template_path, schema_path in template_pairs:
            with self.subTest(template=template_path.name):
                payload = yaml.safe_load(template_path.read_text(encoding="utf-8"))
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                validator = Draft202012Validator(schema, format_checker=FormatChecker())
                self.assertEqual(list(validator.iter_errors(payload)), [])

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "KINGDEE_READER_VERSION": "2.0.0",
            "KINGDEE_PROFILE_MAX_DATA_ROWS_CEILING": "5000000",
            "KINGDEE_BUNDLE_MEMBER_DISPOSITION_REQUIRED": "1",
            "KINGDEE_BUNDLE_INCLUDED_LEGACY_XLS_ALLOWED": "0",
            "KINGDEE_BUNDLE_SCRATCH_EMPTY_REQUIRED": "1",
            "ACCOUNTING_POLICY_TEMPLATE_ACTIVE": "0",
            "ACCOUNTING_UNKNOWN_STATUS_OR_ROW_KIND_ALLOWED": "0",
            "WIP_BRIDGE_DELTA_MINOR": "0",
            "WIP_COGS_TRANSFER_DELTA_MINOR": "0",
            "CLOSED_PERIOD_PRIOR_SNAPSHOT_REQUIRED": "1",
            "NON_CNY_FINAL_METRIC_ALLOWED": "0",
            "SKILL_COMPANY_APPROVAL_STATE_MANAGED": "0",
            "REQUESTED_ACCOUNTING_SCOPE_REQUIRED": "1",
        }
        for parameter_id, value in expected.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R5")

        formula_registry = yaml.safe_load((MODULE_ROOT / "formula_registry.yaml").read_text(encoding="utf-8"))
        wip = {item["formula_id"]: item for item in formula_registry["formulas"]}["FORM-WIP-BRIDGE-V2"]
        self.assertEqual(wip["status"], "IMPLEMENTED_ENGINE_R5_ACTIVE_PRIVATE_POLICY_REQUIRED")
        self.assertIn("5001", wip["companion_control"])
        self.assertIn("6401", wip["companion_control"])

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-010"]["status"], "IMPLEMENTED_R5")
        self.assertIn("tests/test_accounting_basis.py", traceability["REQ-010"]["evidence"])

        public_contract = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                reader_path,
                bundle_path,
                accounting_path,
                MODULE_ROOT / "schemas" / "accounting_basis_policy.schema.json",
            )
        ).casefold()
        for forbidden in ("finance_owner", "authorized_person", "approval_assignee", "company_approver"):
            self.assertNotIn(forbidden, public_contract)

    def test_r5_governed_policy_files_reject_alias_duplicate_and_hardlink_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            alias = root / "alias.yml"
            alias.write_text("root: &value 1\ncopy: *value\n", encoding="utf-8")
            duplicate = root / "duplicate.yml"
            duplicate.write_text("schema_version: one\nschema_version: two\n", encoding="utf-8")
            for path, loader in (
                (alias, KingdeeReaderProfile.from_yaml),
                (duplicate, AccountingBasisPolicy.from_yaml),
                (duplicate, KingdeeBundleProfile.from_yaml),
            ):
                with self.subTest(path=path.name):
                    with self.assertRaises((KingdeeReaderError, KingdeeBundleError, AccountingBasisError)) as caught:
                        loader(path)
                    self.assertEqual(caught.exception.code, "CONFIG_PARSE")

            copied = root / "policy.yml"
            linked = root / "policy-hardlink.yml"
            shutil.copyfile(MODULE_ROOT / "config" / "accounting_basis_policy.template.yml", copied)
            os.link(copied, linked)
            with self.assertRaises(AccountingBasisError) as caught:
                AccountingBasisPolicy.from_yaml(copied)
            self.assertEqual(caught.exception.code, "CONFIG_PATH_UNSAFE")

    def test_r6_lifecycle_templates_schemas_parameters_and_traceability_agree(self) -> None:
        profile_names = (
            "redcircle_invoice_reader_profile.template.yml",
            "redcircle_payment_reader_profile.template.yml",
            "contract_change_reader_profile.template.yml",
            "collection_reader_profile.template.yml",
        )
        schema = json.loads(
            (MODULE_ROOT / "schemas" / "lifecycle_reader_profile.schema.json").read_text(encoding="utf-8")
        )
        profiles = []
        for name in profile_names:
            path = MODULE_ROOT / "config" / name
            profile = LifecycleReaderProfile.from_yaml(path)
            profiles.append(profile)
            self.assertEqual(profile.status, "TEMPLATE_NOT_ACTIVE")
            self.assertEqual(profile.reader_version, LIFECYCLE_READER_VERSION)
            with self.assertRaises(LifecycleReaderError) as blocked:
                profile.validate(require_active=True)
            self.assertEqual(blocked.exception.code, "LIFECYCLE_PROFILE_NOT_ACTIVE")
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(
                list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload)),
                [],
            )
        self.assertEqual(
            {item.slot_id for item in profiles},
            {"project_billing", "cash_out", "contract_and_changes", "cash_in"},
        )

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "LIFECYCLE_READER_VERSION": "2.0.0",
            "LIFECYCLE_PROFILE_MAX_DATA_ROWS_CEILING": "5000000",
            "LIFECYCLE_MULTI_SOURCE_SELECTION_ALLOWED": "1",
            "LIFECYCLE_AUTOMATIC_PROJECT_ASSIGNMENT_ALLOWED": "0",
            "LIFECYCLE_READER_FINAL_METRIC_INCLUSION_ALLOWED": "0",
            "LIFECYCLE_UNKNOWN_SEMANTICS_ALLOWED": "0",
            "LIFECYCLE_REVERSED_EVENT_LINEAGE_REQUIRED": "1",
            "EXACT_EXPORT_DUPLICATE_CONTENT_REQUIRED": "1",
            "DUPLICATE_ALIAS_CHANGES_BUSINESS_FINGERPRINT": "0",
            "SOURCE_ARITHMETIC_OVERWRITE_ALLOWED": "0",
        }
        for parameter_id, value in expected.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R6")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        for requirement_id in ("REQ-008",):
            self.assertEqual(traceability[requirement_id]["status"], "IMPLEMENTED_R9")
            self.assertIn("tests/test_lifecycle_readers.py", traceability[requirement_id]["evidence"])

        public_contract = "\n".join(
            (MODULE_ROOT / "config" / name).read_text(encoding="utf-8") for name in profile_names
        ).casefold()
        for forbidden in ("finance_owner", "authorized_person", "approval_assignee", "company_approver"):
            self.assertNotIn(forbidden, public_contract)

    def test_r7_dedup_links_reconciliation_parameters_and_traceability_agree(self) -> None:
        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        models = {item["model_id"]: item for item in model_registry["models"]}
        expected_models = {
            "POLICY-KMFA-SAME-STAGE-DEDUP-001": "IMPLEMENTED_R7_RELEASE_VALIDATED_R12",
            "MODEL-KMFA-EVENT-LINK-001": "IMPLEMENTED_R7_WITH_R9_EXPLICIT_METRIC_ADAPTER",
            "POLICY-KMFA-SOURCE-CONSERVATION-001": "IMPLEMENTED_EVENT_LEVEL_R7_AND_METRIC_LEVEL_R9",
        }
        for model_id, status in expected_models.items():
            self.assertEqual(models[model_id]["status"], status)
            self.assertFalse(models[model_id]["internal_company_approval_managed"])

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected_parameters = {
            "CANDIDATE_PAIR_BUDGET_MAX": "1000000",
            "CROSS_STAGE_DEDUP_ALLOWED": "0",
            "SIMILARITY_AUTO_LINK_APPROVAL_ALLOWED": "0",
            "LINK_ALLOCATION_AUTOSPREAD_ALLOWED": "0",
            "EVENT_LINK_ALLOCATION_DELTA_MINOR": "0",
            "SOURCE_CONSERVATION_DELTA_MINOR": "0",
            "DUAL_CHANNEL_DELTA_MINOR": "0",
            "R7_FINAL_METRIC_INCLUSION_ALLOWED": "0",
        }
        for parameter_id, value in expected_parameters.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R7")
        self.assertEqual(parameters["SKILL_COMPANY_APPROVAL_STATE_MANAGED"]["value"], "0")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-006"]["status"], "IMPLEMENTED_R7")
        self.assertEqual(traceability["REQ-007"]["status"], "IMPLEMENTED_R7")
        self.assertEqual(traceability["REQ-013"]["status"], "IMPLEMENTED_EVENT_R7_AND_METRIC_R9")
        self.assertIn("tests/test_event_links.py", traceability["REQ-006"]["evidence"])
        self.assertIn("tests/test_reconciliation.py", traceability["REQ-013"]["evidence"])

        for schema_name in (
            "relation_event.schema.json",
            "dedup_decision.schema.json",
            "event_link.schema.json",
            "source_conservation.schema.json",
        ):
            schema = json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)

        public_contract = "\n".join(
            (MODULE_ROOT / path).read_text(encoding="utf-8")
            for path in (
                "src/project_cost_table/dedup.py",
                "src/project_cost_table/links.py",
                "src/project_cost_table/reconciliation.py",
                "schemas/event_link.schema.json",
                "schemas/source_conservation.schema.json",
            )
        ).casefold()
        for forbidden in ("finance_owner", "authorized_person", "approval_assignee", "company_approver"):
            self.assertNotIn(forbidden, public_contract)

    def test_r8_formula_payroll_policy_parameters_and_traceability_agree(self) -> None:
        formula_path = MODULE_ROOT / "config" / "formula_profile.template.yml"
        component_path = MODULE_ROOT / "config" / "pay_component_registry.template.yml"
        payroll_path = MODULE_ROOT / "config" / "payroll_allocation_policy.template.yml"
        formula = FormulaProfile.from_yaml(formula_path)
        components = PayComponentRegistry.from_yaml(component_path)
        payroll = PayrollAllocationPolicy.from_yaml(payroll_path)
        self.assertEqual(formula.status, FormulaStatus.TEMPLATE_NOT_ACTIVE)
        self.assertEqual(components.status, "TEMPLATE_NOT_ACTIVE")
        self.assertEqual(payroll.status, "TEMPLATE_NOT_ACTIVE")
        with self.assertRaises(FormulaError):
            formula.validate(require_active=True)
        with self.assertRaises(PayrollError):
            components.validate(require_active=True)
        with self.assertRaises(PayrollError):
            payroll.validate(require_active=True)

        template_pairs = (
            (formula_path, MODULE_ROOT / "schemas" / "formula_profile.schema.json"),
            (component_path, MODULE_ROOT / "schemas" / "pay_component_registry.schema.json"),
            (payroll_path, MODULE_ROOT / "schemas" / "payroll_allocation_policy.schema.json"),
        )
        for template_path, schema_path in template_pairs:
            payload = yaml.safe_load(template_path.read_text(encoding="utf-8"))
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(
                list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload)), []
            )
        for schema_name in (
            "formula_readiness.schema.json",
            "payroll_allocation.schema.json",
            "project_tax.schema.json",
            "interest_input.schema.json",
            "manual_adjustment.schema.json",
        ):
            Draft202012Validator.check_schema(
                json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            )

        formula_registry = yaml.safe_load((MODULE_ROOT / "formula_registry.yaml").read_text(encoding="utf-8"))
        formulas = {item["formula_id"]: item for item in formula_registry["formulas"]}
        for formula_id in ("FORM-MGMT-V2", "FORM-PAYROLL-V2", "FORM-TAX-V2", "FORM-INTEREST-V2"):
            self.assertIn("IMPLEMENTED_ENGINE_R8", formulas[formula_id]["status"])
        observation = formula_registry["reference_observations"][0]
        self.assertEqual(observation["status"], "REFERENCE_OBSERVED_NOT_ACTIVE")
        self.assertFalse(observation["activation_allowed"])
        self.assertIn("DEFERRED", formula_registry["rate_registry"]["fx_rate"])

        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        models = {item["model_id"]: item for item in model_registry["models"]}
        expected_models = {
            "POLICY-KMFA-FORMULA-RATE-001": "IMPLEMENTED_R8_ACTIVE_PRIVATE_PROFILES_REQUIRED",
            "POLICY-KMFA-FULLY-LOADED-PAYROLL-001": "IMPLEMENTED_R8_ACTIVE_PRIVATE_REGISTRY_CONTROLS_TIME_AND_POLICY_REQUIRED",
            "POLICY-KMFA-TAX-INTEREST-001": "IMPLEMENTED_R8_ACTIVE_PRIVATE_EVIDENCE_AND_POLICY_REQUIRED",
            "MODEL-KMFA-MANUAL-ADJUSTMENT-001": "IMPLEMENTED_R8_WITH_R9_EXPLICIT_METRIC_DECISION_REQUIRED",
        }
        for model_id, status in expected_models.items():
            self.assertEqual(models[model_id]["status"], status)
            self.assertFalse(models[model_id]["internal_company_approval_managed"])
            self.assertEqual(models[model_id]["metric_inclusion_status"], "NOT_EVALUATED_R8")

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected_parameters = {
            "FORMULA_UNKNOWN_METRIC_INCLUSION_ALLOWED": "0",
            "FORMULA_ACTIVE_SCOPE_OVERLAP_ALLOWED": "0",
            "FORMULA_EXECUTABLE_TEST_VECTOR_REQUIRED": "1",
            "FORMULA_REQUEST_INPUT_CONFIG_HASH_BINDING_REQUIRED": "1",
            "MANAGEMENT_OBSERVED_RATE_DEFAULT_ACTIVE": "0",
            "PAYROLL_AUTOMATIC_UNALLOCATED_SPREAD_ALLOWED": "0",
            "PAYROLL_CONTROL_DELTA_MINOR": "0",
            "PAYROLL_TIME_CONTROL_DELTA_UNITS": "0",
            "PAYROLL_ALLOCATION_DELTA_MINOR": "0",
            "PAYROLL_CROSS_ENTITY_ALLOCATION_ALLOWED": "0",
            "PROJECT_TAX_COMPANY_RETURN_DEFAULT_ALLOCATION_ALLOWED": "0",
            "SOURCE_TAX_OVERWRITE_ALLOWED": "0",
            "FX_RATE_ACTIVE_PRODUCT_0_2_ALLOWED": "0",
            "MANUAL_ADJUSTMENT_AUTOMATIC_REVERSAL_ALLOWED": "0",
            "R8_FINAL_METRIC_INCLUSION_ALLOWED": "0",
        }
        for parameter_id, value in expected_parameters.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R8")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            traceability["REQ-009"]["status"],
            "IMPLEMENTED_R8_POLICY_ENGINE_REAL_ACTIVE_INPUTS_REQUIRED",
        )
        self.assertIn("tests/test_payroll.py", traceability["REQ-009"]["evidence"])

        public_contract = "\n".join(
            (MODULE_ROOT / path).read_text(encoding="utf-8")
            for path in (
                "src/project_cost_table/formulas.py",
                "src/project_cost_table/payroll.py",
                "src/project_cost_table/adjustments.py",
                "config/formula_profile.template.yml",
                "config/pay_component_registry.template.yml",
                "config/payroll_allocation_policy.template.yml",
            )
        ).casefold()
        for forbidden in ("finance_owner", "authorized_person", "approval_assignee", "company_approver"):
            self.assertNotIn(forbidden, public_contract)

    def test_r9_metrics_status_workbook_and_generation_contracts_agree(self) -> None:
        status_codes = yaml.safe_load((MODULE_ROOT / "config" / "status_codes.yml").read_text(encoding="utf-8"))
        self.assertFalse(status_codes["company_approval_status_managed"])
        self.assertFalse(status_codes["finance_owner_or_authorized_person_managed"])
        self.assertEqual(
            set(status_codes["generation_status"]),
            {"NOT_GENERATED", "FINAL_GENERATED", "BLOCKED_DIAGNOSTICS_GENERATED", "FAILED", "SUPERSEDED"},
        )

        catalog = MetricCatalog.from_yaml(MODULE_ROOT / "config" / "metric_catalog.yml")
        rules = catalog.metric_map()
        self.assertEqual(rules["COST_POSTED_ACTUAL"].aggregation, "DIRECT")
        self.assertEqual(
            set(rules["COST_POSTED_ACTUAL"].allowed_basis_ids),
            {"JOB_COST_INCURRED", "GL_RECOGNIZED_COGS"},
        )
        self.assertEqual(rules["MARGIN_ACCOUNTING"].aggregation, "DERIVED")

        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        models = {item["model_id"]: item for item in model_registry["models"]}
        for model_id in (
            "MODEL-KMFA-NAMED-METRIC-001",
            "POLICY-KMFA-FOUR-STATUS-PLANES-001",
            "POLICY-KMFA-SAFE-WORKBOOK-001",
            "POLICY-KMFA-FINAL-GENERATION-001",
        ):
            self.assertEqual(models[model_id]["status"], "IMPLEMENTED_R9_RELEASE_VALIDATED_R12")
            self.assertFalse(models[model_id]["internal_company_approval_managed"])
        self.assertFalse(models["POLICY-KMFA-FOUR-STATUS-PLANES-001"]["finance_owner_or_authorized_person_managed"])
        self.assertFalse(models["POLICY-KMFA-FINAL-GENERATION-001"]["finance_owner_or_authorized_person_managed"])

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected_parameters = {
            "METRIC_DUAL_CHANNEL_DELTA_MINOR": "0",
            "METRIC_SOURCE_CONSERVATION_DELTA_MINOR": "0",
            "FINAL_GENERATION_REQUIRES_ALL_GATES": "1",
            "BLOCKED_FINAL_LOOKING_WORKBOOK_ALLOWED": "0",
            "OUTPUT_INDEX_ABSOLUTE_PATH_REQUIRED": "1",
            "RUN_SEAL_SELF_HASH_ALLOWED": "0",
            "INTERNAL_PROCESS_HANDOFF_FINAL_ONLY": "1",
            "WORKBOOK_FORMULA_CELL_ALLOWED": "0",
            "WORKBOOK_EXTERNAL_RELATIONSHIP_ALLOWED": "0",
            "WORKBOOK_ACTIVE_CONTENT_ALLOWED": "0",
            "WORKBOOK_VISIBLE_SHEET_COUNT": "8",
            "WORKBOOK_RUNTIME_EXPLICIT_DEPENDENCY_REQUIRED": "1",
            "FINANCE_OWNER_OR_AUTHORIZED_PERSON_MANAGED": "0",
        }
        for parameter_id, value in expected_parameters.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R9")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        for requirement_id in ("REQ-008", "REQ-012", "REQ-015"):
            self.assertEqual(traceability[requirement_id]["status"], "IMPLEMENTED_R9")
        self.assertEqual(traceability["REQ-014"]["status"], "IMPLEMENTED_R9_R11")
        self.assertEqual(traceability["REQ-019"]["status"], "IMPLEMENTED_R9_R11")
        self.assertEqual(traceability["REQ-013"]["status"], "IMPLEMENTED_EVENT_R7_AND_METRIC_R9")

        for schema_name in (
            "metric_fact.schema.json",
            "metric_facts.schema.json",
            "metric_snapshot.schema.json",
            "metric_batch.schema.json",
            "status_planes.schema.json",
            "run_manifest.schema.json",
            "output_index.schema.json",
        ):
            Draft202012Validator.check_schema(
                json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            )
        self.assertTrue((MODULE_ROOT / "references" / "METRICS_WORKBOOK_GENERATION.md").is_file())
        skill_text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("INTERNAL_PROCESS_HANDOFF.md", skill_text)
        self.assertIn("绝对", skill_text)

    def test_r10_reference_replay_isolation_contracts_agree(self) -> None:
        governance = yaml.safe_load((MODULE_ROOT / "governance.yaml").read_text(encoding="utf-8"))
        self.assertEqual(governance["run_status"]["R10"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R11"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R12"], "COMPLETE")

        status_codes = yaml.safe_load((MODULE_ROOT / "config" / "status_codes.yml").read_text(encoding="utf-8"))
        self.assertEqual(
            set(status_codes["replay_fidelity_status"]),
            {"NOT_EVALUATED", "EXACT", "BLOCKED_HASH", "BLOCKED_LINE_DELTA"},
        )
        self.assertEqual(
            set(status_codes["source_quality_status"]),
            {"CONSISTENT", "SOURCE_ARITHMETIC_DIFFERENCE", "UNKNOWN"},
        )

        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        models = {item["model_id"]: item for item in model_registry["models"]}
        isolation = models["POLICY-KMFA-REFERENCE-REPLAY-ISOLATION-001"]
        replay = models["MODEL-KMFA-REFERENCE-REPLAY-001"]
        self.assertEqual(isolation["status"], "IMPLEMENTED_R10_RELEASE_VALIDATED_R12")
        self.assertEqual(replay["status"], "IMPLEMENTED_R10_RELEASE_VALIDATED_R12")
        self.assertFalse(isolation["calculate_imports_reference_replay_allowed"])
        self.assertFalse(isolation["reference_values_available_to_calculate"])
        self.assertEqual(isolation["replay_calculation_status"], "NOT_EVALUATED")
        self.assertFalse(replay["source_arithmetic_overwrite_allowed"])
        self.assertEqual(replay["expected_reference_project_count"], 8)
        self.assertFalse(replay["internal_company_approval_managed"])

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected_parameters = {
            "REFERENCE_REPLAY_EXPECTED_PROJECT_COUNT": "8",
            "REFERENCE_REPLAY_FIDELITY_DELTA_MINOR": "0",
            "CALCULATE_REFERENCE_IMPORT_ALLOWED": "0",
            "REFERENCE_SOURCE_ARITHMETIC_OVERWRITE_ALLOWED": "0",
            "REFERENCE_REPLAY_CALCULATION_EVALUATED": "0",
            "REFERENCE_REPLAY_FINAL_WORKBOOK_ALLOWED": "0",
            "REFERENCE_REPLAY_INTERNAL_HANDOFF_ALLOWED": "0",
        }
        for parameter_id, value in expected_parameters.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R10")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-011"]["status"], "IMPLEMENTED_R10_R11")
        self.assertIn("tests/test_reference_replay.py", traceability["REQ-011"]["evidence"])

        for schema_name in (
            "reference_baseline.schema.json",
            "reference_baseline_import.schema.json",
            "reference_replay_result.schema.json",
        ):
            Draft202012Validator.check_schema(
                json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            )
        self.assertTrue((MODULE_ROOT / "references" / "REFERENCE_REPLAY_ISOLATION.md").is_file())
        skill_text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("RELEASED_0_2_0_FAIL_CLOSED", skill_text)
        self.assertIn("run_reference_regression.py", skill_text)

    def test_r11_current_expected_block_contracts_agree(self) -> None:
        governance = yaml.safe_load((MODULE_ROOT / "governance.yaml").read_text(encoding="utf-8"))
        self.assertEqual(governance["run_status"]["R11"], "COMPLETE")
        self.assertEqual(governance["run_status"]["R12"], "COMPLETE")

        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        models = {item["model_id"]: item for item in model_registry["models"]}
        source_contract = models["MODEL-KMFA-CURRENT-SOURCE-CONTRACT-001"]
        expected_block = models["POLICY-KMFA-CURRENT-EXPECTED-BLOCK-001"]
        self.assertEqual(source_contract["status"], "IMPLEMENTED_R11_RELEASE_VALIDATED_R12")
        self.assertEqual(expected_block["status"], "IMPLEMENTED_R11_RELEASE_VALIDATED_R12")
        self.assertFalse(source_contract["selected_reference_source_allowed"])
        self.assertTrue(source_contract["both_actual_cost_bases_required"])
        self.assertFalse(source_contract["source_drift_snapshot_overwrite_allowed"])
        self.assertEqual(expected_block["production_expected_exit_code"], 3)
        self.assertEqual(expected_block["harness_exact_match_exit_code"], 0)
        self.assertEqual(expected_block["current_expected_blocker_count"], 9)
        self.assertFalse(expected_block["production_reads_expected_contract"])
        self.assertFalse(expected_block["calculate_reference_data_flow_allowed"])
        self.assertFalse(expected_block["blocked_final_workbook_allowed"])
        self.assertFalse(expected_block["finance_owner_or_authorized_person_managed"])

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected_parameters = {
            "CURRENT_PRODUCTION_BLOCK_EXIT_CODE": "3",
            "CURRENT_EXPECTED_BLOCK_HARNESS_PASS_EXIT_CODE": "0",
            "CURRENT_EXPECTED_BLOCKER_COUNT": "9",
            "CURRENT_EXPECTED_PROJECT_COUNT": "8",
            "CURRENT_ACTUAL_COST_BASIS_COUNT": "2",
            "CALCULATE_REFERENCE_SOURCE_BINDING_ALLOWED": "0",
            "CURRENT_SOURCE_SNAPSHOT_OVERWRITE_ON_DRIFT_ALLOWED": "0",
        }
        for parameter_id, value in expected_parameters.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R11")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-011"]["status"], "IMPLEMENTED_R10_R11")
        self.assertIn("tests/test_current_reconstruction.py", traceability["REQ-011"]["evidence"])
        self.assertEqual(traceability["REQ-018"]["status"], "IMPLEMENTED_R3_R11")
        self.assertEqual(traceability["REQ-019"]["status"], "IMPLEMENTED_R9_R11")

        for schema_name in (
            "current_source_contract.schema.json",
            "expected_block_contract.schema.json",
            "expected_block_validation.schema.json",
        ):
            Draft202012Validator.check_schema(
                json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            )
        current_reference = (
            MODULE_ROOT / "references" / "CURRENT_RECONSTRUCTION_EXPECTED_BLOCK.md"
        ).read_text(encoding="utf-8")
        skill_text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("RELEASED_0_2_0_FAIL_CLOSED", skill_text)
        self.assertIn("prepare_current_regression.py", skill_text)
        self.assertIn("run_current_source_reconstruction.py", skill_text)
        self.assertIn("validate_current_expected_block.py", skill_text)
        self.assertIn("第二次生产运行", skill_text)
        self.assertIn("harness `0`", skill_text)
        self.assertIn("未回复不构成授权", skill_text)
        self.assertIn("绝对", skill_text)
        for script_name in (
            "prepare_current_regression.py",
            "run_current_source_reconstruction.py",
            "validate_current_expected_block.py",
        ):
            self.assertIn(script_name, current_reference)
        self.assertIn("does **not** inspect the direct-production directory", current_reference)
        self.assertIn("exit `3`", current_reference)
        self.assertIn("exit `0`", current_reference)
        self.assertIn("exit `1`", current_reference)

    def test_r12_release_performance_and_global_install_boundary_agree(self) -> None:
        governance = yaml.safe_load((MODULE_ROOT / "governance.yaml").read_text(encoding="utf-8"))
        self.assertEqual(governance["product_version"], "0.2.0")
        self.assertTrue(all(governance["run_status"]["R%d" % number] == "COMPLETE" for number in range(13)))
        self.assertEqual(governance["run_status"]["GLOBAL_INSTALL"], "MACHINE_LOCAL_EXTERNAL")

        model_registry = yaml.safe_load((MODULE_ROOT / "model_registry.yaml").read_text(encoding="utf-8"))
        models = {item["model_id"]: item for item in model_registry["models"]}
        release = models["POLICY-KMFA-RELEASE-PERFORMANCE-001"]
        self.assertEqual(release["status"], "IMPLEMENTED_R12_RELEASED")
        self.assertEqual(release["subsequent_wall_and_peak_rss_factor_max"], "1.50")
        self.assertEqual(release["selected_source_full_digest_per_run_max"], 1)
        self.assertEqual(release["candidate_pair_budget_max"], 1_000_000)
        self.assertFalse(release["global_unpartitioned_matching_allowed"])
        self.assertFalse(release["application_digest_cache_allowed"])
        self.assertEqual(release["current_real_calculation_baseline_status"], "NOT_EVALUATED_BLOCKED_SOURCE")
        self.assertFalse(release["global_install_performed"])
        self.assertFalse(release["internal_company_approval_managed"])
        self.assertFalse(release["finance_owner_or_authorized_person_managed"])
        for model in models.values():
            self.assertNotIn("NOT_RELEASED", model["status"])
            self.assertNotIn("PARTIAL_IMPLEMENTATION", model["status"])

        performance = yaml.safe_load(
            (MODULE_ROOT / "config" / "performance_budgets.yml").read_text(encoding="utf-8")
        )
        budget_schema = json.loads(
            (MODULE_ROOT / "schemas" / "performance_budget.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(budget_schema).iter_errors(performance)), [])
        Draft202012Validator.check_schema(
            json.loads((MODULE_ROOT / "schemas" / "performance_summary.schema.json").read_text(encoding="utf-8"))
        )

        with (MODULE_ROOT / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            parameters = {row["parameter_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "PERFORMANCE_REGRESSION_FACTOR_MAX": "1.50",
            "PERFORMANCE_COLD_PROCESS_RUNS": "1",
            "PERFORMANCE_SUBSEQUENT_PROCESS_RUNS": "3",
            "SELECTED_SOURCE_FULL_DIGEST_PER_RUN_MAX": "1",
            "SELECTED_MEMBER_PARSE_PER_VERIFIED_DIGEST_MAX": "1",
            "GLOBAL_UNPARTITIONED_MATCHING_ALLOWED": "0",
            "APPLICATION_DIGEST_CACHE_ALLOWED": "0",
            "FINAL_GENERATION_FULL_DIGEST_REQUIRED": "1",
            "R12_GLOBAL_INSTALL_ALLOWED": "0",
        }
        for parameter_id, value in expected.items():
            self.assertEqual(parameters[parameter_id]["value"], value)
            self.assertEqual(parameters[parameter_id]["status"], "ACTIVE_R12")

        with (MODULE_ROOT / "TRACEABILITY_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            traceability = {row["requirement_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(traceability["REQ-017"]["run_id"], "R12")
        self.assertEqual(traceability["REQ-017"]["status"], "IMPLEMENTED_R12")
        self.assertIn("tests/test_release.py", traceability["REQ-017"]["evidence"])

        formula_registry = yaml.safe_load((MODULE_ROOT / "formula_registry.yaml").read_text(encoding="utf-8"))
        self.assertTrue(all(item["status"].startswith("IMPLEMENTED") for item in formula_registry["formulas"]))
        matrix = yaml.safe_load((MODULE_ROOT / "config" / "release_test_matrix.yml").read_text(encoding="utf-8"))
        self.assertEqual(
            set(matrix["families"]),
            {
                "adversarial",
                "property",
                "metamorphic",
                "package_governance",
                "workbook_runtime",
                "private_reference_replay",
                "private_current_source",
                "performance",
            },
        )
        release_reference = (
            MODULE_ROOT / "references" / "RELEASE_PERFORMANCE_AND_OPERABILITY.md"
        ).read_text(encoding="utf-8")
        skill_text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "run_release_benchmark.py",
            "validate_skill_package.py",
            "NOT_EVALUATED_BLOCKED_SOURCE",
            "绝对",
            "不设置财务负责人或授权人",
            "不管理公司内部审批",
        ):
            self.assertIn(token, skill_text + release_reference)


if __name__ == "__main__":
    unittest.main()
