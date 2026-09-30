from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[3]
AUDITOR = SKILL_ROOT / "scripts/audit_stage2_readiness.py"
CONTRACT = SKILL_ROOT / "references/stage2-readiness-contract.json"
AUDIT_SPEC = importlib.util.spec_from_file_location(
    "stage2_readiness_auditor_under_test",
    AUDITOR,
)
assert AUDIT_SPEC and AUDIT_SPEC.loader
audit_module = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(audit_module)
DiskUsage = namedtuple("DiskUsage", "total used free")


class Stage2ReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "candidate"
        self.repo.mkdir()
        (self.repo / ".git").write_text("gitdir: synthetic\n", encoding="utf-8")
        self.scratch = self.root / "private-scratch-parent"
        self.scratch.mkdir()
        self.evidence_path = self.root / "github-evidence.json"
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        releases: dict[str, dict] = {}
        for selected in self.contract["source_contract"]["selected_assets"]:
            release = releases.setdefault(
                selected["release_tag"],
                {
                    "tag_name": selected["release_tag"],
                    "draft": False,
                    "prerelease": False,
                    "assets": [],
                },
            )
            release["assets"].append(
                {
                    "id": selected["asset_id"],
                    "name": selected["asset_name"],
                    "size": selected["size_bytes"],
                    "state": "uploaded",
                    "digest": "sha256:" + selected["sha256"],
                }
            )
        self.evidence = {
            "schema_version": "dynamic_profile.stage2_github_evidence.v1",
            "observed_at": "2026-07-24T02:47:00Z",
            "repository": {
                "full_name": "LinzeColin/Private-Database",
                "visibility": "PRIVATE",
                "private": True,
                "archived": False,
            },
            "repository_privacy": {
                "public_raw_audit": {
                    "status": "PASS",
                    "credential_or_private_text_file_count": 0,
                    "unmarked_binary_file_count": 0,
                    "invalid_binary_marker_file_count": 0,
                    "invalid_json_file_count": 0,
                    "oversize_file_count": 0,
                },
                "high_risk_scan": {
                    "status": "PASS",
                    "high_risk_secret_hit_count": 0,
                    "tracked_raw_private_file_count": 0,
                },
            },
            "releases": list(releases.values()),
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_audit(
        self,
        evidence: dict | None = None,
        *,
        free_bytes: int = 500_000_000_000,
        scratch: Path | None = None,
    ) -> tuple[int, dict]:
        self.evidence_path.write_text(
            json.dumps(evidence if evidence is not None else self.evidence),
            encoding="utf-8",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(
                audit_module.shutil,
                "disk_usage",
                return_value=DiskUsage(600_000_000_000, 100_000_000_000, free_bytes),
            ),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            returncode = audit_module.main(
                [
                    "--evidence",
                    str(self.evidence_path),
                    "--repo-root",
                    str(self.repo),
                    "--scratch-root",
                    str(scratch or self.scratch),
                    "--contract",
                    str(CONTRACT),
                ]
            )
        payload = stdout.getvalue() or stderr.getvalue()
        return returncode, json.loads(payload)

    def test_exact_metadata_and_capacity_are_ready_without_raw_access(self) -> None:
        returncode, report = self.run_audit()
        self.assertEqual(returncode, 0, report)
        self.assertEqual(report["status"], "READY")
        self.assertEqual(
            {name: gate["status"] for name, gate in report["gates"].items()},
            {"source": "PASS", "privacy": "PASS", "capacity": "PASS"},
        )
        self.assertEqual(report["selected_asset_count"], 4)
        self.assertEqual(report["selected_source_bytes"], 3276149855)
        self.assertFalse(report["raw_content_read"])
        self.assertFalse(report["network_used"])
        self.assertFalse(report["persistent_output_written"])
        self.assertTrue(report["raw_baseline_authorized_by_evidence"])

    def test_remote_identity_drift_fails_closed(self) -> None:
        cases: list[tuple[str, dict]] = []

        stale_repo = copy.deepcopy(self.evidence)
        stale_repo["repository"]["full_name"] = "LinzeColin/AgentDatabase-Private"
        cases.append(("repository", stale_repo))

        draft = copy.deepcopy(self.evidence)
        draft["releases"][0]["draft"] = True
        cases.append(("draft", draft))

        missing = copy.deepcopy(self.evidence)
        missing["releases"][0]["assets"].pop()
        cases.append(("missing", missing))

        digest = copy.deepcopy(self.evidence)
        digest["releases"][0]["assets"][0]["digest"] = "sha256:" + ("0" * 64)
        cases.append(("digest", digest))

        duplicate_asset = copy.deepcopy(self.evidence)
        duplicate_asset["releases"][0]["assets"].append(
            copy.deepcopy(duplicate_asset["releases"][0]["assets"][0])
        )
        cases.append(("duplicate_asset", duplicate_asset))

        impossible_timestamp = copy.deepcopy(self.evidence)
        impossible_timestamp["observed_at"] = "2026-99-99T25:61:61Z"
        cases.append(("impossible_timestamp", impossible_timestamp))

        for label, evidence in cases:
            with self.subTest(label=label):
                returncode, report = self.run_audit(evidence)
                self.assertEqual(returncode, 2)
                self.assertEqual(report["status"], "NOT_READY")
                self.assertEqual(report["gates"]["source"]["status"], "FAIL")
                self.assertFalse(report["raw_baseline_authorized_by_evidence"])
                self.assertFalse(report["raw_content_read"])

    def test_insufficient_or_repository_local_scratch_fails_closed(self) -> None:
        returncode, report = self.run_audit(free_bytes=8699783357)
        self.assertEqual(returncode, 2)
        self.assertIn(
            "SCRATCH_CAPACITY_INSUFFICIENT",
            report["gates"]["capacity"]["errors"],
        )

        inside = self.repo / "scratch"
        inside.mkdir()
        returncode, report = self.run_audit(scratch=inside)
        self.assertEqual(returncode, 2)
        self.assertIn(
            "SCRATCH_ROOT_INSIDE_REPOSITORY",
            report["gates"]["capacity"]["errors"],
        )

    def test_repository_privacy_baseline_findings_fail_closed(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["repository_privacy"]["public_raw_audit"].update(
            {
                "status": "FAIL",
                "credential_or_private_text_file_count": 449,
            }
        )
        evidence["repository_privacy"]["high_risk_scan"].update(
            {
                "status": "FAIL",
                "high_risk_secret_hit_count": 3,
            }
        )

        returncode, report = self.run_audit(evidence)

        self.assertEqual(returncode, 2)
        self.assertEqual(report["status"], "NOT_READY")
        self.assertEqual(report["gates"]["source"]["status"], "PASS")
        self.assertEqual(report["gates"]["capacity"]["status"], "PASS")
        self.assertEqual(report["gates"]["privacy"]["status"], "FAIL")
        self.assertEqual(
            report["gates"]["privacy"]["errors"],
            [
                "HIGH_RISK_SCAN_NOT_PASS",
                "HIGH_RISK_SECRET_FINDINGS",
                "PUBLIC_RAW_AUDIT_NOT_PASS",
                "PUBLIC_RAW_PRIVATE_TEXT_FINDINGS",
            ],
        )
        self.assertFalse(report["raw_baseline_authorized_by_evidence"])

    def test_duplicate_json_keys_are_rejected_without_upgrading_readiness(self) -> None:
        self.evidence_path.write_text(
            '{"schema_version":"dynamic_profile.stage2_github_evidence.v1",'
            '"schema_version":"dynamic_profile.stage2_github_evidence.v1"}',
            encoding="utf-8",
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            returncode = audit_module.main(
                [
                    "--evidence",
                    str(self.evidence_path),
                    "--repo-root",
                    str(self.repo),
                    "--scratch-root",
                    str(self.scratch),
                    "--contract",
                    str(CONTRACT),
                ]
            )
        report = json.loads(stderr.getvalue())
        self.assertEqual(returncode, 2)
        self.assertEqual(report["status"], "ERROR")
        self.assertFalse(report["raw_baseline_authorized_by_evidence"])
        self.assertFalse(report["raw_content_read"])

    def test_audit_does_not_create_or_modify_files(self) -> None:
        self.evidence_path.write_text(
            json.dumps(self.evidence),
            encoding="utf-8",
        )
        before = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        returncode, report = self.run_audit()
        after = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(returncode, 0, report)
        self.assertEqual(before, after)

    def test_contract_has_exact_scope_and_excludes_repository_bundle(self) -> None:
        selected = self.contract["source_contract"]["selected_assets"]
        self.assertEqual(len(selected), 4)
        self.assertEqual(
            sum(asset["size_bytes"] for asset in selected),
            self.contract["source_contract"]["selected_source_bytes"],
        )
        self.assertEqual(
            self.contract["capacity_contract"]["required_scratch_bytes"],
            2 * self.contract["source_contract"]["selected_source_bytes"]
            + 2 * 1024**3,
        )
        selected_names = {asset["asset_name"] for asset in selected}
        self.assertNotIn(
            "codexproject_remote_non_main_branches_20260708.bundle",
            selected_names,
        )
        self.assertEqual(
            self.contract["runtime_boundary"]["persistent_profile_outputs"],
            ["OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md"],
        )
        self.assertFalse(self.contract["runtime_boundary"]["raw_content_enabled"])
        self.assertTrue(
            self.contract["privacy_contract"][
                "raw_baseline_requires_fresh_readiness_pass"
            ]
        )
        self.assertTrue(
            self.contract["capacity_contract"]["recheck_before_raw_baseline"]
        )
        self.assertNotIn(
            "phase2b_requires_fresh_readiness_pass",
            self.contract["privacy_contract"],
        )

    def test_active_private_storage_pointers_are_coherent(self) -> None:
        raw_policy = json.loads(
            (
                REPO_ROOT
                / "OpenAIDatabase/config/storage/raw_material_policy.json"
            ).read_text(encoding="utf-8")
        )
        lifecycle = json.loads(
            (
                REPO_ROOT
                / "OpenAIDatabase/config/storage/directory_lifecycle.json"
            ).read_text(encoding="utf-8")
        )
        expected = self.contract["source_contract"]["repository"]["full_name"]
        self.assertEqual(raw_policy["private_origin_policy"]["repository"], expected)
        external = lifecycle["external_destinations"]
        self.assertEqual(len(external), 1)
        self.assertIn(expected, external[0]["requirement"])
        for path in (
            REPO_ROOT / "OpenAIDatabase/AGENTS.md",
            REPO_ROOT / "OpenAIDatabase/README.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn(expected, text)
            self.assertNotIn("LinzeColin/AgentDatabase-Private", text)


if __name__ == "__main__":
    unittest.main()
