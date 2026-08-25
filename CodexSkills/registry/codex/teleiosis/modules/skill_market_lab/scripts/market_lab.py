#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from marketlab.common import (  # noqa: E402
    MarketLabError,
    ValidationError,
    iter_jsonl,
    object_sha256,
    read_json,
    strip_internal_fields,
    utc_now,
    write_json,
    write_jsonl,
)
from marketlab.experiments import (  # noqa: E402
    initialize_workspace,
    make_candidate_visible_dataset,
    make_holdout_manifest,
    write_assignments,
)
from marketlab.integrity import load_and_verify_tree, seal_tree  # noqa: E402
from marketlab.metrics import (  # noqa: E402
    aggregate_evidence,
    build_next_iteration_plan,
    decide_gate,
)
from marketlab.privacy import anonymize_feedback_file  # noqa: E402
from marketlab.specs import (  # noqa: E402
    assert_valid,
    validate_competitor_registry,
    validate_experiment_spec,
    validate_feedback,
    validate_result,
    validate_task,
)
from marketlab.stress import STRESS_CATEGORIES, expand_to_jsonl  # noqa: E402


SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_TEMPLATE = SKILL_ROOT / "assets" / "templates" / "experiment_spec.json"


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _load_spec(path: Path) -> Dict[str, Any]:
    spec = read_json(path)
    assert_valid(validate_experiment_spec(spec), "实验规范")
    return spec


def _validate_jsonl(path: Path, validator, context_name: str, arm_ids: Sequence[str] | None = None) -> Dict[str, Any]:
    count = 0
    errors: List[str] = []
    for row in iter_jsonl(path):
        clean = strip_internal_fields(row)
        row_errors = validator(clean, arm_ids) if arm_ids is not None else validator(clean)
        if row_errors:
            line = row.get("_source_line", "?")
            errors.extend(f"{path}:{line}: {item}" for item in row_errors)
        count += 1
    if errors:
        raise ValidationError(f"{context_name} 验证失败:\n" + "\n".join(f"- {item}" for item in errors))
    return {"valid": True, "records": count, "path": str(path)}


def _render_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Skill Market Lab 实验证据汇总",
        "",
        f"- experiment_id: `{summary['experiment_id']}`",
        f"- evidence: `{summary['evidence_level_label']}`",
        f"- records_total: `{summary['records_total']}`",
        f"- subject: `{summary['subject']['skill_name']}@{summary['subject']['skill_version']}`",
        "",
        "## 实验臂",
        "",
        "| Arm | 类型 | 记录 | 成功率 | 平均评分 | 平均成本 USD | 平均时延 ms |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for arm_id, arm in summary["arms"].items():
        lines.append(
            "| {id} | {kind} | {records} | {success} | {score} | {cost} | {latency} |".format(
                id=arm_id,
                kind=arm["kind"],
                records=arm["records"],
                success="—" if arm["success_rate"] is None else f"{arm['success_rate']:.3f}",
                score="—" if arm["mean_score"] is None else f"{arm['mean_score']:.3f}",
                cost="—" if arm["mean_cost_usd"] is None else f"{arm['mean_cost_usd']:.4f}",
                latency="—" if arm["mean_latency_ms"] is None else f"{arm['mean_latency_ms']:.1f}",
            )
        )
    lines.extend(["", "## Candidate 配对差异", ""])
    for comparator_id, pair in summary["candidate_pairs"].items():
        lines.extend(
            [
                f"### vs `{comparator_id}`",
                "",
                f"- paired_tasks: `{pair['paired_tasks']}`",
                f"- success_delta: `{pair['success_delta']['mean']}`; 95% CI `[{pair['success_delta']['low']}, {pair['success_delta']['high']}]`",
                f"- score_delta: `{pair['score_delta']['mean']}`; 95% CI `[{pair['score_delta']['low']}, {pair['score_delta']['high']}]`",
                f"- cost_increase_ratio: `{pair['cost_increase_ratio']}`",
                f"- latency_increase_ratio: `{pair['latency_increase_ratio']}`",
                "",
            ]
        )
    market = summary["market"]
    lines.extend(
        [
            "## 真实市场证据",
            "",
            f"- events_total: `{market['event_count']}`",
            f"- sources: `{json.dumps(market['source_counts'], ensure_ascii=False, sort_keys=True)}`",
            f"- identity_mismatch: `{market['feedback_identity_mismatch_count']}`",
            f"- orphan_run: `{market['feedback_orphan_run_count']}`",
            f"- high_or_critical_incidents_total: `{market['critical_or_high_incidents_total']}`",
            "",
            "| Arm | 事件 | 完成率 | 接受率 | 再用意愿 | 平均人工修改秒 | 付费价值 USD | 最高证据 |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for arm_id, item in market["by_arm"].items():
        lines.append(
            "| {arm} | {events} | {completion} | {acceptance} | {reuse} | {edit} | {paid} | {level} |".format(
                arm=arm_id,
                events=item["event_count"],
                completion="—" if item["completion_rate"] is None else f"{item['completion_rate']:.3f}",
                acceptance="—" if item["acceptance_rate"] is None else f"{item['acceptance_rate']:.3f}",
                reuse="—" if item["reuse_intent_rate"] is None else f"{item['reuse_intent_rate']:.3f}",
                edit="—" if item["mean_human_edit_seconds"] is None else f"{item['mean_human_edit_seconds']:.1f}",
                paid=f"{item['total_paid_value_usd']:.2f}",
                level=item["max_evidence_label"],
            )
        )
    comparison = market["primary_comparison"]
    lines.extend(
        [
            "",
            "### Candidate 与主 Comparator 的市场因果对照",
            "",
            f"- comparator: `{comparison['comparator_id']}`",
            f"- events: candidate `{comparison['candidate_events']}` / comparator `{comparison['comparator_events']}`",
            f"- paired_market_tasks: `{comparison['paired_market_tasks']}`",
            f"- comparable_evidence: `{comparison['comparable_evidence_label']}`",
            f"- completion_delta: `{comparison['completion_delta']['mean']}`",
            f"- acceptance_delta: `{comparison['acceptance_delta']['mean']}`",
            f"- human_edit_increase_ratio: `{comparison['human_edit_increase_ratio']}`",
            "",
            f"summary_digest: `{summary['summary_digest']}`",
            "",
        ]
    )
    return "\n".join(lines)


def _render_gate_markdown(gate: Mapping[str, Any]) -> str:
    lines = [
        "# Skill Market Lab Gate",
        "",
        f"## `{gate['decision']}`",
        "",
        f"- experiment_id: `{gate['experiment_id']}`",
        f"- evidence: `{gate['evidence_level_label']}`",
        f"- primary_comparator: `{gate['primary_comparator']}`",
        "",
        "## 理由",
        "",
    ]
    for item in gate["reasons"]:
        lines.append(f"- **{item['code']}** [{item['severity']}]: {item['detail']}")
    lines.extend(["", f"gate_result_digest: `{gate['gate_result_digest']}`", ""])
    return "\n".join(lines)


def _render_plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        "# 下一轮优化计划",
        "",
        f"- decision: `{plan['decision']}`",
        f"- experiment_id: `{plan['experiment_id']}`",
        "",
    ]
    for action in plan["actions"]:
        lines.extend(
            [
                f"## {action['priority']}. {action['type']}",
                "",
                f"- 假设：{action['hypothesis']}",
                f"- 证据：{action['evidence']}",
                f"- 验收：{action['acceptance']}",
                f"- 回滚：{action['rollback']}",
                f"- 阻断：`{action['blocking']}`",
                "",
            ]
        )
    lines.extend([f"plan_digest: `{plan['plan_digest']}`", ""])
    return "\n".join(lines)


def _parse_frontmatter(skill_md: Path) -> Dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValidationError("SKILL.md 缺少合法 frontmatter")
    result: Dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if ":" not in raw_line:
            raise ValidationError(f"无法解析 frontmatter 行: {raw_line}")
        key, value = raw_line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def doctor_skill(skill_root: Path) -> Dict[str, Any]:
    root = skill_root.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    skill_files = list(root.rglob("SKILL.md"))
    if skill_files != [root / "SKILL.md"]:
        errors.append(f"Skill 目录必须恰好有一个根级 SKILL.md，实际为 {[str(item) for item in skill_files]}")
    if not (root / "SKILL.md").exists():
        errors.append("缺少 SKILL.md")
    else:
        try:
            frontmatter = _parse_frontmatter(root / "SKILL.md")
            if set(frontmatter) != {"name", "description"}:
                errors.append(f"frontmatter 只能包含 name 和 description，实际为 {sorted(frontmatter)}")
            if frontmatter.get("name") != root.name:
                errors.append("frontmatter name 与目录名不一致")
            if not re.fullmatch(r"[a-z0-9-]{1,64}", frontmatter.get("name", "")):
                errors.append("Skill name 不是合法 hyphen-case")
            description = frontmatter.get("description", "")
            if not description or len(description) > 1024 or "<" in description or ">" in description:
                errors.append("description 为空、过长或包含尖括号")
            if len((root / "SKILL.md").read_text(encoding="utf-8").splitlines()) > 500:
                errors.append("SKILL.md 超过 500 行")
        except ValidationError as exc:
            errors.append(str(exc))
    required = [
        root / "agents" / "openai.yaml",
        root / "scripts" / "market_lab.py",
        root / "assets" / "templates" / "experiment_spec.json",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"缺少必要文件: {path.relative_to(root)}")
    for path in root.rglob("*"):
        if path.is_symlink():
            errors.append(f"拒绝符号链接: {path.relative_to(root)}")
        if path.is_file() and path.stat().st_size > 25 * 1024 * 1024:
            errors.append(f"单文件超过 25 MB: {path.relative_to(root)}")
    file_count = sum(1 for path in root.rglob("*") if path.is_file())
    if file_count > 500:
        errors.append(f"文件数超过 500: {file_count}")
    forbidden_names = {"README.md", "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md", "CHANGELOG.md"}
    found_forbidden = [path.name for path in root.iterdir() if path.is_file() and path.name in forbidden_names]
    if found_forbidden:
        errors.append(f"Skill 根目录包含非必要文档: {found_forbidden}")
    return {
        "valid": not errors,
        "skill_root": str(root),
        "file_count": file_count,
        "errors": errors,
        "warnings": warnings,
        "checked_at": utc_now(),
    }


def cmd_init_workspace(args: argparse.Namespace) -> None:
    template = read_json(Path(args.template))
    if args.experiment_id:
        template["experiment_id"] = args.experiment_id
    if args.subject_name:
        template["subject"]["skill_name"] = args.subject_name
    if args.subject_version:
        template["subject"]["skill_version"] = args.subject_version
    if args.subject_digest:
        template["subject"]["artifact_digest"] = args.subject_digest
        for arm in template["arms"]:
            if arm["kind"] == "candidate":
                arm["artifact_digest"] = args.subject_digest
    state = initialize_workspace(Path(args.workspace), template, force=args.force)
    _print_json(state)


def cmd_validate_spec(args: argparse.Namespace) -> None:
    spec = read_json(Path(args.spec))
    errors = validate_experiment_spec(spec)
    if errors:
        assert_valid(errors, "实验规范")
    _print_json({"valid": True, "spec_digest": object_sha256(spec), "experiment_id": spec["experiment_id"]})


def cmd_validate_competitors(args: argparse.Namespace) -> None:
    registry = read_json(Path(args.registry))
    assert_valid(validate_competitor_registry(registry), "竞品登记")
    _print_json(
        {
            "valid": True,
            "registry_id": registry["registry_id"],
            "entries": len(registry["entries"]),
            "registry_digest": object_sha256(registry),
        }
    )


def cmd_validate_tasks(args: argparse.Namespace) -> None:
    _print_json(_validate_jsonl(Path(args.tasks), validate_task, "任务集"))


def cmd_validate_results(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    arm_ids = [arm["id"] for arm in spec["arms"]]
    _print_json(_validate_jsonl(Path(args.results), validate_result, "结果集", arm_ids))


def cmd_validate_feedback(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    arm_ids = [arm["id"] for arm in spec["arms"]]
    _print_json(_validate_jsonl(Path(args.feedback), validate_feedback, "反馈集", arm_ids))


def cmd_expand_stress(args: argparse.Namespace) -> None:
    categories = list(STRESS_CATEGORIES) if args.categories == "all" else [item.strip() for item in args.categories.split(",") if item.strip()]
    count = expand_to_jsonl(
        iter_jsonl(Path(args.input)),
        Path(args.output),
        categories,
        args.variants_per_category,
        args.seed,
        args.include_original,
    )
    _print_json({"output": args.output, "records": count, "categories": categories})


def cmd_make_assignments(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    result = write_assignments(
        spec,
        iter_jsonl(Path(args.tasks)),
        Path(args.output),
        Path(args.blind_map_output),
    )
    result.update({"output": args.output, "blind_map_output": args.blind_map_output})
    _print_json(result)


def cmd_holdout_manifest(args: argparse.Namespace) -> None:
    manifest = make_holdout_manifest(iter_jsonl(Path(args.tasks)))
    write_json(Path(args.output), manifest)
    _print_json({"output": args.output, "count": manifest["count"], "manifest_digest": manifest["manifest_digest"]})


def cmd_candidate_view(args: argparse.Namespace) -> None:
    count = write_jsonl(Path(args.output), make_candidate_visible_dataset(iter_jsonl(Path(args.tasks))))
    _print_json({"output": args.output, "records": count, "sealed_holdout_disclosed": False})


def cmd_anonymize_feedback(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    salt = os.getenv(args.salt_env)
    if not salt:
        raise ValidationError(f"环境变量 {args.salt_env} 未设置")
    arm_ids = [arm["id"] for arm in spec["arms"]]
    report = anonymize_feedback_file(iter_jsonl(Path(args.input)), Path(args.output), salt, arm_ids)
    report["output"] = args.output
    _print_json(report)


def cmd_aggregate(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    feedback_rows = iter_jsonl(Path(args.feedback)) if args.feedback else None
    summary = aggregate_evidence(spec, iter_jsonl(Path(args.results)), feedback_rows)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "SUMMARY.json", summary)
    (output_dir / "SUMMARY.md").write_text(_render_summary_markdown(summary), encoding="utf-8")
    _print_json({"output_dir": str(output_dir), "summary_digest": summary["summary_digest"], "evidence": summary["evidence_level_label"]})


def cmd_gate(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    summary = read_json(Path(args.summary))
    gate = decide_gate(spec, summary)
    output = Path(args.output)
    write_json(output, gate)
    output.with_suffix(".md").write_text(_render_gate_markdown(gate), encoding="utf-8")
    _print_json({"decision": gate["decision"], "output": str(output), "gate_result_digest": gate["gate_result_digest"]})


def cmd_plan_next(args: argparse.Namespace) -> None:
    spec = _load_spec(Path(args.spec))
    summary = read_json(Path(args.summary))
    gate = read_json(Path(args.gate))
    plan = build_next_iteration_plan(spec, summary, gate)
    output = Path(args.output)
    write_json(output, plan)
    output.with_suffix(".md").write_text(_render_plan_markdown(plan), encoding="utf-8")
    _print_json({"output": str(output), "actions": len(plan["actions"]), "plan_digest": plan["plan_digest"]})


def cmd_seal(args: argparse.Namespace) -> None:
    manifest = seal_tree(Path(args.path), Path(args.manifest))
    _print_json({"manifest": args.manifest, "entry_count": manifest["entry_count"], "tree_digest": manifest["tree_digest"]})


def cmd_verify_seal(args: argparse.Namespace) -> None:
    report = load_and_verify_tree(Path(args.path), Path(args.manifest))
    _print_json(report)
    if not report["valid"]:
        raise ValidationError("封存验证失败")


def cmd_doctor(args: argparse.Namespace) -> None:
    report = doctor_skill(Path(args.skill_root))
    _print_json(report)
    if not report["valid"]:
        raise ValidationError("Skill 结构验证失败")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="market_lab.py",
        description="Skill Market Lab：模拟、因果实验、压力、大数据、真实市场反馈与迭代 Gate。",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("init-workspace", help="建立代码目录外的白箱实验工作区")
    item.add_argument("--workspace", required=True)
    item.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    item.add_argument("--experiment-id")
    item.add_argument("--subject-name")
    item.add_argument("--subject-version")
    item.add_argument("--subject-digest")
    item.add_argument("--force", action="store_true")
    item.set_defaults(func=cmd_init_workspace)

    item = sub.add_parser("validate-spec", help="验证冻结实验规范")
    item.add_argument("--spec", required=True)
    item.set_defaults(func=cmd_validate_spec)

    item = sub.add_parser("validate-competitors", help="验证 5–12 个真实/模拟/代理同行登记")
    item.add_argument("--registry", required=True)
    item.set_defaults(func=cmd_validate_competitors)

    item = sub.add_parser("validate-tasks", help="验证 JSONL 任务集")
    item.add_argument("--tasks", required=True)
    item.set_defaults(func=cmd_validate_tasks)

    item = sub.add_parser("validate-results", help="验证 JSONL 结果集")
    item.add_argument("--spec", required=True)
    item.add_argument("--results", required=True)
    item.set_defaults(func=cmd_validate_results)

    item = sub.add_parser("validate-feedback", help="验证 JSONL 真实市场反馈")
    item.add_argument("--spec", required=True)
    item.add_argument("--feedback", required=True)
    item.set_defaults(func=cmd_validate_feedback)

    item = sub.add_parser("expand-stress", help="从任务集生成六类压力变体")
    item.add_argument("--input", required=True)
    item.add_argument("--output", required=True)
    item.add_argument("--categories", default="all", help="all 或逗号分隔的六类")
    item.add_argument("--variants-per-category", type=int, default=1)
    item.add_argument("--seed", type=int, default=20260729)
    item.add_argument("--include-original", action="store_true")
    item.set_defaults(func=cmd_expand_stress)

    item = sub.add_parser("make-assignments", help="生成配对、重复、盲化的实验任务")
    item.add_argument("--spec", required=True)
    item.add_argument("--tasks", required=True)
    item.add_argument("--output", required=True)
    item.add_argument("--blind-map-output", required=True)
    item.set_defaults(func=cmd_make_assignments)

    item = sub.add_parser("holdout-manifest", help="只输出 sealed holdout 的 ID 与哈希")
    item.add_argument("--tasks", required=True)
    item.add_argument("--output", required=True)
    item.set_defaults(func=cmd_holdout_manifest)

    item = sub.add_parser("candidate-view", help="生成不含 sealed holdout 的 Candidate 可见任务集")
    item.add_argument("--tasks", required=True)
    item.add_argument("--output", required=True)
    item.set_defaults(func=cmd_candidate_view)

    item = sub.add_parser("anonymize-feedback", help="匿名化真实反馈并移除原始敏感内容")
    item.add_argument("--spec", required=True)
    item.add_argument("--input", required=True)
    item.add_argument("--output", required=True)
    item.add_argument("--salt-env", default="MARKET_LAB_HASH_SALT")
    item.set_defaults(func=cmd_anonymize_feedback)

    item = sub.add_parser("aggregate", help="流式汇总实验与市场证据")
    item.add_argument("--spec", required=True)
    item.add_argument("--results", required=True)
    item.add_argument("--feedback")
    item.add_argument("--output-dir", required=True)
    item.set_defaults(func=cmd_aggregate)

    item = sub.add_parser("gate", help="依据冻结 Gate 输出 PROMOTE/KEEP/REVERT/REHEAT/BLOCKED")
    item.add_argument("--spec", required=True)
    item.add_argument("--summary", required=True)
    item.add_argument("--output", required=True)
    item.set_defaults(func=cmd_gate)

    item = sub.add_parser("plan-next", help="把证据转为下一轮可证伪优化计划")
    item.add_argument("--spec", required=True)
    item.add_argument("--summary", required=True)
    item.add_argument("--gate", required=True)
    item.add_argument("--output", required=True)
    item.set_defaults(func=cmd_plan_next)

    item = sub.add_parser("seal", help="封存目录树并生成 SHA-256 清单")
    item.add_argument("--path", required=True)
    item.add_argument("--manifest", required=True)
    item.set_defaults(func=cmd_seal)

    item = sub.add_parser("verify-seal", help="复验目录树封存清单")
    item.add_argument("--path", required=True)
    item.add_argument("--manifest", required=True)
    item.set_defaults(func=cmd_verify_seal)

    item = sub.add_parser("doctor", help="检查 Skill 结构、路径和体积硬门")
    item.add_argument("--skill-root", default=str(SKILL_ROOT))
    item.set_defaults(func=cmd_doctor)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except MarketLabError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("ERROR: 用户中断；未将部分结果标记为 PASS。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
