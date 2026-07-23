from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DATABASE_DIR.parent
SCRIPT = DATABASE_DIR / "scripts/workflow_security_audit.py"
CHECKOUT_SHA = "34e114876b0b11c390a56381ad16ebd13914f8d5"


def load_module():
    spec = importlib.util.spec_from_file_location("workflow_security_audit_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workflow_text(permission: str = "read", extra_write: str = "") -> str:
    extra = f"  {extra_write}: write\n" if extra_write else ""
    return (
        "name: Test\n"
        "on:\n"
        "  push:\n"
        "permissions:\n"
        f"  contents: {permission}\n"
        f"{extra}"
        "concurrency:\n"
        "  group: test\n"
        "jobs:\n"
        "  test:\n"
        "    timeout-minutes: 5\n"
        "    steps:\n"
        "      - name: Checkout\n"
        f"        uses: actions/checkout@{CHECKOUT_SHA}\n"
    )


def policy_for(path: str, *, write: bool = False) -> dict:
    workflow = {
        "path": path,
        "role": "test_writer" if write else "test_reader",
        "trust_boundary": "test",
    }
    if write:
        workflow.update(
            {
                "required_permissions": {"contents": "write"},
                "allowed_write_permissions": ["contents"],
                "write_allowlist": ["output.txt"],
            }
        )
    return {
        "allowed_workflows": [path],
        "allowed_nested_workflows": [],
        "required_permissions": {"contents": "read"},
        "action_pins": [
            {
                "action": "actions/checkout",
                "commit_sha": CHECKOUT_SHA,
            }
        ],
        "workflows": [workflow],
        "forbidden_events": [],
    }


class WorkflowSecurityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_repository_policy_owns_scoped_writer_and_exact_nested_payloads(self) -> None:
        policy = self.module.load_policy(REPO_ROOT)
        report = self.module.audit(REPO_ROOT, policy)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["invalid_nested_workflow_count"], 0)
        self.assertEqual(
            sorted(report["nested_workflows"]),
            sorted(policy["allowed_nested_workflows"]),
        )
        writer = next(
            row
            for row in policy["workflows"]
            if row["path"] == ".github/workflows/dynamic-profile-update.yml"
        )
        self.assertEqual(writer["required_permissions"], {"contents": "write"})
        self.assertEqual(writer["allowed_write_permissions"], ["contents"])
        self.assertEqual(
            writer["write_allowlist"],
            ["OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md"],
        )
        recurring_writer = next(
            row
            for row in policy["workflows"]
            if row["path"] == ".github/workflows/recurring-prompt-analysis.yml"
        )
        self.assertEqual(
            recurring_writer["required_permissions"],
            {"contents": "write"},
        )
        self.assertEqual(
            recurring_writer["allowed_write_permissions"],
            ["contents"],
        )
        self.assertEqual(
            recurring_writer["write_allowlist"],
            [
                "OpenAIDatabase/data/derived/behavior_intelligence/"
                "recurring_prompts/",
                "OpenAIDatabase/人类可读/00_Recurring分析_最新.md",
                "OpenAIDatabase/人类可读/00_Recurring运行状态.md",
            ],
        )
        self.assertIn(
            {
                "action": "actions/upload-artifact",
                "commit_sha": "ea165f8d65b6e75b540449e92b4886f43607fa02",
                "source": (
                    "https://api.github.com/repos/actions/upload-artifact/"
                    "git/ref/tags/v4"
                ),
            },
            policy["action_pins"],
        )

    def test_unregistered_nested_workflow_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflow = root / ".github/workflows/ci.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(workflow_text(), encoding="utf-8")
            nested = root / "payload/.github/workflows/ci.yml"
            nested.parent.mkdir(parents=True)
            nested.write_text("name: inert payload\n", encoding="utf-8")
            policy = policy_for(".github/workflows/ci.yml")

            rejected = self.module.audit(root, policy)
            self.assertEqual(rejected["status"], "FAIL")
            self.assertEqual(rejected["invalid_nested_workflow_count"], 1)
            self.assertEqual(
                rejected["invalid_nested_workflows"],
                ["payload/.github/workflows/ci.yml"],
            )

            allowed = copy.deepcopy(policy)
            allowed["allowed_nested_workflows"] = ["payload/.github/workflows/ci.yml"]
            accepted = self.module.audit(root, allowed)
            self.assertEqual(accepted["status"], "PASS")

    def test_single_file_writer_rejects_any_unscoped_write_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workflow = root / ".github/workflows/writer.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(workflow_text(permission="write"), encoding="utf-8")
            policy = policy_for(".github/workflows/writer.yml", write=True)

            accepted = self.module.audit(root, policy)
            self.assertEqual(accepted["status"], "PASS")
            self.assertEqual(accepted["high_privilege_violations"], 0)
            self.assertEqual(accepted["external_action_refs"], 1)

            workflow.write_text(
                workflow_text(permission="write", extra_write="issues"),
                encoding="utf-8",
            )
            rejected = self.module.audit(root, policy)
            self.assertEqual(rejected["status"], "FAIL")
            self.assertEqual(rejected["high_privilege_violations"], 1)

            workflow.write_text(
                workflow_text(permission="write").replace(
                    f"actions/checkout@{CHECKOUT_SHA}",
                    "actions/checkout@v4",
                ),
                encoding="utf-8",
            )
            rejected_pin = self.module.audit(root, policy)
            self.assertEqual(rejected_pin["status"], "FAIL")
            self.assertEqual(rejected_pin["unpinned_actions"], 1)
            self.assertEqual(rejected_pin["unapproved_actions"], 1)


if __name__ == "__main__":
    unittest.main()
