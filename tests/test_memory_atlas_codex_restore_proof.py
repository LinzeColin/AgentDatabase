from __future__ import annotations

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TESTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from memory_atlas_cli.codex_public_raw_archive import (  # noqa: E402
    build_codex_public_raw_archive,
)
from memory_atlas_cli.codex_restore_proof import (  # noqa: E402
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    EXPECTED_PHASE_BOUNDARY,
    CodexRestoreProofError,
    build_codex_restore_proof,
    load_codex_restore_proof_contract,
    load_codex_restore_proof_model_parameters,
    run_codex_restore_proof,
    validate_codex_restore_proof_contract,
    validate_codex_restore_proof_model_parameters,
)
from test_memory_atlas_codex_public_raw_archive import (  # noqa: E402
    make_codex_fixture,
    make_database_fixture,
    tree_evidence,
)


def make_restore_fixture(parent: Path) -> tuple[Path, str]:
    database = make_database_fixture(parent)
    model_dir = database / "机器治理/参数与公式"
    model_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "codex_derived.v1_2_1_s07_p2_t1.json",
        "codex_restore_proof.v1_2_1_s07_p3_t3.json",
    ):
        shutil.copy2(ROOT / "机器治理/参数与公式" / name, model_dir / name)
    shutil.copy2(
        ROOT / "config/data_sources/codex_restore_proof.json",
        database / "config/data_sources/codex_restore_proof.json",
    )
    codex_home = make_codex_fixture(parent)
    old_timestamp = time.time() - 600
    for path in codex_home.rglob("*"):
        if path.is_file():
            os.utime(path, (old_timestamp, old_timestamp))
    source_before = tree_evidence(codex_home)
    archive_id = "restore-proof-baseline"
    build_codex_public_raw_archive(
        database,
        archive_id,
        operator_codex_home=codex_home,
        environ={},
    )
    if tree_evidence(codex_home) != source_before:
        raise AssertionError("fixture builder mutated Codex input")
    return database, archive_id


class CodexRestoreProofTests(unittest.TestCase):
    def test_contract_and_model_freeze_two_empty_runs_and_s07_boundary(self) -> None:
        contract = load_codex_restore_proof_contract(ROOT)
        model = load_codex_restore_proof_model_parameters(ROOT)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["task_id"], "S07-P3-T3")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S07-P3-T3")
        self.assertEqual(contract["phase_boundary"], EXPECTED_PHASE_BOUNDARY)
        self.assertEqual(model["parameters"]["independent_rehearsal_count"], 2)
        self.assertEqual(
            model["formula"],
            "pass = archive_verified AND empty_start[1..2] AND restore_verified[1..2] AND derived_rebuilt[1..2] AND provenance_coverage=1 AND output_hashes_run_1=output_hashes_run_2 AND replay_no_changes[1..2] AND source_unchanged AND no_live_or_remote_dependency",
        )

        mutated_contract = copy.deepcopy(contract)
        mutated_contract["isolation"]["user_codex_home_allowed"] = True
        with self.assertRaises(CodexRestoreProofError):
            validate_codex_restore_proof_contract(mutated_contract)

        mutated_model = copy.deepcopy(model)
        mutated_model["parameters"]["independent_rehearsal_count"] = 1
        with self.assertRaises(CodexRestoreProofError):
            validate_codex_restore_proof_model_parameters(mutated_model)

    def test_workspace_must_be_absolute_empty_and_not_a_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir).resolve()
            database, archive_id = make_restore_fixture(parent)
            non_empty = parent / "non-empty"
            non_empty.mkdir()
            marker = non_empty / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")

            with self.assertRaisesRegex(
                CodexRestoreProofError, "restore_proof_workspace_not_empty"
            ):
                build_codex_restore_proof(database, archive_id, non_empty)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

            symlink = parent / "workspace-link"
            target = parent / "workspace-target"
            target.mkdir()
            symlink.symlink_to(target, target_is_directory=True)
            with self.assertRaisesRegex(
                CodexRestoreProofError, "restore_proof_workspace_unsafe"
            ):
                build_codex_restore_proof(database, archive_id, symlink)

            with self.assertRaisesRegex(
                CodexRestoreProofError, "restore_proof_workspace_not_absolute"
            ):
                build_codex_restore_proof(database, archive_id, Path("relative-proof"))

    def test_real_fixture_restores_and_rebuilds_twice_without_live_codex_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir).resolve()
            database, archive_id = make_restore_fixture(parent)
            workspace = parent / "proof-workspace"
            workspace.mkdir()
            forbidden_home = parent / "forbidden-user-home"
            forbidden_home.mkdir()
            (forbidden_home / ".codex").mkdir()
            (forbidden_home / ".codex/marker.txt").write_text(
                "must-not-be-read\n", encoding="utf-8"
            )
            raw_before = tree_evidence(database / "data/raw_archives/codex" / archive_id)

            with mock.patch.dict(
                os.environ,
                {
                    "HOME": str(forbidden_home),
                    "CODEX_HOME": str(forbidden_home / ".codex"),
                },
                clear=False,
            ):
                proof = build_codex_restore_proof(database, archive_id, workspace)

            self.assertEqual(proof["status"], "PASS")
            self.assertEqual(proof["task_id"], "S07-P3-T3")
            self.assertEqual(proof["archive"]["archive_id"], archive_id)
            self.assertEqual(proof["archive"]["kind"], "baseline")
            self.assertEqual(proof["rehearsal_count"], 2)
            self.assertEqual(len(proof["rehearsals"]), 2)
            self.assertTrue(proof["determinism"]["output_hashes_equal"])
            self.assertTrue(proof["determinism"]["proof_runs_equal"])
            self.assertEqual(proof["provenance"]["coverage_ratio"], 1)
            self.assertEqual(
                proof["provenance"]["verified_event_count"],
                proof["derived"]["event_count"],
            )
            self.assertGreater(proof["derived"]["event_count"], 0)
            self.assertTrue(all(run["empty_start"] for run in proof["rehearsals"]))
            self.assertTrue(all(run["restore_verified"] for run in proof["rehearsals"]))
            self.assertTrue(all(run["replay_outcome"] == "NO_CHANGES" for run in proof["rehearsals"]))
            self.assertEqual(proof["isolation"]["user_codex_home_read"], False)
            self.assertEqual(proof["isolation"]["network_required"], False)
            self.assertEqual(proof["effects"]["raw_mutation"], False)
            self.assertEqual(proof["effects"]["remote_push"], False)
            self.assertEqual(proof["effects"]["deployment"], False)
            self.assertEqual(tree_evidence(database / "data/raw_archives/codex" / archive_id), raw_before)
            self.assertEqual(list(workspace.iterdir()), [])

            serialized = json.dumps(proof, ensure_ascii=False, sort_keys=True)
            self.assertNotIn(str(parent), serialized)
            self.assertNotIn("must-not-be-read", serialized)

    def test_cli_failure_is_structured_and_preserves_non_empty_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir).resolve()
            database, archive_id = make_restore_fixture(parent)
            workspace = parent / "non-empty-cli-workspace"
            workspace.mkdir()
            marker = workspace / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")
            output = parent / "must-not-exist.json"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = run_codex_restore_proof(
                    Namespace(
                        database_dir=database,
                        archive_id=archive_id,
                        workspace_root=workspace,
                        output=output,
                    )
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 2)
            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(
                payload["error_code"], "restore_proof_workspace_not_empty"
            )
            self.assertFalse(output.exists())
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")


if __name__ == "__main__":
    unittest.main()
