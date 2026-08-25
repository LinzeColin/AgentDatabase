from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import complete_run, load_state, make_subject, stage_result, write_json
from teleiosis_core.common import TeleiosisError, tree_digest
from teleiosis_core.workflow import (
    TOTAL_STAGES,
    build_sequence,
    contract,
    create_handoff,
    init_run,
    status_run,
    submit_stage,
    validate_run,
)


class WorkflowTests(unittest.TestCase):
    def test_contract_has_36_stages(self) -> None:
        result = contract()
        self.assertEqual(result["total_stages"], 36)
        self.assertEqual(result["modules"], ["T", "S", "P", "A"])

    def test_sequence_exact_order(self) -> None:
        sequence = build_sequence()
        self.assertEqual([item["module"] for item in sequence[:8]], ["T", "S", "P", "A", "T", "S", "P", "A"])
        self.assertEqual(sequence[-1]["candidate_checkpoint"], "C0036")

    def test_init_clean_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            subject = make_subject(base / "subject")
            workspace = base / "run"
            result = init_run(subject, workspace, "RUN-TEST-INIT")
            self.assertEqual(result["status"], "INITIALIZED")
            self.assertEqual({p.name for p in workspace.iterdir()}, {"candidate", ".teleiosis", "RUN_STATE.json", "RUN_STATUS.json", "SUMMARY.md", "NEXT_STAGE.json", "RESULT.json"})

    def test_no_change_advances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-NOCHANGE")
            state = load_state(workspace)
            result_path = workspace / "NEXT_STAGE.json"
            write_json(result_path, stage_result(workspace, state))
            result = submit_stage(workspace, result_path)
            self.assertEqual(result["decision"], "NO_CHANGE")
            self.assertEqual(load_state(workspace)["next_stage_index"], 1)

    def test_keep_without_delta_normalizes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-KEEP-NODELTA")
            state = load_state(workspace)
            result = stage_result(workspace, state, decision="KEEP")
            path = workspace / "NEXT_STAGE.json"
            write_json(path, result)
            output = submit_stage(workspace, path)
            self.assertEqual(output["decision"], "NO_CHANGE")

    def test_keep_delta_creates_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-KEEP-DELTA")
            (workspace / "candidate/payload.txt").write_text("changed\n", encoding="utf-8")
            state = load_state(workspace)
            path = workspace / "NEXT_STAGE.json"
            write_json(path, stage_result(workspace, state, decision="KEEP"))
            output = submit_stage(workspace, path)
            self.assertEqual(output["decision"], "KEEP")
            self.assertTrue((workspace / ".teleiosis/snapshots/C0001/payload.txt").is_file())

    def test_no_change_with_delta_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-CONFLICT")
            (workspace / "candidate/payload.txt").write_text("changed\n", encoding="utf-8")
            state = load_state(workspace)
            path = workspace / "NEXT_STAGE.json"
            write_json(path, stage_result(workspace, state, decision="NO_CHANGE"))
            with self.assertRaises(TeleiosisError) as ctx:
                submit_stage(workspace, path)
            self.assertEqual(ctx.exception.code, "NO_CHANGE_DELTA_CONFLICT")

    def test_revert_restores_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            subject = make_subject(base / "subject", "original\n")
            init_run(subject, workspace, "RUN-REVERT")
            (workspace / "candidate/payload.txt").write_text("bad\n", encoding="utf-8")
            state = load_state(workspace)
            path = workspace / "NEXT_STAGE.json"
            write_json(path, stage_result(workspace, state, decision="REVERT"))
            submit_stage(workspace, path)
            self.assertEqual((workspace / "candidate/payload.txt").read_text(encoding="utf-8"), "original\n")
            self.assertTrue((workspace / ".teleiosis/rejected/C0001/payload.txt").is_file())

    def test_executed_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-EVIDENCE")
            state = load_state(workspace)
            result = stage_result(workspace, state, status="EXECUTED")
            path = workspace / "NEXT_STAGE.json"
            write_json(path, result)
            with self.assertRaises(TeleiosisError) as ctx:
                submit_stage(workspace, path)
            self.assertEqual(ctx.exception.code, "EXECUTED_WITHOUT_EVIDENCE")

    def test_executed_evidence_is_captured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-CAPTURE")
            evidence = base / "evidence.json"
            evidence.write_text('{"ok":true}\n', encoding="utf-8")
            state = load_state(workspace)
            result = stage_result(workspace, state, status="EXECUTED", evidence_path=evidence)
            path = workspace / "NEXT_STAGE.json"
            write_json(path, result)
            submit_stage(workspace, path)
            captured = list((workspace / ".teleiosis/evidence/stage-00").iterdir())
            self.assertEqual(len(captured), 1)

    def test_blocked_capability_blocks_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-BLOCKED")
            state = load_state(workspace)
            result = stage_result(workspace, state, status="BLOCKED", decision="BLOCKED")
            path = workspace / "NEXT_STAGE.json"
            write_json(path, result)
            output = submit_stage(workspace, path)
            self.assertEqual(output["status"], "BLOCKED")
            self.assertEqual(load_state(workspace)["next_stage_index"], 0)

    def test_wrong_module_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-WRONG-MODULE")
            state = load_state(workspace)
            result = stage_result(workspace, state)
            result["module"] = "A"
            path = workspace / "NEXT_STAGE.json"
            write_json(path, result)
            with self.assertRaises(TeleiosisError) as ctx:
                submit_stage(workspace, path)
            self.assertEqual(ctx.exception.code, "RESULT_IDENTITY")

    def test_unknown_result_field_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-UNKNOWN")
            state = load_state(workspace)
            result = stage_result(workspace, state)
            result["surprise"] = True
            path = workspace / "NEXT_STAGE.json"
            write_json(path, result)
            with self.assertRaises(TeleiosisError) as ctx:
                submit_stage(workspace, path)
            self.assertEqual(ctx.exception.code, "RESULT_UNKNOWN_FIELDS")

    def test_full_run_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-FULL")
            complete_run(workspace, submit_stage)
            result = validate_run(workspace, require_complete=True)
            self.assertTrue(result["complete"])
            handoff = base / "handoff.json"
            created = create_handoff(workspace, handoff)
            self.assertEqual(created["status"], "HANDOFF_READY")
            packet = json.loads(handoff.read_text(encoding="utf-8"))
            self.assertFalse(packet["builder_self_assessment_accepted"])
            self.assertEqual(packet["formal_decision_requested"], "FORMAL_PASS_OR_FAIL")

    def test_hash_chain_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-HASH")
            state = load_state(workspace)
            path = workspace / "NEXT_STAGE.json"
            write_json(path, stage_result(workspace, state))
            submit_stage(workspace, path)
            state = load_state(workspace)
            state["events"][0]["candidate_hash"] = "f" * 64
            write_json(workspace / "RUN_STATE.json", state)
            with self.assertRaises(TeleiosisError) as ctx:
                validate_run(workspace)
            self.assertEqual(ctx.exception.code, "RUN_VALIDATION_FAILED")

    def test_status_never_issues_formal_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-STATUS")
            status = status_run(workspace)
            self.assertEqual(status["formal_pass"], "NOT_ISSUED_INTERNALLY")


if __name__ == "__main__":
    unittest.main()
