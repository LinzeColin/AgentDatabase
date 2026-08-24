#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "prompt_compiler.py"
spec = importlib.util.spec_from_file_location("prompt_compiler_runtime_tests", MODULE_PATH)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runtime
spec.loader.exec_module(runtime)


def make_case(index: int, *, split: str = "case", synthetic: bool = False) -> dict:
    return {
        "id": f"{split}-{index:03d}",
        "task_id": "default" if index % 2 else "secondary",
        "input": f"请处理输入 {index}",
        "must_include": ["结论", "验收标准"],
        "must_not_include": ["伪造"],
        "reference": "结论与验收标准",
        "synthetic": synthetic,
        "provenance": "test",
    }


def populate_datasets(project: Path) -> None:
    runtime.write_jsonl(project / "datasets" / "train.jsonl", [make_case(i, split="train") for i in range(1, 4)])
    runtime.write_jsonl(project / "datasets" / "validation.jsonl", [make_case(i, split="validation") for i in range(1, 4)])
    runtime.write_jsonl(project / "datasets" / "final_test.jsonl", [make_case(i, split="final") for i in range(1, 4)])
    runtime.write_jsonl(project / "datasets" / "regression.jsonl", [make_case(1, split="regression")])
    runtime.write_default_redteam_cases(project)
    runtime.seal_datasets(project)


def configure_mock_roles(project: Path) -> None:
    config = runtime.project_config(project)
    config["runtime"]["roles"] = {
        "task": {"mode": "mock", "command": [], "model": "task", "identity": "mock-task"},
        "reflection": {"mode": "mock", "command": [], "model": "reflection", "identity": "mock-reflection"},
        "evaluator": {"mode": "mock", "command": [], "model": "evaluator", "identity": "mock-evaluator"},
        "final_judge": {"mode": "mock", "command": [], "model": "final", "identity": "mock-final"},
        "compiler": {"mode": "mock", "command": [], "model": "compiler", "identity": "mock-compiler"},
    }
    config["optimization"]["repeat_count"] = 3
    config["optimization"]["matched_budget"]["smoke"] = 18
    runtime.write_json(project / "config.json", config)


def make_fake_promptfoo(folder: Path) -> Path:
    executable = folder / "promptfoo"
    executable.write_text(
        textwrap.dedent(
            r'''#!/usr/bin/env python3
import json
from pathlib import Path
import sys

args = sys.argv[1:]
if not args or '--version' in args:
    print('0.121.20')
    raise SystemExit(0)
if args[0] == 'optimize':
    config = Path(args[args.index('-c') + 1])
    seed = config.parent / 'prompts' / 'seed.md'
    text = seed.read_text(encoding='utf-8')
    text = text.split('\n\n【测试输入】\n', 1)[0]
    print('Optimized prompt:\n```text\n' + text + '\n\n【优化标记】\n明确验收标准并保留全部硬约束。\n```')
    raise SystemExit(0)
if args[0] == 'eval':
    out = Path(args[args.index('-o') + 1])
    config = Path(args[args.index('-c') + 1]).read_text(encoding='utf-8')
    case_count = max(1, config.count('  - vars:'))
    repeat_count = int(args[args.index('--repeat') + 1]) if '--repeat' in args else 1
    rows = []
    for repeat in range(1, repeat_count + 1):
        for i in range(case_count):
            rows.append({
                'id': f'seed-{repeat}-{i}',
                'prompt': {'label': '种子版本'},
                'promptIdx': 0,
                'testIdx': i,
                'success': False,
                'score': 0.55,
                'metadata': {'case_id': f'case-{i}', 'repeat': repeat},
                'response': {'output': '结论 基础回答'},
            })
            rows.append({
                'id': f'optimized-{repeat}-{i}',
                'prompt': {'label': '优化版本'},
                'promptIdx': 1,
                'testIdx': i,
                'success': True,
                'score': 0.95,
                'metadata': {'case_id': f'case-{i}', 'repeat': repeat},
                'response': {'output': '结论 验收标准'},
            })
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'results': {'results': rows}}, ensure_ascii=False), encoding='utf-8')
    raise SystemExit(0)
if args[0] == 'redteam':
    if len(args) > 1 and args[1] == 'generate':
        out = Path(args[args.index('-o') + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text('description: fake redteam\n', encoding='utf-8')
        print('redteam generated')
        raise SystemExit(0)
    if len(args) > 1 and args[1] == 'eval':
        out = Path(args[args.index('-o') + 1])
        repeat_count = int(args[args.index('--repeat') + 1]) if '--repeat' in args else 1
        rows = []
        for repeat in range(1, repeat_count + 1):
            for i in range(5):
                rows.append({
                    'id': f'red-{repeat}-{i}',
                    'prompt': {'label': '待测工件'},
                    'testIdx': i,
                    'success': True,
                    'score': 1.0,
                    'metadata': {'case_id': f'red-{i}', 'repeat': repeat},
                })
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({'results': {'results': rows}}, ensure_ascii=False), encoding='utf-8')
        raise SystemExit(0)
    print('unsupported redteam', args, file=sys.stderr)
    raise SystemExit(1)
print('unsupported', args, file=sys.stderr)
raise SystemExit(1)
'''
        ),
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


class PromptCompilerRuntimeTests(unittest.TestCase):
    def test_self_test(self) -> None:
        result = runtime.self_test()
        self.assertEqual(result["status"], "PASS", result)

    def test_exact_history_and_four_target_versions_for_each_ingest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            first = "第一条原始 Prompt，版本 v0.0.0.1。"
            runtime.initialize_project(project, source=first, objective="保持原意。")
            records = runtime.ledger_list(project)
            self.assertEqual(len(records), 5)
            source_rows = [row for row in records if row["target"] == "source"]
            self.assertEqual(runtime.ledger_get_prompt(project, source_rows[0]["id"])["content"], first)
            second = "第二条原始 Prompt，阈值 60万，链接 https://example.com/test。"
            meta = runtime.ingest_source(project, second)
            records = runtime.ledger_list(project)
            self.assertEqual(len(records), 10)
            self.assertEqual(runtime.read_text(project / "source.md"), second)
            for target in runtime.TARGETS:
                item = meta["prompt_versions"][target]
                record = runtime.ledger_get_prompt(project, item["record_id"])
                self.assertEqual(record["target"], target)
                self.assertEqual(record["sha256"], item["sha256"])
                self.assertIn(second, record["content"])

    def test_default_has_no_provider_and_final_judge_does_not_inherit_task(self) -> None:
        config_blob = json.dumps(runtime.DEFAULT_CONFIG).lower()
        self.assertNotIn("openai:", config_blob)
        self.assertNotIn("anthropic:", config_blob)
        with self.assertRaises(runtime.CompilerError) as caught:
            runtime.resolve_client(runtime.DEFAULT_CONFIG, "final_judge")
        self.assertEqual(caught.exception.code, "DISTINCT_FINAL_JUDGE_REQUIRED")

    def test_runtime_reexec_does_not_skip_a_symlinked_venv_interpreter(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime_python = Path(temp) / "python"
            runtime_python.symlink_to(Path(sys.executable))
            self.assertEqual(runtime_python.resolve(), Path(sys.executable).resolve())
            with mock.patch.dict(runtime.os.environ, {"PROMPT_COMPILER_RUNTIME_PYTHON_ACTIVE": ""}, clear=False), \
                 mock.patch.object(runtime, "runtime_python", return_value=runtime_python), \
                 mock.patch.object(runtime.os, "execve") as execve:
                runtime.maybe_reexec_in_runtime(["external-acceptance"])
                runtime.reexec_in_runtime(["external-acceptance"])
            self.assertEqual(execve.call_count, 2)
            for call in execve.call_args_list:
                executable, argv, env = call.args
                self.assertEqual(executable, str(runtime_python))
                self.assertEqual(argv[:3], [str(runtime_python), "-B", str(Path(runtime.__file__).resolve())])
                self.assertEqual(env["PROMPT_COMPILER_RUNTIME_PYTHON_ACTIVE"], "1")

    def test_codex_timeout_fails_closed_after_process_group_cleanup(self) -> None:
        identity = runtime.RuntimeIdentity("task", "codex", "codex:test")
        with mock.patch.object(runtime.shutil, "which", return_value="/fake/codex"), \
             mock.patch.object(runtime.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="", stderr="")):
            client = runtime.CodexClient(identity, timeout_seconds=7)
        timeout = subprocess.TimeoutExpired(["/fake/codex", "exec"], 7, output="partial", stderr="stuck")
        with mock.patch.object(runtime, "run_process_group", side_effect=timeout):
            with self.assertRaises(runtime.CompilerError) as caught:
                client.generate(system="只返回短语", user="测试")
        self.assertEqual(caught.exception.code, "CODEX_EXEC_TIMEOUT")
        self.assertEqual(client.last_call_record["returncode"], None)
        self.assertEqual(client.last_call_record["timeout_seconds"], 7)
        self.assertIn("partial", client.last_call_record["stdout"])

    def test_distinct_final_judge_identity_is_enforced(self) -> None:
        task = runtime.MockClient("task", "same")
        final = runtime.MockClient("task", "same")
        with self.assertRaises(runtime.CompilerError):
            runtime.ensure_distinct(task, final)
        runtime.ensure_distinct(runtime.MockClient("task", "task"), runtime.MockClient("final_judge", "final"))

    def test_dataset_seal_and_final_open_only_after_candidate_freeze(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            runtime.initialize_project(project, source="测试原始 Prompt。", objective="测试封印。")
            populate_datasets(project)
            candidate = runtime.Candidate("c1", "测试原始 Prompt。\n【优化标记】", "test", ["seed"], 1, {})
            with self.assertRaises(runtime.CompilerError):
                runtime.open_final_test(project, "run-1", candidate)
            runtime.freeze_candidate(project, "run-1", candidate, [candidate])
            final = runtime.open_final_test(project, "run-1", candidate)
            self.assertEqual(len(final), 3)
            freeze = runtime.read_json(project / "runs" / "run-1" / "candidate_freeze.json")
            self.assertTrue(freeze["final_test_opened"])

    def test_frozen_finalist_slate_cannot_change_before_final_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            source = "测试候选冻结与最终名单不可偷换。" * 10
            runtime.initialize_project(project, source=source, objective="保持终审隔离。")
            populate_datasets(project)
            first = runtime.Candidate("a", source + "\n候选甲", "gepa", ["seed"], 1, {})
            second = runtime.Candidate("b", source + "\n候选乙", "promptfoo", ["seed"], 1, {})
            runtime.freeze_candidate(project, "run-slate", first, [first, second], [first, second])
            changed = runtime.Candidate("c", source + "\n候选丙", "promptfoo", ["seed"], 1, {})
            with self.assertRaises(runtime.CompilerError) as caught:
                runtime.open_final_test(project, "run-slate", first, [first, changed])
            self.assertEqual(caught.exception.code, "FINALIST_SLATE_CHANGED")

    def test_contract_guard_preserves_versions_links_thresholds_and_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            source = "必须保留 v0.0.0.1、阈值 60万、链接 https://example.com/a 和路径 LinzeColin/AgentDatabase。"
            runtime.initialize_project(project, source=source, objective="保持全部字面约束。")
            good = runtime.candidate_contract_check(project, source + "\n优化")
            bad = runtime.candidate_contract_check(project, "简短候选")
            self.assertEqual(good["status"], "PASS")
            self.assertEqual(bad["status"], "REJECTED")
            self.assertIn("v0.0.0.1", bad["missing_literals"])

    def test_repeated_evaluation_reports_mean_worst_and_variance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            source = "这是一个足够长的原始 Prompt，用于测试重复运行统计、硬约束和验收标准。" * 8
            runtime.initialize_project(project, source=source, objective="提高可靠性。")
            cases = [runtime.normalize_case(make_case(i), i, split="test") for i in range(1, 4)]
            result = runtime.evaluate_suite(
                project,
                candidate=source + "\n【优化标记】",
                cases=cases,
                task_client=runtime.MockClient("task", "task"),
                judge_client=runtime.MockClient("evaluator", "eval"),
                phase="test",
                repeat_count=3,
            )
            self.assertEqual(result["repeat_count"], 3)
            self.assertEqual(result["row_count"], 9)
            self.assertIn("mean", result)
            self.assertIn("worst", result)
            self.assertIn("variance", result)
            self.assertEqual(result["hard_failure_count"], 0)

    def test_pareto_archive_keeps_non_dominated_candidates(self) -> None:
        seed = "x" * 100
        a = runtime.Candidate("a", seed, "a", [], 1, {}, {"mean": 0.9, "worst": 0.7, "variance": 0.01, "hard_failure_count": 0, "dimensions": {"security": 1}})
        b = runtime.Candidate("b", seed * 2, "b", [], 1, {}, {"mean": 0.8, "worst": 0.6, "variance": 0.03, "hard_failure_count": 0, "dimensions": {"security": 0.9}})
        archive = runtime.pareto_archive([a, b], seed)
        self.assertEqual([item.candidate_id for item in archive], ["a"])

    def test_promptfoo_export_has_seed_and_optimized_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            runtime.initialize_project(project, source="原始提示词。", objective="对照。")
            cases = [runtime.normalize_case(make_case(1), 1, split="final")]
            export = runtime.export_promptfoo_project(project, "种子", "优化", project / "pf", cases=cases, comparison=True)
            text = Path(export["config"]).read_text(encoding="utf-8")
            self.assertIn("file://prompts/seed.md", text)
            self.assertIn("file://prompts/optimized.md", text)
            self.assertIn("种子版本", text)
            self.assertIn("优化版本", text)
            self.assertNotIn("openai:", text.lower())

    def test_promptfoo_parser_requires_two_actual_result_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result_path = Path(temp) / "results.json"
            rows = [
                {"prompt": {"label": "种子版本"}, "success": False, "score": 0.4, "metadata": {"case_id": "a"}, "response": {"output": "x"}},
                {"prompt": {"label": "优化版本"}, "success": True, "score": 0.9, "metadata": {"case_id": "a"}, "response": {"output": "y"}},
            ]
            result_path.write_text(json.dumps({"results": {"results": rows}}, ensure_ascii=False), encoding="utf-8")
            summary = runtime.summarize_promptfoo_result(result_path)
            self.assertEqual(summary["status"], "PASS")
            self.assertTrue(summary["pair_present"])
            self.assertEqual(summary["groups"]["种子版本"]["evaluated_rows"], 1)
            self.assertEqual(summary["groups"]["优化版本"]["evaluated_rows"], 1)

    def test_promptfoo_repeat_coverage_is_proven_not_inferred(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "results.json"
            too_few = [
                {"id": "s1", "prompt": {"label": "种子版本"}, "success": True, "score": 1.0, "metadata": {"case_id": "a"}},
                {"id": "o1", "prompt": {"label": "优化版本"}, "success": True, "score": 1.0, "metadata": {"case_id": "a"}},
            ]
            path.write_text(json.dumps({"results": {"results": too_few}}, ensure_ascii=False), encoding="utf-8")
            blocked = runtime.summarize_promptfoo_result(path, expected_case_count=1, repeat_count=3)
            self.assertEqual(blocked["status"], "BLOCKED")
            rows = []
            for repeat in range(1, 4):
                rows.extend(
                    [
                        {"id": f"s{repeat}", "prompt": {"label": "种子版本"}, "success": True, "score": 0.8, "metadata": {"case_id": "a", "repeat": repeat}},
                        {"id": f"o{repeat}", "prompt": {"label": "优化版本"}, "success": True, "score": 0.9, "metadata": {"case_id": "a", "repeat": repeat}},
                    ]
                )
            path.write_text(json.dumps({"results": {"results": rows}}, ensure_ascii=False), encoding="utf-8")
            passed = runtime.summarize_promptfoo_result(path, expected_case_count=1, repeat_count=3)
            self.assertEqual(passed["status"], "PASS")
            self.assertEqual(passed["groups"]["种子版本"]["evaluated_rows"], 3)
            self.assertIn("sample_variance", passed["groups"]["优化版本"])

    def test_promptfoo_pair_timeout_is_bounded_and_preserves_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            runtime.initialize_project(project, source="原始提示词。", objective="对照。")
            config = runtime.project_config(project)
            config["runtime"]["promptfoo_timeout_seconds"] = 17
            runtime.write_json(project / "config.json", config)
            output = Path(temp) / "promptfoo"
            cases = [runtime.normalize_case(make_case(1), 1, split="final")]
            timeout = subprocess.TimeoutExpired(["promptfoo", "eval"], 17, output="partial", stderr="stuck")
            with mock.patch.object(runtime, "promptfoo_binary", return_value="/fake/promptfoo"), \
                 mock.patch.object(runtime, "run_process_group", side_effect=timeout) as runner:
                result = runtime.run_promptfoo_pair(
                    project,
                    seed="种子版本",
                    optimized="优化版本",
                    cases=cases,
                    output_dir=output,
                    repeat_count=3,
                    description="超时测试",
                )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("超时", result["reason"])
            self.assertEqual(result["timeout_seconds"], 17)
            self.assertEqual(runner.call_args.kwargs["timeout_seconds"], 17)
            command = runtime.read_json(output / "command.json")
            self.assertEqual(command["returncode"], None)
            self.assertEqual(command["timeout_seconds"], 17)
            self.assertIn("partial", command["stdout"])

    def test_promptfoo_official_redteam_parses_failures_instead_of_return_code(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "redteam.json"
            path.write_text(
                json.dumps(
                    {
                        "results": {
                            "results": [
                                {"id": "r1", "prompt": {"label": "待测工件"}, "success": True, "score": 1.0},
                                {"id": "r2", "prompt": {"label": "待测工件"}, "success": False, "score": 0.0},
                            ]
                        }
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = runtime.summarize_promptfoo_redteam_result(path, repeat_count=3)
            self.assertEqual(result["status"], "REJECTED")
            self.assertEqual(result["failure_count"], 1)

    def test_promptfoo_official_redteam_requires_actual_repeat_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "redteam.json"
            rows = [
                {"id": "r1", "prompt": {"label": "待测工件"}, "testIdx": 0, "success": True, "score": 1.0},
                {"id": "r2", "prompt": {"label": "待测工件"}, "testIdx": 1, "success": True, "score": 1.0},
            ]
            path.write_text(json.dumps({"results": {"results": rows}}, ensure_ascii=False), encoding="utf-8")
            result = runtime.summarize_promptfoo_redteam_result(path, repeat_count=3)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertFalse(result["repeat_coverage_proven"])

    def test_promptfoo_official_redteam_targets_optimized_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            runtime.initialize_project(project, source="原始版本", objective="测试红队目标")
            output = Path(temp) / "redteam"
            runtime.write_promptfoo_redteam_config(project, output, candidate="优化版本唯一标记")
            target = runtime.read_text(output / "target.md")
            self.assertIn("优化版本唯一标记", target)
            self.assertNotIn("原始版本", target)

    def test_gepa_component_dictionary_candidate_is_unwrapped(self) -> None:
        self.assertEqual(runtime.unwrap_gepa_candidate({"current_candidate": "  候选正文  "}), "候选正文")
        self.assertEqual(runtime.unwrap_gepa_candidate({"only": "唯一文本"}), "唯一文本")
        self.assertIsNone(runtime.unwrap_gepa_candidate({"a": "甲", "b": "乙"}))

    def test_regression_gate_rejects_old_case_degradation(self) -> None:
        seed = {"mean": 0.9, "hard_failure_count": 0, "per_case": {"old": {"worst": 0.9}}}
        candidate = {"mean": 0.8, "hard_failure_count": 1, "per_case": {"old": {"worst": 0.7}}}
        result = runtime.internal_regression_check(seed, candidate)
        self.assertEqual(result["status"], "REJECTED")
        self.assertGreaterEqual(len(result["reasons"]), 2)

    def test_full_offline_orchestration_reaches_pass_only_with_all_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fake_bin = base / "bin"
            fake_bin.mkdir()
            make_fake_promptfoo(fake_bin)
            project = base / "project"
            source = (
                "这是一个正式 Prompt，版本 v0.0.0.1，必须保留所有目标、硬约束、禁止项、权限边界、"
                "错误恢复、验收标准、证据等级和输出合同；不得伪造执行结果。"
            ) * 7
            runtime.initialize_project(project, source=source, objective="提高泛化、稳定性与安全性。")
            populate_datasets(project)
            configure_mock_roles(project)
            runtime.write_json(project / "reports" / "external_acceptance.json", {"status": "PASS", "note": "测试夹具；不代表外部实测"})
            previous = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{previous}"
            try:
                report = runtime.optimize_project(
                    project,
                    preset="smoke",
                    engines=["autoresearch", "meta_harness", "promptfoo", "omni"],
                    allow_mock=True,
                )
            finally:
                os.environ["PATH"] = previous
            self.assertEqual(report["release_gate"]["decision"], "PASS", report["release_gate"])
            self.assertTrue(report["release_gate"]["release_allowed"])
            self.assertEqual(report["final"]["optimized"]["repeat_count"], 3)
            self.assertGreater(report["final"]["optimized"]["mean"], report["final"]["seed"]["mean"])
            self.assertTrue(report["promptfoo"]["final"]["pair_present"])
            self.assertTrue(report["promptfoo"]["final"]["repeat_coverage_proven"])
            self.assertEqual(report["promptfoo"]["final"]["groups"]["种子版本"]["evaluated_rows"], 9)
            self.assertTrue(report["promptfoo"]["regression"]["pair_present"])
            self.assertEqual(report["redteam"]["promptfoo_official"]["status"], "PASS")
            self.assertGreater(report["redteam"]["promptfoo_official"]["evaluated_rows"], 0)
            self.assertFalse(report["heldout_exposed_before_freeze"])
            self.assertFalse(report["original_overwritten"])
            self.assertEqual(runtime.read_text(project / "source.md"), source)
            self.assertEqual(report["competitive_evidence"]["status"], "PROVEN_ON_THIS_DATASET")
            self.assertTrue(report["competitive_evidence"]["winner_not_worse_than_each_requested_engine"])
            self.assertEqual(set(report["winner"]["target_versions"]), set(runtime.TARGETS))
            for target, item in report["winner"]["target_versions"].items():
                self.assertTrue(Path(item["path"]).is_file(), target)
                record = runtime.ledger_get_prompt(project, item["record_id"])
                self.assertEqual(record["parent_id"], report["winner"]["record_id"])
            kernel = runtime.read_text(project / ".ramify" / "KERNEL.md")
            self.assertIn("当前获胜候选的四模型版本指针", kernel)
            report_md = runtime.read_text(Path(report["artifacts"]["optimized"]).parent / "REPORT.md")
            self.assertIn("决策：**正式通过**", report_md)
            self.assertNotIn("PROVEN_ON_THIS_DATASET", report_md)
            ci = runtime.cli_ci_gate(project)
            self.assertEqual(ci["status"], "PASS", ci)
            self.assertEqual(ci["external_independent_acceptance"]["status"], "PASS")

    def test_ci_gate_blocks_when_latest_report_is_not_release_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            report = project / "reports" / "r" / "report.json"
            runtime.write_json(report, {"release_gate": {"decision": "BLOCKED", "release_allowed": False, "blocked_reasons": ["x"], "rejected_reasons": []}})
            runtime.write_json(project / "reports" / "latest.json", {"report": str(report), "decision": "BLOCKED"})
            result = runtime.cli_ci_gate(project)
            self.assertEqual(result["status"], "BLOCKED")

    def test_ci_gate_ignores_tampered_release_boolean_without_independent_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            report = project / "reports" / "r" / "report.json"
            runtime.write_json(
                report,
                {
                    "release_gate": {
                        "decision": "PASS",
                        "release_allowed": True,
                        "blocked_reasons": [],
                        "rejected_reasons": [],
                    },
                    "promptfoo": {},
                    "redteam": {},
                    "competitive_evidence": {"status": "NOT_PROVEN_FOR_RELEASE"},
                },
            )
            runtime.write_json(project / "reports" / "latest.json", {"report": str(report), "decision": "PASS"})
            result = runtime.cli_ci_gate(project)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertFalse(result["release_allowed"])
            self.assertEqual(result["promptfoo_independent_acceptance"]["status"], "BLOCKED")
            self.assertEqual(result["competitive_evidence"], "BLOCKED")

    def test_doctor_fails_closed_when_independent_final_judge_is_unresolved(self) -> None:
        with mock.patch.object(runtime, "package_version", return_value=runtime.GEPA_VERSION), \
             mock.patch.object(runtime, "promptfoo_binary", return_value="/fake/promptfoo"), \
             mock.patch.object(runtime.shutil, "which", side_effect=lambda name: "/fake/" + name if name in {"node", "codex"} else None), \
             mock.patch.object(runtime.subprocess, "run", return_value=mock.Mock(returncode=0, stdout="v24.0.0", stderr="")):
            result = runtime.doctor(probe=False)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["roles"]["final_judge"]["status"], "BLOCKED")

    def test_ci_gate_rechecks_external_evidence_file_even_when_report_claims_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            group = {
                "evaluated_rows": 3,
                "mean": 1.0,
                "worst": 1.0,
                "variance": 0.0,
                "sample_variance": 0.0,
                "pass_rate": 1.0,
                "case_counts": {"c": 3},
                "repeat_proven": True,
                "failures": [],
            }
            pair = {
                "status": "PASS",
                "pair_present": True,
                "repeat_coverage_proven": True,
                "groups": {"种子版本": group, "优化版本": group},
            }
            report_path = project / "reports" / "r" / "report.json"
            runtime.write_json(
                report_path,
                {
                    "release_gate": {"decision": "PASS", "release_allowed": True, "blocked_reasons": [], "rejected_reasons": []},
                    "promptfoo": {"final": pair, "regression": pair},
                    "redteam": {"promptfoo_fixed": pair, "promptfoo_official": {"status": "PASS"}},
                    "competitive_evidence": {"status": "PROVEN_ON_THIS_DATASET"},
                    "external_evidence": {"status": "PASS", "path": str(project / "missing-external.json")},
                },
            )
            runtime.write_json(project / "reports" / "latest.json", {"report": str(report_path), "decision": "PASS"})
            result = runtime.cli_ci_gate(project)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["external_independent_acceptance"]["status"], "BLOCKED")

    def test_external_evidence_missing_is_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with mock.patch.object(runtime, "runtime_root", return_value=Path(temp) / "runtime"):
                result = runtime.external_evidence_status(Path(temp) / "project")
            self.assertEqual(result["status"], "NOT_RUN_EXTERNAL")


    def test_all_named_competitor_bridges_are_present_and_disabled_by_default(self) -> None:
        external = runtime.DEFAULT_CONFIG["optimization"]["external_engines"]
        self.assertEqual(set(external), set(runtime.EXTERNAL_COMPETITOR_NAMES))
        self.assertTrue(all(not item["enabled"] and item["command"] == [] for item in external.values()))

    def test_external_competitor_bridge_cannot_receive_final_test_and_is_independently_scored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            project = base / "project"
            source = "必须保留版本 v0.0.0.1、阈值 60万和验收标准。" * 8
            runtime.initialize_project(project, source=source, objective="提高稳定性。")
            candidate_text = source + "\n【优化标记】\n明确验收标准。"
            bridge = base / "bridge.py"
            bridge.write_text(
                "import json,sys\n"
                "p=json.load(sys.stdin)\n"
                "assert 'final_test' not in p\n"
                "print(json.dumps({'candidates':[" + repr(candidate_text) + "]}, ensure_ascii=False))\n",
                encoding="utf-8",
            )
            config = runtime.project_config(project)
            config["optimization"]["external_engines"]["dspy_mipro"] = {
                "enabled": True,
                "command": [sys.executable, "-B", str(bridge)],
                "identity": "test-dspy",
                "timeout_seconds": 30,
            }
            runtime.write_json(project / "config.json", config)
            cases = [runtime.normalize_case(make_case(i), i, split="validation") for i in range(1, 4)]
            seed = runtime.Candidate("seed", source, "seed", [], 0, {})
            candidates, report = runtime.run_external_optimizer_engine(
                project,
                engine="dspy_mipro",
                seed_candidate=seed,
                train=cases,
                validation=cases,
                task_client=runtime.MockClient("task", "task"),
                evaluator_client=runtime.MockClient("evaluator", "eval"),
                budget=9,
                run_dir=base / "run",
            )
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].engine, "dspy_mipro")
            self.assertGreater(candidates[0].validation["mean"], 0.8)

    def test_command_evidence_redacts_secret_values(self) -> None:
        completed = mock.Mock(returncode=0, stdout="token=abcdefghijklmnop123456", stderr="")
        record = runtime.command_record(["tool", "--token=abcdefghijklmnop123456"], completed)
        self.assertNotIn("abcdefghijklmnop123456", json.dumps(record, ensure_ascii=False))
        self.assertIn("已脱敏", json.dumps(record, ensure_ascii=False))

    def test_formal_non_prompt_optimization_requires_real_custom_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            source = "def example():\n    return 1\n" * 10
            runtime.initialize_project(project, source=source, objective="优化代码。", artifact_kind="code")
            populate_datasets(project)
            configure_mock_roles(project)
            with self.assertRaises(runtime.CompilerError) as caught:
                runtime.optimize_project(project, preset="formal", engines=["autoresearch"], allow_mock=True)
            self.assertEqual(caught.exception.code, "CUSTOM_EVALUATOR_REQUIRED_FOR_NON_PROMPT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
