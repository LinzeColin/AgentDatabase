#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disclosures must survive all the way to the artifact the host executes.

Why this file exists
--------------------
Three disclosures were added to this skill on 2026-08-17 -- no-domain-signal,
telemetry location, divergence detectability -- and each was verified on the
script that produces it. All three then failed to appear in
`execution-contract.json`, which is the file the host agent actually runs
against. Verified single commands; never verified the chain.

That gap was not cosmetic. `user_output_contract.show` already instructs the
host to surface "material disagreements". Handed `documented_divergences: []`
with no denominator beside it, the honest thing for the host to write is "the
experts agreed" -- asserting something that was never measured. The pseudo-
consensus the Owner flagged was being manufactured at that exact line.

So this test runs the **real user entry point** (`run_team_pipeline.py`) end to
end and asserts on the *final* artifacts, not on intermediate ones. It checks
both directions: a task with a domain signal must NOT carry a caveat, and a
task without one must.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"

# A task whose vocabulary the roster covers, and one it does not.
WITH_SIGNAL = "Our CI pipeline is flaky and the API keeps timing out."
WITHOUT_SIGNAL = "Plan the choreography and lighting cues for the ballet."

# (artifact, dotted path) that must exist on every run.
REQUIRED = [
    ("route-plan.json", "routing_observability.domain_signal_present"),
    ("route-plan.json", "routing_observability.ranking_driver"),
    ("route-plan.json", "routing_observability.telemetry_path"),
    ("route-plan.json", "routing_observability.telemetry_file_present"),
    ("team-dossier.json", "divergence_detectability.members_carrying_divergence_map"),
    ("team-dossier.json", "divergence_detectability.note"),
    # The three below are the ones that were missing: same facts, but in the
    # file the host executes.
    ("execution-contract.json", "divergence_detectability.note"),
    ("execution-contract.json", "selection_caveats"),
    ("execution-contract.json", "user_output_contract.phrasing_rules"),
]


def dig(doc, dotted):
    cur = doc
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None, False
        cur = cur[key]
    return cur, True


def run_pipeline(task, workdir):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "run_team_pipeline.py"),
         "--task", task, "--registry-root", str(ROOT), "--workdir", str(workdir)],
        capture_output=True, text=True)


def main() -> int:
    bad = []
    with tempfile.TemporaryDirectory() as td:
        wd = pathlib.Path(td) / "with"
        wd.mkdir()
        out = run_pipeline(WITH_SIGNAL, wd)
        if out.returncode != 0:
            bad.append("pipeline failed rc=%d: %s" % (out.returncode, out.stderr.strip()[:300]))
        else:
            docs = {}
            for name in ("route-plan.json", "team-dossier.json", "execution-contract.json"):
                f = wd / name
                if not f.is_file():
                    bad.append("%s was not produced" % name)
                else:
                    docs[name] = json.loads(f.read_text(encoding="utf-8"))
            for name, dotted in REQUIRED:
                if name not in docs:
                    continue
                _, ok = dig(docs[name], dotted)
                if not ok:
                    bad.append("%s is missing %s" % (name, dotted))
            # A task the roster covers must not claim it was picked blind.
            contract = docs.get("execution-contract.json", {})
            if contract.get("selection_caveats"):
                bad.append("a task WITH a domain signal must have no selection caveat, got %r"
                           % contract["selection_caveats"])

        # ── The other direction. A caveat that never fires is not a caveat. ──
        wd2 = pathlib.Path(td) / "without"
        wd2.mkdir()
        out2 = run_pipeline(WITHOUT_SIGNAL, wd2)
        if out2.returncode != 0:
            bad.append("pipeline failed on the no-signal task rc=%d: %s"
                       % (out2.returncode, out2.stderr.strip()[:300]))
        else:
            contract2 = json.loads((wd2 / "execution-contract.json").read_text(encoding="utf-8"))
            caveats = contract2.get("selection_caveats") or []
            if not caveats:
                bad.append("a task with NO domain signal must carry a selection caveat "
                           "into the execution contract, got []")
            elif not any("NO DOMAIN SIGNAL" in c for c in caveats):
                bad.append("caveat did not name the condition: %r" % caveats)

    for b in bad:
        print("  x " + b)
    print("disclosures-reach-the-contract %s" % ("FAIL" if bad else "OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
