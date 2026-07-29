#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_ROOT.parent
sys.path.insert(0, str(SCRIPT_ROOT))

from wbi_core.genesis import verify_genesis  # noqa: E402
from wbi_core.competitors import build_competitor_dataset, inspect_repository, load_supplementary_records  # noqa: E402
from wbi_core.freshness import build_freshness_scan, reheat_status  # noqa: E402
from wbi_core.luban import seal_research, validate_luban_gates  # noqa: E402
from wbi_core.evaluation import evaluate_workspace, seal_eval_contract  # noqa: E402
from wbi_core.security import classify_action, validate_authority, write_default_authority  # noqa: E402
from wbi_core.reviews import collect_review, generate_review_plan, review_gate  # noqa: E402
from wbi_core.gates import gate_workspace  # noqa: E402
from wbi_core.install import install_archive, inspect_install_transaction, recover_install_transactions, rollback_install  # noqa: E402
from wbi_core.provenance import generate_release_receipt  # noqa: E402
from wbi_core.io import generate_manifest  # noqa: E402
from wbi_core.package import package_skill  # noqa: E402
from wbi_core.process import run_bounded  # noqa: E402
from wbi_core.smoke import run_release_smoke  # noqa: E402
from wbi_core.validation import validate_skill  # noqa: E402
from wbi_core.workspace import init_run, loop_status, record_change, record_round, transition, update_counters  # noqa: E402
from wbi_core.status import validate_status_file  # noqa: E402
from wbi_core.telemetry import aggregate_file  # noqa: E402
from wbi_core.benchmark import evaluate_benchmark, seal_benchmark_contract  # noqa: E402
from wbi_core.review_adapter import inspect_review_adapter  # noqa: E402
from wbi_core.orchestrator import attach_preflight, explain_block, init_orchestration, inspect_orchestration, mark_step  # noqa: E402
from wbi_core.review_ablation import evaluate_review_ablation_file  # noqa: E402
from wbi_core.portability import evaluate_portability_file  # noqa: E402
from wbi_core.peer_taxonomy import audit_file as audit_peer_file  # noqa: E402
from wbi_core.utility_guard import evaluate_utility_file  # noqa: E402
from wbi_core.environment_doctor import run_environment_doctor  # noqa: E402
from wbi_core.verifier_bridge import export_verifier_packet  # noqa: E402
from wbi_core.expert_panel import export_expert_panel_request  # noqa: E402
from wbi_core.dashboard import render_dashboard_file  # noqa: E402
from wbi_core.diagnostics import diagnose_target  # noqa: E402
from wbi_core.adaptive import build_adaptive_plan, build_adaptive_plan_file  # noqa: E402
from wbi_core.strategy import inspect_strategy_memory, update_strategy_memory  # noqa: E402
from wbi_core.showcase import generate_showcase  # noqa: E402
from wbi_core.market_profile import build_market_profile  # noqa: E402
from wbi_core.environment_strength import capture_environment_snapshot, attest_environment_strength  # noqa: E402
from wbi_core.coverage import evaluate_skill_coverage  # noqa: E402
from wbi_core.shadowing import evaluate_skill_shadowing  # noqa: E402
from wbi_core.stochastic import compare_stochastic_results  # noqa: E402


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False))


def command_verify_self(args: argparse.Namespace) -> int:
    root = Path(args.skill_root).resolve() if args.skill_root else SKILL_ROOT
    validation = validate_skill(
        root, strict=args.strict, expected_genesis_hash=args.expected_genesis_hash or "",
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "", profile="optimizer"
    )
    emit(validation)
    return 0 if validation["status"] == "PASS" else 2


def command_validate(args: argparse.Namespace) -> int:
    result = validate_skill(
        Path(args.skill_dir), strict=args.strict, check_manifest=not args.ignore_manifest,
        expected_genesis_hash=args.expected_genesis_hash or "",
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "", profile=args.profile
    )
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_manifest(args: argparse.Namespace) -> int:
    root = Path(args.skill_dir).resolve()
    count = generate_manifest(root)
    result = validate_skill(
        root, strict=True, expected_genesis_hash=args.expected_genesis_hash or "",
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "", profile=args.profile
    )
    result["manifest_entries"] = count
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_package(args: argparse.Namespace) -> int:
    result = package_skill(
        Path(args.skill_dir), Path(args.output), expected_genesis_hash=args.expected_genesis_hash or "",
        profile=args.profile, verification_level=args.verification_level,
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "",
    )
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_release_smoke(args: argparse.Namespace) -> int:
    expected = args.expected_genesis_hash or __import__("os").environ.get("WBI_EXPECTED_GENESIS_SHA256", "")
    expected_effective = args.expected_effective_genesis_hash or __import__("os").environ.get("WBI_EXPECTED_EFFECTIVE_GENESIS_SHA256", "")
    if not expected:
        emit({"status": "FAIL", "errors": ["release-smoke requires an external Genesis hash anchor"]})
        return 2
    result = run_release_smoke(SKILL_ROOT, expected, expected_effective)
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_self_test(args: argparse.Namespace) -> int:
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(SKILL_ROOT / "tests"), "-p", "test_*.py", "-v"]
    completed = run_bounded(
        command, cwd=SKILL_ROOT, timeout_seconds=args.timeout,
        env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1", "WBI_NESTED_SELF_TEST": "1"},
    )
    result = {
        "status": "PASS" if completed["returncode"] == 0 and not completed["timed_out"] else "FAIL",
        "returncode": completed["returncode"], "timed_out": completed["timed_out"],
        "timeout_seconds": completed["timeout_seconds"],
        "elapsed_seconds": completed["elapsed_seconds"],
        "stdout_bytes": completed["stdout_bytes"], "stderr_bytes": completed["stderr_bytes"],
        "stdout": completed["stdout"], "stderr": completed["stderr"],
    }
    emit(result)
    return 0 if result["status"] == "PASS" else 2



def command_init_run(args: argparse.Namespace) -> int:
    strategies = args.strategy or ["incremental", "architecture", "clean-slate"]
    result = init_run(
        Path(args.target), Path(args.workspace), SKILL_ROOT, strategies,
        Path(args.budget) if args.budget else None, self_evolve=args.self_evolve,
        release_profile=args.release_profile, valid_as_of=args.valid_as_of, timezone_name=args.timezone,
        release_profile_contract_path=Path(args.release_profile_contract) if args.release_profile_contract else None,
        review_attestation_contract_path=Path(args.review_attestation_contract) if args.review_attestation_contract else None,
    )
    emit({"status": "PASS", "run": result})
    return 0


def command_record_change(args: argparse.Namespace) -> int:
    result = record_change(Path(args.workspace), args.candidate_id, Path(args.record))
    emit({"status": "PASS", "record": result})
    return 0


def command_record_round(args: argparse.Namespace) -> int:
    result = record_round(Path(args.workspace), Path(args.record))
    emit({"status": "PASS", "record": result})
    return 0


def command_loop_status(args: argparse.Namespace) -> int:
    result = loop_status(Path(args.workspace))
    emit(result)
    return 0 if result["status"] == "CONTINUE" else 3


def command_transition(args: argparse.Namespace) -> int:
    result = transition(Path(args.workspace), args.status, args.reason, args.actor_id)
    emit({"status": "PASS", "state": result})
    return 0


def command_consume_budget(args: argparse.Namespace) -> int:
    increments = json.loads(args.increments)
    result = update_counters(Path(args.workspace), increments)
    emit(result)
    return 0


def command_competitors(args: argparse.Namespace) -> int:
    local = []
    for item in args.local_repo or []:
        parts = item.split("=", 2)
        if len(parts) != 3:
            raise ValueError("--local-repo must be slug=path=category")
        local.append((parts[0], Path(parts[1]), parts[2]))
    result = build_competitor_dataset(
        Path(args.target), Path(args.workspace), args.seed or [], explicit_queries=args.query or None,
        token=__import__("os").environ.get("GITHUB_TOKEN", ""), max_candidates=args.max_candidates,
        timeout=args.timeout, offline=args.offline, local_repositories=local,
        supplementary_records=load_supplementary_records(Path(args.supplementary) if args.supplementary else None),
        min_remote_github=args.min_remote_github,
    )
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_inspect_repo(args: argparse.Namespace) -> int:
    result = inspect_repository(Path(args.path), source_slug=args.slug or "", resolved_commit=args.commit or "")
    if args.output:
        from wbi_core.io import write_json
        write_json(Path(args.output), result)
    emit({"status": "PASS", "inspection": result})
    return 0


def command_freshness(args: argparse.Namespace) -> int:
    result = build_freshness_scan(Path(args.records), Path(args.output_dir), args.valid_as_of, args.validity_days)
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_reheat_status(args: argparse.Namespace) -> int:
    result = reheat_status(Path(args.scan), args.now or "")
    emit(result)
    return 0 if result["status"] == "CURRENT" else 3


def command_seal_research(args: argparse.Namespace) -> int:
    result = seal_research(Path(args.workspace), args.actor_id)
    emit(result)
    return 0 if result["status"] == "SEALED" else 2


def command_luban_gate(args: argparse.Namespace) -> int:
    result = validate_luban_gates(Path(args.workspace))
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_seal_eval(args: argparse.Namespace) -> int:
    result = seal_eval_contract(Path(args.workspace), Path(args.contract), args.actor_id)
    emit(result)
    return 0 if result.get("status") == "SEALED" else 2


def command_evaluate(args: argparse.Namespace) -> int:
    result = evaluate_workspace(Path(args.workspace), Path(args.results) if args.results else None)
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_authority_init(args: argparse.Namespace) -> int:
    result = write_default_authority(Path(args.workspace))
    emit({"status": "PASS", "authority": result})
    return 0


def command_authority_check(args: argparse.Namespace) -> int:
    result = validate_authority(Path(args.workspace))
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_classify_action(args: argparse.Namespace) -> int:
    authority = json.loads(Path(args.authority).read_text(encoding="utf-8"))
    result = classify_action(args.action, authority, args.explicit_authorization)
    emit(result)
    return 0 if result["status"].startswith("AUTHORIZED") else 2


def command_review_plan(args: argparse.Namespace) -> int:
    result = generate_review_plan(Path(args.workspace), Path(args.evidence_index), args.actor_id)
    emit({"status": "PASS", "plan": result})
    return 0


def command_collect_review(args: argparse.Namespace) -> int:
    result = collect_review(Path(args.workspace), Path(args.record))
    emit(result)
    return 0 if result["status"] == "RECORDED" else 2


def command_review_gate(args: argparse.Namespace) -> int:
    result = review_gate(Path(args.workspace))
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_gate(args: argparse.Namespace) -> int:
    result = gate_workspace(Path(args.workspace), args.as_of or "")
    if args.output:
        from wbi_core.io import write_json
        write_json(Path(args.output), result)
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_install(args: argparse.Namespace) -> int:
    result = install_archive(
        Path(args.archive), Path(args.skills_root), args.expected_genesis_hash or "", args.replace,
        profile=args.profile, verification_level=args.verification_level,
        expected_archive_sha256=args.expected_archive_sha256 or "",
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "",
    )
    if args.result_file:
        from wbi_core.io import write_json
        write_json(Path(args.result_file), result)
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_install_status(args: argparse.Namespace) -> int:
    result = inspect_install_transaction(
        Path(args.skills_root), args.transaction_id or "", verify_installed=args.verify_installed,
        expected_genesis_hash=args.expected_genesis_hash or "",
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "", profile=args.profile,
    )
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_recover_install(args: argparse.Namespace) -> int:
    result = recover_install_transactions(
        Path(args.skills_root), args.expected_genesis_hash or "", args.profile, args.destination_name,
        expected_effective_genesis_hash=args.expected_effective_genesis_hash or "",
    )
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_rollback_install(args: argparse.Namespace) -> int:
    result = rollback_install(Path(args.destination), Path(args.backup))
    emit(result)
    return 0 if result["status"] == "PASS" else 2


def command_receipt(args: argparse.Namespace) -> int:
    gate_result = json.loads(Path(args.gate_result).read_text(encoding="utf-8")) if args.gate_result else None
    install_result = json.loads(Path(args.install_result).read_text(encoding="utf-8")) if args.install_result else None
    result = generate_release_receipt(
        Path(args.skill_dir), Path(args.archive), Path(args.output), Path(args.workspace) if args.workspace else None,
        gate_result, install_result, args.expected_genesis_hash or "",
        args.expected_effective_genesis_hash or "",
    )
    status = result.get("receipt_status", "FAIL")
    emit({"status": status, "receipt": result})
    return 0 if status == "PASS" else 2


def command_status_validate(args: argparse.Namespace) -> int:
    result = validate_status_file(Path(args.summary), Path(args.output) if args.output else None)
    emit(result)
    return 0 if result["validation_status"] == "PASS" else 2


def command_telemetry_aggregate(args: argparse.Namespace) -> int:
    result = aggregate_file(Path(args.input), Path(args.output) if args.output else None)
    emit(result)
    return 0 if result.get("aggregation_status") == "PASS" else 2


def command_benchmark_seal(args: argparse.Namespace) -> int:
    result = seal_benchmark_contract(Path(args.workspace), Path(args.contract), args.actor_id, optimizer_root=SKILL_ROOT)
    emit(result)
    return 0 if result.get("seal_status") == "SEALED" else 2


def command_benchmark_evaluate(args: argparse.Namespace) -> int:
    result = evaluate_benchmark(Path(args.workspace), Path(args.results))
    emit(result)
    return 0 if result.get("benchmark_integrity_status") == "VALID" else 2


def command_review_adapter_check(args: argparse.Namespace) -> int:
    result = inspect_review_adapter(
        Path(args.contract), workspace=Path(args.workspace), target=Path(args.target), optimizer_root=SKILL_ROOT,
        bundled_root=SKILL_ROOT,
        attestation_path=Path(args.attestation) if args.attestation else None,
        packet_index_path=Path(args.packet_index) if args.packet_index else None,
        output=Path(args.output) if args.output else None,
    )
    emit(result)
    return 0 if result.get("adapter_contract_status") == "PASS" else 2



def command_doctor(args: argparse.Namespace) -> int:
    """Compatibility doctor: target diagnosis when target is supplied, otherwise environment readiness."""
    if getattr(args, "target", None):
        result = diagnose_target(
            Path(args.target), valid_as_of=args.valid_as_of,
            output=Path(args.output) if args.output else None,
            max_files=args.max_files, max_text_bytes=args.max_text_bytes,
        )
        emit(result)
        return 0 if result.get("diagnostic_status") != "BLOCKED" else 2
    if not getattr(args, "workspace", None):
        raise ValueError("doctor requires either a target or --workspace")
    result = run_environment_doctor(
        Path(args.workspace), Path(args.output) if args.output else None,
        Path(args.review_contract) if args.review_contract else None,
        Path(args.persona_index) if args.persona_index else None,
    )
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_adaptive_plan(args: argparse.Namespace) -> int:
    result = build_adaptive_plan_file(
        Path(args.diagnostic), run_mode=args.run_mode,
        output=Path(args.output) if args.output else None,
    )
    emit(result)
    return 0 if result.get("plan_status") == "READY" else 2


def command_strategy_update(args: argparse.Namespace) -> int:
    result = update_strategy_memory(Path(args.workspace), Path(args.record))
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_strategy_next(args: argparse.Namespace) -> int:
    result = inspect_strategy_memory(Path(args.workspace))
    emit(result)
    return 0 if result.get("status") in {"PASS", "NOT_INITIALIZED"} else 2


def command_showcase(args: argparse.Namespace) -> int:
    result = generate_showcase(
        Path(args.status), Path(args.output),
        comparison_path=Path(args.comparison) if args.comparison else None,
        title=args.title,
    )
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_market_profile(args: argparse.Namespace) -> int:
    result = build_market_profile(Path(args.target), valid_as_of=args.valid_as_of or "")
    if args.output:
        from wbi_core.io import write_json
        write_json(Path(args.output), result)
    emit(result)
    return 0 if result.get("profile_status") == "PASS" else 2


def command_environment_snapshot(args: argparse.Namespace) -> int:
    result = capture_environment_snapshot(
        Path(args.target), Path(args.optimizer), valid_as_of=args.valid_as_of,
        timezone_name=args.timezone, validity_days=args.validity_days,
        frontier_scan=Path(args.frontier_scan) if args.frontier_scan else None,
        benchmark_summary=Path(args.benchmark_summary) if args.benchmark_summary else None,
        coverage_summary=Path(args.coverage_summary) if args.coverage_summary else None,
        shadowing_summary=Path(args.shadowing_summary) if args.shadowing_summary else None,
        runtime_capabilities=Path(args.runtime_capabilities) if args.runtime_capabilities else None,
        output=Path(args.output) if args.output else None,
    )
    emit(result)
    return 0 if result.get("snapshot_status") == "PASS" else 2


def command_environment_attest(args: argparse.Namespace) -> int:
    result = attest_environment_strength(
        Path(args.snapshot), Path(args.candidate_set),
        output=Path(args.output) if args.output else None,
        checked_at=args.checked_at or "",
    )
    emit(result)
    return 0 if result.get("environment_strength_status") == "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT" else 3


def command_coverage_evaluate(args: argparse.Namespace) -> int:
    result = evaluate_skill_coverage(
        Path(args.constraints), Path(args.trajectories),
        output=Path(args.output) if args.output else None,
        minimum_overall_coverage=args.minimum_overall_coverage,
        minimum_hard_coverage=args.minimum_hard_coverage,
    )
    emit(result)
    return 0 if result.get("coverage_status") == "PASS" else 3


def command_shadowing_evaluate(args: argparse.Namespace) -> int:
    result = evaluate_skill_shadowing(
        Path(args.records), output=Path(args.output) if args.output else None,
        minimum_top1_accuracy=args.minimum_top1_accuracy,
        maximum_false_activation_rate=args.maximum_false_activation_rate,
        maximum_outcome_drop=args.maximum_outcome_drop,
    )
    emit(result)
    return 0 if result.get("shadowing_status") == "PASS" else 3


def command_stochastic_compare(args: argparse.Namespace) -> int:
    result = compare_stochastic_results(
        Path(args.results), baseline_id=args.baseline_id, candidate_id=args.candidate_id,
        minimum_trials=args.minimum_trials, minimum_effect=args.minimum_effect,
        output=Path(args.output) if args.output else None,
    )
    emit(result)
    return 0 if result.get("stochastic_decision") == "SUPPORTED" else 3

def command_optimize(args: argparse.Namespace) -> int:
    target = Path(args.target)
    workspace = Path(args.workspace)
    result = init_orchestration(
        target, workspace, SKILL_ROOT,
        run_mode=args.run_mode, package_profile=args.package_profile,
        verification_level=args.verification_level, valid_as_of=args.valid_as_of,
        review_contract=Path(args.review_attestation_contract) if args.review_attestation_contract else None,
    )
    if result.get("preflight_artifacts"):
        result = inspect_orchestration(workspace)
        emit(result)
        return 0 if result.get("orchestration_status") != "BLOCKED" else 2
    control = workspace.resolve() / "control"
    diagnostic_path = control / "target-diagnostic.json"
    plan_path = control / "adaptive-plan.json"
    diagnostic = diagnose_target(
        target, valid_as_of=args.valid_as_of, output=diagnostic_path,
        max_files=args.max_files, max_text_bytes=args.max_text_bytes,
    )
    build_adaptive_plan(diagnostic, run_mode=args.run_mode, output=plan_path)
    result = attach_preflight(workspace, diagnostic_path, plan_path)
    result["diagnostic_status"] = diagnostic.get("diagnostic_status")
    result["target_class"] = diagnostic.get("classification", {}).get("target_class")
    emit(result)
    return 0 if result.get("orchestration_status") != "BLOCKED" else 2

def command_run_status(args: argparse.Namespace) -> int:
    result = inspect_orchestration(Path(args.workspace))
    emit(result)
    return 0 if result.get("orchestration_status") not in {"BLOCKED", "NOT_INITIALIZED"} else 2


def command_resume(args: argparse.Namespace) -> int:
    result = inspect_orchestration(Path(args.workspace))
    emit(result)
    return 0 if result.get("orchestration_status") not in {"BLOCKED", "NOT_INITIALIZED"} else 2


def command_explain_block(args: argparse.Namespace) -> int:
    result = explain_block(Path(args.workspace))
    emit(result)
    return 0


def command_mark_step(args: argparse.Namespace) -> int:
    result = mark_step(Path(args.workspace), args.step, Path(args.receipt))
    emit(result)
    return 0 if result.get("orchestration_status") != "BLOCKED" else 2


def command_review_ablation(args: argparse.Namespace) -> int:
    result = evaluate_review_ablation_file(Path(args.study), Path(args.output) if args.output else None)
    emit(result)
    return 0 if result.get("ablation_integrity_status") == "VALID" else 2


def command_portability_evaluate(args: argparse.Namespace) -> int:
    result = evaluate_portability_file(
        Path(args.workspace), Path(args.contract), Path(args.results),
        Path(args.output) if args.output else None,
    )
    emit(result)
    return 0 if result.get("portability_integrity_status") == "VALID" else 2


def command_peer_audit(args: argparse.Namespace) -> int:
    result = audit_peer_file(Path(args.input), Path(args.output) if args.output else None)
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_utility_gate(args: argparse.Namespace) -> int:
    result = evaluate_utility_file(Path(args.contract), Path(args.output) if args.output else None)
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_environment_doctor(args: argparse.Namespace) -> int:
    result = run_environment_doctor(
        Path(args.workspace), Path(args.output) if args.output else None,
        Path(args.review_contract) if args.review_contract else None,
        Path(args.persona_index) if args.persona_index else None,
    )
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_verifier_export(args: argparse.Namespace) -> int:
    result = export_verifier_packet(
        Path(args.subject), Path(args.output), args.valid_as_of,
        Path(args.acceptance_contract) if args.acceptance_contract else None,
    )
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_expert_panel_export(args: argparse.Namespace) -> int:
    result = export_expert_panel_request(
        Path(args.output), args.task, args.valid_as_of,
        Path(args.persona_index) if args.persona_index else None,
    )
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def command_render_dashboard(args: argparse.Namespace) -> int:
    result = render_dashboard_file(Path(args.input), Path(args.output))
    emit(result)
    return 0 if result.get("status") == "PASS" else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wbi", description="Teleiosis / 白箱迭代Skill")
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("verify-self", help="verify Genesis, package structure, version consistency and manifest")
    item.add_argument("--skill-root")
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--strict", action="store_true")
    item.set_defaults(func=command_verify_self)

    item = sub.add_parser("validate", help="validate a Skill package")
    item.add_argument("skill_dir")
    item.add_argument("--strict", action="store_true")
    item.add_argument("--ignore-manifest", action="store_true")
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--profile", choices=["auto", "generic", "optimizer"], default="auto")
    item.set_defaults(func=command_validate)

    item = sub.add_parser("manifest", help="generate MANIFEST.sha256 and validate")
    item.add_argument("skill_dir")
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--profile", choices=["auto", "generic", "optimizer"], default="auto")
    item.set_defaults(func=command_manifest)

    item = sub.add_parser("package", help="deterministically package and post-extract validate a Skill")
    item.add_argument("skill_dir")
    item.add_argument("--output", required=True)
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--profile", choices=["auto", "generic", "optimizer"], default="auto")
    item.add_argument("--verification-level", choices=["structural", "release", "deep"], default="release")
    item.set_defaults(func=command_package)

    item = sub.add_parser("init-run", help="freeze baseline and create an external multi-candidate white-box workspace")
    item.add_argument("target")
    item.add_argument("--workspace", required=True)
    item.add_argument("--strategy", action="append", help="open, portable lane identifier such as incremental, pareto-population or coevolution")
    item.add_argument("--budget")
    item.add_argument("--release-profile", default="auto", help="built-in profile or an open custom profile identifier")
    item.add_argument("--release-profile-contract", help="frozen JSON contract required for a custom release profile")
    item.add_argument("--review-attestation-contract", help="frozen external runtime adapter contract required for formal 2x6 review attestation")
    item.add_argument("--valid-as-of", help="authoritative local task date in YYYY-MM-DD; preferred for formal runs")
    item.add_argument("--timezone", default="", help="IANA timezone used only when --valid-as-of is omitted")
    item.add_argument("--self-evolve", action="store_true")
    item.set_defaults(func=command_init_run)

    item = sub.add_parser("record-change", help="record a candidate change with exact diff and rollback snapshot")
    item.add_argument("workspace")
    item.add_argument("--candidate-id", required=True)
    item.add_argument("--record", required=True)
    item.set_defaults(func=command_record_change)

    item = sub.add_parser("record-round", help="record one system-review perspective")
    item.add_argument("workspace")
    item.add_argument("--record", required=True)
    item.set_defaults(func=command_record_round)

    item = sub.add_parser("loop-status", help="evaluate finite-run budgets and saturation")
    item.add_argument("workspace")
    item.set_defaults(func=command_loop_status)

    item = sub.add_parser("transition", help="perform an explicit state transition")
    item.add_argument("workspace")
    item.add_argument("status")
    item.add_argument("--reason", required=True)
    item.add_argument("--actor-id", required=True)
    item.set_defaults(func=command_transition)

    item = sub.add_parser("consume-budget", help="record observed network/eval/model/token/cost counters")
    item.add_argument("workspace")
    item.add_argument("--increments", required=True, help='JSON object, e.g. {"tokens":1000}')
    item.set_defaults(func=command_consume_budget)

    item = sub.add_parser("competitors", help="discover, safely pull, pin and statically evaluate real GitHub peers")
    item.add_argument("--target", required=True)
    item.add_argument("--workspace", required=True)
    item.add_argument("--seed", action="append")
    item.add_argument("--query", action="append")
    item.add_argument("--local-repo", action="append", help="test-only slug=path=category")
    item.add_argument("--supplementary", help="JSONL product-live or artifact-bundle records")
    item.add_argument("--max-candidates", type=int, default=20)
    item.add_argument("--min-remote-github", type=int, default=1)
    item.add_argument("--timeout", type=int, default=180)
    item.add_argument("--offline", action="store_true")
    item.set_defaults(func=command_competitors)

    item = sub.add_parser("inspect-repo", help="perform bounded static no-exec repository inspection")
    item.add_argument("path")
    item.add_argument("--slug")
    item.add_argument("--commit")
    item.add_argument("--output")
    item.set_defaults(func=command_inspect_repo)

    item = sub.add_parser("market-profile", help="classify target and emit market/adoption mechanism lanes")
    item.add_argument("target")
    item.add_argument("--valid-as-of")
    item.add_argument("--output")
    item.set_defaults(func=command_market_profile)

    item = sub.add_parser("peer-audit", help="separate real market peers from method references and engineering analogies")
    item.add_argument("--input", required=True, help="JSON, records JSON, or JSONL peer evidence")
    item.add_argument("--output")
    item.set_defaults(func=command_peer_audit)

    item = sub.add_parser("utility-gate", help="keep, revert, or fall back to baseline using non-compensatory utility evidence")
    item.add_argument("--contract", required=True)
    item.add_argument("--output")
    item.set_defaults(func=command_utility_gate)

    item = sub.add_parser("doctor", help="run target diagnosis or environment readiness without executing target code")
    item.add_argument("target", nargs="?")
    item.add_argument("--workspace")
    item.add_argument("--valid-as-of")
    item.add_argument("--review-contract")
    item.add_argument("--persona-index")
    item.add_argument("--output")
    item.add_argument("--max-files", type=int, default=5000)
    item.add_argument("--max-text-bytes", type=int, default=8 * 1024 * 1024)
    item.set_defaults(func=command_doctor)

    item = sub.add_parser("environment-doctor", help="diagnose engineering and formal runtime capabilities without exposing secrets")
    item.add_argument("--workspace", required=True)
    item.add_argument("--review-contract")
    item.add_argument("--persona-index")
    item.add_argument("--output")
    item.set_defaults(func=command_environment_doctor)

    item = sub.add_parser("adaptive-plan", help="derive a bounded candidate portfolio, gates and budget from a target diagnosis")
    item.add_argument("--diagnostic", required=True)
    item.add_argument("--run-mode", choices=["diagnostic", "engineering", "formal"], default="engineering")
    item.add_argument("--output")
    item.set_defaults(func=command_adaptive_plan)

    item = sub.add_parser("verifier-export", help="export a sealed read-only acceptance packet for the external verifier Skill")
    item.add_argument("--subject", required=True)
    item.add_argument("--output", required=True)
    item.add_argument("--valid-as-of", required=True)
    item.add_argument("--acceptance-contract")
    item.set_defaults(func=command_verifier_export)

    item = sub.add_parser("expert-panel-export", help="export isolated role requirements for persona-distiller-group routing")
    item.add_argument("--output", required=True)
    item.add_argument("--task", required=True)
    item.add_argument("--valid-as-of", required=True)
    item.add_argument("--persona-index")
    item.set_defaults(func=command_expert_panel_export)

    item = sub.add_parser("render-dashboard", help="render a static dependency-free cyan-blue evidence console")
    item.add_argument("--input", required=True)
    item.add_argument("--output", required=True)
    item.set_defaults(func=command_render_dashboard)

    item = sub.add_parser("freshness-scan", help="freeze a dated, categorized current-technology source scan")
    item.add_argument("--records", required=True)
    item.add_argument("--output-dir", required=True)
    item.add_argument("--valid-as-of", required=True)
    item.add_argument("--validity-days", type=int, default=30)
    item.set_defaults(func=command_freshness)

    item = sub.add_parser("reheat-status", help="determine whether a freshness scan has expired")
    item.add_argument("--scan", required=True)
    item.add_argument("--now")
    item.set_defaults(func=command_reheat_status)

    item = sub.add_parser("seal-research", help="freeze read-only research evidence before candidate mutation")
    item.add_argument("workspace")
    item.add_argument("--actor-id", required=True)
    item.set_defaults(func=command_seal_research)

    item = sub.add_parser("luban-gate", help="validate premise, five peers, ecosystem, live artifacts, release and reheat")
    item.add_argument("workspace")
    item.set_defaults(func=command_luban_gate)

    item = sub.add_parser("seal-eval", help="freeze the evaluation contract outside every candidate")
    item.add_argument("workspace")
    item.add_argument("--contract", required=True)
    item.add_argument("--actor-id", required=True)
    item.set_defaults(func=command_seal_eval)

    item = sub.add_parser("evaluate", help="validate raw results and compare baseline/candidates with hard gates and Pareto selection")
    item.add_argument("workspace")
    item.add_argument("--results")
    item.set_defaults(func=command_evaluate)

    item = sub.add_parser("authority-init", help="create the run-scoped Full Permission Bypass authority contract")
    item.add_argument("workspace")
    item.set_defaults(func=command_authority_init)

    item = sub.add_parser("authority-check", help="verify authority, untrusted input, sandbox and secret boundaries")
    item.add_argument("workspace")
    item.set_defaults(func=command_authority_check)

    item = sub.add_parser("classify-action", help="classify whether a requested action is already authorized")
    item.add_argument("--authority", required=True)
    item.add_argument("--action", required=True)
    item.add_argument("--explicit-authorization", action="store_true")
    item.set_defaults(func=command_classify_action)

    item = sub.add_parser("review-plan", help="generate two sealed panels of six independent review packets")
    item.add_argument("workspace")
    item.add_argument("--evidence-index", required=True)
    item.add_argument("--actor-id", default="stable-optimizer")
    item.set_defaults(func=command_review_plan)

    item = sub.add_parser("collect-review", help="validate and store one provider-identifiable independent review")
    item.add_argument("workspace")
    item.add_argument("--record", required=True)
    item.set_defaults(func=command_collect_review)

    item = sub.add_parser("review-gate", help="enforce 2x6 independence and a distinct read-only final verifier")
    item.add_argument("workspace")
    item.set_defaults(func=command_review_gate)

    item = sub.add_parser("gate", help="run the complete Genesis-conformant promotion gate")
    item.add_argument("workspace")
    item.add_argument("--as-of")
    item.add_argument("--output")
    item.set_defaults(func=command_gate)

    item = sub.add_parser("install", help="atomically install or back up and replace a verified Skill archive")
    item.add_argument("archive")
    item.add_argument("--skills-root", required=True)
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--expected-archive-sha256", help="external SHA-256 trust anchor; required for release/deep optimizer installation")
    item.add_argument("--profile", choices=["auto", "generic", "optimizer"], default="auto")
    item.add_argument("--verification-level", choices=["structural", "release", "deep"], default="release")
    item.add_argument("--replace", action="store_true")
    item.add_argument("--result-file", help="atomically persist the CLI result outside stdout")
    item.set_defaults(func=command_install)

    item = sub.add_parser("install-status", help="inspect the latest or a named durable install transaction")
    item.add_argument("--skills-root", required=True)
    item.add_argument("--transaction-id")
    item.add_argument("--verify-installed", action="store_true")
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--profile", choices=["auto", "generic", "optimizer"], default="auto")
    item.set_defaults(func=command_install_status)

    item = sub.add_parser("recover-install", help="reconcile interrupted installs from durable transaction receipts")
    item.add_argument("--skills-root", required=True)
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.add_argument("--profile", choices=["auto", "generic", "optimizer"], default="auto")
    item.add_argument("--destination-name", default="teleiosis")
    item.set_defaults(func=command_recover_install)

    item = sub.add_parser("rollback-install", help="restore an atomic installer backup")
    item.add_argument("--destination", required=True)
    item.add_argument("--backup", required=True)
    item.set_defaults(func=command_rollback_install)

    item = sub.add_parser("release-receipt", help="write an external machine-readable artifact/provenance receipt")
    item.add_argument("--skill-dir", required=True)
    item.add_argument("--archive", required=True)
    item.add_argument("--output", required=True)
    item.add_argument("--workspace")
    item.add_argument("--gate-result")
    item.add_argument("--install-result")
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.set_defaults(func=command_receipt)

    item = sub.add_parser("release-smoke", help="run the bounded non-recursive installation-safe verification profile")
    item.add_argument("--expected-genesis-hash")
    item.add_argument("--expected-effective-genesis-hash")
    item.set_defaults(func=command_release_smoke)

    item = sub.add_parser("self-test", help="run the bundled regression suite with a hard timeout")
    item.add_argument("--timeout", type=int, default=300)
    item.set_defaults(func=command_self_test)


    item = sub.add_parser("status-validate", help="validate the eight-domain status model and semantic transitions")
    item.add_argument("--summary", required=True)
    item.add_argument("--output")
    item.set_defaults(func=command_status_validate)

    item = sub.add_parser("telemetry-aggregate", help="aggregate invocation-level token, cost, latency and human burden evidence")
    item.add_argument("--input", required=True)
    item.add_argument("--output")
    item.set_defaults(func=command_telemetry_aggregate)

    item = sub.add_parser("benchmark-seal", help="freeze the Track A/B/C equal-budget benchmark contract before mutation")
    item.add_argument("workspace")
    item.add_argument("--contract", required=True)
    item.add_argument("--actor-id", required=True)
    item.set_defaults(func=command_benchmark_seal)

    item = sub.add_parser("benchmark-evaluate", help="validate benchmark results, budgets, negative transfer and outcome claims")
    item.add_argument("workspace")
    item.add_argument("--results", required=True)
    item.set_defaults(func=command_benchmark_evaluate)

    item = sub.add_parser("review-adapter-check", help="validate an external 2x6+1 attestation contract without trusting bundled examples")
    item.add_argument("--contract", required=True)
    item.add_argument("--workspace", required=True)
    item.add_argument("--target", required=True)
    item.add_argument("--attestation")
    item.add_argument("--packet-index")
    item.add_argument("--output")
    item.set_defaults(func=command_review_adapter_check)

    item = sub.add_parser("optimize", help="initialize a durable diagnostic, engineering or formal orchestration run")
    item.add_argument("target")
    item.add_argument("--workspace", required=True)
    item.add_argument("--run-mode", choices=["diagnostic", "engineering", "formal"], default="engineering")
    item.add_argument("--package-profile", default="optimizer")
    item.add_argument("--verification-level", choices=["fast", "release", "deep"], default="release")
    item.add_argument("--valid-as-of", required=True)
    item.add_argument("--review-attestation-contract")
    item.add_argument("--max-files", type=int, default=5000)
    item.add_argument("--max-text-bytes", type=int, default=8 * 1024 * 1024)
    item.set_defaults(func=command_optimize)

    item = sub.add_parser("run-status", help="inspect durable orchestration state and frozen receipt bindings")
    item.add_argument("workspace")
    item.set_defaults(func=command_run_status)

    item = sub.add_parser("resume", help="report the next immutable step without changing run identity")
    item.add_argument("workspace")
    item.set_defaults(func=command_resume)

    item = sub.add_parser("explain-block", help="explain blocked capabilities and safe resolution")
    item.add_argument("workspace")
    item.set_defaults(func=command_explain_block)


    item = sub.add_parser("strategy-update", help="append one evidence-bound KEEP/REVERT/NO_CHANGE event to tamper-evident strategy memory")
    item.add_argument("workspace")
    item.add_argument("--record", required=True)
    item.set_defaults(func=command_strategy_update)

    item = sub.add_parser("strategy-next", help="inspect rejected edits, oscillation and the next bounded strategy")
    item.add_argument("workspace")
    item.set_defaults(func=command_strategy_next)

    item = sub.add_parser("showcase", help="generate a truthful self-contained HTML evidence card from frozen status data")
    item.add_argument("--status", required=True)
    item.add_argument("--comparison")
    item.add_argument("--output", required=True)
    item.add_argument("--title", default="Teleiosis Evidence Card")
    item.set_defaults(func=command_showcase)

    item = sub.add_parser("environment-snapshot", help="freeze the current authorized environment and frontier evidence lease")
    item.add_argument("--target", required=True)
    item.add_argument("--optimizer", required=True)
    item.add_argument("--valid-as-of", required=True)
    item.add_argument("--timezone", default="Australia/Sydney")
    item.add_argument("--validity-days", type=int, default=30)
    item.add_argument("--frontier-scan")
    item.add_argument("--benchmark-summary")
    item.add_argument("--coverage-summary")
    item.add_argument("--shadowing-summary")
    item.add_argument("--runtime-capabilities")
    item.add_argument("--output")
    item.set_defaults(func=command_environment_snapshot)

    item = sub.add_parser("environment-attest", help="issue a bounded current-environment Pareto attestation or truthful non-proof status")
    item.add_argument("--snapshot", required=True)
    item.add_argument("--candidate-set", required=True)
    item.add_argument("--checked-at")
    item.add_argument("--output")
    item.set_defaults(func=command_environment_attest)

    item = sub.add_parser("coverage-evaluate", help="measure declared Skill behavior coverage from recorded trajectories")
    item.add_argument("--constraints", required=True)
    item.add_argument("--trajectories", required=True)
    item.add_argument("--minimum-overall-coverage", type=float, default=0.80)
    item.add_argument("--minimum-hard-coverage", type=float, default=1.0)
    item.add_argument("--output")
    item.set_defaults(func=command_coverage_evaluate)

    item = sub.add_parser("shadowing-evaluate", help="measure Skill selection, false activation and library-scale shadowing risk")
    item.add_argument("--records", required=True)
    item.add_argument("--minimum-top1-accuracy", type=float, default=0.90)
    item.add_argument("--maximum-false-activation-rate", type=float, default=0.05)
    item.add_argument("--maximum-outcome-drop", type=float, default=0.02)
    item.add_argument("--output")
    item.set_defaults(func=command_shadowing_evaluate)

    item = sub.add_parser("stochastic-compare", help="apply a predeclared interval rule instead of cherry-picking stochastic trials")
    item.add_argument("--results", required=True)
    item.add_argument("--baseline-id", required=True)
    item.add_argument("--candidate-id", required=True)
    item.add_argument("--minimum-trials", type=int, default=20)
    item.add_argument("--minimum-effect", type=float, default=0.0)
    item.add_argument("--output")
    item.set_defaults(func=command_stochastic_compare)

    item = sub.add_parser("review-ablation", help="measure the marginal findings, correlation and cost of 2/6/12 reviewers")
    item.add_argument("--study", required=True)
    item.add_argument("--output")
    item.set_defaults(func=command_review_ablation)

    item = sub.add_parser("portability-evaluate", help="evaluate a frozen runtime by model-family transfer matrix")
    item.add_argument("workspace")
    item.add_argument("--contract", required=True)
    item.add_argument("--results", required=True)
    item.add_argument("--output")
    item.set_defaults(func=command_portability_evaluate)

    item = sub.add_parser("mark-step", help="advance orchestration only after binding an immutable step receipt")
    item.add_argument("workspace")
    item.add_argument("--step", required=True)
    item.add_argument("--receipt", required=True)
    item.set_defaults(func=command_mark_step)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        emit({"status": "BLOCKED", "completed": False, "error_type": "KeyboardInterrupt", "error": "operation interrupted"})
        return 130
    except Exception as exc:
        emit({
            "status": "BLOCKED", "completed": False,
            "error_type": type(exc).__name__, "error": str(exc),
            "remediation": "Inspect the supplied path, contract and evidence; no PASS was recorded.",
        })
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
