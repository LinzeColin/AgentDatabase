#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import inspect
import os
from pathlib import Path
import tempfile
import unittest

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"

runtime_spec = importlib.util.spec_from_file_location(
    "prompt_compiler_native_path_tests", SCRIPTS_DIR / "prompt_compiler.py"
)
assert runtime_spec and runtime_spec.loader
runtime = importlib.util.module_from_spec(runtime_spec)
import sys
sys.modules[runtime_spec.name] = runtime
runtime_spec.loader.exec_module(runtime)

adapter_spec = importlib.util.spec_from_file_location(
    "native_engine_adapter_tests", SCRIPTS_DIR / "native_engine_adapter.py"
)
assert adapter_spec and adapter_spec.loader
adapter = importlib.util.module_from_spec(adapter_spec)
sys.modules[adapter_spec.name] = adapter
adapter_spec.loader.exec_module(adapter)


class NativePathContractTests(unittest.TestCase):
    def test_promptfoo_extracts_only_exact_best_prompt_section(self) -> None:
        border = "=" * 80
        output = (
            f"noise\n{border}\nBest prompt\n第一行\n第二行\n{border}\n"
            "```text\n错误围栏内容\n```\n"
        )
        self.assertEqual(runtime.extract_promptfoo_candidate(output, "seed"), "第一行\n第二行")

    def test_promptfoo_rejects_alias_and_generic_code_fence(self) -> None:
        output = "Optimized prompt:\n```text\n不能被接受\n```\n"
        self.assertIsNone(runtime.extract_promptfoo_candidate(output, "seed"))

    def test_promptfoo_preserves_unchanged_baseline_when_officially_selected(self) -> None:
        border = "=" * 80
        seed = "基线提示词"
        output = f"Best prompt\n{seed}\n{border}\n"
        self.assertEqual(runtime.extract_promptfoo_candidate(output, seed), seed)

    def test_isolated_workspace_allows_declared_candidate_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            (source / "program.md").write_text("合同", encoding="utf-8")
            (source / "train.py").write_text("seed", encoding="utf-8")
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; Path('train.py').write_text('candidate', encoding='utf-8')",
            ]
            evidence = adapter.run_isolated_workspace(
                source=source,
                destination=base / "isolated",
                command=command,
                required_files=["program.md", "train.py"],
                allowed_paths=["train.py"],
                expected_origin_fragments=["official/example"],
                timeout_seconds=30,
                allow_unverified_origin=True,
            )
            self.assertEqual(evidence.changed_paths, ("train.py",))
            self.assertNotEqual(evidence.before_tree_sha256, evidence.after_tree_sha256)

    def test_isolated_workspace_blocks_out_of_contract_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            (source / "program.md").write_text("合同", encoding="utf-8")
            (source / "train.py").write_text("seed", encoding="utf-8")
            command = [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "Path('train.py').write_text('candidate', encoding='utf-8'); "
                    "Path('program.md').write_text('tampered', encoding='utf-8')"
                ),
            ]
            with self.assertRaises(adapter.NativeEngineError) as caught:
                adapter.run_isolated_workspace(
                    source=source,
                    destination=base / "isolated",
                    command=command,
                    required_files=["program.md", "train.py"],
                    allowed_paths=["train.py"],
                    expected_origin_fragments=["official/example"],
                    timeout_seconds=30,
                    allow_unverified_origin=True,
                )
            self.assertEqual(caught.exception.code, "NATIVE_FORBIDDEN_MUTATION")
            self.assertIn("program.md", caught.exception.details["forbidden_paths"])

    def test_meta_harness_discovers_official_nested_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = root / "reference_examples" / "text_classification" / "meta_harness.py"
            entry.parent.mkdir(parents=True)
            entry.write_text("print('ok')\n", encoding="utf-8")
            self.assertEqual(
                adapter.discover_meta_harness_entrypoint(root),
                "reference_examples/text_classification/meta_harness.py",
            )

    def test_omni_fails_closed_when_any_native_path_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            runtime.initialize_project(project, source="种子提示词", objective="改进")
            seed = runtime.Candidate("seed", "种子提示词", "seed", [], 0, {})
            candidates = []
            reports = {}
            for engine in ("gepa", "autoresearch", "meta_harness"):
                item = runtime.Candidate(
                    f"{engine}-1",
                    f"种子提示词\n{engine}",
                    engine,
                    ["seed"],
                    1,
                    {},
                    validation={"mean": 0.8, "worst": 0.8, "hard_failure_count": 0, "results": []},
                )
                candidates.append(item)
                reports[engine] = {"status": "PASS"}
            generated, report = runtime.run_champion_synthesis(
                project,
                seed_candidate=seed,
                archive=candidates,
                validation=[],
                task_client=runtime.MockClient("task"),
                evaluator_client=runtime.MockClient("evaluator"),
                reflection_client=runtime.MockClient("reflection"),
                budget=10,
                preset="smoke",
                current_run_id="test",
                run_dir=project / "runs" / "test",
                stage_one_candidates=candidates,
                stage_one_reports=reports,
            )
            self.assertEqual(generated, [])
            self.assertEqual(report["status"], "BLOCKED")
            self.assertIn("promptfoo", report["stage_1"]["missing_paths"])
            self.assertFalse(report["local_same_name_simulation"])

    def test_builtin_orchestration_contains_no_local_same_name_runner(self) -> None:
        source = inspect.getsource(runtime.optimize_project)
        self.assertNotIn("run_local_engine", source)
        self.assertNotIn("run_omni_crossover", source)
        self.assertFalse(hasattr(runtime, "run_local_engine"))
        self.assertFalse(hasattr(runtime, "run_omni_crossover"))

    def test_native_input_contract_never_contains_final_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            runtime.initialize_project(project, source="种子提示词", objective="改进")
            contract = runtime.native_input_contract(
                project,
                engine="autoresearch",
                seed_candidate=runtime.Candidate("seed", "种子提示词", "seed", [], 0, {}),
                train=[{"id": "train"}],
                validation=[{"id": "validation"}],
                budget=5,
            )
            self.assertNotIn("final_test", contract)
            self.assertNotIn("final", contract)


if __name__ == "__main__":
    unittest.main()
