from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wbi_run.core import (  # noqa: E402
    PUBLIC_ALLOWED,
    RunError,
    build_contract,
    init_run,
    load_json,
    record_stage,
    validate_run,
)


def write_complete_capability(path: Path, module: str, stage: int, **extra_top: object) -> Path:
    manifest = load_json(ROOT / "modules" / {"T": "raw_teleiosis", "S": "skill_market_lab", "P": "product_reality_lab"}[module] / "CAPABILITIES.json")
    doc = {
        "schema_version": "teleiosis.capability_results.v1",
        "module": module,
        "global_stage": stage,
        "results": [
            {
                "id": row["id"],
                "status": "EXECUTED",
                "reason": "",
                "evidence_refs": [f"fixture://{stage}/{row['id']}"],
            }
            for row in manifest["capabilities"]
        ],
    }
    doc.update(extra_top)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def make_subject(base: Path, text: str = "baseline\n") -> Path:
    subject = base / "subject"
    subject.mkdir()
    (subject / "value.txt").write_text(text, encoding="utf-8")
    return subject


class PokaYokeRunTests(unittest.TestCase):
    def test_subject_and_workspace_must_be_disjoint_before_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-disjoint-") as td:
            base = Path(td)
            subject = make_subject(base)
            workspace = subject / "run"
            with self.assertRaisesRegex(RunError, "不能互相嵌套"):
                init_run(subject, workspace)
            self.assertFalse(workspace.exists())

    def test_symlink_subject_content_is_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory(prefix="teleiosis-symlink-") as td:
            base = Path(td)
            subject = make_subject(base)
            outside = base / "outside.txt"
            outside.write_text("outside", encoding="utf-8")
            os.symlink(outside, subject / "link.txt")
            with self.assertRaisesRegex(RunError, "符号链接"):
                init_run(subject, base / "workspace")
            self.assertFalse((base / "workspace").exists())

    def test_unknown_capability_field_fails_without_state_advance(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-unknown-field-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            cap = write_complete_capability(workspace / "cap.json", "T", 1, surprise="junk")
            before = load_json(workspace / "RUN_STATE.json")
            with self.assertRaisesRegex(RunError, "未声明字段"):
                record_stage(workspace, "T", "AUTO", cap)
            after = load_json(workspace / "RUN_STATE.json")
            self.assertEqual(before["next_stage_index"], after["next_stage_index"])
            self.assertEqual(before["revisions"], after["revisions"])
            self.assertFalse((workspace / ".teleiosis" / "evidence" / "C001").exists())

    def test_sensitive_input_is_rejected_without_echoing_secret(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-secret-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            secret = "github_" + "pat_" + "123456789012345678901234567890"
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            doc = load_json(cap)
            doc["results"][0]["evidence_refs"] = [secret]
            cap.write_text(json.dumps(doc), encoding="utf-8")
            try:
                record_stage(workspace, "T", "AUTO", cap)
            except RunError as exc:
                message = str(exc)
            else:
                self.fail("secret should be rejected")
            self.assertNotIn(secret, message)
            self.assertIn("凭证", message)
            self.assertEqual(load_json(workspace / "RUN_STATE.json")["next_stage_index"], 0)

    def test_no_change_with_real_delta_blocks_and_preserves_candidate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-nochange-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            candidate = workspace / "candidate" / "value.txt"
            candidate.write_text("changed\n", encoding="utf-8")
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            with self.assertRaisesRegex(RunError, "NO_CHANGE.*实际变化"):
                record_stage(workspace, "T", "AUTO", cap, decision="NO_CHANGE")
            self.assertEqual(candidate.read_text(encoding="utf-8"), "changed\n")
            self.assertEqual(load_json(workspace / "RUN_STATE.json")["next_stage_index"], 0)

    def test_keep_without_delta_normalizes_to_no_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-normalize-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            result = record_stage(workspace, "T", "AUTO", cap, decision="KEEP")
            revision = result["revision"]
            self.assertEqual(revision["decision"], "NO_CHANGE")
            self.assertEqual(revision["decision_normalized_from"], "KEEP")
            self.assertFalse(any(revision["changed_files"].values()))

    def test_revert_restores_parent_and_keeps_rejected_archive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-revert-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            candidate = workspace / "candidate" / "value.txt"
            candidate.write_text("rejected\n", encoding="utf-8")
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            result = record_stage(workspace, "T", "AUTO", cap, decision="REVERT")
            self.assertEqual(candidate.read_text(encoding="utf-8"), "baseline\n")
            archive = workspace / result["revision"]["rejected_candidate_archive"]
            self.assertTrue(archive.is_file())
            self.assertGreater(archive.stat().st_size, 0)
            self.assertEqual(result["revision"]["decision"], "REVERT")

    def test_failed_evidence_copy_is_transactional(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-transaction-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace, limits={"evidence_max_bytes": 8})
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            evidence = workspace / "evidence.txt"
            evidence.write_text("this is too large", encoding="utf-8")
            before = load_json(workspace / "RUN_STATE.json")
            with self.assertRaisesRegex(RunError, "容量上限"):
                record_stage(workspace, "T", "AUTO", cap, evidence=evidence, decision="KEEP")
            after = load_json(workspace / "RUN_STATE.json")
            self.assertEqual(before["next_stage_index"], after["next_stage_index"])
            self.assertEqual(before["revisions"], after["revisions"])
            self.assertFalse(any((workspace / ".teleiosis" / "transactions").iterdir()))

    def test_candidate_capacity_limit_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-capacity-") as td:
            base = Path(td)
            subject = make_subject(base, "1234567890")
            with self.assertRaisesRegex(RunError, "单文件超过上限|总容量超过上限"):
                init_run(subject, base / "workspace", limits={
                    "candidate_max_files": 10,
                    "candidate_max_total_bytes": 4,
                    "candidate_max_single_file_bytes": 4,
                })
            self.assertFalse((base / "workspace").exists())

    def test_wrong_global_stage_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-stage-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            cap = write_complete_capability(workspace / "cap.json", "T", 99)
            with self.assertRaisesRegex(RunError, "global_stage"):
                record_stage(workspace, "T", "AUTO", cap)
            self.assertEqual(load_json(workspace / "RUN_STATE.json")["next_stage_index"], 0)

    def test_external_evidence_is_copied_and_source_path_not_persisted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-evidence-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            evidence = base / "outside-evidence.txt"
            evidence.write_text("auditable evidence\n", encoding="utf-8")
            result = record_stage(workspace, "T", "AUTO", cap, evidence=evidence)
            revision = result["revision"]
            self.assertTrue((workspace / revision["evidence_path"]).is_file())
            state_text = (workspace / "RUN_STATE.json").read_text(encoding="utf-8")
            self.assertNotIn(str(evidence), state_text)
            self.assertTrue(evidence.is_file())

    def test_tampered_evidence_is_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-tamper-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            cap = write_complete_capability(workspace / "cap.json", "T", 1)
            evidence = base / "evidence.txt"
            evidence.write_text("original", encoding="utf-8")
            result = record_stage(workspace, "T", "AUTO", cap, evidence=evidence)
            copied = workspace / result["revision"]["evidence_path"]
            copied.write_text("tampered", encoding="utf-8")
            verified = validate_run(workspace)
            self.assertEqual(verified["status"], "FAIL")
            self.assertTrue(any("evidence mismatch" in error for error in verified["errors"]))

    def test_workspace_root_is_strict_allowlist(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-clean-root-") as td:
            base = Path(td)
            workspace = base / "workspace"
            init_run(make_subject(base), workspace)
            self.assertTrue(set(path.name for path in workspace.iterdir()) <= PUBLIC_ALLOWED)
            (workspace / "debug.log").write_text("junk", encoding="utf-8")
            result = validate_run(workspace)
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("debug.log", " ".join(result["errors"]))

    def test_cli_error_is_exactly_one_clean_json_document(self) -> None:
        script = ROOT / "scripts" / "teleiosis_run.py"
        secret = "github_" + "pat_" + "123456789012345678901234567890"
        cp = subprocess.run(
            [sys.executable, str(script), "next", "--workspace", secret],
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(cp.returncode, 2)
        self.assertEqual(cp.stderr, "")
        doc = json.loads(cp.stdout)
        self.assertEqual(doc["status"], "BLOCKED")
        self.assertNotIn(secret, cp.stdout)
        self.assertNotIn("Traceback", cp.stdout)
        self.assertNotIn("usage:", cp.stdout.lower())

    def test_simulation_contract_is_stable(self) -> None:
        contract = build_contract()
        self.assertEqual(contract["round_sequence"], ["T", "C", "S", "C", "P", "C"])
        self.assertEqual(contract["module_stages"], 27)
        self.assertEqual(contract["candidate_revisions"], 27)
        self.assertEqual(contract["execution_mode"], "FULL_NO_ROUTING")
        self.assertFalse(contract["fixed_sha_precondition"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
