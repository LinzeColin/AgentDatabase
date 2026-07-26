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
