#!/usr/bin/env python3
"""Build an admission ledger for persona products consumed by the team runtime.

This is a producer-consumer gate. It does not rebuild Persona Distiller products;
it decides whether a registered product is eligible, restricted to a measured
scope, or blocked from team routing.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from team_runtime_common import clamp, flatten_text, read_json, write_json

NEGATIVE_SCOPE = (
    "plain model wins",
    "do not route here expecting a generally better answer",
    "不应被路由为一般性",
    "不得路由为一般性",
    "negative delta",
)


def parse_date(value: Any) -> date | None:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def artifact_exists(root: Path, card: dict[str, Any]) -> bool:
    artifact = card.get("latest_artifact")
    return bool(artifact and (root / str(artifact)).is_file())


def score_card(root: Path, card: dict[str, Any], require_artifacts: bool) -> dict[str, Any]:
    dimensions = {
        "canonical_identity": 100 if card.get("subject_uid") and card.get("subject_slug") else 0,
        "capability_definition": 100 if card.get("key_capabilities") else 0,
        "scenario_definition": 100 if card.get("application_scenarios") else 0,
        "boundary_definition": 100 if card.get("hard_boundaries") else 0,
        "artifact_registration": 100 if card.get("latest_artifact") and card.get("team_card") else 25,
        "readiness": 100 if card.get("readiness") == "ready" else 0,
        "currentness_metadata": 100 if card.get("subject_status") and card.get("research_cutoff") else 45,
        "measured_scope_clarity": 100 if card.get("user_value") else 40,
    }
    actual_artifact = artifact_exists(root, card)
    if require_artifacts:
        dimensions["runtime_payload_presence"] = 100 if actual_artifact else 0
    else:
        dimensions["runtime_payload_presence"] = 100 if actual_artifact else 65

    score = sum(dimensions.values()) / len(dimensions)
    reasons: list[str] = []
    admission = "eligible"

    if card.get("readiness") != "ready" or not card.get("subject_slug"):
        admission = "blocked"
        reasons.append("canonical readiness gate failed")
    if require_artifacts and not actual_artifact:
        admission = "blocked"
        reasons.append("registered runtime delivery is absent in this checkout")

    measured_text = flatten_text(card.get("user_value")).casefold()
    if any(marker in measured_text for marker in NEGATIVE_SCOPE):
        if admission != "blocked":
            admission = "restricted"
        reasons.append("measured scope warns against general routing")

    cutoff = parse_date(card.get("research_cutoff"))
    if card.get("subject_status") == "living" and cutoff and (date.today() - cutoff).days > 730:
        if admission == "eligible":
            admission = "restricted"
        reasons.append("living-person evidence cutoff is older than two years")

    if score < 55:
        admission = "blocked"
        reasons.append("fleet quality score below 55")
    elif score < 75 and admission == "eligible":
        admission = "restricted"
        reasons.append("fleet quality score below the global 75 floor")

    return {
        "subject_uid": card.get("subject_uid"),
        "subject_slug": card.get("subject_slug"),
        "canonical_name": card.get("canonical_name"),
        "registration_category": card.get("registration_category"),
        "admission": admission,
        "fleet_quality_score": round(score, 2),
        "dimensions": dimensions,
        "runtime_payload_observed": actual_artifact,
        "routing_scope": "measured-only" if admission == "restricted" else "normal" if admission == "eligible" else "none",
        "reasons": reasons,
    }


def build_admission(root: Path, require_artifacts: bool = False) -> dict[str, Any]:
    index = read_json(root / "team-index.json")
    experts = [score_card(root, card, require_artifacts) for card in index.get("products", [])]
    counts = Counter(row["admission"] for row in experts)
    categories = Counter(row["registration_category"] for row in experts if row["admission"] != "blocked")
    category_gaps = [category for category, count in index.get("category_counts", {}).items() if int(count) == 0]
    floor_failures = [row["subject_slug"] for row in experts if row["fleet_quality_score"] < 75]
    return {
        "schema_version": "persona-team.fleet-admission.v1",
        "generated_on": date.today().isoformat(),
        "source_generator_version": index.get("generator_version"),
        "require_artifacts": require_artifacts,
        "summary": {
            "registry_products": len(experts),
            "admission_counts": dict(counts),
            "admitted_category_counts": dict(categories),
            "zero_roster_categories": category_gaps,
            "global_floor": 75,
            "below_floor_count": len(floor_failures),
        },
        "experts": experts,
        "contract": {
            "eligible": "may be routed within declared capabilities and boundaries",
            "restricted": "may be routed only when the measured scope explicitly matches",
            "blocked": "must not be routed until the producer artifact or metadata is repaired",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create persona fleet admission for the expert-team consumer.")
    parser.add_argument("--registry-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-artifacts", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_admission(args.registry_root.resolve(), args.require_artifacts)
    output = args.output or args.registry_root / "expert-fleet-admission.json"
    write_json(output, result)
    print(json.dumps({"written": str(output), **result["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
