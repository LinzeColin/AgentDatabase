from __future__ import annotations

import argparse
import json
import subprocess
import sys

from .constants import (
    AGENT_AUTHORIZATION_BUILDER,
    AGENT_COLLABORATION_BUILDER,
    CLUSTER_BUILDER,
    DECISION_DEBT_BUILDER,
    ECONOMIC_PROXY_BUILDER,
    FACET_EXTRACTOR,
    FORMULA_WHAT_IF_BUILDER,
    INFORMATION_ROI_BUILDER,
    LATENT_SIGNAL_BUILDER,
    LOW_VALUE_LOOP_BUILDER,
    OPPORTUNITY_BUILDER,
    ROOT,
    SELF_ITERATION_BUILDER,
    STAGE_FLIGHT_BUILDER,
)


def facet_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "facets",
        "dry_run": True,
        "writes_files": False,
        "extractor": "scripts/extract_memory_atlas_facets.py",
        "output": "data/derived/behavior_intelligence/events.json",
        "input_roots": [
            "data/public_raw/chatgpt",
            "data/public_raw/codex",
            "data/public_raw/agents",
            "data/processed/conversations/conversation_manifest.jsonl",
            "data/processed/codex/codex_session_manifest.jsonl",
            "data/derived/codex",
            "data/derived/agents",
        ],
        "missing_source_policy": "record source_status missing_reason without fake events",
        "raw_mutation": False,
        "task_id": "MA-V12-S05P3",
        "acceptance_id": "ACC-MA-V12-S05P3",
    }


def cluster_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "clusters",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_clusters.py",
        "input": "data/derived/behavior_intelligence/events.json",
        "output": "data/derived/behavior_intelligence/clusters.json",
        "supported_filters": ["source", "time", "project", "task", "language"],
        "raw_mutation": False,
        "task_id": "MA-V12-S06P1",
        "acceptance_id": "ACC-MA-V12-S06P1",
    }


def low_value_loop_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "low-value-loops",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_low_value_loops.py",
        "input": [
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
        ],
        "output": "data/derived/behavior_intelligence/low_value_loops.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S06P2",
        "acceptance_id": "ACC-MA-V12-S06P2",
        "phase_boundary": {
            "does_not_generate_opportunity_cards": True,
            "next_phase": "S06 P3",
        },
    }


def opportunity_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "opportunities",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_opportunities.py",
        "input": [
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
            "data/derived/behavior_intelligence/low_value_loops.json",
        ],
        "output": "data/derived/behavior_intelligence/opportunities.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S06P3",
        "acceptance_id": "ACC-MA-V12-S06P3",
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_create_infinite_pressure_list": True,
            "next_phase": "S06 Review",
        },
    }


def economic_proxy_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "economic-proxy",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_economic_proxy.py",
        "formula_config": "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json",
        "input": [
            "data/derived/behavior_intelligence/clusters.json",
            "data/derived/behavior_intelligence/low_value_loops.json",
            "data/derived/behavior_intelligence/opportunities.json",
        ],
        "output": "data/derived/economic_proxy/personal_economic_proxy.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S07P1",
        "acceptance_id": "ACC-MA-V12-S07P1",
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_claim_precise_income_prediction": True,
            "does_not_generate_information_roi_gate": True,
            "does_not_generate_what_if_ui": True,
            "next_phase": "S07 P2",
        },
    }


def information_roi_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "information-roi",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_information_roi.py",
        "formula_config": "机器治理/参数与公式/information_roi.v1_2_s07_p2.json",
        "visual_gate_config": "机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json",
        "input": [
            "data/derived/visualization/memory_atlas.json",
            "data/derived/economic_proxy/personal_economic_proxy.json",
        ],
        "output": "data/derived/information_roi/information_roi_gate.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S07P2",
        "acceptance_id": "ACC-MA-V12-S07P2",
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_claim_precise_income_prediction": True,
            "does_not_generate_what_if_ui": True,
            "next_phase": "S07 P3",
        },
    }


def formula_what_if_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "formula-what-if",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_formula_what_if.py",
        "formula_what_if_config": "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
        "active_formula_config": "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json",
        "input": [
            "data/derived/economic_proxy/personal_economic_proxy.json",
            "data/derived/information_roi/information_roi_gate.json",
        ],
        "output": "data/derived/economic_proxy/formula_what_if_preview.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S07P3",
        "acceptance_id": "ACC-MA-V12-S07P3",
        "phase_boundary": {
            "does_not_use_external_economic_database": True,
            "does_not_claim_precise_income_prediction": True,
            "does_not_provide_financial_advice": True,
            "does_not_mutate_active_formula_config": True,
            "requires_proposal_before_apply": True,
            "next_phase": "S07 Review",
        },
    }


def agent_collaboration_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "agent-collaboration",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_agent_collaboration.py",
        "metrics_config": "机器治理/行为智能模型/agent_collaboration_metrics.v1_2_s08_p1.json",
        "input": [
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
            "data/derived/behavior_intelligence/low_value_loops.json",
            "data/derived/behavior_intelligence/opportunities.json",
            "data/derived/information_roi/information_roi_gate.json",
        ],
        "output": "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S08P1",
        "acceptance_id": "ACC-MA-V12-S08P1",
        "phase_boundary": {
            "does_not_create_multi_agent_system": True,
            "does_not_implement_complex_delegation_contract_ui": True,
            "does_not_define_authorization_apply_boundary": True,
            "does_not_generate_stage_flight_recorder": True,
            "next_phase": "S08 P2",
        },
    }


def agent_authorization_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "agent-authorization",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_agent_authorization.py",
        "authorization_config": "机器治理/行为智能模型/agent_authorization_boundary.v1_2_s08_p2.json",
        "input": [
            "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
            "机器治理/同步与备份/raw_public_archive_policy.v1_2_s03_p1.json",
            "机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json",
            "机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json",
        ],
        "output": "data/derived/agent_collaboration/agent_authorization_boundary_report.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S08P2",
        "acceptance_id": "ACC-MA-V12-S08P2",
        "phase_boundary": {
            "authorization_boundary_defined_as_machine_checks": True,
            "does_not_modify_raw": True,
            "does_not_apply_proposals": True,
            "requires_human_approval_before_apply": True,
            "does_not_implement_complex_delegation_contract_ui": True,
            "does_not_generate_stage_flight_recorder": True,
            "next_phase": "S08 P3",
        },
    }


def stage_flight_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "stage-flight",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_stage_flight.py",
        "stage_flight_config": "机器治理/证据与日志/stage_flight_recorder_fields.v1_2_s08_p3.json",
        "input": [
            "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
            "data/derived/agent_collaboration/agent_authorization_boundary_report.json",
        ],
        "output": "data/derived/agent_collaboration/stage_flight_recorder.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S08P3",
        "acceptance_id": "ACC-MA-V12-S08P3",
        "phase_boundary": {
            "lightweight_stage_flight_recorder": True,
            "does_not_include_raw_or_transcript_payloads": True,
            "does_not_generate_bulky_human_docs": True,
            "records_necessary_info_in_development_records": True,
            "next_phase": "S08 Review",
        },
    }


def latent_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "latent",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_latent_signals.py",
        "latent_signal_config": "机器治理/行为智能模型/latent_signals.v1_2_s09_p1.json",
        "input": [
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
            "data/derived/behavior_intelligence/low_value_loops.json",
            "data/derived/behavior_intelligence/opportunities.json",
        ],
        "output": "data/derived/behavior_intelligence/latent_signals.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S09P1",
        "acceptance_id": "ACC-MA-V12-S09P1",
        "phase_boundary": {
            "does_not_output_psychological_diagnosis": True,
            "does_not_output_personality_label": True,
            "does_not_create_self_iteration_suggestions": True,
            "proposal_expiry_deferred_to": "S09 P2",
            "does_not_create_decision_debt_ledger": True,
            "decision_debt_ledger_deferred_to": "S09 P3",
            "next_phase": "S09 P2",
        },
    }


def self_iteration_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "self-iteration",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_self_iteration.py",
        "self_iteration_config": "机器治理/行为智能模型/self_iteration.v1_2_s09_p2.json",
        "input": ["data/derived/behavior_intelligence/latent_signals.json"],
        "output": "data/derived/behavior_intelligence/self_iteration_suggestions.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S09P2",
        "acceptance_id": "ACC-MA-V12-S09P2",
        "phase_boundary": {
            "does_not_apply_proposals": True,
            "requires_human_approval_before_apply": True,
            "proposal_expiry_required": True,
            "action_half_life_required": True,
            "does_not_create_decision_debt_ledger": True,
            "decision_debt_ledger_deferred_to": "S09 P3",
            "next_phase": "S09 P3",
        },
    }


def decision_debt_analyze_contract() -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "analyze",
        "stage": "decision-debt",
        "dry_run": True,
        "writes_files": False,
        "builder": "scripts/build_memory_atlas_decision_debt.py",
        "decision_debt_config": "机器治理/行为智能模型/decision_debt.v1_2_s09_p3.json",
        "input": [
            "data/derived/behavior_intelligence/low_value_loops.json",
            "data/derived/behavior_intelligence/self_iteration_suggestions.json",
            "data/derived/behavior_intelligence/latent_signals.json",
        ],
        "output": "data/derived/behavior_intelligence/decision_debt_ledger.json",
        "raw_mutation": False,
        "task_id": "MA-V12-S09P3",
        "acceptance_id": "ACC-MA-V12-S09P3",
        "phase_boundary": {
            "does_not_generate_pressure_list": True,
            "does_not_apply_proposals": True,
            "requires_human_approval_before_apply": True,
            "minimal_next_step_required": True,
            "does_not_modify_raw": True,
            "stage_review_deferred_to": "S09 Review",
            "next_phase": "S09 Review",
        },
    }


def run_analyze(args: argparse.Namespace) -> int:
    if args.stage not in {
        "facets",
        "clusters",
        "low-value-loops",
        "opportunities",
        "economic-proxy",
        "information-roi",
        "formula-what-if",
        "agent-collaboration",
        "agent-authorization",
        "stage-flight",
        "latent",
        "self-iteration",
        "decision-debt",
    }:
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "command": "analyze",
            "stage": args.stage,
            "reason": "Unknown analyze stage. Supported stages: facets, clusters, low-value-loops, opportunities, economic-proxy, information-roi, formula-what-if, agent-collaboration, agent-authorization, stage-flight, latent, self-iteration, decision-debt.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    if args.stage == "facets":
        if args.dry_run:
            command = [sys.executable, str(FACET_EXTRACTOR), "--database-dir", str(args.database_dir), "--dry-run"]
        else:
            command = [sys.executable, str(FACET_EXTRACTOR), "--database-dir", str(args.database_dir)]
    elif args.stage == "clusters":
        command = [sys.executable, str(CLUSTER_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
        for cli_name, value in [
            ("--source", args.source),
            ("--time-from", args.time_from),
            ("--time-to", args.time_to),
            ("--project", args.project),
            ("--task", args.task),
            ("--language", args.language),
        ]:
            if value:
                command.extend([cli_name, value])
    elif args.stage == "low-value-loops":
        command = [sys.executable, str(LOW_VALUE_LOOP_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "opportunities":
        command = [sys.executable, str(OPPORTUNITY_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "economic-proxy":
        command = [sys.executable, str(ECONOMIC_PROXY_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "information-roi":
        command = [sys.executable, str(INFORMATION_ROI_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "formula-what-if":
        command = [sys.executable, str(FORMULA_WHAT_IF_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "agent-collaboration":
        command = [sys.executable, str(AGENT_COLLABORATION_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "agent-authorization":
        command = [sys.executable, str(AGENT_AUTHORIZATION_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "stage-flight":
        command = [sys.executable, str(STAGE_FLIGHT_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "latent":
        command = [sys.executable, str(LATENT_SIGNAL_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "self-iteration":
        command = [sys.executable, str(SELF_ITERATION_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    elif args.stage == "decision-debt":
        command = [sys.executable, str(DECISION_DEBT_BUILDER), "--database-dir", str(args.database_dir)]
        if args.dry_run:
            command.append("--dry-run")
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode

__all__ = (
    "facet_analyze_contract",
    "cluster_analyze_contract",
    "low_value_loop_analyze_contract",
    "opportunity_analyze_contract",
    "economic_proxy_analyze_contract",
    "information_roi_analyze_contract",
    "formula_what_if_analyze_contract",
    "agent_collaboration_analyze_contract",
    "agent_authorization_analyze_contract",
    "stage_flight_analyze_contract",
    "latent_analyze_contract",
    "self_iteration_analyze_contract",
    "decision_debt_analyze_contract",
    "run_analyze",
)
