# v0.0.0.32 — T06 source tiers, degraded paths, privacy report

Executed 2026-08-04. Authorization: **A1/A2**. Classification: **adapt** — the
adapter already separated Tier A from Tier B, but the tiering was hard-coded, so
it was moved into the registry as data.

## Correction: T03 never actually published anything

Wiring the publisher into `pipeline.py` was not the same as running it. Fixing
T06 required first proving the publish path works, and it did not. Five separate
reasons, each fatal on its own, all swallowed into `_live_snapshot_error`:

| Defect | What the adapter did |
|---|---|
| `run` block carried no `trace_id` | `run_id and trace_id are required` |
| `run` block carried no `source_completed_at` | `source_completed_at is required` |
| called from `_write_web_snapshots`, state still `REFRESHING_ATLAS` | `non-terminal source state refused` |
| `cloud_native_sources: []` | `cloud_native_sources must be non-empty` |
| evidence rows carried `verified: bool`, not `state` | `required authority evidence not PASS` |

On top of that the **reconcile path never called it at all** — and the reconcile
host is the one the browser actually reads from. So the live snapshot could not
have appeared in production under any circumstance.

`OpenAIDatabase/tests/test_memory_atlas_live_snapshot_publish_v32.py` (13 tests)
now drives the adapter with pipeline-shaped inputs and validates the result
against the frozen schema, so this cannot regress silently.

## What changed

- `_publish_live_snapshot` moved into `LiveSnapshotPublisherMixin`, shared by
  `CapturePipeline` and `RemoteReconcilePipeline` — **one adapter, one store,
  two callers**, which is what T03 asked for.
- The caller supplies the evidence, because only the caller knows what it read.
  The capture host passes `ovh_reconcile=None` → `NOT_RUN` → the adapter
  declines. That is not a bug: publishing there would claim an authority the
  Mac never touched. The reconcile host verified all four and publishes.
- `same_run_evidence_rows` makes "never ran" impossible to confuse with "passed":
  `None → NOT_RUN`, `False → FAIL`, `True → PASS`.
- `_release_identity()` reads the release identity from the environment and
  reports `UNVERIFIED` when it is blank, never a fabricated value.
- `cloud_native_authorities()` derives every Tier A state from something the run
  actually read: object read-back results, the normalized delta receipt, the
  Private-Database paths, the GitHub release manifest.

## Tiering is now data, not an assumption

`ops/memory-atlas/source-registry.json` gained `availability_tier` and
`required_for_product` on all ten local sources (all
`B_LOCAL_OPTIONAL` / `false`) plus a new `cloud_native_authorities` block:

| Authority | required_for_product |
|---|---|
| R2 主对象字节 | **true** |
| R2 归一化事件流 | **true** |
| Private-Database 结构化事实 | **true** |
| GitHub 私有仓全量备份 | **false** |

The adapter used to hard-code `required_for_product: True` for every Tier A row.
It now reads the flag, and availability is decided by `required_for_product`
rather than by which tier a row sits in. That distinction is what lets the
GitHub full-history backup be a real, named gap without falsely reporting the
product as FAILED.

The degraded reason also names the source now, instead of a generic sentence:
`至少一个产品必需的云端权威不可用：R2 主对象字节、R2 归一化事件流；系统不能宣称最新。`

## Degraded-path receipts — `DEGRADED_PATH_RECEIPTS.json`, **PASS 8/8**

Every scenario is built by the **real adapter** (`build_degraded_scenarios.py`),
not by hand-edited JSON, then installed as the origin's published snapshot and
read back out of a real browser.

| Scenario | product | freshness | Reader sees |
|---|---|---|---|
| 01 healthy | PASS | FRESH | no banner, four conclusions |
| 02 Tier B local source missing | DEGRADED | DEGRADED | banner names ChatGPT 导出 |
| 03 optional cloud backup missing | DEGRADED | DEGRADED | banner names GitHub 私有仓全量备份 |
| 04 stale but healthy | DEGRADED | STALE | banner names the 1800s target |
| 05 required cloud authority failed | **FAILED** | DEGRADED | banner names both R2 authorities |
| 06 recovered | PASS | FRESH | banner gone |
| 07 authority read-back fails | API **503** | — | **last-good kept**: same run id, same event count, four conclusions, banner shown |
| 08 authority returns | PASS | FRESH | banner gone, same run id |

07 is AC-008 in full: `current` does not move, the browser does not blank, and
no zero is invented. 02 and 03 are AC-009: a Tier B gap and an optional cloud
gap degrade without claiming failure, and neither empties anything.

## Privacy and zero-model — `PRIVACY_DEPENDENCY_SCAN.json`, **PASS**

`privacy_and_dependency_scan.py`, 0 findings across 4 payloads and 7 serving
modules. It checks 18 forbidden key names, 4 forbidden value patterns
(R2 prefixes, absolute private paths, bare sha256, bearer/API keys) and 17
model-runtime imports plus call-shape hints.

Two things worth stating plainly:

1. **The scanner has its own tests** (`test_privacy_and_dependency_scan.py`, 8
   tests) that plant a leaked object key, a `/srv/linze` path, a digest outside
   the release identity, a bearer token, a model import and a model call, and
   require the scanner to catch each. A green scan from an untested scanner is
   worth nothing.
2. Writing those tests found a **real hole in the scanner**: `_walk` recursed
   into lists but never yielded their string elements, so a leak inside
   `truth.limitations[0]` was invisible. Fixed, and the same hole was fixed in
   the test helper that shared the shape.

`$.release.artifact_digest` is the one allowlisted digest — it is the deployed
public bundle's hash, published on purpose so the browser can cross-check it
against the API headers. The allowlist is an exact path, so a digest anywhere
else is still a finding; a test proves that.

## Verification

- Backend: **550 passed**, 2 failed — both the known Python 3.9 `tomllib` gap in
  an untouched file, green under 3.12 and on CI's 3.13.
- `lint`, `validate:v31`, `validate:preservation`, `validate:v31:incremental`,
  `validate:v31:typescript`: all pass.
- `test_verification_policy` caught the new `capture_degraded_receipts_v32.mjs`
  having no package owner before it could ship unowned; registered as
  `validate:v32:degraded`.

## Rollback

`ops/memory-atlas/source-registry.json` is additive — the loader ignores unknown
keys, and removing the two fields restores the previous hard-coded behaviour.
The live snapshot itself remains flag-off reversible
(`MEMORY_ATLAS_LIVE_SNAPSHOT=0`), which now also records why it did not publish
rather than failing silently.
