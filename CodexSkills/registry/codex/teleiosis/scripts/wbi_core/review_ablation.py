from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .io import load_json, utc_now, write_json

SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _non_negative(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value >= 0


def _percentile(values: Sequence[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def validate_review_ablation_study(study: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(study, dict):
        return ["review ablation study must be an object"]
    if study.get("schema_version") != "1.0":
        errors.append("review ablation schema_version must be 1.0")
    if study.get("evidence_class") not in {"REAL_REVIEW", "FIXTURE"}:
        errors.append("review ablation evidence_class must be REAL_REVIEW or FIXTURE")
    packet_hash = study.get("packet_index_sha256")
    if not _is_hash(packet_hash):
        errors.append("review ablation packet_index_sha256 invalid")
    reviews = study.get("reviews")
    if not isinstance(reviews, list) or len(reviews) < 13:
        errors.append("review ablation requires 12 reviewers plus a distinct final verifier")
        reviews = []
    review_ids: Set[str] = set()
    actors: Set[str] = set()
    contexts: Set[str] = set()
    provider_runs: Set[str] = set()
    for index, review in enumerate(reviews, 1):
        if not isinstance(review, dict):
            errors.append("review %d must be an object" % index)
            continue
        for key in ("review_id", "actor_id", "context_id", "provider_run_id", "provider", "model_family"):
            if not isinstance(review.get(key), str) or not str(review.get(key)).strip():
                errors.append("review %d %s missing" % (index, key))
        for key, collection in (("review_id", review_ids), ("actor_id", actors), ("context_id", contexts), ("provider_run_id", provider_runs)):
            value = review.get(key)
            if isinstance(value, str):
                if value in collection:
                    errors.append("review %s reused: %s" % (key, value))
                collection.add(value)
        if review.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}:
            errors.append("review %d verdict invalid" % index)
        if study.get("evidence_class") == "REAL_REVIEW" and review.get("independent_attestation_status") != "PASS":
            errors.append("REAL_REVIEW requires independently attested review %s" % review.get("review_id"))
        findings = review.get("findings")
        if not isinstance(findings, list):
            errors.append("review %d findings must be a list" % index)
        else:
            seen_issues: Set[str] = set()
            for finding_index, finding in enumerate(findings, 1):
                if not isinstance(finding, dict):
                    errors.append("review %d finding %d must be an object" % (index, finding_index))
                    continue
                issue = finding.get("issue_id")
                if not isinstance(issue, str) or not issue:
                    errors.append("review %d finding %d issue_id missing" % (index, finding_index))
                elif issue in seen_issues:
                    errors.append("review %d duplicates issue_id %s" % (index, issue))
                seen_issues.add(issue)
                if finding.get("severity") not in SEVERITIES:
                    errors.append("review %d finding %d severity invalid" % (index, finding_index))
                if not isinstance(finding.get("supported"), bool):
                    errors.append("review %d finding %d supported must be boolean" % (index, finding_index))
        for key in ("tokens", "monetary_cost"):
            value = review.get(key)
            if value is not None and not _non_negative(value):
                errors.append("review %d %s must be null or non-negative" % (index, key))
        for key in ("latency_ms", "human_minutes"):
            if not _non_negative(review.get(key)):
                errors.append("review %d %s must be non-negative" % (index, key))

    cohorts = study.get("cohorts")
    if not isinstance(cohorts, list) or not cohorts:
        errors.append("review ablation cohorts missing")
        cohorts = []
    cohort_ids: Set[str] = set()
    sizes: Set[int] = set()
    for index, cohort in enumerate(cohorts, 1):
        if not isinstance(cohort, dict):
            errors.append("cohort %d must be an object" % index)
            continue
        cohort_id = cohort.get("cohort_id")
        if not isinstance(cohort_id, str) or not cohort_id:
            errors.append("cohort %d id missing" % index)
        elif cohort_id in cohort_ids:
            errors.append("duplicate cohort_id: %s" % cohort_id)
        cohort_ids.add(str(cohort_id))
        ids = cohort.get("review_ids")
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            errors.append("cohort %s review_ids must be a unique non-empty list" % cohort_id)
            continue
        missing = set(ids) - review_ids
        if missing:
            errors.append("cohort %s references unknown reviews: %s" % (cohort_id, sorted(missing)))
        sizes.add(len(ids))
        verifier_id = cohort.get("verifier_id")
        if verifier_id is not None and verifier_id not in review_ids:
            errors.append("cohort %s verifier_id is unknown" % cohort_id)
    if not {2, 6, 12}.issubset(sizes):
        errors.append("review ablation must include 2, 6 and 12 reviewer cohorts")
    twelve_with_verifier = [
        cohort for cohort in cohorts
        if isinstance(cohort, dict)
        and isinstance(cohort.get("review_ids"), list)
        and len(cohort.get("review_ids", [])) == 12
        and cohort.get("verifier_id") is not None
        and cohort.get("verifier_id") not in cohort.get("review_ids", [])
    ]
    if not twelve_with_verifier:
        errors.append("review ablation requires a 12-reviewer cohort plus a distinct verifier")
    return sorted(set(errors))


def _finding_set(reviews: List[Dict[str, Any]]) -> Set[str]:
    return {
        str(finding["issue_id"])
        for review in reviews
        for finding in review.get("findings", [])
        if isinstance(finding, dict) and finding.get("supported") is True and finding.get("issue_id")
    }


def _critical_high_set(reviews: List[Dict[str, Any]]) -> Set[str]:
    return {
        str(finding["issue_id"])
        for review in reviews
        for finding in review.get("findings", [])
        if isinstance(finding, dict) and finding.get("supported") is True and finding.get("severity") in {"CRITICAL", "HIGH"}
    }


def _mean_pairwise_jaccard(reviews: List[Dict[str, Any]]) -> Optional[float]:
    sets = [_finding_set([review]) for review in reviews]
    values: List[float] = []
    for left, right in itertools.combinations(sets, 2):
        union = left | right
        values.append(float(len(left & right)) / float(len(union)) if union else 1.0)
    return sum(values) / len(values) if values else None



def _panel_decision(reviews: List[Dict[str, Any]]) -> str:
    verdicts = [str(review.get("verdict")) for review in reviews]
    if "FAIL" in verdicts:
        return "FAIL"
    if "BLOCKED" in verdicts:
        return "BLOCKED"
    return "PASS"


def _aggregate_resource(reviews: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
    values = [review.get(key) for review in reviews]
    known = sum(float(value) for value in values if value is not None)
    unknown = sum(1 for value in values if value is None)
    return {"total": None if unknown else known, "known_subtotal": known, "unknown_reviews": unknown}


def evaluate_review_ablation(study: Dict[str, Any]) -> Dict[str, Any]:
    errors = validate_review_ablation_study(study)
    if errors:
        return {"ablation_integrity_status": "INVALID", "engineering_panel_recommendation": "NOT_PROVEN", "errors": errors}
    review_map = {str(review["review_id"]): review for review in study["reviews"]}
    reference = set(str(item) for item in study.get("reference_findings", []) if isinstance(item, str) and item)
    cohorts = sorted(study["cohorts"], key=lambda item: (len(item["review_ids"]), str(item["cohort_id"])))
    metrics: Dict[str, Any] = {}
    previous_unique: Set[str] = set()
    previous_high: Set[str] = set()
    for cohort in cohorts:
        reviews = [review_map[str(review_id)] for review_id in cohort["review_ids"]]
        unique = _finding_set(reviews)
        high = _critical_high_set(reviews)
        total_supported = sum(
            1 for review in reviews for finding in review.get("findings", [])
            if isinstance(finding, dict) and finding.get("supported") is True
        )
        unsupported = sum(
            1 for review in reviews for finding in review.get("findings", [])
            if isinstance(finding, dict) and finding.get("supported") is False
        )
        verdicts = {state: sum(1 for review in reviews if review.get("verdict") == state) for state in ("PASS", "FAIL", "BLOCKED")}
        tokens = _aggregate_resource(reviews, "tokens")
        cost = _aggregate_resource(reviews, "monetary_cost")
        latencies = [float(review["latency_ms"]) for review in reviews]
        human = sum(float(review["human_minutes"]) for review in reviews)
        item = {
            "reviewer_count": len(reviews),
            "verifier_included": cohort.get("verifier_id") is not None,
            "unique_supported_findings": len(unique),
            "critical_high_findings": len(high),
            "new_unique_findings_vs_previous": len(unique - previous_unique),
            "new_critical_high_vs_previous": len(high - previous_high),
            "duplicate_supported_findings": max(0, total_supported - len(unique)),
            "unsupported_findings": unsupported,
            "finding_recall": (float(len(unique & reference)) / float(len(reference))) if reference else None,
            "mean_pairwise_finding_jaccard": _mean_pairwise_jaccard(reviews),
            "providers": sorted({str(review["provider"]) for review in reviews}),
            "model_families": sorted({str(review["model_family"]) for review in reviews}),
            "verdicts": verdicts,
            "panel_decision": _panel_decision(reviews),
            "tokens": tokens,
            "monetary_cost": cost,
            "latency_ms": {"p50": _percentile(latencies, 0.50), "p95": _percentile(latencies, 0.95), "total": sum(latencies)},
            "human_minutes": human,
        }
        metrics[str(cohort["cohort_id"])] = item
        previous_unique, previous_high = unique, high

    recommendation = "NOT_PROVEN"
    recommendation_reason = "A real independently attested ablation with complete cost evidence is required."
    if study.get("evidence_class") == "REAL_REVIEW":
        twelve = [item for item in metrics.values() if item["reviewer_count"] == 12]
        if twelve:
            reference_panel = twelve[-1]
            full_unique = max(1, int(reference_panel["unique_supported_findings"]))
            full_high = max(1, int(reference_panel["critical_high_findings"]))
            candidates = []
            for cohort_id, item in metrics.items():
                if item["reviewer_count"] >= 12:
                    continue
                if item["tokens"]["unknown_reviews"] or item["monetary_cost"]["unknown_reviews"]:
                    continue
                unique_coverage = float(item["unique_supported_findings"]) / float(full_unique)
                high_coverage = float(item["critical_high_findings"]) / float(full_high)
                if unique_coverage >= 0.90 and high_coverage >= 0.90 and item["panel_decision"] == reference_panel["panel_decision"]:
                    candidates.append((item["reviewer_count"], cohort_id, unique_coverage, high_coverage))
            if candidates:
                candidates.sort()
                recommendation = str(candidates[0][0])
                recommendation_reason = "Smallest real panel preserving >=90% unique and CRITICAL/HIGH coverage with the same panel decision."
            else:
                recommendation = "12"
                recommendation_reason = "No smaller real panel met the frozen 90% coverage and verdict-stability rule."
    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "ablation_integrity_status": "VALID",
        "evidence_class": study.get("evidence_class"),
        "formal_2x6_requirement_unchanged": True,
        "cohorts": metrics,
        "engineering_panel_recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "errors": [],
    }


def evaluate_review_ablation_file(path: Path, output: Optional[Path] = None) -> Dict[str, Any]:
    try:
        value = load_json(path.resolve())
        result = evaluate_review_ablation(value)
    except Exception as exc:
        result = {
            "ablation_integrity_status": "INVALID",
            "engineering_panel_recommendation": "NOT_PROVEN",
            "errors": ["review ablation input could not be loaded: %s" % exc],
        }
    if output is not None:
        write_json(output.resolve(), result)
    return result
