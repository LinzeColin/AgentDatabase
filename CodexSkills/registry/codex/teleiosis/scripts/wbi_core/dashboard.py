from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .io import sha256_file


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _list_html(values: Iterable[str], empty: str = "None recorded") -> str:
    items = list(values)
    if not items:
        return '<p class="muted">%s</p>' % escape(empty)
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % escape(item) for item in items)


def _status_class(value: str) -> str:
    token = value.upper()
    if any(item in token for item in ("PASS", "READY", "INSTALLABLE", "KEEP_CANDIDATE")):
        return "ok"
    if any(item in token for item in ("BLOCK", "FAIL", "REVERT")):
        return "bad"
    return "warn"


def render_dashboard(data: Dict[str, Any], output: Path) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("dashboard data must be an object")
    title = str(data.get("title") or "Teleiosis Control Console")
    subtitle = str(data.get("subtitle") or "White-box iteration evidence, decisions and blockers")
    version = str(data.get("version") or "UNKNOWN")
    status_domains = data.get("status_domains") if isinstance(data.get("status_domains"), dict) else {}
    improvements = _items(data.get("improvements"))
    blockers = _items(data.get("blockers"))
    next_actions = _items(data.get("next_actions"))
    metrics = data.get("metrics") if isinstance(data.get("metrics"), list) else []

    cards = []
    for key, value in status_domains.items():
        status = str(value)
        cards.append(
            '<section class="card"><div class="eyebrow">%s</div><div class="status %s">%s</div></section>'
            % (escape(str(key).replace("_", " ").title()), _status_class(status), escape(status))
        )
    metric_rows = []
    for metric in metrics:
        if isinstance(metric, dict):
            metric_rows.append(
                "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (escape(str(metric.get("name", ""))), escape(str(metric.get("value", ""))), escape(str(metric.get("evidence", ""))))
            )

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--bg:#06131f;--panel:#0a2234;--panel2:#0d2c43;--line:#1a5874;--text:#e9f8ff;--muted:#9cc7d8;--cyan:#41d9ff;--blue:#4a8dff;--ok:#55e6bd;--warn:#ffd27a;--bad:#ff8d9e}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 10% 0%,#0d3550 0,#06131f 42%);color:var(--text);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{max-width:1180px;margin:auto;padding:44px 24px 72px}}header{{border:1px solid var(--line);background:linear-gradient(135deg,rgba(65,217,255,.11),rgba(74,141,255,.08));padding:30px;border-radius:20px;box-shadow:0 22px 70px rgba(0,0,0,.28)}}
h1{{font-size:clamp(31px,5vw,58px);line-height:1.05;margin:6px 0 12px;letter-spacing:-.04em}}.kicker,.eyebrow{{color:var(--cyan);font-size:12px;font-weight:800;letter-spacing:.13em;text-transform:uppercase}}.sub{{color:var(--muted);max-width:780px;font-size:17px}}.version{{display:inline-block;margin-top:16px;padding:6px 10px;border:1px solid var(--line);border-radius:999px;color:var(--cyan)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:20px 0}}.card,.section{{border:1px solid var(--line);background:linear-gradient(160deg,var(--panel2),var(--panel));border-radius:16px;padding:19px}}.status{{font-size:20px;font-weight:800;margin-top:8px;overflow-wrap:anywhere}}.ok{{color:var(--ok)}}.warn{{color:var(--warn)}}.bad{{color:var(--bad)}}
.columns{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:16px;margin-top:16px}}h2{{font-size:20px;margin:0 0 12px}}ul{{padding-left:20px;margin:8px 0}}li{{margin:7px 0}}.muted{{color:var(--muted)}}table{{width:100%;border-collapse:collapse}}th,td{{padding:11px 9px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--cyan);font-size:12px;text-transform:uppercase;letter-spacing:.08em}}footer{{color:var(--muted);margin-top:22px;font-size:13px}}code{{color:var(--cyan)}}
</style></head><body><main>
<header><div class="kicker">White-box assurance and evolution</div><h1>{title}</h1><div class="sub">{subtitle}</div><div class="version">{version}</div></header>
<div class="grid">{cards}</div>
<div class="columns"><section class="section"><h2>Material improvements</h2>{improvements}</section><section class="section"><h2>Unresolved blockers</h2>{blockers}</section><section class="section"><h2>Next accountable actions</h2>{actions}</section></div>
<section class="section" style="margin-top:16px"><h2>Evidence metrics</h2><table><thead><tr><th>Metric</th><th>Value</th><th>Evidence</th></tr></thead><tbody>{metrics}</tbody></table></section>
<footer>Static, dependency-free console. Rendering does not change evidence or grant promotion.</footer>
</main></body></html>""".format(
        title=escape(title), subtitle=escape(subtitle), version=escape(version), cards="".join(cards),
        improvements=_list_html(improvements), blockers=_list_html(blockers), actions=_list_html(next_actions),
        metrics="".join(metric_rows) or '<tr><td colspan="3" class="muted">No metrics recorded</td></tr>',
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    # pathlib.Path.write_text did not accept ``newline`` until Python 3.10.
    # The skill supports Python 3.9, so use an explicit text handle while
    # retaining deterministic LF output on every supported platform.
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(html)
    return {"status": "PASS", "output": str(output.resolve()), "bytes": output.stat().st_size, "sha256": sha256_file(output), "external_dependencies": 0}


def render_dashboard_file(input_path: Path, output: Path) -> Dict[str, Any]:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    result = render_dashboard(data, output)
    result["input_sha256"] = sha256_file(input_path)
    return result
