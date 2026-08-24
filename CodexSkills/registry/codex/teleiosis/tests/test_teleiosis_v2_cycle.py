from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from wbi_cycle.core import (  # noqa: E402
    CycleError,
    SEQUENCE,
    commit_mutation,
    initialize_workspace,
    record_subrun,
    tree_sha256,
    validate_workspace,
)


def sha(label: str) -> str:
    import hashlib
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class CycleContractTests(unittest.TestCase):
    def _artifact(self, root: Path, index: int) -> Path:
        path = root / f"candidate-{index}"
        path.mkdir()
        (path / "SKILL.md").write_text(f"candidate {index}\n", encoding="utf-8")
        return path

    def test_exact_five_stage_three_subrun_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initial = self._artifact(root, 0)
            workspace = root / "run"
            current = tree_sha256(initial)
            initialize_workspace(workspace, "subject", "v1", current)
            for index, (stage, _profile) in enumerate(SEQUENCE, 1):
                staged = self._artifact(root, index)
                approved = tree_sha256(staged)
                for round_number in (1, 2, 3):
                    record_subrun(
                        workspace,
                        stage,
                        round_number,
                        current,
                        sha(f"{stage}-{round_number}"),
                        "NO_CHANGE" if round_number < 3 else "KEEP",
                        staged_candidate_digest=approved if round_number == 3 else None,
                    )
                result = commit_mutation(workspace, stage, staged)
                current = result["committed_digest"]
            report = validate_workspace(workspace, require_complete=True)
            self.assertTrue(report["valid"], report)
            self.assertTrue(report["complete"])
            self.assertEqual(report["subruns"], 15)
            self.assertEqual(report["mutations"], 5)
            self.assertEqual(report["final_subject_digest"], current)

    def test_skip_or_interleave_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = self._artifact(root, 0)
            workspace = root / "run"
            digest = tree_sha256(artifact)
            initialize_workspace(workspace, "subject", "v1", digest)
            with self.assertRaises(CycleError):
                record_subrun(workspace, "M1", 1, digest, sha("x"), "NO_CHANGE")
            record_subrun(workspace, "T1", 1, digest, sha("t1"), "NO_CHANGE")
            with self.assertRaises(CycleError):
                record_subrun(workspace, "T1", 3, digest, sha("t3"), "KEEP", staged_candidate_digest=sha("candidate"))

    def test_mutation_after_approval_cannot_change_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initial = self._artifact(root, 0)
            staged = self._artifact(root, 1)
            workspace = root / "run"
            current = tree_sha256(initial)
            approved = tree_sha256(staged)
            initialize_workspace(workspace, "subject", "v1", current)
            for round_number in (1, 2, 3):
                record_subrun(
                    workspace,
                    "T1",
                    round_number,
                    current,
                    sha(f"r{round_number}"),
                    "KEEP",
                    staged_candidate_digest=approved if round_number == 3 else None,
                )
            (staged / "SKILL.md").write_text("changed after approval\n", encoding="utf-8")
            with self.assertRaises(CycleError):
                commit_mutation(workspace, "T1", staged)

    def test_event_hash_chain_detects_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = self._artifact(root, 0)
            workspace = root / "run"
            digest = tree_sha256(artifact)
            initialize_workspace(workspace, "subject", "v1", digest)
            record_subrun(workspace, "T1", 1, digest, sha("evidence"), "NO_CHANGE")
            events = workspace / "events.jsonl"
            row = json.loads(events.read_text(encoding="utf-8").strip())
            row["outcome"] = "KEEP"
            events.write_text(json.dumps(row) + "\n", encoding="utf-8")
            report = validate_workspace(workspace)
            self.assertFalse(report["valid"])
            self.assertTrue(any("篡改" in item for item in report["errors"]))

    def test_third_round_requires_staged_digest_and_then_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = self._artifact(root, 0)
            workspace = root / "run"
            digest = tree_sha256(artifact)
            initialize_workspace(workspace, "subject", "v1", digest)
            record_subrun(workspace, "T1", 1, digest, sha("1"), "NO_CHANGE")
            record_subrun(workspace, "T1", 2, digest, sha("2"), "NO_CHANGE")
            with self.assertRaises(CycleError):
                record_subrun(workspace, "T1", 3, digest, sha("3"), "KEEP")
            staged_digest = sha("staged")
            record_subrun(workspace, "T1", 3, digest, sha("3"), "KEEP", staged_candidate_digest=staged_digest)
            with self.assertRaises(CycleError):
                record_subrun(workspace, "M1", 1, digest, sha("4"), "NO_CHANGE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
