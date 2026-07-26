# M-060 protected-local / managed-raw boundary

Status: **DRAFT_NON_ACTIVE**

`root_lifecycle.py` is the Mechanism-owned, read-only scope guard for Task Pack
M-060. It binds private physical roots without serializing their paths,
classifies `SKILL_SOURCE`, `RUN_SOURCE`, and `LEGACY_DATA` as protected local
data, maps `STAGING` to the managed raw spool, and keeps `PUBLIC_QUEUE`
separate from raw retention.

Only an exact, schema-valid, ownership-marker-valid, payload-closed
`raw-segment:v2` under the managed staging root can be returned as
`ELIGIBLE_FOR_M061_TIME_EVALUATION`. The result is not delete authority:
M-060 does not evaluate age, emit expiry receipts, or mutate a file.

The observation and report contain low-entropy refs and aggregate facts only.
Absolute paths, raw bytes, payload digests, metadata contents, and private
root bindings never enter the public-safe evidence.

## M-061 managed-raw 72-hour policy

Status: **DRAFT_NON_ACTIVE**

`managed_raw_policy.py` consumes only the exact candidates and selection
evidence produced by M-060. It revalidates the private `raw-segment:v2`
contract and ownership marker, but never receives or serializes a physical
path. Persistent managed raw remains disabled by default and only synthetic
`TEST_ONLY` segments are eligible while production certification is absent.

The UTC wall-clock contract is anchored to `created_at`, not `sealed_at`.
Stages start at 0, 24, 48, 60, and 72 elapsed hours. The boundary is exact:
elapsed time below 72 hours is `KEEP`; elapsed time at or above 72 hours is
`EXPIRE`. A post-72-hour observation is valid only in an explicit recovery
cycle with evidence that the runtime became unavailable no later than the
expiry instant. It then requires a truthful `OFFLINE_TTL_BREACH` receipt;
offline time is never represented as a hard guarantee.

The deterministic plan orders reprojection, any
`RAW_EXPIRED_UNPUBLISHED` gap record, deletion of the owned segment, and
`retention-receipt:v3`. It does not grant deletion authority or perform any
of those operations. Receipt validation recomputes clock, counts, bytes,
cutoff, policy digest, plan evidence, breach state, and the immutable M-060
scope reference.

Deterministic materialization and tests:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_managed_raw_72h_policy.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_managed_raw_72h_policy
```

The readiness artifact is
`retention/managed-raw-72h-readiness.json`. M-061 leaves real execution,
receipt emission, persistent state, canonical publication, activation, and
VERSION creation false. Its only successor is M-062,
`MECHANISM_PUBLIC_SAFE_QUEUE_LIFECYCLE`.
