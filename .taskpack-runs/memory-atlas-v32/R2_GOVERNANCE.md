# R2 governance — deduplicated to a proven union (A4 authorized by Owner)

Executed 2026-08-04 after the Owner authorized A4. Every deletion was gated on a
verified read-back; nothing was removed before the replacement was proven.

## What was wrong

`primary-objects/memory-atlas/private-agentdatabase/normalized/` held **ten
whole-history rollups**, one per capture run, 341.8–366.9 MB each, **3.579 GB
total** — written over two days. They were never byte-identical, so the
content-addressed store could not dedupe them.

Bucket before: **13,127 objects, 8.040 GB**. Exact-content duplicates: **0** —
content addressing was already working. The waste was *logical supersession*.

## The finding that changed the plan

"Keep only the newest snapshot" would have **destroyed data**. Measured by
streaming all ten and comparing event-id sets:

| | |
|---|---|
| union across all ten runs | **122,080 events** |
| largest single run | 112,036 events |
| **events absent from the largest run** | **10,044 (8.2%)** |
| runs holding events unique to them | **10 of 10** |

Every run held events no other run had — 3,505 / 3,173 / 2,628 / 1,071 / 480 /
114 / 37 / 5 / 5 / 4. The source prunes local sessions between runs, so no run is
a superset of its predecessor. A retention-by-age rule would have silently
dropped 10,044 events.

## What was done

1. **Union proven first, read-only.** Streamed all ten snapshots, ids only, no
   writes, no local disk.
2. **Canonical object built** by union on event id, deterministic source order:
   `normalized/canonical/events.jsonl` — 122,080 unique events, 981,704
   duplicate lines dropped, 389,413,637 bytes,
   `sha256 7b34a3d8eae98315716ffa2abfbae52e35f661a90bb63ee9b587e12afee83bfa`.
3. **Verified by read-back** before any deletion: remote sha256 == local, byte
   count identical, **122,080 ids recovered from the readback**.
4. **Provenance written** to `normalized/canonical/MANIFEST.json`, naming every
   superseded object and the loss check.
5. **Deletion gated**: the ten were removed only after a fresh readback returned
   exactly 122,080 ids. All ten returned HTTP 204.

Bucket after: **13,119 objects, 4.850 GB. Reclaimed 3.190 GB, zero events lost.**

## Stopping the regrowth

The cause was `pipeline.py`, which wrote one whole rollup per run to
`normalized/<run_id>/events.jsonl`. It now publishes **base + per-run delta**:

- base: `normalized/canonical/events.jsonl` — the union to date
- delta: `normalized/canonical/delta/<run_id>.jsonl` — only ids this host has
  not published before, tracked in a durable index in the runtime dir

Union is still base + every delta, so nothing is superseded and nothing is
re-uploaded. On the measured runs the deltas would have been 4–7,748 events
instead of ~110,000 — **over 90% less upload volume**. `event_count` keeps its
old meaning; `published_event_count` and `incremental_upload` report what
actually left the host.

R2 lifecycle rules were **not** used for this: they can only expire by age or
prefix and never read object contents, so they cannot merge overlapping ranges.
The only rule on the bucket remains the default multipart-abort.

## Where the pressure now sits

| Plane | Role | State |
|---|---|---|
| **GitHub `LinzeColin/Private-Database` Releases** | **all-time primary** | already active: age-encrypted payloads sharded to 90 MB to stay under git's 100 MB limit, plus `manifest.json` |
| R2 `weread-port-private` | deduplicated full set | 4.850 GB, one canonical rollup + content-addressed store |
| OVH | runtime only, rebuildable | unchanged |

The 389 MB canonical object cannot live in git — GitHub rejects files over
100 MB — which is why the existing Release-asset sharding is the correct primary
and was kept rather than replaced.
