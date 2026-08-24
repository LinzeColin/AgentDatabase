from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import load_json, sha256_file, write_json  # noqa: E402
from wbi_core.reviews import collect_review, generate_review_plan, review_gate  # noqa: E402
from wbi_core.workspace import init_run  # noqa: E402


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.adapter_patch = mock.patch("wbi_core.reviews._invoke_attestation_adapter", side_effect=self.fake_adapter)
        self.adapter_patch.start()

    def tearDown(self):
        self.adapter_patch.stop()

    def fake_adapter(self, contract: dict, payload: dict):
        if payload.get("action") == "capability":
            return {
                "status": "VERIFIED", "provider": contract["provider"],
                "independent_subagents_available": True,
                "read_only_verifier_available": True,
                "provider_receipt_verification": "VERIFIED",
            }, []
        items = []
        for requested in payload.get("items", []):
            receipt = load_json(Path(requested["receipt_path"]))
            expected = requested["expected_identity"]
            if any(receipt.get(key) != value for key, value in expected.items()):
                return {}, ["fixture adapter identity mismatch"]
            items.append({
                "receipt_sha256": sha256_file(Path(requested["receipt_path"])),
                "identity": expected,
                "context_isolated": receipt.get("context_isolated") is True,
                "independent": receipt.get("independent") is True,
                "read_only": receipt.get("read_only") is True,
            })
        return {"status": "VERIFIED", "provider": contract["provider"], "items": items}, []

    def make_workspace(self, root: Path, with_attestation: bool = True) -> Path:
        target = root / "target"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
        ws = root / "run"
        contract_path = None
        if with_attestation:
            receipt_root = root / "provider-receipts"
            receipt_root.mkdir()
            adapter = root / "provider-adapter.py"
            adapter.write_text(
                """#!/usr/bin/env python3
import hashlib, json, pathlib, sys
payload = json.loads(sys.stdin.read())
provider = 'fixture-runtime'
if payload.get('action') == 'capability':
    print(json.dumps({'status':'VERIFIED','provider':provider,'independent_subagents_available':True,'read_only_verifier_available':True,'provider_receipt_verification':'VERIFIED'}))
    raise SystemExit(0)
if payload.get('action') != 'verify-receipt-batch':
    raise SystemExit(4)
items = []
for requested in payload['items']:
    path = pathlib.Path(requested['receipt_path'])
    receipt = json.loads(path.read_text(encoding='utf-8'))
    expected = requested['expected_identity']
    if any(receipt.get(k) != v for k, v in expected.items()):
        raise SystemExit(3)
    items.append({'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'identity':expected,'context_isolated':receipt.get('context_isolated') is True,'independent':receipt.get('independent') is True,'read_only':receipt.get('read_only') is True})
print(json.dumps({'status':'VERIFIED','provider':provider,'items':items}))
""",
                encoding="utf-8",
            )
            adapter.chmod(0o700)
            contract_path = root / "attestation-contract.json"
            write_json(contract_path, {
                "schema_version": "1.0", "status": "FROZEN", "provider": "fixture-runtime",
                "adapter_path": str(adapter.resolve()), "adapter_sha256": sha256_file(adapter),
                "receipt_root": str(receipt_root.resolve()),
                "capabilities": ["independent-subagents", "read-only-verifier"],
                "timeout_seconds": 10,
            })
        init_run(
            target, ws, ROOT, ["incremental"], self_evolve=True,
            review_attestation_contract_path=contract_path,
        )
        index = root / "index.json"
        write_json(index, {"default": ["run.json"]})
        generate_review_plan(ws, index)
        return ws

    def receipt(self, ws: Path, actor_key: str, actor: str, context: str, provider_run: str, name: str) -> dict:
        contract = load_json(ws / "control/contracts/review-attestation-contract.json")
        directory = Path(contract["receipt_root"])
        path = directory / (name + ".json")
        write_json(path, {
            actor_key: actor,
            "context_id": context,
            "provider_run_id": provider_run,
            "context_isolated": True,
            "independent": True,
            "read_only": actor_key == "verifier_actor_id",
            "issuer": "fixture-runtime-control-plane",
            "tool_call_id": "tool-" + name,
        })
        return {
            "type": "runtime-tool-receipt",
            "verification_status": "VERIFIED",
            "receipt_path": path.relative_to(directory).as_posix(),
            "receipt_sha256": sha256_file(path),
        }

    def populate(self, ws: Path, mode="independent-subagent", critical=False, soft_conditional=False):
        packets = sorted((ws / "reviews/packets").glob("*.json"))
        for number, path in enumerate(packets, 1):
            packet = load_json(path)
            findings = []
            if critical and number == 1:
                findings = [{"finding_id": "critical-1", "severity": "CRITICAL", "domain": "safety", "status": "OPEN", "evidence": ["run.json"]}]
            actor = "actor-%02d" % number
            context = "context-%02d" % number
            provider = "provider-%02d" % number
            record = {
                "packet_id": packet["packet_id"], "panel": packet["panel"], "role": packet["role"],
                "actor_id": actor, "context_id": context, "provider_run_id": provider,
                "runtime": "fixture", "model": "fixture", "mode": mode, "context_isolated": True,
                "saw_other_reviews_before_submission": False,
                "verdict": "CONDITIONAL" if soft_conditional and number == 2 else "PASS", "confidence": 0.9,
                "findings": findings, "unknowns": [],
                "evidence_paths": packet["evidence_paths"], "evidence_bindings": packet["evidence_bindings"],
                "attestation": self.receipt(ws, "actor_id", actor, context, provider, "review-%02d" % number),
                "submitted_at": "2026-07-26T12:00:00+00:00",
            }
            record_path = ws / ("review-input-%02d.json" % number)
            write_json(record_path, record)
            collect_review(ws, record_path)
            record_path.unlink()
        review_ids = [path.stem for path in packets]
        hashes = {
            path.stem: sha256_file(path)
            for panel in (1, 2)
            for path in sorted((ws / ("reviews/panel-%d" % panel)).glob("*.json"))
        }
        binding = [{"path": "run.json", "sha256": sha256_file(ws / "run.json"), "bytes": (ws / "run.json").stat().st_size}]
        write_json(ws / "verifier/final-verdict.json", {
            "verifier_actor_id": "actor-13", "context_id": "context-13", "provider_run_id": "provider-13",
            "mode": "independent-read-only-verifier", "read_only": True, "write_actions": [], "optimizer_actor_id": "stable-optimizer",
            "reviewed_packet_ids": review_ids, "reviewed_review_hashes": hashes,
            "finding_resolutions": [], "verdict": "PASS", "evidence_paths": ["run.json"], "evidence_bindings": binding,
            "attestation": self.receipt(ws, "verifier_actor_id", "actor-13", "context-13", "provider-13", "verifier-13"),
            "submitted_at": "2026-07-26T13:00:00+00:00",
        })

    def test_review_plan_reports_all_missing_evidence_before_writing_packets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            ws = root / "run"
            init_run(target, ws, ROOT, ["incremental"], self_evolve=True)
            index = root / "missing-index.json"
            write_json(index, {"default": ["missing-a.json", "missing-b.json"]})
            with self.assertRaises(ValueError) as caught:
                generate_review_plan(ws, index)
            message = str(caught.exception)
            self.assertIn("missing-a.json", message)
            self.assertIn("missing-b.json", message)
            self.assertEqual(list((ws / "reviews/packets").glob("*.json")), [])

    def test_fallback_cannot_masquerade_as_independent(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            self.populate(ws, mode="role-isolated-fallback")
            self.assertEqual(review_gate(ws)["status"], "BLOCKED")

    def test_soft_dissent_does_not_force_lowest_common_denominator(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            self.populate(ws, soft_conditional=True)
            result = review_gate(ws)
            self.assertEqual(result["status"], "PASS", result)
            self.assertTrue(result["soft_dissent"])

    def test_open_critical_finding_blocks_even_with_pass_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            self.populate(ws, critical=True)
            self.assertEqual(review_gate(ws)["status"], "BLOCKED")

    def test_runtime_unavailable_returns_exact_status(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td), with_attestation=False)
            self.assertEqual(review_gate(ws)["status"], "INDEPENDENT_REVIEW_UNAVAILABLE")

    def test_local_capability_claim_is_unavailable_without_external_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td), with_attestation=False)
            write_json(ws / "reviews/runtime-capability.json", {
                "independent_subagents_available": True,
                "provider_receipt_verification": "VERIFIED",
            })
            self.assertEqual(review_gate(ws)["status"], "INDEPENDENT_REVIEW_UNAVAILABLE")

    def test_external_adapter_hash_tamper_is_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            contract = load_json(ws / "control/contracts/review-attestation-contract.json")
            adapter = Path(contract["adapter_path"])
            adapter.write_text(adapter.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
            self.assertEqual(review_gate(ws)["status"], "INDEPENDENT_REVIEW_UNAVAILABLE")

    def test_external_adapter_process_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            contract = load_json(ws / "control/contracts/review-attestation-contract.json")
            self.adapter_patch.stop()
            try:
                from wbi_core.reviews import _invoke_attestation_adapter
                result, errors = _invoke_attestation_adapter(contract, {
                    "action": "capability", "run_id": "fixture", "required": [],
                })
            finally:
                self.adapter_patch.start()
            self.assertEqual(errors, [])
            self.assertEqual(result["status"], "VERIFIED")

    def test_verifier_must_be_distinct_thirteenth_context(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            self.populate(ws)
            verdict = load_json(ws / "verifier/final-verdict.json")
            verdict["verifier_actor_id"] = "actor-01"
            write_json(ws / "verifier/final-verdict.json", verdict)
            self.assertEqual(review_gate(ws)["status"], "BLOCKED")

    def test_packet_or_evidence_mutation_after_seal_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            packet_path = sorted((ws / "reviews/packets").glob("*.json"))[0]
            packet_path.chmod(0o644)
            packet = load_json(packet_path)
            packet["role"] = "rewritten"
            write_json(packet_path, packet)
            self.assertEqual(review_gate(ws)["status"], "BLOCKED")
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            (ws / "run.json").write_text("{}\n", encoding="utf-8")
            self.assertEqual(review_gate(ws)["status"], "BLOCKED")

    def test_review_submission_is_immutable_and_requires_attestation(self):
        with tempfile.TemporaryDirectory() as td:
            ws = self.make_workspace(Path(td))
            packet = load_json(sorted((ws / "reviews/packets").glob("*.json"))[0])
            record = {
                "packet_id": packet["packet_id"], "panel": packet["panel"], "role": packet["role"],
                "actor_id": "a", "context_id": "c", "provider_run_id": "p", "runtime": "r", "model": "m",
                "mode": "independent-subagent", "context_isolated": True, "saw_other_reviews_before_submission": False,
                "verdict": "PASS", "confidence": 1.0, "findings": [], "unknowns": [],
                "evidence_paths": packet["evidence_paths"], "evidence_bindings": packet["evidence_bindings"], "submitted_at": "2026-07-26T12:00:00+00:00",
            }
            input_path = Path(td) / "record.json"
            write_json(input_path, record)
            self.assertEqual(collect_review(ws, input_path)["status"], "BLOCKED")
            record["attestation"] = self.receipt(ws, "actor_id", "a", "c", "p", "single")
            write_json(input_path, record)
            self.assertEqual(collect_review(ws, input_path)["status"], "RECORDED")
            self.assertEqual(collect_review(ws, input_path)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
