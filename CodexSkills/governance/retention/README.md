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

## M-063 Git active-tree 365-day policy

Status: **DRAFT_NON_ACTIVE**

`git_active_tree_policy.py` validates the complete current daily ledger:
gapless append-only `manifest-NNNN.json` history, immutable part descriptors,
physical `part-NNNN.jsonl` bytes, retained `index-NNNN.jsonl` bytes, and every
historical prune receipt required by the latest tree. A receipt remains bound
to the exact predecessor manifest and transaction where its shard first
changed from ACTIVE to PRUNED; later manifest revisions cannot rewrite that
evidence.

The retention clock is UTC elapsed time from `first_published_at`.
`retention_not_before` is exactly 365 × 24 hours later. Day 364 and the exact
day-365 boundary are `KEEP_FULL_FIDELITY`; only `now >
retention_not_before` is `ELIGIBLE_FOR_CURRENT_TREE_PRUNE`. The retained index
remains mandatory and may contain only the bounded index-entry contract, not a
full-event rollup replacement.

An eligible result is a deterministic plan, not delete authority. A valid
transition deletes exactly the prior shard bytes and publishes the next daily
manifest, `publication-manifest:v2`, and `retention-receipt:v3` as one closed
artifact set. Equality at `retention_not_before + 24h` is on time; later
execution requires the explicit prune-deadline breach reason. The guard has no
filesystem, Git, state, lock, network, publisher, or Auto executor capability.
It neither mutates the current tree nor claims removal from Git history.

Deterministic materialization and tests:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_git_active_tree_365d_policy.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_git_active_tree_365d_policy
```

The readiness artifact is
`retention/git-active-tree-365d-readiness.json`. M-063 creates no shard,
index, manifest, receipt, state, Git commit, VERSION, activation, or canonical
publication. Real execution and Auto integration remain `NOT_BOUND`. Its only
successor is M-064, `MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE`.

## M-064 Git-history persistence disclosure

Status: **DRAFT_NON_ACTIVE**

`git_history_disclosure.py` freezes exact English and zh-CN operator/user
statements for the retention boundary. The 365-day contract is limited to
full-fidelity artifacts in the Git current tree. A strictly post-boundary
shard can become eligible for ordinary current-tree removal, but Git history,
forks, clones, caches, archives, provider backups, and third-party copies may
retain the bytes indefinitely.

A retention receipt proves only the audited current-tree transition. It is
not evidence of permanent deletion, Git-history erasure, all-copy erasure, or
irrecoverability. The bounded UTF-8 surface guard rejects affirmative English
and Chinese hard-erasure claims while accepting the exact truthful
negations. The canonical disclosure is
`retention/GIT_HISTORY_PERSISTENCE_DISCLOSURE.md`; a structured, self-digested
counterpart supports deterministic validation.

Deterministic materialization and tests:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_git_history_persistence_disclosure.py \
  --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_git_history_persistence_disclosure
```

The readiness artifact is
`retention/git-history-persistence-readiness.json`. M-064 performs no
current-tree removal, Git-history rewrite, repository or private-storage
rotation, state write, publication, activation, or VERSION creation. A future
hard-erasure capability requires a separate Owner-authorized MAJOR design.
Its only successor is M-065, `MECHANISM_READ_ONLY_MIGRATION_CUTOVER`.
