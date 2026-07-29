from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Sequence, Tuple

from .common import (
    ValidationError,
    object_sha256,
    stable_id,
    strip_internal_fields,
    utc_now,
    write_json,
    write_jsonl,
)
from .specs import assert_valid, validate_experiment_spec, validate_task


WORKSPACE_DIRS = (
    "config",
    "datasets/development",
    "datasets/validation",
    "datasets/sealed_holdout",
    "datasets/adversarial",
    "datasets/market_live",
    "datasets/incident_replay",
    "assignments/controller_only",
    "runs/raw",
    "feedback/raw",
    "reports",
    "evidence",
    "seals",
)


def initialize_workspace(
    workspace: Path,
    template_spec: Mapping[str, Any],
    force: bool = False,
) -> Dict[str, Any]:
    if workspace.exists() and any(workspace.iterdir()) and not force:
        raise ValidationError(f"工作区非空，拒绝覆盖: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    for relative in WORKSPACE_DIRS:
        (workspace / relative).mkdir(parents=True, exist_ok=True)
    spec = json.loads(json.dumps(template_spec))
    errors = validate_experiment_spec(spec)
    assert_valid(errors, "实验模板")
    write_json(workspace / "config" / "experiment.json", spec)
    state = {
        "schema_version": "1.0",
        "experiment_id": spec["experiment_id"],
        "state": "CONTEXT_CAPTURE",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "allowed_states": [
            "CONTEXT_CAPTURE",
            "RESEARCH_AND_REUSE",
            "PREBUILD",
            "TEN_LENS_REVIEW",
            "REMEDIATION",
            "BUILDER_READINESS",
            "OWNER_GATE",
            "SEALED_TASKPACK",
            "BUILD_LAST_MILE",
            "FROZEN_CANDIDATE",
            "VERIFY_AND_RELEASE",
            "POST_DEPLOY_OBSERVATION",
        ],
        "notes": ["运行数据必须写入此工作区或授权私有事实层，不得写入 Skill 代码目录。"],
    }
    write_json(workspace / "CANONICAL_STATE.json", state)
    return state


def _blind_codes(spec: Mapping[str, Any]) -> Dict[str, str]:
    arms = [str(arm["id"]) for arm in spec["arms"]]
    shuffled = list(arms)
    rng = random.Random(f"{spec['seed']}:{spec['experiment_id']}:blind-map")
    rng.shuffle(shuffled)
    codes = [f"condition-{index + 1:02d}-{object_sha256([spec['experiment_id'], arm])[:6]}" for index, arm in enumerate(shuffled)]
    return dict(zip(shuffled, codes))


def make_assignments(
    spec: Mapping[str, Any],
    tasks: Iterable[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    assert_valid(validate_experiment_spec(spec), "实验规范")
    arm_ids = [str(arm["id"]) for arm in spec["arms"]]
    blind_codes = _blind_codes(spec)
    assignments: List[Dict[str, Any]] = []
    task_count = 0
    for raw_task in tasks:
        task = strip_internal_fields(raw_task)
        assert_valid(validate_task(task), f"任务 {task.get('task_id', '<unknown>')}")
        task_count += 1
        for repetition in range(1, int(spec["repetitions"]) + 1):
            ordered_arms = list(arm_ids)
            rng = random.Random(f"{spec['seed']}:{task['task_id']}:{repetition}:sequence")
            rng.shuffle(ordered_arms)
            for sequence, arm_id in enumerate(ordered_arms, 1):
                assignment_payload = {
                    "experiment_id": spec["experiment_id"],
                    "task_id": task["task_id"],
                    "partition": task["partition"],
                    "repetition": repetition,
                    "sequence": sequence,
                    "condition_code": blind_codes[arm_id],
                    "prompt": task["prompt"],
                    "oracle": task["oracle"],
                    "protected": bool(task.get("protected", False)),
                    "origin": task["origin"],
                    "sensitivity": task.get("sensitivity", "public"),
                    "consent_ref": task.get("consent_ref"),
                    "metadata": task.get("metadata", {}),
                }
                assignment_payload["assignment_id"] = stable_id("asg", assignment_payload, 20)
                assignments.append(assignment_payload)
    blind_map = {
        "schema_version": "1.0",
        "experiment_id": spec["experiment_id"],
        "created_at": utc_now(),
        "controller_only": True,
        "task_count": task_count,
        "repetitions": spec["repetitions"],
        "mapping": {code: arm_id for arm_id, code in blind_codes.items()},
        "warning": "不得向 Candidate、生成器或评委泄露。",
    }
    return assignments, blind_map


def write_assignments(
    spec: Mapping[str, Any],
    tasks: Iterable[Mapping[str, Any]],
    assignments_path: Path,
    blind_map_path: Path,
) -> Dict[str, int]:
    assignments, blind_map = make_assignments(spec, tasks)
    assignment_count = write_jsonl(assignments_path, assignments)
    write_json(blind_map_path, blind_map)
    return {"assignments": assignment_count, "tasks": int(blind_map["task_count"])}


def make_holdout_manifest(tasks: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    entries = []
    for raw_task in tasks:
        task = strip_internal_fields(raw_task)
        assert_valid(validate_task(task), f"任务 {task.get('task_id', '<unknown>')}")
        if task["partition"] != "sealed_holdout":
            continue
        entries.append(
            {
                "task_id": task["task_id"],
                "task_digest": object_sha256(task),
                "oracle_digest": object_sha256(task["oracle"]),
                "content_disclosed": False,
            }
        )
    entries.sort(key=lambda item: item["task_id"])
    manifest = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "partition": "sealed_holdout",
        "count": len(entries),
        "entries": entries,
        "manifest_digest": object_sha256(entries),
    }
    return manifest


def make_candidate_visible_dataset(tasks: Iterable[Mapping[str, Any]]) -> Iterator[Dict[str, Any]]:
    for raw_task in tasks:
        task = strip_internal_fields(raw_task)
        assert_valid(validate_task(task), f"任务 {task.get('task_id', '<unknown>')}")
        if task["partition"] == "sealed_holdout":
            continue
        sanitized = dict(task)
        if sanitized.get("sensitivity") == "restricted":
            sanitized["prompt"] = "[REDACTED_RESTRICTED_TASK_CONTENT]"
            sanitized["oracle"] = {"type": "external_controller", "content_disclosed": False}
        sanitized.pop("consent_ref", None)
        yield sanitized
