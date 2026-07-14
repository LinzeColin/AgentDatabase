from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKTREE_ROOT = ROOT.parent
APP = ROOT / "apps/memory-atlas"
PACKAGE = APP / "package.json"
PROFILE_CONFIG = ROOT / "config/memory_atlas_validator_profiles.json"
MIGRATION_MAP = ROOT / "config/memory_atlas_legacy_command_migrations.json"
LOOKUP_SCRIPT = ROOT / "scripts/memory_atlas_legacy_commands.py"
SOURCE_COMMIT = "f22f2d336e3b5154a68fbabeec33b13be646a56c"
SOURCE_PACKAGE_SHA256 = "06268d65a3db20919a94860a7f2a41c3408204e8aa5276d83f25ca8c8ce29c01"
SOURCE_ALIAS_MANIFEST_SHA256 = "aa3134c05c436f2645052dc6dc8866521df4906a9996dc25fe20b1d2bfcc0689"
PUBLIC_ALIASES = {
    "validate:fast",
    "validate:sync",
    "validate:ui",
    "validate:release",
}


def load_lookup_module():
    if not LOOKUP_SCRIPT.is_file():
        raise AssertionError(f"legacy command lookup script is missing: {LOOKUP_SCRIPT}")
    spec = importlib.util.spec_from_file_location("memory_atlas_legacy_commands_test", LOOKUP_SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("legacy command lookup script cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def source_validate_aliases() -> tuple[bytes, dict[str, str]]:
    package_bytes = subprocess.check_output(
        [
            "git",
            "show",
            f"{SOURCE_COMMIT}:OpenAIDatabase/apps/memory-atlas/package.json",
        ],
        cwd=WORKTREE_ROOT,
    )
    package = json.loads(package_bytes)
    aliases = {
        name: command
        for name, command in package["scripts"].items()
        if name.startswith("validate:")
    }
    return package_bytes, aliases


class LegacyCommandMigrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_lookup_module()
        self.payload = self.module.load_migration_map(ROOT)

    def test_map_matches_the_exact_historical_public_alias_surface(self) -> None:
        package_bytes, source_aliases = source_validate_aliases()
        source_manifest = json.dumps(
            source_aliases,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        mapped_aliases = {
            row["legacy_alias"]: row["previous_package_command"]
            for row in self.payload["migrations"]
        }

        self.assertEqual(hashlib.sha256(package_bytes).hexdigest(), SOURCE_PACKAGE_SHA256)
        self.assertEqual(hashlib.sha256(source_manifest).hexdigest(), SOURCE_ALIAS_MANIFEST_SHA256)
        self.assertEqual(len(source_aliases), 178)
        self.assertEqual(mapped_aliases, source_aliases)
        self.assertEqual(self.payload["source"]["git_commit"], SOURCE_COMMIT)
        self.assertEqual(self.payload["source"]["package_json_sha256"], SOURCE_PACKAGE_SHA256)
        self.assertEqual(
            self.payload["source"]["validate_alias_manifest_sha256"],
            SOURCE_ALIAS_MANIFEST_SHA256,
        )

    def test_policy_is_lookup_only_and_expires_after_one_release(self) -> None:
        policy = self.payload["compatibility_policy"]

        self.assertEqual(policy["mode"], "lookup_only")
        self.assertIs(policy["execution_supported"], False)
        self.assertIs(policy["shell_invocation_allowed"], False)
        self.assertEqual(policy["introduced_version"], "v1.2.1")
        self.assertEqual(policy["removal_version"], "v1.2.2")
        self.assertEqual(policy["maximum_supported_releases"], 1)
        self.assertTrue(policy["removal_required"])

        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        public_aliases = {
            name for name in package["scripts"] if name.startswith("validate:")
        }
        self.assertEqual(public_aliases, PUBLIC_ALIASES)
        self.assertEqual(len(package["scripts"]), 8)

    def test_audit_rejects_a_forged_public_profile_command(self) -> None:
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        package["scripts"]["validate:fast"] = "node scripts/old-validator.cjs"
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            app_dir = database_dir / "apps/memory-atlas"
            app_dir.mkdir(parents=True)
            (app_dir / "package.json").write_text(
                json.dumps(package),
                encoding="utf-8",
            )

            errors = self.module._current_package_errors(database_dir)

        self.assertTrue(any("exact four audited" in error for error in errors))

    def test_every_mapping_is_bounded_to_a_real_profile_and_truthful_target_state(self) -> None:
        profile_config = json.loads(PROFILE_CONFIG.read_text(encoding="utf-8"))
        valid_profiles = set(profile_config["public_profiles"])
        seen: set[str] = set()

        self.assertEqual(self.module.validate_migration_map(self.payload, ROOT), [])
        for row in self.payload["migrations"]:
            with self.subTest(alias=row["legacy_alias"]):
                self.assertNotIn(row["legacy_alias"], seen)
                seen.add(row["legacy_alias"])
                self.assertEqual(row["legacy_command"], f"npm run {row['legacy_alias']}")
                self.assertIn(row["replacement_profile"], valid_profiles)
                self.assertEqual(
                    row["replacement_command"],
                    f"npm run validate:{row['replacement_profile']}",
                )
                self.assertEqual(row["compatibility_mode"], "lookup_only")
                self.assertIs(row["execution_supported"], False)
                target_exists = (APP / row["target_script"]).is_file()
                self.assertEqual(
                    row["target_state"],
                    "retained_internal" if target_exists else "deleted_in_s04_p3_t2",
                )

    def test_invalid_or_indefinite_contract_fails_closed(self) -> None:
        forged = copy.deepcopy(self.payload)
        forged["compatibility_policy"]["removal_version"] = "indefinite"
        forged["compatibility_policy"]["execution_supported"] = True
        forged["migrations"][0]["target_script"] = "scripts/../../outside.cjs"
        forged["migrated_callers"][0]["path"] = "/tmp/forged-caller.mjs"
        forged["migrations"].append(copy.deepcopy(forged["migrations"][0]))

        errors = self.module.validate_migration_map(forged, ROOT)

        self.assertTrue(any("compatibility policy" in error for error in errors))
        self.assertTrue(any("duplicate legacy alias" in error for error in errors))
        self.assertTrue(any("target script is invalid" in error for error in errors))
        self.assertTrue(any("exact 10-path contract" in error for error in errors))

    def test_lookup_returns_machine_readable_replacement_without_execution(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            returncode = self.module.main(
                ["--database-dir", str(ROOT), "--lookup", "validate:stage7"]
            )

        result = json.loads(stdout.getvalue())
        self.assertEqual(returncode, 0)
        self.assertEqual(result["status"], "FOUND")
        self.assertEqual(result["legacy_alias"], "validate:stage7")
        self.assertIn(result["replacement_command"], {
            "npm run validate:fast",
            "npm run validate:sync",
            "npm run validate:ui",
            "npm run validate:release",
        })
        self.assertIs(result["execution_supported"], False)
        self.assertEqual(stderr.getvalue(), "")

        source = LOOKUP_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("shell=True", source)

    def test_unknown_lookup_and_audit_have_explicit_exit_codes(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            unknown_returncode = self.module.main(
                ["--database-dir", str(ROOT), "--lookup", "validate:not-real"]
            )
        unknown = json.loads(stdout.getvalue())

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            audit_returncode = self.module.main(["--database-dir", str(ROOT), "--audit"])
        audit = json.loads(stdout.getvalue())

        self.assertEqual(unknown_returncode, 2)
        self.assertEqual(unknown["status"], "NOT_FOUND")
        self.assertEqual(audit_returncode, 0)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["migration_count"], 178)

    def test_retained_validators_no_longer_require_removed_package_aliases(self) -> None:
        violations: list[str] = []
        for path in sorted((APP / "scripts").glob("validate_*.cjs")) + sorted(
            (APP / "scripts").glob("validate_*.mjs")
        ):
            source = path.read_text(encoding="utf-8")
            if "packageSource.includes" in source and '"validate:' in source:
                violations.append(path.name)
            if "hasAll(packageSource" in source and '"validate:' in source:
                violations.append(path.name)

        self.assertEqual(sorted(set(violations)), [])


if __name__ == "__main__":
    unittest.main()
