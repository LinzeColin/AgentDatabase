from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from teleiosis_core.common import atomic_write_json


def load_json(rel: str) -> Any:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_subject(path: Path, text: str = "baseline\n") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text("---\nname: sample\ndescription: sample skill\n---\n# 示例\n", encoding="utf-8")
    (path / "payload.txt").write_text(text, encoding="utf-8")
    return path


def stage_result(workspace: Path, state: Dict[str, Any], status: str = "NOT_APPLICABLE_WITH_REASON", decision: str = "NO_CHANGE", evidence_path: Optional[Path] = None) -> Dict[str, Any]:
    index = state["next_stage_index"]
    stage = state["sequence"][index]
    manifest_map = {
        "T": "modules/raw_teleiosis/CAPABILITIES.json",
        "S": "modules/skill_market_lab/CAPABILITIES.json",
        "P": "modules/product_reality_lab/CAPABILITIES.json",
        "A": "modules/arena_lab/CAPABILITIES.json",
    }
    manifest = load_json(manifest_map[stage["module"]])
    refs: List[str] = []
    top_files: List[str] = []
    if evidence_path is not None:
        refs = [str(evidence_path)]
        top_files = [str(evidence_path)]
    caps = []
    for cap in manifest["capabilities"]:
        cap_status = status
        reason = "本测试已完成完整适用性检查并有明确依据。"
        cap_refs = refs if cap_status == "EXECUTED" else []
        caps.append({"id": cap["id"], "status": cap_status, "reason": reason, "evidence_refs": cap_refs})
    return {
        "schema_version": "teleiosis.capability_result.v5",
        "run_id": state["run_id"],
        "stage_index": index,
        "module": stage["module"],
        "candidate_revision_id": state["current_candidate"]["revision_id"],
        "decision": decision,
        "summary": "本阶段完成全部能力核验并保持证据边界。",
        "developer_burden_delta": {"closed_unknowns": [], "closed_p0_p1": [], "generated_executable_artifacts": [], "builder_tasks_removed": []},
        "capabilities": caps,
        "evidence_files": top_files,
        "arena_result": None,
    }


def load_state(workspace: Path) -> Dict[str, Any]:
    return json.loads((workspace / "RUN_STATE.json").read_text(encoding="utf-8"))


def complete_run(workspace: Path, submit_stage) -> Dict[str, Any]:
    while True:
        state = load_state(workspace)
        if state["next_stage_index"] >= 36:
            return state
        result = stage_result(workspace, state)
        path = workspace / "NEXT_STAGE.json"
        write_json(path, result)
        submit_stage(workspace, path)
