from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.competitors import (  # noqa: E402
    _safe_extract_tar_bytes, _safe_git_env, build_competitor_dataset, build_queries, github_search, inspect_repository,
    qualify_peer, select_peers, validate_slug,
)
from wbi_core.freshness import build_freshness_scan, reheat_status  # noqa: E402


class CompetitorTests(unittest.TestCase):
    def make_repo(self, root: Path, name: str) -> Path:
        repo = root / name
        repo.mkdir()
        (repo / "SKILL.md").write_text("---\nname: %s\ndescription: agent skill optimizer\n---\n# %s\n" % (name, name), encoding="utf-8")
        (repo / "README.md").write_text("# Demo\nInstall and result showcase.\n", encoding="utf-8")
        (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
        (repo / "assets").mkdir()
        (repo / "assets" / "showcase.html").write_text("<html>result</html>", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True)
        return repo

    def test_slug_rejects_path_and_command_injection(self):
        for value in ("../evil/repo", "owner/repo;rm", "owner/$(id)", "-owner/repo", "owner/-repo"):
            with self.assertRaises(ValueError):
                validate_slug(value)
        self.assertEqual(validate_slug("LearnPrompt/luban-skill"), "LearnPrompt/luban-skill")


    def test_competitor_resource_parameters_are_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "dataset"
            for kwargs in (
                {"max_candidates": 0}, {"max_candidates": 101},
                {"timeout": 4}, {"timeout": 601},
                {"min_remote_github": -1}, {"min_remote_github": 6},
            ):
                with self.assertRaises(ValueError):
                    build_competitor_dataset(ROOT, output, [], offline=True, **kwargs)
        for kwargs in ({"per_page": 0}, {"per_page": 101}, {"timeout": 0}, {"timeout": 61}, {"max_response_bytes": 100}):
            with self.assertRaises(ValueError):
                github_search("agent skill", **kwargs)

    def test_query_generation_is_grounded_and_bounded(self):
        queries = build_queries(ROOT)
        self.assertTrue(queries)
        self.assertLessEqual(len(queries), 10)
        self.assertTrue(any("skill" in query.lower() for query in queries))

    def test_repository_inspection_is_no_exec_and_finds_artifacts(self):
        result = inspect_repository(ROOT)
        self.assertFalse(result["third_party_code_executed"])
        self.assertTrue(result["signals"]["has_skill"])
        self.assertTrue(result["signals"]["has_tests"])

    def test_tar_traversal_and_links_rejected(self):
        for kind in ("traversal", "symlink"):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode="w") as archive:
                if kind == "traversal":
                    info = tarfile.TarInfo("../escape.txt")
                    data = b"x"
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
                else:
                    info = tarfile.TarInfo("link")
                    info.type = tarfile.SYMTYPE
                    info.linkname = "/etc/passwd"
                    archive.addfile(info)
            with tempfile.TemporaryDirectory() as td:
                with self.assertRaises(ValueError):
                    _safe_extract_tar_bytes(stream.getvalue(), Path(td), 10, 1000)

    def test_local_fixtures_never_satisfy_production_peer_gate(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repos = []
            cats = ["direct", "direct", "indirect", "craft", "direct"]
            for index, category in enumerate(cats):
                repo = self.make_repo(base, "repo-%d" % index)
                repos.append(("fixture/repo-%d" % index, repo, category))
            output = base / "dataset"
            result = build_competitor_dataset(ROOT, output, [], offline=True, local_repositories=repos, min_remote_github=1)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["selection"]["eligible_count"], 0)
            rows = [json.loads(line) for line in (output / "competitor-dataset.jsonl").read_text().splitlines()]
            self.assertTrue(all(row["production_eligible"] is False for row in rows))

    def test_multisource_real_peers_can_qualify_but_github_quota_is_separate(self):
        rows = []
        cats = ["direct", "direct", "indirect", "craft", "direct"]
        for index, category in enumerate(cats):
            rows.append({
                "peer_id": "product:%d" % index, "source_url": "https://example.com/%d" % index,
                "category": category, "evidence_mode": "product-live", "captured_at": "2026-07-26T00:00:00+00:00",
                "license_status": "commercial-terms-observed", "observed_artifacts": ["live output"],
                "reproduction_or_observation": ["open product", "run scenario"], "third_party_code_executed": False,
                "relevance_score": 0.9 - index * 0.01,
            })
        self.assertEqual(select_peers(rows, min_remote_github=0)["status"], "PASS")
        blocked = select_peers(rows, min_remote_github=1)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIn("auto-pulled GitHub", " ".join(blocked["errors"]))

    def test_metadata_only_cannot_qualify(self):
        passed, reasons = qualify_peer({
            "peer_id": "x", "category": "direct", "evidence_mode": "web-metadata",
            "source_url": "https://github.com/a/b", "captured_at": "2026-07-26T00:00:00+00:00", "license_status": "unknown",
        })
        self.assertFalse(passed)
        self.assertTrue(reasons)

    def test_freshness_scan_requires_all_categories_and_expires(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            records = root / "sources.jsonl"
            rows = []
            for category in ("models-runtimes", "methods-architectures", "evaluation", "standards-security", "competitors"):
                rows.append({
                    "source_id": category, "category": category, "title": category, "url": "https://example.com/%s" % category,
                    "source_type": "official-doc", "authority": "primary", "queried_at": "2026-07-26T00:00:00+00:00",
                    "claim": "observed", "status": "VERIFIED", "version_or_date": "2026-07-26", "unknowns": [],
                })
            records.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            result = build_freshness_scan(records, root / "out", "2026-07-26T00:00:00+00:00", 30)
            self.assertEqual(result["status"], "PASS")
            current = reheat_status(root / "out" / "freshness-scan.json", "2026-08-01T00:00:00+00:00")
            expired = reheat_status(root / "out" / "freshness-scan.json", "2026-09-01T00:00:00+00:00")
            self.assertEqual(current["status"], "CURRENT")
            self.assertEqual(expired["status"], "REHEAT_REQUIRED")

    def test_git_environment_ignores_host_configs_and_credentials(self):
        env = _safe_git_env()
        self.assertEqual(env["GIT_CONFIG_GLOBAL"], __import__("os").devnull)
        self.assertEqual(env["GIT_CONFIG_SYSTEM"], __import__("os").devnull)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["GIT_ALLOW_PROTOCOL"], "https")
        self.assertEqual(env["GIT_LFS_SKIP_SMUDGE"], "1")
        self.assertNotIn("GIT_CONFIG_COUNT", env)
        with self.assertRaises(ValueError):
            _safe_git_env({"GIT_CONFIG_COUNT": "1"})

    def test_tar_duplicate_case_collision_and_backslash_are_rejected(self):
        builders = []
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            for name in ("a.txt", "a.txt"):
                info = tarfile.TarInfo(name); data = b"x"; info.size = 1; archive.addfile(info, io.BytesIO(data))
        builders.append(stream.getvalue())
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            for name in ("a.txt", "A.txt"):
                info = tarfile.TarInfo(name); data = b"x"; info.size = 1; archive.addfile(info, io.BytesIO(data))
        builders.append(stream.getvalue())
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo("dir\\..\\escape.txt"); data = b"x"; info.size = 1; archive.addfile(info, io.BytesIO(data))
        builders.append(stream.getvalue())
        for payload in builders:
            with tempfile.TemporaryDirectory() as td:
                with self.assertRaises(ValueError):
                    _safe_extract_tar_bytes(payload, Path(td), 10, 1000)


if __name__ == "__main__":
    unittest.main()
