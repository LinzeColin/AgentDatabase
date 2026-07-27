from __future__ import annotations

from pathlib import Path
import json
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentationTests(unittest.TestCase):
    def test_progressive_disclosure_and_current_names(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(skill.splitlines()), 250)
        self.assertIn("白箱迭代Skill", skill)
        self.assertIn("Teleiosis", skill)
        self.assertNotIn("scripts/teleiosis.py", skill)

    def test_all_local_markdown_references_exist(self):
        missing = []
        pattern = re.compile(r"`((?:references|delivery|constitution|templates|schemas|scripts)/[^`]+)`")
        for path in ROOT.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for match in pattern.findall(text):
                candidate = ROOT / match
                if any(char in match for char in ("<", ">", "*")):
                    continue
                if not candidate.exists():
                    missing.append("%s -> %s" % (path.relative_to(ROOT), match))
        self.assertEqual(missing, [])

    def test_no_obsolete_fixed_limits_or_old_cli(self):
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in list((ROOT / "references").glob("*.md")) + [ROOT / "SKILL.md", ROOT / "README.md"])
        self.assertNotIn("10+3", corpus)
        self.assertNotIn("Maximum three extension rounds", corpus)
        self.assertNotIn("one allowed architecture reset", corpus)
        self.assertNotIn("scripts/teleiosis.py", corpus)

    def test_documented_cli_commands_exist(self):
        completed = subprocess.run([sys.executable, str(ROOT / "scripts/wbi.py"), "--help"], text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0)
        for command in ("verify-self", "init-run", "competitors", "freshness-scan", "seal-eval", "review-plan", "gate", "package", "install", "install-status", "recover-install"):
            self.assertIn(command, completed.stdout)

    def test_research_registry_is_dated_and_current(self):
        research = (ROOT / "references/RESEARCH_SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("2026-07-26", research)
        for token in ("darwin-skill", "luban-skill", "SkillOpt", "SkillMOO", "CoEvoSkills", "SkillLens", "MetaSkill-Evolve", "SkillAudit", "SkillsVote", "SkillCoach", "FederatedSkill"):
            self.assertIn(token, research)
        for stale in ("2607.16997", "2607.19063", "2607.13666", "2606.23844"):
            self.assertNotIn(stale, research)

    def test_formal_review_docs_require_external_attestation(self):
        review = (ROOT / "references/INDEPENDENT_REVIEW.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("external", review.lower())
        self.assertIn("--review-attestation-contract", readme)
        self.assertIn("INDEPENDENT_REVIEW_UNAVAILABLE", review)
        self.assertNotIn("provider logs or runtime attestations are the preferred", review)

    def test_release_docs_distinguish_structural_and_deep_verification(self):
        install = (ROOT / "delivery/INSTALL.md").read_text(encoding="utf-8")
        taskpack = (ROOT / "delivery/CODEX_TASK_PACK_v0.0.0.1.md").read_text(encoding="utf-8")
        self.assertIn("--verification-level release", install)
        self.assertIn("--expected-archive-sha256", install)
        self.assertIn("--result-file", install)
        self.assertIn("install-status", install)
        self.assertIn("recover-install", install)
        self.assertIn("engineering", taskpack.lower())
        self.assertIn("formal", taskpack.lower())

    def test_release_docs_use_one_canonical_archive_filename(self):
        release = json.loads((ROOT / "metadata/release.json").read_text(encoding="utf-8"))
        canonical_archive = release["canonical_archive"]
        documents = [
            ROOT / "README.md",
            ROOT / "delivery/INSTALL.md",
            ROOT / "delivery/CODEX_TASK_PACK_v0.0.0.1.md",
        ]
        observed = {}
        archive_pattern = re.compile(r"[A-Za-z][A-Za-z0-9.-]*v0\.0\.0\.1-final\.zip")
        for path in documents:
            matches = sorted(set(archive_pattern.findall(path.read_text(encoding="utf-8"))))
            observed[str(path.relative_to(ROOT))] = matches
            self.assertEqual(matches, [canonical_archive], observed)


if __name__ == "__main__":
    unittest.main()
