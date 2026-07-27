from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import load_json, sha256_tree, verify_file_bindings, write_json
from wbi_core.ledger import append_event, verify_event_chain
from wbi_core.workspace import init_run, loop_status, record_change, record_round, update_counters, verify_control_plane, verify_run_seal


class WorkspaceTests(unittest.TestCase):
    def init(self, base: Path, strategies=None, budget=None):
        target = base / "target-skill"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
        if budget:
            write_json(base / "budget.json", budget)
        return init_run(target, base / "run", ROOT, strategies or ["incremental", "architecture", "clean-slate"], base / "budget.json" if budget else None, self_evolve=True)

    def proof(self, workspace: Path, name: str = "proof.json") -> str:
        path = workspace / "evidence/test" / name
        write_json(path, {"status": "PASS", "name": name})
        return path.relative_to(workspace).as_posix()

    def test_init_run_creates_portfolio_and_read_only_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base)
            self.assertEqual(len(run["target"]["candidates"]), 3)
            self.assertTrue(Path(run["target"]["baseline_path"]).is_dir())
            self.assertEqual(run["genesis"]["baseline_hash"], "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086")
            self.assertEqual(verify_event_chain(base / "run/events.jsonl"), [])

    def test_formal_run_accepts_explicit_local_date_and_avoids_legacy_eval_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            target = base / "target-skill"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            run = init_run(target, base / "run", ROOT, ["incremental"], self_evolve=True, valid_as_of="2026-07-26")
            self.assertEqual(run["valid_as_of"], "2026-07-26")
            self.assertEqual(run["valid_as_of_source"], "explicit")
            self.assertFalse((base / "run/control/contracts/eval-contract.json").exists())
            self.assertTrue((base / "run/control/evals/README.md").is_file())

    def test_invalid_explicit_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            target = base / "target-skill"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            with self.assertRaises(ValueError):
                init_run(target, base / "run", ROOT, ["incremental"], valid_as_of="26-07-2026")

    def test_workspace_must_be_external(self):
        with self.assertRaises(ValueError):
            init_run(ROOT, ROOT / "bad-workspace", ROOT, ["incremental"])

    def test_recursive_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            os.environ["WBI_ACTIVE_RUN_ID"] = "already-running"
            try:
                with self.assertRaises(ValueError):
                    self.init(Path(temp))
            finally:
                os.environ.pop("WBI_ACTIVE_RUN_ID", None)

    def test_budget_is_configurable_but_ten_reviews_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            budget = {"max_total_rounds": 25, "max_candidates": 5}
            run = self.init(base, ["incremental", "architecture", "clean-slate", "composition"], budget)
            self.assertEqual(run["budget"]["max_total_rounds"], 25)
            self.assertEqual(run["budget"]["mandatory_review_rounds"], 10)

    def test_no_hardcoded_thirteen_round_ceiling(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"], {"max_total_rounds": 20})
            workspace = base / "run"
            for number in range(1, 15):
                record = base / ("r%d.json" % number)
                write_json(record, {"round": number, "perspective": "p%d" % number, "evidence_paths": [self.proof(workspace, "round-%02d.json" % number)], "candidate_comparison": {"baseline": "equal", "candidate": "equal"}, "decision": "NO_CHANGE", "actor_id": "a", "residual_risk": []})
                record_round(workspace, record)
            self.assertEqual(load_json(workspace / "state.json")["rounds_completed"], 14)

    def test_keep_change_writes_diff_and_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["architecture"])
            workspace = base / "run"
            candidate = run["target"]["candidates"][0]
            root = Path(candidate["path"])
            (root / "README.md").write_text("changed\n", encoding="utf-8")
            record_file = base / "change.json"
            write_json(record_file, {"hypothesis": "change improves clarity", "evidence_paths": [self.proof(workspace, "keep.json")], "actor_id": "optimizer-1", "commands": ["edit README"], "tools": ["editor"], "risk": ["none"], "decision": "KEEP", "architecture_reset": True})
            result = record_change(workspace, candidate["candidate_id"], record_file)
            self.assertEqual(result["decision"], "KEEP")
            self.assertIn("README.md", result["changed_files"])
            self.assertTrue(Path(result["exact_diff_path"]).is_file())

    def test_no_change_rejects_hidden_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"])
            workspace = base / "run"
            candidate = run["target"]["candidates"][0]
            root = Path(candidate["path"])
            (root / "README.md").write_text("changed\n", encoding="utf-8")
            record_file = base / "change.json"
            write_json(record_file, {"hypothesis": "none", "evidence_paths": [self.proof(workspace, "no-change.json")], "actor_id": "optimizer", "commands": [], "tools": [], "risk": [], "decision": "NO_CHANGE"})
            with self.assertRaises(ValueError):
                record_change(workspace, candidate["candidate_id"], record_file)

    def test_revert_preserves_failed_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"])
            workspace = base / "run"
            candidate = run["target"]["candidates"][0]
            root = Path(candidate["path"])
            original = (root / "README.md").read_text(encoding="utf-8")
            (root / "README.md").write_text("bad\n", encoding="utf-8")
            record_file = base / "change.json"
            write_json(record_file, {"hypothesis": "failed", "evidence_paths": [self.proof(workspace, "revert.json")], "actor_id": "optimizer", "commands": [], "tools": [], "risk": ["regression"], "decision": "REVERT"})
            result = record_change(workspace, candidate["candidate_id"], record_file)
            self.assertEqual((root / "README.md").read_text(encoding="utf-8"), original)
            self.assertTrue((workspace / "failed-candidates" / result["change_id"]).is_dir())

    def test_loop_budget_records_multiple_dimensions(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"], {"max_network_requests": 2})
            workspace = base / "run"
            update_counters(workspace, {"network_requests": 2, "tokens": 10})
            result = loop_status(workspace)
            self.assertEqual(result["status"], "STOP")
            self.assertIn("BUDGET_EXHAUSTED:network_requests", result["reasons"])
            self.assertTrue(result["reheat_allowed"])

    def test_change_counter_is_explicit_for_pre_edit_gates(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"])
            workspace_path = base / "run"
            candidate = Path(run["target"]["candidates"][0]["path"])
            (candidate / "new.txt").write_text("x", encoding="utf-8")
            record = base / "change.json"
            write_json(record, {"hypothesis": "h", "evidence_paths": [self.proof(workspace_path, "counter.json")], "actor_id": "a", "commands": [], "tools": [], "risk": ["low"], "decision": "KEEP"})
            record_change(workspace_path, run["target"]["candidates"][0]["candidate_id"], record)
            self.assertEqual(load_json(workspace_path / "state.json")["changes_recorded"], 1)

    def test_change_and_round_evidence_are_content_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"])
            workspace = base / "run"
            candidate = run["target"]["candidates"][0]
            proof_rel = self.proof(workspace, "bound.json")
            candidate_root = Path(candidate["path"])
            (candidate_root / "bound-change.txt").write_text("new\n", encoding="utf-8")
            change_input = base / "change.json"
            write_json(change_input, {
                "hypothesis": "content-bound proof", "evidence_paths": [proof_rel], "actor_id": "optimizer",
                "commands": ["write bound-change.txt"], "tools": ["test"], "risk": [], "decision": "KEEP",
            })
            change = record_change(workspace, candidate["candidate_id"], change_input)
            self.assertEqual(verify_file_bindings(workspace, change["evidence_bindings"], label="change evidence"), [])
            self.assertEqual(verify_file_bindings(workspace, [change["exact_diff_binding"]], label="exact diff"), [])

            round_input = base / "round.json"
            write_json(round_input, {
                "round": 1, "perspective": "requirements-scope-pain", "evidence_paths": [proof_rel],
                "candidate_comparison": {"candidate": candidate["candidate_id"]}, "decision": "KEEP",
                "actor_id": "optimizer", "residual_risk": [],
            })
            round_record = record_round(workspace, round_input)
            self.assertEqual(verify_file_bindings(workspace, round_record["evidence_bindings"], label="round evidence"), [])
            write_json(workspace / proof_rel, {"status": "TAMPERED"})
            self.assertTrue(verify_file_bindings(workspace, change["evidence_bindings"], label="change evidence"))
            self.assertTrue(verify_file_bindings(workspace, round_record["evidence_bindings"], label="round evidence"))


    def test_event_chain_detects_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            append_event(path, {"type": "A"})
            append_event(path, {"type": "B"})
            rows = path.read_text(encoding="utf-8").splitlines()
            row = json.loads(rows[0]); row["type"] = "X"; rows[0] = json.dumps(row)
            path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            self.assertTrue(verify_event_chain(path))

    def test_zero_budget_unused_is_not_exhausted_but_positive_use_is_violation(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"], {"max_cost": 0.0})
            workspace = base / "run"
            initial = loop_status(workspace)
            self.assertNotIn("BUDGET_EXHAUSTED:cost", initial["reasons"])
            result = update_counters(workspace, {"cost": 0.01})
            self.assertIn("ZERO_BUDGET_EXCEEDED:cost", result["reasons"])
            self.assertEqual(result["budget_status"], "VIOLATION")

    def test_state_tamper_blocks_counter_updates_and_loop_status(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"])
            workspace = base / "run"
            state_path = workspace / "state.json"
            state = load_json(state_path)
            state["counters"]["tokens"] = 999
            write_json(state_path, state)
            with self.assertRaisesRegex(ValueError, "run integrity"):
                update_counters(workspace, {"tokens": 1})
            result = loop_status(workspace)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("state counters differs" in item for item in result["reasons"]))

    def test_positive_budget_exact_limit_stops_without_violation(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"], {"max_network_requests": 2})
            result = update_counters(base / "run", {"network_requests": 2})
            self.assertIn("BUDGET_EXHAUSTED:network_requests", result["reasons"])
            self.assertEqual(result["budget_violations"], [])

    def test_budget_and_counter_types_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            with self.assertRaises(ValueError):
                self.init(base, ["incremental"], {"max_tokens": True})
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"])
            with self.assertRaises(ValueError):
                update_counters(base / "run", {"tokens": float("nan")})
            with self.assertRaises(ValueError):
                update_counters(base / "run", {"model_calls": 0.5})

    def test_budget_consumption_is_written_to_event_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"])
            update_counters(base / "run", {"tokens": 10})
            self.assertEqual(verify_event_chain(base / "run/events.jsonl"), [])
            last = json.loads((base / "run/events.jsonl").read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(last["type"], "BUDGET_CONSUMED")

    def test_change_rejects_tampered_rollback_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"])
            workspace = base / "run"
            candidate = run["target"]["candidates"][0]
            snapshot = Path(candidate["rollback_pointer"])
            # read-only is a policy aid, not a security boundary for the owner.
            (snapshot / "README.md").chmod(0o644)
            (snapshot / "README.md").write_text("tampered snapshot\n", encoding="utf-8")
            root = Path(candidate["path"])
            (root / "README.md").write_text("candidate change\n", encoding="utf-8")
            record = base / "change.json"
            write_json(record, {"hypothesis": "h", "evidence_paths": [self.proof(workspace, "rollback.json")], "actor_id": "a", "commands": ["edit"], "tools": ["editor"], "risk": [], "decision": "KEEP"})
            with self.assertRaisesRegex(ValueError, "rollback snapshot hash"):
                record_change(workspace, candidate["candidate_id"], record)


    def test_malformed_run_never_falls_back_to_or_scans_process_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "run"
            (workspace / "control/contracts").mkdir(parents=True)
            write_json(workspace / "run.json", {})
            write_json(workspace / "control/contracts/run-seal.json", {"schema_version": "1.0"})
            write_json(workspace / "control/contracts/control-plane-manifest.json", {"schema_version": "1.0"})
            with mock.patch("wbi_core.workspace._walk_control_plane_files", side_effect=AssertionError("untrusted path scan")):
                seal_errors = verify_run_seal(workspace, {})
                plane_errors = verify_control_plane(workspace, {})
            self.assertTrue(seal_errors)
            self.assertTrue(plane_errors)
            self.assertTrue(any("optimizer root" in item or "control-plane" in item for item in seal_errors + plane_errors))

    def test_mismatched_frozen_optimizer_root_is_rejected_before_tree_walk(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["incremental"])
            tampered = json.loads(json.dumps(run))
            tampered["control_plane"]["optimizer_root"] = str((base / "untrusted-root").resolve())
            with mock.patch("wbi_core.workspace._walk_control_plane_files", side_effect=AssertionError("untrusted path scan")):
                errors = verify_control_plane(base / "run", tampered)
            self.assertTrue(any("differs from frozen" in item for item in errors), errors)

    def test_run_seal_detects_budget_or_candidate_path_rewrite(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"])
            workspace = base / "run"
            run = load_json(workspace / "run.json")
            run["budget"]["max_tokens"] += 1
            write_json(workspace / "run.json", run)
            self.assertIn("immutable run contract", " ".join(verify_run_seal(workspace)))
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"])
            workspace = base / "run"
            run = load_json(workspace / "run.json")
            run["target"]["candidates"][0]["path"] = str(base / "escape")
            write_json(workspace / "run.json", run)
            errors = verify_run_seal(workspace)
            self.assertTrue(any("candidate path escaped" in item for item in errors), errors)

    def test_non_script_control_plane_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            optimizer = base / "optimizer"
            target = base / "target-skill"
            shutil.copytree(ROOT, optimizer, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            workspace = base / "run"
            init_run(target, workspace, optimizer, ["incremental"], self_evolve=False)
            self.assertEqual(verify_control_plane(workspace), [])
            (optimizer / "templates/premise-challenge.json").write_text("{}\n", encoding="utf-8")
            errors = verify_control_plane(workspace)
            self.assertTrue(any("control-plane" in item or "optimizer tree" in item for item in errors), errors)

    def test_recording_refuses_mutated_run_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            self.init(base, ["incremental"])
            workspace = base / "run"
            run = load_json(workspace / "run.json")
            run["release_profile"] = "rewritten-after-start"
            write_json(workspace / "run.json", run)
            record = base / "round.json"
            write_json(record, {"round": 1, "perspective": "p", "evidence_paths": [self.proof(workspace, "mutated-run.json")], "candidate_comparison": {"baseline": "equal", "candidate": "equal"}, "decision": "NO_CHANGE", "actor_id": "a", "residual_risk": []})
            with self.assertRaisesRegex(ValueError, "run integrity"):
                record_round(workspace, record)

    def test_strategy_namespace_is_open_but_portable(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            run = self.init(base, ["pareto-population", "coevolution-v2"])
            self.assertEqual([item["strategy"] for item in run["target"]["candidates"]], ["pareto-population", "coevolution-v2"])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                self.init(Path(temp), ["../escape"])

    def test_custom_release_profile_contract_is_frozen_into_run(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            target = base / "target-skill"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            contract = base / "profile.json"
            write_json(contract, {
                "schema_version": "1.0", "status": "FROZEN", "profile": "regulatory-evidence",
                "required_profile_evidence": ["audit-trail", "regulatory-mapping"],
                "rationale": "domain-specific release evidence",
            })
            run = init_run(
                target, base / "run", ROOT, ["pareto-population"], self_evolve=True,
                release_profile="regulatory-evidence", release_profile_contract_path=contract,
            )
            bound = run["release_profile_contract"]
            self.assertEqual(bound["profile"], "regulatory-evidence")
            self.assertTrue(Path(bound["path"]).is_file())
            self.assertEqual(verify_run_seal(base / "run"), [])
            profile_path = Path(bound["path"])
            profile_path.chmod(0o644)
            contract_data = load_json(profile_path)
            contract_data["rationale"] = "tampered"
            write_json(profile_path, contract_data)
            self.assertTrue(any("profile contract changed" in item for item in verify_run_seal(base / "run")))

    def test_custom_release_profile_without_contract_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            target = base / "target-skill"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            with self.assertRaisesRegex(ValueError, "custom release profile"):
                init_run(target, base / "run", ROOT, ["incremental"], release_profile="regulatory-evidence")


if __name__ == "__main__":
    unittest.main()
