# Owner Gate — data governance instruction is A4 under v0.0.0.32

Raised at T00. Blocks only this item; the rest of the DAG continues.

## The instruction

Move data pressure onto a GitHub private repository as the full-history primary,
and off Cloudflare R2 / OVH; R2 to keep a deduplicated full set with no
overlapping copies.

## Why it is gated

`CANONICAL_STATE.json` freezes `A4_irreversible_or_scope_expanding: false`, and
T08's stop condition names the two triggers exactly:

> 需要 A4、扩大访问或**改变数据权威**时停止该动作并报告 Owner Gate

`architecture/DATA_AUTHORITY_AND_RUNTIME.mmd` pins the current authorities:

```
R2  primary-objects        → 对象字节权威
PDB Private-Database       → 长期结构化事实权威
R2  backups/private-database → 冷备
```

So the instruction triggers A4 twice:

1. **Changing data authority** — making GitHub the raw-byte authority replaces R2
   in that role.
2. **Irreversible deletion** — reclaiming the superseded snapshots deletes ~3.2 GB
   of production objects.

Both are outside the authorization this taskpack grants a Delivery Agent.

## Measured facts the decision rests on (read-only, 2026-08-04)

Bucket `weread-port-private`, 13,127 objects, **8.040 GB**.

| Store | Objects | Size | State |
|---|---|---|---|
| `primary-objects/memory-atlas/private-agentdatabase/sha256/` | 2,363 | 4.440 GB | content-addressed, **0 exact duplicates** |
| `…/normalized/marun_*/events.jsonl` | 10 | 3.579 GB | one full snapshot per run, ~350 MB each |
| `primary-objects/accounts/` | 10,718 | 0.013 GB | — |
| `backups/private-database/` | 35 | 0.008 GB | fact bundles |

Content-addressing already works: **no byte-identical object is stored twice**.
The waste is *logical supersession* — 10 whole-history snapshots in two days.

Lifecycle rules configured: **one**, the default multipart-abort. Nothing expires,
which is why history accumulates without bound.

## The finding that kills the obvious fix

"Keep only the newest snapshot" is **not provably safe**. Measured:

- oldest vs newest first-1 MB: different hashes — not append-ordered
- first event id differs between them
- in a 4 MB head sample, **143 event ids present in the old are absent from the new**

Ordering differs, so a head-sample comparison does not prove data loss — but it
does prove the snapshots cannot be assumed nested. Deleting older ones without
computing the union first risks losing events.

## Also decision-relevant

**R2 lifecycle rules cannot express the requirement.** They can expire by age or
prefix, abort multipart uploads, and change storage class. They cannot merge
`1-90` and `30-120` into `1-120` — they never read object contents. Union-dedup
has to happen in the uploader (`pipeline.py:40`, which hard-codes one whole
`events.jsonl` per run) or in a periodic compaction job. Both live in this
repository, so **the Codex local automation does not need to change**.

## Minimal decision required from the Owner

1. Do you authorize **A4** for this item — changing the raw-byte authority away
   from R2, and deleting superseded R2 objects? Without it the DAG proceeds and
   this stays blocked.
2. If yes: prove the union first (stream all 10 snapshots, ids only, no writes),
   then write one canonical deduped object, verify it, and only then delete —
   or accept a faster, lossy retention rule?
3. Does the uploader change (`pipeline.py` → content-addressed shards, which is
   the actual "incremental upload" fix) go in this slice, or after v0.0.0.32?

Nothing has been written, deleted, or reconfigured. The R2 work so far is
read-only inventory.
