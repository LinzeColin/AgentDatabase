#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The C-layer feedback loop must actually close: writer -> file -> reader.

Why this file exists
--------------------
`record_team_outcome.py` used to *require* `--telemetry`, while both readers
(`route_team_moe.py`, `run_team_pipeline.py`) took it as optional **with no
default anywhere**. No component named a path. Writer and readers therefore
only ever met if a human passed the same path to both, by hand, on every call.

Measured 2026-08-16: **0 outcomes recorded**, every route plan reporting
`strategy_fallback_reason: "telemetry unavailable"`, strategy C never once
selected. That reads as "the calibration layer has not been used yet". It is
worse than that -- the layer was structurally unable to accumulate anything.
Strategy C needs >=60 outcomes; a counter with nowhere to live never reaches 1,
let alone 60.

This test pins the loop end to end, in a throwaway root, so no synthetic
outcome can ever land in the real telemetry file. The route plan it feeds in is
a **fixture**, and it carries every field `append_outcome` actually reads
(members with scores, task_graph.profile.domains, mode, strategy) -- a fixture
missing those would pass while proving nothing.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from registry_core import default_telemetry_path  # noqa: E402
from route_team_moe import load_telemetry  # noqa: E402

ROUTE_FIXTURE = {
    "schema_version": "persona-team.route-plan.v2",
    "status": "ready",
    "mode": "small_team",
    "strategy": "B",
    "members": [
        {"subject_slug": "fixture-expert-a", "base_score": 0.61, "marginal_score": 0.58},
        {"subject_slug": "fixture-expert-b", "base_score": 0.55, "marginal_score": 0.49},
    ],
    "task_graph": {"profile": {"domains": ["software-ai"]}},
}
DELTA_FIXTURE = {
    "dimensions": {"overall_delta": 0.0413},
    "minimum_dimension": 78.0,
    "formal_market_pass": False,
}


def main() -> int:
    bad = []
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "route.json").write_text(json.dumps(ROUTE_FIXTURE), encoding="utf-8")
        (root / "delta.json").write_text(json.dumps(DELTA_FIXTURE), encoding="utf-8")

        expected = default_telemetry_path(root)
        if expected.exists():
            bad.append("telemetry file existed before anything was written")

        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "record_team_outcome.py"),
             "--route-plan", str(root / "route.json"),
             "--delta-score", str(root / "delta.json"),
             "--task-slice", "small-problem-solving",
             "--actual-success", "0.72",
             "--registry-root", str(root)],
            capture_output=True, text=True)
        if out.returncode != 0:
            bad.append("writer failed rc=%d: %s" % (out.returncode, out.stderr.strip()[:200]))
        else:
            said = json.loads(out.stdout)
            # The writer must land on the shared default WITHOUT being told the path.
            if pathlib.Path(said["written"]).resolve() != expected.resolve():
                bad.append("writer wrote to %s, shared default is %s" % (said["written"], expected))
            if said.get("telemetry_path_source") != "default (shared with route_team_moe.py)":
                bad.append("writer did not report using the default path: %r"
                           % said.get("telemetry_path_source"))
            if not expected.is_file():
                bad.append("nothing appeared at the shared default path")

        # ...and the reader must find it there, with no path argument either.
        if expected.is_file():
            tel = load_telemetry(expected)
            if int(tel.get("sample_count", 0)) != 1:
                bad.append("reader saw sample_count=%r, expected 1" % tel.get("sample_count"))
            # 1 outcome is nowhere near the contract, and the reader must say so
            # rather than quietly enabling C.
            if tel.get("eligible_for_c"):
                bad.append("one outcome must not satisfy the C contract (>=60)")
            if ">=60" not in str(tel.get("reason", "")):
                bad.append("reader did not state the C requirement: %r" % tel.get("reason"))

        # ── The READER side needs its own assertion ───────────────────────
        # First draft of this file only pinned the writer. Removing the
        # reader's default resolution left this test green -- one requirement,
        # two consumers, one of them unguarded. The reader now names the file
        # it consulted, so it can be checked without standing up a whole
        # fixture registry.
        real_root = HERE.parent
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "route_team_moe.py"),
             "--registry-root", str(real_root), "--task", "Our CI pipeline is flaky."],
            capture_output=True, text=True)
        if out.returncode != 0:
            bad.append("reader failed rc=%d: %s" % (out.returncode, out.stderr.strip()[:200]))
        else:
            obs = json.loads(out.stdout[out.stdout.find("{"):])["routing_observability"]
            want = default_telemetry_path(real_root)
            if pathlib.Path(obs.get("telemetry_path", "")).resolve() != want.resolve():
                bad.append("reader consulted %s, shared default is %s"
                           % (obs.get("telemetry_path"), want))
            if obs.get("telemetry_path_source") != "default (shared with record_team_outcome.py)":
                bad.append("reader did not report using the default path: %r"
                           % obs.get("telemetry_path_source"))
            # It must also distinguish "file absent" from "file empty" -- a plan
            # that only says "unavailable" cannot tell those apart.
            if "telemetry_file_present" not in obs:
                bad.append("reader did not report whether the file exists")

        # Negative control: a root that was never written to must stay unavailable.
        with tempfile.TemporaryDirectory() as td2:
            tel2 = load_telemetry(default_telemetry_path(pathlib.Path(td2)))
            if tel2.get("eligible_for_c") is not False:
                bad.append("an empty root must report eligible_for_c=False")

    for b in bad:
        print("  x " + b)
    print("telemetry round-trip %s" % ("FAIL" if bad else "OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
