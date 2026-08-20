from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "ops" / "memory-atlas" / "source-registry.json"


def test_local_agent_state_coverage_is_explicit_and_required() -> None:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    sources = {str(item["source_id"]): item for item in payload["sources"]}
    expected = {
        "codex_skills",
        "shared_agent_skills",
        "claude_projects",
        "claude_sessions",
        "claude_tasks",
        "claude_scheduled_tasks",
        "claude_skills",
        "dsh_sessions",
        "dsh_attachments",
        "dsh_cron_configuration",
        "kimi_code_sessions",
        "kimi_code_user_history",
        "kimi_code_file_state",
        "kimi_code_files",
        "kimi_code_cron_configuration",
        "workbuddy_state_database",
        "workbuddy_projects",
        "workbuddy_sessions",
        "workbuddy_tasks",
        "workbuddy_plans",
        "workbuddy_memory",
        "workbuddy_skills",
        "workbuddy_automation_backups",
        "workbuddy_workspace",
        "workbuddy_file_history",
        "workbuddy_artifact_index",
        "workbuddy_audit_log",
        "automation_reports",
        "codex_configuration",
        "claude_backups",
        "claude_hooks",
        "dsh_profiles",
        "dsh_storages",
        "dsh_plugins",
        "dsh_cron_flags",
        "dsh_cron_logs",
        "dsh_patches",
        "kimi_code_server_state",
        "workbuddy_project_resources",
        "workbuddy_plugins",
        "workbuddy_connectors",
    }

    assert expected <= set(sources)
    assert all(sources[source_id]["required"] is True for source_id in expected)


def test_local_agent_state_sources_are_scoped_to_product_data() -> None:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    sources = {str(item["source_id"]): item for item in payload["sources"]}

    assert sources["workbuddy_state_database"]["kind"] == "sqlite"
    assert sources["dsh_archived_sessions"]["required"] is False
    expected_paths = {
        "kimi_code_file_state": "$HOME/.kimi-code/file",
        "kimi_code_files": "$HOME/.kimi-code/files",
        "workbuddy_tasks": "$HOME/.workbuddy/tasks",
        "workbuddy_plans": "$HOME/.workbuddy/plans",
        "workbuddy_memory": "$HOME/.workbuddy/memory",
        "workbuddy_skills": "$HOME/.workbuddy/skills",
        "workbuddy_automation_backups": "$HOME/.workbuddy/automation-backups",
        "workbuddy_workspace": "$HOME/.workbuddy/workspace",
        "workbuddy_file_history": "$HOME/.workbuddy/file-history",
        "workbuddy_artifact_index": "$HOME/.workbuddy/artifact-index",
        "workbuddy_audit_log": "$HOME/.workbuddy/audit-log",
    }
    for source_id, path_template in expected_paths.items():
        assert sources[source_id]["path_template"] == path_template
        assert "env_var" not in sources[source_id]
