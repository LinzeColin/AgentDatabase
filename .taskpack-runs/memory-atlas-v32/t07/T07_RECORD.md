# v0.0.0.32 — T07 single canonical gate, Git hook, code flow

Executed 2026-08-04. Authorization: **A1/A2**. Classification: **adapt**.

## Why `adapt` and not `apply`

The taskpack's `scripts/canonical_gate.sh` shells out to
`$taskpack/scripts/validate_taskpack.py` and `$taskpack/scripts/stage0_semantic_reconcile.py`.
The taskpack directory is not part of this repository, so that script cannot run
after delivery — it would fail on a path that only exists on the builder's
machine. The repo-resident `ops/memory-atlas/canonical_gate.sh` invokes the
equivalent gates that already live here, per the DAG's "优先复用最新 main 的等价门".

## One gate, two modes

`ops/memory-atlas/canonical_gate.sh <repo> [quick|full] [output.json]`

| | quick | full |
|---|---|---|
| python syntax | ✓ | ✓ |
| acceptance oracles (16 tests) | ✓ | ✓ |
| privacy + zero-model scan | ✓ | ✓ |
| frontend typecheck | ✓ | ✓ |
| preservation (static) | ✓ | ✓ |
| v31 typescript | ✓ | ✓ |
| backend suite (6 files) | | ✓ |
| frontend build | | ✓ |
| v31 static + incremental | | ✓ |
| CI workflow present | | ✓ |
| **`authoritative`** | **false** | **true** |
| measured wall clock | **1.7 s** | **~12 s** |

Both modes emit `memory_atlas.canonical_gate.v1` with a per-check pass/fail and
the tail of any failure. `quick` writes `"authoritative": false` into its own
report, so a quick report cannot be presented as a release certification even by
accident.

## The hook is deliberately not the authority

`.githooks/pre-push` calls `canonical_gate.sh <repo> quick` and nothing else. A
hook that could certify a release would be a second source of truth running on a
machine nobody audits. It is enabled with `git config core.hooksPath .githooks`
(done in this repository), reversed with `git config --unset core.hooksPath`,
and skipped per-push with `MEMORY_ATLAS_SKIP_GATE=1` or `git push --no-verify`.

CI now runs `canonical_gate.sh . full` as its own step. Nine tests in
`test_memory_atlas_canonical_gate_v32.py` pin the shape: exactly one gate script
exists, the hook's *invocation lines* only ever say `quick`, `full` is a strict
superset of `quick`, an invalid mode exits 64, CI calls `full` and never `quick`.

## No parallel timer

Three timers existed before this slice and three exist after —
`memory-atlas-reconcile` (15 min), `memory-atlas-selfheal` (5 min),
`memory-atlas-action-worker` (60 s). The reconcile timer is already the
"missed-event compensation of at most 15 minutes" the DAG asks for, so nothing
was added. A test asserts the timer list is unchanged and that the reconcile
interval is ≤ 15 minutes.

## Post-promote now checks that the numbers came from this release

`ops/memory-atlas/post-promote-probe.sh` proved the surface was up and failed
closed. It said nothing about whether the page's numbers belong to the release
that was just promoted. `post-promote-live-probe.sh` (adapted from the
taskpack's `implementation/runtime/post_promote_live_probe.sh`) adds:

- API header ↔ API body identity for run, trace, release and deployment
- `Cache-Control: no-store`
- the expected release id and deployment revision
- the privacy contract and the three-visual contract

Two deliberate changes from the shipped version:

1. **No Access service token means `NOT_RUN`, exit 3** — not a pass. The shipped
   version would happily probe unauthenticated and interpret whatever Cloudflare
   returned. Verified: it writes `"state": "NOT_RUN"` and exits 3.
2. `UNVERIFIED` satisfies an expectation only when the caller passed
   `UNVERIFIED`, so an unidentified release can never match a real one.

The existing probe calls it and **exits 6** if it fails, so a promotion whose
live identity does not check out cannot be reported as successful.

Verified against the preview origin, both directions:

- correct expectations → `state: PASS`, exit 0, with run/trace/release/deployment,
  `no-store`, ETag, `freshness_state: FRESH`, `product_state: PASS`
- wrong expected release → exit 2,
  `["unexpected release_id: '20260803T101000Z-scenario' != 'WRONG-RELEASE'"]`

## Incidental fix: the repository's own gate could not run here

The full gate failed on `ops/memory-atlas/automation_lifecycle.py` importing
`tomllib`, which is 3.11+. The Owner's system interpreter is **3.9.6**, so two
tests had been failing locally for the whole of v0.0.0.32 (correctly noted as
environmental, but never fixed). It now falls back to `tomli`, and failing that
to a ~15-line reader for the flat `key = "value"` file it actually parses —
which raises rather than guessing on anything it does not understand. Python
3.12 still resolves the real `tomllib`; a check confirms that.

**The backend suite is now 568 passed, 0 failed** on this machine, where it was
566/2 before.

## Evidence

| File | Result |
|---|---|
| `GATE_QUICK.json` | PASS, 6 checks, `authoritative: false` |
| `GATE_FULL.json` | PASS, 11 checks, `authoritative: true` |
| `live-probe/API_RECEIPT.json` | PASS against the preview origin |
| `LIVE_PROBE_NEGATIVE.json` | FAIL on a wrong expected release id |
