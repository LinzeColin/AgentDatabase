#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`restricted` means measured-only. A penalty ranks; it does not forbid.

Why this file exists
--------------------
`persona-producer-consumer-contract.md` states three admission levels:

    `eligible`  ：可在声明能力和边界内使用。
    `restricted`：只允许命中已测量切片；不得外推为一般能力。
    `blocked`   ：...不得路由。

`blocked` was enforced as a hard exclusion. `restricted` was not enforced at
all -- the only thing between a restricted persona and an arbitrary task was
`restriction_penalty = 0.08`, a score adjustment.

Measured 2026-08-17 on the real roster: George Washington Carver
(`admission: restricted`, `routing_scope: "measured-only"`) was seated on a
**poetry-anthology typography** team with `domain_match = 0.0000`. Both
penalties fired (0.08 admission + 0.16 measured-scope prose marker) and he was
selected anyway. **Penalties rank; they do not forbid.**

Worse, the admission ledger already carried the answer in a structured field --
`routing_scope: "measured-only"` -- and the router never read it. The rule was
written in the contract, recorded in the data, and enforced nowhere.

Effect on the benchmarks: measured A/B, **exactly zero** on both the 24-task
routing set and the 72-task oracle set -- only 1 of 102 personas is currently
`restricted`. The evidence for this fix is the probe below, not the benchmark,
and the rule's value is that it holds for every future restricted persona.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"

OUT_OF_SCOPE = "Design the typography for a poetry anthology."
IN_SCOPE = "Plan crop rotation and soil restoration for depleted farmland."


def route(task):
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "route_team_moe.py"), "--task", task,
         "--registry-root", str(ROOT), "--mode", "deep_team", "--size", "20"],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit("router failed rc=%d: %s" % (out.returncode, out.stderr.strip()[:300]))
    return json.loads(out.stdout[out.stdout.find("{"):])


def restricted_slugs():
    d = json.loads((ROOT / "expert-fleet-admission.json").read_text(encoding="utf-8"))
    rows = d if isinstance(d, list) else (d.get("experts") or list(d.values()))
    return [r["subject_slug"] for r in rows
            if isinstance(r, dict) and r.get("admission") == "restricted"
            and r.get("routing_scope") == "measured-only"]


def main() -> int:
    bad = []
    who = restricted_slugs()
    if not who:
        # Not a pass. A rule with nothing to apply to proves nothing.
        print("  x 名册里没有 admission=restricted + routing_scope=measured-only 的人物 —— "
              "**这条测试当前扫不到任何对象，不算通过**")
        print("restricted-is-measured-only NO-SUBJECT")
        return 1

    plan = route(OUT_OF_SCOPE)
    seated = {m.get("subject_slug") for m in plan["members"]}
    excluded = {e.get("subject_slug"): e.get("reason", "") for e in plan.get("excluded_candidates", [])}
    for slug in who:
        if slug in seated:
            bad.append("%s is restricted/measured-only but was seated on an out-of-scope task" % slug)
        elif slug not in excluded:
            bad.append("%s was neither seated nor listed in excluded_candidates -- "
                       "silence is not a decision" % slug)
        elif "measured scope" not in excluded[slug]:
            bad.append("%s was excluded without naming the reason: %r" % (slug, excluded[slug]))

    # The other direction: the rule must not become a permanent ban.
    plan2 = route(IN_SCOPE)
    seated2 = {m.get("subject_slug") for m in plan2["members"]}
    ex2 = {e.get("subject_slug"): e.get("reason", "") for e in plan2.get("excluded_candidates", [])}
    for slug in who:
        if "measured scope" in ex2.get(slug, ""):
            bad.append("%s was excluded as out-of-scope on a task inside its own field -- "
                       "the rule became a ban" % slug)

    for b in bad:
        print("  x " + b)
    print("restricted-is-measured-only %s（对象 %d 人：%s）"
          % ("FAIL" if bad else "OK", len(who), "、".join(who)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
