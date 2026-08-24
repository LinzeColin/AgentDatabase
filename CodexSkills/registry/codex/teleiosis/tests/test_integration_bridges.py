from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.expert_panel import ROLE_REQUIREMENTS, export_expert_panel_request  # noqa: E402
from wbi_core.verifier_bridge import export_verifier_packet  # noqa: E402


class IntegrationBridgeTests(unittest.TestCase):
    def make_subject(self, root: Path) -> Path:
        subject = root / "teleiosis"
        for rel, content in {
            "SKILL.md": "---\nname: teleiosis\ndescription: test\n---\n# Test\n",
            "README.md": "readme",
            "VERSION": "v0.0.0.2\n",
            "metadata/release.json": "{}",
            "constitution/genesis-lock.json": "{}",
            "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md": "locked",
            "delivery/BASELINE_CHANGE_DECISION.md": "decision",
            "delivery/MARKET_LEADERSHIP_ANALYSIS.md": "analysis",
            "delivery/SELF_ITERATION_REPORT.md": "report",
            "delivery/MECHANISM_ADOPTION_LEDGER.md": "ledger",
            "delivery/RELEASE_NOTES.md": "notes",
            "MANIFEST.sha256": "manifest",
        }.items():
            path = subject / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return subject

    def test_verifier_packet_is_read_only_request_not_self_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            subject = self.make_subject(root)
            output = root / "verifier.zip"
            result = export_verifier_packet(subject, output, "2026-07-26")
            self.assertEqual(result["review_status"], "PACKET_READY_REVIEW_PENDING")
            self.assertFalse(result["formal_promotion_granted"])
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                request_name = "teleiosis-verifier-packet/verification-request.json"
                request = json.loads(archive.read(request_name))
            self.assertTrue(request["verdict_policy"]["builder_self_attestation_is_insufficient"])
            self.assertFalse(request["verdict_policy"]["single_aggregate_score_can_override_critical_failure"])

    def test_verifier_output_must_be_external_to_subject(self):
        with tempfile.TemporaryDirectory() as td:
            subject = self.make_subject(Path(td))
            with self.assertRaises(ValueError):
                export_verifier_packet(subject, subject / "packet.zip", "2026-07-26")

    def test_expert_panel_has_isolated_control_roles_and_no_fake_completion(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "panel.json"
            result = export_expert_panel_request(output, "Review candidate", "2026-07-26")
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["panel_size"], 12)
            self.assertEqual(result["panel_counts"], {"A": 6, "B": 6})
            self.assertEqual(packet["routing_status"], "ROSTER_INPUT_REQUIRED")
            self.assertFalse(packet["independent_review_completed"])
            controls = [role for role in ROLE_REQUIREMENTS if role.get("control_role")]
            self.assertEqual({role["seat"] for role in controls}, {"B6"})
            self.assertTrue(packet["routing_policy"]["external_final_verifier_required"])
            self.assertTrue(packet["routing_policy"]["persona_panel_cannot_grant_formal_promotion"])
            self.assertTrue(packet["routing_policy"]["same_person_or_same_context_cannot_claim_independence"])

    def test_persona_index_is_content_bound_not_interpreted_as_completed_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            index = root / "team-index.json"; index.write_text('{"personas": []}', encoding="utf-8")
            output = root / "panel.json"
            export_expert_panel_request(output, "Review candidate", "2026-07-26", index)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(len(packet["persona_index_binding"]["sha256"]), 64)
            self.assertEqual(packet["routing_status"], "READY_FOR_PERSONA_DISTILLER")
            self.assertFalse(packet["formal_promotion_granted"])


if __name__ == "__main__":
    unittest.main()
