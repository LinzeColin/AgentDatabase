from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
DATABASE_DIR = TEST_DIR.parent
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from recurring_prompt_core import (  # noqa: E402
    RuntimeConfig,
    SourceMutationError,
    build_analysis,
    compare_semantic_outputs,
    compare_trees,
    detect_origin,
    escape_markdown_cell,
    iter_jsonl,
    split_clauses,
    validate_outputs,
)


class RecurringPromptAnalysisTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.config = self.repo / "OpenAIDatabase/config/behavior/recurring_prompt_analysis.json"
        self.config.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            DATABASE_DIR / "config/behavior/recurring_prompt_analysis.json",
            self.config,
        )
        self.input_dir = self.repo / "OpenAIDatabase/data/public_raw/codex/sessions"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        fixture_dir = TEST_DIR / "fixtures/recurring_prompt"
        for fixture in sorted(fixture_dir.glob("*.jsonl")):
            shutil.copy2(fixture, self.input_dir / fixture.name)
        self.output = self.repo / "OpenAIDatabase/data/derived/behavior_intelligence/recurring_prompts"
        self.summary = self.repo / "OpenAIDatabase/人类可读/00_Recurring分析_最新.md"
        self.status = self.repo / "OpenAIDatabase/人类可读/00_Recurring运行状态.md"
        self.as_of = dt.datetime(2026, 7, 23, 0, 0, tzinfo=dt.timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self, **kwargs):
        return build_analysis(
            repo_root=self.repo,
            config_path=self.config,
            output_dir=kwargs.pop("output_dir", self.output),
            summary_path=kwargs.pop("summary_path", self.summary),
            status_path=kwargs.pop("status_path", self.status),
            source_commit=kwargs.pop("source_commit", "fixture-commit"),
            as_of=kwargs.pop("as_of", self.as_of),
            previous_output_dir=kwargs.pop("previous_output_dir", None),
            force_full=kwargs.pop("force_full", False),
            publish_atomically=kwargs.pop("publish_atomically", True),
            **kwargs,
        )

    def test_full_build_filters_injection_deduplicates_and_separates_automation(self) -> None:
        manifest = self.build()
        self.assertEqual(manifest["llm_calls"], 0)
        self.assertGreaterEqual(manifest["excluded_injected_messages"], 2)
        self.assertGreaterEqual(manifest["deduplicated_event_copies"], 3)
        self.assertEqual(manifest["malformed_lines"], 1)

        occurrences = list(iter_jsonl(self.output / "occurrences.jsonl"))
        combined = "\n".join(item["normalized_text"] for item in occurrences)
        self.assertNotIn("strict one_shot mode", combined)
        self.assertNotIn("assistant output", combined)
        self.assertNotIn("必须被忽略的注入说明", combined)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", combined)
        self.assertNotIn("/users/example", combined)
        self.assertIn("[redacted_secret]", combined)
        self.assertIn("[redacted_local_path]", combined)

        categories = {item["category"] for item in occurrences}
        self.assertEqual(
            categories,
            {"rules_preferences", "tasks_topics", "problems_corrections"},
        )
        origins = {item["origin"] for item in occurrences}
        self.assertEqual(origins, {"human_interactive", "codex_automation"})

        duplicate_rule_sources = [
            item
            for item in occurrences
            if item["display_text"].startswith("请先核验事实")
        ]
        self.assertTrue(duplicate_rule_sources)
        self.assertTrue(all(item["source_kind"] == "event_msg" for item in duplicate_rule_sources))

    def test_exact_template_and_correction_clusters(self) -> None:
        self.build()
        clusters = list(iter_jsonl(self.output / "clusters.jsonl"))
        correction = [
            item
            for item in clusters
            if "忘记保留 handoff.md" in item["display_text"]
        ]
        self.assertEqual(len(correction), 1)
        self.assertEqual(correction[0]["category"], "problems_corrections")
        self.assertEqual(correction[0]["scope"], "cross_session")
        self.assertGreaterEqual(correction[0]["count"], 2)

        template = [
            item
            for item in clusters
            if "Memory Atlas" in item["display_text"]
        ]
        self.assertEqual(len(template), 1)
        self.assertEqual(template[0]["category"], "tasks_topics")
        self.assertIn(template[0]["detection_method"], {"template", "fuzzy_lexical"})
        self.assertEqual(template[0]["count"], 2)

        automation = [item for item in clusters if item["origin"] == "codex_automation"]
        self.assertTrue(automation)
        self.assertTrue(
            any("每周同步 Codex 数据" in item["display_text"] for item in automation)
        )

    def test_validator_and_chinese_summary_pass(self) -> None:
        self.build()
        errors = validate_outputs(
            repo_root=self.repo,
            config_path=self.config,
            output_dir=self.output,
            summary_path=self.summary,
            status_path=self.status,
            check_sources=True,
        )
        self.assertEqual(errors, [])
        summary = self.summary.read_text(encoding="utf-8")
        self.assertIn("# 00｜Recurring 分析（最新）", summary)
        self.assertIn("问题与纠正", summary)
        self.assertIn("Codex Automation（隔离区）", summary)
        self.assertIn("模型/API 调用：`0`", summary)
        self.assertIn("查看原始记录", summary)
        status = self.status.read_text(encoding="utf-8")
        self.assertIn("# 00｜Recurring 运行状态", status)
        self.assertIn("**PASS**", status)
        self.assertIn("分析脚本 LLM / embedding / 外部模型 API", status)

    def test_validator_detects_human_report_tampering(self) -> None:
        self.build()
        self.summary.write_text(
            self.summary.read_text(encoding="utf-8") + "\n未经校验的修改\n",
            encoding="utf-8",
        )
        errors = validate_outputs(
            repo_root=self.repo,
            config_path=self.config,
            output_dir=self.output,
            summary_path=self.summary,
            status_path=self.status,
            check_sources=True,
        )
        self.assertIn("run_manifest output_hashes mismatch", errors)
        self.assertIn("run_manifest derived_payload_sha256 mismatch", errors)

    def test_deterministic_full_rebuild(self) -> None:
        output_a = self.repo / "build-a/recurring_prompts"
        output_b = self.repo / "build-b/recurring_prompts"
        summary_a = self.repo / "build-a/00_Recurring分析_最新.md"
        summary_b = self.repo / "build-b/00_Recurring分析_最新.md"
        status_a = self.repo / "build-a/00_Recurring运行状态.md"
        status_b = self.repo / "build-b/00_Recurring运行状态.md"
        self.build(output_dir=output_a, summary_path=summary_a, status_path=status_a, force_full=True)
        self.build(output_dir=output_b, summary_path=summary_b, status_path=status_b, force_full=True)
        self.assertEqual(compare_trees(output_a, output_b), [])
        self.assertEqual(summary_a.read_bytes(), summary_b.read_bytes())
        self.assertEqual(status_a.read_bytes(), status_b.read_bytes())

    def test_append_only_incremental_processing(self) -> None:
        self.build()
        target = self.input_dir / "session-d.part-0001.jsonl"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "type": "event_msg",
                        "timestamp": "2026-07-22T03:00:00Z",
                        "payload": {
                            "type": "user_message",
                            "message": "请分析 Memory Atlas v0.0.0.7 的 GitHub Action 产物。",
                            "turn_id": "d-turn-2",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        manifest = self.build(previous_output_dir=self.output)
        self.assertEqual(manifest["appended_files_processed"], 1)
        self.assertGreaterEqual(manifest["reused_files"], 3)
        clusters = list(iter_jsonl(self.output / "clusters.jsonl"))
        task_cluster = next(item for item in clusters if "Memory Atlas" in item["display_text"])
        self.assertEqual(task_cluster["count"], 3)


    def test_incremental_result_matches_independent_full_rebuild(self) -> None:
        self.build()
        target = self.input_dir / "session-d.part-0001.jsonl"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "type": "response_item",
                        "timestamp": "2026-07-22T03:00:00Z",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": "请分析 Memory Atlas v0.0.0.7 的 GitHub Action 产物。",
                                }
                            ],
                            "turn_id": "d-turn-2",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            handle.write(
                json.dumps(
                    {
                        "type": "event_msg",
                        "timestamp": "2026-07-22T03:00:01Z",
                        "payload": {
                            "type": "user_message",
                            "message": "请分析 Memory Atlas v0.0.0.7 的 GitHub Action 产物。",
                            "turn_id": "d-turn-2",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
        incremental_output = self.repo / "incremental/recurring_prompts"
        incremental_summary = self.repo / "incremental/00_Recurring分析_最新.md"
        incremental_status = self.repo / "incremental/00_Recurring运行状态.md"
        # Preserve the pre-append snapshot as the incremental baseline.
        baseline = self.repo / "baseline"
        shutil.copytree(self.output, baseline)
        self.build(
            output_dir=incremental_output,
            summary_path=incremental_summary,
            status_path=incremental_status,
            previous_output_dir=baseline,
        )
        full_output = self.repo / "full/recurring_prompts"
        full_summary = self.repo / "full/00_Recurring分析_最新.md"
        full_status = self.repo / "full/00_Recurring运行状态.md"
        self.build(
            output_dir=full_output,
            summary_path=full_summary,
            status_path=full_status,
            force_full=True,
        )
        self.assertEqual(compare_semantic_outputs(incremental_output, full_output), [])
        self.assertEqual(incremental_summary.read_bytes(), full_summary.read_bytes())
        self.assertEqual(incremental_status.read_bytes(), full_status.read_bytes())


    def test_human_discussion_of_scheduled_automation_stays_human(self) -> None:
        config = RuntimeConfig.load(self.config)
        origin = detect_origin(
            "请比较 scheduled automation 与 GitHub Actions，不要把这条人工讨论归为自动任务。",
            {
                "type": "user_message",
                "message": "请比较 scheduled automation 与 GitHub Actions，不要把这条人工讨论归为自动任务。",
            },
            config,
        )
        self.assertEqual(origin, "human_interactive")

    def test_markdown_in_prompt_is_rendered_as_inert_text(self) -> None:
        escaped = escape_markdown_cell("![x](https://example.com)<script>|value")
        self.assertNotIn("![x]", escaped)
        self.assertNotIn("<script>", escaped)
        self.assertIn("\\!\\[x\\]", escaped)
        self.assertIn("\\<script\\>", escaped)
        self.assertIn("\\|value", escaped)

    def test_comma_chain_is_split_into_reusable_clauses(self) -> None:
        config = RuntimeConfig.load(self.config)
        clauses = split_clauses(
            "请先核验事实，减少 Codex token 压力，最后仅交付一个压缩包。",
            "human_interactive",
            config,
        )
        self.assertEqual(
            clauses,
            ["请先核验事实，", "减少 Codex token 压力，", "最后仅交付一个压缩包。"],
        )

    def test_same_prompt_in_distinct_turns_is_not_event_deduplicated(self) -> None:
        path = self.input_dir / "session-e.part-0001.jsonl"
        rows = [
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T04:00:00Z",
                "payload": {
                    "type": "user_message",
                    "message": "请保留本次人工确认。",
                    "turn_id": "e-turn-1",
                },
            },
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T04:00:05Z",
                "payload": {
                    "type": "user_message",
                    "message": "请保留本次人工确认。",
                    "turn_id": "e-turn-2",
                },
            },
        ]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        self.build()
        clusters = list(iter_jsonl(self.output / "clusters.jsonl"))
        cluster = next(
            item for item in clusters if "请保留本次人工确认" in item["display_text"]
        )
        self.assertEqual(cluster["count"], 2)
        self.assertEqual(cluster["unique_sessions"], 1)
        self.assertEqual(cluster["scope"], "same_session")

    def test_distinct_code_payloads_without_turn_id_are_not_event_deduplicated(self) -> None:
        path = self.input_dir / "code-identity.part-0001.jsonl"
        rows = [
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T04:30:00Z",
                "payload": {
                    "type": "user_message",
                    "message": "请检查以下代码是否正确：\n```python\nprint(1)\n```",
                },
            },
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T04:30:05Z",
                "payload": {
                    "type": "user_message",
                    "message": "请检查以下代码是否正确：\n```python\nprint(2)\n```",
                },
            },
        ]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

        self.build()
        occurrences = [
            item
            for item in iter_jsonl(self.output / "occurrences.jsonl")
            if "请检查以下代码是否正确" in item["display_text"]
        ]
        self.assertEqual(len(occurrences), 2)
        clusters = list(iter_jsonl(self.output / "clusters.jsonl"))
        cluster = next(
            item for item in clusters if "请检查以下代码是否正确" in item["display_text"]
        )
        self.assertEqual(cluster["count"], 2)
        self.assertEqual(cluster["scope"], "same_session")

    def test_versioned_session_snapshots_do_not_double_count_history(self) -> None:
        first = self.input_dir / "versioned-session.hash-a.part-0001.jsonl"
        second = self.input_dir / "versioned-session.hash-b.part-0001.jsonl"
        old_event = {
            "type": "event_msg",
            "timestamp": "2026-07-22T05:00:00Z",
            "payload": {
                "type": "user_message",
                "message": "请确保跨快照历史不会重复累计。",
                "turn_id": "versioned-turn-1",
            },
        }
        new_event = {
            "type": "event_msg",
            "timestamp": "2026-07-22T05:10:00Z",
            "payload": {
                "type": "user_message",
                "message": "请确保跨快照历史不会重复累计。",
                "turn_id": "versioned-turn-2",
            },
        }
        first.write_text(json.dumps(old_event, ensure_ascii=False) + "\n", encoding="utf-8")
        second.write_text(
            json.dumps(old_event, ensure_ascii=False)
            + "\n"
            + json.dumps(new_event, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        self.build()
        occurrences = [
            item
            for item in iter_jsonl(self.output / "occurrences.jsonl")
            if "跨快照历史不会重复累计" in item["display_text"]
        ]
        self.assertEqual(len(occurrences), 2)
        clusters = list(iter_jsonl(self.output / "clusters.jsonl"))
        cluster = next(
            item for item in clusters if "跨快照历史不会重复累计" in item["display_text"]
        )
        self.assertEqual(cluster["count"], 2)
        self.assertEqual(cluster["unique_sessions"], 1)
        self.assertEqual(cluster["scope"], "same_session")

    def test_implementation_hash_is_bound_to_incremental_state(self) -> None:
        manifest = self.build()
        state = json.loads((self.output / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["implementation_sha256"], state["implementation_sha256"])
        self.assertTrue(str(state["implementation_sha256"]).startswith("sha256:"))

    def test_platform_envelopes_do_not_become_user_prompt_candidates(self) -> None:
        path = self.input_dir / "platform-envelope.part-0001.jsonl"
        rows = [
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T00:00:00Z",
                "payload": {
                    "type": "user_message",
                    "turn_id": "platform-boundary",
                    "message": (
                        "Side conversation boundary.\n\n"
                        "Everything before this boundary is inherited history."
                    ),
                },
            },
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T00:00:01Z",
                "payload": {
                    "type": "user_message",
                    "turn_id": "platform-plugins",
                    "message": (
                        "<recommended_plugins>\n- Example\n</recommended_plugins>\n\n"
                        "请只保留真实用户请求。"
                    ),
                },
            },
            {
                "type": "event_msg",
                "timestamp": "2026-07-22T00:00:02Z",
                "payload": {
                    "type": "user_message",
                    "turn_id": "platform-files",
                    "message": (
                        "# Files mentioned by the user:\n\n"
                        "## sample.zip: /Users/example/Downloads/sample.zip\n\n"
                        "## My request for Codex:\n"
                        "请只保留附件后的真实请求。"
                    ),
                },
            },
        ]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )

        manifest = self.build()
        combined = "\n".join(
            item["normalized_text"] for item in iter_jsonl(self.output / "occurrences.jsonl")
        ).lower()

        self.assertGreaterEqual(manifest["excluded_injected_messages"], 3)
        for forbidden in (
            "side conversation boundary",
            "recommended_plugins",
            "files mentioned by the user",
            "sample.zip",
        ):
            self.assertNotIn(forbidden, combined)
        self.assertIn("请只保留真实用户请求", combined)
        self.assertIn("请只保留附件后的真实请求", combined)

    def test_non_append_mutation_fails_closed(self) -> None:
        self.build()
        target = self.input_dir / "session-a.part-0001.jsonl"
        content = target.read_text(encoding="utf-8")
        target.write_text(content.replace("请先核验事实", "请先随便猜测", 1), encoding="utf-8")
        with self.assertRaises(SourceMutationError):
            self.build(previous_output_dir=self.output)


if __name__ == "__main__":
    unittest.main()
