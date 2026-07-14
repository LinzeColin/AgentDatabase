from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from memory_atlas_r8_acceptance import (
    FOUR_LINE_GATES,
    REQUIRED_R8_GATE_IDS,
    AcceptanceHistoryError,
    build_acceptance_summary,
)

from .constants import (
    FINAL_AUDIT_ACCEPTANCE_ID,
    FINAL_AUDIT_CONTRACT_VERSION,
    FINAL_AUDIT_OUTPUT_TAIL_CHARS,
    FINAL_AUDIT_PHASE_STATUS,
    FINAL_AUDIT_TASK_ID,
    ROOT,
)


def final_audit_gate_plan(database_dir: Path) -> list[dict[str, object]]:
    app_dir = database_dir / "apps/memory-atlas"
    worktree_root = database_dir.parent
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree_root,
        text=True,
        capture_output=True,
        check=False,
    )
    exact_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "UNRESOLVED_HEAD"
    recovery_output = Path(tempfile.gettempdir()) / f"memory-atlas-r8-recovery-{uuid.uuid4().hex}"
    return [
        {
            "gate_id": "unit_tests",
            "name_zh": "Python unit tests",
            "command": [sys.executable, "-B", "-m", "unittest", "discover", f"{database_dir.name}/tests", "-q"],
            "cwd": str(database_dir.parent),
            "timeout_seconds": 900,
            "pass_explanation_zh": "Python 单元测试通过。",
            "fail_explanation_zh": "Python 单元测试失败；先看 stdout_tail/stderr_tail 中的失败用例和 traceback。",
        },
        {
            "gate_id": "frontend_build",
            "name_zh": "Frontend build",
            "command": ["npm", "run", "build", "--prefix", "apps/memory-atlas"],
            "cwd": str(database_dir),
            "timeout_seconds": 300,
            "pass_explanation_zh": "前端生产构建通过。",
            "fail_explanation_zh": "前端生产构建失败；先修复 TypeScript 或 Vite build 错误。",
        },
        {
            "gate_id": "chinese_ux_audit",
            "name_zh": "Chinese UX audit",
            "command": [sys.executable, "scripts/atlasctl.py", "audit", "--check", "chinese-ux"],
            "cwd": str(database_dir),
            "timeout_seconds": 180,
            "pass_explanation_zh": "中文 UX 审计通过。",
            "fail_explanation_zh": "中文 UX 审计失败；先修复默认中文、机器字段折叠或中文解释缺失。",
        },
        {
            "gate_id": "rendered_chinese_ux",
            "name_zh": "Rendered Chinese UX and three-viewport Home audit",
            "command": ["node", "scripts/validate_memory_atlas_v1_2_home_multiviewport.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 300,
            "pass_explanation_zh": "三视口真实浏览器中文 UX、布局、可达性和默认人类界面审计通过。",
            "fail_explanation_zh": "三视口中文 UX 失败；先修复重叠、裁切、英文残留、raw manifest 污染或不可达内容。",
        },
        {
            "gate_id": "visual_roi_audit",
            "name_zh": "Visual ROI audit",
            "command": [sys.executable, "scripts/atlasctl.py", "audit", "--check", "visual-roi"],
            "cwd": str(database_dir),
            "timeout_seconds": 180,
            "pass_explanation_zh": "Visual ROI 审计通过。",
            "fail_explanation_zh": "Visual ROI 审计失败；先修复 P0 视觉候选、人类问题或行动解释。",
        },
        {
            "gate_id": "visual_workflows",
            "name_zh": "Twelve visual decision workflows",
            "command": ["node", "scripts/validate_memory_atlas_v1_2_visual_workflows.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 420,
            "pass_explanation_zh": "十二项真实视觉工作流、筛选、证据交互和公式变化审计通过。",
            "fail_explanation_zh": "视觉工作流失败；先修复真实数据联动、筛选差异、证据入口或公式交互。",
        },
        {
            "gate_id": "command_workflows",
            "name_zh": "Command workflow browser audit",
            "command": ["node", "scripts/validate_memory_atlas_v1_2_command_workflows.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 420,
            "pass_explanation_zh": "六个命令工作流通过真实浏览器与受控本地 runtime 审计。",
            "fail_explanation_zh": "命令工作流失败；先修复执行路径、结果反馈、静默发送边界或 runtime 接口。",
        },
        {
            "gate_id": "proposal_e2e",
            "name_zh": "Authorized proposal apply and rollback E2E",
            "command": ["node", "scripts/validate_memory_atlas_v1_2_proposal_e2e.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 420,
            "pass_explanation_zh": "提案审批、授权 apply、验证失败自动回滚和人工回滚端到端审计通过。",
            "fail_explanation_zh": "提案端到端失败；先修复授权令牌、allowlist、验证、事务恢复或 rollback。",
        },
        {
            "gate_id": "owner_daily_e2e",
            "name_zh": "Owner Daily product entry E2E",
            "command": ["node", "scripts/validate_memory_atlas_v1_2_owner_daily_e2e.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 420,
            "pass_explanation_zh": "Owner Daily 八步运行、中文结论和仅重试失败步骤的产品入口审计通过。",
            "fail_explanation_zh": "Owner Daily 失败；先修复八步执行、结果归纳或固定失败步骤重试。",
        },
        {
            "gate_id": "stage7_visual",
            "name_zh": "Canvas visual acceptance",
            "command": ["node", "scripts/validate_stage7_visual_acceptance.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 300,
            "pass_explanation_zh": "Galaxy 与 Memory River 真实 canvas 非空、映射和交互审计通过。",
            "fail_explanation_zh": "Canvas 视觉审计失败；先修复空白画布、映射、构图或浏览器错误。",
        },
        {
            "gate_id": "stage7_performance",
            "name_zh": "Canvas performance acceptance",
            "command": ["node", "scripts/validate_stage7_performance_acceptance.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 300,
            "pass_explanation_zh": "桌面与移动性能预算审计通过。",
            "fail_explanation_zh": "性能审计失败；先修复帧率、启动耗时或资源预算超限。",
        },
        {
            "gate_id": "stage7_privacy_accessibility",
            "name_zh": "Release privacy and accessibility acceptance",
            "command": ["node", "scripts/validate_stage7_privacy_accessibility.cjs"],
            "cwd": str(app_dir),
            "timeout_seconds": 600,
            "pass_explanation_zh": "发布隐私、512 文件全内容安全、reduced-motion 和静默默认审计通过。",
            "fail_explanation_zh": "发布隐私或可访问性失败；先修复敏感数据、manifest/ledger、动效或静默默认。",
        },
        {
            "gate_id": "raw_append_only_audit",
            "name_zh": "Raw append-only audit",
            "command": [sys.executable, "scripts/raw_archive_manifest.py", "audit", "--database-dir", str(database_dir)],
            "cwd": str(database_dir),
            "timeout_seconds": 180,
            "pass_explanation_zh": "raw append-only 审计通过。",
            "fail_explanation_zh": "raw append-only 审计失败；先处理 raw 删除、hash drift 或新增 raw 未登记问题。",
        },
        {
            "gate_id": "credential_audit",
            "name_zh": "Credential audit",
            "command": [sys.executable, "scripts/privacy_guard.py", "--database-dir", str(database_dir), "--scan-only"],
            "cwd": str(database_dir),
            "timeout_seconds": 180,
            "pass_explanation_zh": "凭证审计通过。",
            "fail_explanation_zh": "凭证审计失败；先移除硬编码 secret、token、cookie 或私有 raw 文件。",
        },
        {
            "gate_id": "github_backup_modes",
            "name_zh": "GitHub backup dry-run and apply modes",
            "command": [sys.executable, "-B", "-m", "unittest", "tests.test_s04p3_github_backup", "-q"],
            "cwd": str(database_dir),
            "timeout_seconds": 180,
            "pass_explanation_zh": "GitHub 备份 dry-run 与隔离 apply 本地提交模式通过，且不会远端 push。",
            "fail_explanation_zh": "GitHub 备份模式失败；先修复范围预览、本地 commit 或 no-remote-push 边界。",
        },
        {
            "gate_id": "tracked_only_recovery",
            "name_zh": "Exact-commit tracked-only recovery",
            "command": [
                sys.executable,
                "scripts/audit_memory_atlas_github_recovery.py",
                "--repo-root",
                str(worktree_root),
                "--commit",
                exact_commit,
                "--output-dir",
                str(recovery_output),
            ],
            "cwd": str(database_dir),
            "timeout_seconds": 1200,
            "pass_explanation_zh": "当前精确 Git commit 可仅凭 tracked files 恢复源包、raw、release、依赖和生产构建。",
            "fail_explanation_zh": "精确 commit 恢复失败；先修复 Git 可移植资料、源包、raw 完整性、依赖或构建。",
        },
        {
            "gate_id": "report_contract_audit",
            "name_zh": "Report contract audit",
            "command": [
                sys.executable,
                "scripts/audit_memory_atlas_acceptance.py",
                "--repo-root",
                str(database_dir),
            ],
            "cwd": str(database_dir),
            "timeout_seconds": 300,
            "pass_explanation_zh": "报告与验收合同审计通过。",
            "fail_explanation_zh": "报告与验收合同审计失败；先修复 acceptance、release、Cloudflare preflight 或报告字段合同。",
        },
    ]


def compact_tail(value: str | bytes, limit: int = FINAL_AUDIT_OUTPUT_TAIL_CHARS) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if len(value) <= limit:
        return value
    return value[-limit:]


def final_audit_dry_run_contract(args: argparse.Namespace) -> dict[str, object]:
    gates = [
        {
            "gate_id": gate["gate_id"],
            "name_zh": gate["name_zh"],
            "command": gate["command"],
            "dry_run": True,
            "chinese_explanation": "计划执行该 gate；dry-run 不运行命令。",
        }
        for gate in final_audit_gate_plan(args.database_dir)
    ]
    return {
        "status": "PASS",
        "command": "audit",
        "check": "final",
        "task_id": FINAL_AUDIT_TASK_ID,
        "acceptance_id": FINAL_AUDIT_ACCEPTANCE_ID,
        "contract_version": FINAL_AUDIT_CONTRACT_VERSION,
        "phase_status": FINAL_AUDIT_PHASE_STATUS,
        "dry_run": True,
        "gates": gates,
        "required_r8_gate_ids": list(REQUIRED_R8_GATE_IDS),
        "four_line_gate_plan": [
            {
                "line_id": line["line_id"],
                "name_zh": line["name_zh"],
                "gate_ids": list(line["gate_ids"]),
            }
            for line in FOUR_LINE_GATES
        ],
        "high_token_auto_summary": False,
        "max_output_chars_per_gate": FINAL_AUDIT_OUTPUT_TAIL_CHARS * 2,
        "writes_files": False,
        "writes_tracked_files": False,
        "raw_mutation": False,
        "remote_push": False,
        "github_main_upload": False,
        "phase_boundary": {
            "does_not_upload_github_main": True,
            "does_not_reinstall_app": True,
            "does_not_clean_local_computer": True,
            "stage_review_deferred_to": "S14 Review",
            "next_phase": "S14 P3",
        },
        "中文说明": "S14 P2 final audit dry-run 只列出 gate，不运行测试、不构建、不上传。",
    }


def run_final_audit(args: argparse.Namespace) -> int:
    if args.dry_run:
        print(json.dumps(final_audit_dry_run_contract(args), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    gates: list[dict[str, object]] = []
    for gate in final_audit_gate_plan(args.database_dir):
        command = [str(part) for part in gate["command"]]
        try:
            result = subprocess.run(
                command,
                cwd=str(gate.get("cwd") or ROOT),
                text=True,
                capture_output=True,
                check=False,
                timeout=int(gate["timeout_seconds"]),
            )
            returncode = result.returncode
            stdout_tail = compact_tail(result.stdout or "")
            stderr_tail = compact_tail(result.stderr or "")
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout_tail = compact_tail(exc.stdout or "")
            stderr_tail = compact_tail(exc.stderr or "")

        passed = returncode == 0
        gates.append({
            "gate_id": gate["gate_id"],
            "name_zh": gate["name_zh"],
            "command": command,
            "status": "PASS" if passed else "FAIL",
            "returncode": returncode,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "chinese_explanation": gate["pass_explanation_zh"] if passed else gate["fail_explanation_zh"],
        })

    failed = [gate for gate in gates if gate["status"] != "PASS"]
    try:
        verified_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=args.database_dir.parent,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        r8_acceptance = build_acceptance_summary(args.database_dir, gates, verified_commit)
    except (OSError, subprocess.CalledProcessError, AcceptanceHistoryError) as exc:
        r8_acceptance = {
            "schema_version": "memory_atlas.r8_acceptance.v1",
            "status": "FAIL",
            "reason": str(exc),
        }
    r8_passed = r8_acceptance.get("status") == "PASS"
    total_output_chars = sum(len(str(gate.get("stdout_tail") or "")) + len(str(gate.get("stderr_tail") or "")) for gate in gates)
    payload = {
        "status": "PASS" if not failed and r8_passed else "FAIL",
        "command": "audit",
        "check": "final",
        "task_id": FINAL_AUDIT_TASK_ID,
        "acceptance_id": FINAL_AUDIT_ACCEPTANCE_ID,
        "contract_version": FINAL_AUDIT_CONTRACT_VERSION,
        "phase_status": FINAL_AUDIT_PHASE_STATUS if not failed and r8_passed else "r8_overall_acceptance_failed_pending_fix",
        "gates": gates,
        "gate_count": len(gates),
        "failed_gate_count": len(failed) + (0 if r8_passed else 1),
        "failed_gate_ids": [str(gate["gate_id"]) for gate in failed]
        + ([] if r8_passed else ["r8_58_requirement_reconciliation"]),
        "r8_acceptance": r8_acceptance,
        "four_line_coverage": r8_acceptance.get("four_line_coverage", []),
        "requirements": r8_acceptance.get("requirements", {}),
        "stage_pass_gates": r8_acceptance.get("stage_pass_gates", []),
        "high_token_auto_summary": False,
        "max_output_chars_per_gate": FINAL_AUDIT_OUTPUT_TAIL_CHARS * 2,
        "total_output_chars": total_output_chars,
        "writes_files": False,
        "writes_tracked_files": False,
        "raw_mutation": False,
        "remote_push": False,
        "github_main_upload": False,
        "phase_boundary": {
            "does_not_upload_github_main": True,
            "does_not_reinstall_app": True,
            "does_not_clean_local_computer": True,
            "stage_review_deferred_to": "S14 Review",
            "next_phase": "single final delivery" if not failed and r8_passed else "Fix R8 failing gate",
        },
        "中文说明": "S14 P2 final audit 已运行；失败时先按 failed_gate_ids 和各 gate 的中文解释修复。",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failed and r8_passed else 2


def audit_evidence_collection(
    items: list[dict[str, object]],
    collection_name: str,
    id_field: str,
    required_text_fields: tuple[str, ...],
) -> list[str]:
    bad_items = []
    for item in items:
        item_id = item.get(id_field)
        if not item.get("evidence_refs"):
            bad_items.append(f"{collection_name}:{item_id}:missing_evidence_refs")
        for field_name in required_text_fields:
            if not str(item.get(field_name) or "").strip():
                bad_items.append(f"{collection_name}:{item_id}:missing_{field_name}")
    return bad_items


def run_formula_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json"
    output_path = args.database_dir / "data/derived/economic_proxy/personal_economic_proxy.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    if not config_path.exists():
        bad_items.append("formula_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S07P1" or config.get("acceptance_id") != "ACC-MA-V12-S07P1":
            bad_items.append("formula_config:identity_mismatch")
        boundary = config.get("scope_boundary") or {}
        if not isinstance(boundary, dict) or boundary.get("external_economic_database_dependency") is not False:
            bad_items.append("formula_config:external_database_dependency_not_false")
        if not isinstance(boundary, dict) or boundary.get("precise_income_prediction") is not False:
            bad_items.append("formula_config:precise_income_prediction_not_false")
        parameters = config.get("parameters") if isinstance(config.get("parameters"), dict) else {}
        required_score_keys = {
            "time_saved_proxy",
            "reuse_value_proxy",
            "rework_cost_proxy",
            "opportunity_score_proxy",
            "skill_compounding_proxy",
            "automation_enhancement_ratio_proxy",
        }
        formulas = config.get("formulas") if isinstance(config.get("formulas"), list) else []
        score_keys = {str(item.get("score_key")) for item in formulas if isinstance(item, dict)}
        for key in sorted(required_score_keys - score_keys):
            bad_items.append(f"formula_config:missing_score_key:{key}")
        for item in formulas:
            if not isinstance(item, dict):
                bad_items.append("formula_config:invalid_formula_item")
                continue
            formula_id = item.get("formula_id")
            if not formula_id or not item.get("expression_zh") or not item.get("interpretation_zh"):
                bad_items.append(f"formula_config:{formula_id}:missing_expression_or_interpretation")
            for param_ref in item.get("parameter_refs") or []:
                if param_ref not in parameters:
                    bad_items.append(f"formula_config:{formula_id}:unknown_parameter:{param_ref}")
    if output_path.exists():
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S07P1" or output.get("acceptance_id") != "ACC-MA-V12-S07P1":
            bad_items.append("economic_proxy_output:identity_mismatch")
        external_database = output.get("external_economic_database")
        if not isinstance(external_database, dict) or external_database.get("current_dependency") is not False:
            bad_items.append("economic_proxy_output:external_database_dependency_not_false")
        boundary = output.get("phase_boundary") or {}
        if boundary.get("does_not_use_external_economic_database") is not True:
            bad_items.append("economic_proxy_output:external_database_boundary_missing")
        if boundary.get("does_not_claim_precise_income_prediction") is not True:
            bad_items.append("economic_proxy_output:precise_income_boundary_missing")
        for card in output.get("score_cards") or []:
            card_id = card.get("score_key")
            if not card.get("formula_id") or not card.get("formula_source"):
                bad_items.append(f"score_card:{card_id}:missing_formula_source")
            if not card.get("explanation_zh") or not card.get("formula_expression_zh"):
                bad_items.append(f"score_card:{card_id}:missing_chinese_explanation_or_expression")
            if not card.get("parameter_refs"):
                bad_items.append(f"score_card:{card_id}:missing_parameter_refs")
            if not card.get("evidence_refs"):
                bad_items.append(f"score_card:{card_id}:missing_evidence_refs")
            if int(card.get("score") or -1) < 0 or int(card.get("score") or -1) > 100:
                bad_items.append(f"score_card:{card_id}:score_out_of_range")
    else:
        bad_items.append("economic_proxy_output:missing")
    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "formulas",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "formula_config": "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json",
        "economic_proxy_output": "data/derived/economic_proxy/personal_economic_proxy.json" if output_path.exists() else "",
        "formula_count": len(config.get("formulas") or []) if isinstance(config.get("formulas"), list) else 0,
        "score_card_count": len(output.get("score_cards") or []) if isinstance(output.get("score_cards"), list) else 0,
        "external_economic_database_dependency": False,
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_visual_roi_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/参数与公式/information_roi.v1_2_s07_p2.json"
    visual_config_path = args.database_dir / "机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json"
    output_path = args.database_dir / "data/derived/information_roi/information_roi_gate.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    visual_config: dict[str, object] = {}
    if not config_path.exists():
        bad_items.append("information_roi_formula_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S07P2" or config.get("acceptance_id") != "ACC-MA-V12-S07P2":
            bad_items.append("information_roi_formula_config:identity_mismatch")
        boundary = config.get("scope_boundary") or {}
        if not isinstance(boundary, dict) or boundary.get("external_economic_database_dependency") is not False:
            bad_items.append("information_roi_formula_config:external_database_dependency_not_false")
        parameters = config.get("parameters") if isinstance(config.get("parameters"), dict) else {}
        formulas = config.get("formulas") if isinstance(config.get("formulas"), list) else []
        score_keys = {str(item.get("score_key")) for item in formulas if isinstance(item, dict)}
        for key in sorted({"information_roi_score", "visual_roi_gate"} - score_keys):
            bad_items.append(f"information_roi_formula_config:missing_score_key:{key}")
        for item in formulas:
            if not isinstance(item, dict):
                bad_items.append("information_roi_formula_config:invalid_formula_item")
                continue
            formula_id = item.get("formula_id")
            if not formula_id or not item.get("expression_zh") or not item.get("interpretation_zh"):
                bad_items.append(f"information_roi_formula_config:{formula_id}:missing_expression_or_interpretation")
            for param_ref in item.get("parameter_refs") or []:
                if param_ref not in parameters:
                    bad_items.append(f"information_roi_formula_config:{formula_id}:unknown_parameter:{param_ref}")
    if not visual_config_path.exists():
        bad_items.append("visual_roi_gate_config:missing")
    else:
        visual_config = json.loads(visual_config_path.read_text(encoding="utf-8"))
        if visual_config.get("task_id") != "MA-V12-S07P2" or visual_config.get("acceptance_id") != "ACC-MA-V12-S07P2":
            bad_items.append("visual_roi_gate_config:identity_mismatch")
        for item in visual_config.get("p0_visuals") or []:
            if not item.get("id") or not item.get("human_question") or not item.get("action"):
                bad_items.append(f"visual_roi_gate_config:{item.get('id')}:missing_human_question_or_action")
    if not output_path.exists():
        bad_items.append("information_roi_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S07P2" or output.get("acceptance_id") != "ACC-MA-V12-S07P2":
            bad_items.append("information_roi_output:identity_mismatch")
        boundary = output.get("phase_boundary") or {}
        if boundary.get("does_not_use_external_economic_database") is not True:
            bad_items.append("information_roi_output:external_database_boundary_missing")
        if boundary.get("does_not_claim_precise_income_prediction") is not True:
            bad_items.append("information_roi_output:precise_income_boundary_missing")
        if boundary.get("does_not_generate_what_if_ui") is not True:
            bad_items.append("information_roi_output:what_if_boundary_missing")
        roi_items = output.get("roi_items") if isinstance(output.get("roi_items"), list) else []
        item_types = {item.get("item_type") for item in roi_items if isinstance(item, dict)}
        for required_type in {"insight", "card", "chart"} - item_types:
            bad_items.append(f"information_roi_output:missing_item_type:{required_type}")
        for item in roi_items:
            item_id = item.get("item_id")
            if not item.get("formula_id") or not item.get("formula_source"):
                bad_items.append(f"roi_item:{item_id}:missing_formula_source")
            if not item.get("decision_summary_zh"):
                bad_items.append(f"roi_item:{item_id}:missing_decision_summary")
            if not item.get("evidence_refs"):
                bad_items.append(f"roi_item:{item_id}:missing_evidence_refs")
            if int(item.get("information_roi_score") or -1) < 0 or int(item.get("information_roi_score") or -1) > 100:
                bad_items.append(f"roi_item:{item_id}:score_out_of_range")
            if item.get("item_type") == "chart" and item.get("p0_candidate") is True:
                if not item.get("human_question") or not item.get("action_zh") or item.get("visual_roi_gate_pass") is not True:
                    bad_items.append(f"roi_item:{item_id}:invalid_p0_visual_gate")
        gate = output.get("visual_roi_gate") if isinstance(output.get("visual_roi_gate"), dict) else {}
        if gate.get("failed_p0_count") != 0:
            bad_items.append("visual_roi_gate:failed_p0_count_not_zero")
        if not gate.get("excluded_from_p0"):
            bad_items.append("visual_roi_gate:missing_excluded_from_p0_examples")
    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "visual-roi",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "formula_config": "机器治理/参数与公式/information_roi.v1_2_s07_p2.json",
        "visual_gate_config": "机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json",
        "information_roi_output": "data/derived/information_roi/information_roi_gate.json" if output_path.exists() else "",
        "roi_item_count": len(output.get("roi_items") or []) if isinstance(output.get("roi_items"), list) else 0,
        "p0_visual_count": len((output.get("visual_roi_gate") or {}).get("p0_visuals") or []) if isinstance(output.get("visual_roi_gate"), dict) else 0,
        "failed_p0_count": (output.get("visual_roi_gate") or {}).get("failed_p0_count") if isinstance(output.get("visual_roi_gate"), dict) else None,
        "external_economic_database_dependency": False,
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_formula_what_if_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json"
    output_path = args.database_dir / "data/derived/economic_proxy/formula_what_if_preview.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    if not config_path.exists():
        bad_items.append("formula_what_if_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S07P3" or config.get("acceptance_id") != "ACC-MA-V12-S07P3":
            bad_items.append("formula_what_if_config:identity_mismatch")
        if config.get("active_config_write") is not False:
            bad_items.append("formula_what_if_config:active_config_write_not_false")
        if config.get("proposal_required_before_apply") is not True:
            bad_items.append("formula_what_if_config:proposal_required_before_apply_not_true")
        boundary = config.get("scope_boundary") or {}
        if not isinstance(boundary, dict) or boundary.get("external_economic_database_dependency") is not False:
            bad_items.append("formula_what_if_config:external_database_dependency_not_false")
        if not isinstance(boundary, dict) or boundary.get("precise_income_prediction") is not False:
            bad_items.append("formula_what_if_config:precise_income_prediction_not_false")
        if not isinstance(boundary, dict) or boundary.get("financial_advice") is not False:
            bad_items.append("formula_what_if_config:financial_advice_not_false")
        params = config.get("parameters") if isinstance(config.get("parameters"), dict) else {}
        weights = (params.get("default_weights") or {}) if isinstance(params.get("default_weights"), dict) else {}
        bounds = (params.get("adjustable_weight_bounds") or {}) if isinstance(params.get("adjustable_weight_bounds"), dict) else {}
        for weight_key in ["time_saved_weight", "reuse_value_weight", "skill_compounding_weight", "rework_cost_weight", "low_value_loop_penalty_weight"]:
            if weight_key not in weights or weight_key not in bounds:
                bad_items.append(f"formula_what_if_config:missing_adjustable_weight:{weight_key}")
        formulas = config.get("formulas") if isinstance(config.get("formulas"), list) else []
        score_keys = {str(item.get("score_key")) for item in formulas if isinstance(item, dict)}
        for key in sorted({"formula_what_if_proxy_score", "what_if_parameter_proposal"} - score_keys):
            bad_items.append(f"formula_what_if_config:missing_score_key:{key}")
    if not output_path.exists():
        bad_items.append("formula_what_if_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S07P3" or output.get("acceptance_id") != "ACC-MA-V12-S07P3":
            bad_items.append("formula_what_if_output:identity_mismatch")
        if output.get("status") != "phase_s07_p3_formula_what_if_completed_pending_s07_review":
            bad_items.append("formula_what_if_output:status_mismatch")
        boundary = output.get("phase_boundary") or {}
        if boundary.get("does_not_use_external_economic_database") is not True:
            bad_items.append("formula_what_if_output:external_database_boundary_missing")
        if boundary.get("does_not_claim_precise_income_prediction") is not True:
            bad_items.append("formula_what_if_output:precise_income_boundary_missing")
        if boundary.get("does_not_provide_financial_advice") is not True:
            bad_items.append("formula_what_if_output:financial_advice_boundary_missing")
        if boundary.get("does_not_mutate_active_formula_config") is not True:
            bad_items.append("formula_what_if_output:active_config_mutation_boundary_missing")
        if boundary.get("requires_proposal_before_apply") is not True:
            bad_items.append("formula_what_if_output:proposal_gate_missing")
        scenarios = output.get("scenarios") if isinstance(output.get("scenarios"), list) else []
        if len(scenarios) < 4:
            bad_items.append("formula_what_if_output:scenario_count_too_low")
        covered_weights: set[str] = set()
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            weights = scenario.get("adjustable_weights") if isinstance(scenario.get("adjustable_weights"), dict) else {}
            covered_weights.update(weights)
            proposal = scenario.get("parameter_change_proposal") if isinstance(scenario.get("parameter_change_proposal"), dict) else {}
            if proposal.get("active_config_write") is not False or proposal.get("proposal_required_before_apply") is not True:
                bad_items.append(f"formula_what_if_output:{scenario_id}:invalid_proposal_gate")
            if not scenario.get("description_zh") or not scenario.get("formula_id") or not scenario.get("formula_source"):
                bad_items.append(f"formula_what_if_output:{scenario_id}:missing_description_or_formula")
            if int(scenario.get("weighted_proxy_score") or -1) < 0 or int(scenario.get("weighted_proxy_score") or -1) > 100:
                bad_items.append(f"formula_what_if_output:{scenario_id}:score_out_of_range")
        for weight_key in ["time_saved_weight", "reuse_value_weight", "skill_compounding_weight"]:
            if weight_key not in covered_weights:
                bad_items.append(f"formula_what_if_output:missing_required_weight:{weight_key}")
    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "formula-what-if",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "formula_what_if_config": "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
        "formula_what_if_output": "data/derived/economic_proxy/formula_what_if_preview.json" if output_path.exists() else "",
        "scenario_count": len(output.get("scenarios") or []) if isinstance(output.get("scenarios"), list) else 0,
        "active_config_write": False,
        "proposal_required_before_apply": True,
        "external_economic_database_dependency": False,
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_agent_collaboration_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json"
    output_path = args.database_dir / "data/derived/agent_collaboration/agent_collaboration_quality_report.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    required_metrics = {
        "planning_clarity",
        "execution_clarity",
        "review_burden",
        "rework_count",
        "scope_clarity",
        "testability",
        "rollbackability",
    }
    if not config_path.exists():
        bad_items.append("agent_collaboration_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S08P1" or config.get("acceptance_id") != "ACC-MA-V12-S08P1":
            bad_items.append("agent_collaboration_config:identity_mismatch")
        boundary = config.get("scope_boundary") or {}
        if not isinstance(boundary, dict) or boundary.get("raw_mutation") is not False:
            bad_items.append("agent_collaboration_config:raw_mutation_not_false")
        if not isinstance(boundary, dict) or boundary.get("multi_agent_system_implementation") is not False:
            bad_items.append("agent_collaboration_config:multi_agent_system_not_false")
        if not isinstance(boundary, dict) or boundary.get("complex_delegation_contract_ui") is not False:
            bad_items.append("agent_collaboration_config:complex_ui_not_false")
        metrics = config.get("metrics") if isinstance(config.get("metrics"), list) else []
        metric_keys = {str(item.get("metric_key")) for item in metrics if isinstance(item, dict)}
        for key in sorted(required_metrics - metric_keys):
            bad_items.append(f"agent_collaboration_config:missing_metric:{key}")
        params = config.get("parameters") if isinstance(config.get("parameters"), dict) else {}
        for item in metrics:
            if not isinstance(item, dict):
                bad_items.append("agent_collaboration_config:invalid_metric_item")
                continue
            metric_key = item.get("metric_key")
            if not item.get("formula_id") or not item.get("expression_zh") or not item.get("interpretation_zh"):
                bad_items.append(f"agent_collaboration_config:{metric_key}:missing_formula")
            for param_ref in item.get("parameter_refs") or []:
                if param_ref not in params:
                    bad_items.append(f"agent_collaboration_config:{metric_key}:unknown_parameter:{param_ref}")
    if not output_path.exists():
        bad_items.append("agent_collaboration_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S08P1" or output.get("acceptance_id") != "ACC-MA-V12-S08P1":
            bad_items.append("agent_collaboration_output:identity_mismatch")
        if output.get("status") != "phase_s08_p1_collaboration_metrics_completed_pending_s08_p2":
            bad_items.append("agent_collaboration_output:status_mismatch")
        boundary = output.get("phase_boundary") or {}
        if boundary.get("does_not_create_multi_agent_system") is not True:
            bad_items.append("agent_collaboration_output:multi_agent_boundary_missing")
        if boundary.get("does_not_implement_complex_delegation_contract_ui") is not True:
            bad_items.append("agent_collaboration_output:complex_ui_boundary_missing")
        if boundary.get("does_not_modify_raw") is not True:
            bad_items.append("agent_collaboration_output:raw_boundary_missing")
        if boundary.get("next_phase") != "S08 P2":
            bad_items.append("agent_collaboration_output:next_phase_not_s08p2")
        overall_metrics = output.get("overall_metrics") if isinstance(output.get("overall_metrics"), list) else []
        metric_keys = {str(item.get("metric_key")) for item in overall_metrics if isinstance(item, dict)}
        for key in sorted(required_metrics - metric_keys):
            bad_items.append(f"agent_collaboration_output:missing_metric:{key}")
        for item in overall_metrics:
            metric_key = item.get("metric_key")
            score = int(item.get("score") if item.get("score") is not None else -1)
            if score < 0 or score > 100:
                bad_items.append(f"agent_collaboration_output:{metric_key}:score_out_of_range")
            if not item.get("formula_id") or not item.get("formula_source"):
                bad_items.append(f"agent_collaboration_output:{metric_key}:missing_formula_source")
            if not item.get("explanation_zh"):
                bad_items.append(f"agent_collaboration_output:{metric_key}:missing_chinese_explanation")
            if not item.get("evidence_refs"):
                bad_items.append(f"agent_collaboration_output:{metric_key}:missing_evidence_refs")
        source_summaries = output.get("source_summaries") if isinstance(output.get("source_summaries"), list) else []
        source_types = {item.get("source_type") for item in source_summaries if isinstance(item, dict)}
        for source_type in {"chatgpt", "codex", "other_agent"} - source_types:
            bad_items.append(f"agent_collaboration_output:missing_source_type:{source_type}")
        summary = output.get("chinese_summary") if isinstance(output.get("chinese_summary"), dict) else {}
        for key in [
            "summary_zh",
            "human_responsibility_zh",
            "agent_responsibility_zh",
            "rework_sources_zh",
            "agent_fit_zh",
            "human_judgment_zh",
        ]:
            if not summary.get(key):
                bad_items.append(f"agent_collaboration_output:missing_{key}")
    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "agent-collaboration",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "metrics_config": "机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json",
        "agent_collaboration_output": "data/derived/agent_collaboration/agent_collaboration_quality_report.json" if output_path.exists() else "",
        "metric_count": len(output.get("overall_metrics") or []) if isinstance(output.get("overall_metrics"), list) else 0,
        "source_summary_count": len(output.get("source_summaries") or []) if isinstance(output.get("source_summaries"), list) else 0,
        "complex_delegation_contract_ui": False,
        "multi_agent_system_implementation": False,
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_agent_authorization_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json"
    output_path = args.database_dir / "data/derived/agent_collaboration/agent_authorization_boundary_report.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    required_states = {
        "draft",
        "pending_human_review",
        "approved_by_human",
        "applying",
        "applied",
        "validated",
        "committed",
        "failed_validation",
        "rollback_or_needs_revision",
    }
    required_fields = {
        "proposal_id",
        "target_type",
        "target_files",
        "human_reason_zh",
        "evidence_refs",
        "before_after_diff",
        "risk_level",
        "rollback_plan",
        "expires_at",
        "action_half_life",
        "approval",
        "validation_commands",
    }
    forbidden_targets = {"raw_archive", "public_raw", "credentials"}
    forbidden_prefixes = {"data/public_raw/", "data/raw/"}

    if not config_path.exists():
        bad_items.append("agent_authorization_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S08P2" or config.get("acceptance_id") != "ACC-MA-V12-S08P2":
            bad_items.append("agent_authorization_config:identity_mismatch")
        if config.get("boundary_mode") != "machine_config_and_output_checks":
            bad_items.append("agent_authorization_config:boundary_mode_not_machine_checks")
        ui = config.get("delegation_contract_ui") if isinstance(config.get("delegation_contract_ui"), dict) else {}
        if ui.get("complex_ui_required") is not False:
            bad_items.append("agent_authorization_config:complex_ui_required")
        state_machine = config.get("proposal_state_machine") if isinstance(config.get("proposal_state_machine"), dict) else {}
        states = {str(item) for item in state_machine.get("states") or []}
        for state in sorted(required_states - states):
            bad_items.append(f"agent_authorization_config:missing_state:{state}")
        if state_machine.get("human_approval_required") is not True:
            bad_items.append("agent_authorization_config:human_approval_not_required")
        if state_machine.get("current_phase_executes_apply") is not False:
            bad_items.append("agent_authorization_config:current_phase_executes_apply")
        if state_machine.get("apply_execution_deferred_to") != "S13":
            bad_items.append("agent_authorization_config:apply_not_deferred_to_s13")
        field_set = set(config.get("proposal_required_fields") or [])
        for field in sorted(required_fields - field_set):
            bad_items.append(f"agent_authorization_config:missing_proposal_field:{field}")
        target_set = set(config.get("apply_forbidden_targets") or [])
        for target in sorted(forbidden_targets - target_set):
            bad_items.append(f"agent_authorization_config:missing_forbidden_target:{target}")
        prefix_set = set(config.get("forbidden_path_prefixes") or [])
        for prefix in sorted(forbidden_prefixes - prefix_set):
            bad_items.append(f"agent_authorization_config:missing_forbidden_prefix:{prefix}")
        boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
        if boundary.get("raw_mutation") is not False:
            bad_items.append("agent_authorization_config:raw_mutation_not_false")
        if boundary.get("proposal_apply_execution") is not False:
            bad_items.append("agent_authorization_config:proposal_apply_execution_not_false")
        if boundary.get("authorization_boundary_defined_as_machine_checks") is not True:
            bad_items.append("agent_authorization_config:machine_checks_boundary_missing")
        if boundary.get("stage_flight_recorder") != "deferred_to_s08_p3":
            bad_items.append("agent_authorization_config:stage_flight_not_deferred")

    if not output_path.exists():
        bad_items.append("agent_authorization_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S08P2" or output.get("acceptance_id") != "ACC-MA-V12-S08P2":
            bad_items.append("agent_authorization_output:identity_mismatch")
        if output.get("status") != "phase_s08_p2_authorization_boundary_completed_pending_s08_p3":
            bad_items.append("agent_authorization_output:status_mismatch")
        summary = output.get("authorization_boundary_summary") if isinstance(output.get("authorization_boundary_summary"), dict) else {}
        for key in ["summary_zh", "human_role_zh", "agent_role_zh", "raw_boundary_zh", "future_apply_zh"]:
            if not summary.get(key):
                bad_items.append(f"agent_authorization_output:missing_{key}")
        checks = output.get("machine_output_checks") if isinstance(output.get("machine_output_checks"), list) else []
        check_ids = {item.get("check_id") for item in checks if isinstance(item, dict)}
        for check_id in {"S08P2-CHECK-001", "S08P2-CHECK-002", "S08P2-CHECK-003", "S08P2-CHECK-004"} - check_ids:
            bad_items.append(f"agent_authorization_output:missing_check:{check_id}")
        for item in checks:
            if not isinstance(item, dict):
                bad_items.append("agent_authorization_output:invalid_check_item")
                continue
            check_id = item.get("check_id")
            if item.get("status") != "PASS":
                bad_items.append(f"agent_authorization_output:{check_id}:not_pass")
            if not item.get("explanation_zh"):
                bad_items.append(f"agent_authorization_output:{check_id}:missing_chinese_explanation")
            if not item.get("evidence_refs"):
                bad_items.append(f"agent_authorization_output:{check_id}:missing_evidence_refs")
        proposal_contract = output.get("proposal_contract") if isinstance(output.get("proposal_contract"), dict) else {}
        output_field_set = set(proposal_contract.get("required_fields") or [])
        for field in sorted(required_fields - output_field_set):
            bad_items.append(f"agent_authorization_output:missing_contract_field:{field}")
        if set(proposal_contract.get("apply_forbidden_targets") or []) < forbidden_targets:
            bad_items.append("agent_authorization_output:forbidden_targets_incomplete")
        boundary = output.get("phase_boundary") if isinstance(output.get("phase_boundary"), dict) else {}
        if boundary.get("authorization_boundary_defined_as_machine_checks") is not True:
            bad_items.append("agent_authorization_output:machine_checks_boundary_missing")
        if boundary.get("does_not_modify_raw") is not True:
            bad_items.append("agent_authorization_output:raw_boundary_missing")
        if boundary.get("does_not_apply_proposals") is not True:
            bad_items.append("agent_authorization_output:apply_boundary_missing")
        if boundary.get("requires_human_approval_before_apply") is not True:
            bad_items.append("agent_authorization_output:human_approval_boundary_missing")
        if boundary.get("raw_is_never_apply_target") is not True:
            bad_items.append("agent_authorization_output:raw_target_boundary_missing")
        if boundary.get("does_not_implement_complex_delegation_contract_ui") is not True:
            bad_items.append("agent_authorization_output:complex_ui_boundary_missing")
        if boundary.get("does_not_create_multi_agent_system") is not True:
            bad_items.append("agent_authorization_output:multi_agent_boundary_missing")
        if boundary.get("does_not_generate_stage_flight_recorder") is not True:
            bad_items.append("agent_authorization_output:stage_flight_boundary_missing")
        if boundary.get("next_phase") != "S08 P3":
            bad_items.append("agent_authorization_output:next_phase_not_s08p3")

    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "agent-authorization",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "authorization_config": "机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json",
        "authorization_output": "data/derived/agent_collaboration/agent_authorization_boundary_report.json" if output_path.exists() else "",
        "machine_output_check_count": len(output.get("machine_output_checks") or []) if isinstance(output.get("machine_output_checks"), list) else 0,
        "human_approval_required": True,
        "raw_apply_target_allowed": False,
        "proposal_apply_execution": False,
        "complex_delegation_contract_ui": False,
        "multi_agent_system_implementation": False,
        "stage_flight_recorder": "deferred_to_s08_p3",
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_stage_flight_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json"
    output_path = args.database_dir / "data/derived/agent_collaboration/stage_flight_recorder.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    required_field_ids = {
        "stage_id",
        "phase_id",
        "task_id",
        "acceptance_id",
        "status",
        "summary_zh",
        "evidence_refs",
        "validation_refs",
        "boundary_flags",
        "next_gate",
    }
    required_phases = {"S08 P1", "S08 P2", "S08 P3"}
    if not config_path.exists():
        bad_items.append("stage_flight_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S08P3" or config.get("acceptance_id") != "ACC-MA-V12-S08P3":
            bad_items.append("stage_flight_config:identity_mismatch")
        if config.get("recorder_mode") != "lightweight_run_evidence_fields":
            bad_items.append("stage_flight_config:not_lightweight_mode")
        field_policy = config.get("field_policy") if isinstance(config.get("field_policy"), dict) else {}
        max_fields = int(field_policy.get("max_required_fields") or 0)
        fields = config.get("required_fields") if isinstance(config.get("required_fields"), list) else []
        field_ids = {item.get("field_id") for item in fields if isinstance(item, dict)}
        for field_id in sorted(required_field_ids - field_ids):
            bad_items.append(f"stage_flight_config:missing_field:{field_id}")
        if not fields or len(fields) > max_fields or max_fields > 12:
            bad_items.append("stage_flight_config:field_count_not_lightweight")
        for key in ["no_transcript_payloads", "no_raw_content", "no_bulky_human_docs", "development_record_summary_only"]:
            if field_policy.get(key) is not True:
                bad_items.append(f"stage_flight_config:field_policy_not_true:{key}")
        boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
        for key in [
            "raw_mutation",
            "github_main_upload",
            "complex_delegation_contract_ui",
            "multi_agent_system_implementation",
            "bulky_human_documentation",
            "human_readable_page_required",
        ]:
            if boundary.get(key) is not False:
                bad_items.append(f"stage_flight_config:boundary_not_false:{key}")
        if boundary.get("development_record_summary_only") is not True:
            bad_items.append("stage_flight_config:development_record_summary_only_missing")
        if boundary.get("next_phase") != "S08 Review":
            bad_items.append("stage_flight_config:next_phase_not_s08_review")

    if not output_path.exists():
        bad_items.append("stage_flight_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S08P3" or output.get("acceptance_id") != "ACC-MA-V12-S08P3":
            bad_items.append("stage_flight_output:identity_mismatch")
        if output.get("status") != "phase_s08_p3_stage_flight_recorder_completed_pending_s08_review":
            bad_items.append("stage_flight_output:status_mismatch")
        if output.get("recorder_mode") != "lightweight_run_evidence_fields":
            bad_items.append("stage_flight_output:not_lightweight_mode")
        fields = output.get("required_fields") if isinstance(output.get("required_fields"), list) else []
        if not fields or len(fields) > 12:
            bad_items.append("stage_flight_output:field_count_not_lightweight")
        field_ids = {item.get("field_id") for item in fields if isinstance(item, dict)}
        for field_id in sorted(required_field_ids - field_ids):
            bad_items.append(f"stage_flight_output:missing_field:{field_id}")
        phase_records = output.get("phase_records") if isinstance(output.get("phase_records"), list) else []
        phase_ids = {item.get("phase_id") for item in phase_records if isinstance(item, dict)}
        for phase_id in sorted(required_phases - phase_ids):
            bad_items.append(f"stage_flight_output:missing_phase:{phase_id}")
        for item in phase_records:
            if not isinstance(item, dict):
                bad_items.append("stage_flight_output:invalid_phase_record")
                continue
            phase_id = item.get("phase_id")
            if not item.get("summary_zh"):
                bad_items.append(f"stage_flight_output:{phase_id}:missing_summary")
            if not item.get("evidence_refs"):
                bad_items.append(f"stage_flight_output:{phase_id}:missing_evidence_refs")
            if not item.get("validation_refs"):
                bad_items.append(f"stage_flight_output:{phase_id}:missing_validation_refs")
            flags = item.get("boundary_flags") if isinstance(item.get("boundary_flags"), dict) else {}
            for key in ["raw_mutation", "github_main_upload", "complex_delegation_contract_ui", "multi_agent_system_implementation"]:
                if flags.get(key) is not False:
                    bad_items.append(f"stage_flight_output:{phase_id}:boundary_not_false:{key}")
        checks = output.get("machine_output_checks") if isinstance(output.get("machine_output_checks"), list) else []
        check_ids = {item.get("check_id") for item in checks if isinstance(item, dict)}
        for check_id in {"S08P3-CHECK-001", "S08P3-CHECK-002", "S08P3-CHECK-003", "S08P3-CHECK-004"} - check_ids:
            bad_items.append(f"stage_flight_output:missing_check:{check_id}")
        for item in checks:
            if not isinstance(item, dict):
                bad_items.append("stage_flight_output:invalid_check_item")
                continue
            check_id = item.get("check_id")
            if item.get("status") != "PASS":
                bad_items.append(f"stage_flight_output:{check_id}:not_pass")
            if not item.get("explanation_zh"):
                bad_items.append(f"stage_flight_output:{check_id}:missing_chinese_explanation")
            if not item.get("evidence_refs"):
                bad_items.append(f"stage_flight_output:{check_id}:missing_evidence_refs")
        boundary = output.get("phase_boundary") if isinstance(output.get("phase_boundary"), dict) else {}
        if boundary.get("lightweight_stage_flight_recorder") is not True:
            bad_items.append("stage_flight_output:lightweight_boundary_missing")
        if boundary.get("does_not_include_raw_or_transcript_payloads") is not True:
            bad_items.append("stage_flight_output:raw_payload_boundary_missing")
        if boundary.get("does_not_generate_bulky_human_docs") is not True:
            bad_items.append("stage_flight_output:bulky_human_docs_boundary_missing")
        if boundary.get("records_necessary_info_in_development_records") is not True:
            bad_items.append("stage_flight_output:development_record_boundary_missing")
        if boundary.get("does_not_modify_raw") is not True:
            bad_items.append("stage_flight_output:raw_mutation_boundary_missing")
        if boundary.get("does_not_upload_github_main") is not True:
            bad_items.append("stage_flight_output:github_upload_boundary_missing")
        if boundary.get("next_phase") != "S08 Review":
            bad_items.append("stage_flight_output:next_phase_not_s08_review")

    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "stage-flight",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "stage_flight_config": "机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json",
        "stage_flight_output": "data/derived/agent_collaboration/stage_flight_recorder.json" if output_path.exists() else "",
        "required_field_count": len(output.get("required_fields") or []) if isinstance(output.get("required_fields"), list) else 0,
        "phase_record_count": len(output.get("phase_records") or []) if isinstance(output.get("phase_records"), list) else 0,
        "machine_output_check_count": len(output.get("machine_output_checks") or []) if isinstance(output.get("machine_output_checks"), list) else 0,
        "bulky_human_documentation": False,
        "raw_mutation": False,
        "github_main_upload": False,
        "next_phase": "S08 Review",
        "bad_items": bad_items,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_latent_safety_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json"
    output_path = args.database_dir / "data/derived/behavior_intelligence/latent_signals.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    required_fields = {
        "claim_zh",
        "supporting_evidence_refs",
        "contradicting_evidence_refs",
        "alternative_explanation_zh",
        "confidence",
        "evidence_strength_badge",
        "next_validation_zh",
    }
    blocked_terms = {"心理诊断", "人格诊断", "人格标签", "抑郁", "焦虑症"}

    if not config_path.exists():
        bad_items.append("latent_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S09P1" or config.get("acceptance_id") != "ACC-MA-V12-S09P1":
            bad_items.append("latent_config:identity_mismatch")
        configured_fields = set(config.get("required_signal_fields") or [])
        for field in sorted(required_fields - configured_fields):
            bad_items.append(f"latent_config:missing_required_field:{field}")
        badges = {item.get("badge") for item in config.get("evidence_strength_badges") or [] if isinstance(item, dict)}
        for badge in {"A", "B", "C", "D"} - badges:
            bad_items.append(f"latent_config:missing_badge:{badge}")
        boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
        if boundary.get("raw_mutation") is not False:
            bad_items.append("latent_config:raw_mutation_not_false")
        if boundary.get("psychological_diagnosis") is not False:
            bad_items.append("latent_config:psychological_boundary_not_false")
        if boundary.get("personality_label") is not False:
            bad_items.append("latent_config:personality_boundary_not_false")
        if boundary.get("self_iteration_suggestions") != "deferred_to_s09_p2":
            bad_items.append("latent_config:self_iteration_not_deferred")
        if boundary.get("decision_debt_ledger") != "deferred_to_s09_p3":
            bad_items.append("latent_config:decision_debt_not_deferred")

    psychological_diagnosis_output = False
    personality_label_output = False
    has_contradicting_evidence = False
    if not output_path.exists():
        bad_items.append("latent_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S09P1" or output.get("acceptance_id") != "ACC-MA-V12-S09P1":
            bad_items.append("latent_output:identity_mismatch")
        if output.get("status") != "phase_s09_p1_latent_signals_completed_pending_s09_p2":
            bad_items.append("latent_output:status_mismatch")
        signals = output.get("latent_signals") if isinstance(output.get("latent_signals"), list) else []
        if len(signals) < 4:
            bad_items.append("latent_output:signal_count_too_low")
        confidence_policy = config.get("confidence_policy") if isinstance(config.get("confidence_policy"), dict) else {}
        max_confidence = float(confidence_policy.get("max_confidence") or 0.85)
        high_confidence_badges = set(confidence_policy.get("high_confidence_requires_badge") or ["A", "B"])
        for signal in signals:
            if not isinstance(signal, dict):
                bad_items.append("latent_output:invalid_signal_item")
                continue
            signal_id = signal.get("signal_id")
            for field in sorted(required_fields):
                if signal.get(field) in (None, "", []):
                    bad_items.append(f"latent_output:{signal_id}:missing_{field}")
            if signal.get("evidence_strength_badge") not in {"A", "B", "C", "D"}:
                bad_items.append(f"latent_output:{signal_id}:invalid_badge")
            confidence = float(signal.get("confidence") or 0)
            if confidence < 0 or confidence > max_confidence:
                bad_items.append(f"latent_output:{signal_id}:confidence_out_of_range")
            if confidence >= 0.75 and signal.get("evidence_strength_badge") not in high_confidence_badges:
                bad_items.append(f"latent_output:{signal_id}:high_confidence_without_strong_evidence")
            if signal.get("supporting_evidence_refs") and signal.get("contradicting_evidence_refs"):
                has_contradicting_evidence = True
            else:
                bad_items.append(f"latent_output:{signal_id}:missing_two_sided_evidence")
            text = " ".join(str(signal.get(field) or "") for field in ["claim_zh", "claim_type", "alternative_explanation_zh", "next_validation_zh"])
            if any(term in text for term in blocked_terms):
                bad_items.append(f"latent_output:{signal_id}:blocked_term")
            if signal.get("not_psychological_diagnosis") is not True:
                bad_items.append(f"latent_output:{signal_id}:psychological_boundary_missing")
                psychological_diagnosis_output = True
            if signal.get("not_personality_label") is not True:
                bad_items.append(f"latent_output:{signal_id}:personality_boundary_missing")
                personality_label_output = True
            if signal.get("falsifiable") is not True:
                bad_items.append(f"latent_output:{signal_id}:not_falsifiable")
        boundary = output.get("phase_boundary") if isinstance(output.get("phase_boundary"), dict) else {}
        if boundary.get("does_not_output_psychological_diagnosis") is not True:
            bad_items.append("latent_output:psychological_boundary_missing")
            psychological_diagnosis_output = True
        if boundary.get("does_not_output_personality_label") is not True:
            bad_items.append("latent_output:personality_boundary_missing")
            personality_label_output = True
        if boundary.get("does_not_create_self_iteration_suggestions") is not True:
            bad_items.append("latent_output:self_iteration_not_deferred")
        if boundary.get("does_not_create_decision_debt_ledger") is not True:
            bad_items.append("latent_output:decision_debt_not_deferred")
        if boundary.get("next_phase") != "S09 P2":
            bad_items.append("latent_output:next_phase_not_s09p2")

    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "latent-safety",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "latent_signal_config": "机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json",
        "latent_signal_output": "data/derived/behavior_intelligence/latent_signals.json" if output_path.exists() else "",
        "signal_count": len(output.get("latent_signals") or []) if isinstance(output.get("latent_signals"), list) else 0,
        "psychological_diagnosis_output": psychological_diagnosis_output,
        "personality_label_output": personality_label_output,
        "has_contradicting_evidence": has_contradicting_evidence,
        "raw_mutation": False,
        "bad_items": bad_items,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_self_iteration_safety_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json"
    output_path = args.database_dir / "data/derived/behavior_intelligence/self_iteration_suggestions.json"
    bad_items: list[str] = []
    config: dict[str, object] = {}
    output: dict[str, object] = {}
    required_fields = {
        "suggestion_id",
        "target_type",
        "target_files",
        "rationale_zh",
        "expected_change_zh",
        "evidence_refs",
        "proposal",
        "action_half_life_days",
    }
    required_targets = {"memory", "config", "AGENTS", "style", "personalization"}
    blocked_targets = {"data/public_raw/", "data/raw/", "credentials", "cookies", "tokens"}

    if not config_path.exists():
        bad_items.append("self_iteration_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S09P2" or config.get("acceptance_id") != "ACC-MA-V12-S09P2":
            bad_items.append("self_iteration_config:identity_mismatch")
        configured_fields = set(config.get("required_suggestion_fields") or [])
        for field in sorted(required_fields - configured_fields):
            bad_items.append(f"self_iteration_config:missing_required_field:{field}")
        target_types = {item.get("target_type") for item in config.get("suggestion_targets") or [] if isinstance(item, dict)}
        for target in sorted(required_targets - target_types):
            bad_items.append(f"self_iteration_config:missing_target:{target}")
        expiry = config.get("proposal_expiry") if isinstance(config.get("proposal_expiry"), dict) else {}
        for field in ["warn_after_days", "stale_after_days", "archive_after_days", "expires_after_days"]:
            if int(expiry.get(field) or 0) <= 0:
                bad_items.append(f"self_iteration_config:invalid_expiry:{field}")
        state = config.get("proposal_state") if isinstance(config.get("proposal_state"), dict) else {}
        if state.get("apply_execution_allowed") is not False:
            bad_items.append("self_iteration_config:apply_allowed")
        if state.get("raw_apply_target_allowed") is not False:
            bad_items.append("self_iteration_config:raw_apply_allowed")
        boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
        if boundary.get("raw_mutation") is not False:
            bad_items.append("self_iteration_config:raw_mutation_not_false")
        if boundary.get("proposal_apply_execution") is not False:
            bad_items.append("self_iteration_config:proposal_apply_not_false")
        if boundary.get("decision_debt_ledger") != "deferred_to_s09_p3":
            bad_items.append("self_iteration_config:decision_debt_not_deferred")

    all_proposals_have_expiry = False
    all_suggestions_have_action_half_life = False
    proposal_apply_execution = False
    decision_debt_ledger_created = False
    raw_mutation = False
    if not output_path.exists():
        bad_items.append("self_iteration_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S09P2" or output.get("acceptance_id") != "ACC-MA-V12-S09P2":
            bad_items.append("self_iteration_output:identity_mismatch")
        if output.get("status") != "phase_s09_p2_self_iteration_completed_pending_s09_p3":
            bad_items.append("self_iteration_output:status_mismatch")
        suggestions = output.get("self_iteration_suggestions") if isinstance(output.get("self_iteration_suggestions"), list) else []
        if len(suggestions) < 5:
            bad_items.append("self_iteration_output:suggestion_count_too_low")
        seen_targets = {item.get("target_type") for item in suggestions if isinstance(item, dict)}
        for target in sorted(required_targets - seen_targets):
            bad_items.append(f"self_iteration_output:missing_target:{target}")
        expiry_ok = []
        half_life_ok = []
        for item in suggestions:
            if not isinstance(item, dict):
                bad_items.append("self_iteration_output:invalid_suggestion_item")
                continue
            suggestion_id = item.get("suggestion_id")
            for field in sorted(required_fields):
                if item.get(field) in (None, "", []):
                    bad_items.append(f"self_iteration_output:{suggestion_id}:missing_{field}")
            if int(item.get("action_half_life_days") or 0) <= 0:
                bad_items.append(f"self_iteration_output:{suggestion_id}:invalid_action_half_life")
                half_life_ok.append(False)
            else:
                half_life_ok.append(True)
            if item.get("not_pressure_list") is not True:
                bad_items.append(f"self_iteration_output:{suggestion_id}:pressure_list_boundary_missing")
            if item.get("not_applied") is not True:
                bad_items.append(f"self_iteration_output:{suggestion_id}:applied_in_current_phase")
                proposal_apply_execution = True
            target_files = [str(file) for file in item.get("target_files") or []]
            if any(blocked in file for blocked in blocked_targets for file in target_files):
                bad_items.append(f"self_iteration_output:{suggestion_id}:blocked_target")
                raw_mutation = True
            proposal = item.get("proposal") if isinstance(item.get("proposal"), dict) else {}
            if not proposal.get("expires_at"):
                bad_items.append(f"self_iteration_output:{suggestion_id}:proposal_missing_expiry")
                expiry_ok.append(False)
            else:
                expiry_ok.append(True)
            if proposal.get("state") != "pending_human_review":
                bad_items.append(f"self_iteration_output:{suggestion_id}:proposal_state_not_pending_human_review")
            if proposal.get("not_permanent_pending") is not True:
                bad_items.append(f"self_iteration_output:{suggestion_id}:proposal_permanent_pending")
            if proposal.get("apply_execution_allowed") is not False:
                bad_items.append(f"self_iteration_output:{suggestion_id}:proposal_apply_allowed")
                proposal_apply_execution = True
            if proposal.get("raw_apply_target_allowed") is not False:
                bad_items.append(f"self_iteration_output:{suggestion_id}:proposal_raw_apply_allowed")
                raw_mutation = True
            if not proposal.get("validation_commands") or not proposal.get("rollback_plan_zh"):
                bad_items.append(f"self_iteration_output:{suggestion_id}:proposal_missing_validation_or_rollback")
        all_proposals_have_expiry = bool(expiry_ok) and all(expiry_ok)
        all_suggestions_have_action_half_life = bool(half_life_ok) and all(half_life_ok)
        summary = output.get("proposal_expiry_summary") if isinstance(output.get("proposal_expiry_summary"), dict) else {}
        if summary.get("all_proposals_have_expiry") is not True:
            bad_items.append("self_iteration_output:expiry_summary_not_true")
        if summary.get("all_suggestions_have_action_half_life") is not True:
            bad_items.append("self_iteration_output:half_life_summary_not_true")
        if summary.get("permanent_pending_allowed") is not False:
            bad_items.append("self_iteration_output:permanent_pending_allowed")
        boundary = output.get("phase_boundary") if isinstance(output.get("phase_boundary"), dict) else {}
        if boundary.get("does_not_apply_proposals") is not True:
            bad_items.append("self_iteration_output:proposal_apply_boundary_missing")
            proposal_apply_execution = True
        if boundary.get("does_not_create_decision_debt_ledger") is not True:
            bad_items.append("self_iteration_output:decision_debt_boundary_missing")
            decision_debt_ledger_created = True
        if boundary.get("does_not_modify_raw") is not True:
            bad_items.append("self_iteration_output:raw_boundary_missing")
            raw_mutation = True
        if boundary.get("next_phase") != "S09 P3":
            bad_items.append("self_iteration_output:next_phase_not_s09p3")

    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "self-iteration-safety",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "self_iteration_config": "机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json",
        "self_iteration_output": "data/derived/behavior_intelligence/self_iteration_suggestions.json" if output_path.exists() else "",
        "suggestion_count": len(output.get("self_iteration_suggestions") or []) if isinstance(output.get("self_iteration_suggestions"), list) else 0,
        "all_proposals_have_expiry": all_proposals_have_expiry,
        "all_suggestions_have_action_half_life": all_suggestions_have_action_half_life,
        "proposal_apply_execution": proposal_apply_execution,
        "decision_debt_ledger_created": decision_debt_ledger_created,
        "raw_mutation": raw_mutation,
        "bad_items": bad_items,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_decision_debt_safety_audit(args: argparse.Namespace) -> int:
    config_path = args.database_dir / "机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json"
    output_path = args.database_dir / "data/derived/behavior_intelligence/decision_debt_ledger.json"
    bad_items = []
    config = {}
    output = {}
    required_fields = {
        "decision_debt_id",
        "source_debt_ids",
        "debt_type",
        "decision_area_zh",
        "repeated_discussion_signal_zh",
        "evidence_refs",
        "minimal_next_step",
        "linked_self_iteration_suggestion_ids",
        "confidence",
        "not_pressure_list",
    }
    blocked_terms = {"心理诊断", "人格诊断", "人格标签", "抑郁", "焦虑症"}

    if not config_path.exists():
        bad_items.append("decision_debt_config:missing")
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("task_id") != "MA-V12-S09P3" or config.get("acceptance_id") != "ACC-MA-V12-S09P3":
            bad_items.append("decision_debt_config:identity_mismatch")
        configured_fields = set(config.get("required_debt_fields") or [])
        for field in sorted(required_fields - configured_fields):
            bad_items.append(f"decision_debt_config:missing_required_field:{field}")
        policy = config.get("ledger_policy") if isinstance(config.get("ledger_policy"), dict) else {}
        if int(policy.get("min_entries") or 0) <= 0:
            bad_items.append("decision_debt_config:invalid_min_entries")
        if policy.get("pressure_list_allowed") is not False:
            bad_items.append("decision_debt_config:pressure_list_allowed")
        step_policy = config.get("minimal_next_step_policy") if isinstance(config.get("minimal_next_step_policy"), dict) else {}
        if int(step_policy.get("effort_minutes_max") or 0) <= 0:
            bad_items.append("decision_debt_config:invalid_effort_limit")
        confidence_policy = config.get("confidence_policy") if isinstance(config.get("confidence_policy"), dict) else {}
        if float(confidence_policy.get("max_confidence") or 0) <= 0:
            bad_items.append("decision_debt_config:invalid_confidence_cap")
        boundary = config.get("scope_boundary") if isinstance(config.get("scope_boundary"), dict) else {}
        if boundary.get("raw_mutation") is not False:
            bad_items.append("decision_debt_config:raw_mutation_not_false")
        if boundary.get("proposal_apply_execution") is not False:
            bad_items.append("decision_debt_config:proposal_apply_not_false")
        if boundary.get("stage_review") != "deferred_to_s09_review":
            bad_items.append("decision_debt_config:stage_review_not_deferred")
        blocked_terms = set(config.get("blocked_output_terms") or blocked_terms)

    all_items_have_minimal_next_step = False
    pressure_list_created = False
    proposal_apply_execution = False
    raw_mutation = False
    psychological_diagnosis_output = False
    personality_label_output = False
    if not output_path.exists():
        bad_items.append("decision_debt_output:missing")
    else:
        output = json.loads(output_path.read_text(encoding="utf-8"))
        if output.get("task_id") != "MA-V12-S09P3" or output.get("acceptance_id") != "ACC-MA-V12-S09P3":
            bad_items.append("decision_debt_output:identity_mismatch")
        if output.get("status") != "phase_s09_p3_decision_debt_completed_pending_s09_review":
            bad_items.append("decision_debt_output:status_mismatch")
        ledger = output.get("decision_debt_ledger") if isinstance(output.get("decision_debt_ledger"), list) else []
        min_entries = int(config.get("ledger_policy", {}).get("min_entries") or 1)
        if len(ledger) < min_entries:
            bad_items.append("decision_debt_output:debt_count_too_low")
        minimal_next_step_ok = []
        for item in ledger:
            if not isinstance(item, dict):
                bad_items.append("decision_debt_output:invalid_debt_item")
                continue
            item_id = item.get("decision_debt_id")
            for field in sorted(required_fields):
                if item.get(field) in (None, "", []):
                    bad_items.append(f"decision_debt_output:{item_id}:missing_{field}")
            if item.get("not_pressure_list") is not True:
                bad_items.append(f"decision_debt_output:{item_id}:pressure_list_boundary_missing")
                pressure_list_created = True
            if item.get("not_applied") is not True:
                bad_items.append(f"decision_debt_output:{item_id}:applied_in_current_phase")
                proposal_apply_execution = True
            if item.get("not_psychological_diagnosis") is not True:
                bad_items.append(f"decision_debt_output:{item_id}:psychological_boundary_missing")
                psychological_diagnosis_output = True
            if item.get("not_personality_label") is not True:
                bad_items.append(f"decision_debt_output:{item_id}:personality_boundary_missing")
                personality_label_output = True
            if float(item.get("confidence") or 0) > float(config.get("confidence_policy", {}).get("max_confidence") or 0.75):
                bad_items.append(f"decision_debt_output:{item_id}:confidence_too_high")
            step = item.get("minimal_next_step") if isinstance(item.get("minimal_next_step"), dict) else {}
            has_step = bool(step.get("step_zh") and step.get("expected_artifact_zh") and step.get("stop_condition_zh"))
            minimal_next_step_ok.append(has_step)
            if not has_step:
                bad_items.append(f"decision_debt_output:{item_id}:minimal_next_step_incomplete")
            if int(step.get("effort_minutes_max") or 0) <= 0:
                bad_items.append(f"decision_debt_output:{item_id}:minimal_next_step_invalid_effort")
            target_text = " ".join(str(value) for value in [
                item.get("decision_area_zh"),
                item.get("repeated_discussion_signal_zh"),
                item.get("evidence_summary_zh"),
                step.get("step_zh"),
                step.get("stop_condition_zh"),
            ])
            if any(term and term in target_text for term in blocked_terms):
                bad_items.append(f"decision_debt_output:{item_id}:blocked_term")
                psychological_diagnosis_output = True
            for ref in item.get("evidence_refs") or []:
                path = str(ref.get("path") or "") if isinstance(ref, dict) else ""
                if "data/public_raw/" in path or "data/raw/" in path:
                    raw_mutation = True
        all_items_have_minimal_next_step = bool(minimal_next_step_ok) and all(minimal_next_step_ok)
        summary = output.get("safety_summary") if isinstance(output.get("safety_summary"), dict) else {}
        if summary.get("all_items_have_minimal_next_step") is not True:
            bad_items.append("decision_debt_output:minimal_next_step_summary_not_true")
        if summary.get("pressure_list_created") is not False:
            bad_items.append("decision_debt_output:pressure_list_summary_created")
            pressure_list_created = True
        boundary = output.get("phase_boundary") if isinstance(output.get("phase_boundary"), dict) else {}
        if boundary.get("does_not_generate_pressure_list") is not True:
            bad_items.append("decision_debt_output:pressure_list_boundary_missing")
            pressure_list_created = True
        if boundary.get("does_not_apply_proposals") is not True:
            bad_items.append("decision_debt_output:proposal_apply_boundary_missing")
            proposal_apply_execution = True
        if boundary.get("does_not_modify_raw") is not True:
            bad_items.append("decision_debt_output:raw_boundary_missing")
            raw_mutation = True
        if boundary.get("next_phase") != "S09 Review":
            bad_items.append("decision_debt_output:next_phase_not_s09_review")

    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "decision-debt-safety",
        "task_id": config.get("task_id") or output.get("task_id"),
        "acceptance_id": config.get("acceptance_id") or output.get("acceptance_id"),
        "decision_debt_config": "机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json",
        "decision_debt_output": "data/derived/behavior_intelligence/decision_debt_ledger.json" if output_path.exists() else "",
        "decision_debt_count": len(output.get("decision_debt_ledger") or []) if isinstance(output.get("decision_debt_ledger"), list) else 0,
        "all_items_have_minimal_next_step": all_items_have_minimal_next_step,
        "pressure_list_created": pressure_list_created,
        "proposal_apply_execution": proposal_apply_execution,
        "raw_mutation": raw_mutation,
        "psychological_diagnosis_output": psychological_diagnosis_output,
        "personality_label_output": personality_label_output,
        "bad_items": bad_items,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_chinese_ux_audit(args: argparse.Namespace) -> int:
    src_root = args.database_dir / "apps/memory-atlas/src"
    copy_path = args.database_dir / "apps/memory-atlas/src/i18n/zh-CN.ts"
    style_path = args.database_dir / "apps/memory-atlas/src/styles.css"
    runtime_paths = sorted(
        path
        for pattern in ("*.ts", "*.tsx")
        for path in src_root.rglob(pattern)
        if "experiments" not in path.relative_to(src_root).parts and not path.name.endswith(".d.ts")
    ) if src_root.is_dir() else []
    missing_files = [
        str(path.relative_to(args.database_dir))
        for path in (copy_path, style_path)
        if not path.exists()
    ]
    if not runtime_paths:
        missing_files.append("apps/memory-atlas/src/**/*.ts(x)")
    if missing_files:
        print(json.dumps({
            "status": "FAIL",
            "command": "audit",
            "check": "chinese-ux",
            "task_id": "MA-V12-S10P3",
            "acceptance_id": "ACC-MA-V12-S10P3",
            "reason": "Chinese UX source files missing",
            "missing_files": missing_files,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    app_source = "\n".join(path.read_text(encoding="utf-8") for path in runtime_paths)
    copy_source = copy_path.read_text(encoding="utf-8")
    style_source = style_path.read_text(encoding="utf-8")
    readability_script = args.database_dir / "apps/memory-atlas/scripts/validate_memory_atlas_semantic_readability.mjs"
    readability_config = args.database_dir / "config/memory_atlas_semantic_readability.json"
    readability_payload: dict[str, object] = {
        "status": "FAIL",
        "reason": "semantic readability rule did not run",
    }
    try:
        readability_result = subprocess.run(
            [
                "node",
                str(readability_script),
                "--src-root",
                str(args.database_dir / "apps/memory-atlas/src"),
                "--config",
                str(readability_config),
            ],
            cwd=args.database_dir / "apps/memory-atlas",
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        parsed_readability = json.loads(readability_result.stdout)
        if isinstance(parsed_readability, dict):
            readability_payload = parsed_readability
        else:
            readability_payload = {"status": "FAIL", "reason": "semantic readability output is not an object"}
        if readability_result.returncode != 0 and readability_payload.get("status") == "PASS":
            readability_payload = {
                "status": "FAIL",
                "reason": f"semantic readability exited {readability_result.returncode} after reporting PASS",
            }
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        readability_payload = {"status": "FAIL", "reason": f"semantic readability execution failed: {exc}"}
    required_copy = [
        "上次来以后发生了什么",
        "新增重要资料",
        "增强结论",
        "减弱或过期结论",
        "待授权提案",
        "同步失败",
        "下一步",
    ]
    required_global_chinese_copy = [
        "记忆天气",
        "轻量星图",
        "时间脉冲",
        "下一步行动",
        "仅生成提案",
        "证据入口",
        "稳定度",
        "动量",
        "宇宙状态",
    ]
    required_machine_detail_copy = [
        "高级详情：机器字段",
        "显示高级详情",
        "隐藏高级详情",
        "默认折叠，仅用于核验字段",
    ]
    english_first_fragments = [
        "<dt>Stable</dt>",
        "<dt>Momentum</dt>",
        "<dt>Risk</dt>",
        "<dt>Opportunity</dt>",
        "top actions</small>",
        "top actions=",
        "<small>Universe State derived</small>",
        "<span>proposal-only</span>",
        " assets</small>",
        " themes</small>",
        "<i>Value ",
        "<i>Strength ",
        " records</i>",
        "day half-life",
    ]
    default_visible_machine_fragments = [
        "<h3>search_session_summary</h3>",
        "<h3>Review session output</h3>",
        "<h3>Proposal decision</h3>",
        "<h3>Iteration backlog</h3>",
        "<h3>zero_result_recovery</h3>",
        "<span>jump_to_starfield</span>",
        "<span>jump_to_river</span>",
        "<span>open_inspector</span>",
        "proposal_candidate=true",
        "proposal_candidate=false",
        "<h4>change_comparison</h4>",
        "<h4>stale_conflict_signals</h4>",
        "<h4>proposal_candidates</h4>",
        "<span>{summaryClosure.change_comparison.length} signals</span>",
        "<span>{summaryClosure.stale_conflict_signals.length} checks</span>",
        "<span>{summaryClosure.proposal_candidates.length} candidates</span>",
    ]
    bad_items: list[str] = []
    if readability_payload.get("status") != "PASS" or readability_payload.get("baseline_exact") is not True:
        bad_items.append(
            "semantic_readability_failed:"
            f"unexpected={len(readability_payload.get('unexpected_findings') or [])}:"
            f"missing={len(readability_payload.get('missing_known_findings') or [])}"
        )
    if "data-home-section=\"arrival_briefing\"" not in app_source:
        bad_items.append("home_arrival_briefing_missing")
    if app_source.find("data-home-section=\"arrival_briefing\"") > app_source.find("data-home-section=\"weather\""):
        bad_items.append("arrival_briefing_not_before_weather")
    if "data-s10-p1-home-arrival-briefing" not in app_source:
        bad_items.append("s10p1_data_contract_missing")
    if "arrival-briefing-machine-details" not in app_source or "data-s10-p3-machine-fields=\"collapsed-by-default\"" not in app_source:
        bad_items.append("machine_details_not_folded")
    for label in required_copy:
        if label not in app_source and label not in copy_source:
            bad_items.append(f"copy_missing:{label}")
    for label in required_global_chinese_copy:
        if label not in app_source and label not in copy_source:
            bad_items.append(f"global_chinese_copy_missing:{label}")
    if "data-s10-p2-global-chinese-ux" not in app_source:
        bad_items.append("s10p2_global_chinese_contract_missing")
    if "GLOBAL_CHINESE_UX_VERSION" not in app_source or "__memoryAtlasS10Phase2" not in app_source:
        bad_items.append("s10p2_runtime_proof_missing")
    if "data-s10-p3-machine-detail-folding" not in app_source:
        bad_items.append("s10p3_machine_detail_contract_missing")
    if "MACHINE_DETAIL_FOLDING_VERSION" not in app_source or "__memoryAtlasS10Phase3" not in app_source:
        bad_items.append("s10p3_runtime_proof_missing")
    if "data-s10-p3-machine-fields=\"collapsed-by-default\"" not in app_source:
        bad_items.append("s10p3_machine_fields_default_folded_missing")
    if "advancedDetailsEntryVisible: true" not in app_source or "machineFieldsDefaultCollapsed: true" not in app_source:
        bad_items.append("s10p3_runtime_flags_missing")
    for fragment in english_first_fragments:
        if fragment in app_source:
            bad_items.append(f"english_first_fragment:{fragment}")
    for fragment in default_visible_machine_fragments:
        if fragment in app_source:
            bad_items.append(f"default_visible_machine_fragment:{fragment}")
    for label in required_machine_detail_copy:
        if label not in app_source and label not in copy_source:
            bad_items.append(f"machine_detail_copy_missing:{label}")
    if "Memory Weather" in app_source + copy_source and "记忆天气 v2（Memory Weather）" not in copy_source:
        bad_items.append("machine_term_explanation_missing:Memory Weather")
    if "Universe State" in app_source + copy_source and "宇宙状态（Universe State）" not in app_source + copy_source:
        bad_items.append("machine_term_explanation_missing:Universe State")
    if "仅生成提案，不直接写长期记忆" not in copy_source:
        bad_items.append("machine_term_explanation_missing:proposal-only")
    if ".home-arrival-briefing" not in style_source or ".arrival-briefing-next-step" not in style_source:
        bad_items.append("arrival_briefing_styles_missing")
    if ".machine-field-details" not in style_source or ".inline-machine-field-details" not in style_source:
        bad_items.append("machine_detail_styles_missing")
    if "proposal apply" in app_source.lower() and "No proposal apply execution" not in app_source:
        bad_items.append("possible_apply_language_without_boundary")

    status = "PASS" if not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "chinese-ux",
        "task_id": "MA-V12-S10P3",
        "acceptance_id": "ACC-MA-V12-S10P3",
        "details": {
            "home_arrival_briefing": "home_arrival_briefing_missing" not in bad_items,
            "arrival_before_weather": "arrival_briefing_not_before_weather" not in bad_items,
            "machine_details_default_folded": "machine_details_not_folded" not in bad_items,
            "s10_p2_global_chinese": "s10p2_global_chinese_contract_missing" not in bad_items and "s10p2_runtime_proof_missing" not in bad_items,
            "s10_p3_machine_detail_folding": "s10p3_machine_detail_contract_missing" not in bad_items and "s10p3_runtime_proof_missing" not in bad_items,
            "machine_fields_default_folded": "s10p3_machine_fields_default_folded_missing" not in bad_items and "s10p3_runtime_flags_missing" not in bad_items,
            "advanced_details_entry_visible": not any(item.startswith("machine_detail_copy_missing:") for item in bad_items) and "machine_detail_styles_missing" not in bad_items,
            "core_ui_default_chinese": not any(item.startswith("english_first_fragment:") or item.startswith("global_chinese_copy_missing:") for item in bad_items),
            "machine_terms_with_chinese_explanation": not any(item.startswith("machine_term_explanation_missing:") for item in bad_items),
            "default_visible_machine_fragments_removed": not any(item.startswith("default_visible_machine_fragment:") for item in bad_items),
            "semantic_readability": {
                "status": readability_payload.get("status"),
                "schema_version": readability_payload.get("schema_version"),
                "task_id": readability_payload.get("task_id"),
                "remediation_task": readability_payload.get("remediation_task"),
                "source_file_count": readability_payload.get("source_file_count"),
                "finding_count": readability_payload.get("finding_count"),
                "known_finding_count": readability_payload.get("known_finding_count"),
                "known_t3_debt_count": readability_payload.get("known_t3_debt_count"),
                "semantic_readability_clean": readability_payload.get("semantic_readability_clean"),
                "rule_counts": readability_payload.get("rule_counts"),
                "baseline_exact": readability_payload.get("baseline_exact"),
                "unexpected_finding_count": len(readability_payload.get("unexpected_findings") or []),
                "missing_known_finding_count": len(readability_payload.get("missing_known_findings") or []),
            },
            "bad_items": bad_items,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2


def run_audit(args: argparse.Namespace) -> int:
    if not args.check:
        return run_final_audit(args)
    if args.check == "chinese-ux":
        return run_chinese_ux_audit(args)
    if args.check == "decision-debt-safety":
        return run_decision_debt_safety_audit(args)
    if args.check == "self-iteration-safety":
        return run_self_iteration_safety_audit(args)
    if args.check == "latent-safety":
        return run_latent_safety_audit(args)
    if args.check == "stage-flight":
        return run_stage_flight_audit(args)
    if args.check == "agent-authorization":
        return run_agent_authorization_audit(args)
    if args.check == "agent-collaboration":
        return run_agent_collaboration_audit(args)
    if args.check == "formula-what-if":
        return run_formula_what_if_audit(args)
    if args.check == "visual-roi":
        return run_visual_roi_audit(args)
    if args.check == "formulas":
        return run_formula_audit(args)
    if args.check != "insight-evidence":
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "command": "audit",
            "check": args.check,
            "reason": "Unknown audit check. Supported checks: insight-evidence, formulas, visual-roi, formula-what-if, agent-collaboration, agent-authorization, stage-flight, latent-safety, self-iteration-safety, decision-debt-safety, chinese-ux.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    clusters_path = args.database_dir / "data/derived/behavior_intelligence/clusters.json"
    if not clusters_path.exists():
        print(json.dumps({
            "status": "FAIL",
            "command": "audit",
            "check": "insight-evidence",
            "reason": "clusters output missing",
            "path": "data/derived/behavior_intelligence/clusters.json",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    payload = json.loads(clusters_path.read_text(encoding="utf-8"))
    bad_clusters = []
    for collection_name in ("topic_clusters", "hierarchy_clusters"):
        for cluster in payload.get(collection_name) or []:
            if not cluster.get("evidence_refs"):
                bad_clusters.append(f"{collection_name}:{cluster.get('cluster_id')}:missing_evidence_refs")
            if not cluster.get("summary_zh"):
                bad_clusters.append(f"{collection_name}:{cluster.get('cluster_id')}:missing_summary_zh")
    low_value_path = args.database_dir / "data/derived/behavior_intelligence/low_value_loops.json"
    low_value_payload = {}
    bad_items = []
    if low_value_path.exists():
        low_value_payload = json.loads(low_value_path.read_text(encoding="utf-8"))
        bad_items.extend(audit_evidence_collection(
            low_value_payload.get("loop_clusters") or [],
            "loop_clusters",
            "loop_id",
            ("summary_zh",),
        ))
        bad_items.extend(audit_evidence_collection(
            low_value_payload.get("decision_debt_ledger") or [],
            "decision_debt_ledger",
            "debt_id",
            ("suggested_closure_question",),
        ))
        bad_items.extend(audit_evidence_collection(
            low_value_payload.get("action_half_life") or [],
            "action_half_life",
            "half_life_id",
            ("interpretation_zh",),
        ))
        for item in low_value_payload.get("action_half_life") or []:
            if int(item.get("action_half_life_days") or 0) <= 0:
                bad_items.append(f"action_half_life:{item.get('half_life_id')}:invalid_action_half_life_days")
    opportunities_path = args.database_dir / "data/derived/behavior_intelligence/opportunities.json"
    opportunities_payload = {}
    if opportunities_path.exists():
        opportunities_payload = json.loads(opportunities_path.read_text(encoding="utf-8"))
        bad_items.extend(audit_evidence_collection(
            opportunities_payload.get("opportunity_clusters") or [],
            "opportunity_clusters",
            "opportunity_id",
            ("summary_zh", "next_step_zh"),
        ))
        for item in opportunities_payload.get("opportunity_clusters") or []:
            card = item.get("why_not_now_card") or {}
            if not card.get("reason_zh") or card.get("not_pressure_list") is not True or not card.get("evidence_refs"):
                bad_items.append(f"opportunity_clusters:{item.get('opportunity_id')}:invalid_why_not_now_card")
            if int(item.get("opportunity_half_life_days") or 0) <= 0 and not item.get("defer_reason_zh"):
                bad_items.append(f"opportunity_clusters:{item.get('opportunity_id')}:missing_half_life_or_defer_reason")
    status = "PASS" if not bad_clusters and not bad_items else "FAIL"
    result = {
        "status": status,
        "command": "audit",
        "check": "insight-evidence",
        "task_id": payload.get("task_id"),
        "acceptance_id": payload.get("acceptance_id"),
        "cluster_count": payload.get("cluster_count"),
        "topic_cluster_count": payload.get("topic_cluster_count"),
        "hierarchy_cluster_count": payload.get("hierarchy_cluster_count"),
        "bad_clusters": bad_clusters,
        "low_value_loop_task_id": low_value_payload.get("task_id"),
        "low_value_loop_acceptance_id": low_value_payload.get("acceptance_id"),
        "loop_cluster_count": low_value_payload.get("loop_cluster_count"),
        "decision_debt_count": low_value_payload.get("decision_debt_count"),
        "action_half_life_count": low_value_payload.get("action_half_life_count"),
        "opportunity_task_id": opportunities_payload.get("task_id"),
        "opportunity_acceptance_id": opportunities_payload.get("acceptance_id"),
        "opportunity_count": opportunities_payload.get("opportunity_count"),
        "defer_card_count": opportunities_payload.get("defer_card_count"),
        "bad_items": bad_items,
        "raw_mutation": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 2

__all__ = (
    "FOUR_LINE_GATES",
    "REQUIRED_R8_GATE_IDS",
    "AcceptanceHistoryError",
    "build_acceptance_summary",
    "final_audit_gate_plan",
    "compact_tail",
    "final_audit_dry_run_contract",
    "run_final_audit",
    "audit_evidence_collection",
    "run_formula_audit",
    "run_visual_roi_audit",
    "run_formula_what_if_audit",
    "run_agent_collaboration_audit",
    "run_agent_authorization_audit",
    "run_stage_flight_audit",
    "run_latent_safety_audit",
    "run_self_iteration_safety_audit",
    "run_decision_debt_safety_audit",
    "run_chinese_ux_audit",
    "run_audit",
)
