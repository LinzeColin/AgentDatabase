import subprocess
import sys
import unittest
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.artifact_boundary import (
    ArtifactBoundaryPolicy,
    Plane,
    scan_staged,
    scan_working_tree,
)


POLICY = ArtifactBoundaryPolicy.from_yaml(MODULE_ROOT / "config" / "artifact_classification.yml")


class ArtifactBoundaryTests(unittest.TestCase):
    def test_three_planes_and_default_deny(self) -> None:
        self.assertIs(POLICY.classify("src/project_cost_table/__init__.py"), Plane.PUBLIC_SAFE)
        self.assertIs(POLICY.classify("HANDOFF.md"), Plane.PUBLIC_SAFE)
        self.assertIs(POLICY.classify("private_runtime/runs/result.json"), Plane.PRIVATE_RUNTIME)
        self.assertIs(POLICY.classify("raw/source.xlsx"), Plane.RAW_SOURCE)
        self.assertIs(POLICY.classify("mystery/data.txt"), Plane.UNCLASSIFIED)
        self.assertIs(POLICY.classify("../escape.txt"), Plane.UNCLASSIFIED)

    def test_private_candidate_and_forbidden_extension_are_blocked(self) -> None:
        private_findings = POLICY.inspect_public_bytes("private_seed/reference.json", b"{}")
        self.assertEqual([finding.code for finding in private_findings], ["NON_PUBLIC_PATH"])
        extension_findings = POLICY.inspect_public_bytes("tests/synthetic/example.xlsx", b"not a workbook")
        self.assertIn("FORBIDDEN_EXTENSION", {finding.code for finding in extension_findings})

    def test_local_home_signature_is_blocked_without_storing_a_real_path(self) -> None:
        sensitive = ("/" + "Users" + "/example/private/input").encode("utf-8")
        findings = POLICY.inspect_public_bytes("references/example.txt", sensitive)
        self.assertIn("FORBIDDEN_CONTENT", {finding.code for finding in findings})

    def test_current_public_working_tree_passes(self) -> None:
        self.assertEqual(scan_working_tree(MODULE_ROOT, POLICY), [])

    def test_staged_scanner_reads_index_and_rejects_forced_private_seed(self) -> None:
        with self.subTest("temporary Git index"):
            import tempfile

            with tempfile.TemporaryDirectory() as temporary:
                repo = Path(temporary) / "repo"
                module = repo / "KMFA" / "project-cost-table-skill"
                public_file = module / "src" / "safe.py"
                private_file = module / "private_seed" / "reference.json"
                public_file.parent.mkdir(parents=True)
                private_file.parent.mkdir(parents=True)
                public_file.write_text("SAFE = True\n", encoding="utf-8")
                private_file.write_text("{}\n", encoding="utf-8")
                subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
                self._git(repo, "add", "KMFA/project-cost-table-skill/src/safe.py")
                self.assertEqual(scan_staged(repo, "KMFA/project-cost-table-skill", POLICY), [])
                self._git(repo, "add", "-f", "KMFA/project-cost-table-skill/private_seed/reference.json")
                findings = scan_staged(repo, "KMFA/project-cost-table-skill", POLICY)
                self.assertTrue(any(finding.code == "NON_PUBLIC_PATH" for finding in findings))

    def test_public_symlink_is_blocked(self) -> None:
        findings = POLICY.inspect_public_bytes("references/link.txt", b"", git_mode="120000")
        self.assertIn("SYMLINK_FORBIDDEN", {finding.code for finding in findings})

    @staticmethod
    def _git(repo: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=str(repo), check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
