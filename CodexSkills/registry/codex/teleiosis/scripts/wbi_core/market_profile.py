from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .io import sha256_file, write_json


def _has(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _count_files(root: Path, patterns: List[str]) -> int:
    total = 0
    for pattern in patterns:
        total += sum(1 for item in root.glob(pattern) if item.is_file())
    return total


def _top_markers(root: Path) -> Dict[str, Any]:
    return {
        "skill_md": _has(root, "SKILL.md"),
        "genesis_lock": _has(root, "constitution/genesis-lock.json"),
        "schemas_dir": _has(root, "schemas"),
        "scripts_dir": _has(root, "scripts"),
        "tests_dir": _has(root, "tests"),
        "dockerfile": _has(root, "Dockerfile"),
        "makefile": _has(root, "Makefile"),
        "configs_dir": _has(root, "configs"),
        "deploy_dir": _has(root, "deploy"),
        "web_dir": _has(root, "web") or _has(root, "web-src"),
        "package_json": _has(root, "package.json"),
        "pyproject": _has(root, "pyproject.toml"),
        "go_mod": _has(root, "go.mod"),
        "gradle": _has(root, "build.gradle") or _has(root, "build.gradle.kts") or _has(root, "settings.gradle.kts"),
        "readme": _has(root, "README.md"),
        "license": _has(root, "LICENSE") or _has(root, "LICENSE.txt"),
        "json_schema_count": _count_files(root / "schemas", ["*.json"]) if (root / "schemas").is_dir() else 0,
        "test_file_count": _count_files(root / "tests", ["test_*.py", "*.spec.ts", "*.test.ts", "*.test.js"]) if (root / "tests").is_dir() else 0,
    }


def _classify(markers: Dict[str, Any]) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if markers["skill_md"] and markers["genesis_lock"]:
        reasons.append("SKILL.md + locked Genesis markers")
        return "self-evolving-agent-skill", reasons
    if markers["skill_md"]:
        reasons.append("SKILL.md marker")
        return "agent-skill", reasons
    runtime_score = sum(1 for key in ["dockerfile", "makefile", "configs_dir", "deploy_dir", "web_dir", "go_mod"] if markers[key])
    if runtime_score >= 3:
        reasons.append("runtime/deploy markers >= 3")
        return "runtime-service", reasons
    if markers["gradle"] or markers["pyproject"] or markers["go_mod"]:
        reasons.append("library/package build marker")
        return "library-or-tooling", reasons
    if markers["package_json"] or markers["web_dir"]:
        reasons.append("frontend/web marker")
        return "web-product", reasons
    reasons.append("insufficient typed markers")
    return "unknown-or-documentation", reasons


def _adoption_lanes(target_class: str, markers: Dict[str, Any]) -> List[Dict[str, Any]]:
    lanes: List[Dict[str, Any]] = []
    lanes.append({
        "lane_id": "luban-no-negative-optimization",
        "source_pattern": "Luban: adaptive compression plus pass-through fallback when output is worse than input",
        "teleiosis_action": "protect baseline outcome, safety, installability, recovery and cost; hard regression cannot be averaged away",
        "mandatory": True,
    })
    lanes.append({
        "lane_id": "luban-adaptive-target-routing",
        "source_pattern": "Luban: choose compression strategy from image dimensions and content profile",
        "teleiosis_action": "route target into skill/service/library/web/unknown profile before selecting gates and evidence",
        "mandatory": True,
    })
    lanes.append({
        "lane_id": "verifier-exact-subject-identity",
        "source_pattern": "Verifier: one immutable subject, traceability and fail-closed verdicts",
        "teleiosis_action": "bind candidate tree hash, benchmark contract, artifact and install receipt before any positive claim",
        "mandatory": True,
    })
    lanes.append({
        "lane_id": "persona-isolated-control-roles",
        "source_pattern": "PersonaDistillerGroup: separate forward experts, counterevidence, adjudication and review",
        "teleiosis_action": "use expert routing for discovery but require external receipt before formal independence",
        "mandatory": False,
    })
    if target_class in {"runtime-service", "web-product", "self-evolving-agent-skill"} or markers.get("dockerfile"):
        lanes.append({
            "lane_id": "easydarwin-operations-control-plane",
            "source_pattern": "EasyDarwin: web interface, protocol distribution, monitoring, deployment and runtime status",
            "teleiosis_action": "require status, deploy/recover, config, protocol adapter and rollback evidence for productized skill delivery",
            "mandatory": target_class == "runtime-service",
        })
    if target_class in {"runtime-service", "web-product"} or markers.get("web_dir"):
        lanes.append({
            "lane_id": "easydarwin-protocol-gateway",
            "source_pattern": "EasyDarwin: RTMP/RTSP/HLS/HTTP-FLV/WebSocket-FLV/WebRTC protocol fan-out",
            "teleiosis_action": "separate GitHub, ZIP, runtime status, provider receipt and verifier evidence protocols instead of mixing evidence narratives",
            "mandatory": False,
        })
    return lanes


def build_market_profile(target: Path, *, valid_as_of: str = "") -> Dict[str, Any]:
    root = target.resolve()
    if not root.exists():
        return {"profile_status": "FAIL", "errors": ["target does not exist: %s" % root]}
    if not root.is_dir():
        return {"profile_status": "FAIL", "errors": ["target must be a directory: %s" % root]}
    markers = _top_markers(root)
    target_class, reasons = _classify(markers)
    root_files = []
    for name in ["SKILL.md", "README.md", "VERSION", "LICENSE", "LICENSE.txt", "Dockerfile", "Makefile", "go.mod", "package.json", "pyproject.toml", "build.gradle.kts"]:
        path = root / name
        if path.is_file():
            root_files.append({"path": name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    risk_flags = []
    if not markers["readme"]:
        risk_flags.append("missing-readme")
    if not markers["license"]:
        risk_flags.append("missing-license-or-nonstandard-license-path")
    if target_class in {"agent-skill", "self-evolving-agent-skill"} and markers["test_file_count"] == 0:
        risk_flags.append("skill-has-no-detected-test-files")
    if target_class == "runtime-service" and not (markers["configs_dir"] and markers["deploy_dir"]):
        risk_flags.append("runtime-service-lacks-config-or-deploy-marker")
    return {
        "profile_status": "PASS",
        "schema_version": "1.0",
        "valid_as_of": valid_as_of,
        "target": str(root),
        "target_class": target_class,
        "classification_reasons": reasons,
        "markers": markers,
        "root_file_bindings": root_files,
        "adoption_lanes": _adoption_lanes(target_class, markers),
        "risk_flags": risk_flags,
        "next_required_evidence": [
            "freeze baseline tree hash before mutation",
            "seal research and benchmark contracts before first patch",
            "run no-negative-optimization guard against protected tasks",
            "record exact cost/token/latency unknowns instead of zero",
            "package one deterministic ZIP with install, status, recovery and rollback evidence",
        ],
    }


def write_market_profile(target: Path, output: Path, *, valid_as_of: str = "") -> Dict[str, Any]:
    result = build_market_profile(target, valid_as_of=valid_as_of)
    write_json(output, result)
    return result
