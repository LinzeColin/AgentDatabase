from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import load_json, sha256_file, utc_now, write_json

_STATUS_ORDER = [
    "control_plane", "benchmark_integrity", "outcome", "cost_evidence",
    "independent_review", "engineering_release", "formal_promotion",
    "current_environment_strength",
]


def _safe(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _status_rows(summary: Dict[str, Any]) -> List[Dict[str, str]]:
    domains = summary.get("domains", summary)
    rows: List[Dict[str, str]] = []
    if isinstance(domains, dict):
        keys = _STATUS_ORDER + sorted(key for key in domains if key not in _STATUS_ORDER)
        seen = set()
        for key in keys:
            if key in seen or key not in domains:
                continue
            seen.add(key)
            value = domains[key]
            if isinstance(value, dict):
                state = value.get("status", value.get("state", "UNKNOWN"))
                evidence = value.get("evidence", value.get("reason", ""))
            else:
                state, evidence = value, ""
            rows.append({"domain": key, "status": str(state), "evidence": str(evidence)})
    return rows


def _domain_state(domains: Any, key: str) -> str:
    if not isinstance(domains, dict):
        return "UNKNOWN"
    value = domains.get(key, "UNKNOWN")
    if isinstance(value, dict):
        value = value.get("status", value.get("state", "UNKNOWN"))
    return str(value)


def _leadership_label(summary: Dict[str, Any], comparison: Optional[Dict[str, Any]]) -> Dict[str, str]:
    domains = summary.get("domains", summary)
    outcome = _domain_state(domains, "outcome")
    independent = _domain_state(domains, "independent_review")
    formal = _domain_state(domains, "formal_promotion")
    if comparison and comparison.get("evidence_status") == "PROVEN" and comparison.get("winner") and formal in {"PASS", "PROMOTABLE"}:
        return {"label": "EVIDENCE-BOUNDED LEADER", "detail": "A frozen comparison supports the stated scope; it is not a permanent universal claim."}
    if "PROVEN" in outcome and "UNAVAILABLE" not in independent and formal in {"PASS", "PROMOTABLE"}:
        return {"label": "FORMALLY PROMOTABLE", "detail": "Outcome and independent review evidence are present for the frozen scope."}
    return {"label": "ENGINEERING CANDIDATE - MARKET LEADERSHIP NOT PROVEN", "detail": "Control-plane quality, tests or packaging cannot substitute for real equal-budget outcome evidence."}


def generate_showcase(
    status_path: Path,
    output: Path,
    *,
    comparison_path: Optional[Path] = None,
    title: str = "Teleiosis Evidence Card",
) -> Dict[str, Any]:
    status_path = status_path.resolve()
    output = output.resolve()
    if not status_path.is_file() or status_path.is_symlink():
        raise ValueError("status file must be a regular JSON file")
    summary = load_json(status_path)
    if not isinstance(summary, dict):
        raise ValueError("status summary must be an object")
    comparison = None
    if comparison_path is not None:
        comparison_path = comparison_path.resolve()
        if not comparison_path.is_file() or comparison_path.is_symlink():
            raise ValueError("comparison file must be a regular JSON file")
        comparison = load_json(comparison_path)
        if not isinstance(comparison, dict):
            raise ValueError("comparison must be an object")
    rows = _status_rows(summary)
    leadership = _leadership_label(summary, comparison)

    table_rows = "".join(
        "<tr><td>%s</td><td><span class=\"state\">%s</span></td><td>%s</td></tr>" %
        (_safe(row["domain"]), _safe(row["status"]), _safe(row["evidence"]))
        for row in rows
    ) or '<tr><td colspan="3">No domain status supplied. Evidence remains UNKNOWN.</td></tr>'

    comparison_html = ""
    if comparison is not None:
        evidence_status = str(comparison.get("evidence_status", "UNKNOWN"))
        scope = str(comparison.get("claim_scope", "UNSPECIFIED"))
        winner = str(comparison.get("winner", "NONE")) if evidence_status == "PROVEN" else "WITHHELD"
        comparison_html = (
            '<section><h2>Frozen comparison</h2><div class="grid">'
            '<div class="card"><b>Evidence status</b><span>%s</span></div>'
            '<div class="card"><b>Claim scope</b><span>%s</span></div>'
            '<div class="card"><b>Winner</b><span>%s</span></div>'
            '</div></section>' % (_safe(evidence_status), _safe(scope), _safe(winner))
        )

    document = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--ink:#111827;--muted:#64748b;--line:#dbe3ee;--panel:#f8fafc;--accent:#0f172a}}
*{{box-sizing:border-box}}body{{margin:0;background:#eef2f7;color:var(--ink);font:15px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1080px;margin:36px auto;padding:0 20px}}header,section{{background:white;border:1px solid var(--line);border-radius:18px;padding:24px;margin-bottom:18px;box-shadow:0 8px 24px rgba(15,23,42,.05)}}
h1{{margin:0 0 4px;font-size:34px}}h2{{margin:0 0 16px;font-size:20px}}.muted{{color:var(--muted)}}.banner{{margin-top:18px;padding:16px;border-radius:12px;background:var(--accent);color:white}}
.banner b{{display:block;font-size:16px;margin-bottom:4px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
.state{{display:inline-block;padding:3px 8px;border:1px solid var(--line);border-radius:999px;background:var(--panel);font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.card{{padding:16px;background:var(--panel);border:1px solid var(--line);border-radius:12px}}.card b,.card span{{display:block}}.card span{{margin-top:6px}}footer{{padding:8px 4px 32px;color:var(--muted);font-size:12px}}@media(max-width:720px){{.grid{{grid-template-columns:1fr}}h1{{font-size:28px}}}}
</style></head><body><main>
<header><h1>{title}</h1><div class="muted">Generated {generated}</div><div class="banner"><b>{label}</b>{detail}</div></header>
<section><h2>Evidence-domain state</h2><table><thead><tr><th>Domain</th><th>Status</th><th>Evidence / reason</th></tr></thead><tbody>{rows}</tbody></table></section>
{comparison}
<section><h2>Non-negotiable fallback</h2><p>When a candidate regresses a mandatory metric, fails a hard gate, or produces incomplete evidence, retain the frozen baseline. UNKNOWN and NOT_RUN are never rendered as PASS.</p></section>
<footer>Self-contained, no external scripts, and generated from the supplied evidence files. This card is not an independent attestation.</footer>
</main></body></html>""".format(
        title=_safe(title), generated=_safe(utc_now()), label=_safe(leadership["label"]), detail=_safe(leadership["detail"]),
        rows=table_rows, comparison=comparison_html,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8", newline="\n")
    result = {
        "status": "PASS",
        "output": str(output),
        "sha256": sha256_file(output),
        "bytes": output.stat().st_size,
        "leadership_label": leadership["label"],
        "generated_at": utc_now(),
        "claim_boundary": "The HTML card derives labels from supplied evidence and is not an independent review.",
    }
    receipt = output.with_suffix(output.suffix + ".receipt.json")
    receipt_payload = dict(result)
    # Persist a relocatable path: the receipt is adjacent to the generated card.
    # The CLI return value remains absolute for immediate operator use.
    receipt_payload["output"] = output.name
    receipt_payload["path_base"] = "receipt_parent"
    write_json(receipt, receipt_payload)
    result["receipt"] = str(receipt)
    return result
