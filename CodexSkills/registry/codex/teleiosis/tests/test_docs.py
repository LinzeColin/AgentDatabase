from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from helpers import ROOT, load_json


class DocumentationTests(unittest.TestCase):
    def test_single_physical_skill_four_logical_engines(self) -> None:
        release = load_json("metadata/release.json")
        self.assertEqual(release["architecture"], "single-skill-four-built-in-full-run-engines")
        self.assertEqual(release["run_contract"], "T-C-S-C-P-C-A-C x 3 rounds x 3 groups")
        self.assertEqual(sorted(path.name for path in (ROOT / "modules").iterdir() if path.is_dir()), ["arena_lab", "product_reality_lab", "raw_teleiosis", "skill_market_lab"])

    def test_no_standalone_registry_skill_is_packaged(self) -> None:
        forbidden = {"skill-market-lab", "product-reality-lab", "arena-lab", "external-verifier"}
        names = {path.name for path in ROOT.rglob("*") if path.is_dir()}
        self.assertTrue(forbidden.isdisjoint(names))

    def test_architecture_diagram_contains_all_engines_and_external_verifier(self) -> None:
        text = (ROOT / "architecture/teleiosis-v5.mmd").read_text(encoding="utf-8")
        for token in ["Teleiosis", "Skill Market Lab", "Product Reality Lab", "Arena Lab", "External Verifier"]:
            self.assertIn(token, text)

    def test_data_contract_diagram_contains_arena_contracts(self) -> None:
        text = (ROOT / "architecture/data-contracts.mmd").read_text(encoding="utf-8")
        self.assertIn("ArenaSpec", text)
        self.assertIn("ArenaResult", text)
        self.assertIn("CandidateIdentity", text)

    def test_public_human_docs_are_chinese(self) -> None:
        for rel in ["README.md", "INSTALL.md", "ROADMAP.md", "delivery/HANDOFF.md", "delivery/ONE_CLICK.md"]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertRegex(text, r"[\u4e00-\u9fff]")

    def test_pursuing_goal_is_single_clear_sentence(self) -> None:
        text = (ROOT / "PURSUING_GOAL.txt").read_text(encoding="utf-8").strip()
        self.assertGreater(len(text), 30)
        self.assertIn("同预算密封竞技", text)
        self.assertIn("外部独立复验", text)
        self.assertNotIn("\n", text)

    def test_roadmap_keeps_future_scope_outside_current_release(self) -> None:
        text = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        self.assertIn("L3", text)
        self.assertIn("L4", text)
        self.assertIn("后续路线不改变 v0.0.0.5", text)

    def test_build_estimate_has_p80_p95_and_active_wait_split(self) -> None:
        data = load_json("metadata/build-estimate.json")
        self.assertGreater(data["total"]["p95_tokens"], data["total"]["p80_tokens"])
        self.assertLessEqual(len(data["largest_cost_drivers"]), 5)
        for item in data["stages"]:
            self.assertTrue(0 < item["active_ratio"] <= 1)
            self.assertEqual(item["active_minutes_p80"] + item["wait_minutes_p80"], item["wall_minutes_p80"])
            self.assertEqual(item["active_minutes_p95"] + item["wait_minutes_p95"], item["wall_minutes_p95"])
            self.assertGreaterEqual(item["turns_p95"], item["turns_p80"])
            self.assertGreaterEqual(item["retry_factor_p95"], item["retry_factor_p80"])

    def test_source_ledger_records_first_party_base_and_no_third_party_code_copy(self) -> None:
        ledger = load_json("metadata/source-ledger.json")
        self.assertTrue(ledger["sources"])
        first_party = next(item for item in ledger["sources"] if item["id"] == "SRC-V4-LOCAL-CANDIDATE")
        self.assertTrue(first_party["code_copied"])
        third_party = [item for item in ledger["sources"] if item["id"] in {"SRC-GEPA", "SRC-AUTORESEARCH", "SRC-METAHARNESS", "SRC-PROMPTFOO"}]
        self.assertTrue(all(item["code_copied"] is False for item in third_party))
        ids = {item["id"] for item in ledger["sources"]}
        self.assertTrue({"SRC-GEPA", "SRC-AUTORESEARCH", "SRC-METAHARNESS", "SRC-PROMPTFOO", "SRC-VERIFIER"}.issubset(ids))

    def test_skill_hot_key_owner_source_is_preserved(self) -> None:
        ledger = load_json("metadata/source-ledger.json")
        owner = next(item for item in ledger["sources"] if item["id"] == "SRC-OWNER-HOTKEY")
        self.assertEqual(owner["sha256"], "7c062db3acfc0c19cee61d7c4e28157e67c6d04df45321ab0e3a7263b7458e45")

    def test_external_verifier_is_only_formal_pass_authority(self) -> None:
        boundaries = load_json("metadata/evidence-boundaries.json")
        self.assertEqual(boundaries["formal_pass_authority"], "external independent verifier")
        self.assertEqual(boundaries["internal_engines_cannot_issue_formal_pass"], ["T", "S", "P", "A"])

    def test_review_honesty_is_explicit(self) -> None:
        boundaries = load_json("metadata/evidence-boundaries.json")
        self.assertEqual(boundaries["review_mode_in_this_package"], "role_separated_same_model")
        self.assertEqual(boundaries["formal_independent_review"], "UNAVAILABLE")

    def test_three_skill_catalog_passes_are_evidenced(self) -> None:
        for name in ["skill-pass-a.json", "skill-pass-b.json", "skill-pass-c.json"]:
            data = load_json("evidence/preparation/" + name)
            self.assertIn(data["decision"], {"KEEP", "NO_CHANGE"})
            self.assertTrue(data["developer_burden_delta"])
            self.assertTrue(data["input_hash"])

    def test_ten_lens_review_covers_exactly_ten_views(self) -> None:
        data = load_json("evidence/preparation/ten-lens-review.json")
        self.assertEqual(len(data["lenses"]), 10)
        self.assertEqual([item["lens"] for item in data["lenses"]], list(range(1, 11)))
        self.assertFalse(any(item["open_p0_p1"] for item in data["lenses"]))

    def test_two_role_review_rounds_exist_and_are_not_misrepresented(self) -> None:
        first = load_json("evidence/preparation/role-review-round1.json")
        second = load_json("evidence/preparation/role-review-round2.json")
        self.assertEqual(first["mode"], "role_separated_same_model")
        self.assertEqual(second["mode"], "role_separated_same_model")
        self.assertEqual(len(first["roles"]), 6)
        self.assertEqual(len(second["roles"]), 6)
        self.assertEqual(second["formal_independent_pass"], "UNAVAILABLE")

    def test_fresh_builder_simulation_is_present(self) -> None:
        data = load_json("evidence/preparation/fresh-builder-simulation.json")
        self.assertEqual(data["status"], "ACCEPTANCE_PASS")
        self.assertTrue(data["research_reopened"] is False)
        self.assertTrue(data["only_environment_bound_unknowns_remain"])

    def test_acceptance_contract_has_thirty_unique_criteria(self) -> None:
        criteria = load_json("ACCEPTANCE_CONTRACT.json")["criteria"]
        ids = [item["id"] for item in criteria]
        self.assertEqual(len(ids), 30)
        self.assertEqual(len(set(ids)), 30)
        self.assertTrue(all(item["severity"] == "HARD" for item in criteria))

    def test_task_dag_categories_cover_required_work(self) -> None:
        tasks = load_json("TASK_DAG.json")["tasks"]
        categories = {task["category"] for task in tasks}
        self.assertTrue({"implementation", "testing", "remediation", "review", "research", "release"}.issubset(categories))

    def test_all_schema_files_have_identity_and_object_type(self) -> None:
        for path in (ROOT / "schemas").glob("*.schema.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data.get("type"), "object", path.name)
            self.assertTrue(data.get("$id"), path.name)

    def test_skill_md_is_progressively_disclosed(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(text.splitlines()), 220)
        self.assertIn("references/", text)
        self.assertIn("Arena Lab", text)

    def test_install_command_has_valid_shebang_at_byte_zero(self) -> None:
        data = (ROOT / "INSTALL.command").read_bytes()
        self.assertTrue(data.startswith(b"#!/bin/sh\n"))

    def test_skill_execution_claims_are_honest(self) -> None:
        for name in ["skill-pass-a.json", "skill-pass-b.json", "skill-pass-c.json"]:
            data = load_json("evidence/preparation/" + name)
            self.assertEqual(data["skill"], "teleiosis")
            self.assertEqual(data["formal_independent_review"], "UNAVAILABLE")
            self.assertEqual(data["review_mode"], "role_separated_same_model")
            self.assertEqual(data["catalog_routing"]["persona-distiller-group"]["status"], "ROUTED_METHOD_APPLIED_NOT_FULL_NATIVE_EXECUTION")
            self.assertEqual(data["catalog_routing"]["verifier"]["status"], "CONTRACT_APPLIED_FORMAL_EXECUTION_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
