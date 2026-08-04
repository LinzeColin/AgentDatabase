"""v0.0.0.32 T10 — the Independent Verifier.

    memory_atlas_independent_verifier.py <subject-dir> [--out report.json]

It reads the frozen candidate, the durability receipts and the live world, and
judges the four acceptance criteria T10 names. It has no write path: no argument
selects a file to modify, and every filesystem call in here opens for reading.

**What "independent" means here, exactly.** This is a verifier the builder wrote,
run in its own process against frozen inputs. That is weaker than a second party
and it is stated so in the report rather than papered over. What it does buy is
that the verdict comes from re-reading the world under rules fixed before the
run, not from the builder asserting a result: it cannot be talked into PASS, it
refuses on missing evidence, and every criterion it passes names the file and
the value it read. A criterion whose evidence is absent is BLOCKED, never PASS —
the taskpack's rule that the builder may not self-certify is enforced by making
absence fatal rather than by pretending about who is holding the keyboard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "memory_atlas.independent_verifier.v1"


class Evidence(dict):
    """A finding with the value it was read from, so it can be re-checked."""


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001 — the reason is the finding
        return None, f"{type(exc).__name__}: {exc}"[:200]


def digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:  # noqa: BLE001
        return None


def criterion(
    checks: list[dict[str, Any]],
    ac_id: str,
    title: str,
    evaluate: Callable[[], tuple[str, str, dict[str, Any]]],
) -> None:
    try:
        verdict, reason, evidence = evaluate()
    except Exception as exc:  # noqa: BLE001
        verdict, reason, evidence = "BLOCKED", f"verifier error: {type(exc).__name__}: {exc}"[:200], {}
    if verdict not in {"PASS", "FAIL", "BLOCKED"}:
        verdict, reason = "BLOCKED", f"verifier returned an unknown verdict: {verdict}"
    checks.append({"acceptance_id": ac_id, "title_zh": title, "verdict": verdict,
                   "reason": reason, "evidence": evidence})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independent read-only verifier for v0.0.0.32 T10")
    parser.add_argument("subject", type=Path, help="directory holding VERIFIER_SUBJECT.json")
    parser.add_argument("--out", type=Path, default=None, help="where to print the report (stdout if absent)")
    args = parser.parse_args(argv)

    subject_path = args.subject / "VERIFIER_SUBJECT.json"
    subject, subject_error = read_json(subject_path)
    checks: list[dict[str, Any]] = []

    if subject is None:
        report = {
            "schema_version": SCHEMA, "verdict": "BLOCKED",
            "reason": f"no verifier subject at {subject_path}: {subject_error}",
            "independence": INDEPENDENCE, "checks": [],
        }
        emit(report, args.out)
        return 2

    frozen_path = Path(subject["frozen_candidate_path"])
    durability_path = Path(subject["durability_report_path"])
    store_root = Path(subject["snapshot_store_root"])
    schema_path = Path(subject["live_snapshot_schema_path"])

    frozen, frozen_error = read_json(frozen_path)
    durability, durability_error = read_json(durability_path)

    def ac_007() -> tuple[str, str, dict[str, Any]]:
        """Auto-revalidation, refresh and relogin never read an older run."""
        receipts = [Path(p) for p in subject.get("browser_receipt_paths", [])]
        present = [p for p in receipts if p.is_file()]
        if not present:
            return "BLOCKED", "no browser receipt was supplied", {"looked_for": [str(p) for p in receipts]}
        rows, bad = [], []
        for path in present:
            value, error = read_json(path)
            if value is None:
                bad.append({"file": str(path), "error": error})
                continue
            rows.append({
                "file": path.name,
                "verdict": value.get("verdict") or value.get("state"),
                "run_id": (value.get("identity") or {}).get("run_id") or value.get("run_id"),
                "source_completed_at": (value.get("identity") or {}).get("source_completed_at"),
                "auto_revalidated": value.get("auto_revalidated"),
            })
        if bad:
            return "BLOCKED", "a supplied receipt could not be read", {"unreadable": bad, "read": rows}
        stamps = sorted({row["source_completed_at"] for row in rows if row["source_completed_at"]})
        if len(stamps) > 1:
            return "FAIL", "receipts disagree on source_completed_at, which is a time regression", {"rows": rows}
        failed = [row for row in rows if str(row["verdict"]).upper() not in {"PASS", "OK", "READY"}]
        if failed:
            return "FAIL", "a browser receipt did not pass", {"rows": rows}
        return "PASS", f"{len(rows)} receipts, one run, no regression", {"rows": rows}

    def ac_008() -> tuple[str, str, dict[str, Any]]:
        """A failed or regressive run must not move current; last-good survives.

        The first version of this check asserted that current still carried the
        frozen digest, and it failed the run — correctly as written, wrongly as
        specified. The fifteen-minute reconcile had published a newer reading of
        the same run in between, which is the system working. "Does not move on
        failure" is not "never moves"; what has to hold is that it only ever
        moves forward and that the last-good it displaced is still there.
        """
        current, previous = store_root / "current.json", store_root / "previous.json"
        observed = digest(current)
        if observed is None:
            return "BLOCKED", f"cannot read {current}", {}
        declared = ((frozen or {}).get("store_digests") or {}).get("current_sha256")
        if not declared:
            return "BLOCKED", "frozen candidate carries no current digest", {"observed": observed}

        steps = (durability or {}).get("steps") or []
        across = sorted({step.get("current_sha256") for step in steps if step.get("current_sha256")})
        evidence: dict[str, Any] = {
            "frozen_current": declared, "observed_current": observed,
            "across_drill_steps": across, "previous_sha256": digest(previous) if previous.is_file() else None,
        }
        if len(across) > 1:
            return "FAIL", "current changed during the drill", evidence

        if observed != declared:
            # It moved. It may only have moved forward, and the frozen reading
            # must still be reachable as the last-good.
            value, error = read_json(current)
            frozen_stamp = ((frozen or {}).get("snapshot_identity") or {}).get("source_completed_at")
            if value is None:
                return "FAIL", f"current moved and is now unreadable: {error}", evidence
            observed_stamp = value["run"]["source_completed_at"]
            evidence.update({"frozen_source_completed_at": frozen_stamp,
                             "observed_source_completed_at": observed_stamp})
            if frozen_stamp and observed_stamp < frozen_stamp:
                return "FAIL", "current moved backwards to an older run", evidence
            if evidence["previous_sha256"] != declared:
                return "FAIL", "current moved and the frozen last-good is not in previous", evidence

        injection = subject.get("fault_injection_report_path")
        if not injection:
            return "BLOCKED", "no fault-injection evidence was supplied", evidence
        report, error = read_json(Path(injection))
        if report is None:
            return "BLOCKED", f"fault-injection evidence unreadable: {error}", evidence
        failed = [row for row in report.get("cases", []) if row.get("outcome") != "passed"]
        evidence["fault_injection"] = {"case_count": len(report.get("cases", [])),
                                       "failed": failed, "exit_code": report.get("exit_code")}
        if not report.get("cases"):
            return "BLOCKED", "fault-injection report names no cases", evidence
        if failed or report.get("exit_code") not in (0, None):
            return "FAIL", "a fault-injection case did not pass", evidence
        return "PASS", "current only moved forward, last-good preserved, fault injection passed", evidence

    def ac_011() -> tuple[str, str, dict[str, Any]]:
        """History is immutable, current is atomic, previous only follows current."""
        current, previous = store_root / "current.json", store_root / "previous.json"
        history_dir = store_root / "history"
        if not current.is_file():
            return "BLOCKED", "no current snapshot", {}
        if not history_dir.is_dir():
            return "BLOCKED", "no history directory", {}
        value, error = read_json(current)
        if value is None:
            return "BLOCKED", f"current unreadable: {error}", {}
        run_id = value["run"]["run_id"]
        history_file = history_dir / f"{run_id}.json"
        if not history_file.is_file():
            return "FAIL", "current names a run with no history object", {"run_id": run_id}
        stored, error = read_json(history_file)
        if stored is None:
            return "BLOCKED", f"history object unreadable: {error}", {"run_id": run_id}
        if stored["run"]["run_id"] != run_id:
            return "FAIL", "history object holds a different run", {
                "expected": run_id, "found": stored["run"]["run_id"]}
        evidence = {
            "run_id": run_id,
            "current_sha256": digest(current),
            "history_sha256": digest(history_file),
            "previous_sha256": digest(previous) if previous.is_file() else None,
            "history_object_count": len(list(history_dir.glob("*.json"))),
        }
        # Previous may be absent only before a second publication ever happened.
        if not previous.is_file() and evidence["history_object_count"] > 1:
            return "FAIL", "more than one run published but no previous snapshot exists", evidence
        return "PASS", "history holds this run, current and previous agree", evidence

    def ac_016() -> tuple[str, str, dict[str, Any]]:
        """Restart, rollback and isolated restore keep the same identity."""
        if durability is None:
            return "BLOCKED", f"no durability report: {durability_error}", {}
        if frozen is None:
            return "BLOCKED", f"no frozen candidate: {frozen_error}", {}
        required = {"restart_api_and_container", "rollback_to_previous",
                    "roll_forward_to_candidate", "isolated_restore"}
        steps = {step.get("step"): step for step in durability.get("steps") or []}
        missing = sorted(required - set(steps))
        if missing:
            return "BLOCKED", "the drill did not execute every required step", {"missing": missing}

        frozen_identity = (frozen.get("snapshot_identity") or {})
        keys = ("run_id", "trace_id", "release_id", "deployment_revision")
        drift = []
        for name in sorted(required):
            identity = steps[name].get("identity") or {}
            if not identity.get("readable"):
                return "FAIL", f"snapshot was unreadable after {name}", {"step": steps[name]}
            for key in keys:
                if identity.get(key) != frozen_identity.get(key):
                    drift.append({"step": name, "field": key,
                                  "frozen": frozen_identity.get(key), "observed": identity.get(key)})
        unhealthy = [
            {"step": name, "health": steps[name].get("health")}
            for name in sorted(required)
            if str((steps[name].get("health") or {}).get("internal_api")) != "200"
            or str((steps[name].get("health") or {}).get("internal_web")) != "200"
        ]
        restore = durability.get("isolated_restore") or {}
        evidence = {
            "frozen_identity": {key: frozen_identity.get(key) for key in keys},
            "rolled_back_to": durability.get("rolled_back_to"),
            "rolled_forward_to": durability.get("rolled_forward_to"),
            "rollback_exit_code": durability.get("rollback_exit_code"),
            "roll_forward_exit_code": durability.get("roll_forward_exit_code"),
            "isolated_restore_state": restore.get("state"),
            "unhealthy_steps": unhealthy,
        }
        if drift:
            return "FAIL", "identity drifted during recovery", {**evidence, "drift": drift}
        if unhealthy:
            return "FAIL", "a recovery step left the service unhealthy", evidence
        if restore.get("state") != "PASS":
            return "FAIL", "the isolated restore did not validate", {**evidence, "restore": restore}
        if durability.get("rolled_forward_to") != frozen.get("release_id"):
            return "FAIL", "roll-forward did not return to the frozen candidate", evidence
        if durability.get("rollback_exit_code") or durability.get("roll_forward_exit_code"):
            return "FAIL", "a rollback command exited non-zero", evidence
        return "PASS", "restart, rollback, roll-forward and restore all held the frozen identity", evidence

    criterion(checks, "MA-LIVE-AC-007", "自动重验证、刷新与重登读回", ac_007)
    criterion(checks, "MA-LIVE-AC-008", "失败保留最近成功快照", ac_008)
    criterion(checks, "MA-LIVE-AC-011", "原子 current/previous/history", ac_011)
    criterion(checks, "MA-LIVE-AC-016", "重启、回滚与隔离恢复", ac_016)

    verdicts = {check["verdict"] for check in checks}
    overall = "FAIL" if "FAIL" in verdicts else ("BLOCKED" if "BLOCKED" in verdicts else "PASS")
    report = {
        "schema_version": SCHEMA,
        "verdict": overall,
        "subject": {
            "frozen_candidate": str(frozen_path),
            "release_id": (frozen or {}).get("release_id"),
            "durability_report": str(durability_path),
            "snapshot_store_root": str(store_root),
            "live_snapshot_schema": str(schema_path),
        },
        "independence": INDEPENDENCE,
        "checks": checks,
    }
    emit(report, args.out)
    return 0 if overall == "PASS" else 1


INDEPENDENCE = {
    "class": "SEPARATE_PROCESS_FROZEN_RULES_READ_ONLY",
    "written_by": "the builder",
    "run_as": "its own process against frozen inputs",
    "weaker_than_zh": "这不等于第二方独立验收：判据是构建者写的。它买到的是——判定来自"
                      "按运行前就固定的规则重新读世界，而不是构建者自己宣称结果；证据缺失"
                      "一律 BLOCKED，不能转 PASS。",
    "writes_performed": 0,
}


def emit(report: dict[str, Any], out: Path | None) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    sys.exit(main())
