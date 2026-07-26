from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import sha256_file, write_json

# The persona-distiller-group supplies two independent six-seat panels.
# The thirteenth/final verdict is intentionally outside this request and is
# delegated to the separate verifier Skill through verifier-export.
ROLE_REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "seat": "A1",
        "panel": "A",
        "role": "Skill evolution architect",
        "focus": ["white-box architecture", "candidate isolation", "bounded evolution"],
    },
    {
        "seat": "A2",
        "panel": "A",
        "role": "Evaluation scientist",
        "focus": ["holdout integrity", "equal-budget trials", "negative transfer"],
    },
    {
        "seat": "A3",
        "panel": "A",
        "role": "Competitive intelligence analyst",
        "focus": ["peer qualification", "mechanism transfer", "category-error detection"],
    },
    {
        "seat": "A4",
        "panel": "A",
        "role": "Security and authority reviewer",
        "focus": ["untrusted inputs", "secret boundaries", "fail-closed controls"],
    },
    {
        "seat": "A5",
        "panel": "A",
        "role": "Release and recovery engineer",
        "focus": ["deterministic package", "atomic install", "rollback and recovery"],
    },
    {
        "seat": "A6",
        "panel": "A",
        "role": "Operator UX specialist",
        "focus": ["activation", "status legibility", "human error reduction"],
    },
    {
        "seat": "B1",
        "panel": "B",
        "role": "Cost and efficiency analyst",
        "focus": ["token and cost evidence", "operator burden", "non-negative utility"],
    },
    {
        "seat": "B2",
        "panel": "B",
        "role": "Runtime portability engineer",
        "focus": ["environment diagnosis", "adapter boundaries", "cross-runtime evidence"],
    },
    {
        "seat": "B3",
        "panel": "B",
        "role": "Failure-mechanism investigator",
        "focus": ["root causes", "reproducibility", "bounded corrective action"],
    },
    {
        "seat": "B4",
        "panel": "B",
        "role": "Evidence and provenance auditor",
        "focus": ["requirement traceability", "hash binding", "claim and evidence separation"],
    },
    {
        "seat": "B5",
        "panel": "B",
        "role": "Productization and adoption reviewer",
        "focus": ["installation", "showcase", "operator adoption", "release clarity"],
    },
    {
        "seat": "B6",
        "panel": "B",
        "role": "Counterevidence red team",
        "focus": ["claim falsification", "hidden regressions", "market-leadership challenge"],
        "control_role": True,
    },
]


def export_expert_panel_request(
    output: Path,
    task: str,
    valid_as_of: str,
    persona_index: Optional[Path] = None,
) -> Dict[str, Any]:
    if not task.strip():
        raise ValueError("expert panel task cannot be empty")
    if not valid_as_of or len(valid_as_of) != 10:
        raise ValueError("valid_as_of must be YYYY-MM-DD")
    index_binding = None
    if persona_index:
        if not persona_index.is_file() or persona_index.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("persona index missing or exceeds 10 MiB")
        index_binding = {
            "path": str(persona_index.resolve()),
            "sha256": sha256_file(persona_index),
            "bytes": persona_index.stat().st_size,
        }
    panel_counts = {
        panel: sum(1 for role in ROLE_REQUIREMENTS if role["panel"] == panel)
        for panel in ("A", "B")
    }
    packet = {
        "schema_version": "1.0",
        "request_type": "persona-distiller-group-routing",
        "valid_as_of": valid_as_of,
        "task": task.strip(),
        "formal_review_shape": "2x6-plus-separate-verifier",
        "panel_size": len(ROLE_REQUIREMENTS),
        "panel_counts": panel_counts,
        "role_requirements": ROLE_REQUIREMENTS,
        "persona_index_binding": index_binding,
        "routing_policy": {
            "ready_personas_only": True,
            "panel_a_and_b_must_be_context_isolated": True,
            "same_person_or_same_context_cannot_claim_independence": True,
            "counterevidence_role_must_be_isolated": True,
            "external_final_verifier_required": True,
            "persona_panel_cannot_grant_formal_promotion": True,
            "missing_roster_must_not_be_filled_with_fabricated_people": True,
            "neutral_functional_roles_allowed_but_not_independent": True,
        },
        "required_outputs": [
            "seat-to-persona mapping with source provenance",
            "Panel A individual findings before synthesis",
            "Panel B individual findings before synthesis",
            "counterevidence register",
            "cross-panel conflict and dependency matrix",
            "panel conclusions with unresolved unknowns",
            "handoff to the separate verifier Skill without a self-issued final verdict",
        ],
        "routing_status": "READY_FOR_PERSONA_DISTILLER" if index_binding else "ROSTER_INPUT_REQUIRED",
        "independent_review_completed": False,
        "external_verifier_completed": False,
        "formal_promotion_granted": False,
    }
    write_json(output, packet)
    return {
        "status": "PASS",
        "output": str(output.resolve()),
        "routing_status": packet["routing_status"],
        "panel_size": len(ROLE_REQUIREMENTS),
        "panel_counts": panel_counts,
        "external_verifier_required": True,
    }
