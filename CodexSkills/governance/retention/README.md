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

## M-062 public-safe queue lifecycle

Status: **DRAFT_NON_ACTIVE**

`public_safe_queue.py` consumes only an exact private
`public-queue-envelope:v2` and its already-projected canonical
`public-run-event:v2`. It revalidates the envelope as if public, so unknown,
raw, prompt, output, reasoning, credential, absolute-path, and other private
fields are structurally rejected even though the physical queue itself is
private local storage. The artifact must target the Sydney calendar date and
an exact `part-NNNN.jsonl` path under the canonical Skill run-log root.

A READY entry remains retained when no remote proof is available. Settlement
does not accept a caller boolean or digest map. A repository-external
read-only capability must resolve `origin/main` to an advanced Git object and
return the exact blob from that object. The guard bounds the blob at 20 MiB,
checks LF-only JSONL framing, validates every line as canonical and
public-safe, rejects duplicate UID/digest records, and requires exactly one
line whose UID, digest, and bytes match the queued event.

The result is public-safe observation, readback, and lifecycle-plan evidence.
It never receives a queue root, state path, lock, watermark, or worktree, and
it never mutates the Auto-owned queue. Even after verified readback it grants
neither queue-content deletion nor watermark advancement. Real reader and
Auto executor integration remain `NOT_BOUND`; the daily manifest/index and
365-day active-tree policy remain exclusively M-063.

Deterministic materialization and tests:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_public_safe_queue_lifecycle.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_public_safe_queue_lifecycle
```

The readiness artifact is
`retention/public-safe-queue-lifecycle-readiness.json`. M-062 creates no queue
entry, state, lock, watermark, Git worktree, publication, VERSION, activation,
or canonical run artifact. Its only successor is M-063,
`MECHANISM_GIT_ACTIVE_TREE_365D_POLICY`.
