#!/usr/bin/env python3
"""Load the real reasoning payload for routed persona experts.

The route plan can expose `members`, `domain_experts`, `selected_roles`, or the
legacy `roster` field. Control-plane roles are ignored here because they are
neutral runtime controls rather than persona products.

No dossier means no expert-team execution. Missing products are reported rather
than replaced with invented personas.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from team_runtime_common import read_json, unique_preserving_order, write_json

RIGOROUS = {
    "mental-model": "mental_models",
    "heuristic": "heuristics",
    "value": "values",
    "work-method": "work_methods",
    "blind-spot": "blind_spots",
    "contradiction": "contradictions",
}


def registry_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_index(root: Path) -> dict[str, Any]:
    return read_json(root / "team-index.json")


def route_persona_slugs(plan: dict[str, Any]) -> list[str]:
    rows: list[Any] = []
    for key in ("members", "domain_experts", "selected_roles", "roster"):
        value = plan.get(key)
        if isinstance(value, list):
            rows.extend(value)
    slugs: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("role_type") == "control":
            continue
        slug = row.get("subject_slug")
        if slug:
            slugs.append(str(slug))
    return unique_preserving_order(slugs)


def find_delivery(root: Path, slug: str, card: dict[str, Any] | None = None) -> Path | None:
    if card and card.get("latest_artifact"):
        preferred = root / str(card["latest_artifact"])
        if preferred.is_file():
            return preferred
    hits = sorted(root.glob(f"*/{slug}/versions/*/*.zip"))
    return hits[-1] if hits else None


@contextmanager
def open_runtime(path: Path) -> Iterator[zipfile.ZipFile]:
    outer = zipfile.ZipFile(path)
    inner_name = next(
        (name for name in outer.namelist() if "/runtime/" in name and name.endswith(".zip")),
        None,
    )
    if inner_name is None:
        try:
            yield outer
        finally:
            outer.close()
        return
    inner_bytes = io.BytesIO(outer.read(inner_name))
    outer.close()
    inner = zipfile.ZipFile(inner_bytes)
    try:
        yield inner
    finally:
        inner.close()
        inner_bytes.close()


def _read_text(zf: zipfile.ZipFile, suffixes: tuple[str, ...]) -> str:
    name = next((n for n in zf.namelist() if any(n.endswith(suffix) for suffix in suffixes)), None)
    return zf.read(name).decode("utf-8", errors="replace") if name else ""


def _bullets(text: str, limit: int = 30) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("- ", "* ", "+ ")):
            continue
        value = stripped[2:].strip()
        if len(value) >= 8:
            rows.append(value)
    return unique_preserving_order(rows)[:limit]


def _confidence_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").casefold()
    return {"high": 0.9, "medium": 0.65, "low": 0.35}.get(text, 0.5)


def _compact_claims(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: (-_confidence_value(row.get("confidence")), str(row.get("claim_id") or "")),
    )
    return ordered[:limit]


def read_persona_payload(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "mental_models": [],
        "heuristics": [],
        "values": [],
        "work_methods": [],
        "blind_spots": [],
        "contradictions": [],
        "hard_boundaries": [],
        "claim_index": {},
        "divergence_text": "",
        "runtime_files_loaded": [],
    }
    with open_runtime(path) as zf:
        names = zf.namelist()
        claims_name = next((n for n in names if n.endswith("evidence/claims.jsonl")), None)
        if claims_name:
            payload["runtime_files_loaded"].append(claims_name)
            for line in zf.read(claims_name).decode("utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    claim = json.loads(line)
                except json.JSONDecodeError:
                    continue
                bucket = RIGOROUS.get(str(claim.get("category")))
                if not bucket:
                    continue
                record = {
                    "claim_id": claim.get("claim_id"),
                    "claim": claim.get("claim"),
                    "falsifiers": claim.get("falsifiers", []),
                    "confidence": claim.get("confidence"),
                    "time_scope": claim.get("time_scope"),
                    "source_ids": claim.get("source_ids", claim.get("sources", [])),
                }
                payload[bucket].append(record)
                if record["claim_id"]:
                    payload["claim_index"][record["claim_id"]] = str(record.get("claim") or "")[:220]

        boundaries = _read_text(zf, ("boundaries.md",))
        if boundaries:
            payload["runtime_files_loaded"].append("boundaries.md")
            payload["hard_boundaries"] = _bullets(boundaries, 40)

        divergence = _read_text(zf, ("divergence-map.md",))
        if divergence:
            payload["runtime_files_loaded"].append("divergence-map.md")
            payload["divergence_text"] = divergence

        for label, suffixes in {
            "cognitive_os_text": ("cognitive-os.md",),
            "decision_policy_text": ("decision-policy.md",),
            "capabilities_text": ("capabilities.md",),
            "work_text": ("work.md",),
            "persona_text": ("persona.md",),
        }.items():
            text = _read_text(zf, suffixes)
            if text:
                payload[label] = text[:8000]
                payload["runtime_files_loaded"].append(suffixes[0])

    for bucket in RIGOROUS.values():
        payload[bucket] = _compact_claims(payload[bucket])
    return payload


def compile_capsules(payload: dict[str, Any], card: dict[str, Any]) -> dict[str, Any]:
    methods = payload["mental_models"] + payload["heuristics"] + payload["work_methods"]
    evidence = [
        {"claim_id": claim_id, "claim": text}
        for claim_id, text in list(payload["claim_index"].items())[:30]
    ]
    failures = payload["blind_spots"] + payload["contradictions"]
    return {
        "method_capsule": _compact_claims(methods, 18),
        "evidence_capsule": evidence,
        "work_capsule": _compact_claims(payload["work_methods"], 12),
        "failure_capsule": _compact_claims(failures, 12),
        "boundary_capsule": unique_preserving_order(
            payload["hard_boundaries"] + list(card.get("hard_boundaries", []))
        )[:40],
        "currentness_capsule": {
            "subject_status": card.get("subject_status"),
            "subject_active_through": card.get("subject_active_through"),
            "research_cutoff": card.get("research_cutoff"),
            "current_facts_rule": "Current facts come from a dated factual lane, never from historical persona authority.",
        },
        "voice_capsule": {
            "enabled": False,
            "traits": card.get("distillation_traits", []),
            "rule": "Voice is disabled unless the user explicitly requests expression-style transformation.",
        },
    }


def extract_divergences(members: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract only exact full-name or exact slug references; never surname proxies."""
    found: list[dict[str, Any]] = []
    identity = {
        member["subject_slug"]: {
            "name": member["canonical_name"],
            "slug": member["subject_slug"],
        }
        for member in members
    }
    for member in members:
        text = str(member.pop("divergence_text", "") or "")
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if len(p.strip()) >= 40]
        for other_slug, other in identity.items():
            if other_slug == member["subject_slug"]:
                continue
            needles = [str(other["name"]).casefold(), str(other["slug"]).casefold()]
            for paragraph in paragraphs:
                low = paragraph.casefold()
                if any(needle and needle in low for needle in needles):
                    found.append({
                        "between": sorted([member["canonical_name"], other["name"]]),
                        "stated_by": member["canonical_name"],
                        "source_subject_slug": member["subject_slug"],
                        "text": paragraph[:900],
                        "match_rule": "exact-full-name-or-slug",
                    })
                    break
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in found:
        key = ("|".join(row["between"]), row["stated_by"], row["text"][:120])
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def roster_composition(cards: list[dict[str, Any]]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for card in cards:
        status = str(card.get("subject_status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    years = [
        int(card["subject_active_through"])
        for card in cards
        if isinstance(card.get("subject_active_through"), int)
    ]
    return {
        "persona_expert_count": len(cards),
        "status_counts": statuses,
        "active_through_range": [min(years), max(years)] if years else None,
        "controls_excluded_from_count": True,
    }


def build_dossier(root: Path, slugs: list[str], route_plan: dict[str, Any] | None = None) -> dict[str, Any]:
    index = load_index(root)
    by_slug = {row.get("subject_slug"): row for row in index.get("products", []) if row.get("subject_slug")}
    members: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []

    for slug in unique_preserving_order(slugs):
        card = by_slug.get(slug)
        if not card:
            missing.append({"subject_slug": slug, "reason": "not in canonical team-index"})
            continue
        delivery = find_delivery(root, slug, card)
        if not delivery:
            missing.append({"subject_slug": slug, "reason": "delivery ZIP not found"})
            continue
        try:
            payload = read_persona_payload(delivery)
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            missing.append({"subject_slug": slug, "reason": f"runtime payload unreadable: {exc}"})
            continue
        payload.update({
            "canonical_name": card.get("canonical_name"),
            "subject_slug": slug,
            "subject_uid": card.get("subject_uid"),
            "registration_category": card.get("registration_category"),
            "identity_family_id": card.get("identity_family_id"),
            "known_distortions": card.get("distillation_traits", []),
            "refusal_template": card.get("hard_boundaries", []),
            "subject_status": card.get("subject_status"),
            "subject_active_through": card.get("subject_active_through"),
            "research_cutoff": card.get("research_cutoff"),
            "artifact_path": str(delivery.relative_to(root)),
        })
        payload["capsules"] = compile_capsules(payload, card)
        payload["payload_loaded"] = bool(payload["claim_index"] or payload["hard_boundaries"])
        members.append(payload)
        cards.append(card)

    divergences = extract_divergences(members)
    expected = len(unique_preserving_order(slugs))
    loaded = len(members)
    status = "ready" if expected > 0 and loaded == expected else "blocked_missing_payload"
    return {
        "schema_version": "persona-team.dossier.v2",
        "status": status,
        "requested_persona_experts": expected,
        "loaded_persona_experts": loaded,
        "members": members,
        "missing": missing,
        "divergences": divergences,
        "roster_composition": roster_composition(cards),
        "control_plane": (route_plan or {}).get("control_plane", []),
        "usage_contract": [
            "Every substantive persona contribution cites that persona's own claim_id.",
            "Hard boundaries and refusal templates apply before generation.",
            "Documented divergences are surfaced and adjudicated; they are not averaged away.",
            "Voice is off by default; method, evidence, work and failure capsules take priority.",
            "Missing persona payload blocks execution; no substitute persona is invented.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the real persona-team dossier and capsules.")
    parser.add_argument("--slugs", nargs="*", default=[])
    parser.add_argument("--route-plan", type=Path)
    parser.add_argument("--registry-root", type=Path, default=registry_root())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    plan: dict[str, Any] | None = None
    slugs = list(args.slugs)
    if args.route_plan and args.route_plan.is_file():
        plan = read_json(args.route_plan)
        slugs.extend(route_persona_slugs(plan))
    slugs = unique_preserving_order(slugs)
    if not slugs:
        print(json.dumps({"status": "blocked", "reason": "no persona slugs in arguments or route plan"}, ensure_ascii=False))
        return 2

    dossier = build_dossier(args.registry_root.resolve(), slugs, plan)
    if args.output:
        write_json(args.output, dossier)
        print(json.dumps({
            "written": str(args.output),
            "status": dossier["status"],
            "loaded": dossier["loaded_persona_experts"],
            "requested": dossier["requested_persona_experts"],
        }, ensure_ascii=False))
    else:
        print(json.dumps(dossier, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if dossier["status"] == "ready" else 3


if __name__ == "__main__":
    raise SystemExit(main())
