from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "memory-atlas"
SCRIPT = APP / "scripts" / "validate_memory_atlas_semantic_readability.mjs"
CONFIG = ROOT / "config" / "memory_atlas_semantic_readability.json"
PROFILES = ROOT / "config" / "memory_atlas_validator_profiles.json"
VALIDATE = ROOT / "scripts" / "memory_atlas_cli" / "validate.py"


def fixture_config(known_findings: list[dict[str, str]] | None = None) -> dict[str, object]:
    return {
        "schema_version": "memory_atlas.semantic_readability.v1_2_1_s05_p3_t2",
        "task_id": "S05-P3-T2",
        "remediation_task": "S05-P3-T3",
        "profile_bindings": ["ui", "release"],
        "rules": [
            "mojibake",
            "main_view_machine_field",
            "actionless_error",
            "english_empty_state",
        ],
        "known_findings": known_findings or [],
    }


def run_validator(src_root: Path, config_path: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    result = subprocess.run(
        ["node", str(SCRIPT), "--src-root", str(src_root), "--config", str(config_path)],
        cwd=APP,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    return result, payload


class SemanticReadabilityTests(unittest.TestCase):
    def test_fixture_detects_all_four_rules_and_exact_baseline_can_ratchet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            src = root / "src"
            src.mkdir()
            (src / "Fixture.tsx").write_text(
                """
                export function Fixture({ proposal }) {
                  return <main>
                    <p>Ã© and ä¸­æ–‡ malformed</p>
                    <p>{proposal.proposal_id}</p>
                    <p title={proposal.source_id}>动态辅助文本</p>
                    <p aria-label={proposal.status}>同名字段碰撞</p>
                    <ErrorState dataState="load" title="读取失败" description="当前无法继续。" />
                    <EmptyState title="No results" description="Nothing found" actionLabel="Retry" />
                    <section className="secondary-empty">No records</section>
                    <section className="secondary-error">Request failed</section>
                  </main>;
                }
                """,
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(json.dumps(fixture_config(), ensure_ascii=False), encoding="utf-8")

            failed, payload = run_validator(src, config_path)

            self.assertEqual(failed.returncode, 2)
            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(
                {finding["rule"] for finding in payload["unexpected_findings"]},
                {
                    "mojibake",
                    "main_view_machine_field",
                    "actionless_error",
                    "english_empty_state",
                },
            )

            known = [
                {
                    "fingerprint": finding["fingerprint"],
                    "rule": finding["rule"],
                    "path": finding["path"],
                    "anchor": finding["anchor"],
                }
                for finding in payload["unexpected_findings"]
            ]
            config_path.write_text(json.dumps(fixture_config(known), ensure_ascii=False), encoding="utf-8")

            passed, ratcheted = run_validator(src, config_path)

            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertEqual(ratcheted["status"], "PASS")
            self.assertTrue(ratcheted["baseline_exact"])
            self.assertEqual(ratcheted["known_finding_count"], len(known))
            self.assertEqual(ratcheted["known_t3_debt_count"], len(known))
            self.assertFalse(ratcheted["semantic_readability_clean"])

    def test_hidden_machine_details_and_actionable_chinese_states_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            src = root / "src"
            src.mkdir()
            (src / "Good.tsx").write_text(
                """
                export function Good({ record }) {
                  return <main>
                    <MachineFieldDetails title="高级详情：机器字段">
                      <p>{record.schema_version}</p>
                    </MachineFieldDetails>
                    <ErrorState dataState="load" title="读取失败" description="请检查数据后重试。" />
                    <EmptyState title="没有结果" description="当前没有匹配结果。" actionLabel="重置筛选" />
                  </main>;
                }
                """,
                encoding="utf-8",
            )
            config_path = root / "config.json"
            config_path.write_text(json.dumps(fixture_config(), ensure_ascii=False), encoding="utf-8")

            result, payload = run_validator(src, config_path)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "PASS")
            self.assertEqual(payload["finding_count"], 0)
            self.assertEqual(payload["known_t3_debt_count"], 0)
            self.assertTrue(payload["semantic_readability_clean"])

    def test_missing_known_finding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            src = root / "src"
            src.mkdir()
            (src / "Good.tsx").write_text("export const Good = () => <p>正常</p>;", encoding="utf-8")
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    fixture_config(
                        [{
                            "fingerprint": "0123456789abcdef",
                            "rule": "mojibake",
                            "path": "Missing.tsx",
                            "anchor": "missing",
                        }]
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result, payload = run_validator(src, config_path)

            self.assertEqual(result.returncode, 2)
            self.assertEqual(payload["status"], "FAIL")
            self.assertFalse(payload["baseline_exact"])
            self.assertEqual(len(payload["missing_known_findings"]), 1)

    def test_current_repo_passes_with_bounded_t3_baseline(self) -> None:
        result, payload = run_validator(APP / "src", CONFIG)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["task_id"], "S05-P3-T2")
        self.assertEqual(payload["remediation_task"], "S05-P3-T3")
        self.assertTrue(payload["baseline_exact"])
        self.assertGreater(payload["known_finding_count"], 0)
        self.assertEqual(payload["known_t3_debt_count"], payload["known_finding_count"])
        self.assertFalse(payload["semantic_readability_clean"])
        self.assertEqual(payload["unexpected_findings"], [])
        self.assertEqual(payload["missing_known_findings"], [])

    def test_existing_ui_and_release_profiles_execute_the_rule(self) -> None:
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        ui_steps = {step["id"]: step for step in profiles["profiles"]["ui"]["steps"]}

        self.assertEqual(
            ui_steps["semantic_readability"]["command"],
            ["@python", "scripts/atlasctl.py", "audit", "--check", "chinese-ux"],
        )
        self.assertEqual(ui_steps["semantic_readability"]["cwd"], "database")
        self.assertIn("validate_memory_atlas_semantic_readability.mjs", VALIDATE.read_text(encoding="utf-8"))
        self.assertEqual(
            profiles["profiles"]["release"]["steps"][0]["command"],
            ["@python", "scripts/atlasctl.py", "audit"],
        )

    def test_existing_chinese_ux_gate_reports_readability_summary(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/atlasctl.py", "audit", "--check", "chinese-ux"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(result.stdout)
        readability = payload["details"]["semantic_readability"]

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(readability["status"], "PASS")
        self.assertTrue(readability["baseline_exact"])
        self.assertEqual(readability["known_t3_debt_count"], readability["known_finding_count"])
        self.assertFalse(readability["semantic_readability_clean"])
        self.assertEqual(readability["unexpected_finding_count"], 0)
        self.assertEqual(readability["missing_known_finding_count"], 0)


if __name__ == "__main__":
    unittest.main()
